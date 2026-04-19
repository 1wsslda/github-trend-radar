#!/usr/bin/env python3
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GitHubNetworkDeps:
    session: object
    requests_module: object
    api_timeout: tuple[int, int]
    trending_timeout: tuple[int, int]
    search_api_url: str
    repo_api_url: str
    fetch_semaphore: object


@dataclass(slots=True)
class GitHubStateDeps:
    settings: dict[str, object]
    periods: list[dict[str, object]]
    state_lock: object
    user_state: dict[str, object]
    save_user_state: Callable[[], None]


@dataclass(slots=True)
class GitHubRenderDeps:
    beautifulsoup_cls: object
    thread_pool_executor_cls: object
    as_completed: object
    datetime_cls: object
    timedelta_cls: object


@dataclass(slots=True)
class GitHubRecordDeps:
    normalize: Callable[[object], str]
    clamp_int: object
    extract_count: object
    normalize_repo: object
    repo_from_url: object
    normalize_watch_entry: object
    normalize_favorite_update: object
    parse_iso_timestamp: object
    iso_now: Callable[[], str]
    strip_markdown: object


@dataclass(slots=True)
class GitHubContentDeps:
    translate_snapshot: object
    load_snapshot: object
    cached_repo_details: object
    detail_fetch_lock: object
    translate_text: object
    translate_query_to_en: object
    save_translation_cache: Callable[[], None]
    save_repo_details: object
    flush_translation_cache: Callable[[], bool] | None = None
    flush_repo_details_cache: Callable[[], bool] | None = None


@dataclass(slots=True)
class GitHubFavoritePolicy:
    favorite_watch_min_seconds_no_token: int
    favorite_watch_min_seconds_with_token: int
    favorite_release_min_seconds_no_token: int
    favorite_release_min_seconds_with_token: int
    favorite_watch_max_checks_no_token: int
    favorite_watch_max_checks_with_token: int


@dataclass(slots=True)
class GitHubRuntimeDeps:
    network: GitHubNetworkDeps
    state: GitHubStateDeps
    render: GitHubRenderDeps
    records: GitHubRecordDeps
    content: GitHubContentDeps
    favorite_policy: GitHubFavoritePolicy
    token_validation_time_getter: object = None
    token_validation_cache_ttl_seconds: int = 30

    @property
    def session(self):
        return self.network.session

    @property
    def requests_module(self):
        return self.network.requests_module

    @property
    def api_timeout(self):
        return self.network.api_timeout

    @property
    def trending_timeout(self):
        return self.network.trending_timeout

    @property
    def search_api_url(self):
        return self.network.search_api_url

    @property
    def repo_api_url(self):
        return self.network.repo_api_url

    @property
    def fetch_semaphore(self):
        return self.network.fetch_semaphore

    @property
    def settings(self):
        return self.state.settings

    @property
    def periods(self):
        return self.state.periods

    @property
    def state_lock(self):
        return self.state.state_lock

    @property
    def user_state(self):
        return self.state.user_state

    @property
    def save_user_state(self):
        return self.state.save_user_state

    @property
    def beautifulsoup_cls(self):
        return self.render.beautifulsoup_cls

    @property
    def thread_pool_executor_cls(self):
        return self.render.thread_pool_executor_cls

    @property
    def as_completed(self):
        return self.render.as_completed

    @property
    def datetime_cls(self):
        return self.render.datetime_cls

    @property
    def timedelta_cls(self):
        return self.render.timedelta_cls

    @property
    def normalize(self):
        return self.records.normalize

    @property
    def clamp_int(self):
        return self.records.clamp_int

    @property
    def extract_count(self):
        return self.records.extract_count

    @property
    def normalize_repo(self):
        return self.records.normalize_repo

    @property
    def repo_from_url(self):
        return self.records.repo_from_url

    @property
    def normalize_watch_entry(self):
        return self.records.normalize_watch_entry

    @property
    def normalize_favorite_update(self):
        return self.records.normalize_favorite_update

    @property
    def parse_iso_timestamp(self):
        return self.records.parse_iso_timestamp

    @property
    def iso_now(self):
        return self.records.iso_now

    @property
    def strip_markdown(self):
        return self.records.strip_markdown

    @property
    def translate_snapshot(self):
        return self.content.translate_snapshot

    @property
    def load_snapshot(self):
        return self.content.load_snapshot

    @property
    def cached_repo_details(self):
        return self.content.cached_repo_details

    @property
    def detail_fetch_lock(self):
        return self.content.detail_fetch_lock

    @property
    def translate_text(self):
        return self.content.translate_text

    @property
    def translate_query_to_en(self):
        return self.content.translate_query_to_en

    @property
    def save_translation_cache(self):
        return self.content.save_translation_cache

    @property
    def flush_translation_cache(self):
        return self.content.flush_translation_cache or self.content.save_translation_cache

    @property
    def save_repo_details(self):
        return self.content.save_repo_details

    @property
    def flush_repo_details_cache(self):
        return self.content.flush_repo_details_cache or (lambda: False)

    @property
    def favorite_watch_min_seconds_no_token(self):
        return self.favorite_policy.favorite_watch_min_seconds_no_token

    @property
    def favorite_watch_min_seconds_with_token(self):
        return self.favorite_policy.favorite_watch_min_seconds_with_token

    @property
    def favorite_release_min_seconds_no_token(self):
        return self.favorite_policy.favorite_release_min_seconds_no_token

    @property
    def favorite_release_min_seconds_with_token(self):
        return self.favorite_policy.favorite_release_min_seconds_with_token

    @property
    def favorite_watch_max_checks_no_token(self):
        return self.favorite_policy.favorite_watch_max_checks_no_token

    @property
    def favorite_watch_max_checks_with_token(self):
        return self.favorite_policy.favorite_watch_max_checks_with_token


@dataclass(slots=True)
class GitHubRuntimeState:
    discovery_cache: dict[str, dict[str, object]] = field(default_factory=dict)
    discovery_cache_lock: threading.RLock = field(default_factory=threading.RLock)
    discovery_cache_seconds: int = 10 * 60
    discovery_cache_max_entries: int = 128
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
