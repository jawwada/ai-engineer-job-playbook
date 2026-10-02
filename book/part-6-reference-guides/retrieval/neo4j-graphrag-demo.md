# Small Python + Neo4j GraphRAG Demo

This example uses a tiny vendor-risk graph to answer:

```text
Which owner is responsible for vendors storing customer billing data without a current DPA?
```

The demo intentionally mirrors a simple GraphRAG flow:

1. `index`: model entities and relationships in Neo4j
2. `retrieve`: use Cypher to pull the relevant subgraph
3. `generate`: compose an answer only from the retrieved graph evidence

Files:

- Script: [neo4j_graphrag_stripe_demo.py](<./ Search/Interview preparation/Retrieval/neo4j_graphrag_stripe_demo.py>)

## Graph Schema

Nodes:

- `Vendor`
- `Team`
- `DataType`
- `ComplianceRecord`
- `Document`

Relationships:

- `(:Vendor)-[:OWNED_BY]->(:Team)`
- `(:Vendor)-[:STORES]->(:DataType)`
- `(:Vendor)-[:HAS_COMPLIANCE_RECORD]->(:ComplianceRecord)`
- `(:Document)-[:MENTIONS]->(:Vendor|:Team|:DataType|:ComplianceRecord)`

For the seeded data:

- `Stripe` is owned by `Finance Engineering`
- `Stripe` stores `Billing Email` and `Payment Metadata`
- `Stripe` has `DPA 2025 = missing`
- `Twilio` and `Zendesk` are included as non-matching examples

## Setup

Install the Neo4j Python driver:

```bash
pip install neo4j
```

Run a local Neo4j instance with Docker:

```bash
docker run --rm \
  --name neo4j-graphrag-demo \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Set connection variables if you are not using the defaults:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password
export NEO4J_DATABASE=neo4j
```

## Run

Seed the graph:

```bash
python3 "./ Search/Interview preparation/Retrieval/neo4j_graphrag_stripe_demo.py" seed
```

Ask the demo question:

```bash
python3 "./ Search/Interview preparation/Retrieval/neo4j_graphrag_stripe_demo.py" ask
```

Ask the same query with an explicit question string:

```bash
python3 "./ Search/Interview preparation/Retrieval/neo4j_graphrag_stripe_demo.py" ask \
  "Which owner is responsible for vendors storing customer billing data without a current DPA?"
```

## Expected Output

```text
Question: Which owner is responsible for vendors storing customer billing data without a current DPA?

Answer:
- Finance Engineering is responsible for Stripe. Stripe stores Billing Email, Payment Metadata and its 2025 DPA status is missing.

Evidence Paths:
- (Stripe)-[:OWNED_BY]->(Finance Engineering) [source: Engineering Ownership Map]
- (Stripe)-[:STORES]->(Billing Email, Payment Metadata) [source: Data Inventory 2025]
- (Stripe)-[:HAS_COMPLIANCE_RECORD]->(DPA 2025 = missing) [source: Legal Tracker 2025]
- (Stripe) is cataloged in Vendor Inventory 2025.
```

## Interview Framing

This is a good concise explanation:

```text
Flat vector RAG might retrieve one policy chunk about DPAs or one ownership document, but GraphRAG makes the answer easy because the retrieval unit is the relationship path:

Team <- OWNED_BY - Vendor - STORES -> DataType
Vendor - HAS_COMPLIANCE_RECORD -> DPA status

That gives me multi-hop retrieval plus clean provenance.
```

To make this production-grade, you would usually add:

- entity extraction from unstructured documents into the graph
- hybrid retrieval with vector search plus graph traversal
- LLM answer synthesis over the retrieved subgraph
- permission-aware filtering
- citation validation
