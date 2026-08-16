# 🚀 Antigravity Docs & Session Log Archival Extension (`ag-docs-sync`)

An automatic, zero-friction Antigravity extension that captures, categorizes, timestamps, and indexes all project documents, brain artifacts, and color-coded build/conversation session logs into a clean `.docs/` repository folder across **all your projects**.

---

## 🌟 Key Features

1. **Automatic Archival on Session Completion**:
   - Uses Antigravity's `Stop` lifecycle hook (`hooks.json`) to trigger immediately when an agent task finishes.
   - Requires zero manual intervention.

2. **Organized, Aptly Named Subfolders (`.docs/`)**:
   - `.docs/plans/`: Implementation plans, architecture designs, timestamped snapshots (`implementation_plan_YYYY-MM-DD_HHmmss.md`) + active pointer (`implementation_plan.md`).
   - `.docs/walkthroughs/`: Verification summaries, release notes, changelogs.
   - `.docs/research/`: Technical notes, audits, benchmark docs.
   - `.docs/diagrams/`: Mermaid diagrams, SVGs, architecture schemas.
   - `.docs/media/`: Generated UI mockups, screenshots, recordings.
   - `.docs/scratch/`: Temporary test scripts and scratch data.
   - `.docs/logs/`: Color-coded session logs and timeline history.
   - `.docs/INDEX.md` & `README.md`: Auto-generated master catalog with clickable links, metadata, and timestamps.

3. **Rich Color-Coded Markdown Build Logs**:
   - 🎯 **User Instructions & Goals**: Blue/Cyan callout blocks (`> [!NOTE]`).
   - 🧠 **Thought Process & Reasoning**: Collapsible Purple/Indigo internal reasoning blocks (`> [!TIP]`).
   - ❓ **Questions & Answers**: Interactive modal questions, selections, user confirmations (`> [!IMPORTANT]`).
   - 🛠️ **Tool Executions**: Action summaries, tool arguments, output previews, diffs, error badges (`> [!CAUTION]`).
   - 📊 **Execution Metrics**: Timestamps, duration, prompt counts, and tool actions.
   - 📜 **Cumulative Timeline (`.docs/logs/TIMELINE.md`)**: Chronological index of all sessions across the project lifetime.

4. **Global & Project Exclusions**:
   - Exclude specific projects globally via CLI or configuration.
   - Local project opt-out via `.docs-ignore` file or `.docs-sync.json`.
   - Fast early exit for skipped projects with zero performance penalty.

5. **Timestamped File Identification**:
   - Every archived file and log uses ISO-standardized timestamped naming (`<name>_YYYY-MM-DD_HHmmss.<ext>`) for easy auditing, historical diffing, and version tracking.

---

## 📦 Installation & Setup

### 1. Install Globally (Recommended)
Installs the extension globally to `~/.gemini/config/plugins/ag-docs-sync`. Once installed, it automatically runs across **all projects built in Antigravity**.

```bash
# Windows
.\install.bat

# PowerShell
.\install.ps1

# Python (Cross-platform)
python install.py
```

### 2. Check Installation Status
```bash
python install.py status
```

---

## 🚫 Excluding Projects from Auto-Sync

If you have private, temporary, or sensitive projects you do not want synced:

### Option A: Global CLI Exclusion
```bash
# Exclude a project path
python install.py exclude "D:/Projects/PrivateApp"

# Re-enable a project
python install.py unexclude "D:/Projects/PrivateApp"

# List all excluded projects
python install.py list-excluded
```

### Option B: Local Project Marker (`.docs-ignore`)
Place an empty `.docs-ignore` or `.ag-docs-ignore` file in the project's root folder:
```bash
echo. > .docs-ignore
```

### Option C: Local Config (`.docs-sync.json`)
Create `.docs-sync.json` in the workspace root:
```json
{
  "enabled": false
}
```

---

## 📂 Generated `.docs/` Directory Structure

```text
my-project/
├── .docs/
│   ├── INDEX.md                         # Master documentation index
│   ├── README.md                        # Mirror index for GitHub/viewers
│   ├── plans/
│   │   ├── implementation_plan.md       # Current active plan
│   │   └── implementation_plan_2026-08-16_174400.md
│   ├── walkthroughs/
│   │   ├── walkthrough.md               # Current active walkthrough
│   │   └── walkthrough_2026-08-16_174400.md
│   ├── research/
│   │   └── api_architecture_2026-08-16_174400.md
│   ├── diagrams/
│   │   └── system_flow_2026-08-16_174400.mermaid
│   ├── media/
│   │   └── dashboard_mockup_2026-08-16_174400.png
│   ├── scratch/
│   │   └── test_api_2026-08-16_174400.py
│   └── logs/
│       ├── LATEST_SESSION.md            # Most recent conversation log
│       ├── TIMELINE.md                  # Project historical timeline
│       └── session_2026-08-16_174400_7e598545.md
```

---

## 🛠️ Configuration Options

Configuration can be customized globally in `~/.gemini/config/plugins/ag-docs-sync/config.json` or per-project in `.docs-sync.json`:

```json
{
  "enabled": true,
  "docs_root": ".docs",
  "exclude_projects": [
    "D:/Temp/*"
  ],
  "timestamp_format": "%Y-%m-%d_%H%M%S",
  "keep_latest_symlink_or_copy": true,
  "session_logging": {
    "enabled": true,
    "include_thoughts": true,
    "include_tools": true,
    "include_qa": true,
    "include_prompts": true,
    "collapse_thoughts": true,
    "collapse_tool_outputs": true
  }
}
```

---

## 🧪 Testing

Run the test suite:
```bash
python -m unittest discover tests
```

## 👤 Author & Organization
- **Author**: Don Sony
- **Company**: [infuse.ae](https://infuse.ae)

---

## 📄 License
MIT License
