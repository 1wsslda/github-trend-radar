#!/usr/bin/env python3
from __future__ import annotations

from types import SimpleNamespace

from .details import build_details_api
from .discovery import build_discovery_api
from .favorites import build_favorites_api
from .shared import DiscoveryCancelledError, GitHubRuntimeDeps, GitHubRuntimeState, build_github_get
from .trending import build_trending_api

__all__ = ["GitHubRuntimeDeps", "make_github_runtime"]


def make_github_runtime(
    *,
    session,
    api_timeout: tuple[int, int],
    trending_timeout: tuple[int, int],
    search_api_url: str,
    repo_api_url: str,
    settings: dict[str, object],
    periods: list[dict[str, object]],
    state_lock,
    user_state: dict[str, object],
    save_user_state,
    requests_module,
    beautifulsoup_cls,
    thread_pool_executor_cls,
    as_completed,
    datetime_cls,
    timedelta_cls,
    normalize,
    clamp_int,
    extract_count,
    normalize_repo,
    repo_from_url,
    normalize_watch_entry,
    normalize_favorite_update,
    translate_snapshot,
    load_snapshot,
    cached_repo_details,
    detail_fetch_lock,
    strip_markdown,
    translate_text,
    translate_query_to_en,
    save_translation_cache,
    save_repo_details,
    parse_iso_timestamp,
    iso_now,
    fetch_semaphore,
    favorite_watch_min_seconds_no_token: int,
    favorite_watch_min_seconds_with_token: int,
    favorite_release_min_seconds_no_token: int,
    favorite_release_min_seconds_with_token: int,
    favorite_watch_max_checks_no_token: int,
    favorite_watch_max_checks_with_token: int,
):
    deps = GitHubRuntimeDeps(
        session=session,
        api_timeout=api_timeout,
        trending_timeout=trending_timeout,
        search_api_url=search_api_url,
        repo_api_url=repo_api_url,
        settings=settings,
        periods=periods,
        state_lock=state_lock,
        user_state=user_state,
        save_user_state=save_user_state,
        requests_module=requests_module,
        beautifulsoup_cls=beautifulsoup_cls,
        thread_pool_executor_cls=thread_pool_executor_cls,
        as_completed=as_completed,
        datetime_cls=datetime_cls,
        timedelta_cls=timedelta_cls,
        normalize=normalize,
        clamp_int=clamp_int,
        extract_count=extract_count,
        normalize_repo=normalize_repo,
        repo_from_url=repo_from_url,
        normalize_watch_entry=normalize_watch_entry,
        normalize_favorite_update=normalize_favorite_update,
        translate_snapshot=translate_snapshot,
        load_snapshot=load_snapshot,
        cached_repo_details=cached_repo_details,
        detail_fetch_lock=detail_fetch_lock,
        strip_markdown=strip_markdown,
        translate_text=translate_text,
        translate_query_to_en=translate_query_to_en,
        save_translation_cache=save_translation_cache,
        save_repo_details=save_repo_details,
        parse_iso_timestamp=parse_iso_timestamp,
        iso_now=iso_now,
        fetch_semaphore=fetch_semaphore,
        favorite_watch_min_seconds_no_token=favorite_watch_min_seconds_no_token,
        favorite_watch_min_seconds_with_token=favorite_watch_min_seconds_with_token,
        favorite_release_min_seconds_no_token=favorite_release_min_seconds_no_token,
        favorite_release_min_seconds_with_token=favorite_release_min_seconds_with_token,
        favorite_watch_max_checks_no_token=favorite_watch_max_checks_no_token,
        favorite_watch_max_checks_with_token=favorite_watch_max_checks_with_token,
    )
    state = GitHubRuntimeState()
    github_get = build_github_get(deps)
    trending_api = build_trending_api(deps=deps, github_get=github_get)
    details_api = build_details_api(deps=deps, github_get=github_get)
    discovery_api = build_discovery_api(
        deps=deps,
        state=state,
        github_get=github_get,
        fetch_repo_details=details_api["fetch_repo_details"],
    )
    favorites_api = build_favorites_api(deps=deps, github_get=github_get)
    return SimpleNamespace(
        DiscoveryCancelledError=DiscoveryCancelledError,
        github_get=github_get,
        **trending_api,
        **details_api,
        **discovery_api,
        **favorites_api,
    )
