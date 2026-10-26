# C# quality reference

## Contract and errors

- Use `long` for values that can exceed 32 bits.
- Throw `ArgumentException` or `ArgumentNullException` for invalid arguments.
- Keep nullable annotations honest. Do not suppress nullable warnings to make the build quiet.
- Use `char.IsWhiteSpace` and `Trim` for user input.

## Common failure modes

- `Regex.Match` can match later in the string. Check `match.Index` against the current position when parsing a sequence.
- `long.Parse` throws; `long.TryParse` requires a branch on the result.
- `result[^1]` is the last element; check `Count` or `Length` first.
- Sorting an array mutates it. Clone rows with `(int[])row.Clone()`.
- `Array.Empty<int[]>()` returns an immutable empty array; do not append to it.
- An empty `catch` block hides a failure.
- LINQ is fine, but do not use it to avoid writing a clear boundary check.
- `Process.Start` and dynamic code are unsafe shortcuts in ordinary code.

## Verification

- Build: `dotnet build -c Release` with nullable enabled.
- Run the provided runner.
- Test empty input, invalid ranges, overflow, and input mutation when relevant.
