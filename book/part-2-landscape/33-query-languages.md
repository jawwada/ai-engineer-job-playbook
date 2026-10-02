# 33. Query languages an AI engineer meets: SQL, Spark/Databricks SQL, Cypher/GQL, SPARQL, Gremlin, GraphQL, KQL, PromQL/LogQL, Elasticsearch DSL, vector-store queries, and jq

> **What you need to be able to say:** read and write the everyday forms of each; know which engine speaks which; and know what an agent needs (schemas, examples, validation) to generate them safely. Each section ends with the one query to practice until you can type it from memory.

## 33.1 SQL (the one you must be fluent in)

Everything else is optional; SQL is not. Interviewers test joins, aggregation, window functions, CTEs, and reasoning about NULLs and duplicates.

```sql
-- top 3 products by revenue per region, last 90 days, with share of regional revenue
WITH sales AS (
  SELECT region, product_id, SUM(amount) AS revenue
  FROM orders
  WHERE order_date >= CURRENT_DATE - INTERVAL '90 days' AND status = 'paid'
  GROUP BY region, product_id
), ranked AS (
  SELECT *, RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS rk,
         revenue / SUM(revenue) OVER (PARTITION BY region) AS share
  FROM sales
)
SELECT region, product_id, revenue, ROUND(share, 3) AS share
FROM ranked WHERE rk <= 3 ORDER BY region, rk;
```

Know: `INNER/LEFT/FULL JOIN`, anti-joins (`NOT EXISTS`), `GROUP BY` with `HAVING`, window functions (`ROW_NUMBER`, `RANK`, `LAG`, `SUM OVER`), CTEs, `CASE`, date arithmetic, `COALESCE`, deduplication with `ROW_NUMBER`, `EXPLAIN` and indexes, and the dialect differences (Postgres, MySQL, T-SQL, BigQuery, Snowflake, Databricks). **For agents (text-to-SQL):** give the model a semantic layer or a curated schema with descriptions and sample rows, few-shot examples, read-only credentials, row limits and timeouts, and validate generated SQL (parse with `sqlglot`, check tables/columns exist) before executing.

**Vector SQL (pgvector):**

```sql
SELECT id, title, 1 - (embedding <=> $1) AS cosine_sim
FROM chunks
WHERE tenant_id = $2 AND doc_date >= '2026-01-01'
ORDER BY embedding <=> $1
LIMIT 10;
```

(`<=>` is cosine distance, `<->` Euclidean, `<#>` negative inner product, `<+>` L1; HNSW index: `CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);`. Query-time knobs: `SET hnsw.ef_search = 100;` for recall, and on pgvector 0.8+ `SET hnsw.iterative_scan = relaxed_order;` so a selective `WHERE tenant_id = …` keeps scanning until it finds enough rows instead of returning fewer than `LIMIT`. Use `halfvec` (16-bit) or binary quantization with re-ranking to halve or shrink index memory. Check with `EXPLAIN ANALYZE` that the index is actually used — an `ORDER BY` on an expression that does not match the operator class silently falls back to a sequential scan.)

## 33.2 Spark SQL, Databricks SQL, BigQuery SQL, Snowflake SQL

Same core as SQL with platform functions: Databricks `ai_query('model', prompt)`, `ai_extract`, `ai_classify`, `vector_search(index => …, query_text => …, num_results => …)`, `ai_parse_document`; BigQuery `AI.GENERATE` (and typed `AI.GENERATE_BOOL/INT/DOUBLE`), `AI.GENERATE_TABLE`, `AI.FORECAST`, the older `ML.GENERATE_TEXT`, `ML.GENERATE_EMBEDDING`, `VECTOR_SEARCH`; Snowflake's Cortex AI Functions `AI_COMPLETE`, `AI_CLASSIFY`, `AI_FILTER` (an LLM predicate usable in `WHERE` and joins), `AI_AGG`, `AI_EMBED`, plus the older `SNOWFLAKE.CORTEX.COMPLETE`, `EMBED_TEXT_1024`, `VECTOR_COSINE_SIMILARITY`, and Cortex Search. Every one of these is a model call per row — test on a `LIMIT` sample and estimate rows × tokens × price before running it on a full table (chapter 21). PySpark DataFrame API mirrors SQL (`df.groupBy().agg()`, `Window.partitionBy()`); Delta features: `MERGE INTO`, time travel (`VERSION AS OF`), `OPTIMIZE`/`ZORDER`, liquid clustering.

```sql
-- Databricks: enrich a table with an LLM classification in one pass
SELECT ticket_id,
       ai_classify(body, ARRAY('billing', 'technical', 'sales', 'other')) AS category
FROM support.tickets WHERE created_at >= current_date() - 1;
```

## 33.3 Cypher and GQL (Neo4j, Memgraph, FalkorDB, Neptune openCypher)

Pattern matching with ASCII-art: `(node)-[:REL]->(node)`.

```cypher
// customers who bought a product that was recalled, and the account manager to notify
MATCH (c:Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(p:Product)<-[:AFFECTS]-(r:Recall)
MATCH (c)-[:MANAGED_BY]->(m:Employee)
WHERE r.date >= date('2026-01-01')
RETURN m.email AS manager, c.name AS customer, collect(DISTINCT p.sku) AS products
ORDER BY manager;
```

Know: `MATCH/OPTIONAL MATCH`, `WHERE`, `WITH` (pipelining and aggregation), variable-length paths `[:KNOWS*1..3]` (always bound the upper limit — an unbounded `*` on a dense graph is the classic runaway query), `shortestPath`, `EXISTS { … }` subqueries, `MERGE` (upsert — merge on the key property only, then `SET` the rest, or you create duplicates), indexes and constraints, `EXPLAIN/PROFILE`, and the GDS library for algorithms (PageRank, Louvain/Leiden, node similarity). GQL is the ISO standard (ISO/IEC 39075:2024); Neo4j's calendar-versioned releases (2025.x onwards, "Cypher 25") implement most of its mandatory features alongside Cypher. **For agents (text-to-Cypher):** supply the schema (`CALL db.schema.visualization()` summarized), label and relationship whitelists, examples, and run read-only with limits.

## 33.4 SPARQL (RDF triple stores: GraphDB, Stardog, Virtuoso, Neptune RDF, Wikidata)

```sparql
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd:  <http://www.wikidata.org/entity/>
SELECT ?company ?companyLabel ?founded WHERE {
  ?company wdt:P31 wd:Q4830453 ;          # instance of: business
           wdt:P452 wd:Q11660 ;           # industry: artificial intelligence
           wdt:P571 ?founded .
  FILTER(YEAR(?founded) >= 2020)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} ORDER BY DESC(?founded) LIMIT 20
```

Know: triple patterns, `OPTIONAL`, `FILTER`, `UNION`, property paths (`wdt:P279*` for subclass-of transitively), aggregates with `GROUP BY`, `CONSTRUCT` to produce graphs, federated `SERVICE`, named graphs, and that ontologies (RDFS/OWL) let the store infer triples. SHACL validates shapes.

## 33.5 Gremlin (Apache TinkerPop: Neptune, JanusGraph, Cosmos DB Gremlin API)

Traversal steps chained in code:

```groovy
g.V().has('Customer', 'id', 'C-1001')
 .out('PLACED').out('CONTAINS').in('AFFECTS').hasLabel('Recall')
 .has('date', gte('2026-01-01'))
 .dedup()
 .project('recall', 'products')
   .by('id').by(__.out('AFFECTS').values('sku').fold())
```

(`dedup()` matters: a customer who bought two affected products in three orders would otherwise produce the same recall six times. Note too that the `products` list here is every SKU the recall affects, not only the ones this customer bought — keeping that correlation needs step labels, as in chapter 25's Gremlin example. Dates compare correctly as strings only if they are stored in ISO format.)

Know: `V()`, `E()`, `has`, `out/in/both`, `repeat().times()`, `path()`, `group().by()`, `project`, `as()`/`select()`/`where()` for correlating earlier steps, `dedup()`, and that Gremlin is imperative where Cypher/SPARQL are declarative.

## 33.6 GraphQL (API query language — not a graph database)

```graphql
query CustomerOrders($id: ID!) {
  customer(id: $id) {
    name
    orders(last: 5, status: PAID) { id total items { sku qty } }
  }
}
```

Agents often call GraphQL APIs as tools; schema introspection (`__schema`) gives the model exact types; persist and allow-list queries in production.

## 33.7 KQL — Kusto Query Language (Azure Monitor, Log Analytics, Sentinel, Fabric Real-Time Intelligence)

```kusto
AppDependencies
| where TimeGenerated > ago(1h)
| extend model      = tostring(Properties["gen_ai.request.model"]),
         out_tokens = toint(Properties["gen_ai.usage.output_tokens"]),
         route      = tostring(Properties["route"])
| where model startswith "claude"
| summarize p95_latency_ms = percentile(DurationMs, 95), total_out_tokens = sum(out_tokens)
          by bin(TimeGenerated, 5m), route
| order by TimeGenerated desc
```

(An outgoing model call instrumented with OpenTelemetry lands in Application Insights as a dependency, so its latency is in `AppDependencies.DurationMs`; `AppTraces` holds log messages and has no duration column. Span attributes arrive in the dynamic `Properties` bag and must be cast with `tostring()`/`toint()` before comparison or aggregation.)

Pipe-based, table → operators (`where`, `extend`, `summarize`, `join`, `parse`, `make-series`, `render`); the language for Azure observability questions.

## 33.8 PromQL and LogQL (Prometheus/Grafana)

```promql
# p95 latency of LLM calls per model over 5 minutes
histogram_quantile(0.95, sum(rate(gen_ai_client_operation_duration_seconds_bucket[5m])) by (le, gen_ai_request_model))

# tokens per second by route and token type (input/output)
sum(rate(gen_ai_client_token_usage_sum[5m])) by (route, gen_ai_token_type)
```

(`gen_ai.client.token.usage` is a *histogram* in the OpenTelemetry conventions, so Prometheus exposes `_bucket`, `_sum` and `_count` series — the token total is `_sum`, and there is no `_total` counter. `route` is your own attribute, not a convention. Use a rate window of at least four scrape intervals, typically `[5m]`.)

LogQL filters logs with the same label model: `{service="agent"} |= "tool_error" | json | duration > 2s`. Know: counters vs gauges vs histograms, `rate()`, `increase()`, aggregation `by`/`without`, recording rules and alerts.

## 33.9 Elasticsearch / OpenSearch query DSL (and hybrid search)

```json
{
  "size": 20,
  "retriever": { "rrf": {
    "retrievers": [
      { "standard": { "query": { "bool": {
          "must":   [{ "match": { "text": { "query": "pre-authorization timeline", "operator": "and" }}}],
          "filter": [{ "term": { "tenant": "acme" }}, { "range": { "updated": { "gte": "2026-01-01" }}}]
      }}}},
      { "knn": { "field": "embedding", "query_vector": [0.12, -0.3, "..."], "k": 50, "num_candidates": 200,
                 "filter": { "term": { "tenant": "acme" }}}}
    ],
    "rank_window_size": 50, "rank_constant": 60
  }}
}
```

(Current Elasticsearch expresses hybrid search with the `retriever` API; the older top-level `knn` + `"rank": {"rrf": {}}` form appears in older tutorials and the documentation now says RRF via sub-searches is no longer supported. Note the tenant filter is repeated *inside* the `knn` retriever — a filter on the lexical branch does not restrict the vector branch, which is exactly how cross-tenant results leak into hybrid search. OpenSearch does the same job with a `hybrid` query plus a search pipeline that normalizes and combines scores.)

Know: `match` vs `term`, `bool` with `must/should/filter`, analyzers, aggregations, `knn` and hybrid with RRF via retrievers, and the pipeline/ingest processors (or `semantic_text` fields) for embedding at index time.

## 33.10 Vector-store query APIs

Pinecone (`index.query(vector=..., top_k=10, filter={"tenant": {"$eq": "acme"}}, include_metadata=True)`), Qdrant (`search` with `filter` conditions and `with_payload`), Weaviate (GraphQL-style `Get` with `nearVector`/`hybrid` and `where`), Milvus (`search` with `expr`), Vertex AI Vector Search, Azure AI Search (`vectorQueries` + `search` text + `filter` OData), Databricks `vector_search()` in SQL. The concepts are identical: a vector, a `k`, a metadata filter, and optional hybrid text — chapter 18 explains why the filter semantics matter.

## 33.11 MongoDB, Redis, DynamoDB

MongoDB aggregation pipelines (`$match`, `$group`, `$lookup`, `$vectorSearch` in Atlas, which must be the first stage of the pipeline and takes its own `filter` on pre-declared filter fields); Redis commands and the Redis Query Engine (`FT.SEARCH idx "(@text:claim)=>[KNN 10 @vec $v]" PARAMS 2 v <blob> DIALECT 2` — the vector is passed as a binary parameter and dialect 2 is required); DynamoDB `Query` by partition/sort key with `KeyConditionExpression` — an agent tool over DynamoDB should encapsulate the key design, because a `Scan` generated by a model reads (and bills) the whole table.

## 33.12 jq, Pandas and the small languages

`jq '.items[] | select(.status=="paid") | {id, total}'` for JSON on the command line; Pandas/Polars expressions for tabular work in notebooks; regular expressions for extraction; JSONPath/XPath for structured documents; and policy languages for authorization — OPA's Rego (Datalog-inspired rules over JSON input) and Cedar (AWS's `permit`/`forbid` policies over principal, action, resource and context, designed to be analysable; used by Amazon Verified Permissions and AgentCore Policy) — worth recognizing in security conversations.

## 33.13 What an agent needs to generate any of these safely

A schema or grammar it can see (tables/columns, labels/relationships, fields), a handful of verified examples, read-only credentials and limits, syntax validation before execution, a result-size cap, an execution timeout, logging of every generated query with its result status, and an eval set of (question, expected query/result) pairs. The model writes the query; the harness decides whether it runs.
