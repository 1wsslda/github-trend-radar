#!/usr/bin/env python3
from __future__ import annotations

import base64
import logging
import time
from datetime import timezone
from types import SimpleNamespace

logger = logging.getLogger(__name__)


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
    def github_get(
        url: str,
        *,
        params: dict[str, object] | None = None,
        timeout: tuple[int, int] = api_timeout,
        accept: str = "application/vnd.github+json",
    ):
        response = session.get(url, params=params, timeout=timeout, headers={"Accept": accept})
        response.raise_for_status()
        return response

    def fetch_trending_map(period_key: str) -> dict[str, dict[str, object]]:
        response = session.get(f"https://github.com/trending?since={period_key}", timeout=trending_timeout)
        response.raise_for_status()
        soup = beautifulsoup_cls(response.text, "html.parser")
        mapping: dict[str, dict[str, object]] = {}
        for rank, article in enumerate(soup.select("article.Box-row"), start=1):
            link = article.select_one("h2 a")
            if not link:
                continue
            full_name = normalize(link.get("href")).strip("/").replace(" ", "")
            if "/" not in full_name:
                continue
            anchors = article.select("a.Link--muted")
            desc_node = article.select_one("p")
            language_node = article.select_one('span[itemprop="programmingLanguage"]')
            gained_node = article.select_one("span.d-inline-block.float-sm-right")
            mapping[full_name.lower()] = {
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": normalize(desc_node.get_text(" ", strip=True) if desc_node else ""),
                "language": normalize(language_node.get_text(" ", strip=True) if language_node else ""),
                "stars": extract_count(anchors[0].get_text(" ", strip=True) if len(anchors) > 0 else 0),
                "forks": extract_count(anchors[1].get_text(" ", strip=True) if len(anchors) > 1 else 0),
                "gained": extract_count(gained_node.get_text(" ", strip=True) if gained_node else ""),
                "gained_text": normalize(gained_node.get_text(" ", strip=True) if gained_node else ""),
                "growth_source": "trending",
                "rank": rank,
                "period_key": period_key,
                "source_label": "GitHub Trending",
            }
        return mapping

    def build_previous_repo_index(snapshot: dict[str, object]) -> dict[str, dict[str, object]]:
        index: dict[str, dict[str, object]] = {}
        for period in periods:
            for item in snapshot.get(period["key"], []):
                repo = normalize_repo(item)
                if not repo:
                    continue
                keys = {normalize(repo.get("url")).lower(), normalize(repo.get("full_name")).lower()}
                for key in keys:
                    if not key:
                        continue
                    previous = index.get(key)
                    if previous is None or clamp_int(repo.get("stars"), 0, 0) >= clamp_int(previous.get("stars"), 0, 0):
                        index[key] = repo
        return index

    def enrich_repo_growth(repo: dict[str, object], previous_repo_index: dict[str, dict[str, object]]) -> dict[str, object]:
        enriched = dict(repo)
        if normalize(enriched.get("gained_text")) or clamp_int(enriched.get("gained"), 0, 0) > 0:
            enriched["growth_source"] = "trending"
            return enriched

        lookup_keys = [
            normalize(enriched.get("url")).lower(),
            normalize(enriched.get("full_name")).lower(),
        ]
        previous: dict[str, object] | None = None
        for key in lookup_keys:
            if key and key in previous_repo_index:
                previous = previous_repo_index[key]
                break

        if not previous:
            enriched["gained"] = 0
            enriched["gained_text"] = "待下次估算"
            enriched["growth_source"] = "unavailable"
            return enriched

        current_stars = clamp_int(enriched.get("stars"), 0, 0)
        previous_stars = clamp_int(previous.get("stars"), 0, 0)
        delta = max(0, current_stars - previous_stars)
        enriched["gained"] = delta
        enriched["gained_text"] = f"较上次 +{delta}" if delta > 0 else "较上次持平"
        enriched["growth_source"] = "estimated"
        source_label = normalize(enriched.get("source_label"))
        enriched["source_label"] = f"{source_label} + 本地估算" if source_label else "本地估算"
        return enriched

    def fetch_search_repos(period: dict[str, object], limit: int) -> list[dict[str, object]]:
        key = str(period["key"])
        since = (datetime_cls.now(timezone.utc) - timedelta_cls(days=int(period["days"]))).date().isoformat()
        items = github_get(
            search_api_url,
            params={
                "q": f"pushed:>={since} archived:false mirror:false",
                "sort": "stars",
                "order": "desc",
                "per_page": min(max(limit, 30), 100),
                "page": 1,
            },
        ).json().get("items", [])

        repos: list[dict[str, object]] = []
        for index, item in enumerate(items, start=1):
            full_name = normalize(item.get("full_name"))
            raw_description = normalize(item.get("description"))
            repos.append(
                {
                    "full_name": full_name,
                    "url": normalize(item.get("html_url")) or f"https://github.com/{full_name}",
                    "description": raw_description,
                    "description_raw": raw_description,
                    "language": normalize(item.get("language")),
                    "stars": clamp_int(item.get("stargazers_count"), 0, 0),
                    "forks": clamp_int(item.get("forks_count"), 0, 0),
                    "gained": 0,
                    "gained_text": "",
                    "growth_source": "unavailable",
                    "rank": index,
                    "period_key": key,
                    "source_label": "GitHub API",
                }
            )
            if len(repos) >= limit:
                break
        return repos

    def fetch_period(period: dict[str, object], fallback: dict[str, object]) -> list[dict[str, object]]:
        limit = clamp_int(settings.get("result_limit", 25), 25, 10, 100)
        key = str(period["key"])
        logger.info("抓取 %s 数据...", period["label"])
        previous_repo_index = build_previous_repo_index(fallback)

        api_repos: list[dict[str, object]] = []
        trending: dict[str, dict[str, object]] = {}
        api_error: Exception | None = None
        trending_error: Exception | None = None

        with thread_pool_executor_cls(max_workers=2) as executor:
            futures = {
                executor.submit(fetch_search_repos, period, limit): "api",
                executor.submit(fetch_trending_map, key): "trending",
            }
            for future in as_completed(futures):
                target = futures[future]
                try:
                    result = future.result()
                    if target == "api":
                        api_repos = result
                    else:
                        trending = result
                except Exception as exc:
                    if target == "api":
                        api_error = exc
                    else:
                        trending_error = exc

        if api_error:
            logger.warning("GitHub API 获取失败 %s: %s", key, api_error)
        if trending_error:
            logger.warning("Trending 抓取失败 %s: %s", key, trending_error)

        if trending:
            api_by_name = {repo["full_name"].lower(): repo for repo in api_repos}
            repos: list[dict[str, object]] = []
            used_names: set[str] = set()

            for extra in trending.values():
                full_name = normalize(extra.get("full_name"))
                merged = dict(extra)
                api_repo = api_by_name.get(full_name.lower())
                if api_repo:
                    merged["url"] = normalize(api_repo.get("url")) or normalize(extra.get("url"))
                    merged["stars"] = clamp_int(api_repo.get("stars"), clamp_int(extra.get("stars"), 0, 0), 0)
                    merged["forks"] = clamp_int(api_repo.get("forks"), clamp_int(extra.get("forks"), 0, 0), 0)
                    merged["language"] = normalize(api_repo.get("language")) or normalize(extra.get("language"))
                    merged["description_raw"] = normalize(
                        extra.get("description")
                        or api_repo.get("description_raw")
                        or api_repo.get("description")
                    )
                    merged["description"] = merged["description_raw"]
                    merged["source_label"] = "GitHub Trending + API"
                    merged["growth_source"] = "trending"
                else:
                    merged["description_raw"] = normalize(
                        extra.get("description") or extra.get("description_raw")
                    )
                    merged["description"] = merged["description_raw"]
                    merged["source_label"] = "GitHub Trending"
                    merged["growth_source"] = "trending"

                repos.append(merged)
                used_names.add(full_name.lower())
                if len(repos) >= limit:
                    break

            for repo in api_repos:
                if len(repos) >= limit:
                    break
                if repo["full_name"].lower() in used_names:
                    continue
                fallback_repo = enrich_repo_growth(dict(repo), previous_repo_index)
                fallback_repo["rank"] = len(repos) + 1
                repos.append(fallback_repo)

            cleaned = [repo for item in repos if (repo := normalize_repo(item))]
            logger.info("抓取 %s: 获取 %d 个仓库", key, len(cleaned))
            return cleaned[:limit]

        if api_repos:
            cleaned = [repo for item in (enrich_repo_growth(dict(repo), previous_repo_index) for repo in api_repos) if (repo := normalize_repo(item))]
            logger.info("抓取 %s: GitHub API 回退 %d 条", key, len(cleaned))
            return cleaned[:limit]

        cached = [repo for item in fallback.get(key, []) if (repo := normalize_repo(item))][:limit]
        logger.warning("抓取 %s: 使用本地缓存回退 %d 条", key, len(cached))
        return cached

    def fetch_all() -> dict[str, object]:
        fallback = load_snapshot()
        snapshot = {"fetched_at": iso_now(), **{period["key"]: [] for period in periods}}
        with thread_pool_executor_cls(max_workers=len(periods)) as executor:
            future_map = {executor.submit(fetch_period, period, fallback): period for period in periods}
            for future in as_completed(future_map):
                period = future_map[future]
                try:
                    snapshot[period["key"]] = future.result()
                except Exception as exc:
                    logger.error("抓取 %s 时发生异常，保留上次缓存: %s", period["key"], exc)
                    snapshot[period["key"]] = fallback.get(period["key"], [])
        translate_snapshot(snapshot)
        snapshot["fetched_at"] = iso_now()
        return snapshot

    def fetch_repo_details(owner: str, name: str) -> dict[str, object]:
        owner = normalize(owner)
        name = normalize(name)
        if not owner or not name:
            raise ValueError("缺少仓库参数")

        cache_key = f"{owner}/{name}".lower()
        cached = cached_repo_details(cache_key)
        if cached is not None:
            return cached

        with detail_fetch_lock(cache_key):
            cached = cached_repo_details(cache_key)
            if cached is not None:
                return cached

            with fetch_semaphore:
                repo = github_get(f"{repo_api_url}/{owner}/{name}").json()
                try:
                    readme = github_get(f"{repo_api_url}/{owner}/{name}/readme").json()
                    if readme.get("encoding") == "base64":
                        content = base64.b64decode(readme.get("content", "")).decode("utf-8", errors="ignore")
                    else:
                        content = ""
                    summary = strip_markdown(content)[:900]
                except Exception:
                    summary = ""

            raw_description = normalize(repo.get("description"))
            raw_summary = normalize(summary)
            details = {
                "full_name": normalize(repo.get("full_name")) or f"{owner}/{name}",
                "description": translate_text(raw_description),
                "description_raw": raw_description,
                "license": normalize(
                    repo.get("license", {}).get("spdx_id") if isinstance(repo.get("license"), dict) else ""
                )
                or "未标注",
                "homepage": normalize(repo.get("homepage")),
                "default_branch": normalize(repo.get("default_branch")),
                "updated_at": normalize(repo.get("updated_at")),
                "pushed_at": normalize(repo.get("pushed_at")),
                "topics": repo.get("topics", []) if isinstance(repo.get("topics"), list) else [],
                "html_url": normalize(repo.get("html_url")) or f"https://github.com/{owner}/{name}",
                "stars": clamp_int(repo.get("stargazers_count"), 0, 0),
                "forks": clamp_int(repo.get("forks_count"), 0, 0),
                "watchers": clamp_int(repo.get("watchers_count"), 0, 0),
                "open_issues": clamp_int(repo.get("open_issues_count"), 0, 0),
                "readme_summary": translate_text(raw_summary),
                "readme_summary_raw": raw_summary,
            }
            save_translation_cache()
            save_repo_details(cache_key, details)
            return dict(details)

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
        if isinstance(exc, requests_module.HTTPError):
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
            except requests_module.HTTPError as exc:
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
            except Exception:
                if previous:
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
            changes.append(f"Stars {'+' if star_delta > 0 else ''}{star_delta}")

        fork_delta = clamp_int(after.get("forks"), 0, 0) - clamp_int(before.get("forks"), 0, 0)
        if fork_delta:
            changes.append(f"Forks {'+' if fork_delta > 0 else ''}{fork_delta}")

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
        if len(due_repos) < len(repos):
            logger.info("收藏更新追踪: 本轮检查 %d/%d 个收藏仓库", len(due_repos), len(repos))

        for repo in due_repos:
            url = repo["url"]
            try:
                snapshot = normalize_watch_entry(
                    fetch_favorite_watch_snapshot(repo, previous_watch.get(url), release_min_seconds)
                )
            except Exception as exc:
                if should_stop_favorite_tracking(exc):
                    logger.warning("收藏更新追踪触发限流，本轮剩余仓库跳过: %s", exc)
                    break
                logger.warning("收藏更新追踪失败 %s: %s", repo["full_name"], exc)
                continue

            if not snapshot:
                continue

            fresh_watch[url] = snapshot
            if update := build_favorite_update(previous_watch.get(url), snapshot):
                updates.insert(0, update)
                new_update_count += 1

        if not fresh_watch:
            return 0

        fav_set = set(favorite_urls)
        normalized_updates = [
            item for entry in updates
            if (item := normalize_favorite_update(entry)) and item["url"] in fav_set
        ]
        normalized_updates = normalized_updates[:100]

        with state_lock:
            user_state["favorite_watch"] = {
                url: item for url, item in user_state.get("favorite_watch", {}).items() if url in favorite_urls
            }
            user_state["favorite_watch"].update(fresh_watch)
            user_state["favorite_updates"] = normalized_updates
            save_user_state()

        return new_update_count

    def clear_favorite_updates() -> None:
        with state_lock:
            user_state["favorite_updates"] = []
            save_user_state()

    return SimpleNamespace(
        github_get=github_get,
        fetch_trending_map=fetch_trending_map,
        fetch_search_repos=fetch_search_repos,
        fetch_period=fetch_period,
        fetch_all=fetch_all,
        fetch_repo_details=fetch_repo_details,
        favorite_watch_policy=favorite_watch_policy,
        should_refresh_release=should_refresh_release,
        favorite_watch_candidates=favorite_watch_candidates,
        should_stop_favorite_tracking=should_stop_favorite_tracking,
        fetch_favorite_watch_snapshot=fetch_favorite_watch_snapshot,
        build_favorite_update=build_favorite_update,
        track_favorite_updates=track_favorite_updates,
        clear_favorite_updates=clear_favorite_updates,
    )
