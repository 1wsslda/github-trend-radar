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
| `P1` | 稳定 API、持久化、任务事件和 AI-ready 边界 | `GS-P1-001` ~ `GS-P1-017` | P1 API 安全兼容收紧已完成；下一轮优先处理 Job/Event/SSE 统一接入、Update Inbox 增强、SQLite 第一阶段和 AI provider opt-in 设计。 |
| `P2` | 等边界稳定后推进差异化、发布和同步能力 | `GS-P2-001` ~ `GS-P2-006` | 聚类地图、本地翻译和发布 manifest 已完成；加密同步 / 备份、代码签名继续阻塞。 |

## 已完成的当前能力

### 产品闭环

- 保存发现视图。
- 标签和笔记。
- Update Inbox MVP。
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
- AI artifact metadata cache。

### 智能化和可视化

- 手动结构化 AI Insight artifact。
- 本地发现结果聚类。
- 轻量二维仓库地图。
- 可选 loopback-only Ollama-style 本地翻译 provider。

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
| `GS-P1-001` | AI Insight schema MVP | `[x]` | 已定义 `gitsonar.repo_insight.v1`，支持手动保存 / 删除。 |
| `GS-P1-002` | JSON API boundary MVP | `[x]` | 已新增 bootstrap、repos、updates、discovery views 只读边界。 |
| `GS-P1-003` | SQLite 迁移设计 | `[x]` | 已完成设计，未实施存储切换。 |
| `GS-P1-004` | Job / Event 模型 MVP | `[x]` | 已新增内存级 runtime 和 `/api/jobs`、`/api/events`。 |
| `GS-P1-005` | SSE 事件流 MVP | `[x]` | 已新增 `/api/events/stream` SSE 快照端点。 |
| `GS-P1-006` | AI Artifact 生命周期与缓存 | `[x]` | 已扩展 artifact metadata 和 `/api/ai-artifacts`。 |
| `GS-P1-007` | 发现结果聚类 | `[x]` | 已完成本地聚类、state/API 字段和 UI 展示。 |
| `GS-P1-008` | Discovery job failure 安全化 | `[x]` | 已返回安全摘要并脱敏日志。 |
| `GS-P1-009` | JSON body size limit | `[x]` | 已限制本地 JSON POST body。 |
| `GS-P1-010` | `/api/repo-details` control-token 保护 | `[x]` | 已保护会触发网络和缓存写入的 GET。 |
| `GS-P1-011` | DPAPI UI forbidden | `[x]` | DPAPI 调用已禁止弹系统 UI。 |
| `GS-P1-012` | HTTP route exception log 脱敏 | `[x]` | 未预期 route 异常日志已脱敏。 |
| `GS-P1-013` | 只读 API control-token 收紧评估与兼容迁移 | `[x]` | `bootstrap/repos/updates/settings/status/discovery` 等只读端点已要求 loopback/control-token，前端统一 header 路径保持兼容。 |

下一轮候选：

| Task ID | 任务主题 | 状态 | 说明 |
|---|---|---:|---|
| `GS-P1-014` | 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE | `[ ]` | 将已有后台流程逐步接入同一 runtime，不做大重写。 |
| `GS-P1-015` | Update Inbox 增强 | `[ ]` | 增加自上次查看以来、摘要和重要性解释。 |
| `GS-P1-016` | SQLite 迁移第一阶段 | `[ ]` | 建立 JSON 导入 / 导出兼容和回滚骨架，暂不做破坏性切换。 |
| `GS-P1-017` | AI provider opt-in 设计 | `[ ]` | 设计本地 Ollama / OpenAI-compatible provider pipeline 和隐私预览。 |

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
| `GS-P2-002` | 可选本地翻译模型支持 | `[x]` | 已新增显式 opt-in 的 loopback-only Ollama-style provider。 |
| `GS-P2-003` | 加密多设备同步 / 备份 | `[!]` | 阻塞于同步目标、密钥管理、冲突策略和 opt-in 决策。 |
| `GS-P2-004` | 发布加固与 AV 误报缓解 | `[x]` | 已新增本地 SHA256 release manifest 脚本。 |
| `GS-P2-005` | 代码签名 | `[!]` | 阻塞于证书、私钥保管、密码注入和时间戳服务决策。 |
| `GS-P2-006` | 前端现代化路径评估 | `[x]` | 已完成评估，当前不启动 React / Vite 重写。 |

P2 执行规则：

- 不要为视觉新奇牺牲研究效率。
- 不要让云同步或 AI 成为强制依赖。
- 不要把中心化账号体系作为默认方向。

## 默认顺序

1. `P1 security/API compatibility`
   只读 API control-token 收紧评估与兼容迁移。
2. `P1 runtime unification`
   刷新、发现、更新检查接入统一 Job/Event/SSE。
3. `P1 update judgement`
   Update Inbox 自上次查看以来、摘要、重要性解释。
4. `P1 persistence migration`
   SQLite 第一阶段导入 / 导出兼容和回滚骨架。
5. `P1 AI provider opt-in`
   本地 Ollama / OpenAI-compatible provider pipeline 设计。

## 默认不做

除非有单独计划文件明确说明，否则以下不是默认下一步：

- 完整 React 重写。
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
