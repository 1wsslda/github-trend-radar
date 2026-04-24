# JSON Body Size Limit Plan

## Task Metadata
- Task ID: `GS-P1-009`
- Priority: `P1`
- Current status: `[x]`
- Sprint candidate rank: `4`
- Recommended commit message: `fix(security): limit local JSON request bodies`

## Summary
- Add a conservative request body limit for local JSON POST APIs.
- Return a stable `413 payload_too_large` response when exceeded.
- User-visible result: normal settings/import/export paths keep working, oversized bodies are rejected predictably.

## Current State
- `read_json()` trusts `Content-Length` and reads that many bytes.
- All JSON POST routes share this parser.

## Goal
- Enforce a single max JSON body byte limit.
- Keep invalid JSON behavior unchanged.
- Keep normal small JSON requests compatible.

## Non-Goals
- No streaming import/export redesign.
- No per-route body limits.
- No compression support.

## Scope
- Modify `src/gitsonar/runtime/http.py`.
- Cover with `tests/test_runtime_http.py`.

## Privacy / Opt-In Impact
- No new outbound data.
- Reduces local denial-of-service risk.

## Execution Steps
1. Add a failing HTTP test for oversized JSON body.
   Expected result: current code reads it and returns a non-413 response.
   Rollback: remove the test.
2. Implement max size and `PayloadTooLargeError`.
   Expected result: oversized body returns 413 with code `payload_too_large`.
   Rollback: remove the new error and size check.
3. Confirm normal JSON body regression still passes.
   Expected result: existing settings/import/Markdown tests remain green.
   Rollback: revert this task's files.

## Verification
- HTTP test: oversized body returns 413.
- Existing HTTP tests: settings save, import, Markdown export still pass.

## Acceptance Checklist
- [x] Oversized JSON POST returns `413`.
- [x] Response code is `payload_too_large`.
- [x] Normal JSON POST tests pass.
- [x] verification results recorded.

## Progress Log
| Date | Status | Notes |
|---|---|---|
| `2026-04-24` | `[x]` | Implemented shared JSON body limit and `payload_too_large` response. |

## Verification Record
- Tests run: focused security suite -> 83 passed, 4 subtests passed; full suite `python -m pytest -q` -> 192 passed, 157 subtests passed.
- Manual verification: not run in desktop UI during this pass.
- Gaps: normal import/export manual smoke remains recommended before release.
