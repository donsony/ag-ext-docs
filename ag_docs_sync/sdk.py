"""
Antigravity Python SDK Integration Module for ag-docs-sync
Provides native hooks, context managers, and async lifecycle adapters for google-antigravity.
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from sync_docs import sync_docs_session
from config_loader import ConfigLoader
from artifact_manager import ArtifactManager
from log_formatter import LogFormatter


class AntigravityDocsHook:
    """
    Native hook adapter for the Antigravity Python SDK (`google-antigravity`).
    
    Usage with google.antigravity:
    -----------------------------
    ```python
    from google.antigravity import Agent, LocalAgentConfig
    from ag_docs_sync import AntigravityDocsHook

    # 1. Using as context manager
    with AntigravityDocsHook(workspace_path="."):
        async with Agent(config) as agent:
            resp = await agent.chat("Design an authentication microservice")
            ...

    # 2. Or explicit trigger on session finish
    hook = AntigravityDocsHook(workspace_path=".")
    # ... run agent workflow ...
    hook.sync(conversation_id="conv-123")
    ```
    """

    def __init__(
        self,
        workspace_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        force: bool = False
    ):
        self.workspace_path = str(Path(workspace_path or os.getcwd()).resolve())
        self.config = config or {}
        self.force = force
        self.conversation_id: Optional[str] = None
        self.transcript_path: Optional[str] = None
        self.artifact_dir: Optional[str] = None

    def set_session_info(
        self,
        conversation_id: Optional[str] = None,
        transcript_path: Optional[str] = None,
        artifact_dir: Optional[str] = None
    ) -> "AntigravityDocsHook":
        """Registers active session details before or during agent execution."""
        if conversation_id:
            self.conversation_id = conversation_id
        if transcript_path:
            self.transcript_path = transcript_path
        if artifact_dir:
            self.artifact_dir = artifact_dir
        return self

    def sync(
        self,
        conversation_id: Optional[str] = None,
        transcript_path: Optional[str] = None,
        artifact_dir: Optional[str] = None,
        force: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Triggers document and transcript sync into .docs/ immediately."""
        conv_id = conversation_id or self.conversation_id
        t_path = transcript_path or self.transcript_path
        a_dir = artifact_dir or self.artifact_dir
        is_force = self.force if force is None else force

        return sync_docs_session(
            workspace_path=self.workspace_path,
            conversation_id=conv_id,
            transcript_path=t_path,
            artifact_dir=a_dir,
            config=self.config,
            force=is_force
        )

    def on_session_end(self, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Callback suitable for lifecycle event handlers."""
        return self.sync(conversation_id=conversation_id)

    def __enter__(self) -> "AntigravityDocsHook":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Automatically syncs upon exiting context block."""
        try:
            self.sync()
        except Exception as e:
            sys.stderr.write(f"[ag-docs-sync SDK Hook] Error during auto-sync: {e}\n")


def sync_session(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
    transcript_path: Optional[str] = None,
    artifact_dir: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for Python scripts and SDK pipelines to sync documentation.
    """
    ws = workspace_path or os.getcwd()
    return sync_docs_session(
        workspace_path=ws,
        conversation_id=conversation_id,
        transcript_path=transcript_path,
        artifact_dir=artifact_dir,
        config=config,
        force=force
    )


class sync_on_exit:
    """
    Context manager that automatically archives session artifacts and transcripts on exit.
    
    ```python
    with sync_on_exit(workspace_path="."):
        # run agent tasks...
    ```
    """
    def __init__(
        self,
        workspace_path: Optional[str] = None,
        conversation_id: Optional[str] = None,
        force: bool = False
    ):
        self.hook = AntigravityDocsHook(workspace_path=workspace_path, force=force)
        if conversation_id:
            self.hook.set_session_info(conversation_id=conversation_id)

    def __enter__(self) -> AntigravityDocsHook:
        return self.hook

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.hook.sync()
