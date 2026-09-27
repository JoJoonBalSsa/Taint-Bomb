import json
import os
from pathlib import Path

import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
PYTHON = Path(sys.executable)
JDK = Path(os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk"))
JAVAC = JDK / "bin/javac"
JAVA = JDK / "bin/java"
EVIDENCE = os.environ.get("OPAQUE_EVIDENCE_DIR")

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
import opaquePredicate as opaque  # noqa: E402
from opaquePredicate import OpaquePredicate  # noqa: E402


class OpaqueIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for required in (PYTHON, JAVAC, JAVA):
            if not required.is_file():
                raise AssertionError(f"required test dependency is absent: {required}")
        cls.env = {
            **os.environ,
            "JAVA_HOME": str(JDK),
            "PATH": str(JDK / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": tempfile.gettempdir(),
        }
        cls.evidence = Path(EVIDENCE) if EVIDENCE else None
        if cls.evidence:
            (cls.evidence / "cases").mkdir(parents=True, exist_ok=True)

    def _run(self, argv, cwd):
        return subprocess.run(
            [str(part) for part in argv],
            cwd=cwd,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )

    def _compile_run(self, root, source):
        java_file = root / "Program.java"
        java_file.write_text(source, encoding="utf-8")
        classes = root / "classes"
        classes.mkdir()
        compiled = self._run([JAVAC, "-d", classes, java_file], root)
        ran = None
        if compiled.returncode == 0:
            ran = self._run([JAVA, "-cp", classes, "Program"], root)
        return compiled, ran

    @staticmethod
    def _process_result(result):
        if result is None:
            return None
        return {
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _compare(self, name, original, candidate, changed=True):
        if self.evidence:
            case_root = self.evidence / "cases" / name
            case_root.mkdir(parents=True)
            context = None
        else:
            context = tempfile.TemporaryDirectory()
            case_root = Path(context.name)

        try:
            results = {}
            for variant, source in (("original", original), ("candidate", candidate)):
                folder = case_root / variant
                folder.mkdir()
                compiled, ran = self._compile_run(folder, source)
                results[variant] = {
                    "compile": self._process_result(compiled),
                    "run": self._process_result(ran),
                }
            if self.evidence:
                (case_root / "result.json").write_text(
                    json.dumps(
                        {
                            "name": name,
                            "changed": original != candidate,
                            **results,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ) + "\n",
                    encoding="utf-8",
                )

            original_result = results["original"]
            candidate_result = results["candidate"]
            self.assertEqual(0, original_result["compile"]["exit"], original_result)
            self.assertIsNotNone(original_result["run"])
            self.assertEqual(0, original_result["run"]["exit"], original_result)
            self.assertEqual(0, candidate_result["compile"]["exit"], candidate_result)
            self.assertIsNotNone(candidate_result["run"])
            self.assertEqual(0, candidate_result["run"]["exit"], candidate_result)
            self.assertEqual(original_result["run"], candidate_result["run"])
            self.assertEqual(changed, original != candidate)
            return results
        finally:
            if context:
                context.cleanup()

    def _transform(self, method, family=0, name="opaque00", seed=2_000_000_000, count=1):
        def choose(values):
            return values[family]

        with (
            mock.patch.object(opaque, "_rand_name", return_value=name),
            mock.patch.object(opaque.secrets, "choice", side_effect=choose),
            mock.patch.object(opaque.secrets, "randbelow", return_value=seed - 1),
        ):
            transformed = OpaquePredicate(method, count=count).get_obfuscated_code()
        self.assertIsNotNone(transformed)
        self.assertNotEqual(method, transformed)
        self.assertIn(f"int {name} = {seed};", transformed)
        self.assertIn("if (", transformed)
        return transformed

    @staticmethod
    def _program(methods, main, helpers=""):
        return (
            "public class Program {\n"
            + helpers
            + "\n"
            + "\n".join(methods)
            + "\npublic static void main(String[] args) throws Exception {\n"
            + main
            + "\n}\n}\n"
        )

    def test_predicate_families_preserve_overflow_boundary_execution(self):
        original_methods = []
        candidate_methods = []
        for family in range(4):
            method = f"static int family{family}(int value) {{ return value; }}"
            original_methods.append(method)
            candidate_methods.append(
                self._transform(method, family=family, name=f"opaque0{family}")
            )
        main = (
            "int[] values={Integer.MIN_VALUE,-46341,-1,0,1,46341,Integer.MAX_VALUE};\n"
            "for(int value:values){"
            "System.out.print(family0(value)+\":\"+family1(value)+\":\""
            "+family2(value)+\":\"+family3(value)+\";\");}"
        )
        self._compare(
            "predicate_families_overflow",
            self._program(original_methods, main),
            self._program(candidate_methods, main),
        )

    def test_early_return_throw_empty_body_and_side_effect_order(self):
        methods = [
            "static int early(int value) { if (value < 0) return mark(value); return mark(value + 1); }",
            "static int throwing(int value) { if (value == 0) throw new IllegalStateException(\"zero\"); return mark(value); }",
            "static void empty() {}",
        ]
        candidates = [
            self._transform(method, family=index, name=f"body000{index}")
            for index, method in enumerate(methods)
        ]
        helpers = (
            'static String trace="";\n'
            'static int mark(int value){trace+=value+",";return value;}\n'
        )
        main = (
            "empty();System.out.print(early(-2)+\":\"+early(2)+\":\");"
            "try{throwing(0);}catch(IllegalStateException expected){System.out.print(expected.getMessage()+\":\");}"
            "System.out.print(throwing(4)+\":\"+trace);"
        )
        self._compare(
            "body_forms_side_effects",
            self._program(methods, main, helpers),
            self._program(candidates, main, helpers),
        )

    def test_body_insertion_skips_comments_and_annotation_array_braces(self):
        method = '''/* leading { comment */
// another { comment
@SuppressWarnings({"unused", "rawtypes"})
static int annotated() {
    return 9;
}'''
        transformed = self._transform(method, name="position")
        self.assertGreater(
            transformed.index("int position ="),
            transformed.index("static int annotated() {") + len("static int annotated() {"),
        )
        self._compare(
            "comment_annotation_position",
            self._program([method], "System.out.print(annotated());"),
            self._program([transformed], "System.out.print(annotated());"),
        )

    def test_constructor_invocations_remain_first_statements(self):
        constructors = [
            'Program() { this(3); Trace.log += "D"; }',
            'Program(int value) { super(Trace.mark(value)); Trace.log += "B"; }',
        ]
        candidates = [
            self._transform(constructors[0], family=1, name="ctor0000"),
            self._transform(constructors[1], family=2, name="ctor0001"),
        ]
        prefix = (
            'class Trace { static String log=""; static int mark(int value){log+="M";return value;} }\n'
            'class Base { Base(int value){Trace.log+="S"+value;} }\n'
            'public class Program extends Base {\n'
        )
        suffix = (
            '\npublic static void main(String[] args){new Program();System.out.print(Trace.log);}\n}\n'
        )
        self._compare(
            "constructor_insertion_position",
            prefix + "\n".join(constructors) + suffix,
            prefix + "\n".join(candidates) + suffix,
        )

    def test_generated_names_avoid_parameters_and_other_generated_blocks(self):
        method = "static int collision(int aaaaaaaa) { return aaaaaaaa + 1; }"
        generated = iter(("aaaaaaaa", "bbbbbbbb", "bbbbbbbb", "cccccccc"))
        with (
            mock.patch.object(opaque, "_rand_name", side_effect=lambda: next(generated)),
            mock.patch.object(opaque.secrets, "choice", side_effect=lambda values: values[3]),
            mock.patch.object(opaque.secrets, "randbelow", return_value=46_340),
        ):
            transformed = OpaquePredicate(method, count=2).get_obfuscated_code()
        self.assertIsNotNone(transformed)
        self.assertNotEqual(method, transformed)
        self.assertNotIn("int aaaaaaaa =", transformed)
        self.assertIn("int bbbbbbbb =", transformed)
        self.assertIn("int cccccccc =", transformed)
        self._compare(
            "generated_name_collisions",
            self._program([method], "System.out.print(collision(6));"),
            self._program([transformed], "System.out.print(collision(6));"),
        )

    def test_disabled_control_preserves_source(self):
        method = "static int control() { return 11; }"
        source = self._program([method], "System.out.print(control());")
        self._compare("disabled_identity_control", source, source, changed=False)


if __name__ == "__main__":
    unittest.main()
