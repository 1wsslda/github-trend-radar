#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
import shutil
import sys

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


RUNTIME_ROOT = merge_legacy_runtime_root() if IS_FROZEN else merge_dev_runtime_root()
LEGACY_RUNTIME_ROOT = runtime_root_for_slug(LEGACY_APP_SLUG) if IS_FROZEN else PROJECT_ROOT
DATA_DIR = os.path.join(RUNTIME_ROOT, "data")
HTML_PATH = os.path.join(RUNTIME_ROOT, "trending.html")
STATUS_PATH = os.path.join(RUNTIME_ROOT, "status.json")
SETTINGS_PATH = os.path.join(RUNTIME_ROOT, "settings.json")
USER_STATE_PATH = os.path.join(RUNTIME_ROOT, "user_state.json")
DISCOVERY_STATE_PATH = os.path.join(RUNTIME_ROOT, "discovery_state.json")
LATEST_SNAPSHOT_PATH = os.path.join(DATA_DIR, "latest.json")
DETAIL_CACHE_PATH = os.path.join(RUNTIME_ROOT, "repo_details_cache.json")
RUNTIME_STATE_PATH = os.path.join(RUNTIME_ROOT, "runtime_state.json")
DESKTOP_SHELL_DIR = os.path.join(RUNTIME_ROOT, ".desktop_shell")
CACHE_PATH = os.path.join(RUNTIME_ROOT, ".translation_cache.json")
LEGACY_RUNTIME_STATE_PATH = os.path.join(LEGACY_RUNTIME_ROOT, "runtime_state.json")
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
    "merge_dev_runtime_root",
    "merge_legacy_runtime_root",
]
