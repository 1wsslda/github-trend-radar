from __future__ import annotations

import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_github import make_github_runtime
from gitsonar.runtime.utils import clamp_int, extract_count, iso_now, normalize, parse_iso_timestamp, strip_markdown


class _StubResponse:
    def __init__(self, status_code: int, payload: object | None = None):
        self.status_code = status_code
        self._payload = {} if payload is None else payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _ScriptedSession:
    def __init__(self, responses: dict[str, list[_StubResponse]] | None = None):
        self.responses = {key.upper(): list(value) for key, value in (responses or {}).items()}
        self.calls: list[tuple[str, str]] = []

    def _request(self, method: str, url: str, **_kwargs):
        key = method.upper()
        self.calls.append((key, url))
        queue = self.responses.get(key, [])
        if not queue:
            raise AssertionError(f"unexpected {key} {url}")
        return queue.pop(0)

    def get(self, url: str, **kwargs):
        return self._request("GET", url, **kwargs)

    def put(self, url: str, **kwargs):
        return self._request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self._request("DELETE", url, **kwargs)


class _ConcurrentSession:
    def __init__(self, repo_payloads: dict[str, dict[str, object]], delay: float = 0.05):
        self.repo_payloads = repo_payloads
        self.delay = delay
        self.calls: list[tuple[str, str]] = []
        self._lock = threading.Lock()
        self._in_flight = 0
        self.max_in_flight = 0

    def get(self, url: str, **_kwargs):
        with self._lock:
            self.calls.append(("GET", url))
            self._in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self._in_flight)
        try:
            time.sleep(self.delay)
            suffix = "/repos/"
            if suffix not in url:
                raise AssertionError(f"unexpected GET {url}")
            repo_key = url.split(suffix, 1)[1]
            payload = self.repo_payloads.get(repo_key)
            if payload is None:
                raise AssertionError(f"missing payload for {repo_key}")
            return _StubResponse(200, payload)
        finally:
            with self._lock:
                self._in_flight -= 1

    def put(self, url: str, **kwargs):
        raise AssertionError(f"unexpected PUT {url} {kwargs}")

    def delete(self, url: str, **kwargs):
        raise AssertionError(f"unexpected DELETE {url} {kwargs}")


def _normalize_repo_stub(repo):
    if not isinstance(repo, dict):
        return None
    full_name = normalize(repo.get("full_name"))
    url = normalize(repo.get("url"))
    if not full_name or not url or "/" not in full_name:
        return None
    owner, name = full_name.split("/", 1)
    clean = dict(repo)
    clean["full_name"] = full_name
    clean["url"] = url
    clean["owner"] = owner
    clean["name"] = name
    return clean


def build_runtime(
    session,
    token: str = "token",
    user_state: dict | None = None,
    save_user_state=None,
    *,
    token_validation_time_getter=None,
    token_validation_cache_ttl_seconds: int = 30,
    translate_text=None,
    save_translation_cache=None,
    flush_translation_cache=None,
):
    return make_github_runtime(
        session=session,
        api_timeout=(1, 1),
        trending_timeout=(1, 1),
        search_api_url="https://example.invalid/search",
        repo_api_url="https://example.invalid/repos",
        settings={"github_token": token},
        periods=[{"key": "daily", "label": "Today", "days": 1}],
        state_lock=threading.RLock(),
        user_state=user_state if user_state is not None else {},
        save_user_state=save_user_state or (lambda: None),
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
        cached_repo_details=lambda _cache_key: None,
        detail_fetch_lock=lambda _cache_key: threading.RLock(),
        strip_markdown=strip_markdown,
        translate_text=translate_text or (lambda text: normalize(text)),
        translate_query_to_en=lambda text: normalize(text),
        save_translation_cache=save_translation_cache or (lambda: None),
        flush_translation_cache=flush_translation_cache,
        save_repo_details=lambda _cache_key, _details: None,
        parse_iso_timestamp=parse_iso_timestamp,
        iso_now=iso_now,
        fetch_semaphore=threading.Semaphore(1),
        favorite_watch_min_seconds_no_token=60,
        favorite_watch_min_seconds_with_token=30,
        favorite_release_min_seconds_no_token=60,
        favorite_release_min_seconds_with_token=30,
        favorite_watch_max_checks_no_token=2,
        favorite_watch_max_checks_with_token=4,
        token_validation_time_getter=token_validation_time_getter,
        token_validation_cache_ttl_seconds=token_validation_cache_ttl_seconds,
    )


class GitHubStarSyncTests(unittest.TestCase):
    def test_sync_local_favorites_with_starred_translates_english_descriptions(self):
        user_state = {
            "favorites": [],
            "repo_records": {},
            "favorite_watch": {},
            "favorite_updates": [],
        }
        translate_calls: list[str] = []
        flush_calls: list[str] = []

        def fake_translate(text: str) -> str:
            translate_calls.append(text)
            return {
                "Production-grade engineering skills for AI coding agents.": "AI 编码代理的生产级工程技能。",
                "Windows desktop app for GitHub trending.": "GitHub 趋势的 Windows 桌面应用。",
            }[text]

        runtime = build_runtime(
            _ScriptedSession(),
            user_state=user_state,
            translate_text=fake_translate,
            flush_translation_cache=lambda: flush_calls.append("flush") or True,
        )

        summary = runtime.sync_local_favorites_with_starred(
            [
                {
                    "full_name": "octo/skills",
                    "url": "https://github.com/octo/skills",
                    "description": "Production-grade engineering skills for AI coding agents.",
                    "description_raw": "Production-grade engineering skills for AI coding agents.",
                },
                {
                    "full_name": "octo/radar",
                    "url": "https://github.com/octo/radar",
                    "description": "Windows desktop app for GitHub trending.",
                    "description_raw": "Windows desktop app for GitHub trending.",
                },
            ]
        )

        self.assertEqual(summary, {"total": 2, "added": 2, "removed": 0})
        self.assertCountEqual(
            translate_calls,
            [
                "Production-grade engineering skills for AI coding agents.",
                "Windows desktop app for GitHub trending.",
            ],
        )
        self.assertEqual(flush_calls, ["flush"])
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/skills"]["description"],
            "AI 编码代理的生产级工程技能。",
        )
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/skills"]["description_raw"],
            "Production-grade engineering skills for AI coding agents.",
        )
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/radar"]["description"],
            "GitHub 趋势的 Windows 桌面应用。",
        )
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/radar"]["description_raw"],
            "Windows desktop app for GitHub trending.",
        )

    def test_sync_local_favorites_with_starred_skips_empty_and_han_descriptions(self):
        user_state = {
            "favorites": [],
            "repo_records": {},
            "favorite_watch": {},
            "favorite_updates": [],
        }
        translate_calls: list[str] = []
        flush_calls: list[str] = []

        runtime = build_runtime(
            _ScriptedSession(),
            user_state=user_state,
            translate_text=lambda text: translate_calls.append(text) or f"ZH::{text}",
            flush_translation_cache=lambda: flush_calls.append("flush") or True,
        )

        summary = runtime.sync_local_favorites_with_starred(
            [
                {
                    "full_name": "octo/empty",
                    "url": "https://github.com/octo/empty",
                    "description": "",
                    "description_raw": "",
                },
                {
                    "full_name": "octo/han",
                    "url": "https://github.com/octo/han",
                    "description": "已经是中文描述",
                    "description_raw": "已经是中文描述",
                },
            ]
        )

        self.assertEqual(summary, {"total": 2, "added": 2, "removed": 0})
        self.assertEqual(translate_calls, [])
        self.assertEqual(flush_calls, [])
        self.assertEqual(user_state["repo_records"]["https://github.com/octo/empty"]["description"], "")
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/empty"]["description_raw"],
            "",
        )
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/han"]["description"],
            "已经是中文描述",
        )
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/han"]["description_raw"],
            "已经是中文描述",
        )

    def test_sync_local_favorites_with_starred_continues_when_translation_cache_flush_fails(self):
        user_state = {
            "favorites": [],
            "repo_records": {},
            "favorite_watch": {},
            "favorite_updates": [],
        }
        flush_calls: list[str] = []

        runtime = build_runtime(
            _ScriptedSession(),
            user_state=user_state,
            translate_text=lambda text: "AI 编码代理的生产级工程技能。" if text == "Production-grade engineering skills for AI coding agents." else text,
            flush_translation_cache=lambda: flush_calls.append("flush") or (_ for _ in ()).throw(RuntimeError("disk full")),
        )

        summary = runtime.sync_local_favorites_with_starred(
            [
                {
                    "full_name": "octo/skills",
                    "url": "https://github.com/octo/skills",
                    "description": "Production-grade engineering skills for AI coding agents.",
                    "description_raw": "Production-grade engineering skills for AI coding agents.",
                }
            ]
        )

        self.assertEqual(summary, {"total": 1, "added": 1, "removed": 0})
        self.assertEqual(flush_calls, ["flush"])
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/skills"]["description"],
            "AI 编码代理的生产级工程技能。",
        )
        self.assertEqual(
            user_state["repo_records"]["https://github.com/octo/skills"]["description_raw"],
            "Production-grade engineering skills for AI coding agents.",
        )

    def test_sync_local_favorites_with_starred_replaces_local_favorites(self):
        user_state = {
            "favorites": [
                "https://github.com/octo/old-one",
                "https://github.com/octo/keep-me",
            ],
            "repo_records": {
                "https://github.com/octo/old-one": {
                    "full_name": "octo/old-one",
                    "url": "https://github.com/octo/old-one",
                },
            },
            "favorite_watch": {
                "https://github.com/octo/old-one": {"url": "https://github.com/octo/old-one"},
                "https://github.com/octo/keep-me": {"url": "https://github.com/octo/keep-me"},
            },
            "favorite_updates": [
                {"id": "old", "url": "https://github.com/octo/old-one"},
                {"id": "keep", "url": "https://github.com/octo/keep-me"},
            ],
        }
        save_calls: list[str] = []
        runtime = build_runtime(
            _ScriptedSession(),
            user_state=user_state,
            save_user_state=lambda: save_calls.append("saved"),
        )

        summary = runtime.sync_local_favorites_with_starred(
            [
                {"full_name": "octo/keep-me", "url": "https://github.com/octo/keep-me"},
                {"full_name": "octo/new-one", "url": "https://github.com/octo/new-one"},
            ]
        )

        self.assertEqual(summary, {"total": 2, "added": 1, "removed": 1})
        self.assertEqual(
            user_state["favorites"],
            [
                "https://github.com/octo/keep-me",
                "https://github.com/octo/new-one",
            ],
        )
        self.assertEqual(sorted(user_state["favorite_watch"].keys()), ["https://github.com/octo/keep-me"])
        self.assertEqual([item["url"] for item in user_state["favorite_updates"]], ["https://github.com/octo/keep-me"])
        self.assertIn("https://github.com/octo/new-one", user_state["repo_records"])
        self.assertEqual(save_calls, ["saved"])

    def test_sync_local_favorites_with_starred_can_clear_all_favorites(self):
        user_state = {
            "favorites": ["https://github.com/octo/old-one"],
            "repo_records": {},
            "favorite_watch": {
                "https://github.com/octo/old-one": {"url": "https://github.com/octo/old-one"},
            },
            "favorite_updates": [
                {"id": "old", "url": "https://github.com/octo/old-one"},
            ],
        }
        runtime = build_runtime(_ScriptedSession(), user_state=user_state)

        summary = runtime.sync_local_favorites_with_starred([])

        self.assertEqual(summary, {"total": 0, "added": 0, "removed": 1})
        self.assertEqual(user_state["favorites"], [])
        self.assertEqual(user_state["favorite_watch"], {})
        self.assertEqual(user_state["favorite_updates"], [])

    def test_track_favorite_updates_fetches_due_repos_concurrently(self):
        old_checked_at = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        recent_release_checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        repo_payloads = {
            "octo/a": {
                "full_name": "octo/a",
                "html_url": "https://github.com/octo/a",
                "stargazers_count": 12,
                "forks_count": 2,
                "open_issues_count": 1,
                "updated_at": old_checked_at,
                "pushed_at": old_checked_at,
            },
            "octo/b": {
                "full_name": "octo/b",
                "html_url": "https://github.com/octo/b",
                "stargazers_count": 25,
                "forks_count": 4,
                "open_issues_count": 1,
                "updated_at": old_checked_at,
                "pushed_at": old_checked_at,
            },
            "octo/c": {
                "full_name": "octo/c",
                "html_url": "https://github.com/octo/c",
                "stargazers_count": 30,
                "forks_count": 5,
                "open_issues_count": 1,
                "updated_at": old_checked_at,
                "pushed_at": old_checked_at,
            },
            "octo/d": {
                "full_name": "octo/d",
                "html_url": "https://github.com/octo/d",
                "stargazers_count": 41,
                "forks_count": 6,
                "open_issues_count": 1,
                "updated_at": old_checked_at,
                "pushed_at": old_checked_at,
            },
        }
        user_state = {
            "favorites": [f"https://github.com/{name}" for name in repo_payloads],
            "repo_records": {
                f"https://github.com/{name}": {"full_name": name, "url": f"https://github.com/{name}"}
                for name in repo_payloads
            },
            "favorite_watch": {
                f"https://github.com/{name}": {
                    "full_name": name,
                    "url": f"https://github.com/{name}",
                    "stars": 10,
                    "forks": 1,
                    "checked_at": old_checked_at,
                    "release_checked_at": recent_release_checked_at,
                }
                for name in repo_payloads
            },
            "favorite_updates": [],
        }
        save_calls: list[str] = []
        session = _ConcurrentSession(repo_payloads)
        runtime = build_runtime(session, user_state=user_state, save_user_state=lambda: save_calls.append("saved"))

        new_updates = runtime.track_favorite_updates()

        self.assertGreater(session.max_in_flight, 1)
        self.assertEqual(new_updates, 4)
        self.assertEqual(len(user_state["favorite_watch"]), 4)
        self.assertEqual(len(user_state["favorite_updates"]), 4)
        self.assertEqual(save_calls, ["saved"])

    def test_sync_favorite_repo_stars_when_enabling(self):
        session = _ScriptedSession({"GET": [_StubResponse(404)], "PUT": [_StubResponse(204)]})
        runtime = build_runtime(session)

        result = runtime.sync_favorite_repo(
            {"full_name": "octo/widgets", "url": "https://github.com/octo/widgets"},
            True,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            session.calls,
            [
                ("GET", "https://api.github.com/user/starred/octo/widgets"),
                ("PUT", "https://api.github.com/user/starred/octo/widgets"),
            ],
        )

    def test_sync_favorite_repo_unstars_when_disabling(self):
        session = _ScriptedSession({"GET": [_StubResponse(204)], "DELETE": [_StubResponse(204)]})
        runtime = build_runtime(session)

        result = runtime.sync_favorite_repo(
            {"full_name": "octo/widgets", "url": "https://github.com/octo/widgets"},
            False,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            session.calls,
            [
                ("GET", "https://api.github.com/user/starred/octo/widgets"),
                ("DELETE", "https://api.github.com/user/starred/octo/widgets"),
            ],
        )

    def test_sync_favorite_repo_skips_without_token(self):
        session = _ScriptedSession()
        runtime = build_runtime(session, token="")

        result = runtime.sync_favorite_repo(
            {"full_name": "octo/widgets", "url": "https://github.com/octo/widgets"},
            False,
        )

        self.assertIsNone(result)
        self.assertEqual(session.calls, [])

    def test_validate_github_token_reports_empty_invalid_insufficient_and_success_states(self):
        empty_runtime = build_runtime(_ScriptedSession(), token="")
        self.assertEqual(empty_runtime.validate_github_token()["state"], "empty")

        invalid_session = _ScriptedSession({"GET": [_StubResponse(401)]})
        invalid_runtime = build_runtime(invalid_session)
        invalid = invalid_runtime.validate_github_token("bad-token")
        self.assertEqual(invalid["state"], "invalid")
        self.assertEqual(invalid_session.calls, [("GET", "https://api.github.com/user")])

        insufficient_session = _ScriptedSession(
            {
                "GET": [
                    _StubResponse(200, {"login": "octo"}),
                    _StubResponse(403),
                ]
            }
        )
        insufficient_runtime = build_runtime(insufficient_session)
        insufficient = insufficient_runtime.validate_github_token("limited-token")
        self.assertEqual(insufficient["state"], "insufficient")
        self.assertEqual(insufficient["login"], "octo")
        self.assertEqual(
            insufficient_session.calls,
            [
                ("GET", "https://api.github.com/user"),
                ("GET", "https://api.github.com/user/starred"),
            ],
        )

        success_session = _ScriptedSession({"GET": [_StubResponse(200, {"login": "octo"}), _StubResponse(200, [])]})
        success_runtime = build_runtime(success_session)
        success = success_runtime.validate_github_token("good-token")
        self.assertEqual(success["state"], "success")
        self.assertEqual(success["login"], "octo")
        self.assertIn("详情", success["message"])
        self.assertIn("发现", success["message"])
        self.assertIn("星标同步", success["message"])

    def test_validate_github_token_uses_ttl_cache_until_expiry_or_token_change(self):
        clock = [100.0]
        session = _ScriptedSession(
            {
                "GET": [
                    _StubResponse(200, {"login": "octo"}),
                    _StubResponse(200, []),
                    _StubResponse(200, {"login": "octo-other"}),
                    _StubResponse(200, []),
                    _StubResponse(200, {"login": "octo"}),
                    _StubResponse(200, []),
                ]
            }
        )
        runtime = build_runtime(
            session,
            token_validation_time_getter=lambda: clock[0],
            token_validation_cache_ttl_seconds=30,
        )

        first = runtime.validate_github_token("good-token")
        second = runtime.validate_github_token("good-token")
        other = runtime.validate_github_token("other-token")
        clock[0] += 31
        expired = runtime.validate_github_token("good-token")

        self.assertEqual(first["login"], "octo")
        self.assertEqual(second["login"], "octo")
        self.assertEqual(other["login"], "octo-other")
        self.assertEqual(expired["login"], "octo")
        self.assertEqual(
            session.calls,
            [
                ("GET", "https://api.github.com/user"),
                ("GET", "https://api.github.com/user/starred"),
                ("GET", "https://api.github.com/user"),
                ("GET", "https://api.github.com/user/starred"),
                ("GET", "https://api.github.com/user"),
                ("GET", "https://api.github.com/user/starred"),
            ],
        )

    def test_unstar_repo_returns_error_when_check_fails(self):
        session = _ScriptedSession({"GET": [_StubResponse(500)]})
        runtime = build_runtime(session)

        result = runtime.unstar_repo("octo", "widgets")

        self.assertFalse(result["ok"])
        self.assertNotIn("already_unstarred", result)
        self.assertEqual(result["code"], "github_star_update_failed")
        self.assertNotIn("HTTP 500", result["error"])
        self.assertEqual(session.calls, [("GET", "https://api.github.com/user/starred/octo/widgets")])


if __name__ == "__main__":
    unittest.main()
