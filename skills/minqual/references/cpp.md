# C++ quality reference

## Contract and errors

- Pass large or non-trivial inputs by `const` reference.
- Throw `std::invalid_argument` for invalid values and `std::overflow_error` for an exceeded range.
- Use RAII containers such as `std::vector` and `std::string`. Avoid raw `new`.
- Keep headers minimal and include what they use.

## Common failure modes

- Signed overflow is undefined. Check before multiplication or use a wider intermediate such as `__int128` where supported.
- `std::sort` mutates its input. Copy the container when the caller's data must stay unchanged.
- `std::regex` can match a later substring. Track the position and reject unmatched gaps.
- `std::stoll` throws on a bad value; catch or validate it.
- A comparator must be a strict weak ordering.
- Do not cast away `const`.
- Warnings often point to a real defect. Fix them.

## Verification

- Compile with `-std=c++20 -Wall -Wextra`.
- Run the provided test main.
- Test empty input, invalid ranges, overflow, and input mutation when relevant.
