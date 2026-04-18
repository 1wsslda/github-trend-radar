# CODEMAP

## 顶层先认目录

现在 `src/gitsonar/` 顶层应该只看这几块：

```text
src/gitsonar/
  __init__.py
  __main__.py
  runtime/
  runtime_github/
  runtime_ui/
```

含义很简单：

- `__main__.py`：程序入口
- `runtime/`：本地运行时内核，负责装配、状态、设置、HTTP、托盘
- `runtime_github/`：GitHub 数据抓取和 discovery
- `runtime_ui/`：HTML / CSS / JS 资源

## 改什么看哪里

| 需求 | 先看这些文件 | 说明 |
|---|---|---|
| 应用入口 / 启动流程 | `src/gitsonar/__main__.py`, `src/gitsonar/runtime/app.py` | `__main__` 只负责跳到 `main()` |
| 运行时总装配 | `src/gitsonar/runtime/app.py` | 这里只放装配、刷新调度、HTTP server 启动 |
| 路径、运行目录、兼容迁移 | `src/gitsonar/runtime/paths.py` | 开发态 / 冻结态路径都在这里 |
| 设置读写、Token、代理 | `src/gitsonar/runtime/settings.py` | 只处理设置，不处理 UI |
| 用户状态、snapshot、discovery 状态 | `src/gitsonar/runtime/state.py` | 包括 normalize / load / save / import / export |
| 文本翻译与缓存 | `src/gitsonar/runtime/translation.py` | 描述翻译和查询词翻译 |
| 单实例、开机启动、运行时状态文件 | `src/gitsonar/runtime/startup.py` | 也负责当前窗口 URL / 浏览器进程状态 |
| HTTP API | `src/gitsonar/runtime/http.py` | handler 很薄，业务逻辑通过参数注入 |
| 窗口、托盘、唤醒、退出 | `src/gitsonar/runtime/shell.py` | 所有桌面壳行为都走这里 |
| 通用工具函数 | `src/gitsonar/runtime/utils.py` | 不放业务语义 |
| GitHub Trending 抓取 | `src/gitsonar/runtime_github/trending.py` | 列表抓取、搜索、批量 fetch |
| GitHub discovery 排序与扩展 | `src/gitsonar/runtime_github/discovery.py` | query 生成、related terms、scoring |
| GitHub 仓库详情 | `src/gitsonar/runtime_github/details.py` | README、release、topics、详情补全 |
| 收藏同步和更新追踪 | `src/gitsonar/runtime_github/favorites.py` | star sync、watch、favorite update |
| GitHub 依赖装配 | `src/gitsonar/runtime_github/__init__.py`, `src/gitsonar/runtime_github/shared.py` | `__init__` 只做组装，`shared.py` 放依赖容器和公共工具 |
| HTML 模板 | `src/gitsonar/runtime_ui/template.py` | 只负责模板和 payload 注入 |
| UI 资源拼接 | `src/gitsonar/runtime_ui/assets.py` | 只负责按顺序拼接 CSS / JS |
| 前端 JS 行为 | `src/gitsonar/runtime_ui/js/` | 按功能拆成多个资源片段 |
| 前端 CSS | `src/gitsonar/runtime_ui/css/` | 按 tokens / shell / cards / overlays / responsive 拆分 |
| UI / GitHub 结构回归测试 | `tests/test_runtime_ui_assets.py`, `tests/test_ui_js_smoke.py`, `tests/test_runtime_github_exports.py` | 验证公开导出和资源拼接 |
| discovery / star sync 回归 | `tests/test_discovery_profiles.py`, `tests/test_github_star_sync.py` | 改 GitHub 数据层时优先跑 |

## 公开接口

稳定入口仍然是：

- `from gitsonar.runtime_ui import build_html`
- `from gitsonar.runtime_github import make_github_runtime`
- `from gitsonar.__main__ import main`

## 兼容导入

为了不打断旧脚本，这些旧模块路径目前仍可导入，但只作为兼容别名：

- `gitsonar.app_runtime`
- `gitsonar.runtime_http`
- `gitsonar.runtime_paths`
- `gitsonar.runtime_settings`
- `gitsonar.runtime_shell`
- `gitsonar.runtime_startup`
- `gitsonar.runtime_state`
- `gitsonar.runtime_translation`
- `gitsonar.runtime_utils`

新代码不要继续用这些旧路径。

## 已废弃路径

这些路径已经废弃：

- `gitsonar.runtime_ui_parts`
- `src/gitsonar/runtime_ui.py`
- `src/gitsonar/runtime_github.py`

如果搜索时看到它们，多半是历史文档或旧分支内容，不应该再作为新代码入口。
