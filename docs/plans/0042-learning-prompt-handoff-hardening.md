# GS-P1-022 Learning Prompt Handoff Hardening

## 任务元信息

- 任务 ID：`GS-P1-022`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：用户指定插队任务
- 推荐 commit message：`feat(ai): harden learning prompt handoff`

## 标题

`优化学习型 AI 项目分析提示词`

## 摘要

- 本任务把应用内单仓库、批量仓库和双仓库对比 Prompt 从要求堆叠型改为任务流程型。
- 现在做是因为当前 Prompt 对“先核验仓库、再拆源码、最后给复刻路线”的约束不够强，容易让外部 AI 直接泛泛分析。
- 做完后，用户主动点击 ChatGPT / Gemini / 复制 Prompt 时，会得到更适合学习、源码阅读和 MVP 复刻的中文提示词。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：AI 分析是 prompt handoff，不调用内嵌 provider。
- 当前技术形态：`runtime_ui` 中 Python 维护 Prompt 规格，再注入前端 JS 拼装单仓库、批量和对比 Prompt。
- 已知痛点：Prompt 已偏学习型，但核验状态、证据标注、MVP 拆解和可选 7 天计划规则不够明确。
- 现有约束：不恢复旧 AI Insight JSON，不新增 AI provider，不改变 HTTP API、状态字段、存储或外发边界。
- 需要检查的文件或区域：`src/gitsonar/runtime_ui/prompt_profiles.py`、`src/gitsonar/runtime_ui/js/state.py`、`src/gitsonar/runtime_ui/js/actions.py`、相关 UI 测试。

## 目标

- 主要目标：强化应用内学习型 Prompt，让外部 AI 按“核验仓库 -> 解释问题 -> 拆源码 -> 提炼借鉴 -> MVP 复刻”输出。
- 次要目标：让批量和对比 Prompt 与单仓库 Prompt 保持同一学习取向。
- 成功标准：三类入口都保留现有 handoff 流程，Prompt 明确要求核验证据、可信度标签、MVP、源码阅读顺序和核心行动建议。

## 非目标

- 不实现内嵌 AI provider、云 API、Agent、RAG 或 artifact 缓存。
- 不修改 `/api/chatgpt/open`、`/api/analysis/export-markdown`。
- 不恢复 prompt profile 菜单或运行时 profile 状态。
- 不处理未跟踪文件 `最新prompt.md`。

## 用户影响

- 用户主动触发 AI 分析时，复制或打开的 Prompt 更稳定地要求外部 AI 先核验、再分析、再给学习和复刻路线。
- 批量分析仍保留过长内容导出 Markdown 的 fallback。
- ChatGPT / Gemini / copy-only 目标菜单保持不变。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据：涉及现有 prompt handoff 文案，但不新增任何 provider 或自动调用。
- 是否有数据离开本机：行为不变，只有用户主动点击外部 AI 目标或复制 Prompt 时发生。
- 是否需要显式 opt-in：沿用现有用户主动点击交接。
- 是否需要用户可见的确认或预览：不新增；本任务只优化交接文本。

## 范围

### 范围内

- 重写 `LEARNING_PROMPT_SPEC` 中单仓库、批量和对比 Prompt 文案。
- 更新 Prompt 合约测试。
- 同步任务追踪文档。

### 范围外

- AI provider、云端模型调用、隐私预览 API、artifact 缓存、状态 schema 和导入 / 导出格式。

## 架构触点

- 涉及的运行时模块：`runtime_ui.prompt_profiles`。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：AI 交接生成的 Prompt 内容变化，按钮和菜单不变。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 要新增或修改的端点：无。
- 请求 / 响应结构：无变化。
- 错误行为：无变化。
- 兼容性说明：保留现有 `buildRepoPrompt`、`buildCollectionPrompt`、`buildComparePrompt` 前端入口。

## 执行步骤

1. 补测试
   预期结果：focused 测试先因缺少核验状态、证据规则和强化对比约束失败。
   回滚路径：撤回测试断言。
2. 更新 Prompt 规格
   预期结果：单仓库、批量和对比 Prompt 均包含新的学习型流程约束。
   回滚路径：恢复旧 `LEARNING_PROMPT_SPEC`。
3. 同步任务追踪
   预期结果：`TASKS.md`、`CURRENT_TOP10.md`、`PROGRESS.md` 和本计划记录一致。
   回滚路径：撤回任务追踪新增行和本计划文件。

## 风险

- 技术风险：Prompt 变长后部分 URL 自动填入可能触发既有“提示词过长则复制后手动粘贴”路径。
- 产品风险：过度约束会让输出偏长。通过将 7 天计划设为可选来控制默认篇幅。
- 隐私 / 安全风险：不新增外发路径；风险与现有 prompt handoff 相同。
- 发布风险：低，仅文案和测试改动。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_ui_analysis_export.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py -q`
- 集成测试：`python -m pytest -q`
- 手动检查：单仓库、批量和对比入口生成 Prompt 聚焦学习、证据和复刻路线。
- 性能或可靠性检查：不适用。
- 需要关注的日志 / 诊断信号：无新增。

## 发布与回滚

- 如何增量发布：随当前桌面应用版本发布。
- 是否需要开关或受控状态：不需要。
- 如果失败，用户如何恢复：回滚 `LEARNING_PROMPT_SPEC` 文案即可，现有 API 和状态不受影响。

## 文档更新

- 需要更新的文档：本计划、`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。
- 需要更新的用户可见文案：Prompt 文案本身。
- 需要更新的内部维护说明：无。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-26` | `[x]` | 已完成 Prompt 文案、测试和任务追踪同步。 |
| `2026-04-26` | `[~]` | 已创建计划并开始 TDD 实现。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_runtime_ui_analysis_export.py -q`，先失败 4 项，确认旧 Prompt 缺少核验状态、证据规则、四类可信度标签和强化后的批量 / 对比约束。
  - GREEN targeted：`python -m pytest tests/test_runtime_ui_analysis_export.py -q`，11 passed。
  - 回归切片：`python -m pytest tests/test_runtime_ui_analysis_export.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py -q`，75 passed，285 subtests passed。
  - 全量：`python -m pytest -q`，228 passed，312 subtests passed。
  - Diff 检查：`git diff --check`，退出码 0，仅有 LF/CRLF 工作区提示。
- 手动验证：尚未启动 WebView 手动点击验证；已用 JS Prompt runtime 测试覆盖单仓库和批量 Prompt 内容，对比 Prompt 合约由 JS 文案断言覆盖。
- 尚未覆盖的缺口：未实际打开 ChatGPT / Gemini 外部目标。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
