from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath

from .spec import LIMITS, TMP_ROOT, base_env, normalize_language, tool

CASE_RE = re.compile(r"^CASE (.+) (PASS|FAIL)$")
BLOCKED_NAMES = {
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "go.mod",
    "go.sum",
    "cargo.toml",
    "cargo.lock",
    "makefile",
    "cmakelists.txt",
    "global.json",
    ".editorconfig",
}
BLOCKED_SUFFIXES = (".csproj", ".sln", ".props", ".targets", ".suo", ".user")


class InputError(ValueError):
    pass


def _validate_files(files: dict[str, str] | None) -> dict[str, str]:
    if files is None:
        return {}
    if not isinstance(files, dict):
        raise InputError("files must be an object mapping relative paths to text")
    if len(files) > LIMITS["max_files"]:
        raise InputError(f"too many files (max {LIMITS['max_files']})")
    total = 0
    clean: dict[str, str] = {}
    for raw_name, content in files.items():
        if not isinstance(raw_name, str) or not isinstance(content, str):
            raise InputError("each file path and content must be a string")
        name = raw_name.replace("\\", "/")
        path = PurePosixPath(name)
        if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in path.parts:
            raise InputError(f"unsafe path: {raw_name!r}")
        if not path.parts or any(part in ("", ".") for part in path.parts):
            raise InputError(f"invalid path: {raw_name!r}")
        lower = path.name.lower()
        if lower in BLOCKED_NAMES or lower.startswith("directory.build.") or lower.endswith(BLOCKED_SUFFIXES):
            raise InputError(f"build-control file is not allowed: {raw_name!r}")
        size = len(content.encode("utf-8"))
        if size > LIMITS["max_file_bytes"]:
            raise InputError(f"file too large: {raw_name!r}")
        total += size
        clean[str(path)] = content
    if total > LIMITS["max_total_bytes"]:
        raise InputError(f"total size too large (max {LIMITS['max_total_bytes']} bytes)")
    return clean


def validate_files(files: dict[str, str] | None) -> dict[str, str]:
    return _validate_files(files)


def _write(work: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        target = work / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


def _run(cmd: list[str], cwd: Path, language: str, timeout: int) -> dict:
    started = time.time()
    env = base_env(language)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        creationflags=flags,
    )
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate(timeout=5)
    text = (out or "") + (("\n" + err) if err else "")
    if len(text) > LIMITS["output_chars"]:
        text = text[-LIMITS["output_chars"] :]
    return {
        "ok": (not timed_out and proc.returncode == 0),
        "code": proc.returncode,
        "timed_out": timed_out,
        "output": text,
        "duration": round(time.time() - started, 2),
    }


def _expected_case_names(tests: dict[str, str]) -> list[str]:
    raw = tests.get("cases.tsv", "")
    names: list[str] = []
    seen: set[str] = set()
    for line_number, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name = line.split("\t", 1)[0].strip()
        if not name:
            raise InputError(f"cases.tsv line {line_number} has an empty case name")
        if name in seen:
            raise InputError(f"cases.tsv line {line_number} duplicates case name: {name!r}")
        names.append(name)
        seen.add(name)
    return names


def _parse_cases(output: str, expected_names: list[str]) -> tuple[list[dict], int, list[str]]:
    observed: dict[str, list[bool]] = {}
    expected = set(expected_names)
    errors: list[str] = []
    for line in output.splitlines():
        match = CASE_RE.match(line.strip())
        if match:
            name = match.group(1)
            if name not in expected:
                errors.append(f"unexpected test case result: {name!r}")
            observed.setdefault(name, []).append(match.group(2) == "PASS")

    cases: list[dict] = []
    for name in expected_names:
        results = observed.get(name, [])
        if not results:
            errors.append(f"missing test case result: {name!r}")
        elif len(results) > 1:
            errors.append(f"duplicate test case result: {name!r}")
        cases.append({"name": name, "pass": len(results) == 1 and results[0]})
    return cases, sum(1 for case in cases if case["pass"]), errors


def _py(work: Path, tc: dict) -> tuple[dict, dict | None]:
    py = tool("python", "python")
    sources = [str(p) for p in work.rglob("*.py")]
    build = _run([py, "-m", "py_compile", *sources], work, "python", 30)
    if not build["ok"]:
        return build, None
    return build, _run([py, "run_cases.py"], work, "python", LIMITS["run_timeout"])


def _js(work: Path, tc: dict) -> tuple[dict, dict | None]:
    node = tool("javascript", "node")
    sources = [str(p) for p in work.rglob("*.mjs")]
    build = _run([node, "--check", *sources], work, "javascript", 30)
    if not build["ok"]:
        return build, None
    return build, _run([node, "run_cases.mjs"], work, "javascript", LIMITS["run_timeout"])


def _ts(work: Path, tc: dict) -> tuple[dict, dict | None]:
    tsc = tool("typescript", "tsc")
    if tsc.lower().endswith(".js"):
        tsc_command = [tool("typescript", "node"), tsc]
    elif tsc.lower().endswith((".cmd", ".bat")):
        tsc_command = ["cmd", "/c", tsc]
    else:
        tsc_command = [tsc]
    sources = [str(p.relative_to(work)) for p in work.rglob("*.ts")]
    build = _run(
        [
            *tsc_command,
            "--strict",
            "--target",
            "ES2022",
            "--module",
            "commonjs",
            "--moduleResolution",
            "node",
            "--lib",
            "ES2022,DOM",
            "--skipLibCheck",
            "--outDir",
            "out",
            *sources,
        ],
        work,
        "typescript",
        45,
    )
    if not (work / "out" / "run_cases.js").exists():
        return build, None
    node = tool("typescript", "node")
    return build, _run([node, "out/run_cases.js"], work, "typescript", LIMITS["run_timeout"])


def _java(work: Path, tc: dict) -> tuple[dict, dict | None]:
    javac = tool("java", "javac")
    java = tool("java", "java")
    sources = [str(p.relative_to(work)) for p in work.rglob("*.java")]
    out = work / "out"
    out.mkdir(exist_ok=True)
    build = _run(
        [javac, "--release", "17", "-encoding", "UTF-8", "-Xlint:all", "-d", "out", *sources],
        work,
        "java",
        45,
    )
    if not build["ok"]:
        return build, None
    return build, _run([java, "-cp", "out", "RunCases"], work, "java", LIMITS["run_timeout"])


def _csharp(work: Path, tc: dict) -> tuple[dict, dict | None]:
    dotnet = tool("csharp", "dotnet")
    csproj = work / "Task.csproj"
    if not csproj.exists():
        csproj.write_text(
            """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AssemblyName>Task</AssemblyName>
    <EnableDefaultCompileItems>true</EnableDefaultCompileItems>
    <TreatWarningsAsErrors>false</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
""",
            encoding="utf-8",
            newline="\n",
        )
    build = _run(
        [dotnet, "build", "Task.csproj", "-c", "Release", "-o", "out", "--nologo", "-v", "minimal"],
        work,
        "csharp",
        90,
    )
    if not build["ok"] or not (work / "out" / "Task.dll").exists():
        return build, None
    return build, _run([dotnet, "out/Task.dll"], work, "csharp", LIMITS["run_timeout"])


def _c(work: Path, tc: dict) -> tuple[dict, dict | None]:
    gcc = tool("c", "gcc")
    sources = [str(p.relative_to(work)) for p in work.rglob("*.c")]
    build = _run(
        [gcc, "-std=c17", "-Wall", "-Wextra", "-O1", "-I.", "-o", "test.exe", *sources],
        work,
        "c",
        45,
    )
    if not build["ok"]:
        return build, None
    return build, _run([str(work / "test.exe")], work, "c", LIMITS["run_timeout"])


def _cpp(work: Path, tc: dict) -> tuple[dict, dict | None]:
    gpp = tool("cpp", "g++")
    sources = [str(p.relative_to(work)) for p in work.rglob("*.cpp")]
    build = _run(
        [gpp, "-std=c++20", "-Wall", "-Wextra", "-O1", "-I.", "-o", "test.exe", *sources],
        work,
        "cpp",
        45,
    )
    if not build["ok"]:
        return build, None
    return build, _run([str(work / "test.exe")], work, "cpp", LIMITS["run_timeout"])


def _go(work: Path, tc: dict) -> tuple[dict, dict | None]:
    go = tool("go", "go")
    if not (work / "go.mod").exists():
        (work / "go.mod").write_text("module task\n\ngo 1.21\n", encoding="utf-8")
    build = _run([go, "build", "-o", "test.exe", "."], work, "go", 60)
    if not build["ok"]:
        return build, None
    return build, _run([str(work / "test.exe")], work, "go", LIMITS["run_timeout"])


def _rust(work: Path, tc: dict) -> tuple[dict, dict | None]:
    rustc = tool("rust", "rustc")
    build = _run([rustc, "--edition", "2021", "-O", "run_cases.rs", "-o", "test.exe"], work, "rust", 60)
    if not build["ok"]:
        return build, None
    return build, _run([str(work / "test.exe")], work, "rust", LIMITS["run_timeout"])


def _php(work: Path, tc: dict) -> tuple[dict, dict | None]:
    php = tool("php", "php")
    sources = [str(p.relative_to(work)) for p in work.rglob("*.php")]
    build = _run([php, "-l", *sources], work, "php", 30)
    if not build["ok"]:
        return build, None
    return build, _run(
        [php, "-d", "error_reporting=E_ALL", "-d", "display_errors=1", "run_cases.php"],
        work,
        "php",
        LIMITS["run_timeout"],
    )


RUNNERS = {
    "python": _py,
    "javascript": _js,
    "typescript": _ts,
    "java": _java,
    "csharp": _csharp,
    "c": _c,
    "cpp": _cpp,
    "go": _go,
    "rust": _rust,
    "php": _php,
}


def run_tests(language: str, files: dict[str, str], tests: dict[str, str] | None = None) -> dict:
    lang = normalize_language(language)
    solution = _validate_files(files)
    test_files = _validate_files(tests)
    expected_case_names = _expected_case_names(test_files)
    total = len(expected_case_names)
    work = Path(tempfile.mkdtemp(prefix=f"minqual-{lang}-", dir=str(TMP_ROOT)))
    try:
        _write(work, solution)
        _write(work, test_files)
        build, run = RUNNERS[lang](work, test_files)
        output = (run or {}).get("output", "")
        cases, passed, case_errors = _parse_cases(output, expected_case_names)
        return {
            "language": lang,
            "build_ok": bool(build.get("ok")),
            "build_output": build.get("output", ""),
            "build_timed_out": bool(build.get("timed_out")),
            "run_timed_out": bool((run or {}).get("timed_out")),
            "status": (
                "ok"
                if run and run.get("ok") and not case_errors
                else ("build_failed" if not build.get("ok") else "tests_failed")
            ),
            "passed": passed,
            "total": total,
            "cases": cases,
            "case_errors": case_errors,
            "output": output,
            "duration": round(build.get("duration", 0) + (run or {}).get("duration", 0), 2),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


def solution_source(files: dict[str, str], language: str) -> str:
    suffixes = {
        "python": (".py",),
        "javascript": (".mjs",),
        "typescript": (".ts",),
        "java": (".java",),
        "csharp": (".cs",),
        "c": (".c", ".h"),
        "cpp": (".cpp", ".hpp", ".h"),
        "go": (".go",),
        "rust": (".rs",),
        "php": (".php",),
    }[language]
    return "\n".join(
        content
        for name, content in sorted(files.items())
        if name.endswith(suffixes)
        and "cases" not in Path(name).name.lower()
        and "run_" not in Path(name).name.lower()
    )
