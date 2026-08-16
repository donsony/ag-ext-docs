---
name: ag-docs-sync
description: >-
  Manage and trigger the Antigravity Documentation & Session Log Archival Extension.
  Use to sync artifacts to .docs/, rebuild documentation indexes, manage project exclusions,
  and inspect build session transcripts.
---

# Antigravity Documentation & Session Log Archiver (`ag-docs-sync`)

This skill provides instructions and helper actions for the `ag-docs-sync` extension.

---

## 1. Manual Sync & Backfill

To manually sync the current session or a previous conversation to `.docs/`:

```bash
python scripts/sync_docs.py --workspace "<workspace_path>" --conversation-id "<conv_id>"
```

Options:
- `--workspace`, `-w`: Path to the project workspace root.
- `--conversation-id`, `-c`: Conversation ID to sync.
- `--transcript`, `-t`: Explicit path to `transcript.jsonl`.
- `--artifacts`, `-a`: Explicit path to artifact folder.
- `--force`, `-f`: Bypass project exclusion checks.

---

## 2. Managing Project Exclusions

### Exclude a Project from Global Auto-Sync

```bash
python install.py exclude "D:/Projects/PrivateApp"
```

### Re-Enable a Project

```bash
python install.py unexclude "D:/Projects/PrivateApp"
```

### List All Excluded Projects

```bash
python install.py list-excluded
```

### Local Workspace Opt-Out
Alternatively, create an empty `.docs-ignore` file in any project's root:
```bash
echo. > .docs-ignore
```

---

## 3. Directory Layout in `.docs/`

```text
.docs/
├── INDEX.md               # Master catalog of all docs and logs
├── README.md              # Mirror of INDEX.md for GitHub/IDE rendering
├── plans/                 # Timestamped and active implementation plans
│   ├── implementation_plan.md
│   └── implementation_plan_2026-08-16_174400.md
├── walkthroughs/          # Timestamped walkthroughs and verification summaries
│   ├── walkthrough.md
│   └── walkthrough_2026-08-16_174400.md
├── research/              # Technical analysis, benchmarks, research notes
├── diagrams/              # Architecture diagrams (.mermaid, .svg)
├── media/                 # Mockups, screenshots, recordings
├── scratch/               # Experimental scripts and test outputs
└── logs/                  # Color-coded session logs
    ├── LATEST_SESSION.md
    ├── TIMELINE.md
    └── session_2026-08-16_174400_7e598545.md
```

---

## 4. Rebuilding the Master Index

If you've added or moved documents in `.docs/` manually, run:

```bash
python -c "from scripts.artifact_manager import ArtifactManager; ArtifactManager('.').update_index_file()"
```
