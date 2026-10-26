# MinQual

MinQual: skill и MCP-сервер для проверки качества кода. Он заставляет агента проверять свою работу до того, как он скажет, что задача готова. Поддерживаются десять языков.

[English version](README.md)

## Что внутри

- **Skill**: короткий quality gate, чек-лист граничных случаев, привычка писать focused-тесты и языковые reference для Python, JavaScript, TypeScript, Java, C#, C, C++, Go, Rust и PHP.
- **MCP-сервер `minqual`**: один инструмент `check`. Он собирает переданные файлы, запускает необязательные focused-тесты и возвращает статические замечания. Он также проверяет лимиты, безопасность путей, build-control файлы и таймауты.
- **Отчёт о замере**: [docs/BENCHMARK.md](docs/BENCHMARK.md). В 240 запусках skill сократил долю проваленных скрытых кейсов на 65.6%, MCP на 56.0%. Composite был у потолка и вырос на 3.3% и 3.0%.

MinQual не заменяет полноценную систему сборки проекта. Это небольшой детерминированный feedback loop для файлов, которые агент собирается вернуть.

## Требования

- Python 3.11 или новее.
- [uv](https://docs.astral.sh/uv/) или pipx для команды MCP.
- Хотя бы один языковой тулчейн в `PATH` для языков, которые вы используете. Подробности в [docs/TOOLCHAINS.md](docs/TOOLCHAINS.md).

## Установка

```bash
git clone https://github.com/akley-design/MinQual.git
cd MinQual
uv tool install .
```

Или сразу с GitHub:

```bash
uv tool install "git+https://github.com/akley-design/MinQual.git"
```

Команда `minqual-mcp` должна быть в `PATH` у каждого клиента, который запускает MCP-сервер. Проверка: `where minqual-mcp` в Windows или `command -v minqual-mcp` в macOS и Linux.

Для разработки:

```bash
git clone https://github.com/akley-design/MinQual.git
cd MinQual
uv venv
uv pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Установка skill

Скопируйте папку `skills/minqual` в каталог, который сканирует ваш клиент.

| Клиент | Пользовательский каталог | Каталог проекта |
|---|---|---|
| OpenCode | `~/.config/opencode/skills/minqual` | `.opencode/skills/minqual` |
| Claude Code | `~/.claude/skills/minqual` | `.claude/skills/minqual` |
| Codex | `~/.agents/skills/minqual` | `.agents/skills/minqual` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/minqual` | `.agents/skills/minqual` |
| Antigravity IDE | `~/.gemini/config/skills/minqual` | `.agents/skills/minqual` |

macOS или Linux:

```bash
mkdir -p ~/.config/opencode/skills ~/.claude/skills ~/.agents/skills ~/.gemini/antigravity-cli/skills
cp -r skills/minqual ~/.config/opencode/skills/
cp -r skills/minqual ~/.claude/skills/
cp -r skills/minqual ~/.agents/skills/
cp -r skills/minqual ~/.gemini/antigravity-cli/skills/
```

Windows PowerShell:

```powershell
$skill = ".\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.config\opencode\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.claude\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.agents\skills\minqual"
Copy-Item -Recurse -Force $skill "$HOME\.gemini\antigravity-cli\skills\minqual"
```

Перезапустите клиент или откройте новую сессию, чтобы он перечитал каталог skills.

## Подключение MCP

Сервер локальный, транспорт stdio. Команда `minqual-mcp` без аргументов. Все примеры ниже предполагают, что команда уже в `PATH`.

### OpenCode

Отредактируйте `~/.config/opencode/opencode.jsonc` и добавьте локальный сервер в `mcp`:

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

Проверка:

```bash
opencode mcp list
```

### Claude Code

Добавьте пользовательский stdio-сервер:

```bash
claude mcp add --scope user minqual -- minqual-mcp
claude mcp list
```

Для сервера уровня проекта добавьте `.mcp.json` в корень репозитория:

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

Подтвердите project-сервер, когда Claude Code спросит.

### Codex

Добавьте сервер командой:

```bash
codex mcp add minqual -- minqual-mcp
codex mcp list
```

Codex запишет таблицу `mcp_servers` в `~/.codex/config.toml`:

```toml
[mcp_servers.minqual]
command = "minqual-mcp"
args = []
```

Codex ищет skills в `~/.agents/skills` и `.agents/skills`. После установки вызывайте `$minqual` или выберите skill в picker, в зависимости от версии Codex.

### Google Antigravity CLI

Antigravity читает локальные серверы из `mcpServers`. Поле `type` не используется.

Глобальный конфиг, `~/.gemini/config/mcp_config.json`:

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

Конфиг workspace, `.agents/mcp_config.json`:

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

В Antigravity CLI используйте `/mcp`, чтобы открыть менеджер MCP и перезагрузить сервер.

## Тулчейны

MinQual сам находит тулчейны в `PATH`:

| Язык | Команда |
|---|---|
| Python | `python` |
| JavaScript | `node` |
| TypeScript | `node` и `tsc` |
| Java | `javac` и `java` (JDK 17+) |
| C# | `dotnet` (.NET SDK 8+) |
| C | `gcc` или `cc` |
| C++ | `g++` или `c++` |
| Go | `go` |
| Rust | `rustc` с рабочим линкером |
| PHP | `php` |

Если тулчейн лежит вне `PATH`, создайте JSON и укажите на него `MINQUAL_TOOLCHAINS`:

```json
{
  "python": { "python": "/opt/python/bin/python3" },
  "javascript": { "node": "/usr/bin/node" },
  "typescript": { "node": "/usr/bin/node", "tsc": "/usr/lib/node_modules/typescript/lib/tsc.js" }
}
```

Передача переменной в клиент:

- OpenCode: добавьте `"env": {"MINQUAL_TOOLCHAINS": "/absolute/path/toolchains.json"}` в объект сервера `minqual`.
- Claude Code: `claude mcp add --scope user -e MINQUAL_TOOLCHAINS=/absolute/path/toolchains.json minqual -- minqual-mcp`.
- Codex: `codex mcp add --env MINQUAL_TOOLCHAINS=/absolute/path/toolchains.json minqual -- minqual-mcp`.
- Antigravity: добавьте `"env": {"MINQUAL_TOOLCHAINS": "/absolute/path/toolchains.json"}` в объект сервера `minqual`.

Полная схема и заметки по Windows в [docs/TOOLCHAINS.md](docs/TOOLCHAINS.md).

## Использование

Попросите агента выполнить задачу по коду. Skill срабатывает на написание, исправление, review или рефакторинг. Если MCP подключён, агент может вызвать `check` с полными файлами решения и focused-тестами до финального ответа.

Пример запроса:

```text
Используй MinQual, чтобы реализовать CSV-парсер в src/parser.py, и проверь результат через инструмент minqual перед завершением.
```

Инструмент `check` принимает:

- `language`: один из десяти языков или alias вроде `py`, `js`, `ts`, `cpp`.
- `files`: объект относительный путь -> полное содержимое файла.
- `tests`: необязательные файлы для самодостаточного runner и `cases.tsv`. Skill знает формат и может создать focused-кейсы.
- `mode`: `full` собирает и запускает переданные тесты; `static` возвращает только статические эвристики.

Лимиты: 20 файлов, 200 КБ, таймауты сборки и тестов, относительные пути внутри временного каталога. Build-control файлы вроде `*.csproj` и `go.mod` отклоняются, потому что runner создаёт свои.

Для полного набора тестов репозитория используйте штатные build и test команды агента. MinQual это финальный gate для файлов, которые агент собирается вернуть.

## Безопасность

MinQual собирает и запускает код на вашей машине. Он использует временный каталог, минимальное окружение, таймауты, лимиты размера и проверку путей. Сетевой и файловой песочницы нет. Запускайте только доверенный код.

## Замер

В [docs/BENCHMARK.md](docs/BENCHMARK.md) описаны 240 запусков на десяти языках и двух задачах с Muse Spark 1.2 и 1.3 Contributor. Skill сократил долю проваленных скрытых кейсов с 6.42% до 2.21%, то есть на 65.6%. MCP сократил её до 2.83%, на 56.0%. Composite был у потолка: 94.21 у baseline, 97.31 у skill и 96.86 у MCP.

Замер также нашёл реальную регрессию MCP: один финальный ответ на C# после tool use был синтаксически сломан. Skill оказался стабильнее MCP. Используйте MCP как необязательный feedback loop, а не как гарантию.

## Лицензия

MIT. См. [LICENSE](LICENSE).
