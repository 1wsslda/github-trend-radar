#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from types import SimpleNamespace
from urllib.parse import urlparse

from .ai_insight import normalize_ai_insight as normalize_ai_insight_payload
from .repo_records import build_repo_record

DISCOVERY_RANKING_PROFILES = {"balanced", "hot", "fresh", "builder", "trend"}


def discovery_warning_list(normalize, items: object, *, limit: int = 8) -> list[str]:
    if not isinstance(items, list):
        return []
    return list(dict.fromkeys(normalize(item) for item in items if normalize(item)))[:limit]


def make_state_schema(
    *,
    settings,
    normalize,
    clamp_int,
    as_bool,
    iso_now,
):
    SETTINGS = settings

    def default_user_state() -> dict[str, object]:
        return {
            "favorites": [],
            "watch_later": [],
            "read": [],
            "ignored": [],
            "repo_records": {},
            "repo_annotations": {},
            "favorite_watch": {},
            "favorite_updates": [],
            "feedback_signals": {},
            "ai_insights": {},
        }

    def default_discovery_state() -> dict[str, object]:
        return {
            "remembered_query": {},
            "last_query": {},
            "last_results": [],
            "last_clusters": [],
            "last_related_terms": [],
            "last_generated_queries": [],
            "last_translated_query": "",
            "last_warnings": [],
            "last_run_at": "",
            "last_error": "",
            "saved_views": [],
        }

    def normalize_discovery_ranking_profile(value: object) -> str:
        clean = normalize(value).lower()
        return clean if clean in DISCOVERY_RANKING_PROFILES else "balanced"

    def discovery_query_id(query: str, auto_expand: bool, ranking_profile: str = "balanced") -> str:
        payload = "\n".join(
            (
                normalize(query),
                str(int(bool(auto_expand))),
                normalize_discovery_ranking_profile(ranking_profile),
            )
        )
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def normalize_discovery_query(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        query = normalize(raw.get("query"))
        if not query:
            return None
        auto_expand = as_bool(raw.get("auto_expand"), True)
        ranking_profile = normalize_discovery_ranking_profile(raw.get("ranking_profile"))
        default_limit = clamp_int(SETTINGS.get("result_limit", 20), 20, 5, 100) if SETTINGS else 20
        return {
            "id": normalize(raw.get("id")) or discovery_query_id(query, auto_expand, ranking_profile),
            "query": query,
            "limit": clamp_int(raw.get("limit"), default_limit, 5, 100),
            "auto_expand": auto_expand,
            "ranking_profile": ranking_profile,
            "created_at": normalize(raw.get("created_at")) or iso_now(),
            "last_run_at": normalize(raw.get("last_run_at")),
        }

    def normalize_repo(repo: object) -> dict[str, object] | None:
        return build_repo_record(
            repo,
            normalize=normalize,
            clamp_int=clamp_int,
            as_bool=as_bool,
            default_period_key="daily",
            default_source_label="GitHub API",
        )

    def repo_from_url(url: object) -> dict[str, object] | None:
        raw = normalize(url)
        if not raw:
            return None
        parsed = urlparse(raw)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            return None
        full_name = f"{parts[0]}/{parts[1]}"
        return normalize_repo(
            {
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "source_key": "github_url",
            }
        )

    def normalize_watch_entry(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        full_name = normalize(raw.get("full_name"))
        url = normalize(raw.get("url"))
        if not full_name or not url:
            return None
        return {
            "full_name": full_name,
            "url": url,
            "stars": clamp_int(raw.get("stars"), 0, 0),
            "forks": clamp_int(raw.get("forks"), 0, 0),
            "open_issues": clamp_int(raw.get("open_issues"), 0, 0),
            "updated_at": normalize(raw.get("updated_at")),
            "pushed_at": normalize(raw.get("pushed_at")),
            "latest_release_tag": normalize(raw.get("latest_release_tag")),
            "latest_release_published_at": normalize(raw.get("latest_release_published_at")),
            "release_checked_at": normalize(raw.get("release_checked_at")),
            "checked_at": normalize(raw.get("checked_at")),
        }

    def normalize_repo_annotation(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        tags = [normalize(item) for item in raw.get("tags", []) if normalize(item)]
        note = normalize(raw.get("note"))
        if not tags and not note:
            return None
        return {
            "tags": list(dict.fromkeys(tags))[:12],
            "note": note,
            "updated_at": normalize(raw.get("updated_at")) or iso_now(),
        }

    def normalize_favorite_update(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        full_name = normalize(raw.get("full_name"))
        url = normalize(raw.get("url"))
        if not full_name or not url:
            return None
        changes = [normalize(item) for item in raw.get("changes", []) if normalize(item)]
        if not changes:
            return None
        return {
            "id": normalize(raw.get("id")) or f"{full_name}:{normalize(raw.get('checked_at'))}",
            "full_name": full_name,
            "url": url,
            "checked_at": normalize(raw.get("checked_at")),
            "changes": changes,
            "change_summary": normalize(raw.get("change_summary")),
            "importance_reason": normalize(raw.get("importance_reason")),
            "stars": clamp_int(raw.get("stars"), 0, 0),
            "forks": clamp_int(raw.get("forks"), 0, 0),
            "latest_release_tag": normalize(raw.get("latest_release_tag")),
            "pushed_at": normalize(raw.get("pushed_at")),
            "read_at": normalize(raw.get("read_at")),
            "dismissed_at": normalize(raw.get("dismissed_at")),
            "pinned": as_bool(raw.get("pinned"), False),
            "priority_score": clamp_int(raw.get("priority_score"), 0, 0, 100),
        }

    def normalize_feedback_signal(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        reason = normalize(raw.get("reason"))
        count = clamp_int(raw.get("count"), 0, 0, 9999)
        if not reason and count <= 0:
            return None
        return {
            "reason": reason,
            "count": count or 1,
            "updated_at": normalize(raw.get("updated_at")) or iso_now(),
            "state": normalize(raw.get("state")) or "ignored",
        }

    def normalize_saved_view(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        query_payload = normalize_discovery_query(raw)
        name = normalize(raw.get("name"))
        if not query_payload or not name:
            return None
        return {
            "id": normalize(raw.get("id")) or query_payload["id"],
            "name": name,
            "query": query_payload["query"],
            "limit": query_payload["limit"],
            "auto_expand": query_payload["auto_expand"],
            "ranking_profile": query_payload["ranking_profile"],
            "created_at": normalize(raw.get("created_at")) or query_payload.get("created_at") or iso_now(),
            "last_run_at": normalize(raw.get("last_run_at")) or query_payload.get("last_run_at"),
            "last_result_count": clamp_int(raw.get("last_result_count"), 0, 0, 999),
        }

    def normalize_discovery_cluster(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        cluster_id = normalize(raw.get("id"))
        label = normalize(raw.get("label"))
        if not cluster_id or not label:
            return None
        repo_urls = list(dict.fromkeys(normalize(item) for item in raw.get("repo_urls", []) if normalize(item)))[:100]
        return {
            "id": cluster_id,
            "label": label,
            "count": clamp_int(raw.get("count"), len(repo_urls), 0, 999),
            "repo_urls": repo_urls,
            "top_terms": [normalize(item) for item in raw.get("top_terms", []) if normalize(item)][:8],
            "languages": [normalize(item) for item in raw.get("languages", []) if normalize(item)][:8],
        }

    def normalize_discovery_state(payload: object) -> dict[str, object]:
        raw = payload if isinstance(payload, dict) else {}
        state = default_discovery_state()
        state["remembered_query"] = normalize_discovery_query(raw.get("remembered_query")) or {}
        state["last_query"] = normalize_discovery_query(raw.get("last_query")) or {}
        state["last_results"] = [clean for item in raw.get("last_results", []) if (clean := normalize_repo(item))]
        state["last_clusters"] = [
            clean for item in raw.get("last_clusters", []) if (clean := normalize_discovery_cluster(item))
        ][:20]
        state["last_related_terms"] = [normalize(item) for item in raw.get("last_related_terms", []) if normalize(item)][:12]
        state["last_generated_queries"] = [normalize(item) for item in raw.get("last_generated_queries", []) if normalize(item)][:12]
        state["last_translated_query"] = normalize(raw.get("last_translated_query"))
        state["last_warnings"] = discovery_warning_list(normalize, raw.get("last_warnings"), limit=8)
        state["last_run_at"] = normalize(raw.get("last_run_at"))
        state["last_error"] = normalize(raw.get("last_error"))
        saved_views: list[dict[str, object]] = []
        seen_view_ids: set[str] = set()
        for item in raw.get("saved_views", []):
            clean = normalize_saved_view(item)
            if clean and clean["id"] not in seen_view_ids:
                saved_views.append(clean)
                seen_view_ids.add(clean["id"])
        state["saved_views"] = saved_views[:20]
        return state

    def normalize_user_state(payload: object) -> dict[str, object]:
        raw = payload if isinstance(payload, dict) else {}
        state = default_user_state()
        for key in ("favorites", "watch_later", "read", "ignored"):
            state[key] = list(dict.fromkeys(normalize(item) for item in raw.get(key, []) if normalize(item)))
        records = raw.get("repo_records", {}) if isinstance(raw.get("repo_records"), dict) else {}
        state["repo_records"] = {
            url: clean
            for url, repo in records.items()
            if (clean := normalize_repo(repo))
        }
        annotations = raw.get("repo_annotations", {}) if isinstance(raw.get("repo_annotations"), dict) else {}
        state["repo_annotations"] = {
            url: clean
            for url, item in annotations.items()
            if normalize(url) and (clean := normalize_repo_annotation(item))
        }
        watch = raw.get("favorite_watch", {}) if isinstance(raw.get("favorite_watch"), dict) else {}
        state["favorite_watch"] = {
            url: clean
            for url, item in watch.items()
            if (clean := normalize_watch_entry(item))
        }
        favorite_updates: list[dict[str, object]] = []
        seen_update_ids: set[str] = set()
        for item in raw.get("favorite_updates", []):
            clean = normalize_favorite_update(item)
            if clean and clean["id"] not in seen_update_ids:
                favorite_updates.append(clean)
                seen_update_ids.add(clean["id"])
        state["favorite_updates"] = favorite_updates
        feedback_signals = raw.get("feedback_signals", {}) if isinstance(raw.get("feedback_signals"), dict) else {}
        state["feedback_signals"] = {
            url: clean
            for url, item in feedback_signals.items()
            if normalize(url) and (clean := normalize_feedback_signal(item))
        }
        ai_insights = raw.get("ai_insights", {}) if isinstance(raw.get("ai_insights"), dict) else {}
        state["ai_insights"] = {
            url: clean
            for url, item in ai_insights.items()
            if normalize(url) and (
                clean := normalize_ai_insight_payload(
                    item,
                    normalize=normalize,
                    clamp_int=clamp_int,
                    iso_now=iso_now,
                )
            )
        }
        return state

    def state_counts(state: dict[str, object]) -> dict[str, int]:
        return {
            "favorites": len(state.get("favorites", [])),
            "watch_later": len(state.get("watch_later", [])),
            "read": len(state.get("read", [])),
            "ignored": len(state.get("ignored", [])),
            "repo_records": len(state.get("repo_records", {})),
            "favorite_updates": len(state.get("favorite_updates", [])),
        }

    def ordered_unique_urls(*groups: list[str]) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []
        for group in groups:
            for item in group:
                clean = normalize(item)
                if clean and clean not in seen:
                    merged.append(clean)
                    seen.add(clean)
        return merged

    def merge_favorite_updates(*groups: list[dict[str, object]]) -> list[dict[str, object]]:
        merged: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for group in groups:
            for item in group:
                clean = normalize_favorite_update(item)
                if clean and clean["id"] not in seen_ids:
                    merged.append(clean)
                    seen_ids.add(clean["id"])
        return merged[:100]

    return SimpleNamespace(
        default_user_state=default_user_state,
        default_discovery_state=default_discovery_state,
        normalize_discovery_ranking_profile=normalize_discovery_ranking_profile,
        discovery_query_id=discovery_query_id,
        normalize_discovery_query=normalize_discovery_query,
        normalize_repo=normalize_repo,
        repo_from_url=repo_from_url,
        normalize_watch_entry=normalize_watch_entry,
        normalize_repo_annotation=normalize_repo_annotation,
        normalize_favorite_update=normalize_favorite_update,
        normalize_feedback_signal=normalize_feedback_signal,
        normalize_discovery_cluster=normalize_discovery_cluster,
        normalize_ai_insight=lambda payload: normalize_ai_insight_payload(
            payload,
            normalize=normalize,
            clamp_int=clamp_int,
            iso_now=iso_now,
        ),
        normalize_saved_view=normalize_saved_view,
        normalize_discovery_state=normalize_discovery_state,
        normalize_user_state=normalize_user_state,
        state_counts=state_counts,
        ordered_unique_urls=ordered_unique_urls,
        merge_favorite_updates=merge_favorite_updates,
    )


__all__ = [
    "DISCOVERY_RANKING_PROFILES",
    "discovery_warning_list",
    "make_state_schema",
]
