# Dataset examples lab

Complete, small, runnable examples of the datasets that AI teams buy, build and deliver for training, post-training and evaluation: supervised fine-tuning chats, preference pairs, reward-model rankings and process labels, AI feedback, RL prompts with verifiers, evaluation sets with scorers, subjective pairwise annotation, expert reasoning items, egocentric video annotations, terminal-agent tasks, SWE-bench-style repository tasks, a tau-bench-style agentic gym, and the delivery, provenance, quality and operations files around them. Chapter 26d explains every file: what the dataset is for, each field, how a model or a training job consumes it, how it is produced and checked, and what goes wrong.

Standard library only, Python 3.11 or newer (the terminal-task check reads TOML with `tomllib`). The SWE-bench-style check also needs `git` and `pytest`; without them it reports SKIP.

```bash
cd labs/dataset-examples
python3 validate_all.py          # 17 checks: schemas, consistency, checksums, and every grader on good and bad answers
python3 how_models_use_it.py     # the losses, advantages, intervals and agreement numbers quoted in chapter 26d
python3 05-rlvr/verifiers.py     # reward functions scoring sample completions
python3 06-eval/scorers.py       # execution match on two fixtures, unit tests, rubric aggregation
python3 11-swe-task/verify_instance.py                              # gold patch: resolved
python3 11-swe-task/verify_instance.py 11-swe-task/candidate_wrong.patch   # a plausible model patch: not resolved
python3 12-agentic-gym/gym.py    # replays four agent trajectories against the policy, database and tools
```

## Files

| Folder | Dataset type | What is inside | How it is used |
|---|---|---|---|
| `01-sft/` | Supervised fine-tuning (demonstrations) | Three chats in the OpenAI-style `messages` format: an audience rewrite, a clarify-then-answer SQL exchange, and a tool call with its result | Loss on the assistant's tokens only |
| `02-preference/` | Preference pairs | Two prompt / chosen / rejected records with three annotators' votes, aspect scores and lengths | DPO-family losses, or reward-model training |
| `03-reward-model/` | Rankings and process labels | A four-way ranking with a tie and Likert scores; a math solution labeled step by step | Bradley–Terry pairs; process reward models for best-of-n and search |
| `04-rlaif/` | AI feedback | A judge model's verdicts in both answer orders, a human audit, and an item dropped for position bias | Preference pairs at scale, filtered for consistency |
| `05-rlvr/` | RL with verifiable rewards | Math, code and instruction-following prompts with verifier specs and pass-rate probes; `verifiers.py` | Rewards for GRPO-style policy updates |
| `06-eval/` | Evaluation set | Three held-out items with scorers and a canary string, an eval config, results, two SQL fixtures and `scorers.py` | Pass rates with confidence intervals; release gates |
| `07-pairwise-annotation/` | Subjective pairwise judgments | 45 raw judgments: 8 video-relevance pairs and a gold item, 5 annotators each | Agreement statistics, soft labels, annotator screening |
| `08-reasoning/` | Expert reasoning items | A combinatorics problem, a physics problem and a contract-law question with full reference solutions, traps, rubric and difficulty evidence | Hard evaluation items and RLVR prompts |
| `09-egocentric-video/` | First-person video for robotics | A clip manifest with consent and privacy flags; narrations, action segments, object boxes and hand–object contact | Action recognition and anticipation, video-language pretraining, policy learning |
| `10-terminal-task/` | Terminal-agent task | A Harbor-format task: instruction, `task.toml`, Dockerfile, reference solution and verifier tests | Agent benchmarks and RL environments with a 0/1 reward file |
| `11-swe-task/` | SWE-bench-style instance | A small repository, the issue, the gold and test patches, FAIL_TO_PASS and PASS_TO_PASS lists, a wrong candidate patch and the grader | Coding-agent evaluation and RL |
| `12-agentic-gym/` | Agentic gym (tau-bench style) | A policy, a database, eight MCP-style tool definitions, a user-simulator task, expected actions, four recorded trajectories and the grader | Outcome-graded agent evaluation and pass^k reliability |
| `13-delivery/` | Delivery package | The same records as JSONL and CSV, a datasheet, and a manifest with SHA-256 checksums and the acceptance rule | What a customer receives and verifies |
| `14-synthetic-provenance/` | Synthetic-data lineage | One generated record accepted after an expert edit and one rejected as a near-duplicate | Audits, debugging and licensing questions |
| `15-golden-and-qa/` | Quality control | A golden set, annotators' accuracy on gold questions, and a QA audit sample | Annotator screening and batch acceptance |
| `16-ops-telemetry/` | Operations log | Ten expert tasks with minutes, QA time, rework and acceptance | Cost per accepted item and margin |
| `how_models_use_it.py` | — | Exact, small calculations: SFT masking, DPO and Bradley–Terry losses, process-reward aggregation, GRPO advantages, Wilson intervals, pass@k, Fleiss' kappa and Krippendorff's alpha, acceptance sampling, unit economics | Reproduces the chapter's numbers |
| `validate_all.py` | — | Every check a delivery team would run before shipping these files | Exit code 0 when nothing fails |

## Conventions

- Everything is invented for teaching: companies, customers, products, model names (`judge-large-2026-08`, `generator-model-2026-07`), annotator IDs, bucket URIs and email addresses (`example.com`). No real person's data appears.
- IDs are stable and cross-referenced: the lineage record `syn-30441` points at the delivered chat `sft-000417`; the gym task's expected actions use the database's IDs. `validate_all.py` checks those links.
- Most records carry a `spec_version` (the video annotations an `annotation_version`), because the guidelines change during a project and every label must be traceable to the version it was made under.
- The evaluation items carry a canary string. Do not copy them into any training corpus.
- The verifiers and the SWE grader run model-written code in a subprocess with a timeout. That is fine for these examples; it is not a sandbox. Run untrusted code in an isolated container with no network.
- The terminal task follows the Harbor task layout (the format of Terminal-Bench 2.0). To run it for real, use a Harbor-compatible harness with Docker; the reference solution must score 1 and doing nothing must score 0.
