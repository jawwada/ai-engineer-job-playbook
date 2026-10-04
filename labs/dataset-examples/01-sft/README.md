# 01: Supervised fine-tuning demonstrations

## What this dataset is for

SFT is learning by imitation. A base model can continue any text, but it does not know that it should answer rather than ramble, which format to use, when to ask a clarifying question instead of guessing, or when to call a tool. A demonstration shows it: a complete conversation in which the assistant's turns are exactly what the team wants the model to produce. Training grades the model on the assistant's lines only, never on the user's request, so the lesson is "write this, given that", not "write requests like this".

A few thousand well-chosen demonstrations set a model's defaults: tone, structure, the habit of asking back, the mechanics of tool calls. They do not teach which of two plausible answers is better (that is `02-preference/`) or how to be right where a program can check (that is `05-rlvr/`). The question an SFT record answers is: *given this context, what does a good reply look like?*

## The example

`sft_examples.jsonl` holds three chats in the OpenAI-style `messages` format: an audience rewrite (`sft-000417`), a clarify-then-answer SQL exchange with two trained assistant turns (`sft-000418`), and a tool call with its result (`sft-000419`). The first, trimmed to its shape:

```json
{"id": "sft-000417",
 "messages": [
  {"role": "system", "content": "You are an operations assistant. Write for the reader named in the request."},
  {"role": "user", "content": "Rewrite this incident note for a non-technical manager in three bullet points: \"At 02:14 UTC the primary Postgres node ran out of disk because WAL archiving to object storage had been failing since 23:50. ...\""},
  {"role": "assistant", "content": "- From 02:14 to 02:31 UTC last night (17 minutes), the app could show data but could not save changes, because the main database ran out of disk space.\n- The disk filled up because ...\n- We switched to the standby database ..."}],
 "meta": {"task_type": "rewrite_for_audience", "domain": "it_operations", "language": "en",
          "source": "synthetic_expert_edited", "author": "exp_017", "reviewer": "rev_004",
          "review_score": 5, "spec_version": "sft-v1.2", "created": "2026-09-14"}}
```

The tool-use record adds a top-level `tools` array and an assistant turn with `"content": null` and a `tool_calls` list whose `function.arguments` is a JSON-encoded string (`"{\"order_id\": \"A-1042\"}"`), followed by a `tool` turn carrying `tool_call_id: "call_1"` and the lookup result, then the grounded reply.

| Field | What it is and why it exists |
|---|---|
| `id` | stable id; the lineage record in `14-synthetic-provenance/` points at `sft-000417` |
| `tools` | OpenAI-style function definitions (`type`, `function.name`, `description`, JSON Schema `parameters`), rendered into the prompt so the model learns what it may call |
| `messages[].role` | `system`, `user`, `assistant` or `tool`; decides which tokens are trained (assistant only) |
| `content` | the text; `null` on an assistant turn that only calls a tool |
| `tool_calls[]` | `id`, `type`, `function.name`, `function.arguments` (a JSON string): the call the model must learn to emit |
| `tool_call_id` | on a `tool` turn, the call this result answers |
| `meta.task_type`, `domain`, `language` | mix balancing and evaluation slices |
| `meta.source` | provenance: `synthetic_expert_edited` here, `expert_written` on the other two |
| `meta.author`, `reviewer`, `review_score` | accountability, an independent reviewer, a 1 to 5 score to filter on |
| `meta.spec_version`, `created` | guideline version (`sft-v1.2`) and date |

## How the model uses it

Four steps. **Render**: a chat template turns the messages into one token sequence with role markers; train with the template you will serve with. **Mask**: every position's label is the next token, or −100, which the cross-entropy loss ignores; only assistant tokens keep labels, including the end-of-turn marker (emitting it is how the model learns to stop), while the role header, the system and user turns and any `tool` result are masked. **Average** `−log p(correct token | everything before it)` over the trained tokens only. **Update** for one to three epochs.

`sft_loss_mask_demo()` in `how_models_use_it.py` renders `sft-000417` with a toy template (`<|role|>` headers, an `<|end|>` marker, whitespace tokens) so the counts can be checked by hand. Run `python3 how_models_use_it.py` from the lab root; the first line is:

```text
[SFT] 148 tokens in the rendered chat, 77 carry loss (assistant reply + end marker); mean loss 0.511 nats at p=0.6, 0.105 at p=0.9
```

The system turn is 13 words plus a header and an end marker (15 tokens), the user turn 55, the assistant turn 78: 148 in all. 77 carry loss (the assistant's 76 words plus `<|end|>`, minus its header) and 71 are −100. If the model gives each correct token probability 0.6 before training and 0.9 after, the mean loss falls from −ln 0.6 = 0.511 to −ln 0.9 = 0.105 nats. In `sft-000418` both assistant turns are trained, the clarifying question as much as the final query. In `sft-000419` the trained tokens are the tool name and arguments, the end of that turn (stop and wait), and the final reply that repeats the carrier, tracking number and date from the tool result; the `tool` message itself is masked, because a model trained on tool outputs learns to invent them.

## How it is produced and checked

A versioned specification (`sft-v1.2`: task mix, style rules, when to ask or refuse, tool catalog, good and bad examples) comes first, then a pilot of 20 to 50 records reviewed with the customer, calibration of reviewers, production by screened experts who write from scratch or edit model drafts (`sft-000417` began as a generated draft that invented an alert; its lineage is `syn-30441` in `14-synthetic-provenance/`), independent review, automatic checks, a QA audit and delivery.

`validate_all.py` check **01 SFT demonstrations** asserts: unique ids; only the four roles; a `system` message only in first position; a final non-empty `assistant` message; every `tool_calls` entry names a declared tool and its `arguments` parse as JSON; every `tool` turn answers an open call id; `spec_version` present; `author` differs from `reviewer`; `review_score` in 1 to 5. It prints `3 chats; roles, tool calls and reviewer fields consistent`. Whether the content is right (no invented facts, SQL that runs, tone per spec) is for reviewers and the audit sample in `15-golden-and-qa/`.

## What goes wrong

- **Template mismatch** between training and serving degrades quality silently; **truncation that cuts the end marker** means the model never learns to stop on long answers.
- **Argument format drift**: OpenAI stores `arguments` as a JSON string, Hugging Face chat templates expect a dict, so convert before training with TRL.
- **A set that never asks back** teaches that guessing is always right; **near-duplicates** and **leaked evaluation items** (search for the canary of `06-eval/`) corrupt what the set measures.

## Related

Chapter 26d.2 (intuition, field table, TRL packing and `assistant_only_loss`, interview angle) and 26d.19.1 (the OpenAI message format). Siblings: `02-preference/` for what SFT cannot teach, `14-synthetic-provenance/` for where `sft-000417` came from, `15-golden-and-qa/` for the audit that accepts a batch of these.
