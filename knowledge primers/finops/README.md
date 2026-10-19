# FinOps — knowledge primer

An interactive, single-file primer on FinOps for cloud and AI, written for interview preparation (Google FDE / Applied AI, forward-deployed and platform roles) and for consultative conversations with clients. Open `finops.html` in any browser; no build step, no network needed beyond the Google Fonts link (the page falls back to system fonts without it).

## What is on the page

Ten topic cards, each with six tabs — **Concepts** (with a diagram), **Example** (worked numbers), **Method**, **Pitfalls**, **Code** (BigQuery SQL, Python, gcloud), **Say it in the room** — plus three reference cards.

| # | Card | What it covers |
|---|------|----------------|
| 1 | FinOps as a discipline | The FinOps Framework 2026 (three phases, four domains, twenty-two capabilities, Executive Strategy Alignment new); the 2026 survey; personas; maturity markers (forecast and budget variance, allocation coverage); the monthly cadence as a schedule |
| 2 | Billing data & cost metrics | Billing hierarchy; standard, detailed, pricing and FOCUS exports; the four FOCUS cost columns (list, contracted, billed, effective) and the row classifiers; `cost + credits` ties to the invoice; `cost_at_list`; credit types including the spend-based commitment model; which metric answers which question |
| 3 | Allocation & unit economics | Labels vs Resource Manager tags; the allocation waterfall; shared-cost methods (even, proportional, fixed, usage-driven) with the AI-assistant example; Kubernetes `max(request, used)` and idle policy; showback and chargeback; cost per unit the business counts |
| 4 | Rate optimisation: commitments | Resource-based CUDs, Compute Flexible CUDs, spend-based CUDs per service, Flexible Savings Plans for gen AI, sustained use; coverage, utilisation and ESR; break-even `u* = 1 − d` and the (1 − d)-quantile rule; sizing a commitment on a usage profile; laddering |
| 5 | Usage optimisation | The savings pipeline and where savings decay; rightsizing, scheduling, storage tiers, idle, egress, BigQuery editions, Kubernetes; realised savings against a counterfactual, per initiative and meter |
| 6 | FinOps for AI: token economics | Four token kinds; why agent loops are quadratic (`N·P + g·N(N+1)/2`) and what caching changes; a worked turn with thinking tokens; implicit caching minimums; context control, routing, batch, provisioned capacity; a budget dataclass |
| 7 | FinOps for AI: platforms & GPUs | The cost stack of an AI product; four ways to pay for accelerators (on-demand, Spot, reservations, flex-start); Dynamic Workload Scheduler; utilisation and MFU; fine-tune vs prompt; data and evaluation costs |
| 8 | Anomalies, budgets & guardrails | Native anomaly detection and AI early anomalies; a robust detector of your own (same-weekday median, MAD z-score, floors); triage against the change calendar; severities and SLAs; the enforcement ladder from budget alerts to Pub/Sub automation, quotas, gateway caps and run budgets; spend-cap budgets |
| 9 | Forecasting, budgeting & variance | Baseline + drivers + known changes; MAPE, WAPE, bias, MASE; forecast accuracy ratio and drift; the variance bridge from budget to actual (timing, one-time, rate, usage, credits, savings); signal vs noise rules; the two-minute explanation of a month 19% over |
| 10 | The practice & the conversations | The one-page executive summary; what survives a hostile question; credibility with engineers; one set of numbers; cost in solution design with clients |
| — | The script | The thirty-second and two-minute answers for cloud FinOps and AI FinOps, a glossary, a worked unit-economics case, likely interview questions with answer shapes |
| — | Cost-lever playbook | Levers by Google Cloud service, AWS and Azure equivalents, and which native tool answers which question |
| — | Formulas & KPIs | Cost metrics and commitment math, forecast accuracy and variance decomposition, token arithmetic, maturity markers and targets on one page |

## Conventions

- Google Cloud names, features and dates follow the 2026 documentation and release notes (FinOps hub 2.0 and the FinOps score, the FinOps Explainability Agent, Compute Flexible CUDs for all accounts, billing-account-scoped resource CUDs, Flexible Savings Plans for gen AI, the FOCUS export preview, AI spend early anomalies, spend-cap budgets). Statuses (GA / preview) drift; verify before quoting them to a client.
- The FinOps Framework and survey figures are the FinOps Foundation's 2026 editions; FOCUS column semantics follow FOCUS 1.2.
- Every price, bill and savings figure in the examples is illustrative and labelled as such; the page never quotes a personal rate.
- SQL targets the standard and detailed billing exports in BigQuery; Python samples are plain Python with the Google Cloud client libraries where needed — verify identifiers against current docs before running.
- The page is a hosted Claude artifact as well; this file is the standalone copy for the repository.
