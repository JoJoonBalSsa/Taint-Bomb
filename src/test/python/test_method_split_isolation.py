import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
JDK = Path(os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk"))
JAVAC = JDK / "bin/javac"
JAVA = JDK / "bin/java"
EVIDENCE_DIR = os.environ.get("METHOD_SPLIT_EVIDENCE_DIR")

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
from methodSplit import MethodSplit  # noqa: E402


class MethodSplitIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for required in (JAVAC, JAVA):
            if not required.is_file():
                raise AssertionError(f"required test dependency is absent: {required}")
        cls.env = {
            **os.environ,
            "JAVA_HOME": str(JDK),
            "PATH": str(JDK / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": tempfile.gettempdir(),
        }

    def _compile_run(self, source, root):
        java_file = root / "Program.java"
        classes = root / "classes"
        root.mkdir(parents=True)
        java_file.write_text(source, encoding="utf-8")
        compiled = subprocess.run(
            [str(JAVAC), "-d", str(classes), str(java_file)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            env=self.env,
        )
        ran = None
        if compiled.returncode == 0:
            ran = subprocess.run(
                [str(JAVA), "-cp", str(classes), "Program"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
                env=self.env,
            )
        return compiled, ran

    def _assert_case(self, name, imports, members, method, main, expected):
        transformed = MethodSplit(method).get_new_method()
        self.assertIsNotNone(transformed)
        self.assertNotEqual(method, transformed)

        helper_names = re.findall(
            r"\npublic (?:static )?[^\n{]+ ([a-z][a-z0-9]{7})\([^)]*\) \{",
            transformed,
        )
        self.assertTrue(helper_names, transformed)
        for helper_name in helper_names:
            self.assertGreaterEqual(transformed.count(helper_name + "("), 2, transformed)

        sources = {
            "original": imports + "\npublic class Program {\n" + members + method + main + "\n}\n",
            "candidate": imports + "\npublic class Program {\n" + members + transformed + main + "\n}\n",
        }
        results = {}
        if EVIDENCE_DIR:
            case_root = Path(EVIDENCE_DIR) / name
            case_root.mkdir(parents=True, exist_ok=True)
        else:
            case_root = None

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            for variant, source in sources.items():
                run_root = temp / variant
                compiled, ran = self._compile_run(source, run_root)
                results[variant] = {
                    "compile_exit": compiled.returncode,
                    "compile_stdout": compiled.stdout,
                    "compile_stderr": compiled.stderr,
                    "run_exit": None if ran is None else ran.returncode,
                    "run_stdout": "" if ran is None else ran.stdout,
                    "run_stderr": "" if ran is None else ran.stderr,
                }
                if case_root:
                    (case_root / f"{variant}.java").write_text(source, encoding="utf-8")

        if case_root:
            (case_root / "transformation.txt").write_text(transformed, encoding="utf-8")
            (case_root / "results.json").write_text(
                json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        for variant in ("original", "candidate"):
            result = results[variant]
            self.assertEqual(
                0,
                result["compile_exit"],
                result["compile_stdout"] + result["compile_stderr"],
            )
            self.assertEqual(0, result["run_exit"], result["run_stdout"] + result["run_stderr"])
            self.assertEqual(expected, result["run_stdout"])
        self.assertEqual(results["original"]["run_stdout"], results["candidate"]["run_stdout"])
        return transformed

    def test_parameter_modifiers_generic_and_array_types(self):
        method = """public static int probe(final java.util.Map<String, Integer> values, final int[] offsets) {
        int result = values.get("x") + offsets[0];
        return result;
    }
"""
        transformed = self._assert_case(
            "parameter-types",
            "",
            "",
            method,
            """    public static void main(String[] args) {
        java.util.Map<String, Integer> values = new java.util.HashMap<>();
        values.put("x", 7);
        System.out.print(probe(values, new int[]{2}));
    }
""",
            "9",
        )
        self.assertIn("final java.util.Map<String, Integer> values", transformed)
        self.assertIn("final int[] offsets", transformed)

    def test_instance_field_and_later_local_keep_distinct_bindings(self):
        method = """public int probe(int seed) {
        int before = value;
        int value = seed + 1;
        int result = before * 100 + value;
        return result;
    }
"""
        self._assert_case(
            "instance-field-local-binding",
            "",
            "    int value = 5;\n",
            method,
            """    public static void main(String[] args) {
        System.out.print(new Program().probe(6));
    }
""",
            "507",
        )

    def test_static_field_and_later_local_keep_distinct_bindings(self):
        method = """public static int probe(int seed) {
        int before = value;
        int value = seed + 2;
        int result = before * 100 + value;
        return result;
    }
"""
        transformed = self._assert_case(
            "static-field-local-binding",
            "",
            "    static int value = 4;\n",
            method,
            """    public static void main(String[] args) {
        System.out.print(probe(6));
    }
""",
            "408",
        )
        self.assertRegex(transformed, r"\npublic static [^\n]+ [a-z][a-z0-9]{7}\(")

    def test_local_mutation_order_is_preserved(self):
        method = """public static String probe() {
        int seed = 3;
        int i = 0;
        int value = i++ * 10 + i++;
        return seed + ":" + value + ":" + i;
    }
"""
        transformed = self._assert_case(
            "local-mutation-order",
            "",
            "",
            method,
            """    public static void main(String[] args) {
        System.out.print(probe());
    }
""",
            "3:1:2",
        )
        self.assertIn("int value = i++ * 10 + i++;", transformed)


if __name__ == "__main__":
    unittest.main()
