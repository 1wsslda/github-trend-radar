# 发现结果聚类计划

## 任务元信息

- 任务 ID：`GS-P1-007`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`6`
- 推荐 commit message：`feat: cluster discovery results locally`

## 标题

`发现结果聚类`

## 摘要

- 这个任务把关键词发现结果按本地可解释主题聚类，减少用户面对长列表时的认知负担。
- 现在做是因为 JSON API、Job/Event、SSE 和 AI artifact 本地边界已经稳定，聚类可以作为 P1 智能化能力的最后一项安全增量。
- 做完后用户能看到每个发现结果所属主题，并在发现页看到本次结果的聚类数量和主题摘要。

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

- 当前行为：发现结果以综合分排序的扁平列表展示，卡片可显示推荐原因。
- 当前技术形态：Python runtime 生成 discovery state，本地 HTTP API 和内嵌 vanilla JS 渲染发现页。
- 已知痛点：用户无法快速判断一批发现结果分成哪些主题。
- 现有约束：不能引入云服务、AI provider、大模型下载、SQLite 切换或前端框架迁移。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime_github/discovery.py`
  - `src/gitsonar/runtime/state_schema.py`
  - `src/gitsonar/runtime/state_store.py`
  - `src/gitsonar/runtime/repo_records.py`
  - `src/gitsonar/runtime/api_boundary.py`
  - `src/gitsonar/runtime_ui/js/*.py`
  - `tests/test_discovery_profiles.py`
  - `tests/test_runtime_state.py`
  - `tests/test_runtime_api_boundary.py`

## 目标

- 主要目标：为 discovery results 生成稳定、可解释、纯本地的 cluster metadata。
- 次要目标：在发现页显示聚类摘要和每张发现卡片的聚类标签。
- 成功标准：
  - discovery payload 和 persisted discovery state 都包含 `last_clusters`。
  - discovery result repo record 保留 `cluster_id` 与 `cluster_label`。
  - `/api/bootstrap` 的 discovery 摘要包含聚类数量。
  - 不增加外部依赖，不访问网络，不改变 JSON 兼容性。

## 非目标

- 不做 embedding、RAG、AI 批量归类或 provider 接入。
- 不引入 scikit-learn、SQLite、React、FastAPI 或 WebGL 地图。
- 不改变 discovery 排序算法本身。

## 用户影响

- 发现页用户会看到本次结果分成几个主题。
- 发现卡片会显示所属主题，帮助快速扫读。
- 现有搜索、排序、保存视图、批量分析和状态标记行为保持不变。

## 隐私与显式同意

- 不涉及 AI、云 API、同步、Token 或用户数据外发。
- 没有数据离开本机。
- 不需要额外 opt-in。
- 聚类只基于本地已有 repo name、description、topics、language、matched terms。

## 范围

### 范围内

- 新增本地聚类 helper。
- 在 discovery payload/state 中写入 cluster metadata。
- 保持 JSON 导入 / 导出向后兼容。
- 在现有 UI 小幅展示聚类摘要与卡片标签。
- 添加单元测试和 UI 合约级检查。

### 范围外

- 可视化地图。
- 语义 embedding。
- AI 归类建议。
- 新持久化层。

## 架构触点

- 涉及的运行时模块：`runtime/discovery_clusters.py`、`runtime/state_schema.py`、`runtime/state_store.py`、`runtime/repo_records.py`
- HTTP / API 变更：`/api/discovery` 通过已有 discovery state 返回 `last_clusters`；`/api/bootstrap` discovery 摘要增加 `cluster_count`
- 状态 / 持久化变更：`discovery_state.json` 可新增 `last_clusters`；旧文件缺失该字段时归一化为空列表
- UI 变更：发现页 summary strip、results toolbar、discover card badge/reason strip 小幅展示
- 后台任务变更：完成态 discovery job 自动携带聚类后的 discovery state
- 打包 / 启动 / 壳层变更：无

## 数据模型

- 新字段：
  - repo record：`cluster_id`、`cluster_label`
  - discovery state：`last_clusters`
- 新文件或新表：`src/gitsonar/runtime/discovery_clusters.py`
- 迁移需求：无强制迁移；旧 JSON 缺字段时默认空列表。
- 导入 / 导出影响：导出会包含新增字段；导入旧结构仍可读取。

## API 与契约

- 要新增或修改的端点：不新增端点；扩展既有 JSON payload。
- 请求 / 响应结构：
  - `discovery_state.last_clusters[] = {id, label, count, repo_urls, top_terms, languages}`
  - `repo.cluster_id` / `repo.cluster_label`
  - `bootstrap.discovery.cluster_count`
- 错误行为：聚类失败不应影响搜索结果；实现应保持纯函数和确定性，避免运行时异常。
- 兼容性说明：旧客户端忽略新增字段即可继续工作。

## 执行步骤

1. 第一步：写失败测试。
   预期结果：测试证明 cluster metadata 当前缺失。
   回滚路径：删除新增测试文件或新增测试用例。
2. 第二步：实现本地聚类 helper 并接入 discovery payload/state。
   预期结果：测试通过，旧 discovery state 仍能归一化。
   回滚路径：移除 helper import 与字段写入，恢复旧 state 字段。
3. 第三步：扩展 UI 展示和 API 摘要。
   预期结果：发现页可以展示聚类数和卡片主题标签。
   回滚路径：删除 UI 展示逻辑，保留后端字段也不影响旧行为。
4. 第四步：运行目标测试与全量测试。
   预期结果：目标测试和全量 pytest 通过。
   回滚路径：回退本计划涉及文件。

## 风险

- 技术风险：关键词式聚类不等同语义聚类，主题可能粗糙。
- 产品风险：聚类标签需要简洁，避免把推荐原因区域挤满。
- 隐私 / 安全风险：低；仅处理本地已有公开 repo metadata。
- 发布风险：低；无依赖和启动链路变更。

## 验证

- 单元测试：
  - `python -m pytest tests/test_discovery_clusters.py tests/test_runtime_state.py tests/test_runtime_api_boundary.py -q`
- 集成测试：
  - `python -m pytest tests/test_discovery_profiles.py tests/test_runtime_http.py -q`
- 手动检查：
  - 检查发现页 JS 字符串包含聚类摘要与卡片标签逻辑。
- 性能或可靠性检查：
  - 聚类只处理最多 100 个 discovery results，纯内存 O(n * tokens)。
- 需要关注的日志 / 诊断信号：
  - 无新增网络或敏感日志。

## 发布与回滚

- 如何增量发布？随本地 runtime 一起发布，旧数据自动默认无 cluster。
- 是否需要开关或受控状态？不需要，字段缺失时 UI 自动隐藏。
- 如果失败，用户如何恢复？删除本次 commit 或清空 discovery results 即可回到旧行为。

## 文档更新

- 需要更新的文档：`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`
- 需要更新的用户可见文案：发现页聚类摘要和卡片聚类标签。
- 需要更新的内部维护说明：本计划文件。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成本地 discovery result 聚类、state/API 字段和发现页展示。 |
| `2026-04-24` | `[~]` | 已创建计划并开始 TDD。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_discovery_clusters.py tests/test_runtime_state.py::RuntimeStateFeatureTests::test_apply_discovery_result_persists_clusters_and_repo_labels tests/test_runtime_api_boundary.py::RuntimeAPIBoundaryTests::test_bootstrap_returns_sanitized_settings_and_counts -q`，3 passed。
  - `python -m pytest tests/test_discovery_clusters.py tests/test_runtime_state.py tests/test_runtime_api_boundary.py tests/test_discovery_profiles.py tests/test_runtime_http.py tests/test_runtime_ui_js_contract.py -q`，77 passed，44 subtests passed。
  - `python -m pytest -q`，176 passed，149 subtests passed。
- 手动验证：检查 `git status --short` 与 `git diff --stat`，确认本任务改动集中在 clustering、discovery state/API/UI、测试和追踪文档；`最新prompt.md` 为既有未跟踪 IDE prompt 文件，未纳入本任务。
- 尚未覆盖的缺口：未做真实 GitHub 网络搜索截图验证；本任务聚焦本地算法、state/API 契约和 JS 合约。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
