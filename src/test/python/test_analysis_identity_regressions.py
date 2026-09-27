import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
PYSCRIPTS = ROOT / "src/main/resources/pyscripts"
for path in (
    PYSCRIPTS / "analysis/core",
    PYSCRIPTS / "analysis/data",
    PYSCRIPTS / "analysis/utils",
    PYSCRIPTS / "analysis/reporting",
    PYSCRIPTS,
):
    sys.path.insert(0, str(path))

import astParser as ast_parser  # noqa: E402
import main as pipeline_main  # noqa: E402
import taintAnalyzer as taint_analyzer  # noqa: E402


_REAL_PARSE_ONE = ast_parser._parse_one
_COMPLETION_POLICY = "target_first"


class _Future:
    def __init__(self, file_path):
        self.file_path = file_path
        self._result = _REAL_PARSE_ONE(file_path)

    def result(self):
        return self._result


class _ControlledExecutor:
    def __init__(self, max_workers):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def submit(self, _function, file_path):
        return _Future(file_path)

    def map(self, function, file_paths):
        return map(function, file_paths)


def _controlled_as_completed(futures):
    futures = list(futures)
    preferred = "10_Target.java" if _COMPLETION_POLICY == "target_first" else "20_Decoy.java"
    return sorted(futures, key=lambda future: Path(future.file_path).name != preferred)


class _ForcedFiveWorkerASTParser(ast_parser.ASTParser):
    def __init__(self):
        super().__init__(max_workers=5)


class AnalysisIdentityRegressionTests(unittest.TestCase):
    def setUp(self):
        self.original_executor = ast_parser.ProcessPoolExecutor
        self.original_taint_parser = taint_analyzer.ASTParser
        ast_parser.ProcessPoolExecutor = _ControlledExecutor
        completion_patch = mock.patch.object(
            ast_parser, "as_completed", _controlled_as_completed, create=True
        )
        completion_patch.start()
        self.addCleanup(completion_patch.stop)
        taint_analyzer.ASTParser = _ForcedFiveWorkerASTParser

    def tearDown(self):
        ast_parser.ProcessPoolExecutor = self.original_executor
        taint_analyzer.ASTParser = self.original_taint_parser

    def _write_identity_fixture(self, root):
        sources = {
            "20_Decoy.java": """class Decoy {
    void shared() {
        System.out.println(\"DECOY_SHARED\");
    }
}
""",
            "50_Filler3.java": "class Filler3 { void unique3() { int x = 3; } }\n",
            "30_Filler1.java": "class Filler1 { void unique1() { int x = 1; } }\n",
            "10_Target.java": """class Target {
    void shared() {
        String value = getParameter(\"TARGET_SHARED\");
        System.out.println(value);
    }

    String getParameter(String name) {
        return name;
    }
}
""",
            "40_Filler2.java": "class Filler2 { void unique2() { int x = 2; } }\n",
        }
        for name, source in sources.items():
            (root / name).write_text(source, encoding="utf-8")
        return sorted(sources)

    def test_parallel_completion_order_never_changes_qualified_method_source(self):
        global _COMPLETION_POLICY

        for policy in ("decoy_first", "target_first"):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as temp_dir:
                _COMPLETION_POLICY = policy
                root = Path(temp_dir)
                expected_order = self._write_identity_fixture(root)

                tainted = taint_analyzer.TaintAnalysis(str(root))
                analyze_method = getattr(pipeline_main, "__analyze_method")
                result_path = analyze_method(str(root), tainted)
                payload = json.loads(Path(result_path).read_text(encoding="utf-8"))
                entries = [entry for group in payload for entry in group["tainted"]]
                selected = [entry for entry in entries if entry["method_name"].startswith("Target.shared.")]

                self.assertTrue(selected, payload)
                self.assertTrue(all(Path(entry["file_path"]).name == "10_Target.java" for entry in selected))
                self.assertTrue(all("TARGET_SHARED" in entry["source_code"] for entry in selected))
                self.assertTrue(all("DECOY_SHARED" not in entry["source_code"] for entry in selected))
                self.assertEqual(expected_order, [Path(path).name for path in tainted.source_codes])

    def test_main_serializes_the_exact_tainted_overload(self):
        tainted_no_args = """    void process() {
        String value = getParameter(\"OVERLOAD_TAINT\");
        System.out.println(value);
    }"""
        clean_string = """    void process(String ignored) {
        System.out.println(ignored);
    }"""
        tainted_int = """    void process(int ignored) {
        String value = getParameter(\"OVERLOAD_INT_TAINT\");
        System.out.println(value);
    }"""

        variants = (
            ("tainted_first", (tainted_no_args, clean_string), tainted_no_args),
            ("tainted_second", (clean_string, tainted_no_args), tainted_no_args),
            ("same_arity_types", (clean_string, tainted_int), tainted_int),
        )

        for name, declarations, expected_source in variants:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                java_file = root / "Overloaded.java"
                java_file.write_text(
                    "class Overloaded {\n"
                    + "\n\n".join(declarations)
                    + "\n\n    String getParameter(String name) {\n"
                    + "        return name;\n"
                    + "    }\n"
                    + "}\n",
                    encoding="utf-8",
                )

                compile_result = subprocess.run(
                    [
                        "/usr/lib/jvm/java-17-openjdk/bin/javac",
                        "-d",
                        str(root / "classes"),
                        str(java_file),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(0, compile_result.returncode, compile_result.stderr)

                pipeline_main.main(str(root))
                payload = json.loads((root / "analysis_result.json").read_text(encoding="utf-8"))
                entries = [entry for group in payload for entry in group["tainted"]]

                self.assertEqual(1, len(entries), payload)
                self.assertEqual(java_file, Path(entries[0]["file_path"]))
                self.assertTrue(entries[0]["method_name"].startswith("Overloaded.process."))
                self.assertEqual(expected_source, entries[0]["source_code"])

    def test_constructor_taint_is_serialized_without_aborting_analysis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            java_file = root / "ConstructorCase.java"
            java_file.write_text(
                """class ConstructorCase {
    ConstructorCase() {
        String value = System.getProperty(\"CONSTRUCTOR_TAINT\");
        System.out.println(value);
    }
}
""",
                encoding="utf-8",
            )

            tainted = taint_analyzer.TaintAnalysis(str(root))
            flows = tainted._priority_flow()
            self.assertTrue(
                any("ConstructorCase.ConstructorCase.getProperty" in flow for flow in flows),
                flows,
            )

            analyze_method = getattr(pipeline_main, "__analyze_method")
            result_path = analyze_method(str(root), tainted)
            payload = json.loads(Path(result_path).read_text(encoding="utf-8"))
            entries = [entry for group in payload for entry in group["tainted"]]
            selected = [
                entry
                for entry in entries
                if entry["method_name"].startswith("ConstructorCase.ConstructorCase.")
            ]

            self.assertTrue(selected, payload)
            self.assertTrue(all(Path(entry["file_path"]) == java_file for entry in selected))
            self.assertTrue(all("CONSTRUCTOR_TAINT" in entry["source_code"] for entry in selected))
            self.assertTrue(all(entry["tree_position"] for entry in selected))
            self.assertTrue(all(entry["cut_tree"].startswith("Method: ConstructorCase(") for entry in selected))

    def test_ambiguous_or_missing_identity_clears_previous_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_identity_fixture(root)
            tainted = taint_analyzer.TaintAnalysis(str(root))
            analyzer = tainted.method_analyzer

            self.assertIsNotNone(analyzer.get_cut_tree("shared", "Target"))
            self.assertEqual("10_Target.java", Path(analyzer._file_path).name)

            self.assertIsNone(analyzer.get_cut_tree("missing", "Target"))
            self.assertEqual("", analyzer._file_path)
            self.assertEqual("", analyzer._get_position)
            self.assertIsNone(analyzer._current_node)

            self.assertIsNone(analyzer.get_cut_tree("shared"))
            self.assertEqual("", analyzer._file_path)
            self.assertEqual("", analyzer._get_position)
            self.assertIsNone(analyzer._current_node)


if __name__ == "__main__":
    unittest.main()
