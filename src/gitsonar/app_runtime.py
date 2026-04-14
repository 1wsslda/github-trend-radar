
#!/usr/bin/env python3
from __future__ import annotations

import ctypes
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
    {'key': 'favorites', 'label': '收藏夹', 'button': '收藏'},
    {'key': 'watch_later', 'label': '稍后看', 'button': '稍后看'},
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
REFRESH_LOCK = threading.Lock()
TRANSLATION_LOCK = threading.RLock()
DETAIL_CACHE_LOCK = threading.RLock()
SETTINGS: dict[str, object] = {}
USER_STATE: dict[str, object] = {}
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


def normalize_user_state(payload: object) -> dict[str, object]:
    raw = payload if isinstance(payload, dict) else {}
    state = default_user_state()
    for key in ('favorites', 'watch_later', 'read', 'ignored'):
        state[key] = [normalize(item) for item in raw.get(key, []) if normalize(item)]
    records = raw.get('repo_records', {}) if isinstance(raw.get('repo_records'), dict) else {}
    state['repo_records'] = {url: clean for url, repo in records.items() if (clean := normalize_repo(repo))}
    watch = raw.get('favorite_watch', {}) if isinstance(raw.get('favorite_watch'), dict) else {}
    state['favorite_watch'] = {url: clean for url, item in watch.items() if (clean := normalize_watch_entry(item))}
    state['favorite_updates'] = [clean for item in raw.get('favorite_updates', []) if (clean := normalize_favorite_update(item))]
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
