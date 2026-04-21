from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_ui.assets import JS
from gitsonar.runtime_ui.js.prompt_profiles import JS as JS_PROMPT_PROFILES
from gitsonar.runtime_ui.js.state import JS as JS_STATE


def function_body(source: str, name: str) -> str:
    marker = f"function {name}("
    start = source.find(marker)
    if start == -1:
        marker = f"async function {name}("
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


def eval_prompt_runtime(expression: str) -> object:
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("node is not available")
    repo = {
        "full_name": "acme/agent-stack",
        "owner": "acme",
        "name": "agent-stack",
        "url": "https://github.com/acme/agent-stack",
        "description": "Multi-agent workflow runner for enterprise ops",
        "description_raw": "Multi-agent workflow runner for enterprise ops",
        "language": "Python",
        "stars": 4242,
        "forks": 128,
        "gained": 96,
        "gained_text": "+96",
        "growth_source": "trending",
        "rank": 1,
        "source_label": "GitHub 趋势",
        "source_key": "daily",
    }
    script = "\n".join(
        [
            'const promptProfile = "j_full";',
            "const snapshot = {};",
            "const userState = {repo_records:{}, favorite_updates:[]};",
            "const discoveryState = {};",
            'const UPDATE_PANEL_KEY = "favorite-updates";',
            'const DISCOVER_PANEL_KEY = "discover";',
            JS_PROMPT_PROFILES,
            JS_STATE,
            f"const repo = {json.dumps(repo, ensure_ascii=False)};",
            f"const result = {expression};",
            "console.log(JSON.stringify(result));",
        ]
    )
    completed = subprocess.run([node, "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)


class RuntimeUIAnalysisExportTests(unittest.TestCase):
    def test_analysis_date_stamp_uses_local_calendar_date(self):
        body = function_body(JS, "analysisDateStamp")
        self.assertIn("now.getFullYear()", body)
        self.assertIn("now.getMonth() + 1", body)
        self.assertIn("now.getDate()", body)
        self.assertNotIn('toISOString().slice(0, 10)', body)

    def test_collection_prompt_and_markdown_cover_full_repo_list(self):
        body = function_body(JS, "buildCollectionPrompt")
        self.assertIn("repos.filter(Boolean)", body)
        self.assertIn('return buildCollectionPromptText(normalized, title, profile, "");', body)

        body = function_body(JS, "buildCollectionPromptText")
        self.assertIn("${promptProfileLabel(activeProfile)}", body)
        self.assertIn("${normalized.length}", body)
        self.assertIn('${normalized.map(collectionRepoLine).join("\\n")}', body)
        self.assertIn("必须覆盖列表中的全部仓库", body)

        body = function_body(JS, "buildAnalysisMarkdown")
        self.assertIn("repos.filter(Boolean)", body)
        self.assertIn("normalized.flatMap((repo, index) => [collectionRepoLine(repo, index), \"\"])", body)
        self.assertIn('String(prompt || "").replace(/\\r\\n?/g, "\\n")', body)

    def test_analyze_repo_collection_prefers_single_prompt_then_exports_markdown(self):
        body = function_body(JS, "analyzeRepoCollection")
        self.assertIn("const prompt = buildCollectionPrompt(repos, title, promptProfile);", body)
        self.assertIn("if(canTransportAsSinglePrompt(prompt)){", body)
        self.assertIn("return openAiPrompts([prompt]);", body)
        self.assertIn("const markdown = buildAnalysisMarkdown(title, prompt, repos);", body)
        self.assertIn("await exportAnalysisMarkdown(markdown, filename);", body)
        self.assertIn('\\u5168\\u91cf\\u5185\\u5bb9\\u8fc7\\u957f', body)

    def test_multi_prompt_transport_is_rejected_for_non_copy_targets(self):
        body = function_body(JS, "openAiPrompts")
        self.assertIn('queue.join("\\n\\n-----\\n\\n")', body)
        self.assertIn("if(queue.length > 1){", body)
        self.assertIn('toast("\\u5f53\\u524d AI \\u76ee\\u6807\\u53ea\\u652f\\u6301\\u5355\\u6761\\u63d0\\u793a\\u8bcd', body)
        self.assertIn("body:JSON.stringify({mode:target, prompt:queue[0]})", body)
        self.assertNotIn("queue[queue.length - 1]", body)

    def test_multi_repo_entrypoints_keep_full_visible_and_selected_sets(self):
        visible_body = function_body(JS, "analyzeVisible")
        self.assertIn("const repos = visibleRepos();", visible_body)
        self.assertNotIn(".slice(0, 20)", visible_body)
        self.assertIn("gitsonar-analysis-visible-", visible_body)

        selected_body = function_body(JS, "analyzeSelected")
        self.assertIn("const repos = selectedRepos();", selected_body)
        self.assertIn("gitsonar-analysis-selected-", selected_body)

    def test_profile_specific_batch_prompt_scaffolds_are_present(self):
        focus_body = function_body(JS, "batchProfileFocus")
        self.assertIn('promptProfileSectionConfig(profile, "collection", DEFAULT_COLLECTION_PROMPT_CONFIG);', focus_body)

        structure_body = function_body(JS, "batchProfileStructure")
        self.assertIn('promptProfileSectionConfig(profile, "collection", DEFAULT_COLLECTION_PROMPT_CONFIG);', structure_body)
        self.assertIn("DEFAULT_COLLECTION_PROMPT_CONFIG.structure", structure_body)
        self.assertIn("评分总表", JS)
        self.assertIn("对比矩阵", JS)

    def test_compare_prompt_is_profile_aware(self):
        body = function_body(JS, "buildComparePrompt")
        self.assertIn("const activeProfile = normalizePromptProfile(profile);", body)
        self.assertIn("${promptProfileLabel(activeProfile)}", body)
        self.assertIn("${compareProfileFocus(activeProfile)}", body)
        self.assertIn("${compareProfileStructure(activeProfile)}", body)

        focus_body = function_body(JS, "compareProfileFocus")
        self.assertIn('promptProfileSectionConfig(profile, "compare", DEFAULT_COMPARE_PROMPT_CONFIG);', focus_body)
        self.assertIn("README、Issue、Pull Request、License 和最近活跃度", JS)
        self.assertIn("更适合做内部工具、客户产品或试点项目", JS)
        self.assertIn("离正式上线更近", JS)
        self.assertIn("老板 1 分钟能看完", JS)

    def test_single_repo_prompt_output_uses_profile_specific_constraints(self):
        prompts = eval_prompt_runtime(
            """({
              general: buildRepoPrompt(repo, "a_general"),
              deep: buildRepoPrompt(repo, "b_deep"),
              full: buildRepoPrompt(repo, "j_full")
            })"""
        )
        self.assertIn("不要假装掌握仓库中没有给出的信息", prompts["general"])
        self.assertIn("它是“拿来学”的，还是“拿来直接用”的", prompts["general"])
        self.assertIn("README", prompts["deep"])
        self.assertIn("Pull Request", prompts["deep"])
        self.assertIn("学习资料", prompts["full"])
        self.assertIn("星标高只代表关注度，不代表可上线", prompts["full"])

    def test_prompt_profile_aliases_and_invalid_values_fall_back_to_default_profile(self):
        result = eval_prompt_runtime(
            """({
              fit: normalizePromptProfile("fit"),
              understand: normalizePromptProfile("understand"),
              adopt: normalizePromptProfile("adopt"),
              invalid: normalizePromptProfile("not-a-profile"),
              invalidPrompt: buildRepoPrompt(repo, "not-a-profile")
            })"""
        )
        self.assertEqual(result["fit"], "j_full")
        self.assertEqual(result["understand"], "e4_detail")
        self.assertEqual(result["adopt"], "e3_adoption")
        self.assertEqual(result["invalid"], "j_full")
        self.assertIn("执行摘要", result["invalidPrompt"])
        self.assertIn("星标高只代表关注度，不代表可上线", result["invalidPrompt"])


if __name__ == "__main__":
    unittest.main()
