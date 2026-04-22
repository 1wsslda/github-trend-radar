# GitSonar Working Guide

This file is the project-level execution basis for Codex and future contributors.

## Project Reality

- GitSonar is currently a Windows-native desktop application.
- The current runtime shape is: Python runtime + local HTTP service + desktop browser/WebView shell + embedded HTML/CSS/JS.
- The current codebase is organized around:
  - `src/gitsonar/runtime/`
  - `src/gitsonar/runtime_github/`
  - `src/gitsonar/runtime_ui/`

## Source Of Truth

Before proposing or implementing substantial work, read these files first:

1. `docs/strategy/GITSONAR_STRATEGY.md`
2. `docs/roadmap/ROADMAP.md`
3. `docs/plans/PLAN_TEMPLATE.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SECURITY.md`

Use them this way:

- `GITSONAR_STRATEGY.md`: product and architecture direction
- `ROADMAP.md`: current P0 / P1 / P2 priorities
- `PLAN_TEMPLATE.md`: required structure for complex feature plans and migration plans
- `ARCHITECTURE.md`: current code and runtime shape
- `SECURITY.md`: privacy, token, storage, and network boundary

If strategy and current code diverge, do not force the code to match the strategy in one step. Prefer small, reversible changes that move the codebase toward the strategy.
Unless a user explicitly says otherwise, treat the current workspace contents as the source of truth regardless of prior git modification state. Do not discount or down-rank a file just because it was already modified before the current task.

## Hard Constraints

- Do not rewrite the app into React / FastAPI / SQLite / AI Agent in one step.
- Do not perform big-bang migrations.
- Keep the product local-first and privacy-first by default.
- Any AI, cloud API, sync, token, or user-data transmission must be explicit opt-in.
- Any architecture migration must start with a written execution plan using `docs/plans/PLAN_TEMPLATE.md`.
- Prefer small, rollback-friendly iterations with clear checkpoints.
- Preserve Windows-first desktop behavior unless a task explicitly expands platform scope.

## Implementation Policy

When working on GitSonar:

- Prefer extending the current runtime incrementally over introducing a new stack.
- Keep business logic out of `runtime_ui/assets.py`, `runtime_github/__init__.py`, and other aggregator files.
- Treat `runtime/app.py` as an orchestration layer, not a dumping ground for new domain logic.
- Keep HTTP, GitHub, state, startup, shell, and UI concerns separated by the existing package boundaries.
- When adding persistence or background workflows, design for import/export and rollback from the beginning.

## Planning Rules

You must write or update a plan document before:

- architecture migrations
- persistence migrations
- introducing new background job systems
- introducing AI providers or cloud integrations
- changing privacy or sync boundaries
- major UI navigation or workflow rewrites

The plan must:

- define current state and target state
- explain why the migration is needed
- break work into small reversible steps
- define rollback strategy
- define test and verification steps
- identify privacy / opt-in implications

## Default Delivery Style

Prefer work in this order:

1. clarify the user-facing outcome
2. identify the smallest compatible change
3. add or update tests where appropriate
4. update docs when behavior or architecture meaningfully changes

For complex work, do not jump straight into implementation. First produce a concrete plan document using `docs/plans/PLAN_TEMPLATE.md`.
