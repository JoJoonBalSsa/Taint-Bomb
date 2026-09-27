import contextlib
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
TMPDIR = Path(tempfile.gettempdir())

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
import controlFlowFlatten as control_flow_module  # noqa: E402
from controlFlowFlatten import ControlFlowFlatten  # noqa: E402


class ControlFlowIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for required in (Path(sys.executable), JAVAC, JAVA):
            if not required.is_file():
                raise AssertionError(f"required test dependency is absent: {required}")
        cls.env = {
            **os.environ,
            "JAVA_HOME": str(JDK),
            "PATH": str(JDK / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONPATH": str(PYSCRIPTS),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(TMPDIR),
        }

    @contextlib.contextmanager
    def _case_root(self, name):
        evidence_dir = os.environ.get("TAINT_BOMB_EVIDENCE_DIR")
        if evidence_dir:
            root = Path(evidence_dir) / name
            root.mkdir(parents=True)
            yield root
            return
        with tempfile.TemporaryDirectory(dir=TMPDIR) as temp_dir:
            yield Path(temp_dir)

    def _call(self, command, cwd):
        result = subprocess.run(
            [str(part) for part in command],
            cwd=cwd,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        return {
            "command": [str(part) for part in command],
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _compile_run(self, root, variant, source):
        project = root / variant
        project.mkdir()
        java_file = project / "Main.java"
        java_file.write_text(source, encoding="utf-8")
        classes = project / "classes"
        classes.mkdir()
        compiled = self._call([JAVAC, "-d", classes, java_file], project)
        ran = None
        if compiled["exit_code"] == 0:
            ran = self._call([JAVA, "-cp", classes, "Main"], project)
        return {
            "source": str(java_file),
            "compile": compiled,
            "run": ran,
        }

    def _transform(self, source, methods, enabled=True):
        if not enabled:
            return source, {}
        transformed_source = source
        transformed_methods = {}
        for name, method in methods:
            candidate = ControlFlowFlatten(method).get_obfuscated_code()
            self.assertIsNotNone(candidate, name)
            self.assertNotEqual(method, candidate, name)
            self.assertIn("switch (", candidate, name)
            self.assertIn(method, transformed_source, name)
            transformed_source = transformed_source.replace(method, candidate, 1)
            transformed_methods[name] = candidate
        return transformed_source, transformed_methods

    def _run_pair(self, name, original_source, candidate_source, expected, observations):
        with self._case_root(name) as root:
            original = self._compile_run(root, "original", original_source)
            candidate = self._compile_run(root, "candidate", candidate_source)
            evidence = {
                "name": name,
                "original": original,
                "candidate": candidate,
                "changed": original_source != candidate_source,
                "observations": observations,
            }
            (root / "result.json").write_text(
                json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            self.assertEqual(0, original["compile"]["exit_code"], original["compile"])
            self.assertIsNotNone(original["run"])
            self.assertEqual(0, original["run"]["exit_code"], original["run"])
            self.assertEqual(expected, original["run"]["stdout"])
            self.assertEqual(0, candidate["compile"]["exit_code"], candidate["compile"])
            self.assertIsNotNone(candidate["run"])
            self.assertEqual(0, candidate["run"]["exit_code"], candidate["run"])
            self.assertEqual(original["run"]["stdout"], candidate["run"]["stdout"])
            return evidence

    def test_supported_statement_matrix_matches_original_with_real_jdk17(self):
        methods = [
            ("blank_local", '''static int blankLocal() {
        int value;
        value = 7;
        return value;
    }'''),
            ("blank_finals", '''static int blankFinals() {
        final int left, right;
        left = 3;
        right = 4;
        return left * 10 + right;
    }'''),
            ("dependent_multi", '''static int dependentMulti() {
        final int token = 2;
        int dependent = token + 1, value = dependent * 2;
        return value;
    }'''),
            ("field_shadow", '''static int fieldShadow() {
        int before = fieldValue;
        int fieldValue = 2;
        return before * 10 + fieldValue;
    }'''),
            ("final_string_constant", '''static boolean finalStringConstant() {
        final String prefix = "a";
        final String suffix = prefix + "b";
        String combined = suffix + "c";
        return combined == "abc";
    }'''),
            ("final_numeric_constant", '''static boolean finalNumericConstant() {
        final int number = 7;
        return ("v" + number) == "v7";
    }'''),
            ("side_effect_order", '''static String sideEffectOrder() {
        trace = "";
        mark("A");
        final int first = markInt("B", 2);
        int second = markInt("C", first + 1), third = markInt("D", second + 1);
        return third + ":" + trace;
    }'''),
            ("multiple_statements", '''static int multipleStatements(int value) {
        value += 1;
        value *= 2;
        value -= 3;
        return value;
    }'''),
            ("exception_order", '''static void exceptionOrder() {
        trace = "";
        mark("A");
        fail();
        mark("C");
    }'''),
        ]
        source = '''public class Main {
    static int fieldValue = 7;
    static String trace = "";
    static String mark(String label) { trace += label; return label; }
    static int markInt(String label, int value) { trace += label; return value; }
    static int fail() { trace += "B"; throw new IllegalStateException("boom"); }

%s

    public static void main(String[] args) {
        System.out.println("blank_local=" + blankLocal());
        System.out.println("blank_finals=" + blankFinals());
        System.out.println("dependent_multi=" + dependentMulti());
        System.out.println("field_shadow=" + fieldShadow());
        System.out.println("final_string_constant=" + finalStringConstant());
        System.out.println("final_numeric_constant=" + finalNumericConstant());
        System.out.println("side_effect_order=" + sideEffectOrder());
        System.out.println("multiple_statements=" + multipleStatements(3));
        try {
            exceptionOrder();
            System.out.println("exception_order=no-error:" + trace);
        } catch (IllegalStateException error) {
            System.out.println("exception_order=" + trace + ":" + error.getMessage());
        }
    }
}
''' % "\n\n".join(method for _, method in methods)
        expected = (
            "blank_local=7\n"
            "blank_finals=34\n"
            "dependent_multi=6\n"
            "field_shadow=72\n"
            "final_string_constant=true\n"
            "final_numeric_constant=true\n"
            "side_effect_order=4:ABCD\n"
            "multiple_statements=5\n"
            "exception_order=AB:boom\n"
        )

        candidate, transformed = self._transform(source, methods)
        self.assertEqual(len(methods), candidate.count("switch ("))
        self.assertGreaterEqual(transformed["multiple_statements"].count("case "), 4)
        self._run_pair(
            "supported_matrix",
            source,
            candidate,
            expected,
            {
                "enabled_feature": "ControlFlowFlatten",
                "other_transforms": [],
                "dispatcher_count": candidate.count("switch ("),
                "case_names": [name for name, _ in methods],
            },
        )

    def test_dispatcher_name_avoids_parameters_with_same_generated_prefix(self):
        method = '''static int collision(int _s0, int _s1) {
        _s0 += _s1;
        return _s0;
    }'''
        source = '''public class Main {
    %s
    public static void main(String[] args) { System.out.print(collision(2, 3)); }
}
''' % method
        state_values = iter((0, 1, 2))
        name_values = iter((0, 1, 3))

        def deterministic_randbelow(limit):
            return next(state_values if limit == 9000 else name_values)

        with mock.patch.object(
            control_flow_module.secrets, "randbelow", side_effect=deterministic_randbelow
        ):
            candidate, transformed = self._transform(source, [("dispatcher_collision", method)])

        dispatcher = re.search(r"int (_s\d+) = \d+;", transformed["dispatcher_collision"])
        self.assertIsNotNone(dispatcher)
        self._run_pair(
            "dispatcher_collision",
            source,
            candidate,
            "5",
            {
                "enabled_feature": "ControlFlowFlatten",
                "other_transforms": [],
                "dispatcher": dispatcher.group(1),
            },
        )
        self.assertNotIn(dispatcher.group(1), {"_s0", "_s1"})

    def test_disabled_control_preserves_source_exactly(self):
        method = '''static int disabled(int value) {
        value += 2;
        return value;
    }'''
        source = '''public class Main {
    %s
    public static void main(String[] args) { System.out.print(disabled(3)); }
}
''' % method
        candidate, transformed = self._transform(source, [("disabled", method)], enabled=False)
        self.assertEqual({}, transformed)
        self.assertEqual(source, candidate)
        evidence = self._run_pair(
            "disabled_control",
            source,
            candidate,
            "5",
            {
                "enabled_feature": None,
                "disabled": ["ControlFlowFlatten", "all other transforms"],
                "dispatcher_count": candidate.count("switch ("),
            },
        )
        self.assertFalse(evidence["changed"])
        self.assertNotIn("switch (", candidate)


if __name__ == "__main__":
    unittest.main()
