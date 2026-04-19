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
        self.assertIn('${normalized.map(collectionRepoLine).join("\\n")}', body)
        self.assertIn("${normalized.length}", body)
        self.assertIn("\\u5fc5\\u987b\\u8986\\u76d6", body)

        body = function_body(JS, "buildAnalysisMarkdown")
        self.assertIn("repos.filter(Boolean)", body)
        self.assertIn("normalized.flatMap((repo, index) => [collectionRepoLine(repo, index), \"\"])", body)
        self.assertIn('String(prompt || "").replace(/\\r\\n?/g, "\\n")', body)

    def test_analyze_repo_collection_prefers_single_prompt_then_exports_markdown(self):
        body = function_body(JS, "analyzeRepoCollection")
        self.assertIn("const prompt = buildCollectionPrompt(repos, title);", body)
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


if __name__ == "__main__":
    unittest.main()
