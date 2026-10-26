# JavaScript quality reference

## Contract and errors

- Use `===` and `!==`. Do not rely on implicit coercion.
- Throw `Error` or a specific subclass for invalid input. Do not return `null` to signal an error unless the contract says so.
- Validate runtime types with `typeof`, `Array.isArray`, and `Number.isInteger`. TypeScript types do not protect JavaScript callers.

## Common failure modes

- `parseInt` and `Number` accept prefixes, whitespace, or exponents. Validate the entire token before conversion.
- Numbers above `Number.MAX_SAFE_INTEGER` lose precision. Check the contract's limit before arithmetic.
- A global or non-sticky regex can skip unmatched text. Use a sticky or anchored match and verify the position after every match.
- `sort()` mutates. Copy with `[...items]` or `items.slice()` when needed.
- An empty `catch {}` hides every bug. Handle or rethrow.
- `as any` and `@ts-ignore` silence useful errors. Remove them.
- Floating point arithmetic is not exact for decimal values.

## Verification

- Syntax: `node --check solution.mjs`.
- Tests: `node --test`.
- Include a boundary case, a malformed case, and an input-mutation case when relevant.
