---
name: ag-docs-sync
description: >-
  Manage and trigger the Antigravity Documentation & Session Log Archival Extension across all
  Antigravity versions (Antigravity 2.0, Antigravity CLI agy, Antigravity IDE, and Antigravity SDK).
  Use to sync artifacts to .docs/, rebuild documentation indexes, manage project exclusions,
  and inspect build session transcripts.
---

# Universal Antigravity Documentation & Session Archiver (`ag-docs-sync`)

This skill provides operational workflows and commands for `ag-docs-sync` across all Antigravity runtimes:
- **Antigravity IDE** (VS Code AI-First IDE)
- **Antigravity 2.0** (Desktop Application)
- **Antigravity CLI** (`agy`)
- **Antigravity Python SDK** (`google-antigravity`)

---

## 1. Supported Antigravity Runtimes

| Runtime | Integration Method | Automatic Sync Trigger |
| :--- | :--- | :--- |
| **Antigravity IDE** | `.vsix` extension + Universal plugin | Session completion, status bar, command palette |
| **Antigravity 2.0** | Universal global plugin (`~/.gemini/config/plugins`) | Lifecycle hook (`Stop`), desktop app integration |
| **Antigravity CLI (`agy`)** | Universal global plugin + CLI commands | Lifecycle hook (`Stop`), CLI arguments |
| **Antigravity Python SDK** | `ag_docs_sync` Python package / Hook class | `AntigravityDocsHook` context manager or `sync_session()` |

---

## 2. Python SDK Programmatic Usage (`google-antigravity`)

When building agent pipelines using the Antigravity Python SDK:

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from ag_docs_sync import AntigravityDocsHook, sync_on_exit

# Option A: Automatic archival on exit
async def run_agent():
    config = LocalAgentConfig(capabilities=CapabilitiesConfig())
    
    with sync_on_exit(workspace_path="."):
        async with Agent(config) as agent:
            response = await agent.chat("Implement database migration scripts")
            # ... process response ...

# Option B: Explicit session hook
hook = AntigravityDocsHook(workspace_path=".")
# ... execute agent ...
hook.sync(conversation_id="conv-abc-123")
```

---

## 3. Manual Sync & Backfill CLI

To manually trigger a synchronization or backfill past sessions:

```bash
# Auto-discover latest session across all Antigravity runtimes
python scripts/sync_docs.py --workspace "<workspace_path>"

# Specific conversation ID
python scripts/sync_docs.py --workspace "<workspace_path>" --conversation-id "<conv_id>"

# Explicit paths
python scripts/sync_docs.py -w "." -t "C:/path/to/transcript.jsonl" -a "C:/path/to/artifacts"
```

---

## 4. Multi-Runtime Installer Commands

```bash
# Setup for all detected Antigravity runtimes
python install.py --all

# Check multi-runtime ecosystem status
python install.py status

# Install IDE extension
python install.py --ide

# Install Python SDK package
python install.py --sdk

# Manage project exclusions
python install.py exclude "D:/Projects/PrivateApp"
python install.py unexclude "D:/Projects/PrivateApp"
python install.py list-excluded
```

---

## 5. Directory Layout in `.docs/`

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

## 6. Rebuilding the Master Index

```bash
python -c "from scripts.artifact_manager import ArtifactManager; ArtifactManager('.').update_index_file()"
```
