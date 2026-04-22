# GitSonar Roadmap

This roadmap is extracted from `docs/strategy/GITSONAR_STRATEGY.md` and is the default priority guide for follow-up implementation work.

## Execution Principles

- Keep GitSonar Windows-first, local-first, and privacy-first.
- Do not do big-bang rewrites.
- Prefer small, reversible steps with clear rollback points.
- Any AI, cloud API, sync, token, or user-data transmission must be opt-in by default.
- Any architecture migration must start with a written plan in `docs/plans/PLAN_TEMPLATE.md`.

## P0

Goal: strengthen the existing product loop without changing the stack.

Primary outcomes:

- Save discovery views so repeated research becomes persistent rather than one-off search.
- Add tags for long-term organization beyond the current four-state workflow.
- Add per-repo notes to preserve judgment and research context.
- Introduce `Update Inbox v1` on top of current update tracking.
- Show ranking / recommendation reasons so discovery is explainable.
- Add a diagnostics surface for GitHub API, token, proxy, local port, runtime state, and related failures.
- Keep Markdown export and external analysis handoff as a supported workflow.

P0 delivery rules:

- Stay on the current Python + local HTTP + desktop shell + embedded HTML/CSS/JS stack.
- Do not combine P0 with React, FastAPI, SQLite, or AI-provider migration work.
- Ship P0 as multiple small steps, not one large branch.

## P1

Goal: stabilize data flow, background workflows, and AI-ready interfaces after P0 proves the product model.

Primary outcomes:

- Move toward a static shell plus clearer JSON API boundaries.
- Introduce SQLite only after state model expansion is clear and migration is planned.
- Add a unified Job / Event model for long-running operations.
- Add SSE for progress and event push once the job model exists.
- Add `Repo Insight` and other structured AI outputs through explicit provider abstractions.
- Add AI artifact caching with deletion, regeneration, and opt-in visibility.
- Add discovery clustering and related structure that reduces cognitive load.

P1 delivery rules:

- Do not migrate persistence, API shape, and frontend rendering all at once.
- Do not ship AI as a default-on black box.
- Keep prompt handoff available while AI integration is still maturing.

## P2

Goal: add differentiated capabilities after the workflow, data model, and migration path are stable.

Primary outcomes:

- Repository map / visual clustering experiences.
- Optional local translation model support.
- Encrypted multi-device sync or backup flows.
- Packaging hardening, AV false-positive mitigation, and code signing.
- Longer-term frontend modernization only if earlier boundaries justify it.

P2 delivery rules:

- Do not prioritize visual novelty over research efficiency.
- Do not make cloud sync or AI mandatory.
- Do not introduce centralized account infrastructure as a default direction.

## Suggested Sequencing

1. P0 foundation:
   save discovery views, tags, notes, ranking reasons
2. P0 operations:
   diagnostics, Update Inbox v1, Markdown workflow polish
3. P1 architecture:
   plan-first API boundary cleanup, persistence migration design, job model
4. P1 intelligence:
   Repo Insight, AI artifacts, structured event delivery
5. P2 differentiation:
   clustering, map views, optional local models, encrypted sync, release hardening

## Out Of Scope By Default

These are not default next steps unless a dedicated plan says otherwise:

- full React rewrite
- immediate FastAPI rewrite
- immediate SQLite rewrite
- AI Agent orchestration
- centralized SaaS backend
- mandatory cloud sync

