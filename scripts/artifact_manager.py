#!/usr/bin/env python3
"""
Artifact Organizer & Documentation Indexer for ag-docs-sync
Scans Antigravity brain artifacts, categorizes into .docs/ subfolders with timestamps, and generates INDEX.md.
"""

import os
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ArtifactManager:
    def __init__(self, workspace_path: str, config: Optional[Dict[str, Any]] = None):
        self.workspace_path = Path(workspace_path).resolve()
        self.config = config or {}
        self.docs_root_name = self.config.get("docs_root", ".docs")
        self.docs_dir = self.workspace_path / self.docs_root_name
        self.subfolder_cfg = self.config.get("subfolders", {
            "plans": "plans",
            "walkthroughs": "walkthroughs",
            "research": "research",
            "diagrams": "diagrams",
            "media": "media",
            "scratch": "scratch",
            "raw_artifacts": "raw_artifacts",
            "logs": "logs"
        })
        self.timestamp_fmt = self.config.get("timestamp_format", "%Y-%m-%d_%H%M%S")
        self.keep_latest = self.config.get("keep_latest_symlink_or_copy", True)

    def determine_category(self, file_path: Path, rel_path_str: str) -> str:
        """Determines the target .docs subfolder category for a given artifact file."""
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check directory location first
        if "scratch" in rel_path_str.lower():
            return self.subfolder_cfg.get("scratch", "scratch")

        # Plans
        if "plan" in name or name == "implementation_plan.md":
            return self.subfolder_cfg.get("plans", "plans")

        # Walkthroughs
        if "walkthrough" in name or "changelog" in name or "release_notes" in name:
            return self.subfolder_cfg.get("walkthroughs", "walkthroughs")

        # Research / Analysis
        if any(keyword in name for keyword in ("research", "analysis", "audit", "investigation", "report", "benchmark", "notes")):
            return self.subfolder_cfg.get("research", "research")

        # Diagrams
        if suffix in (".mermaid", ".puml", ".drawio") or ("diagram" in name and suffix in (".md", ".svg", ".json")):
            return self.subfolder_cfg.get("diagrams", "diagrams")

        # Media & Visual assets
        if suffix in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".svg"):
            return self.subfolder_cfg.get("media", "media")

        # Markdown documents default to research or raw_artifacts
        if suffix == ".md":
            return self.subfolder_cfg.get("research", "research")

        return self.subfolder_cfg.get("raw_artifacts", "raw_artifacts")

    def extract_title_or_summary(self, file_path: Path) -> str:
        """Extracts title or first heading from markdown files."""
        if file_path.suffix.lower() == ".md" and file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("# "):
                            return line.lstrip("# ").strip()
            except Exception:
                pass
        return file_path.stem.replace("_", " ").title()

    def sync_artifacts(
        self,
        artifact_dir: str,
        conversation_id: str,
        timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans artifact directory, copies files to timestamped target destinations in .docs/,
        and returns catalog of archived items.
        """
        source_dir = Path(artifact_dir).resolve()
        if not source_dir.exists():
            return []

        ts = timestamp or datetime.now()
        ts_str = ts.strftime(self.timestamp_fmt)
        ts_display = ts.strftime("%Y-%m-%d %H:%M:%S")

        archived_items: List[Dict[str, Any]] = []

        # Recursively find all artifact files (excluding internal hidden logs/cache)
        for root, dirs, files in os.walk(source_dir):
            # Ignore internal system generated logs and caches
            if ".system_generated" in root or "__pycache__" in root:
                continue

            for file in files:
                src_file = Path(root) / file
                rel_to_source = src_file.relative_to(source_dir)
                rel_str = str(rel_to_source).replace("\\", "/")

                # Skip system files, temporary locks, and internal IDE metadata json files
                if file.startswith(".") or file.endswith(".metadata.json") or file.endswith(".metadata"):
                    continue

                category = self.determine_category(src_file, rel_str)
                target_folder = self.docs_dir / category
                target_folder.mkdir(parents=True, exist_ok=True)

                base_name = src_file.stem
                ext = src_file.suffix

                # Construct timestamped filename
                timestamped_filename = f"{base_name}_{ts_str}{ext}"
                target_file = target_folder / timestamped_filename

                # Copy file to timestamped version
                shutil.copy2(src_file, target_file)

                # If requested, maintain an active/latest copy (e.g. implementation_plan.md)
                active_file = target_folder / f"{base_name}{ext}"
                if self.keep_latest:
                    shutil.copy2(src_file, active_file)

                item_info = {
                    "original_name": file,
                    "timestamped_name": timestamped_filename,
                    "active_name": f"{base_name}{ext}",
                    "category": category,
                    "rel_timestamped_path": f"{self.docs_root_name}/{category}/{timestamped_filename}",
                    "rel_active_path": f"{self.docs_root_name}/{category}/{base_name}{ext}",
                    "title": self.extract_title_or_summary(src_file),
                    "size_bytes": src_file.stat().st_size,
                    "timestamp": ts_display,
                    "conversation_id": conversation_id
                }
                archived_items.append(item_info)

        return archived_items

    def generate_index_markdown(self) -> str:
        """
        Scans all files inside .docs/ and generates a comprehensive master catalog (INDEX.md).
        """
        if not self.docs_dir.exists():
            return ""

        sections: Dict[str, List[Dict[str, Any]]] = {}

        for root, dirs, files in os.walk(self.docs_dir):
            for file in files:
                if file in ("INDEX.md", "README.md"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.docs_dir)
                parts = rel_path.parts

                category = parts[0] if len(parts) > 1 else "root"
                if category not in sections:
                    sections[category] = []

                size_kb = max(1, file_path.stat().st_size // 1024)
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                title = self.extract_title_or_summary(file_path)

                sections[category].append({
                    "name": file,
                    "rel_url": str(rel_path).replace("\\", "/"),
                    "title": title,
                    "size_kb": size_kb,
                    "mtime": mtime
                })

        category_titles = {
            "plans": "📋 Implementation Plans & Architecture Specifications",
            "walkthroughs": "🚀 Walkthroughs & Verification Summaries",
            "research": "🔬 Research, Analysis & Technical Notes",
            "logs": "📜 Session Logs & Build Transcripts",
            "diagrams": "📊 Architecture Diagrams & Visualizations",
            "media": "🖼️ Generated Media & Visual Artifacts",
            "scratch": "🧪 Scratch Scripts & Experimental Data",
            "raw_artifacts": "📁 General Documents & Artifacts",
            "root": "📄 General Files"
        }

        md = f"""# 📚 Project Documentation Catalog

> Master index of all auto-archived project plans, walkthroughs, research notes, and session logs.  
> Managed automatically by [ag-docs-sync](file:///d:/Development/ag-ext-docs).  
> **Last Updated:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`

---

"""

        for cat_key, cat_title in category_titles.items():
            items = sections.get(cat_key, [])
            if not items:
                continue

            # Sort by modification time descending
            items.sort(key=lambda x: x["mtime"], reverse=True)

            md += f"## {cat_title}\n\n"
            md += "| Document / File | Description / Title | Modified | Size |\n"
            md += "| :--- | :--- | :--- | :--- |\n"
            for item in items:
                md += f"| [`{item['name']}`](./{item['rel_url']}) | {item['title']} | `{item['mtime']}` | `{item['size_kb']} KB` |\n"
            md += "\n"

        return md

    def update_index_file(self) -> Path:
        """Writes the generated master index to .docs/INDEX.md and .docs/README.md."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        content = self.generate_index_markdown()
        index_file = self.docs_dir / "INDEX.md"
        readme_file = self.docs_dir / "README.md"

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(content)
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(content)

        return index_file


if __name__ == "__main__":
    import sys
    ws = sys.argv[1] if len(sys.argv) > 1 else "."
    manager = ArtifactManager(ws)
    print("ArtifactManager ready for workspace:", manager.workspace_path)
