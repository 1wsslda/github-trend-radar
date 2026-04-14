# Architecture

## 项目定位

GitSonar 是一个面向中文用户的 GitHub 项目情报台。  
它的目标不是做一个“桌面版 Trending 页面”，而是把发现、筛选、跟踪、对比和 AI 分析整合进一套长期常驻的桌面工作流。

## 运行结构

整体链路可以理解为：

```text
GitHub Trending 页面 + GitHub API
                ->
         Python Runtime
                ->
       Local HTTP Server
                ->
    Desktop Shell Window
                ->
          System Tray
```

## 核心模块

### `src/gitsonar/app_runtime.py`

运行时编排层，负责：

- 配置加载与保存
- 本地数据目录管理
- 后台刷新调度
- 单实例控制
- HTML 生成与本地服务启动

### `src/gitsonar/runtime_github.py`

GitHub 数据层，负责：

- 趋势数据抓取
- GitHub API 请求
- 仓库详情获取
- 收藏更新追踪

### `src/gitsonar/runtime_http.py`

本地 HTTP API 层，负责：

- 前端页面服务
- 状态变更接口
- 刷新、窗口、设置相关接口

### `src/gitsonar/runtime_shell.py`

桌面壳与托盘层，负责：

- 系统托盘
- 隐藏 / 唤醒主窗口
- 关闭行为控制
- 桌面壳窗口生命周期管理

### `src/gitsonar/runtime_ui.py`

前端模板层，负责：

- HTML / CSS / JS 模板
- 列表渲染
- 详情抽屉、对比抽屉
- 前端交互与本地 API 协作

### `src/gitsonar/runtime_utils.py`

通用工具层，负责：

- 本地文件读写
- DPAPI 加解密
- 代理检测与标准化
- 文本处理和计数提取

## 设计选择

### 为什么不是 Electron

当前方案不是传统 Electron 桌面应用，而是：

- Python 负责运行时、抓取、状态和本地服务
- 浏览器应用模式窗口负责显示 UI
- 系统托盘负责常驻和唤醒

这个方案的优点是：

- 前端改造成本更低
- 构建链路更轻
- 更适合“长期挂着、偶尔唤醒”的工具形态

### 为什么强调托盘

GitSonar 的价值不在一次性打开，而在持续使用。  
托盘、后台刷新、关闭行为可配置，都是为了把它做成真正能长期陪跑的桌面工作台。

## 数据与兼容性

当前冻结版运行时数据目录已经切换为：

```text
%LOCALAPPDATA%\GitSonar
```

为了兼容旧版本，程序在启动时会自动尝试把旧目录 `%LOCALAPPDATA%\GitHubTrendRadar` 中尚未迁入的新目录内容合并过来，主要覆盖：

- 用户设置
- 已保存状态
- 缓存数据
- 运行时状态文件

此外，新版本会同时兼容旧单实例标识与旧运行时状态文件，避免品牌重命名后出现重复实例或配置断层。
