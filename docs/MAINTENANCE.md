# 仓库维护操作手册

这份文档是给仓库维护者看的。

目标不是讲 Git 原理，而是告诉你后续应该怎么做，什么时候点 GitHub 网页，什么时候在本地终端执行命令，尽量避免出错。

适用仓库：

- GitHub 仓库：`1wsslda/github-trend-radar`
- 默认分支：`main`
- 当前公开状态：`PUBLIC`

## 你只需要记住的最小规则

1. 不要把大改动直接做在 `main` 上。
2. 先开新分支，改完再合并回 `main`。
3. 提交前先看 `git status`，确认没有把不该提交的文件带进去。
4. 不要提交 Token、代理密码、运行时数据、缓存、安装包。
5. 发版前先更新 `CHANGELOG.md`，再按 `docs/RELEASE_CHECKLIST.md` 检查。

## 先理解 4 个概念

### 1. 仓库

就是 GitHub 上那个项目：

- `https://github.com/1wsslda/github-trend-radar`

### 2. 分支

你可以把分支理解成“独立施工线”。

- `main`：正式主线，应该尽量保持稳定
- `feature/...` 或 `fix/...`：你临时做功能或修 bug 的地方

### 3. 提交

提交就是一次有说明的保存点。

例子：

- `Refine desktop intelligence workspace UI`
- `Add changelog and release notes template`

### 4. Release

Release 是“正式发布记录”，通常配合 tag 使用，比如：

- `v1.0.0`
- `v1.0.1`

## 一次性准备

如果你换电脑，先做这几步。

### 1. 安装 Git

安装后先确认：

```powershell
git --version
```

### 2. 配置 Git 用户名和邮箱

只需要做一次：

```powershell
git config --global user.name "你的 GitHub 用户名"
git config --global user.email "你的 GitHub 邮箱"
```

检查是否成功：

```powershell
git config --global --list
```

### 3. 安装 GitHub CLI

建议安装 `gh`，以后很多 GitHub 操作会方便很多。

检查：

```powershell
gh --version
```

登录：

```powershell
gh auth login
```

确认登录状态：

```powershell
gh auth status
```

### 4. 进入仓库目录

```powershell
cd "C:\Users\liushun\Desktop\Github stars"
```

## 日常最常用的 5 个场景

## 场景 1：我要开始一个新改动

这是你以后最常用的流程。

### 步骤 1：先回到主线并拉最新代码

```powershell
git switch main
git pull origin main
```

### 步骤 2：新建一个分支

功能改动：

```powershell
git switch -c feature/ui-polish
```

修 bug：

```powershell
git switch -c fix/settings-save
```

文档改动：

```powershell
git switch -c docs/update-maintenance-guide
```

命名不要太长，但要看得出用途。

### 步骤 3：开始改代码或文档

改完以后，先看有哪些文件变了：

```powershell
git status
```

如果你只想提交某几个文件，不要一上来就 `git add .`。

### 步骤 4：先跑最相关的检查

例如你改了 `runtime_ui.py`：

```powershell
python -m py_compile src\gitsonar\runtime_ui.py
```

如果你改了打包脚本，就至少跑对应脚本做一次烟雾检查。

### 步骤 5：只暂存你想提交的文件

例子：

```powershell
git add src/gitsonar/runtime_ui.py
git add README.md
```

如果你确定当前工作区所有改动都应该提交，再用：

```powershell
git add .
```

### 步骤 6：再次确认提交范围

```powershell
git status
git diff --cached --stat
```

如果看见不该提交的文件，先不要 commit。

### 步骤 7：提交

```powershell
git commit -m "Refine settings panel layout"
```

提交信息建议：

- 用英文短句
- 只写这次真正做的事
- 不要写成一大段

### 步骤 8：推送到 GitHub

第一次推送当前分支：

```powershell
git push -u origin feature/ui-polish
```

后续同一个分支再次推送：

```powershell
git push
```

## 场景 2：我要把分支合并到 main

你可以用两种方式。

### 方式 A：GitHub 网页上合并

适合你想保留 PR 记录的时候。

步骤：

1. 先把分支推上去。
2. 打开 GitHub 仓库页面。
3. GitHub 通常会提示你刚推送了一个分支，可以点 `Compare & pull request`。
4. 检查改动范围。
5. 填标题和说明。
6. 点 `Create pull request`。
7. 确认没问题后点 `Merge pull request`。
8. 合并后删除分支。

这是最安全、最直观的方式。

### 方式 B：本地终端直接合并

适合你一个人维护，改动也很清楚。

先切回 `main`：

```powershell
git switch main
git pull origin main
```

快进合并：

```powershell
git merge --ff-only feature/ui-polish
```

如果成功，再推送：

```powershell
git push origin main
```

合并完成后删除本地分支：

```powershell
git branch -d feature/ui-polish
```

删除远端分支：

```powershell
git push origin --delete feature/ui-polish
```

### `--ff-only` 是什么

它表示“只允许快进合并”。

好处：

- 不会平白多出一个 merge commit
- 线性历史更干净
- 如果不能安全快进，它会直接报错，不会帮你乱合

所以平时本地合并建议优先用这个。

## 场景 3：我要发布新版本

这个流程不要省。

### 步骤 1：确保 `main` 是最新的

```powershell
git switch main
git pull origin main
```

### 步骤 2：更新 `CHANGELOG.md`

把这次版本真正改了什么写进去。

最起码写：

- Added
- Changed
- Fixed

### 步骤 3：按清单检查

打开：

- `docs/RELEASE_CHECKLIST.md`

逐条确认：

- 能启动
- 关键功能能用
- 打包脚本没坏
- 没把运行时数据和秘密文件带进仓库

### 步骤 4：如果改了文档，先提交并推送

```powershell
git add CHANGELOG.md
git commit -m "Prepare changelog for v1.0.1"
git push origin main
```

### 步骤 5：创建 tag

例子：

```powershell
git tag v1.0.1
git push origin v1.0.1
```

### 步骤 6：到 GitHub 创建 Release

网页操作：

1. 打开仓库主页
2. 点右侧或顶部的 `Releases`
3. 点 `Draft a new release`
4. 选择刚才的 tag：`v1.0.1`
5. 标题可以写：

```text
GitSonar v1.0.1
```

6. 打开 `docs/RELEASE_NOTES_TEMPLATE.md`
7. 把模板复制到 Release 正文里
8. 按实际内容填好
9. 上传安装包和便携版
10. 点发布

## 场景 4：我要处理别人提的 Bug 或需求

### 看 issue

在 GitHub 仓库里点 `Issues`。

你已经有模板了：

- bug report
- feature request

所以别人提问题时，信息会比之前完整很多。

### 处理方法

如果是 bug：

1. 先确认能不能复现
2. 复现后开一个修复分支
3. 修完后合并回 `main`
4. 在 issue 里回复修复版本或提交号

如果是需求：

1. 先判断是不是值得做
2. 记录到 Roadmap 或 issue
3. 真要做，再开新分支处理

### issue 常见标签建议

你现在可以先用最简单的一套：

- `bug`
- `enhancement`
- `docs`
- `question`
- `release`

不用一开始把标签体系搞得太复杂。

## 场景 5：我要清理仓库

建议每周或每两周做一次。

### 清理本地已合并分支

先看分支：

```powershell
git branch
```

删除已经合并完的分支：

```powershell
git branch -d 分支名
```

### 清理远端已合并分支

```powershell
git push origin --delete 分支名
```

### 查看当前仓库是否干净

```powershell
git status
```

看到这种最理想：

```text
On branch main
nothing to commit, working tree clean
```

## 你最容易犯错的地方

## 1. 在 `main` 上直接乱改

风险：

- 改一半停住
- 很难回滚
- 多个改动混在一起

建议：

- 除了极小的文档修正，尽量都开分支

## 2. 没看 `git status` 就提交

风险：

- 把缓存、运行时文件、临时文件一起提交上去

建议：

- 每次 commit 前必须看一次 `git status`

## 3. 把不该公开的东西推到 GitHub

绝对不要提交：

- GitHub Token
- 代理账号密码
- 本地配置
- `%LOCALAPPDATA%` 里的运行时数据
- 打包出来的临时缓存
- 私有项目链接或敏感截图

## 4. 不写 changelog 就发版本

风险：

- 过几周以后你自己也不知道这版改了什么

建议：

- 发版前一定先更新 `CHANGELOG.md`

## 5. 分支合并后不删除

风险：

- 仓库看起来很乱
- 你自己以后也分不清哪些还在用

建议：

- 合并后立刻删本地和远端分支

## 遇到问题时怎么救

## 1. 我改乱了，但还没提交

先不要乱执行命令。

先看：

```powershell
git status
git diff
```

如果只是个别文件不想要了，再单独处理，不要随便全盘重置。

## 2. 我已经提交了，但还没推送

先看最近提交：

```powershell
git log --oneline --max-count 5
```

如果你不确定怎么撤销，先停下来，不要自己乱 `reset --hard`。

## 3. 我已经把敏感信息推上 GitHub 了

马上做两件事：

1. 立刻撤销或轮换那个密钥
2. 再考虑清理 git 历史

重点不是先删提交，而是先让密钥失效。

## 我建议你固定采用的工作习惯

每次做改动都按这个顺序：

```powershell
git switch main
git pull origin main
git switch -c feature/本次改动名
```

改完后：

```powershell
git status
git add 具体文件
git commit -m "一句话说明改动"
git push -u origin 当前分支名
```

合并时：

```powershell
git switch main
git pull origin main
git merge --ff-only 分支名
git push origin main
git branch -d 分支名
git push origin --delete 分支名
```

发版时：

```powershell
git switch main
git pull origin main
git tag v版本号
git push origin v版本号
```

然后到 GitHub 网页创建 Release。

## 给你的一条最重要建议

如果你不确定某个 Git 命令会不会破坏东西，先不要执行。

先做两件事：

```powershell
git status
git log --oneline --max-count 10
```

把结果看清楚，再继续。

很多仓库事故，都是因为在没看状态的情况下直接执行了危险命令。
