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

    def test_build_html_keeps_control_token_payload_field(self):
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
            'class="workspace-nav"',
            'class="workspace-nav-shell"',
            'class="workspace-bar"',
            'class="workspace-content-shell workspace-bar-shell"',
            'class="workspace-control-stack"',
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
            "会基于首轮命中的仓库名、主题词和 README 补充相关词，覆盖更广，但会更慢。",
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

    def test_discovery_saved_view_helpers_use_draft_state_without_reusing_stale_run_metadata(self):
        for token in (
            "function currentDiscoveryDraftQuery(){",
            "function isDiscoveryDraftSyncedToLastRun(){",
            'query:String(discoverDraft.query || "").trim(),',
            "const shouldCarryRunMetadata = !discoveryBusy && isDiscoveryDraftSyncedToLastRun();",
            'last_run_at:shouldCarryRunMetadata ? String(discoveryState.last_run_at || completedQuery.last_run_at || "").trim() : "",',
            "last_result_count:shouldCarryRunMetadata ? discoveryResults().length : 0,",
            'if(String(discoverDraft.query || "").trim() && !isDiscoveryDraftSyncedToLastRun()) return "尚未开始";',
            "const draftQuery = currentDiscoveryDraftQuery();",
        ):
            with self.subTest(js=token):
                self.assertIn(token, JS)

    def test_discovery_limit_and_diagnostics_contracts_are_present(self):
        for token in (
            "function currentDiscoveryDraftLimit(){",
            "limit:rememberedQuery.query ? rememberedQuery.limit : legacyDraft.limit,",
            "discoverDraft.limit = currentDiscoveryLimit();",
            "limit:currentDiscoveryDraftLimit(),",
            'document.getElementById("diagnostics-modal").addEventListener("click", event => {',
            'if(event.target.id === "diagnostics-modal") closeDiagnostics();',
            "closeDiagnostics();",
        ):
            with self.subTest(js=token):
                self.assertIn(token, JS)

    def test_discovery_polling_uses_stable_preview_signatures_and_live_status_hooks(self):
        for token in (
            "function discoveryResultSignature(results){",
            "Keep this signature aligned with the fields surfaced by discovery top cards and repo cards.",
            'String(repo?.url || "")',
            'String(repo?.full_name || "")',
            'Number(repo?.rank || 0)',
            'Number(repo?.composite_score || 0)',
            'Number(repo?.relevance_score || 0)',
            'Number(repo?.hot_score || 0)',
            'Number(repo?.stars || 0)',
            'Number(repo?.forks || 0)',
            'String(repo?.language || "")',
            'String(repo?.description || "")',
            'String(repo?.description_raw || "")',
            "repo?.match_reasons",
            'id="discover-progress-stage"',
            'id="discover-progress-text"',
            'id="discover-progress-eta"',
            "function syncDiscoveryLiveStatus(){",
            'const previousResultsSignature = discoveryResultSignature(currentResults);',
            'const nextResultsSignature = discoveryResultSignature(renderableDiscoveryResults(job, currentResults));',
            "const hasTerminalStatus = isTerminalDiscoveryJob(job);",
            "const shouldRenderResults = hasTerminalStatus || previousResultsSignature !== nextResultsSignature;",
            "if(shouldRenderResults){",
            "syncDiscoveryLiveStatus();",
        ):
            with self.subTest(js=token):
                self.assertIn(token, JS)

    def test_selection_enter_motion_hooks_are_present_in_assets(self):
        for token in (
            "let lastSelectionSyncUrls = new Set(selectedUrls);",
            "function clearCardSelectionEnter(card){",
            "function playCardSelectionEnter(card){",
        ):
            with self.subTest(js=token):
                self.assertIn(token, JS)

        for token in (
            ".card.selectable::before,",
            ".card.selection-enter::before,",
            "@keyframes card-selection-sheen {",
            "animation:card-selection-sheen .68s var(--ease-smooth) 1 forwards;",
            "isolation:isolate;",
            "@keyframes badge-selection-enter {",
            "animation:badge-selection-enter .32s var(--ease-smooth) forwards;",
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
        self.assertIn('function renderPrimaryNav(activeFamily, activeTrend, discoverTab, libraryCount, updatesTab){', JS)
        self.assertIn('function renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrendKey, activeLibraryKey){', JS)
        self.assertIn("onclick='setPrimaryPanel(\"trend\")'", JS)
        self.assertIn("onclick='setPrimaryPanel(\"library\")'", JS)
        self.assertIn('class="workspace-primary-nav"', JS)
        self.assertIn('class="workspace-primary-link', JS)
        self.assertIn('class="workspace-primary-label"', JS)
        self.assertIn('class="workspace-primary-count"', JS)
        self.assertIn('class="workspace-subnav-link', JS)
        self.assertIn('class="workspace-subnav-label"', JS)
        self.assertNotIn('data-menu-id="nav-trend-menu"', JS)
        self.assertNotIn('data-menu-id="nav-library-menu"', JS)
        self.assertNotIn('class="nav-pill', JS)
        self.assertNotIn('workspace-subnav-pill', JS)
        self.assertIn(".workspace-subnav-row{", CSS)
        self.assertIn(".workspace-primary-link{", CSS)
        self.assertIn(".workspace-subnav-link{", CSS)
        self.assertIn(".workspace-action-group{", CSS)
        self.assertIn('.workspace-action-group > .action-split[data-menu-id="ai-target-menu"] .split-main,', CSS)

    def test_prompt_profile_menu_is_removed_from_workspace_header(self):
        html = build_fixture_html()

        for token in (
            'data-menu-id="prompt-profile-menu"',
            'id="prompt-profile-trigger"',
            'id="workspace-prompt-profile"',
            'data-prompt-profile=',
            "分析方式",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, html)

    def test_menu_panels_have_scrollable_viewport_clamps_for_tall_content(self):
        for token in (
            "max-height:min(420px, calc(100vh - 24px));",
            "overflow-y:auto;",
            "overscroll-behavior:contain;",
        ):
            with self.subTest(css=token):
                self.assertIn(token, CSS)

    def test_back_to_top_button_contract_replaces_runtime_nav_offset_contract(self):
        html = build_fixture_html()

        self.assertIn('id="workspace-back-to-top"', html)
        self.assertIn('aria-label="回到顶部"', html)
        self.assertIn(".workspace-back-to-top{", CSS)
        self.assertIn(".workspace-back-to-top.is-visible{", CSS)
        self.assertIn("body.has-batch-dock .workspace-back-to-top{", CSS)
        self.assertIn('function scrollWorkspaceToTop(behavior = "smooth"){', JS)
        self.assertIn("function syncBackToTopButton(){", JS)
        self.assertNotIn("--workspace-nav-offset", CSS)
        self.assertNotIn('page.style.setProperty("--workspace-nav-offset",', JS)

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
            'id="setting-translation-provider"',
            'id="setting-translation-local-url"',
            'id="setting-translation-local-model"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, html)

        self.assertNotIn("setting-close-behavior", html)
        self.assertNotIn("隐藏到托盘", html)
        self.assertIn("主窗口关闭会直接退出程序", html)
        self.assertIn('"controlToken": "test-control-token"', html)

    def test_top10_mvp_markup_contracts_are_present(self):
        html = build_fixture_html()

        for token in (
            'id="diagnostics-modal"',
            'onclick="openDiagnostics()"',
            "运行诊断",
            "AI Insight Schema MVP",
            "复制 Markdown 摘要",
            "保存当前视图",
            "为什么推荐",
        ):
            with self.subTest(token=token):
                self.assertIn(token, html if token.startswith("id=") or token.startswith("onclick=") or token == "运行诊断" else JS)


if __name__ == "__main__":
    unittest.main()
