# Plan Template

Use this template before any complex feature, migration, or refactor.

---

## Title

`<short task title>`

## Summary

- What problem is being solved?
- Why now?
- What user-facing outcome should exist after this work?

## Strategy Mapping

- Strategy reference:
  - `docs/strategy/GITSONAR_STRATEGY.md`
- Roadmap reference:
  - `docs/roadmap/ROADMAP.md`
- Priority bucket:
  - `P0` / `P1` / `P2`
- Related current-state docs:
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`

## Current State

- Current behavior:
- Current technical shape:
- Known pain points:
- Existing constraints:
- Relevant code paths inspected:

## Goals

- Primary goal:
- Secondary goals:
- Success criteria:

## Non-Goals

- Explicitly state what this work will not do.
- State what migrations or redesigns are intentionally deferred.

## User Impact

- Who benefits?
- What changes in the UI or workflow?
- What remains unchanged?

## Privacy And Opt-In

- Does this touch AI, cloud APIs, sync, tokens, or user data?
- What data leaves the machine, if any?
- Is the feature opt-in?
- What user-visible consent or preview is required?

## Scope

### In Scope

- `<item>`

### Out Of Scope

- `<item>`

## Architecture Touchpoints

- Runtime modules involved:
- HTTP/API changes:
- State/persistence changes:
- UI changes:
- Background job changes:
- Packaging/startup/shell changes:

## Data Model

- New fields:
- New files or tables:
- Migration needs:
- Import/export implications:

## API And Contracts

- Endpoints to add/change:
- Request/response shape:
- Error behavior:
- Compatibility notes:

## Execution Plan

Break work into small, reversible steps.

1. Step 1:
   expected outcome:
   rollback path:
2. Step 2:
   expected outcome:
   rollback path:
3. Step 3:
   expected outcome:
   rollback path:

## Risks

- Technical risks:
- Product risks:
- Privacy/security risks:
- Rollout risks:

## Validation

- Unit tests:
- Integration tests:
- Manual checks:
- Performance or reliability checks:
- Logging/diagnostics to verify:

## Rollout

- How will this ship incrementally?
- What feature flags or guarded states are needed?
- How will users recover if the feature fails?

## Documentation Updates

- Docs to update:
- User-facing copy to update:
- Internal maintenance notes to update:

## Acceptance Checklist

- [ ] Scope is small and reversible
- [ ] No big-bang migration is hidden inside the task
- [ ] Privacy / opt-in behavior is explicit
- [ ] Rollback path is defined
- [ ] Validation steps are concrete
- [ ] Strategy and roadmap mapping are documented
