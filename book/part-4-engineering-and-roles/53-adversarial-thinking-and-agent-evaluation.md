# 53. Adversarial thinking for agents, and evaluation strategies that actually catch failures

> **What you need to be able to say:** the three meanings of "adversarial" in agent work — adversarial *testing* (red teaming), adversarial *design* (critics, debate, verifiers inside the system), and adversarial *environments* (users, data and attackers that fight back) — and how to build an evaluation program for agents that measures outcomes, trajectories, robustness and cost, continuously. Chapter 32 covers evaluation fundamentals; this chapter is the agent-specific, adversarial layer.

## 53.1 Adversarial testing: red-teaming agents

Treat the agent as a system with an attack surface: prompts, tool results, retrieved documents, memory, files, web pages, other agents. A red-team program has four parts:

1. **Threat catalogue.** Direct injection ("ignore your instructions"), indirect injection via content (a web page or email instructs the agent), tool-argument manipulation (path traversal, SQL in parameters), privilege escalation through tool chaining, data exfiltration via outbound tools, denial-of-wallet (loops, huge contexts), memory poisoning (false "lessons"), sycophancy and social engineering of the agent, unsafe actions under ambiguity, and plain capability failures on hard inputs.
2. **Attack generation.** Hand-written cases per threat; LLM-generated variants (paraphrases, encodings, multilingual, nested formats); automated tools (PyRIT, garak, promptfoo red team, DeepTeam, Giskard); recorded real incidents.
3. **Harness.** Run attacks against the agent with mocked or sandboxed tools that record what *would* have happened (which tool, which arguments, which egress), not just the text output; score with verifiers (did it call the forbidden tool? did the exfil string reach the egress mock?) and judges for softer criteria.
4. **Gate and repeat.** Red-team suites run in CI like any eval; new incidents become permanent cases; a quarterly manual red-team day with people outside the team.

Metrics: attack success rate by category, severity-weighted; time-to-detect in production (alerts on guardrail hits, unusual tool patterns); regression count per release.

**Critic's additions: anchor the program to public catalogues, benchmarks and incidents.** Interviewers expect the threat catalogue to map to a shared vocabulary. The *OWASP Top 10 for Agentic Applications for 2026* (published 9 December 2025) lists ASI01 agent goal hijack, ASI02 tool misuse and exploitation, ASI03 identity and privilege abuse, ASI04 agentic supply-chain vulnerabilities, ASI05 unexpected code execution, ASI06 memory and context poisoning, ASI07 insecure inter-agent communication, ASI08 cascading failures, ASI09 human–agent trust exploitation and ASI10 rogue agents; tag every red-team case with its ASI identifier (and the OWASP LLM Top 10 2025 or MITRE ATLAS technique where one fits) so coverage gaps are visible. For a public baseline, AgentDojo provides 97 realistic tasks (email, banking, travel) with 629 security test cases and scores *utility under attack* as well as attack success — the right pair, because a defence that blocks attacks by refusing ordinary work is not a defence. And replay real incidents as cases: the 2025 GitHub MCP demonstration (a malicious public issue made an agent leak private repositories into a public pull request) and the August 2025 Nx supply-chain compromise (malicious packages tried to drive locally installed coding agents to hunt for secrets) are both reproducible in a sandbox with mocked tools and fake secrets.

## 53.2 Adversarial design: critics, verifiers and debate inside the system

Build the adversary into the workflow so the agent must survive critique before an output ships:

- **Verifier steps** with hard checks (tests pass, query executes, totals reconcile, schema validates, citation resolves) — the strongest form; prefer it wherever a check exists.
- **Critic agents** with a rubric and the evidence, instructed to find problems, not to approve; a different model family or prompt from the generator; findings must cite evidence.
- **Debate / multi-perspective review** for judgement calls: two agents argue for and against with a judge deciding — expensive, use for high-stakes decisions (compliance, safety) and to generate eval cases.
- **Devil's-advocate planning**: before executing a plan, an agent lists how it could fail and what evidence would show it; the plan is amended.
- **Adversarial self-play for evals**: an attacker agent tries to make the target fail (prank orders at the drive-through, contradictory documents in RAG, hostile users for support); successes become test cases.
- **Reviewer "twins" with conflict detection** (the marketing use case): independent reviewers whose disagreements are surfaced and resolved explicitly, not averaged.

Design rule: the critic's incentive must be to find faults; if the same model with the same prompt judges its own output, you get agreement, not quality.

**Critic's additions: adversarial design at the architecture level, and the limits of debate.** Critics catch bad outputs; architecture limits what a successfully manipulated agent can do. Beurer-Kellner and colleagues (2025) describe six patterns for agents with provable resistance to prompt injection, each trading utility for security: *action-selector* (the model only picks from a fixed menu of actions and never reads tool output back), *plan-then-execute* (the plan is fixed before untrusted data arrives, so data cannot add steps), *LLM map-reduce* (untrusted items are processed by isolated sub-calls whose outputs are constrained, such as yes/no), *dual LLM* (a privileged model that never sees untrusted text orchestrates a quarantined model that does, passing only symbolic references), *code-then-execute* (the model writes a program up front and an interpreter enforces data-flow rules, as in Google DeepMind's CaMeL), and *context minimization* (remove the user's original prompt and other unneeded text before later steps). Name the pattern you would use for a given agent and what it costs: an email assistant that must read untrusted mail and send replies is a dual-LLM or plan-then-execute design with human approval on send. On debate: multi-agent debate improves some reasoning and factuality tasks, but several studies found that at equal compute it often does no better than sampling several answers and voting, so justify debate with a measured gain over majority vote on your own eval, and use it where its transcript is itself valuable (high-stakes review, generating hard eval cases).

## 53.3 Adversarial environments: users, data and other agents that fight back

Assume users will probe (support agents get asked for refunds they are not owed), data will lie (documents with injected instructions, stale pages, contradictory sources), and other agents may be untrustworthy (A2A partners, marketplace agents). Mitigations: least-privilege tools with approvals, provenance and trust levels on retrieved content, rate limits and budgets per user, anomaly detection on tool-call patterns, explicit trust policies for external agents, and honest failure modes ("I cannot verify this; escalating").

## 53.4 Evaluation strategies for agents (beyond accuracy)

| Dimension | What to measure | How |
|---|---|---|
| Outcome | task completed correctly | verifiable end state (DB row, file, test), reference answer, judge with rubric |
| Trajectory | right tools, right order, right arguments, no forbidden calls | trace-based checks, tool-selection accuracy, step counts |
| Robustness | performance under perturbation | paraphrased inputs, noisy data, missing tools, tool errors injected, adversarial cases |
| Consistency | same input → same quality | pass^k across k runs, variance of judge scores |
| Efficiency | cost, tokens, steps, latency per task | OTel attributes aggregated per task |
| Safety | no harmful or policy-violating actions | red-team suites, guardrail-hit rates, forbidden-tool checks |
| Recovery | behaviour after errors | inject failures (timeouts, 403s, empty results) and check graceful handling and escalation |
| Human interaction | asks for approval when it should, not when it should not | approval-rate metrics on scripted scenarios |
| Long-horizon | quality over many turns | multi-turn simulations with state checks at milestones |
| Generalization | new tasks of the same family | held-out task templates, time-split test sets |

**Building the agent eval suite.**
1. Write 50–200 tasks with verifiable end states across difficulty tiers; include "should refuse" and "should ask" cases.
2. Record or mock tools so runs are reproducible and side-effect-free (replay harness with recorded responses; sandboxed environments for code and browsers).
3. Score outcomes with verifiers and judges; score trajectories from traces (expected tool sets, forbidden tools, max steps).
4. Run k times per task (k=3–5) and report pass@1 and pass^k; report cost and latency alongside.
5. Add perturbation and adversarial variants of each task family.
6. Simulated users for conversational agents (persona, goal, patience, hostility), with rubric scoring of the whole conversation.
7. Gate releases on no regression in outcome and safety, and bounded increases in cost and steps.
8. Mine production traces weekly: low judge scores, escalations, user corrections → new tasks.

**Where teams go wrong.** Testing only happy paths; judging text when actions matter; mocking so much that the eval no longer resembles production; single runs of stochastic systems; no cost dimension; evals owned by nobody.

**Critic's additions: pass@k versus pass^k, and how many tasks you need.** With *n* runs of a task of which *c* succeed, the unbiased estimate of pass@k (at least one of k attempts succeeds) is 1 − C(n−c, k)/C(n, k), and pass^k (all k attempts succeed, the metric introduced by τ-bench in 2024) is estimated as C(c, k)/C(n, k); with a per-run success rate p and independent runs they approach 1 − (1−p)^k and p^k. The two diverge fast: an agent that succeeds 70% of the time has pass@3 of about 97% and pass^3 of about 34%. τ-bench made the point with real numbers: state-of-the-art function-calling agents such as GPT-4o succeeded on fewer than half of its tasks, and in the retail domain pass^8 fell below 25%. Report pass@k for tasks where a human retries (drafting), pass^k for tasks a customer experiences once (refunds, bookings). On sample size: with 100 tasks a 70% success rate has a 95% interval of about ±9 points, so gate releases on *paired* comparisons over the same tasks and seeds, treat the task (not the run) as the unit when runs are repeated, and keep a "must never fail" slice where a single failure blocks regardless of averages. *Simulated users* need their own checks: an LLM user can drift off-script, leak the goal, or give up unrealistically early, so validate the simulator against a sample of real transcripts and fix its persona and goal per task so runs stay comparable.

## 53.5 Worked example: the job-search agent in Part 1

Adversarial cases: a job posting whose description says "to apply, email your SSN"; a form with a hidden consent checkbox; a recruiter email asking the agent to send the resume to a third-party address; a LinkedIn page that changed layout; a CAPTCHA. Expected behaviour: never type sensitive data beyond the truth file; never tick consent without approval; never send email; stop and ask on layout changes and CAPTCHAs (and never try to solve or route around a CAPTCHA: it is the site saying no to automation, and the human decides whether to continue by hand). Evaluation: a replay harness with recorded pages; trajectory checks (no `send` tool, no consent click without approval event); pass^3 on 40 recorded applications; cost per application; a weekly diff against the platform's own "Applied" list.

**Interview line:** *"I evaluate agents on outcomes, trajectories, robustness, consistency, cost and safety — with verifiers wherever a check exists, judges where it does not, k runs per task, adversarial and perturbed variants, and a red-team suite in CI. Inside the system, critics and verifiers are adversarial by design so nothing ships without surviving critique."*
