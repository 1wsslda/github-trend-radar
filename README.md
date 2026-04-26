# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**Stop losing useful repositories in an endless Star list. GitSonar turns GitHub discovery into a local research workflow: find projects, sort leads, record judgment, and track what changes.**

`Windows` · `local-first` · `no account` · `GitHub token optional` · `MIT`

[Download GitSonar](https://github.com/1wsslda/github-trend-radar/releases) · [Read the security boundary](docs/SECURITY.md) · [Run from source](#development)

![GitSonar Screen](assets/screenshots/trending.png)

If you regularly check GitHub Trending, search for competing projects, and collect more Stars than you can actually revisit, GitSonar is built for the workflow after discovery: why a repo looked useful, whether it changed later, and how it compares with the next option.

It is not a GitHub client replacement and it is not a cloud SaaS. It is a Windows desktop workspace that combines trend discovery, keyword discovery, local states, tags, notes, an Update Inbox, repo comparison, Markdown export, and explicit AI prompt handoff.

## Why Try It

| Problem | What GitSonar does |
|---|---|
| Trending is easy to browse but hard to revisit | Turn candidates into a queue with `Follow / Watch Later / Read / Ignore`. |
| Star counts are too shallow for real decisions | Review recommendation reasons, ranking signals, local clusters, and a lightweight repo map. |
| Technical selection means reopening the same repos repeatedly | Read README summaries, topics, license, and homepage metadata in the detail drawer, then compare two repos side by side. |
| Followed projects change, but most updates are noise | Use the Update Inbox to triage push, star / fork, and release changes by read, pinned, dismissed, and priority states. |
| AI can help, but repo context should not be uploaded by default | Filter locally first, add tags and notes, then explicitly copy a prompt or hand it to ChatGPT / Gemini. |

## 60-Second Workflow

1. Open daily / weekly / monthly trends, or run keyword discovery in Chinese or English.
2. Review recommendation reasons, clusters, and the repo map, then mark useful repos as `Follow` or `Watch Later`.
3. Add tags and notes in the detail drawer: why it matters, risks, fit, and next validation steps.
4. Use the Update Inbox to revisit releases, activity changes, and star / fork movement across followed repos.
5. Compare two similar projects side by side, then export Markdown into notes, PRDs, technical proposals, or external AI tools.

## Who It Is For

- Developers who check GitHub Trending and want good finds to survive beyond the first browse.
- Product people, researchers, and builders doing technical selection or competitive research.
- Heavy open-source users who need to track changes across a curated repo list.
- People who search with Chinese or English keywords and want a repeatable discovery trail.
- Users who want to hand curated repo context to ChatGPT or Gemini only after local filtering.

## Core Capabilities

### Discovery Signals

- Browse daily / weekly / monthly GitHub Trending.
- Discover repositories with Chinese or English keywords.
- Save discovery views and load or rerun them later.
- Review recommendation reasons, ranking signals, local clusters, and a lightweight 2D repo map.

### Candidate Workspace

- Manage repo states with `Follow / Watch Later / Read / Ignore`.
- Add tags, notes, and ignore reasons.
- Run batch marking, analysis, or export actions on the current filtered set.
- Import and export local state for backup and migration.

### Change Tracking

- Track push, star / fork, and release changes for followed repos in the Update Inbox.
- Triage updates with read, pinned, dismissed, and priority states.
- See local change summaries, importance reasons, and since-last-viewed hints.
- Use it to find important changes in your curated watchlist, not to replace every GitHub notification.

### Compare, Export, and AI Handoff

- Read README summaries, topics, license, and homepage metadata in the detail drawer.
- Compare two similar repos side by side.
- Export single-repo, batch, or comparison Markdown summaries.
- ChatGPT / Gemini actions are explicit prompt handoffs; GitSonar does not call an embedded AI provider by default.

## Screenshots

**Discover projects: trends, filters, recommendation reasons, and batch actions**

![GitSonar Screen](assets/screenshots/trending.png)

**Organize candidates: local states, tags, notes, and batch management**

![State Management](assets/screenshots/favorites.png)

**Make decisions: detail drawer, README summary, and repo metadata**

![Repo Detail](assets/screenshots/detail.png)

## Download and Verify

Download from [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases):

- Installer: `GitSonarSetup.exe`
- Portable app: `GitSonar.exe`
- Verification files: `SHA256SUMS.txt` and `release-manifest.json`

There is currently no auto-update and no code signing. Windows SmartScreen may warn before launch; verify the download source and SHA256 files from the release page before running.

You can start without a GitHub token. Token-free usage supports trend browsing and local organization; configuring a token makes GitHub API access, GitHub Star sync, and followed-repo update tracking more reliable.

## Privacy and Boundaries

- GitSonar is a local desktop tool with no project-owned SaaS backend and no account system.
- Packaged app data lives under `%LOCALAPPDATA%\GitSonar`; development runs use `runtime-data/` in the repository.
- The local HTTP service binds to `127.0.0.1` by default, and business endpoints plus read-only JSON APIs require loopback and a runtime control token.
- GitHub tokens and proxy URLs with credentials are stored locally with Windows DPAPI.
- Current network destinations may include GitHub and Google Translate. Optional OpenAI-compatible translation only runs after you explicitly enable it and configure Endpoint, Model, and API Key.
- ChatGPT / Gemini actions only open external targets or copy prompts after you click them.
- There is no default cloud sync, default backup upload, code signing, or auto-update yet.

See [docs/SECURITY.md](docs/SECURITY.md) for the exact security boundary.

## Current Implementation Status

- JSON files remain the fact storage. SQLite has a migration design and dry-run skeleton, but runtime storage has not switched.
- AI-related features are prompt handoff and Markdown summary export, not a default embedded AI provider or in-app model-generated conclusions.
- Frontend modernization has a staged roadmap that starts with low-risk React islands and a modern asset pipeline, not a big rewrite.
- Encrypted backup / sync, code signing, and auto-update remain future roadmap items.

## Development

Requirements:

- Windows
- Python 3.12+

Run from source:

```powershell
python -m pip install -r requirements.txt
python src/gitsonar/__main__.py
```

Build the portable EXE:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

Build the installer:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_setup.ps1
```

One-click packaging:

```cmd
scripts\build_all_click.cmd
```

Write release checksums:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\write_release_manifest.ps1
```

Verify:

```powershell
python scripts\verify_runtime.py
python -m pytest -q
```

## Docs

- [docs/strategy/GITSONAR_STRATEGY.md](docs/strategy/GITSONAR_STRATEGY.md)
- [docs/roadmap/ROADMAP.md](docs/roadmap/ROADMAP.md)
- [docs/plans/PLAN_TEMPLATE.md](docs/plans/PLAN_TEMPLATE.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [CHANGELOG.md](CHANGELOG.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

## License

This project is released under the [MIT License](LICENSE).
