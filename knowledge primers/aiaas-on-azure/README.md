# AI as a Service: concepts, architecture, and implementation on Azure

A 123-page deep-dive on **internal AI-as-a-Service enablement**: the shared AI services (model access, gateway, retrieval, agents, evaluation, governance) that a platform team builds so product teams can adopt generative AI safely and consistently in a regulated business. Part I and II are cloud-agnostic; Part III implements the same architecture on Azure with code; Part IV is interview material for a Senior Principal AIaaS-enablement role.

## Files

| File | What it is |
|---|---|
| `AI as a Service - Concepts, Architecture, and Implementation on Azure.md` | The article in Markdown, with the three diagrams linked from `images/` |
| `AI as a Service - Concepts, Architecture, and Implementation on Azure.pdf` | The same document as a 123-page US-letter PDF |
| `images/aiaas-reference-architecture.png` | The cloud-agnostic reference architecture for internal AIaaS |
| `images/aiaas-azure-reference-architecture.png` | The same architecture mapped onto Azure services |
| `images/aiaas-90-day-roadmap.png` | A 90-day enablement roadmap with gates |

## Contents

**Part I — Foundations.** 1. From AI projects to AI platforms. 2. What "AI as a Service" means. 3. The case for a platform.

**Part II — The core concepts of an AI platform.** 4. Abstraction and contracts: the model access layer. 5. The AI gateway as a control plane for every model call. 6. Retrieval as a service. 7. Agentic frameworks and orchestration. 8. Evaluation as a product. 9. Governance, safety and policy enforcement. 10. Multi-tenancy, identity and data isolation. 11. Observability, reliability and SLOs. 12. FinOps for AI. 13. Lifecycle management of models, prompts and change. 14. Developer experience and adoption. 15. A cloud-agnostic reference architecture. 16. Trade-offs and anti-patterns.

**Part III — Doing it on Azure.** 17. The Azure building blocks. 18. An Azure reference architecture for internal AIaaS. 19. The model access layer with Azure API Management (GenAI gateway policies: token limits and metrics, semantic caching, content safety, backend pools). 20. Retrieval with Azure AI Search, with a pgvector alternative. 21. Agents on Azure (Microsoft Foundry Agent Service, the Microsoft Agent Framework, MCP and A2A). 22. Evaluation, observability and safety on Azure. 23. Governance, identity and FinOps on Azure. 24. Infrastructure as code and CI/CD. 25. A 90-day enablement roadmap.

**Part IV — Interview talking points.** 26. How I would build this service on Azure. 27. My past experience in this light. 28. Likely probes, crisp answers, and questions to ask. Appendix: glossary and sources.

## How it was built

Written on 17 October 2026 as a Claude Doc from the Azure documentation for API Management's GenAI gateway capabilities, Microsoft Foundry and the Agent Service, Azure AI Search, the `azure-ai-evaluation` package, Content Safety, Defender for Cloud and Azure Policy, plus the author's platform experience (E.ON, Capital Group, a Kong-fronted model gateway, the Bedrock AgentCore stack). Azure service names and preview labels change monthly; the appendix lists the pages consulted with the as-of date.
