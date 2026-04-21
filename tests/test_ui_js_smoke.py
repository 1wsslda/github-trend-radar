from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_ui.assets import JS


def function_body(source: str, name: str) -> str:
    marker = f"function {name}("
    start = source.find(marker)
    if start == -1:
        raise AssertionError(f"missing function {name}")
    brace_start = source.find("{", start)
    if brace_start == -1:
        raise AssertionError(f"missing opening brace for {name}")

    depth = 0
    in_single = False
    in_double = False
    in_template = False
    escaped = False
    for index in range(brace_start, len(source)):
        char = source[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and (in_single or in_double or in_template):
            escaped = True
            continue
        if char == "'" and not in_double and not in_template:
            in_single = not in_single
            continue
        if char == '"' and not in_single and not in_template:
            in_double = not in_double
            continue
        if char == "`" and not in_single and not in_double:
            in_template = not in_template
            continue
        if in_single or in_double or in_template:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start + 1 : index]
    raise AssertionError(f"unterminated function {name}")


class UIJSSmokeTests(unittest.TestCase):
    def test_tab_switch_closes_control_drawer_and_scrolls_to_top(self):
        body = function_body(JS, "setPanel")
        self.assertIn("closeControlDrawer();", body)
        self.assertIn("render();", body)
        self.assertIn('scrollWorkspaceToTop("auto");', body)

    def test_selection_summary_keeps_discovery_guard_for_batch_dock(self):
        body = function_body(JS, "refreshSelectionSummary")
        self.assertIn("const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;", body)
        self.assertIn("const showBatchDock = !isDiscoverPanel && selected > 0;", body)

    def test_sync_card_selection_state_only_animates_new_selections(self):
        body = function_body(JS, "syncCardSelectionState")
        self.assertIn("const wasSelected = lastSelectionSyncUrls.has(url);", body)
        self.assertIn("if(!selected) clearCardSelectionEnter(card);", body)
        self.assertIn("if(selected && !wasSelected) playCardSelectionEnter(card);", body)
        self.assertIn("lastSelectionSyncUrls = new Set(selectedUrls);", body)

    def test_play_card_selection_enter_restarts_and_cleans_up_animation(self):
        body = function_body(JS, "playCardSelectionEnter")
        self.assertIn("clearCardSelectionEnter(card);", body)
        self.assertIn("void card.offsetWidth;", body)
        self.assertIn('event.animationName !== "card-selection-sheen"', body)
        self.assertIn('card.classList.add("selection-enter");', body)

    def test_scroll_workspace_to_top_respects_reduced_motion(self):
        body = function_body(JS, "scrollWorkspaceToTop")
        self.assertIn('window.matchMedia("(prefers-reduced-motion: reduce)").matches', body)
        self.assertIn('const nextBehavior = prefersReducedMotion ? "auto" : behavior;', body)
        self.assertIn("window.scrollTo({top:0, behavior: nextBehavior});", body)
        self.assertIn("queueBackToTopButtonSync();", body)

    def test_back_to_top_button_visibility_uses_scroll_threshold(self):
        body = function_body(JS, "syncBackToTopButton")
        self.assertIn('document.getElementById("workspace-back-to-top")', body)
        self.assertIn("window.scrollY >= 480", body)
        self.assertIn('button.classList.toggle("is-visible", isVisible);', body)
        self.assertIn('button.tabIndex = isVisible ? 0 : -1;', body)

    def test_render_tabs_rebuilds_primary_nav_without_runtime_offset_sync(self):
        body = function_body(JS, "renderTabs")
        self.assertIn("renderPrimaryNav(activeFamily, activeTrend, discoverTab, libraryCount, updatesTab);", body)
        self.assertIn("renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrend?.key || \"\", activeLibrary?.key || \"\");", body)
        self.assertNotIn("observeWorkspaceNavOffset();", body)
        self.assertNotIn("syncWorkspaceNavOffset();", body)

    def test_render_pipeline_updates_shell_canvas_and_back_to_top_state(self):
        body = function_body(JS, "render")
        self.assertIn("syncWorkspaceCanvas();", body)
        self.assertIn("syncControlStates();", body)
        self.assertIn("syncBackToTopButton();", body)
        self.assertIn("syncPromptProfileUI();", body)

    def test_filter_state_and_sort_updates_rerender_without_forcing_scroll_reset(self):
        body = function_body(JS, "setStateFilter")
        self.assertIn("render();", body)
        self.assertNotIn("scrollWorkspaceToTop", body)

        body = function_body(JS, "setSortPrimary")
        self.assertIn("render();", body)
        self.assertNotIn("scrollWorkspaceToTop", body)

    def test_boot_wires_back_to_top_button_and_scroll_listener(self):
        self.assertIn('document.getElementById("workspace-back-to-top")?.addEventListener("click", () => {', JS)
        self.assertIn("scrollWorkspaceToTop();", JS)
        self.assertIn('window.addEventListener("scroll", () => {', JS)
        self.assertIn("queueBackToTopButtonSync();", JS)

    def test_token_status_validation_uses_dedicated_settings_endpoint(self):
        body = function_body(JS, "validateTokenStatus")
        self.assertIn('"/api/settings/token-status"', body)
        self.assertIn("const fingerprint = tokenValue ? `override:${tokenValue}` : (settings.has_github_token ? \"saved\" : \"empty\");", body)
        self.assertIn("fingerprint === lastTokenStatusFingerprint && lastTokenStatusResult", body)
        self.assertIn('applyTokenStatus({state:"checking"', body)
        self.assertIn('document.getElementById("setting-clear-token")?.checked', body)
        self.assertIn("JSON.stringify(tokenValue ? {github_token:tokenValue} : {})", body)
        self.assertIn("lastTokenStatusFingerprint = fingerprint;", body)
        self.assertIn("applyTokenStatus(lastTokenStatusResult);", body)

    def test_open_settings_reuses_cached_token_status_when_possible(self):
        body = function_body(JS, "openSettings")
        self.assertIn("validateTokenStatus();", body)
        self.assertNotIn("validateTokenStatus(undefined, {force:true});", body)

    def test_local_api_requests_attach_runtime_control_token(self):
        body = function_body(JS, "localApiOptions")
        self.assertIn("new Headers(next.headers || {})", body)
        self.assertIn("headers.set(CONTROL_TOKEN_HEADER, controlToken);", body)
        self.assertIn("next.headers = headers;", body)

    def test_menu_positioning_clamps_tall_panels_to_available_viewport_height(self):
        body = function_body(JS, "positionMenu")
        self.assertIn("const naturalHeight = panel.scrollHeight;", body)
        self.assertIn("const spaceBelow =", body)
        self.assertIn("const spaceAbove =", body)
        self.assertIn('panel.style.maxHeight = `${fittedHeight}px`;', body)
        self.assertIn('panel.style.overflowY = naturalHeight > fittedHeight ? "auto" : "";', body)

    def test_prompt_profile_selection_is_persisted_and_rebuilds_compare_prompt(self):
        body = function_body(JS, "setPromptProfile")
        self.assertIn("promptProfile = normalizePromptProfile(value);", body)
        self.assertIn('localStorage.setItem("gtr-prompt-profile", promptProfile);', body)
        self.assertIn("if(compareContext){", body)
        self.assertIn("comparePrompt = buildComparePrompt(", body)
        self.assertIn("syncPromptProfileUI();", body)

    def test_compare_overlay_keeps_profile_aware_prompt_context(self):
        open_body = function_body(JS, "openCompareSelected")
        self.assertIn("compareContext = {repoA, repoB, detailA, detailB};", open_body)
        self.assertIn("buildComparePrompt(repoA, repoB, detailA, detailB, promptProfile);", open_body)
        self.assertIn("compareContext = null;", open_body)

        close_body = function_body(JS, "closeCompare")
        self.assertIn('comparePrompt = "";', close_body)
        self.assertIn("compareContext = null;", close_body)
        self.assertIn('setOverlayVisible("compare-modal", false);', close_body)


if __name__ == "__main__":
    unittest.main()
