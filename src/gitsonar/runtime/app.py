
#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import hashlib
import logging
import os
import re
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from ..runtime_github import make_github_runtime
from ..runtime_ui import build_html as build_runtime_html
from .http import make_app_handler
from .paths import (
    APP_NAME,
    APP_SLUG,
    CACHE_PATH,
    DATA_DIR,
    DESKTOP_SHELL_DIR,
    DETAIL_CACHE_PATH,
    DEV_ENTRY_SCRIPT,
    DISCOVERY_STATE_PATH,
    EXEC_DIR,
    HTML_PATH,
    LEGACY_APP_NAME,
    LEGACY_APP_SLUG,
    LEGACY_RUNTIME_STATE_PATH,
    LATEST_SNAPSHOT_PATH,
    LOCAL_HOST,
    RUNTIME_ROOT,
    RUNTIME_STATE_PATH,
    SERVER_HOST,
    SETTINGS_PATH,
    STATUS_PATH,
    USER_STATE_PATH,
)
from .settings import DEFAULT_SETTINGS, make_settings_runtime
from .shell import make_shell_runtime
from .startup import make_startup_runtime
from .state import make_state_runtime
from .translation import make_translation_runtime
from .utils import (
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
RUNTIME_PORT: int | None = None
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


translation_runtime = make_translation_runtime(
    cache_path=CACHE_PATH,
    translation_cache=TRANSLATION_CACHE,
    translation_lock=TRANSLATION_LOCK,
    translate_session=TRANSLATE_SESSION,
    normalize=normalize,
    load_json_file=load_json_file,
    atomic_write_json=atomic_write_json,
    translate_timeout=TRANSLATE_TIMEOUT,
    translate_retries=TRANSLATE_RETRIES,
    max_translation_cache_size=_MAX_TRANSLATION_CACHE_SIZE,
    han_re=HAN_RE,
    thread_pool_executor_cls=ThreadPoolExecutor,
    as_completed=as_completed,
    periods=PERIODS,
)
load_translation_cache = translation_runtime.load_translation_cache
save_translation_cache = translation_runtime.save_translation_cache
has_han = translation_runtime.has_han
translate_text = translation_runtime.translate_text
translate_query_to_en = translation_runtime.translate_query_to_en
apply_repo_translation = translation_runtime.apply_repo_translation
translate_repo_list = translation_runtime.translate_repo_list
translate_snapshot = translation_runtime.translate_snapshot

settings_runtime = make_settings_runtime(
    settings=SETTINGS,
    settings_path=SETTINGS_PATH,
    runtime_root=RUNTIME_ROOT,
    session=SESSION,
    translate_session=TRANSLATE_SESSION,
    current_port_getter=lambda: current_port(),
    runtime_port_getter=lambda: RUNTIME_PORT,
    normalize=normalize,
    clamp_int=clamp_int,
    as_bool=as_bool,
    decrypt_secret=decrypt_secret,
    encrypt_secret=encrypt_secret,
    normalize_proxy_url=normalize_proxy_url,
    parse_proxy_endpoint=parse_proxy_endpoint,
    detect_local_proxy=detect_local_proxy,
    tcp_port_open=tcp_port_open,
    load_json_file=load_json_file,
    atomic_write_json=atomic_write_json,
    default_settings=DEFAULT_SETTINGS,
)
normalize_settings = settings_runtime.normalize_settings
sanitize_settings = settings_runtime.sanitize_settings
save_settings = settings_runtime.save_settings
load_settings = settings_runtime.load_settings
apply_runtime_settings = settings_runtime.apply_runtime_settings

state_runtime = make_state_runtime(
    settings=SETTINGS,
    user_state=USER_STATE,
    discovery_state=DISCOVERY_STATE,
    state_lock=STATE_LOCK,
    discovery_lock=DISCOVERY_LOCK,
    current_snapshot_getter=lambda: CURRENT_SNAPSHOT,
    sync_repo_records_callback=lambda snapshot: sync_repo_records(snapshot),
    user_state_path=USER_STATE_PATH,
    discovery_state_path=DISCOVERY_STATE_PATH,
    latest_snapshot_path=LATEST_SNAPSHOT_PATH,
    periods=PERIODS,
    normalize=normalize,
    clamp_int=clamp_int,
    as_bool=as_bool,
    iso_now=iso_now,
    load_json_file=load_json_file,
    atomic_write_json=atomic_write_json,
    apply_repo_translation=apply_repo_translation,
)
default_user_state = state_runtime.default_user_state
default_discovery_state = state_runtime.default_discovery_state
normalize_discovery_ranking_profile = state_runtime.normalize_discovery_ranking_profile
discovery_query_id = state_runtime.discovery_query_id
normalize_discovery_query = state_runtime.normalize_discovery_query
normalize_repo = state_runtime.normalize_repo
repo_from_url = state_runtime.repo_from_url
normalize_watch_entry = state_runtime.normalize_watch_entry
normalize_favorite_update = state_runtime.normalize_favorite_update
normalize_discovery_state = state_runtime.normalize_discovery_state
normalize_user_state = state_runtime.normalize_user_state
load_user_state = state_runtime.load_user_state
save_user_state = state_runtime.save_user_state
export_user_state = state_runtime.export_user_state
import_user_state = state_runtime.import_user_state
load_discovery_state = state_runtime.load_discovery_state
save_discovery_state = state_runtime.save_discovery_state
export_discovery_state = state_runtime.export_discovery_state
clear_discovery_results = state_runtime.clear_discovery_results
upsert_saved_discovery_query = state_runtime.upsert_saved_discovery_query
delete_saved_discovery_query = state_runtime.delete_saved_discovery_query
discovery_warning_list = state_runtime.discovery_warning_list
empty_snapshot = state_runtime.empty_snapshot
load_snapshot = state_runtime.load_snapshot
save_snapshot = state_runtime.save_snapshot
state_counts = state_runtime.state_counts
ordered_unique_urls = state_runtime.ordered_unique_urls
merge_favorite_updates = state_runtime.merge_favorite_updates

startup_runtime = make_startup_runtime(
    app_name=APP_NAME,
    app_slug=APP_SLUG,
    legacy_app_name=LEGACY_APP_NAME,
    legacy_app_slug=LEGACY_APP_SLUG,
    dev_entry_script=DEV_ENTRY_SCRIPT,
    exec_dir=EXEC_DIR,
    runtime_state_path=RUNTIME_STATE_PATH,
    legacy_runtime_state_path=LEGACY_RUNTIME_STATE_PATH,
    local_host=LOCAL_HOST,
    local_control=LOCAL_CONTROL,
    normalize=normalize,
    clamp_int=clamp_int,
    iso_now=iso_now,
    load_json_file=load_json_file,
    atomic_write_json=atomic_write_json,
    current_port_getter=lambda: current_port(),
)
startup_dir = startup_runtime.startup_dir
startup_launcher_path = startup_runtime.startup_launcher_path
startup_cmd_path = startup_runtime.startup_cmd_path
startup_launch_command = startup_runtime.startup_launch_command
startup_launcher_script = startup_runtime.startup_launcher_script
update_auto_start = startup_runtime.update_auto_start
write_runtime_state = startup_runtime.write_runtime_state
get_main_url = startup_runtime.get_main_url
get_browser_process = startup_runtime.get_browser_process
set_browser_process = startup_runtime.set_browser_process
set_browser_hidden = startup_runtime.set_browser_hidden
clear_runtime_state = startup_runtime.clear_runtime_state
acquire_single_instance = startup_runtime.acquire_single_instance
release_single_instance = startup_runtime.release_single_instance
request_existing_instance_open = startup_runtime.request_existing_instance_open
show_message_box = startup_runtime.show_message_box
set_main_url = startup_runtime.set_main_url


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
    if normalize(SETTINGS.get('github_token', '')):
        try:
            github_runtime.sync_local_favorites_with_starred(github_runtime.fetch_user_starred())
        except Exception as exc:
            logger.warning('同步 GitHub 星标到本地关注失败: %s', exc)
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
    start_discovery_job=start_discovery_job,
    start_saved_discovery_job=start_saved_discovery_job,
    get_discovery_job=get_discovery_job,
    cancel_discovery_job=cancel_discovery_job,
    delete_saved_discovery_query=delete_saved_discovery_query,
    clear_discovery_results=clear_discovery_results,
    export_discovery_state=export_discovery_state,
    export_active_discovery_job=export_active_discovery_job,
    sync_favorite_repo=github_runtime.sync_favorite_repo,
    fetch_user_starred=github_runtime.fetch_user_starred,
    sync_local_favorites_with_starred=github_runtime.sync_local_favorites_with_starred,
    validate_github_token=github_runtime.validate_github_token,
    open_main_window=shell_runtime.open_main_window,
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
    global CURRENT_SNAPSHOT, RUNTIME_PORT
    configure_console()
    ensure_runtime_layout()
    if not acquire_single_instance():
        if not request_existing_instance_open():
            show_message_box('GitSonar 已经在运行。')
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
        set_main_url(f'http://{LOCAL_HOST}:{current_port()}/trending.html?v={int(time.time())}')
        write_runtime_state()
        logger.info('本机访问: %s', get_main_url())
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
