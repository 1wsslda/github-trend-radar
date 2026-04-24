# SSE 事件流 MVP 计划

## 任务元信息

- 任务 ID：`GS-P1-005`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：4
- 推荐 commit message：`feat: expose local SSE event stream`

## 标题

SSE 进度与事件流

## 摘要

- 这个任务在 Job/Event MVP 之上提供只读 SSE 事件流端点。
- 现在做是因为前端轮询 discovery job 已经可用，但后续统一任务进度需要推送边界。
- 做完后本地前端可通过 `/api/events/stream` 接收近期事件快照。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：前端通过轮询 `/api/discovery/job` 获取发现进度。
- 当前技术形态：`ThreadingHTTPServer` + JSON API。
- 已知痛点：事件推送边界不存在。
- 现有约束：必须依赖 `GS-P1-004` 的事件模型，不直接为单个任务写死 SSE。
- 需要检查的文件或区域：`runtime/http.py`、`runtime/jobs.py`、`tests/test_runtime_http.py`。

## 目标

- 主要目标：新增 `GET /api/events/stream`，输出 `text/event-stream; charset=utf-8`。
- 次要目标：保持 loopback 和 control-token 保护。
- 成功标准：HTTP 测试确认 content type、事件格式和权限边界。

## 非目标

- 不实现无限长实时连接和心跳循环。
- 不把前端轮询立即替换为 SSE。
- 不引入 WebSocket。

## 隐私与显式同意

- 不外发数据。
- SSE 仅在本地 loopback 上提供，并要求 control token。
- 事件内容来自本地脱敏事件模型。

## 范围

### 范围内

- 新增 SSE 响应 helper。
- 新增 `/api/events/stream`。
- 测试权限和格式。

### 范围外

- EventSource 前端消费。
- 长连接重连策略。
- 持久化事件流。

## 架构触点

- 运行时模块：`runtime/http.py`
- HTTP / API 变更：新增 SSE GET 端点
- 状态 / 持久化变更：无
- UI 变更：无
- 后台任务变更：无

## 执行步骤

1. 写 HTTP 测试覆盖 SSE endpoint。
   预期结果：测试先失败。
   回滚路径：删除测试。
2. 实现 SSE attachment / stream result。
   预期结果：端点返回标准事件流文本。
   回滚路径：移除 helper 和路由。
3. 验证全量测试。
   预期结果：现有 JSON API 不受影响。
   回滚路径：恢复 `runtime/http.py` 到任务前状态。

## 风险

- 技术风险：长连接容易阻塞测试。MVP 只输出近期事件快照，后续再做持久连接。
- 产品风险：前端暂未消费。该任务先建立传输契约。
- 隐私 / 安全风险：必须继续用 control token。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_http.py -q`
- 集成测试：`python -m pytest -q`
- 手动检查：确认 `Content-Type` 为 `text/event-stream; charset=utf-8`。

## 发布与回滚

- 增量发布：新增端点，不影响现有轮询。
- 回滚：删除端点即可。

## 文档更新

- 更新 `TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成 `/api/events/stream` SSE 快照端点和权限测试。 |
| `2026-04-24` | `[~]` | 开始 SSE 事件流 MVP，基于 Job/Event 事件历史输出快照。 |
| `2026-04-24` | `[ ]` | Auto Top 5 Batch Sprint 选中，等待 `GS-P1-004` 完成后执行。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_jobs.py -q`，40 passed，4 subtests passed；本批最终 `python -m pytest -q`，173 passed，145 subtests passed。
- 手动验证：确认 `/api/events/stream` 返回 `text/event-stream; charset=utf-8`，且缺少 control token 时返回 403。
- 尚未覆盖的缺口：真正前端 EventSource 消费留给后续任务。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
