# 仓库地图 / 可视化体验计划

## 任务元信息

- 任务 ID：`GS-P2-001`
- 优先级：`P2`
- 当前状态：`[x]`
- Sprint 候选排名：`7`
- 推荐 commit message：`feat: add discovery cluster map`

## 标题

`仓库地图 / 可视化体验`

## 摘要

- 这个任务把已完成的发现结果聚类转化为一个轻量二维主题地图，帮助用户在发现页先看主题结构，再看具体仓库卡片。
- 现在做是因为 `GS-P1-007` 已经提供本地 `last_clusters` 和每个 repo 的 `cluster_label`，可以低风险增加可视化层。
- 做完后用户能看到每批发现结果的主题地图，并可一键选中某个主题下的仓库。

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

- 当前行为：发现页展示聚类数量、主题摘要和卡片 cluster badge，但没有可扫读的地图式主题结构。
- 当前技术形态：内嵌 HTML/CSS/vanilla JS，发现页由 `runtime_ui/js/discovery.py`、`cards.py`、`panels.py` 等分片拼接。
- 已知痛点：用户仍需要从列表里逐张读卡片，才能理解主题之间的分布。
- 现有约束：保持阅读型、低噪声界面；不引入 WebGL、Canvas 框架、React、Vite 或新依赖。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime_ui/js/discovery.py`
  - `src/gitsonar/runtime_ui/js/state.py`
  - `src/gitsonar/runtime_ui/css/controls.py`
  - `tests/test_runtime_ui_js_contract.py`
  - `tests/test_runtime_ui_assets.py`
  - `tests/test_ui_js_smoke.py`

## 目标

- 主要目标：在发现页新增一个本地主题地图 MVP。
- 次要目标：主题节点可触发选择该 cluster 下的仓库，配合现有批量分析/标记动作。
- 成功标准：
  - 聚类数大于 1 时显示 `主题地图`。
  - 每个 cluster 节点展示 label、数量、主要语言或关键词。
  - 点击 cluster 节点会选中该 cluster 下的 repo URL。
  - JS 合约和语法检查通过。

## 非目标

- 不做 WebGL 仓库地图。
- 不做拖拽、缩放、力导向图或复杂坐标布局。
- 不做 embedding 语义相似度。
- 不改变 discovery result 排序和状态持久化。

## 用户影响

- 用户进入发现页后，可以先从主题地图判断本批结果结构。
- 用户点击某个主题节点后，可以复用现有批量分析、收藏、稍后看、忽略等动作。
- 原有发现列表、推荐原因、保存视图、AI prompt handoff 都保持不变。

## 隐私与显式同意

- 不涉及 AI、云 API、同步、Token 或用户数据外发。
- 没有数据离开本机。
- 不需要显式 opt-in。
- 地图只基于本地已有 discovery cluster metadata。

## 范围

### 范围内

- 新增 discovery cluster map 渲染函数。
- 新增 cluster select helper。
- 添加低噪声 CSS，使地图符合阅读型工作台风格。
- 更新 JS 合约测试。

### 范围外

- 后端 API 变更。
- 新数据字段。
- 高级图谱交互。
- 新构建工具。

## 架构触点

- 涉及的运行时模块：无后端运行时变更。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：`runtime_ui/js/discovery.py`、`runtime_ui/css/controls.py`。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 要新增或修改的端点：无。
- 请求 / 响应结构：复用 `discoveryState.last_clusters` 和 repo `cluster_id` / `cluster_label`。
- 错误行为：cluster 数据缺失或只有一个 cluster 时隐藏地图。
- 兼容性说明：旧 discovery state 不含 cluster 时 UI 不展示地图。

## 执行步骤

1. 第一步：写失败的 UI 合约测试。
   预期结果：测试指出缺少 cluster map 渲染和 cluster select helper。
   回滚路径：删除测试断言。
2. 第二步：实现 discovery cluster map JS。
   预期结果：发现页 intro 区域出现主题地图，节点点击可选中仓库。
   回滚路径：删除新增渲染函数与调用点。
3. 第三步：补充 CSS。
   预期结果：地图保持低噪声、可扫读、移动端可换行。
   回滚路径：删除新增 CSS block。
4. 第四步：运行 UI 与全量测试。
   预期结果：JS 合约、语法和全量 pytest 通过。
   回滚路径：回退本计划涉及文件。

## 风险

- 技术风险：纯 CSS/HTML 地图表达能力有限。
- 产品风险：如果视觉过重会干扰阅读流，因此默认只在有多个 cluster 时展示。
- 隐私 / 安全风险：低；无网络或敏感数据处理。
- 发布风险：低；无依赖和打包脚本变更。

## 验证

- 单元测试：
  - `python -m pytest tests/test_runtime_ui_js_contract.py -q`
- 集成测试：
  - `python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`
- 手动检查：
  - 检查聚类地图文案、CSS 类名和点击选择逻辑。
- 性能或可靠性检查：
  - 渲染最多 6 个 cluster 节点，不遍历超大 DOM。
- 需要关注的日志 / 诊断信号：
  - 无新增日志。

## 发布与回滚

- 如何增量发布？随 UI 静态资源一并发布。
- 是否需要开关或受控状态？不需要；缺少 cluster 数据时自动隐藏。
- 如果失败，用户如何恢复？回退 commit；旧发现页仍可工作。

## 文档更新

- 需要更新的文档：`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`
- 需要更新的用户可见文案：`主题地图`、`选中本组`。
- 需要更新的内部维护说明：本计划文件。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已完成发现页主题地图和选中本组交互。 |
| `2026-04-24` | `[~]` | 已创建计划并开始 TDD。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_runtime_ui_js_contract.py::RuntimeUIJSContractTests::test_discovery_cluster_map_contract_is_present -q`，1 passed，5 subtests passed。
  - `python -m pytest tests/test_runtime_ui_js_contract.py tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`，40 passed，148 subtests passed。
- 手动验证：检查 `renderDiscoveryClusterMap`、`selectDiscoveryCluster`、`discover-cluster-map` CSS 与 `renderDiscoverCanvasIntro` 调用点；确认未新增依赖、端点或持久化字段。
- 尚未覆盖的缺口：未运行真实浏览器截图；本任务通过 JS 聚合语法、UI 合约和 smoke 测试覆盖静态资源。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
