# 02: Preference pairs

## What this dataset is for

Writing the ideal answer is hard; saying which of two answers is better is easier and more reliable, the way a wine judge can rank two glasses without being able to make either. A preference pair records that judgment: one prompt, two of the model's own answers, and which one people preferred. Training then moves the model toward the winning kind of answer and away from the losing kind.

This is where honesty, safety and calibrated caution get taught, because the losing answer is often fluent and plausible. In the first record below, "they don't interact, take them together" reads perfectly well and is dangerous. The question a pair answers is: *of two things the model might say, which do people want?* SFT (`01-sft/`) cannot answer it, because it only ever sees one answer.

## The example

`preference_pairs.jsonl` holds two records, `pref-02231` (a drug-interaction question) and `pref-02232` (removing duplicates from a Python list while keeping order). The first, trimmed:

```json
{"id": "pref-02231",
 "prompt": [{"role": "user", "content": "Is it OK to take ibuprofen while I'm on lisinopril?"}],
 "chosen": [{"role": "assistant", "content": "Check with your doctor or pharmacist before combining them. Ibuprofen and other NSAIDs can weaken the blood-pressure-lowering effect of ACE inhibitors such as lisinopril, and together they raise the risk of kidney problems ..."}],
 "rejected": [{"role": "assistant", "content": "Yes, that's fine. Ibuprofen and lisinopril don't interact, so you can take them together as needed."}],
 "meta": {"source_policy": "policy-v3@step1200", "chosen_sample": 2, "rejected_sample": 5,
          "annotations": [
            {"annotator": "ann_104", "preferred": "chosen", "strength": "much_better", "rationale": "Rejected answer states a false 'no interaction' claim."},
            {"annotator": "ann_117", "preferred": "chosen", "strength": "much_better", "rationale": "Chosen names the real risks and defers to a clinician."},
            {"annotator": "ann_121", "preferred": "chosen", "strength": "better", "rationale": "Correct and appropriately cautious."}],
          "aspect_scores": {"helpfulness": [4, 2], "honesty": [5, 1], "harmlessness": [5, 1]},
          "length_tokens": [96, 22], "spec_version": "pref-v2.0"}}
```

| Field | What it is and why it exists |
|---|---|
| `prompt` | the conversation so far, ending with a user turn: the context x |
| `chosen`, `rejected` | one assistant message each: the winner y_w and the loser y_l |
| `meta.source_policy` | the checkpoint that sampled both answers; on-policy pairs teach that model most |
| `meta.chosen_sample`, `rejected_sample` | sample indices, proving the two answers are different samples |
| `meta.annotations[]` | each annotator's `preferred`, `strength` and `rationale`: majority, agreement, guideline material |
| `meta.aspect_scores` | `[chosen, rejected]` per aspect; feeds per-aspect reward models and flags a winner that loses on one aspect |
| `meta.length_tokens` | `[96, 22]`: the cheapest length-bias detector |
| `meta.spec_version` | `pref-v2.0` |

The record is TRL's conversational preference type with an explicit prompt, the form `DPOTrainer` recommends; `meta` lives in a side table.

## How the model uses it

**DPO.** Compute four summed log-probabilities, the chosen and rejected answers under the policy being trained and under a frozen reference (usually the SFT model the run starts from), and minimise

`L = −log σ( β · [ (log πθ(y_w|x) − log π_ref(y_w|x)) − (log πθ(y_l|x) − log π_ref(y_l|x)) ] )`

Each bracketed difference says how much more likely the policy makes an answer than the reference did; β times it is the answer's implicit reward. `dpo_demo()` in `how_models_use_it.py` uses illustrative log-probabilities (−42 and −45 under the policy, −43 and −44 under the reference) with β = 0.1. Run `python3 how_models_use_it.py` from the lab root:

```text
[DPO] beta=0.1: implicit reward margin 0.20, loss 0.598 (loss at zero margin would be 0.693); the gradient raises chosen and lowers rejected log-probs
```

The implicit rewards are +0.10 for the chosen answer (−42 against −43) and −0.10 for the rejected one (−45 against −44), so the margin is 0.20 and the loss is −log σ(0.20) = 0.598, against ln 2 = 0.693 when policy and reference agree. The gradient scales each pair by σ(−margin), 0.45 here, so pairs the policy already orders correctly count less. A large β keeps the policy near the reference; a small one lets it travel.

**The same pairs train a reward model** for RLHF: a scalar head scores each answer and −log σ(r_w − r_l) pushes the chosen score up (see `03-reward-model/`); PPO then samples fresh answers and maximises reward minus β times the KL from the reference.

## How it is produced and checked

Sample several answers per prompt from the customer's current checkpoint (`policy-v3@step1200`), pair them, and have three or more annotators choose, state strength and write a rationale against an aspect rubric (helpfulness, honesty, harmlessness). Where a wrong answer looks right, as with the drug interaction, only domain experts can judge. The spec defines ties and what to do when both answers are bad.

`validate_all.py` check **02 preference pairs** asserts: unique ids; the prompt ends with a user turn; `chosen` and `rejected` are each a single assistant message with different content; the annotator majority prefers `chosen`; `chosen_sample` differs from `rejected_sample`. It prints `2 pairs; annotator majority agrees with the chosen side`. A real acceptance adds per-annotator agreement, a length report, aspect consistency and a check against the customer's evaluation prompts.

## What goes wrong

- **Length and style bias.** The winner is several times longer in both records (96 against 22 tokens, 71 against 24): earned here, but a set whose winners are usually longer teaches "longer is better". Compare win rates at matched lengths.
- **Both answers bad.** DPO still raises the less bad one; offer "both unacceptable" and route such prompts to SFT rewriting.
- **Off-policy pairs** from another model teach less and import its style; and **drift**, where the chosen answer's own likelihood falls while the margin grows, so watch `logps/chosen`, not only the loss.

## Related

Chapter 26d.3 (the DPO derivation, β and the reference, IPO/KTO/ORPO/SimPO, HH-RLHF). Siblings: `03-reward-model/` (the Bradley–Terry use of the same pairs), `04-rlaif/` (pairs produced by a judge model instead of people), `07-pairwise-annotation/` (what pairwise judgment looks like with no ground truth at all).
