# Security

## 本地优先架构

GitSonar 是一个本地运行的 Windows 桌面工具。

当前实现下：

- Python 运行时、本地 HTTP 服务、桌面壳和系统托盘都在本机运行
- 打包版运行时数据默认位于 `%LOCALAPPDATA%\GitSonar`
- 直接从仓库运行时，开发态数据位于 `runtime-data/`
- 没有账号系统、没有云同步、没有项目自建的 SaaS 后台

本地控制服务默认绑定到 `127.0.0.1`，变更状态、保存设置、导入数据等操作只允许回环地址访问。

## GitHub Token

GitHub Token 的作用主要是：

- 提高 GitHub API 请求稳定性
- 降低限流影响
- 让 GitHub 星标同步和关注更新追踪更可靠

当前实现里：

- Token 保存在本地 `settings.json`
- 保存前会通过 Windows DPAPI 加密
- 加密和解密依赖当前 Windows 用户环境
- Token 只用于 GitHub 相关请求，不会被上传到项目自建后台

## 当前实现会连接哪些外部服务

GitSonar 当前可能访问这些外部网络目标：

- **GitHub Trending 页面与 GitHub API**
  用于趋势聚合、仓库详情、关注更新追踪、GitHub 星标同步和星标导入。
- **Google Translate 公共接口**
  代码当前会访问 `https://translate.googleapis.com/translate_a/single`，用于：
  - 把英文仓库描述和 README 摘要翻译成中文
  - 把中文关键词发现查询翻译成英文
- **本机 Ollama 类翻译服务**
  只有在你主动把翻译方式切换为“本机 Ollama 模型”并填写模型名时才会使用。
  本地翻译地址只允许 `127.0.0.1`、`localhost` 或 `::1`，用于避免把翻译内容误发到远端服务。
  如果未填写模型名或本机服务不可用，应用会保守返回原文，不会自动回退到 Google Translate。
- **ChatGPT**
  只有在你主动点击分析入口时才会触发。当前实现是生成或复制提示词，并打开 ChatGPT 网页版或桌面版；应用本身并不会直接调用自定义 LLM API，也不会在应用内返回内嵌 AI 结果。

如果你配置了代理，GitHub 和翻译请求会按你的本地代理设置转发。

## 本地存储

冻结版运行时数据默认位于：

```text
%LOCALAPPDATA%\GitSonar
```

开发态直接运行时，仓库内使用：

```text
runtime-data/
```

常见文件包括：

- `settings.json`
- `user_state.json`
- `discovery_state.json`
- `repo_details_cache.json`
- `status.json`
- `runtime_state.json`
- `data/latest.json`

这些文件都是本地运行状态，不应当被当作仓库内容提交或外发。

## 旧数据迁移

如果检测到旧目录 `%LOCALAPPDATA%\GitHubTrendRadar`，新版本会在首次运行时尝试把其中尚未迁入的数据合并到新的 `%LOCALAPPDATA%\GitSonar` 目录。

迁移目标主要包括：

- 用户设置
- 已保存状态
- 缓存数据
- 运行时状态文件

## 代理使用与边界

GitSonar 本身：

- 不提供 VPN
- 不提供翻墙能力
- 不提供加速能力

它只会使用：

- 你当前系统可访问的网络环境
- 你在设置里主动填写的代理地址
- 自动探测到的本地常见代理端口（如果你没有显式填写代理）

需要注意的是：

- 代理地址仍保存在本地 `settings.json`
- 如果代理 URL 含用户名 / 密码，新版本保存设置时会像 GitHub Token 一样用 Windows DPAPI 加密整条代理 URL
- 旧版本留下的明文代理配置仍可读取，并会在下一次保存设置时迁移到新的加密存储方式

## 风险提示

使用时仍建议注意：

- 不要分享高权限 GitHub Token
- 不要把包含本地设置、代理凭据和用户状态的运行目录直接打包外传
- 不要把 `runtime-data/`、`artifacts/`、本地缓存和导出数据误提交到仓库
- 如果截图里含有私有仓库、代理地址或敏感目录，也不要直接公开

根目录 `.gitignore` 已默认忽略常见运行数据和构建产物。
