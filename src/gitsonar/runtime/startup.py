#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from types import SimpleNamespace


def make_startup_runtime(
    *,
    app_name,
    app_slug,
    legacy_app_name,
    legacy_app_slug,
    dev_entry_script,
    exec_dir,
    runtime_state_path,
    legacy_runtime_state_path,
    local_host,
    local_control,
    normalize,
    clamp_int,
    iso_now,
    load_json_file,
    atomic_write_json,
    current_port_getter,
    control_token_getter=None,
):
    APP_NAME = app_name
    APP_SLUG = app_slug
    LEGACY_APP_NAME = legacy_app_name
    LEGACY_APP_SLUG = legacy_app_slug
    DEV_ENTRY_SCRIPT = dev_entry_script
    EXEC_DIR = exec_dir
    RUNTIME_STATE_PATH = runtime_state_path
    LEGACY_RUNTIME_STATE_PATH = legacy_runtime_state_path
    LOCAL_HOST = local_host
    LOCAL_CONTROL = local_control
    control_token_getter = control_token_getter or (lambda: "")
    state = {
        "browser_process": None,
        "browser_hidden": False,
        "main_url": "",
    }
    single_instance_mutexes: list[object] = []

    def current_port():
        return current_port_getter()

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

    def write_runtime_state() -> None:
        browser_process = state["browser_process"]
        pid = int(browser_process.pid) if browser_process and browser_process.poll() is None else 0
        atomic_write_json(
            RUNTIME_STATE_PATH,
            {
                "pid": os.getpid(),
                "port": current_port(),
                "url": state["main_url"],
                "control_token": normalize(control_token_getter()),
                "browser_pid": pid,
                "browser_hidden": bool(state["browser_hidden"]),
                "updated_at": iso_now(),
            },
        )

    def get_main_url() -> str:
        return str(state["main_url"])

    def get_browser_process() -> subprocess.Popen | None:
        return state["browser_process"]

    def set_browser_process(process: subprocess.Popen | None) -> None:
        state["browser_process"] = process

    def set_browser_hidden(hidden: bool) -> None:
        state["browser_hidden"] = bool(hidden)

    def clear_runtime_state() -> None:
        try:
            os.remove(RUNTIME_STATE_PATH)
        except FileNotFoundError:
            pass

    def acquire_single_instance() -> bool:
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
        single_instance_mutexes[:] = handles
        return True

    def release_single_instance() -> None:
        for handle in single_instance_mutexes:
            try:
                ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                pass
        single_instance_mutexes.clear()

    def request_existing_instance_open() -> bool:
        for runtime_path in dict.fromkeys((RUNTIME_STATE_PATH, LEGACY_RUNTIME_STATE_PATH)):
            runtime = load_json_file(runtime_path, {})
            if not isinstance(runtime, dict):
                continue
            port = clamp_int(runtime.get('port'), 0, 1, 65535)
            url = normalize(runtime.get('url'))
            control_token = normalize(runtime.get('control_token'))
            headers = {'X-GitSonar-Control': control_token} if control_token else None
            for _ in range(8):
                if port:
                    try:
                        if LOCAL_CONTROL.post(
                            f'http://{LOCAL_HOST}:{port}/api/window/open',
                            headers=headers,
                            timeout=2,
                        ).ok:
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

    def set_main_url(url: str) -> None:
        state["main_url"] = normalize(url)

    return SimpleNamespace(
        startup_dir=startup_dir,
        startup_launcher_path=startup_launcher_path,
        startup_cmd_path=startup_cmd_path,
        startup_launch_command=startup_launch_command,
        startup_launcher_script=startup_launcher_script,
        update_auto_start=update_auto_start,
        write_runtime_state=write_runtime_state,
        get_main_url=get_main_url,
        get_browser_process=get_browser_process,
        set_browser_process=set_browser_process,
        set_browser_hidden=set_browser_hidden,
        clear_runtime_state=clear_runtime_state,
        acquire_single_instance=acquire_single_instance,
        release_single_instance=release_single_instance,
        request_existing_instance_open=request_existing_instance_open,
        show_message_box=show_message_box,
        set_main_url=set_main_url,
    )
