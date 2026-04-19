#!/usr/bin/env python3
from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Callable


def make_detail_cache_runtime(
    *,
    cache_path,
    detail_cache,
    detail_cache_lock,
    detail_fetch_locks,
    load_json_file,
    atomic_write_json,
    clamp_int,
    detail_cache_seconds,
    max_detail_cache_size,
    max_detail_fetch_locks,
    dirty: bool = False,
    dirty_getter: Callable[[], bool] | None = None,
    dirty_setter: Callable[[bool], None] | None = None,
):
    DETAIL_CACHE = detail_cache
    DETAIL_CACHE_LOCK = detail_cache_lock
    DETAIL_FETCH_LOCKS = detail_fetch_locks
    cache_state = {"dirty": bool(dirty)}

    def is_dirty() -> bool:
        if dirty_getter is not None:
            return bool(dirty_getter())
        return bool(cache_state["dirty"])

    def set_dirty(value: bool) -> None:
        if dirty_setter is not None:
            dirty_setter(bool(value))
            return
        cache_state["dirty"] = bool(value)

    def load_detail_cache() -> dict[str, object]:
        raw = load_json_file(cache_path, {})
        return raw if isinstance(raw, dict) else {}

    def reload_detail_cache() -> None:
        loaded = load_detail_cache()
        with DETAIL_CACHE_LOCK:
            DETAIL_CACHE.clear()
            DETAIL_CACHE.update(loaded)
            set_dirty(False)

    def cached_repo_details(cache_key: str) -> dict[str, object] | None:
        now = int(time.time())
        with DETAIL_CACHE_LOCK:
            cached = DETAIL_CACHE.get(cache_key, {})
            if (
                isinstance(cached, dict)
                and clamp_int(cached.get("expires_at"), 0, 0) > now
                and isinstance(cached.get("data"), dict)
            ):
                return dict(cached["data"])
        return None

    def detail_fetch_lock(cache_key: str) -> threading.Lock:
        with DETAIL_CACHE_LOCK:
            lock = DETAIL_FETCH_LOCKS.get(cache_key)
            if lock is None:
                if len(DETAIL_FETCH_LOCKS) >= max_detail_fetch_locks:
                    stale = [key for key in DETAIL_FETCH_LOCKS if key not in DETAIL_CACHE]
                    for key in stale[:500]:
                        del DETAIL_FETCH_LOCKS[key]
                    if len(DETAIL_FETCH_LOCKS) >= max_detail_fetch_locks:
                        for key in list(DETAIL_FETCH_LOCKS)[:500]:
                            del DETAIL_FETCH_LOCKS[key]
                lock = threading.Lock()
                DETAIL_FETCH_LOCKS[cache_key] = lock
            return lock

    def save_repo_details(cache_key: str, details: dict[str, object]) -> None:
        now = int(time.time())
        with DETAIL_CACHE_LOCK:
            changed = False
            next_entry = {
                "expires_at": now + detail_cache_seconds,
                "data": dict(details),
            }
            if DETAIL_CACHE.get(cache_key) != next_entry:
                DETAIL_CACHE[cache_key] = next_entry
                changed = True
            expired = [
                key
                for key, value in DETAIL_CACHE.items()
                if isinstance(value, dict) and clamp_int(value.get("expires_at"), 0, 0) <= now
            ]
            for key in expired:
                del DETAIL_CACHE[key]
                changed = True
            if len(DETAIL_CACHE) > max_detail_cache_size:
                oldest = sorted(
                    DETAIL_CACHE,
                    key=lambda key: clamp_int(
                        DETAIL_CACHE[key].get("expires_at") if isinstance(DETAIL_CACHE[key], dict) else 0,
                        0,
                        0,
                    ),
                )
                for key in oldest[: len(DETAIL_CACHE) - max_detail_cache_size]:
                    del DETAIL_CACHE[key]
                    changed = True
            if changed:
                set_dirty(True)

    def flush_repo_details_cache() -> bool:
        with DETAIL_CACHE_LOCK:
            if not is_dirty():
                return False
            atomic_write_json(cache_path, DETAIL_CACHE)
            set_dirty(False)
            return True

    return SimpleNamespace(
        cache_path=cache_path,
        detail_cache=DETAIL_CACHE,
        detail_cache_lock=DETAIL_CACHE_LOCK,
        detail_fetch_locks=DETAIL_FETCH_LOCKS,
        load_detail_cache=load_detail_cache,
        reload_detail_cache=reload_detail_cache,
        cached_repo_details=cached_repo_details,
        detail_fetch_lock=detail_fetch_lock,
        save_repo_details=save_repo_details,
        flush_repo_details_cache=flush_repo_details_cache,
        is_dirty=is_dirty,
        set_dirty=set_dirty,
    )


__all__ = ["make_detail_cache_runtime"]
