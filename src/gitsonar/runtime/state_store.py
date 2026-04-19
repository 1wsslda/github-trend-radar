#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from types import SimpleNamespace


def make_state_store(
    *,
    user_state,
    discovery_state,
    state_lock,
    discovery_lock,
    current_snapshot_getter,
    sync_repo_records_callback,
    user_state_path,
    discovery_state_path,
    latest_snapshot_path,
    periods,
    normalize,
    iso_now,
    load_json_file,
    atomic_write_json,
    apply_repo_translation,
    default_user_state,
    default_discovery_state,
    normalize_discovery_query,
    normalize_repo,
    normalize_watch_entry,
    normalize_favorite_update,
    normalize_discovery_state,
    normalize_user_state,
    state_counts,
    ordered_unique_urls,
    merge_favorite_updates,
    discovery_warning_list,
):
    USER_STATE = user_state
    DISCOVERY_STATE = discovery_state
    STATE_LOCK = state_lock
    DISCOVERY_LOCK = discovery_lock
    current_snapshot = current_snapshot_getter
    sync_repo_records = sync_repo_records_callback
    USER_STATE_PATH = user_state_path
    DISCOVERY_STATE_PATH = discovery_state_path
    LATEST_SNAPSHOT_PATH = latest_snapshot_path
    PERIODS = periods

    def load_user_state() -> dict[str, object]:
        state = normalize_user_state(load_json_file(USER_STATE_PATH, default_user_state()))
        if not os.path.exists(USER_STATE_PATH):
            atomic_write_json(USER_STATE_PATH, state)
        return state

    def save_user_state() -> None:
        atomic_write_json(USER_STATE_PATH, USER_STATE)

    def mutate_repo_state(state_key: str, enabled: bool, repo: object) -> dict[str, object]:
        if state_key not in {"favorites", "watch_later", "read", "ignored"}:
            raise ValueError("invalid state")
        clean = normalize_repo(repo)
        if not clean:
            raise ValueError("missing repo")
        url = clean["url"]
        USER_STATE.setdefault("repo_records", {})[url] = clean
        USER_STATE[state_key] = [item for item in USER_STATE.get(state_key, []) if item != url]
        if enabled:
            USER_STATE[state_key].insert(0, url)
        elif state_key == "favorites":
            USER_STATE.get("favorite_watch", {}).pop(url, None)
        return clean

    def set_repo_state(state_key: str, enabled: bool, repo: object) -> dict[str, object]:
        with STATE_LOCK:
            clean = mutate_repo_state(state_key, enabled, repo)
            save_user_state()
            return clean

    def set_repo_state_batch(state_key: str, enabled: bool, repos: object) -> list[dict[str, object]]:
        if not isinstance(repos, list):
            raise ValueError("missing repos")
        processed: list[dict[str, object]] = []
        with STATE_LOCK:
            try:
                for repo in repos:
                    processed.append(mutate_repo_state(state_key, enabled, repo))
            except ValueError as exc:
                if processed:
                    save_user_state()
                error = ValueError(str(exc))
                setattr(error, "processed_repos", list(processed))
                setattr(error, "processed_count", len(processed))
                raise error from exc
            if processed:
                save_user_state()
            return processed

    def export_user_state() -> dict[str, object]:
        with STATE_LOCK:
            return json.loads(json.dumps(USER_STATE, ensure_ascii=False))

    def coerce_import_user_state(payload: object) -> dict[str, object]:
        if isinstance(payload, dict):
            if isinstance(payload.get("data"), dict):
                raw_state = payload.get("data")
            elif isinstance(payload.get("user_state"), dict):
                raw_state = payload.get("user_state")
            else:
                raw_state = payload
        else:
            raw_state = {}
        state = normalize_user_state(raw_state)
        if not any(state.get(key) for key in ("favorites", "watch_later", "read", "ignored")) and not state.get("repo_records"):
            raise ValueError("Import file does not contain any restorable user state.")
        return state

    def import_user_state(payload: object) -> dict[str, object]:
        mode = normalize(payload.get("mode") if isinstance(payload, dict) else "").lower()
        if mode not in {"merge", "replace"}:
            mode = "merge"
        imported = coerce_import_user_state(payload)
        with STATE_LOCK:
            before_counts = state_counts(USER_STATE)
            if mode == "replace":
                next_state = imported
            else:
                next_state = default_user_state()
                for key in ("favorites", "watch_later", "read", "ignored"):
                    next_state[key] = ordered_unique_urls(imported.get(key, []), USER_STATE.get(key, []))
                next_state["repo_records"] = dict(USER_STATE.get("repo_records", {}))
                next_state["repo_records"].update(imported.get("repo_records", {}))
                next_state["favorite_watch"] = dict(USER_STATE.get("favorite_watch", {}))
                next_state["favorite_watch"].update(imported.get("favorite_watch", {}))
                next_state["favorite_updates"] = merge_favorite_updates(
                    imported.get("favorite_updates", []),
                    USER_STATE.get("favorite_updates", []),
                )

            favorite_urls = set(next_state.get("favorites", []))
            next_state["favorite_watch"] = {
                url: item
                for url, item in next_state.get("favorite_watch", {}).items()
                if url in favorite_urls and normalize_watch_entry(item)
            }
            next_state["favorite_updates"] = [
                item
                for item in next_state.get("favorite_updates", [])
                if item.get("url") in favorite_urls
            ][:100]
            USER_STATE.clear()
            USER_STATE.update(normalize_user_state(next_state))
            save_user_state()
            after_counts = state_counts(USER_STATE)
        if callable(sync_repo_records):
            snapshot = current_snapshot() if callable(current_snapshot) else {}
            sync_repo_records(snapshot if isinstance(snapshot, dict) else {})
        return {
            "mode": mode,
            "before_counts": before_counts,
            "after_counts": after_counts,
            "user_state": export_user_state(),
        }

    def load_discovery_state() -> dict[str, object]:
        raw_state = load_json_file(DISCOVERY_STATE_PATH, default_discovery_state())
        state = normalize_discovery_state(raw_state)
        if not os.path.exists(DISCOVERY_STATE_PATH) or raw_state != state:
            atomic_write_json(DISCOVERY_STATE_PATH, state)
        return state

    def save_discovery_state() -> None:
        atomic_write_json(DISCOVERY_STATE_PATH, DISCOVERY_STATE)

    def export_discovery_state() -> dict[str, object]:
        with DISCOVERY_LOCK:
            return json.loads(json.dumps(DISCOVERY_STATE, ensure_ascii=False))

    def clear_discovery_results() -> dict[str, object]:
        with DISCOVERY_LOCK:
            DISCOVERY_STATE["last_query"] = {}
            DISCOVERY_STATE["last_results"] = []
            DISCOVERY_STATE["last_related_terms"] = []
            DISCOVERY_STATE["last_generated_queries"] = []
            DISCOVERY_STATE["last_translated_query"] = ""
            DISCOVERY_STATE["last_warnings"] = []
            DISCOVERY_STATE["last_run_at"] = ""
            DISCOVERY_STATE["last_error"] = ""
            save_discovery_state()
            return export_discovery_state()

    def remember_discovery_query(query_payload: dict[str, object], *, last_run_at: str = "") -> None:
        clean = normalize_discovery_query(query_payload)
        if not clean:
            return
        if last_run_at:
            clean["last_run_at"] = normalize(last_run_at)
        with DISCOVERY_LOCK:
            DISCOVERY_STATE["remembered_query"] = clean
            save_discovery_state()

    def apply_discovery_result(query_payload: dict[str, object], discovery: dict[str, object], *, save_query: bool) -> dict[str, object]:
        results = [clean for item in discovery.get("results", []) if (clean := normalize_repo(item))]
        last_run_at = normalize(discovery.get("run_at")) or iso_now()
        warnings = discovery_warning_list(normalize, discovery.get("warnings"), limit=8)
        with DISCOVERY_LOCK:
            DISCOVERY_STATE["last_query"] = query_payload
            DISCOVERY_STATE["last_results"] = results
            DISCOVERY_STATE["last_related_terms"] = [normalize(item) for item in discovery.get("related_terms", []) if normalize(item)][:12]
            DISCOVERY_STATE["last_generated_queries"] = [normalize(item) for item in discovery.get("generated_queries", []) if normalize(item)][:12]
            DISCOVERY_STATE["last_translated_query"] = normalize(discovery.get("translated_query"))
            DISCOVERY_STATE["last_warnings"] = warnings
            DISCOVERY_STATE["last_run_at"] = last_run_at
            DISCOVERY_STATE["last_error"] = ""
            if save_query:
                remembered_query = dict(query_payload)
                remembered_query["last_run_at"] = last_run_at
                DISCOVERY_STATE["remembered_query"] = remembered_query
            save_discovery_state()
            return export_discovery_state()

    def empty_snapshot() -> dict[str, object]:
        snapshot = {"fetched_at": iso_now()}
        for period in PERIODS:
            snapshot[period["key"]] = []
        return snapshot

    def load_snapshot() -> dict[str, object]:
        raw = load_json_file(LATEST_SNAPSHOT_PATH, empty_snapshot())
        if not isinstance(raw, dict):
            return empty_snapshot()
        snapshot = empty_snapshot()
        snapshot["fetched_at"] = normalize(raw.get("fetched_at")) or iso_now()
        for period in PERIODS:
            snapshot[period["key"]] = [clean for repo in raw.get(period["key"], []) if (clean := normalize_repo(repo))]
            for repo in snapshot[period["key"]]:
                apply_repo_translation(repo)
        return snapshot

    def save_snapshot(snapshot: dict[str, object]) -> None:
        atomic_write_json(LATEST_SNAPSHOT_PATH, snapshot)

    return SimpleNamespace(
        load_user_state=load_user_state,
        save_user_state=save_user_state,
        set_repo_state=set_repo_state,
        set_repo_state_batch=set_repo_state_batch,
        export_user_state=export_user_state,
        import_user_state=import_user_state,
        load_discovery_state=load_discovery_state,
        save_discovery_state=save_discovery_state,
        export_discovery_state=export_discovery_state,
        clear_discovery_results=clear_discovery_results,
        remember_discovery_query=remember_discovery_query,
        apply_discovery_result=apply_discovery_result,
        empty_snapshot=empty_snapshot,
        load_snapshot=load_snapshot,
        save_snapshot=save_snapshot,
    )


__all__ = ["make_state_store"]
