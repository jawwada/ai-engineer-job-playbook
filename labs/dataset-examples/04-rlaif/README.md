# 04: AI feedback (RLAIF)

## What this dataset is for

A strong model given written principles can compare thousands of pairs an hour, far cheaper than the annotators of `02-preference/`. But a judge model has habits: it may prefer the answer shown first, the longer one, or the one in its own style. RLAIF data therefore records the judge's verdict in **both orders**, keeps a label only when the verdict survives the swap, and sends a sample to humans, as a head chef tastes a few plates from each station.

The question this folder answers is: *how do you make a judge model's preferences trustworthy enough to train on?* A kept label is an ordinary preference pair; everything else in the record exists to earn trust in it.

## The example

`ai_feedback.jsonl` holds two items. `aif-55102` (a security-deposit question) was judged consistently and kept; `aif-55103` (naming a bakery) flipped when the order was swapped and was dropped. The kept one, trimmed:

```json
{"id": "aif-55102",
 "prompt": "My landlord hasn't returned my security deposit after 45 days. What can I do?",
 "response_a": "Rules on deposit deadlines vary by state or country, so first check your lease and the local rule ... Send a dated written request ... small-claims court ...",
 "response_b": "Your landlord is breaking the law and you can sue them for triple damages immediately.",
 "principles": ["Prefer the response that is accurate and does not overstate legal certainty.",
                "Prefer the response that gives concrete, safe next steps.",
                "Prefer the response that notes when rules depend on jurisdiction."],
 "judgments": [
   {"judge_model": "judge-large-2026-08", "template": "pairwise-v3", "order": "AB", "verdict": "A", "confidence": 0.94, "rationale": "B asserts illegality and triple damages without knowing the jurisdiction; A gives jurisdiction-aware steps."},
   {"judge_model": "judge-large-2026-08", "template": "pairwise-v3", "order": "BA", "verdict": "A", "confidence": 0.91, "rationale": "Same conclusion with the order swapped: A is accurate and actionable."}],
 "label": {"chosen": "response_a", "rejected": "response_b", "rule": "keep only if both orders agree"},
 "human_audit": {"sampled": true, "auditor": "rev_011", "verdict": "A", "agrees_with_label": true}}
```

The dropped item has `"label": null`, judgments of `A` at 0.58 in order `AB` and `B` at 0.55 in order `BA`, and `"drop_reason": "verdict flipped when the order was swapped (position bias); taste item with no clear winner"`.

| Field | What it is and why it exists |
|---|---|
| `prompt`, `response_a`, `response_b` | the pair, with fixed names that do not change when the display order does |
| `principles` | the rules the judge applies: explicit, auditable, per domain |
| `judgments[]` | `judge_model`, `template`, `order` (`AB` or `BA`), `verdict` (a response name, not a screen position), `confidence`, `rationale` |
| `label` | `chosen`, `rejected` and the rule that produced them, or `null` |
| `drop_reason` | why there is no label: yield accounting and a list of what judges cannot handle |
| `human_audit` | whether sampled, the auditor's verdict and agreement with the label |

## How the model uses it

A kept label is used exactly like a human pair, by DPO or through a reward model (see `02-preference/` and `03-reward-model/`). The consistency filter decides which items get that far. `rlaif_demo()` in `how_models_use_it.py` counts the items whose two verdicts agree and the items that carry a label; run `python3 how_models_use_it.py` from the lab root:

```text
[RLAIF] 1/2 items have the same verdict in both orders; 1 kept as preference pairs
```

In `aif-55102` the judge chose A in both orders with confidence 0.94 and 0.91, so the label is kept, and the human auditor agreed. In `aif-55103` it chose whichever option was listed first, near a coin flip (0.58, 0.55): position bias on a matter of taste. Dropping inconsistent items is stricter than averaging the two orders' preference distributions and lowers yield, but every surviving label has passed a test the judge could not game by position.

## How it is produced and checked

A judge from another model family than the policy where possible; principles per domain; a versioned template (`pairwise-v3`); both orders logged; the keep rule; a human audit, larger for low-confidence and high-stakes categories; recalibration whenever the judge, template or principles change.

`validate_all.py` check **04 AI feedback (RLAIF)** asserts: each item has judgments in exactly the orders `AB` and `BA`; `label` is present exactly when the two verdicts agree; the label's `chosen` side is the judge's winner; a dropped item carries a `drop_reason`; when a human audit was sampled, `agrees_with_label` equals whether the auditor's verdict matches the judge's. It prints `2 items; labels kept only when verdicts survive the order swap`. Acceptance of a real batch rests on the judge's agreement with human audits per batch and category.

## What goes wrong

- **Position bias** is the one bias two orders catch; **verbosity, self-preference and authority bias** survive the swap, and a **judge update** shifts all of them, so recalibrate on every change.
- **Training against the judge's taste**: rotate judges, mix in verifiable rewards (`05-rlvr/`), and keep a human holdout for evaluation; never evaluate with the judge that made the labels.
- **Audits too small to see a problem**: with ten audits, a judge that disagrees with people 5% of the time shows no disagreement 60% of the time (0.95¹⁰ = 0.60); estimating that rate within ±2 points at 95% confidence takes about 460 audits.

## Related

Chapter 26d.5 (Constitutional AI, Lee et al. on RLAIF versus RLHF, UltraFeedback). Siblings: `02-preference/` (the human version of the same record), `06-eval/` (a rubric judge with a recorded calibration), `07-pairwise-annotation/` (position bias measured on human annotators with randomised sides).
