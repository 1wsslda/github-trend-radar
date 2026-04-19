# GitSonar Progress

更新时间：2026-04-19

## 当前状态

GitSonar 目前已经完成从旧的顶层运行时模块向 `runtime/`、`runtime_github/`、`runtime_ui/` 三层结构的迁移，当前主线代码、测试和自动化校验都已经对齐到这套目录。

本轮工作的重点不是新增单点功能，而是把“已经拆了一半”的工程边界彻底收口，减少继续迭代时的漂移和重复定义。

## 当前架构

```text
src/gitsonar/
  __main__.py
  runtime/
    app.py
    discovery_jobs.py
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
    details.py
    discovery.py
    favorites.py
    shared.py
    trending.py
  runtime_ui/
    __init__.py
    assets.py
    template.py
    css/
    js/
```

职责边界如下：

- `runtime/app.py`：运行时装配、刷新调度、HTTP server 启动、应用主入口。
- `runtime/discovery_jobs.py`：关键词发现任务的状态机、ETA、启动、取消、结果落盘。
- `runtime/state.py`：快照、用户状态、discovery state 的读写与归一化；这里只保留状态事实，不再重复 job 常量与流程逻辑。
- `runtime/http.py`：路由表驱动的 HTTP API，集中处理 loopback 校验、JSON 解析、错误映射和响应格式。
- `runtime_github/`：GitHub 侧抓取、详情、discovery 打分、收藏同步与更新跟踪。
- `runtime_ui/`：运行时内嵌 HTML/CSS/JS 资源，按模板、样式、行为分片聚合。

兼容别名仍然保留给旧调用方，但新代码和新测试不应继续围绕 `gitsonar.app_runtime` 之类的旧入口扩展。

## 本轮已完成

### 1. 工程护栏

- 新增统一校验脚本 `scripts/verify_runtime.py`。
- 新增 `pyproject.toml`，收敛测试、lint、coverage 的基础配置。
- 更新 `.github/workflows/ci.yml` 与 `.github/workflows/release.yml`，统一复用同一套验证流程。
- 自动化基线现在覆盖：
  - 当前真实运行时代码的 `py_compile`
  - 聚合前端 JS 的语法检查
  - `python -m unittest discover -s tests -q`

### 2. 运行时拆分收口

- 从 `runtime/app.py` 中抽出 discovery job 生命周期到 `runtime/discovery_jobs.py`。
- 删除 `runtime/state.py` 中重复的 discovery job 常量与辅助逻辑，保留单一事实来源。
- `runtime/app.py` 现在只负责装配和编排，不再承载完整的 discovery 业务状态机。

### 3. HTTP 路由层重构

- `runtime/http.py` 已从长链式 `if/elif` 迁移为 `method + path -> handler` 的路由表。
- 变更后的路由层统一处理：
  - loopback 来源校验
  - JSON body 解析
  - 业务异常到 HTTP 状态码的映射
  - JSON/附件响应输出

### 4. 前端契约清理

- `runtime_ui/js/state.py` 已收敛为状态、选择器和 helper，不再重复定义 action。
- action 逻辑只保留在 `runtime_ui/js/actions.py`。
- Discover 面板的模板、JS、CSS 契约已重新对齐：
  - 新的抽屉区块为 `control-drawer-discover`
  - 抽屉内查询输入为 `discover-query-drawer`
  - 旧的 `discover-filter-panel` 标识已移除

### 5. GitHub 侧优化

- discovery 内存缓存增加上限，避免缓存无界增长。
- `runtime_github/discovery.py` 增加 cache hit / store / duration 日志。
- `runtime_github/favorites.py` 的 `track_favorite_updates()` 已改为受限并发抓取，同时保留遇到限流时的停止策略。
- refresh、discovery、favorite tracking 现在都会输出结构化耗时日志，便于后续继续调优。

### 6. 测试补齐

新增或重写的测试已覆盖：

- discovery job 生命周期与取消流程
- HTTP mutating endpoint 的 happy path / error path
- 收藏更新轮询与并发刷新
- startup / 单实例唤醒流程
- 聚合 UI 资源的结构契约与 JS 语法校验
- 聚合 JS 不允许出现重复命名函数
- discovery 相关测试直接面向 `gitsonar.runtime.*`，不再依赖旧兼容入口

## 当前验证基线

当前仓库已通过以下命令：

```powershell
python -m unittest discover -s tests -q
python scripts/verify_runtime.py
```

截至 2026-04-19，这两条命令都在本地通过。

## 后续建议

后续迭代优先顺序建议保持为：

1. 继续补少量真实 API 降级与 warning 场景的回归测试。
2. 根据结构化日志再做 discovery 与 favorite tracking 的性能调优。
3. 在不引入新技术栈的前提下，继续细化 `runtime_ui/js/` 和 `runtime_ui/css/` 的分片边界。
4. 如需继续开放旧入口兼容层，新增文档时也只把它们标记为“兼容别名”，不要再把它们写成主入口。
