# Changelog

All notable changes to the `ag-docs-sync` Antigravity extension and sync engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.3] - 2026-08-16

### Added
- **Universal Multi-Version & Multi-Type Antigravity Support**:
  - **Antigravity 2.0 (Desktop App)**: Full desktop app lifecycle integration, universal global plugin registration (`~/.gemini/config/plugins/ag-docs-sync`), and multi-brain discovery across `~/.gemini/antigravity`, `~/.gemini/antigravity-2.0`, and `~/.gemini/antigravity-app`.
  - **Antigravity CLI (`agy`)**: Automatic cross-session discovery of terminal transcripts and artifact directories across CLI runs, with CLI argument flags.
  - **Antigravity IDE**: AI-first integrated development environment (`.vsix` extension), Activity Bar tree view (`Project Documentation (.docs/)`), status bar widget, and command palette integration.
  - **Antigravity Python SDK (`google-antigravity`)**: Native `ag_docs_sync` Python package, `AntigravityDocsHook` lifecycle hook adapter, and `sync_on_exit()` / `sync_session()` programmatic helpers.
- **Python Packaging**: Added `setup.py` and `pyproject.toml` for standard pip installation (`pip install -e .`).
- **Multi-Runtime Ecosystem Detection**: Real-time detection and diagnostic reporting in `ConfigLoader.detect_antigravity_runtimes()` and `python install.py status`.
- **Universal Multi-Target Installer**: Added flags `--all`, `--ide`, `--sdk`, `--cli`, and `--app` to `install.py` / `install.ps1` / `install.bat`.
- **Extended Test Suite**: Added 20 automated unit tests covering multi-runtime brain discovery, SDK integration, and CLI installer features.

---

## [1.0.2] - 2026-08-16

### Added
- **Antigravity IDE GUI Extension**:
  - VS Code / Antigravity IDE GUI Extension manifest and runtime (`package.json`, `dist/extension.js`).
  - Visible in **Extensions >> Installed** panel.
  - Status Bar Widget (`$(book) Docs: Active`) with manual sync trigger.
  - Sidebar Tree View (`Project Documentation (.docs/)`) in Activity Bar.
  - Command Palette commands (`Sync Now`, `Open .docs`, `Open Session Logs`, `Exclude/Include Workspace`, `Show Status`).
  - Zero-conflict coexistence engine with shared single source of truth configuration (`config.json`).
  - Packaged installable `.vsix` bundle via `python install.py --vsix`.

---

## [1.0.1] - 2026-08-16

### Added
- **Automated Lifecycle Hooks & Session Log Archival**:
  - Integrated Antigravity `Stop` event hook (`hooks.json`) to automatically archive artifacts on task completion.
  - Color-coded markdown session logs with tool execution badges and thought block collapsing.
  - Categorized subfolder organization (`plans/`, `walkthroughs/`, `research/`, `diagrams/`, `media/`, `scratch/`, `logs/`).
  - Timestamped snapshot history and master catalog `INDEX.md`.

---

## [1.0.0] - 2026-08-16

### Added
- Initial release of `ag-docs-sync`.
- Basic artifact copying and markdown documentation indexing.
