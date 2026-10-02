# 25. Knowledge graphs: what they are, how to build them, and how they work with LLMs

> **What you need to be able to say:** what a knowledge graph is (and is not), the two data models (RDF/triples with ontologies vs labeled property graphs), the query languages, how entities get resolved, how LLMs build and use graphs (GraphRAG, text-to-Cypher, graph memory), and when a graph beats a vector store. Go deeper: Part 6 → *Knowledge graphs complete guide* (47 KB) and the two Neo4j GraphRAG demos with code.

## 25.1 Definitions

A **knowledge graph (KG)** represents knowledge as entities (nodes) and typed relationships (edges), with properties on both, usually under a schema (an **ontology**) that defines the allowed types and relationships. `(:Product {name:"Fund A"})-[:REQUIRES]->(:Disclosure {id:"D-17"})-[:MANDATED_BY]->(:Regulation {name:"SEC Rule 482"})` is a tiny graph. The value is explicit, traversable relationships: multi-hop questions ("which marketing assets mention products governed by rule X?") become path queries instead of fuzzy similarity.

Two data models dominate:

| | RDF / semantic web | Labeled property graph (LPG) |
|---|---|---|
| Unit | triple: subject–predicate–object, global IRIs | nodes and edges with labels and key–value properties |
| Schema | ontologies in RDFS/OWL; formal semantics, inference | optional constraints; schema by convention |
| Query | SPARQL | Cypher (Neo4j, Memgraph, FalkorDB), GQL (ISO/IEC 39075:2024, the first new ISO database language since SQL, largely derived from Cypher), Gremlin (TinkerPop; Neptune, JanusGraph) |
| Stores | GraphDB, Stardog, Virtuoso, Blazegraph, Neptune (RDF mode), Oxigraph | Neo4j, Neptune (openCypher; Neptune Analytics for in-memory graph algorithms and vector similarity), Memgraph, TigerGraph (GSQL), ArangoDB, FalkorDB, Kùzu (embedded; its company was acquired by Apple in October 2025 and the repository archived, with community forks such as RyuGraph continuing it — check maintenance before adopting) |
| Strengths | standards, interoperability, reasoning, linked open data (Wikidata, DBpedia), SHACL validation | developer ergonomics, performance for traversals, analytics (GDS algorithms) |
| Typical users | life sciences, government, publishers, enterprise taxonomies | fraud, recommendations, IT ops, master data, GraphRAG |

## 25.2 Building one

1. **Ontology / schema first**, even a small one: entity types, relationship types, key properties, identifiers. Reuse standards where they exist (schema.org, FIBO for finance, SNOMED/UMLS for health, Dublin Core).
2. **Structured sources**: map tables and APIs to nodes and edges (ETL with Spark, dbt, Neo4j's importer, Neptune bulk loader).
3. **Unstructured sources**: LLM extraction of entities and relations with a constrained schema (structured outputs), confidence scores and provenance (which document, which sentence). Classic NLP (spaCy NER, relation classifiers) still works for narrow, high-volume cases.
4. **Entity resolution**: merge "IBM", "International Business Machines" and "I.B.M." — blocking, similarity (names, attributes, embeddings), rules, and a human review queue for ambiguous merges; keep the merge decisions as data. The scaling reason for blocking: 1 million entities is ~5 × 10¹¹ candidate pairs; blocking on cheap keys (normalized name prefix, postcode, tax id, embedding nearest neighbours) cuts that to a few million comparisons, which a matcher (rules, a gradient-boosted classifier on similarity features, or an LLM for the ambiguous residue) can then score. Measure precision and recall of merges on a labelled sample: a false merge (two suppliers fused into one) is usually far more damaging than a missed one, so set thresholds for high precision and let the review queue absorb the middle band.
5. **Validation**: SHACL/constraints, cardinality checks, orphan detection; a graph with wrong edges is worse than no graph.
6. **Serving**: a graph database for traversal; often alongside a vector index on node descriptions (hybrid), and precomputed community summaries for GraphRAG.
7. **Maintenance**: incremental updates with provenance, versioning (time-aware edges `valid_from`/`valid_to`), and the same eval discipline as RAG.

## 25.3 Query languages in two minutes each

**Cypher** (Neo4j and friends; GQL standardizes it):

```cypher
MATCH (a:Asset)-[:MENTIONS]->(p:Product)-[:REQUIRES]->(d:Disclosure)
WHERE p.name = $product AND NOT EXISTS { (a)-[:CONTAINS]->(d) }
RETURN a.id AS asset, collect(d.id) AS missing_disclosures
```

(`NOT EXISTS { … }` is the current, GQL-aligned form; the older bare pattern predicate `NOT (a)-[:CONTAINS]->(d)` still runs on Neo4j 5 but is the style to move away from.)

**SPARQL** (RDF):

```sparql
PREFIX ex: <http://example.org/>
SELECT ?asset (GROUP_CONCAT(STR(?d); separator=", ") AS ?missing) WHERE {
  ?asset ex:mentions ?product . ?product ex:requires ?d .
  FILTER NOT EXISTS { ?asset ex:contains ?d }
} GROUP BY ?asset
```

(`STR()` because `GROUP_CONCAT` is defined over strings and `?d` is an IRI; some engines coerce silently, others error.)

**Gremlin** (traversal style, Neptune/JanusGraph):

```groovy
g.V().has('Product', 'name', product).as('p').
  in('MENTIONS').hasLabel('Asset').as('a').
  select('p').out('REQUIRES').as('d').
  not(__.in('CONTAINS').where(eq('a'))).
  group().by(select('a').values('id')).by(select('d').values('id').fold())
```

(Editor's note: an earlier draft used `.where(__.out('MENTIONS').out('REQUIRES').not(__.in('CONTAINS')))`, which tests whether *any* asset contains the disclosure rather than *this* asset — the classic Gremlin mistake of losing the reference to the starting vertex. Labelling the asset with `as('a')` and comparing with `where(eq('a'))` keeps the correlation that Cypher's and SPARQL's variables give you for free. Imperative traversals make this class of bug easy, which is one reason generated Gremlin needs a gold test set.)

Chapter 33 covers these alongside SQL and the rest.

## 25.4 Knowledge graphs and LLMs

- **Graph-grounded RAG (GraphRAG).** Microsoft's GraphRAG extracts an entity graph from documents, detects communities (Leiden), writes hierarchical community summaries, and answers *global* questions by map-reduce over summaries and *local* questions by pulling an entity's neighborhood plus linked text chunks; DRIFT search combines the two. Lighter variants (LightRAG, Neo4j's GraphRAG package, LlamaIndex PropertyGraphIndex) combine vector search on node/chunk embeddings with one- or two-hop expansion. Use when questions are relational, aggregate or multi-hop; expect 5–20× the indexing cost of plain RAG for full LLM extraction and summarization (every chunk passes through an extraction prompt, and community summaries are regenerated when the graph changes), and plan the refresh strategy. **LazyGraphRAG** (Microsoft Research, November 2024) is the cost answer: it builds the concept graph with cheap NLP noun-phrase extraction and defers LLM summarization to query time, reporting indexing cost equal to vector RAG and 0.1% of full GraphRAG, with comparable quality on global questions at a fraction of the query cost.
- **Text-to-Cypher / text-to-SPARQL.** The model writes a query against a schema you supply (with examples and allowed labels), the query runs, and the model explains results; validate queries (read-only, limits, timeouts), and evaluate on a gold set of question–query pairs. This is how "agentic GraphRAG" demos work: the agent chooses between vector search, graph query and both.
- **Graph as agent memory.** Temporal knowledge graphs (Zep/Graphiti, custom) store facts about users and entities with validity intervals, so an agent can answer "what changed since last month" and avoid contradictions.
- **Graph for governance and rules.** Product → rule → required-disclosure graphs; data lineage graphs; organizational graphs for permissions — deterministic lookups that an LLM should never guess.
- **LLM for graph construction.** Extraction, schema suggestion, entity resolution assistance, and community summarization — with provenance and human review.

### Critic's additions: making generated graph queries reliable

Text-to-Cypher fails in predictable ways: wrong relationship direction, a label or property that does not exist, a missing `DISTINCT` that multiplies rows through a fan-out, an unbounded variable-length path that times out, and — the dangerous one — a syntactically valid query that answers a different question. The controls, in the order they pay off:

1. **Schema pruning.** Give the model only the labels, relationship types, directions and properties relevant to the question (retrieve them by embedding the schema elements), with one-line descriptions and example values; a 300-label schema in full degrades accuracy.
2. **Few-shot by retrieval.** Keep a library of verified question–query pairs and retrieve the three most similar as examples; this does more than any prompt wording.
3. **Static validation before execution.** Parse the query, check every label, type and property against the schema, run `EXPLAIN` to catch syntax errors and estimate cost, reject write clauses (`CREATE`, `MERGE`, `DELETE`, `SET`) at the role level, and inject `LIMIT` and a timeout.
4. **Self-repair loop, bounded.** On an error, return the database message to the model and allow one or two retries; more rarely helps.
5. **Result sanity checks.** Empty results, a row explosion or an implausible aggregate trigger a clarification or a fallback to vector search rather than a confident answer.
6. **Evaluation by execution.** Score generated queries by comparing *result sets* with the gold query's results on a fixed snapshot, not by string match; track the error classes above separately.

The same controls apply to SPARQL and Gremlin; Gremlin's imperative style needs more examples, because the correlation errors shown in 25.3 are easy to generate and hard to spot.

## 25.5 When a graph beats a vector store (and when it does not)

| Question shape | Vector RAG | Knowledge graph |
|---|---|---|
| "What does the policy say about X?" (lookup) | ✔ | — |
| "Which assets mention products governed by rule X and lack disclosure Y?" (multi-hop, set logic) | ✗ | ✔ |
| "What are the main themes across 10,000 tickets?" (global) | ✗ (sampling) | ✔ via community summaries |
| "Who is connected to whom through what?" (relationships) | ✗ | ✔ |
| "Explain this figure" (unstructured, ambiguous) | ✔ | — |
| Fresh facts changing daily | easy to upsert | needs incremental pipelines |
| Explainability and audit | citations to chunks | explicit paths — stronger |
| Cost to build | low | medium–high (extraction, resolution, maintenance) |

Most mature systems are hybrid: vectors for text, a graph for the relationships and rules that must be exact.

Two corrections to the table that an interviewer may probe. First, "global" questions do not strictly need a graph: clustering the embeddings (k-means or HDBSCAN) and map-reduce summarizing each cluster, or a batch pass of a cheap model that writes each ticket's topic, product and sentiment into a table you then query with SQL, answers "what are the main themes" at a fraction of GraphRAG's build cost — reach for the graph when the *relationships between* entities are the question. Second, multi-hop questions over a handful of hops can often be answered by an agent doing iterative retrieval; the graph wins when the hops must be exact, complete (set logic such as "all assets lacking a disclosure") and auditable.

## 25.6 Scenarios

- **Marketing compliance (resume use case).** A graph of products, share classes, regulations, required disclosures and approved claims, built from structured sources plus LLM extraction from regulatory documents with provenance; reviewer agents query it (Cypher) to check each asset and cite rule ids; a conflict-detection step finds contradictory requirements; humans resolve them and the resolutions become edges.
- **Supplier risk.** Companies, subsidiaries, sanctions lists, locations and events; questions like "which tier-2 suppliers sit in a sanctioned region" are two-hop traversals; GraphRAG summarizes news per community; entity resolution is the hard part.
- **Customer 360 for support agents.** Accounts, contracts, tickets, products and people as a graph; the support agent's "what is this customer's situation" tool is a one-hop neighborhood query, not twenty API calls.
- **IT operations.** Services, dependencies, deployments, incidents; blast-radius questions are path queries; an SRE agent uses the graph to reason about root causes.
- **Life sciences.** Drug–target–disease graphs on public ontologies plus internal data; SPARQL over RDF for standards compliance; LLMs for literature extraction with curation.

**Interview line:** *"A knowledge graph is for questions about relationships and sets, where exactness and explainability matter: build a small ontology, load structured data directly, extract from text with provenance and human-reviewed entity resolution, and let the agent query it with generated Cypher next to vector search over the text. Vectors answer 'what does it say', the graph answers 'how is it connected'."*
