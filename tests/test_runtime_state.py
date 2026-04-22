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
            "repo_annotations": {},
            "favorite_watch": {},
            "favorite_updates": [],
            "feedback_signals": {},
            "ai_insights": {},
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


class RuntimeStateFeatureTests(unittest.TestCase):
    def test_set_repo_annotation_round_trip_and_clear(self):
        runtime = build_state_runtime()
        repo = {"full_name": "octo/demo", "url": "https://github.com/octo/demo"}

        annotation = runtime.set_repo_annotation(
            "https://github.com/octo/demo",
            {"tags": ["agent", "tooling", "agent"], "note": "  值得二刷  "},
            repo=repo,
        )

        self.assertEqual(annotation["tags"], ["agent", "tooling"])
        self.assertEqual(annotation["note"], "值得二刷")
        self.assertEqual(runtime.export_user_state()["repo_annotations"]["https://github.com/octo/demo"]["note"], "值得二刷")

        cleared = runtime.set_repo_annotation("https://github.com/octo/demo", {"tags": [], "note": ""})

        self.assertIsNone(cleared)
        self.assertEqual(runtime.export_user_state()["repo_annotations"], {})

    def test_set_repo_state_ignored_records_feedback_signal(self):
        runtime = build_state_runtime()

        runtime.set_repo_state(
            "ignored",
            True,
            {
                "full_name": "octo/demo",
                "url": "https://github.com/octo/demo",
                "feedback_reason": "只是 demo",
            },
        )

        signal = runtime.export_user_state()["feedback_signals"]["https://github.com/octo/demo"]
        self.assertEqual(signal["reason"], "只是 demo")
        self.assertEqual(signal["count"], 1)
        self.assertEqual(signal["state"], "ignored")

    def test_set_favorite_update_state_updates_flags(self):
        runtime = build_state_runtime(
            user_state={
                "favorites": ["https://github.com/octo/demo"],
                "watch_later": [],
                "read": [],
                "ignored": [],
                "repo_records": {
                    "https://github.com/octo/demo": {
                        "full_name": "octo/demo",
                        "url": "https://github.com/octo/demo",
                    }
                },
                "repo_annotations": {},
                "favorite_watch": {},
                "favorite_updates": [
                    {
                        "id": "update-1",
                        "full_name": "octo/demo",
                        "url": "https://github.com/octo/demo",
                        "checked_at": "2026-04-23T00:00:00",
                        "changes": ["release"],
                        "read_at": "",
                        "dismissed_at": "",
                        "pinned": False,
                    }
                ],
                "feedback_signals": {},
                "ai_insights": {},
            }
        )

        update = runtime.set_favorite_update_state("update-1", read=True, dismissed=True, pinned=True)

        self.assertTrue(update["read_at"])
        self.assertTrue(update["dismissed_at"])
        self.assertTrue(update["pinned"])

    def test_save_discovery_view_updates_last_run_metadata_after_results_apply(self):
        runtime = build_state_runtime()

        runtime.save_discovery_view(
            {
                "id": "view-1",
                "name": "Agent Builder",
                "query": "agent",
                "limit": 25,
                "auto_expand": True,
                "ranking_profile": "builder",
            }
        )
        runtime.apply_discovery_result(
            {"id": "view-1", "query": "agent", "limit": 25, "auto_expand": True, "ranking_profile": "builder"},
            {
                "run_at": "2026-04-23T10:00:00",
                "results": [
                    {
                        "full_name": "octo/demo",
                        "url": "https://github.com/octo/demo",
                    }
                ],
            },
            save_query=True,
        )

        saved_view = runtime.export_discovery_state()["saved_views"][0]
        self.assertEqual(saved_view["last_run_at"], "2026-04-23T10:00:00")
        self.assertEqual(saved_view["last_result_count"], 1)

    def test_set_ai_insight_round_trip_and_delete(self):
        runtime = build_state_runtime()
        repo = {"full_name": "octo/demo", "url": "https://github.com/octo/demo"}

        insight = runtime.set_ai_insight(
            "https://github.com/octo/demo",
            {
                "summary": "适合学习工程结构",
                "best_for": ["学习目录划分"],
                "next_actions": ["先看 README"],
            },
            repo=repo,
        )

        self.assertEqual(insight["schema_version"], "gitsonar.repo_insight.v1")
        self.assertEqual(runtime.export_user_state()["ai_insights"]["https://github.com/octo/demo"]["provider"], "manual")

        state = runtime.delete_ai_insight("https://github.com/octo/demo")

        self.assertEqual(state["ai_insights"], {})


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
