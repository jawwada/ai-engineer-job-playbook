# 16: Operations telemetry and unit economics

## What this dataset is for

The project's dashboard: for each expert task, the expert's minutes, the reviewer's minutes, the rework rounds and whether the customer accepted it. From those come the cost of each accepted item and whether the project earns or loses money on it. Data projects usually fail here, quietly, weeks before anyone looks at the data. The question this folder answers is: *what does an accepted item really cost, and is the trend getting better or worse?*

## The example

`task_log.csv`, in full: ten expert reasoning tasks (the kind in `08-reasoning/`) over one week.

```csv
task_id,expert_id,date,expert_minutes,qa_minutes,rework_rounds,accepted
rsn-0601,exp_003,2026-09-01,140,20,0,true
rsn-0602,exp_012,2026-09-01,155,25,1,true
rsn-0603,exp_027,2026-09-02,210,30,1,true
rsn-0604,exp_003,2026-09-02,125,20,0,true
rsn-0605,exp_038,2026-09-03,260,35,2,false
rsn-0606,exp_041,2026-09-03,230,30,1,true
rsn-0607,exp_012,2026-09-04,245,30,2,true
rsn-0608,exp_027,2026-09-04,275,35,2,true
rsn-0609,exp_038,2026-09-05,300,40,3,false
rsn-0610,exp_041,2026-09-05,265,30,2,true
```

| Field | What it is and why it exists |
|---|---|
| `task_id`, `expert_id`, `date` | breakdowns by expert and week |
| `expert_minutes` | writing time including rework: the largest cost |
| `qa_minutes` | review time, often forgotten in quotes |
| `rework_rounds` | returns to the expert: the leading indicator of spec or calibration trouble |
| `accepted` | only accepted items are paid for |

## How the model uses it

No model uses this file; the forward-deployed engineer does, weekly. `ops_demo(price=150.0, expert_rate=36.0, qa_rate=30.0, budget_minutes=150)` in `how_models_use_it.py` computes cost per accepted item and margin from the log at assumed rates of \$36 an hour for experts and \$30 for reviewers against a \$150 price; run `python3 how_models_use_it.py` from the lab root:

```text
[OPS] 8/10 accepted; cost per accepted item $183.81 vs price $150: gross margin -22.5%; expert minutes per task 178 -> 263 (budget 150)
```

The ten tasks took 2,205 expert and 295 review minutes, costing \$1,470.50, and 8 were accepted: \$183.81 per accepted item against a \$150 price, a gross margin of −22.5%. The trend is worse than the average: the first five tasks averaged 178 expert minutes and \$149.75 per accepted item, break-even; the last five averaged 263 minutes, rework rose from 0.8 to 2.0 rounds per task, and an accepted item cost \$217.88, a margin of about −45%. Both rejections came from one expert, `exp_038`, and cost \$373.50 for nothing.

What the engineer does with the number, in order: **diagnose** (did the spec change mid-week, did the item mix harden, did reviewers raise the bar, is one expert the driver); **fix the process** (a calibration session on the reworked items, recurring review comments turned into spec clarifications and a version bump, automatic pre-checks so reviewers stop catching mechanical errors, `exp_038` paired with a senior reviewer or moved to item types where they succeed); **tell the customer early, with numbers**, and offer options (difficulty-tiered pricing, a different hard-item quota, lower volume); **set a gate**. A 30% margin at \$150 allows \$105 per accepted item: at 80% acceptance, \$84 per attempted task, about 120 expert and 24 review minutes. Even the planned 150 expert minutes, with the observed 29.5 review minutes, give \$130.94 per accepted item, a 12.7% margin. Stop scaling until the gate holds.

## How it is produced and checked

A task tracker records assignment, submission, each review and rework cycle, and acceptance; time comes from the tool where possible rather than self-reports; acceptance flows back from the customer; rates come from contracts so the model can be recomputed.

`validate_all.py` check **16 operations telemetry** asserts: unique task ids; positive expert minutes; non-negative QA minutes and rework rounds; `accepted` is `true` or `false`. It prints `10 task records with minutes, rework and acceptance`. The financial check is the printed `[OPS]` line itself, every week; the final validator check, **how_models_use_it.py numbers**, pins `$183.81` and `-22.5%` among the strings it expects in the script's output, so a change to this file that moves the economics fails the validator.

## What goes wrong

- **Leaving rejected work and review time out** of the cost per item: with them in, break-even becomes a 22.5% loss.
- **Averages that hide one expert** moving the margin by several points, and **self-reported time**, rounded or inflated.
- **Incentives**: hourly pay rewards slowness, per-item pay rewards rushing; pay per accepted item with quality gates. And **small samples**: ten tasks are a reason to look closely, not a forecast.

## Related

Chapter 26d.17 (the four-step response, the margin gate) and 26d.18 (scoping, throughput and the weekly metrics table; 2,000 items in 10 weeks at these rates needs about 16 experts and 3 reviewers). Siblings: `08-reasoning/` (the items being paid for, with `minutes_spent` per item), `15-golden-and-qa/` (why items are rejected), `14-synthetic-provenance/` (edit minutes on synthetic records as the same cost).
