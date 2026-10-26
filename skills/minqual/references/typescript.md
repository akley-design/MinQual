# TypeScript quality reference

## Contract and errors

- Keep `strict` enabled. Prefer `unknown` over `any` at boundaries.
- Validate runtime data. A type assertion does not validate anything.
- Throw `Error` for invalid values and document the expected error.
- Use `readonly` for inputs that must not be mutated.

## Common failure modes

- `as SomeType`, `as any`, and `@ts-ignore` hide errors. Use a type guard or an explicit check.
- Array indexing may be out of bounds. Check the length before reading a position.
- `Number` is a double. Integers above `Number.MAX_SAFE_INTEGER` are not exact.
- An unanchored regex can accept a valid prefix and ignore garbage. Check the match index and the remaining input.
- Optional properties and nullable values need an explicit branch.
- A copied array is shallow. Deep-copy nested pairs when the code mutates them.

## Verification

- Type check: `tsc --strict --noEmit`.
- Run the compiled tests.
- Add a case for a malformed value, a boundary number, and an input that must not change.
