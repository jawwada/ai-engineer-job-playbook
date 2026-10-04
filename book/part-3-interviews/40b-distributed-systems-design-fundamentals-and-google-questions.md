# 40b. Distributed systems design: the fundamentals, and eight Google-style questions for AI engineers

> **What you need to be able to say:** the three facts every distributed-systems argument follows from (messages are lost and you cannot tell which, machines fail partially, there is no shared clock) and the vocabulary they produce: consistency models and external consistency, PACELC, replication and partitioning, consensus, leases with fencing tokens, idempotency keys and write-ahead intent, deadlines and retry budgets, queues and watermarks, caching patterns, hedged requests and admission control, SLOs and error budgets, the four golden signals; which Google Cloud store answers which need and why not the other one (Spanner, Bigtable, Firestore, AlloyDB, BigQuery, Cloud Storage, Memorystore, Vector Search, Pub/Sub); and, for eight infrastructure questions a Google system-design round gives an AI engineer (an LLM inference platform, a billion-document embedding pipeline with permissions, a two-stage recommender, durable agent execution, foundation-model training on TPU pods, a global quota service, a multi-region conversation store, an evaluation and experimentation platform), the intuition, the numbers, the design, the challenges and their fixes, two deep dives, the failure story and the internal Google system each one descends from. Chapter 40 has the application-level exercises and the 45-minute method; this chapter is the infrastructure underneath them. Sections 40b.1–40b.14 are the fundamentals; 40b.15–40b.19 are the questions. Dated October 2026.

## 40b.1 Why distributed systems are hard: the three facts

Everything in this subject follows from three facts about machines connected by networks.

1. **Messages are delayed and lost, and you cannot tell which.** A request that gets no reply may have been dropped on the way there, processed and dropped on the way back, or still be in a queue. So every sender must decide what to do with silence, and every receiver must tolerate receiving the same message twice. This fact alone produces timeouts, retries, idempotency and the impossibility of exactly-once delivery.
2. **Machines fail independently and partially.** A thousand hosts with a one-year mean time between failures see a failure every nine hours. Failures are not clean: a host can be slow rather than dead, reachable by some peers and not others, or alive with a corrupted disk. So the system must keep working through failures it cannot fully diagnose, which produces replication, leases, health checks and the rule that a slow replica is treated as a failed one.
3. **There is no shared clock.** Two machines cannot agree on what happened first without talking, and talking takes time. So ordering is something you build (logical clocks, consensus, a single leader) or buy with specialised hardware (Spanner's TrueTime, which bounds clock uncertainty with GPS and atomic clocks and then waits out the uncertainty before committing).

Hold these in mind and most "why" questions answer themselves.

## 40b.2 The vocabulary of guarantees

**Consistency models** describe what a reader can see.

- *Linearizable (strong)*: every operation appears to happen at a single instant between its start and end, in one global order; a read after a write sees the write. The easiest to program against and the most expensive, because agreeing on the order costs a round trip to a majority.
- *Sequential*: all participants see the same order, but not necessarily in real time.
- *Causal*: if A caused B, everyone sees A before B; unrelated writes may be seen in different orders. Cheap and often enough for user-facing data.
- *Eventual*: replicas converge if writes stop; a read may return old data. Cheapest; the application must tolerate staleness.
- *Read-your-writes, monotonic reads*: session guarantees that make eventual consistency bearable for one user (a user sees their own writes; a user never sees time go backwards).

**External consistency** is Spanner's term for linearizability across a globally distributed database: a transaction that commits after another in real time is ordered after it everywhere. It is why a Spanner read can be trusted as the source of truth in a step log or a directory.

**CAP and PACELC.** During a network partition a system must choose between staying available and staying consistent (CAP). PACELC adds the everyday case: even without a partition, there is a trade-off between latency and consistency, because consistency requires coordination and coordination costs round trips. The useful form of the question is not "CP or AP" but "which operations need coordination, and how far away are the participants". Spanner coordinates across regions and pays the latency; Bigtable coordinates within a row and nothing more; Firestore is strongly consistent per document; caches are eventually consistent by design.

**Durability** is a separate axis: a write acknowledged after one replica's memory, one replica's disk, a majority's disks, or a cross-region majority's disks are four different promises with four latencies. Say which one you are making.

## 40b.3 Replication, partitioning and placement

**Replication** copies data for durability and read scaling. Leader-based (one replica accepts writes, others follow) is simple and gives a clear order; multi-leader allows writes in several regions and forces conflict resolution; leaderless (quorum reads and writes) trades a global order for availability. Synchronous replication waits for followers before acknowledging and costs their latency; asynchronous does not and risks losing acknowledged writes on leader failure. Most production systems are leader-based with synchronous replication to a local majority and asynchronous replication to other regions, and say so.

**Partitioning (sharding)** splits data so no machine holds all of it. By hash (uniform, no range scans), by range (scans, hot ranges), or by a composite that puts related rows together (Bigtable row keys, Spanner interleaved tables). The problems are hot partitions (one key or range gets most of the traffic), rebalancing (moving partitions when machines come and go) and cross-partition operations (a transaction spanning shards needs two-phase commit or a design that avoids it). Consistent hashing assigns keys to machines so that adding one machine moves only a fraction of the keys; it is the basis of every cache ring and of Maglev's connection-stable load balancing.

**Placement** decides where replicas live. Zones within a region fail independently of each other and share low latency; regions fail together only in a disaster and are far apart. The standard pattern is three zones for availability and a second region for disaster recovery, with the data-residency rules of the tenant deciding whether the second region is allowed to exist.

## 40b.4 Consensus, leaders and leases

**Consensus** lets a set of machines agree on a sequence of values despite failures: Paxos, Raft and their relatives. A majority (quorum) must acknowledge each value, so the system tolerates fewer than half of its members failing and pays one round trip to the quorum per decision. You rarely implement consensus; you use a service that does (Chubby inside Google, ZooKeeper and etcd outside, Spanner's Paxos groups underneath its tables) for the few things that must be agreed: who is leader, what the configuration is, which version is current.

**Leader election** picks one machine to serialise decisions. It is cheap once a consensus service exists: the leader holds a lease.

**Leases** are the time-bounded locks of distributed systems. A lease says "you are the owner until time T" and must be renewed; if the owner dies, the lease expires and another can take it. The trap is a paused owner (garbage collection, a long I/O stall) that wakes after expiry and still believes it owns the resource. The cure is a **fencing token**: every lease grant carries a monotonically increasing number, every write carries the number, and the storage rejects writes with a stale one. Chubby taught this lesson; the durable agent service in Q4 depends on it.

## 40b.5 Time, ordering and idempotency

**Logical clocks** (Lamport, vector clocks) order events by causality without a shared physical clock; they tell you "A happened before B" or "A and B are concurrent", which is what conflict resolution needs. **Hybrid logical clocks** combine a physical clock with a counter so timestamps are both roughly real and causally consistent. **TrueTime** gives a physical interval with bounded uncertainty and lets Spanner order transactions in real time by waiting out the interval.

**Idempotency** is the property that doing an operation twice has the same effect as once. Since delivery is at-least-once, every operation with a side effect needs an **idempotency key** (chosen by the caller, stored by the receiver with the result) so a retry returns the stored result instead of acting again. Exactly-once *delivery* does not exist; exactly-once *effect* is built from at-least-once delivery plus idempotent receivers plus a durable record of intent (write-ahead) so a crash mid-operation can be resolved by asking what happened with the key.

**Ordering within a stream** is cheap (one partition, one writer); ordering across a system is expensive (consensus). Design so that the operations that need ordering share a partition (all of a user's events keyed by user id) and the rest do not.

## 40b.6 Communication: synchronous calls, queues and streams

**Synchronous RPC** (gRPC with protocol buffers inside Google) is for requests that need an answer now. The rules: deadlines on every call, propagated through the chain so a slow dependency cannot hold a caller forever; retries only for idempotent calls and only with exponential backoff and jitter, with a retry budget so a struggling service is not amplified into an outage; circuit breakers that stop calling a dependency that is failing; and the recognition that a chain of N sequential calls has a tail latency that compounds.

**Queues** (Pub/Sub, Cloud Tasks) decouple producers from consumers in time and rate: the producer is acknowledged when the message is stored, the consumer processes when it can. They give at-least-once delivery, so consumers are idempotent; they absorb bursts, so the consumer can be sized for the average and the backlog is the buffer; and they make retries and dead-letter handling explicit. The costs are latency (a hop and a queue) and the loss of a synchronous error path (the producer does not know the consumer failed).

**Streams** add ordering within a key and the notion of event time versus processing time. The Dataflow model's contribution is the **watermark**: a statement that no events older than time T are expected, which lets a window close and emit a result while late events are handled by an explicit policy. Exactly-once processing in Dataflow is achieved by deterministic checkpointing of state and deduplication of inputs, not by magic on the wire.

**Backpressure** is what a system does when a downstream stage is slower than an upstream one: buffer (a queue, with a bound), shed (drop or reject the lowest-priority work), or slow the producer. A system with no backpressure plan fails by running out of memory at the most inconvenient stage.

## 40b.7 Caching

A cache trades freshness for latency and cost. The questions to answer for every cache: what is the key, what is the lifetime, what invalidates it, what is the hit rate, and what happens on a miss storm. Patterns: **cache-aside** (the application reads the cache, then the store, then fills the cache), **write-through** (writes go to both), **write-behind** (writes go to the cache and drain later; fast and risky). Problems: **thundering herd** (a popular key expires and every request goes to the store at once; solve with request coalescing or staggered expiry), **hot keys** (one key on one node; solve with local caches in front of the shared cache or key replication), **stale reads after writes** (solve with explicit invalidation or short lifetimes, and never for data where staleness is a correctness bug), and **cache stampede on deploy** (a cold fleet; solve with warm-up or gradual rollout).

Model-specific caches have their own rules: the KV-cache prefix cache keyed by exact token prefix (anything that changes early in the prompt invalidates everything after it); semantic caches keyed by embedding similarity with staleness and tenancy risks; verdict caches in evaluation keyed by (item, configuration, judge version).

## 40b.8 Load balancing, admission control and the tail

**Load balancing** spreads requests across replicas: at the network layer by consistent hashing of connections (Maglev), at the application layer by least-loaded or weighted round robin with health checks, and sometimes by affinity (prefix-cache routing in model serving, session affinity in stateful services). Affinity improves hit rates and worsens balance; say which you are optimising.

**The tail.** The p99 of a service that fans out to a hundred shards is dominated by the slowest shard, so a 1% slow rate per shard becomes a 63% slow rate per request. Dean and Barroso's remedies: **hedged requests** (send a second copy after the p95 and take the first reply; only for idempotent work), **tied requests** (send to two and cancel the loser), micro-partitioning so load can move, and selective replication of hot data. Generation requests cannot be hedged cheaply, so model serving bounds its tail with **admission control**: a queue-time budget per class, beyond which the request is rejected or degraded.

**Load shedding** is the deliberate rejection of work to protect the work that matters. Priorities are set at the edge (interactive before batch, paying before free), the cheapest rejection is the earliest, and a shed request gets an honest error with a retry-after, not a timeout.

## 40b.9 Storage choices in one table

| Need | Choice | Why |
|---|---|---|
| Global transactions, external consistency, SQL | Spanner | Paxos groups, TrueTime; pays commit latency for correctness |
| Very high write throughput, single-row atomicity, row-range locality | Bigtable | wide-column, sorted keys, millisecond reads; no cross-row transactions |
| Document model, strong per-document consistency, client SDKs | Firestore | mobile and web first; security rules per document |
| Relational with extensions, vector search at moderate scale | AlloyDB or Cloud SQL | Postgres with ScaNN or pgvector; row-level security |
| Analytics over petabytes, batch joins | BigQuery | Dremel; columnar; separates storage and compute |
| Blobs, checkpoints, index snapshots, data lakes | Cloud Storage | Colossus underneath; lifecycle classes |
| Low-latency counters, sessions, hot keys | Memorystore | in-memory; sharded; eventually consistent across replicas |
| Vector similarity at billions of vectors | Vector Search | ScaNN; sharded; delta segments for freshness |
| Streams and queues | Pub/Sub, Cloud Tasks | at-least-once; ordering per key; scheduled tasks |

The interview question behind the table is always "why not the other one". Spanner versus Bigtable: do you need cross-row transactions and SQL (Spanner) or the highest write rate with locality (Bigtable)? Firestore versus Bigtable: client model and per-document rules (Firestore) or scale and analytics scans (Bigtable)? BigQuery versus the others: analysis, never a serving path.

## 40b.10 Reliability engineering: SLOs, error budgets and failure domains

An **SLO** is a target for a service-level indicator over a window (99.9% of requests under 300 ms over 30 days). The **error budget** is the allowed failure (0.1% of requests); when it is spent, reliability work takes priority over features. SLOs make trade-offs explicit: a 99.99% target permits 4 minutes of downtime a month and forbids most deployment practices that a 99.9% target allows.

**Failure domains** are the units that fail together: a process, a host, a rack, a zone, a region, a provider. Place replicas so that no single domain's loss breaks the SLO, and test it: Google's DiRT exercises and chaos engineering elsewhere exist because untested failover does not work.

**Graceful degradation** is the planned reduction of service under failure: serve from cache, serve a smaller model, serve popular items instead of personalised ones, disclose stale data with a banner. A system that either works perfectly or fails completely has not been designed for failure.

**Deployment safety**: canaries (a small fraction of traffic on the new version with automatic comparison), gradual rollout by zone and region, rollback by configuration rather than redeploy, and feature flags so behaviour can change without a binary change. For model features, the canary includes an evaluation suite, because a model change has no stack trace.

## 40b.11 Observability

Three signals: **metrics** (aggregates over time; cheap; the basis of alerts), **logs** (events; expensive at scale; the basis of investigation), **traces** (a request's path across services with timing per hop; the basis of latency debugging). Dapper established the trace model Google uses; Monarch holds the metrics. The rules: propagate a trace id through every hop including queues; alert on symptoms the user feels (latency, errors, saturation) rather than causes; put the four golden signals (latency, traffic, errors, saturation) on every service's dashboard; sample traces at the tail so the slow ones are kept; and for model services, add tokens in and out, cache hits, queue time, prefill and decode time, and the model and prompt versions to every span, because that is how cost and quality regressions are found.

## 40b.12 Security and multi-tenancy

Identity on every call (a service identity for machines, a user identity carried through delegation for user-facing work); authorisation at the data layer under that identity, not in the caller's good intentions; isolation between tenants at the level the risk justifies (shared tables with tenant columns and row filters; separate partitions; separate instances; separate projects); encryption in transit and at rest with per-tenant keys where deletion must be provable; secrets in a manager, never in configuration; egress controls so a compromised service cannot talk to the internet; and audit logs of every access decision. Zanzibar is the model for relationship-based authorisation at scale: a global, consistent store of "user is member of group, group can view document" tuples with a snapshot token so a check is never evaluated against permissions older than the content it protects.

## 40b.13 Capacity planning and cost

Size from numbers: peak QPS with a growth factor, bytes per request, storage per day with retention, and the latency budget; then find the bottleneck resource (accelerator memory, network bandwidth, storage IOPS, a single leader) and design around it. Utilisation is the cost lever for expensive resources (accelerators, Spanner nodes): a resource at 30% utilisation costs three times per unit of work. Commit (reservations, committed-use discounts) for the floor of the demand curve and use on-demand for the peak. Report unit costs the business understands (per request, per thousand tokens, per successful task) and watch them per feature, because total spend hides a unit-cost regression under a traffic change.

## 40b.14 The habits that show on the whiteboard

- State numbers before boxes, and say "order of magnitude".
- Name the consistency model of every store and the durability of every write.
- Put a deadline on every call and an idempotency key on every side effect.
- Say what happens when each box dies, and what the user sees.
- Separate the hot path from the durable path when their needs differ.
- Pre-filter, pre-compute and cache; hedge only what is idempotent; shed before the tail grows.
- Make rollout and rollback a configuration change.
- Draw the trace through the design, not after it.
- Give every trade-off a sentence: what you gain, what you pay, why it is right here.

## 40b.15 How the round is run and scored

Forty-five minutes, one open problem, a whiteboard or a shared doc. The interviewer scores four things: whether you turned an ambiguous ask into requirements with numbers; whether the design is sound and complete at the level of components and data flow; whether it scales, degrades and recovers, with the bottleneck identified; and whether you can state trade-offs rather than hide them. For AI engineers a fifth line appears on the feedback form: whether you treat the model as a component with a cost, a latency distribution, a failure rate and an evaluation, not as magic.

**The method, in the order you speak it.**

1. *Clarify* (3 minutes): users, scale, latency target, consistency needs, what "correct" means, what already exists.
2. *Numbers in the corner* (3 minutes): QPS peak and average, data volume and growth, tokens per request, p50 and p99 latency, cost per unit. Chapter 40.1 lists the four calculations; write them before the first box.
3. *High-level design* (10 minutes): ingress, compute, state, async, model, observability. Name the product and the internal system it maps to.
4. *Deep dives* (20 minutes): the two components the interviewer steers you to, usually the state layer and the model-serving layer.
5. *Failure, scale, cost* (8 minutes): what breaks first, what you shed, what you cache, what a region loss does, what it costs per request, and the SLO with its error budget.

**Vocabulary that signals you have run things at Google scale.** SLO and error budget (the SRE book); tail latency and hedged requests ("The Tail at Scale"); consistent hashing and Maglev for load balancing; Spanner's TrueTime and external consistency versus Bigtable's single-row atomicity; Colossus as the file system under Cloud Storage; Borg as the ancestor of Kubernetes and GKE; Dapper as the ancestor of Cloud Trace; Monarch as the ancestor of Cloud Monitoring; Zanzibar as the ancestor of every relationship-based authorisation store; the Dataflow model (MillWheel and Flume) for exactly-once streaming with watermarks; Pathways for multi-pod training and serving on TPUs.

## 40b.16 Numbers to carry in

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

## 40b.17 The questions

### Q1. Design a multi-tenant LLM inference platform serving several open models to internal product teams

**Intuition.** A language model server is a factory with one expensive machine. Every request has two phases: *prefill*, where the whole prompt is pushed through the model at once (compute-bound, parallel, fast per token), and *decode*, where tokens come out one at a time, each step reading the entire set of weights and the growing KV cache (memory-bandwidth-bound, serial). A single request cannot saturate an accelerator during decode, so the only way to make the machine pay is to run many requests' decode steps together in one batch. That is the whole economics of serving: utilisation is throughput, throughput is cost, and anything that stalls the batch (a long prefill, a slow tenant, a cold start) is money lost. The second intuition is that most prompts share a prefix (system prompt, tool schemas, few-shot examples), and a prefix already in the KV cache costs nothing to recompute; routing requests so they land where their prefix is cached is worth more than any other optimisation. The third is that tenants compete for the same batch slots, so fairness has to be designed, not hoped for.

**Clarify.** Models: three to five open-weight models from 8B to 70B plus an embedding model. Traffic: 2,000 requests per second peak across tenants, p99 time-to-first-token under one second for interactive tenants, batch tenants tolerant of minutes. Tenants have quotas and must not starve each other. Prompts average 3k tokens with a shared 1.5k prefix per tenant; answers average 300 tokens. Some tenants carry compliance requirements that forbid sharing hardware with others.

**Numbers.** 2,000 rps × 3,300 tokens is 6.6 million tokens per second of prefill and decode work; at roughly 2,000 tokens per second per accelerator that is on the order of 3,000 accelerators at full utilisation. If the 1.5k prefix is served from cache, prefill work falls by about half, and if real utilisation is 60% the fleet is closer to 3,000 again; the two effects cancel, which is the point: utilisation and caching are the design. Memory: a 70B model at 8-bit is 70 GB of weights per replica plus KV cache, roughly 300 KB per token for a 70B-class model, so a batch of 64 requests at 4k tokens needs about 80 GB of KV cache; the batch size is bounded by memory before it is bounded by compute.

**Design.** Global external load balancer with Cloud Armor in front (Maglev underneath); a gateway service on GKE that authenticates the tenant, applies quota (Q6), picks a model pool and routes by prefix hash so requests sharing a cached prefix land on the same replica; model pools on GKE node pools with TPUs or GPUs, one Deployment per model and size class, running a continuous-batching server (vLLM, SGLang or JetStream on TPU) with prefix caching enabled; a priority queue per pool with interactive traffic ahead of batch; Memorystore for the routing table and prefix-to-replica affinity; Cloud Monitoring and Cloud Trace with a span per request carrying tokens in, tokens out, cached tokens, queue time, prefill time and decode time (the GenAI semantic conventions). Model weights live in Cloud Storage and are pulled to local SSD at pod start; GKE's image streaming and a warm standby per pool hide the cold start.

```
client → global LB (Maglev) → gateway (auth, quota, prefix-hash routing, priority)
      → pool[model, size] on GKE accelerators: continuous batching + prefix cache
      ↘ batch tier (same pools, low priority, half price)
state: Memorystore (routing, affinity) · Cloud Storage (weights) · Spanner (tenants, quotas)
observability: Cloud Trace span per request (tokens, cache hit, queue, prefill, decode) · Monitoring
```

**Challenges and how to solve them.**

1. *Prefill stalls decode.* A 100k-token prompt admitted into a batch holds every other request's next token until its prefill finishes. Solve with chunked prefill (the prompt is processed in slices interleaved with decode steps, so the decode cadence survives), and with a separate prefill queue so that long prompts are rate-limited per pool. The 2026 direction is disaggregated serving: dedicated prefill replicas that compute the KV cache and ship it over the interconnect to decode replicas; it buys predictable decode latency and independent scaling of the two phases at the cost of KV-cache transfer and a harder scheduler. Say you would adopt it once the pools are large enough to keep both sides busy.
2. *The prefix cache is only useful if requests find it.* Random load balancing scatters a tenant's requests across replicas and each replica recomputes the same prefix. Solve with affinity routing: hash the prefix (or the tenant and prompt template version) to a replica set with consistent hashing, so the same prefix lands on the same few machines, and let the server's cache hold it. Measure the cache-hit ratio per tenant; below about 70% on a templated workload something in the prompt is changing per request (a timestamp, a per-user greeting at the top) and the fix is in the prompt, not the server.
3. *Tenants starve each other.* A batch tenant submitting a million-request backlog fills every queue. Solve with a weighted fair queue per pool keyed by tenant, with interactive classes strictly ahead of batch, and quotas in tokens per minute enforced at the gateway before the queue. Fairness in a batching server also means bounding how many slots one tenant holds in a running batch.
4. *Tail latency has no hedging.* For a stateless read you send a second copy after the p95 and take the first answer; for generation you cannot cheaply cancel a half-written answer and the second copy doubles the work. Solve with admission control instead: a queue-time budget per class; when it is exceeded, either reject with a retry-after, or degrade to a smaller model in the same family for tenants that opted in. Bounding the tail by refusing work is a Google habit worth naming.
5. *Cold starts.* A 70B replica takes minutes to load. Solve with weights on local SSD pulled from Cloud Storage with parallel readers, a warm standby per pool, and scaling signals from queue depth rather than CPU; pre-scale for known daily curves.
6. *Isolation and side channels.* A shared batch shares memory; timing differences in a shared KV cache can in principle leak information about another tenant's prompt. Solve with dedicated pools for compliance tenants and no cross-tenant prefix sharing; share within a tenant freely.
7. *Weight updates and regressions.* A new checkpoint can silently degrade quality. Solve with a canary pool that takes a percentage of traffic behind a routing-table flag, an automated eval suite on the canary (chapter 66), and rollback by changing the routing table, not by redeploying.

**Deep dive: the scheduler.** The server maintains a running batch; at every decode step it admits waiting requests whose KV cache fits, evicts finished sequences, and, with chunked prefill, interleaves prefill slices. Two knobs matter: the maximum tokens per step (bounds the step time and therefore the decode cadence) and the KV-cache memory budget (bounds concurrency). Paged KV cache (vLLM's PagedAttention) lets sequences share prefix pages and avoids fragmentation, which is what makes high concurrency possible. Speculative decoding (a small draft model proposes several tokens that the large model verifies in one step) raises per-stream decode speed two- to three-fold when the draft agrees often, at the cost of extra compute when it does not; it helps interactive latency more than throughput.

**Deep dive: observability and the cost model.** Every request's span records queue time, prefill time, decode time, tokens in, tokens out and cached tokens. From these you compute per pool: utilisation, cost per thousand tokens, cache-hit ratio and the p99 of time-to-first-token by class. A cost per request that rises while traffic is flat is a prompt change in one tenant; the span attributes find it in minutes (chapter 63).

**Failure, scale, cost.** A pool loses a zone: multi-zone Deployments with capacity for the loss and gateway draining. The gateway loses Memorystore: fall back to hashing without affinity (slower, correct). Accelerator scarcity: a reservation for the floor of the load curve, on-demand for the peak, and the batch tier as the elastic buffer that absorbs spare capacity at night. Cost is reported per pool as cost per thousand tokens and utilisation; the levers are in that order.

**What the interviewer probes.** "Why not just add replicas?" (utilisation, not count, is the cost.) "What breaks at 10× traffic?" (accelerator supply and the gateway's quota service; the design shards both.) "How do you upgrade a model with zero downtime?" (canary pool and routing table.) "Where does a prompt-injection filter go?" (at the gateway, before the queue, as a classifier with its own latency budget; Model Armor is the managed option.)

**Internal analogues.** Borg for the scheduler, Maglev for L4 balancing, Pathways for serving across TPU pods, Dapper for the trace.

### Q2. Design the embedding and indexing pipeline for a search product over one billion documents with per-document permissions and freshness under five minutes

**Intuition.** Search over embeddings is two problems that pull in opposite directions. An approximate-nearest-neighbour index is fast because it is built in bulk and laid out for reads; a corpus that changes every second wants writes. The standard answer is the same one log-structured storage gave twenty years ago: a large immutable index plus a small mutable delta, searched together and merged on a schedule. The second intuition is that permissions are a separate dataset with its own change rate; they must never be baked into the embedding, and the filter must be applied *inside* the index search, because filtering after taking the top-k returns an empty page to a user who can see only a small slice of the corpus. The third is that an embedding model is part of the index's schema: changing the model means a new index, built beside the old one, never a mutation in place.

**Clarify.** Documents arrive from connectors (Drive, tickets, wikis, a CRM); updates are 1% of the corpus per day, about 10 million; permissions change independently of content and far more often; queries are 5,000 per second; recall at 10 must stay above 90% on the relevance set; a revoked user must stop seeing a document within a stated window.

**Numbers.** 10 million updates a day is about 115 per second average, perhaps 1,000 per second at peak; with ten chunks per document that is 10,000 chunk embeddings per second at peak, a handful of accelerators. The index is 10 billion vectors; at 768 dimensions in 8-bit that is about 8 TB of vectors before the graph or quantisation structures, so it is sharded across tens of nodes. A full re-embed of the corpus is 10 billion chunk embeddings; at tens of thousands per second on a fleet it is days, which is why model upgrades are planned events.

**Design.** Connectors publish change events to Pub/Sub; a Dataflow streaming job (the Dataflow model: event time, watermarks, exactly-once) fetches content, chunks it, calls the embedding service (Q1's platform, batch tier), and writes chunks and metadata to Bigtable keyed by document id and chunk id, with the vector written to Vector Search (ScaNN underneath), or AlloyDB with the ScaNN index for corpora small enough for one database; document ACLs live in a relationship store modelled on Zanzibar (Spanner-backed, or Agent Search's data store with its reader lists), fed by a second Pub/Sub stream of permission changes that updates the permission index and never re-embeds. Query path: the search service expands the caller's identity to its groups, obtains the permission filter, runs the vector query with that filter pushed into the index, reranks the top hundred with a cross-encoder, and returns with citations. Cloud Storage (Colossus) holds raw content and index snapshots.

```
connectors → Pub/Sub(content) → Dataflow: fetch, chunk, embed (batch tier) → Bigtable(chunks) + Vector Search(delta segment)
connectors → Pub/Sub(permissions) → permission index (Zanzibar-style, Spanner)
query → identity → group expansion (cached) → filter → ANN(main + delta, pre-filtered) → rerank → answer
nightly/hourly: merge delta into main; model upgrade = shadow index + cut-over
```

**Challenges and how to solve them.**

1. *Freshness versus index structure.* A quantised, graph-based or tree-based index cannot absorb 1,000 inserts a second without degrading. Solve with a delta segment: new and updated vectors go to a small brute-force or lightly indexed segment searched alongside the main index; a merge job rebuilds the affected shards on a cadence (minutes to hours) chosen so the delta stays small. Latency rises as the delta grows, so alarm on delta size and merge lag.
2. *Updates and deletes in an immutable index.* You cannot edit a vector in place. Solve with tombstones: a deleted or superseded chunk id goes to a tombstone set consulted at query time (excluded immediately) and is physically removed at the next merge. Document versions carry a monotonically increasing version number so an out-of-order replay cannot resurrect an old chunk.
3. *Permissions that change faster than content.* Re-embedding on every ACL change is unaffordable and unnecessary. Solve by keeping permissions out of the vector entirely: a per-chunk allow-list (user and group ids normalised to the identity provider's stable ids) stored as filterable metadata, updated by the permission stream; a document with no ACL entry is unreadable, not public. Group membership changes are handled by expanding the *caller's* groups at query time, not by rewriting documents.
4. *Pre-filtering at scale.* Pushing a filter into an ANN search can destroy recall if the filter is very selective (the nearest neighbours are all filtered out and the search terminates early). Solve by letting the index over-fetch under selective filters, by partitioning the index on the most common coarse filter (tenant, region) so the search runs within the partition, and by measuring recall per filter selectivity band on the relevance set.
5. *Propagation lag as a security property.* A revoked user still matches until the permission index updates. Solve by measuring end-to-end propagation (connector event to filter) and publishing it as an SLO; cache group expansion for seconds, not hours; treat lag above the SLO as an incident, not a backlog.
6. *Model upgrades.* A new embedding model is incompatible with the old vectors. Solve with a shadow index: build the new index from the stored chunks in the background, compare on the relevance set and on a shadow of live queries, cut over by routing, keep the old index for rollback, then delete it. Store chunks and metadata separately from vectors precisely so this rebuild never touches the source systems.
7. *Chunking and duplicates.* The same document arrives through two connectors; a long table is split mid-row. Solve with content hashing for deduplication at ingest, structure-aware chunking (headings, tables, code blocks kept whole), and a chunk-to-document map so reranking and citation work at document level.
8. *Backpressure and replay.* A connector bursts ten million events after an outage. Solve with Dataflow autoscaling bounded by the embedding service's batch quota, backlog alarms, and idempotent writes keyed by (document id, version) so a full replay is safe.

**Deep dive: the query path budget.** 5,000 queries per second with a 300 ms target: identity and group expansion from a cache, 5 ms; permission filter construction, 5 ms; ANN over the sharded index with scatter-gather to tens of shards, 20–40 ms at p99 with hedged shard reads (safe, idempotent); reranking a hundred candidates with a cross-encoder on the inference platform, 50–100 ms; assembly, 10 ms. The reranker is the largest cost and the first thing to cache (by query hash and filter hash, short lifetime) and the first thing to degrade under load (rerank fifty instead of a hundred).

**Deep dive: the merge.** Merging a delta into a sharded main index is a per-shard rebuild: read the shard's vectors from Bigtable, drop tombstoned ids, add the delta's vectors, rebuild the quantisation and graph structures, write the new shard to Cloud Storage, and swap it in atomically behind a version pointer. Shards are rebuilt in parallel on a schedule weighted by their delta size, so hot shards merge more often. The rebuild is the natural place to re-check invariants (every chunk has a document, every document has an ACL entry or a tombstone).

**Failure, scale, cost.** Loss of the delta segment: rebuild from Bigtable and Pub/Sub replay within the freshness window. Index shard unavailable: scatter-gather returns partial results with a flag and the SLO counts it as degraded. Cost is dominated by embedding compute at ingest (batch tier) and reranking at query time; store vectors quantised, and let the relevance set decide the quantisation level.

**What the interviewer probes.** "Why not filter after the search?" (empty pages for narrow permissions; leaks if the filter is forgotten.) "What if a user can see only ten documents?" (the filter is selective; the index over-fetches, or the query falls back to a metadata search.) "How long until a revoked user stops seeing a document?" (a number, and the alarm on it.) "How do you evaluate the index?" (recall at k on a labelled set per filter band; chapter 24c.)

**Internal analogues.** Flume and MillWheel for the pipeline, Bigtable for chunk storage, Colossus for the blobs, Zanzibar for permissions, ScaNN for the index.

### Q3. Design a real-time recommendation system (candidate generation and ranking) for a video or feed product

**Intuition.** You cannot score a hundred million items for every request, so the system is a funnel: a cheap stage narrows the catalogue to hundreds of candidates using a model simple enough to be an index lookup, and an expensive stage ranks those hundreds with every feature you have. The two-tower trick makes the first stage an index: the user tower produces a vector at request time, the item tower produced one per item offline, and the nearest items are the candidates. The second intuition is that the hardest engineering problem is not the model but keeping training and serving consistent: a feature computed one way in the training pipeline and another way at serving time is a silent accuracy loss that no test catches (training-serving skew). The third is that the system has a feedback loop: it trains on what it showed, so it needs deliberate exploration and careful logging of what was served and why.

**Clarify.** 100 million daily users, 50,000 requests per second peak, 100 ms end-to-end budget, a catalogue of 100 million items with thousands added per minute, user features that must reflect actions within seconds, and an experimentation culture where models ship weekly.

**Numbers.** 50,000 requests per second × 300 candidates ranked is 15 million item scores per second; a ranking model at a few microseconds per candidate on an accelerator in batched inference needs tens of replicas. Feature reads: each request fetches one user row and 300 item rows; Bigtable at a few milliseconds per batched read handles it, but 50,000 × 300 is 15 million item-feature reads per second, so item features are cached in the ranker's memory (they change slowly) and only user features are fetched live. Logging: 50,000 impressions per second × a few kilobytes is a few hundred megabytes per second into Pub/Sub, tens of terabytes a day in BigQuery.

**Design.** Candidate generation with a two-tower model (user tower online, item tower precomputed) retrieving a few hundred candidates per request from a ScaNN index over item embeddings, plus a few other candidate sources (recent, popular in segment, followed creators) merged and deduplicated; ranking with a larger model scoring those candidates with user, item and context features. Features: a streaming pipeline (Pub/Sub into Dataflow) computes per-user counters and recent-action windows and writes them to Bigtable (single-row atomic updates, millisecond reads); batch features computed daily in BigQuery and loaded to the same store; a feature registry that holds each feature's definition once so training (BigQuery and Dataflow) and serving (the online store) are generated from the same code. Serving: the ranking model on the inference platform; the request fans out in parallel to the feature store, the candidate index and the ranking model, with a per-stage deadline and a fallback (popular items for the segment) if any stage misses it. Logging: every impression with its features and the served model version written to Pub/Sub and landed in BigQuery for training.

```
request → user features (Bigtable, streaming + batch) ──┐
        → user tower → ScaNN candidates (hundreds) ──────┼→ ranker (batched, accelerators) → policy layer (diversity, exploration, business rules) → response
        → other candidate sources (recent, popular) ─────┘
logs: impressions + features + model version → Pub/Sub → BigQuery → training → model registry → canary
```

**Challenges and how to solve them.**

1. *Training-serving skew.* Solve with a feature registry: one definition per feature, compiled to both the batch and streaming pipelines; log the *served* feature values with each impression and train on the logged values, not on recomputed ones. A skew monitor compares the distribution of served and training features daily.
2. *Freshness of user state.* A user who just watched three cooking videos should see cooking next. Solve with a streaming path: actions to Pub/Sub, Dataflow windows updating counters in Bigtable within seconds; the ranker reads the fresh row. Keep the streaming features few and cheap; the daily batch does the rest.
3. *Cold items.* Thousands of new items per minute have no interactions. Solve by embedding new items from content features (title, transcript, thumbnail) at ingest so the item tower can place them, and by an explicit exploration slot in the ranked list so they gather signal; log the slot so training can account for it.
4. *Cold users.* No history at first request. Solve with a contextual fallback (region, device, time, onboarding choices) and popularity within segment; move to the personalised path once a few actions exist.
5. *The 100 ms budget.* Solve by parallel fan-out with deadlines (candidates 10 ms, features 10 ms, ranking 30 ms), hedged reads to the feature store (idempotent, safe to hedge), item features cached in the ranker, and a precomputed fallback list when any stage misses. Report p99 per stage.
6. *Feedback loops and position bias.* Items shown at the top get clicks because they are at the top. Solve by logging position and training with position as a feature that is fixed to a constant at serving, by randomised exploration on a small slice, and by off-policy evaluation before online tests.
7. *Model rollout.* A new ranker that looks better offline may hurt engagement. Solve with the experiment platform (Q8): shadow scoring, then a small arm with guardrail metrics, automatic ramp-down on regression, and a model registry that records the training data snapshot and features.
8. *Scale of the index.* 100 million item vectors fit on a few machines; the harder part is refreshing the index as item embeddings change. Solve as in Q2: a delta segment and periodic rebuilds, with item embeddings versioned alongside the tower that produced them (a user tower from version N must query item vectors from version N).

**Deep dive: the ranker's serving path.** A request's 300 candidates are scored in one batched call: the user features are broadcast, the item features come from the ranker's local cache (refreshed every few minutes from Bigtable), and the context features travel with the request. The output is a score per candidate; a policy layer then applies diversity (no three videos from one creator), business rules, exploration and the final cut. Separating the learned score from the policy layer keeps the model simple and the rules auditable.

**Deep dive: the training pipeline.** Impressions and outcomes are joined in BigQuery with a delay window (a click can come minutes later); training examples are built with the logged features; a daily job trains, evaluates against the previous model on held-out days, and registers the model with its data snapshot. A nightly skew report and a weekly offline-to-online correlation check (did offline gains predict online gains) keep the loop honest.

**Failure, scale, cost.** Feature store degraded: serve with cached or default features, flag the impressions, exclude them from training. Candidate index down: fall back to the other candidate sources. Ranker overloaded: rank fewer candidates (shed from 300 to 100) before failing requests. Cost: ranking compute scales with candidates per request, so the candidate count is the main cost knob; the feature store's read volume is the second.

**What the interviewer probes.** "Why two stages?" (you cannot score the catalogue; the first stage is an index.) "How do you know the model is better?" (offline metrics, then an online experiment with guardrails; offline gains do not always transfer.) "What if a feature pipeline is late?" (the ranker reads stale values and the training set knows it.) "How do you handle a viral item?" (hot key on the feature store: cache it in the ranker; hot shard on the index: replicate it.)

**Internal analogues.** Bigtable, the two-stage YouTube recommendation architecture, Flume for the training data pipeline, Borg for serving, the layered experiment infrastructure.

### Q4. Design a durable execution service for long-running, multi-step agents with tool side effects

**Intuition.** An agent run is a workflow whose steps are decided at run time by a model. The workflow problem is older than agents: a process that runs for hours, calls external systems, and must survive the machine it runs on dying. The classical answer is that the process does not own its state; a durable log does. Every step is recorded before and after it happens, and any worker can pick the run up by replaying the log. The agent twist is that two kinds of steps are special: tool calls with side effects, which must happen exactly once in the world even though the system can only guarantee at-least-once execution; and model calls, which are non-deterministic and expensive, so a replay must reuse the recorded output instead of calling the model again. Everything else is a scheduler with leases.

**Clarify.** Agents run for minutes to hours, call tools with real side effects (tickets, emails, payments), must survive worker restarts, must never execute a side effect twice, pause for human approval, and must be observable per step. 10,000 concurrent runs; a few thousand tool calls per second; some runs are regulated and must not lose state in a region failure.

**Numbers.** 10,000 concurrent runs with a step every few seconds is a few thousand step appends per second; Spanner handles that comfortably in one region, and multi-region adds commit latency of tens of milliseconds, acceptable for steps measured in seconds. Step payloads: a tool result can be megabytes; the log holds a pointer to Cloud Storage above a threshold. Leases: 10,000 rows with second-granularity expiries; a lease sweep every second is trivial.

**Design.** The run is a state machine persisted outside the worker: run state and the step log in Spanner (external consistency means every worker sees the same step history; a run is a row group keyed by run id, steps are interleaved child rows). Workers on Cloud Run or GKE lease a run (a lease row with an owner and an expiry), execute one step (a model call or a tool call), append the step with its result, and release or renew; a lease that expires is taken over by another worker, which replays from the step log, not from memory. Tool calls with side effects carry an idempotency key derived from (run id, step number, canonical arguments); the tool server stores the key with the result, so a retried call returns the stored result instead of acting twice. Human approvals are steps that park the run; Cloud Tasks schedules the wake-up and the timeout. Agent Runtime on the Gemini Enterprise Agent Platform packages the worker side, with Memory Bank for cross-run memory and Agent Gateway for tool policy; the parts you own are the step log and the idempotency contract.

```
API → run created (Spanner: runs, steps, leases) → Pub/Sub "runnable"
worker: lease run → read step log → next step:
   model call  → record prompt hash, model version, output → append
   tool call   → append INTENT(idempotency key) → call tool → append RESULT
   approval    → park; Cloud Tasks timer → resume
→ release lease; crash → lease expires → another worker replays the log
large payloads → Cloud Storage with pointer; traces → Cloud Trace per step
```

**Challenges and how to solve them.**

1. *Exactly-once side effects.* Delivery is at-least-once; the receiver makes it once. Solve with the write-ahead intent: append "about to call tool X with key K" to the log, call the tool with K, append the result. A crash between the two is resolved on replay by asking the tool server what happened with K (it either has the result or never saw the key). The tool server keeps keys for longer than any run can be retried.
2. *Tools that are not idempotent.* A legacy system with no key support. Solve with a two-phase wrapper (reserve, then confirm; the reserve is harmless if abandoned), or by requiring a human approval step before the call so a duplicate is caught by a person, or by querying the system for the effect before retrying (does ticket with external id K exist?).
3. *Replaying the model.* Re-calling the model on replay produces a different trajectory and doubles cost. Solve by recording model outputs in the log and replaying them verbatim; the model is called only for the next undecided step. Store the prompt hash and model version so a later investigation can diff what the model saw (chapter 64).
4. *Lease correctness.* Two workers believe they own a run (a paused worker wakes after its lease expired). Solve with a fencing token: each lease grant increments a number stored with the run; every append carries the token and Spanner rejects an append with a stale one. This is the Chubby lesson: a lease without fencing is a hope.
5. *Long pauses.* Approvals can take days; a worker cannot hold the run. Solve by making "waiting" a persisted state with no worker; Cloud Tasks (or a scheduler scanning Spanner) wakes it; timeouts are steps too.
6. *Runaway runs.* An agent loops on a failing tool. Solve with per-run budgets recorded in the log (steps, tokens, dollars, wall-clock) checked before each step, and a kill switch that marks the run cancelled so the next lease holder stops (chapter 63's governance).
7. *Large and sensitive payloads.* A tool returns a 50 MB report containing personal data. Solve with Cloud Storage for payloads above a threshold with a pointer in the log, redaction before logging, per-tenant encryption keys, and retention policies on both.
8. *Observability per step.* Solve with a trace per run and a span per step carrying the step type, tool name, idempotency key, tokens, latency and outcome; the step log and the trace share ids so a trace links to the exact log entry.
9. *Versioning the agent.* A run started on agent version 3 should not be replayed by version 4's logic. Solve by recording the version on the run and routing leases to workers of that version (or by making step replay purely data-driven so any version can replay).

**Deep dive: the step log schema.** `runs(run_id, tenant, agent_version, state, budget, lease_owner, lease_expiry, fence)`; `steps(run_id, step_no, kind, input_ref, output_ref, idempotency_key, model_version, prompt_hash, started_at, finished_at, status)` interleaved under `runs` so a run and its steps are co-located in Spanner; `approvals(run_id, step_no, approver, decision, decided_at)`. Reads on resume fetch the run row and its steps in one range read. Writes are one transaction per step (intent and result as two rows when a side effect is involved). The fence column is the single most important detail in the review.

**Deep dive: what the platform gives you.** Agent Runtime manages workers, sessions and memory; Agent Gateway applies tool policy and quotas; Cloud Trace collects spans. Keep the step log and the idempotency contract in your own service even when you adopt the platform, because they define the correctness of side effects, and you will want to run them across clouds.

**Failure, scale, cost.** Worker fleet dies: runs resume from the log on new workers within the lease expiry. Spanner regional outage: regulated tenants on a multi-region configuration continue; others pause and resume. Hot run (a single run with thousands of steps): shard its steps across row ranges by step bucket. Cost: model tokens dominate; the per-step controller from chapter 65 (effort by step class, compaction of the recorded context) lives in the worker.

**What the interviewer probes.** "What happens if the worker crashes after the tool call but before recording the result?" (the intent is in the log; replay asks the tool server by key.) "Two workers at once?" (fencing token.) "Can you replay deterministically?" (yes for recorded steps; the next model call is new.) "How do you cancel?" (state flag checked per step; in-flight tool calls complete or are compensated.)

**Internal analogues.** Spanner, Chubby-style leases with fencing, Pub/Sub, the workflow engines behind Cloud Workflows.

### Q5. Design the training infrastructure for a foundation model on TPU pods

**Intuition.** Training a large model is one synchronous computation spread across thousands of chips: every step, every chip computes its slice of the forward and backward pass, the gradients are averaged across all of them, and nobody can proceed until the slowest has finished. That single fact drives the design. The job is only as fast as its slowest participant, so stragglers must be found and removed; a single failure stops everything, so recovery time (checkpoint interval plus restart) is a first-class metric; and the accelerators are so expensive that any second they spend waiting for data or for a checkpoint write is the most costly idle time in the company. The second intuition is that the model does not fit on one chip, so it is cut three ways: across data (each group sees different examples), across tensors (each chip holds a slice of each matrix) and across layers (a pipeline), and the right mix depends on the interconnect. The third is that the data pipeline is a distributed system of its own and is usually the one that is under-built.

**Clarify.** A model with tens to hundreds of billions of parameters, trained for weeks on thousands of chips, from a multi-petabyte corpus in Cloud Storage; the run must survive chip and host failures without losing more than minutes of work; researchers want to resume, branch and evaluate checkpoints; the corpus must be deduplicated and filtered, and its composition must be reproducible.

**Numbers.** A 100B-parameter model in mixed precision needs on the order of 16 bytes per parameter for weights, gradients and optimiser state, about 1.6 TB, so it is sharded across hundreds of chips before any activation memory is counted. A checkpoint of that state is roughly a terabyte; written in parallel from hundreds of hosts to Cloud Storage at a few gigabytes per second each, it takes tens of seconds, which bounds how often you can checkpoint synchronously and motivates asynchronous checkpointing. Input: at tens of thousands of tokens per second per chip and thousands of chips, the pipeline must deliver on the order of a hundred million tokens per second, hundreds of megabytes per second of pre-tokenised data, continuously. A thousand-host job with a mean time between host failures of a year per host sees a failure every nine hours on average; over a month-long run that is dozens of restarts, so restart cost is a budget line.

**Design.** Compute: TPU pod slices on GKE or the managed training service, programmed through JAX with sharding annotations (data parallel across slices, tensor and pipeline parallel within), with Pathways as the orchestration layer that lets one controller drive many pods and keep going when a slice is lost. Data: a preprocessing pipeline in Dataflow that cleans, deduplicates (exact and near-duplicate by hashing), filters, tokenises and shards the corpus into fixed-size files in Cloud Storage, with a manifest recording the mixture weights and the shard order; a deterministic shuffle keyed by epoch and shard so a resumed run reads exactly where it stopped; host-side input workers that prefetch and batch so accelerators never wait. Checkpointing: asynchronous, sharded checkpoints (each host writes its own shard) to Cloud Storage every N steps, with a faster local-SSD or in-memory copy more often; a checkpoint manager keeps the last K, the evaluation-tagged ones and the branch points. Monitoring: step time, accelerator utilisation, loss and gradient norms, input-queue depth and per-host step time streamed to Cloud Monitoring, with alerts on step-time regression and loss spikes. Evaluation: a separate small job evaluates each tagged checkpoint on held-out sets and benchmarks and writes results to BigQuery against the checkpoint id.

```
corpus (Cloud Storage) → Dataflow: clean, dedupe, filter, tokenise, shard, manifest → sharded files
controller (Pathways) → pod slices (JAX, sharded: data × tensor × pipeline) ← host input workers (prefetch)
every N steps: async sharded checkpoint → Cloud Storage; local fast checkpoint more often
monitoring: step time per host, utilisation, loss, grad norm, input queue → alerts
eval job: tagged checkpoints → benchmarks → BigQuery
```

**Challenges and how to solve them.**

1. *Failures stop everything.* Solve with fast detection (a health check per host and a step-time watchdog), automatic replacement of the failed slice from a standby pool, and resumption from the latest checkpoint; make checkpointing asynchronous so a short interval does not cost step time: the state is copied to host memory in one step and written to storage while training continues. Choose the interval by balancing the write cost against the expected rework (interval divided by two, times the failure rate). Pathways-style controllers can keep the job running on the remaining slices for data-parallel configurations while the replacement joins.
2. *Stragglers.* One slow host (a thermally throttled chip, a bad link) slows the whole job. Solve by recording per-host step time and evicting hosts whose time is persistently above the median by a threshold; keep spare capacity so eviction does not require a restart.
3. *Memory.* The model does not fit. Solve by sharding the optimiser state and gradients across the data-parallel group (the ZeRO or fully sharded approach), by tensor parallelism within a high-bandwidth group, and by activation checkpointing (recompute activations in the backward pass instead of storing them), trading compute for memory. State the mix: tensor parallel within a slice where the interconnect is fastest, pipeline across slices, data parallel across pods.
4. *The input pipeline starves the chips.* Solve by pre-tokenising and pre-shuffling offline so the online path is sequential reads of fixed-size records; by placing data in the same region as the pod; by parallel readers per host with prefetch depth tuned to hide storage latency; and by monitoring input-queue depth as a first-class metric. If the queue drains, the chips are idle and the dashboard must say so.
5. *Reproducibility.* A resumed run must see the same examples in the same order. Solve with the manifest and a deterministic shuffle seeded by (epoch, shard, position), with the data position stored in the checkpoint; mixture changes are new manifests, not edits.
6. *Silent data corruption.* At this scale a bit flip in a chip or a link is a matter of time, and it shows up as a loss that drifts rather than crashes. Solve with checksums on checkpoints, periodic numerical self-checks on hosts, and comparison of loss trajectories across replicas or branches; keep enough checkpoints to roll back before the divergence.
7. *Checkpoint storage and lifecycle.* Terabyte checkpoints every half hour fill storage fast. Solve with a retention policy (last K, tagged, branch points), lifecycle rules to colder storage classes, and deduplicated sharded formats that allow partial restore (restore only the shards a smaller evaluation job needs).
8. *Data quality and deduplication.* Duplicates inflate the effective epoch count and leak evaluation sets. Solve with exact hashing plus near-duplicate detection (MinHash) in the Dataflow pipeline, decontamination against known benchmarks, and per-source quality classifiers with the filter thresholds recorded in the manifest.
9. *Multi-tenancy of the pods.* Researchers want to branch and run ablations. Solve with a scheduler that treats slices as the unit, preemptible lower-priority jobs for ablations, and checkpoint branching (a branch is a new run id pointing at a parent checkpoint and manifest).

**Deep dive: parallelism and the interconnect.** The all-reduce of gradients is the dominant communication; its cost is proportional to model size and inversely to interconnect bandwidth. Tensor parallelism needs the highest bandwidth (activations are exchanged every layer), so it stays inside a slice; pipeline parallelism exchanges activations only at stage boundaries and tolerates slower links; data parallelism exchanges gradients once per step and scales across pods. Overlap communication with computation (start reducing a layer's gradients while the next layer's backward pass runs). Report the fraction of step time spent communicating; above a threshold the parallelism mix is wrong for the hardware.

**Deep dive: the checkpoint manager.** Each host writes its shard to a staging prefix; a manifest is committed last, atomically, so a partially written checkpoint is never visible; restore reads the manifest and lets each host fetch its shard in parallel; a resharding utility converts a checkpoint between parallelism layouts so a model trained on 2,048 chips can be evaluated on 64. The manager also records the data position, the random state and the manifest id so resume is exact.

**Failure, scale, cost.** Loss of a whole pod: the job continues on the others in a reduced data-parallel configuration or pauses until capacity returns; the decision is policy. Storage outage: local checkpoints bridge short gaps. Cost: accelerator hours dominate; report utilisation (compute time over wall-clock) and goodput (useful steps over all steps, discounting rework after failures); a 10% utilisation gain on a multi-million-dollar run is the whole engineering budget.

**What the interviewer probes.** "How often do you checkpoint?" (a formula with the failure rate and the write cost, not a number.) "What happens when a host dies?" (detection, replacement, resume, and the goodput cost.) "Why is the input pipeline hard?" (bandwidth, determinism, and the fact that it is a distributed system nobody owns.) "How do you know the run is healthy?" (step time, loss and gradient norm trends, input queue depth, per-host variance.)

**Internal analogues.** Pathways, Borg, Colossus, the TPU interconnect, the JAX and XLA stack, Flume for the data pipeline.

### Q6. Design a global quota and rate-limiting service for a model API

**Intuition.** A rate limit is a counter that many machines in many regions must agree on, and agreement across continents costs 150 milliseconds per decision, which no API can afford. So the design accepts approximation: decisions are made locally against a budget handed out by a global authority, the budget is refreshed every few seconds, and the error (how far over the limit a customer can go in the worst case) is a stated, bounded number rather than zero. The second intuition is that limits on tokens are different from limits on requests: you do not know the cost of a request until the model has finished answering it, so the check before admission is an estimate and the debit after completion is the truth. The third is that the quota service must never be the reason the API is down; it fails open, within limits.

**Clarify.** Limits per customer in requests per minute and tokens per minute, plus optional hard monthly spend caps; enforced within a second of the true usage across three regions, at 100,000 decisions per second; customers see their remaining budget in response headers; the service must not add more than a millisecond to the request path.

**Numbers.** 100,000 decisions per second across, say, 300 gateway instances is about 330 decisions per second per instance, trivial for an in-memory bucket. A global tier that receives a usage report from each instance every second handles 300 reports per second, also trivial; the challenge is correctness, not load. The worst-case overrun with local buckets and one-second refresh is one second of a customer's limit per region plus one request's worth of tokens per instance, which for a 10,000-token-per-second customer across three regions is on the order of 30,000 tokens plus in-flight requests, a number you can print in the contract.

**Design.** Two tiers. Local: each gateway instance holds a token bucket per active customer in memory and makes the fast decision; it reports consumption to the global tier every second and receives a refreshed allotment. Global: a quota service backed by Memorystore (Redis) for live counters with Spanner as the durable source of limits, of monthly spend and of the audit log; the global tier divides each customer's per-minute limit across regions by observed share and rebalances every few seconds. The gateway fails open to its local bucket if the global tier is unreachable, with the allowance capped at a fraction of the limit so an outage cannot become unlimited admission. Token-based limits: the admission check uses an estimate (prompt tokens, counted locally, plus the customer's average output), the bucket is debited with the true count on completion, and the next allotment corrects any drift. Spend caps: enforced at the global tier asynchronously against Spanner, with a small overrun tolerance written into the contract; a customer at the cap is switched to a "deny" state pushed to every gateway within seconds.

```
request → gateway instance: local bucket[customer] (estimate) → admit / 429 (retry-after, remaining in headers)
          ↓ every second: report usage; receive allotment
global quota service: Memorystore counters (per customer, per region) · rebalance by share
                      Spanner: limits, spend, audit · spend-cap state pushed to gateways
failure: global tier unreachable → local bucket at capped allowance (fail open, bounded)
```

**Challenges and how to solve them.**

1. *Exactness versus latency.* Solve by stating the bound. Local buckets with periodic refresh give enforcement within a known error; customers who need exact caps get the asynchronous spend-cap path with its own tolerance. Never put a cross-region write on the request path.
2. *Cost unknown at admission.* Solve with the estimate-then-settle pattern: reserve an estimate, settle the true token count on completion, reconcile at the next refresh. Keep a per-customer average output length to improve the estimate; for streaming responses, debit incrementally so an abandoned stream is charged for what it produced.
3. *Hot customers.* One customer sends half of all traffic and its counter lands on one Redis shard. Solve with counter sharding: the customer's counter is split across N keys with a random suffix, summed on read; and with consistent hashing of customers to shards so instance churn does not move everyone.
4. *Uneven regional demand.* A customer is 90% in one region today and 60% tomorrow. Solve with share-based rebalancing: the global tier allots each region a share proportional to its recent usage plus a floor, re-evaluated every few seconds; a region that exhausts its share can borrow from the global pool before denying.
5. *Fail open without unlimited admission.* Solve with a capped local allowance (for example 50% of the limit per region) when the global tier is unreachable, a short timeout on the report call, and an alarm; the audit log records every fail-open window.
6. *Clock and burst semantics.* A "per minute" limit can be a fixed window (bursty at boundaries) or a sliding window or a token bucket (smooth). Solve by choosing the token bucket with a burst capacity equal to a few seconds of the limit, and say why: it is smooth, cheap, and its semantics are explainable in a header.
7. *Fairness inside a customer.* A customer's own batch job starves its interactive users. Solve with optional sub-keys (per API key, per project) with their own buckets nested under the customer's; nesting is a tree of buckets, each checked in order.
8. *Audit and disputes.* A customer disputes a 429. Solve with the per-second usage reports written to Spanner and queryable; the response carries a decision id that links to the report.
9. *Priority and degradation.* When capacity is short, who is admitted? Solve by giving the limit service a second output: not only "admit or deny" but "admit at priority P", so the inference platform (Q1) can queue accordingly; the platform's own admission control handles the moment-to-moment, the quota service handles the policy.

**Deep dive: the bucket maths.** A token bucket has capacity C and refill rate r; each request costs its estimated tokens; admission requires the bucket to hold that many; the bucket refills continuously. The local instance's bucket refills at its share of the customer's rate, assigned by the global tier; the sum of shares equals the limit; a share is a lease that expires if the instance stops reporting, so a dead instance's share returns to the pool. With N instances and a refresh period T, the worst-case overrun is the sum of in-flight requests plus one period of share drift; print it.

**Deep dive: consistency of the limit store.** Limits change rarely and must be consistent everywhere within seconds; Spanner holds them, and changes are pushed to the global tier and then to the gateways through a watch or a Pub/Sub topic. Spend accumulates constantly and must be durable; the global tier writes aggregated spend to Spanner every few seconds, which is why the cap has a tolerance.

**Failure, scale, cost.** Redis shard loss: counters are rebuilt from the next round of reports; a few seconds of inaccuracy. Spanner outage: limits are cached at the global tier; spend accumulation is buffered and replayed. Gateway instance death: its share expires and returns to the pool. Cost is negligible compared with the API it protects; the design's cost is complexity, which is why the bound must be simple to explain.

**What the interviewer probes.** "Why not a central counter?" (150 ms per decision across regions.) "How far over can a customer go?" (a formula and a number.) "What if the quota service is down?" (fail open, capped, alarmed.) "How do you limit tokens you have not generated yet?" (estimate, settle, reconcile.)

**Internal analogues.** The quota and rate-limiting layers of Google's API infrastructure; Maglev; Spanner for the limit store; Chubby-style leases for shares.

### Q7. Design a multi-region conversation and session store for a consumer assistant

**Intuition.** A conversation store has two customers with opposite needs. The model needs the recent history on every turn, fast and consistent (it must see the turn that was just written, or it contradicts itself), and the product needs the whole history durable, available from any device, deletable on request and auditable. One store cannot be both the fastest and the most durable, so the design uses two: a hot, single-region, strongly consistent document for the live session, and a durable, append-only log for everything. The second intuition is that the prompt is not the history: the store holds a compacted summary plus recent turns, and the prompt is assembled per turn, so the store's size per session stays bounded however long the conversation runs. The third is that "multi-region" for a consumer product means each user has a home, not that every write goes everywhere.

**Clarify.** 50 million daily users, sessions of tens of turns, each turn appends a few kilobytes; reads of the recent history on every turn; users expect to continue a conversation from another device within seconds; regulators expect deletion within a day; the model call is the latency budget, so the store gets 20 ms; some tenants require that their data never leave a region.

**Numbers.** 50 million users × 20 turns is a billion turns a day, about 12,000 writes per second average, perhaps 50,000 at peak; at a few kilobytes each that is a few hundred gigabytes of new data a day, tens of terabytes a year before compaction. Reads are one per turn plus continuation reads; the hot document read is a single-key fetch at a few milliseconds. Deletion: at one in a thousand users a day, 50,000 deletions a day touching turns, summaries, embeddings and caches; a batch job.

**Design.** Two stores with different jobs. The hot path: a per-session document in Firestore or a per-user row range in Bigtable in the user's home region, holding the last N turns and a compacted summary, read once per turn with strong consistency. The durable record: an append-only turn log in Spanner (multi-region configuration for the regulated tenants, regional for the rest), the source of truth for cross-device continuation, export and audit. A global directory (Spanner, multi-region, tiny) maps each user to a home region chosen at sign-up; the edge routes requests to it; a cross-region continuation reads from the home region, paying the 150 ms once, then the session is served from there. Compaction: when the hot document exceeds a size threshold, a summarisation step (a model call, recorded as a turn of its own) replaces old turns with a summary. Deletion: a tombstone in the directory makes the user invisible immediately; a Dataflow job removes the turns, the summaries, any embeddings in a memory index, and any entries in a semantic cache within the window, and writes a deletion receipt to the audit log. Memory across sessions (facts the assistant remembers) lives in a separate per-user store with its own consent flag and the same deletion path.

```
edge → directory (home region) → home region:
   hot session doc (Firestore / Bigtable, strong read) → prompt assembly (summary + recent turns) → model
   append turn → hot doc + Spanner turn log (durable, audit, export)
compaction: size threshold → summary turn → hot doc shrinks
deletion: tombstone (immediate) → Dataflow: turns, summaries, memory index, caches → receipt
other device: directory → home region (150 ms once) → continue
```

**Challenges and how to solve them.**

1. *Read-your-writes on the hot path.* The turn just written must be visible to the next read. Solve by keeping the hot document single-region and single-key: Firestore and Bigtable both give strong consistency for a single document or row; never serve the hot read from an asynchronous replica.
2. *Bounded context.* A thousand-turn session cannot be sent to the model. Solve with compaction (summary plus recent turns), with the summary stored as a turn so it is auditable and reversible, and with the prompt cached at the model layer by prefix so the summary is not re-processed on each turn (chapter 63).
3. *Cross-device continuation.* Device B in another region asks for the session. Solve with the home-region directory: the request is routed home; the user pays one cross-continent round trip; the client caches the home region. Do not replicate the hot document everywhere; replicate the durable log asynchronously for disaster recovery only.
4. *Deletion that reaches everything.* Deletion must cover the places the data went: the turn log, the hot document, summaries, memory embeddings, semantic caches, analytics exports and backups. Solve with a deletion manifest listing every store that holds user data (maintained as code and checked in review), a job that walks it and writes a receipt per store, backups with a retention shorter than the deletion window or a crypto-shredding scheme (per-user keys destroyed on deletion), and a periodic audit that searches for a deleted user's identifiers.
5. *Regional residency.* Some tenants' data may not leave a region. Solve with a per-tenant residency policy in the directory that pins the home region and disables cross-region replication for that tenant's log; the model call itself must also run in-region, so the inference platform (Q1) exposes regional pools.
6. *Home-region failure.* Solve with asynchronous replication of the durable log to a secondary region, a failover that updates the directory, a product-level disclosure (a banner that recent turns may be missing), and reconciliation by turn id when the home returns; the hot document is rebuilt from the log on failover.
7. *Hot users and abuse.* A bot drives a million turns into one session. Solve with per-session and per-user rate limits (Q6), a maximum session length that forces a new session, and row-range sharding in Bigtable so one user cannot hot-spot a tablet.
8. *Schema evolution.* Turn formats change (tool calls, images, citations). Solve with a versioned turn envelope, forward-compatible readers, and a migration job that rewrites old turns lazily on read.
9. *Privacy in logs and traces.* The observability pipeline is another copy of the data. Solve with redaction at the span level (hash user ids, drop content by default, sample content under consent), and include the trace store in the deletion manifest.

**Deep dive: the choice of hot store.** Firestore gives a document model with strong single-document consistency, native client SDKs and simple per-user security rules; Bigtable gives higher write throughput, row-range locality (all of a user's sessions adjacent) and lower cost at very large scale, with more operational work. At 50,000 writes per second either works; the choice turns on the client model (Firestore for mobile-first) versus the analytics path (Bigtable for row scans). Say both and pick one for the stated reason.

**Deep dive: the durable log in Spanner.** Schema: `users(user_id, home_region, residency, tombstone)`, `sessions(user_id, session_id, created_at, state)`, `turns(user_id, session_id, turn_no, kind, content_ref, model_version, created_at)` interleaved under sessions; a turn's content above a threshold lives in Cloud Storage with a pointer. Spanner's external consistency makes the export and the audit trivially ordered; the multi-region configuration is used only where the regulated tenants' availability requirements justify its commit latency.

**Failure, scale, cost.** Firestore or Bigtable regional outage: the session cannot be continued until failover; the model path degrades to "new session" with an explanation. Spanner outage: hot path continues; durable appends buffer in Pub/Sub and replay. Cost: storage is cheap; the model calls for compaction are not, so compaction thresholds are tuned to the model's prefix-cache behaviour; the deletion job is a daily batch.

**What the interviewer probes.** "Why two stores?" (consistency and latency versus durability and audit.) "What does the user see if their region is down?" (a disclosed degradation, not silence.) "How do you prove deletion?" (manifest, receipts, audit search.) "Where is the prompt assembled?" (in the application, from the hot document, cached by prefix at the model.)

**Internal analogues.** Bigtable, Spanner, the global user directory pattern, the deletion pipelines behind Google's privacy infrastructure.

### Q8. Design the evaluation and experimentation platform for LLM features across many product teams

**Intuition.** A model feature cannot be tested like code, because its output is a distribution. So the platform's job is to make statements about distributions cheaply and repeatably: offline, by replaying a frozen dataset through a candidate configuration and measuring with deterministic checks and calibrated judges; online, by assigning users to arms and measuring outcomes with intervals. The second intuition is that the platform's product is trust: a result nobody believes is worse than none, so every number carries its configuration hash, its data snapshot, its judge version with calibration, and an interval computed the same way for everyone. The third is that judging costs money and the platform is the natural place to spend it well: caching verdicts, using cheap judges with escalation, and sampling production by risk.

**Clarify.** Hundreds of prompt and model changes a week across dozens of teams; offline evaluation before merge; online experiments with guardrails and automatic ramp-down; judges that cost money; results that teams and leadership trust; human labelling capacity that is scarce and must be aimed.

**Numbers.** 500 changes a week × a frozen set of 2,000 items × four judged criteria is four million judge calls a week; at a cheap tier that is thousands of dollars a week, at a frontier tier tens of thousands, so caching unchanged verdicts and routing to a cheap calibrated judge matter. Online: 50,000 requests per second of product traffic logged with arm and configuration is a few hundred megabytes per second into Pub/Sub; daily metric jobs over tens of terabytes in BigQuery. Human labels: a few thousand a week; the sampling policy decides where they go.

**Design.** Offline: every change opens an evaluation run; a job replays the feature's frozen dataset through the candidate configuration (prompt, model, retrieval, tools) on the inference platform's batch tier, runs deterministic checks and LLM judges (chapter 66) with cached verdicts for unchanged items, and writes per-item results to BigQuery keyed by configuration hash and dataset snapshot; a CI gate compares against the baseline with paired statistics, per-slice thresholds and a cost delta. Online: an experiment service assigns users to arms by a stable hash with layered, mutually exclusive experiments; the serving path logs arm, configuration, model version and outcome signals to Pub/Sub and BigQuery; guardrail metrics (latency, cost per request, refusal rate, safety classifier rate, error rate) are computed in near real time by Dataflow and trigger automatic ramp-down; the primary metric is computed daily with confidence intervals, a minimum run length and a pre-registered analysis. Human review: a sampling service pulls production traffic into labelling queues by risk and novelty; labels feed back into the frozen datasets and the judge calibration sets; an anchor set is re-scored continuously to separate judge drift from product drift. A registry holds datasets, judges (prompt hash, model, calibration), configurations and results.

```
change → eval run: frozen dataset (snapshot) × candidate config → batch tier → checks + judges (cached) → BigQuery
      → CI gate: paired stats, slice thresholds, cost delta → merge / block
serving → experiment service (hash → arm, layers) → logs (arm, config, outcome) → Pub/Sub → BigQuery
      → Dataflow guardrails (near real time) → ramp-down; daily primary metric with intervals
production sample → labelling queues (by risk, novelty) → labels → datasets, judge calibration, anchor set
registry: datasets · judges (+calibration) · configurations · results
```

**Challenges and how to solve them.**

1. *Reproducibility.* A result must be recomputable next month. Solve by snapshotting datasets (immutable versions in Cloud Storage), hashing configurations, pinning model versions, recording judge versions, and storing per-item results rather than only aggregates.
2. *Judge cost and latency.* Solve with verdict caching by (item, configuration, judge version), a cheap calibrated judge for the bulk with escalation of low-confidence items to a strong judge, the batch tier at half price, and sampling policies per feature by traffic and risk (chapter 66).
3. *Judge drift and trust.* Solve with calibration numbers attached to every judge version (true-positive and true-negative rates and kappa against humans), the anchor set re-scored continuously, and a rule that a judge model change triggers a parallel run and re-calibration before its verdicts count.
4. *Experiment interference.* Two teams' experiments on the same users confound each other. Solve with layered experiments: orthogonal layers for independent features, mutually exclusive arms within a layer, and a central assignment service so no team hashes its own way.
5. *Peeking and false positives.* Teams look at the dashboard daily and stop when it looks good. Solve with pre-registered metrics and run lengths, sequential testing methods designed for continuous monitoring, and a central analysis service so intervals are computed identically; the dashboard shows "not yet decidable" rather than a tempting point estimate.
6. *Guardrails that act.* A new prompt doubles cost or raises refusals. Solve with near-real-time guardrail metrics from Dataflow, thresholds per feature, and automatic ramp-down to zero with a page, independent of the primary metric.
7. *Slices and fairness.* An average that improves while a language or a segment regresses. Solve with per-slice gates offline and per-slice reporting online, with minimum sample sizes per slice before a slice is reported.
8. *Human labelling as a scarce resource.* Solve with a sampling service that prioritises novelty (inputs unlike the frozen set), judge disagreement, user complaints and high-risk features; labels are versioned and traceable to the labeller and the guidelines version.
9. *Agent trajectories.* Multi-step features need trace-level evaluation. Solve by storing traces (chapter 64) as the evaluation unit, judges per dimension (tool choice, arguments, completion, policy adherence), verifiers for anything checkable, and pass^k from repeated runs.
10. *Privacy in evaluation data.* Frozen sets built from production contain user data. Solve with redaction and synthetic augmentation, access controls on datasets, retention limits, and inclusion of the evaluation stores in the deletion manifest (Q7).

**Deep dive: the offline gate's statistics.** Per-item results for baseline and candidate on the same items give a paired comparison; for binary checks, McNemar's test on discordant pairs; for rates, a bootstrap interval on the paired difference; the gate blocks on any critical check regressing, on the overall pass rate falling beyond the interval, and on cost per item rising beyond a threshold. The dataset's size is chosen from the regression you want to detect (a few hundred items to see a 3-point change; chapter 32b), and a frozen set is retired and rebuilt when the product's input distribution drifts from it.

**Deep dive: the online analysis.** Assignment by a salted hash of the user id per layer; exposure logged at the moment the feature is actually used (not at assignment), to avoid dilution; outcomes joined by user and window in BigQuery; metrics defined once in a shared library; intervals by the delta method or bootstrap at the user level (not the request level, which overstates precision); ramp plan 1% → 5% → 25% → 50% with guardrails checked at each step.

**Failure, scale, cost.** Logging pipeline lag: experiments pause their decisions, not their traffic. Judge platform outage: offline runs queue; CI reports "pending" rather than passing. Cost: judge calls and BigQuery scans; both are controlled by caching, sampling and partitioned tables.

**What the interviewer probes.** "How do teams trust each other's results?" (the registry, the shared analysis library, calibration on every judge.) "What stops a team from shipping on noise?" (pre-registration, sequential tests, minimum run lengths.) "How do you evaluate an agent?" (traces, per-dimension judges, verifiers, pass^k.) "What does a judge cost you?" (a number per item, and the caching that keeps it there.)

**Internal analogues.** Google's layered experiment infrastructure, Flume for log processing, BigQuery (Dremel) for analysis, the human-rating pipelines behind search quality.

## 40b.18 Trade-offs you should be able to say in one breath

- **Consistency:** Spanner for external consistency when a wrong read costs money; Bigtable or Firestore for single-row atomicity at scale; asynchronous replication across regions with the lag disclosed.
- **Latency:** cache the prefix, pre-filter the index, fan out in parallel with deadlines, hedge only idempotent reads, shed load before the tail grows.
- **Throughput:** continuous batching and utilisation decide the accelerator bill; a half-idle fleet costs twice per token.
- **Freshness:** delta segments and streaming features for seconds; rebuilds and batch features for hours; state the number.
- **Exactly-once:** does not exist on the wire; idempotency keys, fencing tokens and a write-ahead step log give it at the receiver.
- **Permissions:** enforced in the index filter and the data layer under the user's identity; missing ACL means deny; propagation lag is an SLO.
- **Cost:** report cost per successful request, utilisation, goodput and cache-hit ratio; commit only for the floor of the curve.
- **Failure:** every design loses a zone without a page and a region with a disclosed degradation.

## 40b.19 Pitfalls that lose the round

Starting to draw before stating numbers. Treating the model call as free or instant. A single region with no story for its loss. Exact global counters at 150 ms per request. Post-filtering a vector search by permission. Re-embedding a corpus in place on a model upgrade. Replaying a workflow by re-running the model. A lease without a fencing token. Synchronous cross-region writes on the hot path. Checkpointing "every hour" with no formula. No canary and no rollback path for a model or prompt change. Naming a retired product (Vertex AI Search is Agent Search; Vertex AI Pipelines is Agent Platform Pipelines; Data Catalog was shut down in 2026). Forgetting observability until asked: a trace per request with tokens, cache hits and queue time is part of the design, not an add-on.

## Sources

Links and papers checked in October 2026.

**Fundamentals (40b.1–40b.14)**
- Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017 (the standard text for sections 2–6).
- Dean and Barroso, *The Tail at Scale*, Communications of the ACM, 2013.
- Lamport, *Time, Clocks, and the Ordering of Events in a Distributed System*, 1978; Ongaro and Ousterhout, *In Search of an Understandable Consensus Algorithm (Raft)*, 2014.
- Burrows, *The Chubby Lock Service*, OSDI 2006; Corbett et al., *Spanner*, OSDI 2012; Chang et al., *Bigtable*, OSDI 2006; Ghemawat, Gobioff and Leung, *The Google File System*, SOSP 2003.
- Akidau et al., *The Dataflow Model*, VLDB 2015.
- Pang et al., *Zanzibar*, USENIX ATC 2019; Eisenbud et al., *Maglev*, NSDI 2016; Sigelman et al., *Dapper*, 2010; Adams et al., *Monarch*, VLDB 2020; Verma et al., *Borg*, EuroSys 2015.
- Beyer et al., *Site Reliability Engineering*, O'Reilly, 2016, and *The Site Reliability Workbook*, 2018.
- Abadi, *Consistency Tradeoffs in Modern Distributed Database System Design (PACELC)*, IEEE Computer, 2012.
- Google Cloud documentation for Spanner, Bigtable, Firestore, Pub/Sub, Dataflow, Memorystore, GKE and Cloud Trace, October 2026.

**The eight questions (40b.15–40b.19)**
- Dean and Barroso, *The Tail at Scale*, Communications of the ACM, 2013.
- Corbett et al., *Spanner: Google's Globally-Distributed Database*, OSDI 2012; Chang et al., *Bigtable*, OSDI 2006.
- Burrows, *The Chubby Lock Service for Loosely-Coupled Distributed Systems*, OSDI 2006.
- Pang et al., *Zanzibar: Google's Consistent, Global Authorization System*, USENIX ATC 2019.
- Eisenbud et al., *Maglev: A Fast and Reliable Software Network Load Balancer*, NSDI 2016.
- Akidau et al., *The Dataflow Model*, VLDB 2015; *MillWheel*, VLDB 2013.
- Sigelman et al., *Dapper, a Large-Scale Distributed Systems Tracing Infrastructure*, 2010; Adams et al., *Monarch*, VLDB 2020.
- Verma et al., *Large-scale cluster management at Google with Borg*, EuroSys 2015.
- Barham et al., *Pathways: Asynchronous Distributed Dataflow for ML*, MLSys 2022.
- Kwon et al., *Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM)*, SOSP 2023.
- Guo et al., *Accelerating Large-Scale Inference with Anisotropic Vector Quantization (ScaNN)*, ICML 2020.
- Covington, Adams and Sargin, *Deep Neural Networks for YouTube Recommendations*, RecSys 2016.
- Tang et al., *Overlapping Experiment Infrastructure: More, Better, Faster Experimentation*, KDD 2010.
- Beyer et al., *Site Reliability Engineering* (the SRE book), 2016.
- Google Cloud documentation for GKE, Spanner, Bigtable, Firestore, Pub/Sub, Dataflow, Memorystore, Vector Search, AlloyDB, Agent Runtime, Agent Search, Agent Gateway and Model Armor, October 2026.

**In this book:** chapter 40 (application design exercises), 63 (token costs), 64 (trace-first troubleshooting), 65 (reasoning budgets in the worker), 66 (judges), 67 (authorisation).
