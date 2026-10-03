# 47a. The cloud FinOps analyst: the role decoded, the finance vocabulary and the operating cadence

> **What you need to be able to say:** what a multi-cloud FinOps analyst produces each day, week, month, quarter and year, and which artifact each line of the job description becomes; where the role sits in the 2026 FinOps Framework; the finance vocabulary IT Finance uses (outlook, accruals, prepaid commitments, chargeback, fiscal calendars, FX, consumption commitments); the cost metrics on AWS, Azure, Google Cloud and FOCUS and which one answers which question; when each cloud's month is final; and how you work with Cloud Engineering, IT Finance, Business Planning and the central IT FinOps team. Chapter 47 covers FinOps as a discipline and chapter 31 AI token economics; 47b–47g continue this track: billing data and tools, forecasting and variance, allocation and anomalies, optimization, reporting and the interview, and a lab.

Most of this book is about building systems. This chapter is about a job whose product is a number other people make decisions with. A FinOps analyst on a multi-cloud estate owns the cloud forecast, explains every variance, keeps allocation complete, and turns optimization ideas into dollars that appear in the forecast before they appear on the bill. Engineers moving into the role usually know the cloud side and not the finance side; people from finance know the opposite. The interview tests whether both sides will trust you.

## 47a.1 The job description decoded

A representative multi-cloud FinOps analyst job description (anonymized and paraphrased) lists 22 responsibilities in five groups: forecasting and tracking across AWS, Microsoft Azure and Google Cloud; visibility, allocation and anomalies; partnership with Cloud Engineering, a central IT FinOps team at the parent-IT level, IT Finance and Business Planning; executive communication; and savings, from commitments to licenses, tracked as realized and fed back into the forecast. It asks for five qualifications, from hands-on FinOps to working knowledge of each cloud's native cost tools. The tables below decode every line.

### The four readings (chapter 35)

- **The pain.** The line about preventing conflicting numbers means the business unit's figures and the parent IT organization's have already collided in front of leadership. The line about planned changes reaching the forecast before the bill means a migration has surprised finance. Reporting with minimal rework means finance has rebuilt earlier reports. Trends versus noise means someone overreacted to a calendar effect or missed a slow leak.
- **The system.** A monthly operating cycle on a data pipeline: three billing exports land in a warehouse, are normalized to FOCUS (47b), feed a driver-based forecast and a variance bridge (47c), and come out as an executive summary, an accrual estimate, a chargeback file and a reconciliation with the central team. Draw that loop before the interview, with the known-changes intake from Cloud Engineering on one side and IT Finance's close calendar on the other.
- **The interviewer.** Usually a head of cloud platform, a director of IT finance or the central FinOps lead, with an IT Finance partner and a cloud engineering lead on the panel. They test fluency (bridge forecast to actual in your head), judgment (is this a trend?) and communication (three sentences to a CFO).
- **Ninety days.** One set of numbers agreed with the central team and IT Finance, a driver-based forecast with an accuracy log, a monthly summary finance uses without rework, and a savings tracker that feeds the forecast. The plan is in 47a.8.

### Every responsibility, decoded

The last column is where this book teaches it, so the table doubles as a coverage map for the track.

| # | Responsibility (paraphrased) | What it means in practice | Artifact | Where taught | How an interviewer probes it |
|---|---|---|---|---|---|
| R1 | Monthly and quarterly forecasts for AWS, Azure and Google Cloud | A rolling 12–18-month model by cloud, cost center and month on amortized cost: baseline, drivers, known changes; refreshed monthly, reforecast quarterly | Forecast model, assumptions register, versions | 47c.2–47c.5, 47c.8 | "Walk me through next year's forecast for three clouds." |
| R2 | Track actuals against forecast and budget; find variances early; explain the drivers | Daily tracking against a phased forecast, a mid-month landing estimate, a month-end bridge in rate, usage, mix and timing | Landing note; bridge and commentary | 47c.2, 47c.6 | "Spend is 6% over forecast. Explain it to the CFO in three sentences." |
| R3 | Visibility by account, service, environment and application | Every dollar mapped to an owner, environment and application, through the hierarchy first, then tags | Mapping table, showback dashboard | 47b.6, 47d.1–47d.5 | "What share of spend is allocated, and how would you raise it?" |
| R4 | Improve tagging, allocation and financial visibility | A short tagging standard enforced in infrastructure as code; written shared-cost rules | Tagging policy, compliance dashboard | 47d.2–47d.6 | "A team refuses to tag. What do you do?" |
| R5 | Identify anomalies, unexpected growth and emerging risks | The three native detectors plus your own unit-cost checks; a risk register of commitment expiries, expiring credits, price changes and contract milestones | Anomaly log, risk register | 47d.9–47d.11, 47c.4, 47c.7 | "The detector fired on a 35% jump in a \$2k-a-day service. What next?" |
| R6 | Drive significant anomalies and variances to resolution | A ticket with owner, severity, due date and cost at risk; closed only when cost normalizes or is accepted into the forecast | Tracker with detection and resolution times | 47d.12–47d.13 | "Tell me about a time an owner did not respond." |
| R7 | Separate trends from temporary fluctuations | A written procedure, and a forecast treatment for each shape of change | Signal-versus-noise checklist | 47c.7 | "February is down 9%. Good news?" |
| R8 | Get Cloud Engineering's planned changes into the forecast before the bill | A weekly intake: owner, dates, ramp, steady state, double-running, decommission date, confidence | Known-changes register | 47c.3, 47d.14, 47f.7 | "Engineering migrates a data platform next quarter. How does it show up?" |
| R9 | Reconcile with the central IT FinOps team | Shared definitions (metric, scope, shared costs, cut-off, FX), a monthly bridge, a signed agreement | Bridge; single-source-of-truth agreement | 47c.9, 47f.6 | "Your number is \$97k below the central team's. Walk me through it." |
| R10 | Align with IT Finance and Business Planning budget cycles, assumptions and funding decisions | Finance's drivers, calendar and basis; funded projects enter as known changes | Planning calendar, assumptions register, budget submission | 47a.3, 47c.8 | "A project is funded after the budget is locked. What changes?" |
| R11 | Translate technical changes into financial impact | Run-rate, in-year cost, cash and unit cost of an engineering decision | One-page impact notes | 47f.7, 47c.8 | "Explain a three-year Savings Plan to a finance director." |
| R12 | Build credibility with technical and finance leaders | Early, right, traceable, in each audience's language | Accuracy log; no surprises at close | 47f.8 | "Tell me about a time you changed an engineering leader's mind with data." |
| R13 | Recurring and ad hoc executive summaries | A monthly page; quick-turn briefs in between | Monthly summary, briefs | 47f.2–47f.3, 47c.6, 47a.6 | "What goes on your one page?" |
| R14 | A narrative on two or three numbers, drivers, risks, opportunities and actions | Outlook against budget, month against forecast, savings realized; three drivers; sized risks; decisions | The summary's structure | 47f.1–47f.2 | "Summarize this dashboard in two numbers." |
| R15 | Present to senior leadership | Live, with hard questions | Memo or short deck | 47f.5 | A mock presentation |
| R16 | Defend the assumptions, method and drivers | Every number traceable to data and to an owned, dated assumption | Methodology note, backtests | 47c.5, 47f.5 | "Why should I trust your forecast?" |
| R17 | Decision-ready reporting with minimal rework | Finance's cost centers, calendar and FX, reconciled to the ledger | Templates agreed with IT Finance | 47f.2, 47a.3 | "How would you know finance can use it without rebuilding it?" |
| R18 | Identify and quantify savings: commitments, rightsizing, storage tiering, idle resources, licenses | A ranked pipeline with net savings, probability, effort, risk and owner | Savings pipeline | 47e.1–47e.10 | "Rank these five opportunities." |
| R19 | Socialize opportunities with owners | Evidence, risk and effort, taken to the owning team | Opportunity briefs | 47e.11 | "How do you get a team to act on a recommendation?" |
| R20 | Implement optimization with owning teams | Plan, schedule and verify without breaking production | Implementation plan | 47e.11 | "Tell me about a rightsizing that went wrong." |
| R21 | Track realized savings; put expected savings in the forecast | Counterfactual baselines; a probability-weighted savings layer | Savings tracker, forecast layer | 47e.12–47e.13, 47c.3 | "How do you prove a saving when usage also grew?" |
| R22 | Monitor results and communicate progress | Monthly pipeline update and commitment KPIs | Savings section of the summary | 47e.13, 47b.10 | "Which commitment KPIs do you report, and why?" |

### The qualifications, decoded

| Qualification (paraphrased) | What it really asks | How to show it | How it is tested |
|---|---|---|---|
| Hands-on FinOps, cloud financial management or technology finance | You have run a close, a forecast and a savings program, not only read about them | Two stories with numbers: a variance you explained and a forecast you rebuilt (47f.13, chapter 38) | "Describe your last month-end close, day by day." |
| Multi-cloud financials (AWS, Azure, Google Cloud) | You know where the billing models differ: amortization, credits, data timing, hierarchy | The metric table in 47a.4, from memory | "How does amortized cost on AWS differ from amortized cost on Azure?" |
| Forecasting and variance analysis, with judgment about trends | Method plus judgment: you know when not to react | The signal-versus-noise procedure (47c.7) and an accuracy log (47c.5) | Case questions with a chart |
| Spend tracking, forecasting, budgeting and variance analysis | Mechanics: phasing, landing estimates, bridges, reforecasts | A worked bridge (47c.6) | A spreadsheet or SQL exercise (47f.12) |
| Native tools: Cost Explorer and CUR, Azure Cost Management, Google Cloud Billing and the BigQuery export | An answer from each console, and SQL against each export | The recipes in 47b | "Find the top movers in Cost Explorer," or live SQL |

## 47a.2 Where the role sits in the FinOps Framework 2026

The FinOps Foundation published the 2026 Framework in March 2026. Its definition now speaks of maximizing the business value of technology, not of cloud alone. It keeps the three phases (Inform, Optimize, Operate) and the Crawl, Walk, Run maturity scale, and organizes the work into four domains with 22 capabilities.

| Domain | Capabilities (2026 name; former name where it changed) |
|---|---|
| Understand Usage & Cost | Data Ingestion; Allocation; Reporting & Analytics; Anomaly Management |
| Quantify Business Value | Planning & Estimating; Forecasting; Budgeting; KPIs & Benchmarking (formerly Benchmarking); Unit Economics |
| Optimize Usage & Cost | Architecting & Workload Placement (formerly Architecting for Cloud); Rate Optimization; Usage Optimization (formerly Workload Optimization); Sustainability (formerly Cloud Sustainability); Licensing & SaaS |
| Manage the FinOps Practice | FinOps Practice Operations; Governance, Policy & Risk (formerly Policy & Governance); FinOps Assessment; Automation, Tools & Services (formerly FinOps Tools & Services); FinOps Education & Enablement; Invoicing & Chargeback; Intersecting Disciplines; Executive Strategy Alignment (new in 2026) |

Executive Strategy Alignment is the one new capability. It ties technology spending to business strategy through executive priorities, multi-year investment strategy, product prioritization and decision support, and it is the capability behind the request for summaries built on a few numbers: the summary exists to support a decision, not to describe the bill. Use the 2026 names in an interview; "Usage Optimization" rather than "Workload Optimization" shows that you follow the practice as it is now.

### The job description mapped to capabilities

| Theme | Responsibilities | Primary capability | Supporting capabilities |
|---|---|---|---|
| Forecasting and budgeting | R1, R2, R10, R16 | Forecasting | Budgeting; Planning & Estimating |
| Visibility and allocation | R3, R4 | Allocation | Data Ingestion; Governance, Policy & Risk |
| Anomalies and trend judgment | R5–R7 | Anomaly Management | Reporting & Analytics |
| Engineering partnership | R8, R11 | Planning & Estimating | Unit Economics |
| One set of numbers with the central team | R9 | Reporting & Analytics | Invoicing & Chargeback; Intersecting Disciplines |
| Executive communication | R12–R15, R17 | Reporting & Analytics | Executive Strategy Alignment |
| Commitment, usage and license savings | R18 | Rate Optimization; Usage Optimization; Licensing & SaaS | Architecting & Workload Placement |
| Implementing and tracking savings | R19–R22 | FinOps Practice Operations | KPIs & Benchmarking |

By phase, R3, R4 and R13 are mostly Inform, R18–R20 are Optimize, and the cadence work (R2, R5, R6, R9, R10, R21, R22) is Operate. The weight sits in Quantify Business Value and Understand Usage & Cost, with a savings program attached; a cost-engineering job sits mostly in Optimize Usage & Cost.

Planning & Estimating and Forecasting are easy to confuse. The Foundation treats estimating as exploratory costing of options, led by engineering and done often (architecture reviews, new workloads), and forecasting as the maintained model of spend the organization has committed to; estimates are inputs to the forecast. In practice an engineer's estimate enters your forecast when it becomes a known change with a date and an owner (47c.3).

### Personas, scopes and technology categories

The Framework's six core personas, and the two allied personas that matter most here, as real people in this job:

| Persona | Who it is here | What they need from you |
|---|---|---|
| FinOps Practitioner | You, and the central IT FinOps team at the parent level | Shared definitions and data; one set of numbers |
| Engineering | Cloud Engineering (the build team) and application engineers | Early, specific cost signals; credit for savings |
| Finance | IT Finance | Numbers that tie to the ledger, on the close calendar, in their cost centers |
| Product | Application owners; Business Planning for business drivers | Unit costs; the cost of a launch |
| Procurement | Whoever negotiates enterprise agreements and consumption commitments | Drawdown against commitments; renewal inputs |
| Leadership | CIO or CTO, business unit leaders, finance director | Two or three numbers, risks with ranges, decisions |
| Allied: IT financial management | The parent IT organization's cost model and ledger | Consistent scope mapping and definitions |
| Allied: IT asset management | License owners | License counts and bring-your-own-license status |

The Foundation's 2026 survey found that 78% of FinOps practices report into the CTO or CIO organization and 8% into the CFO's, so expect your manager to sit on the technology side and your most demanding customer to be finance.

A **scope** in the Framework is a defined segment of technology spending aligned to a business construct, such as a product, a cost center or an environment. Three matter here: the business unit's whole three-cloud estate (yours end to end), the application and environment scopes inside it (where owners act), and the parent IT scope the central team reports (where your numbers must reconcile). Of the Framework's **technology categories** (Public Cloud, SaaS, Data Cloud Platforms, Data Center and AI, with Private Cloud and Licenses also listed), this job is Public Cloud first; it touches SaaS and Licenses through marketplace purchases and license optimization, and AI as soon as a team uses managed models (chapter 31). The same survey found that 98% of respondents now manage some AI spend.

### Maturity markers worth quoting

| Measure | Crawl | Walk | Run | Source |
|---|---|---|---|---|
| Forecast-to-actual variance (maturity-model examples) | under 20% | under 10% | under 5% | FinOps maturity model |
| Budget variance from actual (Budgeting KPI targets) | at most 20% | 15% | 12% | Budgeting capability |
| Share of spend allocated | at least 70% | at least 85% | over 90% | FinOps maturity model |
| Commitment coverage | about 60% | over 75% | over 80% | FinOps maturity model |
| Forecasting method | manual, mostly historical | rolling and trend-based, with commitments included | rolling, trend-based and driver-based, on discount-adjusted amortized data | Forecasting capability |

The forecast and budget thresholds measure different things; 47c.5 shows how to report both.

## 47a.3 Finance vocabulary for engineers

Using IT Finance's words precisely is the fastest way to earn its trust; loose phrases ("the budget changed", "we saved \$50k") lose it. The running example here and in 47c is a business unit whose 2026 fiscal year is the calendar year.

### Planning words

- **Annual operating plan (AOP).** The plan for the fiscal year that leadership approves: revenue, headcount and expenses by cost center and month. Cloud usually appears as one or more expense lines per cost center. It is built two to four months before the year starts from the run-rate, business drivers and known projects, and once approved it becomes the budget. Example: a cloud AOP of \$29.40M for 2026, phased at \$2.40M a month for January–September and \$2.60M for October–December for a seasonal peak.
- **Budget.** The approved amount for a scope and period. It normally does not change during the year, and that is the point: variance to budget tests whether the plan was right and keeps owners accountable. Many companies allow formal budget transfers between cost centers; few allow quiet edits.
- **Forecast.** Your current best estimate of what will be spent, changed whenever information changes: lightly every month, formally every quarter. Variance to forecast measures predictability, which finance needs for cash planning and for any guidance the company gives externally.
- **Outlook or latest estimate (LE).** Actuals for closed months plus forecast for the rest. "9+3" means nine months of actuals and three of forecast. After September, \$22.05M of actuals plus a \$7.86M fourth-quarter forecast gives a \$29.91M outlook, \$0.51M (1.7%) above the \$29.40M budget.
- **Run-rate.** The current spending level extrapolated, always with its window and unit: "September's daily average × 365" is an annualized run-rate; "the last seven complete days × days in the month" a monthly one. The **exit run-rate** (the last month's or last weeks' daily rate) is where next year's budget starts. Run-rate ignores known changes and seasonality, so it is a baseline, not a forecast. Quote it per day so a 28-day February does not look like a saving.

### Variance words

- **Plan versus actual versus forecast.** Every finance review shows budget, latest forecast and actual. For the running example's September:

| | Budget | Forecast | Actual | Actual − budget | Actual − forecast |
|---|---|---|---|---|---|
| Cloud spend, \$k | 2,400 | 2,510 | 2,549 | +149 (U), +6.2% | +39 (U), +1.6% |

  The August reforecast already put September \$110k above budget, so leadership knew about most of the overrun a month early. That early warning is what a forecast is for.
- **Favorable and unfavorable.** For costs, spending less than plan is favorable (F), more is unfavorable (U). Teams differ on whether they print actual − plan or plan − actual, so agree the sign convention with IT Finance and always print F or U next to the number.
- **Materiality.** The threshold above which a variance needs an explanation, usually a dollar amount and a percentage that must both be exceeded: for example \$25k and 2% for a cloud, \$10k and 5% for a single service. Below it, report the number and move on. Adopt the controller's thresholds rather than inventing your own.
- **Variance types.** Rate (price, discount, FX), usage (volume), mix (a shift between items with different prices), and timing or one-time items (real costs that landed in a different month than planned, or will not recur). 47c.6 gives the formulas and a three-cloud bridge.

### Accounting words

- **Accrual and true-up.** The books close before all invoices arrive, so a month's expense is recorded from estimates. Suppose September closes on business day 4 (BD4) while invoices and late charges arrive in the first two weeks of October (47a.5). On BD3 you give IT Finance September's usage charges on the billed basis, excluding prepaid purchases (prepaid assets amortized from their own schedule): \$2,485k in the running example (47c.10). Finance debits cloud hosting expense and credits accrued liabilities, reverses the accrual in October and books the invoices as they arrive. The AWS support fee, estimated at \$45k, came in at \$47k, so October carries a \$2k true-up that belongs to September. Estimate the incomplete last days and the late-posting charges (support, marketplace, taxes) explicitly, and log accrual error as you log forecast error.
- **CapEx and OpEx.** Capital expenditure buys assets that last more than a year and is depreciated; operating expenditure is expensed as incurred. Cloud consumption is operating expense, so cost moves with usage every month instead of stepping up at a hardware purchase. An all-upfront Reserved Instance or Savings Plan is still not capital expenditure: it is a prepayment for a service, held as a prepaid expense and released over its term. Some one-time implementation costs may be capitalized under company policy; the controller decides.
- **Prepaid commitments and amortization.** A standalone illustration, separate from the running totals and reused in 47a.4: on 1 September 2026 an AWS account buys a one-year, all-upfront Compute Savings Plan at \$10.00 an hour, 8,760 hours × \$10.00 = \$87,600 paid at once. Accounting debits prepaid expenses and credits cash for \$87,600, then releases part of it to expense each month. AWS amortizes by the hour: September (720 hours) carries \$7,200, October (744 hours) \$7,440, February 2027 (672 hours) \$6,720, and the twelve months sum to \$87,600. Many accounting teams amortize straight-line at \$7,300 a month. Neither is wrong, but the difference (+\$100 in September, −\$140 in October) becomes a monthly reconciling item unless you agree on one method. Budgets and forecasts use amortized cost, the P&L view, with a separate cash view for purchases.
- **Cash versus P&L.** Cash leaves when an invoice is paid; expense is recognized when the service is consumed. A three-year all-upfront commitment is a large cash event and a small monthly expense. Treasury cares about the first, the P&L about the second, and your model must produce both. Whether to pay upfront at all is a **cost of capital** question: the extra upfront discount must beat the return treasury expects on cash (47c.8 works an example).

### Organization words

- **Cost center, GL account, legal entity, project code.** A cost center is the unit that owns a cost (the Payments team); a general ledger (GL) account says what kind of cost it is (cloud hosting, software subscriptions); the legal entity says which company in the group incurred it, which matters for tax and transfer pricing; capital projects add a project or work-breakdown code. Your allocation must produce all four for every dollar.
- **GL mapping.** The rules that send each kind of charge to the right account:

| Charge in the billing data | Typical GL treatment | Cost center comes from |
|---|---|---|
| Cloud service usage (compute, storage, databases, networking, AI) | Cloud hosting expense | Account, subscription or project mapping, refined by tags or labels |
| Upfront commitment purchases | Prepaid expense, amortized monthly to cloud hosting expense | The owners of the covered usage, through amortized cost |
| Marketplace software and licenses | Software subscriptions expense, or prepaid if paid upfront for a term | The buyer of the subscription |
| Support plans | Cloud support expense | A rule, usually pro rata to usage |
| Taxes | The company's tax treatment (recoverable VAT is not an expense) | Follows the underlying charge |
| Credits and refunds | Reduce the expense they relate to | The cost center that bore the original charge |

- **Showback and chargeback.** Showback reports costs to teams; chargeback posts them to the teams' budgets through journal entries. The FinOps Foundation's Invoicing & Chargeback capability treats neither as more mature than the other; which one you run is company policy. A chargeback entry, with central IT paying all three cloud bills from its own cost center (call it Cloud Platform): if the Payments team's effective cost for September is \$310,400, finance debits cloud hosting expense in the Payments cost center by \$310,400 and credits a cloud recharge account (a contra-expense) in Cloud Platform by the same amount. Total expense does not change; it moves to the team that caused it. Your allocation file feeds that entry, which is why its total must reconcile to the bill, and why a change to it after close becomes a prior-period adjustment.

### Calendar and currency

- **Fiscal versus calendar months.** A fiscal year that starts in July makes July–September 2026 the first quarter of fiscal 2027: a relabeling. A 4-4-5 calendar is harder: fiscal months are four or five whole weeks ending on a fixed weekday. If fiscal September ends on Saturday 26 September 2026, then 27–30 September belong to fiscal October, while every cloud bills the calendar month. Restate cloud costs into fiscal months from daily data, and write a rule for charges booked once a month (support fees, recurring commitment fees, and the unused reservation fees that Cost Explorer's daily amortized view places on the first of the month).
- **Time zones.** AWS and Azure cost data use UTC days. Google Cloud's billing reports start each day at midnight US Pacific Time and follow US daylight saving time, so a daily total computed in UTC from the BigQuery export will not match the console. Pick one convention per report and put it in the footnote.
- **FX.** Keep currency effects out of cost effects. An Azure billing profile invoiced in euros spends €400,000 in September: \$440,000 at the \$1.10 budget rate, \$432,000 at September's \$1.08 average. The \$8,000 is a favorable FX variance on its own line, not inside "Azure usage". Google's export carries `currency_conversion_rate` (`cost` ÷ rate gives US dollars), Microsoft's FOCUS export `x_BillingExchangeRate` and US-dollar copies of the cost columns, AWS's CUR `line_item_currency_code` and `pricing_currency`. Agree with IT Finance which rate applies to budgets (usually a fixed budget rate), actuals (usually the monthly average) and forecasts (usually the budget rate, with FX sensitivity shown separately).

### Contract words

- **AWS Enterprise Discount Program or Private Pricing Agreement (EDP or PPA; both names are used).** A commitment to a level of AWS spend over a term in exchange for a discount across most services. The discount appears as negative discount line items or in the discount columns of the CUR, and flows into the `net_` cost columns (47a.4).
- **Microsoft Azure Consumption Commitment (MACC).** A contract to spend a set amount on Azure over a term. Eligible usage and prepayment purchases such as reservations count toward it; usage covered by credits does not; "Azure benefit eligible" offers in the Microsoft Marketplace (renamed from Azure Marketplace in September 2025) count at 100% of their pre-tax price. A shortfall at the end of the term is billed; Azure sends commitment alerts at 90, 60 and 30 days.
- **Google Cloud commitments.** Agreements can include committed spend over a term, and qualifying third-party Google Cloud Marketplace purchases can draw it down.
- **Drawdown and shortfall risk.** The analyst projects each commitment's end-of-term position. A \$9.0M MACC runs for 36 months, February 2025 to January 2028. After 20 months (to September 2026), eligible consumption is \$4.6M. At the current eligible run-rate of \$260k a month, the remaining 16 months add \$4.16M, for \$8.76M and a \$0.24M shortfall. Closing it needs \$4.4M ÷ 16 = \$275k a month, \$15k more than today. A migration planned for January 2027 adds \$30k a month of eligible usage for the last 13 months (\$0.39M), which closes the gap if it lands on time. Report the projection, the migration dependency and the date by which Procurement must act.
- **The judgment call.** Optimization reduces drawdown. That is no reason to keep waste, but it is a reason to warn Procurement early, so a shortfall is negotiated, or covered by eligible marketplace purchases the company needs anyway, rather than discovered in the last quarter. Read the shortfall clause before you present a savings plan that cuts committed spend.

## 47a.4 The cost metrics, precisely

Every cloud reports several "costs" for the same usage. They differ in three ways: whether commitment fees appear when paid or spread over the usage they cover, whether negotiated discounts are included, and whether credits are netted. Using the wrong one is the most common reason two analysts disagree about the same month.

### AWS

| Metric | What it is | Where it comes from in CUR 2.0 | Use it for |
|---|---|---|---|
| Public on-demand (list) | Usage at public on-demand rates | `pricing_public_on_demand_cost` | Savings baselines; "what would this cost with no discounts?" |
| Unblended | Rate × usage per line. Commitment fees appear when charged (upfront fees on the purchase date, recurring fees as billed); negotiated discounts as their own negative lines or in the discount columns | `line_item_unblended_cost` | Matching the bill line by line |
| Net unblended | Unblended after discounts | `line_item_net_unblended_cost`, present only when the account has a discount in the period | Invoice reconciliation after discounts; the cash view |
| Amortized | Upfront and recurring commitment fees spread over the usage they cover, with the unused part shown separately | Built per line item type: `savings_plan_savings_plan_effective_cost` on SavingsPlanCoveredUsage, `reservation_effective_cost` on DiscountedUsage, unused commitment on the RIFee and SavingsPlanRecurringFee rows (the full expression is in 47b.7) | Trends, showback, forecasting |
| Net amortized | Amortized after discounts | The `net_` versions: `savings_plan_net_savings_plan_effective_cost`, `reservation_net_effective_cost`, `line_item_net_unblended_cost` | Showback and chargeback after the negotiated discount; the usual forecasting basis |
| Blended | Rates averaged across the accounts in the consolidated billing family | `line_item_blended_cost` | Almost nothing; it hides which account benefited from a commitment |

Three details catch people. Cost Explorer's daily amortized view shows the unused portion of reservation fees on the first day of the month, a spike that is not usage. Cost Explorer's unblended view, grouped by charge type, separates discounts into their own lines, so a team's usage viewed alone looks undiscounted. And CUR 2.0 can carry discounts in two ways: in the `discount` map and `discount_total_discount` column, or, when the export includes manual discount compatibility, as separate line items (the two columns are then removed). Check which your export uses before you write a query that filters discount rows.

### Azure

Azure Cost Management offers two datasets for the same usage:

- **Actual cost** reconciles to the invoice. Reservation and savings plan purchases appear as rows with charge type `Purchase` (once if paid upfront, or as monthly installments), and usage covered by a commitment shows an effective price of zero.
- **Amortized cost** gives covered usage the prorated hourly cost of the commitment, adds `UnusedReservation` or `UnusedSavingsPlan` rows for unused hours, and leaves out the purchases.

Microsoft's documented savings estimate works on the amortized data: `UnitPrice` × `Quantity` (or, for savings plans, also `PayGPrice` × `Quantity` against retail prices) minus the summed `Cost`, which includes unused commitment. The FOCUS export carries both views in one row: `BilledCost` corresponds to actual cost and `EffectiveCost` to amortized cost.

### Google Cloud

The BigQuery export has hourly rows by SKU and project (and by resource in the detailed export):

- `cost`: cost under the applicable consumption model, including your negotiated discounts.
- `credits`: a repeated field of negative amounts with a `type`: the CUD types (`COMMITTED_USAGE_DISCOUNT` for resource-based CUDs; `COMMITTED_USAGE_DISCOUNT_DOLLAR_BASE` and `FEE_UTILIZATION_OFFSET` for spend-based CUDs in the old and new data models), sustained use discounts, contractual discounts, promotions and others (47b.5 lists all nine).
- **Cost plus credits** is what you pay. Summed by `invoice.month` over all cost types, including tax and adjustments, it ties to the invoice.
- `cost_at_list` and `cost_at_effective_price_default`: cost at list price and at your negotiated price under the default consumption model; the second measures savings under the new spend-based CUD model (47b.8).

There is no separate amortized dataset: CUD fees appear as their own SKUs while the term runs, with credits (or, in the new spend-based model, lower usage prices) on the covered usage, so the commitment is already spread across the months it covers. In the console, the Savings filter decides which credits and discounts are netted.

### FOCUS

FOCUS defines four cost columns, all in the billing currency:

- `ListCost`: list unit price × pricing quantity.
- `ContractedCost`: contracted unit price × pricing quantity. It includes negotiated discounts but not commitment discounts, and equals `ListCost` where no negotiated discount applies.
- `BilledCost`: the basis for invoicing, after all reduced rates and discounts but without amortization. From FOCUS 1.2, `BilledCost` summed by `InvoiceId` must match the invoice's payable amount, and it must be zero for charges whose payment a third party receives (marketplace transactions).
- `EffectiveCost`: amortized cost after all reduced rates and discounts, plus the applicable share of prepaid purchases. It is zero on `Purchase` rows that cover future charges and equals `BilledCost` for charges unrelated to others, such as credits.

Rows are classified by `ChargeCategory` (`Usage`, `Purchase`, `Tax`, `Credit`, `Adjustment`), `ChargeClass` (`Correction` for a correction to a previous period, otherwise null), `ChargeFrequency` (`One-Time`, `Recurring`, `Usage-Based`), `PricingCategory` (`Standard`, `Dynamic`, `Committed`, `Other`) and, for commitment-related usage, `CommitmentDiscountStatus` (`Used` or `Unused`). One aggregation rule prevents double counting: when you sum `ListCost` or `ContractedCost`, exclude either the purchase rows or the usage they cover, because both carry the commitment's value. This book excludes the purchase rows.

### Which metric answers which question

| Question | Use | Do not use |
|---|---|---|
| Does our data tie to the invoices? | AWS unblended (or net unblended) over all line item types, including purchases, tax, credits and refunds; Azure actual cost, plus the support charges, taxes and credits Cost Management leaves out (47b.6); Google cost plus credits by `invoice.month` over all cost types; FOCUS `BilledCost` by `InvoiceId` | Amortized cost |
| What did a team consume (showback, chargeback)? | Net amortized cost or `EffectiveCost` | Unblended: an upfront purchase lands on whichever account bought it |
| Is spend trending up or down? | `EffectiveCost` per day, excluding tax, credits and one-time charges | Billed cost, which jumps with purchases |
| How much do commitments save? | Effective savings rate, utilization and coverage (47b.10, 47e.2) | Differences in unblended cost |
| What would this cost with no discounts? | `ListCost`, public on-demand cost, `cost_at_list` | Net metrics |
| How much did the negotiated agreement save? | `ListCost − ContractedCost` | `EffectiveCost` alone |
| How much cash leaves this month or quarter? | `BilledCost`, actual cost, unblended including purchases | Amortized cost |
| What goes into the budget and forecast? | Net amortized cost or `EffectiveCost`, plus a separate cash line for purchases | A single blended number |
| What should finance accrue? | Billed basis for usage, plus the accounting amortization schedule for prepaid purchases | The amortized dashboard total without checking the schedule |

### Worked example: one commitment purchase through every metric

Assumptions (fictional, separate from the running totals): the \$87,600 one-year, all-upfront Compute Savings Plan from 47a.3, bought on 1 September 2026, so September's share of the commitment is \$7,200. The plan covers usage worth \$9,500 at public on-demand rates; at the plan's rates that usage costs \$6,840 (28% below on-demand), so \$6,840 of the commitment is used and \$360 is not: 95% utilization. Other usage costs \$2,500 on demand, and the private pricing agreement takes 5% off it (−\$125). For visible arithmetic, the private discount applies only to that on-demand usage, and there are no taxes or credits.

| Metric (AWS) | September | How it is built |
|---|---|---|
| Public on-demand (list) | \$12,000 | 9,500 covered + 2,500 on-demand |
| Unblended, before the negotiated discount | \$90,100 | 87,600 upfront fee + 9,500 covered usage − 9,500 Savings Plan negation + 2,500 on-demand; the −\$125 discount is its own line |
| Net unblended | \$89,975 | 90,100 − 125 |
| Amortized | \$9,700 | 6,840 covered at plan rates + 360 unused + 2,500 on-demand; the upfront fee is replaced by its amortization |
| Net amortized | \$9,575 | 9,700 − 125 |

The same month as FOCUS rows. The unused row's `ListCost` and `ContractedCost` are zero here, which lets the FOCUS savings rate net out unused commitment; check how your provider fills them before relying on it.

| Row | `ChargeCategory` | `PricingCategory` / `CommitmentDiscountStatus` | `ListCost` | `ContractedCost` | `BilledCost` | `EffectiveCost` |
|---|---|---|---|---|---|---|
| Savings Plan purchase | Purchase (one-time) | Standard / null | 87,600 | 87,600 | 87,600 | 0 |
| Covered usage | Usage | Committed / Used | 9,500 | 9,500 | 0 | 6,840 |
| Unused commitment | Usage | Committed / Unused | 0 | 0 | 0 | 360 |
| On-demand usage | Usage | Standard / null | 2,500 | 2,375 | 2,375 | 2,375 |
| All rows | | | 99,600 | 99,475 | 89,975 | 9,575 |
| Excluding the purchase row | | | 12,000 | 11,875 | 2,375 | 9,575 |

Read it this way. `BilledCost` over all rows (\$89,975) equals net unblended cost: September's invoices (AWS charges an all-upfront purchase immediately, on its own invoice). `EffectiveCost` (\$9,575) equals net amortized cost: what the consuming team is shown and what the trend and the forecast use. List minus effective (\$2,425, 20.2% of list) is the total saving: \$125 from the negotiated discount, \$2,300 from the commitment (\$9,500 − \$6,840 − \$360 unused). The FOCUS effective savings rate on usage rows, (`ContractedCost` − `EffectiveCost`) ÷ `ContractedCost`, is \$2,300 ÷ \$11,875 = 19.4%; the FinOps Foundation's version, net commitment savings over on-demand-equivalent spend, is \$2,300 ÷ \$12,000 = 19.2%. Summing `ListCost` over all rows (\$99,600) counts the commitment twice.

**The same economics on Azure.** A one-year reservation bought for \$87,600 upfront with the same coverage. The actual-cost view for September shows the \$87,600 purchase, covered usage at zero and other usage at \$2,375 (Azure puts negotiated prices into the unit price, so there is no discount row): \$89,975. The amortized view shows covered usage at \$6,840, an `UnusedReservation` row of \$360 and other usage at \$2,375: \$9,575, with no purchase row. Paid monthly, the actual-cost view would show a \$7,300 installment (\$87,600 ÷ 12) every month, while the amortized view still shows \$7,200 for a 720-hour September; the difference evens out over the year.

**The same economics on Google Cloud.** A resource-based CUD of the same size, charged through its fee SKU as the term runs. The month's \$7,200 fee appears as its own SKU; covered usage appears at \$9,500 of `cost` with `COMMITTED_USAGE_DISCOUNT` credits of −\$9,500; other usage at \$2,375 of `cost` (negotiated pricing is already in `cost`) and \$2,500 of `cost_at_list`. Summing `cost` gives \$19,075, which counts both the covered usage and the fee; cost plus credits gives \$9,575. Under the new spend-based CUD data model, covered usage appears at the discounted price (\$6,840 of `cost`) and the \$7,200 fee row carries `FEE_UTILIZATION_OFFSET` credits of −\$6,840: `cost` sums to \$16,415, cost plus credits again to \$9,575. Gross `cost` depends on the data model; cost plus credits does not. Never report Google `cost` without its credits.

## 47a.5 Data timing: when numbers land and when a month is final

| | AWS | Azure | Google Cloud |
|---|---|---|---|
| Refresh | Data Exports (CUR 2.0, FOCUS) at least daily; Cost Explorer at least every 24 hours | 8–24 hours for EA and MCA, up to 72 hours for pay-as-you-go; estimates refresh six times a day; the Cost Details API every 4 hours | No delivery guarantee; usually within hours; a new export's backfill can take up to five days |
| The open month | Estimated, refreshed through the month | Estimated charges | Running totals; late usage can still arrive |
| Month close | The monthly invoice follows the end of the billing period; `bill_invoice_id` stays blank until the data is final; one-time fees such as upfront purchases are charged immediately, on their own invoice | The billing period usually closes up to 72 hours after it ends | An invoice should be available by the fifth business day of the next month |
| Late changes | The previous month's export can change during the first two weeks after month end; credits, refunds and support fees can change it after the invoice; support fees land around the 6th–7th | Usage charges can change until about the fifth day after the period ends | Late-reported usage can roll into the next invoice, so rows can carry a later `invoice.month` than their usage date |
| Day boundary | UTC | UTC | Billing reports use US Pacific Time days |

What this means for close and early-month reporting:

1. **Every month has three versions.** A *flash* on BD1 (estimates; the last day or two incomplete; support fees not yet posted), a *preliminary* actual around BD5 (Azure closed, Google's invoice available, AWS close to final) and a *final* actual around BD10. Label every number with its version and date: most "conflicting numbers" are two versions of the same month.
2. **Accruals come from the flash.** IT Finance needs a number before invoices are final (47a.3). Give them the flash plus explicit estimates for what has not landed, and record the true-up.
3. **Lock the month and log restatements.** Freeze final actuals on a fixed day (for example, BD10). Later changes (AWS restating within its two-week window, Google moving late usage into the next invoice month) become prior-period adjustments, not rewritten history; track the restatement percentage.
4. **Never compare partial periods with full ones.** Compare month-to-date spend per day with last month's over the same weekdays, without the last one to three days, which are incomplete on every cloud.
5. **Reconcile on the invoice basis; analyze on the usage basis.** Invoice keys (`invoice.month`, `bill_billing_period_start_date`, `InvoiceId`) answer "does it tie?"; usage dates (`usage_start_time`, `line_item_usage_start_date`, `ChargePeriodStart`) answer "what happened when?". They differ by late usage, corrections and credits. Google's reports make the same split: the billing period includes invoice-level charges such as taxes and adjustments; the charge period does not.

## 47a.6 The operating cadence

The job runs on five clocks, each with a fixed output, so stakeholders know when to expect what.

**Daily (15–30 minutes).** Confirm each cloud's data arrived (latest complete usage date, the AWS manifest, the Azure export's run status, the latest Google `export_time`). Review the native anomaly detectors and your own checks (daily spend by service against a baseline, unit cost per business transaction), and classify each signal as real, artifact or already known. Open a ticket with an owner for anything above materiality (47d.12–47d.13); nothing reaches leadership daily unless it is Sev1 under 47d.13.

**Weekly.** A Monday review of the last seven complete days against the forecast's daily phasing, the month's landing estimate (47c.2), the top ten movers by account and service, and open tickets. A 30-minute known-changes intake with Cloud Engineering: new items, changed dates, ramps, decommissions, planned commitment purchases (47c.3). Every other week, the savings pipeline with its owners. Output: a short landing note to IT Finance and the business unit leader whenever the landing estimate moves by more than materiality.

**Monthly close.** The sequence below. Outputs: the flash, the accrual file, the variance bridge and commentary, the executive summary, the reconciliation with the central team, the chargeback file, and a new row in the forecast accuracy log.

**Quarterly reforecast.** Rebuild the baseline from the latest actuals, refresh drivers with Business Planning, re-confirm every known change, re-weight the savings pipeline, review commitments (expiries in the next six months, coverage, utilization, planned purchases), and backtest. Output: the reforecast pack (full-year outlook against budget with a bridge and a range, the next quarter by month, the commitment plan, the risk register).

**Annual planning.** The budget for next year, built July–December for a calendar fiscal year (47c.8). Outputs: the budget submission by cloud, cost center and month, the assumptions register, the commitment and contract plan, and unit-cost targets for the largest applications.

**Ad hoc requests.** Between the clocks come quick-turn questions: what will the new region cost, why is Azure up this week. Answer in the monthly page's shape, shrunk: the answer and its number in one sentence, with basis and as-of date; the two or three drivers; a range or confidence; what would change it; the next step. Agree turnaround times (same day for leadership), log each request, and use the same definitions and method notes, so the ad hoc number reconciles with next month's report (impact notes in 47f.7).

### A typical month on one page

Business days (BD) count from the first working day of the new month; adjust to your company's close calendar.

| When | Task | Output | Data basis |
|---|---|---|---|
| BD1 | Flash for the month just ended | Total by cloud with a range and known gaps | Estimates; last days incomplete |
| BD1–BD2 | Month-end sweep: last-day spikes, purchases, credits | Anomaly log | Daily data |
| BD3 | Accrual estimate to IT Finance | Accrual file by cost center and GL account | Billed basis plus the amortization schedule |
| BD4 | Finance closes the books (example) | | |
| BD5 | Preliminary actuals; draft bridge reviewed with owners | Bridge, version 1 | Azure closed; Google invoice available |
| BD6–BD7 | AWS support fees post; update | Bridge, version 2 | |
| BD7 | Executive summary | One page | Preliminary actuals, labeled as such |
| BD8 | Reconciliation with the central IT FinOps team | Signed bridge between the two numbers | Agreed definitions (47c.9) |
| BD10 | Lock final actuals; log forecast accuracy; send the chargeback file | Final actuals, accuracy log row, chargeback file | Final |
| Around day 15 | AWS's window for prior-month changes ends; re-check the locked month | Prior-period adjustments, if any | |
| Mid-month | Landing estimate for the current month | Landing note if outside tolerance | Daily data |
| Last week | Next month's forecast frozen; reforecast inputs in quarter-end months | Forecast version | |

## 47a.7 Working with Cloud Engineering, IT Finance, Business Planning and the central IT FinOps team

| Partner | What they need from you | What you need from them | Typical friction and how to handle it |
|---|---|---|---|
| Cloud Engineering (the build team) | Early warning of cost changes; quick estimates for designs; credit for savings; little toil | Known changes with dates, ramps and owners; tags in infrastructure code; owners for anomalies; implementation of savings | "Finance is policing us." Use their units, keep the intake to 30 minutes a week, credit savings by name. |
| IT Finance | Accruals on time; numbers that tie to the ledger; cost centers and GL accounts; explanations above materiality; forecasts in their format | The close calendar, materiality thresholds, FX rates, GL mapping and chargeback policy | Billed versus amortized. Show the bridge between them every month until it is routine. |
| Business Planning | The cloud cost of business plans, and unit costs | Driver forecasts, the planning calendar, scenario assumptions | Drivers arrive late or change. Version them and publish cost sensitivity per 1% of volume. |
| Central IT FinOps team | Consistent numbers for the parent rollup, your scope mapping, your commitment needs, adherence to the enterprise tagging standard | Their data and definitions, cut-off dates, shared-cost allocation, how commitments are allocated | Two numbers for one thing. Agree the definitions in writing (47c.9) and reconcile on a fixed day. |
| Application owners | Their own cost and unit cost, early alerts, practical recommendations | Action on anomalies and savings, tagging, launch plans | Recommendations without context. Bring evidence and risk, not a list. |
| Leadership | Two or three numbers, risks with ranges, decisions to make | Decisions, and backing when owners do not act | Too much detail. One page; the appendix only on request. |

RACI for the recurring work (R responsible, A accountable, C consulted, I informed). It assumes commitments are bought centrally at the payer or billing-account level: the analyst recommends, IT Finance approves, the central team buys. If the business unit buys its own, the analyst also executes the purchase.

| Activity | FinOps analyst | Cloud Engineering | IT Finance | Business Planning | Central IT FinOps | Application owners | Leadership |
|---|---|---|---|---|---|---|---|
| Monthly and quarterly cloud forecast | A, R | C | C | C | I | C | I |
| Known-changes register | A, R | R | I | C | I | R | |
| Annual cloud budget submission | R | C | A | C | C | C | I |
| Month-end accrual estimate | R | | A | | I | | |
| Variance bridge and commentary | A, R | C | C | I | I | C | I |
| Tagging standard for the business unit | A, R | C | I | | C | C | I |
| Tag remediation in infrastructure code | C | A, R | | | I | R | |
| Anomaly triage | A, R | C | I | | I | C | |
| Anomaly resolution | C | R | | | I | A, R | I |
| Commitment purchase (recommend, approve, buy) | R | C | A | | R | I | I |
| Savings tracking and reporting | A, R | C | I | | I | C | I |
| Reconciliation with the parent rollup | A, R | | C | | R | | I |
| Executive summary | A, R | C | C | C | I | I | I |
| Chargeback journal entries | C | | A, R | | C | I | |

## 47a.8 A 30-60-90-day plan

**Days 1–30: learn the estate and reproduce the numbers.** Get read access to every billing scope (the AWS management account's billing views and Data Exports bucket, the Azure EA enrollment or MCA billing profile and its exports, the Google Cloud billing account and its BigQuery dataset). Map every account, subscription and project to an owner, a cost center, an environment and an application, and measure what is unmapped. Rebuild the last three months from the raw exports, tie them to the invoices (47b.6), rebuild the central team's number for the same months and write the bridge. Write the definitions page: performance metric (net amortized cost or `EffectiveCost`), cash metric (billed cost), FX, cut-offs, shared costs, and the flash, preliminary and final versions. Meet the cloud engineering lead, the IT Finance partner, Business Planning, the central team and the five largest application owners. Start the daily review and the known-changes register. *Deliverables:* data dictionary and mapping table, last month's reconciliation bridge, a first variance commentary, and the top ten risks and opportunities with dollar sizes.

**Days 31–60: build the operating system.** A driver-based forecast (47c.3) backtested on the last 12 months (47c.5); one full close on the calendar in 47a.6; a tagging compliance dashboard, the top 20 untagged items with owners, and shared-cost rules agreed with IT Finance and the central team; an anomaly playbook with thresholds, owners and escalation; a quantified savings pipeline. *Deliverables:* forecast with an accuracy log, the first executive summary finance uses without rework, an allocation baseline.

**Days 61–90: make it trusted.** The quarterly reforecast with a range (47c.4); a single-source-of-truth agreement signed with the central team and IT Finance (47c.9); unallocated cost reduced against an agreed target (for example, 22% to 12% of spend); the first optimization initiatives realized and reflected in the forecast; a commitment review; a maturity self-assessment against 47a.2 and a six-month roadmap. *Deliverables:* reforecast pack, signed agreement, savings tracker with realized savings, roadmap.

## 47a.9 Skills map and certifications

| Skill | What good looks like | How to practice |
|---|---|---|
| SQL on billing exports | Correct amortized, coverage, allocation and variance queries on CUR 2.0 (Athena), the Google export (BigQuery) and FOCUS, live in the interview | The recipes in 47b and the lab in 47g, or a small lab account (chapter 34) |
| Forecasting and modeling | Driver models with a clean assumptions tab and versions; knows run-rate, exponential smoothing, ARIMA and Prophet-style models and how each fails; measures WAPE and bias | Rebuild 47c's examples; *Forecasting: Principles and Practice* (free online); backtest two methods in pandas or a spreadsheet |
| Cloud pricing and commitments | Savings Plans, Reserved Instances, CUDs, MACC and EDP; break-even and effective savings rate at a whiteboard | 47e.2 and the example in 47a.4 |
| Accounting basics | Accruals, prepaid amortization, cash versus P&L, cost centers and GL accounts, used correctly | 47a.3 |
| Allocation governance | Tag keys, enforcement and shared-cost rules | Write a tagging policy for a fictional three-cloud estate (47d) |
| BI, communication and influence | One dashboard per audience; two or three numbers, drivers, risks and asks on one page; owners act because of data, credit and convenience | AWS Cloud Intelligence Dashboards or the FinOps toolkit's Power BI reports; rewrite last month's dashboard as five sentences; STAR stories (chapter 38) |

**Certifications.** The FinOps Foundation's catalog (learn.finops.org) in 2026:

| Certification | Price | Notes | Fit for this job |
|---|---|---|---|
| FinOps Certified Practitioner | \$500 (course and exam) | Valid for 24 months | The baseline credential and the Framework vocabulary |
| FinOps Certified FOCUS Analyst | \$400 | Online, no prerequisites | The most direct match for multi-cloud data work |
| FinOps Certified Professional | \$500 | Requires Practitioner or Engineer plus six months of experience | After six months in the role |
| FinOps Certified Engineer | \$500 (\$325 exam only) | Engineering and optimization depth | If the job leans toward optimization |
| FinOps Certified: AI Value | \$500 | Successor to the FinOps for AI course | When AI spend is material |
| FinOps Certified: Technology Value | \$500 | Launched June 2026 | For value and unit-economics conversations |
| FinOps for Containers | \$250 | Kubernetes allocation | If much of the spend runs on Kubernetes |

A sensible order is Practitioner, FOCUS Analyst, then Professional. A finance candidate gains more from a foundational cloud certification; an engineering candidate, from a short accounting course.

## 47a.10 Questions to expect

1. **"Walk me through your month-end close."** Flash on BD1, accrual on BD3, preliminary bridge on BD5, summary on BD7, reconciliation on BD8, lock on BD10, each date tied to when the clouds' data becomes final (47a.5, 47a.6).
2. **"Unblended or amortized: which do you show a team?"** Net amortized (`EffectiveCost`), which charges each team for the commitment it consumed; billed cost is for cash and invoice reconciliation. In 47a.4's example the same month is \$89,975 billed and \$9,575 effective.
3. **"Your forecast missed by 6%. What happened?"** Split the miss into rate, usage, mix and timing (47c.6), code each driver, and fix the process that let the largest through, usually a known change that never reached the intake.
4. **"How does a migration enter the forecast?"** As a known change with an owner, a start date, a ramp, a steady state, a double-running period and a decommission date with its own owner, weighted by confidence (47c.3).
5. **"The central team reports \$2.65M; you report \$2.55M."** Bridge it line by line (metric, FX, scope, shared costs, cut-off), then agree the definitions in writing so the bridge shrinks (47c.9).
6. **"How do you budget a \$1M upfront commitment?"** As a prepaid asset: the P&L budget carries the amortization, the cash plan carries the payment, consuming teams are charged through amortized cost, and paying upfront at all must beat the cost of capital (47c.8).
7. **"A team's spend is up 15% month over month. Trend or noise?"** Per day first, then persistence, breadth, driver backing, one-off charges and data lag; then decide its shape and how it enters the forecast (47c.7).
8. **"Which savings would you go after first?"** Rank by expected net savings over effort; clean up usage before buying commitments; check consumption commitments before cutting committed spend (47e.10).
9. **"How do you know a saving was realized?"** Against a counterfactual chosen before the change, such as the old unit cost × actual volume, never against last month's bill (47e.9).
10. **"What would you do in your first 30 days?"** Reproduce and reconcile the numbers, map every dollar to an owner, write the definitions page, and bring a top-ten list of risks and opportunities with dollar sizes (47a.8).

**Interview line:** *"I run cloud spend as a finance process on an engineering data pipeline: written definitions, net amortized cost for performance and billed cost for cash, a driver-based forecast that carries engineering's changes before they reach the bill, a monthly bridge in rate, usage, mix and timing, and one page built on the two or three numbers leadership will decide on."*

## Sources

- [FinOps Foundation: The 2026 FinOps Framework](https://www.finops.org/insights/2026-finops-framework/) (definition, domains, renamed capabilities, Executive Strategy Alignment; 19 March 2026)
- [FinOps Foundation: Forecasting](https://www.finops.org/framework/capabilities/forecasting/), [Budgeting](https://www.finops.org/framework/capabilities/budgeting/), [Planning & Estimating](https://www.finops.org/framework/capabilities/planning-estimating/), [Invoicing & Chargeback](https://www.finops.org/framework/capabilities/invoicing-chargeback/) and [KPIs & Benchmarking](https://www.finops.org/framework/capabilities/kpis-benchmarking/) capabilities (accessed 2 October 2026)
- [FinOps Foundation: Maturity model](https://www.finops.org/framework/maturity-model/) and [FinOps Scopes](https://www.finops.org/framework/scopes/) (accessed 2 October 2026)
- [FinOps Foundation: State of FinOps 2026](https://data.finops.org/) (reporting lines, AI spend; 19 February 2026) and [certification catalog](https://learn.finops.org/) (prices and prerequisites; accessed 2 October 2026)
- FOCUS specification v1.2: [BilledCost](https://focus.finops.org/docs/specification/v1-2/columns/cost-and-usage/billed-cost/), [EffectiveCost](https://focus.finops.org/docs/specification/v1-2/columns/cost-and-usage/effective-cost/), [ListCost](https://focus.finops.org/docs/specification/v1-2/columns/cost-and-usage/list-cost/) and [ContractedCost](https://focus.finops.org/docs/specification/v1-2/columns/cost-and-usage/contracted-cost/); [column definitions in the specification source](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec/tree/v1.2/specification/columns) (accessed 2 October 2026)
- [AWS Cost Explorer: advanced options and cost metrics](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-advanced.html) (daily amortized view, discounts by charge type; accessed 2 October 2026)
- AWS Data Exports: [line item](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-line-item.html), [bill](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-bill.html), [discount](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-discount.html) and [pricing](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-pricing.html) columns; [export delivery](https://docs.aws.amazon.com/cur/latest/userguide/dataexports-export-delivery.html) (accessed 2 October 2026)
- [AWS Billing: viewing your bill](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/getting-viewing-bill.html) (monthly invoices; one-time fees charged immediately; accessed 2 October 2026)
- Microsoft Learn: [reservation costs and usage](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/understand-reserved-instance-usage-ea), [savings plan cost reports](https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/utilization-cost-reports), [understand Cost Management data](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-cost-mgt-data), [track a Microsoft Azure Consumption Commitment](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/track-consumption-commitment) and [FOCUS cost and usage details schema](https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus) (accessed 2 October 2026)
- Google Cloud: [standard usage cost export schema](https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery-tables/standard-usage), [billing cycles](https://docs.cloud.google.com/billing/docs/how-to/billing-cycle), [Cloud Billing reports](https://docs.cloud.google.com/billing/docs/how-to/reports) and [spend-based CUD data model](https://docs.cloud.google.com/docs/cuds-multiprice-datamodel) (accessed 2 October 2026)
- [Google Cloud Marketplace](https://cloud.google.com/marketplace) (Marketplace purchases drawing down Google Cloud commitments; accessed 2 October 2026)
