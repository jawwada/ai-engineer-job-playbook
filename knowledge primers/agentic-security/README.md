# Agentic Security — knowledge primer

An interactive, single-file primer on securing agentic systems, written for interview preparation (Google FDE / Applied AI) and for consultative conversations with clients. Open `agentic-security.html` in any browser; no build step, no network needed beyond the Google Fonts link (the page falls back to system fonts without it).

## What is on the page

Ten topic cards, each with six tabs — **Concepts** (with a diagram), **Attacks** (with illustrative payloads), **Controls**, **On Google Cloud**, **Code**, **Say it in the room** — plus three reference cards.

| # | Card | What it covers |
|---|------|----------------|
| 1 | Threat model & trust boundaries | The model as an untrusted component holding trusted powers; four entry points; Google's three principles; a threat register in YAML |
| 2 | Prompt injection | Direct vs indirect, zero-click, instruction hierarchy, spotlighting, dual LLM, CaMeL, the six design patterns; EchoLeak, GitHub MCP, Supabase, ForcedLeak; ADK callbacks and plan-then-execute code |
| 3 | Identity & IAM for agents | IAM primitives in one table; agent-auth vs user-auth; confused deputy; Agent Identity (SPIFFE), Auth Manager, deny policies, PAB, VPC-SC, Org Policy; the Vertex AI service-agent escalation research; gcloud + ADK code |
| 4 | Tool security & excessive agency | The tool-call pipeline; side-effect classes; policy as code (Rego); approvals that mean something; budgets; ADK `before_tool_callback` and `require_confirmation`, LangChain middleware |
| 5 | Sandboxing & execution isolation | The isolation ladder (gVisor, microVMs); the sandbox contract; ADK code executors; a hardened `docker run` |
| 6 | Data security & exfiltration | The lethal trifecta; every channel out; ACL-aware retrieval; DLP at four points; output handling; Sensitive Data Protection and Model Armor code |
| 7 | Memory & RAG poisoning | Four stores and who may write them; the write gate by source; corpus integrity; LangGraph store and Memory Bank code |
| 8 | MCP, A2A & multi-agent | MCP authorization by spec revision (2025-06-18, 2025-11-25, 2026-07-28); tool poisoning, rug pulls, shadowing; signed agent cards; cascades and rogue agents; Agent Gateway; server-side token validation and pinned tool descriptions |
| 9 | The guardrail stack | Five layers (access, ingress, model, action, egress) plus observe; Model Armor in one paragraph; ADK plugin and LangChain middleware; template and floor settings |
| 10 | Red teaming, evaluation & operations | ASR, utility under attack, coverage; AgentDojo, InjecAgent, τ-bench, Promptfoo, PyRIT, Garak; the CI gate; honeypots, canaries, kill switch, inventory, AIBOM |
| — | The script | The two-minute answer, a glossary, a worked threat model of an expense agent, likely interview questions |
| — | Attack catalog | Every attack on one table with vector, public example, impact, controls and OWASP mapping; a 2023–2026 timeline |
| — | Frameworks & checklist | OWASP LLM Top 10 (2025), OWASP Top 10 for Agentic Applications (Dec 2025), OWASP agentic threats T1–T15, MITRE ATLAS, NIST AI RMF, SAIF 2.0, MAESTRO, ISO 42001, EU AI Act; a 24-point pre-launch checklist; the autonomy ladder |

## Conventions

- Google Cloud names follow the 2026 naming: Gemini Enterprise Agent Platform (formerly Vertex AI Agent Builder), Agent Runtime (formerly Agent Engine), Agent Identity, Agent Gateway, Model Armor, IAP and Context-Aware Access for Agents. Statuses (GA / preview / announced) are as of the May 2026 announcements and will drift.
- Framework code follows Google ADK 1.x and LangChain / LangGraph 1.x as documented at the time; verify import paths and parameter names against current docs before running.
- Attack payloads are simplified from public advisories and research and are illustrative only; they are there to recognise the shape of an attack in a threat model, not to reproduce one.
- The page is a hosted Claude artifact as well; this file is the standalone copy for the repository.
