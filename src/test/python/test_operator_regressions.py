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
JAVAC = Path(shutil.which("javac") or "javac")
JAVA = Path(shutil.which("java") or "java")

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
from operationObfuscate import ObfuscateOperations  # noqa: E402


class OperatorRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for required in (PYTHON, JAVAC, JAVA):
            if not required.is_file():
                raise AssertionError(f"required test dependency is absent: {required}")

    def _run(self, argv, cwd):
        result = subprocess.run(
            [str(arg) for arg in argv],
            cwd=cwd,
            env={
                **os.environ,
                "JAVA_HOME": "/usr/lib/jvm/java-17-openjdk",
                "PATH": f"/usr/lib/jvm/java-17-openjdk/bin:{os.environ.get('PATH', '')}",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        self.assertEqual(0, result.returncode, result.stdout)
        return result.stdout

    def _compile_run(self, root, main_class):
        classes = root / "classes"
        sources = sorted(root.rglob("*.java"))
        self._run([JAVAC, "-d", classes, *sources], root)
        return self._run([JAVA, "-cp", classes, main_class], root)

    def _transform_and_compare(self, method, main, helpers=""):
        transformed = ObfuscateOperations({
            "file_path": "Program.java",
            "method_name": "probe",
            "tree_position": {},
            "source_code": method,
        }).return_obfuscated_code()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outputs = []
            for name, candidate in (("baseline", method), ("candidate", transformed)):
                folder = root / name
                folder.mkdir()
                (folder / "Program.java").write_text(
                    "public class Program {\n"
                    + helpers + "\n" + candidate
                    + "\npublic static void main(String[] args) {" + main + "}\n}",
                    encoding="utf-8",
                )
                outputs.append(self._compile_run(folder, "Program"))
        self.assertEqual(outputs[0], outputs[1])
        return transformed

    def test_integral_arithmetic_and_relational_categories_are_obfuscated(self):
        main = """int[] v={Integer.MIN_VALUE,-3,-1,0,1,3,Integer.MAX_VALUE};
for(int a:v)for(int b:v){try{System.out.print(probe(a,b)+\";\");}
catch(RuntimeException e){System.out.print(e.getClass().getSimpleName()+\";\");}}"""
        for operator in ("+", "-", "*", "/", "%"):
            with self.subTest(operator=operator):
                method = (
                    f"static int probe(int a,int b) {{ "
                    f"if (((a {operator} b) & 7) == 5) return 1; return 0; }}"
                )
                transformed = self._transform_and_compare(method, main)
                self.assertNotEqual(method, transformed)

        for operator in ("<", "<=", ">", ">="):
            with self.subTest(operator=operator):
                method = (
                    f"static int probe(int a,int b) {{ "
                    f"if (a {operator} b) return 1; return 0; }}"
                )
                transformed = self._transform_and_compare(method, main)
                self.assertNotEqual(method, transformed)

    def test_integral_bitwise_and_shift_categories_are_obfuscated(self):
        main = """int[] v={Integer.MIN_VALUE,-3,-1,0,1,3,31,Integer.MAX_VALUE};
for(int a:v)for(int b:v)System.out.print(probe(a,b)+\";\");"""
        for operator in ("&", "|", "^", "<<", ">>", ">>>"):
            with self.subTest(operator=operator):
                method = (
                    f"static int probe(int a,int b) {{ "
                    f"if (((a {operator} b) & 7) == 5) return 1; return 0; }}"
                )
                transformed = self._transform_and_compare(method, main)
                self.assertNotEqual(method, transformed)

    def test_boolean_short_circuit_eager_and_unary_categories_are_obfuscated(self):
        boolean_main = """for(boolean a:new boolean[]{false,true})
for(boolean b:new boolean[]{false,true}){trace="";System.out.print(probe(a,b)+";");}"""
        helpers = (
            'static String trace=""; '
            'static boolean mark(String label,boolean value){trace+=label;return value;}'
        )
        for operator in ("&&", "||"):
            with self.subTest(operator=operator):
                method = (
                    "static String probe(boolean a,boolean b) { "
                    f"if (mark(\"L\",a) {operator} mark(\"R\",b)) "
                    "return trace+\"T\"; return trace+\"F\"; }"
                )
                transformed = self._transform_and_compare(method, boolean_main, helpers)
                self.assertNotEqual(method, transformed)

        for operator in ("&", "|", "^"):
            with self.subTest(operator=operator):
                effectful = (
                    "static String probe(boolean a,boolean b) { "
                    f"if (mark(\"L\",a) {operator} mark(\"R\",b)) "
                    "return trace+\"T\"; return trace+\"F\"; }"
                )
                self.assertEqual(
                    effectful,
                    self._transform_and_compare(effectful, boolean_main, helpers),
                )
                simple = (
                    "static int probe(boolean a,boolean b) { "
                    f"if (a {operator} b) return 1; return 0; }}"
                )
                simple_main = (
                    "for(boolean a:new boolean[]{false,true})"
                    "for(boolean b:new boolean[]{false,true})"
                    "System.out.print(probe(a,b)+\";\");"
                )
                transformed = self._transform_and_compare(simple, simple_main)
                self.assertNotEqual(simple, transformed)

        not_method = "static int probe(boolean a,int unused) { if (!a) return 1; return 0; }"
        not_main = (
            "for(boolean a:new boolean[]{false,true})"
            "System.out.print(probe(a,0)+\";\");"
        )
        transformed = self._transform_and_compare(not_method, not_main)
        self.assertNotEqual(not_method, transformed)
        self.assertNotIn("if (!a)", transformed)

        complement_method = (
            "static int probe(int a,int unused) { "
            "if ((~a & 7) == 5) return 1; return 0; }"
        )
        complement_main = (
            "for(int a:new int[]{Integer.MIN_VALUE,-1,0,1,Integer.MAX_VALUE})"
            "System.out.print(probe(a,0)+\";\");"
        )
        transformed = self._transform_and_compare(complement_method, complement_main)
        self.assertNotEqual(complement_method, transformed)
        self.assertNotIn("~a", transformed)

    def test_equality_reference_null_instanceof_and_floating_edges(self):
        integer_main = (
            "for(int a:new int[]{Integer.MIN_VALUE,-1,0,1,Integer.MAX_VALUE})"
            "for(int b:new int[]{-1,0,1})System.out.print(probe(a,b)+\";\");"
        )
        for operator in ("==", "!="):
            with self.subTest(operator=operator):
                method = (
                    "static int probe(int a,int b) { "
                    f"if (a {operator} b) return 1; return 0; }}"
                )
                transformed = self._transform_and_compare(method, integer_main)
                self.assertNotEqual(method, transformed)

        reference_method = (
            "static int probe(Object a,Object b) { "
            "if (a != null && b == null) return 1; "
            "if (a == b) return 2; return 3; }"
        )
        reference_main = (
            "Object x=new Guard();"
            "System.out.print(probe(x,null)+\":\"+probe(x,x)+\":\"+probe(null,x));"
        )
        helpers = (
            "static class Guard { public int hashCode(){"
            "throw new AssertionError(\"unexpected hashCode\");} }"
        )
        transformed = self._transform_and_compare(reference_method, reference_main, helpers)
        self.assertNotEqual(reference_method, transformed)
        self.assertNotIn("hashCode", transformed)

        instance_method = (
            "static int probe(Object a,int unused) { "
            "if (a instanceof String) return 1; return 0; }"
        )
        instance_main = (
            "System.out.print(probe(\"x\",0)+\":\"+probe(new Object(),0)+\":\"+probe(null,0));"
        )
        transformed = self._transform_and_compare(instance_method, instance_main)
        self.assertNotEqual(instance_method, transformed)

        floating_equality = (
            "static int probe(double a,double b) { "
            "if (a == b || a != b) return 1; return 0; }"
        )
        floating_main = (
            "double[] v={Double.NaN,Double.NEGATIVE_INFINITY,-0.0,0.0,1.5,"
            "Double.POSITIVE_INFINITY};for(double a:v)for(double b:v)"
            "System.out.print(probe(a,b)+\";\");"
        )
        transformed = self._transform_and_compare(floating_equality, floating_main)
        self.assertNotEqual(floating_equality, transformed)

        for expression in ("a * b > 5.0", "a / b <= -0.0", "a + b < a - b"):
            with self.subTest(retained=expression):
                method = (
                    "static int probe(double a,double b) { "
                    f"if ({expression}) return 1; return 0; }}"
                )
                self.assertEqual(
                    method,
                    self._transform_and_compare(method, floating_main),
                )

    def test_long_overflow_and_shift_distance_preserve_runtime(self):
        method = (
            "static int probe(long a,long b) { "
            "if ((a + b) * (a - b) > 5L || (a >>> b) != (a >> b) "
            "|| a / b < a % b) return 1; return 0; }"
        )
        main = (
            "long[] v={Long.MIN_VALUE,-3,-1,0,1,3,64,Long.MAX_VALUE};"
            "for(long a:v)for(long b:v){try{System.out.print(probe(a,b)+\";\");}"
            "catch(RuntimeException e){System.out.print(e.getClass().getSimpleName()+\";\");}}"
        )
        transformed = self._transform_and_compare(method, main)
        self.assertNotEqual(method, transformed)

    def test_mixed_int_long_arithmetic_promotes_before_rewrite(self):
        orders = (
            (
                "long", "int",
                "long[] av={Long.MIN_VALUE,-1L,0L,1L,Long.MAX_VALUE};"
                "int[] bv={Integer.MIN_VALUE,-1,0,1,Integer.MAX_VALUE};",
            ),
            (
                "int", "long",
                "int[] av={Integer.MIN_VALUE,-1,0,1,Integer.MAX_VALUE};"
                "long[] bv={Long.MIN_VALUE,-1L,0L,1L,Long.MAX_VALUE};",
            ),
        )
        for operator in ("+", "-", "*", "/", "%"):
            for left_type, right_type, values in orders:
                with self.subTest(operator=operator, order=f"{left_type}-{right_type}"):
                    method = (
                        f"static int probe({left_type} a,{right_type} b) {{ "
                        f"if (a {operator} b < 0L) return 1; return 0; }}"
                    )
                    main = (
                        values
                        + "for(" + left_type + " a:av)for(" + right_type + " b:bv){"
                        "try{System.out.print(probe(a,b)+\";\");}"
                        "catch(RuntimeException e){System.out.print(e.getClass().getSimpleName()+\";\");}}"
                    )
                    transformed = self._transform_and_compare(method, main)
                    self.assertNotEqual(method, transformed)

    def test_out_of_scope_local_type_is_not_reused(self):
        method = (
            "static boolean probe(int a) { { int b=1; } "
            "if (a > b) return true; return false; }"
        )
        self.assertEqual(
            method,
            self._transform_and_compare(
                method,
                "System.out.print(probe(2));",
                "static double b=Double.NaN;",
            ),
        )

    def test_nested_and_anonymous_fields_do_not_borrow_parameter_types(self):
        cases = (
            (
                "static String probe(int a) { "
                "class Inner { double a=Double.NaN; boolean run() { "
                "if (a > 0) return true; return false; } } "
                "if (a + 1 > 1) return new Inner().run()+\":outer\"; return \"skip\"; }",
                "",
            ),
            (
                "static String probe(int a) { Runner r=new Runner() { "
                "double a=Double.NaN; public boolean run() { "
                "if (a > 0) return true; return false; } }; "
                "if (a + 1 > 1) return r.run()+\":outer\"; return \"skip\"; }",
                "interface Runner { boolean run(); }",
            ),
        )
        for method, helpers in cases:
            with self.subTest(method=method):
                self.assertEqual(
                    method,
                    self._transform_and_compare(
                        method,
                        "System.out.print(probe(1));",
                        helpers,
                    ),
                )

    def test_nested_condition_range_does_not_corrupt_outer_rewrite(self):
        method = """static boolean probe(){
    if(new Object(){boolean test(){if(1==1)return true;return false;}}.test() && true)
        return true;
    return false;
}"""
        transformed = self._transform_and_compare(
            method,
            "System.out.print(probe());",
        )
        self.assertNotEqual(method, transformed)
        self.assertIn("if(1==1)", transformed)

    def test_unsupported_type_effect_and_lvalue_cases_are_retained(self):
        cases = [
            (
                "static int probe(double a,double b) { "
                "if (a * b > 5.0) return 1; return 0; }",
                "System.out.print(probe(Double.NaN,-0.0));",
                "",
            ),
            (
                "static int probe(int unused,int ignored) { "
                "if ((x[at()] *= value()) > 5) return x[0]+i*100+n*1000; return -1; }",
                "System.out.print(probe(0,0));",
                "static int[] x={2,3};static int i,n;"
                "static int at(){i++;return 0;}static int value(){n++;return 4;}",
            ),
            (
                "static int probe(int a,int b) { "
                "if ((a < b ? a+b : a-b) > 5) return 1; return 0; }",
                "System.out.print(probe(2,3)+\":\"+probe(3,2));",
                "",
            ),
            (
                "static int probe(int a,int b) { "
                "if (a /* retain operator comment */ > b) return 1; return 0; }",
                "System.out.print(probe(2,1));",
                "",
            ),
        ]
        for method, main, helpers in cases:
            with self.subTest(method=method):
                self.assertEqual(
                    method,
                    self._transform_and_compare(method, main, helpers),
                )

        literal_method = (
            "static String probe(int a,int b) { "
            "if (a > b) return \"a > b\"; return \"a <= b\"; }"
        )
        literal_main = "System.out.print(probe(2,1)+\":\"+probe(1,2));"
        transformed = self._transform_and_compare(literal_method, literal_main)
        self.assertNotEqual(literal_method, transformed)
        self.assertIn('return "a > b"', transformed)
        self.assertIn('return "a <= b"', transformed)

    def test_level_then_identifier_preserves_multiplication_comparison(self):
        source = """package sample;
public class Main {
    public static int calc(int a, int b) {
        if (a * b > 5) return 1;
        return 0;
    }
    public static void main(String[] args) {
        System.out.print(calc(2, 3) + ":" + calc(1, 2));
    }
}
"""
        method = """public static int calc(int a, int b) {
        if (a * b > 5) return 1;
        return 0;
    }"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            java_file = project / "sample/Main.java"
            java_file.parent.mkdir(parents=True)
            java_file.write_text(source, encoding="utf-8")
            (project / "analysis_result.json").write_text(
                json.dumps([
                    {
                        "sensitivity": 2,
                        "tainted": [{
                            "file_path": str(java_file),
                            "method_name": "calc",
                            "tree_position": {},
                            "source_code": method,
                        }],
                    }
                ]),
                encoding="utf-8",
            )

            self._run(
                [PYTHON, PYSCRIPTS / "levelObfuscate.py", project,
                 "True", "False", "False", "False"],
                project,
            )
            level_source = java_file.read_text(encoding="utf-8")
            self.assertNotIn("a * b > 5", level_source)
            self.assertIn("-((-(a)) * (b))", level_source)
            self._run([PYTHON, PYSCRIPTS / "identifierObfuscate.py", project], project)

            self.assertEqual("1:0", self._compile_run(project, "sample.Main"))


if __name__ == "__main__":
    unittest.main()
