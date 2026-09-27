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

sys.dont_write_bytecode = True
sys.path.insert(0, str(PYSCRIPTS))
from stringObfuscate import StringObfuscate  # noqa: E402


def find_android_jar():
    configured = os.environ.get("ANDROID_JAR")
    if configured:
        jar = Path(configured).expanduser()
        return jar if jar.is_file() else None

    sdk_roots = [
        os.environ.get("ANDROID_SDK_ROOT"),
        os.environ.get("ANDROID_HOME"),
        str(Path.home() / "Android/Sdk"),
    ]
    for root in filter(None, sdk_roots):
        jars = sorted((Path(root).expanduser() / "platforms").glob("*/android.jar"), reverse=True)
        if jars:
            return jars[0]
    return None


class AndroidDecryptRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.android_jar = find_android_jar()
        if cls.android_jar is None:
            raise unittest.SkipTest(
                "Android SDK android.jar not found; set ANDROID_JAR, ANDROID_SDK_ROOT, or ANDROID_HOME"
            )
        cls.javac = shutil.which("javac")
        cls.java = shutil.which("java")
        if not cls.javac or not cls.java:
            raise AssertionError("javac and java are required")
        cls.env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    def _compile(self, output, *sources, android=False):
        command = [self.javac, "-source", "8", "-target", "8", "-Xlint:-options"]
        if android:
            command += ["-bootclasspath", str(self.android_jar)]
        command += ["-d", str(output), *map(str, sources)]
        return subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=60,
            env=self.env,
        )

    def test_android_pipeline_compiles_and_decrypts_with_one_base64_api(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source/repro/Tiny.java"
            source.parent.mkdir(parents=True)
            source.write_text(
                '''package repro;
public class Tiny {
    public static void main(String[] args) {
        System.out.print("hello-android");
    }
}
''',
                encoding="utf-8",
            )

            StringObfuscate(
                str(root / "source"),
                (JAVA_RESOURCES / "keyDecryptLin.java").read_text(encoding="utf-8"),
                (JAVA_RESOURCES / "stringDecryptAndroid.java").read_text(encoding="utf-8"),
                True,
            )

            generated = source.read_text(encoding="utf-8")
            self.assertIn("import android.util.Base64;", generated)
            self.assertNotIn("import java.util.Base64;", generated)
            self.assertNotIn("Base64.getDecoder()", generated)

            sdk_classes = root / "sdk-classes"
            sdk_classes.mkdir()
            sdk_compile = self._compile(sdk_classes, source, android=True)
            self.assertEqual(0, sdk_compile.returncode, sdk_compile.stderr)

            shim = root / "runtime/android/util/Base64.java"
            shim.parent.mkdir(parents=True)
            shim.write_text(
                '''package android.util;
public final class Base64 {
    public static final int DEFAULT = 0;
    public static byte[] decode(String value, int flags) {
        return java.util.Base64.getDecoder().decode(value);
    }
}
''',
                encoding="utf-8",
            )
            runtime_classes = root / "runtime-classes"
            runtime_classes.mkdir()
            runtime_compile = self._compile(runtime_classes, source, shim)
            self.assertEqual(0, runtime_compile.returncode, runtime_compile.stderr)
            run = subprocess.run(
                [self.java, "-cp", str(runtime_classes), "repro.Tiny"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=60,
                env=self.env,
            )
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertEqual("hello-android", run.stdout)


if __name__ == "__main__":
    unittest.main()
