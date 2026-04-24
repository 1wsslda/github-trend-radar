# Changelog

All notable changes to this project should be recorded here.

This file follows a lightweight Keep a Changelog style.

## [Unreleased]

### Added

- Public repository management files:
  - `CONTRIBUTING.md`
  - issue templates
  - release checklist
  - release notes template
- Cleaner desktop intelligence workspace UI with:
  - field / action visual separation
  - segmented state filter
  - segmented sort with more menu
  - split analyze action
  - floating batch dock
- 2026-04-23 product workflow MVPs:
  - local diagnostics panel and `/api/diagnostics`;
  - saved discovery views;
  - repo tags and notes;
  - Update Inbox MVP with read, pin, dismiss, and priority state;
  - recommendation / ranking reasons;
  - ignore feedback captured into local state;
  - Markdown summary export;
  - manual structured AI Insight artifact save / delete.
- 2026-04-24 architecture and intelligence MVPs:
  - read JSON API boundary for bootstrap, repos, updates, and discovery views;
  - SQLite migration design with JSON compatibility and rollback strategy;
  - in-memory Job / Event runtime and read endpoints;
  - SSE event snapshot endpoint;
  - AI artifact metadata cache and list endpoint;
  - local discovery result clustering;
  - lightweight repo map visualization;
  - optional loopback-only Ollama-style translation provider;
  - local release checksum manifest script.
- 2026-04-24 documentation reality sync:
  - README, architecture, security, roadmap, changelog, task table, sprint queue, and progress log now reflect the current implemented surface;
  - next Project Autopilot Safe Loop queue is tracked as `GS-P1-013` through `GS-P1-017`.

### Changed

- Reorganized the repository into `src/`, `scripts/`, `packaging/`, and `docs/`.
- Moved the main runtime UI implementation into the `src/gitsonar/runtime_ui/` package split by template, assets, CSS, and JS resources.
- Refined the desktop interface toward a calmer, reading-first GitHub intelligence desk.
- Clarified that current AI support is prompt handoff plus manual local Insight artifact storage, not an embedded provider pipeline.
- Clarified that discovery jobs and the general Job / Event / SSE runtime exist but are not yet fully unified.

### Security

- Added user-visible redaction for proxy credentials, local diagnostics details, status/bootstrap payloads, discovery job failures, and HTTP route exception logs.
- DPAPI encrypt/decrypt calls now use `CRYPTPROTECT_UI_FORBIDDEN`.
- Refresh failures and discovery job failures store user-safe summaries instead of raw exception details.
- Local JSON API request bodies are limited; oversized bodies return `413 payload_too_large`.
- `/api/repo-details` now requires loopback access and the runtime control token because it can trigger GitHub requests and cache writes.

### Fixed

- Runtime UI edge cases and several repo copy / layout inconsistencies around the reorganized structure.
- Documentation drift where completed diagnostics, saved discovery views, clustering, map, Markdown export, and security hardening were still described as future work.

## [v1.0.0] - 2026-04-14

### Added

- GitSonar branding and bilingual repository docs.
- Desktop workflow for GitHub trending discovery, saved states, update tracking, details, compare, and ChatGPT prompts.
- Packaging, build, FAQ, architecture, and security documentation.

### Changed

- Refreshed the product presentation and repo storefront for the first public version.
