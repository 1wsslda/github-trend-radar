from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.startup import make_startup_runtime
from gitsonar.runtime.utils import clamp_int, iso_now, normalize


class _DummyResponse:
    def __init__(self, ok: bool):
        self.ok = ok


class _DummyLocalControl:
    def __init__(self, ok: bool = True):
        self.ok = ok
        self.calls: list[tuple[str, dict[str, str] | None, int]] = []

    def post(self, url: str, headers: dict[str, str] | None = None, timeout: int = 0):
        self.calls.append((url, headers, timeout))
        return _DummyResponse(self.ok)


def build_runtime(tempdir: str, *, app_slug: str, legacy_slug: str, local_control, control_token_getter=lambda: "runtime-control-token"):
    runtime_state_path = Path(tempdir) / "runtime-state.json"
    legacy_runtime_state_path = Path(tempdir) / "legacy-runtime-state.json"
    kwargs = dict(
        app_name="GitSonar",
        app_slug=app_slug,
        legacy_app_name="GitSonarLegacy",
        legacy_app_slug=legacy_slug,
        dev_entry_script="dev.py",
        exec_dir=tempdir,
        runtime_state_path=str(runtime_state_path),
        legacy_runtime_state_path=str(legacy_runtime_state_path),
        local_host="127.0.0.1",
        local_control=local_control,
        normalize=normalize,
        clamp_int=clamp_int,
        iso_now=iso_now,
        load_json_file=lambda path, default: json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default,
        atomic_write_json=lambda path, payload: Path(path).write_text(json.dumps(payload), encoding="utf-8"),
        current_port_getter=lambda: 8765,
    )
    if control_token_getter is not None:
        kwargs["control_token_getter"] = control_token_getter
    return make_startup_runtime(**kwargs)


class StartupRuntimeTests(unittest.TestCase):
    def test_make_startup_runtime_preserves_legacy_signature_without_control_token_getter(self):
        with tempfile.TemporaryDirectory() as tempdir:
            control = _DummyLocalControl(ok=True)
            runtime = build_runtime(
                tempdir,
                app_slug="gitsonar-test",
                legacy_slug="gitsonar-test-legacy",
                local_control=control,
                control_token_getter=None,
            )

            runtime.write_runtime_state()

            payload = json.loads((Path(tempdir) / "runtime-state.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["control_token"], "")

    def test_request_existing_instance_open_uses_local_control_endpoint(self):
        with tempfile.TemporaryDirectory() as tempdir:
            control = _DummyLocalControl(ok=True)
            runtime = build_runtime(tempdir, app_slug="gitsonar-test", legacy_slug="gitsonar-test-legacy", local_control=control)
            runtime_state_path = Path(tempdir) / "runtime-state.json"
            runtime_state_path.write_text(
                json.dumps(
                    {
                        "port": 8765,
                        "url": "http://127.0.0.1:8765/trending.html",
                        "control_token": "runtime-control-token",
                    }
                ),
                encoding="utf-8",
            )

            opened = runtime.request_existing_instance_open()

            self.assertTrue(opened)
            self.assertEqual(
                control.calls,
                [
                    (
                        "http://127.0.0.1:8765/api/window/open",
                        {"X-GitSonar-Control": "runtime-control-token"},
                        2,
                    )
                ],
            )

    @unittest.skipUnless(os.name == "nt", "single-instance mutex test is Windows-only")
    def test_acquire_single_instance_rejects_second_runtime_with_same_slug(self):
        with tempfile.TemporaryDirectory() as tempdir:
            slug = f"gitsonar-test-{time.time_ns()}"
            control = _DummyLocalControl(ok=False)
            runtime_one = build_runtime(tempdir, app_slug=slug, legacy_slug=f"{slug}-legacy", local_control=control)
            runtime_two = build_runtime(tempdir, app_slug=slug, legacy_slug=f"{slug}-legacy", local_control=control)
            runtime_three = build_runtime(tempdir, app_slug=slug, legacy_slug=f"{slug}-legacy", local_control=control)
            self.assertTrue(runtime_one.acquire_single_instance())
            self.assertFalse(runtime_two.acquire_single_instance())
            runtime_one.release_single_instance()
            self.assertTrue(runtime_three.acquire_single_instance())
            runtime_three.release_single_instance()


if __name__ == "__main__":
    unittest.main()
