# 11: SWE-bench-style repository task

## What this dataset is for

A real bug report in a real repository, frozen at the commit where the bug existed, with the maintainer's own tests that prove the fix. The model must write a patch that makes the new tests pass without breaking the old ones; nobody judges the patch by reading it. The question an instance answers is: *can the agent fix what the issue describes, in this codebase, without regressions?* As an evaluation the metric is the share of instances resolved; for RL the same check is the reward.

## The example

`instance.json` is the record; `repo/` is the tiny `querykit` package at `base_commit`; `gold.patch` and `test.patch` are the same text as the record's `patch` and `test_patch` fields; `candidate_wrong.patch` is a plausible model patch; `verify_instance.py` is the grader. The record, trimmed:

```json
{"instance_id": "acme__querykit-142", "repo": "acme/querykit",
 "base_commit": "748046bac40afa53861ed2014f8961cc802e3137",
 "problem_statement": "parse_query drops repeated keys\n\n`parse_query(\"tag=a&tag=b\")` returns `{\"tag\": \"b\"}`. The README says a key that appears more than once maps to a list of its values, in order, so I expected `{\"tag\": [\"a\", \"b\"]}`. Keys that appear once should stay plain strings.",
 "hints_text": "Maintainer: keep single keys as strings; only repeated keys become lists.",
 "created_at": "2026-09-02T14:05:11Z", "version": "0.4",
 "environment_setup_commit": "748046bac40afa53861ed2014f8961cc802e3137",
 "patch": "diff --git a/querykit/parse.py b/querykit/parse.py\n... (the gold fix, 11 lines changed)",
 "test_patch": "diff --git a/tests/test_parse.py b/tests/test_parse.py\n...\n+def test_repeated_keys_are_kept():\n+    assert parse_query(\"tag=a&tag=b&x=1&tag=c\") == {\"tag\": [\"a\", \"b\", \"c\"], \"x\": \"1\"}\n",
 "FAIL_TO_PASS": ["tests/test_parse.py::test_repeated_keys_are_kept"],
 "PASS_TO_PASS": ["tests/test_parse.py::test_simple_pairs", "tests/test_parse.py::test_empty_string", "tests/test_parse.py::test_plus_and_percent_decoding"]}
```

| Field | What it is and why it exists |
|---|---|
| `instance_id` | owner, repository and pull-request number: a stable id |
| `repo`, `base_commit` | the exact code the model starts from |
| `problem_statement` | the issue title and body: the task as a user reported it |
| `hints_text` | comments on the issue before the fix; showing them is an evaluation setting |
| `created_at` | when the fix's pull request was opened; dates the task for contamination checks |
| `version`, `environment_setup_commit` | a reproducible install |
| `patch` | the gold fix minus tests: proves solvability; never shown to the model |
| `test_patch` | the fix's tests, applied before grading; never shown to the model |
| `FAIL_TO_PASS` | tests that fail before the fix and must pass after |
| `PASS_TO_PASS` | tests that must keep passing: regression protection |

## How the model uses it

The model receives the repository at `base_commit` and the problem statement (optionally the hints) and produces a patch. The grader `verify_instance.grade(instance, candidate_patch)` rebuilds the repository from `repo/` with a deterministic author, committer and date, so the commit hash must equal `base_commit`; applies `test_patch`; confirms that every FAIL_TO_PASS test fails and every PASS_TO_PASS test passes before any fix (otherwise the instance is broken); applies the candidate patch; and reruns both lists. The instance is **resolved** only if every listed test passes. It needs `git` and `pytest`. From the lab root:

```bash
python3 11-swe-task/verify_instance.py                              # the gold patch
python3 11-swe-task/verify_instance.py 11-swe-task/candidate_wrong.patch
```

```text
PASS tests/test_parse.py::test_repeated_keys_are_kept
PASS tests/test_parse.py::test_simple_pairs
PASS tests/test_parse.py::test_empty_string
PASS tests/test_parse.py::test_plus_and_percent_decoding
resolved: True
```

```text
FAIL tests/test_parse.py::test_repeated_keys_are_kept
FAIL tests/test_parse.py::test_simple_pairs
PASS tests/test_parse.py::test_empty_string
FAIL tests/test_parse.py::test_plus_and_percent_decoding
resolved: False
```

The wrong patch handles the issue's literal example, but its `defaultdict(list)` makes every value a list, so `a=1&b=two` returns `{"a": ["1"], "b": ["two"]}`. Two PASS_TO_PASS tests break, and so does the FAIL_TO_PASS test, which expects `"x": "1"` to stay a string, as the hint said; only the empty-string test survives. Three failures, not resolved: a diff a hurried reviewer might have approved. For RL, resolved is the reward, sometimes with partial credit per test.

## How it is produced and checked

Mine merged pull requests that reference an issue and change tests; split each into fix and tests; build the environment at the right version; run the tests before and after to derive the two lists; then have engineers confirm the problem statement is specific enough and the tests fair (SWE-bench Verified kept 500 of 2,294 instances after that screen).

`validate_all.py` check **11 SWE-bench-style instance** asserts: all twelve SWE-bench fields are present; every file the test patch touches is under `tests/` and the gold patch touches none; every FAIL_TO_PASS test name appears in the test patch; then, if `git` and `pytest` are available, `grade()` resolves the gold patch and fails the wrong one. Without them it reports SKIP with the static checks passed; with them it prints `gold patch resolves; wrong patch fails ['test_repeated_keys_are_kept', 'test_simple_pairs', 'test_plus_and_percent_decoding']`. Delivery acceptance adds: no flaky tests over repeated runs, and alternative valid fixes, written by a second engineer, that pass.

## What goes wrong

- **Overly strict tests** that reject valid designs, the commonest defect found in audits of public sets; here "single keys stay strings" is fair only because the README, the issue and the hint all say so.
- **Underspecified issues** whose tests check behaviour the issue never mentions; **incomplete PASS_TO_PASS lists** that let regressions through.
- **Leakage**: gold patches or test names in the prompt, or the instance in training data, which is the central risk when issues, fixes and tests are public; `created_at` lets you keep only tasks newer than a model's training cutoff.

## Related

Chapter 26d.12 (SWE-bench Verified's screening numbers, SWE-bench Pro, SWE-Gym, SWE-rebench, the February 2026 audit). Siblings: `10-terminal-task/` (a system instead of a repository), `12-agentic-gym/` (state-based grading of a different kind), `06-eval/` (contamination checks and release rules), `05-rlvr/` (unit tests as reward).
