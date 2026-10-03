# 27. When to use what: prompting, RAG, knowledge graphs, fine-tuning, agents, multimodality — a decision guide with scenarios

> **What you need to be able to say:** a crisp decision procedure, the trade-off table, and eight worked scenarios where you name the choice, the reason, the architecture and the metric. Interviewers at FDE level ask exactly this: "a customer wants X — what would you build?"

## 27.1 The decision procedure

1. **Write the task as input → output with an acceptance test.** If you cannot write the test, you are not ready to pick a technique.
2. **Try the simplest thing: a frontier model with a good prompt, a few examples and structured output.** Measure on 50 examples. Most tasks stop here. (Fifty examples are enough to see whether you are at 50% or 90%, not to tell 85% from 90% — the 95% confidence interval on 50 binary outcomes is roughly ±8 points at a 90% pass rate and ±14 points at 50%. Grow the set before you make close calls; chapter 32.)
3. **If it fails on facts, freshness, specificity or citations → add retrieval (RAG).** Measure retrieval first, then generation.
4. **If it fails on relationships, aggregates, multi-hop logic or exactness → add structure (SQL over a semantic layer, or a knowledge graph).**
5. **If it fails on format consistency, cost or latency at volume → fine-tune a smaller model (after you have the eval set and the logs).**
6. **If the path cannot be known in advance (open-ended tasks, tool use with feedback) → an agent, with budgets and approvals.**
7. **If the inputs are not text → multimodal model or a specialized vision/audio model, chosen by volume and auditability (chapter 19).**
8. **Always: evals in CI, traces, cost per request, guardrails, a human path.**

## 27.2 The trade-off table

| Need | Prompting | RAG | Knowledge graph | Fine-tuning | Agent |
|---|---|---|---|---|---|
| Current, specific facts | no | yes | yes (structured) | no | via tools |
| Citations and audit | partial | yes | yes (paths) | no | yes, if tools log |
| Relationships, multi-hop | no | partial | yes | no | yes, with graph tools |
| Consistent format/style | partial | partial | — | yes | — |
| Cost per request at scale | high (frontier) | medium | medium | low (small model) | highest |
| Latency | model-bound | +retrieval | +query | lowest with small model | highest |
| Time to first version | hours | days | weeks | weeks | days–weeks |
| Maintenance | prompts | index + pipeline | ontology + pipeline + ER | data + retraining | tools + evals + budgets |
| Permissions | — | filter at retrieval | per-node/edge | — | per tool |
| Failure mode | hallucination | missed retrieval | wrong edges | overfitting, forgetting | runaway, misuse |

## 27.3 Scenarios

**1. "Our support team answers the same 2,000 questions about our product; we want a bot."**
Choice: RAG over the help center and release notes with permission filters, citations and abstention; no fine-tuning. Reason: facts change weekly; citations build trust; volume is moderate. Architecture: contextual chunks, hybrid + rerank, Sonnet/Flash tier with Haiku/Flash-Lite routing for simple lookups, grounding check, handoff to humans. Metric: resolution without human, citation precision, CSAT. Later: an agent with account tools once the bot is trusted.

**2. "We receive 300,000 invoices a month in 40 layouts; extract 12 fields."**
Choice: document model (layout + OCR) feeding a small fine-tuned or prompted extraction model; multimodal frontier model only for the 5% hard cases. Reason: fixed schema at high volume → cost; need confidence and bounding boxes for audit. Metric: field accuracy, straight-through rate, cost per document. Not an agent: the path is known.

**3. "Analysts want to ask questions over our sales warehouse in English."**
Choice: semantic layer + text-to-SQL with validation; RAG only for the glossary. Reason: numbers must be exact; a graph is overkill; fine-tuning does not fix ambiguous metrics. Metric: execution accuracy on 200 gold questions, analyst acceptance. Later: an agent that can run multi-step analyses with approval.

**4. "Compliance needs to know which marketing assets violate which rules across products and regions."**
Choice: knowledge graph of products, rules, disclosures and assets, plus RAG over the regulations' text, queried by reviewer agents. Reason: multi-hop set logic with exactness and audit; relationships change less often than text. Metric: violations caught vs. human audit, false positives, review time.

**5. "Classify 5 million social posts a day into 30 categories."**
Choice: distill a frontier model into a small fine-tuned classifier (LoRA on a 1–8B model or even a BERT-class model). Reason: volume → cost and latency dominate; labels are stable. The napkin math: 5M posts × ~300 tokens is 1.5B input tokens a day — about \$375/day (≈\$11k/month) even on a \$0.25/MTok cheap tier, and ten times that on a workhorse model — while a fine-tuned encoder classifies thousands of posts per second on one GPU for roughly \$1.5–3k a month. Metric: F1 vs. frontier labels, cost per 1k, drift. Keep a frontier spot-check.

**6. "Automate our month-end close: pull reports, reconcile, draft journal entries, flag anomalies."**
Choice: a workflow with agentic steps — deterministic data pulls and reconciliations in code, an agent for investigating anomalies with read tools, approvals before any posting. Reason: most steps have known paths; the open-ended part is small. Metric: hours saved, exceptions resolved without humans, zero unauthorized postings.

**7. "Customers call to reschedule appointments; handle it by voice."**
Choice: voice agent — speech-to-speech model or chained ASR/LLM/TTS with a deterministic state machine for the booking step and tools over the scheduling system; RAG for policy questions. Reason: real-time latency and transactional correctness. Metric: completion rate, latency, escalation, cost per minute.

**8. "We want a model that writes in our brand voice for 50 product lines in 12 languages."**
Choice: prompting with style guides and examples first; fine-tune (SFT + DPO) on approved copy if consistency is still below the bar; RAG over product facts so the model never invents specs. Reason: style is a behaviour (fine-tuning), facts are knowledge (RAG). Metric: editor acceptance rate, brand-rubric judge score, factual errors per 100 pieces.

**9. "Field technicians photograph equipment; we want automated inspection reports."**
Choice: specialized vision model for defect detection (trained on labeled images), multimodal LLM to draft the report from detections and reference manuals (RAG), human sign-off. Reason: detection needs deterministic, measurable accuracy; narrative needs language. Metric: detection precision/recall, report edit rate.

**10. "Our agent should remember customers across conversations."**
Choice: structured memory (a profile table with explicit write rules) plus a temporal knowledge graph or vector store of past interactions; not fine-tuning. Reason: memory must be inspectable, deletable (privacy), and current. Metric: correct recall of prior facts, no contradictions, deletion compliance.

## 27.4 Combinations you will actually ship

- RAG + small fine-tuned classifier for routing and guardrails.
- RAG + knowledge graph for rules; vectors for text (hybrid GraphRAG).
- Agent + tools over text-to-SQL and RAG; approvals for writes.
- Multimodal document pipeline + RAG over extracted text + human review.
- Frontier model for planning/evaluation + small models for the high-volume steps + prompt caching everywhere.

### Critic's additions: the anti-patterns interviewers listen for

Naming the wrong answer and why it is wrong is often more convincing than the right answer. The ones that come up most:

| Anti-pattern | Why it fails | What to say instead |
|---|---|---|
| Fine-tuning to teach facts | facts learned in weights are fuzzy, uncitable, and stale the day the document changes | RAG for knowledge; fine-tune for behaviour and format |
| An agent for a known workflow | pays agent latency and cost, loses testability, adds failure modes | code the workflow; use a model only for the steps that need judgement |
| Multi-agent by default | ~15× chat tokens, coordination errors, context lost at handoffs | one agent with good tools; split when context or parallelism forces it |
| A vector database for 500 documents | operational weight for a corpus that fits in a cached prompt or a Postgres table | long context with caching, or pgvector |
| GraphRAG for lookup questions | weeks of extraction and entity resolution for questions vectors already answer | a graph only for relational, set-logic or audit questions |
| Text-to-SQL over raw tables | ambiguous joins and metric definitions produce confident wrong numbers | semantic layer first, gold question–SQL set second |
| An LLM where a rule or classifier works | 100–1,000× the cost and latency, non-deterministic | regex, lookup table or a small classifier; LLM for the residue |
| Judging quality with the model that produced it, uncalibrated | self-preference and leniency bias | a calibrated judge from another family, checked against human labels |
| Picking the model from a leaderboard | benchmarks are not your workload | ten real tasks per tier, measured on cost, latency and accuracy |

**Interview line:** *"I pick by failure mode: facts → retrieval, relationships → structure, behaviour → fine-tuning, unknown path → agent, non-text → multimodal — always after a prompted baseline with an eval set, and always with the cost per request and the human path designed in."*
