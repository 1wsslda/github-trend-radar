from __future__ import annotations

import base64
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

from gitsonar.runtime.discovery_jobs import make_discovery_job_runtime
from gitsonar.runtime.state import make_state_runtime
from gitsonar.runtime_github import make_github_runtime
from gitsonar.runtime.utils import clamp_int, extract_count, iso_now, normalize, parse_iso_timestamp, strip_markdown


class _DummySession:
    def get(self, *args, **kwargs):
        raise AssertionError("network should not be used in discovery scoring tests")


class _DummyGitHubRuntime:
    DiscoveryCancelledError = RuntimeError

    def discover_repos(self, **_kwargs):
        raise AssertionError("discover_repos should not run in discovery query tests")


class _SearchResponse:
    def __init__(self, items: list[dict[str, object]]):
        self.status_code = 200
        self._items = list(items)

    def raise_for_status(self):
        return None

    def json(self):
        return {"items": list(self._items)}


class _RecordingSearchSession:
    def __init__(self, items: list[dict[str, object]]):
        self._items = list(items)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs):
        self.calls.append((url, dict(kwargs)))
        return _SearchResponse(self._items)


class _JsonResponse:
    def __init__(self, payload: dict[str, object]):
        self.status_code = 200
        self._payload = dict(payload)

    def raise_for_status(self):
        return None

    def json(self):
        return dict(self._payload)


class _DiscoveryDetailsSession:
    def __init__(
        self,
        *,
        search_api_url: str,
        repo_api_url: str,
        search_items: list[dict[str, object]],
        repo_payloads: dict[str, dict[str, object]],
        readme_payloads: dict[str, dict[str, object]] | None = None,
    ):
        self.search_api_url = search_api_url
        self.repo_api_url = repo_api_url
        self.search_items = list(search_items)
        self.repo_payloads = {key.lower(): dict(value) for key, value in repo_payloads.items()}
        self.readme_payloads = {key.lower(): dict(value) for key, value in (readme_payloads or {}).items()}
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs):
        self.calls.append((url, dict(kwargs)))
        if url == self.search_api_url:
            return _SearchResponse(self.search_items)
        prefix = f"{self.repo_api_url}/"
        if not url.startswith(prefix):
            raise AssertionError(f"unexpected GET {url}")
        suffix = url[len(prefix):]
        if suffix.endswith("/readme"):
            repo_key = suffix[:-7].lower()
            return _JsonResponse(self.readme_payloads.get(repo_key, {}))
        return _JsonResponse(self.repo_payloads[suffix.lower()])


def _normalize_repo_stub(repo):
    if not isinstance(repo, dict):
        return None
    full_name = normalize(repo.get("full_name"))
    url = normalize(repo.get("url"))
    if not full_name or not url:
        return None
    clean = dict(repo)
    clean["full_name"] = full_name
    clean["url"] = url
    if "/" in full_name:
        owner, name = full_name.split("/", 1)
        clean.setdefault("owner", owner)
        clean.setdefault("name", name)
    return clean


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
        as_bool=lambda value, default=False: default if value is None else bool(value),
        iso_now=iso_now,
        load_json_file=lambda _path, default: default,
        atomic_write_json=lambda _path, _payload: None,
        apply_repo_translation=lambda _repo: None,
    )


def build_discovery_job_runtime(settings: dict[str, object], state_runtime):
    return make_discovery_job_runtime(
        settings=settings,
        normalize=normalize,
        clamp_int=clamp_int,
        as_bool=lambda value, default=False: default if value is None else bool(value),
        iso_now=iso_now,
        normalize_repo=state_runtime.normalize_repo,
        normalize_discovery_query=state_runtime.normalize_discovery_query,
        apply_discovery_result=state_runtime.apply_discovery_result,
        discovery_warning_list=state_runtime.discovery_warning_list,
        github_runtime=_DummyGitHubRuntime(),
        job_lock=threading.RLock(),
    )


def build_runtime(
    session=None,
    search_api_url: str = "https://example.invalid/search",
    token: str = "",
    *,
    cached_repo_details=None,
    save_repo_details=None,
    translate_text=None,
    translate_query_to_en=None,
    save_translation_cache=None,
    flush_translation_cache=None,
    flush_repo_details_cache=None,
):
    return make_github_runtime(
        session=session or _DummySession(),
        api_timeout=(1, 1),
        trending_timeout=(1, 1),
        search_api_url=search_api_url,
        repo_api_url="https://example.invalid/repos",
        settings={"github_token": token},
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
        cached_repo_details=cached_repo_details or (lambda _cache_key: None),
        detail_fetch_lock=lambda _cache_key: threading.RLock(),
        strip_markdown=strip_markdown,
        translate_text=translate_text or (lambda text: normalize(text)),
        translate_query_to_en=translate_query_to_en or (lambda text: normalize(text)),
        save_translation_cache=save_translation_cache or (lambda: None),
        flush_translation_cache=flush_translation_cache or (lambda: False),
        save_repo_details=save_repo_details or (lambda _cache_key, _details: None),
        flush_repo_details_cache=flush_repo_details_cache or (lambda: False),
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
        self.settings = {"result_limit": 25, "github_token": ""}
        self.state_runtime = build_state_runtime(self.settings)
        self.discovery_job_runtime = build_discovery_job_runtime(self.settings, self.state_runtime)

    def test_query_id_changes_with_ranking_profile(self):
        balanced = self.state_runtime.discovery_query_id("agent", True, "balanced")
        hot = self.state_runtime.discovery_query_id("agent", True, "hot")
        self.assertNotEqual(balanced, hot)

    def test_normalize_discovery_query_keeps_ranking_profile_and_drops_language(self):
        query = self.state_runtime.normalize_discovery_query(
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
        self.assertNotIn("language", query)
        self.assertEqual(
            query["id"],
            self.state_runtime.normalize_discovery_query(
                {"query": "agent", "limit": 30, "auto_expand": True, "ranking_profile": "builder"}
            )["id"],
        )

    def test_normalize_discovery_query_falls_back_to_balanced(self):
        query = self.state_runtime.normalize_discovery_query({"query": "agent", "ranking_profile": "unknown"})
        self.assertIsNotNone(query)
        self.assertEqual(query["ranking_profile"], "balanced")

    def test_normalize_discovery_query_accepts_limits_up_to_one_hundred(self):
        query = self.state_runtime.normalize_discovery_query({"query": "agent", "limit": 120})
        self.assertIsNotNone(query)
        self.assertEqual(query["limit"], 100)

    def test_normalize_discovery_state_drops_saved_queries_and_language(self):
        state = self.state_runtime.normalize_discovery_state(
            {
                "saved_queries": [{"query": "legacy", "language": "Python"}],
                "remembered_query": {"query": "default", "language": "TypeScript", "limit": 10},
                "last_query": {"query": "latest", "language": "Python", "limit": 15},
            }
        )
        self.assertNotIn("saved_queries", state)
        self.assertEqual(state["remembered_query"]["query"], "default")
        self.assertEqual(state["last_query"]["query"], "latest")
        self.assertNotIn("language", state["remembered_query"])
        self.assertNotIn("language", state["last_query"])

    def test_normalize_repo_round_trip_preserves_shared_schema(self):
        repo = self.state_runtime.normalize_repo(
            {
                "full_name": "octo/agent-kit",
                "url": "https://github.com/octo/agent-kit",
                "description": "Agent toolkit",
                "description_raw": "Agent toolkit",
                "language": "Python",
                "stars": 1200,
                "forks": 90,
                "gained": 12,
                "gained_text": "+12 today",
                "growth_source": "trending",
                "rank": 3,
                "period_key": "discover",
                "source_label": "Keyword Discovery",
                "source_key": "discover",
                "discover_source": "keyword-discovery",
                "trending_hit": True,
                "relevance_score": 84,
                "hot_score": 72,
                "composite_score": 79,
                "matched_terms": ["agent", "kit"],
                "match_reasons": ["name hit", "recent activity"],
                "ranking_profile": "builder",
                "ranking_signal_score": 68,
            }
        )

        self.assertIsNotNone(repo)
        self.assertEqual(repo["owner"], "octo")
        self.assertEqual(repo["name"], "agent-kit")
        self.assertEqual(repo["source_key"], "discover")
        self.assertEqual(repo["ranking_profile"], "builder")
        self.assertEqual(self.state_runtime.normalize_repo(repo), repo)

    def test_estimate_discovery_eta_is_slower_without_token_and_with_expansion(self):
        base_payload = {
            "query": "agent",
            "limit": 25,
            "auto_expand": True,
        }
        no_token_initial, no_token_full = self.discovery_job_runtime.estimate_discovery_eta(base_payload)
        self.settings["github_token"] = "token"
        token_initial, token_full = self.discovery_job_runtime.estimate_discovery_eta(base_payload)
        self.assertGreater(no_token_initial, token_initial)
        self.assertGreater(no_token_full, token_full)
        compact_initial, compact_full = self.discovery_job_runtime.estimate_discovery_eta({**base_payload, "auto_expand": False})
        self.assertGreater(no_token_full, compact_full)
        self.assertGreaterEqual(no_token_full, no_token_initial + 2)

    def test_estimate_discovery_eta_keeps_scaling_past_fifty_results(self):
        medium_initial, medium_full = self.discovery_job_runtime.estimate_discovery_eta({"query": "agent", "limit": 50, "auto_expand": True})
        large_initial, large_full = self.discovery_job_runtime.estimate_discovery_eta({"query": "agent", "limit": 80, "auto_expand": True})
        max_initial, max_full = self.discovery_job_runtime.estimate_discovery_eta({"query": "agent", "limit": 100, "auto_expand": True})

        self.assertGreater(large_initial, medium_initial)
        self.assertGreater(large_full, medium_full)
        self.assertGreater(max_initial, large_initial)
        self.assertGreater(max_full, large_full)


class DiscoveryRankingProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = build_runtime()

    def test_discover_repos_preserves_legacy_language_filter_with_injected_search_api_url(self):
        search_api_url = "https://example.invalid/custom-search"
        session = _RecordingSearchSession(
            [
                {
                    "full_name": "octo/ui-kit",
                    "html_url": "https://github.com/octo/ui-kit",
                    "description": "UI toolkit",
                    "language": "TypeScript",
                    "stargazers_count": 1200,
                    "forks_count": 88,
                    "updated_at": "2026-04-01T00:00:00Z",
                    "pushed_at": "2026-04-01T00:00:00Z",
                    "topics": ["ui", "design-system"],
                }
            ]
        )
        runtime = build_runtime(session=session, search_api_url=search_api_url)

        payload = runtime.discover_repos(query="UI", language="TypeScript", limit=5, auto_expand=False)

        self.assertTrue(payload["results"])
        self.assertEqual(payload["results"][0]["full_name"], "octo/ui-kit")
        self.assertGreaterEqual(len(session.calls), 2)
        self.assertTrue(all(url == search_api_url for url, _kwargs in session.calls))
        for _url, kwargs in session.calls:
            self.assertIn("params", kwargs)
            self.assertEqual(kwargs["params"]["per_page"], 18)
            self.assertIn("q", kwargs["params"])
            self.assertIn("language:TypeScript", kwargs["params"]["q"])

    def test_discover_repos_allows_up_to_one_hundred_results_per_search_request(self):
        session = _RecordingSearchSession(
            [
                {
                    "full_name": "octo/scale-search",
                    "html_url": "https://github.com/octo/scale-search",
                    "description": "Scaled search",
                    "language": "Python",
                    "stargazers_count": 1200,
                    "forks_count": 88,
                    "updated_at": "2026-04-01T00:00:00Z",
                    "pushed_at": "2026-04-01T00:00:00Z",
                    "topics": ["agent", "search"],
                }
            ]
        )
        runtime = build_runtime(session=session)

        payload = runtime.discover_repos(query="agent", limit=100, auto_expand=False)

        self.assertEqual(payload["results"][0]["full_name"], "octo/scale-search")
        self.assertGreaterEqual(len(session.calls), 2)
        for _url, kwargs in session.calls:
            self.assertEqual(kwargs["params"]["per_page"], 100)

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


class DiscoveryDetailPersistenceTests(unittest.TestCase):
    def test_discover_repos_flushes_translation_and_detail_caches_once(self):
        search_api_url = "https://example.invalid/search"
        repo_api_url = "https://example.invalid/repos"
        repo_payload = {
            "full_name": "octo/agent-kit",
            "html_url": "https://github.com/octo/agent-kit",
            "description": "Agent toolkit",
            "license": {"spdx_id": "MIT"},
            "default_branch": "main",
            "updated_at": "2026-04-01T00:00:00Z",
            "pushed_at": "2026-04-01T00:00:00Z",
            "topics": ["agent", "automation"],
            "homepage": "https://example.com",
            "stargazers_count": 1200,
            "forks_count": 88,
            "watchers_count": 90,
            "open_issues_count": 3,
        }
        session = _DiscoveryDetailsSession(
            search_api_url=search_api_url,
            repo_api_url=repo_api_url,
            search_items=[
                {
                    "full_name": "octo/agent-kit",
                    "html_url": "https://github.com/octo/agent-kit",
                    "description": "Agent toolkit",
                    "language": "Python",
                    "stargazers_count": 1200,
                    "forks_count": 88,
                    "updated_at": "2026-04-01T00:00:00Z",
                    "pushed_at": "2026-04-01T00:00:00Z",
                    "topics": ["agent", "automation"],
                }
            ],
            repo_payloads={"octo/agent-kit": repo_payload},
            readme_payloads={
                "octo/agent-kit": {
                    "encoding": "base64",
                    "content": base64.b64encode(b"Agent toolkit with docs").decode("ascii"),
                }
            },
        )
        detail_cache: dict[str, dict[str, object]] = {}
        translation_flush_calls: list[str] = []
        detail_flush_calls: list[str] = []
        runtime = build_runtime(
            session=session,
            search_api_url=search_api_url,
            token="token",
            cached_repo_details=lambda cache_key: dict(detail_cache[cache_key]) if cache_key in detail_cache else None,
            save_repo_details=lambda cache_key, details: detail_cache.__setitem__(cache_key, dict(details)),
            flush_translation_cache=lambda: translation_flush_calls.append("flush") or True,
            flush_repo_details_cache=lambda: detail_flush_calls.append("flush") or True,
        )

        payload = runtime.discover_repos(query="agent", limit=5, auto_expand=False)

        self.assertEqual(payload["results"][0]["full_name"], "octo/agent-kit")
        self.assertEqual(translation_flush_calls, ["flush"])
        self.assertEqual(detail_flush_calls, ["flush"])

    def test_fetch_repo_details_flushes_caches_immediately(self):
        repo_api_url = "https://example.invalid/repos"
        session = _DiscoveryDetailsSession(
            search_api_url="https://example.invalid/search",
            repo_api_url=repo_api_url,
            search_items=[],
            repo_payloads={
                "octo/agent-kit": {
                    "full_name": "octo/agent-kit",
                    "html_url": "https://github.com/octo/agent-kit",
                    "description": "Agent toolkit",
                    "license": {"spdx_id": "MIT"},
                    "default_branch": "main",
                    "updated_at": "2026-04-01T00:00:00Z",
                    "pushed_at": "2026-04-01T00:00:00Z",
                    "topics": ["agent"],
                    "homepage": "https://example.com",
                    "stargazers_count": 1200,
                    "forks_count": 88,
                    "watchers_count": 90,
                    "open_issues_count": 3,
                }
            },
            readme_payloads={
                "octo/agent-kit": {
                    "encoding": "base64",
                    "content": base64.b64encode(b"Agent toolkit with docs").decode("ascii"),
                }
            },
        )
        detail_cache: dict[str, dict[str, object]] = {}
        translation_flush_calls: list[str] = []
        detail_flush_calls: list[str] = []
        runtime = build_runtime(
            session=session,
            token="token",
            cached_repo_details=lambda cache_key: dict(detail_cache[cache_key]) if cache_key in detail_cache else None,
            save_repo_details=lambda cache_key, details: detail_cache.__setitem__(cache_key, dict(details)),
            flush_translation_cache=lambda: translation_flush_calls.append("flush") or True,
            flush_repo_details_cache=lambda: detail_flush_calls.append("flush") or True,
        )

        details = runtime.fetch_repo_details("octo", "agent-kit")

        self.assertEqual(details["full_name"], "octo/agent-kit")
        self.assertEqual(translation_flush_calls, ["flush"])
        self.assertEqual(detail_flush_calls, ["flush"])


if __name__ == "__main__":
    unittest.main()
