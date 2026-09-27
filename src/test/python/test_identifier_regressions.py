import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src/main/resources/pyscripts/identifierObfuscate.py"
PYTHON = Path(sys.executable)
JAVAC = shutil.which("javac")
JAVA = shutil.which("java")


class IdentifierRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for required in (SCRIPT, PYTHON, JAVAC, JAVA):
            if not required or not Path(required).is_file():
                raise AssertionError(f"required test dependency is absent: {required}")

    def obfuscate_compile_run(self, sources, main_class):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "src"
            original_classes = Path(temp_dir) / "original-classes"
            obfuscated_classes = Path(temp_dir) / "obfuscated-classes"
            source_root.mkdir()

            for relative_path, source in sources.items():
                path = source_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            original_java = sorted(map(str, source_root.rglob("*.java")))
            original = subprocess.run(
                [str(JAVAC), "-d", str(original_classes), *original_java],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            self.assertEqual(0, original.returncode, original.stdout)
            original_ran = subprocess.run(
                [str(JAVA), "-cp", str(original_classes), main_class],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            self.assertEqual(0, original_ran.returncode, original_ran.stdout)

            env = dict(os.environ)
            obfuscate = subprocess.run(
                [str(PYTHON), str(SCRIPT), str(source_root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
                env=env,
            )
            self.assertEqual(0, obfuscate.returncode, obfuscate.stdout)

            obfuscated_java = sorted(map(str, source_root.rglob("*.java")))
            compiled = subprocess.run(
                [str(JAVAC), "-d", str(obfuscated_classes), *obfuscated_java],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            self.assertEqual(0, compiled.returncode, compiled.stdout)

            ran = subprocess.run(
                [str(JAVA), "-cp", str(obfuscated_classes), main_class],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
            )
            self.assertEqual(0, ran.returncode, ran.stdout)
            self.assertEqual(original_ran.stdout, ran.stdout)
            obfuscated_sources = {
                path.relative_to(source_root).as_posix(): path.read_text(encoding="utf-8")
                for path in source_root.rglob("*.java")
            }
            return ran.stdout, obfuscated_sources

    def test_external_member_calls_survive_internal_name_collisions(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Collisions.java": """package sample;
class Collisions {
    enum Ext { VALUE }
    String filter(String filter) { return filter; }
    long count(long count) { return count; }
    void setFileHidingEnabled(boolean hidden) {}
}
""",
                "sample/Main.java": """package sample;
import java.util.stream.Stream;
import javax.swing.JFileChooser;
public class Main {
    private static void configure(JFileChooser chooser) {
        chooser.setFileHidingEnabled(false);
    }
    public static void main(String[] args) {
        long value = Stream.of("a", "bb").filter(s -> s.length() > 1).count();
        Collisions collisions = new Collisions();
        collisions.setFileHidingEnabled(false);
        System.out.print(collisions.filter("ok") + ":" + collisions.count(value)
                + ":" + Collisions.Ext.VALUE.name());
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("ok:1:VALUE", output)
        combined = "\n".join(sources.values())
        self.assertNotIn("class Collisions", combined)
        # Resolvable internal methods still rename; ambiguous selectors retain their declarations.
        self.assertNotIn("void setFileHidingEnabled(", combined)
        self.assertIn(".filter(", combined)
        self.assertIn(".count()", combined)
        self.assertIn(".setFileHidingEnabled(false)", combined)

    def test_enhanced_for_and_chained_project_methods_keep_working(self):
        output, _ = self.obfuscate_compile_run(
            {
                "sample/SelectionOption.java": """package sample;
enum SelectionOption {
    ONE;
    String label() { return "one"; }
    int amount() { return 1; }
    static SelectionOption select() { return ONE; }
}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) {
        for (SelectionOption option : SelectionOption.values()) {
            System.out.print(option.label() + ":" + SelectionOption.select().amount());
        }
    }
}
""",
            },
            "sample.Main",
        )
        self.assertEqual("one:1", output)

    def test_same_receiver_name_with_conflicting_types_stays_consistent(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) {
        Helper target = new Helper();
        System.out.print(target.work());
    }
}
class Helper {
    String work() { return "scope-ok"; }
}
class Other {
    String normalize(String target) { return target.trim(); }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("scope-ok", output)
        combined = "\n".join(sources.values())
        self.assertIn("String work()", combined)
        self.assertIn(".work()", combined)

    def test_qualified_project_types_use_conservative_preservation(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Helper.java": """package sample;
public class Helper {
    public String work() { return "qualified-ok"; }
}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) {
        sample.Helper helper = new sample.Helper();
        System.out.print(helper.work());
    }
}
""",
            },
            "sample.Main",
        )
        self.assertEqual("qualified-ok", output)
        combined = "\n".join(sources.values())
        self.assertIn("class Helper", combined)
        self.assertIn("String work()", combined)

    def test_qualified_static_receiver_keeps_class_and_member_names(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Helper.java": """package sample;
public class Helper {
    public static final Helper INSTANCE = new Helper();
    public String work() { return "static-qualified-ok"; }
}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) {
        System.out.print(sample.Helper.INSTANCE.work());
    }
}
""",
            },
            "sample.Main",
        )
        self.assertEqual("static-qualified-ok", output)
        combined = "\n".join(sources.values())
        self.assertIn("class Helper", combined)
        self.assertIn("String work()", combined)

    def test_catch_receiver_keeps_project_method_mapping_consistent(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
class Problem extends Exception {
    String detail() { return "catch-ok"; }
}
public class Main {
    private static void fail() throws Problem { throw new Problem(); }
    public static void main(String[] args) {
        try {
            fail();
        } catch (Problem caught) {
            System.out.print(caught.detail());
        }
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("catch-ok", output)
        combined = "\n".join(sources.values())
        self.assertIn("String detail()", combined)
        self.assertIn(".detail()", combined)

    def test_inherited_project_members_keep_mapping_consistent(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
class Base {
    String value = "field-ok";
    String message() { return "method-ok"; }
}
class Child extends Base {}
public class Main {
    public static void main(String[] args) {
        Child child = new Child();
        System.out.print(child.message() + ":" + child.value);
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("method-ok:field-ok", output)
        combined = "\n".join(sources.values())
        self.assertIn("String message()", combined)
        self.assertIn("String value =", combined)
        self.assertIn(".message()", combined)
        self.assertIn(".value", combined)

    def test_resource_and_lambda_receivers_use_general_preservation_rule(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
import java.util.stream.Stream;
class Resource implements AutoCloseable {
    String detail() { return "resource-ok"; }
    @Override public void close() {}
}
class Item {
    String label() { return "lambda-ok"; }
}
public class Main {
    public static void main(String[] args) throws Exception {
        try (Resource resource = new Resource()) {
            String label = Stream.of(new Item()).map(item -> item.label()).findFirst().get();
            System.out.print(resource.detail() + ":" + label);
        }
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("resource-ok:lambda-ok", output)
        combined = "\n".join(sources.values())
        self.assertIn("String detail()", combined)
        self.assertIn("String label()", combined)
        self.assertIn(".detail()", combined)
        self.assertIn(".label()", combined)

    def test_class_for_name_literal_tracks_obfuscated_class(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Helper.java": """package sample;
public class Helper {
    public String toString() { return "reflection-ok"; }
}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) throws Exception {
        Object helper = Class.forName("sample.Helper").getDeclaredConstructor().newInstance();
        System.out.print(helper.toString());
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("reflection-ok", output)
        self.assertNotIn('Class.forName("sample.Helper")', "\n".join(sources.values()))

    def test_uncertain_inherited_class_receiver_preserves_class_identity(self):
        # R.java is excluded from obfuscation, modeling an external receiver.
        for shadowed in (True, False):
            with self.subTest(shadowed=shadowed):
                field = "protected static final R Class = new R();" if shadowed else ""
                call = 'Class.forName("sample.Helper")'
                if not shadowed:
                    call += ".getDeclaredConstructor().newInstance()"
                output, sources = self.obfuscate_compile_run(
                    {
                        "external/R.java": '''package external;
public class R {
    public String forName(String value) { return value; }
}
''',
                        "sample/Main.java": f'''package sample;
import external.R;
class Helper {{
    public String toString() {{ return "reflection-ok"; }}
}}
class Independent {{}}
class Base {{ {field} }}
public class Main extends Base {{
    public static void main(String[] args) throws Exception {{
        new Independent();
        System.out.print({call});
    }}
}}
''',
                    },
                    "sample.Main",
                )
                self.assertEqual("sample.Helper" if shadowed else "reflection-ok", output)
                combined = "\n".join(sources.values())
                self.assertIn("class Helper", combined)
                self.assertIn('"sample.Helper"', combined)
                self.assertNotIn("class Independent", combined)

    def test_unrelated_method_parameter_named_class_keeps_reflection_working(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
import java.util.function.IntConsumer;
class Keeper implements IntConsumer {
    @Override public void accept(int Class) { if (Class == 7) System.out.print(""); }
}
class Helper {
    public String toString() { return "reflection-ok"; }
}
public class Main {
    public static void main(String[] args) throws Exception {
        new Keeper().accept(7);
        Object value = Class.forName("sample.Helper").getDeclaredConstructor().newInstance();
        System.out.print(value);
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("reflection-ok", output)
        combined = "\n".join(sources.values())
        self.assertNotIn('Class.forName("sample.Helper")', combined)
        self.assertNotIn("class Helper", combined)

    def test_unrelated_for_name_receiver_preserves_data_string(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
class Helper {
    public String toString() { return "reflection-ok"; }
}
class MyClass {
    static String forName(String value) { return value; }
}
public class Main {
    public static void main(String[] args) throws Exception {
        String data = MyClass.forName("sample.Helper");
        String text = "Class.forName(\\\"sample.Helper\\\")";
        // Class.forName("sample.Helper") must remain comment data.
        Object helper = java.lang.Class.forName("sample.Helper")
                .getDeclaredConstructor().newInstance();
        System.out.print(data + ":" + text + ":" + helper);
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual(
            'sample.Helper:Class.forName("sample.Helper"):reflection-ok',
            output,
        )
        combined = "\n".join(sources.values())
        self.assertEqual(2, combined.count('"sample.Helper"'))
        self.assertIn('// Class.forName("sample.Helper") must remain comment data.', combined)
        self.assertNotIn('java.lang.Class.forName("sample.Helper")', combined)
        self.assertNotIn("class Helper", combined)

    def test_shadowed_class_for_name_receiver_preserves_data_string(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
class Helper {}
class Class {
    static String forName(String value) { return value; }
}
public class Main {
    public static void main(String[] args) {
        System.out.print(Class.forName("sample.Helper"));
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("sample.Helper", output)
        combined = "\n".join(sources.values())
        self.assertIn('"sample.Helper"', combined)
        self.assertNotIn("class Helper", combined)
        self.assertNotIn("class Class", combined)

    def test_class_reference_inside_annotation_argument_is_obfuscated(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Use.java": """package sample;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.RUNTIME)
@interface Use { Class<?> value(); }
""",
                "sample/Helper.java": """package sample;
public class Helper {
    public String toString() { return "annotation-ok"; }
}
""",
                "sample/Worker.java": """package sample;
@Use(Helper.class)
class Worker {}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) throws Exception {
        Use use = Worker.class.getAnnotation(Use.class);
        Object helper = use.value().getDeclaredConstructor().newInstance();
        System.out.print(helper.toString());
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("annotation-ok", output)
        annotation_source = next(source for source in sources.values() if "@Use(" in source)
        self.assertIn("@Use(", annotation_source)
        self.assertNotIn("Helper.class", annotation_source)

    def test_annotation_string_that_looks_like_class_literal_stays_data(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.RUNTIME)
@interface Use { String value(); }
class Helper {}
@Use("Helper.class")
class Worker {}
public class Main {
    public static void main(String[] args) {
        System.out.print(Worker.class.getAnnotation(Use.class).value());
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("Helper.class", output)
        combined = "\n".join(sources.values())
        self.assertIn('@Use("Helper.class")', combined)
        self.assertNotIn("class Helper", combined)

    def test_multiline_annotation_rewrites_only_real_class_literal(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.RUNTIME)
@interface Use {
    String value();
    Class<?> type();
}
class Helper {
    public String toString() { return "literal-ok"; }
}
@Use(
    value = "escaped \\\"Helper.class\\\"",
    type = Helper.class // Helper.class must remain comment data.
)
class Worker {}
public class Main {
    public static void main(String[] args) throws Exception {
        Use use = Worker.class.getAnnotation(Use.class);
        Object helper = use.type().getDeclaredConstructor().newInstance();
        System.out.print(use.value() + ":" + helper);
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual('escaped "Helper.class":literal-ok', output)
        annotation_source = next(source for source in sources.values() if "@Use(" in source)
        self.assertIn('value = "escaped \\\"Helper.class\\\""', annotation_source)
        self.assertIn("// Helper.class must remain comment data.", annotation_source)
        self.assertNotIn("type = Helper.class", annotation_source)
        self.assertNotIn("class Helper", annotation_source)

    def test_external_annotation_class_literal_survives_simple_name_collision(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Date.java": """package sample;
public class Date {}
""",
                "sample/Use.java": """package sample;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.RUNTIME)
@interface Use { Class<?> value(); }
""",
                "sample/Worker.java": """package sample;
@Use(java.util.Date.class)
class Worker {}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) {
        Use use = Worker.class.getAnnotation(Use.class);
        System.out.print(use.value().getName());
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("java.util.Date", output)
        combined = "\n".join(sources.values())
        self.assertIn("@Use(java.util.Date.class)", combined)
        self.assertNotIn("class Date", combined)

    def test_external_class_for_name_survives_simple_name_collision(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Date.java": """package sample;
public class Date {}
""",
                "sample/Main.java": """package sample;
public class Main {
    public static void main(String[] args) throws Exception {
        System.out.print(Class.forName("java.util.Date").getName());
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("java.util.Date", output)
        combined = "\n".join(sources.values())
        self.assertIn('Class.forName("java.util.Date")', combined)
        self.assertNotIn("class Date", combined)

    def test_nested_class_constructor_tracks_renamed_type(self):
        output, sources = self.obfuscate_compile_run(
            {
                "sample/Main.java": """package sample;
class Outer {
    static class Inner {
        int value = 7;
        int get() { return value; }
    }
}
public class Main {
    public static void main(String[] args) {
        Outer.Inner inner = new Outer.Inner();
        System.out.print(inner.get() + ":" + inner.value);
    }
}
""",
            },
            "sample.Main",
        )

        self.assertEqual("7:7", output)
        combined = "\n".join(sources.values())
        self.assertNotIn("class Inner", combined)
        self.assertNotIn(".Inner", combined)


if __name__ == "__main__":
    unittest.main()
