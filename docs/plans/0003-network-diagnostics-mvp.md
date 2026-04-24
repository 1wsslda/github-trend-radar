# 0003 - 网络诊断 MVP

## 任务元信息

- 任务 ID：`GS-P0-003`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 候选排名：`3`
- 推荐 commit message：`feat: 添加网络诊断 MVP`

## 摘要

- 问题：GitHub API、Token、代理、端口和本地运行环境出问题时，用户缺少统一诊断入口。
- 为什么现在做：这是高价值、低风险任务，能直接降低排障成本并解锁后续功能实现。
- 结果：提供一组可读、可脱敏、可操作的本地诊断结果。

## 战略映射

- 战略：在当前 Python + 本地 HTTP + 桌面壳上增量补齐排障能力，不引入远程诊断服务。
- 路线图：对应 `docs/roadmap/ROADMAP.md` 中当前 P0 任务，优先降低 Token / 代理 / API 排障成本。
- Sprint：对应 `docs/sprints/CURRENT_TOP10.md` 候选排名 `3`。

## 当前状态

- 已新增 `src/gitsonar/runtime/diagnostics.py`，统一产出本地诊断结果。
- 已新增 `GET /api/diagnostics`，并保持 loopback-only 与 control-token 保护。
- UI 在应用“更多”和设置面板中增加“运行诊断”入口，结果展示在本地 overlay。
- 诊断项覆盖运行目录权限、loopback 端口、状态文件、代理、GitHub Token、GitHub API 和 Trending 可达性。

## 目标

- 提供诊断入口与结果面板。
- 覆盖 GitHub API、Token、代理、loopback 端口、WebView / 浏览器壳层、状态文件权限等关键检查。
- 输出脱敏建议，不泄露 secret。

## 非目标

- 不自动修复用户网络环境。
- 不新增任何云诊断服务。
- 不改变当前本地优先边界。

## 范围

### 范围内

- 一键诊断入口
- 诊断结果结构
- 基础脱敏报告

### 范围外

- 持续后台监控
- 远程诊断上传
- 架构重写

## 架构触点

- 运行时模块：`runtime/http.py`、`runtime/settings.py`、`runtime/startup.py`
- GitHub 模块：`runtime_github/shared.py`
- UI：`runtime_ui/js/panels.py`、`runtime_ui/js/actions.py`

## 发布与回滚

- 发布方式：默认启用，本地生成，本机查看，不涉及用户数据外发。
- 回滚方式：移除 `runtime/diagnostics.py`、`/api/diagnostics` 路由以及模板中的诊断按钮 / overlay；不会影响已有 JSON 用户状态。
- 恢复路径：若上线后发现误判或噪音过高，可先回滚 UI 入口，再移除后端诊断实现。

## 验证

- 手动检查：
  - 有效 Token 场景
  - 无效 Token 场景
  - 代理配置错误场景
  - 本地端口占用场景
  - 诊断结果不泄露明文 secret

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-23` | `[~]` | 开始实现本地诊断运行时、HTTP 端点与 UI 入口。 |
| `2026-04-23` | `[x]` | 完成本地诊断 MVP，实现、测试和文档已同步。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`
- 手动验证：代码检查确认诊断输出为脱敏信息，并保持 loopback-only / control-token 保护。
- 尚未覆盖的缺口：未在真实无效代理、真实端口冲突环境下做端到端手测。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
