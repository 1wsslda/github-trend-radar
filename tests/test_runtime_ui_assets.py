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

    def test_workspace_header_omits_legacy_auxiliary_copy(self):
        html = build_fixture_html()

        self.assertIn('<h1 class="workspace-title">GitSonar</h1>', html)
        self.assertNotIn("GitHub Intelligence Desk", html)
        self.assertNotIn("Reading-first Workspace", html)
        self.assertNotIn('id="panel-summary"', html)

    def test_compact_workspace_shell_is_present(self):
        html = build_fixture_html(control_token="test-control-token")
        for token in (
            'class="workspace-header"',
            'class="workspace-bar"',
            'class="workspace-bar-shell"',
            'id="workspace-subnav"',
            'class="workspace-filter-group"',
            'class="workspace-action-group"',
            'class="workspace-context"',
            'id="workspace-summary-strip"',
            'class="workspace-drawer" id="control-drawer"',
            'id="canvas-intro"',
            'id="control-drawer-trigger"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

    def test_discovery_markup_uses_split_search_and_context_support(self):
        html = build_fixture_html()

        for token in (
            'data-menu-id="discover-ranking-menu"',
            'id="discover-run-note"',
            'id="discover-limit-copy"',
            'id="discover-auto-expand-note"',
            "开始搜索 · 综合排序",
            "会基于首轮命中的仓库名、Topics 和 README 补充相关词，覆盖更广，但会更慢。",
            "只按你输入的关键词直接搜索，返回更快、更可控，但可能漏掉相近项目。",
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

        self.assertNotIn('id="discover-limit"', html)
        self.assertNotIn('id="discover-ranking-profile"', html)
        self.assertNotIn('data-custom-select-for="discover-ranking-profile"', html)

    def test_discovery_split_state_hooks_are_present_in_assets(self):
        for token in (
            'rankingRoot.classList.toggle("is-idle", !discoveryBusy && !hasQuery);',
            'rankingRoot.classList.toggle("is-ready", !discoveryBusy && hasQuery);',
            'rankingRoot.classList.toggle("is-busy", discoveryBusy);',
        ):
            with self.subTest(js=token):
                self.assertIn(token, JS)

        for token in (
            ".discover-run-split.is-idle .split-main:disabled{",
            ".discover-run-split.is-busy .split-trigger{",
            "#discover-ranking-menu-panel{",
            "#discover-ranking-menu-panel .menu-item{",
            ".menu-item-copy{",
        ):
            with self.subTest(css=token):
                self.assertIn(token, CSS)

    def test_primary_nav_and_subnav_use_current_family_switching_contract(self):
        html = build_fixture_html()
        summary_section = html.split('<div class="workspace-summary"', 1)[1].split('<span class="workspace-ai-target"', 1)[0]
        analyze_section = html.split('id="analyze-visible-btn"', 1)[1].split('id="ai-target-trigger"', 1)[0]

        self.assertIn('class="workspace-summary">', html)
        self.assertIn('class="workspace-summary-copy"', html)
        self.assertIn('class="workspace-summary-line">已选', html)
        self.assertIn('class="workspace-ai-target"', html)
        self.assertNotIn('split-main-note', analyze_section)
        self.assertNotIn('data-ai-target-label', analyze_section)
        self.assertNotIn('aria-live="polite"', summary_section)
        self.assertNotIn('role="status"', summary_section)
        self.assertIn('function renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrendKey, activeLibraryKey){', JS)
        self.assertIn("onclick='setPrimaryPanel(\"trend\")'", JS)
        self.assertIn("onclick='setPrimaryPanel(\"library\")'", JS)
        self.assertNotIn('data-menu-id="nav-trend-menu"', JS)
        self.assertNotIn('data-menu-id="nav-library-menu"', JS)
        self.assertIn(".workspace-subnav-row{", CSS)
        self.assertIn(".workspace-action-group{", CSS)
        self.assertIn('.workspace-action-group > .action-split[data-menu-id="ai-target-menu"] .split-main,', CSS)

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
