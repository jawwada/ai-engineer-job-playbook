# 40. AI system design: how to run the whiteboard, and eight worked exercises

> **The idea:** system-design rounds for AI roles test whether you can turn a vague product ask into an architecture with trade-offs, numbers and a plan — in 45 minutes, while talking. The method is fixed; the content changes. Chapter 40b has the distributed-systems fundamentals these exercises assume and eight infrastructure-level questions in the Google style. Go deeper: Part 6 → *Agentic RAG system design walkthrough* and *AI/backend engineer deep dive* §12.

## 40.1 The 45-minute method

| Minute | Step | What you say and draw |
|---|---|---|
| 0–5 | **Clarify** | users, volume (requests/day, documents, QPS), latency and accuracy expectations, data sources and permissions, budget, what "done" means; write them in a corner |
| 5–10 | **Requirements and metrics** | functional (what it must do), non-functional (p95, availability, cost per request, compliance); the two or three metrics you will optimize |
| 10–25 | **Architecture** | draw the eleven-row stack as needed: channels → API → orchestration/agent → models → tools → retrieval → data → identity/guardrails → observability/evals; talk through one request end to end |
| 25–35 | **Deep dive** | pick the hardest component (retrieval quality, agent reliability, permissions, latency) and design it in detail with alternatives |
| 35–40 | **Quality, cost, operations** | eval set and gates, cost per request with numbers, deployment, monitoring, failure modes and fallbacks |
| 40–45 | **Roadmap and questions** | MVP in 6 weeks, v2, what you would validate first; invite the interviewer's constraints |

Habits: say the trade-off every time you draw a box; put numbers on arrows (tokens, QPS, latency); name the human path; mention evals before they ask; when stuck, go back to the metric.

### The four calculations to write in the corner, and the lens check

Interviewers who say "avoid being high level" are listening for arithmetic. Do these four in the first ten minutes, out loud, with round numbers:

| Calculation | Formula | Example |
|---|---|---|
| Throughput | requests a day ÷ 86,400 × peak factor (3–5 for consumer evenings, about 10 for business-hours internal tools) | 100,000 a day → 1.2 QPS on average, about 10 at peak |
| Tokens per second at peak | peak QPS × tokens per request (input plus output; include cached input, which still consumes throughput — check the model's Provisioned Throughput burndown rates for how much) | 10 QPS × 6,400 tokens = 64,000 tokens a second — a Provisioned Throughput sizing input |
| Cost per request | uncached input × input price + cached input × cached price + (output + thinking) × output price + per-call fees (search, ranking, speech) | 3,500 × \$0.75 + 2,500 × \$0.075 + 400 × \$3.75 per million ≈ \$0.0043 on Gemini 3.8 Flash at introductory prices |
| Latency budget | the p95 target split across hops, smallest first | 3 s = 50 ms auth + 300 ms rewrite + 250 ms retrieval + 150 ms rerank + about 2.2 s generation |

Then run the lens check before minute 40 — AI/ML engineering (model choice and evals), operational excellence (deploy, observe, roll back), security, privacy and compliance (identity, data boundaries, audit), scalability (what breaks first at 10×), performance and cost (the two numbers above) — and name any lens you have not touched.

## 40.2 Exercise A — Enterprise document assistant with permissions (RAG)

*Ask:* 20,000 employees ask questions over 2M documents across HR, legal and engineering; answers must be cited and respect access rights; p95 under 3 s; cost under \$0.02/query.

*Design.* Ingestion pipeline (connectors → parsing → structure-aware chunks with contextual summaries → embeddings + BM25 → index with ACL metadata; event-driven refresh). Query path: auth (OBO) → query rewrite (cheap model) → hybrid retrieval with permission filters → reranker to 8 chunks → answer with citations and abstention on a mid-tier model → grounding check → response; cache embeddings and frequent answers per permission set. Evals: retrieval set (recall@10 ≥ 0.85), answer set (faithfulness ≥ 0.95, abstention correct), ACL negative tests; p95 and cost tracked. Deep dive: permissions (ACL sync from source systems, filter semantics in the vector store, tenancy tests). Cost: ~6k input tokens with 2.5k cached, 400 output on a \$2/\$10 model ≈ \$0.012. Roadmap: HR corpus first, then legal with stricter review.

### Exercise A on Google Cloud, with the numbers and four follow-ups

**The build in 2026 names.** Connectors into an access-controlled Agent Search data store (formerly Vertex AI Search) with document ACLs synced from the sources and Workforce Identity Federation to the company's IdP; the Layout Parser for PDFs and tables; the Ranking API to rerank and the Check Grounding API to verify the answer's claims against the passages; Gemini 3.8 Flash for the answer with citations, Flash-Lite for query rewriting; an ADK agent on Agent Runtime with an Agent Identity; Model Armor on prompts and retrieved passages; traces in Cloud Trace and judge scores in BigQuery. If the customer wants control of chunking and embeddings, RAG Engine or Vector Search with `restricts` for ACL groups instead of Agent Search — and then the ACL sync is yours to build.

**The numbers.** 20,000 employees × 5 questions a day = 100,000 a day, about 1.2 QPS on average and 10 at peak. Index: 2 million documents × about 10 chunks = 20 million chunks; at 768 dimensions in float32 that is about 61 GB of raw vectors before index overhead (a managed service hides this, a self-managed one does not). Embedding the corpus once: about 10 billion tokens at 500 tokens a chunk — at roughly \$0.15 per million tokens for a Gemini embedding model, about \$1,500, which is also the price of every full re-embedding. Model cost per query about \$0.0043 (40.1), leaving most of the \$0.02 budget for search and ranking calls; price those per thousand queries from the pricing page. Latency: a 3-second p95 to the last token leaves about 2 seconds for generation, so either cap answers near 250 tokens or agree that the 3 seconds means time to first token with streaming — ask.

**Four follow-ups.**
- *"Someone loses access to a document. How fast does the answer change?"* — As fast as the connector's ACL sync; state the sync interval as an SLO (for example under one hour), test it with a revocation in staging, and for urgent revocations trigger an incremental sync instead of waiting.
- *"The answer exists only in a document the user cannot see."* — Abstain with "I couldn't find this in sources you have access to" — no snippet, no title, no hint that it exists — and log the abstention so content owners can decide whether the document should be broader.
- *"We're changing the embedding model."* — A second index built in parallel, shadow queries against both, recall@10 compared on the gold set, cut-over by alias, the old index kept for a week; budget the full re-embedding cost and run it in batch.
- *"Half the corpus is scanned PDFs with tables."* — Layout-aware parsing with OCR, tables kept whole as markdown with their captions, figures captioned by a multimodal model, and a retrieval gold set that includes table questions so the gain is measured.

## 40.3 Exercise B — Customer-support agent with actions

*Ask:* resolve 60% of chat contacts without a human for a subscription business; actions include refunds (≤ \$100 automatic), plan changes, address updates; 50k conversations/day.

*Design.* Supervisor agent routing to billing/technical/account sub-agents with 3–5 typed tools each over the CRM/billing APIs; RAG over help content; deterministic steps for identity verification and refunds above threshold (approval queue); conversation memory in a session store; handoff to humans with summary and state; guardrails (policy statements, PII); judges sampling 5% daily; simulated-user evals for regression. Deep dive: tool design and authorization (refund tool enforces limits; policy engine; audit). Cost routing: Haiku/Flash tier for most turns, frontier for escalation decisions. Metrics: containment, CSAT, refund error rate, escalation accuracy, cost per conversation.

### The refund tool's contract, honest containment, the numbers, and four follow-ups

**The refund tool is where the design is judged.** `issue_refund(order_id, amount, reason_code)` resolves the customer from the session token (no customer-id argument), checks that the order belongs to that customer, enforces `amount ≤ min(100, order_total − refunds_so_far)` in code, allows one automatic refund per order and a velocity limit per account (for example two in 30 days), requires an idempotency key, and returns a structured status (`issued`, `needs_approval`, `rejected` with a reason). Anything above the limit goes to an approval queue with the conversation summary. The model can ask for a refund; it cannot grant one the policy forbids, however the customer phrases it.

**Containment that survives scrutiny.** Count a conversation as contained only if it reached a defined success state and the customer did not come back about the same issue within seven days; report transfer rate by reason and the seven-day recontact rate next to containment, because a bot that never transfers also "contains".

**The numbers.** 50,000 conversations a day × 8 turns = 400,000 turns, about 5 a second on average and 20 at peak. At the blended cost per turn of chapter 39b's worked example (about \$0.007) that is about \$2,800 a day, roughly \$0.06 per conversation before tools; at 60% containment, 30,000 contacts a day no longer reach a human — the business case is in that line, not in the token bill.

**Four follow-ups.**
- *"A customer pastes text telling the agent to refund \$5,000."* — The tool caps the amount and checks ownership regardless of the prompt; the attempt is logged and counted, and repeated attempts raise the account's fraud score.
- *"Plan changes involve proration."* — The billing API computes it; the model reads the result back. Money arithmetic is never generated.
- *"How do you design the handoff?"* — A summary, the verified identity status, the collected parameters, the actions already taken (with their statuses) and the reason code, delivered to the human's console; measure the repeat-information rate after transfer.
- *"What would you put on Google Cloud?"* — CX Agent Studio or Dialogflow CX for identity verification and refunds as deterministic flows, LLM agents with tools for the rest, the CRM and billing tools behind Agent Gateway, Agent Assist for human agents, Customer Experience Insights for topic and drop-off analysis.

## 40.4 Exercise C — Drive-through voice ordering agent

*Ask:* take orders at 500 restaurants with 95% order accuracy, first response under 1 s, handoff to crew when unsure. (Full design in chapter 41.) Highlights: microphone array and noise suppression; streaming ASR with endpointing and barge-in; menu grounding via a constrained catalog and entity resolution; an order state machine (deterministic) with an LLM for understanding and clarification; TTS with a short-utterance style; POS integration; confirmation step; escalation; evaluation with simulated and real audio; metrics: completion, accuracy, latency, interventions.

### The capacity numbers for 500 restaurants

Chapter 41 carries the operation schema, the latency table and the cost per order; in a design round add the fleet arithmetic. At the lunch peak assume one active lane per restaurant: 500 concurrent conversations, a model turn every 8 seconds each, so about 60 turns a second. With a 9,000-token input per turn (an 8,000-token menu prefix plus 1,000 tokens of order state and transcript) that is over half a million input tokens a second at peak — a Provisioned Throughput and quota conversation weeks before launch, and the strongest argument for a smaller prefix or a catalog tool. The same peak is 500 concurrent recognition streams (or Live sessions) and several thousand speech requests a minute, well above default per-project quotas such as Dialogflow CX's 600 audio requests a minute; request the increases as a tracked launch task.

## 40.5 Exercise D — Document extraction pipeline at scale

*Ask:* 300k invoices/month in 40 layouts, 12 fields, 99% accuracy on amounts, auditable.

*Design.* Ingest → layout/OCR model with field confidences → small fine-tuned/prompted extractor for the easy 90% → multimodal frontier model for low-confidence pages → business-rule validation (totals, VAT, vendor master) → human review queue for exceptions with bounding boxes → ERP posting via idempotent tool → monitoring of field-level accuracy and drift by layout. Batch API for backlog; cost per document by route. Deep dive: the confidence routing and the review UI. Metrics: field accuracy, straight-through rate, cost per document, exception aging.

### The routing threshold as an optimization, the QA sample size, and three follow-ups

**Choose the threshold by total cost, subject to the accuracy constraint.** Each page has a route: the parser alone, the parser plus a Gemini multimodal check, or a human. Total cost per document = model and parser cost + review probability × minutes per review × loaded cost per minute. On a labeled set, sweep the confidence threshold for amount fields and pick the cheapest point where measured amount accuracy on the automatic path stays at or above 99% with its interval; at Flash prices the model check is a fraction of a cent per page, so the human queue dominates the cost and the threshold is really a staffing decision. On Google Cloud: Document AI (the invoice parser or a custom extractor) for fields and confidences, Gemini on low-confidence pages, Cloud Run for the validation rules, a review UI over BigQuery, Batch inference for the backlog.

**How you prove 99% every month.** Sample the automatic path: to estimate 99% accuracy within ±0.5 points at 95% confidence you need about 1,521 documents a month (1.96² × 0.99 × 0.01 / 0.005²); 300,000 invoices a month makes that a half-percent sample. Weight errors by money: an error on a total above a threshold (for example 10,000) gets a second check before posting regardless of confidence.

**Three follow-ups.**
- *"A new vendor layout appears."* — Confidence drops, pages route to review, the reviewed pages become training or few-shot examples for that layout, and a per-layout accuracy chart shows when it can return to the automatic path.
- *"The ERP posting fails halfway."* — Idempotent posting keyed by invoice id and version, a dead-letter queue, and a reconciliation report that matches posted totals with extracted totals daily.
- *"Auditors want to know why an amount was accepted."* — The extracted value, its bounding box on the page image, the confidence, the validation rules it passed, and who or what approved it — stored with the posting.

## 40.6 Exercise E — Marketing content generation and compliance review

*Ask:* generate and review 5,000 assets/month across products and regions with zero regulatory escapes.

*Design.* Knowledge graph of products → rules → disclosures; RAG over guidelines and precedents; drafting agent; parallel reviewer agents (brand, legal, regulatory) with rubrics and citations; conflict detection and resolution planner; human approval; versioned prompts/rubrics; eval on historical assets (escapes, false flags); cost per asset with caching; audit trail. Deep dive: why a graph for rules and how reviewer findings are structured.

### What "zero escapes" can and cannot mean

"Zero regulatory escapes" is untestable as stated; translate it. Seed the evaluation set with assets that contain known violations: with zero escapes observed on 200 seeded violations, the 95% upper bound on the escape rate is about 1.5% (rule of three, 3/200); to claim under 0.5% you need about 600 seeded violations with none missed. Say this, then propose the gate: zero misses on the seeded set per release, a false-flag rate below the human reviewers' baseline, and human approval on every published asset — so the system lowers the human workload without being the last line of defence. 5,000 assets a month is about 250 a working day; with three reviewer agents in parallel the cycle time is bounded by the slowest reviewer plus the human approval queue, which is where the remaining days hide. The reviewer pattern and its ADK mapping are in 36.1 and 39b.3.

## 40.7 Exercise F — Agent platform for an enterprise (build once, reuse)

*Ask:* a platform team must let 30 product teams ship agents safely within six months.

*Design.* Paved road: an agent runtime (Amazon Bedrock AgentCore; Agent Runtime on the Gemini Enterprise Agent Platform, formerly Vertex AI Agent Engine; Foundry Agent Service in Microsoft Foundry, formerly Azure AI Foundry; or LangSmith Deployment, formerly LangGraph Platform), a gateway with identity, rate limits and cost attribution, an MCP tool registry with governance, a retrieval service with ACLs, an eval service (datasets, judges, CI integration), tracing with OTel GenAI conventions, guardrails as a shared service, templates (supervisor, RAG, workflow), and a review board for high-risk use cases. Deep dive: multi-tenancy and cost showback. Metrics: time to first production agent per team, incidents, cost per task, eval coverage.

### The paved road on Google Cloud, and four follow-ups

**The road, component by component.** A project per team under a shared folder; agents built with ADK from templates (Agent Garden for starting points, the platform team's own templates for the supervisor, RAG and workflow patterns) and deployed to Agent Runtime, each with its own Agent Identity; every tool and MCP server registered in Agent Registry and reached only through Agent Gateway, where IAM unified access policies say which agent may call which tool; Model Armor floor settings at the folder level so no team template can weaken them; VPC Service Controls around the data projects; Agent Evaluation and a shared gold-set service for CI gates; Agent Observability and Cloud Trace with the GenAI semantic conventions; cost showback from labels on runtime resources plus `gen_ai` token attributes joined to the billing export; a review board for high-risk use cases with a one-page intake form.

**Four follow-ups.**
- *"How do you stop a team from bypassing the gateway?"* — Egress restrictions and VPC Service Controls so agents cannot reach tools except through the gateway, an organization policy on which runtimes may be deployed, and a weekly report of agents without a registered identity — the paved road must also be the only road for production data.
- *"A model version is deprecated. How do 30 teams upgrade?"* — Versions pinned per agent; the platform runs each team's eval suite against the new version and publishes a per-team diff; teams with green results upgrade by configuration; a deprecation calendar with dates; nobody upgrades through an alias silently.
- *"How do you show cost per team?"* — Runtime labels and token attributes by team and agent, reconciled to the billing export within 5%, a monthly showback report, and per-agent budgets enforced at the gateway.
- *"What does the review board actually check?"* — The data the agent can reach, the actions it can take, the eval results for its riskiest slice, the human gate on irreversible actions, and the owner on call — five questions, thirty minutes, a decision recorded.

## 40.8 Common pitfalls

Jumping to the architecture before clarifying; drawing twelve boxes without a request path; no numbers; forgetting permissions and the human path; "we'll use GPT" as the design; ignoring cost; no evals; not asking the interviewer what they care about. An Applied AI interviewer marks down five more: no capacity arithmetic (tokens per second at peak and the quotas it implies); naming only old products, or only products, with no parameter attached; no rollout plan (shadow, canary, gates, kill switch); no owner for the first week ("I would instrument, baseline and set the gate"); and treating the model bill as the whole cost when search, speech, warehouse scans, runtime and the human review queue are often larger.

## 40.9 Two more exercises a Google Cloud Applied AI loop uses

### Exercise G — Customer-service agent for a retail bank (the guide's broad ask)

*Ask:* chat and voice for 2 million customers: balances and transactions, card freeze, transaction disputes, product questions; regulated; available around the clock.

*Clarify first:* channels and authentication strength per channel, which actions are allowed without a human, languages, complaint-handling obligations, and the cost ceiling per conversation.

*Design.* The customer authenticates in the bank's app (OIDC) and the token travels in the request context; voice callers step up through an app push before any account data is spoken. Deterministic paths (CX Agent Studio flow-based agents or Dialogflow CX flows) for authentication, card freeze (reversible, allowed after explicit confirmation) and dispute intake (creates a case in the bank's case system, which owns regulatory timelines); LLM agents for understanding and product questions grounded in an Agent Search data store of approved product documents; tools that resolve the customer from the token (`get_balance()`, `list_transactions(days ≤ 90)`), never from an argument. Guardrails: no financial advice, rates only from the rate tool, complaint detection that routes to a human with a reason code (complaints carry handling obligations), Model Armor on inputs and retrieved text, Sensitive Data Protection on logs and transcripts. Evals: 300 scripted scenarios plus social-engineering cases ("I'm calling for my mother", "my wife's card"), complaint-detection recall of at least 0.95, zero unauthorized disclosures on the negative suite. Scale: about 0.5 contacts per customer a month is 1 million conversations a month, about 33,000 a day. Deep dive: authorization and social engineering — the agent only ever sees the authenticated customer's data, so a successful manipulation can at worst act on the caller's own account, and the irreversible actions need a confirmation step the model cannot skip.

### Exercise H — A natural-language data agent over BigQuery (the system behind "I can't find the dataset")

*Ask:* 10,000 analysts ask questions over 3,000 BigQuery tables; answers must respect row- and column-level security; p95 under 10 seconds; no runaway query costs.

*Design.* Table discovery from Dataplex Universal Catalog metadata and embedded table and column descriptions; a planner (Gemini Pro, `low` thinking) chooses tables; SQL generated against a semantic layer or verified example queries; a BigQuery dry run (`dryRun`) returns the bytes the query would scan, and a cost guard sets `maximumBytesBilled` (for example 100 GB) on every job; the query runs as the analyst through on-behalf-of credentials so row access policies and policy tags apply; the answer shows the SQL and the rows it summarized. Tools return `found`, `not_found`, `forbidden` or `error` with reasons (chapter 39b.2). Evals: 200 questions with reference SQL, scored by comparing result sets (execution accuracy), plus forbidden-access negative tests.

*The number that surprises people:* at BigQuery on-demand pricing (about \$6.25 per TiB scanned at the time of writing), one 10 GB scan costs about six cents — more than the model tokens for the whole question. In a data agent the warehouse bill beats the token bill: partitioned and clustered tables, result caching, the bytes cap, and a dashboard of bytes scanned per question.
