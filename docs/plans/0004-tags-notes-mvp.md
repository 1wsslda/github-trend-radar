# 0004 - 仓库标签 + 笔记 MVP

## 任务元信息

- 任务 ID：`GS-P0-004`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 候选排名：`4`
- 推荐 commit message：`feat: 添加仓库标签与笔记 MVP`

## 摘要

- 问题：当前四态系统不足以承载长期分类、判断依据和复查上下文。
- 为什么现在做：标签与笔记是保存用户判断的最小闭环，能直接提升整理效率。
- 结果：用户可以为仓库添加本地标签与笔记，并在后续工作流中复用。

## 战略映射

- 战略：保持当前 JSON 状态与本地优先边界，在现有运行时上做增量扩展。
- 路线图：对应 `docs/roadmap/ROADMAP.md` 的 P0 长期整理能力补齐项。
- Sprint：对应 `docs/sprints/CURRENT_TOP10.md` 候选排名 `4`。

## 当前状态

- 已在用户状态中新增 `repo_annotations`，保存标签、笔记和更新时间。
- 已新增 `/api/repo-annotations`，支持按仓库写入和清空本地标签 / 笔记。
- 详情面板可直接编辑标签和笔记，列表搜索、提示词构造和 Markdown 摘要会复用这些本地信息。
- 导入 / 导出路径保持 JSON 兼容，旧状态文件仍可正常读取。

## 目标

- 新增本地标签与笔记能力。
- 保持 JSON 状态兼容。
- 支持后续导入 / 导出与筛选扩展。

## 非目标

- 不做标签层级系统。
- 不做云同步。
- 不做 AI 自动写标签或笔记。

## 范围

### 范围内

- 标签增删改查
- 仓库笔记编辑与保存
- 基础 UI 入口

### 范围外

- 标签推荐
- 复杂批量管理
- 新数据库引入

## 架构触点

- 状态与持久化：`runtime/state.py`、`runtime/state_store.py`、`runtime/state_schema.py`
- HTTP / API：`runtime/http.py`
- UI：`runtime_ui/js/cards.py`、`runtime_ui/js/actions.py`、`runtime_ui/js/overlays.py`

## 发布与回滚

- 发布方式：默认启用，仅写入本地 JSON 状态，不引入新数据库或同步路径。
- 回滚方式：移除 `repo_annotations` 写入 / 读取逻辑与 UI 编辑入口；已有状态中的额外字段可被忽略或手动清理。
- 恢复路径：如需回滚到四态模型，只需停止消费 `repo_annotations`，不需要迁移脚本。

## 验证

- 手动检查：
  - 新增 / 编辑 / 删除标签
  - 保存 / 编辑笔记
  - 重启后数据仍在
  - 导出 / 导入兼容不破坏旧数据

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-23` | `[~]` | 开始扩展用户状态、API 与详情编辑入口。 |
| `2026-04-23` | `[x]` | 完成标签 / 笔记 MVP，实现、测试和文档已同步。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`
- 手动验证：代码检查确认详情编辑、搜索命中、提示词与 Markdown 摘要都会复用本地标签 / 笔记。
- 尚未覆盖的缺口：未做真实 UI 点击式手测；当前以状态、HTTP 和聚合 JS 断言为主。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
