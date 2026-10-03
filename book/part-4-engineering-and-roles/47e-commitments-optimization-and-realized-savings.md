# 47e. Commitments, usage optimization and realized savings

> **What you need to be able to say:** what each cloud sells as a commitment in 2026 and what changed in 2025–2026; the commitment arithmetic (coverage, utilization, waste, break-even utilization of 1 − discount, sizing from a usage floor, laddering) and the competing effective-savings-rate definitions; how to rightsize with percentiles and headroom, schedule non-production, tier storage without paying minimum-duration and retrieval traps, find idle resources, cut data transfer and use licenses well; and how to quantify, prioritize, implement and then prove savings: counterfactual baselines, decay, shared commitments, overlapping changes, and probability-weighted savings in the forecast. Chapter 47.4–47.5 has the optimization catalog and typical magnitudes, chapter 31 AI token costs, 47a.4 the cost metrics, 47d allocation and anomalies, and 47g runs the commitment, savings and forecast methods on synthetic data.

Prices are US list prices where marked as published and illustrative otherwise; check the provider's pricing page before a number goes into a business case. "The lab" is the fictional business unit of chapter 47g, with \$1.23M of amortized cost in September 2026; it is separate from, and smaller than, the running example of 47a and 47c.

## 47e.1 Commitments by cloud, as of 2026

All three clouds trade a promise to pay for a lower rate, in two families. *Spend-based* commitments promise dollars per hour of eligible usage (AWS Savings Plans, Azure savings plans, Google spend-based CUDs and Flexible Savings Plans). *Resource-based* commitments promise a quantity of a specific resource (AWS Reserved Instances, Azure reservations, Google resource-based CUDs). The broad spend-based plans follow workloads across families and regions; resource-based commitments and EC2 Instance Savings Plans are tied to a family or region and give deeper discounts in exchange. All are use-it-or-lose-it by the hour.

### AWS

- **Savings Plans.** Compute Savings Plans (up to 66% off on-demand, any EC2 family, size, region or OS, plus Fargate and Lambda), EC2 Instance Savings Plans (up to 72%, one family in one region) and SageMaker AI Savings Plans (up to 64%); one or three years; all, partial or no upfront. Reserved Instances apply first, then EC2 Instance Savings Plans, then Compute Savings Plans; within a plan, usage with the highest savings percentage is covered first, and at equal percentages the usage with the lowest Savings Plans rate. Each hour's commitment can be used only in that hour.
- **Database Savings Plans** (2 December 2025): one year, no upfront only; up to 35% off serverless usage, 20% off provisioned instances, 18% off DynamoDB and Keyspaces on-demand throughput and 12% off their provisioned capacity; Aurora, RDS, DynamoDB, ElastiCache, DocumentDB, Neptune, Keyspaces, Timestream and DMS, plus OpenSearch and Neptune Analytics since March 2026. They cannot be combined with RDS Reserved Instances or DynamoDB reserved capacity on the same workload, so a move off reservations needs a plan for the overlap.
- **Reserved Instances.** Standard RIs give the larger discount and can be sold on the RI Marketplace (EC2 Standard only, held at least 30 days, at least a month left, a 12% fee, a lifetime limit of \$50,000 or 5,000 RIs per account); Convertible RIs can be exchanged. Reservations also exist for RDS, ElastiCache, OpenSearch, Redshift, MemoryDB and DynamoDB, and since February 2026 three-year reservations for Redshift Serverless.
- **Returns.** A Savings Plan can be returned if its hourly commitment is \$100 or less, it was bought in the last seven days and in the same calendar month (UTC), and it is active; ten returns per calendar year per management account. A safety net for typos, not a sizing strategy.
- **Sharing.** Benefits apply to the owner account first and then across the organization unless sharing is turned off. Group sharing (19 November 2025) uses Cost Categories to define *prioritized* or *restricted* groups (47d.6).
- **Tools and negotiated discounts.** The Savings Plans Purchase Analyzer models recommended, custom or target-coverage purchases on lookbacks within the last 60 days; Cost Optimization Hub counts one action per resource and de-duplicates commitment recommendations. An Enterprise Discount Program or Private Pricing Agreement stacks with commitments and appears as negative discount rows or in the CUR 2.0 discount columns, flowing into the `net_` columns (47a.4), which matters for the savings-rate definitions below.

### Azure

- **Reservations.** One or three years, upfront or monthly for the same total, up to 72% off pay-as-you-go, for VMs, databases (SQL Database and Managed Instance, Cosmos DB, MySQL, PostgreSQL), storage, analytics services and more. The discount applies hourly; an hour without matching usage is lost. Scope is a resource group, a subscription, a management group or shared across the billing context, and can be changed at any time without changing the term. VM reservations "optimized for instance size flexibility" cover other sizes in the same flexibility group.
- **The exchange change.** Reservations bought on or after 1 February 2027 for services covered by savings plans (VMs, App Service, SQL Database and others) cannot be exchanged; earlier ones keep one final exchange. Trade-in to a savings plan is unchanged, refunds are capped at USD 50,000 per rolling 12 months, and there is currently no early-termination fee. From February 2027, buy a VM reservation only for a footprint that will not change family or region, and use a savings plan for the rest.
- **Savings plan for compute.** An hourly commitment for one or three years across VMs, App Service, Functions Premium, Container Instances, Dedicated Host, Container Apps and Spring Apps Enterprise. It applies after reservations, to the usage with the highest discount first, three-year plans before one-year plans; unused commitment is lost each hour, and a plan cannot be canceled.
- **Savings plan for databases** (around March 2026): SQL Database (including Hyperscale and serverless), SQL Managed Instance, PostgreSQL, MySQL, Cosmos DB, DocumentDB, Database Migration Service and SQL Server licenses on VMs and Arc, up to 35% off. The pricing FAQ describes a one-year term and Learn mentions one or three; check before you model it.
- **MACC.** A consumption commitment is a contract to spend, not a discount: optimization reduces drawdown, so check the position before cutting committed spend (47a.3).

### Google Cloud

- **Resource-based CUDs.** Compute Engine vCPUs, memory, GPUs, Local SSD, sole-tenant nodes or OS licenses in a region for one or three years: up to 57% off, 70% for memory-optimized machines. Since 16 June 2026 the default scope is the billing account, so a commitment applies across the projects on that billing account.
- **Sustained use discounts.** Up to 30% for N1, N2, N2D, C2, M1 and M2 vCPUs and memory that run more than a quarter of the month, rising with use; not on usage covered by CUDs, and only for self-serve (online) billing accounts. Check before modeling them for an invoiced account.
- **Compute Flexible CUDs** (spend-based) cover Compute Engine, GKE Standard and Autopilot, and Cloud Run; the expanded coverage applied to all accounts from February 2026, G2 and G4 GPUs were added in August 2026, and separate Cloud Run and GKE Autopilot CUDs are no longer sold. Spend-based CUDs also exist for AlloyDB, BigQuery, Bigtable, Cloud SQL, Dataflow, Firestore, Memorystore, Spanner and others. Commitments cannot be canceled.
- **The new spend-based data model.** The legacy model expressed the commitment in on-demand dollars and showed the discount as a fee plus a credit. The new one shows it as a lower price on the usage (`consumption_model` columns), with `FEE_UTILIZATION_OFFSET` replacing `COMMITTED_USAGE_DISCOUNT_DOLLAR_BASE`, and the hourly commitment is entered in discounted dollars. New billing accounts have used it since 15 July 2025 and migration of existing ones began on 21 January 2026. Dashboards built on the credit columns stop showing the discount after migration (47b.8), and a \$100-an-hour commitment means different coverage under the two models, so never compare them directly.
- **Flexible Savings Plans** (26 August 2026): a spend commitment across Google's generative AI products, 10% off for one year and 20% for three. Size it from the floor of AI spend, which is younger and more volatile than compute.

### The three side by side

| | AWS | Azure | Google Cloud |
|---|---|---|---|
| Spend-based, broad | Compute Savings Plans | Savings plan for compute | Compute Flexible CUDs |
| Spend-based, databases | Database Savings Plans (1 year, no upfront) | Savings plan for databases | Spend-based CUDs per database service |
| Commitments for AI | SageMaker AI Savings Plans | Reservations for provisioned throughput units, one month or one year, bought after the deployments exist (chapter 31) | Flexible Savings Plans for generative AI |
| Resource-based | Reserved Instances and reservations | Reservations | Resource-based CUDs |
| Undo options | Returns within 7 days for small plans; Convertible exchanges; Standard RI resale | Exchanges (narrowed from February 2027); refunds up to \$50,000 per rolling 12 months; trade-in to savings plans | None |
| Discount without commitment | None | None | Sustained use discounts (eligible accounts and series) |
| Where it shows in the data | Amortized columns on covered usage; `RIFee` and `SavingsPlanRecurringFee` rows; FOCUS `CommitmentDiscount*` | Amortized cost dataset; FOCUS export | Credits (resource-based, legacy spend model) or lower prices (new spend model); CUD metadata export (preview) |

## 47e.2 Commitment math

### Coverage, utilization, waste and break-even

- **Coverage** = covered eligible usage ÷ total eligible usage, both at on-demand-equivalent dollars (or hours for resource-based commitments): how much of what we could cover is covered. The FOCUS coverage use case adds a detail that trips up SQL: unused-commitment rows carry a commitment ID, so filter them out of both numerator and denominator.
- **Utilization** = used commitment ÷ total commitment: are we using what we bought.
- **Commitment discount waste %** = unused commitment cost ÷ total commitment cost (= 1 − utilization).
- **Break-even utilization** = 1 − discount. A commitment costing C buys usage worth C ÷ (1 − d) at on-demand rates; at utilization u it delivers u × C ÷ (1 − d), which equals its cost when u = 1 − d. At a 30% discount the break-even is 70%; at 40%, 60%; at 72%, 28%. Deep three-year discounts tolerate a lot of waste; shallow one-year discounts very little.
- **Where to stop.** The same argument at the margin: the next dollar of hourly commitment pays only if eligible usage exceeds that level in at least (1 − d) of the hours. The expected-value optimum is therefore the level usage exceeds 70% of the time at a 30% discount: the 30th percentile of hourly usage, not the minimum and not the average.
- The FinOps Foundation's Rate Optimization capability suggests an upper waterline around 80% utilization for resource-based commitments on steady-state usage. Spend-based plans follow usage across families and regions, so a target of 95% or more is reasonable for them.

### Worked sizing example

Sixty days of hourly data, after removing a workload being decommissioned, show eligible usage at on-demand rates of \$1,000 an hour in business hours (60 hours a week), \$700 on weekday nights (60 hours) and \$600 at weekends (48 hours): \$130,800 a week on demand. A one-year spend-based plan gives 30% off (illustrative). Commitments are in discounted dollars per hour:

| Option | Hourly commitment | Covers (on-demand equivalent) | Utilization | Weekly cost | Weekly savings | Effective savings rate |
|---|---|---|---|---|---|---|
| A: the floor | \$420 | \$600 an hour | 100.0% | \$100,560 | \$30,240 | 23.1% |
| B: the 30th percentile | \$490 | \$700 an hour | 95.9% | \$100,320 | \$30,480 | 23.3% |
| C: the business-hours peak | \$700 | \$1,000 an hour | 77.9% | \$117,600 | \$13,200 | 10.1% |

The layer from \$600 to \$700 is used in 120 of 168 hours (71.4%, just above the 70% break-even) and adds \$240 a week; the layer from \$700 to \$1,000 is used in 60 hours (35.7%) and loses \$17,280 a week. B is the expected-value optimum, but only barely. Finance will ask about the downside:

| Usage over the term | A: floor (\$420) | B: optimum (\$490) | C: peak (\$700) |
|---|---|---|---|
| 10% lower | \$27,360 a week (utilization 97.1%) | \$23,400 (89.9%) | \$120 (70.1%) |
| As planned | \$30,240 (100%) | \$30,480 (95.9%) | \$13,200 (77.9%) |
| 10% higher | \$30,240 (100%) | \$33,360 (98.4%) | \$20,280 (82.1%) |

C at 10% lower usage runs at 70.1% utilization and saves \$120 a week: the break-even rule in action. B gains \$3,120 a week over A if usage grows and loses \$3,960 if it falls. When the two are this close, buy the floor on the longer term and the next layer as a one-year tranche or later, when growth is confirmed. That is laddering.

### The same method in the lab

The lab sizes the renewal of its \$220-an-hour Compute Savings Plan, which expires on 31 January 2027, from projected daily eligible usage without the data platform that is switched off on 1 November:

| Option | Hourly | Utilization | Coverage | Gross savings a year | Unused a year | Net savings a year |
|---|---|---|---|---|---|---|
| Floor: P5 of daily usage | \$195 | 100.0% | 65.9% | \$731,886 | \$466 | \$731,420 |
| Recommended: smallest commitment within 5% of the best net | \$210 | 99.2% | 70.4% | \$782,263 | \$14,319 | \$767,944 |
| Expected-value optimum | \$305 | 91.0% | 93.8% | \$1,041,706 | \$241,153 | \$800,554 |
| Renew as is | \$220 | 98.2% | 73.1% | \$811,233 | \$34,324 | \$776,909 |
| Oversized: 120% of the optimum | \$365 | 80.9% | 99.8% | \$1,108,252 | \$611,478 | \$496,774 |

The net-savings curve is almost flat between \$210 and \$305 because weekdays are 71.4% of days, a hair above the 70% break-even: the optimum buys \$95 an hour of extra exposure for \$32,610 a year. So the lab recommends the plateau's lower edge, \$210. Two caveats belong in the recommendation: the lab works on daily data, and hourly data (with night-time troughs) gives a lower floor and optimum; and the projection assumes the switch-off happens on 1 November. The current plan shows the switch-off risk too: from 1 November to 31 January its utilization falls to 96.5%, about \$5,656 a month unused.

### Laddering, term mix and convertibility

Buy in monthly or quarterly tranches, each sized to the then-current floor, so commitments expire on different dates; one large purchase that expires on one day creates a cliff. Use three-year terms for the floor you are sure of, one year for the next layer, and nothing for the top layer or for workloads with a decommission date. Prefer the spend-based form when a family, ARM or region move is likely within the term, and do not count on the undo options (47e.1). Before every purchase, remove what is leaving, add committed growth, check the consumption-commitment position, and put Finance's approval in the same document as the sizing.

### Effective savings rate: three definitions

| Definition | Formula | Includes negotiated discounts? | Use it for |
|---|---|---|---|
| FinOps Foundation, option 1 | (commitment discount savings − cost to achieve them, such as unused commitment) ÷ on-demand-equivalent spend; approximately utilization × coverage × discount | No | Explaining the commitment program |
| FOCUS | (ContractedCost − EffectiveCost) ÷ ContractedCost | No, by construction: ContractedCost already includes them | Cross-cloud reporting from FOCUS data |
| FinOps Foundation, option 2 | 1 − (actual spend with discounts ÷ equivalent spend at on-demand rates) | Yes, if the on-demand equivalent is at public prices | The total discount from all instruments |

Vendors pick their own variant, so quote a benchmark only with its definition and population. ProsperOps' 2025 report on AWS compute counts Savings Plan and Reserved Instance savings off the on-demand rate for EC2, Lambda and Fargate (close to option 1); its 2024 distribution had a median of 15% (0% a year earlier), a 75th percentile of 30% and a 98th of 47%, with medians of 0% under \$500,000 of annual compute spend, 23% from \$500,000 to \$10 million and 38% above.

The lab's September usage rows (including unused commitment) show how far the definitions diverge:

| Provider | ESR (FOCUS) | Option 1, on-demand equivalent at list | Option 2 at list |
|---|---|---|---|
| AWS | 9.6% | 9.0% | 15.0% |
| Microsoft | 0.0% (the reservation lapsed) | 0.0% | 0.0% |
| Google Cloud | 1.9% | 1.9% | 5.9% |
| All | 5.7% | 5.4% | 9.6% |

On the AWS Savings Plan pool alone (eligible EC2 plus unused commitment) the FOCUS ESR is 16.9%, which matches the approximation: utilization 100% × coverage 56.2% × discount 30% = 16.9%. Two notes on the FOCUS formula: the FOCUS use case computes it over all rows in the period, and Microsoft's FOCUS conversion fills ContractedCost on commitment purchase rows (unit price × quantity) while their EffectiveCost is zero, so filter to usage charges, or purchase and credit rows distort the rate (16.8% instead of 5.7% in the lab, 47f.12).

## 47e.3 Rightsizing

Rightsizing compounds: a smaller instance costs less on demand, needs less commitment, and often fewer per-core licenses. It is also where most savings estimates are wrong, because they use averages and ignore memory.

### The method

1. **Lookback.** At least 14 days; 32 to include a month-end cycle; 90 for quarterly batch. AWS Compute Optimizer offers 14 days (default), 32 days, or 93 days with paid enhanced infrastructure metrics, and uses the maximum utilization within each five-minute interval. Azure Advisor's default is 7 days, configurable to 90; seven days is too short for anything with a monthly cycle.
2. **Percentiles, not averages.** P95 for tolerant workloads, P99 or P99.5 for latency-sensitive ones. Compute Optimizer offers CPU thresholds of P90, P95 or P99.5 (default P99.5), CPU headroom of 0%, 20% or 30% (default 20%) and memory headroom of 10%, 20% or 30% (default 20%), with presets from "maximum savings" (P90, 0%, 10%) to "maximum performance" (P99.5, 30%, 30%).
3. **Memory, always.** CPU-only rightsizing is how databases, JVMs and caches get hurt. Compute Optimizer analyzes EC2 memory only with the CloudWatch agent or external metrics from Datadog, Dynatrace, Instana or New Relic, so put the agent in the base image first.
4. **Headroom.** Required capacity = current size × P99 utilization × (1 + headroom).
5. **Shape, not just size.** Low CPU with high memory calls for a memory-optimized family, not a smaller general-purpose one. Consider newer generations and ARM: AWS states Graviton-based instances cost up to 20% less than comparable x86 instances; Azure Cobalt and Google Axion are the equivalents. ARM needs rebuilt images and tested native dependencies.
6. **Licenses.** Count cores before and after: per-core licenses (SQL Server, some Oracle and middleware) can be worth more than the compute. Azure Hybrid Benefit for Windows Server needs at least 8 core licenses per VM, so shrinking below 8 vCPUs does not reduce the licenses consumed (47e.8).
7. **Verify.** Change in a window, watch latency, throttling, errors and out-of-memory events for one to two weeks, and keep the rollback path open.

### Worked example

A fleet of 120 general-purpose instances with 8 vCPUs and 32 GB each costs an illustrative \$0.384 an hour on demand: 120 × \$0.384 × 730 = \$33,638 a month. Thirty-two days of metrics show P99 CPU at 22% and P99 memory at 41%. With 20% headroom: CPU needed = 8 × 0.22 × 1.2 = 2.1 vCPUs; memory = 32 GB × 0.41 × 1.2 = 15.7 GB. The 4-vCPU, 16 GB size fits (P99 memory 13.1 GB, 82% of 16 GB) at half the price: \$16,819 a month, an on-demand saving of \$16,819.

Now the commitment. A Compute Savings Plan of \$14,000 a month (30% off) covers \$20,000 of this fleet's on-demand-equivalent usage. Before: \$14,000 + (\$33,638 − \$20,000) on demand = \$27,638. After: usage of \$16,819 is below the \$20,000 the plan covers, so the plan is 84% used (\$16,819 × 0.7 = \$11,773 of \$14,000), \$2,227 a month is wasted, and the cost is \$14,000. The saving is \$13,638 a month, 81% of the on-demand estimate.

If other accounts have uncovered eligible usage, the shared plan moves there and the full \$16,819 is realized; if not, time the rightsizing with the next commitment purchase. Always restate a recommendation at your effective rates: Azure Advisor computes savings at retail rates and ignores existing reservations and savings plans, while Compute Optimizer's savings estimation mode prices savings after Savings Plan and Reserved Instance discounts by default for management accounts and organizations enrolled in Cost Optimization Hub, and at on-demand rates otherwise.

**Kubernetes, databases and AI.** In Kubernetes, rightsize requests, not nodes: pods are charged at the larger of request and usage (47d.7), so set requests near P95 usage plus headroom and let the cluster autoscaler or Karpenter remove the nodes no longer needed. For databases, check CPU, memory, IOPS and connections, and consider serverless tiers for spiky loads (Compute Optimizer covers RDS and Aurora; Google's recommender, Cloud SQL). For AI serving, the levers are the model and the utilization of provisioned capacity (chapter 31).

## 47e.4 Scheduling non-production

An environment that runs 12 hours on weekdays runs 60 of the week's 168 hours: 64% fewer. Real programs realize less, because of exceptions, shared environments someone always needs, and resources that cannot stop.

- **Scope.** Development, test and staging compute; non-production databases that can stop; non-production node pools scaled to zero; notebook and workstation fleets.
- **Mechanism.** A schedule by tag (`schedule=office-hours`), applied by a scheduler or IaC, with an opt-out tag that must carry an expiry date and a reason. An opt-out without an expiry is how a schedule decays.
- **Exceptions.** On-call testing, release weekends and load tests get time-boxed opt-outs on the planned-change calendar (47d.14).
- **Commitments.** Scheduling removes eligible hours; if commitments were sized on 24-hour usage, night and weekend hours become waste unless production absorbs the plan. Re-run the floor after scheduling.
- **Measure** weekly: hours off as a share of hours possible, opt-outs by age, realized against projected (47e.12).

The lab's INIT-02 is the realistic version. The business case projected \$40,000 a month. Partial adoption (about 20% fewer weekday hours and 65% fewer weekend hours) delivered \$33,635 in May and \$32,229 in June, 84% and 81% of the projection. In July, part of the AWS fleet was opted out during a release crunch and never re-enrolled, and the saving fell to about \$20,000 a month. The anomaly detector never fired; the savings tracker did (47e.12), and restoring the schedules is the second-ranked item in the pipeline (47e.10).

## 47e.5 Storage tiering

Colder classes cost less per GB stored and more per GB read, and most bill a minimum storage duration and sometimes a minimum object size. Tiering saves money on data that is old, large, rarely read and kept long enough to clear the minimums; it loses money on small objects, data read back in bulk and data deleted early.

| Class | Minimum storage duration | Minimum billable size | Retrieval charge | Access |
|---|---|---|---|---|
| S3 Standard | none | none | none | milliseconds |
| S3 Standard-IA, One Zone-IA | 30 days | 128 KB | per GB | milliseconds |
| S3 Glacier Instant Retrieval | 90 days | 128 KB | per GB | milliseconds |
| S3 Glacier Flexible Retrieval | 90 days | 40 KB of metadata per object (32 KB at the Glacier rate, 8 KB at Standard) | per GB | minutes to hours, after a restore |
| S3 Glacier Deep Archive | 180 days | 40 KB of metadata per object, as above | per GB | hours, after a restore |
| S3 Intelligent-Tiering | none | objects under 128 KB are not monitored and stay in Frequent Access | none | milliseconds in the automatic tiers |
| Azure Blob hot / cool / cold | none / 30 days / 90 days (general-purpose v2) | | none / per GB / per GB | online |
| Azure Blob archive | 180 days | | per GB, plus rehydration | offline; rehydration up to 15 hours |
| Google Standard / Nearline / Coldline / Archive | none / 30 / 90 / 365 days | | none / \$0.01 / \$0.02 / \$0.05 per GB (us-central1) | online, all four |

**Early deletion, and when the clock starts.** All three charge as if the data had stayed for the minimum. On AWS the minimum starts when the lifecycle rule moves the object; on Azure it starts at the tier change (a blob moved to cool and deleted after 21 days pays nine more days of cool, one moved to archive and deleted after 45 days pays 135 more). On Google Cloud, a class change made by Object Lifecycle Management keeps the object's age: the time spent in the earlier class counts toward the new class's minimum, and the lifecycle change itself incurs no early-deletion charge. Changing class by rewriting the object does incur it.

### The automatic options

- **S3 Intelligent-Tiering** moves objects not accessed for 30 consecutive days to an infrequent tier (up to 40% cheaper) and after 90 days to archive instant access (up to 68%), with optional archive and deep archive tiers (up to 95%, restore needed). No retrieval charges; a small monthly monitoring charge per object, which is why objects under 128 KB are left out.
- **Azure Blob smart tier** (generally available in public regions with zone-redundant storage) moves data from hot to cool after 30 days without access and to cold after 90, and back to hot on access, with no early-deletion or retrieval fees and a monitoring charge per 10,000 objects larger than 128 KiB. It needs general-purpose v2 accounts with ZRS, GZRS or RA-GZRS and block blobs.
- **Google Autoclass** moves objects not accessed for 30 days to Nearline, 90 days to Coldline and, if Archive is the terminal class, 365 days to Archive; a read moves an object back to Standard. No retrieval or early-deletion fees except in the enablement charge; a management fee of \$0.0025 per 1,000 objects a month; objects under 128 KiB stay in Standard.

Use the automatic options when access patterns are unknown or mixed, and lifecycle rules when they are known and objects are large.

### Worked example (Google Cloud, us-central1 list prices)

500,000 GB of exports and logs sit in Standard at \$0.020 per GB-month: \$10,000 a month, kept for a year. 50,000 GB are under 30 days old, 100,000 GB are 30 to 90 days old and 350,000 GB are 90 to 365 days old. Analysts read about 5% of the 30-to-90-day data and 2% of the older data each month. Lifecycle rules move data to Nearline at 30 days and Coldline at 90:

| | GB | Price per GB-month | Monthly cost |
|---|---|---|---|
| Standard (under 30 days) | 50,000 | \$0.020 | \$1,000 |
| Nearline (30 to 90 days) | 100,000 | \$0.010 | \$1,000 |
| Coldline (90 to 365 days) | 350,000 | \$0.004 | \$1,400 |
| Retrieval: 5,000 GB from Nearline and 7,000 GB from Coldline | | \$0.01 and \$0.02 per GB | \$190 |
| **Total** | | | **\$3,590** |

The saving is \$6,410 a month (64%), before per-object operation charges, which matter when objects are small and numerous. Should data go on to Archive (\$0.0012 per GB-month) at day 180? The 235,000 GB aged 180 to 365 days would cost about \$660 a month less to store and about \$140 more to read (2% of it at \$0.05 instead of \$0.02 per GB): about \$520 a month better. Because the lifecycle move keeps the object's age, data deleted at 365 days meets Archive's 365-day minimum although it spent only 185 days there. The test for any colder class is the same: the storage price difference per GB-month must exceed the retrieval price difference × the share read each month. Here \$0.0028 against \$0.03 × 2% = \$0.0006, so Archive pays until about 9% of the data is read back each month.

### Traps

- **Small objects.** In S3 Standard-IA, One Zone-IA and Glacier Instant Retrieval a 16 KB object is billed as 128 KB. If the infrequent-access price is about 55% of Standard (illustrative), that object costs 8 × 0.55 = 4.4 times more after tiering. Measure the object-size distribution first; compact small files or leave them in Standard or Intelligent-Tiering.
- **Bulk reads.** A monthly job that rereads a whole "cold" dataset turns retrieval fees into the main cost.
- **Lag.** Access-based tiering starts saving only after the 30-day no-access window: the lab's INIT-03 (S3 Intelligent-Tiering for payments log data, from 1 February 2026) realized nothing in February, part of the projection in March and the full rate from April.
- **Versions and replicas.** Lifecycle rules must cover noncurrent versions and replicated copies, or those keep paying Standard rates.
- **Month length.** Storage is billed per GB-month, so the same data costs 1/28 of the monthly price per day in February and 1/31 in January: 11% more per day. Put storage on a constant-month basis before comparing daily rates, fitting a trend or building a counterfactual (47e.12).

## 47e.6 Idle and underutilized resources

Idle resources are the cheapest savings to find and the easiest to argue about, because "idle" needs a definition and a grace period.

| Resource | Idle signal | Action | Notes |
|---|---|---|---|
| Unattached block volumes | Unattached more than 7 days | Snapshot, then delete after the grace period | Google's recommender flags idle disks |
| Old snapshots and images | Older than the retention policy, unreferenced | Delete or archive | Google flags idle images |
| Idle virtual machines | Azure Advisor's shutdown rule: P95 CPU under 3% and network under 2% | Stop, then delete if unclaimed | Compute Optimizer's idle coverage expanded in June 2026; Google has an idle-VM recommender |
| Idle load balancers | No healthy targets or no requests | Delete | Usually left by deleted services |
| Public IPv4 addresses | Not attached, or attached to something idle | Release | AWS charges \$0.005 per IP-hour, in use or idle: \$43.80 a year each |
| NAT gateways | Little traffic, especially in development VPCs | Remove, share, or use endpoints | \$0.045 per gateway-hour (about \$32.85 a month) plus \$0.045 per GB in us-east-1; regional NAT gateways are charged per Availability Zone |
| Idle databases | No connections for 7+ days | Stop, or snapshot and delete | Google's recommender covers idle Cloud SQL |
| Unattended projects | Low activity, no owner | Archive and shut down | Google's unattended-project recommender |
| Over-requested pods, idle nodes | Requests far above usage | Lower requests; let the autoscaler remove nodes | 47d.7 |
| Idle provisioned AI capacity | Throughput units or GPUs below target utilization | Reduce units; keep base load only | Chapter 31 |
| Expired sandboxes | `expiry` tag in the past | Notify, then delete | 47d.2 |

**Safe deletion.** Tag the candidate with a deletion date and notify the owner from the account map; wait 14 days (7 for sandboxes); snapshot what holds data; delete; keep the snapshot 30 more days and then delete it too, or the saving partly reappears as snapshot storage.

**Sizing it.** The lab's network account holds 400 public IPv4 addresses (9,600 IP-hours a day, \$48 a day, about \$1,460 a month); with old snapshots this is pipeline item OPP-05 at \$1,500 a month. Batch small items into one cleanup ticket per owner per quarter.

## 47e.7 Data transfer

Data transfer hides inside other lines (NAT, load balancers, inter-zone traffic) and grows with architecture rather than traffic, so it needs its own review.

- **NAT processing.** Traffic from private subnets to AWS services through a NAT gateway pays \$0.045 per GB processed in us-east-1 on top of any transfer charge. Gateway endpoints for S3 and DynamoDB have no additional charge, so S3-heavy workloads should never reach S3 through NAT: 40,000 GB a month costs \$1,800 in NAT processing alone. Interface endpoints are billed per hour per Availability Zone plus \$0.01 per GB at the first tier.
- **Cross-zone and cross-region traffic.** Chatty services spread across zones pay in both directions (47.4 gives magnitudes); keep tightly coupled services and their caches in one zone where resilience allows, and replicate across regions only what the recovery objective needs.
- **Internet egress.** AWS gives 100 GB a month out to the internet free across services and regions; above that, a CDN usually lowers cost and latency for static content.
- **Allocation.** Tag the resources that generate traffic and use flow logs when the shared network bill justifies usage-driven allocation (47d.6).

Review the top data-transfer usage types by account monthly; the lab's NAT spike (47d.16) is the same problem arriving as an anomaly.

## 47e.8 License optimization

Licenses are a separate bill inside the compute bill, and licensing terms are contracts. The analyst finds and quantifies the opportunities; the decision belongs to whoever owns licensing (IT asset management, procurement or a licensing specialist). Say so in any interview answer or business case.

**Azure Hybrid Benefit for Windows Server.** Windows Server core licenses with active Software Assurance or qualifying subscription licenses can be applied to Azure VMs, which removes the Windows license charge from the VM. Each VM needs at least 8 core licenses, even a 4-core VM; larger VMs need as many as their cores, and a processor license counts as 16 core licenses. It is set per VM with `licenseType` `Windows_Server`. Cost data has no native column showing whether the benefit is applied; the FinOps toolkit's hubs add one (`x_SkuLicenseStatus`). In the lab, INIT-04 applied the benefit to 70% of the CRM production VM hours and removed about \$12,400 a month of license meter cost against a projection of \$11,500.

**Azure Hybrid Benefit for SQL Server.** For Azure SQL Database (provisioned vCore only; not DTU and not serverless) and SQL Managed Instance, SQL Server licenses with Software Assurance convert at fixed ratios: one Enterprise core covers four General Purpose vCores or one Business Critical vCore; one Standard core covers one General Purpose vCore, and four Standard cores cover one Business Critical vCore. Microsoft quotes savings of up to 30% or more. A 16-vCore General Purpose database needs 4 Enterprise cores or 16 Standard cores. The SQL benefit can be managed centrally at billing-account or subscription scope. RHEL and SUSE have bring-your-own-subscription options on Azure.

**AWS.** Windows Server licenses can be brought to EC2 only on Dedicated Hosts, only if bought before 1 October 2019 (or added as a true-up under an agreement effective before that date), and only for versions released before that date; Software Assurance is not required. Otherwise Windows is license-included. SQL Server licenses with active Software Assurance can come to default (shared) tenancy through License Mobility. Compute Optimizer's license recommendations flag SQL Server Enterprise Edition that uses no Enterprise features (finding "Not optimized", reason `LicenseOverprovisioned`) and suggest Standard Edition, or Developer Edition outside production; they need CloudWatch Application Insights and 24 hours of metrics in the last 14 days.

**Google Cloud.** Resource-based CUDs can cover OS licenses. Bringing physical-core or physical-processor licenses with dedicated-hardware requirements means bringing your own media and running it on hardware such as sole-tenant nodes; RHEL and SLES bring-your-own-subscription and Microsoft applications under License Mobility do not need sole-tenant nodes.

**Rules of thumb.** Rightsize before you license, except where a per-VM minimum applies. An edition downgrade is an application change: the team must confirm which features it uses. Owned licenses are sunk cost, but their Software Assurance renewal is not, so time decisions to renewal dates. Keep license entitlements in a table next to the commitment inventory, with owners and renewal dates, shared with the central IT FinOps or asset management team.

## 47e.9 Quantifying savings

A saving is a claim about a world that did not happen, so it needs a method someone else can rerun, written down before the change ships.

**Baseline: the counterfactual.** The saving is what the scope would have cost without the change minus what it cost. "Last month's bill minus this month's" is not a saving: it mixes the change with growth, seasonality, price changes and month length. Four counterfactuals cover most initiatives, and the lab implements each (47e.12):

| Method | Counterfactual | Fits | Fails when |
|---|---|---|---|
| Unit cost | Pre-change cost per business unit × actual units | Usage that scales with a business driver | Cost does not grow with the driver |
| Trend | Pre-change model projected forward | Usage without a clean driver | The pre-period has seasonality or steps |
| Rate | Pre-change cost per unit of quantity × actual quantity | Price and tier changes (storage tiering, commitments) | The initiative also changes quantity |
| Ratio | Pre-change cost of A per unit of B × actual B | Licenses (license cost per VM hour) | The A–B relationship drifts |

**Run-rate, in-year and one-time.** Report three numbers and never add them. The *monthly run-rate* is the saving per month at steady state; the *annualized* figure is twelve times that, labeled as such; the *in-year* figure is what lands in this fiscal year, which is what IT Finance cares about: a \$27,000-a-month reservation bought on 15 October saves \$68,806 in calendar 2026 (17 days of October plus two full months) and \$324,000 annualized. A *one-time* saving (a refund) is reported once and never annualized.

**Reduction or avoidance.** A reduction lowers spend against the current run-rate; avoidance prevents an increase that would otherwise have happened (renewing a commitment before it lapses) and shows only against a forecast that contained the increase. The lab's new VM reservation is both: a reduction against September's on-demand run-rate and avoidance against the budget, which assumed renewal. Say which comparison you are making.

**Unit-cost normalization.** For workloads that grow, express the saving per unit (per thousand transactions, per conversation) and multiply by actual volume. A team whose cost per transaction fell 18% while transactions grew 20% saved money although its bill went up.

**Gross and net.** Net savings subtract engineering time (hours × a loaded rate agreed with Finance), double-running, one-time services, new license or tool costs, and the commitment waste the change creates (47e.3: \$16,819 gross, \$13,638 net).

**Worked example: an ARM migration business case** (illustrative). Stateless services cost \$75,000 a month at on-demand-equivalent rates. After a performance test the team expects 12% net, below AWS's "up to 20%", because two services need a larger size: \$9,000 a month from 1 December. One-time costs: two engineers for six weeks at an agreed \$100 an hour (\$48,000) and two weeks of double-running (\$3,500). First-year net: 12 × \$9,000 − \$51,500 = \$56,500; payback 5.7 months. At 50% probability until the performance test passes, the expected first-year net is \$28,250. This is the lab's OPP-04.

## 47e.10 The opportunity backlog: scoring and prioritization

Rank by expected net value per unit of effort, and use risk as a gate rather than a weight: **score** = (12-month net savings × probability) ÷ effort in engineer-weeks; medium-risk items need a test plan and a rollback, high-risk items an owner's sign-off before they enter the queue.

| Id | Opportunity | Monthly | One-time cost | Probability | Expected 12-month net | Effort (engineer-weeks) | Risk | Score |
|---|---|---|---|---|---|---|---|---|
| OPP-01 | New 1-year reservation for 240 CRM VMs | \$27,000 | \$0 | 90% | \$291,600 | 0.5 | Low: breaks even at 60% utilization, expected 100% | 583,200 |
| OPP-02 | Restore non-production schedules | \$12,000 | \$0 | 80% | \$115,200 | 1 | Low | 115,200 |
| OPP-05 | Release idle public IPv4 and old snapshots | \$1,500 | \$0 | 90% | \$16,200 | 0.5 | Low, with a grace period | 32,400 |
| OPP-03 | Log Analytics retention and sampling | \$6,000 | \$0 | 70% | \$50,400 | 2 | Medium: investigations need logs | 25,200 |
| OPP-04 | Payments EC2 to Graviton | \$9,000 | \$51,500 | 50% | \$28,250 | 12 | Medium: performance | 2,354 |

By expected value alone the log change would rank above the cleanup; per week of effort it does not. The ranking is also a sequence: usage changes that alter a commitment's size go before the commitment. Restoring the schedules lowers eligible EC2 usage, so the Savings Plan renewal in January is sized after it; the VM reservation can go first because nothing in the backlog changes the CRM VM footprint.

Keep out of the backlog anything without an owner, anything whose saving cannot be measured, and anything that trades reliability or security for money without the owner's explicit decision (moving disaster recovery to one zone, sampling security logs).

## 47e.11 Socializing and implementing with owning teams

The analyst does not change production. Every saving is implemented by a team with other priorities, so the work is to make the change easy, safe and credited.

**The one-page opportunity brief.** (1) What: resources, change, target state. (2) Evidence: utilization percentiles with the lookback, the chart and the query, so the team can reproduce it. (3) Savings: run-rate, in-year, annualized and net, at the team's effective rates, and how the result will be measured. (4) Risk and rollback. (5) Effort, and what FinOps will do (write the ticket, prepare the IaC change, verify). (6) Owner and a date inside the team's change windows.

**Socializing.** Start with the engineering manager, not a broadcast. Show the team's unit cost and trend, not a ranking against other teams. Bring performance or evaluation data for anything that touches latency or quality. Offer to pair on the first change, and credit the team by name in the monthly summary when it ships.

**Implementing.** The ticket lives in the owning team's backlog, not a FinOps queue; the change goes through the normal process (canary, change window, rollback plan); FinOps verifies one and two weeks after, records the realized saving and marks the implementation date, which starts the measurement. Commitment purchases follow the RACI of 47a.7: the analyst recommends, the central IT FinOps team that owns the payer account is accountable for the purchase, and IT Finance is consulted.

## 47e.12 Tracking realized savings

Projected savings are a promise; realized savings are a measurement against a counterfactual chosen before implementation, month by month, per initiative.

**The lab's tracker** through September 2026 (the Truth column exists only in the lab, which can regenerate its data without each initiative):

| Id | Initiative | Start | Method | Projected | Realized | Rate | Trend check | Last month | Status | Truth |
|---|---|---|---|---|---|---|---|---|---|---|
| INIT-01 | Rightsize payments RDS | 2026-03-01 | unit | \$98,000 | \$118,716 | 121% | \$114,285 | \$18,809 | on track | \$107,851 |
| INIT-02 | Schedule non-production compute | 2026-04-15 | trend | \$221,333 | \$141,835 | 64% | \$141,835 | \$20,376 | partial, decaying | \$136,652 |
| INIT-03 | S3 Intelligent-Tiering, payments logs | 2026-02-01 | rate | \$64,000 | \$52,922 | 83% | \$49,621 | \$8,782 | partial | \$52,922 |
| INIT-04 | Azure Hybrid Benefit, CRM VMs | 2026-05-01 | ratio | \$57,500 | \$62,231 | 108% | \$63,002 | \$12,449 | on track | \$62,231 |
| **Total** | | | | **\$440,833** | **\$375,704** | **85%** | **\$368,744** | **\$60,417** | | **\$359,657** |

Status rules: on track at 90% or more of projection, partial from 60% to 90%, at risk below 60%; decaying when the last full month is below 75% of the best month.

What the table teaches:

- **Each method fails in a known direction, so check it against a second one.** INIT-01's unit method claims \$118,716 against a true \$107,851, 10% high, because it assumes RDS cost grows with transactions (2% a month) when it grew 1.5%. The trend check is 6% high, because the six months it learned growth from include the November–December peak. Both overstate; the initiative still beat its business case. INIT-03's rate method matches the truth, because actual quantity × the old rate is exactly the counterfactual of a price change; its trend check is 6% low, because a damped trend under-projects steady 2.5% monthly growth.
- **Value usage on a shared commitment through the commitment.** INIT-02's EC2 runs under the shared Savings Plan, which stayed fully used. Every dollar of usage the schedule removed freed coverage that moved to other accounts, so the company saved the full contracted rate while the team's own amortized cost fell by less, because part of each removed dollar had been discounted. Measured on its own amortized cost, INIT-02 shows \$111,866; through the plan, \$141,835; the truth is \$136,652. Once a plan falls below full use, removing covered usage saves nothing until the plan expires.
- **Ramps are normal.** INIT-03 realized \$0 in February, \$3,324 in March and the full rate from April, because objects must go 30 days without access before they move.
- **Decay is the main risk.** INIT-02 peaked at \$33,635 in May and has run at about \$20,000 a month since July. It never crossed an anomaly threshold (47d.11); only the tracker saw it.

**Why savings decay.** Opt-outs that never expire; new resources created without the policy; instances scaled up during an incident and never reduced; new data landing in Standard because a new bucket lacks a lifecycle rule; a commitment that expires. Re-verify every initiative quarterly against its counterfactual, and close it only when the saving is embedded in a policy (IaC defaults, budgets, guardrails) rather than in someone's memory.

**Attribution when changes overlap.** In the lab, two changes hit the CRM production VMs in 2026: the Hybrid Benefit in May (license meter) and the reservation lapse in September (compute meter). On the bill line "Virtual Machines" alone, they partly cancel and nobody can tell what either did. The rules:

1. Measure each initiative on the meter or usage type it touches (license meter, compute meter, storage class).
2. When two initiatives touch the same meter, measure them in implementation order, each against a baseline that already includes the earlier ones, and record the order.
3. Keep rate and usage apart: commitments are measured as effective savings rate on eligible spend; usage initiatives as quantity reductions priced at the rate that applied at the margin before the change (the contracted rate while a shared plan is fully used). Then a rightsizing does not also claim the commitment's discount, and the commitment's ESR does not claim the rightsizing.
4. Never sum savings from overlapping methods without checking that the total does not exceed counterfactual minus actual for the whole scope.

**Control groups.** When a change rolls out to some accounts first, the accounts not yet changed are the best counterfactual: compare the change in cost per unit of the treated accounts against the untreated ones over the same weeks (a difference in differences), which removes seasonality and price changes that affect both.

## 47e.13 Expected savings in the forecast, and reporting progress

**Expected savings enter the forecast probability-weighted**, at monthly saving × probability from the expected start date, prorated in the first month. Chapter 47c.3 gives default probabilities by pipeline stage; depart from them only with a written reason. The lab's reasons: the reservation 90% (evidence complete, risk low, only the signature missing), the IPv4 and snapshot cleanup 90% (low risk, in the owning team's queue), the schedules 80% (booked for 15 October), the log change 70% (owner agreed, set for 1 November) and Graviton 50% (performance test open).

In the lab's forecast (47g) the pipeline is a separate layer: −\$19,331 in October 2026 (three items start on 15 October), −\$39,450 in November and −\$43,950 a month from December. When an item is implemented, it leaves the savings layer; the statistical baseline absorbs the new level within four weeks (the level is the median of the last 28 days). Leaving it in both places double-counts it, so move an implemented item's expected value into the baseline explicitly on its implementation date.

**Reporting progress.** One section of the monthly summary (47f.2):

- Realized this month and year to date against projection (the lab: \$375,704 of \$440,833, 85%; run-rate \$60,417 a month).
- The pipeline by stage, with expected value (\$55,500 a month at full value, \$43,950 probability-weighted).
- Decay alerts and slipped dates, with owners (INIT-02).
- The decisions needed this month, with their value (the reservation, about \$28,000 a month by the sizing in 47e.2 and carried in the pipeline at a rounded-down \$27,000; the schedules, \$12,000 a month).
- A savings burn-up chart: cumulative realized against cumulative projected, with the pipeline as a dashed extension (47f.4).

For a single efficiency number over time, the Foundation's Usage Optimization capability defines a Cost Optimization Index: COIN = [1 − (total savings opportunity ÷ total cost)] × 100, where 100 means no identified waste; AWS's Cost Efficiency metric (November 2025) has the same shape, [1 − potential savings ÷ optimizable spend] × 100 on net amortized cost. It rises when you stop looking for opportunities, so report it next to the size of the pipeline, never alone. Credit teams by name, and never report a projected saving as achieved.

**Interview line:** *"I commit to the floor of usage after known changes, not the average: break-even utilization is one minus the discount, so a layer is worth buying only if usage exceeds it in at least that share of hours; I ladder terms, prefer flexible plans when the architecture will move, and quote ESR with its definition. On usage I rightsize on percentiles with memory data, schedule non-production, tier storage after checking minimums and object sizes, and restate every saving at our effective rates. Then I prove it: a counterfactual chosen before the change, realized against projected every month, decay flagged, shared commitments valued at the margin, and expected savings in the forecast at their probability."*

## Sources

- AWS, [How Savings Plans apply to your usage](https://docs.aws.amazon.com/savingsplans/latest/userguide/sp-applying.html), [Returning a purchased Savings Plan](https://docs.aws.amazon.com/savingsplans/latest/userguide/return-sp.html) and [Reserved Instance and Savings Plans discount sharing](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ri-turn-off.html) (accessed 2 October 2026)
- AWS News Blog, [Introducing Database Savings Plans for AWS databases](https://aws.amazon.com/blogs/aws/introducing-database-savings-plans-for-aws-databases/) (2 December 2025) and AWS Cloud Financial Management blog, [the Cost Efficiency metric](https://aws.amazon.com/blogs/aws-cloud-financial-management/measuring-cloud-cost-efficiency-with-the-new-cost-efficiency-metric-by-aws) (November 2025)
- AWS, Compute Optimizer [rightsizing preferences](https://docs.aws.amazon.com/compute-optimizer/latest/ug/rightsizing-preferences.html), [metrics analyzed](https://docs.aws.amazon.com/compute-optimizer/latest/ug/metrics.html), [EC2 metrics](https://docs.aws.amazon.com/compute-optimizer/latest/ug/ec2-metrics-analyzed.html), [savings estimation mode](https://docs.aws.amazon.com/compute-optimizer/latest/ug/savings-estimation-mode.html) and [license recommendations](https://docs.aws.amazon.com/compute-optimizer/latest/ug/view-license-recommendations.html) (accessed 2 October 2026)
- AWS, [AWS Graviton processor](https://aws.amazon.com/ec2/graviton/) and [Microsoft licensing on AWS FAQ](https://aws.amazon.com/windows/faq/) (accessed 2 October 2026)
- AWS, [Amazon S3 storage classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html), [lifecycle transition considerations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html) and [S3 Intelligent-Tiering](https://aws.amazon.com/s3/storage-classes/intelligent-tiering/) (accessed 2 October 2026)
- AWS, [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/), [Gateway endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) and [AWS PrivateLink pricing](https://aws.amazon.com/privatelink/pricing/) (accessed 2 October 2026)
- Microsoft Learn, [What are Azure Reservations?](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/save-compute-costs-reservations), [Prepare to buy a reservation](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepare-buy-reservation), [How a reservation discount is applied to virtual machines](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/understand-vm-reservation-charges) and [Self-service exchanges and refunds](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations) (accessed 2 October 2026)
- Microsoft Learn, [Azure savings plans for compute](https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/savings-plan-overview), [Track a Microsoft Azure Consumption Commitment](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/track-consumption-commitment) and [Provisioned throughput onboarding](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/provisioned-throughput-onboarding) (accessed 2 October 2026)
- Microsoft Learn, [Azure Hybrid Benefit for Windows Server](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/hybrid-use-benefit-licensing), [Azure Hybrid Benefit for Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/azure-hybrid-benefit) and [Advisor cost recommendations](https://learn.microsoft.com/en-us/azure/advisor/advisor-cost-recommendations) (accessed 2 October 2026)
- Microsoft Learn, [Access tiers for blob data](https://learn.microsoft.com/en-us/azure/storage/blobs/access-tiers-overview), [Smart tier](https://learn.microsoft.com/en-us/azure/storage/blobs/access-tiers-smart), [FinOps toolkit changelog](https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/changelog) and [FOCUS conversion rules](https://learn.microsoft.com/en-us/cloud-computing/finops/focus/convert) (accessed 2 October 2026)
- Google Cloud, [CUD multiprice data model](https://docs.cloud.google.com/docs/cuds-multiprice-datamodel), [Spend-based committed use discounts](https://docs.cloud.google.com/docs/cuds-spend-based), [Committed use discounts](https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview) and [Sustained use discounts](https://docs.cloud.google.com/compute/docs/sustained-use-discounts) (accessed 2 October 2026)
- Google Cloud, [Storage classes](https://docs.cloud.google.com/storage/docs/storage-classes), [Object Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle), [Autoclass](https://docs.cloud.google.com/storage/docs/autoclass), [Cloud Storage pricing](https://cloud.google.com/storage/pricing) and [Bring your own licenses](https://docs.cloud.google.com/compute/docs/nodes/bringing-your-own-licenses) (accessed 2 October 2026)
- FinOps Foundation, [Rate Optimization capability](https://www.finops.org/framework/capabilities/rate-optimization/) (ESR options, utilization and waste KPIs, the 80% waterline) and [Usage Optimization capability](https://www.finops.org/framework/capabilities/usage-optimization/) (COIN; accessed 2 October 2026)
- FOCUS, [Determine effective savings rate](https://focus.finops.org/docs/use-cases/v1-4/determine-effective-savings-rate/) and [Commitment discount coverage rate](https://focus.finops.org/docs/use-cases/v1-4/calculate-commitment-discount-coverage-rate-with-eligibility-adjusted-denominator/) (accessed 2 October 2026)
- ProsperOps, [2025 AWS Compute Rate Optimization Insights](https://www.prosperops.com/library/2025-aws-compute-rate-optimization-insights/) (accessed 2 October 2026)
