# Self-Improving Agents — improvement with frozen weights

An interactive, single-file knowledge primer on how an agent gets better at a job when its model never changes. It is laid out the same way as the Experience Use Cases primer: a row of cards is the index, one card opens at a time, and every card has six tabs — **Concepts** (with a diagram or a chart), **Example** (a worked example with numbers), **Method** (the steps), **Pitfalls**, **Code** (Python, JSON, MCP), and **Say it in the room** (the thirty-second and two-minute answers plus likely questions). Open `self-improving-agents.html` in any browser; no build step, no network needed beyond the Google Fonts link (the page falls back to system fonts without it).

Thesis: with the weights frozen, every gain lives in the harness — in what the model is told, what it can remember, what it can call, how it checks itself, and who gets to say no. The harness is what you engineer, the gym is where you measure it, and pass^k on a frozen task set is the number that says whether it worked.

## What is on the page

| # | Card | What it covers |
|---|------|----------------|
| 1 | The loop | Where improvement comes from when the model is frozen: trace, grader, reflection, three versioned stores (prompt store, case memory, tool registry), a human gate for side effects and a frozen evaluation split that decides promotion; the five levers and the discipline that makes them safe; an illustrative quarter (pass@1 0.71 → 0.88, pass^4 0.29 → 0.69) |
| 2 | τ-bench and pass^k | Tool-agent-user interaction: a policy document, tools over a seeded database, a simulated user, state-based grading; pass@k versus pass^k with a chart for n = 8, c = 6 (pass^4 = 0.21), and how to read a vendor's number |
| 3 | Agent gyms | Reset, step, reward: the six parts of an environment (task bank, state, tools / action space, simulator, grader, runner); evaluation gyms versus training gyms; an internal IT-operations gym in numbers; a determinism test |
| 4 | Golden trajectories | Verified reference runs: four sources by trust and cost, the audit, the golden store, four uses (validity oracle, exemplars and seed cases, trajectory evaluation, SFT targets) and the exact-match trap |
| 5 | Right tool, right API | Selection, arguments, contracts and least privilege; a typed tool with validation both ways; deferred loading; tool-call precision and recall against a golden trajectory and which fix each metric points at |
| 6 | Dynamic prompt optimisation | The prompt as a parameter: exemplar bootstrapping, instruction search, textual gradients, failure-driven rules; dev, held-out and frozen splits with a six-round chart that shows the overfitting gap; a minimal evolutionary optimiser and the DSPy version |
| 7 | Episodic memory in RAG | Episodic, semantic and procedural memory with a grader-gated write policy and retrieval as data; the Docker-socket failure that becomes a case; the lift measured as pass^k with memory on versus off |
| 8 | Critique and Reflexion | Actor, evaluator, reflection, retry: Reflexion, Self-Refine, CRITIC and the judge in the loop; what grounds a critique and the three rules that keep it honest |
| 9 | Discovery, shell and search | Discovering tools (MCP, OpenAPI, --help, skills) and environments with an allowlist, an injection scan, a dry run and a registry; the two universal tools and the guards that make them safe |
| 10 | Reward models: datasets and method | Outcome, process, generative, rubric and verifiable rewards; the public preference and reward datasets with sizes, labels and dates (HH-RLHF, SHP, UltraFeedback, PRM800K, HelpSteer2/3, Skywork, Arena, AgentRewardBench) and the evaluation sets (RewardBench 2, RM-Bench, PPE, ProcessBench); the pairs your own gym produces; the training recipe (Bradley–Terry, attribute regression, PRM, generative judge); evaluation; deployment as best-of-n, write-gate score, optimiser metric and RL reward; the over-optimisation (Goodhart) curve and its guard |
| — | The script | The thirty-second and two-minute answers, a glossary, and likely questions with answer shapes |
| — | Reference architecture & pitfalls | The runner, the stores, the grader, the sandbox boundary and the human gate; the four pitfalls that decide unattended operation (prompt injection and memory poisoning, ephemeral sandboxing, network segregation, human-in-the-loop gates); the maturity ladder with the number to watch |
| — | Formulas, datasets & names | pass@k and pass^k, tool-call metrics, agreement, the preference-learning losses (Bradley–Terry, DPO, GRPO, PPO, best-of-n), the datasets table, the systems and papers by name |

## Conventions

- Every number in an example is marked `illustrative` unless a paper, a benchmark or a dataset card is named next to it; public dataset sizes and benchmark definitions follow their cards and papers as of October 2026 — verify before quoting.
- The reward-model recipe, the gym and the loop are designs, not a report of a run.
- The two data charts (pass@k versus pass^k; best-of-n proxy versus gold) use the validated two-colour palette shared with the other primers, one axis per panel, a legend for two series and hover titles on marks.
- Code samples are sketches in Python (LangChain, LangGraph, DSPy, TRL/PEFT-style training, FastAPI), JSON and MCP; library paths and arguments change, the shapes are what matter.
- No personal rate appears on the page.
- The page is a hosted Claude artifact as well; this file is the standalone copy for the repository. It replaces the earlier single-page version of this primer (same file name).

## Related

- `knowledge primers/experience-use-cases/` — the same card-and-tab format applied to the engagements on the resume.
- `knowledge primers/rubrics/` — rubric design and judge calibration, which card 10 relies on for rubric rewards.
- `knowledge primers/agentic-security/` — the sandbox, network and injection defences that card 9 and the reference architecture assume.
- `knowledge primers/toloka-fde-final-round/scoping-and-pricing-playbook.html` — scoping and pricing the agentic gyms and coding environments this page assumes.
- `labs/dataset-examples/12-agentic-gym/` — a runnable τ-bench-style gym that prints pass^k.

## How it was built

Written on 19 October 2026 from the τ-bench and τ²-bench papers, Terminal-Bench and SWE-bench, the Reflexion, Self-Refine and CRITIC papers, DSPy and its optimisers, OPRO, TextGrad and GEPA, Voyager, ExpeL and Generative Agents, the reward-model literature (InstructGPT, HH-RLHF, PRM800K and Math-Shepherd, HelpSteer, Skywork-Reward, RewardBench and RewardBench 2, the over-optimisation scaling laws), the Model Context Protocol specification and the major labs' prompt-injection guidance; rebuilt into the card-and-tab format on 20 October 2026. Benchmark and dataset figures are approximate and dated.
