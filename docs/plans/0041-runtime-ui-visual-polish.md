# Runtime UI visual polish

## 任务元信息

- 任务 ID：`GS-P2-015`
- 优先级：`P2`
- 当前状态：`[x]`
- Sprint 候选排名：用户指定插入到 `GS-P2-008` 之前
- 推荐 commit message：`style(ui): polish runtime visual system`

## 标题

`Runtime UI visual polish`

## 摘要

- 本任务只在现有 `runtime_ui` Vanilla HTML/CSS/JS 中做视觉和交互细节收敛。
- 现在做是为了在进入 `GS-P2-008` Modern asset pipeline 前，先把当前工作台的视觉 token、阴影、边框、选中态和卡片挂载动效统一到更稳定的基线。
- 完成后，用户会看到更低噪声的次级 UI、更柔和的多选卡片态，以及仍然保留焦点态、forced-colors 和主容器边界的本地桌面体验。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 当前架构：`docs/ARCHITECTURE.md`
- 安全边界：`docs/SECURITY.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 任务状态事实来源：`TASKS.md`

## 当前状态

- 当前行为：运行时 UI 已拆分为 `src/gitsonar/runtime_ui/css/*.py` 和 `src/gitsonar/runtime_ui/js/*.py`，仍由 Python 拼接为内嵌静态资源。
- 当前技术形态：
  - `tokens.py` 定义全局 CSS 变量与 forced-colors 覆盖。
  - `cards.py` 负责仓库卡片、更新卡片、选中态和挂载动效。
  - `controls.py`、`shell.py`、`overlays.py` 负责工作台、发现、表单、菜单、抽屉和批量 dock 视觉层。
  - `js/cards.py` 负责仓库卡片和更新卡片 HTML 字符串渲染。
- 已知痛点：
  - 次级 chip、pill、info surface 的边框噪声偏高。
  - 多选卡片的 glow 和 sheen 在 5 到 10 张选中卡片时过于抢眼。
  - 卡片挂载延迟依赖 `nth-child`，与 lazy chunk 渲染耦合。
  - 部分可复用文字节奏仍是硬编码 line-height。
- 现有约束：
  - 不引入 React、Vite、Node runtime 或外部资产。
  - 不改变 HTTP API、JSON state、schema、storage 或 Python runtime contract。
  - 不改变业务逻辑和持久化边界。
  - 保留 Windows-first、本地优先、隐私优先。

## 目标

- 主要目标：完成 token-first visual polish 和 bold de-bordering。
- 次要目标：
  - 新增 muted、shadow 和 line-height tokens。
  - 用 `--shadow-soft`、`--shadow`、`--shadow-lift` 分层替换硬编码阴影。
  - 降低次级 UI resting border 噪声，同时保留 hover、focus、active accent。
  - 柔化 `.card.selected` / `.update-card.selected`。
  - 用 `--mount-delay` 替代 `nth-child` 卡片挂载延迟。
- 成功标准：
  - 自动测试覆盖 token、CSS 动效契约、selected inset ring 和 JS renderer mount delay。
  - `GS-P2-015` 的任务、Sprint、进度和计划文件一致。
  - `GS-P2-008` 仍是下一项前端现代化任务。

## 非目标

- 不新增 React、Vite、TypeScript、npm build 或现代前端构建链。
- 不改变 API、状态模型、持久化、导入 / 导出或 Python runtime。
- 不新增外部网络请求、遥测、云 API、AI provider、字体或图片资产。
- 不重写导航、主工作流、详情抽屉或发现页结构。

## 用户影响

- 次级 badge、reason pill、meta pill、topic、repo tag chip、summary strip 和 discovery chip 的静态边框更少。
- 交互控件默认更安静，但 hover / focus / active 仍有清晰反馈。
- 多选卡片仍有 inset accent ring，但大面积 glow 和 selection sheen 更克制。
- 卡片初次挂载仍有轻微 staggered motion，并继续尊重 reduced motion。
- forced-colors 模式继续恢复可见边框。

## 隐私与显式同意

- 不涉及 AI、云 API、同步、Token 或用户数据外发。
- 不新增外部资产、字体、CDN 或 telemetry。
- 不改变 control token、loopback API 或本地 HTTP 安全边界。
- 不需要新的用户 opt-in。

## 范围

### 范围内

- `src/gitsonar/runtime_ui/css/tokens.py`
- `src/gitsonar/runtime_ui/css/cards.py`
- `src/gitsonar/runtime_ui/css/controls.py`
- `src/gitsonar/runtime_ui/css/overlays.py`
- `src/gitsonar/runtime_ui/css/shell.py`
- `src/gitsonar/runtime_ui/js/cards.py`
- `tests/test_runtime_ui_assets.py`
- `tests/test_ui_js_smoke.py`
- `TASKS.md`
- `docs/sprints/CURRENT_TOP10.md`
- `docs/progress/PROGRESS.md`

### 范围外

- `runtime/app.py`、`runtime/http.py` 和任何 Python API contract。
- JSON state、SQLite、settings、import/export。
- React/Vite modernization implementation。
- Browser automation screenshot validation。

## 架构触点

- 涉及的运行时模块：仅 `runtime_ui` 静态资源分片。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：CSS token、边框、阴影、selected state、line-height 和 card mount animation。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：无。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 新增或修改端点：无。
- 请求 / 响应结构：无变化。
- 错误行为：无变化。
- 兼容性说明：`js/cards.py` 渲染出的 card article 可带 `style="--mount-delay:...ms"`，只影响 CSS 动效。

## 执行步骤

1. 更新测试契约。
   预期结果：`tests/test_runtime_ui_assets.py` 和 `tests/test_ui_js_smoke.py` 对新 token、mount delay、selected ring 和旧 `nth-child` 移除有覆盖。
   回滚路径：删除新增测试断言。
2. 更新 CSS token 与视觉系统。
   预期结果：新增 muted、shadow、line-height tokens，并按软阴影 / 标准阴影 / lift 阴影分层使用。
   回滚路径：恢复 `tokens.py` 和相关 CSS 分片。
3. 降低次级 UI 边框噪声。
   预期结果：静态 badge / pill / chip / info surface 边框透明，交互态和 forced-colors 保持可见。
   回滚路径：恢复对应 border declarations。
4. 更新卡片 selected state 与 mount delay。
   预期结果：卡片 CSS 使用 `animation-delay:var(--mount-delay,0ms)`，JS renderer 计算 `Math.min(index, 14) * 32`。
   回滚路径：恢复旧 `nth-child` CSS 和 renderer article markup。
5. 同步任务追踪文档。
   预期结果：`GS-P2-015` 有计划、任务表、Sprint 和进度记录，且 `GS-P2-008` 保持下一项。
   回滚路径：移除 `0041` 计划和任务追踪条目。

## 风险

- 技术风险：CSS 选择器分散在多个分片，后序分片可能覆盖前序分片。
- 产品风险：去边框过度可能降低部分次级信息的容器感。
- 隐私 / 安全风险：无新增风险。
- 发布风险：视觉变化需要真实桌面窗口人工复核，自动测试只能覆盖资源契约。

## 验证

- 单元 / 资源测试：
  - `python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`
- 代码洁净检查：
  - `git diff --check`
- 手动检查建议：
  - main workspace card grid
  - batch selection dock with 5+ selected cards
  - discovery results and saved views
  - detail drawer tags/notes
  - settings and diagnostics panels
  - keyboard focus and forced-colors behavior

## 发布与回滚

- 增量发布：随当前 runtime UI 静态资源一起发布。
- 开关需求：不需要 feature flag。
- 回滚方式：回滚本任务修改的 CSS / JS / test / docs 文件即可；不涉及数据恢复。

## 文档更新

- 新增：`docs/plans/0041-runtime-ui-visual-polish.md`
- 更新：`TASKS.md`
- 更新：`docs/sprints/CURRENT_TOP10.md`
- 更新：`docs/progress/PROGRESS.md`

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 已完成 runtime UI visual polish，并插入到 `GS-P2-008` 之前；`GS-P2-008` 仍为下一项前端现代化任务。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py -q`：54 passed，227 subtests passed。
  - `git diff --check`：退出码 0。
- 手动验证：尚未执行真实浏览器 / WebView 视觉检查。
- 尚未覆盖的缺口：forced-colors、5+ selected cards、设置 / 诊断 / 详情 / 发现页视觉状态仍建议人工复核。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
