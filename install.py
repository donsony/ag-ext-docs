#!/usr/bin/env python3
"""
Installer and Management CLI for ag-docs-sync Antigravity Extension
Supports global (~/.gemini/config/plugins/) or workspace-local installation,
and manages project exclusions.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 console encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


PLUGIN_NAME = "ag-docs-sync"
SOURCE_DIR = Path(__file__).resolve().parent
GLOBAL_PLUGINS_DIR = Path.home() / ".gemini" / "config" / "plugins"
GLOBAL_PLUGIN_DEST = GLOBAL_PLUGINS_DIR / PLUGIN_NAME
GLOBAL_CONFIG_FILE = GLOBAL_PLUGIN_DEST / "config.json"


def copy_plugin_files(dest_dir: Path):
    """Copies all plugin assets to the target destination."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    items_to_copy = [
        "plugin.json",
        "hooks.json",
        "config.default.json",
        "scripts",
        "rules",
        "skills",
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
            shutil.copytree(src_item, dest_item)
        else:
            shutil.copy2(src_item, dest_item)

    # If config.json doesn't exist at destination, initialize from config.default.json
    cfg_file = dest_dir / "config.json"
    if not cfg_file.exists():
        src_cfg = SOURCE_DIR / "config.default.json"
        if src_cfg.exists():
            shutil.copy2(src_cfg, cfg_file)


def install_global():
    """Installs the plugin globally into ~/.gemini/config/plugins/ag-docs-sync."""
    print(f"📦 Installing '{PLUGIN_NAME}' globally...")
    print(f"   Destination: {GLOBAL_PLUGIN_DEST}")
    copy_plugin_files(GLOBAL_PLUGIN_DEST)
    print(f"✅ Successfully installed '{PLUGIN_NAME}' globally!")
    print(f"   Antigravity will now automatically sync documents for all active projects.")


def install_local(workspace_path: str):
    """Installs the plugin locally in <workspace>/.agents/plugins/ag-docs-sync."""
    ws = Path(workspace_path).resolve()
    dest = ws / ".agents" / "plugins" / PLUGIN_NAME
    print(f"📦 Installing '{PLUGIN_NAME}' locally in workspace: {ws}...")
    print(f"   Destination: {dest}")
    copy_plugin_files(dest)
    print(f"✅ Successfully installed '{PLUGIN_NAME}' locally!")


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


def build_vsix() -> Optional[Path]:
    """Builds the extension and packages a .vsix file."""
    print("🔨 Compiling extension bundle (esbuild)...")
    res = subprocess.run(["node", "esbuild.js"], cwd=str(SOURCE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Build failed:\n{res.stderr}")
        return None
    print("📦 Packaging .vsix file...")
    # Try npx @vscode/vsce
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


def show_status():
    """Prints current status of the plugin and exclusions."""
    is_installed = GLOBAL_PLUGIN_DEST.exists()
    cfg = get_global_config()
    enabled = cfg.get("enabled", True)

    print("\n" + "=" * 60)
    print(f" 🚀 Antigravity Extension Status: {PLUGIN_NAME}")
    print("=" * 60)
    print(f"  • AI Agent Plugin (Global) : {'✅ Installed' if is_installed else '❌ Not Installed'}")
    print(f"  • Global Location          : {GLOBAL_PLUGIN_DEST}")
    print(f"  • Master Switch            : {'🟢 Enabled' if enabled else '🔴 Disabled'}")
    print(f"  • Excluded Projects        : {len(cfg.get('exclude_projects', []))}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Manage ag-docs-sync Antigravity Extension")
    parser.add_argument("--vsix", action="store_true", help="Build and package .vsix for Antigravity IDE")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # install
    install_parser = subparsers.add_parser("install", help="Install the extension")
    install_parser.add_argument("--global", "-g", dest="is_global", action="store_true", default=True, help="Install AI Agent plugin globally (default)")
    install_parser.add_argument("--local", "-l", metavar="WORKSPACE", help="Install in a specific workspace")
    install_parser.add_argument("--vsix", action="store_true", help="Build and package .vsix for Antigravity IDE")

    # package / build-vsix
    subparsers.add_parser("build-vsix", help="Build and package .vsix for IDE installation")

    # uninstall
    subparsers.add_parser("uninstall", help="Uninstall the global extension")

    # status
    subparsers.add_parser("status", help="Show extension installation and configuration status")

    # exclude
    exclude_parser = subparsers.add_parser("exclude", help="Exclude a project from auto-sync")
    exclude_parser.add_argument("project_path", help="Path to the project to exclude")

    # unexclude
    unexclude_parser = subparsers.add_parser("unexclude", help="Re-enable a project for auto-sync")
    unexclude_parser.add_argument("project_path", help="Path to the project to re-enable")

    # list-excluded
    subparsers.add_parser("list-excluded", help="List all excluded projects")

    args = parser.parse_args()

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
        # Default behavior: install globally if no args
        install_global()
        show_status()


if __name__ == "__main__":
    main()


