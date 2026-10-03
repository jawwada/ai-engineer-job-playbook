# 30. Security, IAM and guardrails for LLM systems and agents

> **What you need to be able to say:** the threat model for LLM apps (OWASP Top 10 for LLM Applications, MITRE ATLAS); how to limit what an agent can see and do (identity propagation, least privilege, authorization at the data layer, tool allow-lists); prompt-injection defenses; data protection (PII, secrets, retention); and how the clouds package this. Chapter 39 answers "limit an agent to certain data" as an interview question.

## 30.1 Threat model

OWASP's Top 10 for LLM applications names the recurring risks. The 2025 edition listed **prompt injection** (direct and indirect — instructions hidden in a web page, email or document the agent reads), **sensitive information disclosure**, **supply chain** (models, adapters, datasets, MCP servers), **data and model poisoning**, **improper output handling** (model output executed as code/SQL/HTML), **excessive agency** (too many tools, too much permission, too little oversight), **system prompt leakage**, **vector and embedding weaknesses** (poisoned or over-permissive indexes), **misinformation**, and **unbounded consumption** (cost and denial of service). The **2026 edition** (posted on genai.owasp.org on 3 August 2026 and formally announced on 1 September 2026; ranked partly on an analysis of 6,639 real-world incidents alongside practitioner voting) keeps prompt injection at LLM01 and sensitive information disclosure at LLM02, moves **excessive agency up to LLM03** (from sixth), and replaces system prompt leakage with **hidden context exposure** (LLM08) — the confidentiality of everything in the context window, including retrieved documents, agent memory, tool responses and application state; the published order is LLM01 prompt injection, LLM02 sensitive information disclosure, LLM03 excessive agency, LLM04 supply chain, LLM05 data and model poisoning, LLM06 unbounded consumption, LLM07 misinformation, LLM08 hidden context exposure, LLM09 vector and embedding weaknesses, LLM10 improper output handling (order checked against the published PDF in October 2026; identifiers carry the year, LLM03:2026, so say which edition you mean). Its companion, the **OWASP Top 10 for Agentic Applications for 2026** (published 9 December 2025 — a separate list, not the LLM Top 10's 2026 edition), is the list to cite for agents: ASI01 agent goal hijack, ASI02 tool misuse and exploitation, ASI03 identity and privilege abuse, ASI04 agentic supply-chain vulnerabilities, ASI05 unexpected code execution, ASI06 memory and context poisoning, ASI07 insecure inter-agent communication, ASI08 cascading failures, ASI09 human-agent trust exploitation, ASI10 rogue agents. MITRE ATLAS catalogs attack techniques against ML systems. For agents, the sharp end is the combination: indirect injection + excessive agency + a tool with write access — Simon Willison's "lethal trifecta" names the exfiltration version precisely: an agent that has access to private data, is exposed to untrusted content, and can communicate externally can be made to leak the data, and the only robust fix is to remove one of the three legs for that agent.

## 30.2 Identity: who is the agent?

The single most important design decision: **the agent acts as the user, not as a god-mode service account.** Patterns:

- **On-behalf-of (OBO) token exchange**: the user's OAuth token is exchanged for a scoped token the agent presents to tools (AgentCore Identity, Entra ID OBO flow, Google's Agent Identity); the data layer applies the user's permissions.
- **Workload identity for the agent itself** (IAM roles, Entra managed identities, GCP service accounts, SPIFFE/SPIRE) with least privilege for infrastructure access only.
- **Per-tool credentials** stored in a vault (AWS Secrets Manager, Key Vault, Secret Manager, HashiCorp Vault), never in prompts or context; tools receive credentials from the runtime, not from the model.
- **MCP auth**: remote MCP servers use OAuth 2.1 (authorization code with PKCE, resource indicators so a token is minted for one specific server, protected-resource metadata for discovery, Client ID Metadata Documents for client registration, and per-operation step-up scopes); gateways (AgentCore Gateway, Foundry, Apigee/Kong) centralize token handling and audit. Three rules from the MCP security best practices are worth quoting: servers **must not** accept tokens that were not issued for them, which forbids "token passthrough" of the user's upstream token to a downstream API (the confused-deputy and audit-trail problem); proxy servers that front a third-party API with a static client ID **must** collect per-client consent before forwarding, or a malicious client can ride an existing consent cookie; and clients fetching OAuth metadata URLs supplied by a server should block private and link-local ranges (the cloud metadata endpoint at 169.254.169.254 is the classic SSRF target).
- **Human approval** for high-impact actions as a policy, enforced by the runtime (not only by prompt): AgentCore Policy, LangGraph interrupts, Claude Agent SDK permission modes and hooks, Foundry Agent Service approvals.

## 30.3 Authorization: limiting what the agent can see

Apply permissions **where the data lives**, not in the prompt:

1. **Row-level security and column masking** in the warehouse/lakehouse (Unity Catalog row filters and column masks, Snowflake row-access and masking policies, Postgres RLS, BigQuery authorized views and policy tags, Fabric/OneLake security roles).
2. **Document ACLs carried into the index**: each chunk's metadata holds the allowed principals/groups from the source system (SharePoint, Confluence, Drive); retrieval filters by the caller's groups (Azure AI Search security trimming, Google Agent Search ACLs — formerly Vertex AI Search — Bedrock KB metadata filters, Glean-style permission sync). Test with negative cases: a user who must *not* see a document must not see it in any answer. Two traps: ACLs change after indexing (a revoked user still matches until the next sync, so define and monitor the sync lag), and some managed indexes cannot inherit warehouse row security at all — Databricks documents that an AI Search (formerly Vector Search) index cannot be built from a table with row filters or column masks, so the ACL must be an explicit column filtered at query time (chapter 21).
3. **Tool-level authorization**: allow-lists per agent and per user role; argument constraints (this agent may call `refund(amount ≤ 100)`); externalized policy engines (Cedar via Amazon Verified Permissions, OpenFGA/Zanzibar-style relationship authorization, Oso, OPA) evaluated by the gateway before the tool runs.
4. **Scoped data access tools**: give the agent a `query_customer(customer_id)` tool that enforces tenancy inside, not a raw SQL tool.
5. **Separate indexes/tenants** when regulations require hard isolation (per-customer vector collections, separate projects/accounts).
6. **Audit**: every tool call logged with the principal, arguments and result (chapter 29).

For the protocols underneath these patterns (OAuth 2.0 flows, OpenID Connect, PKCE, JWT validation, SAML and SCIM, mutual TLS), see chapter 49b.

## 30.4 Prompt injection and output handling

- Treat **all tool output and retrieved content as untrusted data**; never let it change the agent's goals. Mark it in the prompt as data; use models trained with instruction hierarchy; keep instructions in the system prompt; strip or quarantine instructions found in content.
- **Classifiers** on inputs and on retrieved/tool content: Azure Prompt Shields, Bedrock Guardrails prompt-attack filter, Google Model Armor, Lakera Guard, Llama Prompt Guard, NeMo Guardrails rails.
- **Least privilege** limits the blast radius when injection succeeds; **egress control** (no arbitrary URLs, allow-listed domains for fetch and for sending) prevents exfiltration; **no secrets in context**.
- **Output handling**: validate structured outputs against schemas; never execute model output directly (parameterized queries, sandboxed code execution with no network, HTML escaping); grounding checks and policy filters before display.
- **Human approval for outbound actions** (email, payments, posting, deletes) — the rule this book's job agent lives by.

### Critic's additions: architectural defenses that do not depend on the model behaving

Classifiers lower the success rate of injection; they do not bound it, and adaptive attackers routinely get past published detectors. The defenses that hold are architectural: once an agent has ingested untrusted input, it must be *impossible* for that input to trigger a consequential action. The 2025 paper "Design Patterns for Securing LLM Agents against Prompt Injections" (authors from IBM, Invariant Labs, ETH Zurich, Google and Microsoft) gives six patterns worth naming:

| Pattern | How it works | Typical use |
|---|---|---|
| Action-selector | the model only picks from a fixed menu of actions and never sees tool output afterwards | customer-service bots that route to predefined flows |
| Plan-then-execute | the plan (which tools, in what order) is fixed before any untrusted content is read; content can change data, not control flow | email or calendar assistants |
| LLM map-reduce | each untrusted item is processed by an isolated sub-agent whose output is constrained (a boolean, a category, a number) before aggregation | screening many documents or reviews |
| Dual LLM | a privileged model plans and calls tools but only ever sees symbolic references to untrusted data; a quarantined model reads the data and has no tools | assistants that summarize untrusted content and act on it |
| Code-then-execute | the model writes a program up front; an interpreter tracks data flow so untrusted values cannot reach sensitive sinks (Google DeepMind's CaMeL is the research example) | multi-step workflows over sensitive data |
| Context-minimization | remove the user's original prompt (or other untrusted text) from context before later steps | query-to-database flows where the result, not the prompt, drives the answer |

Each pattern trades capability for safety, which is the honest framing for an interview: a fully general agent that reads the web and holds write credentials cannot be made injection-proof today, so you either narrow its capabilities, split it into privileged and quarantined parts, or put a human on every consequential action.

## 30.5 Data protection and compliance

- **PII**: detect and redact in prompts, logs and traces (Presidio, Amazon Comprehend, Google DLP, Azure PII detection); minimize what the model sees; tokenization/pseudonymization for identifiers.
- **Retention and residency**: configure zero-retention or short retention with vendors where available; choose regions; know each provider's training-data policy (enterprise APIs do not train on your data by default — verify in the contract).
- **Regulations**: GDPR (lawful basis, minimization, right to erasure — memory stores must support deletion), HIPAA (BAAs with vendors, PHI handling), SOC 2/ISO 27001 and ISO/IEC 42001 (the AI management-system standard, increasingly requested in procurement), the EU AI Act (risk categories, transparency), sector rules (FINRA/SEC for marketing communications, PCI for payments). EU AI Act timing, as of 2026 (verify — this moved during 2026): prohibited practices have applied since 2 February 2025 and general-purpose AI model obligations since 2 August 2025; the Article 50 transparency duties (telling people they are talking to an AI, marking synthetic content) applied on 2 August 2026; and the "Digital Omnibus" amendment adopted in July 2026 deferred the high-risk obligations — to 2 December 2027 for stand-alone Annex III systems (employment, credit, education and similar) and to 2 August 2028 for AI embedded in regulated products.
- **Model and supply chain**: pin model versions; verify open-weight checksums and licenses; scan adapters and datasets; vet MCP servers (prefer signed/registry-listed; AgentCore Registry, Docker MCP catalog); SBOMs for agents.
- **Content safety**: harmful-content filters (Bedrock Guardrails, Azure Content Safety, Google safety settings, OpenAI moderation, Llama Guard) tuned to the use case; red teaming with PyRIT, garak, promptfoo; incident response playbooks for AI failures.

## 30.6 How the clouds package it

- **AWS**: IAM, VPC endpoints/PrivateLink for Bedrock, KMS, CloudTrail; Bedrock Guardrails (content, PII, grounding, automated reasoning checks), which since June 2026 (AWS announcement of 17 June) can also run inside AgentCore Policy at the gateway, outside the agent's code; AgentCore Identity (OAuth vault, OBO token exchange since April 2026), Gateway (auth, rate limits), Policy (Cedar or natural-language rules evaluated on every tool call), AWS Agent Registry; Verified Permissions (Cedar).
- **Azure**: Entra ID (Entra Agent ID for durable agent identities, OBO, conditional access), Private Link, Key Vault; Azure AI Content Safety, Prompt Shields, groundedness detection; Purview for data classification and DLP; Defender for AI; Agent 365 and the Foundry Control Plane for fleet-level governance.
- **Google Cloud**: Cloud IAM, VPC Service Controls, CMEK; Model Armor (injection, sensitive data, URL checks); Agent Identity, Agent Gateway and Agent Registry in the Gemini Enterprise Agent Platform, with agent threat and anomaly detection; Sensitive Data Protection; Security Command Center AI protection.
- **Databricks**: Unity Catalog permissions govern tables, functions and agents (with on-behalf-of-user auth on serving endpoints), but vector indexes need explicit ACL columns because they cannot be built on row-filtered tables; Unity Gateway (GA 4 August 2026) for guardrails, spend caps, rate limits and payload logging across models, agents and MCP servers; secrets; serverless network policies.

## 30.7 Scenarios

- **An HR assistant must answer policy questions and look up an employee's own leave balance, never anyone else's.** OBO identity; the leave tool takes no employee-id argument and resolves the caller internally; policy docs retrieved with ACL filters; injection classifier on uploaded documents; audit per call; negative tests in CI.
- **A procurement agent reads supplier emails and drafts purchase orders.** Emails are untrusted content; the agent has read-only tools plus a `draft_po` tool; a human approves; egress limited to the ERP; PII redaction in traces.
- **A multi-tenant SaaS RAG product.** Tenant id enforced at the gateway and in every index filter and SQL policy; per-tenant encryption keys where contracts demand; tenancy tests run on every deploy; prompt-injection red-team suite in CI.
- **A trading-desk research agent at a prediction market.** Read-only market data and news tools; no order-placement tool at all in the research agent; separate, heavily gated execution service with hard limits; full audit for compliance.

**Interview line:** *"The agent acts as the user through on-behalf-of tokens, permissions are enforced where the data lives — row filters, ACL-filtered retrieval, scoped tools — a policy engine gates tool calls, everything the agent reads is untrusted, outbound actions need approval, and every call is audited. Guardrails on top, not instead."*
