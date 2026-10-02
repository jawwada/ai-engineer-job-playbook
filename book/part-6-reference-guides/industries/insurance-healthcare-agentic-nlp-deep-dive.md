# Insurance and Healthcare Plan Recommendation: NLP, Agentic RAG, and Graph Deep Dive

Prepared for interview preparation. Updated May 2026.

This guide is for the version of the role where the company helps customers choose the right insurance or healthcare plan, and where a small change in customer facts can change eligibility, ranking, pricing, or the final recommended plan.

The core interview framing is:

```text
This is not just a chatbot problem.
It is a high-stakes decision-support system:
extract the right customer facts,
retrieve the right plan evidence,
apply hard eligibility rules,
rank valid plans,
and explain the result with citations and auditability.
```

The most important principle:

```text
LLMs should extract, retrieve, summarize, and explain.
Deterministic policy logic should decide hard eligibility and compliance.
```

---

## 1. How to Frame the Problem in the Interview

In an insurance or healthcare plan recommendation system, the pipeline usually mixes:

- unstructured text understanding
- structured eligibility rules
- retrieval over plan and policy documents
- graph relationships across members, providers, drugs, and plans
- agentic orchestration for multi-step decision support

This is not pure recommendation in the Netflix sense.
It is closer to:

```text
constraint satisfaction + classification + ranking + retrieval + explanation
```

### Why a single change can change the plan

One changed field may alter:

- subsidy eligibility
- plan availability by state or county
- provider network fit
- formulary coverage
- plan tier eligibility
- family vs individual plan path
- Medicare or Medicaid path
- employer-sponsored vs exchange path
- special enrollment eligibility

Examples:

- age changes from `64` to `65` -> Medicare path may become relevant
- ZIP or county changes -> network and plan catalog change
- tobacco status changes -> pricing changes
- one high-cost medication is added -> formulary fit changes
- spouse or dependent is added -> household plan options change
- income crosses a threshold -> subsidy and cost-sharing outcomes change

This is a very good interview line:

```text
The system should not just recommend the cheapest plan.
It should first eliminate invalid plans using rules,
then rank the remaining plans using customer needs and evidence.
```

---

## 2. The Right Technical Framing

A strong way to describe the architecture is:

```text
customer conversation + uploaded documents + plan corpus + provider/drug data
    ->
NLP extraction and normalization
    ->
eligibility and constraint engine
    ->
retrieval over plan evidence
    ->
candidate plan generation
    ->
ranking and explanation
    ->
agentic follow-up for missing information or next actions
```

### Separate the system into three layers

1. **Understanding layer**
   - extract entities, preferences, conditions, medications, household facts, dates, and intent

2. **Decision layer**
   - apply hard rules and policy logic
   - generate valid candidate plans
   - score and rank them

3. **Explanation layer**
   - explain why a plan was recommended
   - cite the plan brochure, formulary, provider directory, and eligibility rules

That separation makes you sound practical and production-oriented.

---

## 3. Domain Ontology: What Entities Matter

A generic NER model is not enough here.
You need a domain ontology.

### 3.1 Member and household entities

- member
- spouse
- dependent
- caregiver
- employer
- household size
- marital status
- age
- DOB
- gender if relevant to plan logic
- income
- employment status
- disability status
- tobacco status
- residency state
- county
- ZIP code
- move date
- enrollment date
- qualifying life event

### 3.2 Coverage and medical entities

- plan
- plan ID
- carrier
- metal tier
- premium
- deductible
- copay
- coinsurance
- out-of-pocket maximum
- HSA eligibility
- network
- PCP
- specialist
- hospital
- provider group
- formulary
- medication
- dosage
- diagnosis or condition
- procedure
- prior authorization
- referral requirement
- claim
- denial reason

### 3.3 Document and policy entities

- policy section
- evidence of coverage
- summary of benefits
- formulary tier
- provider directory entry
- effective date
- expiration date
- plan year
- rider
- exclusion
- appeal window

### 3.4 Relationship types

- `MEMBER_HAS_DEPENDENT`
- `MEMBER_TAKES_DRUG`
- `MEMBER_HAS_CONDITION`
- `MEMBER_PREFERS_PROVIDER`
- `PLAN_COVERS_DRUG`
- `PLAN_INCLUDES_PROVIDER`
- `PLAN_AVAILABLE_IN_REGION`
- `PLAN_HAS_PREMIUM`
- `PLAN_HAS_DEDUCTIBLE`
- `PLAN_REQUIRES_PRIOR_AUTH`
- `POLICY_OVERRIDES_POLICY`
- `DOCUMENT_SUPPORTS_CLAIM`

This ontology becomes the backbone for extraction, graph modeling, retrieval filters, and explanation.

---

## 4. Deep Dive: Entity Recognition for Insurance and Healthcare

### 4.1 What entity recognition must do here

The system must detect:

- customer facts from conversation
- facts from uploaded PDFs and forms
- plan attributes from policy documents
- provider and drug names from external datasets
- references across all of them

A good interview answer is:

```text
I would treat entity extraction as domain-specific structured data recovery,
not just generic NER. The goal is to recover decision-critical facts with
normalization, provenance, and confidence.
```

### 4.2 Typical modeling approaches

| Approach | Best for | Strengths | Weaknesses |
|---|---|---|---|
| Regex and rules | IDs, dates, premiums, plan codes | Precise and fast | Fragile outside stable formats |
| Gazetteers | drugs, providers, counties, plan names | Strong coverage for known terms | Misses unseen variants |
| CRF / BiLSTM-CRF | sequence tagging baselines | useful with smaller datasets | weaker than modern encoders |
| Transformer token classification | contextual entity extraction | strong general default | higher cost |
| Span classification | long or overlapping entities | flexible boundaries | more complex training |
| Layout-aware models | forms, PDFs, tables | good for document structure | more pipeline complexity |

### 4.3 Domain-specific entity examples

Conversation:

```text
I am 62, live in Maricopa County, take Humira, and my wife needs an
in-network cardiologist. We may move in September. Which plan fits us best?
```

Possible extracted entities:

```json
{
  "member_age": 62,
  "county": "Maricopa County",
  "medication": "Humira",
  "dependent_relation": "spouse",
  "specialist_needed": "cardiologist",
  "network_preference": "in-network",
  "event": "move",
  "event_date": "September",
  "intent": "plan_recommendation"
}
```

### 4.4 Why extraction is hard

The hard parts are:

- abbreviations and aliases
- OCR noise in uploaded documents
- provider name variants
- medication brand and generic name mapping
- ambiguous plan names
- long entities spanning punctuation
- local shorthand like "my wife," "our doctor," "the current plan"

### 4.5 What to normalize

Raw extraction is not enough.
You often need:

- county -> canonical geographic ID
- provider name -> provider directory ID
- drug name -> formulary or RXNorm-style canonical entry
- plan mention -> plan ID
- date phrase -> machine-readable date
- premium string -> numeric amount with currency

### 4.6 Evaluation

Evaluate at more than one level:

- mention precision / recall / F1
- exact span accuracy
- normalized value accuracy
- entity linking accuracy
- document-source provenance accuracy

For high-stakes fields, you can say:

```text
I would measure both extraction accuracy and decision impact,
because a small entity error may cause a wrong plan recommendation.
```

---

## 5. Pronoun Reference Extraction and Coreference Resolution

This is one of the most valuable topics to go deeper on.

### 5.1 What it means

Coreference resolution identifies when different mentions refer to the same underlying entity.

Examples:

- `Maria` and `she`
- `the applicant` and `the member`
- `the Gold PPO plan` and `it`
- `his son` and `the dependent`
- `the previous policy` and `that coverage`

Pronoun reference extraction is a subset of this problem.

### 5.2 Why it matters in this domain

In plan recommendation, the system often needs to know:

- who has the medical condition
- who takes the medication
- which person is moving
- which plan "it" refers to
- whether "he" refers to the member or spouse
- whether "this doctor" refers to the preferred provider already mentioned

If coreference fails, the decision layer can apply the wrong facts to the wrong person.

### 5.3 Example

```text
Maria is 62 and takes Humira. Her husband is 64. He wants to keep his
cardiologist, and she wants lower monthly premiums. If they move to Nevada,
will the current plan still cover him?
```

Correct resolution:

- `Maria` -> person A
- `Her husband` -> person B
- `He` -> person B
- `his cardiologist` -> provider preference for person B
- `she` -> person A
- `they` -> Maria + husband household
- `the current plan` -> currently enrolled plan
- `him` -> person B

### 5.4 Types of reference you should mention

- pronoun resolution
- nominal coreference
- alias resolution
- cross-document entity linking
- product or plan reference resolution

### 5.5 Practical approaches

1. **Rule-based conversation heuristics**
   - last mentioned person
   - household role tracking
   - plan currently under discussion

2. **Span-based or transformer-based coreference models**
   - score mention pairs or clusters
   - useful when text is conversational and ambiguous

3. **Entity memory in dialogue**
   - maintain structured session state
   - map `he`, `she`, `it`, `their plan`, `that doctor` to explicit IDs

4. **Graph-backed resolution**
   - if the graph already knows the member, spouse, plan, and provider, use it to disambiguate

### 5.6 Interview-ready architecture

```text
I would not rely on raw pronoun resolution alone.
I would maintain a conversation state object and explicit household entities,
then use coreference models plus deterministic dialogue memory to bind pronouns
to the right person or plan.
```

### 5.7 Metrics worth naming

- mention detection precision / recall
- coreference cluster quality
- CoNLL F1 if the interviewer wants standard NLP metrics
- downstream decision accuracy after reference resolution

### 5.8 Failure modes

- "he" refers to the spouse, but system applies medication to the member
- "it" refers to the current plan, but system binds it to a newly suggested plan
- "they" could mean household or provider group
- provider aliases cause wrong network checks

In this domain, wrong reference resolution is not a cosmetic bug.
It changes plan recommendations.

---

## 6. Prefix, Suffix, and Code-Aware Separation

Prefix and suffix separation matters in two different ways here.

### 6.1 Linguistic morphology

Examples:

- `non-covered` -> `non + covered`
- `preauthorization` -> `pre + authorization`
- `re-enrollment` -> `re + enrollment`
- `uninsured` -> `un + insured`

This helps with:

- normalization
- lexical recall
- stemming and lemmatization
- handling OCR noise and variants

### 6.2 Domain code decomposition

In insurance and healthcare, tokenization also needs to handle structured codes:

- `HMO-GOLD-AZ-2026`
- `PPO_3200_FAM_NV`
- `NDC-0002-8215-01`
- `ICD10-E11.9`
- `PLAN-H1234-001`

Useful decomposition strategies:

- split on hyphens and underscores
- split letter-digit boundaries
- preserve the full original token
- keep typed subparts such as state, year, tier, product line

Example:

```text
HMO-GOLD-AZ-2026
-> HMO | GOLD | AZ | 2026
```

That can encode:

- plan family
- metal tier
- state
- plan year

### 6.3 Why this matters in production

It helps with:

- fuzzy search
- exact match recovery
- linking mentions to plan IDs
- better retrieval over plan catalogs
- robust handling of OCR or user-entered variants

### 6.4 Modern nuance

Subword tokenizers already do part of this implicitly, but in enterprise systems you often still need a custom normalization layer for:

- plan codes
- diagnosis and procedure codes
- member IDs
- claim IDs
- formulary IDs

### 6.5 Interview line

```text
For general language, subword tokenization does much of the work.
For insurance and healthcare identifiers, I still build explicit code-aware splitting
and normalization because those tokens carry business semantics.
```

---

## 7. Modern Classifiers: What to Say Beyond the Basics

The role is unlikely to be only about NER.
You should be ready to discuss several classification problems.

### 7.1 Classification tasks in this system

- customer intent classification
- document type classification
- entity type classification
- benefit-category classification
- denial-reason classification
- urgency or escalation classification
- plan-fit classification
- multi-label need classification
- query routing classification

### 7.2 Important distinction: classification vs ranking

For plan recommendation, the last step is often not a plain classifier.
It is:

```text
filter invalid plans -> score valid plans -> rank top candidates
```

So say this clearly:

```text
I would use classification for attributes and intent,
but final plan recommendation is better framed as constrained ranking.
```

### 7.3 A good modern model stack

| Level | Model style | Use |
|---|---|---|
| Level 0 | rules and heuristics | obvious routing, plan IDs, hard constraints |
| Level 1 | TF-IDF + logistic regression / linear SVM | fast baselines, interpretable text classification |
| Level 2 | small encoder models | production latency-sensitive classification |
| Level 3 | stronger transformer encoders | harder semantic classification |
| Level 4 | LLM with schema and verifier | explanation, edge cases, fallback reasoning |

### 7.4 Model families to mention confidently

| Model family | Best use in this system | Tradeoff |
|---|---|---|
| Distilled or tiny encoders | intent routing, lightweight classification, CPU-sensitive services | fastest, lower headroom |
| BERT-style encoders | standard document and sentence classification | strong baseline quality |
| Stronger modern encoders | subtle semantic classification and harder edge cases | better quality, more cost |
| Domain-adapted biomedical or clinical encoders | medical notes, drug and condition language | better domain fit, more specialization |
| Long-context or hierarchical models | long evidence-of-coverage or policy documents | handles long inputs, more complex serving |

Interview line:

```text
I would not start with the biggest model everywhere.
I would use a cascade: small encoders for fast routing, stronger encoders for
harder semantic classification, and LLMs mainly for explanation or fallback.
```

### 7.5 Modern transformer-era classifier patterns

1. **Encoder-only classification**
   - strong choice for document or sentence classification
   - lower latency than generative models

2. **Multi-task learning**
   - one backbone, multiple classification heads
   - useful when tasks are related

3. **Hierarchical classification**
   - useful for taxonomies like `coverage -> pharmacy -> specialty drug coverage`

4. **Retrieval-augmented classification**
   - retrieve policy or product evidence before classification
   - useful when label meaning depends on current plan documents

5. **LLM-as-classifier with structured output**
   - good for rapid iteration
   - needs calibration and validation

### 7.6 When to use small vs large models

Small models are strong when:

- label space is stable
- latency is strict
- inputs are short
- cost matters

Stronger models help when:

- labels depend on long context
- domain semantics are subtle
- cross-sentence reasoning matters
- there are many edge cases

### 7.7 Classifiers that are especially useful here

- intent classifier for "compare plans" vs "check current coverage" vs "find in-network provider"
- missing-information classifier for whether the agent has enough facts to proceed
- eligibility classifier for enrollment pathway or program bucket
- dissatisfaction or escalation classifier for support workflows
- plan suitability scorer combining structured and text-derived features

### 7.8 Calibration and abstention

This is a high-value interview topic.

```text
In a high-stakes domain, the classifier should be calibrated and allowed to abstain.
Low-confidence cases should trigger clarification or human review, not forced decisions.
```

Useful metrics to mention:

- precision / recall / F1
- macro F1 for imbalanced classes
- AUROC if appropriate
- expected calibration error
- Brier score
- abstain rate
- business impact of false positives and false negatives

---

## 8. RAG for Plan Recommendation

RAG is needed because the relevant knowledge changes and lives outside the model.

### 8.1 Typical retrieval sources

- summary of benefits and coverage
- evidence of coverage
- formulary documents
- provider directories
- employer benefit documents
- regulatory guidance
- internal policy manuals
- FAQ and support knowledge base
- historical appeals or case notes if allowed

### 8.2 Why normal retrieval is not enough

Questions are often multi-constraint:

```text
Find plans in this county that cover Humira, include this cardiologist,
support spouse enrollment after a move, and keep monthly premium below a threshold.
```

That is not a single-vector similarity problem.
It combines:

- structured filters
- entity linking
- plan metadata retrieval
- text evidence retrieval

### 8.3 Best chunking strategy here

Chunk by document type:

- benefits docs -> section-aware chunking
- formularies -> table or row-aware chunking
- provider directories -> provider-entry chunking
- regulatory docs -> clause or section chunking
- policy docs -> heading and subsection chunking

Keep metadata such as:

- carrier
- plan ID
- plan year
- state
- county
- network
- drug tier
- source type
- effective date
- access control tags

### 8.4 Retrieval recipe

A good answer:

```text
I would use hybrid retrieval: lexical retrieval for plan codes, provider names,
drug names, and policy sections; dense retrieval for semantic questions; and a
reranker for the final top candidates. I would also apply metadata filters for
state, county, plan year, and permissions before generation.
```

### 8.5 Contextual retrieval is especially helpful here

If a chunk says:

```text
It requires prior authorization.
```

that chunk is weak in isolation.
With contextual retrieval, the chunk can be augmented with:

```text
This chunk is from Carrier X's 2026 Silver PPO formulary section for Humira in Arizona.
```

That makes pronouns and short statements retrievable and auditable.

---

## 9. Agentic RAG for the Right Plan

This is where you can sound especially strong.

### 9.1 What agentic RAG means here

The agent should not simply retrieve documents and answer.
It should:

- determine what facts are missing
- retrieve from the right sources
- call structured tools
- validate eligibility
- compare candidates
- produce an evidence-backed recommendation

### 9.2 A practical execution flow

```text
1. Intake customer request
2. Extract member / household / medication / provider / location facts
3. Resolve pronouns and entity references into session state
4. Ask clarifying questions if critical facts are missing
5. Run structured eligibility checks
6. Retrieve matching plan documents, formularies, and provider evidence
7. Generate candidate plans
8. Rank candidates with constraints and preferences
9. Produce explanation with citations
10. Validate citations and output schema
11. Escalate low-confidence cases
```

### 9.3 Example tool-routing logic

- if location is missing -> ask for ZIP or county
- if medication is ambiguous -> resolve brand/generic or dosage if needed
- if provider name is missing NPI or location -> query provider directory
- if plan year is unclear -> retrieve latest active plan year documents
- if evidence conflicts -> surface conflict instead of guessing

### 9.4 Important design principle

```text
The agent can orchestrate retrieval and evidence gathering,
but hard plan eligibility should still be validated by deterministic logic
or authoritative downstream systems.
```

### 9.5 Good interview language

```text
I would treat the agent as a workflow controller, not as the source of truth.
The source of truth should be the plan catalog, formulary, provider directory,
and eligibility engine.
```

---

## 10. Citation Correction and Claim Verification

In this domain, citations are not decorative.
They are part of trust and compliance.

### 10.1 What can go wrong

- answer is correct but cites the wrong document
- answer cites a generic brochure instead of the exact plan clause
- answer cites an outdated plan year
- answer combines two sources without making the conflict explicit
- answer cites a retrieved chunk that does not support the exact claim

### 10.2 The right validation pipeline

```text
generated answer
    ->
split into atomic claims
    ->
check each claim against cited source span
    ->
if unsupported, replace citation, revise claim, or abstain
```

### 10.3 What "citation correction" should mean

Do not let the model freely invent a better-looking citation.
Instead:

1. verify whether the cited source was actually retrieved
2. verify whether the retrieved text supports the claim
3. if not, search the retrieved set for a better supporting span
4. if still unsupported, revise or remove the claim
5. if no support exists, explicitly say evidence is insufficient

### 10.4 Authority and freshness

You should mention:

- current plan year vs old plan year
- official carrier document vs internal FAQ
- effective-date filtering
- latest authoritative source preference

This is a strong interview line:

```text
Grounded does not always mean correct.
A claim can be grounded in a stale source, so I also rank for authority and freshness.
```

### 10.5 Example answer policy

```text
Every factual recommendation claim should map to a source object containing
document ID, section, plan year, and span reference.
If a claim cannot be supported by current authoritative evidence, the system
should not present it as fact.
```

---

## 11. Constrained Decoding and Structured Outputs

Constrained decoding is extremely important in this kind of system.

### 11.1 What it solves

It helps enforce:

- valid JSON
- enums
- required fields
- tool-call syntax
- output schema consistency

It does **not** solve:

- factual correctness
- groundedness
- citation support
- stale source problems

### 11.2 Where to use it

Use constrained decoding for:

- extracted entity objects
- clarification-question objects
- plan comparison objects
- recommendation outputs
- citation objects
- tool calls

### 11.3 Example structured output

```json
{
  "member_profile": {
    "age": 62,
    "state": "AZ",
    "county": "Maricopa",
    "household_size": 2,
    "medications": ["Humira"],
    "preferred_specialists": ["cardiologist"]
  },
  "candidate_plans": [
    {
      "plan_id": "AZ-SILVER-PPO-204",
      "eligibility_status": "eligible",
      "fit_score": 0.84,
      "reasons": [
        "includes preferred cardiology network",
        "covers Humira with prior authorization"
      ],
      "citations": [
        {
          "document_id": "formulary_2026_carrier_x",
          "section": "Humira",
          "plan_year": 2026
        }
      ]
    }
  ],
  "needs_human_review": false
}
```

### 11.4 Best interview framing

```text
I use constrained decoding to make outputs machine-safe,
then I separately validate facts and citations against retrieved evidence.
```

---

## 12. Knowledge Graphs, Neo4j, and GraphRAG

This is a very natural fit for insurance and healthcare.

### 12.1 Why a knowledge graph helps

Flat text retrieval is not enough when the system must connect:

- a member
- their spouse or dependents
- preferred providers
- medications
- conditions
- candidate plans
- counties and networks
- plan years
- supporting policy clauses

Graph structure makes those relationships explicit.

### 12.2 Example node types

- `Member`
- `Household`
- `Plan`
- `Carrier`
- `Provider`
- `Facility`
- `Drug`
- `Condition`
- `FormularyEntry`
- `Network`
- `County`
- `PolicyDocument`
- `PolicySection`

### 12.3 Example relationships

- `(Member)-[:PART_OF]->(Household)`
- `(Member)-[:TAKES]->(Drug)`
- `(Member)-[:PREFERS]->(Provider)`
- `(Plan)-[:AVAILABLE_IN]->(County)`
- `(Plan)-[:USES_NETWORK]->(Network)`
- `(Provider)-[:IN_NETWORK_FOR]->(Plan)`
- `(Drug)-[:COVERED_BY]->(Plan)`
- `(Plan)-[:DOCUMENTED_IN]->(PolicyDocument)`
- `(PolicySection)-[:SUPPORTS]->(RecommendationClaim)`

### 12.4 Why Neo4j is useful

Neo4j is helpful for:

- explicit relationship traversal
- multi-hop reasoning
- plan explanation paths
- entity resolution and deduplication
- GraphRAG for entity-centric retrieval

### 12.5 How the graph gets built

The graph is usually created from:

- entity extraction
- relation extraction
- reference resolution
- document metadata
- canonical linking to plan, provider, and drug catalogs

This is another strong interview point:

```text
NER alone gives me isolated entities.
I need relation extraction and entity linking to turn those mentions into a usable knowledge graph.
```

### 12.6 Example Cypher question

```cypher
MATCH (m:Member {id: $member_id})-[:TAKES]->(d:Drug),
      (m)-[:PREFERS]->(p:Provider),
      (pl:Plan)-[:COVERS_DRUG]->(d),
      (p)-[:IN_NETWORK_FOR]->(pl),
      (pl)-[:AVAILABLE_IN]->(:County {name: $county})
RETURN pl.id, pl.name
```

### 12.7 When GraphRAG helps

GraphRAG is useful when:

- the question requires multi-hop reasoning
- there are many entity references across documents
- you want explanation paths, not just text similarity
- the same customer fact must be joined across systems

Example:

```text
Find plans available in this county that cover the member's medication,
include the spouse's cardiologist, and are valid after the move date.
```

That is naturally graph-shaped.

### 12.8 Important caution

```text
Do not use GraphRAG just because it sounds advanced.
Use it when relationships are structurally central to the answer.
```

---

## 13. GraphQL: What It Is Doing Here

GraphQL is not the reasoning engine and not the graph database.
It is the application API layer.

### 13.1 Good use cases

- frontend wants flexible plan comparison fields
- recommendation UI needs member, plan, provider, and citation data in one request
- client teams need typed access to entities and relationships

### 13.2 Example GraphQL types

```graphql
type MemberProfile {
  id: ID!
  age: Int
  county: String
  medications: [Drug!]!
  preferredProviders: [Provider!]!
}

type CandidatePlan {
  planId: ID!
  name: String!
  fitScore: Float!
  premium: Float
  deductible: Float
  reasons: [String!]!
  citations: [Citation!]!
}

type Query {
  recommendPlans(memberId: ID!): [CandidatePlan!]!
}
```

### 13.3 Interview distinction

```text
Neo4j stores relationships.
GraphRAG retrieves over those relationships plus source text.
GraphQL exposes the resulting data cleanly to applications.
```

---

## 14. A Strong End-to-End Architecture

```text
Customer chat + uploaded docs + enrollment forms
    ->
Python / FastAPI backend
    ->
OCR + parsing + code-aware normalization
    ->
entity extraction + coreference + entity linking
    ->
member profile state object
    ->
eligibility rules engine
    ->
hybrid retrieval over:
  - plan documents
  - formularies
  - provider directories
  - policy manuals
    ->
candidate plan generation
    ->
plan ranking model
    ->
citation-rich explanation generator
    ->
claim / citation validator
    ->
GraphQL or REST API
    ->
UI + agentic follow-up actions
```

### Storage pattern

- vector DB for semantic retrieval
- Neo4j for explicit relationships
- relational DB for canonical structured records
- object storage for source documents

### Good operational controls

- PHI / PII-aware access control
- per-source permissions
- full trace logs for decisions
- current vs stale plan version protection
- human escalation for low-confidence or high-risk cases

---

## 15. Observability, Safety, and Human Review

This section can differentiate you from candidates who only talk about models.

### 15.1 What to trace

- extracted entities and confidences
- resolved references and entity IDs
- retrieved documents and chunks
- ranking features and reasons
- generated claims and citations
- validation failures
- tool calls
- latency and cost

### 15.2 What to monitor

- extraction drift by source type
- plan recommendation disagreement rate
- citation support rate
- stale-source rate
- human override rate
- clarification-question rate
- retrieval recall for gold evidence

### 15.3 Counterfactual regression tests

Because one changed fact can change the right plan, I would maintain explicit test suites such as:

- same member profile, but county changes
- same member profile, but one medication is added
- same member profile, but spouse is added
- same member profile, but age changes from `64` to `65`
- same member profile, but plan year changes

What I want to validate:

- only the expected eligibility and ranking changes occur
- explanation text updates consistently
- citations switch to the correct plan year and source sections
- unchanged facts do not drift

This is a strong interview line:

```text
For plan recommendation, I would test counterfactual stability:
if one business-critical field changes, the output should change in the
expected way and for the right documented reason.
```

### 15.4 Human-in-the-loop triggers

- low confidence on member facts
- conflict between sources
- unsupported recommendation claim
- unusual eligibility path
- missing required fields
- high-cost or high-impact plan change

### 15.5 Best interview line

```text
In healthcare and insurance, I would optimize for safe recommendations,
not maximum autonomy. The system should know when to ask, verify, or escalate.
```

---

## 16. High-Value Interview Questions and Answers

### Q1. How would you build entity recognition for this plan-recommendation system?

I would define a domain ontology first, then use hybrid extraction: rules for plan IDs, dates, pricing, and structured codes; gazetteers for drugs, providers, and geography; and transformer-based extraction for context-sensitive facts like household relationships, intent, and plan preferences. I would normalize outputs and link them to canonical IDs before any decision logic runs.

### Q2. Why is pronoun resolution important here?

Because the system needs to know which person a condition, medication, provider preference, or life event belongs to. If "he" is the spouse but the system applies the medication to the primary member, the plan ranking can be wrong. I would combine coreference modeling with explicit conversation state and household entities.

### Q3. Is this a classification problem or a recommendation problem?

Both. Upstream tasks like intent detection, document classification, and benefit classification are standard classifiers. But final plan selection is better modeled as constrained ranking: filter invalid plans first, then score and rank the valid ones.

### Q4. Where would you use RAG?

I would use RAG for evidence retrieval from plan documents, formularies, provider directories, policy manuals, and current plan-year materials. The model should answer only from retrieved evidence and cite the exact supporting sections.

### Q5. What makes it agentic?

The agent decides what facts are missing, which data sources to query, which tools to call, whether evidence is sufficient, and whether it needs clarification or escalation before producing a recommendation.

### Q6. Why not let the LLM decide eligibility directly?

Because eligibility is a hard-rule problem with compliance implications. LLMs are useful for extraction and explanation, but authoritative decision logic should live in deterministic systems or validated rules engines.

### Q7. How would you do citation correction?

I would split the answer into claims, check each claim against retrieved evidence, and verify that the attached citation really supports it. If not, I would reattach a correct supporting source, revise the claim, or abstain if no evidence exists.

### Q8. What does constrained decoding solve here?

It ensures machine-safe output shape such as valid JSON, enums, required fields, and tool-call syntax. It does not guarantee correctness, so I would still validate facts and citations separately.

### Q9. When would you use a knowledge graph?

When the recommendation depends on relationships among members, dependents, providers, drugs, plans, geographies, and policy clauses. A graph is especially helpful for multi-hop reasoning and explanation paths.

### Q10. What is GraphQL doing in this design?

GraphQL gives the UI and downstream services a flexible way to fetch member data, candidate plans, reasons, citations, and comparison details from multiple backends through one API.

---

## 17. The Best Short Summary to Memorize

```text
For an insurance or healthcare plan recommendation role, I would build a
hybrid decision-support system. NLP extracts customer facts, resolves pronouns
and references, and normalizes entities like plans, drugs, providers, dates,
and locations. A deterministic eligibility layer removes invalid plans. Hybrid
retrieval and agentic RAG gather current plan, formulary, provider, and policy
evidence. Then a ranking layer scores the valid plans, and the system explains
the recommendation with claim-level citations, schema-constrained outputs, and
human escalation for low-confidence cases.
```

---

## 18. A 60-Second Interview Answer

```text
I would treat this as a high-stakes plan recommendation system rather than just
an LLM chatbot. The first job is to recover decision-critical facts from
conversation and documents: age, household structure, location, medications,
preferred providers, life events, and plan preferences. That requires
domain-specific entity extraction, coreference resolution for pronouns like
"he," "she," and "it," and normalization of plan, provider, and drug names.
Then I would run deterministic eligibility checks, use hybrid retrieval over
current plan documents, formularies, directories, and policy sources, and let
an agent orchestrate clarifications, tool calls, and evidence gathering.
Finally, I would rank valid plans and produce a citation-backed explanation
using constrained output schemas, claim verification, and human review when the
system is uncertain or the decision is high impact.
```
