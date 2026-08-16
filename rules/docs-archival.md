# Project Documentation & Artifact Archival Standards

When working in this workspace, Antigravity is configured with the `ag-docs-sync` extension which automatically syncs, timestamps, and indexes all project documentation, artifacts, and session transcripts into the `.docs/` directory.

`ag-docs-sync` universally supports all Antigravity runtimes:
- **Antigravity 2.0 (Desktop App)**
- **Antigravity CLI (`agy`)**
- **Antigravity IDE (VS Code-based)**
- **Antigravity Python SDK (`google-antigravity`)**

## Documentation Guidelines

1. **Artifact Structure**:
   - Save plans as `implementation_plan.md` in the artifact directory.
   - Save walkthroughs and release summaries as `walkthrough.md`.
   - Save research and audit notes as descriptive filenames (e.g. `research_api_specs.md`, `architecture_audit.md`).
   - Save diagram files with standard extensions (`.mermaid`, `.svg`, `.puml`).

2. **Categorization in `.docs/`**:
   The extension will automatically catalog files into:
   - `.docs/plans/`: Historical and active implementation plans.
   - `.docs/walkthroughs/`: Verification summaries and changelogs.
   - `.docs/research/`: Technical notes, audits, benchmark docs.
   - `.docs/diagrams/`: System diagrams and visualizations.
   - `.docs/media/`: Generated UI mockups and visual assets.
   - `.docs/scratch/`: Temporary test scripts and data.
   - `.docs/logs/`: Color-coded session logs, thought process transcripts, and timelines.
   - `.docs/INDEX.md`: Master documentation index.

3. **Project Exclusions**:
   - If a project should NOT be synced, add a `.docs-ignore` file to its root, or configure `exclude_projects` via `python install.py exclude <path>`.
