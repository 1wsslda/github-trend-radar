# GS-P1-017 AI provider opt-in 设计

## 任务元信息

- 任务 ID：`GS-P1-017`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`5`
- 推荐 commit message：`docs(ai): design opt-in provider pipeline`

## 标题

AI provider opt-in 设计与本地 Ollama / OpenAI-compatible pipeline

## 摘要

- 当前 GitSonar 的 AI 能力是 prompt handoff、copy-only prompt 和手动保存结构化 Insight artifact。
- 本任务只做设计：定义 provider 分层、显式 opt-in、隐私预览、artifact 可追溯、失败回退和后续实施步骤。
- 本任务不实现 provider、不保存 API Key、不调用本地或云端模型。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`
- 既有 AI 基础：
  - `docs/plans/0010-ai-insight-schema-mvp.md`
  - `docs/plans/0015-ai-artifact-lifecycle-cache.md`
  - `src/gitsonar/runtime/ai_insight.py`

## 当前状态

- 当前行为：用户点击分析入口时，应用生成 prompt 并打开 ChatGPT / Gemini 或复制提示词；结构化 Insight 需要用户手动粘贴保存。
- 当前技术形态：本地 HTTP API + JSON 状态 + `gitsonar.repo_insight.v1` artifact metadata。
- 已知痛点：后续接入 provider 前，缺少统一的 opt-in、隐私预览、provider 配置和调用审计边界。
- 现有约束：
  - 默认不能启用云 provider。
  - 不能默认发送 repo、README、notes、tags、updates 或 Token。
  - 不能把 AI 输出自动写入用户状态，除非用户确认保存。
  - 实施 OpenAI-compatible provider 前必须再次查阅官方当前 API 文档，避免写死过期契约。

## 目标

- 主要目标：写清 AI provider opt-in 的目标架构和安全边界。
- 次要目标：定义本地 Ollama-style、OpenAI-compatible local endpoint、cloud OpenAI-compatible endpoint 的分层策略。
- 成功标准：设计明确“关闭 / prompt handoff / 本地 provider / 云 provider”四种模式，并写清隐私预览、Key 存储、artifact 生命周期和回滚。

## 非目标

- 不新增 provider 代码。
- 不新增 `/api/ai/providers` 或 `/api/ai/repo-insight`。
- 不修改设置 UI。
- 不保存或迁移 API Key。
- 不调用 OpenAI、Ollama、LocalAI 或任何兼容接口。

## 用户影响

- 用户可见行为：无直接 UI 变化。
- 保持不变：现有 ChatGPT / Gemini prompt handoff、copy-only 和手动 Insight JSON 保存继续可用。
- 后续价值：为将来的显式 opt-in 内嵌分析打安全地基。

## 隐私与显式同意

- 本任务不外发任何数据。
- 未来 provider 必须默认关闭。
- 调用前必须显示“将发送字段”预览，并允许用户取消。
- 云 provider 需要单独启用、单独保存 Key、单独标注网络目标。
- 本地 provider 只允许 loopback，除非后续有单独计划扩展远端自托管场景。
- 不发送 GitHub Token、代理凭据、本地路径、诊断原始日志或未脱敏异常。

## 范围

### 范围内

- 设计 provider 模式和配置字段。
- 设计隐私预览 payload。
- 设计 artifact 输入 hash、provider、model、source snapshot 追踪。
- 设计失败回退和用户确认保存流程。
- 更新 `TASKS.md`、`CURRENT_TOP10.md`、`PROGRESS.md`、`ROADMAP.md`、`ARCHITECTURE.md`、`SECURITY.md`、README 和 CHANGELOG。

### 范围外

- 真实 provider 调用。
- API Key 输入和 DPAPI 存储。
- AI 结果自动应用到标签、笔记或状态。
- Agent / 工具调用 / RAG。
- OpenAI 具体模型选择或价格策略。

## 架构触点

- 未来运行时模块：`src/gitsonar/runtime_ai/`
  - `providers.py`
  - `context_builder.py`
  - `privacy.py`
  - `openai_compatible.py`
  - `local_ollama.py`
  - `artifacts.py`
  - `schemas.py`
- HTTP / API 变更：本任务不新增；未来可能新增 provider 列表、预览、执行和 artifact 查询端点。
- 状态 / 持久化变更：本任务不新增；未来设置需要 DPAPI 加密 provider secret。
- UI 变更：本任务不新增；未来需要设置、预览确认、结果保存确认。
- 后台任务变更：本任务不新增；未来 provider 调用应进入 Job/Event runtime。

## 数据模型

- 本任务不新增状态字段。
- 未来建议字段：
  - `ai_provider_mode`: `off | prompt_handoff | local | cloud`
  - `ai_provider_id`
  - `ai_provider_base_url`
  - `ai_provider_model`
  - `ai_provider_key_ref`
  - `ai_provider_enabled_at`
  - `ai_privacy_preview_required`
- Provider secret 必须 DPAPI 加密，且不进入 diagnostics/bootstrap/export 明文 payload。

## API 与契约

未来建议端点，不在本任务实现：

- `GET /api/ai/providers`
- `POST /api/ai/preview`
- `POST /api/ai/repo-insight`
- `POST /api/ai/update-digest`
- `POST /api/ai/compare`
- `POST /api/ai/artifacts/save`

建议响应契约：

- `preview` 只返回将发送字段、字段来源、敏感字段排除结果和估算大小，不发起模型调用。
- `repo-insight` 等执行端点必须要求 loopback + control token + provider enabled + preview accepted。
- provider 失败只能返回用户安全摘要，原始错误按既有脱敏日志规则处理。

## Provider 模式设计

| 模式 | 行为 | 网络边界 | 默认状态 |
|---|---|---|---|
| `off` | 不展示内嵌 provider 执行入口，只保留当前 prompt handoff。 | 无新增网络调用。 | 默认 |
| `prompt_handoff` | 继续生成可复制 prompt 或打开外部 ChatGPT / Gemini。 | 由用户主动打开外部目标。 | 当前行为 |
| `local` | 调用用户显式配置的 loopback provider，例如 Ollama / LocalAI / OpenAI-compatible localhost。 | 只允许 `127.0.0.1`、`localhost`、`::1`。 | 关闭 |
| `cloud` | 调用用户显式配置的 OpenAI-compatible HTTPS endpoint。 | 只在用户配置 Key、启用 provider、确认预览后调用。 | 关闭 |

Provider 启用必须是分层的：

1. 用户选择 provider 模式。
2. 用户填写 endpoint、model 和必要凭据。
3. 应用校验 endpoint 边界，本地 provider 默认只允许 loopback。
4. 首次调用前展示隐私预览。
5. 用户确认后才创建 job 并执行 provider。
6. provider 输出先进入临时结果预览，用户确认后才保存 artifact。

## 隐私预览设计

`POST /api/ai/preview` 的未来 payload 建议只使用本地上下文构建，不调用模型：

```json
{
  "task": "repo_insight",
  "provider_mode": "local",
  "provider_id": "local_ollama",
  "model": "example-model",
  "fields": [
    {"name": "repo.full_name", "source": "repo_record", "included": true},
    {"name": "repo.description", "source": "repo_record", "included": true},
    {"name": "detail.readme_summary", "source": "detail_cache", "included": true},
    {"name": "user_note", "source": "repo_annotations", "included": false, "reason": "用户未勾选发送本地笔记"}
  ],
  "excluded_sensitive_fields": [
    "github_token",
    "proxy",
    "runtime_root",
    "diagnostics.raw_error"
  ],
  "estimated_chars": 4200
}
```

预览规则：

- 默认只发送仓库公开元数据、README 摘要和用户明确勾选的本地字段。
- 本地笔记、标签、更新历史和比较上下文需要独立勾选。
- 诊断、Token、代理、runtime path 和原始错误永远不进入预览可选项。
- 预览确认应绑定 input hash，后续执行时如果上下文变化，必须重新预览。

## Artifact 生命周期设计

Provider 输出不能直接覆盖用户状态。建议流程：

1. `ai.job.created`：创建 AI 任务并记录 provider、model、input hash。
2. `ai.preview.accepted`：记录用户确认了哪个 input hash。
3. `ai.output.received`：收到 provider 输出，先进入临时 result。
4. 用户点击保存。
5. `ai.artifact.created`：保存为 `gitsonar.repo_insight.v1` 或后续 schema。

Artifact 必须保留：

- `artifact_id`
- `artifact_type`
- `schema_version`
- `provider`
- `model`
- `input_hash`
- `source_snapshot_id`
- `created_at`
- `updated_at`

后续如果 AI 建议标签、笔记或状态变更，只能作为“建议”展示，不能自动写入用户状态。

## 后续实施切片

1. `AI provider settings skeleton`
   只增加设置字段和 DPAPI secret 存储，默认关闭。
2. `AI privacy preview API`
   只构建预览 payload，不调用 provider。
3. `Local provider execution`
   只支持 loopback local provider，接入 Job/Event runtime。
4. `Cloud provider execution`
   在官方当前文档复核后实现 OpenAI-compatible cloud provider，必须有 preview acceptance。
5. `Artifact save confirmation`
   Provider 输出进入预览，用户确认后保存为本地 artifact。

## 执行步骤

1. 同步任务状态和创建计划。
   预期结果：`GS-P1-017` 明确为设计任务，不实现 provider。
   回滚路径：恢复任务状态为 `[ ]`。
2. 编写 opt-in 设计文档。
   预期结果：设计覆盖 provider 分层、隐私预览、artifact、Key、安全、验证和回滚。
   回滚路径：删除本计划或标记为阻塞。
3. 文档一致性检查。
   预期结果：README、路线图、架构和安全文档都不再把 provider 设计写成未定义。
   回滚路径：恢复文档到上一版。

## 风险

- 技术风险：OpenAI-compatible 端点差异较大。缓解方式：implementation task 必须先查官方文档和目标 provider 文档。
- 产品风险：用户误以为 AI 已自动启用。缓解方式：所有文档写清默认关闭、无调用。
- 隐私 / 安全风险：API Key 和 repo context 外发边界必须在后续实现中再次审查。
- 发布风险：低；本任务为文档设计。

## 验证

- 文档检查：
  - `rg -n "AI provider|OpenAI-compatible|opt-in|隐私预览|provider" docs README.md README.zh-CN.md TASKS.md`
- 安全检查：
  - 确认本任务没有新增 provider 代码、Key 字段、网络调用或设置 UI。
- 手动检查：
  - 阅读 `docs/SECURITY.md` 的 AI 边界，确认仍写明当前不会默认调用内嵌 provider。
  - 阅读 README 规划，确认 provider 仍是未来实现，不是已启用能力。

## 发布与回滚

- 发布方式：设计文档随仓库发布。
- 是否需要开关：不需要；没有运行时行为。
- 如果失败：撤回本计划和文档变更，当前 prompt handoff 行为不受影响。

## 文档更新

- 需要更新的文档：
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
  - `docs/roadmap/ROADMAP.md`
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`
  - `README.md`
  - `README.zh-CN.md`
  - `CHANGELOG.md`

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成 opt-in provider 设计、隐私预览、artifact 生命周期和文档同步。 |
| `2026-04-24` | `[~]` | 已创建计划；准备编写 opt-in 设计与文档同步。 |

## 验证记录

- 已运行检查：
  - `rg -n "AI provider|OpenAI-compatible|opt-in|隐私预览|provider" docs README.md README.zh-CN.md TASKS.md`
  - `rg -n "runtime_ai|ai_provider|api_key|OpenAI-compatible|隐私预览" src docs README.md README.zh-CN.md TASKS.md`
- 手动验证：确认本任务没有新增 provider 代码、API Key 存储字段、设置 UI 或网络调用；现有 prompt handoff 仍是当前行为。
- 尚未覆盖的缺口：真实 provider 实现、API Key 存储、调用预览 UI 和模型输出验证留给后续任务。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
