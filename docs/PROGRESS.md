# GitSonar 进度文档

更新时间：2026-04-15

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
- [x] ChatGPT 快速分析入口（`/api/chatgpt/open`）
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
| GET | `/api/export` | 导出用户状态 |
| POST | `/api/state` | 更新仓库标记状态 |
| POST | `/api/settings` | 保存设置 |
| POST | `/api/refresh` | 手动触发刷新 |
| POST | `/api/chatgpt/open` | 打开 ChatGPT 分析 |
| POST | `/api/open-external` | 在外部浏览器打开链接 |
| POST | `/api/favorite-updates/clear` | 清空收藏更新记录 |
| POST | `/api/window/open` | 唤醒窗口 |
| POST | `/api/window/hide` | 隐藏窗口 |
| POST | `/api/window/exit` | 退出应用 |

---

## 下一步功能规划

优先级从高到低。每条标注了切入模块。

### P0 — 核心体验补全

**1. 用户状态导入**  
当前有导出（`/api/export`）但没有导入。换机或备份恢复时用户数据丢失。  
切入：`runtime_http.py` 新增 `POST /api/import`，`app_runtime.py` 处理合并逻辑。

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
