# Agentic AI Field Guide: FinOps, observability, design, evaluation and security on Google Cloud

A 74-page field guide, written for a Google forward-deployed Applied AI loop, that answers the five senior interview themes with definitions, the actual schemas, and code on Google Cloud: what a token costs and why agent loops are quadratically expensive; how to trace an agent and troubleshoot one that insists a dataset does not exist; agentic interaction patterns, design principles and latent reasoning in the Deep Agents SDK and ADK; how to build and improve an LLM-as-a-judge; and how to authorise an agent, limit it to certain data, and put enterprise guardrails and gateways in front of it. A2A and the agent SDKs are covered throughout.

## Files

| File | What it is |
|---|---|
| `Agentic AI Field Guide - FinOps, Observability, Design, Evaluation, and Security on Google Cloud.md` | The guide in Markdown, with the three figures linked from `images/` |
| `Agentic AI Field Guide - FinOps, Observability, Design, Evaluation, and Security on Google Cloud.pdf` | The same document as a 74-page US-letter PDF |
| `images/agent-loop-token-growth.png` | Chart: input tokens per turn and cumulative tokens as an agent loop grows |
| `images/dataset-not-found-troubleshooting-flow.png` | Flow: diagnosing the "dataset not found" case from traces to the fix |
| `images/guardrails-on-google-cloud.png` | Architecture: gateways, Model Armor, IAM, VPC Service Controls and data-level policies around an agent |

## Contents

**Part 1 — FinOps: token economics.** 1. What a token costs (the components of a bill). 2. Why agent loops are quadratically expensive (the arithmetic). 3. How prompt caching works (Gemini implicit and explicit caching). 4. Shortening reasoning loops (thinking budgets, tool design, early exits). 5. Finding what consumes the most.

**Part 2 — Observability.** 6. Traces, spans and the OpenTelemetry generative-AI conventions. 7. Building observability in code (Langfuse SDK v3, OTel exporters). 8. Troubleshooting case: the dataset exists, the agent says it does not. 9. The Google Cloud alternative to Langfuse (Agent Engine tracing, Cloud Trace).

**Part 3 — Agentic design.** 10. Patterns of interaction. 11. Design principles for production agents. 12. Latent reasoning for agentic workflows in the Deep Agents SDK and ADK, with A2A.

**Part 4 — Quality and evaluation.** 13. LLM-as-a-judge: purpose, construction, criteria, scoring, sync and async. 14. Judge patterns and anti-patterns, embedding human knowledge, conversational AI. 15. Evaluation on Google Cloud (Vertex Gen AI evaluation, rubric-based and trajectory metrics, `adk eval`).

**Part 5 — Security and IAM.** 16. Authorisation for agents: who the agent is and what it may touch (BigQuery row- and column-level security, VPC-SC). 17. Enterprise guardrails and gateways on Google Cloud (Model Armor, Apigee policies).

**Part 6 — Interview readiness.** 18. Talking points for the Google forward-deployed loop. Appendix: glossary and sources.

## How it was built

Written on 17 October 2026 as a Claude Doc from the Google Cloud documentation (Gemini pricing and caching, Agent Engine, Cloud Trace, ADK, Vertex evaluation, BigQuery security, Model Armor, Apigee), the OpenTelemetry generative-AI semantic conventions, the Langfuse documentation, the Deep Agents and A2A specifications, and the author's engagement history. Prices, model names and preview features change; the appendix lists the pages consulted with the as-of date and marks the facts that were still in development.
