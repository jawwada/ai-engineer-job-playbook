# Multi-Agent Frameworks — A Complete Guide

> Current as of May 2026. The agent framework landscape has consolidated dramatically over the past year. This document covers what these frameworks are, why they exist, how they're built and used, where they differ, and how to pick one.

---

## Table of Contents

1. [What a Multi-Agent Framework Actually Is](#1-what-a-multi-agent-framework-actually-is)
2. [Why Frameworks Exist — The Problem They Solve](#2-why-frameworks-exist--the-problem-they-solve)
3. [Core Abstractions Every Framework Has](#3-core-abstractions-every-framework-has)
4. [Coordination Patterns — The Building Blocks](#4-coordination-patterns--the-building-blocks)
5. [The 2026 Landscape Map](#5-the-2026-landscape-map)
6. [Deep Dives by Framework](#6-deep-dives-by-framework)
   - 6.1 [LangGraph](#61-langgraph)
   - 6.2 [CrewAI](#62-crewai)
   - 6.3 [Microsoft Agent Framework (AutoGen + Semantic Kernel)](#63-microsoft-agent-framework-autogen--semantic-kernel)
   - 6.4 [Claude Agent SDK](#64-claude-agent-sdk)
   - 6.5 [OpenAI Agents SDK](#65-openai-agents-sdk)
   - 6.6 [Google ADK](#66-google-adk)
   - 6.7 [Pydantic AI](#67-pydantic-ai)
   - 6.8 [Smolagents](#68-smolagents)
   - 6.9 [AWS Strands Agents](#69-aws-strands-agents)
   - 6.10 [LlamaIndex Agents](#610-llamaindex-agents)
   - 6.11 [Mastra, Agno, Letta, Vercel AI SDK](#611-mastra-agno-letta-vercel-ai-sdk)
7. [The Protocol Layer — MCP, A2A, ACP](#7-the-protocol-layer--mcp-a2a-acp)
8. [Comparison Matrix](#8-comparison-matrix)
9. [Decision Guide — How to Pick One](#9-decision-guide--how-to-pick-one)
10. [Production Concerns Across All Frameworks](#10-production-concerns-across-all-frameworks)
11. [Anti-Patterns to Avoid](#11-anti-patterns-to-avoid)
12. [Where the Field Is Going](#12-where-the-field-is-going)

---

## 1. What a Multi-Agent Framework Actually Is

A **multi-agent framework** is a software library that gives you abstractions for building systems where one or more LLM-powered "agents" coordinate to accomplish tasks that single prompts can't.

An **agent**, in this context, is a loop:

```
observe → think → act → observe → think → act → ...
```

Concretely: the LLM receives a state, decides what to do (call a tool, hand off to another agent, return an answer), the action executes, the result is fed back, and the loop continues until termination.

A **multi-agent system** layers structure on top: instead of one giant agent, you have specialized agents (planner, retriever, validator, writer) coordinated by some orchestration logic.

Frameworks provide:
1. **Agent abstractions** — a way to define an agent's role, tools, model, prompt, and behavior
2. **Coordination primitives** — supervisor patterns, sequential pipelines, handoffs, debates, swarms
3. **State management** — how shared context flows between agents and across steps
4. **Tool use** — connecting agents to external systems (APIs, databases, filesystems)
5. **Memory** — short-term (conversation) and long-term (across sessions)
6. **Persistence and recovery** — what happens when step 7 of 12 fails
7. **Observability** — tracing, logging, debugging the agent's decisions
8. **Production plumbing** — streaming, async, retry, timeouts, cost caps

Without a framework you build all of this yourself with raw API calls. Frameworks save weeks of engineering on plumbing so you can focus on the logic.

---

## 2. Why Frameworks Exist — The Problem They Solve

To understand the value, look at what writing an agent from raw API calls looks like:

```python
# Raw API approach — what you write by hand
import anthropic

client = anthropic.Anthropic()
tools = [{"name": "search", "input_schema": {...}, "description": "..."}]
messages = [{"role": "user", "content": "Find me data on X and summarize it."}]

while True:
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=tools,
        messages=messages,
    )

    if response.stop_reason == "end_turn":
        break

    if response.stop_reason == "tool_use":
        tool_calls = [c for c in response.content if c.type == "tool_use"]
        tool_results = []
        for call in tool_calls:
            try:
                result = your_tool_executor(call.name, call.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": str(result),
                })
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": f"Error: {e}",
                    "is_error": True,
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

That's one agent, one tool loop, with bare-minimum error handling. Now add:
- Retries with exponential backoff when the API rate-limits
- Token budget tracking so a buggy retry doesn't blow your bill
- A second agent that validates the first's output
- A supervisor that decides which sub-agent to call
- State persistence so a crash doesn't lose 8 minutes of work
- Streaming to the UI for perceived latency
- Tracing every LLM call with correlation IDs
- Configurable timeouts per step
- Human-in-the-loop pauses for sensitive actions

You've now written ~2000 lines of plumbing. Every team writes a slightly different version. **Frameworks exist to make this stop being everyone's problem.**

But — and this is the contrarian point worth holding onto — frameworks also cost something:
- Abstraction overhead (harder to debug what's actually happening)
- Token overhead (frameworks tend to wrap prompts with structure)
- Learning curve (each framework has its own mental model)
- Lock-in (migrating between frameworks is painful)
- The Stanford 2026 paper (Tran & Kiela) showed that under matched compute budgets, a strong single agent often beats multi-agent — meaning the framework's coordination cost can exceed its coordination benefit

Use frameworks when complexity warrants them, not by default.

---

## 3. Core Abstractions Every Framework Has

Despite naming differences, every framework has these primitives. Knowing them lets you map from one framework to another quickly.

### 3.1 Agent

An **agent** is the unit of LLM-powered work. Every framework defines an agent as some combination of:
- **Model**: which LLM (and which version)
- **System prompt** / role / persona
- **Tools**: functions the agent can call
- **Input/output schemas**: structured I/O contracts
- **Memory** (optional): how much history it retains

### 3.2 Tool

A **tool** is a function with a schema (JSON Schema for parameters, a name, a description) that the LLM can choose to invoke. The framework handles:
- Showing the schema to the model
- Parsing the model's tool call
- Executing the function
- Returning the result back to the model

Tools are how agents touch reality — APIs, databases, filesystems, web pages, other agents.

### 3.3 State

**State** is the data that flows through the system between steps. Every framework has a position on state:
- **LangGraph**: an explicit `State` TypedDict, mutated by nodes
- **CrewAI**: implicit, shared via task outputs
- **AutoGen / Microsoft Agent Framework**: conversation history is state
- **Claude Agent SDK**: file system + conversation
- **OpenAI Agents SDK**: a context object you pass through

State management is the single biggest source of bugs in production agent systems. Frameworks that make state explicit (LangGraph) are easier to debug; frameworks that hide it (CrewAI) are easier to start with.

### 3.4 Coordination / Orchestration

How agents pass work to each other. Patterns covered in §4.

### 3.5 Memory

Two flavors:
- **Short-term memory** = conversation history. Capped by context window.
- **Long-term memory** = persisted across sessions, usually backed by a vector store.

Some frameworks (Letta, Claude Agent SDK with CLAUDE.md files) treat memory as a first-class citizen. Most treat it as something you bolt on.

### 3.6 Persistence / Checkpointing

For long-running workflows, the state must survive crashes. LangGraph has the most mature support (Postgres, SQLite, in-memory checkpointers); the Claude Agent SDK uses files; most others have weaker stories here.

### 3.7 Observability

Every framework now ships some form of tracing — what the agent did, when, with what cost. LangSmith (LangGraph) and OpenAI's built-in tracing are the most mature. We'll cover this in §10.

---

## 4. Coordination Patterns — The Building Blocks

These are the recurring multi-agent topologies. Every framework supports most of them; they differ in idiom and ergonomics.

### 4.1 Single Agent with Tools (the simplest baseline)

One agent, many tools. The agent loops: call tool, observe result, decide next action. This is the **most underrated pattern** — it's often what you actually need, even when management has asked for "a multi-agent system." Start here.

### 4.2 Sequential Pipeline

```
Agent A → Agent B → Agent C → Output
```

Each agent does one step. Linear, predictable, easy to reason about. **Risk**: early-stage errors cascade with no architectural correction path.

### 4.3 Supervisor / Orchestrator–Specialist

```
       Supervisor
       ↓   ↓   ↓
     A    B    C   (specialists)
```

A planner agent decomposes the task and dispatches to specialists; the supervisor integrates results. This is the "default" multi-agent pattern. **Risk**: supervisor is a single point of failure; downstream verification often can't catch its mistakes.

### 4.4 Handoff / Triage

```
Triage Agent → (one of) Specialist A | B | C
```

An entry agent classifies the request and hands off to one downstream agent. Common for customer support. OpenAI Agents SDK's `handoffs` primitive is built around this.

### 4.5 Parallel Fan-Out / Fan-In

```
         ↓
    ┌────┼────┐
    A    B    C    (parallel)
    └────┼────┘
         ↓
      Aggregator
```

Independent sub-tasks executed in parallel, results aggregated. The right pattern when sub-tasks don't depend on each other. **Anthropic's published research found this can outperform single-agent by up to 90%** when sub-tasks are genuinely parallel and a lead planner coordinates them.

### 4.6 Peer-Critique / Debate

```
A ⇄ B ⇄ C → consensus
```

Agents critique each other over multiple rounds, converging on a final answer. Produces high-quality outputs through deliberation, but costs 20+ LLM calls per interaction (AutoGen's pattern). **Risk**: alignment pressure suppresses minority dissent — the "groupthink" failure mode.

### 4.7 Reflexive / Self-Correcting Loop

```
Agent generates → Evaluator critiques → Agent regenerates → ...
```

One agent generates, another evaluates, the first retries with feedback. Highest field-level accuracy per the Kulkarni 2026 SEC-filings benchmark (F1 0.943) but at 2.3× cost of sequential baselines.

### 4.8 Hierarchical Tree

```
        Root
       /    \
     Mid    Mid
    /  \    /  \
   A    B  C    D
```

Multi-level delegation. Google ADK is built around this. Useful when sub-tasks themselves decompose further.

### 4.9 Swarm

```
A ↔ B ↔ C ↔ D
```

Agents talk peer-to-peer with no central authority. OpenAI's original Swarm framework explored this; Microsoft's Agent Framework supports it. **Reality check**: rarely the right answer for production. Too much non-determinism, too hard to debug.

### 4.10 Three-Agent Harness (Planner → Generator → Evaluator)

Anthropic's canonical pattern for long-running tasks: a Planner sets structure and goals, a Generator executes, an Evaluator runs 5–15 critique-and-refine cycles — sometimes over four hours — on complex creative or full-stack tasks. The agents hand off through structured artifacts rather than shared context, which keeps each agent's window focused.

---

## 5. The 2026 Landscape Map

The space has consolidated into roughly twelve frameworks that matter, splitting into three categories:

### 5.1 Provider-Native SDKs

Optimized for one model family, deepest integration with that vendor's features.

| Framework | Vendor | Notes |
|---|---|---|
| **Claude Agent SDK** | Anthropic | Formerly "Claude Code SDK", renamed early 2026. Same loop that powers Claude Code. |
| **OpenAI Agents SDK** | OpenAI | Replaced the experimental Swarm in 2025. Production-grade. |
| **Google ADK** | Google | Python, TypeScript, Java, Go. A2A protocol native. |

### 5.2 Independent Frameworks

Model-agnostic, work across providers.

| Framework | Style | Strength |
|---|---|---|
| **LangGraph** | Graph state machine | Production-grade, complex stateful workflows |
| **CrewAI** | Role-based | Fast prototyping, intuitive abstractions |
| **AutoGen / AG2** | Conversational | Multi-agent debate, research patterns |
| **Pydantic AI** | Type-first | Testable, validated, production-friendly |
| **Smolagents** | Code-execution | Local LLM friendly, minimal abstraction |
| **LlamaIndex Agents** | Retrieval-first | Strong RAG integration |

### 5.3 Enterprise / Platform Frameworks

Bundled with cloud platform tooling.

| Framework | Platform | Notes |
|---|---|---|
| **Microsoft Agent Framework** | Azure | Merger of AutoGen + Semantic Kernel into one unified Agent Framework |
| **AWS Strands Agents** | AWS | Declarative collaboration patterns ("swarms", "agents-as-tools", "workflow graphs") |
| **Vercel AI SDK** | Vercel | TS-first; added agent abstractions in v6 |

### 5.4 Specialized Niche Frameworks

| Framework | Niche |
|---|---|
| **Mastra** | TypeScript-native, modern alternative to LangChain |
| **Letta** (formerly MemGPT) | Long-term memory as the primary feature |
| **Agno (formerly PhiData)** | Lightweight, fast |
| **Atomic Agents** | Minimalist, schema-driven |

---

## 6. Deep Dives by Framework

### 6.1 LangGraph

**One-line summary**: A graph-based state machine for agents. The most production-mature open-source framework in 2026.

#### Mental model
You define a **state graph**:
- **Nodes** = functions that read and modify state (often LLM calls or tool executions)
- **Edges** = transitions between nodes, possibly conditional
- **State** = a TypedDict (or Pydantic model) that flows through the graph

This maps cleanly onto production requirements like audit trails and rollback points.

#### Code example

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    query: str
    plan: list[str]
    chunks: list[dict]
    draft: str
    final: str
    validation_attempts: int

def planner_node(state: State) -> State:
    state["plan"] = call_planner_llm(state["query"])
    return state

def retriever_node(state: State) -> State:
    state["chunks"] = retrieve(state["plan"])
    return state

def drafter_node(state: State) -> State:
    state["draft"] = call_drafter_llm(state["query"], state["chunks"])
    return state

def validator_node(state: State) -> State:
    if is_valid(state["draft"], state["chunks"]):
        state["final"] = state["draft"]
    state["validation_attempts"] = state.get("validation_attempts", 0) + 1
    return state

def route_after_validation(state: State) -> str:
    if state.get("final"):
        return END
    if state["validation_attempts"] >= 3:
        return END
    return "drafter"  # retry

graph = StateGraph(State)
graph.add_node("planner", planner_node)
graph.add_node("retriever", retriever_node)
graph.add_node("drafter", drafter_node)
graph.add_node("validator", validator_node)

graph.set_entry_point("planner")
graph.add_edge("planner", "retriever")
graph.add_edge("retriever", "drafter")
graph.add_edge("drafter", "validator")
graph.add_conditional_edges("validator", route_after_validation)

app = graph.compile(checkpointer=PostgresSaver(...))  # persistence
```

#### Strengths
- **Explicit state**: easiest framework to debug; you can see exactly what every node read/wrote
- **Persistent checkpointing**: crash recovery, time-travel debugging — the only framework where "what happens when step 7 fails" has a first-class answer
- **Conditional edges, cycles, branching**: handles the actual complexity of production workflows
- **Strong observability**: LangSmith integration provides tracing, evaluation, and prompt management
- **Streaming**: per-node token streaming
- **LangGraph surpassed CrewAI in GitHub stars in early 2026**, driven by enterprise adoption

#### Weaknesses
- **Verbose**: a simple ReAct agent takes ~120 lines in LangGraph vs ~40 in Smolagents
- **Conceptual overhead**: you have to learn graph theory mental model
- **LangChain baggage**: inherits some abstraction creep from LangChain
- **Lock-in to LangSmith** if you want best-in-class observability

#### When to pick it
- Production agents with branching, retries, or human-in-the-loop
- Workflows that must survive crashes
- Regulated environments needing audit trails
- Teams already on LangChain

### 6.2 CrewAI

**One-line summary**: Define agents by role and goal in natural language; the framework infers coordination.

#### Mental model
You define a **crew**:
- **Agents** with roles ("Researcher"), goals, and backstory
- **Tasks** with descriptions and assigned agents
- **Process**: sequential or hierarchical

The framework handles passing outputs between agents based on the role descriptions.

#### Code example

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="Senior Research Analyst",
    goal="Find and synthesize information about {topic}",
    backstory="You are an experienced analyst with attention to detail.",
    tools=[search_tool, web_scrape_tool],
)

writer = Agent(
    role="Technical Writer",
    goal="Write a clear, well-structured report on {topic}",
    backstory="You produce reports that executives actually read.",
)

research_task = Task(
    description="Research {topic} thoroughly. Output a structured summary.",
    agent=researcher,
    expected_output="A 500-word summary with key facts and sources.",
)

writing_task = Task(
    description="Write a 1000-word executive report based on the research.",
    agent=writer,
    expected_output="A polished report with sections and conclusions.",
    context=[research_task],
)

crew = Crew(agents=[researcher, writer], tasks=[research_task, writing_task])
result = crew.kickoff(inputs={"topic": "humanoid robotics market"})
```

#### Strengths
- **Fastest path to a prototype**: role-based abstraction is intuitive
- **Minimal boilerplate**: you describe what you want, not how
- **Good for content workflows**: research → writing → editing flows naturally
- **MCP support**: connects to MCP servers for tool integration
- **Growing ecosystem**: large community, decent docs

#### Weaknesses
- **Opacity**: becomes a black box in a 5-agent pipeline when something fails
- **Token overhead**: role-playing abstraction adds tokens (backstories + role descriptions in every prompt)
- **Limited checkpointing**: weak crash recovery
- **Less control**: harder to fine-tune execution flow
- **Streaming support is limited**

#### When to pick it
- Prototypes and demos
- Content / research workflows where natural-language role descriptions fit
- Teams that prioritize speed-to-first-version over production robustness
- Refactor to LangGraph or similar when the prototype gets serious

### 6.3 Microsoft Agent Framework (AutoGen + Semantic Kernel)

**One-line summary**: Microsoft merged AutoGen and Semantic Kernel into a unified Agent Framework in 2025–2026. Conversational multi-agent, with .NET-first roots.

#### Mental model
Agents have **conversations**. You define a **group chat** with multiple agents, possibly with a "selector" that decides who speaks next.

#### Code example (AutoGen / AG2 style)

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

planner = AssistantAgent(
    name="Planner",
    system_message="You break down complex tasks into subtasks.",
    llm_config={"model": "gpt-4o"},
)

executor = AssistantAgent(
    name="Executor",
    system_message="You execute subtasks with available tools.",
    llm_config={"model": "gpt-4o"},
)

critic = AssistantAgent(
    name="Critic",
    system_message="You evaluate outputs and flag issues.",
    llm_config={"model": "gpt-4o"},
)

user = UserProxyAgent(name="User", code_execution_config={"work_dir": "tmp"})

groupchat = GroupChat(agents=[user, planner, executor, critic], messages=[], max_round=12)
manager = GroupChatManager(groupchat=groupchat)

user.initiate_chat(manager, message="Analyze this CSV and produce insights.")
```

#### Strengths
- **Conversational pattern is intuitive** for debate, code review, planning scenarios
- **Microsoft ecosystem integration**: Azure, .NET, Power Platform
- **Strong academic/research adoption**: lots of papers cite AutoGen
- **Code execution**: built-in safe code execution sandboxes

#### Weaknesses
- **Expensive**: every agent turn is a full LLM call with accumulated history. A 4-agent debate with 5 rounds is 20+ LLM calls minimum, making it expensive for high-volume, real-time use cases
- **Limited streaming**: conversation-based, not streaming-first
- **Merger churn**: the AutoGen → AG2 → Agent Framework path has caused some API instability
- **Overkill for simple flows**: the group-chat abstraction is heavyweight

#### When to pick it
- Offline, quality-sensitive workflows where thoroughness matters more than speed
- Research environments doing multi-agent experiments
- .NET / Azure-native shops
- Tasks that genuinely benefit from deliberation (e.g. complex code review, research synthesis)

### 6.4 Claude Agent SDK

**One-line summary**: Anthropic's first-party agent SDK. Built around the philosophy "give your agent a computer." The same loop that powers Claude Code.

#### Mental model
The agent has a computer — shell, filesystem, web — and uses it like a human would. Built-in tools (Bash, Read, Write, Edit, Glob, Search, Subagents, MCP servers) are first-class, so you skip the tool-wiring boilerplate.

The core loop is **gather context → take action → verify results → repeat**, exposed transparently rather than hidden behind abstraction.

#### Code example

```python
from claude_agent_sdk import query, ClaudeAgentOptions
import asyncio

async def main():
    async for message in query(
        prompt="Find and fix the bug in src/auth.py",
        options=ClaudeAgentOptions(
            allowed_tools=["bash", "read", "edit", "search"],
            max_budget_usd=2.50,  # cost cap
            permission_mode="auto",  # or "always_prompt"
        ),
    ):
        print(message)

asyncio.run(main())
```

For multi-agent, Claude Agent SDK supports a **three-agent harness** (Planner → Generator → Evaluator) shipping to public beta in May 2026, with subagents that can be spawned in parallel.

#### Strengths
- **Built-in tools** = ship working agents fast. No need to wire bash, file I/O, search yourself
- **Best path for Claude Opus 4.7 / Sonnet 4.6**: every model feature available immediately
- **MCP integration is the deepest of any framework** — connects to 18,000+ community MCP servers
- **Context compaction** for long-running tasks: automatic management
- **Cost controls**: `max_budget_usd` parameter caps spend per session
- **Subagent pattern** for parallel sub-tasks
- **Battle-tested**: same loop powers Claude Code
- **Multi-cloud**: supports AWS Bedrock, Google Vertex AI, Azure AI Foundry
- **Managed Agents**: Anthropic also offers a hosted version (launched April 2026) that runs agents and sandboxes for you at $0.08/session-hour

#### Weaknesses
- **Anthropic-first**: works with other providers, but the design is Claude-centric. Lock-in risk if you want to switch models
- **Higher token pricing** than some alternatives (Anthropic's premium model pricing)
- **File-based memory** has its own failure modes (data corruption, access control, race conditions if not managed carefully)
- **Production infrastructure** (sandboxing, state, permissions) is left to you unless you use Managed Agents
- **Testing utilities are thin**: you mock the client directly, brittle tests
- **Newer than LangGraph** as a general-purpose framework

#### When to pick it
- Anthropic-first stacks
- Coding agents, dev tools, OS-level automation
- When you want the agent to actually use a computer (shell, files, web)
- When MCP integration is central
- When you want to skip the tool-wiring boilerplate

### 6.5 OpenAI Agents SDK

**One-line summary**: OpenAI's production-grade replacement for the experimental Swarm. Built around handoffs.

#### Mental model
**Handoffs**: an agent decides to pass control to another agent. The receiving agent gets the full context and takes over. Clean for triage → specialist flows.

#### Code example

```python
from agents import Agent, Runner

triage = Agent(
    name="Triage",
    instructions="Determine if the user needs billing, technical, or sales support. Hand off to the right specialist.",
    handoffs=[billing_agent, tech_agent, sales_agent],
)

billing_agent = Agent(
    name="Billing",
    instructions="Help with billing questions. You have access to the billing API.",
    tools=[get_invoice, refund],
)

tech_agent = Agent(
    name="Technical Support",
    instructions="Solve technical issues. You can search the docs.",
    tools=[search_docs, create_ticket],
)

result = Runner.run_sync(triage, input="My payment was charged twice")
print(result.final_output)
```

#### Strengths
- **Cleanest API** in the field, per multiple 2026 reviews
- **Handoff pattern** maps directly to triage → specialist → escalation flows
- **Built-in guardrails**: input/output validation that catches bad inputs before they reach specialist agents
- **Full streaming support**
- **Built-in tracing**: visualize agent runs in the OpenAI dashboard
- **Strong voice integration**: designed for voice-first products

#### Weaknesses
- **OpenAI-first**: works with other providers but you lose features
- **Less control** than LangGraph: handoff abstraction prioritizes simplicity, limits fine-grained control
- **No built-in checkpointing** for long-running workflows
- **Newer**: smaller community than LangGraph

#### When to pick it
- OpenAI-first stacks
- Customer support, triage, voice-first products
- Teams that want clean abstractions and tracing out of the box
- Linear or branching handoff flows (not cyclic / complex state machines)

### 6.6 Google ADK (Agent Development Kit)

**One-line summary**: Google's multi-agent framework, four languages (Python, TS, Java, Go), built around hierarchical agent trees with A2A protocol native.

#### Mental model
**Hierarchical tree**: a root agent delegates to sub-agents, which can have their own sub-agents. Each agent has its own tools and context. A2A protocol lets agents from different frameworks discover and invoke each other through standardized task interface.

#### Code example

```python
from google.adk.agents import LlmAgent

researcher = LlmAgent(
    name="researcher",
    model="gemini-2.0-pro",
    instruction="Research the topic thoroughly.",
    tools=[google_search, web_fetch],
)

writer = LlmAgent(
    name="writer",
    model="gemini-2.0-pro",
    instruction="Produce a polished report.",
)

orchestrator = LlmAgent(
    name="orchestrator",
    model="gemini-2.0-pro",
    instruction="Coordinate research and writing.",
    sub_agents=[researcher, writer],
)
```

ADK also supports non-Google models via LiteLLM or direct integration — including Claude:

```python
from google.adk.agents import LlmAgent
from google.adk.models import Claude
from anthropic.client import AnthropicOkHttpClient

claude_model = Claude("claude-sonnet-4-6", AnthropicOkHttpClient.builder().apiKey("...").build())
agent = LlmAgent.builder().name("claude_agent").model(claude_model).instruction("...").build()
```

#### Strengths
- **A2A protocol native** — cross-framework agent interoperability
- **Native multimodal**: text + audio + video + image in the same agent loop
- **Four languages** — only major framework with Java and Go SDKs
- **Vertex AI Agent Engine** for managed deployment
- **Hierarchical decomposition** scales to complex task trees

#### Weaknesses
- **Newer / smaller community**
- **Most natural on Google Cloud**; less polished outside that environment
- **Tool-call cost efficiency** is weaker than competitors
- **Early-stage** compared to LangGraph

#### When to pick it
- Google Cloud / Vertex AI shops
- Multi-language teams (Python + Java/Go on the same project)
- Multimodal agent workloads
- Cross-vendor interoperability via A2A is a hard requirement

### 6.7 Pydantic AI

**One-line summary**: Type-safe agents. From the Pydantic team. If you're a Pydantic shop and care about testability, this is the natural choice.

#### Mental model
Your agent's inputs, outputs, and tool parameters are all Pydantic models. You get validation, type checking, and serialization built in. Multiple providers (Anthropic, OpenAI, Gemini, Groq, Mistral) supported.

#### Code example

```python
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

class CustomerInfo(BaseModel):
    name: str
    tier: str

class SupportResponse(BaseModel):
    answer: str
    escalate: bool
    confidence: float

agent = Agent(
    "anthropic:claude-opus-4-7",
    deps_type=CustomerInfo,
    output_type=SupportResponse,
    system_prompt="You are a support agent.",
)

@agent.tool
async def lookup_order(ctx: RunContext[CustomerInfo], order_id: str) -> dict:
    return await db.get_order(ctx.deps.name, order_id)

result = await agent.run(
    "Where is order 12345?",
    deps=CustomerInfo(name="Jane", tier="premium"),
)
print(result.output)  # validated SupportResponse instance
```

#### Strengths
- **Type safety as a first-class citizen**: agents have proper input/output contracts
- **TestModel and FunctionModel**: built-in testing utilities that run in milliseconds without API calls. This means you can write unit tests that cover edge cases hard to trigger with real API calls, run in CI without API keys
- **Dependency injection** via RunContext: clean way to pass DB connections, API clients, user context
- **Multi-provider**: not locked to one model vendor
- **Streaming validation**: validate fields as they stream in
- **Clean Python ergonomics**: feels like FastAPI

#### Weaknesses
- **Less feature-rich** than LangGraph or CrewAI for complex multi-agent orchestration
- **Smaller community** than the giants
- **Pair with LangGraph or CrewAI** if you also need complex orchestration

#### When to pick it
- Production systems that need testability above all
- Type-safe Python shops
- Single-agent or simple multi-agent flows
- When you want low overhead and high control

### 6.8 Smolagents

**One-line summary**: HuggingFace's minimalist framework. Agent writes and executes Python code as its primary action mechanism rather than calling predefined tool functions.

#### Mental model
**Code-as-action**: instead of the model emitting JSON tool calls, it writes actual Python code which the framework executes. Naturally handles composition (the model can chain operations in code) and fits HF's local-model ecosystem.

#### Code example

```python
from smolagents import CodeAgent, HfApiModel, tool

@tool
def search_web(query: str) -> str:
    """Search the web."""
    return your_search(query)

@tool
def fetch_url(url: str) -> str:
    """Fetch a URL."""
    return requests.get(url).text

agent = CodeAgent(
    tools=[search_web, fetch_url],
    model=HfApiModel("meta-llama/Llama-3.3-70B-Instruct"),
)
result = agent.run("Find the population of Tokyo and convert it to thousands.")
```

The model writes Python like `pop = int(search_web("Tokyo population").strip()); print(pop // 1000)` rather than a tool-call schema.

#### Strengths
- **Minimal abstraction**: a simple ReAct agent in 40 lines
- **Strong local LLM support**: built by HuggingFace for their own model ecosystem
- **Code-as-action**: naturally handles composition and multi-step computation
- **No JSON tool-call boilerplate**
- **Steepest relative growth** in 2026 — fills a gap others don't

#### Weaknesses
- **Sandboxing burden**: executing model-generated code requires careful sandboxing for production
- **Less production tooling**: weaker observability, persistence, multi-agent patterns
- **Newer**: still maturing

#### When to pick it
- Local LLM / HuggingFace workflows
- When code-as-action is a natural fit (data analysis, calculations, scripting)
- Prototypes and research
- When you want minimal framework overhead

### 6.9 AWS Strands Agents

**One-line summary**: AWS's multi-agent collaboration framework. Declarative specifications of agent workflows, integrates with Amazon Nova and Bedrock.

#### Mental model
Declarative collaboration patterns: "swarms," "agents-as-tools," "workflow graphs." Strands exposes these as configurable choices in a YAML/JSON-style specification.

#### Strengths
- **Native AWS integration**: Bedrock, Lambda, ECS, IAM
- **Declarative**: workflows as data, not code — easier to version, audit, modify
- **Production-grade**: built for AWS-scale workloads
- **Cross-vendor model support** via Bedrock

#### Weaknesses
- **AWS lock-in**: best within AWS, less natural outside
- **Newer**: smaller community than LangGraph
- **Declarative tradeoff**: less flexibility than imperative code

#### When to pick it
- AWS-native shops
- Enterprise teams that want declarative workflow definitions
- Workloads heavily integrated with other AWS services

### 6.10 LlamaIndex Agents

**One-line summary**: Retrieval-first framework that grew into agents. Strongest when RAG is the heart of the system.

#### Mental model
**Workflows**: event-driven steps connected by typed messages. Agents are workflows specialized for LLM tool use.

#### Strengths
- **Deepest RAG integration** of any framework
- **Workflow abstraction** is general and clean
- **Mature data ingestion**: parsers for hundreds of formats
- **LlamaParse**: world-class PDF/document parsing

#### Weaknesses
- **Less focused on pure agents** — agents are one workload among many
- **Smaller agent community** than LangGraph or CrewAI
- **Newer agent APIs** still maturing

#### When to pick it
- RAG-heavy systems where retrieval is the primary work
- Already using LlamaIndex for ingestion/retrieval
- Document-centric workloads

### 6.11 Mastra, Agno, Letta, Vercel AI SDK

| Framework | Niche | One-line summary |
|---|---|---|
| **Mastra** | TypeScript-native agents | The modern TS alternative to LangChain — agents, workflows, RAG, memory in one package |
| **Agno** (formerly PhiData) | Lightweight, fast | Minimal-overhead agent framework, very low latency |
| **Letta** (formerly MemGPT) | Long-term memory | The memory-first framework. If your agent needs to remember users across months, this is the niche |
| **Vercel AI SDK** | TS / Next.js | 20M+ monthly downloads. v6 added native agent abstractions. Best for TS frontend developers building agent UIs |

---

## 7. The Protocol Layer — MCP, A2A, ACP

Beneath the framework layer, three protocols define how agents connect to tools and to each other. By 2026 these have largely consolidated.

### 7.1 MCP (Model Context Protocol)

**Purpose**: Agent-to-tool standardization.

Launched by Anthropic in November 2024, MCP provides a universal, model-agnostic interface for AI systems to access and interact with diverse resources. It's a JSON-RPC client–server interface for secure context ingestion and structured tool invocation.

By 2026, MCP is the de facto standard for agent-to-tool connectivity, now governed by the Linux Foundation's Agentic AI Foundation (AAIF) with over 18,000 community-indexed servers and tens of millions of monthly SDK downloads.

**Why it matters**: any compliant MCP client can reach any compliant MCP server without custom adapters. You write one Slack integration and every MCP-aware agent can use it.

### 7.2 A2A (Agent-to-Agent Protocol)

**Purpose**: Agent-to-agent coordination, cross-framework.

Launched by Google in April 2025, A2A enables peer-to-peer agent interactions using capability-based representations known as **Agent Cards** that describe what an agent can do and how it can be securely invoked. It supports asynchronous, event-driven communication through HTTP and Server-Sent Events.

By early 2026 it had reached v1.0 with 50+ enterprise partners (Salesforce, Accenture, SAP, Deloitte). An ADK agent can discover and invoke an agent built with LangGraph or CrewAI through A2A's standardized task interface — meaning multi-vendor agent ecosystems are practical, not theoretical.

### 7.3 ACP (Agent Communication Protocol)

**Purpose**: Originally IBM Research's REST-native agent-to-agent protocol. In September 2025, IBM announced that ACP would officially merge with A2A under the Linux Foundation, recognizing that two competing standards created unnecessary fragmentation. So ACP is effectively folded into A2A now.

### 7.4 The Production Pattern

The two-layer stack — MCP for vertical tool integration, A2A for horizontal agent coordination — has become the architectural default for enterprise agent deployments. In practice:

- **An agent uses MCP** to query your CRM
- **Then uses A2A** to delegate follow-up tasks to specialized agents on other teams or systems

**Practical takeaway**: regardless of which framework you pick, ensure it speaks MCP for tools and (ideally) A2A for agent-to-agent. The frameworks that don't will be increasingly isolated.

---

## 8. Comparison Matrix

| Framework | Style | Production Readiness | State Mgmt | Streaming | Checkpointing | Tool Ecosystem | Multi-Provider | Best For |
|---|---|---|---|---|---|---|---|---|
| **LangGraph** | Graph state machine | Highest | Explicit | Per-node tokens | Strong (Postgres/SQLite) | Large (LangChain) | Yes | Complex stateful production |
| **CrewAI** | Role-based | Medium | Implicit | Limited | Limited | Growing | Yes | Rapid prototyping |
| **AutoGen/AG2** | Conversational | Medium | Conversation | Limited | Limited | Medium | Yes | Research, debate patterns |
| **Microsoft Agent Framework** | Unified | High (Azure) | Mixed | Yes | Yes | Microsoft ecosystem | Yes | Enterprise Azure shops |
| **Claude Agent SDK** | Computer-use loop | High | Files + conversation | Native | Via files | MCP-deep | Claude-first | Coding/OS agents |
| **OpenAI Agents SDK** | Handoff | High | Context object | Full | Limited | OpenAI-deep | OpenAI-first | Triage/voice |
| **Google ADK** | Hierarchical | Medium (newest) | Tree-scoped | Vertex | Vertex | A2A-native | Yes (4 languages) | GCP, multimodal |
| **Pydantic AI** | Type-safe | High | Explicit deps | Yes | No | Medium | Yes | Testable production |
| **Smolagents** | Code-execution | Medium | Minimal | Limited | No | HF ecosystem | Yes | Local LLMs, scripting |
| **AWS Strands** | Declarative | High (AWS) | Declarative | Yes | Yes | AWS-deep | Via Bedrock | AWS-native |
| **LlamaIndex** | Workflow | Medium | Event-driven | Yes | Yes | RAG-deep | Yes | RAG-heavy |
| **Mastra** | TS workflows | Medium | Explicit | Yes | Yes | Growing | Yes | TS / Next.js stacks |
| **Letta** | Memory-first | Medium | Long-term memory | Yes | Native | Medium | Yes | Long-running personal agents |

---

## 9. Decision Guide — How to Pick One

The 90% answer is: **start with the simplest thing that could work, and upgrade when complexity warrants.**

### 9.1 Decision Tree

**Step 1 — Do you even need a framework?**
- Single agent, < 5 tools, no complex state → **No framework**. Use raw API calls + a thin loop. ~100 lines, full control, zero abstraction debt.
- Otherwise → continue.

**Step 2 — Which provider's models are you committed to?**
- 100% Claude → **Claude Agent SDK** (deepest integration, built-in tools)
- 100% OpenAI → **OpenAI Agents SDK** (cleanest API, built-in tracing)
- 100% Google / Vertex → **Google ADK** (native A2A, multimodal)
- Multi-provider or unsure → continue.

**Step 3 — What's your primary workload?**
- Coding / OS automation → **Claude Agent SDK**
- Customer support triage → **OpenAI Agents SDK** (handoffs)
- RAG-heavy → **LlamaIndex Agents** or **LangGraph + LlamaIndex**
- Complex stateful workflows with retries, branches, human-in-the-loop → **LangGraph**
- Fast prototype, content/research workflow → **CrewAI**
- Need ironclad testability → **Pydantic AI**
- Local LLMs / HF ecosystem → **Smolagents**
- TS / Next.js frontend stack → **Vercel AI SDK** or **Mastra**

**Step 4 — What's your platform?**
- AWS-native → **AWS Strands** (or LangGraph deployed on ECS)
- Azure-native → **Microsoft Agent Framework**
- GCP-native → **Google ADK**
- No strong cloud preference → **LangGraph**

### 9.2 Common Patterns

| Use case | Recommendation |
|---|---|
| Customer support bot | OpenAI Agents SDK or Claude Agent SDK + MCP |
| Research / report generation | CrewAI for prototype, LangGraph for production |
| Coding agent | Claude Agent SDK |
| Internal knowledge Q&A | LangGraph + LlamaIndex |
| Multi-tenant SaaS agent platform | LangGraph (best persistence) |
| Voice-first product | OpenAI Agents SDK |
| Financial document extraction | LangGraph hierarchical + Pydantic AI for validation |
| Local / on-prem deployment | Smolagents + local model |

### 9.3 The "Refactor Later" Strategy

A pattern that works well:
1. Prototype in **CrewAI** to validate the workflow (1–2 days)
2. Identify the production-critical parts (state, retries, observability)
3. Rewrite the critical paths in **LangGraph** (1–2 weeks)
4. Keep CrewAI for parts where natural-language role definitions still fit

Don't over-commit to the prototype framework.

---

## 10. Production Concerns Across All Frameworks

Frameworks make the happy path easy. Production is where they're tested. The following concerns apply regardless of framework choice.

### 10.1 Observability

You need at minimum:
- **Tracing**: every LLM call, tool call, and agent transition logged with correlation IDs
- **Per-step latency**: p50/p95/p99
- **Token usage per step**: input + output tokens
- **Cost per request**
- **Validation pass rate**: how often did structured output fail?
- **Retry rate**: how often did we have to retry, and at which step?

Tools:
- **LangSmith** (LangGraph) — most mature
- **Langfuse** — open-source, framework-agnostic
- **Braintrust, Galileo, Patronus** — eval-focused
- **OpenAI tracing** (Agents SDK) — built-in
- **AWS X-Ray, Datadog** — general-purpose APM

### 10.2 Cost Engineering

LLM cost is the dominant production expense. Levers:
- **Model routing**: route simple queries to small/cheap models, complex to large
- **Prompt caching**: most providers support this; can cut input cost dramatically
- **Output token caps**: aggressively limit `max_tokens`
- **Embedding cache**: never re-embed the same text
- **Result cache**: exact-match cache on (query, context) → response
- **Budget enforcement**: per-request hard cap to prevent runaway loops

The Kulkarni 2026 financial-document benchmark showed that adding semantic caching, model routing, and adaptive retry recovered 89% of the most expensive architecture's accuracy gains at near-baseline cost. **Engineering on top of the topology matters more than the topology choice itself.**

### 10.3 Testing

Two layers:

**Unit tests** for prompts, tool wrappers, parsers, validators. Run in milliseconds, no API calls. Pydantic AI's `TestModel` is the gold standard here.

**Offline evals** for end-to-end agent behavior. Build a regression set of (input, expected_properties) cases:

```python
evaluations = [
    {"query": "What is our refund policy?", "expected_contains": ["30 days"], "min_citations": 1},
    {"query": "Tell me a joke about the CEO", "expected_refuses": True},
]
```

Run on every PR. Fail the build if pass rate regresses.

### 10.4 Security

The big risks:
- **Prompt injection**: untrusted content (web pages, retrieved docs, user input) contains instructions that subvert the agent's behavior. Defenses: privilege separation (untrusted-content readers have no tools), input filtering, structured outputs, tool least-privilege, sandboxing, human-in-the-loop for sensitive actions.
- **Tool misuse**: agent calls a tool in a way that damages data. Defenses: tool scoping (least IAM permissions), read-only by default, dry-run mode, human approval for writes.
- **Data leakage**: confidential context leaks via LLM API, logs, or vector store. Defenses: PII redaction, provider data-retention controls, log scrubbing, multi-tenant isolation.
- **Cost attacks**: malicious user triggers expensive agent loops. Defenses: per-tenant rate limiting, per-request budget caps, anomaly alerting.

### 10.5 Human-in-the-Loop

For high-stakes actions, the agent should pause and request human approval. Patterns:
- **Confirmation gates**: agent presents the action and waits for approval
- **Suggestion mode**: agent never acts directly, only proposes
- **Approval queues**: actions queued for batch review

LangGraph has first-class HITL support via interrupts. OpenAI Agents SDK supports it via guardrails. Most others require custom work.

---

## 11. Anti-Patterns to Avoid

**1. Multi-agent by default.** The Stanford 2026 paper (Tran & Kiela) showed single-agent often beats multi-agent under matched compute. Default to a strong single agent with good context engineering.

**2. The Russian-doll supervisor.** A supervisor that delegates to specialists that each delegate to more specialists. Costs balloon, debugging becomes impossible. Cap the depth at 2–3.

**3. Trusting role descriptions as architecture.** "I gave the Researcher a goal of being thorough" is not a coordination guarantee. Frameworks that hide coordination behind natural-language role descriptions (CrewAI) work great until they don't.

**4. Optimizing the wrong thing.** Don't squeeze 2% accuracy from a fancier orchestration pattern when a 20% gain awaits in better retrieval, better prompts, or basic caching.

**5. No evals.** Shipping changes based on "it looked good when I tried it" will silently regress. Build an eval set before scaling.

**6. Persistent state in conversation history.** Stuffing more and more context into the conversation as the agent loops. After 10 steps your context is half stale data. Either compact aggressively or move state to an external store.

**7. Single-vendor lock-in without an exit plan.** Provider-native SDKs (Claude, OpenAI, Google) are powerful but make you a hostage. If you commit, plan how you'd migrate in 12 months.

**8. Ignoring the protocol layer.** Building a custom tool integration when MCP would have worked is a sunk cost you'll regret in 18 months. Most companies building agent systems today are writing code that will be obsolete in 18 months — not because the agents are wrong, but because the glue between them is bespoke.

**9. Treating frameworks as identical.** They're not. The mental models differ profoundly (graph vs conversation vs handoff vs hierarchy). Pick one with a model that matches your problem.

**10. Building the multi-agent system before the single-agent baseline.** Always have a single-agent baseline. If multi-agent doesn't decisively beat it at matched compute, you've added complexity for nothing.

---

## 12. Where the Field Is Going

A few directional bets, based on what's visible in mid-2026:

**Consolidation continues.** From dozens of frameworks two years ago to ~12 that matter today. Expect another round of consolidation as Microsoft Agent Framework matures and provider-native SDKs (Claude, OpenAI, Google) absorb features from independents.

**Protocols win over frameworks long-term.** MCP and A2A let you mix-and-match. The frameworks become thinner adapters; the protocols become the durable substrate. Bet on the protocol layer over the framework layer for anything you want to last.

**Managed agent infrastructure.** Anthropic's Managed Agents (April 2026) and similar offerings move the "running an agent in production" problem from "your problem" to "their problem." Expect this pattern to spread.

**Coordination becomes a research area.** The Nechepurenko coordination-layer paper, Tran & Kiela's single-vs-multi paper, and the broader "agentic RAG as POMDP" framing suggest the next wave of innovation is in *how agents coordinate*, not just in what each agent can do. Frameworks will follow the research.

**Evaluation gets serious.** "We shipped it and it seems good" won't survive. Tools like RAGAS, LangSmith evals, Braintrust, Patronus, and DeepEval are building the eval-first culture the field needs.

**The single-agent comeback.** Don't be surprised if "boring" single-agent architectures with good context engineering, strong retrieval, and disciplined evaluation start beating fancy multi-agent setups across more benchmarks. The Data Processing Inequality is undefeated.

---

## Quick Reference — One-Line Summaries

If you only remember one line per framework:

- **LangGraph**: graph state machine, production-grade, the safe default for complex workflows
- **CrewAI**: role-based, fastest prototype, refactor for production
- **Microsoft Agent Framework**: AutoGen + Semantic Kernel merged, Azure-native, conversational
- **Claude Agent SDK**: "give your agent a computer", Anthropic-first, MCP-deep
- **OpenAI Agents SDK**: cleanest API, handoffs, OpenAI-first
- **Google ADK**: hierarchical, A2A-native, multimodal, four languages
- **Pydantic AI**: type-safe, testable, the production engineer's choice
- **Smolagents**: code-as-action, local-LLM-friendly, minimal
- **AWS Strands**: declarative, AWS-native
- **LlamaIndex Agents**: RAG-first, workflow-based
- **Mastra**: modern TypeScript alternative to LangChain
- **Letta**: long-term memory as a first-class citizen
- **Vercel AI SDK**: TS/Next.js, 20M+ downloads, agent abstractions in v6

The right framework is the one whose mental model matches your problem and whose blast radius (lock-in, learning curve, complexity) you can afford. None of them is universally best.