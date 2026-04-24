#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import logging
import os
import re
import secrets
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from ..runtime_github import make_github_runtime
from ..runtime_ui import build_html as build_runtime_html
from .api_boundary import make_api_boundary_runtime
from .diagnostics import make_diagnostics_runtime
from .detail_cache import make_detail_cache_runtime
from .discovery_jobs import make_discovery_job_runtime
from .http import make_app_handler
from .jobs import make_job_event_runtime
from .paths import (
    APP_NAME,
    APP_SLUG,
    DEFAULT_RUNTIME_PATHS,
    DEV_ENTRY_SCRIPT,
    EXEC_DIR,
    LEGACY_APP_NAME,
    LEGACY_APP_SLUG,
    LOCAL_HOST,
    SERVER_HOST,
    RuntimePaths,
    ensure_runtime_paths,
)
from .redaction import SAFE_REFRESH_ERROR, redact_text
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
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SEARCH_API_URL = "https://api.github.com/search/repositories"
REPO_API_URL = "https://api.github.com/repos"
API_TIMEOUT = (5, 12)
TRENDING_TIMEOUT = (4, 10)
TRANSLATE_TIMEOUT = (4, 8)
TRANSLATE_RETRIES = 2
DETAIL_CACHE_SECONDS = 6 * 3600
_MAX_TRANSLATION_CACHE_SIZE = 5000
_MAX_DETAIL_CACHE_SIZE = 500
_MAX_DETAIL_FETCH_LOCKS = 1000
FAVORITE_WATCH_MIN_SECONDS_NO_TOKEN = 6 * 3600
FAVORITE_WATCH_MIN_SECONDS_WITH_TOKEN = 3600
FAVORITE_RELEASE_MIN_SECONDS_NO_TOKEN = 24 * 3600
FAVORITE_RELEASE_MIN_SECONDS_WITH_TOKEN = 6 * 3600
FAVORITE_WATCH_MAX_CHECKS_NO_TOKEN = 6
FAVORITE_WATCH_MAX_CHECKS_WITH_TOKEN = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

PERIODS = [
    {"key": "daily", "label": "今天", "days": 1},
    {"key": "weekly", "label": "本周", "days": 7},
    {"key": "monthly", "label": "本月", "days": 30},
]

STATE_DEFS = [
    {"key": "favorites", "label": "关注", "button": "关注"},
    {"key": "watch_later", "label": "待看", "button": "待看"},
    {"key": "read", "label": "已读", "button": "已读"},
    {"key": "ignored", "label": "忽略", "button": "忽略"},
]

HAN_RE = re.compile(r"[\u3400-\u9fff]")

@dataclass(slots=True)
class RuntimeAppContext:
    paths: RuntimePaths
    session: requests.Session
    local_control: requests.Session
    translate_session: requests.Session
    settings_lock: threading.RLock
    state_lock: threading.RLock
    discovery_lock: threading.RLock
    discovery_job_lock: threading.RLock
    refresh_lock: threading.Lock
    translation_lock: threading.RLock
    detail_cache_lock: threading.RLock
    settings: dict[str, object]
    user_state: dict[str, object]
    discovery_state: dict[str, object]
    current_snapshot: dict[str, object]
    app_exit_event: threading.Event
    browser_lock: threading.RLock
    detail_fetch_semaphore: threading.Semaphore
    translation_cache: dict[str, str]
    detail_cache: dict[str, object]
    detail_fetch_locks: dict[str, threading.Lock]
    detail_cache_dirty: bool = False


_RUNTIME_CONTEXT: RuntimeAppContext | None = None

SESSION: requests.Session | None = None
LOCAL_CONTROL: requests.Session | None = None
TRANSLATE_SESSION: requests.Session | None = None

SETTINGS_LOCK: threading.RLock | None = None
STATE_LOCK: threading.RLock | None = None
DISCOVERY_LOCK: threading.RLock | None = None
DISCOVERY_JOB_LOCK: threading.RLock | None = None
REFRESH_LOCK: threading.Lock | None = None
TRANSLATION_LOCK: threading.RLock | None = None
DETAIL_CACHE_LOCK: threading.RLock | None = None

SETTINGS: dict[str, object] = {}
USER_STATE: dict[str, object] = {}
DISCOVERY_STATE: dict[str, object] = {}
CURRENT_SNAPSHOT: dict[str, object] = {}
RUNTIME_PORT: int | None = None
CONTROL_TOKEN = ""
AUTO_SYNC_USER_STARS_DONE = False

APP_EXIT_EVENT: threading.Event | None = None
BROWSER_LOCK: threading.RLock | None = None
DETAIL_FETCH_SEMAPHORE: threading.Semaphore | None = None
TRANSLATION_CACHE: dict[str, str] = {}
DETAIL_CACHE: dict[str, object] = {}
DETAIL_FETCH_LOCKS: dict[str, threading.Lock] = {}
DETAIL_CACHE_DIRTY = False

translation_runtime = None
settings_runtime = None
state_runtime = None
startup_runtime = None
shell_runtime = None
github_runtime = None
discovery_job_runtime = None
diagnostics_runtime = None
api_boundary_runtime = None
job_event_runtime = None
ServerAppHandler = None

load_translation_cache = None
save_translation_cache = None
flush_translation_cache = None
translate_text = None
translate_query_to_en = None
apply_repo_translation = None
translate_snapshot = None

normalize_settings = None
sanitize_settings = None
save_settings = None
load_settings = None
merge_settings = None
apply_runtime_settings = None

default_user_state = None
default_discovery_state = None
normalize_discovery_ranking_profile = None
discovery_query_id = None
normalize_discovery_query = None
normalize_repo = None
repo_from_url = None
normalize_watch_entry = None
normalize_favorite_update = None
normalize_discovery_state = None
normalize_user_state = None
load_user_state = None
save_user_state = None
set_repo_state_batch = None
set_repo_annotation = None
set_favorite_update_state = None
export_user_state = None
set_ai_insight = None
delete_ai_insight = None
list_ai_artifacts = None
import_user_state = None
load_discovery_state = None
save_discovery_state = None
export_discovery_state = None
save_discovery_view = None
delete_discovery_view = None
clear_discovery_results = None
apply_discovery_result = None
discovery_warning_list = None
empty_snapshot = None
load_snapshot = None
save_snapshot = None
state_counts = None
ordered_unique_urls = None
merge_favorite_updates = None

startup_dir = None
startup_launcher_path = None
startup_cmd_path = None
startup_launch_command = None
startup_launcher_script = None
update_auto_start = None
write_runtime_state = None
get_main_url = None
get_browser_process = None
set_browser_process = None
set_browser_hidden = None
clear_runtime_state = None
acquire_single_instance = None
release_single_instance = None
request_existing_instance_open = None
show_message_box = None
set_main_url = None

estimate_discovery_eta = None
update_discovery_job = None
run_discovery_search = None
start_discovery_job = None
get_discovery_job = None
cancel_discovery_job = None
export_active_discovery_job = None
run_diagnostics = None

if os.name == "nt":
    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),
            ("szExeFile", ctypes.c_wchar * 260),
        ]


def runtime_paths() -> RuntimePaths:
    context = _RUNTIME_CONTEXT
    return context.paths if context is not None else DEFAULT_RUNTIME_PATHS


def _new_session(*, trust_env: bool = True, with_headers: bool = True) -> requests.Session:
    session = requests.Session()
    session.trust_env = trust_env
    if with_headers:
        session.headers.update(HEADERS)
    return session


def _install_runtime_context(context: RuntimeAppContext) -> None:
    global _RUNTIME_CONTEXT
    global SESSION, LOCAL_CONTROL, TRANSLATE_SESSION
    global SETTINGS_LOCK, STATE_LOCK, DISCOVERY_LOCK, DISCOVERY_JOB_LOCK, REFRESH_LOCK, TRANSLATION_LOCK, DETAIL_CACHE_LOCK
    global SETTINGS, USER_STATE, DISCOVERY_STATE, CURRENT_SNAPSHOT
    global APP_EXIT_EVENT, BROWSER_LOCK, DETAIL_FETCH_SEMAPHORE, TRANSLATION_CACHE, DETAIL_CACHE, DETAIL_FETCH_LOCKS
    global DETAIL_CACHE_DIRTY

    _RUNTIME_CONTEXT = context
    SESSION = context.session
    LOCAL_CONTROL = context.local_control
    TRANSLATE_SESSION = context.translate_session
    SETTINGS_LOCK = context.settings_lock
    STATE_LOCK = context.state_lock
    DISCOVERY_LOCK = context.discovery_lock
    DISCOVERY_JOB_LOCK = context.discovery_job_lock
    REFRESH_LOCK = context.refresh_lock
    TRANSLATION_LOCK = context.translation_lock
    DETAIL_CACHE_LOCK = context.detail_cache_lock
    SETTINGS = context.settings
    USER_STATE = context.user_state
    DISCOVERY_STATE = context.discovery_state
    CURRENT_SNAPSHOT = context.current_snapshot
    APP_EXIT_EVENT = context.app_exit_event
    BROWSER_LOCK = context.browser_lock
    DETAIL_FETCH_SEMAPHORE = context.detail_fetch_semaphore
    TRANSLATION_CACHE = context.translation_cache
    DETAIL_CACHE = context.detail_cache
    DETAIL_FETCH_LOCKS = context.detail_fetch_locks
    DETAIL_CACHE_DIRTY = bool(context.detail_cache_dirty)


def ensure_runtime_layout() -> None:
    paths = runtime_paths()
    os.makedirs(paths.runtime_root, exist_ok=True)
    os.makedirs(paths.data_dir, exist_ok=True)


def configure_console() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    hide_console_window_if_needed()


def parent_process_name() -> str:
    if os.name != "nt":
        return ""
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if snapshot == invalid_handle:
        return ""
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return ""
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
    if os.name != "nt":
        return
    for slug in {APP_SLUG, LEGACY_APP_SLUG}:
        if normalize(os.environ.get(f"{slug.upper()}_SHOW_CONSOLE")).lower() in {"1", "true", "yes"}:
            return
    try:
        kernel32 = ctypes.windll.kernel32
        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return
        if parent_process_name() not in {"explorer.exe", "wscript.exe", "cscript.exe"}:
            return
        ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def _get_detail_cache_dirty() -> bool:
    return bool(DETAIL_CACHE_DIRTY)


def _set_detail_cache_dirty(value: bool) -> None:
    global DETAIL_CACHE_DIRTY
    DETAIL_CACHE_DIRTY = bool(value)


def _build_detail_cache_runtime():
    return make_detail_cache_runtime(
        cache_path=runtime_paths().detail_cache_path,
        detail_cache=DETAIL_CACHE,
        detail_cache_lock=DETAIL_CACHE_LOCK,
        detail_fetch_locks=DETAIL_FETCH_LOCKS,
        load_json_file=load_json_file,
        atomic_write_json=atomic_write_json,
        clamp_int=clamp_int,
        detail_cache_seconds=DETAIL_CACHE_SECONDS,
        max_detail_cache_size=_MAX_DETAIL_CACHE_SIZE,
        max_detail_fetch_locks=_MAX_DETAIL_FETCH_LOCKS,
        dirty=DETAIL_CACHE_DIRTY,
        dirty_getter=_get_detail_cache_dirty,
        dirty_setter=_set_detail_cache_dirty,
    )


def _get_detail_cache_runtime():
    return _build_detail_cache_runtime()


def load_detail_cache() -> dict[str, object]:
    return _get_detail_cache_runtime().load_detail_cache()


def cached_repo_details(cache_key: str) -> dict[str, object] | None:
    return _get_detail_cache_runtime().cached_repo_details(cache_key)


def detail_fetch_lock(cache_key: str) -> threading.Lock:
    return _get_detail_cache_runtime().detail_fetch_lock(cache_key)


def save_repo_details(cache_key: str, details: dict[str, object]) -> None:
    _get_detail_cache_runtime().save_repo_details(cache_key, details)


def flush_repo_details_cache() -> bool:
    return _get_detail_cache_runtime().flush_repo_details_cache()


def current_port() -> int:
    return RUNTIME_PORT or clamp_int(SETTINGS.get("port", 8080), 8080, 1, 65535)

def build_runtime_context(*, rebuild: bool = False) -> RuntimeAppContext:
    global translation_runtime, settings_runtime, state_runtime, startup_runtime
    global shell_runtime, github_runtime, discovery_job_runtime, diagnostics_runtime, api_boundary_runtime, job_event_runtime, ServerAppHandler
    global load_translation_cache, save_translation_cache, flush_translation_cache, translate_text, translate_query_to_en, apply_repo_translation, translate_snapshot
    global normalize_settings, sanitize_settings, save_settings, load_settings, merge_settings, apply_runtime_settings
    global default_user_state, default_discovery_state, normalize_discovery_ranking_profile, discovery_query_id, normalize_discovery_query
    global normalize_repo, repo_from_url, normalize_watch_entry, normalize_favorite_update, normalize_discovery_state, normalize_user_state
    global load_user_state, save_user_state, set_repo_state_batch, set_repo_annotation, set_favorite_update_state
    global export_user_state, set_ai_insight, delete_ai_insight, list_ai_artifacts, import_user_state, load_discovery_state, save_discovery_state
    global export_discovery_state, save_discovery_view, delete_discovery_view, clear_discovery_results, apply_discovery_result, discovery_warning_list, empty_snapshot, load_snapshot
    global save_snapshot, state_counts, ordered_unique_urls, merge_favorite_updates
    global startup_dir, startup_launcher_path, startup_cmd_path, startup_launch_command, startup_launcher_script
    global update_auto_start, write_runtime_state, get_main_url, get_browser_process, set_browser_process, set_browser_hidden
    global clear_runtime_state, acquire_single_instance, release_single_instance, request_existing_instance_open, show_message_box, set_main_url
    global estimate_discovery_eta, update_discovery_job, run_discovery_search, start_discovery_job, get_discovery_job, cancel_discovery_job
    global export_active_discovery_job, run_diagnostics

    if _RUNTIME_CONTEXT is not None and not rebuild:
        return _RUNTIME_CONTEXT
    if rebuild:
        translation_runtime = None
        settings_runtime = None
        state_runtime = None
        startup_runtime = None
        shell_runtime = None
        github_runtime = None
        discovery_job_runtime = None
        diagnostics_runtime = None
        api_boundary_runtime = None
        job_event_runtime = None
        ServerAppHandler = None

    paths = ensure_runtime_paths()
    context = RuntimeAppContext(
        paths=paths,
        session=_new_session(),
        local_control=_new_session(trust_env=False, with_headers=False),
        translate_session=_new_session(trust_env=False),
        settings_lock=threading.RLock(),
        state_lock=threading.RLock(),
        discovery_lock=threading.RLock(),
        discovery_job_lock=threading.RLock(),
        refresh_lock=threading.Lock(),
        translation_lock=threading.RLock(),
        detail_cache_lock=threading.RLock(),
        settings={},
        user_state={},
        discovery_state={},
        current_snapshot={},
        app_exit_event=threading.Event(),
        browser_lock=threading.RLock(),
        detail_fetch_semaphore=threading.Semaphore(3),
        translation_cache={},
        detail_cache={},
        detail_fetch_locks={},
        detail_cache_dirty=False,
    )
    _install_runtime_context(context)

    translation_runtime = make_translation_runtime(
        cache_path=paths.cache_path,
        translation_cache=TRANSLATION_CACHE,
        translation_lock=TRANSLATION_LOCK,
        translate_session=TRANSLATE_SESSION,
        settings=SETTINGS,
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
    flush_translation_cache = translation_runtime.flush_translation_cache
    translate_text = translation_runtime.translate_text
    translate_query_to_en = translation_runtime.translate_query_to_en
    apply_repo_translation = translation_runtime.apply_repo_translation
    translate_snapshot = translation_runtime.translate_snapshot

    settings_runtime = make_settings_runtime(
        settings=SETTINGS,
        settings_path=paths.settings_path,
        runtime_root=paths.runtime_root,
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
    merge_settings = settings_runtime.merge_settings
    apply_runtime_settings = settings_runtime.apply_runtime_settings

    state_runtime = make_state_runtime(
        settings=SETTINGS,
        user_state=USER_STATE,
        discovery_state=DISCOVERY_STATE,
        state_lock=STATE_LOCK,
        discovery_lock=DISCOVERY_LOCK,
        current_snapshot_getter=lambda: CURRENT_SNAPSHOT,
        sync_repo_records_callback=lambda snapshot: sync_repo_records(snapshot),
        user_state_path=paths.user_state_path,
        discovery_state_path=paths.discovery_state_path,
        latest_snapshot_path=paths.latest_snapshot_path,
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
    set_repo_state_batch = state_runtime.set_repo_state_batch
    set_repo_annotation = state_runtime.set_repo_annotation
    set_favorite_update_state = state_runtime.set_favorite_update_state
    export_user_state = state_runtime.export_user_state
    set_ai_insight = state_runtime.set_ai_insight
    delete_ai_insight = state_runtime.delete_ai_insight
    list_ai_artifacts = state_runtime.list_ai_artifacts
    import_user_state = state_runtime.import_user_state
    load_discovery_state = state_runtime.load_discovery_state
    save_discovery_state = state_runtime.save_discovery_state
    export_discovery_state = state_runtime.export_discovery_state
    save_discovery_view = state_runtime.save_discovery_view
    delete_discovery_view = state_runtime.delete_discovery_view
    clear_discovery_results = state_runtime.clear_discovery_results
    apply_discovery_result = state_runtime.apply_discovery_result
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
        runtime_state_path=paths.runtime_state_path,
        legacy_runtime_state_path=paths.legacy_runtime_state_path,
        local_host=LOCAL_HOST,
        local_control=LOCAL_CONTROL,
        normalize=normalize,
        clamp_int=clamp_int,
        iso_now=iso_now,
        load_json_file=load_json_file,
        atomic_write_json=atomic_write_json,
        current_port_getter=lambda: current_port(),
        control_token_getter=lambda: CONTROL_TOKEN,
        parse_iso_timestamp=parse_iso_timestamp,
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
    _build_runtime_services()
    return context


def set_repo_state(state_key: str, enabled: bool, repo: object) -> None:
    if state_runtime is None:
        raise RuntimeError("state runtime not initialized")
    state_runtime.set_repo_state(state_key, enabled, repo)


def set_repo_state_batch(state_key: str, enabled: bool, repos: object) -> list[dict[str, object]]:
    if state_runtime is None:
        raise RuntimeError("state runtime not initialized")
    return state_runtime.set_repo_state_batch(state_key, enabled, repos)


def sync_repo_records(snapshot: dict[str, object]) -> None:
    changed = False
    with STATE_LOCK:
        for period in PERIODS:
            for repo in snapshot.get(period["key"], []):
                clean = normalize_repo(repo)
                if clean and USER_STATE["repo_records"].get(clean["url"]) != clean:
                    USER_STATE["repo_records"][clean["url"]] = clean
                    changed = True
        if changed:
            save_user_state()


def choose_runtime_port() -> int:
    preferred = clamp_int(SETTINGS.get("port", 8080), 8080, 1, 65535)
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


def write_status(refreshing: bool, fetched_at: str = "", source: str = "", error: str = "") -> None:
    atomic_write_json(
        runtime_paths().status_path,
        {
            "refreshing": refreshing,
            "fetched_at": fetched_at,
            "source": source,
            "error": error,
            "updated_at": iso_now(),
        },
    )


def create_runtime_job(job_type: str, *, title: str = "", payload: dict[str, object] | None = None) -> str:
    runtime = job_event_runtime
    if runtime is None or not callable(getattr(runtime, "create_job", None)):
        return ""
    try:
        job = runtime.create_job(job_type, title=title, payload=payload if isinstance(payload, dict) else {})
    except Exception as exc:
        logger.warning("runtime_job_create_failed type=%s error=%s", job_type, redact_text(exc))
        return ""
    return normalize(job.get("id") if isinstance(job, dict) else "")


def update_runtime_job(job_id: str, **changes) -> None:
    clean_id = normalize(job_id)
    runtime = job_event_runtime
    if not clean_id or runtime is None or not callable(getattr(runtime, "update_job", None)):
        return
    try:
        runtime.update_job(clean_id, **changes)
    except Exception as exc:
        logger.warning("runtime_job_update_failed job_id=%s error=%s", clean_id, redact_text(exc))


def record_runtime_event(event_type: str, *, job_id: str = "", payload: dict[str, object] | None = None) -> None:
    runtime = job_event_runtime
    if runtime is None or not callable(getattr(runtime, "record_event", None)):
        return
    try:
        runtime.record_event(event_type, job_id=job_id, payload=payload if isinstance(payload, dict) else {})
    except Exception as exc:
        logger.warning("runtime_event_record_failed type=%s error=%s", event_type, redact_text(exc))


def write_html(snapshot: dict[str, object], note: str, pending: bool) -> None:
    atomic_write_text(
        runtime_paths().html_path,
        build_runtime_html(
            app_name=APP_NAME,
            snapshot=snapshot,
            user_state=export_user_state(),
            discovery_state=export_discovery_state(),
            settings=sanitize_settings(False),
            periods=PERIODS,
            states=STATE_DEFS,
            note=note,
            pending=pending,
            control_token=CONTROL_TOKEN,
        ),
    )


def refresh_once_locked(source: str, status_written: bool = False, runtime_job_id: str = "") -> dict[str, object]:
    global CURRENT_SNAPSHOT, AUTO_SYNC_USER_STARS_DONE
    started_ts = time.perf_counter()
    if not status_written:
        write_status(True, str(CURRENT_SNAPSHOT.get("fetched_at", "")), source, "")
    snapshot = github_runtime.fetch_all()
    save_snapshot(snapshot)
    if normalize(SETTINGS.get("github_token", "")) and not AUTO_SYNC_USER_STARS_DONE:
        AUTO_SYNC_USER_STARS_DONE = True
        try:
            github_runtime.sync_local_favorites_with_starred(github_runtime.fetch_user_starred())
        except Exception as exc:
            logger.warning("github_star_sync_failed source=%s error=%s", source, redact_text(exc))
    sync_repo_records(snapshot)
    new_update_count = github_runtime.track_favorite_updates()
    record_runtime_event(
        "favorite_updates.checked",
        job_id=runtime_job_id,
        payload={"source": source, "new_update_count": int(new_update_count or 0)},
    )
    CURRENT_SNAPSHOT = snapshot
    write_html(snapshot, "已显示最新数据", False)
    write_status(False, str(snapshot.get("fetched_at", "")), source, "")
    update_runtime_job(
        runtime_job_id,
        status="completed",
        stage="completed",
        progress=1.0,
        message="刷新完成",
        payload={"source": source, "new_update_count": int(new_update_count or 0)},
    )
    logger.info(
        "refresh_completed source=%s periods=%d new_favorite_updates=%d duration_ms=%d",
        source,
        sum(len(snapshot.get(period["key"], [])) for period in PERIODS),
        new_update_count,
        int((time.perf_counter() - started_ts) * 1000),
    )
    if new_update_count:
        shell_runtime.notify_tray(f"有 {new_update_count} 个收藏仓库发生了变化，请查看“收藏更新”面板。")
    return snapshot


def refresh_once(source: str = "network", runtime_job_id: str = "") -> dict[str, object]:
    if not REFRESH_LOCK.acquire(blocking=False):
        raise RuntimeError("后台正在刷新，请稍后")
    try:
        return refresh_once_locked(source, runtime_job_id=runtime_job_id)
    finally:
        REFRESH_LOCK.release()


def refresh_once_safe(source: str = "network", lock_acquired: bool = False, status_written: bool = False) -> None:
    runtime_job_id = create_runtime_job("refresh", title="刷新 GitHub 数据", payload={"source": source})
    update_runtime_job(
        runtime_job_id,
        status="running",
        stage="refreshing",
        progress=0.05,
        message="正在刷新 GitHub 数据",
        payload={"source": source},
    )
    try:
        if lock_acquired:
            refresh_once_locked(source, status_written=status_written, runtime_job_id=runtime_job_id)
        else:
            refresh_once(source, runtime_job_id=runtime_job_id)
    except Exception as exc:
        write_status(False, str(CURRENT_SNAPSHOT.get("fetched_at", "")), source, SAFE_REFRESH_ERROR)
        update_runtime_job(
            runtime_job_id,
            status="failed",
            stage="failed",
            progress=1.0,
            message=SAFE_REFRESH_ERROR,
            payload={"source": source},
        )
        logger.error("refresh_failed source=%s error=%s", source, redact_text(exc))
    finally:
        if lock_acquired:
            REFRESH_LOCK.release()


def start_refresh_async(source: str) -> bool:
    if not REFRESH_LOCK.acquire(blocking=False):
        return False
    write_status(True, str(CURRENT_SNAPSHOT.get("fetched_at", "")), source, "")
    try:
        threading.Thread(target=refresh_once_safe, args=(source, True, True), daemon=True).start()
        return True
    except Exception as exc:
        REFRESH_LOCK.release()
        write_status(False, str(CURRENT_SNAPSHOT.get("fetched_at", "")), source, SAFE_REFRESH_ERROR)
        logger.error("refresh_thread_start_failed source=%s error=%s", source, redact_text(exc))
        return False


def _build_runtime_services() -> None:
    global shell_runtime, github_runtime, discovery_job_runtime, diagnostics_runtime, api_boundary_runtime, job_event_runtime, ServerAppHandler
    global estimate_discovery_eta, update_discovery_job, run_discovery_search, start_discovery_job, get_discovery_job
    global cancel_discovery_job, export_active_discovery_job, run_diagnostics

    if shell_runtime is None:
        shell_runtime = make_shell_runtime(
            app_name=APP_NAME,
            app_slug=APP_SLUG,
            desktop_shell_dir=runtime_paths().desktop_shell_dir,
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
    if github_runtime is None:
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
            flush_translation_cache=flush_translation_cache,
            save_repo_details=save_repo_details,
            flush_repo_details_cache=flush_repo_details_cache,
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
    if discovery_job_runtime is None:
        if job_event_runtime is None:
            job_event_runtime = make_job_event_runtime(
                normalize=normalize,
                iso_now=iso_now,
            )
        discovery_job_runtime = make_discovery_job_runtime(
            settings=SETTINGS,
            normalize=normalize,
            clamp_int=clamp_int,
            as_bool=as_bool,
            iso_now=iso_now,
            normalize_repo=normalize_repo,
            normalize_discovery_query=normalize_discovery_query,
            apply_discovery_result=apply_discovery_result,
            discovery_warning_list=discovery_warning_list,
            github_runtime=github_runtime,
            job_lock=DISCOVERY_JOB_LOCK,
            event_runtime=job_event_runtime,
        )
        estimate_discovery_eta = discovery_job_runtime.estimate_discovery_eta
        update_discovery_job = discovery_job_runtime.update_discovery_job
        run_discovery_search = discovery_job_runtime.run_discovery_search
        start_discovery_job = discovery_job_runtime.start_discovery_job
        get_discovery_job = discovery_job_runtime.get_discovery_job
        cancel_discovery_job = discovery_job_runtime.cancel_discovery_job
        export_active_discovery_job = discovery_job_runtime.export_active_discovery_job
    if diagnostics_runtime is None:
        diagnostics_runtime = make_diagnostics_runtime(
            app_name=APP_NAME,
            runtime_root=runtime_paths().runtime_root,
            status_path=runtime_paths().status_path,
            sanitize_settings=sanitize_settings,
            current_port=current_port,
            validate_github_token=github_runtime.validate_github_token,
            load_json_file=load_json_file,
            session=SESSION,
            api_timeout=API_TIMEOUT,
            trending_timeout=TRENDING_TIMEOUT,
            tcp_port_open=tcp_port_open,
            iso_now=iso_now,
        )
        run_diagnostics = diagnostics_runtime.run_diagnostics
    if api_boundary_runtime is None:
        api_boundary_runtime = make_api_boundary_runtime(
            periods=PERIODS,
            current_snapshot_getter=lambda: CURRENT_SNAPSHOT,
            export_user_state=export_user_state,
            export_discovery_state=export_discovery_state,
            sanitize_settings=sanitize_settings,
            status_getter=lambda: load_json_file(runtime_paths().status_path, {}),
            normalize=normalize,
        )
    if job_event_runtime is None:
        job_event_runtime = make_job_event_runtime(
            normalize=normalize,
            iso_now=iso_now,
        )
    if ServerAppHandler is None:
        ServerAppHandler = make_app_handler(
            runtime_root=runtime_paths().runtime_root,
            status_path=runtime_paths().status_path,
            settings=SETTINGS,
            settings_lock=SETTINGS_LOCK,
            sanitize_settings=sanitize_settings,
            load_json_file=load_json_file,
            fetch_repo_details=github_runtime.fetch_repo_details,
            normalize=normalize,
            as_bool=as_bool,
            set_repo_state=set_repo_state,
            set_repo_state_batch=set_repo_state_batch,
            set_repo_annotation=set_repo_annotation,
            set_favorite_update_state=set_favorite_update_state,
            export_user_state=export_user_state,
            set_ai_insight=set_ai_insight,
            delete_ai_insight=delete_ai_insight,
            export_ai_artifacts=list_ai_artifacts,
            import_user_state=import_user_state,
            normalize_settings=normalize_settings,
            merge_settings=merge_settings,
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
            get_discovery_job=get_discovery_job,
            cancel_discovery_job=cancel_discovery_job,
            save_discovery_view=save_discovery_view,
            delete_discovery_view=delete_discovery_view,
            clear_discovery_results=clear_discovery_results,
            export_discovery_state=export_discovery_state,
            export_active_discovery_job=export_active_discovery_job,
            sync_favorite_repo=github_runtime.sync_favorite_repo,
            fetch_user_starred=github_runtime.fetch_user_starred,
            sync_local_favorites_with_starred=github_runtime.sync_local_favorites_with_starred,
            validate_github_token=github_runtime.validate_github_token,
            run_diagnostics=run_diagnostics,
            export_api_bootstrap=api_boundary_runtime.export_bootstrap,
            export_api_repos=api_boundary_runtime.export_repos,
            export_api_updates=api_boundary_runtime.export_updates,
            export_api_discovery_views=api_boundary_runtime.export_discovery_views,
            export_jobs=job_event_runtime.export_jobs,
            export_events=job_event_runtime.export_events,
            open_main_window=shell_runtime.open_main_window,
            exit_app=shell_runtime.exit_app,
            control_token_getter=lambda: CONTROL_TOKEN,
        )


def refresh_loop(run_immediately: bool = False) -> None:
    if run_immediately:
        logger.info("startup_refresh_begin")
        refresh_once_safe("startup")
        logger.info("startup_refresh_complete")
    while not APP_EXIT_EVENT.wait(clamp_int(SETTINGS.get("refresh_hours", 1), 1, 1, 24) * 3600):
        logger.info("scheduled_refresh_begin")
        refresh_once_safe("auto")


def main() -> None:
    global CURRENT_SNAPSHOT, RUNTIME_PORT, CONTROL_TOKEN, AUTO_SYNC_USER_STARS_DONE, DETAIL_CACHE_DIRTY
    build_runtime_context(rebuild=True)
    configure_console()
    ensure_runtime_layout()
    if not acquire_single_instance():
        if not request_existing_instance_open():
            show_message_box("GitSonar 已经在运行。")
        return
    server = None
    logger.info("=" * 40)
    logger.info("  %s", APP_NAME)
    logger.info("=" * 40)
    try:
        TRANSLATION_CACHE.clear()
        TRANSLATION_CACHE.update(load_translation_cache())
        _get_detail_cache_runtime().reload_detail_cache()
        CONTROL_TOKEN = secrets.token_urlsafe(32)
        AUTO_SYNC_USER_STARS_DONE = False
        SETTINGS.clear()
        SETTINGS.update(load_settings())
        apply_runtime_settings()
        update_auto_start(bool(SETTINGS.get("auto_start")))
        USER_STATE.clear()
        USER_STATE.update(load_user_state())
        DISCOVERY_STATE.clear()
        DISCOVERY_STATE.update(load_discovery_state())
        RUNTIME_PORT = choose_runtime_port()
        CURRENT_SNAPSHOT = load_snapshot()
        sync_repo_records(CURRENT_SNAPSHOT)
        has_cache = any(CURRENT_SNAPSHOT.get(period["key"]) for period in PERIODS)
        note = "已加载本地缓存，后台刷新中..." if has_cache else "首次启动，正在后台抓取数据..."
        write_html(CURRENT_SNAPSHOT, note, True)
        write_status(True, str(CURRENT_SNAPSHOT.get("fetched_at", "")), "cache", "")
        server = ThreadingHTTPServer((SERVER_HOST, current_port()), ServerAppHandler)
        set_main_url(f"http://{LOCAL_HOST}:{current_port()}/trending.html?v={int(time.time())}")
        write_runtime_state()
        logger.info("local_url=%s", get_main_url())
        logger.info("refresh_interval_hours=%s", SETTINGS.get("refresh_hours", 1))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        threading.Thread(target=refresh_loop, kwargs={"run_immediately": True}, daemon=True).start()
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


if __name__ == "__main__":
    main()
