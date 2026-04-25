# GitSonar UI Performance Audit and Jank Fixes

## 任务元信息

- 任务 ID：`GS-P1-020`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：专项任务
- 推荐 commit message：`perf(ui): reduce scroll jank across overlays and lists`

## 标题

`整页性能审计与滚动卡顿修复`

## 摘要

- 修复仓库详情下拉时的明显卡顿，并覆盖同类前端滚动路径：详情、对比、诊断弹层、主列表、更新页、发现页、控制抽屉和菜单滚动。
- 本轮只在当前 Python + 本地 HTTP + Vanilla JS/CSS 架构中做增量优化，不引入 React、FastAPI、SQLite 切换或云能力。
- 完成后用户可见结果是滚动更顺、菜单滚动重算减少、详情相关重复请求减少，现有详情、摘要、对比、标签笔记和批量选择流程保持可用。

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

- 当前行为：前端使用 Vanilla JS 分片渲染列表和弹层；列表已有 30 条懒加载，但滚动、resize、菜单定位和详情请求仍存在重复工作。
- 当前技术形态：`src/gitsonar/runtime_ui/js/menus.py` 处理菜单定位，`cards.py` 处理卡片渲染和描述测量，`actions.py` 处理详情请求，`boot.py` 注册全局事件，CSS 分布在 `css/cards.py`、`css/overlays.py`、`css/responsive.py`。
- 已知痛点：无打开菜单时滚动仍会进入菜单重定位路径；弹层内部滚动会触发 document 捕获阶段 scroll listener；描述测量会重复读取布局；详情、摘要和对比之间会重复请求同一仓库详情；批量卡片初次渲染动画会增加绘制成本。
- 现有约束：不能改 API、不能改持久化格式、不能引入新前端框架或后端任务系统。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime_ui/js/menus.py`
  - `src/gitsonar/runtime_ui/js/cards.py`
  - `src/gitsonar/runtime_ui/js/actions.py`
  - `src/gitsonar/runtime_ui/js/boot.py`
  - `src/gitsonar/runtime_ui/css/cards.py`
  - `src/gitsonar/runtime_ui/css/overlays.py`
  - `src/gitsonar/runtime_ui/css/responsive.py`
  - `tests/test_runtime_ui_assets.py`
  - `tests/test_ui_js_smoke.py`

## 目标

- 主要目标：降低滚动路径上的布局读取、全屏重绘和重复网络请求。
- 次要目标：用 JS/CSS 合约测试固定性能约束，避免后续回退。
- 成功标准：
  - `repositionOpenMenus()` 在没有打开菜单时直接返回。
  - document 捕获阶段 scroll listener 跳过弹层、面板、菜单和内部滚动容器。
  - resize 和描述测量通过 requestAnimationFrame 合并，且已处理描述不重复测量。
  - `fetchRepoDetails()` 有页面内存缓存和 in-flight 请求去重。
  - 卡片、更新卡片、对比卡片、详情区块和 README 区块有 CSS 渲染隔离。
  - 批量卡片初次渲染动画被移除或限制，选中反馈动画保留。

## 非目标

- 不新增或修改 HTTP API。
- 不修改 JSON state/schema、导入导出格式或 detail cache 持久化格式。
- 不处理后台 API 性能、GitHub 请求速度、SQLite 存储迁移或前端框架迁移。
- 不新增 AI provider、云 API、同步能力或任何数据外发。

## 用户影响

- 受益用户：在仓库详情、对比、诊断、更新页、发现页和主列表中长时间滚动阅读的用户。
- UI 或工作流变化：没有新的用户可见入口；滚动和打开详情的体感应更稳定。
- 保持不变：详情打开、复制 Markdown、编辑标签/笔记、打开 GitHub、对比、诊断、批量选择和菜单操作。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据：否。
- 是否有数据离开本机：否。
- 是否需要显式 opt-in：否。
- 是否需要用户确认或预览：否。

## 范围

### 范围内

- 前端 JS 滚动、resize、菜单定位和详情请求路径。
- CSS 渲染隔离、content visibility、overscroll containment 和低成本 overlay 绘制。
- UI JS/CSS 合约测试。
- 任务追踪文档同步。

### 范围外

- 后端 detail cache 策略、GitHub API 并发或持久化缓存格式。
- React/Vite/FastAPI/SQLite 迁移。
- 视觉重设计或导航重写。
- 云端性能监控或真实用户监控服务。

## 架构触点

- 涉及的运行时模块：`runtime_ui`。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：仅内部性能行为和 CSS 渲染成本优化。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 新增或修改端点：无。
- 请求 / 响应结构：不变。
- 错误行为：不变。
- 兼容性说明：页面内 detail memory cache 只复用当前浏览器会话中的成功详情响应；刷新页面后仍走现有后端 detail cache 和 API。

## 执行步骤

1. 创建 RED 测试和计划追踪。
   预期结果：性能契约在当前代码上失败，失败点对应滚动重定位、详情请求缓存、描述测量和 CSS 隔离缺口。
   回滚路径：删除本计划、任务追踪行和新增测试。
2. 优化滚动与菜单路径。
   预期结果：无打开菜单时 scroll/resize 不进入菜单布局读取；内部滚动容器不会触发菜单重定位。
   回滚路径：恢复 `menus.py` 和 `boot.py`。
3. 优化列表测量与动画。
   预期结果：描述测量只处理新卡片或强制 resize；批量初次渲染动画移除，选中反馈保留。
   回滚路径：恢复 `cards.py`、`css/responsive.py` 和相关测试。
4. 优化详情请求复用。
   预期结果：同一仓库详情在详情、复制摘要和对比之间复用缓存或同一个 in-flight promise。
   回滚路径：恢复 `actions.py`。
5. 优化弹层和卡片 CSS 隔离。
   预期结果：面板内部滚动隔离，全屏 blur 成本降低，长内容区使用 `content-visibility`。
   回滚路径：恢复 `css/overlays.py`、`css/cards.py`。
6. 运行验证并记录结果。
   预期结果：targeted 与 full pytest、`git diff --check` 完成；如有既有非本任务失败，明确记录。
   回滚路径：按文件级 diff 恢复本任务改动。

## 风险

- 技术风险：`content-visibility` 可能影响 offscreen 内容的测量，需要让描述测量只处理已渲染卡片并在 resize 强制刷新。
- 产品风险：菜单在内部滚动容器中可能不跟随重定位；本轮按用户目标跳过内部滚动重算，避免主卡顿路径。
- 隐私 / 安全风险：无新增网络或数据外发。
- 发布风险：CSS containment 在较老浏览器中会被忽略，页面仍可正常工作。

## 验证

- 单元 / 合约测试：
  - `python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py tests/test_runtime_detail_cache.py -q`
  - `python -m pytest -q`
- 静态检查：
  - `git diff --check`
- 手动检查：
  - `python src/gitsonar/__main__.py`
  - 打开仓库详情并连续下拉，确认无明显卡顿。
  - 验证对比弹层、诊断弹层、更新页、发现页、主列表懒加载和控制抽屉滚动。
  - 打开菜单后滚动页面，确认菜单仍能正确定位或关闭；无菜单时滚动不触发菜单布局重算。
  - 验证详情打开、复制 Markdown、编辑标签/笔记、打开 GitHub、批量选择功能不回退。

## 发布与回滚

- 增量发布：随下一次本地应用版本发布；无迁移步骤。
- 开关或受控状态：不需要。
- 失败恢复：回滚本任务涉及的 JS/CSS/测试和文档文件即可；用户数据不受影响。

## 文档更新

- 需要更新的文档：
  - `TASKS.md`
  - `docs/progress/PROGRESS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - 本计划文件
- 用户可见文案：无新增。
- 内部维护说明：本计划记录性能契约与回滚路径。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 已完成性能专项改动和自动验证；手动滚动验证尚未执行。 |
| `2026-04-25` | `[~]` | 已创建计划，准备写 RED 测试并实施性能专项改动。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py tests/test_runtime_detail_cache.py -q`，新增性能契约后 17 failed，确认当前实现缺少滚动短路、详情缓存、描述测量去重和 CSS 隔离。
  - GREEN：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py tests/test_runtime_detail_cache.py -q`，59 passed，239 subtests passed。
  - 全量：`python -m pytest -q`，217 passed，266 subtests passed。
  - 静态：`git diff --check`，退出码 0，仅有 LF/CRLF 警告。
- 手动验证：尚未启动桌面壳逐项滚动验证。
- 尚未覆盖的缺口：真实浏览器 Performance panel 采样需要手动执行。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
