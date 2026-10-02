# 39. Technical interview topics with model answers

> **The idea:** five questions recur in every Applied AI / FDE loop in 2026 — FinOps, observability troubleshooting, agentic design with reasoning, LLM-as-a-judge, and security/IAM. Each gets a model answer here in the shape interviewers reward: headline, structure, numbers, trade-offs, and what you would measure. A second set of shorter answers covers the next twenty questions. Say these out loud until they are yours, then replace the examples with your own.

---

## 39.1 FinOps — "Our token costs are out of control. How do you find out why and bring them down?"

**Headline.** "I instrument first, then pull the levers in order of leverage — caching, routing, context, output control, batching, distillation — and I gate every change on the eval set so savings never come out of quality."

**Find out why (one day).** Every model call already carries, or will carry, OpenTelemetry attributes: feature, route, model, prompt version, input/output/cached/reasoning tokens, latency. Join with a price table and you get cost per request by feature and by route. In my experience the picture is always the same: 60–80% of spend is input tokens, most of them repeated prefixes (system prompt, tool schemas, policy documents) and over-long retrieved context; agent loops multiply calls 5–50×; a frontier model serves traffic a cheap model could handle.

**Bring it down (two weeks).**
1. *Prompt caching:* reorder prompts so the stable prefix comes first; cached reads cost 10% of input price on Anthropic models and on Gemini 2.5 and later models (Google's October 2025 update; older material quotes 25% for 2.5), plus an hourly storage charge for explicit Gemini caches — typically 40–70% off input cost for agents with long tool lists.
2. *Routing:* a difficulty classifier (rules, a small model, or confidence from the cheap model) sends 70–90% of traffic to a Haiku/Flash-tier model; frontier only for hard cases and final answers; measured per route.
3. *Context engineering:* rerank to 5–8 chunks, trim tool outputs to what the next step needs, summarize history, drop unused tool schemas; sub-agents with fresh context instead of one bloated conversation.
4. *Output control:* structured outputs, length limits, no narration; thinking budgets only on planner and evaluator steps, zero for workers.
5. *Batch APIs* (50% off) for evals, backfills and nightly jobs; response and embedding caches for repeats.
6. *Distill* high-volume narrow tasks to a small fine-tuned model; *self-host* only above the volume threshold where utilization is proven.

**Worked number.** Support agent, 100k turns/day, 9k input and 400 output tokens on a $4/$20 model → ~$130k/month. Cache the 2.5k prefix, rerank context to 2.5k, cap history at 800, route 75% to a $2/$10 model → ~$41k/month, −69%, no change on the eval set, lower p95 because inputs shrank.

**Controls that keep it down.** Cost per request on the dashboard next to quality; per-run budgets for agents; gateway spend caps per key; cost deltas in CI; a monthly FinOps review with owners per feature.

**Trade-offs to name.** Routing adds a classification step and a risk of under-serving hard cases (mitigate with escalation on low confidence); aggressive context trimming can hurt recall (watch retrieval metrics); caching changes prompt ordering, which can change behaviour (re-run evals).

### Critic's additions: the parameters, the Google Cloud version of the arithmetic, and five more follow-ups

**Name the knobs, not the lever.** On Gemini: explicit context caching creates a `cachedContent` resource with a TTL (default one hour; you pay storage per million tokens per hour, so a cache that is read once an hour can cost more than it saves); implicit caching is on by default for Gemini 2.5 and later models and needs a minimum prefix (2,048 tokens on 2.5, 4,096 on the 3.x models); the response's `usage_metadata.cached_content_token_count` is your cache-hit measurement and `thoughts_token_count` your thinking spend. Thinking is set per call with `thinking_config` — `thinking_level` (`minimal`/`low`/`medium`/`high`, model-dependent) on Gemini 3 models, `thinking_budget` (a token count; 0 disables it on Flash, Pro cannot be disabled) on Gemini 2.5. `response_schema` and `max_output_tokens` bound output. Batch prediction is 50% off list price. Provisioned Throughput is bought in generative AI scale units (GSUs) on weekly to yearly commits; size it from measured peak tokens per second, never from a forecast.

**The same worked number on Gemini list prices (check the pricing page the week of the interview; these are the published rates at the time of writing).** Frontier tier at $2 input / $12 output per million (Gemini 3.1 Pro), Flash tier at $0.75 / $3.75 (Gemini 3.8 Flash at an introductory rate through 31 December 2026; $1.50 / $7.50 from 1 January 2027, which turns the 69% below into about 54% unless more traffic moves to Flash-Lite — 39b.1 has the arithmetic) and Flash-Lite at $0.30 / $2.50 (Gemini 3.5 Flash-Lite). The 100k-turns-a-day support agent at 9k input and 400 output on the Pro tier costs 9,000 × $2 + 400 × $12 per million = $0.0228 a turn, about $68k a month. Cache the 2.5k prefix at 10% ($0.0005 instead of $0.005), rerank context to 2.5k, cap history at 800 (4.1k uncached input), route 75% of turns to Flash: Pro turns cost about $0.0135, Flash turns about $0.0049, blended $0.0071 — about $21k a month, a 69% reduction with the same eval gate. Say the arithmetic out loud; the interviewer scores the method, not the decimals.

**Five more follow-ups.**
- *"How do you measure your cache hit rate, and what is a good one?"* — `cached_content_token_count` over total input tokens per route; for an agent with a stable system prompt and tool list, 50–70% of input tokens cached is typical, under 30% means the prefix is being invalidated (prompt edits, per-user content placed before the stable part, a TTL shorter than the traffic gap).
- *"Thinking tokens — how do they show up in the bill?"* — As output tokens; a planner that thinks 3k tokens on a $12-per-million tier adds $0.036 per run, which is why thinking goes on the planner and evaluator and not on a worker that runs fifty times per task.
- *"What is the cost of the judge?"* — A Flash-tier judge over a 2k-token transcript is roughly $0.002 per sample; at 3% sampling of 100k turns that is $6 a day — cheap enough to never be the reason you skip it.
- *"How do you forecast cost at ten times the traffic?"* — Linear in turns, but the mix changes: more long conversations (history grows), more retries under rate limits (idempotency and backoff matter), and Provisioned Throughput becomes cheaper than on-demand once utilization is steady above roughly 60–70% of a GSU. Present the forecast as a range with the two assumptions that move it most.
- *"The business asks for a number per ticket, not per token."* — Cost per resolved ticket = model cost per turn × turns per resolution ÷ containment rate, plus tool and search costs; put that on the same dashboard as containment so a cheaper model that lowers containment is visible as a more expensive ticket.

---

## 39.2 Observability — "You built an agent. It says 'I can't find the dataset.' How do you troubleshoot?"

**Headline.** "I read the trace before I read the prompt. The sentence 'I can't find the dataset' is the model narrating a tool result; the trace tells me which layer actually failed — tool, permissions, retrieval, context or the model."

**Method.**
1. **Reproduce and locate.** Find the run by conversation id in the tracing backend (Langfuse/LangSmith/Phoenix/CloudWatch with OTel GenAI spans). Confirm the user, tenant, model, prompt version and the exact input.
2. **Tool layer.** Look at the `execute_tool` spans. Was a dataset-lookup tool called at all? If not: the tool schema was missing, mis-described or not in this agent's allow-list; or the model picked another tool. If yes: what arguments did it pass (wrong catalog, misspelled name, wrong tenant) and what came back — an empty list, a 403, a timeout, a schema error? Most "cannot find" cases are an empty result from a correct call with the wrong scope, or a permission error that the tool swallowed into "no results".
3. **Identity and authorization.** Which principal executed the tool? With on-behalf-of identity, the user may simply not have access (correct behaviour — the message should say so). With a service account, a missing grant or a wrong role.
4. **Retrieval layer.** If discovery goes through search: the `retrieval` span's index name, filters, top_k and scores; was the catalog indexed; did a tenant filter exclude everything; is the embedding model mismatched with the index.
5. **Context layer.** Did the model see the tool result? Context truncation after a long conversation drops tool outputs; check the token counts on the `chat` span and whether compaction happened.
6. **Model layer.** Hallucinated tool names or arguments, or the model answering from the system prompt instead of calling the tool; check the finish reason and the tool-call list.
7. **Fix the layer, not the symptom**, then add the case to the eval set (a replayable test with the captured inputs and a mocked tool) and an alert on the pattern (empty-result rate per tool).

**What the agent should have said.** "I searched catalog X with filters Y as user Z and found no dataset; you may lack access or the name may differ — here are the closest matches." That means tool results carry structured status (found / not found / forbidden / error) and the prompt tells the model to report them distinctly — an observability fix and a UX fix at once.

**What I instrument from the start.** `invoke_agent` root span; `chat`, `execute_tool`, `retrieval` children with tokens, latency, arguments (redacted) and result status; identity on every span; metrics for empty-result rate, tool error rate, p95 and cost; judge sampling; content capture opt-in and redacted.

### Critic's additions: the Google Cloud specifics and the error signatures that decide the layer

**Where the trace lives.** An ADK agent deployed on Agent Runtime (formerly Agent Engine) exports traces to Cloud Trace when tracing is enabled on the app; Agent Observability adds the turnkey dashboards; metrics go to Cloud Monitoring and logs to Cloud Logging with the trace id in the log entry so you can pivot from a log line to the trace. For ad-hoc analysis, Log Analytics (BigQuery-backed) answers "how many `execute_tool` spans for `find_dataset` returned `status=empty` per day per tenant" in one query.

**The error signatures, because they decide the layer in one glance.**
- BigQuery returns `404 notFound` for a dataset or table that does not exist in that project, and `403 accessDenied` with the missing permission named (for example `bigquery.tables.getData`) when it exists but the principal cannot read it. A tool that maps both to "no results" has destroyed the diagnosis; the fix is a structured status.
- Running a query needs `roles/bigquery.jobUser` on the project that runs the job as well as `dataViewer` on the data; a missing `jobUser` fails at `jobs.create` before any data is touched, which looks like "the tool is broken" rather than "no access".
- A VPC Service Controls denial is a `403` whose message says the request is prohibited by the organization's policy and carries a `vpcServiceControlsUniqueIdentifier` you can search in the audit logs; it is not a "not found", but a tool wrapper that catches every exception and returns an empty list makes it look like one.
- A `429 resourceExhausted` (quota) that the wrapper retries silently and then gives up on produces an intermittent "cannot find" — the pattern to recognize is time-of-day correlation in the empty-result-rate chart.
- An empty result with a correct call usually means a scope mismatch: wrong project, wrong region (BigQuery datasets are regional), a tenant filter, or the model abbreviating the name.

**Three more follow-ups.**
- *"The tool returned the dataset correctly, and the model still said it could not find it."* — Context layer: check whether the tool result was truncated by the tool-output cap or dropped by compaction (compare the `chat` span's input tokens before and after the tool call), then the model layer: a system prompt that says "if you are unsure, say you cannot find it" without defining what "found" means. The fix is a structured `found` status the prompt is told to trust.
- *"How do you alert on this before users complain?"* — A Cloud Monitoring alerting policy on `empty_result_rate` per tool: alert when the one-hour rate exceeds 2× the seven-day baseline for ten minutes, and a separate alert on any 403 rate above 1% because permission errors are never expected at scale.
- *"What SLOs would you publish for the agent?"* — Availability of the invoke endpoint (99.9%), p95 end-to-end latency per route (for example 4 s for retrieval-backed answers), tool success rate (99%), and a quality SLO from judge sampling (faithfulness ≥ 0.9 on the daily sample) with an error budget that pauses risky releases when spent.

---

## 39.3 Agentic design — "Where does reasoning belong in an agentic workflow? What about latent reasoning?"

**Headline.** "Reasoning is a budget you spend where the decision is hard and the error is expensive: on the planner, the evaluator and the final synthesis — not on workers in tight loops. Extended thinking spends it in tokens; latent reasoning spends it in hidden computation; the workflow design is the same either way."

**Design.** Start from the six patterns (chain, route, parallelize, orchestrate, evaluate-and-refine, loop). For a document-analysis agent: a *router* with no thinking classifies the request; a *planner* with a moderate thinking budget decomposes it into sub-tasks; *workers* (retrieval, extraction, calculation) run with no thinking and small models in parallel; an *evaluator* with a thinking budget checks the assembled answer against the evidence; a *synthesizer* writes the final output with citations. Budgets: planner 2–4k thinking tokens, evaluator 2k, everything else zero; a cap on loop iterations (3) and on total cost per run.

**Latent reasoning.** Reasoning models emit chains of thought; latent-reasoning architectures (recurrent-depth or looped transformers, "thinking in continuous space") iterate in the hidden state without emitting tokens — potentially cheaper per step and not constrained to language, but less inspectable. For workflow design it changes two things: the cost model (compute per call rather than output tokens) and observability (no visible chain to audit, so you rely on outcome evals and tool traces). The practical stance: treat any reasoning capacity as a knob set per node, measured by accuracy per dollar on the eval set.

**Where reasoning helps measurably.** Planning under constraints, tool selection among many similar tools, reconciling conflicting evidence, math and code, and self-verification. **Where it does not.** Classification, extraction with a schema, formatting, and most retrieval steps — give those to small models.

**Failure modes and guards.** Over-thinking (latency and cost) → budgets and routing; under-thinking on hard cases → escalation on low confidence; reasoning that ignores tool results → force evidence citation; loops → iteration caps.

**Numbers to offer.** "Adding a 4k thinking budget to the planner raised task success from 71% to 84% on our 200-task set at +18% cost; adding it to workers changed nothing at +60% cost — so it stays on the planner."

### Critic's additions: what "latent reasoning" means precisely, the ADK knobs, and four more follow-ups

**Say what latent reasoning is, with the two reference points.** Chain-of-thought reasoning spends compute by generating tokens the model then conditions on. Latent reasoning spends it without emitting tokens: either by feeding the model's last hidden state back as the next input instead of a token (continuous chain of thought — "Coconut", Meta, December 2024), or by looping a block of layers a variable number of times per token at inference (recurrent-depth models — the 3.5-billion-parameter model of Geiping and colleagues, February 2025, which scales test-time compute by iterating a recurrent block). Both decouple reasoning from vocabulary and make the compute per answer a continuous knob. Production Gemini and Claude models expose reasoning as thinking tokens or effort levels, not as recurrent depth, so in practice the knob you set is `thinking_level` or a token budget; the design stance is the same.

**The ADK knobs.** On an `LlmAgent` you attach `planner=BuiltInPlanner(thinking_config=types.ThinkingConfig(thinking_budget=2048, include_thoughts=True))` for the planner and omit the planner on workers; `generate_content_config` carries `temperature` and `max_output_tokens`; `output_schema` forces the planner's plan into a typed structure that the workers and the tests can read; a `LoopAgent(max_iterations=3)` wraps the evaluate-and-refine step; `ParallelAgent` runs the workers; `SequentialAgent` composes the whole. Deploy on Agent Runtime with Agent Sessions for per-conversation state and Memory Bank for facts that must survive sessions.

**Four more follow-ups.**
- *"How do you decide the budget per node?"* — A sweep on the eval set: run each node at off, low, medium and high (or 0, 1k, 4k, 8k tokens), plot task success against cost per task, keep the knee. Report it as "planner at 4k: +13 points for +18% cost; evaluator at 2k: +4 points for +6%; workers: no gain".
- *"ReAct versus a planner-worker workflow?"* — ReAct is the inner loop of any tool-using node (think, act, observe); the workflow is the outer structure that decides which node runs when with what budget. A single ReAct agent is the right answer for short tool chains; the workflow earns its complexity when sub-tasks are parallel, need isolation or need different models.
- *"How do you test a plan without running it?"* — Because the plan is a typed object (sub-tasks with tool, inputs, dependencies, success condition), you can assert on it: no unknown tools, no cycles, every sub-task has a verifiable success condition, cost estimate under budget; 50 reference plans in the eval set give a plan-quality score separate from execution.
- *"Reasoning models ignore tool results sometimes — what do you do?"* — Require evidence citation in the synthesis (`claim`, `source_tool_call_id`), reject uncited claims in a validator, and keep the evaluator on a different model family than the synthesizer; measure it as the uncited-claim rate.

---

## 39.4 Quality and evaluation — "Walk me through building an LLM-as-a-judge."

**Headline.** "A judge is a calibrated classifier built from a rubric: one criterion per call, evidence in the prompt, claim-level decomposition for faithfulness, pairwise comparison for preferences, agreement measured against human labels, and biases controlled. Then it runs in CI and samples production."

**Steps.**
1. **Decide the criteria** with the owners: faithfulness (claims supported by context), correctness (vs. reference), completeness, policy compliance, tone. One judge per criterion.
2. **Write the rubric** with anchored scales and examples of each score; binary where possible.
3. **Build the gold set:** 100–200 outputs labeled by two humans; measure inter-annotator agreement (κ); fix the rubric until humans agree.
4. **Write the judge prompt:** role, rubric, the evidence (question, context, reference, output), a required reasoning format ("list claims, mark each supported/contradicted/not found with the evidence sentence"), and a JSON output with score and rationale; temperature 0.
5. **Calibrate:** run on the gold set; measure agreement; inspect disagreements; iterate on the rubric and prompt; try a different judge model; keep the best.
6. **Control biases:** position bias (swap order in pairwise and average), verbosity bias (penalize unsupported length; use references), self-preference (judge from a different model family), leniency (binary verdicts with evidence).
7. **Run it:** in CI on the eval set with thresholds (e.g., faithfulness ≥ 0.95 mean, no case below 0.6); in production on 1–5% of traffic with alerts; disagreements and low scores go to a human review queue weekly, and labeled cases feed back into the gold set.
8. **Report:** mean with bootstrap confidence intervals, pass rates, agreement with humans, cost of judging.

**Tools.** Ragas/DeepEval/promptfoo/Inspect, LangSmith or Langfuse evaluators, Braintrust, MLflow and Databricks Agent Evaluation (built-in groundedness/relevance judges and custom guidelines), the Gen AI evaluation service with Agent Simulation and Agent Evaluation on the Gemini Enterprise Agent Platform (Vertex AI evaluation, in the old naming), evaluations in Microsoft Foundry (formerly Azure AI Foundry), Bedrock AgentCore Evaluations.

**Trade-offs to name.** Judges cost tokens (use a cheap calibrated judge for monitoring, a strong one for CI); they can drift when the judge model changes (pin and re-calibrate); they are not a substitute for humans on high-stakes decisions (sampled human review stays).

### Critic's additions: the statistics behind the thresholds, the Google Cloud metric names, and four more follow-ups

**Why 100–200 gold cases, and what a 0.95 gate can actually detect.** A binary metric at a 95% pass rate measured on 200 cases has a 95% confidence interval of about ±3 points; on 100 cases about ±4. So a 200-case gate can tell a 95% system from a 90% one and cannot reliably tell it from a 93% one; if the product needs to see a 2-point regression you need roughly 450 cases, or you gate on the worst slice rather than the mean. Say this when you name the threshold; it is the difference between a number and a measured number.

**Agreement, precisely.** Report Cohen's κ for two labelers (0.6–0.8 substantial, above 0.8 near-perfect) and the judge's accuracy against the adjudicated gold label; for pairwise judges report agreement after position swapping and the share of "ties". A judge that agrees with humans 91% of the time on a criterion where humans agree with each other 94% of the time is close to the ceiling; one at 80% against a 95% human ceiling needs rubric work.

**The Google Cloud names.** The Gen AI evaluation service runs pointwise and pairwise model-based metrics (`PointwiseMetric`, `PairwiseMetric` with a prompt template or a managed rubric), computation-based metrics (exact match, ROUGE, BLEU, tool-call match), and rubric-based evaluation where rubrics are generated per prompt and scored; agent evaluation adds trajectory metrics — `trajectory_exact_match`, `trajectory_in_order_match`, `trajectory_any_order_match`, `trajectory_precision`, `trajectory_recall`, `trajectory_single_tool_use` — and final-response judges. Datasets come from BigQuery or Cloud Storage, results land in a BigQuery table you dashboard. On the Agent Platform, Agent Simulation generates synthetic multi-turn interactions against virtualized tools and Agent Evaluation scores live traffic with multi-turn autoraters; Agent Optimizer clusters failures and proposes instruction changes, which you treat as candidates for the eval gate, never as auto-applied fixes.

**Four more follow-ups.**
- *"The judge says 0.96 and users still complain — what is wrong?"* — The criterion set is incomplete (faithful but unhelpful; correct but late), the sample is not representative (judge runs on the easy slice), or the judge drifted. Check per-slice scores, add a helpfulness or task-completion judge, and compare judge scores with user-reported issues weekly.
- *"How do you evaluate the judge after a model upgrade?"* — Re-run the pinned gold set with the new judge model before switching; require agreement within 2 points of the old judge and inspect every flipped verdict; keep both judges running in parallel for a week on production samples.
- *"Rubric-based or reference-based?"* — Reference-based when a correct answer exists (extraction, lookup, calculation); rubric-based when there are many acceptable answers (summaries, advice); claim-level faithfulness always when retrieval is involved. Most systems need two of the three.
- *"How do you keep the eval set honest over time?"* — Version it; add every production failure as a case with its label; retire cases the system has not failed in six months into a regression tier; keep a hidden holdout the prompt authors never see.

---

## 39.5 Security / IAM — "How do you limit an agent to only certain data?"

**Headline.** "Enforce permissions where the data lives, with the agent acting as the user through on-behalf-of identity; scope tools instead of exposing raw access; put a policy engine in front of tool calls; treat everything the agent reads as untrusted; audit every call."

**Layers.**
1. **Identity:** the user's token is exchanged for a scoped token (OBO) that the agent presents to data systems; infrastructure access uses a least-privilege workload identity; credentials live in a vault and never in the prompt.
2. **Data layer:** row-level security and column masking in the warehouse/lakehouse (Unity Catalog, Snowflake policies, Postgres RLS, BigQuery policy tags); document ACLs carried into the vector index and applied as retrieval filters; separate indexes or tenants where regulation demands hard isolation.
3. **Tool layer:** scoped tools (`get_my_leave_balance()` rather than `query(sql)`), argument constraints, allow-lists per agent and role, a policy engine (Cedar/Verified Permissions, OpenFGA, OPA) evaluated by the gateway before execution; approvals for writes.
4. **Content layer:** retrieved text and tool results are data; injection classifiers; no secrets in context; egress allow-lists so a compromised agent cannot exfiltrate.
5. **Audit and tests:** every call logged with principal, arguments and result; negative tests in CI ("user A must not see document B"); red-team suites.

**Cloud mapping.** AWS: AgentCore Identity (OAuth, OBO), Gateway, Policy, Bedrock Guardrails, IAM/VPC endpoints. Microsoft: Entra ID OBO and Microsoft Entra Agent ID for agent identities, Purview, content filters and Prompt Shields governed through the Foundry Control Plane in Microsoft Foundry (formerly Azure AI Foundry). Google: Cloud IAM, Agent Identity (a SPIFFE-based principal per agent), Agent Registry and Agent Gateway (Gemini Enterprise Agent Platform, April 2026), Model Armor, VPC Service Controls. Databricks: Unity Catalog permissions flow into Vector Search and agents; AI Gateway.

**Trade-offs.** Per-user identity propagation complicates caching (cache per permission set, or cache only public content); strict retrieval filters reduce recall for broad questions (explain the limitation to the user); policy engines add latency (cache decisions). The alternative — trusting the prompt to enforce access — fails the first time someone writes "ignore previous instructions".

### Critic's additions: the Google Cloud mechanisms with their syntax, and four more follow-ups

**Say the mechanism with its syntax.**
- BigQuery row-level security: `CREATE ROW ACCESS POLICY eu_only ON dataset.customers GRANT TO ("group:eu-analysts@example.com") FILTER USING (region = "EU");` and, for per-user rows, `FILTER USING (SESSION_USER() = owner_email)`. Column-level security is a policy tag on the column (taxonomies now managed in Dataplex Universal Catalog; enforcement stays in BigQuery) with the Fine-Grained Reader role granted on the tag; without it the query fails on that column rather than returning nulls, which the tool must report as `forbidden`.
- Agent Search (formerly Vertex AI Search) access-controlled data stores: the ACL flag is set at creation and cannot be changed later; one identity provider per location (Google Identity, or Microsoft Entra ID, Okta and others through Workforce Identity Federation); for unstructured documents you supply `acl_info.readers.principals` with user and group ids (up to 3,000 readers per document); results are filtered by the caller's identity before ranking, so a user never sees a snippet of a document they cannot open.
- Vector Search on the Agent Platform (formerly Vertex AI Vector Search): `restricts` (string namespaces with allow and deny lists, for example `tenant` and `acl_group`) and `numeric_restricts` evaluated inside the index, so filtering is pre-filtering, not a post-filter that empties the result set.
- IAM Conditions: a role binding with a condition expression, for example limiting a service account's `bigquery.dataViewer` to resources whose name starts with the tenant prefix, or to business hours for a break-glass role.
- Agent Identity gives every agent a distinct, verifiable principal (rather than a shared service account), Agent Registry records which tools and skills it may use, and Agent Gateway enforces the policy and runs Model Armor on the traffic between agents and tools; Model Armor templates carry the filters — prompt injection and jailbreak detection, sensitive data protection (basic infoTypes or an advanced Sensitive Data Protection template), malicious URL detection, and the responsible-AI categories — each with a confidence setting of high, medium-and-above or low-and-above, and floor settings at organization, folder or project level that no project template can weaken.
- VPC Service Controls: a perimeter around the BigQuery, Cloud Storage and Agent Platform APIs, with ingress and egress rules per identity and project; test it by trying to copy a table to a project outside the perimeter with a valid credential and confirming the 403.

**Four more follow-ups.**
- *"How does the agent get the user's token?"* — The front end authenticates the user with the enterprise IdP (OIDC), the backend exchanges the id token for an access token with the scopes the tools need (token exchange or an OAuth consent flow for Google Workspace data), and the tool wrapper attaches it per call; the agent's own service account is never used for user data. The token is in the request context, never in the prompt, and its expiry is shorter than a long agent run, so the wrapper refreshes it.
- *"Tool-level versus data-level enforcement — if you had to pick one?"* — Data-level, always: a tool is one path to the data and someone will add another. Tool scoping exists to reduce blast radius and to make the agent's actions reviewable, not to replace row-level security.
- *"A legacy system has one shared credential and no per-user auth."* — Put a tool service in front of it that holds the credential in Secret Manager, enforces an allow-list of operations per calling identity, logs principal and arguments on every call, and returns only the fields the caller's role permits; treat it as the compensating control and write down that it is one.
- *"Memory Bank, PII and deletion?"* — Memory is scoped per user (and per tenant where it applies), written only by an explicit policy (what is worth remembering, with provenance), redacted with Sensitive Data Protection before storage, and deletable per user for data-subject requests; nothing retrieved from another user's memory can enter a prompt.

---

## 39.6 Twenty more, briefly

1. **Agentic RAG vs plain RAG?** Plain: one retrieval pass stuffed into the prompt. Agentic: the model decides whether/what/how often to retrieve — decomposition, iteration, self-RAG, corrective RAG, tool-based retrieval; better recall on multi-hop at higher latency/cost. Use agentic when questions are complex; keep plain for lookups.
2. **RAG vs long context?** Long context when the corpus is small and hot and cost is fine; RAG for scale, freshness, citations and permissions; hybrid in practice.
3. **MCP vs function calling?** Function calling is a model capability with tool definitions in your code; MCP is a protocol that lets any client discover and call tools/resources on any server with auth — reuse and governance.
4. **A2A?** Agent cards, task lifecycle, streaming updates and auth between agents across vendors; use for cross-organization or cross-framework delegation.
5. **How do you prevent hallucinations?** Ground with retrieval and tools, require citations, allow abstention, verify with a judge or a check, constrain outputs with schemas, lower temperature, and measure faithfulness.
6. **Structured outputs?** JSON schema enforcement at the API; Pydantic validation and repair loops; never parse free text in production.
7. **Memory for agents?** Working (context, managed), episodic (past runs), semantic (facts with explicit write policy), procedural (skills); inspectable and deletable stores; not fine-tuning.
8. **Multi-agent coordination?** Supervisor with isolated sub-agents for parallelism and fresh context; explicit message schemas; budgets; one owner per decision; avoid chatter.
9. **Choosing a model?** Eval set first; cheapest tier that passes; route the rest up; pin versions; fallback behind a gateway.
10. **Latency optimization?** Streaming, smaller models, fewer hops, parallel tool calls, caching, shorter context, speculative/early stopping, regional endpoints.
11. **Scaling an LLM service?** Stateless API tier, queue for long jobs, rate-limit awareness, provider fallbacks, caching, autoscaling on queue depth, capacity planning in tokens per minute.
12. **Prompt injection?** Untrusted content as data, classifiers, least privilege, egress control, approvals, instruction hierarchy, red-team suite.
13. **Deploying a RAG system to production?** IaC, environments, eval gates in CI, canary, tracing, cost dashboards, ACL tests, index refresh pipeline, rollback.
14. **Handling PII?** Minimize, redact in prompts and logs, tokenize ids, retention policies, vendor zero-retention, access control, DSAR deletion paths.
15. **Chunking strategy?** Structure-aware, 200–800 tokens with overlap, contextual summaries, metadata, tables whole, parent-child; tuned on recall@k.
16. **Vector DB choice?** Where the data is, filtered-search semantics, scale, ops; pgvector default; managed for no-ops.
17. **Fine-tuning vs prompting?** Behaviour/format/cost → tune; facts → RAG; always after a measured baseline.
18. **Evaluating agents?** Outcomes and trajectories, simulated users, replay with mocked tools, pass^k, cost per task.
19. **Drift?** Input/feature/prediction drift monitors, periodic judge sampling, retraining triggers, and change detection on upstream data.
20. **Explaining AI to the business?** Problem, measure, baseline, result, cost, risk — in that order; demo over slides; acceptance criteria written together.

### Critic's additions: eight more, for a Google Cloud loop

21. **Agent Search vs RAG Engine vs your own index?** Agent Search when the sources are enterprise content with ACLs and connectors (Drive, SharePoint, Cloud Storage, BigQuery) and you want managed parsing, ranking and grounding; RAG Engine when you need control over chunking, embeddings and the vector store but still a managed pipeline; your own index (Vector Search, AlloyDB with pgvector, BigQuery vector search) when retrieval is part of a larger data model or needs custom filters and hybrid scoring.
22. **Agent Runtime vs Cloud Run for an agent?** Agent Runtime gives managed sessions, Memory Bank, tracing, identity and scaling for ADK or LangGraph agents with no infrastructure; Cloud Run when you need custom networking, non-Python runtimes, or an existing service mesh — and you then build sessions and tracing yourself.
23. **Flows vs playbooks in Conversational Agents?** Flows for exact, auditable, testable paths (identity, payment, confirmation); playbooks for open-ended tasks with tools and data stores; the production pattern is a flow skeleton that invokes playbooks and takes control back.
24. **Grounding with Google Search vs your own sources?** Google Search grounding for public, fresh facts with citations; your data stores for anything the business owns; never let public grounding answer a question that policy documents should.
25. **BigQuery AI functions?** `AI.GENERATE`-style and `ML.GENERATE_EMBEDDING` functions run Gemini and embedding models from SQL over tables, with vector search in the warehouse; right for batch enrichment and analytics, wrong for interactive latency.
26. **Gemini Live API vs STT + LLM + TTS?** Live gives one model for audio in and out with built-in voice activity detection and interruption handling and the lowest latency; the chain gives control, logging and cost transparency at each stage; for transactions the structured order operations and the state machine stay outside the model either way.
27. **Model Armor vs safety settings on the model?** Safety settings filter the model's own generations by category; Model Armor screens prompts and responses as a policy layer (injection, sensitive data, URLs, responsible-AI categories) with org-level floors and audit; you use both.
28. **How do you ship an agent through environments on Google Cloud?** Terraform for projects, IAM, VPC-SC and data stores; Cloud Build runs unit tests, the eval gate and the cost delta; deploy to Agent Runtime or Cloud Run with a canary; Cloud Deploy or tagged revisions for promotion and rollback; prompts and rubrics versioned with the code.

### Critic's additions: five more that only exist since the 2026 renaming

29. **Gemini Enterprise versus the Gemini Enterprise Agent Platform?** Gemini Enterprise (formerly Agentspace) is the employee-facing app where people use agents; the Agent Platform (formerly Vertex AI) is where developers build, deploy, govern and evaluate them. Agents built on the platform can be published into the app.
30. **CX Agent Studio versus Dialogflow CX?** CX Agent Studio, inside Gemini Enterprise for Customer Experience, is the ADK-based, low-code evolution: LLM agents with instructions, tools, Python callbacks, guardrails and handoff rules, bidirectional-streaming voice and asynchronous tool calls. Dialogflow CX (Conversational Agents console) stays for existing flow-based agents, and CX Agent Studio can call those flows as flow-based agents — so keep the transactional flows and move the open-ended parts.
31. **Agent Identity versus a service account?** Agent Identity is a SPIFFE-based principal tied to one agent's lifecycle, with certificate-bound tokens usable only from the trusted runtime; a service account is a shared, long-lived principal whose keys can be exported. Grant roles to the agent's `principal://…` exactly as to any principal, and remember that switching an agent to Agent Identity drops the grants made to its old service account.
32. **Agent Gateway versus Apigee?** Apigee manages APIs as products (proxies, quotas, keys, analytics, monetization) and can front them for agents; Agent Gateway governs agent traffic — which agent identity may call which registered tool or agent, over HTTP including MCP and A2A, with Model Armor inline. Large customers use both: Apigee to publish the APIs, Agent Gateway to decide which agents reach them.
33. **What are thought signatures, and why should an agent engineer care?** Encrypted representations of Gemini's internal reasoning state returned with its responses; in a stateless multi-step tool loop they must be sent back unchanged with the history, or the model loses its reasoning thread between function calls (and Gemini 3 function-calling turns can be rejected without them). ADK and the stateful Interactions API handle them; hand-written loops and history "cleaners" are where they get lost.

**Interview line for the whole chapter:** *"Every answer has the same skeleton: what I would measure, the layers of the system, the levers in order, a number from a real run, and the trade-off I accepted."*
