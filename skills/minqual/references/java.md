# Java quality reference

## Contract and errors

- Use `long` when intermediate values can exceed the `int` range.
- Throw `IllegalArgumentException` for invalid arguments. Do not catch it and return a default.
- Use `String.strip()` for input from users. `trim()` handles only ASCII control spaces.
- Avoid checked exceptions for ordinary validation unless the contract requires them.

## Common failure modes

- Integer multiplication can overflow before you check the result. Check the operands or use a wider type.
- A `Matcher` with `find()` skips unmatched text. Use `region()` with `lookingAt()` or anchor the pattern.
- Sorting an input array mutates it. Clone each row with `row.clone()` before sorting.
- `Arrays.sort` on `int[][]` does not sort rows by value. Provide a `Comparator`.
- An empty catch block hides a defect. `printStackTrace` alone is not error handling.
- `new int[0][]` is a valid empty result; `null` usually is not.
- Suppressing warnings to pass a build is not a fix.

## Verification

- Compile with `javac -Xlint:all`.
- Run the provided `RunCases` class.
- Test negative values, overflow, empty input, and input mutation when relevant.
