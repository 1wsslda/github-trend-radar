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
    markers = [f"function {name}(", f"async function {name}("]
    start = -1
    for marker in markers:
        start = source.find(marker)
        if start != -1:
            break
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
    def test_tab_switch_closes_control_drawer(self):
        body = function_body(JS, "setPanel")
        self.assertIn("closeControlDrawer();", body)
        self.assertIn("render();", body)

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

    def test_workspace_nav_offset_is_computed_from_runtime_layout(self):
        body = function_body(JS, "applyWorkspaceNavOffset")
        self.assertIn('document.querySelector(".workspace-nav-shell")', body)
        self.assertIn('document.querySelector(".workspace-nav")', body)
        self.assertIn('getComputedStyle(navShell).top', body)
        self.assertIn('getComputedStyle(navSection).marginBottom', body)
        self.assertIn('page.style.setProperty("--workspace-nav-offset",', body)

    def test_render_tabs_rebuilds_primary_nav_and_runtime_offset(self):
        body = function_body(JS, "renderTabs")
        self.assertIn("renderPrimaryNav(activeFamily, activeTrend, discoverTab, libraryCount, updatesTab);", body)
        self.assertIn("renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrend?.key || \"\", activeLibrary?.key || \"\");", body)
        self.assertIn("observeWorkspaceNavOffset();", body)
        self.assertIn("syncWorkspaceNavOffset();", body)

    def test_render_pipeline_updates_shell_and_canvas(self):
        body = function_body(JS, "render")
        self.assertIn("syncWorkspaceCanvas();", body)
        self.assertIn("syncControlStates();", body)

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

    def test_prompt_profile_selection_is_persisted_and_rebuilds_compare_prompt(self):
        body = function_body(JS, "setPromptProfile")
        self.assertIn('promptProfile = normalizePromptProfile(value);', body)
        self.assertIn('localStorage.setItem("gtr-prompt-profile", promptProfile);', body)
        self.assertIn("if(compareContext){", body)
        self.assertIn("comparePrompt = buildComparePrompt(", body)
        self.assertIn("syncPromptProfileUI();", body)

    def test_close_compare_clears_cached_compare_prompt_state(self):
        body = function_body(JS, "closeCompare")
        self.assertIn('comparePrompt = "";', body)
        self.assertIn("compareContext = null;", body)
        self.assertIn('setOverlayVisible("compare-modal", false);', body)

    def test_batch_prompt_profiles_define_expected_limits(self):
        body = function_body(JS, "promptProfileBatchLimit")
        self.assertIn('if(activeProfile === "adopt") return 2;', body)
        self.assertIn('if(activeProfile === "understand") return 4;', body)
        self.assertIn("return 3;", body)

    def test_split_repo_prompts_uses_profile_aware_batching_and_length_draft(self):
        body = function_body(JS, "splitRepoPrompts")
        self.assertIn("const lengthLimit = Number.isFinite(Number(maxEncodedLength)) && Number(maxEncodedLength) > 0 ? Number(maxEncodedLength) : 2600;", body)
        self.assertIn("const batchLimit = Number.isFinite(Number(maxItemsPerBatch)) && Number(maxItemsPerBatch) > 0", body)
        self.assertIn(": promptProfileBatchLimit(activeProfile);", body)
        self.assertIn("const buildDraft = candidate => buildBatchPrompt(candidate, title, 1, 2, activeProfile);", body)
        self.assertIn("encodedLength > lengthLimit || candidate.length > batchLimit", body)

    def test_analysis_entrypoints_pass_current_prompt_profile(self):
        analyze_repo = function_body(JS, "analyzeRepo")
        analyze_visible = function_body(JS, "analyzeVisible")
        analyze_selected = function_body(JS, "analyzeSelected")
        open_compare = function_body(JS, "openCompareSelected")

        self.assertIn("buildRepoPrompt(repo, promptProfile)", analyze_repo)
        self.assertIn("splitRepoPrompts(", analyze_visible)
        self.assertIn("promptProfile,", analyze_visible)
        self.assertIn('splitRepoPrompts(repos, "已选仓库", undefined, undefined, promptProfile)', analyze_selected)
        self.assertIn("buildComparePrompt(repoA, repoB, detailA, detailB, promptProfile);", open_compare)


if __name__ == "__main__":
    unittest.main()
