# 当前 Auto Top 5 Batch Sprint 候选队列

本文件记录当前自动排序后的候选任务队列。
文件名 `CURRENT_TOP10.md` 因历史兼容保留；Auto Top 5 Batch Sprint 每批只选择优先级最高、未完成、未阻塞的最多 5 个可安全执行任务。

最后刷新：`2026-04-24`

## 选择规则

Codex 选择当前 Auto Top 5 Batch 时，应按以下顺序判断：

1. 路线图优先级：P0 高于 P1，P1 高于 P2
2. 用户价值更高的优先
3. 风险更低、改动更小的优先
4. 能解锁后续工作的优先
5. 保持本地优先与 Windows 桌面工作流的优先
6. 不需要大重写的优先

## 当前候选队列

即使本表包含多于 5 个候选，当前批次也只处理前 5 个可安全执行的任务。

| 排名 | 任务 ID | 状态 | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|
| 1 | `GS-P1-002` | `[x]` | 清理静态壳与 JSON API 边界 | `docs/plans/0011-json-api-boundary-mvp.md` | `-` | `-` | 已新增 `/api/bootstrap`、`/api/repos`、`/api/updates` 和 `/api/discovery/views` 只读边界。 |
| 2 | `GS-P1-003` | `[x]` | SQLite 迁移设计 | `docs/plans/0012-sqlite-migration-design.md` | `-` | `-` | 已完成迁移与回滚设计，未实施存储切换。 |
| 3 | `GS-P1-004` | `[x]` | 统一 Job / Event 模型 | `docs/plans/0013-job-event-model-mvp.md` | `-` | `-` | 已新增内存级 Job/Event runtime 和 `/api/jobs`、`/api/events` 只读端点。 |
| 4 | `GS-P1-005` | `[x]` | SSE 进度与事件流 | `docs/plans/0014-sse-event-stream-mvp.md` | `-` | `-` | 已新增 `/api/events/stream` SSE 快照端点，保留 loopback/control-token 保护。 |
| 5 | `GS-P1-006` | `[x]` | AI Artifact 生命周期与缓存 | `docs/plans/0015-ai-artifact-lifecycle-cache.md` | `-` | `-` | 已扩展本地 AI artifact 元数据与 `/api/ai-artifacts` 列表端点，不接入 provider。 |
| 6 | `GS-P1-007` | `[x]` | 发现结果聚类 | `docs/plans/0016-discovery-result-clustering.md` | `codex/runtime-control-compat` | `-` | 已新增本地 discovery result 聚类、state/API 字段和发现页主题展示。 |
| 7 | `GS-P2-001` | `[x]` | 仓库地图 / 可视化体验 | `docs/plans/0017-repo-map-visualization-mvp.md` | `codex/runtime-control-compat` | `-` | 已新增发现页轻量二维主题地图和选中本组交互。 |
| 8 | `GS-P2-002` | `[ ]` | 可选本地翻译模型支持 | `-` | `-` | `-` | P2 后置，必须保持可选。 |
| 9 | `GS-P2-003` | `[ ]` | 加密同步 / 备份 | `-` | `-` | `-` | P2 后置，涉及隐私和同步边界。 |
| 10 | `GS-P2-004` | `[ ]` | 发布加固与 AV 误报缓解 | `-` | `-` | `-` | P2 后置，属于发布层优化。 |

## Sprint 执行规则

- 按排名顺序逐个执行任务，不并行、不混合范围。
- 跳过已标记为 `[x]` 的任务。
- 如果少于 5 个可执行任务，只完成可安全执行的任务，并说明未补满原因。
- 如果任务阻塞，标记为 `[!]`，写清跳过原因，然后继续下一个安全任务。
- 当前批次选中的每个任务都必须有自己的计划文件。
- 每个任务都必须更新验收条件、`TASKS.md`、`docs/progress/PROGRESS.md` 和本文件。
- 最好一任务一 commit。
- 不要为了凑满 5 个任务而做架构大重写。
