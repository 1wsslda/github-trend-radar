# Job / Event 模型 MVP 计划

## 任务元信息

- 任务 ID：`GS-P1-004`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：3
- 推荐 commit message：`feat: add local job event model`

## 标题

统一 Job / Event 模型

## 摘要

- 这个任务建立一个小型本地内存 Job/Event 契约，用于后续发现、刷新、诊断、AI 等长任务共享进度格式。
- 现在做是因为现有 discovery job 已有独立模型，SSE 和更多后台任务需要共同事件边界。
- 做完后运行时会有可复用的 job snapshot 和 event history API，但不会一次迁移所有后台任务。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：关键词发现有独立 `discovery_jobs.py`，手动刷新只有 status JSON。
- 当前技术形态：线程 + 内存状态 + 轮询接口。
- 已知痛点：事件格式不统一，后续 SSE 无统一来源。
- 现有约束：不替换现有 discovery job，不引入外部队列。
- 需要检查的文件或区域：`runtime/discovery_jobs.py`、`runtime/http.py`、`runtime/app.py`。

## 目标

- 主要目标：新增本地 `runtime/jobs.py`，定义 job 和 event 的规范化、创建、更新、查询。
- 次要目标：提供 `/api/jobs` 和 `/api/events` 的只读入口。
- 成功标准：测试能创建 runtime、记录事件、按 job 查询和导出近期事件。

## 非目标

- 不把所有现有后台任务一次迁移到新模型。
- 不引入持久化队列。
- 不引入 WebSocket。

## 隐私与显式同意

- 本任务不外发数据。
- 事件 payload 只保存非敏感元数据，不保存 Token 或代理明文。
- 控制类读取仍限 loopback/control-token。

## 范围

### 范围内

- 新增本地内存 Job/Event runtime。
- 新增只读 HTTP 端点。
- Discovery job 可继续保持原状，后续逐步桥接。

### 范围外

- 持久化任务历史。
- 取消/重试/调度队列。
- SSE 传输层，放到 `GS-P1-005`。

## 架构触点

- 运行时模块：新增 `runtime/jobs.py`，修改 `runtime/http.py`、`runtime/app.py`
- HTTP / API 变更：新增 `/api/jobs`、`/api/events`
- 状态 / 持久化变更：无
- UI 变更：无
- 后台任务变更：新增通用模型，不替换旧任务

## 执行步骤

1. 写 `tests/test_runtime_jobs.py` 覆盖创建、更新、事件记录和裁剪。
   预期结果：测试先失败，模块不存在。
   回滚路径：删除测试。
2. 新增 `runtime/jobs.py`。
   预期结果：job/event runtime 单元测试通过。
   回滚路径：删除模块。
3. 在 HTTP 层注入 runtime 并新增查询端点。
   预期结果：HTTP 测试通过。
   回滚路径：移除注入和路由。

## 风险

- 技术风险：与 discovery job 双模型并存。MVP 明确只作为新通用契约。
- 产品风险：用户暂时看不到 UI 变化。该任务解锁 SSE。
- 隐私 / 安全风险：事件 payload 需要保持脱敏。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_jobs.py tests/test_runtime_http.py -q`
- 集成测试：`python -m pytest -q`
- 手动检查：确认事件接口不返回敏感设置。

## 发布与回滚

- 增量发布：新增 runtime 和端点，不影响现有任务。
- 回滚：移除 `runtime/jobs.py` 和 HTTP 注入。

## 文档更新

- 更新 `TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成内存级 Job/Event runtime 和只读 HTTP 查询端点。 |
| `2026-04-24` | `[~]` | 开始 Job / Event 模型 MVP，先写失败测试。 |
| `2026-04-24` | `[ ]` | Auto Top 5 Batch Sprint 选中，等待执行。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_jobs.py tests/test_runtime_http.py tests/test_runtime_app.py -q`，42 passed，4 subtests passed；本批最终 `python -m pytest -q`，173 passed，145 subtests passed。
- 手动验证：确认 `/api/jobs` 与 `/api/events` 仍要求 loopback/control token。
- 尚未覆盖的缺口：现有 discovery job 的深度迁移后续单独做。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
