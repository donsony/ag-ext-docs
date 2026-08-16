#!/usr/bin/env python3
"""
Configuration Loader, Multi-Runtime Discovery & Project Exclusion Evaluator for ag-docs-sync
Supports Antigravity 2.0, Antigravity CLI (agy), Antigravity IDE, and Antigravity Python SDK.
"""

import fnmatch
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ConfigLoader:
    # Known Antigravity runtime variant directory names under ~/.gemini or custom roots
    KNOWN_VARIANTS = [
        "antigravity-ide",    # Antigravity IDE (VS Code-based)
        "antigravity",        # Antigravity 2.0 (Standard desktop runtime)
        "antigravity-2.0",    # Antigravity 2.0 (Explicit naming)
        "antigravity-app",    # Antigravity 2.0 Desktop App
        "antigravity-cli",    # Antigravity CLI (agy)
        "antigravity-sdk",    # Antigravity Python SDK
        "sdk",                # Generic SDK
    ]

    def __init__(self, plugin_dir: Optional[Path] = None, workspace_path: Optional[str] = None):
        self.plugin_dir = plugin_dir or Path(__file__).resolve().parent.parent
        self.home_dir = Path.home()
        self.global_config_dir = self.home_dir / ".gemini" / "config" / "plugins" / "ag-docs-sync"
        self.global_config_file = self.global_config_dir / "config.json"
        self.default_config_file = self.plugin_dir / "config.default.json"
        self.workspace_path = Path(workspace_path).resolve() if workspace_path else None
        self.config = self._load_merged_config()

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ag-docs-sync] Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return {}

    def _load_merged_config(self) -> Dict[str, Any]:
        # 1. Load default config
        config = self._load_json_file(self.default_config_file)

        # 2. Merge global plugin config (~/.gemini/config/plugins/ag-docs-sync/config.json)
        global_config = self._load_json_file(self.global_config_file)
        self._deep_update(config, global_config)

        # 3. Merge variant-specific configs if present (e.g. CLI or 2.0 custom configs)
        for variant in self.KNOWN_VARIANTS:
            variant_cfg = self.home_dir / ".gemini" / variant / "ag-docs-sync.json"
            if variant_cfg.exists():
                self._deep_update(config, self._load_json_file(variant_cfg))

        # 4. Merge environment-variable specified config file if present
        env_config = os.environ.get("AG_DOCS_CONFIG")
        if env_config and Path(env_config).exists():
            self._deep_update(config, self._load_json_file(Path(env_config)))

        # 5. Merge workspace local config if present (.docs-sync.json, .ag-docs-config.json, .agents/ag-docs-sync.json)
        if self.workspace_path and self.workspace_path.exists():
            candidates = [
                self.workspace_path / ".docs-sync.json",
                self.workspace_path / ".ag-docs-config.json",
                self.workspace_path / ".agents" / "ag-docs-sync.json",
                self.workspace_path / ".agents" / "config.json"
            ]
            for cand in candidates:
                if cand.exists():
                    local_config = self._load_json_file(cand)
                    # If config is namespaced under 'ag-docs-sync' or 'docs_sync'
                    if "ag-docs-sync" in local_config:
                        self._deep_update(config, local_config["ag-docs-sync"])
                    elif "docs_sync" in local_config:
                        self._deep_update(config, local_config["docs_sync"])
                    else:
                        self._deep_update(config, local_config)
                    break

        return config

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        for k, v in update_dict.items():
            if isinstance(v, dict) and k in base_dict and isinstance(base_dict[k], dict):
                self._deep_update(base_dict[k], v)
            else:
                base_dict[k] = v

    @staticmethod
    def normalize_path_str(p: str) -> str:
        if not p:
            return ""
        norm = os.path.abspath(os.path.expanduser(p))
        return norm.replace("\\", "/").rstrip("/").lower()

    def is_project_excluded(self, workspace_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Evaluates whether the specified workspace should be excluded from sync.
        Returns (is_excluded: bool, reason: str).
        """
        target_path = Path(workspace_path).resolve() if workspace_path else self.workspace_path
        if not target_path:
            return True, "No workspace path specified"

        # 1. Check for local opt-out marker files in workspace root
        ignore_files = [".docs-ignore", ".ag-docs-ignore", ".docsignore"]
        for ig in ignore_files:
            if (target_path / ig).exists():
                return True, f"Found local ignore marker '{ig}' in workspace root"

        # 2. Check workspace local config enabled flag
        for cand in [target_path / ".docs-sync.json", target_path / ".ag-docs-config.json", target_path / ".agents" / "ag-docs-sync.json"]:
            if cand.exists():
                ws_cfg = self._load_json_file(cand)
                if ws_cfg.get("enabled") is False or ws_cfg.get("ag-docs-sync", {}).get("enabled") is False:
                    return True, "Workspace local configuration explicitly disabled sync"

        # 3. Check if global master switch is enabled
        if not self.config.get("enabled", True):
            return True, "Extension disabled in global config"

        target_norm = self.normalize_path_str(str(target_path))
        target_name = target_path.name.lower()

        # 4. Check opt-in mode
        if self.config.get("opt_in_mode", False):
            include_projects = self.config.get("include_projects", [])
            matched = False
            for inc in include_projects:
                inc_norm = self.normalize_path_str(inc)
                if inc_norm == target_norm or fnmatch.fnmatch(target_norm, inc_norm) or target_name == inc.lower():
                    matched = True
                    break
            if not matched:
                return True, "Opt-in mode is active and this project is not in include_projects"

        # 5. Check exclude_projects list
        exclude_projects = self.config.get("exclude_projects", [])
        for exc in exclude_projects:
            if not exc:
                continue
            exc_str = str(exc).strip()
            exc_norm = self.normalize_path_str(exc_str)

            # Check exact match
            if exc_norm == target_norm or target_name == exc_str.lower():
                return True, f"Matched excluded project rule '{exc}'"

            # Check glob pattern
            if fnmatch.fnmatch(target_norm, exc_norm) or fnmatch.fnmatch(target_name, exc_str.lower()):
                return True, f"Matched excluded project pattern '{exc}'"

            # Check substring / parent directory exclusion
            if target_norm.startswith(exc_norm + "/"):
                return True, f"Workspace is inside excluded parent directory '{exc}'"

        # 6. Check exclude_patterns
        exclude_patterns = self.config.get("exclude_patterns", [])
        for pat in exclude_patterns:
            if not pat:
                continue
            pat_norm = pat.replace("\\", "/").lower()
            if fnmatch.fnmatch(target_norm, pat_norm):
                return True, f"Matched exclusion pattern '{pat}'"

        return False, "Project is active for documentation synchronization"

    def add_project_exclusion(self, project_path: str) -> None:
        """Adds a project path to the global exclusion list and persists it."""
        self.global_config_dir.mkdir(parents=True, exist_ok=True)
        global_cfg = self._load_json_file(self.global_config_file)
        if "exclude_projects" not in global_cfg:
            global_cfg["exclude_projects"] = []

        norm = os.path.abspath(os.path.expanduser(str(project_path).strip()))
        if norm not in global_cfg["exclude_projects"]:
            global_cfg["exclude_projects"].append(norm)

        with open(self.global_config_file, "w", encoding="utf-8") as f:
            json.dump(global_cfg, f, indent=2)

    def remove_project_exclusion(self, project_path: str) -> bool:
        """Removes a project path from the global exclusion list."""
        if not self.global_config_file.exists():
            return False
        global_cfg = self._load_json_file(self.global_config_file)
        exclude_list = global_cfg.get("exclude_projects", [])

        norm_target = self.normalize_path_str(project_path)
        new_list = [
            p for p in exclude_list
            if p != project_path and self.normalize_path_str(p) != norm_target
        ]

        if len(new_list) != len(exclude_list):
            global_cfg["exclude_projects"] = new_list
            with open(self.global_config_file, "w", encoding="utf-8") as f:
                json.dump(global_cfg, f, indent=2)
            return True
        return False

    def list_exclusions(self) -> List[str]:
        """Returns all configured project exclusions."""
        return self.config.get("exclude_projects", [])

    def detect_antigravity_runtimes(self) -> Dict[str, Dict[str, Any]]:
        """
        Scans system for all types and versions of Google Antigravity:
        - Antigravity 2.0 (Desktop App)
        - Antigravity CLI (agy)
        - Antigravity IDE (VS Code-based)
        - Antigravity Python SDK (google-antigravity)
        """
        results: Dict[str, Dict[str, Any]] = {
            "ide": {
                "name": "Antigravity IDE",
                "detected": False,
                "path": None,
                "type": "Standalone IDE (VS Code-based)",
                "data_dir": str(self.home_dir / ".gemini" / "antigravity-ide")
            },
            "app_2_0": {
                "name": "Antigravity 2.0",
                "detected": False,
                "path": None,
                "type": "Desktop Application",
                "data_dir": str(self.home_dir / ".gemini" / "antigravity")
            },
            "cli": {
                "name": "Antigravity CLI (agy)",
                "detected": False,
                "path": None,
                "type": "Terminal CLI / TUI",
                "data_dir": str(self.home_dir / ".gemini" / "antigravity-cli")
            },
            "sdk": {
                "name": "Antigravity Python SDK",
                "detected": False,
                "path": None,
                "type": "Programmatic Python Library (google-antigravity)",
                "data_dir": str(self.home_dir / ".gemini" / "antigravity-sdk")
            },
            "global_customizations": {
                "name": "Global Customizations Root",
                "detected": False,
                "path": str(self.home_dir / ".gemini" / "config"),
                "type": "Shared Customizations Engine (Skills/Rules/Plugins/Hooks)"
            }
        }

        # 1. Check IDE
        ide_dir = self.home_dir / ".gemini" / "antigravity-ide"
        if ide_dir.exists():
            results["ide"]["detected"] = True
            results["ide"]["path"] = str(ide_dir)

        # 2. Check 2.0 Desktop App
        app_dir = self.home_dir / ".gemini" / "antigravity"
        app_2_dir = self.home_dir / ".gemini" / "antigravity-2.0"
        if app_dir.exists():
            results["app_2_0"]["detected"] = True
            results["app_2_0"]["path"] = str(app_dir)
        elif app_2_dir.exists():
            results["app_2_0"]["detected"] = True
            results["app_2_0"]["path"] = str(app_2_dir)

        # 3. Check CLI (agy in PATH or ~/.gemini/antigravity-cli)
        cli_dir = self.home_dir / ".gemini" / "antigravity-cli"
        agy_bin = shutil.which("agy") or shutil.which("antigravity")
        if cli_dir.exists() or agy_bin:
            results["cli"]["detected"] = True
            results["cli"]["path"] = agy_bin or str(cli_dir)

        # 4. Check Python SDK
        try:
            import importlib.util
            sdk_spec = importlib.util.find_spec("google.antigravity")
            if sdk_spec is not None:
                results["sdk"]["detected"] = True
                results["sdk"]["path"] = sdk_spec.origin or "Installed in Python environment"
            else:
                sdk_dir = self.home_dir / ".gemini" / "antigravity-sdk"
                if sdk_dir.exists():
                    results["sdk"]["detected"] = True
                    results["sdk"]["path"] = str(sdk_dir)
        except Exception:
            pass

        # 5. Check Global Customizations Root
        global_root = self.home_dir / ".gemini" / "config"
        if global_root.exists():
            results["global_customizations"]["detected"] = True

        return results


if __name__ == "__main__":
    loader = ConfigLoader()
    print("Loaded configuration successfully.")
    print("Detected Runtimes:")
    for k, v in loader.detect_antigravity_runtimes().items():
        status = "✅ Found" if v["detected"] else "⚪ Not detected"
        print(f"  • {v['name']} ({v['type']}): {status} [{v.get('path') or 'N/A'}]")
    print("Excluded projects:", loader.list_exclusions())
