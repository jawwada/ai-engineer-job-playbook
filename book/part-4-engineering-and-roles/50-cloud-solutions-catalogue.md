# 50. Cloud solutions catalogue: core services across AWS, Azure and Google Cloud, and five reference architectures

> **What you need to be able to say:** the service for each need on each cloud, so you can follow any architecture conversation; and five reference architectures you can draw from memory. Chapter 15 covered the AI-specific services; this chapter covers the rest of the platform an AI system runs on.

## 50.1 Core services, side by side

| Need | AWS | Azure | Google Cloud |
|---|---|---|---|
| Accounts and org | Organizations, accounts, OUs, SCPs | Tenants, management groups, subscriptions, resource groups, Azure Policy | Organization, folders, projects, Org Policy |
| Identity | IAM (users, roles, policies), IAM Identity Center, Cognito (customer identity) | Entra ID (users, groups, managed identities, app registrations), Entra External ID | Cloud IAM, service accounts, Workload Identity, Identity Platform |
| Compute (VMs) | EC2 (Graviton ARM, GPU P/G instances), Auto Scaling | Virtual Machines, VM Scale Sets | Compute Engine, managed instance groups |
| Containers | ECS, EKS (Auto Mode), Fargate (App Runner closed to new customers in April 2026) | AKS (and AKS Automatic), Container Apps (serverless GPUs), Container Instances | GKE (Autopilot), Cloud Run (with GPUs) |
| Serverless functions | Lambda | Azure Functions | Cloud Run functions |
| Object storage | S3 (+ S3 Tables, Intelligent-Tiering, the Glacier storage classes) | Blob Storage / ADLS Gen2 (hot/cool/cold/archive) | Cloud Storage (standard/nearline/coldline/archive) |
| Block / file | EBS, EFS, FSx | Managed Disks, Azure Files, NetApp Files | Persistent Disk, Filestore |
| Relational DB | RDS, Aurora (Serverless v2), Aurora DSQL | Azure SQL, Database for PostgreSQL/MySQL | Cloud SQL, AlloyDB, Spanner |
| NoSQL | DynamoDB, DocumentDB, Keyspaces | Cosmos DB | Firestore, Bigtable |
| Cache | ElastiCache (Redis/Valkey), MemoryDB | Azure Cache for Redis / Managed Redis | Memorystore |
| Messaging | SQS, SNS, EventBridge, MSK (Kafka), Kinesis | Service Bus, Event Grid, Event Hubs | Pub/Sub, Eventarc |
| Workflow orchestration | Step Functions | Durable Functions, Logic Apps | Workflows |
| API management | API Gateway, AppSync (GraphQL) | API Management | Apigee, API Gateway |
| Load balancing / CDN / DNS | ELB (ALB/NLB), CloudFront, Route 53 | Load Balancer, Application Gateway, Front Door, Azure DNS | Cloud Load Balancing, Cloud CDN, Cloud DNS |
| Networking | VPC, subnets, security groups, Transit Gateway, PrivateLink | VNet, NSGs, Private Link, Virtual WAN | VPC, firewall rules, Private Service Connect, VPC Service Controls |
| Secrets and keys | Secrets Manager, Parameter Store, KMS | Key Vault | Secret Manager, Cloud KMS |
| Observability | CloudWatch (logs, metrics, traces), X-Ray, Managed Grafana/Prometheus | Azure Monitor, Application Insights, Log Analytics (KQL) | Cloud Monitoring, Cloud Logging, Cloud Trace |
| CI/CD | CodePipeline/CodeBuild/CodeDeploy (or GitHub Actions) | Azure DevOps Pipelines, GitHub Actions | Cloud Build, Cloud Deploy |
| IaC | CloudFormation, CDK | Bicep, ARM | Infrastructure Manager (Terraform-based); Deployment Manager reached end of support in April 2026 |
| Data warehouse / lake | Redshift, Athena, Glue, Lake Formation, SageMaker Lakehouse | Fabric (OneLake, Warehouse), Synapse (legacy direction), Data Factory | BigQuery, Knowledge Catalog (formerly Dataplex Universal Catalog), Dataflow, Dataproc |
| Streaming analytics | Managed Service for Apache Flink (formerly Kinesis Data Analytics) | Stream Analytics, Fabric RTI | Dataflow |
| ML platform | SageMaker AI (Unified Studio); note that Model Monitor, Clarify, Ground Truth, Debugger and A2I entered maintenance mode in July 2026 | Azure Machine Learning | the Vertex AI capabilities (pipelines, registry, endpoints, Model Garden), now under the Gemini Enterprise Agent Platform |
| GenAI platform | Bedrock, Bedrock AgentCore (Bedrock Agents is now "Agents Classic", in maintenance since July 2026) | Microsoft Foundry (renamed from Azure AI Foundry at Ignite, November 2025) and Foundry Agent Service | Gemini Enterprise Agent Platform (announced April 2026 as the evolution of Vertex AI: Agent Development Kit, Agent Runtime — formerly Agent Engine — Agent Garden, Model Garden) with Gemini Enterprise as the end-user layer |
| Security posture | GuardDuty, Security Hub, Inspector, WAF, Shield | Defender for Cloud, Sentinel, WAF | Security Command Center, Cloud Armor |
| Cost tools | Cost Explorer, Budgets, Data Exports (CUR 2.0, the successor to the legacy Cost and Usage Report) | Cost Management + Billing | Billing reports, budgets, BigQuery export |
| Edge/IoT | IoT Core, Greengrass (v2; v1 is sunset) | IoT Hub | (IoT via partners / Pub/Sub) |

**Critic's additions: lifecycle notes for late 2026.** Service names date fastest, and an interviewer notices a retired product in a design. Changes since 2025 that affect this table and the architectures below: Google Cloud Deployment Manager reached end of support on 1 April 2026 (shutdown 30 June 2027; use Infrastructure Manager); Google's Data Catalog was shut down on 1 June 2026 and Dataplex Universal Catalog was renamed Knowledge Catalog in April 2026; Vertex AI was folded into the Gemini Enterprise Agent Platform at Cloud Next in April 2026 (the APIs persist; the console, the umbrella brand and several product names changed — Vertex AI Search is now Agent Search and Vertex AI Pipelines is Agent Platform Pipelines); Azure AI Foundry became Microsoft Foundry in November 2025; LangGraph Platform became LangSmith Deployment in October 2025; AWS App Runner closed to new customers on 30 April 2026; Amazon Bedrock Agents became "Bedrock Agents Classic" in maintenance in July 2026 with AgentCore as the path forward; Amazon Kendra entered maintenance mode on 30 June 2026 and closed to new customers on 30 July 2026 (AWS points to the Bedrock Managed Knowledge Base), and Amazon Q Business is closed to new customers (AWS points to Amazon Quick); Databricks renamed Vector Search to AI Search on 1 June 2026 and made Unity Gateway, its governance gateway for models, agents and MCP servers that succeeded Mosaic AI Gateway, generally available on 4 August 2026; several SageMaker AI features (Model Monitor, Clarify, Ground Truth, Debugger, A2I, Studio Lab) entered maintenance in July 2026; the standalone Amazon Glacier service (vaults) entered maintenance in November 2025 while the S3 Glacier storage classes continue; Kinesis Data Analytics has been Amazon Managed Service for Apache Flink since 2023; and the Kubernetes community retired the Ingress NGINX controller in March 2026. "Maintenance" at AWS means existing customers keep using the service but new accounts cannot adopt it — which is exactly the situation an FDE walks into at a customer. Check the provider's "service availability" announcements before an interview at that provider.

## 50.2 Reference architecture 1 — Web application with an LLM feature

Users → CDN + WAF → load balancer → stateless API (containers on ECS/Cloud Run/Container Apps) → LLM gateway (LiteLLM/Portkey or the cloud's) → model API via private endpoint; Postgres for state; Redis for cache and rate limits; a queue (SQS/Pub/Sub/Service Bus) + workers for long jobs; object storage for files; secrets in a vault; OTel traces to the monitoring stack; CI/CD with eval gates; IaC. Scale by adding workers and caching; protect cost with routing and budgets.

**Critic's additions: architecture 1 mapped service by service, with a budget.**

| Component | AWS | Azure | Google Cloud |
|---|---|---|---|
| Edge | CloudFront + WAF + Route 53 | Front Door + WAF + Azure DNS | Cloud CDN + Cloud Armor + Cloud DNS |
| API containers | ECS on Fargate behind an ALB (or EKS) | Container Apps behind Application Gateway (or AKS) | Cloud Run behind a global HTTPS load balancer (or GKE) |
| LLM gateway | LiteLLM/Portkey on Fargate, or Bedrock with application inference profiles | API Management's AI gateway policies in front of Foundry model deployments | LiteLLM/Portkey on Cloud Run, or the Agent Platform's gateway in front of Gemini |
| Model access | Bedrock via VPC endpoint (PrivateLink) | Foundry via Private Link | Gemini API via Private Service Connect |
| State | Aurora PostgreSQL (Serverless v2) | Azure Database for PostgreSQL Flexible Server | Cloud SQL for PostgreSQL or AlloyDB |
| Cache and rate limits | ElastiCache (Valkey/Redis) | Azure Managed Redis | Memorystore |
| Queue and workers | SQS + Fargate workers (or Lambda) | Service Bus + Container Apps jobs (or Functions) | Pub/Sub + Cloud Run jobs (or Cloud Run functions) |
| Files | S3 | Blob Storage | Cloud Storage |
| Secrets | Secrets Manager | Key Vault | Secret Manager |
| Telemetry | OTel collector → CloudWatch / Managed Grafana (or a vendor) | OTel → Azure Monitor / Application Insights | OTel → Cloud Monitoring / Trace |
| Delivery | GitHub Actions with OIDC → ECR → ECS deploy with canary | GitHub Actions / Azure Pipelines → ACR → Container Apps revisions with traffic splitting | Cloud Build → Artifact Registry → Cloud Run revisions with traffic splitting |

The budget you should be able to recite: edge and load balancing under 20 ms, API work under 50 ms, retrieval or tool calls 100–300 ms, first token from the model 500–1,500 ms, full answer 2–6 s streamed; so the p95 target is 3–5 s and the design question is what runs in parallel. Cost per request for a typical assistant with a cached 4k-token system prompt, 2k tokens of context and 400 output tokens is of the order of a cent at mid-tier pricing and a few cents at frontier pricing; the infrastructure around it (containers, database, cache) is usually a few hundred dollars a month until traffic is large, which is why token cost dominates the FinOps conversation.

## 50.3 Reference architecture 2 — RAG platform

Connectors (SharePoint/Drive/S3/Confluence) → ingestion pipeline (parse, chunk, enrich, embed) on Spark/Lakeflow/Glue/Dataflow → lakehouse tables for documents/chunks with ACLs → vector + keyword index (OpenSearch/Azure AI Search/Agent Search, formerly Vertex AI Search/pgvector/Databricks AI Search, formerly Vector Search) → retrieval service with permission filters and reranking → generation service with citations and grounding checks → evaluation datasets and judges in CI → tracing and cost dashboards. Refresh event-driven; index versioned; ACL sync tested.

**Critic's additions: the numbers and the choices in architecture 2.** Sizing: 2M documents become roughly 40M chunks; at 1024 dimensions in float32 that is about 160 GB of vectors (40 GB with int8 quantization, 5 GB binary), plus the HNSW graph, which is why managed engines charge by memory and why quantization is the first lever. Latency budget per query: embed the question 30–80 ms, filtered vector plus keyword search 20–80 ms, rerank the top 20–50 candidates 100–300 ms, generation as in architecture 1 — the whole retrieval side fits in under half a second if the filters are applied before the approximate search. Engine choice by size and need: pgvector or the warehouse's native vector type for up to the low millions of vectors and simple filters; Azure AI Search, OpenSearch, Agent Search or Databricks AI Search when you need hybrid search with facets, ACL filtering at scale and managed refresh; a managed RAG service (Bedrock Knowledge Bases or the Bedrock Managed Knowledge Base, Foundry IQ on Azure AI Search's agentic retrieval, Agent Search) when time-to-first-demo matters more than control, with the caveat that the eval set decides whether its chunking and ranking are good enough for your jargon. Managed ingestion is a trade: fast to stand up, opaque when recall is poor; the escape hatch is to own the document and chunk tables in the lakehouse (chapter 48) and treat any engine as a derived store.

## 50.4 Reference architecture 3 — Agent platform

API/channels → agent runtime (AgentCore Runtime / Agent Runtime / Foundry Agent Service / LangSmith Deployment, formerly LangGraph Platform, on Kubernetes) with sessions and memory → tool gateway (MCP registry, auth, policy, rate limits) over enterprise APIs, databases (read replicas), search and code sandboxes → identity propagation (OBO) → guardrails service (input/tool/output) → human approval queues → observability (OTel GenAI) and evaluation service → FinOps attribution. Templates for supervisor, RAG and workflow agents; a review board for high-risk use cases.

## 50.5 Reference architecture 4 — ML training and serving platform

Lakehouse features → feature store → training on managed jobs (SageMaker/Gemini Enterprise Agent Platform/Azure ML/Databricks) with experiment tracking and registry → batch scoring to tables and online endpoints (autoscaled, canary) → monitoring (drift, performance) → retraining pipelines; GPU pools with spot for training and reserved for steady serving; model governance (cards, approvals, audit).

## 50.6 Reference architecture 5 — Contact center with AI agents

Telephony/chat (Connect / Dynamics 365 CC / Gemini Enterprise for Customer Experience, formerly CES) → bot layer (Lex / Copilot Studio / CX Agent Studio or legacy Dialogflow CX) with deterministic flows → LLM agent for open dialogue grounded in knowledge (Bedrock KB / Azure AI Search / Agent Search) and tools over CRM → agent assist for humans → analytics (Contact Lens / Insights) → QA judges on transcripts → compliance recording and retention.

## 50.7 Cross-cloud decision notes

- **Identity first.** Entra-centric organizations gravitate to Azure; AWS-native shops to IAM; Workspace shops to Google. Agents inherit this.
- **Data gravity second.** Put compute where the lake is; egress is expensive and slow.
- **Managed over self-run** until scale or policy forces otherwise; serverless for spiky and event-driven work.
- **Private networking** for model APIs in regulated environments (PrivateLink / Private Link / Private Service Connect).
- **One IaC language** per organization; policy as code; tags for cost.
- **Multi-cloud** is usually "one primary cloud plus a model provider abstraction", not symmetric deployments.

## 50.8 Example use cases (map to the architectures)

- Policy assistant for 20k employees → architecture 2 on the customer's cloud.
- Support agent with refunds → architecture 3 with a contact-center front door (5).
- Ranking service at 10K QPS → architecture 4 with online feature store and a serving mesh.
- Drive-through voice agent → architecture 5 with edge audio processing and POS integration.
- Marketing review platform → architecture 3 plus a knowledge graph store and a document pipeline from 2.
- Inventory copilot for a retailer → architecture 1 (web app with LLM feature) on top of 4 (forecast models) and 2 (reviews RAG).
