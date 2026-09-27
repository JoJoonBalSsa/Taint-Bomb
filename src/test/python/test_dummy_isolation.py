import contextlib
import io
import json
import os
from pathlib import Path
import re

import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
JDK = Path(os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk"))
JAVAC = JDK / "bin/javac"
JAVA = JDK / "bin/java"

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
import dumbDB  # noqa: E402
import dummyInsert  # noqa: E402
from dumbDB import DumbDB  # noqa: E402
from dummyInsert import InsertDummyCode  # noqa: E402
from levelObfuscate import LevelObfuscation  # noqa: E402


class DummyIsolationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        for required in (JAVAC, JAVA):
            if not required.is_file():
                raise AssertionError(f"required JDK17 tool is absent: {required}")
        cls.env = {
            **os.environ,
            "JAVA_HOME": str(JDK),
            "PATH": str(JDK / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    @contextlib.contextmanager
    def _workdir(self):
        evidence = os.environ.get("DUMMY_EVIDENCE_DIR")
        if evidence:
            root = Path(evidence)
            root.mkdir(parents=True)
            yield root
        else:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as temp_dir:
                yield Path(temp_dir)

    def _compile_run(self, root, label, sources):
        source_root = root / label / "src"
        classes = root / label / "classes"
        source_root.mkdir(parents=True)
        classes.mkdir(parents=True)
        for name, source in sources.items():
            (source_root / name).write_text(source, encoding="utf-8")

        compile_result = subprocess.run(
            [str(JAVAC), "-d", str(classes), *map(str, sorted(source_root.glob("*.java")))],
            text=True,
            capture_output=True,
            env=self.env,
            timeout=60,
        )
        (root / label / "compile.stdout").write_text(compile_result.stdout, encoding="utf-8")
        (root / label / "compile.stderr").write_text(compile_result.stderr, encoding="utf-8")
        self.assertEqual(0, compile_result.returncode, compile_result.stdout + compile_result.stderr)

        run_result = subprocess.run(
            [str(JAVA), "-cp", str(classes), "Runner"],
            text=True,
            capture_output=True,
            env=self.env,
            timeout=60,
        )
        (root / label / "run.stdout").write_text(run_result.stdout, encoding="utf-8")
        (root / label / "run.stderr").write_text(run_result.stderr, encoding="utf-8")
        self.assertEqual(0, run_result.returncode, run_result.stdout + run_result.stderr)
        return {
            "compile": {
                "exit": compile_result.returncode,
                "stdout": compile_result.stdout,
                "stderr": compile_result.stderr,
            },
            "run": {
                "exit": run_result.returncode,
                "stdout": run_result.stdout,
                "stderr": run_result.stderr,
            },
        }

    @staticmethod
    def _method(index):
        return f"""    public String unusedFunction{index}() {{
        int collider = 0;
        try {{
            if (fail) {{
                trace.append("T");
                throw new IllegalStateException("boom");
            }}
            synchronized (this) {{
                collider++;
                trace.append("R");
                return trace.toString() + ":" + collider;
            }}
        }} finally {{
            side++;
            trace.append("F");
        }}
    }}"""

    @staticmethod
    def _class_source(index, method):
        return f"""public class Case{index} {{
    private boolean fail;
    private int side;
    private final StringBuilder trace = new StringBuilder();

{method}

    public void failNext() {{ fail = true; trace.setLength(0); }}
    public int side() {{ return side; }}
    public String trace() {{ return trace.toString(); }}
}}
"""

    @staticmethod
    def _runner(count):
        calls = []
        for index in range(count):
            calls.append(f"""        Case{index} c{index} = new Case{index}();
        System.out.println("{index}:return=" + c{index}.unusedFunction{index}()
                + "|trace=" + c{index}.trace() + "|side=" + c{index}.side());
        c{index}.failNext();
        try {{
            c{index}.unusedFunction{index}();
        }} catch (IllegalStateException expected) {{
            System.out.println("{index}:throw=" + expected.getMessage()
                    + "|trace=" + c{index}.trace() + "|side=" + c{index}.side());
        }}""")
        return "public class Runner {\n    public static void main(String[] args) {\n" + "\n".join(calls) + "\n    }\n}\n"

    def test_disabled_dummy_wrapper_preserves_source(self):
        source = "public String value() { return \"ok\"; }"
        self.assertEqual(
            source,
            LevelObfuscation._safe(source, lambda: LevelObfuscation._dummy(source, None)),
        )

    def test_database_selector_visits_every_real_template_once_then_exhausts(self):
        database = DumbDB()
        count = len(database.dummy_list)
        with mock.patch.object(dumbDB.secrets, "randbelow", side_effect=range(count)):
            selected = [database.get_unique_random_number() for _ in range(count)]
        self.assertEqual(list(range(count)), selected)
        self.assertIsNone(database.get_unique_random_number())

    def test_every_real_template_changes_code_and_preserves_return_throw_and_side_effects(self):
        database = DumbDB()
        count = len(database.dummy_list)
        self.assertGreater(count, 0)
        baseline = {"Runner.java": self._runner(count)}
        candidate = {"Runner.java": self._runner(count)}

        transformed_methods = []
        choices = list("collider") * count
        with mock.patch.object(dummyInsert.secrets, "choice", side_effect=choices), \
                mock.patch.object(dummyInsert.secrets, "randbelow", return_value=7), \
                contextlib.redirect_stdout(io.StringIO()):
            for index, template in enumerate(database.dummy_list):
                with self.subTest(template=index):
                    method = self._method(index)
                    transformed = InsertDummyCode(method, template, index).get_obfuscated_code()
                    self.assertIsNotNone(transformed)
                    self.assertNotEqual(method, transformed)
                    for line in template.splitlines():
                        stripped = line.strip()
                        if stripped and f"unusedFunction{index}" not in stripped:
                            self.assertIn(stripped, transformed)
                    transformed_methods.append(transformed)
                    baseline[f"Case{index}.java"] = self._class_source(index, method)
                    candidate[f"Case{index}.java"] = self._class_source(index, transformed)

        with self._workdir() as root:
            original = self._compile_run(root, "original", baseline)
            changed = self._compile_run(root, "candidate", candidate)
            self.assertEqual(original["run"], changed["run"])
            for index, transformed in enumerate(transformed_methods):
                with self.subTest(template_name=index):
                    self.assertRegex(transformed, rf"\bunusedFunction{index}_+\b")
                    self.assertRegex(transformed, r"\bint collider_+\s*=")
            (root / "summary.json").write_text(
                json.dumps({"template_count": count, "original": original, "candidate": changed},
                           indent=2),
                encoding="utf-8",
            )


if __name__ == "__main__":
    unittest.main()
