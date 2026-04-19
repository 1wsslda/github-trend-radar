#!/usr/bin/env python3
from __future__ import annotations

"""Shared repo record normalization helpers."""


def normalize_text_list(normalize, items: object, *, limit: int | None = None) -> list[str]:
    if not isinstance(items, list):
        return []
    values = [normalize(item) for item in items if normalize(item)]
    if limit is not None:
        values = values[:limit]
    return list(dict.fromkeys(values))


def infer_repo_source_key(payload: dict[str, object], normalize) -> str:
    explicit = normalize(payload.get("source_key")).lower().replace("-", "_").replace(" ", "_")
    if explicit:
        return explicit
    period_key = normalize(payload.get("period_key")).lower()
    discover_source = normalize(payload.get("discover_source")).lower().replace("-", "_")
    growth_source = normalize(payload.get("growth_source")).lower()
    source_label = normalize(payload.get("source_label")).lower()
    if period_key == "discover" or discover_source:
        return discover_source or "discover"
    if "favorite" in source_label and "update" in source_label:
        return "favorite_update"
    if "local" in source_label or period_key == "saved":
        return "local_state"
    if "star" in source_label:
        return "github_starred"
    if "trending" in source_label and "api" in source_label:
        return "trending_api"
    if "trending" in source_label or growth_source == "trending":
        return "trending"
    return "github_api"


def build_repo_record(
    payload: object,
    *,
    normalize,
    clamp_int,
    as_bool,
    default_period_key: str = "daily",
    default_source_label: str = "GitHub API",
) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    full_name = normalize(payload.get("full_name"))
    url = normalize(payload.get("url"))
    if not full_name or not url or "/" not in full_name:
        return None
    owner, name = full_name.split("/", 1)
    gained = clamp_int(payload.get("gained"), 0, 0)
    gained_text = normalize(payload.get("gained_text"))
    growth_source = normalize(payload.get("growth_source")).lower()
    if growth_source not in {"trending", "estimated", "unavailable"}:
        growth_source = "trending" if gained_text or gained > 0 else "unavailable"
    description_raw = normalize(payload.get("description_raw") or payload.get("description"))
    topics = normalize_text_list(normalize, payload.get("topics"), limit=24)
    matched_terms = normalize_text_list(normalize, payload.get("matched_terms"), limit=10)
    match_reasons = normalize_text_list(normalize, payload.get("match_reasons"), limit=4)
    ranking_profile = normalize(payload.get("ranking_profile")).lower()
    if ranking_profile not in {"balanced", "hot", "fresh", "builder", "trend"}:
        ranking_profile = ""
    source_label = normalize(payload.get("source_label")) or default_source_label
    repo_record = {
        "full_name": full_name,
        "owner": owner,
        "name": name,
        "url": url,
        "description": normalize(payload.get("description")) or description_raw,
        "description_raw": description_raw,
        "language": normalize(payload.get("language")),
        "stars": clamp_int(payload.get("stars"), 0, 0),
        "forks": clamp_int(payload.get("forks"), 0, 0),
        "gained": gained,
        "gained_text": gained_text,
        "growth_source": growth_source,
        "rank": clamp_int(payload.get("rank"), 0, 0),
        "period_key": normalize(payload.get("period_key")) or default_period_key,
        "source_label": source_label,
        "source_key": infer_repo_source_key({**payload, "source_label": source_label}, normalize),
        "updated_at": normalize(payload.get("updated_at")),
        "pushed_at": normalize(payload.get("pushed_at")),
        "topics": topics,
        "discover_source": normalize(payload.get("discover_source")),
        "trending_hit": as_bool(payload.get("trending_hit"), False),
        "relevance_score": clamp_int(payload.get("relevance_score"), 0, 0, 100),
        "hot_score": clamp_int(payload.get("hot_score"), 0, 0, 100),
        "composite_score": clamp_int(payload.get("composite_score"), 0, 0, 100),
        "matched_terms": matched_terms,
        "match_reasons": match_reasons,
        "ranking_profile": ranking_profile,
        "ranking_signal_score": clamp_int(payload.get("ranking_signal_score"), 0, 0, 100),
    }
    return repo_record


__all__ = [
    "build_repo_record",
    "infer_repo_source_key",
    "normalize_text_list",
]
