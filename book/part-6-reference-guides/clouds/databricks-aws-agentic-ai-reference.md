# Databricks + AWS + Agentic AI — Complete Reference Guide

> Prepared for interview prep: **Senior ML Engineer / Data Scientist — Agentic AI**
> Covers every technology and concept mentioned in a typical asset-management AI engineering JD.

---

## 1. Databricks — What It Is

Databricks is a unified analytics and AI platform built on top of Apache Spark. It was founded by the creators of Spark, Delta Lake, and MLflow. The core idea: one platform for data engineering, data science, ML, and now GenAI — eliminating the need to stitch together separate tools.

Databricks runs **on top of** your cloud provider (AWS, Azure, or GCP). It doesn't have its own data centers. When you spin up a Databricks workspace on AWS, behind the scenes it's provisioning EC2 instances, using S3 for storage, and managing networking via your AWS account.

### The Lakehouse Architecture

Databricks popularized the "lakehouse" — a hybrid of data lake (cheap, scalable, raw storage on S3) and data warehouse (structured, queryable, ACID-compliant). The key enabling tech is **Delta Lake**, an open-source storage layer that adds reliability (ACID transactions, schema enforcement, time travel) to data lakes.

**Before the lakehouse:** You'd have a data lake (S3 with Parquet files, messy, no transactions) + a separate data warehouse (Redshift/Snowflake, structured but expensive, data duplication). The lakehouse merges these — one copy of data, with both the flexibility of a lake and the governance of a warehouse.

---

## 2. Databricks Core Services (In Detail)

### 2.1 Apache Spark (Compute Engine)

Spark is the distributed compute engine underneath Databricks. When you run a query or train a model, Spark splits the work across a cluster of machines.

**Key concepts:**
- **Driver + Executors**: The driver is the coordinator; executors are worker nodes doing the actual computation
- **DataFrames / SparkSQL**: The two main APIs for working with data — DataFrames are programmatic (Python/Scala), SparkSQL is SQL queries over the same data
- **Lazy evaluation**: Spark builds a DAG (directed acyclic graph) of transformations, then optimizes and executes only when you trigger an action (`.collect()`, `.write()`, `.count()`)
- **Partitioning**: Data is split across nodes. Good partitioning = fast queries. Bad partitioning = data skew and slow jobs
- **Shuffle**: When Spark needs to rearrange data across nodes (joins, group-bys), that's a shuffle — expensive in network I/O and often the bottleneck

**In the context of this role:** You'd use Spark for large-scale data processing — feature engineering, preprocessing training data, running batch inference, ETL pipelines that feed ML models.

### 2.2 Delta Lake (Storage Layer)

Delta Lake sits between Spark and the raw files on S3. It stores data as Parquet files but adds a transaction log (`_delta_log/`) that tracks every change.

**What it gives you:**
- **ACID transactions**: Multiple writers can't corrupt data; reads are consistent
- **Time travel**: Query data as it existed at any previous point (`SELECT * FROM table VERSION AS OF 5` or `TIMESTAMP AS OF '2025-01-01'`)
- **Schema enforcement**: Rejects writes that don't match the expected schema
- **Schema evolution**: Lets you add columns over time without breaking existing queries
- **MERGE (upsert)**: Efficiently update/insert/delete rows — critical for slowly changing dimensions and CDC pipelines
- **Z-ordering**: A data layout optimization that co-locates related data on disk, speeding up queries that filter on specific columns
- **Liquid clustering**: A newer, adaptive replacement for Z-ordering that automatically manages data layout

**In the context of this role:** Your feature stores, training datasets, model artifacts, and governance audit trails would all sit in Delta tables.

### 2.3 Unity Catalog (Governance)

Unity Catalog is Databricks' centralized governance layer. It provides a three-level namespace: **catalog → schema → table/view/model/function**.

**What it does:**
- **Centralized access control**: Fine-grained permissions (row-level, column-level) on tables, models, and functions across all workspaces
- **Data lineage**: Automatically tracks which tables, columns, and notebooks produced a given dataset — visual lineage graphs showing upstream/downstream dependencies
- **Audit logging**: Who accessed what, when, from which notebook or job
- **Data discovery**: Searchable catalog of all data assets, with tags, descriptions, and owners
- **Model governance**: MLflow models registered in Unity Catalog get the same access controls and lineage as data tables
- **Delta Sharing**: Securely share data with external organizations without copying it

**Why this matters for the JD:** The role explicitly calls for "data governance tools and practices such as Unity Catalog, data lineage, access controls, and audit trails." In a regulated financial firm, governance isn't optional — regulators require you to prove who had access to what data, how models were trained, and what data lineage exists.

### 2.4 MLflow (ML Lifecycle Management)

MLflow is an open-source platform (originally built by Databricks, now widely used outside it too) for managing the full ML lifecycle.

**Four components:**

1. **MLflow Tracking**: Log experiments — parameters, metrics, artifacts (model files, plots). Every training run gets a unique ID. You can compare runs side-by-side.
   ```python
   with mlflow.start_run():
       mlflow.log_param("learning_rate", 0.01)
       mlflow.log_metric("f1_score", 0.87)
       mlflow.sklearn.log_model(model, "model")
   ```

2. **MLflow Models**: A standard format for packaging models so they can be served anywhere — as a REST API, a batch Spark job, or an edge deployment. Supports "flavors" (sklearn, pytorch, transformers, langchain, etc.)

3. **Model Registry**: A centralized model store with versioning and stage transitions (None → Staging → Production → Archived). In Unity Catalog, models are registered as `catalog.schema.model_name` and inherit governance.

4. **MLflow Evaluate**: Evaluate LLM and traditional ML model quality — includes built-in metrics for toxicity, relevance, faithfulness (for RAG), plus custom evaluators.

**In the context of this role:** You'd use MLflow to track experiments, register production models, set up evaluation harnesses for agents, and maintain model lineage for audit.

### 2.5 Databricks Model Serving

Databricks can host models behind REST endpoints — you register a model in MLflow/Unity Catalog and deploy it as a serverless endpoint.

**Types:**
- **Custom model serving**: Your own trained models (sklearn, PyTorch, etc.)
- **Foundation model APIs**: Access to hosted LLMs (DBRX, Llama, Mistral, etc.) via pay-per-token endpoints
- **External model endpoints**: Proxy to external APIs (OpenAI, Anthropic) with centralized governance, rate limiting, and cost tracking through Databricks
- **Feature serving**: Serve real-time features from Databricks Feature Store

**Why this matters:** The role involves "scalable inference pipelines" — Model Serving is how you expose ML/LLM capabilities as APIs consumed by downstream products.

### 2.6 Databricks Workflows (Orchestration)

Workflows is the native job orchestrator — schedule and run notebooks, Python scripts, JARs, SQL queries, and dbt models as multi-step DAGs.

**Key features:**
- Task dependencies (run task B only after task A succeeds)
- Parameterized runs
- Retry logic
- Alerts on failure
- Cluster policies (control cost by capping what clusters jobs can use)

**Alternative:** Many teams use Airflow (Amazon MWAA on AWS) or Prefect for orchestration and trigger Databricks jobs externally.

### 2.7 Databricks SQL (SQL Warehouse)

A SQL-native query engine for analysts and BI tools. It's Spark under the hood, but optimized for low-latency SQL queries on Delta tables.

**Use case:** Business analysts query data through BI tools (Tableau, Power BI, Looker) connected to a SQL Warehouse — they don't need to know Spark or Python.

### 2.8 Mosaic AI (GenAI / Agent Framework)

Databricks' GenAI product suite, added through the Mosaic ML acquisition:

- **AI Playground**: A UI for testing prompts against different LLMs
- **AI Gateway**: Centralized proxy for LLM API calls — rate limiting, cost tracking, governance
- **Agent Framework**: Tools for building, evaluating, and deploying compound AI systems (agents)
  - Build agents using LangChain, LlamaIndex, or raw Python
  - Evaluate with MLflow Evaluate (custom metrics, human-in-the-loop review)
  - Deploy agents as Model Serving endpoints
  - **Agent Evaluation**: Specialized tooling for measuring agent quality — correctness, groundedness, tool-use accuracy, latency

---

## 3. How Databricks Runs on AWS

Databricks on AWS is a **control plane + data plane** architecture:

### Control Plane (Managed by Databricks)
Lives in Databricks' own AWS account. Handles:
- Workspace UI (the notebooks, job scheduler, dashboards you see in browser)
- Cluster management (decides when to spin up/down EC2 instances)
- Metadata (Unity Catalog, MLflow tracking server, job definitions)

### Data Plane (Your AWS Account)
This is where the actual compute and data live:
- **EC2 instances**: The cluster nodes running Spark, model training, inference
- **S3 buckets**: Where all your data lives (Delta tables, raw files, model artifacts)
- **VPC**: Network isolation — your Databricks clusters run inside your VPC
- **IAM roles**: Control what Databricks can access in your AWS account

### The Key AWS Services Involved

| AWS Service | Role in the Databricks Stack |
|---|---|
| **EC2** | Compute nodes for Spark clusters, model training, inference |
| **S3** | All data storage — Delta tables, checkpoints, model artifacts, logs |
| **IAM** | Authentication/authorization — instance profiles, cross-account roles |
| **VPC** | Network isolation, security groups, private endpoints |
| **KMS** | Encryption keys for data at rest |
| **CloudFormation / Terraform** | Infrastructure as Code to provision the Databricks workspace |
| **CloudWatch** | Monitoring, logs, alerts for the underlying infrastructure |
| **STS** | Temporary credentials for cross-account access |

### What "Infrastructure as Code" Means Here

The JD says "use Infrastructure as Code to provision and manage cloud-native, scalable, and secure environments." In practice this means:

- **Terraform** (most common): Databricks provides an official Terraform provider. You define your workspaces, clusters, jobs, Unity Catalog objects, and permissions as `.tf` files. Changes are version-controlled and applied via `terraform apply`.
- **CloudFormation**: AWS-native IaC. Can provision the underlying AWS resources (VPC, S3, IAM) that Databricks needs.
- **Databricks Asset Bundles (DABs)**: A newer Databricks-native tool for packaging and deploying jobs, pipelines, and ML projects as code.

---

## 4. AWS Services for AI Applications (Beyond Databricks)

The JD mentions several data stores and AWS services that sit alongside Databricks:

### 4.1 Vector Stores

**What they are:** Databases optimized for storing and searching high-dimensional embedding vectors. When you embed text/images into vectors (using models like `text-embedding-3-small`), you need to search for "nearest neighbors" — vector stores do this efficiently.

**Options on AWS:**
- **Amazon OpenSearch** with vector search (k-NN plugin)
- **Amazon Aurora / RDS** with pgvector extension (PostgreSQL-based)
- **Pinecone, Weaviate, Qdrant** (third-party managed services)
- **Databricks Vector Search**: Native to Databricks, indexes Delta tables as vector stores — auto-syncs when the underlying table updates

**In the context of this role:** Vector stores power RAG (Retrieval-Augmented Generation). When an agent needs to answer a question, it embeds the query, searches the vector store for relevant documents, and passes them to the LLM as context.

### 4.2 Graph Databases

**What they are:** Databases that store data as nodes and relationships. Great for knowledge graphs, entity relationships, fraud detection, and network analysis.

**Options on AWS:**
- **Amazon Neptune**: AWS-managed graph database (supports both property graphs via Gremlin/openCypher and RDF via SPARQL)
- **Neo4j on AWS** (self-hosted or AuraDB managed)

**In the context of this role:** GraphRAG — combining knowledge graphs with RAG for more structured, relationship-aware retrieval. An agent that needs to understand "who reports to whom" or "which products are related" benefits from a graph structure.

### 4.3 Redis (ElastiCache for Redis)

**What it is:** An in-memory key-value store. Extremely fast (sub-millisecond latency).

**Uses in AI systems:**
- **Caching**: Cache LLM responses for repeated queries (saves cost and latency)
- **Session/conversation memory**: Store chat history for multi-turn agents
- **Rate limiting**: Track API usage per user
- **Feature store**: Serve pre-computed features for real-time inference
- **Pub/sub**: Event-driven messaging between services

**ElastiCache** is the AWS-managed version — you get Redis without managing the infrastructure.

### 4.4 DynamoDB

**What it is:** AWS's fully managed NoSQL key-value / document database. Scales to virtually unlimited throughput with single-digit millisecond latency.

**Uses in AI systems:**
- **Agent state persistence**: Store tool results, intermediate reasoning, execution plans
- **Metadata storage**: Track which documents have been indexed, user preferences, configuration
- **Session management**: Conversation history, user authentication tokens
- **Event sourcing**: Immutable log of every action an agent took (audit trail)

**DynamoDB vs Redis:** DynamoDB is durable (data persists on disk, replicated), Redis is faster but volatile by default. Use DynamoDB for data you can't afford to lose; Redis for data you can recompute.

### 4.5 Amazon SageMaker (Complementary, Not Mentioned but Relevant)

SageMaker is AWS's ML platform — competes with Databricks ML to some extent. Some teams use both: Databricks for data engineering + feature engineering, SageMaker for model training + deployment. The example employer appears to be Databricks-first based on its JD.

---

## 5. Agentic AI Architecture — The Core of This Role

This is the most forward-looking part of the JD. Here's the full picture:

### 5.1 What Is an "Agent"?

An agent is an LLM that can take actions — not just generate text. It observes its environment, reasons about what to do, uses tools, evaluates results, and iterates.

**Simple LLM call:**
```
User → LLM → Response
```

**Agent:**
```
User → LLM (reasons about the task)
         → Calls Tool A (e.g., search database)
         → Observes result
         → Calls Tool B (e.g., run calculation)
         → Observes result
         → Synthesizes final answer
         → Response
```

### 5.2 Key Agent Patterns

**ReAct (Reasoning + Acting):** The agent alternates between thinking ("I need to look up X") and acting (calling a tool). Most common pattern.

**Plan-and-Execute:** The agent creates a multi-step plan upfront, then executes each step. Better for complex tasks but less adaptive.

**Reflection:** After generating output, the agent critiques its own work and iterates. Used for code generation, writing, analysis.

**Multi-agent:** Multiple specialized agents collaborate — e.g., a "researcher" agent gathers info, a "writer" agent drafts, a "reviewer" agent critiques. Orchestrated by a supervisor agent.

### 5.3 Orchestration Frameworks

| Framework | Description |
|---|---|
| **LangChain** | The most widely used. Provides chains, agents, tool abstractions, memory, retrievers. Large ecosystem. |
| **LangGraph** | Built on LangChain. Models agents as state machines / graphs. Each node is a step; edges are transitions. Better for complex, multi-step, conditional workflows. |
| **LlamaIndex** | Focused on data retrieval and RAG. Strong indexing, query engines, and data connectors. |
| **CrewAI** | Multi-agent framework — define agents with roles, goals, and tools, then let them collaborate. |
| **AutoGen (Microsoft)** | Multi-agent conversation framework. |
| **Semantic Kernel (Microsoft)** | Lightweight SDK for integrating LLMs with plugins/tools. |
| **Databricks Mosaic AI Agent Framework** | Databricks-native. Tight integration with MLflow, Unity Catalog, Model Serving. |

### 5.4 MCP (Model Context Protocol)

MCP is an open protocol (created by Anthropic) that standardizes how LLMs interact with external tools and data sources.

**The problem it solves:** Every tool integration is currently custom — each LLM framework has its own way of defining tools. MCP creates a universal standard:

- **MCP Server**: Exposes capabilities (tools, resources, prompts) via a standard protocol
- **MCP Client**: The LLM/agent framework that connects to MCP servers
- **Tool**: A function the LLM can call (e.g., "search_database", "send_email")
- **Resource**: Data the LLM can read (e.g., a file, a database table)

**Why a regulated asset manager cares:** In enterprise settings, you want agents to securely access internal systems (databases, APIs, ticketing systems). MCP provides a governed, standardized way to do that instead of ad-hoc integrations.

### 5.5 Tool / Function Calling

This is the mechanism by which an LLM invokes external tools. The LLM doesn't actually execute code — it generates a structured request (JSON) describing which function to call and with what arguments. The orchestrator executes the function and feeds the result back.

```
LLM output: {"tool": "search_db", "args": {"query": "Q3 revenue"}}
    ↓
Orchestrator executes search_db("Q3 revenue")
    ↓
Result fed back to LLM as context
    ↓
LLM generates final response using the result
```

### 5.6 RAG (Retrieval-Augmented Generation)

RAG is the pattern of augmenting LLM generation with retrieved documents.

**Pipeline:**
1. **Indexing (offline):** Chunk documents → embed each chunk → store in vector store
2. **Retrieval (at query time):** Embed the user query → search vector store for top-K similar chunks
3. **Generation:** Pass retrieved chunks + user query to LLM → LLM answers grounded in the retrieved context

**Advanced RAG patterns:**
- **Hybrid search**: Combine vector similarity with keyword (BM25) search
- **Reranking**: Use a cross-encoder model to re-score retrieved chunks for relevance
- **Query transformation**: Rewrite the user query for better retrieval (HyDE, step-back prompting)
- **Agentic RAG**: The agent decides when and how to retrieve — it can reformulate queries, search multiple sources, and validate results before answering

### 5.7 Evaluation Harnesses for Agents

The JD emphasizes "evaluation harnesses, traces, and replay tooling." This is about measuring and improving agent quality:

**What to evaluate:**
- **Correctness**: Did the agent produce the right answer?
- **Groundedness / faithfulness**: Is the answer supported by the retrieved evidence? (No hallucination)
- **Tool use accuracy**: Did it call the right tools with the right arguments?
- **Latency**: How long did it take?
- **Cost**: How many tokens / API calls were consumed?
- **Safety**: Did it refuse unsafe requests? Did it leak PII?

**How to evaluate:**
- **LLM-as-judge**: Use a separate LLM to score the agent's output against a rubric
- **Human-in-the-loop**: Route uncertain or high-stakes outputs to human reviewers
- **Regression testing**: Maintain a suite of test cases; run them after every change
- **Tracing**: Log every step the agent took (LangSmith, MLflow Tracing, Arize Phoenix) — input/output at each node, latency, token count
- **Replay**: Re-run a traced execution to debug failures or test improvements

### 5.8 Guardrails

Mechanisms to constrain LLM/agent behavior:

- **Input guardrails**: Filter/validate user inputs before they reach the LLM (block prompt injection, PII)
- **Output guardrails**: Validate LLM outputs before they reach the user (block toxic content, check factual grounding, enforce format)
- **Tool guardrails**: Limit which tools an agent can call and with what parameters (don't let it delete production data)
- **Human-in-the-loop**: For high-stakes actions, require human approval before the agent executes

**Libraries:** Guardrails AI, NeMo Guardrails (NVIDIA), custom validation layers.

---

## 6. ML Engineering Fundamentals

### 6.1 Production ML Lifecycle

```
Data Collection → Data Cleaning → Feature Engineering → Model Training
    → Evaluation → Deployment → Monitoring → Retraining (loop)
```

**Key concepts:**
- **Feature store**: Centralized repository of features, shared across models. Ensures consistency between training and serving.
- **Model registry**: Versioned storage of trained models with metadata (who trained it, on what data, with what metrics).
- **CI/CD for ML**: Automated pipelines that train, evaluate, and deploy models on code push or data change.
- **Drift detection**: Monitor whether input data distribution or model performance is changing over time. Types: data drift (input distribution shifts), concept drift (relationship between input and target changes), prediction drift (model outputs shift).
- **A/B testing / shadow deployment**: Serve a new model alongside the old one, compare performance before full rollout.

### 6.2 APIs for ML (REST and Streaming)

**REST APIs**: Standard request-response. Client sends a request, waits for a complete response. Good for: batch predictions, simple inference, tool calls.

**Streaming APIs**: Server sends data incrementally (Server-Sent Events or WebSockets). Good for: LLM token-by-token streaming, real-time dashboards, long-running agent workflows where you want partial results.

**In practice on AWS:**
- API Gateway + Lambda for lightweight REST endpoints
- ECS/EKS (containers) for heavier model serving
- Databricks Model Serving for Databricks-native models
- FastAPI is the most common Python framework for ML APIs

### 6.3 Cost Optimization

The JD mentions "optimize performance, cost, and computational efficiency." Key levers:

- **Spot instances**: Use AWS spot EC2 for non-critical training jobs (60-90% cheaper, but can be interrupted)
- **Autoscaling**: Scale clusters up/down based on demand (Databricks auto-termination, serverless SQL)
- **Model distillation**: Train a smaller model to mimic a larger one — cheaper inference
- **Quantization**: Reduce model precision (FP32 → FP16 → INT8) for faster, cheaper inference
- **Caching**: Cache LLM responses (Redis) for repeated queries
- **Batch inference**: Process many requests at once instead of one-by-one
- **Right-sizing**: Don't use a GPU cluster for a job that runs fine on CPU

---

## 7. DevOps / MLOps on AWS

### 7.1 Containerization

- **Docker**: Package your application + all dependencies into an image. Reproducible across environments.
- **Amazon ECR**: Managed Docker container registry on AWS.
- **Amazon ECS / EKS**: Run containers in production. ECS is AWS-native; EKS is managed Kubernetes.

### 7.2 CI/CD

- **GitHub Actions**: Most common for open-source and startup teams.
- **AWS CodePipeline / CodeBuild**: AWS-native CI/CD.
- **Databricks Asset Bundles**: CI/CD for Databricks-specific resources (jobs, notebooks, models).

A typical ML CI/CD pipeline:
1. Developer pushes code to Git
2. CI runs unit tests + linting
3. CI triggers a training job on Databricks
4. Model is evaluated against a holdout set
5. If metrics pass threshold → model is registered in MLflow (Staging)
6. Manual or automated promotion to Production
7. CD deploys the new model to a serving endpoint

### 7.3 Observability

- **MLflow Tracing**: Trace agent/LLM calls end-to-end
- **CloudWatch**: Infrastructure metrics (CPU, memory, network)
- **Prometheus + Grafana**: Custom metrics dashboards
- **LangSmith**: Specialized tracing for LangChain agents
- **Arize / Evidently / WhyLabs**: ML-specific monitoring (drift, data quality, model performance)

---

## 8. Responsible AI & Governance (Asset-Management Context)

Financial services firms operate under heavy regulatory scrutiny. The JD's emphasis on governance isn't aspirational — it's mandatory.

**What "embed responsible AI practices" means in practice:**

- **Model explainability**: Can you explain why the model made a specific prediction? (SHAP, LIME, attention visualization)
- **Bias detection**: Are model outputs unfair to any protected group? Regular bias audits.
- **Data lineage**: For any model output, trace back to the exact training data, features, and preprocessing steps.
- **Access controls**: Principle of least privilege — data scientists can't access production PII; models can't access data they weren't explicitly granted.
- **Audit trails**: Every model training run, deployment, and prediction is logged and immutable.
- **Human-in-the-loop**: For high-stakes decisions (investment recommendations, risk assessments), require human review before acting on model output.
- **Model risk management (SR 11-7)**: Federal Reserve guidance requiring financial institutions to validate, monitor, and govern models — including AI/ML models.

---

## 9. Quick-Reference Glossary

| Term | Definition |
|---|---|
| **ACID** | Atomicity, Consistency, Isolation, Durability — guarantees for database transactions |
| **CDC** | Change Data Capture — streaming changes from a database to a data pipeline |
| **DAG** | Directed Acyclic Graph — workflow of tasks with dependencies |
| **DTE** | Days to Expiration (you know this from options — same concept applies to data retention/TTL) |
| **Embedding** | A dense vector representation of text/images in continuous space |
| **ETL** | Extract, Transform, Load — moving data from sources to a target system |
| **Feature Store** | Centralized repo of reusable ML features with consistent serving |
| **Fine-tuning** | Further training a pre-trained model on task-specific data |
| **GraphRAG** | RAG enhanced with knowledge graph structure for relationship-aware retrieval |
| **HyDE** | Hypothetical Document Embeddings — generate a hypothetical answer, embed it, search with that |
| **IaC** | Infrastructure as Code (Terraform, CloudFormation) |
| **k-NN** | k-Nearest Neighbors — the core algorithm behind vector search |
| **Lakehouse** | Architecture combining data lake storage with warehouse governance |
| **LCEL** | LangChain Expression Language — declarative way to chain LLM operations |
| **MLOps** | DevOps practices applied to ML systems |
| **PERM** | Not the immigration PERM — in this context, permissions/access controls |
| **Prompt engineering** | Crafting inputs to LLMs to get desired outputs (few-shot, chain-of-thought, etc.) |
| **Serverless** | Compute that scales to zero when idle — you pay only for usage |
| **SDLC** | Software Development Lifecycle |
| **Unity Catalog** | Databricks' centralized governance platform |
| **Vector store** | Database optimized for similarity search over embedding vectors |

---

## 10. How These Pieces Fit Together (Architecture Diagram in Words)

```
                          ┌─────────────────────────┐
                          │     User / Product       │
                          │  (Web App, Internal Tool) │
                          └────────────┬──────────────┘
                                       │
                              REST / Streaming API
                                       │
                          ┌────────────▼──────────────┐
                          │   Agent Orchestrator       │
                          │ (LangGraph / Mosaic AI)    │
                          │                            │
                          │  ┌─────────────────────┐   │
                          │  │ LLM (via Model       │   │
                          │  │ Serving / AI Gateway) │   │
                          │  └─────────────────────┘   │
                          │           │                 │
                          │     Tool Calls (MCP)        │
                          │    ┌──────┼──────┐          │
                          │    ▼      ▼      ▼          │
                          │  Vector  Graph  Redis       │
                          │  Store   DB     Cache       │
                          │  (RAG)  (KG)   (Memory)    │
                          └────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                   ▼
            ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
            │  Databricks   │  │    MLflow     │   │ Unity Catalog │
            │  (Spark ETL,  │  │  (Tracking,   │   │ (Governance,  │
            │   Training,   │  │   Registry,   │   │  Lineage,     │
            │   Serving)    │  │   Evaluate)   │   │  Access Ctrl) │
            └──────┬───────┘  └──────────────┘   └──────────────┘
                   │
            ┌──────▼───────┐
            │  Delta Lake   │
            │  (on S3)      │
            │  ACID, Schema │
            │  Time Travel  │
            └──────────────┘
```

---

*Last updated: May 2026 — Cross-reference with official Databricks and AWS documentation for the latest features.*
