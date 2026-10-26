# Rust quality reference

## Contract and errors

- Return `Result<T, E>` for validation and parsing. Do not use `unwrap`, `expect`, or `panic!` for user input.
- Use checked arithmetic or a wider type (`i128`) for intermediates that can overflow.
- Prefer `&str` and slices for read-only input.
- Keep ownership clear. A borrowed input should not be cloned unless the algorithm needs a copy.

## Common failure modes

- Release builds wrap on overflow by default; debug builds panic. Check explicitly.
- `sort()` mutates. Clone the input when the caller's data must stay unchanged.
- Byte slicing can split a UTF-8 character. Validate ASCII before byte indexing.
- `unwrap` hides the error path. Propagate or map the error.
- `usize` subtraction underflows and panics. Check before subtracting.
- Unsafe blocks need a documented invariant. Do not use them to silence the borrow checker.
- Warnings and `clippy` findings often expose a simpler correct version.

## Verification

- Compile with `rustc` or `cargo check` with warnings enabled.
- Run the provided test main.
- Test empty input, malformed input, overflow, and a mutation-sensitive input.
