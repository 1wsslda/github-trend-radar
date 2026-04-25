# GS-P1-019 Remove AI Insight JSON Workflow

## 任务元信息

- 任务 ID：`GS-P1-019`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`1`
- 推荐 commit message：`refactor(ai): remove manual insight json workflow`

## 标题

移除 AI Insight JSON 手动保存工作流

## 摘要

- 本任务彻底移除详情页里的 AI Insight schema 面板、RepoContext payload、结构化 Insight 保存和清除工作流。
- 现在做是为了把 AI 方向收回到实际使用的 prompt handoff：单仓库、批量、对比提示词，ChatGPT / Gemini 跳转，复制 Prompt，Markdown 摘要导出。
- 完成后应用不再维护本地 legacy insight 状态字段、AI artifact 缓存、列表端点和手动 JSON schema；旧 `user_state.json` 中的 legacy insight 字段会在加载或导入后被忽略，并在后续保存时自然消失。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前详情抽屉有手动 AI Insight JSON 面板。
- 当前前端包含 `buildAiInsightContext`、`copyAiInsightContext`、`saveAiInsight`、`removeAiInsight`、`saveCurrentDetailAiInsight`、`clearCurrentDetailAiInsight`。
- 当前 runtime 注册 legacy insight 保存、删除和 artifact 列表端点。
- 当前 state schema/store 暴露并导出 legacy insight 状态字段与对应保存、删除、列表 helper。
- 当前 SQLite dry-run 仍统计 `ai_artifacts`。

## 目标

- 主要目标：删除手动 Insight JSON 保存/缓存能力。
- 次要目标：保留现有 prompt handoff、ChatGPT / Gemini / 复制 Prompt 目标菜单和 Markdown 摘要导出。
- 成功标准：
  - UI 不再出现 AI Insight schema 面板、RepoContext payload、结构化 Insight 保存和清除入口。
  - legacy insight 保存、删除和 artifact 列表端点不再注册。
  - 默认 user state 和导出 payload 不再包含 legacy insight 状态字段。
  - 导入或加载含旧 legacy insight 字段的 payload 时忽略该字段。
  - SQLite dry-run 不再统计 `ai_artifacts`。

## 非目标

- 不删除单仓库、批量、对比提示词生成逻辑。
- 不删除 `/api/chatgpt/open`。
- 不删除 `/api/analysis/export-markdown`。
- 不实现新的 AI provider、云 API、Agent 或本地模型调用。
- 不写破坏性迁移脚本。
- 不处理未跟踪文件 `最新prompt.md`。

## 用户影响

- 仓库详情抽屉会变短，不再提供手动粘贴 Insight JSON 的文本框。
- 用户仍可复制 Markdown 摘要、打开 GitHub、生成分析提示词并发送到 ChatGPT / Gemini 或复制 Prompt。
- 旧本地 legacy insight 数据不会再显示、导出或继续维护。

## 隐私与显式同意

- 本任务减少本地 AI artifact 持久化面，不新增任何外发。
- ChatGPT / Gemini 仍只在用户主动触发 prompt handoff 时打开或复制内容。
- 未来重新做 AI 必须另起任务，从 prompt 或显式 opt-in provider 重新设计，不能默认复用这套手动 JSON 面板。

## 范围

### 范围内

- `src/gitsonar/runtime/ai_insight.py`
- `src/gitsonar/runtime/state_schema.py`
- `src/gitsonar/runtime/state_store.py`
- `src/gitsonar/runtime/state.py`
- `src/gitsonar/runtime/http.py`
- `src/gitsonar/runtime/app.py`
- `src/gitsonar/runtime/sqlite_migration.py`
- `src/gitsonar/runtime_ui/js/actions.py`
- `src/gitsonar/runtime_ui/js/constants.py`
- `src/gitsonar/runtime_ui/js/overlays.py`
- `src/gitsonar/runtime_ui/js/state.py`
- 相关 tests、README、SECURITY、ARCHITECTURE、ROADMAP、CHANGELOG、TASKS、Sprint、progress 和历史计划说明

### 范围外

- React / FastAPI / SQLite 实际迁移
- AI provider pipeline
- Prompt 生成逻辑重写
- GitHub、翻译、诊断、更新中心等无关功能

## 架构触点

- 运行时模块：删除 `runtime/ai_insight.py`，从 state/http/app wiring 中移除 AI insight 依赖。
- HTTP / API 变更：删除 legacy insight 保存、删除和 artifact 列表端点。
- 状态 / 持久化变更：不再把 legacy insight 状态字段作为默认、导入、导出或合并字段。
- UI 变更：详情抽屉删除手动 JSON 面板；保留 Markdown 摘要和 GitHub 打开按钮。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 移除字段：legacy insight user-state 字段
- 移除表 / dry-run 统计：`ai_artifacts`
- 迁移需求：无破坏性迁移脚本；旧 JSON 字段加载 / 导入后被忽略。
- 导入 / 导出影响：导出不再包含 legacy insight 状态字段。

## API 与契约

- 删除端点：
  - legacy artifact list endpoint
  - legacy insight save endpoint
  - legacy insight delete endpoint
- 保留端点：
  - `POST /api/chatgpt/open`
  - `POST /api/analysis/export-markdown`
- 兼容说明：旧客户端调用删除的端点会得到普通 `404`，不保留兼容 shim。

## 执行步骤

1. 写计划和任务追踪。
   预期结果：`GS-P1-019` 进入 `[~]`，计划文件存在。
   回滚路径：删除计划文件并恢复任务追踪行。
2. 写 RED 测试。
   预期结果：state、HTTP、UI、SQLite 测试因仍存在旧能力而失败。
   回滚路径：删除新增测试断言。
3. 移除 state schema/store 的 legacy insight 状态字段和 artifact helper。
   预期结果：默认、加载、导入、导出均忽略旧字段。
   回滚路径：恢复 `state_schema.py`、`state_store.py` 和对应测试。
4. 移除 HTTP/app wiring 和 `runtime/ai_insight.py`。
   预期结果：旧 API 不再注册，模块不再被 import。
   回滚路径：恢复路由、注入参数和模块文件。
5. 移除详情抽屉手动 JSON UI 和前端 helper。
   预期结果：旧面板和函数名不再出现在 JS；prompt handoff 与 Markdown 摘要仍保留。
   回滚路径：恢复 UI JS 片段。
6. 更新 SQLite dry-run。
   预期结果：schema 与 dry-run 不再包含 `ai_artifacts`。
   回滚路径：恢复 dry-run schema 和测试。
7. 更新文档和任务追踪。
   预期结果：README、SECURITY、ARCHITECTURE、ROADMAP、CHANGELOG、TASKS、Sprint、progress 和历史计划说明一致。
   回滚路径：恢复文档 diff。
8. 运行验证。
   预期结果：指定 pytest、残留关键词检查和 `git diff --check` 完成。
   回滚路径：根据失败项修正或回退对应小改动。

## 风险

- 技术风险：旧 legacy insight 字段仍被某条导入/导出路径带出。用 state 和 HTTP 测试覆盖。
- 产品风险：用户误以为 AI 分析被删除。文档和 UI 验证必须明确 prompt handoff 保留。
- 隐私 / 安全风险：残留 API 或 artifact 列表仍暴露本地 AI JSON。用路由测试和全文检索覆盖。
- 发布风险：旧本地 Insight 数据不再可见；本任务选择忽略并自然淘汰，不做迁移恢复。

## 验证

- 单元 / 集成测试：
  - `python -m pytest tests/test_runtime_state.py tests/test_runtime_http.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_analysis_export.py tests/test_sqlite_migration.py -q`
- 残留检查：
  - 运行本任务的 AI Insight JSON 工作流残留关键词检查，确认旧 UI 文案、旧 API path 和旧状态字段不再出现在运行时代码、测试和公开文档中。
- 格式检查：
  - `git diff --check`
- 手动检查：
  - 详情抽屉保留 `复制 Markdown 摘要` 和 `打开 GitHub`。
  - ChatGPT / Gemini / copy 目标菜单仍存在。

## 发布与回滚

- 增量发布：删除 UI、API 和 state 持久化路径；无新配置开关。
- 回滚：恢复本任务涉及的 state/http/UI 文件和 `runtime/ai_insight.py`，旧 JSON 字段仍可被旧版本读取。
- 失败恢复：用户如需要旧 Insight JSON，只能用旧版本读取旧 `user_state.json`；当前版本不提供迁移工具。

## 文档更新

- README / README.zh-CN
- CHANGELOG
- `docs/SECURITY.md`
- `docs/ARCHITECTURE.md`
- `docs/roadmap/ROADMAP.md`
- `TASKS.md`
- `docs/sprints/CURRENT_TOP10.md`
- `docs/progress/PROGRESS.md`
- `docs/plans/0010-ai-insight-schema-mvp.md`
- `docs/plans/0015-ai-artifact-lifecycle-cache.md`

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 已完成 UI/API/state/sqlite 删除、文档同步和验证。 |
| `2026-04-25` | `[~]` | 创建计划，开始移除 AI Insight JSON 手动保存工作流。 |

## 验证记录

- RED：新增测试后确认旧 state/API/UI 仍存在，失败点符合预期。
- 已运行测试：`python -m pytest tests/test_runtime_state.py tests/test_runtime_http.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_analysis_export.py tests/test_sqlite_migration.py -q`，103 passed，164 subtests passed。
- 残留检查：旧 UI 文案、旧 API path 和旧状态字段关键词无匹配。
- 格式检查：`git diff --check` 退出码 0，仅输出 LF/CRLF 转换警告。
- 手动验证：详情抽屉保留 `复制 Markdown 摘要` 和 `打开 GitHub`；AI 目标菜单保留 ChatGPT / Gemini / copy。
- 尚未覆盖的缺口：未提供旧 Insight JSON 的迁移导出工具；本任务按计划忽略旧字段并让后续保存自然淘汰。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
- [x] 旧 AI Insight JSON UI 已移除
- [x] 旧 AI Insight API 已移除
- [x] 旧 legacy insight 状态字段加载 / 导入后被忽略
