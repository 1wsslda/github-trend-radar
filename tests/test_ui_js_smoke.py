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
        self.assertNotIn("syncPromptProfileUI();", body)

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

    def test_save_settings_includes_translation_provider_fields(self):
        body = function_body(JS, "saveSettings")
        self.assertIn('translation_provider:document.getElementById("setting-translation-provider").value,', body)
        self.assertIn('translation_api_endpoint:document.getElementById("setting-translation-api-endpoint").value,', body)
        self.assertIn('translation_api_model:document.getElementById("setting-translation-api-model").value,', body)
        self.assertIn('translation_api_key:document.getElementById("setting-translation-api-key").value,', body)
        self.assertIn('clear_translation_api_key:document.getElementById("setting-clear-translation-api-key").checked,', body)
        self.assertNotIn("translation_local_url", body)
        self.assertNotIn("translation_local_model", body)

    def test_poll_uses_safe_refresh_status_message(self):
        self.assertIn("function refreshStatusMessage(", JS)
        body = function_body(JS, "poll")
        self.assertIn("refreshStatusMessage(data)", body)
        self.assertNotIn('data.error || "已显示最新数据"', body)

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

    def test_menu_repositioning_noops_when_no_menu_is_open(self):
        self.assertIn("function hasOpenMenus(){", JS)
        body = function_body(JS, "repositionOpenMenus")

        self.assertIn("if(!hasOpenMenus()) return;", body)
        self.assertIn("if(menuRepositionFrame) return;", body)
        self.assertLess(
            body.index("if(!hasOpenMenus()) return;"),
            body.index("requestAnimationFrame"),
        )

    def test_internal_scroll_containers_do_not_reposition_menus(self):
        body = function_body(JS, "shouldSkipMenuScrollReposition")
        for token in (
            ".panel-body",
            ".overlay",
            ".menu-panel",
            ".select-menu",
            ".workspace-drawer",
            ".batch-dock-actions",
            ".workspace-primary-nav",
            ".workspace-subnav-row",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)
        self.assertIn("target.closest", body)

    def test_resize_batches_description_measurement_with_animation_frame(self):
        self.assertIn("function queueExpandableDescriptionsSync(scope = document, options = {}){", JS)
        self.assertIn("queueExpandableDescriptionsSync(document, {force:true});", JS)
        self.assertNotIn("syncExpandableDescriptions();\n  queueBackToTopButtonSync();", JS)

    def test_expandable_descriptions_skip_previously_measured_cards_until_forced(self):
        body = function_body(JS, "syncExpandableDescriptions")

        self.assertIn("const force = !!options.force;", body)
        self.assertIn('wrap.dataset.descMeasured === "true" && !force', body)
        self.assertIn('wrap.dataset.descMeasured = "true";', body)

    def test_repo_detail_fetch_uses_memory_cache_and_in_flight_deduplication(self):
        self.assertIn("const repoDetailsCache = new Map();", JS)
        self.assertIn("const repoDetailsInFlight = new Map();", JS)
        self.assertIn("function repoDetailsCacheKey(repo){", JS)
        body = function_body(JS, "fetchRepoDetails")

        for token in (
            "const cacheKey = repoDetailsCacheKey(repo);",
            "if(repoDetailsCache.has(cacheKey)) return repoDetailsCache.get(cacheKey);",
            "if(repoDetailsInFlight.has(cacheKey)) return repoDetailsInFlight.get(cacheKey);",
            "repoDetailsCache.set(cacheKey, data.details);",
            "repoDetailsInFlight.delete(cacheKey);",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_prompt_profile_state_is_removed_from_runtime(self):
        self.assertNotIn("function setPromptProfile(", JS)
        self.assertNotIn("syncPromptProfileUI()", JS)
        self.assertNotIn("gtr-prompt-profile", JS)
        self.assertNotIn("normalizePromptProfile", JS)

    def test_compare_overlay_keeps_learning_prompt_context(self):
        open_body = function_body(JS, "openCompareSelected")
        self.assertIn("compareContext = {repoA, repoB, detailA, detailB};", open_body)
        self.assertIn("buildComparePrompt(repoA, repoB, detailA, detailB);", open_body)
        self.assertIn("compareContext = null;", open_body)

        close_body = function_body(JS, "closeCompare")
        self.assertIn('comparePrompt = "";', close_body)
        self.assertIn("compareContext = null;", close_body)
        self.assertIn('setOverlayVisible("compare-modal", false);', close_body)

    def test_ai_insight_json_workflow_is_removed_but_prompt_handoff_remains(self):
        for removed_function in (
            "buildAi" + "InsightContext",
            "copyAi" + "InsightContext",
            "saveAi" + "Insight",
            "removeAi" + "Insight",
            "saveCurrentDetailAi" + "Insight",
            "clearCurrentDetailAi" + "Insight",
            "ai" + "InsightByUrl",
        ):
            with self.subTest(removed_function=removed_function):
                self.assertNotIn(f"function {removed_function}(", JS)

        for removed_text in (
            "AI Insight" + " Schema MVP",
            "RepoContext" + " JSON",
            "保存 Insight" + " JSON",
            "清除 Insight",
            "/api/ai-" + "insights",
            "/api/ai-" + "artifacts",
            "userState.ai_" + "insights",
        ):
            with self.subTest(removed_text=removed_text):
                self.assertNotIn(removed_text, JS)

        self.assertIn("function buildRepoPrompt(", JS)
        self.assertIn("function buildCollectionPrompt(", JS)
        self.assertIn("function buildComparePrompt(", JS)
        self.assertIn('"/api/chatgpt/open"', JS)
        self.assertIn('"/api/analysis/export-markdown"', JS)

    def test_tag_and_note_edit_actions_do_not_use_browser_prompt(self):
        tag_body = function_body(JS, "editRepoTags")
        note_body = function_body(JS, "editRepoNote")

        self.assertNotIn("window.prompt", tag_body)
        self.assertNotIn("window.prompt", note_body)
        self.assertIn("focusDetailOrganizer", tag_body)
        self.assertIn("focusDetailOrganizer", note_body)

    def test_note_autosave_uses_repo_annotations_without_rerendering_detail(self):
        body = function_body(JS, "saveDetailRepoNote")

        self.assertIn("persistRepoAnnotation", body)
        self.assertIn("{note:nextNote}", body)
        self.assertIn('setDetailNoteSaveStatus("saving"', body)
        self.assertIn('setDetailNoteSaveStatus("saved"', body)
        self.assertIn('setDetailNoteSaveStatus("failed"', body)
        self.assertNotIn("renderCurrentDetailPanel", body)
        self.assertNotIn("render();", body)

    def test_tag_editor_enforces_limit_and_refreshes_visible_cards(self):
        normalize_body = function_body(JS, "normalizeRepoTagList")
        save_body = function_body(JS, "saveRepoTagsFromDetail")

        self.assertIn("MAX_REPO_TAGS", normalize_body)
        self.assertIn("tags.length >= MAX_REPO_TAGS", normalize_body)
        self.assertIn("persistRepoAnnotation", save_body)
        self.assertIn("{tags:nextTags}", save_body)
        self.assertIn("refreshRepoAnnotationSurfaces", save_body)
        self.assertIn("refreshVisibleCards();", function_body(JS, "refreshRepoAnnotationSurfaces"))

    def test_detail_readme_preview_contract_uses_helper_in_detail_panel(self):
        body = function_body(JS, "renderCurrentDetailPanel")

        self.assertIn("${renderDetailReadmeSection(repo, detail)}", body)
        self.assertNotIn('detail.readme_summary || detail.readme_summary_raw || "暂无 README 摘要"', body)

    def test_detail_readme_preview_helper_defaults_to_preview_then_expands(self):
        body = function_body(JS, "renderDetailReadmeSection")

        for token in (
            "DETAIL_README_PREVIEW_CHARS",
            "readme.length > DETAIL_README_PREVIEW_CHARS",
            "detailReadmeExpandedUrls.has(url)",
            "readme.slice(0, DETAIL_README_PREVIEW_CHARS)",
            "hiddenCount",
            "展开全文",
            "收起预览",
            "detail-readme-section",
            "detail-readme-block",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_detail_readme_toggle_keeps_state_in_frontend_session_only(self):
        self.assertIn("const detailReadmeExpandedUrls = new Set();", JS)
        body = function_body(JS, "toggleDetailReadmeExpanded")

        self.assertIn("detailReadmeExpandedUrls.add(key);", body)
        self.assertIn("detailReadmeExpandedUrls.delete(key);", body)
        self.assertIn("renderCurrentDetailPanel();", body)
        self.assertIn("nextBody.scrollTop = scrollTop;", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("userState", body)

    def test_open_detail_resets_detail_body_scroll_for_new_repo(self):
        self.assertIn("function resetDetailBodyScroll(){", JS)
        body = function_body(JS, "openDetail")

        self.assertGreaterEqual(body.count("resetDetailBodyScroll();"), 2)

    def test_copy_markdown_summary_uses_full_detail_readme(self):
        copy_body = function_body(JS, "copyRepoMarkdownSummary")
        summary_body = function_body(JS, "buildRepoMarkdownSummary")

        self.assertIn("const detail = repo.owner && repo.name ? await fetchRepoDetails(repo) : null;", copy_body)
        self.assertIn("buildRepoMarkdownSummary(repo, detail)", copy_body)
        self.assertIn("target.readme_summary || target.readme_summary_raw", summary_body)
        self.assertNotIn("DETAIL_README_PREVIEW_CHARS", summary_body)


if __name__ == "__main__":
    unittest.main()
