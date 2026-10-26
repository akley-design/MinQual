# Toolchains

MinQual does not bundle compilers. It detects the commands below on `PATH` and uses them in a temporary workspace.

| Language | Required commands | Notes |
|---|---|---|
| Python | `python` | Python 3.11+ |
| JavaScript | `node` | Node.js 20+ |
| TypeScript | `node`, `tsc` | Install with `npm install -g typescript` |
| Java | `javac`, `java` | JDK 17+; the runner compiles with `--release 17` |
| C# | `dotnet` | .NET SDK 8+ |
| C | `gcc` or `cc` | C17 |
| C++ | `g++` or `c++` | C++20 |
| Go | `go` | Go 1.21+ |
| Rust | `rustc` | A working linker is required. On Windows, the GNU toolchain or MSVC build tools must be installed. |
| PHP | `php` | PHP 8+ |

When a command is missing, `check` returns a JSON error naming the language and the missing command. It does not silently skip the check.

## Custom toolchains

Create a JSON file and set `MINQUAL_TOOLCHAINS` to its absolute path. The schema is a map of language to command map:

```json
{
  "python": {
    "python": "/opt/python/bin/python3"
  },
  "javascript": {
    "node": "/usr/bin/node"
  },
  "typescript": {
    "node": "/usr/bin/node",
    "tsc": "/usr/lib/node_modules/typescript/lib/tsc.js"
  },
  "java": {
    "javac": "/opt/jdk-21/bin/javac",
    "java": "/opt/jdk-21/bin/java"
  },
  "csharp": {
    "dotnet": "/usr/share/dotnet/dotnet"
  },
  "c": {
    "gcc": "/usr/bin/gcc"
  },
  "cpp": {
    "g++": "/usr/bin/g++"
  },
  "go": {
    "go": "/usr/local/go/bin/go"
  },
  "rust": {
    "rustc": "/home/user/.cargo/bin/rustc"
  },
  "php": {
    "php": "/usr/bin/php"
  }
}
```

Only include the languages you need. `tsc` can be a `.js` file, a `.cmd` on Windows, or an executable.

Windows paths in JSON must escape backslashes:

```json
{
  "python": { "python": "C:\\Python313\\python.exe" },
  "typescript": {
    "node": "C:\\Program Files\\nodejs\\node.exe",
    "tsc": "C:\\Users\\you\\AppData\\Roaming\\npm\\node_modules\\typescript\\lib\\tsc.js"
  }
}
```

## Client configuration

The variable must reach the MCP server process:

- OpenCode: add `"env": {"MINQUAL_TOOLCHAINS": "/absolute/path/toolchains.json"}` inside the `minqual` server object.
- Claude Code: `claude mcp add --scope user -e MINQUAL_TOOLCHAINS=/absolute/path/toolchains.json minqual -- minqual-mcp`.
- Codex: `codex mcp add --env MINQUAL_TOOLCHAINS=/absolute/path/toolchains.json minqual -- minqual-mcp`.
- Antigravity: add `"env": {"MINQUAL_TOOLCHAINS": "/absolute/path/toolchains.json"}` inside the `minqual` server object.

Without the variable, MinQual falls back to `PATH`.

## Caches

MinQual writes build caches under the platform cache directory in a `minqual` folder. It uses a temporary workspace for each check and removes it afterward. Set `XDG_CACHE_HOME` or `LOCALAPPDATA` if you need a different cache location.
