#!/usr/bin/env python3
from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

SAFE_REFRESH_ERROR = "刷新失败。请检查网络、代理或 GitHub Token 后重试。"
SAFE_DISCOVERY_ERROR = "关键词发现失败。请检查网络、代理或 GitHub Token 后重试。"

_URL_CREDENTIALS_RE = re.compile(r"(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*://)(?P<userinfo>[^/\s@]+@)")
_GITHUB_TOKEN_RE = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{6,}|github_pat_[A-Za-z0-9_]{6,})\b")
_AUTH_BEARER_RE = re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s,;]+)")
_TOKEN_ASSIGNMENT_RE = re.compile(r"(?i)\b(token|access_token|github_token)\s*[:=]\s*([^\s,;]+)")
_WINDOWS_PATH_RE = re.compile(r"(?i)\b[A-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\?)+")


def redact_proxy_url(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = urlsplit(text)
    except ValueError:
        return redact_text(text)
    if parsed.scheme and "@" in parsed.netloc:
        hostport = parsed.netloc.rsplit("@", 1)[1]
        return urlunsplit((parsed.scheme, f"***:***@{hostport}", parsed.path, parsed.query, parsed.fragment))
    return redact_text(text)


def redact_text(value: object) -> str:
    text = str(value or "")
    if not text:
        return ""
    text = _URL_CREDENTIALS_RE.sub(lambda match: f"{match.group('scheme')}***:***@", text)
    text = _AUTH_BEARER_RE.sub(lambda match: f"{match.group(1)}[secret]", text)
    text = _TOKEN_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[secret]", text)
    text = _GITHUB_TOKEN_RE.sub("[secret]", text)
    text = _WINDOWS_PATH_RE.sub("[local path]", text)
    return text


def safe_status_payload(payload: object) -> dict[str, object]:
    clean = dict(payload) if isinstance(payload, dict) else {}
    if str(clean.get("error") or "").strip():
        clean["error"] = SAFE_REFRESH_ERROR
    return clean


__all__ = [
    "SAFE_DISCOVERY_ERROR",
    "SAFE_REFRESH_ERROR",
    "redact_proxy_url",
    "redact_text",
    "safe_status_payload",
]
