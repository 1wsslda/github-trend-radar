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
    cache_state = {"dirty": False}

    def load_translation_cache() -> dict[str, str]:
        raw = load_json_file(CACHE_PATH, {})
        if not isinstance(raw, dict):
            return {}
        return {normalize(key): normalize(value) for key, value in raw.items() if normalize(key) and normalize(value)}

    def flush_translation_cache() -> bool:
        with TRANSLATION_LOCK:
            if not cache_state["dirty"]:
                return False
            if len(TRANSLATION_CACHE) > _MAX_TRANSLATION_CACHE_SIZE:
                trimmed = dict(list(TRANSLATION_CACHE.items())[-_MAX_TRANSLATION_CACHE_SIZE:])
                TRANSLATION_CACHE.clear()
                TRANSLATION_CACHE.update(trimmed)
            atomic_write_json(CACHE_PATH, TRANSLATION_CACHE)
            cache_state["dirty"] = False
            return True

    def save_translation_cache() -> bool:
        return flush_translation_cache()

    def has_han(text: str) -> bool:
        return bool(HAN_RE.search(text or ''))

    def request_translation(text: str, *, target_lang: str, cache_key: str, skip_translation) -> str:
        raw = normalize(text)
        if not raw or skip_translation(raw):
            return raw
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
                        'tl': target_lang,
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
            if TRANSLATION_CACHE.get(cache_key) != translated:
                TRANSLATION_CACHE[cache_key] = translated
                cache_state["dirty"] = True
        return translated

    def translate_text(text: str) -> str:
        raw = normalize(text)
        return request_translation(
            raw,
            target_lang='zh-CN',
            cache_key=raw,
            skip_translation=has_han,
        )

    def translate_query_to_en(text: str) -> str:
        raw = normalize(text)
        if not raw:
            return raw
        return request_translation(
            raw,
            target_lang='en',
            cache_key=f'en::{raw}',
            skip_translation=lambda value: not has_han(value),
        )

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
        flush_translation_cache()
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
        flush_translation_cache=flush_translation_cache,
        has_han=has_han,
        request_translation=request_translation,
        translate_text=translate_text,
        translate_query_to_en=translate_query_to_en,
        apply_repo_translation=apply_repo_translation,
        translate_repo_list=translate_repo_list,
        translate_snapshot=translate_snapshot,
    )
