import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
