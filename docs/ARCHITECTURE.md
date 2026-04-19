# Architecture

## 定位

GitSonar 是一个面向中文用户的 GitHub 项目情报台。

它不是单纯的“桌面版 Trending 页面”，而是一个本地工作台：负责抓取、筛选、跟踪、收藏、详情补全和前端展示。当前版本里，主窗口关闭就退出，单实例唤醒仍然保留。

## 运行链路

```text
GitHub Trending + GitHub API
              ->
        Python Runtime
              ->
      Local HTTP Server
              ->
   Desktop Shell Window
```

## 当前目录结构

```text
src/gitsonar/
  __init__.py
  __main__.py
  runtime/
    __init__.py
    app.py
    http.py
    paths.py
    settings.py
    shell.py
    startup.py
    state.py
    translation.py
    utils.py
  runtime_github/
    __init__.py
    shared.py
    discovery.py
    trending.py
    details.py
    favorites.py
  runtime_ui/
    __init__.py
    template.py
    assets.py
    js/
    css/
```

## 模块职责

### `src/gitsonar/__main__.py`

应用入口。负责把仓库内直接运行 `python src/gitsonar/__main__.py` 和打包后的启动方式统一到 `runtime.app.main()`。

### `src/gitsonar/runtime/app.py`

运行时编排层。这里只保留顶层装配和调度逻辑：

- 初始化全局会话、锁和共享内存状态
- 组装 `runtime/settings.py`、`runtime/state.py`、`runtime/translation.py`、`runtime/startup.py`
- 组装 `runtime_github`、`runtime/http.py`、`runtime/shell.py`
- 启动本地 HTTP 服务
- 执行后台刷新循环

### `src/gitsonar/runtime/paths.py`

路径与运行目录模块。负责：

- 应用名和路径常量
- 开发态 / 冻结态运行目录计算
- 旧目录向新目录的迁移合并

### `src/gitsonar/runtime/settings.py`

设置模块。负责：

- 默认设置
- 设置归一化
- 设置加载 / 保存
- 敏感字段加解密
- 代理与 GitHub Token 生效

### `src/gitsonar/runtime/state.py`

本地状态模块。负责：

- `snapshot`
- `user_state`
- `discovery_state`
- import / export / normalize / load / save

### `src/gitsonar/runtime/translation.py`

翻译模块。负责：

- 翻译缓存
- 英文到中文描述翻译
- 中文查询词转英文
- snapshot 内仓库描述翻译

### `src/gitsonar/runtime/startup.py`

启动与单实例模块。负责：

- 单实例互斥
- 开机启动脚本
- 运行时状态文件
- 唤醒已存在实例
- 主窗口 URL / 浏览器进程状态

### `src/gitsonar/runtime/http.py`

本地 HTTP API 层。负责请求解析、响应输出和接口路由，本身不持有业务逻辑，业务能力都通过参数注入。

### `src/gitsonar/runtime/shell.py`

桌面壳层。负责浏览器应用窗口、外链打开、关闭监听和窗口唤醒。

### `src/gitsonar/runtime/utils.py`

通用工具模块。负责：

- 文件读写
- 文本归一化
- DPAPI 加解密
- 代理探测
- 时间与计数处理

### `src/gitsonar/runtime_github/`

GitHub 数据层，按职责拆分：

- `shared.py`：依赖容器 `GitHubRuntimeDeps`、公共异常和基础请求工具
- `trending.py`：Trending 抓取、搜索、批量拉取
- `details.py`：仓库详情、README、release 等详情补全
- `discovery.py`：query 生成、ranking、相关词扩展、结果重排
- `favorites.py`：收藏同步、watch 追踪、更新记录
- `__init__.py`：对外只暴露 `make_github_runtime(...)`

### `src/gitsonar/runtime_ui/`

前端模板层，保留“Python 内嵌 HTML/CSS/JS”的模式，但按资源职责拆分：

- `template.py`：HTML 模板和 payload 注入
- `assets.py`：按固定顺序拼接 CSS / JS
- `css/`：样式分片
- `js/`：行为分片
- `__init__.py`：对外只暴露 `build_html(...)`

## 依赖方向

保持这个方向，不要反向依赖：

```text
runtime/utils.py + runtime/paths.py
                ->
runtime/settings.py + runtime/state.py + runtime/translation.py + runtime/startup.py
                ->
runtime/app.py
                ->
runtime/http.py + runtime/shell.py + runtime_github/ + runtime_ui/
```

`runtime/http.py` 和 `runtime/shell.py` 不应该反向 import `runtime/app.py`。

## 公开接口

当前稳定公开接口只有这几个：

- `from gitsonar.runtime_ui import build_html`
- `from gitsonar.runtime_github import make_github_runtime`
- `from gitsonar.__main__ import main`

## 兼容性

为了兼容旧代码，`gitsonar.__init__` 里保留了旧模块路径的兼容别名：

- `gitsonar.app_runtime`
- `gitsonar.runtime_http`
- `gitsonar.runtime_paths`
- `gitsonar.runtime_settings`
- `gitsonar.runtime_shell`
- `gitsonar.runtime_startup`
- `gitsonar.runtime_state`
- `gitsonar.runtime_translation`
- `gitsonar.runtime_utils`

新代码不要继续使用这些旧别名。

## 运行时数据

开发态默认写入仓库根目录下的 `runtime-data/`。

冻结版默认写入：

```text
%LOCALAPPDATA%\GitSonar
```

程序启动时会尝试把旧品牌目录 `%LOCALAPPDATA%\GitHubTrendRadar` 的数据迁移到新目录。
