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
| `P1` | 7 | 0 | 0 | 0 | 7 | 0 |
| `P2` | 6 | 4 | 0 | 0 | 2 | 0 |

## 当前 Auto Top 5 Batch 候选队列

`docs/sprints/CURRENT_TOP10.md` 可以保留多于 5 个候选；Auto Top 5 Batch Sprint 每批只选择优先级最高、未完成、未阻塞的最多 5 个可安全执行任务。

| 排名 | 优先级 | 状态 | 任务 ID | 任务 | Plan | Branch | Commit / PR | 备注 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | `P1` | `[x]` | `GS-P1-002` | 清理静态壳与 JSON API 边界 | `docs/plans/0011-json-api-boundary-mvp.md` | `-` | `-` | 已新增 `/api/bootstrap`、`/api/repos`、`/api/updates` 和 `/api/discovery/views` 只读边界。 |
| 2 | `P1` | `[x]` | `GS-P1-003` | SQLite 迁移设计 | `docs/plans/0012-sqlite-migration-design.md` | `-` | `-` | 已完成迁移与回滚设计，未实施存储切换。 |
| 3 | `P1` | `[x]` | `GS-P1-004` | 统一 Job / Event 模型 | `docs/plans/0013-job-event-model-mvp.md` | `-` | `-` | 已新增内存级 Job/Event runtime 和 `/api/jobs`、`/api/events` 只读端点。 |
| 4 | `P1` | `[x]` | `GS-P1-005` | SSE 进度与事件流 | `docs/plans/0014-sse-event-stream-mvp.md` | `-` | `-` | 已新增 `/api/events/stream` SSE 快照端点，保留 loopback/control-token 保护。 |
| 5 | `P1` | `[x]` | `GS-P1-006` | AI Artifact 生命周期与缓存 | `docs/plans/0015-ai-artifact-lifecycle-cache.md` | `-` | `-` | 已扩展本地 AI artifact 元数据与 `/api/ai-artifacts` 列表端点，不接入 provider。 |
| 6 | `P1` | `[x]` | `GS-P1-007` | 发现结果聚类 | `docs/plans/0016-discovery-result-clustering.md` | `codex/runtime-control-compat` | `-` | 已新增本地 discovery result 聚类、state/API 字段和发现页主题展示。 |
| 7 | `P2` | `[x]` | `GS-P2-001` | 仓库地图 / 可视化体验 | `docs/plans/0017-repo-map-visualization-mvp.md` | `codex/runtime-control-compat` | `-` | 已新增发现页轻量二维主题地图和选中本组交互。 |
| 8 | `P2` | `[x]` | `GS-P2-002` | 可选本地翻译模型支持 | `docs/plans/0019-optional-local-translation-model.md` | `codex/runtime-control-compat` | `-` | 已新增显式可选的本地 Ollama 类翻译 provider、loopback URL 校验和设置 UI；默认仍保持现有 Google Translate 行为。 |
| 9 | `P2` | `[ ]` | `GS-P2-003` | 加密同步 / 备份 | `-` | `-` | `-` | P2 后置，涉及隐私和同步边界。 |
| 10 | `P2` | `[x]` | `GS-P2-004` | 发布加固与 AV 误报缓解 | `docs/plans/0018-release-hardening-av-mitigation.md` | `codex/runtime-control-compat` | `-` | 已新增本地 SHA256 release manifest 脚本，不改签名或打包策略。 |

## 候选队列之外的任务池

| 优先级 | 状态 | 任务 ID | 任务 | Plan | 备注 |
|---|---:|---|---|---|---|
| `P1` | `[x]` | `GS-P1-007` | 发现结果聚类 | `docs/plans/0016-discovery-result-clustering.md` | 已完成本地聚类 MVP，不接入 AI provider。 |
| `P2` | `[x]` | `GS-P2-001` | 仓库地图 / 可视化体验 | `docs/plans/0017-repo-map-visualization-mvp.md` | 已完成轻量二维主题地图 MVP。 |
| `P2` | `[x]` | `GS-P2-002` | 可选本地翻译模型支持 | `docs/plans/0019-optional-local-translation-model.md` | 已完成可选本地 Ollama 类 provider，不下载模型、不改变默认翻译路径。 |
| `P2` | `[ ]` | `GS-P2-003` | 加密同步 / 备份 | `-` | 涉及隐私和同步边界，先写计划。 |
| `P2` | `[x]` | `GS-P2-004` | 发布加固与 AV 误报缓解 | `docs/plans/0018-release-hardening-av-mitigation.md` | 已补本地 release checksum manifest。 |
| `P2` | `[ ]` | `GS-P2-005` | 代码签名 | `-` | 位于打包加固之后的信任建设工作。 |
| `P2` | `[ ]` | `GS-P2-006` | 前端现代化评估 | `-` | 只在当前工作流边界稳定后评估。 |
