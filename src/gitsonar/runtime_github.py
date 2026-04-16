#!/usr/bin/env python3
from __future__ import annotations

import base64
import logging
import math
import re
import threading
import time
from collections import Counter
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

    discovery_cache: dict[str, dict[str, object]] = {}
    discovery_cache_lock = threading.RLock()
    discovery_cache_seconds = 10 * 60
    query_term_re = re.compile(r"[a-z0-9][a-z0-9+.#/_-]*")
    stop_terms = {
        "a", "an", "and", "app", "apps", "awesome", "best", "build", "built", "cli", "code", "data",
        "for", "framework", "from", "github", "helper", "in", "is", "kit", "library", "of", "on", "open",
        "project", "python", "repo", "repository", "sdk", "simple", "starter", "template", "the", "to",
        "tool", "tools", "typescript", "with",
    }
    ranking_profiles = {"balanced", "hot", "fresh", "builder", "trend"}

    class DiscoveryCancelledError(RuntimeError):
        pass

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

    def clone_discovery_payload(payload: dict[str, object]) -> dict[str, object]:
        return {
            "ranking_profile": normalize_ranking_profile(payload.get("ranking_profile")),
            "translated_query": normalize(payload.get("translated_query")),
            "related_terms": [normalize(item) for item in payload.get("related_terms", []) if normalize(item)],
            "generated_queries": [normalize(item) for item in payload.get("generated_queries", []) if normalize(item)],
            "warnings": [normalize(item) for item in payload.get("warnings", []) if normalize(item)],
            "run_at": normalize(payload.get("run_at")),
            "results": [dict(item) for item in payload.get("results", []) if isinstance(item, dict)],
        }

    def extract_tokens(text: str) -> list[str]:
        lowered = normalize(text).lower()
        tokens: list[str] = []
        for token in query_term_re.findall(lowered):
            clean = token.strip("./-_")
            if len(clean) < 2 or clean.isdigit() or clean in stop_terms:
                continue
            tokens.append(clean)
        return list(dict.fromkeys(tokens))

    def build_query_terms(text: str) -> list[str]:
        lowered = normalize(text).lower()
        terms: list[str] = []
        if lowered and len(lowered) >= 2:
            terms.append(lowered)
        terms.extend(extract_tokens(lowered))
        return list(dict.fromkeys(terms))

    def build_discovery_search_query(search_text: str, language: str, recent_days: int = 0) -> str:
        parts = [normalize(search_text), "archived:false", "mirror:false"]
        if language:
            parts.append(f"language:{language}")
        if recent_days > 0:
            since = (datetime_cls.now(timezone.utc) - timedelta_cls(days=recent_days)).date().isoformat()
            parts.append(f"pushed:>={since}")
        return " ".join(part for part in parts if part)

    def build_discovery_repo(item: dict[str, object], spec: dict[str, object], index: int) -> dict[str, object]:
        full_name = normalize(item.get("full_name"))
        raw_description = normalize(item.get("description"))
        return {
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
            "period_key": "discover",
            "source_label": "关键词发现",
            "updated_at": normalize(item.get("updated_at")),
            "pushed_at": normalize(item.get("pushed_at")),
            "topics": item.get("topics", []) if isinstance(item.get("topics"), list) else [],
            "discover_source": normalize(spec.get("label")) or "query",
            "trending_hit": False,
            "relevance_score": 0,
            "hot_score": 0,
            "composite_score": 0,
            "matched_terms": [],
            "match_reasons": [],
            "_query_hits": [normalize(spec.get("text")).lower()],
            "_query_labels": [normalize(spec.get("label")) or "query"],
            "_search_sorts": [normalize(spec.get("sort")) or "stars"],
        }

    def merge_discovery_candidate(existing: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
        merged = dict(existing)
        merged["description_raw"] = normalize(merged.get("description_raw")) or normalize(incoming.get("description_raw"))
        merged["description"] = normalize(merged.get("description")) or normalize(incoming.get("description"))
        merged["language"] = normalize(merged.get("language")) or normalize(incoming.get("language"))
        merged["stars"] = max(clamp_int(merged.get("stars"), 0, 0), clamp_int(incoming.get("stars"), 0, 0))
        merged["forks"] = max(clamp_int(merged.get("forks"), 0, 0), clamp_int(incoming.get("forks"), 0, 0))
        merged["updated_at"] = normalize(incoming.get("updated_at")) or normalize(merged.get("updated_at"))
        merged["pushed_at"] = normalize(incoming.get("pushed_at")) or normalize(merged.get("pushed_at"))
        topics = [normalize(item) for item in [*(merged.get("topics", []) or []), *(incoming.get("topics", []) or [])] if normalize(item)]
        merged["topics"] = list(dict.fromkeys(topics))
        merged["_query_hits"] = list(dict.fromkeys([*(merged.get("_query_hits", []) or []), *(incoming.get("_query_hits", []) or [])]))
        merged["_query_labels"] = list(dict.fromkeys([*(merged.get("_query_labels", []) or []), *(incoming.get("_query_labels", []) or [])]))
        merged["_search_sorts"] = list(dict.fromkeys([*(merged.get("_search_sorts", []) or []), *(incoming.get("_search_sorts", []) or [])]))
        return merged

    def search_discovery_specs(
        specs: list[dict[str, object]],
        per_page: int,
        *,
        warnings: list[str] | None = None,
    ) -> list[dict[str, object]]:
        if not specs:
            return []
        merged: dict[str, dict[str, object]] = {}
        last_error: Exception | None = None
        with thread_pool_executor_cls(max_workers=min(4, len(specs))) as executor:
            future_map = {
                executor.submit(
                    github_get,
                    search_api_url,
                    params={
                        "q": build_discovery_search_query(
                            normalize(spec.get("text")),
                            normalize(spec.get("language")),
                            clamp_int(spec.get("recent_days"), 0, 0, 365),
                        ),
                        "sort": normalize(spec.get("sort")) or "stars",
                        "order": "desc",
                        "per_page": per_page,
                        "page": 1,
                    },
                ): spec
                for spec in specs
            }
            for future in as_completed(future_map):
                spec = future_map[future]
                try:
                    items = future.result().json().get("items", [])
                except Exception as exc:
                    last_error = exc
                    logger.warning("关键词发现搜索失败 %s: %s", spec.get("text"), exc)
                    if warnings is not None:
                        warnings.append(f"查询 {normalize(spec.get('text')) or '关键词'} 失败：{exc}")
                    continue
                for index, item in enumerate(items, start=1):
                    repo = normalize_repo(build_discovery_repo(item, spec, index))
                    if not repo:
                        continue
                    repo["_query_hits"] = [normalize(spec.get("text")).lower()]
                    repo["_query_labels"] = [normalize(spec.get("label")) or "query"]
                    repo["_search_sorts"] = [normalize(spec.get("sort")) or "stars"]
                    key = repo["full_name"].lower()
                    merged[key] = merge_discovery_candidate(merged[key], repo) if key in merged else repo
        if not merged and last_error:
            raise last_error
        return list(merged.values())

    def fetch_discovery_details_map(
        repos: list[dict[str, object]],
        detail_limit: int,
        *,
        warnings: list[str] | None = None,
    ) -> dict[str, dict[str, object]]:
        selected = [repo for repo in repos[:detail_limit] if normalize(repo.get("owner")) and normalize(repo.get("name"))]
        details_map: dict[str, dict[str, object]] = {}
        if not selected:
            return details_map
        with thread_pool_executor_cls(max_workers=min(4, len(selected))) as executor:
            future_map = {
                executor.submit(fetch_repo_details, repo["owner"], repo["name"]): repo
                for repo in selected
            }
            for future in as_completed(future_map):
                repo = future_map[future]
                try:
                    details_map[repo["full_name"].lower()] = future.result()
                except Exception as exc:
                    logger.warning("关键词发现详情补全失败 %s: %s", repo["full_name"], exc)
                    if warnings is not None:
                        warnings.append(f"详情补全失败：{repo['full_name']}")
        return details_map

    def build_compound_discovery_query(base_text: str, related_term: str) -> str:
        pieces = [*extract_tokens(base_text)[:3], normalize(related_term).lower()]
        pieces = [piece for piece in pieces if piece]
        if pieces:
            return " ".join(dict.fromkeys(pieces))
        return f"{normalize(base_text)} {normalize(related_term)}".strip()

    def extract_related_terms_from_candidates(
        repos: list[dict[str, object]],
        details_map: dict[str, dict[str, object]],
        base_terms: list[str],
    ) -> list[str]:
        counter: Counter[str] = Counter()
        blocked = set(base_terms) | set(stop_terms)
        for repo in repos:
            details = details_map.get(normalize(repo.get("full_name")).lower(), {})
            name_tokens = extract_tokens(repo.get("name"))
            topic_tokens: list[str] = []
            for topic in details.get("topics", []) or repo.get("topics", []) or []:
                topic_tokens.extend(extract_tokens(topic))
            desc_tokens = extract_tokens(details.get("description_raw") or repo.get("description_raw"))
            readme_tokens = extract_tokens(details.get("readme_summary_raw"))
            for token in name_tokens:
                if token not in blocked:
                    counter[token] += 4
            for token in topic_tokens:
                if token not in blocked:
                    counter[token] += 6
            for token in desc_tokens[:10]:
                if token not in blocked:
                    counter[token] += 2
            for token in readme_tokens[:12]:
                if token not in blocked:
                    counter[token] += 1
        return [term for term, _count in counter.most_common(6)]

    def trending_full_names_from_snapshot() -> set[str]:
        snapshot = load_snapshot()
        names: set[str] = set()
        for period in periods:
            for item in snapshot.get(period["key"], []):
                full_name = normalize(item.get("full_name")).lower()
                if full_name:
                    names.add(full_name)
        return names

    def days_since_repo_activity(repo: dict[str, object], details: dict[str, object]) -> int:
        timestamp = parse_iso_timestamp(
            details.get("pushed_at")
            or repo.get("pushed_at")
            or details.get("updated_at")
            or repo.get("updated_at")
        )
        if not timestamp:
            return 99999
        return max(0, int((time.time() - timestamp) // 86400))

    def format_metric(value: int) -> str:
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}k"
        return str(value)

    def normalize_ranking_profile(value: object) -> str:
        clean = normalize(value).lower()
        return clean if clean in ranking_profiles else "balanced"

    def score_discovery_repo(
        repo: dict[str, object],
        details: dict[str, object],
        *,
        base_terms: list[str],
        query_variants: list[str],
        related_terms: list[str],
        trending_names: set[str],
        allow_description_translation: bool = True,
        ranking_profile: str = "balanced",
    ) -> dict[str, object]:
        ranking_profile = normalize_ranking_profile(ranking_profile)
        full_name = normalize(repo.get("full_name"))
        name_text = f"{full_name} {normalize(repo.get('name'))}".lower()
        desc_raw = normalize(details.get("description_raw") or repo.get("description_raw"))
        desc_text = normalize(
            details.get("description")
            or repo.get("description")
            or (translate_text(desc_raw) if allow_description_translation else desc_raw)
        ).lower()
        readme_raw = normalize(details.get("readme_summary_raw"))
        readme_text = normalize(details.get("readme_summary")).lower()
        topics = [normalize(item).lower() for item in (details.get("topics") or repo.get("topics") or []) if normalize(item)]
        topic_text = " ".join(topics)
        body_text = " ".join(part for part in [desc_raw.lower(), desc_text, readme_raw.lower(), readme_text] if part)

        exact_phrase = next(
            (term for term in query_variants if term and len(term) >= 2 and (term in name_text or term in topic_text or term in body_text)),
            "",
        )
        matched_base_name = [term for term in base_terms if term and len(term) >= 2 and term in name_text]
        matched_base_topic = [term for term in base_terms if term and len(term) >= 2 and term in topic_text and term not in matched_base_name]
        matched_base_body = [
            term for term in base_terms
            if term and len(term) >= 2 and term in body_text and term not in matched_base_name and term not in matched_base_topic
        ]
        matched_related = [
            term for term in related_terms
            if term and len(term) >= 2 and (term in name_text or term in topic_text or term in body_text)
        ]

        relevance_score = 0
        if exact_phrase:
            relevance_score += 24
        relevance_score += min(36, 14 * len(matched_base_name))
        relevance_score += min(24, 10 * len(matched_base_topic))
        relevance_score += min(24, 8 * len(matched_base_body))
        relevance_score += min(18, 6 * len(matched_related))
        relevance_score += min(10, 3 * len(repo.get("_query_hits", []) or []))
        relevance_score = min(100, relevance_score)

        stars = clamp_int(details.get("stars"), clamp_int(repo.get("stars"), 0, 0), 0)
        forks = clamp_int(details.get("forks"), clamp_int(repo.get("forks"), 0, 0), 0)
        activity_days = days_since_repo_activity(repo, details)
        trending_hit = full_name.lower() in trending_names
        license_id = normalize(details.get("license"))
        homepage = normalize(details.get("homepage"))
        readme_available = bool(readme_raw or readme_text)
        stars_score = min(55, int(round(math.log10(stars + 1) * 14)))
        forks_score = min(10, int(round(math.log10(forks + 1) * 4)))
        freshness_score = 30 if activity_days <= 7 else 24 if activity_days <= 30 else 16 if activity_days <= 90 else 8 if activity_days <= 180 else 0
        activity_score = 100 if activity_days <= 7 else 82 if activity_days <= 30 else 60 if activity_days <= 90 else 28 if activity_days <= 180 else 8
        trend_score = 15 if trending_hit else 0
        hot_score = min(100, stars_score + forks_score + freshness_score + trend_score)
        docs_score = 18 if readme_available else 0
        topic_score = min(18, len(topics) * 4)
        license_score = 14 if license_id and license_id != "未标注" else 0
        homepage_score = 6 if homepage else 0
        engineering_score = min(100, docs_score + topic_score + license_score + homepage_score + min(20, activity_score // 4) + min(18, relevance_score // 5))
        trendiness_score = min(100, (54 if trending_hit else 0) + min(28, activity_score // 2) + min(18, stars_score // 2) + min(12, len(repo.get("_query_hits", []) or []) * 4))
        if ranking_profile == "hot":
            composite_score = min(100, int(round(relevance_score * 0.34 + hot_score * 0.66)))
        elif ranking_profile == "fresh":
            composite_score = min(100, int(round(relevance_score * 0.30 + activity_score * 0.52 + hot_score * 0.18)))
        elif ranking_profile == "builder":
            composite_score = min(100, int(round(relevance_score * 0.36 + engineering_score * 0.42 + hot_score * 0.22)))
        elif ranking_profile == "trend":
            composite_score = min(100, int(round(relevance_score * 0.24 + trendiness_score * 0.54 + hot_score * 0.22)))
        else:
            composite_score = min(100, int(round(relevance_score * 0.58 + hot_score * 0.42)))

        reasons: list[str] = []
        if matched_base_name:
            reasons.append(f"仓库名命中“{matched_base_name[0]}”")
        elif exact_phrase:
            reasons.append(f"关键词短语命中“{exact_phrase}”")
        if matched_base_topic:
            reasons.append(f"Topic 命中“{matched_base_topic[0]}”")
        if matched_related:
            reasons.append(f"相关词命中“{matched_related[0]}”")
        if activity_days <= 30:
            reasons.append(f"最近 {max(1, activity_days)} 天仍有提交")
        if trending_hit:
            reasons.append("出现在当前热门快照")
        if stars >= 1000:
            reasons.append(f"Stars {format_metric(stars)}")
        if ranking_profile == "fresh" and activity_days <= 30:
            reasons.append("排序偏向最近活跃项目")
        elif ranking_profile == "builder" and (readme_available or license_score or topic_score):
            reasons.append("工程信息相对完整")
        elif ranking_profile == "trend" and (trending_hit or activity_days <= 30):
            reasons.append("排序偏向趋势信号")
        elif ranking_profile == "hot" and stars >= 1000:
            reasons.append("排序偏向高热度项目")

        result = dict(repo)
        result.update({
            "description_raw": desc_raw,
            "description": normalize(details.get("description")) or translate_text(desc_raw),
            "language": normalize(repo.get("language")),
            "stars": stars,
            "forks": forks,
            "updated_at": normalize(details.get("updated_at") or repo.get("updated_at")),
            "pushed_at": normalize(details.get("pushed_at") or repo.get("pushed_at")),
            "topics": topics,
            "source_label": "关键词发现",
            "period_key": "discover",
            "discover_source": "keyword-discovery",
            "trending_hit": trending_hit,
            "relevance_score": relevance_score,
            "hot_score": hot_score,
            "composite_score": composite_score,
            "ranking_profile": ranking_profile,
            "ranking_signal_score": engineering_score if ranking_profile == "builder" else trendiness_score if ranking_profile == "trend" else activity_score if ranking_profile == "fresh" else hot_score,
            "matched_terms": list(dict.fromkeys([*matched_base_name, *matched_base_topic, *matched_base_body, *matched_related]))[:10],
            "match_reasons": list(dict.fromkeys(reasons))[:4],
        })
        result.pop("_query_hits", None)
        result.pop("_query_labels", None)
        result.pop("_search_sorts", None)
        return result

    def rank_discovery_results(
        repos: list[dict[str, object]],
        details_map: dict[str, dict[str, object]],
        *,
        base_terms: list[str],
        search_variants: list[str],
        query_variants: list[str],
        related_terms: list[str],
        trending_names: set[str],
        limit: int,
        allow_description_translation: bool = True,
        ranking_profile: str = "balanced",
    ) -> list[dict[str, object]]:
        scored = [
            score_discovery_repo(
                repo,
                details_map.get(repo["full_name"].lower(), {}),
                base_terms=base_terms,
                query_variants=search_variants + query_variants,
                related_terms=related_terms,
                trending_names=trending_names,
                allow_description_translation=allow_description_translation,
                ranking_profile=ranking_profile,
            )
            for repo in repos
        ]
        ranked = [repo for repo in scored if normalize_repo(repo)]
        ranked.sort(
            key=lambda item: (
                -clamp_int(item.get("composite_score"), 0, 0),
                -clamp_int(item.get("relevance_score"), 0, 0),
                -clamp_int(item.get("hot_score"), 0, 0),
                -clamp_int(item.get("stars"), 0, 0),
                normalize(item.get("full_name")),
            )
        )
        for index, repo in enumerate(ranked[:limit], start=1):
            repo["rank"] = index
        return ranked

    def emit_discovery_progress(progress_callback, stage: str, payload: dict[str, object]) -> None:
        if not callable(progress_callback):
            return
        try:
            progress_callback(stage, payload)
        except Exception as exc:
            logger.warning("关键词发现进度回调失败 %s: %s", stage, exc)

    def ensure_discovery_not_cancelled(cancel_callback) -> None:
        if not callable(cancel_callback):
            return
        if cancel_callback():
            raise DiscoveryCancelledError("关键词发现已取消")

    def discover_repos(
        *,
        query: str,
        language: str = "",
        limit: int = 20,
        auto_expand: bool = True,
        ranking_profile: str = "balanced",
        progress_callback=None,
        is_cancelled=None,
    ) -> dict[str, object]:
        query = normalize(query)
        language = normalize(language)
        ranking_profile = normalize_ranking_profile(ranking_profile)
        limit = clamp_int(limit, 20, 5, 50)
        if not query:
            raise ValueError("请输入关键词")

        cache_key = f"{query.lower()}|{language.lower()}|{limit}|{int(bool(auto_expand))}|{ranking_profile}"
        now = int(time.time())
        has_token = bool(normalize(settings.get("github_token", "")))
        seed_detail_limit = min(max(limit // 2, 6), 8) if has_token else 0
        full_detail_limit = min(max(limit // 2 + 4, 8), 14) if has_token else 0
        expansion_limit = 3 if has_token else 2
        with discovery_cache_lock:
            cached = discovery_cache.get(cache_key)
            if isinstance(cached, dict) and now - clamp_int(cached.get("saved_at"), 0, 0) < discovery_cache_seconds:
                return clone_discovery_payload(cached.get("payload", {}))

        translated_query = normalize(translate_query_to_en(query))
        search_variants: list[str] = []
        for item in [query, translated_query]:
            clean = normalize(item)
            if clean and clean.lower() not in {value.lower() for value in search_variants}:
                search_variants.append(clean)
        query_variants = list(dict.fromkeys(term for item in search_variants for term in build_query_terms(item)))
        base_terms = query_variants[:]

        initial_specs: list[dict[str, object]] = []
        for text in search_variants[:2]:
            initial_specs.append({"text": text, "sort": "stars", "recent_days": 0, "label": "query", "language": language})
        primary_variant = search_variants[-1] if search_variants else query
        initial_specs.append({"text": primary_variant, "sort": "updated", "recent_days": 180, "label": "fresh", "language": language})

        generated_queries = list(dict.fromkeys(normalize(spec.get("text")) for spec in initial_specs if normalize(spec.get("text"))))
        candidate_map: dict[str, dict[str, object]] = {}
        warnings: list[str] = []
        emit_discovery_progress(progress_callback, "initial_search", {
            "ranking_profile": ranking_profile,
            "translated_query": translated_query if translated_query.lower() != query.lower() else "",
            "generated_queries": generated_queries,
            "related_terms": [],
            "warnings": [],
            "results": [],
        })
        ensure_discovery_not_cancelled(is_cancelled)
        for repo in search_discovery_specs(
            initial_specs,
            per_page=min(max(limit * 3, 18), 50),
            warnings=warnings,
        ):
            candidate_map[repo["full_name"].lower()] = repo

        if not candidate_map:
            payload = {
                "ranking_profile": ranking_profile,
                "translated_query": translated_query if translated_query.lower() != query.lower() else "",
                "related_terms": [],
                "generated_queries": generated_queries,
                "warnings": list(dict.fromkeys(warnings))[:6],
                "run_at": iso_now(),
                "results": [],
            }
            with discovery_cache_lock:
                discovery_cache[cache_key] = {"saved_at": now, "payload": clone_discovery_payload(payload)}
            emit_discovery_progress(progress_callback, "completed", payload)
            return payload

        initial_candidates = sorted(candidate_map.values(), key=lambda item: (-clamp_int(item.get("stars"), 0, 0), normalize(item.get("full_name"))))
        trending_names = trending_full_names_from_snapshot()
        preview_ranked = rank_discovery_results(
            initial_candidates,
            {},
            base_terms=base_terms,
            search_variants=search_variants,
            query_variants=query_variants,
            related_terms=[],
            trending_names=trending_names,
            limit=limit,
            allow_description_translation=False,
            ranking_profile=ranking_profile,
        )
        emit_discovery_progress(progress_callback, "initial_results", {
            "ranking_profile": ranking_profile,
            "translated_query": translated_query if translated_query.lower() != query.lower() else "",
            "generated_queries": generated_queries,
            "related_terms": [],
            "warnings": list(dict.fromkeys(warnings))[:6],
            "results": preview_ranked[:limit],
        })
        ensure_discovery_not_cancelled(is_cancelled)

        emit_discovery_progress(progress_callback, "seed_details", {
            "ranking_profile": ranking_profile,
            "translated_query": translated_query if translated_query.lower() != query.lower() else "",
            "generated_queries": generated_queries,
            "related_terms": [],
            "warnings": list(dict.fromkeys(warnings))[:6],
            "results": preview_ranked[:limit],
        })
        seed_details_map = fetch_discovery_details_map(
            initial_candidates,
            detail_limit=seed_detail_limit,
            warnings=warnings,
        )
        related_terms = extract_related_terms_from_candidates(initial_candidates[:10], seed_details_map, base_terms) if auto_expand else []
        ensure_discovery_not_cancelled(is_cancelled)

        if auto_expand and related_terms:
            existing_queries = {item.lower() for item in generated_queries}
            expansion_specs: list[dict[str, object]] = []
            for term in related_terms[:expansion_limit]:
                compound = build_compound_discovery_query(primary_variant, term)
                if not compound or compound.lower() in existing_queries:
                    continue
                existing_queries.add(compound.lower())
                generated_queries.append(compound)
                expansion_specs.append({"text": compound, "sort": "stars", "recent_days": 365, "label": "related", "language": language})
            emit_discovery_progress(progress_callback, "expansion_search", {
                "ranking_profile": ranking_profile,
                "translated_query": translated_query if translated_query.lower() != query.lower() else "",
                "generated_queries": generated_queries,
                "related_terms": related_terms,
                "warnings": list(dict.fromkeys(warnings))[:6],
                "results": preview_ranked[:limit],
            })
            try:
                expansion_results = search_discovery_specs(
                    expansion_specs,
                    per_page=min(max(limit * 2, 12), 40),
                    warnings=warnings,
                )
            except Exception as exc:
                logger.warning("关键词发现扩词阶段降级为首轮结果: %s", exc)
                expansion_results = []
                warnings.append(f"扩词阶段已降级：{exc}")
            for repo in expansion_results:
                key = repo["full_name"].lower()
                candidate_map[key] = merge_discovery_candidate(candidate_map[key], repo) if key in candidate_map else repo
            ensure_discovery_not_cancelled(is_cancelled)

        candidates = sorted(
            candidate_map.values(),
            key=lambda item: (-clamp_int(item.get("stars"), 0, 0), -clamp_int(item.get("forks"), 0, 0), normalize(item.get("full_name"))),
        )
        emit_discovery_progress(progress_callback, "rescoring", {
            "ranking_profile": ranking_profile,
            "translated_query": translated_query if translated_query.lower() != query.lower() else "",
            "generated_queries": generated_queries,
            "related_terms": related_terms,
            "warnings": list(dict.fromkeys(warnings))[:6],
            "results": preview_ranked[:limit],
        })
        details_map = dict(seed_details_map)
        details_map.update(
            fetch_discovery_details_map(
                candidates,
                detail_limit=full_detail_limit,
                warnings=warnings,
            )
        )
        ensure_discovery_not_cancelled(is_cancelled)
        ranked = rank_discovery_results(
            candidates,
            details_map,
            base_terms=base_terms,
            search_variants=search_variants,
            query_variants=query_variants,
            related_terms=related_terms,
            trending_names=trending_names,
            limit=limit,
            ranking_profile=ranking_profile,
        )
        save_translation_cache()
        payload = {
            "ranking_profile": ranking_profile,
            "translated_query": translated_query if translated_query.lower() != query.lower() else "",
            "related_terms": related_terms,
            "generated_queries": generated_queries,
            "warnings": list(dict.fromkeys(warnings))[:6],
            "run_at": iso_now(),
            "results": ranked[:limit],
        }
        with discovery_cache_lock:
            discovery_cache[cache_key] = {"saved_at": now, "payload": clone_discovery_payload(payload)}
        emit_discovery_progress(progress_callback, "completed", payload)
        return payload

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
                headers={"Accept": "application/vnd.github+json"},
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
                repos.append({
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
                })
            if len(items) < 100:
                break
            page += 1
        return repos

    def check_repo_starred(owner: str, name: str) -> bool:
        if not normalize(settings.get("github_token", "")):
            return False
        try:
            response = session.get(
                f"https://api.github.com/user/starred/{owner}/{name}",
                timeout=api_timeout,
                headers={"Accept": "application/vnd.github+json"},
            )
            return response.status_code == 204
        except Exception:
            return False

    def star_repo(owner: str, name: str) -> dict[str, object]:
        if not normalize(settings.get("github_token", "")):
            return {"ok": False, "error": "请先在设置中配置 GitHub Token"}
        try:
            if check_repo_starred(owner, name):
                return {"ok": False, "already_starred": True, "message": "该仓库已在你的 GitHub 星标中"}
            response = session.put(
                f"https://api.github.com/user/starred/{owner}/{name}",
                timeout=api_timeout,
                headers={"Accept": "application/vnd.github+json", "Content-Length": "0"},
            )
            response.raise_for_status()
            return {"ok": True, "message": "已同步到 GitHub 星标 ⭐"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    return SimpleNamespace(
        DiscoveryCancelledError=DiscoveryCancelledError,
        github_get=github_get,
        fetch_trending_map=fetch_trending_map,
        fetch_search_repos=fetch_search_repos,
        fetch_period=fetch_period,
        fetch_all=fetch_all,
        fetch_repo_details=fetch_repo_details,
        discover_repos=discover_repos,
        normalize_ranking_profile=normalize_ranking_profile,
        score_discovery_repo=score_discovery_repo,
        rank_discovery_results=rank_discovery_results,
        favorite_watch_policy=favorite_watch_policy,
        should_refresh_release=should_refresh_release,
        favorite_watch_candidates=favorite_watch_candidates,
        should_stop_favorite_tracking=should_stop_favorite_tracking,
        fetch_favorite_watch_snapshot=fetch_favorite_watch_snapshot,
        build_favorite_update=build_favorite_update,
        track_favorite_updates=track_favorite_updates,
        clear_favorite_updates=clear_favorite_updates,
        fetch_user_starred=fetch_user_starred,
        check_repo_starred=check_repo_starred,
        star_repo=star_repo,
    )
