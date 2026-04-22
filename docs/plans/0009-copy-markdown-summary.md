# 0009 - 复制仓库 Markdown 摘要

## 任务元信息

- 任务 ID：`GS-P0-009`
- 优先级：`P0`
- 当前状态：`[x]`
- Sprint 排名：`9`
- 推荐 commit message：`feat: 添加仓库 Markdown 摘要复制功能`

## 摘要

- 问题：用户缺少一个低摩擦方式，把仓库信息快速带到外部分析、笔记或 AI 工作流。
- 为什么现在做：这是低风险、容易验证的实用功能。
- 结果：用户可以一键复制仓库 Markdown 摘要。

## 战略映射

- 战略：继续保留本地优先和外部分析工作流，不引入新的分享服务或同步边界。
- 路线图：对应 `docs/roadmap/ROADMAP.md` 的低风险高价值效率增强项。
- Sprint：对应 `docs/sprints/CURRENT_TOP10.md` 排名 `9`。

## 当前状态

- 已新增 `buildRepoMarkdownSummary()`，复用仓库详情、README 摘要、本地标签和笔记生成标准 Markdown。
- 仓库卡片、更新卡片和详情面板都提供“复制 Markdown 摘要”入口。
- 复制动作优先拉取详情数据，确保摘要包含 README、topics、最近推送时间等关键信息。
- 未引入文件同步或云分享；仍由用户自行决定后续粘贴到哪里。

## 目标

- 提供一键复制 Markdown 摘要。
- 复用现有仓库详情数据。
- 保持本地工作流顺畅。

## 非目标

- 不做复杂导出向导。
- 不新增云剪贴板。
- 不引入新的存储层。

## 范围

### 范围内

- 生成 Markdown 摘要
- 复制入口
- 基础格式约定

### 范围外

- 批量高级导出
- 文件同步
- 新格式设计系统

## 架构触点

- 数据：`runtime/repo_records.py`
- HTTP：`runtime/http.py`
- UI：`runtime_ui/js/actions.py`、`runtime_ui/js/cards.py`

## 发布与回滚

- 发布方式：默认启用，仅增加本地字符串拼装和剪贴板复制入口。
- 回滚方式：移除摘要生成函数和 UI 按钮，不影响既有详情 / 分析逻辑。
- 恢复路径：若摘要格式后续需要调整，可保持入口不变，仅替换 Markdown 模板。

## 验证

- 手动检查：
  - 生成 Markdown 摘要
  - 复制到剪贴板
  - 外部粘贴格式正确

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-23` | `[~]` | 开始补齐仓库 Markdown 摘要生成和多入口复制动作。 |
| `2026-04-23` | `[x]` | 完成 Markdown 摘要复制 MVP，实现、测试和文档已同步。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`
- 手动验证：代码检查确认摘要会带上 README、tags、note，且多入口动作都复用同一份生成逻辑。
- 尚未覆盖的缺口：未在真实浏览器剪贴板中逐项粘贴校验格式。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
