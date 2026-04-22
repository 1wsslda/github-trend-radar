# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**GitSonar 是一个 Windows 桌面 GitHub 情报台，把日常的 GitHub 浏览收束成一条持续工作流：发现 → 整理 → 跟踪 → 判断。**

![GitSonar 主界面](assets/screenshots/trending.png)

GitSonar 不是把 GitHub Trending 页面搬到桌面。它把趋势发现、关键词发现、本地状态整理、关注更新、仓库详情、双仓库对比和 ChatGPT 提示词交接放进一个桌面工作台，适合需要持续筛选和跟进 GitHub 项目的人。

## 它解决什么问题

- Trending 能帮你发现项目，但很难帮你决定哪些值得继续看。
- 浏览器标签页适合一次性看榜，不适合长期整理、持续跟踪和回头判断。
- GitSonar 把“发现后的动作”放回桌面：先标记、再跟踪、再对比、再判断。

## 核心工作流

1. **发现**
   今天 / 本周 / 本月趋势榜，加上独立的关键词发现面板。当前实现支持中英文关键词、自动扩词、保存搜索和多种排序模式。
2. **整理**
   用 `关注 / 稍后看 / 已读 / 忽略` 四态本地状态做去噪，支持搜索、筛选、排序、批量操作，以及用户状态导出 / 导入。
3. **跟踪**
   关注列表的 Push、Star / Fork、Release 变化会进入“收藏更新 / 关注更新”面板；支持从 GitHub 星标批量导入，也支持在标记关注时尝试同步 GitHub 星标。
4. **判断**
   用详情抽屉、README 摘要、双仓库并排对比和 ChatGPT 提示词，快速完成单仓库、批量或对比判断。

## 已实现的核心能力

- **趋势与发现**：今天 / 本周 / 本月趋势聚合，关键词发现，保存搜索，排序模式切换
- **整理与沉淀**：四态本地状态，批量操作，导出 / 导入用户状态
- **变化跟踪**：关注仓库的 Push、Star / Fork、Release 变化追踪与更新面板
- **仓库理解**：详情抽屉、README 摘要、Topics、License、主页等关键信息
- **对比与提示词**：双仓库对比，单仓库 / 批量 / 对比三种 ChatGPT 提示词交接
- **桌面体验**：单实例唤醒、关闭行为、开机启动、代理支持
- **本地运行**：GitHub Token 本地加密保存，旧数据目录迁移，开发态 `runtime-data/` 与打包态 `%LOCALAPPDATA%\GitSonar`

## 它适合谁

- 需要长期跟踪 GitHub 项目，而不是只看一次榜单的人
- 做技术选型、竞品观察、产品研究的开发者和产品人
- 独立开发者、开源重度用户、中文关键词检索需求较强的人
- 希望先整理候选，再集中做判断的人

## 为什么它不是普通的 Trending 查看器

- 普通 Trending viewer 主要解决“今天有什么火”；GitSonar 继续处理“哪些值得继续看、为什么值得继续看”
- 普通 Trending viewer 更像一次性浏览；GitSonar 强调桌面上的持续整理、刷新和回头判断
- 普通 Trending viewer 往往停在 GitHub Star；GitSonar 增加了本地状态、更新跟踪、详情阅读、对比和提示词工作流

## 术语说明

- **应用内的 `关注 / 收藏 / favorites`**
  当前界面和代码里还存在“关注”“收藏”“favorites”混用，它们在文档里统一指 GitSonar 的本地关注列表，是一条应用内工作流状态。
- **GitHub `Star`**
  这是 GitHub 平台上的公开动作和指标，不等同于应用内状态。配置 Token 后，GitSonar 在你把仓库标记为“关注”时会尝试同步 GitHub Star，也支持把现有 GitHub 星标批量导入到本地关注列表。

## 快速开始

### 普通用户

- GitSonar 是一个 Windows 桌面应用，当前 README 以 Windows 10 及以上为目标环境。
- 如果当前仓库已经发布版本，优先从 [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases) 下载：
  - 安装版：`GitSonarSetup.exe`
  - 便携版：`GitSonar.exe`
- `artifacts/` 是仓库内的构建输出目录，不是面向普通用户的默认下载入口。
- 当前**没有自动更新，也没有代码签名**。如果 Windows SmartScreen 拦截，请按你的环境判断后再选择是否继续运行。

首次启动后，按需配置这些项目：

- `GitHub Token`：建议长期使用时填写
- `代理地址`：网络无法稳定访问 GitHub 时填写
- `刷新间隔`
- `结果上限`

### 开发者 / 维护者

环境要求：

- Windows
- Python 3.12+

直接运行：

```powershell
python -m pip install -r requirements.txt
python src/gitsonar/__main__.py
```

构建 EXE：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

构建安装包：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_setup.ps1
```

一键打包：

```cmd
scripts\build_all_click.cmd
```

## 典型工作流

1. 在 `今天 / 本周 / 本月` 或关键词发现里找候选仓库
2. 先用 `关注 / 稍后看 / 已读 / 忽略` 做整理，不急着立刻下结论
3. 在程序运行期间，回到“收藏更新”看哪些仓库发生了 Push / Star / Release 变化
4. 打开详情或对比视图，再把单仓库 / 批量 / 对比提示词交给 ChatGPT 辅助判断

## 截图

**主界面：趋势、筛选、批量分析**

![GitSonar 主界面](assets/screenshots/trending.png)

**关注列表：本地状态整理与批量动作**

![状态管理](assets/screenshots/favorites.png)

**仓库详情：抽屉阅读与 README 摘要**

![仓库详情](assets/screenshots/detail.png)

**更新追踪面板**

当前仓库里还没有这部分的真实截图，后续补充。

## 规划中

以下内容是规划方向，不代表当前已经实现：

- **更新中心更强的研判能力**：变化摘要、优先级、降噪、“自上次查看以来”的视角
- **内嵌 AI 判断**：当前只有 ChatGPT 提示词交接，尚未提供应用内直接输出 AI 结论
- **更完整的发现与可靠性体验**：自定义发现视角、首启引导、网络诊断、更平滑的本地迁移与备份体验

## 安全、数据目录与迁移

- 打包版运行时数据默认在 `%LOCALAPPDATA%\GitSonar`
- 开发态直接运行时使用仓库内的 `runtime-data/`
- 旧目录 `%LOCALAPPDATA%\GitHubTrendRadar` 会在首次运行时尝试合并到新目录
- GitHub Token 使用 Windows DPAPI 在本地加密保存
- 当前实现除了访问 GitHub，还会访问 Google Translate 公共接口做翻译；ChatGPT 功能目前是生成 / 复制提示词并打开外部 ChatGPT，而不是内嵌 AI

更多细节见 [docs/SECURITY.md](docs/SECURITY.md)。

## 文档入口

- [docs/strategy/GITSONAR_STRATEGY.md](docs/strategy/GITSONAR_STRATEGY.md)
- [docs/roadmap/ROADMAP.md](docs/roadmap/ROADMAP.md)
- [docs/plans/PLAN_TEMPLATE.md](docs/plans/PLAN_TEMPLATE.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [CHANGELOG.md](CHANGELOG.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

本项目采用 [MIT License](LICENSE)。
