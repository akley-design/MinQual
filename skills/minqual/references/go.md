# Go quality reference

## Contract and errors

- Return `(Value, error)` for inputs that can fail. Do not use `panic` for ordinary validation.
- Use `int64` when the contract has a wide numeric range.
- Check every error. Do not discard one with `_`.
- Use `strconv.ParseInt` with an explicit bit size rather than `Atoi` when the range matters.

## Common failure modes

- Slices share their backing array. Copy with `append([]T(nil), input...)` before sorting or mutating.
- `sort.Slice` mutates the slice in place.
- Integer overflow wraps silently. Check before multiplication and addition.
- A regexp `FindAllStringSubmatch` ignores gaps. Validate the whole string or use indices.
- `strings.TrimSpace` does not validate the interior.
- `defer` runs at function return, not at block exit. Keep cleanup close to acquisition.
- Formatting drift is easy to spot with `gofmt -l`.

## Verification

- Build: `go build ./...`.
- Vet: `go vet ./...`.
- Run the provided test main.
- Test empty input, invalid ranges, overflow, and input mutation when relevant.
