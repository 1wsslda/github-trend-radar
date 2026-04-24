from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_ui.assets import JS
from gitsonar.runtime_ui import prompt_profiles as prompt_profiles_module
from gitsonar.runtime_ui.js import prompt_profiles as js_prompt_profiles_module


class RuntimeUIJSContractTests(unittest.TestCase):
    def test_legacy_prompt_profile_python_exports_remain_available_for_compat(self):
        for attr in (
            "DEFAULT_PROMPT_PROFILE",
            "PROMPT_PROFILE_DEFINITIONS",
            "PROMPT_PROFILE_DEFINITIONS_JSON",
            "PROMPT_PROFILE_LEGACY_ALIASES",
            "PROMPT_PROFILE_LEGACY_ALIASES_JSON",
            "PROMPT_PROFILE_MENU_GROUPS",
            "PROMPT_PROFILE_MENU_GROUPS_JSON",
            "PROMPT_PROFILE_ORDER",
            "PROMPT_PROFILE_ORDER_JSON",
            "render_prompt_profile_menu_panel",
            "LEARNING_PROMPT_SPEC",
            "LEARNING_PROMPT_SPEC_JSON",
        ):
            with self.subTest(attr=attr):
                self.assertTrue(hasattr(prompt_profiles_module, attr))

        self.assertEqual(prompt_profiles_module.DEFAULT_PROMPT_PROFILE, "j_full")
        self.assertIn("j_full", prompt_profiles_module.PROMPT_PROFILE_DEFINITIONS)
        self.assertIn("a_general", prompt_profiles_module.PROMPT_PROFILE_DEFINITIONS)
        self.assertTrue(callable(prompt_profiles_module.render_prompt_profile_menu_panel))

    def test_legacy_prompt_profile_js_module_path_remains_importable(self):
        self.assertIsInstance(js_prompt_profiles_module.JS, str)
        self.assertIn("function normalizePromptProfile(value){", js_prompt_profiles_module.JS)
        self.assertIn("const PROMPT_PROFILE_DEFINITIONS = {", js_prompt_profiles_module.JS)

    def test_aggregate_js_has_no_duplicate_named_functions(self):
        pattern = re.compile(r"(?m)^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
        names = pattern.findall(JS)
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        self.assertEqual(duplicates, [], f"duplicate function definitions found: {duplicates}")

    def test_primary_nav_contract_uses_subnav_and_shared_ai_target_sync(self):
        for token in (
            'function preferredFamilyPanel(family){',
            'function setPrimaryPanel(family){',
            'function renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrendKey, activeLibraryKey){',
            'onclick=\'setPanel(${JSON.stringify(tab.key)})\'',
            'document.querySelectorAll("[data-ai-target-label]").forEach(node => {',
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS)

    def test_request_json_sends_control_token_through_shared_options(self):
        for token in (
            "function localApiOptions(options){",
            "headers.set(CONTROL_TOKEN_HEADER, controlToken);",
            "async function requestJson(url, options, errorMessage = \"无法连接本地服务\"){",
            "resp = await fetch(url, localApiOptions(options));",
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS)

    def test_discovery_cluster_contract_is_present(self):
        for token in (
            "function discoveryClusters(){",
            "last_clusters:Array.isArray(raw.last_clusters)",
            "主题分组",
            "repo.cluster_label",
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS)

    def test_discovery_cluster_map_contract_is_present(self):
        for token in (
            "function renderDiscoveryClusterMap(){",
            "function selectDiscoveryCluster(clusterId){",
            "主题地图",
            "选中本组",
            "discover-cluster-map",
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS)

    def test_learning_prompt_contract_uses_single_prompt_spec(self):
        for token in (
            'const LEARNING_PROMPT_SPEC = {',
            "let compareContext = null;",
            'function learningPromptSection(name){',
            'function promptSectionText(section, key){',
            'function learnerGoalBlock(){',
            'function learningLanguageRules(extraLines = []){',
            'function buildRepoPrompt(repo){',
            'function buildBatchPrompt(repos, title, batchIndex, batchCount){',
            'function buildCollectionPrompt(repos, title){',
            'function compareResearchRules(){',
            'function buildComparePrompt(a, b, detailA, detailB){',
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS)

        for token in (
            "PROMPT_PROFILE",
            "normalizePromptProfile",
            "promptProfileDefinition",
            "promptProfileLabel",
            "promptProfileDescription",
            "setPromptProfile",
            "syncPromptProfileUI",
            "gtr-prompt-profile",
        ):
            with self.subTest(absent=token):
                self.assertNotIn(token, JS)

    def test_aggregate_js_passes_node_syntax_check_when_available(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
            handle.write(JS)
            temp_path = Path(handle.name)
        try:
            subprocess.run([node, "--check", str(temp_path)], check=True, capture_output=True, text=True)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
