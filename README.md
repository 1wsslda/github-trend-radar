# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

> GitHub Intelligence Desk  
> Windows desktop app for trending repos, saved projects, and update tracking.

GitSonar is a Windows desktop app for following GitHub projects over time. It combines trending lists, saved states, update tracking, repository details, side-by-side comparison, and ChatGPT prompts in one place.

## What It Solves

Many people browse GitHub Trending, but the real cost starts after discovery:

- Which repositories are worth checking today, this week, or this month?
- Which ones should be favorited, queued for later, marked as read, or ignored?
- What changed in the repositories you already care about?
- What does a repository actually do, and is it worth following long term?
- Which of two similar repositories is the better long-term bet?

GitSonar turns those scattered actions into a repeatable desktop workflow.

## Highlights

- **Trend discovery**: daily, weekly, and monthly hot repositories
- **State management**: favorite, later, read, ignore
- **Favorite update tracking**: push, star/fork, and release changes
- **Repository understanding**: detail drawer and README summaries
- **Repository comparison**: compare two repositories side by side
- **ChatGPT prompts**: single repo, batch, and comparison prompts
- **Desktop presence**: tray, wake-up, configurable close behavior, auto start

## Who It Is For

- Developers who want to follow GitHub projects over time
- Product, strategy, and research users doing technical scanning
- Indie hackers and heavy open-source users
- People who want a workflow, not just a ranking page
- Users who want faster judgment, not just faster browsing

## Why It Is Not Just a Trending Viewer

GitSonar does more than show projects. It helps you move through the expensive part after discovery:

- discover, then decide
- mark, then process
- favorite, then track
- compare, then understand
- analyze, then judge

It is closer to a long-running GitHub intelligence workspace than a page you open once and close.

## Quick Start

### Download

1. Run the installer: `artifacts/dist/installer/GitSonarSetup.exe`
2. Or launch the portable build: `artifacts/dist/GitSonar.exe`
3. On first launch, configure what you need:
   - GitHub Token
   - Proxy
   - Refresh interval
   - Result limit
   - Close behavior

### Recommended Defaults

- `GitHub Token`: recommended if available
- `Proxy`: fill in a local proxy if GitHub is unstable in your network
- `Refresh interval`: `1 hour`
- `Result limit`: `25`
- `Close behavior`: keep running in tray

## Current Capabilities

### 1. Trend Discovery

- Today / This Week / This Month hot repositories
- Dual-source aggregation from GitHub Trending and GitHub API
- Multiple sorting modes: stars, trending, gained, forks, name, language

### 2. State Management

- Favorite
- Later
- Read
- Ignore
- Batch state changes for selected repositories

### 3. Favorite Update Tracking

- Recent push time changes
- Star / Fork changes
- Release changes
- Dedicated updates panel for favorited repositories

### 4. Repository Understanding and Comparison

- Repository detail drawer
- README summary
- Two-repository comparison

### 5. ChatGPT Prompts

- Single repository prompts
- Batch prompts
- Comparison prompts
- Open ChatGPT web / desktop, or copy prompts

### 6. Desktop Experience

- System tray resident mode
- Tray wake-up
- Configurable close behavior
- Auto start
- Proxy support
- Local encrypted GitHub Token storage

## Typical Workflow

1. Discover hot repositories across daily, weekly, and monthly views.
2. Organize them with favorite, later, read, and ignore.
3. Open details, read summaries, and compare similar repositories.
4. Send one repository, a list, or a comparison to AI for faster understanding.
5. Keep tracking the repositories that matter through the updates panel.

## Screenshots

**Trend Discovery** — browse today, this week, and this month's hot repositories.

![Trending](assets/screenshots/trending.png)

**State Management** — favorite, later, read, ignore with batch operations.

![Favorites](assets/screenshots/favorites.png)

**Repository Detail** — drawer view with README summary and quick actions.

![Detail](assets/screenshots/detail.png)

**Update Tracking** — monitor push, star/fork, and release changes for favorited repos.

![Updates](assets/screenshots/updates.png)

## Roadmap

These are product directions, not features already shipped.

### P0

- Embedded AI with OpenAI, DeepSeek, Ollama, and OpenAI-compatible APIs
- Smarter update center with change levels, one-line summaries, filters, mute, and “since last viewed”
- First-run onboarding with connectivity checks, proxy detection, optional token, and recommended defaults
- System notifications for important repository events
- Cleaner navigation split across discovery, lists, and updates

### P1

- Global shortcuts
- Better network diagnostics
- A more polished storefront and release presentation

### P2

- Data migration and backup
- Auto update
- Custom subscriptions and reminder strategies

## Naming

- Brand: `GitSonar`
- Chinese name: `GitHub 情报台`
- Tagline: `Track GitHub projects with a desktop workflow.`

Default runtime data now lives in:

- `%LOCALAPPDATA%\GitSonar`

If an older installation exists, GitSonar will try to merge data from:

- `%LOCALAPPDATA%\GitHubTrendRadar`

## License

This project is released under the [MIT License](LICENSE).

## Documentation

Detailed docs remain in the `docs` directory:

- [CHANGELOG.md](CHANGELOG.md)
- [docs/BUILD.md](docs/BUILD.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/FAQ.md](docs/FAQ.md)
- [docs/MAINTENANCE.md](docs/MAINTENANCE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- [docs/RELEASE_NOTES_TEMPLATE.md](docs/RELEASE_NOTES_TEMPLATE.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

These documents are currently Chinese-first.

## Repository Layout

- `src/`: desktop entry script and application source package
- `scripts/`: PowerShell and CMD build entry points
- `packaging/`: Inno Setup installer definition
- `runtime-data/`: local development runtime files, cache, and shell profile
- `artifacts/`: generated EXE, installer, and PyInstaller temporary output
- `docs/`: build, architecture, FAQ, and security notes
