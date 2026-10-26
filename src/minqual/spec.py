from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

LANGUAGES = [
    "python",
    "javascript",
    "typescript",
    "java",
    "csharp",
    "c",
    "cpp",
    "go",
    "rust",
    "php",
]

ALIASES = {
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "node": "javascript",
    "ts": "typescript",
    "c#": "csharp",
    "cs": "csharp",
    "c++": "cpp",
    "cxx": "cpp",
    "golang": "go",
    "rs": "rust",
    "rb": "ruby",
}

LIMITS = {
    "max_files": 20,
    "max_file_bytes": 100_000,
    "max_total_bytes": 200_000,
    "build_timeout": 60,
    "run_timeout": 20,
    "output_chars": 20_000,
}

HINTS = {
    "python": "Python 3.11+",
    "javascript": "Node.js 20+",
    "typescript": "Node.js and tsc (npm install -g typescript)",
    "java": "JDK 17+ with javac and java on PATH",
    "csharp": ".NET SDK 8+ (dotnet)",
    "c": "gcc or cc",
    "cpp": "g++ or c++",
    "go": "Go 1.21+",
    "rust": "Rust toolchain with a working linker (rustc)",
    "php": "PHP 8+",
}


class ToolchainError(ValueError):
    pass


def normalize_language(value: str) -> str:
    key = str(value or "").strip().lower()
    key = ALIASES.get(key, key)
    if key not in LANGUAGES:
        raise ValueError(f"unsupported language: {value!r}; expected one of {', '.join(LANGUAGES)}")
    return key


def _cache_root() -> Path:
    base = (
        os.environ.get("XDG_CACHE_HOME")
        or os.environ.get("LOCALAPPDATA")
        or os.environ.get("HOME")
        or tempfile.gettempdir()
    )
    return Path(base) / "minqual"


CACHE_ROOT = _cache_root()
CACHE_ROOT.mkdir(parents=True, exist_ok=True)
TMP_ROOT = CACHE_ROOT / "tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def _which(name: str | None) -> str | None:
    if not name:
        return None
    found = shutil.which(name)
    return str(Path(found)) if found else None


def _detect() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    python = sys.executable
    if python:
        result["python"] = {"python": python}
    node = _which("node")
    if node:
        result["javascript"] = {"node": node}
    tsc = _which("tsc")
    if node and tsc:
        result["typescript"] = {"node": node, "tsc": tsc}
    java = _which("java")
    javac = _which("javac")
    if java and javac:
        result["java"] = {"java": java, "javac": javac}
    dotnet = _which("dotnet")
    if dotnet:
        result["csharp"] = {"dotnet": dotnet}
    gcc = _which("gcc") or _which("cc")
    if gcc:
        result["c"] = {"gcc": gcc}
    gpp = _which("g++") or _which("c++")
    if gpp:
        result["cpp"] = {"g++": gpp}
    go = _which("go")
    if go:
        result["go"] = {"go": go}
    rustc = _which("rustc")
    if rustc:
        result["rust"] = {"rustc": rustc}
    php = _which("php")
    if php:
        result["php"] = {"php": php}
    return result


def _load() -> dict[str, dict[str, str]]:
    configured = os.environ.get("MINQUAL_TOOLCHAINS", "").strip()
    if not configured:
        return _detect()
    path = Path(configured).expanduser()
    if not path.is_file():
        raise ToolchainError(f"MINQUAL_TOOLCHAINS is not a file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolchainError("MINQUAL_TOOLCHAINS must contain a JSON object")
    return data


TOOLCHAINS = _load()


def tool(language: str, key: str) -> str:
    value = (TOOLCHAINS.get(language) or {}).get(key)
    if not isinstance(value, str) or not value.strip():
        hint = HINTS.get(language, language)
        raise ToolchainError(
            f"missing toolchain '{key}' for {language}. Install {hint}, add it to PATH, "
            "or set MINQUAL_TOOLCHAINS to a JSON configuration."
        )
    return value


def _command_dirs() -> list[Path]:
    directories: list[Path] = []
    for commands in TOOLCHAINS.values():
        if not isinstance(commands, dict):
            continue
        for value in commands.values():
            if isinstance(value, str) and value and not value.lower().endswith(".js"):
                parent = Path(value).parent
                if parent.exists():
                    directories.append(parent)
    rust_gcc = (TOOLCHAINS.get("c") or {}).get("gcc")
    if isinstance(rust_gcc, str):
        directories.append(Path(rust_gcc).parent)
    system_root = Path(os.environ.get("SYSTEMROOT", r"C:\Windows"))
    directories.extend([system_root / "System32", system_root])
    seen: set[str] = set()
    unique: list[Path] = []
    for directory in directories:
        key = str(directory).lower()
        if key not in seen:
            seen.add(key)
            unique.append(directory)
    return unique


def base_env(language: str) -> dict[str, str]:
    keep = [
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "TEMP",
        "TMP",
        "COMSPEC",
        "PATHEXT",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "COMMONPROGRAMFILES",
        "PROGRAMDATA",
        "ALLUSERSPROFILE",
        "COMPUTERNAME",
        "USERNAME",
        "USERDOMAIN",
        "OS",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER",
    ]
    env = {key: os.environ[key] for key in keep if key in os.environ}
    env["PATH"] = os.pathsep.join(str(path) for path in _command_dirs())
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["HOME"] = os.environ.get("USERPROFILE", str(CACHE_ROOT))
    env["DOTNET_CLI_HOME"] = str(CACHE_ROOT / "dotnet-home")
    env["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
    env["DOTNET_NOLOGO"] = "1"
    env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    env["NUGET_PACKAGES"] = str(CACHE_ROOT / "nuget")
    env["GOCACHE"] = str(CACHE_ROOT / "gocache")
    env["GOPATH"] = str(CACHE_ROOT / "gopath")
    env["GO111MODULE"] = "on"
    env["GOTOOLCHAIN"] = "local"
    env["CARGO_TARGET_DIR"] = str(CACHE_ROOT / "cargo-target")
    dotnet = (TOOLCHAINS.get("csharp") or {}).get("dotnet")
    if isinstance(dotnet, str):
        env["DOTNET_ROOT"] = str(Path(dotnet).parent)
    for folder in (env["DOTNET_CLI_HOME"], env["NUGET_PACKAGES"], env["GOCACHE"], env["GOPATH"]):
        Path(folder).mkdir(parents=True, exist_ok=True)
    return env
