# Self-Improving Agents: improvement with frozen weights

A knowledge primer, written as a single HTML page, on how an agent gets better at a job when its model never changes. It covers what τ-bench and τ²-bench measure and how to read pass^k; the six parts of an agent gym and the difference between an evaluation gym and a training gym; where improvement can live when the weights are frozen (prompt, memory, critique, discovery, the control loop); golden trajectories and what they are for; right tool usage and the tool-call accuracy metric; the five mechanisms in depth — dynamic prompt optimisation (bootstrapped exemplars, instruction search, textual gradients, failure-driven rules), episodic memory in RAG with a worked Docker-failure case and its write and read policies, automated critique and Reflexion, dynamic discovery of tools and environments, and the shell and web-search tools — and the pitfalls: prompt injection (including memory poisoning), ephemeral sandboxing, network segregation and human-in-the-loop gates. It closes with a reference architecture and a maturity ladder with the number to watch at each level.

## Files

| File | What it is |
|---|---|
| `self-improving-agents.html` | The primer as a self-contained page with two figures (the improvement loop; the reference architecture). Open in a browser. |

## Related

- `knowledge primers/agentic-ai-field-guide/` — FinOps, observability, design, evaluation and security on Google Cloud (the LLM-as-a-judge sections this page builds on).
- `knowledge primers/toloka-fde-final-round/scoping-and-pricing-playbook.html` — scoping and pricing the agentic gyms and coding environments this page assumes.
- `labs/dataset-examples/12-agentic-gym/` — a runnable τ-bench-style gym that prints pass^k.

## How it was built

Written on 19 October 2026 from the τ-bench and τ²-bench papers, Terminal-Bench and SWE-bench, the Reflexion, Self-Refine and CRITIC papers, DSPy and its optimisers, OPRO and TextGrad, Voyager, ExpeL and Generative Agents, the Model Context Protocol specification and the major labs' prompt-injection guidance. Benchmark figures are approximate and dated.
