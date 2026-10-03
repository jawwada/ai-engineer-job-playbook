# 31. FinOps for AI: token economics, cost levers and how to run a cost review

> **What you need to be able to say:** where the money goes in an LLM system; the ten levers in order of leverage; how to attribute cost per feature, tenant and request; how to set budgets and alerts; and a worked optimization that cuts 60–80% without hurting quality. Chapter 39 turns this into the "how do you optimize token costs" interview answer.

## 31.1 Where the money goes

Per request: input tokens (system prompt + tools + retrieved context + history), output tokens (answer + reasoning), tool and server fees (web search, code execution), plus retrieval infrastructure (vector DB, rerankers), observability, and the people reviewing outputs. Across a system: the frontier tier's share of traffic, the number of model calls per user request (agents multiply this 5–50×), retries and fallbacks, evaluation runs, and idle provisioned capacity (PTUs, GPUs). The typical surprise: 60–80% of tokens are **input**, most of them repeated prefixes and over-long context — which is why caching and context trimming come first.

## 31.2 The levers, in order of leverage

1. **Prompt caching.** Put the stable prefix first (system prompt, tool schemas, long reference documents); cache reads cost 10% or less of input price (2.5–5% on the Anthropic frontier tiers as of 2026: \$0.25 on a \$10 input price, \$0.20 on \$4). Agents with long tool lists and multi-turn loops see 50–90% input-cost reductions. The mechanics behind that number: on Anthropic you mark up to four `cache_control` breakpoints and pay a write premium (1.25× input for a 5-minute TTL, 2× for one hour), so a prefix pays for itself from its second read; OpenAI caches automatically for prompts above about 1,024 tokens; Gemini has implicit caching plus explicit cache objects billed for storage per hour. The minimum cacheable prompt length depends on the model; on the Claude API in October 2026 it is 512 tokens for Claude Opus 5.5, Sonnet 5.5, Opus 5, Fable 5 and 5.1, and Mythos 5 and 5.1; 1,024 for Opus 4.8, Sonnet 5, Sonnet 4.6 and Sonnet 4.5; 2,048 for Opus 4.7 and Mythos Preview; and 4,096 for Opus 4.6, Opus 4.5 and Haiku 4.5. A shorter prompt marked with `cache_control` is processed without caching and without an error, so check that `cache_creation_input_tokens` or `cache_read_input_tokens` is non-zero. Watch cache TTLs and ordering — the cache is a prefix match in the order tools → system → messages, so one changed byte early (a timestamp in the system prompt, a re-ordered tool list, a per-user greeting) invalidates everything after it; measure the cache-hit ratio (`cache_read_input_tokens` ÷ total input) as a first-class metric.
2. **Model routing.** Classify difficulty (rules, a small model, or confidence from the cheap model) and send the easy 70–90% to the cheap tier; reserve frontier for hard cases and final answers. Measure quality per route on the eval set.
3. **Context engineering.** Retrieve fewer, better chunks (rerank to 5–8), trim tool outputs to what the next step needs, summarize history, drop dead tool schemas, use sub-agents with fresh windows instead of one bloated conversation.
4. **Output control.** Structured outputs instead of prose, explicit length limits, stop sequences, no "explain your reasoning" unless needed; for reasoning models, set thinking budgets per step and zero for workers.
5. **Batch APIs** for anything offline — evals, backfills, nightly classification, embeddings: 50% off.
6. **Caching responses and embeddings.** Exact and semantic caches for repeated questions (GPTCache-style, gateway caches); never re-embed unchanged chunks.
7. **Right-size the architecture.** Fewer agent hops; deterministic code for deterministic steps; a classifier instead of an LLM call where a classifier will do; distill high-volume tasks to small models (chapter 26).
8. **Self-host where volume justifies it.** Open-weight models on vLLM at steady high utilization beat per-token prices above a threshold; measure utilization and include ops cost.
9. **Provisioned capacity only when utilization is proven.** PTUs/provisioned throughput cost money while idle; use on-demand with fallbacks until traffic is steady, then commit for the base load.
10. **Stop waste.** Retry storms, loops, duplicate calls from parallel workers, logging full prompts twice, evaluation jobs on frontier tiers when a cheap judge suffices.

## 31.3 Attribution and controls

- **Tag every call** with feature, tenant, user segment, model, prompt version, route (OTel attributes; gateway metadata) and compute cost from a price table at ingestion; dashboards by feature and tenant; unit economics (cost per resolved ticket, per document, per asset) that the business recognizes. Chapter 29b works through cost per span and per trace: where to compute it (application, Collector or warehouse), the versioned price table, and how sampling distorts the totals.
- **Gateways** (LiteLLM, Portkey, Databricks Unity Gateway, Azure APIM, Cloudflare/Kong AI gateways, AgentCore Gateway) enforce budgets, rate limits and per-key spend caps, and route/fallback across providers. A budget is only as good as its enforcement point: a hard cap in the gateway stops spend; an alert on a dashboard tells you about it the next morning.
- **Budgets per run** for agents (max tokens/tool calls/dollars) and alerts on anomalies (a run 10× the median).
- **Cost in CI**: the eval suite reports cost per task next to quality; a change that improves quality by 1% and doubles cost needs a conversation.
- **Vendor levers**: committed-use discounts, enterprise pricing, data-residency multipliers (e.g., 1.1× for pinned geography on some tiers), long-context surcharges (Gemini 3.1 Pro doubles input above 200k tokens; the current Claude models do not), priority/fast tiers at roughly 2× list for latency-critical paths, and announced price changes (Gemini 3.8 Flash is scheduled to double on 1 January 2027 — budgets built on today's price need the step in them).

## 31.4 A worked optimization

Baseline: a support agent on a frontier model, 50 turns/day/agent-seat × 2,000 seats; each turn 9,000 input tokens (2,500 system+tools, 5,000 retrieved context, 1,500 history) and 400 output; price \$4/\$20 per MTok.

```
per turn: 9,000 × $4/1M + 400 × $20/1M = $0.036 + $0.008 = $0.044
per day:  100,000 turns × $0.044 = $4,400  → ~$130k/month
```

Changes: cache the 2,500-token prefix (reads at 5% on this \$4 tier: \$0.0005 instead of \$0.010); rerank context to 2,500 tokens; route 75% of turns to a \$2/\$10 model (whose cache reads are 10% of input, \$0.20/MTok); cap history at 800 tokens via summaries.

```
frontier turn: (2,500×0.05 + 2,500 + 800) × $4/1M + 400 × $20/1M ≈ $0.0137 + $0.008 = $0.0217
cheap turn:    (2,500×0.10 + 2,500 + 800) × $2/1M + 400 × $10/1M ≈ $0.0071 + $0.004 = $0.0111
blended: 0.25 × 0.0217 + 0.75 × 0.0111 ≈ $0.0138 per turn → ~$1,380/day → ~$41k/month (−69%)
```

(Cache writes are ignored above: the prefix is written once per 5-minute window per model at 1.25× input — a few dollars a day at this traffic. Note also that each lever's saving must be computed at that tier's own cache-read ratio; applying one vendor-tier ratio to another is the most common error in these calculations.)

Quality check: the eval set shows no change on resolution rate for routed turns; p95 latency drops because inputs are smaller. This is the shape of the answer interviewers want: numbers, levers, and the quality gate.

### Critic's additions: why agent costs grow quadratically, and what caching does to the curve

A chat turn sends its context once; an agent loop re-sends the whole growing transcript on every step. If a run starts with a 10k-token prefix and each step adds 3k tokens (tool call, tool result, reasoning), step *i* sends 10k + 3k × (i − 1) input tokens, so a 30-step run sends 30 × 10k + 3k × (30 × 29 / 2) ≈ **1.6M input tokens** — quadratic in the number of steps. On a \$2/\$10 model:

```
uncached:  1.6M × $2/1M                                   ≈ $3.21 per run (+ ~$0.15 output)
cached:    ~1.5M cached reads × $0.20/1M  ≈ $0.30
           + ~0.1M new tokens written × $2.50/1M ≈ $0.25    ≈ $0.55 per run (−83%)
```

The levers specific to agents follow from the formula: cache the transcript prefix every turn (frameworks that rewrite earlier messages — re-ordering tools, injecting timestamps, editing past tool results — break the cache and silently multiply cost); shrink the per-step increment (truncate tool outputs, return ids not documents); reset the curve with compaction or sub-agents that start from a clean context; and cap steps per run. Report **cost per successful task**, not cost per call — an agent that fails 30% of the time and retries is 1.4× more expensive than its per-run cost suggests.

## 31.5 Classic ML and infrastructure costs (don't forget them)

GPU utilization (batching, autoscaling to zero, spot instances for training), vector-DB sizing (dimensions × vectors × replicas; quantization), serverless vs provisioned warehouses, log volume (sampling, retention), and the human review cost that a better model can reduce. A FinOps review lists all of them with owners. Chapters 47a–47g cover the whole bill from the cloud FinOps analyst's seat: the role and finance vocabulary, billing data and native tools, forecasting and variance, allocation, tagging and anomalies, commitments and realized savings, executive reporting and the interview, and a hands-on lab.

## 31.6 Scenarios

- **Marketing automation (resume use case).** Reviewer agents ran five frontier calls per asset; moving three reviewers to a mid tier, caching the rules prefix and trimming the retrieved disclosures cut cost per asset by ~70% with identical review outcomes on the regression set.
- **Document extraction at scale.** Batch API plus a distilled small model for the easy 90%; frontier model only for low-confidence pages; cost per document tracked by layout type.
- **Agentic coding in CI.** Budget per task, sub-agents with fresh context, cheap model for exploration and frontier for the final patch; cost per merged PR as the KPI.

**Interview line:** *"I measure cost per request by feature and route, then pull the levers in order: cache the prefix, route by difficulty, shrink context, control output and thinking budgets, batch what is offline, distill the high-volume narrow tasks — and I gate every change on the eval set so savings never come out of quality."*
