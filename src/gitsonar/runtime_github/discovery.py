#!/usr/bin/env python3
from __future__ import annotations

import logging
import math
import time
from collections import Counter
from datetime import timezone

from ..runtime.repo_records import build_repo_record

from .shared import DiscoveryCancelledError

logger = logging.getLogger(__name__)


def build_discovery_api(*, deps, state, github_get, fetch_repo_details):
    settings = deps.settings
    periods = deps.periods
    normalize = deps.normalize
    clamp_int = deps.clamp_int
    translate_query_to_en = deps.translate_query_to_en
    iso_now = deps.iso_now
    load_snapshot = deps.load_snapshot
    thread_pool_executor_cls = deps.thread_pool_executor_cls
    as_completed = deps.as_completed
    normalize_repo = deps.normalize_repo
    translate_text = deps.translate_text
    parse_iso_timestamp = deps.parse_iso_timestamp
    datetime_cls = deps.datetime_cls
    timedelta_cls = deps.timedelta_cls
    flush_translation_cache = deps.flush_translation_cache
    flush_repo_details_cache = deps.flush_repo_details_cache
    search_api_url = deps.search_api_url
    as_bool = lambda value, default=False: default if value is None else bool(value)
    query_term_re = state.query_term_re
    stop_terms = state.stop_terms
    ranking_profiles = state.ranking_profiles
    discovery_cache = state.discovery_cache
    discovery_cache_lock = state.discovery_cache_lock
    discovery_cache_seconds = state.discovery_cache_seconds
    discovery_cache_max_entries = state.discovery_cache_max_entries

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
                "source_key": "discover",
            },
            normalize=normalize,
            clamp_int=clamp_int,
            as_bool=as_bool,
            default_period_key="discover",
            default_source_label="Keyword Discovery",
        )
        return repo or {}

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
                executor.submit(fetch_repo_details, repo["owner"], repo["name"], persist_cache=False): repo
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

    def flush_discovery_content_caches() -> None:
        flush_translation_cache()
        flush_repo_details_cache()

    def ensure_discovery_not_cancelled(cancel_callback, *, flush_caches: bool = False) -> None:
        if not callable(cancel_callback):
            return
        if cancel_callback():
            if flush_caches:
                flush_discovery_content_caches()
            raise DiscoveryCancelledError("关键词发现已取消")

    def store_discovery_cache(cache_key: str, payload: dict[str, object], saved_at: int) -> None:
        with discovery_cache_lock:
            discovery_cache[cache_key] = {"saved_at": saved_at, "payload": clone_discovery_payload(payload)}
            expired = [
                key
                for key, item in discovery_cache.items()
                if not isinstance(item, dict) or saved_at - clamp_int(item.get("saved_at"), 0, 0) >= discovery_cache_seconds
            ]
            for key in expired:
                discovery_cache.pop(key, None)
            if len(discovery_cache) > discovery_cache_max_entries:
                oldest = sorted(
                    discovery_cache,
                    key=lambda key: clamp_int(
                        discovery_cache[key].get("saved_at") if isinstance(discovery_cache[key], dict) else 0,
                        0,
                        0,
                    ),
                )
                for key in oldest[: len(discovery_cache) - discovery_cache_max_entries]:
                    discovery_cache.pop(key, None)

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
        started_ts = time.perf_counter()
        query = normalize(query)
        language = normalize(language)
        ranking_profile = normalize_ranking_profile(ranking_profile)
        limit = clamp_int(limit, 20, 5, 100)
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
                logger.info(
                    "discovery_cache_hit limit=%d auto_expand=%s ranking_profile=%s",
                    limit,
                    bool(auto_expand),
                    ranking_profile,
                )
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
            per_page=min(max(limit * 3, 18), 100),
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
            store_discovery_cache(cache_key, payload, now)
            emit_discovery_progress(progress_callback, "completed", payload)
            logger.info(
                "discovery_completed results=%d warnings=%d cache_store=true duration_ms=%d",
                0,
                len(payload["warnings"]),
                int((time.perf_counter() - started_ts) * 1000),
            )
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
        ensure_discovery_not_cancelled(is_cancelled, flush_caches=True)

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
                    per_page=min(max(limit * 2, 12), 100),
                    warnings=warnings,
                )
            except Exception as exc:
                logger.warning("关键词发现扩词阶段降级为首轮结果: %s", exc)
                expansion_results = []
                warnings.append(f"扩词阶段已降级：{exc}")
            for repo in expansion_results:
                key = repo["full_name"].lower()
                candidate_map[key] = merge_discovery_candidate(candidate_map[key], repo) if key in candidate_map else repo
            ensure_discovery_not_cancelled(is_cancelled, flush_caches=True)

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
        ensure_discovery_not_cancelled(is_cancelled, flush_caches=True)
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
        flush_discovery_content_caches()
        payload = {
            "ranking_profile": ranking_profile,
            "translated_query": translated_query if translated_query.lower() != query.lower() else "",
            "related_terms": related_terms,
            "generated_queries": generated_queries,
            "warnings": list(dict.fromkeys(warnings))[:6],
            "run_at": iso_now(),
            "results": ranked[:limit],
        }
        store_discovery_cache(cache_key, payload, now)
        emit_discovery_progress(progress_callback, "completed", payload)
        logger.info(
            "discovery_completed results=%d warnings=%d cache_store=true duration_ms=%d",
            len(payload["results"]),
            len(payload["warnings"]),
            int((time.perf_counter() - started_ts) * 1000),
        )
        return payload

    return {
        "discover_repos": discover_repos,
        "normalize_ranking_profile": normalize_ranking_profile,
        "score_discovery_repo": score_discovery_repo,
        "rank_discovery_results": rank_discovery_results,
    }
