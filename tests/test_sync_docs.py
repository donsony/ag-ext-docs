import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.sync_docs import sync_docs_session, get_known_brain_roots, find_latest_conversation


class TestSyncDocsEndToEnd(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "ws"
        self.workspace.mkdir(parents=True)

        self.artifacts = Path(self.temp_dir) / "artifacts"
        self.artifacts.mkdir(parents=True)
        (self.artifacts / "implementation_plan.md").write_text("# Feature Spec\nPlan details.", encoding="utf-8")
        (self.artifacts / "walkthrough.md").write_text("# Release Walkthrough\nAll tests verified.", encoding="utf-8")

        self.transcript = Path(self.temp_dir) / "transcript.jsonl"
        with open(self.transcript, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "step_index": 0,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "created_at": "2026-08-16T12:00:00Z",
                "content": "<USER_REQUEST>Build integration</USER_REQUEST>"
            }) + "\n")
            f.write(json.dumps({
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-08-16T12:00:05Z",
                "content": "<thought>Finished work</thought>Done."
            }) + "\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sync_cli_execution(self):
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "sync_docs.py"
        
        proc = subprocess.run([
            sys.executable,
            str(script_path),
            "--workspace", str(self.workspace),
            "--conversation-id", "test-conv-001",
            "--transcript", str(self.transcript),
            "--artifacts", str(self.artifacts)
        ], capture_output=True, text=True, stdin=subprocess.DEVNULL)

        self.assertEqual(proc.returncode, 0, f"Error output: {proc.stderr}")
        docs_dir = self.workspace / ".docs"
        self.assertTrue(docs_dir.exists())
        self.assertTrue((docs_dir / "plans" / "implementation_plan.md").exists())
        self.assertTrue((docs_dir / "walkthroughs" / "walkthrough.md").exists())
        self.assertTrue((docs_dir / "logs" / "LATEST_SESSION.md").exists())
        self.assertTrue((docs_dir / "logs" / "TIMELINE.md").exists())
        self.assertTrue((docs_dir / "INDEX.md").exists())

    def test_sync_hook_stdin_execution(self):
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "sync_docs.py"
        hook_payload = {
            "conversationId": "hook-conv-999",
            "workspacePaths": [str(self.workspace)],
            "transcriptPath": str(self.transcript),
            "artifactDirectoryPath": str(self.artifacts)
        }

        proc = subprocess.run(
            [sys.executable, str(script_path), "--hook"],
            input=json.dumps(hook_payload),
            capture_output=True,
            text=True
        )

        self.assertEqual(proc.returncode, 0, f"Error output: {proc.stderr}")
        self.assertEqual(json.loads(proc.stdout.strip()), {})
        docs_dir = self.workspace / ".docs"
        self.assertTrue(docs_dir.exists())

    def test_sync_docs_session_programmatic_api(self):
        res = sync_docs_session(
            workspace_path=str(self.workspace),
            conversation_id="sdk-conv-123",
            transcript_path=str(self.transcript),
            artifact_dir=str(self.artifacts)
        )
        self.assertTrue(res["success"])
        self.assertFalse(res["skipped"])
        self.assertEqual(res["conversation_id"], "sdk-conv-123")
        self.assertEqual(res["archived_artifacts_count"], 2)
        self.assertTrue(res["transcript_synced"])
        self.assertTrue(res["index_updated"])

    def test_multi_runtime_brain_discovery_with_env(self):
        # Create a mock Antigravity 2.0 / CLI brain directory
        mock_brain = Path(self.temp_dir) / "mock_gemini" / "antigravity" / "brain"
        conv_folder = mock_brain / "mock-conv-2026"
        conv_logs = conv_folder / ".system_generated" / "logs"
        conv_logs.mkdir(parents=True)
        shutil.copy2(self.transcript, conv_logs / "transcript.jsonl")
        shutil.copy2(self.artifacts / "implementation_plan.md", conv_folder / "implementation_plan.md")

        old_env = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
        try:
            os.environ["ANTIGRAVITY_BRAIN_DIR"] = str(mock_brain)
            roots = get_known_brain_roots()
            self.assertTrue(any(str(mock_brain).lower() in str(r).lower() for r in roots))

            latest = find_latest_conversation([mock_brain])
            self.assertIsNotNone(latest)
            self.assertEqual(latest[0], "mock-conv-2026")

            # Perform sync using auto-discovery
            res = sync_docs_session(
                workspace_path=str(self.workspace),
                conversation_id="mock-conv-2026"
            )
            self.assertTrue(res["success"])
            self.assertTrue(res["transcript_synced"])
        finally:
            if old_env:
                os.environ["ANTIGRAVITY_BRAIN_DIR"] = old_env
            else:
                os.environ.pop("ANTIGRAVITY_BRAIN_DIR", None)


if __name__ == "__main__":
    unittest.main()
