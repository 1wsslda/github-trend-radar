# AI Artifact 生命周期与缓存计划

> 历史任务说明：本任务保持 `[x]`，但其运行时 UI/API/state 表面已由 `GS-P1-019` 取代。当前版本只保留 prompt handoff，不再维护手动结构化 Insight artifact 缓存。

## 任务元信息

- 任务 ID：`GS-P1-006`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：5
- 推荐 commit message：`feat: extend local ai artifact lifecycle`

## 标题

AI Artifact 生命周期与缓存

## 摘要

- 这个任务扩展当前本地 AI Insight 缓存，让 artifact 有更明确的来源、输入 hash、更新时间、列表和删除边界。
- 现在做是因为 `GS-P1-001` 已有本地 schema 和手动保存 / 删除流程，后续 provider 接入前需要先稳住本地生命周期。
- 做完后用户数据仍只在本机，应用可以列出本地 AI artifacts 并按仓库删除。

## 战略映射

- 战略文档：`docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：`docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：`docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：`docs/ARCHITECTURE.md`、`docs/SECURITY.md`

## 当前状态

- 当前行为：历史版本曾在 `user_state.json` 中保存 legacy insight 字段，支持手动保存和删除。
- 当前技术形态：`runtime/ai_insight.py` 负责 schema normalize，`state_store.py` 负责写入。
- 已知痛点：artifact 缺少稳定 id/input_hash/source metadata，列表 API 也不明确。
- 现有约束：不接入云 provider，不自动调用 AI。
- 需要检查的文件或区域：`runtime/ai_insight.py`、`runtime/state_schema.py`、`runtime/state_store.py`、`runtime/http.py`。

## 目标

- 主要目标：增强本地 AI artifact 元数据，新增列表读取 API。
- 次要目标：保存时保留手动 provider 和 schema 兼容。
- 成功标准：测试覆盖 normalize、保存、列表和删除。

## 非目标

- 不调用 OpenAI、本地 AI 服务或任何云 API。
- 不自动生成 AI 内容。
- 不改变用户现有手动 prompt 工作流。

## 隐私与显式同意

- 不外发数据。
- 不需要新的 opt-in，因为不引入 provider。
- 后续 provider 接入必须另行计划并显示字段预览。

## 范围

### 范围内

- 增加 `artifact_id`、`artifact_type`、`input_hash`、`source_snapshot_id` 等本地元数据。
- 历史上新增 legacy artifact 只读列表。
- 历史上保持 legacy insight 保存 / 删除兼容。

### 范围外

- Provider 抽象实现。
- 批量生成、重新生成和模型配置。
- AI 输出 UI 大改。

## 架构触点

- 运行时模块：`runtime/ai_insight.py`、`runtime/state_schema.py`、`runtime/state_store.py`、`runtime/http.py`
- HTTP / API 变更：历史上新增只读 artifact 列表端点
- 状态 / 持久化变更：历史 legacy insight 状态字段元数据向后兼容
- UI 变更：无
- 后台任务变更：无

## 执行步骤

1. 写 state 和 HTTP 测试覆盖 artifact metadata/list。
   预期结果：测试先失败。
   回滚路径：删除测试。
2. 扩展 `normalize_ai_insight`。
   预期结果：旧 payload 仍可 normalize，新字段稳定输出。
   回滚路径：恢复旧 schema 字段。
3. 增加列表 API。
   预期结果：可读取本地 artifact 列表但不外发。
   回滚路径：删除路由。

## 风险

- 技术风险：破坏旧 legacy insight 兼容。测试必须覆盖旧 payload。
- 产品风险：列表 API 暂未 UI 消费。作为 provider 前置边界。
- 隐私 / 安全风险：不能把 prompt 或敏感 Token 写入 artifact 元数据。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_state.py tests/test_runtime_http.py -q`
- 集成测试：`python -m pytest -q`
- 手动检查：确认没有新增外部网络调用。

## 发布与回滚

- 增量发布：新增兼容字段和只读列表。
- 回滚：删除新增字段和路由，旧 `summary` 等字段仍可读取。

## 文档更新

- 更新 `TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已扩展本地 AI artifact 元数据和只读列表 API。 |
| `2026-04-25` | `[x]` | 历史任务保持完成状态；运行时表面已由 `GS-P1-019` 取代。 |
| `2026-04-24` | `[~]` | 开始 AI Artifact 生命周期与缓存增强，先写失败测试。 |
| `2026-04-24` | `[ ]` | Auto Top 5 Batch Sprint 选中，等待执行。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_state.py tests/test_runtime_http.py -q`，49 passed，4 subtests passed；本批最终 `python -m pytest -q`，173 passed，145 subtests passed。
- 手动验证：确认本任务没有新增外部网络调用，历史 artifact 列表端点仍要求 loopback/control token。
- 尚未覆盖的缺口：provider 接入、自动重生成和 UI 列表消费留给后续任务。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
