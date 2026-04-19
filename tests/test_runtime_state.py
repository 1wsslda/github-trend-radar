from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.state import make_state_runtime
from gitsonar.runtime.utils import as_bool, clamp_int, iso_now, normalize


def build_state_runtime(*, user_state: dict[str, object] | None = None, write_calls: list[str] | None = None):
    writes = write_calls if write_calls is not None else []
    sync_calls: list[dict[str, object]] = []
    current_snapshot = {"daily": [], "fetched_at": "now"}
    runtime = make_state_runtime(
        settings={},
        user_state=user_state
        if user_state is not None
        else {
            "favorites": [],
            "watch_later": [],
            "read": [],
            "ignored": [],
            "repo_records": {},
            "favorite_watch": {},
            "favorite_updates": [],
        },
        discovery_state={},
        state_lock=threading.RLock(),
        discovery_lock=threading.RLock(),
        current_snapshot_getter=lambda: dict(current_snapshot),
        sync_repo_records_callback=lambda snapshot: sync_calls.append(dict(snapshot)),
        user_state_path=str(ROOT / "artifacts" / "_test_user_state.json"),
        discovery_state_path=str(ROOT / "artifacts" / "_test_discovery_state.json"),
        latest_snapshot_path=str(ROOT / "artifacts" / "_test_snapshot.json"),
        periods=[{"key": "daily", "label": "Today", "days": 1}],
        normalize=normalize,
        clamp_int=clamp_int,
        as_bool=as_bool,
        iso_now=iso_now,
        load_json_file=lambda _path, default: default,
        atomic_write_json=lambda path, _payload: writes.append(str(path)),
        apply_repo_translation=lambda _repo: None,
    )
    runtime._write_calls = writes
    runtime._sync_calls = sync_calls
    runtime._current_snapshot = current_snapshot
    return runtime


class RuntimeStateBatchTests(unittest.TestCase):
    def test_set_repo_state_batch_saves_user_state_once(self):
        write_calls: list[str] = []
        runtime = build_state_runtime(write_calls=write_calls)
        repos = [
            {"full_name": "octo/one", "url": "https://github.com/octo/one"},
            {"full_name": "octo/two", "url": "https://github.com/octo/two"},
            {"full_name": "octo/three", "url": "https://github.com/octo/three"},
        ]

        runtime.set_repo_state_batch("watch_later", True, repos)

        self.assertEqual(len(write_calls), 1)
        self.assertEqual(
            runtime.export_user_state()["watch_later"],
            [
                "https://github.com/octo/three",
                "https://github.com/octo/two",
                "https://github.com/octo/one",
            ],
        )

    def test_set_repo_state_batch_matches_single_repo_rules(self):
        repos = [
            {"full_name": "octo/one", "url": "https://github.com/octo/one"},
            {"full_name": "octo/two", "url": "https://github.com/octo/two"},
        ]
        single_runtime = build_state_runtime()
        batch_runtime = build_state_runtime()

        for repo in repos:
            single_runtime.set_repo_state("read", True, repo)
        batch_runtime.set_repo_state_batch("read", True, repos)

        self.assertEqual(single_runtime.export_user_state(), batch_runtime.export_user_state())

    def test_set_repo_state_batch_keeps_partial_success_and_saves_once_on_failure(self):
        write_calls: list[str] = []
        runtime = build_state_runtime(write_calls=write_calls)
        repos = [
            {"full_name": "octo/one", "url": "https://github.com/octo/one"},
            {"full_name": "broken/repo"},
        ]

        with self.assertRaises(ValueError) as ctx:
            runtime.set_repo_state_batch("favorites", True, repos)

        self.assertEqual(getattr(ctx.exception, "processed_count", 0), 1)
        self.assertEqual(len(write_calls), 1)
        self.assertEqual(runtime.export_user_state()["favorites"], ["https://github.com/octo/one"])


class RuntimeStateImportTests(unittest.TestCase):
    def test_import_user_state_merge_combines_lists_and_prunes_favorite_metadata(self):
        runtime = build_state_runtime(
            user_state={
                "favorites": [
                    "https://github.com/octo/existing",
                    "https://github.com/octo/keep",
                ],
                "watch_later": ["https://github.com/octo/existing"],
                "read": [],
                "ignored": [],
                "repo_records": {
                    "https://github.com/octo/existing": {
                        "full_name": "octo/existing",
                        "url": "https://github.com/octo/existing",
                    },
                    "https://github.com/octo/keep": {
                        "full_name": "octo/keep",
                        "url": "https://github.com/octo/keep",
                    },
                },
                "favorite_watch": {
                    "https://github.com/octo/keep": {
                        "full_name": "octo/keep",
                        "url": "https://github.com/octo/keep",
                        "checked_at": "2026-01-01T00:00:00",
                    },
                    "https://github.com/octo/stale": {
                        "full_name": "octo/stale",
                        "url": "https://github.com/octo/stale",
                        "checked_at": "2026-01-01T00:00:00",
                    },
                },
                "favorite_updates": [
                    {
                        "id": "existing-update",
                        "full_name": "octo/existing",
                        "url": "https://github.com/octo/existing",
                        "checked_at": "2026-01-02T00:00:00",
                        "changes": ["stars +1"],
                    },
                    {
                        "id": "stale-update",
                        "full_name": "octo/stale",
                        "url": "https://github.com/octo/stale",
                        "checked_at": "2026-01-02T00:00:00",
                        "changes": ["stars +1"],
                    },
                ],
            }
        )

        result = runtime.import_user_state(
            {
                "mode": "merge",
                "user_state": {
                    "favorites": [
                        "https://github.com/octo/new",
                        "https://github.com/octo/keep",
                    ],
                    "watch_later": ["https://github.com/octo/new"],
                    "repo_records": {
                        "https://github.com/octo/new": {
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                        }
                    },
                    "favorite_watch": {
                        "https://github.com/octo/new": {
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                            "checked_at": "2026-02-01T00:00:00",
                        },
                        "https://github.com/octo/ignored": {
                            "full_name": "octo/ignored",
                            "url": "https://github.com/octo/ignored",
                            "checked_at": "2026-02-01T00:00:00",
                        },
                    },
                    "favorite_updates": [
                        {
                            "id": "new-update",
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                            "checked_at": "2026-02-02T00:00:00",
                            "changes": ["release"],
                        },
                        {
                            "id": "ignored-update",
                            "full_name": "octo/ignored",
                            "url": "https://github.com/octo/ignored",
                            "checked_at": "2026-02-02T00:00:00",
                            "changes": ["release"],
                        },
                    ],
                },
            }
        )

        state = result["user_state"]
        self.assertEqual(
            state["favorites"],
            [
                "https://github.com/octo/new",
                "https://github.com/octo/keep",
                "https://github.com/octo/existing",
            ],
        )
        self.assertEqual(sorted(state["favorite_watch"].keys()), ["https://github.com/octo/keep", "https://github.com/octo/new"])
        self.assertEqual(
            [item["id"] for item in state["favorite_updates"]],
            ["new-update", "existing-update"],
        )
        self.assertEqual(result["mode"], "merge")
        self.assertEqual(len(runtime._sync_calls), 1)
        self.assertEqual(runtime._sync_calls[0]["fetched_at"], "now")

    def test_import_user_state_replace_discards_previous_lists_and_prunes_non_favorites(self):
        runtime = build_state_runtime(
            user_state={
                "favorites": ["https://github.com/octo/old"],
                "watch_later": ["https://github.com/octo/old"],
                "read": [],
                "ignored": [],
                "repo_records": {
                    "https://github.com/octo/old": {
                        "full_name": "octo/old",
                        "url": "https://github.com/octo/old",
                    }
                },
                "favorite_watch": {
                    "https://github.com/octo/old": {
                        "full_name": "octo/old",
                        "url": "https://github.com/octo/old",
                        "checked_at": "2026-01-01T00:00:00",
                    }
                },
                "favorite_updates": [
                    {
                        "id": "old-update",
                        "full_name": "octo/old",
                        "url": "https://github.com/octo/old",
                        "checked_at": "2026-01-02T00:00:00",
                        "changes": ["stars +1"],
                    }
                ],
            }
        )

        result = runtime.import_user_state(
            {
                "mode": "replace",
                "data": {
                    "favorites": ["https://github.com/octo/new"],
                    "watch_later": [],
                    "read": ["https://github.com/octo/readme"],
                    "ignored": [],
                    "repo_records": {
                        "https://github.com/octo/new": {
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                        }
                    },
                    "favorite_watch": {
                        "https://github.com/octo/new": {
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                            "checked_at": "2026-03-01T00:00:00",
                        },
                        "https://github.com/octo/old": {
                            "full_name": "octo/old",
                            "url": "https://github.com/octo/old",
                            "checked_at": "2026-03-01T00:00:00",
                        },
                    },
                    "favorite_updates": [
                        {
                            "id": "new-update",
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                            "checked_at": "2026-03-02T00:00:00",
                            "changes": ["release"],
                        },
                        {
                            "id": "old-update",
                            "full_name": "octo/old",
                            "url": "https://github.com/octo/old",
                            "checked_at": "2026-03-02T00:00:00",
                            "changes": ["release"],
                        },
                    ],
                },
            }
        )

        state = result["user_state"]
        self.assertEqual(state["favorites"], ["https://github.com/octo/new"])
        self.assertEqual(state["watch_later"], [])
        self.assertEqual(state["read"], ["https://github.com/octo/readme"])
        self.assertEqual(list(state["favorite_watch"].keys()), ["https://github.com/octo/new"])
        self.assertEqual([item["id"] for item in state["favorite_updates"]], ["new-update"])
        self.assertEqual(result["mode"], "replace")

    def test_import_user_state_trims_favorite_updates_to_hundred_items(self):
        runtime = build_state_runtime()
        updates = [
            {
                "id": f"update-{index:03d}",
                "full_name": "octo/new",
                "url": "https://github.com/octo/new",
                "checked_at": f"2026-04-01T00:{index % 60:02d}:00",
                "changes": [f"change-{index:03d}"],
            }
            for index in range(120)
        ]

        result = runtime.import_user_state(
            {
                "mode": "replace",
                "user_state": {
                    "favorites": ["https://github.com/octo/new"],
                    "repo_records": {
                        "https://github.com/octo/new": {
                            "full_name": "octo/new",
                            "url": "https://github.com/octo/new",
                        }
                    },
                    "favorite_updates": updates,
                },
            }
        )

        favorite_updates = result["user_state"]["favorite_updates"]
        self.assertEqual(len(favorite_updates), 100)
        self.assertEqual(favorite_updates[0]["id"], "update-000")
        self.assertEqual(favorite_updates[-1]["id"], "update-099")


if __name__ == "__main__":
    unittest.main()
