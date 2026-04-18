#!/usr/bin/env python3
from __future__ import annotations

import time
from types import SimpleNamespace


def make_translation_runtime(
    *,
    cache_path,
    translation_cache,
    translation_lock,
    translate_session,
    normalize,
    load_json_file,
    atomic_write_json,
    translate_timeout,
    translate_retries,
    max_translation_cache_size,
    han_re,
    thread_pool_executor_cls,
    as_completed,
    periods,
):
    CACHE_PATH = cache_path
    TRANSLATION_CACHE = translation_cache
    TRANSLATION_LOCK = translation_lock
    TRANSLATE_SESSION = translate_session
    TRANSLATE_TIMEOUT = translate_timeout
    TRANSLATE_RETRIES = translate_retries
    _MAX_TRANSLATION_CACHE_SIZE = max_translation_cache_size
    HAN_RE = han_re
    ThreadPoolExecutor = thread_pool_executor_cls
    PERIODS = periods
    def load_translation_cache() -> dict[str, str]:
        raw = load_json_file(CACHE_PATH, {})
        if not isinstance(raw, dict):
            return {}
        return {normalize(key): normalize(value) for key, value in raw.items() if normalize(key) and normalize(value)}

    def save_translation_cache() -> None:
        with TRANSLATION_LOCK:
            if len(TRANSLATION_CACHE) > _MAX_TRANSLATION_CACHE_SIZE:
                trimmed = dict(list(TRANSLATION_CACHE.items())[-_MAX_TRANSLATION_CACHE_SIZE:])
                TRANSLATION_CACHE.clear()
                TRANSLATION_CACHE.update(trimmed)
            atomic_write_json(CACHE_PATH, TRANSLATION_CACHE)

    def has_han(text: str) -> bool:
        return bool(HAN_RE.search(text or ''))

    def translate_text(text: str) -> str:
        raw = normalize(text)
        if not raw or has_han(raw):
            return raw
        with TRANSLATION_LOCK:
            cached = TRANSLATION_CACHE.get(raw)
        if cached:
            return cached
        translated = ''
        for attempt in range(TRANSLATE_RETRIES):
            try:
                response = TRANSLATE_SESSION.get(
                    'https://translate.googleapis.com/translate_a/single',
                    params={
                        'client': 'gtx',
                        'sl': 'auto',
                        'tl': 'zh-CN',
                        'dt': 't',
                        'q': raw,
                    },
                    timeout=TRANSLATE_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                translated = normalize(''.join(part[0] for part in data[0] if isinstance(part, list) and part and part[0]))
                if translated:
                    break
            except Exception:
                translated = ''
                if attempt + 1 < TRANSLATE_RETRIES:
                    time.sleep(0.25 * (attempt + 1))
        if not translated:
            return raw
        with TRANSLATION_LOCK:
            TRANSLATION_CACHE[raw] = translated
        return translated

    def translate_query_to_en(text: str) -> str:
        raw = normalize(text)
        if not raw:
            return raw
        if not has_han(raw):
            return raw
        cache_key = f'en::{raw}'
        with TRANSLATION_LOCK:
            cached = TRANSLATION_CACHE.get(cache_key)
        if cached:
            return cached
        translated = ''
        for attempt in range(TRANSLATE_RETRIES):
            try:
                response = TRANSLATE_SESSION.get(
                    'https://translate.googleapis.com/translate_a/single',
                    params={
                        'client': 'gtx',
                        'sl': 'auto',
                        'tl': 'en',
                        'dt': 't',
                        'q': raw,
                    },
                    timeout=TRANSLATE_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                translated = normalize(''.join(part[0] for part in data[0] if isinstance(part, list) and part and part[0]))
                if translated:
                    break
            except Exception:
                translated = ''
                if attempt + 1 < TRANSLATE_RETRIES:
                    time.sleep(0.25 * (attempt + 1))
        if not translated:
            return raw
        with TRANSLATION_LOCK:
            TRANSLATION_CACHE[cache_key] = translated
        return translated

    def apply_repo_translation(repo: dict[str, object]) -> None:
        raw = normalize(repo.get('description_raw') or repo.get('description'))
        repo['description_raw'] = raw
        if not raw:
            repo['description'] = ''
            return
        with TRANSLATION_LOCK:
            cached = TRANSLATION_CACHE.get(raw)
        repo['description'] = cached or raw

    def translate_repo_list(repos: list[dict[str, object]]) -> None:
        pending: list[str] = []
        seen: set[str] = set()
        for repo in repos:
            apply_repo_translation(repo)
            raw = normalize(repo.get('description_raw'))
            lowered = raw.lower()
            if raw and not has_han(raw) and repo.get('description') == raw and lowered not in seen:
                seen.add(lowered)
                pending.append(raw)
        if not pending:
            return
        with ThreadPoolExecutor(max_workers=min(4, len(pending))) as executor:
            futures = [executor.submit(translate_text, text) for text in pending]
            for future in as_completed(futures):
                future.result()
        save_translation_cache()
        for repo in repos:
            apply_repo_translation(repo)

    def translate_snapshot(snapshot: dict[str, object]) -> None:
        repos: list[dict[str, object]] = []
        for period in PERIODS:
            repos.extend(snapshot.get(period['key'], []))
        translate_repo_list(repos)
    return SimpleNamespace(
        load_translation_cache=load_translation_cache,
        save_translation_cache=save_translation_cache,
        has_han=has_han,
        translate_text=translate_text,
        translate_query_to_en=translate_query_to_en,
        apply_repo_translation=apply_repo_translation,
        translate_repo_list=translate_repo_list,
        translate_snapshot=translate_snapshot,
    )
