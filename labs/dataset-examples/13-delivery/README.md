# 13: The delivery package

## What this dataset is for

Shipping a dataset is like shipping parts to a factory: a packing list with counts and checksums (the manifest), a specification sheet that says what the parts are and are not for (the datasheet), and an inspection rule the receiver applies before signing. The customer should be able to verify everything without taking anyone's word. The question this folder answers is: *what does the customer actually receive, and how do they check it before a single record enters a training job?*

## The example

Four files: `train.jsonl` (the source of truth), `train.csv` (a flattened mirror), `datasheet.md` (one page after *Datasheets for Datasets*), and `manifest.json`. The records are four support messages labeled with an intent and entity spans for a home-goods store's inbox. One record from `train.jsonl` and the same row in `train.csv`:

```json
{"id": "cs-0001", "text": "I was charged twice for order 7731, can you refund one?", "intent": "billing_refund", "entities": [{"type": "order_id", "value": "7731", "start": 30, "end": 34}], "language": "en", "split": "train"}
```

```csv
id,text,intent,entities_json,entity_count,language,split
cs-0001,"I was charged twice for order 7731, can you refund one?",billing_refund,"[{""type"": ""order_id"", ""value"": ""7731"", ""start"": 30, ""end"": 34}]",1,en,train
```

The manifest, trimmed:

```json
{"dataset": "support-intents", "version": "v1", "spec_version": "intent-v1.3", "created": "2026-09-30",
 "records": {"train": 4},
 "schema": {"id": "string", "text": "string",
            "intent": "enum[billing_refund, update_address, shipping_policy, cancel_order]",
            "entities": "list[{type, value, start, end}]", "language": "string (BCP 47)", "split": "enum[train, validation, test]"},
 "files": {"train.jsonl": {"sha256": "78a8f5d1e3247d6aa06bab14a71da4c7e86dad78388d73b1beff1fd69e9baee0", "bytes": 852},
           "train.csv": {"sha256": "0a75726297b3ed585b4a2cea08eee6671407868e9ed4e0b43de0bd9b5fc4dd77", "bytes": 684},
           "datasheet.md": {"sha256": "aaeeb85082fdca7f3a4bd6f8748f506af0e80a783b823e0bcd4da315177e4b4b", "bytes": 2144}},
 "quality": {"audit_sample": 80, "audit_defects": 1, "acceptance_rule": "accept if defects <= 2 in 80", "gold_accuracy_min": 0.9},
 "pipeline": {"generator_model": "generator-model-2026-07", "prompt_template": "support-message-v2", "editor_pool": "experts-en-retail"}}
```

| Field | What it is and why it exists |
|---|---|
| `dataset`, `version`, `spec_version`, `created` | which data, under which guidelines, when |
| `records` | counts per split, the first thing a loader checks |
| `schema` | each field's type, including the intent enum and entity spans: the contract the files must meet |
| `files` | per file, `sha256` and `bytes`: proof the files are complete and unmodified |
| `quality` | audit sample, defects, acceptance rule, gold accuracy floor (used by `15-golden-and-qa/`) |
| `pipeline` | generator model, prompt template, editor pool (lineage format in `14-synthetic-provenance/`) |
| `entities[]` | `type`, `value`, and Python string offsets, end exclusive: "7731" is `text[30:34]` |
| `entities_json`, `entity_count` | the CSV's flattened entities and a count for quick checks |
| `datasheet.md` | motivation, composition, collection and labeling, uses, distribution: the reviewer's questions answered before the data is opened |

## How the model uses it

The model never sees the manifest; the customer's pipeline does, in order. **Verify integrity**: recompute each file's SHA-256 and size (`shasum -a 256 train.jsonl` must print `78a8f5d1…` and the file must be 852 bytes); a mismatch means a truncated download, a corrupted copy or a silent edit, and nothing else is checked until it passes. **Load**: JSONL is the source of truth, the CSV a mirror; check counts against `records`, types against `schema`, and that every span reproduces its value. **Read the datasheet**: intended use (training and evaluating an intent and entity model) and unintended use (estimating real intent frequencies, because the class mix is balanced by design). **Apply the acceptance rule**: 1 defect in an 80-record audit is within "at most 2 in 80", so the lot is accepted. **Pin the version**, so every training run traces to exact files; corrections arrive as a new version with a changelog, never as silent edits. Only then does `train.jsonl` go to a classifier's training loop as ordinary supervised data.

There is no `how_models_use_it.py` function for this folder; the computation that matters is the checksum, and `validate_all.py` performs it.

## How it is produced and checked

An export job writes JSONL from the accepted records, derives the CSV from it, validates both against the schema, computes counts and checksums last and writes the manifest; the project lead writes the datasheet. The package goes to an access-controlled location, with the manifest sent separately so a tampered package cannot carry a matching one. The datasheet records the controls: gold questions at 5% of tasks with a 90% accuracy floor, a 2% random audit per batch, and lot acceptance at most 2 defects in 80.

`validate_all.py` check **13 delivery package (JSONL, CSV, datasheet, manifest)** asserts: every file in `manifest.files` has the listed SHA-256 and byte size; the record count equals `records.train`; every intent is in the schema's enum and every split is `train`; every entity's `text[start:end]` equals its `value`; and the CSV mirrors the JSONL row for row (`text`, `intent`, parsed `entities_json`, `entity_count`). It prints `3 checksums match; 4 records; entity offsets exact; CSV mirrors JSONL`. Editing any of the three files, even a trailing newline, changes a checksum and fails the check, which is the point.

## What goes wrong

- **CSV quoting, line endings and encodings**: commas and quotes force quoting with inner quotes doubled (RFC 4180); the CSV ends rows with CRLF as RFC 4180 specifies, JSONL with `\n`; tools that "fix" either change the checksum. **Spreadsheets** strip leading zeros and rewrite dates and long ids.
- **Offsets in the wrong unit**: Python counts code points, JavaScript UTF-16 code units, many tools UTF-8 bytes; they agree only on ASCII, so the schema must say which.
- **A manifest sent with the package** rather than separately, and **silent corrections** that leave two files with the same version and different checksums.

## Related

Chapter 26d.14 (the customer's five-step verification, Gebru et al.'s datasheet sections) and 26d.19 (JSONL, CSV, Parquet, Croissant). Siblings: `14-synthetic-provenance/` (the `pipeline` block's lineage), `15-golden-and-qa/` (the `quality` block's evidence and what "2 in 80" guarantees), `16-ops-telemetry/` (what each accepted record cost).
