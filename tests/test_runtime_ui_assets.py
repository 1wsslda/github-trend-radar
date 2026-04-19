from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_ui import build_html
from gitsonar.runtime_ui.assets import CSS, JS


def build_fixture_html(**overrides) -> str:
    payload = {
        "app_name": "GitSonar",
        "snapshot": {"daily": [], "weekly": [], "monthly": []},
        "user_state": {"repo_records": {}, "favorite_updates": []},
        "discovery_state": {},
        "settings": {"result_limit": 25, "default_sort": "stars"},
        "periods": [
            {"key": "daily", "label": "今天"},
            {"key": "weekly", "label": "本周"},
            {"key": "monthly", "label": "本月"},
        ],
        "states": [
            {"key": "favorites", "label": "收藏"},
            {"key": "watch_later", "label": "待看"},
            {"key": "read", "label": "已读"},
            {"key": "ignored", "label": "忽略"},
        ],
        "note": "ready",
        "pending": False,
    }
    payload.update(overrides)
    return build_html(**payload)


class RuntimeUILayoutSmokeTests(unittest.TestCase):
    def test_runtime_ui_public_exports_are_available(self):
        self.assertIn("function render()", JS)
        self.assertIn(".workspace-header{", CSS)

    def test_build_html_preserves_legacy_signature(self):
        html = build_fixture_html()

        self.assertIn('"controlToken": ""', html)
        self.assertIn('id="panel-summary"', html)

    def test_compact_workspace_shell_is_present(self):
        html = build_fixture_html(control_token="test-control-token")
        for token in (
            'class="workspace-header"',
            'class="workspace-bar"',
            'id="workspace-summary-strip"',
            'class="workspace-drawer" id="control-drawer"',
            'id="canvas-intro"',
            'id="control-drawer-trigger"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

    def test_settings_markup_includes_sensitive_setting_controls(self):
        html = build_fixture_html(control_token="test-control-token")
        for token in (
            'data-menu-id="app-more-menu"',
            'data-menu-id="ai-target-menu"',
            'data-menu-id="language-select-menu"',
            'data-menu-id="sort-more-menu"',
            'data-menu-id="batch-more-menu"',
            'id="setting-token-status"',
            'id="setting-token-presence"',
            'id="setting-clear-token"',
            'id="setting-proxy-presence"',
            'id="setting-clear-proxy"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

        self.assertNotIn("setting-close-behavior", html)
        self.assertNotIn("隐藏到托盘", html)
        self.assertIn("主窗口关闭会直接退出程序", html)
        self.assertIn('"controlToken": "test-control-token"', html)


if __name__ == "__main__":
    unittest.main()
