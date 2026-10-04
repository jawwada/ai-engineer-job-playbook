# 15: Golden sets, gold questions, QA audits and acceptance sampling

## What this dataset is for

Two controls on the people who make labels. **Gold questions** are items with known answers slipped unannounced into annotators' queues, like a proctor's spot check; they measure each person. The **QA audit** is an inspector re-checking a random sample of finished work; it measures the batch, and a sampling plan turns its result into accept or reject with known risks. The question this folder answers is: *which annotators can stay on the project, and can this batch ship?*

## The example

Three files. `golden_set.jsonl` holds four intent items with expert-consensus labels; `gold_question_results.csv` holds four annotators' accuracy on gold; `qa_audit_sample.csv` holds ten rows of an auditor's re-labeling of batch 07 (the delivery manifest in `13-delivery/` records the full audit as 1 defect in 80).

```json
{"id": "gold-004", "text": "Stop my order, I bought the wrong size", "label": "cancel_order", "explanation": "'stop my order' means cancel; exchange intent is secondary under rule 4 of the spec", "consensus": "2/3 experts, adjudicated", "spec_version": "intent-v1.3"}
```

```csv
annotator_id,gold_seen,gold_correct
ann_301,40,39
ann_302,38,36
ann_303,41,33
ann_304,40,40
```

```csv
batch,record_id,delivered_label,auditor_label,defect,note
batch-07,cs-1219,cancel_order,cancel_order,false,
batch-07,cs-1240,shipping_policy,update_address,true,asked to reroute a parcel
batch-07,cs-1251,update_address,update_address,false,
```

| Field | What it is and why it exists |
|---|---|
| gold `text`, `label`, `explanation` | the item, its answer, and the reason citing the spec: trains annotators and settles disputes |
| gold `consensus` | "3/3 experts" or "2/3 experts, adjudicated": how sure the answer is |
| gold `spec_version` | gold answers change when guidelines do |
| `gold_seen`, `gold_correct` | per-annotator accuracy and the evidence behind it |
| audit `batch`, `record_id` | traceability to delivered data |
| `delivered_label`, `auditor_label`, `defect`, `note` | the comparison that drives acceptance |

## How the model uses it

No model trains on these files; they decide which labels reach a model. **Screening**: gold accuracy is 97.5% (`ann_301`), 94.7% (`ann_302`), 80.5% (`ann_303`) and 100% (`ann_304`); against the manifest's 90% floor, `ann_303` is flagged. Put intervals on it first: 33 of 41 has a 95% Wilson interval of 0.660–0.898, so `ann_303` is below the floor with reasonable confidence, while `ann_302`'s 36 of 38 (0.827–0.985) is consistent with being above it. Then review the misses against the explanations, retrain, re-test on fresh gold, and remove them if accuracy stays low. **Auditing**: `cs-1240` was delivered as `shipping_policy` but asks to reroute a parcel, which is `update_address`: one defect.

**Accepting.** A single sampling plan with n = 80 and c = 2 accepts a lot when the sample holds at most 2 defects. For a true defect rate p, `P(accept) = Σ_{k=0..c} C(n, k) · p^k · (1 − p)^(n−k)`, the plan's operating characteristic. `acceptance_demo(n=80, c=2)` in `how_models_use_it.py` computes it; run `python3 how_models_use_it.py` from the lab root:

```text
[QA] audit 80 records, accept the batch if at most 2 defects; P(accept) by true defect rate: {'0.5%': 0.992, '1.0%': 0.953, '2.0%': 0.784, '3.0%': 0.568, '5.0%': 0.231, '8.0%': 0.04}
```

A good lot with 1% defects is rejected 4.7% of the time (the producer's risk); a bad lot with 5% defects is accepted 23.1% of the time, and an 8% lot 4% (the consumer's risk). If 5% lots must almost never pass, this plan is too loose: n = 105, c = 2 accepts a 5% lot 9.9% of the time; n = 200, c = 5 reaches 6.2%. Larger samples buy both protections. The golden set also trains new annotators, regression-tests pre-labelers and judges, and serves as a small evaluation set, so it stays out of training data.

## How it is produced and checked

Experts label gold items independently and keep unanimous ones (adjudicated items like `gold-004` only with an explanation citing the spec); gold is mixed into queues at a fixed rate (5% in the datasheet), disguised and refreshed; audits sample each batch at random (2% in the datasheet) by people outside production; the plan is agreed with the customer before production.

`validate_all.py` check **15 golden set, gold questions and QA audit** asserts: every gold label is in the delivery manifest's intent enum and has an explanation; annotators whose `gold_correct / gold_seen` is below the manifest's `gold_accuracy_min` (0.9) are listed; each audit row's `defect` is `true` exactly when `delivered_label` differs from `auditor_label`. It prints `4 gold items; below the 90% gold floor: ['ann_303']; audit sample 1/10 defects`.

## What goes wrong

- **Recognisable gold**, learned and passed by annotators whose real work is poor; **gold too easy or too ambiguous**; gold counts too small to judge without intervals.
- **Audits by the production team**, or chosen rather than random samples.
- **Plans nobody computed**: "at most 2 in 80" sounds strict and accepts a 5% lot almost a quarter of the time.

## Related

Chapter 26d.16 (operating characteristics, ISO 2859-1, interview angle) and exercise 7 in 26d.21. Siblings: `13-delivery/` (the manifest whose `quality` block this folder substantiates), `07-pairwise-annotation/` (gold on a subjective task, and agreement where no gold exists), `16-ops-telemetry/` (rejected work as cost).
