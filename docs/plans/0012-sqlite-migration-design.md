# SQLite 迁移设计计划

## 任务元信息

- 任务 ID：`GS-P1-003`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：2
- 推荐 commit message：`docs: design sqlite migration path`

## 标题

SQLite 迁移设计

## 摘要

- 这个任务只定义从 JSON 状态到 SQLite 的迁移、导入导出和回滚方案。
- 现在做是因为状态模型已经包含标签、笔记、发现视图、更新收件箱和 AI Insight，本地 JSON 将逐步变重。
- 做完后仓库会有可执行前置设计，后续才能安全实施迁移。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：运行态使用 `user_state.json`、`discovery_state.json`、`repo_details_cache.json` 和 `data/latest.json`。
- 当前技术形态：本地 JSON 文件 + 内存字典 + 原子写入。
- 已知痛点：长期数据增长后，更新事件、搜索、AI artifact 和导出边界会变难维护。
- 现有约束：本任务不切换存储，不破坏 JSON 导入 / 导出。
- 需要检查的文件或区域：`runtime/state.py`、`runtime/state_store.py`、`runtime/state_schema.py`、`docs/SECURITY.md`。

## 目标

- 主要目标：写清 SQLite 目标表、迁移顺序、备份和回滚策略。
- 次要目标：明确仍保留 JSON 导入 / 导出作为用户可携带数据格式。
- 成功标准：计划包含表映射、迁移步骤、验证步骤和失败恢复路径。

## 非目标

- 不创建数据库文件。
- 不改运行时代码。
- 不废弃 JSON 状态文件。

## 隐私与显式同意

- 不涉及数据外发。
- 不涉及 AI provider、云同步或 Token 边界变更。
- 设计必须保留本地优先和可导出。

## 范围

### 范围内

- 定义表结构草案。
- 定义 JSON 到 SQLite 的导入顺序。
- 定义备份、校验、回滚和导出策略。

### 范围外

- 实施 SQLite runtime。
- 写迁移脚本。
- 改 UI 或 API。

## 架构触点

- 运行时模块：未来可能新增 `runtime_storage/` 或 `runtime/storage_sqlite.py`
- HTTP / API 变更：无
- 状态 / 持久化变更：仅设计
- UI 变更：无
- 后台任务变更：无

## 当前 JSON 状态清单

当前迁移设计必须覆盖这些本地文件，但实施阶段不得一次删除旧文件：

| 文件 | 当前职责 | 迁移策略 |
|---|---|---|
| `user_state.json` | 四态列表、仓库记录、标签/笔记、收藏 watch、更新收件箱、反馈信号、AI Insight | 第一阶段导入核心用户数据，保留 JSON 导出 |
| `discovery_state.json` | remembered query、last query/results、扩词结果、保存发现视图 | 第一阶段导入保存视图和最近发现结果 |
| `data/latest.json` | 当前 Trending / API 快照 | 作为 `repos` / `repo_snapshots` 的导入来源 |
| `repo_details_cache.json` | README、release、topics 等详情缓存 | 第二阶段再迁入或保留为缓存文件 |
| `settings.json` | 设置、DPAPI 加密 Token / 代理 | 不迁入明文 Token；可迁移非敏感设置或继续留在 settings |

## 目标表结构草案

第一阶段只实现能替代现有 JSON 状态的最小表：

| 表 | 关键字段 | 来源 |
|---|---|---|
| `repos` | `id`, `url`, `owner`, `name`, `full_name`, `description`, `language`, `topics_json`, `last_seen_at` | `repo_records`, `latest.json`, `last_results` |
| `repo_snapshots` | `id`, `repo_id`, `stars`, `forks`, `gained`, `rank`, `source_key`, `captured_at`, `raw_json` | `latest.json`, `repo_records` |
| `user_repo_state` | `repo_id`, `state`, `created_at`, `updated_at` | `favorites`, `watch_later`, `read`, `ignored` |
| `repo_annotations` | `repo_id`, `tags_json`, `note`, `updated_at` | `repo_annotations` |
| `favorite_watch` | `repo_id`, `stars`, `forks`, `latest_release_tag`, `checked_at`, `release_checked_at` | `favorite_watch` |
| `update_events` | `id`, `repo_id`, `changes_json`, `priority_score`, `read_at`, `dismissed_at`, `pinned`, `checked_at` | `favorite_updates` |
| `feedback_signals` | `repo_id`, `reason`, `count`, `state`, `updated_at` | `feedback_signals` |
| `discovery_views` | `id`, `name`, `query`, `limit`, `auto_expand`, `ranking_profile`, `last_run_at`, `last_result_count` | `saved_views` |
| `discovery_runs` | `id`, `query_json`, `run_at`, `result_count`, `warnings_json` | `last_query`, `last_run_at`, `last_warnings` |
| `discovery_results` | `run_id`, `repo_id`, `rank`, `score_json`, `raw_json` | `last_results` |
| `ai_artifacts` | `id`, `repo_id`, `artifact_type`, `schema_version`, `provider`, `model`, `input_hash`, `output_json`, `created_at`, `updated_at` | `ai_insights` |
| `settings_kv` | `key`, `value_json`, `updated_at` | 仅非敏感设置，Token / proxy 仍由 DPAPI 设置层处理 |

第二阶段可追加：

- `repo_details_cache`：替代详情缓存文件。
- `search_index` / FTS5：为描述、README、笔记做本地全文检索。
- `job_events`：如果 Job/Event 需要持久化历史，再从内存事件模型迁入。

## 迁移执行顺序

1. 启动时检测 `gitsonar.db` 是否存在。
   - 若存在：继续使用 SQLite，并保留 JSON 导出能力。
   - 若不存在：进入一次性导入流程。
2. 生成备份目录：
   - `backups/YYYYMMDD-HHMMSS/user_state.json`
   - `backups/YYYYMMDD-HHMMSS/discovery_state.json`
   - `backups/YYYYMMDD-HHMMSS/latest.json`
3. 创建 SQLite 到临时文件 `gitsonar.db.tmp`，不要直接覆盖目标库。
4. 导入仓库基础数据：
   - 先导入 `repo_records`
   - 再导入 `latest.json`
   - 再导入 `discovery_state.last_results`
   - 以 `url` 作为唯一键合并
5. 导入用户状态：
   - 四态列表写入 `user_repo_state`
   - 标签/笔记写入 `repo_annotations`
   - 收藏 watch 写入 `favorite_watch`
   - 更新收件箱写入 `update_events`
   - 反馈信号写入 `feedback_signals`
   - AI Insight 写入 `ai_artifacts`
6. 导入发现状态：
   - 保存视图写入 `discovery_views`
   - 最近一次发现写入 `discovery_runs` / `discovery_results`
7. 校验计数和关键样本。
8. 校验通过后把 `gitsonar.db.tmp` 原子移动为 `gitsonar.db`。
9. 首个版本保留 JSON 文件作为可回滚备份，不立即删除。

## 校验规则

迁移完成前必须至少校验：

- 四态 URL 数量与 JSON 一致。
- `repo_records` 去重后数量不小于四态、更新和发现结果引用的仓库数量。
- `favorite_updates` 数量一致，且 `read_at`、`dismissed_at`、`pinned` 保留。
- `saved_views` 数量一致，且 `query`、`limit`、`ranking_profile` 保留。
- `repo_annotations` 的 tags/note 保留。
- `ai_insights` 输出 JSON 可反序列化，schema version 保留。
- 明文 GitHub Token 和明文代理凭据不进入数据库。

## 回滚策略

- 如果导入过程中任一步失败：
  - 删除 `gitsonar.db.tmp`
  - 保持 JSON runtime 不变
  - 在诊断报告中记录迁移失败原因，但不阻止应用继续启动
- 如果 SQLite 已启用后用户选择回滚：
  - 从 SQLite 导出 JSON 到 `rollback-export/YYYYMMDD-HHMMSS/`
  - 关闭 SQLite 开关
  - 下次启动继续读取 JSON
- 如果 SQLite 文件损坏：
  - 自动重命名为 `gitsonar.db.corrupt-YYYYMMDD-HHMMSS`
  - 尝试从最近 JSON 备份恢复
  - 恢复失败时启动空状态并提示用户导入备份

## 后续实施建议

- 第一个代码任务只新增 `runtime_storage/sqlite_schema.py` 和迁移 dry-run 测试。
- 第二个代码任务实现 JSON -> SQLite 导入，但默认不启用读取。
- 第三个代码任务增加设置开关或自动切换策略。
- 第四个代码任务实现 SQLite -> JSON 导出，确认可回滚后再默认启用。

## 执行步骤

1. 补全本计划的当前状态和目标状态。
   预期结果：迁移边界可审查。
   回滚路径：删除本计划文件。
2. 写出表结构和 JSON 字段映射。
   预期结果：后续实现不需要重新猜数据模型。
   回滚路径：恢复计划到上一版。
3. 写出迁移、校验、导出和回滚步骤。
   预期结果：后续实施有明确检查点。
   回滚路径：不实施迁移，继续使用 JSON。

## 风险

- 技术风险：过早固定表结构。计划中保留阶段性迁移，不一次覆盖所有未来字段。
- 产品风险：迁移失败会影响用户信任。设计要求先备份再导入。
- 隐私 / 安全风险：Token 不进入 SQLite 明文表，继续沿用 DPAPI 设置边界。

## 验证

- 单元测试：本任务为设计任务，无代码测试。
- 手动检查：交叉检查计划与 `state_schema.py`、`state_store.py` 当前字段一致。
- 可靠性检查：计划必须包含备份文件、校验计数和回滚恢复。

## 发布与回滚

- 增量发布：仅新增设计文档。
- 回滚：删除或撤回该计划，不影响运行时。

## 文档更新

- 更新 `TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成 SQLite 迁移设计，明确 JSON 文件覆盖、表结构、迁移顺序、校验和回滚。 |
| `2026-04-24` | `[~]` | 开始 SQLite 迁移设计，仅写文档计划，不实施存储切换。 |
| `2026-04-24` | `[ ]` | Auto Top 5 Batch Sprint 选中，等待执行。 |

## 验证记录

- 已运行测试：不涉及运行时代码，未运行代码测试。
- 手动验证：已用全文检索核对计划覆盖 `user_state`、`discovery_state`、`favorite_updates`、`saved_views`、`ai_insights`、`settings`、`rollback` 等关键迁移字段。
- 尚未覆盖的缺口：后续实施阶段才写迁移 dry-run 与 SQLite schema 测试。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
