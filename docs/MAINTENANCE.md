# 仓库维护手册

## 目标

这份文档只回答一件事：以后要改 GitSonar，应该先看哪里、怎么改、改完怎么验。

如果你只记 3 条规则，记这 3 条：

1. 不要再往 `runtime/app.py`、`runtime_ui/assets.py`、`runtime_github/__init__.py` 里继续堆大段新逻辑。
2. 先按职责找模块，再动代码；找不到入口时先看 `docs/CODEMAP.md`。
3. 提交前至少跑 `python scripts/verify_runtime.py` 和 `python -m unittest discover -s tests -q`。

## 先看哪里

### 改 GitHub 抓取 / discovery / 收藏同步

看：

- `src/gitsonar/runtime_github/discovery.py`
- `src/gitsonar/runtime_github/trending.py`
- `src/gitsonar/runtime_github/details.py`
- `src/gitsonar/runtime_github/favorites.py`

不要直接往 `runtime_github/__init__.py` 加业务逻辑，那里只做组装。

### 改 HTML / CSS / JS UI

看：

- `src/gitsonar/runtime_ui/template.py`
- `src/gitsonar/runtime_ui/assets.py`
- `src/gitsonar/runtime_ui/js/`
- `src/gitsonar/runtime_ui/css/`

不要改已经删除的 `runtime_ui_parts/` 路径。

### 改设置、状态、翻译、启动行为

看：

- `src/gitsonar/runtime/settings.py`
- `src/gitsonar/runtime/state.py`
- `src/gitsonar/runtime/translation.py`
- `src/gitsonar/runtime/startup.py`

`runtime/app.py` 只保留装配与调度，不再承载这些实现细节。

### 改 HTTP 接口

看：

- `src/gitsonar/runtime/http.py`

接口背后的业务实现一般来自 `runtime/app.py` 注入的方法，而不是直接写死在 handler 里。

### 改窗口、外部打开行为

看：

- `src/gitsonar/runtime/shell.py`

### 改路径、运行目录、兼容迁移

看：

- `src/gitsonar/runtime/paths.py`

## 推荐工作流

### 1. 拉起新分支

```powershell
git switch main
git pull origin main
git switch -c feature/some-change
```

### 2. 先确认改动范围

```powershell
git status
rg -n "你要改的关键字" src tests docs
```

### 3. 改代码

改动原则：

- 新逻辑优先放进职责最贴近的子模块
- 共享常量和小工具优先放进对应包的 `shared.py` 或同层 helper
- 只有装配代码才放进 `runtime/app.py`

### 4. 跑最小验证

如果你只改了 UI：

```powershell
python -m py_compile src\gitsonar\runtime_ui\__init__.py src\gitsonar\runtime_ui\assets.py src\gitsonar\runtime_ui\template.py
python -m unittest tests.test_runtime_ui_assets tests.test_ui_js_smoke -q
```

如果你只改了 GitHub 数据层：

```powershell
python -m py_compile src\gitsonar\runtime_github\__init__.py src\gitsonar\runtime_github\shared.py src\gitsonar\runtime_github\discovery.py src\gitsonar\runtime_github\trending.py src\gitsonar\runtime_github\details.py src\gitsonar\runtime_github\favorites.py
python -m unittest tests.test_discovery_profiles tests.test_github_star_sync tests.test_runtime_github_exports -q
```

如果你改了本地运行时内核：

```powershell
python -m py_compile src\gitsonar\runtime\app.py src\gitsonar\runtime\http.py src\gitsonar\runtime\paths.py src\gitsonar\runtime\settings.py src\gitsonar\runtime\shell.py src\gitsonar\runtime\startup.py src\gitsonar\runtime\state.py src\gitsonar\runtime\translation.py src\gitsonar\runtime\utils.py
python -m unittest discover -s tests -q
```

### 5. 跑仓库级回归

这是默认必跑项：

```powershell
python scripts/verify_runtime.py
python -m unittest discover -s tests -q
```

### 6. 检查提交范围

```powershell
git status
git diff --cached --stat
```

不要把这些东西提交进仓库：

- Token
- 本地代理密码
- `runtime-data/`
- `%LOCALAPPDATA%\GitSonar` 导出的运行时文件
- 打包产物

## 常见注意事项

### 关于入口

统一入口是：

```powershell
python src/gitsonar/__main__.py
```

打包和运行都以 `src/gitsonar/__main__.py` 为准，不再使用旧的 `src/GitSonar.pyw`。

### 关于 UI 资源

`runtime_ui/assets.py` 只负责拼接顺序，不负责写业务。

如果你需要改 UI 行为：

- 改 `runtime_ui/js/*.py`
- 改 `runtime_ui/css/*.py`
- 最后确认 `assets.py` 仍然保持正确拼接顺序

### 关于 `runtime_github/__init__.py`

这个文件只做依赖组装与对外暴露。

如果你想新增 GitHub 相关功能：

- 先判断它属于 `discovery`、`trending`、`details` 还是 `favorites`
- 实在跨模块，再放到 `shared.py`

### 关于 `runtime/app.py`

这里只有这些东西是合理的：

- 全局共享对象初始化
- 子模块组装
- 刷新调度
- HTTP server 启动
- `main()`

如果一个函数能独立说明职责，优先挪到 `runtime/settings.py`、`runtime/state.py`、`runtime/translation.py` 或 `runtime/startup.py`。

### 关于旧路径

`gitsonar.app_runtime`、`gitsonar.runtime_utils` 这些旧路径现在还能导入，但只是兼容层。

新代码统一使用新路径：

- `gitsonar.runtime.app`
- `gitsonar.runtime.utils`
- `gitsonar.runtime.settings`
- `gitsonar.runtime.state`

## 发版前检查

至少确认：

1. `python -m unittest discover -s tests -q` 通过。
2. `python src/gitsonar/__main__.py` 能正常启动。
3. 设置保存、后台刷新、单实例唤醒、详情抽屉、收藏同步这几条主路径没有回退。
4. 文档里的路径没有再写旧的单文件运行时结构。
