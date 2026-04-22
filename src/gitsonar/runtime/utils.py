#!/usr/bin/env python3
from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes
import json
import logging
import os
import re
import socket
from datetime import datetime
from html import escape
from urllib.parse import urlparse

_DPAPI_PREFIX = 'dpapi:'
logger = logging.getLogger(__name__)


class _DataBlob(ctypes.Structure):
    _fields_ = [('cbData', ctypes.wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]


def encrypt_secret(plaintext: str) -> str:
    """用 Windows DPAPI 加密字符串，仅当前用户/机器可解密。非 Windows 或失败时原样返回。"""
    if not plaintext or os.name != 'nt':
        return plaintext
    try:
        data = plaintext.encode('utf-8')
        in_blob = _DataBlob(len(data), ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)))
        out_blob = _DataBlob()
        if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        ):
            return plaintext
        encrypted = bytes(ctypes.string_at(out_blob.pbData, out_blob.cbData))
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return _DPAPI_PREFIX + base64.b64encode(encrypted).decode('ascii')
    except Exception:
        return plaintext


def decrypt_secret(ciphertext: str) -> str:
    """解密 DPAPI 加密的字符串。若无 dpapi: 前缀则原样返回；非 Windows 且有前缀则返回空。"""
    if not ciphertext or not ciphertext.startswith(_DPAPI_PREFIX):
        return ciphertext
    if os.name != 'nt':
        return ''
    try:
        data = base64.b64decode(ciphertext[len(_DPAPI_PREFIX):])
        in_blob = _DataBlob(len(data), ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)))
        out_blob = _DataBlob()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        ):
            return ''
        plaintext_bytes = bytes(ctypes.string_at(out_blob.pbData, out_blob.cbData))
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return plaintext_bytes.decode('utf-8', errors='replace')
    except Exception:
        return ''

SPACE_RE = re.compile(r'\s+')
COUNT_RE = re.compile(r'([\d,]+)')
MD_CODE_RE = re.compile(r'```.*?```', re.S)
MD_LINK_RE = re.compile(r'\[([^\]]+)\]\([^)]+\)')
MD_IMG_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')
MD_HTML_RE = re.compile(r'<[^>]+>')
COMMON_LOCAL_PROXY_PORTS = (7897, 7890, 7892, 7893)


def normalize(value: object) -> str:
    return SPACE_RE.sub(' ', str(value or '').replace('\xa0', ' ')).strip()


def clamp_int(value: object, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        number = int(str(value).strip())
    except Exception:
        number = default
    if minimum is not None:
        number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def as_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    lowered = normalize(value).lower()
    if lowered in {'1', 'true', 'yes', 'on'}:
        return True
    if lowered in {'0', 'false', 'no', 'off'}:
        return False
    return default


def iso_now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def parse_iso_timestamp(value: object) -> int:
    raw = normalize(value)
    if not raw:
        return 0
    try:
        return int(datetime.fromisoformat(raw.replace('Z', '+00:00')).timestamp())
    except Exception:
        return 0


def atomic_write_json(path: str, payload: object) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=isinstance(payload, dict))
    os.replace(temp, path)


def atomic_write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(temp, path)


def load_json_file(path: str, default: object) -> object:
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("json_load_failed path=%s error=%s", path, exc)
        return default


def escape_attr(value: object) -> str:
    return escape(str(value or ''), quote=True)


def strip_markdown(text: str) -> str:
    text = MD_CODE_RE.sub(' ', text or '')
    text = MD_IMG_RE.sub(' ', text)
    text = MD_LINK_RE.sub(r'\1', text)
    text = MD_HTML_RE.sub(' ', text)
    text = re.sub(r'^[>#*\-]+', ' ', text, flags=re.M)
    return SPACE_RE.sub(' ', text).strip()


def extract_count(value: object) -> int:
    match = COUNT_RE.search(normalize(value))
    if not match:
        return 0
    digits = match.group(1).replace(',', '')
    return int(digits) if digits else 0


def normalize_proxy_url(value: object) -> str:
    proxy = normalize(value)
    if not proxy:
        return ''
    if '://' not in proxy:
        proxy = f'http://{proxy}'
    return proxy.rstrip('/')


def parse_proxy_endpoint(proxy_url: str) -> tuple[str | None, int | None]:
    parsed = urlparse(normalize_proxy_url(proxy_url))
    try:
        return parsed.hostname, int(parsed.port or 0)
    except Exception:
        return None, None


def tcp_port_open(host: str, port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def detect_local_proxy(skip: set[str] | None = None, ports: tuple[int, ...] = COMMON_LOCAL_PROXY_PORTS) -> str:
    skipped = {normalize_proxy_url(item) for item in (skip or set())}
    for port in ports:
        proxy = f'http://127.0.0.1:{port}'
        if proxy in skipped:
            continue
        if tcp_port_open('127.0.0.1', port):
            return proxy
    return ''
