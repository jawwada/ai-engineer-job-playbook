# FinOps analyst lab

A one-file lab for the work a multi-cloud FinOps analyst does every month: forecasting, variance analysis, anomaly detection, allocation, commitment management, savings tracking and executive reporting. It generates 18 months of synthetic, FOCUS-like daily cost data for a fictional business unit on AWS, Microsoft Azure and Google Cloud, with planted problems, and then runs each analysis with printed tables you can check by hand.

Chapter 47g of the book (`book/part-4-engineering-and-roles/47g-finops-analyst-hands-on-lab.md`) explains the data, the methods and the exercises; chapters 47d, 47e and 47f use the lab's numbers.

Everything is fictional: the company, accounts, prices and events. Unit prices are illustrative, except NAT gateway (\$0.045 per hour and per GB) and public IPv4 (\$0.005 per hour), which match published AWS us-east-1 prices in October 2026. The data imitates FOCUS columns but is not a conformant FOCUS dataset.

## Requirements and quick start

Python 3.10 or later, standard library only. No installation.

```bash
cd labs/finops-analyst
python3 finops_lab.py generate            # writes data/ (24,842 cost rows, about 10 MB)
python3 finops_lab.py summary             # one-page Markdown executive summary
```

The data is deterministic for a given seed (`--seed`, default 42): two runs produce byte-identical files. All eight subcommands together take about 13 seconds on a laptop (`generate` about 4 of them, because it also regenerates the data once per savings initiative to compute the true savings).

| Command | What it does | Book section |
|---|---|---|
| `generate [--out data] [--seed 42]` | Writes the data set: cost rows, business drivers, budget, tag standard, account map, change calendar, commitment inventory, initiative register and the ground truth | 47g.2 |
| `forecast [--data data]` | 12-month forecast with a rolling-origin backtest (MAPE, WAPE, bias), driver adjustments and a range | 47c.2–47c.5, 47g.3, 47f.5 |
| `variance [--month 2026-09]` | Budget vs forecast vs actual, by budget line, with a volume, mix, rate and one-time bridge | 47c.6, 47g.3 |
| `anomalies` | Same-weekday median and MAD detector, triage, unit-cost detection, precision and recall against the ground truth, threshold sweep | 47d.11 |
| `allocation [--month 2026-09]` | Tag compliance, violations by cost, allocation waterfall, shared-cost methods, fully loaded showback, trend | 47d.1–47d.8 |
| `commitments [--month 2026-09]` | Coverage, utilization, waste, three ESR definitions, Savings Plan renewal sizing with sensitivity, reservation sizing | 47e.2 |
| `savings [--month 2026-09]` | Projected vs realized savings with two counterfactual methods, scored against the true savings; decay detection; pipeline | 47e.12 |
| `summary [--month 2026-09]` | The one-page executive summary | 47f.3 |

`--data` defaults to `data` and `--month` to `2026-09` for every analysis command.

## The data set

| File | Contents |
|---|---|
| `focus_costs.csv` | 24,842 daily rows from 1 April 2025 to 30 September 2026, 31 FOCUS-like columns: billing account, billing and charge periods, `ServiceProviderName`, `SubAccountId`/`Name`/`Type`, `RegionId`, `ServiceName`, `ServiceCategory`, `ChargeCategory` (Usage, Purchase, Credit), `ChargeClass`, `ChargeFrequency`, `ChargeDescription`, `PricingUnit`, `PricingQuantity`, `ListUnitPrice`, `ContractedUnitPrice`, `ListCost`, `ContractedCost`, `EffectiveCost`, `BilledCost`, `BillingCurrency`, the `CommitmentDiscount*` columns (Used and Unused) and `Tags` as JSON |
| `business_metrics.csv` | Daily volumes per application: transactions, conversations, sessions, claims, documents |
| `budget.csv` | The 2026 budget by month, provider and budget line, built in late 2025 with that time's assumptions |
| `account_map.csv` | What each of the 13 sub-accounts is for: kind (single, multi, shared), default application, environment, cost center, owner, budget line, shared pool |
| `tag_standard.json` | Required keys, allowed values, case rule, sources of truth, alias tables |
| `planned_changes.csv` | The change calendar: load test, migration, annual renewal, decommissions, commitment expiry, each with the date it was added |
| `commitments.json` | AWS Compute Savings Plan, two Azure VM reservations (the second expires on 31 August 2026 and is not renewed), a Google resource-based CUD |
| `initiatives.json` | Four implemented initiatives with projected savings and measurement methods; five pipeline opportunities with probabilities |
| `ground_truth.json` | The injected anomalies, the data artifact, the planned events, the migration plan, the budget assumptions, and the true monthly saving of each initiative (the data regenerated with that initiative switched off, same random draws). Used only for scoring; a real analyst has no such file |

Commitment rows follow the amortized pattern: covered usage has `BilledCost` 0 and `EffectiveCost` at the committed rate; unused commitment appears as `CommitmentDiscountStatus = Unused` rows; the monthly fee is a `Purchase` row with `BilledCost` equal to the fee and `EffectiveCost` 0.

### The fictional business unit

| Sub-account | Provider | Kind | What runs there |
|---|---|---|---|
| aws-management | AWS | shared | Governance services; owns the Compute Savings Plan; a one-time marketplace subscription |
| aws-payments-prod, aws-payments-nonprod | AWS | single | The payments API (EC2, RDS, S3, CloudWatch, data transfer) |
| aws-data-platform-prod | AWS | multi | The claims-analytics platform (EMR, EC2, S3) being migrated to Google Cloud |
| aws-shared-network | AWS | shared | NAT gateways, Transit Gateway, public IPv4 addresses |
| aws-ml-sandbox | AWS | multi | GPU experiments, notebooks, model inference trials |
| az-crm-prod, az-crm-dev | Azure | single | The customer portal (VMs, Windows licenses, SQL, storage, Log Analytics, App Service) |
| az-security-shared | Azure | shared | Defender, Sentinel, Key Vault |
| az-ai-assistant-prod | Azure | single | The AI assistant (model tokens, search, App Service) |
| gcp-analytics-prod, gcp-analytics-dev | Google Cloud | single | BigQuery, Compute Engine, Cloud Storage and, from July 2026, Dataproc: the migration target |
| gcp-docai-prod | Google Cloud | single | Document intelligence (Gemini API, Cloud Run, Cloud Logging) |

### What is planted in the data

- Weekday and yearly seasonality, different per workload; growth from 0.3% to 6% a month; storage priced per GB-month, so its daily cost depends on the length of the month.
- A migration with double-running: Google Cloud build-out from 1 July to 15 September 2026; AWS compute off on 1 November, storage deleted on 1 December (in the forecast horizon).
- Commitments with negotiated discounts (AWS 6%, Google 4%), a Savings Plan shared across accounts, and a VM reservation that lapses on 31 August 2026.
- Seven injected anomalies (a NAT spike, a runaway query, a forgotten GPU cluster, a logging explosion, a prompt change that raised tokens per conversation, an expired reservation, and a savings decay that only the savings tracker catches), one data-lag artifact, one change below the dollar threshold, and three planned events.
- Tags with typical violations (unknown values, wrong case, misspelled keys, missing keys, untagged storage) and remediation dates.
- Four optimization initiatives with realistic results (over-delivery, ramp-up, decay, one on usage covered by the shared Savings Plan), five pipeline opportunities, migration credits, a service credit and a \$48,000 one-time marketplace charge.
- A budget built from October 2025 data with an old migration date, an AI growth cap and a 3% efficiency target.

## Exercises

Chapter 47g has twelve exercises mapped to a representative multi-cloud FinOps analyst job description (anonymized), with expected answers. In short:

1. Reproduce September's total and split it into usage, one-time and credits.
2. Compare unallocated cost with tags alone, with aliases, and with the account map.
3. Find the cheapest path to 90% tag compliance.
4. Choose and defend a shared-cost method for the network pool.
5. Run the forecast with and without drivers and explain the difference.
6. Recompute MAPE, WAPE and bias from the backtest; turn off trend damping and compare.
7. Write the three-sentence explanation of September's variance.
8. Decide whether February 2026 was a drop or noise.
9. Tune the anomaly thresholds to an alert budget; write the ticket and the postmortem for the GPU cluster.
10. Size the Savings Plan renewal and the new VM reservation.
11. Score the savings methods against the truth and fix the decaying initiative.
12. Reconcile billed and amortized cost by month and rewrite the summary for two audiences.

## Expected outputs (seed 42, abridged)

### generate

```
Wrote 24,842 cost rows (24,784 usage rows) for 2025-04-01 to 2026-09-30 into data/

Month    EffectiveCost (amortized)
-------  -------------------------
2025-04                   $837,455
...
2026-07                 $1,060,171
2026-08                 $1,126,668
2026-09                 $1,234,195
```

### forecast

```
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
...
2027-09   $1,034,112         $151,185       +$621     +$48,000      -$43,950   $1,189,968  $1.07M - $1.31M
Total    $11,625,598       $2,048,298     +$1,878     +$48,000     -$498,281  $13,225,493

Full-year 2026 outlook: actual Jan-Sep $9,253,713 + forecast $3,366,834 = $12,620,546 vs budget $12,190,400 (+$430,146, +3.5%).
Savings Plan after the AWS decommission (2026-11-01): projected utilization 96.5%, about $5,656/month unused until expiry on 2027-01-31.
```

### variance

```
Measure                          Amount  Actual minus       %
---------------------------  ----------  ------------  ------
Budget (approved late 2025)  $1,036,400     +$197,795  +19.1%
Forecast (made 2026-08-31)   $1,160,724      +$73,472   +6.3%
Actual                       $1,234,195

Bridge: budget -> forecast -> actual:
Step                                   Change  Running total
----------------------------------  ---------  -------------
Budget                                            $1,036,400
  plan change: ai-assistant          +$26,253     $1,062,653
  plan change: claims-analytics     +$102,788     $1,165,441
  ...
Forecast                                          $1,160,724
  Volume (usage at forecast rates)      +$294     $1,161,018
  Mix (between services)                 -$63     $1,160,955
  Rate (price per unit)              +$25,241     $1,186,195
  Unused commitment                       +$0     $1,186,195
  One-time charges                   +$48,000     $1,234,195
  Credits                                 +$0     $1,234,195
Actual                                            $1,234,195
```

### anomalies

```
 #  Series                                               Start       End         Days   Excess  ...  Triage                     Truth
 1  aws-payments-nonprod / Amazon EC2                    2025-11-18  2025-11-20  3      $5,634  ...  planned (PC-01)            PC-01
 2  aws-shared-network / Amazon VPC                      2026-02-10  2026-02-15  6     $13,651  ...  anomaly                    A1
 3  aws-payments-prod / Amazon EC2                       2026-03-04  2026-03-04  1      $2,857  ...  data artifact (late rows)  A2
 4  gcp-analytics-dev / BigQuery                         2026-04-22  2026-04-22  1      $3,880  ...  anomaly                    A3
 5  aws-ml-sandbox / Amazon EC2                          2026-05-18  2026-05-29  12    $30,057  ...  anomaly                    A4
 6  az-crm-prod / Log Analytics                          2026-07-07  2026-07-11  5      $9,037  ...  anomaly                    A5
 7  gcp-analytics-prod / BigQuery                        2026-07-15  2026-07-17  3      $1,868  ...  planned (PC-02)            PC-02
 8  gcp-analytics-prod / BigQuery                        2026-07-21  2026-07-28  7      $5,171  ...  planned (PC-02)            PC-02
 9  az-ai-assistant-prod / Azure OpenAI                  2026-08-03  2026-08-11  9     $18,238  ...  anomaly                    A7
10  az-crm-prod / Virtual Machines                       2026-09-01  2026-09-21  21    $16,629  ...  anomaly                    A8
11  aws-management / AWS Marketplace: SIEM subscription  2026-09-15  2026-09-15  1     $48,000  ...  planned (PC-03)            PC-03

Events flagged: 11. Raw precision (before triage): 54.5%.
After triage: 6 labeled anomaly, 6 true, 0 false -> precision 100.0%.
Recall on detector-targeted anomalies: 100.0%.
A6 (Non-production schedules disabled (savings decay)) is meant for the savings-tracker: not caught by the detector.

Threshold sweep (precision and recall after triage):
Rule     Thresholds               Events  Labeled  TP  FP  Precision  Recall  Missed
loose    z>=3.0, >=15%, >=$250        23       18   8  10      44.4%  100.0%  -
medium   z>=3.5, >=20%, >=$400        17       11   9   2      81.8%  100.0%  -
default  z>=4.0, >=25%, >=$500        11        6   6   0     100.0%  100.0%  -
strict   z>=5.0, >=40%, >=$1,000       8        5   5   0     100.0%   83.3%  A8
```

With `--seed 7` the detector also reaches 100% precision and recall (7 of 7 labeled anomalies are true; the savings decay crosses the thresholds with that seed's noise).

### allocation

```
Tagging Policy Compliance = compliant cost / taggable cost = $1,001,544 / $1,198,195 = 83.6% (first target > 90%)
Unallocated cost % = $8,495 / $1,234,195 = 0.69%; allocated 99.3%

How the cost was allocated                 Cost  Share
-----------------------------------  ----------  -----
Direct: tag (after normalization)    $1,035,452  83.9%
Direct: account default (hierarchy)     $35,118   2.8%
Credits (to the account's owner)       -$12,000  -1.0%
Shared pools (split below)             $167,131  13.5%
Unallocated                              $8,495   0.7%
```

### commitments

```
Commitment         Provider      ...  Utilization  Coverage  Waste %  Savings  Status
sp-0a1b2c3d4e5f    AWS           ...       100.0%     56.2%     0.0%  $67,886  active
ri-crm-vm-2025     Microsoft     ...          n/a       n/a      n/a       $0  expired 2026-08-31
cud-gce-analytics  Google Cloud  ...       100.0%     73.3%     0.0%   $4,262  active

Provider        ListCost  ContractedCost  EffectiveCost  ESR (FOCUS)  Option 1 at list  Option 2 at list
AWS             $755,194        $709,882       $641,997         9.6%              9.0%             15.0%
Microsoft       $341,842        $341,842       $341,842         0.0%              0.0%              0.0%
Google Cloud    $227,728        $218,619       $214,357         1.9%              1.9%              5.9%
All           $1,324,764      $1,270,343     $1,198,195         5.7%              5.4%              9.6%

Option                                        Hourly  Utilization  Coverage  Gross savings/yr  Unused/yr  Net savings/yr
Floor: P5 of daily usage                        $195       100.0%     65.9%          $731,886       $466        $731,420
Recommended: 95% of best net, least exposure    $210        99.2%     70.4%          $782,263    $14,319        $767,944
Expected-value optimum on the $5 grid           $305        91.0%     93.8%        $1,041,706   $241,153        $800,554
Renew as is                                     $220        98.2%     73.1%          $811,233    $34,324        $776,909
Oversized: 120% of the optimum                  $365        80.9%     99.8%        $1,108,252   $611,478        $496,774
```

### savings

```
Id       Initiative                                                ...  Method  Projected  Realized  Rate  Trend check  Last month  Status                Truth
INIT-01  Rightsize payments RDS instances                          ...  unit      $98,000  $118,716  121%     $114,285     $18,809  on track           $107,851
INIT-02  Schedule non-production compute (nights, weekends)        ...  trend    $221,333  $141,835   64%     $141,835     $20,376  partial, decaying  $136,652
INIT-03  S3 Intelligent-Tiering for payments log and archive data  ...  rate      $64,000   $52,922   83%      $49,621      $8,782  partial             $52,922
INIT-04  Azure Hybrid Benefit for Windows Server on CRM VMs        ...  ratio     $57,500   $62,231  108%      $63,002     $12,449  on track            $62,231
Total                                                              ...           $440,833  $375,704   85%     $368,744     $60,417                     $359,657

Year to date 2026: realized $375,704 of $440,833 projected (85%). Current monthly run-rate $60,417.
```

### summary (first section)

```
1. **September cost $1.23M: $198k (+19%) over budget and $73k (+6.3%) over our forecast.** Most of the budget
   gap is timing and one-offs: the claims-analytics migration started two months earlier than the budget assumed
   (+$117k until AWS is switched off on 1 November), a one-time marketplace renewal (+$48k) and a VM reservation
   that lapsed on 31 August 2026 (+$23k). The recurring overrun is AI assistant growth (+$25k).
2. **Full-year 2026 outlook $12.62M against a $12.19M budget: +$430k (+3.5%).** ...
3. **Savings now run at $60k a month; $376k realized this year (85% of plan).** ...
```

## How it was tested

From a clean directory: `generate`, then each of the seven analysis commands, all exiting with status 0; two `generate` runs compared byte for byte (identical); a second seed (`--seed 7`) run through `anomalies`, `forecast` and `savings`; `variance` and `summary` for `--month 2026-08`; an AST scan for unused names; and the SQL of chapter 47f.12, run on SQLite 3.45 against the same CSV files, reproducing the Python results (budget by line, tag compliance 83.6%, ESR 9.6%, 0.0% and 1.9%, and the same 68 flagged anomaly days).

## Limitations

- Daily grain only. Real commitment sizing needs hourly data, which gives lower floors than daily data.
- Savings Plan benefits are shared pro rata across eligible accounts. AWS applies a plan to the usage with the highest savings percentage first and, at equal percentages, to the usage with the lowest Savings Plans rate, so cost shifts between accounts differ in reality.
- The migration plan's increments are exactly what the generator adds, which flatters the backtest of the driver model; real engineering estimates miss.
- A subset of FOCUS columns, one currency (USD), no tax, no `InvoiceId`; `ServiceProviderName` stands in for the provider and publisher columns.
- The budget is produced by the lab's own forecast with the assumptions of late 2025; real budgets are negotiated.
- Anomalies and savings come with a ground-truth file; real ones are messier and nobody hands you the answers.

## License

The code is offered under the repository's MIT license (`LICENSE`); the book text is CC BY 4.0 (`LICENSE-CONTENT.md`).
