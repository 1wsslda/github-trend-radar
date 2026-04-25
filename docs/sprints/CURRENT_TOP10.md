# 当前 Auto Top 5 Batch Sprint 候选队列

本文件记录当前自动排序后的候选任务队列。
文件名 `CURRENT_TOP10.md` 因历史兼容保留；Auto Top 5 Batch Sprint 每批只选择优先级最高、未完成、未阻塞的最多 5 个可安全执行任务。

最后刷新：`2026-04-25`

## 选择规则

Codex 选择当前 Auto Top 5 Batch 时，应按以下顺序判断：

1. 路线图优先级：P0 高于 P1，P1 高于 P2
2. 用户价值更高的优先
3. 风险更低、改动更小的优先
4. 能解锁后续工作的优先
5. 保持本地优先与 Windows 桌面工作流的优先
6. 不需要大重写的优先

## Runtime UI visual polish 批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P2-015` | `[x]` | Runtime UI visual polish | `docs/plans/0041-runtime-ui-visual-polish.md` | `codex/runtime-control-compat` | `-` | 已完成；按用户指定插入到 `GS-P2-008` 之前。只修改当前 `runtime_ui` CSS/JS 和测试，新增视觉 token、柔化 selected state、降低次级边框噪声，并用 `--mount-delay` 替代旧 `nth-child` 卡片挂载延迟。推荐 commit message：`style(ui): polish runtime visual system`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| `GS-P2-008` Modern asset pipeline | 仍是下一项前端现代化可执行任务；本批只做 Vanilla runtime UI polish，不引入 React / Vite / Node runtime。 |
| `GS-P2-009` ~ `GS-P2-014` | 必须等待 `GS-P2-008` 完成并有验证记录，不能跳过前序现代化阶段。 |
| API / storage / AI / sync changes | 本批明确不改变 HTTP API、JSON state、schema、storage、Python runtime contract、AI provider、云 API 或同步边界。 |

## 前端现代化总路线与文档同步批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P2-007` | `[x]` | 前端现代化总路线与文档同步 | `docs/plans/0040-frontend-modernization-roadmap.md` | `codex/runtime-control-compat` | `-` | 已完成；将 React/Vite 从“当前不启动完整重写”更新为局部试点路线，并新增 `GS-P2-008` ~ `GS-P2-014` 阶段任务。推荐 commit message：`docs(frontend): add staged modernization roadmap`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| `GS-P2-008` Modern asset pipeline | 后续实现任务，已放入下一轮候选；开始前必须创建或更新任务级计划。 |
| `GS-P2-009` ~ `GS-P2-014` | 必须等待前序阶段完成并有验证记录，不能为了凑批次直接迁移 React 页面或主工作台。 |
| 完整 React 大重写 | 本路线只允许局部试点和 feature flag 切换，不允许一次性替换主工作台。 |

## 详情抽屉 README 滚动卡顿修复批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P1-021` | `[x]` | 详情抽屉 README 滚动卡顿修复 | `docs/plans/0039-detail-drawer-readme-jank.md` | `codex/runtime-control-compat` | `-` | 已完成；默认只渲染 README 摘要前 `12000` 字，提供“展开全文 / 收起预览”，复制 Markdown 摘要继续使用完整详情内容。推荐 commit message：`perf(ui): reduce detail drawer readme scroll jank`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| React / Vite rewrite | 本批只在当前 Vanilla JS/CSS 前端内做详情抽屉局部性能修复。 |
| FastAPI / SQLite migration | 本批不改变 HTTP API、运行时服务、detail cache 或 JSON 事实存储。 |
| AI provider / cloud telemetry | 本批不新增 AI、云 API、同步、性能上报或用户数据外发。 |

## 标签与笔记编辑体验优化批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P0-013` | `[x]` | 标签与笔记编辑体验优化 | `docs/plans/0038-tags-notes-editor-ux.md` | `codex/runtime-control-compat` | `-` | 已完成；详情抽屉改为“本地整理”编辑区，标签 chip / 推荐标签 / 输入添加和笔记失焦自动保存均复用 `/api/repo-annotations`。推荐 commit message：`feat(ui): improve tags and notes editor`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| 其他 `window.prompt()` 流程 | 本批只处理标签 / 笔记编辑；忽略原因和保存发现视图命名保持现状。 |
| React / SQLite / AI provider | 本批不改变前端技术栈、持久化事实来源、后端 API 或隐私边界。 |

## UI 性能审计与滚动卡顿修复批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P1-020` | `[x]` | 整页性能审计与滚动卡顿修复 | `docs/plans/0038-ui-performance-audit-and-jank-fixes.md` | `codex/runtime-control-compat` | `-` | 已完成；优化详情 / 对比 / 诊断弹层、主列表、更新页、发现页、控制抽屉和菜单滚动卡顿。推荐 commit message：`perf(ui): reduce scroll jank across overlays and lists`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| React / Vite rewrite | 本批只在当前 Vanilla JS/CSS 前端内做小步性能优化。 |
| FastAPI / SQLite migration | 本批不改变 HTTP API、运行时服务或持久化事实来源。 |
| AI provider / cloud telemetry | 本批不新增 AI、云 API、同步、性能上报或用户数据外发。 |

## OpenAI-compatible 翻译 API 批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P1-018` | `[x]` | 移除旧本机翻译路径并改为 OpenAI-compatible 翻译 API | `docs/plans/0036-openai-compatible-translation-api.md` | `codex/runtime-control-compat` | `feat(translation): use openai-compatible translation api` | 已完成；默认保留 Google Translate，新增显式 opt-in 的 OpenAI-compatible 翻译 API，API Key 本地 DPAPI 加密保存。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| AI provider implementation | 本批只影响翻译 provider；AI 分析继续保持 ChatGPT / Gemini 跳转和复制 Prompt。 |
| `最新prompt.md` | 用户明确说明不处理未跟踪文件。 |

## 移除 AI Insight JSON 工作流批次 - 2026-04-25

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P1-019` | `[x]` | 移除 AI Insight JSON 手动保存工作流 | `docs/plans/0037-remove-ai-insight-json-workflow.md` | `codex/runtime-control-compat` | `-` | 已完成；删除手动 Insight JSON UI/API/state/artifact 缓存，保留 ChatGPT / Gemini / 复制 Prompt / Markdown 摘要导出。推荐 commit message：`refactor(ai): remove manual insight json workflow`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| AI provider implementation | 本批不实现新的 provider、云 API 或 Agent；未来 AI 需要另起显式 opt-in 设计。 |
| `最新prompt.md` | 用户明确说明不处理未跟踪文件。 |

## 文档现实同步批次 - 2026-04-24

Selected tasks:

| Rank | Task ID | Status | Task | Plan | Branch | Commit / PR | Notes |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P0-012` | `[x]` | 文档现实同步与下一轮任务队列计划 | `docs/plans/0030-docs-reality-sync.md` | `codex/runtime-control-compat` | `-` | 已同步文档和任务追踪，不改业务代码；推荐 commit message：`docs: sync project status and next autopilot queue`。 |

Skipped or blocked tasks:

| Task | Reason |
|---|---|
| `GS-P2-003` encrypted sync / backup | Still blocked on sync target, key management, conflict strategy, and explicit opt-in decisions. |
| `GS-P2-005` code signing | Still blocked on certificate, private-key custody, password injection, and timestamp service decisions. |
| SQLite implementation | Planned as `GS-P1-016`; this batch only documents the next queue and does not change persistence. |
| AI provider implementation | Planned as `GS-P1-017`; this batch only documents opt-in design work and does not call providers. |
| Full Job/Event/SSE migration | `GS-P1-014` is now completed as a small runtime bridge; it did not replace the existing frontend polling path. |

## 下一轮 Project Autopilot Safe Loop 候选队列

即使本表包含多于 5 个候选，当前批次也只处理前 5 个可安全执行的任务。

| 排名 | 任务 ID | 状态 | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P2-008` | `[ ]` | Modern asset pipeline | `docs/plans/0040-frontend-modernization-roadmap.md` | `-` | `-` | `GS-P2-015` 已插入并完成；下一项仍是 Modern asset pipeline。建立 Vite 构建、allowlisted modern assets、runtime copy 和缺失 fallback。开始前需创建或更新任务级计划。 |

## 后续前端现代化顺序队列

这些任务不是当前下一批可直接执行任务；只有前序任务完成并写入验证记录后，才进入 Selected tasks。

| 顺序 | 任务 ID | 状态 | 任务 | 前置条件 | 备注 |
|---:|---|---:|---|---|---|
| 2 | `GS-P2-009` | `[ ]` | React 诊断页试点 | `GS-P2-008` 完成 | 先迁移诊断弹层，保留 Vanilla fallback。 |
| 3 | `GS-P2-010` | `[ ]` | React 设置页试点 | `GS-P2-009` 完成 | 验证敏感字段、保存流程和 DPAPI 边界。 |
| 4 | `GS-P2-011` | `[ ]` | 静态壳与 bootstrap 收敛 | 诊断和设置试点稳定 | 减少 HTML 大 payload，保留旧 `INITIAL` fallback。 |
| 5 | `GS-P2-012` | `[ ]` | 详情抽屉迁移 | `GS-P2-011` 完成 | 不丢失标签 / 笔记编辑体验优化能力。 |
| 6 | `GS-P2-013` | `[ ]` | 发现页迁移 | `GS-P2-012` 稳定 | 初期继续轮询，不强制切 SSE。 |
| 7 | `GS-P2-014` | `[ ]` | 主工作台迁移评估与切换 | 前序 islands 稳定 + 浏览器级 smoke test | 必须用 feature flag 保留 legacy workspace。 |

## 已完成或阻塞的上一轮候选

| 任务 ID | 状态 | 说明 |
|---|---:|---|
| `GS-P1-002` | `[x]` | 已新增 `/api/bootstrap`、`/api/repos`、`/api/updates` 和 `/api/discovery/views` 只读边界。 |
| `GS-P1-003` | `[x]` | 已完成 SQLite 迁移与回滚设计，未实施存储切换。 |
| `GS-P1-004` | `[x]` | 已新增内存级 Job/Event runtime 和 `/api/jobs`、`/api/events`。 |
| `GS-P1-005` | `[x]` | 已新增 `/api/events/stream` SSE 快照端点。 |
| `GS-P1-006` | `[x]` | 历史任务已完成；对应缓存和列表端点已被 `GS-P1-019` 取代。 |
| `GS-P1-007` | `[x]` | 已完成发现结果聚类。 |
| `GS-P2-001` | `[x]` | 已完成轻量二维仓库地图 MVP。 |
| `GS-P2-002` | `[x]` | 历史任务已完成；方向已被 `GS-P1-018` 取代。 |
| `GS-P2-003` | `[!]` | 阻塞：同步目标、密钥管理、冲突策略和显式 opt-in 决策未定。 |
| `GS-P2-004` | `[x]` | 已新增本地 SHA256 release manifest。 |
| `GS-P2-005` | `[!]` | 阻塞：证书、私钥保管、密码注入和时间戳服务决策未定。 |
| `GS-P2-006` | `[x]` | 历史评估已完成；当时结论是不启动完整 React / Vite 重写，已由 `GS-P2-007` 细化为局部试点路线。 |
| `GS-P2-007` | `[x]` | 已完成前端现代化总路线与文档同步，新增 `GS-P2-008` ~ `GS-P2-014` 阶段任务。 |
| `GS-P2-015` | `[x]` | 已完成 Runtime UI visual polish；作为 `GS-P2-008` 前的纯 `runtime_ui` 视觉收敛任务，不改变 API、存储或现代化构建链。 |
| `GS-P1-008` | `[x]` | discovery job 失败已安全化。 |
| `GS-P1-009` | `[x]` | JSON body size limit 已完成。 |
| `GS-P1-010` | `[x]` | `/api/repo-details` 已保护。 |
| `GS-P1-011` | `[x]` | DPAPI UI forbidden 已完成。 |
| `GS-P1-012` | `[x]` | HTTP route exception logs 脱敏已完成。 |

## Sprint 执行规则

- 按排名顺序逐个执行任务，不并行、不混合范围。
- 跳过已标记为 `[x]` 的任务。
- 如果少于 5 个可执行任务，只完成可安全执行的任务，并说明未补满原因。
- 如果任务阻塞，标记为 `[!]`，写清跳过原因，然后继续下一个安全任务。
- 当前批次选中的每个任务都必须有自己的计划文件。
- 每个任务都必须更新验收条件、`TASKS.md`、`docs/progress/PROGRESS.md` 和本文件。
- 最好一任务一 commit。
- 不要为了凑满 5 个任务而做架构大重写。
