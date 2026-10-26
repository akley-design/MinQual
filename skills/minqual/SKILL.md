---
name: minqual
description: MinQual quality gate. Use when writing, fixing, reviewing, or refactoring code in Python, JavaScript, TypeScript, Java, C#, C, C++, Go, Rust, or PHP. Enforces a verify-before-finish workflow: contract, edge cases, explicit error paths, build, tests, static findings, and a final self-review. Not for prose, documentation, or presentation work.
license: MIT
metadata:
  version: "1.0.0"
---

# MinQual quality gate

## When to use

Load this skill for any code generation, bug fix, review, or refactor in the supported languages. It applies to small functions and full files. It is not needed for prose or non-code explanations.

## Non-negotiables

- Read the task contract before writing code. Note the exact function name, signature, output type, error convention, and files you must change.
- Validate at the boundary. Never assume input is present, well formed, or inside the documented range.
- Fail loudly on invalid input. Use the language's normal argument or value error, or its documented error return. Never return a plausible default after an error.
- Handle empty, single, boundary, malformed, duplicate, out-of-order, negative, zero, overflowing, whitespace, and case variations when the contract allows them.
- Use exact integer arithmetic for exact results. Check for overflow before multiplying or adding. Do not route exact integer work through floating point.
- Do not mutate the caller's input unless the contract requires it. Copy before sorting.
- Do not suppress diagnostics to make a build pass. No blanket ignore, empty catch, bare except, `unwrap` without a checked reason, or disabled warning.
- Do not add a fallback that hides a defect. Fix the cause.
- Keep the smallest correct design. No placeholder code, no unused scaffolding, no dead code.
- Tests are evidence. A build alone is not proof that the behavior is correct.

## Verification workflow

1. Restate the contract in one or two lines. Identify the required source files and tests.
2. List the concrete edge cases from the contract. For each one, decide the expected result or error.
3. Read the visible tests and examples. Do not change them. Infer the caller's expected behavior.
4. Implement the smallest complete version in the required files.
5. Verify before answering:
   - If the `minqual` MCP tool `check` is available, call it with the complete solution files and the visible test files. Use it again after fixes.
   - If the visible suite does not cover a spec clause, write focused tests for that clause. With the MCP, copy the provided runner without editing it, add cases, and run the copy through `check`.
   - Fix every build error, every failing case, and every high-severity finding. Re-run after each substantive change.
   - If the tool is not available, run the language's build and tests directly.
   - Do not claim that tests pass if you did not run them.
6. Self-review the final code against the checklist below.
7. Return the files in the exact format the task requests. Do not include test modifications unless asked.

## Universal edge cases

- Empty input, a single element, and the smallest valid value.
- Zero, negative values, and the largest documented value.
- Overflow at intermediate steps, not only at the final result.
- Leading, trailing, repeated, and missing separators or whitespace.
- Case differences and malformed characters.
- Unknown units, trailing garbage, and partial matches.
- Duplicate entries, unsorted entries, nested or touching ranges, and equal boundaries.
- Invalid ordering, such as a start greater than an end.
- Input mutation, especially after sorting or merging.
- The required error type or error return for every invalid path.
- Resource cleanup on success and on failure.

## Final self-review

- Does every required behavior have a code path and a test, including clauses absent from the visible examples?
- Are invalid inputs rejected instead of silently normalized?
- Is the arithmetic exact and safe at the boundaries?
- Is the input left untouched when the contract says so?
- Are exceptions specific and useful?
- Did I remove every temporary shortcut, TODO, and debug print?
- Did the final build and the visible tests run cleanly?
- Do the returned files use the required paths and complete contents?

## MCP feedback

When the MinQual MCP is available, `check(language, files, tests, mode="full")` compiles the supplied files and runs the supplied visible tests in a temp directory. Pass complete file contents, keep paths relative, and pass the visible tests exactly as provided. Read the JSON: `build_ok`, `passed/total`, failing case names, compiler output, and static findings. Fix the causes, then call `check` again. Never pass hidden tests or credentials, and never treat the absence of a tool call as a passing test run.

## References

- [Python](references/python.md)
- [JavaScript](references/javascript.md)
- [TypeScript](references/typescript.md)
- [Java](references/java.md)
- [C#](references/csharp.md)
- [C](references/c.md)
- [C++](references/cpp.md)
- [Go](references/go.md)
- [Rust](references/rust.md)
- [PHP](references/php.md)
