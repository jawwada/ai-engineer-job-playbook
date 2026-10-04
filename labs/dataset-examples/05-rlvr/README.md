# 05: RL with verifiable rewards (RLVR)

## What this dataset is for

Practice problems with an answer key. The model attempts each problem several times, a program checks every attempt (does the number match, do the tests pass, are the format rules obeyed), and the policy is pushed toward whatever its successful attempts did differently. Nobody grades the reasoning, only the checkable outcome. That is why RLVR scales past human labeling, and why the key must be right and hard to fool: the model learns whatever the key rewards.

A record here is a prompt plus a verifier spec plus evidence of how hard the prompt is for the policy about to be trained. The question it answers is: *can the current policy sometimes, but not always, get this right, and can a program tell?*

## The example

`rlvr_prompts.jsonl` holds four prompts with three verifier types: numeric (`rlvr-math-0091`), unit tests (`rlvr-code-0337`), format rules (`rlvr-if-0512`), and one excluded prompt (`rlvr-math-0092`, "What is 17 + 25?"). The coding prompt:

```json
{"id": "rlvr-code-0337",
 "prompt": "Write a Python function is_balanced(s: str) -> bool that returns True when every bracket in s among ()[]{} is closed in the correct order, ignoring all other characters. Return only the code in one ```python block.",
 "verifier": {"type": "unit_tests", "entry_point": "is_balanced", "timeout_s": 5,
              "tests": ["assert is_balanced('') is True", "assert is_balanced('([]{})') is True",
                        "assert is_balanced('(]') is False", "assert is_balanced('((') is False",
                        "assert is_balanced('a(b[c]d)e') is True", "assert is_balanced('}{') is False"]},
 "difficulty_probe": {"model": "policy-v3@step1200", "samples": 16, "correct": 11},
 "use_in_batch": true}
```

The excluded one ends with `"use_in_batch": false, "exclude_reason": "solved by every sample: zero advantage, no learning signal"`.

| Field | What it is and why it exists |
|---|---|
| `prompt` | the task, including the output format ("End with a line of the form 'Answer: <number>'", "one ```python block") that makes the answer extractable |
| `verifier.type` | `numeric`, `unit_tests` or `format_rules`: selects the reward function in `verifiers.py` |
| `answer`, `tolerance`, `extract` | what counts as correct and where to find it (numeric) |
| `entry_point`, `tests`, `timeout_s` | the executable specification of a coding task |
| `rules` | machine-checkable constraints (`bullet_count`, `max_words_per_bullet`, `forbidden_first_word`) |
| `difficulty_probe` | 16 samples from `policy-v3@step1200`, the checkpoint to be trained, and how many passed |
| `use_in_batch`, `exclude_reason` | keeps prompts that cannot teach out of the batch |

## How the model uses it

**Sample** G completions per prompt from the current policy (8 to 16 is typical). **Score** each with the prompt's verifier: `verifiers.reward(item, completion)` dispatches on `verifier.type` to `verify_numeric`, `verify_unit_tests` or `verify_format_rules`, each returning 1.0 or 0.0. Run `python3 05-rlvr/verifiers.py` from the lab root to score the built-in `SAMPLE_COMPLETIONS`:

```text
rlvr-math-0091: rewards [1.0, 0.0, 0.0]
rlvr-code-0337: rewards [1.0, 0.0]
rlvr-if-0512: rewards [1.0, 0.0]
```

The math completions score 1 (576 with the answer line), 0 (a guess of 458) and 0 (the right number without the required `Answer:` line: deliberately, since a verifier that hunts for any matching number rewards answers that merely mention it). The bracket-counting program passes five of six tests and fails `is_balanced('}{')`; the reward is 0, not 5/6, so partial cheats do not pay. The second bullet list starts with "The": 0.

**Advantages.** GRPO replaces PPO's value model with the group: `A_i = (r_i − mean(r)) / std(r)` over one prompt's G completions, shared by every token of completion i. `grpo_demo()` in `how_models_use_it.py` works a group of eight and then applies the batch filter to the four prompts; run `python3 how_models_use_it.py` from the lab root:

```text
[RLVR] group rewards [1, 0, 0, 1, 1, 0, 0, 0]: mean 0.375, std 0.484, advantages [1.29, -0.77, -0.77, 1.29, 1.29, -0.77, -0.77, -0.77]
[RLVR] all-correct or all-wrong groups have std 0, so every advantage is 0 and the prompt teaches nothing
        rlvr-math-0091   pass rate 0.31 -> train on it
        rlvr-code-0337   pass rate 0.69 -> train on it
        rlvr-if-0512     pass rate 0.56 -> train on it
        rlvr-math-0092   pass rate 1.00 -> exclude
```

Three of eight passed: mean 0.375, standard deviation 0.484, so successes get +1.29 and failures −0.77, summing to zero. **Update** with a clipped policy gradient, each token's ratio clipped to [1 − ε, 1 + ε] times its advantage. **Filter**: if all G completions pass or all fail, the standard deviation is zero and every advantage is zero; the prompt costs generation and teaches nothing. Hence the probe: `rlvr-math-0092` passed 16 of 16 and is excluded; the others sit at 0.31, 0.69 and 0.56 and stay. Refresh the probe as the policy improves: today's 0.31 is next month's 1.00.

## How it is produced and checked

Experts write problems with unique, checkable answers, or convert material into checkable form (a proof becomes "compute this number"; a coding task gets a reference implementation and tests). Each prompt gets a verifier spec and an adversarial review in which the author tries to pass it with wrong answers. The probe on the customer's checkpoint sets `use_in_batch`, and prompts are deduplicated against the customer's evaluation sets.

`validate_all.py` check **05 RLVR prompts and verifiers** asserts that `use_in_batch` is true exactly when `0 < correct < samples`, then imports `verifiers.py` and requires `reward()` to give `[1, 0, 0]`, `[1, 0]` and `[1, 0]` on the sample completions. It prints `batch filter matches the pass-rate probe; verifiers score the samples [1,0,0] [1,0] [1,0]`. A real acceptance adds a test suite per verifier with known-correct, known-wrong and adversarial answers.

## What goes wrong

- **False positives**: extraction from the reasoning instead of the answer line; tests too weak to catch a wrong program (without the `'}{'` assertion, bracket counting earns 1); guessable multiple-choice answers.
- **Exploitable harnesses.** `verify_unit_tests` appends the assertions to the candidate's code and trusts the exit code, so a completion whose code ends with `import sys; sys.exit(0)` never reaches the assertions and earns 1.0. Policies under RL find such exits. Accept only positive evidence through a channel the candidate cannot forge (exercise 4 in chapter 26d.21).
- **False negatives and ignored units**: the numeric verifier rejects "3/4" for 0.75 and ignores units, so "600 cm" fails against 6 m while "6.0 kg" passes. And **unsafe execution**: the subprocess with a timeout is not a sandbox; run model code in a container with no network and resource limits.

## Related

Chapter 26d.6 (the GRPO objective, DAPO's dynamic filter, TRL's `GRPOTrainer`, the `exit(0)` hack). Siblings: `08-reasoning/` (where hard verifiable prompts come from), `06-eval/` (the same scorer hole in `unit_tests`), `10-terminal-task/`, `11-swe-task/` and `12-agentic-gym/` (environments whose 0/1 reward feeds the same group-relative update).
