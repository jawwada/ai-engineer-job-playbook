# Part 6 — Reference guides (study library)

Long-form study guides written during interview preparation, included here as a library. They are deeper and more code-heavy than the chapters in Parts 2–4; read a chapter first, then the matching guide. Company names, personal details and local paths were removed; the technical content is unchanged.

| Folder | Files | Read with chapter |
|---|---|---|
| `agentic-ai/` | design-patterns study guide (interview cheat sheet, failure modes, multi-agent deep dive), multi-agent frameworks complete guide, multi-agent papers reading list | 20, 22, 22b, 23 |
| `retrieval/` | modern RAG architectures, RAG evaluation guide, knowledge graphs complete guide, two Neo4j GraphRAG demos (plain and agentic) with runnable Python | 18, 24, 25, 32 |
| `llms/` | LLM fine-tuning guide, modern LLM engineering guide | 16, 26, 26b |
| `machine-learning/` | causal inference, mechanistic interpretability, time-series forecasting, ranking systems, uplift modeling | 17, 36 |
| `clouds/` | AWS cloud-native development, Kubernetes complete guide, Databricks + AWS agentic AI reference | 15, 21, 45, 50 |
| `python-backend/` | Python and backend guide, CI/CD pipelines complete guide | 45, 49 |
| `industries/` | ad-tech, e-commerce, energy, insurance, telecom data studies; insurance/healthcare agentic NLP deep dive; NLP extraction and RAG guide; systematic trading and ML | 36, 58 |
| `interview-practice/` | behavioural interviews at top tech companies; AI/backend engineer deep dive (code, algorithms, worked answers); agentic RAG system-design walkthrough; agentic RAG deep-dive questions; two 50-question banks (Azure/A2A/MCP/healthcare; AWS/agentic AI-ML engineer); an anonymized example job description | 35, 37–43 |
| `practice/` | two React quiz apps for quantitative practice (`quant_practice.jsx`, `quant_practice_2.jsx`) | 37 |

## Further reading that was in the same folder (not reproduced; find the originals)

These papers and articles informed the guides. They are copyrighted by their authors, so only pointers and one-paragraph takeaways are included.

1. **Edge et al. (Microsoft Research), "From Local to Global: A GraphRAG Approach to Query-Focused Summarization"** (arXiv 2404.16130). RAG fails on *global* questions ("what are the main themes in this corpus?"); GraphRAG extracts an entity graph, detects communities and pre-summarizes them, then answers global questions by map-reduce over community summaries. Takeaway for chapter 25: use it for sensemaking over a corpus, expect heavy indexing cost.
2. **Anthropic Engineering, "Introducing Contextual Retrieval"** (September 2024). Prepending a chunk-specific context sentence (generated from the whole document) before embedding and BM25 indexing substantially reduces retrieval failures, especially combined with reranking. Takeaway for chapters 18 and 24: cheapest large recall gain available.
3. **Bal & Puhan (UT Austin), "Benchmarking Retrieval Strategies for Biomedical RAG: A Controlled Empirical Study"** (arXiv 2605.02520, May 2026). Controlled comparison of dense, hybrid BM25+dense, cross-encoder reranking, multi-query expansion and MMR in a biomedical QA pipeline with multiple metrics. Takeaway: measure retrieval strategies on your own domain; hybrid plus rerank is a strong default but not free.
4. **Korn, "Architecture Matters: Comparing RAG Systems under Knowledge Base Poisoning"** (arXiv 2605.05632, May 2026). Evaluates vanilla RAG, agentic RAG, multi-agent debate (MADAM-RAG) and recursive language models under adversarially optimized contradictory documents (CorruptRAG-AK) on 921 Natural Questions pairs. Takeaway for chapter 53: architecture changes robustness to poisoning; test it adversarially.
5. **Tran & Kiela (Stanford), "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets"** (preprint). An information-theoretic argument (data processing inequality) that under a fixed reasoning budget a single agent with good context utilization is more efficient; multi-agent systems become competitive when a single agent's effective context is the bottleneck. Takeaway for chapter 22: justify sub-agents by context limits and parallelism, not by faith.
6. **Nechepurenko & Shuvalov, "Coordination as an Architectural Layer for LLM-Based Multi-Agent Systems: An Information-Controlled Empirical Study on Prediction Markets"** (May 2026). Production multi-agent systems fail often, mostly through coordination defects; the paper argues coordination should be a configurable architectural layer with predictable failure-mode signatures, studied on prediction-market tasks. Takeaway for chapters 22 and 42: design coordination explicitly; prediction markets are a live testbed.
7. **Zhang, "Reinforcement Learning for LLM-based Multi-Agent Systems through Orchestration Traces"** (preprint, May 2026). Treats orchestration traces (spawn, delegate, communicate, tool use, aggregate, stop) as the unit for reward design and credit assignment in multi-agent RL; catalogs reward families. Takeaway for chapters 26b and 29: traces are the substrate for both observability and learning.
8. **Chhabra, Medrano & Verma (Dell Technologies), "Case-Aware LLM-as-a-Judge Evaluation for Enterprise-Scale RAG Systems."** Multi-turn, case-based enterprise RAG (support, IT ops) needs judges that understand case identifiers, workflow alignment and partial resolution across turns. Takeaway for chapter 32: judge rubrics must reflect the operational workflow, not just answer quality.
9. **Kar (Google Cloud Community, Medium, March 2026), "Serverless A2A Swarms on Cloud Run: Secure Multi-Agent Orchestration."** A practitioner write-up of orchestrating specialized agents over the A2A protocol on Cloud Run with secure service-to-service auth, from incident-triage experience. Takeaway for chapters 22 and 30: A2A plus workload identity is the practical shape of cross-service agent security on GCP.

Also in the original folder but deliberately not included: third-party study books (vocabulary and GRE practice), a resume PDF, a timesheet, and IDE configuration files.
