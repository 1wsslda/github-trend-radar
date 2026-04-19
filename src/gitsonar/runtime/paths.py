#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

APP_NAME = "GitSonar"
APP_SLUG = "GitSonar"
LEGACY_APP_NAME = "GitHub Trend Radar"
LEGACY_APP_SLUG = "GitHubTrendRadar"
IS_FROZEN = getattr(sys, "frozen", False)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PACKAGE_DIR))
DEV_RUNTIME_ROOT = os.path.join(PROJECT_ROOT, "runtime-data")
DEV_ENTRY_SCRIPT = os.path.join(PACKAGE_DIR, "__main__.py")
EXEC_DIR = os.path.dirname(os.path.abspath(sys.executable)) if IS_FROZEN else PROJECT_ROOT
LOCAL_APPDATA_ROOT = os.environ.get("LOCALAPPDATA", EXEC_DIR)
DEV_RUNTIME_ITEMS = (
    "data",
    ".desktop_shell",
    ".translation_cache.json",
    "settings.json",
    "status.json",
    "trending.html",
    "user_state.json",
    "repo_details_cache.json",
    "runtime_state.json",
)


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    runtime_root: str
    legacy_runtime_root: str
    data_dir: str
    html_path: str
    status_path: str
    settings_path: str
    user_state_path: str
    discovery_state_path: str
    latest_snapshot_path: str
    detail_cache_path: str
    runtime_state_path: str
    desktop_shell_dir: str
    cache_path: str
    legacy_runtime_state_path: str


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
                logger.warning("杩佺Щ寮€鍙戞€佽繍琛屾暟鎹け璐? %s (%s)", source, exc)
        if migrated_items:
            logger.info("宸插皢 %s 椤瑰紑鍙戞€佽繍琛屾暟鎹縼绉诲埌 %s", len(migrated_items), preferred)
    except Exception as exc:
        logger.warning("鍒濆鍖栧紑鍙戞€佽繍琛岀洰褰曞け璐ワ紝鍥為€€鍒颁粨搴撴牴鐩綍: %s", exc)
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
                logger.warning("杩佺Щ鏃ф暟鎹」澶辫触: %s (%s)", source, exc)
        if migrated_items:
            logger.info("宸蹭粠鏃ф暟鎹洰褰曞悎骞?%s 椤瑰埌 %s", len(migrated_items), preferred)
    except Exception as exc:
        logger.warning("鍒濆鍖栨柊鏁版嵁鐩綍澶辫触锛屽洖閫€鍒版棫鐩綍: %s", exc)
        if os.path.isdir(legacy) and not os.path.isdir(preferred):
            return legacy
    return preferred


def build_runtime_paths(*, migrate: bool = False) -> RuntimePaths:
    runtime_root = (
        merge_legacy_runtime_root()
        if migrate and IS_FROZEN
        else merge_dev_runtime_root()
        if migrate
        else runtime_root_for_slug(APP_SLUG)
        if IS_FROZEN
        else DEV_RUNTIME_ROOT
    )
    legacy_runtime_root = runtime_root_for_slug(LEGACY_APP_SLUG) if IS_FROZEN else PROJECT_ROOT
    data_dir = os.path.join(runtime_root, "data")
    return RuntimePaths(
        runtime_root=runtime_root,
        legacy_runtime_root=legacy_runtime_root,
        data_dir=data_dir,
        html_path=os.path.join(runtime_root, "trending.html"),
        status_path=os.path.join(runtime_root, "status.json"),
        settings_path=os.path.join(runtime_root, "settings.json"),
        user_state_path=os.path.join(runtime_root, "user_state.json"),
        discovery_state_path=os.path.join(runtime_root, "discovery_state.json"),
        latest_snapshot_path=os.path.join(data_dir, "latest.json"),
        detail_cache_path=os.path.join(runtime_root, "repo_details_cache.json"),
        runtime_state_path=os.path.join(runtime_root, "runtime_state.json"),
        desktop_shell_dir=os.path.join(runtime_root, ".desktop_shell"),
        cache_path=os.path.join(runtime_root, ".translation_cache.json"),
        legacy_runtime_state_path=os.path.join(legacy_runtime_root, "runtime_state.json"),
    )


def ensure_runtime_paths() -> RuntimePaths:
    return build_runtime_paths(migrate=True)


DEFAULT_RUNTIME_PATHS = build_runtime_paths()
RUNTIME_ROOT = DEFAULT_RUNTIME_PATHS.runtime_root
LEGACY_RUNTIME_ROOT = DEFAULT_RUNTIME_PATHS.legacy_runtime_root
DATA_DIR = DEFAULT_RUNTIME_PATHS.data_dir
HTML_PATH = DEFAULT_RUNTIME_PATHS.html_path
STATUS_PATH = DEFAULT_RUNTIME_PATHS.status_path
SETTINGS_PATH = DEFAULT_RUNTIME_PATHS.settings_path
USER_STATE_PATH = DEFAULT_RUNTIME_PATHS.user_state_path
DISCOVERY_STATE_PATH = DEFAULT_RUNTIME_PATHS.discovery_state_path
LATEST_SNAPSHOT_PATH = DEFAULT_RUNTIME_PATHS.latest_snapshot_path
DETAIL_CACHE_PATH = DEFAULT_RUNTIME_PATHS.detail_cache_path
RUNTIME_STATE_PATH = DEFAULT_RUNTIME_PATHS.runtime_state_path
DESKTOP_SHELL_DIR = DEFAULT_RUNTIME_PATHS.desktop_shell_dir
CACHE_PATH = DEFAULT_RUNTIME_PATHS.cache_path
LEGACY_RUNTIME_STATE_PATH = DEFAULT_RUNTIME_PATHS.legacy_runtime_state_path
LOCAL_HOST = "127.0.0.1"
SERVER_HOST = LOCAL_HOST

__all__ = [
    "APP_NAME",
    "APP_SLUG",
    "LEGACY_APP_NAME",
    "LEGACY_APP_SLUG",
    "IS_FROZEN",
    "PACKAGE_DIR",
    "PROJECT_ROOT",
    "DEV_RUNTIME_ROOT",
    "DEV_ENTRY_SCRIPT",
    "EXEC_DIR",
    "LOCAL_APPDATA_ROOT",
    "DEV_RUNTIME_ITEMS",
    "RUNTIME_ROOT",
    "LEGACY_RUNTIME_ROOT",
    "DATA_DIR",
    "HTML_PATH",
    "STATUS_PATH",
    "SETTINGS_PATH",
    "USER_STATE_PATH",
    "DISCOVERY_STATE_PATH",
    "LATEST_SNAPSHOT_PATH",
    "DETAIL_CACHE_PATH",
    "RUNTIME_STATE_PATH",
    "DESKTOP_SHELL_DIR",
    "CACHE_PATH",
    "LEGACY_RUNTIME_STATE_PATH",
    "LOCAL_HOST",
    "SERVER_HOST",
    "runtime_root_for_slug",
    "RuntimePaths",
    "build_runtime_paths",
    "ensure_runtime_paths",
    "DEFAULT_RUNTIME_PATHS",
    "merge_dev_runtime_root",
    "merge_legacy_runtime_root",
]
