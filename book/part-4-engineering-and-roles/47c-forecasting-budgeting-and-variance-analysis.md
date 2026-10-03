# 47c. Forecasting, budgeting and variance analysis for multi-cloud spend

> **What you need to be able to say:** which forecasting method fits which horizon, and how each fails; what the native forecasts cannot do; how to build a driver-based forecast with a known-changes layer fed by Cloud Engineering, commitments and probability-weighted savings; how to express uncertainty and measure accuracy (the FinOps Foundation KPIs, MAPE, WAPE, bias, backtests); how to split a variance into rate, usage, mix and timing and write the commentary; how to tell a trend from noise and what each shape does to the forecast; how budgets, reforecasts and commitments fit the finance calendar; and how to reconcile with the central IT FinOps team so leadership sees one number. 47a has the finance vocabulary and cost metrics, 47b the data and SQL, 47d anomaly management, 47e the measurement of savings.

The running example continues from 47a: a business unit on AWS, Azure and Google Cloud with a 2026 cloud budget of \$29.40M (calendar fiscal year), phased at \$2.40M a month for January–September and \$2.60M for October–December. All figures are fictional, in thousands of US dollars (\$k) unless stated, on the net amortized basis (`EffectiveCost`) at the budget FX rate except where FX is called out.

## 47c.1 Three numbers, three jobs

- **The budget** is a commitment made months ago. Variance to budget tests whether the plan was right and holds owners accountable.
- **The forecast** is today's best estimate. Variance to forecast measures predictability, which finance needs for cash, for the full-year outlook and for any external guidance.
- **The actual** is the reconciled number, final only at about BD10 (47a.5).

A forecast is not a target. Two habits destroy it: anchoring to the budget ("we will land on budget" when the drivers say otherwise) and padding ("add 5% to be safe"). Both make it useless for decisions, and both show up in the accuracy log as bias. Forecast what you expect, show the uncertainty separately (47c.4), and let the budget conversation happen in the open.

Forecast what finance books: net amortized cost by cloud, cost center (or application) and month, with a separate cash view for upfront purchases and a tax line if finance wants one.

## 47c.2 Forecasting methods

### Granularity: daily for the current month, monthly beyond it

The current month needs **daily** data: where it will land depends on weekday and weekend patterns, incomplete recent days, charges that post on fixed days and anomalies with known start dates. Beyond it, **monthly** granularity is better: daily noise averages out, budgets and drivers are monthly, and long daily forecasts mostly forecast noise. AWS's forecast API makes the same split (three months daily, 18 months monthly). Phase monthly numbers by day type rather than by calendar days: a daily rate for weekdays and for weekend days, times the month's count of each. October 2026 has 22 weekdays and 9 weekend days, November 21 and 9, December 23 and 8. Where weekends cost 40% of a weekday (non-production schedules, business-hours workloads), phasing November at September's average daily rate overstates it by 2.4%, a large share of a 5% accuracy target.

### Basis: amortized, discount-adjusted

The FinOps Foundation's Run maturity for forecasting combines rolling, trend-based and driver-based methods on discount-adjusted amortized data. The reason is mechanical: billed cost jumps on the day an upfront commitment is bought, so a model trained on it learns spikes that will not recur, while amortized cost follows usage. Model the cash view separately, from the schedule of purchases and contract payments.

A useful refinement is to forecast volume and rate separately. Write the effective cost of any scope as

```
EffectiveCost = ListCost × (1 − d)
```

where `ListCost` (excluding purchase rows, 47a.4) measures usage at constant list prices and `d` is the effective discount from negotiated pricing and commitments. Forecast `ListCost` from history and drivers and `d` from the commitment plan and the contracts. A commitment purchase or expiry then changes `d` from a known date instead of distorting the usage history. In September the running example had about \$3,120k of list cost against \$2,549k of effective cost, an effective discount of 18.3%.

### The methods

| Method | How it works | Use it when | How it fails |
|---|---|---|---|
| Run-rate | Recent average per day × days in the period | Current-month landing; a first draft | Ignores trend, seasonality and known changes; one spike distorts it |
| Seasonal naive | Repeat the same period of the last cycle (same weekday last week, same month last year) | The baseline every other method must beat | Ignores growth; repeats last year's one-offs |
| Linear or log-linear trend | Fit cost = a + b·t, or log(cost) = a + b·t for constant percentage growth | Steady growth with 6–24 months of clean history | Breaks at step changes; extrapolates forever; log-linear compounds error at long horizons |
| Exponential smoothing (ETS): simple, Holt, Holt-Winters | Decaying weights; Holt adds a trend, Holt-Winters seasonality; a damped trend flattens long horizons | Monthly series with trend and seasonality; daily series with weekly seasonality | Slow to react to structural breaks; seasonal versions need two full cycles |
| ARIMA family, including regression with ARIMA errors | Models autocorrelation; with regressors, a dynamic regression on drivers | Stable series; drivers known in advance | Needs clean data; brittle at breaks; hard to explain to finance |
| Prophet-style additive models | Piecewise trend with changepoints, seasonality and holidays; tolerates missing data | Daily data with strong seasonality and several seasons of history | Extrapolates from the last changepoint; can chase a one-off |
| Machine learning (gradient-boosted trees, neural networks) | Learns from calendar, lag and driver features across many related series | Hundreds of related series with rich drivers | Overfits small data (36 monthly points is small); trees cannot extrapolate; opaque to finance |
| Driver-based | Fixed base + unit cost × volume per driver + known changes | Spend that follows the business; planning; explaining to finance | Wrong when the cost-driver relationship breaks or the driver forecast is wrong |

Cloud spend is hierarchical (cloud → account or subscription → service → resource), and forecasts made at different levels will not add up unless you reconcile them; *Forecasting: Principles and Practice* covers bottom-up, top-down and reconciled approaches. A practical split: forecast the 20 largest applications individually (often most of the spend), the long tail as one series, and reconcile to the cloud totals.

### Month-end landing from daily data: a worked example

On the morning of Wednesday 16 September 2026, data is complete through Monday 14 September. September 2026 starts on a Tuesday and has 22 weekdays and 8 weekend days.

- **Actual to date (1–14 September): \$1,175.2k.** Ten weekdays averaged \$86.0k and four weekend days \$71.0k (\$860.0k + \$284.0k = \$1,144.0k). On top of that pattern: \$15.0k of monthly fees posted on 1 September, and \$16.2k from a Savings Plan that expired on 6 September (on-demand rates cost \$1.8k a day more until its replacement starts on 16 September: 9 days × \$1.8k to date).
- **Naive run-rate:** \$1,175.2k ÷ 14 × 30 = \$2,518.3k.
- **Pattern-aware landing:** the remaining days, 15–30 September, are 12 weekdays and 4 weekend days: 12 × \$86.0k + 4 × \$71.0k = \$1,316.0k; plus one more lapse day (15 September) at \$1.8k; plus known one-offs outside the daily pattern: the AWS support fee for September (posting in early October; estimated from last month's ratio at \$45.0k) and a Google Cloud Marketplace renewal on 21 September (\$9.0k, from the contract calendar). Landing = \$1,175.2k + \$1,316.0k + \$1.8k + \$45.0k + \$9.0k = **\$2,547.0k**.

September closed at \$2,549.0k (the support fee came in at \$47.0k), so the pattern-aware landing missed by \$2.0k (0.08%). The naive run-rate came in \$30.7k (1.2%) low. It repeated the to-date one-offs on every remaining day (+\$34k) and missed that the second half held more weekdays (−\$9k), a net \$25k too high, but knew nothing of the support fee and the renewal (\$56k).

### The native forecasts and their limits

| | AWS Cost Explorer | Azure cost analysis | Google Cloud Billing reports |
|---|---|---|---|
| Horizon and granularity | Up to 18 months monthly or 3 months daily (since 19 November 2025) | The selected period | Forecasted cost when the report's date range ends in the future; the header shows the current month's forecasted total, including forecasted savings |
| Method and history | Uses up to 36 months of history (AWS's blog says 38); 80% prediction interval in the console; natural-language explanations in preview | Time-series linear regression; lookback of 28 days for forecasts up to 28 days, equal to the forecast length beyond that, capped at 90 days; at least 90 days of history recommended for an annual forecast; settles within a few days after reservation purchases | Not documented |
| API and options | `GetCostForecast`: cost metric (`AMORTIZED_COST`, `NET_AMORTIZED_COST`, `UNBLENDED_COST`, `NET_UNBLENDED_COST`, `BLENDED_COST`) or a usage metric, filters, billing views, prediction interval from 51% to 99% | Cost Management APIs | Budgets can alert on forecasted spend |

All three see one cloud, extrapolate history, know nothing about migrations, launches, purchases, renewals or price changes, and treat last month's one-off as signal; none works at your cost-center granularity or keeps an accuracy log. Use them as a sanity check: a gap of more than a few percent from your forecast should be explained by your known-changes register, or your model has a problem.

## 47c.3 Driver-based forecasting

A trend model answers "what happens if nothing changes?". A driver-based model answers the question finance and Business Planning ask, "what will cloud cost if the business does what the plan says?", and it is the only kind of forecast you can defend line by line.

### Drivers and unit costs

| Driver | Typical services it moves | Unit cost (fictional) | Who owns the driver forecast |
|---|---|---|---|
| Business volume (orders, transactions, API calls) | Compute, serverless, databases, data transfer | \$38 per 1,000 orders on the checkout platform | Business Planning |
| Active users or tenants | Compute and storage per tenant | \$0.42 per monthly active user | Product analytics |
| Environments | Non-production compute and databases | \$14k per non-production environment per month | Cloud Engineering |
| Data growth (TB stored, TB scanned) | Object storage, warehouses, backups | \$21 per TB-month across storage tiers | Data platform team |
| Engineering headcount | Sandboxes, CI runners, developer tooling | \$1.1k per engineer per month | Business Planning (headcount plan) |
| Launches, regions, markets | Step changes in everything above | Per-launch estimate from the known-changes register | Product and Cloud Engineering |
| AI usage (requests, tokens) | Model APIs and inference capacity | Cost per 1,000 requests (chapter 31) | Product telemetry |

Estimate each unit cost by regressing monthly effective cost on the driver over 12 months or more (a trend in the residuals means the unit cost is drifting), or from an engineer's bottom-up estimate for new systems. Refresh unit costs every quarter.

### Unit cost × volume: a worked example

Twelve months of history for the checkout platform fit monthly effective cost ≈ \$260k fixed + \$38 per 1,000 orders. Business Planning forecasts 9.20M orders for October:

```
October = 260 + 9,200 × 0.038 = 260.0 + 349.6 = $609.6k
+6% orders (9.752M) = 260 + 9,752 × 0.038 = 260.0 + 370.6 = $630.6k   (+$21.0k)
Sensitivity: about $3.5k per 1% of orders
```

Track cost per 1,000 orders every month. If total cost rises while unit cost stays flat, the business grew: a budget conversation, not an anomaly. If unit cost rises while volume is flat, efficiency slipped: a conversation with the owner.

### Bottom-up, top-down and the middle

Bottom-up (each owner forecasts their own spend) captures known changes and composition but is slow, and owners pad. Top-down (the total trend scaled by the plan's growth) is fast but misses changes in composition. In practice: top-down for the long tail, bottom-up for the largest applications and every known change, and a reconciliation of the two; investigate any gap above about 5%.

### The known-changes layer

The job description asks for planned workload changes, migrations, new infrastructure and roadmap items to be in the forecast before they reach the bill. That needs a structured intake with Cloud Engineering, not hallway conversations. Keep a **known-changes register**, one row per change (the same table can serve as the planned-change calendar that suppresses expected anomalies, 47d.14):

| Field | Example | Why it matters |
|---|---|---|
| ID, title and source | KC-031: data platform migration from a self-managed cluster to a managed service; design document link | Traceability and evidence |
| Engineering owner and finance contact | Data platform lead; IT Finance partner | Someone answers for the dates |
| Cloud, accounts, cost center | AWS, data production accounts, cost center 5300 | Allocation |
| Type | Migration, new infrastructure, decommission, scaling, price or contract change, commitment purchase, optimization | How it enters the forecast |
| Start date and ramp | 1 August 2026; new platform \$20k, \$45k, then \$60k a month | Phasing |
| Steady-state monthly cost | \$60k a month (effective) | The new run-rate |
| One-time costs | Data transfer and tooling during the migration | No surprise in month one |
| Decommission credit | −\$2.4k a day once the old cluster is deleted | Where the savings come from |
| Double-running period | Planned 1–15 September | The temporary bump |
| Decommission date (separate owner) | 15 September 2026 | Savings begin only when resources, snapshots and backups are deleted |
| Confidence | High 90% (in a sprint), medium 70% (planned and funded), low 30% (idea) | Probability weight |
| Status and last updated | In progress; updated 11 September | Stale entries flagged after 60 days |

Run the intake as a 30-minute weekly review. Agree a threshold above which a change must be logged (for example, \$5k a month), and make the forecast read directly from the register.

**Calibrate the register.** Record each change's planned and actual dates and costs. After two or three quarters you know, by change type and by team, how far dates slip and how far estimates miss. Decommissions in particular tend to run late, because nobody switches off the old system until they are sure of the new one. Apply the median slip to new entries unless the owner shows evidence, and say so in the methodology note. It is often worth more than a better statistical model, as the accuracy log in 47c.5 shows.

### Migrations and the double-running bump

A migration usually raises cost before it lowers it: the new platform ramps up while the old one keeps running for validation, and the old one is often switched off later than planned. The forecast must show the bump and the date the savings start. The data platform migration, as planned in the August reforecast (\$k; the old cluster costs \$2.4k a day):

| Month | Old cluster | New platform | Total with migration | Old cluster only (no migration) | Difference |
|---|---|---|---|---|---|
| August | 74.4 | 20.0 | 94.4 | 74.4 | +20.0 |
| September (old cluster off on 15 September) | 36.0 | 45.0 | 81.0 | 72.0 | +9.0 |
| October | 0.0 | 60.0 | 60.0 | 74.4 | −14.4 |
| November | 0.0 | 60.0 | 60.0 | 72.0 | −12.0 |
| December | 0.0 | 60.0 | 60.0 | 74.4 | −14.4 |

What happened: the cutover slipped, so the old cluster ran all of September (72.0, +36.0 against the plan) and was deleted at the end of 2 October, leaving two more days (4.8) and a final month of its snapshots (1.2) in October, +6.0 against the plan. The plan had a bump of \$29.0k in August–September (20.0 + 9.0) and fourth-quarter savings of \$40.8k (14.4 + 12.0 + 14.4). The slip raised the bump to \$65.0k (20.0 + 45.0) and cut fourth-quarter savings to \$34.8k (8.4 + 12.0 + 14.4). That is why the register carries the decommission date as its own field with its own owner.

Two more traps: a decommissioned platform covered by Reserved Instances or a Savings Plan leaves the commitment unused until it is exchanged, reused or expires, so record the net saving; and the migration's data transfer is a one-time cost in the month of the copy.

### Commitments and optimization savings in the forecast

**Planned commitment purchases** change the rate from a known date. The August reforecast assumes a one-year, no-upfront Compute Savings Plan at \$67 an hour from 1 December 2026. December has 744 hours, so the commitment is 744 × \$67 = \$49,848. At 98% utilization it covers usage worth \$48,851 ÷ 0.72 = \$67,849 at on-demand rates (a 28% discount), a net saving of \$67,849 − \$49,848 = **\$18.0k** in December. With no upfront payment, cash and amortized cost are the same; an all-upfront plan would add the full payment to the cash forecast in the purchase month.

**Optimization savings** enter probability-weighted, from the date they will be implemented, not the date they were approved. Use the pipeline stage as the default probability: identified 30%, owner agreed 60%, scheduled 75%, in progress 90%, done 100% (and then measured). The fourth-quarter pipeline:

| Initiative | Cloud | Full monthly saving | Start and ramp | Stage (probability) | Expected Oct | Expected Nov | Expected Dec | Expected Q4 |
|---|---|---|---|---|---|---|---|---|
| EC2 rightsizing, wave 2 | AWS | \$20.0k | 1 November; 50% in November | Scheduled (75%) | 0.0 | 7.5 | 15.0 | 22.5 |
| Azure Hybrid Benefit for SQL | Azure | \$12.0k | 1 November | Owner agreed (60%) | 0.0 | 7.2 | 7.2 | 14.4 |
| S3 lifecycle tiering | AWS | \$8.0k | 15 October (half month) | In progress (90%) | 3.6 | 7.2 | 7.2 | 18.0 |
| Total | | | | | 3.6 | 21.9 | 29.4 | **54.9** |

At full value the pipeline is worth \$74.0k in the quarter (4.0 + 30.0 + 40.0); 47c.4 uses the gap as a scenario. Three rules keep savings honest:

1. **Do not count a saving twice.** Rightsizing shrinks the usage commitments cover, so buy commitments after rightsizing, and de-duplicate the pipeline as AWS Cost Optimization Hub does (one action per resource).
2. **Measure realized savings against a counterfactual** (the old configuration at today's volume), not against last month's bill (47e.9, 47e.12).
3. **Fold completed savings into the baseline.** A done and measured initiative leaves the savings layer and becomes part of the run-rate, or it is counted twice.

### Putting the layers together

```
Forecast(month, scope) = baseline (trend on amortized history, excluding one-offs and the items below)
                       + Σ drivers (fixed base + unit cost × volume)
                       + Σ known changes × confidence (ramps, double-running, decommission credits, one-time costs)
                       − Σ optimization savings × probability
                       − commitment savings from planned purchases (from the start date)
                       + recurring fees and known one-offs (support, marketplace renewals)
```

AWS for October 2026, as rebuilt after the September close:

| Layer | \$k | Source |
|---|---|---|
| Baseline for all applications not listed below (Holt-Winters on amortized history) | 543.4 | Model |
| Checkout platform: \$260k + 9.20M orders × \$38 per 1,000 | 609.6 | Driver model and Business Planning |
| Data platform: new platform 60.0, old cluster residual 6.0 | 66.0 | Known change KC-031 |
| Search in a new region: ramp month 1 of 3, \$40k × 70% confidence | 28.0 | Known change KC-036 |
| S3 lifecycle tiering: \$4.0k × 90% | −3.6 | Savings pipeline |
| AWS support fee (from the support plan's pricing and the forecast usage) | 47.6 | Fees |
| **AWS October forecast** | **1,291.0** | |

## 47c.4 Scenario ranges, intervals and how to talk about uncertainty

A single number invites false precision. Give leadership a base case and a range, and say what would move it.

**Scenarios** capture the risks you can name. Each comes from the risk register with a trigger, a date and an owner. For the fourth quarter (base \$7,857k, built in 47c.10):

| Scenario | What changes | Q4 impact, \$k | Q4 total, \$k |
|---|---|---|---|
| Downside | Data platform cutover slips again, to 16 October: 15 days of the old cluster (36.0 instead of the base's 4.8) | +31 | |
| | Orders run 2.5% above the new forecast (0.025 × 28.85M orders × \$38 per 1,000) | +27 | |
| | The BigQuery dashboard fix slips to 1 December (October and November at the full +22 instead of +12 and +2) | +30 | |
| | The optimization pipeline realizes half its full value (37.0 instead of the expected 54.9) | +18 | |
| | **Downside total** | **+106** | **7,963** |
| Base | Drivers as forecast; known changes and savings probability-weighted | 0 | **7,857** |
| Upside | Orders 2% below forecast | −22 | |
| | Optimization pipeline at full value (74.0 instead of 54.9) | −19 | |
| | The \$67-an-hour Savings Plan bought on 1 November instead of 1 December (720 hours × \$67 = \$48,240, 98% utilized at a 28% discount) | −17 | |
| | **Upside total** | **−58** | **7,799** |

With nine months of actuals (\$22,050k), the full-year outlook is \$29,907k in the base case, \$30,013k in the downside and \$29,849k in the upside.

**Intervals from your own track record** capture the risks you cannot name. Seven of the last eight quarter-ahead forecasts of quarterly totals landed within ±2% (47c.5), so for the fourth quarter quote \$7,857k × (1 ± 0.02) = \$7,700k–\$8,014k as roughly an 80–90% band; eight quarters is too few to be more precise. The scenario range (\$7,799k–\$7,963k) sits inside it, which is normal: scenarios list known risks, while historical errors include the surprises. Quote the wider range for cash planning and the scenarios for decisions. AWS's console shows an 80% prediction interval for its own forecast; its API accepts any level from 51% to 99%.

**How to say it.** Lead with the base and the range, name the two biggest swing factors and the date each resolves: *"We expect \$7.86M for the fourth quarter. Named risks put it between \$7.80M and \$7.96M; our track record says plan cash for up to \$8.0M. The swing factors are the data platform cutover, which we will know by 16 October, and holiday order volumes, which we will know by mid-November."* Avoid percentages of percentages, avoid more than three scenarios, and never present the upside as the plan.

## 47c.5 Forecast accuracy

### The FinOps Foundation KPIs

The Forecasting capability defines:

```
Forecast Accuracy Rate (spend) = (Forecasted spend − Actual spend) / Forecasted spend
Forecast Accuracy Rate (usage) = (Forecasted usage − Actual usage) / Forecasted usage
Forecast Drift Rate            = (New forecast − Previous forecast) / Previous forecast
```

The Budgeting capability adds the percentage variance of budgeted versus forecasted spend, (budgeted effective cost − forecasted effective cost) ÷ budgeted effective cost, and the budget burn rate, actual spend per unit of time.

For September (forecast frozen in August, actuals final at BD10):

| Scope | Forecast | Actual | Accuracy rate (F − A) ÷ F |
|---|---|---|---|
| AWS | 1,260 | 1,318 | −4.6% |
| Azure | 820 | 776 | +5.4% |
| Google Cloud | 430 | 455 | −5.8% |
| **Total** | **2,510** | **2,549** | **−1.6%** |

Drift after the September reforecast (47c.10): October +0.08% (2,515 → 2,517), the fourth quarter +0.09% (7,850 → 7,857), the full year +0.15% (29,861 → 29,907). Budgeted versus forecasted spend: (7,800 − 7,857) ÷ 7,800 = −0.7% for the fourth quarter, (29,400 − 29,907) ÷ 29,400 = −1.7% for the year.

### Two sets of thresholds that measure different things

The FinOps maturity model gives forecast-to-actual variance examples of under 20% (Crawl), under 10% (Walk) and under 5% (Run); the Budgeting capability sets variance-from-actual targets of at most 20%, 15% and 12% (47a.2). They are different tests. A forecast is re-made every month, so a Run practice should land within 5% of it at a one-month horizon; a budget is fixed for a year, before the year's projects are known, so its tolerance is wider. Report both: the September forecast missed by 1.6% in total (Run territory) but by 4.6–5.8% per cloud (at the line between Walk and Run), while the year is tracking 1.7% over budget, well inside the 12% Run target.

### MAPE, WAPE, bias and a naive benchmark

```
MAPE = (1/n) × Σ |A_i − F_i| / A_i          mean absolute percentage error
WAPE = Σ |A_i − F_i| / Σ A_i                 weighted absolute percentage error
Bias = Σ (F_i − A_i) / Σ A_i                 negative = under-forecast
MASE = MAE of the forecast / MAE of a naive forecast    below 1 beats naive
```

Across the three clouds in September: MAPE = (58/1,318 + 44/776 + 25/455) ÷ 3 = (4.40% + 5.67% + 5.49%) ÷ 3 = **5.19%**; WAPE = (58 + 44 + 25) ÷ 2,549 = **4.98%**; bias = (2,510 − 2,549) ÷ 2,549 = **−1.53%**.

- **MAPE** weights a small cloud's miss like a large one's, is undefined when an actual is zero, and is asymmetric: an over-forecast can exceed 100% error, an under-forecast cannot (see the accuracy chapter of *Forecasting: Principles and Practice*). Use it to compare scopes of similar size.
- **WAPE** weights errors by spend, which is what finance feels: the headline metric.
- **Bias** shows direction. Always a little high means padding; always a little low, optimism. Either way the fix is in the process, not the model.
- **Total accuracy hides offsetting errors.** September's total missed by 1.6% while every cloud missed by about 5%, in different directions. Measure accuracy where you manage the work.
- **Beat naive or simplify.** If seasonal naive would have done as well, the model is not earning its complexity; MASE makes that explicit.

### Backtesting

Backtest with a rolling origin: for each of the last 12 months, rebuild the forecast as it would have been made then, from the data and the known-changes register as they stood (so keep versions of both), and record the error at horizons of one, three, six and twelve months. Compare each method with seasonal naive, pick per scope the lowest WAPE with acceptable bias, and size intervals from the error distribution. *Forecasting: Principles and Practice* suggests a test set of about 20% of the sample, at least as long as the longest horizon you need.

For the running example's total at a one-month horizon, September 2025 to August 2026, the accuracy rates were −2.6%, +1.9%, −0.8%, +2.4%, −1.5%, +0.6%, −2.1%, +1.2%, +0.3%, −1.0%, +2.8% and −0.9%. The mean is +0.03% (no bias), the mean absolute error 1.51%, and 10 of the 12 months fell within ±2.5%, the band to quote as roughly 80%. A seasonal-naive forecast over the same months had a mean absolute error of 4.8%, so the model is about three times better than naive. For quarterly totals forecast a quarter ahead, seven of the last eight landed within ±2%: longer horizons widen the error per month, but monthly errors partly offset in a quarterly total. That is the band 47c.4 uses.

### The forecast accuracy log

One row per scope, month and horizon, written at BD10 when actuals are final, with the forecast version it measures (here the August reforecast, frozen on 25 August, at a one-month horizon):

| Month | Scope | Forecast | Actual | (F − A) ÷ F | Main drivers | Reason codes | Action |
|---|---|---|---|---|---|---|---|
| Sep 2026 | Total | 2,510 | 2,549 | −1.6% | Double-running, Savings Plan lapse, BigQuery dashboards; offset by early Azure rightsizing | Timing, Rate, Usage | Decommission dates as a register field; commitment expiry alerts 60 days ahead |
| Sep 2026 | AWS | 1,260 | 1,318 | −4.6% | Double-running +36, Savings Plan lapse +18, orders +12, Graviton mix −8 | Timing, Rate, Usage, Mix | As above |
| Sep 2026 | Azure | 820 | 776 | +5.4% | Rightsizing a month early −30, FX −8, test environment removed −6 | Timing, Rate (FX), Usage | Ask owners for completion dates, not plans |
| Sep 2026 | Google Cloud | 430 | 455 | −5.8% | BigQuery dashboards +22, Marketplace renewal early +9, contract amendment −6 | Usage, Timing, Rate | Review dashboard refresh schedules with the analytics team |

Reason codes: **Timing** (a real change landed in a different month than forecast), **Usage** (a volume driver differed), **Rate** (prices, discounts, commitments, FX), **Mix**, **One-time** (an unforecast one-off), **Data** (late or restated data), **Model** (the method was wrong). After a few quarters the codes show where to invest: here, timing errors from the known-changes process cost more accuracy than the model did.

## 47c.6 Variance analysis

### Three variances, three audiences

- **Actual − budget:** accountability. Leadership and IT Finance read it against the operating plan.
- **Actual − forecast:** predictability. The forecaster owns it; it feeds the accuracy log.
- **Forecast − budget:** the early warning. It tells leadership, months ahead, how the year will end against plan, and it is where funding decisions happen.

In the running example, the August reforecast put September \$110k above the \$2,400k budget (order volumes above the budget assumption +45, an Azure analytics workspace for a compliance program approved in June +40, a Google AI pilot +16, the migration's planned bump +9). The actual added \$39k more. Of the \$149k overrun against budget, \$110k was known a month ahead: a forecast doing its job.

### Decomposition: rate, usage, mix, one-time and timing

Take out one-time and timing items first: charges that are real but will not recur (a one-off purchase, a migration copy) and changes that landed in a different month than forecast. Then decompose the rest. For each line *i* (an instance family, a SKU group or a service), with effective unit price *P*, quantity *Q*, forecast *f* and actual *a*:

```
Rate variance        = Σ (P_a,i − P_f,i) × Q_a,i
Usage variance       = Σ (Q_a,i − Q_f,i) × P_f,i
  of which volume    = (Q_a − Q_f) × P̄_f            Q = Σ Q_i,  P̄_f = Σ (Q_f,i × P_f,i) / Q_f
  of which mix       = Σ (Q_a,i × P_f,i) − Q_a × P̄_f
Check: rate + volume + mix = Σ P_a,i × Q_a,i − Σ P_f,i × Q_f,i
FX (part of rate)    = foreign-currency amount × (actual rate − budget rate)
```

The convention matters. These formulas price the quantity change at the forecast price and the price change at the actual quantity, so the joint effect of both moving lands in rate. Other conventions put it in usage or show it on its own line. Pick one, write it in the methodology note and keep it, or the same month will be explained differently next time.

Prices and quantities come from the data: `line_item_usage_amount` and amortized cost in CUR 2.0, `usage.amount_in_pricing_units` and cost plus credits in the Google export, `PricingQuantity` and `EffectiveCost` in FOCUS. When a line mixes units (a whole service, or an application), use list cost as the volume yardstick, with *L* the list cost excluding purchases and *d* the effective discount:

```
Usage variance (at list)  = (L_a − L_f) × (1 − d_f)
Rate variance (discount)  = (d_f − d_a) × L_a
Check: sum = L_a × (1 − d_a) − L_f × (1 − d_f)
```

### A worked single-service decomposition

One team's EC2 compute in September, two instance families (fictional effective rates):

| | Forecast hours | Forecast rate | Forecast cost | Actual hours | Actual rate | Actual cost |
|---|---|---|---|---|---|---|
| Graviton family | 40,000 | \$0.20 | \$8,000 | 55,000 | \$0.20 | \$11,000 |
| x86 family | 60,000 | \$0.25 | \$15,000 | 50,000 | \$0.26 | \$13,000 |
| Total | 100,000 | \$0.23 average | \$23,000 | 105,000 | | \$24,000 |

```
Rate   = (0.20 − 0.20) × 55,000 + (0.26 − 0.25) × 50,000          = +$500   (U)
Volume = (105,000 − 100,000) × 0.23                               = +$1,150 (U)
Mix    = (55,000 × 0.20 + 50,000 × 0.25) − 105,000 × 0.23
       = 23,500 − 24,150                                          = −$650   (F)
Total  = 500 + 1,150 − 650                                        = +$1,000 = 24,000 − 23,000
```

Read it as: the team ran 5% more hours (+\$1,150), a faster move to the cheaper Graviton family saved \$650, and the x86 rate rose by a cent an hour because part of that usage lost Savings Plan coverage during the lapse (+\$500).

### The three-cloud bridge for September 2026

| # | Cloud | Driver | Category | \$k | Recurs? |
|---|---|---|---|---|---|
| 1 | AWS | Data platform cutover slipped; the old cluster ran in parallel all month | One-time and timing | +36 | No; +6 in October |
| 2 | AWS | A Compute Savings Plan (\$175 an hour, 30% discount) expired on 6 September; its replacement started on 16 September: 240 hours × \$75 an hour at on-demand rates | Rate | +18 | No |
| 3 | AWS | Orders 0.32M above forecast × \$38 per 1,000 | Usage | +12 | While orders stay above plan |
| 4 | AWS | Graviton migration ahead of plan (instance mix) | Mix | −8 | Already in the November forecast |
| 5 | Azure | SQL Managed Instance rightsizing done on 1 September; forecast for 1 October | One-time and timing | −30 | Permanent; already in the forecast from October |
| 6 | Azure | €400k at an average \$1.08 against the \$1.10 budget rate | Rate (FX) | −8 | Depends on FX |
| 7 | Azure | Test environment removed after its project ended | Usage | −6 | Yes |
| 8 | Google Cloud | A new analytics dashboard refreshing every 15 minutes raised BigQuery scanning | Usage | +22 | Until fixed (target 10 October) |
| 9 | Google Cloud | Contract amendment effective 1 September lowered prices | Rate | −6 | Yes |
| 10 | Google Cloud | Marketplace annual renewal billed in September, forecast for October | One-time and timing | +9 | Reverses in October |
| | | **Total** (AWS +58, Azure −44, Google Cloud +25) | | **+39** | |

The waterfall:

```
Forecast, September                     2,510
  One-time and timing     +15    AWS double-running +36, Azure rightsizing early −30, Google renewal early +9
  Rate                     +4    AWS Savings Plan lapse +18, Azure FX −8, Google contract amendment −6
  Usage                   +28    Google BigQuery dashboards +22, AWS orders +12, Azure test environment −6
  Mix                      −8    AWS Graviton ahead of plan
Actual, September                       2,549   (+39, +1.6% against forecast; +149, +6.2% against budget)
```

Sort by size within each category, keep the bridge to ten lines or fewer, and never let an "other" line exceed materiality; if it does, the analysis is not finished.

### The commentary an executive reads

> **September cloud spend: \$2.55M, \$39k (1.6%) over forecast and \$149k (6.2%) over budget. Full-year outlook: \$29.91M, \$0.51M (1.7%) over budget, up \$46k from last month's outlook.**
>
> **Drivers against forecast.** (1) The data platform cutover slipped two weeks, so the old cluster ran all month (+\$36k); it was switched off on 2 October, so October carries only +\$6k. (2) A Savings Plan expired on 6 September and its replacement started on 16 September: ten days at on-demand rates cost \$18k, and renewals are now flagged 60 days ahead. (3) A new dashboard refreshing every 15 minutes raised BigQuery costs by \$22k; it moves to hourly refresh by 10 October. Offsets: Azure SQL rightsizing landed a month early (−\$30k, permanent from October) and a weaker euro lowered Azure costs in dollars (−\$8k).
>
> **Fourth-quarter risks and opportunities.** Downside up to +\$0.11M if the cutover slips again, holiday orders run 2.5% above forecast, the dashboard fix slips to December and savings realize at half value. Upside up to −\$0.06M if orders run 2% below forecast, savings realize in full and the planned Savings Plan is bought a month early.
>
> **Decision needed.** Approve buying the planned \$67-an-hour, one-year, no-upfront Savings Plan on 1 November instead of 1 December: about \$17k lower cost in the fourth quarter, no upfront cash.

That is the shape the job description asks for: two or three numbers, three drivers in business language, risks with dollar ranges, one decision. 47f.2–47f.3 develop the full one-page summary.

## 47c.7 Signal versus noise

The job description asks for "the judgment to distinguish meaningful trends from temporary fluctuations". Judgment is easier to defend when it follows a procedure, and more useful when every conclusion says what happens to the forecast. Anomaly detection and triage are in 47d.9–47d.12; this section is the forecaster's side.

### The procedure, with thresholds

Work down the table in order; most false alarms end in the first four rows.

| Question | How to check | Example threshold |
|---|---|---|
| Is it the calendar? | Per-day rates on amortized cost; same-weekday comparison; count weekdays, weekend days and holidays; 28-, 30- and 31-day months | Per-day change under 2% means calendar |
| Is the data complete? | Freshness per provider (47b.6); drop the last one to three days | Last 2 days (AWS, Google, Azure EA and MCA); last 3 days (Azure pay-as-you-go) |
| Is it a one-off or a posting artifact? | Charge category, bill type, purchases, renewals, support fees, credits, refunds, first-of-month amortization, restatements | Exclude and track separately |
| Is it rate, not usage? | Credits by type over time; the commitment expiry calendar; the effective discount *d* | A step in *d* with flat list cost on a known date: a lapsed commitment or an expired credit |
| Is it material? | Dollars and percent of the line | At least \$10k a month and 5% for a service; \$25k and 2% for a cloud; below that, note it and stop |
| Is it persistent? | Consecutive periods above the baseline | 3 consecutive days (or 5 of 7); 2 consecutive months |
| How broad is it? | Accounts, services and resources contributing | Top contributor above 80% of the change usually means an incident; many moving together, a business or price change |
| Is it backed by a driver, or did unit cost move? | Orders, users, data volume against cost; cost per unit of the driver | Unit cost within ±3%: growth. Up 5% or more for two months: efficiency |
| Is it outside normal variation? | Residual against a same-weekday baseline; native anomaly detectors | Beyond about 3 robust standard deviations, or a detector fired |
| Did someone change something? | Change log, deployments, infrastructure-as-code applies, the known-changes register | A dated change explains it: a known change arrived, possibly early or late |

Then decide the queue: *noise* (note it), *anomaly* (a ticket now, 47d.12–47d.13), *trend* (change the forecast and tell the owner and finance) or *watch* (a re-check date). For anything that changes the forecast, its shape decides how.

### The shape decides what the forecast does

| Shape | What it looks like | In the running example | What the forecast does |
|---|---|---|---|
| Spike | A day or a few, then back | A one-off data copy | Excluded from the baseline; a one-time line if material |
| Step | A new level from a date | The BigQuery dashboard (+\$0.7k a day from early September); the Savings Plan lapse | Re-based from the date, with an end date when a fix or replacement is scheduled, weighted by its probability |
| Ramp | A growing slope | The migration build-out; a storage leak | A known change with its ramp and its cap, or a changed growth term; never left for a trend model to extrapolate |
| Seasonal | Recurs on the calendar | The fourth-quarter peak; month-end batch jobs | A seasonal index or a calendar profile, compared year over year |

### Statistics rank; materiality and persistence decide

A change can be statistically striking and immaterial (a \$300 step in a quiet series), or material and statistically invisible (a \$20k-a-month drift spread across thirty days and ten services). Use statistics to rank signals and set alert thresholds; decide on materiality, persistence and driver backing. Two tests cover the gaps a daily detector leaves:

- **Slow drifts.** Every week, compare the last four weeks' cost per day, divided by its driver, with the four weeks before, and flag two consecutive increases above a few percent. A leak of 2% a week shows as +8% at the first check, while a daily detector with a dollar floor may never fire (47d.11).
- **Regression to the mean.** Never reforecast from one extreme month; the month after a spike usually looks like a decline. Re-base on a level that has held for two periods, or on a dated change that explains it.

### Five examples

1. **February spend is 9.7% below January. Noise.** Per day it is flat: February has 28 days and January 31, and 28 ÷ 31 = 0.903. The monthly number fell; nothing changed. The exception is storage billed per GB-month: its daily cost is about 11% higher in February for the same data, so normalize storage by month length before comparing days (47b.11).
2. **Yesterday's Azure spend is 35% below the day before. Noise.** EA and MCA data arrives 8–24 hours late, so yesterday is incomplete; Azure's own anomaly detection waits about 36 hours for the same reason. Re-check in 48 hours.
3. **The daily amortized chart shows a \$40k spike on every 1st. Noise for trend purposes.** Cost Explorer's daily amortized view puts unused reservation fees on the first of the month, and monthly fees post that day too. The unused part is real waste: it belongs in the commitment review, not the anomaly queue.
4. **Storage cost in one account has risen 2% a week for eight weeks while data ingested is flat. Trend (a ramp).** It is persistent and not driver-backed (cost per TB ingested is rising), and it comes from one account's snapshots and log retention. That is a leak: an owner, a ticket, and a forecast that carries it, capped at the fix date.
5. **Compute cost has risen 6% a month for three months, orders have risen 6% a month, and cost per 1,000 orders is flat. Trend (growth).** Persistent, broad and driver-backed: update the forecast through the driver model and raise the budget conversation; do not open an anomaly ticket.

## 47c.8 Budget cycles

### Annual planning

For a calendar fiscal year, a typical sequence is: baseline and driver assumptions in July and August; Cloud Engineering's roadmap and known changes, announced price changes and the commitment strategy (including any enterprise agreement or consumption commitment renewal) in September; a draft by cloud, cost center and month in October; review with IT Finance and leadership in November; approval in December; budgets loaded into AWS Budgets, Azure budgets, Google Cloud budgets and the dashboards in January. Start from the exit run-rate, not the year's average.

Two practices prevent a year of false variances:

- **Phase the budget by month from the forecast, not by dividing by twelve.** Seasonality, ramps and known changes belong in the phasing; the running example's \$2.60M a month for October–December reflects a seasonal peak that a flat \$2.45M would have reported as an overrun every fourth-quarter month.
- **Show targets separately from forecasts.** If leadership adds an efficiency target that no identified initiative supports (say −3%), put it in the budget as a visible "unidentified savings" line, so the commentary can say how much of the gap is the target not yet met instead of hiding it inside every team's numbers.

### Quarterly reforecasts and rolling forecasts

Formal reforecasts usually follow the quarter: 3+9 (three months of actuals and nine of forecast), 6+6 and 9+3. Present each as a bridge from the previous forecast, line by line, so drift is explained rather than discovered. A **rolling forecast** always looks 12–18 months ahead and is refreshed every month regardless of the fiscal year; it is what the FinOps Foundation describes at Walk and Run maturity, and it matches the 18-month horizon AWS now offers natively.

### Aligning with IT Finance and Business Planning

- **One assumptions register,** shared with IT Finance and Business Planning: driver values (orders, users, data volume), the FX budget rate, announced price changes, contract terms, headcount, launches and the commitment plan, each with an owner and a date.
- **One calendar:** when Business Planning delivers drivers, when the cloud forecast is due, when the reforecast is reviewed.
- **Funding decisions.** A project funded after the budget was set enters the forecast as a known change with its funding reference. Finance may move budget to it through a formal transfer or record an approved overrun. Track approved overruns separately, so the commentary can say how much of a variance was decided rather than discovered: in the running example, \$56k of September's \$110k forecast-over-budget gap came from projects approved after the budget (the Azure compliance workspace, the Google AI pilot); the rest was order growth above the plan's assumption and the migration's planned bump.

### The month-end reforecast

After each close (around BD6–BD9): roll the actuals in, update the current quarter month by month, re-weight known changes and savings, write the drift bridge, update the full-year outlook, and freeze next month's forecast on a fixed date (for example, the last week of the month), so accuracy is always measured against a known version.

### Commitments and contracts in the budget

- **P&L and cash are different lines.** A three-year, all-upfront commitment of \$1.08M is \$30k a month in the P&L budget for 36 months and \$1.08M of cash in the purchase month. Budget the first; plan the second with treasury.
- **Upfront or monthly is a cost-of-capital decision.** Suppose (illustrative prices) the same commitment costs \$31,500 a month for 36 months if paid monthly, \$1.134M in total. Paying \$1.08M upfront saves \$54,000, an implied return of about 3.2% a year on the cash. If treasury's cost of capital is 8%, the monthly stream is worth about \$1.01M today, so paying monthly is cheaper. Ask treasury for the rate before you recommend a payment option.
- **Decide who gets the savings.** Team budgets at effective rates pass commitment savings to teams through amortization; at on-demand rates, the central team keeps them on a separate line. Match the chargeback policy, or a central purchase produces favorable variances in teams that did nothing.
- **Put expiries and renewals in the forecast with dates.** A commitment that expires reverts its covered usage to on-demand rates the next hour; September's \$18k lapse is the example. Track every expiry in the commitments register and alert 60 days ahead.
- **Size conservatively, because mistakes are hard to undo.** AWS returns are limited to small plans within seven days of purchase, Azure reservations bought from 1 February 2027 cannot be exchanged where savings plans cover the service, and Google commitments cannot be canceled (47e.1).
- **Track enterprise commitments against the budget.** EDP or PPA, MACC and Google Cloud commitments have drawdown targets; a budget cut or a successful optimization program raises shortfall risk (47a.3). Align renewal negotiations with the planning calendar, so the next commitment is sized from the new plan, not the old run-rate.

## 47c.9 Reconciling with the central IT FinOps team

The job description asks you to coordinate with a central IT FinOps team, which tracks spend at the parent-IT level, so that leadership never sees conflicting numbers. Two competent teams looking at the same bill will still produce different totals unless they agree on six things:

| Source of difference | Business unit (typical) | Central team (typical) | How to close it |
|---|---|---|---|
| Metric | Effective (net amortized) cost | Billed cost, to match invoices | Publish both; agree which one each report uses |
| Scope mapping | The business unit's own list of accounts, subscriptions and projects | The parent's mapping table | One mapping table with effective dates, owned by one team and signed off by the other |
| Shared costs | Excluded, because the unit cannot control them | Allocated from the parent (support, shared networking, security tooling) | Show shared costs as a separate "allocated from parent" line |
| Timing cut-off | Final at BD10 | Snapshot at BD3 | One cut-off; later changes become a prior-period adjustment next month |
| FX | Monthly average rate | Month-end spot rate | One rate table from treasury |
| Credits, refunds, tax | Credits in the month received; tax excluded | Varies | Write it down |

**Build the bridge one definition at a time.** Start from one total, switch one definition, recompute from the same data, record the change, and move to the next, in a fixed order (here: metric, FX, scope, shared costs, timing). Built this way, the lines always sum to the gap, an interaction (a euro-billed account that also changes scope) lands in whichever line comes later, and next month's bridge is comparable. A bridge assembled from two independent calculations rarely sums, and its "other" line becomes the argument.

### A reconciliation bridge for September

| Step | \$k | Explanation |
|---|---|---|
| Business unit, September | 2,549 | Effective cost, monthly-average FX, business-unit scope, final at BD10 |
| Metric | +58 | The central team reports billed cost: it includes a \$120k Azure reservation bought upfront on 14 September in full, and excludes the \$62k of prepaid-commitment amortization that effective cost carries (including \$5.6k for the new reservation: 408 hours of a one-year term ÷ 8,760 hours × \$120k). The business unit's replacement Savings Plan is no-upfront, so it adds nothing here |
| FX | +2 | The euro billing profile converted at the month-end spot rate (\$1.085) instead of the monthly average (\$1.08): €400k × \$0.005 |
| Scope | +31 | Two shared data-lake accounts that the central mapping assigns to this business unit and the business unit's mapping assigns to the parent's shared platform |
| Shared costs | +24 | A share of enterprise support and of the shared network hub, allocated by the central team |
| Timing | −18 | The central team's BD3 snapshot missed \$11k of Azure corrections posted through day 5 and \$7k of AWS support fee above its estimate |
| Central IT FinOps team, September | 2,646 | |

Every line is legitimate; none is an error. The problem is only that nobody wrote the bridge before leadership saw both numbers. Once it exists, most lines can be removed by agreement, and the rest become labeled lines in both reports.

### The single-source-of-truth agreement

One page, signed by the business unit's FinOps analyst, the central IT FinOps lead and the IT Finance partner:

1. **Data.** Both teams query the same FOCUS-normalized tables (47b.6); no private copies for official numbers.
2. **Scope.** The central team owns the mapping table; the business unit signs off changes, which take effect at month boundaries.
3. **Metrics.** Effective cost excluding tax for performance and showback; billed cost for invoice and cash reporting; both published monthly, by name.
4. **Shared costs.** Allocated by the central team under published rules, shown on a separate line in business-unit reports.
5. **Commitments.** Amortized to the consuming accounts; the purchase decision and its cash shown by the central team.
6. **Cut-offs.** Preliminary at BD5, final at BD10; later changes post as prior-period adjustments.
7. **FX.** Treasury's monthly average rates for actuals; the budget rate for budgets and forecasts.
8. **Reconciliation.** A bridge signed by both teams by BD8; unexplained differences above the larger of 0.5% or \$10k escalated.
9. **Change control.** Definition changes announced a month ahead; restated history flagged.
10. **Escalation.** Unsettled disagreements go to the IT finance director, with the bridge attached.

## 47c.10 A worked end-to-end month: September 2026

**The forecast (late August).** The August reforecast sets September at **\$2,510k**: AWS 1,260, Azure 820, Google Cloud 430. That is \$110k above the \$2,400k budget (AWS 1,206, Azure 780, Google Cloud 414) because of order volumes above the budget assumption (+45), the Azure compliance workspace approved in June (+40), the Google AI pilot (+16) and the migration's planned bump (+9). The forecast is frozen on 25 August for accuracy measurement.

**During the month.**

| Date | Signal | Source | What the analyst did |
|---|---|---|---|
| Thursday 3 September | Azure SQL Managed Instance down about \$1k a day from 1 September | Daily review, after Azure's data delay | Owner confirmed the rightsizing planned for 1 October was done early: timing, favorable |
| Tuesday 8 September | EC2 compute up \$1.8k a day on 6 and 7 September, list cost flat | Daily rate check (effective discount down) | Root cause the same day: an expired Compute Savings Plan. Replacement approved from 16 September; an expiry calendar added to the commitments register |
| Wednesday 9 September | BigQuery up about \$0.7k a day | Google Cloud anomaly detection | A new dashboard refreshing every 15 minutes; fix promised for 10 October |
| Friday 11 September | Data platform cutover moved to early October | Known-changes intake | Old cluster keeps running, +\$2.4k a day for the rest of the month; register updated |
| Wednesday 16 September | Landing estimate \$2,547k (+\$37k, +1.5%) | Landing model (47c.2) | Landing note to IT Finance and the business unit leader with the four drivers |

**The close.**

- **BD1 (Thursday 1 October): flash \$2,547k**, with 30 September estimated from the weekday pattern and the AWS support fee estimated at \$45k.
- **BD3: accrual.** IT Finance books \$2,485k of usage charges on the billed basis, excluding prepaid purchases. The \$120k Azure reservation bought on 14 September is booked as a prepaid asset, and the \$62k of prepaid amortization comes from the prepaid schedule, so September's expense totals \$2,547k.
- **BD5: preliminary actuals \$2,547k** and the draft bridge, reviewed with the owner of each line.
- **BD6–BD7:** the AWS support fee posts at \$47k: **\$2,549k**. The executive summary goes out (47c.6). October will carry a \$2k accrual true-up.
- **BD8:** reconciliation with the central IT FinOps team, \$2,549k against \$2,646k, bridged and signed (47c.9).
- **BD10:** final actuals locked; four rows added to the accuracy log (47c.5); chargeback file sent.

**The variance.** +\$39k against forecast (+1.6%) and +\$149k against budget (+6.2%), decomposed into one-time and timing +15, rate +4, usage +28 and mix −8 (47c.6).

**The reforecast (BD6–BD9).** Each change to the fourth quarter traces back to a line in the bridge or to a new driver value:

| Month | Cloud | Previous | Changes | New | Reason |
|---|---|---|---|---|---|
| October | AWS | 1,280 | +13, +6, −8 | 1,291 | Orders forecast raised from 8.86M to 9.20M (0.34M × \$38 per 1,000); old cluster ran to 2 October plus a final month of snapshots; Graviton migration ahead of plan |
| October | Azure | 790 | −6 | 784 | Test environment removed |
| October | Google Cloud | 445 | −9, −6, +12 | 442 | Marketplace renewal already billed in September; contract amendment; BigQuery dashboard until the fix (70% chance of the fix on 10 October: 0.7 × \$7.1k + 0.3 × \$22k ≈ \$12k) |
| **October** | **Total** | **2,515** | **+2** | **2,517** | Drift +0.08% |
| November | AWS | 1,340 | +14 | 1,354 | Orders 9.18M → 9.55M |
| November | Azure | 800 | −6 | 794 | Test environment |
| November | Google Cloud | 490 | −7, +2 | 485 | Contract amendment; the 30% chance the dashboard fix slips into November |
| **November** | **Total** | **2,630** | **+3** | **2,633** | |
| December | AWS | 1,390 | +15 | 1,405 | Orders 9.71M → 10.10M |
| December | Azure | 810 | −6 | 804 | Test environment |
| December | Google Cloud | 505 | −7 | 498 | Contract amendment |
| **December** | **Total** | **2,705** | **+2** | **2,707** | |
| **Fourth quarter** | **Total** | **7,850** | **+7** | **7,857** | Drift +0.09%; still includes the \$54.9k probability-weighted savings pipeline and the 1 December Savings Plan (−\$18k) |

The full-year outlook moves from \$29,861k to **\$29,907k** (+\$46k: September's +\$39k and the fourth quarter's +\$7k), \$507k (1.7%) over the \$29,400k budget, with a range of \$29,849k–\$30,013k from the scenarios in 47c.4.

Notice what the totals hide: October's total moved by \$2k, but seven separate changes moved underneath it, in both directions. A reviewer who sees only the total learns nothing; a reviewer who sees the table can challenge each line.

**The process changes the month produced.** Commitment expiries now raise an alert 60 days ahead; the known-changes register has a decommission date with its own owner; the support-fee accrual uses the support plan's pricing instead of last month's ratio; and the analytics team reviews dashboard refresh schedules before launch. The next accuracy log will show whether they worked.

**Interview line:** *"I forecast net amortized cost bottom-up for the big applications and top-down for the tail, with a known-changes register fed by engineering and calibrated against how late changes really land, probability-weighted savings and dated commitments, and I quote a base case with a range. Every month I split the variance into rate, usage, mix and timing, log accuracy by cloud as well as in total, and reconcile with the central team through a bridge built one definition at a time, so leadership hears one number and the two or three things that moved it."*

## Sources

- [FinOps Foundation: Forecasting capability](https://www.finops.org/framework/capabilities/forecasting/) (definition, maturity, Forecast Accuracy Rate, Forecast Drift Rate; accessed 2 October 2026)
- [FinOps Foundation: Budgeting capability](https://www.finops.org/framework/capabilities/budgeting/) (variance targets of 20%, 15% and 12%; budgeted versus forecasted variance; burn rate; accessed 2 October 2026)
- [FinOps Foundation: Maturity model](https://www.finops.org/framework/maturity-model/) (forecast variance examples; accessed 2 October 2026)
- [FinOps Foundation: Planning & Estimating capability](https://www.finops.org/framework/capabilities/planning-estimating/) and [Invoicing & Chargeback capability](https://www.finops.org/framework/capabilities/invoicing-chargeback/) (accessed 2 October 2026)
- [Rob J Hyndman and George Athanasopoulos, *Forecasting: Principles and Practice*, 3rd edition](https://otexts.com/fpp3/) (exponential smoothing, ARIMA, dynamic regression, hierarchical forecasting; free online) and its chapter on [evaluating point forecast accuracy](https://otexts.com/fpp3/accuracy.html) (MAPE limitations, scaled errors, test-set size) (accessed 2 October 2026)
- [Prophet documentation](https://facebook.github.io/prophet/) (additive model with trend changepoints, seasonality and holidays; accessed 2 October 2026)
- AWS: [Cost Explorer 18-month forecasting and AI-powered explanations](https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/) (19 November 2025), [GetCostForecast API reference](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostForecast.html), [Cost Explorer advanced options](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-advanced.html) (daily amortized view) and [returning a Savings Plan](https://docs.aws.amazon.com/savingsplans/latest/userguide/return-sp.html) (accessed 2 October 2026)
- [AWS blog: the Cost Efficiency metric](https://aws.amazon.com/blogs/aws-cloud-financial-management/measuring-cloud-cost-efficiency-with-the-new-cost-efficiency-metric-by-aws) (Cost Optimization Hub de-duplication; November 2025)
- Microsoft Learn: [cost analysis and forecasting](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/quick-acm-cost-analysis) (linear regression, lookback periods), [understand Cost Management data](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-cost-mgt-data) (data latency), [anomaly detection](https://learn.microsoft.com/en-us/azure/cost-management-billing/understand/analyze-unexpected-charges) and [reservation exchanges and refunds](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations) (accessed 2 October 2026)
- Google Cloud: [Cloud Billing reports](https://docs.cloud.google.com/billing/docs/how-to/reports) (forecasted costs, Pacific Time days) and [billing cycles](https://docs.cloud.google.com/billing/docs/how-to/billing-cycle) (late-reported usage; accessed 2 October 2026)
- [FOCUS use case: forecast amortized costs month over month](https://focus.finops.org/docs/use-cases/v1-4/forecast-amortized-costs-month-over-month-based-on-historical-trends-2/) (accessed 2 October 2026)
