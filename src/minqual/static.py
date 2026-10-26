from __future__ import annotations

import re
from pathlib import Path

from .checks import solution_source
from .spec import normalize_language

COMMON = [
    (r"(?i)\bTODO\b|\bFIXME\b", "unfinished_marker", 4),
    (r"(?i)\bapi[_-]?key\b\s*[:=]\s*['\"][^'\"]+['\"]", "hardcoded_secret", 20),
    (r"catch\s*\([^)]*\)\s*\{\s*\}", "empty_catch", 6),
    (r"(?i)#\s*noqa|@ts-ignore|@SuppressWarnings|#!\[allow\(|//\s*nolint", "suppressed_diagnostic", 4),
    (r"(?i)shortcut:", "known_shortcut", 0),
]

BY_LANGUAGE = {
    "python": [
        (r"except\s*:", "bare_except", 6),
        (r"except\s+Exception\s*:\s*(?:pass|\.\.\.)", "swallowed_exception", 8),
        (r"\beval\s*\(", "eval", 8),
        (r"\bexec\s*\(", "exec", 8),
        (r"os\.system\s*\(", "os_system", 8),
        (r"subprocess\.(?:run|Popen)\([^)]*shell\s*=\s*True", "shell_true", 8),
        (r"\bassert\s+False", "assert_false", 4),
    ],
    "javascript": [
        (r"\beval\s*\(", "eval", 8),
        (r"new\s+Function\s*\(", "dynamic_function", 8),
        (r"\bas\s+any\b", "any_cast", 4),
        (r"\.innerHTML\s*=", "inner_html", 6),
        (r"child_process", "child_process", 6),
    ],
    "typescript": [
        (r"\beval\s*\(", "eval", 8),
        (r"new\s+Function\s*\(", "dynamic_function", 8),
        (r"\bas\s+any\b", "any_cast", 4),
        (r"@ts-ignore", "ts_ignore", 6),
        (r"\.innerHTML\s*=", "inner_html", 6),
        (r"child_process", "child_process", 6),
    ],
    "java": [
        (r"catch\s*\([^)]*\)\s*\{\s*\}", "empty_catch", 6),
        (r"Runtime\.getRuntime\(\)\.exec", "runtime_exec", 8),
        (r"e\.printStackTrace\(\)", "print_stacktrace", 2),
        (r"@SuppressWarnings", "suppressed_warning", 4),
    ],
    "csharp": [
        (r"catch\s*\([^)]*\)\s*\{\s*\}", "empty_catch", 6),
        (r"\bGC\.Collect\s*\(", "forced_gc", 4),
        (r"\bdynamic\b", "dynamic", 2),
        (r"Process\.Start\s*\(", "process_start", 6),
    ],
    "c": [
        (r"\b(?:strcpy|strcat|sprintf|gets)\s*\(", "unsafe_string", 6),
        (r"\bsystem\s*\(", "system", 8),
        (r"\bmalloc\s*\(", "unchecked_malloc", 2),
    ],
    "cpp": [
        (r"\b(?:strcpy|strcat|sprintf|gets)\s*\(", "unsafe_string", 6),
        (r"\bsystem\s*\(", "system", 8),
        (r"\breinterpret_cast\b", "reinterpret_cast", 2),
        (r"\bnew\s+\w+", "raw_new", 2),
    ],
    "go": [
        (r"\bpanic\s*\(", "panic", 6),
        (r"exec\.Command\s*\(", "exec_command", 4),
        (r"(?m)^\s*_\s*=\s*\w+", "ignored_value", 3),
    ],
    "rust": [
        (r"\.unwrap\s*\(\s*\)", "unwrap", 6),
        (r"\.expect\s*\(", "expect", 4),
        (r"\bpanic!\s*\(", "panic", 6),
        (r"\bunsafe\s*\{", "unsafe", 8),
        (r"\btodo!\s*\(|\bunimplemented!\s*\(", "unimplemented", 8),
    ],
    "php": [
        (r"\beval\s*\(", "eval", 8),
        (r"\b(?:exec|shell_exec|system|passthru)\s*\(", "shell_exec", 8),
        (r"(?<![A-Za-z0-9_])@\w+", "error_suppression", 4),
        (r"\bmysql_\w+", "legacy_mysql", 4),
    ],
}


def _lines(source: str) -> list[str]:
    return source.splitlines()


def _nesting(lines: list[str], language: str) -> int:
    if language == "python":
        depth = 0
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            depth = max(depth, len(line) - len(line.lstrip(" ")))
        return depth // 4
    depth = 0
    maximum = 0
    for line in lines:
        depth += line.count("{")
        maximum = max(maximum, depth)
        depth = max(0, depth - line.count("}"))
    return maximum


def _duplication(lines: list[str]) -> float:
    normalized = [line.strip() for line in lines if len(line.strip()) > 10 and not line.strip().startswith(("//", "#", "/*", "*"))]
    if len(normalized) < 8:
        return 0.0
    return round((len(normalized) - len(set(normalized))) / len(normalized), 3)


def _build_counts(output: str) -> tuple[int, int]:
    warnings = 0
    errors = 0
    for line in output.splitlines():
        low = line.lower()
        if "warning" in low and not re.search(r"\b0 warnings?\b", low):
            warnings += 1
        if "error" in low and not re.search(r"\b0 errors?\b", low):
            errors += 1
    return warnings, errors


def analyze(
    language: str,
    files: dict[str, str],
    build_ok: bool | None = None,
    build_output: str = "",
) -> dict:
    lang = normalize_language(language)
    source = solution_source(files, lang)
    lines = _lines(source)
    findings: list[dict] = []
    seen: set[tuple[str, int]] = set()
    penalty = 0
    for pattern, code, points in COMMON + BY_LANGUAGE[lang]:
        for match in re.finditer(pattern, source):
            line_no = source[: match.start()].count("\n") + 1
            key = (code, line_no)
            if key in seen:
                continue
            seen.add(key)
            if points:
                penalty += points
            snippet = lines[line_no - 1].strip()[:160] if line_no <= len(lines) else ""
            findings.append(
                {
                    "code": code,
                    "severity": "high" if points >= 8 else "medium" if points >= 4 else "low",
                    "line": line_no,
                    "message": snippet,
                }
            )
    warnings, errors = _build_counts(build_output)
    duplicate_ratio = _duplication(lines)
    max_nesting = _nesting(lines, lang)
    safety = max(0, 20 - min(20, penalty))
    warning_score = max(0, 20 - min(20, 3 * min(warnings, 6) + 5 * min(errors, 4)))
    maintain = 20
    maintain -= min(8, int(duplicate_ratio * 25))
    maintain -= min(6, max(0, max_nesting - 4) * 2)
    maintain = max(0, maintain)
    if build_ok is None:
        raw = warning_score + safety + maintain
        score = round(raw / 60 * 100)
        parts = {"build": None, "warnings": warning_score, "safety": safety, "maintainability": maintain}
    else:
        build = 40 if build_ok else 0
        score = build + warning_score + safety + maintain
        parts = {"build": build, "warnings": warning_score, "safety": safety, "maintainability": maintain}
    return {
        "score": max(0, min(100, score)),
        "build_ok": build_ok,
        "build_skipped": build_ok is None,
        "parts": parts,
        "warnings": warnings,
        "errors": errors,
        "findings": findings[:30],
        "duplicate_ratio": duplicate_ratio,
        "max_nesting": max_nesting,
        "lines": len([line for line in lines if line.strip()]),
    }
