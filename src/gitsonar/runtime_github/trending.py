#!/usr/bin/env python3
from __future__ import annotations

import logging
from datetime import timezone

from ..runtime.repo_records import build_repo_record

logger = logging.getLogger(__name__)


def build_trending_api(*, deps, github_get):
    session = deps.session
    trending_timeout = deps.trending_timeout
    beautifulsoup_cls = deps.beautifulsoup_cls
    normalize = deps.normalize
    extract_count = deps.extract_count
    periods = deps.periods
    normalize_repo = deps.normalize_repo
    clamp_int = deps.clamp_int
    as_bool = lambda value, default=False: default if value is None else bool(value)
    settings = deps.settings
    datetime_cls = deps.datetime_cls
    timedelta_cls = deps.timedelta_cls
    search_api_url = deps.search_api_url
    thread_pool_executor_cls = deps.thread_pool_executor_cls
    as_completed = deps.as_completed
    load_snapshot = deps.load_snapshot
    translate_snapshot = deps.translate_snapshot
    iso_now = deps.iso_now

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
            repo = build_repo_record(
                {
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
                    "source_key": "trending",
                },
                normalize=normalize,
                clamp_int=clamp_int,
                as_bool=as_bool,
                default_period_key=period_key,
                default_source_label="GitHub Trending",
            )
            if repo:
                mapping[full_name.lower()] = repo
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
            repo = build_repo_record(
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
                    "source_key": "github_api",
                },
                normalize=normalize,
                clamp_int=clamp_int,
                as_bool=as_bool,
                default_period_key=key,
                default_source_label="GitHub API",
            )
            if repo:
                repos.append(repo)
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

    return {
        "fetch_trending_map": fetch_trending_map,
        "fetch_search_repos": fetch_search_repos,
        "fetch_period": fetch_period,
        "fetch_all": fetch_all,
    }
