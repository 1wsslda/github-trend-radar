# Safe Refresh Status Errors Plan

## Task Metadata
- Task ID: `GS-P0-011`
- Priority: `P0`
- Current status: `[x]`
- Sprint candidate rank: `2`
- Recommended commit message: `fix(security): keep refresh status errors user safe`

## Summary
- Prevent refresh exceptions from being persisted to `status.json` or shown through `/api/status`.
- Keep detailed error information only in redacted local logs.
- User-visible result: refresh failures show a generic actionable message.

## Current State
- `refresh_once_safe()` writes `str(exc)` to status.
- `start_refresh_async()` writes thread-start exceptions to status.
- frontend polling displays `data.error`.

## Goal
- Persist only a safe refresh failure message.
- Redact details in logs.
- Avoid frontend direct display of raw legacy `data.error` status details.

## Non-Goals
- No global exception handling rewrite.
- No log file transport changes.
- No retry scheduler changes.

## Scope
- Modify `src/gitsonar/runtime/app.py`.
- Modify status sanitization in local API/bootstrap path as needed.
- Modify `src/gitsonar/runtime_ui/js/actions.py` for safe status polling text.
- Cover with app/http/UI smoke tests.

## Privacy / Opt-In Impact
- No new outbound data.
- Reduces accidental local detail and secret exposure.

## Execution Steps
1. Add a failing app test where refresh raises an exception containing token, proxy credentials, and a local path.
   Expected result: current status write contains raw details.
   Rollback: remove the test.
2. Add a failing status API/UI test for safe status error display.
   Expected result: current response or poll body uses raw `data.error`.
   Rollback: remove the test.
3. Implement safe status error text and redacted logging.
   Expected result: status and UI text are generic; logs keep redacted details.
   Rollback: restore previous `str(exc)` writes.
4. Run focused tests and full suite.
   Expected result: all targeted tests pass.
   Rollback: revert this task's files.

## Verification
- Unit tests: refresh failure writes safe status text.
- HTTP tests: `/api/status` does not return sensitive legacy error text.
- UI smoke: polling no longer directly uses `data.error` as the displayed note.

## Acceptance Checklist
- [x] `/api/status` does not expose token, proxy credentials, or local paths.
- [x] status file writes safe user text for refresh failures.
- [x] detailed log message is redacted.
- [x] verification results recorded.

## Progress Log
| Date | Status | Notes |
|---|---|---|
| `2026-04-24` | `[x]` | Implemented safe refresh status text, status payload sanitization, and UI polling fallback. |

## Verification Record
- Tests run: focused security suite -> 83 passed, 4 subtests passed; full suite `python -m pytest -q` -> 192 passed, 157 subtests passed.
- Manual verification: not run in desktop UI during this pass.
- Gaps: manual forced-refresh failure check remains recommended before release.
