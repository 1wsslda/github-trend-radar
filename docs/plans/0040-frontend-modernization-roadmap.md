# 前端现代化分阶段路线

## 任务元信息

- 任务 ID：`GS-P2-007`
- 优先级：`P2`
- 当前状态：`[x]`
- Sprint 候选排名：用户直接指定
- 推荐 commit message：`docs(frontend): add staged modernization roadmap`

## 标题

`前端现代化总路线与文档同步`

## 摘要

- 这个任务把 GitSonar 前端从“当前不启动 React / Vite 重写”的历史评估，更新为“静态壳 + JSON API + 局部 React / Vite 组件 + 最终主工作台可迁移”的分阶段路线。
- 现在做是因为 `GS-P1-002` 等 API 边界、诊断、发现视图、详情抽屉、Update Inbox 和任务追踪已经具备继续拆前端边界的基础。
- 做完后，贡献者会知道 GitSonar 不是永远不迁移前端，而是先迁移低风险页面，再评估主工作台，且每一步都可发布、可回滚、可单独验收。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 当前架构：`docs/ARCHITECTURE.md`
- 安全边界：`docs/SECURITY.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 任务状态事实来源：`TASKS.md`

## 当前状态

- 当前行为：GitSonar 仍由 Python 运行时、本地 HTTP 服务、桌面浏览器 / WebView 外壳和内嵌 HTML/CSS/Vanilla JS 组成。
- 当前技术形态：
  - `src/gitsonar/runtime_ui/template.py` 负责 HTML 和 bootstrap payload。
  - `src/gitsonar/runtime_ui/assets.py` 聚合 CSS / JS 分片。
  - `src/gitsonar/runtime_ui/js/*.py` 和 `src/gitsonar/runtime_ui/css/*.py` 承担主要前端交互。
- 已知痛点：
  - 设置、诊断、详情、发现和主列表交互继续增长，Vanilla JS 字符串模板维护成本上升。
  - 当前 HTML 仍承载较多初始状态，前端和 Python runtime 的边界还不够清晰。
  - 前端缺少组件级构建、类型检查和浏览器级 smoke test。
- 现有约束：
  - 不做一次性 React 大重写。
  - 用户机器运行 GitSonar 不依赖 Node。
  - 运行时继续保持 Windows-first、本地优先、隐私优先。
  - 不引入 FastAPI、SQLite、AI provider、云同步或中心化账号系统。
  - 任何阶段失败都必须可以回滚到旧 UI 或明确显示本地错误。

## 目标

- 主要目标：建立完整、可执行、可回滚的前端现代化路线。
- 次要目标：
  - 把 `GS-P2-006` 的历史结论修正为“当时不启动完整重写”，不再代表永久不迁移。
  - 明确从诊断页、设置页、详情抽屉、发现页到主工作台的迁移顺序。
  - 明确 modern assets 的开发源码、构建产物、运行时复制和静态资源边界。
- 成功标准：
  - `docs/plans/0040-frontend-modernization-roadmap.md` 写清阶段、回滚、测试和安全边界。
  - `TASKS.md` 新增 `GS-P2-007` ~ `GS-P2-014`。
  - `docs/roadmap/ROADMAP.md`、`docs/ARCHITECTURE.md`、`docs/SECURITY.md`、`docs/sprints/CURRENT_TOP10.md` 和 `docs/progress/PROGRESS.md` 同步更新。
  - 后续贡献者能直接从 `GS-P2-008` 开始执行 Phase 1，而不会误判为一次性迁移。

## 非目标

- 本任务不实现 React、Vite、TypeScript 或 npm 构建链。
- 本任务不新增 `frontend/`、`modern_assets.py` 或 `modern_dist/` 代码。
- 本任务不改变用户可见 UI。
- 本任务不改变 HTTP API、状态模型、持久化事实来源或桌面壳。
- 本任务不把主工作台切到 React。
- 本任务不改变隐私、Token、代理、同步或 AI 边界。

## 用户影响

- 本轮用户可见功能无变化。
- 后续版本中，用户会先看到低风险弹层更稳定、更易扩展，再逐步看到复杂区域迁移。
- 用户机器运行 GitSonar 仍不需要 Node；构建产物会随仓库或发布产物提供。
- 任何阶段失败时，用户应继续可用旧 UI 或看到明确的本地错误，不应白屏。

## 隐私与显式同意

- 本路线本身不涉及 AI、云 API、同步、Token 或用户数据外发。
- 后续 React/Vite bundle 只能调用本地 loopback JSON API。
- `/api/*` 继续要求 loopback + runtime control token。
- control token 仍由 HTML bootstrap 注入，modern 前端不得把 token 写入日志、URL、外部请求或持久化文件。
- `/assets/modern/*` 只能作为只读 allowlist 静态资源接口，禁止路径穿越和目录枚举。

## 目标架构

最终方向：

```text
Python Runtime
  -> Local HTTP API
  -> Static HTML Shell
  -> Built frontend assets
  -> React islands / migrated React workspace
  -> Desktop browser / WebView shell
```

阶段性目录：

```text
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  src/
    shared/
      api.ts
      types.ts
      runtime.ts
      components/
    diagnostics/
    settings/
    detail/
    discovery/
    workspace/

src/gitsonar/runtime_ui/
  template.py
  assets.py
  modern_assets.py
  modern_dist/
    manifest.json
    diagnostics.js
    diagnostics.css
    settings.js
    settings.css
```

运行时产物：

```text
runtime-data/
  trending.html
  assets/
    modern/
      diagnostics.js
      diagnostics.css
      settings.js
      settings.css
```

保留的关键接口：

- `GET /api/bootstrap`
- `GET /api/repos`
- `GET /api/updates`
- `GET /api/discovery/views`
- `GET /api/diagnostics`
- `POST /api/settings`
- `POST /api/repo-annotations`

新增静态资源接口：

- `GET /assets/modern/<allowlisted-file>`

## 任务序列

| 阶段 | Task ID | 状态 | 任务 | 默认验收 |
|---|---|---:|---|---|
| Phase 0 | `GS-P2-007` | `[x]` | 前端现代化总路线与文档同步 | 总路线、任务表、路线图、架构、安全和进度日志一致。 |
| Phase 1 | `GS-P2-008` | `[ ]` | Modern asset pipeline | Vite 构建产物可复制到 runtime，缺失时旧 UI 可用。 |
| Phase 2 | `GS-P2-009` | `[ ]` | React 诊断页试点 | 诊断弹层优先 React island，失败回退 Vanilla 渲染。 |
| Phase 3 | `GS-P2-010` | `[ ]` | React 设置页试点 | 设置表单、敏感字段和保存流程在 React 中保持现有安全边界。 |
| Phase 4 | `GS-P2-011` | `[ ]` | 静态壳与 bootstrap 收敛 | HTML 只保留最小 boot flags，主数据改由 JSON API 加载。 |
| Phase 5 | `GS-P2-012` | `[ ]` | 详情抽屉迁移 | 标签、笔记、README 摘要和详情交互迁移且不丢失 `0038` 能力。 |
| Phase 6 | `GS-P2-013` | `[ ]` | 发现页迁移 | Discovery View、搜索进度、工具条和主题地图进入 React 管理。 |
| Phase 7 | `GS-P2-014` | `[ ]` | 主工作台迁移评估与切换 | 满足前置条件后，以 feature flag 评估列表、筛选和 Update Inbox 切换。 |

除 `GS-P2-007` 外，后续每个任务开始前都必须创建或更新任务级计划，写清验收、回滚、测试和推荐 commit message。

## 实施阶段

### Phase 0：文档与任务基线

目标：先把路线写入 docs，避免后续实现变成隐性大迁移。

范围：

- 新增本计划文件。
- 更新任务总表、Sprint 队列和进度日志。
- 更新路线图、架构和安全文档。
- 更新战略文档中 React/Vite 的阶段化判断。

验收：

- 当前仍保留 Vanilla JS 主工作台。
- React/Vite 只作为局部试点路线。
- 迁移顺序明确为：诊断页 -> 设置页 -> 详情抽屉 -> 发现页 -> 主工作台。
- 每一阶段必须保留 fallback 或明确回滚路径。

### Phase 1：Modern Asset Pipeline

目标：建立 React/Vite 构建链，但不改变用户可见 UI。

预计新增：

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `src/gitsonar/runtime_ui/modern_assets.py`
- `src/gitsonar/runtime_ui/modern_dist/manifest.json`

预计修改：

- `src/gitsonar/runtime/app.py`
- `src/gitsonar/runtime/http.py`
- `src/gitsonar/runtime_ui/template.py`

行为：

- `npm run build` 输出到 `src/gitsonar/runtime_ui/modern_dist/`。
- Python 启动时复制 allowlisted modern assets 到 runtime root。
- HTML 可以注入 modern CSS/JS 标签。
- 如果 modern assets 不存在，旧 UI 仍正常运行。

验证：

- modern assets 缺失不影响 `build_html()`。
- `/assets/modern/diagnostics.js` 可访问。
- `/assets/modern/../settings.json` 被拒绝。
- `python -m pytest tests/test_runtime_http.py tests/test_runtime_ui_assets.py -q`

回滚：

- 删除 `frontend/`、`modern_assets.py`、`modern_dist/` 和静态资源路由。
- 恢复 `template.py` 不注入 modern 标签。

### Phase 2：React 诊断页试点

目标：迁移最低风险的运行诊断弹层，验证 React island 方案。

预计新增：

- `frontend/src/diagnostics/main.tsx`
- `frontend/src/diagnostics/DiagnosticsApp.tsx`
- `frontend/src/shared/api.ts`
- `frontend/src/shared/types.ts`

预计修改：

- `src/gitsonar/runtime_ui/js/overlays.py`

接口：

```ts
window.GitSonarModernDiagnostics.open({
  controlToken: string
})
```

行为：

- 点击运行诊断时优先使用 React 渲染 `#diagnostics-body`。
- modern bundle 加载失败时回退到现有 Vanilla JS 诊断渲染。
- React 只调用 `/api/diagnostics`。
- 请求继续携带 `X-GitSonar-Control`。

验证：

- `npm run typecheck`
- `npm run build`
- Python asset contract 测试确认 fallback 仍存在。
- 手动打开诊断弹层，确认无白屏、无控制台语法错误。

### Phase 3：React 设置页试点

目标：迁移设置弹层，验证表单、敏感字段和保存流程。

预计新增：

- `frontend/src/settings/main.tsx`
- `frontend/src/settings/SettingsApp.tsx`

迁移范围：

- GitHub Token 输入与状态校验。
- 代理设置。
- 翻译 provider 设置。
- 开机启动。
- 保存设置。
- 退出程序按钮保留旧逻辑或通过 wrapper 调用。

保持不变：

- `POST /api/settings`
- `POST /api/settings/token-status`
- DPAPI 加密逻辑。
- 脱敏 payload。

验收：

- 设置页不再依赖大段 `innerHTML` 和手写 DOM 同步。
- 敏感字段保存、校验和脱敏展示保持现有安全边界。
- modern bundle 缺失或初始化失败时，旧设置 UI 可用。

### Phase 4：Static Shell + Bootstrap 收敛

目标：减少 Python 注入的大 payload，为主工作台迁移铺路。

预计修改：

- `src/gitsonar/runtime_ui/template.py`
- `src/gitsonar/runtime_ui/js/constants.py`
- `src/gitsonar/runtime/api_boundary.py`

行为：

- 初始 HTML 只保留 app name、control token 和 minimal boot flags。
- 主数据由前端启动后调用：
  - `/api/bootstrap`
  - `/api/repos`
  - `/api/updates`
  - `/api/discovery/views`

兼容：

- 阶段内可保留旧 `INITIAL` payload fallback。
- 如果 bootstrap 失败，显示本地服务错误，不白屏。

验收：

- HTML 不再承载大状态快照。
- 前端更接近独立应用。
- React 主工作台迁移风险下降。

### Phase 5：详情抽屉迁移

目标：迁移仓库详情、标签、笔记和 README 摘要区域。

预计新增：

- `frontend/src/detail/DetailDrawer.tsx`
- `frontend/src/detail/RepoOrganizer.tsx`

保持接口：

- `GET /api/repo-details`
- `POST /api/repo-annotations`
- `POST /api/analysis/export-markdown`

行为：

- 标签 chip、推荐标签、输入添加和笔记失焦保存继续可用。
- 保存失败显示明确状态。
- 不丢失 `docs/plans/0038-tags-notes-editor-ux.md` 已完成能力。

### Phase 6：发现页迁移

目标：迁移 Discovery View、搜索、搜索进度、结果工具条和主题地图。

预计新增：

- `frontend/src/discovery/DiscoveryView.tsx`
- `frontend/src/discovery/DiscoveryProgress.tsx`
- `frontend/src/discovery/DiscoveryClusterMap.tsx`

保持接口：

- `POST /api/discover`
- `GET /api/discovery/job`
- `POST /api/discovery/cancel`
- `POST /api/discovery/views`
- `POST /api/discovery/views/delete`
- `POST /api/discovery/clear`

行为：

- 初期继续轮询。
- SSE 只作为后续增强，不在本阶段强制切换。
- 保存视图、载入视图、删除视图、取消搜索全部保留。

### Phase 7：主工作台迁移评估与切换

目标：迁移列表、筛选、排序、批量选择和 Update Inbox。

前置条件：

- 诊断页、设置页、详情抽屉和发现页已经稳定。
- React 数据加载和 control-token 请求机制稳定。
- 至少有一组浏览器级 smoke test。
- 手动验证记录连续两轮无回退。

迁移范围：

- 主导航。
- 趋势列表。
- 我的库。
- Update Inbox。
- 批量操作 dock。
- 搜索、筛选、排序。
- 懒加载或虚拟列表。

切换策略：

- 保留 legacy workspace 入口至少一个版本。
- 添加内部 feature flag：`modern_workspace=false` 默认旧主工作台。
- 验证完成后再切为 true。
- 失败时切回旧 workspace。

## 通用验证

每个实现阶段按风险选择以下验证：

- `npm ci`
- `npm run typecheck`
- `npm run build`
- `python -m pytest -q`
- `git diff --check`
- `python src/gitsonar/__main__.py`

浏览器手动验收：

- 页面无白屏。
- 控制台无语法错误。
- 设置、诊断、详情、发现、列表和更新页核心流程可用。
- modern bundle 缺失时 fallback 或错误提示符合预期。
- 无新增外部网络请求。
- API token 错误时返回 403，且不泄露数据。

## 发布与回滚

- Phase 1 只发布构建链和静态资源边界，不改变默认 UI。
- Phase 2 到 Phase 6 使用局部 fallback；失败时恢复对应 Vanilla JS 调用路径。
- Phase 7 使用 feature flag；失败时切回 legacy workspace。
- 任一阶段都不得删除旧 UI 能力，除非计划文件写清至少一个版本的兼容期和回滚策略。

## 文档更新

本任务更新：

- `docs/plans/0040-frontend-modernization-roadmap.md`
- `docs/strategy/GITSONAR_STRATEGY.md`
- `docs/roadmap/ROADMAP.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `TASKS.md`
- `docs/sprints/CURRENT_TOP10.md`
- `docs/progress/PROGRESS.md`

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-25` | `[x]` | 已创建总路线并同步任务、路线图、架构、安全、Sprint 队列和进度日志。 |

## 验证记录

- 已运行检查：
  - `git diff --check -- TASKS.md docs/ARCHITECTURE.md docs/SECURITY.md docs/progress/PROGRESS.md docs/roadmap/ROADMAP.md docs/sprints/CURRENT_TOP10.md docs/strategy/GITSONAR_STRATEGY.md docs/plans/0040-frontend-modernization-roadmap.md`：退出码 0，仅有 LF/CRLF 警告。
  - 旧 `0039` frontend 计划路径检索：无匹配，确认没有遗留已弃用文件引用。
  - `rg -n 'GS-P2-00[7-9]|GS-P2-01[0-4]' TASKS.md docs/roadmap/ROADMAP.md docs/sprints/CURRENT_TOP10.md docs/progress/PROGRESS.md docs/plans/0040-frontend-modernization-roadmap.md`：确认任务序列可追踪。
- 手动验证：确认本任务只改文档和任务追踪，不改运行时代码。
- 尚未覆盖的缺口：Phase 1 之后的实现、npm 构建、浏览器 smoke test 和真实 UI fallback 验证需要在对应任务中完成。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
