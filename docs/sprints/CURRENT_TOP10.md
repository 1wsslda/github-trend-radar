# 当前 Top 10 Sprint

本文件记录当前自动排序后的 Top 10 任务队列。

最后刷新：`2026-04-23`

## 选择规则

Codex 选择当前 Top 10 时，应按以下顺序判断：

1. 路线图优先级：P0 高于 P1，P1 高于 P2
2. 用户价值更高的优先
3. 风险更低、改动更小的优先
4. 能解锁后续工作的优先
5. 保持本地优先与 Windows 桌面工作流的优先
6. 不需要大重写的优先

## 当前 Top 10

| 排名 | 任务 ID | 状态 | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P0-001` | `[x]` | 添加 Codex 指南与战略文档 | `docs/plans/0001-codex-guidance-docs.md` | `-` | `-` | 基础规则文档已刷新。 |
| 2 | `GS-P0-002` | `[x]` | 建立任务追踪系统 | `docs/plans/0002-task-tracking-system.md` | `-` | `-` | 已建立 TASKS / PLANS / PROGRESS / CURRENT_TOP10 闭环。 |
| 3 | `GS-P0-003` | `[x]` | 网络诊断 MVP | `docs/plans/0003-network-diagnostics-mvp.md` | `-` | `-` | 已上线本地诊断面板与 `/api/diagnostics`。 |
| 4 | `GS-P0-004` | `[x]` | 仓库标签 + 笔记 MVP | `docs/plans/0004-tags-notes-mvp.md` | `-` | `-` | 已提供本地标签 / 笔记存储、编辑与搜索入口。 |
| 5 | `GS-P0-005` | `[x]` | 保存发现视图 MVP | `docs/plans/0005-saved-discovery-views-mvp.md` | `-` | `-` | 已支持保存、载入、重跑和删除发现视图。 |
| 6 | `GS-P0-006` | `[x]` | 更新收件箱 MVP | `docs/plans/0006-update-inbox-mvp.md` | `-` | `-` | 已支持更新队列排序、已读、置顶和忽略。 |
| 7 | `GS-P0-007` | `[x]` | 发现结果“为什么推荐”解释 | `docs/plans/0007-why-recommended.md` | `-` | `-` | 推荐理由已出现在卡片和详情页，并优先展示本地反馈。 |
| 8 | `GS-P0-008` | `[x]` | 忽略原因 + 反馈信号 | `docs/plans/0008-ignore-feedback.md` | `-` | `-` | 忽略原因已结构化存储并用于发现降权。 |
| 9 | `GS-P0-009` | `[x]` | 复制仓库 Markdown 摘要 | `docs/plans/0009-copy-markdown-summary.md` | `-` | `-` | 已提供多入口复制仓库 Markdown 摘要。 |
| 10 | `GS-P1-001` | `[x]` | 结构化 AI Insight Schema MVP | `docs/plans/0010-ai-insight-schema-mvp.md` | `-` | `-` | 已定义本地 schema 和显式 opt-in 的保存 / 删除工作流。 |

## Sprint 执行规则

- 按排名顺序执行任务。
- 跳过已标记为 `[x]` 的任务。
- 如果任务阻塞，标记为 `[!]`，写清跳过原因，然后继续下一个安全任务。
- 当前 Top 10 中的每个任务都必须有自己的计划文件。
- 每个任务都必须更新验收条件、`TASKS.md`、`docs/progress/PROGRESS.md` 和本文件。
- 最好一任务一 commit。
- 不要为了完成 Top 10 而做架构大重写。
