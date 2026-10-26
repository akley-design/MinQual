from __future__ import annotations

import json
from typing import Literal

from mcp.server.fastmcp import FastMCP

from .checks import run_tests, validate_files
from .spec import normalize_language
from .static import analyze

mcp = FastMCP(
    "minqual",
    instructions=(
        "MinQual is a verification gate for code. It compiles supplied files, runs optional focused tests, "
        "and returns static findings for Python, JavaScript, TypeScript, Java, C#, C, C++, Go, Rust and PHP. "
        "It never receives credentials or hidden tests."
    ),
)


@mcp.tool()
def check(
    language: str,
    files: dict[str, str],
    tests: dict[str, str] | None = None,
    mode: Literal["full", "static"] = "full",
) -> str:
    """Check code before finishing.

    language: python, javascript, typescript, java, csharp, c, cpp, go, rust or php.
    files: relative path -> complete file content for solution files.
    tests: relative path -> complete content for a self-contained test runner and cases.tsv.
    mode: full compiles and runs the supplied tests; static only reports source heuristics.

    Limits: 20 files, 200 KB total, 15-90s timeouts. Paths must stay inside a temporary workspace.
    Any build error, failing case, or high-severity finding is returned as JSON. Fix it and call again.
    Code is compiled and executed locally in a temporary directory with a minimal environment.
    There is no network or filesystem sandbox; run only trusted code.
    """
    try:
        lang = normalize_language(language)
        if mode not in ("full", "static"):
            raise ValueError("mode must be full or static")
        if mode == "static" or not tests:
            files = validate_files(files)
            if tests:
                validate_files(tests)
            static = analyze(lang, files, None, "")
            return json.dumps(
                {
                    "ok": True,
                    "language": lang,
                    "mode": "static",
                    "static": static,
                    "tests": None,
                    "note": "Static heuristics only. Pass tests with mode=full to compile and run them.",
                },
                ensure_ascii=False,
            )
        run = run_tests(lang, files, tests)
        static = analyze(lang, files, run["build_ok"], run["build_output"])
        ok = bool(
            run["build_ok"]
            and run["total"] > 0
            and run["passed"] == run["total"]
            and not run["case_errors"]
        )
        payload = {
            "ok": ok,
            "language": lang,
            "mode": "full",
            "static": static,
            "tests": {
                "status": run["status"],
                "build_ok": run["build_ok"],
                "passed": run["passed"],
                "total": run["total"],
                "cases": run["cases"][:40],
                "case_errors": run["case_errors"][:40],
                "build_output": run["build_output"][-4000:],
                "output": run["output"][-4000:],
                "timed_out": bool(run["build_timed_out"] or run["run_timed_out"]),
                "duration": run["duration"],
            },
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as error:
        return json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}, ensure_ascii=False)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
