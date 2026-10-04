# 47. FinOps as a discipline: cloud and AI cost management

> **What you need to be able to say:** what FinOps is (the practice and the role), its three phases, the data it runs on, the optimization catalogue for compute, storage, data and AI, how commitments work, how Kubernetes and GPUs are allocated, and how an AI engineer participates. Chapter 31 covers token-level FinOps; this chapter covers the whole bill.

## 47.1 Definition and the three phases

FinOps (the FinOps Foundation's framework) is the operating model that brings engineering, finance and product together to get the most value from cloud spend: **Inform** (visibility — allocation, tagging, showback/chargeback, unit economics, forecasts), **Optimize** (rates — commitments and discounts; usage — rightsizing, scheduling, architecture), **Operate** (budgets, anomaly alerts, policies, reviews, culture). Principles: teams own their usage, decisions are driven by business value (unit cost), everyone can see costs in near real time, and a central team enables rather than polices. In 2026 the framework explicitly extends to AI spend (tokens, GPUs, managed AI services) and to SaaS/licensing.

## 47.2 The role

A FinOps practitioner (or cloud cost engineer) builds the cost data pipeline (billing exports → warehouse → dashboards), owns tagging and allocation standards, runs optimization programs with engineering teams, manages commitments with finance, forecasts, and runs the monthly review. Knowledge required: cloud billing models (on-demand, reserved/savings plans, spot, serverless), each provider's cost tools (AWS Cost Explorer and Data Exports — the successor to the classic Cost and Usage Report, with a FOCUS-format export; Azure Cost Management exports; GCP Billing export to BigQuery), Kubernetes cost allocation (OpenCost/Kubecost), SQL, basic scripting, the FOCUS billing-data specification (version 1.3, December 2025, added allocation columns for splitting shared resources such as Kubernetes nodes and database instances, plus a contract-commitment dataset), unit-economics modeling, and enough architecture to suggest changes. Interview focus: "spend doubled last month — walk me through finding why", commitment strategy, and persuading teams without authority.

Walk the "spend doubled" case with a method, not a guess. (1) *Confirm the shape*: daily spend by service for 60 days — a step change on one day points to a deployment or a left-running resource; a ramp points to growth or a slow leak; a monthly spike points to a billing event (commitment purchase, support tier, data egress). (2) *Decompose*: service → usage type → account/project → tag; the top three line items usually explain 80% of the delta. (3) *Separate rate from usage*: did the price change (expired commitment, instance family change, region) or did the quantity (hours, GB, tokens)? (4) *Correlate with changes*: deployments, IaC applies, new accounts, quota increases, a prompt change that doubled context length — the change log is the most underused FinOps tool. (5) *Fix in order of reversibility*: turn off the idle thing today, add the cap and the alert this week, change the architecture this quarter. (6) *Close the loop*: a unit-cost chart that shows the fix, and a policy that prevents recurrence. Spoken with the example in 47.7 it takes ninety seconds and sounds like someone who has done it.

Chapters 47a–47g follow the role as a cloud FinOps analyst track: the role and finance vocabulary (47a), billing data and native tools (47b), forecasting and variance (47c), allocation, tagging and anomalies (47d), commitments and realized savings (47e), executive reporting and the interview (47f), and a hands-on lab (47g).

## 47.3 The data

- **Billing exports** at line-item granularity (AWS Data Exports / CUR 2.0, Azure Cost Management exports, GCP billing export to BigQuery) into a warehouse; normalized with the FOCUS schema for multi-cloud (all three providers now offer FOCUS-format exports, but at different versions and stages — AWS 1.2, Azure 1.0r2 with 1.2 in preview, Google's native export in preview — so a thin mapping layer is still needed; chapter 47b.6).
- **Allocation**: tags/labels (team, product, environment, cost center) enforced by policy; account/project/subscription hierarchy; shared-cost rules (networking, support, platforms) split by usage.
- **Usage telemetry**: utilization metrics (CPU/GPU/memory), Kubernetes pod requests vs usage, storage access patterns, token usage from OTel attributes, API call counts.
- **Unit economics**: cost per customer, per transaction, per 1k requests, per resolved ticket, per document, per token; the number the business recognizes.

## 47.4 The optimization catalogue

| Area | Levers |
|---|---|
| Compute | rightsizing (requests vs usage), autoscaling and scale-to-zero, scheduling non-prod off-hours, spot/preemptible for fault-tolerant work, newer instance families, ARM (Graviton, Azure Cobalt, Google Axion), serverless for spiky loads |
| Kubernetes | right-size requests/limits, bin-packing, cluster autoscaler/Karpenter, node pools per workload, OpenCost/Kubecost allocation, remove idle namespaces |
| Storage | lifecycle policies and tiers (S3 Intelligent-Tiering and the S3 Glacier storage classes, Azure cool/cold/archive, GCS nearline/coldline/archive), delete orphaned volumes and snapshots, compress and partition data lakes, Delta/Iceberg table maintenance |
| Data platforms | serverless warehouses with auto-stop, query cost attribution (BigQuery slots/bytes scanned, Snowflake credits, Databricks DBUs), partition pruning, caching, avoiding SELECT *, scheduled pipelines instead of always-on clusters |
| Networking | avoid cross-region/AZ egress, NAT gateway costs, private endpoints, CDN for static content |
| Databases | right-size instances, reserved capacity for steady state, read replicas only when needed, serverless options (Aurora Serverless, Cosmos autoscale) |
| Observability | log sampling and retention, metric cardinality control, trace sampling |
| AI/LLM | prompt caching, routing, context trimming, batch, distillation, self-host at proven volume, GPU utilization and scale-to-zero, provisioned throughput only for steady base load (chapter 31) |
| Rates | savings plans/reserved instances/committed-use discounts sized to the steady base (70–80% coverage), enterprise agreements, marketplace private offers |
| Architecture | consolidate duplicate services, event-driven instead of polling, async batch processing, edge caching |

Typical magnitudes let you rank the levers in an interview. Figures are typical ranges and list prices in a representative US region as of 2025–2026; quote them as orders of magnitude and verify before a real decision.

| Lever | Typical effect | Effort and risk | What to say |
|---|---|---|---|
| Rightsizing over-provisioned compute | 10–30% of the affected bill | low effort, low risk if based on 2–4 weeks of p95 utilization | "Requests were 4× usage; I cut them with a 30% headroom and watched throttling for a week." |
| Scheduling non-prod off-hours | up to ~65% of non-prod compute hours (12 h × 5 days of 168) | low; needs an override for on-call testing | "Dev and staging sleep nights and weekends; one tag opts out." |
| Spot/preemptible for fault-tolerant jobs | 60–90% discount | medium; needs checkpoints and a fallback pool | "Training and batch scoring on spot with checkpoints; serving never." |
| ARM instance families | ~20–40% better price-performance for many workloads | medium; rebuild images, test native dependencies | "We moved the Python services; the one with a legacy native lib stayed on x86." |
| Commitments (savings plans, reservations, CUDs) | list discounts up to roughly 70% for three-year terms; a realistic blended saving on a mixed estate is 25–40% | finance decision; risk of paying for idle commitment | "Cover 70–80% of the 90-day base, ladder terms, review monthly." |
| Storage tiering | cold tiers are 70–95% cheaper per GB, with retrieval fees and minimum storage durations of 30–180 days on most cold tiers and 365 days on Google Archive (a lifecycle class change on Google Cloud keeps the object's age; chapter 47e) | low; needs access-pattern data | "Lifecycle rules after 30 and 90 days; archive after a year; never tier data a pipeline rereads nightly." |
| Networking | NAT gateway ~\$0.045/hour plus ~\$0.045/GB processed; cross-AZ traffic ~\$0.01/GB each way; internet egress ~\$0.09/GB | low; often a surprise line item | "Model traffic went through NAT; a private endpoint cut \$4k/month." |
| Query cost in warehouses | BigQuery on-demand ~\$6.25/TB scanned; partitioning and clustering cut scans 10× or more | low to medium | "One unpartitioned table behind 40% of scans." |
| Observability | log ingestion ~\$0.50/GB (CloudWatch) and similar elsewhere; sampling and retention cut 50–80% | low | "Debug logs at 10% sampling, 14-day retention in hot storage." |
| LLM prompt caching | cached input tokens at ~10% of the base input price (Anthropic) | low | "A 6k-token system prompt cached across 100k requests a day." |
| LLM batch processing | 50% off for asynchronous jobs with a 24-hour window | low | "Nightly classification runs through the batch endpoint." |
| LLM routing by difficulty | small-tier models are 10–20× cheaper per token than frontier-tier | medium; needs an eval to prove quality holds | "80% of tickets to the small model, 20% escalated; faithfulness unchanged on the eval set." |
| GPU utilization | on-demand H100 pricing in 2025–2026 ranged from about \$2 per GPU-hour at specialist GPU clouds to \$6–8 at hyperscalers before discounts; a serving GPU at 20% utilization costs 5× per token what it should | medium; batching, right-sized models, scale-to-zero | "Tokens per second per GPU is the metric; we doubled it with continuous batching." |

Annual industry surveys put self-reported cloud waste at roughly a quarter to a third of spend, which is why the first three rows (usage levers that require no finance decision) are where a FinOps program starts.

## 47.5 Commitments in one paragraph

Reserved instances, savings plans and committed-use discounts trade flexibility for 30–70% lower rates; buy them for the steady, proven base load (measured over 60–90 days), ladder terms (1- and 3-year), keep coverage below peak so you are not paying for idle commitments, review monthly, and treat them as a finance decision with engineering input. For AI: provisioned throughput/PTUs follow the same rule — only after utilization is measured.

Two numbers run every commitment review. *Coverage* is the share of eligible usage that a commitment pays for; *utilization* is the share of the commitment that is actually used. Target utilization at or above 95% and coverage of 70–80% on steady workloads; coverage above that is where idle commitments start. Worked example: 90 days of compute show a floor of \$60k/month and peaks of \$100k; buy commitments for \$45k (75% of the floor), ladder them as one-year for two thirds and three-year for one third so a third expires each year and the architecture can change, and re-check monthly; if a migration to ARM is planned, buy compute-family-flexible plans rather than instance-specific reservations. For AI the same arithmetic applies to provisioned throughput: an Azure PTU or a Bedrock provisioned-throughput unit is worth buying only when the tokens it can process per hour, priced at pay-as-you-go, would cost more than the hourly unit price — in practice sustained utilization above roughly 60–70% of the unit's capacity — and only for the steady base, with pay-as-you-go absorbing peaks. GPUs are a third case: capacity reservations guarantee availability (which spot and on-demand do not for the largest instances) and are priced like reservations; buy them for training campaigns with a known calendar, not for experimentation.

## 47.6 Operate: budgets, anomalies, reviews

Budgets per team and product with alerts at 50/80/100% and forecast-to-exceed; anomaly detection on daily spend by service (all three clouds offer it; add your own on unit cost); a monthly FinOps review with each team's unit-cost trend, top levers, and committed actions; policies as code (required tags, approved instance types, auto-stop) in IaC pipelines; a "cost of delay" conversation when an optimization competes with features.

Allocation is where FinOps programs stall, so know the mechanisms for Kubernetes and AI spend. *Kubernetes:* OpenCost or Kubecost price each pod at the larger of its requests and its usage, multiplied by the node's hourly price; what remains on the node is *idle cost*, and the choice of who pays it is a policy decision — charge idle to the cluster owner and teams have no incentive to right-size, charge it proportionally to tenants and the platform team has no incentive to bin-pack, so most programs split it and publish both numbers. Shared costs (control plane, logging, ingress) are allocated proportionally to allocated cost; FOCUS 1.3's allocation columns exist to make these splits explicit in the billing data itself. *AI spend:* three complementary mechanisms. First, the gateway issues a virtual key per team and feature (LiteLLM, Portkey, Kong and the cloud gateways all do this) and records tokens per key. Second, the provider's own allocation feature — on Bedrock an *application inference profile* per team with cost-allocation tags, which makes team spend appear directly in Cost Explorer; on Microsoft Foundry a deployment per cost center with tags; on Google Cloud a project or label per team. Third, the traces: the OpenTelemetry GenAI attributes (`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, model, feature) joined to a price table in the warehouse give cost per request, per feature and per customer, which neither the gateway nor the bill can give alone. Reconcile the three monthly; a gap above a few percent means untagged traffic or a price-table error.

## 47.7 Example use cases

- **Spend doubled.** Billing export by service and tag shows a new GPU node pool left running after a lab and a 4× increase in LLM tokens from a prompt change that doubled context; fixes: scale-to-zero schedule, prompt cache and context trim, alert on tokens per request; result: back to baseline plus 10%.
- **Pipeline cost −25% (resume use case).** Scheduled serverless jobs instead of always-on clusters, incremental processing, cheaper storage tiers, fewer redundant retrains.
- **Kubernetes allocation.** OpenCost shows three teams requesting 4× the CPU they use; rightsizing requests and enabling Karpenter cuts the cluster bill 35%.
- **Commitment plan.** 90 days of usage shows a steady 60% base; a laddered savings-plan purchase covers 70% of it; monthly review adjusts.
- **AI unit economics.** Cost per resolved ticket for the support agent falls from \$0.42 to \$0.13 after routing and caching; the business approves expanding to two more queues.
- **Data warehouse.** Attributing BigQuery bytes scanned to dashboards reveals one unpartitioned table behind 40% of cost; partitioning and a materialized view fix it.
- **Denial-of-wallet.** Token spend on the public-facing assistant triples in one afternoon; traces show a handful of sessions with 40-turn loops and 100k-token contexts — a prompt-injection loop, not growth. Fixes: per-session token and turn caps, per-user daily budgets at the gateway, an anomaly alert on tokens per session, and the incident goes to the security review (chapter 53).
- **The NAT gateway bill.** Model and embedding traffic from private subnets runs through a NAT gateway at ~\$0.045/GB; a month of 90 TB is about \$4k of NAT processing on top of the API bill. A private endpoint for the model API and a gateway endpoint for object storage remove most of it; the request path gets faster as well.
- **GPU reservation decision.** A team wants eight H100s "for a quarter of experiments". Usage history shows 30% utilization on the current pool; the answer is a scheduled pool with scale-to-zero and a queue, and a reservation only for the two-week training campaign with a calendar date.
- **Log retention.** 60% of the observability bill is debug-level logs retained for a year; sampling debug logs at 10%, keeping 14 days hot and 13 months in cold archive cuts it by more than half with no loss for incidents, which rarely look back more than a week.
- **Idle environments.** 120 developer sandboxes in a lab account each run a small database and a load balancer around the clock; an auto-stop policy after 48 idle hours and an expiry tag enforced in IaC save more than the next three rightsizing projects combined.
- **Batch instead of online.** A nightly document-classification job calls the model synchronously from 50 workers and hits rate limits; moving it to the batch endpoint halves the token price, removes the retries, and finishes in the 24-hour window with one worker.
- **Cross-region model calls.** The model is only available in another region, so every request pays inter-region egress and 60 ms; the fix is the provider's cross-region inference profile within the same geography (which keeps data residency) and a check that the region quota exists before launch.

## 47.8 How an AI engineer participates

Tag everything, emit token and latency attributes in traces, know the cost per request of your feature, bring the eval set to every cost conversation, and propose levers with measured impact. The engineer who can say "this change saves \$30k a month and the eval set did not move" gets both the budget and the promotion.

**Interview line:** *"FinOps is inform, optimize, operate: allocate every dollar to a team and a unit of value, pull the usage and rate levers in order of impact, and run the budgets and reviews so it sticks. For AI the unit is cost per task, the levers are caching, routing, context and utilization, and quality is the gate."*
