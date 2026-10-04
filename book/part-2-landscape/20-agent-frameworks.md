# 20. Agent frameworks: LangGraph, Claude Agent SDK, OpenAI Agents SDK, Google ADK, Strands, Microsoft Agent Framework, CrewAI, PydanticAI, LlamaIndex and friends

> **What you need to be able to say:** the three shapes a framework can take (graph of steps, model-driven loop, role-based crew), which products take which shape, what each gives you for free (state, persistence, streaming, tools, MCP, tracing, deployment), and why you would still write a 60-line loop yourself sometimes. Go deeper: Part 6 → *Multi-agent frameworks — complete guide* and *Agentic AI design patterns study guide*.

## 20.1 Three shapes

1. **Graph of steps with explicit state.** You declare nodes (functions or model calls), edges (fixed or conditional), and a typed state object that flows through; the runtime checkpoints state so runs can pause, resume, branch and be inspected. LangGraph is the archetype; Google ADK's workflow agents, Microsoft Agent Framework workflows and LlamaIndex Workflows take the same view. Best for production systems where you need determinism, human-in-the-loop interrupts and replay.
2. **Model-driven loop.** You give a model a system prompt, tools and a stop condition; the model plans and calls tools until done. Claude Agent SDK, AWS Strands, OpenAI Agents SDK, PydanticAI and smolagents are built this way (with graphs available as an option). Fastest to build, most flexible, and the behaviour is only as predictable as the model — which in 2026 is usually predictable enough with good tools and evals.
3. **Role-based crew.** You define agents with roles, goals and backstories, hand them tasks, and a process (sequential or hierarchical) coordinates them. CrewAI popularized it; AutoGen's conversational multi-agent was the research version. Good for demos and content pipelines, harder to debug and to bound in cost.

Most teams end up with shape 2 inside shape 1: a graph of a few explicit stages, where one or two stages are model-driven loops with tools.

## 20.2 The products, compared

| Framework | Shape | Language | Model support | Tools / MCP | State & persistence | Multi-agent | Tracing | Hosting |
|---|---|---|---|---|---|---|---|---|
| **LangGraph** (+ LangChain 1.0 `create_agent` with middleware; Deep Agents on top) | graph (+ prebuilt ReAct agent) | Python, TS | any via LangChain integrations | tools, MCP adapters | checkpointers (memory, Postgres, Redis), threads, time-travel, interrupts | subgraphs, supervisor, swarm libraries | LangSmith (or OTel) | LangSmith Deployment (formerly LangGraph Platform; cloud, hybrid, self-hosted), self-host |
| **Claude Agent SDK** | model-driven loop (the Claude Code harness) | Python, TS | Claude (API, Bedrock, Google's Agent Platform, Foundry) | built-in file/shell/web tools, MCP client, custom tools, Skills | sessions, resumable; hooks on tool events; permission modes | subagents (parallel, isolated context) | hooks + OTel export | you host; Claude Managed Agents (beta, \$0.08 per active session-hour plus tokens) |
| **OpenAI Agents SDK** (+ AgentKit) | loop with handoffs | Python, TS | OpenAI; others via LiteLLM | function tools, hosted tools (web/file search, computer use), MCP | sessions (SQLite/Redis), tracing | handoffs, agents-as-tools | built-in traces dashboard | you host; AgentKit's Agent Builder and ChatKit for hosted flows and UI |
| **Google ADK** | graph + loop (LlmAgent, Sequential/Parallel/Loop agents) | Python, Go, Java, TS | Gemini first; others via LiteLLM | function tools, OpenAPI, MCP, built-in search/code exec | sessions, memory, artifacts; Agent Memory Bank | sub-agents, A2A native | OTel, Cloud Trace | Agent Runtime (formerly Agent Engine) on the Gemini Enterprise Agent Platform (formerly Vertex AI), Cloud Run |
| **AWS Strands Agents** | model-driven loop | Python, TS (preview since December 2025) | Bedrock default; Anthropic, OpenAI, Ollama, llama.cpp, LiteLLM | `@tool` functions, MCP first-class | session managers (file, S3, AgentCore Memory) | agents-as-tools, swarm, graph, A2A | OTel built in | AgentCore Runtime or Harness, Lambda, Fargate/EKS |
| **Microsoft Agent Framework** (SK + AutoGen; 1.0 GA April 2026) | graph workflows + ChatAgent | Python, .NET | Azure OpenAI/Foundry, OpenAI, others | plugins, MCP, OpenAPI | threads, checkpointing | group chat, handoff, magentic orchestration | OTel GenAI conventions | Foundry Agent Service (hosted agents) |
| **CrewAI** | role-based crew (+ Flows for control) | Python | any via LiteLLM | tools, MCP | memory modules | crews, hierarchical process | built-in + integrations | CrewAI AMP |
| **PydanticAI** | typed loop | Python | any | typed tools, MCP | dependency injection, graphs (pydantic-graph) | agent delegation | Logfire/OTel | you host |
| **LlamaIndex** | workflows (event-driven) + data framework | Python, TS | any | tools, MCP; best-in-class RAG components | workflow state | agent workflows | OTel integrations | LlamaCloud |
| **Haystack** | pipelines | Python | any | components, MCP | pipeline state | agents | OTel | you host |
| **DSPy** | programs with optimizable prompts | Python | any | — | — | modules | — | — |
| **Mastra / Vercel AI SDK** | TypeScript-first loops and workflows | TS | any | tools, MCP | memory, workflows | networks | OTel | Vercel |
| **smolagents** | code-acting loop (agent writes Python) | Python | any via HF | tools, MCP | — | managed agents | — | you host |

(Details change monthly; the shape, the state model and the hosting story are what persist.) Two 2026 developments cut across the table: **managed harnesses** (AgentCore Harness, Foundry hosted agents, Claude Managed Agents) let you skip the framework entirely for standard agents — model, instructions, tools, skills and memory declared through an API — and **AG-UI** (the agent–user-interface event protocol, adopted by AgentCore, CopilotKit and several frameworks) standardizes streaming of agent events to a front end, which used to be bespoke per framework.

## 20.3 What you should look at in any framework

- **State model.** Typed, inspectable, checkpointed? Can you pause for a human and resume a week later? Can you replay a failed run from step 7? Graph frameworks answer yes; loop frameworks answer "sessions".
- **Tool model.** Plain functions with schemas generated from type hints; MCP for external tools; permission or approval hooks before dangerous tools; parallel tool calls; structured outputs.
- **Context control.** How the framework manages the growing conversation: summarization, compaction, subagents with fresh context, file-backed memory. This is where agent reliability is won in 2026 ("context engineering").
- **Multi-agent primitives.** Supervisor/sub-agent, handoff, agents-as-tools, swarm; whether sub-agents get isolated context windows (they should) and bounded turns and budgets (they must).
- **Observability.** Native OpenTelemetry with the GenAI semantic conventions means you can use any backend; proprietary tracing locks you to one vendor's UI.
- **Evaluation hooks.** Running an eval set against a graph with mocked tools; recording runs as test cases.
- **Deployment.** Does the vendor run it for you (LangSmith Deployment, Agent Runtime, AgentCore, Foundry, Claude Managed Agents) and what does a session-hour cost? Can you self-host on Kubernetes or serverless?
- **Model portability.** Native support for the three big providers plus open models; a gateway (LiteLLM, Portkey) if not.
- **Durability and idempotency.** What happens if the process dies between a tool call and its result being checkpointed? Graph frameworks replay from the last checkpoint, which re-executes the tool — fine for reads, dangerous for a payment or an email. Tools with side effects need idempotency keys or a "check before act" step, and the framework needs to let you mark them.
- **Streaming surface.** Token streaming for the UI is table stakes; what you also need is an *event* stream (tool started, tool finished, approval requested, sub-agent spawned) that a front end and a trace backend can both consume — this is what AG-UI standardizes.

## 20.4 Code shapes to recognize

A LangGraph agent is a state schema, a few nodes and conditional edges:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    question: str
    docs: Annotated[list, operator.add]
    answer: str
    verified: bool

def retrieve(s): return {"docs": search(s["question"])}
def answer(s): return {"answer": llm(prompt(s["question"], s["docs"]))}
def verify(s): return {"verified": judge(s["answer"], s["docs"])}

g = StateGraph(State)
g.add_node("retrieve", retrieve); g.add_node("answer", answer); g.add_node("verify", verify)
g.set_entry_point("retrieve"); g.add_edge("retrieve", "answer"); g.add_edge("answer", "verify")
g.add_conditional_edges("verify", lambda s: END if s["verified"] else "retrieve")
app = g.compile(checkpointer=PostgresSaver(...))
```

A Strands agent is a model, a prompt and tools; the loop is the model's:

```python
from strands import Agent, tool
from strands.tools.mcp import MCPClient

@tool
def lookup_order(order_id: str) -> dict:
    """Return the order record for an order id."""
    return orders.get(order_id)

agent = Agent(system_prompt="You are a support agent...", tools=[lookup_order, MCPClient(...)])
result = agent("Where is order 8841?")
```

A Claude Agent SDK call is similar, with the harness's built-in tools and permission model:

```python
from claude_agent_sdk import query, ClaudeAgentOptions
async for msg in query(prompt="Tailor resume.docx to jd.md and save as out.docx",
                       options=ClaudeAgentOptions(allowed_tools=["Read","Edit","Bash"], permission_mode="acceptEdits")):
    ...
```

Being able to sketch these three in an interview shows you know the shapes, not just the names.

## 20.5 When to write it yourself

A single-agent tool loop is about sixty lines against any model API: build messages, call the model with tools, execute tool calls, append results, repeat until no tool calls or a budget is hit. Write it yourself when you need full control of context, when a dependency's upgrade cadence is a risk, or when the "agent" is really a fixed pipeline. Use a framework when you need persistence, interrupts, multi-agent primitives, streaming UIs and tracing without building them. Either way, the eval set and the tool design matter more than the framework. The loop itself is short enough to write on a whiteboard:

```python
def run(client, system, tools, user_msg, max_turns=25, max_cost=2.00):
    msgs, spent = [{"role": "user", "content": user_msg}], 0.0
    for turn in range(max_turns):
        resp = client.messages.create(model=MODEL, system=system, tools=tools,
                                      messages=msgs, max_tokens=4096)
        spent += cost(resp.usage)
        msgs.append({"role": "assistant", "content": resp.content})  # keep thinking blocks intact
        calls = [b for b in resp.content if b.type == "tool_use"]
        if resp.stop_reason != "tool_use" or not calls or spent > max_cost:
            return resp, msgs                      # done, or budget hit (a resumed run must first
                                                   # answer any pending tool_use with a tool_result)
        results = []
        for c in calls:                             # parallel where tools are independent
            ok, out = execute(c.name, c.input)      # validate args, enforce allow-list, truncate output
            results.append({"type": "tool_result", "tool_use_id": c.id,
                            "content": out[:MAX_TOOL_CHARS], "is_error": not ok})
        msgs.append({"role": "user", "content": results})
    return None, msgs                               # turn budget exhausted
```

Everything a framework adds hangs off this skeleton: checkpoint `msgs` after each turn (persistence), pause before `execute` for approval (HITL), summarize `msgs` when it grows (compaction), run the loop in a sub-process with a fresh `msgs` (sub-agents), and emit a span per iteration (tracing). If you can say where each of those hooks goes, you understand every framework in the table.

## 20.6 Choosing

- On AWS with Claude or Nova and a need for managed runtime, identity and memory: **Strands + AgentCore**, or LangGraph on AgentCore if the team already knows it; **AgentCore Harness** when the agent is standard enough to declare rather than code.
- On Google Cloud with Gemini: **ADK + Agent Runtime**; A2A if you must interoperate with other vendors' agents.
- On Azure, Microsoft shop: **Agent Framework + Foundry Agent Service**; Copilot Studio for business-built agents.
- Cross-cloud, Python team, complex stateful workflows with humans in the loop: **LangGraph** (self-hosted or LangSmith Deployment).
- Coding and file-system style agents, or an agent that should feel like Claude Code: **Claude Agent SDK**.
- TypeScript product teams: **Vercel AI SDK / Mastra**, or the OpenAI Agents SDK in TS.
- Research-style prompt optimization: **DSPy** on top of any of the above.

**Interview line:** *"I separate the workflow skeleton — an explicit graph with checkpointed state and human interrupts — from the agentic steps inside it, which are model-driven loops with typed tools and MCP. LangGraph or ADK for the skeleton, Strands or the Claude Agent SDK for the loops, OpenTelemetry for traces, and the cloud's managed runtime for identity and memory."*
