# 08: Expert reasoning items

## What this dataset is for

Olympiad- and bar-exam-grade questions written by specialists to find where the strongest models fail. Each item carries a worked solution, the typical wrong answers, a checkable answer or a rubric, and evidence of two things: correctness (an independent re-solve, a program where possible) and hardness (a strong model failing it, with the date and attempt count). The question an item answers is: *is this correct, is it hard for the model we care about, and how will it be scored?* The same item can be a private evaluation question, an RLVR prompt, or an SFT target through its reference solution.

## The example

`reasoning_items.jsonl` holds three items: a combinatorics problem (`rsn-math-0144`), a work-energy physics problem kept as an easy calibration anchor (`rsn-phys-0057`), and a self-contained contract-interpretation question scored by rubric (`rsn-legal-0023`). The first, trimmed:

```json
{"id": "rsn-math-0144", "domain": "math", "subdomain": "combinatorics / number theory",
 "problem": "How many 7-digit numbers that use each of the digits 1 through 7 exactly once are divisible by 11?",
 "reference_solution": [
   "A number is divisible by 11 exactly when the alternating sum of its digits is divisible by 11. ... let O be the sum of the digits in odd positions (four digits) and E the sum in even positions (three digits).",
   "O + E = 1 + 2 + ... + 7 = 28, and we need O - E to be a multiple of 11.",
   "... So O = E = 14.",
   "Count the 3-element sets of digits with sum 14 ...: {1,6,7}, {2,5,7}, {3,4,7}, {3,5,6}. That is 4 sets.",
   "Each choice can be arranged in 3! ways in the even positions and the remaining digits in 4! ways in the odd positions: 4 x 6 x 24 = 576."],
 "final_answer": "576", "answer_type": "integer",
 "verifier": {"type": "numeric", "answer": 576, "tolerance": 0},
 "common_wrong_answers": [{"answer": "288", "why": "forgets one of the two position classes when counting arrangements"},
                          {"answer": "144", "why": "counts only one digit set"}],
 "difficulty_evidence": {"target_model": "frontier-model-x (illustrative)", "attempts": 8, "correct": 0, "recorded": "2026-09-20"},
 "review": {"independent_resolve": {"reviewer": "exp_012", "answer": "576", "agrees": true}, "checked_by_program": true},
 "meta": {"author": "exp_003", "minutes_spent": 95, "spec_version": "rsn-v2.1"}}
```

The physics item's verifier is `{"type": "numeric", "answer": 6.0, "unit": "m", "tolerance": 0.05}` and its `difficulty_evidence` is a note that it does not count toward the hard-item quota. The legal item's verifier is a five-criterion rubric worth 3 + 2 + 2 + 2 + 1 = 10 points with `pass_threshold` 8, and its target model solved it 3 times in 8.

| Field | What it is and why it exists |
|---|---|
| `domain`, `subdomain` | coverage targets and slicing |
| `problem` | self-contained; nothing to look up |
| `reference_solution` | steps: proof of correctness, SFT target, grading guide |
| `final_answer`, `answer_type`, `verifier` | how the item is scored: numeric with tolerance (and unit), or a rubric with a pass threshold |
| `common_wrong_answers` | the traps (288, 144) that make the item discriminating |
| `difficulty_evidence` | target model, attempts, passes, date (0/8 and 3/8), or a note for anchors |
| `review` | the independent re-solve and whether a program checked it |
| `meta` | author, minutes spent (95, 20, 70), spec version |

## How the model uses it

**As an RLVR prompt**, through the numeric verifier of `05-rlvr/`. Difficulty is relative to the policy: the target model solved `rsn-math-0144` 0 times in 8, so its GRPO groups on this item would almost always be all zeros; it is an evaluation item for that model and becomes a training item only for a policy that sometimes solves it. The legal item, at 3 of 8, is informative now. **As a hard evaluation item**, private and canaried as in `06-eval/`. **By rubric** for the legal item: a judge scores criterion by criterion and code sums; the listed trap answer ("Yes, because 22 days exceeds the 15-day safe harbor") fails the conclusion, both conditions, the materiality point and the cure-period computation, and can earn at most the 1 point for citing no outside law. **As SFT targets**, the reference solutions are worked reasoning in each domain's style.

`reasoning_demo()` in `how_models_use_it.py` re-derives the two numeric answers by program; run `python3 how_models_use_it.py` from the lab root:

```text
[REASONING] brute force over 5,040 permutations finds 576 multiples of 11; incline answer d = h/mu = 6.0 m
```

The brute-force count over all 7! permutations confirms the expert's argument, and the physics answer d = 1.5 / 0.25 is recomputed within the 0.05 tolerance.

## How it is produced and checked

Domain experts, screened by test, write self-contained items with one defensible answer or a rubric and list the traps; each draft runs against the target model several times and is kept only if it fails often enough; a second expert solves it independently; a program checks it where possible; easy anchors are flagged; pay is usually tied to difficulty.

`validate_all.py` check **08 expert reasoning items** asserts: unique ids; the brute-force count equals the verifier's answer and 576; the physics answer is within tolerance of h/μ; the legal rubric totals 10 and the threshold is at most that; every item's independent re-solve agrees and lists at least one common wrong answer. It prints `576 re-counted by brute force; d = 6.0 m re-computed; rubric totals 10 with pass at 8`. Acceptance usually adds a hardness bar on a named model and date (for example, at most 2 passes in 8).

## What goes wrong

- **Hard because wrong or ambiguous**: a 0/8 on a malformed item proves nothing; the independent re-solve and the program check exist to separate hard from broken.
- **Difficulty measured once**, on one model at one setting, and never refreshed; **leakage** from published sources before or after delivery.
- **Rubrics that reward keywords**, and units or tolerances that admit the trap answers (multiplying by the 2.0 kg mass gives 12 m; using h × μ gives 0.6 m).

## Related

Chapter 26d.9 (production pipeline, the hardness bar, interview angle). Siblings: `05-rlvr/` (the verifier that scores the numeric items and the batch filter that decides whether 0/8 can train), `06-eval/` (rubric aggregation and canaries), `03-reward-model/` (step labels on solutions like these), `16-ops-telemetry/` (what 95 minutes per item costs).
