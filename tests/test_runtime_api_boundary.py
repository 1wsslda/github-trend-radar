from __future__ import annotations

import sys
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.api_boundary import make_api_boundary_runtime
from gitsonar.runtime.utils import normalize


class RuntimeAPIBoundaryTests(unittest.TestCase):
    def build_runtime(self, *, status: dict[str, object] | None = None):
        snapshot = {
            "fetched_at": "2026-04-24T10:00:00",
            "daily": [
                {
                    "full_name": "octo/daily",
                    "url": "https://github.com/octo/daily",
                    "description": "Daily repo",
                    "language": "Python",
                    "stars": 100,
                    "forks": 10,
                }
            ],
            "weekly": [],
        }
        user_state = {
            "favorites": ["https://github.com/octo/daily"],
            "watch_later": ["https://github.com/octo/local"],
            "read": [],
            "ignored": [],
            "repo_records": {
                "https://github.com/octo/daily": {
                    "full_name": "octo/daily",
                    "url": "https://github.com/octo/daily",
                    "description": "Daily repo",
                    "language": "Python",
                    "stars": 100,
                    "forks": 10,
                },
                "https://github.com/octo/local": {
                    "full_name": "octo/local",
                    "url": "https://github.com/octo/local",
                    "description": "Local repo",
                    "language": "TypeScript",
                    "stars": 12,
                    "forks": 2,
                },
            },
            "favorite_updates": [
                {
                    "id": "update-1",
                    "full_name": "octo/daily",
                    "url": "https://github.com/octo/daily",
                    "changes": ["release"],
                    "pinned": True,
                    "read_at": "",
                    "dismissed_at": "",
                }
            ],
        }
        discovery_state = {
            "last_results": [
                {
                    "full_name": "octo/discovered",
                    "url": "https://github.com/octo/discovered",
                    "description": "Discovery repo",
                    "language": "Rust",
                    "stars": 50,
                    "forks": 5,
                }
            ],
            "last_clusters": [
                {
                    "id": "cluster-rust",
                    "label": "Rust",
                    "count": 1,
                    "repo_urls": ["https://github.com/octo/discovered"],
                    "top_terms": ["rust"],
                    "languages": ["Rust"],
                }
            ],
            "saved_views": [
                {
                    "id": "view-1",
                    "name": "Agents",
                    "query": "agent",
                    "limit": 20,
                    "auto_expand": True,
                    "ranking_profile": "balanced",
                }
            ],
        }
        return make_api_boundary_runtime(
            periods=[{"key": "daily", "label": "Today"}, {"key": "weekly", "label": "Week"}],
            current_snapshot_getter=lambda: snapshot,
            export_user_state=lambda: user_state,
            export_discovery_state=lambda: discovery_state,
            sanitize_settings=lambda _include_sensitive=False: {"has_github_token": True, "github_token": ""},
            status_getter=lambda: status or {"refreshing": False, "fetched_at": "2026-04-24T10:00:00"},
            normalize=normalize,
        )

    def test_bootstrap_returns_sanitized_settings_and_counts(self):
        payload = self.build_runtime().export_bootstrap()

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["settings"]["github_token"], "")
        self.assertEqual(payload["counts"]["repos"], 3)
        self.assertEqual(payload["counts"]["favorite_updates"], 1)
        self.assertEqual(payload["discovery"]["saved_view_count"], 1)
        self.assertEqual(payload["discovery"]["cluster_count"], 1)

    def test_repos_endpoint_payload_filters_by_view_state_and_query(self):
        runtime = self.build_runtime()

        self.assertEqual([item["full_name"] for item in runtime.export_repos(view="daily")["repos"]], ["octo/daily"])
        self.assertEqual([item["full_name"] for item in runtime.export_repos(view="discover")["repos"]], ["octo/discovered"])
        self.assertEqual([item["full_name"] for item in runtime.export_repos(state="watch_later")["repos"]], ["octo/local"])
        self.assertEqual([item["full_name"] for item in runtime.export_repos(q="rust")["repos"]], ["octo/discovered"])

    def test_updates_and_discovery_views_are_exposed_as_read_only_payloads(self):
        runtime = self.build_runtime()

        self.assertEqual(runtime.export_updates()["updates"][0]["id"], "update-1")
        self.assertEqual(runtime.export_discovery_views()["views"][0]["name"], "Agents")

    def test_bootstrap_status_error_is_user_safe(self):
        runtime = self.build_runtime(
            status={
                "refreshing": False,
                "fetched_at": "old",
                "error": "ghp_secret_token http://user:pass@127.0.0.1:7890 C:\\Users\\liushun\\runtime-data",
            }
        )

        payload = runtime.export_bootstrap()
        payload_text = json.dumps(payload, ensure_ascii=False)

        self.assertTrue(payload["status"]["error"])
        self.assertNotIn("ghp_secret_token", payload_text)
        self.assertNotIn("user:pass", payload_text)
        self.assertNotIn("C:\\Users\\liushun", payload_text)


if __name__ == "__main__":
    unittest.main()
