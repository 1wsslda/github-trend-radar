from __future__ import annotations

import sys
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gitsonar.runtime.app as runtime_app


class RuntimeAppTests(unittest.TestCase):
    def test_refresh_once_locked_auto_syncs_starred_only_once_per_process(self):
        starred_calls: list[str] = []
        sync_calls: list[list[dict[str, object]]] = []
        tracked_sources: list[str] = []
        snapshots: list[dict[str, object]] = []

        github_runtime = SimpleNamespace(
            fetch_all=lambda: {"daily": [], "weekly": [], "monthly": [], "fetched_at": "now"},
            fetch_user_starred=lambda: starred_calls.append("fetch") or [{"full_name": "octo/demo", "url": "https://github.com/octo/demo"}],
            sync_local_favorites_with_starred=lambda repos: sync_calls.append(list(repos)) or {"total": len(repos)},
            track_favorite_updates=lambda: tracked_sources.append("track") or 0,
        )

        with (
            patch.object(runtime_app, "github_runtime", github_runtime),
            patch.object(runtime_app, "SETTINGS", {"github_token": "token", "port": 8080}),
            patch.object(runtime_app, "CURRENT_SNAPSHOT", {"fetched_at": "old"}),
            patch.object(runtime_app, "AUTO_SYNC_USER_STARS_DONE", False),
            patch.object(runtime_app, "save_snapshot", lambda snapshot: snapshots.append(snapshot)),
            patch.object(runtime_app, "sync_repo_records", lambda _snapshot: None),
            patch.object(runtime_app, "write_html", lambda *_args, **_kwargs: None),
            patch.object(runtime_app, "write_status", lambda *_args, **_kwargs: None),
            patch.object(runtime_app, "shell_runtime", SimpleNamespace(notify_tray=lambda _message: None)),
        ):
            runtime_app.refresh_once_locked("startup")
            runtime_app.refresh_once_locked("manual")

        self.assertEqual(starred_calls, ["fetch"])
        self.assertEqual(len(sync_calls), 1)
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(tracked_sources, ["track", "track"])

    def test_refresh_once_locked_skips_auto_star_sync_without_token(self):
        starred_calls: list[str] = []
        sync_calls: list[str] = []

        github_runtime = SimpleNamespace(
            fetch_all=lambda: {"daily": [], "weekly": [], "monthly": [], "fetched_at": "now"},
            fetch_user_starred=lambda: starred_calls.append("fetch") or [],
            sync_local_favorites_with_starred=lambda _repos: sync_calls.append("sync") or {"total": 0},
            track_favorite_updates=lambda: 0,
        )

        with (
            patch.object(runtime_app, "github_runtime", github_runtime),
            patch.object(runtime_app, "SETTINGS", {"github_token": "", "port": 8080}),
            patch.object(runtime_app, "CURRENT_SNAPSHOT", {"fetched_at": "old"}),
            patch.object(runtime_app, "AUTO_SYNC_USER_STARS_DONE", False),
            patch.object(runtime_app, "save_snapshot", lambda _snapshot: None),
            patch.object(runtime_app, "sync_repo_records", lambda _snapshot: None),
            patch.object(runtime_app, "write_html", lambda *_args, **_kwargs: None),
            patch.object(runtime_app, "write_status", lambda *_args, **_kwargs: None),
            patch.object(runtime_app, "shell_runtime", SimpleNamespace(notify_tray=lambda _message: None)),
        ):
            runtime_app.refresh_once_locked("startup")
            self.assertFalse(runtime_app.AUTO_SYNC_USER_STARS_DONE)

        self.assertEqual(starred_calls, [])
        self.assertEqual(sync_calls, [])

    def test_detail_cache_helpers_use_current_globals_and_update_dirty_state(self):
        writes: list[tuple[str, dict[str, object]]] = []
        runtime_paths = SimpleNamespace(detail_cache_path=str(ROOT / "artifacts" / "_detail_cache.json"))

        with (
            patch.object(runtime_app, "runtime_paths", lambda: runtime_paths),
            patch.object(runtime_app, "DETAIL_CACHE", {}),
            patch.object(runtime_app, "DETAIL_CACHE_LOCK", threading.RLock()),
            patch.object(runtime_app, "DETAIL_FETCH_LOCKS", {}),
            patch.object(runtime_app, "DETAIL_CACHE_DIRTY", False),
            patch.object(runtime_app, "atomic_write_json", lambda path, payload: writes.append((str(path), dict(payload)))),
            patch.object(runtime_app, "load_json_file", lambda _path, default: {"first": default}),
        ):
            first = runtime_app.load_detail_cache()

            with patch.object(runtime_app, "load_json_file", lambda _path, default: {"second": default}):
                second = runtime_app.load_detail_cache()

            runtime_app.save_repo_details("octo/demo", {"full_name": "octo/demo"})
            flushed = runtime_app.flush_repo_details_cache()
            dirty_after_flush = runtime_app.DETAIL_CACHE_DIRTY

        self.assertEqual(first, {"first": {}})
        self.assertEqual(second, {"second": {}})
        self.assertTrue(flushed)
        self.assertEqual(writes[0][1]["octo/demo"]["data"]["full_name"], "octo/demo")
        self.assertFalse(dirty_after_flush)

    def test_refresh_once_safe_writes_user_safe_status_error(self):
        writes: list[dict[str, object]] = []
        sensitive_error = (
            "refresh failed for ghp_secret_token via "
            "http://user:pass@127.0.0.1:7890 at C:\\Users\\liushun\\runtime-data\\status.json"
        )

        with (
            patch.object(runtime_app, "refresh_once", lambda _source: (_ for _ in ()).throw(RuntimeError(sensitive_error))),
            patch.object(runtime_app, "CURRENT_SNAPSHOT", {"fetched_at": "old"}),
            patch.object(runtime_app, "runtime_paths", lambda: SimpleNamespace(status_path=str(ROOT / "artifacts" / "_status.json"))),
            patch.object(runtime_app, "atomic_write_json", lambda _path, payload: writes.append(dict(payload))),
            patch.object(runtime_app, "iso_now", lambda: "now"),
        ):
            runtime_app.refresh_once_safe("manual")

        self.assertEqual(len(writes), 1)
        status_text = json.dumps(writes[0], ensure_ascii=False)
        self.assertTrue(writes[0]["error"])
        self.assertNotIn("ghp_secret_token", status_text)
        self.assertNotIn("user:pass", status_text)
        self.assertNotIn("C:\\Users\\liushun", status_text)


if __name__ == "__main__":
    unittest.main()
