# Distributed systems design fundamentals

The principles behind every design in *Distributed Systems Design Questions for AI Engineers*, written for someone who has built services but has not had to argue them on a whiteboard. Each section gives the intuition, the standard vocabulary, the trade-off, and the Google-flavoured example an interviewer will recognise. Dated October 2026.

## 1. Why distributed systems are hard: the three facts

Everything in this subject follows from three facts about machines connected by networks.

1. **Messages are delayed and lost, and you cannot tell which.** A request that gets no reply may have been dropped on the way there, processed and dropped on the way back, or still be in a queue. So every sender must decide what to do with silence, and every receiver must tolerate receiving the same message twice. This fact alone produces timeouts, retries, idempotency and the impossibility of exactly-once delivery.
2. **Machines fail independently and partially.** A thousand hosts with a one-year mean time between failures see a failure every nine hours. Failures are not clean: a host can be slow rather than dead, reachable by some peers and not others, or alive with a corrupted disk. So the system must keep working through failures it cannot fully diagnose, which produces replication, leases, health checks and the rule that a slow replica is treated as a failed one.
3. **There is no shared clock.** Two machines cannot agree on what happened first without talking, and talking takes time. So ordering is something you build (logical clocks, consensus, a single leader) or buy with specialised hardware (Spanner's TrueTime, which bounds clock uncertainty with GPS and atomic clocks and then waits out the uncertainty before committing).

Hold these in mind and most "why" questions answer themselves.

## 2. The vocabulary of guarantees

**Consistency models** describe what a reader can see.

- *Linearizable (strong)*: every operation appears to happen at a single instant between its start and end, in one global order; a read after a write sees the write. The easiest to program against and the most expensive, because agreeing on the order costs a round trip to a majority.
- *Sequential*: all participants see the same order, but not necessarily in real time.
- *Causal*: if A caused B, everyone sees A before B; unrelated writes may be seen in different orders. Cheap and often enough for user-facing data.
- *Eventual*: replicas converge if writes stop; a read may return old data. Cheapest; the application must tolerate staleness.
- *Read-your-writes, monotonic reads*: session guarantees that make eventual consistency bearable for one user (a user sees their own writes; a user never sees time go backwards).

**External consistency** is Spanner's term for linearizability across a globally distributed database: a transaction that commits after another in real time is ordered after it everywhere. It is why a Spanner read can be trusted as the source of truth in a step log or a directory.

**CAP and PACELC.** During a network partition a system must choose between staying available and staying consistent (CAP). PACELC adds the everyday case: even without a partition, there is a trade-off between latency and consistency, because consistency requires coordination and coordination costs round trips. The useful form of the question is not "CP or AP" but "which operations need coordination, and how far away are the participants". Spanner coordinates across regions and pays the latency; Bigtable coordinates within a row and nothing more; Firestore is strongly consistent per document; caches are eventually consistent by design.

**Durability** is a separate axis: a write acknowledged after one replica's memory, one replica's disk, a majority's disks, or a cross-region majority's disks are four different promises with four latencies. Say which one you are making.

## 3. Replication, partitioning and placement

**Replication** copies data for durability and read scaling. Leader-based (one replica accepts writes, others follow) is simple and gives a clear order; multi-leader allows writes in several regions and forces conflict resolution; leaderless (quorum reads and writes) trades a global order for availability. Synchronous replication waits for followers before acknowledging and costs their latency; asynchronous does not and risks losing acknowledged writes on leader failure. Most production systems are leader-based with synchronous replication to a local majority and asynchronous replication to other regions, and say so.

**Partitioning (sharding)** splits data so no machine holds all of it. By hash (uniform, no range scans), by range (scans, hot ranges), or by a composite that puts related rows together (Bigtable row keys, Spanner interleaved tables). The problems are hot partitions (one key or range gets most of the traffic), rebalancing (moving partitions when machines come and go) and cross-partition operations (a transaction spanning shards needs two-phase commit or a design that avoids it). Consistent hashing assigns keys to machines so that adding one machine moves only a fraction of the keys; it is the basis of every cache ring and of Maglev's connection-stable load balancing.

**Placement** decides where replicas live. Zones within a region fail independently of each other and share low latency; regions fail together only in a disaster and are far apart. The standard pattern is three zones for availability and a second region for disaster recovery, with the data-residency rules of the tenant deciding whether the second region is allowed to exist.

## 4. Consensus, leaders and leases

**Consensus** lets a set of machines agree on a sequence of values despite failures: Paxos, Raft and their relatives. A majority (quorum) must acknowledge each value, so the system tolerates fewer than half of its members failing and pays one round trip to the quorum per decision. You rarely implement consensus; you use a service that does (Chubby inside Google, ZooKeeper and etcd outside, Spanner's Paxos groups underneath its tables) for the few things that must be agreed: who is leader, what the configuration is, which version is current.

**Leader election** picks one machine to serialise decisions. It is cheap once a consensus service exists: the leader holds a lease.

**Leases** are the time-bounded locks of distributed systems. A lease says "you are the owner until time T" and must be renewed; if the owner dies, the lease expires and another can take it. The trap is a paused owner (garbage collection, a long I/O stall) that wakes after expiry and still believes it owns the resource. The cure is a **fencing token**: every lease grant carries a monotonically increasing number, every write carries the number, and the storage rejects writes with a stale one. Chubby taught this lesson; the durable agent service in Q4 depends on it.

## 5. Time, ordering and idempotency

**Logical clocks** (Lamport, vector clocks) order events by causality without a shared physical clock; they tell you "A happened before B" or "A and B are concurrent", which is what conflict resolution needs. **Hybrid logical clocks** combine a physical clock with a counter so timestamps are both roughly real and causally consistent. **TrueTime** gives a physical interval with bounded uncertainty and lets Spanner order transactions in real time by waiting out the interval.

**Idempotency** is the property that doing an operation twice has the same effect as once. Since delivery is at-least-once, every operation with a side effect needs an **idempotency key** (chosen by the caller, stored by the receiver with the result) so a retry returns the stored result instead of acting again. Exactly-once *delivery* does not exist; exactly-once *effect* is built from at-least-once delivery plus idempotent receivers plus a durable record of intent (write-ahead) so a crash mid-operation can be resolved by asking what happened with the key.

**Ordering within a stream** is cheap (one partition, one writer); ordering across a system is expensive (consensus). Design so that the operations that need ordering share a partition (all of a user's events keyed by user id) and the rest do not.

## 6. Communication: synchronous calls, queues and streams

**Synchronous RPC** (gRPC with protocol buffers inside Google) is for requests that need an answer now. The rules: deadlines on every call, propagated through the chain so a slow dependency cannot hold a caller forever; retries only for idempotent calls and only with exponential backoff and jitter, with a retry budget so a struggling service is not amplified into an outage; circuit breakers that stop calling a dependency that is failing; and the recognition that a chain of N sequential calls has a tail latency that compounds.

**Queues** (Pub/Sub, Cloud Tasks) decouple producers from consumers in time and rate: the producer is acknowledged when the message is stored, the consumer processes when it can. They give at-least-once delivery, so consumers are idempotent; they absorb bursts, so the consumer can be sized for the average and the backlog is the buffer; and they make retries and dead-letter handling explicit. The costs are latency (a hop and a queue) and the loss of a synchronous error path (the producer does not know the consumer failed).

**Streams** add ordering within a key and the notion of event time versus processing time. The Dataflow model's contribution is the **watermark**: a statement that no events older than time T are expected, which lets a window close and emit a result while late events are handled by an explicit policy. Exactly-once processing in Dataflow is achieved by deterministic checkpointing of state and deduplication of inputs, not by magic on the wire.

**Backpressure** is what a system does when a downstream stage is slower than an upstream one: buffer (a queue, with a bound), shed (drop or reject the lowest-priority work), or slow the producer. A system with no backpressure plan fails by running out of memory at the most inconvenient stage.

## 7. Caching

A cache trades freshness for latency and cost. The questions to answer for every cache: what is the key, what is the lifetime, what invalidates it, what is the hit rate, and what happens on a miss storm. Patterns: **cache-aside** (the application reads the cache, then the store, then fills the cache), **write-through** (writes go to both), **write-behind** (writes go to the cache and drain later; fast and risky). Problems: **thundering herd** (a popular key expires and every request goes to the store at once; solve with request coalescing or staggered expiry), **hot keys** (one key on one node; solve with local caches in front of the shared cache or key replication), **stale reads after writes** (solve with explicit invalidation or short lifetimes, and never for data where staleness is a correctness bug), and **cache stampede on deploy** (a cold fleet; solve with warm-up or gradual rollout).

Model-specific caches have their own rules: the KV-cache prefix cache keyed by exact token prefix (anything that changes early in the prompt invalidates everything after it); semantic caches keyed by embedding similarity with staleness and tenancy risks; verdict caches in evaluation keyed by (item, configuration, judge version).

## 8. Load balancing, admission control and the tail

**Load balancing** spreads requests across replicas: at the network layer by consistent hashing of connections (Maglev), at the application layer by least-loaded or weighted round robin with health checks, and sometimes by affinity (prefix-cache routing in model serving, session affinity in stateful services). Affinity improves hit rates and worsens balance; say which you are optimising.

**The tail.** The p99 of a service that fans out to a hundred shards is dominated by the slowest shard, so a 1% slow rate per shard becomes a 63% slow rate per request. Dean and Barroso's remedies: **hedged requests** (send a second copy after the p95 and take the first reply; only for idempotent work), **tied requests** (send to two and cancel the loser), micro-partitioning so load can move, and selective replication of hot data. Generation requests cannot be hedged cheaply, so model serving bounds its tail with **admission control**: a queue-time budget per class, beyond which the request is rejected or degraded.

**Load shedding** is the deliberate rejection of work to protect the work that matters. Priorities are set at the edge (interactive before batch, paying before free), the cheapest rejection is the earliest, and a shed request gets an honest error with a retry-after, not a timeout.

## 9. Storage choices in one table

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

## 10. Reliability engineering: SLOs, error budgets and failure domains

An **SLO** is a target for a service-level indicator over a window (99.9% of requests under 300 ms over 30 days). The **error budget** is the allowed failure (0.1% of requests); when it is spent, reliability work takes priority over features. SLOs make trade-offs explicit: a 99.99% target permits 4 minutes of downtime a month and forbids most deployment practices that a 99.9% target allows.

**Failure domains** are the units that fail together: a process, a host, a rack, a zone, a region, a provider. Place replicas so that no single domain's loss breaks the SLO, and test it: Google's DiRT exercises and chaos engineering elsewhere exist because untested failover does not work.

**Graceful degradation** is the planned reduction of service under failure: serve from cache, serve a smaller model, serve popular items instead of personalised ones, disclose stale data with a banner. A system that either works perfectly or fails completely has not been designed for failure.

**Deployment safety**: canaries (a small fraction of traffic on the new version with automatic comparison), gradual rollout by zone and region, rollback by configuration rather than redeploy, and feature flags so behaviour can change without a binary change. For model features, the canary includes an evaluation suite, because a model change has no stack trace.

## 11. Observability

Three signals: **metrics** (aggregates over time; cheap; the basis of alerts), **logs** (events; expensive at scale; the basis of investigation), **traces** (a request's path across services with timing per hop; the basis of latency debugging). Dapper established the trace model Google uses; Monarch holds the metrics. The rules: propagate a trace id through every hop including queues; alert on symptoms the user feels (latency, errors, saturation) rather than causes; put the four golden signals (latency, traffic, errors, saturation) on every service's dashboard; sample traces at the tail so the slow ones are kept; and for model services, add tokens in and out, cache hits, queue time, prefill and decode time, and the model and prompt versions to every span, because that is how cost and quality regressions are found.

## 12. Security and multi-tenancy

Identity on every call (a service identity for machines, a user identity carried through delegation for user-facing work); authorisation at the data layer under that identity, not in the caller's good intentions; isolation between tenants at the level the risk justifies (shared tables with tenant columns and row filters; separate partitions; separate instances; separate projects); encryption in transit and at rest with per-tenant keys where deletion must be provable; secrets in a manager, never in configuration; egress controls so a compromised service cannot talk to the internet; and audit logs of every access decision. Zanzibar is the model for relationship-based authorisation at scale: a global, consistent store of "user is member of group, group can view document" tuples with a snapshot token so a check is never evaluated against permissions older than the content it protects.

## 13. Capacity planning and cost

Size from numbers: peak QPS with a growth factor, bytes per request, storage per day with retention, and the latency budget; then find the bottleneck resource (accelerator memory, network bandwidth, storage IOPS, a single leader) and design around it. Utilisation is the cost lever for expensive resources (accelerators, Spanner nodes): a resource at 30% utilisation costs three times per unit of work. Commit (reservations, committed-use discounts) for the floor of the demand curve and use on-demand for the peak. Report unit costs the business understands (per request, per thousand tokens, per successful task) and watch them per feature, because total spend hides a unit-cost regression under a traffic change.

## 14. The habits that show on the whiteboard

- State numbers before boxes, and say "order of magnitude".
- Name the consistency model of every store and the durability of every write.
- Put a deadline on every call and an idempotency key on every side effect.
- Say what happens when each box dies, and what the user sees.
- Separate the hot path from the durable path when their needs differ.
- Pre-filter, pre-compute and cache; hedge only what is idempotent; shed before the tail grows.
- Make rollout and rollback a configuration change.
- Draw the trace through the design, not after it.
- Give every trade-off a sentence: what you gain, what you pay, why it is right here.

## Sources and further reading

- Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017 (the standard text for sections 2–6).
- Dean and Barroso, *The Tail at Scale*, Communications of the ACM, 2013.
- Lamport, *Time, Clocks, and the Ordering of Events in a Distributed System*, 1978; Ongaro and Ousterhout, *In Search of an Understandable Consensus Algorithm (Raft)*, 2014.
- Burrows, *The Chubby Lock Service*, OSDI 2006; Corbett et al., *Spanner*, OSDI 2012; Chang et al., *Bigtable*, OSDI 2006; Ghemawat, Gobioff and Leung, *The Google File System*, SOSP 2003.
- Akidau et al., *The Dataflow Model*, VLDB 2015.
- Pang et al., *Zanzibar*, USENIX ATC 2019; Eisenbud et al., *Maglev*, NSDI 2016; Sigelman et al., *Dapper*, 2010; Adams et al., *Monarch*, VLDB 2020; Verma et al., *Borg*, EuroSys 2015.
- Beyer et al., *Site Reliability Engineering*, O'Reilly, 2016, and *The Site Reliability Workbook*, 2018.
- Abadi, *Consistency Tradeoffs in Modern Distributed Database System Design (PACELC)*, IEEE Computer, 2012.
- Google Cloud documentation for Spanner, Bigtable, Firestore, Pub/Sub, Dataflow, Memorystore, GKE and Cloud Trace, October 2026.
