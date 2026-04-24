# Security

## 本地优先架构

GitSonar 是一个本地运行的 Windows 桌面工具。

当前实现下：

- Python 运行时、本地 HTTP 服务、桌面壳和系统托盘都在本机运行。
- 打包版运行时数据默认位于 `%LOCALAPPDATA%\GitSonar`。
- 直接从仓库运行时，开发态数据位于 `runtime-data/`。
- 没有账号系统、没有云同步、没有项目自建的 SaaS 后台。
- AI 仍是 prompt handoff + 手动保存结构化 Insight artifact，不是默认内嵌 provider。

默认原则：

- local-first；
- privacy-first；
- 任何 AI、云 API、同步、Token 或用户数据外发都必须显式 opt-in；
- 用户数据外发前必须能被用户理解和确认。

## 本地 API 边界

本地 HTTP 服务默认绑定到 `127.0.0.1`。变更状态、保存设置、导入数据、刷新、发现、导出、打开外部链接、窗口控制和 GitHub star sync 等操作只允许 loopback 访问，并要求 runtime control token。

### 当前未强制 control token 的只读端点

以下端点当前用于前端读取和兼容路径，payload 必须保持脱敏：

- `GET /api/bootstrap`
- `GET /api/repos`
- `GET /api/updates`
- `GET /api/discovery/views`
- `GET /api/settings`
- `GET /api/status`
- `GET /api/discovery`
- `GET /api/discovery/job`

这些只读端点仍需在 `GS-P1-013` 中评估是否收紧 control-token 边界，并设计兼容迁移，避免直接破坏当前前端加载路径。

### 当前要求 loopback + control token 的端点

以下端点已经要求 loopback 和 runtime control token：

- `GET /api/ai-artifacts`
- `GET /api/jobs`
- `GET /api/events`
- `GET /api/events/stream`
- `GET /api/repo-details`
- `GET /api/diagnostics`
- `GET /api/export`
- `POST /api/state`
- `POST /api/state/batch`
- `POST /api/repo-annotations`
- `POST /api/favorite-updates/state`
- `POST /api/import`
- `POST /api/settings`
- `POST /api/settings/token-status`
- `POST /api/refresh`
- `POST /api/chatgpt/open`
- `POST /api/analysis/export-markdown`
- `POST /api/open-external`
- `POST /api/favorite-updates/clear`
- `POST /api/discover`
- `POST /api/discovery/cancel`
- `POST /api/discovery/views`
- `POST /api/discovery/views/delete`
- `POST /api/discovery/clear`
- `POST /api/ai-insights`
- `POST /api/ai-insights/delete`
- `POST /api/window/open`
- `POST /api/window/exit`
- `POST /api/sync-stars`

`/api/repo-details` 被保护是因为它虽然是 GET，但会触发 GitHub 请求和本地详情缓存写入。

## GitHub Token

GitHub Token 的作用主要是：

- 提高 GitHub API 请求稳定性；
- 降低限流影响；
- 让 GitHub 星标同步和关注更新追踪更可靠。

当前实现里：

- Token 保存在本地 `settings.json`。
- 保存前会通过 Windows DPAPI 加密。
- 加密和解密依赖当前 Windows 用户环境。
- DPAPI 调用使用 `CRYPTPROTECT_UI_FORBIDDEN`，避免后台任务触发系统 UI。
- Token 只用于 GitHub 相关请求，不会被上传到项目自建后台。
- 设置、bootstrap、诊断、日志和错误响应不应暴露明文 Token。

## 当前实现会连接哪些外部服务

GitSonar 当前可能访问这些外部网络目标：

- **GitHub Trending 页面与 GitHub API**
  用于趋势聚合、仓库详情、关注更新追踪、GitHub 星标同步和星标导入。
- **Google Translate 公共接口**
  代码当前会访问 `https://translate.googleapis.com/translate_a/single`，用于：
  - 把英文仓库描述和 README 摘要翻译成中文；
  - 把中文关键词发现查询翻译成英文。
- **本机 Ollama 类翻译服务**
  只有在用户主动把翻译方式切换为本机 Ollama 类 provider 并填写模型名时才会使用。
  本地翻译地址只允许 `127.0.0.1`、`localhost` 或 `::1`，用于避免把翻译内容误发到远端服务。
  如果未填写模型名或本机服务不可用，应用会保守返回原文，不会自动回退到 Google Translate。
- **ChatGPT / Gemini**
  只有在用户主动点击分析入口时才会触发。当前实现是生成或复制提示词，并打开 ChatGPT 网页版、桌面版或 Gemini 网页版。应用本身不会直接调用自定义 LLM API，也不会在应用内自动返回 AI provider 结论。

如果用户配置了代理，GitHub 和翻译请求会按本地代理设置转发。

## 当前 AI 边界

当前已实现：

- prompt handoff；
- copy-only prompt；
- 手动保存 `gitsonar.repo_insight.v1` 结构化 Insight JSON；
- 本地 AI artifact metadata、列表和删除。

当前未实现：

- 默认内嵌 AI provider；
- OpenAI-compatible provider pipeline；
- 自动向云端发送 repo、README、notes、tags、updates 或 Token；
- 自动根据 AI 输出修改用户状态。

后续任何 AI provider 都必须满足：

- 显式 opt-in；
- 本地 provider 和云 provider 分开配置；
- 调用前展示将发送字段；
- 输出可缓存、可删除、可重新生成；
- 不默认发送 GitHub Token、代理凭据、本地路径或未脱敏诊断信息。

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

SQLite 迁移尚未实施。任何持久化迁移必须保留 JSON 导入 / 导出兼容和回滚路径。

## 旧数据迁移

如果检测到旧目录 `%LOCALAPPDATA%\GitHubTrendRadar`，新版本会在首次运行时尝试把其中尚未迁入的数据合并到新的 `%LOCALAPPDATA%\GitSonar` 目录。

迁移目标主要包括：

- 用户设置；
- 已保存状态；
- 缓存数据；
- 运行时状态文件。

## 代理使用与边界

GitSonar 本身：

- 不提供 VPN；
- 不提供翻墙能力；
- 不提供加速能力。

它只会使用：

- 用户当前系统可访问的网络环境；
- 用户在设置里主动填写的代理地址；
- 自动探测到的本地常见代理端口，如果用户没有显式填写代理。

需要注意的是：

- 代理地址仍保存在本地 `settings.json`。
- 如果代理 URL 含用户名 / 密码，新版本保存设置时会像 GitHub Token 一样用 Windows DPAPI 加密整条代理 URL。
- 旧版本留下的明文代理配置仍可读取，并会在下一次保存设置时迁移到新的加密存储方式。
- API/UI payload 和日志只能展示脱敏后的代理地址。

## 当前用户可见脱敏保证

截至 2026-04-24，settings、bootstrap、diagnostics、status、discovery job payload 和 HTTP route exception logs 不应暴露：

- 明文代理凭据；
- GitHub Token；
- 原始 refresh / discovery 异常文本；
- 原始 traceback；
- 本地 runtime 绝对路径。

当前加固包括：

- 代理 URL 内部可以保留凭据，但 API/UI 只显示类似 `http://***:***@127.0.0.1:7890` 的值。
- Windows DPAPI encrypt/decrypt 调用使用 `CRYPTPROTECT_UI_FORBIDDEN`。
- 刷新失败写入用户安全状态消息，详细异常只在脱敏后记录。
- discovery job 失败返回安全摘要，不返回原始 backend exception。
- 未预期 HTTP route 失败记录脱敏摘要，不再附带原始 traceback payload。
- 过大的本地 JSON API request body 返回 `413 payload_too_large`。
- `/api/repo-details` 要求 loopback 和 control token。

## 备份、同步与代码签名

当前没有默认云同步、没有默认备份上传、没有代码签名、没有自动更新。

后续这些方向的安全边界：

- 加密备份 / 同步必须先明确同步目标、密钥管理、冲突策略和显式 opt-in。
- 任何同步都不能上传明文 GitHub Token、代理凭据、未脱敏诊断日志或用户未确认的 AI payload。
- 代码签名必须先明确证书来源、私钥保管、密码注入和时间戳服务。
- 自动更新必须先明确发布校验、回滚和用户确认策略。

## 风险提示

使用时仍建议注意：

- 不要分享高权限 GitHub Token。
- 不要把包含本地设置、代理凭据和用户状态的运行目录直接打包外传。
- 不要把 `runtime-data/`、`artifacts/`、本地缓存和导出数据误提交到仓库。
- 如果截图里含有私有仓库、代理地址或敏感目录，也不要直接公开。

根目录 `.gitignore` 已默认忽略常见运行数据和构建产物。
