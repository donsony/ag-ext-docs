# Implementation Plan: Antigravity Docs & Session Log Archival Extension (`ag-docs-sync`)

Build an Antigravity extension/plugin that automatically organizes and archives all project documents, brain artifacts, and color-coded session logs (instructions, thoughts, Q&A, and tool actions) into a structured `.docs/` directory for any project running in Antigravity.

## User Review Required

> [!IMPORTANT]
> **Global Installation vs. Project Installation**:
> The extension is structured as an Antigravity Plugin with lifecycle hooks (`hooks.json`). When installed globally in `~/.gemini/config/plugins/ag-docs-sync/` (or registered in global `plugins.json`), Antigravity executes the `Stop` hook automatically whenever an agent execution loop terminates across **all projects**.
>
> We will provide automated install scripts (`install.py`, `install.ps1`, `install.sh`) so you can enable it globally with one command or install it locally in individual projects.

## Architecture Overview

```
ag-ext-docs /
├── plugin.json                # Plugin manifest
├── hooks.json                 # Lifecycle hook (Stop hook triggers sync)
├── scripts/
│   ├── sync_docs.py           # Core engine: processes transcript, artifacts, and generates .docs/
│   ├── log_formatter.py       # Formats conversation events into color-coded markdown
│   └── artifact_manager.py    # Classifies and archives artifacts into structured subfolders
├── rules/
│   └── docs-archival.md       # Rule guiding agent on documentation & artifact standards
├── skills/
│   └── ag-docs-sync/
│       └── SKILL.md           # On-demand skill for manual sync, backfills, & re-indexing
├── install.py                 # Cross-platform installer/uninstaller (Global or Local)
├── install.ps1                # PowerShell fast install script
├── install.bat                # Windows Batch install helper
├── README.md                  # Comprehensive user and developer guide
└── tests/
    ├── test_log_formatter.py  # Unit tests for markdown color-coding & log generation
    ├── test_artifact_manager.py # Unit tests for folder organization
    └── test_sync_docs.py      # End-to-end hook pipeline tests
```

---

## Proposed Changes

### 1. Plugin Manifest, Hook Configuration & Exclusion Settings

#### [NEW] [plugin.json](file:///d:/Development/ag-ext-docs/plugin.json)
- Defines plugin metadata (`ag-docs-sync`), version `1.0.0`, description, author, and capabilities.

#### [NEW] [hooks.json](file:///d:/Development/ag-ext-docs/hooks.json)
- Configures the `Stop` lifecycle hook to run `python scripts/sync_docs.py` (with Windows & POSIX compatibility).
- Receives `stdin` containing `conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`.

#### [NEW] [config.default.json](file:///d:/Development/ag-ext-docs/config.default.json) & Configuration System
- Global config (`~/.gemini/config/plugins/ag-docs-sync/config.json`) supporting:
  - `exclude_projects`: List of workspace paths, names, or glob patterns to skip (e.g. `["D:/private/*", "C:/Users/*/temp"]`).
  - `opt_in_mode`: Boolean flag (default `false` = sync all projects except excluded).
  - `custom_subfolders`: Configurable folder names for plans, walkthroughs, logs, etc.
  - `color_theme`: Configurable color palette for session logs.
- Workspace-level opt-out:
  - Supports `.docs-ignore` or `.ag-docs-ignore` file in project root.
  - Supports `.docs-sync.json` with `{"enabled": false}`.

---

### 2. Core Python Processing Engine

#### [NEW] [scripts/config_loader.py](file:///d:/Development/ag-ext-docs/scripts/config_loader.py)
- Resolves global and workspace configuration.
- Evaluates project exclusion rules (exact match, glob patterns, `.docs-ignore` markers).
- If a project is excluded, cleanly exits early with zero overhead.

#### [NEW] [scripts/artifact_manager.py](file:///d:/Development/ag-ext-docs/scripts/artifact_manager.py)
- Scans the conversation artifact directory (`<appDataDir>\brain\<conversation-id>`).
- Categorizes artifacts into structured `.docs/` subfolders using **timestamped versioning**:
  - `.docs/plans/` -> `implementation_plan_YYYY-MM-DD_HHmmss.md` (and active `implementation_plan.md`)
  - `.docs/walkthroughs/` -> `walkthrough_YYYY-MM-DD_HHmmss.md` (and active `walkthrough.md`)
  - `.docs/research/` -> `<doc_name>_YYYY-MM-DD_HHmmss.md` (research notes, audit docs)
  - `.docs/diagrams/` -> `diagram_YYYY-MM-DD_HHmmss.<ext>`
  - `.docs/media/` -> `asset_YYYY-MM-DD_HHmmss.<ext>`
  - `.docs/scratch/` -> `scratch_YYYY-MM-DD_HHmmss.<ext>`
  - `.docs/raw_artifacts/` -> `<name>_YYYY-MM-DD_HHmmss.<ext>`
- Maintains a `.docs/INDEX.md` master document catalog with timestamped entries, quick links, file size, conversation ID, and summaries.

#### [NEW] [scripts/log_formatter.py](file:///d:/Development/ag-ext-docs/scripts/log_formatter.py)
- Parses `transcript.jsonl` and `transcript_full.jsonl`.
- Formats session history into rich, color-coded Markdown:
  - 🎯 **User Instructions / Prompts**: Vibrant cyan/blue callout blocks (`> [!NOTE]`).
  - 🧠 **Thought Process & Reasoning**: Collapsible purple/indigo thought sections (`> [!TIP]`).
  - ❓ **Questions & Answers**: Interactive questions, user choices, confirmations (`> [!IMPORTANT]`).
  - 🛠️ **Tool Executions**: Commands run, file replacements, searches, image generation with success/error status (`> [!CAUTION]`).
  - 💬 **Assistant Responses & Summaries**: Clean output sections with syntax-highlighted code.
- Generates:
  - `.docs/logs/session_YYYY-MM-DD_HHmmss_<conversationId>.md`
  - `.docs/logs/LATEST_SESSION.md` (always points to the latest run)
  - `.docs/logs/TIMELINE.md` (chronological session history index with timestamps and step counts)

#### [NEW] [scripts/sync_docs.py](file:///d:/Development/ag-ext-docs/scripts/sync_docs.py)
- Entry point for the hook (`stdin` / CLI).
- Checks configuration & exclusion rules first.
- Runs `ArtifactManager` and `LogFormatter`.
- Outputs valid JSON response for the Antigravity hook runtime.

---

### 3. Rules and Skills Integration

#### [NEW] [rules/docs-archival.md](file:///d:/Development/ag-ext-docs/rules/docs-archival.md)
- Antigravity rule instructing the model about `.docs/` conventions, artifact naming best practices, and documentation completeness.

#### [NEW] [skills/ag-docs-sync/SKILL.md](file:///d:/Development/ag-ext-docs/skills/ag-docs-sync/SKILL.md)
- Antigravity skill enabling on-demand manual documentation synchronization, rebuilding indexes, managing exclusions, or exporting custom summaries.

---

### 4. Installation, Exclusion CLI, & Test Suite

#### [NEW] [install.py](file:///d:/Development/ag-ext-docs/install.py), [install.ps1](file:///d:/Development/ag-ext-docs/install.ps1), [install.bat](file:///d:/Development/ag-ext-docs/install.bat)
- Automated installer that copies/symlinks the plugin into global `C:\Users\donso\.gemini\config\plugins\ag-docs-sync` or local `.agents/`.
- CLI commands:
  - `python install.py --global` (Installs globally)
  - `python install.py exclude <path>` (Adds project path/pattern to global exclusion list)
  - `python install.py unexclude <path>` (Removes project path from exclusion list)
  - `python install.py list-excluded` (Lists currently excluded projects)
  - `python install.py --status` (Checks installation and configuration status)

#### [NEW] [README.md](file:///d:/Development/ag-ext-docs/README.md)
- Complete documentation on installation, configuration, folder structure, log color codes, and customization options.

#### [NEW] [tests/test_log_formatter.py](file:///d:/Development/ag-ext-docs/tests/test_log_formatter.py), [tests/test_artifact_manager.py](file:///d:/Development/ag-ext-docs/tests/test_artifact_manager.py), [tests/test_sync_docs.py](file:///d:/Development/ag-ext-docs/tests/test_sync_docs.py)
- Comprehensive test suite to ensure robust parsing of transcripts, error handling, Windows path handling, and formatting accuracy.

---

## Verification Plan

### Automated Tests
- Run `python -m unittest discover tests` to verify:
  1. Transcript parsing (prompts, thought blocks, Q&A steps, tool calls, errors).
  2. Markdown rendering with correct GitHub alert badges and HTML color highlights.
  3. Artifact scanning, categorizing into `.docs/` subfolders, and `INDEX.md` generation.
  4. End-to-end hook simulation with actual mock JSON payload.

### Manual Verification
1. Run `sync_docs.py` using the current active conversation transcript and artifact directory to verify real `.docs/` output.
2. Verify that `.docs/plans/`, `.docs/logs/`, `.docs/INDEX.md`, and `LATEST_SESSION.md` are generated cleanly with beautiful color-coding and valid markdown formatting.
3. Test the global installer script to verify seamless registration.
