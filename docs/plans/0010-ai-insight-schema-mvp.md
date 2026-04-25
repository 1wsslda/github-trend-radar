# 0010 - 结构化 AI Insight schema MVP

> 历史任务说明：本任务保持 `[x]`，但其运行时 UI/API/state 表面已由 `GS-P1-019` 取代。当前版本只保留 prompt handoff，不再维护手动结构化 Insight 保存工作流。

## 任务元信息

- 任务 ID：`GS-P1-001`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：`10`
- 推荐 commit message：`feat: 添加结构化 AI Insight schema MVP`

## 摘要

- 问题：当前 AI 相关能力更偏 prompt handoff，缺少稳定、结构化、可验证的 Insight 输出契约。
- 为什么现在做：这是后续 AI 集成的基础，但必须保持 opt-in 与本地优先边界。
- 结果：定义最小可用的 AI Insight Schema，为后续 provider 接入和缓存打基础。

## 战略映射

- 战略：只定义本地 schema、缓存和手动交接路径，不默认接入任何云端 provider。
- 路线图：对应 `docs/roadmap/ROADMAP.md` 中必须显式 opt-in 的 AI 基础能力。
- Sprint：对应 `docs/sprints/CURRENT_TOP10.md` 候选排名 `10`。

## 当前状态

- 已新增 `src/gitsonar/runtime/ai_insight.py`，定义 `gitsonar.repo_insight.v1` 和归一化规则。
- 历史上曾新增 legacy insight 状态字段，支持本地保存、删除和导入 / 导出兼容。
- 历史上曾新增 legacy insight 保存与删除端点。
- 详情面板曾提供 RepoContext payload 复制、结构化 Insight 手动粘贴保存、删除和本地展示入口。
- 当前不会自动调用云端 AI；所有外部模型使用都必须由用户显式复制出去并手动贴回。

## 目标

- 定义稳定的 AI Insight Schema。
- 保持 AI 能力显式 opt-in。
- 为后续缓存、展示和验证提供契约基础。

## 非目标

- 不默认接入云端 AI。
- 不做 AI Agent。
- 不强制引入新架构层。

## 范围

### 范围内

- Schema 设计
- 最小输入 / 输出契约
- 本地缓存与展示边界规划

### 范围外

- 完整 provider 实现
- 云端默认开启
- 复杂自治代理系统

## 架构触点

- HTTP：`runtime/http.py`
- 状态：`runtime/state.py`
- 记录与展示：`runtime/repo_records.py`
- 未来边界：`runtime_ai/`（如确需引入，需小步推进）

## 发布与回滚

- 发布方式：默认启用本地 schema 和缓存能力，但不默认开启任何云调用。
- 回滚方式：移除 legacy insight 状态字段、AI Insight API 和详情面板入口；现有 prompt handoff 路径不受影响。
- 恢复路径：若后续 schema 需要演进，可通过 `schema_version` 增量兼容，不做 big-bang 迁移。

## 验证

- 手动检查：
  - Schema 字段清晰
  - 可支持本地缓存与删除
  - 不破坏当前 prompt handoff 路径
  - 不引入默认云端外发

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-23` | `[~]` | 开始定义本地 schema、RepoContext 复制与手动缓存工作流。 |
| `2026-04-25` | `[x]` | 历史任务保持完成状态；运行时表面已由 `GS-P1-019` 取代。 |
| `2026-04-23` | `[x]` | 完成 AI Insight schema MVP，实现、测试和文档已同步。 |

## 验证记录

- 已运行测试：`python -m pytest tests/test_runtime_http.py tests/test_runtime_state.py tests/test_discovery_profiles.py tests/test_runtime_ui_assets.py -q`；`python -m pytest -q`
- 手动验证：代码检查确认 UI 明确标注“显式 opt-in”，当前只支持本地复制 / 粘贴，不会自动外发。
- 尚未覆盖的缺口：未在真实外部 AI 往返工作流上做人工验收；当前以 schema、状态和 UI 契约为主。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
