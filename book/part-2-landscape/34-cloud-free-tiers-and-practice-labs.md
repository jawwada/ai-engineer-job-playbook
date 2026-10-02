# 34. Cloud free tiers and credits, and a practice-lab plan for each solution

> **What you need to be able to say:** how to get hands-on on AWS, Azure, Google Cloud, Databricks and the model APIs without a bill; what the offers are (as of October 2026 — they change, so re-check the linked pages); how to keep the bill at zero; and a lab plan that turns each chapter of Part 2 into a repo you can talk about in an interview.

## 34.1 The offers (October 2026)

| Provider | What you get | How long | Card? | Notes |
|---|---|---|---|---|
| **AWS** (accounts created after 15 July 2025) | Free plan: $100 credit at sign-up plus up to $100 more for completing activities (launch EC2, set a budget, etc.), capped free-plan services; or Paid plan with the same credits and all services | 6 months or until credits run out; account closes after 6 months on the free plan unless upgraded (data deleted 90 days later) | yes | The old 12-month per-service free tier is gone for new accounts. Always-free: Lambda 1M requests + 400k GB-s/month, DynamoDB 25 GB, CloudFront 1 TB transfer/10M requests, S3 only via credits/limits — check the Free Tier page |
| **Azure** | $200 credit for 30 days, then 12 months of popular services free within limits (B1s VM hours, 250 GB SQL, 5 GB blob, etc.), plus always-free services (Functions 1M executions, App Service F1, Cosmos DB 1,000 RU/s + 25 GB, Azure AI services free tiers) | 30 days credit / 12 months limits / always-free | yes | Azure OpenAI/Foundry models are pay-as-you-go; the $200 covers a lot of tokens. Students: Azure for Students $100 without a card |
| **Google Cloud** | $300 credit for new customers plus the always-free tier (Cloud Run 2M requests/month, Firestore 1 GiB, e2-micro VM, 5 GB Cloud Storage in US regions, BigQuery 1 TB queries + 10 GB storage/month) | 90 days credit; free tier ongoing | yes | Nothing auto-upgrades to paid; you must activate billing. Gemini API also has a free tier with rate limits through AI Studio (free-tier prompts may be used to improve Google's products — never send real customer data through it). Agent Platform (formerly Vertex AI) usage draws on the $300 credit |
| **Databricks** | **Free Edition**: a free, limited workspace on serverless compute with notebooks, SQL, Lakeflow (Lakeflow Designer added in 2026), Unity Catalog, MLflow, model serving, vector search (AI Search) and agents for individuals | ongoing | no | Replaced Community Edition (June 2025); quotas apply (small serverless sizes, limited endpoints, no GPU training); perfect for the lakehouse and agent labs |
| **Snowflake** | 30-day trial with $400 credits | 30 days | no | enough for Cortex Search/Analyst labs |
| **Anthropic Claude** | Developer Platform is pay-as-you-go (prepaid credits; a few dollars goes far on Haiku); Claude Pro/Max subscriptions include Claude Code usage | — | yes | Claude is also usable via Bedrock, Vertex AI and Foundry credits |
| **OpenAI / Google Gemini API** | Pay-as-you-go; Gemini API free tier with daily limits via AI Studio | — | varies | |
| **Hugging Face** | free model/dataset hosting, free Spaces (CPU), Inference Providers with monthly free credits; Pro adds GPU and ZeroGPU | ongoing | no | host demos here |
| **GitHub** | free Actions minutes, Codespaces hours, GitHub Models playground; **Student Developer Pack** adds cloud credits (Azure, DigitalOcean, etc.) | ongoing | no | your portfolio lives here |
| **Oracle Cloud / IBM Cloud** | Oracle always-free (ARM VMs, 2 DBs); IBM Lite plans (40+ services, no expiry) and $200 PAYG credit | ongoing | varies | useful for always-on demos |
| **Kaggle / Colab** | free GPU/TPU notebook hours (Kaggle 30 h/week GPU; Colab free tier variable) | ongoing | no | fine-tuning labs with LoRA on 7–8B models |
| **Local** | Ollama / llama.cpp / LM Studio on your laptop; Apple-silicon or a 12–24 GB GPU runs 7–27B models at 4-bit | — | — | the cheapest way to practice serving |

Practical rules: one email per provider (aliases work), set a **budget alert at $1** the day you sign up (AWS Budgets, Azure Cost Management, GCP Budgets), tear down everything after a lab (`terraform destroy`; delete resource groups/projects), never leave a GPU VM, a provisioned vector index or a NAT gateway running overnight, and never put credentials in a repo (use the cloud CLI's login and `.env` files in `.gitignore`).

### Critic's additions: the services that quietly bill while idle

Budget alerts are delayed by hours, so know the usual culprits in AI labs before you create them (prices as of 2026 are approximate and regional — check the pricing page):

| Service | Why it bills when you are not using it | What to do |
|---|---|---|
| OpenSearch Serverless (often created by a Bedrock Knowledge Base quick-create) | minimum capacity units run continuously — historically on the order of $100+ a month even for a toy index | choose Aurora pgvector, S3 Vectors or a free-tier store for labs; delete the collection after |
| Azure AI Search above the Free tier | a Basic or Standard search unit bills per hour from creation | use the Free tier (limited indexes and storage) for labs |
| Vector Search endpoints and managed online endpoints (Vertex, Azure ML, SageMaker) | dedicated nodes bill per hour whether or not they serve traffic | undeploy the model and delete the index endpoint, not just the index |
| Provisioned throughput (Bedrock model units, Azure PTUs, Google Provisioned Throughput) | committed hourly or monthly capacity | never in a lab; use on-demand |
| NAT gateways and idle public IPv4 addresses | hourly charge plus data processing | private subnets only when the lab needs them; delete the VPC |
| GPU VMs and notebook instances | per-second billing continues while idle | auto-shutdown policies; stop, then delete |
| Agent runtimes with keep-warm or long session timeouts | session-hours accrue while a session stays open | short idle timeouts; end sessions in code |

## 34.2 The lab plan (one weekend each; every lab becomes a public repo)

Each lab has the same shape so the repos look like a series: a README with the problem, architecture diagram (Mermaid), setup, cost incurred, what you measured, and what you would do next; infrastructure as code where it fits; an eval set and results; a two-minute screen recording.

| # | Lab | Where | What you build | What you measure |
|---|---|---|---|---|
| 1 | RAG on AWS | Bedrock Knowledge Base on Aurora pgvector or S3 Vectors (OpenSearch Serverless works but has a standing minimum cost), Lambda + API Gateway, Guardrails | Q&A over 50 PDFs with citations and PII masking | recall@10, faithfulness, p95, cost/query |
| 2 | Agent on AWS | Strands agent with an MCP tool (weather or your own API), deployed on AgentCore Runtime with Memory, Identity (OAuth to a test API), Observability; then the same agent declared in AgentCore Harness for comparison | a support agent with two tools and long-term memory | task success on 30 tasks, tool-selection accuracy, cost/run; AgentCore Evaluations on the traces |
| 3 | RAG + agent on Azure | Azure AI Search (integrated vectorization) + Foundry Agent Service (file search, OpenAPI tool) with Content Safety and Prompt Shields, Entra ID auth | the same Q&A agent, Microsoft style | the same metrics; compare with lab 1 |
| 4 | Agent on Google Cloud | ADK agent with Vertex AI Search data store, deployed to Agent Engine with Sessions and Memory Bank; A2A agent card | the same agent, plus an A2A call from lab 2's agent | interoperability demo, latency |
| 5 | Voice agent | Dialogflow CX (Conversational Agents) with a playbook, a data store and a webhook to FastAPI on Cloud Run; or Amazon Connect + Lex + Nova Sonic | appointment rescheduling by voice | task completion, latency, fallback rate |
| 6 | Lakehouse + governed agent | Databricks Free Edition: Lakeflow pipeline → Delta tables → Vector Search → Agent Framework agent with UC Functions, MLflow tracing and Agent Evaluation | policy assistant with row-level permissions | eval judge scores, latency, cost |
| 7 | Knowledge graph | Neo4j AuraDB Free (or Neptune): LLM extraction → graph → text-to-Cypher agent + vector search (hybrid GraphRAG) | supplier-risk or compliance graph | question accuracy on 40 multi-hop questions |
| 8 | Fine-tuning | Colab/Kaggle: LoRA on a 3–8B open model for a classification or extraction task distilled from a frontier model; serve on vLLM locally or a HF endpoint | small-model replacement | F1 vs frontier, cost per 1k, latency |
| 9 | Evaluation + observability | Langfuse (self-host via Docker) or Phoenix + OpenTelemetry on labs 1–4; promptfoo/DeepEval in GitHub Actions | eval gates in CI with judges | agreement with your 50 human labels, regression catches |
| 10 | Multimodal document pipeline | Azure Document Intelligence or Google Document AI → extraction with a multimodal LLM → validation → review UI (Streamlit) | invoice/claims extraction | field accuracy, straight-through rate |
| 11 | Computer-use / browser agent | Claude Agent SDK or Claude in Chrome with Playwright MCP | the job-search agent in Part 1, or a form-filling bot | task success, steps, interventions |
| 12 | FinOps | a cost dashboard over labs 1–9 (OTel token attributes → Grafana), with caching and routing experiments | cost per task before/after | the −60% story for interviews |

Twelve labs is a quarter of weekends. Six are enough to change interviews: pick 1 or 3 (RAG on the cloud the target companies use), 2 or 4 (agent runtime), 6 (Databricks), 7 (graph), 9 (evals), and either 5 (voice) or 11 (browser agent) depending on the roles you want.

## 34.3 How to talk about labs in interviews

Lead with the problem and the numbers, not the stack: "I built a permission-aware policy assistant on Databricks Free Edition over 400 documents; recall@10 went from 0.62 to 0.88 after contextual chunking and reranking; p95 was 2.1 s; cost per query $0.004 on a mid-tier model; the eval set has 120 questions including 20 'no answer' cases, and the judge agreed with my labels 91% of the time." Then show the repo. A lab with measurements beats a certificate; a certificate plus a lab beats both.

## 34.4 Certifications (worth it when the JD names them)

AWS Certified AI Practitioner, Machine Learning Engineer – Associate, and the newer **Generative AI Developer – Professional** (AIP-C01; beta ran to March 2026 — Bedrock, knowledge bases, agents, evaluation, security; check GA status); Microsoft **Azure AI Apps and Agents Developer Associate (AI-103)**, which replaced the Azure AI Engineer Associate exam AI-102 when AI-102 retired on 30 June 2026 (verify on Microsoft Learn — older study guides and JDs still say AI-102); Google Professional Machine Learning Engineer, and Generative AI Leader for business-facing roles; Databricks Generative AI Engineer Associate; Neo4j Certified Professional / Graph Data Science; Kubernetes CKAD if the role is platform-heavy. Study them with the labs above, not instead of them.
