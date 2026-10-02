# 16. The model landscape: frontier, open-weight, reasoning, small — and what tokens cost

> **What you need to be able to say:** which model tier you would use for a given task and why; the difference between dense and mixture-of-experts models; what "open-weight" does and does not give you; how a thinking budget changes cost and latency; how to compute the cost of a feature per request and per month; and what quantization, speculative decoding and prompt caching buy you. Prices and names below are as of October 2026 and will change — the method does not.

## 16.1 Tiers, not brands

Every vendor ships three tiers, and routing between them is the single biggest cost lever you have:

| Tier | Anthropic | OpenAI | Google | Typical use |
|---|---|---|---|---|
| Frontier reasoning | Claude Fable 5.1 / Mythos 5.1, Claude Opus 5.5 | GPT-5.6 "Sol", GPT-5.5, the "pro" variants | Gemini 3.1 Pro | Hard multi-step reasoning, agentic coding, planning, final answers that must be right |
| Workhorse | Claude Sonnet 5.5 | GPT-5.6 "Terra", GPT-5.4 | Gemini 3.8 Flash | Most production traffic: RAG answers, tool-using agents, extraction, drafting |
| Fast/cheap | Claude Haiku 4.5 | GPT-5.6 "Luna", GPT-5.4 mini/nano | Gemini 3.x Flash-Lite | Classification, routing, guardrail checks, bulk extraction, sub-agents |

Three facts shape every design: the frontier tier costs 5–25× the cheap tier per token; the cheap tier is roughly as good as the frontier tier was two years ago; and most requests in a real system are easy. A router (rules, a small classifier, or the cheap model itself judging difficulty) that sends 80% of traffic to the cheap tier and 20% to the frontier tier typically cuts cost by 60–75% with no measurable quality loss on an eval set — which is why interviewers ask about it (chapter 31). Anthropic's own guidance in 2026 is to start on Opus 5.5 and move up to Fable 5.1 only when evals on Opus fall short; the same logic — start one tier below the top, climb on evidence — applies to every vendor.

## 16.2 Current prices (October 2026) and the cost formula

Anthropic's published list prices, per million tokens (MTok):

| Model | Input | Output | Cache write (5 min / 1 h) | Cache read | Batch input / output |
|---|---|---|---|---|---|
| Claude Fable 5.1 / Mythos 5.1 | $10 | $50 | $12.50 / $20 | $0.25 | $5 / $25 |
| Claude Opus 5.5 | $4 | $20 | $5 / $8 | $0.20 | $2 / $10 |
| Claude Opus 5 / 4.8 / 4.7 | $5 | $25 | $6.25 / $10 | $0.50 | $2.50 / $12.50 |
| Claude Sonnet 5.5 / 5 | $2 | $10 | $2.50 / $4 | $0.20 | $1 / $5 |
| Claude Haiku 4.5 | $1 | $5 | $1.25 / $2 | $0.10 | $0.50 / $2.50 |

Google's Gemini API (paid tier): Gemini 3.8 Flash $0.75 in / $3.75 out (announced to rise to $1.50 / $7.50 on 1 January 2027), Gemini 3.5 Flash $1.50 / $9.00, Flash-Lite tiers $0.25–0.30 in / $1.50–2.50 out, Gemini 3.1 Pro Preview $2 in / $12 out for prompts up to 200k tokens and $4 / $18 above; context caching at a tenth of input price plus hourly storage; batch at 50% off; the Live (speech-to-speech) models are priced per audio minute. OpenAI (as of August 2026 — verify on platform.openai.com/docs/pricing): GPT-5.6 Sol $5 in / $30 out, GPT-5.6 Terra $2 / $12, GPT-5.6 Luna $0.20 / $1.20, GPT-5.4 $2.50 / $15 with mini at $0.75 / $4.50 and nano at $0.20 / $1.25, "pro" variants at $30 / $180; cached input at a tenth, batch at half, and a priority/"fast" tier at roughly twice list. Open-weight models through hosts like Together, Fireworks, Groq or DeepSeek's own API run $0.10–$2 per MTok (DeepSeek V4 Flash is around $0.22 / $0.66 off-peak on DeepSeek's API), and on your own GPUs the price is your utilization.

Two pricing shapes to notice. Claude 4.6 and later (and the 5.x family) bill the full 1M-token window at the standard rate, so a 900k-token request costs the same per token as a 9k one; Gemini 3.1 Pro doubles its input price above 200k tokens. And server-side tools carry their own line: web search is $10 per 1,000 searches on the Claude API (also on Claude Managed Agents), code execution has a free monthly allowance and then an hourly container fee, and the clouds bill knowledge-base queries and guardrail evaluations separately from tokens.

**The formula.** For one request:

```
cost = (uncached_input × p_in) + (cached_input × p_cache_read) + (cache_writes × p_cache_write)
     + (output_tokens × p_out) + (thinking_tokens × p_out) + tool/search fees
```

Thinking (reasoning) tokens are billed as output. A worked example for a RAG answer on Sonnet 5.5: 2,000-token system prompt and tool definitions (cached), 6,000 tokens of retrieved context, 300-token question, 500-token answer, no thinking:

```
uncached input: 6,300 × $2/1M     = $0.0126
cached read:    2,000 × $0.20/1M  = $0.0004
output:           500 × $10/1M    = $0.0050
total ≈ $0.018 per request → 100,000 requests/day ≈ $1,800/day ≈ $54k/month
```

The same request on Haiku 4.5 is about $0.009; routing 80% of them there gives ≈ $27k/month. Adding a 4,000-token thinking budget on Opus 5.5 for the hard 20% adds 20,000 × 4,000 × $20/1M = $1,600/day; the same budget on Fable 5.1 ($50 output) is $4,000/day. Put numbers like these in interviews; vague "it depends" answers lose to a napkin calculation every time.

**Four discounts you must know.** Prompt caching (repeated prefixes — system prompt, tool schemas, long documents — are re-read at 10% or less of the input price, 2.5–5% on the Anthropic frontier tiers; writes cost 1.25× for a 5-minute TTL and 2× for an hour, so a prefix pays for itself on its second read; order your prompt so the stable part comes first); batch APIs (50% off for asynchronous jobs: evals, backfills, nightly classification); tier routing (above); and output control (shorter answers, structured outputs instead of prose, stop sequences, max_tokens). Context-window surcharges above 200k tokens exist on some models and not on others — check before you design around a 1M window.

## 16.3 Open-weight models: what you get and what you owe

"Open-weight" means the weights are downloadable under a license; it rarely means the training data or full recipe is open. The 2026 field, as of the latest comparisons (verify sizes and licences before quoting them — they change monthly): DeepSeek V4 (MIT; the 1.6T-parameter MoE "Pro" with ~49B active, GA August 2026, and the 284B/13B "Flash", GA July 2026, both with 1M context, plus an experimental Flash Vision variant); Qwen 3.8 (Apache-2.0 for the downloadable sizes — the 27B dense model fits a 24 GB GPU at 4-bit, about 17 GB in Q4_K_M; the 2.4T sparse-MoE Qwen3.8-Max was hosted-only as of mid-2026); Meta Llama 4 Scout and Maverick (17B active, 109B and 400B total, Llama community license, very long context on Scout); Mistral Small 4 (March 2026; 119B sparse MoE, Apache-2.0, one model replacing the separate reasoning, vision and coding lines) and Medium 3.5; Z.ai GLM-5.3 (744B/40B active, a bespoke revenue-gated license) and GLM-5.3-Flash (320B/18B active, plain MIT, multimodal, roughly a ninth of the price), both strong at long agentic coding tasks; Moonshot Kimi K2.x and K3 (1T–2.8T MoE; K3's weights shipped July 2026 — check its licence terms, the K2 line used a modified MIT with commercial conditions); OpenAI gpt-oss-20b and gpt-oss-120b (Apache-2.0; the 120b runs on a single 80 GB GPU); Google Gemma 4 (April 2026, Apache-2.0: E2B and E4B for devices, a 26B MoE with 3.8B active, a 31B dense with 256k context, all multimodal); Microsoft Phi-4 variants. Capability-wise the best open models trail the frontier closed models by months, not years, on most benchmarks, and lead on price.

**What you get:** data stays in your VPC (the usual reason), no per-token bill at high volume, full control over versions (no silent model updates), fine-tuning on your data, and latency you can engineer. **What you owe:** GPUs and capacity planning, an inference stack (vLLM/SGLang/TensorRT-LLM), model ops (updates, evals, safety), and the engineering time to match managed-API reliability. Rule of thumb from procurement conversations: self-hosting wins on cost above roughly a few hundred million tokens a day of steady traffic or when policy forbids external APIs; below that, managed APIs win on total cost of ownership. The arithmetic behind the rule: one H100 (about $2–3 per hour on demand in 2026) serving an 8B model with vLLM at a few thousand output tokens per second aggregate yields roughly $0.10–0.30 per million tokens *at full utilization*; at 20% utilization the same tokens cost five times that, which is where a $0.20–1.00 hosted price wins. A 70B model needs two to four GPUs and ten times fewer tokens per second, so its break-even volume is correspondingly higher.

**Licenses to recognize:** Apache-2.0 and MIT (do anything, keep the notice), Llama community license (free up to a very large user threshold, naming requirements), Gemma terms (Apache-2.0 since Gemma 4; earlier Gemma versions had their own terms), "modified MIT"/custom with revenue clauses (Kimi K2, GLM-5.3, Mistral Medium) — legal reads these before a production deployment, and you should know they exist. Also check the *output* terms of the closed APIs you distil from (chapter 26b).

## 16.4 Architecture words that come up

- **Dense vs mixture-of-experts (MoE).** A dense model uses all its parameters for every token; an MoE model has many expert feed-forward blocks and a router that activates a few per token (e.g., 17B active of 400B total, or 49B of 1.6T in DeepSeek V4 Pro). MoE buys more knowledge per FLOP of inference; the cost is memory (all experts must be loaded — 1.6T parameters is 1.6 TB at FP8, i.e. a multi-node deployment even though each token touches 3%), load-balancing between experts, and serving complexity (expert parallelism, all-to-all communication). Most frontier and large open models are MoE now; the small on-device models are mostly dense.
- **Attention variants you will be asked about.** Grouped-query attention (GQA) shares key/value heads across query heads to shrink the KV cache (Llama 3 70B uses 8 KV heads for 64 query heads); multi-head latent attention (MLA, DeepSeek) compresses keys and values into a low-rank latent and cuts cache memory by an order of magnitude; sliding-window and hybrid local/global attention (Gemma, Mistral) bound memory on long inputs; FlashAttention is the kernel that makes any of them fast. The KV cache, not the weights, is what limits concurrency at long context.
- **Context window and effective context.** 200k–1M tokens is standard; effective use degrades with position and clutter ("lost in the middle"), so retrieval and context engineering still matter. Long context is also expensive: input tokens are billed every turn unless cached, and prefill of a 500k-token prompt takes tens of seconds even on a frontier API.
- **Reasoning / thinking models.** The model generates hidden or visible chains of thought before answering; you control a *thinking budget* (tokens) or an effort level (`thinking` with `budget_tokens` or an effort setting on Claude — adaptive and always on for Fable 5.1 and Opus 5.5, opt-in on Haiku 4.5; `reasoning.effort` on OpenAI; `thinking_config` on Gemini). More thinking raises accuracy on hard problems and raises latency and cost linearly; a good router spends it only where needed. "Latent reasoning" refers to reasoning in the model's hidden state (recurrent depth, looped layers) rather than in emitted tokens; it is a research direction and an interview topic (chapter 39).
- **Tokenizers.** Byte-pair or SentencePiece tokenizers; ~0.75 words per token in English, worse for code, non-Latin scripts and numbers. Token counts drive cost and context limits; count them (vendor token-count endpoints, `tiktoken`, the Anthropic token counting API) rather than guessing.
- **Multimodal natively vs bolted-on** (chapter 19): native models (Gemini, Claude, GPT, Qwen-VL, Llama 4) consume images, audio or video as tokens; the older pattern bolts a vision encoder onto an LLM with a projector.
- **State-space and hybrid models** (Mamba, Jamba, hybrid attention) trade attention's quadratic cost for linear-time sequence modelling; they appear in long-context and edge use cases (chapter 17).
- **Distillation and small models.** Teaching a small model with a large model's outputs (and sometimes logits) is how the cheap tiers get good; you can do the same for a narrow task (chapter 26).

## 16.5 Serving an open model: the vocabulary

- **Engines:** vLLM (PagedAttention for KV-cache memory, continuous batching, prefix caching, OpenAI-compatible server — the default); SGLang (RadixAttention prefix sharing, fast structured outputs); TensorRT-LLM (NVIDIA kernels, best raw throughput, more setup); llama.cpp and Ollama (CPU/Apple-silicon/consumer GPUs, GGUF format); TGI; MLX.
- **Quantization:** FP16/BF16 (full), FP8 (near-lossless on Hopper/Blackwell), INT8, INT4 (AWQ, GPTQ, GGUF Q4_K_M) — 4-bit roughly quarters memory and costs a few points of accuracy; NF4 for QLoRA training. Rule: quantize weights first, KV-cache second, and always re-run the eval set.
- **Throughput levers:** continuous batching, KV-cache reuse (prefix caching), speculative decoding (a draft model proposes tokens, the big model verifies), tensor/pipeline parallelism across GPUs, MoE expert parallelism, chunked prefill, and disaggregated prefill/decode.
- **Capacity math:** memory = weights + KV cache + activations/overhead (~10–20%); weights = parameters × bytes per parameter (2 in BF16, 1 in FP8, ~0.5 in INT4); KV cache per token = 2 (K and V) × layers × kv_heads × head_dim × bytes. Worked numbers: Llama-3-class 8B (32 layers, 8 KV heads, head_dim 128, BF16) = 2 × 32 × 8 × 128 × 2 ≈ 131 KB per token, so a 32k-token context costs ~4 GB per sequence on top of ~16 GB of weights; the 70B (80 layers, 8 KV heads) ≈ 328 KB per token, so a 128k context is ~42 GB per sequence on top of 140 GB of BF16 weights (two H100s) or ~40 GB at 4-bit. Concurrency = (GPU memory − weights) ÷ (KV per token × average context), which is why FP8 KV caches, MLA and short contexts raise throughput more than any kernel trick. Interviewers like this question because it separates people who have deployed from people who have read.
- **Latency math:** time ≈ time-to-first-token (prefill, roughly proportional to input length) + output tokens ÷ decode rate. Typical 2026 figures: frontier APIs stream 50–150 tokens/s per request with 0.5–2 s TTFT on a few thousand input tokens; wafer-scale and LPU hosts (Cerebras, Groq) reach 500–2,000 tokens/s on open models; a 500-token answer therefore takes 4–10 s on a standard API and under a second on the fast hosts. Thinking tokens add to the output side at the output price, so a 4k-token thinking budget adds 30–80 s on a 100 tokens/s stream — budget thinking per step, never globally.

## 16.6 Benchmarks and how to read them

Headline benchmarks in 2026: MMLU-Pro and GPQA Diamond (knowledge and reasoning), Humanity's Last Exam, AIME/HMMT (math), SWE-bench Verified and Terminal-Bench (software engineering agents), τ²-bench (tool-using agents with users), BrowseComp (web research agents), ARC-AGI-2/3 (abstraction), MMMU and Video-MME (multimodal), LMArena (human preference Elo), Artificial Analysis (price/speed/quality index). Read them with four cautions: contamination and saturation (a 95% score tells you nothing; MMLU and GSM8K are no longer informative), agentic benchmarks depend heavily on the harness (the same model scores ten points apart under two scaffolds), vendor-reported numbers use different sampling budgets (pass@1 at temperature 0 versus best-of-n with tools), and none of them is your workload. The right answer to "which model is best" is "on our eval set, X, by this margin, at this cost" — and chapter 32 shows how to build that set in a day.

### Critic's additions: the questions behind "which model"

- **"Why not always the frontier model?"** Latency and cost scale with the tier, and the eval set rarely shows a difference on the easy 80%. Say the number: on the RAG example above the frontier path is 2× the workhorse path and 10× the cheap path per request.
- **"How do you handle a model deprecation?"** Dated IDs in config, a gateway alias, the eval suite re-run on the candidate, a canary at 5% of traffic, and a prompt-caching check (cache keys change with the model).
- **"What breaks when you switch vendors?"** Tool-schema details (strictness, nested enums), system-prompt sensitivity, tokenizer differences (same text, different token count and therefore cost), structured-output guarantees, and safety-filter thresholds — all of which the eval set must cover.
- **"When would you self-host?"** Policy (data cannot leave), volume (steady hundreds of millions of tokens a day), latency you must engineer (speculative decoding, pinned GPUs), or fine-tuned weights you cannot upload. Otherwise rent.
- **"What is the KV cache?"** The per-token keys and values each layer keeps so that decoding does not recompute attention over the whole prompt; it is why prefix caching exists and why long contexts limit concurrency.

## 16.7 Choosing a model: a short procedure

1. Write ten representative tasks with expected outputs (the seed of your eval set).
2. Run them on one model per tier from two vendors; measure accuracy, latency (p50/p95), cost per task.
3. Pick the cheapest tier that meets the bar; route the rest up.
4. Decide managed vs self-hosted on data policy and volume, not on fashion.
5. Pin versions (dated model IDs), keep a fallback model behind a gateway, and re-run the eval set when either changes.

**Interview line:** *"I start from an eval set, not a leaderboard. Then I route: a cheap tier for the easy majority, a frontier tier with a bounded thinking budget for the hard minority, prompt caching for the stable prefix, batch for anything offline — and I can show the cost per request for each path."*
