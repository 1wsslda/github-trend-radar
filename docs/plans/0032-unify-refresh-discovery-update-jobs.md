# 刷新 / 发现 / 更新检查接入统一 Job/Event/SSE

## 任务元信息

- 任务 ID：`GS-P1-014`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`2`
- 推荐 commit message：`feat(runtime): bridge refresh and discovery to job events`

## 标题

`刷新 / 发现 / 更新检查接入统一 Job/Event/SSE`

## 摘要

- 这个任务把已有刷新、关键词发现和收藏更新检查流程小步接入通用 `Job/Event` runtime，让 `/api/jobs`、`/api/events` 和 `/api/events/stream` 能看到这些后台活动。
- 现在做是因为通用 Job/Event/SSE MVP 已存在，但 refresh、discovery、update check 仍主要维护自己的状态。
- 做完后，现有 UI 行为不变；新增的通用事件可供后续 SSE 前端进度整合使用。

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

- 当前行为：
  - `runtime/jobs.py` 已提供内存级 `create_job`、`update_job`、`record_event`、`export_jobs`、`export_events`。
  - `runtime/discovery_jobs.py` 有自己的 discovery job 状态和 `/api/discovery/job` payload。
  - `refresh_once_safe()` 只写 status 文件，不创建通用 job。
  - 收藏更新检查发生在 `refresh_once_locked()` 内部，但没有通用事件。
- 当前技术形态：Python runtime + local HTTP API + embedded JS；SSE 端点当前输出通用事件历史快照。
- 已知痛点：`/api/jobs` 和 `/api/events` 无法反映最主要的后台流程，后续前端无法统一监听。
- 现有约束：
  - 不替换 discovery job 现有 API。
  - 不重写 refresh 线程模型。
  - 不引入队列系统、数据库或外部依赖。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime/app.py`
  - `src/gitsonar/runtime/discovery_jobs.py`
  - `src/gitsonar/runtime/jobs.py`
  - `tests/test_runtime_app.py`
  - `tests/test_discovery_jobs.py`

## 目标

- 主要目标：让 refresh、discovery、update check 在通用 Job/Event runtime 中留下可查询记录。
- 次要目标：保持现有 discovery job 和 status payload 兼容。
- 成功标准：
  - `refresh_once_safe()` 创建并完成/失败通用 `refresh` job。
  - refresh 内的收藏更新检查记录 `favorite_updates.checked` 事件。
  - discovery job 的 queued/running/completed/failed/cancelled 状态同步到通用 `discovery` job。
  - `/api/jobs` 和 `/api/events` 现有契约不变。

## 非目标

- 不把所有后台流程改成队列 worker。
- 不替换 `/api/discovery/job`。
- 不改变前端轮询逻辑。
- 不实现真正持续推送的 SSE 连接。
- 不改变刷新频率、GitHub API 请求策略或收藏更新算法。

## 用户影响

- 正常 UI 行为保持不变。
- 维护者和后续前端可以通过 `/api/jobs`、`/api/events`、`/api/events/stream` 观察刷新、发现和更新检查进度。
- 出错时通用 job message 仍使用用户安全摘要，不暴露原始异常。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据：仅记录本地 job/event 元数据，不新增外发。
- 是否有数据离开本机：没有。
- 是否需要显式 opt-in：不需要。
- 是否需要用户可见的确认或预览：不需要。

## 范围

### 范围内

- 给 `make_discovery_job_runtime()` 增加可选通用 event runtime 桥接。
- 给 refresh safe wrapper 增加通用 refresh job 生命周期。
- 在收藏更新检查后记录 `favorite_updates.checked` 事件。
- 更新 focused tests 和文档追踪。

### 范围外

- 不新增 UI。
- 不改变持久化。
- 不改变 GitHub 请求逻辑。
- 不改 discovery result schema。

## 架构触点

- 涉及的运行时模块：
  - `src/gitsonar/runtime/app.py`
  - `src/gitsonar/runtime/discovery_jobs.py`
  - `src/gitsonar/runtime/jobs.py`
- HTTP / API 变更：无新增端点；`/api/jobs` 和 `/api/events` 会包含更多 runtime 事件。
- 状态 / 持久化变更：无。
- UI 变更：无。
- 后台任务变更：仅新增本地 event bridge，不改变执行线程。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：
  - discovery 内部 job 可保存通用 `event_job_id`。
  - refresh 通用 job payload 可包含 `source` 和 `new_update_count`。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 要新增或修改的端点：无。
- 请求 / 响应结构：
  - `/api/jobs` 继续返回 `jobs` 列表，但会出现 `job_type=refresh` 和 `job_type=discovery`。
  - `/api/events` 继续返回 `events` 列表，但会出现 `favorite_updates.checked`。
- 错误行为：
  - refresh 失败时通用 job 标记 `failed`，message 使用安全摘要。
  - discovery 失败继续使用 `SAFE_DISCOVERY_ERROR`。
- 兼容性说明：
  - 现有 discovery job API 不变。

## 执行步骤

1. 写 discovery bridge 失败测试。
   预期结果：`make_discovery_job_runtime(..., event_runtime=...)` 当前不支持参数或不会产生通用事件。
   回滚路径：删除测试。
2. 写 refresh/update bridge 失败测试。
   预期结果：`refresh_once_safe()` 当前不会创建通用 `refresh` job，也不会记录 `favorite_updates.checked`。
   回滚路径：删除测试。
3. 实现 discovery 可选 bridge。
   预期结果：discovery 生命周期映射到通用 job/event runtime。
   回滚路径：移除 optional 参数和桥接调用。
4. 实现 refresh/update bridge。
   预期结果：refresh 生命周期与 update check 事件可通过通用 runtime 查询。
   回滚路径：移除 helper 和 `refresh_once_safe()` 传参。
5. 运行 focused tests 与 diff 检查。
   预期结果：测试通过，文档状态一致。
   回滚路径：按本计划回滚代码和文档。

## 风险

- 技术风险：中低，新增桥接不能影响原有 refresh/discovery 成功路径。
- 产品风险：低，无 UI 变化。
- 隐私 / 安全风险：低，event payload 不能包含 Token、代理凭据、原始异常或本地路径。
- 发布风险：低。

## 验证

- 单元测试：
  - `python -m pytest tests/test_discovery_jobs.py::DiscoveryJobRuntimeTests::test_discovery_job_mirrors_lifecycle_to_event_runtime -q`
  - `python -m pytest tests/test_runtime_app.py::RuntimeAppTests::test_refresh_once_safe_records_job_events_and_update_check -q`
- 集成测试：
  - `python -m pytest tests/test_discovery_jobs.py tests/test_runtime_app.py tests/test_runtime_jobs.py tests/test_runtime_http.py -q`
- 手动检查：
  - 启动应用后点击刷新，访问 `/api/jobs` 查看 `refresh` job。
  - 运行关键词发现，访问 `/api/jobs` 查看 `discovery` job。
  - 访问 `/api/events/stream`，确认存在 `job.created`、`job.updated`、`job.completed` 和 `favorite_updates.checked`。
- 性能或可靠性检查：
  - 桥接失败不能中断原后台任务。
- 需要关注的日志 / 诊断信号：
  - 不应出现原始 Token、代理凭据、本地路径或 traceback。

## 发布与回滚

- 如何增量发布：作为 runtime bridge commit 发布。
- 是否需要开关或受控状态：不需要；桥接仅记录内存事件。
- 如果失败，用户如何恢复：回滚本 commit，原 refresh/discovery 路径恢复到独立状态。

## 文档更新

- 需要更新的文档：
  - `docs/ARCHITECTURE.md`
  - `docs/roadmap/ROADMAP.md`
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
- 需要更新的用户可见文案：无。
- 需要更新的内部维护说明：Job/Event/SSE 接入现状。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[~]` | 已创建计划，开始 refresh/discovery/update check 通用 Job/Event bridge。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_discovery_jobs.py::DiscoveryJobRuntimeTests::test_discovery_job_mirrors_lifecycle_to_event_runtime -q`，按预期失败，`make_discovery_job_runtime()` 不接受 `event_runtime`。
  - RED：`python -m pytest tests/test_runtime_app.py::RuntimeAppTests::test_refresh_once_safe_records_job_events_and_update_check -q`，按预期失败，未创建通用 refresh job。
  - GREEN：上述两个 focused 测试分别通过。
  - Focused：`python -m pytest tests/test_discovery_jobs.py tests/test_runtime_app.py tests/test_runtime_jobs.py tests/test_runtime_http.py -q`，56 passed，12 subtests passed。
  - 文档一致性：已用 `rg` 检查未完成状态残留；只保留历史进度记录。
  - 收尾检查：`git diff --check` 通过，仅有 LF/CRLF 提示。
- 手动验证：
  - 未启动桌面 UI；已用 runtime 和 HTTP 回归测试覆盖通用 job/event bridge。
  - 用户可手动点击刷新、运行关键词发现，然后访问 `/api/jobs`、`/api/events` 或 `/api/events/stream` 查看 `refresh`、`discovery` 和 `favorite_updates.checked`。
- 尚未覆盖的缺口：未运行全量测试；前端仍未切换到 EventSource 驱动。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
