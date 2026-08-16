#!/usr/bin/env python3
"""
Installer and Multi-Runtime Management CLI for ag-docs-sync Antigravity Extension
Supports Antigravity 2.0 (Desktop App), Antigravity CLI (agy), Antigravity IDE, and Antigravity Python SDK.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 console encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config_loader import ConfigLoader

PLUGIN_NAME = "ag-docs-sync"
SOURCE_DIR = SCRIPT_DIR
GLOBAL_PLUGINS_DIR = Path.home() / ".gemini" / "config" / "plugins"
GLOBAL_PLUGIN_DEST = GLOBAL_PLUGINS_DIR / PLUGIN_NAME
GLOBAL_CONFIG_FILE = GLOBAL_PLUGIN_DEST / "config.json"


def copy_plugin_files(dest_dir: Path) -> None:
    """Copies all plugin assets to the target destination."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    items_to_copy = [
        "plugin.json",
        "hooks.json",
        "config.default.json",
        "scripts",
        "rules",
        "skills",
        "ag_docs_sync",
        "setup.py",
        "pyproject.toml",
        "README.md"
    ]

    for item in items_to_copy:
        src_item = SOURCE_DIR / item
        if not src_item.exists():
            continue
        dest_item = dest_dir / item
        if src_item.is_dir():
            if dest_item.exists():
                shutil.rmtree(dest_item)
            shutil.copytree(
                src_item,
                dest_item,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
            )
        else:
            shutil.copy2(src_item, dest_item)

    # If config.json doesn't exist at destination, initialize from config.default.json
    cfg_file = dest_dir / "config.json"
    if not cfg_file.exists():
        src_cfg = SOURCE_DIR / "config.default.json"
        if src_cfg.exists():
            shutil.copy2(src_cfg, cfg_file)


def install_global() -> bool:
    """Installs the plugin globally into ~/.gemini/config/plugins/ag-docs-sync."""
    print(f"📦 Installing '{PLUGIN_NAME}' globally...")
    print(f"   Destination: {GLOBAL_PLUGIN_DEST}")
    copy_plugin_files(GLOBAL_PLUGIN_DEST)
    print(f"✅ Successfully installed '{PLUGIN_NAME}' globally!")
    print(f"   Antigravity will now automatically sync documents for all active projects.")
    return True


def install_local(workspace_path: str) -> bool:
    """Installs the plugin locally in <workspace>/.agents/plugins/ag-docs-sync."""
    ws = Path(workspace_path).resolve()
    dest = ws / ".agents" / "plugins" / PLUGIN_NAME
    print(f"📦 Installing '{PLUGIN_NAME}' locally in workspace: {ws}...")
    print(f"   Destination: {dest}")
    copy_plugin_files(dest)
    print(f"✅ Successfully installed '{PLUGIN_NAME}' locally!")
    return True


def install_sdk() -> bool:
    """Installs the Python SDK package in editable mode in the active Python environment."""
    print("🐍 Installing ag-docs-sync Python package for Antigravity SDK...")
    res = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(SOURCE_DIR)],
        capture_output=True,
        text=True
    )
    if res.returncode == 0:
        print("✅ Successfully installed ag-docs-sync Python SDK integration!")
        print("   You can now use `from ag_docs_sync import AntigravityDocsHook, sync_session` in Python scripts.")
        return True
    else:
        print(f"⚠️  Pip install warning:\n{res.stderr or res.stdout}")
        return False


def build_vsix() -> Optional[Path]:
    """Builds the extension and packages a .vsix file."""
    print("🔨 Compiling extension bundle (esbuild)...")
    res = subprocess.run(["node", "esbuild.js"], cwd=str(SOURCE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Build failed:\n{res.stderr}")
        return None
    print("📦 Packaging .vsix file...")
    cmd = ["npx", "@vscode/vsce", "package", "--no-git-tag-version"]
    if sys.platform == "win32":
        cmd = ["npx.cmd", "@vscode/vsce", "package", "--no-git-tag-version"]
    res2 = subprocess.run(cmd, cwd=str(SOURCE_DIR), capture_output=True, text=True)
    if res2.returncode != 0:
        print(f"❌ VSIX packaging failed:\n{res2.stderr or res2.stdout}")
        return None

    for f in SOURCE_DIR.glob("*.vsix"):
        print(f"✅ Created VSIX package: {f.name}")
        return f
    return None


def install_ide_extension(vsix_file: Optional[Path] = None) -> bool:
    """Installs the packaged VSIX into Antigravity IDE / VS Code."""
    if not vsix_file:
        vsix_file = build_vsix()
    if not vsix_file or not vsix_file.exists():
        print("❌ Could not locate VSIX file to install.")
        return False

    print(f"🧩 Installing extension '{vsix_file.name}' into Antigravity IDE / VS Code...")
    installed = False

    # Check for CLI commands: antigravity, code
    for bin_name in ["antigravity", "code"]:
        cmd_path = shutil.which(bin_name)
        if cmd_path:
            try:
                res = subprocess.run([cmd_path, "--install-extension", str(vsix_file), "--force"], capture_output=True, text=True)
                if res.returncode == 0:
                    print(f"✅ Successfully installed into {bin_name} via `{bin_name} --install-extension`")
                    installed = True
            except Exception as e:
                print(f"ℹ️  Could not run {bin_name} CLI: {e}")

    if not installed:
        print(f"💡 Tip: You can install the VSIX manually in Antigravity IDE via 'Extensions -> Install from VSIX...':\n   Path: {vsix_file}")

    return True


def install_all() -> None:
    """Configures ag-docs-sync for all detected Antigravity runtimes."""
    print("=" * 65)
    print("🚀 Installing ag-docs-sync Universal Support (All Antigravity Versions)")
    print("=" * 65)
    
    # 1. Global Plugin
    install_global()
    print()

    # 2. Python SDK module
    install_sdk()
    print()

    # 3. Antigravity IDE VSIX
    vsix = build_vsix()
    if vsix:
        install_ide_extension(vsix)
    print()

    show_status()


def uninstall_global():
    """Removes the globally installed plugin."""
    if GLOBAL_PLUGIN_DEST.exists():
        shutil.rmtree(GLOBAL_PLUGIN_DEST)
        print(f"🗑️  Successfully uninstalled global '{PLUGIN_NAME}'.")
    else:
        print(f"ℹ️  '{PLUGIN_NAME}' is not installed globally.")


def get_global_config() -> dict:
    if GLOBAL_CONFIG_FILE.exists():
        try:
            with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"exclude_projects": [], "enabled": True}


def save_global_config(cfg: dict):
    GLOBAL_PLUGIN_DEST.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def exclude_project(project_path: str):
    """Adds a project path to the global exclusion list."""
    cfg = get_global_config()
    if "exclude_projects" not in cfg:
        cfg["exclude_projects"] = []

    norm_path = os.path.abspath(os.path.expanduser(project_path))
    if norm_path not in cfg["exclude_projects"]:
        cfg["exclude_projects"].append(norm_path)
        save_global_config(cfg)
        print(f"🚫 Excluded project: '{norm_path}'")
        print(f"   ag-docs-sync will skip this project during Antigravity runs.")
    else:
        print(f"ℹ️  Project '{norm_path}' is already in the exclusion list.")


def unexclude_project(project_path: str):
    """Removes a project path from the global exclusion list."""
    cfg = get_global_config()
    exclude_list = cfg.get("exclude_projects", [])

    norm_path = os.path.abspath(os.path.expanduser(project_path)).replace("\\", "/").lower()
    new_list = [p for p in exclude_list if os.path.abspath(p).replace("\\", "/").lower() != norm_path]

    if len(new_list) != len(exclude_list):
        cfg["exclude_projects"] = new_list
        save_global_config(cfg)
        print(f"✅ Re-enabled project: '{project_path}'")
    else:
        print(f"ℹ️  Project '{project_path}' was not found in the exclusion list.")


def list_excluded():
    """Lists all currently excluded projects."""
    cfg = get_global_config()
    exclusions = cfg.get("exclude_projects", [])
    print("\n🚫 Excluded Projects:")
    if not exclusions:
        print("   (No projects currently excluded. Auto-sync is active for all projects.)")
    else:
        for idx, exc in enumerate(exclusions, 1):
            print(f"   {idx}. {exc}")
    print()


def show_status():
    """Prints current multi-runtime status of the plugin and exclusions."""
    is_installed = GLOBAL_PLUGIN_DEST.exists()
    cfg = get_global_config()
    enabled = cfg.get("enabled", True)

    loader = ConfigLoader()
    runtimes = loader.detect_antigravity_runtimes()

    print("\n" + "=" * 65)
    print(f" 🚀 Antigravity Extension Status: {PLUGIN_NAME}")
    print("=" * 65)
    print(f"  • AI Agent Plugin (Global) : {'✅ Installed' if is_installed else '❌ Not Installed'}")
    print(f"  • Global Plugin Location   : {GLOBAL_PLUGIN_DEST}")
    print(f"  • Master Auto-Sync Switch  : {'🟢 Enabled' if enabled else '🔴 Disabled'}")
    print(f"  • Excluded Projects Count  : {len(cfg.get('exclude_projects', []))}")
    print("-" * 65)
    print(" 📡 Antigravity Multi-Runtime Ecosystem Detection:")
    for key, info in runtimes.items():
        icon = "✅ Detected" if info["detected"] else "⚪ Not found"
        loc = f" -> {info['path']}" if info.get("path") else ""
        print(f"  • {info['name']:<25} : {icon}{loc}")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Manage ag-docs-sync Antigravity Multi-Runtime Extension")
    parser.add_argument("--vsix", action="store_true", help="Build and package .vsix for Antigravity IDE")
    parser.add_argument("--all", action="store_true", help="Configure for all Antigravity runtimes (IDE, 2.0, CLI, SDK)")
    parser.add_argument("--ide", action="store_true", help="Build and install Antigravity IDE extension")
    parser.add_argument("--sdk", action="store_true", help="Install Python SDK integration")
    parser.add_argument("--cli", action="store_true", help="Configure Antigravity CLI (agy)")
    parser.add_argument("--app", "--v2", action="store_true", dest="is_app", help="Configure Antigravity 2.0 desktop app")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # install
    install_parser = subparsers.add_parser("install", help="Install the extension")
    install_parser.add_argument("--global", "-g", dest="is_global", action="store_true", default=True, help="Install AI Agent plugin globally (default)")
    install_parser.add_argument("--local", "-l", metavar="WORKSPACE", help="Install in a specific workspace")
    install_parser.add_argument("--all", "-a", dest="install_all", action="store_true", help="Install for all runtimes (IDE, 2.0, CLI, SDK)")
    install_parser.add_argument("--vsix", action="store_true", help="Build and package .vsix for Antigravity IDE")
    install_parser.add_argument("--ide", action="store_true", help="Install IDE VSIX extension")
    install_parser.add_argument("--sdk", action="store_true", help="Install Python SDK integration")
    install_parser.add_argument("--cli", action="store_true", help="Configure for CLI (agy)")
    install_parser.add_argument("--app", "--v2", dest="install_app", action="store_true", help="Configure for Antigravity 2.0")

    # package / build-vsix
    subparsers.add_parser("build-vsix", help="Build and package .vsix for IDE installation")

    # uninstall
    subparsers.add_parser("uninstall", help="Uninstall the global extension")

    # status
    subparsers.add_parser("status", help="Show extension installation and multi-runtime configuration status")

    # exclude
    exclude_parser = subparsers.add_parser("exclude", help="Exclude a project from auto-sync")
    exclude_parser.add_argument("project_path", help="Path to the project to exclude")

    # unexclude
    unexclude_parser = subparsers.add_parser("unexclude", help="Re-enable a project for auto-sync")
    unexclude_parser.add_argument("project_path", help="Path to the project to re-enable")

    # list-excluded
    subparsers.add_parser("list-excluded", help="List all excluded projects")

    args = parser.parse_args()

    # Handle top-level flags
    if args.all or (args.command == "install" and getattr(args, "install_all", False)):
        install_all()
        return

    if args.sdk or (args.command == "install" and getattr(args, "sdk", False)):
        install_sdk()
        return

    if args.ide or (args.command == "install" and getattr(args, "ide", False)):
        vsix = build_vsix()
        if vsix:
            install_ide_extension(vsix)
        return

    if getattr(args, "vsix", False) or args.command == "build-vsix":
        build_vsix()
        if args.command != "install" and not getattr(args, "local", None):
            install_global()
            show_status()
            return

    if args.command == "install":
        if args.local:
            install_local(args.local)
        else:
            install_global()
    elif args.command == "uninstall":
        uninstall_global()
    elif args.command == "status":
        show_status()
    elif args.command == "exclude":
        exclude_project(args.project_path)
    elif args.command == "unexclude":
        unexclude_project(args.project_path)
    elif args.command == "list-excluded":
        list_excluded()
    else:
        # Default behavior: install globally & show multi-runtime status
        install_global()
        show_status()


if __name__ == "__main__":
    main()
