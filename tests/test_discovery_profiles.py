from __future__ import annotations

import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar import app_runtime
from gitsonar.runtime_github import make_github_runtime
from gitsonar.runtime_utils import clamp_int, extract_count, iso_now, normalize, parse_iso_timestamp, strip_markdown


class _DummySession:
    def get(self, *args, **kwargs):
        raise AssertionError("network should not be used in discovery scoring tests")


def _normalize_repo_stub(repo):
    if not isinstance(repo, dict):
        return None
    full_name = normalize(repo.get("full_name"))
    url = normalize(repo.get("url"))
    if not full_name or not url:
        return None
    return dict(repo)


def build_runtime():
    return make_github_runtime(
        session=_DummySession(),
        api_timeout=(1, 1),
        trending_timeout=(1, 1),
        search_api_url="https://example.invalid/search",
        repo_api_url="https://example.invalid/repos",
        settings={"github_token": ""},
        periods=[{"key": "daily", "label": "Today", "days": 1}],
        state_lock=threading.RLock(),
        user_state={},
        save_user_state=lambda: None,
        requests_module=None,
        beautifulsoup_cls=lambda *args, **kwargs: None,
        thread_pool_executor_cls=ThreadPoolExecutor,
        as_completed=as_completed,
        datetime_cls=datetime,
        timedelta_cls=timedelta,
        normalize=normalize,
        clamp_int=clamp_int,
        extract_count=extract_count,
        normalize_repo=_normalize_repo_stub,
        repo_from_url=lambda url: None,
        normalize_watch_entry=lambda entry: entry,
        normalize_favorite_update=lambda entry: entry,
        translate_snapshot=lambda snapshot: snapshot,
        load_snapshot=lambda: {},
        cached_repo_details={},
        detail_fetch_lock=threading.RLock(),
        strip_markdown=strip_markdown,
        translate_text=lambda text: normalize(text),
        translate_query_to_en=lambda text: normalize(text),
        save_translation_cache=lambda: None,
        save_repo_details=lambda: None,
        parse_iso_timestamp=parse_iso_timestamp,
        iso_now=iso_now,
        fetch_semaphore=threading.Semaphore(1),
        favorite_watch_min_seconds_no_token=60,
        favorite_watch_min_seconds_with_token=30,
        favorite_release_min_seconds_no_token=60,
        favorite_release_min_seconds_with_token=30,
        favorite_watch_max_checks_no_token=2,
        favorite_watch_max_checks_with_token=4,
    )


class DiscoveryQueryTests(unittest.TestCase):
    def setUp(self):
        self._settings = dict(app_runtime.SETTINGS)
        app_runtime.SETTINGS.clear()
        app_runtime.SETTINGS.update({"result_limit": 25, "github_token": ""})

    def tearDown(self):
        app_runtime.SETTINGS.clear()
        app_runtime.SETTINGS.update(self._settings)

    def test_query_id_changes_with_ranking_profile(self):
        balanced = app_runtime.discovery_query_id("agent", "Python", True, "balanced")
        hot = app_runtime.discovery_query_id("agent", "Python", True, "hot")
        self.assertNotEqual(balanced, hot)

    def test_normalize_discovery_query_keeps_ranking_profile(self):
        query = app_runtime.normalize_discovery_query(
            {
                "query": "agent",
                "language": "Python",
                "limit": 30,
                "auto_expand": True,
                "ranking_profile": "builder",
            }
        )
        self.assertIsNotNone(query)
        self.assertEqual(query["ranking_profile"], "builder")
        self.assertEqual(query["limit"], 30)

    def test_normalize_discovery_query_falls_back_to_balanced(self):
        query = app_runtime.normalize_discovery_query({"query": "agent", "ranking_profile": "unknown"})
        self.assertIsNotNone(query)
        self.assertEqual(query["ranking_profile"], "balanced")

    def test_estimate_discovery_eta_is_slower_without_token_and_with_expansion(self):
        base_payload = {
            "query": "agent",
            "language": "Python",
            "limit": 25,
            "auto_expand": True,
        }
        no_token_initial, no_token_full = app_runtime.estimate_discovery_eta(base_payload)
        app_runtime.SETTINGS["github_token"] = "token"
        token_initial, token_full = app_runtime.estimate_discovery_eta(base_payload)
        self.assertGreater(no_token_initial, token_initial)
        self.assertGreater(no_token_full, token_full)
        compact_initial, compact_full = app_runtime.estimate_discovery_eta({**base_payload, "auto_expand": False})
        self.assertGreater(no_token_full, compact_full)
        self.assertGreaterEqual(no_token_full, no_token_initial + 2)


class DiscoveryRankingProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = build_runtime()

    def test_ranking_profiles_reorder_candidates(self):
        recent_iso = (datetime.now(timezone.utc) - timedelta(days=70)).isoformat().replace("+00:00", "Z")
        stale_iso = (datetime.now(timezone.utc) - timedelta(days=240)).isoformat().replace("+00:00", "Z")
        repos = [
            {
                "full_name": "alpha/agent-hot",
                "name": "agent-hot",
                "url": "https://github.com/alpha/agent-hot",
                "description_raw": "Agent toolkit",
                "language": "Python",
                "stars": 50000,
                "forks": 6000,
                "updated_at": stale_iso,
                "pushed_at": stale_iso,
            },
            {
                "full_name": "beta/agent-builder",
                "name": "agent-builder",
                "url": "https://github.com/beta/agent-builder",
                "description_raw": "Agent framework with docs",
                "language": "TypeScript",
                "stars": 900,
                "forks": 120,
                "updated_at": recent_iso,
                "pushed_at": recent_iso,
            },
        ]
        details_map = {
            "alpha/agent-hot": {
                "stars": 50000,
                "forks": 6000,
                "updated_at": stale_iso,
                "pushed_at": stale_iso,
                "topics": [],
                "license": "",
                "homepage": "",
                "readme_summary": "",
                "readme_summary_raw": "",
            },
            "beta/agent-builder": {
                "stars": 900,
                "forks": 120,
                "updated_at": recent_iso,
                "pushed_at": recent_iso,
                "topics": ["agent", "workflow", "automation"],
                "license": "MIT",
                "homepage": "https://example.com",
                "readme_summary": "Agent framework docs and examples",
                "readme_summary_raw": "Agent framework docs and examples",
            },
        }
        common = {
            "repos": repos,
            "details_map": details_map,
            "base_terms": ["agent"],
            "search_variants": ["agent"],
            "query_variants": ["agent"],
            "related_terms": [],
            "trending_names": set(),
            "limit": 2,
        }

        hot_ranked = self.runtime.rank_discovery_results(ranking_profile="hot", **common)
        builder_ranked = self.runtime.rank_discovery_results(ranking_profile="builder", **common)
        fresh_ranked = self.runtime.rank_discovery_results(ranking_profile="fresh", **common)
        trend_ranked = self.runtime.rank_discovery_results(ranking_profile="trend", **common)

        self.assertEqual(hot_ranked[0]["full_name"], "alpha/agent-hot")
        self.assertEqual(builder_ranked[0]["full_name"], "beta/agent-builder")
        self.assertEqual(fresh_ranked[0]["full_name"], "beta/agent-builder")
        self.assertEqual(trend_ranked[0]["full_name"], "beta/agent-builder")

    def test_scoring_exposes_profile_specific_signal(self):
        recent_iso = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat().replace("+00:00", "Z")
        repo = {
            "full_name": "gamma/agent-kit",
            "name": "agent-kit",
            "url": "https://github.com/gamma/agent-kit",
            "description_raw": "Agent toolkit",
            "language": "Python",
            "stars": 1200,
            "forks": 90,
            "updated_at": recent_iso,
            "pushed_at": recent_iso,
        }
        details = {
            "stars": 1200,
            "forks": 90,
            "updated_at": recent_iso,
            "pushed_at": recent_iso,
            "topics": ["agent", "toolkit"],
            "license": "Apache-2.0",
            "homepage": "https://example.com",
            "readme_summary": "Agent toolkit with docs",
            "readme_summary_raw": "Agent toolkit with docs",
        }

        hot = self.runtime.score_discovery_repo(
            repo,
            details,
            base_terms=["agent"],
            query_variants=["agent"],
            related_terms=["toolkit"],
            trending_names=set(),
            ranking_profile="hot",
        )
        builder = self.runtime.score_discovery_repo(
            repo,
            details,
            base_terms=["agent"],
            query_variants=["agent"],
            related_terms=["toolkit"],
            trending_names=set(),
            ranking_profile="builder",
        )
        fresh = self.runtime.score_discovery_repo(
            repo,
            details,
            base_terms=["agent"],
            query_variants=["agent"],
            related_terms=["toolkit"],
            trending_names=set(),
            ranking_profile="fresh",
        )

        self.assertEqual(hot["ranking_profile"], "hot")
        self.assertEqual(builder["ranking_profile"], "builder")
        self.assertEqual(fresh["ranking_profile"], "fresh")
        self.assertNotEqual(hot["composite_score"], builder["composite_score"])
        self.assertNotEqual(builder["ranking_signal_score"], hot["ranking_signal_score"])
        self.assertNotEqual(fresh["ranking_signal_score"], hot["ranking_signal_score"])


if __name__ == "__main__":
    unittest.main()
