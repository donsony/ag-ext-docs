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


class TestInstaller(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.local_ws = Path(self.temp_dir) / "test_project"
        self.local_ws.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_install_local_workspace(self):
        script_path = PROJECT_ROOT / "install.py"
        res = subprocess.run(
            [sys.executable, str(script_path), "install", "--local", str(self.local_ws)],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")
        plugin_dir = self.local_ws / ".agents" / "plugins" / "ag-docs-sync"
        self.assertTrue(plugin_dir.exists())
        self.assertTrue((plugin_dir / "plugin.json").exists())
        self.assertTrue((plugin_dir / "hooks.json").exists())
        self.assertTrue((plugin_dir / "skills" / "ag-docs-sync" / "SKILL.md").exists())
        self.assertTrue((plugin_dir / "ag_docs_sync" / "sdk.py").exists())

    def test_installer_status_command(self):
        script_path = PROJECT_ROOT / "install.py"
        res = subprocess.run(
            [sys.executable, str(script_path), "status"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Antigravity Multi-Runtime Ecosystem Detection", res.stdout)
        self.assertIn("Antigravity IDE", res.stdout)
        self.assertIn("Antigravity 2.0", res.stdout)
        self.assertIn("Antigravity CLI", res.stdout)
        self.assertIn("Antigravity Python SDK", res.stdout)


if __name__ == "__main__":
    unittest.main()
