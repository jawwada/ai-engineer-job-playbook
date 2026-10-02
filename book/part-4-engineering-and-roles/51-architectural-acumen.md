# 51. Architectural acumen: principles, trade-offs, organizing large unstructured datasets, metadata-rich RAG, and why knowledge graphs become necessary

> **What you need to be able to say:** the handful of principles that senior engineers apply to every design; how to organize a large unstructured corpus so that retrieval, governance and cost work; what "RAG with metadata" really means; the point at which a knowledge graph stops being optional; and how to argue trade-offs with numbers instead of taste.

## 51.1 Ten principles that survive every technology cycle

1. **Start from the question and the metric.** A design without a measurable success criterion is a sketch. Write the acceptance test first (chapter 27).
2. **Put complexity where it is cheapest to change.** Prompts and configs change daily; indexes weekly; schemas monthly; identity and data models yearly. Design so the frequent changes touch the cheap layers.
3. **Make the deterministic parts deterministic.** Anything with a rule — money, permissions, formats, validation — is code, not a prompt. Use the model for understanding, judgement and language.
4. **Design the boundaries, not the boxes.** Interfaces (schemas, contracts, tool signatures, events) outlive implementations. A model behind an interface can be swapped; a model woven into business logic cannot.
5. **Separate control plane from data plane.** Orchestration, policy, identity and observability (control) should not depend on the volume path (data); scale them differently.
6. **Prefer idempotent, replayable steps.** Every pipeline stage and tool call should be safe to rerun; every run reproducible from its inputs. This is what makes evals, debugging and recovery possible.
7. **Permissions where the data lives.** Never in the prompt (chapter 30).
8. **Observe everything at the boundary.** Traces, metrics and logs at every interface; cost as a metric.
9. **Evaluate before optimizing.** Tune against a frozen set; argue with numbers.
10. **Buy the undifferentiated, build the differentiating.** Rent runtimes, gateways, memory, guardrails; own the orchestration logic, tools, data and evals.

**Critic's additions: three corollaries that agentic systems force.** The ten principles predate agents; agents add three failure classes that a reviewer will test for. *Every input is a potential instruction.* Documents, tickets, web pages and tool results can steer the model, so decide at design time which of untrusted input, private data and outbound action each session gets, and put a human approval on the third leg when all three are needed (the lethal trifecta and the Rule of Two, chapter 49). *Models are a dependency with an expiry date.* Providers retire model versions on published schedules with notice periods measured in months; pin snapshots, route through a gateway so a version change is configuration, keep the eval set as the migration gate, and budget at least one migration per feature per year. *Budgets are architecture, not monitoring.* Anthropic reported that agents use about four times the tokens of a chat and multi-agent systems about fifteen times; turn limits, token caps, deadlines and per-tenant spend limits therefore belong in the orchestrator and the gateway, enforced in code, before the first user arrives.

## 51.2 How to reason about trade-offs out loud

Use a four-column table in every design discussion: *option*, *what it optimizes*, *what it costs*, *when it wins*. Fill it in with numbers you can estimate (latency, tokens, dollars, days). Examples: single agent vs supervisor (context isolation and parallelism vs coordination cost); vector-only vs hybrid retrieval (simplicity vs recall on jargon); managed RAG vs custom (speed vs control); frontier vs small fine-tuned model (quality headroom vs 20× cost); sync vs async (simplicity vs resilience); one index vs per-tenant indexes (operations vs isolation). The decision is the row whose "when it wins" matches the customer's constraints; say the constraints first.

**Critic's additions: the same table with numbers you can cite.** "With numbers" means published or measured figures, not adjectives. Quote the source and say you would re-measure on the customer's data.

| Decision | What it optimizes | What it costs | Numbers to bring |
|---|---|---|---|
| Single agent vs orchestrator with sub-agents | breadth and parallelism on research-style tasks | tokens, coordination bugs, harder debugging | Anthropic's research system (2025): an Opus 4 lead with Sonnet 4 sub-agents beat a single Opus 4 agent by 90.2% on its internal research eval while using about 15 times the tokens of a chat, and token usage alone explained about 80% of the performance variance; the same write-up warns that tightly coupled work such as most coding parallelizes poorly |
| Vector-only vs hybrid retrieval with reranking | recall on exact terms and jargon | a keyword index, a reranker call (100–300 ms) | Anthropic's contextual-retrieval study (2024): top-20 retrieval failures fell from 5.7% to 2.9% with contextual embeddings plus BM25, and to 1.9% with reranking (chapter 24b) |
| Frontier vs small or fine-tuned model | quality headroom vs unit cost | evaluation work to prove the small model is good enough | small-tier models are typically 10–20 times cheaper per token (chapter 47); route by difficulty and show the eval did not move |
| Managed agentic retrieval vs your own graph | time to a governed first version | variable, token-based cost and less control | Azure's own example: 2,000 agentic retrievals with three subqueries each cost about $4.32 in search plus model tokens (chapter 24b); compare with engineer-weeks and with your recall gap on the gold set |
| Synchronous vs queued | simplicity and streaming | a job store, polling or webhooks | move to a queue when p95 passes what an HTTP connection and a user will tolerate (chapter 49 uses 20 s) |
| One shared index vs per-tenant indexes | operations at scale vs isolation by construction | per-tenant: index count, memory floor per index; shared: a mandatory tenant filter that must never be skipped | above a few thousand tenants, shared indexes with a tenant partition key are usual; regulated tenants or very large ones get their own |

## 51.3 Organizing large unstructured datasets

A corpus of millions of documents, emails, tickets, recordings and images is a data product. Organize it in six moves:

1. **Inventory and classify.** Crawl the sources; record for each document its system, owner, type, language, size, date, sensitivity and access control; sample and look. Automated classification (small LLM or classifier) assigns a taxonomy (policy, contract, ticket, spec…) and a sensitivity level; a human validates samples. Decide what *not* to index (duplicates, drafts, archived, prohibited).
2. **Normalize and parse.** Convert everything to a canonical representation (text + structure + tables + images with coordinates) using document AI; keep the original; record parse quality and failures; handle versions (same document, many revisions) and near-duplicates (minhash/simhash, embedding similarity) explicitly.
3. **Model the metadata.** A document table (id, source, path, title, type, taxonomy, language, created/updated, author/owner, ACL principals, sensitivity, version, hash, parse status) and a chunk table (chunk id, document id, section path, page, text, contextual summary, embedding model and version, vector, token count). Metadata is what makes retrieval filterable, governance enforceable and cost attributable.
4. **Index by use, not by source.** Collections per use case (support answers, legal research, engineering specs) with the chunking and embedding model tuned per collection; the same document can appear in two collections with different chunking. Keep a lineage link from chunk to source page for citations and audits.
5. **Govern and refresh.** ACLs synced from the source system (and tested); retention and deletion propagated to indexes; event-driven updates with nightly reconciliation; versioned indexes with blue/green rebuilds when the embedding model changes.
6. **Measure.** Coverage (what share of questions have an answer in the corpus), freshness, parse-failure rate, duplicate rate, retrieval recall on a gold set per collection, cost per million tokens embedded.

Tooling: lakehouse tables (Delta/Iceberg) as the system of record for documents and chunks; Spark/Lakeflow/Glue/Dataflow for pipelines; Docling/Unstructured/Document AI for parsing; a catalog (Unity Catalog, Google Cloud's Knowledge Catalog — formerly Dataplex — or Purview) for governance; the vector/search engine as a *derived* store that can be rebuilt from the tables at any time.

**Critic's additions: sizing the corpus, and how organized corpora still fail.** Do the arithmetic before choosing an engine: 2 million documents typically become about 40 million chunks of roughly 400 tokens, which is about 16 billion tokens to embed and, at 1,024 dimensions in float32, about 160 GB of raw vectors (40 GB with int8 quantization) before index overhead (chapters 48 and 50). A full re-embedding is cheap in dollars and slow in time when rate limits apply, so plan it as a migration. Then design against the failures that well-organized corpora still have:

| Failure | How it shows up | Prevention |
|---|---|---|
| ACL drift | a group change in the source system is not reflected, and someone sees what they should not | permissions resolved at query time from the source of truth, nightly reconciliation, and a negative test |
| Version skew | the assistant quotes last year's policy because both versions are indexed and the old one ranks higher | version and effective-date fields, "current only" as the default filter, superseded versions archived |
| Silent parse failure | scanned PDFs produce empty or garbled text and never appear in answers | parse-quality score per document, an OCR fallback, and a threshold that fails the run |
| Mixed embedding models | chunks embedded with two model versions share an index and similarity scores become meaningless | the embedding model and version stored per chunk, blue/green index rebuilds, never an in-place upgrade |
| Deletion lag | an erased document survives in the index, a cache or the logs | deletion events consumed by every store and an audit query that proves zero references |
| Wrong extracted metadata | an LLM classifies a contract as a policy, and filters then hide it | confidence per extracted field, human review below a threshold, and metadata accuracy measured like any model |
| Taxonomy drift | new document types arrive and fall into "other" | a monthly review of the unclassified share with an owner who can change the taxonomy |

## 51.4 RAG with metadata — what it is and why it matters

"RAG with metadata" means every chunk carries structured fields, and retrieval uses them in three ways: **filtering** (tenant, ACL, document type, date range, product, language) so the candidate set is correct before similarity is applied; **ranking features** (recency boosts, authority of the source, section type) fused with similarity; and **context assembly** (grouping chunks by document, ordering by section, attaching titles and breadcrumbs so the model knows what it is reading). Metadata also enables **routing** (a question about "2025 benefits" goes to the HR collection with a year filter), **citations** (page, section, version), **evaluation slicing** (recall by document type), and **cost control** (smaller candidate sets). Without metadata, RAG degrades into "similar-sounding text from anywhere", which is the most common reason enterprise pilots stall. Practical rules: extract metadata at ingestion (from the source system, the document structure and an LLM pass for taxonomy/entities), store it in the same row as the vector, make every filterable field indexed, and design the query path to apply filters *before* approximate search (chapter 18).

**Critic's additions: what "filters before approximate search" means mechanically.** There are three strategies, and interviewers like to hear the trade-off. *Post-filtering* (take the top k by similarity, then drop what the filter rejects) is fast but loses results when the filter is selective: if a tenant owns 1% of the vectors, a top-100 search followed by a tenant filter returns about one usable hit. *Pre-filtering* (apply the filter, then search only the matching vectors exactly) is correct but slow when the filtered set is large. *Filtered approximate search* applies the filter while traversing the index (Qdrant's filterable HNSW, Weaviate's ACORN strategy, pgvector's iterative index scans since 0.8, and the managed engines' pre-filter options); engines typically fall back to exact search when the filter is very selective. The practical rules: measure recall@k by filter-selectivity band (a filter that keeps 50% of the corpus behaves very differently from one that keeps 0.1%); make the tenant or permission filter mandatory in the retrieval service so a code path cannot omit it; and when one filter dominates every query (tenant, region), partition the index on it instead of filtering at all.

## 51.5 When a knowledge graph becomes required

Metadata-rich RAG answers "find me text about X with these properties". It cannot answer questions whose shape is **relational** ("which assets mention products governed by rule R and lack disclosure D"), **aggregate** ("what are the recurring failure causes across 10,000 incidents"), **temporal** ("what was true about this account last quarter"), or **rule-based** ("which approvals does this request need"). You need a knowledge graph when at least two of these hold:

- Questions require multi-hop joins across entities (product → rule → disclosure → asset).
- Exactness and explainability are mandatory (compliance, finance, safety) — a path is an audit trail; a similarity score is not.
- Entities recur across many documents and must be resolved to one identity (customers, suppliers, parts, people).
- Rules and constraints are deterministic and change independently of the text that describes them.
- Agents need a small, trustworthy world model to plan against (dependencies, ownership, permissions), not a pile of passages.
- Global summaries over a corpus are needed (GraphRAG community summaries) rather than top-k passages.

Build it incrementally: start with the entity types the questions mention, load structured sources first, add LLM extraction with provenance for the rest, resolve entities with review, and let the agent use both vector search and graph queries (chapter 25). Skip it when questions are lookups, when the corpus changes faster than you can maintain edges, or when nobody will own the ontology.

**Critic's additions: deciding on the graph with a test and a budget, not a diagram.** Write 50–100 of the relational, aggregate, temporal and rule questions the business actually asks, with expected answers, and run them against the best metadata-rich RAG you can build in a week. If it already answers them at the required accuracy, the graph is not needed yet; if it fails on the multi-hop and "which ones lack X" questions while passing the lookups, you have the case in numbers. Then price it. An LLM extraction pass over 2 million documents of about 2,000 tokens each is roughly 4 billion input tokens — on the order of hundreds to a few thousand dollars at small-model prices, plus output tokens — and the larger cost is people: entity resolution needs human review of the uncertain merges, and the ontology needs an owner who approves changes every week. Incremental extraction on changed documents keeps the running cost close to the change rate. If the main need is global summaries rather than exact relations, LazyGraphRAG-style approaches keep indexing cost close to plain vector RAG (Microsoft reported about 0.1% of full GraphRAG indexing) and defer the work to query time. Failure modes to name: duplicate entities that split the evidence, stale edges that assert relations the documents no longer support, and extraction errors that look authoritative because a graph path feels like proof — keep provenance (document, page, extraction version) on every edge so an auditor can check it.

## 51.6 Reading a system like an architect (a checklist for reviews)

- What is the request path, step by step, with latencies and token counts?
- Where are the permissions enforced? Show me the negative test.
- What is deterministic, what is model-driven, and why is each where it is?
- What is the eval set and when does it run?
- What does a failed run look like in the traces, and how is it replayed?
- What is the cost per request today and at 10×?
- What changes weekly, and how expensive is that change?
- What is the human path?
- What breaks first under load, and what is the fallback?
- Which parts are bought and which are built, and why?

**Critic's additions: five questions reviewers of agentic systems now add.** *Which sessions combine untrusted input, private data and an outbound action, and where is the approval?* *What happens when the pinned model version is retired — who runs the migration, against which eval, and how long does it take?* *What data leaves the boundary (to a model provider, a web search, a third-party MCP server), in which region, and under which retention terms?* *How is a bad prompt, model or index rolled back, and how long does that take?* *Who is paged when quality, not availability, degrades?* A design that has crisp answers to these is ready for a pilot; a design that answers them with "the model will handle it" is not.

**Interview line:** *"Architecture is deciding where change is cheap: deterministic code for rules and money, models for understanding, metadata-rich retrieval for text, a graph when questions are relational and must be exact, permissions where the data lives, and traces and evals at every boundary — then arguing each choice with a number."*
