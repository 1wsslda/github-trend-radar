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
            "const snapshot = {};",
            "const userState = {repo_records:{}, favorite_updates:[]};",
            "const discoveryState = {};",
            'const UPDATE_PANEL_KEY = "favorite-updates";',
            'const DISCOVER_PANEL_KEY = "discover";',
            JS_STATE,
            f"const repo = {json.dumps(repo, ensure_ascii=False)};",
            f"const result = {expression};",
            "console.log(JSON.stringify(result));",
        ]
    )
    completed = subprocess.run([node, "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)


def eval_js_function(source: str, signature: str, expression: str) -> object:
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("node is not available")
    name = signature.split("(", 1)[0]
    body = function_body(source, name)
    script = "\n".join(
        [
            f"function {signature}{{",
            body,
            "}",
            f"console.log(JSON.stringify({expression}));",
        ]
    )
    completed = subprocess.run([node, "-e", script], check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)


class RuntimeUIAnalysisExportTests(unittest.TestCase):
    def test_format_display_time_normalizes_ui_timestamps_without_mutating_unparseable_values(self):
        self.assertEqual(
            eval_js_function(JS, "formatDisplayTime(value)", 'formatDisplayTime("2026-04-23T10:11:12")'),
            "2026-04-23 10:11:12",
        )
        self.assertEqual(eval_js_function(JS, "formatDisplayTime(value)", 'formatDisplayTime("")'), "")
        self.assertEqual(
            eval_js_function(JS, "formatDisplayTime(value)", 'formatDisplayTime("bad-time")'),
            "bad-time",
        )

        zoned = eval_js_function(JS, "formatDisplayTime(value)", 'formatDisplayTime("2026-04-23T10:11:12Z")')
        self.assertRegex(zoned, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertNotIn("T", zoned)
        self.assertNotIn("Z", zoned)
        self.assertNotIn("/", zoned)

    def test_analysis_date_stamp_uses_local_calendar_date(self):
        body = function_body(JS, "analysisDateStamp")
        self.assertIn("now.getFullYear()", body)
        self.assertIn("now.getMonth() + 1", body)
        self.assertIn("now.getDate()", body)
        self.assertNotIn('toISOString().slice(0, 10)', body)

    def test_collection_prompt_and_markdown_cover_full_repo_list(self):
        body = function_body(JS, "buildCollectionPrompt")
        self.assertIn("repos.filter(Boolean)", body)
        self.assertIn('return buildCollectionPromptText(normalized, title, "");', body)

        body = function_body(JS, "buildCollectionPromptText")
        self.assertIn("${normalized.length}", body)
        self.assertIn('${normalized.map(collectionRepoLine).join("\\n")}', body)
        self.assertIn("collectionHardRules()", body)
        self.assertIn('promptSectionText("collection", "structure")', body)

        body = function_body(JS, "buildAnalysisMarkdown")
        self.assertIn("repos.filter(Boolean)", body)
        self.assertIn('normalized.flatMap((repo, index) => [collectionRepoLine(repo, index), ""])', body)
        self.assertIn('String(prompt || "").replace(/\\r\\n?/g, "\\n")', body)
        self.assertIn("formatDisplayTime(new Date())", body)
        self.assertNotIn("toISOString()", body)

    def test_analyze_repo_collection_prefers_single_prompt_then_exports_markdown(self):
        body = function_body(JS, "analyzeRepoCollection")
        self.assertIn("const prompt = buildCollectionPrompt(repos, title);", body)
        self.assertIn("if(canTransportAsSinglePrompt(prompt)){", body)
        self.assertIn("return openAiPrompts([prompt]);", body)
        self.assertIn("const markdown = buildAnalysisMarkdown(title, prompt, repos);", body)
        self.assertIn("await exportAnalysisMarkdown(markdown, filename);", body)
        self.assertIn("\\u5168\\u91cf\\u5185\\u5bb9\\u8fc7\\u957f", body)

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

    def test_import_user_state_file_strips_utf8_bom_before_json_parse(self):
        self.assertIn("function stripUtf8Bom(text)", JS)
        cleaned = eval_js_function(JS, "stripUtf8Bom(text)", 'stripUtf8Bom("\\ufeff{\\"ok\\":1}")')
        untouched = eval_js_function(JS, "stripUtf8Bom(text)", 'stripUtf8Bom("{\\"ok\\":1}")')
        self.assertEqual(cleaned, '{"ok":1}')
        self.assertEqual(untouched, '{"ok":1}')
        body = function_body(JS, "importUserStateFile")
        self.assertIn("JSON.parse(stripUtf8Bom(await file.text()))", body)

    def test_learning_prompt_scaffolds_are_present(self):
        self.assertIn('const LEARNING_PROMPT_SPEC = {', JS)
        self.assertIn("最值得借鉴的点", JS)
        self.assertIn("本轮学习路线建议", JS)
        self.assertIn("如果融合成你自己的版本，该怎么取舍", JS)
        self.assertNotIn("PROMPT_PROFILE", JS)
        self.assertNotIn("normalizePromptProfile", JS)

    def test_compare_prompt_is_learning_focused(self):
        body = function_body(JS, "buildComparePrompt")
        self.assertIn('promptSectionText("compare", "intro")', body)
        self.assertIn("compareResearchRules()", body)
        self.assertIn("compareHardRules()", body)
        self.assertIn("compareProfileFocus()", body)
        self.assertIn("compareProfileStructure()", body)
        self.assertIn("compareLengthGuidance()", body)
        self.assertIn("learnerGoalBlock()", body)

        self.assertIn("各自最值得借鉴的部分", JS)
        self.assertIn("各自不该照搬的部分", JS)
        self.assertIn("先重点学哪个，先做哪个部分", JS)

    def test_single_repo_prompt_output_uses_learning_constraints(self):
        prompt = eval_prompt_runtime('buildRepoPrompt(repo)')
        self.assertIn("先看仓库再分析", prompt)
        self.assertIn("联网能力不足", prompt)
        self.assertIn("最值得借鉴的设计 / 实现点", prompt)
        self.assertIn("不该照搬的部分与风险", prompt)
        self.assertIn("MVP 应该怎么拆", prompt)
        self.assertIn("建议的源码阅读顺序", prompt)
        self.assertIn("我的最终目标不是复述仓库，而是做出属于自己的版本", prompt)

    def test_batch_prompt_output_is_learning_first(self):
        prompt = eval_prompt_runtime('buildCollectionPrompt([repo], "当前候选项目")')
        self.assertIn("必须覆盖列表中的全部仓库", prompt)
        self.assertIn("当前未核验", prompt)
        self.assertIn("最值得学的点", prompt)
        self.assertIn("最值得借鉴的点", prompt)
        self.assertIn("本轮学习路线建议", prompt)
        self.assertNotIn("业务高管", prompt)


if __name__ == "__main__":
    unittest.main()
