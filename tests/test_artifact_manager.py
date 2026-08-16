import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from scripts.artifact_manager import ArtifactManager


class TestArtifactManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "workspace"
        self.workspace.mkdir(parents=True)
        self.artifact_dir = Path(self.temp_dir) / "artifacts"
        self.artifact_dir.mkdir(parents=True)

        self.manager = ArtifactManager(str(self.workspace))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_determine_category(self):
        plan_file = Path("implementation_plan.md")
        self.assertEqual(self.manager.determine_category(plan_file, "implementation_plan.md"), "plans")

        walkthrough_file = Path("walkthrough.md")
        self.assertEqual(self.manager.determine_category(walkthrough_file, "walkthrough.md"), "walkthroughs")

        research_file = Path("research_notes.md")
        self.assertEqual(self.manager.determine_category(research_file, "research_notes.md"), "research")

        diagram_file = Path("arch.mermaid")
        self.assertEqual(self.manager.determine_category(diagram_file, "arch.mermaid"), "diagrams")

    def test_sync_artifacts_and_index(self):
        # Create dummy artifacts
        plan_file = self.artifact_dir / "implementation_plan.md"
        plan_file.write_text("# Master Plan\nDetails here.", encoding="utf-8")

        walk_file = self.artifact_dir / "walkthrough.md"
        walk_file.write_text("# Walkthrough Summary\nChanges verified.", encoding="utf-8")

        fixed_time = datetime(2026, 8, 16, 17, 30, 0)
        items = self.manager.sync_artifacts(str(self.artifact_dir), "conv-xyz", timestamp=fixed_time)

        self.assertEqual(len(items), 2)
        plans_dir = self.workspace / ".docs" / "plans"
        self.assertTrue((plans_dir / "implementation_plan_2026-08-16_173000.md").exists())
        self.assertTrue((plans_dir / "implementation_plan.md").exists())

        # Generate index
        index_file = self.manager.update_index_file()
        self.assertTrue(index_file.exists())
        index_content = index_file.read_text(encoding="utf-8")
        self.assertIn("Project Documentation Catalog", index_content)
        self.assertIn("Master Plan", index_content)


if __name__ == "__main__":
    unittest.main()
