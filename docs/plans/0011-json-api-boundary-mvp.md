# JSON API 边界 MVP 计划

## 任务元信息

- 任务 ID：`GS-P1-002`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：1
- 推荐 commit message：`feat: add local JSON API boundary endpoints`

## 标题

清理静态壳与 JSON API 边界

## 摘要

- 这个任务要把当前已有的运行时数据通过更清晰的只读 JSON API 暴露出来，为后续静态壳和局部渲染铺路。
- 现在做是因为 P0 工作流已经闭环，P1 的第一步应先稳定前后端契约，而不是直接重写前端。
- 做完后前端或调试工具能通过 `/api/bootstrap`、`/api/repos`、`/api/updates` 和 `/api/discovery/views` 获取结构化数据。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：HTML 首屏仍由 Python 生成，已有多个操作型 API，但缺少统一只读 bootstrap/repos/updates 入口。
- 当前技术形态：`runtime/http.py` 负责路由，`runtime/app.py` 注入运行时依赖，状态仍来自 JSON 文件和内存快照。
- 已知痛点：前端若要逐步静态化，需要稳定的数据读取契约。
- 现有约束：不改 React / FastAPI / SQLite，不把业务聚合逻辑塞进 `runtime/app.py`。
- 需要检查的文件或区域：`src/gitsonar/runtime/http.py`、`src/gitsonar/runtime/app.py`、`tests/test_runtime_http.py`。

## 目标

- 主要目标：增加只读 JSON API 边界。
- 次要目标：让端点复用现有状态导出函数，保持 loopback/control-token 边界清晰。
- 成功标准：测试覆盖新端点，返回结构包含设置摘要、状态计数、仓库列表、更新列表和保存发现视图。

## 非目标

- 不重写前端为静态 SPA。
- 不改变现有 `trending.html` 生成链路。
- 不引入 FastAPI、OpenAPI 或 SQLite。

## 隐私与显式同意

- 不涉及新的 AI、云 API、同步或 Token 外发。
- 数据不离开本机。
- 只读 API 仍保持本地服务边界；敏感设置继续通过 `sanitize_settings(False)` 脱敏。

## 范围

### 范围内

- 新增 `/api/bootstrap`、`/api/repos`、`/api/updates`、`/api/discovery/views`。
- 为 `make_app_handler(...)` 增加可选只读数据提供函数，保持旧签名兼容。
- 增加 HTTP 单元测试。

### 范围外

- 前端改为完全通过这些 API 渲染。
- API 分页、复杂过滤和写操作重命名。

## 架构触点

- 运行时模块：`runtime/http.py`、`runtime/app.py`
- HTTP / API 变更：新增只读 GET 端点
- 状态 / 持久化变更：无
- UI 变更：无
- 后台任务变更：无

## 执行步骤

1. 写 HTTP 测试覆盖 `/api/bootstrap`、`/api/repos`、`/api/updates`、`/api/discovery/views`。
   预期结果：测试先失败，提示端点不存在。
   回滚路径：删除新增测试。
2. 在 `runtime/http.py` 增加只读数据提供依赖和路由。
   预期结果：新端点返回稳定 JSON。
   回滚路径：移除新增依赖和 GET 路由。
3. 在 `runtime/app.py` 注入当前快照、用户状态和发现状态导出函数。
   预期结果：真实运行时端点可读取本地状态。
   回滚路径：删除注入参数，保留旧端点。

## 风险

- 技术风险：端点返回过多数据。MVP 先复用已有本地状态，不做跨网络请求。
- 产品风险：前端尚未消费这些端点。该任务只建立契约。
- 隐私 / 安全风险：敏感设置必须脱敏，写操作仍需 control token。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_http.py -q`
- 集成测试：`python -m pytest -q`
- 手动检查：确认新端点不返回明文 GitHub Token 或代理。

## 发布与回滚

- 增量发布：新增只读 API，不影响现有页面。
- 回滚：删除端点和注入参数即可恢复。

## 文档更新

- 更新 `TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已新增只读 JSON API 边界并完成相关测试。 |
| `2026-04-24` | `[~]` | Auto Top 5 Batch Sprint 选中，开始 JSON API 边界 MVP。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_api_boundary.py tests/test_runtime_http.py -q`，38 passed，4 subtests passed；本批最终 `python -m pytest -q`，173 passed，145 subtests passed。
- 手动验证：检查 `/api/bootstrap` 使用脱敏 settings，不返回明文 `github_token`。
- 尚未覆盖的缺口：前端尚未切换到 API-first 渲染，后续任务继续推进。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
