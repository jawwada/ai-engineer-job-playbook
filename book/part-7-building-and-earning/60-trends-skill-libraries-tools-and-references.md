# 60. Modern trends, skill libraries, tools and references: an intuitive map for 2026

> **How to use this chapter:** trends tell you what to learn next; skill libraries tell you how agents are getting better without retraining; the tool lists are the practical shortlist; the references are where to read when a chapter here is not enough. Everything is dated October 2026; re-check anything that smells like it moved.

## 60.1 Twelve trends that are shaping the work

1. **Agents became infrastructure.** Managed runtimes with identity, gateway, memory, policy and evals on every cloud (AgentCore, Agent Engine, Foundry Agent Service), frameworks converging on graphs-with-state plus model-driven loops, MCP as the tool interface and A2A as the agent interface, and registries for discovering and governing agents, tools and skills inside an organization (AWS's Agent Registry in AgentCore, the public MCP Registry). *What to learn:* one runtime deeply, MCP server authoring, A2A basics.
2. **Harness engineering over prompt engineering.** The gains now come from the loop around the model: planning tools, file systems as memory, sub-agents with fresh context, compaction, hooks, permissions, skills — the "deep agent" harness (chapter 22b). *What to learn:* build a harness once by hand, then use Deep Agents / the Claude Agent SDK.
3. **Context engineering replaced "prompt tricks".** Caching, ordering, trimming, retrieval quality, memory with write policies; long context did not kill retrieval, it moved it up-stack. *What to learn:* measure recall and cost per request; design the window.
4. **Reasoning as a budget.** Thinking tokens and effort levels, routed by difficulty; latent-reasoning research in the background. *What to learn:* per-node budgets and accuracy-per-dollar evals.
5. **Open-weight parity for most workloads** (DeepSeek V4, Qwen 3.8, GLM-5.x, Kimi K3, Llama 4, gpt-oss, Gemma 4, plus the Mistral and NVIDIA Nemotron families; version numbers move monthly, so verify before you quote one) and a mature serving stack (vLLM, SGLang). "Parity" means on your eval set, not on a leaderboard: the open model wins on cost and data residency and loses on the hardest reasoning and on tool-use reliability, so the honest comparison is accuracy-per-dollar per node. *What to learn:* serve one open model with quantization and measure.
6. **Evaluation is the product discipline.** Judges in CI, trajectory evals, red-team suites, OpenTelemetry GenAI conventions; "production-ready" means evaluated and traced. *What to learn:* build one eval service end to end.
7. **Skills and self-improvement loops.** Reusable instruction-plus-script packages the model loads on demand; eval-driven prompt optimization (DSPy/GEPA, Agent Bricks, AgentCore Optimization); memory of lessons; agents that improve without weight updates. *What to learn:* write skills; run one optimization loop against an eval set.
8. **Voice went native and multimodal went everywhere.** Speech-to-speech models, real-time APIs, document understanding by vision models, video understanding at hours of context. *What to learn:* one voice agent; one multimodal document pipeline.
9. **Governance caught up.** EU AI Act obligations phasing in, model risk management in finance, HIPAA-aligned AI stacks, identity-propagating agents, policy engines, content safety suites. *What to learn:* chapter 30 cold; one negative-test suite.
10. **FinOps for AI.** Token attribution, routing, caching and distillation as standard practice; unit economics in every roadmap. *What to learn:* chapter 31's worked example with your own numbers.
11. **Coding agents changed how software is written** — and interviewers ask how you work with them (chapter 52). *What to learn:* a disciplined workflow with tests as the reward.
12. **Vertical agents won.** Customer support, legal, finance ops, healthcare documentation, sales, IT ops: the winners are products with deep integrations and evaluation data, not general chatbots (chapter 23). *What to learn:* pick a vertical and build the labs there.

**Critic's additions: turning each trend into an interview answer and a lab.** A trend list is only useful if it changes what you can demonstrate. The mapping below is the mechanism: the question an interviewer derives from the trend, and the artifact that answers it.

| Trend | The question it generates | The artifact that answers it |
|---|---|---|
| 1 Agents as infrastructure | "Walk me through deploying an agent on a managed runtime with identity and a gateway." | Lab 2 or 4 (chapter 34): an agent on AgentCore or Agent Engine with a tool behind the gateway and a trace |
| 2 Harness engineering | "What is in your harness besides the model?" | A repo with hooks, a planning tool, sub-agents and compaction, and a before/after eval |
| 3 Context engineering | "How do you decide what goes into the window?" | A context budget table per node and a recall-versus-cost curve |
| 4 Reasoning as a budget | "When do you turn thinking on?" | Per-node accuracy-per-dollar results at three budgets |
| 5 Open-weight parity | "Would you use an open model here?" | One served open model with quantization and the eval-set comparison against a frontier API |
| 6 Evaluation as product discipline | "Show me your eval pipeline." | Judges calibrated to human labels, running in CI, with a regression history |
| 7 Skills and self-improvement | "How does the agent get better without retraining?" | A skill with tests and one optimization run (DSPy or GEPA) with the numbers |
| 8 Voice and multimodality | "Design a voice agent; where does latency go?" | A voice lab with a latency budget per stage and a document pipeline with field-level accuracy |
| 9 Governance | "How do you limit an agent to the user's data?" | Identity propagation, ACL-filtered retrieval, and a negative-test suite |
| 10 FinOps for AI | "Your bill doubled. Why?" | Cost attribution per feature and tenant, a routing policy and the savings table (chapter 31) |
| 11 Coding agents | "How do you work with coding agents?" | Your workflow with tests as the reward signal and a PR an agent wrote that you reviewed |
| 12 Vertical agents | "Why did the horizontal chatbot lose?" | A vertical lab with integrations and evaluation data from the domain (Part 6) |

## 60.2 Skill libraries: what they are and how to build one

A **skill** is a folder with a short instruction file (what the skill does, when to use it, step-by-step procedure), optional scripts and reference files, loaded by the agent on demand (progressive disclosure keeps context small). Anthropic's Agent Skills define the format used by Claude Code and the Claude Agent SDK (SKILL.md with name, description, allowed tools, invocation rules; scripts referenced with `${CLAUDE_SKILL_DIR}`); LangChain's Deep Agents add SkillsMiddleware; other frameworks implement the idea as tool bundles or playbooks. The research lineage runs from Voyager's growing skill library for embodied agents to today's production libraries.

**A good skill:** states what to do, not why; names its inputs and outputs; includes a verification step; bundles deterministic scripts for the parts that must be exact; carries one or two worked examples; stays under a few hundred lines; and is versioned with tests (run the skill on three recorded cases in CI).

**A skill library for an engineering team:** repo setup and conventions; code review checklist; incident runbooks; data-access patterns (how to query the lakehouse safely); eval authoring; prompt/tool design review; deployment playbooks; customer discovery and acceptance-criteria templates (for FDEs). The kit in this repo is a skill library for job searching; the structure transfers.

**Self-improving skills:** after a run, the agent proposes an edit to the skill ("the form has a hidden consent checkbox; check it only after approval"); a human reviews the diff; the skill's tests run; the change ships. This is the safest self-improvement loop (chapter 22b).

**Critic's additions: a minimal skill, and how it is tested.** The paragraphs above describe skills; here is one, so the shape is concrete. A skill called `rag-eval` is a folder with `SKILL.md`, a `scripts/` directory and an `examples/` directory. The instruction file has front matter (`name: rag-eval`, a one-line `description` that says when to use it — "run the retrieval eval set and report recall@k and faithfulness; use before any prompt or index change ships" — and an `allowed-tools` list limited to reading files and running the eval script) followed by the procedure: confirm the eval set path and the index version; run `scripts/eval.py --set <path> --k 10`, which is deterministic and writes `results/<timestamp>.json`; compare with the last committed results and flag any metric that fell by more than two points; write a five-line summary in the fixed format in `examples/report.md`; stop and ask before modifying anything. The test for the skill is three recorded cases in CI: a run where nothing changed (the summary must say so), a run with a planted regression (the summary must flag the right metric), and a run with a missing eval set (the skill must stop and ask, not invent a set). What makes this a skill rather than a prompt is the deterministic script for the exact part, the fixed output format, and the tests; what makes it reusable is that it says nothing about why — the why lives in chapter 32 and in the engineer's head.

## 60.3 Tool shortlist (one line each)

- **Agent frameworks:** LangGraph, Claude Agent SDK, Google ADK, AWS Strands, OpenAI Agents SDK, Microsoft Agent Framework, Deep Agents, PydanticAI, CrewAI, LlamaIndex Workflows, DSPy (optimization).
- **Runtimes:** Bedrock AgentCore, Vertex AI Agent Engine, Foundry Agent Service, LangGraph Platform, Modal, Temporal (durable execution).
- **Protocols and registries:** MCP (servers, inspector, the public MCP Registry), A2A (now under the Linux Foundation), Docker MCP Catalog, AWS Agent Registry in AgentCore (preview 2026), Claude Code plugin marketplaces; commerce protocols (ACP, AP2, UCP) for agent-initiated purchases.
- **Models and serving:** Claude, GPT, Gemini; DeepSeek, Qwen, Llama, GLM, Kimi, gpt-oss, Gemma; vLLM, SGLang, TensorRT-LLM, Ollama; LiteLLM/Portkey gateways.
- **Retrieval:** pgvector, Qdrant, Weaviate, Milvus, Pinecone, Vespa, Elasticsearch/OpenSearch; Vertex AI Search, Azure AI Search, Bedrock Knowledge Bases, Databricks Vector Search; rerankers (Cohere, Voyage, BGE); parsers (Docling, Unstructured, LlamaParse, Document AI/Intelligence/Textract); graphs (Neo4j, Neptune, Memgraph; Microsoft GraphRAG, LightRAG).
- **Evaluation:** Ragas, DeepEval, promptfoo, Inspect, LangSmith, Langfuse, Braintrust, Phoenix, MLflow evaluate, Databricks Agent Evaluation, Vertex AI evaluation, Foundry evaluation SDK, AgentCore Evaluations; red teaming: PyRIT, garak, DeepTeam.
- **Observability:** OpenTelemetry (GenAI conventions), Langfuse, LangSmith, Phoenix/Arize, Datadog LLM Observability, New Relic, Dash0, Honeycomb, Grafana stack, Cloud Trace/CloudWatch/Azure Monitor.
- **Guardrails and security:** Bedrock Guardrails, Azure Content Safety and Prompt Shields, Model Armor, NeMo Guardrails, Guardrails AI, Lakera, Llama Guard; OpenFGA, Cedar/Verified Permissions, OPA; Presidio, DLP APIs; Vault/Secrets Manager/Key Vault.
- **Voice:** LiveKit Agents, Pipecat, Vapi, Retell, Twilio ConversationRelay, Deepgram, ElevenLabs, Cartesia, OpenAI Realtime, Gemini Live, Nova Sonic; Dialogflow CX/CES, Lex/Connect, Copilot Studio.
- **Data:** Databricks, Snowflake, BigQuery, Fabric; Airflow, Dagster, dbt, Lakeflow; Kafka, Flink; Delta/Iceberg; Great Expectations/Soda; MLflow, W&B.
- **Collection:** Apify, Firecrawl, Crawl4AI, Browserbase, Playwright; official APIs and RSS first (chapter 54).
- **Coding agents:** Claude Code, Codex, Cursor, GitHub Copilot agent, Gemini CLI, Devin, Aider, Cline.
- **Low-code:** Copilot Studio, Gemini Enterprise (formerly Agentspace)/Conversational Agents, Agentforce, n8n, Dify, Langflow, Zapier Agents.

## 60.4 Interesting apps and solutions to study (what to look at and why)

- **Claude Code / Codex / Cursor** — the deep-agent harness in production; study the tool set, permissions, sub-agents and memory files.
- **Perplexity and the deep-research products** — orchestrator–workers with citation verification; study how they present sources and budgets.
- **Sierra and Decagon** — support agents with actions and evaluation loops; study the handoff and QA tooling.
- **Harvey, Hebbia, Rogo** — document-heavy vertical agents with permissions; study review workflows and citations.
- **Abridge / Microsoft Dragon Copilot (formerly Nuance DAX) / Ambience** — ambient clinical documentation; study safety gates and clinician review as product.
- **Wendy's FreshAI (with Google) and the drive-through vendors** — voice at the edge; study latency engineering and crew handoff.
- **Databricks Genie, Snowflake Cortex Analyst** — text-to-SQL done with semantic layers; study trust features.
- **Microsoft 365 Copilot, Google Gemini Enterprise (formerly Agentspace), Glean** — permission-aware enterprise retrieval at scale; study ACL sync.
- **Shopify/Stripe agent toolkits and the commerce protocols (OpenAI-Stripe's Agentic Commerce Protocol, Google's Agent Payments Protocol, the Universal Commerce Protocol with Shopify and other retailers)** — commerce for agents; study payment delegation, mandates and confirmation UX.
- **Resolve AI, Datadog Bits** — SRE agents; study evidence-driven investigation and write-permission design.
- **Open-source references:** Microsoft GraphRAG, LightRAG, Ragas, promptfoo, Langfuse, the OpenTelemetry Demo (for the telemetry wiring) with the GenAI instrumentation libraries (OpenLLMetry, OpenInference), Deep Agents, ADK samples, Strands samples, the OpenAI Agents SDK examples, Anthropic's cookbook and quickstarts.

**Critic's additions: five more to study, and what each one teaches.** *Lovable, Bolt and v0* — app generation from prompts; study how they constrain the model with a fixed stack and a preview loop, which is harness engineering for non-engineers. *Manus (acquired by Meta in December 2025) and the general-purpose agent products* — long-horizon tasks in a sandboxed computer; study the task-plan display, the checkpointing and where they ask for confirmation. *Claude for Chrome and OpenAI's browser agents* — study the permission prompts and the site allow-lists, because that is what your enterprise customers will ask you to copy. *Cursor and Claude Code's permission systems* — study how "ask before write" is made cheap enough that people leave it on. *Kraken Technologies (Octopus Energy's platform, being demerged; a minority stake was sold at an $8.65 billion valuation in December 2025)* — not an agent product but the best example in the book's domains of a system of record that makes every later AI feature cheap; study why licensing the platform to competitors was the right move.

## 60.5 References (read in this order)

**Foundations.** Anthropic, "Building effective agents" (patterns); Anthropic, "Contextual Retrieval"; Microsoft Research, "From Local to Global: A GraphRAG Approach"; Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (the original RAG paper); Vaswani et al., "Attention Is All You Need"; Hu et al., "LoRA"; Rafailov et al., "Direct Preference Optimization"; the DeepSeek-R1 report (RL with verifiable rewards); Yao et al., "ReAct"; Shinn et al., "Reflexion"; Wang et al., "Voyager" (skill libraries); Tran & Kiela, "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets" (2026 — the finding that much of the multi-agent advantage was extra compute); Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (2025 — a taxonomy of failure modes worth reading before designing a supervisor); Liu et al., "Lost in the Middle" (2023 — why evidence ordering matters); the OWASP Top 10 for LLM Applications; MITRE ATLAS.

**Critic's additions: the vendor engineering posts that function as textbooks.** Anthropic's "How we built our multi-agent research system", "Effective context engineering for AI agents", "Writing tools for agents" and "Building agents with the Claude Agent SDK"; OpenAI's "A practical guide to building agents"; Google's "Agents" whitepaper series; LangChain's posts on context engineering and Deep Agents; Chroma's "Context Rot" study on long-context degradation. Each is short, dated and opinionated, which is what an interview answer should be; read them with a notebook open and write the one-line claim and the one number you took from each.

**Documentation worth reading end to end.** Model Context Protocol specification; A2A protocol; OpenTelemetry GenAI semantic conventions; Claude Code docs (skills, sub-agents, hooks, MCP, Chrome, Remote Control); Google ADK and Agent Engine docs; AWS Strands and AgentCore docs; Azure AI Foundry Agent Service and Agent Framework docs; LangGraph concepts; Databricks Mosaic AI Agent Framework and Agent Evaluation docs; Dialogflow CX/Conversational Agents docs (flows, pages, playbooks, data stores, test cases).

**Benchmarks and leaderboards (for orientation, not decisions).** LMArena, Artificial Analysis, SWE-bench Verified, τ²-bench, BrowseComp, MTEB/MMTEB, ARC-AGI, Humanity's Last Exam.

**Industry reports and newsletters.** The FinOps Foundation's framework and "FinOps for AI" material; cloud providers' well-architected AI/ML lenses; Latent Space, The Batch, Import AI, Ahead of AI, Interconnects, Simon Willison's weblog, the LangChain and Anthropic engineering blogs; vendor release notes (AgentCore, Agent Engine, Foundry) read monthly.

**Part 6 of this repo** holds longer study guides and the reading list of multi-agent papers.
