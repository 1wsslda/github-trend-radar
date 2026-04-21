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


class RuntimeUIJSContractTests(unittest.TestCase):
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

    def test_prompt_profile_contract_uses_global_profile_state(self):
        for token in (
            'const PROMPT_PROFILE_ORDER = [',
            'const PROMPT_PROFILE_MENU_GROUPS = [',
            'const PROMPT_PROFILE_DEFINITIONS = {',
            'const PROMPT_PROFILE_LABELS = Object.fromEntries(',
            'const PROMPT_PROFILE_DESCRIPTIONS = Object.fromEntries(',
            'const VALID_PROMPT_PROFILES = new Set(PROMPT_PROFILE_ORDER);',
            'let promptProfile = normalizePromptProfile(localStorage.getItem("gtr-prompt-profile") || "j_full");',
            "let compareContext = null;",
            'function normalizePromptProfile(value){',
            'function promptProfileDefinition(value){',
            'function promptProfileLabel(value){',
            'function promptProfileDescription(value){',
            'function currentPromptProfileLabel(){',
            'function currentPromptProfileDescription(){',
            'function setPromptProfile(value){',
            'localStorage.setItem("gtr-prompt-profile", promptProfile);',
            'function syncPromptProfileUI(){',
            'document.querySelectorAll("[data-prompt-profile-label]").forEach(node => {',
            'document.querySelectorAll("[data-prompt-profile]").forEach(btn => {',
            'function buildRepoPrompt(repo, profile){',
            'function buildBatchPrompt(repos, title, batchIndex, batchCount, profile){',
            'function buildCollectionPrompt(repos, title, profile){',
            'function buildComparePrompt(a, b, detailA, detailB, profile){',
        ):
            with self.subTest(token=token):
                self.assertIn(token, JS)

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
