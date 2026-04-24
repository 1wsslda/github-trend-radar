# 只读 API control-token 收紧评估与兼容迁移

## 任务元信息

- 任务 ID：`GS-P1-013`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`1`
- 推荐 commit message：`fix(security): require control token for read APIs`

## 标题

`只读 API control-token 收紧评估与兼容迁移`

## 摘要

- 这个任务要解决只读本地 API 仍可在缺少 runtime control token 时读取脱敏 payload 的边界不一致问题。
- 现在做是因为状态变更、诊断、导出、事件等端点已经要求 control token，而 `bootstrap/repos/updates/settings/status/discovery` 等只读端点仍处于兼容开放状态。
- 做完后，当前前端加载路径继续工作；无 token 的直接 API 请求会得到 `403 invalid_control_token`，降低本机跨进程或误暴露端口时的数据读取面。

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

- 任务开始前行为：
  - `GET /api/ai-artifacts`、`/api/jobs`、`/api/events`、`/api/events/stream`、`/api/repo-details`、`/api/diagnostics`、`/api/export` 已要求 loopback + control token。
- 任务开始前，`GET /api/bootstrap`、`/api/repos`、`/api/updates`、`/api/discovery/views`、`/api/settings`、`/api/status`、`/api/discovery`、`/api/discovery/job` 仍未强制 control token。
- 当前技术形态：
  - 前端 `requestJson()` 已通过 `localApiOptions()` 对所有 fetch 自动加 `X-GitSonar-Control`。
  - 初始 HTML payload 已包含 `controlToken`。
- 已知痛点：
  - 安全文档已把这些端点列为下一步收紧对象。
  - 端点保护策略不一致，增加维护者误判风险。
- 现有约束：
  - 不改变 JSON payload schema。
  - 不改变当前前端入口。
  - 不引入账号、云 API 或新认证系统。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime/http.py`
  - `src/gitsonar/runtime_ui/js/helpers.py`
  - `src/gitsonar/runtime_ui/template.py`
  - `tests/test_runtime_http.py`
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`

## 目标

- 主要目标：把剩余只读本地 API 统一收紧为 loopback + runtime control token。
- 次要目标：用测试确认当前前端兼容路径仍能携带 control token 调用这些端点。
- 成功标准：
  - 无 token 请求访问受影响只读 API 返回 `403 invalid_control_token`。
  - 带正确 token 请求继续返回原 payload。
  - 前端统一请求 helper 仍会为所有本地 API 请求附加 token。
  - 文档中的 API 边界与实现一致。

## 非目标

- 不修改 runtime control token 生成、保存或轮换策略。
- 不引入登录、用户账号、OAuth 或跨设备认证。
- 不改变 GitHub Token 存储和 DPAPI 格式。
- 不改变 API 响应字段。
- 不改变绑定地址或 CORS 行为。

## 用户影响

- 正常打开 GitSonar UI 的用户不需要额外操作。
- 直接用浏览器地址栏访问这些 JSON API 时，如果没有携带 `X-GitSonar-Control`，会看到 `403`。
- 依赖本地 API 的脚本需要从 runtime state 或当前 UI 上下文取得 control token 后再请求。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据：涉及 runtime control token 边界，不涉及 GitHub Token 外发。
- 是否有数据离开本机：没有。
- 是否需要显式 opt-in：不需要；这是本地 API 读边界收紧。
- 是否需要用户可见的确认或预览：不需要；正常 UI 行为保持不变。

## 范围

### 范围内

- 保护以下只读端点：
  - `GET /api/bootstrap`
  - `GET /api/repos`
  - `GET /api/updates`
  - `GET /api/discovery/views`
  - `GET /api/settings`
  - `GET /api/status`
  - `GET /api/discovery`
  - `GET /api/discovery/job`
- 更新 HTTP 回归测试。
- 更新 UI JS 合约测试，锁定 `requestJson()` 继续通过 `localApiOptions()` 携带 token。
- 更新架构、安全、任务、Sprint 和进度文档。

### 范围外

- 不保护静态 HTML、CSS、JS 资源。
- 不新增跨进程 API token 发现端点。
- 不变更 POST 端点。
- 不变更 `/api/repo-details` 等已保护端点。

## 架构触点

- 涉及的运行时模块：`src/gitsonar/runtime/http.py`
- HTTP / API 变更：剩余只读 JSON API 改为 loopback + control-token 保护。
- 状态 / 持久化变更：无。
- UI 变更：无可见 UI 变化；仅验证现有 fetch helper。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 要新增或修改的端点：
  - 修改上述只读端点的访问前置条件。
- 请求 / 响应结构：
  - 带正确 `X-GitSonar-Control`：响应结构不变。
  - 缺少或错误 token：返回 `{"ok": false, "code": "invalid_control_token", "error": "缺少控制令牌或控制令牌无效。"}`，HTTP `403`。
- 错误行为：
  - loopback 检查仍先于 token 检查。
- 兼容性说明：
  - 当前 UI 已统一携带 token，因此不破坏主界面读取。
  - 旧的无 token 直接 API 调用需要迁移。

## 执行步骤

1. 写失败测试，断言剩余只读 API 缺少 control token 会被拒绝。
   预期结果：测试失败，当前返回 `200`。
   回滚路径：删除新增测试。
2. 写失败测试，断言状态 API 带 token 仍返回脱敏 payload。
   预期结果：测试仍通过或只需随路由收紧一起通过。
   回滚路径：恢复旧测试。
3. 写失败测试，锁定前端 `requestJson()` 继续调用 `localApiOptions()`。
   预期结果：如果 helper 被破坏，测试失败。
   回滚路径：删除新增合约断言。
4. 修改 `src/gitsonar/runtime/http.py` 的 GET 路由配置。
   预期结果：受影响只读 API 要求 loopback + control token。
   回滚路径：恢复对应路由的 `loopback_only/control_only` 标记。
5. 运行 focused tests 与 diff 检查。
   预期结果：测试通过，文档状态一致。
   回滚路径：按本计划回滚代码和文档。

## 风险

- 技术风险：低，路由保护机制已存在。
- 产品风险：依赖无 token 直接读取 JSON API 的个人脚本需要迁移。
- 隐私 / 安全风险：降低只读数据暴露面；不新增外发。
- 发布风险：低。

## 验证

- 单元测试：
  - `python -m pytest tests/test_runtime_http.py::RuntimeHTTPServerTests::test_read_api_routes_require_control_token -q`
  - `python -m pytest tests/test_runtime_http.py::RuntimeHTTPServerTests::test_get_status_redacts_legacy_sensitive_error -q`
  - `python -m pytest tests/test_runtime_ui_js_contract.py::RuntimeUIJSContractTests::test_request_json_sends_control_token_through_shared_options -q`
- 集成测试：
  - `python -m pytest tests/test_runtime_http.py tests/test_runtime_ui_js_contract.py tests/test_runtime_ui_assets.py -q`
- 手动检查：
  - 启动应用，确认首页数据加载、设置弹窗、发现页恢复状态和更新页读取正常。
  - 使用无 `X-GitSonar-Control` 的直接请求访问 `/api/status`，预期 `403 invalid_control_token`。
  - 使用正确 header 访问 `/api/status`，预期返回当前状态 payload。
- 性能或可靠性检查：
  - 无额外后台任务或网络请求。
- 需要关注的日志 / 诊断信号：
  - 不应出现原始 Token、代理凭据、本地路径或 traceback。

## 发布与回滚

- 如何增量发布：作为安全兼容收紧 commit 发布。
- 是否需要开关或受控状态：不需要，前端已携带 token。
- 如果失败，用户如何恢复：回滚本 commit 即可恢复只读 API 的无 token 兼容行为。

## 文档更新

- 需要更新的文档：
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
- 需要更新的用户可见文案：无。
- 需要更新的内部维护说明：只读 API 边界说明。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[~]` | 已创建计划，开始只读 API control-token 收紧兼容迁移。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_read_api_routes_require_control_token -q`，按预期失败，8 个子用例从当前 `200` 暴露未收紧行为。
  - GREEN：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_read_api_routes_require_control_token -q`，1 passed，8 subtests passed。
  - GREEN：`python -m pytest tests/test_runtime_http.py::RuntimeHTTPHandlerTests::test_get_status_redacts_legacy_sensitive_error -q`，1 passed。
  - Contract：`python -m pytest tests/test_runtime_ui_js_contract.py::RuntimeUIJSContractTests::test_request_json_sends_control_token_through_shared_options -q`，1 passed，4 subtests passed。
  - Focused：`python -m pytest tests/test_runtime_http.py tests/test_runtime_ui_js_contract.py tests/test_runtime_ui_assets.py -q`，67 passed，167 subtests passed。
  - 文档一致性：已用 `rg` 检查未完成状态残留；只保留历史进度记录和本计划的“任务开始前”描述。
  - 收尾检查：`git diff --check` 通过，仅有 LF/CRLF 提示。
- 手动验证：
  - 未启动桌面 UI；已用 HTTP 回归测试覆盖带 token 与无 token 的本地 API 行为。
  - 用户可手动启动应用，确认首页、设置弹窗、发现页状态恢复和更新页读取正常。
- 尚未覆盖的缺口：未运行全量测试；未做真实浏览器手动点击验证。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
