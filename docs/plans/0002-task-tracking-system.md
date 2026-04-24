# 0002 - 建立任务追踪系统

## 任务元信息

- 任务 ID：`GS-P0-002`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 候选排名：`2`
- 推荐 commit message：`docs: 建立 Auto Top 5 Batch Sprint 任务体系`

## 摘要

- 问题：仓库缺少“任务主表 -> Sprint 队列 -> 计划文件 -> 进度日志”的完整闭环。
- 原因：已有任务追踪基础，但没有当前 Auto Top 5 Batch 候选队列文件，也没有把逐任务计划、验证、进度与 commit 建议完整串起来。
- 结果：完成后，Codex 可以自动读取任务文档、刷新候选队列，并按每批最多 5 个任务的统一规则推进。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 当前 Sprint：`docs/sprints/CURRENT_TOP10.md`
- 参考现状：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 已存在基础任务表与进度日志思路。
- 缺少 `docs/sprints/CURRENT_TOP10.md`。
- 候选队列对应计划文件未补齐。
- 任务规则需要统一中文化并保持一致。

## 目标

- 建立稳定的 `TASKS.md`、`PLANS.md`、`docs/plans/*.md`、`docs/progress/PROGRESS.md`、`docs/sprints/CURRENT_TOP10.md` 闭环。
- 为当前候选队列任务补齐计划文件。
- 不实现任何业务功能。

## 非目标

- 不修改 `src/` 业务代码。
- 不推进功能开发。
- 不进行 commit。

## 用户影响

- 仓库维护者能直接用固定流程驱动后续任务。
- 用户不会看到产品功能变化。
- 现有本地优先与隐私边界不变。

## 隐私与显式同意

- 不涉及外部数据传输。
- 不需要新增 opt-in。

## 范围

### 范围内

- 重写 `TASKS.md`
- 重写 `PLANS.md`
- 重写 `docs/plans/PLAN_TEMPLATE.md`
- 重写 `docs/progress/PROGRESS.md`
- 创建 `docs/sprints/CURRENT_TOP10.md`
- 创建候选队列对应计划文件

### 范围外

- `src/` 代码
- 业务功能实现

## 架构触点

- 运行时模块：无
- HTTP / API：无
- 状态 / 持久化：无
- UI：无

## 数据模型

- 新字段：文档级任务元信息
- 新文件：`docs/sprints/CURRENT_TOP10.md`、`docs/plans/0001-0010*.md`
- 迁移需求：无运行时迁移

## API 与契约

- 无运行时 API 变更

## 执行步骤

1. 读取现有执行文档与约束。
   预期结果：确认当前任务体系边界。
   回滚路径：不写入文件。
2. 重写核心任务管理文档。
   预期结果：统一中文规则、状态和追踪流程。
   回滚路径：回退这些文档。
3. 创建当前 Sprint 候选队列与对应计划文件。
   预期结果：后续任务可按固定顺序直接执行。
   回滚路径：删除新增文档并回退修改。

## 风险

- 技术风险：低，主要是文档一致性风险。
- 产品风险：低，不涉及行为变化。
- 隐私 / 安全风险：无新增风险。

## 验证

- 单元测试：不适用
- 集成测试：不适用
- 手动检查：
  - 检查任务 ID、计划路径、Sprint 候选排名是否一致
  - 检查没有 `src/` 文件变更
  - 检查所有核心文档均为中文

## 发布与回滚

- 直接以文档形式生效。
- 回滚时删除新增计划文件与 Sprint 文件，并回退相关文档。

## 文档更新

- `TASKS.md`
- `PLANS.md`
- `docs/plans/PLAN_TEMPLATE.md`
- `docs/progress/PROGRESS.md`
- `docs/sprints/CURRENT_TOP10.md`

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-22` | `[~]` | 开始建立仓库任务追踪基础，先确认战略、路线图、计划模板、架构与安全边界。 |
| `2026-04-22` | `[x]` | 建立初版任务追踪文档。 |
| `2026-04-23` | `[x]` | 扩展为 Auto Top 5 Batch Sprint 体系，并统一改成中文。 |

## 验证记录

- 已运行测试：无
- 手动验证：
  - 人工检查 `TASKS.md`、`PLANS.md`、`docs/progress/PROGRESS.md`、`docs/sprints/CURRENT_TOP10.md`
  - 人工检查候选队列对应计划文件是否存在
  - `git status --short` 检查未触碰 `src/`
- 尚未覆盖的缺口：无

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
