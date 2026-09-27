#!/usr/bin/env python3
"""Run full Java-target acceptance with no AI key; output directory must be new.

Requires Python 3.10+, javalang, pycryptodome, JDK 17, target Gradle wrapper,
and Xvfb for EXIF. This maintainer harness is not the plugin runtime.
Target baseline JARs must already have been built. See docs/release-0.8.0.md.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

if sys.version_info < (3, 10):
    raise SystemExit("run_target_smoke.py requires Python 3.10 or later")

EXCLUDED = {"obfuscated_project_folder", "build", "temp", ".git", "test", "docs"}
SCRIPT_DIRS = ("", "analysis/core", "analysis/data", "analysis/utils", "analysis/reporting")
XMAS_CASES = {
    "valid-full": "3\n티본스테이크-1,바비큐립-1,초코케이크-2,제로콜라-1\n",
    "valid-no-benefit": "26\n타파스-1,제로콜라-1\n",
    "invalid-date-retry": "a\n3\n티본스테이크-1,바비큐립-1,초코케이크-2,제로콜라-1\n",
    "invalid-menu-retry": "3\n뚝배기-1\n타파스-1,제로콜라-1\n",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def copy_target(source: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(source, output, ignore=lambda _path, names: [name for name in names if name in EXCLUDED])


def flatten_scripts(repo: Path, destination: Path) -> list[str]:
    resources = repo / "src/main/resources/pyscripts"
    names = []
    for line in (resources / "check_hash").read_text(encoding="utf-8").splitlines():
        name, expected = line.split()
        source = next((resources / folder / f"{name}.py" for folder in SCRIPT_DIRS
                       if (resources / folder / f"{name}.py").is_file()), None)
        if source is None:
            raise FileNotFoundError(f"missing script: {name}")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"hash mismatch: {name}: {actual} != {expected}")
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination / source.name)
        names.append(name)
    return names


def run_logged(name: str, argv: list[str], env: dict[str, str], logs: Path,
               cwd: Path | None = None, allowed: tuple[int, ...] = (0,), timeout: int = 300) -> dict:
    log_path = logs / f"{name}.log"
    try:
        process = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=timeout)
        output = process.stdout
        code = process.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b""
        code = None
        timed_out = True
    header = ("COMMAND: " + json.dumps(argv, ensure_ascii=False) + "\n"
              + f"CWD: {cwd or Path.cwd()}\n").encode()
    footer = f"\nEXIT_CODE: {code}\nTIMED_OUT: {str(timed_out).lower()}\n".encode()
    log_path.write_bytes(header + output + footer)
    result = {"name": name, "command": argv, "cwd": str(cwd or Path.cwd()),
              "exit_code": code, "timed_out": timed_out, "log": str(log_path),
              "status": "passed" if not timed_out and code in allowed else "failed"}
    return result


def require(result: dict) -> dict:
    if result["status"] != "passed":
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


def capture(argv: list[str], env: dict[str, str], log_path: Path, cwd: Path | None = None,
            input_data: bytes | None = None, timeout: int = 30) -> tuple[int, bytes]:
    try:
        process = subprocess.run(argv, cwd=cwd, env=env, input=input_data, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=timeout)
        code, output = process.returncode, process.stdout
    except subprocess.TimeoutExpired as exc:
        code, output = 124, exc.stdout or b""
    log_path.write_bytes(output)
    return code, output


def only_jar(folder: Path) -> Path:
    jars = sorted(path for path in (folder / "build/libs").glob("*.jar")
                  if not any(tag in path.name for tag in ("-sources", "-javadoc")))
    if len(jars) != 1:
        raise RuntimeError(f"expected one runnable jar in {folder / 'build/libs'}, found {jars}")
    return jars[0]


def mapped_class(mapping_path: Path, original_file: str) -> str:
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    matches = [value for key, value in mapping.items()
               if key.replace("\\", "/").endswith("/src/main/java/" + original_file)]
    if len(matches) != 1:
        raise RuntimeError(f"mapping for {original_file}: {matches}")
    normalized = matches[0].replace("\\", "/")
    marker = "/src/main/java/"
    if marker not in normalized:
        raise RuntimeError(f"mapped path lacks {marker}: {normalized}")
    return normalized.split(marker, 1)[1].removesuffix(".java").replace("/", ".")


def exif_acceptance(args, output: Path, jar: Path, env: dict[str, str], logs: Path) -> dict:
    classes = args.run_root / "smoke/classes"
    classes.mkdir(parents=True, exist_ok=True)
    compile_result = require(run_logged(
        "accept-exif-compile",
        [str(args.jdk / "bin/javac"), "-d", str(classes), str(args.exif_probe)],
        env, logs,
    ))
    class_name = mapped_class(output / "identifier_mapping.json",
                              "de/florian/exif/remover/ExifRemover.java")
    core_result = require(run_logged(
        "accept-exif-core",
        [str(args.jdk / "bin/java"), "-cp", f"{classes}{os.pathsep}{jar}",
         "ExifRemoverReflectionSmoke", class_name,
         str(args.target / "docs/images/mainframe-screenshot.png"),
         str(args.run_root / "smoke/exif-work")],
        env, logs,
    ))
    gui_log = logs / "accept-exif-gui.log"
    gui_command = ["timeout", "5s", "xvfb-run", "-a", str(args.jdk / "bin/java"), "-jar", str(jar)]
    gui_code, gui_output = capture(gui_command, env, gui_log, timeout=10)
    stack_trace = bool(re.search(rb"(?m)^(Exception in thread|Caused by:|\s+at \S+\(|java\.[\w.]+(?:Exception|Error):)", gui_output))
    gui = {"name": "accept-exif-gui", "command": gui_command, "exit_code": gui_code,
           "log": str(gui_log), "stack_trace": stack_trace,
           "status": "passed" if gui_code == 124 and not stack_trace else "failed"}
    if gui["status"] != "passed":
        raise RuntimeError(json.dumps(gui, ensure_ascii=False))
    return {"status": "passed", "mapped_class": class_name,
            "compile": compile_result, "core": core_result, "gui": gui}


def christmas_acceptance(args, jar: Path, env: dict[str, str], logs: Path) -> dict:
    baseline_jar = args.baseline_jar or only_jar(args.target)
    cases = []
    for name, transcript in XMAS_CASES.items():
        baseline_log = logs / f"accept-christmas-{name}-baseline.log"
        transformed_log = logs / f"accept-christmas-{name}-transformed.log"
        command_base = [str(args.jdk / "bin/java"), "-jar"]
        data = transcript.encode("utf-8")
        baseline_code, baseline = capture(command_base + [str(baseline_jar)], env, baseline_log, input_data=data)
        transformed_code, transformed = capture(command_base + [str(jar)], env, transformed_log, input_data=data)
        equal = baseline == transformed
        case = {"name": name, "input": transcript, "baseline_jar": str(baseline_jar),
                "baseline_exit_code": baseline_code, "transformed_exit_code": transformed_code,
                "byte_equal": equal, "baseline_log": str(baseline_log),
                "transformed_log": str(transformed_log),
                "status": "passed" if baseline_code == transformed_code == 0 and equal else "failed"}
        cases.append(case)
    return {"status": "passed" if all(case["status"] == "passed" for case in cases) else "failed",
            "cases": cases}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--kind", required=True, choices=("exif", "christmas"))
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--jdk", type=Path, default=Path("/usr/lib/jvm/java-17-openjdk"))
    parser.add_argument("--gradle-home", required=True, type=Path)
    parser.add_argument("--baseline-jar", type=Path)
    parser.add_argument("--exif-probe", type=Path,
                        default=Path(__file__).with_name("ExifRemoverReflectionSmoke.java"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.repo = args.repo.resolve()
    args.target = args.target.resolve()
    args.run_root = args.run_root.resolve()
    args.python = Path(os.path.abspath(args.python))  # keep a venv executable symlink intact
    args.jdk = args.jdk.resolve()
    args.gradle_home = args.gradle_home.resolve()
    args.exif_probe = args.exif_probe.resolve()
    if args.baseline_jar:
        args.baseline_jar = args.baseline_jar.resolve()

    if args.run_root.is_relative_to(args.repo) or args.run_root.is_relative_to(args.target):
        raise ValueError("--run-root must be outside the source repositories")
    args.run_root.mkdir(parents=True, exist_ok=False)
    output = args.run_root / "obfuscated_project_folder"
    scripts = args.run_root / "temp_asdf_qwer"
    logs = args.run_root / "logs"
    logs.mkdir(parents=True)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "driver": str(Path(__file__).resolve()),
        "repo": str(args.repo), "repo_commit": git(args.repo, "rev-parse", "HEAD"),
        "repo_status_before": git(args.repo, "status", "--porcelain"),
        "target": str(args.target), "target_commit": git(args.target, "rev-parse", "HEAD"),
        "target_status_before": git(args.target, "status", "--porcelain"),
        "output": str(output), "kind": args.kind, "steps": [], "status": "running",
    }
    summary_path = args.run_root / "summary.json"
    try:
        copy_target(args.target, output)
        names = flatten_scripts(args.repo, scripts)
        summary["flattened_scripts"] = names
        summary["flattened_script_count"] = len(names)

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["JAVA_HOME"] = str(args.jdk)
        env["PATH"] = str(args.jdk / "bin") + os.pathsep + env.get("PATH", "")
        env["GRADLE_USER_HOME"] = str(args.gradle_home)
        for key in tuple(env):
            if key.endswith("API_KEY") or key in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"}:
                env.pop(key, None)

        java = args.repo / "src/main/resources/java"
        key_decrypt = (java / "keyDecryptLin.java").read_text(encoding="utf-8")
        string_decrypt = (java / "stringDecryptLin.java").read_text(encoding="utf-8")
        py = str(args.python)
        pipeline = [
            ("01-checkJavaSyntax", [py, "-u", str(scripts / "checkJavaSyntax.py"), str(args.target)], None),
            ("02-removeComments", [py, "-u", str(scripts / "removeComments.py"), str(output)], None),
            ("03-stringObfuscate", [py, "-u", str(scripts / "stringObfuscate.py"), str(output),
                                    key_decrypt, string_decrypt, "false"], None),
            ("04-main", [py, "-u", str(scripts / "main.py"), str(output), "", "true", "true", "true"], None),
            ("05-levelObfuscate", [py, "-u", str(scripts / "levelObfuscate.py"), str(output),
                                   "true", "true", "true", "true"], None),
            ("06-identifierObfuscate", [py, "-u", str(scripts / "identifierObfuscate.py"), str(output)], None),
            ("07-target-build", ["sh", str(output / "gradlew"), "--no-daemon", "--max-workers=2", "clean", "build"], output),
        ]
        for name, command, cwd in pipeline:
            result = run_logged(name, command, env, logs, cwd=cwd)
            summary["steps"].append(result)
            require(result)

        jar = only_jar(output)
        summary["artifact"] = str(jar)
        summary["acceptance"] = (exif_acceptance(args, output, jar, env, logs) if args.kind == "exif"
                                 else christmas_acceptance(args, jar, env, logs))
        require(summary["acceptance"])
        summary["target_status_after"] = git(args.target, "status", "--porcelain")
        if summary["target_status_after"] != summary["target_status_before"]:
            raise RuntimeError("target repository changed")
        summary["status"] = "passed"
        return 0
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = repr(exc)
        summary["target_status_after"] = git(args.target, "status", "--porcelain")
        return 1
    finally:
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": summary["status"], "summary": str(summary_path),
                          "error": summary.get("error")}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
