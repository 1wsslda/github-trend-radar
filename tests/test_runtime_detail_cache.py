from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gitsonar.runtime.detail_cache as detail_cache_module
from gitsonar.runtime.detail_cache import make_detail_cache_runtime
from gitsonar.runtime.utils import clamp_int


class RuntimeDetailCacheTests(unittest.TestCase):
    def build_runtime(
        self,
        *,
        initial_cache: dict[str, object] | None = None,
        loaded_cache: dict[str, object] | None = None,
        fetch_locks: dict[str, threading.Lock] | None = None,
        writes: list[tuple[str, dict[str, object]]] | None = None,
        max_detail_cache_size: int = 5,
        max_detail_fetch_locks: int = 5,
    ):
        cache_store = dict(initial_cache or {})
        fetch_lock_store = dict(fetch_locks or {})
        write_log = writes if writes is not None else []
        runtime = make_detail_cache_runtime(
            cache_path=str(ROOT / "artifacts" / "_detail_cache.json"),
            detail_cache=cache_store,
            detail_cache_lock=threading.RLock(),
            detail_fetch_locks=fetch_lock_store,
            load_json_file=lambda _path, default: dict(loaded_cache or default),
            atomic_write_json=lambda path, payload: write_log.append((str(path), dict(payload))),
            clamp_int=clamp_int,
            detail_cache_seconds=3600,
            max_detail_cache_size=max_detail_cache_size,
            max_detail_fetch_locks=max_detail_fetch_locks,
        )
        return runtime, cache_store, fetch_lock_store, write_log

    def test_save_and_flush_repo_details_updates_cache_and_dirty_state(self):
        runtime, cache_store, _fetch_locks, writes = self.build_runtime()

        with patch.object(detail_cache_module.time, "time", lambda: 2_000_000_000):
            runtime.save_repo_details("octo/demo", {"full_name": "octo/demo", "stars": 7})
            cached = runtime.cached_repo_details("octo/demo")
            flushed = runtime.flush_repo_details_cache()

        self.assertEqual(cached, {"full_name": "octo/demo", "stars": 7})
        self.assertTrue(flushed)
        self.assertFalse(runtime.is_dirty())
        self.assertIn("octo/demo", cache_store)
        self.assertEqual(writes[0][1]["octo/demo"]["data"]["stars"], 7)
        self.assertFalse(runtime.flush_repo_details_cache())

    def test_reload_detail_cache_replaces_memory_cache_and_clears_dirty_state(self):
        runtime, cache_store, _fetch_locks, _writes = self.build_runtime(
            initial_cache={"stale": {"expires_at": 1, "data": {"full_name": "octo/stale"}}},
            loaded_cache={"fresh": {"expires_at": 2_000_003_600, "data": {"full_name": "octo/fresh"}}},
        )
        runtime.set_dirty(True)

        runtime.reload_detail_cache()

        with patch.object(detail_cache_module.time, "time", lambda: 2_000_000_000):
            cached = runtime.cached_repo_details("fresh")

        self.assertEqual(cache_store, {"fresh": {"expires_at": 2_000_003_600, "data": {"full_name": "octo/fresh"}}})
        self.assertEqual(cached, {"full_name": "octo/fresh"})
        self.assertFalse(runtime.is_dirty())

    def test_detail_fetch_lock_prunes_stale_entries_before_adding_new_lock(self):
        stale_lock = threading.Lock()
        runtime, _cache_store, fetch_lock_store, _writes = self.build_runtime(
            fetch_locks={"stale": stale_lock},
            max_detail_fetch_locks=1,
        )

        fresh_lock = runtime.detail_fetch_lock("fresh")

        self.assertIs(fetch_lock_store["fresh"], fresh_lock)
        self.assertEqual(list(fetch_lock_store), ["fresh"])

    def test_separate_runtime_instances_share_dirty_state_via_callbacks(self):
        cache_store: dict[str, object] = {}
        dirty_state = {"dirty": False}
        writes: list[tuple[str, dict[str, object]]] = []
        common_kwargs = {
            "cache_path": str(ROOT / "artifacts" / "_detail_cache.json"),
            "detail_cache": cache_store,
            "detail_cache_lock": threading.RLock(),
            "detail_fetch_locks": {},
            "load_json_file": lambda _path, default: default,
            "atomic_write_json": lambda path, payload: writes.append((str(path), dict(payload))),
            "clamp_int": clamp_int,
            "detail_cache_seconds": 3600,
            "max_detail_cache_size": 5,
            "max_detail_fetch_locks": 5,
            "dirty_getter": lambda: dirty_state["dirty"],
            "dirty_setter": lambda value: dirty_state.__setitem__("dirty", value),
        }
        runtime_one = make_detail_cache_runtime(**common_kwargs)
        runtime_two = make_detail_cache_runtime(**common_kwargs)

        with patch.object(detail_cache_module.time, "time", lambda: 2_000_000_000):
            runtime_one.save_repo_details("octo/demo", {"full_name": "octo/demo"})
            flushed = runtime_two.flush_repo_details_cache()

        self.assertTrue(flushed)
        self.assertFalse(dirty_state["dirty"])
        self.assertEqual(writes[0][1]["octo/demo"]["data"]["full_name"], "octo/demo")


if __name__ == "__main__":
    unittest.main()
