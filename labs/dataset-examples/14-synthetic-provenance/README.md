# 14: Synthetic data and provenance

## What this dataset is for

A family tree for each generated record: which seed, model and prompt template produced it, which automatic checks it passed, who edited it and how much, and why it was accepted or rejected. Without it nobody can answer what customers, auditors and lawyers ask later: how much of this did a model write, which model, under which terms, and could it contain our evaluation set? The question a lineage record answers is: *where did this delivered record come from, and what happened to it on the way?*

## The example

`lineage.jsonl` holds two records from the same seed. `syn-30441` was generated, flagged by a fact-preservation judge, repaired by an expert and accepted as the delivered SFT chat `sft-000417` in `01-sft/`. `syn-30442` was rejected before anyone spent time on it:

```json
{"id": "syn-30441", "final_record_id": "sft-000417",
 "seed": {"topic": "incident communication", "persona": "non-technical manager", "seed_source": "topic-taxonomy-v5"},
 "generation": {"model": "generator-model-2026-07", "prompt_template": "rewrite-for-audience-v4", "temperature": 0.8, "created": "2026-09-13T10:02:11Z"},
 "automatic_checks": {"json_schema": "pass", "near_duplicate_max_cosine": 0.71, "dedupe_threshold": 0.92, "pii_scan": "pass",
                      "facts_preserved_judge": "fail: added an alert that the source never mentions"},
 "expert_edit": {"expert": "exp_017", "minutes": 7, "edit_summary": "removed the invented alert claim; restated the 17-minute window", "chars_changed": 212},
 "qa_review": {"reviewer": "rev_004", "score": 5, "decision": "accept"},
 "status": "accepted"}
```

```json
{"id": "syn-30442", "final_record_id": null,
 "seed": {"topic": "incident communication", "persona": "non-technical manager", "seed_source": "topic-taxonomy-v5"},
 "generation": {"model": "generator-model-2026-07", "prompt_template": "rewrite-for-audience-v4", "temperature": 0.8, "created": "2026-09-13T10:02:15Z"},
 "automatic_checks": {"json_schema": "pass", "near_duplicate_max_cosine": 0.96, "dedupe_threshold": 0.92},
 "expert_edit": null, "qa_review": null,
 "status": "rejected", "reject_reason": "near-duplicate of syn-30441 (cosine 0.96 > 0.92)"}
```

| Field | What it is and why it exists |
|---|---|
| `id`, `final_record_id` | links lineage and delivered data in both directions; `null` when nothing was delivered |
| `seed` | topic, persona, taxonomy version: explains and rebalances diversity |
| `generation` | model, template, temperature, time: reproducibility, licensing, debugging |
| `automatic_checks` | schema, nearest-neighbour cosine against the threshold, personal-data scan, a fact-preservation judge |
| `expert_edit` | who, minutes, what changed, characters changed: the human contribution and its cost |
| `qa_review`, `status`, `reject_reason` | independent acceptance and yield accounting |

## How the model uses it

The model never trains on lineage; the team uses it to decide what the model trains on, and to answer for it afterwards.

- **Audits.** The share of delivered records a model generated, by model and template. Each delivered record's `meta.source` must agree with its lineage: `sft-000417` reads `synthetic_expert_edited`, and the validator fails if a record with accepted lineage claims `expert_written`.
- **Contamination.** Generators reproduce what they saw, including public benchmark items; lineage lets you deduplicate generated records against every evaluation set (`06-eval/` carries a canary for exactly this search) and trace a hit to its template.
- **Licensing.** Provider terms on training with model outputs vary and some prohibit it; the `generation` block records which model, and therefore which terms, apply.
- **Dedupe.** `syn-30442` sat at cosine 0.96 from `syn-30441`, above the 0.92 threshold, and was rejected with no expert minutes spent; `syn-30441`'s nearest neighbour was at 0.71. The threshold belongs to an embedding model; re-tune it when the model changes.
- **Value of editing.** The judge flagged that the draft "added an alert that the source never mentions"; the expert removed it and restated the 17-minute window in 7 minutes, changing 212 characters. Across a project, edit minutes and characters changed show whether experts add value or rubber-stamp.

There is no `how_models_use_it.py` function for this folder; the arithmetic is one comparison, 0.96 > 0.92, and `validate_all.py` performs it.

## How it is produced and checked

A seed taxonomy (topics × personas) feeds a generator with versioned templates; automatic checks run on every output (schema, near-duplicate search against everything accepted so far, personal-data scan, faithfulness judge); survivors go to an expert editor and then a reviewer; every step writes to the lineage record. The lab's lineage belongs to the SFT set in `01-sft/`; the delivery in `13-delivery/` cites this folder for its format.

`validate_all.py` check **14 synthetic-data lineage** asserts: an `accepted` record is not a near-duplicate (`near_duplicate_max_cosine` at or below `dedupe_threshold`), has a QA decision of `accept`, points at a record that exists in `01-sft/sft_examples.jsonl`, and that record's `meta.source` is not `expert_written`; a non-accepted record is either a duplicate or carries a `reject_reason`, and its `final_record_id` is `null`. It prints `accepted record traces to sft-000417; the near-duplicate (0.96 > 0.92) was rejected`. Customers often add limits on the synthetic share or require lineage for every synthetic record.

## What goes wrong

- **Near-duplicates that slip through**: a threshold tuned on other embeddings, too loose or too tight; and **low diversity** from one template at one temperature, which dedupe hides rather than fixes (it shows the waste, not the narrowness).
- **Source labels that contradict lineage**, so a delivered record claims to be expert-written when a model drafted it.
- **Judges that miss invented facts** and **edits too light to catch them**; and **lineage lost** when records are merged, split or re-exported.

## Related

Chapter 26d.15 (licensing terms, the audit questions, interview angle). Siblings: `01-sft/` (the delivered record this lineage points at), `13-delivery/` (the manifest's `pipeline` block), `06-eval/` (the canary that dedupe should search for), `16-ops-telemetry/` (edit minutes as cost).
