# 03: Reward-model rankings and process labels

## What this dataset is for

A reward model is a learned grader: given a prompt and an answer, it returns one number, higher meaning people would prefer it. It learns from comparisons, as a new judge learns a panel's taste by watching its decisions. A **ranking** of several answers yields many comparisons at once, so it is a denser way to collect the preferences of `02-preference/`. **Process labels** grade each step of a solution, like a teacher marking a maths exam line by line, so the grader knows not only that a solution is wrong but where it went wrong; that is what a process reward model (PRM) learns.

The question this folder answers is: *how do we turn human judgment into a number a training loop can maximise, per answer or per step?*

## The example

Two files. `rankings.jsonl` holds `rank-00881`: four explanations of a database index for a new analyst, a full order with one tie, and Likert scores per criterion:

```json
{"id": "rank-00881",
 "prompt": "Explain what a database index is to a new analyst in two sentences.",
 "responses": [{"id": "r1", "text": "An index is a separate, sorted structure that lets the database find rows ... costs storage and slows down inserts and updates a little."},
               {"id": "r2", "text": "An index makes queries faster by sorting the data ... You should add indexes to every column."},
               {"id": "r3", "text": "A database index is a B-tree."},
               {"id": "r4", "text": "Indexes are like a book's index: ... at the cost of extra storage and slightly slower writes."}],
 "ranking": ["r1", "r4", "r2", "r3"], "ties": [["r1", "r4"]],
 "likert": {"r1": {"accuracy": 5, "clarity": 5}, "r4": {"accuracy": 5, "clarity": 5},
            "r2": {"accuracy": 2, "clarity": 4}, "r3": {"accuracy": 3, "clarity": 1}},
 "meta": {"annotator": "ann_142", "spec_version": "rank-v1.1"}}
```

`prm_steps.jsonl` holds `prm-01210`, a four-step solution to "Pens cost \$3 each or \$10 for a pack of 4. What is the least you can pay for exactly 10 pens?" with a label per step:

```json
{"id": "prm-01210",
 "steps": [{"text": "A pack costs $10 for 4 pens, which is $2.50 per pen, cheaper than $3 for a single pen.", "label": 1},
           {"text": "Two packs give 8 pens for $20, leaving 2 pens to buy singly.", "label": 1},
           {"text": "The remaining 2 pens cost 2 x $3 = $5.", "label": -1},
           {"text": "So the total is $20 + $5 = $25.", "label": -1}],
 "final_answer": "25", "reference_answer": "26", "first_error_step": 3,
 "meta": {"labeler": "exp_008", "label_scheme": "+1 correct and useful, 0 correct but not useful, -1 incorrect", "spec_version": "prm-v1.0"}}
```

| Field | What it is and why it exists |
|---|---|
| `responses[]`, `ranking` | the answers and their order, best first: the source of pairwise preferences |
| `ties` | pairs judged equal; a tie is not a preference |
| `likert` | 1 to 5 per criterion: a consistency check on the ranking, or a margin |
| `steps[].label` | +1 correct and useful, 0 correct but not useful, −1 incorrect: the per-step targets |
| `final_answer`, `reference_answer` | 25 against 26: the outcome label |
| `first_error_step` | 3, where 2 × \$3 became \$5 |
| `meta` | annotator or labeler, label scheme, spec version |

## How the model uses it

**Bradley–Terry.** A reward model is usually the policy's architecture with a one-number head. It models P(y_w beats y_l) = σ(r_w − r_l) and minimises −log σ(r_w − r_l). A ranking of K answers gives C(K, 2) pairs, 6 for K = 4; a tie is dropped (or trained toward equal scores). `reward_model_demo()` in `how_models_use_it.py` computes the loss for an illustrative pair of rewards and expands the lab's ranking into pairs; run `python3 how_models_use_it.py` from the lab root:

```text
[RM] Bradley-Terry loss for rewards 1.3 vs -0.4: 0.168; ranking ['r1', 'r4', 'r2', 'r3'] with tie ['r1', 'r4'] gives 5 training pairs: [('r1', 'r2'), ('r1', 'r3'), ('r4', 'r2'), ('r4', 'r3'), ('r2', 'r3')]
```

Rewards of 1.3 and −0.4 say the chosen answer wins with probability σ(1.7) = 0.85, so the loss is 0.168; reversed, it would be 1.868. The `r1`–`r4` tie removes one of the six pairs, leaving the five printed. The Likert totals (10, 10, 6, 4) must agree with the ranking. Keep a prompt's comparisons in one batch element; treating them as independent examples overfits.

**Process reward model.** A PRM predicts each step's label and combines step scores into a solution score, by the **minimum** (the weakest step decides) or the **product** (the chance that every step is right). The same function hard-codes what a trained PRM might output for the pen solution and for a correct one:

```text
[PRM] flawed solution min/product 0.18/0.063; correct solution 0.90/0.747; best-of-n keeps the correct one
```

The flawed solution's third step scores 0.18, giving 0.18 and 0.063; the correct one scores 0.90 and 0.747, so best-of-n selection keeps it. In step-level search a PRM scores partial solutions after every step and prunes weak ones before they finish, which an outcome reward model cannot do.

## How it is produced and checked

Rankings: four to nine answers per prompt, a full order with ties allowed, per-criterion scores, and a written definition of a tie. Process labels: an expert solves the problem first, then reads the solution step by step; the spec defines what a step is, what "correct but not useful" means, and whether labeling stops at the first error; the reference answer is re-derived independently.

`validate_all.py` check **03 rankings and process labels** asserts: `ranking` is a permutation of the response ids; tied responses are adjacent in it; Likert totals are non-increasing along the ranking; step labels are in {−1, 0, 1}; `first_error_step` is the first −1; `final_answer` differs from `reference_answer`; and the reference is recomputed by brute force (the cheapest way to buy exactly 10 pens from packs of 4 at \$10 and singles at \$3 is \$26). It prints `ranking is a permutation with adjacent ties; PRM first error at step 3; reference $26 re-derived`.

## What goes wrong

- **Over-optimisation**: the policy finds what the reward model over-rates (length, tone, keywords) while real quality falls; keep human-judged evaluations and cap KL or steps.
- **Inconsistent rankings**, ties used as an escape hatch, and pairs from one prompt treated as independent samples.
- **Step segmentation** that differs between labeling and inference, and PRMs that never saw the policy's current errors.

## Related

Chapter 26d.4 (InstructGPT's 4 to 9 answers per prompt, PRM800K, Math-Shepherd, TRL's `RewardTrainer`). Siblings: `02-preference/` (the pair form of the same signal), `05-rlvr/` (a program instead of a learned grader), `08-reasoning/` (where step-labeled solutions come from).
