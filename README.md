# GitSonar

[English](README.md) | [简体中文](README.zh-CN.md)

**Not just a Trending rank viewer, but a GitHub Intelligence Desk.**

![GitSonar Screen](assets/screenshots/trending.png)

GitSonar is a Windows desktop application built for developers, product managers, and researchers. It turns endless GitHub browsing into a structured pipeline: **Discover + Organise + Track + Judge**.

## 3 Core Workflows

1. **Noise Reduction & Accumulation**: Categorize the repositories you encounter into **Follow**, **Watch Later**, **Read**, or **Ignore**. Only pay attention to updates that matter.
2. **Actionable Tracking**: Instead of just telling you a repository gained stars, it tracks hard metrics like new Releases and active Pushes across your followed lists.
3. **AI-Driven Judgement**: Stop copying and pasting into browser tabs. With one click, send complex repository details or side-by-side comparisons to AI, getting structured technical or business judgements instantly from your desktop.

## The Pipeline

`Discover` ➔ `Organise` ➔ `Track` ➔ `Judge`

## Capability Matrix

| Module | Feature | Status | Note |
| --- | --- | --- | --- |
| **Discovery** | Dual-source trend aggregation (Day/Week/Month) | ✅ Ready | Blends native trending with API data |
| | Multi-dimensional Sorting (Stars/Trend/Gained/Forks) | ✅ Ready | Deep filtering capabilities |
| | Saved Filters & Custom Discovery Views | 🚧 Planned | Subscribe to specific languages or topics |
| **Organisation** | 4-State Pipeline (Follow/Watch Later/Read/Ignore) | ✅ Ready | Move beyond "read and forget" |
| | Import Initial Follow List | 🚧 Planned | Sync with existing GitHub account stars |
| **Tracking** | Basic Update Monitoring (Push/Stars/Releases) | ✅ Ready | Dedicated updates panel for followed items |
| | **Advanced Intelligence Center** | 🚧 High P0 | Change severity summaries, diffs, and noise reduction |
| **AI Judgement** | Fast context prompt generation | ✅ Ready | Supports batching and comparison |
| | Embedded AI Judgement Engine | 🚧 High P0 | Output direct "Keep Following" / "Ignore" conclusions |
| **Desktop Core** | System tray / Hot wake-up / Proxy routing| ✅ Ready | Self-contained loop |
| | First-run onboarding & Network Diagnostics | 🚧 Planned | Lower configuration barriers for Token/Proxy |

> **💡 What is the Advanced Intelligence Center? (The Next Core Focus)**
> This is what pushes GitSonar beyond a simple crawler. Instead of just noting "gained 50 stars", it will analyze "Was there a major version bump? Has the main language shifted?" and output a conclusion.

## Interfaces

**State Management** — Follow, watch later, read, ignore, with batch operations.

![Favorites](assets/screenshots/favorites.png)

**Repository Detail** — Drawer view with README summary and quick actions.

![Detail](assets/screenshots/detail.png)

**Update Tracking** — Monitor push, star/fork, and release changes for followed repos.

*Screenshot coming soon.*

## Installation

**System Requirements**: Windows 10 and above.
**Note**: The app is currently not signed. If Windows SmartScreen blocks execution, please select "Run anyway".

You can download the latest version from the [GitHub Releases](https://github.com/1wsslda/github-trend-radar/releases) page:

1. **Installer (Recommended)**: Download `GitSonarSetup.exe` to install.
2. **Portable (Standalone)**: Download `GitSonar.exe` and run directly.

On first launch, configure what you need:

### Recommended Defaults

- `GitHub Token`: recommended if available
- `Proxy`: fill in a local proxy if GitHub is unstable in your network
- `Refresh interval`: `1 hour`
- `Result limit`: `25`
- `Close behavior`: keep running in tray

## Roadmap Priorities

These are the immediate evolutionary directions:

### Priority 1: Advanced Update Intelligence (The Deep End)

- **Embedded AI Engine**: Support for OpenAI, DeepSeek, Ollama APIs. Not just templating prompts, but directly outputting structured conclusions inside the app.
- **Full-Spectrum Awareness**: Aggregate event streams per repo, highlight major version changes, auto-assign update severities, and provide "since last read" diffs.

### Priority 2: Building a Personal Intelligence Pool

- **Private Streams**: Save custom filters and perspectives.
- **Account Sync**: Support an initial import from a user's GitHub Account Stars.
- **Local Reliability**: Polish network diagnostics, provide recommended proxy values, and offer safe, lossless data migration and auto-backups.

### Experience Upgrades

- Global launch shortcuts.
- Better release portals and portable updates.

## Privacy & Data Security

We take security boundaries seriously for an app handling your GitHub token:

- **Strictly Local**: All data is stored purely locally at `%LOCALAPPDATA%\GitSonar`.
- **Encrypted Tokens**: Your optionally provided GitHub Token is encrypted using native Windows encryption mechanisms before being persisted.
- **Zero Telemetry**: Outside of strictly communicating with the genuine GitHub API and your configured AI endpoints, the application performs absolutely zero remote sniffing or telemetry on your reading habits and credentials.

## License

This project is released under the [MIT License](LICENSE).

## Docs

## Naming

- Brand: `GitSonar`
- Chinese name: `GitHub 情报台`
- Tagline: `Track GitHub projects with a desktop workflow.`



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
