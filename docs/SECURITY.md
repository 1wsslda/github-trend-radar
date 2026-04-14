# Security

## 本地优先

GitSonar 是一个本地运行的桌面工具。

当前实现下：

- 抓取、缓存、状态管理都在本机完成
- 前端页面由本地 HTTP 服务提供
- Token、设置和用户状态保存在本地

它不是 SaaS，也不会把你的使用状态同步到远端后台。

## GitHub Token

GitHub Token 的作用主要是：

- 提高 GitHub API 请求稳定性
- 降低限流影响
- 让收藏更新追踪更可靠

在 Windows 上，Token 通过本地 DPAPI 加密保存。  
这意味着：

- 加密和解密都依赖当前 Windows 用户环境
- 不是明文直存
- 不是上传到外部服务器的云凭证

## 本地存储

冻结版运行时数据当前默认位于：

```text
%LOCALAPPDATA%\GitSonar
```

常见文件包括：

- `settings.json`
- `user_state.json`
- `repo_details_cache.json`
- `runtime_state.json`
- `data/latest.json`

如果检测到旧目录 `%LOCALAPPDATA%\GitHubTrendRadar`，新版本会在首次运行时自动尝试将其内容合并到新目录中。

## 网络边界

GitSonar 本身：

- 不提供 VPN
- 不提供翻墙能力
- 不提供加速能力

它只会使用：

- 你当前系统可访问的 GitHub 网络环境
- 你在设置里主动填写的代理地址

如果 GitHub 当前不可访问，产品本身无法替代网络环境。

## 代理使用

如果你填写代理地址，程序会将它用于 GitHub 相关请求。  
这可以降低配置成本，但并不改变安全边界：

- 代理由你自己提供
- 流量仍按你的本地网络环境和代理配置转发
- 项目不会额外代管你的网络出口

## 风险提示

使用时仍建议注意：

- 不要把高权限 Token 直接分享给别人
- 不要把包含本地配置和用户状态的运行目录随意打包外传
- 如果准备开源同步仓库，确保不提交本地运行数据文件

根目录 `.gitignore` 已默认忽略常见运行数据和构建产物。
