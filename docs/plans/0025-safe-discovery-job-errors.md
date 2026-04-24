# Safe Discovery Job Errors Plan

## Task Metadata
- Task ID: `GS-P1-008`
- Priority: `P1`
- Current status: `[x]`
- Sprint candidate rank: `3`
- Recommended commit message: `fix(security): sanitize discovery job failures`

## Summary
- Prevent discovery job failures from storing raw exception text in job `message` or `error`.
- Keep detailed failure information only in redacted local logs.
- User-visible result: failed search jobs show a safe actionable summary.

## Current State
- `discovery_jobs.py` stores `str(exc)` in job message and error.
- `/api/discovery/job` can return those raw strings.
- discovery UI displays job `error` or `message`.

## Goal
- Store a safe failure summary in job snapshots.
- Redact details in logs.
- Preserve cancellation behavior and normal progress payloads.

## Non-Goals
- No job runtime migration.
- No SSE or event model changes.
- No discovery ranking changes.

## Scope
- Modify `src/gitsonar/runtime/discovery_jobs.py`.
- Cover with `tests/test_discovery_jobs.py`.

## Privacy / Opt-In Impact
- No new outbound data.
- Reduces exposure of tokens, proxy credentials, paths, and backend internals in UI/API.

## Execution Steps
1. Add a failing discovery job test where the GitHub runtime raises sensitive exception text.
   Expected result: current job payload includes the sensitive text.
   Rollback: remove the test.
2. Implement safe discovery failure text and redacted logging.
   Expected result: job payload excludes the raw exception.
   Rollback: restore previous failure handling.
3. Run focused discovery job tests and full suite.
   Expected result: all targeted tests pass.
   Rollback: revert this task's files.

## Verification
- Unit test: failed job payload does not include token, proxy credentials, or paths.
- Manual check: trigger search failure and inspect discovery panel error text.

## Acceptance Checklist
- [x] Failed job `message` is safe.
- [x] Failed job `error` is safe.
- [x] Redacted local log preserves useful detail without secrets.
- [x] verification results recorded.

## Progress Log
| Date | Status | Notes |
|---|---|---|
| `2026-04-24` | `[x]` | Implemented safe discovery failure summary and redacted logging. |

## Verification Record
- Tests run: focused security suite -> 83 passed, 4 subtests passed; full suite `python -m pytest -q` -> 192 passed, 157 subtests passed.
- Manual verification: not run in desktop UI during this pass.
- Gaps: manual failed-search UI check remains recommended before release.
