# GitSonar Roadmap

本文件从 `docs/strategy/GITSONAR_STRATEGY.md` 提炼默认优先级，并作为后续实施的阶段性指引。

## 文档分工

- `docs/strategy/GITSONAR_STRATEGY.md`：产品和架构长期方向。
- `docs/roadmap/ROADMAP.md`：`P0 / P1 / P2` 优先级、阶段目标和默认顺序。
- `TASKS.md`：任务当前状态、计划文件、分支、commit / PR 的主索引。
- `docs/progress/PROGRESS.md`：按时间记录状态变化和里程碑。
- `PLANS.md` 与 `docs/plans/*.md`：计划编写、验收、验证和回滚规范。

## 执行原则

- 保持 GitSonar 的 Windows-first、local-first、privacy-first 定位。
- 不做 big-bang rewrite。
- 优先做小步、可回滚、边界清晰的变更。
- 任何 AI、云 API、同步、Token 或用户数据外发都必须显式 opt-in。
- 任何架构迁移都必须先写计划，再实施。
- 路线图负责优先级，不负责 commit 级追踪；状态细节统一写进 `TASKS.md` 和 `docs/progress/PROGRESS.md`。

## 当前优先级快照

| Priority | 目标 | 对应任务 | 当前说明 |
|---|---|---|---|
| `P0` | 补齐“发现之后的管理”闭环并完成文档现实同步 | `GS-P0-001` ~ `GS-P0-012` | 当前 P0 MVP、诊断、Markdown 导出、安全加固和文档同步均已完成。 |
| `P1` | 稳定 API、持久化、任务事件和 AI-ready 边界 | `GS-P1-001` ~ `GS-P1-019` | 当前 P1 队列已完成 OpenAI-compatible 翻译 API，并通过 `GS-P1-019` 将 AI 分析收回为 prompt handoff，不再维护手动 Insight JSON 缓存。 |
| `P2` | 等边界稳定后推进差异化、发布、同步和前端现代化能力 | `GS-P2-001` ~ `GS-P2-014` | 聚类地图、本地翻译和发布 manifest 已完成；前端现代化总路线已建立，下一步从 `GS-P2-008` Modern asset pipeline 开始；加密同步 / 备份、代码签名继续阻塞。 |

## 已完成的当前能力

### 产品闭环

- 保存发现视图。
- 标签和笔记。
- Update Inbox MVP。
- Update Inbox 本地摘要、重要性解释和自上次查看以来提示。
- 推荐 / 排名原因。
- 忽略反馈。
- Markdown 摘要导出。
- 网络 / 运行诊断。

### API 与运行时

- JSON API boundary MVP。
- SQLite 迁移设计。
- 内存级 Job / Event runtime。
- SSE event snapshot endpoint。
- Discovery job runtime。
- Refresh / discovery / favorite update check bridge into Job/Event runtime。
- SQLite migration dry-run schema and backup / rollback path skeleton。

### 智能化和可视化

- AI 分析当前只保留 prompt handoff：ChatGPT / Gemini 跳转、复制 Prompt 和 Markdown 摘要导出。
- AI provider opt-in design for local/cloud modes, privacy previews, and artifact traceability。
- 本地发现结果聚类。
- 轻量二维仓库地图。
- 可选 OpenAI-compatible 翻译 API provider，默认仍为 Google Translate，API Key 本地 DPAPI 加密保存。

### 安全与发布

- DPAPI `CRYPTPROTECT_UI_FORBIDDEN`。
- settings/bootstrap/diagnostics/status/discovery job payload 脱敏。
- HTTP route exception log 脱敏。
- JSON body size limit。
- `/api/repo-details` loopback/control-token 保护。
- 剩余只读 JSON API 已要求 loopback/control-token。
- 本地 release checksum manifest 脚本。

## P0

目标：在不改变当前运行栈的前提下，强化现有产品闭环。

当前状态：已完成。

任务映射：

| Task ID | 任务主题 | 状态 | 说明 |
|---|---|---:|---|
| `GS-P0-001` | Codex 执行规则与文档基线 | `[x]` | 已建立仓库级工作指南。 |
| `GS-P0-002` | 任务追踪体系与 Auto Top 5 Batch Sprint | `[x]` | 已建立任务、计划、进度和 Sprint 队列规则。 |
| `GS-P0-003` | 网络 / 运行诊断 MVP | `[x]` | 已提供本地诊断面板和 `/api/diagnostics`。 |
| `GS-P0-004` | 标签与笔记 MVP | `[x]` | 已支持本地标签、笔记、搜索命中和导入 / 导出兼容。 |
| `GS-P0-005` | 保存发现视图 MVP | `[x]` | 已支持保存、载入、重跑和删除发现视图。 |
| `GS-P0-006` | Update Inbox MVP | `[x]` | 已支持已读、置顶、忽略和优先级排序。 |
| `GS-P0-007` | 推荐 / 排名原因 | `[x]` | 已在发现卡片和详情中展示原因。 |
| `GS-P0-008` | 忽略反馈 | `[x]` | 已记录忽略原因并参与后续排序信号。 |
| `GS-P0-009` | Markdown 摘要导出 | `[x]` | 已支持单仓库、批量和对比摘要复制 / 导出。 |
| `GS-P0-010` | 代理和诊断脱敏 | `[x]` | 已避免用户可见 payload 暴露代理凭据和本地路径。 |
| `GS-P0-011` | 刷新状态错误安全化 | `[x]` | 已避免 status/bootstrap/UI 暴露原始异常。 |
| `GS-P0-012` | 文档现实同步与下一轮队列计划 | `[x]` | 已同步 README、CHANGELOG、架构、安全、路线图和任务队列。 |

## P1

目标：在 P0 闭环稳定后，再稳定数据流、后台任务、持久化迁移和 AI-ready 边界。

当前状态：基础 MVP 已完成，下一轮继续做兼容收紧和迁移骨架。

已完成任务：

| Task ID | 任务主题 | 状态 | 说明 |
|---|---|---:|---|
| `GS-P1-001` | AI Insight schema MVP | `[x]` | 历史任务已完成；对应运行时表面已被 `GS-P1-019` 取代，不再维护手动 JSON 保存工作流。 |
| `GS-P1-002` | JSON API boundary MVP | `[x]` | 已新增 bootstrap、repos、updates、discovery views 只读边界。 |
| `GS-P1-003` | SQLite 迁移设计 | `[x]` | 已完成设计，未实施存储切换。 |
| `GS-P1-004` | Job / Event 模型 MVP | `[x]` | 已新增内存级 runtime 和 `/api/jobs`、`/api/events`。 |
| `GS-P1-005` | SSE 事件流 MVP | `[x]` | 已新增 `/api/events/stream` SSE 快照端点。 |
| `GS-P1-006` | AI Artifact 生命周期与缓存 | `[x]` | 历史任务已完成；对应缓存和列表运行时已被 `GS-P1-019` 取代。 |
| `GS-P1-007` | 发现结果聚类 | `[x]` | 已完成本地聚类、state/API 字段和 UI 展示。 |
| `GS-P1-008` | Discovery job failure 安全化 | `[x]` | 已返回安全摘要并脱敏日志。 |
| `GS-P1-009` | JSON body size limit | `[x]` | 已限制本地 JSON POST body。 |
| `GS-P1-010` | `/api/repo-details` control-token 保护 | `[x]` | 已保护会触发网络和缓存写入的 GET。 |
| `GS-P1-011` | DPAPI UI forbidden | `[x]` | DPAPI 调用已禁止弹系统 UI。 |
| `GS-P1-012` | HTTP route exception log 脱敏 | `[x]` | 未预期 route 异常日志已脱敏。 |
| `GS-P1-013` | 只读 API control-token 收紧评估与兼容迁移 | `[x]` | `bootstrap/repos/updates/settings/status/discovery` 等只读端点已要求 loopback/control-token，前端统一 header 路径保持兼容。 |
| `GS-P1-014` | 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE | `[x]` | Refresh、discovery 和 favorite update check 已桥接到通用 Job/Event runtime，现有 UI 轮询路径保持不变。 |
| `GS-P1-015` | Update Inbox 增强 | `[x]` | 已增加自上次查看以来提示、本地变化摘要和重要性解释。 |
| `GS-P1-016` | SQLite 迁移第一阶段 | `[x]` | 已新增 SQLite schema helper、dry-run 计数和备份 / 回滚路径规划；未切换事实存储。 |
| `GS-P1-017` | AI provider opt-in 设计 | `[x]` | 已设计本地 / 云端 provider 模式、隐私预览、artifact 可追溯和后续实施切片；未实现 provider。 |
| `GS-P1-018` | OpenAI-compatible 翻译 API | `[x]` | 已完成；删除旧本机翻译 provider 路径，默认保留 Google，新增显式 opt-in 的 Chat Completions 风格翻译 API。 |
| `GS-P1-019` | 移除 AI Insight JSON 手动保存工作流 | `[x]` | 已完成；删除详情页手动 JSON 面板、本地缓存和旧 API，保留 prompt handoff 与 Markdown 摘要导出。 |

下一轮候选：

| Task ID | 任务主题 | 状态 | 说明 |
|---|---|---:|---|
| `-` | 当前 P1 队列 | `[x]` | `GS-P1-001` ~ `GS-P1-017` 均已完成；新的 P1 任务需要单独进入下一轮队列。 |

P1 执行规则：

- 不要同时迁移持久化、API 形态和前端渲染。
- 不要把 AI 做成默认开启的黑盒。
- 在 AI provider 成熟前，保留现有 prompt handoff 路径。

## P2

目标：在工作流、数据模型和迁移路径稳定后，再补差异化能力、同步能力和发布信任能力。

任务映射：

| Task ID | 任务主题 | 状态 | 说明 |
|---|---|---:|---|
| `GS-P2-001` | 仓库地图 / 可视化体验 | `[x]` | 已新增轻量二维主题地图。 |
| `GS-P2-002` | 可选本地翻译模型支持 | `[x]` | 历史任务已完成；方向已被 `GS-P1-018` 取代，后续使用 OpenAI-compatible 翻译 API。 |
| `GS-P2-003` | 加密多设备同步 / 备份 | `[!]` | 阻塞于同步目标、密钥管理、冲突策略和 opt-in 决策。 |
| `GS-P2-004` | 发布加固与 AV 误报缓解 | `[x]` | 已新增本地 SHA256 release manifest 脚本。 |
| `GS-P2-005` | 代码签名 | `[!]` | 阻塞于证书、私钥保管、密码注入和时间戳服务决策。 |
| `GS-P2-006` | 前端现代化路径评估 | `[x]` | 历史评估任务已完成；结论代表当时不启动完整 React / Vite 重写，不再代表永久不迁移。 |
| `GS-P2-007` | 前端现代化总路线与文档同步 | `[x]` | 已新增 `docs/plans/0040-frontend-modernization-roadmap.md`，明确局部 React/Vite 试点和主工作台后置切换路线。 |
| `GS-P2-008` | Modern asset pipeline | `[ ]` | 下一步可安全执行；建立 Vite 构建、allowlisted modern assets、运行时复制和缺失 fallback。 |
| `GS-P2-009` | React 诊断页试点 | `[ ]` | 依赖 `GS-P2-008`；先迁移最低风险诊断弹层，验证 React island。 |
| `GS-P2-010` | React 设置页试点 | `[ ]` | 依赖 `GS-P2-009`；验证敏感字段、保存流程和 DPAPI 边界。 |
| `GS-P2-011` | 静态壳与 bootstrap 收敛 | `[ ]` | 依赖设置和诊断试点稳定；减少 HTML 大 payload。 |
| `GS-P2-012` | 详情抽屉迁移 | `[ ]` | 依赖 `GS-P2-011`；迁移标签、笔记、README 摘要和详情交互。 |
| `GS-P2-013` | 发现页迁移 | `[ ]` | 依赖详情抽屉迁移稳定；迁移 Discovery View、进度、工具条和主题地图。 |
| `GS-P2-014` | 主工作台迁移评估与切换 | `[ ]` | 依赖诊断、设置、详情和发现页稳定，并需要浏览器级 smoke test 与 feature flag。 |

P2 执行规则：

- 不要为视觉新奇牺牲研究效率。
- 不要让云同步或 AI 成为强制依赖。
- 不要把中心化账号体系作为默认方向。
- 前端现代化必须按 `GS-P2-008` -> `GS-P2-014` 顺序推进；不能跳过低风险试点直接迁移主工作台。
- 除 `GS-P2-007` 外，每个前端现代化实现任务开始前都必须有任务级计划、fallback / 回滚说明和验证记录。

## 前端现代化路线

`GS-P2-006` 已完成的是历史评估：当时不启动完整 React / Vite 重写。新的路线不是推翻本地优先和小步迭代原则，而是把前端现代化拆成可发布、可回滚、可单独验收的局部试点。

目标形态：

```text
Python Runtime
  -> Local HTTP API
  -> Static HTML Shell
  -> Built frontend assets
  -> React islands / migrated React workspace
  -> Desktop browser / WebView shell
```

默认迁移顺序：

```text
Modern asset pipeline
  -> React 诊断页
  -> React 设置页
  -> Static Shell + Bootstrap 收敛
  -> 详情抽屉
  -> 发现页
  -> 主工作台迁移评估与切换
```

约束：

- 用户机器运行 GitSonar 不依赖 Node。
- 构建产物必须随仓库或发布产物提供。
- `/api/*` 继续要求 loopback + control token。
- `/assets/modern/*` 只能暴露 allowlisted 只读构建产物。
- 主工作台迁移必须后置，并通过 feature flag 保留 legacy workspace 回退路径。

## 默认顺序

当前默认顺序中的 P1 队列已完成。下一轮应先重新读取 `TASKS.md` 与 `CURRENT_TOP10.md`，只选择仍未完成、未阻塞且安全的任务。前端现代化方向默认只从 `GS-P2-008` 开始，不直接执行后续 React 页面迁移。

## 默认不做

除非有单独计划文件明确说明，否则以下不是默认下一步：

- 完整 React 大重写或直接迁移主工作台。
- 立即切到 FastAPI。
- 立即切到 SQLite。
- AI Agent orchestration。
- 中心化 SaaS 后端。
- 强制云同步。
- 加密同步 / 备份实现。
- 代码签名实现。

## 路线图维护规则

- 当优先级或阶段目标变化时，更新 `docs/roadmap/ROADMAP.md`。
- 当任务状态、分支、commit / PR 变化时，更新 `TASKS.md` 和 `docs/progress/PROGRESS.md`。
- 当某个任务需要明确范围、回滚和验收时，创建或更新对应的 `docs/plans/*.md`。
