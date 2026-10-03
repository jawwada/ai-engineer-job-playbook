# 47d. Cost allocation, tagging and anomaly management

> **What you need to be able to say:** why allocation starts with the account, subscription and project hierarchy and only then uses tags; a tagging standard that works on all three clouds and how each cloud enforces it; the KPIs that move compliance; business mapping with AWS Cost Categories, Azure cost allocation rules and a warehouse mapping table; four shared-cost methods and how to keep them out of disputes; Kubernetes and AI allocation with an idle-cost policy; how showback becomes chargeback and a journal entry; and anomaly management end to end: what the native detectors miss, a custom detector with its arithmetic, a triage runbook, severity levels and SLAs for driving resolution with owning teams, a planned-change calendar, a postmortem and six worked cases. Chapter 47 has the optimization catalog, 47a the cost metrics and accounting vocabulary, 47b the billing data and SQL, 47c forecasting and variance, 47e optimization and realized savings, 47f reporting and the interview, and 47g runs every method here on synthetic data.

The running example is the lab of chapter 47g: a fictional business unit with 13 sub-accounts on AWS, Azure and Google Cloud and \$1.23M of amortized cost in September 2026. It is separate from, and smaller than, the running example of 47a and 47c; both are fictional.

## 47d.1 Allocation starts with the hierarchy

Tags are the second allocation key, not the first. Some charges cannot carry a tag at all: support plans, taxes, most credits and refunds, commitment purchases, some data transfer and many marketplace charges. Tags arrive late: a resource tagged on the 20th carries the tag on its cost from the 20th onward (Google says so explicitly about labels; AWS's 12-month backfill fills values only where a tag existed; Azure's tag inheritance applies to the current month). And tags break silently when someone renames a key or changes its case. The hierarchy (AWS accounts, Azure subscriptions and resource groups, Google Cloud projects and folders) covers every dollar from the first day, because the provider stamps it on every row.

| | AWS | Azure | Google Cloud |
|---|---|---|---|
| Billing container | Management (payer) account, consolidated billing | EA enrollment or MCA billing account and billing profiles | Billing account |
| Workload container | Member accounts in organizational units | Subscriptions in management groups; resource groups inside | Projects in folders under an organization |
| Grouping in native reports | Linked account, Cost Categories | Management group, subscription, resource group; billing scopes | Project, folder, organization, label |
| Point to know | Organizations account tags apply to charges that cannot be tagged, including credits and refunds (December 2025) | Management groups are not a cost scope for MCA and exclude purchases | A billing account can pay for projects in other organizations |

**Design rules for the account structure.** Most of allocation is decided when the landing zone is designed.

1. One sub-account per application and environment where practical, at least one per team and environment. Production and non-production never share one.
2. Shared functions get their own sub-accounts: the network hub, security tooling, logging, and the management account that owns commitments.
3. Sandboxes are separate sub-accounts with an expiry date and a budget.
4. Multi-team sub-accounts are allowed only with mandatory tags. They are where unallocated cost comes from, so keep them few and watch them.

**The account map** is the first artifact to build: one row per sub-account with its provider, id, kind (`single`, `multi` or `shared`), default application, environment, cost center, owner, budget line and shared pool. Add `valid_from` and `valid_to`: when an account moves to another team on 1 July, add a row instead of editing the old one, or last quarter's chargeback will no longer reconcile. The same map gives visibility by environment for free, because production and non-production never share a sub-account.

The lab's 13 sub-accounts are 8 single-application, 2 multi-team (the data platform and the machine-learning sandbox) and 3 shared (network, security, management). September 2026 allocates like this:

| How the cost was allocated | Cost | Share |
|---|---|---|
| Direct, by tag (after normalizing aliases) | \$1,035,452 | 83.9% |
| Direct, by the account default (untagged storage in single-application accounts) | \$35,118 | 2.8% |
| Credits, to the account that earned them | −\$12,000 | −1.0% |
| Shared pools (network, security, commitments and governance) | \$167,131 | 13.5% |
| Unallocated (an untagged model experiment in the multi-team sandbox) | \$8,495 | 0.7% |
| **Total** | **\$1,234,195** | **100%** |

The same month allocated by tags alone leaves 18.0% unallocated (\$222,285). Normalizing aliases (`Application` to `application`, `payments` to `payments-api`) brings it to 11.1%. The account map brings it to 0.7%. That is the case for building the hierarchy first.

## 47d.2 A tagging standard that works on three clouds

A good standard is short; every extra required key lowers compliance and adds little. Four keys answer almost every allocation question.

| Key | Purpose | Allowed values come from | Example | Set by | Checked where |
|---|---|---|---|---|---|
| `application` | The service or product the cost belongs to; the main allocation key | Service catalog | `payments-api` | Engineering, in IaC modules | IaC validation, policy at creation, warehouse dictionary check |
| `environment` | Production versus non-production; drives scheduling and budgets | Fixed list | `prod`, `staging`, `dev`, `sandbox`, `shared` | IaC module default per account | Same, plus account map cross-check |
| `cost-center` | Finance's owner of the cost; drives chargeback | Finance chart of accounts | `cc-1001` | Derived from `application` in the warehouse; the tag is a check | Dictionary check |
| `owner` | The team that answers tickets and anomalies | Team directory (never a person's email) | `team-payments` | Derived from `application`; the tag is a check | Directory sync |
| `expiry` (optional) | When a sandbox or experiment should be deleted | Date | `2026-11-30` | The person creating it | Daily scan; budget actions in sandboxes |

**Case and format.** Use lowercase kebab-case for keys and values and write it into the standard, because the clouds treat case differently:

- **AWS** tag keys and values are case-sensitive, so `CostCenter` and `costcenter` become two cost allocation tags. AWS's tagging guidance recommends all lowercase with hyphens between words.
- **Azure** tag names are case-insensitive for operations, but the resource provider may keep the casing you supplied and cost reports show it; tag values are case-sensitive. `Prod` and `prod` are two values in a cost report.
- **Google Cloud** labels accept only lowercase letters, digits, underscores and dashes (international characters are allowed), with keys and values up to 63 characters and up to 64 labels per resource. A standard with uppercase values (`CC-1001`) cannot be applied on Google at all.

**Sources of truth.** Cost centers and owners change when finance reorganizes or a team splits, and nobody re-tags ten thousand resources when that happens. Keep a dictionary table in the warehouse (application → cost center → owner → budget line), refreshed from the service catalog, the chart of accounts and the team directory. Treat the resource's `cost-center` and `owner` tags as checks and derive the allocation values from `application`. One reorganization then becomes one row change.

**Untaggable and late-tagged cost.** Write a rule for each class of untaggable charge so nobody argues about it monthly: support fees pro rata to the usage they are priced on; taxes follow the underlying charge; credits and refunds go to the sub-account that earned them; commitment purchases are amortized into the covered usage (47a.4); marketplace subscriptions go to the buyer on the procurement record. For late tags, decide whether to restate history (AWS backfills up to 12 months, one request per 24 hours) or not, and say which in the footnote of every trend chart.

## 47d.3 Enforcing the standard on each cloud

Enforcement has three layers: block bad tags at creation, repair existing resources, and catch the rest in the data. No cloud gives you all three in one feature.

### AWS

- **Tag policies** (AWS Organizations) standardize keys, key case and allowed values. When a policy is *enforced* for a resource type, noncompliant tagging operations are rejected, but untagged resources and tags the policy does not define are not evaluated. The `ALL_SUPPORTED` wildcard (July 2025) enforces across every supported resource type of a service.
- **Required-tag validation in infrastructure as code** (November 2025) checks required tags from the tag policies before deployment, through a CloudFormation hook and Terraform and Pulumi integrations. This is the layer that stops untagged resources, which tag policies alone cannot.
- **Service control policies** can deny creation without a tag: a `Deny` on the create action with `"Null": {"aws:RequestTag/application": "true"}`. AWS's own example warns that CloudFormation creates a Secrets Manager secret and tags it in two steps, so the policy blocks secrets in stacks. Test each resource type, and prefer IaC validation for broad coverage.
- **Cost allocation tags** must be activated in the management account (`user:` for yours, `aws:` for AWS-generated) and take up to 24 hours to appear. Organizations account tags (December 2025) cover charges with no resource, including credits and refunds.

### Azure

- **Azure Policy** blocks and repairs. "Require a tag on resources" and "Require a tag and its value on resources" use the *deny* effect. "Inherit a tag from the resource group" and "Inherit a tag from the subscription" (each with an "if missing" variant) and "Add or replace a tag on resources" use *modify*, which tags at deployment and, through a remediation task, existing resources. *Append* is the older effect.
- **Tag inheritance in Cost Management** (EA billing account, MCA billing profile or subscription scope) copies subscription and resource-group tags onto usage records, not onto resources. It applies to the current month, takes 8 to 24 hours and skips purchases. It fixes allocation without touching infrastructure; it does not fix compliance on the resources.
- Resources do not inherit tags on their own; you need one of the two mechanisms above. Each resource, resource group and subscription can carry up to 50 tags.

### Google Cloud

- **Labels** are not inherited. The billing export carries them in `labels` (the resource's), `project.labels` and `system_labels` (set by Google), and a label carries cost only from the time it is applied.
- **Resource Manager tags** are governed by IAM, inherited down the hierarchy and usable in IAM and organization policy conditions; the export carries them in `tags` with `key`, `value`, `inherited` and `namespace`. Not every resource type supports them.
- **Practical pattern.** Label every project with the four keys, so every row carries them through `project.labels`; use resource labels only in multi-team projects; enforce labels in IaC and CI, and measure coverage from the export, not from inventory.

## 47d.4 Driving compliance up

Measure on cost, not resource count: a thousand untagged test buckets matter less than one untagged database.

| KPI | Formula | First target |
|---|---|---|
| Tagging Policy Compliance (FinOps Foundation KPI library) | compliant cost ÷ taggable cost | above 90% |
| Unallocated cost % (Foundation, Allocation capability) | effective cost of unallocated resources ÷ total cloud cost | below 10%, then 5% (suggested here) |
| Allocation Accuracy Index (Foundation, Allocation capability) | directly attributed cost ÷ total infrastructure cost × 100 | rising every quarter (suggested here) |

The Foundation's maturity examples put allocated spend at 70% or more for Crawl, 85% for Walk and over 90% for Run, and its Run description is the goal of the whole program: ownership and metadata fields enforced as a precondition for provisioning.

**Strict compliance, lenient allocation.** Measure compliance strictly (exact key, lowercase, a dictionary value) so the source gets fixed; allocate leniently (normalize aliases and case in the warehouse) so the showback is right today. In the lab, strict compliance is 83.6% while unallocated cost is 0.7%.

**Fix the expensive violations first.** The lab's list, by cost:

| Sub-account | Violation | Cost affected | % of taggable cost |
|---|---|---|---|
| aws-payments-nonprod | `application=payments` is not in the dictionary | \$85,181 | 7.1% |
| aws-shared-network | untagged | \$53,802 | 4.5% |
| gcp-analytics-prod | untagged storage buckets | \$23,429 | 2.0% |
| az-crm-prod | untagged storage accounts | \$11,690 | 1.0% |
| gcp-analytics-dev | key spelled `costcenter` | \$10,366 | 0.9% |
| aws-ml-sandbox | untagged model experiment | \$8,495 | 0.7% |
| aws-management | untagged governance services | \$3,689 | 0.3% |

Fixing one value on one account lifts compliance from 83.6% to 90.7% and clears the first target. That is the sentence to put in front of an engineering manager.

**The remediation loop.** (1) A weekly per-owner report: violations with cost, the exact fix (key, value, resource IDs) and a due date. (2) Defaults in the shared IaC modules, so new resources comply without anyone thinking about it. (3) Blocking at creation once the modules are in place. (4) Repair for existing resources: Azure Policy *modify* with remediation tasks, scripts elsewhere. (5) An exceptions register with expiry dates. (6) A monthly compliance chart by owner, with escalation for anything older than two cycles. In the lab, strict compliance rose from 44.0% in October 2025 to 83.6% in September 2026 in steps at each remediation date, while unallocated cost fell from 4.7% to 0.7%.

## 47d.5 Business mapping: from accounts and tags to the organization

Finance needs cost centers, products and business units; the mapping should live in one place, with history.

- **AWS Cost Categories** build business dimensions from rules on account, service, tag, charge type, usage type, billing entity or other categories, with inherited values and a default for anything unmatched. Split charges distribute a shared cost proportionally, by fixed percentages or evenly, but appear only in Cost Categories views, not in Cost Explorer, Budgets or Cost Anomaly Detection. Rules can apply up to 12 months back; an account can have 50 categories. Cost Categories also define the account groups for commitment group sharing (47e.1), so one mapping drives showback and the sharing policy.
- **Azure cost allocation rules** (EA and MCA) move cost from source subscriptions, resource groups or tags to targets, evenly, in proportion to total, compute, storage or network cost, or by custom percentages. Reservation and savings plan purchases are excluded, the invoice does not change, and the result appears in cost analysis, budgets and exports (`costAllocationRuleName`).
- **Google Cloud** has no comparable rule engine: map in BigQuery with a table joined to the export, usually keyed on project with label overrides.

Keep the authoritative mapping in the warehouse anyway: it is the only place where one rule set covers three clouds, keeps history and can be audited by IT Finance. A workable table has a stable `rule_id` (carried into the allocation output and the journal entry), a `priority` (explicit override, then tag, then sub-account default, then shared pool, then unallocated), match conditions (provider, sub-account, service, tag key and value), the result (application, cost center, budget line, shared pool), and `valid_from`, `valid_to` and `approved_by`. Test every change: each row of the month matches exactly one rule at the winning priority, allocated cost equals total cost, no cost center is negative except through credits, and the change log explains any month-over-month shift above materiality. Chapter 47b has the SQL for the joins.

## 47d.6 Shared costs

A shared cost is real cost that no single application caused. Leaving it central makes every team's unit cost look better than it is; spreading it carelessly starts arguments that outlast the analyst.

| Shared cost | Usual method | Notes |
|---|---|---|
| Network hub (transit gateways, NAT, interconnects, firewalls, DNS) | Usage-driven when bytes per consumer can be measured; proportional otherwise | Flow logs can attribute traffic; worth it only above a few percent of spend |
| Support plans | Proportional to the usage the fee is priced on | The fee is a percentage of spend, so proportional is also causal |
| Security tooling (SIEM, posture management) | Proportional, or GB ingested per source | Some companies keep security central on purpose |
| Shared platforms (Kubernetes, data platforms, observability) | Usage-driven (requests, CPU-hours, GB, queries) | Needs platform telemetry (47d.7) |
| Commitment benefits and waste | Discount follows usage through amortized cost; unused to a central pool | The policy question is who pays for waste |
| Enterprise purchases used by several teams | Fixed split agreed at purchase | Write it on the purchase request |

### Four methods on one pool

| Method | How | Strength | Weakness |
|---|---|---|---|
| Even | Pool ÷ number of consumers | Simple, stable | Unfair to small consumers |
| Proportional | Pool × consumer's share of direct cost | No extra data | Taxes large teams that may not use the service |
| Fixed | Agreed percentages, reviewed yearly | Predictable for budgets | Drifts during the year |
| Usage-driven | Pool × share of a measured driver | Causal; rewards efficiency | Needs telemetry; drivers can be gamed |

The lab's September network pool was \$53,802:

| Application | Direct cost | Even | Proportional | Fixed | Usage-driven (compute and network footprint) |
|---|---|---|---|---|---|
| payments-api | \$362,418 | \$8,967 | \$18,420 | \$21,521 | \$25,599 |
| claims-analytics | \$348,369 | \$8,967 | \$17,706 | \$13,451 | \$14,618 |
| customer-portal | \$191,564 | \$8,967 | \$9,736 | \$8,070 | \$10,642 |
| ai-assistant | \$88,639 | \$8,967 | \$4,505 | \$5,380 | \$538 |
| doc-intelligence | \$40,331 | \$8,967 | \$2,050 | \$2,690 | \$671 |
| ml-research | \$27,250 | \$8,967 | \$1,385 | \$2,690 | \$1,734 |

The AI assistant pays \$8,967 under the even method and \$538 under the usage-driven one, because its cost is model tokens rather than compute and network. Neither number is wrong; the driver decides. That is why the method is agreed before the numbers are shown.

The lab's showback applies the proportional method to all three pools:

| Application | Direct | Commitments and governance | Network | Security | Fully loaded | Share |
|---|---|---|---|---|---|---|
| payments-api | \$362,418 | \$17,696 | \$18,420 | \$21,103 | \$419,638 | 34.0% |
| claims-analytics | \$348,369 | \$17,010 | \$17,706 | \$20,285 | \$403,370 | 32.7% |
| customer-portal | \$191,564 | \$9,354 | \$9,736 | \$11,155 | \$221,808 | 18.0% |
| ai-assistant | \$88,639 | \$4,328 | \$4,505 | \$5,161 | \$102,633 | 8.3% |
| doc-intelligence | \$40,331 | \$1,969 | \$2,050 | \$2,348 | \$46,698 | 3.8% |
| ml-research | \$27,250 | \$1,331 | \$1,385 | \$1,587 | \$31,552 | 2.6% |
| unallocated | \$8,495 | | | | \$8,495 | 0.7% |

The commitments-and-governance pool this month includes a \$48,000 marketplace subscription, so payments (34.2% of direct cost) absorbs about \$16,400 of a security tool it did not choose. A fixed split written on the purchase request would have avoided the argument.

### Commitment benefits move cost between teams

AWS shares Reserved Instance and Savings Plans benefits across the organization by default, the owner account first and then the others. When one account's eligible usage jumps, it takes part of the shared discount and every other account's amortized rate rises. In the lab, the forgotten GPU cluster of May 2026 (47d.16) absorbed part of the Savings Plan: for its 12 days, the payments team's EC2 cost rose from 80.9% to 85.4% of the contracted rate, \$2,746 in total, with no change in the team's usage. The same shift fires anomaly alerts on accounts that did nothing (47d.11). Propose one policy in writing:

1. **Benefit follows usage** (the default amortized view): accurate for the month, noisy for teams.
2. **Restricted or prioritized group sharing** (generally available November 2025): Cost Categories define account groups; *prioritized* shares inside the group first and then across the organization, *restricted* only inside the group. Useful when a business unit buys its own commitments.
3. **Blended-rate showback:** charge every team its usage at a published rate (on-demand equivalent minus the portfolio's expected savings rate) and keep commitment savings and waste on a central line owned by FinOps. Teams see stable rates; the central team owns utilization. It suits a central team that buys commitments for everyone.

### Keeping shared costs out of disputes

Keep the pools few (three to five) and named; show shared cost on its own line ("you control this, we control that"); use drivers teams can see in their own telemetry and publish the calculation; change rules only at fiscal-year boundaries, except to fix errors; cap shared cost as a share of a team's fully loaded cost or explain when it exceeds the cap; give teams a five-business-day dispute window with a materiality threshold; and record each dispute, because a recurring dispute is a rule that needs changing.

## 47d.7 Kubernetes and AI allocation

### The Kubernetes model

The OpenCost specification (the model behind OpenCost, Kubecost and the AKS cost analysis add-on) prices a workload at the larger of what it requested and what it used (the scheduler reserved the request, so a pod that requests a core and uses a tenth still blocks the core). Cluster idle cost is the cluster's asset cost minus the workload costs. Overhead covers provider management fees and the cost of operating the cluster; treat system workloads (kube-system, daemon sets) the same way. Idle, overhead and shared workloads can be kept separate or spread uniformly, in proportion to tenants' costs, or by a custom metric.

**Worked example.** A cluster's nodes cost \$120,000 a month (amortized, commitments applied).

| | Requested | Used | Allocated (max of the two) |
|---|---|---|---|
| Team A | \$48,000 | \$30,000 | \$48,000 |
| Team B | \$20,000 | \$26,000 | \$26,000 |
| Team C | \$12,000 | \$6,000 | \$12,000 |
| System (kube-system, daemon sets) | | | \$9,000 |
| Idle (120,000 − 95,000) | | | \$25,000 (20.8%) |

| Idle policy | Team A | Team B | Team C | Platform team | Effect |
|---|---|---|---|---|---|
| Idle and system to the platform team | \$48,000 | \$26,000 | \$12,000 | \$34,000 | Teams have no reason to right-size requests |
| Idle and system proportional to workload cost (\$34,000 × share of \$86,000) | \$66,977 | \$36,279 | \$16,744 | \$0 | The platform team has no reason to bin-pack |
| Hybrid: system proportional, idle proportional up to a 15% target (\$18,000), excess idle (\$7,000) to the platform team | \$63,070 | \$34,163 | \$15,767 | \$7,000 | Teams pay for what they reserve plus a fair share; the platform team owns efficiency beyond the target |

Propose the hybrid: it rewards teams for right-sizing requests (47e.3) and gives the platform team a target for bin-packing and autoscaling. Publish the idle percentage monthly; a cluster at 20% idle against a 15% target is a platform backlog item, not a tenant problem.

### What each cloud gives you

- **Amazon EKS split cost allocation data** (ECS and Batch since April 2023, EKS since April 2024) splits each EC2 instance's amortized cost among its pods by the larger of requested and used CPU and memory, and spreads unused instance cost in proportion. GPUs, Trainium and Inferentia are included automatically since September 2025, and since October 2025 up to 50 Kubernetes labels per pod can be imported as cost allocation tags. Turn it on in billing preferences and in the CUR 2.0 export.
- **GKE cost allocation** needs the detailed usage cost export. Rows carry `goog-k8s-cluster-name`, `k8s-namespace`, `k8s-workload-type`, `k8s-workload-name` and `k8s-label/<key>`, with `kube:system-overhead` and `kube:unallocated`. Data can take up to three days, and a pod with more than 50 labels loses all of them.
- **The AKS cost analysis add-on**, built on OpenCost and reconciled with the Azure invoice, shows cost by namespace and by Azure resource with four charge types: idle, service (for example the uptime SLA and Defender for Containers), system (capacity AKS reserves on each node) and unallocated. It needs the Standard or Premium tier, EA or MCA, no virtual nodes, and supports about 7,000 containers per cluster under its current memory limit; data appears within 8 to 24 hours.
- **OpenCost** (a CNCF incubating project since October 2024, with an MCP server) and **Kubecost** (owned by IBM since September 2024) give one model across clouds, near-real-time data and allocation inside namespaces.

### AI spend

Chapter 47.6 and chapter 31.3 cover the three sources to combine (gateway virtual keys, the provider's allocation feature, OpenTelemetry token attributes joined to a price table). What changed in 2025–2026:

- **Amazon Bedrock.** Application inference profiles, created from a model or a cross-region inference profile, carry cost allocation tags, so each team invokes the model through its own tagged profile. Since April 2026, IAM-principal cost allocation adds the calling principal to the cost data (`line_item_iam_principal`, with an IAM-principal option in Data Exports), which allocates by caller without code changes.
- **Azure.** A deployment per cost center with tags, or a gateway that records tokens per key; shared provisioned throughput is allocated by tokens consumed, with unused capacity treated like Kubernetes idle.
- **Google Cloud.** A project or label per team; the FinOps Explainability Agent (generally available April 2026) breaks AI cost down by model, API key and token type, which makes API keys a practical allocation key.

Reconcile gateway totals with the provider bill monthly; a gap above a few percent means traffic bypassing the gateway or a wrong price table.

## 47d.8 Showback, chargeback and the journal entry

The FinOps Foundation's Invoicing & Chargeback capability is explicit: showback is visibility of cost for any group at any granularity and is always needed; chargeback formally posts cost to budgets and the general ledger and depends on accounting policy; neither is more mature than the other. Its KPIs are worth adopting as they are: chargeback processing time (cost incurred to cost posted), the general-ledger recharge rate (the gap between cloud cost in the FinOps tool and the amount charged in the ledger), the accuracy of chargebacks to the intended cost centers, and the variance between chargeback estimates and actuals. Crawl is manual spreadsheets with material variances and no shared-cost breakout; Run is automated integration with financial systems, reconciled at invoicing.

47a.3 explains the accounting: the chargeback debits cloud expense in each consuming cost center and credits a recharge account in the central cost center that pays the bills, so total expense does not change. The analyst's job is the file that feeds the entry, and its controls.

**The allocation file** has one row per period, cost center, GL account and allocation rule: period, legal entity, cost center, GL account, amount, cost basis (amortized), method (tag, account default, shared pool, credit), `rule_id`, and the source totals.

**Controls before it goes to finance.** (1) The file total equals the month's amortized cost to the cent, with the bridge to billed cost attached (47f.6). (2) Every dollar has a cost center; unallocated cost goes to a suspense cost center with a 30-day clearance rule, not into a shared pool where it disappears. (3) No cost center is negative except through credits. (4) Every line above materiality that moved more than 10% from last month has a comment. (5) The file is frozen at close; later corrections post in the current month as a prior-period adjustment (47a.3).

The lab's September showback as journal lines, in cents because the entry must balance (the central cost center is cc-1999; suspense is a fictional cc-9999):

| Cost center | Application | Debit (cloud hosting expense) | Credit |
|---|---|---|---|
| cc-1001 | payments-api | \$419,638.13 | |
| cc-1002 | claims-analytics | \$403,370.35 | |
| cc-1003 | customer-portal | \$221,808.37 | |
| cc-1005 | ai-assistant | \$102,633.38 | |
| cc-1006 | doc-intelligence | \$46,698.25 | |
| cc-1004 | ml-research | \$31,552.07 | |
| cc-9999 | suspense (unallocated) | \$8,494.78 | |
| cc-1999 | cloud recharge (central) | | \$1,234,195.33 |

Two judgment calls sit in this table. If Finance books the \$48,000 marketplace subscription as a prepaid expense (47a.3), the chargeback should carry \$4,000 a month for twelve months: the file follows the ledger, not the bill. And the \$8,495 in suspense needs an owner within 30 days or a rule that sends it to the sandbox's budget line.

**Moving from showback to chargeback.** Run three months of showback with the exact file that would be posted, publish disputes and resolutions, agree the shared-cost rules and the dispute window with IT Finance and the cost-center owners, and start at a fiscal-year or quarter boundary with budgets transferred to the consuming cost centers. Starting mid-year without budget transfers turns every team's first chargeback into an overrun.

## 47d.9 Anomaly management: definitions, lifecycle and KPIs

Three words get mixed up in reviews, and each has a different owner and clock:

- An **anomaly** is spend that differs, usually upward, from what was expected for a scope, seen at daily or hourly grain. It is handled in days, by the team that owns the resource.
- A **variance** is the difference between actual and budget or forecast for a period. It is explained at close, in the bridge (47c.6).
- A **trend** is a sustained change in level or growth rate. It belongs in the forecast, not an alert queue.

An anomaly nobody resolves becomes next month's variance; a variance that persists is a trend. The analyst's job is to move each item to the right queue fast.

In the Foundation's Anomaly Management capability, Crawl is manual checking, a week or more late, investigated centrally; Walk adds automated detection, context-relevant thresholds and routing to the responsible teams; Run adds event-system integration, thresholds tuned by persona and full root-cause analysis.

| KPI | Definition | Practical target |
|---|---|---|
| Anomaly count, by severity | Events confirmed after triage | Falling quarter over quarter |
| Mean time to detect | First flagged − start of the anomaly | Close to data latency: 1–2 days |
| Mean time to notify the owner | Owner notified − detection | Same business day for Sev1 and Sev2 |
| Duration unresolved | Resolution − start | Sev1 within 3 days |
| Actioned anomalies and spend avoided | Daily excess × days avoided by acting | Reported monthly, with the method |
| Anomaly cost % | Cost of anomaly spikes ÷ total spend | Below 2% |
| Alert precision (not a Foundation KPI) | Confirmed anomalies ÷ alerts sent to owners | Above 80%, or owners stop reading |

The Foundation's "Anomaly Detection Rate" KPI, written for AI spend, computes anomaly cost % and bands it: below 2% green, 2–7% yellow, above 7% red. The same ratio works for the whole estate. In the lab, anomaly cost % from April to September 2026 was 0.40%, 3.00% (yellow: the forgotten GPU cluster), 0.00%, 0.85%, 1.62% and 1.35%.

## 47d.10 The native detectors and where they stop

All three clouds detect cost anomalies at no charge; 47b.1–47b.3 list their features. What matters for driving resolution is how they differ:

| | AWS Cost Anomaly Detection | Azure anomaly detection | Google Cloud Billing anomaly detection |
|---|---|---|---|
| Cost basis | Net unblended cost | The day's total usage against a forecast from 60 days (univariate WaveNet model); the cost metric is not documented | Usage at on-demand rates (list or negotiated); CUD credits, sustained use discounts and promotions excluded |
| Scope | Monitors by service, linked account, cost category or tag; an AWS-managed monitor per value of a dimension; up to 500 custom monitors | Subscription only | Billing account, with project-level views |
| Cadence | About three times a day, up to 24 hours behind; rolling 24-hour windows | Daily, about 36 hours after the day ends | From historical patterns; early anomalies for AI services (preview, July 2026) 20–40 minutes after usage |
| Thresholds | Default 40% above expected and at least \$100; adjustable | Built into the model | Set automatically on cost impact and deviation; filter, for example, to \$200 and 20% |
| Root cause and routing | Up to 10 contributors; email, SNS, EventBridge | Drill-down in cost analysis; up to 5 alert rules per subscription, email | Top services, regions and SKUs; email per anomaly or daily summary, Pub/Sub |

Where they stop:

- **Calendar blindness.** A planned load test, a migration ramp or an annual renewal looks like a leak.
- **Wrong grain for ownership.** Azure's subscription scope and Google's billing-account scope do not map to applications; AWS monitors on cost categories come closest.
- **Different cost bases.** Your reports use amortized cost. A lapsed commitment raises AWS net unblended cost the day it ends, while Google's detector, which ignores CUD credits, does not see a CUD lapse at all.
- **No unit costs.** A prompt change that doubles cost per conversation on a growing service may stay inside every native threshold.
- **No cross-cloud view and no shared queue.**

Keep them on (the AWS and Google detectors catch fast spikes well), route their alerts into the same ticket queue, and run your own detector on the warehouse for application, unit-cost and cross-cloud views.

## 47d.11 A custom detector that works

The lab's detector (47g) works like this.

**Grain.** Daily amortized cost per sub-account and service, plus one-time purchases; add application and unit-cost series once allocation is in place.

**Baseline.** The median of the same weekday over the previous six weeks. Same-weekday comparison removes the weekly cycle: a non-production account at 40% of weekday cost on Saturday is normal.

**Spread.** The median absolute deviation (MAD) of those six values times 1.4826, which makes it comparable to a standard deviation for normal data. Medians resist the anomalies themselves: one spike in the history moves a mean and standard deviation a lot and a median not at all. Floor the spread at 5% of the median so a flat series (public IP hours) does not produce an infinite z-score on a 1% change.

**Three conditions, all required.** z = (today − median) ÷ spread of at least 4, an increase of at least 25%, and an increase of at least \$500. Percentage alone fires on tiny series; dollars alone fire on the noise of large ones; z alone ignores whether anyone should care.

**Worked example.** The previous six Mondays for a production EC2 series were \$3,820, \$3,910, \$3,760, \$3,880, \$3,850 and \$3,900. The median is \$3,865. The absolute deviations are 45, 45, 105, 15, 15 and 35, with median 40, so the spread is 1.4826 × 40 = \$59.30, floored to 5% of \$3,865 = \$193.25. Today is \$6,510: an excess of \$2,645, z = 13.7, +68%. All three conditions hold. (Illustrative; the lab's data-lag case in 47d.16 has the same shape, and triage rejects it.)

**Events, not days.** Consecutive flagged days merge into one event across gaps of up to two days, so a weekend does not split it. Severity uses the cost so far plus, if the event is still running, 30 days at the latest daily excess.

**Usage or rate.** Split each flagged day's excess into volume (the change in list-priced usage at the baseline effective rate) and rate (the change in effective cost per list dollar). An event that is 60% or more rate is labeled "rate": a lapsed commitment, a price change, a lost discount. It needs a different owner from a usage spike.

**Unit-cost series.** Run the same detector on cost per business unit, with impact measured as unit-cost excess times volume. In the lab, the AI assistant's cost per conversation rose from a baseline of \$0.0529 to \$0.0888 (+68%) on the worst day of a nine-day event worth \$16,846, while conversations did not change.

**Results on the lab's 18 months** (default rule): 11 events flagged; 4 planned (on the change calendar before detection); 1 data artifact; 6 labeled anomalies after triage, all true (precision 100%), covering all 6 detector-targeted anomalies (recall 100%); detection 1–2 days after the start, which is the providers' data latency. Raw precision before triage was 54.5%: without the calendar and the data-lag rule, almost half the alerts would have gone to owners for nothing.

**Tuning for precision.** The lab's threshold sweep:

| Rule | Thresholds | Events | Labeled | True | False | Precision | Recall | Missed |
|---|---|---|---|---|---|---|---|---|
| Loose | z ≥ 3, ≥ 15%, ≥ \$250 | 23 | 18 | 8 | 10 | 44.4% | 100% | |
| Medium | z ≥ 3.5, ≥ 20%, ≥ \$400 | 17 | 11 | 9 | 2 | 81.8% | 100% | |
| Default | z ≥ 4, ≥ 25%, ≥ \$500 | 11 | 6 | 6 | 0 | 100% | 100% | |
| Strict | z ≥ 5, ≥ 40%, ≥ \$1,000 | 8 | 5 | 5 | 0 | 100% | 83.3% | the expired reservation |

The strict rule misses the expired reservation because its daily excess (about \$790) sits under the \$1,000 floor, although it adds \$23,040 a month: a daily dollar floor is blind to moderate, persistent changes, so add a run-rate test (daily excess × 30 above a monthly materiality) or a weekly-aggregate detector. One of the loose rule's false alerts is instructive: on 23 May the data platform's EC2 cost rose 19% while its contracted cost rose 7%, because the GPU cluster was taking Savings Plan coverage away (47d.6). For series covered by a shared commitment, detect on contracted cost as well, or suppress alerts on the other accounts while one of them spikes.

Rules for tuning: set an alert budget per owner (no more than two false alerts a month) and tune to it; allow per-series overrides for noisy series (sandboxes, batch analytics); suppress through the calendar, never by muting a series; hold each provider's newest one or two days until complete (47a.5); review precision and recall monthly against the confirmed anomaly log, and thresholds quarterly.

**What the detector cannot do.** A step change is absorbed into the baseline after three to four weeks: the expired reservation was flagged from 1 to 21 September and then became "normal", so the ticket, not the detector, must keep it open. A slow leak never crosses the thresholds: when part of the non-production fleet left its schedule in July (+15% on weekdays, under \$500 a day), the detector saw nothing and the savings tracker caught it (47e.12). A ramp is seen only when it outpaces the baseline.

## 47d.12 The triage runbook

Seven steps, in order. Most false alarms die at step 1; most slow resolutions die at step 4.

1. **Validate.** Is the data complete? Check the provider's latency and partial days; whether the previous day dropped by about what this day rose (late rows); duplicated export partitions; currency or pricing-unit changes; credits and refunds posted on one day. If the two-day total is normal, close it as a data artifact and fix the pipeline check.
2. **Scope.** Which sub-account, service, region, SKU, resource and tag? When did it start, is it still running, and what shape is it: spike, step, ramp or periodic?
3. **Attribute.** Usage, rate or one-time? For usage, find the resources and the change behind them: deployments, IaC applies, CloudTrail, Azure Activity Log, Google Cloud Audit Logs, quota increases. For rate, check commitment expiries, price and discount changes, and shifts in shared commitment coverage. For one-time, check purchases and marketplace orders.
4. **Owner.** The account map gives the team; the ticket goes to the team's queue with a named person acknowledged. A multi-team or sandbox account without an owner is itself a finding.
5. **Decide.** With the owner: stop or scale down, fix the code or configuration, accept it as growth and move it into the forecast, or commit to it if it is a new steady state.
6. **Resolve and verify.** Watch the series return to baseline; record the anomaly's cost and the cost avoided.
7. **Document.** Close with a root cause, a reason code (leak, misconfiguration, planned but unannounced, rate change, data artifact, growth) and any change to the detector, the calendar or the guardrails. Sev1 and Sev2 get a postmortem (47d.15).

## 47d.13 Driving anomalies and variances to resolution

"Drive to resolution" means the analyst does not fix the resource but owns the outcome. That needs severity levels agreed in advance.

| Severity | Projected monthly impact, or trigger | Acknowledge within | Mitigate within | Escalate to, if missed |
|---|---|---|---|---|
| Sev1 | Above \$25,000, or any sign of misuse or a security cause | 4 business hours | 1 business day | Engineering director and the finance partner |
| Sev2 | \$5,000 to \$25,000 | 1 business day | 5 business days | Engineering manager |
| Sev3 | Below \$5,000 | 3 business days | Next sprint, or accept | Weekly FinOps review |

Scale the thresholds to the estate (these suit about \$1M a month); a useful rule is Sev1 above 2–3% of monthly spend.

**The ticket.** Title (series and amount); severity; start and detection dates; daily excess and cost so far; shape; usage, rate or one-time; resource IDs and links to the queries; the suspected change; owner and due date; the decision requested; closure criteria.

**Escalation.** Owner, then the owner's engineering manager, then the director in the weekly operations review, with IT Finance informed at Sev1. Escalate on missed SLAs, not on disagreement; disagreement is settled with evidence.

**When the owner says "it's growth".** Ask for the driver: customers, data, a launch. If it backs the change, close the ticket as "accepted" and add the change to the forecast with its date and run-rate; if not, keep it open. Either way the decision is written down.

**Follow-up.** A weekly 15-minute review of open items by age and severity, decisions needed and items accepted into the forecast. A ticket closes only when cost is back to baseline or explicitly accepted. Report the KPIs of 47d.9 monthly, by team.

**Variances use the same machinery.** Every month-end variance above materiality gets the same fields, a reason code (rate, usage, mix, timing, one-time, data) and an owner, and stays open until explained and, where needed, reflected in the forecast (47c.5 has the codes; 47c.6 the decomposition).

In the lab, detection was fast and resolution was not: the forgotten GPU cluster was visible on 19 May, one day after it started, and ran until 29 May, because the sandbox was multi-team with no routing rule and the alert went to a shared mailbox. The fix was organizational: an owner for every account, expiry tags in sandboxes, and a sandbox budget with an action that stops instances (AWS Budgets actions can apply an IAM policy or SCP or stop EC2 and RDS instances, automatically or after approval).

## 47d.14 The planned-change calendar

The planned-change calendar is the analyst's link with Cloud Engineering. One table suppresses expected spikes in anomaly detection and feeds known changes into the forecast (it can be the known-changes register of 47c.3).

| Field | Example |
|---|---|
| Id; start, end | PC-03; 2026-09-15, 2026-09-15 |
| Scope | Sub-account and service (wildcards allowed) |
| Type | planned spike, migration, one-time, decommission, commitment expiry, price change, credit end |
| Expected amount; recurrence | \$48,000; annual |
| Owner; description | team-security; annual SIEM subscription renewal through AWS Marketplace |
| Added on | 2026-09-10 |

Two rules make it work. An entry suppresses an alert only if it was added before detection; otherwise the calendar becomes a place to hide surprises. And it is filled automatically where possible: commitment end dates from the commitment inventory, credit end dates from contracts, renewals from procurement, decommissions and migrations from the engineering roadmap.

The lab shows both rules. The marketplace renewal was added on 10 September, after the 31 August forecast, so it was suppressed as an anomaly (detected on 16 September) but is still a \$48,000 variance against the forecast. The Azure VM reservation's end on 31 August was never on the calendar, so it is both an anomaly and a variance, and the most avoidable item of the month.

## 47d.15 The anomaly postmortem

Write one for every Sev1 and Sev2: one page, blameless (45a.6 describes the practice for incidents; the same rules apply to cost). Sections: summary (what ran, how long, what it cost); timeline (start, visible in data, detected, owner notified, mitigated, resolved); impact (excess cost, cost avoided, budget lines affected); detection (which detector, why not earlier, was it on the calendar); root cause (the change and why the system allowed it); what went well and what did not; actions with owners and dates; forecast effect.

**Example (lab case A4; costs from the lab, timeline narrative illustrative).** *Summary:* an eight-node GPU training cluster in the ML sandbox ran for 12 days after an experiment ended, costing \$30,057 above baseline. *Timeline:* started 18 May; visible and flagged 19 May (Sev1 by projected impact); the alert went to a shared mailbox; identified 27 May from the account's instance list; stopped 29 May. *Root cause:* no owner mapping for the multi-team sandbox, no expiry tag, no budget action. *Actions:* owner field mandatory in the account map (team-platform, done); `expiry` tag required in sandbox IaC modules (team-ml, two weeks); a sandbox budget with an approval-gated stop action (FinOps, one week); alerts for unowned accounts escalate to the platform lead at Sev1 (FinOps, done). *Cost avoided and lost:* stopping on the day of detection would have saved about \$25,000 of the \$30,057; leaving it until the June invoice review would have added about \$17,500 more.

## 47d.16 Six worked anomaly cases

Five come from the lab, so you can reproduce them; prices are the lab's illustrative ones unless marked as published.

**1. NAT gateway spike (usage).** From 10 to 15 February, the shared network account's NAT data processing rose by about 53,000 GB a day: about \$2,385 a day at the published us-east-1 price of \$0.045 per GB, \$13,651 over six days in the lab's amortized cost (z = 54.5, +272%). Triage: usage, in the hub VPC's NAT gateway; the change was a new nightly sync to a partner and a bulk copy to S3 routed through NAT. Response: send S3 traffic through a gateway endpoint (no additional charge), reach the partner through an interface endpoint if it offers one (\$0.01 per GB at the first tier plus hourly endpoint charges), and add a NAT-bytes alert. While there, check gateway-hours (\$0.045 each) and idle public IPv4 addresses (\$0.005 per IP-hour) (47e.6).

**2. Forgotten GPU cluster (usage).** From 18 to 29 May, the ML sandbox's EC2 cost rose nearly fourteenfold (+1,280% at peak, z = 203; \$30,057 of excess). Detection next day, resolution eleven days later (the postmortem above); and the cluster took part of the shared Savings Plan, so the payments team paid \$2,746 more for unchanged usage (47d.6).

**3. Logging explosion (usage).** From 7 to 11 July, Log Analytics ingestion in the CRM production subscription rose by about 780 GB a day after a release shipped with debug logging: about \$1,794 a day at the lab's \$2.30 per GB, \$9,037 in total (+191%), detected on 9 July, two days after it started (the lab's data latency for Azure). Response: revert the log level, add sampling and a per-table ingestion alert, review retention (pipeline item OPP-03, 47e.10). The owner is the application team, because its release caused it.

**4. Expired commitment: rates up, usage flat (rate).** From 1 to 28 September, the CRM production VMs' daily cost ran 34–64% above the same weekdays four weeks earlier while VM hours rose about 1.5%, and the detector labeled the event "rate". A one-year reservation for 200 VMs (4,800 hours a day) had ended on 31 August: the same hours moved from \$0.24 to \$0.40, \$768 a day, \$23,040 in September. Response: a new reservation sized to the current floor (240 instances, about \$28,000 a month, 47e.2), and every commitment end date on the calendar with alerts at 90, 60 and 30 days. If the VM family may change, a savings plan for compute fits better, because reservations bought from 1 February 2027 for savings-plan-covered services cannot be exchanged (47e.1).

**5. One-time marketplace charge (one-time).** On 15 September a \$48,000 SIEM subscription bought through AWS Marketplace appeared in the management account under a new service name. The detector flagged new spend; triage matched calendar entry PC-03 (added 10 September) and labeled it planned, but it is still a \$48,000 variance against the 31 August forecast. Response: no anomaly ticket; procurement feeds purchase orders into the calendar when they are raised; IT Finance decides between expensing it now and booking it as prepaid at \$4,000 a month (47a.3); a fixed split on the purchase request allocates it. Before the next renewal, compare marketplaces after contracts: a purchase that draws down a consumption commitment (47a.3) may be cheaper in effect.

**6. Data-lag false positive (data).** On 3 March the payments EC2 series dropped to 36% of normal; on 4 March it rose to 171% (+71%, z = 14.1, \$2,857 above baseline). The two-day total was normal: 65% of 3 March's rows had arrived late and were stamped with the next day. The data-lag rule labeled it an artifact and no owner was paged. Response: compare two-day sums before alerting, hold each provider's newest days until complete (Azure EA and MCA data can take 8 to 24 hours, pay-as-you-go up to 72; Google's export has no delivery guarantee), and log the event in the data-quality log.

A seventh case belongs to chapter 31: on 3 August a prompt release raised the AI assistant's tokens per conversation by 80% for nine days. The cost detector saw a usage spike (+98%); the unit-cost detector saw what mattered, cost per conversation up 68% with volume flat. The fix was a revert and a cost-per-conversation gate in the release pipeline.

**Interview line:** *"I allocate from the hierarchy up: an account map, then four lowercase tags enforced in infrastructure code, then written rules for shared costs, idle capacity and commitment benefits, so every dollar has an owner before anyone argues about tags. For anomalies I keep the native detectors on and run my own same-weekday median-and-MAD detector on amortized and unit cost, suppress only what was on the change calendar before detection, and drive each confirmed anomaly through a ticket with a severity, an owner, an SLA and a postmortem. The detector finds spikes; the savings tracker finds the slow leaks it cannot."*

## Sources

- FinOps Foundation, [Allocation capability](https://www.finops.org/framework/capabilities/allocation/) (Allocation Accuracy Index, unallocated-cost formula, maturity; accessed 2 October 2026)
- FinOps Foundation, [Anomaly Management capability](https://www.finops.org/framework/capabilities/anomaly-management/) (definition, phases, maturity, KPIs, the Anomaly Detection Rate bands; accessed 2 October 2026)
- FinOps Foundation, [Invoicing & Chargeback capability](https://www.finops.org/framework/capabilities/invoicing-chargeback/) (showback and chargeback, KPIs, maturity; accessed 2 October 2026)
- FinOps Foundation, [Maturity model](https://www.finops.org/framework/maturity-model/) (allocated-spend examples; accessed 2 October 2026)
- AWS, [Cost allocation tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html), [Tag policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html), [Example SCPs for tagging](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples_tagging.html) and [Tagging best practices](https://docs.aws.amazon.com/tag-editor/latest/userguide/best-practices-and-strats.html) (accessed 2 October 2026)
- AWS, [Cost Categories FAQs](https://aws.amazon.com/aws-cost-management/aws-cost-categories/faqs), [Reserved Instance and Savings Plans discount sharing](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ri-turn-off.html) and [Data Exports](https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html) (accessed 2 October 2026)
- AWS, [Cost Anomaly Detection FAQs](https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/faqs/) and [Amazon Bedrock inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html) (accessed 2 October 2026)
- AWS, [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/), [Gateway endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) and [AWS PrivateLink pricing](https://aws.amazon.com/privatelink/pricing/) (accessed 2 October 2026)
- Microsoft Learn, [Assign policy definitions for tag compliance](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-policies), [Use tags to organize Azure resources](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-resources), [Tag inheritance](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/enable-tag-inheritance) and [Cost allocation rules](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/allocate-costs) (accessed 2 October 2026)
- Microsoft Learn, [Understand and work with scopes](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-work-scopes), [Identify anomalies and unexpected changes in cost](https://learn.microsoft.com/en-us/azure/cost-management-billing/understand/analyze-unexpected-charges) and [AKS cost analysis](https://learn.microsoft.com/en-us/azure/aks/cost-analysis) (accessed 2 October 2026)
- Google Cloud, [Labels overview](https://docs.cloud.google.com/resource-manager/docs/labels-overview), [Tags overview](https://docs.cloud.google.com/resource-manager/docs/tags/tags-overview), [Export Cloud Billing data to BigQuery](https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery) and [Manage cost anomalies](https://docs.cloud.google.com/billing/docs/how-to/manage-anomalies) (accessed 2 October 2026)
- OpenCost, [Specification](https://www.opencost.io/docs/specification) (accessed 2 October 2026)
