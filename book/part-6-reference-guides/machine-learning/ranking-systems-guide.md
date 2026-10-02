# Ranking Systems and Machine Learning: A Complete Practical Guide

Prepared for interview preparation and real system design. Updated May 2026.

This guide explains modern ranking systems from first principles through production-scale machine learning: retrieval, two-tower models, learning to rank, deep rankers, reranking, marketplace and ad ranking, data collection, labels, evaluation, experimentation, serving, monitoring, and practical application patterns.

The central idea:

```text
A ranking system chooses the best ordered list of items for a user, query, context, and objective.
```

Ranking is everywhere:

- search results
- recommendations
- feeds
- ads
- ecommerce product ordering
- marketplace matching
- job matching
- short-video feeds
- music and movie recommendations
- news personalization
- email priority inboxes
- support ticket prioritization
- fraud and risk investigation queues
- candidate ranking in recruiting
- notification ranking
- autocomplete and typeahead
- RAG document ranking

The practical challenge is that the system must rank the right items, quickly, fairly, safely, and profitably, using noisy behavioral data.

---

## 1. The One-Sentence Definition

A ranking system maps:

```text
context + candidate items -> ordered list of items
```

The context can include:

- user identity
- query
- session history
- location
- device
- time
- intent
- page surface
- previous impressions
- business constraints

Candidate items can be:

- documents
- products
- videos
- posts
- ads
- jobs
- restaurants
- people
- answers
- notifications
- RAG chunks

The output is usually:

```text
item_1, item_2, item_3, ..., item_k
```

where earlier items are expected to have higher utility.

---

## 2. Ranking vs Classification vs Retrieval

Classification asks:

```text
Is this item relevant?
```

Retrieval asks:

```text
Which small subset should we consider from millions or billions of items?
```

Ranking asks:

```text
In what order should the candidate items be shown?
```

Recommendation asks:

```text
What should this user see next?
```

Search ranking asks:

```text
Which results best satisfy this query?
```

Ads ranking asks:

```text
Which ad should be shown, considering user value, advertiser value, marketplace rules, and long-term platform health?
```

RAG ranking asks:

```text
Which retrieved chunks should be sent to the LLM context?
```

Ranking is not only prediction. It is decision-making under constraints.

---

## 3. The Production Ranking Funnel

Large-scale ranking systems almost never score every item with the most expensive model.

They use a cascade.

```text
All available items
    |
    v
Candidate generation / retrieval
    |
    v
Light filtering
    |
    v
Pre-ranking
    |
    v
Main ranking
    |
    v
Reranking / slate optimization
    |
    v
Business rules, safety, diversity, freshness
    |
    v
Displayed list
```

Why the cascade exists:

- There may be billions of items.
- The user expects low latency.
- Rich models are expensive.
- Some constraints are easier after scoring.
- Ranking quality depends on both recall and precision.

Typical scale:

| Stage | Input Size | Output Size | Model Type |
| --- | ---: | ---: | --- |
| retrieval | millions to billions | hundreds to thousands | ANN, BM25, graph, two-tower |
| pre-rank | thousands | hundreds | small GBDT or neural model |
| rank | hundreds | tens | richer GBDT/deep/ranker ensemble |
| rerank | tens | final slate | diversity, constraints, calibration, exploration |

Interview line:

```text
Ranking is usually a multi-stage system. Retrieval optimizes recall under latency, ranking optimizes item-level utility, and reranking optimizes the final slate under business and user-experience constraints.
```

---

## 4. Core Concepts

| Term | Meaning |
| --- | --- |
| candidate generation | retrieving a manageable set of plausible items |
| retrieval | high-recall selection from a large corpus |
| ranker | model that scores candidates for ordering |
| reranker | model or algorithm that adjusts final list order |
| slate | final ordered list shown to the user |
| impression | item was shown |
| click | user clicked or tapped |
| conversion | user completed target action |
| dwell time | time spent after click/view |
| negative sample | item treated as not relevant |
| hard negative | plausible but not clicked/chosen item |
| position bias | higher-ranked items get more attention |
| propensity | probability an item was exposed or examined |
| CTR | click-through rate |
| CVR | conversion rate |
| GMV | gross merchandise value |
| eCPM | expected revenue per thousand impressions |
| NDCG | rank-aware metric for graded relevance |
| MRR | metric for first relevant result position |
| recall@k | fraction of relevant items retrieved in top k |
| calibration | predicted probabilities match observed frequencies |
| exploration | showing uncertain items to learn |
| exploitation | showing best-known items |

---

## 5. Ranking Objectives

A ranking system needs a utility function.

Examples:

```text
Search:
  utility = relevance + freshness + authority + satisfaction

Ecommerce:
  utility = purchase probability * margin * satisfaction adjustment

Ads:
  utility = p(click) * p(conversion | click) * bid * quality

Feed:
  utility = engagement + retention - hide/report risk - repetition penalty

Marketplace:
  utility = expected match quality + liquidity + fairness + trust

RAG:
  utility = answer usefulness + factual support + source trust + diversity
```

The hard part is that the true objective is rarely directly observed.

You often observe proxies:

- clicks
- likes
- purchases
- dwell time
- add-to-cart
- saves
- replies
- follows
- shares
- skips
- hides
- reports
- refunds
- churn

Good systems combine:

- short-term engagement
- long-term satisfaction
- business value
- safety
- fairness
- diversity
- latency
- explainability where needed

---

## 6. Common Ranking Use Cases

### 6.1 Web Search

Input:

```text
query + user context + corpus
```

Goal:

```text
rank documents that satisfy intent
```

Signals:

- lexical match
- semantic match
- page quality
- freshness
- authority
- location
- personalization
- click satisfaction
- dwell time
- query-document interaction

Architecture:

```text
BM25/dense retrieval -> neural/GBDT ranker -> reranking/diversity/safety
```

### 6.2 Ecommerce Search

Goal:

```text
rank products for query and shopper intent
```

Signals:

- text relevance
- price
- availability
- shipping speed
- ratings
- image quality
- past purchases
- conversion history
- margin
- seller quality
- returns/refunds
- inventory

Special constraints:

- do not show out-of-stock products
- avoid near-duplicates
- balance relevance and conversion
- handle cold-start products
- respect seller and marketplace rules

### 6.3 Recommendations

Goal:

```text
rank items the user may want next
```

Signals:

- user history
- item metadata
- collaborative behavior
- sequence patterns
- freshness
- popularity
- similarity
- diversity
- social graph
- location/time

Architecture:

```text
candidate generators -> ranker -> slate reranker -> exploration
```

### 6.4 Ads Ranking

Goal:

```text
select ads that maximize user value, advertiser value, and platform value
```

Common formula:

```text
ad_score = bid * predicted_action_rate * quality_adjustment
```

Where predicted action rate can be:

```text
pCTR
pCVR
pInstall
pPurchase
```

Ads ranking must consider:

- auction rules
- budgets
- frequency caps
- advertiser constraints
- user fatigue
- policy/safety
- long-term trust
- measurement and attribution

### 6.5 Marketplace Matching

Examples:

- jobs and candidates
- drivers and riders
- hosts and guests
- doctors and patients
- freelancers and clients

Ranking must optimize both sides:

```text
match_score(user, item) = demand-side value + supply-side value + marketplace health
```

Key issue:

```text
The best item for one user may consume supply that could be better used elsewhere.
```

This creates allocation and fairness problems beyond ordinary ranking.

### 6.6 Feeds

Examples:

- social feed
- short videos
- news feed
- professional feed

Goals:

- relevance
- freshness
- engagement
- creator ecosystem health
- retention
- safety
- diversity
- novelty

Feeds use ranking plus slate construction:

```text
avoid showing 10 similar items in a row
avoid repeated authors
promote fresh content
downrank low-quality engagement bait
mix exploration with exploitation
```

### 6.7 RAG Retrieval and Reranking

In RAG, ranking decides what context the LLM sees.

Pipeline:

```text
query -> lexical/dense retrieval -> reranker -> context packer -> LLM
```

Ranking errors become generation errors:

- missing evidence causes incomplete answers
- irrelevant evidence causes distraction
- contradictory chunks cause hallucination risk
- duplicate chunks waste context window

Common RAG ranking methods:

- BM25
- dense embeddings
- hybrid retrieval
- cross-encoder reranker
- LLM-as-reranker
- metadata filters
- source quality rules
- diversity-aware context packing

---

## 7. Data in Ranking Systems

Ranking quality depends heavily on data logging.

The system should log:

```text
request_id
user_id or anonymized user key
session_id
timestamp
surface
query
context features
candidate item ids
retrieval source
rank position
model scores
features or feature references
displayed items
clicks
conversions
dwell time
skips
hides
reports
purchase value
delayed outcomes
experiment bucket
policy version
model version
```

A minimal impression log:

| Field | Example |
| --- | --- |
| request_id | req_123 |
| user_id | u_42 |
| item_id | item_9 |
| query | running shoes |
| position | 3 |
| score | 0.781 |
| displayed | true |
| clicked | false |
| purchased | false |
| timestamp | 2026-05-15T10:21:00 |
| model_version | ranker_v14 |
| experiment | treatment_b |

Without position and exposure logging, ranking data is almost useless.

Why:

```text
An unclicked item at position 1 is different from an unclicked item that was never shown.
An unclicked item at position 50 may never have been examined.
```

---

## 8. Labels for Ranking

Ranking labels can be explicit or implicit.

### 8.1 Explicit Labels

Examples:

- human relevance judgments
- star ratings
- "is this result useful?"
- expert labels
- editorial quality scores

Advantages:

- less biased by historical rank
- can label unshown items
- useful for search relevance
- useful for cold start

Disadvantages:

- expensive
- may not match real user behavior
- requires label guidelines
- can have annotator disagreement

### 8.2 Implicit Labels

Examples:

- click
- purchase
- watch time
- add-to-cart
- save
- share
- skip
- hide
- report
- reply

Advantages:

- abundant
- behaviorally grounded
- cheap to collect

Disadvantages:

- biased by position
- biased by previous system
- noisy
- confounded by UI
- delayed
- ambiguous

Important:

```text
Click does not always mean relevance.
No click does not always mean irrelevance.
Purchase does not always mean satisfaction.
Long dwell does not always mean quality.
```

### 8.3 Graded Relevance

Many ranking systems use graded labels:

| Label | Meaning |
| ---: | --- |
| 0 | irrelevant |
| 1 | weakly relevant |
| 2 | relevant |
| 3 | highly relevant |
| 4 | perfect |

This supports metrics like NDCG.

### 8.4 Composite Labels

Production systems often define a weighted target:

```text
label = click
      + 3 * purchase
      + 0.1 * dwell_time_bucket
      - 5 * report
      - 2 * hide
```

Be careful. Composite labels encode product values.

Risks:

- over-optimizing engagement
- hiding long-term harm
- mixing incomparable actions
- creating incentives for bad content
- making calibration unclear

Better approach:

```text
Train separate heads for different outcomes, then combine them with an explicit decision function.
```

Example:

```text
score = 0.4 * p_click
      + 2.0 * p_purchase
      + 0.3 * expected_dwell
      - 4.0 * p_report
      - 1.5 * p_return
```

This makes tradeoffs more visible.

---

## 9. Biases in Ranking Data

Ranking logs are not IID data. They are generated by previous ranking policies.

Common biases:

| Bias | Meaning |
| --- | --- |
| position bias | top items get more attention |
| selection bias | only shown items get labels |
| presentation bias | UI changes behavior |
| popularity bias | popular items get more data and exposure |
| feedback loops | model promotes items that then collect more signals |
| survivorship bias | failed items disappear from logs |
| freshness bias | old items have more accumulated interactions |
| trust bias | users click known brands |
| confounding | treatment/exposure not random |
| delayed feedback | conversions happen later |

### 9.1 Position Bias

If an item is shown at position 1, it gets more clicks than if shown at position 10, even if relevance is identical.

Observed click:

```text
click = examination * attractiveness
```

The model sees:

```text
P(click | item, position)
```

but wants:

```text
P(relevance | item, query, user)
```

### 9.2 Debiasing Strategies

Common methods:

- randomized swaps
- interleaving experiments
- position-based click models
- inverse propensity weighting
- counterfactual learning to rank
- exploration buckets
- human labels
- train on randomized traffic slices
- include position during bias modeling, not as a relevance feature

Inverse propensity weighting idea:

```text
weighted_loss = observed_loss / probability_of_observation
```

If lower positions are rarely examined, their observed clicks receive more weight.

But IPW can have high variance if propensities are small.

Practical fix:

- clip weights
- use stabilized weights
- use randomized logging data
- combine with doubly robust estimators

---

## 10. Retrieval: The First Stage

Retrieval finds candidates from a huge corpus.

Goal:

```text
high recall at low latency
```

Retrieval should avoid missing good items.

Ranking can fix bad ordering among candidates, but it cannot rank an item that was never retrieved.

### 10.1 Retrieval Methods

| Method | Good For | Weakness |
| --- | --- | --- |
| rules | cold start, safety, exact filters | brittle |
| BM25 | keyword search | misses semantic similarity |
| dense embeddings | semantic match | can miss exact constraints |
| hybrid retrieval | search/RAG/ecommerce | more complex |
| collaborative filtering | user-item behavior | cold start |
| matrix factorization | scalable preference modeling | limited context |
| item-to-item similarity | related items | can over-repeat |
| graph retrieval | social/recommendation graphs | expensive, biased |
| two-tower | scalable personalized retrieval | limited cross features |
| sequence retrieval | next-item prediction | needs behavior history |
| generative retrieval | semantic IDs/item tokens | operationally newer |

### 10.2 Retrieval Metrics

Important retrieval metrics:

- recall@k
- hit rate@k
- coverage
- latency
- index freshness
- candidate source diversity
- downstream ranker lift

Retrieval evaluation should be downstream-aware.

Example:

```text
Retrieval model A has higher recall@1000.
Retrieval model B has lower recall but better final conversion because it retrieves more diverse and rankable candidates.
```

Both candidate quality and candidate mix matter.

---

## 11. Two-Tower Architecture

The two-tower model is one of the most important architectures in modern retrieval and recommendation.

It is also called:

- dual encoder
- bi-encoder
- two-tower retrieval model
- user-item embedding model
- query-document embedding model

### 11.1 Basic Idea

Two towers independently encode the two sides of a match.

```text
User / query / context tower:
  user_features, query_features, session_features -> vector u

Item / document tower:
  item_features, document_text, metadata -> vector v

Score:
  score(user, item) = dot(u, v)
```

Diagram:

```text
                user/query/context features
                          |
                          v
                    user tower
                          |
                          v
                    embedding u
                          |
                          | dot product / cosine
                          v
                    embedding v
                          ^
                          |
                    item tower
                          ^
                          |
                    item features
```

The key advantage:

```text
Item embeddings can be precomputed and indexed.
```

At request time:

```text
1. compute user/query embedding
2. search ANN index for nearest item embeddings
3. return top candidates
```

This is why two-tower models scale.

### 11.2 Why Two-Tower Models Are Used

They solve the retrieval bottleneck.

Without two-tower:

```text
score every user-item pair with a rich model
```

This is impossible at large scale.

With two-tower:

```text
precompute all item vectors
compute one user/query vector online
nearest-neighbor search retrieves candidates
```

Benefits:

- scalable to millions or billions of items
- low latency
- supports personalization
- supports semantic retrieval
- works for recommendation and search
- can combine text, IDs, categories, and behavior
- simple serving story

### 11.3 Inputs to the User Tower

User tower features:

- user ID embedding
- demographics, if allowed and ethical
- geography
- language
- membership tier
- long-term interests
- recent session events
- recent searches
- recent clicks
- recent purchases
- device
- time of day
- location
- price sensitivity
- creator/category affinities

For anonymous users:

- session behavior
- query
- referrer
- coarse location
- device
- trending/popular features

### 11.4 Inputs to the Item Tower

Item tower features:

- item ID embedding
- title/text embedding
- category
- brand
- price
- image embedding
- seller/creator features
- popularity
- freshness
- quality score
- availability
- language
- location
- historical CTR/CVR
- graph embeddings

For documents:

- title
- body text
- URL/domain
- author
- freshness
- authority
- embedding from text encoder

For videos:

- creator
- transcript
- visual embedding
- audio embedding
- tags
- watch-time stats
- safety labels

### 11.5 Scoring Functions

Common scores:

```text
dot(u, v)
cosine_similarity(u, v)
u^T W v
MLP([u, v, u * v, |u - v|])
```

For retrieval, dot product is common because ANN libraries support it efficiently.

### 11.6 Training Objective

A common objective is sampled softmax.

For one positive item and many negatives:

```text
P(item_positive | user) =
  exp(score(user, positive) / temperature)
  /
  sum_j exp(score(user, item_j) / temperature)
```

Loss:

```text
loss = -log P(item_positive | user)
```

This pulls positive pairs together and pushes negative pairs apart.

### 11.7 In-Batch Negatives

In-batch negatives use other examples in the batch as negatives.

If batch has 1024 positive user-item pairs:

```text
each user has 1 positive and 1023 in-batch negatives
```

Benefits:

- efficient
- many negatives for free
- works well with contrastive training

Risks:

- false negatives
- popularity bias
- batch composition matters

False negative example:

```text
User A bought item X.
Item Y is treated as negative only because user A did not buy it in this batch.
But user A may also like item Y.
```

### 11.8 Negative Sampling

Common negative types:

- random negatives
- popularity-weighted negatives
- in-batch negatives
- hard negatives from retrieval
- hard negatives from current model mistakes
- unclicked impressions
- same-category negatives
- cross-category negatives
- adversarial negatives

Random negatives are easy but often too easy.

Hard negatives are more informative but can include false negatives.

Good practice:

```text
mix easy negatives, hard negatives, and logged non-clicked impressions
```

### 11.9 Temperature

Temperature controls softmax sharpness.

```text
lower temperature -> sharper distribution -> stronger push apart
higher temperature -> smoother distribution
```

Temperature affects embedding geometry, recall, and training stability.

### 11.10 Serving a Two-Tower Model

Offline:

```text
compute item embeddings
build ANN index
publish index
```

Online:

```text
read user/session/query features
compute user/query embedding
ANN search top N items
apply filters
send candidates to ranker
```

### 11.11 ANN Search

Approximate nearest neighbor search trades exactness for speed.

Popular methods and tools:

- FAISS
- ScaNN
- HNSW
- Annoy
- Milvus
- Vespa
- Elasticsearch/OpenSearch vector search
- pgvector for smaller or operationally simple cases

ANN parameters affect:

- recall
- latency
- memory
- update speed
- filtering support

### 11.12 Limitations of Two-Tower Models

Two-tower retrieval is powerful but limited.

Main weakness:

```text
The user tower and item tower do not deeply interact before scoring.
```

This makes it hard to model:

- exact query-item term interactions
- complex feature crosses
- price sensitivity by category
- user intent interacting with item details
- rule-heavy constraints
- fine-grained relevance
- subtle language matching

Example:

```text
Query: "apple laptop charger"
Item: "Apple fruit slicer"
```

Dense embeddings may overmatch semantic proximity unless lexical and category constraints help.

That is why two-tower is usually retrieval, not final ranking.

### 11.13 Improving Two-Tower Retrieval

Common improvements:

- add query tokens and text encoders
- use separate towers per surface
- train multi-task objectives
- include sequence models in user tower
- use hard negative mining
- use multiple embeddings per user/item
- use hybrid lexical + dense retrieval
- add popularity/freshness retrieval sources
- use item availability filters
- calibrate retrieval sources
- add ANN index refresh pipeline
- train with examples from randomized or diverse traffic

---

## 12. Beyond Two-Tower Retrieval

### 12.1 Multi-Vector Retrieval

A single vector may not represent all user interests.

Example:

```text
User likes:
  running shoes
  Python books
  espresso machines
```

A single embedding may blur these interests.

Multi-vector methods represent a user or item with multiple vectors.

Benefits:

- captures multiple interests
- improves diversity
- supports multiple intents

Costs:

- more index queries
- more merging logic
- more memory
- harder serving

### 12.2 Sequential Recommendation

Sequential recommenders use the order of user actions.

Examples:

```text
viewed phone -> viewed phone case -> viewed charger
```

This suggests next-item intent.

Common architectures:

- GRU/RNN sequence models
- SASRec-style self-attention
- BERT4Rec-style masked item modeling
- transformer encoders
- hierarchical sequence models
- session-based recommenders

Inputs:

- item sequence
- action type
- timestamp
- dwell time
- query sequence
- category sequence
- device/context

Use cases:

- short-video feeds
- ecommerce sessions
- music/video recommendations
- next-best action
- news feeds
- recently viewed products

### 12.3 Graph-Based Retrieval

Ranking ecosystems naturally form graphs:

```text
user -> item
item -> category
item -> creator
user -> user
query -> item
item -> item
```

Graph methods:

- item-item co-occurrence
- random walks
- Personalized PageRank
- graph embeddings
- graph neural networks
- knowledge graph retrieval

Good for:

- related items
- social recommendations
- marketplace trust
- cold-start with metadata
- explainable "because you viewed X"

Risks:

- reinforces popularity
- can be stale
- expensive at scale
- graph leakage across time

### 12.4 Hybrid Retrieval

Modern systems often combine candidate sources:

```text
source 1: lexical/BM25
source 2: two-tower personalized retrieval
source 3: item-to-item similarity
source 4: trending items
source 5: fresh content
source 6: editorial/sponsored candidates
source 7: graph retrieval
```

Then merge and deduplicate:

```text
candidate_pool = union(source_candidates)
candidate_pool = apply_filters(candidate_pool)
candidate_pool = dedupe(candidate_pool)
candidate_pool = pass_to_ranker(candidate_pool)
```

Why hybrid retrieval works:

- different sources catch different intents
- lexical protects exact matching
- dense retrieval adds semantic matching
- graph retrieval captures behavior
- freshness source helps cold-start items
- popularity source gives robust fallback

---

## 13. Pre-Ranking

Pre-ranking is a middle stage between retrieval and the main ranker.

Purpose:

```text
reduce thousands of candidates to hundreds using a cheap model
```

Typical input:

```text
1000 to 10000 candidates
```

Output:

```text
100 to 1000 candidates
```

Pre-ranker features:

- retrieval score
- source ID
- item popularity
- user-category affinity
- query-item lexical match
- item freshness
- simple price/availability features
- lightweight embeddings

Models:

- logistic regression
- small GBDT
- shallow neural network
- small two-tower score
- distilled model from final ranker

Why pre-ranking matters:

- protects ranker latency
- improves candidate quality
- allows expensive ranker to focus
- can merge candidates from many sources

Risk:

```text
If pre-rank drops good candidates, the final ranker cannot recover them.
```

Therefore pre-rank should optimize recall of final-good items, not only immediate precision.

---

## 14. Main Ranking Models

The main ranker scores a manageable set of candidates using richer features.

Common model families:

- linear models
- gradient boosted decision trees
- LambdaMART
- neural CTR/CVR models
- Wide & Deep
- DeepFM/xDeepFM
- Deep & Cross Network
- DLRM
- DIN/DIEN/BST-style behavior models
- transformer-based rankers
- cross-encoders
- multi-task networks
- ensembles

### 14.1 Pointwise Ranking

Pointwise ranking treats ranking as prediction for each item.

Example:

```text
predict p(click | user, item, context)
```

Then rank by score.

Common losses:

- binary cross-entropy
- mean squared error
- Poisson loss for counts
- regression loss for dwell time

Advantages:

- simple
- scalable
- works with CTR/CVR
- easy calibration
- easy business score composition

Disadvantages:

- does not directly optimize rank order
- may ignore within-query competition
- sensitive to label bias

### 14.2 Pairwise Ranking

Pairwise ranking learns that one item should be above another.

Training example:

```text
for same request:
  clicked item > unclicked item
```

Loss idea:

```text
loss = log(1 + exp(-(score_positive - score_negative)))
```

Advantages:

- directly learns preferences
- useful when only relative labels matter

Disadvantages:

- many item pairs
- noisy preferences
- clicks are biased by position

### 14.3 Listwise Ranking

Listwise ranking optimizes the whole ranked list.

Examples:

- LambdaRank
- LambdaMART
- ListNet
- ListMLE
- softmax losses
- differentiable NDCG approximations

Advantages:

- closer to ranking metrics
- handles graded relevance
- strong for search ranking

Disadvantages:

- more complex
- needs query/request grouping
- training can be expensive

---

## 15. Learning to Rank

Learning to rank, or LTR, is the family of supervised methods for optimizing order.

Classic setting:

```text
query q
documents d1, d2, ..., dn
labels y1, y2, ..., yn
learn score(q, d)
```

Then sort documents by score.

LTR is common in:

- search engines
- ecommerce search
- document retrieval
- legal search
- enterprise search
- RAG reranking
- recommendation reranking

### 15.1 LambdaMART

LambdaMART combines:

- LambdaRank-style gradient signals
- MART, a gradient boosted tree algorithm

It is historically one of the strongest learning-to-rank methods.

Why it works well:

- handles tabular features
- captures nonlinear interactions
- robust with mixed feature types
- strong on medium-sized data
- easy to inspect compared with deep models
- works well with NDCG-like objectives

Common tools:

- LightGBM LambdaRank
- XGBoost rank objectives
- CatBoost ranking
- RankLib

### 15.2 Feature Groups for LTR

Query features:

- query length
- query category
- query frequency
- query intent
- language
- spelling correction confidence

Document/item features:

- popularity
- freshness
- quality
- authority
- rating
- price
- availability
- seller quality

Query-item features:

- BM25 score
- dense similarity
- title match
- category match
- brand match
- phrase match
- embedding similarity
- cross-encoder score

User features:

- preferences
- past actions
- location
- device
- membership tier
- price sensitivity

Context features:

- time
- surface
- page type
- inventory
- experiment

### 15.3 LTR Grouping

For listwise and pairwise ranking, examples must be grouped by request/query.

Example training group:

```text
query: "wireless headphones"
items:
  item_a label=3
  item_b label=2
  item_c label=0
  item_d label=1
```

The model learns the relative ordering inside the group.

Important:

```text
Do not randomly shuffle items across requests for group-based ranking losses.
```

---

## 16. Gradient Boosted Trees in Ranking

GBDT models remain very strong for ranking.

Why:

- strong on tabular data
- handles nonlinear feature interactions
- robust to feature scaling
- quick to train
- interpretable enough for debugging
- great baseline
- often hard to beat with deep models when data is mostly tabular

Use GBDT when:

- you have engineered features
- data is not huge enough for deep models
- explainability matters
- serving latency must be low
- you need a strong first production ranker

Common objectives:

- binary classification for CTR
- regression for value
- LambdaRank/LambdaMART for NDCG
- pairwise ranking loss

Limitations:

- less natural with huge sparse ID features
- not ideal for raw text/image/audio
- less effective for representation learning
- feature engineering burden

Practical pattern:

```text
Use two-tower or embedding models for retrieval.
Use GBDT/LambdaMART as a strong ranker over engineered and neural features.
```

This hybrid is common and effective.

---

## 17. Deep Ranking Models

Deep rankers learn representations and feature interactions.

They are useful when:

- you have huge sparse categorical features
- item/user IDs matter
- raw text/image/audio features matter
- sequence behavior matters
- personalization is critical
- multi-task learning is needed
- embeddings are shared across retrieval and ranking

### 17.1 Wide & Deep

Wide & Deep combines:

```text
wide linear memorization
deep neural generalization
```

Wide part:

- memorizes feature crosses
- good for known associations

Deep part:

- learns embeddings
- generalizes to unseen combinations

Use cases:

- app recommendations
- ads
- ecommerce
- personalization

### 17.2 DeepFM and Factorization Machines

Factorization machines model feature interactions through embeddings.

DeepFM combines:

- FM component for low-order interactions
- neural network for high-order interactions

Good for:

- CTR prediction
- ads ranking
- recommendation ranking

### 17.3 Deep & Cross Network

DCN explicitly models feature crosses.

Useful when:

- cross features are important
- sparse categorical features dominate
- you want learned feature crossing without manual crosses

Examples:

```text
user_age x category
query_brand x item_brand
price_sensitivity x item_price
location x restaurant_distance
```

### 17.4 DLRM

DLRM, or Deep Learning Recommendation Model, is a widely known architecture for recommendation ranking.

Core idea:

- embed sparse categorical features
- transform dense numerical features
- compute feature interactions
- feed interactions to MLP

Good for:

- large-scale ads
- recommendations
- CTR/CVR prediction

### 17.5 DIN and DIEN

Deep Interest Network models user interest with attention over behavior history.

Example:

```text
candidate item: running shoes
user history: laptop, socks, running shorts, water bottle
```

The model can attend more to:

```text
running shorts, socks, water bottle
```

and less to:

```text
laptop
```

This is important because user interests are candidate-dependent.

DIEN adds interest evolution over time.

### 17.6 Transformer Rankers

Transformers are used for:

- sequence modeling
- query-document matching
- session recommendation
- cross-encoder reranking
- multimodal ranking
- slate context modeling

Benefits:

- strong sequence modeling
- attention over behavior
- can process text and metadata
- good for cross interactions

Costs:

- latency
- memory
- serving complexity
- harder debugging

### 17.7 Cross-Encoders

A cross-encoder jointly processes the query and item.

Example:

```text
input: [query tokens] [SEP] [document tokens]
output: relevance score
```

Benefits:

- strong relevance
- models fine-grained interactions
- excellent reranker for search/RAG

Costs:

- cannot precompute item embeddings independently
- expensive per candidate
- usually used after retrieval

Use:

```text
retrieve top 1000 -> cross-encoder rerank top 100
```

### 17.8 Multi-Task Ranking Models

A ranking item can have many outcomes:

- click
- like
- share
- purchase
- conversion
- dwell
- skip
- hide
- report
- return
- churn impact

Instead of one label, train multiple heads:

```text
shared representation -> CTR head
                     -> CVR head
                     -> dwell head
                     -> report-risk head
                     -> long-term value head
```

Benefits:

- learns shared structure
- supports explicit utility composition
- can model tradeoffs
- improves rare-task learning

Architectures:

- shared-bottom network
- mixture of experts
- multi-gate mixture of experts
- expert routing
- task-specific towers

Risk:

- task interference
- unstable objectives
- poor calibration across heads

---

## 18. Ranking Score Construction

The model may output one score or many scores.

### 18.1 Single-Score Ranking

Simple:

```text
score = model(user, item, context)
rank by score descending
```

Good for:

- relevance
- basic recommendation
- simple search

### 18.2 Multi-Objective Ranking

Production systems often combine multiple predictions:

```text
score =
    w1 * p_click
  + w2 * p_purchase
  + w3 * expected_watch_time
  + w4 * expected_margin
  - w5 * p_report
  - w6 * p_return
  + w7 * freshness_bonus
```

Advantages:

- explicit tradeoffs
- easier product tuning
- supports guardrails
- separates prediction from decision

Disadvantages:

- weights can be political
- interactions may be missed
- tuning can overfit A/B tests
- calibration matters

### 18.3 Expected Value Ranking

Ecommerce example:

```text
expected_profit =
    p_purchase * margin
  - p_return * return_cost
  - p_bad_experience * support_cost
```

Ads example:

```text
expected_ad_value =
    bid * p_click * p_conversion_given_click * quality_adjustment
```

Feed example:

```text
feed_score =
    expected_satisfaction
  + expected_session_value
  - expected_negative_feedback
```

### 18.4 Calibration

If a model says:

```text
p_click = 0.20
```

then among similar examples, about 20 percent should click.

Calibration matters when scores are combined.

Examples:

```text
score = p_click * price
score = p_conversion * bid
score = p_purchase * margin
```

If probabilities are miscalibrated, business decisions become wrong.

Calibration methods:

- Platt scaling
- isotonic regression
- temperature scaling
- beta calibration
- group-wise calibration
- online calibration layers

Check calibration by:

- reliability plots
- expected calibration error
- calibration by segment
- calibration by position
- calibration by time
- calibration by traffic source

---

## 19. Reranking and Slate Optimization

The final list is not just independent top scores.

A user sees a slate.

Problems with naive top-k:

- too many similar items
- repeated sellers/creators
- no fresh content
- no exploration
- filter bubble
- business constraints violated
- unsafe adjacency
- poor category coverage
- cannibalization

### 19.1 Reranking Goals

Reranking can enforce:

- diversity
- novelty
- freshness
- fairness
- creator/seller caps
- topic balance
- price range balance
- inventory constraints
- geography constraints
- safety constraints
- ad load constraints
- sponsored/organic blending
- exploration

### 19.2 Maximal Marginal Relevance

MMR balances relevance and diversity.

```text
select item that maximizes:
  lambda * relevance(item)
  - (1 - lambda) * max_similarity(item, selected_items)
```

High lambda:

```text
more relevance
```

Low lambda:

```text
more diversity
```

Use cases:

- search results
- RAG context packing
- product recommendations
- news feeds

### 19.3 Rules and Constraints

Examples:

```text
no more than 2 items from same seller in top 10
no duplicate product variants in top 20
at least 3 fresh items in top 50
do not show unavailable items
do not show blocked creators
respect frequency caps
```

Constraints can be:

- hard constraints
- soft penalties
- post-processing rules
- optimization constraints

Hard constraints protect safety and correctness.

Soft constraints tune experience.

### 19.4 Learning to Rerank

More advanced rerankers model the whole slate.

Inputs:

```text
candidate item scores
candidate embeddings
already selected items
position
user context
slate context
```

Output:

```text
next item to place
```

Methods:

- greedy reranking
- sequence models
- pointer networks
- reinforcement learning
- contextual bandits
- constrained optimization

Hard part:

```text
The value of an item depends on what else is shown.
```

Example:

```text
A running shoe is good.
Ten similar running shoes in a row is not.
```

---

## 20. Exploration and Bandits

Ranking systems create their own data.

If you only show what the current model likes, you learn less about unseen items.

This creates feedback loops.

Exploration deliberately shows uncertain items to learn.

### 20.1 Exploration vs Exploitation

Exploitation:

```text
show items believed to be best
```

Exploration:

```text
show uncertain items to learn their value
```

Too much exploitation:

- stale results
- popularity bias
- cold-start failure
- poor long-term discovery

Too much exploration:

- worse short-term experience
- lower conversion
- user frustration

### 20.2 Common Exploration Methods

- epsilon-greedy
- Thompson sampling
- upper confidence bound
- contextual bandits
- randomized interleaving
- traffic slices for exploration
- uncertainty bonuses
- fresh-item boosts

### 20.3 Where Exploration Is Applied

- candidate generation source allocation
- fresh item exposure
- creator/seller discovery
- ads bidding and quality estimation
- notification ranking
- recommendations
- search result swaps for debiasing

Important:

```text
Log propensities when using exploration.
```

This enables counterfactual evaluation.

---

## 21. Evaluation Metrics

Ranking evaluation must cover:

- offline ranking quality
- online user/business impact
- calibration
- diversity
- fairness
- latency
- robustness

### 21.1 Precision@k

```text
precision@k = relevant items in top k / k
```

Good when:

- only top results matter
- binary relevance
- user sees fixed number of results

Weakness:

- ignores order within top k
- ignores relevance grades

### 21.2 Recall@k

```text
recall@k = relevant items in top k / total relevant items
```

Good for:

- retrieval evaluation
- candidate generation
- RAG retrieval

Weakness:

- total relevant set may be unknown
- not enough for final rank quality

### 21.3 Hit Rate@k

```text
hit_rate@k = 1 if at least one relevant item appears in top k else 0
```

Common in recommendation.

### 21.4 MRR

Mean reciprocal rank:

```text
MRR = average(1 / rank_of_first_relevant_item)
```

Good when the first good result matters.

Examples:

- question answering
- known-item search
- typeahead

### 21.5 MAP

Mean average precision rewards ranking all relevant items high.

Useful in information retrieval when there are multiple relevant documents.

### 21.6 DCG and NDCG

Discounted cumulative gain:

```text
DCG@k = sum_i gain_i / log2(i + 1)
```

NDCG normalizes by ideal DCG:

```text
NDCG@k = DCG@k / IDCG@k
```

Why NDCG is popular:

- handles graded relevance
- rewards top positions more
- normalized per query
- strong for search and LTR

### 21.7 AUC

AUC measures whether positives score above negatives.

Useful for:

- binary ranking models
- CTR models
- candidate scoring

Weakness:

- not top-k focused
- can hide poor top positions
- can look good with class imbalance

### 21.8 Log Loss

Log loss evaluates probability quality.

Useful for:

- calibrated CTR/CVR prediction
- expected value ranking
- ads

Weakness:

- not directly rank-aware

### 21.9 Business Metrics

Examples:

- conversion rate
- revenue per session
- gross merchandise value
- retention
- watch time
- search success rate
- add-to-cart rate
- booking rate
- advertiser ROI
- marketplace liquidity

### 21.10 Guardrail Metrics

Examples:

- latency
- error rate
- diversity
- negative feedback
- return/refund rate
- user complaints
- hide/report rate
- creator/seller concentration
- fairness metrics
- calibration drift
- cold-start exposure

### 21.11 Diversity Metrics

- category coverage
- creator coverage
- intra-list diversity
- average pairwise dissimilarity
- entropy of categories
- Gini coefficient of exposure
- long-tail exposure

### 21.12 Freshness Metrics

- average item age
- fresh item exposure
- fresh item success rate
- time-to-first-impression
- index update latency

### 21.13 Fairness and Exposure Metrics

Ranking controls exposure.

Fairness metrics can include:

- exposure parity
- equal opportunity
- demographic parity, where appropriate
- seller/creator concentration
- protected-group representation
- disparate impact
- fairness of allocation

Fairness must be defined with domain and legal context.

---

## 22. Offline Evaluation vs Online Experiments

Offline evaluation answers:

```text
Does the model rank historical logged data better?
```

Online A/B testing answers:

```text
Does the model improve real user behavior when deployed?
```

They often disagree.

Reasons:

- offline data is biased by previous model
- labels are noisy
- users react to changed ranking
- model changes candidate distribution
- metrics are proxies
- exploration changes data
- long-term effects are not visible offline

### 22.1 Offline Evaluation Best Practices

- split by time, not random rows
- group by request/query/user
- avoid leakage from future interactions
- evaluate by segment
- compare to current production policy
- evaluate retrieval and ranking separately
- test calibration
- test latency
- test cold-start items
- test new users
- test tail queries
- test popular queries
- test failure cases

### 22.2 Online Experiment Best Practices

- define primary metric
- define guardrails
- decide unit of randomization
- check sample ratio mismatch
- monitor ramp carefully
- run long enough for delayed effects
- segment results
- check novelty effects
- check long-term retention
- do not overfit repeated experiments

### 22.3 Interleaving

Interleaving compares two rankers in the same user session by mixing their results.

Good for:

- search ranking
- fast preference testing
- lower variance than A/B for relevance

Risk:

- harder to apply when items interact strongly
- business metrics may need standard A/B

---

## 23. Training Data Construction

Training data quality is the backbone of ranking.

### 23.1 Point-in-Time Correctness

All features must be known at ranking time.

Bad:

```text
feature = total purchases after impression
```

Good:

```text
feature = purchases before impression timestamp
```

Leakage is especially easy in ranking because item popularity and user history evolve.

### 23.2 Negative Examples

What is a negative?

Options:

- shown but not clicked
- shown but skipped
- retrieved but not shown
- random catalog item
- item from same query group
- hard negative from model

Each means something different.

Best practice:

```text
Use negatives that match the serving stage.
```

For retrieval:

- random negatives
- in-batch negatives
- hard negatives
- unclicked retrieved items

For ranking:

- candidates shown in same request
- clicked vs unclicked impressions
- converted vs non-converted candidates

For reranking:

- full slate outcomes
- position-aware labels

### 23.3 Sampling

Ranking data is often huge.

Sampling choices:

- downsample easy negatives
- keep all positives
- sample by request
- sample by user
- sample by query frequency
- balance head and tail
- preserve group structure

If you downsample negatives, remember:

```text
predicted probabilities may need correction/calibration
```

### 23.4 Delayed Feedback

Conversions may occur later.

Examples:

- purchase after click
- booking after search
- subscription after trial
- return/refund weeks later

Approaches:

- wait fixed attribution window
- train separate short-term and long-term labels
- model delayed feedback
- use survival/hazard models
- update labels when feedback arrives

### 23.5 Data Splits

Good splits:

- train on older period
- validate on later period
- test on most recent holdout

For recommendation, also evaluate:

- new users
- new items
- cold-start categories
- tail users
- heavy users
- geography/language segments

Avoid random row splits when interactions from the same session appear in train and test.

---

## 24. Feature Engineering for Ranking

### 24.1 User Features

- user ID embedding
- long-term category affinities
- recent session behavior
- purchase history
- price sensitivity
- brand affinity
- location
- language
- device
- subscription tier
- churn risk
- trust/safety state

### 24.2 Item Features

- item ID embedding
- category
- brand
- price
- quality
- rating
- inventory
- shipping time
- freshness
- popularity
- image/text embeddings
- seller/creator features
- historical CTR/CVR
- return/refund rate

### 24.3 Query Features

- query text
- query embedding
- query length
- detected category
- intent
- spelling correction
- brand/entity extraction
- location intent
- commercial intent

### 24.4 User-Item Features

- user-category affinity
- user-brand affinity
- user-price compatibility
- distance to item
- similarity to viewed items
- similarity to purchased items
- previously seen item
- creator already followed
- item matches recent query

### 24.5 Query-Item Features

- BM25
- exact match
- phrase match
- semantic similarity
- category match
- brand match
- attribute match
- cross-encoder score

### 24.6 Context Features

- time of day
- day of week
- seasonality
- device
- page surface
- network
- user journey step
- experiment bucket
- inventory state

### 24.7 Feature Freshness

Some features must be real-time:

- inventory
- price
- availability
- recent clicks
- session actions
- safety state

Some can be batch:

- long-term preferences
- item embeddings
- historical popularity
- seller quality

Common architecture:

```text
offline feature store + online feature store + streaming features
```

---

## 25. System Architecture

### 25.1 Offline Training Pipeline

```text
logs
  -> sessionization
  -> label generation
  -> feature joins
  -> train/validation/test split
  -> model training
  -> offline evaluation
  -> calibration
  -> model registry
  -> deployment
```

### 25.2 Online Serving Pipeline

```text
request
  -> parse context
  -> retrieve candidates
  -> apply filters
  -> fetch features
  -> pre-rank
  -> rank
  -> rerank
  -> apply final constraints
  -> return slate
  -> log impressions and outcomes
```

### 25.3 Embedding Index Pipeline

```text
item catalog
  -> item feature generation
  -> item tower inference
  -> embeddings
  -> ANN index build
  -> index validation
  -> publish index
```

For fresh items:

- stream new item embeddings
- maintain delta index
- use fallback retrieval
- use freshness candidate source

### 25.4 Latency Budget

Example:

| Stage | Budget |
| --- | ---: |
| request parsing | 2 ms |
| candidate retrieval | 20 ms |
| feature fetch | 20 ms |
| pre-rank | 10 ms |
| main rank | 30 ms |
| rerank/rules | 10 ms |
| logging/response overhead | 8 ms |
| total | 100 ms |

Real budgets depend on product surface.

Search may tolerate more latency than feed scroll.

Ads often have very strict latency.

### 25.5 Fallbacks

Always design fallbacks:

- if ANN index unavailable, use popular/trending
- if user features missing, use session/query features
- if item features missing, use metadata defaults
- if ranker fails, use previous stable ranker
- if feature store times out, use cached features
- if personalization unavailable, use non-personalized ranking

---

## 26. Applying Ranking Methods: Practical Recipes

### 26.1 Build an Ecommerce Search Ranker

Start:

```text
query -> retrieve products -> rank products -> show top results
```

Step 1: Retrieval

- BM25 over title/description/attributes
- dense query-product retrieval
- category/entity filters
- popularity/freshness candidates

Step 2: Labels

- query-product clicks
- add-to-cart
- purchases
- returns
- reformulations
- zero-result sessions

Step 3: Features

- query-product text match
- category match
- brand match
- price
- availability
- shipping
- product rating
- seller quality
- historical CTR/CVR
- query intent

Step 4: Model

- start with LambdaMART or GBDT
- use NDCG and conversion metrics
- add neural embeddings as features
- later add deep ranker if needed

Step 5: Rerank

- dedupe variants
- ensure availability
- diversify brands/sellers
- apply sponsored blending
- boost freshness carefully

Step 6: Online test

- search success
- purchase rate
- revenue
- reformulation rate
- latency
- refund rate

### 26.2 Build a Personalized Recommendation System

Step 1: Candidate generation

- two-tower personalized retrieval
- item-to-item from recent views
- trending/popular
- fresh items
- graph candidates

Step 2: User representation

- long-term interests
- short-term session sequence
- recent actions
- negative feedback

Step 3: Ranking labels

- clicks
- dwell
- saves
- purchases
- hides
- reports

Step 4: Model

- GBDT baseline over features
- deep CTR model with embeddings
- sequence model for session intent
- multi-task model for engagement and negative feedback

Step 5: Reranking

- diversity
- creator caps
- freshness
- exploration
- repetition penalties

Step 6: Evaluation

- engagement quality
- retention
- negative feedback
- diversity
- creator ecosystem metrics

### 26.3 Build an Ads Ranking System

Step 1: Candidate ads

- targeting constraints
- eligibility
- budget
- auction participation

Step 2: Predict outcomes

- pCTR
- pCVR
- expected value
- user negative feedback
- quality

Step 3: Score

```text
ad_rank_score = bid * pCTR * pCVR * quality_adjustment
```

or:

```text
expected_platform_value =
    advertiser_bid * predicted_action
  + long_term_user_value_adjustment
  - negative_feedback_cost
```

Step 4: Constraints

- budget pacing
- frequency caps
- policy
- category blocking
- user fatigue

Step 5: Evaluate

- CTR/CVR
- advertiser ROI
- revenue
- user retention
- ad hide/report rate
- calibration
- auction health

### 26.4 Build a Job Matching Ranker

Candidates:

- jobs for candidate
- candidates for recruiter

Signals:

- skills
- title match
- location
- salary
- seniority
- industry
- work authorization
- preferences
- application history
- recruiter response

Special care:

- fairness
- legal compliance
- explainability
- protected attributes
- feedback loops
- marketplace balance

Model:

- two-tower for retrieval
- cross features for ranking
- multi-objective score for candidate interest and employer response
- constraints for fairness and diversity

### 26.5 Build a RAG Ranking System

Step 1: Chunk and index documents.

Step 2: Retrieve candidates:

- BM25
- dense embeddings
- metadata filters
- graph links

Step 3: Rerank:

- cross-encoder
- LLM reranker for small candidate sets
- source quality
- recency
- authority

Step 4: Pack context:

- remove duplicates
- include diverse evidence
- avoid contradictions where possible
- respect token budget

Metrics:

- recall@k
- MRR
- answer faithfulness
- context precision
- context recall
- citation accuracy
- latency

---

## 27. Choosing the Right Model

### 27.1 If You Need Retrieval at Scale

Use:

- two-tower
- ANN
- hybrid retrieval
- graph/item-to-item

Do not use:

- cross-encoder over entire corpus
- expensive ranker over millions of items

### 27.2 If You Need Strong Tabular Ranking

Use:

- LightGBM LambdaRank
- XGBoost ranking
- CatBoost ranking
- GBDT classifier/regressor

Great for:

- ecommerce search
- enterprise search
- marketplace ranking
- early production ranker

### 27.3 If You Need Personalization at Huge Scale

Use:

- embeddings
- deep retrieval
- sequence models
- multi-task rankers
- feature stores

### 27.4 If You Need Fine Query-Document Relevance

Use:

- BM25/dense retrieval first
- cross-encoder reranker
- LTR model with query-document features

### 27.5 If You Need Multi-Objective Ranking

Use:

- multi-task prediction
- calibrated heads
- explicit utility function
- guardrails
- online experiments

### 27.6 If You Have Little Data

Use:

- rules
- BM25
- popularity
- content-based similarity
- human labels
- pretrained embeddings
- simple GBDT

Avoid overbuilding deep recommenders before you have data.

---

## 28. Cold Start

Cold start appears when:

- new user
- new item
- new query
- new market
- new seller/creator
- new surface

### 28.1 New User

Solutions:

- use query/session context
- use location/device/time
- ask onboarding preferences
- use trending/popular
- use contextual bandits
- quickly adapt from first actions

### 28.2 New Item

Solutions:

- content embeddings
- metadata
- seller/creator reputation
- exploration allocation
- freshness boost
- similar item transfer
- editorial/quality review

### 28.3 New Query

Solutions:

- lexical retrieval
- query embeddings
- spelling/entity understanding
- category prediction
- query rewriting
- semantic matching

---

## 29. Safety, Fairness, and Trust

Ranking systems shape attention and opportunity.

They can affect:

- creators
- sellers
- candidates
- advertisers
- publishers
- users
- communities

Important concerns:

- unfair exposure
- rich-get-richer loops
- demographic bias
- manipulation
- harmful content amplification
- low-quality engagement bait
- opaque decisions
- ad discrimination
- marketplace concentration

Mitigations:

- fairness-aware metrics
- exposure audits
- segment-level evaluation
- policy filters
- calibrated ranking
- exploration for new entrants
- human review for high-stakes domains
- explainability for regulated settings
- protected-attribute handling with legal guidance

For high-stakes ranking, such as jobs, lending, housing, education, healthcare, or public services, ranking is not just an ML problem. It requires legal, ethical, and domain review.

---

## 30. Monitoring

Monitor:

- latency
- timeout rate
- candidate count
- empty results
- feature freshness
- feature missingness
- model score distribution
- calibration
- CTR/CVR
- conversion value
- negative feedback
- diversity
- item exposure concentration
- cold-start exposure
- index freshness
- data drift
- label drift
- segment performance

Important dashboards:

```text
funnel metrics:
  retrieval candidates -> pre-rank candidates -> ranked items -> displayed items -> actions

model metrics:
  score distributions, feature drift, calibration, top features

business metrics:
  conversion, revenue, retention, satisfaction

quality metrics:
  NDCG, relevance labels, complaints, safety issues
```

Alert examples:

- candidate count drops
- ANN recall drops
- feature missingness spikes
- score distribution shifts
- CTR drops after deployment
- latency exceeds budget
- one seller/category dominates exposure
- fresh items receive no impressions

---

## 31. Debugging Ranking Systems

When ranking quality drops, ask:

### 31.1 Candidate Generation

- Did retrieval miss good items?
- Did a source fail?
- Did ANN index become stale?
- Did filters remove too much?
- Did candidate diversity collapse?

### 31.2 Features

- Are features fresh?
- Are online and offline features consistent?
- Are default values increasing?
- Is there leakage in training?
- Did feature distributions drift?

### 31.3 Model

- Did model scores shift?
- Is calibration broken?
- Are certain segments worse?
- Did the model overfit head items?
- Are labels delayed or corrupted?

### 31.4 Reranking

- Are constraints too aggressive?
- Is dedupe removing good items?
- Is diversity hurting relevance?
- Are business rules overriding model scores?

### 31.5 Experimentation

- Is sample ratio correct?
- Are buckets balanced?
- Are metrics delayed?
- Is novelty effect present?
- Are guardrails violated?

---

## 32. Common Pitfalls

| Pitfall | Why It Hurts | Fix |
| --- | --- | --- |
| optimizing clicks only | clickbait and shallow engagement | add satisfaction and negative feedback |
| ignoring position bias | model learns previous rank | debias labels, randomize, use propensities |
| no impression logging | cannot train or evaluate correctly | log exposure, position, candidates, model version |
| random row split | leakage across sessions/time | use time and group splits |
| overusing two-tower for final rank | misses rich interactions | use ranker/reranker after retrieval |
| no calibration | expected value scores wrong | calibrate and monitor |
| no cold-start strategy | new users/items fail | content features and exploration |
| no diversity | repetitive user experience | slate reranking |
| no guardrails | business/user harm | add constraints and monitoring |
| offline-only evaluation | biased conclusions | run A/B tests |
| unbounded business rules | model quality destroyed | measure overrides |
| stale features/index | irrelevant results | freshness SLAs |
| popularity feedback loops | tail suppressed | exploration and exposure audits |
| one metric obsession | local optimization | primary plus guardrails |

---

## 33. Modern Trends and State of the Art

Production SOTA is not one architecture. It is a system.

Modern ranking systems combine:

- hybrid retrieval
- two-tower dense retrieval
- approximate nearest neighbor search
- sequence-aware user modeling
- multi-task deep ranking
- GBDT/LambdaMART where tabular signals dominate
- cross-encoder reranking for high-value surfaces
- calibration
- slate optimization
- exploration/bandits
- counterfactual evaluation
- real-time features
- monitoring and A/B testing

Research directions include:

- generative recommenders
- semantic item IDs
- large sequence models for user behavior
- LLM-enhanced ranking features
- LLM reranking for small candidate sets
- multimodal recommendation
- graph-enhanced retrieval
- causal and counterfactual ranking
- fairness-aware exposure optimization
- reinforcement learning for long-term ranking
- learned slate optimization

Practical reality:

```text
The best production system is often a carefully engineered cascade, not a single giant model.
```

GBDT, two-tower, ANN, and multi-task deep models remain core workhorses.

LLMs are increasingly useful for:

- query understanding
- item/content embeddings
- metadata extraction
- semantic labeling
- reranking small candidate sets
- explanations
- synthetic labels
- cold-start enrichment

But LLMs are usually too expensive to score every candidate in real time.

---

## 34. How to Explain Ranking in Interviews

### "Design a ranking system."

Strong answer:

```text
I would design it as a multi-stage funnel. First, candidate generation retrieves a high-recall pool using sources like BM25, two-tower embeddings, graph candidates, and popularity/freshness. Then a pre-ranker cheaply narrows the pool. The main ranker scores candidates using user, item, query, context, and interaction features. Finally, a reranker enforces diversity, safety, business constraints, and exploration. I would log impressions, positions, candidates, scores, and outcomes, evaluate offline with NDCG/recall/calibration, then validate online with A/B tests and guardrails.
```

### "What is a two-tower model?"

Strong answer:

```text
A two-tower model independently encodes the user or query and the item or document into vectors. The score is usually a dot product or cosine similarity. Because item vectors can be precomputed and stored in an ANN index, the model is scalable for retrieval. Its weakness is limited cross-feature interaction, so it is usually used for candidate generation rather than final ranking.
```

### "Why not use the biggest neural model for everything?"

Strong answer:

```text
At production scale, latency and corpus size make that impossible. A rich cross-encoder or deep ranker may be excellent for 100 candidates, but not for a billion. Ranking systems use cascades: cheap high-recall retrieval first, then increasingly expensive models on smaller candidate sets.
```

### "How do you train a ranking model?"

Strong answer:

```text
I start by defining the ranking objective and logging exposed candidates with positions and outcomes. For retrieval, I train with positives and sampled or in-batch negatives, often using a softmax contrastive loss. For ranking, I can use pointwise CTR/CVR losses, pairwise preferences, or listwise objectives like LambdaMART/NDCG. I split by time, prevent leakage, evaluate by segment, calibrate scores if they drive expected value, and validate online.
```

### "How do you handle bias in clicks?"

Strong answer:

```text
Clicks are biased by exposure and position. I would log positions and propensities, use randomized swaps or exploration data where possible, apply click models or inverse propensity weighting, and evaluate with human labels or randomized traffic slices. I would avoid treating every unclicked item as equally irrelevant.
```

### "What metrics would you use?"

Strong answer:

```text
For retrieval I use recall@k and hit rate. For ranking I use NDCG, MRR, MAP, AUC, and log loss depending on labels. For production, I use online metrics like conversion, revenue, retention, satisfaction, and guardrails like latency, negative feedback, diversity, fairness, and calibration.
```

### "How do you apply ranking to a new product?"

Strong answer:

```text
I start simple: define the objective, instrument logging, build candidate retrieval, create baseline ranking from rules or GBDT, evaluate offline and online, then add personalization, two-tower retrieval, deep rankers, and reranking as data volume and product complexity grow. I would not start with a complex model before data and logging are trustworthy.
```

---

## 35. A Practical Implementation Roadmap

### Phase 1: Instrumentation

Build logging for:

- requests
- candidates
- positions
- scores
- features or feature references
- outcomes
- model versions
- experiment buckets

Without this, do not overinvest in modeling.

### Phase 2: Baseline

Build:

- rule-based filters
- BM25 or metadata retrieval
- popularity fallback
- simple score
- basic dashboards

### Phase 3: First ML Ranker

Build:

- pointwise CTR/CVR model or LambdaMART
- time-based splits
- NDCG/recall metrics
- feature store basics
- online A/B test

### Phase 4: Candidate Generation Upgrade

Build:

- two-tower retrieval
- item embeddings
- ANN index
- hybrid source merging
- retrieval monitoring

### Phase 5: Rich Ranking

Add:

- deep model or stronger GBDT
- sequence features
- multi-task heads
- calibration
- segment-specific evaluation

### Phase 6: Reranking

Add:

- diversity
- freshness
- dedupe
- business constraints
- fairness/exposure audits
- exploration

### Phase 7: Advanced Optimization

Add:

- counterfactual evaluation
- bandits
- long-term value models
- slate models
- LLM-assisted content understanding
- generative/sequential recommenders if justified

---

## 36. Mini Case Study: Ranking Products

Suppose a user searches:

```text
"lightweight running shoes"
```

Stage 1: Retrieval

```text
BM25 retrieves exact text matches.
Dense retrieval retrieves semantically related products.
Personalized two-tower retrieves products matching user's running history.
Popularity source retrieves best sellers.
Freshness source retrieves new arrivals.
```

Stage 2: Filtering

```text
remove out-of-stock
remove blocked sellers
apply size/location constraints
```

Stage 3: Pre-rank

```text
score 5000 candidates cheaply
keep top 500
```

Stage 4: Main rank

Features:

```text
query-title match
query-attribute match
semantic similarity
user-brand affinity
user-price sensitivity
product rating
shipping speed
historical conversion
return rate
seller quality
```

Predictions:

```text
p_click
p_add_to_cart
p_purchase
p_return
expected_margin
```

Score:

```text
score =
    0.5 * p_click
  + 3.0 * p_purchase
  + 0.2 * expected_margin
  - 2.0 * p_return
```

Stage 5: Rerank

```text
dedupe colors/sizes
limit same seller
ensure category relevance
include fresh products
respect sponsored blending
```

Stage 6: Evaluate

Offline:

- NDCG@10
- recall@100
- purchase AUC
- calibration

Online:

- conversion rate
- revenue per search
- add-to-cart
- reformulation rate
- return rate
- latency

---

## 37. Mini Case Study: Ranking a Feed

Candidate sources:

- followed creators
- similar items
- trending
- fresh posts
- collaborative filtering
- two-tower retrieval
- exploration candidates

Ranker predicts:

- p_view
- expected dwell
- p_like
- p_share
- p_follow
- p_hide
- p_report
- long-term value

Score:

```text
score =
    expected_satisfaction
  + short_term_engagement_weight * expected_engagement
  - negative_feedback_weight * p_negative_feedback
  + freshness_bonus
  + exploration_bonus
```

Reranker:

- creator caps
- topic diversity
- freshness
- avoid repetition
- safety filters
- ad insertion

Metrics:

- retention
- session satisfaction
- hide/report rate
- diversity
- creator exposure
- long-term user value

---

## 38. Mini Case Study: Ranking Ads

Candidate ads are selected by targeting and eligibility.

Ranker estimates:

```text
pCTR
pCVR
pConversionValue
pNegativeFeedback
quality
```

Auction score:

```text
score = bid * pCTR * quality
```

For conversion campaigns:

```text
score = bid * pConversion * quality
```

Constraints:

- budget
- pacing
- frequency cap
- advertiser quality
- policy
- user fatigue

Monitoring:

- calibration by advertiser
- calibration by placement
- advertiser ROI
- platform revenue
- user negative feedback
- auction stability

---

## 39. Summary Mental Model

The simplest mental model:

```text
Retrieval finds plausible items.
Ranking orders them by predicted utility.
Reranking turns item scores into a good slate.
Logging creates the data for the next model.
Evaluation prevents the model from optimizing the wrong thing.
```

A strong ranking system has:

- complete exposure logging
- high-recall candidate generation
- a strong ranker
- calibrated scores
- debiased evaluation
- online experiments
- reranking constraints
- exploration
- monitoring
- fallbacks

---

## 40. Quick Glossary

| Term | Meaning |
| --- | --- |
| retrieval | finding candidate items from a large corpus |
| candidate generation | same as retrieval, often multi-source |
| two-tower | dual encoder that embeds user/query and item separately |
| ANN | approximate nearest neighbor search |
| pre-rank | cheap model that narrows candidates |
| ranker | model that scores candidates |
| reranker | adjusts final slate using constraints/context |
| slate | final ordered list shown |
| CTR | click-through rate |
| CVR | conversion rate |
| pCTR | predicted click probability |
| pCVR | predicted conversion probability |
| LTR | learning to rank |
| LambdaMART | tree-based listwise/pairwise ranking method |
| NDCG | normalized discounted cumulative gain |
| MRR | mean reciprocal rank |
| MAP | mean average precision |
| IPW | inverse propensity weighting |
| calibration | predicted probabilities match observed rates |
| exploration | showing uncertain items to learn |
| position bias | higher ranks get more attention |
| cold start | lack of history for user/item/query |
| cross-encoder | jointly encodes query and item for relevance |
| multi-task model | predicts several outcomes at once |
| slate optimization | optimizing final list, not independent items |

---

## 41. References

- YouTube recommendations: [Deep Neural Networks for YouTube Recommendations](https://research.google/pubs/deep-neural-networks-for-youtube-recommendations/)
- Wide & Deep: [Wide & Deep Learning for Recommender Systems](https://arxiv.org/abs/1606.07792)
- DLRM: [Deep Learning Recommendation Model for Personalization and Recommendation Systems](https://arxiv.org/abs/1906.00091)
- DCN V2: [DCN V2: Improved Deep & Cross Network and Practical Lessons for Web-scale Learning to Rank Systems](https://arxiv.org/abs/2008.13535)
- TensorFlow Recommenders: [Basic retrieval with TFRS](https://www.tensorflow.org/recommenders/examples/basic_retrieval)
- TensorFlow Ranking: [TensorFlow Ranking](https://www.tensorflow.org/ranking)
- Learning to rank overview: [From RankNet to LambdaRank to LambdaMART](https://www.microsoft.com/en-us/research/publication/from-ranknet-to-lambdarank-to-lambdamart-an-overview/)
- XGBoost ranking: [Learning to Rank](https://xgboost.readthedocs.io/en/stable/tutorials/learning_to_rank.html)
- LightGBM LambdaRank: [Parameters: lambdarank](https://lightgbm.readthedocs.io/en/stable/Parameters.html)
- FAISS: [FAISS documentation](https://faiss.ai/)
- ScaNN: [ScaNN: Efficient Vector Similarity Search](https://research.google/blog/announcing-scann-efficient-vector-similarity-search/)
- HNSW: [Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs](https://arxiv.org/abs/1603.09320)
- Vespa phased ranking: [Phased ranking](https://docs.vespa.ai/en/phased-ranking.html)
- MIND: [Multi-Interest Network with Dynamic Routing for Recommendation at Tmall](https://arxiv.org/abs/1904.08030)
- SASRec: [Self-Attentive Sequential Recommendation](https://arxiv.org/abs/1808.09781)
- BERT4Rec: [Sequential Recommendation with Bidirectional Encoder Representations from Transformer](https://arxiv.org/abs/1904.06690)
- DIN: [Deep Interest Network for Click-Through Rate Prediction](https://arxiv.org/abs/1706.06978)
- ESMM: [Entire Space Multi-Task Model](https://arxiv.org/abs/1804.07931)
- Counterfactual LTR: [Unbiased Learning-to-Rank with Biased Feedback](https://arxiv.org/abs/1608.04468)
- Recommender calibration: [Calibrated Recommendations](https://dl.acm.org/doi/10.1145/3240323.3240372)
- Generative recommendations: [Actions Speak Louder than Words: Trillion-Parameter Sequential Transducers for Generative Recommendations](https://arxiv.org/abs/2402.17152)

