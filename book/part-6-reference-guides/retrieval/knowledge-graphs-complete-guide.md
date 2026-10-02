# Knowledge Graphs — A Complete Guide

> A practical, end-to-end guide to knowledge graphs: what they are, how they work, how to build and query them, how they intersect with LLMs (GraphRAG), and how to decide when to use one. Written with AI engineering interview prep in mind, but useful as a working reference.

---

## Table of Contents

1. [What a Knowledge Graph Actually Is](#1-what-a-knowledge-graph-actually-is)
2. [Why They Exist — The Problem They Solve](#2-why-they-exist--the-problem-they-solve)
3. [Core Concepts and Vocabulary](#3-core-concepts-and-vocabulary)
4. [The Two Big Schools — RDF vs Property Graphs](#4-the-two-big-schools--rdf-vs-property-graphs)
5. [Query Languages — SPARQL, Cypher, Gremlin](#5-query-languages--sparql-cypher-gremlin)
6. [Ontologies, Schemas, and Reasoning](#6-ontologies-schemas-and-reasoning)
7. [How Knowledge Graphs Are Built](#7-how-knowledge-graphs-are-built)
8. [Storage — The Database Landscape](#8-storage--the-database-landscape)
9. [GraphRAG — The Modern Intersection with LLMs](#9-graphrag--the-modern-intersection-with-llms)
10. [Real-World Applications](#10-real-world-applications)
11. [Production Considerations](#11-production-considerations)
12. [When to Use a KG vs Alternatives](#12-when-to-use-a-kg-vs-alternatives)
13. [Anti-Patterns](#13-anti-patterns)
14. [Practical Workflow — Building One End to End](#14-practical-workflow--building-one-end-to-end)
15. [Interview-Ready Talking Points](#15-interview-ready-talking-points)

---

## 1. What a Knowledge Graph Actually Is

A **knowledge graph (KG)** is a structured representation of real-world information as a network of **entities** (nodes) and the **relationships** (edges) between them, typically enriched with **semantic context** — meaning the entities and relationships have well-defined types and properties.

A toy example:

```
(Marie Curie) —[born_in]→ (Warsaw)
(Warsaw) —[capital_of]→ (Poland)
(Marie Curie) —[won]→ (Nobel Prize in Physics, 1903)
(Marie Curie) —[won]→ (Nobel Prize in Chemistry, 1911)
(Marie Curie) —[married_to]→ (Pierre Curie)
```

Five facts, but the structure means you can answer questions text alone couldn't:
- *"Which Nobel laureates were born in countries that no longer exist as they were?"*
- *"Who married another Nobel laureate?"*
- *"What's the shortest connection between Marie Curie and quantum mechanics?"*

These are **multi-hop reasoning** questions — they require following relationships through multiple steps. That's what KGs are fundamentally for.

### 1.1 The Three Essentials

A knowledge graph has three things that distinguish it from "a database of stuff":

1. **Entities are first-class** — they have identity beyond a row in a table. The same entity referenced from ten data sources resolves to one node.
2. **Relationships are first-class** — they have types, directions, and can themselves carry properties. They aren't joins; they're data.
3. **Semantics matter** — `:born_in` and `:lived_in` are different relationship types with different meanings. A KG enforces (or at least documents) that distinction.

### 1.2 Brief History

- **1960s–70s**: semantic networks in AI research (Quillian, Schank)
- **1980s–90s**: expert systems, frame-based knowledge representation
- **2001**: Tim Berners-Lee proposes the Semantic Web → RDF, RDFS, OWL standards
- **2007**: DBpedia and Freebase launch — first large public KGs
- **2012**: Google announces "Knowledge Graph" as a product. Coins the modern term.
- **2014**: Google buys Freebase, eventually shuts it down. Wikidata takes over.
- **2024**: Microsoft publishes GraphRAG paper — KGs become a major component of LLM retrieval stacks
- **2025–26**: Explosion of GraphRAG variants (LightRAG, HippoRAG, FastGraphRAG); LLM-driven KG construction becomes mainstream

---

## 2. Why They Exist — The Problem They Solve

Three things relational databases, document stores, and vector stores each handle poorly that KGs handle well.

### 2.1 Multi-Hop Queries

In SQL, a 5-table join with conditions across each is painful to write and slow to execute. In a KG:

```cypher
MATCH (p:Person)-[:WORKS_AT]->(:Company)-[:LOCATED_IN]->(:City)-[:IN_COUNTRY]->(c:Country)
WHERE c.name = 'Germany' AND p.role = 'CEO'
RETURN p.name
```

Three hops, one line, executes in milliseconds even on large graphs because the database is built around traversal.

### 2.2 Heterogeneous Schemas

Real-world entities have wildly different attributes. A person has a birthday; a company has an industry; a drug has a chemical formula. Forcing them all into one relational schema gives you sparse tables and nullable columns everywhere. KGs let each entity carry only the properties it needs.

### 2.3 Implicit Knowledge

A KG can store *facts* that imply *more facts*. If `Marie Curie :born_in Warsaw` and `Warsaw :in_country Poland`, a KG reasoner can infer `Marie Curie :born_in_country Poland` without anyone writing that fact. Relational databases don't reason; KGs (with the right tooling) do.

### 2.4 The LLM Connection

LLMs hallucinate confident facts. Vector databases retrieve text chunks that may or may not contain the answer. A KG provides **structured, verifiable knowledge** that an LLM can ground its answers in — and you can cite the specific triple that supported a claim. That's why GraphRAG is having a moment.

---

## 3. Core Concepts and Vocabulary

The terminology trips people up because two communities (Semantic Web / RDF and Property Graph / Neo4j) use different words for similar concepts.

### 3.1 The Triple

The atomic unit of a knowledge graph in the RDF tradition: **subject — predicate — object**.

```
<Marie Curie> <born_in> <Warsaw>
```

Equivalent in property-graph language: **node — relationship — node**.

### 3.2 Entity (Node)

A thing in the world. Has an identifier (URI in RDF, internal ID in property graphs), a type (also called a class or label), and properties.

### 3.3 Relationship (Edge, Predicate)

A typed, directed connection between entities. In RDF, relationships have URIs too (e.g. `dbo:birthPlace`). In property graphs, they have type names like `BORN_IN`.

### 3.4 Property

A key-value attribute on an entity or relationship. `name`, `birthDate`, `population`. In RDF, properties are also expressed as triples with literal values as objects.

### 3.5 Ontology / Schema

A formal specification of the types of entities and relationships your graph allows, their hierarchies, and constraints. Example: "A `Person` can have a `:born_in` relationship to a `Place`, but not to another `Person`."

### 3.6 Class Hierarchy

Entities can have type hierarchies: a `Scientist` is a `Person`, a `Person` is an `Agent`. Queries against a parent class match all subclasses.

### 3.7 Reification

Saying things about statements themselves. "Marie Curie was born in Warsaw" is a fact; "according to Wikipedia, Marie Curie was born in Warsaw" reifies that fact with provenance. RDF has formal mechanisms for this; property graphs handle it by promoting relationships to nodes.

### 3.8 SPARQL Endpoint

A queryable HTTP endpoint that accepts SPARQL queries and returns results. Wikidata's endpoint (`query.wikidata.org`) is one of the most-used in the world.

### 3.9 Federation

Querying across multiple KGs as if they were one. SPARQL has explicit federation support (`SERVICE` keyword); property graphs typically don't.

---

## 4. The Two Big Schools — RDF vs Property Graphs

The single most confusing thing about KGs for newcomers is that there are two parallel ecosystems with different vocabulary, different query languages, and different strengths.

### 4.1 RDF (Resource Description Framework)

**Origin**: W3C Semantic Web stack. Designed for *the* knowledge graph of all human knowledge (the original Web vision).

**Data model**: triples. Everything — entities, types, relationships, properties — is a URI or a literal.

**Strengths**:
- Standards-based, vendor-neutral
- Formal semantics: you can write OWL ontologies and reason about them
- Built-in federation: you can query across KGs from different organizations
- Excellent for *interoperability* and *open data*
- The model behind Wikidata, DBpedia, schema.org, biomedical ontologies (UMLS, GO, Mondo)

**Weaknesses**:
- Verbose (every property is a triple with a URI)
- Performance at scale historically weaker than property graphs
- Less ergonomic for engineers used to "objects with properties"
- Tooling lags property graphs for developer experience

**Query language**: SPARQL

### 4.2 Labeled Property Graphs (LPG)

**Origin**: Neo4j (2007). Pragmatic engineering response to "RDF is too verbose for application development."

**Data model**: nodes with labels and properties; relationships with types and properties. No URIs required; identity is internal.

**Strengths**:
- Properties on relationships are first-class (RDF requires reification for this)
- Cypher is much easier to read than SPARQL
- Better tooling and developer experience
- Generally faster on operational workloads
- Native to most enterprise graph use cases (fraud detection, recommendations, supply chain)

**Weaknesses**:
- No standards-based semantics or reasoning
- Weaker federation
- Less suited to publish-and-share use cases

**Query language**: Cypher (Neo4j), Gremlin (TinkerPop), GSQL (TigerGraph), now openCypher as an emerging standard.

### 4.3 Which Should You Use?

| If you're doing... | Use |
|---|---|
| Internal enterprise app (fraud, recommendations, customer 360) | Property graph (Neo4j, Neptune LPG mode, FalkorDB, ArangoDB) |
| Biomedical, scientific, regulatory data | RDF — you'll want to integrate with existing ontologies |
| Public data publishing / open data | RDF |
| GraphRAG for LLMs | Either — most modern GraphRAG frameworks are LPG-first |
| Cross-organization data integration | RDF + SPARQL federation |
| You just need to ship something fast | Property graph |

In practice, **80%+ of new KG projects in 2026 use property graphs** unless they specifically need RDF's semantics or have to integrate with existing semantic data.

---

## 5. Query Languages — SPARQL, Cypher, Gremlin

### 5.1 SPARQL (for RDF)

SPARQL is SQL-like and pattern-based. You specify a triple pattern with variables, and SPARQL finds all bindings.

**Example**: Find all Nobel laureates born in cities that are capitals.

```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>

SELECT ?laureate ?city
WHERE {
  ?laureate dbo:award dbr:Nobel_Prize_in_Physics .
  ?laureate dbo:birthPlace ?city .
  ?city a dbo:Capital .
}
LIMIT 100
```

The verbosity comes from URIs and explicit prefixing. SPARQL is powerful but unfriendly to people who aren't already comfortable with it.

### 5.2 Cypher (for Neo4j and openCypher-compatible engines)

Cypher uses ASCII-art pattern matching that reads more naturally.

**Same query in Cypher**:

```cypher
MATCH (laureate:Person)-[:WON]->(:Award {name: 'Nobel Prize in Physics'}),
      (laureate)-[:BORN_IN]->(city:City {is_capital: true})
RETURN laureate.name, city.name
LIMIT 100
```

Cypher's pattern syntax — `()` for nodes, `-[]-` for relationships, `-[]->` for directed relationships — is the killer feature. You're literally drawing the pattern you want.

**More Cypher patterns to know**:

```cypher
// Create a node
CREATE (m:Person {name: 'Marie Curie', born: 1867})

// Create a relationship
MATCH (m:Person {name: 'Marie Curie'}), (w:City {name: 'Warsaw'})
CREATE (m)-[:BORN_IN]->(w)

// Variable-length paths (multi-hop)
MATCH path = (a:Person {name: 'Alice'})-[:KNOWS*1..3]-(b:Person)
RETURN b.name, length(path)

// Aggregation
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
RETURN c.name, count(p) AS employee_count
ORDER BY employee_count DESC

// Shortest path
MATCH path = shortestPath(
  (a:Person {name: 'Marie Curie'})-[*]-(b:Person {name: 'Einstein'})
)
RETURN path
```

### 5.3 Gremlin (for TinkerPop / Neptune)

Gremlin is a functional, traversal-based language. Less declarative than SPARQL or Cypher, more procedural.

```groovy
g.V().has('Person', 'name', 'Marie Curie')
  .out('WON').has('name', 'Nobel Prize in Physics')
  .V().has('Person', 'name', 'Marie Curie')
  .out('BORN_IN').has('is_capital', true)
  .values('name')
```

Gremlin's strength is that you describe the *traversal*, step by step, which gives you very precise control over performance. Its weakness is that it's harder to read for complex patterns.

### 5.4 GSQL (TigerGraph)

A SQL-like graph language. TigerGraph's pitch is that you can write GSQL like SQL but it executes like graph traversal.

```sql
SELECT p
FROM Person:p-(WON>:w)-Award:a
WHERE a.name = "Nobel Prize in Physics"
```

### 5.5 Which Query Language to Learn?

If you're learning one: **Cypher**. It's the most intuitive, the most widely used in property-graph databases, and there's an emerging openCypher standard supported by Neo4j, Memgraph, FalkorDB, Neptune, and others. Time-to-productivity is the lowest of the four.

If you need to work with scientific or regulatory data: also learn enough SPARQL to read existing queries.

---

## 6. Ontologies, Schemas, and Reasoning

### 6.1 What an Ontology Is

An **ontology** is a formal specification of what types of entities and relationships exist in your domain, and what rules govern them. It's the "schema" of a knowledge graph, but typically more expressive than a relational schema.

A minimal ontology might say:
- `Person` is a class
- `City` is a class
- `:born_in` is a property whose domain is `Person` and whose range is `City`
- Every `Person` has exactly one `:born_in` value
- A `Scientist` is a subclass of `Person`

### 6.2 RDFS and OWL

In the RDF world, ontologies are written in **RDFS** (RDF Schema — simple) or **OWL** (Web Ontology Language — much more expressive). OWL supports:

- Class hierarchies (`Scientist ⊑ Person`)
- Property hierarchies (`:authored_by ⊑ :related_to`)
- Cardinality constraints (`a Person has exactly one birth_date`)
- Disjointness (`Person and Place are disjoint classes`)
- Inverse properties (`:parent_of` is the inverse of `:child_of`)
- Transitivity (`:ancestor_of` is transitive)
- Symmetry (`:married_to` is symmetric)

### 6.3 Reasoning

Given an OWL ontology and a set of facts, a **reasoner** can derive new facts.

```
Facts:
  Marie Curie :born_in Warsaw
  Warsaw :located_in Poland

Ontology:
  :born_in_country ⊑ chain(:born_in, :located_in)

Derived:
  Marie Curie :born_in_country Poland   ← inferred
```

This is genuinely useful in domains where the ontology is rich and stable (biomedical, legal). It's less useful in fast-moving domains where the ontology can't keep up.

### 6.4 Schema in Property Graphs

Property graphs traditionally take a schema-light or schema-optional approach. You don't have to declare types upfront; you just create nodes and relationships, and the labels emerge.

Modern property graph databases (Neo4j, Memgraph) now support **schema constraints**:

```cypher
// Ensure unique node IDs
CREATE CONSTRAINT person_id_unique FOR (p:Person) REQUIRE p.id IS UNIQUE

// Require property presence
CREATE CONSTRAINT person_name_exists FOR (p:Person) REQUIRE p.name IS NOT NULL
```

And **type checking** for properties. But there's no equivalent to OWL-level reasoning out of the box.

### 6.5 Pragmatic Take

For most engineering applications, you don't need OWL reasoning. You need:
1. A documented vocabulary of entity types and relationship types
2. Constraints that prevent obvious data errors (unique IDs, required properties)
3. A pattern for what *should* and *shouldn't* be modeled as a node vs a property

If you're in a regulated domain (biomedical, legal, compliance), OWL might genuinely earn its complexity. Otherwise, treat ontology as documentation.

---

## 7. How Knowledge Graphs Are Built

The biggest cost in a KG project is almost never the database — it's the construction.

### 7.1 The Pipeline

```
Data sources → Extraction → Normalization → Entity resolution
   → Schema mapping → Triple generation → Loading → Validation → Maintenance
```

### 7.2 Data Sources

**Structured**: relational databases, CSVs, JSON APIs. Easiest to ingest because the schema is known.

**Semi-structured**: XML, JSON with variable schemas, wikis, knowledge bases. Need parsing logic per source.

**Unstructured**: documents, web pages, emails, transcripts. The hardest and most interesting case — requires NLP to extract entities and relationships.

### 7.3 Entity Extraction (Named Entity Recognition)

The first NLP step: identify the entities mentioned in text.

**Traditional approach**: spaCy, Stanford NER, or fine-tuned BERT models with labels like `PERSON`, `ORG`, `LOCATION`, `DATE`.

**Modern (2024+) approach**: prompt an LLM with the document and a schema. The LLM returns structured JSON:

```python
prompt = f"""
Extract entities from the following text. Return as JSON with this schema:
{{
  "entities": [
    {{"id": "e1", "type": "Person|Company|Location|Drug", "text": "..."}}
  ]
}}

Text: {document}
"""
```

LLM-based extraction is wildly more flexible — it handles domain-specific entity types without retraining — but costs more per document and is less deterministic.

### 7.4 Relation Extraction

Given two entities in a sentence, what's the relationship between them?

```
"Marie Curie was born in Warsaw in 1867"
  → (Marie Curie, born_in, Warsaw)
  → (Marie Curie, born_on, 1867)
```

**Traditional approach**: dependency parsing + rule patterns, or supervised classification with labeled training data.

**Modern approach**: LLMs again. Give the LLM the text and a schema of relationship types you care about, get triples back.

**Hybrid approach** (often the best): dependency parsing for "obvious" syntactic relations (subject-verb-object), LLM for harder cases. This is the approach taken by recent "practical GraphRAG" papers — they use dependency parsing to achieve 94% of LLM-based extraction performance at significantly lower cost.

### 7.5 Entity Resolution (Entity Linking)

The hardest problem in KG construction. "Marie Curie", "Madame Curie", "Maria Skłodowska-Curie", and "M. Curie" all refer to the same person. The KG needs one node, not four.

Strategies:
- **Exact + alias matching**: maintain a table of known aliases
- **String similarity**: Levenshtein, Jaro-Winkler, token-set ratios
- **Embedding similarity**: encode entity mentions with a sentence embedding model, link if cosine similarity > threshold
- **Linking to a reference KG**: if Wikidata has an entry for "Marie Curie" (Q7186), link your mention to that QID. Suddenly your KG can federate with Wikidata.
- **LLM-based disambiguation**: give the LLM the mention plus surrounding context plus candidate entities, ask which one matches

Real production pipelines combine all of these.

### 7.6 Schema Mapping

You've extracted entities and relations. They need to fit your KG's schema (or extend it).

- Map extracted entity types to your ontology classes
- Map relation strings to canonical relation types (`"was born in"` → `:born_in`)
- Handle synonyms and abbreviations

### 7.7 Quality and Validation

Before loading: check for obvious errors (a person born in another person, a company located in a year). After loading: spot-check against known facts.

For production KGs, build **assertion tests**:

```python
def test_marie_curie_facts(graph):
    result = graph.query("MATCH (p:Person {name: 'Marie Curie'})-[:WON]->(a:Award) RETURN count(a) as c")
    assert result['c'] == 2  # she won two Nobel Prizes
```

### 7.8 The Modern LLM-Driven Pipeline

Microsoft's GraphRAG popularized a fully LLM-driven construction pipeline:

```
For each text chunk:
  1. LLM extracts entities (with types and descriptions)
  2. LLM extracts relationships (with types and descriptions)
  3. Deduplicate and merge entities across chunks
  4. (Optional) LLM generates community summaries via graph clustering
```

It's powerful but expensive — extracting a KG from a million-document corpus this way can cost tens of thousands of dollars in LLM tokens. The cost-efficient alternative is the hybrid approach: dependency parsing for the cheap cases, LLM for the hard ones.

---

## 8. Storage — The Database Landscape

### 8.1 The Major Property Graph Databases

| Database | Style | Strengths | Weaknesses | Sweet spot |
|---|---|---|---|---|
| **Neo4j** | Native property graph | Mature ecosystem (APOC, GDS, Bloom), Cypher's gold standard, large community | Write scaling limited to single writer, Enterprise edition expensive | Default choice for property-graph KGs |
| **Amazon Neptune** | Managed property graph + RDF | AWS-native, supports both LPG and RDF, multi-AZ | Network overhead (cloud-hosted only), single writer for writes, eventual-consistency replicas | AWS-native shops, need RDF + LPG in one service |
| **TigerGraph** | Distributed parallel | Massively scalable, real-time analytics on trillions of edges, GSQL is SQL-like | Higher complexity, smaller community, commercial | Massive-scale enterprise analytics |
| **Memgraph** | In-memory property graph | Microsecond-latency queries, openCypher-compatible | Memory cost at scale | Real-time / streaming graph workloads |
| **FalkorDB** | In-memory, Redis-based | Extremely low latency, easy to deploy, GraphRAG-friendly | Newer, smaller community | Real-time AI applications, GraphRAG |
| **ArangoDB** | Multi-model (document + graph + key-value) | One database for everything, flexible | Less specialized than pure graph DBs | When you need graph + document together |
| **JanusGraph** | Distributed graph on top of Cassandra/HBase | Massive scale, open source | Operational complexity | Self-hosted at very large scale |
| **PuppyGraph** | Zero-ETL graph query engine over existing data | Query relational data as graph without migration | Newer, niche | Avoiding the ETL cost of moving to a graph DB |

### 8.2 The Major RDF Triple Stores

| Database | Strengths | Use case |
|---|---|---|
| **GraphDB** (Ontotext) | Strong reasoning, mature | Enterprise semantic data |
| **Stardog** | Knowledge graph platform with reasoning + federation | Enterprise data integration |
| **Virtuoso** | Battle-tested, powers DBpedia | Large-scale public KGs |
| **Apache Jena Fuseki** | Open source, easy to deploy | Prototyping, small/medium RDF graphs |
| **Amazon Neptune (RDF mode)** | Managed RDF on AWS | AWS-native RDF |
| **Blazegraph** | High-performance triplestore | Wikidata's backend until 2024 |

### 8.3 Choosing — A Quick Decision Tree

```
Are you on AWS and want managed? → Neptune
Do you need RDF / SPARQL? → Neptune (RDF) or GraphDB / Stardog
Do you need microsecond latency? → Memgraph or FalkorDB
Do you need to scale to trillions of edges? → TigerGraph or JanusGraph
Default choice, broad ecosystem? → Neo4j
You want to avoid moving data? → PuppyGraph
You want graph + document in one? → ArangoDB
```

### 8.4 Self-Hosted vs Managed

Like every database decision, this is about operational maturity. Neo4j AuraDB, Neptune, and TigerGraph Cloud are all managed offerings. Self-hosted gives you cost control and flexibility at the price of having to operate it (backups, upgrades, scaling). The general advice: managed for production unless you have strong reasons.

---

## 9. GraphRAG — The Modern Intersection with LLMs

This is where KGs are having their renaissance.

### 9.1 The Problem GraphRAG Solves

Standard RAG (vector retrieval over text chunks) fails on **multi-hop questions** and **global synthesis questions**.

- *"What's the chain of acquisitions that led Company X to own Subsidiary Y?"* — requires following entity links across multiple documents.
- *"What are the major themes in this corpus of 10,000 documents?"* — requires aggregating across the entire corpus, not retrieving a few chunks.

Vector retrieval pulls semantically-similar chunks, but it doesn't know about entity relationships and it can't aggregate at corpus scale.

GraphRAG addresses both by building a knowledge graph from the corpus and using it as the retrieval substrate.

### 9.2 The Microsoft GraphRAG Pattern (the original)

Published mid-2024, it kicked off the modern wave.

**Construction phase** (expensive, one-time):
1. Chunk the corpus
2. For each chunk, LLM extracts entities and relationships
3. Build a graph from all extracted triples
4. Run **community detection** (Leiden algorithm) to find clusters of densely-connected entities
5. For each community, LLM generates a summary describing what that community is about
6. Build hierarchical summaries: communities of communities, summarized at each level

**Query phase**:
- **Local search**: identify entities relevant to the query, fetch the local neighborhood + chunks where those entities appear. Best for "tell me about Marie Curie"-style queries.
- **Global search**: query against the community summaries (or a level of them), aggregate. Best for "what are the themes in this corpus" questions.

### 9.3 The GraphRAG Variants

The field exploded after Microsoft's paper. The variants worth knowing:

| Variant | Key innovation | Trade-off |
|---|---|---|
| **Microsoft GraphRAG** | Original; community detection + hierarchical summaries | Expensive to build; high LLM cost during construction |
| **LightRAG** | Dual-level (entity + relation) indexing, simpler than communities | Lower construction cost, less global synthesis power |
| **HippoRAG** | Personalized PageRank traversal inspired by hippocampal memory | Strong on multi-hop; less strong on aggregation |
| **Fast GraphRAG** | Optimized implementation; reportedly 27× faster than Microsoft GraphRAG, 40% accuracy gain in retrieval | Newer, less battle-tested |
| **LazyGraphRAG** | Defers KG construction; builds on-the-fly during querying | Cheaper to start, slower at query time |
| **PathRAG** | Focuses on retrieving relational paths, not just entities | Better for path-based questions |
| **HippoRAG 2** | Builds on HippoRAG; improved entity resolution and reasoning | Incremental improvement |
| **GFM-RAG** | Graph foundation model for RAG; pre-trained reasoning | Requires the foundation model |
| **PAI-2 (PersonalAI 2.0)** | Adaptive iterative retrieval with planning | 4% LLM-as-Judge gain over LightRAG/RAPTOR/HippoRAG 2 |

### 9.4 Hybrid GraphRAG — The Production Pattern

The pragmatic answer in 2026 isn't "pick one variant" — it's **combine graph and vector retrieval**:

```
Query → Both:
  ├─ Vector retrieval over chunks (semantic similarity)
  └─ Graph retrieval (entity-anchored, multi-hop traversal)
       ├─ Find entities mentioned in query
       ├─ Traverse N hops in the graph
       └─ Pull chunks attributed to traversed entities

Merge using Reciprocal Rank Fusion (RRF) or learned reranking
→ Top context → LLM generation
```

This was the approach in the late-2025 GraphRAG production paper from Microsoft Research: a hybrid retrieval strategy that fuses vector similarity with graph traversal using Reciprocal Rank Fusion (RRF), with separate embeddings maintained for entities and chunks. Improvements of up to 15% over vanilla vector retrieval baselines using LLM-as-Judge evaluation metrics.

### 9.5 When GraphRAG Is Worth It

GraphRAG isn't always worth the construction cost. It pays off when:

- **Multi-hop reasoning is essential** — queries that span 2+ entities/documents
- **Global / aggregate questions are needed** — "what are the major themes?", "give me an overview"
- **Entities are first-class in your domain** — biomedical, legal, financial, supply chain
- **The corpus is stable** — you're not constantly re-indexing
- **Hallucination has high cost** — you need verifiable provenance

It's overkill when:

- Single-hop semantic retrieval works
- Corpus is changing too fast to maintain a KG
- Cost-sensitive deployment

### 9.6 The Construction Cost Reality

Microsoft GraphRAG on a 1M-document corpus with gpt-4o-mini for extraction costs roughly **$5K–20K in API costs** depending on chunking and prompt design. With Claude Opus, multiply by ~10. This is the gating factor for adoption.

Mitigations:
- **Dependency-parsing-first construction**: dependency parsing achieves 94% of LLM-based extraction performance (61.87% vs 65.83% in some benchmarks) at far lower cost.
- **Incremental construction**: only re-extract changed documents
- **LLM tiering**: cheap model for extraction, expensive model only for ambiguous cases

---

## 10. Real-World Applications

### 10.1 Search and Information Retrieval

Google Knowledge Graph powers the info boxes you see on search results. Behind the scenes, Google maintains a KG of 500+ billion facts about 5 billion entities. When you search "Marie Curie", the KG provides the structured panel.

### 10.2 Recommendation Systems

Knowledge-graph-aware recommenders use entity relationships (e.g., "users who bought books by this author also bought…") in addition to collaborative filtering. Spotify and Netflix both use KG-style modeling for content metadata.

### 10.3 Fraud Detection

The classic KG win. Traditional rule-based systems can't see patterns like: "this account is linked to a phone number that's also linked to three accounts that were flagged last week." Graph traversal makes that query trivial.

### 10.4 Drug Discovery and Biomedical Research

The biomedical world runs on KGs — UMLS, Gene Ontology, MeSH, Mondo, ChEBI. Modern drug discovery pipelines connect proteins, diseases, drugs, and genes in a KG to identify candidate drug targets through graph queries like "find diseases connected to this protein via a known drug interaction."

### 10.5 Cybersecurity

Threat intelligence is fundamentally graph-shaped. An IP address connects to malware, which connects to a campaign, which connects to a threat actor, which connects to other IPs. Half of the top-20 cybersecurity companies use graph databases for threat intelligence.

### 10.6 Customer 360 / Master Data Management

Resolving "the same customer" across CRM, billing, support, and product systems is an entity resolution problem at heart. A KG can store the unified view and let queries flow naturally.

### 10.7 Supply Chain and Logistics

Goods flow through networks of suppliers, warehouses, and routes. Disruption propagation ("if this port shuts down, what products are at risk?") is a graph query.

### 10.8 Compliance and Regulatory

Sanctions screening, beneficial ownership disclosure, and AML investigations all involve tracing relationships across entities. Panama Papers analysis used Neo4j extensively.

### 10.9 LLM Grounding (the new one)

Using a KG to ground LLM responses with cited facts. The user asks a question, the LLM queries the KG, gets back facts with provenance, and synthesizes an answer that cites the specific triples it used. This is the production pattern for high-stakes Q&A systems in 2026.

---

## 11. Production Considerations

### 11.1 Scale

Property graph databases handle:
- Up to ~10B nodes/edges on a single Neo4j cluster
- 100B+ on TigerGraph or JanusGraph
- Sub-millisecond traversals on FalkorDB / Memgraph for in-memory workloads

For most enterprise KGs, you're nowhere near these limits. The "big graph" problem is rarer than the "messy graph" problem.

### 11.2 Updates and Maintenance

KGs aren't built once. They evolve:
- New facts arrive from data sources
- Existing facts get corrected
- Schema evolves (new entity types, new relationships)
- Entities merge (entity resolution improves)

You need:
- **Versioning**: at minimum, timestamp every triple ("valid from", "valid to")
- **Provenance**: where did this fact come from? Critical for trust and debugging
- **Reversible operations**: a bad batch update shouldn't be permanent
- **Incremental update pipelines**: don't rebuild the whole graph for one new document

### 11.3 Quality

A KG with bad data is worse than no KG — people trust it and get wrong answers. Quality strategies:

- **Source validation**: only ingest from trusted sources, or weight by source reliability
- **Cross-source agreement**: if three sources agree on a fact, confidence is high
- **Automated checks**: unique IDs, required properties, type constraints
- **Spot-check assertions**: known facts that must always be retrievable
- **Confidence scores on triples**: not all facts are equally certain

### 11.4 Federation

When you have multiple KGs (your enterprise KG, Wikidata, a partner's KG), you can federate queries. SPARQL has built-in federation via `SERVICE`; property graphs typically don't, but A2A and similar protocols are starting to enable cross-system queries.

### 11.5 Cost

Storage is cheap; LLM extraction is expensive. If you're using LLMs for construction, that's your dominant cost. Mitigations:
- Hybrid extraction (dependency parsing + LLM only for hard cases)
- Caching: never re-extract from an unchanged document
- Incremental: only process the delta
- Cheaper models for extraction; reserve premium models for ambiguity resolution

### 11.6 Observability

Track:
- **Construction metrics**: extraction throughput, cost per document, confidence distribution
- **Query metrics**: latency per query type, cache hit rate, slow-query log
- **Quality metrics**: validation pass rate, drift in source-data agreement
- **Drift**: if Wikidata says X and your KG says Y, why?

---

## 12. When to Use a KG vs Alternatives

This is the highest-leverage decision and the one interviewers love to probe.

### 12.1 KG vs Relational Database

| Use a KG when | Use relational when |
|---|---|
| Relationships are central to queries | Relationships are incidental |
| Schema varies widely across entity types | Schema is stable and uniform |
| Multi-hop traversal is common | Most queries are single-table aggregates |
| You need explicit semantics / typed relationships | Implicit relations via foreign keys are enough |
| Data is sparse (lots of optional attributes) | Data is dense |

### 12.2 KG vs Vector Database

This is the modern question. The honest answer: **they're complementary**, not competing.

| Use a vector DB when | Use a KG when |
|---|---|
| Queries are about semantic similarity | Queries are about entity relationships |
| Source content is unstructured text | Source content has clear entities |
| Single-hop "find me the most relevant chunk" | Multi-hop "trace the path from A to B" |
| Hallucination tolerance is moderate | Need verifiable provenance |
| Construction cost matters | Reasoning quality matters more |

**In production GraphRAG systems, you use both.** Vector for semantic chunk retrieval; KG for structured fact retrieval and multi-hop traversal. They merge at the context-assembly stage.

### 12.3 KG vs Document Store

Document stores (MongoDB, Elasticsearch) excel at full-text search and semi-structured documents. KGs excel at entity-centric and relationship-centric queries. Often complementary: store the source documents in Elasticsearch, store the extracted KG in Neo4j, link them.

### 12.4 When NOT to Use a KG

- **Your data has no entities or relationships worth modeling explicitly.** Most analytics workloads.
- **You can't afford the construction cost.** KG construction is expensive in human + LLM time.
- **Your data is too fast-changing to maintain a graph.** Real-time streams of unstructured text are hard to KG-ify continuously.
- **You can solve the problem with vector search.** If single-hop semantic retrieval gives you 90% of what you need, adding a KG is overkill.

---

## 13. Anti-Patterns

**1. KG for the sake of having a KG.** Building a graph because it's trendy, not because graph-shaped queries are central to the workload. The result is an expensive way to do things SQL would have done better.

**2. Ontology paralysis.** Spending six months designing the perfect ontology before ingesting any data. You learn what you actually need by trying to use the graph. Start with the simplest schema and iterate.

**3. Modeling everything as a node.** "What if cities are nodes? What if countries are nodes? What if calendar dates are nodes?" Eventually, your graph is mostly noise. Reserve node status for things that have identity worth following.

**4. No entity resolution.** Building a graph from messy data without resolving aliases. Your graph ends up with three Marie Curies and the multi-hop queries return zero results.

**5. LLM-only extraction at scale.** Microsoft GraphRAG-style construction is genuinely expensive. If you have a million documents, dependency parsing or hybrid extraction will save you tens of thousands of dollars.

**6. Treating the graph as a single source of truth.** A KG is one view of your data, often derived from other sources. Treat it as a query-optimized projection, not the system of record (unless you really mean it).

**7. Not versioning.** Facts change. Without versioning, you can't answer "what did we know on date X?" or "when did this fact change?"

**8. Underestimating maintenance.** A KG is a living system. Construction is 20% of the work; keeping it accurate as the world changes is the other 80%.

**9. Querying without thinking about indexes.** Just like relational databases, KGs need indexes on properties that are queried often. Neo4j's `:Person(name)` index changes a query from seconds to milliseconds.

**10. Building GraphRAG for problems vector RAG already solves.** GraphRAG is much harder to build and maintain than vector RAG. If your queries are single-hop semantic lookups, you don't need a graph.

---

## 14. Practical Workflow — Building One End to End

A concrete sequence for a real project.

### Step 1: Define the use case

What questions will this graph answer? Write down 10 example queries. If they don't involve traversal or entity-centric questions, stop — you don't need a graph.

### Step 2: Identify entities and relationships

From the queries, extract the entity types (Person, Company, Drug) and relationship types (works_at, treats, located_in). This is your starter ontology. Keep it small — 10–20 entity types max for the first iteration.

### Step 3: Identify data sources

For each entity type, where does the data come from? Internal databases, external APIs, documents? Map each source to the ontology.

### Step 4: Pick a database

For a first project, default to **Neo4j** (or Memgraph if you need microsecond latency). Skip the RDF/property-graph debate unless you have a specific reason for RDF.

### Step 5: Build the extraction pipeline

For structured sources: write mapping code. For unstructured: hybrid extraction (dependency parsing + LLM for hard cases).

```python
from neo4j import GraphDatabase
import spacy

nlp = spacy.load("en_core_web_lg")

def extract_from_text(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "type": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        })
    # ... extract relationships via dependency parsing or LLM
    return entities, relationships

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def load_triple(subject, predicate, obj):
    with driver.session() as session:
        session.run(
            """
            MERGE (s {name: $subject})
            MERGE (o {name: $object})
            MERGE (s)-[:RELATION {type: $predicate}]->(o)
            """,
            subject=subject, predicate=predicate, object=obj
        )
```

### Step 6: Entity resolution

Before loading, dedupe and normalize. Maintain an alias table. Use string similarity for fuzzy matching, embedding similarity for tougher cases.

### Step 7: Load and validate

Bulk-load for the initial build (Neo4j's `LOAD CSV` or `neo4j-admin import` is much faster than per-row inserts). After loading, run assertion tests.

### Step 8: Build query patterns

Write the 10 example queries from step 1. Tune indexes. Measure performance.

### Step 9: Wire up to your application

Cypher queries from your backend service, results back to the user or LLM.

### Step 10: Set up maintenance

- Incremental update pipeline for new data
- Quality monitoring (validation pass rate over time)
- Provenance tracking on every triple
- Backups

---

## 15. Interview-Ready Talking Points

For when these come up in design discussions.

### "When would you choose a knowledge graph over a vector database?"

Strong answer:

> "They're complementary, not competing. I use a vector database when retrieval is fundamentally about semantic similarity over text chunks — 'find me the parts of these documents that are about X.' I use a knowledge graph when the queries are entity-centric or require multi-hop reasoning — 'find me the path from A to B,' 'what are all the entities related to this drug through clinical trials.'
>
> In production GraphRAG systems, I'd use both: vector retrieval for semantic chunk lookup, graph retrieval for structured fact retrieval and traversal, merged at the context-assembly stage. The Microsoft GraphRAG production paper from late 2025 reported about 15% improvement over vector-only baselines using exactly this hybrid pattern with reciprocal rank fusion."

### "What's the construction cost of GraphRAG, and how would you manage it?"

Strong answer:

> "Microsoft-style LLM-driven GraphRAG construction on a million-document corpus runs $5K–20K in API costs with gpt-4o-mini, multiplied by ~10x for premium models. That's the gating factor for adoption.
>
> The cost optimizations I'd reach for: first, hybrid extraction — dependency parsing handles the syntactic majority of entity-relation pairs and gets you within 94% of pure-LLM performance at a fraction of the cost. Second, model tiering — cheap model for extraction, expensive model only for ambiguity resolution. Third, incremental construction — never re-extract from unchanged documents."

### "Should our KG use RDF or property graphs?"

Strong answer:

> "For most internal enterprise applications, property graphs — relationships have first-class properties, Cypher is much easier to read and write, and the tooling around Neo4j and similar is more mature.
>
> RDF earns its complexity in a few specific cases: biomedical or regulatory domains where established ontologies exist (UMLS, GO, Mondo), publish-and-share scenarios where SPARQL federation matters, or cases where formal reasoning is a hard requirement. In 2026, 80%+ of new KG projects in production are property-graph based."

### "How do you handle entity resolution at scale?"

Strong answer:

> "Layered approach. First, exact-match plus an alias table for known aliases. Second, string similarity (Jaro-Winkler or token-set ratio) for fuzzy matches. Third, embedding similarity — encode entity mentions plus surrounding context with a sentence embedding model, cluster by cosine similarity. Fourth, linking to an external reference KG when possible — if Wikidata has a QID for the entity, link to that, and now you also get federation for free.
>
> For ambiguous cases, an LLM disambiguator gets the mention plus context plus candidate entities and picks. Production pipelines combine all four. Entity resolution is the highest-leverage and most error-prone step in KG construction — bad ER cascades into useless multi-hop queries."

### "How would you ground an LLM's response in a knowledge graph?"

Strong answer:

> "Three-stage. First, entity linking: parse the user's query, identify entity mentions, link them to graph nodes. Second, subgraph extraction: pull the N-hop neighborhood around those entities, plus any chunks attributed to those entities in the source corpus. Third, generation with explicit citation: pass the subgraph plus the chunks to the LLM with a prompt that requires citing the specific triples or chunks for every factual claim. Validate citations post-hoc against the actual graph; reject responses that hallucinate non-existent triples.
>
> The graph gives you provenance — every claim traces back to a specific source via a specific path. That's the killer feature for high-stakes Q&A: not just better answers, but verifiable answers."

### "What's the biggest risk in adopting a knowledge graph?"

Strong answer:

> "Construction cost and maintenance burden. The graph is the easy part — the database itself runs fine on Neo4j or Neptune. The hard part is keeping it accurate. Ontology drift, schema evolution, entity resolution errors compounding, source data changing without the graph being updated. Most KG projects fail not because the graph technology is wrong, but because the team underestimated the ongoing maintenance.
>
> The mitigation is to treat the KG like a derived data product, not a system of record: version it, track provenance, have automated quality checks, and make it cheap to rebuild from sources if drift gets bad. And resist the urge to model everything as a node — most successful production KGs are smaller and more focused than their architects originally planned."

### "What's new in the field?"

Strong answer:

> "The 2024–2026 wave is GraphRAG and its variants. Microsoft's original paper kicked it off with community-based hierarchical summaries. Since then we've had LightRAG with dual-level indexing, HippoRAG with personalized PageRank traversal, Fast GraphRAG with claimed 27× speedups, LazyGraphRAG deferring construction to query time. The convergence is toward hybrid retrieval — graph plus vector with learned reranking — and toward dependency-parsing-augmented construction to control LLM cost.
>
> The deeper trend is that knowledge graphs are moving from 'a thing some industries use' to 'the structured-knowledge layer underneath production LLM systems.' That's a meaningful shift in how AI systems are architected."

---

## Quick Reference Cheat Sheet

**Triple**: subject — predicate — object (e.g., Marie Curie — born_in — Warsaw)

**Property graph**: nodes + relationships, both with labels/types and properties. Default for engineering applications.

**RDF**: triples with URIs. Default for semantic / regulatory / scientific data.

**Cypher**: query language for property graphs. Pattern-based, easy to read.

**SPARQL**: query language for RDF. Powerful but verbose.

**Ontology**: formal schema of entity and relationship types. Document at minimum.

**Entity resolution**: detecting that "Marie Curie" and "Madame Curie" are the same entity. The single most error-prone step in KG construction.

**GraphRAG**: using a KG as part of LLM retrieval. Pattern: build the KG from a corpus, retrieve subgraphs at query time, ground LLM generation in the retrieved facts.

**Default tooling stack for a new KG project**: Neo4j (or Memgraph for low latency) + spaCy for NER + an LLM (Claude or gpt-4o-mini) for relation extraction + custom entity resolution.

**Default GraphRAG framework**: Microsoft GraphRAG for full quality at high cost, LightRAG for cost-efficient, Fast GraphRAG for speed, hybrid graph+vector retrieval with RRF for production.