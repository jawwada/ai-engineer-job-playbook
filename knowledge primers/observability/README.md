# Observability — knowledge primer

An interactive, single-file primer on observability for distributed and AI systems, written for interview preparation (observability and platform engineering roles, Google FDE / Applied AI, SRE-flavoured loops) and for consultative conversations with clients. Open `observability.html` in any browser; no build step, no network needed beyond the Google Fonts link (the page falls back to system fonts without it).

## What is on the page

Ten topic cards, each with six tabs — **Concepts** (with a diagram or a data chart), **Example** (worked numbers), **Method**, **Pitfalls**, **Code** (OpenTelemetry Python, Collector YAML, PromQL, SQL), **Say it in the room** — plus three reference cards.

| # | Card | What it covers |
|---|------|----------------|
| 1 | Observability as a discipline | Monitoring vs observability; the signals; golden signals, RED and USE with LLM-gateway examples; where to measure; a quarter of a program in numbers; the maturity model; the six questions to ask of any component; the strategy one-pager; program metrics; a 30-60-90-day plan; the OpenAI (Dec 2024) and Datadog (Mar 2023) incidents |
| 2 | The OpenTelemetry data model | The OTLP envelope (resource, scope, records); span fields, kinds and status rules; instruments to Prometheus types; temporality and exemplars; context propagation (traceparent, tracestate, baggage); resource attributes; semantic conventions by domain with stability; schema URLs and migrations; SDK setup, a manual span, a View, propagation through a queue |
| 3 | Instrumenting LLM and agent systems | The GenAI conventions name by name (operations, span names and kinds, usage attributes and subset rules, events, metrics, MCP); a fourteen-span agent run as a waterfall; what to capture by layer; the run costed and timed with four optimisations; the six checks for "the dataset exists, the agent says it does not"; configuration for ADK on Agent Runtime; the usage conversion; an evaluation event |
| 4 | The pipeline: Collector, sampling, cardinality | Agent and gateway tiers; the components to get right; five kinds of sampling with adjusted counts; the failure modes of the telemetry pipeline; cardinality arithmetic (408,000 series); sizing tail sampling; the semantic-convention migration; a gateway configuration that derives RED and cost metrics before sampling |
| 5 | Metrics, Prometheus and PromQL | Why averages lie (a chart); PromQL essentials; Prometheus at scale (storage, memory, relabeling, remote write, HA, long-term stores, Prometheus 3 changes); twelve worked queries; the thirteen PromQL mistakes; rules, a watchdog, relabeling for the budget |
| 6 | SLIs, SLOs, error budgets and alerting | How fast a budget burns (a chart); budgets in minutes; SLI types; multiwindow burn-rate thresholds; the checkout example with detection times; composite availability; canary statistics; an error-budget policy; the hand-written SLO rule set and a Sloth spec; the SLA checklist and red flags |
| 7 | Latency, tail and capacity | Fan-out and queueing (two charts); percentiles and sample sizes; model-call latency (TTFT, TPOT, duration); mitigations (timeouts, hedging, deadlines); the 16.5-second run broken down; a per-hop latency budget; Little's law in dollars; a hedge that respects the deadline |
| 8 | Cost as a signal | What sampling does to a cost number (a chart); cost per span by span type; where to compute it; roll-up rules; the cost of observability and its levers; one call, one run and three bills for watching it; the six things that make the formula wrong; cost in the application, the Collector and the warehouse |
| 9 | Quality signals and AI for observability | A trustworthy investigation agent (diagram); quality signals as telemetry and the quality SLO; why classic AIOps disappointed; the 2026 products; natural language to PromQL failure modes; evaluating an AI SRE on replayed incidents; time-series foundation models; a read-only MCP server, validated queries, a scorecard |
| 10 | Google Cloud and the tool landscape | The Google Cloud map for an agent; the Agent Observability tab; three stacks (Google Cloud, Grafana LGTM, LLM-native) side by side; choosing; setup for ADK on Agent Runtime and self-hosted; pitfalls; deployment, export and SQL |
| — | The script | The thirty-second and two two-minute answers, a thirty-term glossary, the billing-support run from start to finish, twenty-two likely questions with answer shapes |
| — | Query & pipeline cookbook | Twelve PromQL shapes; LogQL, TraceQL and warehouse SQL; Collector OTTL recipes (name normalisation, redaction, baggage, noise, routing, schema); which tool answers which question |
| — | Formulas & names | Reliability math, latency and capacity, telemetry economics, the names with stability and Prometheus forms, the versions the page was written against |

## Conventions

- OpenTelemetry facts follow specification 1.61, OTLP 1.11, semantic conventions 1.44 and the `semantic-conventions-genai` repository as checked in early October 2026 (every GenAI name is development-status; there is no release or schema URL to pin). Collector configurations use the 2026 snake_case component names and were written against contrib v0.161.
- Prometheus queries assume 3.14 with the default OTLP translation strategy; Grafana stack versions are those current in October 2026.
- Google Cloud names follow the 2026 naming (Gemini Enterprise Agent Platform, Agent Runtime, Agent Observability) and the release notes for statuses and dates (GA and preview); statuses drift, so verify before quoting them to a client.
- The worked agent run (fourteen spans, $0.0453, 16.5 s) and every price on the page are illustrative, at the list prices the book recorded on 2 October 2026; the page never quotes a personal rate.
- Code samples are plain Python with the OpenTelemetry SDK and Google Cloud client libraries; verify module paths and parameter names against current docs before running.
- The page is a hosted Claude artifact as well; this file is the standalone copy for the repository.
