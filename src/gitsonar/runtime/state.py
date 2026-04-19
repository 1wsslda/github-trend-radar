#!/usr/bin/env python3
from __future__ import annotations

from types import SimpleNamespace

from .state_schema import DISCOVERY_RANKING_PROFILES, discovery_warning_list, make_state_schema
from .state_store import make_state_store

__all__ = [
    "DISCOVERY_RANKING_PROFILES",
    "discovery_warning_list",
    "make_state_runtime",
]


def make_state_runtime(
    *,
    settings,
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
    clamp_int,
    as_bool,
    iso_now,
    load_json_file,
    atomic_write_json,
    apply_repo_translation,
):
    schema = make_state_schema(
        settings=settings,
        normalize=normalize,
        clamp_int=clamp_int,
        as_bool=as_bool,
        iso_now=iso_now,
    )
    store = make_state_store(
        user_state=user_state,
        discovery_state=discovery_state,
        state_lock=state_lock,
        discovery_lock=discovery_lock,
        current_snapshot_getter=current_snapshot_getter,
        sync_repo_records_callback=sync_repo_records_callback,
        user_state_path=user_state_path,
        discovery_state_path=discovery_state_path,
        latest_snapshot_path=latest_snapshot_path,
        periods=periods,
        normalize=normalize,
        iso_now=iso_now,
        load_json_file=load_json_file,
        atomic_write_json=atomic_write_json,
        apply_repo_translation=apply_repo_translation,
        default_user_state=schema.default_user_state,
        default_discovery_state=schema.default_discovery_state,
        normalize_discovery_query=schema.normalize_discovery_query,
        normalize_repo=schema.normalize_repo,
        normalize_watch_entry=schema.normalize_watch_entry,
        normalize_favorite_update=schema.normalize_favorite_update,
        normalize_discovery_state=schema.normalize_discovery_state,
        normalize_user_state=schema.normalize_user_state,
        state_counts=schema.state_counts,
        ordered_unique_urls=schema.ordered_unique_urls,
        merge_favorite_updates=schema.merge_favorite_updates,
        discovery_warning_list=discovery_warning_list,
    )
    return SimpleNamespace(
        **vars(schema),
        **vars(store),
        discovery_warning_list=lambda items, *, limit=8: discovery_warning_list(normalize, items, limit=limit),
    )
