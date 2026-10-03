# Interview Prep — AI / Backend Engineer (Agent-Oriented Systems)

---

## Part 1: System Design — "Design an Agentic RAG Pipeline"

This is the most likely design question you'll face. Below is a reference architecture you can walk through on a whiteboard, then adapt to whatever scenario they throw at you.

---

### 1.1 The Scenario

> "Design a system where business users can ask complex questions over internal company documents (policies, contracts, reports). The system should break down ambiguous questions, retrieve relevant context, and produce validated, structured answers."

### 1.2 High-Level Architecture

```
User (React frontend)
  │
  ▼
API Gateway (REST / WebSocket)
  │
  ▼
┌─────────────────────────────────┐
│  SUPERVISOR AGENT               │
│  (orchestrator / router)        │
│  - classifies intent            │
│  - decides which sub-agents     │
│  - manages conversation state   │
└─────┬───────┬───────┬───────────┘
      │       │       │
      ▼       ▼       ▼
  ┌───────┐ ┌──────┐ ┌──────────────┐
  │Query  │ │RAG   │ │Validation /  │
  │Planner│ │Agent │ │Output Agent  │
  └───┬───┘ └──┬───┘ └──────┬───────┘
      │        │             │
      ▼        ▼             ▼
  (rewrites  ┌──────────┐  (Pydantic
   multi-hop │Retrieval │   schema
   queries)  │Pipeline  │   checks,
             └──┬───────┘   citations)
                │
        ┌───────┴────────┐
        ▼                ▼
  Vector Store      Keyword Index
  (OpenSearch /     (OpenSearch BM25 /
   Pinecone /        Elasticsearch)
   pgvector)
        │                │
        └───────┬────────┘
                ▼
         Re-ranker (Cohere / cross-encoder)
                │
                ▼
         Context window assembly
```

### 1.3 How to Walk Through It

Use this sequence — it mirrors how senior engineers think:

**Step 1 — Clarify requirements (30 seconds)**
- "What's the document corpus size? Thousands or millions?"
- "Latency target — interactive (<3s) or async report?"
- "Do answers need citations back to source paragraphs?"
- "Multi-tenant or single org?"

**Step 2 — Start at the edges, work inward**
- User sends a question via React frontend → hits an API Gateway (API Gateway + Lambda or ALB + ECS)
- Response streams back via WebSocket or SSE for perceived speed

**Step 3 — The Supervisor pattern (this is your star moment)**
- A top-level **supervisor agent** receives every request
- It decides the execution plan: does this need retrieval? Does the query need decomposition? Is it a follow-up that can use cached context?
- The supervisor dispatches to **sub-agents** and collects their results
- This is the **supervisor/sub-agent pattern** — the JD calls it out explicitly

**Step 4 — Sub-agents in detail**
- **Query Planner**: rewrites vague user questions into precise retrieval queries; handles multi-hop (Q1 → retrieve → Q2 → retrieve → synthesize)
- **RAG Agent**: calls the retrieval pipeline, assembles context, calls the LLM with the grounded prompt
- **Validation Agent**: checks the LLM output against a Pydantic schema, verifies citations exist in source chunks, retries if malformed

**Step 5 — Retrieval pipeline**
- Documents ingested offline: chunked (512–1024 tokens, with overlap), embedded (OpenAI `text-embedding-3-small` or Cohere), stored in vector DB
- At query time: **hybrid search** = dense vector similarity + sparse BM25 keyword match
- Results go through a **cross-encoder re-ranker** for precision
- Top-k chunks assembled into the prompt's context window

**Step 6 — Infrastructure (AWS-native)**
- Compute: ECS Fargate or Lambda for stateless agents
- Vector store: Amazon OpenSearch Serverless (has both vector and BM25) or self-hosted pgvector on RDS
- Object storage: S3 for raw documents and pre-computed embeddings
- Cache: ElastiCache (Redis) for embedding cache and frequent-query result cache
- Queue: SQS or Step Functions for async multi-step workflows
- CI/CD: CodePipeline + CodeBuild, or GitHub Actions → ECR → ECS

**Step 7 — Observability (earns bonus points)**
- Structured logging with correlation IDs that trace a request across supervisor → sub-agents → LLM calls → retrieval
- Metrics: latency per agent step, token usage, retrieval hit rate, cache hit rate
- Tracing: OpenTelemetry spans or AWS X-Ray
- LLM-specific: log prompt/completion pairs to S3 for evaluation; track hallucination rate over time

### 1.4 Design Trade-offs to Discuss Proactively

| Decision | Option A | Option B | Trade-off |
|---|---|---|---|
| Vector DB | Managed (Pinecone, OpenSearch Serverless) | Self-hosted (pgvector) | Cost vs. control & latency |
| Agent orchestration | LangGraph (graph-based) | Custom Python (asyncio + state machine) | Flexibility vs. ecosystem/community |
| Chunking strategy | Fixed-size (512 tokens) | Semantic (by heading/paragraph) | Simplicity vs. retrieval quality |
| LLM calls | Single large model | Router → small model for easy, large for hard | Cost vs. latency vs. quality |
| Sync vs. async | Synchronous API | Async with WebSocket streaming | Simplicity vs. UX |
| Caching layer | Cache embeddings only | Cache full query→answer pairs | Freshness vs. speed |

Interviewers love when you name the trade-off before they ask.

---

## Part 2: Tools & Frameworks Landscape

Know these well enough to discuss when you'd pick each one and why.

### 2.1 Agent Orchestration

| Tool | What it is | When to use | Key concept |
|---|---|---|---|
| **LangGraph** | Graph-based agent framework by LangChain | Complex multi-step agents with branching, cycles, human-in-the-loop | State graph with nodes (agents/tools) and conditional edges |
| **CrewAI** | Role-based multi-agent framework | When you want agents with distinct personas/roles collaborating | Crew = set of agents with goals, tasks, and tools |
| **Autogen (Microsoft)** | Multi-agent conversation framework | Research prototyping, conversational agent topologies | Agents talk to each other in a conversation loop |
| **Custom (asyncio + state machine)** | Roll your own | When frameworks add overhead or you need full control | You own the complexity but also the flexibility |
| **AWS Step Functions** | Managed state machine | When workflows are well-defined and you want AWS-native durability | Great for retry/error handling; less great for dynamic agent routing |

**Your go-to answer**: "For production, I'd start with LangGraph for its explicit state management and conditional routing, but I'd evaluate whether the complexity warrants it — for simpler linear workflows, Step Functions or plain asyncio with a state dict can be cleaner."

### 2.2 LLM Integration

| Tool | Purpose |
|---|---|
| **LangChain** | Chain-of-thought composition, tool use, output parsing |
| **LiteLLM** | Unified API across OpenAI, Anthropic, Bedrock, etc. |
| **Instructor** | Pydantic-validated structured outputs from LLMs |
| **Guardrails AI** | Output validation, re-asking on failure |
| **Amazon Bedrock** | Managed LLM access on AWS (Claude, Titan, Llama) |

### 2.3 Retrieval & Vector Search

| Tool | Type | Notes |
|---|---|---|
| **Amazon OpenSearch Serverless** | Managed, hybrid | Supports both k-NN vector and BM25; AWS-native |
| **Pinecone** | Managed vector DB | Simple API, serverless tier, metadata filtering |
| **pgvector** | Postgres extension | Good when you already run RDS; co-locates structured + vector data |
| **ChromaDB** | Lightweight, local-first | Good for prototyping; less proven at scale |
| **FAISS** | Facebook's similarity search lib | Blazing fast, no managed service — you host it |
| **Cohere Rerank** | Cross-encoder re-ranker | Dramatically improves retrieval precision as a second stage |

### 2.4 Embeddings

| Model | Dimensions | Notes |
|---|---|---|
| OpenAI `text-embedding-3-small` | 1536 | Good balance of quality and cost |
| OpenAI `text-embedding-3-large` | 3072 | Higher quality, higher cost |
| Cohere `embed-v3` | 1024 | Strong multilingual support |
| Amazon Titan Embeddings | 1536 | AWS-native, stays within Bedrock |
| Open-source (e5-large, BGE) | varies | Self-hosted, no API costs |

### 2.5 AWS Services Map

| Concern | Service |
|---|---|
| Compute (containers) | ECS Fargate, EKS |
| Compute (serverless) | Lambda |
| API layer | API Gateway, ALB |
| Async workflows | SQS, SNS, Step Functions, EventBridge |
| Storage | S3 (documents, embeddings), DynamoDB (metadata, state) |
| Vector search | OpenSearch Serverless |
| Caching | ElastiCache (Redis) |
| LLM access | Bedrock |
| Auth | Cognito, IAM |
| CI/CD | CodePipeline, CodeBuild, ECR |
| Observability | CloudWatch, X-Ray, OpenSearch (logs) |
| Secrets | Secrets Manager, Parameter Store |

### 2.6 CI/CD & Environment Management

| Practice | Implementation |
|---|---|
| Infrastructure as Code | Terraform or AWS CDK (Python) |
| Container registry | ECR |
| Pipeline | GitHub Actions → build → push to ECR → deploy to ECS |
| Environments | dev / staging / prod via separate AWS accounts or namespaces |
| Feature flags | LaunchDarkly or AWS AppConfig |
| Testing in pipeline | Unit → integration → contract → smoke test post-deploy |

### 2.7 Observability Stack

| Layer | Tool | What to capture |
|---|---|---|
| Logging | CloudWatch Logs + structured JSON | Every agent step, LLM call, retrieval query, with correlation ID |
| Metrics | CloudWatch Metrics or Prometheus | Latency (p50/p95/p99), token usage, error rate, cache hit rate |
| Tracing | AWS X-Ray or OpenTelemetry | End-to-end trace from API call → supervisor → sub-agents → LLM → retrieval |
| LLM-specific | LangSmith, Langfuse, or custom S3 logging | Prompt/completion pairs, cost tracking, evaluation scores |

---

## Part 3: Best Practices (by Skill Area)

### 3.1 Python Backend Engineering

- **Project structure**: Use a clean package layout — `src/agents/`, `src/retrieval/`, `src/api/`, `src/models/` (Pydantic schemas)
- **Async-first**: Use `asyncio` and `httpx` (async HTTP client) for I/O-bound agent workflows; avoid blocking calls in the event loop
- **Dependency injection**: Use a lightweight DI pattern or `dependency-injector` for testability — inject LLM clients, vector store clients, config
- **Error handling**: Wrap every LLM call and external API call in retry logic with exponential backoff (`tenacity` library); define custom exception hierarchy
- **Testing pyramid**: Unit tests for prompt templates and output parsers, integration tests for retrieval pipeline, end-to-end tests for full agent flows with mocked LLM responses
- **Type safety**: Pydantic models everywhere — request/response schemas, agent state, LLM outputs

### 3.2 Agent Orchestration Patterns

- **Supervisor pattern**: A top-level agent that routes and coordinates; sub-agents are stateless and return results to the supervisor
- **State management**: Pass an explicit state object through the graph; never rely on global mutable state; serialize state to DynamoDB for long-running workflows
- **Human-in-the-loop**: Design breakpoints where the supervisor can pause and request human approval before proceeding (critical for enterprise)
- **Retry & fallback**: If a sub-agent fails, the supervisor can retry with a different strategy (e.g., simpler prompt, different model, cached result)
- **Idempotency**: Every agent step should be idempotent — safe to retry without side effects

### 3.3 Prompt & Context Management

- **Prompt templates**: Version-controlled, parameterized templates (Jinja2 or plain f-strings with a registry)
- **Context window budget**: Explicitly allocate token budgets — e.g., system prompt (500 tokens), retrieved context (3000 tokens), conversation history (1000 tokens), leave room for output
- **Context compression**: Summarize older conversation turns; truncate retrieved chunks to the most relevant sections
- **Few-shot examples**: Include 2–3 examples in the prompt for structured output tasks; store examples alongside the template
- **Prompt evaluation**: Track prompt versions and run offline evals (correctness, hallucination rate, format compliance) before deploying changes

### 3.4 Structured Outputs & Validation

- **Pydantic all the way**: Define output schemas as Pydantic models; use `Instructor` or equivalent to constrain LLM output
- **Retry on failure**: If the LLM returns invalid JSON or fails schema validation, retry with the error message appended to the prompt (up to 3 retries)
- **Partial parsing**: For streaming responses, parse incrementally and validate at the end
- **Citation validation**: If the output claims "according to document X, paragraph Y", verify that chunk actually exists in the retrieved context

### 3.5 Retrieval Pipeline Best Practices

- **Chunking**: Start around 200–400 tokens without overlap and measure; add overlap only if recall@k improves on your gold set (chapter 24c); prefer semantic boundaries (headings, paragraphs) over fixed-size
- **Hybrid search**: Always combine dense (vector) + sparse (BM25) retrieval; tune the weight between them
- **Re-ranking**: Add a cross-encoder re-ranker as a second stage — it's the single highest-impact improvement to retrieval quality
- **Metadata filtering**: Store document metadata (date, author, department, document type) and filter before or after retrieval
- **Evaluation**: Measure retrieval quality separately from generation quality — use metrics like Recall@k, MRR, NDCG
- **Index refresh**: Design the ingestion pipeline to handle document updates (re-chunk, re-embed, upsert) without full reindexing

#### Retrieval Evaluation Terms You Should Be Able to Explain

- **Offline evaluation**: Evaluate retrieval on a fixed labeled dataset before shipping changes. The standard format is a set of `(query, relevant_documents)` pairs, where each query has one or more documents or chunks marked as correct. This lets you compare retrieval pipelines repeatably without depending on live traffic.

Example:

```python
test_set = [
    {
        "query": "What is the company travel reimbursement policy?",
        "relevant_documents": ["policy_chunk_17", "policy_chunk_18"]
    },
    {
        "query": "How do I reset my VPN access?",
        "relevant_documents": ["it_doc_chunk_4"]
    }
]
```

- **Recall@k**: Measures whether the retriever gets the correct documents into the top `k` results. It answers: "Did we retrieve the right evidence at all?" If there are 2 relevant chunks and 1 appears in the top 5, then `Recall@5 = 1/2 = 0.5`. This is especially useful in RAG because the generator can only use evidence that was actually retrieved.

- **MRR (Mean Reciprocal Rank)**: Measures how early the first relevant result appears. If the first correct result is at rank 1, the score is `1`. If it is at rank 2, the score is `1/2`. If it is at rank 5, the score is `1/5`. Then average that across all queries. MRR is good when you care a lot about the first good match being near the top.

- **NDCG (Normalized Discounted Cumulative Gain)**: Measures ranking quality while giving more credit to relevant results that appear earlier. It is better than a simple hit/miss metric when you care about the full ranking order, not just whether one relevant chunk showed up somewhere in the list. In practice, a score closer to `1.0` means the ranking is closer to ideal.

- **A/B test chunking strategies, embedding models, and re-rankers**: Do not assume the "best" offline setup is best in production. Compare variants on live traffic. For chunking, you might compare `512-token fixed chunks` vs `semantic paragraph chunks`. For embeddings, compare two embedding models. For re-ranking, compare `vector-only retrieval` vs `vector retrieval + cross-encoder reranker`. Use online metrics like answer success rate, user satisfaction, latency, and cost alongside offline retrieval metrics.

- **Separate retrieval evaluation from generation evaluation**: Judge retrieval and answer generation as two different stages. A bad final answer might come from poor retrieval, or retrieval may be correct but the LLM may still hallucinate, misread, or summarize badly. Retrieval evaluation uses metrics like `Recall@k`, `MRR`, and `NDCG`. Generation evaluation looks at factuality, completeness, formatting, citation quality, and user satisfaction.

- **Track retrieval metrics in production dashboards**: Retrieval quality should not live only in notebooks. Put it into dashboards alongside latency and error rate. Useful production metrics include retrieval latency, reranker latency, zero-hit rate, average top-k similarity score, cache hit rate, citation coverage, and sampled online Recall@k from labeled traffic.

- **Use feedback loops**: When users flag bad answers, trace back to the retrieval step and inspect which chunks were used. Store the original query, rewritten query, retrieved chunk IDs, chunk ranks, cited chunks, and final answer. This helps you determine whether the issue was chunking, embedding quality, reranking, filtering, or answer generation. It also creates new labeled failure cases for future offline evaluation.

**One-line interview summary**: "For RAG, I evaluate retrieval offline with `(query, relevant_documents)` test sets and metrics like Recall@k, MRR, and NDCG, then validate changes online with A/B tests, production dashboards, and user feedback loops that let me trace bad answers back to the retrieved chunks."

### 3.6 Security & IAM

- **Least privilege**: Each service gets its own IAM role with minimal permissions
- **Secrets**: Never hardcode API keys; use Secrets Manager or Parameter Store; rotate regularly
- **Data at rest**: Encrypt S3 buckets (SSE-S3 or SSE-KMS), encrypt vector DB indices
- **Data in transit**: TLS everywhere; enforce HTTPS on all API endpoints
- **Multi-tenancy**: If serving multiple orgs, enforce tenant isolation at the retrieval layer (metadata filter on tenant ID) and at the API layer (Cognito + JWT claims)

### 3.7 Working with Stakeholders

- **Discovery → Design → Deliver**: Translate a business use case into a technical design doc with acceptance criteria before coding
- **Trade-off communication**: Use a simple framework — "We can optimise for X (quality/speed/cost), but that means accepting Y. Here's my recommendation and why."
- **Incremental delivery**: Ship a thin vertical slice first (one agent, one document type, one query pattern), get feedback, iterate
- **Demo-driven development**: Show working software to stakeholders every 1–2 weeks; let them interact with it

---

## Part 4: Likely Interview Questions & Answer Frameworks

### Q1: "Walk me through how you'd design an agent system for [X use case]."

**Framework** (use the STAR-D method — Situation, Task, Architecture, Risks, Delivery):
1. Clarify the requirements (ask 2–3 questions)
2. Sketch the supervisor/sub-agent topology
3. Walk through the data flow end to end
4. Call out 2–3 key trade-offs and your recommendation
5. Describe how you'd deliver incrementally

### Q2: "How do you handle errors and retries in multi-step agent workflows?"

**Strong answer elements**:
- Idempotent agent steps (safe to retry)
- Retry with exponential backoff at the individual step level (tenacity)
- Supervisor-level fallback strategies (different model, simpler prompt, cached result)
- Dead-letter queue for permanently failed requests
- Correlation IDs for tracing failures across steps
- Circuit breaker pattern for external API calls

### Q3: "How do you evaluate and improve retrieval quality?"

**Strong answer elements**:
- Offline evaluation: build a test set of (query, relevant_documents) pairs
- Metrics: Recall@k, MRR, NDCG
- A/B test chunking strategies, embedding models, re-rankers
- Separate retrieval evaluation from generation evaluation
- Track retrieval metrics in production dashboards
- Use feedback loops: if users flag bad answers, trace back to which retrieved chunks were used

### Q4: "How do you manage prompts in production?"

**Strong answer elements**:
- Prompts are version-controlled alongside code
- Parameterized templates (not string concatenation)
- Token budget allocation strategy
- Offline evaluation before deploying prompt changes
- A/B testing framework for prompt variants
- LLM observability (log all prompt/completion pairs for debugging and evaluation)

### Q5: "How would you make this system observable?"

**Strong answer elements**:
- Correlation ID propagated from API gateway through every agent step and LLM call
- Structured JSON logging (not print statements)
- Key metrics: end-to-end latency, per-step latency, token usage, retrieval recall, cache hit rate, error rate by type
- Distributed tracing (X-Ray or OpenTelemetry)
- LLM-specific observability: prompt/completion logging, cost tracking, hallucination detection
- Alerting on anomalies (latency spike, error rate increase, token cost spike)

### Q6: "Tell me about a time you had to communicate a technical trade-off to a non-technical stakeholder."

**Use your ad-tech experience**:
- Framing: "The business wanted X. The straightforward approach had [cost/risk/latency] implications. I presented two options with clear trade-offs — Option A optimised for [quality] at the cost of [delivery time], Option B shipped faster but required [follow-up work]. We chose B and iterated."
- Show that you use data and concrete examples, not jargon

### Q7: "What's the difference between LangChain, LangGraph, and when would you not use either?"

**Strong answer**:
- LangChain: library for composing LLM chains — prompt templates, output parsers, tool integrations. Good for linear workflows.
- LangGraph: built on LangChain, adds a state graph with conditional edges, cycles, and persistence. Use for complex agents with branching logic, retries, human-in-the-loop.
- Skip both when: the workflow is simple enough that raw API calls + Pydantic + asyncio are cleaner, or when you need maximum control over execution flow and error handling. Frameworks add abstraction layers that can make debugging harder.

---

## Part 5: Quick-Reference Cheat Sheet

### Vocabulary to use naturally in conversation

| Instead of... | Say... |
|---|---|
| "The main AI" | "The supervisor agent" |
| "It calls the database" | "The retrieval pipeline performs hybrid search — dense vector similarity plus BM25 keyword matching" |
| "We check the output" | "We validate the structured output against a Pydantic schema and retry with error context on failure" |
| "We deploy it" | "We push to ECR, deploy via ECS Fargate with blue-green deployment, and validate with smoke tests" |
| "We log stuff" | "We emit structured logs with correlation IDs and propagate OpenTelemetry spans across agent steps" |
| "We break the document into pieces" | "We chunk documents at semantic boundaries with configurable overlap, embed with [model], and upsert into the vector index" |
| "We make sure it's secure" | "Each service runs with a least-privilege IAM role, secrets are in Secrets Manager, and tenant isolation is enforced at the retrieval layer via metadata filtering" |

### Numbers to have ready

- Typical embedding dimensions: 1024–3072
- Chunk size: start around 200–400 tokens with no overlap and add overlap only if recall@k improves on your gold set (evidence in chapter 24c; older guidance of 256–1024 tokens with 10–20% overlap tends to lower precision)
- Retrieval top-k: 5–20 candidates before re-ranking, 3–5 after
- LLM context budget: allocate explicitly (system 500, context 3000, history 1000, output 1500 — adjust per model)
- Target latency for interactive agent: <3s end-to-end for simple queries, <10s for multi-hop
- Re-ranker improvement: typically 10–30% improvement in Recall@5 over vector-only retrieval


## Appendix
⏺ A correlation ID is a unique identifier attached to a request (or event) that follows it through every system, service, and log entry it touches.
                                                                                                                                                                                                                                         
  Why it exists: In distributed systems, a single user action might pass through 5+ microservices. When something goes wrong, you need a way to trace that request end-to-end across all those services' logs. Without a correlation ID, you'd be trying to
   stitch together logs by timestamp alone — nearly impossible under load.

  How it works:
  1. A request arrives (or is created) — a unique ID is generated (e.g., a UUID)
  2. Every service that handles the request reads the ID and passes it along (usually as an HTTP header like X-Correlation-ID or X-Request-ID)
  3. Every log entry includes that ID
  
  Result: You can run one log query — correlation_id = "abc-123" — and see the complete journey of that request across all services.

  Simple example:

  API Gateway  → logs: correlation_id=abc-123, "received POST /order"
  Order Service → logs: correlation_id=abc-123, "created order #99"
  Payment Service → logs: correlation_id=abc-123, "charge failed: card declined"
  Notification Service → logs: correlation_id=abc-123, "sent failure email"

  Without the correlation ID, those four log lines are invisible needles in a haystack of concurrent requests.


⏺ The circuit breaker pattern protects a system from cascading failures when a downstream service is unavailable or slow. It's named after the electrical circuit breaker — which cuts power before a fault can damage the whole system.

  The Problem It Solves

  Without it: your service keeps sending requests to a failing dependency, those requests pile up (threads, connections, timeouts), and your service goes down too — a cascading failure.

  The Three States
  
           [failure threshold exceeded]
  CLOSED ─────────────────────────────► OPEN
    │                                     │
    │ (normal operation,                  │ (all requests fail
    │  requests pass through)             │  immediately, no calls made)
    │                                     │
    │         [timeout expires]           │
  HALF-OPEN ◄──────────────────────────-─┘
    │
    │ (lets one test request through)
    │
    ├─ success → back to CLOSED
    └─ failure → back to OPEN

  - Closed — everything works, requests flow normally, failures are counted
  - Open — threshold exceeded, requests are rejected immediately (fast fail) without even calling the dependency
  - Half-Open — after a timeout, one probe request is allowed through to test if the dependency recovered

  Why It Helps

  - Fail fast — instead of waiting 30s for a timeout, callers get an instant error
  - Gives the dependency breathing room — stops hammering a struggling service
  - Prevents cascading failures — your service stays healthy even when its dependencies don't

  Simple Example

  # Without circuit breaker: hangs for 30s, consumes a thread
  response = payment_service.charge(card)

  # With circuit breaker: fails in <1ms if payment service is down
  try:
      response = circuit_breaker.call(payment_service.charge, card)
  except CircuitOpenError:
      return "Payment temporarily unavailable, try again later"

  Real-World Usage
  
  Popular libraries: Resilience4j (Java), Polly (.NET), Hystrix (Java, now deprecated), pybreaker (Python).

  It's almost always paired with a retry with exponential backoff — circuit breaker handles sustained outages, retry handles transient blips.
