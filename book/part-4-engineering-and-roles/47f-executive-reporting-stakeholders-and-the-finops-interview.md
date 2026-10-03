# 47f. Executive reporting, stakeholder management and the FinOps analyst interview

> **What you need to be able to say:** which two or three numbers matter for a given audience; the answer-first narrative and a one-page template, with a worked, decision-ready example; the charts that work for executives; how to defend assumptions and methodology with an assumptions log, sensitivities, an accuracy record and data lineage, hostile questions included; how to translate technical changes into financial impact; how to earn credibility with senior engineers and finance and keep your numbers and the central IT FinOps team's from conflicting; and, for the interview, model answers to 35 questions that cover every responsibility and qualification in a representative multi-cloud FinOps analyst job description (anonymized), five cases with solutions, tested SQL and spreadsheet exercises, STAR templates and questions to ask. Chapter 47a decodes the job description and the finance vocabulary, 47b the billing data, 47c forecasting and variance, 47d allocation and anomalies, 47e optimization and realized savings, and 47g is the lab every number here comes from unless marked illustrative.

The lab's business unit (\$1.23M of amortized cost in September 2026) is separate from, and smaller than, the running example of 47a and 47c (\$2.55M in the same month). Both are fictional; do not compare figures across them.

## 47f.1 The two or three numbers that matter

An executive reads the first three numbers and the decision that follows them. The job description asks for "the two or three numbers that matter"; the skill is choosing them, and the choice changes with the audience.

**A headline number passes four tests.** It is *material* (if it moved 10%, someone would act); *comparative* (against budget, forecast or last year, never alone); *owned* (someone in the room can change it); and *stable* (same metric, scope and cut-off every month).

| Audience | Their real question | Number 1 | Number 2 | Number 3 |
|---|---|---|---|---|
| CIO or CTO | Are we on plan, and what needs my decision? | Full-year outlook against budget | This month against forecast (predictability) | Savings realized and the decisions that unlock more |
| CFO and IT Finance | Will you land the number, and what hits cash? | Full-year outlook against budget, with a range | Forecast accuracy over recent months | Commitments: cash outlay, obligations, consumption-commitment drawdown |
| Engineering leadership | Which teams, why, and what do we do? | Unit cost of the top applications | The top three drivers by team | Open anomalies and savings by team |
| Product or business owner | What does growth cost us? | Cost per customer, transaction or conversation | Marginal cost of the next increment of volume | Cost-to-serve trend against revenue |
| Central IT FinOps team | Do our numbers agree? | Your total reconciled to theirs | Your commitment needs | Your tag compliance against the enterprise standard |

**Anti-patterns.** Total spend with no comparison; a percentage without its base ("+21%" of what?); fifteen KPIs at one level; billed and amortized cost in one table; a definition changed since last month without a note.

**The lab's choice for September 2026** (to a CIO, with Finance in the room): (1) September at \$1.23M against a \$1.04M budget and a \$1.16M forecast, split into timing, one-offs and recurring; (2) the full-year outlook, \$12.62M against a \$12.19M budget; (3) savings of \$60,000 a month realized, with two decisions worth \$40,000 a month. Unit costs, tag compliance and anomalies go in the appendix, because nothing in them needs a decision this month.

## 47f.2 The narrative and a one-page template

**Answer first.** Lead with the conclusion, then the reasons, then the evidence. In each section: *what happened* (the number and its comparison), *why* (the drivers, sized), *so what* (the effect on the year, the risk, the decision), *now what* (actions with owners and dates).

**A sentence pattern that works.** "[Scope] cost [\$A] in [period], [\$B] ([C%]) [over/under] [budget/forecast], because of [driver 1 (\$)], [driver 2 (\$)] and [driver 3 (\$)]. For the year this means [\$D] against budget. We recommend [action] by [date], worth [\$E]."

| Block | Content | Rules |
|---|---|---|
| Header | Scope, cost basis, data cut-off, preparation date | One line |
| The three numbers | Three bolded sentences, each followed by one or two sentences of explanation | Every number with its comparison; rounded in prose, exact in tables |
| What drove the gap | A bridge of at most six drivers plus "other", summing exactly | Sorted by size; one line of business explanation each |
| Outlook | Next three months and the full year, with a range | Say what the range comes from |
| Risks | At most four, each with a dollar range, a date or probability, and an owner | Risks are future; drivers are past |
| Opportunities | The top three, with value and stage | Expected value, not best case |
| Decisions and actions | What, value, basis, owner, date | A decision without an owner and a date is a wish |
| Method and reconciliation | Two or three lines: basis, forecast method, reconciliation to the central report, data quality | The footnote that prevents the second meeting |

**House rules.** Same order every month; one printed sign convention (over budget is "+" and unfavorable, 47a.3); two or three significant figures in prose, exact figures in tables; dates in words; no jargon in the first block; anything longer than a page in an appendix nobody has to read. Write the three numbers once and the second paragraph twice: for Finance about landing the year, accruals and cash; for engineering leadership about teams and changes.

## 47f.3 A worked executive summary

This is the lab's September 2026 summary (`finops_lab.py summary`), edited the way a person edits a generated draft: rounding, ordering, and the words a CIO uses. It is fictional throughout.

---

**Cloud cost summary: September 2026**

*Business unit spend on AWS, Microsoft Azure and Google Cloud (13 accounts). Amortized cost by charge date. Data through 30 September; prepared on the fifth business day of October.*

**1. September cost \$1.23M: \$198k (19%) over budget and \$73k (6.3%) over our 31 August forecast.** \$188k of the \$198k is timing and one-offs: the claims-analytics migration started two months earlier than the budget assumed (+\$117k, which ends when AWS is switched off on 1 November), a one-time security software renewal (+\$48k) and a VM reservation that lapsed on 31 August (+\$23k). The recurring overrun is AI assistant growth (+\$25k).

**2. Full-year outlook \$12.62M against a \$12.19M budget: +\$430k (+3.5%), give or take about \$0.1M.** January to September is \$394k over budget; the fourth quarter adds \$37k, because October is still \$104k over while November is \$87k under after the AWS switch-off.

**3. Savings run at \$60k a month; \$376k realized this year, 85% of plan.** A further \$56k a month is identified (\$44k weighted by probability). Two decisions this month are worth \$40k a month.

**What drove the gap to budget**

| Driver | vs budget | Explanation |
|---|---:|---|
| Migration ahead of plan (timing) | +\$117k | Google Cloud build-out began 1 July, not 1 September; both sides run until 1 November |
| One-time software renewal | +\$48k | Annual SIEM subscription bought through AWS Marketplace; reached the change calendar after the forecast |
| AI assistant growth | +\$25k | Conversations up about 6% a month; the budget assumed 3% |
| Lapsed VM reservation | +\$23k | Same VM hours at on-demand rates: price, not usage |
| Migration credits | −\$12k | Last month of Google Cloud credits |
| Other, net | −\$3k | Savings beyond the budget's 3% efficiency target, net of new ML experiments and organic growth |
| **Total** | **+\$198k** | Budget \$1,036k; actual \$1,234k |

**Outlook**

| Month | Forecast | Likely range | Budget |
|---|---:|---:|---:|
| October | \$1.23M | \$1.19M to \$1.26M | \$1.12M |
| November | \$1.05M | \$1.01M to \$1.10M | \$1.14M |
| December | \$1.09M | \$1.03M to \$1.14M | \$1.07M |
| Full year | \$12.62M | about ±\$0.1M | \$12.19M |

**Risks**

- **The AWS switch-off slips.** Each month of delay adds about \$200k (both platforms keep running). Owner: claims-analytics lead; the go/no-go is on 20 October.
- **AI assistant growth.** Spend grows about 6% a month. A prompt change in August raised cost per conversation by about 70% for nine days before it was reverted, and the release process has no cost gate yet.
- **Savings decay.** The non-production schedule saves about \$20k a month against \$34k at its peak, because instances opted out in July were never re-enrolled.
- **Savings Plan after the switch-off.** Utilization falls to about 96% from November until the plan expires on 31 January (about \$6k a month unused); the renewal must be sized without the data platform.

**Opportunities (top three by value)**

| Opportunity | Value | Stage |
|---|---:|---|
| New one-year reservation for 240 CRM VMs | \$28k a month | Ready for approval |
| Restore the non-production schedules | \$12k a month | Owner agreed; scheduled for 15 October |
| Log retention and sampling for the CRM platform | \$6k a month | Approved by the owner; starts 1 November |

**Decisions and actions requested**

| Decision or action | Value | Owner | By |
|---|---:|---|---|
| Approve the CRM VM reservation (breaks even at 60% use; expected 100%) | \$28k a month | CRM engineering lead and FinOps | 9 October |
| Re-enroll non-production instances in the schedule | \$12k a month | Payments engineering manager | 15 October |
| Renew the Compute Savings Plan at about \$210 an hour (today \$220), sized without the data platform | keeps \$768k a year of savings | FinOps and Finance | December |
| Add a cost-per-conversation gate to AI assistant releases | risk control | AI team lead | next release |

*Method and reconciliation.* Forecast: per-service weekday profile, level and damped trend, plus the migration plan, commitments, known one-time items and the savings pipeline at its probability; the one-month-ahead error on recurring usage averaged 1.7% (WAPE) over six months. Reconciled to the central IT FinOps report (invoice basis): amortized and billed cost are equal this month (\$1,234,195), because the commitment fees billed (\$165,658) equal the commitment cost amortized into usage; Finance may book the \$48k subscription as a prepaid expense at \$4k a month. Tag compliance 84%; unallocated cost 0.7%.

---

**Why it is written this way.** The first sentence is the answer with both comparisons. The split into timing, one-offs and recurring tells the CIO that \$188k of the \$198k does not repeat before anyone asks. Every risk has a size, a date or an owner ("costs may increase" is not a risk statement), and the reservation carries its break-even so nobody needs the appendix. The reconciliation line answers the email the central team would otherwise send the next morning.

## 47f.4 Charts that work for executives

Five charts cover almost every executive conversation. Title each with its conclusion, not its contents.

**1. The variance bridge (waterfall).** Budget, each driver as a floating bar sorted by size, actual; unfavorable and favorable in different colors; seven bars or fewer, each labeled with the amount and a three-word reason. The lab's September, in thousands of dollars: budget 1,036 → migration timing +117 → one-time renewal +48 → AI growth +25 → lapsed reservation +23 → credits −12 → other −3 → actual 1,234. Title: "September is \$198k over budget; \$188k is timing and one-offs."

**2. Forecast against budget, with a range.** Actuals as a solid line, the forecast dashed with a shaded 80% band, the budget as a step line, and two or three annotated known changes (migration start on 1 July, switch-off on 1 November). Title: "The year lands \$0.43M over budget; November turns favorable after the switch-off."

**3. The savings burn-up.** Cumulative realized against cumulative projected savings, with the pipeline as a dashed extension at its expected value. The lab's 2026 values, in thousands of dollars:

| Month | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep |
|---|---|---|---|---|---|---|---|---|
| Cumulative projected | 8 | 30 | 73 | 147 | 220 | 294 | 367 | 441 |
| Cumulative realized | 0 | 18 | 58 | 127 | 197 | 256 | 315 | 376 |

A small gap opens early (the storage-tiering ramp, then a schedule that delivered at most 84% of its projection) and widens from July, when the schedule decayed. Title: "Savings are 85% of plan; one initiative accounts for the gap."

**4. Unit cost over time.** Cost per transaction or conversation as the main line; volume as a small chart below it, not on a second axis. A unit-cost chart tells the business whether growth is efficient; a total-spend chart cannot.

**5. Commitment health.** Utilization and coverage per commitment over time, with expiry dates marked. The lab's would have shown the Azure reservation's end on 31 August six months ahead.

**Leave out** daily charts (unless the subject is an anomaly), pies with more than three slices, dual axes, stacked areas with twenty services, truncated axes on bar charts, undefined acronyms, any chart without a comparison, and any chart the presenter has to explain how to read.

## 47f.5 Defending assumptions and methodology, and presenting to leadership

Leaders trust a forecast when they can see what it depends on, how sensitive it is, and how often it has been right.

### The assumptions log

| Id | Assumption | Value | Source | Owner | Updated | Sensitivity on the 2026 outlook |
|---|---|---|---|---|---|---|
| A-01 | AWS data platform switched off | Compute 1 November, storage 1 December | Migration plan | Claims-analytics lead | 20 Sep | One month later: +\$200k |
| A-02 | AI assistant growth | About 6% a month, damped | Six-month trend | AI team lead | 30 Sep | 8% a month: +\$14k; 4%: −\$8k |
| A-03 | CRM VM reservation bought | From 15 October, 90% probability | Pipeline | FinOps | 20 Sep | Not bought: +\$62k |
| A-04 | Non-production schedules restored | From 15 October, 80% probability | Pipeline | Payments manager | 20 Sep | Not restored: +\$24k |
| A-05 | Savings pipeline | Five items at their probabilities | Pipeline | FinOps | 20 Sep | All at 100%: −\$21k |
| A-06 | Migration credits | Ended in September | Contract | Procurement | 20 Feb | none left |
| A-07 | Annual software renewal | Next in September 2027 | Change calendar | Security lead | 10 Sep | none in 2026 |

The sensitivities come from rerunning the lab's forecast with each assumption changed. The table tells leadership where the risk is: one date, the switch-off, is worth more than every other assumption together.

### The accuracy record

Show how the forecast has done before asking anyone to trust the next one. The lab's rolling backtest over six months:

| Model | One month ahead (WAPE) | Three months ahead (WAPE) | Bias, one month |
|---|---|---|---|
| Last month's daily rate | 3.9% | 10.1% | −3.8% |
| Statistical only | 3.5% | 8.4% | −2.7% |
| Statistical plus drivers | 1.7% | 3.6% | −0.9% |

Two things to say: the drivers (mostly the migration plan) more than halve the error at three months; and the bias is negative, so the forecast has run slightly low, which is the direction leadership should hear about. The FinOps Foundation's maturity examples put forecast variance under 20% for Crawl, 10% for Walk and 5% for Run (47a.2; 47c.5 compares them with the budgeting thresholds).

### Data lineage

Be able to say in one breath where a number comes from: "the providers' FOCUS exports land daily in the warehouse; the model reads amortized cost by charge date; totals tie to the invoices within 0.5% once the month is final; the version and refresh time are in the footer." Keep the query behind every headline number one click away.

### Hostile questions

| Question | Answer that works |
|---|---|
| "You missed September by 6%. Why trust the next forecast?" | "Leave out a \$48k renewal and a \$23k lapsed reservation, neither of which was on the change calendar, and we missed by \$2k. Over six months the one-month error on recurring usage averages 1.7%. Purchases and commitment end dates now feed the calendar automatically." |
| "Just cut 20%." | "Twenty percent is \$2.5M a year. Our identified pipeline is \$56k a month; the next tier needs architecture changes with their own risk. I can show what 10% and 20% would take, by team, by Friday." |
| "Isn't AI spend out of control?" | "Volume grows 6% a month and cost per conversation is flat apart from nine days in August. The risk is a release that changes the prompt; we are adding a cost-per-conversation gate to the release process." |
| "Why buy a reservation if we might migrate?" | "It is one year, it breaks even at 60% use, and nothing on the roadmap touches these VMs before 2028. If that changes, it still pays as long as we use 60% of the reserved hours." |
| "Your number doesn't match central IT's." | "It reconciles; the bridge is in the footnote. Amortized and billed cost are equal this month, so the basis is not the issue. The \$52.6k gap is \$6.2k of August Google Cloud usage on the September invoice and two parent allocations, enterprise support and the shared logging service, that our written agreement keeps outside the business unit's scope." |

### Presenting to leadership

- **Pre-wire.** Send the page 24 hours ahead and walk the finance partner and the engineering director through it individually; nobody should see a surprise in the room, least of all their own team's number.
- **Ten minutes.** Two for the three numbers, three for the drivers, three for the decisions, two for questions. Stop talking when the decision is made.
- **Interruptions.** Answer the question in one sentence and return: "Yes, it is mostly timing; the split is on the next slide."
- **"I don't know yet."** Say it, then what you know and when you will know the rest: "I don't know yet whether the switch-off will slip; the go/no-go is on 20 October and I will send the updated outlook that afternoon. Each month of delay is about \$200k." Never invent a number in the room; a wrong number said to a CFO is quoted for a year.
- **After the meeting.** Send decisions, owners and dates within two hours, and record each decision in the assumptions log.

## 47f.6 One set of numbers with the central IT FinOps team

47a.7 gives the working relationship and 47c.9 the mechanics: the six sources of difference (metric, scope, shared costs, cut-off, exchange rates, credits and tax), a worked bridge and a ten-point single-source-of-truth agreement. The reporting side adds three habits.

**The bridge, before anyone publishes** (illustrative amounts on the lab's September). The business unit reports \$1,234,195; the central team's draft shows \$1,286,795 for the same accounts. The metric lines cancel this month, which is worth knowing before anyone argues about amortization.

| Step | Amount |
|---|---:|
| Business unit, amortized, charge date | \$1,234,195 |
| − commitment cost amortized into usage | −\$165,658 |
| + commitment fees billed in September | +\$165,658 |
| + Google Cloud rows for August usage on the September invoice (billing period against charge period) | +\$6,200 |
| + Enterprise support allocated by the parent (outside the business unit's scope by agreement) | +\$31,000 |
| + Parent-level shared logging service allocated to the business unit | +\$15,400 |
| = Central team's draft | \$1,286,795 |
| Unexplained | \$0 |

**A reconciliation line in every report:** "Reconciles to the central IT FinOps report of [date], \$X: metric \$a, scope \$b, cut-off \$c, allocation \$d; unexplained \$e (under 0.5%)." If the unexplained part exceeds the agreed tolerance, the report waits or says so.

**Ownership and timing.** Reconcile on a fixed business day of the close calendar (47a.6); never send leadership a number the central team has not seen; agree one owner per number (the central team owns the parent rollup, the business unit its own allocation); and send commitment needs to whoever owns the payer account early, because they buy for the whole organization.

## 47f.7 Translating technical changes into financial impact

Engineers describe a change in instances, gigabytes, requests and dates; finance needs dollars per month, dollars this fiscal year, cash against expense, and risk. The translation follows six steps: (1) the engineering fact, with dates; (2) the cost model, quantity × rate per line at your effective rates; (3) the run-rate; (4) the in-year amount, including one-time costs and overlaps; (5) cash and commitments: upfront payments, commitments left idle or needing resizing, consumption-commitment drawdown; (6) the unit cost and the one variable that moves the answer most.

### 1. A migration (the lab's claims-analytics platform)

*Fact.* EMR, EC2 and S3 on AWS move to BigQuery, Dataproc and Cloud Storage on Google Cloud: build-out from 1 July to 15 September, AWS compute off on 1 November, AWS data deleted on 1 December.

*Model and run-rate.* Before: the AWS data platform at about \$186k a month plus the existing Google Cloud analytics services at about \$27k, \$213k in all. After: about \$150k a month on Google Cloud alone (the forecast for the first half of 2027). Steady-state saving: about \$63k a month, 30%.

*In-year.* Running both platforms costs about \$30k in July, \$78k in August, \$126k in September and \$138k in October above the before-state, \$371k in total, less \$36k of migration credits. November saves \$17k (AWS storage is still on) and December \$67k. Net effect on 2026: about \$250k *more* than staying put. In 2027: about \$750k less.

*Cash and commitments.* No upfront payments. The Compute Savings Plan loses the data platform's EC2 on 1 November, so about \$5.7k a month of it goes unused until it expires on 31 January; the renewal is sized without that usage (47e.2).

*Risk.* The switch-off date: each month of delay costs about \$200k, about \$46k a week.

*To finance:* "The migration costs about \$250k more than staying put this year, from four months of running both platforms, and then saves about \$63k a month, about \$750k next year; it pays back by April. The number to watch is the switch-off date: a month's delay costs \$200k." *To engineering:* "Every week the old cluster runs after cut-over costs about \$46k; the switch-off date is the most valuable line on your plan."

### 2. A new region (illustrative)

*Fact and model.* The payments API adds a European region for data residency on 1 March 2027, with a minimum two-zone footprint: compute \$45,000 a month, databases \$22,000, storage and replication \$6,000, networking \$4,000, observability and security tooling \$5,000, about \$82,000 a month. One-time: three engineers for eight weeks at an agreed \$100 an hour (\$96,000) and \$8,000 of data migration. In-year: ten months at \$82,000 plus \$104,000, about \$924,000.

*Commitments and unit cost.* EC2 Instance Savings Plans, Reserved Instances, Azure reservations and Google resource-based CUDs are tied to a region; Compute Savings Plans, Azure savings plans for compute and Compute Flexible CUDs are not. Use headroom in the flexible plans and buy nothing for the new region until three months of usage show its floor. At 300,000 transactions a day the region costs about \$0.009 per transaction against \$0.005 in the main region, because the footprint is fixed while volume is small: put the volume ramp in the forecast as a driver.

### 3. A logging change (the lab's CRM platform)

*Fact.* The CRM platform ingests about 480 GB of logs a day, about \$1,100 a day (\$33,100 in September) at the lab's \$2.30 per GB. Sampling debug logs and dropping health-check logs cuts ingestion by about 18%.

*Model.* 86 GB a day × \$2.30 × 30.4 days = about \$6,000 a month (pipeline item OPP-03, at 70% probability). The same arithmetic in reverse explains the July anomaly: debug logging in a release added 780 GB a day, about \$1,800 a day.

*Risk and guardrail.* Investigations need logs: agree the sampling with the on-call team, keep errors unsampled, and add a daily ingestion alert per table so the next verbose release costs one day, not five.

### 4. A model-provider switch (illustrative)

*Fact.* The AI assistant handles 55,000 conversations a day at 15,000 tokens each: 825 million tokens a day at a blended \$3.00 per million, \$2,475 a day, about \$75,300 a month, \$0.045 per conversation. A router would send 70% of conversations to a smaller model at a blended \$1.20 per million.

*Model.* 577.5 million tokens at \$1.20 plus 247.5 million at \$3.00 = \$1,435.50 a day, about \$43,700 a month, \$0.026 per conversation: \$31,600 a month saved (42%). If the smaller model's tokenizer produces 10% more tokens for the same text, the saving is about \$29,500 (39%).

*One-time and gates.* Evaluation and prompt work: two engineers for four weeks, about \$32,000. Ship only if the resolution rate on the evaluation set stays within one point (chapter 32), and check commitments first: provisioned throughput reserved for the current model would go idle.

*To finance:* "About \$30k a month for a one-time \$32k, if quality holds; payback in about a month." *To the product owner:* "Cost per conversation falls from 4.5 to about 2.7 cents."

### 5. An architecture change (illustrative)

A nightly batch moves from an always-on 20-node cluster (\$0.50 an hour each: 20 × \$0.50 × 730 = \$7,300 a month) to an ephemeral one that runs three hours a night (20 × \$0.50 × 3 × 30.4 = \$912, plus about \$300 of orchestration and storage). Saving: about \$6,100 a month (83%). If the always-on nodes sit under a reservation with eight months left, report the saving net of the idle reservation until it can be exchanged, rescoped or absorbed, or time the change with the expiry. And watch run time against the batch window as closely as cost.

## 47f.8 Earning credibility with senior engineers and finance leaders

Credibility is earned in the months when nothing dramatic happens:

- **Be early.** Raise a variance in the forecast before it reaches the bill; "I told you in August" is the sentence that builds trust.
- **Be right, and show the record.** Keep an accuracy log for forecasts and accruals and publish it unprompted.
- **Show your work.** Every number has a query and a method note one click away; the fastest answer to a challenge is the query.
- **Be consistent.** Announce a change of method in advance and show old and new numbers side by side for a month.
- **Own mistakes fast.** A correction within a day: what was wrong, the right number, the effect, the process fix. Illustrative: "The October forecast I sent on Monday double-counted the reservation savings; the correct outlook is \$12.66M, not \$12.62M. The item was also in the baseline from 15 October. Implemented items now leave the savings layer automatically." It costs less credibility than any defense.
- **Speak both languages.** To engineers, units and resources ("requests at four times usage"); to finance, periods, accounts and materiality ("\$23k unfavorable, rate, non-recurring if we buy by 15 October").

With senior engineers, ask the owner what you are missing before you present, offer to do the tedious part, and never show a team's waste to its leadership before the team has seen it. With finance, hit the close calendar, use their materiality and sign conventions, give ranges rather than "approximately", and never change a sent number without a note.

## 47f.9 The interview: the loop and what each round tests

A typical loop has five or six steps: a recruiter screen; the hiring manager (your experience and how you work with engineering and finance); a technical screen (billing data, SQL or a spreadsheet, native tools); a case (a forecast, a variance, an anomaly or a commitment decision from a data pack); a presentation of the case to a panel that includes finance; and a behavioral round. Some companies use a take-home instead of the case. Chapter 35 covers reading the job description, chapter 37 the preparation timeline, and 47a.1 decodes this role line by line.

| Job description line (paraphrased) | Where it is tested | Questions in 47f.10 | Chapters |
|---|---|---|---|
| Monthly and quarterly forecasts across AWS, Azure and Google Cloud; align with budget cycles | Case, hiring manager | 1–6 | 47c.2–47c.5, 47c.8, 47g |
| Track against forecast and budget, find variances early, explain drivers; trends versus noise | Case, presentation | 7–10 | 47c.6, 47c.7, 47f.3 |
| Visibility by account, service, environment and application; tagging and allocation | Technical screen | 11–15 | 47d.1–47d.8 |
| Anomalies and emerging risks; drive them to resolution with owners | Case | 16–20 | 47d.9–47d.16 |
| Partner with Cloud Engineering, the central IT FinOps team, IT Finance and Business Planning | Hiring manager, behavioral | 21–25 | 47a.7, 47c.3, 47c.8, 47c.9, 47f.6, 47f.7 |
| Translate technical change; credibility; executive summaries; present and defend | Presentation, behavioral | 26–30 | 47f.1–47f.8 |
| Savings across commitments, rightsizing, storage, idle and licenses; implement; track realized; forecast them | Technical case | 31–34 | 47e |
| Qualifications: native tools, multi-cloud, forecasting and variance | Technical screen | 35 | 47a.9, 47b, 47c |

## 47f.10 Thirty-five questions with model answers

These complement the ten in 47a.10. Each answer takes about a minute; the numbers come from the lab or the worked examples in 47d–47f.

### Forecasting

1. **"Walk me through a 12-month forecast for AWS, Azure and Google Cloud."** Amortized cost by charge date per service and account. Per series, a statistical baseline: a weekday profile, a median level, a damped and clipped trend, yearly seasonality only with 13 months or more, and storage on a constant-month basis because it is billed per GB-month. Then a driver layer from the known-changes register (migrations with ramp, double-running and switch-off; launches; commitment expiries and renewals; credits ending; price changes), one-time items, and pipeline savings at their probability. Backtest on a rolling origin and publish a range from the errors. In the lab, the drivers cut three-month WAPE from 8.4% to 3.6%.
2. **"MAPE, WAPE or bias?"** All three. WAPE (Σ|A − F| ÷ ΣA) weights by dollars, which is what Finance feels; MAPE (the mean of |A − F| ÷ A) weights series equally, which finds the badly forecast ones but explodes on small actuals; bias (Σ(F − A) ÷ ΣA) shows the direction WAPE hides. The lab's one-month figures: MAPE 1.6%, WAPE 1.7%, bias −0.9%. The FinOps Foundation's Forecast Accuracy Rate is (F − A) ÷ F per period.
3. **"How do you stop a forecast from extrapolating a migration ramp or a one-off?"** Medians for the level and for monthly growth, so one step does not become a trend; a clipped, damped trend; one-time charges and credits outside the modeled series; and the plan, not the model, for any series in a known change. In the lab, the Google Cloud services doubled monthly during the build-out; the migration driver forecasts them from their pre-migration base plus the observed increment.
4. **"How do you align with IT Finance's budget cycle?"** Same basis (amortized), calendar (fiscal months), rates (budget FX), structure (their cost centers), drivers (Business Planning's volumes) and dates: monthly refresh, quarterly reforecast, annual plan two to four months ahead. Every version ships with the assumptions log and its drift since the last one.
5. **"How do you forecast AI spend?"** As volume × tokens per unit × price per token, by model and route, not as a trend on dollars. In the lab, model spend grows about 6% a month; at 8% the fourth quarter is \$14k higher, at 4% \$8k lower. The bigger risk is a release that changes tokens per conversation, which only a unit-cost gate catches.
6. **"How would you build next year's budget?"** From the exit run-rate, organic growth by driver, dated known changes, new initiatives with business cases, and an efficiency target made of named initiatives rather than a plug; phased by month; with a range and the assumptions. The lab's budget shows the failure: built from October data, with a migration date that later moved and an AI growth cap with no driver behind it.

### Variance and signal versus noise

7. **"September is 19% over budget. Explain it in two minutes."** "We spent \$1.23M against \$1.04M, \$198k over. \$117k is timing: the migration started two months early and ends on 1 November. \$48k is a one-time renewal and \$23k a reservation that lapsed, which is price, not usage. \$25k is AI growth, offset by a \$12k credit and \$3k of net savings elsewhere. Against our own forecast we were \$73k over, almost all of it the renewal and the reservation, neither of which was on the change calendar. The year lands \$430k over, and two decisions this month recover \$40k a month."
8. **"Define rate, usage and mix variance."** With L as usage at list prices and e as effective cost per list dollar: volume = (ΣL actual − ΣL forecast) × the average forecast rate; mix = Σ(L actual × e forecast) − ΣL actual × the average forecast rate; rate = ΣL actual × (e actual − e forecast). They sum exactly to the usage variance; one-time charges and credits are separate lines (47c.6 has the price × quantity form). The lab's September: volume +\$294, mix −\$63, rate +\$25,241, one-time +\$48,000. Part of the rate line on Savings Plan accounts is really volume: when a plan is fully used, each extra dollar of eligible usage is on demand, so the blended rate rises.
9. **"Trend or noise?"** Normalize per day and weekday (and storage for month length); check persistence (three consecutive days or five of seven at daily level, two consecutive months at monthly level; 47c.7), breadth, driver backing, known changes and data completeness; compare with a same-weekday median and a robust spread. Then pick the queue: anomaly ticket, forecast change, or nothing. A 9% drop in February is mostly three fewer days.
10. **"When do you change the forecast mid-quarter?"** When a change is persistent and explained, a driver moved or a known change got a date, not because one week was high. Record each change with its reason and size, report the drift, and never change the budget: the budget measures the plan, the forecast what you know now.

### Visibility, tagging and allocation

11. **"Design a tagging standard for three clouds."** Four required keys (application, environment, cost-center, owner) in lowercase kebab-case, because Google labels accept only lowercase; values from the service catalog, the chart of accounts and the team directory, with cost center and owner derived from application; enforcement in IaC on each cloud; compliance measured strictly, on cost (47d.2–47d.4).
12. **"Tag compliance is 84%. How do you reach 90% this month?"** Rank violations by cost. In the lab, one invalid value (`application=payments` on one account) is 7.1% of taggable cost; fixing it takes compliance to 90.7%. Then fix the IaC default so it does not come back, and block it at creation.
13. **"How do you allocate shared costs without disputes?"** Few pools, a written method each, shared cost on its own line, rule changes only at fiscal-year boundaries, a dispute window with a materiality threshold, and the method agreed before the numbers: the lab's AI assistant pays \$8,967 of the network pool under an even split and \$538 under a usage-driven one.
14. **"How do you allocate a shared Kubernetes cluster?"** Each workload at the larger of requests and usage, times the node price; idle is the rest. Publish the idle percentage, spread system overhead and idle up to a target in proportion, and charge excess idle to the platform team (47d.7).
15. **"Showback or chargeback?"** Showback always; chargeback when Finance wants cloud cost in cost-center budgets; neither is more mature. Chargeback needs a file that ties to the bill, a suspense cost center, budgets transferred at a fiscal boundary and a dispute process; run three months of showback with the exact file first (47d.8).

### Anomalies

16. **"How would you set up anomaly detection across three clouds?"** Keep the native detectors on and route them into one queue; add a warehouse detector on amortized and unit cost (same-weekday median, MAD-based z-score, and z ≥ 4, +25% and +\$500 together), triage with the change calendar and a data-lag rule, and route by the account map. In the lab: 11 events, 6 confirmed, 100% precision and recall, against 54.5% precision without triage.
17. **"An alert fires every Monday on the same account."** It is probably comparing Mondays with weekends; use same-weekday baselines. If it already does, a weekly job varies in size: give the series its own threshold or put the job on the calendar. Never mute the series.
18. **"What severity levels and SLAs?"** By projected monthly impact: Sev1 above about 2–3% of monthly spend (acknowledge in four business hours, mitigate in a day), Sev2 a middle band (a day and five days), Sev3 below (three days, next sprint). Escalate on missed SLAs to the engineering manager and then the director; inform Finance at Sev1.
19. **"The owner says it's growth and closes the ticket."** Ask for the driver. If transactions or customers moved with it, close it as accepted and add it to the forecast with a date and a run-rate; if nothing moved, reopen it. Escalate on missed SLAs, never on disagreement.
20. **"Your detector missed a \$13k-a-month leak. Why, and what fixes it?"** Slow changes below the daily thresholds never fire, and a six-week baseline absorbs a step within about three weeks. In the lab, schedules disabled on part of the non-production fleet cut a \$34k-a-month saving to \$20k without crossing \$500 a day. The savings tracker caught it; a weekly-aggregate detector or a run-rate test (daily excess × 30 above monthly materiality) would have too.

### Partnering, planning and the central team

21. **"Cloud Engineering is planning a migration. What do you need, and when?"** Two to three months ahead, an entry in the known-changes register: start date, ramp, steady-state cost on the target, double-running period, switch-off and deletion dates, commitments on both sides, credits and an owner; then a monthly check of the dates. The switch-off date matters most: in the lab, a one-month slip adds \$200k.
22. **"How do you prevent conflicting numbers with a central FinOps team?"** A signed single-source-of-truth agreement, a bridge on a fixed business day before either side publishes, a reconciliation line in every report, and one owner per number (47c.9, 47f.6).
23. **"Explain a Savings Plan to a CFO in one minute."** "We promise to spend \$210 an hour on compute for a year, at rates about 30% below on-demand. If we use less, we still pay, so we size it below the lowest usage we expect: we break even if we use 70% of it, and we expect 99%. Paid monthly it is an operating expense over the year; paid upfront, a prepaid asset released month by month."
24. **"Engineering wants a new region. What do you tell Finance?"** The run-rate of the minimum footprint (about \$82k a month in 47f.7), the one-time build, the in-year amount, that region-bound commitments do not follow the workload, and the unit-cost curve: expensive per transaction at launch, cheaper as volume grows.
25. **"A team wants to switch model provider to save money. How do you validate it?"** On cost per successful task with the evaluation set as the gate, not on list prices: tokenizers differ, caching behaves differently, routing changes the mix. Count the one-time work and any idle provisioned capacity left behind. In 47f.7, \$31,600 a month on paper becomes about \$29,500 after a 10% token difference, and only if resolution stays within a point.

### Reporting and credibility

26. **"What goes on your one page?"** Three numbers with comparisons, a bridge of at most six drivers that sums, the outlook with a range, at most four sized risks, the top opportunities, decisions with owners and dates, and a two-line method and reconciliation note (47f.2).
27. **"How do you deliver bad news to leadership?"** Early, in numbers, with the cause, the effect on the year and a recommendation, pre-wired with the people it affects, and in the first sentence: "We will land \$430k over budget; \$188k of September's gap is timing and one-offs; I need a decision on the reservation this week."
28. **"The CFO challenges an assumption in the meeting."** Point to the assumptions log and its sensitivity: "If AI grows 8% instead of 6%, the quarter is \$14k higher; the assumption that matters is the switch-off date, at about \$200k a month." If you do not know, say when you will.
29. **"How do you build credibility with engineers who see FinOps as a tax?"** Their units, evidence they can reproduce, no surprises in front of their leadership, help with the tedious part, and public credit when they ship.
30. **"What makes a report decision-ready?"** Finance's format and definitions, reconciled, every number traceable to a query, every decision with an owner and a date, nothing that needs a second meeting, and short enough to forward unedited.

### Savings and commitments

31. **"How do you size a commitment?"** On hourly eligible usage after removing what is leaving. Break-even utilization is 1 − discount; the expected-value optimum is the level usage exceeds in at least 1 − discount of the hours; take the smallest commitment near that plateau, buy the floor on longer terms and the next layer on one-year terms, and ladder purchases (47e.2).
32. **"Coverage is 56% and utilization 100%. Should we buy more?"** Not before checking what is leaving. In the lab, the data platform's EC2 leaves on 1 November, utilization falls to 96.5%, and the plan expires in January; the right move is a renewal at about \$210 an hour, not more commitment now.
33. **"Two optimizations hit the same VMs in one quarter. How do you attribute the savings?"** By meter: the Hybrid Benefit on the license meter (license cost per VM hour), the reservation on the compute meter (effective rate per hour). When two changes share a meter, measure them in implementation order against baselines that include the earlier one, and check that the total does not exceed counterfactual minus actual for the scope (47e.12).
34. **"Your program realized 85% of plan. Good or bad?"** It depends on why. In the lab, three initiatives are at 83–121% and one at 64% and decaying, because opt-outs never expired; the fix is restoring the schedules and putting expiry dates on opt-outs, not a new initiative. Check the methods too: against the lab's ground truth, the unit method overstated the best performer by 10%. Report realization per initiative with its method, and the pipeline by stage.

### Qualifications

35. **"Which native tool answers which question?"** Cost Explorer for trends, forecasts and month-over-month Cost Comparison drivers; CUR 2.0 or the FOCUS export for line-item SQL; Azure Cost Management's cost analysis, exports, budgets, anomaly alerts and cost allocation rules; Google Cloud Billing reports and the BigQuery export (the detailed export for resources and GKE); the three FOCUS exports for one cross-cloud model (47b).

Interviewers compare notes across a loop, so do not reuse one story or one number for everything (38.6).

## 47f.11 Five case studies with model solutions

### Case 1: build the forecast (45 minutes)

*Prompt.* "Eighteen months of daily FOCUS-format cost data for AWS, Azure and Google Cloud, the account map, a migration plan and the savings pipeline. Forecast the next 12 months by month and provider, explain your method, and tell us how confident you are."

*What a good answer does.* Confirms the basis (amortized) and scope; profiles the data (per-day totals, weekday pattern, steps and their causes, one-time charges); builds a baseline per series without the migration scope; adds the drivers (switch-off and deletion dates, the Savings Plan effect of removing EC2, the end of the credits, next September's renewal, the pipeline at its probability); backtests and gives a range; and names the one assumption that matters.

*Model answer (lab).* October \$1.23M, November \$1.05M, December \$1.09M; 12 months \$13.23M. The migration scope falls from \$351k in October (both platforms) to \$146k in December (Google Cloud only). The 2026 outlook is \$12.62M against a \$12.19M budget. In the backtest, one-month WAPE is 1.7% with drivers against 3.5% without, three-month WAPE 3.6% against 8.4%. The switch-off date is worth about \$200k a month.

*Common mistakes.* Forecasting billed cost, so commitment fees spike on the first of each month; extrapolating the Google Cloud ramp; forgetting that removing covered EC2 leaves part of the Savings Plan unused; forecasting storage per day without allowing for month length; treating the \$48k renewal as monthly; missing that the \$12k credit does not recur; one number without a range.

*Follow-ups.* "What if the switch-off slips a month?" (+\$200k.) "How accurate has your method been?" (The backtest table.) "How would you forecast AI spend separately?" (Question 5.)

### Case 2: explain the variance (20 minutes)

*Prompt.* "Budget, forecast and actual by budget line for September, the change calendar and the commitment inventory. Explain September to the CIO in three minutes."

*What a good answer does.* Separates the gap to budget (the plan) from the gap to forecast (the in-month surprise), bridges both, labels each driver as timing, one-time or recurring, and ends with what changes.

*Model answer (lab).* Budget \$1,036,400; forecast \$1,160,724; actual \$1,234,195. Budget to forecast: claims-analytics +\$102,788 (migration timing), AI assistant +\$26,253, payments −\$12,069, customer portal −\$11,707, ML research +\$11,009, shared platform +\$7,015, document intelligence +\$1,036. Forecast to actual: volume +\$294, mix −\$63, rate +\$25,241 (of which \$23,415 is the CRM VMs at on-demand rates after the reservation ended), one-time +\$48,000, credits \$0. Then the answer to question 7, and two process fixes: purchase orders and commitment end dates feed the change calendar automatically.

*Common mistakes.* Explaining by service instead of by driver; mixing billed and amortized cost; percentages without a base; no distinction between what was known at forecast time and what was not.

### Case 3: the anomaly (15 minutes)

*Prompt.* "Azure costs for the CRM production subscription have been about \$800 a day higher since 1 September. The owner says nothing changed. What do you do?"

*Model answer.* Validate: a month of data, well past Azure's latency, so it is real. Scope: the Virtual Machines meter only, starting exactly on the first, which points at a contract or commitment event. Attribute: VM hours rose about 1.5% while cost per hour rose by roughly half, so it is rate, and the owner is right that the workload did not change. The commitment inventory shows a one-year reservation for 200 VMs (4,800 hours a day) that ended on 31 August: the same hours moved from \$0.24 to \$0.40, \$768 a day, \$23,040 in September. Decide: a new reservation at the floor, the 10th percentile of concurrent VMs over 30 days (241), so 240 instances, about \$28,000 a month at 40% and 99.8% expected utilization; a savings plan for compute instead if the VM family may change, since reservations bought from 1 February 2027 for savings-plan-covered services cannot be exchanged. Prevent: every commitment end date on the calendar with alerts at 90, 60 and 30 days. Communicate: tell the owner and their manager it was a lapsed discount, not their workload.

*Follow-ups.* "Why 240 and not the September average of about 274?" (The first 240 are in use on nearly every day, because 241 is the 10th percentile, and return about 67% on each dollar of commitment (1 ÷ 0.6 − 1). The units between 240 and about 280 run only on weekdays, 71% of days; that clears the 60% break-even but returns only about 19% (0.714 ÷ 0.6 − 1). Buy 240 now and decide the weekday band after looking at hourly data, because daily averages hide night-time troughs.) "Who should have caught it?" (The owner of the commitment inventory; the gap is that expiries were not on the calendar.)

### Case 4: the commitment purchase (30 minutes)

*Prompt.* "Sixty days of hourly eligible compute: \$1,000 an hour at on-demand rates in business hours (60 hours a week), \$700 on weekday nights (60 hours), \$600 at weekends (48 hours). A one-year plan gives 30% off, a three-year plan 45% (illustrative). A decommission of about 10% of usage within six months is possible but not approved. What do you recommend?"

*Model answer.* Break-even utilization is 70% for one year and 55% for three. The level exceeded in at least 70% of hours is \$700 (120 of 168 hours, 71.4%); \$1,000 is exceeded only 35.7% of the time, so it is never worth committing. A 10% decommission would lower the floor to \$540, so buy the floor that survives it on three years and the next layer on one:

| Layer | Covers (on-demand equivalent) | Hourly commitment | Term |
|---|---|---|---|
| Floor | \$540 an hour | \$297 (45% off) | 3 years |
| Next layer | \$540 to \$700 an hour | \$112 (30% off) | 1 year |

| Usage | On-demand cost a week | Ladder cost a week | Savings | Effective savings rate |
|---|---|---|---|---|
| 10% lower | \$117,720 | \$80,712 | \$37,008 | 31.4% |
| As planned | \$130,800 | \$86,712 | \$44,088 | 33.7% |
| 10% higher | \$143,880 | \$96,912 | \$46,968 | 32.6% |

A one-year plan alone at the 30th percentile (\$490 an hour) saves \$30,480 a week (23.3%); the ladder is better because the floor earns the deeper three-year discount, and it stays good in the downside case. Review the one-year layer in six months, when the decommission is decided.

*Common mistakes.* Sizing to average usage; buying the deepest discount for everything; ignoring a possible decommission; not stating break-even.

### Case 5: the executive summary (30 minutes to write, 10 to present)

*Prompt.* "Using your answers to cases 1 to 4, write a one-page summary for the CIO and present it to the CIO, the finance director and an engineering director."

*Model answer.* The page in 47f.3. *How it is scored:* answer in the first sentence; three numbers, each with a comparison; a bridge that sums; an outlook with a range and its source; risks with sizes, dates or owners; decisions with owners and dates; a reconciliation line; no unexplained acronyms; one page; and the presenter stops when the decision is made. Panels often interrupt in the first minute to test composure: answer in one sentence and return to the structure.

## 47f.12 SQL and spreadsheet exercises with solutions

### SQL on the lab data

The queries use FOCUS column names and were run against the lab's CSV files loaded into SQLite 3.45 (47g.6 shows a ten-line loader). Date and JSON functions differ between engines; chapter 47b has provider-specific versions.

**Exercise 1. Actual against budget by budget line for September 2026.**

```sql
SELECT m.BudgetLine,
       ROUND(SUM(c.EffectiveCost)) AS actual,
       (SELECT SUM(b.Budget) FROM budget b
         WHERE b.Month = '2026-09' AND b.BudgetLine = m.BudgetLine) AS budget
FROM focus_costs c
JOIN account_map m ON m.SubAccountName = c.SubAccountName
WHERE substr(c.ChargePeriodStart, 1, 7) = '2026-09'
GROUP BY m.BudgetLine
ORDER BY actual DESC;
```

Expected: payments-api 362,418 against 374,500; claims-analytics 348,369 against 243,600; customer-portal 191,564 against 178,700; shared-platform 167,131 against 111,500; ai-assistant 88,639 against 63,700; doc-intelligence 40,331 against 38,800; ml-research 35,745 against 25,600.

**Exercise 2. Top movers from August to September, per day** (August has 31 days, September 30; compare daily rates).

```sql
WITH m AS (
  SELECT SubAccountName, ServiceName, substr(ChargePeriodStart, 1, 7) AS month,
         SUM(EffectiveCost) / COUNT(DISTINCT ChargePeriodStart) AS cost_per_day
  FROM focus_costs
  WHERE ChargeCategory = 'Usage'
  GROUP BY 1, 2, 3)
SELECT cur.SubAccountName, cur.ServiceName,
       ROUND(prev.cost_per_day) AS aug_per_day,
       ROUND(cur.cost_per_day) AS sep_per_day,
       ROUND(cur.cost_per_day - COALESCE(prev.cost_per_day, 0)) AS change_per_day,
       ROUND(100.0 * (cur.cost_per_day / prev.cost_per_day - 1), 1) AS pct
FROM m cur
LEFT JOIN m prev
  ON prev.SubAccountName = cur.SubAccountName
 AND prev.ServiceName = cur.ServiceName
 AND prev.month = '2026-08'
WHERE cur.month = '2026-09'
ORDER BY ABS(cur.cost_per_day - COALESCE(prev.cost_per_day, 0)) DESC
LIMIT 5;
```

Expected: Google Cloud BigQuery +\$1,011 a day (+44.6%, the migration), CRM Virtual Machines +\$829 (+45.9%, the lapsed reservation), Dataproc +\$384 (+60.6%), Azure OpenAI −\$345 (−12.0%, August contained the prompt incident), payments EC2 +\$213 (+5.1%). The follow-up is always "which of these is a rate change?": only the VMs. (Storage is the one service where per-day comparison misleads: billed per GB-month, it costs about 3% more per day in a 30-day month than in a 31-day one.)

**Exercise 3. Tagging Policy Compliance (strict).**

```sql
SELECT ROUND(100.0 * SUM(CASE WHEN
         json_extract(Tags, '$.application') IN ('payments-api','claims-analytics','customer-portal',
                                                  'ai-assistant','doc-intelligence','ml-research','shared-platform')
     AND json_extract(Tags, '$.environment') IN ('prod','staging','dev','sandbox','shared')
     AND json_extract(Tags, '$."cost-center"') IN ('cc-1001','cc-1002','cc-1003','cc-1004',
                                                    'cc-1005','cc-1006','cc-1999')
     AND json_extract(Tags, '$.owner') IN ('team-payments','team-claims-data','team-crm','team-ai',
                                            'team-ml','team-platform','team-security')
     THEN EffectiveCost ELSE 0 END) / SUM(EffectiveCost), 1) AS tagging_policy_compliance_pct
FROM focus_costs
WHERE substr(ChargePeriodStart, 1, 7) = '2026-09'
  AND ChargeCategory = 'Usage'
  AND CommitmentDiscountStatus <> 'Unused';
```

Expected: 83.6. In production, join to a dictionary table instead of listing values in the query.

**Exercise 4. Commitment utilization and the FOCUS effective savings rate.**

```sql
SELECT CommitmentDiscountId,
       ROUND(SUM(CASE WHEN CommitmentDiscountStatus = 'Used'   THEN EffectiveCost ELSE 0 END)) AS used,
       ROUND(SUM(CASE WHEN CommitmentDiscountStatus = 'Unused' THEN EffectiveCost ELSE 0 END)) AS unused,
       ROUND(100.0 * SUM(CASE WHEN CommitmentDiscountStatus = 'Used' THEN EffectiveCost ELSE 0 END)
             / SUM(EffectiveCost), 1) AS utilization_pct
FROM focus_costs
WHERE substr(ChargePeriodStart, 1, 7) = '2026-09'
  AND ChargeCategory = 'Usage' AND CommitmentDiscountId <> ''
GROUP BY CommitmentDiscountId;

SELECT ServiceProviderName,
       ROUND(100.0 * (SUM(ContractedCost) - SUM(EffectiveCost)) / SUM(ContractedCost), 1) AS esr_focus_pct
FROM focus_costs
WHERE substr(ChargePeriodStart, 1, 7) = '2026-09' AND ChargeCategory = 'Usage'
GROUP BY ServiceProviderName;
```

Expected: the CUD and the Savings Plan at 100.0% utilization (used \$7,258 and \$158,400, unused \$0); ESR 9.6% for AWS, 0.0% for Microsoft, 1.9% for Google Cloud. Now remove `AND ChargeCategory = 'Usage'` and compute one ESR over all rows: it returns 16.8% instead of 5.7%, because commitment purchase rows carry ContractedCost with zero EffectiveCost and credit rows carry negative EffectiveCost with no ContractedCost. Explaining that difference is a good interview answer (47e.2).

**Exercise 5. A same-weekday median and MAD anomaly detector in SQL.**

```sql
WITH daily AS (
  SELECT SubAccountName || ' / ' || ServiceName AS series, ChargePeriodStart AS day,
         SUM(EffectiveCost) AS cost
  FROM focus_costs WHERE ChargeCategory = 'Usage'
  GROUP BY 1, 2),
hist AS (                                   -- the same weekday in each of the previous six weeks
  SELECT d.series, d.day, d.cost AS today, h.cost AS past,
         ROW_NUMBER() OVER (PARTITION BY d.series, d.day ORDER BY h.cost) AS rn,
         COUNT(*) OVER (PARTITION BY d.series, d.day) AS n
  FROM daily d JOIN daily h
    ON h.series = d.series
   AND julianday(d.day) - julianday(h.day) IN (7, 14, 21, 28, 35, 42)),
base AS (                                   -- median of six values = mean of the 3rd and 4th
  SELECT series, day, today, AVG(past) AS median6
  FROM hist WHERE n = 6 AND rn IN (3, 4)
  GROUP BY 1, 2, 3),
dev AS (
  SELECT h.series, h.day, ABS(h.past - b.median6) AS ad,
         ROW_NUMBER() OVER (PARTITION BY h.series, h.day ORDER BY ABS(h.past - b.median6)) AS rn
  FROM hist h JOIN base b ON b.series = h.series AND b.day = h.day),
mad AS (
  SELECT series, day, AVG(ad) AS mad FROM dev WHERE rn IN (3, 4) GROUP BY 1, 2)
SELECT b.series, b.day,
       ROUND(b.today - b.median6) AS excess,
       ROUND((b.today - b.median6) / MAX(1.4826 * m.mad, 0.05 * b.median6, 1.0), 1) AS z,
       ROUND(100.0 * (b.today / b.median6 - 1)) AS pct
FROM base b JOIN mad m ON m.series = b.series AND m.day = b.day
WHERE b.today - b.median6 >= 500
  AND b.today >= 1.25 * b.median6
  AND (b.today - b.median6) / MAX(1.4826 * m.mad, 0.05 * b.median6, 1.0) >= 4
ORDER BY b.day;
```

Expected: 68 flagged days in nine series, the same days as the lab's Python detector (the marketplace purchase is absent because the query reads usage rows only). Without the z-score condition the query flags 123 days, 65 of them on the ramping BigQuery series: the z-score, not the percentage, keeps a fast-growing series quiet.

### Spreadsheet exercises

**Exercise 6. A volume, mix and rate bridge.** Forecast and actual for one month:

| | Forecast list cost (B) | Forecast effective cost (C) | Actual list cost (D) | Actual effective cost (E) |
|---|---|---|---|---|
| Compute | 100,000 | 70,000 | 104,000 | 78,000 |
| Storage | 40,000 | 40,000 | 46,000 | 46,000 |
| AI services | 20,000 | 20,000 | 30,000 | 30,000 |
| Total | 160,000 | 130,000 | 180,000 | 154,000 |

With the services in rows 2–4 and totals in row 5: forecast rate F2 = C2/B2; actual rate G2 = E2/D2; average forecast rate = C5/B5 (0.8125); volume = (D5 − B5) × C5/B5 = **16,250**; mix = SUMPRODUCT(D2:D4, F2:F4) − D5 × C5/B5 = 148,800 − 146,250 = **2,550**; rate = SUMPRODUCT(D2:D4, G2:G4 − F2:F4) = 104,000 × 0.05 = **5,200**. Check: 16,250 + 2,550 + 5,200 = 24,000 = E5 − C5. Reading: usage grew \$16k at forecast rates; the mix moved toward undiscounted AI and storage (+\$2.6k); compute's effective rate rose because commitment coverage fell (+\$5.2k).

**Exercise 7. MAPE, WAPE and bias.** The lab's one-month-ahead backtest:

| Month | Actual (A) | Forecast (F) |
|---|---|---|
| April | 971,297 | 989,301 |
| May | 1,001,129 | 998,956 |
| June | 972,746 | 979,229 |
| July | 1,072,171 | 1,042,959 |
| August | 1,138,668 | 1,113,393 |
| September | 1,198,195 | 1,172,724 |

MAPE = AVERAGE(ABS(A2:A7 − F2:F7)/A2:A7) (an array formula) = **1.63%**; WAPE = SUMPRODUCT(ABS(A2:A7 − F2:F7))/SUM(A2:A7) = 106,618/6,354,206 = **1.68%**; bias = (SUM(F2:F7) − SUM(A2:A7))/SUM(A2:A7) = −57,643/6,354,206 = **−0.91%**. The last three months were all under-forecast: say so before anyone asks.

**Exercise 8. The commitment break-even table.** Net value per dollar of commitment = utilization ÷ (1 − discount) − 1, as a data table:

| Utilization | 20% off | 30% off | 45% off | 60% off |
|---|---|---|---|---|
| 100% | +25.0% | +42.9% | +81.8% | +150.0% |
| 90% | +12.5% | +28.6% | +63.6% | +125.0% |
| 80% | 0.0% | +14.3% | +45.5% | +100.0% |
| 70% | −12.5% | 0.0% | +27.3% | +75.0% |
| 60% | −25.0% | −14.3% | +9.1% | +50.0% |
| 50% | −37.5% | −28.6% | −9.1% | +25.0% |

The diagonal of zeros is the break-even rule: utilization = 1 − discount.

## 47f.13 STAR story templates for FinOps scenarios

Chapter 38 explains the method and the tags. Fill these with your own facts and prepare the "number defense" (the figures an interviewer will probe) for each.

| Story | Tags | Situation and task | Actions to include | Numbers they will probe |
|---|---|---|---|---|
| A variance you explained | DATA, INF | A month that surprised Finance; you owned the explanation | Bridge by driver, rate versus usage, what was known when, the process fix | Each driver's size, the share explained, the residual |
| A forecast you rebuilt | OWN, TECH | A forecast that kept missing | Basis change (to amortized), a driver layer, a backtest, a range | Accuracy before and after (WAPE), the horizon |
| An anomaly you drove to resolution | OWN, INF, DEL | A spike with an unclear owner | Validation, attribution, routing, the decision, the guardrail | Cost, days to detect and to resolve, cost avoided |
| A savings program and its decay | DATA, OWN | Savings that looked done but slipped | Counterfactual, tracker, root cause of decay, the policy that fixed it | Projected against realized, the decay, the recovery |
| Conflicting numbers reconciled | INF, AMB | Two teams reporting different figures to leadership | The bridge, the written agreement, the reconciliation line | The gap, each reconciling item, the residual |
| Bad news to leadership | INF, ETH | An overrun or a mistake of yours | Early warning, the numbers, options, a recommendation | The overrun, the range, the decision taken |
| A commitment decision | TECH, DATA | A renewal or purchase with uncertain usage | Floor, break-even, sensitivity, laddering, approval | Size, utilization, ESR, the downside case |

**A filled example, with fictional facts, as a model of form.** *Situation:* in the month a data-platform migration started, cloud spend came in 19% over budget and the finance director asked whether the year was at risk. *Task:* I owned the forecast and the monthly explanation. *Action:* I bridged the month by driver instead of by service, which showed that \$188k of the \$198k was timing and one-offs: the migration had started two months before the budget assumed, a software renewal had not been on our change calendar, and a VM reservation had lapsed. I put the switch-off date into the forecast as a driver with a sensitivity of about \$200k a month, and asked procurement to feed purchase orders and commitment end dates into the calendar. *Result:* the full-year outlook settled at +3.5% with a range of about \$0.1M, the reservation was replaced within a week (\$28k a month), and the next month's forecast missed by under 2%. *Reflection:* the analysis was the easy part; the calendar feed is what stopped the same surprise from repeating.

## 47f.14 Questions to ask the interviewer

| Question | What the answer tells you |
|---|---|
| "Which cost metric does leadership see, billed or amortized, and who decided?" | How mature the reporting is, and whether your first month goes to arguing about definitions |
| "How is spend split between the business unit's accounts and the parent's shared services, and who owns the reconciliation?" | Whether coordination with the central team is a process or a conflict |
| "What was the last forecast miss, and what caused it?" | Whether known changes reach the forecast, and how blame is handled |
| "Who buys commitments, and who owns their utilization?" | Whether you recommend or decide, and where waste lands |
| "How do engineering teams learn about their own cost today?" | Whether showback exists and whether teams act on it |
| "What share of spend is allocated, and what share is tag-compliant?" | The size of the allocation project you inherit |
| "How is AI spend tracked and allocated?" | Whether the fastest-growing line is visible |
| "Which tools are in place beyond the native consoles?" | How much pipeline work comes before analysis |
| "What would make this role a success at six months?" | The real priorities |
| "Who presents to the CIO and CFO today, and how often?" | Whether you will present, and to whom |
| "What decision is waiting on better cost data right now?" | The first piece of work that will matter |
| "How does Finance treat commitment purchases and marketplace subscriptions in the ledger?" | Whether amortization and prepaid treatment are settled |

**Interview line:** *"I give leadership two or three numbers with their comparisons, a bridge that sums, an outlook with a range and the decisions I need, on one page, reconciled with the central FinOps team before it goes out. Behind it sit an assumptions log with sensitivities, a published accuracy record and a query for every number, so I can defend the method in the room, and say 'I don't know yet; you'll have it Thursday' when that is the truth."*

## Sources

- FinOps Foundation, [Budgeting capability](https://www.finops.org/framework/capabilities/budgeting/), [Forecasting capability](https://www.finops.org/framework/capabilities/forecasting/) and [Maturity model](https://www.finops.org/framework/maturity-model/) (variance thresholds, forecast accuracy and drift KPIs, maturity examples; accessed 2 October 2026)
- FinOps Foundation, [Invoicing & Chargeback capability](https://www.finops.org/framework/capabilities/invoicing-chargeback/) and [Rate Optimization capability](https://www.finops.org/framework/capabilities/rate-optimization/) (accessed 2 October 2026)
- FOCUS, [Determine effective savings rate](https://focus.finops.org/docs/use-cases/v1-4/determine-effective-savings-rate/) (accessed 2 October 2026)
- AWS, [Cost Explorer cost comparison](https://aws.amazon.com/about-aws/whats-new/2025/05/aws-cost-explorer-new-cost-comparison-feature) (May 2025) and [Data Exports](https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html) (accessed 2 October 2026)
- Microsoft Learn, [Understand Cost Management data](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-cost-mgt-data) and [Self-service exchanges and refunds for Azure Reservations](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/exchange-and-refund-azure-reservations) (accessed 2 October 2026)
- Google Cloud, [Export Cloud Billing data to BigQuery](https://docs.cloud.google.com/billing/docs/how-to/export-data-bigquery) (accessed 2 October 2026)
- The lab: `labs/finops-analyst/finops_lab.py` in this repository (chapter 47g); all lab figures are from a run with the default seed of 42
