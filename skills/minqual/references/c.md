# C quality reference

## Contract and errors

- Use fixed-width types from `<stdint.h>` when the range matters.
- Return a documented error code and leave the output untouched on failure.
- Use `const` pointers for input that must not change.
- Check every allocation and free every owned allocation, including error paths.

## Common failure modes

- Signed integer overflow is undefined behavior. Check before multiplying or adding.
- `atoi` and `atof` hide invalid suffixes. Use `strtol` or `sscanf` and check the consumed length.
- `strtok` collapses empty fields. Write a field splitter when empty fields matter.
- `strcpy`, `strcat`, `sprintf`, and `gets` are unsafe. Use bounded operations.
- A `const` pointer does not prevent a cast that violates the contract. Do not cast it away.
- `qsort` mutates its input. Sort a copy when the caller's array must stay unchanged.
- A missing newline or a fixed-size input buffer can silently truncate data.
- Compile with warnings enabled and fix them instead of ignoring them.

## Verification

- Compile with `-std=c17 -Wall -Wextra`.
- Run the provided test main.
- Test empty input, malformed input, maximum values, and allocation/error paths.
