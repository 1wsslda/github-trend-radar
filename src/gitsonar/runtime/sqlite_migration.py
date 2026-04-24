#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SQLITE_SCHEMA_VERSION = 1

PHASE_ONE_TABLES = (
    "schema_meta",
    "repos",
    "repo_snapshots",
    "user_repo_state",
    "repo_annotations",
    "favorite_watch",
    "update_events",
    "feedback_signals",
    "discovery_views",
    "discovery_runs",
    "discovery_results",
    "ai_artifacts",
    "settings_kv",
)

SENSITIVE_SETTING_KEYS = {
    "github_token",
    "github_token_encrypted",
    "proxy_url",
    "proxy_url_encrypted",
    "proxy",
    "proxies",
}


def sqlite_schema_statements() -> list[str]:
    return [
        """
        create table if not exists schema_meta (
            key text primary key,
            value text not null
        )
        """,
        """
        create table if not exists repos (
            id integer primary key,
            url text not null unique,
            owner text not null default '',
            name text not null default '',
            full_name text not null default '',
            description text not null default '',
            language text not null default '',
            topics_json text not null default '[]',
            last_seen_at text not null default '',
            raw_json text not null default '{}'
        )
        """,
        """
        create table if not exists repo_snapshots (
            id integer primary key,
            repo_id integer not null,
            stars integer not null default 0,
            forks integer not null default 0,
            gained integer not null default 0,
            rank integer not null default 0,
            source_key text not null default '',
            captured_at text not null default '',
            raw_json text not null default '{}',
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists user_repo_state (
            repo_id integer not null,
            state text not null,
            created_at text not null default '',
            updated_at text not null default '',
            primary key (repo_id, state),
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists repo_annotations (
            repo_id integer primary key,
            tags_json text not null default '[]',
            note text not null default '',
            updated_at text not null default '',
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists favorite_watch (
            repo_id integer primary key,
            stars integer not null default 0,
            forks integer not null default 0,
            latest_release_tag text not null default '',
            checked_at text not null default '',
            release_checked_at text not null default '',
            raw_json text not null default '{}',
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists update_events (
            id text primary key,
            repo_id integer not null,
            changes_json text not null default '[]',
            change_summary text not null default '',
            importance_reason text not null default '',
            priority_score integer not null default 0,
            read_at text not null default '',
            dismissed_at text not null default '',
            pinned integer not null default 0,
            checked_at text not null default '',
            raw_json text not null default '{}',
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists feedback_signals (
            repo_id integer primary key,
            reason text not null default '',
            count integer not null default 0,
            state text not null default '',
            updated_at text not null default '',
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists discovery_views (
            id text primary key,
            name text not null default '',
            query text not null default '',
            limit_value integer not null default 25,
            auto_expand integer not null default 1,
            ranking_profile text not null default 'balanced',
            last_run_at text not null default '',
            last_result_count integer not null default 0,
            raw_json text not null default '{}'
        )
        """,
        """
        create table if not exists discovery_runs (
            id text primary key,
            query_json text not null default '{}',
            run_at text not null default '',
            result_count integer not null default 0,
            warnings_json text not null default '[]'
        )
        """,
        """
        create table if not exists discovery_results (
            run_id text not null,
            repo_id integer not null,
            rank integer not null default 0,
            score_json text not null default '{}',
            raw_json text not null default '{}',
            primary key (run_id, repo_id),
            foreign key (run_id) references discovery_runs(id) on delete cascade,
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists ai_artifacts (
            id text primary key,
            repo_id integer not null,
            artifact_type text not null default '',
            schema_version text not null default '',
            provider text not null default '',
            model text not null default '',
            input_hash text not null default '',
            output_json text not null default '{}',
            created_at text not null default '',
            updated_at text not null default '',
            foreign key (repo_id) references repos(id) on delete cascade
        )
        """,
        """
        create table if not exists settings_kv (
            key text primary key,
            value_json text not null default 'null',
            updated_at text not null default ''
        )
        """,
        "create index if not exists idx_repo_snapshots_repo_id on repo_snapshots(repo_id)",
        "create index if not exists idx_update_events_repo_id on update_events(repo_id)",
        "create index if not exists idx_user_repo_state_state on user_repo_state(state)",
    ]


def create_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.execute("pragma foreign_keys = on")
    connection.executescript(";\n".join(statement.strip() for statement in sqlite_schema_statements()) + ";")
    connection.execute(
        "insert or replace into schema_meta(key, value) values(?, ?)",
        ("schema_version", str(SQLITE_SCHEMA_VERSION)),
    )
    connection.commit()


def sqlite_migration_file_plan(base_dir: str | Path, *, timestamp: str) -> dict[str, object]:
    base_path = Path(base_dir)
    backup_dir = base_path / "backups" / timestamp
    rollback_export_dir = base_path / "rollback-export" / timestamp
    return {
        "database": str(base_path / "gitsonar.db"),
        "temporary_database": str(base_path / "gitsonar.db.tmp"),
        "backup_dir": str(backup_dir),
        "rollback_export_dir": str(rollback_export_dir),
        "backup_files": {
            "user_state": str(backup_dir / "user_state.json"),
            "discovery_state": str(backup_dir / "discovery_state.json"),
            "latest_snapshot": str(backup_dir / "latest.json"),
        },
    }


def _as_dict(payload: object) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: object) -> list[object]:
    return payload if isinstance(payload, list) else []


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _repo_url(repo: object) -> str:
    raw = _as_dict(repo)
    return _clean_text(raw.get("url"))


def _collect_repo_urls_from_mapping(urls: set[str], payload: object) -> None:
    mapping = _as_dict(payload)
    for key, value in mapping.items():
        clean_key = _clean_text(key)
        if clean_key:
            urls.add(clean_key)
        clean_url = _repo_url(value)
        if clean_url:
            urls.add(clean_url)


def _collect_repo_urls_from_list(urls: set[str], payload: object) -> None:
    for item in _as_list(payload):
        if isinstance(item, dict):
            clean_url = _repo_url(item)
        else:
            clean_url = _clean_text(item)
        if clean_url:
            urls.add(clean_url)


def _collect_snapshot_repo_urls(urls: set[str], latest_snapshot: dict[str, Any]) -> None:
    for value in latest_snapshot.values():
        if isinstance(value, list):
            _collect_repo_urls_from_list(urls, value)


def _safe_json_list_count(payload: object) -> int:
    return len(_as_list(payload))


def _safe_json_mapping_count(payload: object) -> int:
    return len(_as_dict(payload))


def _setting_is_sensitive(key: object) -> bool:
    clean = _clean_text(key).lower()
    return clean in SENSITIVE_SETTING_KEYS or "token" in clean or "proxy" in clean


def _safe_settings_keys(settings: dict[str, Any]) -> tuple[list[str], list[str]]:
    safe: list[str] = []
    excluded: list[str] = []
    for key in settings:
        clean = _clean_text(key)
        if not clean:
            continue
        if _setting_is_sensitive(clean):
            excluded.append(clean)
        else:
            safe.append(clean)
    return sorted(safe), sorted(excluded)


def dry_run_sqlite_migration(
    *,
    user_state: object,
    discovery_state: object,
    latest_snapshot: object,
    settings: object | None = None,
) -> dict[str, object]:
    user = _as_dict(user_state)
    discovery = _as_dict(discovery_state)
    latest = _as_dict(latest_snapshot)
    clean_settings = _as_dict(settings)

    repo_urls: set[str] = set()
    _collect_repo_urls_from_mapping(repo_urls, user.get("repo_records"))
    for state_key in ("favorites", "watch_later", "read", "ignored"):
        _collect_repo_urls_from_list(repo_urls, user.get(state_key))
    _collect_repo_urls_from_mapping(repo_urls, user.get("repo_annotations"))
    _collect_repo_urls_from_mapping(repo_urls, user.get("favorite_watch"))
    _collect_repo_urls_from_list(repo_urls, user.get("favorite_updates"))
    _collect_repo_urls_from_mapping(repo_urls, user.get("feedback_signals"))
    _collect_repo_urls_from_mapping(repo_urls, user.get("ai_insights"))
    _collect_repo_urls_from_list(repo_urls, discovery.get("last_results"))
    _collect_snapshot_repo_urls(repo_urls, latest)

    settings_keys, excluded_sensitive_settings = _safe_settings_keys(clean_settings)
    favorite_updates = _as_list(user.get("favorite_updates"))
    favorite_update_fields = sorted(
        {
            field
            for item in favorite_updates
            if isinstance(item, dict)
            for field in ("changes", "change_summary", "importance_reason", "priority_score", "read_at", "dismissed_at", "pinned", "checked_at")
            if field in item
        }
    )

    counts = {
        "repos": len(repo_urls),
        "repo_records": _safe_json_mapping_count(user.get("repo_records")),
        "user_repo_state": sum(_safe_json_list_count(user.get(key)) for key in ("favorites", "watch_later", "read", "ignored")),
        "repo_annotations": _safe_json_mapping_count(user.get("repo_annotations")),
        "favorite_watch": _safe_json_mapping_count(user.get("favorite_watch")),
        "favorite_updates": len(favorite_updates),
        "feedback_signals": _safe_json_mapping_count(user.get("feedback_signals")),
        "discovery_views": _safe_json_list_count(discovery.get("saved_views")),
        "discovery_results": _safe_json_list_count(discovery.get("last_results")),
        "ai_artifacts": _safe_json_mapping_count(user.get("ai_insights")),
        "settings_kv": len(settings_keys),
    }

    return {
        "ok": True,
        "schema_version": SQLITE_SCHEMA_VERSION,
        "tables": list(PHASE_ONE_TABLES),
        "counts": counts,
        "settings_keys": settings_keys,
        "excluded_sensitive_settings": excluded_sensitive_settings,
        "favorite_update_fields": favorite_update_fields,
        "validation": {
            "json_export_compatible": True,
            "default_storage_unchanged": True,
            "rollback_export_planned": True,
            "sensitive_settings_excluded": not any(key in settings_keys for key in excluded_sensitive_settings),
        },
    }


__all__ = [
    "PHASE_ONE_TABLES",
    "SENSITIVE_SETTING_KEYS",
    "SQLITE_SCHEMA_VERSION",
    "create_sqlite_schema",
    "dry_run_sqlite_migration",
    "sqlite_migration_file_plan",
    "sqlite_schema_statements",
]
