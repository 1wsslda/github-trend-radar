# Protect Repo Details Endpoint Plan

## Task Metadata
- Task ID: `GS-P1-010`
- Priority: `P1`
- Current status: `[x]`
- Sprint candidate rank: `5`
- Recommended commit message: `fix(security): require control token for repo details`

## Summary
- Protect `/api/repo-details` because it can trigger GitHub requests, README processing, and cache writes.
- Keep frontend detail loading compatible via the existing control-token request helper.
- User-visible result: normal detail panels still load; unauthenticated local requests are rejected.

## Current State
- `/api/repo-details` is a GET route without loopback/control-token protection.
- Frontend already uses `requestJson()`, which attaches the control token.

## Goal
- Mark `/api/repo-details` as loopback-only and control-token-only.
- Preserve sanitized failure behavior.
- Add regression tests for missing token and normal success.

## Non-Goals
- No full read API control-token migration.
- No detail cache behavior changes.
- No frontend request helper rewrite.

## Scope
- Modify `src/gitsonar/runtime/http.py`.
- Cover with `tests/test_runtime_http.py`.

## Privacy / Opt-In Impact
- No new outbound data.
- Reduces unintended local network/cache side effects.

## Execution Steps
1. Add a failing HTTP test proving `/api/repo-details` currently works without a control token.
   Expected result: current response is not 403.
   Rollback: remove the test.
2. Add route protection.
   Expected result: missing token returns 403; normal token request returns 200.
   Rollback: remove route flags.
3. Run focused HTTP tests and full suite.
   Expected result: detail loading and existing route tests pass.
   Rollback: revert this task's files.

## Verification
- HTTP test: missing control token is rejected.
- HTTP test: token request still returns details.
- Manual check: open any repository detail; no-token request returns 403.

## Acceptance Checklist
- [x] `/api/repo-details` requires loopback.
- [x] `/api/repo-details` requires control token when configured.
- [x] frontend detail loading remains compatible.
- [x] verification results recorded.

## Progress Log
| Date | Status | Notes |
|---|---|---|
| `2026-04-24` | `[x]` | Added loopback/control-token protection for `/api/repo-details`. |

## Verification Record
- Tests run: focused security suite -> 83 passed, 4 subtests passed; full suite `python -m pytest -q` -> 192 passed, 157 subtests passed.
- Manual verification: not run in desktop UI during this pass.
- Gaps: manual repository detail panel check remains recommended before release.
