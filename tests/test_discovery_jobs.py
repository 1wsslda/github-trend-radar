from __future__ import annotations

import sys
import json
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.discovery_jobs import make_discovery_job_runtime
from gitsonar.runtime.state import make_state_runtime
from gitsonar.runtime.utils import as_bool, clamp_int, iso_now, normalize


class _Cancelled(RuntimeError):
    pass


class _SuccessfulGitHubRuntime:
    DiscoveryCancelledError = _Cancelled

    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def discover_repos(self, **kwargs):
        self.calls.append(dict(kwargs))
        progress_callback = kwargs.get("progress_callback")
        if callable(progress_callback):
            progress_callback("initial_results", {"results": [{"full_name": "octo/agent", "url": "https://github.com/octo/agent"}]})
        return {
            "translated_query": "agent",
            "generated_queries": ["agent"],
            "related_terms": ["workflow"],
            "warnings": [],
            "run_at": iso_now(),
            "results": [
                {
                    "full_name": "octo/agent",
                    "url": "https://github.com/octo/agent",
                    "description": "Agent toolkit",
                    "language": "Python",
                    "stars": 120,
                    "forks": 12,
                }
            ],
        }


class _SlowGitHubRuntime:
    DiscoveryCancelledError = _Cancelled

    def discover_repos(self, **kwargs):
        progress_callback = kwargs.get("progress_callback")
        is_cancelled = kwargs.get("is_cancelled")
        for _ in range(50):
            if callable(progress_callback):
                progress_callback("initial_search", {"results": []})
            if callable(is_cancelled) and is_cancelled():
                raise _Cancelled("cancelled")
            time.sleep(0.01)
        return {"results": [], "warnings": [], "run_at": iso_now()}


class _FailingGitHubRuntime:
    DiscoveryCancelledError = _Cancelled

    def discover_repos(self, **_kwargs):
        raise RuntimeError(
            "query failed with ghp_secret_token via "
            "http://user:pass@127.0.0.1:7890 at C:\\Users\\liushun\\runtime-data\\discovery.json"
        )


def build_state_runtime(settings: dict[str, object] | None = None):
    return make_state_runtime(
        settings=settings or {},
        user_state={},
        discovery_state={},
        state_lock=threading.RLock(),
        discovery_lock=threading.RLock(),
        current_snapshot_getter=lambda: {},
        sync_repo_records_callback=lambda _snapshot: None,
        user_state_path=str(ROOT / "artifacts" / "_test_user_state.json"),
        discovery_state_path=str(ROOT / "artifacts" / "_test_discovery_state.json"),
        latest_snapshot_path=str(ROOT / "artifacts" / "_test_snapshot.json"),
        periods=[{"key": "daily", "label": "Today", "days": 1}],
        normalize=normalize,
        clamp_int=clamp_int,
        as_bool=as_bool,
        iso_now=iso_now,
        load_json_file=lambda _path, default: default,
        atomic_write_json=lambda _path, _payload: None,
        apply_repo_translation=lambda _repo: None,
    )


def build_job_runtime(settings: dict[str, object], state_runtime, github_runtime):
    return make_discovery_job_runtime(
        settings=settings,
        normalize=normalize,
        clamp_int=clamp_int,
        as_bool=as_bool,
        iso_now=iso_now,
        normalize_repo=state_runtime.normalize_repo,
        normalize_discovery_query=state_runtime.normalize_discovery_query,
        apply_discovery_result=state_runtime.apply_discovery_result,
        discovery_warning_list=state_runtime.discovery_warning_list,
        github_runtime=github_runtime,
        job_lock=threading.RLock(),
    )


def wait_for_terminal(job_runtime, job_id: str, timeout: float = 2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = job_runtime.get_discovery_job(job_id)
        if job["status"] in {"completed", "failed", "cancelled"}:
            return job
        time.sleep(0.02)
    raise AssertionError(f"discovery job {job_id} did not finish in time")


class DiscoveryJobRuntimeTests(unittest.TestCase):
    def test_start_discovery_job_completes_and_updates_discovery_state(self):
        settings = {"result_limit": 20, "github_token": "token"}
        state_runtime = build_state_runtime(settings)
        job_runtime = build_job_runtime(settings, state_runtime, _SuccessfulGitHubRuntime())

        snapshot = job_runtime.start_discovery_job({"query": "agent", "save_query": True})
        finished = wait_for_terminal(job_runtime, snapshot["id"])
        discovery_state = state_runtime.export_discovery_state()

        self.assertEqual(finished["status"], "completed")
        self.assertEqual(discovery_state["last_query"]["query"], "agent")
        self.assertEqual(discovery_state["last_results"][0]["full_name"], "octo/agent")
        self.assertEqual(discovery_state["remembered_query"]["query"], "agent")
        self.assertIsNone(job_runtime.export_active_discovery_job())

    def test_save_query_false_does_not_overwrite_remembered_query(self):
        settings = {"result_limit": 20, "github_token": "token"}
        state_runtime = build_state_runtime(settings)
        state_runtime.apply_discovery_result(
            state_runtime.normalize_discovery_query({"query": "remember me"}),
            {"results": [], "warnings": [], "run_at": iso_now()},
            save_query=True,
        )
        job_runtime = build_job_runtime(settings, state_runtime, _SuccessfulGitHubRuntime())

        snapshot = job_runtime.start_discovery_job({"query": "agent", "save_query": False})
        wait_for_terminal(job_runtime, snapshot["id"])
        discovery_state = state_runtime.export_discovery_state()

        self.assertEqual(discovery_state["last_query"]["query"], "agent")
        self.assertEqual(discovery_state["remembered_query"]["query"], "remember me")

    def test_cancel_discovery_job_marks_job_cancelled(self):
        settings = {"result_limit": 20, "github_token": ""}
        state_runtime = build_state_runtime(settings)
        job_runtime = build_job_runtime(settings, state_runtime, _SlowGitHubRuntime())

        snapshot = job_runtime.start_discovery_job({"query": "cancel me"})
        time.sleep(0.05)
        cancel_snapshot = job_runtime.cancel_discovery_job(snapshot["id"])
        finished = wait_for_terminal(job_runtime, snapshot["id"])

        self.assertTrue(cancel_snapshot["cancel_requested"])
        self.assertEqual(finished["status"], "cancelled")

    def test_start_discovery_job_accepts_limit_up_to_one_hundred(self):
        settings = {"result_limit": 100, "github_token": "token"}
        state_runtime = build_state_runtime(settings)
        github_runtime = _SuccessfulGitHubRuntime()
        job_runtime = build_job_runtime(settings, state_runtime, github_runtime)

        snapshot = job_runtime.start_discovery_job({"query": "agent", "limit": 100, "save_query": True})
        finished = wait_for_terminal(job_runtime, snapshot["id"])
        discovery_state = state_runtime.export_discovery_state()

        self.assertEqual(finished["status"], "completed")
        self.assertEqual(discovery_state["last_query"]["limit"], 100)
        self.assertEqual(discovery_state["remembered_query"]["limit"], 100)
        self.assertTrue(github_runtime.calls)
        self.assertEqual(github_runtime.calls[0]["limit"], 100)

    def test_failed_discovery_job_payload_uses_safe_error_summary(self):
        settings = {"result_limit": 20, "github_token": "token"}
        state_runtime = build_state_runtime(settings)
        job_runtime = build_job_runtime(settings, state_runtime, _FailingGitHubRuntime())

        snapshot = job_runtime.start_discovery_job({"query": "agent"})
        finished = wait_for_terminal(job_runtime, snapshot["id"])
        payload_text = json.dumps(finished, ensure_ascii=False)

        self.assertEqual(finished["status"], "failed")
        self.assertTrue(finished["error"])
        self.assertNotIn("ghp_secret_token", payload_text)
        self.assertNotIn("user:pass", payload_text)
        self.assertNotIn("C:\\Users\\liushun", payload_text)


if __name__ == "__main__":
    unittest.main()
