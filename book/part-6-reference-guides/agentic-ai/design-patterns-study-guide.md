# Agentic AI — Design Patterns, Use Cases & Study Guide

> A comprehensive reference for understanding, designing, and discussing agentic AI systems in technical interviews and applied research.

---

## Table of Contents

1. [What Is an Agentic AI System?](#1-what-is-an-agentic-ai-system)
2. [Core Design Patterns](#2-core-design-patterns)
   - [2.1 Chain of Thought (CoT)](#21-chain-of-thought-cot)
   - [2.2 ReAct (Reasoning + Acting)](#22-react-reasoning--acting)
   - [2.3 Reflection and Self-Critique](#23-reflection-and-self-critique)
   - [2.4 Plan-and-Execute](#24-plan-and-execute)
   - [2.5 Multi-Agent Systems](#25-multi-agent-systems)
   - [2.6 Memory Architecture](#26-memory-architecture)
   - [2.7 Tool Use and Function Calling](#27-tool-use-and-function-calling)
   - [2.8 Retrieval-Augmented Generation (RAG)](#28-retrieval-augmented-generation-rag)
   - [2.9 Human-in-the-Loop (HITL)](#29-human-in-the-loop-hitl)
   - [2.10 Prompt Chaining](#210-prompt-chaining)
3. [Choosing the Right Pattern](#3-choosing-the-right-pattern)
4. [Real-World Use Cases](#4-real-world-use-cases)
5. [Common Failure Modes and Mitigations](#5-common-failure-modes-and-mitigations)
6. [Multi-Agent Architectures Deep Dive](#6-multi-agent-architectures-deep-dive)
7. [The Agentic AI Stack](#7-the-agentic-ai-stack)
8. [Interview Cheat Sheet](#8-interview-cheat-sheet)
9. [Resources in This Folder](#9-resources-in-this-folder)
10. [Key Papers and References](#10-key-papers-and-references)
11. [Real Interview Questions — Deep Dives](#11-real-interview-questions--deep-dives)
    - [11.1 Agentic RAG vs Normal RAG](#111-agentic-rag-vs-normal-rag)
    - [11.2 Multi-Hop Reasoning](#112-multi-hop-reasoning)
    - [11.3 Skills vs MCP](#113-skills-vs-mcp)
    - [11.4 Skill Use Cases Beyond Email Generation](#114-skill-use-cases-beyond-email-generation)

---

## 1. What Is an Agentic AI System?

A traditional LLM interaction is stateless and single-turn: prompt in, response out. An **agentic AI system** breaks this mold — the LLM is embedded in a loop that allows it to reason, take actions, observe results, and iterate toward a goal across multiple steps without requiring human guidance at each one.

### Defining Properties

| Property | Description |
|---|---|
| **Autonomy** | Decides what to do next without explicit instruction at each step |
| **Tool use** | Can act on the world — search, code execution, API calls, file I/O |
| **Memory** | Retains and retrieves context across steps and sessions |
| **Goal-directedness** | Works toward an objective, not just a prompt |
| **Adaptability** | Adjusts behavior based on observations and feedback |

### The Agent Loop

```
┌─────────────────────────────────────────────────────┐
│                   AGENT LOOP                        │
│                                                     │
│   Observe → Think → Decide → Act → Observe → ...   │
│                                                     │
│   Terminates when: goal reached | max steps hit |  │
│   human intervenes | error threshold exceeded       │
└─────────────────────────────────────────────────────┘
```

### Why Agents Now?

Three converging forces made agents practical:

1. **Better reasoning** — LLMs in the 2023–2025 era can follow multi-step instructions reliably enough to sustain an agent loop
2. **Function calling** — structured output (JSON) let models declare tool intent without hallucinating API calls
3. **Long context windows** — 100K–1M token windows let agents maintain rich state without external memory for many tasks

---

## 2. Core Design Patterns

---

### 2.1 Chain of Thought (CoT)

**Core idea:** Prompt the model to externalize its reasoning before producing a final answer. Intermediate reasoning tokens act as scratch space that improves final output quality.

#### Variants

| Variant | Mechanism | Best For |
|---|---|---|
| **Zero-shot CoT** | Append "Let's think step by step" | Quick improvement with no examples |
| **Few-shot CoT** | Provide worked examples with reasoning traces | Consistent format, domain-specific style |
| **Least-to-Most** | Decompose into sub-problems, solve each | Long-horizon math and logic |
| **Self-Consistency** | Sample N chains, take majority vote | Reducing variance, high-stakes answers |
| **Tree of Thought (ToT)** | Branch reasoning into a tree, search/prune | Planning problems, creative tasks |

#### Why It Works

Transformers generate tokens sequentially. Every reasoning token the model writes before the final answer gives it additional "compute" to work through complexity. More tokens = more intermediate state the model can condition on.

#### Example — Zero-shot CoT

```
Prompt:
  A train travels 60 mph for 2.5 hours, then 45 mph for 1.5 hours.
  What is the total distance? Let's think step by step.

Model:
  Step 1: Distance for first leg = 60 × 2.5 = 150 miles
  Step 2: Distance for second leg = 45 × 1.5 = 67.5 miles
  Step 3: Total = 150 + 67.5 = 217.5 miles
```

#### When to Use

- Multi-step math and logic
- Code generation (reason about edge cases first)
- Medical or legal differential reasoning
- Any task where accuracy matters more than speed

---

### 2.2 ReAct (Reasoning + Acting)

**Core idea:** Interleave reasoning traces with tool actions in a tight loop. At each step the model produces a Thought → Action → Observation cycle, repeating until it reaches a final answer.

**Paper:** Yao et al. (2022) — *ReAct: Synergizing Reasoning and Acting in Language Models*

#### The ReAct Loop

```
┌──────────────────────────────────────────────────────┐
│  Thought   → What do I need? What should I do next?  │
│  Action    → tool_name(parameters)                   │
│  Observation → <tool result injected into context>   │
│  ... repeat until done ...                           │
│  Final Answer → synthesized response                 │
└──────────────────────────────────────────────────────┘
```

#### Example — Research Agent

```
User: What is the population of Tokyo and how does it compare to NYC?

Thought: I need current population figures for both cities.
Action: search("Tokyo population 2025")
Observation: Tokyo metropolitan area population is approximately 37.4 million.

Thought: Now I need NYC's population.
Action: search("New York City population 2025")
Observation: NYC population is approximately 8.3 million (city) / 20 million (metro).

Thought: I have both figures. Tokyo metro is ~37.4M, NYC metro is ~20M.
         That's roughly 1.87x larger.
Action: calculator(37.4 / 20)
Observation: 1.87

Final Answer: Tokyo's metropolitan area (~37.4M) is approximately 1.87× 
              larger than NYC's metro area (~20M).
```

#### Why ReAct Over Pure Reasoning?

- Pure reasoning fails on stale or unknown facts — the model hallucinates
- Pure tool use is brittle — rigid pipelines can't adapt to unexpected results
- ReAct combines both: dynamic selection of tools + reasoning about what results mean

#### Common Tools in ReAct Agents

| Tool | Purpose |
|---|---|
| `search(query)` | Web or vector-store retrieval |
| `calculator(expr)` | Precise arithmetic |
| `run_code(code)` | Python execution, data analysis |
| `read_file(path)` | File system access |
| `api_call(endpoint, params)` | External service calls |
| `browser(url, action)` | Web navigation and extraction |
| `spawn_agent(task)` | Delegate to a subagent |

---

### 2.3 Reflection and Self-Critique

**Core idea:** Treat the model's first output as a draft. A second pass — by the same model or a separate critic — evaluates and revises the output. Mimics the "draft → review → revise" cycle.

#### Variants

**Self-Reflection** — same model critiques its own output:
```
[Generate]  → Draft response
[Critique]  → "Is this correct? What's missing? What could be wrong?"
[Revise]    → Improved response based on critique
```

**Constitutional AI** — check output against fixed principles, revise until passing:
```
Principles: [accurate, helpful, harmless, complete]
For each principle → score → revise if failing → accept when all pass
```

**Reflexion** (Shinn et al., 2023) — store verbal reflections of past failures in memory:
```
Episode 1 → Agent fails task
Reflection stored → "I called the delete API before confirming the target"
Episode 2 → Agent reads stored reflection → avoids the mistake
```

**Critic-Generator** — two separate model instances, one generates, one critiques:
```
Generator → Code solution
Critic    → "Off-by-one error on line 8; doesn't handle null input"
Generator → Revised solution
Critic    → "Correct." → Accept
```

#### Example — Code Review Loop

```python
max_rounds = 3
solution = llm(f"Solve: {problem}")

for _ in range(max_rounds):
    critique = llm(f"""
    Review this code for bugs, edge cases, and inefficiency:
    {solution}
    
    Format: list specific issues with line references.
    If correct, respond only with "LGTM".
    """)
    
    if critique.strip() == "LGTM":
        break
    
    solution = llm(f"""
    Fix the following issues in your code:
    {critique}
    
    Original code:
    {solution}
    """)
```

#### When to Use

- Safety-critical outputs (medical, legal, financial)
- Code generation where correctness is testable
- Long-form content with quality requirements
- Any task where a first pass is likely insufficient

---

### 2.4 Plan-and-Execute

**Core idea:** Separate planning from execution. A planner decomposes a high-level goal into a task graph. Executors (which may be simpler models, specialized agents, or code) carry out each step.

#### Architecture

```
Goal
  ↓
[Planner LLM]  →  Task Graph / Ordered Steps
                        ↓
        ┌───────────────┼───────────────┐
    [Task 1]        [Task 2]        [Task 3]
    Executor        Executor        Executor
        └───────────────┼───────────────┘
                        ↓
               [Result Synthesizer]
                        ↓
                  Final Output
```

#### Why Separate Planning and Execution?

1. **Human review** — plans can be inspected before any action is taken
2. **Specialization** — different executors for different task types
3. **Parallelism** — independent tasks run concurrently
4. **Failure isolation** — one executor failing doesn't abort the entire plan
5. **Re-planning** — the planner can revise the plan if an executor reports failure

#### Example — Market Research Agent

```
Goal: "Produce a competitive analysis of the top 3 CRM platforms"

Plan (planner output):
  1. Identify top 3 CRMs by market share [search]
  2. For each CRM:
     a. Scrape pricing page [browser]
     b. Extract feature list [browser + LLM]
     c. Collect user reviews from G2 [scraper]
  3. Build comparison table [LLM]
  4. Write executive summary [LLM]

Execution:
  - Steps 2a, 2b, 2c run in parallel per CRM
  - Step 3 depends on completion of all Step 2s
  - Step 4 depends on Step 3
```

#### Re-planning Pattern

```python
plan = planner.create_plan(goal)

for step in plan:
    result = executor.run(step)
    
    if result.failed:
        # Feed failure back to planner
        plan = planner.replan(
            original_goal=goal,
            completed_steps=plan.completed,
            failed_step=step,
            failure_reason=result.error
        )
```

---

### 2.5 Multi-Agent Systems

**Core idea:** Distribute work across specialized agents that communicate. Each agent has a defined role, tool set, and scope. The whole system achieves goals no single agent could handle efficiently alone.

**See:** `multiagent archtiectures.pdf` and `Multi-Agent Frameworks — A Complete Guid.md` in this folder.

#### Topologies

**Orchestrator → Subagents**
```
[Orchestrator]
    ├── [Research Agent]   → web search, summarization
    ├── [Code Agent]       → generation, execution, testing
    ├── [Writer Agent]     → drafting, editing, formatting
    └── [Review Agent]     → quality control, fact-checking
```

**Peer-to-Peer / Debate**
```
[Agent A: Pro position] ←→ [Agent B: Con position]
            ↓                        ↓
              [Judge Agent: Synthesizes verdict]
```

**Hierarchical**
```
[CEO Agent]
    ├── [Department Agent A]
    │       ├── [Worker Agent 1]
    │       └── [Worker Agent 2]
    └── [Department Agent B]
            ├── [Worker Agent 3]
            └── [Worker Agent 4]
```

**Pipeline (linear)**
```
[Researcher] → [Analyst] → [Writer] → [Editor] → [Publisher]
```

#### Example — Software Engineering Team Simulation

```
User: "Build a REST API for user authentication with JWT"

[PM Agent]
  → Writes requirements doc: endpoints, auth flows, error codes

[Architect Agent]
  → Reads requirements
  → Designs: POST /register, POST /login, GET /me, POST /refresh
  → Specifies: JWT payload structure, token TTLs, DB schema

[Dev Agent]
  → Reads architecture spec
  → Implements FastAPI code with SQLAlchemy models

[QA Agent]
  → Reads implementation
  → Writes pytest suite covering happy paths + edge cases
  → Runs tests → reports 2 failures to Dev Agent

[Dev Agent]
  → Reads failure report
  → Fixes: missing refresh token rotation + bcrypt import error

[QA Agent]
  → Re-runs tests → all pass
  → Writes test coverage report

[PM Agent]
  → Confirms completion
  → Writes handoff summary
```

#### Coordination Mechanisms

| Mechanism | Description | Trade-offs |
|---|---|---|
| **Shared scratchpad** | All agents read/write a central document | Simple, but can conflict |
| **Message queue** | Agents post/consume messages asynchronously | Decoupled, scalable, harder to debug |
| **Direct delegation** | Orchestrator calls subagents via structured API | Tight control, single point of failure |
| **Blackboard** | Agents post partial results; others build on them | Emergent coordination, unpredictable order |
| **Event-driven** | Agents subscribe to event types | Reactive, good for real-time systems |

#### Multi-Agent vs. Single Agent

| Dimension | Single Agent | Multi-Agent |
|---|---|---|
| Complexity | Lower | Higher |
| Specialization | Generalist | Can be domain-expert |
| Parallelism | Sequential | Concurrent |
| Cost | Lower per task | Higher (multiple model calls) |
| Failure modes | Simpler to debug | Cascading failures, harder to trace |
| Capability ceiling | Limited by context | Higher for complex tasks |

---

### 2.6 Memory Architecture

**Core idea:** Give agents the ability to read from and write to persistent stores so they can learn from experience, personalize, and maintain state across sessions.

#### Memory Types

| Type | Analogy | Storage | Retrieval |
|---|---|---|---|
| **In-context (working)** | RAM | Prompt window | Immediate, but ephemeral |
| **Conversation buffer** | Short-term memory | Rolling message list | Last N turns |
| **Episodic** | Journal | Vector DB | Semantic similarity search |
| **Semantic** | Encyclopedia | Knowledge graph / vector DB | Structured query + similarity |
| **Procedural** | Muscle memory | Fine-tuned weights / cached prompts | Implicit (baked in) |

#### Memory Operations

```
WRITE  → Distill and store a fact, observation, or plan
READ   → Retrieve top-K relevant memories for current context
UPDATE → Overwrite stale or incorrect entries
FORGET → Remove irrelevant, private, or expired information
```

#### Example — Personalized Coding Assistant

```python
# On each turn:
query_embedding = embed(user_message)
relevant_memories = vector_db.search(query_embedding, top_k=5)

prompt = f"""
You are a coding assistant for this user.

What you know about them and their project:
{format_memories(relevant_memories)}

User: {user_message}
"""

response = llm(prompt)

# After turn — distill new facts worth storing:
new_facts = llm(f"""
From this conversation turn, extract any facts worth remembering
about the user, their preferences, or their project.
Return as a list. If nothing new, return empty list.

User said: {user_message}
Assistant said: {response}
""")

for fact in new_facts:
    vector_db.upsert(embed(fact), fact, metadata={"timestamp": now()})
```

#### Memory Compression

For long agent runs, the context window fills up. Strategies:

- **Summarization** — periodically summarize the conversation so far into a compressed form
- **Forgetting** — drop old, low-relevance memories based on recency + importance scores
- **Hierarchical memory** — recent events in full detail, older events as summaries
- **External offload** — move everything beyond N tokens to a vector store, retrieve on demand

---

### 2.7 Tool Use and Function Calling

**Core idea:** The model doesn't execute tools itself — it declares intent via structured output (JSON), and the host environment executes the tool and returns the result. This separation is fundamental to safety.

#### The Function Calling Protocol

```
1. Model receives tool schemas in system prompt
2. Model outputs structured JSON declaring tool intent:
   {"tool": "search", "parameters": {"query": "Anthropic funding 2024"}}
3. Host parses JSON, calls actual tool, returns result
4. Result is appended to context as an observation
5. Model continues reasoning from updated context
```

#### Tool Design Principles

1. **Narrow scope** — each tool does one thing well; avoid "do_everything" tools
2. **Typed schemas** — clear parameter definitions prevent ambiguous calls
3. **Idempotency** — prefer tools that are safe to retry
4. **Reversibility** — write to temp before overwriting; prefer soft deletes
5. **Informative errors** — error messages are data; the model should be able to adapt
6. **Least privilege** — tools should have only the access they need

#### Tool Categories

| Category | Examples | Risk Level |
|---|---|---|
| **Read / retrieve** | search, read_file, query_db | Low |
| **Compute** | calculator, run_code, render_template | Medium |
| **Write local** | write_file, create_db_record | Medium |
| **External state** | send_email, post_slack, API POST | High |
| **System** | run_shell, deploy, restart_service | Critical |
| **Agent delegation** | spawn_agent, call_specialist | Medium–High |

---

### 2.8 Retrieval-Augmented Generation (RAG)

**Core idea:** Before generating, retrieve relevant documents from an external knowledge base and inject them into context. Solves the knowledge cutoff problem and reduces hallucination on factual questions.

#### Standard RAG Pipeline

```
Query
  ↓
[Embedding Model]  →  Query Vector
                           ↓
                   [Vector DB Search]
                           ↓
                  Top-K Relevant Chunks
                           ↓
Prompt = System Prompt + Retrieved Context + Query
                           ↓
                    [LLM Generates Answer]
```

#### Agentic RAG Extensions

| Extension | Description |
|---|---|
| **Iterative RAG** | If retrieval is insufficient, agent generates a follow-up query and retrieves again |
| **HyDE** | Generate a hypothetical ideal answer, embed it, use *that* embedding to retrieve |
| **Self-RAG** | Model decides *whether* to retrieve at all; critiques retrieved passages for relevance |
| **Corrective RAG** | Scores retrieved docs; if all low-relevance, falls back to web search |
| **Graph RAG** | Retrieves from a knowledge graph, capturing entity relationships |

#### RAG vs. Fine-tuning

| Dimension | RAG | Fine-tuning |
|---|---|---|
| Knowledge freshness | Real-time | Frozen at training time |
| Cost to update | Reindex documents | Retrain model |
| Factual grounding | Citations possible | Opaque |
| Latency | Higher (retrieval step) | Lower |
| Best for | Factual Q&A, enterprise KB | Style, format, task adaptation |

---

### 2.9 Human-in-the-Loop (HITL)

**Core idea:** Define checkpoints where the agent pauses and requests human confirmation — especially before irreversible or high-stakes actions.

#### Trust Escalation Model

```
Level 1 — Fully automated:
  Read files, web search, calculations, read-only API calls

Level 2 — Soft confirmation (show what will happen):
  Write files, create records, send internal messages

Level 3 — Hard confirmation (explicit approval required):
  Send external communications, delete data, financial operations

Level 4 — Always manual:
  Production deployments, policy changes, large financial transactions
```

#### Interrupt Triggers

- Action affects external state (email, payment, deployment)
- Agent confidence below a threshold
- Action falls outside predefined scope
- User preference for review at this step type
- Anomaly detected (unexpected tool output, unfamiliar data)

#### HITL Patterns

**Approve/reject** — agent presents plan, human approves or rejects before execution

**Edit and continue** — human edits the agent's proposed action, agent continues with edited version

**Escalation** — agent routes to human when it can't resolve a situation

**Audit trail** — agent logs all actions; human reviews asynchronously; can revert

---

### 2.10 Prompt Chaining

**Core idea:** Break a complex task into a linear sequence of LLM calls, where each call's output feeds the next. Unlike an agent loop (dynamic), prompt chains are static pipelines defined upfront.

#### When Chains vs. Agents

| Chains | Agents |
|---|---|
| Steps known in advance | Steps depend on prior results |
| Predictable and auditable | Flexible and adaptive |
| Easier to test and debug | Higher capability ceiling |
| Lower latency | Can handle unexpected situations |
| Good for production pipelines | Good for open-ended tasks |

#### Example — Automated Report Pipeline

```
Raw Data
  ↓ [Step 1: Summarize raw data into key statistics]
Statistical Summary
  ↓ [Step 2: Identify 3 most significant trends]
Trend List
  ↓ [Step 3: Write executive narrative from trends]
Draft Narrative
  ↓ [Step 4: Fact-check narrative against raw data]
Verified Narrative
  ↓ [Step 5: Format into Markdown report with sections]
Final Report
```

---

## 3. Choosing the Right Pattern

| Situation | Recommended Pattern |
|---|---|
| Complex reasoning, no external data | Chain of Thought |
| Reasoning + real-world lookups | ReAct |
| Quality-critical or safety-sensitive output | Reflection / Critic |
| Long-horizon multi-step tasks | Plan-and-Execute |
| Specialized parallel workstreams | Multi-Agent |
| Factual grounding from a document corpus | RAG |
| Personalization or continuity across sessions | Memory Architecture |
| High-stakes or irreversible actions | HITL |
| Known, repeatable production pipeline | Prompt Chaining |

**Patterns compose.** A production customer support agent might use:
- RAG (knowledge base retrieval)
- ReAct (CRM lookups, order status)
- Reflection (quality check before sending)
- HITL (escalation for edge cases or large refunds)
- Memory (customer history and preferences)

---

## 4. Real-World Use Cases

### Software Engineering Agents
- **Code generation** — generate, test, debug in a loop (ReAct + Reflection)
- **Code review** — critic agent flags issues, writer agent fixes (Multi-Agent)
- **Repo exploration** — search files, understand architecture, answer questions (ReAct + RAG)
- **CI/CD agents** — monitor build failures, diagnose, open PRs with fixes

### Research and Knowledge Work
- **Literature review** — retrieve papers, extract claims, synthesize, cite (RAG + Plan-and-Execute)
- **Competitive intelligence** — multi-source web research, structured output (ReAct + Multi-Agent)
- **Data analysis** — write code, execute, interpret results, iterate (ReAct + CoT)

### Customer Operations
- **Support agents** — answer questions from KB, handle returns, escalate (RAG + ReAct + HITL)
- **Sales agents** — qualify leads, draft outreach, log to CRM (Multi-Agent + HITL)
- **Onboarding agents** — guide users through setup, adapt to their responses (Memory + ReAct)

### Healthcare and Science
- **Clinical decision support** — retrieve guidelines, reason through differentials (RAG + CoT + HITL)
- **Drug discovery** — design experiments, run simulations, reflect on results (Plan-and-Execute + Reflection)
- **Medical record summarization** — extract, structure, verify (Chaining + Reflection)

### Finance and Legal
- **Document analysis** — extract clauses, flag anomalies, compare against templates (RAG + Reflection)
- **Financial research** — retrieve filings, compute ratios, draft memos (ReAct + CoT)
- **Compliance monitoring** — monitor transactions, flag anomalies, generate reports (Multi-Agent + HITL)

---

## 5. Common Failure Modes and Mitigations

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Hallucination** | Confabulating facts during reasoning | RAG, Reflection, grounded tool calls |
| **Infinite loops** | Agent can't determine stopping condition | Max step limits; explicit done-state |
| **Tool misuse** | Wrong parameters, wrong tool selected | Strong JSON schemas, few-shot examples |
| **Context overflow** | Long chains exhaust context window | Summarization steps, memory compression |
| **Cascading errors** | Early mistake amplified by later steps | Reflection checkpoints, human review |
| **Goal misgeneralization** | Agent pursues proxy metric, not true goal | Clear success criteria; output validators |
| **Excessive cost** | Runaway loops with expensive model calls | Budget caps; cheap model for routing/planning |
| **Prompt injection** | Malicious content in tool results hijacks agent | Sanitize observations; restricted tool scopes |
| **State corruption** | Agent writes incorrect state to memory/DB | Optimistic locking, dry-run modes, audit logs |
| **Premature termination** | Agent gives up before solving the problem | Retry logic; re-planning on failure |

---

## 6. Multi-Agent Architectures Deep Dive

> See also: `multiagent archtiectures.pdf` and `Multi-Agent Frameworks — A Complete Guid.md`

### Key Design Decisions

**1. How do agents communicate?**
- Shared state (blackboard) — simple but can produce race conditions
- Message passing — decoupled but requires routing logic
- Direct API calls — tight control but creates bottlenecks
- Event bus — scalable, eventually consistent

**2. How is work routed?**
- Central orchestrator (hub-and-spoke) — single point of control and failure
- Emergent routing (agents decide who to call) — flexible but unpredictable
- Static pipeline — predictable, inflexible
- Capability registry — agents advertise skills; router matches tasks to agents

**3. How do agents maintain shared context?**
- Full context passed with every message — high token cost, always consistent
- Reference-passing — agents share pointers to shared storage — efficient, requires coordination
- Summarized handoffs — each agent summarizes what the next needs — risk of information loss

**4. How do you handle failures?**
- Retry with backoff — for transient failures
- Re-planning — for strategic failures (wrong approach)
- Escalation — route to human or more capable agent
- Compensation — undo completed steps before re-trying

### Agent Communication Protocol (A2A)

Google's Agent-to-Agent (A2A) protocol (see `Secure Multi-Agent Orchestration with A2A | Google Cloud.pdf`) defines a standard for:
- Agent capability advertisement (agent cards)
- Task delegation format
- Result reporting
- Authentication between agents

This is an emerging standard for interoperable multi-agent systems.

### Single Agent vs. Multi-Agent: Research Findings

Recent research (`Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning...pdf`) shows that under equal token budgets, single agents with CoT often match or beat multi-agent systems on multi-hop reasoning. Key insight: **multi-agent adds value for parallelism and specialization, not just raw reasoning complexity.** Use multi-agent when tasks can be genuinely decomposed into independent parallel workstreams, not just because a task is "complex."

---

## 7. The Agentic AI Stack

### Frameworks

| Framework | Language | Strengths |
|---|---|---|
| **LangGraph** | Python | Graph-based state machines, streaming, persistence |
| **AutoGen** | Python | Multi-agent conversation patterns, human-in-loop |
| **CrewAI** | Python | Role-based multi-agent, easy setup |
| **Claude Agent SDK** | Python | Native Anthropic integration, safety-first |
| **LlamaIndex Workflows** | Python | RAG-native, event-driven |
| **Semantic Kernel** | Python / C# | Enterprise-oriented, Microsoft ecosystem |

### Key Infrastructure Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTIC AI STACK                         │
├─────────────────────────────────────────────────────────────┤
│  Application Layer     │  UI, API endpoints, user auth       │
├─────────────────────────────────────────────────────────────┤
│  Orchestration Layer   │  LangGraph, AutoGen, CrewAI        │
├─────────────────────────────────────────────────────────────┤
│  LLM Layer             │  Claude, GPT-4, Gemini, Llama      │
├─────────────────────────────────────────────────────────────┤
│  Tool Layer            │  Search, code exec, browser, APIs  │
├─────────────────────────────────────────────────────────────┤
│  Memory Layer          │  Vector DB, KV store, RDBMS        │
├─────────────────────────────────────────────────────────────┤
│  Observability Layer   │  LangSmith, Langfuse, traces       │
└─────────────────────────────────────────────────────────────┘
```

### Observability Essentials

Production agents need:
- **Traces** — full step-by-step log of every thought, action, observation
- **Span timing** — latency per step to identify bottlenecks
- **Token counts** — cost tracking per agent and per step
- **Error rates** — failure frequency per tool and agent
- **Human feedback** — thumbs up/down, corrections, escalation rates

---

## 8. Interview Cheat Sheet

### "What is an AI agent?"
> An AI agent is an LLM embedded in a loop that can observe its environment, reason about what to do, take actions via tools, and iterate toward a goal — autonomously, across multiple steps.

### "What is ReAct?"
> ReAct interleaves reasoning (Thought) with actions (Action + Observation) in a loop. The model reasons about what tool to call, calls it, observes the result, and reasons again. This grounds the model's reasoning in real-world state rather than relying on potentially stale parametric knowledge.

### "What is the difference between CoT and ReAct?"
> CoT is purely internal — the model reasons without taking actions. ReAct extends CoT by allowing the model to call external tools. Use CoT when all necessary information is in the prompt; use ReAct when the model needs to retrieve or compute information from the environment.

### "What is Reflection?"
> Reflection has the model (or a separate critic) evaluate its own output and produce a critique. The model then revises based on the critique. This simulates a review cycle and is effective for code generation, fact-checking, and quality-critical outputs.

### "When would you use multi-agent vs. single agent?"
> Multi-agent adds value when tasks can be parallelized across specialized agents, when the total context needed exceeds a single window, or when different subtasks benefit from different tools or prompting strategies. For reasoning complexity alone, a well-prompted single agent often matches multi-agent at lower cost.

### "How do you prevent an agent from looping forever?"
> Set a maximum number of steps. Use an explicit done-state that the agent must produce. Implement a goal-checking function that evaluates whether the task is complete after each step. Add budget limits (cost, time) as hard stops.

### "What is the role of memory in agents?"
> Memory lets agents maintain context across sessions (episodic), store and retrieve facts (semantic), and avoid repeating past mistakes (Reflexion). Without memory, each session starts from zero. Vector databases are the most common implementation for fuzzy retrieval; key-value stores work for structured state.

### "How do you handle tool errors in an agent?"
> Return informative error messages as observations — the model should be able to read the error and decide whether to retry with different parameters, try a different tool, ask for clarification, or escalate to a human.

---

## 9. Resources in This Folder

| File | What It Covers |
|---|---|
| `Multi-Agent Frameworks — A Complete Guid.md` | Practical guide to building with multi-agent frameworks |
| `multiagent archtiectures.pdf` | Architectural patterns for multi-agent systems |
| `Secure Multi-Agent Orchestration with A2A \| Google Cloud.pdf` | Google's A2A protocol for secure agent-to-agent communication |
| `Single-Agent LLMs Outperform Multi-Agent Systems...pdf` | Research: when single agents beat multi-agent under equal token budgets |
| `recent_multiagent_papers_reading_list.md` | Curated reading list of foundational and recent papers |

---

## 10. Key Papers and References

### Foundational

| Paper | Key Contribution |
|---|---|
| Wei et al. (2022) — *Chain-of-Thought Prompting* | Demonstrated CoT dramatically improves multi-step reasoning |
| Yao et al. (2022) — *ReAct* | Interleaving reasoning and acting; benchmark-setting agent framework |
| Shinn et al. (2023) — *Reflexion* | Verbal reinforcement learning via reflection stored in memory |
| Yao et al. (2023) — *Tree of Thoughts* | Branching CoT for planning and search problems |
| Significant-Gravitas (2023) — *AutoGPT* | Popularized autonomous multi-step agents |
| Park et al. (2023) — *Generative Agents* | Simulated social agents with memory and planning |

### Architecture and Safety

| Paper | Key Contribution |
|---|---|
| Anthropic (2024) — *Claude's Model Spec* | Principles for safe agentic behavior and trust hierarchies |
| Wang et al. (2024) — *Survey of LLM Agents* | Comprehensive taxonomy of agent components and patterns |
| Google DeepMind (2024) — *A2A Protocol* | Standardized agent-to-agent communication |

### Evaluation

| Paper | Key Contribution |
|---|---|
| Liu et al. (2023) — *AgentBench* | Benchmark for evaluating LLM agents across real-world tasks |
| Jimenez et al. (2024) — *SWE-bench* | Code agent benchmark on real GitHub issues |

---

---

## 11. Real Interview Questions — Deep Dives

---

### 11.1 Agentic RAG vs Normal RAG

#### The Short Answer
Normal RAG is a fixed, single-pass pipeline. Agentic RAG treats retrieval as a dynamic, reasoned action — the agent decides *whether* to retrieve, *what* to search for, *how many times*, and *whether the results are good enough*.

#### Normal RAG — What It Does

```
User query
    ↓
Embed query → search vector DB → retrieve top-K chunks
    ↓
Stuff chunks into prompt → LLM generates answer
```

**Limitations of normal RAG:**
- The query is used as-is — if the user phrases it poorly, retrieval fails
- Always retrieves, even when the answer is already in context
- Single shot — no retry if the retrieved chunks miss the point
- Can't combine information across multiple retrieval passes
- No verification that retrieved content actually supports the answer

#### Agentic RAG — What It Adds

| Capability | Description | Benefit |
|---|---|---|
| **Query decomposition** | Breaks a complex question into sub-queries, retrieves for each | Handles multi-part and ambiguous questions |
| **Iterative retrieval** | If first retrieval is poor, reformulates query and retrieves again | Higher recall on difficult questions |
| **Self-RAG** | Agent decides *whether* retrieval is needed at all | Saves latency and cost for simple questions |
| **Corrective RAG** | Scores retrieved chunks for relevance; falls back to web search if all are low | Avoids hallucinating from irrelevant context |
| **HyDE** | Generates a hypothetical ideal answer, embeds *that*, uses it to retrieve | Retrieves more semantically relevant chunks |
| **Multi-source routing** | Agent chooses which knowledge base to query based on question type | Better precision, avoids noise from wrong corpus |
| **Citation verification** | Agent checks that each claim is supported by what was actually retrieved | Reduces hallucination in the final answer |

#### Example — Why Agentic RAG Wins on a Complex Question

**Question:** *"What does our refund policy say about digital goods, and has it changed in the last year?"*

**Normal RAG:**
- Embeds the full question
- Retrieves top-5 chunks from the policy KB
- May get chunks about physical goods, not digital
- Has no way to retrieve change history
- Generates a potentially wrong answer

**Agentic RAG:**
```
Thought: This has two parts — current policy for digital goods, 
         and historical changes. I'll retrieve separately.

Action: search(kb="policy", query="refund policy digital goods")
Observation: [Chunk: "Digital goods are non-refundable except within 
              48 hours of purchase..."]

Thought: Good. Now I need to find if this changed recently.
Action: search(kb="policy_changelog", query="refund policy digital goods 2024 2025")
Observation: [Chunk: "2024-11-01: Extended digital goods refund window 
              from 24h to 48h"]

Thought: I have both pieces. I can now give a complete, verified answer.
Final Answer: Current policy allows refunds on digital goods within 48 hours.
              This was extended from 24 hours in November 2024.
```

#### When to Use Each

| Use Normal RAG | Use Agentic RAG |
|---|---|
| Simple, single-topic questions | Complex, multi-part questions |
| Controlled, high-quality corpus | Mixed-quality or multi-source corpus |
| Latency is critical | Accuracy is critical |
| Budget-constrained | Quality-constrained |
| Production pipeline with known query types | Open-ended Q&A or research |

---

### 11.2 Multi-Hop Reasoning

#### What It Is

Multi-hop reasoning answers questions that **cannot be resolved from a single document or a single reasoning step**. The answer to step N depends on the result of step N-1. Each "hop" bridges a gap between a known fact and an unknown one.

```
Question → [Hop 1: retrieve/reason] → Intermediate fact
         → [Hop 2: retrieve/reason] → Intermediate fact
         → [Hop 3: retrieve/reason] → Final Answer
```

#### Classic Examples

**Example 1 — Knowledge graph traversal:**
```
Q: "Who is the CEO of the company that acquired Slack?"

Hop 1: What company acquired Slack?
       → Salesforce (acquired in 2021)
Hop 2: Who is the CEO of Salesforce?
       → Marc Benioff

Answer: Marc Benioff
```

**Example 2 — Policy + compliance:**
```
Q: "Is our product compliant with GDPR's rules on data retention 
     for minors?"

Hop 1: What does GDPR say about data retention for minors?
       → Article 8: member states may lower consent age to 13; 
         data must be deleted upon request regardless of age

Hop 2: What is our product's data retention policy?
       → We retain user data for 3 years after account deletion

Hop 3: Do we have a special path for minor account deletion?
       → No special path found in policy docs

Answer: Partial gap — deletion timeline may violate GDPR 
        for minor accounts. Escalate for legal review.
```

**Example 3 — Financial chain:**
```
Q: "What is the credit rating of the parent company of 
     the brand that makes AirPods?"

Hop 1: What brand makes AirPods? → Apple
Hop 2: What is Apple's parent company? → Apple Inc. (self)
Hop 3: What is Apple's credit rating? → AA+ (S&P)

Answer: AA+
```

#### When Multi-Hop Reasoning Is Needed

- **Knowledge base Q&A** — facts are spread across separate documents
- **Research synthesis** — connecting findings across papers
- **Legal/compliance** — trace a regulation → company policy → specific implementation
- **Medical** — symptom → diagnosis → treatment → contraindication check
- **Competitive intelligence** — company → acquisition history → technology portfolio → patent filings
- **Debugging** — error → root cause → related component → fix

#### How It's Implemented

**In RAG systems:** Retrieve → extract intermediate fact → use that fact as next query → retrieve again

**In agent systems (ReAct):** The Thought-Action-Observation loop naturally supports multi-hop — each observation feeds the next thought, which may trigger another tool call

**In CoT:** The model reasons through all hops internally, without external retrieval (only works if all facts are in the training data or context)

#### The Research Finding (From This Folder)

The paper *"Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets"* shows that a single agent with sufficient reasoning tokens often handles multi-hop better than multi-agent setups that split the hops across agents — because inter-agent communication overhead and context loss outweigh the benefits of parallelism for sequential reasoning chains. **Multi-hop is inherently sequential; multi-agent is for parallelism.**

#### Interview One-Liner
> "Multi-hop reasoning is when the answer to a question requires a chain of intermediate lookups or inferences, where each step's output becomes the next step's input. It's used whenever no single document or reasoning step can answer the question directly."

---

### 11.3 Skills vs MCP

These are often confused because both extend what an AI system can do — but they operate at completely different levels of abstraction.

#### The Core Distinction

| | Skills | MCP (Model Context Protocol) |
|---|---|---|
| **What it is** | A reusable behavioral workflow | A protocol (standard interface) for connecting tools/data to models |
| **Analogy** | An appliance (uses power to do something useful) | An electrical outlet (standard interface for power) |
| **Level** | High-level — HOW to approach a task | Low-level — WHAT capabilities are available |
| **Defines** | Sequence of steps, prompts, decision logic | Tool schemas, resource endpoints, data formats |
| **Created by** | Prompt engineers, product teams | Developers building integrations |
| **Consumed by** | The LLM following structured instructions | The LLM calling structured tool APIs |

#### MCP — What It Is

MCP (Model Context Protocol, developed by Anthropic) is a **standard protocol** for exposing tools, resources, and context to LLMs. An MCP server advertises a set of capabilities; any MCP-compatible client (Claude, an IDE plugin, an agent framework) can connect and call them.

Think of it as USB-C for AI tools — one standard connector, many devices.

**MCP provides three things:**
1. **Tools** — functions the model can call (read_file, search_db, create_issue)
2. **Resources** — data the model can access (a file, a database row, a webpage)
3. **Prompts** — pre-built prompt templates the server exposes

**MCP Examples:**

| MCP Server | Tools It Exposes |
|---|---|
| **GitHub MCP** | `create_pr`, `read_file`, `search_code`, `list_issues`, `merge_pr` |
| **Jira/Confluence MCP** | `create_issue`, `search_jql`, `get_page`, `add_comment`, `transition_issue` |
| **Filesystem MCP** | `read_file`, `write_file`, `list_directory`, `search_files` |
| **Database MCP** | `query`, `insert`, `update`, `list_tables`, `describe_schema` |
| **Slack MCP** | `post_message`, `list_channels`, `get_thread`, `search_messages` |
| **Browser MCP** | `navigate`, `click`, `extract_text`, `take_screenshot`, `fill_form` |
| **Postgres MCP** | `run_sql`, `list_schemas`, `explain_query` |

The model doesn't know (or care) that GitHub is written in Go and the DB is PostgreSQL — it just calls the tools defined by the MCP schema.

#### Skills — What They Are

A skill is a **reusable, composable behavioral workflow** — a structured set of instructions, prompts, and decision logic that defines how an agent should tackle a category of task. Skills sit on top of tools; they orchestrate tool use purposefully.

**A skill answers:** "Given this type of task, what is the right sequence of steps, what questions to ask, what format to use, how to handle errors?"

**Skills Examples:**

| Skill | What It Defines |
|---|---|
| **Email generator** | Ask for context → draft in appropriate tone → offer subject line variants → ask for revisions |
| **Code reviewer** | Read the diff → check for bugs → check for style → check for security → produce structured report |
| **PR description writer** | Read git diff → identify what changed and why → write summary, test plan, and risk section |
| **Test suite generator** | Read function → identify edge cases → write happy path, error path, boundary tests |
| **Security reviewer** | Scan for OWASP top 10 → check auth → check input validation → check secrets → produce severity-ranked report |
| **SQL query builder** | Understand the business question → infer schema → write query → explain it in plain English |

#### MCP + Skills Together

They are complementary, not competing:

```
User: "Create a Jira ticket for the bug I just described"

Skill: Bug ticket creator
  Step 1: Extract: title, description, severity, affected component
  Step 2: Look up which project this component belongs to
  Step 3: Format ticket per team's template
  Step 4: Create the ticket
  Step 5: Post link to Slack channel

Tools used (via MCP):
  - Jira MCP → searchJiraProjects(), createJiraIssue()
  - Slack MCP → postMessage()
```

The **skill** defines the workflow and decision logic. The **MCP** provides the actual tools to execute it.

#### Interview One-Liner
> "MCP is a protocol — it's the standard way external systems expose tools and data to a model, like a universal adapter. Skills are behavioral workflows — reusable sequences of steps that define how to accomplish a class of task, potentially using many MCP-connected tools. MCP is the plumbing; skills are the plumber's method."

---

### 11.4 Skill Use Cases Beyond Email Generation

Skills shine wherever a task has a **consistent structure**, **repeatable steps**, and **domain-specific quality criteria** — but the inputs vary each time.

#### Development and Engineering Skills

| Skill | What It Does | Key Steps |
|---|---|---|
| **Code reviewer** | Reviews a PR or code snippet for bugs, style, security | Read code → identify issues by category → rank by severity → suggest fixes |
| **PR description writer** | Generates a structured PR description from a git diff | Read diff → extract intent → write summary, test plan, risk section, screenshots checklist |
| **Test suite generator** | Writes comprehensive tests for a function or module | Analyze signature + docstring → enumerate edge cases → write pytest/jest suite |
| **Refactor advisor** | Identifies code smells and suggests targeted refactors | Parse code → detect patterns (long method, duplicate logic) → propose minimal refactors |
| **Commit message writer** | Writes a conventional commit message from staged changes | Read diff → identify change type (feat/fix/refactor) → write concise imperative message |
| **Dependency auditor** | Reviews package files for vulnerabilities and outdated deps | Read requirements.txt/package.json → cross-reference CVE DB → report by severity |
| **API spec generator** | Generates OpenAPI/Swagger spec from code or description | Read endpoints → infer request/response schemas → produce YAML spec |
| **Database migration writer** | Writes a safe migration script from a schema change description | Understand before/after schema → generate up + down migrations → add safety checks |

#### Documentation and Communication Skills

| Skill | What It Does |
|---|---|
| **README generator** | Reads codebase structure and generates a professional README |
| **Architecture diagram describer** | Reads infrastructure config and writes a textual architecture overview |
| **Meeting notes formatter** | Converts raw transcript or bullet points into structured action items |
| **Incident postmortem writer** | Structures a blameless postmortem from an incident timeline |
| **User story writer** | Converts feature requirements into Agile user stories with acceptance criteria |
| **Release notes generator** | Summarizes a sprint's merged PRs into customer-facing release notes |
| **Onboarding guide writer** | Reads a repo and generates a new-joiner getting-started guide |

#### Analysis and Research Skills

| Skill | What It Does |
|---|---|
| **Log analyzer** | Parses error logs, identifies patterns, clusters errors, suggests root causes |
| **SQL query builder** | Translates business questions into correct, optimized SQL |
| **Data profiler** | Summarizes a CSV/DataFrame: nulls, distributions, outliers, suggested cleanups |
| **Contract summarizer** | Extracts key clauses, obligations, deadlines, and risks from a legal document |
| **Competitive analysis builder** | Scrapes and compares competitor features, pricing, and positioning |
| **Resume screener** | Scores a resume against a job description, flags gaps, suggests interview questions |
| **Paper summarizer** | Reads an academic paper and produces: problem, method, results, limitations, relevance |

#### Security Skills

| Skill | What It Does |
|---|---|
| **Security reviewer** | Scans code for OWASP Top 10, insecure defaults, hardcoded secrets, missing auth |
| **Threat modeler** | Given a system description, generates a STRIDE threat model with mitigations |
| **Pentest report writer** | Converts raw findings into a structured pentest report with severity and remediation |
| **Secrets scanner** | Reviews a codebase or diff for accidentally committed credentials or API keys |

#### What Makes a Good Skill (Design Criteria)

A task is a good candidate for a skill when:

1. **Repeated frequently** — worth the investment in structure
2. **Has clear quality criteria** — you know what "good" looks like
3. **Consistent phases** — input gathering → analysis → output → review always follow the same arc
4. **Benefits from domain prompting** — the skill can encode expert knowledge about format, tone, common mistakes
5. **Composable** — the skill can call other skills or MCP tools as sub-steps

A task is a poor candidate when:
- It's one-off and highly unique
- The user needs to guide every decision (better as a conversation)
- The output format varies wildly per use case

---

*Last updated: May 2026*
