# GS-P1-016 SQLite 迁移第一阶段

## 任务元信息

- 任务 ID：`GS-P1-016`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`4`
- 推荐 commit message：`feat(storage): add sqlite migration dry-run skeleton`

## 标题

SQLite 迁移第一阶段：JSON 兼容与回滚骨架

## 摘要

- 现有设计 `docs/plans/0012-sqlite-migration-design.md` 已明确未来从 JSON 状态迁移到 SQLite 的方向。
- 本任务只实现第一阶段安全骨架：SQLite schema、dry-run 计数校验和备份 / 回滚路径规划。
- 完成后，后续迁移可以先在内存或测试环境验证表结构和 JSON 字段覆盖，不会默认切换事实存储。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`
- 前置设计：`docs/plans/0012-sqlite-migration-design.md`

## 当前状态

- 当前行为：运行时继续使用 `user_state.json`、`discovery_state.json`、`data/latest.json` 和缓存 JSON 文件。
- 当前技术形态：本地 JSON 文件 + 内存字典 + 原子写入。
- 已知痛点：后续数据增长后，更新事件、保存视图、AI artifact 和搜索会需要更稳的结构化存储。
- 现有约束：不能在本任务中创建真实用户数据库、不能默认读取 SQLite、不能删除或改写现有 JSON。
- 需要检查的文件或区域：
  - `docs/plans/0012-sqlite-migration-design.md`
  - `src/gitsonar/runtime/state_schema.py`
  - `src/gitsonar/runtime/state_store.py`
  - `docs/SECURITY.md`

## 目标

- 主要目标：新增可测试的 SQLite schema 与 dry-run 迁移统计。
- 次要目标：提供备份、临时库、最终库和 rollback export 的路径规划，方便后续实施原子切换和回滚。
- 成功标准：测试能在内存 SQLite 上创建 schema，dry-run 能覆盖用户状态、发现状态和最新快照的关键计数，并明确敏感设置不入库。

## 非目标

- 不启用 SQLite 读取。
- 不写入 `gitsonar.db` 或 `gitsonar.db.tmp`。
- 不迁移真实用户数据。
- 不新增 UI 设置开关。
- 不删除或停用 JSON 导入 / 导出。

## 用户影响

- 用户可见行为：无直接 UI 变化。
- 数据风险：无真实数据迁移；本阶段只提供测试用骨架。
- 保持不变：JSON 仍是事实存储，导入 / 导出继续可用。

## 隐私与显式同意

- 不涉及数据外发。
- 不涉及 AI、云 API、同步或 Token 边界变更。
- `github_token`、代理配置等敏感设置不会进入迁移 dry-run 的 settings payload。

## 范围

### 范围内

- 新增 SQLite schema helper。
- 新增 dry-run 迁移计划 / 计数 helper。
- 新增备份与回滚路径规划 helper。
- 新增 focused 测试。
- 同步任务、Sprint、进度和路线图文档。

### 范围外

- 启动时自动迁移。
- SQLite -> JSON 导出实现。
- 真实文件备份。
- 数据库读写 facade。
- FTS / 搜索索引。

## 架构触点

- 运行时模块：新增 `src/gitsonar/runtime/sqlite_migration.py`
- HTTP / API 变更：无。
- 状态 / 持久化变更：无默认行为变更；仅新增迁移骨架代码。
- UI 变更：无。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无用户状态新字段。
- 新文件或新表：新增 SQLite schema 常量，包含设计中的第一阶段表。
- 迁移需求：本任务不执行迁移。
- 导入 / 导出影响：保持 JSON 导入 / 导出事实格式；dry-run 只读取传入的 dict。

## API 与契约

- 新增 Python helper：
  - `create_sqlite_schema(connection)`
  - `sqlite_migration_file_plan(base_dir, timestamp)`
  - `dry_run_sqlite_migration(user_state, discovery_state, latest_snapshot, settings=None)`
- 请求 / 响应结构：无 HTTP API 变化。
- 错误行为：helper 对非 dict 输入保守按空状态处理。
- 兼容性说明：运行时未接入这些 helper，因此不会影响现有启动和 JSON 状态读写。

## 执行步骤

1. 写失败测试。
   预期结果：当前缺少 `runtime.sqlite_migration` 模块，测试失败。
   回滚路径：删除新增测试。
2. 新增 SQLite migration helper。
   预期结果：测试可在内存 SQLite 创建第一阶段表，并能 dry-run 统计 JSON 状态。
   回滚路径：删除新增模块。
3. 同步文档和任务状态。
   预期结果：计划、任务表、Sprint 队列、进度日志和路线图反映第一阶段完成。
   回滚路径：恢复文档到 `[ ]` 并保留失败说明。

## 风险

- 技术风险：schema 过早固化。缓解方式：只作为阶段 1 helper，不接入运行时读取路径。
- 产品风险：用户误以为已经启用 SQLite。缓解方式：文档明确“未默认切换事实存储”。
- 隐私 / 安全风险：敏感设置不得进入 dry-run settings payload。
- 发布风险：低；新增代码无运行时调用入口。

## 验证

- 单元测试：
  - `python -m pytest tests/test_sqlite_migration.py -q`
- 回归测试：
  - `python -m pytest tests/test_runtime_state.py tests/test_runtime_api_boundary.py tests/test_sqlite_migration.py -q`
- 静态检查：
  - `git diff --check`
- 手动检查：
  - 确认应用启动逻辑未 import 或调用 `sqlite_migration.py`。
  - 确认工作区没有生成 `gitsonar.db`、`gitsonar.db.tmp` 或备份目录。

## 发布与回滚

- 发布方式：作为未接入运行时的迁移骨架随代码发布。
- 是否需要开关：不需要；没有运行时入口。
- 如果失败：撤回本 commit，JSON 状态读写不受影响。

## 文档更新

- 需要更新的文档：
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
  - `docs/roadmap/ROADMAP.md`
  - `docs/ARCHITECTURE.md`
  - `CHANGELOG.md`
- 用户可见文案：README 规划项可说明 SQLite 第一阶段骨架已完成。
- 内部维护说明：本计划文件。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成 SQLite schema helper、dry-run 计数、敏感设置排除和回滚路径规划。 |
| `2026-04-24` | `[~]` | 已创建计划；准备写迁移骨架测试。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_sqlite_migration.py -q`，`3 passed, 10 subtests passed`
  - `python -m pytest tests/test_runtime_state.py tests/test_runtime_api_boundary.py tests/test_sqlite_migration.py tests/test_import_side_effects.py -q`，`22 passed, 10 subtests passed`
- 手动验证：待用户按下方步骤执行。
  - 全局搜索 `sqlite_migration`，确认只在测试和文档中直接使用，启动路径没有调用。
  - 检查工作区和运行目录，确认没有生成 `gitsonar.db`、`gitsonar.db.tmp` 或备份目录。
  - 继续使用现有 JSON 导入 / 导出入口，预期行为不变。
- 尚未覆盖的缺口：真实 SQLite 读写切换、SQLite -> JSON 导出和启动迁移将在后续任务处理。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
