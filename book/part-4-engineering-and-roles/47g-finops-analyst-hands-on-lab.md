# 47g. A hands-on FinOps analyst lab

> **What you need to be able to say:** what the lab's synthetic multi-cloud data contains and why each planted feature is there; how to run its eight commands and read their output; the method behind each analysis (a forecast with drivers and a backtest, a volume, mix and rate bridge, a robust anomaly detector with triage, allocation from the hierarchy up, commitment metrics and sizing, counterfactual savings scored against ground truth, the executive summary); the expected results; twelve exercises mapped to a representative multi-cloud FinOps analyst job description (anonymized), with answers; and how to extend the lab. Chapters 47a–47f explain the concepts; this chapter is where you practice them with numbers you can check.

## 47g.1 What the lab is and how to run it

The lab is one Python file, `labs/finops-analyst/finops_lab.py`, using only the standard library of Python 3.10 or later. It generates 18 months of daily, FOCUS-like cost data (1 April 2025 to 30 September 2026) for a fictional business unit on AWS, Microsoft Azure and Google Cloud, and runs the analyses a FinOps analyst is hired to do. "Today" is early October 2026: September is the month just closed. The business unit is separate from, and smaller than, the running example of 47a and 47c.

```bash
cd labs/finops-analyst
python3 finops_lab.py generate          # writes data/ (24,842 cost rows, about 10 MB)
python3 finops_lab.py forecast          # 12-month forecast, backtest, full-year outlook
python3 finops_lab.py variance          # budget vs forecast vs actual for September, with a bridge
python3 finops_lab.py anomalies         # detector, triage, precision and recall, threshold sweep
python3 finops_lab.py allocation        # tag compliance, unallocated cost, shared costs, showback
python3 finops_lab.py commitments       # coverage, utilization, ESR, renewal sizing
python3 finops_lab.py savings           # projected vs realized vs true savings, pipeline
python3 finops_lab.py summary           # the one-page executive summary
```

Every analysis takes `--data` (default `data`) and `--month` (default `2026-09`); `generate` takes `--out` and `--seed` (default 42). Two runs with the same seed produce byte-identical files, and every number in chapters 47d–47g comes from seed 42. The whole sequence runs in a few seconds (about 4 on a 2026 laptop). The lab's README lists every file and column and shows the full expected output.

Each analysis is a `compute_*` function that returns data and a `cmd_*` function that prints it, with the method in the docstring, so you can call them from your own scripts:

```python
import finops_lab as f
D = f.Data("data")                      # loads the CSV and builds daily series per sub-account and service
V = f.compute_variance(D, "2026-09")    # the same numbers the variance command prints
print(V["bridge"])
```

## 47g.2 The synthetic data and why it looks the way it does

### The business unit

Thirteen sub-accounts exercise the allocation hierarchy of 47d.1: eight belong to one application, two are shared by several teams (so tags decide), and three are shared pools.

| Sub-account | Provider | Kind | What runs there |
|---|---|---|---|
| aws-management | AWS | shared (commitments and governance) | AWS Config; owns the Compute Savings Plan; a one-time marketplace subscription in September 2026 |
| aws-payments-prod | AWS | single | The payments API: EC2, RDS, S3, CloudWatch, data transfer |
| aws-payments-nonprod | AWS | single | Development and test for payments |
| aws-data-platform-prod | AWS | multi | The claims-analytics platform on EMR, EC2 and S3, being migrated |
| aws-shared-network | AWS | shared (network) | NAT gateways, Transit Gateway, public IPv4 addresses |
| aws-ml-sandbox | AWS | multi | GPU experiments, notebooks, model-inference trials |
| az-crm-prod | Azure | single | The customer portal: VMs and Windows licenses, SQL Database, storage, Log Analytics, App Service |
| az-crm-dev | Azure | single | Development for the customer portal |
| az-security-shared | Azure | shared (security) | Defender for Cloud, Sentinel, Key Vault |
| az-ai-assistant-prod | Azure | single | The AI assistant: model tokens, AI Search, App Service |
| gcp-analytics-prod | Google Cloud | single | BigQuery, Compute Engine, Cloud Storage, and Dataproc from July 2026: the migration target |
| gcp-analytics-dev | Google Cloud | single | Development analytics |
| gcp-docai-prod | Google Cloud | single | Document intelligence: Gemini API, Cloud Run, Cloud Logging |

Total amortized cost grows from \$837,455 in April 2025 to \$1,234,195 in September 2026.

### The cost rows

`focus_costs.csv` has 31 columns named after FOCUS (the README lists them), including `ChargeCategory` (Usage, Purchase, Credit), `PricingQuantity`, the four cost columns, the `CommitmentDiscount*` columns and `Tags` as JSON. It is FOCUS-like, not FOCUS-conformant: a subset of columns, one currency, no tax and no invoice identifiers.

Commitment-covered usage follows the amortized pattern of 47a.4. Two rows for the data platform's EC2 on 1 April 2025:

| Row | PricingQuantity | ListCost | ContractedCost | EffectiveCost | BilledCost | CommitmentDiscountStatus |
|---|---|---|---|---|---|---|
| On demand | 10,080.14 hours | \$2,016.03 | \$1,895.07 | \$1,895.07 | \$1,895.07 | (empty) |
| Covered by the Savings Plan | 15,304.11 hours | \$3,060.82 | \$2,877.17 | \$2,014.02 | \$0.00 | Used |

ContractedCost applies AWS's 6% negotiated discount; the covered row's EffectiveCost applies the plan's 30% discount and its BilledCost is zero, because the fee is billed separately: a Purchase row on the first of each month with BilledCost equal to the fee (\$158,400 for a 30-day month at \$220 an hour) and EffectiveCost zero. Unused commitment appears as rows with `CommitmentDiscountStatus = Unused`. September 2026 breaks down like this:

| ChargeCategory | EffectiveCost (amortized) | BilledCost (invoice) |
|---|---|---|
| Usage | \$1,198,195 | \$1,032,538 |
| Purchase | \$48,000 | \$213,658 |
| Credit | −\$12,000 | −\$12,000 |
| **Total** | **\$1,234,195** | **\$1,234,195** |

The totals agree in September because the commitment fees billed (\$165,658) equal the commitment cost amortized into usage; in earlier months they differ (exercise 12).

### What is planted, and why

| Feature | Why it is there | Where it shows up |
|---|---|---|
| Weekday profiles (production, non-production at 40% at weekends, batch, research) | A month's total depends on its weekdays; detectors must compare like days | Forecast, anomalies, exercise 8 |
| Yearly seasonality (payments peaks in November and December) | Seasonal indices need 13+ months of history | Forecast, savings counterfactuals |
| Growth from 0.3% to 6% a month (the AI assistant fastest) | Trend estimation and AI risk | Forecast, variance, summary |
| Storage priced per GB-month | The same data costs more per day in short months | Forecast, savings |
| A Compute Savings Plan at \$220 an hour shared across four accounts | Coverage, utilization, cost shifts between teams, renewal sizing | Commitments, savings, 47d.6 |
| An Azure VM reservation that ends on 31 August 2026 and is not renewed | The classic rate variance that looks like a usage spike | Anomalies (A8), variance, commitments |
| A Google resource-based CUD; negotiated discounts (AWS 6%, Google 4%) | Usage-based commitment metrics; ListCost and ContractedCost differ, so ESR definitions differ | Commitments |
| A migration from AWS to Google Cloud: build-out from 1 July, AWS compute off on 1 November, storage deleted on 1 December | Double-running, a known change the statistical model cannot see, Savings Plan waste after the switch-off | Forecast, variance, summary |
| Tags with deliberate violations and remediation dates; untagged storage | Strict compliance against lenient allocation; the hierarchy fallback | Allocation |
| Seven injected anomalies, one data-lag artifact, one change below the dollar threshold, three planned events | A scored detector: precision, recall, triage | Anomalies |
| Four implemented initiatives (one over-delivers, one ramps, one decays) and five pipeline opportunities | Counterfactual savings, decay, probability-weighted savings in the forecast | Savings, forecast |
| Migration credits (\$12,000 a month, July–September 2026), a \$3,000 service credit, a \$48,000 one-time marketplace charge | One-time items and credits belong outside the run-rate | Variance, anomalies, summary |
| A 2026 budget built from October 2025 data with the old migration date (1 September), an AI growth cap of 3% a month and a 3% efficiency target | A budget is a plan made with old information | Variance, summary |
| Daily business volumes (transactions, conversations, sessions, claims, documents) | Unit costs and unit-based counterfactuals | Anomalies, savings |

`ground_truth.json` lists the injected events and, for each initiative, the true monthly saving, computed by regenerating the data with that initiative switched off (same random draws) and differencing the totals. The analyses read it only to print the "Truth" columns and the scores.

## 47g.3 The methods

### forecast

Per series (sub-account × service), using only data up to the forecast date: a weekday profile from the last 12 weeks (the median ratio of each weekday to its week's mean); a level equal to the median of the last 28 weekday-adjusted days; a monthly trend equal to the median month-over-month change of the last six weekday-balanced monthly levels, clipped to between −4% and +8% and damped by 0.97 a month; and a yearly index from a 2 × 12 centered moving average, used only where 13 months of history allow it and the index differs from 1 by at least 4%. Storage, billed per GB-month, is fitted on a constant-month basis (daily cost × days in the month ÷ 30.4375) and converted back: otherwise its daily cost swings 3% between 30- and 31-day months and 11% into February, and a median of month-over-month changes can get the sign of its growth wrong.

Drivers then replace or adjust the statistical forecast: the migration scope is forecast from the plan (the target's pre-migration baseline with 1% organic growth plus the build-out increment, measured from the data once the ramp is complete; the AWS source switched off at its dates; the Savings Plan pool recomputed without the source's EC2, which is where unused commitment appears); the Savings Plan renewal is applied at the size `commitments` recommends; calendar one-time items and contracted credits are added; and pipeline savings enter at monthly saving × probability from their start dates.

The backtest re-runs the forecast from six month-ends (March to August 2026) and compares one- and three-month-ahead forecasts of recurring usage with actuals, for a naive model, the statistical model and the model with drivers. The forecast's range is ±1.28 standard deviations of the backtest's percentage errors, widened with the horizon. 47c.2–47c.5 and 47f.5 explain the reasoning; 47e.13 the savings layer.

### variance

The forecast for the month is re-made from the day before the month began, so the comparison is fair. Each series' usage is measured at list prices (L) and its effective rate as EffectiveCost ÷ ListCost (e), with the forecast rate from the 28 days before the month. Volume is the change in total L at the forecast's average rate, mix the shift of L between series with different rates, and rate the change in e on actual volume; the three add up exactly to the usage variance. Unused commitment, one-time charges, credits and unrealized pipeline savings are separate lines. The budget comparison is by budget line, with a materiality flag at the larger of \$10,000 and 5%. One subtlety shows in the output: on Savings Plan accounts, extra usage at the margin is all on demand, so part of what the decomposition calls rate is volume.

### anomalies

The detector of 47d.11: the median of the same weekday over the previous six weeks, a MAD-based spread floored at 5% of the median, three conditions (z ≥ 4, +25%, +\$500), flagged days merged into events across gaps of up to two days, attribution to usage, rate or one-time, triage (planned if on the calendar before detection; a data artifact if a one-day spike follows a drop and the two-day sum is normal; provisional if newer than the provider's latency), severity from cost so far plus 30 days of the latest excess if still running, and routing by the account map. A second pass runs on cost per conversation and per thousand transactions. The threshold sweep re-runs everything with four rules.

### allocation

Hierarchy first, then tags (47d.1): shared sub-accounts go to their pool, credits to the account's owner, then the normalized `application` tag, then the single-application account's default, otherwise unallocated. Compliance is strict and cost-weighted; shared pools are split in proportion to direct cost, and the network pool under all four methods.

### commitments

For the month: per commitment, the billed fee, amortized cost, used and unused amounts, utilization, coverage (contracted dollars for the Savings Plan, hours for the reservation and the CUD), waste and savings against contracted rates; the cost of the lapsed reservation at on-demand rates; and three savings rates per provider (FOCUS, and the FinOps Foundation's two options with the on-demand equivalent at list prices). For the Savings Plan renewal: projected daily eligible usage without the data platform for the year after expiry, its P5 and P30, the current plan's utilization after the switch-off, and a grid of hourly commitments with gross savings, unused commitment and net savings, from which the smallest commitment within 5% of the best net is recommended (47e.2). For the VM reservation: the 10th percentile of concurrent VMs over 30 days, with the saving net of unused hours.

### savings

For each implemented initiative, a counterfactual chosen before the change (pre-change unit cost × volume, the pre-change trend, the pre-change rate × quantity, or a license-per-VM-hour ratio), realized saving per month, the realization rate, a trend-method cross-check, a decay flag when the last full month falls below 75% of the best, and the true saving from the ground truth. Usage on the shared Savings Plan is valued through the plan: while the plan stays fully used, removing a dollar of covered usage saves a dollar at contracted rates, because the coverage moves to other accounts (47e.12). The pipeline shows monthly value, probability and expected value.

### summary

The page of 47f.3, assembled from the other analyses.

## 47g.4 Expected results at a glance

| Command | Headline results (seed 42) |
|---|---|
| forecast | One month ahead: WAPE 3.9% naive, 3.5% statistical, 1.7% with drivers; three months ahead: 10.1%, 8.4%, 3.6%. Next 12 months \$13.23M; October \$1.23M, November \$1.05M, December \$1.09M. Full-year 2026 outlook \$12.62M against a \$12.19M budget (+3.5%). Savings Plan utilization after the switch-off 96.5%, about \$5,656 a month unused |
| variance | September: budget \$1,036,400, forecast \$1,160,724, actual \$1,234,195 (+19.1% and +6.3%). Bridge from forecast: volume +\$294, mix −\$63, rate +\$25,241, one-time +\$48,000 |
| anomalies | 11 events; 6 confirmed after triage, all true (precision 100%, recall 100%); raw precision 54.5%; detection one to two days after start; the AI assistant's cost per conversation +68% on the worst day of a nine-day event; the savings decay is not caught |
| allocation | Tag compliance 83.6%; unallocated 0.69%; allocation 83.9% by tag, 2.8% by account default, 13.5% shared; the network pool split four ways |
| commitments | Savings Plan 100% utilized at 56.2% coverage; reservation lapsed (+\$23,040 in September); ESR (FOCUS) 9.6% AWS, 0.0% Azure, 1.9% Google, 5.7% overall; renewal at \$210 an hour; 240 VMs for the new reservation, about \$27,900 a month net |
| savings | Realized \$375,704 of \$440,833 projected in 2026 (85%) against a true \$359,657; run-rate \$60,417 a month; INIT-02 at 64% and decaying; pipeline \$55,500 a month, \$43,950 expected |
| summary | The page in 47f.3 |

## 47g.5 Twelve exercises mapped to the job description

Each exercise names the responsibility it practices (paraphrased from the job description decoded in 47a.1), what to do, and the answer for seed 42.

**1. Track actual spend.** Reproduce September's total and split it into usage, one-time charges and credits, amortized and billed. *Answer:* the table in 47g.2; billed purchases of \$213,658 are the \$48,000 subscription plus \$165,658 of commitment fees. Explain why the totals agree this month.

**2. Visibility by account, service, environment and application.** Allocate September by the `application` tag alone, then after the alias table, then with the account map. *Answer:* unallocated cost is \$222,285 (18.0%), then \$137,104 (11.1%), then \$8,495 (0.69%). Name what each step fixed (the invalid `payments` value; untagged shared network and storage in single-application accounts).

**3. Improve tagging.** Find the smallest change that takes Tagging Policy Compliance from 83.6% above the 90% first target. *Answer:* correct `application=payments` to `payments-api` on aws-payments-nonprod, 7.1% of taggable cost: compliance becomes 90.7%. Then write the IaC default that prevents a recurrence and the tag policy that would have rejected it.

**4. Allocate shared costs.** Compare the four splits of the \$53,802 network pool, then write a policy for the three pools that a team lead would accept. *Answer:* the AI assistant pays \$8,967, \$4,505, \$5,380 or \$538 depending on the method. A defensible policy: proportional for security and governance, usage-driven for the network once flow-log data exists, a fixed split on the purchase request for the marketplace subscription, shared cost on its own line, changes only at fiscal-year boundaries.

**5. Forecast across three clouds, with planned changes.** Run the forecast, then repeat it without drivers (`f.forecast_engine(D, D.last, f.date(2027, 9, 30), use_drivers=False)`) and compare. *Answer:* without drivers the next 12 months total \$16.15M instead of \$13.23M, \$2.9M higher, and November is \$1.215M instead of \$1.054M: the statistical model carries the Google Cloud build-out's growth forward and keeps the AWS platform running after its switch-off. This is why the job description wants planned changes in the forecast before they reach the bill.

**6. Defend the method.** Recompute MAPE, WAPE and bias for the one-month backtest (47f.12 exercise 7 has the six rows). Then remove the trend damping (set the default `phi` to 1.0 in `growth_multiplier`) and rerun. *Answer:* MAPE 1.63%, WAPE 1.68%, bias −0.91%. Without damping, the 12-month total rises by \$0.21M and September 2027 from \$1.190M to \$1.238M. Decide which version you would defend to a CFO (damping is conservative when growth rates come from a short history).

**7. Explain the variance in business terms.** Run `variance` and write three sentences on September for the CIO. *Answer:* compare yours with question 7 of 47f.10. It should give both comparisons (\$198k over budget, \$73k over forecast), split the budget gap into timing (\$117k), one-offs (\$48k and \$23k) and recurring (\$25k), and end with the year (+\$430k) and the decisions.

**8. Distinguish trends from noise.** January 2026 cost \$975,228 and February \$922,142, 5.4% less. Did spending fall? *Answer:* no. February has 28 days and 20 weekdays against 31 and 22; per day it cost \$32,934 against \$31,459, 4.7% more, and it contained the NAT spike. Rewrite the sentence a careless report would print.

**9. Identify anomalies and drive them to resolution.** Pick a rule for an alert budget of at most one false alert per quarter, then write the ticket and the postmortem for the forgotten GPU cluster (47d.13, 47d.15). *Answer:* over the roughly 16 months evaluated, the loose rule sends 10 false alerts (about two a quarter); the medium rule sends 2 (noise on the new Bedrock experiments) and also flags the savings decay on three weekends in July; the default sends none and misses the decay. Choose the default plus a run-rate test, or the medium rule, and say why. The cluster cost \$30,057 over 12 days and ran ten days after detection.

**10. Optimize commitments.** Recommend the Savings Plan renewal and the new VM reservation, with break-even and sensitivity. *Answer:* renew at about \$210 an hour (99.2% expected utilization, \$767,944 net a year), not at the \$305 optimum, because the net-savings curve is flat between them and daily data overstates the floor; buy 240 VMs for one year (P10 of concurrent VMs is 241), about \$27,900 a month net at 40% off, breaking even at 60% utilization. Then explain why overall ESR is only 5.7%.

**11. Track realized savings.** Run `savings`. Which counterfactual came closest to the truth for each initiative, and why? What would INIT-02 show measured on its own amortized cost? What do you do about INIT-02? *Answer:* the rate and ratio methods match the truth for INIT-03 and INIT-04, because they model exactly a price change and a license-per-VM-hour change; INIT-01's unit method is 10% high (\$118,716 against \$107,851) and its trend check 6% high; INIT-02, valued through the plan, shows \$141,835 against a true \$136,652, and \$111,866 on its own amortized cost (47e.12 explains each gap). For INIT-02, restore the schedules (OPP-02, \$12,000 a month at 80%) and put expiry dates on opt-outs.

**12. Reconcile and report.** Compute billed minus amortized cost for every month, explain the pattern, then rewrite the summary for the CFO and for engineering leadership. *Answer:* the difference is +\$480 in 30-day months, −\$672 in 31-day months, +\$2,784 in February and \$0 in September: the Azure reservation was paid in equal monthly installments of \$35,040, while amortized cost spreads it at \$1,152 a day, and it ended in August. The CFO version leads with the full-year outlook, cash (commitment fees, the prepaid subscription) and the accrual; the engineering version with the teams, the anomalies and the actions with owners.

## 47g.6 Extensions

**Redo the analysis in SQL.** Load the CSV files into a database and rebuild the numbers with the queries of 47f.12. This loader uses only Python's standard library and SQLite:

```python
import csv, sqlite3

con = sqlite3.connect("finops.db")
NUMERIC = {"PricingQuantity", "ListUnitPrice", "ContractedUnitPrice", "ListCost",
           "ContractedCost", "EffectiveCost", "BilledCost", "Budget"}
for table in ("focus_costs", "account_map", "budget"):
    with open(f"data/{table}.csv", newline="") as f:
        rows = csv.reader(f)
        header = next(rows)
        cols = ", ".join(f'"{h}" {"REAL" if h in NUMERIC else "TEXT"}' for h in header)
        con.execute(f"CREATE TABLE {table} ({cols})")
        con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(header))})",
                        ([float(v) if h in NUMERIC and v else v for h, v in zip(header, r)] for r in rows))
con.commit()
```

For DuckDB or BigQuery, use the engine's CSV loader and adapt the date and JSON functions (47b). Check that your SQL reproduces the Python results: compliance 83.6%, ESR 9.6%, 0.0% and 1.9%, the same 68 flagged anomaly days.

**Build a dashboard** with the five executive charts of 47f.4, each titled with its conclusion.

**Add a fourth provider:** an entry in `PROVIDERS` and `SUBACCOUNTS`, a few series in `SERIES` (a SaaS data platform is realistic: FOCUS 1.3 publishers include Snowflake and Databricks) and their budget lines in `ACCOUNT_MAP`; then check that every command still reconciles.

**Go hourly.** Generate hourly rows for the Savings Plan's eligible series and re-size the renewal. The floor falls (night-time troughs), and so does the recommended commitment; quantify by how much.

**Apply the plan as AWS does.** Replace the pro-rata Savings Plan split with AWS's rule (highest savings percentage first, then lowest Savings Plans rate) using different discounts per series, and see how the cost shifts of 47d.6 change.

**More.** Bill one provider in euros and separate FX in the bridge; re-cut the months to a 4-4-5 calendar (47a.3); add pod-level series and the three idle policies of 47d.7; replace the forecast model with exponential smoothing or a regression on drivers (keep the driver layer: no statistical model knows the switch-off date); change the seed or the injected sizes and watch precision, recall and the gap between realized and true savings.

## 47g.7 What the lab does not teach

The lab is clean where reality is messy. Real exports have late and restated rows, schema changes, currency, tax, refunds, support fees and marketplace invoices, and providers disagree with their own consoles (47b.11). The lab's engineering plan for the migration is exactly right, which flatters the driver model's backtest; real estimates miss. Its Savings Plan is shared pro rata by day, while AWS applies it hour by hour to the highest savings percentage first. Real anomalies and savings come without a ground-truth file, budgets are negotiated rather than generated, and owners push back. Use the lab to make the arithmetic and the method automatic, so that in the job your attention goes to the mess.

**Interview line:** *"I practiced the monthly cycle on eighteen months of synthetic three-cloud data: a forecast whose drivers cut three-month error from 8% to under 4%, a bridge that splits a 19% budget overrun into timing, one-offs and a rate change, a detector that found every planted spike with no false alerts after triage, allocation from 18% unallocated to under 1%, a renewal sized from the post-migration floor, and a savings tracker, scored against ground truth, that caught the decay the detector missed. I can show the code and redo any of it in SQL."*

## Sources

- FOCUS, [FinOps Open Cost and Usage Specification](https://focus.finops.org/) (column definitions; use cases for effective savings rate and commitment coverage; accessed 2 October 2026)
- FinOps Foundation, [Allocation](https://www.finops.org/framework/capabilities/allocation/), [Anomaly Management](https://www.finops.org/framework/capabilities/anomaly-management/), [Rate Optimization](https://www.finops.org/framework/capabilities/rate-optimization/), [Budgeting](https://www.finops.org/framework/capabilities/budgeting/) and [Forecasting](https://www.finops.org/framework/capabilities/forecasting/) capabilities (accessed 2 October 2026)
- AWS, [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/) (the NAT gateway and public IPv4 prices the lab uses) and [How Savings Plans apply to your usage](https://docs.aws.amazon.com/savingsplans/latest/userguide/sp-applying.html) (accessed 2 October 2026)
- Microsoft Learn, [FOCUS conversion rules](https://learn.microsoft.com/en-us/cloud-computing/finops/focus/convert) (how commitment purchase rows are populated; accessed 2 October 2026)
- The lab: `labs/finops-analyst/finops_lab.py` and its README in this repository (seed 42; outputs reproduced in chapters 47d–47g)
