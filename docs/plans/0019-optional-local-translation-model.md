# 可选本地翻译模型支持计划

## 任务元信息

- 任务 ID：`GS-P2-002`
- 优先级：`P2`
- 当前状态：`[x]`
- Sprint 候选排名：`8`
- 推荐 commit message：`feat: add optional local translation provider`

## 标题

`可选本地翻译模型支持`

## 摘要

- 这个任务在现有翻译链路中增加显式可选的本地 Ollama 类翻译 provider。
- 现在做是因为 P0/P1 和仓库地图基础已经完成，P2 可以补离线和隐私增强能力。
- 做完后用户可以继续默认使用当前 Google Translate 公共接口，也可以主动选择只把翻译请求发给本机 loopback 模型服务。

## 战略映射

- 战略文档：
  - `docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：
  - `docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：
  - `docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`

## 当前状态

- 当前行为：`runtime/translation.py` 固定调用 Google Translate 公共接口。
- 当前技术形态：翻译运行时由 `runtime/app.py` 装配，设置由 `runtime/settings.py` 归一化并保存，UI 设置弹窗只包含 Token、代理、刷新和端口。
- 已知痛点：隐私敏感用户无法选择本机模型；中文关键词转英文和描述翻译都会依赖外部公共接口。
- 现有约束：不能默认下载模型；不能默认启用本地模型；不能把云 provider 当默认；不能引入新后台任务系统。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime/translation.py`
  - `src/gitsonar/runtime/settings.py`
  - `src/gitsonar/runtime/app.py`
  - `src/gitsonar/runtime_ui/template.py`
  - `src/gitsonar/runtime_ui/js/overlays.py`
  - `tests/test_runtime_translation.py`
  - `tests/test_runtime_settings.py`
  - `tests/test_runtime_ui_assets.py`
  - `tests/test_ui_js_smoke.py`

## 目标

- 主要目标：增加 `google` / `local_ollama` 两种翻译 provider 设置，默认保持 `google`。
- 次要目标：本地 provider 只允许 loopback URL，并要求用户配置模型名后才发请求。
- 成功标准：
  - 默认设置行为与现有 Google Translate 兼容。
  - 用户选择 `local_ollama` 且配置模型名后，翻译通过本机 Ollama `/api/generate` 类接口完成。
  - 非 loopback 本地翻译 URL 不允许保存。
  - 本地 provider 失败或未配置模型时返回原文，不回退到 Google，避免隐私预期被破坏。

## 非目标

- 不下载、安装或管理本地模型。
- 不新增 AI provider 框架。
- 不接入云翻译 API。
- 不改变发现搜索、详情缓存或状态 JSON 结构的兼容性。
- 不移除现有 Google Translate 路径。

## 用户影响

- 设置弹窗新增翻译 provider 选择和本地模型配置字段。
- 默认用户无感知，现有翻译行为不变。
- 隐私敏感用户可以显式选择本机模型；配置错误时翻译会保守返回原文。

## 隐私与显式同意

- 默认仍沿用当前外部 Google Translate 行为，文档中已有说明。
- 本地模型模式必须由用户显式选择。
- 本地模型 URL 只允许 `127.0.0.1`、`localhost` 或 `::1`。
- 不保存 API Key 或模型凭据，不把本地模型配置当敏感字段回显之外处理。

## 范围

### 范围内

- 设置归一化、保存和前端设置表单。
- 翻译运行时 provider 选择、Ollama 请求和缓存键。
- 自动化测试和任务追踪文档。

### 范围外

- 模型安装向导。
- Ollama 诊断项。
- AI Insight provider。
- 云翻译 provider 市场。

## 架构触点

- 涉及的运行时模块：`runtime/settings.py`、`runtime/translation.py`、`runtime/app.py`。
- HTTP / API 变更：复用 `/api/settings`，不新增端点。
- 状态 / 持久化变更：新增设置字段，旧 `settings.json` 可按默认值归一化。
- UI 变更：设置弹窗新增翻译 provider 与本地模型字段。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：
  - `translation_provider`
  - `translation_local_url`
  - `translation_local_model`
- 新文件或新表：无。
- 迁移需求：无；旧设置文件缺少字段时使用默认值。
- 导入 / 导出影响：设置仍保存在本地 `settings.json`，用户状态导入 / 导出不受影响。

## API 与契约

- 要新增或修改的端点：无，复用 `/api/settings`。
- 请求 / 响应结构：
  - `/api/settings` 响应新增翻译设置字段。
  - `/api/settings` 保存时接受同名字段。
- 错误行为：
  - 本地翻译 URL 非 loopback 时，保存设置失败并返回中文错误。
  - 本地 provider 未配置模型名时，翻译返回原文且不请求外部服务。
- 兼容性说明：旧客户端忽略新增字段；旧设置文件可读取。

## 执行步骤

1. 第一步：写失败测试。
   预期结果：本地 provider、设置字段和 UI 字段测试失败。
   回滚路径：删除新增测试。
2. 第二步：实现设置字段。
   预期结果：设置可归一化、保存、暴露，并拒绝非 loopback URL。
   回滚路径：回退 `runtime/settings.py`。
3. 第三步：实现本地翻译 provider。
   预期结果：`local_ollama` 使用本机模型请求，失败时返回原文。
   回滚路径：回退 `runtime/translation.py` 和 `runtime/app.py`。
4. 第四步：接入设置 UI。
   预期结果：用户可以在设置弹窗中切换 provider 并填写本地 URL / 模型名。
   回滚路径：回退 UI 模板和 JS。
5. 第五步：验证并更新进度。
   预期结果：相关测试通过，任务追踪文档一致。
   回滚路径：回退本任务所有改动。

## 风险

- 技术风险：不同 Ollama 模型输出格式可能包含额外解释，需要提示词约束为只输出译文。
- 产品风险：本地模型质量不稳定，可能影响翻译准确性。
- 隐私 / 安全风险：如果允许非 loopback URL 会造成数据外发，所以必须拒绝。
- 发布风险：低；不新增依赖，不改变默认路径。

## 验证

- 单元测试：
  - `python -m pytest tests/test_runtime_translation.py tests/test_runtime_settings.py -q`
- UI 合约测试：
  - `python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`
- 集成测试：
  - `python -m pytest tests/test_runtime_http.py -q`
- 手动检查：
  - 打开设置，确认翻译 provider 和本地模型字段可见。
  - 默认 `Google Translate` 模式下保存设置后现有行为不变。
  - 切到本地模型，填 loopback URL 和模型名后运行中文关键词发现。
- 性能或可靠性检查：
  - 本地 provider 失败时应快速回退原文，不重试到 Google。
- 需要关注的日志 / 诊断信号：
  - 翻译失败不会输出原文敏感内容到日志。

## 发布与回滚

- 如何增量发布？随应用设置一起发布，默认不启用本地 provider。
- 是否需要开关或受控状态？`translation_provider` 就是开关。
- 如果失败，用户如何恢复？在设置中切回 `Google Translate` 或清空本地模型名。

## 文档更新

- 需要更新的文档：`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`、`docs/SECURITY.md`
- 需要更新的用户可见文案：设置弹窗翻译 provider 说明。
- 需要更新的内部维护说明：本计划文件。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已新增可选本机 Ollama 类翻译 provider、设置 UI 和 loopback 校验，并完成验证。 |
| `2026-04-24` | `[~]` | 已创建计划，准备按 TDD 实现。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_runtime_translation.py tests/test_runtime_settings.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`，50 passed，106 subtests passed。
  - `python -m pytest tests/test_runtime_translation.py tests/test_runtime_settings.py tests/test_runtime_http.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`，88 passed，110 subtests passed。
- 手动验证：尚未启动桌面应用；已通过 UI 合约测试确认设置弹窗包含翻译 provider、loopback URL 和模型名字段，且保存设置会提交这些字段。
- 尚未覆盖的缺口：未连接真实 Ollama 服务验证模型输出质量；这是本地环境和模型选择问题，不影响默认 Google Translate 行为。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
