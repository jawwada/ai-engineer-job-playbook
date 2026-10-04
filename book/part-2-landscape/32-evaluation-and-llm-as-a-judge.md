# 32. Evaluation: building eval sets, LLM-as-a-judge, and quality gates

> **What you need to be able to say:** why evaluation is the core engineering discipline of LLM systems; how to build an eval set in a day; the metric families; how to build and calibrate an LLM judge (the "walk me through LLM-as-a-judge" question, chapter 39); how to evaluate agents; and how to wire evals into CI and production. Go deeper: Part 6 → *RAG evaluation guide* (47 KB), *AI/backend engineer deep dive* §5.

## 32.1 Why evaluation is the job

Prompts, models, retrieval settings and tools change weekly, and none of them throws an exception when quality drops. Without an eval set you are tuning by anecdote. With one, every change is a measured decision, cost and quality are traded explicitly, and regressions are caught before users see them. Teams that ship reliable agents spend more time on evals than on prompts.

## 32.2 Build the eval set in a day

1. **Collect 100–300 real inputs** from logs, tickets, SME interviews or user research; stratify by type (easy lookups, multi-hop, ambiguous, "no answer", adversarial, each language).
2. **Write expected outputs** or rubrics: reference answers for factual tasks; required elements and forbidden elements for open tasks; expected tool calls for agents; the correct abstention for unanswerable cases.
3. **Label a human-gold subset** (50–100) with two annotators and measure agreement; this calibrates judges later.
4. **Version it** (a table in the lakehouse, a Langfuse/LangSmith/Braintrust dataset, a JSONL in git) and add to it from every production failure.
5. **Synthesize carefully**: an LLM can generate questions from documents and rubrics from policies; review every generated item — synthetic sets drift toward what the generator finds easy.

Chapter 26d.7 shows a complete evaluation set with its scorers (execution match on several fixtures, unit tests, a rubric judge), a canary string and confidence intervals; 26d.8 shows how to aggregate subjective judgments that have no ground truth.

## 32.3 Metric families

| Task | Metrics | Notes |
|---|---|---|
| Classification / extraction | accuracy, precision, recall, F1, exact match per field, calibration | the easy, deterministic cases — automate fully |
| Retrieval | recall@k, MRR, NDCG, context precision/recall | measured before generation (chapter 18) |
| RAG answers | faithfulness/groundedness, answer relevance, correctness vs reference, citation precision, abstention correctness | judge-based with rubrics; Ragas, DeepEval, cloud evaluators |
| Generation (writing, summaries) | rubric scores (accuracy, completeness, style), pairwise preference vs baseline, edit distance from human edits | ROUGE/BLEU only as sanity checks |
| Code | tests pass, lint/type checks, pass@k, review acceptance | verifiable — the best reward signal |
| Agents | task success, tool-selection accuracy, argument correctness, steps and cost per task, policy violations, trajectory quality | τ-bench style; simulate users for conversations |
| Safety | harmful-output rate, injection success rate, PII leakage, refusal correctness | red-team suites |
| Operational | p50/p95 latency, cost per task, token usage, error/retry rate | always next to quality |

For RAG-specific evaluation — retrieval metrics with their formulas, how each RAGAS metric is computed and where it misleads, the other frameworks and benchmarks, and a practical evaluation plan — see chapter 24c.

## 32.4 LLM-as-a-judge, properly

A judge is a model prompted to score outputs against a rubric. Done well it agrees with human judgement at 80–90%+ on well-defined criteria — the MT-Bench study (Zheng et al., 2023) found GPT-4's pairwise agreement with expert humans, excluding ties, was about 85%, above the ~81% agreement between humans themselves — done badly it rewards verbosity and its own style. Note the subtlety in that number: humans disagree with each other too, so the target is "as consistent with the human panel as the humans are with each other", not 100%.

**Design:**
- **One criterion per judge call** (faithfulness; completeness; tone) with a written rubric and a scale (binary or 1–5 with anchors); multi-criteria single calls are noisier.
- **Give the judge the evidence**: the question, the retrieved context, the reference answer where one exists, the output. For faithfulness, ask it to list each claim and whether a source supports it, then score — "claim decomposition" beats a single holistic score.
- **Pairwise comparisons** (A vs B, randomized order, ties allowed) for preference-type criteria; position bias is real, so swap and average.
- **Calibrate against the human-gold subset**: measure agreement (Cohen's κ, accuracy); tune the rubric until agreement is acceptable; re-check whenever the judge model changes.
- **Use a different model family** from the one being judged where possible, or at least a different prompt, to limit self-preference bias; use a stronger model for judging than for generating when budgets allow; use a cheap model for high-volume monitoring once calibrated.
- **Known biases**: verbosity, position, self-preference, style-over-substance, leniency; mitigations: reference answers, claim-level checks, explicit penalties, swapped order, few-shot anchors, structured (JSON) verdicts, and low sampling temperature *where the model allows it*. On many 2026 frontier models you cannot set it: Claude 4.7 and later reject non-default `temperature`/`top_p`/`top_k`, GPT-5-family reasoning models do not support `temperature`, and Google recommends leaving Gemini 3 at its default of 1.0. Get consistency instead from tight rubrics and binary or anchored scales, and measure judge self-consistency by scoring each item two or three times and taking the majority — the disagreement rate is itself a useful signal of an ambiguous rubric.
- **Report** mean score with confidence intervals (bootstrap), pass rates against thresholds, and disagreement cases for human review.

**A minimal faithfulness judge prompt:**

```
You are grading whether an ANSWER is supported by the CONTEXT.
1. List each factual claim in the ANSWER.
2. For each claim, say SUPPORTED, CONTRADICTED or NOT_FOUND, citing the context sentence.
3. Output JSON: {"claims":[{"claim":..., "verdict":..., "evidence":...}], "score": supported/total}
QUESTION: ... CONTEXT: ... ANSWER: ...
```

**Tooling:** Ragas, DeepEval, promptfoo, Inspect, OpenAI Evals (read-only from 31 October 2026 and shut down on 30 November 2026; OpenAI's migration guide points to promptfoo), LangSmith and Langfuse evaluators, Braintrust, Arize Phoenix evals, MLflow LLM evaluate and Databricks Agent Evaluation (built-in judges for groundedness, relevance, safety; custom guidelines), the Gen AI evaluation service on Google's Gemini Enterprise Agent Platform, formerly Vertex AI (pointwise/pairwise, computation-based and model-based metrics), the Microsoft Foundry (formerly Azure AI Foundry) evaluation SDK (groundedness, relevance, coherence, fluency, safety evaluators, simulators), Bedrock AgentCore Evaluations (built-in and custom evaluators, DeepEval/AutoEval integrations).

## 32.5 Evaluating agents

Score **outcomes** (did the task complete correctly) and **trajectories** (were the right tools called with the right arguments in a sensible order, within budget, without policy violations). Build tasks with verifiable end states (a database row, a file, a test), use **simulated users** (an LLM playing the customer from a persona and goal) for conversational agents, replay recorded production runs with mocked tools for regression, and report pass@1 and pass^k (consistency across k runs) because agents are stochastic. Track cost and steps per task as first-class metrics.

The two consistency metrics are easy to confuse: **pass@k** is the probability that *at least one* of k attempts succeeds (it rises with k — the right metric when a human or verifier picks the best attempt), while **pass^k**, introduced with τ-bench, is the probability that *all* k attempts succeed (it falls with k — the right metric for an unattended agent that must succeed every time). An agent with pass@1 = 0.8 whose attempts were independent would have pass^8 ≈ 0.17; τ-bench reported exactly this kind of steep drop for tool-calling agents, which is the quantitative case for verification steps and deterministic workflow around the agent. Simulated users need their own sanity check: an LLM "customer" that gives up too easily or volunteers information a real one would withhold inflates success, so read a sample of simulated conversations before trusting the metric.

## 32.6 Quality gates: CI, canaries, production

- **CI**: run the eval suite on every change to prompts, models, retrieval or tools (promptfoo/DeepEval/Inspect in GitHub Actions; LangSmith/Braintrust/MLflow CI integrations); block merges on regressions beyond a threshold; report cost deltas.
- **Canary and A/B**: ship prompt/model changes to a slice; compare judge scores, user feedback and operational metrics with statistical tests; roll back automatically.
- **Production monitoring**: sample 1–5% of traffic through judges daily; alert on drops; mine failures into the eval set; review disagreements weekly with humans.
- **Human evaluation** remains the anchor: periodic calibration sets, SME review of high-stakes outputs, and user feedback (thumbs, edits, escalations) tied to traces.

### The statistics behind "it got better"

Most eval claims in interviews (and in production changelogs) do not survive a confidence interval. Four facts to have ready:

1. **Small sets cannot see small changes.** The 95% interval on a pass rate from n items is roughly ±1.96·√(p(1−p)/n): ±8 points at n = 100 and p = 0.8, ±4 points at n = 400. A 3-point "improvement" on 100 items is noise.
2. **Pair your comparisons.** Run both variants on the *same* items and test the items that flipped (McNemar's test, or a paired bootstrap). To detect an 80% → 85% improvement with 80% power, independent samples need about 900 items per variant; a paired design where ~10% of items change outcome needs about 300. Paired evaluation is the cheapest statistical power you will ever buy.
3. **Correct for the judge's own error.** If the judge passes truly good outputs with sensitivity *s* and fails truly bad ones with specificity *c* (measured on your human-gold subset), the observed pass rate *o* relates to the true rate *t* by o = t·s + (1 − t)(1 − c), so t = (o + c − 1)/(s + c − 1). A lenient judge with s = 0.95 and c = 0.70 reports 69% when the truth is 60%. Report the corrected figure, or at least the judge's s and c next to the score.
4. **Account for model stochasticity.** Re-running the same eval twice gives different numbers; estimate run-to-run variance by repeating the suite (or each item 3–5 times) and treat changes smaller than that variance as zero.

The interview sentence: "We compared variants on the same 400 items, used a paired test, corrected the judge's pass rate for its measured false-pass rate, and the improvement held at p < 0.05 — and we checked the slices so the average did not hide a regression."

## 32.7 Scenarios

- **Marketing review agents (resume use case).** Rubrics per reviewer (brand, legal, regulatory); judges calibrated against 120 human-reviewed assets; CI gate on "escapes" (violations missed) and false flags; weekly drift review.
- **Ranking model (resume use case).** Offline NDCG/AUC on held-out days, online A/B with CTR and revenue, statistical gates and rollback — the classic ML version of the same discipline.
- **Support RAG.** 250-question set with references and ACL negative cases; faithfulness, correctness, abstention and citation precision; p95 and cost per query; judge sampling in production.
- **Voice agent.** Simulated callers with accents and interruptions; task completion and order accuracy; latency percentiles; human QA on 2% of calls.

**Interview line:** *"Evaluation is how I make every change a measured decision: a versioned set of real inputs with references or rubrics, deterministic metrics where possible, calibrated LLM judges with claim-level rubrics where not, agent trajectories scored alongside outcomes, and all of it in CI and sampled in production with cost next to quality."*
