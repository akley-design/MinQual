from __future__ import annotations

import unittest

from minqual.checks import InputError, run_tests, validate_files
from minqual.static import analyze

SOLUTION = "def add(a: int, b: int) -> int:\n    return a + b\n"
HARNESS = """from solution import add

ok = add(2, 3) == 5
print("CASE add PASS" if ok else "CASE add FAIL")
print(f"TOTAL 1 PASSED {1 if ok else 0}")
"""
CASES = "add\t2,3\t5\t0\t0\n"


class RunnerTests(unittest.TestCase):
    def test_python_reference_passes(self):
        result = run_tests("python", {"solution.py": SOLUTION}, {"run_cases.py": HARNESS, "cases.tsv": CASES})
        self.assertTrue(result["build_ok"], result["build_output"])
        self.assertEqual((result["passed"], result["total"]), (1, 1), result["output"])

    def test_static_analysis_returns_score(self):
        result = analyze("python", {"solution.py": SOLUTION})
        self.assertGreater(result["score"], 0)
        self.assertTrue(result["build_skipped"])

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(InputError):
            run_tests("python", {"../escape.py": "print('x')"}, {})

    def test_build_control_file_is_rejected(self):
        with self.assertRaises(InputError):
            run_tests("csharp", {"Task.csproj": "<Project />"}, {})

    def test_missing_case_result_fails(self):
        result = run_tests("python", {"solution.py": SOLUTION}, {
            "run_cases.py": "print('TOTAL 1 PASSED 0')\n",
            "cases.tsv": CASES,
        })
        self.assertEqual(result["status"], "tests_failed")
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["case_errors"], ["missing test case result: 'add'"])

    def test_unknown_case_result_fails(self):
        result = run_tests("python", {"solution.py": SOLUTION}, {
            "run_cases.py": "print('CASE other PASS')\n",
            "cases.tsv": CASES,
        })
        self.assertEqual(result["status"], "tests_failed")
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["case_errors"], [
            "unexpected test case result: 'other'",
            "missing test case result: 'add'",
        ])

    def test_duplicate_case_result_fails(self):
        result = run_tests("python", {"solution.py": SOLUTION}, {
            "run_cases.py": "print('CASE add PASS')\nprint('CASE add PASS')\n",
            "cases.tsv": CASES,
        })
        self.assertEqual(result["status"], "tests_failed")
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["case_errors"], ["duplicate test case result: 'add'"])

    def test_duplicate_expected_case_name_is_rejected(self):
        with self.assertRaises(InputError):
            run_tests("python", {"solution.py": SOLUTION}, {
                "run_cases.py": HARNESS,
                "cases.tsv": CASES + CASES,
            })

    def test_file_count_limit_is_enforced(self):
        with self.assertRaises(InputError):
            validate_files({f"{index}.py": "" for index in range(21)})

    def test_file_size_limit_is_enforced(self):
        with self.assertRaises(InputError):
            validate_files({"large.py": "x" * 100_001})

    def test_total_size_limit_is_enforced(self):
        with self.assertRaises(InputError):
            validate_files({f"{index}.py": "x" * 50_001 for index in range(4)})

    def test_absolute_and_windows_paths_are_rejected(self):
        for name in ("/absolute.py", "C:\\outside.py"):
            with self.subTest(name=name), self.assertRaises(InputError):
                validate_files({name: "print('x')"})


if __name__ == "__main__":
    unittest.main()
