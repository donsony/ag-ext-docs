import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.log_formatter import LogFormatter


class TestLogFormatter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.transcript_file = Path(self.temp_dir) / "transcript.jsonl"
        self.formatter = LogFormatter()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_thought_and_content(self):
        raw = "<thought>Thinking about the architecture</thought>Here is the answer."
        thought, content = self.formatter.extract_thought_and_content(raw)
        self.assertEqual(thought, "Thinking about the architecture")
        self.assertEqual(content, "Here is the answer.")

    def test_extract_user_request(self):
        raw = "<USER_REQUEST>\nImplement feature XYZ\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\ntime\n</ADDITIONAL_METADATA>"
        user_req = self.formatter.extract_user_request_text(raw)
        self.assertEqual(user_req, "Implement feature XYZ")

    def test_generate_session_markdown(self):
        # Create a mock transcript
        events = [
            {
                "step_index": 0,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "status": "DONE",
                "created_at": "2026-08-16T12:00:00Z",
                "content": "<USER_REQUEST>\nBuild testing system\n</USER_REQUEST>"
            },
            {
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-08-16T12:00:05Z",
                "content": "<thought>I will execute command</thought>Plan approved.",
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {
                            "CommandLine": "pytest",
                            "toolSummary": "Run test suite"
                        }
                    }
                ]
            },
            {
                "step_index": 2,
                "source": "MODEL",
                "type": "RUN_COMMAND",
                "status": "DONE",
                "created_at": "2026-08-16T12:00:10Z",
                "content": "5 passed in 0.12s"
            }
        ]

        with open(self.transcript_file, "w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

        md_output, meta = self.formatter.generate_session_markdown(
            transcript_path=str(self.transcript_file),
            conversation_id="conv-12345",
            workspace_path="/test/workspace"
        )

        self.assertIn("Build & Conversation Session Log", md_output)
        self.assertIn("Build testing system", md_output)
        self.assertIn("I will execute command", md_output)
        self.assertIn("run_command", md_output)
        self.assertIn("5 passed in 0.12s", md_output)
        self.assertEqual(meta["prompt_count"], 1)
        self.assertEqual(meta["tool_count"], 1)


if __name__ == "__main__":
    unittest.main()
