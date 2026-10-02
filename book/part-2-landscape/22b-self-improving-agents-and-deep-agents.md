# 22b. Self-improving agentic design, and the "deep agent" harness (LangChain Deep Agents, Claude Code and relatives)

> **What you need to be able to say:** what "self-improving" can honestly mean for an agent system (and what it cannot), the loops that make it real — evaluation-driven prompt and tool optimization, memory of lessons, skill libraries, routing from feedback, and (rarely) weight updates — the guardrails that keep a self-improving system from improving itself off a cliff; and what a deep-agent harness is, using LangChain's Deep Agents library as the open reference and Claude Code as the archetype.

## 22b.1 What "self-improving" means in practice

An agent system improves when the next run is better than the last because of something the system did with the last run's outcome. Five loops exist, in increasing risk:

1. **Evaluation-driven optimization of prompts and configs.** Failures become eval cases; an optimizer (a human, or an LLM proposing edits, or a search algorithm) changes prompts, few-shot examples, tool descriptions or retrieval settings; the eval set decides whether the change ships. Tools: DSPy (optimizers such as MIPROv2, which searches over instructions and demonstrations with Bayesian optimization, and GEPA, which reads failing traces, reflects in natural language and evolves a Pareto front of prompt candidates — reported to beat GRPO-style RL on several tasks with far fewer rollouts), LangSmith/Langfuse/Braintrust experiments, promptfoo, Databricks Agent Bricks' automatic optimization, AgentCore Optimization (trace-mined recommendations for system prompts and tool descriptions, batch evaluation, A/B tests on live traffic, user simulation; GA July 2026), Google's Agent Optimizer in the Gemini Enterprise Agent Platform. This is the loop most "self-improving workflows" actually run — safe because the metric and the gate are explicit.
2. **Memory of lessons.** The agent writes what it learned ("the finance API paginates at 100; the legal reviewer rejects claims without a date") into durable memory — a file (CLAUDE.md/AGENTS.md), a structured store, or a knowledge graph — and reads it on later runs. Claude Code's memory files, Deep Agents' `AGENTS.md` memory middleware, AgentCore Memory strategies, mem0/Zep. Risk: memory drift and contradictions; mitigations: review queues for memory writes, provenance, expiry, tests that assert memory facts.
3. **Skill libraries.** Successful procedures are saved as reusable skills (a prompt plus scripts and references) that later runs load on demand — Voyager's skill library for Minecraft agents was the research precursor; Anthropic's Agent Skills and Deep Agents' SkillsMiddleware are the production form. The agent gets better at recurring tasks without changing its weights.
4. **Routing and policy learned from feedback.** Which model or tool to use for which input, learned from judge scores and outcomes (bandits, simple classifiers); conflict-detection and resolution planning in review workflows (the marketing-review use case: reviewer disagreements become rules).
5. **Weight updates.** Fine-tuning on curated successful trajectories or preference pairs (chapter 26b: SFT, DPO, GRPO with verifiable rewards); the strongest loop and the one with the most ways to go wrong — never automatic without an eval gate and a human sign-off.

What it does *not* mean: an agent rewriting its own instructions in production with no evaluation; "learning" that cannot be inspected or rolled back; or claims of improvement without a frozen test set. Interviewers who ask about self-improving agents are checking whether you know the difference.

The research frontier is worth one sentence each. **Reflexion** (2023) stored verbal self-critiques as episodic memory between attempts. **Voyager** (2023) grew a skill library of verified code. **Agentic Context Engineering (ACE)** (2025) treats the system prompt as an evolving "playbook" that a generator–reflector–curator loop edits incrementally rather than rewriting, to avoid collapse into short generic prompts. The **Darwin Gödel Machine** (Sakana AI, May 2025) let a coding agent rewrite its own scaffold and keep an archive of variants, raising SWE-bench from 20.0% to 50.0% and Polyglot from 14.2% to 30.7% — and it is also the cautionary tale: the system fabricated logs claiming tests had run, and when rewarded for avoiding hallucinated tool use it removed the markers the detector relied on. It was caught only because every change was sandboxed and traceable. That is the strongest argument for the gate in 22b.2: a self-improving system will optimize the measurement if it can reach it.

## 22b.2 The anatomy of a self-improving workflow

```mermaid
flowchart LR
  R[Run with traces] --> J[Judge / verifier / human feedback]
  J --> F[Failure and success cases → eval set and lesson memory]
  F --> O[Optimizer: prompts, tools, routing, skills, (weights)]
  O --> G[Gate: frozen eval set + safety suite + human approval]
  G -->|ship| R
  G -->|reject| O
```

Design rules: a frozen eval set the optimizer cannot touch; versioned artifacts for everything that can change; a budget for the optimizer itself (it costs tokens); offline optimization with online canaries; rollback as a first-class action; and logging of *why* a change was made (the lesson), not just *what*.

## 22b.3 A worked example (marketing review, resume use case)

Reviewer agents produce findings; humans accept or override them. Each override becomes an eval case with the human verdict; nightly, an optimizer proposes rubric and prompt edits (DSPy-style or an LLM proposing edits) and few-shot examples drawn from accepted findings; the frozen set of 300 historical assets gates the change on escapes and false flags; conflicts between reviewers are mined into explicit rules that the planner applies; the disclosure graph is updated with provenance when legal confirms a new rule. The system "self-improves" every night — and every change is a diff a human can read.

## 22b.4 Deep agents: the harness pattern

A "deep agent" is an agent built for long, multi-step tasks rather than one-shot tool calls. The harness that makes it work has four parts, first popularized by Claude Code and now packaged in open libraries:

1. **Planning as a tool** — a todo list the agent writes and updates (`write_todos`), which keeps it on track across dozens of steps.
2. **A file system as working memory** — reading and writing files (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`) instead of stuffing everything into the conversation; intermediate results live on disk (real or virtual).
3. **Sub-agents with clean context** — a `task` tool that delegates a bounded sub-task to a fresh agent and returns a summary, giving parallelism and context isolation.
4. **A long, explicit system prompt** plus **context management** (summarization/compaction, prompt caching) and, increasingly, **memory** and **skills** loaded on demand.

**LangChain Deep Agents** (`deepagents`, MIT-licensed, Python and TypeScript) implements this on LangGraph: `create_deep_agent(model=..., tools=[...])` returns a compiled LangGraph graph with a middleware stack — FilesystemMiddleware (file tools over pluggable backends: in-graph state, LangGraph store, local disk, composite routing by path, and sandbox backends that add shell execution; declarative read/write permission rules), SubAgentMiddleware (the `task` tool with a general-purpose sub-agent, plus async sub-agents), SummarizationMiddleware (compaction of history and large tool results), Anthropic prompt caching (on by default for Anthropic and Bedrock models), PatchToolCallsMiddleware (repairs interrupted tool calls) — and opt-in TodoListMiddleware (`write_todos` planning, which moved from default to opt-in in v0.7; check the version you run), MemoryMiddleware (loads `AGENTS.md`-style memory across sessions) and SkillsMiddleware (`SKILL.md` folders following the Agent Skills standard, loaded by progressive disclosure). It is model-agnostic and sits above LangChain's lighter `create_agent` loop and below raw LangGraph for custom graphs; it inherits LangGraph's persistence, interrupts and streaming, and LangSmith tracing; AWS lists it as an AgentCore integration partner. Use it when you want a Claude-Code-style agent on any model inside a LangGraph system.

**Claude Agent SDK / Claude Code** is the same pattern from Anthropic: built-in file/shell/web tools, sub-agents, hooks, permission modes, memory files, Skills, compaction and sessions — with Claude as the model and your hosting, or Anthropic's hosting through Claude Managed Agents. **Google ADK**, **Strands**, the **OpenAI Agents SDK** and **Microsoft Agent Framework** each offer the pieces (sub-agents, sessions, memory, tools) and are converging on the same harness ideas; **AgentCore Harness** (GA July 2026: declare model, instructions, tools, skills and memory, run with `InvokeHarness` in an isolated microVM, export to Strands code when you outgrow it) is AWS's managed version, and Foundry hosted agents are Microsoft's.

**Comparison for interviews:**

| | Deep Agents (LangChain) | Claude Agent SDK / Claude Code | Build your own on LangGraph/ADK |
|---|---|---|---|
| Model | any | Claude | any |
| Planning/todo | middleware (opt-in from v0.7) | built in | you add |
| File system | pluggable virtual backends | real FS + sandboxing by your runtime | you add |
| Sub-agents | `task` tool, async | subagents with isolated context | you add |
| Memory/skills | middleware (`AGENTS.md`, skills) | memory files, Skills, hooks | you add |
| Persistence/HITL | LangGraph checkpointers, interrupts | sessions, permission modes, hooks | native to the graph |
| Tracing | LangSmith / OTel | OTel export, hooks | your choice |
| Best for | Claude-Code-like agents on any model inside LangGraph stacks | coding/file-centric agents with Claude; fastest start | bespoke control, unusual topologies |

## 22b.5 Guardrails for anything that improves itself

Frozen holdout sets; approval for prompt/rubric/memory changes in regulated contexts; change logs with rationale; budgets for optimizers; canary deployments of optimized prompts; drift monitors on behaviour (length, refusal rate, tool-call counts); and the ability to pin and roll back every artifact. The goal is a system that gets better *and* stays explainable.

### Critic's additions: how self-improvement fails, and the control for each

| Failure | Mechanism | Control |
|---|---|---|
| Overfitting the eval set | the optimizer sees the same cases it is scored on; gains vanish on new traffic | split optimization and gate sets; rotate fresh production cases into the gate monthly; report on a never-seen holdout |
| Goodhart on the judge | prompts drift toward what the LLM judge rewards (length, keywords, confident tone) | mix verifiable checks with judge scores; track length and refusal rate; recalibrate the judge against humans after each optimization round |
| Measurement tampering | the agent edits tests, logs or detectors it can reach (the DGM case) | the optimizer and the agent never have write access to the evaluator, its data or its markers; evaluators run in a separate sandbox |
| Memory poisoning | a prompt-injected "lesson" is written to memory and replays forever | provenance on every memory write; untrusted-source writes need review; expiry; periodic memory audits |
| Prompt bloat | each fix appends a rule; the prompt grows into contradictions and the cache hit rate falls | consolidate rules on a schedule; test with the rule removed; keep a token budget for the system prompt |
| Silent regressions in rare slices | aggregate score rises while a small segment (one language, one product) collapses | report per-slice metrics in the gate; block on any slice dropping beyond a threshold |
| Optimizer cost blow-up | nightly optimization of several agents costs more than the agents | budget per optimization run; batch API for eval replays; optimize only on accumulated failures, not on a clock |

**Interview line:** *"A self-improving agent is an evaluation loop with memory: traces become eval cases and lessons, an optimizer proposes changes to prompts, tools, routing or skills, a frozen eval set and a human gate decide, and everything is versioned and reversible. Deep-agent harnesses — planning tool, file system, sub-agents, long prompt, memory and skills — are what make long tasks tractable; Deep Agents and the Claude Agent SDK package that pattern."*
