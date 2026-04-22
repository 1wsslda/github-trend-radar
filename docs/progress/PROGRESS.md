# GitSonar 进度日志

`docs/progress/PROGRESS.md` 用于按时间顺序记录仓库工作的状态变化。

## 记录规则

- 按时间记录任务状态变化，最新记录放最上面。
- 每条状态变化都必须与 `TASKS.md` 保持一致。
- 如果任务属于当前 Sprint 队列，也要同步 `docs/sprints/CURRENT_TOP10.md`。
- 每条记录都应写清 Plan、Branch、Commit / PR、验证方式和下一步。
- 暂时没有 Branch 或 Commit / PR 时，统一写 `-`。

## 进度记录

| 日期 | 任务 ID | 状态 | 摘要 | Plan | Branch | Commit / PR | 验证 | 下一步 |
|---|---|---|---|---|---|---|---|---|
| `2026-04-23` | `GS-P1-001` | `[x]` | 定义 `gitsonar.repo_insight.v1` 本地 Schema，新增 RepoContext 复制、Insight JSON 手动保存 / 删除和本地缓存展示。 | `docs/plans/0010-ai-insight-schema-mvp.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续如接入 provider，继续保持显式 opt-in。 |
| `2026-04-23` | `GS-P0-009` | `[x]` | 为仓库卡片、更新卡片和详情面板新增 Markdown 摘要复制入口，摘要会复用 README、标签和本地笔记。 | `docs/plans/0009-copy-markdown-summary.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续可在不引入同步的前提下扩展批量导出。 |
| `2026-04-23` | `GS-P0-008` | `[x]` | 忽略动作现在会采集本地原因，并将反馈信号写入用户状态，参与后续发现排序与推荐原因展示。 | `docs/plans/0008-ignore-feedback.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续可在本地前提下继续细化反馈维度。 |
| `2026-04-23` | `GS-P0-007` | `[x]` | 发现结果卡片和详情页会显示“为什么推荐”，并把本地忽略反馈提升到高优先级说明。 | `docs/plans/0007-why-recommended.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续可在不暴露内部权重的前提下继续细化文案。 |
| `2026-04-23` | `GS-P0-006` | `[x]` | 把收藏更新扩展为可处理收件箱：支持已读、置顶、忽略和优先级排序。 | `docs/plans/0006-update-inbox-mvp.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续如需实时推送，先完成统一 Job / Event 模型。 |
| `2026-04-23` | `GS-P0-005` | `[x]` | 增加本地保存发现视图能力，可保存、载入、重跑和删除搜索配置，并记录上次运行结果数。 | `docs/plans/0005-saved-discovery-views-mvp.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续可在保持本地优先前提下加入更细粒度筛选。 |
| `2026-04-23` | `GS-P0-004` | `[x]` | 为仓库新增本地标签和笔记状态，支持详情编辑、列表搜索命中和导入 / 导出兼容。 | `docs/plans/0004-tags-notes-mvp.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续可在不引入新存储层前提下继续扩展筛选。 |
| `2026-04-23` | `GS-P0-003` | `[x]` | 新增本地网络诊断面板与 `/api/diagnostics`，覆盖运行目录、loopback 端口、状态文件、代理、Token 和 GitHub 可达性。 | `docs/plans/0003-network-diagnostics-mvp.md` | `-` | `-` | `python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`。 | 后续仅在确认用户价值后再考虑更深的环境自检。 |
| `2026-04-23` | `GS-P0-002` | `[x]` | 完成 Auto Top 10 Sprint 任务体系：重写 `TASKS.md`、`PLANS.md`、`docs/plans/PLAN_TEMPLATE.md`、`docs/progress/PROGRESS.md`，创建 `docs/sprints/CURRENT_TOP10.md`，并补齐 Top 10 对应计划文件。 | `docs/plans/0002-task-tracking-system.md` | `-` | `-` | 人工交叉检查任务表、计划文件、Sprint 队列和进度日志；确认未修改 `src/`。 | 下一轮从 `GS-P0-003` 开始。 |
| `2026-04-23` | `GS-P0-001` | `[x]` | 刷新 `AGENTS.md` 中的 Codex 执行规则，明确读文档顺序、任务追踪规则和 Auto Top 10 Sprint 规则。 | `docs/plans/0001-codex-guidance-docs.md` | `-` | `-` | 人工检查 `AGENTS.md` 与战略、路线图、计划、进度、Sprint 文档之间的交叉引用。 | 后续任务体系变更时继续同步 `AGENTS.md`。 |
| `2026-04-22` | `GS-P0-002` | `[x]` | 建立最初的仓库任务追踪基础，包括 `TASKS.md`、`PLANS.md`、`docs/progress/PROGRESS.md` 与编号计划文件。 | `docs/plans/0002-task-tracking-system.md` | `-` | `-` | 仅文档改动；无 `src/` 变更。 | 继续扩展成自动 Sprint 队列。 |
| `2026-04-22` | `GS-P0-002` | `[~]` | 开始建立仓库任务追踪体系，先阅读战略、路线图、计划模板、架构与安全文档。 | `docs/plans/0002-task-tracking-system.md` | `-` | `-` | 已确认范围只限于文档与任务管理体系。 | 起草任务表、计划规则与进度日志。 |
