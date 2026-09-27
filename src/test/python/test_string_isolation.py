import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
JAVA_RESOURCES = ROOT / "src/main/resources/java"
PYTHON = Path(sys.executable)
JDK = Path(os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk"))
JAVAC = JDK / "bin/javac"
JAVA = JDK / "bin/java"

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
from stringObfuscate import StringObfuscate  # noqa: E402


class StringIsolationTests(unittest.TestCase):
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

    def _compile_run(self, root, main_class):
        classes = root / "classes"
        if classes.exists():
            shutil.rmtree(classes)
        classes.mkdir()
        compile_result = subprocess.run(
            [str(JAVAC), "-encoding", "UTF-8", "-d", str(classes),
             *sorted(str(path) for path in root.rglob("*.java"))],
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=60,
            env=self.env,
        )
        run_result = None
        if compile_result.returncode == 0:
            run_result = subprocess.run(
                [str(JAVA), "-cp", str(classes), main_class],
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=60,
                env=self.env,
            )
        return compile_result, run_result

    @staticmethod
    def _write_sources(root, sources):
        for relative, source in sources.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")

    def _aes_case(self, sources, main_class):
        temp = tempfile.TemporaryDirectory(dir=self.env["TMPDIR"])
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        original = root / "original"
        candidate = root / "candidate"
        self._write_sources(original, sources)
        self._write_sources(candidate, sources)

        original_compile, original_run = self._compile_run(original, main_class)
        self.assertEqual(0, original_compile.returncode, original_compile.stderr)
        self.assertEqual(0, original_run.returncode, original_run.stderr)

        StringObfuscate(
            str(candidate),
            (JAVA_RESOURCES / "keyDecryptLin.java").read_text(encoding="utf-8"),
            (JAVA_RESOURCES / "stringDecryptLin.java").read_text(encoding="utf-8"),
            False,
        )
        transformed = {
            str(path.relative_to(candidate)): path.read_text(encoding="utf-8")
            for path in sorted(candidate.rglob("*.java"))
        }
        candidate_compile, candidate_run = self._compile_run(candidate, main_class)
        self.assertEqual(0, candidate_compile.returncode, candidate_compile.stderr)
        self.assertEqual(0, candidate_run.returncode, candidate_run.stderr)
        self.assertEqual(original_run.stdout, candidate_run.stdout)
        return transformed

    def test_aes_preserves_escaped_literals_and_encodes_utf8(self):
        sources = {
            "sample/Main.java": r'''package sample;
public class Main {
    public static void main(String[] args) throws Exception {
        String escaped = "line1\nline2|tab=\t|quote=\"|slash=\\|literal=\\n";
        String utf8 = "한글-é-😀";
        String reflected = (String) Class.forName("sample.Helper")
                .getMethod("value").invoke(null);
        System.out.print(escaped + "|" + utf8 + "|" + reflected);
    }
}
''',
            "sample/Helper.java": '''package sample;
public class Helper {
    public static String value() { return "reflection-ok"; }
}
''',
        }
        transformed = self._aes_case(sources, "sample.Main")
        combined = "\n".join(transformed.values())
        # Keep the existing escaped/path-literal exclusion policy.
        escaped_line = next(line.strip() for line in sources["sample/Main.java"].splitlines()
                            if "String escaped =" in line)
        self.assertIn(escaped_line, combined)
        for plaintext in (
            '"한글-é-😀"',
            '"reflection-ok"',
        ):
            self.assertNotIn(plaintext, combined)
        self.assertIn("Class.forName(STRING_LITERALS", transformed["sample/Main.java"])
        self.assertIn("STRING_LITERALS", combined)
        self.assertIn("stringDecrypt", combined)
        self.assertIn("keyDecrypt", combined)


if __name__ == "__main__":
    unittest.main()
