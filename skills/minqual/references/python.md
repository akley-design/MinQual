# Python quality reference

## Contract and errors

- Use type hints on public functions. Raise `ValueError` for an invalid value and `TypeError` for a wrong type.
- Do not return `None` or `0` to signal an error unless the contract says so.
- Catch only exceptions you can handle. Never use a bare `except:` or `except Exception: pass`.

## Common failure modes

- `re.findall` ignores unmatched text. Anchor the whole input or advance a matcher and reject any gap.
- `str.strip()` removes surrounding whitespace, not internal whitespace. Decide which is allowed.
- Floats lose exactness. Use integers or `Decimal` for exact arithmetic.
- Mutable default arguments are shared across calls.
- `sort()` mutates. Sort a copy when the caller's list must stay unchanged.
- Integer size is unbounded, but the contract may still impose a limit. Check it explicitly.
- A regex such as `\d+` accepts Unicode digits. Use `re.ASCII` when the contract means ASCII digits.

## Verification

- Compile: `python -m py_compile solution.py`.
- Tests: `python -m unittest` or the provided runner.
- Lint: `ruff check`.
- Add a case for empty input, a case for malformed input, a boundary case, and a no-mutation case when relevant.
