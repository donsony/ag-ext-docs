#!/usr/bin/env python3
"""
Main Entry Point and Universal Sync Engine for ag-docs-sync
Supports Antigravity 2.0, Antigravity CLI (agy), Antigravity IDE, and Antigravity Python SDK.
Archives artifacts and session transcripts into .docs/
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 console encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add script directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import ConfigLoader
from artifact_manager import ArtifactManager
from log_formatter import LogFormatter


def get_known_brain_roots() -> List[Path]:
    """Returns all possible brain root paths across all Antigravity runtimes & env overrides."""
    home_dir = Path.home()
    roots: List[Path] = []

    # 1. Environment variable overrides
    env_vars = [
        "ANTIGRAVITY_BRAIN_DIR",
        "ANTIGRAVITY_DATA_DIR",
        "AGY_DATA_DIR",
        "GEMINI_DATA_DIR",
        "GEMINI_HOME"
    ]
    for ev in env_vars:
        val = os.environ.get(ev)
        if val:
            p = Path(val).resolve()
            if p.name == "brain":
                roots.append(p)
            else:
                roots.append(p / "brain")
                roots.append(p)

    # 2. Standard runtime directories under ~/.gemini
    for variant in ConfigLoader.KNOWN_VARIANTS:
        roots.append(home_dir / ".gemini" / variant / "brain")
        roots.append(home_dir / ".gemini" / variant)

    # 3. Direct brain directory if present
    roots.append(home_dir / ".gemini" / "brain")

    # Filter to existing directories and deduplicate
    seen = set()
    existing_roots: List[Path] = []
    for r in roots:
        r_str = str(r).lower()
        if r_str not in seen and r.exists():
            seen.add(r_str)
            existing_roots.append(r)

    return existing_roots


def find_latest_conversation(brain_roots: List[Path]) -> Optional[Tuple[str, Path]]:
    """
    Searches across all Antigravity brain directories for the most recently active conversation.
    Returns (conversation_id, conversation_dir).
    """
    latest_conv: Optional[Tuple[str, Path, float]] = None

    for root in brain_roots:
        if not root.exists() or not root.is_dir():
            continue
        try:
            for item in root.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    mtime = item.stat().st_mtime
                    if latest_conv is None or mtime > latest_conv[2]:
                        latest_conv = (item.name, item, mtime)
        except Exception:
            continue

    if latest_conv:
        return (latest_conv[0], latest_conv[1])
    return None


def resolve_paths(payload: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Optional[str]]:
    """
    Universally resolves workspace path, conversation ID, transcript path, and artifact directory
    across all Antigravity versions (IDE, 2.0, CLI, and SDK).
    """
    # 1. Workspace path
    workspace_path = getattr(args, "workspace", None)
    if not workspace_path and "workspacePaths" in payload and payload["workspacePaths"]:
        workspace_path = payload["workspacePaths"][0]
    if not workspace_path and "workspace_path" in payload:
        workspace_path = payload["workspace_path"]
    if not workspace_path:
        workspace_path = os.getcwd()

    workspace_path = str(Path(workspace_path).resolve())

    brain_roots = get_known_brain_roots()

    # 2. Conversation ID
    conversation_id = getattr(args, "conversation_id", None) or payload.get("conversationId") or payload.get("conversation_id")
    conv_dir: Optional[Path] = None

    if conversation_id and conversation_id not in ("latest", "auto", "session"):
        # Search for this explicit conversation in brain roots
        for root in brain_roots:
            candidate = root / conversation_id if root.name == "brain" else root / "brain" / conversation_id
            if candidate.exists():
                conv_dir = candidate
                break
    else:
        # Resolve latest active conversation
        latest = find_latest_conversation(brain_roots)
        if latest:
            conversation_id, conv_dir = latest
        else:
            conversation_id = conversation_id or "session"

    # 3. Transcript path
    transcript_path = getattr(args, "transcript", None) or payload.get("transcriptPath") or payload.get("transcript_path")
    if not transcript_path and conv_dir:
        # Check standard locations
        candidates = [
            conv_dir / ".system_generated" / "logs" / "transcript.jsonl",
            conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl",
            conv_dir / "transcript.jsonl",
            conv_dir / "logs" / "transcript.jsonl"
        ]
        for cand in candidates:
            if cand.exists() and cand.stat().st_size > 0:
                transcript_path = str(cand)
                break

    # If still not found, search all brain roots for this conversation_id
    if not transcript_path and conversation_id and conversation_id != "session":
        for root in brain_roots:
            cand = (root / conversation_id / ".system_generated" / "logs" / "transcript.jsonl") if root.name == "brain" else (root / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl")
            if cand.exists():
                transcript_path = str(cand)
                break

    # 4. Artifact directory path
    artifact_dir = getattr(args, "artifacts", None) or payload.get("artifactDirectoryPath") or payload.get("artifact_directory_path")
    if not artifact_dir and conv_dir and conv_dir.exists():
        artifact_dir = str(conv_dir)
    elif not artifact_dir and conversation_id and conversation_id != "session":
        for root in brain_roots:
            cand = root / conversation_id if root.name == "brain" else root / "brain" / conversation_id
            if cand.exists():
                artifact_dir = str(cand)
                break

    return {
        "workspace_path": workspace_path,
        "conversation_id": conversation_id,
        "transcript_path": transcript_path,
        "artifact_dir": artifact_dir
    }


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


def sync_docs_session(
    workspace_path: str,
    conversation_id: Optional[str] = None,
    transcript_path: Optional[str] = None,
    artifact_dir: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Programmatic API to sync artifacts and transcripts for an Antigravity session.
    Used by Python SDK, IDE extension, CLI, and lifecycle hooks.
    """
    ws_path = str(Path(workspace_path).resolve())
    config_loader = ConfigLoader(workspace_path=ws_path)
    merged_config = config_loader.config
    if config:
        config_loader._deep_update(merged_config, config)

    if not force:
        is_excluded, reason = config_loader.is_project_excluded(ws_path)
        if is_excluded:
            return {
                "success": False,
                "skipped": True,
                "reason": reason,
                "workspace": ws_path
            }

    # Resolve paths if not fully provided
    dummy_args = argparse.Namespace(
        workspace=ws_path,
        conversation_id=conversation_id,
        transcript=transcript_path,
        artifacts=artifact_dir,
        force=force
    )
    resolved = resolve_paths({}, dummy_args)

    conv_id = resolved["conversation_id"] or conversation_id or "session"
    t_path = resolved["transcript_path"] or transcript_path
    a_dir = resolved["artifact_dir"] or artifact_dir

    now = datetime.now()
    timestamp_tag = now.strftime(merged_config.get("timestamp_format", "%Y-%m-%d_%H%M%S"))

    # 1. Process Artifacts
    artifact_mgr = ArtifactManager(ws_path, config=merged_config)
    archived_artifacts = []
    if a_dir and Path(a_dir).exists():
        try:
            archived_artifacts = artifact_mgr.sync_artifacts(a_dir, conv_id, timestamp=now)
        except Exception as e:
            sys.stderr.write(f"[ag-docs-sync] Error archiving artifacts: {e}\n")

    # 2. Process Session Transcript & Generate Color-Coded Markdown Log
    log_formatter = LogFormatter(config=merged_config)
    session_meta: Dict[str, Any] = {}
    if t_path and Path(t_path).exists():
        try:
            log_md, session_meta = log_formatter.generate_session_markdown(
                transcript_path=t_path,
                conversation_id=conv_id,
                workspace_path=ws_path,
                session_time=now
            )

            logs_dir = artifact_mgr.docs_dir / merged_config.get("subfolders", {}).get("logs", "logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_filename = f"session_{timestamp_tag}_{conv_id[:8]}.md"
            log_filepath = logs_dir / log_filename
            with open(log_filepath, "w", encoding="utf-8") as f:
                f.write(log_md)

            latest_filepath = logs_dir / "LATEST_SESSION.md"
            with open(latest_filepath, "w", encoding="utf-8") as f:
                f.write(log_md)

            timeline_path = logs_dir / "TIMELINE.md"
            log_formatter.update_timeline_index(timeline_path, session_meta, f"./{log_filename}")
        except Exception as e:
            sys.stderr.write(f"[ag-docs-sync] Error generating session markdown: {e}\n")

    # 3. Update Master Documentation Catalog (INDEX.md / README.md)
    index_path = None
    try:
        index_path = str(artifact_mgr.update_index_file())
    except Exception as e:
        sys.stderr.write(f"[ag-docs-sync] Error updating INDEX.md: {e}\n")

    return {
        "success": True,
        "skipped": False,
        "workspace": ws_path,
        "conversation_id": conv_id,
        "archived_artifacts_count": len(archived_artifacts),
        "transcript_synced": bool(t_path and Path(t_path).exists()),
        "index_updated": bool(index_path),
        "session_metrics": session_meta
    }


def main():
    parser = argparse.ArgumentParser(description="Antigravity Documentation & Session Log Sync Engine (Universal Multi-Version)")
    parser.add_argument("--workspace", "-w", help="Workspace path to process")
    parser.add_argument("--conversation-id", "-c", help="Antigravity conversation ID (or 'latest')")
    parser.add_argument("--transcript", "-t", help="Path to transcript.jsonl")
    parser.add_argument("--artifacts", "-a", help="Path to artifacts directory")
    parser.add_argument("--force", "-f", action="store_true", help="Bypass project exclusion checks")
    parser.add_argument("--hook", action="store_true", help="Indicates invocation via Antigravity lifecycle hook")
    args, unknown = parser.parse_known_args()

    # Read stdin payload if called by Antigravity Hook
    payload = {}
    if args.hook or not (args.workspace and args.transcript and args.artifacts):
        payload = parse_hook_stdin()

    paths = resolve_paths(payload, args)

    workspace_path = paths["workspace_path"]
    conversation_id = paths["conversation_id"]
    transcript_path = paths["transcript_path"]
    artifact_dir = paths["artifact_dir"]

    result = sync_docs_session(
        workspace_path=workspace_path,
        conversation_id=conversation_id,
        transcript_path=transcript_path,
        artifact_dir=artifact_dir,
        force=args.force
    )

    if result.get("skipped"):
        sys.stderr.write(f"[ag-docs-sync] Skipping workspace '{workspace_path}': {result.get('reason')}\n")
        # Return empty JSON object as expected by Antigravity Hook contract
        print(json.dumps({}))
        sys.exit(0)

    # Output valid JSON hook result
    print(json.dumps({}))
    sys.exit(0)


if __name__ == "__main__":
    main()
