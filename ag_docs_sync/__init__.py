"""
ag-docs-sync: Universal Documentation & Session Transcript Archiver for Google Antigravity.
Supports Antigravity 2.0, Antigravity CLI (agy), Antigravity IDE, and Antigravity Python SDK.
"""

from .sdk import AntigravityDocsHook, sync_session, sync_on_exit

# Re-export core modules for programmatic usage
import sys
from pathlib import Path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from sync_docs import sync_docs_session
from config_loader import ConfigLoader
from artifact_manager import ArtifactManager
from log_formatter import LogFormatter

__version__ = "1.0.3"
__all__ = [
    "AntigravityDocsHook",
    "sync_session",
    "sync_on_exit",
    "sync_docs_session",
    "ConfigLoader",
    "ArtifactManager",
    "LogFormatter",
]
