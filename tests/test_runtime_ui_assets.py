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


def build_fixture_html() -> str:
    return build_html(
        app_name="GitSonar",
        snapshot={"daily": [], "weekly": [], "monthly": []},
        user_state={"repo_records": {}, "favorite_updates": []},
        discovery_state={},
        settings={"result_limit": 25, "default_sort": "stars"},
        periods=[
            {"key": "daily", "label": "今天"},
            {"key": "weekly", "label": "本周"},
            {"key": "monthly", "label": "本月"},
        ],
        states=[
            {"key": "favorites", "label": "收藏"},
            {"key": "watch_later", "label": "稍后看"},
            {"key": "read", "label": "已读"},
            {"key": "ignored", "label": "忽略"},
        ],
        note="ready",
        pending=False,
    )


class RuntimeUILayoutSmokeTests(unittest.TestCase):
    def test_runtime_ui_public_exports_are_available(self):
        self.assertIn("function render()", JS)
        self.assertIn(".workspace-header{", CSS)

    def test_compact_workspace_shell_is_present(self):
        html = build_fixture_html()
        for token in (
            'class="workspace-header"',
            'class="workspace-bar"',
            'id="panel-summary"',
            'id="workspace-summary-strip"',
            'class="workspace-drawer" id="control-drawer"',
            'id="canvas-intro"',
            'id="control-drawer-trigger"',
            'id="control-drawer-list"',
            'id="control-drawer-discover"',
            'id="control-drawer-updates"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

    def test_layout_and_render_paths_no_longer_reference_removed_dom_ids(self):
        html = build_fixture_html()
        stale_dom_tokens = {
            "filter-panel": 'id="filter-panel"',
            "filter-toggle": 'id="filter-toggle"',
            "discover-module": 'id="discover-module"',
            "discover-shell": 'id="discover-shell"',
        }
        for stale_id, dom_token in stale_dom_tokens.items():
            with self.subTest(stale_id=stale_id):
                self.assertNotIn(dom_token, html)
                self.assertNotIn(stale_id, JS)

    def test_assets_aggregate_split_modules(self):
        self.assertIn("const DISCOVER_PANEL_KEY = \"discover\";", JS)
        self.assertIn("function syncControlDrawer(){", JS)
        self.assertIn("@media (max-width:759px){", CSS)
        self.assertIn(".workspace-drawer{", CSS)

    def test_settings_markup_and_menu_roots_match_current_contract(self):
        html = build_fixture_html()
        for token in (
            'data-menu-id="app-more-menu"',
            'data-menu-id="ai-target-menu"',
            'data-menu-id="language-select-menu"',
            'data-menu-id="sort-more-menu"',
            'data-menu-id="discover-ranking-profile-menu"',
            'data-menu-id="batch-more-menu"',
            'data-custom-select-for="language"',
            'data-custom-select-for="discover-ranking-profile"',
            'id="setting-token-status"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

        for token in (
            'toggleMenu(event, "nav-trend-menu")',
            'toggleMenu(event, "nav-library-menu")',
            "batch-more-menu",
            "sort-more-menu",
            "state-more-toggle",
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS + html)

        self.assertNotIn("setting-close-behavior", html)
        self.assertNotIn("隐藏到托盘", html)
        self.assertIn("主窗口关闭会直接退出程序", html)


if __name__ == "__main__":
    unittest.main()
