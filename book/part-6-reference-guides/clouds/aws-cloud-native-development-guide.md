# AWS Cloud-Native Development — Complete Guide

> Covers every layer of building production services on AWS: compute, networking, storage, messaging, security, observability, and infrastructure as code. Emphasizes patterns for AI/LLM applications.

---

## Table of Contents

1. [What Cloud-Native Actually Means on AWS](#1-what-cloud-native-actually-means-on-aws)
2. [The AWS Service Map — What Goes Where](#2-the-aws-service-map--what-goes-where)
3. [Compute — Lambda vs ECS vs EKS](#3-compute--lambda-vs-ecs-vs-eks)
4. [Networking — VPC, Load Balancers, API Gateway](#4-networking--vpc-load-balancers-api-gateway)
5. [Storage — S3, DynamoDB, RDS, ElastiCache](#5-storage--s3-dynamodb-rds-elasticache)
6. [Messaging & Async — SQS, SNS, EventBridge, Step Functions](#6-messaging--async--sqs-sns-eventbridge-step-functions)
7. [Security — IAM, Cognito, KMS, Secrets Manager](#7-security--iam-cognito-kms-secrets-manager)
8. [Observability — CloudWatch, X-Ray, OpenTelemetry](#8-observability--cloudwatch-x-ray-opentelemetry)
9. [Infrastructure as Code — CDK, Terraform, CloudFormation](#9-infrastructure-as-code--cdk-terraform-cloudformation)
10. [AWS for AI/LLM Applications](#10-aws-for-aillm-applications)
11. [The Well-Architected Framework — The Six Pillars](#11-the-well-architected-framework--the-six-pillars)
12. [Reference Architectures](#12-reference-architectures)
13. [Cost Optimization](#13-cost-optimization)
14. [Environment Management](#14-environment-management)
15. [Anti-Patterns](#15-anti-patterns)
16. [Interview Talking Points](#16-interview-talking-points)

---

## 1. What Cloud-Native Actually Means on AWS

Cloud-native doesn't mean "runs in the cloud." It means the application is designed *for* the cloud — taking advantage of managed services, elastic scaling, and pay-per-use economics instead of fighting against them.

**The five properties of cloud-native on AWS**:

1. **Managed over self-managed**: use RDS instead of running Postgres on EC2; use SQS instead of running RabbitMQ; use Bedrock instead of hosting your own LLM
2. **Elastic**: scales up and down automatically based on demand, not pre-provisioned for peak
3. **Loosely coupled**: services communicate via APIs, queues, and events — not shared databases or in-process calls
4. **Observable**: every service emits structured logs, metrics, and traces; you can diagnose issues without SSH
5. **Infrastructure as code**: every resource is defined in Terraform, CDK, or CloudFormation — reproducible, version-controlled, reviewable

---

## 2. The AWS Service Map — What Goes Where

This maps concerns to AWS services. Memorize the default choices.

| Concern | AWS Service | When to use |
|---|---|---|
| **Container compute** | ECS Fargate | Default for containerized services |
| **Kubernetes** | EKS | When you need K8s specifically |
| **Serverless compute** | Lambda | Event-driven, short-lived (<15 min), bursty |
| **API layer** | API Gateway (REST/HTTP/WebSocket) | Public-facing APIs |
| **Internal load balancing** | ALB (Application Load Balancer) | Service-to-service routing |
| **CDN / edge** | CloudFront | Static assets, caching, TLS termination |
| **DNS** | Route 53 | Domain management, health-check routing |
| **Object storage** | S3 | Documents, embeddings, logs, model artifacts |
| **Relational database** | RDS (Aurora Postgres) | Structured data, transactions |
| **NoSQL / key-value** | DynamoDB | Session state, metadata, high-throughput key-value |
| **In-memory cache** | ElastiCache (Redis/Valkey) | Caching, rate limiting, session store |
| **Vector search** | OpenSearch Serverless | Embeddings, hybrid BM25+vector |
| **Message queue** | SQS | Decoupling, buffering, async work |
| **Pub-sub** | SNS | Fan-out to multiple consumers |
| **Event bus** | EventBridge | Event-driven architecture, cross-service events |
| **Workflow orchestration** | Step Functions | Multi-step workflows with retry/error handling |
| **LLM access** | Bedrock | Claude, Titan, Llama, Mistral — managed |
| **Auth** | Cognito | User authentication, JWT tokens |
| **Secrets** | Secrets Manager | API keys, database passwords |
| **Configuration** | Systems Manager Parameter Store | Feature flags, config values |
| **Encryption** | KMS | Key management, envelope encryption |
| **Container registry** | ECR | Docker image storage |
| **CI/CD** | CodePipeline + CodeBuild (or GitHub Actions) | Build and deploy automation |
| **Logging** | CloudWatch Logs | Centralized log aggregation |
| **Metrics** | CloudWatch Metrics | Custom and system metrics |
| **Tracing** | X-Ray or OpenTelemetry | Distributed tracing |
| **Alerting** | CloudWatch Alarms + SNS | Threshold-based alerts |

---

## 3. Compute — Lambda vs ECS vs EKS

This is the most common architectural decision and the one interviewers probe on.

### 3.1 AWS Lambda

**What**: serverless functions. You write code; AWS runs it when triggered. No servers to manage.

**Pricing**: per invocation + per millisecond of execution time. Zero cost when idle.

**Limits**: 15 minutes max execution, 10 GB memory, 250 MB deployment package (or 10 GB with container images), 1000 default concurrent executions.

**Best for**: event-driven workloads (S3 uploads, SQS messages, API Gateway requests), short-lived tasks, bursty traffic with long idle periods.

**Not great for**: long-running processes (agents, model inference >15 min), high-throughput steady-state workloads (ECS is cheaper at scale), workloads needing GPUs.

```python
# lambda_function.py
import json

def handler(event, context):
    query = event.get("queryStringParameters", {}).get("q", "")
    # process query...
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"answer": "...", "query": query}),
    }
```

**Cold starts**: first invocation after idle takes 100ms–2s. Mitigations: provisioned concurrency (keeps N instances warm), SnapStart (Java), or just accept the cold start for non-latency-sensitive workloads.

### 3.2 ECS Fargate

**What**: managed container orchestration. You define a Docker container, ECS runs it. Fargate means AWS manages the underlying servers.

**Pricing**: per vCPU-second + per GB-second of memory. You pay while containers are running.

**Best for**: long-running services (APIs, agents, workers), workloads that need consistent low latency, anything that exceeds Lambda's limits.

**Architecture**:

```
ECR (image registry)
  ↓
ECS Task Definition (container config: image, CPU, memory, env vars, ports)
  ↓
ECS Service (desired count, scaling rules, load balancer attachment)
  ↓
ECS Cluster (logical grouping)
  ↓
Fargate (serverless capacity — no EC2 to manage)
```

**Task Definition example** (Terraform):

```hcl
resource "aws_ecs_task_definition" "agent_service" {
  family                   = "agent-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024    # 1 vCPU
  memory                   = 2048    # 2 GB
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.agent_service_task.arn

  container_definitions = jsonencode([{
    name      = "agent-service"
    image     = "${aws_ecr_repository.agent.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENV", value = "production" },
      { name = "AWS_REGION", value = "eu-central-1" },
    ]

    secrets = [
      {
        name      = "ANTHROPIC_API_KEY"
        valueFrom = aws_secretsmanager_secret.anthropic_key.arn
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/agent-service"
        "awslogs-region"        = "eu-central-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}
```

**Auto-scaling**:

```hcl
resource "aws_appautoscaling_target" "agent" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.agent.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-target-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.agent.resource_id
  scalable_dimension = aws_appautoscaling_target.agent.scalable_dimension
  service_namespace  = aws_appautoscaling_target.agent.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 60.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

### 3.3 EKS (Elastic Kubernetes Service)

**What**: managed Kubernetes. AWS runs the control plane; you manage worker nodes (or use Fargate profiles for serverless pods).

**When to use**: when you need Kubernetes features (Helm charts, custom operators, service mesh, GitOps with ArgoCD), multi-cloud portability, or the team already knows K8s.

**When not to use**: if ECS Fargate covers your needs. EKS adds significant operational complexity (node groups, RBAC, ingress controllers, cluster upgrades). Don't adopt K8s for a 3-service stack.

### 3.4 Decision Matrix

| Factor | Lambda | ECS Fargate | EKS |
|---|---|---|---|
| Operational overhead | Lowest | Low | Medium-high |
| Startup latency | Cold starts (100ms–2s) | None (already running) | None |
| Max execution | 15 minutes | Unlimited | Unlimited |
| Pricing model | Per-invocation | Per-container-second | Per-node + control plane |
| Idle cost | Zero | Container always running | Cluster always running |
| Scaling speed | Instant (to concurrency limit) | Minutes (new tasks) | Minutes (new pods/nodes) |
| GPU support | No | No (EC2 launch type yes) | Yes |
| Best for | Event-driven, bursty, short tasks | Long-running APIs, agents, workers | Complex multi-service, K8s ecosystem |

**For AI/LLM agent services**: ECS Fargate is the default. Agent workflows run 10+ seconds, need consistent low latency, and benefit from always-warm containers. Lambda for lightweight triggers (S3 event → start processing).

---

## 4. Networking — VPC, Load Balancers, API Gateway

### 4.1 VPC (Virtual Private Cloud)

Every AWS deployment lives in a VPC — your private network in AWS.

**Standard layout**:

```
VPC: 10.0.0.0/16
├── Public subnets (10.0.1.0/24, 10.0.2.0/24)  — ALB, NAT Gateway
│   └── Internet Gateway attached
├── Private subnets (10.0.3.0/24, 10.0.4.0/24)  — ECS tasks, RDS, ElastiCache
│   └── NAT Gateway for outbound internet (LLM API calls)
└── Isolated subnets (10.0.5.0/24, 10.0.6.0/24)  — no internet access
    └── RDS in strictest isolation (optional)
```

**Key concepts**:
- **Public subnet**: has a route to an Internet Gateway. Resources get public IPs.
- **Private subnet**: no direct internet access. Outbound via NAT Gateway.
- **Security Groups**: stateful firewalls per resource. Default: deny all inbound, allow all outbound.
- **NACLs**: stateless subnet-level firewalls. Usually left at defaults.
- **VPC Endpoints**: private connections to AWS services (S3, DynamoDB, Bedrock) without going through the internet. Cheaper and lower-latency.

**Always use at least two Availability Zones** for high availability. Put subnets in each AZ.

### 4.2 Application Load Balancer (ALB)

Routes HTTP/HTTPS traffic to your ECS tasks.

```
Internet → CloudFront → ALB (public subnet) → ECS tasks (private subnet)
```

Features: path-based routing (`/api/*` → service A, `/admin/*` → service B), host-based routing, WebSocket support, integration with Cognito for auth, integration with WAF for protection.

### 4.3 API Gateway

**REST API**: full-featured, request/response transformation, API keys, usage plans, caching. More expensive per request.

**HTTP API**: lightweight, faster, cheaper. Supports Lambda and HTTP backends. Sufficient for most use cases.

**WebSocket API**: persistent bidirectional connections. Use for streaming LLM responses to clients.

**When to use API Gateway vs ALB**:
- API Gateway: public-facing, need rate limiting, API keys, request validation, or WebSocket
- ALB: internal service-to-service, simpler routing, lower cost at high volume

### 4.4 CloudFront

CDN for static assets and API caching. Put it in front of your ALB for TLS termination at the edge, DDoS protection (Shield Standard included), and caching of static responses.

### 4.5 Route 53

DNS management. Health-check-based routing for failover between regions. Latency-based routing to direct users to the nearest region.

---

## 5. Storage — S3, DynamoDB, RDS, ElastiCache

### 5.1 Amazon S3

**What**: object storage. Unlimited capacity, 99.999999999% (11 nines) durability.

**Use for**: documents (PDFs, contracts), pre-computed embeddings, LLM prompt/completion logs, model artifacts, Terraform state, deployment artifacts.

**Key features**:
- **Lifecycle rules**: move old objects to cheaper tiers (S3 → S3-IA → Glacier)
- **Versioning**: keep every version of every object
- **Server-side encryption**: SSE-S3 (free), SSE-KMS (auditable, per-key)
- **Event notifications**: trigger Lambda on upload (`s3:ObjectCreated:*`)
- **Pre-signed URLs**: give temporary access to a specific object without making it public

```python
import boto3

s3 = boto3.client('s3')

# Upload
s3.upload_file('document.pdf', 'my-bucket', 'documents/doc-001.pdf')

# Generate pre-signed URL (expires in 1 hour)
url = s3.generate_presigned_url('get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'documents/doc-001.pdf'},
    ExpiresIn=3600)
```

### 5.2 DynamoDB

**What**: fully managed NoSQL key-value and document database. Single-digit millisecond latency at any scale.

**Use for**: session state, agent workflow state, metadata, user profiles, rate limiting counters.

**Key concepts**:
- **Partition key**: determines which partition stores the item. Must be high-cardinality.
- **Sort key**: optional second key for range queries within a partition.
- **GSI (Global Secondary Index)**: query by a different key pattern. Eventual consistency.
- **TTL**: auto-delete items after a timestamp. Perfect for session state.
- **On-demand vs provisioned**: on-demand for unpredictable traffic; provisioned for steady-state.
- **Conditional writes**: optimistic locking (`PutItem` only if version matches).
- **DynamoDB Streams**: CDC (change data capture) — trigger Lambda on item changes.

**Table design for agent sessions**:

```
Table: agent_sessions
  Partition key: session_id (String)
  Sort key: step_number (Number)
  Attributes: state (Map), created_at (Number), ttl (Number)

  TTL attribute: ttl (auto-delete sessions after 24 hours)

  GSI: user_id-index
    Partition key: user_id
    Sort key: created_at
    (Query: "get all sessions for user X, ordered by time")
```

```python
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('agent_sessions')

# Write session state
table.put_item(Item={
    'session_id': 'sess-abc123',
    'step_number': 3,
    'state': {'query': '...', 'chunks': [...], 'draft': '...'},
    'user_id': 'user-xyz',
    'created_at': int(datetime.now().timestamp()),
    'ttl': int((datetime.now() + timedelta(hours=24)).timestamp()),
})

# Read session state
response = table.get_item(Key={
    'session_id': 'sess-abc123',
    'step_number': 3,
})
state = response['Item']['state']
```

### 5.3 RDS (Aurora PostgreSQL)

**What**: managed relational database. Aurora is AWS's enhanced Postgres/MySQL — faster, more available, auto-scaling storage.

**Use for**: structured business data, user accounts, billing, anything needing transactions and complex queries.

**With pgvector**: Aurora Postgres supports the pgvector extension for vector similarity search. This lets you co-locate structured data and embeddings in one database — great for smaller-scale RAG where operational simplicity beats dedicated vector DB performance.

```sql
-- Enable pgvector
CREATE EXTENSION vector;

-- Create table with embedding column
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    chunk_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimensions
    metadata JSONB
);

-- Create HNSW index for fast similarity search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Query: find similar chunks
SELECT chunk_text, 1 - (embedding <=> $1::vector) AS similarity
FROM document_chunks
WHERE document_id = ANY($2)
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

### 5.4 ElastiCache (Redis / Valkey)

**What**: managed in-memory cache. Sub-millisecond latency.

**Use for**: query result caching (exact-match cache for repeated queries), embedding caching (don't re-embed the same text), session state (alternative to DynamoDB for short-lived state), rate limiting (token-bucket per user), real-time leaderboards, pub-sub.

```python
import redis
import json
import hashlib

r = redis.Redis(host='cache.abc123.eu-central-1.cache.amazonaws.com', port=6379)

def cached_query(query: str, retriever, ttl=900):
    cache_key = f"query:{hashlib.sha256(query.encode()).hexdigest()}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    result = retriever.run(query)  # expensive LLM + retrieval
    r.setex(cache_key, ttl, json.dumps(result))
    return result
```

### 5.5 OpenSearch Serverless

**What**: managed search and vector database. Supports both BM25 keyword search and k-NN vector search in the same index.

**Use for**: the retrieval layer of RAG systems. Hybrid search (dense + sparse) without managing separate vector and keyword indexes.

**Why over standalone vector DBs**: if you're already on AWS and need hybrid search, OpenSearch Serverless gives you BM25 + k-NN + metadata filtering in one managed service. Trade-off: less fine-grained control than Pinecone or self-hosted FAISS.

---

## 6. Messaging & Async — SQS, SNS, EventBridge, Step Functions

### 6.1 SQS (Simple Queue Service)

**What**: fully managed message queue. Decouples producers and consumers.

**Two flavors**:
- **Standard**: at-least-once delivery, best-effort ordering. Near-unlimited throughput.
- **FIFO**: exactly-once processing, strict ordering. 3000 messages/sec with batching.

**Use for**: decoupling API from heavy processing (user sends request → SQS → worker processes), buffering bursts, retry with backoff (failed messages go to dead-letter queue).

**Pattern for agent workloads**:

```
User API request → Lambda puts message on SQS → ECS worker reads SQS
   → Worker runs agent loop (could take 30+ seconds)
   → Worker writes result to DynamoDB
   → User polls /status/{job_id} or gets WebSocket notification
```

**Dead-letter queue (DLQ)**: messages that fail processing N times automatically move to a separate queue for investigation. Always configure a DLQ.

### 6.2 SNS (Simple Notification Service)

**What**: pub-sub. One message, multiple subscribers (Lambda, SQS, HTTP, email, SMS).

**Use for**: fan-out (one event triggers multiple services), notifications, alerting.

**Pattern**: `EventBridge → SNS → [SQS queue A, SQS queue B, Lambda C]`

### 6.3 EventBridge

**What**: serverless event bus. The backbone of event-driven architecture on AWS.

**Use for**: cross-service events (order.placed, document.processed, model.deployed), scheduled events (cron), AWS service events (EC2 state change, S3 events via CloudTrail).

**Why over SNS**: EventBridge has content-based filtering (route events by their content, not just topic), schema registry, archive/replay, and integration with 30+ AWS services as sources.

```json
// EventBridge rule: route document-processed events to the indexing service
{
  "source": ["document-service"],
  "detail-type": ["document.processed"],
  "detail": {
    "status": ["success"],
    "document_type": ["contract", "policy"]
  }
}
```

### 6.4 Step Functions

**What**: managed workflow orchestration. Visual state machine with retry, error handling, branching, parallel execution, and human approval steps.

**Use for**: multi-step agent workflows where you want durability and visibility without writing your own state machine.

**Standard vs Express**:
- **Standard**: up to 1 year execution, exactly-once, \$0.025 per 1000 state transitions. For long-running workflows.
- **Express**: up to 5 minutes, at-least-once, \$1 per million executions. For high-volume short workflows.

**Example: document processing pipeline**:

```json
{
  "StartAt": "ExtractText",
  "States": {
    "ExtractText": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:extract-text",
      "Retry": [{"ErrorEquals": ["States.TaskFailed"], "MaxAttempts": 3}],
      "Next": "ChunkDocument"
    },
    "ChunkDocument": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:chunk-document",
      "Next": "ParallelProcessing"
    },
    "ParallelProcessing": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "GenerateEmbeddings",
          "States": {
            "GenerateEmbeddings": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:embed-chunks",
              "End": true
            }
          }
        },
        {
          "StartAt": "ExtractEntities",
          "States": {
            "ExtractEntities": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:extract-entities",
              "End": true
            }
          }
        }
      ],
      "Next": "IndexResults"
    },
    "IndexResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:index-to-opensearch",
      "End": true
    }
  }
}
```

### 6.5 When to Use Which

| Pattern | Service |
|---|---|
| Decouple producer from consumer | SQS |
| One event → many consumers | SNS (or EventBridge) |
| Cross-service event routing with filtering | EventBridge |
| Multi-step workflow with retry and error handling | Step Functions |
| Scheduled job (cron) | EventBridge Scheduler |
| Simple async processing | SQS + Lambda |
| Complex async with branching and human approval | Step Functions |

---

## 7. Security — IAM, Cognito, KMS, Secrets Manager

### 7.1 IAM — The Foundation

IAM is the most important AWS service to understand deeply. Every request to every AWS service is authorized by IAM.

**Core principle: least privilege.** Every service, every Lambda, every ECS task gets its own IAM role with only the permissions it needs.

**Anatomy of an IAM policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:eu-central-1::foundation-model/anthropic.claude-*"
      ]
    },
    {
      "Sid": "AllowS3ReadDocuments",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::my-documents-bucket/*"]
    },
    {
      "Sid": "DenyS3Delete",
      "Effect": "Deny",
      "Action": ["s3:DeleteObject", "s3:DeleteBucket"],
      "Resource": ["*"]
    }
  ]
}
```

**IAM roles for ECS**:
- **Execution role**: lets ECS pull the container image from ECR and write logs to CloudWatch. Needed to *start* the task.
- **Task role**: lets the running container access AWS services (S3, DynamoDB, Bedrock, Secrets Manager). This is where least-privilege matters most.

**Common IAM mistakes**:
- `Action: "*"` on `Resource: "*"` — never acceptable
- Using IAM users with long-lived access keys instead of IAM roles
- Same role for dev and production — separate roles, separate accounts
- Not using conditions (time-based, IP-based, MFA-required)

### 7.2 Cognito

**What**: managed user authentication. User pools (username/password, social login, MFA) + identity pools (federated access to AWS resources).

**Use for**: authenticating end users of your agent system. Cognito issues JWT tokens; your API validates them.

**Flow**:

```
User → Cognito login → JWT token → API Gateway (validates JWT) → ECS
```

### 7.3 Secrets Manager

**What**: managed secret storage with automatic rotation.

**Use for**: API keys (Anthropic, OpenAI), database passwords, third-party credentials.

**Access from code**:

```python
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
anthropic_key = get_secret("prod/anthropic-api-key")["api_key"]
```

**In ECS task definitions**: inject secrets directly from Secrets Manager into container environment variables — the container never sees the secret ARN, just the value.

### 7.4 KMS (Key Management Service)

**What**: managed encryption keys. Envelope encryption for data at rest.

**Use for**: encrypting S3 buckets, DynamoDB tables, SQS queues, EBS volumes, RDS instances. Also for customer-managed keys when you need audit trails of who decrypted what.

**Best practice**: use AWS-managed keys (`aws/s3`, `aws/dynamodb`) unless you need customer-managed keys for compliance. CMKs give you CloudTrail audit of every decrypt operation.

### 7.5 WAF (Web Application Firewall)

**What**: layer-7 firewall for API Gateway, ALB, and CloudFront.

**Use for**: rate limiting per IP, blocking known-bad IPs, SQL injection protection, bot detection. Attach to your public-facing API.

### 7.6 VPC Endpoints

**What**: private connections from your VPC to AWS services. Traffic stays on the AWS backbone network, never touches the public internet.

**Use for**: S3, DynamoDB, Bedrock, Secrets Manager, SQS, CloudWatch, ECR. Cheaper than NAT Gateway for AWS-to-AWS traffic, and more secure.

**Two types**:
- **Gateway endpoints** (free): S3, DynamoDB only
- **Interface endpoints** (\$0.01/hr + data): everything else (Bedrock, Secrets Manager, etc.)

---

## 8. Observability — CloudWatch, X-Ray, OpenTelemetry

### 8.1 CloudWatch Logs

Centralized logging. Every ECS task, Lambda, and API Gateway automatically sends logs here.

**Structured logging** (always use JSON):

```python
import structlog
import json

logger = structlog.get_logger()

logger.info("retrieval_completed",
    correlation_id="req-abc123",
    query="refund policy",
    chunks_retrieved=5,
    latency_ms=230,
    cache_hit=False,
)
```

**Log Insights** query language:

```
fields @timestamp, @message
| filter correlation_id = "req-abc123"
| sort @timestamp asc
| limit 100
```

**Retention**: set retention policies (30 days for dev, 90 days for prod, archive to S3 after).

### 8.2 CloudWatch Metrics

**Custom metrics** for agent systems:

```python
import boto3

cw = boto3.client('cloudwatch')

cw.put_metric_data(
    Namespace='AgentService',
    MetricData=[
        {
            'MetricName': 'LLMLatencyMs',
            'Value': 2340,
            'Unit': 'Milliseconds',
            'Dimensions': [
                {'Name': 'Model', 'Value': 'claude-sonnet-4-6'},
                {'Name': 'AgentStep', 'Value': 'drafting'},
            ],
        },
        {
            'MetricName': 'TokensUsed',
            'Value': 4500,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Direction', 'Value': 'output'},
            ],
        },
    ]
)
```

**Key metrics to track**: request latency (p50/p95/p99), error rate by type, tokens per request, \$ per request, cache hit rate, queue depth, active tasks.

### 8.3 CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "agent-service-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5xxErrorRate"
  namespace           = "AgentService"
  period              = 60
  statistic           = "Average"
  threshold           = 5  # 5% error rate

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}
```

### 8.4 X-Ray (Distributed Tracing)

Traces requests across services: API Gateway → Lambda → DynamoDB → Bedrock.

```python
from aws_xray_sdk.core import xray_recorder, patch_all

patch_all()  # auto-instrument boto3, requests, etc.

@xray_recorder.capture('process_query')
def process_query(query: str):
    with xray_recorder.in_subsegment('retrieval') as subsegment:
        chunks = retrieve(query)
        subsegment.put_annotation('chunks_count', len(chunks))

    with xray_recorder.in_subsegment('llm_call') as subsegment:
        answer = generate(query, chunks)
        subsegment.put_annotation('tokens', answer.usage.total_tokens)

    return answer
```

### 8.5 OpenTelemetry (OTEL)

The vendor-neutral alternative to X-Ray. Use OTEL if you want portability or plan to use Datadog, Grafana, or Jaeger alongside AWS. AWS Distro for OpenTelemetry (ADOT) bridges OTEL → X-Ray.

---

## 9. Infrastructure as Code — CDK, Terraform, CloudFormation

### 9.1 Terraform

**The de facto standard.** HCL language. Provider-agnostic (AWS, GCP, Azure, Kubernetes, Datadog).

**Workflow**: `init` → `plan` → `apply`.

```hcl
# main.tf
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "prod/agent-service/terraform.tfstate"
    region = "eu-central-1"
    dynamodb_table = "terraform-locks"  # state locking
    encrypt = true
  }
}

provider "aws" {
  region = "eu-central-1"
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "agent-service"
      ManagedBy   = "terraform"
    }
  }
}
```

**State management**: remote state in S3 with DynamoDB locking. Never commit state files to Git (they contain secrets).

### 9.2 AWS CDK (Cloud Development Kit)

**What**: write IaC in Python, TypeScript, Java, Go. CDK synthesizes to CloudFormation.

**Advantage over Terraform**: you use a real programming language (loops, conditionals, abstractions), and higher-level constructs (L2 constructs) reduce boilerplate.

```python
# cdk_stack.py
from aws_cdk import (
    Stack, Duration, RemovalPolicy,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
)
from constructs import Construct

class AgentServiceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, "VPC", max_azs=2)

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "AgentService",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=2,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repo, tag="latest"),
                container_port=8000,
            ),
            public_load_balancer=True,
        )

        # Auto-scaling
        scaling = service.service.auto_scale_task_count(min_capacity=2, max_capacity=10)
        scaling.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=60,
            scale_in_cooldown=Duration.seconds(300),
        )
```

### 9.3 When to Use Which

| Factor | Terraform | CDK | CloudFormation |
|---|---|---|---|
| Language | HCL | Python/TS/Java/Go | YAML/JSON |
| Multi-cloud | Yes | AWS only | AWS only |
| Abstraction level | Low (explicit) | High (L2 constructs) | Low (explicit) |
| Learning curve | Medium | Low (if you know Python) | High (verbose YAML) |
| State management | S3 + DynamoDB | CloudFormation (managed) | CloudFormation (managed) |
| Community modules | Huge (Terraform Registry) | Growing (Construct Hub) | Limited |
| Best for | Multi-cloud, large teams, mature orgs | AWS-only, Python teams, rapid prototyping | AWS-native, simple stacks |

**Default recommendation**: Terraform if multi-cloud or team already knows it. CDK if AWS-only and team prefers Python. CloudFormation rarely directly — it's the compilation target for CDK.

---

## 10. AWS for AI/LLM Applications

### 10.1 Amazon Bedrock

**What**: managed access to foundation models (Claude, Titan, Llama, Mistral, Cohere) via a unified API. No infrastructure to manage.

**Key features**:
- **Model access**: Claude Opus 4.7, Claude Sonnet 4.6, Claude Haiku 4.5, Llama 3+, Titan
- **Knowledge Bases**: managed RAG with S3 data sources and OpenSearch vector store
- **Agents**: managed agent workflows with tool use
- **Guardrails**: content filtering, PII redaction, topic denial
- **Model evaluation**: built-in evaluation jobs
- **Fine-tuning**: custom model training on your data
- **Prompt caching**: cache system prompts across requests (lower cost)

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

response = bedrock.invoke_model(
    modelId='anthropic.claude-sonnet-4-6-20250514-v1:0',
    contentType='application/json',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": "What is our refund policy?"}
        ],
        "system": "You are a helpful assistant. Cite your sources.",
    }),
)

result = json.loads(response['body'].read())
answer = result['content'][0]['text']
```

**Why Bedrock over direct API**: data stays in your VPC (via VPC endpoint), IAM-based access control, CloudTrail audit, no API key management, consolidated billing.

### 10.2 Full AI Stack on AWS

```
┌─────────────────────────────────────────────────────────┐
│                     CloudFront + WAF                     │
│                     (CDN, DDoS, rate limit)              │
└────────────────────────────┬────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│              API Gateway (WebSocket + REST)              │
│              + Cognito authorizer                        │
└────────────────────────────┬────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│                    ECS Fargate Cluster                   │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Agent API   │  │  Worker      │  │  Ingestion   │  │
│  │  (FastAPI)   │  │  (SQS cons.) │  │  (S3 events) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
└─────────┼─────────────────┼─────────────────┼───────────┘
          │                 │                 │
    ┌─────┴─────┐     ┌────┴────┐      ┌────┴────┐
    │ Bedrock   │     │DynamoDB │      │   S3    │
    │ (Claude)  │     │(state)  │      │ (docs)  │
    └───────────┘     └─────────┘      └─────────┘
          │                                 │
    ┌─────┴──────────────────────┐    ┌────┴────────┐
    │   OpenSearch Serverless    │    │ ElastiCache  │
    │   (vectors + BM25)         │    │ (Redis cache)│
    └────────────────────────────┘    └─────────────┘

    Observability: CloudWatch Logs + Metrics + X-Ray
    Secrets: Secrets Manager
    IaC: Terraform or CDK
    CI/CD: GitHub Actions → ECR → ECS
```

---

## 11. The Well-Architected Framework — The Six Pillars

AWS's official framework for evaluating architectures. Know these for interviews.

### Pillar 1: Operational Excellence
- Automate everything (IaC, CI/CD, runbooks)
- Make frequent, small, reversible changes
- Anticipate failure and practice recovery
- Learn from operational events (post-mortems)

### Pillar 2: Security
- Implement least-privilege IAM
- Enable traceability (CloudTrail, VPC Flow Logs)
- Apply security at all layers (WAF, security groups, NACLs, encryption)
- Automate security best practices (Config Rules, GuardDuty)
- Protect data in transit (TLS) and at rest (KMS)

### Pillar 3: Reliability
- Automatically recover from failure (health checks, auto-scaling)
- Test recovery procedures (chaos engineering, game days)
- Scale horizontally (multiple AZs, multiple regions)
- Manage change through automation (no manual changes)

### Pillar 4: Performance Efficiency
- Use the right service for the workload (Lambda vs ECS vs EKS)
- Go global in minutes (CloudFront, multi-region)
- Experiment more often (easy to spin up test environments)
- Use serverless where possible

### Pillar 5: Cost Optimization
- Right-size resources (don't over-provision)
- Use savings plans / reserved instances for baseline
- Use spot / Fargate Spot for non-critical workloads
- Monitor and attribute costs (Cost Explorer, tags)

### Pillar 6: Sustainability
- Optimize utilization (right-size, auto-scale to zero when possible)
- Choose efficient architectures (serverless, managed services)
- Minimize data movement (process data close to storage)

---

## 12. Reference Architectures

### 12.1 Synchronous Agent API

```
Client → API Gateway → ALB → ECS (agent loop) → Bedrock + OpenSearch + DynamoDB → response
```

Latency target: <5 seconds. Use for simple queries where the agent can complete in one shot.

### 12.2 Async Agent with Streaming

```
Client → API GW (WebSocket) → Lambda (queue job to SQS, return job_id)
                                    ↓
                            ECS worker reads SQS
                                    ↓
                            Worker runs agent loop
                            (Bedrock + OpenSearch + DynamoDB)
                                    ↓
                            Worker streams tokens via WebSocket
                                    ↓
                            Worker writes final result to DynamoDB
```

For multi-step agent workflows that take 10–60 seconds.

### 12.3 Document Ingestion Pipeline

```
User uploads PDF → S3 → S3 Event → EventBridge → Step Functions
                                                       ↓
                                            ┌──────────┴──────────┐
                                            ↓                     ↓
                                      Lambda: extract        Lambda: OCR
                                      text (PyMuPDF)        (Textract fallback)
                                            ↓                     ↓
                                            └──────────┬──────────┘
                                                       ↓
                                            Lambda: chunk + embed
                                                       ↓
                                            ┌──────────┴──────────┐
                                            ↓                     ↓
                                    OpenSearch              DynamoDB
                                    (index chunks)        (metadata)
                                            ↓                     ↓
                                            └──────────┬──────────┘
                                                       ↓
                                              EventBridge: "document.indexed"
```

---

## 13. Cost Optimization

### 13.1 The Cost Stack for AI Applications

Rank-ordered by typical impact:

1. **LLM API costs** (often 60–80% of total): model routing, prompt caching, output token caps, caching at the application layer
2. **Compute (ECS/Lambda)**: right-size task definitions, use Fargate Spot for non-critical workers (70% cheaper), scale to zero in dev
3. **Data transfer**: VPC endpoints eliminate NAT Gateway charges for AWS-to-AWS traffic. NAT Gateway data processing is \$0.045/GB — adds up fast
4. **Storage**: S3 lifecycle rules (IA at 30 days, Glacier at 90), DynamoDB on-demand vs provisioned, ElastiCache sizing
5. **OpenSearch**: serverless OCU pricing can spike under load; monitor and right-size

### 13.2 Tagging Strategy

Tag every resource so you can attribute costs:

```hcl
default_tags {
  tags = {
    Environment = "production"
    Team        = "ai-platform"
    Service     = "agent-service"
    CostCenter  = "engineering"
    ManagedBy   = "terraform"
  }
}
```

Use AWS Cost Explorer and Cost Anomaly Detection to track spending by tag.

### 13.3 Savings Plans

For steady-state workloads: Compute Savings Plans (1 or 3 year commitment) save 30–60% on Fargate and Lambda. Don't commit until your baseline is stable.

---

## 14. Environment Management

### 14.1 The Three-Account Pattern

Best practice for production AWS:

```
┌──────────────────────────────────────────────┐
│              AWS Organizations               │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Dev     │  │ Staging  │  │ Production│  │
│  │  Account  │  │  Account │  │  Account  │  │
│  │           │  │          │  │           │  │
│  │ 123456789 │  │ 234567890│  │ 345678901│  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                              │
│  ┌──────────┐                                │
│  │ Shared   │ ← ECR, Terraform state,       │
│  │ Services │   CI/CD roles, DNS             │
│  └──────────┘                                │
└──────────────────────────────────────────────┘
```

**Why separate accounts**: blast radius isolation (a dev mistake can't touch production), separate billing, separate IAM (no accidental cross-environment access), compliance boundaries.

**Cross-account access**: IAM roles with `sts:AssumeRole`. CI/CD pipeline assumes a role in the target account.

### 14.2 Environment Parity

Same Terraform modules, different variables:

```
infra/
  modules/
    agent-service/     # shared module
      main.tf
      variables.tf
  environments/
    dev/
      main.tf          # module "agent" { source = "../../modules/agent-service" }
      terraform.tfvars  # instance_count = 1, instance_size = "small"
    staging/
      main.tf
      terraform.tfvars  # instance_count = 2, instance_size = "medium"
    production/
      main.tf
      terraform.tfvars  # instance_count = 4, instance_size = "large"
```

### 14.3 Feature Flags

Use AWS AppConfig or LaunchDarkly to control feature rollout without redeploying:

```python
import boto3

appconfig = boto3.client('appconfigdata')

# Start session
session = appconfig.start_configuration_session(
    ApplicationIdentifier="agent-service",
    EnvironmentIdentifier="production",
    ConfigurationProfileIdentifier="feature-flags",
)

# Get current flags
config = appconfig.get_latest_configuration(
    ConfigurationToken=session['InitialConfigurationToken']
)

flags = json.loads(config['Configuration'].read())
if flags.get("use_new_prompt_v3", False):
    prompt = load_prompt("rag_answer", version="v3")
else:
    prompt = load_prompt("rag_answer", version="v2")
```

---

## 15. Anti-Patterns

**1. Running everything on EC2.** If you're managing OS patches, security groups, and auto-scaling groups for every service, you're not cloud-native — you're running a data center in someone else's building.

**2. One giant IAM role for everything.** "It works if I give it `AdministratorAccess`." Yes, and it also works for an attacker.

**3. No VPC endpoints.** All your S3, DynamoDB, and Bedrock traffic routing through a NAT Gateway at \$0.045/GB adds up fast and adds latency.

**4. Storing secrets in environment variables in task definitions.** Use Secrets Manager references.

**5. No auto-scaling.** Running 10 ECS tasks 24/7 because you sized for peak. Use target-tracking scaling.

**6. No DLQ on SQS queues.** Failed messages vanish silently. Always configure a dead-letter queue.

**7. CloudWatch Logs with no retention policy.** Default is "keep forever." At \$0.50/GB-month for ingestion + \$0.03/GB-month for storage, this adds up over years.

**8. Single-AZ deployments.** One AZ goes down (it happens), your service goes down.

**9. Not using IaC.** "I'll just click through the console." Six months later, nobody knows what's deployed or why.

**10. Over-engineering on day one.** Multi-region active-active with global DynamoDB tables and cross-region replication for a service with 100 users. Start simple. Add complexity when metrics justify it.

---

## 16. Interview Talking Points

### "How would you deploy an agent service on AWS?"

> "ECS Fargate for the agent API — agent workflows can run 10+ seconds, which rules out Lambda for the main path. The API sits behind an ALB in private subnets, with API Gateway (WebSocket) in front for streaming responses to clients. Bedrock for Claude access via VPC endpoint so traffic stays private. OpenSearch Serverless for hybrid retrieval. DynamoDB for session state with TTL. ElastiCache for query caching. Secrets Manager for API keys, injected into the task definition. Auto-scaling on CPU utilization at 60% target.
>
> For async workloads — document ingestion, long-running research — SQS queue with ECS workers, or Step Functions if the workflow has branching and retry requirements."

### "How do you handle security?"

> "Four layers. Network: private subnets, security groups scoped per service, VPC endpoints for all AWS service traffic. Identity: every ECS task has its own IAM role with least-privilege policies — the agent service can invoke Bedrock and read S3 but can't delete anything. Secrets: Secrets Manager with automatic rotation, injected at runtime, never in code or env vars. Data: KMS encryption at rest for S3, DynamoDB, and OpenSearch; TLS everywhere in transit. Monitoring: CloudTrail for API audit, GuardDuty for threat detection, Config Rules for compliance drift."

### "How do you manage multiple environments?"

> "Separate AWS accounts via AWS Organizations — dev, staging, production, and a shared-services account for ECR and Terraform state. Same Terraform modules across all environments, different variable files for sizing. CI/CD pipeline uses OIDC to assume environment-specific IAM roles. Branch protection ensures only main deploys to staging and production. Feature flags via AppConfig for runtime control without redeployment."

### "How do you optimize costs?"

> "LLM API cost is the dominant line item — typically 60–80% of total spend for an agent service. The levers there are model routing (Haiku for simple queries, Opus for complex), prompt caching, output token caps, and application-level caching in Redis. Infrastructure costs: VPC endpoints to eliminate NAT Gateway data processing charges, Fargate Spot for non-critical workers (70% cheaper), DynamoDB on-demand mode for unpredictable traffic, S3 lifecycle rules. Everything tagged by team and service for cost attribution. Cost Anomaly Detection alerts if any line item spikes 2× baseline."

### "What's the difference between Lambda and ECS Fargate?"

> "Lambda is per-invocation, zero idle cost, instant scaling, but capped at 15 minutes and has cold starts. Fargate is per-container-second, always-running, no cold starts, unlimited execution time. For agent workloads I default to Fargate — agent loops run 10+ seconds, need consistent latency, and benefit from warm containers. Lambda for event-driven triggers (S3 upload → start processing) and lightweight API endpoints."
