# 29b. Observability reference: definitions, the OpenTelemetry data model and schema, and the parameters that matter (latency, cost per span, cost per trace)

> **What you need to be able to say:** a precise definition, with an example, of every term an observability interview uses (signals, instrument kinds, cardinality, exemplars, temporality, the single-writer principle, span kind and status, events and links, context, baggage, resources and scopes, the five kinds of sampling, percentiles, SLO terms, MTTx, golden signals, RED, USE, Apdex, RUM, profiling, eBPF, OTLP, the Collector, semantic conventions and schema URLs); the OTLP envelope for traces, metrics, logs and profiles down to field numbers, and the rules for each Span field; how OTLP metric points become Prometheus series under each translation strategy; which semantic conventions are stable, release candidate or still in development, with the exact GenAI attribute and metric names; how schema files describe renames; the latency arithmetic (percentiles, fan-out, latency budgets, queueing, Little's law, time to first token, time per output token); how to compute cost per span and cost per trace from span attributes and a versioned price table, in the application, the Collector or the warehouse, without letting sampling distort the numbers; what observability itself costs; and a fully costed and timed agent trace with the TraceQL and SQL to reproduce it. Chapter 29 covers how to use the GenAI conventions in an LLM system, chapter 31 token prices and cost levers, chapter 45a SLOs and the telemetry pipeline at scale, chapter 45b the Collector, Prometheus, PromQL and Tempo, and chapter 47 FinOps.

## 29b.1 What this chapter was checked against, and how to read stability

Observability standards move every month. Everything below was checked on 2 October 2026 against these versions; when you quote a name in an interview or a design document, quote the version with it.

| Component | Version checked | What to know |
|---|---|---|
| OpenTelemetry specification | 1.61.0 | Traces, metrics and logs APIs, SDKs and data models are stable; profiles are in public alpha |
| OTLP (`opentelemetry-proto`) | 1.11.0 (21 July 2026) | Traces, metrics and logs messages are stable; profiles live in the `v1development` package |
| Semantic conventions | 1.44.0 (August 2026) | Schema URL `https://opentelemetry.io/schemas/1.44.0` |
| GenAI semantic conventions | `semantic-conventions-genai`, `main` branch on 2 October 2026 | Moved out of the main repository in v1.42.0 (June 2026); no tagged release; the schema URL section of its README still says "TODO"; every GenAI name is at development stability |
| Prometheus | 3.14.0 (17 August 2026) | OTLP receiver, UTF-8 names, translation strategies |
| OpenTelemetry Collector contrib | v0.161.0 (15 September 2026; v0.162.0 followed on 29 September) | Most component types are snake_case (`tail_sampling`, `span_metrics`, `signal_to_metrics`), but not all were renamed (`deltatocumulative`); 45b.2 lists the renames |
| Grafana Tempo | 3.1 (29 September 2026) | TraceQL and TraceQL metrics, including sampling-aware extrapolation |
| Prices | List prices on 2 October 2026 | Claude API, Voyage AI, AWS Fargate, DynamoDB and SES, Grafana Cloud, Datadog |

**Stability levels.** Semantic-convention pages mark each convention group, attribute and metric as *development* (names and meanings may still change or disappear), *release candidate* (believed complete and waiting for implementation feedback; breaking changes are unlikely but still possible), *stable* (only changes a schema file can describe, such as renames, plus additions), or *deprecated* (kept in the registry with a pointer to its replacement because older instrumentation still emits it). A few newer attributes carry *alpha*. Collector components have their own scale (development, alpha, beta, stable) per signal. "Stable" is a promise about names and meanings, not a promise that your library or backend implements them, so pin the convention version your instrumentation emits (it travels with the data as `schema_url`) and treat development names as configuration that can change under you.

## 29b.2 Definitions

Each entry gives a definition and an example. Where another chapter covers the idea in depth, the entry points there instead of repeating it.

### Foundations

**Monitoring.** Collecting measurements chosen in advance and alerting when they cross thresholds chosen in advance. It answers the questions you knew to ask. *Example:* page when the 5xx ratio of checkout stays above 1% for ten minutes.

**Observability.** A property of a system and its telemetry: how well you can explain any internal state, including states nobody anticipated, from data the system already emits, without shipping new code. The word comes from control theory (Rudolf Kálmán, 1960), where a system is observable if its internal state can be inferred from its outputs. *Example:* discovering that only requests from one tenant, on one model route, with prompts above 100,000 tokens time out, by slicing existing spans by attributes nobody had put on a dashboard.

**Telemetry.** The data a system emits about its own behavior (measurements, events, records), produced by instrumentation and shipped elsewhere for storage and analysis. *Example:* an SDK exporting a batch of spans over OTLP every five seconds.

**Signal.** One category of telemetry with its own data model and API. OpenTelemetry defines traces, metrics and logs, plus baggage (propagated context, not stored data) and profiles (public alpha since 26 March 2026; 45b.2 lists the per-language status). An *event* is a log record with a name. *Example:* one LLM call produces a span (traces), adds to token and duration histograms (metrics) and may emit an opt-in content event (logs).

### Metric instruments, point kinds and Prometheus types

**Instrument.** The API object that code uses to record measurements. Its kind fixes the default aggregation, the OTLP point type and therefore the Prometheus type at the end of the pipeline.

| OpenTelemetry instrument | Records | Example | Default aggregation and OTLP point | Prometheus type after export |
|---|---|---|---|---|
| Counter | Monotonic increments | Tokens billed, requests served | Sum, monotonic | counter (`_total`) |
| Asynchronous Counter | Monotonic totals read in a callback | CPU seconds read from the operating system | Sum, monotonic | counter |
| UpDownCounter | Increments and decrements | Requests in flight, items in an in-process queue | Sum, non-monotonic | gauge |
| Asynchronous UpDownCounter | Totals that can fall, read in a callback | Memory in use | Sum, non-monotonic | gauge |
| Gauge and Asynchronous Gauge | The current value, which must not be summed | Temperature, configured pool size, a cache-hit ratio | Gauge (last value) | gauge |
| Histogram | A distribution of values | Request duration, tokens per call | Histogram with explicit buckets, or an exponential histogram if configured | classic histogram (`_bucket`, `_sum`, `_count`) or native histogram |
| (no instrument) | Quantiles computed in the client | Legacy client libraries, bridged | Summary | summary |

**Explicit-bucket histogram.** Counts of values falling between fixed boundaries, plus a count, sum, and optionally min and max. Bucket *i* holds values greater than boundary *i−1* and less than or equal to boundary *i*. *Example:* the HTTP conventions advise the boundaries 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5 and 10 seconds.

**Exponential histogram.** A histogram whose boundaries are powers of base = 2^(2^−scale), so the relative precision is the same at 1 millisecond and at 100 seconds, and histograms with compatible scales merge exactly. *Example:* at scale 3 each bucket is 9.05% wider than the previous one, so the midpoint of a bucket is within about ±4.3% of any value in it. Prometheus stores these as native histograms.

**Summary.** Quantiles (for example p50, p90, p99) computed in the client over a sliding window, plus a count and a sum. Quantiles from different instances cannot be combined into a fleet quantile, so the summary is a compatibility format in OTLP; use histograms for anything you will aggregate. *Example:* a Java service exposing `rpc_latency{quantile="0.99"}` from an older client library.

**Prometheus metric types.** Counter, gauge, histogram (classic, with one series per bucket and an `le` label, or native, stable since Prometheus 3.8, with all buckets in one series) and summary. OpenMetrics 1.0 adds gaugehistogram, info, stateset and unknown. 45b.3 covers storage, and 45b.4 the queries.

**Cardinality.** The number of distinct values of an attribute, or, for a metric, the number of distinct series it produces: the product of the distinct values of its labels, multiplied by the series per label set (17 for a classic histogram with 14 boundaries). Cardinality drives metric memory and cost; 45a.2 works the arithmetic. *Example:* adding a tenant label with 500 values to `gen_ai.client.token.usage` multiplies its series by 500 (29b.5 prices it).

**Dimensionality.** The number of attributes (dimensions) on a record. Traces and logs tolerate high dimensionality and high cardinality because they are stored per event; metrics tolerate dimensionality only with bounded cardinality. *Example:* a span with 40 attributes, including a conversation id, is normal; a metric with a conversation-id label is an outage waiting to happen.

**Exemplar.** A single raw measurement kept alongside an aggregated metric point, carrying the trace id and span id of the request that produced it, so a dashboard can jump from a slow bucket to the trace behind it. OpenTelemetry SDKs keep exemplars only from sampled traces by default (exemplar filter `trace_based`); Prometheus stores them only with the `exemplar-storage` feature flag. *Example:* the highest occupied bucket of `gen_ai.client.operation.duration` links to the 7.285-second final-answer call in 29b.6.

**Aggregation temporality.** Whether a Sum or Histogram point reports the change since the previous report (*delta*: the intervals (T0, T1], (T1, T2], (T2, T3]) or the running total since a fixed start (*cumulative*: (T0, T1], (T0, T2], (T0, T3]). Cumulative survives a lost export and is what Prometheus expects; delta needs less memory in the SDK and suits backends that sum on ingest. Gauges have no temporality. *Example:* a token counter that reports 1,000 and then 1,500 cumulatively reports 1,000 and then 500 as deltas. 45b.2 lists the SDK setting and Prometheus's experimental delta options.

**Single-writer principle.** Every metric stream (29b.3.3 lists what identifies one) must have exactly one writer. Two writers of one stream produce interleaved points that a backend rejects as duplicates or out of order, or worse, accepts as a counter that keeps resetting. *Example:* two Collector replicas that each compute a cost counter for the same service and model must add something that tells their outputs apart, and it has to survive translation into the backend's series identity (45b.2, 29b.5.4).

### Traces

**Trace.** All spans that share one 16-byte trace id: the record of one end-to-end operation, usually a request, across threads, processes and services. *Example:* one agent run, from the HTTP request to the final guard check, in fourteen spans (29b.6).

**Span.** A named, timed operation inside a trace, with a parent (unless it is the root), a kind, attributes, events, links and a status. *Example:* `chat claude-sonnet-5-5`, 7.285 seconds, with token counts and a computed cost as attributes.

**Span kind.** The span's role in a remote interaction. SERVER handles an incoming synchronous request; CLIENT makes an outgoing synchronous request; PRODUCER creates or sends a message that will be processed later; CONSUMER processes such a message; INTERNAL has no remote side. Backends pair CLIENT and SERVER spans to draw service graphs. *Example:* an LLM API call is CLIENT; an `execute_tool` span for an in-process Python function is INTERNAL.

**Span status.** Unset (the default), Error or Ok. Instrumentation sets Error when the operation failed and otherwise leaves the status Unset; Ok is for application code or configuration that wants to override a failure classification, and once set it cannot be changed back. *Example:* the server span for an HTTP 404 stays Unset (the caller made the mistake), while the client span that received the 404 is Error.

**Span event.** A timestamped, named annotation inside a span, with attributes. The convention that put exceptions on spans as `exception` events is now deprecated in favor of log-based events correlated with the span (29b.3.4). *Example:* a `retry.scheduled` event with the back-off delay as an attribute.

**Span link.** A pointer from one span to another span context, possibly in another trace, used when one operation relates to others but a single parent does not fit. *Example:* a consumer span that processes a batch of 200 messages links to the 200 producer spans.

### Context

**Context.** The immutable in-process carrier for the active span context (trace id, span id, trace flags, trace state, and whether that span context arrived from another process) and for baggage. *Example:* a coroutine started inside a request inherits the context, so the spans it creates get the right parent.

**Context propagation.** Injecting the context into an outgoing carrier (HTTP headers, message headers, the `_meta` field of an MCP request) and extracting it on the other side, so spans in different processes join one trace. *Example:* an agent calls a remote MCP server, and the server's spans appear as children of the agent's tool-call span instead of starting a new trace.

**traceparent and tracestate.** The two W3C Trace Context headers. `traceparent` carries a version, the 32-hex-digit trace id, the 16-hex-digit id of the calling span and 8 bits of flags: bit 0 means sampled, and Trace Context Level 2 (a candidate recommendation) defines bit 1, *random*, which promises that the rightmost 7 bytes of the trace id are random. `tracestate` carries up to 32 vendor entries; OpenTelemetry's entry `ot` holds the sampling threshold. *Example:* `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-03` (flags 03: sampled and random) with `tracestate: ot=th:c`, which records a 25% sampling probability.

**Baggage.** Application key-value pairs propagated with the context to every downstream service (a W3C format, separate from trace context). Baggage is not copied onto spans unless a processor does it, and it travels to every service you call, including third parties, so it must never hold secrets or personal data. *Example:* `baggage: acme.tenant.id=t-4821,acme.feature=billing-support`, copied onto every span so cost can be rolled up per tenant and feature.

### Identity

**Resource.** The attributes describing the entity that produces telemetry (service, version, instance, deployment environment, host, container, Kubernetes pod, cloud region), attached once per batch rather than repeated on every record. *Example:* `service.name=support-agent`, `service.namespace=support`, `service.version=2.3.0`, `deployment.environment.name=production`.

**Instrumentation scope.** The name, and optionally the version, schema URL and attributes, of the library or module that emitted a group of records. It tells you whether a span came from an auto-instrumentation library or from your own code. *Example:* scope `acme.agent.loop` version `2.3.0` for spans created by the team's agent loop.

### Sampling

**Head sampling.** The keep-or-drop decision is made when the root span starts, from the trace id, and is propagated in the sampled flag so every service agrees. It is cheap and blind to how the request turns out. *Example:* the SDK sampler `parentbased_traceidratio` with argument 0.1 keeps 10% of traces; the default sampler is `parentbased_always_on`.

**Tail sampling.** The decision is made after the whole trace has been buffered, usually in a Collector tier, so it can keep every trace with an error, high latency or high cost, plus a random baseline. It requires every span of a trace to reach the same Collector instance (45b.2 shows the two-tier layout and sizing). *Example:* keep all traces containing an Error span or costing more than \$0.10, and 5% of the rest.

**Probabilistic sampling.** Keeping each trace with a fixed probability *p*, decided deterministically from the randomness in the trace id so that all participants agree. Each kept trace stands for 1/*p* traces, its *adjusted count*. OpenTelemetry's development-status tracestate specification encodes *p* as a 56-bit rejection threshold, `th`. *Example:* `ot=th:c` means *p* = 0.25, so each stored trace counts as four when you compute totals.

**Rate-limiting sampling.** Keeping at most a fixed number of traces, spans or bytes per second whatever the traffic, so storage cost is bounded. The effective probability then changes with load and must be recorded with the data, or totals cannot be reconstructed. *Example:* a tail-sampling `rate_limiting` policy capped at 500 spans per second.

**Adaptive (dynamic) sampling.** Adjusting probabilities per key (service, operation, status, tenant) to hit a target volume while keeping rare keys well represented. *Example:* Jaeger's remote sampling serves per-operation probabilities, which its backend can compute adaptively, to SDKs that use the `jaeger_remote` sampler; the Collector contrib `adaptive_tail_sampling` processor (development stability in v0.161.0) does the same in the tail and writes the rate it applied into `tracestate`.

### Statistics

**Percentile (quantile).** The value that a given share of observations do not exceed: p50 is the median, p99 the value that 99% of requests beat. Percentiles describe the experience of a share of users. They cannot be averaged across instances or added across hops (45a.3 and 45b.4), and when computed from histograms they are estimates whose error depends on the bucket width. *Example:* a p99 of 1.2 seconds means one request in a hundred takes longer than 1.2 seconds.

**Why averages lie.** The mean is dominated by the bulk of requests and hides the tail. Take 1,000 requests: 980 at 100 ms, 15 at 1 s and 5 at 10 s. The mean is (980 × 0.1 + 15 × 1 + 5 × 10) / 1,000 = 0.163 s, which looks healthy; the median is 100 ms, the p99 is 1 s and the p99.9 is 10 s. Five users in a thousand waited a hundred times longer than the median, and the mean does not show it. A mean also has no unit of experience: no user waited 163 ms. Agents make this worse, because a run is slow if any one of its calls is slow (29b.4).

### Reliability vocabulary

Chapter 45a defines these in depth, with burn-rate arithmetic; one line each here:

- **SLI:** a measured ratio of good events to valid events.
- **SLO:** a target for an SLI over a window, such as 99.9% of valid requests over 28 days.
- **SLA:** a contract with consequences, deliberately looser than the internal SLO.
- **Error budget:** one minus the SLO, counted in events or in time.
- **Burn rate:** the observed error ratio divided by the error budget; at 1 the budget lasts exactly the window, at 14.4 a 30-day budget is gone in 50 hours.

**MTTD, MTTA, MTTR, MTBF.** Mean time to detect (impact starts until it is detected), to acknowledge (alert until a person acknowledges it), to repair, recover or resolve (always say which, and from which starting point), and between failures (from the start of one failure to the start of the next). For a repairable system, steady-state availability is MTTF / (MTTF + MTTR), where MTTF is the mean uptime; many people write MTBF in its place. Incident durations are heavy-tailed, so one long incident moves a mean; Google's 2021 report *Incident Metrics in SRE* argues that these means are poorly suited to decisions and trend analysis, and DORA replaced its "mean time to restore" with *failed deployment recovery time*. Report medians and percentiles over many incidents. *Example:* one failure every 30 days (720 hours) and 43 minutes to recover gives 720 / (720 + 0.72) ≈ 99.90% availability.

**Golden signals.** From the Google SRE book: latency (track successful and failed requests separately, because fast errors flatter the average), traffic, errors (explicit, implicit such as a 200 with wrong content, and by policy) and saturation (how full the most constrained resource is). *Example:* for an LLM gateway, p95 time to first token, requests and tokens per second, 5xx plus guardrail-blocked responses, and the share of the provider's tokens-per-minute quota in use.

**RED.** Rate, errors and duration for every service or endpoint: the request-centered subset of the golden signals, created by Tom Wilkie in 2015. *Example:* the Collector's span-metrics connector produces RED for every span name (45b.2).

**USE.** For every resource, its utilization (share of time busy), saturation (work queued that it cannot yet serve) and errors: Brendan Gregg's method, published in 2012, for resources rather than requests. *Example:* GPU utilization, the number of requests waiting for a KV-cache slot, and ECC errors on an inference node.

**Apdex.** A score from 0 to 1 based on a target time T: requests at or under T count as satisfied, those up to 4T as tolerating (half credit), and slower or failed ones as frustrated (no credit). Apdex = (satisfied + tolerating / 2) / total. It hides the shape of the tail and depends on one arbitrary T, so use it only as a summary next to percentiles. *Example:* with T = 0.5 s, 850 satisfied, 120 tolerating and 30 frustrated requests score (850 + 60) / 1,000 = 0.91. New Relic's default T for application servers is 0.5 s.

### User-side monitoring

**Real user monitoring (RUM).** Telemetry from real users' browsers and apps: page loads, interactions, errors and network timing. It includes Core Web Vitals, which count as "good" at the 75th percentile when Largest Contentful Paint is at most 2.5 s, Interaction to Next Paint at most 200 ms (it replaced First Input Delay in 2024) and Cumulative Layout Shift at most 0.1. RUM sees what users experience, including their networks and devices, but only on the paths they take. *Example:* the time from pressing Send to the first streamed token on screen, measured in the browser.

**Synthetic monitoring.** Scripted probes run from fixed locations on a schedule: an HTTP check, a multi-step browser journey, or a canary prompt with a known answer. It detects outages when there is no traffic and provides SLA evidence, but it never sees the long tail of real inputs. *Example:* a probe that asks the support agent a fixed billing question every minute and checks that the answer links to the refund policy.

### Profiling

**Profiling.** Sampling where a program spends a resource and aggregating the samples by stack trace. The main types:

- **CPU (on-CPU):** stacks sampled at a fixed frequency while threads run. *Example:* JSON serialization of tool results using 30% of the orchestrator's CPU.
- **Heap or memory:** allocations (count and bytes) or memory in use, by allocation site. *Example:* finished transcripts that are never released.
- **Wall-clock:** all threads sampled whether running or not, so waiting shows up. *Example:* a request thread that spends 90% of its wall time waiting for a lock.
- **Off-CPU:** time threads spend blocked on I/O, locks, sleep or paging, usually measured by tracing the scheduler, often with eBPF. *Example:* a worker blocked on a synchronous DNS lookup.
- Also lock and mutex contention, and goroutine or thread counts.

**Continuous profiling.** Always-on, low-frequency profiling of production processes, stored as a time series of profiles that can be filtered by labels and compared across versions. Span profiles link profile samples to the span that was active (45b.10). *Example:* diffing the CPU profiles of versions 2.3.0 and 2.4.0 after a latency regression.

### Collection and standards

**eBPF instrumentation.** Small, kernel-verified programs attached to kernel and user-space probes that observe system calls, network traffic and function calls without changing or restarting the application. OpenTelemetry eBPF Instrumentation (OBI) uses it to emit spans and RED metrics for HTTP, gRPC, SQL and other protocols (45b.2). It sees protocols, not business context. *Example:* RED metrics for a vendor binary you cannot modify.

**Structured logging.** Logs as records with named fields (JSON, or OTLP log records) instead of free text, with consistent keys, a severity, and the trace and span ids of the active span. *Example:* `{"time":"2026-10-02T09:00:05.296Z","severity":"INFO","event":"tool.result","tool":"get_billing_history","rows":12,"trace_id":"5b8efff798038103d269b633813fc60c","span_id":"7d1e5a0b9c3f2846"}`.

**Wide event.** One structured record per unit of work per service, carrying every attribute that might later be worth slicing by (identifiers, versions, feature flags, tenant, counts, timings), instead of many narrow log lines. A span with rich attributes is a wide event plus timing and parentage, which is why traces and structured logs can answer questions no dashboard anticipated. *Example:* one record per agent run with tenant, model route, prompt version, step count, tokens, cost and outcome.

**Correlation ID.** Any identifier carried across components so that records about the same unit of work can be joined. The trace id is the standard one; business identifiers such as an order id or `gen_ai.conversation.id` correlate at a coarser grain, across many traces. *Example:* finding every trace of one support conversation by its conversation id.

**OTLP.** The OpenTelemetry Protocol: protobuf messages for each signal, sent over gRPC (port 4317) or HTTP (port 4318, paths `/v1/traces`, `/v1/metrics`, `/v1/logs` and `/v1development/profiles`), encoded as binary protobuf or JSON. Servers can report partial success, clients retry 429, 502, 503 and 504 responses with back-off, and since OTLP 1.11.0 the specification recommends default limits of 64 MiB per request and 4 MiB per response. 29b.3 covers the messages field by field.

**Collector.** A vendor-neutral process that receives, processes and exports telemetry through pipelines of receivers, processors, exporters and connectors (45b.2). *Example:* the gateway in 29b.5 that computes cost per span before tail sampling.

**Semantic conventions.** The registry of standard names, types, units and meanings for attributes, spans, metrics and events, so tools can interpret telemetry from any source. *Example:* the HTTP status code is `http.response.status_code`, not `status`, `http_status` or `code`.

**Schema URL.** A URL such as `https://opentelemetry.io/schemas/1.44.0`, recorded on each resource and scope block, that names the semantic-convention version the data follows. The schema file at that URL lists the renames between versions, so tools can translate data from one version to another (29b.3.9).

## 29b.3 The OpenTelemetry data model and the OTLP schema

The specification defines the data model; `opentelemetry-proto` encodes it as protobuf messages. Field numbers below are from the proto files on `main` at OTLP 1.11.0. You rarely type a field number, but knowing the shape lets you read raw exports, write Collector transformations and design warehouse tables without guessing.

### 29b.3.1 The envelope every signal shares

Every signal uses the same three-level envelope: a list of resource blocks, each holding a list of scope blocks, each holding the records. Resource and scope attributes are sent once per block instead of once per record.

| Signal | Top-level message | Resource level | Scope level | Records | OTLP/HTTP path | Status |
|---|---|---|---|---|---|---|
| Traces | `TracesData` (same shape as the export request) | `ResourceSpans` | `ScopeSpans` | `Span` | `/v1/traces` | Stable |
| Metrics | `MetricsData` | `ResourceMetrics` | `ScopeMetrics` | `Metric`, which holds data points | `/v1/metrics` | Stable |
| Logs | `LogsData` | `ResourceLogs` | `ScopeLogs` | `LogRecord` | `/v1/logs` | Stable |
| Profiles | `ProfilesData`, plus a shared `ProfilesDictionary` | `ResourceProfiles` | `ScopeProfiles` | `Profile`, which holds samples | `/v1development/profiles` | Development (public alpha) |

The levels have the same fields in every signal:

- **Resource level** (`ResourceSpans` and its siblings): `resource` = 1, the scope list = 2, `schema_url` = 3 (field 1000 is reserved).
- **Scope level** (`ScopeSpans` and its siblings): `scope` = 1, the records = 2, `schema_url` = 3.
- **`Resource`**: `attributes` = 1, `dropped_attributes_count` = 2, `entity_refs` = 3 (development; references to entities whose identifying keys must exist in the attributes).
- **`InstrumentationScope`**: `name` = 1, `version` = 2, `attributes` = 3, `dropped_attributes_count` = 4.
- **`KeyValue`**: `key` = 1, `value` = 2, an `AnyValue` whose one-of is `string_value` = 1, `bool_value` = 2, `int_value` = 3 (int64), `double_value` = 4, `array_value` = 5, `kvlist_value` = 6 or `bytes_value` = 7. Fields `string_value_strindex` = 8 and `key_strindex` = 3 are alpha additions used only by profiles.

The two `schema_url` fields have different scopes: the one on the resource block describes the resource attributes, and the one on the scope block describes the records under it. Instrumentation libraries set the scope-level URL to the convention version they were written against, which is how one batch can mix data from libraries pinned to different versions.

**OTLP/JSON rules that break hand-written payloads.** Field names are lowerCamelCase (`resourceSpans`, `startTimeUnixNano`). Trace and span ids are hex strings, not the base64 that generic protobuf JSON would produce. Enums must be integers (`"kind": 3`, not `"SPAN_KIND_CLIENT"`). Every 64-bit integer is a decimal string, which covers all timestamps, histogram counts and `intValue` attributes (`"intValue": "11220"`); decoders accept numbers too. Receivers must ignore unknown fields, which is what lets new fields roll out without breaking old Collectors.

### 29b.3.2 Traces: the Span message, field by field

| # | Field | Type | Meaning and rules |
|---|---|---|---|
| 1 | `trace_id` | bytes, 16 | Shared by every span of the trace; all zeros is invalid. Generate it randomly: probability sampling and the W3C random flag depend on its rightmost 7 bytes being random. |
| 2 | `span_id` | bytes, 8 | Unique within the trace; all zeros is invalid. |
| 3 | `trace_state` | string | The W3C `tracestate` at span creation, for example `ot=th:c`. |
| 4 | `parent_span_id` | bytes, 8 | Empty for a root span. For a span started from an incoming request, the id of the remote caller's span. |
| 16 | `flags` | fixed32 | Bits 0 to 7 are the W3C trace flags of the span's context (bit 0 sampled, bit 1 random). Bit 8 says whether the parent's remoteness is known and bit 9 whether the parent is remote. A sampled span with a known local parent has flags 0x101 = 257. |
| 5 | `name` | string | A low-cardinality name for the class of operation; identifiers go in attributes (rules below). |
| 6 | `kind` | enum | `UNSPECIFIED` 0 (receivers may treat it as INTERNAL), `INTERNAL` 1, `SERVER` 2, `CLIENT` 3, `PRODUCER` 4, `CONSUMER` 5. |
| 7 | `start_time_unix_nano` | fixed64 | Nanoseconds since the Unix epoch, from the local clock. |
| 8 | `end_time_unix_nano` | fixed64 | Not before the start. Duration is end minus start. Host clocks differ, so compare durations, never timestamps from two hosts (45a.8, question 17). |
| 9 | `attributes` | repeated `KeyValue` | Keys must be unique. The SDK keeps at most 128 by default (`OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT`) and does not truncate values unless you set `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT`. |
| 10 | `dropped_attributes_count` | uint32 | Attributes discarded at the limit. A non-zero value means data is being lost silently; alert on it. |
| 11 | `events` | repeated `Event` | `time_unix_nano` = 1, `name` = 2, `attributes` = 3, `dropped_attributes_count` = 4. Default limit 128 per span. |
| 12 | `dropped_events_count` | uint32 | Events discarded at the limit. |
| 13 | `links` | repeated `Link` | `trace_id` = 1, `span_id` = 2, `trace_state` = 3, `attributes` = 4, `dropped_attributes_count` = 5, `flags` = 6. Default limit 128. |
| 14 | `dropped_links_count` | uint32 | Links discarded at the limit. |
| 15 | `status` | `Status` | `message` = 2, `code` = 3 with `UNSET` 0, `OK` 1, `ERROR` 2. Field 1 is reserved. |

The rules behind the fields:

1. **Names.** A span name identifies a statistically interesting class of spans: `get_account`, not `get_account/42` (the id goes in an attribute) and not `get` (too vague). Semantic conventions fix the names for common operations: `{method} {http.route}` for HTTP servers, such as `GET /accounts/{id}`, never the raw path; the query summary, or `{db.operation.name} {target}`, for database calls; `{messaging.operation.name} {destination}` for messaging; `{gen_ai.operation.name} {gen_ai.request.model}` for model calls; `execute_tool {gen_ai.tool.name}` for tools. A high-cardinality span name breaks every backend feature that groups by name, including span metrics, whose series multiply by the number of distinct names.
2. **Kind.** Choose it by the remote interaction, not by importance. A call over the network to a model API is CLIENT; a model loaded in-process may be INTERNAL. `invoke_agent` is CLIENT when it calls a remote agent service and INTERNAL for an agent running in your process. `execute_tool` is INTERNAL; any HTTP or database call the tool makes is its own CLIENT child. A queue publish is PRODUCER and the processing is CONSUMER.
3. **Status.** Leave it Unset unless the operation failed. On failure set Error, put human-readable detail in the message (the exception message, for example) without repeating the status code, and set `error.type` (stable) to the exception's type, the error code, or `_OTHER`. For HTTP, a server span is Error only for 5xx responses, because a 4xx is the caller's mistake, while a client span is Error for both 4xx and 5xx; 1xx to 3xx are never errors, and neither is a request the caller canceled on purpose (a user stopping a streamed answer, a hedged duplicate). Instrumentation libraries do not set Ok; application code may, and Ok then wins over any later attempt to set Error. If an operation is retried and finally succeeds, the logical operation is not an error, although each failed attempt's own span records its failure.
4. **Events.** Recording exceptions as `exception` span events is deprecated in the 1.44.0 conventions. Instrumentations are moving exceptions to log records correlated with the span (29b.3.4), controlled during the transition by `OTEL_SEMCONV_EXCEPTION_SIGNAL_OPT_IN` set to `logs` or `logs/dup`; SDKs can still route such records to span events if your backend prefers them. Record each exception once, at the boundary where it escapes.
5. **Links or a parent.** The messaging conventions use links between producer and consumer spans by default, because batch receives and processing inside another request make a single parent impossible. Add links at span creation when you can: head samplers see only what exists when the span starts.
6. **Timestamps.** A span is exported only when it ends, so the root of a 20-minute agent run, and any long step inside it, stays invisible until it closes, while finished children arrive earlier. Long-running work therefore benefits from smaller child spans, and tail-sampling buffers must be sized for the longest trace (chapter 29).

A trace in OTLP/JSON with two of the fourteen spans from the agent run in 29b.6: the `invoke_agent` span and the final-answer model call under it. The `acme.cost.*` attributes are custom (29b.5 explains the `acme.` prefix); everything else is a semantic-convention name.

```json
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          { "key": "service.name", "value": { "stringValue": "support-agent" } },
          { "key": "service.namespace", "value": { "stringValue": "support" } },
          { "key": "service.version", "value": { "stringValue": "2.3.0" } },
          { "key": "service.instance.id", "value": { "stringValue": "0b6f3a52-6a1e-4c0e-9d0f-2b7f0c9c4a11" } },
          { "key": "deployment.environment.name", "value": { "stringValue": "production" } }
        ]
      },
      "schemaUrl": "https://opentelemetry.io/schemas/1.44.0",
      "scopeSpans": [
        {
          "scope": { "name": "acme.agent.loop", "version": "2.3.0" },
          "spans": [
            {
              "traceId": "5b8efff798038103d269b633813fc60c",
              "spanId": "eee19b7ec3c1b174",
              "traceState": "ot=th:0",
              "parentSpanId": "53995c3f42cd8ad8",
              "flags": 257,
              "name": "invoke_agent billing-support",
              "kind": 1,
              "startTimeUnixNano": "1790931600040000000",
              "endTimeUnixNano": "1790931616524000000",
              "attributes": [
                { "key": "gen_ai.operation.name", "value": { "stringValue": "invoke_agent" } },
                { "key": "gen_ai.agent.name", "value": { "stringValue": "billing-support" } },
                { "key": "gen_ai.conversation.id", "value": { "stringValue": "conv_7f3a91" } }
              ],
              "status": {}
            },
            {
              "traceId": "5b8efff798038103d269b633813fc60c",
              "spanId": "c2d9e1f0a3b47586",
              "traceState": "ot=th:0",
              "parentSpanId": "eee19b7ec3c1b174",
              "flags": 257,
              "name": "chat claude-sonnet-5-5",
              "kind": 3,
              "startTimeUnixNano": "1790931608902000000",
              "endTimeUnixNano": "1790931616187000000",
              "attributes": [
                { "key": "gen_ai.operation.name", "value": { "stringValue": "chat" } },
                { "key": "gen_ai.provider.name", "value": { "stringValue": "anthropic" } },
                { "key": "gen_ai.request.model", "value": { "stringValue": "claude-sonnet-5-5" } },
                { "key": "gen_ai.response.model", "value": { "stringValue": "claude-sonnet-5-5" } },
                { "key": "gen_ai.request.stream", "value": { "boolValue": true } },
                { "key": "gen_ai.response.time_to_first_chunk", "value": { "doubleValue": 1.0 } },
                { "key": "gen_ai.usage.input_tokens", "value": { "intValue": "11220" } },
                { "key": "gen_ai.usage.cache_read.input_tokens", "value": { "intValue": "6000" } },
                { "key": "gen_ai.usage.output_tokens", "value": { "intValue": "420" } },
                { "key": "gen_ai.response.finish_reasons", "value": { "arrayValue": { "values": [ { "stringValue": "stop" } ] } } },
                { "key": "server.address", "value": { "stringValue": "api.anthropic.com" } },
                { "key": "server.port", "value": { "intValue": "443" } },
                { "key": "acme.cost.usd", "value": { "doubleValue": 0.01584 } },
                { "key": "acme.cost.price_table", "value": { "stringValue": "2026-10-01" } }
              ],
              "status": {}
            }
          ]
        }
      ]
    }
  ]
}
```

`ot=th:0` is a rejection threshold of zero, a sampling probability of 100%. An empty `status` object is Unset, because default values are not serialized.

### 29b.3.3 Metrics: metric, point kinds and data points

**The `Metric` message.** `name` = 1, `description` = 2, `unit` = 3, then exactly one of `gauge` = 5, `sum` = 7, `histogram` = 9, `exponential_histogram` = 10 or `summary` = 11, and `metadata` = 12 (non-identifying key-values about the metric; fields 4, 6 and 8 are reserved). Units follow UCUM (`s`, `ms`, `By`, `1`), and a part in braces is an annotation, not a unit: `{token}`, `{request}`, `{USD}`. The conventions never put a unit in a metric name and never end a counter name in `_total`; exporters add those for Prometheus.

**Point kinds.**

| Kind | Fields | Rules |
|---|---|---|
| `Gauge` | `data_points` (`NumberDataPoint`) | Last value; no temporality; never summed over time. |
| `Sum` | `data_points`, `aggregation_temporality` = 2 (`DELTA` 1, `CUMULATIVE` 2), `is_monotonic` = 3 | Monotonic cumulative sums become Prometheus counters; non-monotonic sums become gauges. |
| `Histogram` | `data_points` (`HistogramDataPoint`), `aggregation_temporality` = 2 | Explicit boundaries; `bucket_counts` has one more entry than `explicit_bounds`. |
| `ExponentialHistogram` | `data_points` (`ExponentialHistogramDataPoint`), `aggregation_temporality` = 2 | Boundaries implied by `scale`. |
| `Summary` | `data_points` (`SummaryDataPoint`) | Compatibility format: count, sum and precomputed quantiles; cannot be aggregated across instances. |

**Data point fields.**

| Point | Fields (number) |
|---|---|
| `NumberDataPoint` | `attributes` 7, `start_time_unix_nano` 2, `time_unix_nano` 3, value `as_double` 4 or `as_int` 6, `exemplars` 5, `flags` 8 |
| `HistogramDataPoint` | `attributes` 9, `start_time_unix_nano` 2, `time_unix_nano` 3, `count` 4, `sum` 5 (optional), `bucket_counts` 6, `explicit_bounds` 7, `exemplars` 8, `flags` 10, `min` 11, `max` 12 |
| `ExponentialHistogramDataPoint` | `attributes` 1, `start_time_unix_nano` 2, `time_unix_nano` 3, `count` 4, `sum` 5, `scale` 6, `zero_count` 7, `positive` 8 and `negative` 9 (each `Buckets`: `offset` 1, `bucket_counts` 2), `flags` 10, `exemplars` 11, `min` 12, `max` 13, `zero_threshold` 14 |
| `SummaryDataPoint` | `attributes` 7, `start_time_unix_nano` 2, `time_unix_nano` 3, `count` 4, `sum` 5, `quantile_values` 6 (each `quantile` 1, `value` 2), `flags` 8 |
| `Exemplar` | `filtered_attributes` 7, `time_unix_nano` 2, value `as_double` 3 or `as_int` 6, `span_id` 4, `trace_id` 5 |

The rules that matter in practice:

- **Identity.** A metric stream is identified by its resource, scope, metric name, unit, point kind and the data point's attributes. Every stream must have exactly one logical writer (the single-writer principle). Two writers (two replicas reporting the same attributes without an instance id, for example) produce overlapping points that receivers have to drop or deduplicate. Translation can break the rule even when OTLP keeps it: a Prometheus-compatible backend builds a series from `job`, `instance` and the point's attributes only, so two streams that differ only in some other resource attribute become one series there (table below).
- **Start time.** For cumulative points the start time stays fixed while the series is unbroken; a new start time marks a reset, such as a process restart. For delta points each start time equals the previous point's time. A start time equal to the point's time means a reset at an unknown moment.
- **Flags.** Bit 0, `NO_RECORDED_VALUE`, marks a series that disappeared: the equivalent of a Prometheus staleness marker. All other fields of such a point except attributes and timestamps are ignored.
- **Explicit buckets.** Bucket 0 holds values up to and including `explicit_bounds[0]`, bucket *i* holds values above `explicit_bounds[i−1]` up to and including `explicit_bounds[i]`, and the last bucket holds everything above the last bound. OTLP bucket counts are per bucket; Prometheus `_bucket` series are cumulative (each `le` includes all smaller buckets), and the exporter converts between them.
- **The default-bucket trap.** The SDK's default explicit boundaries are 0, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1,000, 2,500, 5,000, 7,500 and 10,000: designed for milliseconds. The conventions record durations in seconds and ship advisory boundaries with each metric (the HTTP list in 29b.2; 0.01 to 81.92 seconds, doubling, for the GenAI client duration). A hand-made histogram in seconds that keeps the default boundaries puts almost every request into the bucket from 0 to 5 seconds, and every percentile from it is useless. Set boundaries in a View.
- **Exponential buckets.** With base = 2^(2^−scale), the bucket with index *i* holds values above base^*i* up to and including base^(*i*+1), and `bucket_counts[k]` is the count for index `offset + k`. The index of a positive value *v* is ⌈log₂(*v*) × 2^scale⌉ − 1. The SDK defaults are at most 160 buckets per sign and a maximum scale of 20; the SDK lowers the scale as the observed range widens, so that 160 buckets still cover it. Values spanning 1 ms to 100 s, a ratio of 10⁵ (about 2^16.6), end at scale 3, because scale 3 covers 2^(160/8) = 2^20 and scale 4 only 2^10. Prometheus native histograms accept schemas −4 to 8, so points at higher scales are reduced to 8 on conversion.
- **Worked exponential example.** The four Claude Sonnet call durations in 29b.6 (2.085, 2.485, 3.335 and 7.285 seconds), recorded through a View that caps the scale at 3: log₂ of each value times 8 is 8.48, 10.51, 13.90 and 22.92, so the indices are 8, 10, 13 and 22. The point has `offset` 8 and 15 bucket counts, with a 1 at positions 0, 2, 5 and 14. The bucket for index 22 spans 6.727 to 7.336 seconds, so the 7.285-second call is known to within about ±4.3%.
- **Exemplars.** `filtered_attributes` holds the measurement's attributes that aggregation removed (a View that drops `acme.tenant.id` from the metric can still keep it on the exemplar). The default filter is `trace_based` (`OTEL_METRICS_EXEMPLAR_FILTER` also accepts `always_on` and `always_off`); explicit-bucket histograms keep one exemplar per bucket, and other aggregations a small fixed-size reservoir.
- **Cardinality limit.** The SDK specification's default limit is 2,000 attribute sets per metric; measurements beyond it are folded into one series carrying `otel.metric.overflow=true`. Treat a non-zero overflow series as an alert.

A metrics export from the same service in OTLP/JSON: the Claude Sonnet data point of `gen_ai.client.operation.duration` after the four calls, with an exemplar pointing to the final-answer span, and a cost counter.

```json
{
  "resourceMetrics": [
    {
      "resource": {
        "attributes": [
          { "key": "service.name", "value": { "stringValue": "support-agent" } },
          { "key": "service.namespace", "value": { "stringValue": "support" } },
          { "key": "service.instance.id", "value": { "stringValue": "0b6f3a52-6a1e-4c0e-9d0f-2b7f0c9c4a11" } }
        ]
      },
      "scopeMetrics": [
        {
          "scope": { "name": "acme.agent.loop", "version": "2.3.0" },
          "metrics": [
            {
              "name": "gen_ai.client.operation.duration",
              "description": "GenAI operation duration.",
              "unit": "s",
              "histogram": {
                "aggregationTemporality": 2,
                "dataPoints": [
                  {
                    "attributes": [
                      { "key": "gen_ai.operation.name", "value": { "stringValue": "chat" } },
                      { "key": "gen_ai.provider.name", "value": { "stringValue": "anthropic" } },
                      { "key": "gen_ai.request.model", "value": { "stringValue": "claude-sonnet-5-5" } }
                    ],
                    "startTimeUnixNano": "1790928000000000000",
                    "timeUnixNano": "1790931660000000000",
                    "count": "4",
                    "sum": 15.19,
                    "bucketCounts": ["0", "0", "0", "0", "0", "0", "0", "0", "2", "1", "1", "0", "0", "0", "0"],
                    "explicitBounds": [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92],
                    "min": 2.085,
                    "max": 7.285,
                    "exemplars": [
                      {
                        "timeUnixNano": "1790931616187000000",
                        "asDouble": 7.285,
                        "traceId": "5b8efff798038103d269b633813fc60c",
                        "spanId": "c2d9e1f0a3b47586"
                      }
                    ]
                  }
                ]
              }
            },
            {
              "name": "acme.llm.cost",
              "description": "Model spend computed from token counts and the 2026-10-01 price table.",
              "unit": "{USD}",
              "sum": {
                "aggregationTemporality": 2,
                "isMonotonic": true,
                "dataPoints": [
                  {
                    "attributes": [
                      { "key": "gen_ai.request.model", "value": { "stringValue": "claude-sonnet-5-5" } }
                    ],
                    "startTimeUnixNano": "1790928000000000000",
                    "timeUnixNano": "1790931660000000000",
                    "asDouble": 0.04162
                  }
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

The bucket counts put two calls in the bucket above 1.28 and up to 2.56 seconds, one in the bucket up to 5.12 and one in the bucket up to 10.24. The start time is the process start (08:00 UTC), and the point covers everything since then, which is what cumulative temporality means; to keep the numbers readable, this process has served only the one run.

**How OTLP metrics become Prometheus series.** The OpenTelemetry compatibility specification and Prometheus's OTLP receiver (enabled with `--web.enable-otlp-receiver`, serving `/api/v1/otlp/v1/metrics`) apply these rules:

| OTLP | Prometheus |
|---|---|
| Monotonic cumulative Sum | Counter; `_total` appended |
| Non-monotonic Sum | Gauge |
| Delta Sum or delta Histogram | Dropped, unless converted to cumulative first (the Collector's `deltatocumulative` processor, or Prometheus's experimental `otlp-deltatocumulative` flag); `otlp-native-delta-ingestion` stores raw deltas experimentally |
| Gauge | Gauge; unit `1` becomes the suffix `_ratio` |
| Explicit-bucket Histogram | Classic histogram: `_bucket` with cumulative `le` labels, `_sum`, `_count`; or a native histogram with custom buckets when `convert_histograms_to_nhcb` is on. Boundaries are written as given, so a bound of 1 becomes `le="1"`, not the `le="1.0"` that Prometheus 3 writes for scraped histograms |
| ExponentialHistogram | Native histogram (scale reduced to at most 8), one series per label set |
| Summary | Summary: `{quantile="0.99"}`, `_sum`, `_count` |
| Resource attributes | `service.namespace` and `service.name` form `job` (as `namespace/name`), `service.instance.id` becomes `instance`, and the rest go to a `target_info` series unless promoted with `promote_resource_attributes` |
| Scope | The specification's exporters add `otel_scope_name`, `otel_scope_version` and `otel_scope_schema_url` labels; Prometheus's receiver adds scope labels only with `promote_scope_metadata` |
| Exemplar | Prometheus exemplar with `trace_id` and `span_id` labels (stored only with the `exemplar-storage` flag) |

Metric and label names depend on the receiver's `translation_strategy`. For `http.server.request.duration` (unit `s`, attribute `http.request.method`):

| Strategy | Metric name | Label name | Notes |
|---|---|---|---|
| `UnderscoreEscapingWithSuffixes` (default) | `http_server_request_duration_seconds` | `http_request_method` | The conventional Prometheus form; unit and type suffixes added, unsupported characters become `_` |
| `UnderscoreEscapingWithoutSuffixes` | `http_server_request_duration` | `http_request_method` | Shorter names; metrics that differ only by unit or type can collide |
| `NoUTF8EscapingWithSuffixes` | `http.server.request.duration_seconds` | `http.request.method` | Keeps dots, adds suffixes; quote names in PromQL: `{"http.server.request.duration_seconds", "http.request.method"="GET"}` |
| `NoTranslation` (experimental) | `http.server.request.duration` | `http.request.method` | Names exactly as in OTLP; collisions possible without suffixes |

Unit translation turns `s` into `seconds`, `By` into `bytes`, `ms` into `milliseconds` and `By/s` into `bytes_per_second`, and drops annotations in braces, so `gen_ai.client.token.usage` (unit `{token}`) becomes `gen_ai_client_token_usage_bucket`, `_sum` and `_count`, and the cost counter above becomes `acme_llm_cost_total`. Prometheus 3.14 logs a warning, and counts it in `prometheus_api_otlp_translation_warnings_total`, when two attribute names collapse into the same label after escaping (`http.method` and `http_method`, for example). Choose one strategy for the whole estate before building dashboards; changing it later renames every series.

### 29b.3.4 Logs: the LogRecord and events

| # | Field | Rules |
|---|---|---|
| 1 | `time_unix_nano` (Timestamp) | When the event happened at the source; may be absent |
| 11 | `observed_time_unix_nano` (ObservedTimestamp) | When the collection system saw it; set by the SDK, the Collector or a log-file receiver. Formats with one timestamp use Timestamp when present and ObservedTimestamp otherwise |
| 2 | `severity_number` | Normalized severity, 1 to 24 (table below); 0 means unspecified |
| 3 | `severity_text` | The original level string, such as `WARNING` or `err` |
| 5 | `body` | `AnyValue`: a human-readable string or structured data |
| 6 | `attributes` | Event-specific attributes (default limit 128, `OTEL_LOGRECORD_ATTRIBUTE_COUNT_LIMIT`) |
| 7 | `dropped_attributes_count` | Attributes dropped at the limit |
| 8 | `flags` | W3C trace flags (bits 0 to 7) of the span context the log was emitted in |
| 9 | `trace_id` | Set automatically when the record is emitted inside an active span |
| 10 | `span_id` | Likewise |
| 12 | `event_name` | A non-empty name makes the record an *event*: all records with the same name share one structure for attributes and body |

Field 4 is reserved. Resource and scope come from the envelope.

| Range | Numbers | Use |
|---|---|---|
| TRACE | 1 to 4 | Fine-grained debugging |
| DEBUG | 5 to 8 | Debugging |
| INFO | 9 to 12 | Informational |
| WARN | 13 to 16 | Something unexpected that did not fail the operation |
| ERROR | 17 to 20 | A failed operation |
| FATAL | 21 to 24 | The process or service cannot continue |

Within a range, a higher number is more severe (`ERROR2` is 18). Map a source's levels to the first number of the matching range unless it has finer levels; Python's `WARNING`, `ERROR` and `CRITICAL` map to 13, 17 and 21. Comparisons work across sources because the ranges are fixed: `severity_number >= 17` selects every error, whatever each library calls it.

**Events.** There is no separate events signal any more: an event is a log record with `event_name` set, and the logs data model says semantic conventions defined for logs should be events. The GenAI conventions use events for opt-in content (`gen_ai.client.inference.operation.details`) and for evaluation results (`gen_ai.evaluation.result`); the exception conventions use an event named `exception`, or `<operation>.exception` such as `http.client.request.exception`, with `exception.type`, `exception.message` and `exception.stacktrace` (all stable). Severity for exceptions follows impact: FATAL (21) when the application shuts down, ERROR (17) when an unhandled exception does not stop it, WARN (13) for expected, handled exceptions. An exception event emitted by an instrumentation that also records a span for the operation must carry that span's context.

An online-evaluation result for the final answer in 29b.6, emitted by an evaluation worker and correlated with the model-call span:

```json
{
  "resourceLogs": [
    {
      "resource": {
        "attributes": [
          { "key": "service.name", "value": { "stringValue": "online-evals" } },
          { "key": "service.namespace", "value": { "stringValue": "support" } }
        ]
      },
      "scopeLogs": [
        {
          "scope": { "name": "acme.evals.judge", "version": "1.4.0" },
          "logRecords": [
            {
              "timeUnixNano": "1790931619310000000",
              "observedTimeUnixNano": "1790931619310400000",
              "severityNumber": 9,
              "severityText": "INFO",
              "eventName": "gen_ai.evaluation.result",
              "traceId": "5b8efff798038103d269b633813fc60c",
              "spanId": "c2d9e1f0a3b47586",
              "flags": 1,
              "attributes": [
                { "key": "gen_ai.evaluation.name", "value": { "stringValue": "groundedness" } },
                { "key": "gen_ai.evaluation.score.value", "value": { "doubleValue": 0.92 } },
                { "key": "gen_ai.evaluation.score.label", "value": { "stringValue": "pass" } },
                { "key": "gen_ai.evaluation.explanation", "value": { "stringValue": "Every claim cites the October invoice or the refund policy." } }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 29b.3.5 Profiles: status and data model in brief

Profiles entered public alpha on 26 March 2026. The messages live in the `opentelemetry.proto.profiles.v1development` package, the OTLP/HTTP path is `/v1development/profiles`, and the project's own guidance is not to use the signal for critical production workloads yet. Collector support at alpha includes a pprof receiver, the eBPF profiler running as a receiver, Kubernetes metadata from `k8s_attributes`, and OTTL in the transform processor (experimental for profiles).

The data model is built to round-trip pprof without loss while deduplicating aggressively:

- `ProfilesData` carries one **`ProfilesDictionary`** shared by every profile in the message: tables of strings, functions, locations (with lines), mappings (loaded binaries), stacks, attributes and links. Each table has a zero-value entry at index 0 meaning "not set", and records refer to entries by index, so a call stack appearing in a thousand samples is stored once.
- `ResourceProfiles` → `ScopeProfiles` → **`Profile`**: sample types (such as CPU nanoseconds or allocated bytes), the samples, a start time and duration, the sampling period and its type, an optional profile id, the original payload and its format (for example, the raw pprof), and attribute indices.
- **`Sample`**: a stack index, either values (one per sample type) or timestamps, attribute indices, and a link index. The **`Link`** holds a 16-byte trace id and an 8-byte span id: that is how a CPU sample is tied to the span that was running, which is what span profiles in Pyroscope use (45b.10).

### 29b.3.6 Resource and scope: the attributes that matter

| Attribute | Stability (1.44.0) | Notes |
|---|---|---|
| `service.name` | Stable | Required. Without it the SDK reports `unknown_service:` followed by the process name. Must be the same for all instances of a horizontally scaled service |
| `service.namespace` | Stable | Groups services; with `service.name` it forms the Prometheus `job` label |
| `service.version` | Stable | Any version string, such as `2.3.0` or a commit hash |
| `service.instance.id` | Stable | Unique per instance within a namespace and name; a random UUID, or a version-5 UUID derived from stable inputs. Becomes the Prometheus `instance` label, so a new value per pod restart is series churn (45a.2) |
| `deployment.environment.name` | Stable | Well-known values `production`, `staging`, `test`, `development`; replaced `deployment.environment` |
| `telemetry.sdk.name`, `.language`, `.version` | Stable | Set by the SDK itself |
| `k8s.cluster.name`, `k8s.namespace.name`, `k8s.pod.name`, `k8s.pod.uid`, `k8s.node.name`, `k8s.deployment.name`, `k8s.statefulset.name`, `k8s.daemonset.name`, `k8s.job.name`, `k8s.container.name` | Stable (Kubernetes conventions reached stable in June 2026) | Added by the Collector's `k8s_attributes` processor (45b.2) |
| `container.id`, `container.image.name`, `container.image.tags` | Stable | `container.name` and `container.runtime.name` are still development |
| `cloud.provider`, `cloud.platform`, `cloud.region`, `cloud.availability_zone`, `cloud.account.id`, `cloud.resource_id` | Development | Added by cloud resource detectors |
| `host.name`, `host.id`, `host.type`, `host.arch` | Development | Added by the host or system detectors |

**Resource detection.** In the SDK, `OTEL_SERVICE_NAME` sets the service name and `OTEL_RESOURCE_ATTRIBUTES` (comma-separated `key=value` pairs) sets the rest; built-in and contrib detectors add process, host, operating-system, container and cloud attributes at startup. In the Collector, the `resource_detection` processor queries the environment (detectors include `env`, `system`, `docker`, `ec2`, `ecs`, `eks`, `lambda`, `gcp`, `azure` and `aks`; when two detectors set the same attribute the first one listed wins, and `override` defaults to true) and `k8s_attributes` adds pod metadata by matching the connection's IP or a pod attribute. Rules of thumb: set identity (service name, namespace, version, environment) in the SDK, where it cannot be wrong; add infrastructure attributes in the Collector agent on each node, where they are cheap; keep high-churn values such as `service.instance.id` or `k8s.pod.name` out of metric labels unless you need them, and join `target_info` when you do (45b.4).

**Scope.** The scope name identifies the instrumentation library or module (an auto-instrumentation package, or your own `acme.agent.loop`), and the version tells you which release of it produced the data. Use it to separate auto-instrumented spans from business spans, to find which library emits an unexpected attribute, and to attribute telemetry volume to its source when you cut costs.

### 29b.3.7 Semantic conventions by domain, with stability

| Domain | Status in 1.44.0 | Span name and key attributes | Key metrics (instrument, unit) |
|---|---|---|---|
| HTTP | Stable since 1.23.0 | `{method} {http.route}` on servers, `{method}` or `{method} {url.template}` on clients; `http.request.method`, `http.route`, `url.path` and `url.scheme` (server), `url.full` (client), `http.response.status_code`, `server.address`, `server.port`, `error.type`, `http.request.resend_count` | `http.server.request.duration` and `http.client.request.duration` (histograms, `s`, stable); `http.server.active_requests` (UpDownCounter, `{request}`, development) |
| Database | Stable for client spans and the operation duration | `{db.query.summary}`, else `{db.operation.name} {target}`; `db.system.name`, `db.namespace`, `db.collection.name`, `db.operation.name`, `db.query.text` (keep parameterized queries as they are; replace literals in non-parameterized ones with `?`), `db.query.summary`, `db.response.status_code`, `db.operation.batch.size` | `db.client.operation.duration` (histogram, `s`, stable, advisory buckets 0.001 to 10); connection-pool metrics such as `db.client.connection.count` are development |
| RPC | Release candidate | `{rpc.method}`, else `{rpc.system.name}`; `rpc.system.name` (replaces `rpc.system`), `rpc.method` (fully qualified), `rpc.response.status_code`, `server.address`, `error.type` | `rpc.server.call.duration` and `rpc.client.call.duration` (histograms, `s`, release candidate); older instrumentation emits `rpc.server.duration` in milliseconds |
| Messaging | Development | `{messaging.operation.name} {destination}`; kind by operation type (create PRODUCER; send PRODUCER, or CLIENT when a separate create span exists; receive and settle CLIENT; process CONSUMER); `messaging.system`, `messaging.operation.name`, `messaging.operation.type`, `messaging.destination.name`, `messaging.message.id`, `messaging.batch.message_count`; links between producer and consumer by default | `messaging.client.operation.duration` and `messaging.process.duration` (`s`), `messaging.client.sent.messages` and `messaging.client.consumed.messages` (`{message}`), all development |
| Exceptions | Attributes stable; the span-event form deprecated in favor of log events | `exception.type`, `exception.message`, `exception.stacktrace`; event `exception` or `<operation>.exception` | none |
| Kubernetes and containers | Most resource attributes stable | See 29b.3.6 | `container.cpu.time` (Counter, `s`) and `container.memory.working_set` (UpDownCounter, `By`) are release candidate; `container.cpu.usage` and `k8s.pod.cpu.usage` (Gauges, `{cpu}`) are development |
| GenAI and MCP | Development, in `semantic-conventions-genai` | 29b.3.8 | 29b.3.8 |

When a domain changes from an experimental version to a stable one, instrumentations keep emitting the old names by default and switch through `OTEL_SEMCONV_STABILITY_OPT_IN`: `http` or `http/dup` for HTTP, `database` or `database/dup` for databases, `rpc` or `rpc/dup` for RPC (the `/dup` forms emit both, for migration), and `gen_ai_latest_experimental` for the newest GenAI names in libraries that support it. Chapter 45a.2 covers the migration playbook.

### 29b.3.8 The GenAI conventions, name by name

Chapter 29 explains how to use these conventions in an LLM system; this section is the exact-name reference. Everything here is at development stability, lives in the `semantic-conventions-genai` repository, and was read from its `main` branch on 2 October 2026. There is no release to pin, so pin the version of the instrumentation library you run and normalize names in the Collector (29b.3.9).

**Operations, span names and kinds.**

| `gen_ai.operation.name` | Span name | Kind |
|---|---|---|
| `chat`, `generate_content`, `text_completion` (inference) | `{gen_ai.operation.name} {gen_ai.request.model}`, such as `chat claude-sonnet-5-5` | CLIENT; INTERNAL allowed for in-process models |
| `embeddings` | `embeddings {gen_ai.request.model}` | CLIENT |
| `retrieval` | `retrieval {gen_ai.data_source.id}` | CLIENT |
| `execute_tool` | `execute_tool {gen_ai.tool.name}` | INTERNAL |
| `invoke_agent` | `invoke_agent {gen_ai.agent.name}` | CLIENT for a remote agent, INTERNAL in-process |
| `create_agent` | `create_agent {gen_ai.agent.name}` | CLIENT |
| `invoke_workflow` | `invoke_workflow {gen_ai.workflow.name}` | INTERNAL |
| `plan` | `plan {gen_ai.agent.name}` | INTERNAL |
| `fetch_response` | retrieves a previously generated response without new inference | |
| `create_memory`, `update_memory`, `upsert_memory`, `search_memory`, `delete_memory`, `create_memory_store`, `delete_memory_store` | memory operations | |

**Inference-span attributes.**

- *Required:* `gen_ai.operation.name`; `gen_ai.provider.name`, whose well-known values are `anthropic`, `aws.bedrock`, `azure.ai.inference`, `azure.ai.openai`, `cohere`, `deepseek`, `gcp.gemini`, `gcp.gen_ai`, `gcp.vertex_ai`, `groq`, `ibm.watsonx.ai`, `mistral_ai`, `moonshot_ai`, `openai`, `perplexity` and `x_ai` (other providers use their own value).
- *Conditionally required:* `gen_ai.request.model`, `gen_ai.conversation.id` (when available), `error.type` (on failure), `gen_ai.output.type`, `gen_ai.request.stream`, `gen_ai.request.seed`, `gen_ai.request.top_k`, `gen_ai.request.choice.count` (when not 1), `gen_ai.prompt.name` and `gen_ai.prompt.version` (when the prompt comes from a managed template), `server.port`.
- *Recommended:* `gen_ai.response.model`, `gen_ai.response.id`, `gen_ai.response.finish_reasons` (string array), `gen_ai.response.time_to_first_chunk` (seconds, for streaming requests), request parameters (`gen_ai.request.max_tokens`, `.temperature`, `.top_p`, `.frequency_penalty`, `.presence_penalty`, `.stop_sequences`, `.reasoning.level`, `.previous_response.id`), `gen_ai.conversation.compacted` (set only to `true`, when the context is a compacted view of an earlier conversation), `server.address`, and the usage attributes below.
- *Opt-in (content):* `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions`, `gen_ai.prompt.variable`.

**Usage attributes and how to read them.**

| Attribute | Meaning |
|---|---|
| `gen_ai.usage.input_tokens` | All input tokens, including tokens read from and written to a provider cache; the billed count when a provider reports both billed and consumed counts |
| `gen_ai.usage.cache_read.input_tokens` | Input tokens served from a provider-managed cache (a subset of input) |
| `gen_ai.usage.cache_write.input_tokens` | Input tokens written to a provider-managed cache (a subset of input). Semantic-convention releases up to v1.41.0 called this `gen_ai.usage.cache_creation.input_tokens`, and libraries pinned to those releases still emit that name |
| `gen_ai.usage.output_tokens` | All output tokens, billed count |
| `gen_ai.usage.reasoning.output_tokens` | Reasoning (thinking) tokens, a subset of output |
| `gen_ai.usage.text.input_tokens`, `.image.input_tokens`, `.audio.input_tokens`, the matching `.cache_read.input_tokens` and `.output_tokens` variants | Per-modality breakdowns, each a subset of the totals |

The subset rules are what cost formulas depend on: uncached input is `input_tokens − cache_read − cache_write`, and reasoning tokens are already inside `output_tokens`. `invoke_agent` spans may also carry usage totals for the whole run (recommended there), so a query that sums `gen_ai.usage.*` over every span of a trace counts the run twice; sum over inference spans only, or over agent spans only.

**Agent, tool, retrieval and memory attributes.** `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.description`, `gen_ai.agent.version`; `gen_ai.workflow.name`; `gen_ai.tool.name` (required on `execute_tool`), `gen_ai.tool.call.id`, `gen_ai.tool.type`, `gen_ai.tool.description` (recommended), `gen_ai.tool.call.arguments` and `gen_ai.tool.call.result` (opt-in); `gen_ai.data_source.id`; `gen_ai.retrieval.top_k` (recommended), `gen_ai.retrieval.query.text` and `gen_ai.retrieval.documents` (opt-in); `gen_ai.embeddings.dimension.count` and `gen_ai.request.encoding_formats`; `gen_ai.memory.store.id`, `gen_ai.memory.record.id`, `gen_ai.memory.record.count`, `gen_ai.memory.query.text`, `gen_ai.memory.records`.

**Events.** `gen_ai.client.inference.operation.details` carries the opt-in content (`gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions`) together with the operation, provider, model and conversation; on events the content must be structured, while on spans a JSON string is acceptable where structured attributes are not supported. `gen_ai.evaluation.result` carries `gen_ai.evaluation.name` (required), `gen_ai.evaluation.score.value`, `gen_ai.evaluation.score.label`, `gen_ai.evaluation.explanation` and `gen_ai.response.id`.

**Content capture in practice.** Capture is off by default. The OpenTelemetry Python GenAI instrumentations turn it on with `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`: `true` gives the older event format, while `span_only`, `event_only` and `span_and_event` use the newest conventions and require `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`. Setting `OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK=upload` with `OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH` pointing at an fsspec path (a bucket such as `gs://my_bucket`, or a directory) writes content to storage instead of into telemetry, which is the cheapest and safest default for large prompts (29b.5.7).

**Metrics.**

| Metric | Instrument, unit | Required attributes | Advisory buckets |
|---|---|---|---|
| `gen_ai.client.token.usage` | Histogram, `{token}` | `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.token.type` (`input` or `output`) | 1, 4, 16, ... ×4 ... 67,108,864 |
| `gen_ai.client.operation.duration` | Histogram, `s` | `gen_ai.operation.name` | 0.01 to 81.92, doubling |
| `gen_ai.client.operation.time_to_first_chunk` | Histogram, `s` | `gen_ai.operation.name`, `gen_ai.provider.name` | 0.01 to 81.92, doubling |
| `gen_ai.client.operation.time_per_output_chunk` | Histogram, `s` | `gen_ai.operation.name`, `gen_ai.provider.name` | 0.01 to 81.92, doubling |
| `gen_ai.server.request.duration` | Histogram, `s` | `gen_ai.operation.name`, `gen_ai.provider.name` | 0.01 to 81.92, doubling |
| `gen_ai.server.time_to_first_token` | Histogram, `s` | `gen_ai.operation.name`, `gen_ai.provider.name` | 0.001 to 10 |
| `gen_ai.server.time_per_output_token` | Histogram, `s` | `gen_ai.operation.name`, `gen_ai.provider.name` | 0.01 to 2.5 |
| `gen_ai.invoke_agent.duration` | Histogram, `s` | (`gen_ai.agent.name` when available) | 0.1 to 409.6, doubling |
| `gen_ai.invoke_agent.inference_calls` | Histogram, `{inference_call}` | | 1 to 128, doubling |
| `gen_ai.invoke_agent.tool_calls` | Histogram, `{tool_call}` | | 1 to 128, doubling |
| `gen_ai.execute_tool.duration` | Histogram, `s` | `gen_ai.tool.name` | 0.01 to 81.92, doubling |
| `gen_ai.invoke_workflow.duration` | Histogram, `s` | (`gen_ai.workflow.name` when available) | 1 to 7,200 |

The client metrics also take `gen_ai.request.model`, `gen_ai.response.model`, `server.address`, `server.port` and, on failures, `error.type`. Note what the token metric cannot tell you: `gen_ai.token.type` has only `input` and `output`, so cache reads and writes, which decide cost, are visible only on spans. A cost metric has to be derived from spans (29b.5.4).

**MCP.** The same repository defines Model Context Protocol spans named `{mcp.method.name} {target}` (the target is the tool or prompt name when there is one, as in `tools/call get_billing_history`), CLIENT on the caller and SERVER on the server, with `mcp.method.name` (required), `gen_ai.tool.name`, `jsonrpc.request.id`, `mcp.session.id`, `mcp.protocol.version` and `rpc.response.status_code` on errors; metrics `mcp.client.operation.duration`, `mcp.server.operation.duration`, `mcp.client.session.duration` and `mcp.server.session.duration` (all `s`); and context propagation through `traceparent`, `tracestate` and `baggage` keys in the request's `params._meta` (chapter 20b).

### 29b.3.9 Schema URLs and convention versioning

A schema URL names the version of the conventions that a block of telemetry follows, and the file published at that URL describes, in machine-readable form, how names changed between versions. Its format (file format 1.1.0, development status) has three top-level keys: `file_format`, `schema_url`, and `versions`, which maps each version to the changes introduced in it. Each version can have sections `all`, `resources`, `spans`, `span_events`, `metrics` and `logs`, and each section lists transformations: `rename_attributes` everywhere, `rename_metrics` and `split` (turning one metric with an attribute into several metrics) under `metrics`, and `rename_events` under `span_events`, optionally limited to named spans, events or metrics. To upgrade data from version X to Y, a tool applies the `all` changes first, then the others, each list in order; to downgrade, it applies them in reverse.

An excerpt from the real 1.27.0 file, showing two renames you will meet in old data:

```yaml
file_format: 1.1.0
schema_url: https://opentelemetry.io/schemas/1.27.0
versions:
  1.27.0:
    all:
      changes:
        - rename_attributes:
            attribute_map:
              deployment.environment: deployment.environment.name
        - rename_attributes:
            attribute_map:
              gen_ai.usage.completion_tokens: gen_ai.usage.output_tokens
              gen_ai.usage.prompt_tokens: gen_ai.usage.input_tokens
```

**What a schema file cannot express.** Only renames and splits. A unit change is not a rename: the move from `http.server.duration` in milliseconds to `http.server.request.duration` in seconds needed instrumentations to emit both for a while, and every dashboard query had to change. Neither can a schema express a change of value (older `gen_ai.system` values such as `az.ai.inference` and `xai` became the `gen_ai.provider.name` values `azure.ai.inference` and `x_ai`) or of meaning (whether `input_tokens` includes cached tokens). And the GenAI conventions currently have no schema URL at all.

**How data is migrated across versions.**

1. *At the source:* instrumentations dual-emit during a migration (`OTEL_SEMCONV_STABILITY_OPT_IN` with a `/dup` value), so old and new dashboards both work for one retention period (45a.2).
2. *In the Collector, from schema files:* the contrib `schema` processor (alpha) translates incoming data to the schema versions you list in `targets`, can keep both names during a `migration`, can prefetch and cache schema files, and should not downgrade data by more than three versions.
3. *In the Collector, by hand:* where no schema exists, OTTL statements in the `transform` processor rename attributes. For GenAI data from libraries pinned to different releases:

   ```yaml
   processors:
     transform/genai_names:          # Collector contrib v0.161.0; run before any cost computation
       error_mode: ignore
       trace_statements:
         - set(span.attributes["gen_ai.provider.name"], span.attributes["gen_ai.system"]) where span.attributes["gen_ai.provider.name"] == nil and span.attributes["gen_ai.system"] != nil
         - set(span.attributes["gen_ai.usage.input_tokens"], span.attributes["gen_ai.usage.prompt_tokens"]) where span.attributes["gen_ai.usage.input_tokens"] == nil and span.attributes["gen_ai.usage.prompt_tokens"] != nil
         - set(span.attributes["gen_ai.usage.output_tokens"], span.attributes["gen_ai.usage.completion_tokens"]) where span.attributes["gen_ai.usage.output_tokens"] == nil and span.attributes["gen_ai.usage.completion_tokens"] != nil
         - set(span.attributes["gen_ai.usage.cache_write.input_tokens"], span.attributes["gen_ai.usage.cache_creation.input_tokens"]) where span.attributes["gen_ai.usage.cache_write.input_tokens"] == nil and span.attributes["gen_ai.usage.cache_creation.input_tokens"] != nil
         - delete_matching_keys(span.attributes, "^gen_ai\\.(system|usage\\.prompt_tokens|usage\\.completion_tokens|usage\\.cache_creation\\.input_tokens)$")
   ```

   The values of `gen_ai.provider.name` copied this way still need mapping where the old `gen_ai.system` values differ from the new well-known values; add one `set` per value that differs.

4. *At query time:* dashboards union old and new names (`or` in PromQL, `coalesce` in SQL) until the old data ages out.
5. *In the warehouse:* views that coalesce old and new keys, so historical analyses do not depend on which library produced the row.

Whatever the mechanism, record which version each dataset follows; the `schema_url` on the scope is the cheapest place, because it arrives with the data.

## 29b.4 Observability parameters: what to measure and how

### 29b.4.1 Latency, defined

**Response time** is what the caller experiences: queueing time (waiting for a worker, a connection, a GPU slot or a rate limit) plus service time (actually doing the work). People usually say "latency" for response time; be precise when it matters, because queueing time responds to capacity and service time to code. Measure response time where users feel it (45a.3 compares the client, the edge, the server and probes), and break it into service and queueing time where you can act on it.

**Which percentiles.** p50 is the typical experience; p90 and p95 describe most users; p99 is one request in a hundred, which a user who makes dozens of requests per session meets every session; p99.9 matters at high volume and under fan-out. Keep the maximum only as a debugging aid. A percentile is only as good as the number of samples behind it: at 10 requests per second, a 5-minute window holds 3,000 requests, so a 5-minute p99.9 rests on the slowest 3 of them. Compute rare percentiles over longer windows, or alert on the share of requests above a threshold instead (45a.3).

**Measuring it correctly.** Record durations in histograms whose bucket boundaries bracket your SLO thresholds; never average percentiles across instances or add them across hops (45b.4); and in load tests use a constant arrival rate. A generator that sends the next request only after the previous one returns sends fewer requests exactly when the system is slow, so it under-reports the tail (the "coordinated omission" problem).

### 29b.4.2 Tail latency under fan-out

If a request waits for N independent backends in parallel, and each backend is slower than its own p99 on 1% of calls, the share of requests that wait for at least one slow backend is 1 − 0.99^N. Dean and Barroso's "The Tail at Scale" (2013) uses the same arithmetic: with 100 servers whose p99 is one second, 63% of user requests take more than one second. Turned around, the per-backend percentile that must stay fast for the whole request to be fast 99% of the time is 0.99^(1/N):

| Backends (N) | Requests that hit at least one backend p99 | Backend percentile that must be fast for a 99% fast request |
|---|---|---|
| 1 | 1.0% | p99 |
| 5 | 4.9% | p99.8 |
| 10 | 9.6% | p99.9 |
| 20 | 18.2% | p99.95 |
| 50 | 39.5% | p99.98 |
| 100 | 63.4% | p99.99 |

Agents fan out in time rather than in space: a run with six sequential model calls, each with an independent 1% chance of being in its own slow tail, contains at least one slow call in 1 − 0.99^6 = 5.9% of runs, and because the steps are sequential the slow call's full delay lands on the user.

**Mitigations.** Timeouts slightly above the expected p99 of each dependency; *hedged requests*, which send a second copy only after the first has been outstanding longer than the p95, so at most about 5% of calls are duplicated (Dean and Barroso report a benchmark in which hedging cut the p99.9 for fetching 1,000 values from 1,800 ms to 74 ms while sending 2% more requests); and tied requests that cancel the slower copy. Hedging a model call has a price that hedging a key-value read does not: the duplicate repeats prefill and possibly output, and a canceled request has already consumed its input tokens, so hedge only short, idempotent calls on the time-to-first-token path, cancel the loser at the winner's first token, and check how your provider bills canceled streams. The HTTP conventions treat an intentional cancellation by the caller as not an error: leave the canceled span's status Unset and do not set `error.type`, or every hedge will look like a failure.

### 29b.4.3 Latency budgets per hop

A latency SLO is a budget that has to be divided among hops. For a retrieval-augmented chat endpoint whose SLO is a p95 time to first token of 2.0 seconds:

| Hop | Budget (p95) | Metric to watch |
|---|---|---|
| Edge, TLS and authentication | 60 ms | `http.server.request.duration` at the gateway |
| Query embedding | 120 ms | `gen_ai.client.operation.duration` where `gen_ai.operation.name` is `embeddings` |
| Vector search | 80 ms | duration of `retrieval` spans |
| Reranking | 150 ms | duration of the rerank span (custom) |
| Prompt assembly | 20 ms | self time of the request span |
| Model time to first token, cached prefix | 1,200 ms | `gen_ai.client.operation.time_to_first_chunk` |
| Network to the client | 70 ms | RUM |
| **Total** | **1,700 ms** | 300 ms of headroom |

Summing per-hop p95s is conservative, because independent hops rarely all hit their p95 on the same request, so the budget is safe but leaves money on the table; check the result against the measured end-to-end distribution. Give each hop a timeout a little above its budget, propagate an overall deadline so later hops know how much time is left (49.4), and allow a retry only when the remaining deadline can absorb it: a retried model call alone would spend the whole budget.

### 29b.4.4 Queueing and Little's law

**Queueing.** For one server with random arrivals and service times (the M/M/1 model), the mean response time is R = S / (1 − ρ), where S is the mean service time and ρ the utilization (arrival rate × S):

| Utilization ρ | Response time as a multiple of service time |
|---|---|
| 0.5 | 2× |
| 0.7 | 3.3× |
| 0.8 | 5× |
| 0.9 | 10× |
| 0.95 | 20× |

A tool service with a 50 ms service time answers in about 100 ms at half load and in about 500 ms at 90%, and its tail grows faster than its mean. Services with more variable service times, such as model servers whose requests range from 100 to 100,000 tokens, queue worse than this model. This is why saturation belongs next to latency on every dashboard: the latency curve turns upward well before utilization reaches 100%.

**Little's law.** In any stable system, averaged over a long enough window, the mean number of items in the system equals the arrival rate times the mean time each spends there: L = λ × W, whatever the distributions. Three uses:

1. *Concurrency you need.* 200 requests per second at a mean of 0.25 seconds means 50 requests in flight; a pool of 40 workers will queue.
2. *A free concurrency metric.* The rate of a duration histogram's `_sum` is total request-seconds per second, which is exactly the mean number of requests in flight. `sum(rate(http_server_request_duration_seconds_sum{job="support/support-agent"}[5m]))` should match `sum(http_server_active_requests{job="support/support-agent"})` (the development-status UpDownCounter); a gauge well above the computed value points at requests that hang without completing.
3. *Capacity in dollars.* 29b.5.3 prices the agent of 29b.6: 20 runs per second for 16.5 seconds each keeps 330 runs in flight.

### 29b.4.5 Latency for LLM calls and agents

| Quantity | Definition | Metric or attribute |
|---|---|---|
| Time to first token (TTFT), server side | Request received until the first output token is generated: queueing plus prefill | `gen_ai.server.time_to_first_token` (`s`) |
| Time to first chunk, client side | Request sent until the first streamed chunk arrives; adds network and provider front ends | `gen_ai.client.operation.time_to_first_chunk` (`s`); span attribute `gen_ai.response.time_to_first_chunk` |
| Time per output token (TPOT), or inter-token latency (ITL) | Mean time between output tokens after the first: the decode speed | `gen_ai.server.time_per_output_token` (`s`); client view `gen_ai.client.operation.time_per_output_chunk` |
| End-to-end call duration | Request sent until the last token | `gen_ai.client.operation.duration`, `gen_ai.server.request.duration` (`s`), the span's duration |
| Output tokens per second, per request | About 1 / ITL | Derived |
| Output tokens per second, system-wide | Total output tokens across requests per second: a capacity measure for model servers | `sum(rate(gen_ai_client_token_usage_sum{gen_ai_token_type="output"}[5m]))` |
| Time to first visible token | Until the user sees text: may follow hidden reasoning, tool-use blocks or an earlier agent step | RUM, or a custom attribute on the request span |
| Tool-call latency | One tool execution | `gen_ai.execute_tool.duration`, duration of `execute_tool` spans |
| Agent run duration and steps | One `invoke_agent` | `gen_ai.invoke_agent.duration`, `gen_ai.invoke_agent.inference_calls`, `gen_ai.invoke_agent.tool_calls` |

For one call, duration ≈ TTFT + (output tokens − 1) × ITL. The final-answer call in 29b.6 has a TTFT of 1.0 s, 420 output tokens and an ITL of 15 ms: 1.0 + 419 × 0.015 = 7.285 s, about 67 output tokens per second. The levers follow from the formula. TTFT grows with uncached input tokens (prefill) and with provider queueing; a cache read skips most of the prefill for the cached prefix. ITL depends on the model and on the server's load and batch size. Output length multiplies ITL, so for user-visible latency the cheapest fix is often a shorter answer; for an agent, the number of sequential steps multiplies everything.

**Retries.** Each attempt is its own span, and a retry's latency adds to the parent's. HTTP client spans carry `http.request.resend_count` (stable) from the second attempt on; count retries per dependency and alert when they exceed a retry budget (49.4), because retries during an outage multiply load. For LLM calls, a retry after the first token has been streamed to a user is visible to the user, so retry only before the first token.

Two queries worth having on the dashboard, valid for Prometheus 3.14 with the default translation strategy and classic histograms:

```promql
# p95 time to first chunk by model over 5 minutes
histogram_quantile(0.95,
  sum by (le, gen_ai_request_model) (rate(gen_ai_client_operation_time_to_first_chunk_seconds_bucket[5m])))

# Output tokens per second across the fleet, by model
sum by (gen_ai_request_model) (rate(gen_ai_client_token_usage_sum{gen_ai_token_type="output"}[5m]))
```

### 29b.4.6 Throughput, errors, saturation, availability and freshness

| Parameter | What to measure | Standard names (stability) | Notes |
|---|---|---|---|
| Throughput | Requests, messages, runs or tokens per second | Count of any duration histogram (`rate(..._count[5m])`); `messaging.client.consumed.messages` (development); output tokens from `gen_ai.client.token.usage` | Measure demand at the edge as well as served throughput: the gap is shed or queued load |
| Error rate | Failed ÷ valid, by error type | `error.type` on duration metrics (stable attribute; absent on success); `http.response.status_code`; span status | Decide what "valid" excludes (45a.3); count guardrail blocks and empty answers as errors where users see them as failures |
| Saturation | How full the tightest resource is | `container.cpu.time` and `container.memory.working_set` (release candidate), `http.server.active_requests` and `db.client.connection.count` (development); queue age; provider rate-limit headroom (custom, from response headers) | Saturation predicts latency; queue age beats queue depth (45a.2) |
| Availability | Good minutes ÷ minutes, or good requests ÷ valid requests | Derived from status codes and `error.type` | 45a.3 covers request-based and window-based SLIs and burn-rate alerts |
| Freshness | Age of the newest correctly processed data where it is consumed | No standard metric; a custom gauge of the last success time, read as `time() - acme_index_last_success_timestamp_seconds` | For RAG, the age of the index behind each answer is a correctness signal |

### 29b.4.7 Quality signals for AI systems

An AI system can be fast, available and wrong, so quality needs telemetry of its own:

- **Online evaluation scores**, from an LLM judge or a classifier on a sample of production traffic: groundedness (claims supported by the retrieved context), answer relevance, policy compliance, tool-call correctness.
- **Outcome signals**: task success (resolved without escalation), user feedback, re-asks within a session, human-handoff rate.
- **Safety signals**: guardrail block rate, refusal rate, PII-redaction hits.

Emit each judgment as a `gen_ai.evaluation.result` event (29b.3.4) carrying the response id and the span context, so a bad score links to its trace. Derive counts by `gen_ai.evaluation.name` and `gen_ai.evaluation.score.label` in the Collector (the count connector or `signal_to_metrics`) or in the backend; the **groundedness rate** is then passes divided by judged responses over the window. Mind the sample size: judging 2% of 20,000 daily answers yields 400 judgments a day, enough for a 95% interval of about ±2.9 points on a 90% pass rate, which supports a daily quality SLO but not an hourly page. Chapters 32 and 32b cover judges, and 45a.3 quality SLOs.

## 29b.5 Cost as a first-class telemetry signal

The semantic conventions record units consumed (tokens, seconds, bytes, requests), never money; chapter 29 notes that there is no standard cost attribute. Cost is a derived signal: the units on a span multiplied by the price that was valid when the span happened. Treat it like any other signal. Compute it the same way everywhere, version the prices, attach it to spans for debugging, aggregate it into unsampled metrics for dashboards and budgets, and reconcile it monthly with the invoice (chapter 47).

Custom attributes need a prefix that cannot collide with OpenTelemetry's namespaces: the naming guidance recommends a reverse domain name or an application-specific prefix and warns against reusing an OpenTelemetry namespace. This chapter uses `acme.` (`acme.cost.usd`, `acme.cost.price_table`, `acme.run.cost.usd`, `acme.tenant.id`, `acme.feature`). Avoid `app.`, which the conventions already use for client-application attributes such as `app.installation.id`.

### 29b.5.1 Cost per span

**LLM spans.** With prices per million tokens:

cost = [ (I − R − W) × p_input + R × p_cache_read + W × p_cache_write + O × p_output ] / 1,000,000

where I is `gen_ai.usage.input_tokens` (which, under the conventions, includes cached tokens), R is `gen_ai.usage.cache_read.input_tokens`, W is `gen_ai.usage.cache_write.input_tokens` (`cache_creation` in older libraries) and O is `gen_ai.usage.output_tokens`. The prices used in this chapter, Claude API list prices on 2 October 2026 per million tokens (chapter 31 explains the levers behind them):

| Model (API id) | Input | 5-minute cache write | 1-hour cache write | Cache read | Output |
|---|---|---|---|---|---|
| `claude-opus-5-5` | \$4.00 | \$5.00 | \$8.00 | \$0.20 | \$20.00 |
| `claude-sonnet-5-5` | \$2.00 | \$2.50 | \$4.00 | \$0.20 | \$10.00 |
| `claude-haiku-4-5-20251001` | \$1.00 | \$1.25 | \$2.00 | \$0.10 | \$5.00 |

The final-answer call of 29b.6 has I = 11,220, R = 6,000, W = 0 and O = 420, so it costs (5,220 × 2.00 + 6,000 × 0.20 + 420 × 10.00) / 1,000,000 = (10,440 + 1,200 + 4,200) / 1,000,000 = \$0.01584.

Six things make the formula wrong in practice:

1. **Provider semantics differ from the conventions.** Anthropic's `usage.input_tokens` counts only the tokens after the last cache breakpoint, and its total input is `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`; OpenAI-style usage reports the total, with cached tokens as a subset. The conventions use the total. A library that copies Anthropic's field straight into `gen_ai.usage.input_tokens` makes the uncached part come out too small, even negative. Check one span per instrumentation library against the raw usage object, clamp negatives to zero, and alert on them.
2. **Cache-write duration.** One-hour writes cost twice the input price and five-minute writes 1.25 times; the conventions have one write count, while Anthropic's usage object splits writes by duration (`cache_creation.ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens`). If you use both, record the split in custom attributes.
3. **Discounts and multipliers the span does not show.** The Batch API halves input and output prices; US-only inference (`inference_geo`) on Claude 4.6 and later models multiplies every token price by 1.1; fast mode doubles Claude Opus 5.5's list prices (\$8 input, \$40 output); priority tiers and committed-use discounts change the rate (chapter 31); and some providers charge more above a context-length threshold, which the current Claude models do not. Record the batch flag, the speed mode, the inference region and the route on the span.
4. **Per-use fees.** Server-side tools are billed outside tokens: web search at \$10 per 1,000 searches, so one search (\$0.01) costs about as much as a whole mid-size model call; code execution at \$0.05 per container-hour beyond 1,550 free hours per organization per month. They appear as usage counts in the provider response, not as tokens.
5. **Reasoning tokens.** `gen_ai.usage.reasoning.output_tokens` is already inside `output_tokens`; adding it again double-counts.
6. **Aggregate spans.** `invoke_agent` spans may carry the run's token totals; sum inference spans only.

**Compute spans.** Choose the method by how the resources are shared:

| Method | Formula | Right when | Example (AWS Fargate, Linux/x86, US East: \$0.000011244 per vCPU-second, \$0.000001235 per GB-second) |
|---|---|---|---|
| Exclusive | duration × (vCPU × vCPU rate + GB × memory rate) | The span had the resources to itself: a batch task, a serverless invocation, a GPU held for one request | A 90-second task with 4 vCPU and 16 GB: 90 × (0.000044976 + 0.00001976) = \$0.0058. Fargate bills a 1-minute minimum, so a 40-second task costs the same as a 60-second one |
| Shared by concurrency | duration × allocation rate ÷ mean concurrency | Asynchronous services that interleave many requests | The agent orchestrator, a task with 1 vCPU and 2 GB (\$0.000013714 per second) running 40 runs at once: 16.5 s × \$0.000013714 ÷ 40 = \$0.0000057 |
| Consumed | CPU-seconds used × vCPU rate (plus a memory share) | CPU-bound work in shared processes, when you can measure per-request CPU time | 0.35 CPU-seconds × \$0.000011244 = \$0.0000039 |
| Fleet (showback) | Fleet cost per hour ÷ requests per hour | Shared platforms; matches the bill because it includes idle capacity | A vector index on 3 tasks of 4 vCPU and 16 GB costs \$0.699 per hour; at 72,000 queries per hour, \$0.0000097 per query |
| Self-hosted GPU inference | GPU-hour price × duration ÷ 3,600 ÷ concurrent sequences in the batch; or fleet cost ÷ tokens generated | Batched model servers | Price unit: dollars per GPU-hour. Divide by the measured batch concurrency, not by 1, or every request looks as expensive as the whole GPU |

**Database and external API spans.** Multiply the units on the span by the unit price. DynamoDB on demand charges \$0.125 per million read request units, one unit per 4 KB for strongly consistent reads and half that for eventually consistent ones, so a Query returning 20 KB eventually consistently uses 2.5 units, or \$0.0000003; the AWS SDK instrumentation records `aws.dynamodb.consumed_capacity` (a string array of JSON, development) when the request asks for consumed capacity. Amazon SES charges \$0.10 per 1,000 emails on its à la carte pricing, \$0.0001 per send. Embeddings are token-priced like model calls: Voyage's `voyage-4-lite` lists \$0.02 per million tokens after the first 200 million free, so a 40-token query costs \$0.0000008.

**Storage and egress.** Priced per GB-month stored and per GB transferred (AWS gives 100 GB per month of free internet egress, aggregated across services). Attribute them to the spans that write or move the bytes, using a byte count recorded on the span. Egress is the item most often missed: a tool that downloads a 50 MB file across regions on every call can cost more than the model call that requested it.

### 29b.5.2 Roll-ups and attribution rules

**Per trace:** the sum over spans of the trace, counting tokens on inference spans only. **Per request:** the same, when one request is one trace; when a request triggers asynchronous work in other traces, follow the span links and add their cost. **Per feature and per tenant:** group by attributes propagated as baggage and copied onto spans by a baggage span processor (available in several SDKs' contrib packages), such as `acme.feature` and `acme.tenant.id`, or by resource attributes for per-service views. **Per successful task:** divide by successful runs, not all runs (chapter 31). Shared work needs explicit rules:

| Shared work | Rule | Why |
|---|---|---|
| Fan-out | Sum every child into the trace; when one worker or sub-agent serves several parent traces, split its cost across the links | Children are work the request caused |
| Retries | Count every attempt, and report the cost of failed attempts as retry overhead | You paid for them; a rising overhead is a reliability signal |
| Prompt-cache writes | Charge the writer (simple), or spread the write over the reads of that prefix within its lifetime (fair) | At feature level the two converge; at request level the first request in a window looks expensive |
| Response and semantic caches | Charge the lookup; record the avoided cost as its own metric | Savings are invisible otherwise |
| Batch jobs | Divide the job's cost by items or tokens and assign each share through the link to the item's originating trace or tenant | Embedding backfills and nightly evaluations are real cost of a feature |
| Shared platforms (vector database, gateway, Collector) | Allocate by usage share per period: queries, CPU-seconds or bytes | Matches how the bill grows |
| Idle provisioned capacity (provisioned throughput, reserved GPUs) | Allocate the used share by tokens and report the idle remainder as its own line | Hiding idle capacity in per-request cost makes efficient features look expensive |
| Failed runs | Keep them in cost per run, and also report cost per successful task | A 30% failure rate with retries costs 1.4 times what cost per run suggests (chapter 31) |

### 29b.5.3 Latency cost

**What latency costs the business.** Few controlled public studies exist, and none that could be verified for this chapter is about chat or agents.

- Google injected 100 to 400 ms of extra delay into search results for some users in 2009: searches per user fell by 0.2% to 0.6% over four to six weeks, the effect grew the longer users were exposed, and users who had seen a 400 ms delay for six weeks still searched 0.21% less during the five weeks after it was removed.
- Deloitte, commissioned by Google, analyzed mobile sites of retail, travel, luxury and lead-generation brands in Europe and the US (*Milliseconds Make Millions*, March 2020): a 0.1-second improvement in load-time metrics went with 8.4% more retail conversions, 9.2% higher retail average order value and 10.1% more travel conversions. The study is correlational and about page loads.

For conversational AI, run the experiment yourself, the way Google did: add delay for a random slice of users, then measure task completion, abandonment (streams canceled before the first token) and return rate, and turn the effect into dollars per 100 ms. Latency work then has a price you can compare with token savings.

**What latency costs the infrastructure.** By Little's law, the capacity you hold is arrival rate × time held, and every second a request is held is a second of whatever is priced by time. The support agent in 29b.6 at a peak of 20 runs per second for 16.5 seconds keeps 330 runs in flight; orchestrator tasks with 1 vCPU and 2 GB handle 40 concurrent runs each, so the peak needs 9 tasks, and cutting the run to 12.9 seconds (29b.6) brings that to about 258 runs and 7 tasks, a saving of two tasks or about \$72 a month at Fargate prices. The orchestrator is cheap; the same arithmetic is expensive where capacity is: a self-hosted model server holds a batch slot for the whole generation, so at 120 calls per second of 2.5 seconds each it holds 300 sequences, and at 64 concurrent sequences per replica that is 5 GPU replicas, while calls of 2.0 seconds (shorter answers) need 240 sequences and 4 replicas, one GPU-replica-hour saved every hour. Provider concurrency limits, provisioned throughput and database connection pools obey the same law. For pay-per-token APIs, latency costs little infrastructure money and a lot of user attention.

### 29b.5.4 Where to compute cost: application, Collector or warehouse

| | Application | Collector | Warehouse |
|---|---|---|---|
| How | A price table in code or configuration; compute from the provider's usage object when each call returns; set the cost on the span; accumulate per run | OTTL in the `transform` processor computes cost from span attributes; `signal_to_metrics` (alpha) or the `sum` connector (alpha) turns it into metrics before sampling | Join exported spans with a versioned price table |
| Strengths | Real-time budgets and per-run caps (stop the agent at \$0.50); sees provider-specific detail such as the cache-write split, batch and server-side tools | One place for every service and language; runs before sampling, so metrics are unbiased; no redeploys | Recomputable when prices, discounts or contracts change; auditable; joins with invoices, tenants and contracts |
| Weaknesses | Every service needs the table, and a price change needs a deploy | Prices live in Collector configuration; OTTL has no lookup tables, so one statement per model; a value stamped at ingest is never recomputed | Sees only what was exported (sampled, unless you export inference spans separately); hours of delay; no enforcement |
| Use it for | Budgets and guardrails | Dashboards and alerts | Finance, showback, chargeback and reconciliation |

Use all three, consistently: the application estimates for enforcement, the Collector stamps `acme.cost.usd` with `acme.cost.price_table` and emits unsampled cost metrics, and the warehouse recomputes the authoritative figure from token counts and reconciles it with the invoice.

**In the application.** A function the agent loop calls after every model call (Anthropic Python SDK usage fields; OpenTelemetry Python API 1.45). Instrumentation libraries usually set the `gen_ai.usage.*` attributes themselves; the conversion is shown because it is the step people get wrong.

```python
# llm_cost.py: cost of one Claude call from the Messages API usage object.
from opentelemetry import trace

PRICE_TABLE = "2026-10-01"
# USD per million tokens: input, 5-minute cache write, 1-hour cache write, cache read, output.
PRICES = {
    "claude-sonnet-5-5": (2.00, 2.50, 4.00, 0.20, 10.00),
    "claude-haiku-4-5-20251001": (1.00, 1.25, 2.00, 0.10, 5.00),
}

def record_llm_cost(model: str, usage) -> float:
    p_in, p_write_5m, p_write_1h, p_read, p_out = PRICES[model]
    read = usage.cache_read_input_tokens or 0
    write = usage.cache_creation_input_tokens or 0
    write_1h = (usage.cache_creation.ephemeral_1h_input_tokens or 0) if usage.cache_creation else 0
    cost = (usage.input_tokens * p_in                      # Anthropic: tokens after the last breakpoint
            + (write - write_1h) * p_write_5m + write_1h * p_write_1h
            + read * p_read
            + usage.output_tokens * p_out) / 1_000_000
    span = trace.get_current_span()
    # The conventions count cached tokens inside input_tokens; Anthropic's usage object does not.
    span.set_attribute("gen_ai.usage.input_tokens", usage.input_tokens + write + read)
    span.set_attribute("gen_ai.usage.cache_read.input_tokens", read)
    span.set_attribute("gen_ai.usage.cache_write.input_tokens", write)
    span.set_attribute("gen_ai.usage.output_tokens", usage.output_tokens)
    span.set_attribute("acme.cost.usd", cost)
    span.set_attribute("acme.cost.price_table", PRICE_TABLE)
    return cost
```

The loop adds each call's return value to a running total, stops the run when the total passes its budget, and sets the total as `acme.run.cost.usd` on the `invoke_agent` span when the run ends. That one attribute is what makes trace-level cost cheap to query, to alert on and to tail-sample on (an `ottl_condition` policy that keeps every run above \$0.10).

**In the Collector.** Changes to the gateway in 45b.2, for Collector contrib v0.161.0: the processors and connectors below are added, and the pipelines replace its trace and metrics pipelines (its receivers, `memory_limiter`, `transform/normalize`, `tail_sampling`, `batch`, `span_metrics` and exporters stay as they are). A forward connector runs the cost transformation once and fans the costed spans out to an unsampled metrics pipeline and a sampled storage pipeline. Prices are the list prices above in dollars per token, with five-minute cache writes assumed.

```yaml
processors:
  transform/llm_cost:
    error_mode: ignore
    trace_statements:
      # Working copies of the cache counts: 0 when absent; the pre-v1.42 cache_creation name is accepted.
      - set(span.attributes["acme.tmp.cache_read"], 0) where span.attributes["gen_ai.usage.input_tokens"] != nil
      - set(span.attributes["acme.tmp.cache_read"], span.attributes["gen_ai.usage.cache_read.input_tokens"]) where span.attributes["gen_ai.usage.cache_read.input_tokens"] != nil
      - set(span.attributes["acme.tmp.cache_write"], 0) where span.attributes["gen_ai.usage.input_tokens"] != nil
      - set(span.attributes["acme.tmp.cache_write"], span.attributes["gen_ai.usage.cache_creation.input_tokens"]) where span.attributes["gen_ai.usage.cache_creation.input_tokens"] != nil
      - set(span.attributes["acme.tmp.cache_write"], span.attributes["gen_ai.usage.cache_write.input_tokens"]) where span.attributes["gen_ai.usage.cache_write.input_tokens"] != nil
      # claude-sonnet-5-5: input 2.00, cache read 0.20, cache write 2.50, output 10.00 per million tokens
      - set(span.attributes["acme.cost.usd"], (Double(span.attributes["gen_ai.usage.input_tokens"]) - Double(span.attributes["acme.tmp.cache_read"]) - Double(span.attributes["acme.tmp.cache_write"])) * 0.000002 + Double(span.attributes["acme.tmp.cache_read"]) * 0.0000002 + Double(span.attributes["acme.tmp.cache_write"]) * 0.0000025 + Double(span.attributes["gen_ai.usage.output_tokens"]) * 0.00001) where span.attributes["gen_ai.operation.name"] == "chat" and span.attributes["gen_ai.provider.name"] == "anthropic" and IsMatch(span.attributes["gen_ai.response.model"], "^claude-sonnet-5-5") and span.attributes["gen_ai.usage.output_tokens"] != nil
      # claude-haiku-4-5: input 1.00, cache read 0.10, cache write 1.25, output 5.00 per million tokens
      - set(span.attributes["acme.cost.usd"], (Double(span.attributes["gen_ai.usage.input_tokens"]) - Double(span.attributes["acme.tmp.cache_read"]) - Double(span.attributes["acme.tmp.cache_write"])) * 0.000001 + Double(span.attributes["acme.tmp.cache_read"]) * 0.0000001 + Double(span.attributes["acme.tmp.cache_write"]) * 0.00000125 + Double(span.attributes["gen_ai.usage.output_tokens"]) * 0.000005) where span.attributes["gen_ai.operation.name"] == "chat" and span.attributes["gen_ai.provider.name"] == "anthropic" and IsMatch(span.attributes["gen_ai.response.model"], "^claude-haiku-4-5") and span.attributes["gen_ai.usage.output_tokens"] != nil
      - set(span.attributes["acme.cost.price_table"], "2026-10-01") where span.attributes["acme.cost.usd"] != nil
      - delete_key(span.attributes, "acme.tmp.cache_read")
      - delete_key(span.attributes, "acme.tmp.cache_write")
  deltatocumulative: {}           # signal_to_metrics emits deltas; Prometheus-compatible backends want cumulative

connectors:
  forward/costed: {}
  signal_to_metrics:
    spans:
      - name: acme.llm.cost
        description: Model spend computed in the Collector from token counts
        unit: "{USD}"
        conditions:
          - span.attributes["acme.cost.usd"] != nil
        attributes:
          - key: gen_ai.request.model
          - key: acme.feature
            default_value: unknown
        sum:
          value: span.attributes["acme.cost.usd"]
          monotonic: true
      - name: acme.agent.run.cost
        description: Cost of one agent run, set by the agent loop on its invoke_agent span
        unit: "{USD}"
        conditions:
          - span.attributes["acme.run.cost.usd"] != nil
        attributes:
          - key: gen_ai.agent.name
        histogram:
          buckets: [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5]
          value: span.attributes["acme.run.cost.usd"]

service:
  pipelines:
    traces/in:                    # every span passes here once
      receivers: [otlp]
      processors: [memory_limiter, transform/normalize, transform/genai_names, transform/llm_cost]
      exporters: [forward/costed]
    traces/metrics:               # unsampled: RED and cost metrics
      receivers: [forward/costed]
      exporters: [span_metrics, signal_to_metrics]
    traces/sampled:               # sampled for storage, as in 45b.2
      receivers: [forward/costed]
      processors: [tail_sampling, batch]
      exporters: [otlp_grpc/tempo]
    metrics:
      receivers: [otlp, span_metrics, signal_to_metrics]
      processors: [memory_limiter, transform/normalize, deltatocumulative, batch]
      exporters: [otlp_http/mimir]
```

Notes on why it is written this way. OTTL refuses arithmetic that mixes integers and floats, so every token count passes through `Double()`; the working copies avoid arithmetic on a missing attribute, and with `error_mode: ignore` a malformed span loses its cost instead of the batch being dropped. `IsMatch` returns false for a missing model, so unpriced models simply get no cost: alert on inference spans without `acme.cost.usd` (29b.5.6), because a new model id is the most common way cost tracking silently breaks. `signal_to_metrics` produces delta sums, which the `deltatocumulative` processor converts before the Prometheus-compatible exporter. The connector keeps all resource attributes by default, so `job` and `instance` still identify the service, and it adds `signal_to_metrics.service.instance.id` to the resource so that each gateway replica writes its own stream. Prometheus and Mimir leave that attribute out of the series (it lands on `target_info`), so on a gateway with several replicas the replicas' cost series collide (29b.2, single-writer principle). Either promote the attribute to a label (`promote_resource_attributes` in Prometheus, `-distributor.otel-promote-resource-attributes` in Mimir) and let queries sum it away, as the `sum by (job)` queries in 29b.5.6 do, or run `transform/llm_cost` and `signal_to_metrics` in the node agents, where every span of a pod passes through one Collector (45b.2). In Prometheus the metrics arrive as `acme_llm_cost_total` and `acme_agent_run_cost_bucket`.

**In the warehouse.** Section 29b.6 gives the SQL: spans exported to ClickHouse joined with a versioned price table through an `ASOF JOIN`, so each span is priced at the rate valid when it ran.

### 29b.5.5 Sampling and cost metrics

Sampling changes what stored traces represent, and cost computed from stored traces inherits the distortion.

- **Head sampling** at probability *p* without weighting under-reports totals by a factor of 1/*p*: at 10%, the trace store holds a tenth of the spend.
- **Tail sampling** is worse, because it is biased on purpose. Take 100,000 runs: 95,000 ordinary runs at \$0.03 and 5,000 expensive ones at \$0.30. A tail sampler that keeps every expensive run and 5% of the rest stores 4,750 + 5,000 = 9,750 traces. Their unweighted mean is (4,750 × 0.03 + 5,000 × 0.30) / 9,750 = \$0.168, almost four times the true mean of (2,850 + 1,500) / 100,000 = \$0.0435, while their total, \$1,642.50, is 38% of the true \$4,350.

Three ways to get it right:

1. **Compute cost metrics before sampling**, as in the Collector configuration above: the same principle as deriving RED metrics from 100% of spans (45b.2).
2. **Weight each stored trace by its adjusted count**, 1/*p*. Weighting the example's ordinary traces by 20 gives (4,750 × 20 × 0.03 + 5,000 × 0.30) / (4,750 × 20 + 5,000) = \$0.0435, the true mean. The probability has to travel with the data, as the `th` threshold in `tracestate`. Samplers that implement OpenTelemetry's probability-sampling specification (available in some SDKs) and the Collector's `probabilistic_sampler` processor write it. The `tail_sampling` processor does so behind the `processor.tailsamplingprocessor.usetracestate` feature gate, writing the smallest threshold among the policies that voted to keep the trace; filter-style policies such as `status_code` or a cost condition count as `th:0`, so in the example an expensive run carries an adjusted count of 1 and a baseline run 20, exactly the weights needed. The `processor.tailsamplingprocessor.recordpolicy` gate adds `tailsampling.policy`, `tailsampling.composite_policy` and `tailsampling.cached_decision` attributes, so you know why each trace was kept. Three things can read the threshold: the `signal_to_metrics` connector's `AdjustedCount()` function (for example as a histogram's `count`), which matters wherever metrics are computed after sampling, such as in a Collector behind head sampling in the SDK; Tempo 3.1's experimental `with(extrapolate=true)` hint for TraceQL metrics (45b.8); and your own SQL. In ClickHouse, the adjusted count of a span exported by the ClickHouse exporter is:

   ```sql
   -- th holds up to 14 hex digits of a 56-bit rejection threshold; p = 1 - threshold / 2^56.
   -- No threshold gives 1, which is right only if the trace was not sampled by an unrecorded policy.
   1 / (1 - reinterpretAsUInt64(reverse(unhex(rightPad(
           extract(TraceState, 'ot=(?:[^,]*;)?th:([0-9a-f]{1,14})'), 14, '0')))) / pow(2, 56)) AS adjusted_count
   ```

   For `ot=th:c` the expression yields 4.

3. **Export inference spans unsampled.** They are a small share of all spans and carry nearly all of the cost, so route spans with a `gen_ai.operation.name` to the warehouse before tail sampling (without content) and sample the rest.

### 29b.5.6 Cost attributes, dashboards and alerts

On spans: `acme.cost.usd` (double) and `acme.cost.price_table` (string) on every priced span, `acme.run.cost.usd` on `invoke_agent`, and the attribution keys `acme.tenant.id` and `acme.feature`. On metrics: `acme.llm.cost` by model and feature, and the `acme.agent.run.cost` histogram. A tenant label on a cost metric is acceptable while tenants number in the hundreds; beyond that, roll tenants up in the warehouse (29b.5.7 shows what a tenant label costs).

A cost dashboard worth having shows: cost per run (mean, p95, p99) by agent; spend per hour by model, feature and tenant; cost per successful task; the cache-hit ratio (cache-read tokens over input tokens, from spans or a derived metric); retry overhead; and the count of inference spans with no price. Queries for Prometheus 3.14 with the default translation strategy:

```promql
# Model spend per completed agent run over the last hour, by service
sum by (job) (rate(acme_llm_cost_total[1h]))
/
sum by (job) (rate(gen_ai_invoke_agent_duration_seconds_count[1h]))

# p95 cost of one run
histogram_quantile(0.95, sum by (le, job) (rate(acme_agent_run_cost_bucket[1h])))

# Spend rate relative to the same hour last week
sum by (job) (rate(acme_llm_cost_total[1h]))
/
sum by (job) (rate(acme_llm_cost_total[1h] offset 1w))
```

Alerting rules in the Prometheus 3.x format. Cost alerts are tickets, not pages, unless a runaway loop can spend real money within the hour; the hard stop belongs in the gateway or the agent loop, not in an alert (chapter 31).

```yaml
groups:
  - name: llm-cost
    rules:
      - alert: AgentRunCostP95High
        expr: histogram_quantile(0.95, sum by (le, job) (rate(acme_agent_run_cost_bucket[1h]))) > 0.10
        for: 30m
        labels:
          severity: ticket
        annotations:
          summary: "p95 cost per agent run above $0.10 for 30 minutes in {{ $labels.job }}"
      - alert: LLMSpendDoubledWeekOverWeek
        expr: |
          sum by (job) (rate(acme_llm_cost_total[1h]))
            > 2 * sum by (job) (rate(acme_llm_cost_total[1h] offset 1w))
        for: 1h
        labels:
          severity: ticket
        annotations:
          summary: "Model spend in {{ $labels.job }} is more than twice last week's rate"
```

The p95 threshold of 0.10 is a bucket boundary, so the alert does not depend on interpolation inside a bucket. The unpriced-span check runs best in the warehouse (`unpriced_model_spans` in 29b.6), or as a `signal_to_metrics` counter whose condition selects spans that have `gen_ai.usage.input_tokens` but no `acme.cost.usd`.

### 29b.5.7 The cost of observability itself

| Cost driver | Billed per | Grows with | Main control |
|---|---|---|---|
| Active metric series | 1,000 series per month | Label cardinality and churn | Drop or aggregate labels; native histograms; recording rules (45a.2) |
| Samples (data points) | Points per minute or per second | Series × collection frequency | Longer intervals for slow-moving metrics |
| Log volume | GB ingested; events indexed | Traffic × verbosity | Drop debug logs and health checks at the source; sample; log patterns |
| Spans | GB ingested; spans indexed; spans | Traffic × spans per request | Head or tail sampling; drop probes; attribute limits |
| Captured content | GB | Tokens per request, which grow quadratically in agent loops (chapter 31) | Store by reference (prompt name and version) or upload through the completion hook; short retention |
| Retention | GB-month | Days kept | Tiered retention: content days, traces weeks, metrics 13 months |
| Queries | Per query or per GB scanned, on some backends | Dashboards, alerts, ad hoc work | Recording rules, caching, sensible refresh rates |
| Hosts | Host per month | Fleet size | Fewer, larger nodes; agentless collection where it is enough |
| Egress to a vendor | GB transferred | Everything above | Filter and compress at the edge |

List prices on 2 October 2026, for orientation:

| Vendor | Item | List price |
|---|---|---|
| Grafana Cloud Pro | Metrics | From \$6.50 per 1,000 active series per month; 10,000 series included with the \$19 monthly platform fee; 13 months' retention |
| Grafana Cloud Pro | Logs, traces, profiles | From \$0.05 per GB processed + \$0.40 per GB written + \$0.10 per GB retained (\$0.55 per GB for data that is all three); 50 GB per month included for each; 30 days' retention |
| Datadog | APM | \$31 per host per month (annual billing) |
| Datadog | Spans | Ingestion \$0.10 per GB beyond the allotment; indexed spans \$1.70 per million at 15-day retention (annual) |
| Datadog | Logs | Ingestion \$0.10 per GB; indexing \$1.70 per million events at 15-day retention (annual); Flex Logs storage \$0.05 per million events |
| Datadog | Custom metrics | \$5 per 100 per month |
| Datadog | LLM Observability (listed with Agent Observability) | \$3.50 per 10,000 spans per month at 15-day retention (annual) |

Three worked numbers for an agent platform at 1 million runs a month, using the run in 29b.6 (14 spans, \$0.0452 of model spend per run, \$45,165 a month):

- **Per-span pricing.** At \$3.50 per 10,000 spans, observing every span of every run costs 14 × \$0.00035 = \$0.0049 per run, \$4,900 a month, 10.8% of the model spend, if all 14 spans are billable; check which span kinds your contract counts. Sampling 10% of runs (all errors and expensive runs plus a baseline) brings it under 2%.
- **Captured content.** The six model calls send 41,930 input tokens and receive 805 output tokens; at about 4 characters per token (OpenAI's rule of thumb for English), full content capture adds about 171 KB per run to about 17 KB of span metadata (14 spans at an assumed 1.2 KB each). At 1 million runs that is about 188 GB a month, \$75.90 at Grafana Cloud's \$0.55 per GB after the 50 GB included: cheap in money, expensive in privacy review, which is why content belongs in a store with short retention and strict access (chapter 29).
- **Cardinality.** `gen_ai.client.token.usage` as a classic histogram has 17 series per label set; with 2 models, 2 token types and 1 operation on 30 pods, that is 4 × 30 × 17 = 2,040 series, \$13.26 a month at list price. Add `acme.tenant.id` with 500 active tenants and it becomes 1,020,000 series, \$6,630 a month for one metric. Keep the tenant on spans and in the warehouse, not on metric labels.

The controls are the same as for any telemetry (45a.2 lists the failure modes): sample at the source and in the tail, aggregate before storing, drop labels nobody queries, capture content by reference, and tier retention.

## 29b.6 Worked example: one agent run, costed and timed

### The run

The `billing-support` agent of the `support-agent` service (namespace `support`) receives: "I was charged twice for my October invoice; please fix it." The run makes six model calls, three tool calls, one vector search and one database query:

- a router on Claude Haiku 4.5 classifies the request;
- a loop on Claude Sonnet 5.5 calls `search_kb` (a query embedding, then a vector search over `kb-articles`), `get_billing_history` (a DynamoDB query) and `send_email` (Amazon SES), then writes the answer;
- a guard on Claude Haiku 4.5 checks the answer before it is sent.

**Caching.** The 6,000-token system prompt and tool definitions form a cached prefix shared by every conversation in the workspace, so it stays warm and each loop call reads it. The transcript that grows after it is not cached: that is the configuration under test. Claude Haiku 4.5 cannot cache prompts shorter than 4,096 tokens, so the router (1,200 tokens) and the guard (2,220) pay the full input price; Claude Sonnet 5.5's minimum is 512 tokens.

**Assumptions for everything else.** The vector index runs on 3 Fargate tasks with 4 vCPU and 16 GB each and serves 20 queries per second on average; the orchestrator runs 40 concurrent runs per Fargate task with 1 vCPU and 2 GB; DynamoDB is on demand; SES is on à la carte pricing. Claude Sonnet 5.5 streams at 15 ms per output token and Claude Haiku 4.5 at 8 ms, the times to first token are those given below the table, and the orchestrator adds 10 ms between steps. Prices are the list prices of 29b.5.1.

### The spans

| # | Span | Kind | Start (s) | Duration (s) | Input tokens (cache read) | Output tokens | Cost (USD) |
|---|---|---|---|---|---|---|---|
| 1 | `POST /v1/support/messages` | SERVER | 0.000 | 16.534 | | | |
| 2 | `invoke_agent billing-support` | INTERNAL | 0.040 | 16.484 | | | 0.0000057 (orchestrator compute) |
| 3 | `chat claude-haiku-4-5-20251001` (router) | CLIENT | 0.045 | 0.412 | 1,200 (0) | 15 | 0.001275 |
| 4 | `chat claude-sonnet-5-5` (step 1) | CLIENT | 0.467 | 2.085 | 6,900 (6,000) | 90 | 0.003900 |
| 5 | `execute_tool search_kb` | INTERNAL | 2.562 | 0.170 | | | |
| 6 | `embeddings voyage-4-lite` | CLIENT | 2.567 | 0.110 | 40 | | 0.0000008 |
| 7 | `retrieval kb-articles` (vector search) | CLIENT | 2.677 | 0.045 | | | 0.0000097 |
| 8 | `chat claude-sonnet-5-5` (step 2) | CLIENT | 2.742 | 2.485 | 9,390 (6,000) | 110 | 0.009080 |
| 9 | `execute_tool get_billing_history` | INTERNAL | 5.237 | 0.060 | | | |
| 10 | `DynamoDB.Query` (database) | CLIENT | 5.257 | 0.018 | | | 0.0000003 |
| 11 | `chat claude-sonnet-5-5` (step 3) | CLIENT | 5.307 | 3.335 | 11,000 (6,000) | 160 | 0.012800 |
| 12 | `execute_tool send_email` (SES call inside) | INTERNAL | 8.652 | 0.240 | | | 0.0001000 |
| 13 | `chat claude-sonnet-5-5` (final answer) | CLIENT | 8.902 | 7.285 | 11,220 (6,000) | 420 | 0.015840 |
| 14 | `chat claude-haiku-4-5-20251001` (guard) | CLIENT | 16.197 | 0.322 | 2,220 (0) | 10 | 0.002270 |

How the input grows: step 1 sends the 6,000-token prefix plus 900 tokens of user message and customer context; step 2 adds step 1's 90-token tool call and the 2,400-token search result; step 3 adds 110 tokens of tool call and 1,500 tokens of billing rows; the final answer adds 160 + 60 (the email confirmation). Every step re-sends the uncached part of the transcript, 900, 3,390, 5,000 and then 5,220 tokens: the quadratic growth described in chapter 31.

How the durations arise: each model span takes TTFT + (output tokens − 1) × ITL. Step 1 is 0.75 + 89 × 0.015 = 2.085 s, step 2 is 0.85 + 109 × 0.015 = 2.485 s, step 3 is 0.95 + 159 × 0.015 = 3.335 s, the final answer 1.00 + 419 × 0.015 = 7.285 s, the router 0.30 + 14 × 0.008 = 0.412 s and the guard 0.25 + 9 × 0.008 = 0.322 s. Inside `search_kb`, the embedding (0.110 s) and the vector search (0.045 s) run one after the other, with 15 ms of tool overhead.

### Trace totals

**Cost per run: \$0.04528.**

- Model calls: \$0.045165, 99.74% of the run. Uncached input is \$0.03244 of it (71.8%: 3,420 Haiku tokens at \$1 and 14,510 Sonnet tokens at \$2 per million), cache reads \$0.00480 (10.6%: 24,000 tokens at \$0.20) and output \$0.007925 (17.5%).
- Tools and data: \$0.0001108 (SES \$0.0001, vector search \$0.0000097, embedding \$0.0000008, DynamoDB \$0.0000003).
- Orchestrator compute: \$0.0000057.
- At 1 million runs a month: about \$45,280.

**Latency: 16.534 s end to end.**

| Component | Seconds | Share |
|---|---|---|
| Output generation in the six model calls | 11.824 | 71.5% |
| of which the final answer | 6.285 | 38.0% |
| Time to first token in the six model calls | 4.100 | 24.8% |
| Tools: embedding, vector search, database, SES and tool overhead | 0.470 | 2.8% |
| Orchestration gaps and HTTP handling | 0.140 | 0.8% |

**The critical path.** When children run in parallel, the critical path is the chain of spans that decides when the root ends: start at the root, step into the child that finished last, and repeat; a span off that chain can get slower, up to its slack, without changing the end-to-end time. This agent is sequential, so every span is on the critical path and the end-to-end time is the sum of the steps plus the gaps. The user sees nothing for 16.5 seconds, because the guard runs on the complete answer before anything is sent.

Two facts decide what to fix. The money is in input tokens (72% of model spend is uncached input), and the time is in output tokens (71.5% of the run is generation). The non-model spans are 0.26% of the cost and 2.8% of the time, so tuning the vector index or the database would be wasted effort.

### What to optimize first

| Change | Model cost per run | End to end | First visible token | Risk |
|---|---|---|---|---|
| Baseline | \$0.0452 | 16.53 s | 16.53 s | |
| 1. Cache the transcript: a cache breakpoint at the end of each loop request | \$0.0309 (−31.5%) | Slightly lower (less prefill; not modeled) | 16.53 s | None for quality; a configuration change |
| 2. Stream the final answer and run the guard incrementally | \$0.0452 | 16.53 s | 9.90 s | The guard must be able to stop a stream (chapter 53b) |
| 3. Request both lookups in step 1 (parallel tool calls), which removes step 2 | \$0.0370 (−18%) | 15.47 s (−1.07 s) | 8.84 s together with change 2 | Needs an evaluation run |
| 4. A 250-token final answer instead of 420 | \$0.0433 (−4%) | 13.98 s (−2.55 s) | Unchanged | A product decision; needs an evaluation run |
| All four | \$0.0271 (−40%) | 12.92 s (−22%) | 8.84 s (−47%) | |

How change 1 works. With a breakpoint at the end of each loop request, the new part of the transcript is written to the cache once at 1.25 times the input price and read by the next step at a tenth of it:

| Call | Cache read | Cache write | Uncached | Output | Cost before | Cost after |
|---|---|---|---|---|---|---|
| Step 1 | 6,000 | 900 | 0 | 90 | \$0.003900 | \$0.004350 |
| Step 2 | 6,900 | 2,490 | 0 | 110 | \$0.009080 | \$0.008705 |
| Step 3 | 9,390 | 1,610 | 0 | 160 | \$0.012800 | \$0.007503 |
| Final answer (no breakpoint, because nothing follows) | 11,000 | 0 | 220 | 420 | \$0.015840 | \$0.006840 |
| Loop total | | | | | \$0.041620 | \$0.027398 |

Step 1 gets slightly more expensive, because it pays for the write, and every later step gets cheaper; the run saves \$0.0142, about \$14,200 a month at 1 million runs, for a configuration change. Change 3 alters the trace's shape: step 1 emits two tool calls (190 output tokens instead of 90, so it takes 3.585 s), the two tools run in parallel (0.170 s, the longer of the two), and step 2 disappears. Change 2 is as much a safety design question as a latency one. Changes 3 and 4 alter what the model sees or says, so they must pass the evaluation set like any prompt change (chapter 32).

### The same analysis as queries

**TraceQL (Tempo 3.1).** These need `acme.cost.usd`, which the Collector in 29b.5.4 adds before the spans are stored. Each query stands alone.

1. Runs whose model calls cost more than \$0.04:
   ```traceql
   { resource.service.name = "support-agent" && span.gen_ai.operation.name = "chat" } | sum(span.acme.cost.usd) > 0.04
   ```
2. Runs with more than four model calls below the agent span:
   ```traceql
   { span.gen_ai.operation.name = "invoke_agent" } >> { span.gen_ai.operation.name = "chat" } | count() > 4
   ```
3. p95 duration by operation, as a time series:
   ```traceql
   { resource.service.name = "support-agent" && span.gen_ai.operation.name =~ "chat|execute_tool|embeddings|retrieval" } | quantile_over_time(span:duration, .95) by (span.gen_ai.operation.name)
   ```
4. Model spend by model, as a time series:
   ```traceql
   { resource.service.name = "support-agent" && span.gen_ai.operation.name = "chat" } | sum_over_time(span.acme.cost.usd) by (span.gen_ai.request.model)
   ```

TraceQL metrics run over stored spans, so under sampling query 4 shows relative spend, not totals (29b.5.5). Take totals from `acme_llm_cost_total`, or, if every sampler wrote its threshold into `tracestate`, append Tempo 3.1's experimental `with(extrapolate=true)` to weight each span by its adjusted count.

**SQL (ClickHouse).** The queries use syntax from the current ClickHouse documentation (October 2026) and run over the `otel_traces` table that the Collector contrib ClickHouse exporter (v0.161.0) creates. That schema keeps span attributes in `SpanAttributes`, a `Map(LowCardinality(String), String)`, so numbers arrive as strings, and `Duration` in nanoseconds. Prices live in versioned tables, so a price change is a new row and never an update:

```sql
CREATE TABLE llm_prices
(
    model                String,
    valid_from           DateTime,
    price_table          String,
    input_per_mtok       Float64,
    cache_read_per_mtok  Float64,
    cache_write_per_mtok Float64,  -- 5-minute writes
    output_per_mtok      Float64
)
ENGINE = MergeTree
ORDER BY (model, valid_from);

INSERT INTO llm_prices VALUES
    ('claude-sonnet-5-5',         '2026-10-01 00:00:00', '2026-10-01', 2.00, 0.20, 2.50, 10.00),
    ('claude-haiku-4-5-20251001', '2026-10-01 00:00:00', '2026-10-01', 1.00, 0.10, 1.25,  5.00),
    ('voyage-4-lite',             '2026-10-01 00:00:00', '2026-10-01', 0.02, 0.00, 0.00,  0.00);

CREATE TABLE span_unit_prices
(
    span_name    String,
    usd_per_span Float64,
    basis        String
)
ENGINE = MergeTree
ORDER BY span_name;

INSERT INTO span_unit_prices VALUES
    ('retrieval kb-articles',   0.0000097, 'fleet: $0.699 per hour / 72,000 queries per hour'),
    ('DynamoDB.Query',          0.0000003, '2.5 read request units at $0.125 per million'),
    ('execute_tool send_email', 0.0001,    'SES: $0.10 per 1,000 emails');
```

Per-span model cost for this trace, each span priced at the rate valid when it started:

```sql
WITH model_spans AS
(
    SELECT
        SpanName,
        toDateTime(Timestamp) AS ts,
        Duration / 1e9 AS seconds,
        if(SpanAttributes['gen_ai.response.model'] != '',
           SpanAttributes['gen_ai.response.model'],
           SpanAttributes['gen_ai.request.model']) AS model,
        toInt64OrZero(SpanAttributes['gen_ai.usage.input_tokens']) AS input_tokens,
        toInt64OrZero(SpanAttributes['gen_ai.usage.cache_read.input_tokens']) AS cache_read,
        greatest(toInt64OrZero(SpanAttributes['gen_ai.usage.cache_write.input_tokens']),
                 toInt64OrZero(SpanAttributes['gen_ai.usage.cache_creation.input_tokens'])) AS cache_write,
        toInt64OrZero(SpanAttributes['gen_ai.usage.output_tokens']) AS output_tokens
    FROM otel_traces
    WHERE TraceId = '5b8efff798038103d269b633813fc60c'
      AND SpanAttributes['gen_ai.operation.name'] IN ('chat', 'generate_content', 'text_completion', 'embeddings')
)
SELECT
    s.SpanName,
    s.seconds,
    s.input_tokens,
    s.cache_read,
    s.output_tokens,
    round(( greatest(s.input_tokens - s.cache_read - s.cache_write, 0) * p.input_per_mtok
          + s.cache_read    * p.cache_read_per_mtok
          + s.cache_write   * p.cache_write_per_mtok
          + s.output_tokens * p.output_per_mtok) / 1e6, 6) AS cost_usd,
    p.price_table
FROM model_spans AS s
ASOF LEFT JOIN llm_prices AS p
    ON s.model = p.model AND s.ts >= p.valid_from
ORDER BY cost_usd DESC;
```

The `ASOF JOIN` picks, for each span, the newest price row whose `valid_from` is not later than the span's start; a span with no matching row gets an empty `price_table` and a cost of zero, which the next query counts. `greatest(..., 0)` guards against libraries that report Anthropic-style input counts (29b.5.1).

Cost per trace over the last day, model and non-model spans together, most expensive first:

```sql
WITH
model_costs AS
(
    SELECT
        s.TraceId AS trace_id,
        ( greatest(s.input_tokens - s.cache_read - s.cache_write, 0) * p.input_per_mtok
        + s.cache_read    * p.cache_read_per_mtok
        + s.cache_write   * p.cache_write_per_mtok
        + s.output_tokens * p.output_per_mtok) / 1e6 AS cost_usd,
        p.price_table = '' AS unpriced
    FROM
    (
        SELECT
            TraceId,
            toDateTime(Timestamp) AS ts,
            if(SpanAttributes['gen_ai.response.model'] != '',
               SpanAttributes['gen_ai.response.model'],
               SpanAttributes['gen_ai.request.model']) AS model,
            toInt64OrZero(SpanAttributes['gen_ai.usage.input_tokens']) AS input_tokens,
            toInt64OrZero(SpanAttributes['gen_ai.usage.cache_read.input_tokens']) AS cache_read,
            greatest(toInt64OrZero(SpanAttributes['gen_ai.usage.cache_write.input_tokens']),
                     toInt64OrZero(SpanAttributes['gen_ai.usage.cache_creation.input_tokens'])) AS cache_write,
            toInt64OrZero(SpanAttributes['gen_ai.usage.output_tokens']) AS output_tokens
        FROM otel_traces
        WHERE ServiceName = 'support-agent'
          AND Timestamp >= now() - INTERVAL 1 DAY
          AND SpanAttributes['gen_ai.operation.name'] IN ('chat', 'generate_content', 'text_completion', 'embeddings')
    ) AS s
    ASOF LEFT JOIN llm_prices AS p
        ON s.model = p.model AND s.ts >= p.valid_from
),
other_costs AS
(
    SELECT t.TraceId AS trace_id, u.usd_per_span AS cost_usd, toUInt8(0) AS unpriced
    FROM otel_traces AS t
    INNER JOIN span_unit_prices AS u ON t.SpanName = u.span_name
    WHERE t.ServiceName = 'support-agent'
      AND t.Timestamp >= now() - INTERVAL 1 DAY
)
SELECT
    trace_id,
    round(sum(cost_usd), 6) AS trace_cost_usd,
    countIf(unpriced = 1) AS unpriced_model_spans
FROM
(
    SELECT trace_id, cost_usd, unpriced FROM model_costs
    UNION ALL
    SELECT trace_id, cost_usd, unpriced FROM other_costs
)
GROUP BY trace_id
ORDER BY trace_cost_usd DESC
LIMIT 20;
```

For this run it returns 0.045276: model, embedding and data spans, without the orchestrator's compute share, which is better allocated monthly from the bill than per span. If the trace store is sampled, multiply each trace's cost by the adjusted count from 29b.5.5 before summing across traces; if tools run in other services, select the trace ids from the agent service first and drop the `ServiceName` filter for the other spans.

Self time per span, the duration minus the durations of its children, shows where a sequential trace spends its time:

```sql
SELECT
    p.SpanName AS span,
    round(p.Duration / 1e9, 3) AS total_s,
    round((toInt64(p.Duration) - toInt64(sum(c.Duration))) / 1e9, 3) AS self_s
FROM otel_traces AS p
LEFT JOIN
(
    SELECT ParentSpanId, Duration
    FROM otel_traces
    WHERE TraceId = '5b8efff798038103d269b633813fc60c'
) AS c ON c.ParentSpanId = p.SpanId
WHERE p.TraceId = '5b8efff798038103d269b633813fc60c'
GROUP BY p.SpanId, p.SpanName, p.Duration, p.Timestamp
ORDER BY p.Timestamp;
```

Here the `invoke_agent` span has 0.090 s of self time (the gaps between steps), the HTTP span 0.050 s and `execute_tool search_kb` 0.015 s, while every model span is entirely self time. A negative self time means children overlapped, which is where you need a real critical-path computation instead of a sum.

### What observing this run costs

Fourteen spans, about 17 KB without content and 188 KB with it: \$0.0049 at a per-span list price (10.8% of the run's model spend, 29b.5.7) against about \$0.00001 to \$0.0001 at Grafana Cloud's \$0.55 per GB. The design that follows: derive RED and cost metrics from every span before sampling; store complete traces for errors, expensive runs and a small random baseline; keep content out of the trace store, by reference or in a short-retention bucket.

## 29b.7 Quick reference: thirty names

Stability as of semantic conventions 1.44.0 and the GenAI repository's `main` branch on 2 October 2026; Prometheus names under the default translation strategy.

| Name | Kind | Type and unit | Stability | Prometheus name or label |
|---|---|---|---|---|
| `service.name` | Resource attribute | string | Stable | Part of `job` |
| `service.namespace` | Resource attribute | string | Stable | Part of `job` |
| `service.version` | Resource attribute | string | Stable | `service_version` on `target_info` |
| `service.instance.id` | Resource attribute | string | Stable | `instance` |
| `deployment.environment.name` | Resource attribute | string | Stable | `deployment_environment_name` on `target_info`, or promoted |
| `k8s.pod.name` | Resource attribute | string | Stable | `k8s_pod_name` on `target_info` |
| `http.request.method` | Span and metric attribute | string | Stable | `http_request_method` |
| `http.route` | Span and metric attribute | string, low cardinality | Stable | `http_route` |
| `http.response.status_code` | Span and metric attribute | int | Stable | `http_response_status_code` |
| `error.type` | Span and metric attribute | string, absent on success | Stable | `error_type` |
| `db.system.name` | Span and metric attribute | string | Stable | `db_system_name` |
| `db.query.summary` | Span attribute | string | Stable | |
| `rpc.system.name` | Span and metric attribute | string | Release candidate | `rpc_system_name` |
| `gen_ai.operation.name` | Span and metric attribute | string | Development | `gen_ai_operation_name` |
| `gen_ai.provider.name` | Span and metric attribute | string | Development | `gen_ai_provider_name` |
| `gen_ai.request.model` | Span and metric attribute | string | Development | `gen_ai_request_model` |
| `gen_ai.usage.input_tokens` | Span attribute | int, `{token}`, includes cached tokens | Development | Spans only |
| `gen_ai.usage.output_tokens` | Span attribute | int, `{token}`, includes reasoning tokens | Development | Spans only |
| `gen_ai.usage.cache_read.input_tokens` | Span attribute | int, `{token}` | Development | Spans only |
| `gen_ai.usage.cache_write.input_tokens` | Span attribute | int, `{token}`; `cache_creation` up to v1.41.0 | Development | Spans only |
| `gen_ai.conversation.id` | Span attribute | string, high cardinality | Development | Never a metric label |
| `http.server.request.duration` | Metric | Histogram, `s` | Stable | `http_server_request_duration_seconds` |
| `http.client.request.duration` | Metric | Histogram, `s` | Stable | `http_client_request_duration_seconds` |
| `db.client.operation.duration` | Metric | Histogram, `s` | Stable | `db_client_operation_duration_seconds` |
| `rpc.server.call.duration` | Metric | Histogram, `s` | Release candidate | `rpc_server_call_duration_seconds` |
| `container.cpu.time` | Metric | Counter, `s` | Release candidate | `container_cpu_time_seconds_total` |
| `gen_ai.client.operation.duration` | Metric | Histogram, `s` | Development | `gen_ai_client_operation_duration_seconds` |
| `gen_ai.client.token.usage` | Metric | Histogram, `{token}` | Development | `gen_ai_client_token_usage` |
| `gen_ai.client.operation.time_to_first_chunk` | Metric | Histogram, `s` | Development | `gen_ai_client_operation_time_to_first_chunk_seconds` |
| `gen_ai.invoke_agent.duration` | Metric | Histogram, `s` | Development | `gen_ai_invoke_agent_duration_seconds` |

Classic histograms add `_bucket`, `_sum` and `_count` to the metric names in the last column; native histograms use the name as it is. Teams that serve models add `gen_ai.server.time_to_first_token` and `gen_ai.server.time_per_output_token` (histograms, `s`, development).

## 29b.8 Interview questions with model answers

1. **What fields does a span have, and which do people get wrong?** A 16-byte trace id, an 8-byte span id, the parent's span id (empty for a root), the W3C trace state, flags (the W3C trace flags plus two bits saying whether the parent is remote), a name, a kind, start and end times in Unix nanoseconds, attributes, events, links, three dropped counts, and a status with a code and a message. The usual mistakes: span names with ids in them, which break grouping and span metrics; Error status on server spans for 4xx responses; libraries setting Ok; links added after creation, which head samplers never see; attributes silently dropped at the default limit of 128 (watch `dropped_attributes_count`); and latency computed from timestamps taken on two different hosts.

2. **Which span kind do you use for a model call, a tool and a queue consumer?** CLIENT for a call to a remote model API, INTERNAL for a model in the same process. `execute_tool` is INTERNAL, and the HTTP or database calls the tool makes are CLIENT children. A publish is PRODUCER and the processing is CONSUMER, linked to the producer spans because batches have many parents. `invoke_agent` is CLIENT for a remote agent and INTERNAL for a local one. Kind matters because backends pair CLIENT and SERVER spans to build service graphs.

3. **When should a span's status be Error?** When the operation failed: an exception escaped or an error code came back. For HTTP, server spans are Error only on 5xx and client spans on 4xx and 5xx; an intentional cancellation, such as a user stopping a stream or a hedged duplicate, is not an error. Set `error.type` alongside. Instrumentation libraries never set Ok, and an operation that succeeded after retries is not an error, although each failed attempt's own span is.

4. **Delta or cumulative temporality?** Cumulative points report the total since a fixed start time and survive a lost export; delta points report the change since the last export, need less memory in the SDK and suit backends that sum on ingest. Prometheus expects cumulative and drops deltas unless they are converted, in the Collector with the `deltatocumulative` processor or in Prometheus behind the experimental `otlp-deltatocumulative` flag. The SDK default is cumulative; the `delta` preference switches counters and histograms but leaves UpDownCounters cumulative, and gauges have no temporality.

5. **Why are averages misleading for latency?** Because the bulk hides the tail. With 980 requests at 100 ms, 15 at 1 s and 5 at 10 s, the mean is 163 ms while one request in a thousand takes 10 s. Report percentiles computed from merged histograms (never averaged across instances), make sure the window holds enough requests for the percentile you quote, and for SLOs prefer the share of requests above a threshold (45a.3).

6. **A request fans out to 50 shards, each with a p99 of 200 ms. What do users see?** 1 − 0.99^50 = 39.5% of requests wait on at least one shard slower than its p99, so the request's p99 is set by roughly the shards' p99.98, far above 200 ms. Reduce fan-out, tighten shard tails, hedge after the p95, or return partial results at a deadline.

7. **How would you compute cost per trace for an agent?** For each inference span, (input − cache read − cache write) × input price + cache read × read price + cache write × write price + output × output price, using the conventions' inclusive input count and a versioned price table, and only inference spans, because `invoke_agent` may repeat the totals. Add tool, database and egress spans at their unit prices, count every retry, and attribute shared work by explicit rules. Compute it in the application for budgets, in the Collector before sampling for metrics, and in the warehouse for the authoritative number, reconciled with the invoice. Stamp the price-table version on every span.

8. **Your cost dashboard fell 90% the day you turned on sampling. What happened?** It summed cost over stored traces, and head sampling at 10% stores a tenth of them. Compute cost metrics from all spans before sampling, or weight each stored trace by its adjusted count from the `th` threshold. Tail sampling distorts the other way: keeping every expensive run and 5% of the rest made the stored mean nearly four times the true mean in 29b.5.5.

9. **What is an exemplar, and how does it reach Grafana?** A raw measurement attached to a metric point, with the trace and span ids of the request behind it. The SDK keeps exemplars from sampled traces by default (`trace_based`) and exports them in the OTLP `Exemplar` message with any filtered attributes; Prometheus stores them with `trace_id` and `span_id` labels when the `exemplar-storage` flag is on; Grafana draws them on histogram panels and links them to Tempo (45b.6).

10. **How does `http.server.request.duration` appear in Prometheus?** Under the default `UnderscoreEscapingWithSuffixes` strategy, as `http_server_request_duration_seconds_bucket`, `_sum` and `_count` with labels such as `http_request_method`, `job` built from the service namespace and name, `instance` from `service.instance.id`, and the other resource attributes on `target_info`. With exponential histograms it is one native-histogram series. `NoUTF8EscapingWithSuffixes` keeps the dots (`http.server.request.duration_seconds`), and `NoTranslation` keeps the OTLP name unchanged.

11. **What is a schema URL for, and what can a schema file not do?** It records which convention version the data follows, and the file at that URL lists renames and splits between versions, so a pipeline such as the Collector's schema processor can translate data. It cannot express unit changes, value changes or changes of meaning, which need dual emission or query changes; and the GenAI conventions have no schema URL yet, so their renames are handled with OTTL in the Collector.

12. **Explain TTFT, TPOT and end-to-end latency for a model call, and what moves each.** TTFT is queueing plus prefill, so it grows with uncached input and falls with cache reads; TPOT is the decode time per token, set by the model and the server's load; end to end is about TTFT + (output tokens − 1) × TPOT, so output length multiplies TPOT. Standard metrics: `gen_ai.server.time_to_first_token`, `gen_ai.server.time_per_output_token`, `gen_ai.client.operation.time_to_first_chunk` and `gen_ai.client.operation.duration`. For agents, measure time to first visible token at the client, because the first API token may belong to a hidden step.

13. **Fifty agent runs per second take 8 seconds each. How many are in flight, and what does cutting 2 seconds buy?** By Little's law, 50 × 8 = 400 in flight, and 50 × 6 = 300 after the change: a quarter less memory, fewer connections and fewer batch slots, which is real money wherever capacity is priced by time, such as self-hosted GPUs. You can check the in-flight number from telemetry, because the rate of a duration histogram's `_sum` equals the mean concurrency.

14. **Head or tail sampling, and where do RED and cost metrics come from?** Head sampling is cheap and blind to outcomes; tail sampling keeps errors, slow runs and expensive runs, but needs a trace-aware Collector tier and a buffer sized for the longest trace (45b.2). Either way, derive RED and cost metrics from every span before sampling, and record the sampling probability and policy with the stored traces so they can be weighted.

15. **Why not put the tenant id on a metric?** Because series multiply: the token-usage histogram on 30 pods is 2,040 series, about \$13 a month at Grafana Cloud's list price, and a 500-value tenant label makes it 1,020,000 series, about \$6,630 a month, for one metric. Put the tenant on spans through baggage and roll it up in the warehouse; a cost metric can carry it only while tenants number in the hundreds.

16. **What does it cost to observe an agent?** Count spans and bytes. The run in 29b.6 has 14 spans: at a per-span price of \$3.50 per 10,000 spans it costs \$0.0049 to observe, 10.8% of its model spend, while byte-priced trace storage costs a hundredth of a cent. Captured content dominates bytes (about 171 KB of 188 KB per run), so store content by reference, sample traces, and keep metrics unsampled.

17. **Three gateway replicas each compute cost metrics from the spans they receive. What can go wrong?** The single-writer principle. Routing by trace ID gives every replica a slice of every service, so all three write the same series. In OTLP they differ by a resource attribute that marks the replica, but Prometheus and Mimir build series from `job`, `instance` and point attributes only, so the three streams collide: samples are rejected as duplicates or out of order, or accepted as a counter that seems to reset all the time. Promote the replica attribute to a label and aggregate it away in queries, route by service to the tier that computes metrics, or compute the metrics in the node agents, where each pod has exactly one Collector.

**Interview line:** *"I read telemetry as data with a schema: spans with the right kind and status, semantic-convention names at a pinned version, and RED and cost metrics derived from every span before sampling. Cost is just another derived signal, inference-span tokens times a versioned price weighted by each trace's adjusted count, so I can tell you what one agent run costs, where its seconds go, and what observing it costs."*

## Sources

All links were accessed on 2 October 2026; dates in parentheses are publication or release dates.

Specifications and protocol:

- [OpenTelemetry Tracing API specification](https://opentelemetry.io/docs/specs/otel/trace/api/) (specification 1.61.0: span names, kinds, status rules, links)
- [OTLP specification](https://opentelemetry.io/docs/specs/otlp/) and [opentelemetry-proto specification.md](https://github.com/open-telemetry/opentelemetry-proto/blob/main/docs/specification.md) (ports, paths including `/v1development/profiles`, JSON encoding, retryable codes, size limits)
- opentelemetry-proto on `main`: [trace.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/trace/v1/trace.proto), [metrics.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/metrics/v1/metrics.proto), [logs.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/logs/v1/logs.proto), [common.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/common/v1/common.proto), [resource.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/resource/v1/resource.proto), [profiles.proto (v1development)](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/profiles/v1development/profiles.proto), and the [v1.11.0 release](https://github.com/open-telemetry/opentelemetry-proto/releases/tag/v1.11.0) (21 July 2026)
- [OpenTelemetry metrics data model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/), [metrics SDK](https://opentelemetry.io/docs/specs/otel/metrics/sdk/) (default aggregations and buckets, exponential defaults, cardinality limit, exemplars) and [OTLP metrics exporter temporality](https://opentelemetry.io/docs/specs/otel/metrics/sdk_exporters/otlp/)
- [OpenTelemetry logs data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) (fields, severity ranges, events)
- [SDK environment variables](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/) (limits, samplers, exemplar filter, export intervals)
- [TraceState probability sampling](https://opentelemetry.io/docs/specs/otel/trace/tracestate-probability-sampling/) (`th`, `rv`, adjusted count; development)
- [Prometheus and OpenMetrics compatibility](https://opentelemetry.io/docs/specs/otel/compatibility/prometheus_and_openmetrics/)
- [Schema file format 1.1.0](https://opentelemetry.io/docs/specs/otel/schemas/file_format_v1.1.0/), the [1.27.0 schema file](https://github.com/open-telemetry/semantic-conventions/blob/main/schemas/1.27.0) and [versioning and stability](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/)
- [OpenTelemetry blog: Profiles enters public alpha](https://opentelemetry.io/blog/2026/profiles-alpha/) (26 March 2026)
- [W3C Trace Context Level 2](https://www.w3.org/TR/trace-context-2/) (candidate recommendation draft; random flag, tracestate limits)

Semantic conventions (release 1.44.0, August 2026, and the GenAI repository's `main` branch):

- [Semantic conventions releases](https://github.com/open-telemetry/semantic-conventions/releases) (v1.42.0 moved GenAI out; v1.44.0 contents)
- [HTTP spans](https://opentelemetry.io/docs/specs/semconv/http/http-spans/) and [HTTP metrics](https://opentelemetry.io/docs/specs/semconv/http/http-metrics/); [database spans](https://opentelemetry.io/docs/specs/semconv/database/database-spans/) and [database metrics](https://opentelemetry.io/docs/specs/semconv/database/database-metrics/); [DynamoDB](https://opentelemetry.io/docs/specs/semconv/database/dynamodb/); [RPC spans](https://opentelemetry.io/docs/specs/semconv/rpc/rpc-spans/) and [RPC metrics](https://opentelemetry.io/docs/specs/semconv/rpc/rpc-metrics/); [messaging spans](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/) and [messaging metrics](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-metrics/)
- [Exceptions on spans](https://opentelemetry.io/docs/specs/semconv/exceptions/exceptions-spans/) (deprecated), [exceptions in logs](https://opentelemetry.io/docs/specs/semconv/exceptions/exceptions-logs/) and [recording errors](https://opentelemetry.io/docs/specs/semconv/general/recording-errors/)
- [Naming guidance](https://opentelemetry.io/docs/specs/semconv/general/naming/); registries for [service](https://opentelemetry.io/docs/specs/semconv/registry/attributes/service/), [cloud](https://opentelemetry.io/docs/specs/semconv/registry/attributes/cloud/), [Kubernetes](https://opentelemetry.io/docs/specs/semconv/registry/attributes/k8s/), [host](https://opentelemetry.io/docs/specs/semconv/registry/attributes/host/), [container](https://opentelemetry.io/docs/specs/semconv/registry/attributes/container/) and [app](https://opentelemetry.io/docs/specs/semconv/registry/attributes/app/); [service resource](https://opentelemetry.io/docs/specs/semconv/resource/service/), [deployment environment](https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/), [resource overview](https://opentelemetry.io/docs/specs/semconv/resource/), [Kubernetes metrics](https://opentelemetry.io/docs/specs/semconv/system/k8s-metrics/) and [container metrics](https://opentelemetry.io/docs/specs/semconv/system/container-metrics/)
- [semantic-conventions-genai repository](https://github.com/open-telemetry/semantic-conventions-genai): docs [gen-ai-spans.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md), [gen-ai-agent-spans.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md), [gen-ai-metrics.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md), [gen-ai-events.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md), [mcp.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/mcp.md), the [attribute registry](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/registry/attributes/gen-ai.md) and [model/gen-ai/spans.yaml](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/model/gen-ai/spans.yaml); the earlier name `gen_ai.usage.cache_creation.input_tokens` from [semantic-conventions v1.41.0](https://github.com/open-telemetry/semantic-conventions/blob/v1.41.0/model/gen-ai/registry.yaml)
- [OpenTelemetry Python OpenAI instrumentation README](https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation-genai/opentelemetry-instrumentation-openai-v2/README.rst) (content-capture and upload settings)

Prometheus, Collector, Tempo and ClickHouse:

- Prometheus: [configuration (`otlp` block)](https://prometheus.io/docs/prometheus/latest/configuration/configuration/), [using Prometheus as an OpenTelemetry backend](https://prometheus.io/docs/guides/opentelemetry/), [feature flags](https://prometheus.io/docs/prometheus/latest/feature_flags/), [releases](https://github.com/prometheus/prometheus/releases) (3.14.0, 17 August 2026), [OpenMetrics 1.0](https://prometheus.io/docs/specs/om/open_metrics_spec/) and the [otlptranslator library](https://github.com/prometheus/otlptranslator)
- Collector contrib (v0.161.0 [release](https://github.com/open-telemetry/opentelemetry-collector-contrib/releases/tag/v0.161.0)): [transform processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/transformprocessor/README.md), [OTTL language](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/pkg/ottl/LANGUAGE.md) and [functions](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/pkg/ottl/ottlfuncs/README.md), [signal_to_metrics connector](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/connector/signaltometricsconnector/README.md) (`AdjustedCount()`, single-writer resource attribute), [sum connector](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/connector/sumconnector/README.md), [deltatocumulative processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/deltatocumulativeprocessor/README.md) and its [metadata.yaml](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/deltatocumulativeprocessor/metadata.yaml) (type name), [tail_sampling processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/tailsamplingprocessor/README.md), [probabilistic_sampler processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/probabilisticsamplerprocessor/README.md), [adaptive_tail_sampling processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/adaptivetailsamplingprocessor/README.md), [schema processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/schemaprocessor/README.md), [resource_detection processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/resourcedetectionprocessor/README.md), [ClickHouse exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/exporter/clickhouseexporter/README.md) and its [traces table](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/exporter/clickhouseexporter/internal/sqltemplates/traces_table.sql)
- Grafana Tempo 3.1: [release notes](https://grafana.com/docs/tempo/latest/release-notes/v3-1/), [TraceQL](https://grafana.com/docs/tempo/latest/traceql/construct-traceql-queries/) and [TraceQL metrics functions](https://grafana.com/docs/tempo/latest/metrics-from-traces/metrics-queries/functions/) (including `with(extrapolate=true)`)
- Prometheus OTLP translator, [helper.go](https://github.com/prometheus/prometheus/blob/main/storage/remote/otlptranslator/prometheusremotewrite/helper.go) (`le` values written with `strconv.FormatFloat`), and [Mimir: configure the OpenTelemetry Collector](https://grafana.com/docs/mimir/latest/configure/configure-otel-collector/) (`-distributor.otel-promote-resource-attributes`)
- [ClickHouse JOIN, including ASOF JOIN](https://clickhouse.com/docs/sql-reference/statements/select/join)

Prices (list prices on 2 October 2026):

- [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing) (token prices, cache multipliers, web search, code execution, US-only inference, fast mode, long-context pricing), [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) (API ids) and [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (usage fields, minimum cacheable lengths, workspace isolation)
- [Voyage AI pricing](https://docs.voyageai.com/docs/pricing); [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/); [DynamoDB on-demand pricing](https://aws.amazon.com/dynamodb/pricing/on-demand/); [Amazon SES pricing](https://aws.amazon.com/ses/pricing/); [Amazon EC2 on-demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) (free egress allowance)
- [Grafana Cloud pricing](https://grafana.com/pricing/) and [Datadog list pricing](https://www.datadoghq.com/pricing/list/)
- [OpenAI Help Center: what are tokens](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them) (about 4 characters per token in English)

Latency, reliability and methods:

- Jake Brutlag, [Speed Matters](https://research.google/blog/speed-matters/), Google Research (23 June 2009)
- Deloitte Ireland for Google, [Milliseconds Make Millions](https://www.deloitte.com/ie/en/services/consulting/research/milliseconds-make-millions.html) (March 2020)
- Jeffrey Dean and Luiz André Barroso, [The Tail at Scale](https://cacm.acm.org/research/the-tail-at-scale/), Communications of the ACM 56(2) (February 2013)
- NVIDIA, [LLM Inference Benchmarking: Fundamental Concepts](https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/) (2 April 2025)
- [Google SRE book, chapter 6: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (golden signals, tail latency)
- Tom Wilkie, [The RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) (August 2018); Brendan Gregg, [The USE Method](https://www.brendangregg.com/usemethod.html)
- [New Relic: Apdex](https://docs.newrelic.com/docs/apm/new-relic-apm/apdex/apdex-measure-user-satisfaction/); [DORA metrics](https://dora.dev/guides/dora-metrics-four-keys/); Štěpán Davidovič, [Incident Metrics in SRE](https://sre.google/resources/practices-and-processes/incident-metrics-in-sre/) (Google, 2021)
- [web.dev: Web Vitals](https://web.dev/articles/vitals)
