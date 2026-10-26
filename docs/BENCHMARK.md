# Benchmark note

This note records the benchmark that shaped MinQual. It is a practical measurement, not a formal research paper.

## Setup

- Two tasks: `parse_duration` (bug fix with hidden edge cases) and `merge_intervals` (greenfield implementation with validation).
- Ten languages: Python, JavaScript, TypeScript, Java, C#, C, C++, Go, Rust, PHP.
- Three arms: baseline, skill, skill plus MCP.
- Two models: Muse Spark 1.3 Contributor and Muse Spark 1.2 Contributor, both through OpenCode Go.
- Two samples per cell, 240 runs total. The skill and MCP used the same prompts and model settings as baseline; only the skill text and the MCP tool differed.
- Hidden tests were never sent to the models or to the MCP.

The score was 70% hidden-test pass rate and 30% static quality. A separate metric counted the share of hidden cases that failed.

## Results

| Arm | Runs | Composite | Hidden failure rate | Build failures | Mean tool calls |
|---|---:|---:|---:|---:|---:|
| baseline | 80 | 94.21 | 6.42% | 1 | 0.00 |
| skill | 80 | 97.31 | 2.21% | 1 | 0.00 |
| skill + MCP | 80 | 96.86 | 2.83% | 1 | 2.45 |

- The skill cut hidden failures by 65.6%.
- The MCP cut hidden failures by 56.0%.
- Composite moved from 94.21 to 97.31 and 96.86, relative gains of 3.3% and 3.0%.

The composite could not grow 50% on this task set. With a baseline of 94.21, a perfect solution reaches only 100, which is a 6.1% relative gain. A 50% composite gain would require a baseline at or below 66.7. The benchmark tasks were already close to the models' ceiling.

## Per-language composite

| Language | baseline | skill | skill + MCP |
|---|---:|---:|---:|
| Python | 96.13 | 99.70 | 98.70 |
| JavaScript | 96.02 | 99.89 | 98.82 |
| TypeScript | 96.79 | 99.55 | 99.78 |
| Java | 95.04 | 97.30 | 97.14 |
| C# | 94.74 | 96.69 | 86.14 |
| C | 95.38 | 97.88 | 97.00 |
| C++ | 96.24 | 99.89 | 97.71 |
| Go | 84.50 | 89.26 | 99.55 |
| Rust | 94.40 | 96.69 | 97.03 |
| PHP | 92.90 | 96.30 | 96.70 |

## What worked

The clearest wins came from specification clauses that the baseline skipped:

- Python, JavaScript, TypeScript, C++, Go, and PHP merge tasks: the skill reduced hidden failures to zero in the tested cells.
- Go `parse_duration`: baseline and skill each had a build failure in one run; the MCP compiled both and passed all 30 cases.
- Java `merge_intervals`: the MCP wrote focused range cases and passed 19/19 in both samples, while baseline and skill stayed at 17/19.

## What did not work

- One C# `parse_duration` MCP run returned syntactically broken code after tool use. The final build failed and the run scored 11.4. This lowered the C# MCP average to 86.14.
- Some MCP runs missed the range cases that the skill alone caught. The MCP is not uniformly better than the skill.
- The skill without MCP was more stable overall: 2.21% hidden failures against 2.83% for the MCP.

## Harder probe

A separate Python-only probe used a checked 64-bit stack VM with memory, calls, jumps, overflow checks, truncated operands, and a step limit. The hidden set had 38 cases. Both models solved it 38/38 on the first attempt. The skill and MCP also passed 38/38, with no meaningful composite gain.

This supports the conclusion that the ceiling is the model's capability on well-specified tasks, not only the difficulty of the two main tasks.

## Limitations

- Two tasks, two samples per cell, and tests written by the benchmark author.
- The static score is a heuristic. The 70% hidden-test weight is the main signal.
- The benchmark harness and raw runs are not shipped in this repository.
- The MCP compiles and runs code locally. It has no network or filesystem sandbox. Use it with trusted code.
- Results depend on the model, API, and toolchain versions used at the time.
