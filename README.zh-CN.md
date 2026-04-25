# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**GitSonar 是一个 Windows 本地优先的 GitHub 开源项目情报工作台。它把“发现项目、整理线索、持续跟踪、形成判断”放到一个桌面工作流里。**

![GitSonar 主界面](assets/screenshots/trending.png)

GitSonar 不只是 GitHub Trending 查看器。它更像一个给开发者、产品人、研究者使用的开源项目雷达：先帮你发现值得看的仓库，再让你用本地状态、标签、笔记、更新收件箱、对比视图和 Markdown / AI 提示词交接，把一次性浏览变成可持续积累。

## 系统亮点

| 能力 | 你能做什么 |
|---|---|
| **趋势与关键词发现** | 查看今日 / 本周 / 本月趋势，用中英文关键词发现仓库，保存发现视图，下次一键重跑。 |
| **可解释推荐** | 在结果卡片里看到推荐原因、排序依据、本地聚类主题和轻量仓库地图，不只看 Star 数。 |
| **本地整理台** | 用 `关注 / 稍后看 / 已读 / 忽略` 四态管理候选仓库，补充标签、笔记、忽略原因，支持批量操作和导入 / 导出。 |
| **Update Inbox** | 持续跟踪关注仓库的 Push、Star / Fork、Release 变化，按已读、置顶、忽略、优先级整理更新。 |
| **详情、对比与导出** | 在详情抽屉阅读 README 摘要、Topics、License、主页信息，并做双仓库对比或导出 Markdown 摘要。 |
| **隐私优先** | 数据默认留在本机。GitHub Token 和带凭据代理 URL 使用 Windows DPAPI 本地加密；本地 API 有 loopback 和 control token 保护。 |

## 适合谁

- 经常看 GitHub Trending，但希望把好项目沉淀下来的人。
- 做技术选型、竞品观察、开源项目研究的开发者和产品人。
- 需要跟踪某批仓库更新，而不是只收藏一个链接的人。
- 使用中文关键词寻找英文开源项目，并希望保留判断过程的人。
- 想把仓库信息交给 ChatGPT / Gemini 分析，但希望先在本地筛选和整理上下文的人。

## 5 分钟上手

### 1. 下载和启动

从 [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases) 下载：

- 安装版：`GitSonarSetup.exe`
- 便携版：`GitSonar.exe`
- 校验文件：`SHA256SUMS.txt` 和 `release-manifest.json`

当前版本没有自动更新，也没有代码签名。Windows SmartScreen 可能会提示风险；请确认下载来源和 SHA256 后再运行。

### 2. 首次配置

打开右上角设置，根据需要填写：

- `GitHub Token`：长期使用、同步 GitHub Stars、提高 GitHub API 稳定性时建议配置。
- `代理地址`：你的网络无法稳定访问 GitHub 时配置。
- `刷新间隔`：控制后台刷新频率。
- `结果上限`：控制趋势和发现列表规模。
- `翻译 provider`：默认使用 Google 翻译路径；OpenAI-compatible 翻译 API 需要你显式启用并填写 Endpoint、Model 和 API Key。

不配置 Token 也可以浏览趋势和做本地整理，只是 GitHub API 稳定性、Star 同步和更新追踪能力会受限。

### 3. 发现仓库

1. 在主界面切换 `今日 / 本周 / 本月` 查看趋势榜。
2. 用搜索、语言、状态和排序控件缩小范围。
3. 打开关键词发现，输入中文或英文关键词，例如 `本地 AI 工具`、`terminal ui`、`data visualization`。
4. 查看结果里的推荐原因、聚类主题和仓库地图，判断哪些值得进入候选池。
5. 对有价值的查询保存发现视图，下次可以直接加载或重跑。

### 4. 整理候选仓库

对每个仓库做本地状态标记：

- `关注`：值得长期跟踪，会进入关注列表和更新追踪。
- `稍后看`：暂时有兴趣，但还没判断。
- `已读`：已经看过，不需要继续出现在待处理列表里。
- `忽略`：明确不关注，可以记录忽略原因，帮助后续排序去噪。

在详情抽屉里可以补充标签和笔记。比如：

- 标签：`ai-agent`、`cli`、`database`、`值得试用`
- 笔记：记录你为什么关注、风险点、适用场景、后续验证动作

状态、标签、笔记都保存在本机，也可以导出 / 导入。

### 5. 跟踪更新

进入 `Update Inbox` 查看关注仓库的变化：

- Push 活跃度变化
- Star / Fork 数变化
- 新 Release
- 本地生成的变化摘要
- 重要性解释
- 自上次查看以来的提示

你可以把更新标记为已读、置顶、忽略，或按优先级处理。它的目标不是替代 GitHub 通知，而是帮你从“我关注的一批项目里”挑出真正值得回看的变化。

### 6. 阅读、对比和形成判断

常用判断路径：

1. 打开仓库详情，先看描述、语言、Topics、License、主页、README 摘要。
2. 给候选项目加标签和笔记。
3. 选两个仓库做并排对比，快速看定位差异。
4. 导出单仓库、批量仓库或对比 Markdown 摘要。
5. 把整理好的上下文交给 ChatGPT / Gemini，或只复制提示词到你自己的工作流。

GitSonar 当前不会在应用内默认调用 AI provider。AI 相关功能是提示词交接，由你主动点击后才会打开外部目标或复制内容。

## 典型工作流

### 每日开源雷达

1. 打开今日趋势。
2. 用语言和排序筛掉无关项目。
3. 把 3 到 5 个项目标记为关注或稍后看。
4. 给重点项目加标签。
5. 晚些时候从 Update Inbox 看它们是否有新的 Release 或活跃变化。

### 技术选型候选池

1. 用关键词发现找某个方向的项目，例如 `vector database` 或 `workflow engine`。
2. 保存发现视图，保留查询条件和结果上下文。
3. 给候选项目添加标签，例如 `成熟`、`轻量`、`风险待查`。
4. 用对比视图比较两个最接近的项目。
5. 导出 Markdown 摘要进入方案文档。

### AI 辅助判断

1. 先在 GitSonar 里筛选项目，补标签和笔记。
2. 打开单仓库、批量或对比分析入口。
3. 选择 ChatGPT、Gemini 或仅复制提示词。
4. 在外部 AI 工具里继续分析，不把 GitHub Token、代理凭据或本地路径交给模型。

## 界面操作指南

### 趋势页

- `今日 / 本周 / 本月`：切换 GitHub Trending 时间范围。
- 搜索和筛选：按仓库名、描述、语言、状态快速缩小列表。
- 排序：按 Star、增长、更新时间或推荐信号查看不同优先级。
- 批量操作：对当前筛选结果批量标记、分析或导出。

### 关键词发现

- 输入中文关键词时，GitSonar 会按当前翻译设置尝试生成英文查询。
- 发现任务在后台执行，可以查看进度，也可以取消。
- 发现结果支持推荐原因、聚类主题和仓库地图。
- 常用查询可以保存成发现视图，后续加载、重跑或删除。

### 关注列表

- 关注列表是 GitSonar 的本地工作流状态，不等同于 GitHub Star。
- 配置 GitHub Token 后，标记关注时会尝试同步 GitHub Star，也可以把已有 GitHub Stars 导入本地关注列表。
- 你可以继续用标签、笔记、筛选和批量操作整理关注仓库。

### Update Inbox

- 展示关注仓库的 Push、Star / Fork、Release 变化。
- 支持已读、置顶、忽略和优先级。
- 本地摘要和重要性解释帮助你判断哪些更新值得打开。
- 这个面板适合定期清理，不需要每条更新都跳转到 GitHub。

### 详情抽屉和对比

- 详情抽屉用于阅读 README 摘要、Topics、License、主页等信息。
- 标签和笔记编辑也在详情抽屉里完成。
- 对比视图适合在两个相似仓库之间做选择。
- Markdown 导出适合进入笔记、PRD、技术方案或外部 AI 工具。

### 设置与诊断

- 设置里管理 GitHub Token、代理、刷新间隔、结果上限、翻译 provider 和开机启动。
- 诊断面板会检查运行目录、端口、代理、Token 状态、GitHub 可达性等信息。
- 诊断输出会脱敏，不应暴露明文 Token、代理凭据或本地绝对路径。

## 截图

**主界面：趋势、筛选、批量分析**

![GitSonar 主界面](assets/screenshots/trending.png)

**关注列表：本地状态整理与批量动作**

![状态管理](assets/screenshots/favorites.png)

**仓库详情：抽屉阅读与 README 摘要**

![仓库详情](assets/screenshots/detail.png)

## 当前实现边界

### AI 边界

已经实现：

- ChatGPT / Gemini 提示词交接
- 仅复制提示词
- 单仓库、批量、对比三种上下文整理

尚未实现：

- 默认内嵌 AI provider
- 应用内自动返回模型结论
- OpenAI-compatible AI 分析 provider pipeline
- 手动结构化 Insight 本地缓存工作流

OpenAI-compatible 当前只用于可选翻译 provider，不等同于内嵌 AI 分析功能。

### 存储边界

- 当前事实存储仍是本地 JSON 文件。
- SQLite 已有迁移设计和 dry-run 骨架，但尚未切换为运行时事实存储。
- 打包版数据默认在 `%LOCALAPPDATA%\GitSonar`。
- 开发态数据默认在仓库内 `runtime-data/`。
- 旧目录 `%LOCALAPPDATA%\GitHubTrendRadar` 会在首次运行时尝试合并到新目录。

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

## 安全与隐私

- GitSonar 是本地运行工具，没有项目自建 SaaS 后台。
- 本地 HTTP 服务默认绑定到 `127.0.0.1`。
- 业务、状态、诊断、导出、事件和只读数据 API 要求 loopback 与 runtime control token。
- GitHub Token 和带凭据代理 URL 使用 Windows DPAPI 本地加密保存。
- 当前可能访问 GitHub 和 Google Translate；OpenAI-compatible 翻译 API 只有在你显式启用后才会访问你配置的 Endpoint。
- ChatGPT / Gemini 入口只在你主动点击时打开外部目标或复制提示词。
- 当前没有默认云同步、默认备份上传、代码签名或自动更新。

更多细节见 [docs/SECURITY.md](docs/SECURITY.md)。

## 路线图

真实剩余项：

- **SQLite 运行时切换**：在 dry-run 骨架之后，实现导入 / 导出和受控存储切换。
- **AI provider 实施**：按 opt-in 设计实现设置、隐私预览、本地 / 云端执行路径和结果确认。
- **前端现代化**：按 `docs/plans/0040-frontend-modernization-roadmap.md` 从低风险 React island 和 modern asset pipeline 开始，不做一次性大重写。
- **加密备份 / 同步**：在同步目标、密钥管理和冲突策略明确后再启动。
- **代码签名与自动更新**：在证书、私钥保管、时间戳服务和发布策略明确后再启动。

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
