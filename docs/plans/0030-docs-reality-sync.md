# 文档现实同步与下一轮任务队列计划

## 任务元信息

- 任务 ID：`GS-P0-012`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 候选排名：当前文档现实同步批次第 1 项
- 推荐 commit message：`docs: sync project status and next autopilot queue`

## 标题

`文档现实同步与下一轮任务队列计划`

## 摘要

- 这个任务同步 README、CHANGELOG、架构、安全、路线图、任务总表、Sprint 队列和进度日志，让文档准确反映当前实现。
- 现在做是因为诊断、保存发现视图、标签/笔记、Update Inbox MVP、推荐原因、AI Insight artifact、JSON API、Job/Event、SSE、聚类、地图和安全加固已经完成，但部分文档仍把它们写成规划中。
- 做完后，下一轮 Project Autopilot Safe Loop 可以直接从新的 P1 候选队列继续执行。

## 战略映射

- 战略文档：
  - `docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：
  - `docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：
  - `docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`

## 当前状态

- 当前行为：已完成多个 P0/P1/P2 MVP 和安全加固，但 README、CHANGELOG、ARCHITECTURE、SECURITY、ROADMAP 和队列文档存在滞后。
- 当前技术形态：Python runtime + local HTTP + desktop browser/WebView-style shell + embedded HTML/CSS/JS。
- 已知痛点：已实现能力和“规划中”描述不一致，下一轮自动任务队列缺少明确的 P1 候选顺序。
- 现有约束：本轮只做文档和任务追踪同步，不改业务代码。
- 需要检查的文件或区域：
  - `README.md`
  - `README.zh-CN.md`
  - `CHANGELOG.md`
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`
  - `docs/roadmap/ROADMAP.md`
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`

## 目标

- 主要目标：让用户可见文档和维护文档准确反映当前实现。
- 次要目标：把下一轮高优先级任务转成可被 Auto Top 5 Batch Sprint 继续执行的候选队列。
- 成功标准：
  - README 中不再把已完成能力写成未实现。
  - 架构和安全文档列出当前模块、API 边界和限制。
  - 任务总表、Sprint 队列、进度日志和本计划状态一致。

## 非目标

- 不实现 SQLite。
- 不实现 AI provider。
- 不实现加密备份 / 同步。
- 不实现代码签名。
- 不迁移事件总线。
- 不改业务代码或测试代码。

## 用户影响

- 用户能从 README 看到当前真实能力。
- 维护者能从 ROADMAP、TASKS、CURRENT_TOP10 和 PROGRESS 看到下一轮默认顺序。
- UI 和运行行为不变。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据：仅文档说明，不改变行为。
- 是否有数据离开本机：没有。
- 是否需要显式 opt-in：不涉及新行为；文档明确后续 AI provider、同步、备份必须显式 opt-in。
- 是否需要用户可见的确认或预览：不涉及。

## 范围

### 范围内

- 同步 README 和中文 README 的实现状态。
- 同步 CHANGELOG。
- 同步 architecture 和 security 当前边界。
- 同步 roadmap、task table、sprint queue、progress log。
- 新增 `GS-P0-012` 计划文件。
- 新增下一轮 P1 候选任务：
  - `GS-P1-013`
  - `GS-P1-014`
  - `GS-P1-015`
  - `GS-P1-016`
  - `GS-P1-017`

### 范围外

- `src/` 下任何业务代码。
- 测试代码。
- `最新prompt.md`。
- 新建下一轮 P1 候选任务的完整计划文件。

## 架构触点

- 涉及的运行时模块：仅在文档中描述。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：无。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：新增 `docs/plans/0030-docs-reality-sync.md`。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 要新增或修改的端点：无。
- 请求 / 响应结构：无。
- 错误行为：无。
- 兼容性说明：本任务只记录当前 API 边界和下一轮兼容迁移候选。

## 执行步骤

1. 创建计划并标记 `GS-P0-012` 进行中。
   预期结果：任务追踪有明确计划和状态。
   回滚路径：删除本计划并恢复任务表状态。
2. 同步 README、CHANGELOG、ARCHITECTURE、SECURITY、ROADMAP。
   预期结果：用户文档和维护文档不再滞后。
   回滚路径：按 git diff 逐文件回滚文档。
3. 同步 `TASKS.md`、`CURRENT_TOP10.md` 和 `PROGRESS.md`。
   预期结果：下一轮队列包含 `GS-P1-013` 到 `GS-P1-017`。
   回滚路径：恢复任务追踪文件。
4. 执行文档一致性、相关测试和 diff 检查。
   预期结果：验证命令通过或记录失败原因。
   回滚路径：修正文档后重新验证，或保留阻塞记录。

## 风险

- 技术风险：低，仅文档变更。
- 产品风险：文档误写已实现/未实现边界会误导用户。
- 隐私 / 安全风险：低，但安全文档必须准确描述 opt-in 和本地 API 边界。
- 发布风险：低。

## 验证

- 文档一致性检查：
  - `rg -n "规划中|not yet implemented|diagnostics|saved discovery|聚类|地图|Job / Event|SSE|SQLite|code signing" README.md README.zh-CN.md CHANGELOG.md docs`
- 事实验证测试：
  - `python -m pytest tests/test_runtime_http.py tests/test_runtime_api_boundary.py tests/test_runtime_diagnostics.py tests/test_runtime_jobs.py tests/test_discovery_clusters.py tests/test_release_manifest_script.py -q`
- 收尾检查：
  - `git diff --check`
  - `git status --short`
  - `git diff --stat`

## 发布与回滚

- 如何增量发布：作为纯文档 commit 发布。
- 是否需要开关或受控状态：不需要。
- 如果失败，用户如何恢复：回滚文档 commit。

## 文档更新

- 需要更新的文档：
  - `README.md`
  - `README.zh-CN.md`
  - `CHANGELOG.md`
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`
  - `docs/roadmap/ROADMAP.md`
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
- 需要更新的用户可见文案：README 中的已实现和规划中。
- 需要更新的内部维护说明：任务队列、路线图和安全 / 架构边界。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成文档现实同步和下一轮队列计划，验证通过。 |
| `2026-04-24` | `[~]` | 已创建计划，开始文档现实同步。 |

## 验证记录

- 已运行测试：
  - `rg -n "规划中|not yet implemented|diagnostics|saved discovery|聚类|地图|Job / Event|SSE|SQLite|code signing" README.md README.zh-CN.md CHANGELOG.md docs`
  - `python -m pytest tests/test_runtime_http.py tests/test_runtime_api_boundary.py tests/test_runtime_diagnostics.py tests/test_runtime_jobs.py tests/test_discovery_clusters.py tests/test_release_manifest_script.py -q`，52 passed，4 subtests passed。
  - `git diff --check`，通过；仅有 Git LF/CRLF 换行提示。
- 手动验证：README 中已实现能力不再被写成未实现；规划中只保留 SQLite、Job/Event/SSE 接入、Update Inbox 增强、AI provider opt-in、备份和代码签名等剩余项。
- 尚未覆盖的缺口：未运行全量测试；本轮未改业务代码。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
