# 49. Engineering fundamentals for AI engineers

> **What you need to be able to say:** the software-engineering basics interviewers assume — production Python, API design, databases, distributed-systems patterns, testing, security basics, Git — each with the AI-specific twist and an example. Go deeper: Part 6 → *Python and backend guide*, *CI/CD pipelines complete guide*, *Kubernetes complete guide*; for algorithms and data structures in the coding round, chapter 39d.

## 49.1 Production Python

- **Project structure and packaging**: `pyproject.toml`, `uv`/`poetry`/`pip-tools` for locked dependencies, `src/` layout, entry points, semantic versions; Docker images with multi-stage builds and non-root users.
- **Typing and validation**: type hints everywhere, `mypy`/`pyright`, Pydantic models for every boundary (API payloads, tool arguments, LLM structured outputs, config).
- **Async**: `asyncio` for I/O-bound work (LLM and tool calls run concurrently with `asyncio.gather`, semaphores for rate limits); avoid blocking calls in async paths; use `httpx.AsyncClient`; know when a thread pool or process pool is the right tool (CPU-bound parsing).
- **Error handling and resilience**: explicit exceptions, retries with exponential backoff and jitter (`tenacity`), timeouts on every network call, circuit breakers for providers, idempotency keys for side effects, structured logging with trace ids.
- **Configuration and secrets**: environment variables and settings objects (`pydantic-settings`), no secrets in code, per-environment configs.
- **Code quality**: `ruff` (lint + format), pre-commit hooks, small functions, pure functions for logic and thin adapters for I/O, docstrings that say what and why.
- **Performance**: profile before optimizing (`cProfile`, `py-spy`), vectorize with NumPy/Polars, batch I/O, cache (`functools.lru_cache`, Redis), stream large files.

Example: a tool wrapper that is typed, validated, timed, retried, logged and idempotent — the unit of safety in any agent:

```python
import logging, time
import httpx
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter

log = logging.getLogger(__name__)

class GetOrder(BaseModel):
    order_id: str = Field(pattern=r"^ORD-\d{6}$")

def _transient(exc: BaseException) -> bool:
    # Retry only what a retry can fix: network errors, timeouts, 429 and 5xx.
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and (
        exc.response.status_code == 429 or exc.response.status_code >= 500
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(1, 8),
       retry=retry_if_exception(_transient), reraise=True)
async def get_order(args: GetOrder, client: httpx.AsyncClient, trace_id: str) -> dict:
    t0 = time.perf_counter()
    r = await client.get(f"/orders/{args.order_id}", timeout=5.0)
    if r.status_code == 404:
        return {"status": "not_found", "order_id": args.order_id}   # a result, not an exception
    r.raise_for_status()
    log.info("tool=get_order id=%s status=%s ms=%.0f trace=%s",
             args.order_id, r.status_code, (time.perf_counter() - t0) * 1000, trace_id)
    return {"status": "found", "order": r.json()}
```

**Critic's additions: what a senior reviewer would still ask about this function.** *Why is "not found" a return value?* Because the agent must reason about it; an exception would be retried or turned into "the tool failed". *Where is the overall deadline?* The 5-second timeout is per attempt; three attempts plus backoff can take 25 seconds, so the caller wraps the tool in `asyncio.timeout()` with the request's remaining budget. *What bounds concurrency?* A semaphore per downstream (for example 20 in flight to the orders API) and a shared token bucket for the model provider's rate limit, otherwise `asyncio.gather` over 500 tool calls is a self-inflicted outage. *GET is idempotent — what about the write tools?* A `POST /refunds` tool takes an idempotency key derived from the run id and the arguments, the server stores key → response for 24 hours and replays the stored response on a retry, so a timeout after a successful write cannot refund twice. *What is logged?* Never the payload (PII); the ids, status, latency and trace id are enough to replay from stored inputs. Being able to give these five answers is the difference between "I know tenacity" and "I have run tools in production".

## 49.2 API design

- **REST** with FastAPI: resources and verbs, status codes, pagination, filtering, versioning (`/v1`), OpenAPI generated from Pydantic models, auth via OAuth2/JWT, rate limiting, idempotency keys on POST, async endpoints and background tasks; **long-running jobs**: `202 Accepted` + job id + polling or webhooks.
- **Streaming**: server-sent events or WebSockets for token streaming; chunked responses; backpressure.
- **gRPC** for internal high-throughput services; **GraphQL** when clients need flexible queries; **MCP** when the consumer is an agent (chapter 22).
- **Contracts and tests**: schema-first, contract tests, backward-compatible changes, deprecation policy.

Example: an agent service exposes `POST /runs` (returns run id), `GET /runs/{id}` (status, partial output, trace link), `POST /runs/{id}/approve` (HITL), and `GET /runs/{id}/events` (SSE stream).

**Critic's additions: API mechanics with numbers and trade-offs.**
- **SSE versus WebSockets.** SSE is one-directional, plain HTTP, works through most proxies and load balancers, reconnects with `Last-Event-ID` for free; WebSockets are bidirectional and needed only when the client sends mid-stream (voice, collaborative editing). Default to SSE for token streaming; send a keep-alive comment every 15–30 seconds so idle proxies do not cut the connection; persist partial output server-side so a reconnect resumes rather than restarts.
- **Idempotency keys.** Client sends `Idempotency-Key`; the server stores key → status and response in Redis with a 24-hour TTL; a repeat with the same key returns the stored response, a repeat while the first is in flight returns 409; keys are scoped per principal so one tenant cannot replay another's.
- **Pagination.** Cursor-based (opaque, stable under inserts) rather than offset-based (slow and inconsistent past a few thousand rows); page sizes capped (100) and returned in the response.
- **Timeouts and long jobs.** First token within 10 seconds, whole response within 60–120 seconds, anything longer becomes `202 Accepted` with a job id, polling with `Retry-After`, or a signed webhook; webhooks carry an HMAC signature and a timestamp, and receivers reject replays older than five minutes.
- **Errors.** One error shape (RFC 9457 problem details), with a stable machine-readable `type`, a trace id, and no stack traces; 4xx for the caller's mistakes, 5xx for yours, 429 with `Retry-After` for rate limits.
- **Versioning.** Additive changes without a version bump; breaking changes as `/v2` with the old version supported for a stated period (six months is common); OpenAPI generated from the code so the spec cannot drift.
- **MCP as an API.** When the consumer is an agent, the tool description is the contract and the enemy is ambiguity: one tool per intent, typed arguments with examples, explicit error values the model can act on, and read-only tools separated from tools with side effects so policies can differ.

## 49.3 Databases

- **Relational (Postgres)**: schema design and normalization, indexes (B-tree, composite order, partial, GIN for JSONB/full-text), query plans (`EXPLAIN ANALYZE`), transactions and isolation levels, locking, connection pooling (PgBouncer), migrations (Alembic), row-level security, pgvector for small vector workloads.
- **Key-value and document**: Redis (caching, rate limits, queues, semantic cache), DynamoDB/Cosmos DB (partition key design, single-table patterns), MongoDB.
- **Analytical**: columnar warehouses, partitioning, clustering, cost by bytes scanned (chapter 48).
- **Search and vectors**: chapter 18.
- **Patterns**: outbox for reliable events, CQRS where read and write shapes differ, soft deletes with retention, audit tables.

Example: the job-search agent's tracker as a Postgres table with a unique constraint on `(platform, job_id)`, an index on `(status, follow_up_date)`, and a view for the daily digest.

**Critic's additions: Postgres numbers and patterns for LLM services.**
- **Connections.** Postgres defaults to 100 connections and each one costs memory; an async service with 20 workers and a pool of 10 each is already 200. Put PgBouncer (transaction pooling) or the cloud equivalent in front, size application pools at roughly two to four times the core count of the database, and set `statement_timeout` so a runaway query cannot hold a connection forever.
- **pgvector limits.** With HNSW indexes pgvector is a sound choice up to the low millions of vectors per table (index build needs the index in memory — plan several gigabytes for a million 1024-dimension vectors — and filtered queries can lose recall when the filter is selective); beyond that, or when you need hybrid search with BM25 and faceting at scale, move to a dedicated engine (chapter 18). State the number and the reason, not "pgvector doesn't scale".
- **Outbox pattern.** Write the business row and an `outbox` row in the same transaction; a relay publishes outbox rows to the queue and marks them sent; consumers are idempotent. This is how "update the ticket and notify the agent" never half-happens.
- **Zero-downtime migrations.** Expand (add the nullable column, backfill in batches of 10k rows, add the index `CONCURRENTLY`), deploy code that writes both, switch reads, then contract (drop the old column) a release later. Never rename a column in one step on a table an agent tool reads.
- **Multi-tenancy.** Row-level security with a tenant id set per connection (`SET app.tenant_id`) is cheaper and safer than a schema per tenant up to thousands of tenants; the agent's tools inherit it automatically, which is the whole point.
- **Text-to-SQL safety.** A read-only role on views, `statement_timeout` of a few seconds, a row limit appended by code (not by the prompt), no access to system catalogs beyond what the semantic layer exposes, and query logging with the principal; generated SQL is parsed and allow-listed (SELECT only) before execution.

## 49.4 Distributed systems basics

Idempotency and at-least-once delivery; retries with backoff and jitter; timeouts and deadlines propagated through calls; circuit breakers and bulkheads; queues (SQS, Pub/Sub, RabbitMQ, Kafka) to decouple and absorb bursts; exactly-once as idempotent consumers; consistency models (strong vs eventual; read-your-writes); caching layers and invalidation; rate limiting (token bucket); leader election and locks (sparingly); the CAP/PACELC intuition; observability as the only way to debug any of it. For LLM apps: provider rate limits and outages are the common failure, so queue, throttle, fall back, and cache.

Example: a document-processing pipeline where each page is a message, workers are idempotent (results keyed by page hash), failures go to a dead-letter queue with alerts, and a reconciliation job re-queues missing pages nightly.

**Critic's additions: resilience defaults you can quote.**

| Mechanism | A sane default for an LLM service | Why |
|---|---|---|
| Timeouts | connect 2 s; tool call 5–10 s; model call: first token 10 s, total 60–120 s; whole request deadline propagated in a header | an unbounded call is a leaked worker |
| Retries | 3 attempts, exponential backoff from 1 s capped at 8–30 s, full jitter, only on transient errors, never on 4xx except 429 | retrying a 400 is a loop; retrying without jitter is a thundering herd |
| Retry budget | at most 10–20% of requests may be retries per minute per dependency | retries during an outage amplify it |
| Circuit breaker | open after 50% failures over the last 20 calls, half-open after 30 s, one probe | fail fast and fall back instead of queueing on a dead provider |
| Bulkheads | separate pools and semaphores per provider and per tool | one slow tool must not consume every worker |
| Rate limiting | token bucket per principal and a shared bucket per provider key, in Redis, sized to the provider's tokens-per-minute quota | the provider's 429s are your incident |
| Queues | visibility timeout greater than the maximum processing time; dead-letter after 3–5 attempts; alert on DLQ depth above 0 for ten minutes | at-least-once delivery means duplicates and stuck messages are normal |
| Idempotency | key = hash(run id, tool, arguments) stored with the result for 24 h | retries and replays become safe |
| Fallbacks | secondary model behind the gateway with the same eval score within tolerance; cached answer for identical requests; honest "try later" | availability above the single provider's SLA |

Example: a shared rate limiter for a provider's 2M-tokens-per-minute quota across 30 workers is a Redis token bucket refilled every second; each worker reserves the estimated input plus the `max_tokens` output before calling and returns the unused part after the response — without it, 30 workers each at "their share" still burst past the quota at the top of every minute.

## 49.5 Testing strategy

Unit tests for pure logic (parsers, tool argument validation, prompt builders), contract tests for schemas and APIs, integration tests with real dependencies in containers (Testcontainers), **eval suites** for model behaviour (chapter 32) separated from unit tests because they are slow and stochastic, load tests (k6, Locust) for latency under concurrency, security tests (dependency scans, injection suites), and smoke tests after deploy. Mock the model in unit tests (record/replay fixtures); never mock it in evals. Numbers to aim for: the unit suite runs in under a minute locally, the integration suite in under ten minutes in CI, the eval suite in under fifteen with a concurrency of twenty, and a load test proves the p95 at twice the expected peak before launch. Example: the refund tool has unit tests for argument validation (rejects an amount above the order total), a contract test against the payments API's recorded schema, an integration test with a sandbox account in a container, an eval case where the user claims a refund they are not owed, and a load test showing the approval queue holds at 50 concurrent runs.

## 49.6 Security basics every engineer must know

TLS everywhere; OAuth 2.1/OIDC for users and services (authorization code with PKCE, client credentials, on-behalf-of); JWT validation (issuer, audience, expiry, signature); least-privilege IAM; secrets in a vault with rotation; input validation and output encoding; SQL parameterization; dependency and container scanning; audit logging; the OWASP Top 10 (web; the 2025 edition replaced the 2021 list), the OWASP Top 10 for LLM Applications (the 2026 edition, posted in August 2026, replaced the 2025 list; chapter 30 has both orders) and, since December 2025, the separate OWASP Top 10 for Agentic Applications (published as the list "for 2026"); data classification and retention; threat modeling (STRIDE) for a new service.

**Critic's additions: the agent-specific security list.** The OWASP Top 10 for Agentic Applications for 2026 (published 9 December 2025, entries ASI01 to ASI10 in the order below) names the failures interviewers now ask about: agent goal hijack, tool misuse and exploitation, identity and privilege abuse, agentic supply-chain vulnerabilities, unexpected code execution, memory and context poisoning, insecure inter-agent communication, cascading failures, human–agent trust exploitation, and rogue agents. Two design rules compress most of it. The *lethal trifecta* (Simon Willison, 2025): an agent that has access to private data, is exposed to untrusted content, and can communicate externally can be made to exfiltrate — remove one leg per session. Meta's *Agents Rule of Two* (October 2025) states the same constraint operationally: within a session an agent should satisfy at most two of (A) processing untrustworthy inputs, (B) access to sensitive systems or private data, (C) changing state or communicating externally; if all three are needed, a human approves the step. Concrete controls that follow: tools that fetch URLs enforce an allow-list and block private address ranges and cloud metadata endpoints (SSRF through an agent is a 2026 classic); credentials are injected by the tool gateway, never placed in the prompt or returned in tool output; the agent acts as the user through on-behalf-of tokens so it cannot become a confused deputy with the service's broad permissions; tool descriptions from third-party MCP servers are pinned by hash and re-approved on change; logs are redacted before storage; and every write tool has an approval policy by action class (refund under \$50 automatic, above it human).

## 49.7 Git and collaboration

Trunk-based with short branches, meaningful commits, PRs with a description that states intent and testing, code review etiquette (ask questions, suggest, approve what you would run), semantic versioning and changelogs, ADRs (architecture decision records) for the decisions you will be asked about in a year, READMEs that let a stranger run the project in ten minutes.

## 49.8 Clean architecture for LLM services

Separate **domain logic** (what the agent does), **adapters** (model providers, vector stores, tools), and **delivery** (API, CLI, workers); make the model provider an interface so you can swap Claude/GPT/Gemini/open models in tests and in production; keep prompts as versioned files with tests; put evaluation next to the code it evaluates; log at boundaries; design for replay (every run reproducible from its inputs).

## 49.9 Example use cases

- **A FastAPI agent service** with async tool calls, SSE streaming, idempotent approvals, Postgres state, Redis rate limits, OTel tracing, pytest + promptfoo in CI, Docker + Helm, Argo CD deploy.
- **A document ingestion worker** on a queue with idempotent processing, dead-letter handling, Pydantic-validated outputs, and nightly reconciliation.
- **A tool gateway** that validates arguments, checks a policy engine, injects credentials from a vault, enforces timeouts and logs every call with the principal.
- **A migration** from synchronous LLM calls to a job queue when p95 crossed 20 s — the classic "scale an LLM service" story.

**Critic's additions: more use cases.**
- **The kill switch.** Every LLM feature sits behind a flag with three states (on, degraded to cached or deterministic behaviour, off); the on-call engineer can disable the agent in seconds without a deploy; the flag is tested monthly in a game day.
- **Webhook receiver for a payments provider.** Verifies the HMAC signature and timestamp, deduplicates by event id in Redis, writes to the outbox in the same transaction as the state change, returns 200 within a second, and processes asynchronously; replays from the provider are harmless.
- **Zero-downtime schema change on the tracker table.** Expand/contract over two releases while the agent keeps writing; the migration runs in batches with `lock_timeout` set so it cannot block production.
- **Log redaction pipeline.** Prompts and responses pass through a redaction step (regex plus a small NER model) before they reach the trace store; the raw payload lives for 24 hours in a restricted bucket for incident replay and is then deleted; access to it is logged.
- **A memory leak found by observability.** Worker RSS grows 50 MB an hour; the trace shows a per-request `httpx.AsyncClient` never closed; one shared client and a connection pool limit fix it, and a resource metric alert prevents the next one.
- **Rate-limited batch job.** 2M documents through a provider with a 1M-tokens-per-minute quota: a token-bucket limiter, a queue with checkpointed progress, the batch endpoint for the bulk and the online endpoint for retries; the job survives a worker restart without reprocessing.

**Interview line:** *"I write typed, validated, observable Python; every network call has a timeout, a retry policy and an idempotency key; the model provider is behind an interface; prompts are versioned and tested; and the service is designed to be replayed and rolled back."*
