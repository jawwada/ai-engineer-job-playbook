# 36. Use-case thinking: six use cases from one resume, worked from every angle

> **The idea:** interviewers do not hire a list of technologies; they hire someone who can take a business situation and turn it into a system that works, measurably, inside constraints. "Use-case thinking" is the habit of describing any piece of work as *problem → users → data → architecture → models → quality → security → cost → operations → outcome → what I would do differently*. This chapter applies that template to six use cases from the reference resume in Part 4. The facts and numbers come from the resume; the design detail is how such a system is built and discussed, so you can narrate your own work the same way.

## 36.0 The template (memorize the headings)

1. **Business problem and why it mattered** (money, risk, time, people).
2. **Users and stakeholders** (who touches it, who pays, who is afraid of it).
3. **Data** (sources, volume, quality, permissions, freshness).
4. **Architecture** (boxes and arrows; the eleven rows of chapter 14).
5. **Models and methods** (what, why that one, alternatives rejected).
6. **Quality: evaluation and guardrails** (how you knew it worked).
7. **Security, compliance, governance**.
8. **Cost and performance** (latency, throughput, unit economics).
9. **Operations** (deployment, monitoring, on-call, change management).
10. **Outcome** (numbers; adoption; what the business did with it).
11. **Hard parts and lessons** (what broke; what you would change).
12. **Questions an interviewer will ask** and your short answers.

---

## 36.1 Marketing process automation with agentic review (asset management)

**Problem.** A very large asset manager produces thousands of marketing assets a year; every one must satisfy editorial standards, legal review and regulatory disclosure rules that vary by product and jurisdiction. Reviews were slow, inconsistent and expensive; rewrites looped between writers and reviewers. The goal: self-improving agentic workflows that draft, review and fix content with humans approving — faster cycles, fewer escapes, auditable decisions.

**Users and stakeholders.** Marketing writers (speed), editorial and legal reviewers (consistency, auditability), compliance (zero regulatory escapes), IT security (data handling), and the business owner (cost per asset, time-to-market).

**Data.** Marketing assets and their history in a work-management system (Adobe Workfront), brand and editorial guidelines, legal precedents and prior review comments, regulatory data and required disclosures per product and region, product master data. Permissions: assets and legal comments are restricted; disclosures are versioned and dated.

**Architecture.** Ingestion from Workfront via API; a knowledge graph of products → rules → required disclosures → approved claims, built from structured sources and LLM extraction with provenance; RAG over guidelines, precedents and regulatory texts; an orchestrated workflow (LangChain/LangGraph with MCP tools): a drafting or rewriting agent, parallel reviewer agents ("digital twins" of the editorial and legal reviewers, each with its own retrieval and rubric), a conflict-detection step that compares reviewer findings and a planner that proposes resolution-based rewrites, structured outputs for every finding (rule id, span, severity, suggested fix), and a human-in-the-loop review queue in the tool writers already use; multi-LLM routing (cheap models for classification and checks, frontier models for drafting and conflict resolution); model-serving infrastructure and a delivery plan balancing quality, cost and risk.

**Models and methods.** Frontier LLMs for drafting and judgement; mid-tier models for reviewer checks; embeddings + hybrid retrieval; graph queries for disclosure logic (deterministic where the rule is deterministic); judges for evaluation. Rejected: fine-tuning for rules (rules change; graph + RAG is auditable), a single monolithic agent (context bloat; reviewers need isolation).

**Quality.** An eval set of historical assets with the real review outcomes; metrics: escapes (violations missed), false flags, agreement with human reviewers per rule, cycle time; LLM judges calibrated against reviewers; CI gate on the regression set; weekly disagreement review. Guardrails: no claim without a cited source; every finding carries rule id and evidence; humans approve every publication.

**Security.** Enterprise identity throughout; retrieval filtered by permissions; no customer PII in prompts; prompt-injection screening on ingested documents; audit trail of every agent decision and human override (regulators ask for it).

**Cost and performance.** Cost per asset tracked by route; prefix caching of rules and rubrics; reviewers run in parallel so cycle time is bounded by the slowest reviewer, not the sum; batch mode for back-catalog re-reviews.

**Operations.** Versioned prompts and rubrics; traces per asset; dashboards for cycle time, escapes and cost; a change process where legal signs off on rubric changes; rollback of model/prompt versions.

**Outcome (how to state it).** Faster review cycles, consistent application of rules across thousands of assets, an auditable record, and a reusable platform for other content types. Give the numbers you own; if you cannot quote one, describe the measurement.

**Hard parts.** Reviewer "twins" disagreeing with each other and with humans — solved by conflict detection and explicit resolution planning; keeping the disclosure graph current; convincing legal to trust structured findings (evidence spans did it).

**Likely questions.** *How do you stop the agent from inventing a rule?* — findings must cite a graph node or a retrieved passage; unsupported findings are dropped and logged. *How did you measure success?* — escapes and false flags against human review on a frozen set, plus cycle time. *What did the humans do?* — approve, override with reasons, and their overrides fed the eval set.

### Critic's additions: the probes behind the likely questions, and how such a system is typically built

The three answers above will each get a second question. Prepare the mechanism, not the adjective. (Design detail below describes how a system of this kind is typically built; use only the parts that match what you actually did.)

- *"Escapes are violations the humans missed too — how do you measure something nobody caught?"* — Two sources: retrospective findings (regulator or audit comments on already-published assets form the ground truth for escapes) and injected cases (a seeded set of assets with known violations run through the pipeline; escape rate is measured on those). Say which one you had and what the other would cost.
- *"What is the unit of a finding?"* — A typical schema: `rule_id`, `span` (character offsets in the asset), `severity` (block / fix / note), `evidence` (the graph node or passage id that supports it), `suggested_fix`, `confidence`. Legal reviewers trust a finding they can click through to; a finding without `evidence` is dropped before it reaches a human.
- *"The reviewer agents disagree — who wins?"* — Conflict detection compares findings on overlapping spans; precedence is a policy, not a model judgement: regulatory over legal over brand, and any `block` severity stops publication. The planner proposes a rewrite that satisfies all blocking findings; if none exists it escalates with the conflict stated in one paragraph.
- *"How do you keep the disclosure graph current?"* — Typically: structured sources (product master data, disclosure registry) are the system of record and re-ingested on change; LLM-extracted edges carry provenance and a review flag; a graph diff is part of the release notes; a stale-node check (last verified date) runs weekly.
- *"What did a reviewer twin cost per asset, and what was the cycle-time baseline?"* — Have the arithmetic: three reviewer passes × context size × mid-tier price, plus one planner pass on a frontier tier; the baseline cycle time came from the work-management system's timestamps (submission to approval). If you cannot quote a figure, say which timestamps you would pull.
- *"How is this built on Google Cloud?"* (asked by a Google interviewer) — A typical mapping: reviewer and planner agents as ADK `LlmAgent`s inside a `SequentialAgent` wrapping a `ParallelAgent`, deployed on Agent Runtime; rules and precedents in an Agent Search data store with document ACLs; the disclosure graph in Spanner Graph or a Postgres-backed graph with a query tool; Gemini Flash for reviewers with `response_schema` for the finding schema, Gemini Pro with a thinking budget for the planner; Model Armor on ingested documents; findings and human decisions in BigQuery for the eval set; Cloud Trace for per-asset traces.

---

## 36.2 Agentic, multimodal creative platform for film and sound production

**Problem.** A start-up building AI for film and sound production needed an end-to-end platform: creative workflows that combine retrieval over footage and references, multimodal models (vision, audio, image generation), agentic orchestration with human review, and a conversational interface — with engineering leadership across research, ML, backend and DevOps.

**Users.** Filmmakers and sound designers (speed and control), researchers (model iteration), the business (engagement, throughput, cost).

**Data.** Video, audio, scripts, reference images; user projects and versions; usage logs. Large binary assets, rights-sensitive, needing lineage from source to generated output.

**Architecture.** Python/FastAPI backend; agentic workflows in LangGraph with prompt optimization and HITL review stages; Pinecone for retrieval over transcripts, descriptions and embeddings of media; model-serving on GCP Vertex AI and GKE with GPU/TPU serving for ViT (visual classification/retrieval), Audio Spectrogram Transformers (audio tagging) and Stable Diffusion (image generation); a conversational AI layer built in Dialogflow CX — flows, pages, intents, entities, webhook fulfillment to FastAPI — as the web/in-app chat front door to the agentic workflows; asset versioning and review UI; CI/CD and observability.

**Models and methods.** ViT for frame-level understanding; AST over mel-spectrograms for sound events; Stable Diffusion with adapters for concept art variants; LLMs for planning and dialogue; embeddings for retrieval. Rejected or deferred: fully generative video at the time (cost/quality), fine-tuning dialogue models (Dialogflow CX gave deterministic control over the critical paths).

**Quality.** Offline evals per model (classification accuracy, retrieval recall); human review of generated assets; A/B tests on engagement; latency and throughput targets per endpoint.

**Security and rights.** Content provenance and rights metadata; isolation per customer project; model outputs watermarked where appropriate; access control on assets.

**Cost and performance.** The resume reports an 80% throughput uplift on serving — achieved by batching, mixed precision, right-sizing GPU/TPU nodes and autoscaling on GKE — and a 90% lift in user engagement after the multimodal features shipped. Cost per generated asset and per minute of audio processed were the unit economics.

**Operations.** Hiring and leading a cross-functional team; architecture reviews; delivery cadence and quarterly roadmap; incident process for serving.

**Hard parts.** GPU cost discipline for a start-up; keeping research models deployable (packaging, versioning); designing HITL so creatives felt in control; Dialogflow CX's determinism versus the open-endedness of creative requests (solved by routing open requests to the agent and keeping navigation/transactions in flows).

**Likely questions.** *Why Dialogflow CX for the chat layer?* — deterministic flows for navigation and account actions, built-in NLU and channels, webhooks to the agent for open requests. *How did you get 80% throughput?* — batching and precision changes measured with load tests; autoscaling policies. *How do you evaluate generated media?* — human rubric reviews, engagement A/B, and automatic checks (resolution, safety, duplication).

### Critic's additions: the follow-ups on the two headline numbers and on the Dialogflow CX layer

An interviewer at Google will spend most of this use case on the two numbers and the CX layer. Prepare these:

- *"80% throughput — of what, measured how?"* — Give the unit (requests per second or images per second per node at a fixed p95), the baseline configuration, the load-test tool and profile, and which lever contributed what. The levers that typically produce a gain of that size on GPU serving are dynamic batching (a batch window of a few milliseconds that fills requests into one forward pass), mixed precision or lower-precision weights, right-sized node pools and autoscaling on queue depth instead of CPU. If you do not have the per-lever split, say "batching was the largest share; I would have to look up the exact split", which is a professional answer; do not guess a split.
- *"90% engagement lift — what metric, what population, over what period, with what control?"* — Define engagement (sessions per user per week, time in tool, assets completed), state whether it was an A/B or before-and-after, and name the confounders you accounted for (new users, seasonality, the launch itself). "Before/after without a control, attributed conservatively" is an acceptable answer if it is the true one.
- *"What exactly did your webhook do?"* — The contract: the CX webhook request carries the session id, the matched intent and its confidence, the page, the tag you set on the fulfillment, and the session parameters; your service returns messages, parameter updates and optionally a target page or flow. The business logic (project lookups, triggering a workflow, returning results) lived in the service, not in CX; the response must come back inside the webhook timeout (default 5 s, maximum 30 s) or CX fires `webhook.error.timeout`, which you handle with an event handler that tells the user the task is running and how to check it.
- *"How did long-running agentic jobs fit in a chat turn?"* — In a system of this kind the webhook starts the job and returns immediately with a job id in a session parameter; a later page polls or the user asks "is it ready"; results are pushed into the conversation through a custom event or fetched on the next turn. Say which you did.
- *"Why not playbooks (the generative agents inside CX) for the open requests?"* — Depending on when you built it: playbooks either did not exist or were not mature, or the agentic workflows already lived in your backend and the CX layer was the deterministic front door. The answer the interviewer wants today: "I'd keep flows for navigation and account actions, use a playbook with a data-store tool for questions about the product, and call the backend workflows as playbook tools (OpenAPI tools) so one set of tools serves both." On the 2026 product line the same answer reads: a CX Agent Studio agent (the ADK-based evolution of Dialogflow CX in Gemini Enterprise for Customer Experience) with the backend workflows as tools and the navigation and account flows called as flow-based agents — generic design, so say which parts you actually built.
- *"What were the fallback and containment numbers?"* — No-match rate per page, the share of sessions resolved without a human, and the weekly triage that converts no-match utterances into training phrases. If you tracked these, quote them; if not, say which Customer Experience Insights (formerly Conversational Insights) or conversation-history report you would pull.

---

## 36.3 Deep ranking, pricing and forecasting in ad-tech

**Problem.** An ad-tech company serving European broadcasters needed production ML for ranking (which ad to show), pricing (what to charge), forecasting (inventory and demand) and audience analytics across 1,000+ ad-serving entities — at serving scale, with daily updates and safe rollouts.

**Users.** Ad operations and yield managers, advertisers (indirectly), finance (revenue), the platform team (latency and reliability).

**Data.** Impression and click logs at scale, advertiser and inventory metadata, prices and bids, audience segments; streaming and daily batch; strict latency at serve time.

**Architecture.** Feature pipelines (batch + streaming); a two-tower deep ranking model (user/context tower, ad tower) whose item embeddings are precomputed and served through an approximate nearest-neighbor index, with a scoring stage at 10K QPS; daily incremental retraining; an A/B harness with statistical gates and rollback paths; price-elasticity and demand-forecasting models for bid-floor and yield-versus-volume decisions; embedding-based retrieval for advertiser scoring and look-alike audiences; and, in the later phase, agentic and RAG workflows (LangGraph, MCP, AWS Bedrock, pgvector) for analytics and operations assistance.

**Models and methods.** Two-tower neural ranking (PyTorch) for retrieval-scale candidate scoring; gradient boosting and neural models for elasticity and forecasting; embeddings for look-alikes. Rejected: cross-encoder scoring over all candidates (latency), a single monolithic model for pricing and ranking (different objectives and cadences).

**Quality.** Offline AUC/NDCG and calibration on held-out days; online A/B with CTR and revenue; statistical significance gates before full rollout; monitoring for drift and for feedback loops.

**Security and compliance.** Privacy constraints on audience data (GDPR); segment-level rather than user-level features where possible; access controls on advertiser data.

**Cost and performance.** 10K QPS serving with p99 budgets; precomputed embeddings and ANN; feature caching; retraining cost bounded by incremental updates. The resume reports roughly 100% CTR uplift from the ranking model.

**Operations.** Daily training jobs with validation gates; canary deployments; rollback paths; dashboards for serving latency, model freshness and business KPIs; on-call for serving incidents.

**Hard parts.** Position bias and feedback loops in click data; keeping offline and online metrics aligned; training-serving skew; the organizational work of statistical gates (saying no to launches that "looked good").

**Likely questions.** *Why two-tower?* — it makes candidate retrieval a nearest-neighbor lookup at serving time; cross-features are added later in reranking. *How did you handle position bias?* — logging the position, debiasing via inverse propensity or position features at training with position set to a constant at inference. *What is in your A/B harness?* — randomization unit, guardrail metrics, sequential testing or fixed horizons, rollback criteria.

### Critic's additions: the serving, skew and gating probes

- *"10K QPS with a p99 budget — where does the time go?"* — Typical budget for a system of this kind: feature fetch from a low-latency store 2–5 ms, user-tower inference 1–3 ms, ANN lookup over precomputed item embeddings 1–2 ms, scoring and business rules 2–5 ms; the p99 target is usually under 50 ms end to end. Name the tail risks: cold caches after a deploy, index rebuilds, garbage-collection pauses. Say which numbers were yours.
- *"How fresh are the item embeddings, and what happens to a new ad?"* — Precomputed embeddings are refreshed on the retraining cadence (daily here); new items get an embedding at ingestion with a cold-start path (content features, exploration bonus). The failure to name: a daily index that silently serves yesterday's catalog; monitor index age and the share of traffic with missing embeddings.
- *"How did you detect training–serving skew?"* — Log the features as served, replay them offline against the training pipeline, and compare distributions and model scores per feature; the mechanism that prevents it is one feature-computation codebase for both paths. Alert on score-distribution drift per day.
- *"What exactly was the statistical gate?"* — Pre-registered primary metric and minimum detectable effect, the sample size computed from them, guardrail metrics (revenue per impression, latency, error rate) with non-inferiority bounds, a fixed horizon or a sequential test with alpha spending, and a written rollback criterion. The organizational part: the gate is published before the test starts, so "it looks good" cannot change it.
- *"CTR roughly doubled — against what baseline?"* — State the baseline model (for example a logistic or rules-based ranker), the population and period, and whether revenue moved with CTR (a CTR gain that cannibalizes revenue is not a win). If some of this is not yours to quote, say so and describe the measurement.
- *"How would you build the later agentic analytics layer on Google Cloud?"* — Typical mapping: BigQuery as the analytical store with a semantic layer, a read-only SQL tool with row-level security and query cost limits, an ADK agent on Agent Runtime, embeddings and vector search in BigQuery or Vector Search on the Agent Platform (formerly Vertex AI Vector Search), Gemini Flash for routine questions, an eval set of 100 analyst questions with reference SQL.

---

## 36.4 LLM-first inventory, pricing and retail-operations platform

**Problem.** A major Amazon retailer needed to make inventory, pricing and replenishment decisions across marketplaces with data scattered across tools; the co-founded AI product arm built an LLM-first platform from concept to production in nine months.

**Users.** Retail operations and pricing managers, finance, the executive sponsor; later, other retailers.

**Data.** Sales and inventory data, Amazon reviews, marketplace analytics (Helium10, Jungle Scout), web analytics (Google Analytics), order management (Linnworks) — integrated into a unified AI data model.

**Architecture.** Python/FastAPI backend; data integration layer into a unified model; forecasting (XGBoost, NeuralProphet) and pricing-intelligence services; agent-based multi-LLM workflows for inventory planning, forecasting, pricing and replenishment decisions, where the LLM orchestrates tools that call the models and the data model rather than computing numbers itself; an "Ask-AI" copilot with RAG (Pinecone) over reviews and sales data; Azure ML and Databricks for pipelines and training.

**Models and methods.** Gradient boosting and NeuralProphet for demand (hierarchical by SKU/marketplace), pricing heuristics plus elasticity estimates, LLM agents for decision workflows and explanations, embeddings for reviews. Rejected: letting the LLM reason about numbers without tools; a BI dashboard alone (users wanted decisions, not charts).

**Quality.** Forecast accuracy (the resume reports 89%) with backtests by horizon; decision-quality reviews with operations; RAG evals over merchant questions; guardrails so the copilot cites data and never invents SKUs.

**Security.** Tenant isolation per retailer; API keys for third-party sources in a vault; least privilege on marketplace credentials.

**Cost and performance.** Nightly batch for forecasts; on-demand LLM calls routed by complexity; cost per decision and per question tracked.

**Operations.** Release cadence with a small team; monitoring of data-source failures (third-party APIs break); feedback from users into prompts and models.

**Outcome.** The resume reports $1.5M in saved or added revenue and 15% better stock handling, with the platform in production within nine months.

**Hard parts.** Data integration across five tools with different semantics; trust — users needed explanations and the ability to override; keeping forecasting honest on intermittent demand.

**Likely questions.** *How does the agent decide a reorder?* — it calls the forecast and inventory tools, applies policy thresholds, and proposes; a human approves above a threshold. *How did you measure revenue impact?* — before/after on stockouts and overstock with controls, attributed conservatively. *Why multi-LLM?* — cost routing and task fit; a cheap model classifies, a stronger one explains.

### Critic's additions: the forecasting and decision-quality probes

- *"89% forecast accuracy — which metric, at which level, at which horizon?"* — Say the metric (1 − WAPE or 1 − MAPE are the usual definitions behind an "accuracy" figure; MAPE is undefined on zero-demand weeks, which matters for intermittent SKUs), the aggregation level (SKU × marketplace × week), the horizon (one to four weeks ahead), and the baseline (seasonal naive or the previous process). An interviewer will accept "weekly WAPE at SKU-marketplace level, 2-week horizon, versus a seasonal-naive baseline" and will not accept "89% accurate".
- *"How do you forecast intermittent demand?"* — Typical methods: Croston or TSB for intermittent series, zero-inflated or hurdle models, or classifying SKUs by demand pattern (smooth, intermittent, lumpy) and routing each class to a different model; evaluate with scale-free metrics (RMSSE) rather than MAPE. Name the one you used or would use.
- *"What stops the LLM from inventing a number?"* — The agent never computes: it calls `forecast(sku, horizon)`, `inventory_position(sku)`, `lead_time(supplier)` and a `reorder_policy` tool that applies the thresholds; the LLM composes the explanation from tool outputs, and the structured proposal (`sku`, `quantity`, `reason`, `evidence`) is validated before a human sees it. A test asserts that every number in the explanation appears in a tool output.
- *"How did you attribute $1.5M?"* — Before/after on stockout days and overstock value with a holdout set of SKUs or marketplaces where possible, seasonality adjusted, counted conservatively (only effects the operations team signed off on). If the figure includes revenue the business attributed to the platform rather than a measured increment, say that plainly.
- *"How does a system like this map onto Google Cloud today?"* — Typical mapping: BigQuery for sales and inventory, BigQuery ML or the Agent Platform's training pipelines (Vertex AI Pipelines, in the old naming) for the forecasters, the agent on Agent Runtime with ADK tools over BigQuery and the marketplace APIs, Gemini Flash routing with Pro for explanations, review-embedding retrieval in Vector Search (formerly Vertex AI Vector Search) or BigQuery vector search, Looker for the decision dashboards, Cloud Scheduler and Cloud Run jobs for the nightly batch.

---

## 36.5 Enterprise AI at a utility: district-heating optimization, customer-service GenAI, and inspection vision

**Problem.** Europe's largest energy utility ran a portfolio of AI use cases: optimize district-heating production against demand forecasts (energy and cost), modernize customer service with GenAI chat capabilities, and detect anomalies and asset issues from sensors, geospatial data and drone imagery across energy, broadband and water assets — while building and leading the team that did it.

**Users.** Heat-plant operators, customer-service centers, asset-management and inspection teams, executives sponsoring the portfolio.

**Data.** Time series from plants and weather; customer conversations; sensor streams; GIS layers; drone images. Highly regulated (critical infrastructure, customer data).

**Architecture.** Optiheat: forecasting pipelines (NeuralProphet and autoencoder-based anomaly detection) on Azure Data Factory and Databricks with MLOps pipelines; optimization logic on top of forecasts. Customer service: Hugging Face Transformers and an LSTM with self-attention for intent classification, Flask services, CI/CD, with GenAI capabilities layered on. Vision: CNNs, VAEs and semantic segmentation on drone images with Vertex AI; geospatial scoring with PostGIS.

**Models and methods.** Decomposable forecasting with NeuralProphet (trend, seasonality, holidays, regressors like weather), autoencoders for anomaly scores, transformer intent models, segmentation networks. Rejected: pure deep sequence models without decomposition (operators needed interpretable components), generic chatbots without domain intents.

**Quality.** Forecast error by horizon; operator acceptance; intent accuracy (the resume reports +30%) on labeled transcripts; segmentation IoU with field validation; anomaly precision at the alert budget.

**Security.** Critical-infrastructure data residency; access controls; model monitoring as part of governance.

**Cost and performance.** The resume reports 25% lower cloud cost for the heating use case through pipeline redesign and right-sizing; batch inference where real time was not required.

**Operations.** MLOps pipelines with retraining and validation; portfolio governance (acceptance criteria per use case); a team of about fifteen to hire, grow and run.

**Hard parts.** Translating executive use cases into architectures, roadmaps and acceptance criteria; data access across business units; sustaining models after launch (ownership).

**Likely questions.** *How did you cut cloud cost 25%?* — scheduled compute, right-sized clusters, incremental pipelines, cheaper storage tiers, fewer redundant retrains. *How do you evaluate an intent model in production?* — sampled labeling, confusion matrices on top intents, fallback rate, containment. *How did you prioritize the portfolio?* — value × feasibility × data readiness, with acceptance criteria agreed before build.

### Critic's additions: the FinOps and customer-service probes an Applied AI interviewer will add

- *"25% of what, and which lever gave the most?"* — State the baseline (monthly spend of the pipeline's resource group or project), the measurement (billing export by tag before and after), and rank the levers. In pipelines of this kind the largest single saving usually comes from not retraining what has not changed (incremental runs with a data-change trigger) and from scheduling clusters to terminate after jobs; right-sizing and storage tiers are second order. Be ready to say which was true for you.
- *"+30% intent accuracy — from what, on what set?"* — Baseline model and its accuracy, the labeled test set size and how it was labeled (two annotators, agreement), and whether the gain held on production traffic (sampled weekly labeling). The follow-up "how did you handle class imbalance across hundreds of intents?" expects: per-class metrics on the top intents by volume, a fallback threshold tuned on the confidence distribution, and a "other" class.
- *"How would you build the customer-service piece today?"* — The honest modern answer: Conversational Agents (Dialogflow CX) with flows for identity verification, outage reporting and billing actions, a playbook with a data-store tool over the policy and tariff documents, generative fallback for no-match, Agent Assist for the human agents, Customer Experience Insights (formerly Conversational Insights) for drop-off analysis; LSTM intent classifiers are replaced by CX NLU plus Gemini, and the measurement stays the same — containment, fallback rate, CSAT, handoff quality. On the 2026 product line (Gemini Enterprise for Customer Experience) a new build would start in CX Agent Studio, with the identity and billing steps as flow-based agents and the tariff questions answered by an LLM agent with a data-store tool.
- *"Critical infrastructure — what did residency and governance actually require?"* — Data stays in-region (EU regions and Assured Workloads on Google Cloud, equivalent controls elsewhere), model monitoring and retraining approvals documented per use case, access by business unit with audit logs, and a model register with owners. Say which of these you ran and which you would add.
- *"How do you keep fifteen people's models alive after launch?"* — One owner per model in the register, a retraining and validation pipeline with alerts on data-quality and forecast-error thresholds, a quarterly review of models nobody uses (decommission is a result too).

---

## 36.6 Predictive modeling and telematics at an insurer

**Problem.** A global insurer wanted personalized digital experiences and better risk and retention decisions: a predictive-modeling service that builds models on the fly for web properties; churn, next-best-product, propensity, risk and customer-lifetime-value models with actuaries; and pay-how-you-drive telematics features from smartphone sensors.

**Users.** Digital and marketing teams, actuaries and pricing, product owners, compliance.

**Data.** Customer and policy data (sensitive, regulated), web behavior, and telematics streams (GPS, accelerometer, gyroscope) requiring map matching and feature engineering.

**Architecture.** The "Automatic Predictive Modeler": a service (SAS, SQL, SVMs, gradient boosting) that trains and scores models on demand for personalization; batch pipelines for churn/CLV/propensity; a telematics pipeline on Hadoop/Spark/MongoDB with snap-to-road (map matching — the PhD topic), accelerometer/gyroscope profiling, and explainability and monitoring practices.

**Models and methods.** Gradient boosting and SVMs for tabular prediction; survival and uplift ideas for churn and retention; engineered driving-behavior features. Rejected: black-box models without explanations (actuaries and regulators required interpretability).

**Quality.** The resume reports 20% accuracy gains versus baselines; validation with actuaries; stability monitoring; explainability reports.

**Security and compliance.** Insurance regulation and data protection; model governance (documentation, approval, monitoring).

**Hard parts.** Data quality in telematics; aligning data science with actuarial standards; productionizing in a conservative enterprise.

**Likely questions.** *How do you explain a gradient-boosting churn model to an actuary?* — SHAP values, partial dependence, monotonic constraints, and a validation report. *What is map matching?* — aligning noisy GPS traces to the road network with a probabilistic model (kernelized map matching in the PhD work). *How do you prevent leakage in churn models?* — point-in-time features, label windows, no post-outcome signals.

### Critic's additions: the probes on telematics and governance

- *"20% accuracy gain — which metric and against which baseline?"* — For churn, AUC or lift in the top decile against the previous production model or a logistic baseline; for propensity, precision at the contact budget. Say the metric first; "accuracy" alone invites the follow-up.
- *"Map matching: what did you compare against, and why kernelized?"* — The standard baseline is a hidden-Markov-model matcher (emission from GPS-to-road distance, transition from route plausibility, Viterbi decoding). A kernel method trades the explicit state model for a learned similarity between trace segments and road segments; the case for it is robustness to noisy, sparse traces. The interviewer wants the comparison and the failure cases (parallel roads, tunnels, low sampling rates), not the derivation.
- *"How did driving features become pricing features?"* — Trip segmentation, event detection (harsh braking and acceleration from accelerometer thresholds after orientation correction), exposure normalization (events per 100 km), aggregation to a policy period, and stability checks before any feature reaches an actuarial model.
- *"What did model governance require, concretely?"* — Documentation per model (purpose, data, validation, limitations), independent validation, approval before deployment, monitoring with defined thresholds, and a change log; a model the regulator could ask about at any time.

---

## 36.7 Using the template on your own work

Write each of your three to six biggest projects under the twelve headings, two or three sentences each. Where a number is missing, either find it or describe the measurement you would run. Then compress each into a 90-second STAR story (chapter 38) and a 30-second headline. This file — not the resume — is what you study the night before an interview.

### Critic's additions: the number-defense card

Every number on a resume is a question in waiting. For each one, write a five-line card before the interview and keep it next to the use-case file:

1. **Metric and definition** ("1 − WAPE at SKU-week level", not "accuracy").
2. **Baseline** (what it was compared against, and when).
3. **Measurement** (dataset or period, who measured, with what control).
4. **Attribution** (your share versus the team's; what else changed at the same time).
5. **Caveat** (the one honest limitation you say before they find it).

An interviewer scoring "professionalism and ownership" rewards the candidate who answers in the shape "the figure is weekly WAPE on the high-volume SKUs; on the long tail it was lower, which is why we kept human review there" (an illustrative shape, not a fact from the reference resume — fill in your own definitions) over the one who repeats the headline number.
