# Agentic Python + Neo4j GraphRAG Demo

This version is the agentic one.

Files:

- Script: [neo4j_agentic_graphrag_stripe_demo.py](<./ Search/Interview preparation/Retrieval/neo4j_agentic_graphrag_stripe_demo.py>)
- Baseline non-agentic version: [neo4j_graphrag_stripe_demo.py](<./ Search/Interview preparation/Retrieval/neo4j_graphrag_stripe_demo.py>)

## Why This Counts As Agentic GraphRAG

The earlier baseline script did:

```text
one graph query -> one grounded answer
```

This agentic version does:

```text
question
  -> planner extracts year, categories, and subgoals
  -> agent finds candidate vendors
  -> agent calls graph tools per vendor
  -> agent checks whether evidence is sufficient
  -> agent expands neighbors for explainability
  -> final answer with trace
```

That is the key difference: retrieval is not one fixed query. The agent decides which graph tool to call next based on what evidence is still missing.

## Graph Tools

The agent uses these Neo4j-backed tools:

- `find_candidate_vendors`
- `get_vendor_owner`
- `get_vendor_data_types`
- `get_vendor_compliance`
- `get_vendor_documents`
- `expand_vendor_neighbors`

## Setup

Install the Neo4j driver:

```bash
pip install neo4j
```

Run Neo4j locally:

```bash
docker run --rm \
  --name neo4j-graphrag-demo \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Set connection variables if needed:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password
export NEO4J_DATABASE=neo4j
```

## Run

Seed the graph:

```bash
python3 "./ Search/Interview preparation/Retrieval/neo4j_agentic_graphrag_stripe_demo.py" seed
```

Ask the Stripe question:

```bash
python3 "./ Search/Interview preparation/Retrieval/neo4j_agentic_graphrag_stripe_demo.py" ask
```

Ask a custom question:

```bash
python3 "./ Search/Interview preparation/Retrieval/neo4j_agentic_graphrag_stripe_demo.py" ask \
  "Which owner is responsible for vendors storing customer billing data without a current DPA?"
```

## What To Say In An Interview

Good short framing:

```text
This is an agentic GraphRAG pattern, not just graph lookup. I first plan from the question, then I use graph tools iteratively to gather missing evidence: ownership, stored data, compliance status, and source documents. The final answer is produced only after the agent decides the evidence is sufficient.
```

Good stronger framing:

```text
In production I would replace the rule-based planner with an LLM planner, keep the graph tools, add vector retrieval as a fallback, and let the agent choose between local graph traversal, broader graph expansion, and document retrieval depending on uncertainty.
```
