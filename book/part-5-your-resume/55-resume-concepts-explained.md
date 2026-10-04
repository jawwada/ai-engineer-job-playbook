# 55. Every concept on the reference resume, explained

> **Purpose:** a principal-level AI resume names eighty-odd technologies and methods. An interviewer can pick any of them and ask "tell me about X". This chapter goes line by line through the reference resume (a Senior Principal AI Engineer: agentic systems, MCP, RAG, enterprise AI standards; 15+ years from telecom data mining through insurance, ad-tech, energy, retail and creative AI to agentic marketing automation) and explains each concept: what it is, why it is there, and the two sentences to say about it, with the chapter that goes deeper. Replace the examples with your own evidence and you have a study sheet for any resume.

## 55.1 Headline and profile

- **Agentic systems** — software in which an LLM decides steps and calls tools within limits you set; the headline claim is about designing and standardizing them at enterprise scale (chapters 22, 22b, 23).
- **MCP (Model Context Protocol)** — the open standard for connecting models to tools, resources and prompts; "tool/MCP design" means defining typed, safe, well-described tools and servers (chapters 20, 28b).
- **RAG (retrieval-augmented generation)** — grounding answers in retrieved evidence; "retrieval at enterprise scale" implies hybrid search, reranking, permissions and evaluation (chapters 18, 24).
- **Reference architectures, paved-road patterns, evaluation standards** — the principal-engineer deliverables: documented target designs, reusable templates teams adopt by default, and the eval sets and judges that define "good" (chapters 32, 44, 50, 51).
- **Fine-tuning and evaluating models (PyTorch, Hugging Face, LoRA/PEFT)** — adapting open models with low-rank adapters and measuring them (chapters 26, 26b).
- **Multi-agent orchestration (LangGraph, MCP, multi-LLM routing)** — supervisor/sub-agent graphs with state, tools over MCP, and routing between model tiers for cost and quality (chapters 20, 22, 31).
- **Hybrid search, re-ranking, memory** — BM25 + vectors fused and reranked by a cross-encoder; memory as working/episodic/semantic stores (chapters 18, 22).
- **Tracing, guardrails, cost/token economics** — OpenTelemetry-style traces, input/tool/output guardrails, and FinOps for tokens (chapters 29, 30, 31).
- **Azure, AWS and GCP** — all three clouds; be ready for "which do you know best and what did you build on each" (chapter 15).
- **Built and led a 15-person AI team; directed engineering at a start-up; owns agentic marketing automation** — the leadership line; have the STAR stories (chapter 38).

**The two sentences for the headline terms, and the follow-up that comes next.** Knowing what each term is gets you only half-way; an interviewer wants to hear what you did with it and will immediately ask one harder question. Prepare both.

| Headline term | Two sentences to say | The follow-up to expect |
|---|---|---|
| Agentic systems | "An agentic system is one where the model chooses the next step and the tools, inside a budget and a permission set that I define. In practice that means a graph with typed state, tool contracts, a step cap, an approval gate for side effects, and traces for every run." | "When would you *not* use an agent?" (answer: when the path is known — use a workflow; chapter 22) |
| MCP | "MCP standardizes how a model discovers and calls tools, reads resources and loads prompts, so one server works with any client. The hard part is not the protocol but the tool design: narrow verbs, typed inputs, short descriptions, idempotent writes, and an allow-list per agent." | "How do you secure an MCP server?" (identity on the gateway, scoped tokens, no secrets in tool outputs, rate limits; chapter 30) |
| RAG at enterprise scale | "Enterprise RAG is retrieval with permissions, freshness and evaluation, not a vector lookup. We index with ACLs attached, fuse BM25 and dense retrieval with RRF, rerank with a cross-encoder, and measure recall@k and faithfulness on a gold set before any prompt change ships." | "What do you do when retrieval returns nothing relevant?" (abstain with a reason, suggest a rephrase, log the miss for the knowledge-gap queue; chapter 24) |
| Paved-road patterns | "A paved road is the default template a team gets for free: repo skeleton, gateway, tracing, eval harness and deployment, so the easy path is the compliant one. Adoption, not documentation, is the metric." | "How did you get teams to adopt it?" (make it faster than the alternative; migrate one team visibly; measure time-to-first-deploy) |
| LoRA/PEFT | "LoRA trains small low-rank matrices on top of frozen weights, so a 70B model adapts on one GPU and the adapter is a few hundred megabytes. We fine-tune only when prompting and retrieval plateau on the eval set, and we keep the base model's eval as the regression check." | "How do you know the fine-tune didn't break something else?" (held-out general eval, A/B against the prompted baseline; chapter 26) |
| Multi-agent orchestration | "A supervisor decomposes the task and dispatches to specialists with their own context, then merges results; the state lives in a checkpointer so runs can pause and resume. I route each node to the cheapest model that passes its eval." | "Single agent or multi-agent?" (under an equal token budget a single agent often wins on reasoning; split for isolation, parallelism or permissions, not for style; chapter 60.5) |
| Hybrid search, reranking, memory | "Lexical search catches identifiers and rare terms, vectors catch paraphrase, and the reranker fixes the top of the list. Memory is three stores with explicit write policies: working (this turn), episodic (what happened), semantic (what is true)." | "What goes wrong with memory?" (stale facts, unbounded growth, cross-user leakage; write policies and TTLs) |
| Tracing, guardrails, token economics | "Every request carries a trace id across the gateway, the retrieval calls and each model call, with token counts as span attributes. Guardrails sit at three points — input, tool call, output — and cost is attributed per feature and tenant so routing and caching decisions are measurable." | "Your token bill doubled last month — walk me through it" (chapter 39b.1) |

## 55.2 Core expertise — Python backend and APIs

- **Python, FastAPI, Flask** — FastAPI for typed async APIs with OpenAPI; Flask for older services (chapter 49).
- **REST-style APIs, service integration** — resource design, auth, pagination, idempotency; integrating enterprise systems through gateways (chapter 49).
- **Async and multi-step workflows** — `asyncio` for concurrent I/O; queues and durable state for long-running steps (chapters 45, 49).
- **Backend reliability, error handling, test automation, production code quality** — timeouts, retries with backoff, circuit breakers, structured logging, pytest, CI gates (chapters 45, 49, 52).

## 55.3 Core expertise — Agentic and LLM applications

- **LangGraph, LangChain** — graph-of-steps framework with checkpointed state; the library of integrations (chapter 20).
- **Supervisor/sub-agent patterns** — a coordinator delegates to specialists with isolated context and merges results (chapter 22).
- **Multi-LLM orchestration** — routing tasks across models (cheap vs frontier; different vendors) with fallbacks (chapters 16, 31).
- **Prompt/context management** — versioned prompts, cached prefixes, trimmed evidence, summaries (chapter 22 "context engineering").
- **Structured outputs, validation** — JSON-schema-constrained generation validated with Pydantic and repaired on failure (chapter 49).
- **HITL review** — human-in-the-loop approval gates and review queues (chapter 22).
- **LLM copilots** — assistants embedded in a workflow (the Ask-AI copilot; chapter 36.4).
- **Conversational AI (Dialogflow CX)** — flows, pages, intents, entities, webhooks, playbooks (chapters 28, 39c, 41).

**The mechanisms behind four lines that interviewers probe.** "Structured outputs", "HITL", "multi-LLM orchestration" and "prompt/context management" are easy to claim and easy to expose. Say how, not that.

- *Structured outputs.* Ask for the schema through the model's native mechanism (a tool/function definition or JSON-schema mode), validate the result with Pydantic, and on failure re-prompt once with the validation error attached; after two failures, fall back to a smaller deterministic extractor or route to a human. Log the failure rate per schema; a rising rate usually means the schema grew too wide or the input distribution changed.
- *HITL.* In LangGraph the gate is an interrupt before the side-effecting node; the checkpointer persists state, the reviewer sees a diff-style summary (what the agent will do, with evidence), and the run resumes with the reviewer's decision as input. The gate is policy-driven: dollar amount, external recipient, or low judge confidence triggers review; everything else is sampled for audit. Measure reviewer time per item and the override rate; an override rate near zero means the gate can be loosened, near 100% means the agent is not ready.
- *Multi-LLM orchestration.* A small classifier (or a rule on input length, tool count and risk) assigns each request to a tier; a cost table and a per-node accuracy eval decide which model serves which node; a fallback chain handles provider errors and rate limits; prompts are kept provider-neutral behind a gateway so a swap is a configuration change. Report accuracy-per-dollar per node, not a single model choice.
- *Prompt/context management.* Prompts are versioned files reviewed like code, with a stable prefix first (for caching), evidence trimmed to a token budget, and conversation history compacted into a summary plus the last few turns. Every prompt change runs the eval set in CI before it ships; a prompt without an eval is a bug waiting for a customer.

## 55.4 Core expertise — Retrieval and data systems

- **Knowledge graphs** — entities and typed relationships with an ontology; GraphRAG and text-to-Cypher (chapter 25).
- **Vector search, embeddings** — dense representations and approximate nearest-neighbor search (chapter 18).
- **Pinecone, pgvector, PostgreSQL** — a managed vector DB; the Postgres extension; the relational workhorse (chapters 18, 49).
- **Snowflake, dbt, Airflow** — cloud warehouse; SQL transformation framework; pipeline orchestration (chapters 21, 48).
- **Indexing, similarity retrieval, caching and performance design** — HNSW/IVF indexes, filtered search, response/embedding caches (chapter 18).

## 55.5 Core expertise — Cloud-native delivery

- **AWS Bedrock** — managed model API, Knowledge Bases, Guardrails; **AgentCore** (in the environment line) — agent runtime, gateway, memory, identity, plus (as of 2026) Policy, Evaluations, an Agent Registry and optimization features that propose prompt and tool-description fixes from production traces (chapter 15; verify the current component list before an interview, it changes quarterly).
- **Vertex AI, ADK, A2A** — Google's ML/GenAI platform, renamed the Gemini Enterprise Agent Platform in April 2026 (a resume may keep the old name for the period it describes; write both, "Vertex AI / Gemini Enterprise Agent Platform", so keyword filters match either); the Agent Development Kit; the agent-to-agent protocol, now governed under the Linux Foundation's Agentic AI Foundation (chapters 15, 20, 22).
- **Azure ML, Azure OpenAI, Microsoft Fabric, Azure AI Foundry** — Azure's ML platform, OpenAI models on Azure, the data platform, and the AI app/agent platform, called Microsoft Foundry since November 2025 (chapters 15, 21).
- **Databricks** — lakehouse with Unity Catalog, Mosaic AI (Model Serving, AI Search — formerly Vector Search — Unity Gateway, Agent Framework), MLflow (chapter 21).
- **Security-aware design** — identity propagation, least privilege, data-layer permissions, guardrails (chapter 30).
- **Kubernetes, Docker, Argo CD, CI/CD** — containers, orchestration, GitOps deployment, pipelines (chapter 45).
- **Scalability, resiliency, latency and cost optimization** — stateless services, queues, autoscaling, caching, routing, FinOps (chapters 31, 45, 50).

## 55.6 Core expertise — Observability and operations

- **Structured logging, metrics, tracing** — JSON logs with trace ids, Prometheus-style metrics, OpenTelemetry traces (chapter 29).
- **Model monitoring** — drift, performance decay, data quality (chapter 46).
- **MLflow** — experiment tracking, model registry, tracing (chapters 21, 46).
- **Grafana, Datadog/OpenTelemetry-compatible telemetry** — dashboards and vendor backends fed by OTel (chapter 29).
- **A/B testing** — randomized experiments with guardrail metrics and statistical gates (chapters 17.8, 36.3).
- **Incident diagnosis, performance tuning** — the trace-first ladder; profiling and caching (chapters 29, 39b.2).

## 55.7 Core expertise — ML and deep learning

- **PyTorch, Transformers (Hugging Face)** — the training framework and the model library (chapter 17).
- **XGBoost** — gradient-boosted trees, the tabular default (chapter 17.9).
- **NeuralProphet** — decomposable forecasting (trend, seasonality, holidays, regressors) with a neural layer (chapter 17.9).
- **Autoencoders, VAEs** — compression/reconstruction models for anomaly detection and latent spaces (chapter 17.9, 17.5).
- **CNNs, ViT** — convolutional networks and Vision Transformers for images (chapter 17.3).
- **Audio Spectrogram Transformers (AST)** — ViT over mel-spectrograms for audio tagging (chapter 17.4).
- **Stable Diffusion** — latent diffusion for image generation (chapter 17.5).
- **Forecasting, ranking, optimization** — time-series models; retrieve-then-rank systems; mathematical optimization (the quadratic revenue program in the Xdemand work) (chapters 17.8, 17.9, 58 E).

## 55.8 Experience — agentic marketing process automation at an asset manager

- **Marketing Process Automation (MPA)** — the platform name for agentic workflows that draft, review and fix marketing content (chapter 36.1).
- **Self-improving agentic workflows** — eval-driven optimization and lesson memory with human gates (chapter 22b).
- **Knowledge-graph and RAG pipelines** — rules as a graph, text as retrieval (chapters 24, 25, 51).
- **Model-serving infrastructure** — endpoints, gateways, caching, routing (chapters 31, 46).
- **Delivery plans balancing quality, cost and risk** — acceptance criteria, cost per asset, approval gates (chapters 35, 47).
- **Adobe Workfront** — the work-management system of record for marketing assets; integrated by API.
- **Regulatory data and disclosures** — required statements per product and jurisdiction; graph-modeled (chapter 25).
- **Digital twins for editorial and legal review** — reviewer agents that emulate a reviewer's rubric with their own retrieval (chapters 22, 36.1).
- **Agentic conflict detection and resolution-based planning** — comparing reviewer findings and planning rewrites that resolve conflicts (chapter 22b).

## 55.9 Experience — creative-AI platform (film and sound)

- **Agentic, multimodal and retrieval-based creative workflows** — chapter 36.2.
- **Prompt optimization** — systematic improvement of prompts against evals (DSPy-style) (chapter 22b).
- **Model-serving on GCP Vertex AI, GKE, GPU/TPU serving** — managed endpoints and Kubernetes GPU pools; TPUs for throughput (chapters 15, 45).
- **80% throughput uplift, 90% user-engagement lift** — batching/precision/autoscaling results and the product outcome; know how each was measured (chapter 36.2).
- **Led cross-functional engineering; hiring, architecture reviews, delivery cadence, quarterly roadmap** — leadership evidence (chapter 38).

## 55.10 Experience — ad-tech ranking and pricing

- **Ranking, pricing, forecasting, audience analytics at broadcaster scale** — chapter 36.3.
- **Two-tower deep neural ranking model at 10K QPS** — separate towers for context and ad embeddings, ANN retrieval, scoring at ten thousand queries per second (chapter 17.8).
- **~100% CTR uplift, daily incremental updates** — the measured lift and the retraining cadence; be ready for "how did you validate it" (chapter 36.3).
- **A/B harnesses, statistical gates, rollback paths** — experiment infrastructure and launch discipline (chapter 46).
- **Ad-price elasticity, demand-forecasting models, bid-floor and yield-versus-volume decisions** — pricing economics for ad inventory (chapter 36.3).
- **Embedding-based retrieval for advertiser scoring and look-alike audiences** — similarity search over advertiser/user embeddings (chapter 18).
- **Langfuse, AWS Neptune, Bedrock and AgentCore, pgvector, Argo CD** (environment line) — LLM observability, graph database, agent infrastructure, vector extension, GitOps.

## 55.11 Experience — LLM-first inventory and pricing platform (co-founder)

- **Inventory planning, forecasting, pricing and replenishment workflows with agents** — chapter 36.4.
- **Ask-AI copilot with RAG over reviews and sales data** — chapters 24, 36.4.
- **Helium 10, Jungle Scout, Google Analytics, Linnworks** — Amazon-seller analytics tools (keyword, listing and competitor data), web analytics and order management integrated into one data model; the integration mechanism is nightly batch pulls through each vendor's API or export into a job-status table, then a star schema keyed on SKU, marketplace and day (chapter 48).
- **\$1.5M saved/added revenue, 15% better stock handling, 89% forecast accuracy** — outcomes; know the measurement (chapter 36.4).
- **Azure ML, Databricks, NeuralProphet, XGBoost** — the training and pipeline stack (chapters 21, 46).

## 55.12 Experience — enterprise AI at a utility

- **Smart Agents team, Interim Head of Advanced Analytics** — leadership of an AI portfolio (chapter 44).
- **Optiheat district-heating optimization, time-series forecasting, autoencoders, Azure Data Factory, Databricks, MLOps pipelines, 25% cloud-cost reduction** — chapter 36.5.
- **Customer-service GenAI/chatbot (Hugging Face Transformers, LSTM with self-attention, Flask, CI/CD), +30% intent accuracy** — transformer and recurrent intent models behind a chatbot (chapters 17, 28).
- **Anomaly detection, geospatial scoring, drone-image computer vision (CNNs, VAEs, semantic segmentation, Vertex AI), PostGIS** — pixel-level labeling of imagery and spatial joins to assets (chapters 17.3, 19).

## 55.13 Experience — senior data scientist across a sportswear brand, a telecom operator and an energy innovation hub

- **Customer segmentation, promotional-lift analysis (hierarchical K-means, PCA)** — clustering and dimensionality reduction for retention and promotions (chapter 17; Part 6 uplift guide).
- **Footfall and movement-pattern analytics (Scala, Spark, Kafka streaming, GIS)** — location analytics for retail decisions (chapter 48; chapter 61.7).
- **Rapid AI prototypes, startup evaluation, A/B experimentation, demand forecasting** — innovation-hub work.

## 55.14 Experience — insurance analytics lead

- **Automatic Predictive Modeler (SAS, SQL, SVMs, gradient boosting)** — on-the-fly model building for personalization (chapter 36.6).
- **Churn, next-best-product, risk, propensity, CLV, personalization models; +20% accuracy** — classic predictive modeling with actuaries (chapter 17.9).
- **Pay-how-you-drive telematics (snap-to-road, accelerometer/gyroscope profiling, Hadoop, Spark, MongoDB); explainability and monitoring** — sensor-based driving features and model governance (chapters 36.6, 46).

**The measurement sentence behind every number (sections 55.9 to 55.14).** Sections 55.9 to 55.14 keep saying "know how each was measured"; this is what that means. A number on a resume is only as good as the sentence that defines it; an interviewer who hears a vague definition discounts every other number. Use this pattern: *metric definition, baseline, comparison method, period, caveat.* Replace the illustrative definitions below with your own.

| Resume number | A defensible measurement sentence | The caveat to volunteer before you are asked |
|---|---|---|
| 80% throughput uplift (creative platform) | "Requests per second per GPU at a fixed p95 latency, measured on the same load generator before and after dynamic batching, bf16 inference and autoscaling tuned on queue depth, over a two-week window." | Part of the gain came from batching that increased p50 latency; we accepted that for batch-style creative jobs. |
| 90% user-engagement lift | "Weekly active creators who completed at least one generation-and-export, new cohort versus the pre-launch cohort, over eight weeks." | Cohorts were not randomized; we corrected for seasonality but it is an observational number. |
| ~100% CTR uplift at 10K QPS (ad-tech) | "Click-through rate of the two-tower ranker versus the rules-based baseline in a 50/50 traffic-split A/B over three weeks, significance checked with a sequential test and a revenue guardrail metric." | Lift was measured against a weak baseline; against the tuned logistic model the lift was smaller, and we reported both. |
| Daily incremental updates | "The ranking model retrained on the previous day's impressions every night, with a shadow evaluation gate: the new model had to match or beat the live model on offline NDCG before promotion." | Daily retraining introduced drift in embeddings; we pinned the item tower and refreshed only the context tower on most days. |
| \$1.5M saved or added revenue (inventory platform) | "Sum over SKUs of avoided stockout days times average daily margin, plus overstock reduction times holding cost, computed from the client's own sales and stock tables for the twelve months after go-live." | Attribution is counterfactual; we validated it on a holdout set of SKUs that stayed on the old process. |
| 89% forecast accuracy | "One minus weighted absolute percentage error (WAPE) at the SKU-week grain, over a rolling eight-week horizon, on the top 80% of SKUs by revenue." | Long-tail SKUs were far worse; we used category-level forecasts and safety stock there. |
| 15% better stock handling | "Reduction in days of inventory on hand at constant fill rate, before versus after the replenishment recommendations were adopted." | Adoption was partial; the number is for the SKUs where the buyer followed the recommendation. |
| 25% cloud-cost reduction (utility) | "Monthly cloud bill for the analytics platform, same workload, after moving batch jobs to spot capacity, right-sizing clusters and scheduling pipelines off-peak; compared on a three-month average." | The workload grew the next year, so the absolute bill rose while unit cost fell. |
| +30% intent accuracy (chatbot) | "Macro-F1 over 40 intents on a held-out, human-labeled test set, transformer model versus the previous keyword-plus-LSTM classifier." | Macro-F1 hides that the two largest intents barely moved; the gain was in the rare intents. |
| +20% accuracy (insurance models) | "AUC improvement on the churn model, gradient boosting versus the incumbent logistic regression, on a time-based holdout; other models in the suite moved less." | The biggest gain came from new features (claims recency), not from the algorithm. |

The habit to build: for every number you put on a resume, write this sentence in your truth file (Part 1) the day you add it. Numbers you cannot define this way are the ones to cut.

## 55.15 Research and early career

- **Trajectory analysis, map matching, mobility mining, similarity search, kernel methods, structured prediction** — the PhD: aligning GPS traces to road networks (kernelized map matching) and mining movement patterns; kernel methods and structured prediction are the statistical learning foundations (chapter 17).
- **Data mining / BI team lead in telecom: predictive modeling, segmentation, campaign design, social-network analysis** — early customer analytics (chapter 61.7).
- **Publications and awards (ACM SIGSPATIAL, IEEE; best poster; DAAD scholarship)** — research credibility; be ready to explain one paper in two minutes.

## 55.16 How to use this chapter

For each line, write your own two sentences and one number; where you cannot, either refresh the skill with a lab (chapter 34) or move the term off the resume. Interviewers do not penalize a shorter list; they penalize a term you cannot defend.

**The defense drill and the questions this resume invites.** Reading this chapter is not preparation; answering out loud is. A drill that works: put every bolded term above on a card (there are about eighty), draw ten at random each morning, and answer each in under a minute with the two sentences, the number and the follow-up. Record yourself once a week and listen for hedges ("sort of", "basically"), because those are what an interviewer hears. Then prepare the questions that a resume like this one reliably provokes:

1. "You list three clouds. Which one would you choose for a new agent platform today, and what would you miss from the other two?" (chapter 15; have a real answer with trade-offs, not diplomacy.)
2. "Eighty technologies is a lot. Which five did you use in the last six months?" (name them, with the lab or project.)
3. "Tell me about a time the agentic workflow did something wrong in production." (chapters 38, 53; if you have no story, you have not run one in production.)
4. "How did you decide between fine-tuning and retrieval on the marketing-compliance work?" (chapter 27.)
5. "What did the 15-person team cost and what did it deliver?" (leadership lines get budget questions.)
6. "Which of these numbers would you be least comfortable defending?" (say which, and why, before they find it.)
7. "Walk me through the trace of one request through your system." (chapter 29; draw it.)
8. "What is the difference between MCP and A2A, and when do you need neither?" (chapter 28b.)
9. "What happened with the company you co-founded, and what would you do differently?" (the honest version, with one lesson; chapter 36.4.)
10. "Explain your PhD to a product manager in two minutes." (chapter 55.15.)
11. "What is the one tool on this list you would remove and why?" (shows judgement; chapter 60.)
12. "How do you keep eighty skills fresh?" (chapter 37; the answer is the drill above plus one lab a month.)
