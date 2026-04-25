# GS-P1-018 OpenAI-compatible translation API

## 任务元信息

- 任务 ID：`GS-P1-018`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`1`
- 推荐 commit message：`feat(translation): use openai-compatible translation api`

## 标题

移除旧本机翻译 provider，新增显式 opt-in 的 OpenAI-compatible 翻译 API

## 摘要

- 本任务删除旧本机翻译 provider 路径，改为用户显式配置的 `openai_compatible` 翻译 provider。
- 默认翻译方式保持 `google`，避免破坏现有开箱体验。
- OpenAI-compatible 翻译只在 endpoint、model 和 API key 都完整时调用；失败、缺配置或空结果返回原文，不自动回退到 Google。
- AI 分析边界保持现状：只做 ChatGPT / Gemini 跳转、复制 Prompt 和手动保存 Insight，不新增内嵌 AI provider。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前翻译 provider 为 `google` 和旧本机翻译 provider。
- 旧本机翻译 provider 使用用户配置的 loopback `/api/generate` 风格 endpoint、`prompt` 字段和本机翻译服务名称。
- 设置 UI 暴露“本机翻译地址 / 本机模型名”。
- `sanitize_settings()` 会返回本地翻译 URL 和模型名。
- `GS-P2-002` 和 `docs/plans/0019-optional-local-translation-model.md` 已记录为完成，但本任务会取代它的方向，不回写历史状态为未完成。

## 目标

- 主要目标：新增 `openai_compatible` 翻译 provider，按 Chat Completions 兼容契约调用用户配置的完整 endpoint。
- 次要目标：API key 使用现有 DPAPI secret helper 本地加密保存；settings/bootstrap/diagnostics/export 不返回明文 key。
- 成功标准：
  - 默认 provider 仍是 `google`。
  - `openai_compatible` 请求体固定为 `model + messages + temperature: 0 + stream: false`。
  - 解析 `choices[0].message.content` 作为译文。
  - 远端 `https://...` endpoint 允许；loopback HTTP/HTTPS 允许；普通远端 `http://...` 拒绝。
  - 缺 key、缺 model、请求失败或空响应时返回原文，且不调用 Google。
  - cache key 包含 provider、endpoint、model、target_lang 和原文，但不包含 API key。

## 非目标

- 不实现 AI Insight provider。
- 不新增 `/api/ai/providers` 或应用内模型分析执行路径。
- 不调用 Responses API。
- 不支持自定义 prompt 模板市场。
- 不处理未跟踪文件 `最新prompt.md`。

## 用户影响

- 用户仍可不配置任何翻译 API，继续使用默认 Google Translate 路径。
- 需要自定义 OpenAI-compatible 翻译时，用户在设置里显式选择 provider，并填写 endpoint、model 和 API key。
- 旧的本机翻译服务字段会从设置 UI 消失。
- API key 保存后只显示是否已配置，不回显明文。

## 隐私与显式同意

- 涉及云 API、API Key 和用户待翻译文本外发。
- 只有用户主动选择 `openai_compatible` 并配置完整信息才会发出请求。
- 不完整配置、请求失败或空译文均返回原文，不回退到 Google，避免把用户预期只发往 API provider 的文本发给另一个服务。
- API Key 使用 DPAPI 加密保存；不进入 settings/bootstrap/diagnostics/export 明文 payload。

## 范围

### 范围内

- `src/gitsonar/runtime/settings.py`
- `src/gitsonar/runtime/translation.py`
- `src/gitsonar/runtime_ui/template.py`
- `src/gitsonar/runtime_ui/js/overlays.py`
- `tests/test_runtime_settings.py`
- `tests/test_runtime_translation.py`
- `tests/test_ui_js_smoke.py`
- `tests/test_runtime_ui_assets.py`
- README、SECURITY、ARCHITECTURE、ROADMAP、CHANGELOG、TASKS、Sprint、progress 和相关计划文档

### 范围外

- React / FastAPI / SQLite 迁移
- AI provider pipeline
- 真实 provider 选择器或隐私预览 UI
- 自动下载、启动或管理本机翻译服务

## 架构触点

- 翻译运行时：provider 选择、Chat Completions 请求、响应解析和缓存 key。
- 设置运行时：provider 字段、endpoint/model/key 归一化、DPAPI 存储、sanitize 输出。
- UI：设置弹窗字段和保存 payload。
- 文档：把“AI 只跳转；翻译可显式配置 API”的边界同步到用户和维护者文档。

## 数据模型

- 新字段：
  - `translation_provider`: `google | openai_compatible`
  - `translation_api_endpoint`
  - `translation_api_model`
  - `translation_api_key`
- 移除运行时使用：
  - `translation_local_url`
  - `translation_local_model`
- 导入 / 导出影响：
  - settings sanitize payload 只暴露 `has_translation_api_key`，不暴露明文 key。
  - 保存 settings 时加密 `translation_api_key`。

## API 与契约

- 现有 `GET /api/settings` 和 `POST /api/settings` 保持路径不变。
- `POST /api/settings` 新增字段：
  - `translation_provider`
  - `translation_api_endpoint`
  - `translation_api_model`
  - `translation_api_key`
  - `clear_translation_api_key`
- 错误行为：
  - 非 loopback 的远端 HTTP endpoint 返回设置保存错误。
  - loopback HTTP/HTTPS endpoint 和远端 HTTPS endpoint 可保存。

## 执行步骤

1. 写计划和任务追踪。
   预期结果：`GS-P1-018` 进入 `[~]`，计划文件存在。
   回滚路径：删除计划文件并恢复任务追踪行。
2. 写 RED 测试。
   预期结果：settings、translation、UI smoke 测试因缺少新字段和 provider 行为失败。
   回滚路径：删除新增测试断言。
3. 实现 settings 字段、endpoint 校验、DPAPI 保存和 sanitize。
   预期结果：settings 测试通过。
   回滚路径：恢复 `settings.py` 与对应测试。
4. 实现 OpenAI-compatible 翻译请求并删除旧本机翻译路径。
   预期结果：translation 测试通过，失败或空响应返回原文且不调用 Google。
   回滚路径：恢复 `translation.py` 与对应测试。
5. 更新设置 UI 和 JS 保存 payload。
   预期结果：UI smoke 测试通过，旧本机翻译字段不再出现。
   回滚路径：恢复模板、JS 和测试。
6. 更新文档和任务追踪。
   预期结果：README、SECURITY、ARCHITECTURE、ROADMAP、CHANGELOG、TASKS、Sprint 和 progress 一致。
   回滚路径：恢复文档 diff。
7. 运行验证。
   预期结果：聚焦 pytest、`rg` 文档检查和 `git diff --check` 完成。
   回滚路径：根据失败项逐步修正或回退相关小改动。

## 风险

- 技术风险：第三方 OpenAI-compatible endpoint 差异较大。本任务只支持 Chat Completions 常见契约，失败返回原文。
- 产品风险：用户可能误以为 AI 分析也接入了 API。本任务明确只影响翻译，AI 分析仍是 prompt handoff。
- 隐私 / 安全风险：API key 明文泄漏。通过 DPAPI 加密保存和 sanitize 只暴露布尔值缓解。
- 发布风险：旧本机翻译设置会被归一化回默认 `google`，用户需要重新配置 API provider。

## 验证

- 单元测试：
  - `python -m pytest tests/test_runtime_translation.py tests/test_runtime_settings.py tests/test_ui_js_smoke.py -q`
- 文档检查：
  - 按任务验收要求运行旧 provider 关键词检查，除已取代历史计划外不应再命中。
- 格式检查：
  - `git diff --check`
- 手动检查：
  - 设置 UI 不再出现旧本机翻译字段。
  - AI 目标菜单仍只保留 ChatGPT、Gemini 和复制 Prompt。

## 发布与回滚

- 增量发布：随设置和翻译运行时发布，默认 provider 仍是 `google`。
- 受控状态：`translation_provider` 是显式开关。
- 失败恢复：用户切回 `google`，或清空 API key；缺配置时运行时返回原文。

## 文档更新

- README / README.zh-CN
- CHANGELOG
- `docs/SECURITY.md`
- `docs/ARCHITECTURE.md`
- `docs/roadmap/ROADMAP.md`
- `TASKS.md`
- `docs/sprints/CURRENT_TOP10.md`
- `docs/progress/PROGRESS.md`
- `docs/plans/0019-optional-local-translation-model.md`

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 已完成 OpenAI-compatible 翻译 API、设置 UI、DPAPI Key 保存、文档同步和验证。 |
| `2026-04-25` | `[~]` | 创建计划，开始移除旧本机翻译 provider 并接入 OpenAI-compatible 翻译 API。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_translation.py tests/test_runtime_settings.py tests/test_ui_js_smoke.py tests/test_runtime_ui_assets.py -q`，55 passed，108 subtests passed。
- 文档检查：按任务验收要求运行旧 provider 关键词检查；最终只剩 `docs/plans/0019-optional-local-translation-model.md` 的“已取代”说明。
- 格式检查：`git diff --check` 退出码 0，仅输出 LF/CRLF 转换警告。
- 手动验证：设置 UI 合约测试确认旧字段消失，新 API Endpoint / Model / API Key / 清空 API Key 字段存在；AI 目标菜单未增加内嵌 provider。
- 尚未覆盖的缺口：真实第三方 provider 兼容性需要用户按各 provider endpoint 实测。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
- [x] 旧本机翻译 provider 运行时代码已移除
- [x] API key 不出现在 sanitize payload
