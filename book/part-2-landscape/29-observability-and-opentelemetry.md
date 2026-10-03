# 29. Observability and OpenTelemetry for LLM systems

> **What you need to be able to say:** the three (now four) signals; what OpenTelemetry is and how the SDK, the Collector and OTLP fit; the GenAI semantic conventions (span names, attributes, metrics) and their status; what to trace in an agent; which tools you would use; and how you troubleshoot "the agent says it cannot find the dataset" (worked in chapter 39). Go deeper: Part 6 → *AI/backend engineer deep dive* §8 and the *Python and backend guide*. Chapter 29b is the reference companion (definitions, the OpenTelemetry data model and OTLP schema, latency, and cost per span and per trace); chapters 45a–45c cover observability engineering as a role, the open-source stack (OpenTelemetry, Prometheus and PromQL, Grafana, Loki, Tempo, Mimir), and AI for observability with how to build and ship AI skills.

## 29.1 Observability in one paragraph

Observability is the ability to answer questions about a running system from the data it emits without shipping new code. The classic signals are **logs** (events with context), **metrics** (numeric time series: counts, latencies, saturation), and **traces** (a tree of timed spans showing one request's path across services); **profiles** are the fourth. For LLM systems the trace is the primary signal, because one user request becomes a tree of model calls, tool calls and retrievals, each with tokens, cost, latency and a result that may be wrong without erroring.

## 29.2 OpenTelemetry (OTel)

OpenTelemetry is the vendor-neutral standard (CNCF) for producing telemetry: **APIs and SDKs** per language instrument your code (auto-instrumentation for HTTP, DB clients, frameworks; manual spans for your logic); the **OTLP** protocol (gRPC or HTTP/protobuf) carries data; the **Collector** is a pipeline process that receives (OTLP, Prometheus, Jaeger…), processes (batching, sampling, attribute transforms, redaction, tail sampling) and exports (to Datadog, Grafana Tempo/Loki/Mimir, Honeycomb, New Relic, CloudWatch, Azure Monitor, Google Cloud Trace, Langfuse, Dash0, Elastic…). **Context propagation** (W3C `traceparent` header) ties spans across services; **resources** describe the emitting service; **semantic conventions** standardize attribute names so backends can build generic dashboards.

Why it matters for you: instrument once with OTel and you can switch backends; every cloud agent runtime (AgentCore, Google's Agent Runtime — formerly Agent Engine — and Foundry) and every serious LLM-observability tool speaks OTLP; and interviewers use "OpenTelemetry" as a shibboleth for "has run something in production".

**Sampling, the mechanism people get wrong.** *Head sampling* decides at the root span (keep 10% of traces) — cheap, but it throws away the rare failures you most need. *Tail sampling* buffers all spans of a trace in the Collector and decides after the trace completes, so you can keep 100% of traces with errors, guardrail blocks, latency above p95, cost above a threshold or a low judge score, plus a small random baseline. Tail sampling only works if every span of a trace reaches the same Collector instance: run a first tier of Collectors with the load-balancing exporter keyed on trace ID in front of the tail-sampling tier, and size the buffer for your longest agent run (a 20-minute agent trace must be held for 20 minutes, or decided in pieces). Context propagation must also cross your tool boundary: the MCP 2026-07-28 revision documents carrying `traceparent`/`tracestate` in the request `_meta`, so a remote MCP server's spans join the agent's trace instead of starting a new one.

## 29.3 The GenAI semantic conventions (status: Development, October 2026)

The `gen_ai.*` conventions define how to name and attribute LLM spans and metrics. They are still at *Development* stability (breaking changes allowed), moved on 12 June 2026 (with semantic-conventions v1.42.0) into their own `semantic-conventions-genai` repository, and ship from `main` without a tagged release or schema URL as of mid-2026; pin the version your instrumentation library emits and normalize at the Collector if you mix libraries.

- **Span names**: `{operation} {model}` for inference, with the model id as sent to the API (`chat claude-sonnet-5-5`, not a marketing name such as "Claude Sonnet 5.5"), `{operation} {agent}` for agents (`invoke_agent support-triage`), `execute_tool {tool}`.
- **Required attributes** on inference spans: `gen_ai.operation.name` (chat, generate_content, text_completion, embeddings, create_agent, invoke_agent, invoke_workflow, plan, execute_tool, retrieval, create_memory/search_memory/upsert_memory) and `gen_ai.provider.name` (openai, anthropic, aws.bedrock, gcp.vertex_ai, azure.ai.inference…).
- **Conditionally required/recommended**: `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.conversation.id`, `error.type`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.cache_read.input_tokens`, `gen_ai.usage.cache_write.input_tokens`, `gen_ai.usage.reasoning.output_tokens`, request parameters (temperature, max_tokens), `gen_ai.agent.name/id/version`, `gen_ai.tool.name`, `gen_ai.tool.call.id`, `gen_ai.tool.type`, `gen_ai.data_source.id`, `gen_ai.retrieval.top_k`, `gen_ai.memory.*`.
- **Content** (prompts and completions) is opt-in and goes into an event (`gen_ai.client.inference.operation.details` with `gen_ai.input.messages` / `gen_ai.output.messages`), not span attributes — for privacy and size.
- **Metrics**: `gen_ai.client.token.usage` (histogram by token type, model, operation), `gen_ai.client.operation.duration`, `gen_ai.client.operation.time_to_first_chunk` and `time_per_output_chunk` (streaming, added in 2026), `gen_ai.invoke_agent.duration`, `gen_ai.invoke_agent.tool_calls`, `gen_ai.invoke_agent.inference_calls`, `gen_ai.execute_tool.duration`, `gen_ai.invoke_workflow.duration`; server-side `gen_ai.server.request.duration`, `gen_ai.server.time_to_first_token` and `gen_ai.server.time_per_output_token` for people serving models.
- **Trace shape for an agent turn**: root `invoke_agent` → children `chat` (model calls), `execute_tool`, `retrieval`, nested `invoke_agent` for sub-agents — exactly like a checkout flow calling three microservices.
- **Renames that break old dashboards**: `gen_ai.system` became `gen_ai.provider.name`; `gen_ai.usage.prompt_tokens`/`completion_tokens` became `input_tokens`/`output_tokens`; `gen_ai.usage.cache_creation.input_tokens`, the name in semantic-convention releases up to v1.41.0, became `gen_ai.usage.cache_write.input_tokens`; the `gen_ai.prompt`/`gen_ai.completion` attributes were removed in favour of the opt-in content event. Libraries pinned to older convention versions still emit the old names, which is the most common reason two teams' GenAI dashboards disagree — normalize in the Collector with a transform processor.
- **What the conventions do not define**: cost. There is no standard cost attribute; compute it from token counts and a versioned price table (including cache-write and cache-read rates, batch discounts and long-context tiers) either in the Collector or in the backend, and record the price-table version so historical cost does not silently change when prices do.

Instrumentation libraries that emit these: OpenLLMetry (Traceloop), OpenInference (Arize), Langfuse and LangSmith SDKs (with OTel export), MLflow Tracing, Strands and ADK built-ins, the Claude Agent SDK/Claude Code OTel export, vendor SDK instrumentations in `opentelemetry-python-contrib`, and the OpenTelemetry Demo's agent service.

## 29.4 What to capture for an LLM system

| Layer | Capture | Why |
|---|---|---|
| Request | user/tenant id (hashed), conversation id, feature flag, model route, prompt version | slicing quality and cost by segment |
| Model call | model, parameters, input/output/cached/reasoning tokens, latency, time-to-first-token, finish reason, cost (computed) | FinOps, latency SLOs |
| Retrieval | query (hashed or opt-in), index, top_k, returned ids and scores, filters, latency | diagnosing "it never retrieved the right doc" |
| Tools | name, arguments schema (redacted values), result size, latency, errors, side-effect flag, approval status | safety and debugging |
| Agent run | turns, tool-call count, budget consumption, stop reason, sub-agent tree | runaway detection |
| Quality | judge scores (sampled), user feedback, grounding-check result, guardrail hits | evaluation in production |
| Content | prompts and outputs, opt-in, redacted, retained per policy | reproducing failures |

Logs carry structured events (JSON with trace ids); metrics feed SLO dashboards (p95 latency, error rate, cost per request, token usage, guardrail block rate, escalation rate); traces are for debugging and for building eval datasets from real runs.

### Critic's additions: volume, cardinality and privacy

LLM telemetry is heavier than web telemetry, and the bill and the privacy review arrive together:

- **Volume.** A single agent run can carry 50–500k tokens of prompt and tool content. At 100,000 requests a day with an average 20 KB of captured content, that is ~2 GB a day before indexing — and several times more for agents. Capture content for a sampled subset (errors, low judge scores, a small random slice) and keep span attributes for everything.
- **Cardinality.** Metric labels multiply time series: model × route × prompt version × tenant is fine; user id, conversation id or raw tool arguments as metric labels will break Prometheus-style backends. Put high-cardinality identifiers on spans and logs, not on metrics.
- **Redaction where it is cheapest.** Redact PII and secrets in the Collector (redaction or transform processors with patterns, or a PII service) before export, so no backend ever stores raw content; hash user identifiers; keep a short retention for content and a longer one for metrics.
- **Access control.** Traces with content are as sensitive as the underlying data; restrict who can view content-bearing spans, and log access to them.
- **SLOs that matter for LLM features.** Availability and p95 latency (including time to first token for streaming UIs), cost per successful task, and a quality SLO (judge pass rate on sampled traffic) with an error budget — breaching the quality SLO should freeze prompt and model changes the same way an availability breach freezes deploys.

## 29.5 Tools

- **LLM-specific**: LangSmith (LangChain-native, evals), Langfuse (open source, self-host, prompts + evals + OTLP), Arize Phoenix/AX (open source tracing + evals, OpenInference), Braintrust (evals + logs), W&B Weave, Helicone (proxy-based), Traceloop, MLflow Tracing (Databricks), Datadog LLM Observability, New Relic AI Monitoring, Dash0, Honeycomb, Dynatrace; cloud-native: AgentCore Observability (CloudWatch, with a unified span destination for agents and cross-account monitoring), Agent Runtime tracing in Cloud Trace and Agent Observability in the Gemini Enterprise Agent Platform (formerly Vertex AI), Azure Monitor/Application Insights with Foundry tracing and the Foundry Control Plane. A useful distinction: proxy-based tools (Helicone, gateways) see every model call with zero code but nothing inside your agent; SDK/OTel instrumentation sees the whole tree (tools, retrieval, sub-agents) but must be added to code — production systems usually want the second, often with the first as a safety net.
- **General**: Prometheus + Grafana (metrics), Grafana Tempo/Jaeger (traces), Loki/Elastic (logs), Datadog/New Relic/Splunk (suites), Sentry (errors).
- **Model monitoring (classic ML)**: drift (input/feature/prediction), performance decay, data quality (Evidently, Arize, WhyLabs, SageMaker Model Monitor, model monitoring on Google's Agent Platform, Databricks Lakehouse Monitoring).

## 29.6 Troubleshooting method (the interview version)

When an agent misbehaves — "I cannot find the dataset" — do not read the prompt first; read the trace: (1) find the run by conversation id; (2) look at the `execute_tool` spans — was the tool called at all, with what arguments, what did it return (empty list? permission error? wrong catalog?); (3) check the `retrieval` span — index name, filters, top_k, scores; (4) check the model span — was the tool schema present, was the context truncated, did the model hallucinate a tool name; (5) check identity — which principal executed the tool and what it was allowed to see; (6) reproduce with the captured inputs in a test; (7) fix the layer that failed (tool description, permissions, index, context budget) and add the case to the eval set. Chapter 39 walks the full answer.

## 29.7 Scenarios

- **Marketing automation agents (resume use case).** Langfuse/LangSmith traces per asset with model route, reviewer-agent verdicts and token cost; Grafana dashboards on p95 and cost per asset; judge sampling nightly; alerts on guardrail blocks and on cost per run above a threshold.
- **Ranking service at 10K QPS (resume use case).** Classic observability: Prometheus metrics (latency histograms, QPS, error rate, model version), feature drift monitors, A/B harness metrics with statistical gates, canary rollout and automated rollback — plus traces sampled at 0.1%.
- **Multi-cloud agent platform.** OTel SDKs in every service → Collector with redaction and tail sampling → one backend; GenAI conventions normalized via Collector transform processors; cost computed from token attributes with a price table.

**Interview line:** *"Everything emits OpenTelemetry with the GenAI conventions: an `invoke_agent` root span with model, tool and retrieval children carrying tokens, latency and results; content opt-in and redacted; metrics for p95, cost and guardrail rate; judge scores sampled in production. When something breaks, I read the trace before the prompt."*
