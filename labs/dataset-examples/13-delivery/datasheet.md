# Datasheet: support-intents-v1 (example delivery)

Structured after "Datasheets for Datasets" (Gebru et al.). One page per delivery; the client's reviewers read this before they open the data.

## Motivation
- **Purpose:** train and evaluate an intent classifier with entity extraction for a home-goods store's support inbox.
- **Requested by:** the client's applied-AI team. **Produced by:** the data-production team under spec `intent-v1.3`.

## Composition
- **Records:** 4 in this example (a real delivery has thousands). One record = one customer message with one intent label and zero or more entity spans.
- **Labels:** `billing_refund`, `update_address`, `shipping_policy`, `cancel_order` (definitions and tie-break rules in the spec, rule 4 for cancel versus exchange).
- **Entities:** `order_id`, `address`, `country`; `start` and `end` are Python string offsets into `text` (end exclusive).
- **Splits:** `train` only in this example; real deliveries add `validation` and a held-back `test` split.
- **Sensitive data:** messages were written by contractors from templates; no real customer data, no personal data.

## Collection and labeling
- Messages written by contractors from 40 scenario templates, then paraphrased by a generator model and edited by experts (lineage in `14-synthetic-provenance`).
- Each record labeled by one annotator and reviewed by a second; disagreements adjudicated by a lead.
- Quality controls: gold questions at 5% of tasks (annotator accuracy at least 90% to stay on the project), a 2% random audit per batch, and lot acceptance at most 2 defects in an 80-record audit sample (see `15-golden-and-qa`).

## Uses
- **Intended:** supervised training and evaluation of intent and entity models.
- **Not intended:** estimating real customer intent frequencies (the class mix is balanced by design).

## Distribution and maintenance
- Delivered as JSONL (source of truth) and CSV (flattened; entities as a JSON string column), with `manifest.json` holding record counts and SHA-256 checksums.
- Versioned as `support-intents-v1`; corrections ship as a new version with a changelog, never as silent edits.
