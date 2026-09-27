"""Smoke-harness CLI requirements, separate from plugin runtime support."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

HARNESS = Path(__file__).with_name("run_target_smoke.py")


class SmokeHarnessCLITests(unittest.TestCase):
    def test_help_on_supported_python(self):
        result = subprocess.run([sys.executable, "-B", str(HARNESS), "--help"],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--run-root", result.stdout)

    def test_python39_reports_requirement_before_evaluating_annotations(self):
        python39 = os.environ.get("TAINT_BOMB_PYTHON39") or shutil.which("python3.9")
        if not python39:
            self.skipTest("set TAINT_BOMB_PYTHON39 to exercise the old-runtime diagnostic")
        version = subprocess.check_output([python39, "-c", "import sys; print(sys.version_info[:2])"],
                                          text=True, timeout=20).strip()
        self.assertEqual("(3, 9)", version)
        result = subprocess.run([python39, "-B", str(HARNESS), "--help"],
                                capture_output=True, text=True, timeout=20)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("requires Python 3.10 or later", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
