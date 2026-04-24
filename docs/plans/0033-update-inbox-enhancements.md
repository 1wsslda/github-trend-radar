# GS-P1-015 Update Inbox 增强

## 任务元信息

- 任务 ID：`GS-P1-015`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`3`
- 推荐 commit message：`feat(updates): add inbox summaries and importance reasons`

## 标题

Update Inbox 自上次查看以来、摘要与重要性解释

## 摘要

- 现有 Update Inbox 已支持已读、置顶、忽略和优先级排序，但每条更新主要展示原始变化列表，研判信息还不够直接。
- 本任务在不改变刷新链路、不新增 provider、不迁移存储的前提下，为收藏更新补充本地生成的变化摘要和重要性解释，并在 UI 中标明自上次查看以来仍需处理的更新。
- 完成后，用户打开“更新”面板时，可以更快判断“发生了什么”和“为什么值得看”。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：收藏更新由 `runtime_github/favorites.py` 生成 `changes` 与 `priority_score`，由 JSON 状态保存，再在前端 Update Inbox 卡片渲染。
- 当前技术形态：JSON 状态仍是事实存储，前端仍是内嵌 Vanilla JS 分片。
- 已知痛点：更新卡片能看到变化项，但缺少一句话摘要、重要性解释和更明确的“自上次查看以来”提示。
- 现有约束：必须保持本地优先、JSON 兼容、当前 API payload 兼容，不新增云调用或大规模 UI 重写。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime_github/favorites.py`
  - `src/gitsonar/runtime/state_schema.py`
  - `src/gitsonar/runtime_ui/js/constants.py`
  - `src/gitsonar/runtime_ui/js/panels.py`
  - `src/gitsonar/runtime_ui/js/cards.py`
  - `tests/test_github_star_sync.py`
  - `tests/test_runtime_state.py`
  - `tests/test_runtime_ui_js_contract.py`

## 目标

- 主要目标：为 favorite update 增加本地生成的 `change_summary` 与 `importance_reason`，并在 UI 中清晰展示。
- 次要目标：让 Update Inbox 搜索覆盖摘要和重要性解释；通过已有 `read_at` 判断并展示“自上次查看以来”状态。
- 成功标准：新字段可生成、可归一化、可导入导出保留、可在 UI 合约中被检查。

## 非目标

- 不新增 AI provider。
- 不调用云 API 生成摘要。
- 不更改 `/api/updates` 的端点形态。
- 不引入 SQLite 或前端框架。
- 不改收藏更新检查频率和调度策略。

## 用户影响

- 受益用户：持续关注 GitHub 收藏项目、需要快速判断更新价值的用户。
- UI 变化：Update Inbox 卡片会显示一句话摘要、重要性说明，以及未读/自上次查看以来提示。
- 保持不变：已读、置顶、忽略、详情、复制摘要、排序和筛选入口保持兼容。

## 隐私与显式同意

- 不涉及新的 Token、AI、云 API、同步或用户数据外发。
- 摘要与重要性解释完全基于已有本地更新字段生成。
- 不需要新增 opt-in。

## 范围

### 范围内

- 扩展 favorite update 本地字段。
- 扩展状态归一化与导入 / 导出兼容。
- 扩展 Update Inbox 前端归一化、搜索和卡片展示。
- 补充 focused 单元测试和 UI 合约测试。

### 范围外

- 真实自然语言 AI 摘要。
- SSE 驱动前端替换。
- 持久化迁移。
- 大规模视觉重设计。

## 架构触点

- 运行时模块：`runtime_github/favorites.py`、`runtime/state_schema.py`
- HTTP / API 变更：无新端点；现有 payload 增加向后兼容字段。
- 状态 / 持久化变更：`favorite_updates` 条目允许保留 `change_summary` 和 `importance_reason`。
- UI 变更：Update Inbox 卡片展示和搜索索引增强。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：
  - `change_summary`：字符串，本地生成的一句话变化摘要。
  - `importance_reason`：字符串，本地生成的重要性说明。
- 新文件或新表：无。
- 迁移需求：无破坏性迁移；旧 update 没有新字段时继续使用 `changes` fallback。
- 导入 / 导出影响：字段由状态归一化保留，旧 JSON 仍可导入。

## API 与契约

- 修改端点：无。
- 响应结构：`/api/updates` 和 bootstrap 中的 favorite update 条目可能包含新增兼容字段。
- 错误行为：无变化。
- 兼容性说明：旧字段仍保留；旧数据没有新字段时 UI 继续显示已有 `changes`。

## 执行步骤

1. 补测试并确认 RED。
   预期结果：现有实现缺少摘要、重要性解释或 UI 展示契约，测试失败。
   回滚路径：删除新增测试。
2. 实现最小后端字段生成与归一化。
   预期结果：新生成的 favorite update 带 `change_summary` 和 `importance_reason`，导入导出保留。
   回滚路径：移除新字段生成和归一化。
3. 实现最小前端展示与搜索增强。
   预期结果：Update Inbox 卡片展示摘要、重要性和“自上次查看以来”提示；搜索覆盖新字段。
   回滚路径：撤销 `runtime_ui/js` 改动。
4. 运行 focused 验证并更新文档。
   预期结果：相关 Python 与 JS 合约测试通过，计划和进度记录同步。
   回滚路径：恢复本计划状态为未完成并保留失败说明。

## 风险

- 技术风险：摘要字段可能和 `changes` 重复，需要 UI 避免噪音。
- 产品风险：重要性解释必须短而可扫读，不能显得像不透明评分。
- 隐私 / 安全风险：低；不新增网络外发。
- 发布风险：低；新增字段向后兼容。

## 验证

- 单元测试：
  - `python -m pytest tests/test_github_star_sync.py::GitHubStarSyncTests::test_track_favorite_updates_adds_summary_and_importance_reason -q`
  - `python -m pytest tests/test_runtime_state.py::RuntimeStateFeatureTests::test_favorite_update_summary_and_importance_round_trip -q`
- UI 合约测试：
  - `python -m pytest tests/test_runtime_ui_js_contract.py::RuntimeUIJSContractTests::test_update_inbox_enhancement_contract_is_present -q`
- 集成回归：
  - `python -m pytest tests/test_github_star_sync.py tests/test_runtime_state.py tests/test_runtime_api_boundary.py tests/test_runtime_ui_js_contract.py tests/test_runtime_ui_assets.py -q`
- 手动检查：
  - 启动应用，打开“更新”面板。
  - 准备一条有 `changes`、`change_summary`、`importance_reason` 的 favorite update。
  - 预期卡片显示变化摘要、重要性说明、自上次查看以来 / 未读提示。
  - 搜索摘要或重要性关键词时能命中该更新。
- 需要关注的日志 / 诊断信号：无新增外部调用；刷新失败仍走既有安全状态。

## 发布与回滚

- 发布方式：随本地应用代码默认启用。
- 是否需要开关：不需要；旧数据自动 fallback。
- 如果失败，用户恢复方式：撤回本次 commit 或删除新增字段，旧 `changes` 仍可继续展示。

## 文档更新

- 需要更新的文档：
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
  - `docs/roadmap/ROADMAP.md`
  - `docs/ARCHITECTURE.md`
  - `CHANGELOG.md`
- 用户可见文案：Update Inbox 卡片内短标签和说明。
- 内部维护说明：本计划文件。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成后端字段生成、状态归一化、前端展示与 focused 验证。 |
| `2026-04-24` | `[~]` | 已创建计划；准备补 TDD 测试。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_github_star_sync.py::GitHubStarSyncTests::test_track_favorite_updates_adds_summary_and_importance_reason tests/test_runtime_state.py::RuntimeStateFeatureTests::test_favorite_update_summary_and_importance_round_trip tests/test_runtime_ui_js_contract.py::RuntimeUIJSContractTests::test_update_inbox_enhancement_contract_is_present -q`，`3 passed, 9 subtests passed`
  - `python -m pytest tests/test_github_star_sync.py tests/test_runtime_state.py tests/test_runtime_api_boundary.py tests/test_runtime_ui_js_contract.py tests/test_runtime_ui_assets.py -q`，`56 passed, 164 subtests passed`
- 手动验证：待用户在桌面应用中按下方步骤执行。
  - 启动 GitSonar，进入“更新”面板。
  - 触发刷新或准备一条包含 Star / Fork / Push / Release 变化的收藏仓库更新。
  - 预期更新卡片显示 `自上次查看以来`、变化摘要和 `重要性` 说明；搜索摘要或重要性关键词可以命中该卡片。
- 尚未覆盖的缺口：未在本轮启动真实桌面壳截图验证；通过 UI 合约和手动步骤覆盖。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
