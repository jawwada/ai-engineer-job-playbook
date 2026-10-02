# 42. Applied AI at prediction markets (Kalshi, Polymarket and peers): what the work is and how to interview for it

> **The idea:** prediction markets are exchanges for event contracts ("Will X happen by date Y?"). They have grown into mainstream venues for politics, economics, sports and culture, and they hire Applied AI engineers for a specific set of problems — market creation, resolution, integrity, support and internal operations — each a textbook agentic use case with unusual constraints (money, adversaries, regulation). This chapter explains the domain, the problems, and what interviewers will probe.

## 42.1 The domain in two paragraphs

A **prediction market** lists binary (or multi-outcome) contracts that pay out 1 unit if an event resolves YES and 0 otherwise; the price (0–100¢) is the market's probability. **Kalshi** is a US exchange regulated by the CFTC (a Designated Contract Market) with cash settlement and internal resolution rules; **Polymarket** grew as a crypto-native market on Polygon with USDC collateral and decentralized resolution through the UMA optimistic oracle, and has moved toward regulated US operation through a licensed exchange acquisition. Volume concentrates around elections, macro data releases, sports and news; liquidity comes from market makers and from traders using the markets as information and hedging tools. Peers and adjacent players include Metaculus and Manifold (forecasting communities), sportsbooks, and brokerages integrating event contracts.

The business runs on three loops: **supply** (creating many well-specified markets quickly), **integrity** (resolving them correctly and keeping manipulation, insider trading and fraud out), and **growth and operations** (support, compliance, finance, marketing at scale with small teams). AI touches all three.

### Critic's additions: the two platforms side by side, with dates (check before the interview; this domain changes monthly)

| | Kalshi | Polymarket |
|---|---|---|
| Regulatory status | CFTC-designated contract market since November 2020 | international venue on Polygon; acquired QCEX, a CFTC-licensed exchange and clearinghouse, for $112 million (July 2025); amended CFTC order of designation for intermediated US access (November 2025); US users again from December 2025 |
| Who decides the outcome | the exchange's markets team, from the source named in the rules; "a market settles when the official outcome is confirmed and our markets team finalizes the result", most within a few hours | UMA's optimistic oracle: a proposer posts a bond (typically $750); two-hour challenge window; a first dispute restarts proposals; a second goes to a token-holder vote of about 48 hours; clarifications are published on-chain via a bulletin-board contract |
| Where disputes come from | wording, source delays and revisions, determination times later than the event | wording, proposer and voter incentives, clarifications added mid-market |
| Live regulatory questions | US states challenging sports event contracts, with litigation and mixed rulings through 2026 | the same state questions for the US product, plus country-level restrictions on the international one |
| What an AI system may touch | drafting, evidence packages, surveillance narratives, support — never the determination itself | drafting, clarifications, proposal monitoring, dispute evidence — never the oracle |

Two public episodes worth knowing because they make the wording argument for you: Polymarket's 2025 market on whether Zelensky would wear a suit, decided by a vote about what counts as a suit; and Kalshi's published enforcement actions against insiders in 2026, including candidates trading on their own races. Mention them as illustrations of the risk, not as opinions about either company.

## 42.2 The Applied AI problem set

1. **Market generation and specification.** Turn news, schedules and data releases into candidate markets with unambiguous resolution criteria (source, time zone, edge cases), check for duplicates and overlapping markets, estimate initial probability and liquidity needs, and route to human review. Architecture: news/event ingestion → LLM drafting with templates per category → rule checks (resolution-source allow-list, date validity) → duplicate detection with embeddings → analyst approval. Metrics: markets launched per analyst-hour, post-launch disputes, edits before approval.
2. **Resolution assistance.** Gather evidence from the designated sources, extract the outcome, assess ambiguity, and prepare a resolution package for humans (or the oracle). Hard parts: source reliability, contradictory reports, time-zone and wording traps, adversarial pressure (traders will argue). Architecture: retrieval over allow-listed sources with citations, claim-level verification, confidence scoring, escalation rules; everything auditable. Metrics: resolution latency, dispute rate, reversal rate.
3. **Market integrity and risk.** Detect manipulation (wash trading, spoofing), insider trading around resolution sources, coordinated accounts, and bot abuse; monitor unusual price moves against news; triage alerts for analysts. Architecture: streaming features over trades and accounts, anomaly detection and graph analysis of account relationships, LLM-generated alert narratives with evidence, case management. Metrics: precision of alerts, time to detect, analyst load.
4. **Compliance and KYC/AML automation.** Document checks, sanctions screening, suspicious-activity narratives, regulatory reporting drafts — with humans signing off. Architecture: document AI + rules + LLM drafting with strict templates; full audit trail.
5. **Customer support and user-facing assistants.** Explain market rules and resolutions, handle account and payment questions, translate; strict grounding in official rules; escalation. Metrics: containment, CSAT, resolution-explanation accuracy.
6. **Internal operations automation (the "AI Ops" role).** The published Polymarket AI Ops Specialist posting (2026) describes exactly this: identify inefficiencies across ops, finance, talent, customer experience, engineering and marketing; design and deploy agents, copilots and automations with LLMs and APIs; production code in Python and TypeScript integrated with Notion, Linear, Slack and GitHub; shared infrastructure — prompt libraries, evaluation frameworks, RAG pipelines; company-wide standards for AI. Expectations: 5+ years of software engineering, expertise in LLMs, agents, tool use, evaluation and RAG, full-stack ability (API, UI, pipeline, infrastructure). That is an FDE job pointed inward.
7. **Forecasting and research.** Models that forecast event probabilities from news and data (as benchmarks against the market and as inputs to market making), sentiment and news-impact models, and trader tools (summaries of what moved a market). Caution: anything that touches trading is heavily gated; research agents get read-only tools (chapter 30).
8. **Content and growth.** Automated market summaries, explainers and multilingual content, with brand and compliance review (see the marketing-review use case in chapter 36).

### Critic's additions: each problem with a metric, a threshold, a Google Cloud build and the human gate

The thresholds below are illustrative starting points to propose and then agree with the customer; the point is that every agent ships with a number and a named human decision.

| Problem | Metric and starting threshold | Build on Google Cloud (2026 names) | Human gate |
|---|---|---|---|
| Market generation | markets per analyst-hour at least 3× the manual baseline; post-launch clarification rate under 2%; dispute rate not above baseline | news and calendar feeds on Pub/Sub, Dataflow normalization, Gemini Flash drafting with a `response_schema` per category template, an ambiguity lint (named source, time zone, determination time, tie, postponement and cancellation clauses, no relative dates), duplicate detection with embeddings in Vector Search (cosine at least 0.90 plus the same entity and date window) | an analyst approves every listing |
| Resolution assistance | share of markets auto-proposed at 99.5% or better precision on the backtest; source publication to package in under 10 minutes; zero reversals caused by a package | an ADK resolver on Agent Runtime with read-only tools for the designated sources, Gemini Pro with `high` thinking only on evidence reconciliation, a judge on a different model, packages and decisions in BigQuery | the markets team (or the operator's oracle process) decides; the agent proposes |
| Integrity and surveillance | alert precision at the analysts' budget (for example at least 30% actionable at 50 alerts per analyst per day); time to detect pre-resolution trading under one hour | trades on Pub/Sub, features in Dataflow and BigQuery, an account-relationship graph (Spanner Graph or BigQuery), anomaly models, a Gemini-written narrative citing the evidence rows, case management | analysts decide; automated actions limited to rule-based holds |
| Compliance and KYC/AML | time to a draft suspicious-activity narrative; screening false-positive rate | Document AI for identity documents, a rules engine for sanctions screening, Gemini drafting into fixed templates, Sensitive Data Protection on everything stored | a compliance officer signs every filing |
| Support | containment; faithfulness of rule explanations at least 0.95 against the official rules; escalation accuracy | CX Agent Studio or Dialogflow CX with a data-store tool over the rulebook and each market's rules; no account-changing tools | handoff for accounts, payments and disputes |
| Internal operations ("AI Ops") | hours saved per process against a measured baseline | ADK agents with MCP connectors to the team's tools, an Agent Identity per agent, Agent Gateway policies, one shared eval harness | approval on every write |
| Forecasting and research | Brier score against the market's own price as the benchmark; calibration by probability bucket | read-only research agents over BigQuery and news | no path to order placement |
| Content and growth | brand and compliance pass rate; time to publish | the chapter 36 review workflow | human approval before publication |

## 42.3 Constraints that make this domain different

- **Money and adversaries.** Every mistake has a price and someone looking to exploit it; evaluations must include adversarial cases; approvals and audit trails are not optional.
- **Regulation.** CFTC rules for a US exchange; AML/KYC; recordkeeping; model governance expectations; some jurisdictions restrict access entirely.
- **Latency and freshness.** Markets move on news in seconds; resolution sources update on their own schedules; stale retrieval is a correctness bug.
- **Ambiguity is the product risk.** Market wording decides outcomes; LLM assistance must *reduce* ambiguity (templates, checklists, examples of past disputes), never introduce it.
- **Small teams, broad surface.** The AI Ops framing — one engineer serving many functions — rewards generalists who can ship full-stack and measure.

### Critic's additions: each constraint turned into a design requirement with a number

| Constraint | Design requirement |
|---|---|
| Money and adversaries | at least 10% adversarial cases in every eval set (manipulative wording, forged screenshots of sources, injected instructions in fetched pages); a two-person rule for any change to a published market or a determination |
| Regulation and recordkeeping | an exchange's required records are generally kept for at least five years under CFTC Regulation 1.31, so treat any agent output that informed a determination or a surveillance case as a record: store its inputs, sources with timestamps, model and prompt versions, and the human decision; keep a model inventory with owners and change control |
| Freshness | explicit SLOs: news to draft market in under 5 minutes; designated-source publication to resolution package in under 10 minutes; per-source cache TTLs, and a test that fails when the resolver reads a cached page older than the determination time |
| Ambiguity | the template-plus-lint approach above, the past disputes as few-shot counter-examples, and the clarification rate as the metric that tells you whether drafting improved |
| Jurisdiction | geofencing and per-jurisdiction product availability enforced in the product layer and tested, because the state of the law differs by state and by country and changes during the year |
| Small teams | one paved road: one agent template, one identity pattern, one eval harness, one cost dashboard — otherwise each automation becomes its own maintenance burden |

## 42.4 How to interview for it

- **Lead with integrity and evaluation.** For any agent you propose, say how you would evaluate it adversarially and where the human approval sits.
- **Show domain fluency.** Know how resolution works on each platform (Kalshi's internal rules and resolution sources; Polymarket's UMA optimistic oracle and dispute process), what a market spec looks like, and why wording disputes happen.
- **Bring a demo.** A small repo that ingests a news feed, drafts market specs with resolution criteria, flags duplicates with embeddings, and produces a resolution package with citations for a past event — with an eval set of 30 real markets and a dispute-rate proxy. Chapter 34's lab format.
- **Expect these questions.** "How would you automate resolution without being wrong?" (allow-listed sources, claim verification, confidence thresholds, humans on anything below threshold, audit); "How would you detect insider trading around a resolution source?" (features: timing relative to source updates, account history, P&L concentration; graph of related accounts; alert triage with narratives); "How do you keep an internal copilot from leaking data between teams?" (chapter 30: identity, scoped tools, ACL retrieval); "What would you automate first in operations?" (map processes by volume × pain × data availability; start with support macros and finance reconciliations; measure hours saved).
- **Rates and expectations.** Roles are often on-site in New York (both companies) or remote-friendly for contractors; emphasize shipping speed, ownership and measurement.

### Critic's additions: six more questions with specific answers, the demo's acceptance numbers, and what not to say

Chapter 39c.3 has the resolution, insider-trading, leakage and build questions in interview form; these are the next six.

- *"Walk me through your demo in two minutes."* — Thirty historical markets: the drafter rewrites each from its headline and the lint scores the result; the duplicate detector runs over all thirty plus fifty near-duplicates I seeded; the resolver builds a package for each and I compare it to the actual outcome. Report: lint pass rate, duplicate precision and recall, package agreement with the real outcome, minutes per package, and cost per market. Say what failed and why.
- *"What is a Brier score, and why use it here?"* — The mean squared difference between a probability forecast and the 0/1 outcome (0 is perfect; always saying 50% scores 0.25). It lets you compare a forecasting agent with the market's own price on the same events; pair it with a calibration plot by probability bucket.
- *"Should the drafter create markets on sensitive events — deaths, violence?"* — That is a listing policy the company owns, not a model judgement; the drafter applies the written policy with a classifier and routes anything near the line to a human, and the eval set contains the cases the policy forbids.
- *"A trader says your assistant caused a wrong resolution."* — The audit trail answers it: the package with sources and timestamps, the reviewer's decision, and what the reviewer saw. The human decision is the record; if the package was wrong, the fix is in the template or the source tool, and the case joins the eval set.
- *"Thousands of markets — how do you keep the AI bill small?"* — Flash for drafting, Batch or Flex for nightly duplicate scans and backfills, a cache of fetched source pages with TTLs, thinking only on reconciliation, and cost per listed market and per resolution on the dashboard.
- *"Which metric would you report to the regulator-facing team?"* — For each automated step: precision on the automatic path with its confidence bound, the human-review share, reversal count, and evidence completeness (share of packages with source, timestamp and reviewer) — numbers a compliance officer can sign.

**What not to say.** Anything about trading strategies, "beating" the market or influencing the oracle; opinions on the state litigation; or a design in which a model decides an outcome without a named human or process owning the determination.

**Interview line:** *"At a prediction market the agent's job is to make humans faster and more consistent on market creation, resolution, integrity and operations — with allow-listed sources, adversarial evals, approvals on anything that moves money or resolves a market, and an audit trail a regulator can read."*
