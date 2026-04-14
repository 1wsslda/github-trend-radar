# GitSonar

> GitHub 情报台  
> 把 GitHub 热榜变成可追踪的项目情报流  
> Turn GitHub trending into a trackable intelligence flow.

GitSonar 不是把 GitHub Trending 简单搬到桌面，而是一套面向中文用户、同时对国际用户也足够友好的 GitHub 项目情报工作台。它把热门项目发现、状态管理、收藏更新追踪、仓库对比和 AI 分析整合到一个轻量、常驻、可托盘运行的桌面工具里，让你不只是“看到项目”，而是真正持续跟踪值得长期关注的机会。

GitSonar is not just a desktop wrapper around GitHub Trending. It is a lightweight GitHub intelligence desk for discovery, tracking, comparison, and AI-assisted understanding, built for long-running desktop use instead of one-off browsing.

## What It Solves / 它解决什么问题

Many people browse GitHub Trending, but the real cost starts after discovery:

- Which repos are worth checking today, this week, or this month?  
  今天、本周、本月，到底哪些仓库值得看。
- Which ones should be favorited, queued for later, marked as read, or ignored?  
  哪些仓库应该收藏、稍后处理、标记已读，或者直接忽略。
- What changed in the repos you already care about?  
  你已经收藏的仓库，最近到底发生了什么变化。
- What does a repo actually do, and is it worth following long term?  
  一个项目到底在做什么，值不值得长期关注。
- Which of two similar repos is a better long-term bet?  
  两个相近项目之间，谁更值得继续跟踪。

GitSonar turns those scattered actions into a repeatable desktop workflow.

## Core Value / 核心价值

- `Discover, then decide / 先发现，再判断`
- `Track, not just browse / 不只是刷榜，而是持续跟踪`
- `Desktop-first workflow / 长驻桌面的工作流`
- `Chinese-friendly understanding / 更适合中文理解`
- `AI-assisted judgment / 用 AI 加速理解与比较`

## Highlights / 核心亮点

- `Trend discovery / 趋势发现`: daily, weekly, and monthly hot repositories
- `State management / 状态管理`: favorite, later, read, ignore
- `Favorite update tracking / 收藏更新追踪`: push, star/fork, and release changes
- `Repo understanding / 仓库理解`: repo details and README summary
- `Repo comparison / 仓库对比`: compare two repositories side by side
- `AI workflows / AI 辅助`: single repo, batch, and compare analysis
- `Desktop presence / 桌面常驻`: tray, wake-up, configurable close behavior, auto start

## Who It Is For / 它适合谁

- Developers who want to follow GitHub projects over time  
  想长期跟踪 GitHub 项目的开发者
- Product, strategy, and research users doing technical scanning  
  做技术选型、竞品观察、产品研究的人
- Indie hackers and heavy open-source users  
  独立开发者和开源重度用户
- People who want a workflow, not just a ranking page  
  想把“刷榜”变成“筛选 + 跟踪 + 判断”的人

## Why It Is Not Just a Trending Viewer / 为什么它不是普通的 Trending 查看器

GitSonar does more than show projects. It helps you move through the expensive part after discovery:

- find → filter  
- mark → process  
- favorite → track  
- compare → understand  
- analyze → decide

它不是“打开网页看一下”的工具，而是一个能长期陪跑的 GitHub 情报工作台。

## Quick Start / 快速开始

### Download / 直接使用

1. Run the installer: `dist/installer/GitSonarSetup.exe`
2. Or launch the portable build: `dist/GitSonar.exe`
3. On first launch, configure what you need:
   - GitHub Token
   - Proxy
   - Refresh interval
   - Result limit
   - Close behavior

### Recommended Defaults / 推荐初始设置

- `GitHub Token`: recommended if available  
  有条件建议填写
- `Proxy`: fill in a local proxy if GitHub is unstable in your network  
  网络不稳定时填写本地代理
- `Refresh interval`: `1 hour`  
  建议 `1 小时`
- `Result limit`: `25`  
  建议 `25`
- `Close behavior`: keep running in tray  
  建议关闭主窗口时保留托盘运行

## Current Capabilities / 当前已实现能力

### 1. Trend Discovery / 趋势发现

- Today / This Week / This Month hot repositories
- Dual-source aggregation from GitHub Trending and GitHub API
- Multiple sorting modes: stars, trending, gained, forks, name, language

### 2. State Management / 状态管理

- Favorite / 收藏
- Later / 稍后看
- Read / 已读
- Ignore / 忽略
- Batch state changes for selected repos / 已选仓库支持批量改状态

### 3. Favorite Update Tracking / 收藏更新追踪

- Recent push time changes
- Star / Fork changes
- Release changes
- Dedicated updates panel for favorited repositories

### 4. Repo Understanding and Comparison / 仓库理解与比较

- Repo detail drawer / 仓库详情
- README summary / README 摘要
- Two-repo comparison / 两仓库对比

### 5. AI Assistance / AI 辅助

- Single repo analysis / 单仓库分析
- Batch analysis / 批量分析
- Comparison analysis / 对比分析
- Open ChatGPT web / desktop, or copy prompts / 打开 ChatGPT 网页版、桌面版或复制提示词

### 6. Desktop Experience / 桌面化体验

- System tray resident mode / 系统托盘常驻
- Tray wake-up / 托盘唤醒
- Configurable close behavior / 关闭行为可配置
- Auto start / 开机启动
- Proxy support / 代理支持
- Local encrypted GitHub Token storage / GitHub Token 本地加密保存

## Typical Workflow / 典型工作流

1. Discover hot repositories across daily, weekly, and monthly views.  
   在今天、本周、本月里发现值得看的项目。
2. Organize them with favorite, later, read, and ignore.  
   用收藏、稍后看、已读、忽略整理信息流。
3. Open details, read summaries, and compare similar repos.  
   看详情、读摘要、对比相近项目。
4. Send one repo, a list, or a comparison to AI for faster understanding.  
   把单仓库、列表或对比结果交给 AI 加速理解。
5. Keep tracking the repos that matter through the updates panel.  
   通过“收藏更新”持续跟踪真正重要的仓库。

## Screenshots / 截图

Coming soon.  
这里预留给真实运行截图，你可以直接替换成自己的应用界面截图。

## Roadmap / 优化方向

These are product directions, not features already shipped.  
以下内容是后续演进方向，不代表当前已经实现。

### P0

- `Embedded AI / 内嵌 AI`: support OpenAI, DeepSeek, Ollama, and OpenAI-compatible APIs inside the app instead of only jumping out to ChatGPT
- `Smarter update center / 更强的更新中心`: change levels, one-line summaries, filters for release / re-activation / star spikes, repo mute, and “since last viewed”
- `First-run onboarding / 首启向导`: connectivity checks, proxy detection, optional token, recommended defaults, and explicit close behavior choice
- `System notifications / 系统通知`: release alerts, rapid star growth, re-activated repos, important release reminders
- `Navigation cleanup / 导航优化`: clearer separation between discovery, lists, and updates

### P1

- `Global shortcuts / 全局快捷键`
- `Network diagnostics / 网络体验优化`
- `More product-like README and release presentation / 更完整的产品化门面`

### P2

- `Data migration and backup / 数据迁移与备份`
- `Auto update / 自动更新`
- `Custom subscriptions / 自定义订阅与提醒策略`

## Promo Copy / 宣传文案

### One-liner / 一句话版

**Turn GitHub trending into your project intelligence system.**  
**把 GitHub 热榜，升级成你的项目情报系统。**

### Short Repo Description / 仓库简介版

**A Chinese-friendly GitHub intelligence desk for trend discovery, repo tracking, comparison, and AI-assisted analysis.**  
**一个面向中文用户的 GitHub 情报台，集趋势发现、状态管理、收藏更新追踪、仓库对比和 AI 分析于一体。**

### Release / Social Copy / 发布页短版

GitSonar is a desktop GitHub intelligence desk that helps you discover, track, compare, and understand repositories in one long-running workflow.

GitSonar 是一个常驻桌面的 GitHub 情报台，把项目发现、收藏管理、更新追踪、仓库对比和 AI 分析整合进同一套工作流里。

## Naming / 命名

- Brand: `GitSonar`
- Chinese name: `GitHub 情报台`
- Tagline: `Turn GitHub trending into a trackable intelligence flow.`

Default runtime data now lives in:

- `%LOCALAPPDATA%\GitSonar`

If an older installation exists, GitSonar will try to merge data from:

- `%LOCALAPPDATA%\GitHubTrendRadar`

这样旧版本的配置、状态和缓存可以尽量平滑迁移到新目录。

## License / 许可证

This project is released under the [MIT License](LICENSE).  
本项目采用 [MIT License](LICENSE)。

## Documentation / 文档

Detailed docs remain in the `docs` directory:

- [docs/BUILD.md](docs/BUILD.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/FAQ.md](docs/FAQ.md)
- [docs/SECURITY.md](docs/SECURITY.md)

These documents are currently Chinese-first.  
这些文档目前仍以中文为主。
