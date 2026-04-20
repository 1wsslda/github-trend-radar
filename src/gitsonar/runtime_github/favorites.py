#!/usr/bin/env python3
from __future__ import annotations

import logging
import time

from ..runtime.repo_records import build_repo_record

logger = logging.getLogger(__name__)


def build_favorites_api(*, deps, github_get):
    normalize = deps.normalize
    normalize_repo = deps.normalize_repo
    state_lock = deps.state_lock
    user_state = deps.user_state
    save_user_state = deps.save_user_state
    normalize_watch_entry = deps.normalize_watch_entry
    normalize_favorite_update = deps.normalize_favorite_update
    repo_from_url = deps.repo_from_url
    settings = deps.settings
    clamp_int = deps.clamp_int
    parse_iso_timestamp = deps.parse_iso_timestamp
    iso_now = deps.iso_now
    thread_pool_executor_cls = deps.thread_pool_executor_cls
    as_completed = deps.as_completed
    requests_module = deps.requests_module
    session = deps.session
    api_timeout = deps.api_timeout
    repo_api_url = deps.repo_api_url
    translate_text = deps.translate_text
    flush_translation_cache = deps.flush_translation_cache
    as_bool = lambda value, default=False: default if value is None else bool(value)
    favorite_watch_min_seconds_no_token = deps.favorite_watch_min_seconds_no_token
    favorite_watch_min_seconds_with_token = deps.favorite_watch_min_seconds_with_token
    favorite_release_min_seconds_no_token = deps.favorite_release_min_seconds_no_token
    favorite_release_min_seconds_with_token = deps.favorite_release_min_seconds_with_token
    favorite_watch_max_checks_no_token = deps.favorite_watch_max_checks_no_token
    favorite_watch_max_checks_with_token = deps.favorite_watch_max_checks_with_token
    token_validation_time_getter = getattr(deps, "token_validation_time_getter", None) or time.monotonic
    token_validation_cache_ttl_seconds = max(
        0,
        int(getattr(deps, "token_validation_cache_ttl_seconds", 30) or 0),
    )
    token_validation_cache: dict[str, tuple[float, dict[str, object]]] = {}

    def github_api_headers(token: str = "") -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def has_han_text(text: str) -> bool:
        return any("\u3400" <= ch <= "\u9fff" for ch in text)

    def sync_local_favorites_with_starred(repos: list[dict[str, object]]) -> dict[str, int]:
        cleaned_repos: list[dict[str, object]] = []
        seen_urls: set[str] = set()
        for repo in repos:
            clean = normalize_repo(repo)
            if not clean:
                continue
            url = normalize(clean.get("url"))
            if not url or url in seen_urls:
                continue
            cleaned_repos.append(clean)
            seen_urls.add(url)

        pending_translations: dict[str, str] = {}
        translated_by_raw_key: dict[str, str] = {}
        for repo in cleaned_repos:
            raw_description = normalize(repo.get("description_raw") or repo.get("description"))
            current_description = normalize(repo.get("description"))
            repo["description_raw"] = raw_description
            if not raw_description:
                repo["description"] = ""
                continue
            if current_description and current_description != raw_description:
                repo["description"] = current_description
                continue
            repo["description"] = raw_description
            if has_han_text(raw_description):
                continue
            pending_translations.setdefault(raw_description.lower(), raw_description)

        if pending_translations:
            with thread_pool_executor_cls(max_workers=min(4, len(pending_translations))) as executor:
                future_map = {
                    executor.submit(translate_text, raw_text): raw_key
                    for raw_key, raw_text in pending_translations.items()
                }
                for future in as_completed(future_map):
                    raw_key = future_map[future]
                    raw_text = pending_translations[raw_key]
                    try:
                        translated_by_raw_key[raw_key] = normalize(future.result()) or raw_text
                    except Exception as exc:
                        logger.warning("favorite_description_translate_failed text=%s error=%s", raw_text, exc)
                        translated_by_raw_key[raw_key] = raw_text
            try:
                flush_translation_cache()
            except Exception as exc:
                logger.warning("favorite_translation_cache_flush_failed error=%s", exc)
            for repo in cleaned_repos:
                raw_description = normalize(repo.get("description_raw"))
                if raw_description and normalize(repo.get("description")) == raw_description:
                    repo["description"] = translated_by_raw_key.get(raw_description.lower(), raw_description)

        favorite_urls = [normalize(repo.get("url")) for repo in cleaned_repos if normalize(repo.get("url"))]
        favorite_set = set(favorite_urls)

        with state_lock:
            existing_favorites = [normalize(item) for item in user_state.get("favorites", []) if normalize(item)]
            existing_set = set(existing_favorites)
            added = sum(1 for url in favorite_urls if url not in existing_set)
            removed = sum(1 for url in existing_favorites if url not in favorite_set)

            repo_records = user_state.setdefault("repo_records", {})
            for repo in cleaned_repos:
                repo_records[str(repo.get("url") or "")] = repo

            user_state["favorites"] = favorite_urls
            user_state["favorite_watch"] = {
                url: item
                for url, item in user_state.get("favorite_watch", {}).items()
                if url in favorite_set and normalize_watch_entry(item)
            }
            user_state["favorite_updates"] = [
                clean
                for item in user_state.get("favorite_updates", [])
                if (clean := normalize_favorite_update(item)) and clean["url"] in favorite_set
            ][:100]
            save_user_state()

        return {"total": len(favorite_urls), "added": added, "removed": removed}

    def favorite_watch_policy(favorite_count: int) -> tuple[int, int, int]:
        refresh_seconds = clamp_int(settings.get("refresh_hours", 1), 1, 1, 24) * 3600
        has_token = bool(normalize(settings.get("github_token", "")))
        if has_token:
            min_seconds = max(refresh_seconds, favorite_watch_min_seconds_with_token)
            release_min_seconds = max(refresh_seconds * 2, favorite_release_min_seconds_with_token)
            max_checks = min(max(4, favorite_count // 3), favorite_watch_max_checks_with_token)
        else:
            min_seconds = max(refresh_seconds * 2, favorite_watch_min_seconds_no_token)
            release_min_seconds = max(refresh_seconds * 6, favorite_release_min_seconds_no_token)
            max_checks = min(max(2, favorite_count // 6), favorite_watch_max_checks_no_token)
        return min_seconds, release_min_seconds, max_checks

    def should_refresh_release(entry: dict[str, object] | None, release_min_seconds: int, now_ts: int) -> bool:
        if not entry:
            return True
        release_checked_at = parse_iso_timestamp(entry.get("release_checked_at"))
        if not release_checked_at:
            return True
        return now_ts - release_checked_at >= release_min_seconds

    def favorite_watch_candidates(
        repos: list[dict[str, object]],
        previous_watch: dict[str, dict[str, object]],
        min_seconds: int,
        max_checks: int,
    ) -> list[dict[str, object]]:
        if max_checks <= 0:
            return []
        now_ts = int(time.time())
        candidates: list[tuple[int, int, int, dict[str, object]]] = []
        for index, repo in enumerate(repos):
            previous = previous_watch.get(repo["url"])
            checked_at = parse_iso_timestamp(previous.get("checked_at")) if previous else 0
            if previous and now_ts - checked_at < min_seconds:
                continue
            candidates.append((0 if previous is None else 1, checked_at, index, repo))
        candidates.sort()
        return [repo for *_meta, repo in candidates[:max_checks]]

    def should_stop_favorite_tracking(exc: Exception) -> bool:
        http_error = getattr(requests_module, "HTTPError", None)
        if http_error and isinstance(exc, http_error):
            response = exc.response
            if response is not None and response.status_code in {403, 429}:
                return True
        return False

    def fetch_favorite_watch_snapshot(
        repo: dict[str, object],
        previous: dict[str, object] | None = None,
        release_min_seconds: int = favorite_release_min_seconds_no_token,
    ) -> dict[str, object]:
        owner = normalize(repo.get("owner"))
        name = normalize(repo.get("name"))
        if not owner or not name:
            raise ValueError("收藏仓库缺少 owner/name")

        data = github_get(f"{repo_api_url}/{owner}/{name}").json()
        now = iso_now()
        now_ts = int(time.time())
        release_tag = ""
        release_published_at = ""
        release_checked_at = now

        if previous and not should_refresh_release(previous, release_min_seconds, now_ts):
            release_tag = normalize(previous.get("latest_release_tag"))
            release_published_at = normalize(previous.get("latest_release_published_at"))
            release_checked_at = (
                normalize(previous.get("release_checked_at"))
                or normalize(previous.get("checked_at"))
                or now
            )
        else:
            try:
                release = github_get(f"{repo_api_url}/{owner}/{name}/releases/latest").json()
                release_tag = normalize(release.get("tag_name"))
                release_published_at = normalize(release.get("published_at"))
            except Exception as exc:
                http_error = getattr(requests_module, "HTTPError", None)
                if http_error and isinstance(exc, http_error):
                    response = exc.response
                    if response is not None and response.status_code == 404:
                        release_tag = ""
                        release_published_at = ""
                    elif response is not None and response.status_code in {403, 429}:
                        raise
                    elif previous:
                        release_tag = normalize(previous.get("latest_release_tag"))
                        release_published_at = normalize(previous.get("latest_release_published_at"))
                    else:
                        raise
                elif previous:
                    release_tag = normalize(previous.get("latest_release_tag"))
                    release_published_at = normalize(previous.get("latest_release_published_at"))
                else:
                    raise

        full_name = normalize(data.get("full_name")) or f"{owner}/{name}"
        return {
            "full_name": full_name,
            "url": normalize(data.get("html_url")) or normalize(repo.get("url")) or f"https://github.com/{full_name}",
            "stars": clamp_int(data.get("stargazers_count"), 0, 0),
            "forks": clamp_int(data.get("forks_count"), 0, 0),
            "open_issues": clamp_int(data.get("open_issues_count"), 0, 0),
            "updated_at": normalize(data.get("updated_at")),
            "pushed_at": normalize(data.get("pushed_at")),
            "latest_release_tag": release_tag,
            "latest_release_published_at": release_published_at,
            "release_checked_at": release_checked_at,
            "checked_at": now,
        }

    def build_favorite_update(before: dict[str, object] | None, after: dict[str, object]) -> dict[str, object] | None:
        if not before:
            return None

        changes: list[str] = []
        star_delta = clamp_int(after.get("stars"), 0, 0) - clamp_int(before.get("stars"), 0, 0)
        if star_delta:
            changes.append(f"星标 {'+' if star_delta > 0 else ''}{star_delta}")

        fork_delta = clamp_int(after.get("forks"), 0, 0) - clamp_int(before.get("forks"), 0, 0)
        if fork_delta:
            changes.append(f"派生 {'+' if fork_delta > 0 else ''}{fork_delta}")

        latest_release_tag = normalize(after.get("latest_release_tag"))
        if latest_release_tag and latest_release_tag != normalize(before.get("latest_release_tag")):
            changes.append(f"新版本 {latest_release_tag}")

        if normalize(after.get("pushed_at")) and normalize(after.get("pushed_at")) != normalize(before.get("pushed_at")):
            changes.append("最近有新提交")
        elif normalize(after.get("updated_at")) and normalize(after.get("updated_at")) != normalize(before.get("updated_at")):
            changes.append("仓库信息有更新")

        if not changes:
            return None

        checked_at = normalize(after.get("checked_at")) or iso_now()
        return {
            "id": f"{normalize(after.get('full_name'))}:{checked_at}",
            "full_name": normalize(after.get("full_name")),
            "url": normalize(after.get("url")),
            "checked_at": checked_at,
            "changes": changes,
            "stars": clamp_int(after.get("stars"), 0, 0),
            "forks": clamp_int(after.get("forks"), 0, 0),
            "latest_release_tag": latest_release_tag,
            "pushed_at": normalize(after.get("pushed_at")),
        }

    def track_favorite_updates() -> int:
        started_ts = time.perf_counter()
        with state_lock:
            favorite_urls = list(user_state.get("favorites", []))
            repo_records = dict(user_state.get("repo_records", {}))
            previous_watch = dict(user_state.get("favorite_watch", {}))
            previous_updates = list(user_state.get("favorite_updates", []))

        repos: list[dict[str, object]] = []
        for url in favorite_urls:
            repo = normalize_repo(repo_records.get(url)) or repo_from_url(url)
            if repo:
                repos.append(repo)
        if not repos:
            return 0

        min_seconds, release_min_seconds, max_checks = favorite_watch_policy(len(repos))
        due_repos = favorite_watch_candidates(repos, previous_watch, min_seconds, max_checks)
        if not due_repos:
            return 0

        fresh_watch: dict[str, dict[str, object]] = {}
        updates: list[dict[str, object]] = list(previous_updates)
        new_update_count = 0
        max_workers = min(4, len(due_repos))
        logger.info(
            "favorite_update_tracking_start favorites=%d due=%d max_workers=%d",
            len(repos),
            len(due_repos),
            max_workers,
        )

        def fetch_one(repo: dict[str, object]) -> tuple[dict[str, object], dict[str, object] | None]:
            snapshot = normalize_watch_entry(
                fetch_favorite_watch_snapshot(repo, previous_watch.get(repo["url"]), release_min_seconds)
            )
            return repo, snapshot

        stop_dispatch = False
        pending_repos = iter(due_repos)
        with thread_pool_executor_cls(max_workers=max_workers) as executor:
            future_map = {}
            for _ in range(max_workers):
                repo = next(pending_repos, None)
                if repo is None:
                    break
                future_map[executor.submit(fetch_one, repo)] = repo

            while future_map:
                future = next(as_completed(list(future_map)))
                repo = future_map.pop(future)
                try:
                    repo, snapshot = future.result()
                except Exception as exc:
                    if should_stop_favorite_tracking(exc):
                        logger.warning("favorite_update_tracking_rate_limited repo=%s error=%s", repo["full_name"], exc)
                        stop_dispatch = True
                        for pending in list(future_map):
                            pending.cancel()
                        break
                    logger.warning("favorite_update_tracking_failed repo=%s error=%s", repo["full_name"], exc)
                else:
                    if snapshot:
                        fresh_watch[repo["url"]] = snapshot
                        if update := build_favorite_update(previous_watch.get(repo["url"]), snapshot):
                            updates.insert(0, update)
                            new_update_count += 1
                if stop_dispatch:
                    break
                next_repo = next(pending_repos, None)
                if next_repo is not None:
                    future_map[executor.submit(fetch_one, next_repo)] = next_repo

        if not fresh_watch:
            return 0

        favorite_set = set(favorite_urls)
        normalized_updates = [
            item
            for entry in updates
            if (item := normalize_favorite_update(entry)) and item["url"] in favorite_set
        ][:100]

        with state_lock:
            user_state["favorite_watch"] = {
                url: item
                for url, item in user_state.get("favorite_watch", {}).items()
                if url in favorite_urls
            }
            user_state["favorite_watch"].update(fresh_watch)
            user_state["favorite_updates"] = normalized_updates
            save_user_state()

        logger.info(
            "favorite_update_tracking_complete refreshed=%d new_updates=%d duration_ms=%d",
            len(fresh_watch),
            new_update_count,
            int((time.perf_counter() - started_ts) * 1000),
        )
        return new_update_count

    def clear_favorite_updates() -> None:
        with state_lock:
            user_state["favorite_updates"] = []
            save_user_state()

    def cached_token_status(token_value: str) -> dict[str, object] | None:
        if not token_validation_cache_ttl_seconds or not token_value:
            return None
        cached = token_validation_cache.get(token_value)
        if not cached:
            return None
        checked_at, status = cached
        if token_validation_time_getter() - checked_at > token_validation_cache_ttl_seconds:
            token_validation_cache.pop(token_value, None)
            return None
        return dict(status)

    def store_token_status(token_value: str, status: dict[str, object]) -> dict[str, object]:
        clean = dict(status)
        if token_validation_cache_ttl_seconds and token_value:
            token_validation_cache[token_value] = (float(token_validation_time_getter()), clean)
            if len(token_validation_cache) > 16:
                oldest = min(token_validation_cache.items(), key=lambda item: item[1][0])[0]
                token_validation_cache.pop(oldest, None)
        return clean

    def validate_github_token(token: object | None = None) -> dict[str, object]:
        token_value = normalize(settings.get("github_token", "")) if token is None else normalize(token)
        if not token_value:
            return {
                "state": "empty",
                "message": "未配置 GitHub Token。仓库详情、关键词发现和 GitHub 星标同步会走匿名请求或不可用，结果更容易触发限流。",
            }
        if cached := cached_token_status(token_value):
            return cached

        profile_response = session.get(
            "https://api.github.com/user",
            timeout=api_timeout,
            headers=github_api_headers(token_value),
        )
        if profile_response.status_code == 401:
            return store_token_status(token_value, {"state": "invalid", "message": "GitHub Token 无效或已过期，请更新后重试。"})
        profile_response.raise_for_status()
        profile = profile_response.json() if hasattr(profile_response, "json") else {}
        login = normalize(profile.get("login"))

        starred_response = session.get(
            "https://api.github.com/user/starred",
            params={"per_page": 1, "page": 1},
            timeout=api_timeout,
            headers=github_api_headers(token_value),
        )
        if starred_response.status_code == 401:
            return store_token_status(token_value, {"state": "invalid", "message": "GitHub Token 无效或已过期，请更新后重试。"})
        if starred_response.status_code in {403, 404}:
            return store_token_status(token_value, {
                "state": "insufficient",
                "message": "GitHub Token 已生效，但权限不足；当前可用于仓库详情和关键词发现，无法执行 GitHub 星标同步。",
                "login": login,
            })
        starred_response.raise_for_status()
        return store_token_status(token_value, {
            "state": "success",
            "message": "GitHub Token 校验通过，可用于仓库详情、关键词发现和 GitHub 星标同步。",
            "login": login,
        })

    def fetch_user_starred() -> list[dict[str, object]]:
        if not normalize(settings.get("github_token", "")):
            raise ValueError("请先在设置中配置 GitHub Token")
        repos: list[dict[str, object]] = []
        page = 1
        while True:
            response = session.get(
                "https://api.github.com/user/starred",
                params={"per_page": 100, "page": page},
                timeout=api_timeout,
                headers=github_api_headers(normalize(settings.get("github_token", ""))),
            )
            response.raise_for_status()
            items = response.json()
            if not items:
                break
            for item in items:
                full_name = normalize(item.get("full_name", ""))
                html_url = normalize(item.get("html_url", ""))
                if not full_name or "/" not in full_name:
                    continue
                repo = build_repo_record(
                    {
                        "full_name": full_name,
                        "url": html_url,
                        "description": normalize(item.get("description") or ""),
                        "description_raw": normalize(item.get("description") or ""),
                        "language": normalize(item.get("language") or ""),
                        "stars": int(item.get("stargazers_count") or 0),
                        "forks": int(item.get("forks_count") or 0),
                        "gained": 0,
                        "gained_text": "",
                        "growth_source": "unavailable",
                        "rank": 0,
                        "source_label": "GitHub 星标",
                        "source_key": "github_starred",
                    },
                    normalize=normalize,
                    clamp_int=clamp_int,
                    as_bool=as_bool,
                    default_source_label="GitHub 星标",
                )
                if repo:
                    repos.append(repo)
            if len(items) < 100:
                break
            page += 1
        return repos

    def fetch_repo_starred_state(owner: str, name: str) -> bool:
        response = session.get(
            f"https://api.github.com/user/starred/{owner}/{name}",
            timeout=api_timeout,
            headers=github_api_headers(normalize(settings.get("github_token", ""))),
        )
        if response.status_code == 204:
            return True
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return False

    def check_repo_starred(owner: str, name: str) -> bool:
        if not normalize(settings.get("github_token", "")):
            return False
        try:
            return fetch_repo_starred_state(owner, name)
        except Exception:
            return False

    def set_repo_starred(owner: str, name: str, enabled: bool) -> dict[str, object]:
        if not normalize(settings.get("github_token", "")):
            return {"ok": False, "error": "请先在设置中配置 GitHub Token", "code": "github_token_missing"}
        owner = normalize(owner)
        name = normalize(name)
        if not owner or not name:
            return {"ok": False, "error": "缺少仓库信息", "code": "repo_missing"}
        try:
            starred = fetch_repo_starred_state(owner, name)
            endpoint = f"https://api.github.com/user/starred/{owner}/{name}"
            if enabled:
                if starred:
                    return {"ok": False, "already_starred": True, "message": "该仓库已在你的 GitHub 星标中"}
                response = session.put(
                    endpoint,
                    timeout=api_timeout,
                    headers={**github_api_headers(normalize(settings.get("github_token", ""))), "Content-Length": "0"},
                )
                response.raise_for_status()
                return {"ok": True, "message": "已同步到 GitHub 星标 ⭐"}
            if not starred:
                return {"ok": False, "already_unstarred": True, "message": "该仓库已经不在你的 GitHub 星标中"}
            response = session.delete(
                endpoint,
                timeout=api_timeout,
                headers=github_api_headers(normalize(settings.get("github_token", ""))),
            )
            response.raise_for_status()
            return {"ok": True, "message": "已从 GitHub 取消星标"}
        except Exception as exc:
            logger.warning(
                "github_star_update_failed repo=%s/%s enabled=%s error=%s",
                owner,
                name,
                enabled,
                exc,
            )
            return {
                "ok": False,
                "error": "GitHub 星标同步失败，请检查 Token 与网络后重试。",
                "code": "github_star_update_failed",
            }

    def unstar_repo(owner: str, name: str) -> dict[str, object]:
        return set_repo_starred(owner, name, False)

    def sync_favorite_repo(repo: object, enabled: bool) -> dict[str, object] | None:
        if not normalize(settings.get("github_token", "")):
            return None
        clean = normalize_repo(repo)
        if not clean:
            raise ValueError("缺少仓库信息")
        return set_repo_starred(str(clean.get("owner") or ""), str(clean.get("name") or ""), enabled)

    return {
        "favorite_watch_policy": favorite_watch_policy,
        "should_refresh_release": should_refresh_release,
        "favorite_watch_candidates": favorite_watch_candidates,
        "should_stop_favorite_tracking": should_stop_favorite_tracking,
        "fetch_favorite_watch_snapshot": fetch_favorite_watch_snapshot,
        "build_favorite_update": build_favorite_update,
        "track_favorite_updates": track_favorite_updates,
        "clear_favorite_updates": clear_favorite_updates,
        "validate_github_token": validate_github_token,
        "fetch_user_starred": fetch_user_starred,
        "sync_local_favorites_with_starred": sync_local_favorites_with_starred,
        "fetch_repo_starred_state": fetch_repo_starred_state,
        "check_repo_starred": check_repo_starred,
        "set_repo_starred": set_repo_starred,
        "unstar_repo": unstar_repo,
        "sync_favorite_repo": sync_favorite_repo,
    }
