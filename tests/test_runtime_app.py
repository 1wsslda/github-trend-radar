from __future__ import annotations

import sys
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


if __name__ == "__main__":
    unittest.main()
