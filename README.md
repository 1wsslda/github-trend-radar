# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

> GitHub Intelligence Desk  
> Turn GitHub trending into a trackable intelligence flow.

GitSonar is a desktop GitHub intelligence desk for discovery, tracking, comparison, and AI-assisted understanding. Instead of acting like a simple wrapper around GitHub Trending, it brings hot project discovery, state management, favorite update tracking, repository comparison, and AI workflows into one lightweight, tray-friendly desktop workspace.

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
- **AI workflows**: single repo, batch, and comparison analysis
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

1. Run the installer: `dist/installer/GitSonarSetup.exe`
2. Or launch the portable build: `dist/GitSonar.exe`
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

### 5. AI Assistance

- Single repository analysis
- Batch analysis
- Comparison analysis
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

Coming soon. This section is reserved for real application screenshots.

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

## Promo Copy

### One-liner

**Turn GitHub trending into your project intelligence system.**

### Short Repository Description

**A Chinese-friendly GitHub intelligence desk for trend discovery, repository tracking, comparison, and AI-assisted analysis.**

### Release / Social Copy

GitSonar is a desktop GitHub intelligence desk that helps you discover, track, compare, and understand repositories in one long-running workflow.

## Naming

- Brand: `GitSonar`
- Chinese name: `GitHub 情报台`
- Tagline: `Turn GitHub trending into a trackable intelligence flow.`

Default runtime data now lives in:

- `%LOCALAPPDATA%\GitSonar`

If an older installation exists, GitSonar will try to merge data from:

- `%LOCALAPPDATA%\GitHubTrendRadar`

## License

This project is released under the [MIT License](LICENSE).

## Documentation

Detailed docs remain in the `docs` directory:

- [docs/BUILD.md](docs/BUILD.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/FAQ.md](docs/FAQ.md)
- [docs/SECURITY.md](docs/SECURITY.md)

These documents are currently Chinese-first.
