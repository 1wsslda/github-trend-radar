# GitSonar 计划规则

`PLANS.md` 定义本仓库计划文档如何创建、追踪、验证与关闭。

最后刷新：`2026-04-23`

## 文件职责

- `docs/plans/PLAN_TEMPLATE.md`：新计划文件默认模板
- `docs/plans/*.md`：一任务一文件，记录范围、验证、回滚、验收与推荐 commit message
- `TASKS.md`：任务状态与元数据事实来源
- `docs/sprints/CURRENT_TOP10.md`：当前自动排序的 Top 10 执行队列
- `docs/progress/PROGRESS.md`：跨任务的时间序列状态日志
- `docs/roadmap/ROADMAP.md`：优先级分层与执行顺序参考

## 什么时候必须写计划

以下情况必须先创建或更新计划，再开始实现：

- 架构迁移
- 持久化迁移
- 新的后台任务系统
- AI provider 或云集成
- 隐私、同步、Token 或数据边界变更
- 重要导航或工作流重写
- 任意 Auto Top 10 Sprint 任务在开始实现前

## 命名规则

- 计划文件统一放在 `docs/plans/`。
- 文件名使用 `NNNN-short-title.md`，例如 `0003-network-diagnostics-mvp.md`。
- 一个任务只对应一个计划文件。
- 继续同一任务时，复用原计划文件，不要重复创建。

## Auto Top 10 Sprint 规则

- 开始新的 Auto Top 10 回合前，先刷新 `docs/sprints/CURRENT_TOP10.md`。
- 当前 Top 10 中的每个任务，在实现前都必须有独立计划文件。
- 计划、实现、验证、进度更新、commit 建议必须逐任务记录。
- 不要把多个 Top 10 任务混成一个计划、一个验收记录或一个完成状态。
- 最好一任务一 commit。如果当前回合不提交，也必须保留推荐 commit message。

## 单任务执行流程

1. 开始任务。
   - 在 `TASKS.md` 中标记为 `[~]`
   - 如果任务在当前 Sprint 队列中，同步更新 `docs/sprints/CURRENT_TOP10.md`
   - 在 `docs/progress/PROGRESS.md` 中追加一条记录
   - 创建或刷新该任务的计划文件
2. 实现任务。
   - 只做该任务范围内的改动
   - 不顺手混入无关功能
   - 保持改动小步、可回滚
   - 保持本地优先、隐私优先、Windows 桌面工作流、JSON 兼容、loopback-only 与 control-token 保护
3. 验证任务。
   - 运行可用测试，或写清楚手动验证步骤
   - 把验证结果记录进计划文件
4. 关闭任务。
   - 更新计划中的验收结果
   - 更新 `TASKS.md`
   - 更新 `docs/sprints/CURRENT_TOP10.md`
   - 在 `docs/progress/PROGRESS.md` 追加完成记录
   - 记录 branch 与 commit / PR；没有就写 `-`
   - 记录推荐 commit message

## 阻塞任务规则

如果任务阻塞：

- 在 `TASKS.md` 中标记为 `[!]`
- 在 `docs/sprints/CURRENT_TOP10.md` 中标记为 `[!]`
- 在计划文件中记录阻塞原因与当前安全状态
- 在 `docs/progress/PROGRESS.md` 中追加阻塞记录
- 不要强做，继续处理下一个安全任务

## 验收规则

只有满足以下条件，任务才可以标记为 `[x]`：

- 计划仍然准确反映实际范围，或范围变更已明确记录
- 验收条件已打勾，或写清楚原因
- 验证已执行，或者已记录无法执行的原因
- 回滚说明仍然可操作
- 相关文档已同步更新
- `TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md` 状态一致
- branch 与 commit / PR 字段有值，或明确写为 `-`

## 推荐工作顺序

1. 先读战略、路线图、架构、安全和当前 Sprint 队列。
2. 确认下一个优先级最高且安全的任务。
3. 创建或更新该任务的计划文件。
4. 只实现这个任务。
5. 验证任务结果。
6. 更新任务状态、Sprint 队列、进度日志和验收记录。
7. 如果环境允许，做该任务自己的 commit；否则记录推荐 commit message。
