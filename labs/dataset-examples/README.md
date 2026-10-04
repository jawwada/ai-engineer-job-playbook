# Dataset examples lab

Complete, small, runnable examples of the datasets that AI teams buy, build and deliver for training, post-training and evaluation: supervised fine-tuning chats, preference pairs, reward-model rankings and process labels, AI feedback, RL prompts with verifiers, evaluation sets with scorers, subjective pairwise annotation, expert reasoning items, egocentric video annotations, terminal-agent tasks, SWE-bench-style repository tasks, a tau-bench-style agentic gym, and the delivery, provenance, quality and operations files that ship around them. Every folder has its own `README.md` with the real record, a field table, the exact mechanism by which a model or grader consumes it, the production and validation steps, and the failure modes. This page is the map and the shared material: how the types fit together, what the two scripts compute, and how to use and extend the lab. Chapter 26d of the book goes deeper on every folder and quotes this lab's numbers.

## Requirements

Standard library only, Python 3.11 or newer (the terminal-task check reads TOML with `tomllib`). The SWE-bench-style check and grader also need `git` and `pytest`; without them `validate_all.py` reports that check as SKIP, not FAIL, and `verify_instance.py` cannot run. Nothing downloads anything; no model is called.

## Quick start

Run everything from this folder.

```bash
cd labs/dataset-examples
python3 validate_all.py          # 17 checks: schemas, consistency, checksums, and every grader on good and bad answers
python3 how_models_use_it.py     # the losses, advantages, intervals and agreement numbers quoted in chapter 26d
python3 05-rlvr/verifiers.py     # reward functions scoring sample completions
python3 06-eval/scorers.py       # execution match on two fixtures, unit tests, rubric aggregation
python3 11-swe-task/verify_instance.py                                    # gold patch: resolved
python3 11-swe-task/verify_instance.py 11-swe-task/candidate_wrong.patch  # a plausible model patch: not resolved
python3 12-agentic-gym/gym.py    # replays four agent trajectories against the policy, database and tools
```

What each prints: `validate_all.py` prints one `PASS`, `SKIP` or `FAIL` line per check with a one-line detail, then `17/17 checks without failures` and exits 0 when nothing fails. `how_models_use_it.py` runs eleven functions that print twelve labeled blocks (`[SFT]`, `[DPO]`, `[RM]`, `[PRM]`, `[RLAIF]`, `[RLVR]`, `[EVAL]`, `[ANNOT]`, `[REASONING]`, `[VIDEO]`, `[QA]`, `[OPS]`). `verifiers.py` prints three reward lists: `[1.0, 0.0, 0.0]`, `[1.0, 0.0]`, `[1.0, 0.0]`. `scorers.py` prints six scorer verdicts, including the lucky SQL query that matches fixture v1 and differs on v2. `verify_instance.py` prints PASS or FAIL per test and `resolved: True` for the gold patch, `resolved: False` with three failures for the wrong one. `gym.py` prints one line per trajectory (`reward=1` for the reference, `reward=0` for the three flawed runs) and pass^k for 6 successes in 8 trials: `{1: 0.75, 2: 0.536, 4: 0.214, 8: 0.0}`.

## The map

| Folder | Dataset type | Files | What the model does with it | Chapter |
|---|---|---|---|---|
| [`01-sft/`](01-sft/README.md) | Supervised fine-tuning demonstrations | `sft_examples.jsonl` (3 chats, one with a tool call) | cross-entropy on the assistant's tokens only | 26d.2 |
| [`02-preference/`](02-preference/README.md) | Preference pairs | `preference_pairs.jsonl` (2 pairs, 3 annotators each) | DPO-family losses, or reward-model training | 26d.3 |
| [`03-reward-model/`](03-reward-model/README.md) | Rankings and process labels | `rankings.jsonl`, `prm_steps.jsonl` | Bradley–Terry pairs; process reward models for best-of-n and search | 26d.4 |
| [`04-rlaif/`](04-rlaif/README.md) | AI feedback | `ai_feedback.jsonl` (2 items, judged in both orders) | preference pairs at scale, after a consistency filter | 26d.5 |
| [`05-rlvr/`](05-rlvr/README.md) | RL with verifiable rewards | `rlvr_prompts.jsonl` (4 prompts), `verifiers.py` | 0/1 rewards and group-relative advantages (GRPO) | 26d.6 |
| [`06-eval/`](06-eval/README.md) | Evaluation set | `eval_items.jsonl`, `eval_config.json`, `results_example.jsonl`, `fixtures/`, `scorers.py` | never trained on; pass rates with Wilson intervals, pass@k, release gates | 26d.7 |
| [`07-pairwise-annotation/`](07-pairwise-annotation/README.md) | Subjective pairwise judgments | `raw_annotations.csv` (45 judgments) | soft labels for rankers; agreement and position-bias statistics | 26d.8 |
| [`08-reasoning/`](08-reasoning/README.md) | Expert reasoning items | `reasoning_items.jsonl` (3 items) | hard evaluation items, RLVR prompts, SFT targets | 26d.9 |
| [`09-egocentric-video/`](09-egocentric-video/README.md) | First-person video for robotics | `clip_manifest.json`, `clip_annotations.json` | action recognition and anticipation, video–language pretraining, hand–object detection | 26d.10 |
| [`10-terminal-task/`](10-terminal-task/README.md) | Terminal-agent task (Harbor format) | `fix-log-permissions/` (instruction, `task.toml`, Dockerfile, solution, tests) | agent benchmark and RL environment with a 0/1 reward file | 26d.11 |
| [`11-swe-task/`](11-swe-task/README.md) | SWE-bench-style instance | `instance.json`, `repo/`, three patches, `verify_instance.py` | resolved only if every FAIL_TO_PASS and PASS_TO_PASS test passes | 26d.12 |
| [`12-agentic-gym/`](12-agentic-gym/README.md) | Agentic gym (tau-bench style) | `policy.md`, `db.json`, `tools.json`, `tasks.json`, `trajectories/`, `gym.py` | outcome grading by final database state plus required outputs; pass^k | 26d.13 |
| [`13-delivery/`](13-delivery/README.md) | Delivery package | `train.jsonl`, `train.csv`, `datasheet.md`, `manifest.json` | what the customer verifies before any record is loaded | 26d.14 |
| [`14-synthetic-provenance/`](14-synthetic-provenance/README.md) | Synthetic-data lineage | `lineage.jsonl` (one accepted, one rejected) | audits, contamination and licensing answers; dedupe | 26d.15 |
| [`15-golden-and-qa/`](15-golden-and-qa/README.md) | Quality control | `golden_set.jsonl`, `gold_question_results.csv`, `qa_audit_sample.csv` | annotator screening and lot acceptance with known risks | 26d.16 |
| [`16-ops-telemetry/`](16-ops-telemetry/README.md) | Operations log | `task_log.csv` (10 tasks) | cost per accepted item and margin | 26d.17 |

## How models learn from data, in one page

Pretraining data is filtered at scale rather than written record by record, so the lab has no folder for it; everything here is data that people write, judge or build on purpose, after pretraining. The types differ in what signal they carry, what it costs to produce one unit of it, and why a team buys it rather than builds it.

**Demonstrations (01)** carry the densest signal per record and the simplest loss: the model copies the assistant's tokens, graded on each one. They set a model's defaults (format, tone, when to ask back, how to call a tool) but can only show one answer per prompt, and writing an excellent answer is expensive expert work. Teams buy them when a behaviour is missing and experts can write it affordably.

**Preferences (02, 03, 04)** carry one bit per comparison, but a cheap and reliable bit: judging two answers is easier than writing one. The three folders are three ways to collect the same signal. Pairs (02) feed DPO directly or train a reward model; rankings (03) yield several pairs at once and process labels grade each step; AI feedback (04) replaces most human judges with a model plus principles, a both-orders filter and a human audit. This is where honesty and caution get taught, because the losing answer is often fluent. The cost moves from writing to judging, and with RLAIF to judge engineering.

**Reward models (03)** turn comparisons into a number a training loop can maximise. Their weakness is the policy's strength: it finds what the grader over-rates. So teams cap how far the policy may drift and keep human-judged evaluations.

**Verifiable rewards (05)** remove the human from the loop where a program can check the answer: a number, a test suite, a format rule. The model samples several attempts, the verifier scores each, and the group's mean and spread become advantages; prompts the policy always or never solves carry no signal and are filtered out. The cost is in verifier engineering and adversarial review: a verifier is ready only when it rejects the answers people will sneak past it, and the lab's unit-test verifier deliberately leaves an `exit(0)` hole for exercise 4 of chapter 26d.21.

**Environments (10, 11, 12)** are verifiable rewards for agents: a container, a repository or a simulated business, with a hidden check that runs after the agent stops. The same folder is a benchmark item (many agents, compare pass rates) and an RL environment (one agent, many attempts). Only the end state counts, which is why each has an oracle that must score 1 and a no-op or wrong attempt that must score 0.

**Hard items (08) and subjective judgments (07)** are the two edges of labeling. Reasoning items need an expert to write, a second to re-solve, a program to check, and a strong model to fail; their value is in being correct and hard. Pairwise relevance judgments have no right answer at all, so their value is measured by agreement, hidden gold and bias reports, and delivered as soft labels. **Video (09)** shows what annotation looks like when the unit is a frame range and consent travels with the data.

**Evaluation sets (06)** measure all of the above and must never be trained on; hence a canary string in every item, contamination checks, a private holdout, and intervals on every number (2 of 3 says almost nothing; 400 items at the same rate say 0.62–0.71).

**The wrapper (13, 14, 15, 16)** is what makes any of this deliverable: a manifest with checksums and a datasheet; lineage for every generated record; gold questions for annotators and an audit plan with computed risks for each batch; and a cost log, because a project that loses \$33.81 on every accepted item fails before its data quality is ever questioned.

## The two scripts

### `how_models_use_it.py`

Eleven functions, each printing the numbers chapter 26d quotes; standard library only; run from this folder. Each folder README explains its function in context; the summary:

| Function | What it computes | Printed line begins |
|---|---|---|
| `sft_loss_mask_demo()` | renders `sft-000417` with a toy template, masks all but the assistant's tokens, and gives the mean loss at p = 0.6 and 0.9 | `[SFT] 148 tokens in the rendered chat, 77 carry loss` |
| `dpo_demo(beta=0.1)` | the DPO implicit reward margin and loss from four illustrative log-probabilities | `[DPO] beta=0.1: implicit reward margin 0.20, loss 0.598` |
| `reward_model_demo()` | the Bradley–Terry loss for rewards 1.3 and −0.4; the five training pairs from `rank-00881`'s ranking with its tie; min and product aggregation for a flawed and a correct PRM-scored solution | `[RM] Bradley-Terry loss ... 0.168` and `[PRM] flawed solution min/product 0.18/0.063` |
| `rlaif_demo()` | how many of the AI-feedback items agree across both orders and carry a label | `[RLAIF] 1/2 items have the same verdict in both orders` |
| `grpo_demo()` | group-relative advantages for eight rewards; the zero-variance warning; the pass-rate filter for each RLVR prompt | `[RLVR] group rewards [1, 0, 0, 1, 1, 0, 0, 0]: mean 0.375, std 0.484` |
| `wilson(successes, n)`, `pass_at_k(n, c, k)`, `eval_demo()` | the 95% Wilson interval for 2 of 3 and for the same rate on 400 items; unbiased pass@1 and pass@5 from 10 samples with 3 correct | `[EVAL] 2/3 passed: 95% Wilson interval 0.21-0.94` and `[EVAL] pass@1 and pass@5 ... 0.30, 0.92` |
| `fleiss_kappa(table)`, `krippendorff_alpha_nominal(units)`, `annotation_demo()` | per-item votes, majority and soft label; κ and α over the eight regular items; the gold item's result | `[ANNOT] P-01: votes ...`, `[ANNOT] Fleiss' kappa 0.351`, `[ANNOT] gold item: 4/5 correct; failed: ['ann_206']` |
| `reasoning_demo()` | brute-force count of 7-digit permutations divisible by 11; the incline distance h/μ | `[REASONING] brute force over 5,040 permutations finds 576` |
| `video_demo()` | action segments as frame ranges at 30 fps, their coverage of the clip, the verb histogram | `[VIDEO] 7 action segments cover 22.7 of 24.0 s` |
| `acceptance_demo(n=80, c=2)` | the operating characteristic of the n = 80, c = 2 sampling plan at six defect rates | `[QA] audit 80 records, accept the batch if at most 2 defects` |
| `ops_demo(price=150.0, expert_rate=36.0, qa_rate=30.0, budget_minutes=150)` | cost per accepted item, gross margin, expert minutes per task in the first and second half of the log | `[OPS] 8/10 accepted; cost per accepted item $183.81 vs price $150: gross margin -22.5%` |

The illustrative inputs (DPO log-probabilities, the reward pair 1.3 and −0.4, PRM step scores, the GRPO group of eight, the pass@k sample of 10) are hard-coded in the functions and labeled as such; everything else is read from the folder files.

### `validate_all.py`

Seventeen named checks, registered with a `@check(name)` decorator and run in order; each returns a detail string on success, raises `Skip` when a dependency is missing, or raises on failure. Every failure is reported and the script keeps going; the exit code is 1 if any check failed. Imports of the lab modules set `sys.dont_write_bytecode`, so running it leaves no `__pycache__` behind.

| Check | What it asserts | A failure means |
|---|---|---|
| `01 SFT demonstrations` | unique ids; valid roles; system first; final non-empty assistant turn; tool calls name declared tools with JSON-parsable arguments; tool results answer open calls; reviewer ≠ author; review score 1–5 | a chat a trainer would mis-render or a review that was not independent |
| `02 preference pairs` | prompt ends with a user turn; single, different chosen and rejected messages; annotator majority prefers `chosen`; two different sample indices | a pair whose label contradicts its annotators, or two copies of one sample |
| `03 rankings and process labels` | ranking is a permutation with tied ids adjacent; Likert totals follow the ranking; step labels in {−1, 0, 1}; `first_error_step` is the first −1; the \$26 reference re-derived by brute force | a ranking that contradicts its own scores, or a wrong answer key |
| `04 AI feedback (RLAIF)` | both orders judged; a label exactly when verdicts agree; the label's winner is the judge's; dropped items have a reason; audit agreement consistent | a position-biased verdict leaked into training pairs |
| `05 RLVR prompts and verifiers` | `use_in_batch` is true exactly when 0 < correct < samples; verifiers score the samples [1, 0, 0], [1, 0], [1, 0] | a zero-signal prompt in the batch, or a verifier that rewards a wrong answer |
| `06 evaluation set and scorers` | unique ids; items file and fixtures exist; one canary on every item; results refer to real items; SQL candidates [True, False, False] with the lucky query caught by v2; median candidates [True, False] | an uncanaried item, or a scorer that passes a wrong answer |
| `07 pairwise annotation (no ground truth)` | valid choices, sides, confidence, times; identical item text per item; five distinct annotators per item; κ and α pinned at 0.351 and 0.367 | a malformed judgment, or an edit that changed the agreement statistics |
| `08 expert reasoning items` | 576 by brute force; the physics answer within tolerance; rubric totals 10 with threshold ≤ 10; every re-solve agrees; traps listed | an item whose answer key or review is wrong |
| `09 egocentric video annotations` | clip ids match; frames = fps × duration; privacy flags and consent; non-overlapping in-range actions; every narration starts `#C C ` and lies inside an action; boxes inside the frame; contacts name real tracks | a label a loader would place at the wrong frame, or a clip without consent |
| `10 terminal-agent task (Harbor format)` | six files present; `task.toml` parses with positive timeouts; no `COPY`/`ADD` of `tests` or `solution`; `test.sh` writes the reward file; `test_outputs.py` compiles | a task the agent could cheat, or one the harness cannot run |
| `11 SWE-bench-style instance` | twelve required fields; test patch touches only `tests/`, gold patch touches no tests; FAIL_TO_PASS names in the test patch; with git and pytest, gold resolves and the wrong patch fails three tests (else SKIP) | a broken or leaky instance |
| `12 agentic gym (tau-bench style)` | every tool is a gym method with an object schema; expected actions name real tools; trajectories score {1, 0, 0, 0}; pass^k for 6 of 8 is [0.75, 0.536, 0.214, 0.0] | a grader that passes a trap or fails the reference |
| `13 delivery package (JSONL, CSV, datasheet, manifest)` | SHA-256 and byte sizes match; record count matches; intents in the enum; entity offsets reproduce their values; CSV mirrors JSONL | a modified, truncated or inconsistent delivery |
| `14 synthetic-data lineage` | accepted records are not duplicates, passed review, point at a delivered record not marked `expert_written`; rejected records are duplicates or have a reason, and point at nothing | provenance that contradicts the delivered data |
| `15 golden set, gold questions and QA audit` | gold labels in the enum with explanations; annotators below the 90% floor listed (`ann_303`); each audit row's `defect` equals a label mismatch | a gold item outside the spec, or an audit row that miscounts defects |
| `16 operations telemetry` | unique task ids; positive expert minutes; non-negative QA minutes and rework; acceptance true or false | a log the unit-economics calculation cannot trust |
| `how_models_use_it.py numbers` | runs the script and searches its output for fourteen pinned strings (`77 carry loss`, `loss 0.598`, `kappa 0.351`, `finds 576`, `$183.81`, `-22.5%`, and so on) | a record or function changed and chapter 26d's quoted numbers no longer hold |

## Using the lab

**For interviews.** The lab backs chapters 26 (fine-tuning), 26b (alignment and RL), 26c (data strategy) and 26d (this lab, with interview questions in 26d.20). Be able to say, for any folder, what one record looks like, which field the loss or grader reads, the number the lab prints for it and why, and the failure mode that would corrupt it: for 01, the −100 mask and the end-of-turn marker; for 02, four log-probabilities, a margin of 0.20 and a loss of 0.598 against 0.693; for 05, why a prompt at pass rate 1.00 teaches nothing; for 06, why 2 of 3 is an interval from 0.21 to 0.94; for 07, why κ = 0.35 is a reason to look for position bias rather than to discard the data; for 12, why the state hash and the required outputs are both necessary; for 15, why "at most 2 in 80" accepts a 5% lot a quarter of the time; for 16, why cost per accepted item must include rejected work and review minutes. Data-production interviews often add a short coding exercise on these utilities (Fleiss' κ, the Wilson interval, pass@k, a state-hash grader); write them from the chapter's formulas and test against `how_models_use_it.py`.

**Extending it with your own records.** Work on a copy and rerun `python3 validate_all.py` after every change; several checks pin exact results (κ and α, the gym rewards, the delivery checksums, the fourteen strings from `how_models_use_it.py`), so an exercise that adds a case also updates its check. Follow the conventions the validator enforces: give every labeled record a `spec_version` (or `annotation_version` for video) naming the guideline version it was made under; keep ids stable and cross-referenced (a lineage record's `final_record_id` must exist in `01-sft/`; a gym task's expected actions must use the database's ids); put the canary string on every evaluation item and search for it before any record enters a training set; invent people, companies and addresses (`example.com`, model names like `judge-large-2026-08`); and when you change a delivery file, recompute its SHA-256 and size in `manifest.json` last. Chapter 26d.21 lists eight exercises, from a fifth gym trajectory to re-pricing the project at \$45 an hour.

**The sandbox warning.** `05-rlvr/verifiers.py`, `06-eval/scorers.py` and `11-swe-task/verify_instance.py` execute model-written code in a subprocess with a timeout. That is acceptable for these fixed examples; it is not a sandbox, and the unit-test verifier and scorer also trust the exit code, so a completion that calls `sys.exit(0)` before the assertions earns a reward. Run untrusted code in an isolated container with no network and resource limits, and accept only positive evidence of passing through a channel the candidate cannot forge.

## Conventions

- Everything is invented for teaching: companies, customers, products, model names (`judge-large-2026-08`, `generator-model-2026-07`), annotator IDs, bucket URIs and email addresses (`example.com`). No real person's data appears.
- IDs are stable and cross-referenced: the lineage record `syn-30441` points at the delivered chat `sft-000417`; the gym task's expected actions use the database's IDs. `validate_all.py` checks those links.
- Most records carry a `spec_version` (the video annotations an `annotation_version`), because the guidelines change during a project and every label must be traceable to the version it was made under.
- The evaluation items carry a canary string. Do not copy them into any training corpus.
- The verifiers and the SWE grader run model-written code in a subprocess with a timeout. That is fine for these examples; it is not a sandbox. Run untrusted code in an isolated container with no network.
- The terminal task follows the Harbor task layout (the format of Terminal-Bench 2.0). To run it for real, use a Harbor-compatible harness with Docker; the reference solution must score 1 and doing nothing must score 0.
