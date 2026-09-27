import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
PYTHON = Path(sys.executable)
JDK = Path("/usr/lib/jvm/java-17-openjdk")
JAVAC = JDK / "bin/javac"
JAVA = JDK / "bin/java"

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
from controlFlowFlatten import ControlFlowFlatten  # noqa: E402
from stringSplit import StringArraySplit  # noqa: E402


class ConstantSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for required in (PYTHON, JAVAC, JAVA):
            if not required.is_file():
                raise AssertionError(f"required test dependency is absent: {required}")
        cls.env = {
            **os.environ,
            "JAVA_HOME": str(JDK),
            "PATH": str(JDK / "bin") + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONPATH": str(PYSCRIPTS),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": tempfile.gettempdir(),
        }

    def _compile_run(self, root, main_class):
        classes = root / "classes"
        classes.mkdir()
        java_files = sorted(str(path) for path in root.rglob("*.java"))
        compiled = subprocess.run(
            [str(JAVAC), "-d", str(classes), *java_files],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
            env=self.env,
        )
        self.assertEqual(0, compiled.returncode, compiled.stdout)
        ran = subprocess.run(
            [str(JAVA), "-cp", str(classes), main_class],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
            env=self.env,
        )
        self.assertEqual(0, ran.returncode, ran.stdout)
        return ran.stdout

    def _pipeline(self, source, method, sensitivity, level_args, expected):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            java_file = root / "sample/Main.java"
            java_file.parent.mkdir(parents=True)
            java_file.write_text(source, encoding="utf-8")

            self.assertEqual(expected, self._compile_run(root, "sample.Main"))
            shutil.rmtree(root / "classes")

            (root / "analysis_result.json").write_text(
                json.dumps([
                    {
                        "sensitivity": sensitivity,
                        "tainted": [{
                            "file_path": str(java_file),
                            "method_name": "sample.Main.run",
                            "tree_position": {},
                            "cut_tree": {},
                            "source_code": method,
                        }],
                    }
                ]),
                encoding="utf-8",
            )
            for command in (
                [PYTHON, PYSCRIPTS / "levelObfuscate.py", root, *level_args],
                [PYTHON, PYSCRIPTS / "identifierObfuscate.py", root],
            ):
                result = subprocess.run(
                    [str(part) for part in command],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=60,
                    env=self.env,
                )
                self.assertEqual(0, result.returncode, result.stdout)

            transformed = java_file.read_text(encoding="utf-8")
            self.assertNotEqual(source, transformed)
            self.assertEqual(expected, self._compile_run(root, "sample.Main"))
            return transformed

    def _direct_transform_run(self, source, method, expected):
        transformed_method = ControlFlowFlatten(method).get_obfuscated_code()
        self.assertIsNotNone(transformed_method)
        self.assertNotEqual(method, transformed_method)
        self.assertIn("switch (", transformed_method)
        transformed_source = source.replace(method, transformed_method)
        self.assertNotEqual(source, transformed_source)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            java_file = root / "Main.java"
            java_file.write_text(transformed_source, encoding="utf-8")
            self.assertEqual(expected, self._compile_run(root, "Main"))
        return transformed_method

    def test_constant_concat_survives_level_then_identifier_pipeline(self):
        source = '''package sample;
public class Main {
    public static void run() {
        if (("a" + 1 + "b") == "a1b") {
            System.out.print("same");
        } else {
            System.out.print("different");
        }
    }
    public static void main(String[] args) { run(); }
}
'''
        method = '''public static void run() {
        if (("a" + 1 + "b") == "a1b") {
            System.out.print("same");
        } else {
            System.out.print("different");
        }
    }'''
        direct = StringArraySplit(method).get_obfuscated_code()
        self.assertIsNotNone(direct)
        self.assertNotEqual(method, direct)
        self.assertIn('"" + (char)', direct)
        transformed = self._pipeline(
            source, method, 2, ["False", "False", "False", "True"], "same"
        )
        self.assertIn("new String(new char[]", transformed)
        self.assertIn('"" + (char)', transformed)

    def test_unknown_concat_operands_preserve_constant_and_dynamic_identity(self):
        cases = (
            ("enclosing_final_field", "static final int NUMBER = 7;", "NUMBER", "v7", "true"),
            ("qualified_final_field", "static final int NUMBER = 7;", "Main.NUMBER", "v7", "true"),
            ("external_constant_field", "", "Integer.SIZE", "v32", "true"),
            ("dynamic_field", "static int NUMBER = 7;", "NUMBER", "v7", "false"),
        )
        for name, field, operand, target, expected in cases:
            with self.subTest(name=name):
                method = f'''public static boolean run() {{
        return ("v" + {operand}) == "{target}";
    }}'''
                source = f'''package sample;
public class Main {{
    {field}
    {method}
    public static void main(String[] args) {{ System.out.print(run()); }}
}}
'''
                direct = StringArraySplit(method).get_obfuscated_code()
                self.assertIsNotNone(direct)
                self.assertIn('"" + (char)', direct)
                self.assertNotIn('"v"', direct)
                self.assertNotIn(f'"{target}"', direct)
                transformed = self._pipeline(
                    source, method, 2, ["False", "False", "False", "True"], expected
                )
                self.assertIn('"" + (char)', transformed)
                self.assertNotIn('"v"', transformed)
                self.assertNotIn(f'"{target}"', transformed)

    def test_final_string_constant_survives_flatten_then_identifier_pipeline(self):
        source = '''package sample;
public class Main {
    public static boolean run() {
        final String prefix = "a";
        String combined = prefix + "b";
        return combined == "ab";
    }
    public static void main(String[] args) { System.out.print(run()); }
}
'''
        method = '''public static boolean run() {
        final String prefix = "a";
        String combined = prefix + "b";
        return combined == "ab";
    }'''
        direct = ControlFlowFlatten(method).get_obfuscated_code()
        self.assertIsNotNone(direct)
        self.assertNotEqual(method, direct)
        self.assertIn("switch (", direct)
        self.assertIn("final String prefix", direct)
        transformed = self._pipeline(
            source, method, 3, ["False", "True", "False", "False"], "true"
        )
        self.assertIn("switch (", transformed)
        self.assertIn("final String", transformed)

    def test_blank_local_survives_flatten_then_identifier_pipeline(self):
        source = '''package sample;
public class Main {
    public static int run() {
        int value;
        value = 7;
        return value;
    }
    public static void main(String[] args) { System.out.print(run()); }
}
'''
        method = '''public static int run() {
        int value;
        value = 7;
        return value;
    }'''
        direct = ControlFlowFlatten(method).get_obfuscated_code()
        self.assertIsNotNone(direct)
        self.assertNotEqual(method, direct)
        self.assertIn("switch (", direct)
        self.assertIn("int value;", direct)
        transformed = self._pipeline(
            source, method, 3, ["False", "True", "False", "False"], "7"
        )
        self.assertIn("switch (", transformed)

    def test_required_constant_contexts_are_encoded_as_java_constants(self):
        source = '''import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.RUNTIME)
@interface Tag { String value(); }
@Tag(value = "a" + 1 + "b")
public class Main {
    static boolean run(String value) {
        final int digit = 1;
        final String prefix = "a";
        String combined = (prefix + (digit + "b"));
        switch (value) {
            case ("a" + 1 + "b"): return combined == "a1b";
            default: return false;
        }
    }
    public static void main(String[] args) {
        System.out.print(run("a1b") + ":" + Main.class.getAnnotation(Tag.class).value());
    }
}
'''
        transformed = StringArraySplit(source).get_obfuscated_code()
        self.assertIsNotNone(transformed)
        self.assertNotEqual(source, transformed)
        self.assertIn('@Tag(value = "a" + 1 + "b")', transformed)
        self.assertIn('case ("a" + 1 + "b")', transformed)
        self.assertIn('final String prefix = ("" + (char)', transformed)
        self.assertIn('digit + ("" + (char)', transformed)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Main.java").write_text(transformed, encoding="utf-8")
            self.assertEqual("true:a1b", self._compile_run(root, "Main"))

    def test_flatten_keeps_final_initializers_dependencies_and_field_binding(self):
        method = '''int run() {
        int before = value;
        final int token = mark(2);
        int dependent = token + 1;
        int value = mark(dependent);
        return before * 100 + value;
    }'''
        source = '''public class Main {
    int value = 5;
    static String trace = "";
    static int mark(int value) { trace += value; return value; }
    int run() {
        int before = value;
        final int token = mark(2);
        int dependent = token + 1;
        int value = mark(dependent);
        return before * 100 + value;
    }
    public static void main(String[] args) {
        Main main = new Main();
        System.out.print(main.run() + ":" + trace);
    }
}
'''
        transformed = self._direct_transform_run(source, method, "503:23")
        self.assertIn("final int token = mark(2);", transformed)
        self.assertLess(transformed.index("int before = value;"), transformed.index("int value = mark(dependent);"))

    def test_flatten_without_locals_still_uses_multiple_dispatch_cases(self):
        method = '''static int run(int value) {
        value = value + 1;
        value = value * 2;
        return value;
    }'''
        source = '''public class Main {
    static int run(int value) {
        value = value + 1;
        value = value * 2;
        return value;
    }
    public static void main(String[] args) { System.out.print(run(3)); }
}
'''
        transformed = self._direct_transform_run(source, method, "8")
        self.assertGreaterEqual(transformed.count("case "), 3)


if __name__ == "__main__":
    unittest.main()
