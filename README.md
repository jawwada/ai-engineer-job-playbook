# AI Engineer Job Playbook

A free, open book and toolkit for engineers who want to land — and do well in — **AI Engineer** and **Forward Deployed Engineer** roles. It has three parts:

1. **A Claude Code job-search agent** (`kit/`): skills, subagents, templates and scripts that turn Claude Code into an assistant that scouts fresh US AI roles, tailors your resume to each posting from a truth file, fills applications in your own browser with you approving every submission, keeps a tracker, and drafts recruiter replies in Gmail. Part 1 explains how to install and run it.
2. **A book** (`book/`): the agentic-AI landscape (clouds, models, JEPA and world models, frameworks, MCP, latent reasoning, RAG techniques and RAG evaluation, knowledge graphs, fine-tuning and distillation, evaluation, observability and the OpenTelemetry schema, security, FinOps), interview preparation (reading a job description, use-case thinking, STAR, coding patterns for LeetCode-style rounds, system design, the five role-related-knowledge topics in depth, conversational and voice AI), engineering and adjacent roles (DevOps, observability engineering with OpenTelemetry, Prometheus and the Grafana stack, MLOps, a complete cloud FinOps analyst track, data engineering, harnesses, guardrails, rogue agents, industrial challenges), and building a business with agents.
3. **Labs** (`labs/`): hands-on exercises that run on a laptop: tested templates for the coding-interview patterns (chapter 39d) and a FinOps analyst lab (chapter 47g).

> **Status:** work in progress — October 2026 snapshot. Chapters were drafted, then reviewed by adversarial editing agents that checked facts against official sources; product names and prices change monthly, so verify anything you will rely on. Nothing here is legal, financial or immigration advice.

## Quick start (the agent)

```bash
git clone https://github.com/jawwada/ai-engineer-job-playbook.git
cd ai-engineer-job-playbook
bash kit/install.sh          # skills + subagents into ~/.claude, workspace into ~/job-search
cd ~/job-search && claude --chrome
# inside Claude Code:
/job-setup                   # builds your truth file from your master resume
/job-scout                   # finds and scores fresh postings
```

Requirements: a Claude Pro, Max, Team or Enterprise plan (signed in with `/login`), the Claude in Chrome extension, Python 3.10+, LibreOffice and git. Details, Windows notes and the daily loop are in [Part 1](book/part-1-the-agent/01-what-youre-building.md) and [kit/README.md](kit/README.md).

## Read the whole book in one file

`python3 tools/build_book.py --html` writes `dist/ai-engineer-job-playbook.md` and a styled HTML version with a table of contents (needs pandoc for HTML). Reading paths are in [chapter 0](book/part-0-introduction/00-the-promise-of-agents.md).

## Contents

**Part 0 — Introduction**

- [0. The promise of agents: what is happening, who is winning, and how to read this book](book/part-0-introduction/00-the-promise-of-agents.md)

**Part 1 — The Claude Code job-search agent**

- [1. What you're building](book/part-1-the-agent/01-what-youre-building.md)
- [2. Before you start](book/part-1-the-agent/02-before-you-start.md)
- [3. Install the job-agent kit into Claude Code](book/part-1-the-agent/03-install-the-kit.md)
- [4. Connect Gmail](book/part-1-the-agent/04-connect-gmail.md)
- [5. Connect the browser: Claude in Chrome for LinkedIn, Dice and Indeed](book/part-1-the-agent/05-connect-the-browser.md)
- [6. Your truth file and master resume](book/part-1-the-agent/06-truth-file-and-master-resume.md)
- [7. Optimizing the resume for Forward Deployed Engineer and AI Engineer roles](book/part-1-the-agent/07-optimizing-the-resume.md)
- [8. The daily loop](book/part-1-the-agent/08-the-daily-loop.md)
- [9. Platform playbooks](book/part-1-the-agent/09-platform-playbooks.md)
- [10. Screening questions, US work authorization and rates](book/part-1-the-agent/10-screening-questions-and-rates.md)
- [11. Monitoring and staying connected](book/part-1-the-agent/11-monitoring-and-staying-connected.md)
- [12. Guardrails and platform risk](book/part-1-the-agent/12-guardrails-and-platform-risk.md)
- [13. Troubleshooting](book/part-1-the-agent/13-troubleshooting.md)

**Part 2 — The AI engineering landscape**

- [14. The AI engineering landscape: one map of everything](book/part-2-landscape/14-the-landscape-map.md)
- [15. Cloud AI platforms: AWS Bedrock and AgentCore, Microsoft Foundry, Google's Gemini Enterprise Agent Platform, and the Anthropic platform](book/part-2-landscape/15-cloud-ai-platforms.md)
- [16. The model landscape: frontier, open-weight, reasoning, small — and what tokens cost](book/part-2-landscape/16-the-model-landscape.md)
- [17. Beyond LLMs: the model families you will be asked about](book/part-2-landscape/17-beyond-llms-model-families.md)
- [17b. JEPA, world models and joint-embedding architectures in depth](book/part-2-landscape/17b-jepa-world-models-and-joint-embedding-architectures.md)
- [18. Embeddings and vector search](book/part-2-landscape/18-embeddings-and-vector-search.md)
- [19. Multimodality: what it is, how it works, when to use it](book/part-2-landscape/19-multimodality.md)
- [20. Agent frameworks: LangGraph, Claude Agent SDK, OpenAI Agents SDK, Google ADK, Strands, Microsoft Agent Framework, CrewAI, PydanticAI, LlamaIndex and friends](book/part-2-landscape/20-agent-frameworks.md)
- [20b. MCP in depth: what it is, why teams add it, real server examples, building and securing servers](book/part-2-landscape/20b-mcp-in-depth.md)
- [21. Databricks and the data-platform side: Unity Catalog, Mosaic AI, Agent Bricks, AI Search (formerly Vector Search), MLflow — plus Snowflake, Fabric and BigQuery](book/part-2-landscape/21-databricks-and-data-platforms.md)
- [22. Agentic design patterns](book/part-2-landscape/22-agentic-design-patterns.md)
- [22b. Self-improving agentic design, and the "deep agent" harness (LangChain Deep Agents, Claude Code and relatives)](book/part-2-landscape/22b-self-improving-agents-and-deep-agents.md)
- [22c. Latent reasoning in agents: thinking and communicating in hidden space](book/part-2-landscape/22c-latent-reasoning-in-agents.md)
- [23. Modern agentic AI applications: what they do and how they are built](book/part-2-landscape/23-modern-agentic-applications.md)
- [23b. Field notes from menuagentic.com: deciding axes, the 2026 incident record, and the controls they teach](book/part-2-landscape/23b-menuagentic-field-notes.md)
- [24. RAG: retrieval-augmented generation, from first principles to production](book/part-2-landscape/24-rag.md)
- [24b. Agentic RAG patterns and reranking solutions in depth](book/part-2-landscape/24b-agentic-rag-patterns-and-reranking.md)
- [24c. The RAG technique catalogue and RAG evaluation (RAGAS and friends)](book/part-2-landscape/24c-rag-techniques-catalogue-and-rag-evaluation.md)
- [25. Knowledge graphs: what they are, how to build them, and how they work with LLMs](book/part-2-landscape/25-knowledge-graphs.md)
- [26. Fine-tuning: SFT, LoRA/QLoRA, preference optimization, distillation — and when not to](book/part-2-landscape/26-fine-tuning.md)
- [26b. Post-training in depth: SFT, RLHF, DPO/GRPO, distillation and judges — with concrete setups](book/part-2-landscape/26b-post-training-in-depth.md)
- [26c. Distillation techniques in depth: from soft targets to on-policy distillation](book/part-2-landscape/26c-distillation-techniques-in-depth.md)
- [27. When to use what: prompting, RAG, knowledge graphs, fine-tuning, agents, multimodality — a decision guide with scenarios](book/part-2-landscape/27-when-to-use-what.md)
- [28. Conversational AI platforms: Google CX Agent Studio and Dialogflow CX, Amazon Lex and Connect, Microsoft Copilot Studio, Rasa and the voice stacks](book/part-2-landscape/28-conversational-ai-platforms.md)
- [28b. Cross-solution Rosetta stones: the same concept under every vendor's name](book/part-2-landscape/28b-cross-solution-rosetta-stones.md)
- [29. Observability and OpenTelemetry for LLM systems](book/part-2-landscape/29-observability-and-opentelemetry.md)
- [29b. Observability reference: definitions, the OpenTelemetry data model and schema, and the parameters that matter (latency, cost per span, cost per trace)](book/part-2-landscape/29b-observability-reference-definitions-otel-schema-and-cost.md)
- [30. Security, IAM and guardrails for LLM systems and agents](book/part-2-landscape/30-security-iam-and-guardrails.md)
- [31. FinOps for AI: token economics, cost levers and how to run a cost review](book/part-2-landscape/31-finops-and-token-economics.md)
- [32. Evaluation: building eval sets, LLM-as-a-judge, and quality gates](book/part-2-landscape/32-evaluation-and-llm-as-a-judge.md)
- [32b. Optimizing LLM-as-a-judge: accuracy, robustness, cost and statistical honesty](book/part-2-landscape/32b-optimizing-llm-as-a-judge.md)
- [33. Query languages an AI engineer meets: SQL, Spark/Databricks SQL, Cypher/GQL, SPARQL, Gremlin, GraphQL, KQL, PromQL/LogQL, Elasticsearch DSL, vector-store queries, and jq](book/part-2-landscape/33-query-languages.md)
- [34. Cloud free tiers and credits, and a practice-lab plan for each solution](book/part-2-landscape/34-cloud-free-tiers-and-practice-labs.md)

**Part 3 — Interviews**

- [35. Reading a job description: the problem behind the posting, and the interviewer's shoes](book/part-3-interviews/35-reading-a-job-description.md)
- [36. Use-case thinking: six use cases from one resume, worked from every angle](book/part-3-interviews/36-use-case-thinking.md)
- [37. Interview preparation: the process, the timeline, and arriving fresh](book/part-3-interviews/37-interview-preparation-and-staying-fresh.md)
- [38. The STAR method: drills, a story bank, and worked examples](book/part-3-interviews/38-star-method.md)
- [39. Technical interview topics with model answers](book/part-3-interviews/39-technical-interview-topics.md)
- [39b. The Applied AI / FDE role-related-knowledge interview (Google Cloud flavor): the five topics in depth](book/part-3-interviews/39b-applied-ai-fde-rrk-five-topics-in-depth.md)
- [39c. The role-related-knowledge interview, part two: Dialogflow CX background, the drive-through and prediction-market use cases, the Applied AI team context, and the communication playbook](book/part-3-interviews/39c-conversational-ai-background-and-use-cases-for-the-rrk.md)
- [39d. Coding interview patterns: the twenty LeetCode patterns, with tested templates and how to recognize them](book/part-3-interviews/39d-coding-interview-patterns.md)
- [40. AI system design: how to run the whiteboard, and eight worked exercises](book/part-3-interviews/40-ai-system-design-exercises.md)
- [41. Conversational AI in depth: Dialogflow CX, and designing a drive-through voice agent](book/part-3-interviews/41-conversational-ai-and-voice-agents.md)
- [42. Applied AI at prediction markets (Kalshi, Polymarket and peers): what the work is and how to interview for it](book/part-3-interviews/42-prediction-markets-applied-ai.md)
- [43. Question bank: 173 questions with short answers](book/part-3-interviews/43-question-bank.md)

**Part 4 — Engineering, roles and operating agents**

- [44. The roles map: AI Engineer, Forward Deployed Engineer, ML Engineer, MLOps, DevOps/Platform, Data Engineer, FinOps, SRE, Solutions Architect, Data Scientist](book/part-4-engineering-and-roles/44-roles-map.md)
- [45. DevOps and platform engineering for AI teams](book/part-4-engineering-and-roles/45-devops-and-platform-engineering.md)
- [45a. Observability engineering: the role, systems at scale, and SLAs that mean something](book/part-4-engineering-and-roles/45a-observability-engineering-role-slos-and-systems-at-scale.md)
- [45b. The open-source observability stack in depth: OpenTelemetry, Prometheus at scale, PromQL, Grafana, Loki, Tempo and Mimir](book/part-4-engineering-and-roles/45b-opentelemetry-prometheus-promql-and-the-lgtm-stack.md)
- [45c. AI for observability, and building and distributing AI skills that work](book/part-4-engineering-and-roles/45c-ai-for-observability-and-shipping-ai-skills.md)
- [46. MLOps and LLMOps: the lifecycle machinery](book/part-4-engineering-and-roles/46-mlops-and-llmops.md)
- [47. FinOps as a discipline: cloud and AI cost management](book/part-4-engineering-and-roles/47-finops-as-a-discipline.md)
- [47a. The cloud FinOps analyst: the role decoded, the finance vocabulary and the operating cadence](book/part-4-engineering-and-roles/47a-finops-analyst-role-finance-vocabulary-and-cadence.md)
- [47b. Multi-cloud billing data and native cost tools: AWS, Azure and Google Cloud, normalized with FOCUS](book/part-4-engineering-and-roles/47b-multi-cloud-billing-data-and-native-cost-tools.md)
- [47c. Forecasting, budgeting and variance analysis for multi-cloud spend](book/part-4-engineering-and-roles/47c-forecasting-budgeting-and-variance-analysis.md)
- [47d. Cost allocation, tagging and anomaly management](book/part-4-engineering-and-roles/47d-cost-allocation-tagging-and-anomaly-management.md)
- [47e. Commitments, usage optimization and realized savings](book/part-4-engineering-and-roles/47e-commitments-optimization-and-realized-savings.md)
- [47f. Executive reporting, stakeholder management and the FinOps analyst interview](book/part-4-engineering-and-roles/47f-executive-reporting-stakeholders-and-the-finops-interview.md)
- [47g. A hands-on FinOps analyst lab](book/part-4-engineering-and-roles/47g-finops-analyst-hands-on-lab.md)
- [48. Data engineering and pipelines](book/part-4-engineering-and-roles/48-data-engineering-and-pipelines.md)
- [49. Engineering fundamentals for AI engineers](book/part-4-engineering-and-roles/49-engineering-fundamentals.md)
- [50. Cloud solutions catalogue: core services across AWS, Azure and Google Cloud, and five reference architectures](book/part-4-engineering-and-roles/50-cloud-solutions-catalogue.md)
- [51. Architectural acumen: principles, trade-offs, organizing large unstructured datasets, metadata-rich RAG, and why knowledge graphs become necessary](book/part-4-engineering-and-roles/51-architectural-acumen.md)
- [52. Working with coding agents: writing better code, reviewing agent-written complexity, and how to argue for simplicity](book/part-4-engineering-and-roles/52-working-with-coding-agents.md)
- [52a. Harnesses: Claude Code and the other coding and agent harnesses](book/part-4-engineering-and-roles/52a-harnesses-claude-code-and-friends.md)
- [53. Adversarial thinking for agents, and evaluation strategies that actually catch failures](book/part-4-engineering-and-roles/53-adversarial-thinking-and-agent-evaluation.md)
- [53b. Enterprise guardrails: architecture, platforms, policy and governance](book/part-4-engineering-and-roles/53b-enterprise-guardrails.md)
- [53c. Self-improving agents, rogue agents and recursive agentic chains: failure modes and containment](book/part-4-engineering-and-roles/53c-self-improving-rogue-agents-and-recursive-chains.md)
- [54. Practical agent recipes with Claude: job applications, lead generation, motivated-seller finders, scrapers where browsers cannot go, and mixing determinism with non-determinism](book/part-4-engineering-and-roles/54-practical-agent-recipes-with-claude.md)
- [54b. Industrial challenges: why AI and agent projects stall between pilot and production, and how teams get through](book/part-4-engineering-and-roles/54b-industrial-challenges.md)

**Part 5 — The resume, glossary and portfolio**

- [55. Every concept on the reference resume, explained](book/part-5-your-resume/55-resume-concepts-explained.md)
- [56. Glossary](book/part-5-your-resume/56-glossary.md)
- [57. The GitHub portfolio: what to show, how to show it](book/part-5-your-resume/57-github-portfolio.md)

**Part 6 — Reference guides (study library)**

- [Study library index](book/part-6-reference-guides/README.md) — agentic AI, retrieval, LLMs, machine learning, clouds, Python and backend, industries, interview practice

**Part 7 — Building and earning**

- [58. Startup and side-business ideas: the ones already in the folder, and twenty more across domains](book/part-7-building-and-earning/58-startup-ideas.md)
- [59. How to make money with Claude: income playbooks for AI engineers](book/part-7-building-and-earning/59-how-to-make-money-with-claude.md)
- [60. Modern trends, skill libraries, tools and references: an intuitive map for 2026](book/part-7-building-and-earning/60-trends-skill-libraries-tools-and-references.md)
- [61. Successful startups in the domains on the resume: what they do and how they do it](book/part-7-building-and-earning/61-successful-startups-in-your-domains.md)
- [62. Research directions and innovation challenges: what is unsolved in agentic AI, and where builders can win](book/part-7-building-and-earning/62-research-directions-and-innovation-challenges.md)

**Labs:** [Coding-interview patterns](labs/coding-patterns/README.md) — tested templates for the twenty LeetCode patterns and the families beyond them, checked against brute force (chapter 39d); [FinOps analyst lab](labs/finops-analyst/README.md) — synthetic multi-cloud billing data with forecasting, variance, anomaly, allocation, commitment, savings and executive-summary exercises (chapter 47g). Both are standard-library Python.

**Glossary:** [GLOSSARY.md](GLOSSARY.md)

## Ground rules the agent follows

Never creates accounts, types passwords or solves CAPTCHAs; never edits your LinkedIn profile; never sends email (drafts only); never answers a screening question outside your truth file; never claims a skill, year or number your master resume does not support; respects daily caps and platform terms (it does not submit on Indeed, whose terms prohibit automating Indeed Apply). See [chapter 12](book/part-1-the-agent/12-guardrails-and-platform-risk.md).

## Contributing

Issues and pull requests are welcome: corrections with a source, new chapters, new skills. The `kit/agents/adversarial-reviewer.md` subagent is the same critic used to review this book — run it on your changes (`@"adversarial-reviewer (agent)" review book/part-2-landscape/24-rag.md`). After adding or renaming a chapter, run `python3 tools/update_readme_contents.py` to rebuild the contents list above, and `python3 tools/escape_dollars.py` so GitHub does not render prices as math.

## License

Text and diagrams: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — see [LICENSE-CONTENT.md](LICENSE-CONTENT.md). Code and its documentation in `kit/`, `tools/` and `labs/`: MIT — see [LICENSE](LICENSE). Third-party product names belong to their owners.
