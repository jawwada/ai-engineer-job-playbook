# 35. Reading a job description: the problem behind the posting, and the interviewer's shoes

> **The idea:** every job announcement is a company saying *we have a problem we cannot solve with the people we have*. The posting is a compressed description of that problem, written by someone who will have to live with the hire. If you can reconstruct the problem, the system they are probably building, and the person who wrote the posting, you walk into the interview already on their side of the table.

## 35.1 The four readings of a JD

Read every JD four times with four different questions:

1. **What is broken or missing?** Underline every verb and noun that implies pain: "scale", "productionize", "modernize", "reduce", "migrate", "reliability", "governance", "stakeholders". A JD that says "take proofs-of-concept to production" is telling you the POCs exist and are stuck. "Translate use cases into technical designs and acceptance criteria" means the business cannot write requirements and engineering cannot read them.
2. **What system are they building?** Map the must-have skills onto the eleven rows of chapter 14. Eight skills that say Python backend, agent orchestration, APIs, LLM apps with structured outputs, retrieval, AWS, CI/CD and observability describe one system: an agentic RAG platform on AWS with a React front end, integrated into enterprise tools, that someone has to run. Draw it before the interview (section 35.4).
3. **Who wrote it and who will interview you?** The hiring manager's language shows through: "strong engineering practices (testing, code quality, error handling)" means they were burned by prototype code; "communicate trade-offs across quality, cost, risk and timelines" means they report to a business owner who asks about cost. The interviewer wants to hear their own problems described back to them with a plan.
4. **What would success look like in 90 days?** Write it down as three outcomes ("the document-QA agent answers 70% of policy questions with citations; the pipeline has traces and an eval gate; two business teams onboarded"). You will use this sentence in the interview and in the cover note.

## 35.2 Worked example: the anonymized posting in Part 6

The posting (`part-6-reference-guides/interview-practice/example-job-description-agentic-backend.md`) reads, in short: a contractor to support the design and delivery of agent-based, AI-enabled workflows that integrate with enterprise systems, working closely with business stakeholders; must-haves: Python backend, agent-oriented workflow development, API development and integration, LLM-enabled apps (prompt and context management, structured outputs), retrieval systems (vector search, indexing, embeddings), AWS cloud-native development, CI/CD and environment management, observability; plus React-enablement, IAM/security, scalability, incident diagnosis, and translating use cases into designs and acceptance criteria.

**Reading 1 — the pain.** "Support the design and delivery" plus "translate use cases" plus "acceptance criteria" says: there is a backlog of business use cases, no one is turning them into buildable specs, and earlier attempts did not reach production ("robust, scalable solutions"). "Supervisor/sub-agent patterns" and "multi-step, asynchronous workflows" say they already tried single-prompt bots and hit the wall. "Observability … incident diagnosis" says something is in production and nobody can tell why it fails. "Caching for performance and scalability" says cost or latency has already hurt.

**Reading 2 — the system.** A React front end → API gateway → Python (FastAPI) services → a supervisor agent that routes to sub-agents (query planner, retrieval agent, validation/output agent) → tools over enterprise APIs through secure gateways → retrieval over S3-stored documents with a vector index (OpenSearch/Aurora pgvector/Bedrock Knowledge Bases) and caching (ElastiCache/DynamoDB) → async workflows (SQS/Step Functions/EventBridge) for long-running steps → structured, validated outputs (Pydantic schemas) → logging, metrics, tracing (CloudWatch/OTel) → CI/CD (GitHub Actions/CodePipeline, environments, IaC). Part 6's *Agentic RAG system design walkthrough* draws exactly this; chapter 40 drills it.

**Reading 3 — the interviewer.** An engineering lead who owns delivery to business stakeholders and has been promised "AI agents" by vendors. They will ask: how do you keep agents reliable (patterns, budgets, validation), how do you integrate with systems that have no API, how do you prove it works (evals, traces), what it costs, and how you talk to the business (acceptance criteria, trade-offs). They will value: a calm structure, numbers, and stories where you were the one who turned ambiguity into a plan.

**Reading 4 — 90 days.** "In 90 days: two use cases in production behind an API with structured outputs and traces; a supervisor/sub-agent template the team reuses; an eval gate in CI; a one-page cost and latency report per use case; business owners signing acceptance criteria before build."

### Critic's additions: the same four readings for a cloud-provider Applied AI / FDE posting

The example above is a customer-side posting on AWS. A provider-side Applied AI / Forward Deployed Engineer posting (Google Cloud is the running example in chapters 39b and 39c) reads differently, and the reading must change with it.

**Reading 1 — the pain.** "Help customers move from pilot to production", "scale from thousands of internal users to millions of external ones", "troubleshoot high-traffic agent deployments", "enable the customer's team" say: customers have built demos on the platform that fall over on identity, cost, latency and evaluation; the provider's own product teams need field feedback; and the team is measured on customer production launches, not on code. "Travel up to X%" and "workshops" say the job is half consulting.

**Reading 2 — the system.** The implied stack is the provider's agent platform end to end. On Google Cloud in late 2026 that is the Gemini Enterprise Agent Platform (the April 2026 evolution of Vertex AI; many docs, SDKs and interviewers still say "Vertex AI"): Gemini models through Model Garden, the Agent Development Kit (ADK), Agent Runtime (formerly Agent Engine) with Agent Sessions and Memory Bank, Agent Identity, Agent Registry and Agent Gateway with Model Armor, Agent Simulation, Agent Evaluation and Agent Observability; Agent Search (formerly Vertex AI Search) and RAG Engine for retrieval; Gemini Enterprise for Customer Experience (formerly the Customer Engagement Suite) for voice and chat, with CX Agent Studio as the ADK-based evolution of Dialogflow CX and Dialogflow CX itself still running existing flow-based agents; BigQuery, Pub/Sub and Dataflow for data; Cloud IAM, VPC Service Controls and Sensitive Data Protection for the security lens; Cloud Trace, Logging and Monitoring for operations. Draw that stack before the interview and be able to say, for each box, what it enforces, what it costs and how it fails.

**Reading 3 — the interviewer.** A lead on the Applied AI team who has watched customer pilots fail for predictable reasons (no evals, no cost attribution, permissions bolted on last, a demo that cannot take load). They score against named lenses — AI/ML engineering, operational excellence, security/privacy/compliance, scalability, performance and cost — and the explicit instruction to the candidate is "avoid being high level". They want product names with parameters, numbers from real or napkin arithmetic, and ownership language.

**Reading 4 — 90 days, written for a customer engagement.** "In 90 days: one customer use case in production on Agent Runtime behind the customer's identity provider, with ACL-filtered retrieval, Model Armor on prompts and responses, traces in Cloud Trace, a 200-case eval set gating releases in Cloud Build, a cost-per-task dashboard the customer's finance team accepts, and the customer's two engineers able to ship the next agent without me."

**Three questions to add to the five in 35.3 for this kind of posting.** "Which customer use case most recently stalled between pilot and production, and on which lens?" "How much of the role is building versus enabling the customer's team?" "What product feedback has the team pushed back to engineering this quarter, and what changed?"

## 35.3 Turning the reading into interview material

- **Three stories** (chapter 38) matched to the three biggest pains: one where you took a POC to production, one where you fixed reliability/observability, one where you turned a vague use case into acceptance criteria.
- **One architecture** you can draw in five minutes (section 35.4), with the places you would ask the interviewer questions ("where do the documents live today? what identity provider? what is the latency expectation?").
- **Five questions to ask them**, each showing you understand the problem: "Which use cases are stuck between POC and production, and what stopped them?", "How are stakeholders writing requirements today?", "What does the on-call look like for the agent workflows?", "What is the cost ceiling per transaction the business will accept?", "What would make the first 90 days a success for you?"
- **A tailored resume** (chapter 7) whose headline and three profile bullets echo the JD's words with your numbers next to them.

## 35.4 Understand and practice the architectural components

For every system you infer from a JD, list the components and make sure you can do three things with each: explain it in two sentences, name two alternatives, and say how you would test it. For the example above:

| Component | Two sentences | Alternatives | How you test it |
|---|---|---|---|
| Supervisor / sub-agents | A router agent decomposes requests and delegates to specialists with their own tools and fresh context; it merges results and owns the conversation state. | single agent with many tools; fixed workflow graph | task-success evals, tool-selection accuracy, cost per request |
| Retrieval pipeline | Documents are parsed, chunked with context, embedded and indexed with BM25 + vectors; queries are rewritten, hybrid-retrieved, reranked and filtered by permission. | managed KB (Bedrock), long context | recall@k on a gold set, ACL negative tests |
| Structured outputs | Schemas (Pydantic/JSON Schema) constrain model output; validation and repair loops make it safe for downstream code. | free text + parsing | schema-pass rate, repair rate |
| Async workflows | Long steps run as jobs (queue + workers + durable state); the API returns job ids; clients poll or receive webhooks. | synchronous calls with timeouts | load tests, idempotency tests |
| Observability | OTel traces per request with model/tool/retrieval spans; metrics for p95, cost, errors; logs with trace ids. | vendor SDK only | a trace for a failing run; dashboards |
| CI/CD and environments | IaC (Terraform/CDK), pipelines with tests and eval gates, dev/stage/prod with separate keys and data. | manual deploys | a pipeline run; rollback drill |
| IAM and security | least-privilege roles, user identity propagated to tools, secrets in a vault, guardrails on inputs/outputs. | shared service accounts | negative access tests, injection tests |

Practice means building a small version of each (chapter 34's labs) — the difference between "I know what a supervisor agent is" and "I built one; here is what broke" is the difference between a screen and an offer.

### Critic's additions: three rows the table misses, and the "how it fails" column

An interviewer who has been told to avoid high level will not accept "two sentences, two alternatives, one test" for a component without hearing how it fails in production. Add a fourth question to every row — *how does it fail, and how would I know* — and add the three rows that Applied AI postings in 2026 assume:

| Component | Two sentences | Alternatives | How you test it | How it fails and how you know |
|---|---|---|---|---|
| Cost attribution (FinOps) | Every model call carries feature, route, model, prompt version and token counts (input, cached, output, thinking) as trace attributes; a nightly join with the price table gives cost per request and per task. | billing export only (no per-feature view); gateway metering | a cost-per-task panel reconciled to the billing export within 5% | silent cost growth from loops and retries; alert when cost per task exceeds 2× the 7-day median or a run exceeds its budget |
| Conversational / voice layer | Deterministic flows for identity, payment and confirmation; LLM playbooks or an agent for open requests; webhooks into the backend; streaming speech at every stage. | pure LLM chat; IVR menus | golden-transcript test cases in CI; a simulated-user suite; a latency budget per stage | no-match spirals, slow webhooks inside the turn budget, intent collisions; fallback rate per page and webhook p95 tell you |
| Evaluation service (judges and gates) | Human-labeled gold sets per criterion, calibrated LLM judges, CI gates with thresholds, production sampling with a human review queue. | manual spot checks; vendor dashboards only | judge agreement with humans per criterion (κ ≥ 0.7) and the gate blocking a known-bad change | judge drift after a model change; one holistic score hiding regressions; re-calibrate on every judge change |

For the existing rows, the failure column reads: supervisor/sub-agents — runaway loops and context bloat (max turns, cost per run, repeated-tool-call detection); retrieval — recall collapse after a filter or embedding change (recall@10 on the gold set in CI); structured outputs — schema drift and repair loops (schema-pass and repair rates); async workflows — duplicate side effects on retry (idempotency keys, dead-letter queue depth); observability — traces without identity or token counts (a trace review in the first week); CI/CD — prod keys in staging (environment separation tests); IAM — permissions in vector metadata but not enforced in the query (negative access tests).

## 35.5 Red flags and how to read them

"Rockstar/ninja", seven roles in one (data engineer + ML + full-stack + DevOps), "fast-paced" with no mention of testing, must-haves that no single person has (ten frameworks, three clouds, "expert" everywhere), vague "AI initiatives" with no product — these mean an unclear problem or an unclear owner. Still apply if the pay and the people are right, but ask the problem questions early; a company that cannot answer "what is broken" will not be able to tell you when you have succeeded.

### Critic's additions: reading a provider-side Applied AI / FDE posting for what it does not say

Provider-side postings are written to attract many profiles, so the signal is in the specifics and in what is missing:

| Line in the posting | What it usually means | The question that confirms it |
|---|---|---|
| A list of frameworks (ADK, LangGraph, CrewAI) and patterns (ReAct, chain of thought) | the team meets customers on whatever they already use; depth in one plus fluency in the vocabulary is enough | "Which framework do most of your engagements end up on?" |
| "Contact center", "CCAI", "conversational AI" | a share of the work is Gemini Enterprise for Customer Experience — CX Agent Studio and Dialogflow CX — not only custom agents | "How much of the work is customer-experience agents versus custom agent builds?" |
| "Thousands of internal users to millions of external users" | the scalability lens is scored; bring capacity and cost arithmetic | "What is the largest deployment the team supports today, in requests a day?" |
| "Travel" without a percentage | ask, and ask where the customers are | "What share of time is on site, and in which regions?" |
| No mention of evaluation or observability | either the team assumes it, or customers lack it and you will build it — both are good news for a candidate who leads with it | "How do your customers gate releases today?" |
| "Feedback to product teams" | the team is measured partly on product influence; have a story where field evidence changed a product or platform decision | "What did the team push back to product this quarter?" |

The rule from 35.1 holds: reconstruct the problem, then prepare the evidence that you have solved it before.

## 35.6 A 20-minute JD routine (what `/interview-prep` in the kit automates)

1. Paste the JD; extract must-haves, nice-to-haves, pains, and the implied system (5 min).
2. Map each must-have to your evidence (bullet, project, years) and mark gaps honestly (5 min).
3. Draw the architecture and list the questions you would ask (5 min).
4. Pick three stories and write the 90-day sentence (5 min).

Do this for every interview and you will never again be surprised by "so, tell me how you would approach our problem".
