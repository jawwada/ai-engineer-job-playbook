# 26. Fine-tuning: SFT, LoRA/QLoRA, preference optimization, distillation — and when not to

> **What you need to be able to say:** the four reasons to fine-tune (format/style, narrow task at scale, latency/cost, behaviour you cannot prompt), the methods and their costs, what data you need, how to evaluate, how to serve adapters, and the honest list of cases where prompting, RAG or a bigger model wins. Go deeper: Part 6 → *LLM fine-tuning guide* (40 KB) and *Modern LLM engineering guide*.

## 26.1 Why fine-tune (and the four honest reasons)

Fine-tuning changes a model's weights on your examples. It is the right tool when you want the model to **behave** differently in a consistent way: (1) a fixed output format or house style that prompting gets right only 90% of the time; (2) a narrow task at high volume where a small fine-tuned model matches a frontier model at 10–50× lower cost and latency (classification, extraction, routing, tagging, domain-specific summarization); (3) latency targets a large model cannot meet; (4) skills that are hard to specify in a prompt (a dialect, a company's coding conventions, a tool-use protocol). It is the wrong tool for injecting facts (use RAG; facts fade and cannot be updated), for the first version of anything (prompt and evaluate first), and for problems you cannot measure.

## 26.2 Methods

| Method | What changes | Data | Cost | Typical use |
|---|---|---|---|---|
| **Supervised fine-tuning (SFT)**, full | all weights | 1k–100k (input, ideal output) pairs | GPUs for hours–days; ~16 bytes per parameter with Adam in mixed precision (≈8× the BF16 weights) | large budgets, base-model adaptation |
| **LoRA** (low-rank adapters) | small rank-r matrices added to attention/MLP weights (0.1–2% of params) | same as SFT | one GPU for 7–13B models; minutes–hours | the default for everything |
| **Reinforcement fine-tuning (RFT)**, managed | policy optimized against your grader (code check, rubric judge) | a few hundred prompts + a grader | per training hour or token; vendor-hosted | OpenAI RFT on reasoning models (closed to new organizations since 7 May 2026, no new jobs from 6 January 2027), Bedrock RFT (December 2025, Nova 2 Lite first), Foundry RFT — RLVR without running the RL stack yourself |
| **QLoRA** | LoRA on a 4-bit-quantized base | same | a 70B model on one 48–80 GB GPU | budget fine-tuning of big open models |
| **Preference optimization** (DPO, ORPO, KTO, SimPO) | aligns outputs to preferences without a reward model | pairs (chosen, rejected) or binary feedback | cheap after SFT | tone, safety, helpfulness, format adherence |
| **RLHF / RL with verifiable rewards** (PPO, GRPO) | policy optimized against a reward model or verifiable checks | prompts + reward signal (tests, verifiers, judges) | expensive, unstable; expert territory | reasoning, tool use, agentic behaviours |
| **Distillation** | train a small student on a large teacher's outputs (and sometimes logits) | teacher-generated data, filtered | moderate | cheap models for a narrow task (chapter 26c covers the techniques in depth) |
| **Continued pretraining** | next-token training on domain text | GBs of raw domain text | expensive | legal/medical/code vocabularies before SFT |
| **Embedding / reranker fine-tuning** | contrastive on (query, positive, negatives) | 5k–100k triples from logs | cheap | retrieval quality in a domain |
| **Managed tuning** | vendor-hosted versions of the above | JSONL uploads | per-token training fees | OpenAI (SFT, DPO, RFT; being wound down — closed to new organizations since 7 May 2026, no new jobs for anyone from 6 January 2027, existing fine-tuned models served until their base models are deprecated), Gemini (supervised tuning; distillation in early access), Bedrock custom models (SFT, distillation, RFT), Foundry, Databricks, and open-model tuning APIs such as Thinking Machines' Tinker |

Anthropic does not offer fine-tuning of Claude weights on its own API (the one historical exception, Claude 3 Haiku fine-tuning on Amazon Bedrock from 2024, was tied to a model Anthropic retired in April 2026), and Amazon Bedrock Model Distillation is not currently available for Anthropic models either (AWS gives no timeline for its return, October 2026); Claude is tuned by prompting, examples, tools and skills — and that is often the right design for a frontier-model workflow.

### Critic's additions: LoRA versus full fine-tuning, with the 2025 evidence

The question "is LoRA as good as full fine-tuning?" now has a better answer than "usually close". Thinking Machines' "LoRA Without Regret" (September 2025) found that LoRA matches full fine-tuning for supervised fine-tuning on small-to-medium instruction and reasoning datasets, and fully matches it for policy-gradient RL even at very low rank, under two conditions: apply it to **all** layers, especially the MLP/MoE projections (attention-only LoRA underperforms even at equal parameter count), and do not starve it of capacity (rank too low for a large dataset falls off the learning curve). The optimal learning rate for LoRA was consistently about **10× higher** than for full fine-tuning (closer to 15× for short runs). Earlier work ("LoRA Learns Less and Forgets Less", 2024) showed the flip side: on large continued-pretraining-style datasets full fine-tuning learns more, while LoRA forgets less of the base model's general ability. Interview summary: LoRA on all linear layers, rank 16–64 for typical SFT sets, learning rate around 1e-4–2e-4, and full fine-tuning only when the dataset is large enough to need the capacity.

## 26.3 Data is the product

- **Quantity**: hundreds of excellent examples beat tens of thousands of mediocre ones for LoRA on a capable base; style/format tasks converge with 500–2,000; classification with a few thousand; complex generation with 10k+.
- **Quality**: deduplicate, remove contradictions, balance classes, and review a random 200 by hand; errors in training data become confident errors in production.
- **Sources**: production logs with human corrections (the best), SME-written examples, frontier-model-generated examples filtered by a judge (synthetic data; check licenses — some providers restrict training competitors on their outputs), public datasets for format.
- **Format**: chat-formatted JSONL with system, user, assistant turns; include tool calls if you tune for tools; mask loss on prompt tokens; keep a held-out set and a separate test set from a later time period.
- **Hygiene**: no secrets or PII in training data; a data card documenting provenance; versioning (DVC, lakehouse tables, Hugging Face datasets).
- **Worked examples**: chapter 26d shows a complete, tested record of every training and evaluation dataset type (SFT, preference pairs, rankings and process labels, AI feedback, RL prompts with verifiers, evaluation sets, agent environments) and how the trainer or grader reads each field.

## 26.4 Training in practice

- **Stack**: Hugging Face `transformers` + `peft` + `trl` (SFTTrainer, DPOTrainer, GRPOTrainer), `bitsandbytes` for 4/8-bit, Unsloth or Axolotl for speed and configs, DeepSpeed/FSDP for multi-GPU; Databricks Mosaic, SageMaker, tuning on the Gemini Enterprise Agent Platform (formerly Vertex AI), Azure ML for managed runs; MLflow or W&B to track.
- **Hyperparameters to know**: learning rate (LoRA ~1e-4–2e-4, full SFT ~1e-5 — the 10× ratio above), epochs (1–3; watch validation loss), LoRA rank r (8–64) and alpha (commonly 2r; rsLoRA scales by 1/√r so higher ranks stay stable), target modules (all linear layers: q,k,v,o and the MLP gate/up/down projections), sequence length, batch size with gradient accumulation, warmup, weight decay; for DPO the beta (0.05–0.5, typically 0.1).
- **Overfitting signals**: validation loss rising after epoch 1–2 while training loss keeps falling; outputs that copy training phrasing verbatim; collapse of diversity (the same opening sentence for every input). Small datasets overfit in one epoch — evaluate at checkpoints, not only at the end.
- **Compute math**: full fine-tuning memory ≈ 16 bytes × parameters (weights, gradients, Adam states in mixed precision) → 7B needs ~112 GB; LoRA keeps the base frozen (~14 GB in bf16 for 7B) plus small adapter states; QLoRA ~5–6 GB for 7B.
- **Serving adapters**: merge LoRA into base weights for simplicity, or serve many adapters on one base with vLLM/LoRAX/S-LoRA (multi-tenant: hundreds of adapters share one GPU's base weights, each adapter a few to a few hundred MB, swapped per request at a small throughput cost); managed endpoints on Bedrock, Google's Agent Platform, Foundry and Databricks handle this for you. Watch the quantization trap: an adapter trained against a BF16 base can lose accuracy when served on an INT4-quantized base (or vice versa) — evaluate in the serving configuration, not the training one.
- **Total cost, not training cost**: a LoRA run on a 7–8B model is tens of dollars of GPU time; the real costs are the labelled data, the eval harness, the serving endpoint that runs 24/7 (a dedicated GPU endpoint is roughly \$1–4 per hour, \$700–3,000 a month, whether or not traffic arrives) and re-tuning when the base model is deprecated. Compare that monthly figure with the prompted baseline's token bill before deciding.

## 26.5 Evaluation and guard against regressions

Hold out a test set from a later period; measure task metrics (accuracy/F1, exact match, rouge for summaries only as a sanity check, judge scores for open generation) **and** general-capability regressions (a small suite of unrelated tasks — fine-tuning can erase abilities), safety behaviours, and format compliance. Compare against the strongest prompted baseline at equal cost. Ship behind a flag, A/B on real traffic, keep the previous adapter for rollback.

## 26.6 Decision guide

```
Can a frontier model + good prompt + few-shot examples + tools hit the bar?  → yes: stop here.
Is the bottleneck facts/freshness?                                            → RAG, not tuning.
Is it cost or latency at high volume on a narrow task?                        → distill/SFT a small open model (LoRA), serve on vLLM or a managed endpoint.
Is it style/format consistency?                                               → SFT 500–2k examples, then DPO on preference pairs.
Is it reasoning or tool-use behaviour with a verifier?                        → managed RFT with your grader, RL with verifiable rewards (expert team), or buy a reasoning model.
Is it retrieval quality in a domain?                                          → fine-tune the embedding model and reranker on logs.
```

## 26.7 Scenarios

- **Ticket classifier at 2M tickets/month.** Frontier model labels 20k tickets (judge-checked), a 3–8B open model is LoRA-tuned to 94% agreement, served on vLLM at under \$0.0002 per ticket versus \$0.004 on the frontier tier; drift monitored monthly with a frontier spot-check. Check the arithmetic both ways: the saving is about \$7,600 a month on tokens, so a dedicated GPU endpoint at \$1,500–3,000 a month still pays back — at 200k tickets a month it would not, and a cheap-tier API model would be the better answer.
- **Clinical note style.** SFT on 1,500 clinician-edited notes gives the house format; DPO on 2,000 (edited vs original) pairs reduces verbosity; a judge measures edit rate; PHI never leaves the VPC because the model is self-hosted.
- **Domain retrieval.** 30k (query, clicked chunk) pairs from logs fine-tune BGE-M3 and a reranker; recall@10 improves from 0.71 to 0.86; no change to the generator.
- **Code conventions.** Distill a repository's conventions into a small model for inline completion while keeping the frontier model for agentic tasks.
- **Multimodal video understanding (resume-adjacent).** LoRA-tuning a vision-language model (LLaVA-NeXT-Video class) on labeled clips for a narrow film-production task where prompting a general model was inconsistent; evaluate on held-out clips with human review.

**Interview line:** *"I fine-tune when a measured prompt-and-RAG baseline cannot hit the bar on format, cost or latency — usually LoRA on a small open model for a narrow, high-volume task, with data mined from corrected production logs, a held-out set from a later period, regression checks on general ability, and adapters served behind a flag with rollback."*
