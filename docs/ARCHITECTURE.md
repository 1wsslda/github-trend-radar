# Architecture

## 定位

GitSonar 是一个 Windows-first、本地优先的 GitHub 项目情报工作台。

当前运行形态仍是：

```text
Python Runtime
  -> Local HTTP Server
  -> Desktop browser / WebView-style shell
  -> Embedded HTML / CSS / JS
```

仓库已经完成了多轮增量拆分，但还没有迁移到 React、FastAPI、SQLite 或内嵌 AI provider。任何后续迁移都应继续按计划文件小步推进。

## 当前运行链路

```text
GitHub Trending HTML + GitHub REST API
              ->
        runtime_github data layer
              ->
        runtime app orchestration
              ->
      local HTTP API + embedded UI
              ->
   desktop browser / WebView shell
```

## 当前目录结构

```text
src/gitsonar/
  __init__.py
  __main__.py
  runtime/
    __init__.py
    ai_insight.py
    api_boundary.py
    app.py
    detail_cache.py
    diagnostics.py
    discovery_clusters.py
    discovery_jobs.py
    http.py
    jobs.py
    paths.py
    redaction.py
    repo_records.py
    settings.py
    shell.py
    startup.py
    state.py
    state_schema.py
    state_store.py
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
    css/
    js/
```

## 模块职责

### `src/gitsonar/__main__.py`

应用入口。负责把仓库内直接运行 `python src/gitsonar/__main__.py` 和打包后的启动方式统一到 `runtime.app.main()`。

### `src/gitsonar/runtime/app.py`

运行时编排层。这里负责顶层装配和调度：

- 初始化会话、锁、运行时状态和桌面壳；
- 组装 settings、state、translation、startup、GitHub runtime、HTTP server 和 UI；
- 启动本地 HTTP 服务；
- 执行后台刷新循环；
- 连接 discovery job、job/event runtime、diagnostics、detail cache 等能力。

该文件仍有编排压力。新增领域逻辑不应继续堆进 `app.py`，应优先放进独立 runtime 模块。

### `src/gitsonar/runtime/http.py`

本地 HTTP API 层。负责请求解析、响应输出、路由表、loopback/control-token 校验、JSON body size limit 和错误响应。

业务能力通过参数注入，不应从这里反向 import `runtime.app.py`。

### `src/gitsonar/runtime/api_boundary.py`

只读 JSON API 边界整理模块。为 `/api/bootstrap`、`/api/repos`、`/api/updates`、`/api/discovery/views` 等端点生成稳定 payload。

### `src/gitsonar/runtime/diagnostics.py`

本地诊断模块。覆盖运行目录、状态文件、端口、代理、Token、GitHub 可达性等信号，并通过脱敏后的 payload 给 UI 展示。

### `src/gitsonar/runtime/discovery_jobs.py`

发现任务运行时。负责关键词发现的后台 job 状态、取消、错误摘要和结果回写。

当前 discovery job runtime 已存在，但还没有完全接入通用 `jobs.py` Job / Event runtime。

### `src/gitsonar/runtime/jobs.py`

通用内存级 Job / Event runtime。提供 job 创建、状态更新、事件历史、过滤和 SSE 快照数据。

当前它已支撑 `/api/jobs`、`/api/events`、`/api/events/stream`，但 refresh、discovery、update check 等工作流尚未全部统一接入。

### `src/gitsonar/runtime/ai_insight.py`

结构化 Insight artifact 模块。当前支持手动保存、归一化、删除、列表和本地 metadata，不接入任何 AI provider。

### `src/gitsonar/runtime/discovery_clusters.py`

本地发现结果聚类模块。基于 repo 文本、topic、language 等本地信息生成轻量主题聚类，供 state/API/UI 展示。

### `src/gitsonar/runtime/redaction.py`

脱敏模块。集中处理 proxy credentials、Token、路径、异常文本等用户可见和日志可见内容的安全化展示。

### `src/gitsonar/runtime/state_schema.py`

状态 schema 与归一化规则。负责当前 JSON 状态中的 tags、notes、saved discovery views、favorite updates、AI insights、clusters 等结构兼容。

### `src/gitsonar/runtime/state_store.py`

JSON 状态读写和存储辅助。当前持久化仍以 JSON 文件为事实存储，SQLite 尚未实施。

### `src/gitsonar/runtime/detail_cache.py`

仓库详情缓存模块。负责 repo details / README / release 等详情缓存读写。

### `src/gitsonar/runtime/paths.py`

路径与运行目录模块。负责应用名、开发态 / 冻结态运行目录计算，以及旧品牌目录 `%LOCALAPPDATA%\GitHubTrendRadar` 向 `%LOCALAPPDATA%\GitSonar` 的迁移合并。

### `src/gitsonar/runtime/settings.py`

设置模块。负责默认设置、设置归一化、加载 / 保存、敏感字段 DPAPI 加解密、代理与 GitHub Token 生效。

### `src/gitsonar/runtime/state.py`

本地状态 facade。负责 snapshot、user_state、discovery_state 的 import / export / normalize / load / save 编排。

### `src/gitsonar/runtime/translation.py`

翻译模块。支持默认在线翻译路径和显式 opt-in 的 loopback-only Ollama-style 本地翻译 provider。

### `src/gitsonar/runtime/startup.py`

启动与单实例模块。负责单实例互斥、开机启动脚本、运行时状态文件、唤醒已存在实例、主窗口 URL / 浏览器进程状态。

### `src/gitsonar/runtime/shell.py`

桌面壳层。负责浏览器应用窗口、外链打开、关闭监听和窗口唤醒。

### `src/gitsonar/runtime/utils.py`

通用工具模块。负责文件读写、文本归一化、DPAPI 加解密、代理探测、时间与计数处理。

### `src/gitsonar/runtime_github/`

GitHub 数据层，按职责拆分：

- `shared.py`：依赖容器 `GitHubRuntimeDeps`、公共异常和基础请求工具。
- `trending.py`：Trending 抓取、搜索、批量拉取。
- `details.py`：仓库详情、README、release 等详情补全。
- `discovery.py`：query 生成、ranking、相关词扩展、结果重排。
- `favorites.py`：收藏同步、watch 追踪、更新记录。
- `__init__.py`：对外只暴露 `make_github_runtime(...)`。

### `src/gitsonar/runtime_ui/`

前端模板层。继续保留 Python 内嵌 HTML/CSS/JS，但已按资源职责拆分：

- `template.py`：HTML 模板和 payload 注入。
- `assets.py`：按固定顺序拼接 CSS / JS。
- `css/`：样式分片。
- `js/`：行为分片。
- `__init__.py`：对外只暴露 `build_html(...)`。

## API 分层现状

### 当前 loopback + control-token 保护端点

本地 JSON API 当前统一要求 loopback 访问；业务、状态、诊断、导出、事件和只读数据端点也要求 runtime control token。

只读数据端点包括：

- `GET /api/bootstrap`
- `GET /api/repos`
- `GET /api/updates`
- `GET /api/discovery/views`
- `GET /api/settings`
- `GET /api/status`
- `GET /api/discovery`
- `GET /api/discovery/job`
- `GET /api/ai-artifacts`
- `GET /api/jobs`
- `GET /api/events`
- `GET /api/events/stream`
- `GET /api/repo-details`
- `GET /api/diagnostics`
- `GET /api/export`
- 所有状态、设置、导入、刷新、发现、AI Insight、窗口控制、外链打开和 GitHub star sync 的 POST 端点。

主界面通过初始 HTML payload 中的 runtime control token 调用这些 API；缺少或错误 token 的直接 API 请求会返回 `403 invalid_control_token`。

### SSE MVP

`GET /api/events/stream` 当前是 SSE 快照端点，输出已记录的 Job/Event 历史。它不是完整实时后台总线替代品，后续还需要把刷新、发现、更新检查等流程逐步接入统一 runtime。

## 数据与持久化现状

当前仍使用 JSON 文件作为事实存储：

```text
settings.json
user_state.json
discovery_state.json
repo_details_cache.json
status.json
runtime_state.json
data/latest.json
```

SQLite 迁移已有设计文档，但尚未实施存储切换。任何实际迁移都必须保留 JSON 导入 / 导出兼容和明确回滚路径。

## 依赖方向

保持这个方向，不要反向依赖：

```text
runtime/utils.py + runtime/paths.py + runtime/redaction.py
                ->
runtime/settings.py + runtime/state_schema.py + runtime/state_store.py
                ->
runtime/state.py + runtime/translation.py + runtime/startup.py
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

## 当前限制

- 持久化仍是 JSON 文件，长期数据量、查询、迁移和并发写入会继续承压。
- `runtime/app.py` 仍承担较多编排职责，需要继续把领域逻辑移入小模块。
- Vanilla JS 分片可维护性已改善，但复杂交互继续增长会带来维护压力。
- Trending 数据仍依赖 GitHub 页面结构，页面结构变化会影响抓取稳定性。
- 桌面壳仍偏浏览器 app mode，WebView2 native bridge 还不是主通道。
- Discovery job runtime 与通用 Job / Event / SSE runtime 尚未完全统一。
- AI 仍是 prompt handoff + 手动 artifact，不是 provider pipeline。

## 运行时数据

开发态默认写入仓库根目录下的 `runtime-data/`。

冻结版默认写入：

```text
%LOCALAPPDATA%\GitSonar
```

程序启动时会尝试把旧品牌目录 `%LOCALAPPDATA%\GitHubTrendRadar` 的数据迁移到新目录。
