import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "test_workspace"
        self.workspace.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_config_loading(self):
        loader = ConfigLoader(workspace_path=str(self.workspace))
        self.assertTrue(loader.config.get("enabled"))
        self.assertEqual(loader.config.get("docs_root"), ".docs")

    def test_local_docs_ignore(self):
        ignore_file = self.workspace / ".docs-ignore"
        ignore_file.write_text("ignore", encoding="utf-8")

        loader = ConfigLoader(workspace_path=str(self.workspace))
        excluded, reason = loader.is_project_excluded(str(self.workspace))
        self.assertTrue(excluded)
        self.assertIn("ignore marker", reason)

    def test_local_config_disabled(self):
        ws_config = self.workspace / ".docs-sync.json"
        ws_config.write_text('{"enabled": false}', encoding="utf-8")

        loader = ConfigLoader(workspace_path=str(self.workspace))
        excluded, reason = loader.is_project_excluded(str(self.workspace))
        self.assertTrue(excluded)
        self.assertIn("explicitly disabled", reason)

    def test_exclude_projects_matching(self):
        loader = ConfigLoader(workspace_path=str(self.workspace))
        loader.config["exclude_projects"] = [str(self.workspace)]

        excluded, reason = loader.is_project_excluded(str(self.workspace))
        self.assertTrue(excluded)
        self.assertIn("Matched excluded project", reason)


if __name__ == "__main__":
    unittest.main()
