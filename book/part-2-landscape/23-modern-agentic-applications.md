# 23. Modern agentic AI applications: what they do and how they are built

> **What you need to be able to say:** for each major category of agent product in 2026, what it does, what the architecture looks like under the hood, where the hard part is, and what you would measure. These are also the systems interviewers ask you to design (chapter 40) and the companies that hire FDEs and AI engineers.

## 23.1 Coding agents

**Products:** Claude Code, OpenAI Codex, Cursor (editor + background agents), GitHub Copilot coding agent, Devin, Gemini CLI, Google Jules and Antigravity, AWS Kiro (spec-driven), Windsurf, Cline, Aider, Replit Agent, Lovable/Bolt (app generation).

**What they do:** take a task in natural language, read a repository, plan, edit files, run commands and tests, iterate until the task passes, and open a pull request — in the terminal, the IDE, or as a background cloud job.

**Architecture:** a model-driven loop with a small set of powerful tools (read/search files, edit, shell, web fetch, MCP), permission modes and hooks, sub-agents for parallel exploration with isolated context, persistent sessions, a project memory file (CLAUDE.md/AGENTS.md), context compaction, and a sandbox (container or worktree) per task. Retrieval over the repository is mostly *agentic search* (grep, glob, read) rather than a vector index, because code needs exact symbols and the index goes stale on every edit; some products add an embedding index for very large monorepos. The hard parts: context management on large repos, verification (tests as the reward signal — and the agent editing the tests to pass them, chapter 22), safe shell execution, and cost per task (a long task re-reads hundreds of thousands of tokens of context per turn, so prompt-cache hit rate is the dominant cost lever). **Metrics:** SWE-bench-style resolve rate on your own tasks, PR acceptance rate, cost and wall-clock per task, reverts and post-merge defects, human review time per PR.

## 23.2 Computer-use and browser agents

**Products:** OpenAI's agent mode/Operator lineage and the ChatGPT Atlas browser, Claude computer use and Claude in Chrome, Google's Project Mariner lineage, the Gemini computer-use model and Gemini agent features, Perplexity Comet, Browserbase/Stagehand, AgentCore Browser, Browser Use, Skyvern, Anthropic's browser toolset.

**What they do:** operate a GUI the way a person does — click, type, scroll, read screenshots or the accessibility tree — to complete tasks on sites with no API: forms, bookings, back-office systems, legacy ERPs.

**Architecture:** a perception loop (screenshot and/or DOM/accessibility tree → model → action), a safe-action layer (confirmation for purchases, sending, deleting; blocked sites), session isolation (dedicated browser profile or cloud browser), credential handling outside the model (password managers, OAuth, pause-for-login), and recordings for audit. Hard parts: brittleness of UIs, CAPTCHAs and bot detection (and site terms that forbid automation — Web Bot Auth, signed agent requests, is the emerging answer), prompt injection from page content, latency (a click costs a model call: 2–10 s per step, so a 30-step task takes minutes), and cost (each step re-sends a screenshot of 1,000–1,500 tokens). Prefer an API or MCP server whenever one exists; GUI automation is the fallback, not the architecture. Benchmarks: OSWorld(-Verified) for desktop tasks, WebArena and Online-Mind2Web for the web — the best reported OSWorld-Verified scores passed the ~72% human baseline in 2026 (mid-80s as of mid-2026; verify the current leaderboard), which says more about the benchmark's ceiling than about reliability on your ERP. Part 1 of this book is a worked example. **Metrics:** task success rate, steps per task, intervention rate, time per task, injection-resistance on a red-team page set.

## 23.3 Deep research and knowledge-work agents

**Products:** OpenAI Deep Research, Gemini Deep Research, Claude research, Perplexity Deep Research, Elicit and Consensus (science), Hebbia and AlphaSense (finance), Harvey and Legora (legal), Glean agents (enterprise).

**What they do:** turn a question into a cited report by searching, reading many sources, verifying and synthesizing over minutes rather than seconds.

**Architecture:** orchestrator–workers: a planner decomposes the question; parallel searcher agents with fresh context run web or enterprise search and read pages; a verifier checks claims against sources; a writer synthesizes with citations; budgets cap cost; the UI streams progress. Enterprise versions add permission-aware retrieval over internal documents. Hard parts: source quality and recency, citation faithfulness (a citation that exists but does not support the sentence is the most common defect, and readers rarely check), contradiction handling, cost (a single report can run to hundreds of thousands of tokens across sub-agents — the ~15× multi-agent token multiplier from chapter 22). Public yardsticks are BrowseComp and Humanity's Last Exam with tools; your own yardstick should be a set of questions with expert answers. **Metrics:** citation precision (do sources support the sentence), coverage against expert-written answers, user rating, cost per report.

## 23.4 Customer-support and service agents

**Products:** Sierra, Decagon, Intercom Fin, Zendesk AI agents, Salesforce Agentforce, ServiceNow Now Assist, Google Conversational Agents, Amazon Connect + Q, Microsoft Copilot Studio agents, Ada, Kore.ai.

**What they do:** resolve customer requests end to end across chat, email and voice — answer questions from policy and account data, take actions (refunds, changes, bookings), and hand off to humans with context.

**Architecture:** a supervisor with specialized sub-flows or agents, permission-aware RAG over help content and account data, typed tools over the CRM/order systems with approval thresholds, deterministic guardrails for regulated statements, conversation memory, a human handoff with full transcript and summary, and a quality loop (LLM judges sampling conversations, CSAT, escalation reasons). Hard parts: integrating with the systems of record, policy fidelity, measuring "resolution" honestly, multilingual quality. The canonical cautionary tale: Klarna announced in early 2024 that its assistant handled two-thirds of customer chats (the work of roughly 700 agents), and in 2025 said it would bring human agents back because quality had suffered — "resolution" counted as "no human touched it" is not the same as "the customer's problem was solved". Pricing models matter here too: several vendors charge per resolution (on the order of a dollar each), which makes the definition of "resolved" a commercial question. **Metrics:** resolution rate without human (verified by follow-up contact rate within 7 days), containment, CSAT, handle time, escalation accuracy, cost per conversation, policy-violation rate.

## 23.5 Voice agents

**Products:** drive-through systems (Wendy's FreshAI with Google, Yum/Taco Bell's platform, SoundHound, Presto, Hi Auto), phone agents (Vapi, Retell, Bland, ElevenLabs Conversational AI, PolyAI, Parloa), contact-center stacks (Amazon Connect + Nova Sonic, Google CES, Microsoft Dynamics 365 Contact Center, Genesys, NICE, Twilio ConversationRelay), platforms (LiveKit Agents, Pipecat, Deepgram Voice Agent API, OpenAI Realtime, Gemini Live).

**What they do:** hold spoken conversations in real time to take orders, answer calls, schedule, qualify and collect — with interruptions, noise and accents.

**Architecture:** telephony/WebRTC in; either a native speech-to-speech model or the chain (streaming ASR with endpointing → LLM with tools → streaming TTS); barge-in handling; turn-taking and latency budget (first audio under ~800 ms); grounding in a live catalog or account; a deterministic state machine for critical steps (order confirmation, payment); fallbacks to human; recording and QA. A typical chained budget: endpointing (deciding the caller has finished) 200–500 ms, LLM time-to-first-token 300–600 ms on a fast tier, TTS first audio 100–250 ms, transport 50–150 ms — which is why filler phrases, speculative LLM calls on partial transcripts, and small fast models for the turn are standard tricks. Chapter 41 designs the drive-through case. **Metrics:** task completion, order accuracy, interruptions handled, latency percentiles, escalation rate, cost per minute.

## 23.6 Sales, marketing and growth agents

**Products:** SDR agents (11x, Artisan, AiSDR, Regie), prospecting data agents (Clay), marketing content and review agents (Jasper, Typeface, Adobe GenStudio; the marketing-process-automation work on this book's reference resume), ad-ops agents.

**What they do:** research prospects, write and send personalized outreach, qualify replies, book meetings; generate and compliance-check marketing content across channels.

**Architecture:** data enrichment tools (CRM, web, LinkedIn-like sources), personalization prompts with brand voice, parallel reviewer agents (legal, brand, regulatory) with knowledge-graph-backed rules, human approval gates before sending or publishing, deliverability and compliance guardrails (CAN-SPAM, GDPR), and feedback loops from replies and conversions. Hard parts: hallucinated personalization, compliance, sending at scale without burning domains, measurement attribution. **Metrics:** reply and meeting rates, content cycle time, review escapes, cost per qualified lead.

## 23.7 Document and back-office workflow agents

**Products:** insurance claims and underwriting agents (Sixfold, Gradient AI, insurers' in-house), accounts payable and finance ops (Ramp, Brex, Vic.ai), legal contract agents (Harvey, Ironclad, Spellbook), healthcare prior-auth and coding (Cohere Health, Anterior), HR and procurement agents, Agent Bricks Information Extraction, n8n/Zapier/Make agent workflows.

**What they do:** read documents, extract and validate fields, apply policy, update systems, and route exceptions — the classic "digital worker".

**Architecture:** multimodal document understanding (chapter 19) → structured extraction with schemas and confidence → rules and policy checks (deterministic where law or policy is deterministic) → LLM judgement only for the genuinely ambiguous → system updates via typed tools → exception queues for humans → monitoring of field-level drift. Hard parts: edge cases, auditability, idempotent integration with legacy systems. **Metrics:** straight-through rate, accuracy per field, exception rate, cycle time, cost per document.

## 23.8 Data and analytics agents

**Products:** Databricks Genie, Snowflake Cortex Analyst/Agents, Google's data agents in BigQuery, Microsoft Fabric data agents, Hex Magic, Julius, ThoughtSpot Spotter, Tableau Pulse, text-to-SQL copilots in every BI tool.

**What they do:** answer business questions in natural language with charts and SQL, and increasingly run analyses (anomaly explanation, forecasting) on request.

**Architecture:** semantic layer (metrics, dimensions, joins) → candidate SQL generation constrained to the semantic model → execution with limits → self-check (row counts, nulls, sanity) → chart and narrative → logging of question/SQL pairs for evaluation. Hard parts: ambiguity, joins and metric definitions, trust (wrong numbers delivered confidently). **Metrics:** SQL execution accuracy on a gold set, user acceptance of answers, time to answer, share of questions needing an analyst.

## 23.9 IT operations, SRE and security agents

**Products:** SRE agents (Resolve AI, Traversal, Datadog Bits AI, PagerDuty and incident.io agents, Google's SRE agents), cloud ops (AWS and Azure Copilot/agents), security operations (Microsoft Security Copilot agents, CrowdStrike Charlotte, Google Security Operations, Torq, Dropzone), vulnerability triage (Semgrep and Snyk assistants).

**What they do:** investigate alerts across logs, metrics and traces, propose or execute remediations, write post-mortems; triage security alerts and run playbooks.

**Architecture:** tools over observability and cloud APIs (read-heavy), knowledge of runbooks and past incidents (retrieval), hypothesis-driven loops with explicit evidence, strict write permissions with approvals (restart, scale, rollback), and durable execution for long investigations. Hard parts: noisy data at scale, safety of actions, trust. **Metrics:** time to detect/mitigate, correct root-cause rate, actions requiring rollback, analyst hours saved.

## 23.10 Healthcare and regulated-domain agents

**Products:** ambient clinical documentation (Abridge, Microsoft DAX, Ambience, Nabla), prior authorization and revenue-cycle agents, patient-intake voice agents (Hippocratic AI, Assort), clinical trial matching, pharma literature agents.

**What they do:** listen to visits and draft notes; handle insurance workflows; answer patient logistics calls; search evidence.

**Architecture:** ASR with medical vocabulary, structured note generation with citation to transcript spans, clinician review as the mandatory gate, HIPAA-aligned storage and audit, PHI minimization in prompts, guardrails that forbid diagnosis or medication advice outside policy, and evaluation by clinicians. Hard parts: safety, liability, integration with EHRs (FHIR), consent. **Metrics:** documentation time saved, clinician edit rate, error categories, patient satisfaction.

## 23.11 Commerce and consumer agents

**Products:** shopping and checkout agents (ChatGPT Instant Checkout on the Agentic Commerce Protocol, Perplexity shopping, Amazon's assistants, Google's agentic checkout in Search and Gemini), travel booking agents, personal assistants (Lindy, Manus, Genspark), and the merchant side (Shopify and Stripe agent toolkits, AgentCore Payments, machine payments over HTTP 402).

**What they do:** search, compare and buy on the user's behalf; merchants expose catalogs and checkout to agents through protocols.

**Architecture:** product knowledge via MCP/feeds, cart and checkout protocols with delegated payment credentials and spend limits, strong confirmation UX, fraud and bot-policy considerations for merchants. The protocol map as of 2026 (it is crowded and still settling): **ACP** (Agentic Commerce Protocol, OpenAI and Stripe, September 2025) for checkout inside a chat assistant using a delegated, scoped payment token; **AP2** (Agent Payments Protocol, Google and partners, September 2025) for verifiable "mandates" that prove the user authorized a purchase; **UCP** (Universal Commerce Protocol, Google with Shopify, Etsy, Wayfair, Target and Walmart, January 2026) for discovery-to-checkout across agents, designed to work with A2A, AP2 and MCP; and for machine-to-machine micropayments **x402** (Coinbase; HTTP 402 with stablecoin settlement) and **MPP** (Machine Payments Protocol, Stripe and Tempo, March 2026; a 402 challenge plus spending sessions over stablecoins or cards). Hard parts: trust and payments, merchant bot policies, liability for wrong purchases, and proving user intent when a dispute arrives. **Metrics:** conversion, error/return rate, dispute rate.

## 23.12 Scientific, robotics and physical-world agents

Lab automation and literature agents (FutureHouse, Google's co-scientist), materials and drug discovery loops (design → simulate → synthesize → test), robotics stacks combining VLAs and world models (chapter 17) with LLM task planners. Architecture: closed loops with experiments as the verifier; the engineering is in the tool and safety layers.

## 23.13 Cross-cutting: what every serious agent product has

A **permission-aware retrieval** layer; **typed tools** with approval thresholds; **evaluation** on real tasks with judges and human review; **observability** with per-run traces and cost; **memory** with explicit write policies; **guardrails** at input, tool and output; a **human handoff** that preserves context; and a **FinOps** model (cost per task) that the business understands. If you can draw those eight boxes for any product above and say where the hard part is, you can design any of them in an interview.

### Critic's additions: build versus buy, category by category

The follow-up to "how is it built" is always "would you build it". The honest answer depends on where the differentiation sits:

| Category | Buy when… | Build when… |
|---|---|---|
| Coding agents | almost always — the harness is a commodity and improves monthly | you need it inside your own product (then build on an agent SDK, not from scratch) |
| Browser/computer use | the task is occasional and the vendor's sandbox meets security review | the target is one internal system — build an API or MCP server instead and skip the GUI |
| Deep research | the sources are public | the sources are internal and permissioned — the retrieval layer is the product |
| Customer support | the policies are standard and the vendor integrates with your CRM | resolution depends on proprietary systems, regulated statements or complex transactions |
| Voice | standard call flows on a supported telephony stack | latency, voice quality or a transactional state machine is the product |
| Document back office | the documents are common types (invoices, IDs) with prebuilt extractors | layouts and policies are specific, volume is high, and accuracy per field must be audited |
| Data/analytics agents | the platform's own agent (Genie, Cortex Analyst, Fabric data agents) covers the semantic layer | metrics span several platforms or need logic the semantic layer cannot express |

The FDE framing: buy the loop, build the context — the tools, the data access, the evals and the integration into the customer's systems are where your work creates value.
