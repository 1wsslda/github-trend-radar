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
| `P0` | 9 | 0 | 0 | 0 | 9 | 0 |
| `P1` | 7 | 1 | 0 | 0 | 6 | 0 |
| `P2` | 6 | 6 | 0 | 0 | 0 | 0 |

## 当前 Auto Top 5 Batch 候选队列

`docs/sprints/CURRENT_TOP10.md` 可以保留多于 5 个候选；Auto Top 5 Batch Sprint 每批只选择优先级最高、未完成、未阻塞的最多 5 个可安全执行任务。

| 排名 | 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | `P1` | `[x]` | `GS-P1-002` | 清理静态壳与 JSON API 边界 | `docs/plans/0011-json-api-boundary-mvp.md` | `-` | `-` | 已新增 `/api/bootstrap`、`/api/repos`、`/api/updates` 和 `/api/discovery/views` 只读边界。 |
| 2 | `P1` | `[x]` | `GS-P1-003` | SQLite 迁移设计 | `docs/plans/0012-sqlite-migration-design.md` | `-` | `-` | 已完成迁移与回滚设计，未实施存储切换。 |
| 3 | `P1` | `[x]` | `GS-P1-004` | 统一 Job / Event 模型 | `docs/plans/0013-job-event-model-mvp.md` | `-` | `-` | 已新增内存级 Job/Event runtime 和 `/api/jobs`、`/api/events` 只读端点。 |
| 4 | `P1` | `[x]` | `GS-P1-005` | SSE 进度与事件流 | `docs/plans/0014-sse-event-stream-mvp.md` | `-` | `-` | 已新增 `/api/events/stream` SSE 快照端点，保留 loopback/control-token 保护。 |
| 5 | `P1` | `[x]` | `GS-P1-006` | AI Artifact 生命周期与缓存 | `docs/plans/0015-ai-artifact-lifecycle-cache.md` | `-` | `-` | 已扩展本地 AI artifact 元数据与 `/api/ai-artifacts` 列表端点，不接入 provider。 |
| 6 | `P1` | `[ ]` | `GS-P1-007` | 发现结果聚类 | `-` | `-` | `-` | 本批跳过：已达到最多 5 个任务，留待下一批。 |
| 7 | `P2` | `[ ]` | `GS-P2-001` | 仓库地图 / 可视化体验 | `-` | `-` | `-` | P2 后置，等待 P1 边界稳定。 |
| 8 | `P2` | `[ ]` | `GS-P2-002` | 可选本地翻译模型支持 | `-` | `-` | `-` | P2 后置，必须保持可选。 |
| 9 | `P2` | `[ ]` | `GS-P2-003` | 加密同步 / 备份 | `-` | `-` | `-` | P2 后置，涉及隐私和同步边界。 |
| 10 | `P2` | `[ ]` | `GS-P2-004` | 发布加固与 AV 误报缓解 | `-` | `-` | `-` | P2 后置，属于发布层优化。 |

## 候选队列之外的任务池

| 优先级 | 状态 | 任务 ID | 任务 | Plan | 备注 |
|---|---:|---|---|---|---|
| `P1` | `[ ]` | `GS-P1-007` | 发现结果聚类 | `-` | 在主 P0 闭环稳定后再推进。 |
| `P2` | `[ ]` | `GS-P2-001` | 仓库地图 / 可视化体验 | `-` | 属于差异化能力，后于核心工作流。 |
| `P2` | `[ ]` | `GS-P2-002` | 可选本地翻译模型支持 | `-` | 必须保持可选，不拖慢默认上手体验。 |
| `P2` | `[ ]` | `GS-P2-003` | 加密同步 / 备份 | `-` | 涉及隐私和同步边界，先写计划。 |
| `P2` | `[ ]` | `GS-P2-004` | 发布加固与 AV 误报缓解 | `-` | 属于打包与分发优化，不是当前 Sprint 任务。 |
| `P2` | `[ ]` | `GS-P2-005` | 代码签名 | `-` | 位于打包加固之后的信任建设工作。 |
| `P2` | `[ ]` | `GS-P2-006` | 前端现代化评估 | `-` | 只在当前工作流边界稳定后评估。 |
