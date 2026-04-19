#!/usr/bin/env python3
from __future__ import annotations

import os
from types import SimpleNamespace
from urllib.parse import urlparse

DEFAULT_SETTINGS = {
    "port": 8080,
    "refresh_hours": 1,
    "result_limit": 25,
    "github_token": "",
    "proxy": "",
    "default_sort": "stars",
    "auto_start": False,
}


def make_settings_runtime(
    *,
    settings,
    settings_path,
    runtime_root,
    session,
    translate_session,
    current_port_getter,
    runtime_port_getter,
    normalize,
    clamp_int,
    as_bool,
    decrypt_secret,
    encrypt_secret,
    normalize_proxy_url,
    parse_proxy_endpoint,
    detect_local_proxy,
    tcp_port_open,
    load_json_file,
    atomic_write_json,
    default_settings=None,
):
    SETTINGS = settings
    SETTINGS_PATH = settings_path
    RUNTIME_ROOT = runtime_root
    SESSION = session
    TRANSLATE_SESSION = translate_session
    defaults = dict(default_settings or DEFAULT_SETTINGS)
    proxy_state = {"effective": "", "source": "none"}

    def normalize_proxy_setting(value: object) -> str:
        return normalize_proxy_url(decrypt_secret(normalize(value)))

    def proxy_has_credentials(proxy_url: str) -> bool:
        parsed = urlparse(normalize_proxy_url(proxy_url))
        return bool(parsed.username or parsed.password)

    def normalize_settings(payload: object) -> dict[str, object]:
        raw = payload if isinstance(payload, dict) else {}
        normalized = dict(defaults)
        normalized["port"] = clamp_int(raw.get("port"), defaults["port"], 1, 65535)
        normalized["refresh_hours"] = clamp_int(raw.get("refresh_hours"), defaults["refresh_hours"], 1, 24)
        normalized["result_limit"] = clamp_int(raw.get("result_limit"), defaults["result_limit"], 10, 100)
        normalized["github_token"] = decrypt_secret(normalize(raw.get("github_token", "")))
        normalized["proxy"] = normalize_proxy_setting(raw.get("proxy", ""))
        normalized["default_sort"] = normalize(raw.get("default_sort", defaults["default_sort"])) or defaults["default_sort"]
        normalized["auto_start"] = as_bool(raw.get("auto_start"), False)
        return normalized

    def merge_settings(payload: object, current: object | None = None) -> dict[str, object]:
        raw = payload if isinstance(payload, dict) else {}
        existing = normalize_settings(current if isinstance(current, dict) else SETTINGS)
        merged = dict(existing)
        merged["port"] = clamp_int(raw.get("port"), existing["port"], 1, 65535)
        merged["refresh_hours"] = clamp_int(raw.get("refresh_hours"), existing["refresh_hours"], 1, 24)
        merged["result_limit"] = clamp_int(raw.get("result_limit"), existing["result_limit"], 10, 100)
        merged["default_sort"] = normalize(raw.get("default_sort", existing["default_sort"])) or existing["default_sort"]
        merged["auto_start"] = as_bool(raw.get("auto_start"), existing["auto_start"])

        if as_bool(raw.get("clear_github_token"), False):
            merged["github_token"] = ""
        elif "github_token" in raw:
            token = decrypt_secret(normalize(raw.get("github_token", "")))
            if token:
                merged["github_token"] = token

        if as_bool(raw.get("clear_proxy"), False):
            merged["proxy"] = ""
        elif "proxy" in raw:
            proxy = normalize_proxy_setting(raw.get("proxy", ""))
            if proxy:
                merged["proxy"] = proxy

        return merged

    def sanitize_settings(include_sensitive: bool = False) -> dict[str, object]:
        configured_port = clamp_int(SETTINGS.get("port", defaults["port"]), defaults["port"], 1, 65535)
        payload = {
            "port": configured_port,
            "effective_port": current_port_getter(),
            "restart_required": bool(runtime_port_getter() and configured_port != current_port_getter()),
            "refresh_hours": SETTINGS.get("refresh_hours", defaults["refresh_hours"]),
            "result_limit": SETTINGS.get("result_limit", defaults["result_limit"]),
            "default_sort": SETTINGS.get("default_sort", defaults["default_sort"]),
            "auto_start": bool(SETTINGS.get("auto_start")),
            "has_github_token": bool(normalize(SETTINGS.get("github_token", ""))),
            "has_proxy": bool(normalize_proxy_url(SETTINGS.get("proxy", ""))),
            "effective_proxy": proxy_state["effective"],
            "proxy_source": proxy_state["source"],
            "runtime_root": RUNTIME_ROOT,
        }
        if include_sensitive:
            # Preserve the legacy response shape without returning plaintext secrets.
            payload["github_token"] = ""
            payload["proxy"] = ""
        return payload

    def save_settings(payload: dict[str, object]) -> None:
        clean = dict(payload)
        token = normalize(clean.get("github_token", ""))
        if token:
            clean["github_token"] = encrypt_secret(token)
        elif "github_token" in clean:
            clean["github_token"] = ""
        if "proxy" in clean:
            proxy = normalize_proxy_setting(clean.get("proxy", ""))
            clean["proxy"] = encrypt_secret(proxy) if proxy and proxy_has_credentials(proxy) else proxy
        atomic_write_json(SETTINGS_PATH, clean)

    def load_settings() -> dict[str, object]:
        loaded = normalize_settings(load_json_file(SETTINGS_PATH, defaults))
        if not os.path.exists(SETTINGS_PATH):
            save_settings(loaded)
        return loaded

    def apply_runtime_settings() -> None:
        SESSION.proxies.clear()
        TRANSLATE_SESSION.proxies.clear()
        proxy_state["effective"] = ""
        proxy_state["source"] = "none"

        configured = normalize_proxy_url(SETTINGS.get("proxy", ""))
        effective = configured
        if configured:
            host, port = parse_proxy_endpoint(configured)
            if host in {"127.0.0.1", "localhost"} and port and not tcp_port_open(host, port):
                effective = detect_local_proxy(skip={configured})
                proxy_state["source"] = "auto-fallback" if effective else "none"
            else:
                proxy_state["source"] = "configured"
        else:
            effective = detect_local_proxy()
            proxy_state["source"] = "auto" if effective else "none"

        if effective:
            SESSION.proxies.update({"http": effective, "https": effective})
            TRANSLATE_SESSION.proxies.update({"http": effective, "https": effective})
            proxy_state["effective"] = effective

        SESSION.headers.pop("Authorization", None)
        token = normalize(SETTINGS.get("github_token", ""))
        if token:
            SESSION.headers["Authorization"] = f"Bearer {token}"

    return SimpleNamespace(
        normalize_settings=normalize_settings,
        merge_settings=merge_settings,
        sanitize_settings=sanitize_settings,
        save_settings=save_settings,
        load_settings=load_settings,
        apply_runtime_settings=apply_runtime_settings,
    )


__all__ = ["DEFAULT_SETTINGS", "make_settings_runtime"]
