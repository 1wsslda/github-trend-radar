# GS-P2-002 可选本地翻译模型支持（已取代）

> 本历史计划已被 `GS-P1-018` / `docs/plans/0036-openai-compatible-translation-api.md` 取代。

## 已取代说明

- 已取代：原计划实现的是 `local_ollama` / Ollama 风格的显式可选翻译路径。
- 新方向删除该运行时路径，保留默认 `google`，并新增显式 opt-in 的 `openai_compatible` 翻译 API。
- 历史任务状态不回写为未完成；`GS-P2-002` 仍表示当时的实现已完成。

## 新验收入口

- 新计划：`docs/plans/0036-openai-compatible-translation-api.md`
- 新任务：`GS-P1-018`
- 推荐 commit message：`feat(translation): use openai-compatible translation api`
