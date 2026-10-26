# PHP quality reference

## Contract and errors

- Add `declare(strict_types=1);` to source files.
- Throw `InvalidArgumentException` for invalid arguments. Do not return `null` or `0` to signal failure.
- Use `intdiv` for integer division. PHP integers are 64-bit on this platform, but check the contract's limit.
- Use `preg_match` with `\G` and an offset for sequential parsing. Check the full input.

## Common failure modes

- `(int)` casts accept valid prefixes and hide malformed values.
- `preg_match_all` skips unmatched gaps. Validate the whole string.
- `trim` removes only surrounding whitespace, not internal or garbage text.
- Arrays are value types in PHP; pass-by-value already protects the caller. Do not rely on that as a substitute for a correct algorithm.
- `usort` mutates the array you give it.
- `@` suppresses errors. Do not use it.
- `eval`, `exec`, `shell_exec`, and `system` are unsafe shortcuts in ordinary code.
- A nested array is not a tuple by contract. Validate the shape and the integer types.

## Verification

- Syntax: `php -l solution.php`.
- Run the provided test script.
- Test empty input, malformed input, overflow, and a case with nested values.
