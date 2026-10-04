# Distributed systems design questions at Google for AI engineers

Eight questions of the kind a Google system-design round gives an AI or Applied AI engineer, each answered the way the round is scored: requirements and numbers first, a high-level design, two deep dives, failure modes, and the trade-offs said out loud. Every design names the Google Cloud component you would use and the Google-internal system it descends from, because interviewers at Google think in those systems (Borg, Spanner, Bigtable, Colossus, Zanzibar, Maglev, Dapper, Monarch, Pathways) and notice when a candidate does too. Chapter 40 of the book has the application-level exercises (RAG assistant, support agent, voice, extraction, agent platform, the BigQuery data agent); this document covers the infrastructure underneath them. Dated October 2026.

## 1. How the round is run and scored

Forty-five minutes, one open problem, a whiteboard or a shared doc. The interviewer scores four things: whether you turned an ambiguous ask into requirements with numbers; whether the design is sound and complete at the level of components and data flow; whether it scales, degrades and recovers, with the bottleneck identified; and whether you can state trade-offs rather than hide them. For AI engineers a fifth line appears on the feedback form: whether you treat the model as a component with a cost, a latency distribution, a failure rate and an evaluation, not as magic.

**The method, in the order you speak it.**

1. *Clarify* (3 minutes): users, scale, latency target, consistency needs, what "correct" means, what already exists.
2. *Numbers in the corner* (3 minutes): QPS peak and average, data volume and growth, tokens per request, p50 and p99 latency, cost per unit. Chapter 40.1 lists the four calculations; write them before the first box.
3. *High-level design* (10 minutes): ingress, compute, state, async, model, observability. Name the product and the internal system it maps to.
4. *Deep dives* (20 minutes): the two components the interviewer steers you to, usually the state layer and the model-serving layer.
5. *Failure, scale, cost* (8 minutes): what breaks first, what you shed, what you cache, what a region loss does, what it costs per request, and the SLO with its error budget.

**Vocabulary that signals you have run things at Google scale.** SLO and error budget (the SRE book); tail latency and hedged requests ("The Tail at Scale"); consistent hashing and Maglev for load balancing; Spanner's TrueTime and external consistency versus Bigtable's single-row atomicity; Colossus as the file system under Cloud Storage; Borg as the ancestor of Kubernetes and GKE; Dapper as the ancestor of Cloud Trace; Monarch as the ancestor of Cloud Monitoring; Zanzibar as the ancestor of every relationship-based authorisation store; the Dataflow model (MillWheel and Flume) for exactly-once streaming with watermarks; Pathways for multi-pod training and serving on TPUs.

## 2. Numbers to carry in

| Quantity | Order of magnitude | Why it matters |
|---|---|---|
| Round trip inside a region | 0.5 ms | a design with ten sequential service hops already spends 5 ms |
| Cross-continent round trip | 150 ms | multi-region synchronous writes cost this per commit |
| SSD random read | 100–200 µs; Bigtable or Memorystore point read 1–10 ms | cache tiers exist because of this gap |
| LLM time to first token | 200–800 ms for a warm prefix; seconds for a cold 100k-token prompt | prefill is the latency; prefix caching is the lever |
| LLM decode rate per stream | 50–150 tokens per second | a 400-token answer streams for 3–8 seconds whatever you do |
| Aggregate throughput, one accelerator, 70B-class model | roughly 1,000–3,000 tokens per second with continuous batching | sizes the serving fleet; utilisation decides the bill |
| Embedding throughput | thousands of chunks per second per accelerator | a billion chunks is hours on a fleet, not minutes |
| Approximate nearest-neighbour query over 1B vectors | 5–20 ms at 95%+ recall with ScaNN-class indexes, sharded | retrieval is rarely the bottleneck; the model call is |
| Token prices (October 2026) | frontier \$4–10 per million input, cheap tier \$0.20–1; cache reads 2.5–10% | cost per request is dominated by input tokens and reasoning |
| Spanner commit | 5–10 ms single-region, higher multi-region | fine for session state, wrong for per-token writes |

Say "order of magnitude" when you quote them; the interviewer wants the reasoning, not the decimal.

## 3. The questions

### Q1. Design a multi-tenant LLM inference platform serving several open models to internal product teams

**Clarify.** Models: three to five open-weight models from 8B to 70B plus an embedding model. Traffic: 2,000 requests per second peak across tenants, p99 time-to-first-token under one second for interactive tenants, batch tenants tolerant of minutes. Tenants have quotas and must not starve each other. Prompts average 3k tokens with a shared 1.5k prefix per tenant; answers average 300 tokens.

**Numbers.** 2,000 rps × 3,300 tokens is 6.6 million tokens per second of prefill and decode work; at roughly 2,000 tokens per second per accelerator that is on the order of 3,000 accelerators at full utilisation, so utilisation and prefix caching are the whole design. If the 1.5k prefix is cached, prefill work falls by about half.

**Design.** Global external load balancer with Cloud Armor in front (Maglev underneath); a gateway service on GKE that authenticates the tenant, applies quota (Q6), picks a model pool and routes by prefix hash so requests sharing a cached prefix land on the same replica; model pools on GKE node pools with TPUs or GPUs, one Deployment per model and size class, running a continuous-batching server (vLLM, SGLang or JetStream on TPU) with prefix caching enabled; a priority queue per pool with interactive traffic ahead of batch; Memorystore for the routing table and prefix-to-replica affinity; Cloud Monitoring and Cloud Trace with a span per request carrying tokens in, tokens out, cached tokens, queue time, prefill time and decode time (the GenAI semantic conventions). Model weights live in Cloud Storage and are pulled to local SSD at pod start; GKE's image streaming and a warm standby per pool hide the cold start.

**Deep dive: scheduling and tail latency.** Continuous batching admits new requests into a running batch at every decode step; the trade-off is that a long prefill stalls every decode in the batch, so split prefill into chunks (chunked prefill) and cap the chunk so decode steps keep their cadence. Disaggregated prefill and decode (separate pools, KV cache shipped between them) buys predictable decode latency at the cost of network and a harder scheduler; say it is the 2026 direction and that you would adopt it once the pools are large enough to keep both sides busy. Hedged requests do not work for generation (you cannot cancel a half-written answer cheaply), so bound the tail with admission control instead: reject or degrade (smaller model) when queue time exceeds a budget rather than letting p99 grow.

**Deep dive: isolation.** Quota per tenant in tokens per minute, enforced at the gateway; a weighted fair queue per pool so a batch tenant's backlog cannot delay interactive tenants; separate pools for tenants with compliance isolation requirements rather than shared batches, because a shared KV cache is a side channel in principle.

**Failure and cost.** A pool loses a zone: the Deployment is multi-zone with capacity for the loss, and the gateway drains the pool while weights pull elsewhere. A model regression after a weight update: canary pool with an eval suite and a rollback by routing table, not by redeploy. Cost: report cost per thousand tokens per pool and utilisation per accelerator; buy committed use only for the floor of the load curve.

**Internal analogues.** Borg for the scheduler, Maglev for L4 balancing, Pathways for serving across TPU pods, Dapper for the trace.

### Q2. Design the embedding and indexing pipeline for a search product over one billion documents with per-document permissions and freshness under five minutes

**Clarify.** Documents arrive from connectors (Drive, tickets, wikis); updates are 1% of the corpus per day, about 10 million; permissions change independently of content; queries are 5,000 per second; recall at 10 must stay above 90% on the relevance set.

**Numbers.** 10 million updates a day is about 115 per second average, perhaps 1,000 per second peak; with ten chunks per document that is 10,000 chunk embeddings per second at peak, a handful of accelerators. The index is 10 billion vectors; at 768 dimensions in 8-bit that is about 8 TB, sharded.

**Design.** Connectors publish change events to Pub/Sub; a Dataflow streaming job (the Dataflow model: event time, watermarks, exactly-once) fetches content, chunks it, calls the embedding service (Q1's platform), and writes chunks and metadata to Bigtable keyed by document id and chunk id, with the vector written to Vector Search (ScaNN underneath) or AlloyDB with the ScaNN index for smaller corpora; document ACLs are stored separately in a relationship store modelled on Zanzibar (Spanner-backed, or Google Cloud's Agent Search data store with its reader lists), and ACL changes are a second Pub/Sub stream that updates only the permission index, never re-embeds. Query path: the search service expands the caller's identity to its groups, asks the permission store for a filter, runs the vector query with that filter pushed into the index (pre-filtering, never post-filtering the top-k), reranks the top hundred with a cross-encoder, and returns. Cloud Storage (Colossus) holds raw content and the index snapshots.

**Deep dive: freshness versus index rebuild.** ANN indexes are built in bulk; updates go to a small write-ahead segment searched alongside the main index and merged on a schedule (minutes to hours). The five-minute freshness target is met by the delta segment, and the merge cadence is tuned by the delta's size; say what happens if the merge falls behind (query latency grows as the unmerged segment grows; alarm on it).

**Deep dive: permissions.** A document with no ACL entry is unreadable, not public. Group expansion is cached per user with a short lifetime; a revocation must reach the filter within the stated SLO, so measure propagation time from the source system to the filter and alarm on it. Deletes are tombstoned first (query excludes them immediately) and physically removed at the merge.

**Failure and cost.** Embedding model upgrade: a second index built in the background from the stored chunks, a shadow comparison on the relevance set, a cut-over by routing; never re-embed in place. Pub/Sub backlog: Dataflow autoscaling with a backlog alarm; connectors are idempotent on document version, so a replay is safe.

**Internal analogues.** Flume and MillWheel for the pipeline, Bigtable for chunk storage, Colossus for the blobs, Zanzibar for permissions, ScaNN for the index.

### Q3. Design a real-time recommendation system (candidate generation and ranking) for a video or feed product

**Clarify.** 100 million daily users, 50,000 requests per second peak, 100 ms end-to-end budget, a catalogue of 100 million items with thousands added per minute, user features that must reflect actions within seconds.

**Design.** Two stages, as in Google's own published recommender work: candidate generation with a two-tower model (user tower online, item tower precomputed) retrieving a few hundred candidates per request from a ScaNN index over item embeddings; ranking with a larger model scoring those candidates with rich user and context features. Features: a streaming pipeline (Pub/Sub into Dataflow) computes per-user counters and recent-action windows and writes them to Bigtable (single-row atomic updates, millisecond reads, the right fit); batch features computed daily in BigQuery and loaded to the same store; the feature definitions registered once so training and serving read the same code path (the training-serving skew problem). Serving: the ranking model on the inference platform; the whole request fans out in parallel to the feature store, the candidate index and the ranking model, with a per-stage deadline and a fallback (popular items for the segment) if any stage misses it. Logging: every impression and its features written to Pub/Sub and landed in BigQuery for training, with the served model version on each row.

**Deep dive: freshness of items.** New items have no interaction history; the item tower embeds them from content features at ingest so they are retrievable immediately, and the ranker has an explicit exploration slot so they collect signal.

**Deep dive: the 100 ms budget.** Candidate retrieval 10 ms, feature fetch 10 ms in parallel, ranking 30 ms for a few hundred candidates in one batched call, network and serialisation the rest; the p99 is bounded by hedged reads to the feature store (safe, idempotent) and a hard deadline on the ranker.

**Failure.** Feature store degraded: serve with stale cached features and flag the request in logs so the training set can exclude it. Model regression: the online A/B framework with guardrail metrics and automatic rollback.

**Internal analogues.** Bigtable, the two-stage YouTube recommendation architecture, Flume for the training data pipeline, Borg for serving.

### Q4. Design a durable execution service for long-running, multi-step agents with tool side effects

**Clarify.** Agents run for minutes to hours, call tools with real side effects (tickets, emails, payments), must survive worker restarts, must never execute a side effect twice, and must be observable per step. 10,000 concurrent runs; a few thousand tool calls per second.

**Design.** The run is a state machine persisted outside the worker: run state and the step log in Spanner (external consistency means every worker sees the same step history; a run is a row group keyed by run id, steps are child rows). Workers on Cloud Run or GKE lease a run (a lease row with an expiry), execute one step (a model call or a tool call), append the step with its result, and release; a lease that expires is taken over by another worker, which replays from the step log, not from memory. Tool calls that have side effects carry an idempotency key derived from (run id, step number, canonical arguments); the tool server stores the key with the result, so a retried call returns the stored result instead of acting twice. Human approvals are steps that park the run; Cloud Tasks schedules the wake-up and the timeout. Agent Runtime on the Gemini Enterprise Agent Platform packages the worker side of this, with Memory Bank for cross-run memory and Agent Gateway for tool policy; say which parts you would take from the platform and which you would own (the step log and the idempotency contract).

**Deep dive: exactly-once side effects.** There is no exactly-once delivery, only at-least-once delivery plus idempotent receivers. The step log is the source of truth; the tool call is made after the intent is recorded (write-ahead), and the result is recorded after; a crash between the two is resolved on replay by asking the tool server for the idempotency key. If the tool cannot be made idempotent (a legacy system), wrap it in a reservation step with a confirmation, or require human approval for it.

**Deep dive: the model as a non-deterministic step.** Replaying a run must not re-call the model for completed steps; the recorded model output is replayed. Model outputs are stored with the prompt hash and model version so a later debug can reproduce or diff them (chapter 64).

**Failure and cost.** Spanner is the bottleneck at scale by write rate; batch step appends per run and keep tool results in Cloud Storage with a pointer when large. A region loss: multi-region Spanner for the step log is justified here, because losing runs mid-payment is worse than the commit latency. Cost per run is dominated by model tokens, so the controller from chapter 65 (effort per step, compaction) lives in the worker.

**Internal analogues.** Spanner, Chubby-style leases, Pub/Sub, the workflow engines behind Cloud Workflows.

### Q5. Design the training infrastructure for a foundation model on TPU pods

**Clarify.** A model with tens to hundreds of billions of parameters, trained for weeks on thousands of chips, from a multi-petabyte corpus in Cloud Storage; the run must survive chip and host failures without losing more than minutes of work; researchers want to resume, branch and evaluate checkpoints.

**Design.** Compute: TPU pod slices on GKE or the managed training service, programmed through JAX with sharding annotations (data parallel across slices, tensor and pipeline parallel within), with Pathways as the orchestration layer that lets one controller drive many pods. Data: a preprocessing pipeline in Dataflow that tokenises, deduplicates and shards the corpus into fixed-size files in Cloud Storage, with a deterministic shuffle keyed by epoch and shard so a resumed run reads exactly where it stopped; the input pipeline prefetches on the host CPUs so accelerators never wait on storage. Checkpointing: asynchronous, sharded checkpoints (each host writes its own shard) to Cloud Storage every N steps, with a small in-memory or local-SSD checkpoint more often for fast recovery; a checkpoint manager keeps the last K and the evaluation-tagged ones. Monitoring: step time, accelerator utilisation, loss and gradient norms streamed to Cloud Monitoring, with alerts on step-time regression (a slow host) and on loss spikes.

**Deep dive: failure handling.** A chip or host failure stops the synchronous step; the job restarts from the last checkpoint on a replacement slice, so recovery time is the checkpoint interval plus restart cost; the interval is chosen by balancing checkpoint write time against expected loss. Stragglers are detected by per-host step time and the host is evicted. Silent data corruption is real at this scale; periodic checksum verification on checkpoints and a loss-trajectory comparison across branches catch it.

**Deep dive: the data pipeline as the bottleneck.** With thousands of accelerators the input pipeline must deliver tens of gigabytes per second; the fix is the sharded, pre-tokenised format, parallel readers per host, and placing the corpus in the same region as the pod (egress is both slow and expensive).

**Cost.** Accelerator hours dominate; utilisation (the fraction of time the chips compute rather than wait) is the one number to report; a 10% utilisation gain on a multi-million-dollar run is the whole engineering budget.

**Internal analogues.** Pathways, Borg, Colossus, the TPU interconnect, the JAX and XLA stack.

### Q6. Design a global quota and rate-limiting service for a model API

**Clarify.** Limits per customer in requests per minute and tokens per minute, enforced within a second of the true usage, across three regions, at 100,000 decisions per second, without becoming a single point of failure for the API.

**Design.** Two tiers. Local: each gateway instance holds a token bucket per customer in memory and makes the fast decision; it periodically reports consumption and receives a refreshed allotment from the global tier. Global: a quota service backed by Memorystore for counters with Spanner as the durable source of limits and the audit log; the global tier divides each customer's limit across regions by observed share and rebalances every few seconds. The gateway fails open to its local bucket if the global tier is unreachable (a short over-admission is cheaper than an outage), with the allowance capped. Token-based limits count input and output tokens after the request, so the bucket is debited on completion and the pre-admission check uses an estimate; say that this means a burst can exceed the limit by one request's worth per instance and that the global tier corrects it.

**Deep dive: consistency choice.** Exact global counters would need a synchronous cross-region write per request (150 ms); the design accepts approximate enforcement with a bounded error, and the bound is a stated number. Customers who need hard caps (spend limits) are enforced at the global tier asynchronously with a small overrun tolerance written into the contract.

**Deep dive: hot keys.** One customer at 50% of traffic hashes to one shard; shard the counter by customer and a small random suffix, summing on read; Maglev-style consistent hashing keeps the mapping stable under instance churn.

**Internal analogues.** The quota and rate-limiting layers of Google's API infrastructure; Maglev; Spanner for the limit store.

### Q7. Design a multi-region conversation and session store for a consumer assistant

**Clarify.** 50 million daily users, sessions of tens of turns, each turn appends a few kilobytes; reads of the recent history on every turn; users expect to continue a conversation from another device within seconds; regulators expect deletion within a day; the model call is the latency budget, so the store gets 20 ms.

**Design.** Two stores with different jobs. The hot path: a per-session document in Firestore or a per-user row range in Bigtable in the user's home region, holding the last N turns and a compacted summary (the compaction from chapter 63), read once per turn. The durable record: an append-only turn log in Spanner (multi-region configuration for the small set of regulated tenants, regional for the rest), which is the source of truth for cross-device continuation and audit. A user's home region is chosen at sign-up and recorded in a global directory; requests are routed to it, and a cross-region continuation reads from the home region with the 150 ms penalty paid once. Deletion: a tombstone in the directory makes the user invisible immediately; a Dataflow job removes the turns, the summaries, the embeddings in any memory index, and the entries in any semantic cache within the window, and writes a deletion receipt.

**Deep dive: consistency.** A turn must not be answered against a stale history (the model would contradict itself), so the hot-path read after a write is read-your-writes: single-region, single-document, strongly consistent reads, which Firestore and Bigtable both provide within a row or document. Cross-region replication is asynchronous and the design says so; the cross-device case tolerates seconds.

**Deep dive: context size.** The store holds the summary and the recent turns, not the full prompt; the prompt is assembled per turn and cached at the model layer by prefix; a turn that would exceed the window triggers compaction, recorded as its own entry.

**Failure.** Home region down: the directory fails the user over to a replica with the asynchronous lag disclosed in the product (a banner, not silence) and fails back with reconciliation by turn id.

**Internal analogues.** Bigtable, Spanner, the global user directory pattern.

### Q8. Design the evaluation and experimentation platform for LLM features across many product teams

**Clarify.** Hundreds of prompt and model changes a week, offline evaluation before merge, online experiments with guardrails, judges that cost money, and results teams trust.

**Design.** Offline: every change produces an evaluation run, a Dataflow or batch job that replays a frozen dataset per feature through the candidate configuration, runs deterministic checks and LLM judges (chapter 66), and writes per-item results to BigQuery with the configuration hash; a CI gate compares against the baseline with paired statistics and per-slice thresholds; judge calls go through the inference platform's batch tier at half price. Online: an experiment framework assigns users to arms by a stable hash with layered, mutually exclusive experiments; the serving path logs the arm, the configuration and the outcome signals to Pub/Sub and BigQuery; guardrail metrics (latency, cost per request, refusal rate, safety classifier rate) are computed in near real time by Dataflow and trigger automatic ramp-down; the primary metric is computed daily with confidence intervals and a minimum run length. Human review: a sampling of production traffic into a labelling queue, labels feeding back into the frozen datasets and the judge calibration sets.

**Deep dive: trust.** Results are reproducible from the stored configuration and data snapshot; judge versions are recorded with their calibration numbers; an anchor set re-scored continuously separates judge drift from product drift; experiment analysis is centralised so every team computes intervals the same way.

**Deep dive: cost.** Judges on a cheap calibrated tier with escalation; cached verdicts for unchanged items; sampling rates per feature by traffic and risk.

**Internal analogues.** Google's layered experiment infrastructure, Flume for log processing, BigQuery (Dremel) for analysis.

## 4. Trade-offs you should be able to say in one breath

- **Consistency:** Spanner for external consistency when a wrong read costs money; Bigtable or Firestore for single-row atomicity at scale; asynchronous replication across regions with the lag disclosed.
- **Latency:** cache the prefix, pre-filter the index, fan out in parallel with deadlines, hedge only idempotent reads, shed load before the tail grows.
- **Throughput:** continuous batching and utilisation decide the accelerator bill; a half-idle fleet costs twice per token.
- **Freshness:** delta segments and streaming features for seconds; rebuilds and batch features for hours; state the number.
- **Exactly-once:** does not exist on the wire; idempotency keys and a write-ahead step log give it at the receiver.
- **Permissions:** enforced in the index filter and the data layer under the user's identity; missing ACL means deny; propagation lag is an SLO.
- **Cost:** report cost per successful request, utilisation, and cache-hit ratio; commit only for the floor of the curve.
- **Failure:** every design loses a zone without a page and a region with a disclosed degradation.

## 5. Pitfalls that lose the round

Starting to draw before stating numbers. Treating the model call as free or instant. A single region with no story for its loss. Exact global counters at 150 ms per request. Post-filtering a vector search by permission. Re-embedding a corpus in place on a model upgrade. Replaying a workflow by re-running the model. Synchronous cross-region writes on the hot path. No canary and no rollback path for a model or prompt change. Naming a retired product (Vertex AI Search is Agent Search; Vertex AI Pipelines is Agent Platform Pipelines; Data Catalog was shut down in 2026). Forgetting observability until asked: a trace per request with tokens, cache hits and queue time is part of the design, not an add-on.

## Sources and further reading

- Dean and Barroso, *The Tail at Scale*, Communications of the ACM, 2013.
- Corbett et al., *Spanner: Google's Globally-Distributed Database*, OSDI 2012; Chang et al., *Bigtable*, OSDI 2006.
- Pang et al., *Zanzibar: Google's Consistent, Global Authorization System*, USENIX ATC 2019.
- Eisenbud et al., *Maglev: A Fast and Reliable Software Network Load Balancer*, NSDI 2016.
- Akidau et al., *The Dataflow Model*, VLDB 2015; *MillWheel*, VLDB 2013.
- Sigelman et al., *Dapper, a Large-Scale Distributed Systems Tracing Infrastructure*, 2010; Adams et al., *Monarch*, VLDB 2020.
- Verma et al., *Large-scale cluster management at Google with Borg*, EuroSys 2015.
- Barham et al., *Pathways: Asynchronous Distributed Dataflow for ML*, MLSys 2022.
- Guo et al., *Accelerating Large-Scale Inference with Anisotropic Vector Quantization (ScaNN)*, ICML 2020.
- Covington, Adams and Sargin, *Deep Neural Networks for YouTube Recommendations*, RecSys 2016.
- Beyer et al., *Site Reliability Engineering* (the SRE book), 2016.
- Google Cloud documentation for GKE, Spanner, Bigtable, Pub/Sub, Dataflow, Memorystore, Vector Search, AlloyDB, Agent Runtime, Agent Search, Agent Gateway and Model Armor, October 2026.
- This repository: chapters 40 (application design exercises), 63 (token costs), 64 (trace-first troubleshooting), 65 (reasoning budgets in the worker), 66 (judges), 67 (authorisation).
