# GitSonar 任务总表

`TASKS.md` 是仓库级任务状态的事实来源。请配合 `docs/roadmap/ROADMAP.md`、`PLANS.md`、`docs/plans/*.md`、`docs/sprints/CURRENT_TOP10.md` 和 `docs/progress/PROGRESS.md` 一起使用。

最后刷新：`2026-04-24`

## 状态说明

- `[ ]` 未开始
- `[~]` 进行中
- `[!]` 阻塞
- `[x]` 已完成
- `[-]` 取消 / 延后

## 使用规则

- 每个任务都必须有唯一任务 ID，格式为 `GS-P0-001`。
- `TASKS.md` 是状态事实来源。
- `docs/sprints/CURRENT_TOP10.md` 是当前 Auto Top 5 Batch Sprint 候选队列事实来源（文件名因历史兼容保留）。
- 当前批次选中的每个任务，在实现前必须有独立计划文件。
- 状态变化时，必须同步更新 `TASKS.md`、`docs/sprints/CURRENT_TOP10.md` 和 `docs/progress/PROGRESS.md`。
- 推荐一任务一 commit；如果本轮不提交，`Commit / PR` 填 `-`，并在计划文件中留下推荐 commit message。
- 没有验收与验证记录前，不要把任务标记为 `[x]`。

## 汇总

| 优先级 | 总数 | `[ ]` | `[~]` | `[!]` | `[x]` | `[-]` |
|---|---:|---:|---:|---:|---:|---:|
| `P0` | 12 | 0 | 0 | 0 | 12 | 0 |
| `P1` | 17 | 1 | 0 | 0 | 16 | 0 |
| `P2` | 6 | 0 | 0 | 2 | 4 | 0 |

## 当前执行批次

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P1` | `[x]` | `GS-P1-016` | SQLite 迁移第一阶段：JSON 导入 / 导出兼容与回滚骨架 | `docs/plans/0034-sqlite-migration-phase-1.md` | `codex/runtime-control-compat` | `feat(storage): add sqlite migration dry-run skeleton` | 已完成；新增 SQLite schema helper、dry-run 计数和备份 / 回滚路径规划，未默认切换事实存储。 |
| `P1` | `[x]` | `GS-P1-015` | Update Inbox 增强：自上次查看以来、摘要、重要性解释 | `docs/plans/0033-update-inbox-enhancements.md` | `codex/runtime-control-compat` | `feat(updates): add inbox summaries and importance reasons` | 已完成；favorite update 已增加本地变化摘要、重要性解释，Update Inbox 卡片会标明自上次查看以来的未处理更新。 |
| `P1` | `[x]` | `GS-P1-014` | 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE | `docs/plans/0032-unify-refresh-discovery-update-jobs.md` | `codex/runtime-control-compat` | `feat(runtime): bridge refresh and discovery to job events` | 已完成；refresh、discovery 和 favorite update check 已写入通用 Job/Event runtime，现有 UI 轮询路径保持不变。 |
| `P1` | `[x]` | `GS-P1-013` | 只读 API control-token 收紧评估与兼容迁移 | `docs/plans/0031-read-api-control-token-compat.md` | `codex/runtime-control-compat` | `fix(security): require control token for read APIs` | 已完成；剩余只读本地 API 已要求 loopback/control-token，前端统一 header 路径保持兼容。 |
| `P0` | `[x]` | `GS-P0-012` | 文档现实同步与下一轮任务队列计划 | `docs/plans/0030-docs-reality-sync.md` | `codex/runtime-control-compat` | `-` | 已同步 README、CHANGELOG、架构、安全、路线图、任务表、Sprint 队列和进度日志；验证通过。推荐 commit message：`docs: sync project status and next autopilot queue`。 |

## 当前 Auto Top 5 Batch 候选队列

`docs/sprints/CURRENT_TOP10.md` 可以保留多于 5 个候选；Auto Top 5 Batch Sprint 每批只选择优先级最高、未完成、未阻塞的最多 5 个可安全执行任务。

| 排名 | 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | `P1` | `[x]` | `GS-P1-013` | 只读 API control-token 收紧评估与兼容迁移 | `docs/plans/0031-read-api-control-token-compat.md` | `codex/runtime-control-compat` | `fix(security): require control token for read APIs` | 已完成；无 token 直接读取返回 `403 invalid_control_token`，主界面请求继续携带 control header。 |
| 2 | `P1` | `[x]` | `GS-P1-014` | 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE | `docs/plans/0032-unify-refresh-discovery-update-jobs.md` | `codex/runtime-control-compat` | `feat(runtime): bridge refresh and discovery to job events` | 已完成；focused 测试通过，现有 discovery job API 和 UI 轮询路径保持兼容。 |
| 3 | `P1` | `[x]` | `GS-P1-015` | Update Inbox 增强：自上次查看以来、摘要、重要性解释 | `docs/plans/0033-update-inbox-enhancements.md` | `codex/runtime-control-compat` | `feat(updates): add inbox summaries and importance reasons` | 已完成；在现有 read/pin/dismiss/priority MVP 上补充本地摘要、重要性解释和自上次查看以来提示。 |
| 4 | `P1` | `[x]` | `GS-P1-016` | SQLite 迁移第一阶段：JSON 导入 / 导出兼容与回滚骨架 | `docs/plans/0034-sqlite-migration-phase-1.md` | `codex/runtime-control-compat` | `feat(storage): add sqlite migration dry-run skeleton` | 已完成；新增迁移骨架和兼容验证，不默认切换事实存储。 |
| 5 | `P1` | `[ ]` | `GS-P1-017` | AI provider opt-in 设计与本地 Ollama / OpenAI-compatible pipeline | 待创建：`docs/plans/0035-ai-provider-opt-in-design.md` | `-` | `-` | 先设计 provider、隐私预览、artifact 可追溯和手动启用边界，不默认调用云端。 |

## 阻塞或暂不进入下一批的任务

| 优先级 | 状态 | 任务 ID | 任务 | Plan | 备注 |
|---|---:|---|---|---|---|
| `P2` | `[!]` | `GS-P2-003` | 加密同步 / 备份 | `docs/plans/0020-encrypted-sync-backup-blocked.md` | 阻塞：需先明确同步目标、密钥管理、冲突处理和显式 opt-in 设计。 |
| `P2` | `[!]` | `GS-P2-005` | 代码签名 | `docs/plans/0021-code-signing-blocked.md` | 阻塞：需要证书、私钥保管、密码注入和时间戳服务决策。 |
| `P1/P2` | `[-]` | `-` | React / FastAPI / SQLite / AI provider 大迁移 | `-` | 不为了补满批次而做大重写；必须按独立计划推进。 |

## 已完成的产品闭环与文档任务

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P0` | `[x]` | `GS-P0-001` | Codex 执行规则与文档基线 | `docs/plans/0001-codex-guidance-docs.md` | `-` | `-` | 已建立仓库级工作指南。 |
| `P0` | `[x]` | `GS-P0-002` | 任务追踪体系与 Auto Top 5 Batch Sprint | `docs/plans/0002-task-tracking-system.md` | `-` | `-` | 已建立任务、计划、进度和 Sprint 队列规则。 |
| `P0` | `[x]` | `GS-P0-003` | 网络 / 运行诊断 MVP | `docs/plans/0003-network-diagnostics-mvp.md` | `-` | `-` | 已新增本地诊断面板和 `/api/diagnostics`。 |
| `P0` | `[x]` | `GS-P0-004` | 标签与笔记 MVP | `docs/plans/0004-tags-notes-mvp.md` | `-` | `-` | 已支持本地标签、笔记、搜索命中和导入 / 导出兼容。 |
| `P0` | `[x]` | `GS-P0-005` | 保存发现视图 MVP | `docs/plans/0005-saved-discovery-views-mvp.md` | `-` | `-` | 已支持保存、载入、重跑和删除发现视图。 |
| `P0` | `[x]` | `GS-P0-006` | Update Inbox MVP | `docs/plans/0006-update-inbox-mvp.md` | `-` | `-` | 已支持已读、置顶、忽略和优先级排序。 |
| `P0` | `[x]` | `GS-P0-007` | 推荐 / 排名原因 | `docs/plans/0007-why-recommended.md` | `-` | `-` | 已在发现卡片和详情中展示原因。 |
| `P0` | `[x]` | `GS-P0-008` | 忽略反馈 | `docs/plans/0008-ignore-feedback.md` | `-` | `-` | 已记录忽略原因并参与后续排序信号。 |
| `P0` | `[x]` | `GS-P0-009` | Markdown 摘要导出 | `docs/plans/0009-copy-markdown-summary.md` | `-` | `-` | 已支持单仓库、批量和对比摘要导出。 |

## 已完成的 P1 / P2 MVP 与安全加固

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P1` | `[x]` | `GS-P1-001` | AI Insight schema MVP | `docs/plans/0010-ai-insight-schema-mvp.md` | `-` | `-` | 已定义 `gitsonar.repo_insight.v1`，支持手动保存 / 删除。 |
| `P1` | `[x]` | `GS-P1-002` | JSON API boundary MVP | `docs/plans/0011-json-api-boundary-mvp.md` | `-` | `-` | 已新增 bootstrap、repos、updates、discovery views 只读边界。 |
| `P1` | `[x]` | `GS-P1-003` | SQLite 迁移设计 | `docs/plans/0012-sqlite-migration-design.md` | `-` | `-` | 已完成迁移与回滚设计，未实施存储切换。 |
| `P1` | `[x]` | `GS-P1-004` | 统一 Job / Event 模型 | `docs/plans/0013-job-event-model-mvp.md` | `-` | `-` | 已新增内存级 Job/Event runtime。 |
| `P1` | `[x]` | `GS-P1-005` | SSE 进度与事件流 | `docs/plans/0014-sse-event-stream-mvp.md` | `-` | `-` | 已新增 `/api/events/stream` SSE 快照端点。 |
| `P1` | `[x]` | `GS-P1-006` | AI Artifact 生命周期与缓存 | `docs/plans/0015-ai-artifact-lifecycle-cache.md` | `-` | `-` | 已扩展本地 AI artifact metadata 和列表端点。 |
| `P1` | `[x]` | `GS-P1-007` | 发现结果聚类 | `docs/plans/0016-discovery-result-clustering.md` | `codex/runtime-control-compat` | `-` | 已完成本地 discovery result 聚类。 |
| `P2` | `[x]` | `GS-P2-001` | 仓库地图 / 可视化体验 | `docs/plans/0017-repo-map-visualization-mvp.md` | `codex/runtime-control-compat` | `-` | 已新增轻量二维主题地图。 |
| `P2` | `[x]` | `GS-P2-002` | 可选本地翻译模型支持 | `docs/plans/0019-optional-local-translation-model.md` | `codex/runtime-control-compat` | `-` | 已新增显式可选的 loopback-only Ollama-style provider。 |
| `P2` | `[x]` | `GS-P2-004` | 发布加固与 AV 误报缓解 | `docs/plans/0018-release-hardening-av-mitigation.md` | `codex/runtime-control-compat` | `-` | 已新增本地 SHA256 release manifest 脚本。 |
| `P2` | `[x]` | `GS-P2-006` | 前端现代化评估 | `docs/plans/0022-frontend-modernization-evaluation.md` | `codex/runtime-control-compat` | `-` | 已完成评估，当前不启动 React / Vite 重写。 |
| `P0` | `[x]` | `GS-P0-010` | Redact proxy credentials and local diagnostics details | `docs/plans/0023-redact-proxy-and-local-diagnostics.md` | `-` | `-` | Settings/bootstrap/diagnostics 不再暴露代理凭据或原始 runtime path。 |
| `P0` | `[x]` | `GS-P0-011` | Keep refresh status errors user safe | `docs/plans/0024-safe-refresh-status-errors.md` | `-` | `-` | status/bootstrap/UI polling 使用安全失败消息。 |
| `P1` | `[x]` | `GS-P1-008` | Sanitize discovery job failures | `docs/plans/0025-safe-discovery-job-errors.md` | `-` | `-` | discovery job 失败 payload 不返回原始异常文本。 |
| `P1` | `[x]` | `GS-P1-009` | Limit JSON request body size | `docs/plans/0026-json-body-size-limit.md` | `-` | `-` | 过大 JSON body 返回 `413 payload_too_large`。 |
| `P1` | `[x]` | `GS-P1-010` | Protect `/api/repo-details` side-effect GET | `docs/plans/0027-protect-repo-details-endpoint.md` | `-` | `-` | `/api/repo-details` 已要求 loopback/control token。 |
| `P1` | `[x]` | `GS-P1-011` | Forbid DPAPI UI prompts | `docs/plans/0028-dpapi-ui-forbidden.md` | `codex/runtime-control-compat` | `fix(security): forbid dpapi ui prompts` | DPAPI encrypt/decrypt now pass `CRYPTPROTECT_UI_FORBIDDEN`。 |
| `P1` | `[x]` | `GS-P1-012` | Redact HTTP route exception logs | `docs/plans/0029-redact-http-route-exception-logs.md` | `codex/runtime-control-compat` | `fix(security): redact http route exception logs` | 未预期 HTTP route failure 日志已脱敏。 |
