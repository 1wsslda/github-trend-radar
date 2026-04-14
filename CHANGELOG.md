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

### Changed

- Reorganized the repository into `src/`, `scripts/`, `packaging/`, and `docs/`.
- Moved the main runtime UI implementation to `src/gitsonar/runtime_ui.py`.
- Refined the desktop interface toward a calmer, reading-first GitHub intelligence desk.

### Fixed

- Runtime UI edge cases and several repo copy / layout inconsistencies around the reorganized structure.

## [v1.0.0] - 2026-04-14

### Added

- GitSonar branding and bilingual repository docs.
- Desktop workflow for GitHub trending discovery, saved states, update tracking, details, compare, and ChatGPT prompts.
- Packaging, build, FAQ, architecture, and security documentation.

### Changed

- Refreshed the product presentation and repo storefront for the first public version.
