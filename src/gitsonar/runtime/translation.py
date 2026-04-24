#!/usr/bin/env python3
from __future__ import annotations

import time
from types import SimpleNamespace
from urllib.parse import urlparse


DEFAULT_LOCAL_TRANSLATION_URL = "http://127.0.0.1:11434/api/generate"


def make_translation_runtime(
    *,
    cache_path,
    translation_cache,
    translation_lock,
    translate_session,
    settings,
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
    SETTINGS = settings
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

    def translation_provider() -> str:
        key = normalize(SETTINGS.get("translation_provider", "google")).lower().replace("-", "_")
        if key in {"local", "ollama", "local_ollama"}:
            return "local_ollama"
        return "google"

    def local_translation_model() -> str:
        return normalize(SETTINGS.get("translation_local_model", ""))

    def local_translation_url() -> str:
        return (normalize(SETTINGS.get("translation_local_url", "")) or DEFAULT_LOCAL_TRANSLATION_URL).rstrip("/")

    def is_loopback_url(url: str) -> bool:
        parsed = urlparse(normalize(url))
        host = (parsed.hostname or "").lower()
        return parsed.scheme in {"http", "https"} and host in {"127.0.0.1", "localhost", "::1"}

    def translation_cache_key(raw: str, target_lang: str) -> str:
        if translation_provider() == "local_ollama":
            return f"local_ollama::{local_translation_model()}::{target_lang}::{raw}"
        if target_lang == "en":
            return f"en::{raw}"
        return raw

    def local_translation_prompt(raw: str, target_lang: str) -> str:
        target = "English" if target_lang == "en" else "Simplified Chinese"
        return (
            f"Translate the following text to {target}. "
            "Return only the translated text, with no explanation or quotes.\n\n"
            f"{raw}"
        )

    def request_google_translation(raw: str, target_lang: str) -> str:
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
        return translated

    def request_local_ollama_translation(raw: str, target_lang: str) -> str:
        model = local_translation_model()
        endpoint = local_translation_url()
        if not model or not is_loopback_url(endpoint):
            return ""
        translated = ""
        for attempt in range(TRANSLATE_RETRIES):
            try:
                response = TRANSLATE_SESSION.post(
                    endpoint,
                    json={
                        "model": model,
                        "prompt": local_translation_prompt(raw, target_lang),
                        "stream": False,
                        "options": {"temperature": 0},
                    },
                    timeout=TRANSLATE_TIMEOUT,
                    proxies={"http": None, "https": None},
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    translated = normalize(data.get("response"))
                if translated:
                    break
            except Exception:
                translated = ""
                if attempt + 1 < TRANSLATE_RETRIES:
                    time.sleep(0.25 * (attempt + 1))
        return translated

    def request_translation(text: str, *, target_lang: str, cache_key: str, skip_translation) -> str:
        raw = normalize(text)
        if not raw or skip_translation(raw):
            return raw
        with TRANSLATION_LOCK:
            cached = TRANSLATION_CACHE.get(cache_key)
        if cached:
            return cached
        if translation_provider() == "local_ollama":
            translated = request_local_ollama_translation(raw, target_lang)
        else:
            translated = request_google_translation(raw, target_lang)
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
            cache_key=translation_cache_key(raw, 'zh-CN'),
            skip_translation=has_han,
        )

    def translate_query_to_en(text: str) -> str:
        raw = normalize(text)
        if not raw:
            return raw
        return request_translation(
            raw,
            target_lang='en',
            cache_key=translation_cache_key(raw, 'en'),
            skip_translation=lambda value: not has_han(value),
        )

    def apply_repo_translation(repo: dict[str, object]) -> None:
        raw = normalize(repo.get('description_raw') or repo.get('description'))
        repo['description_raw'] = raw
        if not raw:
            repo['description'] = ''
            return
        with TRANSLATION_LOCK:
            cached = TRANSLATION_CACHE.get(translation_cache_key(raw, 'zh-CN')) or TRANSLATION_CACHE.get(raw)
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
