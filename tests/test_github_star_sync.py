from __future__ import annotations

import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_github import make_github_runtime
from gitsonar.runtime_utils import clamp_int, extract_count, iso_now, normalize, parse_iso_timestamp, strip_markdown


class _StubResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return {}


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


def build_runtime(session, token: str = "token", user_state: dict | None = None, save_user_state=None):
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


class GitHubStarSyncTests(unittest.TestCase):
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
        self.assertEqual(
            sorted(user_state["favorite_watch"].keys()),
            ["https://github.com/octo/keep-me"],
        )
        self.assertEqual(
            [item["url"] for item in user_state["favorite_updates"]],
            ["https://github.com/octo/keep-me"],
        )
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

    def test_sync_favorite_repo_stars_when_enabling(self):
        session = _ScriptedSession(
            {
                "GET": [_StubResponse(404)],
                "PUT": [_StubResponse(204)],
            }
        )
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
        session = _ScriptedSession(
            {
                "GET": [_StubResponse(204)],
                "DELETE": [_StubResponse(204)],
            }
        )
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

    def test_unstar_repo_returns_error_when_check_fails(self):
        session = _ScriptedSession({"GET": [_StubResponse(500)]})
        runtime = build_runtime(session)

        result = runtime.unstar_repo("octo", "widgets")

        self.assertFalse(result["ok"])
        self.assertNotIn("already_unstarred", result)
        self.assertEqual(session.calls, [("GET", "https://api.github.com/user/starred/octo/widgets")])


if __name__ == "__main__":
    unittest.main()
