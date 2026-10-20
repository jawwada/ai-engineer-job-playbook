# Rubrics — knowledge primer

An interactive, single-file primer on rubrics for evaluating and producing AI data, written for interview preparation (Google FDE / Applied AI, Toloka forward-deployed engineering) and for consultative conversations with clients. Open `rubrics.html` in any browser; no build step, no network needed beyond the Google Fonts link (the page falls back to system fonts without it).

## What is on the page

Ten topic cards, each with six tabs — **Concepts** (with a diagram), **Example**, **Method**, **Pitfalls**, **Code**, **Say it in the room** — plus three reference cards.

| # | Card | What it covers |
|---|------|----------------|
| 1 | What a rubric is | The verifiability spectrum; anatomy of a criterion (id, statement, scale, weight, gate, polarity, dimension, evidence, provenance); analytic / holistic / checklist / single-point / hybrid; binary, ordinal, nominal scales; global vs instance-specific; a complete small rubric scored on a response; a rubric file schema and scoring function |
| 2 | Writing a rubric | The drafting pipeline (intent + reference answer + candidates → failure modes → criteria → lint → pilot); the principles as a per-item checklist; weak → strong rewrites; a Toloka-style reasoning rubric before and after expert editing; candidate-based drafting with Gemini and a `lint_rubric()` |
| 3 | Validating a rubric | Reliability vs validity (the four targets); κ, weighted κ, Fleiss, Krippendorff's α, ICC, Spearman, macro-F1; the κ paradox; rater effects; discrimination; a pilot table with actions; the pilot protocol; per-criterion α with bootstrap CIs and judge macro-F1 in code |
| 4 | Rubrics for human annotation | The quality system (qualification, goldens, honeypots, overlap, adjudication, calibration); the guideline as a decision procedure; mechanisms table; the five Toloka products; a one-page pairwise-preference guideline with a gold item; queue building, rater health and the batch acceptance report in code |
| 5 | Rubrics for LLM-as-a-judge | Anatomy of a judge call; design choices (pointwise/pairwise, per-item/batched, reasoning, votes, anchors, abstention, judge model, rubric origin); biases and structural controls; a judge prompt, a verdict, an injection that fails; a Gemini per-item judge with evidence checks, voting and a swap test |
| 6 | Rubrics as rewards | The RL loop and where it breaks; Rubrics as Rewards, RLCF checklist feedback, OpenRubrics, HealthBench, OpenAI model graders side by side; explicit vs implicit aggregation; a hacked response caught by pitfalls; a rubric reward for GRPO, an RFT multi-grader, a hacking monitor |
| 7 | Rubrics for agents | Five criterion families on a trajectory (outcome, process, policy, efficiency, safety & communication); pass^k; ADK and Vertex agent metrics; the expense agent's trajectory rubric with one run scored and pass^k computed; ADK `EvalConfig` with rubric criteria; a harness with programmatic gates |
| 8 | Scoring & aggregation | Normalised weighted sums, negative points, gates as multipliers, tiers, hierarchical trees (PaperBench), implicit scores, abstention policies; intervals, paired comparisons, ROC-derived thresholds; a two-system comparison read honestly; tree aggregation, bootstrap, Wilson and threshold code |
| 9 | Rubrics on Google Cloud | The Gen AI evaluation service's managed rubric metrics, adaptive vs static rubrics, rubric groups, custom metrics; ADK's rubric-based criteria; an adaptive rubric example with a two-candidate comparison; `generate_rubrics` → freeze → `run_inference` → `evaluate` in code |
| 10 | Rubric operations & clients | Lifecycle and versioning semantics; drift signals and cadence; the rubric as the contract (acceptance criteria, disputes, change control, explainable pricing); a data-contract excerpt, a changelog, a monitoring week; registry, acceptance check and drift job in code |
| — | The script | The thirty-second and two-minute answers, a 30-term glossary, a pairwise-preference rubric built from kickoff to contract, eleven likely questions with answer shapes |
| — | Rubric gallery | Ready-to-adapt rubrics for preference pairs, reasoning data (prompt and answer), robotics video (capture and annotation), coding tasks (task and solution, SWE-bench Verified style), agentic gyms (environment), plus the judge-call and agent-trajectory templates and a rubric file skeleton |
| — | Papers, benchmarks & lint | HealthBench, PaperBench, Rubrics as Rewards, RLCF, OpenRubrics, XpertBench, Autorubric, SWE-bench Verified, τ-bench, Toloka's reasoning datasets, the judge lineage, Vertex adaptive rubrics; a 20-point rubric lint checklist; the metrics cheat sheet |

## Conventions

- Agreement bands follow Krippendorff (α ≥ 0.80 reliable, 0.667–0.80 tentative) and Landis & Koch for κ; judge validation uses macro-F1 against the human majority as in HealthBench.
- Scores normalise by the positive maximum weight (HealthBench, Autorubric); gates multiply; pass^k = C(c,k)/C(n,k) for agents.
- Google Cloud identifiers follow the 2026 documentation (Gen AI evaluation service in the Gemini Enterprise Agent Platform, `types.RubricMetric`, rubric groups, ADK `rubric_based_*` criteria); SDK names change — verify before running.
- Pilot numbers, prices and agreement figures in the examples are illustrative unless attributed to a paper; the page never quotes a personal rate.
- The page is a hosted Claude artifact as well; this file is the standalone copy for the repository.
