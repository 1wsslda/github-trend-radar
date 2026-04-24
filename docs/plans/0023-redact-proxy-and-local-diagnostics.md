# Redact Proxy And Local Diagnostics Plan

## Task Metadata
- Task ID: `GS-P0-010`
- Priority: `P0`
- Current status: `[x]`
- Sprint candidate rank: `1`
- Recommended commit message: `fix(security): redact proxy credentials from settings and diagnostics`

## Summary
- Prevent proxy credentials and local runtime paths from appearing in settings, bootstrap, and diagnostics payloads.
- Keep internal HTTP sessions using the original proxy URL.
- User-visible result: settings and diagnostics show only redacted proxy information and local status summaries.

## Current State
- `sanitize_settings()` exposes `effective_proxy` and `runtime_root`.
- diagnostics renders the effective proxy and runtime directory detail directly.
- UI settings and diagnostics panels render those API values.

## Goal
- Redact `user:pass` from any proxy URL returned to API/UI callers.
- Remove or summarize local runtime path details from API/UI payloads.
- Keep the raw proxy only inside runtime settings and `requests.Session.proxies`.

## Non-Goals
- No proxy storage migration.
- No global logging refactor.
- No frontend rewrite.

## Scope
- Modify `src/gitsonar/runtime/settings.py`.
- Modify `src/gitsonar/runtime/diagnostics.py`.
- Add a shared redaction helper under `src/gitsonar/runtime/`.
- Cover with settings and diagnostics tests.

## Privacy / Opt-In Impact
- No new outbound data.
- This reduces exposure of local configuration data.
- No user opt-in is required.

## Execution Steps
1. Add failing tests for credential-bearing proxy URLs in settings and diagnostics payloads.
   Expected result: tests fail because `user:pass` and runtime paths are currently present.
   Rollback: remove the new tests.
2. Implement shared redaction helpers.
   Expected result: returned API values are redacted while internal proxy use stays raw.
   Rollback: remove helper import and restore previous payload construction.
3. Update diagnostics runtime to use summaries rather than raw local paths.
   Expected result: diagnostics items do not include local filesystem paths.
   Rollback: restore prior diagnostics detail.
4. Run focused tests and full suite.
   Expected result: all targeted tests pass.
   Rollback: revert this task's files.

## Verification
- Unit tests: settings redaction and diagnostics redaction.
- Integration tests: bootstrap/settings payloads do not include `user:pass`.
- Manual check: configure `http://user:pass@host:port`, open settings and diagnostics, confirm only redacted values appear.

## Acceptance Checklist
- [x] Proxy credentials are absent from `/api/settings`.
- [x] Proxy credentials are absent from `/api/bootstrap`.
- [x] Proxy credentials and runtime paths are absent from diagnostics payloads.
- [x] Internal proxy use still receives the original URL.
- [x] Verification results recorded.

## Progress Log
| Date | Status | Notes |
|---|---|---|
| `2026-04-24` | `[x]` | Implemented shared redaction helper and settings/diagnostics sanitization. |

## Verification Record
- Tests run: focused security suite -> 83 passed, 4 subtests passed; full suite `python -m pytest -q` -> 192 passed, 157 subtests passed.
- Manual verification: not run in desktop UI during this pass.
- Gaps: manual proxy UI check remains recommended before release.
