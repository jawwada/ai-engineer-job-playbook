# 45a. Observability engineering: the role, systems at scale, and SLAs that mean something

> **What you need to be able to say:** what an observability engineer owns and how each line of a typical job description is tested; how both the observed systems and the telemetry pipeline fail at scale (cardinality explosions, high-churn labels, backpressure and dropped samples, sampling bias, clock skew, out-of-order and duplicate data, collector memory limits, queries of death, fan-out, alert storms, missing meta-monitoring, circular dependencies, cost blowups) with a detection signal and a mitigation for each; the life cycle of metrics, dashboards, alerts, services, stored telemetry and semantic conventions; SLIs, SLOs, SLAs and error budgets with the burn-rate arithmetic and correct Prometheus rules; what a canary gate can and cannot detect; SLOs for the observability platform itself; composite availability; how to tell a meaningful SLA from a hollow one; how to set a technical agenda, write an RFC and measure an observability program; how to communicate in incidents, postmortems and workshops; and a 30-60-90-day plan. Chapter 45b covers the open-source stack (OpenTelemetry, Prometheus, PromQL, Grafana, Loki, Tempo, Mimir) in depth, chapter 45c covers AI for observability and how to build and distribute AI skills, chapter 45 has the SRE vocabulary, and chapter 29 covers telemetry for LLM systems.

## 45a.1 The job description decoded

A representative job description (anonymized, paraphrased) for this kind of role reads like this. About the role: reason about systems at scale, including their edge cases, failure modes and life cycles; set the technical agenda and come up with novel, broad ideas; keep up with the newest AI advances in observability and monitoring; know what a good SLA looks like and teach others how to spot one; communicate as well as you code, in a team that values clear and frequent communication. Skills: five or more years with the open-source Grafana stack (Grafana, Loki, Tempo, Mimir, often called "LGTM"); hands-on instrumentation of distributed systems with OpenTelemetry and metrics pipelines with Prometheus at scale; direct experience building and distributing Claude Skills, Gemini Gems or other reusable AI processes and iterating on their efficacy; and working with time-series data, ideally in PromQL.

Titles vary: Observability Engineer, Senior or Staff Observability Engineer, Monitoring Platform Engineer, SRE (Observability), Telemetry Platform Engineer. The posting mixes three jobs. The first is a platform engineer who runs a large telemetry stack as a product for other teams. The second is a reliability practitioner who defines what "working" means for users and turns it into SLOs, alerts and contracts. The third is a staff-level engineer who sets direction, writes it down and teaches it. The AI line is the newest part of these postings in 2025–2026, and it is where candidates differ most.

| Requirement (paraphrased) | What it means in practice | Artifacts you produce | How it is tested in interviews |
|---|---|---|---|
| Reason about systems at scale: edge cases, failure modes, life cycles | Predict what breaks first when traffic, label values, tenants or retention grow tenfold, in the observed systems and in the telemetry pipeline itself; design limits and degradation paths before they are needed | Failure-mode analyses, capacity models (active series, samples per second, GB per day), tenant limits and overrides, meta-monitoring dashboards, runbooks | System design ("metrics and traces for 5,000 services"), "what breaks first at 10x?", a pipeline that silently drops data, a cardinality incident |
| Set the technical agenda; novel, broad ideas | Decide what the observability platform does next year and why, and get other teams to adopt it | Strategy one-pager, maturity assessment, RFCs, roadmap, adoption and outcome metrics | "Tell me about a direction you set", "how did you get forty teams to adopt it?", presenting an RFC to a panel |
| Keep up with AI advances in observability | Evaluate investigation assistants, MCP access to telemetry, time-series foundation models and natural-language querying, and adopt only what measurably helps | Evaluation reports on replayed incidents, pilot results, guardrail designs | "How would you evaluate an AI SRE agent?", "where does an LLM help in an incident and where does it hurt?" (chapter 45c) |
| Know what a good SLA looks like; teach others to spot one | Write and review SLIs, SLOs, error-budget policies and SLAs, including vendor SLAs your company depends on | SLO documents, error-budget policies, an SLA review checklist, workshop material | Critiquing an SLA live, designing SLOs for a service, burn-rate arithmetic on a whiteboard |
| Communicate as well as you code | Incident updates, postmortems, RFC reviews, office hours, written status reports | Status-update templates, postmortems, review comments, documentation | Behavioral questions (chapter 38), "write a customer update in five minutes", "explain a burn-rate alert to a product manager" |
| 5+ years with Grafana, Loki, Tempo, Mimir | Operate the stack at scale: sizing, upgrades (Mimir 3 ingest storage, Tempo 3's new architecture), tenant limits, log label design, query performance | Helm values, limits and overrides, dashboards as code, upgrade plans | Deep dives: "this LogQL query is slow, why?", "Mimir ingesters run out of memory after a deploy", "design the labels for these logs" |
| OpenTelemetry instrumentation; Prometheus pipelines at scale | Instrument services (SDKs, auto-instrumentation, eBPF), run Collectors (agent and gateway tiers, tail sampling), run Prometheus and remote write at scale (sharding, HA pairs, relabeling, cardinality control) | Collector configurations, instrumentation guides, semantic-convention standards, relabeling and recording rules | "Follow a trace across a message queue", "design tail sampling for 50,000 spans per second", writing relabel configs |
| Build and distribute Claude Skills, Gemini Gems or similar; iterate on efficacy | Package team procedures (incident triage, query writing, SLO review) as AI skills, distribute them, and prove they help with trigger accuracy, task success and a no-skill baseline | Skills with eval suites, a plugin marketplace or org-wide provisioning, usage telemetry, a changelog | "Show a skill you built and how you know it works", "how do you review a third-party skill?" (chapter 45c) |
| Time-series data, ideally PromQL | Fluent PromQL (rate before sum, histograms, vector matching) and time-series reasoning (resolution, staleness, seasonality) | Recording rules, alert rules, dashboards, a vetted query library | Live PromQL exercise, "why is this p99 wrong?", "write a burn-rate alert" |

**Reading the seniority.** "Set the technical agenda" and "novel, broad ideas" signal a staff-level loop: expect a written exercise or a presentation, and questions about influence without authority. "Teach others" means you will be asked how you run a workshop and how you know it worked.

**The loop to expect** (it varies by company): a recruiter screen; a technical screen with live PromQL and LogQL; a system design round on a telemetry pipeline or an SLO platform; an incident scenario debugged from dashboards and traces; an SLO or SLA review exercise; a communication round (present an RFC or walk through a postmortem); and, increasingly, an AI round where you show a skill or agent you built and how you measured it. Prepare one story per row of the table (chapter 38) and one number per story.

## 45a.2 Reasoning about systems at scale

### Six questions to ask of any component

1. **What grows with traffic, and what grows with cardinality?** Request volume drives samples per second, log bytes and spans. The number of distinct label values drives active series, index size and memory. The two grow independently, and the second is the one that surprises people.
2. **What is shared?** A shared ingester, Kafka partition, query frontend, Collector gateway or Alertmanager is the blast radius of a bad tenant, a bad query or a bad deploy.
3. **What is retried, and by whom?** Retries multiply load when a system is weakest. Telemetry clients retry too, and a retry after a timeout can write the same data twice.
4. **What is unbounded?** Queues, label values, query time ranges, log line sizes, trace durations and fan-out are the usual suspects. Every unbounded thing needs a limit and a behavior at the limit.
5. **What depends on what?** Draw the dependency graph and look for cycles: does the tool you need during an outage depend on the system that is out?
6. **What changes over time?** Every metric, dashboard, alert, service and convention has a life cycle (see "Life cycles" below). Most production telemetry problems are changes nobody planned for.

### The arithmetic of cardinality

The number of series a metric can produce is bounded by the product of the distinct values of its labels. Take an HTTP server latency histogram emitted by OpenTelemetry (`http.server.request.duration`, which Prometheus exposes as `http_server_request_duration_seconds_*`). The semantic conventions advise 14 explicit bucket boundaries, so a classic Prometheus histogram has 15 `_bucket` series (including `+Inf`) plus `_sum` and `_count`: 17 series per label combination.

| Dimension | Distinct values | Running total of label combinations |
|---|---|---|
| route and method pairs actually used | 60 | 60 |
| status codes seen | 8 | 480 |
| pods | 50 | 24,000 |
| series per combination (classic histogram) | 17 | **408,000 series** |

That is one metric in one service. At a 15-second scrape interval it is 27,200 samples per second; at 1–2 bytes per sample on disk (Prometheus's documented average), about 2.35 billion samples and roughly 3.5 GB per day before replication. Three changes shrink it: aggregating away the `pod` label in a recording rule or at the Collector brings the stored aggregate to 480 × 17 = 8,160 series; a native histogram stores all buckets in one series, so the per-pod version becomes 24,000 series; and dropping a `user_id` label that someone added "for debugging" prevents the multiplication by 100,000 that would otherwise follow. Memory follows active series and churn, not sample rate; measure memory per series on your own server (45b.3) rather than trusting a rule of thumb.

### Failure modes of the observed systems

These belong to distributed systems in general (chapter 49.4) but they shape what you measure. **Retry storms and metastable failure**: a brief slowdown triggers client retries that keep the system overloaded after the original cause is gone. **Gray failure**: health checks pass while users fail, because the check exercises a different path. **Slow dependencies**: latency is more dangerous than errors because slow calls hold threads, connections and memory. **Queue backlogs**: depth looks fine until the oldest message is an hour old; measure age, not only depth. **Cascading failure and thundering herds**: one overloaded instance sheds load onto the others; recovery triggers a synchronized reconnect. **Noisy neighbors**: one tenant or pod saturates a shared resource. **Poison messages**: one bad input crashes every consumer that reads it. The observability consequences are consistent: alert on user-facing symptoms (SLO burn) rather than causes, capture tail latency with histograms, measure client-side latency and errors per dependency, and record queue age and saturation, not only throughput.

### Failure modes of the telemetry pipeline

The telemetry pipeline is a distributed system with the same failure modes, plus some of its own. This is the table to know cold.

| Failure mode | How it happens | Detection signal | Mitigation |
|---|---|---|---|
| Cardinality explosion | A label with unbounded values (user ID, request ID, full URL, error text, pod IP) is added to a metric, and series multiply | Jump in `prometheus_tsdb_head_series` (Mimir: `cortex_ingester_memory_series`); `scrape_series_added` spikes on one target; top label pairs in `/api/v1/status/tsdb`; Mimir `cortex_discarded_samples_total` with a series-limit reason | Per-scrape `sample_limit` and `label_limit`; per-tenant series limits; drop or aggregate labels in the Collector or with `metric_relabel_configs`; SDK Views with attribute allow-lists; a review gate for new metrics; identifiers belong on spans and logs, not metric labels |
| High-churn labels | Labels whose values change on every rollout (pod name, container ID, version, deployment hash) create new series while the old ones stay in memory until head compaction | `rate(prometheus_tsdb_head_series_created_total[5m])` high relative to head series; memory sawtooth on deploy days | Aggregate pod away in stored views; put version in an info metric and join it when needed; avoid churny labels on high-volume metrics |
| Ingestion backpressure and dropped samples | The backend is slower than producers; queues fill; clients block or drop | Collector `otelcol_exporter_queue_size` near `otelcol_exporter_queue_capacity`, plus enqueue-failed and refused counters; Prometheus remote-write lag and `prometheus_remote_storage_samples_failed_total`; Loki and Mimir discarded-sample counters by reason | `memory_limiter` first in every Collector pipeline; persistent queues; enough shards and replicas; per-tenant rate limits that return clear 429s; alert on remote-write lag well before the WAL's roughly two hours run out; shed low-value data (debug logs) first |
| Sampling bias | Head sampling keeps a random share and loses rare errors; tail-sampling policies over-represent errors; metrics derived from sampled spans undercount traffic | Request rate from span metrics differs from service metrics; error ratio from traces far above the metric error ratio | Derive RED metrics from 100% of spans before sampling (45b.2); keep the sampling probability with the data and weight by it; never compute SLIs from sampled traces |
| Clock skew | Hosts disagree on time: children appear to start before parents, logs interleave wrongly, samples are rejected as too old or from the future | Negative gaps in traces; Loki rejections for out-of-order or too-old entries; `node_timex_offset_seconds` from node exporter | NTP or chrony everywhere with an alert on offset; server-side timestamps where possible; out-of-order windows where legitimate; for client devices, record both client and server time |
| Out-of-order samples | Two writers for one series, delayed replays from queues, backfills | `prometheus_tsdb_out_of_order_samples_total`; Mimir discards with an out-of-order reason | Exactly one writer per series (add an instance or replica label); enable `out_of_order_time_window` only where data legitimately arrives late, such as OTLP push or replays |
| Two writers from Collector-generated metrics | Span metrics or `signal_to_metrics` computed in a gateway with several replicas: routed by trace ID, every replica sees a slice of every service's spans and computes the same series | Out-of-order or duplicate samples rejected, or counters that jump between replicas' values; with the span metrics connector's per-replica `collector.instance.id` label, series counts that scale with the replica count and churn on restarts | Compute span metrics in the node agents or in a tier fed by a `load_balancing` exporter with `routing_key: service`; otherwise aggregate the replica label away after `rate`, and promote `signal_to_metrics`'s replica resource attribute to a label (45b.2) |
| Retries and duplicate data | A client retries after a timeout although the first write succeeded; HA Prometheus pairs send the same series | Duplicate log lines; double-counted events when two writers disagree | Idempotent writes (a sample is keyed by series and timestamp); HA deduplication with `cluster` and `__replica__` labels in Mimir or replica labels in Thanos; dedup keys for logs and events |
| Collector memory limits | Bursts, large batches, tail-sampling buffers or a slow exporter push the Collector past its container limit; an OOM kill loses buffered data | Restarts with `OOMKilled`; process memory near the limit; refusals from `memory_limiter` | `memory_limiter` below the container limit; size tail sampling from traffic × decision wait (45b.2); scale horizontally; persistent queues |
| Query of death | One query (unbounded regex on a high-cardinality label, a year at fine resolution, `count by` over everything) exhausts querier memory | Querier OOMs; p99 query latency spikes; query-frontend queue grows | Per-tenant query limits (series fetched, samples, range, timeout); Prometheus `--query.max-samples` (50 million by default) and `--query.timeout` (2 minutes); query splitting and sharding; results caching |
| Fan-out queries | Dashboards with thirty panels, many template variables and a 10-second refresh hit every querier and store-gateway; cross-cluster queries multiply | Read-path request rate per dashboard; queue length; Grafana usage data | Recording rules for hot panels; minimum refresh intervals; `$__rate_interval`; dashboard reviews; caching |
| Alert storms | One root cause (a partition, a shared dependency, a bad deploy) fires hundreds of alerts | Notifications per minute; `alertmanager_alerts{state="active"}` jumps | Page on symptoms (SLO burn), not causes; `group_by` service and cluster; inhibition (cluster down mutes pod alerts); rate limits on paging |
| Missing meta-monitoring | The monitoring system fails silently: the rule evaluator is down or data stopped arriving, and nothing fires | A watchdog alert that always fires and pages through an external heartbeat service when it stops arriving; `up` for monitoring components; `absent_over_time` on key series | An independent meta-monitoring stack in a different failure domain; external synthetic checks |
| Depending on the thing being monitored | Monitoring runs on the cluster it watches; paging uses the same SSO, DNS or network; runbooks sit behind the failing SSO; break-glass access needs the broken control plane | Game days; a dependency review of the incident tooling itself | Separate failure domains; out-of-band paging; cached runbooks; tested break-glass access |
| Cost blowups | Debug logging left on, a new high-cardinality metric, traces at 100%, long retention for everything; the bill grows faster than traffic | Ingested GB per day and active series by team and source; cost per service; anomaly alerts on ingestion volume | Showback and budgets per team (chapter 47); per-tenant limits; sampling and retention tiers; remove unused metrics based on query usage |
| Silent data loss and staleness | A target disappears and its series stop; `rate(errors_total[5m]) > 0.05` evaluates to nothing and never fires; pushed OTLP data has no `up` series | `up == 0`; `absent_over_time(...)`; heartbeat series per source | An absence alert for every SLI input; heartbeat metrics for push pipelines; expected target counts per scrape pool |

**Two incidents from the public record.** On 11 December 2024 OpenAI deployed a new telemetry service to collect Kubernetes metrics. Its configuration made every node in each cluster run Kubernetes API operations whose cost grew with cluster size; the API servers were overwhelmed, DNS-based service discovery broke, and the API, ChatGPT and Sora were degraded or down from 3:16 to 7:38 p.m. PST, about 4 hours 20 minutes, with substantial recovery starting after about two hours and twenty minutes. Staging did not reproduce it because the effect appeared only in large clusters, and DNS caching on each node delayed visible failures long enough for the rollout to reach every cluster. Remediation was slow because fixing it required the control plane that was overloaded. OpenAI's follow-ups were phased rollouts with cluster-health checks, fault injection for control-plane failures, break-glass access to the API servers, and decoupling DNS from the control plane. Lessons for an observability team: telemetry agents have the widest footprint of any software you deploy, so roll them out in phases with load gates; test at production cluster sizes; and keep break-glass access that does not depend on the failing control plane.

Earlier, on 8 March 2023, a systemd security update applied automatically to Datadog's hosts restarted the network daemon, which deleted the routes their container network (Cilium) relied on, on tens of thousands of nodes across five regions; customers lost or had degraded access to dashboards, alerting and historical data, and the incident lasted about 27 hours. Datadog's own conclusion was that live data and alerts matter far more than historical data. The lesson for customers of any vendor: your monitoring provider is a dependency with an availability of its own, so keep a minimal independent path for paging on your most important SLOs.

### Life cycles

| Object | Birth | Healthy life | Decay signals | Retirement |
|---|---|---|---|---|
| Metric or label | Proposed with an owner, a purpose and a cardinality estimate; reviewed against conventions | Referenced by dashboards, alerts or recording rules | Not queried for 90 days; cardinality creeping up; duplicate of a standard metric | Announce, dual-emit if renamed, remove from instrumentation, drop at the Collector in the meantime |
| Dashboard | Created as code with an owner and a question it answers | Viewed during incidents and reviews; panels use recording rules | No views in 90 days; broken queries; duplicates | Archive, then delete; keep the JSON in git |
| Alert | Created with an owner, a runbook, a severity and a link to the SLO or failure it protects | Fires rarely and is acted on | Precision below about 50% (most firings need no action); always firing; nobody owns it | Rewrite as an SLO burn alert, downgrade to a ticket, or delete; review alerts quarterly |
| Service | Onboarding checklist: OpenTelemetry SDK, resource attributes, SLOs, dashboards, alerts, runbook | SLOs reviewed monthly; error-budget policy applied | Missing owner; telemetry gaps after a re-architecture | Remove scrape targets, alerts and SLOs together, or the absence alerts page forever |
| Stored telemetry | Ingested with a retention class | Hot, then compacted; summarized where useful | Retention cost exceeds use; legal hold or deletion requests | Expiry by retention; deletion APIs for privacy requests |
| Semantic convention | Adopted at a pinned version | Instrumentation, dashboards and rules agree on names | A new version renames attributes or units | Dual-emit, translate at the Collector, migrate queries, remove the old names |
| Component or agent | Chosen with a support horizon | Upgraded on a cadence | Deprecation or end-of-life announcement | Migrate before end of life; keep a deprecation calendar |

**Metrics and labels.** Usage data tells you what to delete. Mimir's `mimirtool` can analyze which metrics Grafana dashboards and rule files reference, and query logs show what people query; Grafana Cloud's Adaptive Metrics does the same commercially by analyzing use across dashboards, alerts, recording rules and queries and recommending aggregations. A metric nobody queries is pure cost.

**Stored data.** Prometheus's head block, WAL, compaction and retention settings are in 45b.3; the life-cycle decision is how long each signal is worth keeping. Thanos's compactor downsamples raw data to 5-minute resolution after 40 hours and to 1-hour resolution after 10 days, and its documentation is explicit that downsampling speeds up long-range queries rather than saving space: keeping all three resolutions can roughly triple storage. Mimir does not downsample; it relies on query splitting, sharding and caching, and on recording rules as manual downsampling (45b.5). A typical policy: metrics 13 months (for year-over-year comparisons), logs 14–30 days hot plus an archive, traces 7–14 days, profiles 7–14 days.

**Semantic-convention migrations.** The HTTP conventions moved from `http.server.duration` in milliseconds to `http.server.request.duration` in seconds, with renamed attributes (`http.method` to `http.request.method`, `http.status_code` to `http.response.status_code`); OpenTelemetry instrumentations let you emit the new names (`OTEL_SEMCONV_STABILITY_OPT_IN=http`) or both (`http/dup`) during migration. The Kubernetes conventions reached stable in June 2026, and the `k8s_attributes` Collector processor shipped v1.0.0 in September 2026 with breaking attribute changes to match. Prometheus 3 normalizes the `le` and `quantile` label values of scraped classic histograms and summaries to floats, so a query on scraped data written as `le="1"` must now be `le="1.0"`; data ingested through OTLP keeps the translator's formatting (`le="1"`), so list a label's values before writing a selector (45b.3). The GenAI conventions are still moving (chapter 29). The playbook is the same each time: inventory every consumer (dashboards and rules in git, `mimirtool` analysis, query logs), dual-emit or translate at the Collector with the transform processor, migrate queries, wait one retention period for dashboards that look back, then remove the old names.

**Deprecations in the stack, 2025–2026.** Grafana Agent reached end of life on 1 November 2025 (migrate to Alloy); Promtail reached end of life on 2 March 2026 and is removed as of Loki 3.7.3; Mimir 3.0 (October 2025) removed the read-write deployment mode and Redis caching and made the query-scheduler mandatory; Tempo 3.0 (May 2026) removed ingesters and the compactor in favor of a Kafka-based architecture, and Tempo 3.1 (29 September 2026) made vParquet5 the default block format and refuses to start if configured to write vParquet3; the Collector renamed many components to snake_case during 2026 with deprecated aliases, and its queue-based successor to the batch processor, added as `queuebatch` in v0.158.0, was renamed `queue_batch` in v0.162.0 (45b.2); 45b.1 tracks the current versions. An observability team keeps a deprecation calendar and treats each item as a planned migration, not a surprise.

## 45a.3 SLIs, SLOs, SLAs and error budgets in depth

### Definitions

- **SLI (service level indicator):** a measured ratio of good events to valid events, between 0% and 100%. It has a *specification* (what users experience, such as "checkout requests that succeed") and an *implementation* (where and how it is measured, such as "non-5xx responses at the edge load balancer, from its request counters").
- **SLO (service level objective):** a target for an SLI over a window: "99.9% of valid checkout requests succeed, measured over a rolling 30 days."
- **Error budget:** one minus the SLO, in events or time. At 99.9% and 10 million requests in 30 days, the budget is 10,000 failed requests.
- **Error-budget policy:** the agreed actions when the budget runs low or runs out, signed by engineering and product.
- **SLA (service level agreement):** a contract with consequences, usually service credits, plus legal definitions, exclusions and a claims process. It is normally looser than the internal SLO (see the end of this section).

What a budget means in time, for a full outage at uniform traffic:

| SLO | Per 28 days | Per 30 days | Per 90 days |
|---|---|---|---|
| 99% | 6.72 h | 7.2 h | 21.6 h |
| 99.5% | 3.36 h | 3.6 h | 10.8 h |
| 99.9% | 40.3 min | 43.2 min | 2.16 h |
| 99.95% | 20.2 min | 21.6 min | 64.8 min |
| 99.99% | 4.03 min | 4.32 min | 12.96 min |

For a request-based SLI the budget is counted in requests, so an hour of 50% errors at 3 a.m. costs less than five minutes of 50% errors at peak. That is a feature: it tracks what users experienced.

### Choosing SLIs from the user's perspective

Start from user journeys ("pay for an order", "search returns results", "a dashboard loads", "an alert reaches the on-call engineer"), not from the metrics you happen to have. For each journey ask what the user notices when it is broken, then pick the SLI type.

| SLI type | Good event ÷ valid event | Example implementation | Pitfalls |
|---|---|---|---|
| Availability | Successful responses ÷ valid requests | Request counters by status code at the load balancer or server | Counting 4xx as bad punishes you for client bugs; counting 429 as good hides throttling |
| Latency | Requests faster than a threshold ÷ valid requests | The histogram bucket at the threshold divided by the count | Averages; percentiles of percentiles; a threshold that is not a bucket boundary |
| Freshness | Checks where the data is newer than X ÷ all checks | `time() - pipeline_last_success_timestamp_seconds < 900`, evaluated every minute | Measuring that the job ran rather than how old the data is |
| Correctness | Verified-correct outputs ÷ sampled outputs | Probers with known inputs and expected outputs; reconciliation counts | Samples too small to see a 0.1% defect; stale ground truth |
| Throughput | Minutes at or above the required processing rate ÷ minutes with work queued | `rate(records_processed_total[5m])` compared with demand | Penalizing idle periods; ignoring queue age |
| Durability | Objects readable after write ÷ objects written | Read-back probes on a sample | Aggregate numbers that hide one customer's loss |
| Quality (LLM features) | Responses passing a judge ÷ sampled responses | Judge scores on 1–5% of traffic (chapters 29 and 32) | Judge drift; too few samples per hour to alert on |

### Request-based versus window-based SLIs

A **request-based** SLI is the ratio of good to valid events over the window. It suits high-traffic request-driven services. A **window-based** (time-slice) SLI counts good minutes: a minute is good if, say, the error ratio is below 1% and p99 latency is below 500 ms, and the SLI is good minutes divided by minutes. It suits low-traffic services, freshness and throughput, and most SLAs ("monthly uptime percentage"). The trade-offs: request-based SLIs are dominated by peak hours and say little about a quiet service where one failure in ten requests is 10%; window-based SLIs weigh a quiet 3 a.m. minute the same as a peak minute and depend on an arbitrary per-minute threshold. For low-traffic services the SRE workbook lists four remedies: generate synthetic traffic, combine small services into one monitored unit, change the product so failures are retried or absorbed, or lower the SLO or lengthen the window.

A window-based SLI in PromQL records one "good minute" indicator per minute, then averages it. Minutes with no traffic count as good:

```yaml
# One rule for a rule group evaluated every minute (Prometheus 3.x). Needs a scrape or export
# interval of 15 s or less, so that a 1-minute rate window holds at least four samples.
- record: job:slo_good_minute:bool
  expr: |
    (
      sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5.."}[1m]))
        or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[1m]))
    )
    <= bool
    0.01 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[1m]))
```

The SLI over 30 days is then `avg_over_time(job:slo_good_minute:bool{job="checkout"}[30d])`. The parentheses matter: `or` has the lowest precedence of all PromQL binary operators, so without them the comparison would bind to the right-hand side of `or` only. The `or 0 * ...` clause fills in a zero when no 5xx series exists yet, so the rule produces a value instead of nothing.

### Where to measure

| Measurement point | Sees | Misses | Use it for |
|---|---|---|---|
| Client (browser, mobile, SDK) | What users experience, including DNS, TLS, network and rendering | Requests from clients that never load; noisy devices and clocks | Latency SLIs for user-facing journeys; product analytics |
| Edge or load balancer | Every request that reaches you, including crashed pods and connection resets | Failures before the edge (DNS, ISP); work done after the response | The default for availability and latency of request-driven services |
| Server (application metrics) | Detailed context by route and dependency | Requests that never reached a healthy process | Debugging, per-route SLIs, internal services |
| Synthetic probes | Reachability from outside on a fixed schedule | Real traffic patterns and long-tail inputs | Low-traffic services, freshness checks, SLA evidence |

A common, defensible choice: SLIs from the load balancer or gateway, a synthetic probe for external reachability, client-side latency for the main user journey, and server metrics to debug.

### Windows: rolling versus calendar

Rolling windows (the SRE workbook favors four weeks, so every window contains the same number of weekends; 30 days is the other common choice, and the one the workbook's burn-rate thresholds below assume, so this chapter's checkout examples use it) drive engineering decisions, because a budget spent yesterday still limits risk today. Calendar months suit business reporting and SLAs, but they reset on the first of the month, which invites spending the budget at month end. Use rolling windows for SLOs and alerts, calendar months for SLA reporting, and say so in the SLO document.

### An error-budget policy (example)

> **Service:** checkout. **SLOs:** 99.9% of valid requests succeed, and 99% of valid requests complete within 250 ms, both measured at the edge load balancer over a rolling 30 days. **Normal state:** with more than 25% of either budget remaining, releases follow the usual process. **Budget at risk:** with 25% or less remaining, or after any fast-burn page in the last seven days, each release needs a reliability review and the team reserves a quarter of its sprint capacity for reliability actions. **Budget exhausted:** feature releases stop until the 30-day SLI is back above target; security fixes and changes that reduce risk continue; postmortem action items become the team's top priority. **Single large incident:** an incident that consumes more than 20% of a budget gets a postmortem within five business days. **What counts:** planned maintenance and failures caused by dependencies count against the budget, because users notice them; the response is to change the architecture or the dependency, not to exclude the minutes. **Disputes** go to the engineering director; the policy is reviewed every quarter.

### Critic's additions: SLOs in the release path, and what a canary can detect

An error-budget policy acts after the damage; a canary gate acts during the rollout. Argo Rollouts and Flagger both run Prometheus queries at each canary step and roll back when a check fails, and the check should be the SLI, compared between the canary and the stable version, not a CPU threshold. The statistics decide what a gate can catch. With 5% of 100 requests per second on the canary, it sees 5 requests per second. Telling a 1% error ratio from a 0.1% baseline needs about 1,060 requests per arm, three to four minutes; telling 0.2% from 0.1% needs about 23,500 per arm, about 78 minutes (two-sided test at the 5% level with 80% power). So a canary stops gross regressions within minutes, a latency SLI at 99% detects a doubling with roughly a tenth of the traffic because its bad events are ten times more common, and subtle regressions are left to burn-rate alerts after full rollout. Annotate every deploy in Grafana so dashboards, triage notes and postmortems line changes up with burn.

### Multiwindow, multi-burn-rate alerting

**Burn rate** is the observed error ratio divided by the error budget (one minus the SLO). A burn rate of 1 spends exactly the whole budget by the end of the SLO window; a burn rate of 10 spends it in a tenth of the window. The fraction of the budget spent in time *t* at burn rate *b* is *b × t / T*, where *T* is the SLO window; the time to exhaustion is *T / b*.

The SRE workbook recommends these thresholds for a 30-day window:

| Severity | Long window | Short window | Burn rate | Budget spent when it fires | Error-ratio threshold at 99.9% |
|---|---|---|---|---|---|
| Page | 1 hour | 5 minutes | 14.4 | 2% | 1.44% |
| Page | 6 hours | 30 minutes | 6 | 5% | 0.6% |
| Ticket | 3 days | 6 hours | 1 | 10% | 0.1% |

Both windows of a row must exceed the threshold. The long window gives the alert significance (a real share of the budget is gone); the short window, which the workbook suggests should be about one twelfth of the long one, makes the alert stop firing soon after the problem stops. Many implementations, including Sloth's defaults and the workbook's own example rules, add a second ticket condition at a burn rate of 3 over 1 day with a 2-hour short window. For a 28-day SLO window the same budget shares correspond to burn rates of 13.44, 5.6 and 0.93; most teams keep the 30-day numbers, which page slightly later.

**Worked example.** Checkout has a 99.9% SLO over 30 days (720 hours) and serves 100 requests per second.

- Budget: 100 × 2,592,000 seconds = 259.2 million requests, so 259,200 failures are allowed.
- Burn rate 14.4 for one hour spends 14.4 / 720 = 2% of the budget, which is 5,184 failures out of the hour's 360,000 requests: an error ratio of 1.44%. Left alone, it exhausts the budget in 720 / 14.4 = 50 hours.
- Burn rate 6 for six hours spends 5% (12,960 failures) at an error ratio of 0.6%; exhaustion in five days.
- Burn rate 1 for three days spends 10% (25,920 failures) at 0.1%; exhaustion in 30 days.

**Detection times, worked.** A total outage (100% errors) pushes the 1-hour ratio past 1.44% after 0.0144 × 60 minutes ≈ 52 seconds and the 5-minute ratio past it in about 4 seconds, so the page goes out within a minute or two once scrape and evaluation delays are added. A 2% error ratio needs 0.0144 / 0.02 × 60 ≈ 43 minutes to move the 1-hour average past 1.44% (the 6-hour condition would need 1.8 hours), and by then about 2% of the budget is gone, which is the design intent. A 0.5% error ratio (burn rate 5) never pages: it stays below both page thresholds. It opens a ticket after about 14.4 hours, when both the 1-day ratio passes 0.3% and the 3-day ratio passes 0.1%, by which time 10% of the budget is spent; left alone it would exhaust the budget in six days. That gap is a deliberate trade-off between noise and speed, and you should be able to say so.

**Recording and alerting rules.** The rules below implement the availability SLO for a service whose OpenTelemetry HTTP server metrics arrive in Prometheus as `http_server_request_duration_seconds_*` with a `job` label of `checkout` (OTLP ingestion derives `job` from `service.namespace` and `service.name`). They are valid for Prometheus 3.x and for the Mimir ruler, which uses the same rule format.

```yaml
# slo-checkout.rules.yaml
# SLO: 99.9% of valid checkout requests succeed over a rolling 30 days (error budget 0.001).
# Bad events: 5xx and 429 responses. Rules in one group run in order, so later rules can use earlier ones.
groups:
  - name: slo-checkout-availability
    interval: 30s
    rules:
      - record: job:slo_requests:rate5m
        expr: sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[5m]))

      - record: job:slo_errors:rate5m
        expr: |
          sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[5m]))
            or 0 * job:slo_requests:rate5m{job="checkout"}

      - record: job:slo_errors_per_request:ratio_rate5m
        expr: job:slo_errors:rate5m{job="checkout"} / job:slo_requests:rate5m{job="checkout"}

      - record: job:slo_errors_per_request:ratio_rate30m
        expr: |
          (
            sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[30m]))
              or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[30m]))
          )
          / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[30m]))

      - record: job:slo_errors_per_request:ratio_rate1h
        expr: |
          (
            sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[1h]))
              or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[1h]))
          )
          / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[1h]))

      - record: job:slo_errors_per_request:ratio_rate2h
        expr: |
          (
            sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[2h]))
              or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[2h]))
          )
          / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[2h]))

      - record: job:slo_errors_per_request:ratio_rate6h
        expr: |
          (
            sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[6h]))
              or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[6h]))
          )
          / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[6h]))

      - record: job:slo_errors_per_request:ratio_rate1d
        expr: |
          (
            sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[1d]))
              or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[1d]))
          )
          / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[1d]))

      - record: job:slo_errors_per_request:ratio_rate3d
        expr: |
          (
            sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout", http_response_status_code=~"5..|429"}[3d]))
              or 0 * sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[3d]))
          )
          / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[3d]))

  - name: slo-checkout-availability-alerts
    interval: 30s
    rules:
      - alert: CheckoutAvailabilityBudgetFastBurn
        expr: |
          (
              job:slo_errors_per_request:ratio_rate1h{job="checkout"} > (14.4 * 0.001)
            and
              job:slo_errors_per_request:ratio_rate5m{job="checkout"} > (14.4 * 0.001)
          )
          or
          (
              job:slo_errors_per_request:ratio_rate6h{job="checkout"} > (6 * 0.001)
            and
              job:slo_errors_per_request:ratio_rate30m{job="checkout"} > (6 * 0.001)
          )
        labels:
          severity: page
          slo: checkout-availability
        annotations:
          summary: "checkout is spending its 30-day error budget at 6x the sustainable rate or faster"
          description: "Long-window error ratio {{ $value | humanizePercentage }}; the budget is 0.1% of requests."
          runbook_url: "https://runbooks.example.internal/checkout/availability-slo"

      - alert: CheckoutAvailabilityBudgetSlowBurn
        expr: |
          (
              job:slo_errors_per_request:ratio_rate1d{job="checkout"} > (3 * 0.001)
            and
              job:slo_errors_per_request:ratio_rate2h{job="checkout"} > (3 * 0.001)
          )
          or
          (
              job:slo_errors_per_request:ratio_rate3d{job="checkout"} > (1 * 0.001)
            and
              job:slo_errors_per_request:ratio_rate6h{job="checkout"} > (1 * 0.001)
          )
        labels:
          severity: ticket
          slo: checkout-availability
        annotations:
          summary: "checkout will exhaust its 30-day error budget early at the current error ratio"
          runbook_url: "https://runbooks.example.internal/checkout/availability-slo"

      - alert: CheckoutSLIInputMissing
        expr: absent_over_time(http_server_request_duration_seconds_count{job="checkout"}[15m])
        labels:
          severity: page
          slo: checkout-availability
        annotations:
          summary: "No checkout request metrics for 15 minutes: the SLO alerts above cannot fire"
```

Notes on these rules. The alerts have no `for` clause, because the short window already filters brief spikes; adding `for: 2m` trades two minutes of detection time for slightly fewer flaps. The `or 0 * ...` clauses make the error side read zero instead of empty before the first 5xx response is ever recorded. The 1-day and 3-day ratios read raw counters over long ranges; that is fine for a handful of services, and for hundreds you compute long windows from the 5-minute recordings instead: `sum_over_time(job:slo_errors:rate5m[3d]) / sum_over_time(job:slo_requests:rate5m[3d])` is a ratio of sums and therefore valid, while averaging 5-minute ratios is not. For dashboards, the SLI and the remaining budget over 30 days come from the same recordings:

```promql
# 30-day availability SLI
1 - (
  sum_over_time(job:slo_errors:rate5m{job="checkout"}[30d])
  / sum_over_time(job:slo_requests:rate5m{job="checkout"}[30d])
)

# Share of the 30-day error budget remaining (1 = untouched, 0 = spent, negative = overspent)
1 - (
  (
    sum_over_time(job:slo_errors:rate5m{job="checkout"}[30d])
    / sum_over_time(job:slo_requests:rate5m{job="checkout"}[30d])
  ) / 0.001
)
```

A **latency SLO** works the same way with a different bad-event definition: "99% of requests complete within 250 ms" has a budget of 0.01, so the fast-burn page fires above 14.4% slow requests over an hour. With classic histograms, choose a threshold that is a bucket boundary (the OpenTelemetry HTTP advice includes 0.25 but not 0.3), and remember that Prometheus 3 writes the integer boundaries of scraped histograms with a decimal point (`le="1.0"`), while histograms ingested through OTLP keep `le="1"` (45b.4):

```promql
# Share of slow requests over 5 minutes, classic histogram
1 - (
  sum by (job) (rate(http_server_request_duration_seconds_bucket{job="checkout", le="0.25"}[5m]))
  / sum by (job) (rate(http_server_request_duration_seconds_count{job="checkout"}[5m]))
)

# The same with a native histogram (no _bucket suffix; histogram_fraction interpolates inside buckets)
1 - histogram_fraction(0, 0.25, sum by (job) (rate(http_server_request_duration_seconds{job="checkout"}[5m])))
```

Generators such as Sloth and Pyrra produce these rules from a short SLO specification (45a.5), and they are the right tool once you have more than a few SLOs. Write them by hand once so you can debug what the generators produce.

### Composite availability

**Serial dependencies.** If a request needs every component, availability multiplies: *A = a₁ × a₂ × … × aₙ*. An edge at 99.99%, the checkout service at 99.95%, its database at 99.95% and a payment provider at 99.9% give 0.9999 × 0.9995 × 0.9995 × 0.999 ≈ 99.79%, about 91 minutes of expected unavailability in a 30-day month, more than twice the 43 minutes a 99.9% SLO allows. You cannot promise 99.9% on top of that chain without changing it.

**Parallel (redundant) dependencies.** If any one of several independent replicas suffices, *A = 1 − (1 − a₁)(1 − a₂)…*. Two regions at 99.9% give 99.9999% on paper. In practice failures correlate (the same bad deploy, configuration, DNS provider or certificate reaches both) and the failover mechanism has its own availability: *A ≈ a_failover × (1 − (1 − a₁)(1 − a₂))*. With a failover path at 99.95%, the result is about 99.95%, so the failover path, not the regions, sets the ceiling.

**Soft dependencies** do not belong in the product at all. If recommendations fail and checkout still completes without them, recommendations are a soft dependency. Turning hard dependencies into soft ones (timeouts, fallbacks, caches, asynchronous work) is the main lever for composite availability.

**Latency composes differently.** Serial latencies add, but the p99 of a sum is not the sum of p99s, and under fan-out the tail dominates: a request that waits for 100 parallel calls meets at least one call's p99 in 1 − 0.99¹⁰⁰ ≈ 63% of requests. 29b.4.2 works the table and the mitigations (timeouts, hedged and tied requests).

### Why internal SLOs must be stricter than external SLAs

1. **Time to act before money moves.** You want burn-rate alerts on the internal SLO to fire while there is still room before the SLA is breached.
2. **Measurement differences.** The customer-facing definition (for example, error rates averaged over 5-minute periods at region level) rarely matches your internal SLI exactly; the gap needs headroom.
3. **Window mismatch.** SLAs use calendar months; SLOs use rolling windows.
4. **Dependencies.** Your SLA cannot exceed the composite of your dependencies' commitments without redundancy, and those commitments are themselves SLAs with exclusions.

A healthy ladder looks like this: an external SLA of 99.9% per calendar month, an internal SLO of 99.95% over a rolling 28 days, and measured performance around 99.97%. If measured performance sits well above the SLO for quarters, the SLO is too loose to guide decisions; if it sits below, either the system or the promise has to change.

### Critic's additions: SLOs for the observability platform itself

Platform interviews ask what SLOs the telemetry platform should have, because its users are other engineers during their worst hour. Four SLIs cover most of it, each measured from outside the component it judges:

| SLI | Good events ÷ valid events | How to measure it | Example target |
|---|---|---|---|
| Ingestion availability | Writes accepted ÷ valid writes (a 429 above the tenant's contracted limit is not a failure) | Distributor and gateway request metrics by route and status code (`cortex_request_duration_seconds_count` in Mimir), plus the Collector's refused and failed-send counters | 99.9% over 30 days |
| Freshness and correctness | Probe samples or log lines readable, with the right values, within 2 minutes of the write ÷ probes | A canary that writes and reads back: `mimir-continuous-test` (`mimir_continuous_test_query_result_checks_failed_total` counts wrong answers, not only errors) and Loki Canary, which measures write-to-read latency and missing, duplicate and out-of-order lines | 99% of probes |
| Query success and latency | Queries answered within 10 seconds ÷ valid queries, per tenant | Query-frontend request metrics by route and status code; exclude queries rejected for exceeding limits | 99.5% |
| Alert pipeline | Rule groups evaluated on time and notifications delivered within 2 minutes ÷ all | `prometheus_rule_group_iterations_missed_total` and rule-evaluation failures; `alertmanager_notifications_failed_total` and `alertmanager_notification_latency_seconds`; the end-to-end watchdog through an external heartbeat | 99.9% |

Two design rules make them trustworthy. Evaluate them in the separate meta-monitoring stack, because a Mimir outage would otherwise hide its own SLI. And count wrong data as bad: a query that returns quickly with missing samples is worse than an error, which is why the canaries check results rather than status codes. Published on the platform's status page, these four numbers turn "Grafana is slow" tickets into data.

## 45a.4 What a good SLA looks like, and how to spot a bad one

### The checklist

| Element | A good SLA | Red flag |
|---|---|---|
| SLI definition | Names the event, the success condition (status codes, a latency bound) and what counts as a valid request | "Available", "up" or "operational" with no definition |
| Measurement method and source | Says where it is measured (load-balancer logs, probes), at what granularity (per 5-minute period, per minute) and how the customer can see the data | "As determined by the provider's internal monitoring" |
| Exclusions | Specific and bounded: maintenance with notice, a cap and blackout hours; customer-caused failures; force majeure as defined in the master agreement | Open-ended maintenance; "emergency maintenance"; "degraded performance"; "third-party providers"; a minimum outage length |
| Scope | Lists the components, regions and tiers covered, and whether preview features are excluded | Silent about which APIs count; covers the console but not ingestion or alert delivery |
| Window | Calendar month in a stated time zone, with the formula for the monthly figure | Undefined period, or a figure that mixes periods |
| Remedies and claims | Credit tiers, a cap, how to claim, a deadline, a response time; a termination right for chronic failure | Discretionary credits; "up to 5%"; no process; credits as the sole remedy with no exit |
| Achievability | Consistent with the provider's architecture and dependencies (a 99.99% promise from a single region deserves questions) | A number more ambitious than the dependencies allow |
| Customer obligations | Stated plainly (retries with back-off, multi-zone deployment for region-level SLAs) | Hidden in definitions, or so broad that almost any failure becomes the customer's |
| Reporting | Monthly SLI reports and root-cause reports for major incidents | No reporting; status page only |
| Change control | Service levels cannot be reduced during the term | "Provider may update this SLA at any time" |
| Alignment | Your internal SLO is stricter than what you sell; what you buy feeds your composite availability | An SLA written by sales with no SLO behind it |

**Red flags at a glance:** "commercially reasonable efforts" as the whole promise, with no remedy triggered by a measured number; an undefined "available"; measurement only by the provider's internal monitoring; open-ended or "emergency" maintenance; "degraded performance" excluded; a minimum outage length that swallows real outages; third-party failures excluded wholesale; credits "at the provider's discretion" or "up to" a small percentage; no claim process or deadline; no exit for chronic failure; the right to change the SLA at any time; a headline number the architecture cannot support.

### A deliberately bad SLA, critiqued and rewritten

> **Provider Monitoring Cloud: Service Level Agreement (bad example).** (1) Provider will use commercially reasonable efforts to make the Service available 99.99% of the time. (2) Availability is determined by Provider's internal monitoring. (3) Downtime excludes scheduled maintenance, emergency maintenance, degraded performance, issues caused by third-party providers, and any period shorter than 15 minutes. (4) If availability falls below the target in a month, Customer may request a credit of up to 5% of the monthly fee, issued at Provider's sole discretion. (5) Provider may update this SLA at any time.

What is wrong with it:

1. **"Commercially reasonable efforts"** with nothing measurable attached turns the promise into an intention. The phrase alone is not the problem: AWS's EC2 SLA uses it too, but its credits are triggered by measured uptime whatever the effort. Here the only remedy is discretionary, so nothing is guaranteed.
2. **"Available" is undefined.** Does the login page count? Ingestion? Queries? Alert delivery, the one thing a monitoring customer needs during an outage?
3. **The measurement is invisible.** The customer cannot verify or dispute it.
4. **The exclusions swallow the promise.** Unlimited maintenance; "emergency maintenance" is anything; "degraded performance" means a query that takes 90 seconds counts as up; "third-party providers" includes the provider's own cloud. A 99.99% monthly target allows 4.3 minutes of downtime, so excluding every outage shorter than 15 minutes means a month of 14-minute outages every hour would still count as compliant.
5. **The remedy is discretionary and tiny.** "Up to 5%" at the provider's discretion, with no claim process and no deadline.
6. **Unilateral change** makes the rest irrelevant.
7. **The number itself is suspicious.** A 99.99% commitment without multi-region architecture and with third-party failures excluded says the number was chosen for the sales deck.

A rewritten version:

> **Provider Metrics Service: Service Level Agreement (example).**
> 1. **Scope.** This SLA covers the Metrics Ingestion API, the Query API and Alert Notification Delivery in generally available regions. Preview features are excluded.
> 2. **Service levels**, per calendar month in UTC. *Ingestion:* Monthly Ingestion Success of at least 99.9%. For each 5-minute period, Ingestion Success is the number of valid write requests that received a 2xx response within 10 seconds divided by all valid write requests; Monthly Ingestion Success is the average over the 5-minute periods in which the Customer sent at least one request. *Query:* Monthly Query Success of at least 99.9%, defined the same way for valid query requests answered with 2xx within 30 seconds. *Alert delivery:* at least 99.5% of notifications generated by the service are handed to the configured integration within 2 minutes of the evaluation that triggered them.
> 3. **Valid requests** conform to the documentation, are authenticated and are within the Customer's contracted limits. A 429 response caused by exceeding contracted limits is not a failure; a 429 response below those limits is a failure.
> 4. **Measurement** uses the Provider's load-balancer logs. The Provider publishes a monthly SLI report per customer within five business days of month end and keeps the underlying data for 13 months. The Customer may submit its own client-side logs as evidence.
> 5. **Exclusions:** (a) scheduled maintenance announced at least five business days ahead, at most 4 hours per quarter, never between 08:00 and 20:00 local time on business days in the affected region; (b) failures caused by the Customer's systems or by requests that violate the documentation; (c) force majeure as defined in the Agreement. Failures of the Provider's subcontractors and cloud providers are not excluded.
> 6. **Service credits**, per affected component, as a share of that component's monthly fee: 10% below target but at least 99.0%; 25% below 99.0% but at least 95.0%; 50% below 95.0%. Credits are capped at 50% of the monthly fee.
> 7. **Claims** are filed through the support portal within 30 days after the affected month, naming the component and region. The Provider answers within 15 business days.
> 8. **Chronic failure.** If Monthly Ingestion Success is below 99.0% in any three months of a rolling six-month period, the Customer may terminate the affected service without penalty.
> 9. **Incident reports.** For any incident that consumes more than 10% of a monthly target, the Provider publishes a root-cause report within ten business days.
> 10. **Changes.** The Provider will not reduce these service levels during the subscription term.

### How real cloud SLAs are structured

Two current examples show the pattern, and both repay a careful reading.

**Amazon EC2 (the Amazon Compute SLA, last updated 25 May 2022).** It has two commitments, each worded as "commercially reasonable efforts" and each backed by credits computed from measured uptime. The *Region-Level* SLA promises a Monthly Uptime Percentage of at least 99.99%, where a region counts as unavailable only when all of your running instances deployed in two or more Availability Zones concurrently have no external connectivity; credits are 10% of the monthly charge below 99.99% (down to 99.0%), 30% below 99.0% (down to 95.0%) and 100% below 95.0%. The *Instance-Level* SLA promises 99.5% per instance, with the same 10%, 30% and 100% tiers at 99.0% and 95.0%, and AWS does not charge for a single instance that is unavailable for more than six minutes of a clock hour. Claims must be filed by the end of the second billing cycle after the incident, with dates, affected resources and request logs; credits apply only against future payments; exclusions cover factors outside AWS's reasonable control, the customer's own actions, equipment and software, and suspension of service.

**Google Cloud Storage (SLA last modified 1 April 2026).** Standard storage promises at least 99.95% monthly uptime in multi-region and dual-region locations and 99.9% in regional locations (lower figures apply to the colder classes and to two named regions). The error rate is the share of valid requests answered with an HTTP 5xx status, and the monthly uptime percentage is 100% minus the average of the error rates measured over each 5-minute period in the month. Customers must back off after errors, starting at one second and doubling up to 32 seconds, and repeated requests that ignore the back-off do not count toward the error rate. Credits for multi-region Standard storage are 10% from 99.0% to just below 99.95%, 25% from 95.0% to below 99.0% and 50% below 95.0%; the customer must notify support within 30 days of becoming eligible, and credits are capped at 50% of the monthly bill for the service. Pre-GA features are excluded.

**What to take from them.** The unit of measurement decides what you can claim: a workload in a single Availability Zone can never make EC2 "Region Unavailable", so the region-level 99.99% does not protect it. Error-rate SLIs averaged over 5-minute periods mean a short, total outage and a long, partial one can cost the same. Credits are small relative to business loss: 10% of a \$20,000 monthly bill is \$2,000, against whatever an hour of checkout downtime costs you. Customer obligations (multi-zone deployment, exponential back-off) are part of the contract. Both are good templates for definitions, measurement windows and credit tiers; checked against the list above, neither offers a chronic-failure exit or a monthly SLI report, so the customer carries the burden of measuring and claiming.

### Teaching others to spot a hollow SLA: the ten-minute review

1. Read the definitions before the numbers: what is an error, a valid request, a period, unavailability?
2. Find the measurement source and ask whether you can see the data.
3. Convert the target into minutes or failed requests per month and per incident.
4. List every exclusion and estimate how much of a real outage it would remove.
5. Compute the credit for a plausible bad month and compare it with your cost of that month.
6. Check the claims process and deadline, and put the deadline in a calendar.
7. Compare the commitment with the provider's architecture and with your own dependency chain (composite availability above).
8. Check for change rights and chronic-failure exits.
9. Write down the SLO you will monitor internally for this dependency, measured from your side.
10. Decide what you would do if the provider failed for a day, because the SLA will not do it for you.

## 45a.5 Setting the technical agenda

### An observability strategy on one page

A strategy is a short document that names the problem in numbers, the principles that guide decisions, the target state and how progress will be measured. Principles that hold up well:

- OpenTelemetry for all new instrumentation; vendor-neutral by default, so backends can change without re-instrumenting.
- Every tier-1 service has SLOs and burn-rate alerts; a page without an SLO or a named failure mode behind it needs a written justification.
- Telemetry has a budget: every team can see its active series, ingested gigabytes and cost (chapter 47).
- Dashboards, alerts, SLOs and Collector pipelines are code: reviewed, owned and versioned.
- High-cardinality context lives in traces and logs; metrics carry bounded aggregates.
- The monitoring path is in a different failure domain from what it monitors.

### A maturity model

| Dimension | Level 1: reactive | Level 2: instrumented | Level 3: SLO-driven | Level 4: proactive | Level 5: optimized |
|---|---|---|---|---|---|
| Instrumentation | Host metrics and ad hoc logs | Metrics and logs per service; some tracing | OpenTelemetry everywhere; context propagated end to end | Semantic conventions enforced in CI; profiles for key services | Telemetry contracts versioned with the code |
| Alerting | Threshold alerts on causes | Alerts with owners and runbooks | SLO burn-rate pages; cause alerts as tickets | Alert precision tracked and reviewed | Paging volume within an agreed budget per team |
| Incident response | Heroics; customers report outages | On-call rotations and templates | Blameless postmortems with tracked actions | Game days; error-budget policies enforced | Learning reviews feed the roadmap |
| Cost and governance | Nobody knows the bill | Bill known per backend | Showback per team; limits per tenant | Budgets and usage-based pruning | Unit cost per request falling as traffic grows |
| Self-service | Tickets to the platform team | Templates and documentation | Golden-path onboarding in under a day | SLOs and dashboards generated from specs | Platform adoption is the default, exceptions are rare |
| AI assistance | None | Ad hoc chat use | Skills for queries and triage with eval sets | Read-only investigation agents measured on replayed incidents | Agents in the loop with approvals and audited actions |

Score each team or service on each row, publish the distribution, and pick the two rows where moving one level buys the most.

### Writing an RFC

A useful RFC template has these sections: title, author, status and decision date; context and problem, with data; goals and non-goals; the proposal; alternatives considered, including doing nothing; failure modes, rollback and migration; cost in infrastructure and people; security and privacy; how success will be measured and what would make you stop; open questions. Habits that get RFCs accepted: lead with the problem in numbers ("40% of pages last quarter required no action"); keep one decision per RFC; show it to the people most likely to object before it is public; set a two-week comment window; record the outcome as an architecture decision record so the next person knows why.

### Building a roadmap

Plan in now, next and later. Sequence by risk and dependency: make the platform safe (limits, meta-monitoring, upgrades) before adding features; drive adoption before expanding scope; ship one visible win each quarter. Reserve 20–30% of capacity for operations and upgrades, because migrations such as Mimir's move to ingest storage or Tempo 3's new architecture are quarter-sized projects. Express each quarter as outcomes ("SLO coverage of tier-1 services from 30% to 70%"), not outputs ("build an SLO service").

### Proposing novel, broad ideas responsibly

Write each idea as a hypothesis, the smallest experiment that tests it, the metric that decides, a kill criterion and a cost. Examples that fit this role:

- **SLO-as-code platform.** Teams declare SLOs in a short spec in their repository (Sloth's `prometheus/v1` format, Pyrra's `ServiceLevelObjective` resource, or the OpenSLO specification); CI generates recording rules, burn-rate alerts, dashboards and monthly budget reports. Hypothesis: tier-1 SLO coverage rises from 30% to 90% in two quarters and page precision improves. Experiment: five teams for six weeks. Kill criterion: fewer than three teams keep using it after the pilot.
- **Adaptive telemetry and cost controls.** Per-team cardinality budgets enforced in the Collector and in tenant limits; usage-based aggregation that drops labels nobody queries (the idea behind Grafana Cloud's Adaptive Metrics); log levels and trace sampling that rise automatically while an SLO is burning and fall back afterwards. Metric: cost per million requests at constant incident-detection performance.
- **Trace-based testing.** Run integration tests with tracing on and assert on the trace: "checkout makes at most three database calls", "no span reaches the legacy pricing service", "the payment call carries the idempotency key attribute". It catches N+1 queries and accidental dependencies before production. Metric: regressions caught in CI versus found in production.
- **AI-assisted investigations.** A read-only agent with access to metrics, logs and traces that produces cited hypotheses when a page fires, evaluated on replayed historical incidents before anyone relies on it (chapter 45c).
- **Telemetry contracts.** Semantic-convention registries for your own attributes and metrics, defined and checked in CI with OpenTelemetry's Weaver, so a renamed attribute fails a build instead of breaking a dashboard. Metric: dashboard and alert breakages caused by telemetry changes, per quarter.

### Measuring the observability program

| Metric | Definition | Notes |
|---|---|---|
| Time to detect | From the start of user impact to the first page or detection | Report the median and 90th percentile; incident durations are heavily skewed, so a mean is dominated by a few long incidents |
| Time to mitigate | From detection to user impact ending | More actionable than time to resolve, which includes follow-up work |
| Alert precision | Pages that led to action ÷ all pages | Review weekly; below about 50% means the pager is training people to ignore it |
| Detected by humans first | Share of incidents first reported by customers or support | The best available proxy for recall |
| Pages per on-call shift | Including the share outside working hours | A health metric for people, not only systems. Google's SRE book allows at most two incidents per 12-hour shift, because each takes about six hours of diagnosis, remediation and follow-up |
| SLO coverage | Share of tier-1 services with SLOs, burn-rate alerts and runbooks | Also track the share whose SLOs were reviewed this quarter |
| Trace coverage | Share of services emitting traces; share of requests with unbroken context end to end | Broken traces usually mean a queue or a proxy that drops headers |
| Platform SLOs | Ingestion success, freshness and correctness, query success and latency, alert delivery | The observability platform needs SLOs too (45a.3) |
| Unit cost | Cost per GB of logs ingested, per 1,000 active series per month, per million spans; telemetry cost as a share of infrastructure cost | Show it per team (chapter 47) |

A worked example of a quarter's report: pages fell from 120 to 38 a month after cause-based alerts were replaced with burn-rate alerts, and the share leading to action rose from 35% (42 of 120) to 79% (30 of 38); median time to detect fell from 14 to 6 minutes; log ingestion fell from 3.0 to 1.2 TB per day after debug logs were sampled and health-check lines dropped, which at an assumed \$0.50 per GB is about 1,800 GB × \$0.50 × 30 ≈ \$27,000 a month.

## 45a.6 Communication

### Incident communication

Roles: an **incident commander** who coordinates and decides, an **operations lead** who works the problem, a **communications lead** who writes updates, and a scribe who keeps the timeline. Tie severity to SLO impact (for example, SEV1 when a tier-1 SLO's fast-burn page fires and users are affected) and fix an update cadence per severity (every 30 minutes for SEV1, hourly for SEV2) so people stop asking. A status update has four parts: what we know, who is affected and how, what we are doing, and when the next update comes. Separate facts from hypotheses, and never guess at causes in external updates.

> **Update 14:20 UTC, SEV1, checkout errors.** Since 13:52 UTC about 6% of checkout attempts in the EU region fail with an error page; other regions are unaffected. We have rolled back the 13:40 release of the payment service and are watching error rates recover. Customers can retry; failed attempts were not charged. Next update at 14:50 UTC or sooner if the situation changes.

### Blameless postmortems

Google's SRE book lists the usual triggers: user-visible downtime or degradation beyond a threshold, data loss of any kind, on-call intervention (a rollback or rerouting), resolution time above a threshold, and a monitoring failure, which usually means a person discovered the incident instead of an alert. A structure that works:

1. **Summary** in three sentences: what happened, impact, what fixed it.
2. **Impact** in numbers: duration, users or requests affected, error budget consumed, money if known.
3. **Timeline** in UTC, from the triggering change to full recovery, including when each signal appeared and when people noticed it.
4. **Detection**: how it was detected, how long that took, and what would have detected it sooner.
5. **Response and recovery**: what was tried, what worked, what slowed the team down.
6. **Contributing factors**: the conditions that combined, without naming people as causes; ask why the system made the mistake easy.
7. **What went well** and **where we got lucky**.
8. **Action items**, each with an owner, a priority and a due date, split into prevent, detect and mitigate.

The blameless part is practical, not polite: people who fear blame hide the details you need. The SRE book's point is that you cannot fix people, but you can fix the systems and processes that are supposed to support them. Review postmortems in a regular forum, track action items to completion, and look across postmortems quarterly for repeated contributing factors.

### Reviewing RFCs

Read for the problem first; if the problem is not real or not quantified, nothing else matters. Then ask five questions: is there a simpler alternative; how does it fail and how is it rolled back; who owns it in a year and what does it cost; what are the security and privacy consequences; how will we know it worked. Label comments as blocking or non-blocking, propose wording rather than only objecting, and summarize the decision at the end of the thread.

### Teaching others: a 2.5-hour SLO workshop

| Time | Activity | Output |
|---|---|---|
| 0:00–0:15 | Why SLOs: two incidents where cause-based alerts failed | Shared motivation |
| 0:15–0:45 | Map the team's two most important user journeys | Journeys with what users notice when they break |
| 0:45–1:15 | Choose SLIs and measurement points; write the specification and the implementation | Two SLIs per journey |
| 1:15–1:30 | Break | |
| 1:30–1:55 | Pick targets from the last 90 days of data; compute budgets in requests and minutes | Draft SLOs with budgets |
| 1:55–2:15 | Burn-rate alerts: work the arithmetic, then write a Sloth or Pyrra spec and generate the rules | Generated rules in a pull request |
| 2:15–2:30 | Draft an error-budget policy and agree who signs it | Policy draft and owner |

Send pre-work (a dashboard of the service's request rates and errors), use the team's own data rather than toy examples, and hold office hours two weeks later to review the pull requests. Measure the workshop by outcomes: how many SLOs reach production within 30 days, and how many teams use their error-budget policy in a release decision within a quarter.

## 45a.7 A 30-60-90-day plan

**Days 1–30: learn and stabilize.** Inventory the estate in numbers: services, active series, samples per second, log GB per day, spans per second, cost per backend, top 20 alerts by volume, SLO coverage, the last ten postmortems. Check meta-monitoring first (is there a watchdog, does paging work if the cluster is down, how far behind is remote write right now). Shadow on-call for two weeks. Hold twenty short conversations with users of the platform: what they look at during incidents, what they gave up on. Take two or three quick wins with the owners' agreement, such as deleting or downgrading the three noisiest alerts and closing one data-loss risk (an exporter queue without persistence, a Collector without `memory_limiter`). Deliverable: a "state of observability" document with numbers and the top five risks.

**Days 31–60: plan and prove.** Write the strategy one-pager and score the maturity model. Write the RFC for the first agenda item (for example, SLO-as-code with burn-rate alerting, or cardinality budgets with tenant limits) and pilot it with two or three teams. Run the first SLO workshop. Build a first AI skill for a narrow job, such as writing and explaining PromQL against your metric catalog, with a 20-case eval set and a no-skill baseline (chapter 45c). Deliverable: pilot results with before-and-after numbers.

**Days 61–90: deliver and scale.** Get the roadmap approved with quarterly outcomes. Ship the platform guardrails (per-tenant limits, alerts on pipeline lag and refused data, a deprecation calendar). Publish pilot results: page precision, time to detect, SLO coverage. Distribute the skill through a plugin marketplace or organization provisioning with usage telemetry and a changelog. Deliverable: the next quarter's plan and a short talk to engineering leadership.

The sentence to have ready, in the form the interview-prep skill in the kit uses: "In 90 days I will have SLO-based paging live for the ten tier-1 services, measured by page precision above 70% and a median time to detect under five minutes, with the platform's own ingestion and query SLOs published."

## 45a.8 Interview question bank

1. **What is the difference between an SLI, an SLO and an SLA?** An SLI is a measured ratio of good events to valid events; an SLO is the target for that ratio over a window; an SLA is a contract with consequences, deliberately looser than the internal SLO so the team can act before money moves.

2. **A service has a 99.9% SLO over 30 days and serves 50 requests per second. What is the budget, and what should page within an hour?** 50 × 2,592,000 = 129.6 million requests, so 129,600 failures. Page at a burn rate of 14.4, when both the 1-hour and 5-minute error ratios exceed 1.44%: that is 2% of the budget, 2,592 failures out of 180,000 requests in the hour.

3. **Why not page when the error rate exceeds 1% for five minutes?** A fixed threshold ignores how much budget is at stake: short spikes page for nothing and slow leaks never page. Burn-rate alerts tie paging to budget consumption; the long window provides significance, and the short window makes the alert clear quickly after recovery.

4. **What SLIs would you choose for a data pipeline?** Freshness (age of the newest correctly processed data, measured where it is consumed), correctness (verified samples or reconciliation counts), and coverage (share of input records processed). Measuring that the job ran is not enough.

5. **A dashboard shows the average of each pod's p99 latency. What is wrong?** Percentiles cannot be averaged; the fleet p99 can be far from the mean of per-pod p99s. Sum the histogram buckets across pods (keeping `le`) and take the quantile of the sum, or use native histograms.

6. **Prometheus memory doubled overnight. Walk me through it.** Check `prometheus_tsdb_head_series` and the series creation rate; find the target with `scrape_series_added` and the top label pairs on the TSDB status page; correlate with deploys. Stop the growth (drop the label with `metric_relabel_configs`, roll back, set `sample_limit`); memory falls only after the next head compaction, about two hours later, or a restart. Then add a review gate for new labels.

7. **Design tail sampling for 50,000 spans per second.** Agents export through a load-balancing exporter keyed on trace ID to a gateway tier that runs tail sampling, so all spans of a trace meet in one place. At 25 spans per trace that is 2,000 traces per second; a 30-second decision wait holds 60,000 traces, roughly 1.5 GB at 1 KB per span, spread over the replicas. Derive span metrics before sampling, keep errors, slow traces and key tenants, plus a small random baseline, and plan for trace splitting when the gateway scales.

8. **How do you monitor the monitoring?** A watchdog alert that always fires and pages through an external dead-man's switch when it stops; a small meta-monitoring stack in another failure domain; alerts on remote-write lag, refused and dropped telemetry, rule-evaluation failures and notification failures; absence alerts on every SLI input; and a synthetic probe that writes a sample and reads it back.

9. **Metrics, logs or traces: which for what?** Metrics for bounded aggregates, alerting and long retention; traces for request paths, latency attribution and high-cardinality context; logs for discrete events and details; profiles for code-level resource use. Link them with exemplars and trace IDs so an alert leads to a trace, its logs and its profile.

10. **What makes an SLA hollow?** An undefined SLI, a measurement the customer cannot see, open-ended exclusions, discretionary credits, unilateral change rights, and a target the provider's architecture cannot support.

11. **Four hard dependencies each promise 99.9%. What can you promise?** About 99.6% (0.999⁴), before your own failures. To offer 99.9% you need redundancy, fallbacks that make some dependencies soft, or better dependencies, and your internal SLO must sit above whatever you sell.

12. **How would you get forty teams to adopt OpenTelemetry and SLOs?** Make the right way the easy way: injected auto-instrumentation, service templates, SLO specs that generate rules and dashboards. Start with two willing teams, publish their numbers, run workshops and office hours, and get an engineering leader to sign the error-budget policy. Mandates work only after the tooling is good.

13. **Tell me about a technical direction you set.** Use STAR (chapter 38) with numbers: the problem (for example, 120 pages a month with 35% precision), the RFC and the pilot, how you handled objections, and the result (38 pages a month at 79% precision, median detection from 14 to 6 minutes).

14. **How do you measure an observability program?** Median and 90th-percentile time to detect and to mitigate, alert precision, the share of incidents customers found first, SLO and trace coverage, the platform's own SLOs, and unit cost per GB, per thousand active series and per million spans.

15. **An alert fires thirty times a week and nobody acts. What do you do?** Find the owner and the failure it protects against. If it protects nothing users would notice, delete it or make it a ticket; if it does, replace it with a burn-rate alert or fix its condition. Then track its precision.

16. **What changed in Prometheus 3 that can break existing queries?** Range selectors are now left-open; `le` and `quantile` values of scraped histograms and summaries are normalized to floats (`le="1.0"`), while OTLP-ingested data keeps the translator's formatting (`le="1"`; 45b.3); `.` in regular expressions matches newlines; `holt_winters` became `double_exponential_smoothing` behind a feature flag; scrapes fail on missing or wrong content types unless a fallback protocol is set; retention flags are deprecated in favor of the configuration file. Native histograms are stable since 3.8 but still need `scrape_native_histograms` to be ingested.

17. **A trace shows a child span starting before its parent. Why?** Clock skew: each span is timestamped by its own host's clock. Fix time synchronization and alert on offset; do not compute cross-host latencies from timestamps; rely on each side's measured durations.

18. **How do you roll out a semantic-convention change across 200 services?** Inventory every consumer (dashboards and rules in git, query logs), dual-emit or translate at the Collector, migrate queries, keep both names for one retention period, then remove the old ones and add a CI check so they do not come back.

19. **How do you keep a postmortem blameless when someone clearly made a mistake?** Ask why the system made the mistake easy and hard to catch: missing guardrails, confusing tools, no test, time pressure. Fix those. The person's account is the most valuable evidence you have, and blame makes it disappear.

20. **Where would you use AI during on-call, and where not?** Read-only investigation help that cites the query behind every claim, incident summaries, and drafts of updates and postmortems. Not autonomous changes without approval. Evaluate any agent on replayed incidents first and track its hallucinated-evidence rate (chapter 45c).

21. **What SLOs would you set for the observability platform?** Ingestion availability, freshness and correctness measured by a write-and-read-back canary, query success within a latency bound per tenant, and alert delivery end to end, all evaluated from a meta-monitoring stack in another failure domain (45a.3).

22. **Your canary takes 5% of traffic. Will it catch an error ratio that doubles from 0.1% to 0.2%?** Not quickly: at 5 requests per second it needs about 23,500 requests per arm, well over an hour, to tell the two apart. It catches a jump to 1% in a few minutes. Gate canaries on gross regressions and on the latency SLI, and rely on burn-rate alerts for subtle ones.

**Interview line:** *"I run the telemetry pipeline as a production system with its own SLOs, limits and failure modes, and I page people only when users' error budgets burn: multiwindow burn-rate alerts on SLIs measured where users feel them, internal SLOs stricter than anything we sell, and SLAs I have read line by line for definitions, measurement and exclusions."*

## Sources

- [Google SRE Workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) (burn-rate table and windows; accessed October 2026)
- [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/) (SLI menu, measurement points, rolling windows, policies; accessed October 2026)
- [Google SRE Book: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) (postmortem triggers; accessed October 2026)
- [Google SRE Book: Being On-Call](https://sre.google/sre-book/being-on-call/) (six hours per incident, two incidents per 12-hour shift; accessed October 2026)
- [Argo Rollouts: Analysis and progressive delivery](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/) and [Flagger: Metrics analysis](https://docs.flagger.app/usage/metrics) (accessed October 2026)
- [Grafana Mimir: mimir-continuous-test](https://grafana.com/docs/mimir/latest/manage/tools/mimir-continuous-test/) and [Grafana Loki: Loki Canary](https://grafana.com/docs/loki/latest/operations/loki-canary/) (accessed October 2026)
- [Prometheus: Storage](https://prometheus.io/docs/prometheus/latest/storage/) (blocks, WAL, compaction, retention, bytes per sample; accessed October 2026)
- [Prometheus: Command-line flags](https://prometheus.io/docs/prometheus/latest/command-line/prometheus/) (query limits, deprecated retention flags; Prometheus 3.14, accessed October 2026)
- [Prometheus: Migration from 2.x to 3.0](https://prometheus.io/docs/prometheus/latest/migration/) (accessed October 2026)
- [Prometheus: Querying basics](https://prometheus.io/docs/prometheus/latest/querying/basics/) (left-open ranges, lookback; accessed October 2026)
- [Prometheus: Recording rule naming](https://prometheus.io/docs/practices/rules/) (accessed October 2026)
- [Prometheus: Native histograms specification](https://prometheus.io/docs/specs/native_histograms/) (stable since v3.8.0; accessed October 2026)
- [Prometheus: Using Prometheus as an OpenTelemetry backend](https://prometheus.io/docs/guides/opentelemetry/) (accessed October 2026)
- [Prometheus releases on GitHub](https://github.com/prometheus/prometheus/releases) (3.13 LTS, July 2026; 3.14, August 2026)
- [OpenTelemetry semantic conventions: HTTP metrics](https://opentelemetry.io/docs/specs/semconv/http/http-metrics/) (advisory buckets; accessed October 2026)
- [OpenTelemetry semantic conventions: HTTP migration guide](https://opentelemetry.io/docs/specs/semconv/non-normative/http-migration/) (`OTEL_SEMCONV_STABILITY_OPT_IN`; accessed October 2026)
- [OpenTelemetry blog: Kubernetes attributes processor reaches v1.0.0](https://opentelemetry.io/blog/2026/k8s-attributes-processor-v1/) (16 September 2026)
- [Thanos: Compactor and downsampling](https://thanos.io/tip/components/compact.md/) (accessed October 2026)
- [Grafana Mimir 3.0 release notes](https://grafana.com/docs/mimir/latest/release-notes/v3.0/) and [GitHub release](https://github.com/grafana/mimir/releases/tag/mimir-3.0.0) (31 October 2025)
- [Grafana Mimir: Configure high-availability deduplication](https://grafana.com/docs/mimir/latest/configure/configure-high-availability-deduplication/) (accessed October 2026)
- [Grafana Tempo 3.0 release notes](https://grafana.com/docs/tempo/latest/release-notes/v3-0/) (May 2026) and [3.1 release notes](https://grafana.com/docs/tempo/latest/release-notes/v3-1/) (29 September 2026)
- [OpenTelemetry Collector changelog](https://github.com/open-telemetry/opentelemetry-collector/blob/main/CHANGELOG.md) (v0.158.0 queue-based batch processor, v0.162.0 `queue_batch` rename)
- [Grafana Agent documentation: end of life on 1 November 2025](https://grafana.com/docs/agent/latest/)
- [Grafana Loki: Promtail end of life on 2 March 2026](https://grafana.com/docs/loki/latest/send-data/promtail/)
- [Grafana Loki 3.7 release notes](https://grafana.com/docs/loki/latest/release-notes/v3-7/) (March 2026)
- [Grafana Cloud Adaptive Metrics](https://grafana.com/docs/grafana-cloud/adaptive-telemetry/adaptive-metrics/) (accessed October 2026)
- [OpenAI: 11 December 2024 incident report](https://status.openai.com/incidents/ctrsv3lwd797) and [TechCrunch coverage](https://techcrunch.com/2024/12/13/openai-blames-its-massive-chatgpt-outage-on-a-new-telemetry-service) (December 2024)
- [Datadog: 8 March 2023 incident postmortem](https://www.datadoghq.com/blog/2023-03-08-multiregion-infrastructure-connectivity-issue/)
- [AWS: Amazon Compute Service Level Agreement](https://aws.amazon.com/compute/sla/) (last updated 25 May 2022; accessed October 2026)
- [Google Cloud Storage SLA](https://cloud.google.com/storage/sla) (last modified 1 April 2026)
- [Sloth](https://github.com/slok/sloth), [Pyrra](https://github.com/pyrra-dev/pyrra) and [OpenSLO](https://github.com/OpenSLO/OpenSLO) (accessed October 2026)
