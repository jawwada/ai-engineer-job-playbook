# 43. Question bank: 173 questions with short answers

> Use this for rapid-fire drills: read the question, answer aloud in two sentences, compare. Long-form answers live in the chapters referenced in brackets and in Part 6's 50-question guides.

## LLM fundamentals [16, 17]

1. **What is a token and why does it matter?** A sub-word unit from the tokenizer; cost, context limits and latency are all in tokens (~0.75 English words each, worse for code and numbers).
2. **Temperature vs top-p?** Temperature scales the logits (randomness); top-p truncates to the smallest set of tokens with cumulative probability p. Use 0 for extraction, moderate for creative.
3. **What is a context window?** The maximum tokens the model attends to per call; effective use degrades with clutter and position — hence retrieval and context engineering.
4. **Dense vs MoE?** Dense uses all parameters per token; MoE routes each token to a few experts — more capacity per FLOP, more memory.
5. **What are reasoning models?** Models that generate (hidden or visible) chains of thought before answering, with a controllable thinking budget; more accuracy on hard tasks at more cost and latency.
6. **Open-weight vs open-source?** Open-weight: downloadable weights under a license; open-source adds code, data and recipe. Check the license (Apache-2.0, MIT, Llama community, custom).
7. **What is quantization?** Storing weights (and KV cache) in fewer bits (FP8/INT8/INT4); cuts memory and cost with small accuracy loss; re-run evals.
8. **What is KV cache?** Stored keys/values of previous tokens so decoding does not recompute attention; dominates memory at long context; prefix caching reuses it.
9. **Speculative decoding?** A small draft model proposes tokens, the large model verifies in parallel; 2–3× faster decoding with identical outputs.
10. **Structured outputs?** Constraining generation to a JSON schema (grammar-constrained decoding); validate anyway.
11. **Prompt caching?** Billing and latency discount for repeated prefixes; put static content first.
12. **Batch API?** Asynchronous processing at ~50% discount for non-interactive workloads.
13. **What is distillation?** Training a small model on a large model's outputs (and sometimes logits) for a narrow task.
14. **What is RLHF/DPO/GRPO?** Preference optimization methods: RLHF trains a reward model and uses PPO; DPO optimizes directly on preference pairs; GRPO-style RL uses verifiable rewards (tests, math) — behind reasoning models.
15. **Embeddings vs LLM?** Embeddings map text to vectors for similarity; LLMs generate; both are transformers trained differently.
16. **What is a world model / JEPA?** A model that predicts future states in representation space (not pixels); V-JEPA 2 learns physics from video and plans robot actions.

## Retrieval and RAG [18, 24, 25]

17. **Why RAG?** Current, specific, permissioned, citable knowledge without retraining.
18. **Chunking strategy?** Structure-aware, 200–800 tokens, overlap, contextual summaries, metadata, tables whole, parent-child.
19. **Hybrid search?** BM25 + dense fused (RRF) then reranked; exact terms plus semantics.
20. **What is a reranker?** A cross-encoder scoring query–document pairs; accurate, expensive; apply to top-k only.
21. **HNSW?** A layered proximity graph for approximate nearest neighbor search; tune M, efConstruction, efSearch; memory ≈ 1.5× vectors.
22. **Filtered vector search problems?** Post-filtering loses recall; pre-filtering is slower; use stores with native filtered search.
23. **How do you evaluate retrieval?** recall@k, MRR, NDCG on a gold set of (query, relevant chunks); tune before touching prompts.
24. **Faithfulness?** Whether every claim in the answer is supported by retrieved context; measured with claim-level judges.
25. **Agentic RAG?** The model decides whether/what/how often to retrieve; decomposition, iteration, corrective fallback.
26. **GraphRAG?** Entity graph + community summaries for global and multi-hop questions; costly to build.
27. **When is a knowledge graph better than vectors?** Relationships, set logic, multi-hop, exactness, audit.
28. **RDF vs property graph?** Triples + ontologies + SPARQL (standards, reasoning) vs nodes/edges with properties + Cypher (ergonomics, performance).
29. **Entity resolution?** Merging records that refer to the same real-world entity: blocking, similarity, rules, human review.
30. **Long context vs RAG?** Small hot corpus → long context with caching; scale, freshness, permissions, citations → RAG.
31. **Multimodal RAG?** Index page images/charts with multimodal embeddings or ColPali; send images to a multimodal model with citations.
32. **Contextual retrieval?** Prepending chunk-specific context before embedding/indexing; large recall gains at low cost.

## Agents, tools, protocols [20, 22, 23]

33. **Workflow vs agent?** Code decides the path vs the model decides; use the simplest that works.
34. **Six patterns?** Chaining, routing, parallelization, orchestrator–workers, evaluator–optimizer, autonomous loop.
35. **ReAct?** Reason → act (tool) → observe, repeated; the base of tool loops.
36. **Why sub-agents?** Fresh context windows and parallelism; cost is coordination and tokens.
37. **Tool design rules?** Clear names/descriptions, typed inputs, informative errors, idempotency, dry-run, pagination, small outputs.
38. **What is MCP?** The open protocol for tools, resources and prompts between clients and servers (stdio or streamable HTTP with OAuth).
39. **What is A2A?** Agent-to-agent protocol: agent cards, task lifecycle, streaming, auth across vendors.
40. **Function calling vs MCP?** Model capability with tools in your code vs protocol for discovery and reuse across clients.
41. **How do you stop runaway agents?** Max turns/tool calls/tokens/dollars, loop detection, timeouts, approvals.
42. **Context engineering?** Deciding what goes into the window each turn: cached prefix, trimmed evidence, summaries, sub-agents, files.
43. **Memory types?** Working, episodic, semantic, procedural; explicit write policies; inspectable and deletable.
44. **HITL design?** Approval gates before irreversible actions, review queues, durable pauses, handoff with state.
45. **LangGraph in one sentence?** A graph of nodes with typed, checkpointed state, conditional edges, interrupts and persistence.
46. **Strands in one sentence?** AWS's model-driven agent SDK: prompt + tools + model, MCP first-class, deploys to AgentCore.
47. **Claude Agent SDK?** The Claude Code harness as a library: file/shell/web tools, MCP, subagents, hooks, permissions, sessions.
48. **AgentCore?** AWS's managed agent infrastructure: Runtime, Gateway, Memory, Identity, Browser, Code Interpreter, Policy, Observability, Evaluations.
49. **Computer-use agents?** Perception–action loops over GUIs; safe-action layers, credential isolation, pause on login/CAPTCHA.
50. **Coding agents' secret?** Verifiable feedback (tests), sandboxes, context compaction, sub-agents, memory files.

## Evaluation and observability [29, 32]

51. **How do you build an eval set?** 100–300 real inputs, references or rubrics, human-gold subset, versioned, grown from failures.
52. **LLM-as-a-judge steps?** Criteria → rubric → gold set → judge prompt with evidence → calibrate → control biases → CI and sampling.
53. **Judge biases?** Position, verbosity, self-preference, leniency; mitigations: swap order, references, claim decomposition, other model family.
54. **Agent evaluation?** Outcomes + trajectories, simulated users, replay with mocked tools, pass^k, cost per task.
55. **Three signals?** Logs, metrics, traces (plus profiles); traces are primary for LLM systems.
56. **OpenTelemetry?** Vendor-neutral SDKs, OTLP protocol, Collector pipeline, semantic conventions.
57. **GenAI semantic conventions?** `gen_ai.*` span names/attributes/metrics for inference, agents, tools, retrieval; still in Development status.
58. **What to trace in an agent?** `invoke_agent` root with `chat`, `execute_tool`, `retrieval` children: tokens, latency, args (redacted), results, identity.
59. **Troubleshooting "can't find the dataset"?** Read the trace: tool call and args, permissions, retrieval filters, context truncation, model behaviour; fix the layer; add to evals.
60. **Drift?** Monitor input/prediction distributions and judge scores; retrain or re-prompt on triggers.

## Security and governance [30]

61. **OWASP LLM top risks?** The 2026 edition (August 2026), in order: prompt injection, sensitive information disclosure, excessive agency, supply chain, data and model poisoning, unbounded consumption, misinformation, hidden context exposure (which replaced system-prompt leakage), vector and embedding weaknesses, improper output handling. For agents, cite the separate Top 10 for Agentic Applications (December 2025, ASI01–ASI10).
62. **Limit an agent to certain data?** Identity propagation (OBO), RLS/ACL filters at the data layer, scoped tools, policy engine, audit, negative tests.
63. **Indirect prompt injection?** Instructions hidden in content the agent reads; treat as data, classify, least privilege, egress control, approvals.
64. **Secrets in prompts?** Never; vault + runtime injection into tools.
65. **PII handling?** Minimize, redact, tokenize, retention and deletion, vendor policies.
66. **Guardrails on which layers?** Input, tool arguments, output.
67. **Zero-retention?** Vendor settings/contracts so prompts are not stored; verify per provider.
68. **Model supply chain?** Pin versions, checksums, licenses, vetted MCP servers, SBOMs.

## FinOps and cost [31]

69. **Where do tokens go?** Mostly input: repeated prefixes and over-long context; agents multiply calls.
70. **Top levers?** Caching, routing, context trimming, output/thinking control, batch, distillation, self-host at volume.
71. **Cost per request formula?** Uncached input × p_in + cached × p_cache + output (incl. thinking) × p_out + tool fees.
72. **How do you attribute cost?** OTel attributes (feature, tenant, route, model) joined to a price table.
73. **PTUs/provisioned throughput?** Reserved capacity; only after utilization is proven.
74. **Self-host threshold?** High steady volume or policy; include GPU utilization and ops cost.

## Cloud platforms [15, 21]

75. **Bedrock vs AgentCore?** Model API + managed RAG/guardrails vs agent infrastructure (runtime, gateway, memory, identity, policy, evals).
76. **Microsoft Foundry (formerly Azure AI Foundry, renamed November 2025)?** Model catalog, Foundry Agent Service (voice agents through Voice Live), evaluations and observability, Foundry Tools (formerly Azure AI Services), governance through the Foundry Control Plane; Entra-integrated, with Microsoft Entra Agent ID for agent identities.
77. **Gemini Enterprise Agent Platform (formerly Vertex AI and its Agent Builder)?** Build with ADK and Agent Studio; run on Agent Runtime (formerly Agent Engine) with Agent Sessions, Memory Bank and Agent Sandbox; govern with Agent Identity, Registry and Gateway plus Model Armor; improve with Agent Simulation, Evaluation, Observability and Optimizer; Agent Search (formerly Vertex AI Search), A2A and MCP around it.
78. **Choosing a cloud for AI?** Where data and identity live; model behind an abstraction; rent plumbing.
79. **Databricks for agents?** Unity Catalog governance, AI Search (formerly Vector Search), Agent Framework + Evaluation, MLflow, Unity Gateway, Agent Bricks.
80. **Snowflake Cortex?** LLM functions in SQL, Cortex Search/Analyst/Agents.
81. **BigQuery ML?** Models and embeddings via SQL, vector search in the warehouse.
82. **Lakehouse?** Open table formats (Delta/Iceberg) on object storage with ACID, one copy for BI/ML/AI.
83. **Medallion?** Bronze raw, silver cleaned, gold business-ready.

## Data, pipelines, MLOps [21, 46, 48]

84. **Batch vs streaming?** Scheduled bulk vs continuous; micro-batch is the common middle.
85. **Idempotent pipelines?** Re-runs produce the same result; MERGE/upsert, deterministic keys.
86. **Data quality in pipelines?** Expectations/tests, freshness SLAs, schema checks, quarantine.
87. **Feature store?** Consistent features for training and serving with point-in-time correctness.
88. **Model registry?** Versioned models with lineage, stages and approvals (MLflow, Unity Catalog).
89. **Training–serving skew?** Features computed differently offline vs online; fix with shared feature code.
90. **Canary deployment for models?** Small traffic slice with metric gates and rollback.
91. **Retraining triggers?** Schedule, drift, performance decay, new data volume.
92. **Text-to-SQL safely?** Semantic layer, schema + examples, read-only, validation, limits, eval set.

## Classic ML [17]

93. **Bias–variance?** Underfit vs overfit; regularize, more data, cross-validate.
94. **Gradient boosting?** Sequential trees fitting residuals; XGBoost/LightGBM/CatBoost; tabular default.
95. **Leakage?** Training features that encode the label or future; point-in-time discipline.
96. **AUC vs precision/recall?** Ranking quality vs threshold performance; use PR for imbalanced data.
97. **Two-tower model?** Separate encoders for query/user and item; retrieval via ANN.
98. **Position bias?** Clicks depend on rank; log position, debias with IPS or position features.
99. **A/B testing gates?** Pre-registered sample size, guardrail metrics, significance, rollback.
100. **Uplift modeling?** Predicting the causal effect of a treatment on an individual, not the outcome.
101. **Time-series forecasting choices?** Decomposable (Prophet/NeuralProphet), gradient boosting with lags, deep (TFT), foundation models (Chronos); evaluate by horizon.
102. **Anomaly detection?** Reconstruction error (autoencoders), isolation forests, residuals; threshold by alert budget.
103. **Map matching?** Aligning noisy GPS traces to a road network probabilistically.
104. **Explainability?** SHAP, partial dependence, monotonic constraints, surrogate models.

## Conversational and voice [28, 41]

105. **Dialogflow CX building blocks?** Flows, pages, intents, entities, routes, webhooks, session parameters, playbooks, data stores. In CX Agent Studio, its 2026 evolution: agents, instructions, tools, variables, callbacks, guardrails, handoff rules and flow-based agents.
106. **Why keep a state machine?** Transactions need guaranteed, testable paths.
107. **Voice latency budget?** ~800 ms to first audio; streaming at every stage.
108. **Barge-in?** Interruption handling with VAD and echo cancellation.
109. **Speech-to-speech vs chain?** Lower latency and prosody vs control, logging and cost.
110. **Drive-through failure modes?** Noise, accents, customizations, pranks, compounding errors; fixes: audio front end, catalog grounding, state machine with corrections, caps, crew handoff.

## System design and engineering [40, 49]

111. **First five minutes of a design?** Users, volume, latency, accuracy, data, permissions, budget, definition of done.
112. **Async long-running LLM calls?** Queue + workers + job ids + polling/webhooks; durable state.
113. **Rate limits from providers?** Client-side limiting, retries with backoff and jitter, fallbacks, queueing.
114. **Caching layers?** Prompt cache, response cache (exact/semantic), embedding cache, tool-result cache.
115. **Multi-tenancy?** Tenant id at gateway, filters in every query, per-tenant keys where needed, tests.
116. **Idempotency keys?** Prevent duplicate side effects on retries (payments, emails, orders).
117. **REST vs gRPC vs GraphQL?** Simplicity/ubiquity vs performance/streaming vs flexible client queries.
118. **Testing an LLM app?** Unit tests for tools and parsers, contract tests for schemas, eval suites for quality, load tests for latency, red-team suites for safety.
119. **Database indexing basics?** B-tree for equality/range, composite order matters, covering indexes, avoid over-indexing writes.
120. **Transactions and isolation?** ACID; read committed vs repeatable read vs serializable; choose per use.

## FDE and behavioural [35–38]

121. **What does an FDE do?** Embeds with customers to take use cases from idea to production in their environment; part engineer, part consultant, part product.
122. **How do you run discovery?** Problem, users, data, constraints, success metrics, decision makers — before architecture.
123. **Customer wants something unsafe?** Explain the risk, propose the safe alternative, document; escalate if needed.
124. **Tell me about a POC that stalled.** Story with cause (data access, ownership, evals missing) and what you changed.
125. **How do you write acceptance criteria?** Observable, measurable outcomes agreed before build, tied to the eval set.
126. **Handling ambiguity?** Timebox discovery, propose options with trade-offs, decide, revisit with data.
127. **Disagreement with an engineer?** Data, prototype, principle; agree on the test that settles it.
128. **Your biggest production failure?** Story with the process fix.
129. **How do you keep up?** Labs (chapter 34), reading lists (Part 6), notes you maintain.
130. **Why this company?** Their problem in their words, your evidence, the 90-day sentence.

## Quick definitions (say in one breath)

131. **MCP** — tool protocol. 132. **A2A** — agent protocol. 133. **RRF** — rank fusion. 134. **HNSW** — ANN graph. 135. **LoRA** — low-rank adapters. 136. **DPO** — direct preference optimization. 137. **OTLP** — OpenTelemetry protocol. 138. **RLS** — row-level security. 139. **OBO** — on-behalf-of token. 140. **PTU** — provisioned throughput unit. 141. **KV cache** — attention cache. 142. **RAG** — retrieval-augmented generation. 143. **CoT** — chain of thought. 144. **SLO** — service-level objective. 145. **CDC** — change data capture. 146. **IaC** — infrastructure as code. 147. **SHAP** — feature attribution. 148. **NDCG** — ranking metric. 149. **pass^k** — all-k-runs success. 150. **FinOps** — cloud financial operations.

## Critic's additions: 23 rapid-fire questions for a Google Cloud role-related-knowledge round [39b, 39c, 41, 42]

Each answer carries the number or parameter an interviewer listens for; check prices and limits the week of the interview.

151. **Price of a cached Gemini token?** 10% of the input price on Gemini 2.5 and later; explicit caches add storage per million tokens per hour; minimum prefix 2,048 tokens on 2.5, 4,096 on 3.x.
152. **Ways to buy Gemini capacity?** Standard PayGo, Priority (about 1.8× list), Flex (about 50% off), Batch (about 50% off), Provisioned Throughput in GSUs on one-week to one-year terms.
153. **Thinking knobs?** `thinking_level` (minimal, low, medium, high) on Gemini 3.x, `thinking_budget` in tokens on 2.5; billed as output; Gemini 3.8 Flash defaults to medium, so set `minimal` on workers.
154. **First move when an agent "can't find the dataset"?** Open the trace: was the `execute_tool` span called, with which arguments, and what status came back.
155. **BigQuery 404 versus 403?** `404 notFound`: no such dataset in that project and region; `403 accessDenied`: it exists, and the message names the missing permission; running queries also needs `roles/bigquery.jobUser`.
156. **A VPC Service Controls denial looks like?** A 403 saying the request is prohibited by the organization's policy, with a `vpcServiceControlsUniqueIdentifier` to search in the audit logs.
157. **Two alerts for tool failures?** Empty-result rate above 2× its seven-day baseline for ten minutes; any tool's 403 rate above 1% over five minutes.
158. **Latent reasoning in one breath?** Reasoning in hidden state rather than emitted tokens (continuous chain of thought, recurrent depth); in production models, hidden thinking you can budget but not read, carried across tool calls by thought signatures.
159. **Where does reasoning go in a workflow?** Planner and evaluator, chosen by a budget sweep; not on workers; not on a voice turn.
160. **ADK agent types?** `LlmAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`, custom agents; ADK 2.0 adds graph workflows; `output_schema` and `output_key` pass typed results through session state.
161. **What can a 200-case gate detect?** About ±3 points at 95% confidence near a 95% pass rate; about 450 cases for a 2-point change; gate on the worst slice too.
162. **Rule of three?** Zero errors in n cases bounds the error rate below about 3/n at 95% confidence — 600 clean cases to claim under 0.5%.
163. **Judge biases and fixes?** Position (swap order), verbosity (claim-level checks against references), self-preference (a different model family), leniency (binary verdicts with evidence).
164. **Agent Identity principal?** `principal://agents.global.org-ORG_ID.system.id.goog/resources/aiplatform/projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/AGENT_ID` — SPIFFE-based, certificate-bound tokens, granted roles like any principal.
165. **Agent Gateway modes and policies?** Client-to-agent (ingress) and agent-to-anywhere (egress); IAM unified access policies to Agent Registry tools, semantic governance policies, Model Armor; up to 5,000 registered resources per gateway.
166. **Model Armor blind spots?** No conversation history, no decoding of encoded content, no audio or video, fewer than three words returns no match; up to 256 URLs per request, documents up to 4 MB.
167. **Per-user rows in BigQuery?** `CREATE ROW ACCESS POLICY … GRANT TO (…) FILTER USING (SESSION_USER() = owner_email)`, with the query run under the user's identity.
168. **Dialogflow CX webhook timeout?** 5 seconds by default, 30 at most, one retry on transient failure; handle `webhook.error.timeout` with a message and a path, never silence.
169. **Gemini Live API session facts?** Audio-only sessions 15 minutes without compression, about 10 minutes per connection, resumption handles valid for two hours, 16 kHz PCM in and 24 kHz out, accumulated context re-billed every turn.
170. **Chirp 3 facts for a drive-through?** `chirp_3` with streaming recognition, up to 1,000 adaptation phrases, a denoiser that cannot remove background voices, word confidences that are not true confidences, $0.016 a minute at the first tier.
171. **How does Polymarket resolve?** UMA's optimistic oracle: a bond of about $750, a two-hour challenge window, a second dispute goes to a token-holder vote of about 48 hours.
172. **How does Kalshi resolve?** Its markets team finalizes the outcome from the source named in the rules, usually within a few hours of the outcome being known.
173. **Old names to new?** Vertex AI → Gemini Enterprise Agent Platform; Agent Engine → Agent Runtime; Vertex AI Search → Agent Search; Customer Engagement Suite → Gemini Enterprise for Customer Experience; Dialogflow CX → still Dialogflow CX, now filed as legacy, with CX Agent Studio as its evolution; Conversational Insights → Customer Experience Insights; Agentspace → Gemini Enterprise; Azure AI Foundry → Microsoft Foundry; LangGraph Platform → LangSmith Deployment; Databricks Vector Search → AI Search; Databricks AI Gateway → Unity Gateway; Amazon Kendra and Q Business → closed to new customers (AWS points to Bedrock Managed Knowledge Base and Amazon Quick).
