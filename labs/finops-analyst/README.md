# FinOps analyst lab

A one-file lab for the work a multi-cloud FinOps analyst does every month: forecasting, variance analysis, anomaly detection, allocation, commitment management, savings tracking and executive reporting. It generates 18 months of synthetic, FOCUS-like daily cost data for a fictional business unit on AWS, Microsoft Azure and Google Cloud, with planted problems, and then runs each analysis with printed tables you can check by hand.

Chapter 47g of the book (`book/part-4-engineering-and-roles/47g-finops-analyst-hands-on-lab.md`) explains the data, the methods and the exercises; chapters 47c, 47d, 47e and 47f use the lab's numbers. This README is the companion to the code: for each analysis it gives the intuition, the algorithm as implemented (with function names, parameters and thresholds), the actual printed output from a run with seed 42, and how the same work is done on real billing data.

Everything is fictional: the company, accounts, prices and events. Unit prices are illustrative, except NAT gateway (\$0.045 per hour and per GB) and public IPv4 (\$0.005 per hour), which match published AWS us-east-1 prices in October 2026. The data imitates FOCUS columns but is not a conformant FOCUS dataset.

## Purpose

Three things the lab is for:

1. **Making the monthly cycle automatic.** Forecast, close, bridge, detect, allocate, size, track, report: eight commands whose numbers reconcile to the cent.
2. **Showing what each method gets wrong when the answer is known.** Every anomaly, saving and planned event is in `ground_truth.json`, so precision, recall and the gap between a measured and a true saving can be scored. A real analyst never has that file.
3. **Giving you code you can read and change.** Each analysis is a `compute_*` function that returns a dictionary and a `cmd_*` function that prints it; both can be called from your own scripts.

## Requirements

Python 3.10 or later, standard library only (`argparse`, `csv`, `json`, `math`, `random`, `statistics`, `datetime`, `collections`). No installation, no virtual environment, no network.

## Quick start

```bash
cd labs/finops-analyst
python3 finops_lab.py generate            # writes data/ (24,842 cost rows, about 10 MB)
python3 finops_lab.py forecast            # 12-month forecast, backtest, full-year outlook
python3 finops_lab.py variance            # budget vs forecast vs actual for September, with a bridge
python3 finops_lab.py anomalies           # detector, triage, precision and recall, threshold sweep
python3 finops_lab.py allocation          # tag compliance, unallocated cost, shared costs, showback
python3 finops_lab.py commitments         # coverage, utilization, ESR, renewal sizing
python3 finops_lab.py savings             # projected vs realized vs true savings, pipeline
python3 finops_lab.py summary             # the one-page executive summary (Markdown)
```

`python3 finops_lab.py --help` lists the subcommands; each subcommand has its own `--help`. `generate` takes `--out` (default `data`) and `--seed` (default 42). Every analysis command takes `--data` (default `data`) and `--month` (default `2026-09`, the month just closed; "today" is early October 2026). If `data/focus_costs.csv` is missing, the analysis commands exit with a message telling you to run `generate`.

The data is deterministic for a given seed: two runs produce byte-identical files. The whole sequence of eight commands ran in about 4 seconds on the laptop used for this README; `generate` is the slowest single step because it regenerates the data once per implemented initiative to compute the true savings.

| Command | What it prints | Book section |
|---|---|---|
| `generate` | Row count, file list, monthly amortized totals | 47g.2 |
| `forecast` | Rolling-origin backtest; MAPE, WAPE and bias for three models; the 12-month forecast by component with an 80% range; by provider; full-year outlook against budget; the Savings Plan after the decommission | 47c.2–47c.5, 47g.3, 47f.5 |
| `variance` | Budget vs forecast vs actual; FinOps Foundation accuracy and bands; by budget line with a materiality flag; the bridge; the top ten drivers with context from the analyst's own records | 47c.6, 47g.3 |
| `anomalies` | Every event with its triage label and the ground truth; precision and recall; time to detect; unit-cost anomalies; a threshold sweep; anomaly cost % by month | 47d.9–47d.12 |
| `allocation` | Tag compliance, unallocated cost, violations by cost, the allocation waterfall, the network pool under four methods, showback, the trend since October 2025 | 47d.1–47d.8 |
| `commitments` | Inventory with utilization, coverage, waste and savings; the cost of the lapsed reservation; three ESR definitions; Savings Plan renewal sizing with sensitivity; the VM reservation recommendation | 47e.1–47e.2 |
| `savings` | Projected vs realized per initiative with a trend cross-check, status, decay flag and the true saving; by month; the probability-weighted pipeline | 47e.9, 47e.12–47e.13 |
| `summary` | The one-page Markdown executive summary | 47f.1–47f.3 |

To use the analyses from your own code:

```python
import finops_lab as f
D = f.Data("data")                       # loads the CSV and builds daily series per sub-account and service
V = f.compute_variance(D, "2026-09")     # the same numbers the variance command prints
print(V["bridge"])
```

## The data

### How it is generated

`generate(out_dir, seed)` calls `generate_rows(seed)`, which simulates every day from 1 April 2025 to 30 September 2026 (548 days) for the 41 series in `SERIES`. A series is one sub-account, service and meter, built with `series_spec(...)`: a base daily quantity in April 2025 (`qty`), a unit `price`, a monthly `growth` rate, a weekday profile (`dow`, normalized to a mean of 1 in `DOW_N`), a yearly `season`, a `noise` level, flags for storage priced per GB-month and commitment eligibility (`sp`, `ri`, `cud`), an optional `start` date and a dated list of tag sets. The 41 series collapse into 39 sub-account-and-service keys because the three NAT and IPv4 meters all bill under Amazon VPC.

Each day's quantity is base × `growth_factor` × weekday factor × seasonal factor × a Gaussian noise draw floored at 0.5 × `initiative_multiplier` (implemented initiatives and the savings decay), plus `additive_list_usd` (injected anomalies and the planned load test, in list dollars per day) and, for the migration target, the build-out increment times `ramp`. Three series are derived: the Windows license meter follows VM hours, Azure OpenAI tokens equal conversations × tokens per conversation, and the drivers come from `simulate_drivers`. `price_multiplier` applies the one rate change (INIT-03). Storage series hold GB stored and the day's `PricingQuantity` is GB ÷ days in the month, so the same data costs more per day in February than in January.

Commitments come next. The Savings Plan is spend-based: the day's commitment (\$220 × 24) covers contracted usage worth commitment ÷ (1 − 30%) across the four EC2 series flagged `sp=True`, pro rata; the rest is on demand, and a shortfall is an `Unused` row. The Azure reservation and the Google CUD are usage-based on `hours_per_day`. `make_row` writes the amortized convention: covered usage has `EffectiveCost` at the committed rate and `BilledCost` 0; a `Purchase` row on the first of the month carries the fee in `BilledCost` with `EffectiveCost` 0. Credits, the one-time charge and the data-lag artifact (65% of one day's payments EC2 rows re-stamped to the next day) are added last.

`true_savings` regenerates the rows once per initiative with it switched off (the `off` argument) and differences the monthly totals. Every series, driver and migration increment has its own random stream (`random.Random(f"{seed}:series:{id}")` and the like), so switching one initiative off changes nothing else and the difference is exactly its company-level saving, including the Savings Plan coverage that moved to other accounts.

`build_budget` makes the budget last: the lab's own `forecast_engine` run as of 31 October 2025 to the end of 2026 with the migration's `budget_plan` dates (ramp from 1 September 2026, compute off on 1 December, storage deleted on 1 January 2027), AI growth capped at 3% a month, a 3% efficiency haircut from April 2026, no one-time items, rounded to \$100. That is how a planning team would have built it with the information of the time, which is why it is wrong in instructive ways.

### The files

| File | Contents |
|---|---|
| `focus_costs.csv` | 24,842 daily rows (24,784 of them `Usage`) from 1 April 2025 to 30 September 2026, 31 FOCUS-like columns: `BillingAccountId`, `BillingAccountName`, `BillingPeriodStart`, `BillingPeriodEnd`, `ChargePeriodStart`, `ChargePeriodEnd`, `ServiceProviderName`, `SubAccountId`, `SubAccountName`, `SubAccountType`, `RegionId`, `ServiceName`, `ServiceCategory`, `ChargeCategory` (Usage, Purchase, Credit), `ChargeClass`, `ChargeFrequency`, `ChargeDescription`, `PricingUnit`, `PricingQuantity`, `ListUnitPrice`, `ContractedUnitPrice`, `ListCost`, `ContractedCost`, `EffectiveCost`, `BilledCost`, `BillingCurrency`, `CommitmentDiscountId`, `CommitmentDiscountType`, `CommitmentDiscountCategory`, `CommitmentDiscountStatus` (Used, Unused or empty) and `Tags` as JSON |
| `business_metrics.csv` | Daily volumes per application: transactions (payments-api), conversations (ai-assistant), sessions (customer-portal), claims processed (claims-analytics), documents (doc-intelligence) |
| `budget.csv` | The 2026 budget by month, provider and budget line |
| `account_map.csv` | What each of the 13 sub-accounts is for: kind (single, multi, shared), default application, environment, cost center, owner, budget line, shared pool |
| `tag_standard.json` | Required keys, allowed values, case rule, sources of truth, key and value alias tables |
| `planned_changes.csv` | The change calendar: a load test, the migration, the annual renewal, two decommissions and the Savings Plan expiry, each with the date it was added |
| `commitments.json` | The AWS Compute Savings Plan, two consecutive Azure VM reservations (the second ends on 31 August 2026 and is not renewed), a Google resource-based CUD |
| `initiatives.json` | Four implemented initiatives with projected savings and measurement methods; five pipeline opportunities with probabilities |
| `ground_truth.json` | The injected anomalies, the data artifact, the below-threshold change, the planned events, the migration plan, the budget assumptions and the true monthly saving of each initiative. Used only for scoring |

### The three clouds and the fictional business unit

`PROVIDERS` holds one billing account per cloud (an AWS payer, an Azure MCA billing account, a Google Cloud billing account), its sub-account type (AWS Account, Subscription, Project), one region each and a negotiated discount: 6% on AWS, 0% on Azure, 4% on Google Cloud. `ContractedCost` is `ListCost` × (1 − negotiated), which is why the ESR definitions diverge in `commitments`. `LATENCY_DAYS` gives each provider's typical delay before a day's cost is visible (AWS 1, Azure 2, Google Cloud 1); triage uses it.

| Sub-account | Provider | Kind | What runs there |
|---|---|---|---|
| aws-management | AWS | shared | AWS Config; owns the Compute Savings Plan; a one-time marketplace subscription in September 2026 |
| aws-payments-prod, aws-payments-nonprod | AWS | single | The payments API (EC2, RDS, S3, CloudWatch, data transfer) |
| aws-data-platform-prod | AWS | multi | The claims-analytics platform (EMR, EC2, S3) being migrated to Google Cloud |
| aws-shared-network | AWS | shared | NAT gateways, Transit Gateway, public IPv4 addresses |
| aws-ml-sandbox | AWS | multi | GPU experiments, SageMaker notebooks, Bedrock inference trials from August 2026 |
| az-crm-prod, az-crm-dev | Azure | single | The customer portal (VMs, Windows licenses, SQL Database, storage, Log Analytics, App Service) |
| az-security-shared | Azure | shared | Defender for Cloud, Sentinel, Key Vault |
| az-ai-assistant-prod | Azure | single | The AI assistant (Azure OpenAI tokens, AI Search, App Service) |
| gcp-analytics-prod, gcp-analytics-dev | Google Cloud | single | BigQuery, Compute Engine, Cloud Storage and, from July 2026, Dataproc: the migration target |
| gcp-docai-prod | Google Cloud | single | Document intelligence (Gemini API, Cloud Run, Cloud Logging) |

Monthly amortized cost, as `generate` prints it:

```
Month    EffectiveCost (amortized)
-------  -------------------------
2025-04                   $837,455
2025-05                   $866,930
2025-06                   $851,235
2025-07                   $902,506
2025-08                   $898,310
2025-09                   $902,476
2025-10                   $943,799
2025-11                   $933,573
2025-12                 $1,012,170
2026-01                   $975,228
2026-02                   $922,142
2026-03                   $993,137
2026-04                   $971,297
2026-05                 $1,001,129
2026-06                   $969,746
2026-07                 $1,060,171
2026-08                 $1,126,668
2026-09                 $1,234,195
```

### What is planted, and where

Everything in this table is a constant near the top of `finops_lab.py`, so you can change it and watch the analyses respond.

| Planted feature | Where in the code | Dates and size | Which analysis is meant to see it |
|---|---|---|---|
| A1, NAT gateway data-processing spike | `INJECTED`, series `aws-net-natgb` | 10–15 February 2026, +\$2,385 list per day | anomalies |
| A2, late-arriving rows (data artifact) | `DATA_ARTIFACT`, series `aws-pay-ec2` | 65% of 3 March 2026 re-stamped to 4 March | anomalies (triage must reject it) |
| A3, runaway BigQuery query | `INJECTED`, series `gcp-dev-bq` | 22 April 2026, +\$4,000 | anomalies |
| A4, forgotten GPU cluster | `INJECTED`, series `aws-ml-ec2` | 18–29 May 2026, +\$3,104 per day | anomalies |
| A5, logging explosion | `INJECTED`, series `az-crm-la` | 7–11 July 2026, +\$1,794 per day | anomalies |
| A6, non-production schedules disabled (savings decay) | `initiative_multiplier`: `aws-nonprod-ec2` runs at 0.92 on weekdays and 0.70 at weekends from 1 July 2026 instead of 0.80 and 0.35 | July–September 2026 | savings (the detector is not meant to catch it) |
| A7, prompt change raised tokens per conversation | `generate_rows`: 27,000 tokens per conversation instead of 15,000 | 3–11 August 2026 | anomalies, including the unit-cost pass |
| A8, reservation expired, rates rose | `COMMITMENTS`: `ri-crm-vm-2025` ends 31 August 2026 and nothing replaces it | September 2026 | anomalies (a rate event), variance, commitments |
| A9, a small storage increase | `IMMATERIAL`, series `gcp-dev-gcs` | 9–12 June 2026, +\$120 per day | nothing: it must stay below the dollar threshold |
| PC-01, peak-season load test | `CALENDAR` (added 3 November 2025) and `additive_list_usd` (+\$2,000 per day) | 18–20 November 2025 | anomalies (triage: planned) |
| PC-02, the migration | `MIGRATION` (approved 20 February 2026): Google Cloud ramp 1 July to 15 September 2026, AWS compute off 1 November, storage deleted 1 December; increments of \$2,800 (BigQuery), \$1,100 (Dataproc) and \$600 (Cloud Storage) list per day | July 2026 onward | forecast, variance, commitments, anomalies (triage: planned) |
| PC-03, annual SIEM subscription through AWS Marketplace | `ONE_TIME` and `CALENDAR` (added 10 September, after the August forecast was made) | 15 September 2026, \$48,000 | variance, anomalies (triage: planned), summary |
| Migration credits and a service credit | `MIGRATION["credits"]`, `OTHER_CREDITS` | −\$12,000 in July, August and September 2026; −\$3,000 on 10 June 2026 | variance, allocation (credits follow the account) |
| INIT-01, RDS rightsizing | `initiative_multiplier`: `aws-pay-rds` × 0.82 | from 1 March 2026; projected \$14,000 a month | savings |
| INIT-02, non-production scheduling | `initiative_multiplier`: `aws-nonprod-ec2` and `az-dev-vm` × 0.80 on weekdays, × 0.35 at weekends | from 15 April 2026; projected \$40,000 a month | savings |
| INIT-03, S3 Intelligent-Tiering | `price_multiplier`: `aws-pay-s3` price falls 22%, ramping between days 30 and 60 | from 1 February 2026; projected \$8,000 a month | savings |
| INIT-04, Azure Hybrid Benefit | `generate_rows`: the license meter runs at 30% of VM hours | from 1 May 2026; projected \$11,500 a month | savings |
| Tag violations with remediation dates | The `T_*` tag sets and each series' dated `tags` list | `payments` for `payments-api` (never fixed); wrong case on CRM prod until 1 June 2026; missing `owner` on the data platform until 15 March; untagged ML sandbox until 15 January; missing cost center and owner on CRM dev until 1 May; `costcenter` misspelled on analytics dev (never fixed); storage and shared accounts never tagged | allocation |
| Weekday and yearly seasonality, growth, month-length effects | `DOW`, `SEASON`, each series' `growth` (0.3% to 4% a month; the AI assistant's tokens follow conversations growing 6% a month), `storage=True` | always | forecast, variance, exercise 8 |
| A budget built with old information | `BUDGET_ASSUMPTIONS` and `build_budget` | migration two months later than it happened, AI growth capped at 3%, 3% efficiency from April | variance, summary |

### Seeds and reproducibility

`--seed` (default 42) seeds every random stream by name, so changing the seed changes the noise but not the planted events. Two runs with the same seed give byte-identical files. All numbers in this README and in chapters 47d–47g are from seed 42. With `--seed 7` the detector again reaches 100% precision and 100% recall and, with that seed's noise, also flags the savings decay (7 of 7 labeled anomalies true); the savings tracker reads \$374,088 realized of \$440,833 projected against a true \$359,551.

## Forecasting

### Intuition

The question is "what will we spend next month, next quarter and next year, and how sure are we?". Most of cloud spend is recurring usage that moves slowly, so a statistical model of each series' recent level, weekly pattern and trend forecasts it well one month out. What no statistical model can see is the future that is already decided: a migration with a switch-off date, a commitment that expires, an annual renewal, savings that are booked but not yet implemented. The lab therefore forecasts in layers: statistics for the run-rate, drivers for what is known, and a backtest to prove the layers earn their keep against a naive benchmark.

### How the lab does it

`fit_series(vals, as_of, ...)` fits one daily series using only days up to `as_of`:

- a weekday profile `w` from the last 12 weeks: for each weekday, the median of that day's ratio to its week's mean, normalized to a mean of 1 (seasonal naive);
- a level: the median of the last 28 weekday-adjusted days (`level_days=28`), robust to a spike;
- a monthly growth rate `g`: the median month-over-month change of the last six weekday-balanced monthly levels from `monthly_levels`, clipped to between −4% and +8%, so one step change cannot become a trend;
- a yearly index `S` from a 2 × 12 centered moving average, only when 13 or more complete months exist and only for months whose index differs from 1 by at least 4%;
- for storage series (`per_month=True`), the fit is on a constant-month basis (daily cost × days in month ÷ 30.4375) and `predict` converts back.

`predict(fit, day)` returns level × `growth_multiplier(g, h)` × weekday factor × yearly index, where `growth_multiplier` damps the trend by `phi=0.97` a month so a 12-month horizon does not run away.

`forecast_engine(D, as_of, end, plan_key="actual", use_drivers=True, include_items=True, growth_overrides=None, renewal_hourly=None)` adds the components per month: `statistical` (the sum of the fits); `migration` (the Google Cloud target forecast from the plan's increments and ramp instead of its statistical extrapolation, the AWS source's EMR and S3 switched off at the decommission dates, and the Savings Plan pool recomputed with `sp_pool_cost` without the source's EC2, which is where unused commitment appears); `renewal` (the plan renewed at `renewal_hourly` after 31 January 2027); `known_one_time` and `known_credits` (calendar items added before `as_of`, with annual recurrence); and `savings` (each `PIPELINE` item at monthly × probability from its start date).

`backtest(D, origins)` re-runs the engine from the six month-ends in `BACKTEST_ORIGINS` (31 March to 31 August 2026) at horizons 1 and 3 for a naive model (last month's daily rate), the statistical model and the model with drivers; `error_stats` computes MAPE, WAPE and bias, and `rms_pct_error` the error that `compute_forecast` turns into an 80% range (±1.28 sigma, widened with the square root of the horizon). The renewal size comes from `sp_sizing`.

### Worked example

```
Backtest (rolling origin; recurring usage only, one-time items excluded):
Origin      Month    h      Actual       Naive  Statistical  Stat+drivers  APE naive  APE stat  APE drivers
----------  -------  -  ----------  ----------  -----------  ------------  ---------  --------  -----------
2026-03-31  2026-04  1    $971,297    $961,100     $989,327      $989,301       1.0%      1.9%         1.9%
2026-03-31  2026-06  3    $972,746    $961,100   $1,025,628    $1,025,551       1.2%      5.4%         5.4%
2026-04-30  2026-05  1  $1,001,129  $1,003,674     $998,950      $998,956       0.3%      0.2%         0.2%
2026-04-30  2026-07  3  $1,072,171  $1,003,674   $1,057,162    $1,084,019       6.4%      1.4%         1.1%
2026-05-31  2026-06  1    $972,746    $968,834     $979,148      $979,229       0.4%      0.7%         0.7%
2026-05-31  2026-08  3  $1,138,668  $1,001,129   $1,025,457    $1,105,870      12.1%      9.9%         2.9%
2026-06-30  2026-07  1  $1,072,171  $1,005,171   $1,016,045    $1,042,959       6.2%      5.2%         2.7%
2026-06-30  2026-09  3  $1,198,195    $972,746   $1,011,223    $1,135,846      18.8%     15.6%         5.2%
2026-07-31  2026-08  1  $1,138,668  $1,072,171   $1,064,117    $1,113,393       5.8%      6.5%         2.2%
2026-08-31  2026-09  1  $1,198,195  $1,101,937   $1,133,126    $1,172,724       8.0%      5.4%         2.1%

Accuracy (MAPE = mean |A-F|/A; WAPE = sum |A-F| / sum A; bias = sum (F-A) / sum A):
Model                            MAPE h=1  WAPE h=1  Bias h=1  MAPE h=3  WAPE h=3  Bias h=3
-------------------------------  --------  --------  --------  --------  --------  --------
Naive (last month's daily rate)      3.6%      3.9%     -3.8%      9.6%     10.1%    -10.1%
Statistical                          3.3%      3.5%     -2.7%      8.1%      8.4%     -6.0%
Statistical + drivers                1.6%      1.7%     -0.9%      3.7%      3.6%     -0.7%

12-month forecast (renewal assumed at $210/hour; range from backtest errors, sigma h1 1.9%, h3 4.1%):
Month       Run-rate  Migration scope  SP renewal  Known items  Exp. savings     Forecast       ~80% range
-------  -----------  ---------------  ----------  -----------  ------------  -----------  ---------------
2026-10     $895,228         $350,686         +$0          +$0      -$19,331   $1,226,584  $1.19M - $1.26M
2026-11     $897,431         $196,231         +$0          +$0      -$39,450   $1,054,213  $1.01M - $1.10M
2026-12     $983,921         $146,066         +$0          +$0      -$43,950   $1,086,037  $1.03M - $1.14M
2027-01     $933,232         $153,163         +$0          +$0      -$43,950   $1,042,445   $980k - $1.11M
2027-02     $884,109         $137,973       +$137          +$0      -$43,950     $978,270   $913k - $1.04M
2027-03     $981,216         $153,651       +$446          +$0      -$43,950   $1,091,362  $1.01M - $1.17M
2027-04     $960,261         $148,616       +$343          +$0      -$43,950   $1,065,270   $981k - $1.15M
2027-05     $990,971         $152,199       -$240          +$0      -$43,950   $1,098,981  $1.01M - $1.19M
2027-06     $991,322         $150,378       +$343          +$0      -$43,950   $1,098,092   $999k - $1.20M
2027-07   $1,028,858         $153,480       +$103          +$0      -$43,950   $1,138,491  $1.03M - $1.25M
2027-08   $1,044,936         $154,668       +$126          +$0      -$43,950   $1,155,780  $1.04M - $1.27M
2027-09   $1,034,112         $151,185       +$621     +$48,000      -$43,950   $1,189,968  $1.07M - $1.31M
Total    $11,625,598       $2,048,298     +$1,878     +$48,000     -$498,281  $13,225,493

Full-year 2026 outlook: actual Jan-Sep $9,253,713 + forecast $3,366,834 = $12,620,546 vs budget $12,190,400 (+$430,146, +3.5%).
Savings Plan after the AWS decommission (2026-11-01): projected utilization 96.5%, about $5,656/month unused until expiry on 2027-01-31.
AI assistant model spend trend: +5.9% a month (damped in the forecast).
```

Reading it. The backtest's worst rows are the three-month forecasts made in May and June: the naive model is 12% and 19% low and the statistical model 10% and 16% low, because neither knew the Google Cloud build-out would start on 1 July; the driver model, which reads the plan, is 2.9% and 5.2% low, and its remaining September error is the lapsed reservation (\$23,040) that nobody put on the calendar. Over six one-month origins the driver model's WAPE is 1.7% against 3.9% for naive, with a bias of −0.9% (slightly low, which the summary says before anyone asks). In the forecast table the migration scope falls from \$350,686 in October to \$196,231 in November (AWS compute off) and \$146,066 in December (storage deleted); the SP renewal column is a few hundred dollars because \$210 an hour is close to today's \$220; the \$48,000 renewal recurs in September 2027. Without drivers (`forecast_engine(D, D.last, date(2027, 9, 30), use_drivers=False)`) the 12-month total is \$16,150,489 instead of \$13,225,493 and November \$1,215,242 instead of \$1,054,213: the statistical model extrapolates the build-out and keeps the AWS platform running.

### How you would do it on real billing data

The series are `SubAccountName` × `ServiceName` sums of `EffectiveCost` over `Usage` rows by `ChargePeriodStart`: the FOCUS view you build from AWS Data Exports (CUR 2.0 or FOCUS 1.2), the Azure FOCUS export and the Google BigQuery billing export (47b.5–47b.6). The native forecasts (Cost Explorer, Azure cost analysis, the Google billing report) are cross-checks for the current-month landing and nothing more: per cloud, extrapolated, blind to your calendar. The drivers layer is your own work: a known-changes register with dates, owners and amounts (47c.3), the commitment inventory with end dates, and the savings pipeline with probabilities. Pitfalls the lab's data lacks: restated months (AWS can change the previous month for two weeks), partial last days, credits that distort trend months, Google `cost` without credits, support fees posting on the 6th or 7th, taxes and currencies. Keep versions of the register as it stood at each origin, or your backtest flatters the driver model the way the lab's does.

## Variance analysis

### Intuition

Three numbers meet at month end: the budget (fixed a year ago with old information), the forecast (made last month) and the actual. The analyst's job is to explain the gaps in words a CIO can act on: how much is timing (it will reverse), how much is one-off (it will not recur), how much is rate (prices or discounts changed) and how much is real growth (it will persist). A bridge that adds up exactly is what makes the explanation defensible.

### How the lab does it

`compute_variance(D, month)` re-makes the forecast from the day before the month began (`forecast_engine(D, as_of=month start − 1, end=month end)`), so the comparison is fair. For each series it takes usage at list prices as the volume measure (L) and `EffectiveCost ÷ ListCost` as the effective rate (e). The forecast rate `eF` is e over the 28 days before the month; the forecast volume `LF` is the forecast cost divided by `eF`. Then, across all usage series:

- volume = (ΣLA − ΣLF) × average `eF`: more or less usage, at the forecast's average rate;
- mix = Σ(LA × eF) − ΣLA × average `eF`: usage moved between services with different rates;
- rate = Σ LA × (eA − eF): the price paid per list dollar changed;

and volume + mix + rate equals actual usage cost minus forecast usage cost exactly. Unused commitment, one-time charges, credits and expected pipeline savings not yet realized are separate bridge lines, and any residual is printed. The budget comparison is by budget line (from `budget_line_of`, which reads `ACCOUNT_MAP`), with a materiality flag at the larger of \$10,000 and 5%. `cmd_variance` also prints the FinOps Foundation accuracy rate, (forecast − actual) ÷ forecast, the budget-variance band (Run 12%, Walk 15%, Crawl 20%) and the top ten drivers, each annotated by `context_notes`, which looks the series up in the commitment inventory, the calendar and the initiative register before printing "investigate".

### Worked example

```
Measure                          Amount  Actual minus       %
---------------------------  ----------  ------------  ------
Budget (approved late 2025)  $1,036,400     +$197,795  +19.1%
Forecast (made 2026-08-31)   $1,160,724      +$73,472   +6.3%
Actual                       $1,234,195

Forecast accuracy (FinOps Foundation: (forecast - actual) / forecast) = -6.3%
Budget variance 19.1%: within Crawl (20%) of the FinOps Foundation budgeting thresholds.

By budget line (materiality: |difference| >= max($10,000, 5%)):
Budget line           Budget    Forecast      Actual  Act - Bud  Act - Fcst  Materiality
----------------  ----------  ----------  ----------  ---------  ----------  -----------
ai-assistant         $63,700     $89,953     $88,639   +$24,939     -$1,314      explain
claims-analytics    $243,600    $346,388    $348,369  +$104,769     +$1,981      explain
customer-portal     $178,700    $166,993    $191,564   +$12,864    +$24,571      explain
doc-intelligence     $38,800     $39,836     $40,331    +$1,531       +$495
ml-research          $25,600     $36,609     $35,745   +$10,145       -$864      explain
payments-api        $374,500    $362,431    $362,418   -$12,082        -$13
shared-platform     $111,500    $118,515    $167,131   +$55,631    +$48,616      explain
Total             $1,036,400  $1,160,724  $1,234,195  +$197,795    +$73,472

Bridge: budget -> forecast -> actual:
Step                                   Change  Running total
----------------------------------  ---------  -------------
Budget                                            $1,036,400
  plan change: ai-assistant          +$26,253     $1,062,653
  plan change: claims-analytics     +$102,788     $1,165,441
  plan change: customer-portal       -$11,707     $1,153,733
  plan change: doc-intelligence       +$1,036     $1,154,769
  plan change: ml-research           +$11,009     $1,165,778
  plan change: payments-api          -$12,069     $1,153,709
  plan change: shared-platform        +$7,015     $1,160,724
Forecast                                          $1,160,724
  Volume (usage at forecast rates)      +$294     $1,161,018
  Mix (between services)                 -$63     $1,160,955
  Rate (price per unit)              +$25,241     $1,186,195
  Unused commitment                       +$0     $1,186,195
  One-time charges                   +$48,000     $1,234,195
  Credits                                 +$0     $1,234,195
Actual                                            $1,234,195

Top drivers, forecast -> actual:
Series                               Usage (vol+mix)      Rate     Total  Context from calendar, commitments, register
-----------------------------------  ---------------  --------  --------  ----------------------------------------------------------------------
az-crm-prod / Virtual Machines                 +$484  +$23,415  +$23,899  commitment ri-crm-vm-2025 ended 2026-08-31
aws-payments-prod / Amazon EC2                 +$923     +$715   +$1,638  Savings Plan coverage shifts between accounts
aws-data-platform-prod / Amazon EC2            +$751     +$646   +$1,397  Savings Plan coverage shifts between accounts; migration source
az-ai-assistant-prod / Azure OpenAI          -$1,327       +$0   -$1,327  investigate
aws-payments-nonprod / Amazon EC2            -$1,547     +$349   -$1,198  Savings Plan coverage shifts between accounts; INIT-02: Schedule non-p
aws-ml-sandbox / Amazon EC2                    -$751      +$80     -$671  Savings Plan coverage shifts between accounts
az-crm-prod / Log Analytics                    +$566       +$0     +$566  investigate
gcp-docai-prod / Gemini API                    +$447       +$0     +$447  investigate
aws-data-platform-prod / Amazon EMR            +$432       -$0     +$432  migration source
aws-payments-prod / Amazon RDS                 -$397       -$0     -$397  INIT-01: Rightsize payments RDS instances
(one-time charges)                          +$48,000       +$0  +$48,000  not in the forecast: added to the calendar after it was made
```

Reading it. The budget gap (\$197,795) is mostly plan change the forecast already knew: the migration started two months early (+\$102,788 on claims-analytics) and the AI assistant grew 6% a month rather than the budgeted 3% (+\$26,253). The forecast gap (\$73,472) is two things it could not know: the rate line (+\$25,241, of which \$23,415 is the CRM VMs whose reservation lapsed, the rest Savings Plan shifts between accounts) and the \$48,000 subscription added to the calendar ten days after the forecast was made. Usage was as forecast (volume +\$294, mix −\$63). One subtlety in the EC2 rows: on Savings Plan accounts marginal usage is all on demand, so part of what the decomposition calls rate is really volume. `variance --month 2026-08` shows a quieter month: \$112,568 (+11.1%) over budget, \$25,275 (+2.3%) over forecast.

### How you would do it on real billing data

The decomposition needs `ListCost` and `EffectiveCost` per line, which FOCUS gives directly; CUR 2.0 has the public on-demand cost and amortized cost columns; the Google export has `cost` plus `credits` against the pricing export (47b.5). Budget lines come from your account map. Cost Explorer's Cost Comparison names month-over-month drivers (usage, credits, refunds, volume discounts) and is a cross-check for the bridge; Azure cost analysis and Google's cost breakdown help with the rate side. Pitfalls: take one-time and timing items out first; write down the convention (quantity changes at the forecast rate, rate changes at actual quantity) and keep it; reconcile amortized to billed before the numbers leave your desk, because the central team reports on the invoice basis (47c.9).

## Anomaly detection

### Intuition

An anomaly is a day that is wrong for its scope, caught while it can still be stopped. Two things make detection hard: cloud cost has a weekly cycle (a non-production account at 40% on Saturday is normal), and most spikes are expected (a load test, a migration, an annual renewal). So the detector compares like with like (same weekday), uses statistics that the anomalies themselves cannot distort (medians), requires a change to be statistically unusual and large in percentage and large in dollars at the same time, and then triages against the analyst's own records before anyone is paged. Precision is the metric that keeps owners reading alerts.

### How the lab does it

`robust_baseline(vals, d, weeks)` returns the median of the same weekday over the previous `weeks` weeks and a spread of 1.4826 × MAD, floored at 5% of the median and at \$1 so a flat series cannot produce an infinite z-score. `detect_series` flags a day when all three conditions of the rule hold: z ≥ 4.0, increase ≥ 25% and increase ≥ \$500 (`DEFAULT_RULE = {"weeks": 6, "z": 4.0, "pct": 0.25, "usd": 500.0}`). `group_events` merges flagged days across gaps of up to two days, so a weekend does not split an event. `attribute_event` splits each day's excess into usage (change in list-priced volume at the baseline effective rate) and rate (change in effective cost per list dollar); an event is "rate" at 60% or more, "usage" at 40% or less, otherwise "mixed". `triage` applies three rules in order: planned if a calendar entry for that sub-account and service overlaps the event and was added before the detection date (start plus the provider's latency); data artifact if a one-day spike follows a day below 60% of its baseline and the two days together are within 20% of normal; provisional if newer than the provider's latency. Severity is cost so far plus 30 days of the latest excess if still running: Sev1 at \$25,000, Sev2 at \$5,000. `detector_view` adds one-time purchases to the usage series; `compute_anomalies` runs from eight weeks after the first day, scores against `INJECTED` through `truth_of` and computes time to detect; `compute_unit_cost_anomalies` runs the same rule on cost per conversation and per thousand transactions (`UNIT_SCOPES`) with impact = unit-cost excess × volume; `SWEEP_RULES` re-scores with loose, medium, default and strict thresholds; `anomaly_cost_share` gives the FinOps Foundation bands.

### Worked example

```
Events (Truth = the injected ground truth, for scoring only):
 #  Series                                               Start       End         Days   Excess  Max z   Max %  Driver    Triage                     Detected    Sev   Truth
--  ---------------------------------------------------  ----------  ----------  ----  -------  -----  ------  --------  -------------------------  ----------  ----  -----
 1  aws-payments-nonprod / Amazon EC2                    2025-11-18  2025-11-20  3      $5,634   12.7    +64%  usage     planned (PC-01)            2025-11-19  Sev2  PC-01
 2  aws-shared-network / Amazon VPC                      2026-02-10  2026-02-15  6     $13,651   54.5   +272%  usage     anomaly                    2026-02-11  Sev2  A1
 3  aws-payments-prod / Amazon EC2                       2026-03-04  2026-03-04  1      $2,857   14.1    +71%  usage     data artifact (late rows)  2026-03-05  Sev3  A2
 4  gcp-analytics-dev / BigQuery                         2026-04-22  2026-04-22  1      $3,880  245.5  +1228%  usage     anomaly                    2026-04-23  Sev3  A3
 5  aws-ml-sandbox / Amazon EC2                          2026-05-18  2026-05-29  12    $30,057  203.0  +1280%  usage     anomaly                    2026-05-19  Sev1  A4
 6  az-crm-prod / Log Analytics                          2026-07-07  2026-07-11  5      $9,037   38.2   +191%  usage     anomaly                    2026-07-09  Sev2  A5
 7  gcp-analytics-prod / BigQuery                        2026-07-15  2026-07-17  3      $1,868   17.8    +89%  usage     planned (PC-02)            2026-07-16  Sev3  PC-02
 8  gcp-analytics-prod / BigQuery                        2026-07-21  2026-07-28  7      $5,171   21.4   +119%  usage     planned (PC-02)            2026-07-22  Sev2  PC-02
 9  az-ai-assistant-prod / Azure OpenAI                  2026-08-03  2026-08-11  9     $18,238   19.6    +98%  usage     anomaly                    2026-08-05  Sev2  A7
10  az-crm-prod / Virtual Machines                       2026-09-01  2026-09-21  21    $16,629   11.2    +56%  rate      anomaly                    2026-09-03  Sev2  A8
11  aws-management / AWS Marketplace: SIEM subscription  2026-09-15  2026-09-15  1     $48,000  999.0     new  one-time  planned (PC-03)            2026-09-16  Sev1  PC-03

Events flagged: 11. Raw precision (before triage): 54.5%.
After triage: 6 labeled anomaly, 6 true, 0 false -> precision 100.0%.
Recall on detector-targeted anomalies: 100.0%.
A6 (Non-production schedules disabled (savings decay)) is meant for the savings-tracker: not caught by the detector.

Time to detect (start of the anomaly to data available + flagged):
Id  Anomaly                                              Started     Detected    Days  Excess cost  Driver  Route to
--  ---------------------------------------------------  ----------  ----------  ----  -----------  ------  ----------------
A1  NAT gateway data-processing spike                    2026-02-10  2026-02-11     1      $13,651  usage   team-platform
A3  Runaway BigQuery query in development                2026-04-22  2026-04-23     1       $3,880  usage   team-claims-data
A4  Forgotten GPU cluster                                2026-05-18  2026-05-19     1      $30,057  usage   team-ml
A5  Logging explosion                                    2026-07-07  2026-07-09     2       $9,037  usage   team-crm
A7  Prompt change raised tokens per conversation by 80%  2026-08-03  2026-08-05     2      $18,238  usage   team-ai
A8  Reservation expired: rates rose, usage did not       2026-09-01  2026-09-03     2      $16,629  rate    team-crm

Unit-cost anomalies (cost per business unit; baseline and peak on the day of the largest increase; impact = excess x volume):
Application   Unit cost              Start       End         Days  Baseline    Peak  Peak %   Impact
------------  ---------------------  ----------  ----------  ----  --------  ------  ------  -------
ai-assistant  cost per conversation  2026-08-03  2026-08-11     9    0.0529  0.0888    +68%  $16,846

Threshold sweep (precision and recall after triage):
Rule     Thresholds               Events  Labeled  TP  FP  Precision  Recall  Missed
-------  -----------------------  ------  -------  --  --  ---------  ------  ------
loose    z>=3.0, >=15%, >=$250        23       18   8  10      44.4%  100.0%  -
medium   z>=3.5, >=20%, >=$400        17       11   9   2      81.8%  100.0%  -
default  z>=4.0, >=25%, >=$500        11        6   6   0     100.0%  100.0%  -
strict   z>=5.0, >=40%, >=$1,000       8        5   5   0     100.0%   83.3%  A8

Anomaly cost % = anomaly excess / total spend (FinOps Foundation bands <2% / 2-7% / >7%):
Month    Anomaly cost  Anomaly cost %    Band
-------  ------------  --------------  ------
2026-04        $3,880           0.40%   green
2026-05       $30,057           3.00%  yellow
2026-06            $0           0.00%   green
2026-07        $9,037           0.85%   green
2026-08       $18,238           1.62%   green
2026-09       $16,629           1.35%   green
```

Reading it. Every planted spike is in the table, and so is everything triage exists for. Event 1 is the load test, on the calendar two weeks before it ran. Event 3 is the data artifact: 4 March is +71% because 65% of 3 March's rows arrived a day late, and the two-day sum is normal. Events 7 and 8 are the build-out, planned since February. Event 11 is the \$48,000 subscription, added to the calendar on 10 September, before the 16 September detection date. Six events survive, all true: raw precision 54.5% becomes 100%. Event 10 is the lapsed reservation, labeled rate because VM hours barely moved while cost per hour rose; it is flagged until 21 September and then absorbed into the six-week baseline, so the ticket, not the detector, must keep it open. The strict rule misses it: a daily excess of about \$790 is under the \$1,000 floor although it costs \$23,040 a month. The savings decay (A6, +15% on weekdays, under \$500 a day) is invisible to the default rule; the medium rule catches it on three July weekends and adds two false alerts on the new Bedrock experiments. The unit-cost pass shows cost per conversation rising from \$0.0529 to \$0.0888 while conversations did not change. The detector flags 69 days in all; the SQL version in 47f.12 reports 68 because it reads usage rows only and does not see the marketplace purchase.

### How you would do it on real billing data

Run the detector on your FOCUS table at `SubAccountName` × `ServiceName` grain, then at application and unit-cost grain once allocation exists. Keep the native detectors on and route them into the same queue: AWS Cost Anomaly Detection (net unblended cost, about three runs a day), Azure's anomaly alerts (subscription scope, about 36 hours late) and Google Cloud Billing anomaly detection (on-demand rates, so it does not see a CUD lapse). None knows your calendar, unit costs or amortized basis (47d.10). Pitfalls: hold each provider's newest one or two days until complete; detect on `ContractedCost` as well as `EffectiveCost` for series under a shared commitment, because one account's spike takes coverage from the others (the GPU cluster did this to the payments team); add a run-rate test for moderate persistent changes a daily dollar floor cannot see; suppress through the calendar, never by muting a series.

## Allocation and tagging

### Intuition

Allocation answers "who caused this dollar?". Tags are the obvious key and the unreliable one: some charges cannot carry a tag, tags arrive late, and they break silently when a key is renamed or a value is miscased. The provider's own hierarchy (account, subscription, project) is stamped on every row from day one. So the lab allocates hierarchy first, tags second, account defaults third, and measures two different things: strict compliance (is the tag exactly right?) and lenient allocation (can we tell whose dollar it is?). Shared costs are real and must be split by a method agreed before the numbers are shown.

### How the lab does it

`is_taggable(r)` restricts compliance to usage rows that are not unused commitment. `tag_issues(tags)` checks each of the four required keys against `TAG_STANDARD`: a missing key, a misspelled key (one that the alias table would map), a wrong-case value, or a value not in the dictionary; a row is compliant only with no issues. `normalize_tags(tags)` applies the key aliases, lowercases, and applies the value aliases (`payments` to `payments-api`); it is used for allocation, not for compliance. `allocate_row(r)` returns the method: `shared` for shared-kind accounts (to their pool), `credit` for credits in single-application accounts (to that application), `tag` when the normalized `application` is in the dictionary, `account` for a single-application account's default, otherwise `unallocated` (which can only happen in multi-team accounts). `allocation_month` sums cost by method, application, pool and violation, and records a compute-and-network footprint per application in list dollars as the usage proxy. `split_pool(amount, method, direct, proxy)` implements the four shared-cost methods: even, proportional to direct cost, fixed (`FIXED_SPLIT`, an agreed table), and usage-driven on the proxy. `compute_allocation` adds the monthly trend from October 2025.

### Worked example

```
Tagging Policy Compliance = compliant cost / taggable cost = $1,001,544 / $1,198,195 = 83.6% (first target > 90%)
Unallocated cost % = $8,495 / $1,234,195 = 0.69%; allocated 99.3% (FinOps Foundation maturity examples: >=70% Crawl, >=85% Walk, >90% Run)

Tag compliance by provider (strict: exact keys, lowercase, dictionary values):
Provider      Taggable cost  Compliant cost  Compliance
------------  -------------  --------------  ----------
AWS                $641,997        $490,830       76.5%
Microsoft          $341,842        $330,152       96.6%
Google Cloud       $214,357        $180,562       84.2%

Top tag violations by cost (fix the expensive ones first):
Sub-account           Violation                                     Cost affected  % of taggable
--------------------  --------------------------------------------  -------------  -------------
aws-payments-nonprod  value not in dictionary application=payments        $85,181           7.1%
aws-shared-network    untagged (all required keys missing)                $53,802           4.5%
gcp-analytics-prod    untagged (all required keys missing)                $23,429           2.0%
az-crm-prod           untagged (all required keys missing)                $11,690           1.0%
gcp-analytics-dev     key spelled 'costcenter'                            $10,366           0.9%
aws-ml-sandbox        untagged (all required keys missing)                 $8,495           0.7%
aws-management        untagged (all required keys missing)                 $3,689           0.3%

Allocation waterfall (hierarchy first, then tags, then account defaults):
How the cost was allocated                 Cost  Share
-----------------------------------  ----------  -----
Direct: tag (after normalization)    $1,035,452  83.9%
Direct: account default (hierarchy)     $35,118   2.8%
Credits (to the account's owner)       -$12,000  -1.0%
Shared pools (split below)             $167,131  13.5%
Unallocated                              $8,495   0.7%

What is unallocated:
Unallocated series                 Cost  Why
-------------------------------  ------  --------------------------------------------
aws-ml-sandbox / Amazon Bedrock  $8,495  multi-team account, no valid application tag

Network pool ($53,802) under four split methods:
Application       Direct cost  Network: even  Network: proportional  Network: fixed  Network: usage-driven
----------------  -----------  -------------  ---------------------  --------------  ---------------------
payments-api         $362,418         $8,967                $18,420         $21,521                $25,599
claims-analytics     $348,369         $8,967                $17,706         $13,451                $14,618
customer-portal      $191,564         $8,967                 $9,736          $8,070                $10,642
ai-assistant          $88,639         $8,967                 $4,505          $5,380                   $538
doc-intelligence      $40,331         $8,967                 $2,050          $2,690                   $671
ml-research           $27,250         $8,967                 $1,385          $2,690                 $1,734

Showback with shared pools split proportionally to direct cost:
Application         Direct  + commitments-and-governance  + network  + security  Fully loaded  % of total
----------------  --------  ----------------------------  ---------  ----------  ------------  ----------
payments-api      $362,418                       $17,696    $18,420     $21,103      $419,638       34.0%
claims-analytics  $348,369                       $17,010    $17,706     $20,285      $403,370       32.7%
customer-portal   $191,564                        $9,354     $9,736     $11,155      $221,808       18.0%
ai-assistant       $88,639                        $4,328     $4,505      $5,161      $102,633        8.3%
doc-intelligence   $40,331                        $1,969     $2,050      $2,348       $46,698        3.8%
ml-research        $27,250                        $1,331     $1,385      $1,587       $31,552        2.6%
unallocated         $8,495                                                             $8,495        0.7%

Trend (tag remediation: ml-sandbox Jan 15, data platform Mar 15, CRM dev May 1, CRM prod Jun 1):
Month    Tag compliance  Unallocated  Allocated
-------  --------------  -----------  ---------
2025-10           44.0%        4.71%      95.3%
2025-11           45.3%        4.58%      95.4%
2025-12           46.4%        4.59%      95.4%
2026-01           45.9%        3.48%      96.5%
2026-02           46.8%        2.31%      97.7%
2026-03           57.2%        1.09%      98.9%
2026-04           66.1%        0.00%     100.0%
2026-05           71.8%        0.00%     100.0%
2026-06           84.1%        0.00%     100.0%
2026-07           83.6%        0.00%     100.0%
2026-08           83.2%        0.76%      99.2%
2026-09           83.6%        0.69%      99.3%
```

Reading it. Compliance is 83.6% while allocation is 99.3%: the gap is the point. The biggest violation, `application=payments` on the non-production payments account (\$85,181, 7.1% of taggable cost), is harmless for allocation because the value alias maps it, and fixing that one value lifts compliance to 90.7%. Untagged shared network and storage rows are allocated by the hierarchy. The only unallocated cost is the Bedrock experiments in the multi-team sandbox, untagged since they started in August. By the raw `application` tag alone, \$222,285 (18.0%) would be unallocated; with aliases, \$137,104 (11.1%); with the account map, \$8,495 (0.7%). On the network pool the AI assistant pays \$8,967 under the even method and \$538 under the usage-driven one, because its cost is tokens rather than compute and network: neither is wrong, so the method is agreed first. The trend shows each remediation date as a step; the August dip is the Bedrock series arriving.

### How you would do it on real billing data

The hierarchy is `SubAccountId` in FOCUS (`line_item_usage_account_id` in CUR 2.0, the subscription in Azure, `project.id` in Google) and the account map is a table you keep with `valid_from` and `valid_to`. Tags are the `Tags` map in FOCUS, `resource_tags` in CUR 2.0, `tags` in Azure and `labels` in Google; enforcement is AWS tag policies, Azure Policy and tag inheritance, Google organization policies (47d.3). Mirror your allocation in the native tools (AWS Cost Categories with split charges, Azure cost allocation rules, Google labels and folders) so console users see the same owners (47d.5). Pitfalls: Google labels are lowercase only, so one standard must be lowercase everywhere; AWS's 12-month backfill fills only values a tag already had; a tag table with several rows per resource multiplies cost in a join; shared Savings Plan benefits move cost between accounts; keep pools few, on their own line, with rules that change only at fiscal-year boundaries (47d.6).

## Commitment management

### Intuition

A commitment trades flexibility for a discount. Two numbers describe how well it is working: utilization (are we using what we bought?) and coverage (how much of what we could cover is covered?). The break-even rule decides where to stop: a commitment of C costs C whether used or not and saves d ÷ (1 − d) per covered dollar, so the marginal dollar pays off only if usage exceeds it at least (1 − d) of the time; at a 30% discount that is 70%, and the expected-value optimum is the 30th percentile of usage, not the minimum and not the average. Because the net-savings curve is flat near the optimum and usage can fall, the lab recommends the smallest commitment that earns almost all of the best net.

### How the lab does it

`compute_commitments(D, month)` walks `COMMITMENTS` and sums, from the month's rows, used and unused `EffectiveCost` by `CommitmentDiscountId` and `CommitmentDiscountStatus`, the billed fee from `Purchase` rows, and coverage (covered `ContractedCost` over all eligible EC2 in `SP_KEYS` for the spend-based plan; covered hours over the series' hours for the reservation and the CUD). Savings is covered contracted cost minus used effective cost. For a commitment that ended before the month, `lost` prices the hours it would have covered at on-demand rate × discount. Three ESR definitions are computed per provider over usage rows including unused commitment: FOCUS, (`ContractedCost` − `EffectiveCost`) ÷ `ContractedCost`; FinOps Foundation option 1, (commitment savings − unused commitment) ÷ `ListCost`; option 2, 1 − `EffectiveCost` ÷ `ListCost`.

`sp_sizing(D, as_of)` fits the eligible series on `ContractedCost`, projects daily eligible usage in Savings Plan dollars for the year after expiry without the source account's EC2, and evaluates every hourly commitment from \$100 to \$400 in \$5 steps: utilization, coverage, gross savings (covered × d ÷ (1 − d)), unused and net. The recommendation is the smallest grid point whose net is at least 95% of the best (`plateau`); the table also shows the P5 floor, the expected-value optimum, renewing as is and 120% of the optimum, and the current plan's utilization and monthly waste between decommission and expiry. `ri_sizing` takes the 10th percentile of concurrent VMs (daily VM-hours ÷ 24) over 30 days, rounds down to a multiple of ten and nets the hours paid for and not used.

### Worked example

```
Inventory and month metrics (utilization = used / amortized commitment; coverage = covered / eligible usage):
Commitment         Provider      Type                            Term                    Billed fee  Amortized      Used  Unused  Utilization  Coverage  Waste %  Savings  Status
-----------------  ------------  ------------------------------  ----------------------  ----------  ---------  --------  ------  -----------  --------  -------  -------  ------------------
sp-0a1b2c3d4e5f    AWS           Savings Plan (Spend)            2024-02-01..2027-01-31    $158,400   $158,400  $158,400      $0       100.0%     56.2%     0.0%  $67,886  active
ri-crm-vm-2025     Microsoft     Reservation (Usage)             2025-09-01..2026-08-31          $0         $0        $0      $0          n/a       n/a      n/a       $0  expired 2026-08-31
cud-gce-analytics  Google Cloud  Committed Use Discount (Usage)  2024-06-01..2027-05-31      $7,258     $7,258    $7,258      $0       100.0%     73.3%     0.0%   $4,262  active

ri-crm-vm-2025 expired on 2026-08-31: the same hours at on-demand rates cost $23,040 more in 2026-09 (rate, not usage).

Effective savings rate, three definitions (usage rows incl. unused commitment):
Provider        ListCost  ContractedCost  EffectiveCost  ESR (FOCUS)  Option 1 at list  Option 2 at list
------------  ----------  --------------  -------------  -----------  ----------------  ----------------
AWS             $755,194        $709,882       $641,997         9.6%              9.0%             15.0%
Microsoft       $341,842        $341,842       $341,842         0.0%              0.0%              0.0%
Google Cloud    $227,728        $218,619       $214,357         1.9%              1.9%              5.9%
All           $1,324,764      $1,270,343     $1,198,195         5.7%              5.4%              9.6%

  AWS Savings Plan pool (eligible EC2 + unused): ESR 16.9%.

Savings Plan renewal (sp-0a1b2c3d4e5f, $220/hour, expires 2027-01-31):
  Eligible usage in SP dollars, last 60 days: min $248/h, P5 $259/h, median $427/h (includes the data platform).
  Projected for the renewal year without the data platform: P5 $198/h, P30 $304/h, median $321/h.
  Current plan after the decommission on 2026-11-01: utilization 96.5%, about $5,656/month unused until expiry.
  Break-even utilization = 1 - discount = 70%.

Sensitivity for the renewal year (1-year view, discount 30%):
Option                                        Hourly  Utilization  Coverage  Gross savings/yr  Unused/yr  Net savings/yr
--------------------------------------------  ------  -----------  --------  ----------------  ---------  --------------
Floor: P5 of daily usage                        $195       100.0%     65.9%          $731,886       $466        $731,420
Recommended: 95% of best net, least exposure    $210        99.2%     70.4%          $782,263    $14,319        $767,944
Expected-value optimum on the $5 grid           $305        91.0%     93.8%        $1,041,706   $241,153        $800,554
Renew as is                                     $220        98.2%     73.1%          $811,233    $34,324        $776,909
Oversized: 120% of the optimum                  $365        80.9%     99.8%        $1,108,252   $611,478        $496,774

Azure VM reservation (expired): P10 of concurrent VMs over 30 days = 241; recommend 240 instances, expected utilization 99.8%, net saving about $27,912/month at 40% (break-even utilization 60%).
```

Reading it. The Savings Plan is fully used but covers only 56.2% of eligible EC2, so there is room to buy more until the data platform leaves on 1 November, after which the current plan runs at 96.5% and wastes about \$5,656 a month. The ESR definitions differ because `ContractedCost` already contains the negotiated discounts: FOCUS and option 1 see only commitment savings, option 2 everything. On the Savings Plan pool alone the FOCUS ESR is 16.9%, which equals utilization 100% × coverage 56.2% × discount 30%. Azure's ESR is 0.0% because the reservation lapsed; the same hours cost \$23,040 more. For the renewal, the \$305 optimum earns \$32,610 a year more net than the \$210 recommendation but exposes \$95 an hour more to a fall in usage; the curve is flat because weekdays are 71.4% of days, just above the 70% break-even. The 240-VM reservation is the largest decision on the summary page.

### How you would do it on real billing data

FOCUS gives `CommitmentDiscountId`, `CommitmentDiscountStatus` and the four cost columns, so utilization and coverage are the SQL of 47f.12 exercise 5 (filter unused rows out of both sides of coverage). In CUR 2.0 the metrics come from `RIFee` and `SavingsPlanRecurringFee` rows and the amortized columns; Cost Explorer has utilization and coverage reports, Purchase Analyzer and Cost Optimization Hub the sizing; Azure's reservation datasets, utilization alerts and Advisor and Google's CUD recommender and CUD metadata export do the same per cloud (47e.1). Pitfalls: size from hourly data, because the lab's daily floor is an upper bound; remove what is leaving and add committed growth before every purchase; AWS applies a plan to the highest savings percentage first, not pro rata, so cost shifts differ from the lab's; quote every savings rate with its definition and population, and filter to usage rows, because over all rows the lab's FOCUS ESR reads 16.8% instead of 5.7% (purchase rows carry `ContractedCost` with zero `EffectiveCost`; 47f.12).

## Savings tracking

### Intuition

A saving is a claim about a world that did not happen, so it needs a counterfactual chosen before the change ships and re-measured every month. Four counterfactuals cover most initiatives: pre-change unit cost × actual volume, the pre-change trend projected forward, pre-change rate × actual quantity, and a ratio to a related meter. Each fails in a known direction, so cross-check with a second method, and watch for decay, which is the main way savings disappear. The lab can score each method against the truth because it can regenerate its data without each initiative.

### How the lab does it

`counterfactual(D, ini, method, k, vals, days)` builds the no-change cost per day from the 28 days before the start date: `unit` is pre-change cost per business unit × the driver's actual volume; `trend` fits `fit_series` on the day before the change and projects it; `rate` is pre-change cost per unit of `PricingQuantity` × actual quantity; `ratio` does the same against a related series (`ratio_of`: VM hours for the license meter). `realized_by_day` sums counterfactual minus actual. Series under the shared Savings Plan (`SP_KEYS`) are valued through the plan: their counterfactual and actual `ContractedCost` go through `sp_pool_cost` with all other eligible usage, so while the plan stays fully used a removed dollar of covered usage counts at the full contracted rate (its coverage moved to other accounts), and once usage falls below the plan, removing usage saves nothing. `compute_savings` prorates projections in partial months, sets the realization rate (on track at 90% or more, partial from 60%, at risk below), a trend cross-check, the decay flag (last full month below 75% of the best) and the true saving from `ground_truth.json`.

### Worked example

```
Implemented initiatives (since each start date; 'Trend check' = realized by the trend method; Truth = from the ground truth, for scoring only):
Id       Initiative                                                Start       Method  Projected  Realized  Rate  Trend check  Last month  Status                Truth
-------  --------------------------------------------------------  ----------  ------  ---------  --------  ----  -----------  ----------  -----------------  --------
INIT-01  Rightsize payments RDS instances                          2026-03-01  unit      $98,000  $118,716  121%     $114,285     $18,809  on track           $107,851
INIT-02  Schedule non-production compute (nights, weekends)        2026-04-15  trend    $221,333  $141,835   64%     $141,835     $20,376  partial, decaying  $136,652
INIT-03  S3 Intelligent-Tiering for payments log and archive data  2026-02-01  rate      $64,000   $52,922   83%      $49,621      $8,782  partial             $52,922
INIT-04  Azure Hybrid Benefit for Windows Server on CRM VMs        2026-05-01  ratio     $57,500   $62,231  108%      $63,002     $12,449  on track            $62,231
Total                                                                                   $440,833  $375,704   85%     $368,744     $60,417                     $359,657

Realized / projected by month (watch for decay):
Id       2026-02    2026-03    2026-04    2026-05    2026-06    2026-07    2026-08    2026-09
-------  -------  ---------  ---------  ---------  ---------  ---------  ---------  ---------
INIT-01           $15k/$14k  $16k/$14k  $16k/$14k  $17k/$14k  $18k/$14k  $18k/$14k  $19k/$14k
INIT-02                      $16k/$21k  $34k/$40k  $32k/$40k  $20k/$40k  $19k/$40k  $20k/$40k
INIT-03   $0/$8k    $3k/$8k    $8k/$8k    $8k/$8k    $8k/$8k    $8k/$8k    $9k/$8k    $9k/$8k
INIT-04                                 $12k/$12k  $12k/$12k  $13k/$12k  $13k/$12k  $12k/$12k

Year to date 2026: realized $375,704 of $440,833 projected (85%). Current monthly run-rate $60,417.

Pipeline (enters the forecast at monthly x probability from its start date):
Id      Opportunity                                                Start       Monthly  Probability  Expected  Owner
------  ---------------------------------------------------------  ----------  -------  -----------  --------  -----------------
OPP-01  Buy a new 1-year VM reservation (240 VMs) for az-crm-prod  2026-10-15  $27,000          90%   $24,300  team-crm + FinOps
OPP-02  Restore non-production schedules (opt-outs since July)     2026-10-15  $12,000          80%    $9,600  team-payments
OPP-03  Log Analytics retention and sampling for CRM               2026-11-01   $6,000          70%    $4,200  team-crm
OPP-04  Move payments EC2 to Graviton instances                    2026-12-01   $9,000          50%    $4,500  team-payments
OPP-05  Release idle public IPv4 addresses and old snapshots       2026-10-15   $1,500          90%    $1,350  team-platform
Total                                                                          $55,500                $43,950
```

Reading it. The rate and ratio methods hit the truth exactly for INIT-03 and INIT-04, because actual quantity × the old rate is precisely the counterfactual of a price or license-per-hour change. INIT-01's unit method is 10% high (\$118,716 against \$107,851) because it assumes RDS cost grows with transactions (2% a month) when the series grows 1.5%; its trend check is 6% high because the months it learned from include the November–December peak. INIT-02 is the lesson: through the plan it shows \$141,835 against a true \$136,652; on its own amortized `EffectiveCost` it would show only \$111,866, because the discount on each removed dollar moved to other accounts. Its monthly row shows the decay: \$34,000 in May, about \$20,000 since July, when half the fleet opted out. The detector never saw it (under \$500 a day); the tracker did. INIT-03's ramp (\$0, \$3,000, then \$8,000) is objects waiting 30 days without access before they move tiers.

### How you would do it on real billing data

The counterfactuals need `PricingQuantity` and the cost columns at meter grain (`line_item_usage_type` in CUR 2.0, `MeterId` in Azure, `sku.id` in Google) and business drivers from outside the bill. Register the method, scope and pre-period before implementation in the backlog that Cost Optimization Hub, Azure Advisor and Google's Recommender feed (47e.10), and restate every console estimate at your effective rates, because consoles quote retail rates and assume full adoption. Pitfalls: measure each initiative on the meter it touches (Hybrid Benefit on the license meter, the reservation on the compute meter), measure overlapping initiatives in implementation order, value usage on a shared commitment at the margin, never sum overlapping methods without checking the scope total, and re-verify quarterly until the saving is embedded in a policy (47e.12). Report run-rate, in-year and one-time figures separately and never add them.

## Executive reporting

### Intuition

Executives want two or three numbers, in words, with the decisions attached: this month against budget and forecast, the year's landing, and what savings are doing. Everything else on the page exists to defend those numbers if challenged: the drivers of the gap, the range on the outlook, the risks, and a reconciliation to the number the central finance team will quote.

### How the lab does it

`cmd_summary` calls `compute_variance`, `compute_forecast`, `compute_savings`, `compute_anomalies`, `compute_allocation` and `compute_commitments` and assembles the page of chapter 47f.3 in Markdown: three numbered sentences; a driver table that splits the budget gap into the migration's timing (the claims-analytics line's variance net of credits), the one-time charge, the lapsed reservation's `lost` cost, AI assistant growth, credits and a net remainder; the next three months with ranges and budgets; risks from the sizing, the AI series' fitted growth, the decay flag and the credits' end; a decisions table; and a reconciliation: amortized total − commitment cost amortized into usage + commitment fees billed = billed total. `kmoney` and `skmoney` round to the nearest thousand or to two decimals of a million.

### Worked example

```
## The three numbers

1. **September cost $1.23M: $198k (+19%) over budget and $73k (+6.3%) over our forecast.** Most of the budget gap is timing and one-offs: the claims-analytics migration started two months earlier than the budget assumed (+$117k until AWS is switched off on 1 November), a one-time marketplace renewal (+$48k) and a VM reservation that lapsed on 31 August 2026 (+$23k). The recurring overrun is AI assistant growth (+$25k).
2. **Full-year 2026 outlook $12.62M against a $12.19M budget: +$430k (+3.5%).** The outlook includes the AWS decommission on 1 November, the end of the migration credits and the savings pipeline at its probability. One month ahead, the forecast of recurring usage has been within 1.6% on average over six months (WAPE 1.7%); in September it missed by 2.1% (+$25k), of which the lapsed reservation was $23k, and the $48k one-time renewal came on top. Neither was on the change calendar.
3. **Savings now run at $60k a month; $376k realized this year (85% of plan).** Another $56k a month is identified ($44k probability-weighted); two decisions this month unlock $40k of it.

## What drove the gap to budget

| Driver | vs budget | Explanation |
| --- | ---: | --- |
| Claims-analytics migration ahead of plan (timing) | +$116,769 | Google Cloud build-out began 1 July, not 1 September; both sides run until 1 November |
| One-time marketplace renewal | +$48,000 | Annual SIEM subscription; not in the forecast |
| Azure VM reservation lapsed | +$23,040 | Same VM hours at on-demand rates (rate, not usage) |
| AI assistant growth | +$24,939 | Conversations up about 6% a month; budget assumed 3% |
| Migration credits | -$12,000 | Google Cloud migration credits |
| Other (net) | -$2,952 | Organic growth net of savings above the 3% target |
| **Total** | **+$197,795** | Budget $1,036,400; actual $1,234,195 |

## Decisions and actions requested

| Decision or action | Value | Basis | Owner | By |
| --- | ---: | --- | --- | --- |
| Approve a 1-year reservation for 240 CRM VMs | $28k/month | breaks even at 60% utilization; expected 100% | team-crm, FinOps | this week |
| Re-enroll non-production instances in the schedule | $12k/month | opt-outs since July | team-payments | 15 October |
| Renew the Compute Savings Plan at about $210/hour (today $220) | $768k/year net vs on-demand | usage without the data platform; 99% expected utilization | FinOps, Finance | before 31 January 2027 |
| Set a cost-per-conversation guardrail and alert for the AI assistant | risk control | unit-cost anomaly in August | team-ai | next review |
```

Reading it. Every figure traces to a table above: \$117k is the claims-analytics line's +\$104,769 less the −\$12,000 credit; \$23k is `lost` from `compute_commitments`; \$25k is the ai-assistant line; 1.6% and 1.7% are the backtest's one-month MAPE and WAPE; \$40k is the reservation's \$27,912 plus the schedules' \$12,000. The reconciliation line (not shown) reads: amortized \$1,234,195 − commitment cost amortized into usage \$165,658 + commitment fees billed \$165,658 = billed \$1,234,195. The totals agree in September only because the Azure reservation, paid in monthly installments of \$35,040 while amortized at \$1,152 a day, ended in August; earlier, billed minus amortized is +\$480 in 30-day months, −\$672 in 31-day months and +\$2,784 in February (exercise 12).

### How you would do it on real billing data

The page is the same; the inputs come from your warehouse and registers, and the reconciliation is to the central IT FinOps team's invoice-basis number, with scope and cut-off agreed in writing (47c.9, 47f.6). Keep an assumptions log and an accuracy record next to the page, because the first hostile question is "how good was last month's forecast?" (47f.5). Never put a projected saving in the realized number, label annualized figures, footnote the cost basis and data-through date on every chart, and present the three numbers before the tables.

## Exercises

Chapter 47g.5 has twelve exercises mapped to a representative multi-cloud FinOps analyst job description, with answers for seed 42. In short, with hints on where to look in the code:

1. **Reproduce September's total and split it into usage, one-time and credits, amortized and billed.** `Data.items[month]` holds `usage`, `one_time`, `credits`, `billed`, `effective` and `commitment_purchases`; `Data.month_total` adds the first three. Billed purchases are \$213,658: the \$48,000 subscription plus \$165,658 of commitment fees.
2. **Compare unallocated cost with tags alone, with aliases, and with the account map.** Call `allocate_row` on `D.rows_in("2026-09")`, then rewrite it to skip `normalize_tags`, then to skip the hierarchy. Expected: \$222,285 (18.0%), \$137,104 (11.1%), \$8,495 (0.69%).
3. **Find the cheapest path to 90% compliance.** `allocation_month(D, month)["issues"]` is cost by violation; fixing `application=payments` lifts compliance from 83.6% to 90.7%.
4. **Choose and defend a shared-cost method for the network pool.** `split_pool` and `FIXED_SPLIT`; the proxy is the compute-and-network `ListCost` footprint collected in `allocation_month`.
5. **Run the forecast with and without drivers.** `forecast_engine(D, D.last, date(2027, 9, 30), use_drivers=False)`: \$16,150,489 against \$13,225,493 with drivers.
6. **Recompute MAPE, WAPE and bias; turn off damping.** `error_stats(R["backtest"], "drivers", 1)` gives 1.63%, 1.68% and −0.91%; set `phi=1.0` in `growth_multiplier` and the 12-month total rises by \$211,220, September 2027 from \$1,189,968 to \$1,238,493.
7. **Write the three-sentence explanation of September.** Start from `compute_variance(D, "2026-09")["bridge"]` and the driver table in `cmd_summary`.
8. **Was February a drop?** January cost \$975,228 and February \$922,142, but per day \$31,459 against \$32,934: February has 28 days, and it also contained the NAT spike. `Data.month_total` and `days_in_month`.
9. **Tune the thresholds to an alert budget; write the ticket and the postmortem for the GPU cluster.** `SWEEP_RULES` and `compute_anomalies(D, rule)`; the loose rule's 10 false alerts over about 16 months is two a quarter, the medium rule's 2 are the Bedrock experiments. The cluster cost \$30,057 over 12 days and ran ten days after detection.
10. **Size the Savings Plan renewal and the new VM reservation.** `sp_sizing(D, D.last)["options"]` and `ri_sizing(D, D.last)`; then explain why overall ESR is only 5.7%.
11. **Score the savings methods and fix INIT-02.** `compute_savings(D, "2026-09")` and `counterfactual(...)` on `D.E[k]` instead of through the plan: \$111,866 on its own amortized cost against \$141,835 through the plan and a true \$136,652.
12. **Reconcile billed and amortized by month and rewrite the summary for two audiences.** `D.items[mo]["billed"] - D.items[mo]["effective"]` for each month: +\$480, −\$672, +\$2,784 in February, \$0 in September.

## Extending the lab

**Add a cloud.** Add an entry to `PROVIDERS` (billing account, sub-account type, region, negotiated discount), its name to `PROVIDER_ORDER` and `LATENCY_DAYS`, sub-accounts to `SUBACCOUNTS` and `ACCOUNT_MAP` (with a budget line and, for shared accounts, a pool), a tag set, and a few `series_spec` entries in `SERIES`. A SaaS data platform is realistic (FOCUS 1.3 publishers include Snowflake and Databricks). Everything downstream (`Data`, the budget, every analysis) is driven by these tables; run all eight commands and check that the waterfall, the bridge and the reconciliation still add up.

**Add a planted problem.** Append a dictionary to `INJECTED` with a `series` id, dates, `add_list_per_day`, a `kind` (usage, rate or unit-cost) and a `target` (`detector` or `savings-tracker`). `additive_list_usd` injects it, `truth_of` and `compute_anomalies` score it automatically. For a rate event, change a commitment's end date in `COMMITMENTS` or add a branch to `price_multiplier`; for a slow leak, add a branch to `initiative_multiplier`; for a planned event, add a row to `CALENDAR` with an `added_on` date and see whether triage labels it before or after detection. To add an initiative, append to `INITIATIVES` with a `method`, give it a branch in `initiative_multiplier` or `price_multiplier` keyed on its id so `true_savings` can switch it off, and the tracker scores it.

**Add a report.** Write `compute_x(D, ...)` returning a dictionary and `cmd_x(D, args)` printing it with `print_table` or `md_table`, then add the name to the loop and the dispatch dictionary in `main`. A unit-economics report (cost per transaction, per conversation, per document by month, from `D.E` and `D.drivers`) is a good first one.

**Other extensions from chapter 47g.6.** Redo the analyses in SQL (the chapter has a ten-line SQLite loader; the queries are in 47f.12); build the five executive charts of 47f.4; generate hourly rows for the Savings Plan's eligible series and re-size the renewal; apply the plan the way AWS does (highest savings percentage first); bill one provider in euros and separate FX in the bridge; re-cut the months to a 4-4-5 calendar; replace the statistical model with exponential smoothing or a regression on drivers, keeping the driver layer; change the seed or the injected sizes and watch precision, recall and the realized-to-true gap.

## Function-to-chapter map

| Area | Functions and constants | Chapter |
|---|---|---|
| Synthetic world | `PROVIDERS`, `SUBACCOUNTS`, `ACCOUNT_MAP`, `TAG_STANDARD`, the `T_*` tag sets, `DOW`, `SEASON`, `SERIES`, `DRIVERS`, `MIGRATION`, `COMMITMENTS`, `INITIATIVES`, `PIPELINE`, `CALENDAR`, `INJECTED`, `DATA_ARTIFACT`, `IMMATERIAL`, `ONE_TIME`, `OTHER_CREDITS`, `BUDGET_ASSUMPTIONS` | 47g.2 |
| Generator | `growth_factor`, `ramp`, `tags_for`, `initiative_multiplier`, `price_multiplier`, `additive_list_usd`, `simulate_drivers`, `make_row`, `generate_rows`, `true_savings`, `generate` | 47g.2, 47a.4 (the amortized row pattern) |
| Loading | `Data` (`.E`, `.L`, `.C`, `.Q` daily series; `.items` by month; `.OT` one-time; `.drivers`; `.budget`; `.true_savings`), `budget_line_of` | 47b.5–47b.6 |
| Forecast | `monthly_levels`, `fit_series`, `growth_multiplier`, `predict`, `sp_pool_cost`, `forecast_engine`, `build_budget`, `backtest`, `error_stats`, `rms_pct_error`, `compute_forecast`, `cmd_forecast`, `BACKTEST_ORIGINS` | 47c.2–47c.5, 47c.8, 47e.13, 47f.5 |
| Variance | `compute_variance`, `cmd_variance`, `context_notes`, `service_match` | 47c.6, 47c.7, 47c.9, 47c.10 |
| Anomalies | `DEFAULT_RULE`, `SWEEP_RULES`, `UNIT_SCOPES`, `robust_baseline`, `detect_series`, `group_events`, `attribute_event`, `truth_of`, `triage`, `detector_view`, `compute_anomalies`, `compute_unit_cost_anomalies`, `anomaly_cost_share`, `cmd_anomalies` | 47d.9–47d.16 |
| Allocation | `normalize_tags`, `tag_issues`, `is_taggable`, `allocate_row`, `allocation_month`, `split_pool`, `FIXED_SPLIT`, `compute_allocation`, `cmd_allocation` | 47d.1–47d.8 |
| Commitments | `sp_sizing`, `ri_sizing`, `compute_commitments`, `cmd_commitments` | 47e.1–47e.2 |
| Savings | `counterfactual`, `realized_by_day`, `compute_savings`, `cmd_savings` | 47e.9, 47e.12, 47e.13 |
| Summary | `cmd_summary`, `kmoney`, `skmoney`, `md_table` | 47f.1–47f.3, 47f.6 |
| Utilities | `daterange`, `ym`, `add_months`, `month_end`, `days_in_month`, `month_bounds`, `month_list`, `median`, `percentile`, `money`, `smoney`, `pct`, `spct`, `print_table`, `section`, `main` | |

## How it was tested

From a clean directory: `generate`, then each of the seven analysis commands, all exiting with status 0; two `generate` runs compared byte for byte (identical); a second seed (`--seed 7`) run through `anomalies`, `forecast` and `savings`; `variance` and `summary` for `--month 2026-08`; an AST scan for unused names; and the SQL of chapter 47f.12, run on SQLite 3.45 against the same CSV files, reproducing the Python results (budget by line, tag compliance 83.6%, ESR 9.6%, 0.0% and 1.9%, and the same 68 flagged anomaly days on usage rows). Every table in this README was pasted from a run with seed 42 on 4 October 2026.

## Limitations

- Daily grain only. Real commitment sizing needs hourly data, which gives lower floors than daily data.
- Savings Plan benefits are shared pro rata across eligible accounts. AWS applies a plan to the usage with the highest savings percentage first and, at equal percentages, to the usage with the lowest Savings Plans rate, so cost shifts between accounts differ in reality.
- The migration plan's increments are exactly what the generator adds, which flatters the backtest of the driver model; real engineering estimates miss.
- A subset of FOCUS columns, one currency (USD), no tax, no `InvoiceId`; `ServiceProviderName` stands in for the provider and publisher columns.
- The budget is produced by the lab's own forecast with the assumptions of late 2025; real budgets are negotiated.
- Anomalies and savings come with a ground-truth file; real ones are messier and nobody hands you the answers.

## License

The code is offered under the repository's MIT license (`LICENSE`); the book text is CC BY 4.0 (`LICENSE-CONTENT.md`).
