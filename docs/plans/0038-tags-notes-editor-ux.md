# 标签与笔记编辑体验优化

## 任务元信息

- 任务 ID：`GS-P0-013`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 候选排名：用户直接指定
- 推荐 commit message：`feat(ui): improve tags and notes editor`

## 摘要

- 去掉标签 / 笔记编辑的浏览器原生 `window.prompt()`。
- 在仓库详情抽屉内提供本地整理编辑区，支持标签 chip、推荐标签、输入添加和笔记失焦自动保存。
- 保持现有 Windows-first、Vanilla JS、本地 JSON 状态和 `/api/repo-annotations` 接口，不引入 React、SQLite、AI 或云能力。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 当前架构：`docs/ARCHITECTURE.md`
- 安全边界：`docs/SECURITY.md`
- 对应能力：P0 标签与笔记闭环的体验增强。

## 当前状态

- 标签和笔记已经通过 `repo_annotations[url].tags`、`repo_annotations[url].note` 存入本地 JSON。
- 后端已有 `POST /api/repo-annotations`，请求为 `{ url, repo, tags, note }`，响应为 `{ ok, annotation, user_state }`。
- 旧 UI 在详情抽屉按钮中调用 `window.prompt()`，编辑体验割裂且不适合连续整理。

## 目标

- 详情抽屉中的“本地标签与笔记”升级为“本地整理”。
- 已选标签以可点击 chip 展示，再次点击可移除。
- 推荐标签基于本地已有仓库信息确定性生成，不联网、不调用 AI。
- 标签输入框支持 Enter 添加，逗号和中文逗号分隔，前端限制最多 12 个标签。
- 笔记始终显示为 textarea，失焦自动保存，并展示“保存中 / 已保存 / 保存失败”状态。

## 非目标

- 不改后端 API。
- 不改数据模型。
- 不新增持久化层、后台任务系统、AI provider、云同步或外部数据流。
- 不处理忽略原因、保存发现视图命名等其他仍使用 `window.prompt()` 的功能。
- 不更新 `ROADMAP.md`、`ARCHITECTURE.md`、`SECURITY.md`，因为本任务不改变架构、安全边界或外部网络行为。

## 用户影响

- 用户在详情抽屉内即可完成标签和笔记整理，不再被浏览器 prompt 打断。
- 标签保存后会刷新列表卡片中的标签展示。
- 笔记保存不会强制重绘详情抽屉，避免 textarea 输入焦点和编辑上下文丢失。

## 隐私与显式同意

- 不涉及 AI、云 API、同步、Token 或用户数据外发。
- 所有推荐标签只使用本地已加载的仓库字段和确定性关键词规则。
- 不需要新增 opt-in。

## 范围

### 范围内

- `src/gitsonar/runtime_ui/js/actions.py`
- `src/gitsonar/runtime_ui/js/overlays.py`
- `src/gitsonar/runtime_ui/js/constants.py`
- `src/gitsonar/runtime_ui/css/overlays.py`
- `tests/test_runtime_ui_assets.py`
- `tests/test_ui_js_smoke.py`
- `TASKS.md`
- `docs/sprints/CURRENT_TOP10.md`
- `docs/progress/PROGRESS.md`

### 范围外

- `src/gitsonar/runtime/http.py`
- `src/gitsonar/runtime/state.py`
- `src/gitsonar/runtime/state_schema.py`
- `docs/roadmap/ROADMAP.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`

## 架构触点

- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：详情抽屉内新增原生风格整理区。
- 后台任务变更：无。
- 启动 / 桌面壳变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 继续使用 `POST /api/repo-annotations`。
- 请求仍为 `{ url, repo, tags, note }`。
- 响应仍为 `{ ok, annotation, user_state }`。
- 前端继续复用 `persistRepoAnnotation()`。

## 执行步骤

1. 新增 UI asset 测试。
   预期结果：旧 prompt 编辑流无法通过测试。
   回滚路径：删除新增测试。
2. 实现详情抽屉整理区。
   预期结果：标签 chip、推荐标签、输入添加、笔记 textarea 和保存状态可渲染。
   回滚路径：恢复旧 `renderCurrentDetailPanel()` 标签与笔记段落。
3. 接入保存逻辑。
   预期结果：标签变化调用 `/api/repo-annotations` 并刷新卡片；笔记失焦保存且不重绘详情抽屉。
   回滚路径：恢复旧 `editRepoTags()` / `editRepoNote()` prompt 流。
4. 更新任务追踪文档并运行验证。
   预期结果：`TASKS.md`、`CURRENT_TOP10.md`、`PROGRESS.md` 与计划文件一致。
   回滚路径：恢复文档记录为任务未完成。

## 风险

- 技术风险：Vanilla JS 字符串模板较长，需要通过 asset smoke test 保护函数和标记契约。
- 产品风险：推荐标签是轻量规则，不能等同 AI 语义标签。
- 隐私 / 安全风险：无新增外发边界。
- 发布风险：低，仅影响详情抽屉局部交互。

## 验证

- RED：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q` 先失败，确认缺少本地整理 UI helper 且编辑函数仍使用 `window.prompt()`。
- GREEN：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`：`39 passed, 156 subtests passed`。
- 回归：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_http.py tests/test_runtime_state.py -q`：最终重跑 `100 passed, 196 subtests passed`。
- 静态检查：`git diff --check` 退出码 0，仅有 LF/CRLF 提示。
- 手动验证：尚未打开桌面壳逐项点击验证；本轮以 UI asset 和后端状态回归测试覆盖。

## 发布与回滚

- 增量发布：随普通 UI 资源发布。
- 失败回滚：恢复本计划涉及的前端资源和测试改动即可；后端状态和 JSON 数据无需迁移回滚。

## 文档更新

- 已更新：`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。
- 未更新：`ROADMAP.md`、`ARCHITECTURE.md`、`SECURITY.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 完成详情抽屉本地整理编辑区、测试和任务追踪更新。 |

## 验收清单

- [x] 范围小且可回滚。
- [x] 没有隐藏的大迁移。
- [x] 隐私 / opt-in 行为明确。
- [x] 回滚路径已定义。
- [x] 验证步骤具体可执行。
- [x] 已写明战略与路线图映射。
