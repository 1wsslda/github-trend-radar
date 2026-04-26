# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**别再让有价值的仓库淹没在 Star 列表里。GitSonar 把 GitHub 发现变成本地可持续的研究工作流：发现项目、筛选线索、记录判断、持续跟踪变化。**

`Windows` · `本地优先` · `无需账号` · `GitHub Token 可选` · `MIT`

[下载 GitSonar](https://github.com/1wsslda/github-trend-radar/releases) · [查看安全边界](docs/SECURITY.md) · [从源码运行](#开发者运行)

![GitSonar 主界面](assets/screenshots/trending.png)

如果你经常刷 GitHub Trending、搜索同类项目、攒了一堆 Stars，却很难记住“为什么关注它、后来有没有变化、和另一个仓库比到底选谁”，GitSonar 解决的就是这段发现之后的工作流。

它不是 GitHub 客户端替代品，也不是云端 SaaS。它是一个 Windows 本地桌面工具，把趋势发现、关键词发现、本地状态、标签笔记、Update Inbox、仓库对比、Markdown 导出和 AI 提示词交接放在同一个工作台里。

## 为什么值得试

| 你遇到的问题 | GitSonar 的处理方式 |
|---|---|
| Trending 看完就忘，Star 越攒越乱 | 用 `关注 / 稍后看 / 已读 / 忽略` 把候选仓库变成可处理队列。 |
| 只看 Star 数很难判断价值 | 在结果里查看推荐原因、排序信号、本地聚类主题和轻量仓库地图。 |
| 技术选型时反复打开多个仓库 | 在详情抽屉读 README 摘要、Topics、License、主页信息，再做双仓库对比。 |
| 关注项目后不知道哪些更新重要 | 用 Update Inbox 汇总 Push、Star / Fork、Release 变化，并按已读、置顶、忽略、优先级整理。 |
| 想用 AI 辅助分析，但不想默认上传数据 | 先在本地筛选、加标签和笔记，再主动复制 Prompt 或交给 ChatGPT / Gemini。 |

## 60 秒工作流

1. 打开 `今日 / 本周 / 本月` 趋势，或用中文、英文关键词发现仓库。
2. 查看推荐原因、聚类主题和仓库地图，把值得看的项目标记为 `关注` 或 `稍后看`。
3. 在详情抽屉里补标签和笔记，记录关注原因、风险点、适用场景和后续验证动作。
4. 通过 Update Inbox 定期回看关注仓库的 Release、活跃度和 Star / Fork 变化。
5. 在两个相似项目之间做并排对比，导出 Markdown 摘要进入笔记、PRD、技术方案或外部 AI 工具。

## 适合谁

- 每天或每周都会看 GitHub Trending，但希望把好项目沉淀下来的人。
- 做技术选型、竞品观察、开源项目研究的开发者、产品人和研究者。
- 需要跟踪一批仓库的变化，而不是只收藏链接的人。
- 使用中文关键词寻找英文开源项目，并希望保留查询和判断过程的人。
- 想把仓库上下文交给 ChatGPT / Gemini 分析，但希望先在本地筛选和整理的人。

## 核心能力

### 发现信号

- 查看今日 / 本周 / 本月 GitHub Trending。
- 使用中文或英文关键词发现仓库。
- 保存发现视图，下次可以直接加载或重跑。
- 查看推荐原因、排序依据、本地聚类主题和轻量二维仓库地图。

### 整理候选池

- 用 `关注 / 稍后看 / 已读 / 忽略` 管理仓库状态。
- 给仓库添加标签、笔记和忽略原因。
- 对当前筛选结果执行批量标记、分析或导出。
- 导入 / 导出本地状态，便于备份和迁移。

### 跟踪变化

- Update Inbox 跟踪关注仓库的 Push、Star / Fork 和 Release 变化。
- 支持已读、置顶、忽略和优先级整理。
- 本地生成变化摘要、重要性解释和自上次查看以来的提示。
- 目标不是替代 GitHub 通知，而是帮你从关注列表里挑出真正值得回看的变化。

### 对比、导出和 AI 交接

- 在详情抽屉阅读 README 摘要、Topics、License 和主页信息。
- 对两个相似仓库做并排对比。
- 导出单仓库、批量仓库或对比 Markdown 摘要。
- ChatGPT / Gemini 入口只做显式 Prompt 交接，不会默认调用内嵌 AI provider。

## 截图

**发现项目：趋势、筛选、推荐原因和批量动作**

![GitSonar 主界面](assets/screenshots/trending.png)

**整理候选池：本地状态、标签、笔记和批量管理**

![状态管理](assets/screenshots/favorites.png)

**形成判断：详情抽屉、README 摘要和仓库信息**

![仓库详情](assets/screenshots/detail.png)

## 下载与校验

从 [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases) 下载：

- 安装版：`GitSonarSetup.exe`
- 便携版：`GitSonar.exe`
- 校验文件：`SHA256SUMS.txt` 和 `release-manifest.json`

当前版本没有自动更新，也没有代码签名。Windows SmartScreen 可能会提示风险；建议先确认下载来源，并用发布页提供的 SHA256 校验文件后再运行。

首次使用时可以不配置 GitHub Token。无 Token 也能浏览趋势和做本地整理；配置 Token 后，GitHub API 稳定性、GitHub Star 同步和关注仓库更新追踪会更可靠。

## 隐私与边界

- GitSonar 是本地运行工具，没有项目自建 SaaS 后台，也没有账号系统。
- 打包版数据默认保存在 `%LOCALAPPDATA%\GitSonar`；开发态数据默认在仓库内 `runtime-data/`。
- 本地 HTTP 服务默认绑定到 `127.0.0.1`，业务和只读 JSON API 要求 loopback 与 runtime control token。
- GitHub Token 和带凭据代理 URL 使用 Windows DPAPI 本地加密保存。
- 当前可能访问 GitHub 和 Google Translate；OpenAI-compatible 翻译 API 只有在你显式启用并填写 Endpoint、Model 和 API Key 后才会使用。
- ChatGPT / Gemini 入口只在你主动点击时打开外部目标或复制提示词。
- 当前没有默认云同步、默认备份上传、代码签名或自动更新。

更多细节见 [docs/SECURITY.md](docs/SECURITY.md)。

## 当前实现状态

- 事实存储仍是本地 JSON 文件；SQLite 已有迁移设计和 dry-run 骨架，但尚未切换为运行时事实存储。
- AI 相关能力当前是 Prompt 交接和 Markdown 摘要导出，不是默认内嵌 AI provider，也不会在应用内自动返回模型结论。
- 前端现代化已有路线图，会从低风险 React island 和 modern asset pipeline 开始，不做一次性大重写。
- 加密备份 / 同步、代码签名和自动更新仍在后续路线图中。

## 开发者运行

环境要求：

- Windows
- Python 3.12+

直接运行：

```powershell
python -m pip install -r requirements.txt
python src/gitsonar/__main__.py
```

构建便携 EXE：

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

生成发布校验清单：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\write_release_manifest.ps1
```

运行验证：

```powershell
python scripts\verify_runtime.py
python -m pytest -q
```

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
