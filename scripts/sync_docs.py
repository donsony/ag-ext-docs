#!/usr/bin/env python3
"""
Main Entry Point for ag-docs-sync Lifecycle Hook and CLI
Archives artifacts and session transcripts into .docs/
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure UTF-8 console encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add script directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import ConfigLoader
from artifact_manager import ArtifactManager
from log_formatter import LogFormatter


def parse_hook_stdin() -> Dict[str, Any]:
    """Reads and parses JSON payload provided by Antigravity on stdin."""
    if sys.stdin.isatty():
        return {}
    # If explicit CLI arguments are provided without --hook or --stdin, do not block on stdin
    has_hook_flag = any(arg in sys.argv for arg in ("--hook", "--stdin", "-s"))
    if len(sys.argv) > 1 and not has_hook_flag:
        return {}
    try:
        content = sys.stdin.read().strip()
        if content:
            return json.loads(content)
    except Exception as e:
        sys.stderr.write(f"[ag-docs-sync] Error reading stdin hook payload: {e}\n")
    return {}


def resolve_paths(payload: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Optional[str]]:
    """Resolves workspace path, conversation ID, transcript path, and artifact directory."""
    # 1. Workspace path
    workspace_path = args.workspace
    if not workspace_path and "workspacePaths" in payload and payload["workspacePaths"]:
        workspace_path = payload["workspacePaths"][0]
    if not workspace_path and "workspace_path" in payload:
        workspace_path = payload["workspace_path"]
    if not workspace_path:
        workspace_path = os.getcwd()

    workspace_path = str(Path(workspace_path).resolve())

    # 2. Conversation ID
    conversation_id = args.conversation_id or payload.get("conversationId") or payload.get("conversation_id") or "session"

    # 3. Transcript path
    transcript_path = args.transcript or payload.get("transcriptPath") or payload.get("transcript_path")
    if not transcript_path:
        # Check standard location under brain/<conversation_id>/.system_generated/logs/transcript.jsonl
        home_dir = Path.home()
        for variant in ["antigravity-ide", "antigravity", "antigravity-cli"]:
            possible_path = home_dir / ".gemini" / variant / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
            if possible_path.exists():
                transcript_path = str(possible_path)
                break

    # 4. Artifact directory path
    artifact_dir = args.artifacts or payload.get("artifactDirectoryPath") or payload.get("artifact_directory_path")
    if not artifact_dir:
        # Check standard location under brain/<conversation_id>
        home_dir = Path.home()
        for variant in ["antigravity-ide", "antigravity", "antigravity-cli"]:
            possible_path = home_dir / ".gemini" / variant / "brain" / conversation_id
            if possible_path.exists():
                artifact_dir = str(possible_path)
                break

    return {
        "workspace_path": workspace_path,
        "conversation_id": conversation_id,
        "transcript_path": transcript_path,
        "artifact_dir": artifact_dir
    }


def main():
    parser = argparse.ArgumentParser(description="Antigravity Documentation & Session Log Sync Engine")
    parser.add_argument("--workspace", "-w", help="Workspace path to process")
    parser.add_argument("--conversation-id", "-c", help="Antigravity conversation ID")
    parser.add_argument("--transcript", "-t", help="Path to transcript.jsonl")
    parser.add_argument("--artifacts", "-a", help="Path to artifacts directory")
    parser.add_argument("--force", "-f", action="store_true", help="Bypass project exclusion checks")
    args, unknown = parser.parse_known_args()

    # Read stdin payload if called by Antigravity Hook (i.e. CLI args don't fully provide paths)
    payload = {}
    if not (args.workspace and args.transcript and args.artifacts):
        payload = parse_hook_stdin()

    paths = resolve_paths(payload, args)

    workspace_path = paths["workspace_path"]
    conversation_id = paths["conversation_id"]
    transcript_path = paths["transcript_path"]
    artifact_dir = paths["artifact_dir"]

    # Initialize configuration and evaluate exclusions
    config_loader = ConfigLoader(workspace_path=workspace_path)
    config = config_loader.config

    if not args.force:
        is_excluded, reason = config_loader.is_project_excluded(workspace_path)
        if is_excluded:
            # Clean exit for excluded projects
            sys.stderr.write(f"[ag-docs-sync] Skipping workspace '{workspace_path}': {reason}\n")
            # Output empty JSON as required by Antigravity Hook contract
            print(json.dumps({}))
            sys.exit(0)

    now = datetime.now()
    timestamp_tag = now.strftime(config.get("timestamp_format", "%Y-%m-%d_%H%M%S"))

    # 1. Process Artifacts
    artifact_mgr = ArtifactManager(workspace_path, config=config)
    archived_artifacts = []
    if artifact_dir and Path(artifact_dir).exists():
        try:
            archived_artifacts = artifact_mgr.sync_artifacts(artifact_dir, conversation_id, timestamp=now)
        except Exception as e:
            sys.stderr.write(f"[ag-docs-sync] Error archiving artifacts: {e}\n")

    # 2. Process Session Transcript & Generate Color-Coded Markdown Log
    log_formatter = LogFormatter(config=config)
    if transcript_path and Path(transcript_path).exists():
        try:
            log_md, meta = log_formatter.generate_session_markdown(
                transcript_path=transcript_path,
                conversation_id=conversation_id,
                workspace_path=workspace_path,
                session_time=now
            )

            # Write timestamped session log
            logs_dir = artifact_mgr.docs_dir / config.get("subfolders", {}).get("logs", "logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_filename = f"session_{timestamp_tag}_{conversation_id[:8]}.md"
            log_filepath = logs_dir / log_filename
            with open(log_filepath, "w", encoding="utf-8") as f:
                f.write(log_md)

            # Write active/latest copy
            latest_filepath = logs_dir / "LATEST_SESSION.md"
            with open(latest_filepath, "w", encoding="utf-8") as f:
                f.write(log_md)

            # Update timeline index
            timeline_path = logs_dir / "TIMELINE.md"
            log_formatter.update_timeline_index(timeline_path, meta, f"./{log_filename}")

        except Exception as e:
            sys.stderr.write(f"[ag-docs-sync] Error generating session markdown: {e}\n")

    # 3. Update Master Documentation Catalog (INDEX.md / README.md)
    try:
        artifact_mgr.update_index_file()
    except Exception as e:
        sys.stderr.write(f"[ag-docs-sync] Error updating INDEX.md: {e}\n")

    # Return valid Hook JSON Response on stdout
    print(json.dumps({}))
    sys.exit(0)


if __name__ == "__main__":
    main()
