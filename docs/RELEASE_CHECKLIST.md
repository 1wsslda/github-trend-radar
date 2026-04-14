# Release Checklist

Use this checklist before cutting a public GitHub release.

## Scope

- Confirm which commits are included in the release.
- Confirm version number and release title.
- Confirm README screenshots and setup instructions still match the app.

## Product

- App launches normally on Windows.
- Main tabs load correctly.
- Search, filters, sort, and batch actions work.
- Detail drawer and compare drawer still open and render correctly.
- Settings can be opened, saved, and reopened.
- Tray hide and wake-up behavior still work.

## Networking

- GitHub access works in a normal network.
- Proxy flow still works if relevant changes were made.
- No token or secret values are printed into logs or bundled artifacts.

## Packaging

- `scripts/build_exe.ps1` completes.
- `scripts/build_setup.ps1` completes if installer changes are included.
- Output artifacts are placed under `artifacts/`.
- Installer metadata still matches app name and version.

## Repository

- `main` is clean and pushed.
- No runtime data, settings, caches, or secrets are tracked.
- Docs changed together with behavior changes.
- Release notes summarize what changed and any migration notes.

## Publish

- Create Git tag.
- Create GitHub Release.
- Upload installer and portable build if available.
- Paste concise release notes with user-facing changes first.
