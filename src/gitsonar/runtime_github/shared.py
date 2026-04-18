#!/usr/bin/env python3
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GitHubRuntimeDeps:
    session: object
    api_timeout: tuple[int, int]
    trending_timeout: tuple[int, int]
    search_api_url: str
    repo_api_url: str
    settings: dict[str, object]
    periods: list[dict[str, object]]
    state_lock: object
    user_state: dict[str, object]
    save_user_state: object
    requests_module: object
    beautifulsoup_cls: object
    thread_pool_executor_cls: object
    as_completed: object
    datetime_cls: object
    timedelta_cls: object
    normalize: object
    clamp_int: object
    extract_count: object
    normalize_repo: object
    repo_from_url: object
    normalize_watch_entry: object
    normalize_favorite_update: object
    translate_snapshot: object
    load_snapshot: object
    cached_repo_details: object
    detail_fetch_lock: object
    strip_markdown: object
    translate_text: object
    translate_query_to_en: object
    save_translation_cache: object
    save_repo_details: object
    parse_iso_timestamp: object
    iso_now: object
    fetch_semaphore: object
    favorite_watch_min_seconds_no_token: int
    favorite_watch_min_seconds_with_token: int
    favorite_release_min_seconds_no_token: int
    favorite_release_min_seconds_with_token: int
    favorite_watch_max_checks_no_token: int
    favorite_watch_max_checks_with_token: int


@dataclass(slots=True)
class GitHubRuntimeState:
    discovery_cache: dict[str, dict[str, object]] = field(default_factory=dict)
    discovery_cache_lock: threading.RLock = field(default_factory=threading.RLock)
    discovery_cache_seconds: int = 10 * 60
    query_term_re: re.Pattern[str] = field(default_factory=lambda: re.compile(r"[a-z0-9][a-z0-9+.#/_-]*"))
    stop_terms: set[str] = field(default_factory=lambda: {
        "a", "an", "and", "app", "apps", "awesome", "best", "build", "built", "cli", "code", "data",
        "for", "framework", "from", "github", "helper", "in", "is", "kit", "library", "of", "on", "open",
        "project", "python", "repo", "repository", "sdk", "simple", "starter", "template", "the", "to",
        "tool", "tools", "typescript", "with",
    })
    ranking_profiles: set[str] = field(default_factory=lambda: {"balanced", "hot", "fresh", "builder", "trend"})


class DiscoveryCancelledError(RuntimeError):
    pass


def build_github_get(deps: GitHubRuntimeDeps):
    session = deps.session
    api_timeout = deps.api_timeout
    normalize = deps.normalize
    settings = deps.settings

    def github_get(
        url: str,
        *,
        params: dict[str, object] | None = None,
        timeout: tuple[int, int] = api_timeout,
        accept: str = "application/vnd.github+json",
    ):
        response = session.get(url, params=params, timeout=timeout, headers={"Accept": accept})
        if response.status_code == 401 and normalize(settings.get("github_token", "")):
            logger.warning("GitHub Token 鉴权失败，降级为匿名请求: %s", url)
            response = session.get(
                url,
                params=params,
                timeout=timeout,
                headers={"Accept": accept, "Authorization": None},
            )
        response.raise_for_status()
        return response

    return github_get
