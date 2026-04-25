# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**GitSonar is a Windows, local-first GitHub intelligence desk for discovering repositories, organizing leads, tracking changes, and making better open-source decisions.**

![GitSonar Screen](assets/screenshots/trending.png)

GitSonar is not just a GitHub Trending viewer. It is a desktop workflow for people who repeatedly scout, compare, and follow open-source projects. It combines trend discovery, keyword discovery, local states, tags, notes, an Update Inbox, repo details, side-by-side comparison, Markdown exports, and AI prompt handoff.

## Highlights

| Capability | What you can do |
|---|---|
| **Trends and keyword discovery** | Browse daily / weekly / monthly trends, search by keywords, save discovery views, and rerun them later. |
| **Explainable ranking** | See recommendation reasons, ranking signals, local clusters, and a lightweight repo map instead of judging only by stars. |
| **Local research workspace** | Sort repos with `Follow / Watch Later / Read / Ignore`, then add tags, notes, ignore reasons, batch actions, and import / export. |
| **Update Inbox** | Track push, star / fork, and release changes for followed repos, then mark updates as read, pinned, dismissed, or priority. |
| **Details, compare, and export** | Read README summaries, topics, license, homepage metadata, compare two repos, and export Markdown summaries. |
| **Privacy-first desktop model** | Data stays local by default. GitHub tokens and proxy credentials are encrypted with Windows DPAPI; local APIs use loopback and a runtime control token. |

## Who It Is For

- Developers who check GitHub Trending but want to keep and revisit good finds.
- Product people, researchers, and builders doing technical selection or competitive research.
- Heavy open-source users who need to track changes across a curated repo list.
- People who search with Chinese or English keywords and want a repeatable discovery workflow.
- Users who want to hand curated repo context to ChatGPT or Gemini only after local filtering.

## Quick Start

### 1. Download and Run

Download from [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases):

- Installer: `GitSonarSetup.exe`
- Portable app: `GitSonar.exe`
- Verification files: `SHA256SUMS.txt` and `release-manifest.json`

There is currently no auto-update and no code signing. Windows SmartScreen may warn before launch; verify the download source and SHA256 before running.

### 2. First-Time Setup

Open Settings and configure what you need:

- `GitHub Token`: recommended for long-term use, GitHub Star sync, and more stable GitHub API access.
- `Proxy`: useful when your network cannot reliably reach GitHub.
- `Refresh interval`: controls background refresh frequency.
- `Result limit`: controls trend and discovery list size.
- `Translation provider`: Google is the default path. OpenAI-compatible translation requires explicit opt-in plus Endpoint, Model, and API Key.

You can use GitSonar without a token for trend browsing and local organization. Token-free usage has less stable API access and limited Star sync / update tracking.

### 3. Discover Repositories

1. Switch between daily, weekly, and monthly trends.
2. Use search, language, state, and sort controls to narrow the list.
3. Run keyword discovery with Chinese or English queries such as `local AI tools`, `terminal ui`, or `data visualization`.
4. Review recommendation reasons, clusters, and the repo map.
5. Save useful discovery views so you can load or rerun them later.

### 4. Organize Candidates

Use local workflow states:

- `Follow`: worth tracking over time.
- `Watch Later`: interesting but not decided yet.
- `Read`: already reviewed.
- `Ignore`: not relevant. You can record an ignore reason to reduce future noise.

Open the detail drawer to add tags and notes, for example:

- Tags: `ai-agent`, `cli`, `database`, `try-next`
- Notes: why it matters, risks, fit, and next validation steps

States, tags, and notes are stored locally and can be exported or imported.

### 5. Track Updates

Use the Update Inbox to review followed repo changes:

- Push activity
- Star / fork changes
- New releases
- Local change summaries
- Importance reasons
- Since-last-viewed indicators

You can mark updates as read, pin important ones, dismiss noise, and process the list by priority. The goal is not to replace GitHub notifications; it is to identify which changes matter inside your curated watchlist.

### 6. Read, Compare, and Decide

A common judgement path:

1. Open repo details and review description, language, topics, license, homepage, and README summary.
2. Add tags and notes.
3. Compare two similar repos side by side.
4. Export single-repo, batch, or comparison Markdown summaries.
5. Send the curated context to ChatGPT / Gemini, or copy the prompt into your own workflow.

GitSonar does not call an embedded AI provider by default. AI-related features are prompt handoff actions that only run when you click them.

## Common Workflows

### Daily Open-Source Radar

1. Open daily trends.
2. Filter by language and sort mode.
3. Mark a few repos as Follow or Watch Later.
4. Add tags to important repos.
5. Check the Update Inbox later for releases or activity changes.

### Technical Selection Shortlist

1. Run keyword discovery for a domain such as `vector database` or `workflow engine`.
2. Save the discovery view.
3. Tag candidates as `mature`, `lightweight`, or `risk-to-check`.
4. Compare the two closest options.
5. Export Markdown into a note, PRD, or technical proposal.

### AI-Assisted Review

1. Filter repos locally first.
2. Add tags and notes.
3. Open single-repo, batch, or comparison analysis.
4. Send the prompt to ChatGPT / Gemini or copy it.
5. Keep GitHub tokens, proxy credentials, and local paths out of the AI payload.

## UI Guide

### Trends

- Daily / weekly / monthly tabs switch the Trending period.
- Search and filters narrow repos by name, description, language, and local state.
- Sort modes help you inspect stars, growth, update signals, and recommendation signals.
- Batch actions let you mark, analyze, or export the current result set.

### Keyword Discovery

- Chinese queries are translated to English according to the current translation settings.
- Discovery runs as a background job with progress and cancellation.
- Results include recommendation reasons, clusters, and a repo map.
- Saved discovery views can be loaded, rerun, or deleted.

### Follow List

- The GitSonar follow list is a local workflow state, not the same thing as a GitHub Star.
- With a GitHub token configured, marking a repo as Follow will try to sync a GitHub Star.
- Existing GitHub Stars can also be imported into the local follow list.
- Tags, notes, filters, and batch actions keep the list useful over time.

### Update Inbox

- Shows push, star / fork, and release changes for followed repos.
- Supports read, pinned, dismissed, and priority states.
- Local summaries and importance reasons help you decide what to open.
- Designed for periodic triage rather than one notification per event.

### Details and Compare

- The detail drawer shows README summary, topics, license, homepage, and related metadata.
- Tags and notes are edited in the detail drawer.
- Comparison view is useful when two repos solve a similar problem.
- Markdown exports are designed for notes, PRDs, technical proposals, and external AI tools.

### Settings and Diagnostics

- Settings cover GitHub Token, proxy, refresh interval, result limit, translation provider, and auto start.
- Diagnostics check runtime directories, port, proxy, token status, GitHub reachability, and related signals.
- Diagnostic output is redacted and should not expose raw tokens, proxy credentials, or local absolute paths.

## Screenshots

**Main workspace: trends, filters, and batch analysis**

![GitSonar Screen](assets/screenshots/trending.png)

**Follow list: local states and batch actions**

![State Management](assets/screenshots/favorites.png)

**Repo detail drawer: reading and README summary**

![Repo Detail](assets/screenshots/detail.png)

## Current Boundaries

### AI Boundary

Implemented:

- ChatGPT / Gemini prompt handoff
- Copy-only prompts
- Single-repo, batch, and comparison context preparation

Not implemented:

- Default embedded AI provider
- In-app model-generated conclusions
- OpenAI-compatible AI analysis provider pipeline
- Manual structured Insight cache workflow

OpenAI-compatible support currently applies only to the optional translation provider. It is not an embedded AI analysis feature.

### Storage Boundary

- JSON files remain the fact storage.
- SQLite has a migration design and dry-run skeleton, but runtime storage has not switched.
- Packaged app data lives under `%LOCALAPPDATA%\GitSonar`.
- Development runs use `runtime-data/` in the repository.
- Legacy `%LOCALAPPDATA%\GitHubTrendRadar` data is merged on first run when needed.

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

## Security and Privacy

- GitSonar is a local desktop tool with no project-owned SaaS backend.
- The local HTTP service binds to `127.0.0.1` by default.
- Business, state, diagnostics, export, event, and read APIs require loopback plus a runtime control token.
- GitHub tokens and proxy URLs with credentials are stored locally with Windows DPAPI.
- Current network destinations may include GitHub and Google Translate. Optional OpenAI-compatible translation is explicit opt-in and only uses the endpoint you configure.
- ChatGPT / Gemini actions only open external targets or copy prompts after you click them.
- There is no default cloud sync, default backup upload, code signing, or auto-update yet.

See [docs/SECURITY.md](docs/SECURITY.md) for the exact security boundary.

## Roadmap

Remaining planned work:

- **SQLite runtime cutover**: import / export and controlled storage switching after the dry-run skeleton.
- **AI provider implementation**: settings, privacy preview, local / cloud execution, and result confirmation from the opt-in design.
- **Frontend modernization**: start with low-risk React islands and a modern asset pipeline from `docs/plans/0040-frontend-modernization-roadmap.md`, not a big rewrite.
- **Encrypted backup / sync**: only after sync target, key management, and conflict policy decisions are clear.
- **Code signing and auto-update**: only after certificate, private-key custody, timestamping, and release policy decisions are clear.

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
