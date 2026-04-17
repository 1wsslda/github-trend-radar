#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import threading
import time
import webbrowser
from types import SimpleNamespace

logger = logging.getLogger(__name__)


def make_shell_runtime(
    *,
    app_name: str,
    app_slug: str,
    desktop_shell_dir: str,
    app_exit_event,
    browser_lock,
    start_refresh_async,
    write_runtime_state,
    get_main_url,
    get_browser_process,
    set_browser_process,
    set_browser_hidden,
    normalize,
    quote,
):
    create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    popen_flags: dict[str, object] = {"creationflags": create_no_window} if os.name == "nt" else {}
    max_chatgpt_url_chars = 3500
    browser_pid_hints: set[int] = set()
    close_monitor_grace_until = 0.0
    close_monitor_handled = True

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

    def launch_process(command: list[str]) -> subprocess.Popen:
        return subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **popen_flags,
        )

    def remember_browser_pids(pids: list[int] | set[int] | tuple[int, ...]) -> None:
        for pid in pids:
            if int(pid) > 0:
                browser_pid_hints.add(int(pid))

    def arm_close_monitor(grace_seconds: float = 4.0) -> None:
        nonlocal close_monitor_grace_until, close_monitor_handled
        close_monitor_grace_until = time.time() + max(0.5, grace_seconds)
        close_monitor_handled = False

    def disarm_close_monitor() -> None:
        nonlocal close_monitor_grace_until, close_monitor_handled
        close_monitor_grace_until = 0.0
        close_monitor_handled = True

    def snapshot_process_tree() -> tuple[dict[int, list[int]], set[int]]:
        if os.name != "nt":
            return {}, set()
        kernel32 = ctypes.windll.kernel32
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        invalid_handle = ctypes.c_void_p(-1).value
        if snapshot == invalid_handle:
            return {}, set()
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                return {}, set()
            children: dict[int, list[int]] = {}
            existing: set[int] = set()
            while True:
                pid = int(entry.th32ProcessID)
                parent_pid = int(entry.th32ParentProcessID)
                existing.add(pid)
                children.setdefault(parent_pid, []).append(pid)
                if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
            return children, existing
        finally:
            kernel32.CloseHandle(snapshot)

    def process_tree_pids(root_pid: int) -> set[int]:
        if root_pid <= 0:
            return set()
        if os.name != "nt":
            return {root_pid}
        children, existing = snapshot_process_tree()
        if root_pid not in existing:
            return set()
        pids: set[int] = set()
        stack = [root_pid]
        while stack:
            pid = stack.pop()
            if pid in pids:
                continue
            pids.add(pid)
            stack.extend(children.get(pid, []))
        return pids

    def browser_candidate_pids() -> set[int]:
        seeds: set[int] = set(browser_pid_hints)
        process = get_browser_process()
        if process and process.pid > 0:
            seeds.add(int(process.pid))
        pids: set[int] = set()
        for pid in seeds:
            tree = process_tree_pids(pid)
            if tree:
                pids.update(tree)
        if pids:
            browser_pid_hints.intersection_update(pids)
        return pids

    def find_desktop_browser() -> str | None:
        candidates = [
            shutil.which("chrome"),
            shutil.which("chromium"),
            shutil.which("msedge"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Chromium\Application\chromium.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    def find_chatgpt_desktop() -> str | None:
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            shutil.which("ChatGPT"),
            shutil.which("chatgpt"),
            os.path.join(local_appdata, "Programs", "ChatGPT", "ChatGPT.exe"),
            os.path.join(local_appdata, "ChatGPT", "ChatGPT.exe"),
            r"C:\Program Files\ChatGPT\ChatGPT.exe",
            r"C:\Program Files (x86)\ChatGPT\ChatGPT.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    def open_external_url(url: str) -> bool:
        target = normalize(url)
        if not target:
            return False
        try:
            if os.name == "nt" and hasattr(os, "startfile"):
                os.startfile(target)
                return True
            return bool(webbrowser.open(target))
        except Exception:
            logger.exception("使用系统默认方式打开外部链接失败: %s", target)
            try:
                return bool(webbrowser.open(target))
            except Exception:
                logger.exception("使用 webbrowser 打开外部链接失败: %s", target)
                return False

    def open_system_target(target: str) -> bool:
        normalized_target = normalize(target)
        if not normalized_target:
            return False
        try:
            if os.name == "nt" and hasattr(os, "startfile"):
                os.startfile(normalized_target)
                return True
            return bool(webbrowser.open(normalized_target))
        except Exception:
            logger.exception("使用系统协议打开目标失败: %s", normalized_target)
            return False

    def chatgpt_url(prompt: str) -> str:
        normalized_prompt = normalize(prompt)
        if not normalized_prompt:
            return "https://chatgpt.com/"
        return f"https://chatgpt.com/?q={quote(normalized_prompt)}"

    def gemini_url(prompt: str) -> str:
        normalized_prompt = normalize(prompt)
        if not normalized_prompt:
            return "https://gemini.google.com/"
        return f"https://gemini.google.com/app?q={quote(normalized_prompt)}"

    def prompt_too_long(prompt: str) -> bool:
        return len(chatgpt_url(prompt)) > max_chatgpt_url_chars

    def open_chatgpt_target(mode: str, prompt: str) -> tuple[bool, str]:
        cleaned_mode = normalize(mode).lower() or "web"
        normalized_prompt = normalize(prompt)
        too_long = bool(normalized_prompt) and prompt_too_long(normalized_prompt)

        if cleaned_mode == "desktop":
            desktop = find_chatgpt_desktop()
            if desktop:
                if too_long:
                    launch_process([desktop])
                    return True, "提示词过长，已打开 ChatGPT 桌面版。提示词已复制到剪贴板，请手动粘贴。"
                if os.name == "nt" and normalized_prompt:
                    try:
                        if open_system_target(f"chatgpt:///?q={quote(normalized_prompt)}"):
                            return True, "已打开 ChatGPT 桌面版并自动填入分析提示词。"
                    except Exception:
                        logger.exception("通过 chatgpt:// 协议打开桌面版失败，回退到普通启动")
                launch_process([desktop])
                return True, "已打开 ChatGPT 桌面版。提示词已复制到剪贴板，请手动粘贴。"
            if too_long:
                opened = open_external_url("https://chatgpt.com/")
                return opened, "未发现 ChatGPT 桌面版，已改为在默认浏览器打开 ChatGPT。提示词已复制到剪贴板，请手动粘贴。"
            opened = open_external_url(chatgpt_url(normalized_prompt))
            return opened, "未发现 ChatGPT 桌面版，已改为在默认浏览器打开 ChatGPT 并自动填入提示词。"

        if cleaned_mode == "gemini_web":
            if too_long:
                opened = open_external_url("https://gemini.google.com/")
                return opened, "提示词过长，已在默认浏览器打开 Gemini。提示词已复制到剪贴板，请手动粘贴。"
            opened = open_external_url(gemini_url(normalized_prompt))
            return opened, "已在默认浏览器打开 Gemini 并自动填入分析提示词。"

        if too_long:
            opened = open_external_url("https://chatgpt.com/")
            return opened, "提示词过长，已在默认浏览器打开 ChatGPT。提示词已复制到剪贴板，请手动粘贴。"

        opened = open_external_url(chatgpt_url(normalized_prompt))
        return opened, "已在默认浏览器打开 ChatGPT 并自动填入分析提示词。"

    def browser_windows(pids: set[int]) -> list[dict[str, object]]:
        if os.name != "nt" or not pids:
            return []
        user32 = ctypes.windll.user32
        windows: list[dict[str, object]] = []
        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum_proc
        def callback(hwnd, _):
            process_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            pid = int(process_id.value)
            if pid in pids and user32.GetWindow(hwnd, 4) == 0:
                title_buffer = ctypes.create_unicode_buffer(512)
                class_buffer = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
                user32.GetClassNameW(hwnd, class_buffer, len(class_buffer))
                windows.append({
                    "hwnd": int(hwnd),
                    "pid": pid,
                    "title": normalize(title_buffer.value),
                    "class_name": normalize(class_buffer.value),
                    "visible": bool(user32.IsWindowVisible(hwnd)),
                })
            return True

        user32.EnumWindows(callback, 0)
        return windows

    def split_browser_windows(windows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        main_windows: list[dict[str, object]] = []
        aux_windows: list[dict[str, object]] = []
        for window in windows:
            class_name = normalize(window.get("class_name"))
            title = normalize(window.get("title"))
            if class_name == "Base_PowerMessageWindow":
                continue
            if class_name == "Chrome_WidgetWin_1" or (class_name.startswith("Chrome_WidgetWin_") and title):
                main_windows.append(window)
            else:
                aux_windows.append(window)
        return main_windows, aux_windows

    def main_browser_window_count() -> int:
        main_windows, _ = split_browser_windows(browser_windows(browser_candidate_pids()))
        return len(main_windows)

    def show_browser_window() -> bool:
        user32 = ctypes.windll.user32
        for _ in range(30):
            windows = browser_windows(browser_candidate_pids())
            main_windows, aux_windows = split_browser_windows(windows)
            if main_windows:
                remember_browser_pids([int(window["pid"]) for window in main_windows + aux_windows])
                for window in aux_windows:
                    user32.ShowWindow(int(window["hwnd"]), 0)
                for window in main_windows:
                    hwnd = int(window["hwnd"])
                    user32.ShowWindow(hwnd, 9 if user32.IsIconic(hwnd) else 5)
                    user32.SetForegroundWindow(hwnd)
                arm_close_monitor()
                return True
            time.sleep(0.1)
        return False

    def hide_browser_window() -> bool:
        windows = browser_windows(browser_candidate_pids())
        main_windows, aux_windows = split_browser_windows(windows)
        if not main_windows and not aux_windows:
            return False
        remember_browser_pids([int(window["pid"]) for window in main_windows + aux_windows])
        user32 = ctypes.windll.user32
        for window in aux_windows + main_windows:
            user32.ShowWindow(int(window["hwnd"]), 0)
        disarm_close_monitor()
        return bool(main_windows)

    def terminate_browser_tree() -> None:
        process = get_browser_process()
        target_pid = int(process.pid) if process and process.pid > 0 else 0
        if target_pid:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(target_pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    **popen_flags,
                )
            except Exception:
                try:
                    process.terminate()
                except Exception:
                    pass
        else:
            for pid in sorted(browser_candidate_pids(), reverse=True):
                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        **popen_flags,
                    )
                except Exception:
                    pass
        browser_pid_hints.clear()
        disarm_close_monitor()

    def open_main_window() -> bool:
        browser = find_desktop_browser()
        if not browser:
            open_external_url(get_main_url())
            return False
        with browser_lock:
            if show_browser_window():
                set_browser_hidden(False)
                write_runtime_state()
                return True
            terminate_browser_tree()
            os.makedirs(desktop_shell_dir, exist_ok=True)
            process = launch_process(
                [
                    browser,
                    f"--app={get_main_url()}",
                    "--new-window",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                    "--disable-features=Translate,msHubApps",
                    f"--user-data-dir={desktop_shell_dir}",
                    "--window-size=1480,960",
                ]
            )
            set_browser_process(process)
            remember_browser_pids([process.pid])
            set_browser_hidden(False)
            arm_close_monitor(grace_seconds=6.0)
            write_runtime_state()
        show_browser_window()
        return True

    def close_main_window() -> None:
        with browser_lock:
            set_browser_process(None)
            set_browser_hidden(False)
        terminate_browser_tree()

    def request_app_exit(icon=None) -> None:
        disarm_close_monitor()
        app_exit_event.set()

    def exit_app() -> None:
        request_app_exit()

    def notify_tray(message: str) -> None:
        return None

    def close_monitor_loop() -> None:
        nonlocal close_monitor_handled
        while not app_exit_event.wait(0.8):
            should_handle = False
            with browser_lock:
                if close_monitor_handled or time.time() < close_monitor_grace_until:
                    continue
                if get_browser_process() is None and not browser_pid_hints:
                    continue
                if get_browser_process() and get_browser_process().poll() is not None:
                    set_browser_process(None)
                if main_browser_window_count() > 0:
                    continue
                close_monitor_handled = True
                set_browser_hidden(True)
                write_runtime_state()
                should_handle = True
            if not should_handle:
                continue
            exit_app()

    def run_tray_loop() -> None:
        threading.Thread(target=close_monitor_loop, daemon=True).start()
        while not app_exit_event.wait(0.8):
            pass

    return SimpleNamespace(
        open_chatgpt_target=open_chatgpt_target,
        open_external_url=open_external_url,
        open_main_window=open_main_window,
        close_main_window=close_main_window,
        exit_app=exit_app,
        run_tray_loop=run_tray_loop,
        notify_tray=notify_tray,
    )
