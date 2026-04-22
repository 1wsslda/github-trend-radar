# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**GitSonar is a Windows desktop GitHub intelligence desk for ongoing repository discovery, organisation, tracking, and judgement.**

![GitSonar Screen](assets/screenshots/trending.png)

GitSonar is not just a Trending viewer. It combines trend discovery, keyword discovery, local workflow states, update tracking, repo detail reading, side-by-side comparison, and ChatGPT prompt handoff in one desktop workspace.

## Workflow

1. **Discover**
   Daily / weekly / monthly trend aggregation plus a keyword discovery panel with saved searches and ranking profiles.
2. **Organise**
   Local `Follow / Watch Later / Read / Ignore` states, search, filters, sorting, batch actions, and state import / export.
3. **Track**
   Followed repo updates for push, star / fork, and release changes, plus optional GitHub star sync and import.
4. **Judge**
   Repo detail drawer, README summary, side-by-side compare, and AI prompt handoff (ChatGPT web / desktop, Gemini web — single, batch, or compare workflows, multi-target supported).

## What Is Implemented Today

- Trend aggregation for day / week / month
- Keyword discovery with saved searches
- Local follow states and batch actions
- Followed repo update tracking
- Repo detail drawer and README summary
- Side-by-side repo comparison
- AI prompt handoff to ChatGPT web / desktop, Gemini web, or copy-only; multi-target supported
- Single-instance wake-up, close-to-exit behavior, auto start, proxy support, and local token storage

## Who It Is For

- People who follow GitHub projects over time, not just once
- Builders, researchers, product people, and heavy open-source users
- Anyone who wants a desktop workspace instead of a one-off Trending page

## Not Just A Trending Viewer

- A viewer helps you discover repos. GitSonar keeps the follow-up workflow on desktop.
- GitHub stars are only one signal. GitSonar adds local states, update tracking, detail reading, compare, and judgement tools.
- The app keeps the follow-up workflow on desktop with single-instance wake-up and explicit relaunch when needed.

## Terms

- **Local `Follow / Favorites / favorites`**
  The current UI and codebase still mix these labels. In practice they point to the same local follow list inside GitSonar.
- **GitHub `Star`**
  This is a GitHub platform action and metric. With a token configured, marking a repo as `Follow` will try to sync a GitHub star, and you can also import your existing GitHub stars into the local follow list.

## Quick Start

### Users

- GitSonar is a Windows desktop app.
- If this repository currently has published releases, download them from [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases):
  - `GitSonarSetup.exe`
  - `GitSonar.exe`
- `artifacts/` is a repo build-output directory, not the default download entry for normal users.
- There is currently **no auto-update and no code signing**. Windows SmartScreen may ask you to confirm before running.

### Developers

Requirements:

- Windows
- Python 3.12+

```powershell
python -m pip install -r requirements.txt
python src/gitsonar/__main__.py
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\build_setup.ps1
```

One-click packaging:

```cmd
scripts\build_all_click.cmd
```

## Security & Data

- Packaged app data lives under `%LOCALAPPDATA%\GitSonar`
- Repository development runs use `runtime-data/`
- Legacy `%LOCALAPPDATA%\GitHubTrendRadar` data is merged on first run when needed
- GitHub tokens are stored locally with Windows DPAPI
- Current network destinations include GitHub and Google Translate for translation
- AI analysis currently means prompt handoff to external ChatGPT (web / desktop) or Gemini web — not embedded AI inside the app. Multiple targets can be selected to open simultaneously.

See [docs/SECURITY.md](docs/SECURITY.md) for the exact security boundary.

## Roadmap

Planned, not yet implemented:

- Smarter update judgement: summaries, prioritisation, and “since last read” views
- Embedded AI judgement instead of prompt handoff
- Custom discovery views, onboarding, diagnostics, and stronger local reliability tooling

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
