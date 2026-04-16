
#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import hashlib
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from .runtime_github import make_github_runtime
from .runtime_http import make_app_handler
from .runtime_shell import make_shell_runtime
from .runtime_ui import build_html as build_runtime_html
from .runtime_utils import (
    as_bool,
    atomic_write_json,
    atomic_write_text,
    clamp_int,
    decrypt_secret,
    detect_local_proxy,
    encrypt_secret,
    extract_count,
    iso_now,
    load_json_file,
    normalize,
    normalize_proxy_url,
    parse_iso_timestamp,
    parse_proxy_endpoint,
    strip_markdown,
    tcp_port_open,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

APP_NAME = 'GitSonar'
APP_SLUG = 'GitSonar'
LEGACY_APP_NAME = 'GitHub Trend Radar'
LEGACY_APP_SLUG = 'GitHubTrendRadar'
IS_FROZEN = getattr(sys, 'frozen', False)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PACKAGE_DIR))
DEV_RUNTIME_ROOT = os.path.join(PROJECT_ROOT, 'runtime-data')
DEV_ENTRY_SCRIPT = os.path.join(PROJECT_ROOT, 'src', 'GitSonar.pyw')
EXEC_DIR = os.path.dirname(os.path.abspath(sys.executable)) if IS_FROZEN else PROJECT_ROOT
LOCAL_APPDATA_ROOT = os.environ.get('LOCALAPPDATA', EXEC_DIR)
DEV_RUNTIME_ITEMS = (
    'data',
    '.desktop_shell',
    '.translation_cache.json',
    'settings.json',
    'status.json',
    'trending.html',
    'user_state.json',
    'repo_details_cache.json',
    'runtime_state.json',
)


def runtime_root_for_slug(slug: str) -> str:
    return os.path.join(LOCAL_APPDATA_ROOT, slug) if IS_FROZEN else DEV_RUNTIME_ROOT


def merge_dev_runtime_root() -> str:
    preferred = DEV_RUNTIME_ROOT
    legacy = PROJECT_ROOT
    try:
        os.makedirs(preferred, exist_ok=True)
        migrated_items: list[str] = []
        for name in DEV_RUNTIME_ITEMS:
            source = os.path.join(legacy, name)
            target = os.path.join(preferred, name)
            if not os.path.exists(source) or os.path.exists(target):
                continue
            try:
                if os.path.isdir(source):
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
                migrated_items.append(name)
            except Exception as exc:
                logger.warning('迁移开发态运行数据失败: %s (%s)', source, exc)
        if migrated_items:
            logger.info('已将 %s 项开发态运行数据迁移到 %s', len(migrated_items), preferred)
    except Exception as exc:
        logger.warning('初始化开发态运行目录失败，回退到仓库根目录: %s', exc)
        return legacy
    return preferred


def merge_legacy_runtime_root() -> str:
    preferred = runtime_root_for_slug(APP_SLUG)
    legacy = runtime_root_for_slug(LEGACY_APP_SLUG)
    if not IS_FROZEN or preferred == legacy or not os.path.isdir(legacy):
        return preferred
    try:
        os.makedirs(preferred, exist_ok=True)
        migrated_items: list[str] = []
        for name in os.listdir(legacy):
            source = os.path.join(legacy, name)
            target = os.path.join(preferred, name)
            if os.path.exists(target):
                continue
            try:
                if os.path.isdir(source):
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
                migrated_items.append(name)
            except Exception as exc:
                logger.warning('迁移旧数据项失败: %s (%s)', source, exc)
        if migrated_items:
            logger.info('已从旧数据目录合并 %s 项到 %s', len(migrated_items), preferred)
    except Exception as exc:
        logger.warning('初始化新数据目录失败，回退到旧目录: %s', exc)
        if os.path.isdir(legacy) and not os.path.isdir(preferred):
            return legacy
    return preferred


RUNTIME_ROOT = merge_legacy_runtime_root() if IS_FROZEN else merge_dev_runtime_root()
LEGACY_RUNTIME_ROOT = runtime_root_for_slug(LEGACY_APP_SLUG) if IS_FROZEN else PROJECT_ROOT
DATA_DIR = os.path.join(RUNTIME_ROOT, 'data')
HTML_PATH = os.path.join(RUNTIME_ROOT, 'trending.html')
STATUS_PATH = os.path.join(RUNTIME_ROOT, 'status.json')
SETTINGS_PATH = os.path.join(RUNTIME_ROOT, 'settings.json')
USER_STATE_PATH = os.path.join(RUNTIME_ROOT, 'user_state.json')
DISCOVERY_STATE_PATH = os.path.join(RUNTIME_ROOT, 'discovery_state.json')
LATEST_SNAPSHOT_PATH = os.path.join(DATA_DIR, 'latest.json')
DETAIL_CACHE_PATH = os.path.join(RUNTIME_ROOT, 'repo_details_cache.json')
RUNTIME_STATE_PATH = os.path.join(RUNTIME_ROOT, 'runtime_state.json')
DESKTOP_SHELL_DIR = os.path.join(RUNTIME_ROOT, '.desktop_shell')
CACHE_PATH = os.path.join(RUNTIME_ROOT, '.translation_cache.json')
LEGACY_RUNTIME_STATE_PATH = os.path.join(LEGACY_RUNTIME_ROOT, 'runtime_state.json')
LOCAL_HOST = '127.0.0.1'
SERVER_HOST = LOCAL_HOST
SEARCH_API_URL = 'https://api.github.com/search/repositories'
REPO_API_URL = 'https://api.github.com/repos'
API_TIMEOUT = (5, 12)
TRENDING_TIMEOUT = (4, 10)
TRANSLATE_TIMEOUT = (4, 8)
TRANSLATE_RETRIES = 2
DETAIL_CACHE_SECONDS = 6 * 3600
_MAX_TRANSLATION_CACHE_SIZE = 5000
_MAX_DETAIL_CACHE_SIZE = 500
FAVORITE_WATCH_MIN_SECONDS_NO_TOKEN = 6 * 3600
FAVORITE_WATCH_MIN_SECONDS_WITH_TOKEN = 3600
FAVORITE_RELEASE_MIN_SECONDS_NO_TOKEN = 24 * 3600
FAVORITE_RELEASE_MIN_SECONDS_WITH_TOKEN = 6 * 3600
FAVORITE_WATCH_MAX_CHECKS_NO_TOKEN = 6
FAVORITE_WATCH_MAX_CHECKS_WITH_TOKEN = 20
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
PERIODS = [
    {'key': 'daily', 'label': '今天', 'days': 1},
    {'key': 'weekly', 'label': '本周', 'days': 7},
    {'key': 'monthly', 'label': '本月', 'days': 30},
]
STATE_DEFS = [
    {'key': 'favorites', 'label': '关注', 'button': '关注'},
    {'key': 'watch_later', 'label': '待看', 'button': '待看'},
    {'key': 'read', 'label': '已读', 'button': '已读'},
    {'key': 'ignored', 'label': '忽略', 'button': '忽略'},
]
DEFAULT_SETTINGS = {
    'port': 8080,
    'refresh_hours': 1,
    'result_limit': 25,
    'github_token': '',
    'proxy': '',
    'default_sort': 'stars',
    'auto_start': False,
    'close_behavior': 'tray',
}
HAN_RE = re.compile(r'[\u3400-\u9fff]')

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
LOCAL_CONTROL = requests.Session()
LOCAL_CONTROL.trust_env = False
TRANSLATE_SESSION = requests.Session()
TRANSLATE_SESSION.trust_env = False
TRANSLATE_SESSION.headers.update({
    'User-Agent': HEADERS['User-Agent'],
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})
SETTINGS_LOCK = threading.RLock()
STATE_LOCK = threading.RLock()
DISCOVERY_LOCK = threading.RLock()
DISCOVERY_JOB_LOCK = threading.RLock()
REFRESH_LOCK = threading.Lock()
TRANSLATION_LOCK = threading.RLock()
DETAIL_CACHE_LOCK = threading.RLock()
SETTINGS: dict[str, object] = {}
USER_STATE: dict[str, object] = {}
DISCOVERY_STATE: dict[str, object] = {}
DISCOVERY_JOBS: dict[str, dict[str, object]] = {}
ACTIVE_DISCOVERY_JOB_ID = ''
CURRENT_SNAPSHOT: dict[str, object] = {}
ACTIVE_PROXY = ''
ACTIVE_PROXY_SOURCE = 'none'
RUNTIME_PORT: int | None = None
BROWSER_PROCESS: subprocess.Popen | None = None
BROWSER_HIDDEN = False
MAIN_URL = ''
SINGLE_INSTANCE_MUTEXES: list[object] = []
APP_EXIT_EVENT = threading.Event()
BROWSER_LOCK = threading.RLock()
DETAIL_FETCH_SEMAPHORE = threading.Semaphore(3)
TRANSLATION_CACHE: dict[str, str] = {}
DETAIL_CACHE: dict[str, object] = {}
DETAIL_FETCH_LOCKS: dict[str, threading.Lock] = {}
_MAX_DETAIL_FETCH_LOCKS = 1000

if os.name == 'nt':
    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ('dwSize', ctypes.c_ulong),
            ('cntUsage', ctypes.c_ulong),
            ('th32ProcessID', ctypes.c_ulong),
            ('th32DefaultHeapID', ctypes.c_size_t),
            ('th32ModuleID', ctypes.c_ulong),
            ('cntThreads', ctypes.c_ulong),
            ('th32ParentProcessID', ctypes.c_ulong),
            ('pcPriClassBase', ctypes.c_long),
            ('dwFlags', ctypes.c_ulong),
            ('szExeFile', ctypes.c_wchar * 260),
        ]


def ensure_runtime_layout() -> None:
    os.makedirs(RUNTIME_ROOT, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def configure_console() -> None:
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name, None)
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
    hide_console_window_if_needed()


def parent_process_name() -> str:
    if os.name != 'nt':
        return ''
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if snapshot == invalid_handle:
        return ''
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return ''
        names: dict[int, str] = {}
        parent_pid = 0
        while True:
            names[int(entry.th32ProcessID)] = entry.szExeFile
            if int(entry.th32ProcessID) == os.getpid():
                parent_pid = int(entry.th32ParentProcessID)
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
        return normalize(names.get(parent_pid)).lower()
    finally:
        kernel32.CloseHandle(snapshot)


def hide_console_window_if_needed() -> None:
    if os.name != 'nt':
        return
    for slug in {APP_SLUG, LEGACY_APP_SLUG}:
        if normalize(os.environ.get(f'{slug.upper()}_SHOW_CONSOLE')).lower() in {'1', 'true', 'yes'}:
            return
    try:
        kernel32 = ctypes.windll.kernel32
        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return
        if parent_process_name() not in {'explorer.exe', 'wscript.exe', 'cscript.exe'}:
            return
        ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def load_detail_cache() -> dict[str, object]:
    raw = load_json_file(DETAIL_CACHE_PATH, {})
    return raw if isinstance(raw, dict) else {}


def cached_repo_details(cache_key: str) -> dict[str, object] | None:
    now = int(time.time())
    with DETAIL_CACHE_LOCK:
        cached = DETAIL_CACHE.get(cache_key, {})
        if isinstance(cached, dict) and clamp_int(cached.get('expires_at'), 0, 0) > now and isinstance(cached.get('data'), dict):
            return dict(cached['data'])
    return None


def detail_fetch_lock(cache_key: str) -> threading.Lock:
    with DETAIL_CACHE_LOCK:
        lock = DETAIL_FETCH_LOCKS.get(cache_key)
        if lock is None:
            if len(DETAIL_FETCH_LOCKS) >= _MAX_DETAIL_FETCH_LOCKS:
                # 优先清理不在缓存中的过期锁；仍超限则删除前一半
                stale = [k for k in DETAIL_FETCH_LOCKS if k not in DETAIL_CACHE]
                for k in stale[:500]:
                    del DETAIL_FETCH_LOCKS[k]
                if len(DETAIL_FETCH_LOCKS) >= _MAX_DETAIL_FETCH_LOCKS:
                    for k in list(DETAIL_FETCH_LOCKS)[:500]:
                        del DETAIL_FETCH_LOCKS[k]
            lock = threading.Lock()
            DETAIL_FETCH_LOCKS[cache_key] = lock
        return lock


def save_repo_details(cache_key: str, details: dict[str, object]) -> None:
    now = int(time.time())
    with DETAIL_CACHE_LOCK:
        DETAIL_CACHE[cache_key] = {
            'expires_at': now + DETAIL_CACHE_SECONDS,
            'data': dict(details),
        }
        # 清理已过期条目
        expired = [k for k, v in DETAIL_CACHE.items() if isinstance(v, dict) and clamp_int(v.get('expires_at'), 0, 0) <= now]
        for k in expired:
            del DETAIL_CACHE[k]
        # 若仍超过上限，按过期时间升序删除最旧条目
        if len(DETAIL_CACHE) > _MAX_DETAIL_CACHE_SIZE:
            oldest = sorted(DETAIL_CACHE, key=lambda k: clamp_int(DETAIL_CACHE[k].get('expires_at') if isinstance(DETAIL_CACHE[k], dict) else 0, 0, 0))
            for k in oldest[:len(DETAIL_CACHE) - _MAX_DETAIL_CACHE_SIZE]:
                del DETAIL_CACHE[k]
        atomic_write_json(DETAIL_CACHE_PATH, DETAIL_CACHE)


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


def normalize_settings(payload: object) -> dict[str, object]:
    raw = payload if isinstance(payload, dict) else {}
    settings = dict(DEFAULT_SETTINGS)
    settings['port'] = clamp_int(raw.get('port'), DEFAULT_SETTINGS['port'], 1, 65535)
    settings['refresh_hours'] = clamp_int(raw.get('refresh_hours'), DEFAULT_SETTINGS['refresh_hours'], 1, 24)
    settings['result_limit'] = clamp_int(raw.get('result_limit'), DEFAULT_SETTINGS['result_limit'], 10, 100)
    settings['github_token'] = decrypt_secret(normalize(raw.get('github_token', '')))
    settings['proxy'] = normalize_proxy_url(raw.get('proxy', ''))
    settings['default_sort'] = normalize(raw.get('default_sort', DEFAULT_SETTINGS['default_sort'])) or DEFAULT_SETTINGS['default_sort']
    settings['auto_start'] = as_bool(raw.get('auto_start'), False)
    close_behavior = normalize(raw.get('close_behavior', DEFAULT_SETTINGS['close_behavior'])).lower()
    settings['close_behavior'] = close_behavior if close_behavior in {'tray', 'exit'} else DEFAULT_SETTINGS['close_behavior']
    return settings


def sanitize_settings(include_sensitive: bool) -> dict[str, object]:
    payload = {
        'port': SETTINGS.get('port', 8080),
        'effective_port': current_port(),
        'restart_required': bool(RUNTIME_PORT and clamp_int(SETTINGS.get('port', 8080), 8080, 1, 65535) != current_port()),
        'refresh_hours': SETTINGS.get('refresh_hours', 1),
        'result_limit': SETTINGS.get('result_limit', 25),
        'default_sort': SETTINGS.get('default_sort', 'stars'),
        'auto_start': bool(SETTINGS.get('auto_start')),
        'close_behavior': SETTINGS.get('close_behavior', 'tray'),
        'has_github_token': bool(normalize(SETTINGS.get('github_token', ''))),
        'effective_proxy': ACTIVE_PROXY,
        'proxy_source': ACTIVE_PROXY_SOURCE,
        'runtime_root': RUNTIME_ROOT,
    }
    if include_sensitive:
        payload['github_token'] = SETTINGS.get('github_token', '')
        payload['proxy'] = SETTINGS.get('proxy', '')
    return payload


def save_settings(settings: dict[str, object]) -> None:
    payload = dict(settings)
    token = normalize(payload.get('github_token', ''))
    if token:
        payload['github_token'] = encrypt_secret(token)
    atomic_write_json(SETTINGS_PATH, payload)


def load_settings() -> dict[str, object]:
    settings = normalize_settings(load_json_file(SETTINGS_PATH, DEFAULT_SETTINGS))
    if not os.path.exists(SETTINGS_PATH):
        save_settings(settings)
    return settings


def apply_runtime_settings() -> None:
    global ACTIVE_PROXY, ACTIVE_PROXY_SOURCE
    SESSION.proxies.clear()
    TRANSLATE_SESSION.proxies.clear()
    ACTIVE_PROXY = ''
    ACTIVE_PROXY_SOURCE = 'none'
    configured = normalize_proxy_url(SETTINGS.get('proxy', ''))
    effective = configured
    if configured:
        host, port = parse_proxy_endpoint(configured)
        if host in {'127.0.0.1', 'localhost'} and port and not tcp_port_open(host, port):
            effective = detect_local_proxy(skip={configured})
            ACTIVE_PROXY_SOURCE = 'auto-fallback' if effective else 'none'
        else:
            ACTIVE_PROXY_SOURCE = 'configured'
    else:
        effective = detect_local_proxy()
        ACTIVE_PROXY_SOURCE = 'auto' if effective else 'none'
    if effective:
        SESSION.proxies.update({'http': effective, 'https': effective})
        TRANSLATE_SESSION.proxies.update({'http': effective, 'https': effective})
        ACTIVE_PROXY = effective
    SESSION.headers.pop('Authorization', None)
    token = normalize(SETTINGS.get('github_token', ''))
    if token:
        SESSION.headers['Authorization'] = f'Bearer {token}'


def default_user_state() -> dict[str, object]:
    return {'favorites': [], 'watch_later': [], 'read': [], 'ignored': [], 'repo_records': {}, 'favorite_watch': {}, 'favorite_updates': []}


def default_discovery_state() -> dict[str, object]:
    return {
        'saved_queries': [],
        'last_query': {},
        'last_results': [],
        'last_related_terms': [],
        'last_generated_queries': [],
        'last_translated_query': '',
        'last_warnings': [],
        'last_run_at': '',
        'last_error': '',
    }


DISCOVERY_RANKING_PROFILES = {'balanced', 'hot', 'fresh', 'builder', 'trend'}


def normalize_discovery_ranking_profile(value: object) -> str:
    clean = normalize(value).lower()
    return clean if clean in DISCOVERY_RANKING_PROFILES else 'balanced'


def discovery_query_id(query: str, language: str, auto_expand: bool, ranking_profile: str = 'balanced') -> str:
    payload = f'{normalize(query)}\n{normalize(language)}\n{int(bool(auto_expand))}\n{normalize_discovery_ranking_profile(ranking_profile)}'
    return hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]


def normalize_discovery_query(payload: object) -> dict[str, object] | None:
    raw = payload if isinstance(payload, dict) else {}
    query = normalize(raw.get('query'))
    if not query:
        return None
    language = normalize(raw.get('language'))
    auto_expand = as_bool(raw.get('auto_expand'), True)
    ranking_profile = normalize_discovery_ranking_profile(raw.get('ranking_profile'))
    default_limit = clamp_int(SETTINGS.get('result_limit', 20), 20, 5, 50) if SETTINGS else 20
    return {
        'id': normalize(raw.get('id')) or discovery_query_id(query, language, auto_expand, ranking_profile),
        'query': query,
        'language': language,
        'limit': clamp_int(raw.get('limit'), default_limit, 5, 50),
        'auto_expand': auto_expand,
        'ranking_profile': ranking_profile,
        'created_at': normalize(raw.get('created_at')) or iso_now(),
        'last_run_at': normalize(raw.get('last_run_at')),
    }


def normalize_repo(repo: object) -> dict[str, object] | None:
    if not isinstance(repo, dict):
        return None
    full_name = normalize(repo.get('full_name'))
    url = normalize(repo.get('url'))
    if not full_name or not url or '/' not in full_name:
        return None
    owner, name = full_name.split('/', 1)
    gained = clamp_int(repo.get('gained'), 0, 0)
    gained_text = normalize(repo.get('gained_text'))
    growth_source = normalize(repo.get('growth_source')).lower()
    if growth_source not in {'trending', 'estimated', 'unavailable'}:
        growth_source = 'trending' if gained_text or gained > 0 else 'unavailable'
    return {
        'full_name': full_name,
        'owner': owner,
        'name': name,
        'url': url,
        'description': normalize(repo.get('description')),
        'description_raw': normalize(repo.get('description_raw') or repo.get('description')),
        'language': normalize(repo.get('language')),
        'stars': clamp_int(repo.get('stars'), 0, 0),
        'forks': clamp_int(repo.get('forks'), 0, 0),
        'gained': gained,
        'gained_text': gained_text,
        'growth_source': growth_source,
        'rank': clamp_int(repo.get('rank'), 0, 0),
        'period_key': normalize(repo.get('period_key')) or 'daily',
        'source_label': normalize(repo.get('source_label')) or 'GitHub API',
        'updated_at': normalize(repo.get('updated_at')),
        'pushed_at': normalize(repo.get('pushed_at')),
        'topics': [normalize(item) for item in repo.get('topics', []) if normalize(item)] if isinstance(repo.get('topics'), list) else [],
        'discover_source': normalize(repo.get('discover_source')),
        'trending_hit': as_bool(repo.get('trending_hit'), False),
        'relevance_score': clamp_int(repo.get('relevance_score'), 0, 0, 100),
        'hot_score': clamp_int(repo.get('hot_score'), 0, 0, 100),
        'composite_score': clamp_int(repo.get('composite_score'), 0, 0, 100),
        'matched_terms': [normalize(item) for item in repo.get('matched_terms', []) if normalize(item)] if isinstance(repo.get('matched_terms'), list) else [],
        'match_reasons': [normalize(item) for item in repo.get('match_reasons', []) if normalize(item)] if isinstance(repo.get('match_reasons'), list) else [],
    }


def repo_from_url(url: object) -> dict[str, object] | None:
    raw = normalize(url)
    if not raw:
        return None
    parsed = urlparse(raw)
    parts = [part for part in parsed.path.split('/') if part]
    if len(parts) < 2:
        return None
    full_name = f'{parts[0]}/{parts[1]}'
    return normalize_repo({'full_name': full_name, 'url': f'https://github.com/{full_name}'})


def normalize_watch_entry(payload: object) -> dict[str, object] | None:
    raw = payload if isinstance(payload, dict) else {}
    full_name = normalize(raw.get('full_name'))
    url = normalize(raw.get('url'))
    if not full_name or not url:
        return None
    return {
        'full_name': full_name,
        'url': url,
        'stars': clamp_int(raw.get('stars'), 0, 0),
        'forks': clamp_int(raw.get('forks'), 0, 0),
        'open_issues': clamp_int(raw.get('open_issues'), 0, 0),
        'updated_at': normalize(raw.get('updated_at')),
        'pushed_at': normalize(raw.get('pushed_at')),
        'latest_release_tag': normalize(raw.get('latest_release_tag')),
        'latest_release_published_at': normalize(raw.get('latest_release_published_at')),
        'release_checked_at': normalize(raw.get('release_checked_at')),
        'checked_at': normalize(raw.get('checked_at')),
    }


def normalize_favorite_update(payload: object) -> dict[str, object] | None:
    raw = payload if isinstance(payload, dict) else {}
    full_name = normalize(raw.get('full_name'))
    url = normalize(raw.get('url'))
    if not full_name or not url:
        return None
    changes = [normalize(item) for item in raw.get('changes', []) if normalize(item)]
    if not changes:
        return None
    return {
        'id': normalize(raw.get('id')) or f'{full_name}:{normalize(raw.get("checked_at"))}',
        'full_name': full_name,
        'url': url,
        'checked_at': normalize(raw.get('checked_at')),
        'changes': changes,
        'stars': clamp_int(raw.get('stars'), 0, 0),
        'forks': clamp_int(raw.get('forks'), 0, 0),
        'latest_release_tag': normalize(raw.get('latest_release_tag')),
        'pushed_at': normalize(raw.get('pushed_at')),
    }


def normalize_discovery_state(payload: object) -> dict[str, object]:
    raw = payload if isinstance(payload, dict) else {}
    state = default_discovery_state()
    saved_queries: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for item in raw.get('saved_queries', []):
        clean = normalize_discovery_query(item)
        if clean and clean['id'] not in seen_ids:
            saved_queries.append(clean)
            seen_ids.add(clean['id'])
    state['saved_queries'] = saved_queries
    state['last_query'] = normalize_discovery_query(raw.get('last_query')) or {}
    state['last_results'] = [clean for item in raw.get('last_results', []) if (clean := normalize_repo(item))]
    state['last_related_terms'] = [normalize(item) for item in raw.get('last_related_terms', []) if normalize(item)][:12]
    state['last_generated_queries'] = [normalize(item) for item in raw.get('last_generated_queries', []) if normalize(item)][:12]
    state['last_translated_query'] = normalize(raw.get('last_translated_query'))
    state['last_warnings'] = [normalize(item) for item in raw.get('last_warnings', []) if normalize(item)][:8]
    state['last_run_at'] = normalize(raw.get('last_run_at'))
    state['last_error'] = normalize(raw.get('last_error'))
    return state


def normalize_user_state(payload: object) -> dict[str, object]:
    raw = payload if isinstance(payload, dict) else {}
    state = default_user_state()
    for key in ('favorites', 'watch_later', 'read', 'ignored'):
        state[key] = list(dict.fromkeys(normalize(item) for item in raw.get(key, []) if normalize(item)))
    records = raw.get('repo_records', {}) if isinstance(raw.get('repo_records'), dict) else {}
    state['repo_records'] = {url: clean for url, repo in records.items() if (clean := normalize_repo(repo))}
    watch = raw.get('favorite_watch', {}) if isinstance(raw.get('favorite_watch'), dict) else {}
    state['favorite_watch'] = {url: clean for url, item in watch.items() if (clean := normalize_watch_entry(item))}
    favorite_updates: list[dict[str, object]] = []
    seen_update_ids: set[str] = set()
    for item in raw.get('favorite_updates', []):
        clean = normalize_favorite_update(item)
        if clean and clean['id'] not in seen_update_ids:
            favorite_updates.append(clean)
            seen_update_ids.add(clean['id'])
    state['favorite_updates'] = favorite_updates
    return state


def load_user_state() -> dict[str, object]:
    state = normalize_user_state(load_json_file(USER_STATE_PATH, default_user_state()))
    if not os.path.exists(USER_STATE_PATH):
        atomic_write_json(USER_STATE_PATH, state)
    return state


def save_user_state() -> None:
    atomic_write_json(USER_STATE_PATH, USER_STATE)


def export_user_state() -> dict[str, object]:
    with STATE_LOCK:
        return json.loads(json.dumps(USER_STATE, ensure_ascii=False))


def state_counts(state: dict[str, object]) -> dict[str, int]:
    return {
        'favorites': len(state.get('favorites', [])),
        'watch_later': len(state.get('watch_later', [])),
        'read': len(state.get('read', [])),
        'ignored': len(state.get('ignored', [])),
        'repo_records': len(state.get('repo_records', {})),
        'favorite_updates': len(state.get('favorite_updates', [])),
    }


def ordered_unique_urls(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            clean = normalize(item)
            if clean and clean not in seen:
                merged.append(clean)
                seen.add(clean)
    return merged


def merge_favorite_updates(*groups: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for group in groups:
        for item in group:
            clean = normalize_favorite_update(item)
            if clean and clean['id'] not in seen_ids:
                merged.append(clean)
                seen_ids.add(clean['id'])
    return merged[:100]


def coerce_import_user_state(payload: object) -> dict[str, object]:
    if isinstance(payload, dict):
        if isinstance(payload.get('data'), dict):
            raw_state = payload.get('data')
        elif isinstance(payload.get('user_state'), dict):
            raw_state = payload.get('user_state')
        else:
            raw_state = payload
    else:
        raw_state = {}
    state = normalize_user_state(raw_state)
    if not any(state.get(key) for key in ('favorites', 'watch_later', 'read', 'ignored')) and not state.get('repo_records'):
        raise ValueError('导入文件里没有可恢复的用户状态')
    return state


def import_user_state(payload: object) -> dict[str, object]:
    mode = normalize(payload.get('mode') if isinstance(payload, dict) else '').lower()
    if mode not in {'merge', 'replace'}:
        mode = 'merge'
    imported = coerce_import_user_state(payload)
    with STATE_LOCK:
        before_counts = state_counts(USER_STATE)
        if mode == 'replace':
            next_state = imported
        else:
            next_state = default_user_state()
            for key in ('favorites', 'watch_later', 'read', 'ignored'):
                next_state[key] = ordered_unique_urls(imported.get(key, []), USER_STATE.get(key, []))
            next_state['repo_records'] = dict(USER_STATE.get('repo_records', {}))
            next_state['repo_records'].update(imported.get('repo_records', {}))
            next_state['favorite_watch'] = dict(USER_STATE.get('favorite_watch', {}))
            next_state['favorite_watch'].update(imported.get('favorite_watch', {}))
            next_state['favorite_updates'] = merge_favorite_updates(
                imported.get('favorite_updates', []),
                USER_STATE.get('favorite_updates', []),
            )

        favorite_urls = set(next_state.get('favorites', []))
        next_state['favorite_watch'] = {
            url: item for url, item in next_state.get('favorite_watch', {}).items()
            if url in favorite_urls and normalize_watch_entry(item)
        }
        next_state['favorite_updates'] = [
            item for item in next_state.get('favorite_updates', [])
            if item.get('url') in favorite_urls
        ][:100]
        USER_STATE.clear()
        USER_STATE.update(normalize_user_state(next_state))
        save_user_state()
        after_counts = state_counts(USER_STATE)
    sync_repo_records(CURRENT_SNAPSHOT)
    return {
        'mode': mode,
        'before_counts': before_counts,
        'after_counts': after_counts,
        'user_state': export_user_state(),
    }


def load_discovery_state() -> dict[str, object]:
    state = normalize_discovery_state(load_json_file(DISCOVERY_STATE_PATH, default_discovery_state()))
    if not os.path.exists(DISCOVERY_STATE_PATH):
        atomic_write_json(DISCOVERY_STATE_PATH, state)
    return state


def save_discovery_state() -> None:
    atomic_write_json(DISCOVERY_STATE_PATH, DISCOVERY_STATE)


def export_discovery_state() -> dict[str, object]:
    with DISCOVERY_LOCK:
        return json.loads(json.dumps(DISCOVERY_STATE, ensure_ascii=False))


def clear_discovery_results() -> dict[str, object]:
    with DISCOVERY_LOCK:
        DISCOVERY_STATE['last_query'] = {}
        DISCOVERY_STATE['last_results'] = []
        DISCOVERY_STATE['last_related_terms'] = []
        DISCOVERY_STATE['last_generated_queries'] = []
        DISCOVERY_STATE['last_translated_query'] = ''
        DISCOVERY_STATE['last_warnings'] = []
        DISCOVERY_STATE['last_run_at'] = ''
        DISCOVERY_STATE['last_error'] = ''
        save_discovery_state()
        return export_discovery_state()


def upsert_saved_discovery_query(query_payload: dict[str, object], *, last_run_at: str = '') -> None:
    clean = normalize_discovery_query(query_payload)
    if not clean:
        return
    if last_run_at:
        clean['last_run_at'] = normalize(last_run_at)
    with DISCOVERY_LOCK:
        existing = [item for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') != clean['id']]
        existing.insert(0, clean)
        DISCOVERY_STATE['saved_queries'] = existing[:20]
        save_discovery_state()


def delete_saved_discovery_query(query_id: str) -> dict[str, object]:
    clean_id = normalize(query_id)
    if not clean_id:
        raise ValueError('缺少搜索标识')
    with DISCOVERY_LOCK:
        DISCOVERY_STATE['saved_queries'] = [item for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') != clean_id]
        save_discovery_state()
        return export_discovery_state()


DISCOVERY_JOB_STAGE_LABELS = {
    'queued': '等待开始',
    'initial_search': '首轮搜索中',
    'initial_results': '首轮结果已返回',
    'seed_details': '正在补全详情',
    'expansion_search': '正在扩展相关词',
    'rescoring': '正在综合重排',
    'completed': '已完成',
    'failed': '执行失败',
    'cancelled': '已取消',
}

DISCOVERY_JOB_STAGE_PROGRESS = {
    'queued': 0.02,
    'initial_search': 0.16,
    'initial_results': 0.38,
    'seed_details': 0.52,
    'expansion_search': 0.74,
    'rescoring': 0.9,
    'completed': 1.0,
    'failed': 1.0,
    'cancelled': 1.0,
}

DISCOVERY_JOB_TERMINAL = {'completed', 'failed', 'cancelled'}


def discovery_warning_list(items: object, *, limit: int = 8) -> list[str]:
    if not isinstance(items, list):
        return []
    return list(dict.fromkeys(normalize(item) for item in items if normalize(item)))[:limit]


def estimate_discovery_eta(query_payload: dict[str, object]) -> tuple[int, int]:
    limit = clamp_int(query_payload.get('limit'), 20, 5, 50)
    has_token = bool(normalize(SETTINGS.get('github_token', '')))
    auto_expand = as_bool(query_payload.get('auto_expand'), True)
    language = normalize(query_payload.get('language'))
    size_penalty = min(6, max(0, (limit - 5) // 10) * 2)
    initial_seconds = 14 + size_penalty
    if language:
        initial_seconds += 1
    if not has_token:
        initial_seconds += 2
    full_seconds = initial_seconds + (10 if auto_expand else 6) + (4 if has_token else 5) + size_penalty
    return initial_seconds, max(initial_seconds + 2, full_seconds)


def build_discovery_job_message(stage: str, query_payload: dict[str, object], payload: dict[str, object] | None = None) -> str:
    query = normalize(query_payload.get('query')) or '当前关键词'
    payload = payload if isinstance(payload, dict) else {}
    result_count = len(payload.get('results', [])) if isinstance(payload.get('results'), list) else 0
    if stage == 'initial_search':
        return f'正在为“{query}”执行首轮 GitHub 搜索'
    if stage == 'initial_results':
        return f'首轮结果已返回 {result_count} 个候选，正在继续补全与扩词'
    if stage == 'seed_details':
        return f'正在为“{query}”补全首批仓库详情'
    if stage == 'expansion_search':
        return f'正在扩展相关词并补充更多候选仓库'
    if stage == 'rescoring':
        return f'正在对“{query}”执行综合打分与重排'
    if stage == 'completed':
        return f'关键词发现已完成，共返回 {result_count} 个结果'
    if stage == 'cancelled':
        return '关键词发现已取消'
    if stage == 'failed':
        return normalize(payload.get('error')) or '关键词发现失败'
    return '正在准备关键词发现任务'


def build_discovery_job_snapshot(job: dict[str, object]) -> dict[str, object]:
    started_ts = float(job.get('_started_ts') or 0.0)
    finished_ts = float(job.get('_finished_ts') or 0.0)
    now_ts = finished_ts or time.time()
    elapsed_seconds = max(0, int(round(now_ts - started_ts))) if started_ts else 0
    eta_initial_seconds = clamp_int(job.get('eta_initial_seconds'), 4, 1, 300)
    eta_full_seconds = clamp_int(job.get('eta_full_seconds'), eta_initial_seconds + 2, eta_initial_seconds, 600)
    preview_results = [clean for item in job.get('preview_results', []) if (clean := normalize_repo(item))]
    status = normalize(job.get('status')) or 'queued'
    target_seconds = eta_initial_seconds if not preview_results and status not in DISCOVERY_JOB_TERMINAL else eta_full_seconds
    eta_remaining_seconds = 0 if status in DISCOVERY_JOB_TERMINAL else max(1, target_seconds - elapsed_seconds)
    return {
        'id': normalize(job.get('id')),
        'status': status,
        'stage': normalize(job.get('stage')) or 'queued',
        'stage_label': normalize(job.get('stage_label')) or DISCOVERY_JOB_STAGE_LABELS.get(normalize(job.get('stage')) or 'queued', '处理中'),
        'message': normalize(job.get('message')),
        'query': normalize_discovery_query(job.get('query')) or {},
        'save_query': as_bool(job.get('save_query'), False),
        'cancel_requested': as_bool(job.get('cancel_requested'), False),
        'created_at': normalize(job.get('created_at')),
        'started_at': normalize(job.get('started_at')),
        'finished_at': normalize(job.get('finished_at')),
        'elapsed_seconds': elapsed_seconds,
        'eta_initial_seconds': eta_initial_seconds,
        'eta_full_seconds': eta_full_seconds,
        'eta_remaining_seconds': eta_remaining_seconds,
        'progress': max(0.0, min(1.0, float(job.get('progress') or 0.0))),
        'progress_percent': max(0, min(100, int(round(float(job.get('progress') or 0.0) * 100)))),
        'translated_query': normalize(job.get('translated_query')),
        'generated_queries': [normalize(item) for item in job.get('generated_queries', []) if normalize(item)][:12] if isinstance(job.get('generated_queries'), list) else [],
        'related_terms': [normalize(item) for item in job.get('related_terms', []) if normalize(item)][:12] if isinstance(job.get('related_terms'), list) else [],
        'warnings': discovery_warning_list(job.get('warnings'), limit=8),
        'preview_results': preview_results[:50],
        'error': normalize(job.get('error')),
        'discovery_state': job.get('discovery_state') if isinstance(job.get('discovery_state'), dict) else None,
    }


def export_active_discovery_job() -> dict[str, object] | None:
    with DISCOVERY_JOB_LOCK:
        active_id = normalize(ACTIVE_DISCOVERY_JOB_ID)
        job = DISCOVERY_JOBS.get(active_id) if active_id else None
        if not isinstance(job, dict):
            return None
        return build_discovery_job_snapshot(job)


def update_discovery_job(job_id: str, **changes) -> dict[str, object] | None:
    global ACTIVE_DISCOVERY_JOB_ID
    clean_id = normalize(job_id)
    if not clean_id:
        return None
    with DISCOVERY_JOB_LOCK:
        job = DISCOVERY_JOBS.get(clean_id)
        if not isinstance(job, dict):
            return None
        if 'status' in changes and normalize(changes.get('status')) == 'running' and not normalize(job.get('started_at')):
            job['started_at'] = iso_now()
            job['_started_ts'] = time.time()
        if 'stage' in changes:
            stage = normalize(changes.get('stage')) or job.get('stage') or 'queued'
            job['stage'] = stage
            job['stage_label'] = DISCOVERY_JOB_STAGE_LABELS.get(stage, stage)
            job['progress'] = DISCOVERY_JOB_STAGE_PROGRESS.get(stage, job.get('progress', 0.0))
        for key in ('status', 'message', 'translated_query', 'error'):
            if key in changes and changes.get(key) is not None:
                job[key] = normalize(changes.get(key))
        for key in ('generated_queries', 'related_terms'):
            if key in changes and changes.get(key) is not None:
                job[key] = [normalize(item) for item in changes.get(key, []) if normalize(item)][:12]
        if 'warnings' in changes and changes.get('warnings') is not None:
            existing = discovery_warning_list(job.get('warnings'), limit=8)
            incoming = discovery_warning_list(changes.get('warnings'), limit=8)
            job['warnings'] = list(dict.fromkeys([*existing, *incoming]))[:8]
        if 'preview_results' in changes and changes.get('preview_results') is not None:
            job['preview_results'] = [clean for item in changes.get('preview_results', []) if (clean := normalize_repo(item))][:50]
        if 'discovery_state' in changes and isinstance(changes.get('discovery_state'), dict):
            job['discovery_state'] = changes.get('discovery_state')
        if 'cancel_requested' in changes:
            job['cancel_requested'] = as_bool(changes.get('cancel_requested'), False)
        status = normalize(job.get('status')) or 'queued'
        if status not in DISCOVERY_JOB_TERMINAL:
            ACTIVE_DISCOVERY_JOB_ID = clean_id
        else:
            job['finished_at'] = normalize(job.get('finished_at')) or iso_now()
            job['_finished_ts'] = float(job.get('_finished_ts') or time.time())
            if ACTIVE_DISCOVERY_JOB_ID == clean_id:
                ACTIVE_DISCOVERY_JOB_ID = ''
        snapshot = build_discovery_job_snapshot(job)
        stale_ids = [
            key for key, value in DISCOVERY_JOBS.items()
            if key != ACTIVE_DISCOVERY_JOB_ID and normalize(value.get('status')) in DISCOVERY_JOB_TERMINAL
        ]
        for stale_id in stale_ids[:-10]:
            DISCOVERY_JOBS.pop(stale_id, None)
        return snapshot


def apply_discovery_result(query_payload: dict[str, object], discovery: dict[str, object], *, save_query: bool) -> dict[str, object]:
    results = [clean for item in discovery.get('results', []) if (clean := normalize_repo(item))]
    last_run_at = normalize(discovery.get('run_at')) or iso_now()
    warnings = discovery_warning_list(discovery.get('warnings'), limit=8)
    with DISCOVERY_LOCK:
        DISCOVERY_STATE['last_query'] = query_payload
        DISCOVERY_STATE['last_results'] = results
        DISCOVERY_STATE['last_related_terms'] = [normalize(item) for item in discovery.get('related_terms', []) if normalize(item)][:12]
        DISCOVERY_STATE['last_generated_queries'] = [normalize(item) for item in discovery.get('generated_queries', []) if normalize(item)][:12]
        DISCOVERY_STATE['last_translated_query'] = normalize(discovery.get('translated_query'))
        DISCOVERY_STATE['last_warnings'] = warnings
        DISCOVERY_STATE['last_run_at'] = last_run_at
        DISCOVERY_STATE['last_error'] = ''
        if save_query:
            saved_queries = [item for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') != query_payload['id']]
            saved_query = dict(query_payload)
            saved_query['last_run_at'] = last_run_at
            saved_queries.insert(0, saved_query)
            DISCOVERY_STATE['saved_queries'] = saved_queries[:20]
        elif query_payload['id'] in {item.get('id') for item in DISCOVERY_STATE.get('saved_queries', [])}:
            for item in DISCOVERY_STATE['saved_queries']:
                if item.get('id') == query_payload['id']:
                    item['last_run_at'] = last_run_at
                    break
        save_discovery_state()
        return export_discovery_state()


def run_discovery_search(payload: object) -> dict[str, object]:
    query_payload = normalize_discovery_query(payload)
    if not query_payload:
        raise ValueError('请输入关键词')
    save_query = as_bool(payload.get('save_query') if isinstance(payload, dict) else False, False)
    discovery = github_runtime.discover_repos(
        query=query_payload['query'],
        language=query_payload['language'],
        limit=query_payload['limit'],
        auto_expand=query_payload['auto_expand'],
        ranking_profile=query_payload['ranking_profile'],
    )
    return apply_discovery_result(query_payload, discovery, save_query=save_query)


def run_saved_discovery_query(query_id: str) -> dict[str, object]:
    clean_id = normalize(query_id)
    if not clean_id:
        raise ValueError('缺少搜索标识')
    with DISCOVERY_LOCK:
        query_payload = next((dict(item) for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') == clean_id), None)
    if not query_payload:
        raise ValueError('未找到已保存搜索')
    query_payload['save_query'] = False
    return run_discovery_search(query_payload)


def start_discovery_job(payload: object) -> dict[str, object]:
    global ACTIVE_DISCOVERY_JOB_ID
    query_payload = normalize_discovery_query(payload)
    if not query_payload:
        raise ValueError('请输入关键词')
    save_query = as_bool(payload.get('save_query') if isinstance(payload, dict) else False, False)
    eta_initial_seconds, eta_full_seconds = estimate_discovery_eta(query_payload)
    job_hash = hashlib.sha1(f"{query_payload['id']}-{time.time()}".encode('utf-8')).hexdigest()[:8]
    job_id = f"discover-{int(time.time() * 1000)}-{job_hash}"
    created_at = iso_now()
    with DISCOVERY_JOB_LOCK:
        for other_id, other in DISCOVERY_JOBS.items():
            if other_id == job_id:
                continue
            if normalize(other.get('status')) not in DISCOVERY_JOB_TERMINAL:
                other['cancel_requested'] = True
                other['message'] = '已有新的关键词发现开始，当前任务正在取消'
        DISCOVERY_JOBS[job_id] = {
            'id': job_id,
            'status': 'queued',
            'stage': 'queued',
            'stage_label': DISCOVERY_JOB_STAGE_LABELS['queued'],
            'message': '正在准备关键词发现任务',
            'query': query_payload,
            'save_query': save_query,
            'cancel_requested': False,
            'created_at': created_at,
            'started_at': '',
            'finished_at': '',
            'progress': DISCOVERY_JOB_STAGE_PROGRESS['queued'],
            'eta_initial_seconds': eta_initial_seconds,
            'eta_full_seconds': eta_full_seconds,
            'translated_query': '',
            'generated_queries': [],
            'related_terms': [],
            'warnings': [],
            'preview_results': [],
            'error': '',
            'discovery_state': None,
            '_created_ts': time.time(),
            '_started_ts': 0.0,
            '_finished_ts': 0.0,
        }
        ACTIVE_DISCOVERY_JOB_ID = job_id
        snapshot = build_discovery_job_snapshot(DISCOVERY_JOBS[job_id])

    cancel_error = getattr(github_runtime, 'DiscoveryCancelledError', RuntimeError)

    def worker():
        def is_cancelled() -> bool:
            with DISCOVERY_JOB_LOCK:
                job = DISCOVERY_JOBS.get(job_id, {})
                return as_bool(job.get('cancel_requested'), False)

        def on_progress(stage: str, progress_payload: dict[str, object]) -> None:
            update_discovery_job(
                job_id,
                status='running',
                stage=stage,
                message=build_discovery_job_message(stage, query_payload, progress_payload),
                translated_query=progress_payload.get('translated_query'),
                generated_queries=progress_payload.get('generated_queries'),
                related_terms=progress_payload.get('related_terms'),
                warnings=progress_payload.get('warnings'),
                preview_results=progress_payload.get('results'),
            )

        try:
            update_discovery_job(
                job_id,
                status='running',
                stage='initial_search',
                message=build_discovery_job_message('initial_search', query_payload),
            )
            discovery = github_runtime.discover_repos(
                query=query_payload['query'],
                language=query_payload['language'],
                limit=query_payload['limit'],
                auto_expand=query_payload['auto_expand'],
                ranking_profile=query_payload['ranking_profile'],
                progress_callback=on_progress,
                is_cancelled=is_cancelled,
            )
            if is_cancelled():
                raise cancel_error('关键词发现已取消')
            discovery_state = apply_discovery_result(query_payload, discovery, save_query=save_query)
            update_discovery_job(
                job_id,
                status='completed',
                stage='completed',
                message=build_discovery_job_message('completed', query_payload, {'results': discovery_state.get('last_results', [])}),
                translated_query=discovery.get('translated_query'),
                generated_queries=discovery.get('generated_queries'),
                related_terms=discovery.get('related_terms'),
                warnings=discovery.get('warnings'),
                preview_results=discovery_state.get('last_results'),
                discovery_state=discovery_state,
            )
        except cancel_error:
            update_discovery_job(
                job_id,
                status='cancelled',
                stage='cancelled',
                message=build_discovery_job_message('cancelled', query_payload),
            )
        except Exception as exc:
            update_discovery_job(
                job_id,
                status='failed',
                stage='failed',
                message=build_discovery_job_message('failed', query_payload, {'error': str(exc)}),
                error=str(exc),
            )

    threading.Thread(target=worker, name=f'discovery-job-{job_id}', daemon=True).start()
    return snapshot


def start_saved_discovery_job(query_id: str) -> dict[str, object]:
    clean_id = normalize(query_id)
    if not clean_id:
        raise ValueError('缺少搜索标识')
    with DISCOVERY_LOCK:
        query_payload = next((dict(item) for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') == clean_id), None)
    if not query_payload:
        raise ValueError('未找到已保存搜索')
    query_payload['save_query'] = False
    return start_discovery_job(query_payload)


def get_discovery_job(job_id: str) -> dict[str, object]:
    clean_id = normalize(job_id)
    if not clean_id:
        active = export_active_discovery_job()
        if active:
            return active
        raise ValueError('缺少 discovery job 标识')
    with DISCOVERY_JOB_LOCK:
        job = DISCOVERY_JOBS.get(clean_id)
        if not isinstance(job, dict):
            raise ValueError('未找到对应的 discovery job')
        return build_discovery_job_snapshot(job)


def cancel_discovery_job(job_id: str) -> dict[str, object]:
    clean_id = normalize(job_id)
    if not clean_id:
        raise ValueError('缺少 discovery job 标识')
    with DISCOVERY_JOB_LOCK:
        job = DISCOVERY_JOBS.get(clean_id)
        if not isinstance(job, dict):
            raise ValueError('未找到对应的 discovery job')
        status = normalize(job.get('status'))
        if status in DISCOVERY_JOB_TERMINAL:
            return build_discovery_job_snapshot(job)
        job['cancel_requested'] = True
        job['message'] = '已收到取消请求，当前阶段结束后会停止'
        return build_discovery_job_snapshot(job)


def set_repo_state(state_key: str, enabled: bool, repo: object) -> None:
    if state_key not in {item['key'] for item in STATE_DEFS}:
        raise ValueError('无效状态')
    clean = normalize_repo(repo)
    if not clean:
        raise ValueError('缺少仓库信息')
    url = clean['url']
    with STATE_LOCK:
        USER_STATE['repo_records'][url] = clean
        USER_STATE[state_key] = [item for item in USER_STATE.get(state_key, []) if item != url]
        if enabled:
            USER_STATE[state_key].insert(0, url)
        elif state_key == 'favorites':
            USER_STATE.get('favorite_watch', {}).pop(url, None)
        save_user_state()


def batch_add_favorites(repos: list[dict[str, object]]) -> tuple[int, int]:
    added = 0
    with STATE_LOCK:
        existing = set(USER_STATE.get('favorites', []))
        for repo in repos:
            clean = normalize_repo(repo)
            if not clean:
                continue
            url = clean['url']
            USER_STATE['repo_records'][url] = clean
            if url not in existing:
                USER_STATE['favorites'].insert(0, url)
                existing.add(url)
                added += 1
        save_user_state()
    return len(repos), added


def sync_repo_records(snapshot: dict[str, object]) -> None:
    changed = False
    with STATE_LOCK:
        for period in PERIODS:
            for repo in snapshot.get(period['key'], []):
                clean = normalize_repo(repo)
                if clean and USER_STATE['repo_records'].get(clean['url']) != clean:
                    USER_STATE['repo_records'][clean['url']] = clean
                    changed = True
        if changed:
            save_user_state()


def startup_dir() -> str:
    return os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')


def startup_launcher_path(app_name: str = APP_NAME) -> str:
    return os.path.join(startup_dir(), f'{app_name}.vbs')


def startup_cmd_path(app_name: str = APP_NAME) -> str:
    return os.path.join(startup_dir(), f'{app_name}.cmd')


def startup_launch_command() -> list[str]:
    if getattr(sys, 'frozen', False):
        return [sys.executable]
    executable = sys.executable
    if os.name == 'nt' and os.path.basename(executable).lower() == 'python.exe':
        pythonw = os.path.join(os.path.dirname(executable), 'pythonw.exe')
        if os.path.exists(pythonw):
            executable = pythonw
    return [executable, DEV_ENTRY_SCRIPT]


def vbs_string(value: str) -> str:
    return normalize(value).replace('"', '""')


def startup_launcher_script() -> str:
    command = ' '.join(f'"{part}"' for part in startup_launch_command())
    return (
        'Set shell = CreateObject("WScript.Shell")\r\n'
        f'shell.CurrentDirectory = "{vbs_string(EXEC_DIR)}"\r\n'
        f'shell.Run "{vbs_string(command)}", 0, False\r\n'
    )


def update_auto_start(enabled: bool) -> None:
    path = startup_launcher_path(APP_NAME)
    cleanup_paths = {
        startup_cmd_path(APP_NAME),
        startup_launcher_path(LEGACY_APP_NAME),
        startup_cmd_path(LEGACY_APP_NAME),
    }
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(startup_launcher_script())
        for candidate in cleanup_paths:
            try:
                os.remove(candidate)
            except FileNotFoundError:
                pass
    else:
        for candidate in {path, *cleanup_paths}:
            try:
                os.remove(candidate)
            except FileNotFoundError:
                pass


def empty_snapshot() -> dict[str, object]:
    snapshot = {'fetched_at': iso_now()}
    for period in PERIODS:
        snapshot[period['key']] = []
    return snapshot


def load_snapshot() -> dict[str, object]:
    raw = load_json_file(LATEST_SNAPSHOT_PATH, empty_snapshot())
    if not isinstance(raw, dict):
        return empty_snapshot()
    snapshot = empty_snapshot()
    snapshot['fetched_at'] = normalize(raw.get('fetched_at')) or iso_now()
    for period in PERIODS:
        snapshot[period['key']] = [clean for repo in raw.get(period['key'], []) if (clean := normalize_repo(repo))]
        for repo in snapshot[period['key']]:
            apply_repo_translation(repo)
    return snapshot


def save_snapshot(snapshot: dict[str, object]) -> None:
    atomic_write_json(LATEST_SNAPSHOT_PATH, snapshot)


def current_port() -> int:
    return RUNTIME_PORT or clamp_int(SETTINGS.get('port', 8080), 8080, 1, 65535)


def choose_runtime_port() -> int:
    preferred = clamp_int(SETTINGS.get('port', 8080), 8080, 1, 65535)
    for port in [preferred, *range(preferred + 1, min(preferred + 20, 65535))]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((SERVER_HOST, port))
                return port
            except OSError:
                pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((SERVER_HOST, 0))
        return int(sock.getsockname()[1])


def write_status(refreshing: bool, fetched_at: str = '', source: str = '', error: str = '') -> None:
    atomic_write_json(STATUS_PATH, {'refreshing': refreshing, 'fetched_at': fetched_at, 'source': source, 'error': error, 'updated_at': iso_now()})


def write_runtime_state() -> None:
    pid = int(BROWSER_PROCESS.pid) if BROWSER_PROCESS and BROWSER_PROCESS.poll() is None else 0
    atomic_write_json(RUNTIME_STATE_PATH, {'pid': os.getpid(), 'port': current_port(), 'url': MAIN_URL, 'browser_pid': pid, 'browser_hidden': BROWSER_HIDDEN, 'updated_at': iso_now()})


def get_main_url() -> str:
    return MAIN_URL


def get_browser_process() -> subprocess.Popen | None:
    return BROWSER_PROCESS


def set_browser_process(process: subprocess.Popen | None) -> None:
    global BROWSER_PROCESS
    BROWSER_PROCESS = process


def set_browser_hidden(hidden: bool) -> None:
    global BROWSER_HIDDEN
    BROWSER_HIDDEN = hidden


def clear_runtime_state() -> None:
    try:
        os.remove(RUNTIME_STATE_PATH)
    except FileNotFoundError:
        pass


def acquire_single_instance() -> bool:
    global SINGLE_INSTANCE_MUTEXES
    if os.name != 'nt':
        return True
    handles: list[object] = []
    for slug in dict.fromkeys((APP_SLUG, LEGACY_APP_SLUG)):
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, f'Local\\{slug}Singleton')
        if not mutex:
            continue
        if ctypes.windll.kernel32.GetLastError() == 183:
            ctypes.windll.kernel32.CloseHandle(mutex)
            for handle in handles:
                ctypes.windll.kernel32.CloseHandle(handle)
            return False
        handles.append(mutex)
    SINGLE_INSTANCE_MUTEXES = handles
    return True

def release_single_instance() -> None:
    global SINGLE_INSTANCE_MUTEXES
    for handle in SINGLE_INSTANCE_MUTEXES:
        try:
            ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass
    SINGLE_INSTANCE_MUTEXES = []


def request_existing_instance_open() -> bool:
    for runtime_path in dict.fromkeys((RUNTIME_STATE_PATH, LEGACY_RUNTIME_STATE_PATH)):
        runtime = load_json_file(runtime_path, {})
        if not isinstance(runtime, dict):
            continue
        port = clamp_int(runtime.get('port'), 0, 1, 65535)
        url = normalize(runtime.get('url'))
        for _ in range(8):
            if port:
                try:
                    if LOCAL_CONTROL.post(f'http://{LOCAL_HOST}:{port}/api/window/open', timeout=2).ok:
                        return True
                except Exception:
                    pass
            time.sleep(0.35)
        if url:
            try:
                if os.name == 'nt' and hasattr(os, 'startfile'):
                    os.startfile(url)
                    return True
            except Exception:
                pass
    return False


def show_message_box(message: str) -> None:
    if os.name == 'nt':
        ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x40)


def write_html(snapshot: dict[str, object], note: str, pending: bool) -> None:
    atomic_write_text(HTML_PATH, build_runtime_html(
        app_name=APP_NAME,
        snapshot=snapshot,
        user_state=export_user_state(),
        discovery_state=export_discovery_state(),
        settings=sanitize_settings(False),
        periods=PERIODS,
        states=STATE_DEFS,
        note=note,
        pending=pending,
    ))


def refresh_once_locked(source: str, status_written: bool = False) -> dict[str, object]:
    global CURRENT_SNAPSHOT
    if not status_written:
        write_status(True, str(CURRENT_SNAPSHOT.get('fetched_at', '')), source, '')
    snapshot = github_runtime.fetch_all()
    save_snapshot(snapshot)
    sync_repo_records(snapshot)
    new_update_count = github_runtime.track_favorite_updates()
    CURRENT_SNAPSHOT = snapshot
    write_html(snapshot, '已显示最新数据', False)
    write_status(False, str(snapshot.get('fetched_at', '')), source, '')
    if new_update_count:
        shell_runtime.notify_tray(f'有 {new_update_count} 个收藏仓库发生了变化，请查看「收藏更新」面板。')
    return snapshot


def refresh_once(source: str = 'network') -> dict[str, object]:
    global CURRENT_SNAPSHOT
    if not REFRESH_LOCK.acquire(blocking=False):
        raise RuntimeError('后台正在刷新，请稍后')
    try:
        return refresh_once_locked(source)
    finally:
        REFRESH_LOCK.release()


def refresh_once_safe(source: str = 'network', lock_acquired: bool = False, status_written: bool = False) -> None:
    try:
        if lock_acquired:
            refresh_once_locked(source, status_written=status_written)
        else:
            refresh_once(source)
    except Exception as exc:
        write_status(False, str(CURRENT_SNAPSHOT.get('fetched_at', '')), source, str(exc))
        logger.error('后台刷新失败: %s', exc)
    finally:
        if lock_acquired:
            REFRESH_LOCK.release()


def start_refresh_async(source: str) -> bool:
    if not REFRESH_LOCK.acquire(blocking=False):
        return False
    write_status(True, str(CURRENT_SNAPSHOT.get('fetched_at', '')), source, '')
    try:
        threading.Thread(target=refresh_once_safe, args=(source, True, True), daemon=True).start()
        return True
    except Exception as exc:
        REFRESH_LOCK.release()
        write_status(False, str(CURRENT_SNAPSHOT.get('fetched_at', '')), source, str(exc))
        logger.error('启动后台刷新线程失败: %s', exc)
        return False


shell_runtime = make_shell_runtime(
    app_name=APP_NAME,
    app_slug=APP_SLUG,
    desktop_shell_dir=DESKTOP_SHELL_DIR,
    app_exit_event=APP_EXIT_EVENT,
    browser_lock=BROWSER_LOCK,
    start_refresh_async=start_refresh_async,
    write_runtime_state=write_runtime_state,
    get_main_url=get_main_url,
    get_browser_process=get_browser_process,
    set_browser_process=set_browser_process,
    set_browser_hidden=set_browser_hidden,
    get_close_behavior=lambda: normalize(SETTINGS.get('close_behavior', 'tray')).lower(),
    normalize=normalize,
    quote=quote,
)


github_runtime = make_github_runtime(
    session=SESSION,
    api_timeout=API_TIMEOUT,
    trending_timeout=TRENDING_TIMEOUT,
    search_api_url=SEARCH_API_URL,
    repo_api_url=REPO_API_URL,
    settings=SETTINGS,
    periods=PERIODS,
    state_lock=STATE_LOCK,
    user_state=USER_STATE,
    save_user_state=save_user_state,
    requests_module=requests,
    beautifulsoup_cls=BeautifulSoup,
    thread_pool_executor_cls=ThreadPoolExecutor,
    as_completed=as_completed,
    datetime_cls=datetime,
    timedelta_cls=timedelta,
    normalize=normalize,
    clamp_int=clamp_int,
    extract_count=extract_count,
    normalize_repo=normalize_repo,
    repo_from_url=repo_from_url,
    normalize_watch_entry=normalize_watch_entry,
    normalize_favorite_update=normalize_favorite_update,
    translate_snapshot=translate_snapshot,
    load_snapshot=load_snapshot,
    cached_repo_details=cached_repo_details,
    detail_fetch_lock=detail_fetch_lock,
    strip_markdown=strip_markdown,
    translate_text=translate_text,
    translate_query_to_en=translate_query_to_en,
    save_translation_cache=save_translation_cache,
    save_repo_details=save_repo_details,
    parse_iso_timestamp=parse_iso_timestamp,
    iso_now=iso_now,
    fetch_semaphore=DETAIL_FETCH_SEMAPHORE,
    favorite_watch_min_seconds_no_token=FAVORITE_WATCH_MIN_SECONDS_NO_TOKEN,
    favorite_watch_min_seconds_with_token=FAVORITE_WATCH_MIN_SECONDS_WITH_TOKEN,
    favorite_release_min_seconds_no_token=FAVORITE_RELEASE_MIN_SECONDS_NO_TOKEN,
    favorite_release_min_seconds_with_token=FAVORITE_RELEASE_MIN_SECONDS_WITH_TOKEN,
    favorite_watch_max_checks_no_token=FAVORITE_WATCH_MAX_CHECKS_NO_TOKEN,
    favorite_watch_max_checks_with_token=FAVORITE_WATCH_MAX_CHECKS_WITH_TOKEN,
)


ServerAppHandler = make_app_handler(
    runtime_root=RUNTIME_ROOT,
    status_path=STATUS_PATH,
    settings=SETTINGS,
    settings_lock=SETTINGS_LOCK,
    sanitize_settings=sanitize_settings,
    load_json_file=load_json_file,
    fetch_repo_details=github_runtime.fetch_repo_details,
    normalize=normalize,
    as_bool=as_bool,
    set_repo_state=set_repo_state,
    export_user_state=export_user_state,
    import_user_state=import_user_state,
    normalize_settings=normalize_settings,
    save_settings=save_settings,
    apply_runtime_settings=apply_runtime_settings,
    update_auto_start=update_auto_start,
    clamp_int=clamp_int,
    current_port=current_port,
    start_refresh_async=start_refresh_async,
    open_chatgpt_target=shell_runtime.open_chatgpt_target,
    open_external_url=shell_runtime.open_external_url,
    clear_favorite_updates=github_runtime.clear_favorite_updates,
    run_discovery_search=run_discovery_search,
    run_saved_discovery_query=run_saved_discovery_query,
    start_discovery_job=start_discovery_job,
    start_saved_discovery_job=start_saved_discovery_job,
    get_discovery_job=get_discovery_job,
    cancel_discovery_job=cancel_discovery_job,
    delete_saved_discovery_query=delete_saved_discovery_query,
    clear_discovery_results=clear_discovery_results,
    export_discovery_state=export_discovery_state,
    export_active_discovery_job=export_active_discovery_job,
    star_repo=github_runtime.star_repo,
    fetch_user_starred=github_runtime.fetch_user_starred,
    batch_add_favorites=batch_add_favorites,
    open_main_window=shell_runtime.open_main_window,
    hide_main_window=shell_runtime.hide_main_window,
    exit_app=shell_runtime.exit_app,
)


def refresh_loop(run_immediately: bool = False) -> None:
    if run_immediately:
        logger.info('后台刷新最新数据...')
        refresh_once_safe('startup')
        logger.info('首次后台刷新完成')
    while not APP_EXIT_EVENT.wait(clamp_int(SETTINGS.get('refresh_hours', 1), 1, 1, 24) * 3600):
        logger.info('自动刷新中...')
        refresh_once_safe('auto')


def main() -> None:
    global CURRENT_SNAPSHOT, RUNTIME_PORT, MAIN_URL
    configure_console()
    ensure_runtime_layout()
    if not acquire_single_instance():
        if not request_existing_instance_open():
            show_message_box('GitSonar 已经在运行。请从系统托盘打开主窗口。')
        return
    server = None
    logger.info('=' * 40)
    logger.info('  %s', APP_NAME)
    logger.info('=' * 40)
    try:
        TRANSLATION_CACHE.clear()
        TRANSLATION_CACHE.update(load_translation_cache())
        with DETAIL_CACHE_LOCK:
            DETAIL_CACHE.clear()
            DETAIL_CACHE.update(load_detail_cache())
        SETTINGS.clear()
        SETTINGS.update(load_settings())
        apply_runtime_settings()
        update_auto_start(bool(SETTINGS.get('auto_start')))
        USER_STATE.clear()
        USER_STATE.update(load_user_state())
        DISCOVERY_STATE.clear()
        DISCOVERY_STATE.update(load_discovery_state())
        RUNTIME_PORT = choose_runtime_port()
        CURRENT_SNAPSHOT = load_snapshot()
        sync_repo_records(CURRENT_SNAPSHOT)
        has_cache = any(CURRENT_SNAPSHOT.get(p['key']) for p in PERIODS)
        note = '已加载本地缓存，后台刷新中...' if has_cache else '首次启动，正在后台抓取数据...'
        write_html(CURRENT_SNAPSHOT, note, True)
        write_status(True, str(CURRENT_SNAPSHOT.get('fetched_at', '')), 'cache', '')
        server = ThreadingHTTPServer((SERVER_HOST, current_port()), ServerAppHandler)
        MAIN_URL = f'http://{LOCAL_HOST}:{current_port()}/trending.html?v={int(time.time())}'
        write_runtime_state()
        logger.info('本机访问: %s', MAIN_URL)
        logger.info('每 %s 小时自动更新一次', SETTINGS.get('refresh_hours', 1))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        threading.Thread(target=refresh_loop, kwargs={'run_immediately': True}, daemon=True).start()
        shell_runtime.open_main_window()
        shell_runtime.run_tray_loop()
    finally:
        APP_EXIT_EVENT.set()
        shell_runtime.close_main_window()
        clear_runtime_state()
        release_single_instance()
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
