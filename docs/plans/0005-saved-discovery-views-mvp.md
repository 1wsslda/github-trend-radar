# 0005 - 保存发现视图 MVP

## 任务元信息

- 任务 ID：`GS-P0-005`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 排名：`5`
- 推荐 commit message：`feat: 添加保存发现视图 MVP`

## 摘要

- 问题：当前发现流程偏一次性，用户难以保存搜索语境并持续复用。
- 为什么现在做：这是把“发现”升级为长期工作流的关键基础。
- 结果：用户可以保存 query、filter、排序方式等发现视图，并重新运行。

## 战略映射

- 战略：延续当前发现引擎，只补本地持久化和复用能力，不引入新调度系统。
- 路线图：对应 `docs/roadmap/ROADMAP.md` 的 P0 发现工作流闭环任务。
- Sprint：对应 `docs/sprints/CURRENT_TOP10.md` 排名 `5`。

## 当前状态

- 已在发现状态中新增 `saved_views`，保存视图名、查询参数、排序配置、最近运行时间和结果数。
- 已新增 `/api/discovery/views` 与 `/api/discovery/views/delete`。
- 发现页可保存当前视图、载入配置、重跑视图和删除视图。
- 每次发现任务完成后，会回写对应保存视图的 `last_run_at` 与 `last_result_count`。

## 目标

- 保存发现视图配置。
- 支持重新运行和查看最近结果。
- 保持本地优先与 JSON 兼容。

## 非目标

- 不做云同步视图。
- 不做复杂自动调度。
- 不重写发现引擎。

## 范围

### 范围内

- 视图保存
- 视图列表
- 视图重跑

### 范围外

- 跨设备同步
- AI 自动扩展视图
- 新持久化引擎

## 架构触点

- 状态：`runtime/state.py`
- 作业：`runtime/discovery_jobs.py`
- GitHub 发现：`runtime_github/discovery.py`
- UI：`runtime_ui/js/discovery.py`

## 发布与回滚

- 发布方式：默认启用，仅写入本地发现状态 JSON。
- 回滚方式：移除 `saved_views` 字段读写和相关 API / UI 入口；旧发现结果仍可继续使用。
- 恢复路径：若视图结构后续需要调整，可先兼容旧字段，再增量替换，不需要大迁移。

## 验证

- 手动检查：
  - 保存视图
  - 重跑视图
  - 重启后仍可读取
  - 旧 JSON 数据不损坏

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-23` | `[~]` | 开始扩展发现状态、保存视图接口和发现页工具条。 |
| `2026-04-23` | `[x]` | 完成保存发现视图 MVP，实现、测试和文档已同步。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`
- 手动验证：代码检查确认视图保存、载入、删除和运行结果统计都走本地状态闭环。
- 尚未覆盖的缺口：未做真实浏览器内多次保存 / 删除交互手测。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
