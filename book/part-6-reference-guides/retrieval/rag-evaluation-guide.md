# RAG Evaluation: A Complete Guide

Prepared for interview preparation and real-system design. Updated May 2026.

## 1. What RAG Evaluation Means

Retrieval-Augmented Generation evaluation asks four questions:

1. Did the system retrieve the right evidence?
2. Did the model use that evidence faithfully?
3. Did the final answer solve the user's task?
4. Did the system behave reliably, safely, quickly, and cheaply enough for production?

The most important principle: do not evaluate RAG with one score. A RAG system is a pipeline. You need component-level metrics so you can tell whether a bad answer came from missing data, poor retrieval, weak reranking, bad context packing, prompt issues, model limitations, citation errors, or safety policy failures.

## 2. The RAG Pipeline To Evaluate

A typical RAG system looks like this:

```text
User query
  -> query normalization / query rewrite
  -> retrieval from vector, keyword, hybrid, graph, or SQL sources
  -> reranking and filtering
  -> context assembly / compression
  -> LLM generation
  -> citations, refusal, tool actions, or follow-up questions
  -> logging, monitoring, feedback, and evaluation
```

Evaluate every stage separately and then evaluate the end-to-end experience.

## 3. Evaluation Layers

### 3.1 Corpus And Index Quality

Before retrieval metrics, check whether the answer is even available in the knowledge base.

Key checks:

- Coverage: Are the important documents, tables, policies, tickets, pages, or records indexed?
- Freshness: Are updates reflected quickly enough?
- Permissions: Does retrieval respect user-level access control?
- Chunk quality: Are chunks semantically complete, not too large, not too tiny, and not split across important boundaries?
- Metadata quality: Are document IDs, titles, timestamps, owners, URLs, sections, and permissions attached?
- Deduplication: Are repeated chunks crowding out more useful chunks?
- Conflict detection: Does the corpus contain contradictory versions of policies or facts?

Good interview line:

> If the knowledge base does not contain the answer, retrieval and generation metrics are downstream symptoms, not root causes.

### 3.2 Retrieval Evaluation

Retrieval evaluation asks whether the retriever returns useful evidence for a query.

Use when comparing:

- embedding models
- vector databases
- hybrid search vs vector-only search
- chunk size and overlap
- metadata filters
- rerankers
- query rewriting
- top-k values
- graph retrieval or multi-hop retrieval

Core retrieval metrics:

| Metric | What It Measures | When It Helps |
| --- | --- | --- |
| `Hit@k` | Whether at least one relevant item appears in the top `k` | Quick "did we find anything useful?" check |
| `Recall@k` | Fraction of all relevant items retrieved in top `k` | Best when multiple documents are needed |
| `Precision@k` | Fraction of top `k` results that are relevant | Best when context budget is tight |
| `MRR` | Rank of the first relevant result | Useful for single-answer QA |
| `nDCG@k` | Ranking quality with graded relevance | Useful when some docs are more useful than others |
| Context relevance | Whether each retrieved chunk helps answer the query | Useful with LLM-as-judge or human labeling |
| Context recall | Whether retrieved context contains the information needed for the reference answer | Useful when you have a gold answer |
| Redundancy | How many retrieved chunks repeat the same evidence | Useful for context efficiency |
| Latency and cost | Retrieval time and infrastructure cost | Required for production |

Typical formulas:

```text
Precision@k = relevant retrieved documents in top k / k
Recall@k = relevant retrieved documents in top k / total relevant documents
Hit@k = 1 if any relevant document appears in top k, else 0
MRR = average of 1 / rank of the first relevant document
```

Retrieval labels can be:

- gold document IDs selected by domain experts
- gold passages marked by annotators
- synthetic question-context pairs generated from documents
- LLM-labeled relevance scores, calibrated against human samples
- production thumbs-up or answer-click data, used carefully because user feedback is noisy

### 3.3 Context Evaluation

Context evaluation sits between retrieval and generation. A retriever can return good chunks, but the final context can still be poor if ranking, truncation, compression, or packing loses the useful evidence.

Evaluate:

- Sufficiency: Is there enough evidence to answer?
- Focus: Is irrelevant context minimized?
- Ordering: Are the most useful chunks near the top?
- Diversity: Does the context cover all parts of a multi-hop question?
- Citation readiness: Can each answer claim be traced to a chunk?
- Contradiction: Do chunks conflict with each other?
- Token efficiency: How much context is wasted?

Important failure mode:

```text
Retriever found the right chunk at rank 12.
Context assembler only passed top 5 to the LLM.
End-to-end answer failed, but the root cause is context packing, not embedding quality.
```

### 3.4 Generation Evaluation

Generation evaluation asks whether the answer is correct, grounded, useful, and aligned with policy.

Core generation metrics:

| Metric | Meaning | Requires Reference Answer? |
| --- | --- | --- |
| Faithfulness / groundedness | Are answer claims supported by retrieved context? | No, but needs retrieved context |
| Correctness / answer accuracy | Does the answer match the expected answer? | Usually yes |
| Answer relevance | Does the answer address the user query? | No |
| Completeness | Does the answer cover all required parts? | Often yes |
| Citation accuracy | Do citations support the claims they are attached to? | No, but needs source mapping |
| Refusal accuracy | Does the system abstain when context is insufficient or unsafe? | Yes, for strong evaluation |
| Conciseness | Is the answer neither bloated nor underspecified? | No |
| Policy/safety compliance | Does the answer avoid disallowed content and data leakage? | Depends |

Faithfulness is not the same as correctness:

- A faithful answer can be wrong if the retrieved context is wrong.
- A correct answer can be unfaithful if the model used prior knowledge instead of provided evidence.
- A production RAG system usually needs both.

### 3.5 End-To-End Task Evaluation

End-to-end evaluation asks whether the full system solved the user's task. It combines retrieval, reasoning, answer generation, citations, latency, and UX.

Examples:

- Customer support bot: Did it resolve the user's issue without escalation?
- Legal search assistant: Did it cite the controlling authority and avoid unsupported claims?
- Internal policy assistant: Did it answer with the current policy and respect permissions?
- Research assistant: Did it synthesize across multiple sources and cite each claim?
- Data analyst assistant: Did it retrieve the right schema or records and compute the answer correctly?

End-to-end metrics:

- task success rate
- human preference win rate
- correctness score
- groundedness score
- citation support rate
- escalation rate
- refusal precision and recall
- average latency
- p95 latency
- cost per successful answer
- user satisfaction
- production defect rate

## 4. The RAG Triad

A common mental model is the RAG triad:

1. Context relevance: Are retrieved chunks relevant to the query?
2. Groundedness: Is the answer supported by the retrieved context?
3. Answer relevance: Does the final answer address the query?

This triad is useful because it maps to the edges of the pipeline:

```text
Question -> Context: context relevance
Context -> Answer: groundedness
Question -> Answer: answer relevance
```

It is not enough by itself. Add correctness, citation quality, refusal behavior, safety, latency, cost, and product-specific success metrics.

### 4.1 Metric Catalog: Meaning, Inputs, And Similar Metrics

Use this catalog when explaining, choosing, or debugging RAG metrics. The "similar metrics" column helps you connect different names used by Ragas, DeepEval, TruLens, LangSmith, Phoenix, LlamaIndex, and custom eval systems.

#### Retrieval Metrics

| Metric | Meaning | Required Inputs | Good Score Means | Similar Or Related Metrics |
| --- | --- | --- | --- | --- |
| `Hit@k` | Whether at least one relevant document or chunk appears in the top `k` results | Query, retrieved ranked list, gold relevant docs/chunks | The retriever can find at least one useful evidence item | Success@k, Recall-at-least-one |
| `Recall@k` | Fraction of all relevant docs/chunks retrieved in top `k` | Query, retrieved ranked list, full set of gold relevant docs/chunks | The retriever captures most of the evidence needed | Context recall, evidence coverage |
| `Precision@k` | Fraction of top `k` retrieved docs/chunks that are relevant | Query, retrieved ranked list, relevance labels | Retrieved context is focused and not noisy | Context precision, document precision |
| `F1@k` | Harmonic mean of precision and recall at `k` | Precision@k and Recall@k | Balance between finding enough evidence and avoiding junk context | Retrieval F1 |
| `MRR` | Average reciprocal rank of the first relevant result | Query, ranked list, relevance labels | The first useful result appears near the top | First relevant rank, rank quality |
| `MAP` | Mean average precision across queries | Query set, ranked lists, relevance labels | Relevant items appear consistently high across rankings | Average precision |
| `nDCG@k` | Ranking quality when relevance can be graded, such as 0, 1, 2, 3 | Ranked list, graded relevance labels | Highly relevant docs are ranked above weakly relevant docs | DCG, graded ranking quality |
| Context relevance | Whether each retrieved chunk is useful for answering the query | Query and retrieved chunk | Retrieved chunks are topically and semantically useful | Document relevance, retrieval relevance |
| Context recall | Whether the retrieved context contains the information needed for the expected answer | Query, retrieved context, gold answer or gold evidence | The answer can be produced from retrieved evidence | Evidence recall, answer support coverage |
| Context precision | Whether useful chunks are ranked before less useful chunks | Query, retrieved chunks, relevance labels or judge scores | The context budget is spent on useful evidence first | Ranked context quality |
| Context entity recall | Whether entities from the gold answer appear in retrieved context | Gold answer, retrieved context, entity extraction | Key people, products, dates, IDs, or concepts were retrieved | Entity coverage |
| Noise sensitivity | How robust the system is when irrelevant context is present | Query, answer, relevant and irrelevant context | The generator ignores distracting retrieved text | Distractor robustness |
| Redundancy rate | How much retrieved context repeats the same information | Retrieved chunks and similarity/overlap measure | Context is diverse rather than duplicated | Duplicate rate, diversity |
| Empty retrieval rate | How often retriever returns no usable results | Query logs and retrieval results | Index or filters are not silently failing | No-result rate |
| Filter accuracy | Whether metadata and permission filters include/exclude correctly | Query, user role, metadata labels, expected docs | The right user sees the right docs only | ACL accuracy, permission-aware retrieval |
| Retrieval latency | Time spent in retrieval, filtering, and reranking | Trace timings | Retrieval is fast enough for product targets | p50/p95 retrieval latency |

#### Generation Metrics

| Metric | Meaning | Required Inputs | Good Score Means | Similar Or Related Metrics |
| --- | --- | --- | --- | --- |
| Faithfulness | Whether the answer is supported by retrieved context | Question, retrieved context, answer | The model did not add unsupported claims | Groundedness, hallucination inverse |
| Groundedness | Whether answer claims can be traced to source evidence | Retrieved context, answer, sometimes question | Each factual claim has evidence | Faithfulness, attribution |
| Hallucination rate | Fraction of answers or claims unsupported by context | Retrieved context and answer | Low unsupported claim rate | Unsupported claim rate |
| Correctness | Whether the answer is factually right against a gold answer or expert label | Question, answer, gold answer or rubric | The answer matches the expected truth | Answer accuracy, factual correctness |
| Semantic similarity | Meaning-level similarity between generated and reference answer | Answer and reference answer | The answer says the same thing, even with different wording | Answer similarity, BERTScore-style metrics |
| Exact match | Whether generated answer exactly matches reference | Answer and reference string | Useful for short factual answers like IDs or dates | String match |
| Answer relevance | Whether the answer addresses the user question | Question and answer | The answer is on-topic and responsive | Response relevancy, QA relevance |
| Completeness | Whether all required parts of the question are answered | Question, answer, rubric or gold answer | No important sub-question is missing | Coverage, answer completeness |
| Conciseness | Whether the answer is direct without unnecessary detail | Question, answer, rubric | The answer is not bloated | Brevity, verbosity control |
| Citation support | Whether citations actually support the claims they cite | Answer, citations, source chunks | The cited evidence proves the statement | Citation accuracy, attribution precision |
| Citation recall | Whether all factual claims that need citations have them | Answer, claims, citations | Important claims are not uncited | Attribution coverage |
| Refusal precision | Of the answers that refuse, how many should have refused | Answer, expected behavior labels | Refusals are appropriate | Abstention precision |
| Refusal recall | Of unanswerable or unsafe cases, how many are refused | Answer, expected behavior labels | The system avoids fabricating answers | Abstention recall, no-answer recall |
| Clarification accuracy | Whether the system asks a useful follow-up when the query is underspecified | Query, answer, expected behavior | Ambiguity is handled instead of guessed | Ambiguity handling |
| Safety compliance | Whether answer follows safety, privacy, legal, or policy rules | Query, answer, policy rubric | The answer avoids disallowed behavior | Policy compliance, toxicity inverse |
| Format adherence | Whether output follows requested schema or style | Answer and expected schema | Downstream systems can parse the output | JSON validity, schema accuracy |

#### End-To-End And Product Metrics

| Metric | Meaning | Required Inputs | Good Score Means | Similar Or Related Metrics |
| --- | --- | --- | --- | --- |
| Task success rate | Fraction of user tasks completed successfully | User goal, final answer/action, human or rubric label | The system solves real work | Resolution rate |
| Human preference win rate | How often users or annotators prefer version A over B | Paired outputs and preference labels | A change improves perceived quality | Pairwise win rate, A/B preference |
| User satisfaction | User rating or feedback after answer | Product feedback | Users find answers helpful | CSAT, thumbs-up rate |
| Escalation rate | Fraction of sessions needing human support | Session logs | Lower is better if quality stays high | Deflection rate inverse |
| Reopen rate | How often users return because answer did not solve issue | Session or ticket data | Answers are durable and complete | Repeat contact rate |
| Latency | Time to final answer | Trace timings | Response speed meets UX requirements | p50, p95, p99 latency |
| Cost per answer | Model, embedding, vector DB, reranker, and infrastructure cost | Cost logs and traces | Quality is achieved within budget | Cost per successful answer |
| Token efficiency | Tokens spent per successful answer | Prompt, context, output token counts | Context and prompts are not wasteful | Cost efficiency |
| Trace completeness | Fraction of runs with all needed debug fields logged | Observability logs | Failures can be diagnosed | Logging coverage |
| Drift rate | Change in query, corpus, retrieval, or answer distributions over time | Production logs over time | System behavior is stable or drift is detected early | Data drift, query drift |

#### Corpus, Index, And Governance Metrics

| Metric | Meaning | Required Inputs | Good Score Means | Similar Or Related Metrics |
| --- | --- | --- | --- | --- |
| Corpus coverage | Whether the knowledge base contains answers to target questions | Question set, corpus, expert labels | The system has the knowledge it needs | Knowledge coverage |
| Freshness lag | Time between source update and index availability | Source timestamps and index timestamps | Answers reflect current information | Index freshness |
| Metadata completeness | Fraction of chunks with required metadata | Indexed chunks and metadata schema | Filtering, citation, and permissions can work | Metadata quality |
| Chunk coherence | Whether chunks preserve meaningful units | Chunks and human/LLM labels | Chunks are understandable and self-contained | Chunk quality |
| Duplicate chunk rate | Fraction of chunks that are near duplicates | Chunk embeddings or text similarity | Index is not crowded with repeated text | Deduplication rate |
| Permission leakage rate | Restricted content shown to unauthorized users | User role, retrieved docs, permission labels | Access control is working | ACL violation rate |
| Prompt injection pass rate | Fraction of malicious retrieved instructions ignored by the model | Adversarial docs, query, answer | Retrieved content cannot hijack behavior | Indirect prompt injection robustness |

### 4.2 Which Metrics To Use Together

Use metric bundles instead of isolated metrics:

| Goal | Recommended Bundle |
| --- | --- |
| Tune retriever | `Recall@k`, `Precision@k`, `MRR`, `nDCG@k`, retrieval latency |
| Tune reranker | `nDCG@k`, `MRR`, context precision, context relevance |
| Tune chunking | `Recall@k`, context recall, redundancy rate, groundedness, cost |
| Tune prompt | faithfulness, answer relevance, correctness, refusal precision/recall |
| Tune citations | citation support, citation recall, groundedness |
| Handle no-answer cases | refusal precision, refusal recall, false answer rate, answer relevance |
| Prepare release gate | retrieval recall, correctness, groundedness, citation support, safety, p95 latency, cost |
| Monitor production | task success, thumbs-up rate, escalation rate, hallucination reports, latency, cost, drift |

### 4.3 Metric Interpretation Rules

- High recall and low precision means the system finds evidence but sends too much noise.
- High precision and low recall means the context is clean but misses needed evidence.
- High groundedness and low correctness usually means the retrieved source is wrong, stale, or incomplete.
- High correctness and low groundedness means the model may be using memorized knowledge instead of provided evidence.
- High answer relevance and low correctness means the answer sounds helpful but is wrong.
- High retrieval scores and low generation scores point to prompt, model, reasoning, or citation issues.
- Low retrieval scores and low generation scores usually mean generation is failing because evidence never arrived.
- Good average scores with bad slice scores mean the eval set has hidden failure pockets.

### 4.4 SOTA RAG Evaluation View As Of 2026

The state of the art is no longer just "run Ragas metrics" or "score faithfulness with an LLM judge." Current RAG evaluation is moving toward fine-grained, source-aware, task-aware diagnosis.

SOTA themes:

| Theme | What It Adds Beyond Basic RAG Evals | Why It Matters |
| --- | --- | --- |
| Claim-level evaluation | Break answers into atomic factual claims and check each claim against context and/or gold answer | Catches partial hallucinations that whole-answer scores miss |
| Nugget-level evaluation | Decompose expected answers into information nuggets and measure coverage | Better for long-form, multi-faceted answers |
| Attribution verification | Evaluate whether each sentence or claim is supported by its cited source | Prevents "correct answer, fake citation" failures |
| Long-form groundedness | Evaluate long answers over long source documents, not just short QA | Matches enterprise reports, legal summaries, research synthesis, and policy answers |
| Fine-grained diagnostics | Separate retriever failures, context-packing failures, generator failures, and citation failures | Makes metrics actionable instead of just descriptive |
| Judge calibration | Validate LLM judges against human labels, use held-out test sets, and sometimes aggregate multiple judges | Reduces judge bias and unstable scoring |
| Synthetic-plus-human datasets | Generate broad synthetic tests, then calibrate or audit with human labels | Balances scale and trust |
| Unanswerability and deflection | Explicitly evaluate "I don't know", insufficient context, ambiguity, and stale/conflicting evidence | Reduces confident fabrication |
| Dynamic and realistic benchmarks | Test changing facts, private corpora, APIs, knowledge graphs, and real-world document messiness | Moves beyond static Wikipedia-style QA |
| Robustness and safety evals | Test prompt injection, poisoned documents, permission leaks, and irrelevant distractors | Required for production RAG |
| Agentic and tool-using RAG evals | Evaluate retrieval, tool calls, intermediate reasoning, and final answer separately | Needed when RAG is part of an agent workflow |
| Multimodal and structured-data RAG evals | Evaluate tables, PDFs, images, charts, audio, SQL, and knowledge graphs | Modern RAG is often not plain text only |

Representative SOTA frameworks and benchmarks:

| Framework / Benchmark | SOTA Contribution |
| --- | --- |
| RAGChecker | Fine-grained diagnostic metrics for retrieval and generation, including claim recall, context precision, context utilization, noise sensitivity, hallucination, self-knowledge, and faithfulness |
| RAGBench / TRACe | Large-scale explainable benchmark with industry-style domains and actionable labels for utilization, relevance, adherence, and completeness |
| ARES | Automated RAG evaluation with lightweight fine-tuned judges and prediction-powered inference using a small human-labeled set |
| TREC RAG Track | Shared-task evaluation emphasizing realistic retrieval-plus-generation, response completeness, citation support, attribution, and agreement analysis |
| FACTS Grounding | Long-form grounding benchmark where answers must fulfill the user request and remain fully grounded in provided context |
| GaRAGe | Human-curated long-form RAG benchmark with grounding passage annotations across private and web document sources |
| CRAG | Comprehensive RAG benchmark with dynamic facts, low-popularity facts, complex questions, mock APIs, and knowledge graph search |
| RAGTruth | Hallucination corpus with fine-grained annotations for detecting unsupported or contradictory claims in RAG outputs |

What this means in practice:

```text
Basic RAG evaluation:
  retrieval recall + faithfulness + answer relevance

SOTA RAG evaluation:
  claim/nugget-level answer coverage
  + claim-level groundedness
  + citation support verification
  + retrieval diagnostics
  + context utilization and noise sensitivity
  + no-answer/refusal behavior
  + calibrated LLM judges
  + human audit slices
  + production traces and drift monitoring
```

Interview-ready framing:

> The SOTA direction is diagnostic and attribution-aware. Instead of asking whether the answer is "good" globally, modern RAG eval breaks the answer into claims or nuggets, checks whether each one is covered, grounded, and properly cited, then traces failures back to retrieval, reranking, context assembly, generation, or refusal logic.

## 5. Dataset Design

The evaluation dataset is usually more important than the evaluation framework.

### 5.1 What Each Test Case Should Contain

Use a structured schema:

```json
{
  "id": "benefits_014",
  "question": "How many weeks of paid parental leave do full-time employees get?",
  "expected_behavior": "answer",
  "gold_answer": "Full-time employees get 16 weeks of paid parental leave.",
  "gold_doc_ids": ["hr_policy_2026_parental_leave"],
  "gold_spans": [
    {
      "doc_id": "hr_policy_2026_parental_leave",
      "start": 1200,
      "end": 1375
    }
  ],
  "category": "single-hop policy QA",
  "difficulty": "easy",
  "must_cite": true,
  "notes": "Answer changed from 12 to 16 weeks in 2026."
}
```

For conversational RAG, include turns:

```json
{
  "id": "support_021",
  "turns": [
    {"role": "user", "content": "Can I return my laptop?"},
    {"role": "assistant", "content": "What purchase date is on your receipt?"},
    {"role": "user", "content": "March 4, 2026"}
  ],
  "expected_behavior": "answer_with_policy",
  "gold_doc_ids": ["returns_policy_2026"],
  "gold_answer": "The laptop is returnable only if it is within the return window and meets the condition requirements."
}
```

### 5.2 Dataset Categories To Include

Build a balanced set, not just easy happy-path examples.

| Category | Example |
| --- | --- |
| Single-hop factual | "What is the refund window?" |
| Multi-hop | "Which plan covers X, and what form is required?" |
| Comparison | "How does the Pro plan differ from Enterprise?" |
| Aggregation | "List all security controls required for vendors." |
| Temporal | "What is the current policy as of May 2026?" |
| Ambiguous | "Can I expense this?" without enough details |
| No-answer | Knowledge base lacks the answer |
| Conflicting sources | Old policy and new policy disagree |
| Permissioned data | User should not see restricted docs |
| Adversarial | Prompt injection hidden inside retrieved docs |
| Long-tail terminology | Acronyms, synonyms, misspellings |
| Multilingual | Query in one language, documents in another |
| Citation-heavy | Every claim must cite a source |

### 5.3 Dataset Size Guidance

Practical starting points:

- 30 to 50 examples: smoke test for early prototypes
- 100 to 300 examples: useful regression set for iteration
- 500 to 1,000 examples: stronger offline benchmark
- 1,000+ examples: mature product evaluation with category-level slicing

Always slice results by category. A single average can hide that multi-hop questions, no-answer cases, or permissioned queries are failing.

### 5.4 Gold Labels

The best gold labels are human-reviewed:

- relevant document IDs
- relevant passages or spans
- expected answer
- acceptable alternate answers
- expected refusal or clarification
- citation requirements
- safety or compliance constraints

Synthetic data is useful for coverage, but do not treat it as fully trusted. Use it to bootstrap, then human-review a representative subset.

## 6. LLM-As-Judge Evaluation

LLM-as-judge is widely used because RAG outputs are often natural language answers where exact match is too strict.

Good uses:

- groundedness scoring
- answer relevance
- semantic correctness
- citation support
- style or policy rubric scoring
- pairwise comparison between system versions

Weak uses:

- replacing all human review
- evaluating specialized legal, medical, financial, or scientific claims without expert calibration
- scoring vague criteria such as "good answer" without a rubric
- judging answers using the same context or prompt that may have caused the error

### 6.1 Judge Rubric Template

Use small, specific rubrics.

```text
You are evaluating a RAG answer.

Question:
{{question}}

Retrieved context:
{{context}}

Answer:
{{answer}}

Score groundedness from 1 to 5:
1 = Most claims are unsupported or contradicted by the context.
2 = Some important claims are unsupported.
3 = Main answer is supported, but minor claims lack support.
4 = All important claims are supported, with small citation or wording issues.
5 = Every factual claim is directly supported by the provided context.

Return JSON:
{
  "score": 1-5,
  "unsupported_claims": ["..."],
  "contradicted_claims": ["..."],
  "explanation": "short explanation"
}
```

### 6.2 Judge Reliability Practices

- Use a clear rubric and require structured output.
- Calibrate the judge against human-labeled examples.
- Measure judge-human agreement, not just model scores.
- Keep a small expert-reviewed validation set.
- Use multiple judges or pairwise comparisons for high-stakes changes.
- Separate the answer generator from the judge model when possible.
- Randomize answer order for pairwise comparisons.
- Track judge model and prompt versions.
- Sample failed and passed cases for human audit.

### 6.3 Reference-Based vs Reference-Free

Reference-based eval:

- Uses a gold answer.
- Better for correctness.
- Harder to maintain when answers change.
- Good for regression testing.

Reference-free eval:

- Uses question, retrieved context, and answer.
- Useful for groundedness, context relevance, and answer relevance.
- Easier to scale.
- Needs judge calibration because it may miss subtle domain errors.

Mature RAG evaluation uses both.

## 7. Failure Taxonomy

Use this taxonomy during debugging:

| Failure Type | Symptom | Likely Fix |
| --- | --- | --- |
| Missing corpus data | System cannot answer because docs do not contain answer | Add or refresh data |
| Bad chunking | Correct info split across chunks | Change chunk strategy, semantic splitting, parent-child retrieval |
| Bad embeddings | Semantically relevant docs rank low | Try better embedding model, domain fine-tuning, hybrid retrieval |
| Query mismatch | User phrasing differs from document language | Query rewriting, synonyms, metadata boosts |
| Filter error | Correct docs excluded | Fix metadata filters or permissions logic |
| Low recall | Correct doc not in top-k | Increase k, hybrid search, multi-query retrieval |
| Low precision | Too much irrelevant context | Reranking, stricter filters, lower k |
| Reranker failure | Good docs retrieved but demoted | Tune reranker, evaluate reranker separately |
| Context truncation | Correct chunk found but not passed to LLM | Improve context packing |
| Prompt failure | Context is good but answer ignores it | Improve instructions, answer format, citation constraints |
| Model reasoning failure | Context requires synthesis but model misses it | Stronger model, decomposition, multi-step retrieval |
| Hallucination | Unsupported claims | Grounding prompt, claim verification, stricter refusal |
| Citation error | Cites irrelevant source | Citation-aware generation or post-hoc citation validation |
| Abstention failure | Answers when context is insufficient | No-answer training examples, refusal rubric |
| Over-refusal | Refuses answerable questions | Improve sufficiency threshold and prompt |
| Stale answer | Uses old policy | Freshness filters, recency ranking, index update monitoring |
| Security failure | Leaks restricted content | Permission-aware retrieval and red-team evals |

## 8. Practical Evaluation Workflow

### Step 1: Define Success

Write task-specific requirements:

```text
For policy QA, a successful answer must:
- use only documents the user is allowed to access
- answer the question directly when context is sufficient
- cite the exact policy section
- say it does not know when evidence is missing
- avoid using outdated policy versions
- respond in under 4 seconds at p95
```

### Step 2: Build The Dataset

Start with:

- real production or expected user queries
- domain expert questions
- synthetic questions generated from docs
- no-answer and ambiguous questions
- adversarial and permission tests

Label:

- gold answer
- gold docs or spans
- expected behavior
- category
- difficulty

### Step 3: Instrument The Pipeline

Log each run with:

- query
- rewritten query
- retrieved document IDs and scores
- reranked document IDs and scores
- final context passed to the model
- prompt version
- model name and parameters
- generated answer
- citations
- latency by stage
- total cost
- user feedback

Without traces, evaluation only tells you that something failed. With traces, evaluation tells you where it failed.

### Step 4: Run Retrieval Evals

For each query:

- compare retrieved docs to gold docs
- compute `Hit@k`, `Recall@k`, `Precision@k`, `MRR`, and `nDCG`
- inspect failures by category
- compare top-k, embeddings, chunking, hybrid search, and reranking

### Step 5: Run Generation Evals

For each generated answer:

- correctness against reference answer
- groundedness against retrieved context
- answer relevance against question
- citation support
- completeness
- refusal accuracy
- safety and policy compliance

### Step 6: Run End-To-End Evals

Score the full response as the user would experience it:

- final answer correctness
- helpfulness
- source quality
- user-visible citation quality
- latency
- expected behavior

### Step 7: Analyze By Slices

Slice by:

- question type
- document source
- product area
- language
- user role or permission level
- difficulty
- answerable vs unanswerable
- single-hop vs multi-hop
- old vs new documents
- short vs long queries

### Step 8: Set Gates

Example gates:

```text
Release gate:
- Retrieval Recall@5 >= 0.90
- Groundedness >= 0.92
- Correctness >= 0.85
- Citation support >= 0.90
- No-answer refusal recall >= 0.80
- Permission leakage = 0 critical failures
- p95 latency <= 4.0 seconds
- Cost per successful answer <= target budget
```

Thresholds should be domain-specific. A shopping assistant and a medical assistant should not share the same risk tolerance.

### Step 9: Add Regression Testing

Run evals:

- before changing prompts
- before changing embedding models
- before changing chunking
- before changing vector DB filters
- before model upgrades
- before major corpus refreshes
- in CI for a smaller smoke set
- nightly or weekly for larger eval sets

### Step 10: Monitor Production

Track:

- answer thumbs-up/down
- escalation rate
- query abandonment
- hallucination reports
- missing-document reports
- retrieval empty rate
- refusal rate
- latency and cost
- drift in query categories
- drift in corpus freshness
- high-risk safety events

Mine production logs for new eval cases. The best regression tests often come from real failures.

## 9. Experiment Design

When improving a RAG system, change one major variable at a time.

Common experiments:

| Experiment | Metrics To Watch |
| --- | --- |
| Chunk size 256 vs 512 vs 1024 tokens | Recall@k, precision@k, groundedness, latency |
| Chunk overlap 0 vs 10 percent vs 20 percent | Recall@k, redundancy, cost |
| Embedding model A vs B | Recall@k, MRR, domain slice performance |
| Vector vs keyword vs hybrid retrieval | Recall@k, exact-term queries, acronym queries |
| With vs without reranker | Precision@k, nDCG@k, latency |
| Top-k 3 vs 5 vs 10 | Context recall, hallucination rate, cost |
| Query rewriting on/off | Recall@k, bad rewrite rate |
| Context compression on/off | Answer correctness, groundedness, latency |
| Model A vs B | Correctness, groundedness, latency, cost |
| Prompt variants | Refusal accuracy, citation quality, answer relevance |

Use both absolute scores and pairwise comparisons. Pairwise evaluation is often easier for humans and judges: "Which answer is better for this question and why?"

## 10. Tooling Landscape

Use tools to accelerate evaluation, but keep ownership of your dataset, rubric, and interpretation.

| Tool / Framework | Best For |
| --- | --- |
| Ragas | RAG metrics such as context precision, context recall, faithfulness, response relevancy, synthetic testset generation |
| DeepEval | Unit-test-like LLM evals, RAG metrics, component-level retriever and generator evals, CI-style workflows |
| TruLens | RAG triad, tracing, groundedness/context relevance/answer relevance feedback functions |
| LangSmith | Dataset-based evals, traces, experiments, correctness/groundedness/relevance/retrieval relevance evaluators |
| Arize Phoenix | OpenTelemetry/OpenInference tracing, evals on traces, retrieval metrics, hallucination/correctness analysis |
| LlamaIndex evals | Faithfulness, relevancy, correctness, retrieval evaluation, synthetic question generation |
| OpenAI Evals/API | General eval orchestration and custom model/application evals. *Update (October 2026):* existing evals become read-only on 31 October 2026 and the Evals dashboard and API are scheduled to shut down on 30 November 2026, so export results and plan a replacement; OpenAI fine-tuning, often paired with it, closed to new organizations on 7 May 2026 and accepts no new jobs from 6 January 2027 ([deprecations](https://developers.openai.com/api/docs/deprecations)) |
| Custom notebooks | Maximum flexibility, useful for metric prototypes and domain-specific rubrics |

Tool selection advice:

- Choose based on integration with your stack and traces.
- Prefer tools that let you export raw examples and scores.
- Avoid black-box dashboards as the only source of truth.
- Keep a plain dataset format such as JSONL or CSV so you can switch tools.

## 11. Benchmarks

Public benchmarks are useful for retriever or model comparison, but internal RAG quality usually needs domain-specific evals.

Useful benchmark families:

- BEIR: heterogeneous information retrieval benchmark for zero-shot retrieval.
- KILT: knowledge-intensive language tasks with retrieval grounding.
- Natural Questions, TriviaQA, HotpotQA: open-domain QA and multi-hop QA patterns.
- MS MARCO: passage ranking and retrieval evaluation.
- Domain-specific benchmarks: legal, biomedical, financial, customer support, code search.

Interview framing:

> Public benchmarks help select components. Production evals must reflect the application's users, documents, permissions, and failure costs.

## 12. Special Cases

### 12.1 No-Answer Questions

RAG systems must know when not to answer.

Metrics:

- refusal precision: when it refuses, is refusal appropriate?
- refusal recall: does it refuse all unanswerable cases?
- false answer rate: how often does it fabricate an answer?

Include:

- answer not in corpus
- ambiguous query
- insufficient user permissions
- conflicting evidence
- outdated evidence
- unsafe request

### 12.2 Citations

Citation quality is separate from answer quality.

Evaluate:

- Does every factual claim have a citation?
- Does the cited source actually support the claim?
- Is the citation specific enough?
- Does the answer cite the latest or authoritative source?
- Are citations attached to the correct sentences?

Bad citation pattern:

```text
The answer is correct, but the citation points to a generic document that does not support the specific claim.
```

### 12.3 Multi-Hop RAG

Multi-hop questions require multiple evidence pieces.

Evaluate:

- evidence coverage across all required hops
- reasoning correctness
- whether each sub-answer is grounded
- whether the final synthesis is supported
- whether retrieval over-focuses on only one hop

### 12.4 Agentic RAG

If the system can call tools, browse sources, query databases, or plan steps, add:

- tool selection accuracy
- tool input correctness
- plan quality
- intermediate step grounding
- final answer grounding
- loop or timeout rate
- side-effect safety

### 12.5 GraphRAG

For graph-based RAG, add:

- entity linking accuracy
- relation retrieval accuracy
- subgraph relevance
- community summary quality
- path correctness
- conflict resolution across graph nodes

### 12.6 Multilingual RAG

Add:

- retrieval across languages
- translation accuracy
- language-specific answer quality
- name/entity preservation
- culturally or legally local context
- tokenization issues for non-English text

### 12.7 High-Stakes RAG

For legal, medical, financial, HR, security, or regulated domains:

- require human expert labeling
- maintain audit logs
- evaluate citation support strictly
- separate answer correctness from legal/medical/financial appropriateness
- include adversarial tests
- include permission and privacy tests
- use conservative refusal policies
- document known limitations

## 13. Example Scorecard

Use a scorecard like this for each release:

| Area | Metric | Target | Current | Pass? |
| --- | --- | --- | --- | --- |
| Retrieval | Recall@5 | >= 0.90 | 0.88 | No |
| Retrieval | Precision@5 | >= 0.70 | 0.76 | Yes |
| Generation | Groundedness | >= 0.92 | 0.95 | Yes |
| Generation | Correctness | >= 0.85 | 0.82 | No |
| Citations | Citation support | >= 0.90 | 0.86 | No |
| Refusal | No-answer recall | >= 0.80 | 0.62 | No |
| Safety | Permission leakage | 0 critical | 0 | Yes |
| Performance | p95 latency | <= 4 sec | 3.6 sec | Yes |
| Cost | Cost/success | <= budget | within budget | Yes |

Interpretation:

```text
Do not ship. Retrieval precision and groundedness are healthy, but recall, correctness, citations, and refusal behavior need work. The system is likely missing needed evidence in some cases and over-answering no-answer questions.
```

## 14. Interview-Ready Explanation

Strong concise answer:

```text
I evaluate RAG at three levels: retrieval, generation, and end-to-end product quality. For retrieval I use Hit@k, Recall@k, Precision@k, MRR, and nDCG against gold documents or passages. For generation I evaluate correctness, groundedness, answer relevance, completeness, citation support, and refusal accuracy. Then I slice results by query type, difficulty, source, permission level, and answerable vs unanswerable cases. I also log traces so I can diagnose whether failures come from corpus coverage, chunking, retrieval, reranking, context packing, prompting, or the model. In production I monitor user feedback, escalation, latency, cost, drift, hallucination reports, and permission failures.
```

If asked about LLM-as-judge:

```text
LLM-as-judge is useful for scalable evaluation of groundedness, answer relevance, and semantic correctness, but I do not trust it blindly. I use clear rubrics, structured JSON output, versioned judge prompts, calibration against human labels, and periodic audits. For high-stakes domains I require expert review and stricter release gates.
```

If asked how to improve a weak RAG system:

```text
I first identify the failure stage. If gold evidence is absent, fix ingestion. If evidence exists but is not retrieved, tune chunking, embeddings, hybrid search, filters, top-k, or reranking. If evidence is retrieved but not used, fix context packing and prompts. If the answer is unsupported, add grounding checks, citation validation, and refusal behavior. I measure each change against the same eval set and slice by failure category.
```

## 15. Common Mistakes

- Using only answer correctness and ignoring retrieval.
- Averaging scores without category slices.
- Treating LLM judge scores as ground truth.
- Building evals only after launch.
- Using synthetic data without human review.
- Ignoring no-answer cases.
- Ignoring citation support.
- Optimizing for recall while flooding the model with irrelevant context.
- Changing embedding model, chunking, prompt, and model at the same time.
- Forgetting latency, cost, and permission failures.
- Using public benchmarks as a substitute for application-specific evals.

## 16. Minimum Viable RAG Eval Setup

For a first serious RAG evaluation, build:

1. A 100-question dataset with categories and expected behavior.
2. Gold document IDs or gold spans for each answerable question.
3. At least 15 percent no-answer or ambiguous questions.
4. Retrieval metrics: `Hit@k`, `Recall@k`, `Precision@k`, `MRR`.
5. Generation metrics: correctness, groundedness, answer relevance, citation support, refusal accuracy.
6. Tracing for retrieved docs, final context, prompt, model, answer, citations, latency, and cost.
7. A release scorecard with thresholds.
8. A failure taxonomy and weekly review of failed examples.

## 17. Advanced RAG Eval Setup

For mature production:

- 500+ curated eval cases with slices.
- Continuous production sampling.
- Human annotation queues.
- Pairwise comparison between versions.
- Judge calibration set.
- Red-team set for prompt injection, data leakage, and policy abuse.
- Separate evals for retriever, reranker, context compressor, generator, and citation validator.
- Drift monitoring for query types and corpus updates.
- Automated regression gates in CI.
- Experiment tracking for every prompt, model, index, embedding, and retrieval config.
- Cost and latency budgets tied to quality.

## 18. Quick Diagnostic Map

Use this map when a RAG answer is bad:

```text
Was the answer available in the corpus?
  No -> ingestion, freshness, coverage problem.
  Yes -> did retrieval return it?
    No -> retrieval, embeddings, keyword, filters, top-k, query rewrite problem.
    Yes -> did reranking/context packing pass it to the LLM?
      No -> reranker or context assembly problem.
      Yes -> did the LLM use it correctly?
        No -> prompt, model, reasoning, citation, or refusal problem.
        Yes -> check whether user expectation, UI, or evaluation label is wrong.
```

## 19. References And Further Reading

- Original RAG paper: [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- Ragas paper: [Ragas: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)
- Ragas metrics documentation: [List of available metrics](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/)
- ARES paper: [An Automated Evaluation Framework for Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2311.09476)
- TruLens RAG triad: [RAG Triad](https://www.trulens.org/getting_started/core_concepts/rag_triad/)
- LangSmith RAG evaluation tutorial: [Evaluate a RAG application](https://docs.langchain.com/langsmith/evaluate-rag-tutorial)
- DeepEval RAG quickstart: [RAG Evaluation Quickstart](https://deepeval.com/docs/getting-started-rag)
- Arize Phoenix RAG evaluation: [Evaluate RAG](https://arize.com/docs/phoenix/cookbook/evaluation/evaluate-rag)
- LlamaIndex evaluation guide: [Evaluating](https://developers.llamaindex.ai/python/framework/module_guides/evaluating/)
- OpenAI evaluation guidance: [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- BEIR benchmark: [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/abs/2104.08663)
- KILT benchmark: [KILT: a Benchmark for Knowledge Intensive Language Tasks](https://arxiv.org/abs/2009.02252)
- RAGChecker: [A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation](https://arxiv.org/abs/2408.08067)
- RAGBench: [Explainable Benchmark for Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2407.11005)
- ARES: [An Automated Evaluation Framework for Retrieval-Augmented Generation Systems](https://huggingface.co/papers/2311.09476)
- TREC RAG 2025: [Overview of the TREC 2025 Retrieval Augmented Generation Track](https://arxiv.org/abs/2603.09891)
- FACTS Grounding: [Benchmarking LLMs' Ability to Ground Responses to Long-Form Input](https://arxiv.org/abs/2501.03200)
- GaRAGe: [A Benchmark with Grounding Annotations for RAG Evaluation](https://arxiv.org/abs/2506.07671)
- CRAG: [Comprehensive RAG Benchmark](https://arxiv.org/abs/2406.04744)
- RAGTruth: [A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models](https://arxiv.org/abs/2401.00396)
- RAG evaluation survey: [Retrieval Augmented Generation Evaluation in the Era of Large Language Models](https://arxiv.org/abs/2504.14891)
