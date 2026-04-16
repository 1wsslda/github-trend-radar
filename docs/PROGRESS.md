# GitSonar 进度文档

更新时间：2026-04-16

---

## 项目定位

GitSonar 是一个面向中文开发者的 GitHub 情报桌面工作台。  
目标用户：日常需要扫描 GitHub、发现、过滤、跟踪和分析项目的开发者、产品人和独立构建者。  
定位不是"桌面版 Trending 页面"，而是长期常驻的本地情报台。

设计基调：Readwise 式的编辑沉浸阅读台，暖色暗调、双语排版、低噪控件、右侧抽屉展开。

---

## 技术架构

```
GitHub Trending 页面 + GitHub API
        ↓
   Python Runtime (app_runtime.py)
        ↓
   Local HTTP Server (runtime_http.py)
        ↓
   Desktop Shell Window (runtime_shell.py)
        ↓
   System Tray
```

| 模块 | 职责 |
|---|---|
| `app_runtime.py` (1095 行) | 编排核心：配置、状态、刷新调度、单实例、HTML 生成 |
| `runtime_github.py` | 数据层：Trending 抓取、API 请求、详情、收藏追踪 |
| `runtime_http.py` | HTTP API 层：前端服务、状态变更接口 |
| `runtime_shell.py` | 桌面壳：托盘、窗口隐藏/唤醒、关闭行为 |
| `runtime_ui.py` | 前端模板层：HTML/CSS/JS，列表、详情抽屉、对比抽屉 |
| `runtime_utils.py` | 工具层：文件读写、DPAPI 加密、代理检测、文本处理 |

**入口：** `src/GitSonar.pyw` → `src/gitsonar/__main__.py`  
**打包：** Inno Setup (`packaging/GitSonar.iss`)  
**数据目录：** `%LOCALAPPDATA%\GitSonar`

---

## 已完成功能

### 数据层
- [x] GitHub Trending 抓取（日 / 周 / 月 三个周期）
- [x] GitHub API 仓库详情获取（含 README、语言、License、Topics）
- [x] Star 增长量计算（与上次快照对比）
- [x] 收藏仓库更新追踪：Star 变化、Release 发布（分层轮询策略）
- [x] 中文描述翻译（带缓存）

### 用户状态
- [x] 收藏 / 已读 / 忽略 三态标记
- [x] 用户状态持久化（`user_state.json`）
- [x] 快照持久化（`snapshot.json`）
- [x] 用户状态导出（`/api/export`）
- [x] 旧版数据目录自动迁移（GitHubTrendRadar → GitSonar）

### 桌面 UI
- [x] 卡片列表，支持状态分段过滤（全部 / 收藏 / 已读 / 未读）
- [x] 多维排序 + 更多排序菜单
- [x] 仓库详情右侧抽屉
- [x] 仓库对比抽屉
- [x] 拆分式分析操作（Analyze 按钮组）
- [x] 浮动批量操作 Dock
- [x] 多 AI 分析入口（`/api/chatgpt/open`）：支持 ChatGPT 网页版、桌面版、Gemini 网页版，可多选同时发送
- [x] 在外部浏览器打开仓库（`/api/open-external`）

### 系统集成
- [x] 系统托盘常驻（隐藏 / 唤醒 / 退出）
- [x] 单实例控制（已有实例时唤醒前台）
- [x] Windows 开机自启（VBS 启动脚本）
- [x] 后台自动刷新（可配置间隔）
- [x] DPAPI 加密存储 Token 和代理密码
- [x] 代理配置与自动检测

### 设置
- [x] GitHub Token 配置
- [x] 刷新间隔
- [x] 代理设置
- [x] 关闭行为（最小化到托盘 / 退出）
- [x] 开机自启开关

### 工程基础设施
- [x] 仓库改名（GitHubTrendRadar → GitSonar）
- [x] 双语 README（EN + zh-CN）
- [x] 结构化目录（`src/` `scripts/` `docs/` `packaging/` `artifacts/`）
- [x] CHANGELOG、CONTRIBUTING、issue 模板、RELEASE_CHECKLIST、RELEASE_NOTES_TEMPLATE
- [x] 架构文档、FAQ、BUILD、SECURITY、MAINTENANCE 文档
- [x] Karpathy 编码规范（`CLAUDE.md` + `.claude/skills/karpathy-guidelines`）

---

## HTTP API 现状

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/settings` | 读取设置 |
| GET | `/api/status` | 刷新状态 |
| GET | `/api/repo-details` | 仓库详情 |
| GET | `/api/discovery` | 读取关键词发现状态 |
| GET | `/api/discovery/job` | 轮询关键词发现任务进度 |
| GET | `/api/export` | 导出用户状态 |
| POST | `/api/state` | 更新仓库标记状态 |
| POST | `/api/import` | 导入用户状态（合并 / 覆盖） |
| POST | `/api/settings` | 保存设置 |
| POST | `/api/refresh` | 手动触发刷新 |
| POST | `/api/chatgpt/open` | 打开 ChatGPT 分析 |
| POST | `/api/open-external` | 在外部浏览器打开链接 |
| POST | `/api/favorite-updates/clear` | 清空收藏更新记录 |
| POST | `/api/discover` | 执行关键词发现 |
| POST | `/api/discovery/run-saved` | 运行已保存搜索 |
| POST | `/api/discovery/cancel` | 取消关键词发现任务 |
| POST | `/api/discovery/delete` | 删除已保存搜索 |
| POST | `/api/discovery/clear` | 清空本次关键词发现结果 |
| POST | `/api/window/open` | 唤醒窗口 |
| POST | `/api/window/hide` | 隐藏窗口 |
| POST | `/api/window/exit` | 退出应用 |

---

## 下一步功能规划

优先级从高到低。每条标注了切入模块。

### P0 — 核心体验补全

**1. ~~用户状态导入~~ ✅ 已完成**  
已支持从导出 JSON 导入用户状态，并提供“合并导入 / 覆盖导入”两种模式。  
切入：`runtime_http.py` 新增 `POST /api/import`，`app_runtime.py` 处理合并逻辑，`runtime_ui.py` 新增导入入口。

**2. ~~收藏时同步 GitHub 星标~~ ✅ 已完成**
**3. ~~从 GitHub 同步全部星标~~ ✅ 已完成**

**4. 收藏更新角标 / 通知**  
`track_favorite_updates()` 已在后台运行，但更新结果在 UI 中的曝光方式需要打磨。  
明确：卡片上 Release 或 Star 变化的角标样式，以及托盘图标徽章。  
切入：`runtime_ui.py`（卡片模板），`runtime_shell.py`（托盘徽章）。

**3. 搜索 / 过滤栏**  
当前只有状态分段过滤，没有关键词搜索。数据量大时找具体项目很慢。  
切入：`runtime_ui.py` 前端过滤（本地 JS 即可，无需后端），不需要改 Python。

### P1 — 分析与 AI 集成

**4. AI 分析抽屉**  
ChatGPT 入口目前是直接打开外部浏览器。可以在详情抽屉内嵌入 AI 分析结果（调用本地或远端 LLM API，结果缓存在本地）。  
切入：`runtime_http.py` 新增 `POST /api/analyze`，`runtime_ui.py` 分析标签页。

**5. 自定义 AI Prompt 模板**  
当前 ChatGPT Prompt 是固定模板。允许用户编辑 Prompt 模板，适配不同分析场景。  
切入：`app_runtime.py`（设置扩展），`runtime_ui.py`（设置面板）。

### P2 — 数据与发现

**6. 自定义追踪列表（非 Trending 来源）**  
用户可以直接输入 `owner/repo` 加入追踪，不依赖 Trending 出现。  
切入：`runtime_github.py` 扩展 `fetch_all()`，`runtime_http.py` 新增 `POST /api/watch`。

**7. 历史趋势图**  
展示某仓库在多次快照中的 Star 增长曲线。快照数据已经有了，差的是 UI 可视化层。  
切入：`runtime_ui.py` 详情抽屉新增图表（Chart.js 或 D3，前端引入即可）。

**8. 标签 / 分组管理**  
允许用户给收藏仓库打自定义标签，支持按标签分组浏览。  
切入：`app_runtime.py`（用户状态结构扩展），`runtime_ui.py`（标签 UI）。

### P3 — 工程质量

**9. 自动化测试**  
当前无测试套件，所有验证依赖手动运行。  
建议从覆盖 `app_runtime.py` 中的纯函数开始（`normalize_repo`、`normalize_settings`、`export_user_state` 等），用 `pytest`。

**10. `app_runtime.py` 拆分**  
当前 1095 行，承担了过多职责。可以把翻译、用户状态、启动管理各自独立成文件，降低每次改动的风险半径。  
节奏：不要一次性重构，每次新功能开发时顺手把对应片段提取出去。

---

## 当前版本状态

| 项 | 值 |
|---|---|
| 当前版本 | v1.0.0（2026-04-14 发布） |
| 主线分支 | `main` |
| 待发版内容 | UI 优化、公开仓库基础设施（见 `CHANGELOG.md` Unreleased 区块） |
| 下一个版本号 | `v1.0.1` |

发版前执行 `docs/RELEASE_CHECKLIST.md`，上传安装包和便携版，用 `docs/RELEASE_NOTES_TEMPLATE.md` 填写 Release 正文。

---

## In Progress: Keyword Discovery Panel

更新时间：2026-04-15

### Goal

新增一个独立的“关键词发现”面板，让用户输入中文或英文关键词后，自动抓取相关热门 GitHub 仓库，按综合分排序，并给出推荐原因，供用户自行挑选和收藏。

### Confirmed Scope

- 支持单词、短语、多关键词输入
- 支持中文和英文查询
- 自动扩展相关词，不只做精确匹配
- 使用 5 个维度做综合打分
- 结果同时返回推荐原因
- 搜索可以选择保存，也可以只跑一次
- 默认不过滤用户已有收藏/已读/忽略
- 以独立面板呈现，不复用现有 Trending 数据面板

### Planned Scoring Dimensions

1. 查询词命中度：仓库名、描述、README 摘要、Topics
2. 自动扩词命中度：是否命中自动扩展出的相关词
3. 热度：Stars 规模
4. 活跃度：最近 Push / Update 时间
5. 趋势信号：是否出现在当前 Trending / 本地快照中

### Implementation Stages

#### Stage 1: Backend Discovery Foundation

- [x] 新增 discovery state 持久化文件
- [x] 扩展仓库标准结构，支持 discovery 评分与解释字段
- [x] 实现关键词搜索、相关词扩展、去重与基础打分
- [x] 增加手动触发的 discovery HTTP 接口

#### Stage 2: Discovery UI

- [x] 新增 Discover 独立面板
- [x] 增加关键词输入、语言、结果数、自动扩词、保存搜索等控件
- [x] 展示 Top 5 推荐和完整候选列表
- [x] 展示命中词、综合分、推荐原因

#### Stage 3: Saved Queries

- [x] 支持保存搜索条件
- [x] 支持重跑已保存搜索
- [x] 支持删除已保存搜索
- [x] 页面刷新后保留最近一次 discovery 结果和已保存搜索

#### Stage 4: Hardening

- [x] 查询结果缓存，避免短时间重复打 GitHub API
- [x] 无 Token 时的降级提示
- [ ] 手动回归验证：中英文关键词、保存/不保存、收藏联动、详情面板联动

#### Stage 5: Ranking Profiles & Tests

- [x] 为关键词发现增加可切换的排名模式：偏热门 / 偏新项目 / 偏工程可用 / 偏趋势
- [x] 将 ranking profile 纳入 discovery query、已保存搜索和 job 状态
- [x] 为 discovery 搜索参数生成、打分和 ETA 行为补自动化测试

### Completed This Round

#### 2026-04-16 - 关键词发现 Job 化与 ETA
- [x] 将关键词发现从同步阻塞接口改成 job 模式
- [x] 新增分阶段状态：`queued / initial_search / initial_results / seed_details / expansion_search / rescoring / completed`
- [x] 新增首轮结果预览，首轮返回后即可先展示候选仓库
- [x] 新增完整耗时预估、剩余时间估算和阶段文案
- [x] 新增取消 discovery 任务能力
- [x] 新增 discovery 任务轮询接口与前端恢复轮询能力
- [x] 下调详情补全预算，减少 discovery 默认详情抓取成本
- [x] GitHub Token 401 时自动降级为匿名请求，避免 discovery 直接失败

#### 2026-04-16 - 多 AI 分析目标 + 提示词优化

- [x] 分析目标从单选改为多选：用户可同时勾选 ChatGPT 网页版、桌面版、Gemini 网页版
- [x] 新增 Gemini 网页版支持（`runtime_shell.py` 新增 `gemini_url()`，`open_chatgpt_target` 扩展 `gemini_web` 分支）
- [x] `aiTarget` 单字符串升级为 `aiTargets: Set`，localStorage 改存 JSON 数组，兼容旧版单值格式
- [x] 菜单改为 checkbox 语义（`menu-item--check`）：选中项显示 ✓，支持多选，`copy` 独占互斥
- [x] 按钮标签动态更新：单选显示 AI 名称，双选拼接"A + B"，多选显示"N 个 AI"
- [x] 发送逻辑升级：按选中 targets 顺序依次打开，每组提示词间加间隔，错误时显示具体 AI 名称
- [x] 单仓库提示词升级：资深技术总监角色 + 6 节结构化输出（一句话解释 / 核心价值 / 坑和局限 / 具体场景 / 竞品对比 / 决策建议）
- [x] 批量提示词升级：资深架构师角色 + 4 节精简输出（一句话 / 亮点 / 风险 / 决策建议）

#### Next Up
- [ ] discovery 模块继续拆分，降低 `runtime_github.py` / `runtime_ui.py` 复杂度
- [ ] 补更多 discovery 回归测试：真实 API 降级、warnings、cancel、saved query 轮询流程

#### 2026-04-16 - 排名模式与自动化测试
- [x] 关键词发现面板新增排序模式下拉：综合平衡 / 偏热门 / 偏新项目 / 偏工程可用 / 偏趋势
- [x] 排序模式写入 discovery query、本地草稿、已保存搜索、job 状态与最终结果元数据
- [x] 结果面板与已保存搜索展示当前排序模式，便于判断这次 discovery 的排序倾向
- [x] `runtime_github.py` 暴露 discovery 评分 helper，便于独立测试不同 ranking profile
- [x] 新增 `tests/test_discovery_profiles.py`
- [x] 覆盖 discovery query 归一化、query id、ETA 估算、ranking profile 排序差异与 profile-specific signal
- [x] 本轮验证通过：
  `python -m py_compile src/gitsonar/app_runtime.py src/gitsonar/runtime_github.py src/gitsonar/runtime_http.py src/gitsonar/runtime_ui.py tests/test_discovery_profiles.py`
  `python -m unittest discover -s tests`
  `node -e "new Function(fs.readFileSync('artifacts/_runtime_ui_script.js','utf8'))"`

#### 2026-04-16 - 关键词发现交互补强
- [x] 给关键词发现增加显式“发现中”加载状态
- [x] 发现执行期间禁用输入与重复触发按钮，避免误以为点击无效
- [x] 在面板内解释 discovery 会依次执行首轮搜索、详情补全、扩词搜索和综合打分
- [x] 完成后提示本次发现的大致耗时
- [x] 已保存搜索重跑时也复用同样的加载反馈
#### 2026-04-15 - 关键词发现面板

- [x] 新增独立的“关键词发现”面板，不复用现有 Trending 视图
- [x] 支持中英文关键词输入
- [x] 支持自动扩展相关词
- [x] 支持 Top 5 推荐 + 完整候选列表
- [x] 支持展示综合分、相关度、热度、命中词、推荐原因
- [x] 支持保存搜索、重跑已保存搜索、删除已保存搜索
- [x] 新增 discovery state 持久化
- [x] 新增 discovery 接口：
  `GET /api/discovery`
  `POST /api/discover`
  `POST /api/discovery/run-saved`
  `POST /api/discovery/delete`
  `POST /api/discovery/clear`
- [x] 增加 GitHub API 限流场景下的缓存和降级处理

#### 2026-04-15 — 用户状态导入

- [x] 支持从导出 JSON 恢复用户状态
- [x] 支持“合并导入”与“覆盖导入”两种模式
- [x] 前端“更多”菜单新增导入入口
- [x] 导入后自动刷新当前界面状态
- [x] 导入时对仓库记录、收藏监控、收藏更新做清洗和去重
- [x] 新增接口：
  `POST /api/import`

### Current Build Order

1. 先完成 discovery state 和后端 API
2. 再把搜索扩词和评分接通
3. 然后实现独立面板和保存搜索 UI
4. 最后做缓存、降级提示和回归检查
