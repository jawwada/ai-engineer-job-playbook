# Agentic AI Field Guide: FinOps, observability, design, evaluation and security on Google Cloud

A 74-page field guide, written for a Google forward-deployed Applied AI loop, that answers the five senior interview themes with definitions, the actual schemas, and code on Google Cloud: what a token costs and why agent loops are quadratically expensive; how to trace an agent and troubleshoot one that insists a dataset does not exist; agentic interaction patterns, design principles and latent reasoning in the Deep Agents SDK and ADK; how to build and improve an LLM-as-a-judge; and how to authorise an agent, limit it to certain data, and put enterprise guardrails and gateways in front of it. A2A and the agent SDKs are covered throughout. The guide exists in three forms: the interactive card page, the Markdown, and the PDF.

## Files

| File | What it is |
|---|---|
| `agentic-ai-field-guide.html` | The guide as an interactive single-file page: thirteen topic cards and three reference cards, each card with six tabs (Concepts with a diagram or chart, Example, Method, Pitfalls, Code, Say it in the room). Open it in any browser; no build step, no network needed beyond the Google Fonts link (the page falls back to system fonts without it). Also published as a hosted Claude artifact. |
| `Agentic AI Field Guide - FinOps, Observability, Design, Evaluation, and Security on Google Cloud.md` | The guide in Markdown, with the three figures linked from `images/` |
| `Agentic AI Field Guide - FinOps, Observability, Design, Evaluation, and Security on Google Cloud.pdf` | The same document as a 74-page US-letter PDF |
| `images/agent-loop-token-growth.png` | Chart: input tokens per turn and cumulative tokens as an agent loop grows |
| `images/dataset-not-found-troubleshooting-flow.png` | Flow: diagnosing the "dataset not found" case from traces to the fix |
| `images/guardrails-on-google-cloud.png` | Architecture: gateways, Model Armor, IAM, VPC Service Controls and data-level policies around an agent |

## The card page

| # | Card | What it covers |
|---|------|----------------|
| 1 | What a token costs, and why loops are quadratic | The eight components of a bill, the four counts in the usage object, a worked turn with and without caching; input per turn P + g·n, the loop total N·P + g·N(N+1)/2, the two-panel chart of per-turn and cumulative tokens (162,500 over ten turns), and the rule that falls out of it |
| 2 | Prompt caching | Prefix matching on the KV cache, implicit and explicit caching on Gemini and the other vendors, the stable-first prompt order, caching inside a loop (≈ 29,750 full-rate tokens instead of 162,500), the hit ratio, the explicit-cache break-even |
| 3 | Shorter loops, and where the money goes | Runtime budgets, thinking effort per step, plan once, compact tool results, prune at checkpoints, smaller outputs, routing, parallel calls, explicit finish; the three views, the detection recipe, carry cost (tokens introduced × turns after), a cost-by-step chart, the carry-cost script and the BigQuery cut |
| 4 | Traces, spans and the OpenTelemetry GenAI schema | Definitions; a contract-review turn as a waterfall; the `gen_ai.*` vocabulary and its two metrics; Langfuse's observations, sessions, scores, prompts and datasets on top; the attribute-name module |
| 5 | Instrumenting in code, and the Google Cloud native stack | Three layers; the loop and its tools as spans with usage and sizes; context propagation; redaction before export; Langfuse versus Cloud Trace need by need; Agent Runtime tracing by configuration (Agent Observability GA June 2026, telemetry env vars, `identity_type=AGENT_IDENTITY`); OTLP to the Telemetry API; the SDK 2.0 rename |
| 6 | The dataset that "does not exist" | Six checks read off the trace in order (tool called at all; 403 versus 404; arguments; empty or cut off; swallowed error; stale) and only then the prompt; the resolver tool, typed errors and the diagnosis function |
| 7 | Patterns of interaction, and A2A | Nine patterns with failure modes and cost profiles; workflow versus agent; composition as a graph; the supervisor rules; A2A v1.0 (Agent Card, Task states, Message, Artifact, bindings); `to_a2a` and `RemoteA2aAgent`; ADK workflow agents |
| 8 | Twelve principles for production agents | The principles as rules checked in review, the blast-radius ladder for side effects, where each principle is enforced, a worked design review, a tool registry with a gate derived from blast class, explicit state with checkpoints |
| 9 | Latent reasoning in Deep Agents and ADK | Thinking tokens, the plan and scratchpad, reflection; when each pays; the same portfolio-review agent built with Deep Agents middleware and with ADK planners, workflow agents and state; the three measures read from the trace |
| 10 | LLM-as-a-judge | Three purposes and deployments, the five-part anatomy and contract, judge types, criteria, scales, sync versus async; the calibration loop; embedding expert knowledge; judging conversations at two levels; the anti-pattern table; a groundedness judge, a position-swapped pairwise judge, the agreement report |
| 11 | Evaluation on Google Cloud | The Gen AI evaluation service (pointwise and pairwise model-based, computation, rubric-based, trajectory, batch, judge tooling), ADK evalsets and `adk eval`, the trace-to-case-to-gate loop, a worked run with two blocking failures |
| 12 | Authorisation: who the agent is, what it may touch | Three principals, acting as the agent versus on behalf of the user, the seven-layer BigQuery confinement recipe, the same recipe elsewhere, the read-only tool, row access policies, dataset-scoped grants, the cross-tenant test |
| 13 | Guardrails and gateways on Google Cloud | Four enforcement points inside one perimeter (Apigee or Agent Gateway, Model Armor, the runtime's rules, the data layer) and six shared controls; what to do by case; how Google handles it; floor settings, per-request templates, an Apigee policy sketch, the untrusted tool-result label |
| — | The script | The one-minute answers for the forward-deployed loop with proof points, the questions to ask them, a glossary, the likely follow-ups |
| — | Map, names and dates | The trace as the spine; the thirteen cards side by side; every product, price, setting, protocol version and model with the date checked; sources |
| — | Checklists and formulas | The cost and evaluation formulas with worked values, the recipes as checklists, the design-review questions, the go-live list |

## Contents of the Markdown and PDF

**Part 1 — FinOps: token economics.** 1. What a token costs (the components of a bill). 2. Why agent loops are quadratically expensive (the arithmetic). 3. How prompt caching works (Gemini implicit and explicit caching). 4. Shortening reasoning loops (thinking budgets, tool design, early exits). 5. Finding what consumes the most.

**Part 2 — Observability.** 6. Traces, spans and the OpenTelemetry generative-AI conventions. 7. Building observability in code (Langfuse SDK v3, OTel exporters). 8. Troubleshooting case: the dataset exists, the agent says it does not. 9. The Google Cloud alternative to Langfuse (Agent Engine tracing, Cloud Trace).

**Part 3 — Agentic design.** 10. Patterns of interaction. 11. Design principles for production agents. 12. Latent reasoning for agentic workflows in the Deep Agents SDK and ADK, with A2A.

**Part 4 — Quality and evaluation.** 13. LLM-as-a-judge: purpose, construction, criteria, scoring, sync and async. 14. Judge patterns and anti-patterns, embedding human knowledge, conversational AI. 15. Evaluation on Google Cloud (Vertex Gen AI evaluation, rubric-based and trajectory metrics, `adk eval`).

**Part 5 — Security and IAM.** 16. Authorisation for agents: who the agent is and what it may touch (BigQuery row- and column-level security, VPC-SC). 17. Enterprise guardrails and gateways on Google Cloud (Model Armor, Apigee policies).

**Part 6 — Interview readiness.** 18. Talking points for the Google forward-deployed loop. Appendix: glossary and sources.

## Conventions

- The card page uses the current product names with the former name in brackets on first use: Vertex AI became the Gemini Enterprise Agent Platform on 22 April 2026 (Agent Engine → Agent Runtime, Vertex AI Search → Agent Search, Vertex AI Studio → Agent Studio); the Markdown and PDF, written on 17 October 2026, use the older names in places.
- Prices, limits, model names and feature names are as published on 17–19 October 2026 and are listed with their dates on the Map card; the vendor pages are the source of truth. Code samples use gemini-2.5-pro and gemini-2.5-flash as in the guide; substitute the current GA model and re-run the golden set.
- Every number in a worked example is marked `illustrative` unless a document is named beside it. The proof points in the script are the author's own engagements (Capital Group, Noctal, Virtual Minds, the AgentCore supervisor); no personal rate appears anywhere.
- The two data charts (per-turn and cumulative tokens; cost by step name) use the validated two-colour palette shared with the other primers, one axis per panel, a legend where there is more than one series, and hover titles on marks.

## How it was built

The Markdown and PDF were written on 17 October 2026 as a Claude Doc from the Google Cloud documentation (Gemini pricing and caching, Agent Engine, Cloud Trace, ADK, Vertex evaluation, BigQuery security, Model Armor, Apigee), the OpenTelemetry generative-AI semantic conventions, the Langfuse documentation, the Deep Agents and A2A specifications, and the author's engagement history. The card page was built on 19–20 October 2026 from that guide, with the product names, release notes (Agent Observability, Agent Gateway, the Agent Platform SDK 2.0 migration, the deferred tier, Gemini 4 Argon's thinking levels) and the Agent Runtime quickstart re-checked against Google Cloud's documentation on 19 October 2026.
