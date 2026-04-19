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
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from ..runtime_github import make_github_runtime
from ..runtime_ui import build_html as build_runtime_html
from .discovery_jobs import make_discovery_job_runtime
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

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

LOCAL_CONTROL = requests.Session()
LOCAL_CONTROL.trust_env = False

TRANSLATE_SESSION = requests.Session()
TRANSLATE_SESSION.trust_env = False
TRANSLATE_SESSION.headers.update(HEADERS)

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
CURRENT_SNAPSHOT: dict[str, object] = {}
RUNTIME_PORT: int | None = None
CONTROL_TOKEN = ""
AUTO_SYNC_USER_STARS_DONE = False

APP_EXIT_EVENT = threading.Event()
BROWSER_LOCK = threading.RLock()
DETAIL_FETCH_SEMAPHORE = threading.Semaphore(3)
TRANSLATION_CACHE: dict[str, str] = {}
DETAIL_CACHE: dict[str, object] = {}
DETAIL_FETCH_LOCKS: dict[str, threading.Lock] = {}

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


def ensure_runtime_layout() -> None:
    os.makedirs(RUNTIME_ROOT, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


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


def load_detail_cache() -> dict[str, object]:
    raw = load_json_file(DETAIL_CACHE_PATH, {})
    return raw if isinstance(raw, dict) else {}


def cached_repo_details(cache_key: str) -> dict[str, object] | None:
    now = int(time.time())
    with DETAIL_CACHE_LOCK:
        cached = DETAIL_CACHE.get(cache_key, {})
        if (
            isinstance(cached, dict)
            and clamp_int(cached.get("expires_at"), 0, 0) > now
            and isinstance(cached.get("data"), dict)
        ):
            return dict(cached["data"])
    return None


def detail_fetch_lock(cache_key: str) -> threading.Lock:
    with DETAIL_CACHE_LOCK:
        lock = DETAIL_FETCH_LOCKS.get(cache_key)
        if lock is None:
            if len(DETAIL_FETCH_LOCKS) >= _MAX_DETAIL_FETCH_LOCKS:
                stale = [key for key in DETAIL_FETCH_LOCKS if key not in DETAIL_CACHE]
                for key in stale[:500]:
                    del DETAIL_FETCH_LOCKS[key]
                if len(DETAIL_FETCH_LOCKS) >= _MAX_DETAIL_FETCH_LOCKS:
                    for key in list(DETAIL_FETCH_LOCKS)[:500]:
                        del DETAIL_FETCH_LOCKS[key]
            lock = threading.Lock()
            DETAIL_FETCH_LOCKS[cache_key] = lock
        return lock


def save_repo_details(cache_key: str, details: dict[str, object]) -> None:
    now = int(time.time())
    with DETAIL_CACHE_LOCK:
        DETAIL_CACHE[cache_key] = {
            "expires_at": now + DETAIL_CACHE_SECONDS,
            "data": dict(details),
        }
        expired = [
            key
            for key, value in DETAIL_CACHE.items()
            if isinstance(value, dict) and clamp_int(value.get("expires_at"), 0, 0) <= now
        ]
        for key in expired:
            del DETAIL_CACHE[key]
        if len(DETAIL_CACHE) > _MAX_DETAIL_CACHE_SIZE:
            oldest = sorted(
                DETAIL_CACHE,
                key=lambda key: clamp_int(
                    DETAIL_CACHE[key].get("expires_at") if isinstance(DETAIL_CACHE[key], dict) else 0,
                    0,
                    0,
                ),
            )
            for key in oldest[: len(DETAIL_CACHE) - _MAX_DETAIL_CACHE_SIZE]:
                del DETAIL_CACHE[key]
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


def current_port() -> int:
    return RUNTIME_PORT or clamp_int(SETTINGS.get("port", 8080), 8080, 1, 65535)


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
    control_token_getter=lambda: CONTROL_TOKEN,
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


def set_repo_state(state_key: str, enabled: bool, repo: object) -> None:
    if state_key not in {item["key"] for item in STATE_DEFS}:
        raise ValueError("无效状态")
    clean = normalize_repo(repo)
    if not clean:
        raise ValueError("缺少仓库信息")
    url = clean["url"]
    with STATE_LOCK:
        USER_STATE["repo_records"][url] = clean
        USER_STATE[state_key] = [item for item in USER_STATE.get(state_key, []) if item != url]
        if enabled:
            USER_STATE[state_key].insert(0, url)
        elif state_key == "favorites":
            USER_STATE.get("favorite_watch", {}).pop(url, None)
        save_user_state()


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
        STATUS_PATH,
        {
            "refreshing": refreshing,
            "fetched_at": fetched_at,
            "source": source,
            "error": error,
            "updated_at": iso_now(),
        },
    )


def write_html(snapshot: dict[str, object], note: str, pending: bool) -> None:
    atomic_write_text(
        HTML_PATH,
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


def refresh_once_locked(source: str, status_written: bool = False) -> dict[str, object]:
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
            logger.warning("github_star_sync_failed source=%s error=%s", source, exc)
    sync_repo_records(snapshot)
    new_update_count = github_runtime.track_favorite_updates()
    CURRENT_SNAPSHOT = snapshot
    write_html(snapshot, "已显示最新数据", False)
    write_status(False, str(snapshot.get("fetched_at", "")), source, "")
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


def refresh_once(source: str = "network") -> dict[str, object]:
    if not REFRESH_LOCK.acquire(blocking=False):
        raise RuntimeError("后台正在刷新，请稍后")
    try:
        return refresh_once_locked(source)
    finally:
        REFRESH_LOCK.release()


def refresh_once_safe(source: str = "network", lock_acquired: bool = False, status_written: bool = False) -> None:
    try:
        if lock_acquired:
            refresh_once_locked(source, status_written=status_written)
        else:
            refresh_once(source)
    except Exception as exc:
        write_status(False, str(CURRENT_SNAPSHOT.get("fetched_at", "")), source, str(exc))
        logger.error("refresh_failed source=%s error=%s", source, exc)
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
        write_status(False, str(CURRENT_SNAPSHOT.get("fetched_at", "")), source, str(exc))
        logger.error("refresh_thread_start_failed source=%s error=%s", source, exc)
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
)
estimate_discovery_eta = discovery_job_runtime.estimate_discovery_eta
update_discovery_job = discovery_job_runtime.update_discovery_job
run_discovery_search = discovery_job_runtime.run_discovery_search
start_discovery_job = discovery_job_runtime.start_discovery_job
get_discovery_job = discovery_job_runtime.get_discovery_job
cancel_discovery_job = discovery_job_runtime.cancel_discovery_job
export_active_discovery_job = discovery_job_runtime.export_active_discovery_job

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
    clear_discovery_results=clear_discovery_results,
    export_discovery_state=export_discovery_state,
    export_active_discovery_job=export_active_discovery_job,
    sync_favorite_repo=github_runtime.sync_favorite_repo,
    fetch_user_starred=github_runtime.fetch_user_starred,
    sync_local_favorites_with_starred=github_runtime.sync_local_favorites_with_starred,
    validate_github_token=github_runtime.validate_github_token,
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
    global CURRENT_SNAPSHOT, RUNTIME_PORT, CONTROL_TOKEN, AUTO_SYNC_USER_STARS_DONE
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
        with DETAIL_CACHE_LOCK:
            DETAIL_CACHE.clear()
            DETAIL_CACHE.update(load_detail_cache())
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
