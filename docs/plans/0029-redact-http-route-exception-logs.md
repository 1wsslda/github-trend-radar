# GS-P1-012 Redact HTTP Route Exception Logs

## 任务元信息

- 任务 ID：`GS-P1-012`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：Project Autopilot Safe Loop / Security hardening
- 推荐 commit message：`fix(security): redact http route exception logs`
- Commit / PR：`fix(security): redact http route exception logs`

## 标题

`HTTP 路由异常日志脱敏`

## 摘要

- 这个任务要解决什么问题？本地 HTTP 路由捕获未预期异常时使用 `logger.exception(...)`，真实日志处理器可能把原始异常 traceback 写入日志。
- 为什么现在做？上一批已保护用户可见错误，本任务补齐同一路由层的日志侧敏感信息边界。
- 做完后用户能看到什么结果？UI/API 行为不变；日志中不再记录原始异常 traceback 中的明文 Token、代理凭据或本地路径。

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

- 当前行为：`exception_to_error()` 对非 `LocalAPIError` 调用 `logger.exception("http_route_failed ...")`。
- 当前技术形态：`runtime/http.py` 是本地 HTTP API 层，路由错误响应已支持安全用户文案。
- 已知痛点：异常对象可能包含 GitHub Token、代理 URL 或本地路径；`exc_info` 格式化后会泄露原文。
- 现有约束：不能改变 API 响应契约；不能把栈信息暴露给用户；不能扩大到仓库级日志重构。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime/http.py`
  - `tests/test_runtime_http.py`
  - `docs/SECURITY.md`

## 目标

- 主要目标：HTTP 路由未预期异常日志只记录脱敏后的异常摘要，不附带原始 `exc_info`。
- 次要目标：`LocalAPIError` 的拒绝日志也复用脱敏文本。
- 成功标准：测试确认日志不包含明文 secret、代理凭据或本地路径，响应仍保持原安全错误。

## 非目标

- 不做仓库级所有 logger 调用重构。
- 不改变 HTTP 路由权限模型。
- 不改变用户可见错误文案。
- 不新增日志系统或结构化日志依赖。

## 用户影响

- 谁会受益？使用 Token、代理或本地诊断能力的用户。
- UI 或工作流会发生什么变化？无正常路径 UI 变化。
- 哪些行为保持不变？HTTP 状态码、错误 code、control-token 和 loopback 保护保持不变。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据？涉及 Token / 代理 / 本地路径的日志脱敏。
- 是否有数据离开本机？没有。
- 是否需要显式 opt-in？不需要，属于默认安全边界。
- 是否需要用户可见的确认或预览？不需要。

## 范围

### 范围内

- 新增 HTTP 路由异常日志脱敏测试。
- `runtime/http.py` 引入 `redact_text`。
- 非预期异常日志改为 `logger.error(... error=<redacted>)`，不传 `exc_info`。
- `LocalAPIError` 拒绝日志使用脱敏后的错误摘要。
- 更新任务追踪和安全文档。

### 范围外

- 不改 `runtime_github` 其他日志。
- 不移除现有安全响应文案。
- 不新增日志文件或日志配置。

## 架构触点

- 涉及的运行时模块：`runtime/http.py`
- HTTP / API 变更：无响应契约变更
- 状态 / 持久化变更：无
- UI 变更：无
- 后台任务变更：无
- 打包 / 启动 / 壳层变更：无

## 数据模型

- 新字段：无
- 新文件或新表：无
- 迁移需求：无
- 导入 / 导出影响：无

## API 与契约

- 要新增或修改的端点：无
- 请求 / 响应结构：无
- 错误行为：用户响应继续使用 route 的 `error_message` / `error_code`。
- 兼容性说明：只改变日志内容，不改变 HTTP 合约。

## 执行步骤

1. 第一步：新增失败测试，让 `/api/sync-stars` 抛出带 secret 的未预期异常，并断言日志没有 `exc_info` 且包含脱敏标记。
   预期结果：当前实现仍用 `logger.exception`，测试失败。
   回滚路径：删除新增测试。
2. 第二步：修改 `exception_to_error()`，日志使用 `redact_text(exc)` 且不附加原 traceback。
   预期结果：聚焦测试通过，已有错误响应测试不变。
   回滚路径：恢复 `logger.exception` 调用。
3. 第三步：更新任务追踪、安全文档和验证记录。
   预期结果：`TASKS.md`、`CURRENT_TOP10.md`、`PROGRESS.md` 与本计划一致。
   回滚路径：撤销文档修改。

## 风险

- 技术风险：低；调试日志少了原始 traceback，但保留 route path、code 和脱敏错误摘要。
- 产品风险：无用户可见正常路径变化。
- 隐私 / 安全风险：降低本地日志泄露敏感信息风险。
- 发布风险：无数据迁移。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_unexpected_route_exception_log_redacts_sensitive_details -q`
- 集成测试：`python -m pytest tests/test_runtime_http.py -q`
- 手动检查：触发 GitHub Stars 同步异常，确认 UI 使用安全错误文案，日志不含明文 secret。
- 性能或可靠性检查：无额外 I/O。
- 需要关注的日志 / 诊断信号：`http_route_failed path=... code=... error=...` 中只应出现脱敏摘要。

## 发布与回滚

- 如何增量发布？随下一版安全加固发布。
- 是否需要开关或受控状态？不需要。
- 如果失败，用户如何恢复？回滚 `runtime/http.py` 和测试。

## 文档更新

- 需要更新的文档：
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
  - `docs/SECURITY.md`
- 需要更新的用户可见文案：无
- 需要更新的内部维护说明：本计划验证记录

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[~]` | 已创建计划，准备按 TDD 添加 HTTP 路由日志脱敏测试。 |
| `2026-04-24` | `[x]` | 已完成 HTTP 路由未预期异常日志脱敏，并验证 API 安全错误响应保持不变。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_unexpected_route_exception_log_redacts_sensitive_details -q`，失败原因是日志 traceback 含原始 `ghp_secret_token`、代理凭据和本地路径。
  - GREEN：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_unexpected_route_exception_log_redacts_sensitive_details -q`，1 passed。
  - Focused：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_sync_stars_unexpected_failure_is_sanitized tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_repo_details_internal_value_error_is_sanitized -q`，2 passed。
  - Regression：`python -m pytest tests/test_runtime_http.py -q`，42 passed，4 subtests passed。
- 手动验证：触发 GitHub Stars 同步异常，确认 UI 使用“GitHub 星标同步失败，请检查 Token 和网络后重试。”，日志 `http_route_failed` 只含脱敏摘要。
- 尚未覆盖的缺口：仓库级其他 logger 调用未在本任务内重构。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
