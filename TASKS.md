# GitSonar 任务总表

`TASKS.md` 是仓库级任务状态的事实来源。请配合 `docs/roadmap/ROADMAP.md`、`PLANS.md`、`docs/plans/*.md`、`docs/sprints/CURRENT_TOP10.md` 和 `docs/progress/PROGRESS.md` 一起使用。

最后刷新：`2026-04-26`

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
| `P0` | 13 | 0 | 0 | 0 | 13 | 0 |
| `P1` | 22 | 0 | 0 | 0 | 22 | 0 |
| `P2` | 15 | 7 | 0 | 2 | 6 | 0 |

## 当前执行批次

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P1` | `[x]` | `GS-P1-022` | 优化学习型 AI 项目分析提示词 | `docs/plans/0042-learning-prompt-handoff-hardening.md` | `codex/runtime-control-compat` | `-` | 已完成；单仓库、批量和对比 prompt handoff 已强化核验状态、证据规则、可信度标签、MVP、源码阅读顺序和可选 7 天计划约束，不新增 AI provider、云 API、状态字段或数据外发。推荐 commit message：`feat(ai): harden learning prompt handoff`。 |
| `P2` | `[x]` | `GS-P2-015` | Runtime UI visual polish | `docs/plans/0041-runtime-ui-visual-polish.md` | `codex/runtime-control-compat` | `-` | 已完成；在当前 Vanilla `runtime_ui` 中统一 muted/shadow/line-height tokens，降低次级 UI 边框噪声，柔化多选卡片态，并用 renderer `--mount-delay` 替代旧 `nth-child` 挂载延迟。推荐 commit message：`style(ui): polish runtime visual system`。 |
| `P1` | `[x]` | `GS-P1-021` | 详情抽屉 README 滚动卡顿修复 | `docs/plans/0039-detail-drawer-readme-jank.md` | `codex/runtime-control-compat` | `-` | 已完成；长 README 摘要默认只渲染前 `12000` 字，提供“展开全文 / 收起预览”，复制 Markdown 摘要继续使用完整详情内容。推荐 commit message：`perf(ui): reduce detail drawer readme scroll jank`。 |
| `P2` | `[x]` | `GS-P2-007` | 前端现代化总路线与文档同步 | `docs/plans/0040-frontend-modernization-roadmap.md` | `codex/runtime-control-compat` | `-` | 已完成；把 React/Vite 从“当前不启动完整重写”更新为局部试点路线，后续按 `GS-P2-008` -> `GS-P2-014` 顺序推进。推荐 commit message：`docs(frontend): add staged modernization roadmap`。 |
| `P0` | `[x]` | `GS-P0-013` | 标签与笔记编辑体验优化 | `docs/plans/0038-tags-notes-editor-ux.md` | `codex/runtime-control-compat` | `-` | 已完成；详情抽屉改为“本地整理”编辑区，标签 chip / 推荐标签 / 输入添加和笔记失焦自动保存均复用 `/api/repo-annotations`。推荐 commit message：`feat(ui): improve tags and notes editor`。 |
| `P1` | `[x]` | `GS-P1-020` | 整页性能审计与滚动卡顿修复 | `docs/plans/0038-ui-performance-audit-and-jank-fixes.md` | `codex/runtime-control-compat` | `-` | 已完成；优化菜单 scroll/resize、弹层滚动、详情请求缓存、列表测量和卡片渲染成本。推荐 commit message：`perf(ui): reduce scroll jank across overlays and lists`。 |
| `P1` | `[x]` | `GS-P1-019` | 移除 AI Insight JSON 手动保存工作流 | `docs/plans/0037-remove-ai-insight-json-workflow.md` | `codex/runtime-control-compat` | `-` | 已完成；删除详情页手动 Insight JSON 面板、本地 legacy insight 缓存和旧 API，保留 ChatGPT / Gemini / 复制 Prompt / Markdown 摘要导出。推荐 commit message：`refactor(ai): remove manual insight json workflow`。 |
| `P1` | `[x]` | `GS-P1-018` | 移除旧本机翻译路径并改为 OpenAI-compatible 翻译 API | `docs/plans/0036-openai-compatible-translation-api.md` | `codex/runtime-control-compat` | `feat(translation): use openai-compatible translation api` | 已完成；默认保留 Google Translate，新增显式 opt-in 的 OpenAI-compatible 翻译 API，API Key 本地 DPAPI 加密保存，不实现内嵌 AI provider。 |
| `P1` | `[x]` | `GS-P1-017` | AI provider opt-in 设计与 OpenAI-compatible pipeline | `docs/plans/0035-ai-provider-opt-in-design.md` | `codex/runtime-control-compat` | `docs(ai): design opt-in provider pipeline` | 已完成；已定义 provider 分层、隐私预览、artifact 可追溯、Key/Token 边界和后续实施切片，未实现 provider。 |
| `P1` | `[x]` | `GS-P1-016` | SQLite 迁移第一阶段：JSON 导入 / 导出兼容与回滚骨架 | `docs/plans/0034-sqlite-migration-phase-1.md` | `codex/runtime-control-compat` | `feat(storage): add sqlite migration dry-run skeleton` | 已完成；新增 SQLite schema helper、dry-run 计数和备份 / 回滚路径规划，未默认切换事实存储。 |
| `P1` | `[x]` | `GS-P1-015` | Update Inbox 增强：自上次查看以来、摘要、重要性解释 | `docs/plans/0033-update-inbox-enhancements.md` | `codex/runtime-control-compat` | `feat(updates): add inbox summaries and importance reasons` | 已完成；favorite update 已增加本地变化摘要、重要性解释，Update Inbox 卡片会标明自上次查看以来的未处理更新。 |
| `P1` | `[x]` | `GS-P1-014` | 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE | `docs/plans/0032-unify-refresh-discovery-update-jobs.md` | `codex/runtime-control-compat` | `feat(runtime): bridge refresh and discovery to job events` | 已完成；refresh、discovery 和 favorite update check 已写入通用 Job/Event runtime，现有 UI 轮询路径保持不变。 |
| `P1` | `[x]` | `GS-P1-013` | 只读 API control-token 收紧评估与兼容迁移 | `docs/plans/0031-read-api-control-token-compat.md` | `codex/runtime-control-compat` | `fix(security): require control token for read APIs` | 已完成；剩余只读本地 API 已要求 loopback/control-token，前端统一 header 路径保持兼容。 |
| `P0` | `[x]` | `GS-P0-012` | 文档现实同步与下一轮任务队列计划 | `docs/plans/0030-docs-reality-sync.md` | `codex/runtime-control-compat` | `-` | 已同步 README、CHANGELOG、架构、安全、路线图、任务表、Sprint 队列和进度日志；验证通过。推荐 commit message：`docs: sync project status and next autopilot queue`。 |

## 当前 Auto Top 5 Batch 候选队列

`docs/sprints/CURRENT_TOP10.md` 可以保留多于 5 个候选；Auto Top 5 Batch Sprint 每批只选择优先级最高、未完成、未阻塞的最多 5 个可安全执行任务。

| 排名 | 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | `P1` | `[x]` | `GS-P1-022` | 优化学习型 AI 项目分析提示词 | `docs/plans/0042-learning-prompt-handoff-hardening.md` | `codex/runtime-control-compat` | `-` | 已完成；只修改 prompt handoff 文案和测试，保持 ChatGPT / Gemini / copy-only 入口、HTTP API、状态与隐私边界不变。 |
| 2 | `P2` | `[x]` | `GS-P2-015` | Runtime UI visual polish | `docs/plans/0041-runtime-ui-visual-polish.md` | `codex/runtime-control-compat` | `-` | 已按用户指定插入到 `GS-P2-008` 之前并完成；纯 `runtime_ui` 视觉 / 交互 polish，不改 API、存储、业务逻辑或现代化构建链。 |
| 3 | `P2` | `[ ]` | `GS-P2-008` | Modern asset pipeline | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 下一项前端现代化可执行任务；开始前需创建或更新任务级计划，建立 Vite 构建、allowlisted modern assets 和缺失 fallback。 |
| 4 | `P1` | `[x]` | `GS-P1-021` | 详情抽屉 README 滚动卡顿修复 | `docs/plans/0039-detail-drawer-readme-jank.md` | `codex/runtime-control-compat` | `-` | 已完成；默认预览长 README，展开状态仅前端会话保存，不改 API、缓存、JSON state 或导入导出。 |
| 5 | `P1` | `[x]` | `GS-P1-020` | 整页性能审计与滚动卡顿修复 | `docs/plans/0038-ui-performance-audit-and-jank-fixes.md` | `codex/runtime-control-compat` | `-` | 已完成；只在当前 Vanilla JS/CSS 前端中做滚动、弹层、详情请求和列表渲染性能优化，不改 API 或存储。 |
| 6 | `P1` | `[x]` | `GS-P1-013` | 只读 API control-token 收紧评估与兼容迁移 | `docs/plans/0031-read-api-control-token-compat.md` | `codex/runtime-control-compat` | `fix(security): require control token for read APIs` | 已完成；无 token 直接读取返回 `403 invalid_control_token`，主界面请求继续携带 control header。 |
| 7 | `P1` | `[x]` | `GS-P1-014` | 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE | `docs/plans/0032-unify-refresh-discovery-update-jobs.md` | `codex/runtime-control-compat` | `feat(runtime): bridge refresh and discovery to job events` | 已完成；focused 测试通过，现有 discovery job API 和 UI 轮询路径保持兼容。 |
| 8 | `P1` | `[x]` | `GS-P1-015` | Update Inbox 增强：自上次查看以来、摘要、重要性解释 | `docs/plans/0033-update-inbox-enhancements.md` | `codex/runtime-control-compat` | `feat(updates): add inbox summaries and importance reasons` | 已完成；在现有 read/pin/dismiss/priority MVP 上补充本地摘要、重要性解释和自上次查看以来提示。 |
| 9 | `P1` | `[x]` | `GS-P1-016` | SQLite 迁移第一阶段：JSON 导入 / 导出兼容与回滚骨架 | `docs/plans/0034-sqlite-migration-phase-1.md` | `codex/runtime-control-compat` | `feat(storage): add sqlite migration dry-run skeleton` | 已完成；新增迁移骨架和兼容验证，不默认切换事实存储。 |
| 10 | `P1` | `[x]` | `GS-P1-017` | AI provider opt-in 设计与 OpenAI-compatible pipeline | `docs/plans/0035-ai-provider-opt-in-design.md` | `codex/runtime-control-compat` | `docs(ai): design opt-in provider pipeline` | 已完成；已设计 provider、隐私预览、artifact 可追溯和手动启用边界，未调用云端。 |

## 阻塞或暂不进入下一批的任务

| 优先级 | 状态 | 任务 ID | 任务 | Plan | 备注 |
|---|---:|---|---|---|---|
| `P2` | `[!]` | `GS-P2-003` | 加密同步 / 备份 | `docs/plans/0020-encrypted-sync-backup-blocked.md` | 阻塞：需先明确同步目标、密钥管理、冲突处理和显式 opt-in 设计。 |
| `P2` | `[!]` | `GS-P2-005` | 代码签名 | `docs/plans/0021-code-signing-blocked.md` | 阻塞：需要证书、私钥保管、密码注入和时间戳服务决策。 |
| `P2` | `[ ]` | `GS-P2-009` ~ `GS-P2-014` | 后续 React 页面 / 主工作台迁移 | `docs/plans/0040-frontend-modernization-roadmap.md` | 暂不进入下一批；必须先完成 `GS-P2-008` 并按顺序逐项创建或更新任务级计划。 |
| `P1/P2` | `[-]` | `-` | FastAPI / SQLite / AI provider 大迁移 | `-` | 不为了补满批次而做大重写；必须按独立计划推进。 |
| `P2` | `[-]` | `-` | 完整主工作台 React 大重写 | `docs/plans/0040-frontend-modernization-roadmap.md` | 不直接执行；只能在 `GS-P2-009` ~ `GS-P2-013` 稳定并通过浏览器级 smoke test 后，由 `GS-P2-014` 评估 feature flag 切换。 |

## 已完成的产品闭环与文档任务

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P0` | `[x]` | `GS-P0-001` | Codex 执行规则与文档基线 | `docs/plans/0001-codex-guidance-docs.md` | `-` | `-` | 已建立仓库级工作指南。 |
| `P0` | `[x]` | `GS-P0-002` | 任务追踪体系与 Auto Top 5 Batch Sprint | `docs/plans/0002-task-tracking-system.md` | `-` | `-` | 已建立任务、计划、进度和 Sprint 队列规则。 |
| `P0` | `[x]` | `GS-P0-003` | 网络 / 运行诊断 MVP | `docs/plans/0003-network-diagnostics-mvp.md` | `-` | `-` | 已新增本地诊断面板和 `/api/diagnostics`。 |
| `P0` | `[x]` | `GS-P0-004` | 标签与笔记 MVP | `docs/plans/0004-tags-notes-mvp.md` | `-` | `-` | 已支持本地标签、笔记、搜索命中和导入 / 导出兼容。 |
| `P0` | `[x]` | `GS-P0-013` | 标签与笔记编辑体验优化 | `docs/plans/0038-tags-notes-editor-ux.md` | `codex/runtime-control-compat` | `-` | 已将详情抽屉标签 / 笔记编辑从浏览器 prompt 改成本地整理编辑区，后端 API 和数据模型不变。推荐 commit message：`feat(ui): improve tags and notes editor`。 |
| `P0` | `[x]` | `GS-P0-005` | 保存发现视图 MVP | `docs/plans/0005-saved-discovery-views-mvp.md` | `-` | `-` | 已支持保存、载入、重跑和删除发现视图。 |
| `P0` | `[x]` | `GS-P0-006` | Update Inbox MVP | `docs/plans/0006-update-inbox-mvp.md` | `-` | `-` | 已支持已读、置顶、忽略和优先级排序。 |
| `P0` | `[x]` | `GS-P0-007` | 推荐 / 排名原因 | `docs/plans/0007-why-recommended.md` | `-` | `-` | 已在发现卡片和详情中展示原因。 |
| `P0` | `[x]` | `GS-P0-008` | 忽略反馈 | `docs/plans/0008-ignore-feedback.md` | `-` | `-` | 已记录忽略原因并参与后续排序信号。 |
| `P0` | `[x]` | `GS-P0-009` | Markdown 摘要导出 | `docs/plans/0009-copy-markdown-summary.md` | `-` | `-` | 已支持单仓库、批量和对比摘要导出。 |

## 已完成的 P1 / P2 MVP 与安全加固

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P1` | `[x]` | `GS-P1-021` | 详情抽屉 README 滚动卡顿修复 | `docs/plans/0039-detail-drawer-readme-jank.md` | `codex/runtime-control-compat` | `-` | 已完成；默认渲染 README 摘要前 `12000` 字，长内容提供“展开全文 / 收起预览”，复制 Markdown 摘要仍使用完整 detail 内容。推荐 commit message：`perf(ui): reduce detail drawer readme scroll jank`。 |
| `P1` | `[x]` | `GS-P1-020` | 整页性能审计与滚动卡顿修复 | `docs/plans/0038-ui-performance-audit-and-jank-fixes.md` | `codex/runtime-control-compat` | `-` | 已完成；菜单无打开项时不进入重定位，内部滚动容器跳过 document scroll 重算，详情请求有内存缓存和 in-flight 去重，列表测量与卡片/弹层绘制成本已降低。推荐 commit message：`perf(ui): reduce scroll jank across overlays and lists`。 |
| `P1` | `[x]` | `GS-P1-001` | AI Insight schema MVP | `docs/plans/0010-ai-insight-schema-mvp.md` | `-` | `-` | 历史任务已完成；运行时手动 JSON 保存工作流已被 `GS-P1-019` 取代。 |
| `P1` | `[x]` | `GS-P1-002` | JSON API boundary MVP | `docs/plans/0011-json-api-boundary-mvp.md` | `-` | `-` | 已新增 bootstrap、repos、updates、discovery views 只读边界。 |
| `P1` | `[x]` | `GS-P1-003` | SQLite 迁移设计 | `docs/plans/0012-sqlite-migration-design.md` | `-` | `-` | 已完成迁移与回滚设计，未实施存储切换。 |
| `P1` | `[x]` | `GS-P1-004` | 统一 Job / Event 模型 | `docs/plans/0013-job-event-model-mvp.md` | `-` | `-` | 已新增内存级 Job/Event runtime。 |
| `P1` | `[x]` | `GS-P1-005` | SSE 进度与事件流 | `docs/plans/0014-sse-event-stream-mvp.md` | `-` | `-` | 已新增 `/api/events/stream` SSE 快照端点。 |
| `P1` | `[x]` | `GS-P1-006` | AI Artifact 生命周期与缓存 | `docs/plans/0015-ai-artifact-lifecycle-cache.md` | `-` | `-` | 历史任务已完成；本地 artifact 缓存和列表端点已被 `GS-P1-019` 取代。 |
| `P1` | `[x]` | `GS-P1-019` | 移除 AI Insight JSON 手动保存工作流 | `docs/plans/0037-remove-ai-insight-json-workflow.md` | `codex/runtime-control-compat` | `-` | 已完成；删除手动 JSON 保存 / 缓存能力，保留 prompt handoff 和 Markdown 摘要导出。推荐 commit message：`refactor(ai): remove manual insight json workflow`。 |
| `P1` | `[x]` | `GS-P1-007` | 发现结果聚类 | `docs/plans/0016-discovery-result-clustering.md` | `codex/runtime-control-compat` | `-` | 已完成本地 discovery result 聚类。 |
| `P2` | `[x]` | `GS-P2-001` | 仓库地图 / 可视化体验 | `docs/plans/0017-repo-map-visualization-mvp.md` | `codex/runtime-control-compat` | `-` | 已新增轻量二维主题地图。 |
| `P2` | `[x]` | `GS-P2-002` | 可选翻译模型支持 | `docs/plans/0019-optional-local-translation-model.md` | `codex/runtime-control-compat` | `-` | 历史任务已完成；方向已被 `GS-P1-018` 取代。 |
| `P2` | `[x]` | `GS-P2-004` | 发布加固与 AV 误报缓解 | `docs/plans/0018-release-hardening-av-mitigation.md` | `codex/runtime-control-compat` | `-` | 已新增本地 SHA256 release manifest 脚本。 |
| `P2` | `[x]` | `GS-P2-006` | 前端现代化评估 | `docs/plans/0022-frontend-modernization-evaluation.md` | `codex/runtime-control-compat` | `-` | 历史评估已完成；当时结论是不启动完整 React / Vite 重写，已由 `GS-P2-007` 细化为局部试点路线。 |
| `P2` | `[x]` | `GS-P2-007` | 前端现代化总路线与文档同步 | `docs/plans/0040-frontend-modernization-roadmap.md` | `codex/runtime-control-compat` | `-` | 已完成；新增分阶段路线和 `GS-P2-008` ~ `GS-P2-014` 任务序列。推荐 commit message：`docs(frontend): add staged modernization roadmap`。 |
| `P2` | `[x]` | `GS-P2-015` | Runtime UI visual polish | `docs/plans/0041-runtime-ui-visual-polish.md` | `codex/runtime-control-compat` | `-` | 已完成；作为 `GS-P2-008` 前的纯 Vanilla runtime UI polish，统一视觉 token、柔化 selected state、降低次级边框噪声并保留 forced-colors。推荐 commit message：`style(ui): polish runtime visual system`。 |
| `P0` | `[x]` | `GS-P0-010` | Redact proxy credentials and local diagnostics details | `docs/plans/0023-redact-proxy-and-local-diagnostics.md` | `-` | `-` | Settings/bootstrap/diagnostics 不再暴露代理凭据或原始 runtime path。 |
| `P0` | `[x]` | `GS-P0-011` | Keep refresh status errors user safe | `docs/plans/0024-safe-refresh-status-errors.md` | `-` | `-` | status/bootstrap/UI polling 使用安全失败消息。 |
| `P1` | `[x]` | `GS-P1-008` | Sanitize discovery job failures | `docs/plans/0025-safe-discovery-job-errors.md` | `-` | `-` | discovery job 失败 payload 不返回原始异常文本。 |
| `P1` | `[x]` | `GS-P1-009` | Limit JSON request body size | `docs/plans/0026-json-body-size-limit.md` | `-` | `-` | 过大 JSON body 返回 `413 payload_too_large`。 |
| `P1` | `[x]` | `GS-P1-010` | Protect `/api/repo-details` side-effect GET | `docs/plans/0027-protect-repo-details-endpoint.md` | `-` | `-` | `/api/repo-details` 已要求 loopback/control token。 |
| `P1` | `[x]` | `GS-P1-011` | Forbid DPAPI UI prompts | `docs/plans/0028-dpapi-ui-forbidden.md` | `codex/runtime-control-compat` | `fix(security): forbid dpapi ui prompts` | DPAPI encrypt/decrypt now pass `CRYPTPROTECT_UI_FORBIDDEN`。 |
| `P1` | `[x]` | `GS-P1-012` | Redact HTTP route exception logs | `docs/plans/0029-redact-http-route-exception-logs.md` | `codex/runtime-control-compat` | `fix(security): redact http route exception logs` | 未预期 HTTP route failure 日志已脱敏。 |

## 未开始的前端现代化任务

这些任务必须按顺序推进。除 `GS-P2-008` 外，其余任务暂不进入下一批；每个任务开始前都需要创建或更新任务级计划，写清 fallback、回滚、验证和推荐 commit message。

| 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---|---:|---|---|---|---|---|---|
| `P2` | `[ ]` | `GS-P2-008` | Modern asset pipeline | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 下一项可执行；建立 Vite 构建链、allowlisted modern assets、runtime copy 和缺失 fallback。推荐 commit message：`feat(frontend): add modern asset pipeline`。 |
| `P2` | `[ ]` | `GS-P2-009` | React 诊断页试点 | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 依赖 `GS-P2-008`；优先迁移诊断弹层，保留 Vanilla fallback。推荐 commit message：`feat(frontend): add react diagnostics island`。 |
| `P2` | `[ ]` | `GS-P2-010` | React 设置页试点 | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 依赖 `GS-P2-009`；验证表单、敏感字段和保存流程。推荐 commit message：`feat(frontend): add react settings island`。 |
| `P2` | `[ ]` | `GS-P2-011` | 静态壳与 bootstrap 收敛 | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 依赖诊断和设置试点稳定；减少 HTML 大 payload。推荐 commit message：`refactor(ui): converge shell bootstrap payload`。 |
| `P2` | `[ ]` | `GS-P2-012` | 详情抽屉迁移 | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 依赖 `GS-P2-011`；迁移详情、标签、笔记和 README 摘要。推荐 commit message：`feat(frontend): migrate detail drawer island`。 |
| `P2` | `[ ]` | `GS-P2-013` | 发现页迁移 | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 依赖详情抽屉迁移稳定；迁移 Discovery View、进度、工具条和主题地图。推荐 commit message：`feat(frontend): migrate discovery view island`。 |
| `P2` | `[ ]` | `GS-P2-014` | 主工作台迁移评估与切换 | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | 依赖前序 React islands 稳定和浏览器级 smoke test；必须用 feature flag 保留 legacy workspace。推荐 commit message：`docs(frontend): evaluate modern workspace switch`。 |
