# 0006 - 更新收件箱 MVP

## 任务元信息

- 任务 ID：`GS-P0-006`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 候选排名：`6`
- 推荐 commit message：`feat: 添加更新收件箱 MVP`

## 摘要

- 问题：当前更新信息更像日志，而不是可处理的工作事项。
- 为什么现在做：用户需要把收藏仓库的变化转化成“下一步做什么”的本地队列。
- 结果：新增更新收件箱入口，支持最小处理动作。

## 战略映射

- 战略：在现有收藏更新能力上做增量处理动作，不提前引入 SSE 或新任务系统。
- 路线图：对应 `docs/roadmap/ROADMAP.md` 中高价值、低风险的收藏工作流增强项。
- Sprint：对应 `docs/sprints/CURRENT_TOP10.md` 候选排名 `6`。

## 当前状态

- 已为 `favorite_updates` 增加 `read_at`、`dismissed_at`、`pinned` 和 `priority_score`。
- 已新增 `/api/favorite-updates/state`，支持更新收件箱的最小处理动作。
- 更新卡片可执行标已读 / 标未读、置顶 / 取消置顶、忽略和复制摘要。
- 更新页会按置顶、未读、优先级和检查时间排序，标签页数字按未忽略待处理项统计。

## 目标

- 提供更新收件箱列表。
- 支持已读、忽略、置顶等最小动作。
- 与现有收藏更新能力兼容。

## 非目标

- 不引入 SSE。
- 不做复杂自动优先级模型。
- 不改后台作业架构。

## 范围

### 范围内

- 更新列表
- 已读 / 忽略 / 置顶
- 基础优先级呈现

### 范围外

- 实时推送
- 多端同步
- AI 自动总结

## 架构触点

- GitHub 更新：`runtime_github/favorites.py`
- 状态：`runtime/state.py`
- HTTP：`runtime/http.py`
- UI：`runtime_ui/js/panels.py`、`runtime_ui/js/cards.py`

## 发布与回滚

- 发布方式：默认启用，仍基于本地 `favorite_updates`，不改变后台刷新结构。
- 回滚方式：移除新状态字段、API 和卡片动作；旧更新数据仍保留为兼容列表。
- 恢复路径：若排序或处理动作不稳定，可先保留展示、回退交互动作，不需要数据迁移。

## 验证

- 手动检查：
  - 收件箱展示
  - 已读、忽略、置顶动作
  - 重启后状态保持

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-23` | `[~]` | 开始扩展更新状态字段、收件箱动作与排序规则。 |
| `2026-04-23` | `[x]` | 完成更新收件箱 MVP，实现、测试和文档已同步。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`
- 手动验证：代码检查确认更新页支持已读、置顶、忽略与摘要复制，多入口文案已同步。
- 尚未覆盖的缺口：未在真实收藏仓库更新数据上做端到端手测。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
