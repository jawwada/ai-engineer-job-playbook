# 50 expert-level questions — Senior Data Scientist / Agentic AI Engineer (Azure, A2A, MCP, healthcare)
## Interview Preparation Guide — 50 Expert-Level Questions

> Role focus: Agentic Layer · A2A Frameworks · MCP Protocol · Vector Embeddings · Prompt & Context Engineering · Python/Azure · Azure AI Search / Redis / Cosmos DB · Azure Functions & Container Apps · Healthcare Domain

---

## Table of Contents

1. [Agentic AI, A2A & MCP (Q1–Q15)](#section-1-agentic-ai-a2a--mcp-q1q15)
2. [Vector Embeddings, Prompt & Context Engineering (Q16–Q25)](#section-2-vector-embeddings-prompt--context-engineering-q16q25)
3. [Python, Architecture & Azure Cloud (Q26–Q35)](#section-3-python-architecture--azure-cloud-q26q35)
4. [Databases: Azure AI Search, Redis, Cosmos DB (Q36–Q43)](#section-4-databases-azure-ai-search-redis-cosmos-db-q36q43)
5. [Azure Functions, Container Apps & Cloud-Native (Q44–Q48)](#section-5-azure-functions-container-apps--cloud-native-q44q48)
6. [Healthcare Domain (Q49–Q50)](#section-6-healthcare-domain-q49q50)
7. [Your Power Stories — STAR Format](#your-power-stories--star-format)

---

## Section 1: Agentic AI, A2A & MCP (Q1–Q15)

---

### Q1. What is the Agent-to-Agent (A2A) protocol and why does it matter for multi-agent systems?

**Answer:**
A2A is an open protocol (announced by Google in 2025) that defines how AI agents discover each other's capabilities and exchange tasks. Before A2A, agents built on different frameworks (LangGraph, AutoGen, CrewAI) couldn't communicate without bespoke glue code.

A2A defines three standards:
1. **Agent Card** — a JSON manifest published at `/.well-known/agent.json` that describes the agent: its name, capabilities, input/output formats, authentication requirements
2. **Task lifecycle** — a standard state machine: `submitted → working → input-required → completed | failed | canceled`
3. **Message format** — structured envelopes for delegating tasks and returning results, including streaming (SSE) and push notifications

**Why it matters:**
- Agents built by different teams or vendors can interoperate
- Orchestrators can discover and delegate to agents dynamically (capability-based routing)
- Authentication is standardized — agents can trust each other using OAuth/API keys without custom auth logic

**Real example:**
A hospital system has a `diagnosis-support-agent` (built with LangGraph) and a `lab-results-agent` (built with AutoGen). With A2A, the orchestrator reads both agent cards, discovers the lab agent accepts `patient_id` and returns structured lab panels, and delegates accordingly — without the teams needing to coordinate on a shared framework.

---

### Q2. Walk me through designing a multi-agent orchestration system using A2A for a healthcare use case.

**Answer:**
Use case: *Automated pre-authorization workflow for surgical procedures.*

```
Patient record received
        ↓
[Orchestrator Agent]
  Reads patient record → determines pre-auth needed
        ↓
  Discovers agents via A2A registry:
  ┌─────────────────────────────────────────────────────┐
  │  [Clinical Criteria Agent]  agent-card capabilities:│
  │    - input: diagnosis_code, procedure_code          │
  │    - output: payer_criteria_met: bool, evidence[]   │
  │                                                     │
  │  [Benefit Verification Agent]  capabilities:        │
  │    - input: member_id, procedure_code               │
  │    - output: covered: bool, copay, deductible       │
  │                                                     │
  │  [Document Extraction Agent]  capabilities:         │
  │    - input: pdf_url                                 │
  │    - output: structured clinical notes              │
  └─────────────────────────────────────────────────────┘
        ↓
  Runs Clinical Criteria + Benefit Verification in parallel
        ↓
  If criteria_met AND covered → auto-approve
  If not → routes to [Human Review Agent] with evidence package
        ↓
[Notification Agent] → sends result to provider EHR via HL7 FHIR
```

**Key design decisions:**
- Agent cards are versioned so the orchestrator can pin to a stable capability version
- Each agent runs in its own Azure Container App with independent scaling
- A2A task states allow the orchestrator to handle `input-required` (e.g., missing clinical notes) without blocking

---

### Q3. What is the Model Context Protocol (MCP) and how does it differ from function calling?

**Answer:**

**Function calling** is a capability of individual LLMs: you define a JSON schema for a tool, the model outputs a structured call, your code executes it. It's model-specific (OpenAI's format differs from Anthropic's), the tool definitions live in the client code, and there's no standard for discovery.

**MCP** is a protocol layer above that. An MCP server is a standalone process that:
- Advertises its tools, resources, and prompt templates via a standard schema
- Handles execution of those tools itself
- Can be connected by any MCP-compatible client (Claude Desktop, VS Code extension, LangGraph agent)

| Dimension | Function Calling | MCP |
|---|---|---|
| Standardization | Per-provider | Open protocol |
| Discovery | Hardcoded in prompt | Dynamic capability listing |
| Execution | Client-side | Server-side |
| Reusability | Specific to one agent | Any MCP-compatible client |
| Resources | Tools only | Tools + Resources + Prompts |

**Real example:**
Without MCP: you write Jira API calls directly in your agent code, hardcode schemas, maintain auth.
With Jira MCP server: you point your agent at the MCP endpoint, it lists available tools (`create_issue`, `search_jql`, `add_comment`), and any agent you build can call Jira without duplicating the integration code.

---

### Q4. Describe a production agentic system you've designed end to end. What were the failure modes and how did you address them?

**Answer template (adapt with your experience):**

**System:** Clinical documentation assistant that listens to doctor-patient conversations, extracts structured data, and pre-fills EHR fields.

**Architecture:**
```
Audio stream → [Transcription Agent] → raw text
            → [NER Agent] → entities: symptoms, medications, dosages
            → [FHIR Mapper Agent] → structured FHIR resources
            → [Review UI] → doctor approves/edits
            → [EHR Writer Agent] → writes to Epic via FHIR API
```

**Failure modes and mitigations:**

| Failure | Root Cause | Mitigation |
|---|---|---|
| Hallucinated medication dosages | NER agent confabulated when audio was unclear | Added confidence score; flagged low-confidence extractions for mandatory human review |
| Infinite retry loop | EHR API returned 503, agent kept retrying | Added exponential backoff with max retries; circuit breaker after 5 failures |
| Context loss across long appointments | 30-minute conversation exceeded context window | Implemented sliding window summarization every 5 minutes; key entities persisted to Redis |
| Agent picked wrong FHIR resource type | Ambiguous entity mappings | Built a validation step against FHIR schema; critic agent checked mappings before write |

---

### Q5. How do you design trust and security boundaries between agents in a multi-agent system?

**Answer:**

Multi-agent systems introduce a new attack surface: **prompt injection through agent messages**. A malicious observation returned by one tool could instruct an agent to take unauthorized actions.

**Layered trust model:**

```
Trust Level 1 — System prompt (hardcoded by developer)
  → Always trusted, cannot be overridden by external input

Trust Level 2 — Orchestrator agent messages
  → Trusted if authenticated (signed JWT, API key)
  → Validated against declared capability scope

Trust Level 3 — Subagent observations / tool results
  → Never trusted as instructions
  → Sanitized before being injected into context
  → Scope-limited: tool results can only inform, not override policy

Trust Level 4 — User input
  → Validated, rate-limited, sandboxed
```

**Concrete mitigations:**
- **Capability-scoped tokens** — each agent has a token that grants only the tools it needs (least privilege)
- **Observation sanitization** — strip instruction-like patterns from tool results before passing to next agent
- **Action allow-lists** — agents can only call tools on an explicit allow-list, not arbitrary endpoints
- **Audit log** — every agent action is logged with timestamp, actor, tool, parameters, result
- **HITL gates** — for any action affecting PHI or external systems, require human approval

---

### Q6. What is the ReAct pattern and when would you choose it over a static prompt chain?

**Answer:**

**ReAct** (Reasoning + Acting) interleaves reasoning traces with tool calls in a loop:
```
Thought → Action → Observation → Thought → Action → ...
```

**Static prompt chain** = a fixed pipeline of N LLM calls, each transforming the previous output.

**Choose ReAct when:**
- The number of steps is unknown upfront (depends on what you find)
- Tool selection at each step depends on the prior result
- The task may require backtracking or trying a different approach
- You need the model to reason about whether it has enough information to stop

**Choose prompt chaining when:**
- Steps are always the same for every input
- You need predictable latency and cost
- The pipeline must be auditable and testable step-by-step
- You're building a production feature that runs at scale

**Healthcare example:**
- **Static chain**: `OCR PDF → Extract ICD codes → Validate against payer list` — always the same three steps, good for prompt chaining
- **ReAct**: `Answer clinician's question about drug interaction` — may need 1 search or 5, depending on complexity; ReAct is the right pattern

---

### Q7. Explain how you would implement multi-hop reasoning in a RAG system for healthcare queries.

**Answer:**

Multi-hop RAG is needed when the answer requires chaining facts across multiple documents.

**Example query:** *"What is the recommended monitoring frequency for a patient on warfarin who also has CKD stage 3?"*

This requires:
- Hop 1: What is the standard warfarin monitoring protocol? (anticoagulation guidelines)
- Hop 2: How does CKD stage 3 modify warfarin dosing and monitoring? (nephrology guidelines)
- Hop 3: Are there any drug-dose adjustment calculators for this combination? (clinical tools index)

**Implementation:**

```python
def multihop_rag(query: str, kb: VectorDB, llm, max_hops: int = 4):
    context_accumulated = []
    current_query = query
    
    for hop in range(max_hops):
        # Retrieve for current sub-query
        chunks = kb.search(current_query, top_k=5)
        context_accumulated.extend(chunks)
        
        # Ask model: is this enough to answer? If not, what do I need next?
        assessment = llm(f"""
        Original question: {query}
        
        Context gathered so far:
        {format(context_accumulated)}
        
        Can you fully answer the question with this context?
        If yes, respond: ANSWER: <your answer with citations>
        If no, respond: NEED: <specific sub-question to search next>
        """)
        
        if assessment.startswith("ANSWER:"):
            return assessment[7:].strip()
        else:
            current_query = assessment[5:].strip()  # next hop query
    
    # Fallback: answer with what we have
    return llm(f"Answer as best you can: {query}\nContext: {context_accumulated}")
```

**Production additions:**
- Deduplicate accumulated chunks by document ID
- Score each chunk's relevance to the original query before including
- Cap total context at 80% of model's context window
- Store intermediate sub-queries for explainability / audit

---

### Q8. How does the Reflexion pattern improve agent performance over time, and how would you implement it in Azure?

**Answer:**

**Reflexion** (Shinn et al., 2023): after each failed task attempt, the agent generates a verbal reflection — a natural-language summary of *what went wrong and why*. This reflection is stored and prepended to future attempts, allowing the agent to learn from failure without weight updates.

```
Attempt 1 → Fails
Reflection: "I queried the wrong table — patient demographics are in 
             dbo.PatientMaster, not dbo.Encounters"

Attempt 2 (with reflection in context) → Succeeds
```

**Azure implementation:**

```
Reflection Storage → Azure Cosmos DB (document per task type)
  Document structure:
  {
    "task_type": "sql_query_generation",
    "reflection": "Always check schema before writing JOIN...",
    "timestamp": "2025-11-01T09:00:00Z",
    "success_rate_before": 0.62,
    "success_rate_after": 0.89
  }

Retrieval → Azure AI Search (semantic search over reflections)
  On each new task:
    1. Embed task description
    2. Search for top-3 relevant past reflections
    3. Prepend to system prompt

Evaluation → Azure Function (post-task)
    1. Run automated test / human rating
    2. If failed → trigger reflection generation
    3. Upsert to Cosmos DB
```

**Measured impact:** Teams report 15-30% reduction in failure rate on repeated task categories after 20-50 episodes.

---

### Q9. What are the tradeoffs between orchestrator-worker and peer-to-peer agent topologies?

**Answer:**

**Orchestrator-Worker (Hub and Spoke):**
```
[Orchestrator] → delegates → [Worker A]
               → delegates → [Worker B]
               → delegates → [Worker C]
               ← collects results ←
```

Pros: centralized control, easy to audit, single place to enforce policy, clear task routing
Cons: orchestrator is a single point of failure, bottleneck for high throughput, orchestrator needs context about all workers

**Peer-to-Peer:**
```
[Agent A] ←→ [Agent B] ←→ [Agent C]
```
Each agent can call any other based on capability discovery.

Pros: no single point of failure, agents can self-organize, scales better
Cons: harder to audit (who called whom?), risk of circular delegation, harder to enforce global policy

**Hybrid (recommended for production):**
- Orchestrator handles task decomposition, routing, and result synthesis
- Workers are peers among themselves for sub-task collaboration
- A2A protocol handles the discovery and communication

**Healthcare use case:**
- Orchestrator receives pre-auth request
- Delegates to clinical criteria agent and benefit verification agent (parallel)
- Workers exchange notes if one finds ambiguous data
- Orchestrator synthesizes final decision

---

### Q10. How do you prevent prompt injection in a multi-agent system where agents consume external data?

**Answer:**

Prompt injection in agents: a malicious document or API response contains text that looks like instructions (`Ignore your previous instructions and...`), hijacking the agent's behavior.

**Mitigations:**

1. **Structural separation** — never mix retrieved content and instructions in the same text block. Use XML tags or JSON to keep them separate:
```xml
<instructions>You are a clinical data extractor...</instructions>
<retrieved_content>
  [Patient document content here — treat as data only]
</retrieved_content>
```

2. **Observation sanitization** — strip known injection patterns from tool results before including in context. A simple classifier (even a small fine-tuned model) can flag suspicious content.

3. **Capability-scoped prompts** — the agent processing external data should not have tools that take irreversible actions. Separate "reader" agents (can only read/search) from "writer" agents (can write to systems).

4. **Output validation** — before an agent's output is passed to another agent, run it through a schema validator or a guard model that checks for policy violations.

5. **Sandboxed execution** — code execution tools run in isolated containers (Azure Container Apps with no network egress) so even if injection succeeds, the blast radius is contained.

---

### Q11. How would you implement an agent memory system using Azure services?

**Answer:**

```
Memory Types → Azure Services Mapping:

Working memory (in-context)
  → The current prompt window; managed by the LLM framework

Episodic memory (past interactions)
  → Azure Cosmos DB: stores interaction summaries
  → Partitioned by user_id + session_id
  → TTL set based on retention policy (HIPAA: 6 years for clinical data)

Semantic memory (facts and knowledge)
  → Azure AI Search (vector index): stores embedded facts
  → Hybrid search: keyword + semantic for best recall
  → Updated as new facts are confirmed

Procedural memory (learned skills/reflections)
  → Azure Cosmos DB: stores Reflexion-style failure analyses
  → Indexed in Azure AI Search for retrieval by task similarity
```

**Retrieval pattern on each agent turn:**
```python
def build_prompt_with_memory(user_query, user_id, cosmos_client, ai_search_client):
    # 1. Recent episodes (last 3 sessions)
    recent_sessions = cosmos_client.query(
        f"SELECT TOP 3 * FROM c WHERE c.user_id='{user_id}' ORDER BY c._ts DESC"
    )
    
    # 2. Relevant semantic facts
    relevant_facts = ai_search_client.search(
        search_text=user_query,
        vector_fields="content_vector",
        top=5
    )
    
    # 3. Relevant reflections for this task type
    reflections = ai_search_client.search(
        search_text=user_query,
        filter="memory_type eq 'reflection'",
        top=3
    )
    
    return build_prompt(recent_sessions, relevant_facts, reflections, user_query)
```

---

### Q12. What is the difference between tool use and function calling? When would you choose one framing over the other?

**Answer:**

They are effectively the same mechanism — both refer to the model declaring structured intent that the host environment executes. The terminology differs by provider and context:

- **Function calling** — OpenAI's original term; emphasizes calling a function with parameters
- **Tool use** — Anthropic's term for the same pattern; preferred because "tools" is broader (a tool can be an API, a code interpreter, another agent)

**When framing matters in a system design interview:**

If you say "I used function calling," you're describing the low-level mechanism. If you say "I designed a tool layer," you're describing an architecture with:
- A registry of available tools with schemas
- A dispatcher that routes tool calls to implementations
- An observation formatter that structures results for re-injection into context
- An error handler that returns useful error messages as observations

**The architectural framing is what interviewers at senior level want to hear.**

---

### Q13. Describe how you would use the Plan-and-Execute pattern for a complex healthcare workflow.

**Answer:**

**Use case:** Automated discharge summary generation.

**Problem:** A discharge summary requires pulling data from 5+ systems (labs, medications, vitals, diagnoses, procedures) and synthesizing it into a structured clinical document. The steps are mostly known, but some are conditional.

```
[Planner Agent] receives: patient_id, admission_date, discharge_date

Generated Plan:
  1. Retrieve admission diagnosis from EHR [tool: fhir_query]
  2. Retrieve all lab results during admission [tool: fhir_query, parallel]
  3. Retrieve medication list at discharge [tool: fhir_query, parallel]  
  4. Retrieve procedure notes [tool: fhir_query, parallel]
  5. Retrieve vital signs trends [tool: fhir_query, parallel]
  6. IF any critical labs flagged → retrieve attending physician notes [conditional]
  7. Synthesize into SOAP-format summary [tool: llm_generate]
  8. Validate against discharge summary template [tool: schema_validator]
  9. Flag any missing required fields for human review [tool: hitl_gate]
  10. If approved → write to EHR [tool: fhir_write]

[Executor] runs steps 2-5 in parallel (independent)
[Executor] runs step 6 only if triggered
[Synthesizer] runs steps 7-10 sequentially
```

**Why Plan-and-Execute here:**
- Steps are largely known in advance (good for a plan)
- Steps 2-5 can run in parallel (saves 4x latency vs. sequential)
- Step 6 is conditional — the planner can encode this; the executor just checks the condition
- Human review (step 9) is a hard gate before any write to PHI systems

---

### Q14. How do you evaluate an agentic system in production? What metrics matter?

**Answer:**

**Task-level metrics:**

| Metric | What It Measures | Target |
|---|---|---|
| Task completion rate | % of tasks reaching a final answer | >95% for structured tasks |
| Steps to completion | Average hops/actions per task | Baseline vs. optimized |
| Correctness rate | % of outputs that pass human or automated validation | Domain-specific |
| False action rate | % of tool calls that were wrong/unnecessary | <5% |
| Escalation rate | % routed to human review | Track trend, not absolute |

**System-level metrics:**

| Metric | What It Measures |
|---|---|
| P50/P95 latency | Per-step and end-to-end |
| Token cost per task | Total input + output tokens × price |
| Tool error rate | Failures per tool per day |
| Memory hit rate | % of retrievals that returned relevant context |

**Healthcare-specific:**

| Metric | What It Measures |
|---|---|
| PHI exposure incidents | Any unauthorized access to patient data |
| Hallucination rate on clinical facts | Sampled manual review |
| Time-to-human escalation | For urgent cases: how fast does the agent escalate? |

**Evaluation approach:**
- **Automated**: deterministic tests for known-answer queries; schema validation for structured output
- **LLM-as-judge**: a second model scores factual accuracy, completeness, format compliance
- **Human review**: rotating sample of 2-5% of production outputs reviewed by domain experts
- **A/B testing**: shadow mode — new agent runs in parallel, results compared before promotion

---

### Q15. What is context engineering and how is it different from prompt engineering?

**Answer:**

**Prompt engineering** = crafting the *text* of individual prompts for clarity, format, and task alignment. It's about what you say.

**Context engineering** = managing the *entire information space* the model can see at each step. It's about what you include, exclude, compress, and retrieve to maximize model performance given a fixed context window.

Context engineering decisions:
- **What to include**: relevant memory, retrieved chunks, tool results, conversation history
- **What to exclude**: irrelevant history, noise, redundant chunks that waste tokens
- **How to order**: most relevant context closest to the query (recency bias in attention)
- **How to compress**: summarize old turns; compress retrieved chunks to key sentences
- **When to retrieve**: not every turn needs retrieval — context engineering decides when

**Example — clinical agent with 200K token context:**

Bad context engineering:
```
[Full 6-month patient history] [All 47 lab results] [Full medication list since birth]
→ 180K tokens, model's attention diluted, slow, expensive
```

Good context engineering:
```
[Last 3 visits, summarized: 800 tokens]
[Labs from last 30 days, flagged values only: 400 tokens]  
[Current medication list: 200 tokens]
[Semantic search result for current query: 1,200 tokens]
→ 2,600 tokens, focused, fast, cheaper
```

Context engineering is the primary lever for cost, latency, and accuracy optimization in production agents.

---

## Section 2: Vector Embeddings, Prompt & Context Engineering (Q16–Q25)

---

### Q16. Explain the difference between sparse and dense retrieval. When would you use hybrid search?

**Answer:**

**Sparse retrieval (BM25/TF-IDF):**
- Represents documents as bags of words; matches on exact keyword overlap
- Fast, interpretable, no ML required
- Fails on synonyms, paraphrases, semantic similarity

**Dense retrieval (embeddings):**
- Represents documents as continuous vectors; matches on semantic similarity
- Handles synonyms, related concepts, intent-based search
- Requires embedding model; more expensive to build index

**Hybrid search:** combines both — BM25 score + semantic similarity score, fused via Reciprocal Rank Fusion (RRF) or linear combination.

**When to use hybrid (almost always in production):**
- Medical terminology: "MI" vs "myocardial infarction" — sparse misses the semantic link, dense catches it
- Drug names: "Tylenol" vs "acetaminophen" — sparse won't match unless both terms are in the document
- Exact codes: ICD-10 code "E11.9" — dense embeddings often mis-cluster codes; sparse exact match wins here

**Azure AI Search** supports hybrid search natively: `search_mode=All` with `vector` parameter combines BM25 and vector retrieval with RRF.

---

### Q17. What embedding model would you choose for a clinical text search system, and why?

**Answer:**

General-purpose models (OpenAI text-embedding-ada-002, text-embedding-3-large) are trained on web text and underperform on clinical language.

**Recommended options:**

| Model | Strengths | Dimensions |
|---|---|---|
| **BioBERT / PubMedBERT** | Pretrained on PubMed + PMC clinical notes; strong on biomedical NER and similarity | 768 |
| **ClinicalBERT** | Fine-tuned on MIMIC-III discharge notes; strong on clinical documentation | 768 |
| **MedCPT** | Contrastively trained for medical question-answer retrieval; strong for patient queries | 768 |
| **OpenAI text-embedding-3-large** | General, strong; reasonable on clinical text; easy to integrate | 3072 |
| **Azure OpenAI embeddings** | Same as OpenAI but within Azure VNet — required for HIPAA compliance | 1536/3072 |

**Production choice for HIPAA-compliant system on Azure:**
- Primary: Azure OpenAI `text-embedding-3-large` (stays within Azure tenant, no data leaves VNet)
- Fine-tune on anonymized clinical documents if budget allows (15-25% retrieval improvement)
- Evaluate with nDCG@10 on a held-out clinical question set before deploying

---

### Q18. How do you handle chunking strategy for long medical documents in a RAG system?

**Answer:**

Chunking is critical — too large and retrieval is noisy; too small and context is lost.

**Strategies:**

**Fixed-size chunking** — simple, fast, breaks semantic units
- Avoid for clinical documents (a sentence about dosing may be split mid-thought)

**Sentence-level chunking** — respects semantic units, fast with spaCy/NLTK
- Good baseline for clinical notes

**Section-aware chunking** (best for clinical docs):
- Parse SOAP notes, discharge summaries, and clinical reports by section headers
- Each section (Chief Complaint, HPI, Assessment, Plan) becomes its own chunk
- Add section type as metadata for filtering: `{"section": "Assessment", "doc_type": "discharge_summary"}`

**Hierarchical chunking (parent-child):**
```
Parent chunk: Full section (1000 tokens) — for broad retrieval
Child chunks: Sentences within section (100-200 tokens) — for precise retrieval

Retrieval: search child chunks → return parent chunk as context
→ Best of both: precise matching, complete context
```

**Overlap sliding window:**
- 20-30% overlap between chunks prevents information loss at boundaries
- Use for continuous narrative text (progress notes)

**Azure AI Search implementation:**
- Store both parent and child chunk IDs
- `chunk_id`, `parent_chunk_id`, `section_type`, `document_id` as filterable fields
- Retrieve child, return parent for LLM context

---

### Q19. How do you measure and improve retrieval quality in a RAG system?

**Answer:**

**Offline metrics (before deployment):**

| Metric | Formula | What it measures |
|---|---|---|
| **Recall@K** | Relevant docs retrieved / Total relevant | Are relevant docs found at all? |
| **Precision@K** | Relevant retrieved / K | Are retrieved docs relevant? |
| **nDCG@K** | Normalized Discounted Cumulative Gain | Are relevant docs ranked higher? |
| **MRR** | Mean Reciprocal Rank | How high is the first relevant doc? |

**Online metrics (in production):**
- **Faithfulness** — does the answer only use information in the retrieved context? (LLM-as-judge)
- **Answer relevance** — does the answer address the user's question? (LLM-as-judge)
- **Context precision** — of retrieved chunks, how many were actually used by the model?
- **User feedback** — thumbs up/down, correction rate, escalation rate

**Improvement levers:**

| Problem | Fix |
|---|---|
| Recall too low | Better chunking, domain-tuned embeddings, increase K |
| Precision too low | Metadata filters, re-ranking (Cohere Rerank, BGE-Reranker) |
| Wrong semantics | Fine-tune embedding model on domain data |
| Stale results | Re-indexing pipeline with change detection |
| Slow | ANN index tuning (HNSW parameters), caching frequent queries in Redis |

---

### Q20. What is the difference between zero-shot, few-shot, and fine-tuning for production AI systems?

**Answer:**

| Approach | What You Provide | When To Use | Cost |
|---|---|---|---|
| **Zero-shot** | Task description only | Task is well-defined and model is capable | Lowest |
| **Few-shot** | 3-10 input/output examples in prompt | When output format/style must be consistent | Low |
| **Fine-tuning** | Thousands of labeled examples, training run | When zero/few-shot fail; domain-specific style | High |

**Decision framework:**

1. Try zero-shot first with a strong model (GPT-4o, Claude Sonnet)
2. If format/style is inconsistent → add few-shot examples
3. If few-shot is still insufficient after prompt optimization → fine-tune
4. If you need latency/cost reduction after quality is achieved → fine-tune a smaller model to match the larger one's performance (distillation)

**Healthcare example:**
- Extracting ICD codes from clinical notes: few-shot works well with 5-10 examples showing the exact format expected
- Detecting PHI for de-identification: fine-tuned NER model outperforms few-shot LLM on precision (critical for compliance)

---

### Q21. How do you handle hallucination in a RAG-based clinical decision support system?

**Answer:**

**Detection:**
- **Faithfulness check**: after generating, re-prompt the model: "Is every claim in this response supported by the retrieved context? List any unsupported claims."
- **Entailment model**: a dedicated NLI (natural language inference) model checks whether each claim in the output is entailed by retrieved chunks
- **Citation grounding**: require the model to cite a specific chunk ID for each factual claim; validate that the cited chunk contains the claim

**Prevention:**
- **Restrictive system prompt**: "Answer ONLY using information in the provided context. If the context doesn't contain the answer, say so."
- **Structured output**: require the model to produce JSON with `answer` and `source_chunk_ids` fields; reject if source is missing
- **Confidence gating**: if retrieval score is below threshold, refuse to answer and route to human

**Azure implementation:**
```python
def safe_clinical_rag(query, retrieved_chunks, llm):
    response = llm(f"""
    Context (only use this):
    {format_chunks(retrieved_chunks)}
    
    Question: {query}
    
    Instructions:
    - Answer using ONLY the provided context
    - For each fact, cite the chunk_id in brackets: [chunk_3]
    - If context is insufficient, respond: "INSUFFICIENT CONTEXT"
    """)
    
    if "INSUFFICIENT CONTEXT" in response:
        return route_to_human(query, retrieved_chunks)
    
    # Validate citations exist
    cited_ids = extract_citation_ids(response)
    validate_citations(cited_ids, retrieved_chunks)
    
    return response
```

---

### Q22. What is a system prompt and how do you design one for a production agentic system?

**Answer:**

The system prompt is the highest-trust instruction layer — it defines the agent's identity, capabilities, constraints, and output format. It persists across the entire conversation.

**Production system prompt structure:**

```
1. ROLE & IDENTITY
   Who the agent is, what it specializes in, its authority level

2. CAPABILITIES
   What tools are available and when to use each

3. CONSTRAINTS (the most important section)
   - What the agent must NOT do
   - What requires human escalation
   - PHI/PII handling rules
   - Tone and formality requirements

4. OUTPUT FORMAT
   Exact structure expected (JSON schema, section headers)

5. ERROR HANDLING
   What to do when tools fail, context is insufficient, confidence is low

6. FEW-SHOT EXAMPLES (optional but powerful)
   1-3 canonical examples of good input → output
```

**Example for clinical documentation agent:**
```
You are a clinical documentation assistant for licensed healthcare providers.
You help extract structured information from clinical notes and patient records.

CAPABILITIES:
- You can query patient records via FHIR tools
- You can search clinical guidelines via the knowledge base tool
- You can flag items for physician review

CONSTRAINTS:
- Never provide a clinical diagnosis
- Never recommend treatment changes without physician confirmation
- Always cite the source document for every extracted fact
- If a query involves PHI, verify the requestor has been authenticated before responding
- Escalate to human when: confidence < 0.8, conflicting information found, urgent safety concern

OUTPUT FORMAT:
Return structured JSON: {"extracted_fields": {...}, "citations": [...], "flags": [...]}
```

---

### Q23. How do you optimize token cost for a high-volume agentic system?

**Answer:**

**Prompt compression:**
- Summarize long conversation history into a compressed form every N turns
- Use a cheap model (GPT-4o-mini, Claude Haiku) for summarization before sending to expensive model
- Remove redundant retrieved chunks — if the same document is retrieved 3 times, deduplicate

**Model routing:**
- Route simple tasks (classification, extraction) to cheap small models
- Route complex reasoning to expensive large models
- A classifier (or even a rules-based router) decides which tier each query goes to

**Caching:**
- Cache responses for identical or near-identical queries (semantic cache with Redis + vector similarity)
- Cache embedding computations — don't re-embed the same document chunks
- Azure AI Search caches search results for 30s by default; tune the TTL

**Prompt caching:**
- Anthropic's prompt caching: if the system prompt + static context is the same across requests, cache it (90% cost reduction on cached tokens)
- Structure prompts so static content (system prompt, tools, documents) comes first — this is what gets cached

**Batch processing:**
- For non-real-time tasks (nightly report generation), use the Anthropic/OpenAI batch API — 50% cost reduction, no rate limit pressure

**Monitoring:**
- Track tokens per step, per agent, per task type
- Set cost budgets per task; abort if exceeded
- Alert on anomalous token consumption (possible loop)

---

### Q24. How do you design a reranking step to improve RAG precision?

**Answer:**

Initial vector retrieval (top-K) maximizes recall but trades off precision — some retrieved chunks are semantically similar to the query but not actually useful for answering it. A reranker takes the top-K candidates and reorders them by relevance to the specific query.

**Reranking models:**
- **Cohere Rerank** — API-based, state of the art for general text
- **BGE-Reranker-Large** — open source, strong multilingual
- **Cross-encoder models** — encode query + document together (more accurate but slower than bi-encoders)

**Pipeline:**
```
Query
  ↓
Vector search → top-50 candidates (high recall, mixed precision)
  ↓
Reranker → scores each of 50 candidates against query
  ↓
Top-5 reranked results (high precision)
  ↓
LLM generation with top-5 context
```

**Azure implementation:**
```python
from azure.search.documents import SearchClient
import cohere

def reranked_rag(query: str, search_client: SearchClient, co: cohere.Client):
    # Step 1: broad retrieval
    results = search_client.search(
        search_text=query,
        vector=embed(query),
        top=50  # retrieve many candidates
    )
    candidates = [(r["chunk_id"], r["content"]) for r in results]
    
    # Step 2: rerank
    reranked = co.rerank(
        query=query,
        documents=[c[1] for c in candidates],
        top_n=5,
        model="rerank-english-v3.0"
    )
    
    top_chunks = [candidates[r.index][1] for r in reranked.results]
    return top_chunks
```

**Measured improvement:** reranking typically improves nDCG@5 by 15-30% over vector search alone.

---

### Q25. What is the lost-in-the-middle problem and how does it affect RAG system design?

**Answer:**

Research (Liu et al., 2023) showed that LLMs perform best when relevant information is at the **beginning or end** of the context window — information in the middle receives less attention and is more likely to be ignored.

**Impact on RAG:**
- If you retrieve 10 chunks and the relevant one is chunk #5, the model may fail to use it
- Longer contexts amplify the problem

**Mitigations:**

1. **Put the most relevant chunk first** — sort retrieved chunks by relevance score descending before injecting into context

2. **Use fewer, higher-quality chunks** — 3 highly relevant chunks outperform 10 mixed-quality chunks

3. **Reranking** — ensures the highest-scoring chunk is first in context

4. **Relevance-aware truncation** — if context is long, drop the least relevant chunks from the middle, not from the ends

5. **Query decomposition + targeted retrieval** — instead of one query returning 10 chunks, decompose into 3 sub-queries, each retrieving 2 focused chunks

6. **Chunk summarization** — for each retrieved chunk, generate a 1-sentence summary and put that first, then the full chunk — the summary anchors attention

---

## Section 3: Python, Architecture & Azure Cloud (Q26–Q35)

---

### Q26. How do you design a production-grade agentic AI system on Azure? Walk me through the architecture.

**Answer:**

```
┌──────────────────────────────────────────────────────────────────────┐
│                     AZURE AGENTIC AI ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────────┤
│  Client Layer                                                        │
│  Web App / API / EHR Integration                                     │
│  → Azure API Management (rate limiting, auth, routing)              │
├──────────────────────────────────────────────────────────────────────┤
│  Orchestration Layer                                                 │
│  Azure Container Apps — Orchestrator Agent Service                   │
│  → Runs LangGraph or AutoGen orchestrator                           │
│  → Auto-scales 0 → N replicas based on queue depth                  │
├──────────────────────────────────────────────────────────────────────┤
│  Agent Worker Layer                                                  │
│  Azure Container Apps — one Container App per agent type             │
│  → Research Agent, Code Agent, Writer Agent, Review Agent           │
│  → Each independently scalable                                       │
│  Communication: Azure Service Bus (async task queue)                 │
├──────────────────────────────────────────────────────────────────────┤
│  Tool / Integration Layer                                            │
│  Azure Functions — thin wrappers around external APIs               │
│  → FHIR query function, EHR write function, notification function   │
│  → Event-driven, pay-per-execution                                  │
├──────────────────────────────────────────────────────────────────────┤
│  Data Layer                                                          │
│  Azure AI Search    — vector + hybrid search (RAG retrieval)        │
│  Azure Cosmos DB    — agent state, memory, reflections, audit log   │
│  Azure Redis Cache  — semantic cache, rate limiting, session state   │
│  Azure Blob Storage — documents, media, model artifacts             │
├──────────────────────────────────────────────────────────────────────┤
│  LLM Layer                                                           │
│  Azure OpenAI Service — GPT-4o, text-embedding-3-large             │
│  → Private endpoint — no data leaves Azure VNet                     │
│  → PTU (Provisioned Throughput Units) for latency-sensitive paths   │
├──────────────────────────────────────────────────────────────────────┤
│  Observability Layer                                                 │
│  Azure Monitor + Application Insights — traces, metrics, alerts     │
│  Azure Log Analytics — structured logging, dashboards               │
└──────────────────────────────────────────────────────────────────────┘
```

---

### Q27. How do you implement a semantic cache for an LLM-based system using Redis?

**Answer:**

A semantic cache stores previous (query, response) pairs. On a new query, if a semantically similar query was already answered, return the cached response — avoiding an LLM call entirely.

```python
import redis
import numpy as np
from openai import AzureOpenAI

redis_client = redis.Redis(host="your-cache.redis.cache.windows.net", ssl=True)
oai_client = AzureOpenAI(...)
SIMILARITY_THRESHOLD = 0.92

def embed(text: str) -> list[float]:
    return oai_client.embeddings.create(
        model="text-embedding-3-large", input=text
    ).data[0].embedding

def semantic_cache_lookup(query: str) -> str | None:
    query_vec = embed(query)
    
    # Search Redis vector index (Redis Stack with HNSW index)
    results = redis_client.ft("cache_idx").search(
        Query(f"*=>[KNN 1 @embedding $vec AS score]")
        .sort_by("score")
        .return_fields("response", "score")
        .dialect(2),
        query_params={"vec": np.array(query_vec, dtype=np.float32).tobytes()}
    )
    
    if results.docs and float(results.docs[0].score) >= SIMILARITY_THRESHOLD:
        return results.docs[0].response
    return None

def cached_llm_call(query: str) -> str:
    cached = semantic_cache_lookup(query)
    if cached:
        return cached
    
    response = call_llm(query)
    
    # Store in cache with 1-hour TTL
    cache_key = f"cache:{hash(query)}"
    redis_client.hset(cache_key, mapping={
        "query": query,
        "response": response,
        "embedding": np.array(embed(query), dtype=np.float32).tobytes()
    })
    redis_client.expire(cache_key, 3600)
    
    return response
```

**Cost impact:** For FAQ-style queries (high repetition), semantic caching can reduce LLM calls by 40-60%.

---

### Q28. How do you handle rate limiting and backpressure in a high-throughput agent system?

**Answer:**

Azure OpenAI has TPM (tokens per minute) and RPM (requests per minute) limits. Exceeding them causes 429 errors.

**Strategy stack:**

**1. Token budget per request** — estimate token count before sending, queue if would exceed budget

**2. Exponential backoff with jitter:**
```python
import time, random

def call_with_retry(fn, max_retries=5):
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
    raise MaxRetriesExceeded()
```

**3. Azure Service Bus for async queuing:**
- Agents submit tasks to a Service Bus queue
- A pool of workers pulls tasks; if Azure OpenAI returns 429, the message stays in queue and is retried after visibility timeout

**4. Model tiering:**
- Route low-priority tasks to a lower-tier deployment with separate TPM quota
- High-priority (real-time user-facing) tasks use dedicated PTU deployment (no rate limits)

**5. Semantic caching (Q27)** — reduces raw call volume

**6. Batch API:**
- Non-real-time tasks (nightly processing) use the batch endpoint — no rate limits, 50% cost reduction, 24h SLA

---

### Q29. Explain the difference between Azure Container Apps and Azure Functions. When do you use each for an agentic system?

**Answer:**

| Dimension | Azure Functions | Azure Container Apps |
|---|---|---|
| Model | Serverless, event-triggered, stateless | Container-based, can be stateful, long-running |
| Cold start | Yes (consumption plan) | No (always-on option) |
| Max execution | 10 minutes (consumption) | Unlimited |
| Scaling | 0 → N instantaneous | 0 → N with KEDA |
| Best for | Short, event-driven, discrete tasks | Long-running services, agent workers, web APIs |
| Cost | Pay per execution | Pay per vCPU/memory-hour |

**In an agentic system:**

**Use Azure Functions for:**
- Tool wrappers: `fhir_query()`, `send_notification()`, `validate_schema()`
- Event triggers: "when a new document arrives in Blob Storage, chunk and index it"
- Lightweight transformations between agent steps
- Webhook receivers (EHR system sends a webhook → Function triggers agent)

**Use Azure Container Apps for:**
- Agent workers that run LangGraph/AutoGen loops (can run for minutes)
- The orchestrator service (long-lived, handles many concurrent agent runs)
- API servers exposing agent capabilities
- MCP servers (need to be always available, not serverless)

**Typical architecture:**
```
[Azure Container App — Orchestrator] 
    → delegates via Service Bus
    → [Azure Container App — Agent Workers]
    → calls tool via HTTP
    → [Azure Function — Tool: fhir_query]
```

---

### Q30. How do you implement streaming responses for an agent that has multiple tool calls before producing a final answer?

**Answer:**

Users experience poor UX if they see nothing for 30+ seconds while an agent does multi-step reasoning. Streaming intermediate steps solves this.

**Architecture:**
```
Client ←— SSE stream ←— API Gateway ←— Orchestrator Container App
                                              ↓ writes events
                                        Azure Redis Pub/Sub
                                              ↑ publishes events
                                        Agent Worker
```

**Agent publishes events at each step:**
```python
from azure.core.messaging import CloudEvent
import redis

pubsub = redis.Redis(...)

def agent_loop(task_id, query):
    pubsub.publish(task_id, json.dumps({
        "type": "thought",
        "content": "I need to look up the patient's lab history"
    }))
    
    result = tool_fhir_query(patient_id=...)
    
    pubsub.publish(task_id, json.dumps({
        "type": "tool_result",
        "tool": "fhir_query",
        "summary": f"Found {len(result)} lab results"
    }))
    
    final_answer = llm_generate(result)
    
    pubsub.publish(task_id, json.dumps({
        "type": "final_answer",
        "content": final_answer
    }))
```

**API Gateway relays as SSE:**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.get("/stream/{task_id}")
async def stream(task_id: str):
    async def event_generator():
        sub = redis.pubsub()
        sub.subscribe(task_id)
        for message in sub.listen():
            if message["type"] == "message":
                yield f"data: {message['data'].decode()}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

### Q31. How would you implement a circuit breaker for an LLM-dependent agent service?

**Answer:**

A circuit breaker prevents a failing dependency (LLM API, external tool) from cascading into system-wide failure.

**States:** `CLOSED` (normal) → `OPEN` (failing, reject fast) → `HALF-OPEN` (testing recovery)

```python
import time
from enum import Enum

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, success_threshold=2):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state = State.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def call(self, fn, *args, **kwargs):
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = State.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit is open — failing fast")
        
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        if self.state == State.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = State.CLOSED
                self.failure_count = 0
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = State.OPEN

# Usage
llm_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
response = llm_breaker.call(azure_openai_client.chat.completions.create, ...)
```

**When circuit opens:** route to fallback (simpler model, cached response, human queue).

---

### Q32. How do you design for observability in a multi-agent system?

**Answer:**

**Three pillars:**

**1. Distributed Tracing (spans)**
Every agent action is a span. Spans are nested: the orchestrator span contains child spans for each subagent, which contain child spans for each tool call.

```python
from opentelemetry import trace

tracer = trace.get_tracer("agent.orchestrator")

with tracer.start_as_current_span("orchestrator.run") as span:
    span.set_attribute("task_id", task_id)
    span.set_attribute("user_id", user_id)
    
    with tracer.start_as_current_span("subagent.research") as sub_span:
        sub_span.set_attribute("query", research_query)
        result = research_agent.run(research_query)
        sub_span.set_attribute("chunks_retrieved", len(result.chunks))
```

Send to Azure Monitor via OpenTelemetry exporter → view in Application Insights end-to-end transaction map.

**2. Structured Logging**
```python
import structlog

log = structlog.get_logger()
log.info("tool_call", tool="fhir_query", patient_id=pid, 
         latency_ms=elapsed, success=True, result_count=len(results))
```

**3. Metrics**
- `agent.task.duration` — histogram by agent type
- `agent.tool.calls` — counter by tool name
- `agent.token.usage` — counter by model, input/output
- `agent.error.rate` — counter by error type
- `agent.escalation.rate` — counter (human review triggered)

All shipped to Azure Monitor; alerts configured for anomaly thresholds.

---

### Q33. How do you version and deploy updates to a production agent system with zero downtime?

**Answer:**

**Challenges specific to agents:**
- Changing the system prompt changes behavior — like a code change but harder to test
- Tool schema changes can break the agent's ability to call tools correctly
- Memory format changes can invalidate existing stored memories

**Deployment strategy:**

**1. Shadow mode:** new agent version runs in parallel with production, receives same inputs, results are compared but not served to users. Promotes only when quality parity (or improvement) is confirmed.

**2. Canary deployment via Azure Container Apps:**
- Deploy new version as a revision
- Route 5% of traffic to new revision
- Monitor error rate, task completion rate, user feedback
- Ramp to 100% if metrics are healthy

```bash
az containerapp revision set-mode \
  --name my-agent-app \
  --resource-group rg-prod \
  --mode multiple

# Set traffic split
az containerapp ingress traffic set \
  --name my-agent-app \
  --revision-weight stable=95 canary=5
```

**3. Prompt versioning:**
- Store all system prompts in Azure Cosmos DB with version IDs
- Agent fetches its prompt at startup from config (not hardcoded)
- Roll back by updating config to previous version ID

**4. Tool schema migration:**
- Add new tool schema alongside old one; agent supports both for one release cycle
- Remove old schema in next release (blue-green)

---

### Q34. Describe how you would implement async, parallel tool execution in Python for an agent.

**Answer:**

In a ReAct loop, when the model requests multiple independent tools, running them in parallel cuts latency proportionally.

```python
import asyncio
from typing import Callable

async def execute_tools_parallel(tool_calls: list[dict]) -> list[dict]:
    """Execute independent tool calls concurrently."""
    
    async def run_tool(tool_call: dict) -> dict:
        tool_name = tool_call["tool"]
        params = tool_call["parameters"]
        
        # Each tool wrapped as async function
        fn: Callable = TOOL_REGISTRY[tool_name]
        result = await fn(**params)
        
        return {
            "tool": tool_name,
            "call_id": tool_call["call_id"],
            "result": result
        }
    
    # Run all tool calls concurrently
    results = await asyncio.gather(
        *[run_tool(tc) for tc in tool_calls],
        return_exceptions=True  # don't let one failure abort all
    )
    
    # Separate successes from failures
    observations = []
    for tc, result in zip(tool_calls, results):
        if isinstance(result, Exception):
            observations.append({
                "tool": tc["tool"],
                "call_id": tc["call_id"],
                "error": str(result)
            })
        else:
            observations.append(result)
    
    return observations

# Example: agent model returns two tool calls
tool_calls = [
    {"tool": "fhir_query", "call_id": "1", "parameters": {"patient_id": "P123", "resource": "Observation"}},
    {"tool": "search_guidelines", "call_id": "2", "parameters": {"query": "warfarin monitoring CKD"}}
]

# Run in parallel — total time = max(tool1_time, tool2_time) instead of sum
observations = asyncio.run(execute_tools_parallel(tool_calls))
```

**For Azure Container Apps:** each async task can be a separate coroutine; the event loop handles multiplexing. For truly independent heavy workloads, dispatch to separate agent workers via Service Bus and await their completion events.

---

### Q35. How do you implement a cost-aware agent that stops itself before exceeding a budget?

**Answer:**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class BudgetTracker:
    max_tokens: int = 100_000
    max_cost_usd: float = 0.50
    max_steps: int = 20
    
    tokens_used: int = 0
    cost_usd: float = 0.0
    steps_taken: int = 0
    
    # Azure OpenAI pricing (example)
    INPUT_PRICE_PER_1K = 0.005   # GPT-4o
    OUTPUT_PRICE_PER_1K = 0.015

    def record_llm_call(self, input_tokens: int, output_tokens: int):
        self.tokens_used += input_tokens + output_tokens
        self.cost_usd += (input_tokens / 1000 * self.INPUT_PRICE_PER_1K +
                          output_tokens / 1000 * self.OUTPUT_PRICE_PER_1K)
        self.steps_taken += 1
    
    @property
    def budget_exceeded(self) -> Optional[str]:
        if self.tokens_used > self.max_tokens:
            return f"Token budget exceeded: {self.tokens_used}/{self.max_tokens}"
        if self.cost_usd > self.max_cost_usd:
            return f"Cost budget exceeded: ${self.cost_usd:.4f}/${self.max_cost_usd}"
        if self.steps_taken >= self.max_steps:
            return f"Step limit reached: {self.steps_taken}/{self.max_steps}"
        return None

def agent_loop_with_budget(task: str, budget: BudgetTracker):
    context = [{"role": "user", "content": task}]
    
    while True:
        if reason := budget.budget_exceeded:
            return {"status": "budget_exceeded", "reason": reason,
                    "partial_result": context[-1]["content"]}
        
        response = call_llm(context)
        budget.record_llm_call(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )
        
        if response.is_final:
            return {"status": "complete", "result": response.content,
                    "cost_usd": budget.cost_usd}
        
        # Execute tools, add observations, continue loop
        observations = execute_tools(response.tool_calls)
        context.extend(format_observations(observations))
```

---

## Section 4: Databases — Azure AI Search, Redis, Cosmos DB (Q36–Q43)

---

### Q36. How do you design an Azure AI Search index for a clinical RAG system?

**Answer:**

```json
{
  "name": "clinical-knowledge-index",
  "fields": [
    {"name": "chunk_id",       "type": "Edm.String", "key": true},
    {"name": "parent_doc_id",  "type": "Edm.String", "filterable": true},
    {"name": "content",        "type": "Edm.String", "searchable": true, "analyzer": "en.microsoft"},
    {"name": "content_vector", "type": "Collection(Edm.Single)", "dimensions": 3072,
     "vectorSearchProfile": "hnsw-profile"},
    {"name": "section_type",   "type": "Edm.String", "filterable": true, "facetable": true},
    {"name": "doc_type",       "type": "Edm.String", "filterable": true},
    {"name": "source_system",  "type": "Edm.String", "filterable": true},
    {"name": "patient_id",     "type": "Edm.String", "filterable": true},
    {"name": "encounter_date", "type": "Edm.DateTimeOffset", "filterable": true, "sortable": true},
    {"name": "icd10_codes",    "type": "Collection(Edm.String)", "filterable": true},
    {"name": "last_updated",   "type": "Edm.DateTimeOffset", "filterable": true}
  ],
  "vectorSearch": {
    "profiles": [{"name": "hnsw-profile", "algorithm": "hnsw-config"}],
    "algorithms": [{"name": "hnsw-config", "kind": "hnsw", 
                    "hnswParameters": {"m": 4, "efConstruction": 400, "efSearch": 500}}]
  },
  "semantic": {
    "configurations": [{"name": "clinical-semantic", 
                        "prioritizedFields": {"contentFields": [{"fieldName": "content"}]}}]
  }
}
```

**Key design decisions:**
- `patient_id` as filterable field — always pre-filter on patient_id before semantic search (security + relevance)
- HNSW index tuned for recall: `efSearch=500` (higher = better recall, more latency)
- Semantic configuration enables BM25 + neural re-ranking in one call
- `icd10_codes` as filterable collection — retrieve all chunks tagged with specific diagnoses

---

### Q37. When would you use Cosmos DB vs Azure AI Search vs Redis in an agentic system?

**Answer:**

| Data Type | Service | Why |
|---|---|---|
| Agent state (current task, step number, context) | **Cosmos DB** | Transactional, document model, globally distributed, TTL |
| Conversation history (sessions) | **Cosmos DB** | Document model, queryable by user_id, session_id |
| Agent reflections / lessons learned | **Cosmos DB** + **AI Search** | Store in Cosmos, index in AI Search for semantic retrieval |
| Knowledge base (documents, guidelines, policies) | **Azure AI Search** | Vector + hybrid search, semantic ranking |
| Semantic cache (query → response) | **Redis** | Sub-millisecond reads, vector similarity, TTL-based eviction |
| Session state (short-lived, current user context) | **Redis** | Low latency, auto-expiry, pub/sub for streaming |
| Audit log (immutable record of agent actions) | **Cosmos DB** | Append-only pattern, long retention, queryable |
| Large file storage (PDFs, audio, model artifacts) | **Blob Storage** | Cheapest per-GB, CDN integration |

---

### Q38. How do you implement partitioning in Cosmos DB for an agent memory system serving millions of users?

**Answer:**

**Partition key selection is the most critical decision.**

**Option A: partition by `user_id`**
- All memories for a user are co-located — efficient reads for single-user queries
- Hot partition risk if some users have massive history
- Good for: personal assistant applications

**Option B: partition by `memory_type + user_id` composite**
- Spreads load across memory types
- More predictable partition sizes
- Slightly more complex queries across types

**Option C: partition by `tenant_id` (for B2B SaaS)**
- Co-locates all data for a healthcare organization
- Enables tenant-level operations (purge all PHI for a client)

**For a healthcare multi-tenant agent system:**
```python
# Document structure
memory_doc = {
    "id": str(uuid4()),
    "partitionKey": f"{tenant_id}:{user_id}",  # composite
    "tenant_id": tenant_id,
    "user_id": user_id,
    "memory_type": "episodic",  # or "semantic", "reflection"
    "content": "Patient mentioned penicillin allergy during intake",
    "embedding": [...],  # for in-cosmos vector search (preview)
    "tags": ["allergy", "medication"],
    "timestamp": datetime.utcnow().isoformat(),
    "ttl": 60 * 60 * 24 * 365 * 7  # 7-year HIPAA retention
}

container.upsert_item(memory_doc)
```

**HIPAA consideration:** Enable Cosmos DB customer-managed keys (CMK) so PHI at rest is encrypted with keys you control. Enable diagnostic logs and ship to Azure Monitor for audit compliance.

---

### Q39. How do you implement change data capture from Cosmos DB to keep Azure AI Search in sync?

**Answer:**

The **Cosmos DB change feed** streams all document insertions and updates in order. Use it to keep the AI Search index current without polling.

```
[Agent writes memory doc to Cosmos DB]
        ↓
[Cosmos DB Change Feed]
        ↓
[Azure Function — Change Feed Trigger]
        ↓
  Reads new/updated document
  Generates embedding via Azure OpenAI
  Upserts into Azure AI Search index
```

**Azure Function implementation:**
```python
import azure.functions as func
from azure.search.documents import SearchClient
from openai import AzureOpenAI

@func.cosmos_db_trigger(arg_name="docs", 
                         database_name="agent-memory",
                         collection_name="memories",
                         connection="CosmosConnection",
                         lease_collection_name="leases",
                         create_lease_collection_if_not_exists=True)
def sync_to_search(docs: func.DocumentList) -> None:
    oai = AzureOpenAI(...)
    search = SearchClient(endpoint=SEARCH_ENDPOINT, 
                          index_name="memories", 
                          credential=SEARCH_KEY)
    
    batch = []
    for doc in docs:
        embedding = oai.embeddings.create(
            model="text-embedding-3-large",
            input=doc["content"]
        ).data[0].embedding
        
        batch.append({
            "chunk_id": doc["id"],
            "user_id": doc["user_id"],
            "content": doc["content"],
            "content_vector": embedding,
            "memory_type": doc["memory_type"],
            "timestamp": doc["timestamp"]
        })
    
    search.upload_documents(batch)
```

This gives you near-real-time search index updates with zero polling.

---

### Q40. How do you use Redis for agent session management in a multi-agent system?

**Answer:**

Session management challenges in multi-agent:
- An agent loop may span multiple HTTP requests (async, long-running)
- Multiple subagents need shared context
- Session must survive container restarts

**Redis data structure per session:**
```python
import redis, json
from datetime import timedelta

r = redis.Redis(host="cache.redis.cache.windows.net", ssl=True)

SESSION_TTL = timedelta(hours=2)

class AgentSession:
    def __init__(self, session_id: str):
        self.key = f"session:{session_id}"
        self.session_id = session_id
    
    def get_state(self) -> dict:
        raw = r.hgetall(self.key)
        return {k.decode(): json.loads(v) for k, v in raw.items()}
    
    def set_step(self, step: int, thought: str, action: dict, observation: dict):
        r.hset(self.key, mapping={
            f"step:{step}:thought": json.dumps(thought),
            f"step:{step}:action": json.dumps(action),
            f"step:{step}:observation": json.dumps(observation),
            "current_step": json.dumps(step)
        })
        r.expire(self.key, SESSION_TTL)
    
    def get_context_window(self, last_n: int = 5) -> list[dict]:
        state = self.get_state()
        current = json.loads(state.get("current_step", "0"))
        steps = []
        for i in range(max(0, current - last_n + 1), current + 1):
            if f"step:{i}:thought" in state:
                steps.append({
                    "thought": json.loads(state[f"step:{i}:thought"]),
                    "action": json.loads(state[f"step:{i}:action"]),
                    "observation": json.loads(state[f"step:{i}:observation"])
                })
        return steps
```

**Pub/Sub for agent-to-agent coordination:**
```python
# Orchestrator publishes task completion events
r.publish(f"agent:events:{task_id}", json.dumps({
    "event": "subagent_complete",
    "subagent": "research",
    "result_key": f"result:{task_id}:research"
}))

# Worker subagent subscribes and reacts
pubsub = r.pubsub()
pubsub.subscribe(f"agent:events:{task_id}")
for message in pubsub.listen():
    event = json.loads(message["data"])
    # process event
```

---

### Q41. What is Azure Blob Storage Iceberg and when would you use it over Cosmos DB?

**Answer:**

**Apache Iceberg** is an open table format for large-scale analytical data. Azure Blob Storage (ADLS Gen2) can host Iceberg tables, making them queryable via Apache Spark, Azure Databricks, or Microsoft Fabric.

**Iceberg on Azure Blob provides:**
- ACID transactions on massive datasets (petabyte scale)
- Time travel — query data as it was at any point in time
- Schema evolution without rewriting data
- Partition pruning for fast analytical queries

**When to use Iceberg (Blob):**

| Use Case | Iceberg | Cosmos DB |
|---|---|---|
| Petabyte-scale audit logs | ✅ | ❌ (cost-prohibitive) |
| Historical trend analysis (agent performance over months) | ✅ | ❌ |
| Training data storage for model fine-tuning | ✅ | ❌ |
| Time-travel queries ("what did the agent know on Nov 1?") | ✅ | ❌ |
| Transactional writes, millisecond reads | ❌ | ✅ |
| Real-time agent state | ❌ | ✅ |

**In an agentic system:** Use Iceberg/Blob for the **analytics and compliance layer** — store all agent actions as Iceberg tables for retrospective analysis, model evaluation, and regulatory audit. Use Cosmos DB for the **operational layer** — real-time state, session management, memory.

---

### Q42. How do you implement vector search in Azure AI Search for a hybrid RAG query?

**Answer:**

```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

def hybrid_search(
    query: str,
    patient_id: str,
    doc_types: list[str] = None,
    top_k: int = 10
) -> list[dict]:
    
    oai = AzureOpenAI(...)
    search = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name="clinical-knowledge",
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # Generate query embedding
    query_vector = oai.embeddings.create(
        model="text-embedding-3-large",
        input=query
    ).data[0].embedding
    
    # Build filter (always restrict to patient's data)
    filters = [f"patient_id eq '{patient_id}'"]
    if doc_types:
        type_filter = " or ".join(f"doc_type eq '{t}'" for t in doc_types)
        filters.append(f"({type_filter})")
    
    # Hybrid search: BM25 + vector + semantic reranking
    results = search.search(
        search_text=query,           # BM25 component
        vector_queries=[VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k * 3,  # retrieve more candidates for reranking
            fields="content_vector"
        )],
        filter=" and ".join(filters),
        query_type="semantic",       # semantic reranking on top
        semantic_configuration_name="clinical-semantic",
        top=top_k,
        select=["chunk_id", "content", "doc_type", "section_type", 
                "encounter_date", "parent_doc_id"]
    )
    
    return [
        {
            "chunk_id": r["chunk_id"],
            "content": r["content"],
            "score": r["@search.reranker_score"],
            "doc_type": r["doc_type"]
        }
        for r in results
    ]
```

---

### Q43. How would you design a caching strategy across Redis, Cosmos DB, and Blob Storage for an agent system?

**Answer:**

```
Cache Tier    │ Service         │ What's Cached         │ TTL
──────────────┼─────────────────┼───────────────────────┼──────────
L1 (hot)      │ Redis           │ Semantic query cache   │ 1 hour
              │                 │ Session state          │ 2 hours
              │                 │ Frequently-read facts  │ 30 min
──────────────┼─────────────────┼───────────────────────┼──────────
L2 (warm)     │ Cosmos DB       │ Agent memory/state     │ Per policy
              │                 │ User preferences       │ 30 days
              │                 │ Conversation summaries │ 90 days
──────────────┼─────────────────┼───────────────────────┼──────────
L3 (cold)     │ Blob Storage    │ Full conversation logs │ 7 years
              │                 │ Document corpus        │ Indefinite
              │                 │ Model artifacts        │ Versioned
```

**Cache invalidation strategy:**
- When a document is updated → invalidate Redis L1 cache for related queries (use Redis keyspace events)
- When agent state changes → Cosmos DB is source of truth; Redis is populated on next read (lazy loading)
- Blob Storage documents are immutable (versioned); old versions never invalidated, new versions indexed

**Cache warming:**
- On service startup: pre-load top-100 most frequent clinical queries into Redis from Cosmos DB analytics
- Predictive warming: if a patient has a scheduled appointment, pre-load their relevant records into Redis 5 minutes before

---

## Section 5: Azure Functions, Container Apps & Cloud-Native (Q44–Q48)

---

### Q44. How do you scale an agent worker pool using KEDA with Azure Container Apps?

**Answer:**

KEDA (Kubernetes Event-Driven Autoscaling) allows Container Apps to scale based on external event sources — perfect for scaling agent workers based on queue depth.

```yaml
# containerapp.yaml
properties:
  template:
    scale:
      minReplicas: 1
      maxReplicas: 50
      rules:
        - name: servicebus-scaler
          custom:
            type: azure-servicebus
            metadata:
              queueName: agent-tasks
              namespace: my-servicebus-namespace
              messageCount: "5"  # scale up when queue depth > 5 messages per replica
            auth:
              - secretRef: servicebus-connection
                triggerParameter: connection
```

**Behavior:**
- 0 messages in queue → scale to minReplicas (1, to avoid cold start)
- 50 messages → scale to 10 replicas (50/5 = 10)
- 500 messages → scale to maxReplicas (50)
- Queue drains → scale back to 1

**For healthcare:** HIPAA requires audit trails for autoscaling events — configure Container Apps diagnostics to Log Analytics; alert on unexpected scale-out (potential cost anomaly or runaway agent).

---

### Q45. How do you implement a durable agent workflow using Azure Durable Functions?

**Answer:**

Durable Functions add state, orchestration, and long-running capability to the serverless model — useful for agent workflows that span minutes or hours.

```python
import azure.durable_functions as df

# Orchestrator function — runs the agent loop durably
def orchestrator(context: df.DurableOrchestrationContext):
    task_input = context.get_input()
    
    # Durable: survives restarts, replays history to restore state
    plan = yield context.call_activity("planner_agent", task_input)
    
    # Run independent steps in parallel (durable fan-out)
    parallel_tasks = [
        context.call_activity("research_agent", step)
        for step in plan["parallel_steps"]
    ]
    results = yield context.task_all(parallel_tasks)
    
    # Sequential synthesis
    summary = yield context.call_activity("synthesis_agent", {
        "plan": plan,
        "results": results
    })
    
    # Wait for human approval (can wait days without consuming resources)
    approval_event = context.wait_for_external_event("human_approval")
    approved = yield context.create_timer(
        context.current_utc_datetime + timedelta(hours=48)
    ) if not approval_event else approval_event
    
    if approved:
        yield context.call_activity("write_to_ehr", summary)
    
    return summary

# Register orchestrator
main = df.Orchestrator.create(orchestrator)
```

**Benefits over Container Apps for this:**
- No charge when waiting for human approval (serverless billing)
- Automatic replay on failure — no lost progress
- Built-in timeout and retry patterns

**Use Durable Functions for:** agent workflows with human-in-the-loop gates, long pauses, or complex fan-out/fan-in

---

### Q46. How do you implement secure secrets management for agent tools that call external APIs?

**Answer:**

**Never hardcode secrets.** Use Azure Key Vault as the single source of truth.

```python
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

# Container App uses Managed Identity — no credentials in code
credential = ManagedIdentityCredential()
kv_client = SecretClient(
    vault_url="https://my-vault.vault.azure.net/",
    credential=credential
)

def get_secret(name: str) -> str:
    return kv_client.get_secret(name).value

# Agent tool using secret
async def call_ehr_api(patient_id: str) -> dict:
    api_key = get_secret("ehr-api-key")  # fetched at runtime, never stored
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as client:
        return await client.get(f"{EHR_BASE_URL}/patient/{patient_id}", headers=headers)
```

**Key Vault best practices:**
- Enable soft-delete and purge protection (prevents accidental deletion)
- Set secret expiry dates — rotate secrets every 90 days
- Use RBAC (not access policies) for granular per-identity permissions
- Enable diagnostic logging — every secret access is auditable
- Cache secrets for 5 minutes in memory to reduce Key Vault calls (rate limits apply)

---

### Q47. How do you design for fault tolerance in an Azure-based multi-agent system?

**Answer:**

**Fault tolerance layers:**

**1. Message durability** — Azure Service Bus with dead-letter queue
- If an agent crashes mid-processing, the message is not acknowledged and redelivered after lock timeout
- After N failed deliveries, message moves to dead-letter queue for investigation

**2. Idempotent operations** — every agent action must be safe to retry
- Check if the action was already completed before executing: `if not cosmos.get(task_id + ":step_3_done"): do_step_3()`

**3. Checkpointing** — persist state after each significant step
- Agent saves `{"step": N, "intermediate_results": {...}}` to Cosmos DB after each step
- On restart, agent reads checkpoint and resumes from step N

**4. Circuit breakers** per downstream dependency (Q31)

**5. Multi-region for disaster recovery:**
- Cosmos DB: enable multi-region writes (active-active)
- Azure AI Search: zone-redundant by default (Standard tier+)
- Redis: Azure Cache for Redis with geo-replication
- Container Apps: deploy to secondary region; Azure Front Door routes traffic if primary fails

**6. Graceful degradation:**
- If the embedding model is unavailable → fall back to keyword-only search
- If the LLM is unavailable → return cached response or route to human
- If Redis is unavailable → skip cache, read from Cosmos DB directly

---

### Q48. Explain how you would implement a HIPAA-compliant logging system for an agent that processes PHI.

**Answer:**

**Requirements:** all access to PHI must be logged; logs must be retained for 6 years; logs must be tamper-evident; logs must be accessible for audit.

**Architecture:**

```
Agent action (reads/writes PHI)
        ↓
Structured audit event emitted:
{
  "event_type": "phi_access",
  "agent_id": "clinical-rag-agent-v2",
  "user_id": "dr_smith_123",
  "patient_id": "P456789",  ← PHI reference (not PHI content)
  "action": "read",
  "resource_type": "lab_result",
  "resource_id": "lab_2025_11_01",
  "purpose": "pre_authorization_check",
  "timestamp": "2025-11-01T09:00:00Z",
  "source_ip": "10.0.0.5"
}
        ↓
Azure Event Hub (high-throughput, ordered, durable)
        ↓
Azure Function (processes stream)
        ↓
  ┌──────────────────────────────────┐
  │ Cosmos DB audit container        │
  │ - Immutable (append-only policy) │
  │ - Customer-managed encryption    │
  │ - 7-year TTL                     │
  └──────────────────────────────────┘
        ↓
Azure Monitor Alerts
  - Alert if: unusual access patterns, bulk PHI reads, off-hours access
```

**Tamper evidence:** Cosmos DB with analytical store + hash chaining — each audit record includes a hash of the previous record, so deletion or modification is detectable.

**Access:** Only auditors with dedicated RBAC role can read the audit container — not the agents, not the developers.

---

## Section 6: Healthcare Domain (Q49–Q50)

---

### Q49. What are the key compliance requirements for deploying AI agents that process healthcare data, and how do you address them technically?

**Answer:**

**HIPAA Technical Safeguards for AI Systems:**

| Requirement | Technical Implementation |
|---|---|
| **Encryption at rest** | Azure Storage + Cosmos DB with CMK (customer-managed keys via Key Vault) |
| **Encryption in transit** | TLS 1.2+ enforced at API Management; private endpoints for all Azure services |
| **Access controls** | Azure AD + RBAC; Managed Identity for agent-to-service auth; no shared credentials |
| **Audit logging** | Every PHI access logged to tamper-evident audit store (Q48) |
| **Minimum necessary access** | Agent tools request only the specific PHI fields needed; no bulk reads |
| **Data retention** | 6 years minimum; Cosmos DB TTL configured; Blob Storage lifecycle policies |
| **Breach notification** | Azure Defender for Cloud; alerts for anomalous access patterns |
| **Business Associate Agreements** | Azure has a BAA — must be executed before using Azure for PHI |

**De-identification for development/testing:**
- Use Microsoft Presidio (open source) to strip PHI from clinical notes before using in non-production
- Azure Health Data Services has a built-in de-identification API

**AI-specific risks:**
- **Model memorization**: fine-tuned models can memorize PHI from training data — mitigate by training on de-identified data only
- **Embedding leakage**: embeddings can sometimes be inverted to reveal source text — store embeddings separately from source text; apply access controls to both
- **Prompt injection via PHI**: a malicious patient record could inject instructions into the agent — sanitize all PHI before injecting into prompts (Q10)

---

### Q50. How would you architect a clinical decision support agent that assists physicians with diagnosis, while ensuring safety and regulatory compliance?

**Answer:**

**Key design principles:**
1. The agent is a **decision support tool** — it assists, never replaces, the physician
2. Every recommendation must be **explainable and cited**
3. All outputs go through a **physician review gate** before influencing care

**Architecture:**

```
[EHR Integration Layer — HL7 FHIR R4]
  Receives: patient record, physician query
        ↓
[Clinical Context Agent]
  - Retrieves: current meds, allergies, recent labs, diagnoses, vitals
  - Summarizes relevant context for current query
  - Flags: critical values, known allergies, recent changes
        ↓
[Multi-Hop RAG — Clinical Knowledge Agent]
  - Query: clinical guidelines (UpToDate-style KB), drug interactions DB
  - Multi-hop: diagnosis → treatment → contraindications for this patient
  - Returns: evidence-based recommendations WITH citations
        ↓
[Safety Check Agent]
  - Checks recommendations against patient allergies and medications
  - Checks recommended dosages against renal function (eGFR from labs)
  - Checks for drug-drug interactions
  - Hard stops: if safety check fails → escalate immediately, do not proceed
        ↓
[Explanation Generator]
  - Generates plain-language explanation of reasoning
  - Each claim linked to a specific guideline, with section reference
        ↓
[Human Review Gate — Physician UI]
  - Physician sees: recommendation, evidence, safety checks, reasoning
  - Options: Accept, Modify, Reject, Request more information
  - Physician's decision + rationale logged
        ↓
[EHR Write — only after physician acceptance]
  - Order written to EHR under physician's credentials
  - Agent's contribution noted in order metadata for audit
```

**Safety non-negotiables:**
- The agent can NEVER write a clinical order without physician acceptance — this is hardcoded, not prompt-configured
- All PHI access is logged (Q48)
- The agent must surface uncertainty: "Evidence quality: Low — only 2 RCTs, small n"
- Physician override is always available with a documented reason

**Regulatory:**
- This type of system likely requires FDA clearance as a Software as a Medical Device (SaMD) — Class II, 510(k)
- Document the agent's decision logic for FDA submission
- Maintain a version history of all model updates — each update triggers re-validation

---

## Your Power Stories — STAR Format

Prepare 3-minute STAR stories for each of these, drawing from your experience:

| Scenario | What They're Testing |
|---|---|
| "Tell me about a complex agent system you built" | Architecture depth, trade-off reasoning |
| "Describe a time an AI system failed in production and how you fixed it" | Debugging, resilience, post-mortems |
| "How did you improve RAG accuracy in a previous role?" | Technical depth on embeddings, retrieval |
| "Tell me about a time you influenced a team's technical direction" | Leadership, communication |
| "Describe your experience with healthcare data / HIPAA" | Domain credibility |

**STAR structure:**
- **Situation**: context, scale, constraints
- **Task**: what you specifically owned
- **Action**: concrete technical decisions you made and why
- **Result**: quantified outcome (latency, accuracy, cost, revenue impact)

---

*Last updated: May 2026 | Role: Senior Data Scientist / Agentic AI Engineer (anonymized)*
