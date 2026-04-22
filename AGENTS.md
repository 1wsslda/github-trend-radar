# GitSonar 工作指南

本文件是 GitSonar 仓库级执行规范，也是 Codex 与未来贡献者的统一工作基线。

## 项目现实

- GitSonar 当前是一个 Windows 原生桌面应用。
- 当前运行形态是：Python 运行时 + 本地 HTTP 服务 + 桌面浏览器 / WebView 外壳 + 内嵌 HTML/CSS/JS。
- 当前代码主要按以下边界组织：
  - `src/gitsonar/runtime/`
  - `src/gitsonar/runtime_github/`
  - `src/gitsonar/runtime_ui/`

## 信息源与优先文档

在提出方案或实施较大改动前，先读这些文件：

1. `docs/strategy/GITSONAR_STRATEGY.md`
2. `docs/roadmap/ROADMAP.md`
3. `docs/plans/PLAN_TEMPLATE.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SECURITY.md`

这些文件的用途如下：

- `GITSONAR_STRATEGY.md`：产品与架构长期方向
- `ROADMAP.md`：当前 P0 / P1 / P2 优先级
- `PLAN_TEMPLATE.md`：复杂功能与迁移任务的计划模板
- `ARCHITECTURE.md`：当前代码与运行时形态
- `SECURITY.md`：隐私、Token、存储与网络边界

如果战略与当前代码存在偏差，不要试图一次性强行对齐。优先做小步、可回滚、能把代码逐步推向目标方向的变更。
除非用户明确说明，否则把当前工作区内容视为事实来源，不因文件之前已被修改就降低其可信度。

## 硬约束

- 不要一步把应用重写成 React / FastAPI / SQLite / AI Agent。
- 不要做 big-bang 式迁移。
- 默认保持本地优先、隐私优先。
- 任何 AI、云 API、同步、Token 或用户数据外发，都必须是显式 opt-in。
- 任何架构迁移都必须先写 `docs/plans/PLAN_TEMPLATE.md` 结构化计划，再实施。
- 优先做小步、可回滚、检查点清晰的迭代。
- 除非任务明确扩大平台范围，否则保持 Windows-first 桌面行为。

## 实现策略

在 GitSonar 中工作时：

- 优先在当前运行时上做增量扩展，而不是引入一套新栈。
- 不要把业务逻辑塞进 `runtime_ui/assets.py`、`runtime_github/__init__.py` 之类聚合文件。
- 把 `runtime/app.py` 当作编排层，而不是新领域逻辑的堆放点。
- 保持 HTTP、GitHub、状态、启动、桌面壳、UI 关注点分离，尊重现有包边界。
- 新增持久化或后台工作流时，从第一天就考虑导入 / 导出和回滚。

## 计划规则

以下场景必须先创建或更新计划文档：

- 架构迁移
- 持久化迁移
- 引入新的后台任务系统
- 引入 AI provider 或云集成
- 修改隐私或同步边界
- 重要的 UI 导航或工作流重写

计划必须明确：

- 当前状态与目标状态
- 为什么现在要做
- 小步、可回滚的执行步骤
- 回滚策略
- 测试与验证步骤
- 隐私 / opt-in 影响

## 任务追踪

仓库执行追踪分散在这些文件中：

- `TASKS.md`：任务状态事实来源
- `PLANS.md`：计划、验证、验收与记录规则
- `docs/progress/PROGRESS.md`：按时间排序的进度日志
- `docs/sprints/CURRENT_TOP10.md`：当前自动排序的 Top 10 Sprint 队列
- `docs/plans/*.md`：任务级计划、回滚说明、验收记录与推荐 commit message

使用规则：

- 开始较大可追踪工作前，先创建或复用任务 ID，格式为 `GS-P0-001`。
- `TASKS.md` 是状态事实来源，状态含义如下：
  - `[ ]` 未开始
  - `[~]` 进行中
  - `[!]` 阻塞
  - `[x]` 已完成
  - `[-]` 取消 / 延后
- 任务状态发生变化时，必须在同一次变更中同步更新 `TASKS.md` 与 `docs/progress/PROGRESS.md`。
- 如果任务位于当前 Sprint 队列中，还必须同步更新 `docs/sprints/CURRENT_TOP10.md`。
- 需要独立计划的任务，使用编号文件，例如 `docs/plans/0003-network-diagnostics-mvp.md`。
- 分支名与 commit / PR 一旦存在就记录；暂时没有则写 `-`。
- 任务未写清验收条件与验证结果前，不要标记为 `[x]`。

## Auto Top 10 Sprint 规则

当用户说“继续”、“做下一批任务”、“自动完成高优先级任务”或类似表达时，默认进入 Auto Top 10 Sprint 模式。

在 Auto Top 10 Sprint 模式下：

1. 先读取：
   - `TASKS.md`
   - `docs/roadmap/ROADMAP.md`
   - `docs/strategy/GITSONAR_STRATEGY.md`
   - `docs/progress/PROGRESS.md`
   - `docs/sprints/CURRENT_TOP10.md`

2. 自动选择优先级最高、未完成、未阻塞的前 10 个任务。

3. 选择优先级时按以下顺序判断：
   - P0 优先于 P1，P1 优先于 P2
   - 用户价值高的优先
   - 风险低、改动小的优先
   - 能解锁后续工作的优先
   - 不破坏本地优先和 Windows 桌面工作流的优先
   - 不需要大重写的优先

4. 不要询问用户“接下来做哪个任务”，除非：
   - 任务会破坏现有用户数据
   - 任务需要外部账号、API Key 或密钥
   - 任务需要大规模架构迁移
   - 任务验收条件互相冲突
   - 当前代码状态无法安全判断

5. 每个任务必须：
   - 创建或更新对应 `docs/plans/*.md`
   - 更新 `TASKS.md`
   - 更新 `docs/sprints/CURRENT_TOP10.md`
   - 更新 `docs/progress/PROGRESS.md`
   - 写清楚验收条件
   - 运行可用测试，或写明手动验证
   - 推荐一个 commit message

6. 每个任务最好单独 commit。

7. 如果一个任务被阻塞：
   - 在 `TASKS.md` 标记为 `[!]`
   - 在对应计划文件中写明阻塞原因
   - 在 `CURRENT_TOP10.md` 中写明跳过原因
   - 继续处理下一个安全任务

8. 不允许为了完成 Top 10 而做大重写。

## 默认交付方式

默认按这个顺序工作：

1. 先澄清用户可见结果
2. 找到最小且兼容现状的改动
3. 适合时补测试或更新测试
4. 行为或架构语义有明显变化时同步更新文档

复杂工作不要直接跳到实现。先基于 `docs/plans/PLAN_TEMPLATE.md` 写清楚计划。
