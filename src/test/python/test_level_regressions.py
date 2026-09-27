import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
MANAGER = ROOT / "src/main/kotlin/io/JoJoonBalSsa/TaintBomb/services/ManageObfuscate.kt"
PYTHON = Path(sys.executable)
JAVAC = shutil.which("javac") or "javac"
JAVA = shutil.which("java") or "java"

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
from stringSplit import StringArraySplit  # noqa: E402


class LevelRegressionTests(unittest.TestCase):
    def _transform_and_run(self, source, class_name):
        transformed = StringArraySplit(source).get_obfuscated_code()
        self.assertIsNotNone(transformed)
        with tempfile.TemporaryDirectory() as temp_dir:
            java_file = Path(temp_dir) / f"{class_name}.java"
            java_file.write_text(transformed, encoding="utf-8")
            compile_result = subprocess.run(
                [JAVAC, java_file], text=True, capture_output=True
            )
            self.assertEqual(0, compile_result.returncode, compile_result.stdout + compile_result.stderr)
            return subprocess.run(
                [JAVA, "-cp", temp_dir, class_name],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

    def _run_level(self, string_obf=None):
        method = 'public String token() { return "secret"; }'
        source = f"public class Sample {{ {method} }}\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            java_file = temp / "Sample.java"
            java_file.write_text(source, encoding="utf-8")
            (temp / "analysis_result.json").write_text(
                json.dumps([
                    {
                        "sensitivity": 2,
                        "tainted": [{"file_path": str(java_file), "source_code": method}],
                    }
                ]),
                encoding="utf-8",
            )
            command = [
                PYTHON,
                PYSCRIPTS / "levelObfuscate.py",
                temp,
                "False",
                "False",
                "False",
            ]
            if string_obf is not None:
                command.append(str(string_obf))
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                env={**os.environ, "PYTHONPATH": str(PYSCRIPTS), "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            return java_file.read_text(encoding="utf-8")

    def test_level_runs_before_identifier_in_actual_orchestrator(self):
        source = MANAGER.read_text(encoding="utf-8")
        body = source.split("private fun executePythonScript()", 1)[1].split(
            "private fun executeOptionalScript", 1
        )[0]
        self.assertLess(
            body.index("runLevelObfuscate(currentFraction)"),
            body.index('scriptName = "identifierObfuscate"'),
        )

    def test_string_setting_is_forwarded_and_controls_level_split(self):
        source = MANAGER.read_text(encoding="utf-8")
        run_level = source.split("private fun runLevelObfuscate", 1)[1].split(
            "private fun runPythonScript", 1
        )[0]
        self.assertIn("settings.enableStringEncryption.toString()", run_level)
        self.assertIn("new String(new char[]", self._run_level())
        self.assertNotIn("new String(new char[]", self._run_level("False"))

    def test_individual_literals_keep_interned_identity(self):
        source = '''
public class Identity {
    public static void main(String[] args) {
        System.out.println("admin" == "admin");
    }
}
'''
        self.assertEqual("true", self._transform_and_run(source, "Identity"))

    def test_literal_concatenation_keeps_compile_time_identity(self):
        source = '''
public class Concatenation {
    public static void main(String[] args) {
        System.out.println(("ad" + "min") == "admin");
    }
}
'''
        self.assertEqual("true", self._transform_and_run(source, "Concatenation"))

    def test_final_string_constant_remains_valid_switch_label(self):
        source = '''
public class ConstantSwitch {
    static String classify(String value) {
        final String x = "a";
        switch (value) {
            case x: return "yes";
            default: return "no";
        }
    }
    public static void main(String[] args) {
        System.out.println(classify("a"));
    }
}
'''
        self.assertEqual("yes", self._transform_and_run(source, "ConstantSwitch"))


if __name__ == "__main__":
    unittest.main()
