#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json

AI_INSIGHT_SCHEMA_VERSION = "gitsonar.repo_insight.v1"


def normalize_text_list(normalize, items: object, *, limit: int = 8) -> list[str]:
    if not isinstance(items, list):
        return []
    values = [normalize(item) for item in items if normalize(item)]
    return list(dict.fromkeys(values))[:limit]


def normalize_ai_insight(
    payload: object,
    *,
    normalize,
    clamp_int,
    iso_now,
) -> dict[str, object] | None:
    raw = payload if isinstance(payload, dict) else {}
    summary = normalize(raw.get("summary"))
    best_for = normalize_text_list(normalize, raw.get("best_for"), limit=8)
    not_good_for = normalize_text_list(normalize, raw.get("not_good_for"), limit=8)
    learning_value = normalize_text_list(normalize, raw.get("learning_value"), limit=8)
    risk_signals = normalize_text_list(normalize, raw.get("risk_signals"), limit=8)
    next_actions = normalize_text_list(normalize, raw.get("next_actions"), limit=8)
    if not any((summary, best_for, not_good_for, learning_value, risk_signals, next_actions)):
        return None
    created_at = normalize(raw.get("created_at")) or iso_now()
    updated_at = normalize(raw.get("updated_at")) or created_at
    artifact_type = normalize(raw.get("artifact_type")) or "repo_insight"
    hash_payload = {
        "schema_version": AI_INSIGHT_SCHEMA_VERSION,
        "artifact_type": artifact_type,
        "provider": normalize(raw.get("provider")) or "manual",
        "model": normalize(raw.get("model")),
        "summary": summary,
        "best_for": best_for,
        "not_good_for": not_good_for,
        "learning_value": learning_value,
        "risk_signals": risk_signals,
        "next_actions": next_actions,
    }
    input_hash = normalize(raw.get("input_hash")) or hashlib.sha1(
        json.dumps(hash_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    artifact_id = normalize(raw.get("artifact_id") or raw.get("id")) or f"{artifact_type}_{input_hash[:12]}"
    return {
        "schema_version": AI_INSIGHT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "status": normalize(raw.get("status")) or "saved",
        "provider": normalize(raw.get("provider")) or "manual",
        "model": normalize(raw.get("model")),
        "input_hash": input_hash,
        "source_snapshot_id": normalize(raw.get("source_snapshot_id")),
        "summary": summary,
        "best_for": best_for,
        "not_good_for": not_good_for,
        "learning_value": learning_value,
        "risk_signals": risk_signals,
        "next_actions": next_actions,
        "confidence": clamp_int(raw.get("confidence"), 0, 0, 100),
        "created_at": created_at,
        "updated_at": updated_at,
    }


def build_repo_context(
    repo: object,
    detail: object,
    annotation: object,
    *,
    normalize,
    clamp_int,
) -> dict[str, object]:
    repo_payload = repo if isinstance(repo, dict) else {}
    detail_payload = detail if isinstance(detail, dict) else {}
    annotation_payload = annotation if isinstance(annotation, dict) else {}
    topics = []
    for item in detail_payload.get("topics", []) or repo_payload.get("topics", []) or []:
        clean = normalize(item)
        if clean:
            topics.append(clean)
    tags = normalize_text_list(normalize, annotation_payload.get("tags"), limit=12)
    return {
        "schema_version": AI_INSIGHT_SCHEMA_VERSION,
        "repo": normalize(detail_payload.get("full_name") or repo_payload.get("full_name")),
        "url": normalize(detail_payload.get("html_url") or repo_payload.get("url")),
        "description": normalize(
            detail_payload.get("description")
            or detail_payload.get("description_raw")
            or repo_payload.get("description")
            or repo_payload.get("description_raw")
        ),
        "language": normalize(detail_payload.get("language") or repo_payload.get("language")),
        "topics": list(dict.fromkeys(topics))[:24],
        "stars": clamp_int(detail_payload.get("stars"), clamp_int(repo_payload.get("stars"), 0, 0), 0),
        "forks": clamp_int(detail_payload.get("forks"), clamp_int(repo_payload.get("forks"), 0, 0), 0),
        "watchers": clamp_int(detail_payload.get("watchers"), 0, 0),
        "open_issues": clamp_int(detail_payload.get("open_issues"), 0, 0),
        "updated_at": normalize(detail_payload.get("updated_at") or repo_payload.get("updated_at")),
        "pushed_at": normalize(detail_payload.get("pushed_at") or repo_payload.get("pushed_at")),
        "latest_release_tag": normalize(detail_payload.get("latest_release_tag")),
        "readme_summary": normalize(detail_payload.get("readme_summary") or detail_payload.get("readme_summary_raw")),
        "user_tags": tags,
        "user_note": normalize(annotation_payload.get("note")),
    }


__all__ = [
    "AI_INSIGHT_SCHEMA_VERSION",
    "build_repo_context",
    "normalize_ai_insight",
    "normalize_text_list",
]
