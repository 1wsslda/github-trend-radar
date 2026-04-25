# 详情抽屉 README 滚动卡顿修复

## 任务元信息

- 任务 ID：`GS-P1-021`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：用户直接指定
- 推荐 commit message：`perf(ui): reduce detail drawer readme scroll jank`

## 标题

`详情抽屉 README 预览与展开`

## 摘要

- 主列表 700 条离线压力滚动没有 long task，详情抽屉掉帧更集中在超长 README 摘要作为单个大文本块渲染。
- 本任务按用户已选择的“预览加展开”方案处理：默认只渲染 README 摘要前 `12000` 字，长内容提供“展开全文 / 收起预览”。
- 复制 Markdown 摘要仍使用完整详情内容，不受详情抽屉预览影响。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 当前架构：`docs/ARCHITECTURE.md`
- 安全边界：`docs/SECURITY.md`
- 对应能力：P1 前端体验稳定性与详情阅读性能优化。

## 当前状态

- 当前行为：`renderCurrentDetailPanel()` 会把 `detail.readme_summary || detail.readme_summary_raw` 直接渲染进一个 `.readme-block`。
- 当前技术形态：详情抽屉仍是 `runtime_ui` 中的 Vanilla JS 字符串模板；README 详情来自现有 `/api/repo-details` 和 detail cache。
- 已知痛点：超长 README 摘要会形成单个巨大文本节点，打开详情和在抽屉内滚动时容易造成明显掉帧。
- 现有约束：不能改 HTTP API、GitHub detail cache、JSON state、导入导出格式或桌面壳。

## 目标

- 默认只渲染长 README 摘要前 `12000` 字。
- 长内容显示隐藏字符数量，并提供“展开全文 / 收起预览”。
- 短 README 保持原样，不显示展开控件。
- 展开状态只保存在当前前端会话，不写入 JSON state。
- 打开新详情时重置 `#detail-body.scrollTop = 0`。
- 复制 Markdown 摘要继续使用完整 detail 内容。

## 非目标

- 不修改后端 API。
- 不修改 detail cache、JSON state、导入 / 导出格式。
- 不引入 React / Vite、FastAPI、SQLite、AI provider、云 API 或同步能力。
- 不重写详情抽屉导航结构或做 Tab 化。

## 用户影响

- 超长 README 的详情抽屉默认打开和滚动更轻。
- 用户需要阅读全文时可手动展开，展开后仍能收起回到预览。
- 复制 Markdown 摘要、标签、笔记、打开 GitHub 等现有动作保持不变。

## 隐私与显式同意

- 不涉及 AI、云 API、同步、Token 或用户数据外发。
- 不新增网络请求，不新增 telemetry。
- 不需要新增 opt-in。

## 范围

### 范围内

- `src/gitsonar/runtime_ui/js/constants.py`
- `src/gitsonar/runtime_ui/js/overlays.py`
- `tests/test_runtime_ui_assets.py`
- `tests/test_ui_js_smoke.py`
- `TASKS.md`
- `docs/sprints/CURRENT_TOP10.md`
- `docs/progress/PROGRESS.md`

### 范围外

- `src/gitsonar/runtime/http.py`
- `src/gitsonar/runtime/detail_cache.py`
- `src/gitsonar/runtime_github/`
- `src/gitsonar/runtime/state*.py`
- `docs/roadmap/ROADMAP.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`

## 架构触点

- 涉及的运行时模块：`runtime_ui`。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：详情抽屉 README 摘要改为预览 helper，并新增会话内展开状态。
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
- 兼容性说明：README 展开状态只存在于当前浏览器会话的 JS `Set`，刷新页面后恢复默认预览。

## 执行步骤

1. 新增 RED 测试。
   预期结果：当前详情抽屉仍直接渲染完整 README，缺少预览 helper、展开状态和滚动重置，测试失败。
   回滚路径：删除新增测试。
2. 实现 README 预览 helper。
   预期结果：长 README 默认截断为 `12000` 字，短 README 不显示展开控件。
   回滚路径：恢复 `renderCurrentDetailPanel()` 中原始 README 区块。
3. 实现展开 / 收起与滚动控制。
   预期结果：展开状态保存在会话内，切换后尽量保留阅读位置；打开新详情时抽屉滚动归零。
   回滚路径：删除 `detailReadmeExpandedUrls`、toggle helper 和滚动重置。
4. 确认复制 Markdown 摘要仍使用完整 detail 内容。
   预期结果：`copyRepoMarkdownSummary()` 和 `buildRepoMarkdownSummary()` 不引用预览阈值。
   回滚路径：恢复原有摘要构建路径。
5. 同步任务追踪文档并运行验证。
   预期结果：计划、任务表、Sprint 队列和进度日志一致。
   回滚路径：恢复文档记录为任务未完成。

## 风险

- 技术风险：Vanilla JS 模板字符串较长，需通过 asset/smoke/contract 测试约束函数名和关键行为。
- 产品风险：用户展开完整 README 后仍可能遇到长文本滚动成本；本任务默认降低首次打开和默认阅读成本。
- 隐私 / 安全风险：无新增外发边界。
- 发布风险：低，仅影响详情抽屉局部渲染。

## 验证

- RED：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py -q`，新增 README 合约在旧实现上失败。
- GREEN：
  - `python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py -q`
  - `python -m pytest -q`
  - `git diff --check`
- 手动验证：
  - 打开详情抽屉滚动长 README，确认默认预览不卡顿。
  - 点击展开全文后确认完整内容可读。
  - 验证标签、笔记、复制摘要、打开 GitHub 不回退。

## 发布与回滚

- 增量发布：随普通 UI 资源发布。
- 开关或受控状态：不需要。
- 失败恢复：回滚本任务涉及的 JS/CSS/测试和文档文件即可；用户数据不受影响。

## 文档更新

- 需要更新：`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。
- 不需要更新：`ROADMAP.md`、`ARCHITECTURE.md`、`SECURITY.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 已完成 README 预览 helper、展开/收起、滚动重置、测试和任务追踪更新。 |
| `2026-04-25` | `[~]` | 已创建计划并实现 README 预览 helper；等待全量验证。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py -q`，新增 README 预览契约在旧实现上失败。
  - GREEN targeted：`python -m pytest tests/test_runtime_ui_assets.py tests/test_ui_js_smoke.py tests/test_runtime_ui_js_contract.py -q`，61 passed，257 subtests passed。
  - 全量：`python -m pytest -q`，223 passed，284 subtests passed。
  - 静态：`git diff --check`，退出码 0，仅有 LF/CRLF 警告。
- 手动验证：尚未启动桌面壳逐项验证。
- 尚未覆盖的缺口：真实浏览器 Performance panel 采样需要手动执行。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
