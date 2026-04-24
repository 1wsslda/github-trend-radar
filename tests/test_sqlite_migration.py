from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.sqlite_migration import (
    SQLITE_SCHEMA_VERSION,
    create_sqlite_schema,
    dry_run_sqlite_migration,
    sqlite_migration_file_plan,
)


class SQLiteMigrationSkeletonTests(unittest.TestCase):
    def test_schema_creates_phase_one_tables_and_update_fields(self):
        connection = sqlite3.connect(":memory:")

        create_sqlite_schema(connection)

        self.assertEqual(SQLITE_SCHEMA_VERSION, 1)
        tables = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"
            )
        }
        self.assertTrue(
            {
                "schema_meta",
                "repos",
                "repo_snapshots",
                "user_repo_state",
                "repo_annotations",
                "favorite_watch",
                "update_events",
                "feedback_signals",
                "discovery_views",
                "discovery_runs",
                "discovery_results",
                "ai_artifacts",
                "settings_kv",
            }.issubset(tables)
        )
        update_columns = {row[1] for row in connection.execute("pragma table_info(update_events)")}
        for column in (
            "id",
            "repo_id",
            "changes_json",
            "change_summary",
            "importance_reason",
            "priority_score",
            "read_at",
            "dismissed_at",
            "pinned",
            "checked_at",
        ):
            with self.subTest(column=column):
                self.assertIn(column, update_columns)

    def test_dry_run_counts_json_state_and_excludes_sensitive_settings(self):
        result = dry_run_sqlite_migration(
            user_state={
                "favorites": ["https://github.com/octo/a"],
                "watch_later": ["https://github.com/octo/b"],
                "read": [],
                "ignored": [],
                "repo_records": {
                    "https://github.com/octo/a": {
                        "full_name": "octo/a",
                        "url": "https://github.com/octo/a",
                    },
                    "https://github.com/octo/b": {
                        "full_name": "octo/b",
                        "url": "https://github.com/octo/b",
                    },
                },
                "repo_annotations": {
                    "https://github.com/octo/a": {"tags": ["agent"], "note": "重点跟踪"}
                },
                "favorite_watch": {
                    "https://github.com/octo/a": {
                        "full_name": "octo/a",
                        "url": "https://github.com/octo/a",
                        "checked_at": "2026-04-24T10:00:00",
                    }
                },
                "favorite_updates": [
                    {
                        "id": "update-1",
                        "full_name": "octo/a",
                        "url": "https://github.com/octo/a",
                        "checked_at": "2026-04-24T11:00:00",
                        "changes": ["星标 +12"],
                        "change_summary": "星标 +12",
                        "importance_reason": "星标增长明显，说明近期关注度正在上升。",
                    }
                ],
                "feedback_signals": {
                    "https://github.com/octo/b": {"reason": "只是 demo", "count": 1, "state": "ignored"}
                },
                "ai_insights": {
                    "https://github.com/octo/a": {
                        "schema_version": "gitsonar.repo_insight.v1",
                        "summary": "适合研究",
                    }
                },
            },
            discovery_state={
                "saved_views": [
                    {
                        "id": "view-1",
                        "name": "Agent",
                        "query": "agent",
                        "limit": 25,
                        "ranking_profile": "balanced",
                    }
                ],
                "last_query": {"query": "agent", "limit": 25},
                "last_results": [
                    {
                        "full_name": "octo/c",
                        "url": "https://github.com/octo/c",
                    }
                ],
                "last_run_at": "2026-04-24T12:00:00",
                "last_warnings": ["rate limited"],
            },
            latest_snapshot={
                "fetched_at": "2026-04-24T09:00:00",
                "daily": [
                    {
                        "full_name": "octo/d",
                        "url": "https://github.com/octo/d",
                    }
                ],
            },
            settings={
                "github_token": "ghp_secret",
                "proxy_url": "http://user:pass@127.0.0.1:7890",
                "refresh_hours": 2,
                "result_limit": 25,
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["counts"]["repos"], 4)
        self.assertEqual(result["counts"]["user_repo_state"], 2)
        self.assertEqual(result["counts"]["repo_annotations"], 1)
        self.assertEqual(result["counts"]["favorite_watch"], 1)
        self.assertEqual(result["counts"]["favorite_updates"], 1)
        self.assertEqual(result["counts"]["feedback_signals"], 1)
        self.assertEqual(result["counts"]["discovery_views"], 1)
        self.assertEqual(result["counts"]["discovery_results"], 1)
        self.assertEqual(result["counts"]["ai_artifacts"], 1)
        self.assertEqual(result["settings_keys"], ["refresh_hours", "result_limit"])
        self.assertIn("github_token", result["excluded_sensitive_settings"])
        self.assertIn("proxy_url", result["excluded_sensitive_settings"])
        self.assertTrue(result["validation"]["json_export_compatible"])
        self.assertTrue(result["validation"]["default_storage_unchanged"])
        self.assertTrue(result["validation"]["rollback_export_planned"])

    def test_file_plan_uses_tmp_database_backup_and_rollback_paths(self):
        plan = sqlite_migration_file_plan(
            Path("C:/Users/example/AppData/Local/GitSonar"),
            timestamp="20260424-120000",
        )

        self.assertTrue(plan["database"].endswith("gitsonar.db"))
        self.assertTrue(plan["temporary_database"].endswith("gitsonar.db.tmp"))
        self.assertIn("backups", plan["backup_dir"])
        self.assertIn("rollback-export", plan["rollback_export_dir"])
        self.assertTrue(plan["backup_files"]["user_state"].endswith("user_state.json"))
        self.assertTrue(plan["backup_files"]["discovery_state"].endswith("discovery_state.json"))
        self.assertTrue(plan["backup_files"]["latest_snapshot"].endswith("latest.json"))


if __name__ == "__main__":
    unittest.main()
