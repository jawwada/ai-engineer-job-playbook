# 06: Evaluation set and scorers

## What this dataset is for

The final exam: written by someone other than the student, locked away and never used for studying. Each item carries its own marking scheme (run the query on fixture databases, run the tests, apply a rubric), and the result is a pass rate with an error bar, broken down by slice, that decides whether a model ships. The question this folder answers is: *how good is the model, with what uncertainty, and can we trust the number?*

## The example

`eval_items.jsonl` holds three items with three scorer types; `eval_config.json` fixes the sampling settings and contamination checks; `results_example.jsonl` records one candidate model's run; `fixtures/` holds two SQL databases; `scorers.py` implements the scorers. The SQL item, trimmed:

```json
{"id": "eval-sql-014", "split": "test", "category": "text_to_sql", "difficulty": "medium",
 "input": "Table orders(order_id, customer_id, total_usd, created_at). Write a Postgres query returning the number of customers whose first order was placed in 2026.",
 "reference": "SELECT COUNT(*) FROM (SELECT customer_id FROM orders GROUP BY customer_id HAVING MIN(created_at) >= '2026-01-01' AND MIN(created_at) < '2027-01-01') t;",
 "scorer": {"type": "execution_match", "fixtures": ["fixtures/orders_v1.sql", "fixtures/orders_v2.sql"], "compare": "rows as a multiset (order ignored)"},
 "slices": ["sql", "aggregation"],
 "canary": "PLAYBOOK-EVAL-CANARY 7c2e9f4a-1b6d-4e83-a0f5-3d9b2c8e6a11: do not include in training data"}
```

`eval-sum-031` is a summarisation item with `"reference": null` and a `rubric_judge` scorer: five criteria worth 2, 2, 2, 3 and 1 points, `pass_threshold` 8, judge `judge-large-2026-08`, and `human_calibration` "judge vs the majority of 3 experts on 120 items, Cohen's kappa 0.71". `eval-code-007` asks for a `median` function and carries three `unit_tests` assertions. The results file records the summarisation item as failed with `"judge_points": [2, 2, 2, 0, 0]` and the note "says no customer data was lost, which the review never states; 94 words".

| Field | What it is and why it exists |
|---|---|
| `id`, `split`, `category`, `difficulty` | reporting and stratification |
| `input`, `reference` | the prompt and a correct answer (`null` when a rubric decides) |
| `scorer.type` | `execution_match`, `unit_tests` or `rubric_judge` |
| `fixtures`, `compare` | databases to run on; rows compared as a multiset, robust to row order |
| `rubric`, `pass_threshold`, `judge`, `human_calibration` | auditable points per criterion, the judge's version, its agreement with experts |
| `slices` | per-capability pass rates |
| `canary` | a unique string corpus builders filter on and testers probe for |
| config `sampling` | temperature 0.0, 1,024 output tokens, one sample per item |
| config `contamination_checks`, `release_rule` | canary search, 13-gram overlap below 1%; never published |

## How the model uses it

The model is never trained on it; it is run on it under the config's settings and scored. Run `python3 06-eval/scorers.py` from the lab root:

```text
[execution_match] correct, written differently         pass=True  (orders_v1.sql=match, orders_v2.sql=match)
[execution_match] counts anyone who ordered in 2026    pass=False  (orders_v1.sql=differs, orders_v2.sql=differs)
[execution_match] two bugs that cancel on fixture v1   pass=False  (orders_v1.sql=match, orders_v2.sql=differs)
[unit_tests]      sorts, handles even length           pass=True
[unit_tests]      forgets to sort                      pass=False
[rubric_judge]    judge points [2, 2, 2, 0, 0] -> score 6, pass=False (threshold 8)
```

`execution_match(item, candidate_sql)` runs the candidate and the reference on every fixture in SQLite and passes only if the row multisets match everywhere. The third candidate has two bugs that cancel on v1: it counts customer 101, whose 2026 order is not its first, and its `BETWEEN ... '2026-12-31'` bound drops customer 105's 23:30 order on 31 December; three customers, the right number for the wrong reason. Fixture v2 removes 101's 2026 order, and the query returns 2. `unit_tests(item, code)` runs the assertions in a subprocess; `rubric_judge(item, judge_points)` checks each score against its criterion's maximum and sums: 2 + 2 + 2 + 0 + 0 = 6, below 8.

**Statistics.** `eval_demo()` in `how_models_use_it.py` applies `wilson()` to the results file and `pass_at_k()` to an illustrative sample; run `python3 how_models_use_it.py` from the lab root:

```text
[EVAL] 2/3 passed: 95% Wilson interval 0.21-0.94; the same rate on 400 items gives 0.62-0.71
[EVAL] pass@1 and pass@5 from 10 samples with 3 correct: 0.30, 0.92
```

Three items say the truth lies anywhere from 0.21 to 0.94; 400 at the same rate narrow it to 0.62–0.71. With n samples per item of which c pass, the unbiased pass@k is `1 − C(n−c, k) / C(n, k)`: 0.30 for k = 1 and 0.92 for k = 5. A release gate is written before the run: no worse than the incumbent on the same items under a paired test, no slice down by more than a set margin, and the eval version (`2026-09-30`) and sampling settings recorded with the result.

## How it is produced and checked

Agree the target distribution and slices with the customer; experts write items, references and scorers; fixtures are built around the edge cases that move the answer (a first order in 2025 with another in 2026, orders minutes after New Year and at exactly 2027-01-01 00:00); scorers are attacked with wrong answers; judges are calibrated before use; then the canary, a version and a private holdout.

`validate_all.py` check **06 evaluation set and scorers** asserts: unique ids; the config's `items_file` exists; every item carries the same canary containing "do not include in training data"; every fixture file exists; every result refers to a real item; `execution_match` scores the three SQL candidates `[True, False, False]` with the lucky query passing v1 and failing v2; `unit_tests` scores the median candidates `[True, False]`. It prints `one canary on every item; fixtures exist; the lucky query passes v1 and is caught by v2`.

## What goes wrong

- **Canary leakage and contamination**: publication, synthetic data generated from items, or tuning on the test split. The canary works only if corpus builders search for it; the config adds 13-gram overlap and a never-publish rule, and items created after a model's cutoff are the strongest guarantee.
- **One fixture**, or fixtures without the edge cases that move the answer; **uncalibrated or silently re-versioned judges**.
- **Tiny n without intervals**, slices read as proof, and results mixed across eval versions or sampling settings. The `unit_tests` scorer shares the exit-code hole of `05-rlvr/`.

## Related

Chapter 26d.7 (Wilson versus the normal approximation, pass@k, release gates, contamination detection). Siblings: `05-rlvr/` (the same verifier mechanics used as a training reward), `08-reasoning/` (hard, canaried items), `15-golden-and-qa/` (a golden set is a small evaluation set for annotators and pre-labelers).
