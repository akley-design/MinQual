# MinQual

MinQual is a verification-first code-quality skill and MCP server for coding agents. It makes the agent check its own work in ten languages before saying the task is done.

[Русская версия](README-rus.md)

## What is inside

- **Skill**: a short quality gate, edge-case checklist, focused-test habit, and language references for Python, JavaScript, TypeScript, Java, C#, C, C++, Go, Rust, and PHP.
- **MCP server `minqual`**: one tool, `check`. It compiles supplied files, runs optional focused tests, and returns static findings. It also checks input limits, path safety, build-control files, and timeouts.
- **Benchmark note**: [docs/BENCHMARK.md](docs/BENCHMARK.md). In the 240-run benchmark, the skill reduced hidden-test failures by 65.6% and the MCP by 56.0%. The composite score was near its ceiling and grew 3.3% and 3.0%.

MinQual is not a full project build system. It is a small, deterministic feedback loop for the files the agent is about to return.

## Requirements

- Python 3.11 or newer.
- [uv](https://docs.astral.sh/uv/) or pipx for the MCP command.
- At least one language toolchain on `PATH` for the languages you use. See [docs/TOOLCHAINS.md](docs/TOOLCHAINS.md).

## Install

```bash
git clone https://github.com/akley-design/MinQual.git
cd MinQual
uv tool install .
```

Or install from GitHub directly:

```bash
uv tool install "git+https://github.com/akley-design/MinQual.git"
```

The command `minqual-mcp` must be on `PATH` in every client that launches the MCP server. Check it with `where minqual-mcp` on Windows or `command -v minqual-mcp` on macOS and Linux.

For development, use a checkout:

```bash
git clone https://github.com/akley-design/MinQual.git
cd MinQual
uv venv
uv pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Install the skill

Copy the skill folder into the location your client scans. The folder is `skills/minqual`.

| Client | User scope | Project scope |
|---|---|---|
| OpenCode | `~/.config/opencode/skills/minqual` | `.opencode/skills/minqual` |
| Claude Code | `~/.claude/skills/minqual` | `.claude/skills/minqual` |
| Codex | `~/.agents/skills/minqual` | `.agents/skills/minqual` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/minqual` | `.agents/skills/minqual` |
| Antigravity IDE | `~/.gemini/config/skills/minqual` | `.agents/skills/minqual` |

On macOS or Linux:

```bash
mkdir -p ~/.config/opencode/skills ~/.claude/skills ~/.agents/skills ~/.gemini/antigravity-cli/skills
cp -r skills/minqual ~/.config/opencode/skills/
cp -r skills/minqual ~/.claude/skills/
cp -r skills/minqual ~/.agents/skills/
cp -r skills/minqual ~/.gemini/antigravity-cli/skills/
```

On Windows PowerShell:

```powershell
$skill = ".\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.config\opencode\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.claude\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.agents\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.gemini\antigravity-cli\skills\minqual"
```

Restart the client, or open a new session, so it reloads the skill directory.

## Connect the MCP

The server is a local stdio server. The command is `minqual-mcp`; it takes no arguments. All snippets below assume the command is on `PATH`.

### OpenCode

Edit `~/.config/opencode/opencode.jsonc` and add a local server under `mcp`:

```jsonc
{
  "mcp": {
    "minqual": {
      "type": "local",
      "command": ["minqual-mcp"],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

Verify:

```bash
opencode mcp list
```

### Claude Code

Add a user-scoped stdio server:

```bash
claude mcp add --scope user minqual -- minqual-mcp
claude mcp list
```

For a project-scoped server, add `.mcp.json` at the repository root:

```json
{
  "mcpServers": {
    "minqual": {
      "type": "stdio",
      "command": "minqual-mcp",
      "args": []
    }
  }
}
```

Approve the project server when Claude Code asks.

### Codex

Add the server with the CLI:

```bash
codex mcp add minqual -- minqual-mcp
codex mcp list
```

Codex writes a `mcp_servers` table to `~/.codex/config.toml`:

```toml
[mcp_servers.minqual]
command = "minqual-mcp"
args = []
```

Codex looks for skills in `~/.agents/skills` and `.agents/skills`. After the skill is installed, invoke it with `$minqual` or select it in the skill picker, depending on your Codex version.

### Google Antigravity CLI

Antigravity reads local servers from `mcpServers`. It does not use a `type` field.

Global config, `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "minqual": {
      "command": "minqual-mcp",
      "args": []
    }
  }
}
```

Workspace config, `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "minqual": {
      "command": "minqual-mcp",
      "args": []
    }
  }
}
```

Use the `/mcp` command in Antigravity CLI to open the MCP manager and reload the server.

## Toolchains

MinQual auto-detects toolchains on `PATH`:

| Language | Command |
|---|---|
| Python | `python` |
| JavaScript | `node` |
| TypeScript | `node` and `tsc` |
| Java | `javac` and `java` (JDK 17+) |
| C# | `dotnet` (.NET SDK 8+) |
| C | `gcc` or `cc` |
| C++ | `g++` or `c++` |
| Go | `go` |
| Rust | `rustc` with a working linker |
| PHP | `php` |

If a toolchain lives outside `PATH`, create a toolchains JSON file and point `MINQUAL_TOOLCHAINS` at it:

```json
{
  "python": { "python": "/opt/python/bin/python3" },
  "javascript": { "node": "/usr/bin/node" },
  "typescript": { "node": "/usr/bin/node", "tsc": "/usr/lib/node_modules/typescript/lib/tsc.js" }
}
```

Pass the variable through the client:

- OpenCode: add `"env": {"MINQUAL_TOOLCHAINS": "/absolute/path/toolchains.json"}` inside the `minqual` server object.
- Claude Code: `claude mcp add --scope user -e MINQUAL_TOOLCHAINS=/absolute/path/toolchains.json minqual -- minqual-mcp`.
- Codex: `codex mcp add --env MINQUAL_TOOLCHAINS=/absolute/path/toolchains.json minqual -- minqual-mcp`.
- Antigravity: add `"env": {"MINQUAL_TOOLCHAINS": "/absolute/path/toolchains.json"}` inside the `minqual` server object.

The full schema and Windows notes are in [docs/TOOLCHAINS.md](docs/TOOLCHAINS.md).

## Use

Ask the agent to do a code task. The skill description triggers on writing, fixing, reviewing, or refactoring code. If the MCP is connected, the agent can call `check` with the complete solution files and focused tests before it answers.

Example prompt:

```text
Use MinQual to implement the CSV parser in src/parser.py, then check the result with the minqual tool before finishing.
```

The `check` tool accepts:

- `language`: one of the ten supported languages or an alias such as `py`, `js`, `ts`, or `cpp`.
- `files`: an object mapping relative paths to complete file contents.
- `tests`: optional files for a self-contained runner and `cases.tsv`. The skill knows the convention and can create focused cases.
- `mode`: `full` compiles and runs the supplied tests; `static` only returns source heuristics.

Limits: 20 files, 200 KB total, build and test timeouts, and relative paths inside a temporary workspace. Build-control files such as `*.csproj` and `go.mod` are rejected because the runner generates its own.

For full repository test suites, use the agent's native test and build tools. MinQual is the final gate for the files the agent is about to return.

## Safety

MinQual compiles and runs code on your machine. It uses a temporary directory, a minimal environment, timeouts, size limits, and path validation. It does not provide a network or filesystem sandbox. Run only code you trust.

## Benchmark

The [benchmark note](docs/BENCHMARK.md) documents 240 runs across ten languages and two tasks with Muse Spark 1.2 and 1.3 Contributor. The skill cut the hidden-test failure rate from 6.42% to 2.21%, a 65.6% reduction. The MCP cut it to 2.83%, a 56.0% reduction. Composite scores were near the ceiling: 94.21 baseline, 97.31 with the skill, and 96.86 with the MCP.

The benchmark also found a real MCP regression: one C# final answer was syntactically broken after tool use. The skill was more stable than the MCP. Use the MCP as an optional feedback loop, not as a guarantee.

## License

MIT. See [LICENSE](LICENSE).
