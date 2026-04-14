# Contributing

Thanks for contributing to GitSonar.

## Before You Open An Issue

- Confirm you are using the latest release or the latest `main`.
- Check [docs/FAQ.md](docs/FAQ.md) and [docs/BUILD.md](docs/BUILD.md) first.
- If the issue is network-related, include whether you used a proxy and whether GitHub itself was reachable.
- Do not paste tokens, cookies, local proxy credentials, or private repository URLs.

## Before You Open A Pull Request

- Keep the scope narrow. One fix or one feature per PR is ideal.
- Use a short-lived branch instead of committing directly to `main`.
- Update docs when behavior, setup, packaging, or runtime paths change.
- Keep Windows packaging paths and runtime paths consistent with the repo layout.

## Development Notes

- Main app entry: `src/GitSonar.pyw`
- Package source: `src/gitsonar/`
- Build scripts: `scripts/`
- Installer config: `packaging/GitSonar.iss`

## Recommended Workflow

1. Branch from `main`.
2. Make the smallest useful change.
3. Run the most relevant check for your change.
4. Update docs if needed.
5. Open a PR with a clear summary and validation notes.

## Validation Expectations

Pick the checks that match your change:

- `python -m py_compile src\\gitsonar\\runtime_ui.py`
- App launch smoke test on Windows
- Packaging script smoke test when touching installer or build files
- Manual verification for UI, tray behavior, settings, and GitHub connectivity flows

## Security

- Never commit runtime data, local settings, tokens, or generated cache files.
- Treat anything under `%LOCALAPPDATA%` as local runtime state, not repository content.
- If you find a security issue, follow [docs/SECURITY.md](docs/SECURITY.md) instead of opening a public bug report.
