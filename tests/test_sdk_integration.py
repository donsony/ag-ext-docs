import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ag_docs_sync import AntigravityDocsHook, sync_session, sync_on_exit, sync_docs_session


class TestSdkIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "sdk_workspace"
        self.workspace.mkdir(parents=True)

        self.artifacts = Path(self.temp_dir) / "sdk_artifacts"
        self.artifacts.mkdir(parents=True)
        (self.artifacts / "implementation_plan.md").write_text("# SDK Generated Plan\nSpec details.", encoding="utf-8")

        self.transcript = Path(self.temp_dir) / "transcript.jsonl"
        with open(self.transcript, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "step_index": 0,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "created_at": "2026-08-16T14:00:00Z",
                "content": "<USER_REQUEST>Run SDK Pipeline</USER_REQUEST>"
            }) + "\n")
            f.write(json.dumps({
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-08-16T14:00:02Z",
                "content": "Pipeline finished."
            }) + "\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sync_session_helper(self):
        res = sync_session(
            workspace_path=str(self.workspace),
            conversation_id="sdk-test-01",
            transcript_path=str(self.transcript),
            artifact_dir=str(self.artifacts)
        )
        self.assertTrue(res["success"])
        docs_dir = self.workspace / ".docs"
        self.assertTrue(docs_dir.exists())
        self.assertTrue((docs_dir / "plans" / "implementation_plan.md").exists())
        self.assertTrue((docs_dir / "INDEX.md").exists())

    def test_antigravity_docs_hook_object(self):
        hook = AntigravityDocsHook(workspace_path=str(self.workspace))
        hook.set_session_info(
            conversation_id="sdk-test-hook-02",
            transcript_path=str(self.transcript),
            artifact_dir=str(self.artifacts)
        )
        res = hook.sync()
        self.assertTrue(res["success"])
        self.assertEqual(res["conversation_id"], "sdk-test-hook-02")
        self.assertEqual(res["archived_artifacts_count"], 1)

    def test_antigravity_docs_hook_context_manager(self):
        with AntigravityDocsHook(workspace_path=str(self.workspace)) as hook:
            hook.set_session_info(
                conversation_id="sdk-test-ctx-03",
                transcript_path=str(self.transcript),
                artifact_dir=str(self.artifacts)
            )

        docs_dir = self.workspace / ".docs"
        self.assertTrue(docs_dir.exists())
        self.assertTrue((docs_dir / "logs" / "LATEST_SESSION.md").exists())

    def test_sync_on_exit_context_manager(self):
        with sync_on_exit(workspace_path=str(self.workspace), conversation_id="sdk-exit-04") as hook:
            hook.transcript_path = str(self.transcript)
            hook.artifact_dir = str(self.artifacts)

        docs_dir = self.workspace / ".docs"
        self.assertTrue(docs_dir.exists())
        self.assertTrue((docs_dir / "INDEX.md").exists())


if __name__ == "__main__":
    unittest.main()
