# 18. Embeddings and vector search

> **What you need to be able to say:** what an embedding is and how it is trained; why cosine similarity works; what HNSW does and what it costs; when to use dense, sparse, hybrid or late-interaction retrieval; how to choose and evaluate an embedding model; and the five mistakes that silently ruin RAG retrieval. Go deeper: Part 6 → *Modern RAG architectures* and *RAG evaluation guide*.

## 18.1 What an embedding is

An embedding is a fixed-length vector (256–4,096 numbers) produced by a neural encoder such that inputs with similar *meaning* land close together. The encoder is trained contrastively: pairs that belong together (a question and its answer, a sentence and its paraphrase, an image and its caption) are pulled together, and in-batch negatives or mined hard negatives are pushed apart (InfoNCE loss). Modern text embedding models are transformer encoders or decoder-derived models fine-tuned this way on hundreds of millions of pairs, often with instructions prepended ("Represent this query for retrieving relevant passages:") so that one model can serve search, clustering and classification.

Similarity is usually **cosine** (angle between vectors; equals dot product on normalized vectors); **dot product** when magnitudes carry information; **Euclidean distance** for some image embeddings. Because the geometry is learned, "close" means "would be judged related by the training signal", nothing more — which is why domain evaluation matters more than leaderboards.

## 18.2 The 2026 model menu

| Model | Dims (flexible) | Max tokens | Notes |
|---|---|---|---|
| Gemini Embedding 2 (`gemini-embedding-2-preview`, March 2026) and gemini-embedding-001 | 3,072 default, Matryoshka (1,536 / 768 recommended) | 8,192 text; images, video (≤120 s), audio and PDFs (≤6 pages) in one request | Google's first natively multimodal embedder; interleaved inputs; 100+ languages; preview as of 2026, verify GA |
| OpenAI text-embedding-3-large / small | 3,072 / 1,536, Matryoshka | 8,191 | ubiquitous, cheap (\$0.13 / \$0.02 per MTok), battle-tested |
| Voyage 4 family (voyage-4-large, voyage-4, voyage-4-lite, open-weight voyage-4-nano; January 2026), voyage-multimodal-3.5, domain variants (law, finance, code) | 2,048 flexible | 32,000 | MongoDB-owned, recommended in Anthropic's docs; strong on long documents and code; multimodal 3.5 adds video |
| Cohere Embed 4 | 1,536 default, Matryoshka (256–1,536) | 128,000 | multimodal (text + images, PDFs), VPC/on-prem options, int8/binary outputs |
| Qwen3-Embedding (0.6B/4B/8B) | up to 4,096 | 32,000 | Apache-2.0, tops multilingual MTEB among open models; self-host |
| BGE-M3 | 1,024 | 8,192 | dense + sparse + multi-vector from one model; MIT |
| NV-Embed-v2 | 4,096 | 32,768 | strong, non-commercial license |
| Jina embeddings v3 / v4 | 1,024 / 2,048 flexible | 8,192 / 32,000 | task adapters, multilingual, multimodal and code (v4) |
| Nomic embed v1.5/v2 | 768 flexible | 8,192 | fully open (data + code) |
| all-MiniLM-L6-v2 | 384 | 512 | prototyping and CPU-only; too weak for production RAG |

**Matryoshka** representation learning trains vectors whose first *k* dimensions are themselves a good embedding, so you can truncate 3,072 → 512 dims and trade a little recall for 6× less storage and faster search. **Quantized embeddings** (int8, binary) cut memory 4–32× with small losses when combined with a rescoring step on full-precision vectors. The storage arithmetic matters more than the leaderboard: 10 million chunks × 3,072 float32 dimensions is 123 GB of raw vectors before any index; at 768 dimensions int8 it is 7.7 GB.

**Rerankers** (cross-encoders) read query and document together and output a relevance score; they are far more accurate than bi-encoder similarity but cost one model call per pair, so they rerank the top 20–100 candidates, not the whole corpus: Cohere Rerank 4 (Pro and Fast; about \$2 per 1,000 searches), Voyage rerank-2.5, Qwen3-Reranker (open), BGE-reranker-v2-m3 (open), Jina reranker, ColBERT-style late interaction (token-level vectors with MaxSim; see ColPali for documents as images). Budget 50–300 ms for reranking 50 candidates on a hosted API and plan for it in the latency budget (chapter 24).

## 18.3 Dense, sparse, hybrid, late interaction

- **Dense (vector) retrieval** captures meaning and paraphrase; it misses exact identifiers, part numbers, rare names and negations.
- **Sparse lexical retrieval** (BM25 over an inverted index) is exact on terms, fast, explainable, and still the best single method for many enterprise corpora with jargon. BM25 scores a term by its frequency in the document (saturating with `k1`, usually 1.2–2.0), discounted by document length (`b`, usually 0.75) and weighted by inverse document frequency; the two knobs you tune are `b` (lower it for corpora of uniform length) and the analyzer (stemming, synonyms, tokenization of part numbers).
- **Learned sparse** (SPLADE, BGE-M3 sparse) expands terms with a model while staying in an inverted index.
- **Hybrid** runs both and fuses them (Reciprocal Rank Fusion: score = Σ 1/(k + rank), with k = 60 in the original paper, Elasticsearch and Azure AI Search but 2 by default in Qdrant — check your engine's default, 24c.4.3; or weighted linear fusion on normalized scores, with the dense weight tuned on the retrieval set), then reranks. Hybrid + rerank is the production default in 2026; it is what Azure AI Search, Vespa, OpenSearch, Weaviate, Qdrant and pgvector-plus-tsvector setups implement. Typical gain on enterprise corpora: hybrid adds 5–15 points of recall@10 over dense alone, mostly on queries containing identifiers and rare terms; the reranker then adds precision at the top.
- **Late interaction** (ColBERT) keeps one vector per token and scores by summing per-query-token max similarities; higher accuracy than single-vector dense at 10–50× the storage, mitigated by compression (PLAID). ColPali/ColQwen apply it to page images, which sidesteps PDF parsing for visually rich documents.

## 18.4 Indexes: how approximate nearest neighbor search works

Exact search compares the query to every vector — fine up to a few hundred thousand vectors on one machine, not beyond. Approximate indexes trade recall for speed:

- **HNSW** (hierarchical navigable small world) builds a layered graph; search greedily walks from a top layer down. Parameters: `M` (links per node; 16–64), `efConstruction` (build-time beam; 100–400), `efSearch` (query-time beam; the recall knob — 64–256 typically gives 0.95–0.99 recall@10 at single-digit-millisecond p50 on a million vectors). Memory ≈ raw vectors + graph links (about 2M × 4 bytes per vector at layer 0, so ~128 bytes at M=16 — small next to a 4 KB float32 vector at 1,024 dimensions; the raw vectors dominate, which is why quantization and Matryoshka matter more than index tuning). Build time is the hidden cost: tens of minutes to hours for 10M vectors on one node, and `maintenance_work_mem` must hold the graph in pgvector or the build spills and crawls. The default in pgvector, Qdrant, Weaviate, Milvus, Elasticsearch, Vespa, FAISS.
- **IVF** (inverted file) clusters vectors with k-means and searches the `nprobe` closest clusters; smaller memory, needs training, worse at high recall, and the centroids go stale as data drifts. **IVF-PQ / product quantization** compresses vectors to bytes for billion-scale (FAISS, ScaNN, Milvus).
- **DiskANN / Vamana** keeps the graph on SSD for very large corpora at low memory (Azure, Milvus, pgvectorscale).
- **Flat / brute force** with GPU (FAISS-GPU, cuVS) is often the simplest exact answer up to tens of millions when latency budgets are loose; on CPU, a flat scan of 1M × 1,024-d vectors is ~100 ms, which is fine for many internal tools and removes a whole class of recall bugs.

Filtering ("only documents of tenant X updated this year") is where ANN indexes break: pre-filtering shrinks the candidate set before search (good selectivity, slower), post-filtering searches then filters (loses recall when the filter is selective), and filtered-HNSW variants (Qdrant, Weaviate, Vespa, pgvector 0.8+ iterative scans) handle it natively by walking the graph while checking the filter and widening the search until `k` results pass. Ask any vector-DB vendor how they do filtered search before anything else, and test it at your most selective filter (a tenant with 50 documents in a 10M-chunk index) — that is the case that returns zero results on a post-filtered index.

## 18.5 Choosing a vector store

| Store | Best when | Watch out |
|---|---|---|
| pgvector (Postgres) | you already run Postgres; <50M vectors; need transactions, joins, row-level security | tune HNSW build memory; use pgvectorscale for scale; hybrid via tsvector |
| Pinecone | managed, serverless, no ops; multi-tenant namespaces | cost at high QPS; data egress; vendor lock-in |
| Qdrant | filtered search, payload indexes, quantization, self-host or cloud | smaller ecosystem than Elastic |
| Weaviate | hybrid BM25+vector out of the box, modules, multi-tenancy | memory sizing |
| Milvus / Zilliz | billions of vectors, GPU indexes | operational weight (etcd, MinIO) |
| Elasticsearch / OpenSearch | you already run it; hybrid search, aggregations, security | vector performance tuning; licensing/forks |
| Vespa | search engineering at scale, ranking expressions, late interaction | learning curve |
| LanceDB / Chroma | local, embedded, prototyping, notebooks | not multi-node |
| Cloud-native (Google's Agent Platform Vector Search, formerly Vertex AI Vector Search; Azure AI Search; Bedrock KB stores; Amazon S3 Vectors; Databricks AI Search, formerly Vector Search) | staying inside one cloud and its IAM; S3 Vectors and Databricks' storage-optimized endpoints for large, cold, cheap indexes | portability; cold stores have higher query latency |

Default advice: start with pgvector or your cloud's managed search; move to a dedicated store when you measure a need (QPS, corpus size, filtered-search latency), not before. Rough thresholds: pgvector is comfortable to ~10–50M vectors and a few hundred QPS on one well-sized instance; above that, or with heavy filtered search across many tenants, a dedicated engine earns its operational cost.

## 18.6 Chunking and the index design that actually matters

Retrieval quality is decided before the model runs: **chunking** (by structure — headings, paragraphs, tables — rather than fixed characters; start at about 200–400 tokens without overlap and add overlap only if recall improves on your eval set, as the evidence summarized in 24c.3 suggests; keep tables whole; attach titles and breadcrumbs), **contextual enrichment** (prepend a one-sentence summary of the parent document or section to each chunk before embedding — Anthropic's "contextual retrieval" experiments reported a 35% drop in retrieval failures from contextual embeddings alone, 49% when contextual BM25 was added, and 67% with a reranker on top; the summaries cost about \$1 per million document tokens with prompt caching), **late chunking** (embed the whole document with a long-context model, then pool token embeddings per chunk, so each chunk vector already carries document context — Jina's alternative to the summary approach), **metadata** (source, date, tenant, section, permissions) for filtering, **parent-child retrieval** (search small chunks, return the parent section), **multi-vector documents** (title, summary and body embedded separately), and **freshness** (upsert on change, soft-delete, re-embed on model change — keep the model name in the metadata because you cannot mix vectors from two models in one index).

## 18.7 Evaluating retrieval (before you evaluate generation)

Build a set of 100–300 (query, relevant chunk ids) pairs — from real logs, from SMEs, or synthesized by an LLM from the documents and then reviewed — and measure **recall@k**, **MRR**, **NDCG@k** and **context precision**. Tune chunking, hybrid weights, `efSearch` and the reranker against this set; it is the single highest-leverage hour in any RAG project. Then evaluate generation (chapter 32). MTEB and the newer MTEB-v2/MMTEB leaderboards rank public models, and RTEB (retrieval-only, with private test sets) is the one to prefer because it is harder to overfit; treat all of them as a shortlist generator, not as a decision. Expect domain results to move models by ±10 points of recall@10 relative to the leaderboard order.

### Critic's additions: operating an index, not just building one

- **Re-embedding migrations.** Changing the embedding model means re-embedding everything: 10M chunks × 500 tokens = 5B tokens ≈ \$100 on text-embedding-3-small or ≈ \$650 on -large, plus hours of throughput. Do it as a shadow index: dual-write new content to both, backfill the new index, compare recall on the eval set, then flip reads. Never mix vectors from two models in one index (silent killer #1).
- **Tenancy.** Three isolation levels, in increasing cost: a `tenant_id` metadata filter in one index (cheapest; test the selective-filter case), a namespace or partition per tenant (Pinecone namespaces, Qdrant multitenancy payload indexes, Milvus partition keys, Weaviate tenants), and a separate collection or database per tenant when contracts demand it. Permission trimming on top of tenancy needs the caller's groups in every query (chapter 30).
- **Freshness and deletes.** Deletions in HNSW are tombstones until a rebuild; a store that cannot vacuum will grow and slow. Define the maximum staleness (minutes for tickets, a day for policies) and measure it as a metric.
- **Cold starts and memory.** HNSW must be in RAM to be fast; a 40 GB index on a 32 GB node pages and p99 explodes. Size nodes for the index plus the working set, or use DiskANN-style stores and accept higher latency.
- **Observability.** Log index name, filters, `k`, returned ids and scores for every retrieval (chapter 29); "it never retrieved the right doc" is unanswerable without them.

## 18.8 Beyond text: multimodal and multi-vector embeddings

CLIP/SigLIP and the commercial multimodal embedders (Gemini Embedding 2, voyage-multimodal-3.5, Cohere Embed 4, Jina v4) place images, charts, screenshots, video and text in one space, so a query like "the chart showing Q3 churn" can retrieve a slide. For documents, embedding **page images** with ColPali-style models avoids OCR entirely, at the price of multi-vector storage (hundreds of vectors per page) and a store that supports MaxSim (Vespa, Qdrant, Milvus). Audio embeddings (CLAP, Whisper encoders) and code embeddings (voyage-code, Qodo, OpenAI) follow the same pattern. The trade-off against text extraction is cost and auditability: page-image embeddings need no parser but cannot show "which sentence" supported an answer.

## 18.9 The five silent killers

1. **Mixed models** — some chunks embedded with model A, some with B; similarities become meaningless.
2. **Wrong normalization or metric** — cosine model served with raw dot product on unnormalized vectors.
3. **Chunks without context** — a paragraph that says "it increased 12%" with no subject.
4. **Post-filtering at high selectivity** — top-k returns 10 results, the filter leaves 0.
5. **No retrieval eval** — tuning prompts to fix what is actually a recall problem.

**Interview line:** *"Hybrid retrieval — BM25 plus a dense model — fused with RRF and reranked with a cross-encoder, over structure-aware chunks with contextual summaries and metadata filters, measured on a recall@k set before we touch the prompt. The vector store is whichever one gives us filtered search and lives where the data already is."*
