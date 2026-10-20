# Agentic Design Patterns: the ten patterns, from intuition to code

An interactive page (open in a browser) on the ten patterns agent systems are assembled from: prompt chaining, routing, parallelization, reflection (evaluator-optimizer), tool use and MCP, the ReAct loop, planning (plan-and-execute), multi-agent (orchestrator-workers, supervisor, A2A), memory and knowledge retrieval, and human-in-the-loop with guardrails and exception handling. Each pattern has six tabs: an intuitive introduction with a diagram and the when/when-not; a small worked example; how to build it with Google's Agent Development Kit; how to build it with LangGraph / LangChain 1.x; where it is used in real products and research; and the pitfalls with tips.

Three reference cards: choosing a pattern (a task-trait decision table, the ladder of autonomy from one call to multi-agent, common compositions and a cost/latency table); an ADK <-> LangGraph crosswalk (concept map, the run loop in each, deploy/observe/evaluate); and anti-patterns with what to measure at each layer.

## Files

| File | What it is |
|---|---|
| `agentic-design-patterns.html` | The page: 13 cards, 66 tabs, 10 diagrams. Self-contained; loads fonts from Google Fonts when online and falls back to system fonts offline. |

## Related

- `knowledge primers/self-improving-agents/` — the loop that uses reflection, memory and discovery to improve a frozen-weight agent.
- `knowledge primers/system-design-top-10/` — the systems these patterns are deployed into.
- `knowledge primers/agentic-ai-field-guide/` — FinOps, observability, evaluation and security around them.

## How it was built

Written on 19 October 2026 from Anthropic's "Building effective agents", Google's ADK documentation (LlmAgent, Sequential/Parallel/Loop agents, tools, MCPToolset, planners, callbacks, memory services, A2A), the LangChain and LangGraph 1.x documentation (StateGraph, Send, Command, interrupt, create_agent and middleware, stores, MCP adapters), and the ReAct, Reflexion and Self-Refine papers. Framework APIs move quickly; check import paths against the current docs before running the snippets.
