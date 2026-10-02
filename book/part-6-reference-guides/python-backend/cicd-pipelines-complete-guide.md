# CI/CD Pipelines — Complete Guide (GitHub Actions & Jenkins)

> Covers every component of a production CI/CD pipeline, with real configuration files for both GitHub Actions and Jenkins. Includes patterns specific to AI/LLM applications.

---

## Table of Contents

1. [What CI/CD Actually Is](#1-what-cicd-actually-is)
2. [The Anatomy of a Production Pipeline](#2-the-anatomy-of-a-production-pipeline)
3. [Pipeline Components — Deep Dive](#3-pipeline-components--deep-dive)
4. [GitHub Actions — Complete Reference](#4-github-actions--complete-reference)
5. [Jenkins — Complete Reference](#5-jenkins--complete-reference)
6. [GitHub Actions vs Jenkins — When to Pick Which](#6-github-actions-vs-jenkins--when-to-pick-which)
7. [Advanced Patterns](#7-advanced-patterns)
8. [CI/CD for AI/LLM Applications](#8-cicd-for-aillm-applications)
9. [Security in CI/CD](#9-security-in-cicd)
10. [Observability and Debugging](#10-observability-and-debugging)
11. [Anti-Patterns](#11-anti-patterns)
12. [Interview Talking Points](#12-interview-talking-points)

---

## 1. What CI/CD Actually Is

**Continuous Integration (CI)**: every code change triggers automated build and test. The goal: catch bugs before they reach production, measured in minutes not days.

**Continuous Delivery (CD)**: every passing build is *deployable* to production. A human clicks the button.

**Continuous Deployment**: every passing build is *deployed* to production automatically. No human in the loop.

Most teams do CI + Continuous Delivery. Full Continuous Deployment requires mature testing, observability, and rollback — most organizations aren't there.

### 1.1 Why It Matters for the Interview

The JD calls out "CI/CD and environment management" as a must-have skill. Interviewers will ask:
- How do you structure a pipeline?
- What checks run at each stage?
- How do you handle secrets?
- How do you manage multiple environments?
- How do you roll back a bad deploy?
- What's different about CI/CD for AI/ML workloads?

---

## 2. The Anatomy of a Production Pipeline

Every production CI/CD pipeline has these stages, in this order. The details vary; the sequence doesn't.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER PUSHES CODE                        │
└────────────────────────────────┬─────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: CODE QUALITY (seconds)                                     │
│   • Linting (ruff, eslint)                                          │
│   • Formatting (black, prettier)                                    │
│   • Static type checking (mypy, tsc)                                │
│   • Dependency vulnerability scan (safety, snyk, dependabot)        │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: UNIT TESTS (seconds–minutes)                               │
│   • Fast, no external dependencies                                  │
│   • Mocked LLM calls, mocked DB                                    │
│   • Code coverage reporting                                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: BUILD (minutes)                                            │
│   • Docker image build (multi-stage)                                │
│   • Dependency resolution and lockfile verification                 │
│   • Build artifacts (wheel, JAR, etc.)                              │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: INTEGRATION TESTS (minutes)                                │
│   • Test against real services (DB, cache, queues)                  │
│   • Usually via Docker Compose or testcontainers                    │
│   • Contract tests (API schema validation)                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 5: SECURITY SCANNING (minutes)                                │
│   • Container image scanning (Trivy, Snyk)                          │
│   • SAST (static application security testing)                      │
│   • Secret detection (gitleaks, trufflehog)                         │
│   • License compliance                                              │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 6: PUSH ARTIFACTS (minutes)                                   │
│   • Push Docker image to registry (ECR, Docker Hub, GCR)            │
│   • Tag with commit SHA + branch + semver                           │
│   • Push Helm chart / Terraform plan                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 7: DEPLOY TO STAGING (minutes)                                │
│   • Apply infrastructure changes (Terraform / CDK)                  │
│   • Deploy application (ECS update, K8s rollout, Lambda update)     │
│   • Run database migrations                                        │
│   • Wait for health checks to pass                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 8: E2E TESTS ON STAGING (minutes)                             │
│   • End-to-end scenarios against staging                            │
│   • For AI apps: LLM eval suite (regression tests)                  │
│   • Performance / load tests (optional, can be scheduled)           │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 9: APPROVAL GATE (manual)                                     │
│   • Human review for production deploy                              │
│   • Required reviewers sign off                                     │
│   • Change management ticket linked                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 10: DEPLOY TO PRODUCTION (minutes)                            │
│   • Canary deployment (5–10% traffic)                               │
│   • Monitor key metrics (latency, errors, cost)                     │
│   • Auto-rollback if metrics breach thresholds                      │
│   • Progressive rollout to 100%                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 11: POST-DEPLOY VERIFICATION (minutes)                        │
│   • Synthetic transactions (smoke tests)                            │
│   • Monitoring dashboards checked                                   │
│   • Deployment tagged in observability tool                         │
└─────────────────────────────────────────────────────────────────────┘
```

Not every project needs all 11 stages on day one. But the ordering is important: fast, cheap checks run first; slow, expensive checks run later. A linting failure should not wait for integration tests to complete.

---

## 3. Pipeline Components — Deep Dive

### 3.1 Linting and Formatting

**What**: automated code quality enforcement. Catches style violations, unused imports, common bugs.

**Python stack**: `ruff` (linting + formatting, replaces both flake8 and black — fast, written in Rust), `mypy` (static type checking), `isort` (import ordering, now bundled in ruff).

**TypeScript stack**: `eslint` + `prettier` + `tsc --noEmit`.

**Why it matters**: eliminates 80% of code review comments, freeing reviewers to focus on logic and architecture.

```yaml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py312"
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
disallow_untyped_defs = true
```

### 3.2 Unit Tests

**What**: tests that run in isolation, no external dependencies. Mocked databases, mocked API calls, mocked LLM responses. Must complete in under 60 seconds for the full suite.

**Tools**: `pytest` (Python), `jest` (TypeScript). `pytest-cov` for coverage.

**Key patterns for AI apps**:

```python
# Mock the LLM client — don't call real APIs in unit tests
from unittest.mock import AsyncMock, patch

@patch("app.agents.supervisor.llm_client")
async def test_supervisor_routes_to_rag_agent(mock_llm):
    mock_llm.complete = AsyncMock(return_value='{"route": "rag", "reasoning": "..."}')
    state = await supervisor.run("What is our refund policy?")
    assert state.status == "done"
    assert "rag" in state.step_log[0]
```

### 3.3 Build (Docker)

**What**: packaging the application into a deployable artifact. For Python services, almost always a Docker container.

**Multi-stage build** (production pattern):

```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Stage 2: Runtime image
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Why multi-stage: the builder stage has all the build tools (compilers, pip, etc.) but the runtime image doesn't — smaller image, smaller attack surface.

### 3.4 Integration Tests

**What**: tests that hit real services — database, cache, message queue. Run against Docker Compose or testcontainers.

```python
# conftest.py
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()

# test_retrieval.py
async def test_vector_search_returns_relevant_chunks(postgres):
    # Insert test embeddings, run a query, verify results
    results = await retriever.search("refund policy", top_k=5)
    assert len(results) >= 1
    assert "refund" in results[0].text.lower()
```

### 3.5 Security Scanning

**Container scanning**: `trivy image myapp:latest` — finds known CVEs in OS packages and dependencies.

**Secret detection**: `gitleaks detect --source .` — finds accidentally committed secrets (API keys, passwords).

**SAST**: `bandit` (Python) or `semgrep` — finds common security bugs in code.

**Dependency audit**: `pip-audit` (Python), `npm audit` (Node).

### 3.6 Artifact Registry

Where you push your built containers and packages:
- **AWS ECR** (Elastic Container Registry) — AWS-native, integrates with ECS/EKS
- **Docker Hub** — public, widely used for open source
- **GitHub Container Registry (ghcr.io)** — integrates tightly with GitHub Actions
- **Google Artifact Registry** — GCP-native

Tag images with at least: `<commit-sha>`, `<branch>`, `latest` (for the default branch).

### 3.7 Infrastructure as Code (IaC)

Your infrastructure definition lives in version control alongside application code.

**Tools**:
- **Terraform**: the de facto standard. HCL language. Provider-agnostic.
- **AWS CDK**: AWS-specific, write IaC in Python/TypeScript/Java.
- **Pulumi**: like CDK but multi-cloud.
- **CloudFormation**: AWS-native YAML/JSON. Verbose but direct.

**Pipeline integration**: `terraform plan` runs on every PR (shows what *would* change). `terraform apply` runs on merge to main (applies the change). Never apply without a plan review.

### 3.8 Deployment Strategies

| Strategy | How it works | Risk | Rollback speed |
|---|---|---|---|
| **Rolling update** | Gradually replace old instances with new | Brief period with mixed versions | Minutes |
| **Blue-green** | Two identical environments; switch traffic | Full second environment cost | Seconds (DNS/LB switch) |
| **Canary** | Send 5–10% of traffic to new version | Small blast radius | Seconds (route traffic back) |
| **Feature flags** | New code deployed but disabled; toggle on | Zero-risk deploy | Instant (flag off) |
| **Recreate** | Kill all old, start all new | Downtime | Minutes |

**Production default**: canary + auto-rollback. Route 5% of traffic to the new version. Monitor P99 latency, error rate, and business metrics for 15–30 minutes. If any threshold breaches, automatically route all traffic back to the old version.

### 3.9 Database Migrations

The most dangerous part of any deploy. Rules:

1. **Never destructive in a single migration.** Don't rename or drop columns in the same deploy that changes the code. Two-phase: (a) add new column, (b) deploy code that uses new column, (c) next migration drops old column.
2. **Migrations run before the application deploy.** If the migration fails, the deploy stops.
3. **Every migration must be reversible.** `alembic downgrade` should work.
4. **Test migrations on a staging copy of production data** — not on empty databases.

**Tools**: Alembic (SQLAlchemy/Python), Flyway (Java), Prisma Migrate (TypeScript).

### 3.10 Smoke Tests

Minimal end-to-end checks that run immediately after deployment. They answer one question: "is the thing alive and serving correct responses?"

```bash
#!/bin/bash
# smoke-test.sh
set -e

BASE_URL=$1

# Health check
curl -sf "$BASE_URL/health" | jq -e '.status == "ok"'

# Basic API call
RESPONSE=$(curl -sf "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}')

echo "$RESPONSE" | jq -e '.answer != null'
echo "$RESPONSE" | jq -e '.latency_ms < 5000'

echo "Smoke tests passed"
```

---

## 4. GitHub Actions — Complete Reference

### 4.1 Core Concepts

| Concept | What it is |
|---|---|
| **Workflow** | A YAML file in `.github/workflows/` that defines a pipeline |
| **Trigger** | What starts the workflow (`push`, `pull_request`, `schedule`, `workflow_dispatch`) |
| **Job** | A set of steps that run on the same runner. Jobs run in parallel by default. |
| **Step** | A single command or action within a job |
| **Action** | A reusable unit of work (e.g., `actions/checkout@v4`). Community marketplace has thousands. |
| **Runner** | The machine that executes the job. GitHub-hosted (free tier) or self-hosted. |
| **Environment** | A named deployment target (staging, production) with approval rules and secrets. |
| **Secret** | An encrypted variable stored at repo or org level. Never logged. |
| **Matrix** | Run the same job across multiple configurations (Python versions, OS). |
| **Artifact** | Files produced by one job and consumed by another. |
| **Cache** | Cached dependencies (pip, npm) to speed up builds. |
| **Concurrency** | Controls whether workflows can run simultaneously. |

### 4.2 Full Production Pipeline — GitHub Actions

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # cancel stale runs

env:
  PYTHON_VERSION: "3.12"
  AWS_REGION: eu-central-1
  ECR_REGISTRY: 123456789.dkr.ecr.eu-central-1.amazonaws.com
  ECR_REPOSITORY: agent-service
  ECS_CLUSTER: production
  ECS_SERVICE: agent-service

# ─────────────────────────────────────────────────
# STAGE 1 + 2: Code quality + Unit tests
# ─────────────────────────────────────────────────
jobs:
  lint-and-test:
    name: Lint & Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
          restore-keys: ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --frozen

      - name: Lint
        run: |
          ruff check .
          ruff format --check .

      - name: Type check
        run: mypy src/ --strict

      - name: Unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: false

  # ─────────────────────────────────────────────────
  # STAGE 3: Security scanning
  # ─────────────────────────────────────────────────
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Secret detection
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Dependency audit
        run: |
          pip install pip-audit
          pip-audit -r requirements.txt

  # ─────────────────────────────────────────────────
  # STAGE 4: Integration tests
  # ─────────────────────────────────────────────────
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [lint-and-test]
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install uv && uv sync --frozen
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: pytest tests/integration/ -v --tb=short

  # ─────────────────────────────────────────────────
  # STAGE 5 + 6: Build and push Docker image
  # ─────────────────────────────────────────────────
  build:
    name: Build & Push
    runs-on: ubuntu-latest
    needs: [lint-and-test, security, integration-tests]
    if: github.ref == 'refs/heads/main'
    permissions:
      id-token: write   # OIDC for AWS
      contents: read
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: ecr-login
        uses: aws-actions/amazon-ecr-login@v2

      - name: Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          format: table
          exit-code: 1
          severity: CRITICAL,HIGH

  # ─────────────────────────────────────────────────
  # STAGE 7: Deploy to staging
  # ─────────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build]
    environment:
      name: staging
      url: https://staging.example.com
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy to ECS (staging)
        run: |
          # Update task definition with new image
          TASK_DEF=$(aws ecs describe-task-definition \
            --task-definition agent-service-staging \
            --query 'taskDefinition' --output json)

          NEW_TASK_DEF=$(echo $TASK_DEF | jq \
            --arg IMAGE "${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}" \
            '.containerDefinitions[0].image = $IMAGE |
             del(.taskDefinitionArn, .revision, .status, .requiresAttributes,
                 .compatibilities, .registeredAt, .registeredBy)')

          aws ecs register-task-definition \
            --cli-input-json "$NEW_TASK_DEF"

          aws ecs update-service \
            --cluster staging \
            --service agent-service-staging \
            --task-definition agent-service-staging \
            --force-new-deployment

      - name: Wait for stable
        run: |
          aws ecs wait services-stable \
            --cluster staging \
            --services agent-service-staging

      - name: Smoke test staging
        run: ./scripts/smoke-test.sh https://staging.example.com

  # ─────────────────────────────────────────────────
  # STAGE 8: LLM eval on staging (AI-specific)
  # ─────────────────────────────────────────────────
  llm-eval:
    name: LLM Regression Tests
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install uv && uv sync --frozen
      - name: Run eval suite
        env:
          API_BASE_URL: https://staging.example.com
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python -m pytest tests/evals/ \
            --eval-threshold=0.85 \
            --eval-report=eval_report.json \
            -v
      - name: Upload eval report
        uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: eval_report.json

  # ─────────────────────────────────────────────────
  # STAGE 9 + 10: Deploy to production (with approval)
  # ─────────────────────────────────────────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [llm-eval]
    environment:
      name: production        # requires manual approval
      url: https://api.example.com
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy-prod
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy to ECS (production)
        run: |
          TASK_DEF=$(aws ecs describe-task-definition \
            --task-definition agent-service-prod \
            --query 'taskDefinition' --output json)

          NEW_TASK_DEF=$(echo $TASK_DEF | jq \
            --arg IMAGE "${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}" \
            '.containerDefinitions[0].image = $IMAGE |
             del(.taskDefinitionArn, .revision, .status, .requiresAttributes,
                 .compatibilities, .registeredAt, .registeredBy)')

          aws ecs register-task-definition \
            --cli-input-json "$NEW_TASK_DEF"

          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service ${{ env.ECS_SERVICE }} \
            --task-definition agent-service-prod \
            --force-new-deployment

      - name: Wait for stable
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services ${{ env.ECS_SERVICE }}

      - name: Smoke test production
        run: ./scripts/smoke-test.sh https://api.example.com

      - name: Tag release
        run: |
          git tag "deploy-$(date +%Y%m%d-%H%M%S)-${{ github.sha }}"
          git push origin --tags
```

### 4.3 Key GitHub Actions Features

**OIDC authentication** (no long-lived AWS keys):
```yaml
permissions:
  id-token: write
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789:role/github-actions
```
GitHub generates a short-lived token; AWS validates it via IAM OIDC provider. No `AWS_ACCESS_KEY_ID` secret needed.

**Environments** with protection rules:
```
Settings → Environments → production
  [x] Required reviewers: [lead-engineer, devops]
  [x] Wait timer: 5 minutes
  [x] Deployment branches: only "main"
```

**Matrix builds** (test across versions):
```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    os: [ubuntu-latest, macos-latest]
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

**Caching** (speeds up CI by 50–80%):
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ hashFiles('pyproject.toml') }}
```

**Concurrency** (cancel stale runs):
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Reusable workflows** (DRY across repos):
```yaml
# .github/workflows/reusable-deploy.yml
on:
  workflow_call:
    inputs:
      environment:
        type: string
        required: true
```

**Scheduled workflows** (nightly evals, weekly scans):
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2am UTC daily
```

---

## 5. Jenkins — Complete Reference

### 5.1 Core Concepts

| Concept | What it is |
|---|---|
| **Controller** | The main Jenkins server that manages jobs and distributes work |
| **Agent (Node)** | A machine that executes builds (can be EC2, K8s pod, container) |
| **Pipeline** | A Jenkinsfile (Groovy DSL) defining the build stages |
| **Declarative Pipeline** | Structured syntax (`pipeline { ... }`) — preferred for most use cases |
| **Scripted Pipeline** | Full Groovy flexibility (`node { ... }`) — for complex logic |
| **Stage** | A named phase (Build, Test, Deploy) |
| **Step** | A single command within a stage (`sh`, `docker.build`, etc.) |
| **Shared Library** | Reusable Groovy code loaded from a Git repo |
| **Blue Ocean** | Modern Jenkins UI for pipeline visualization |
| **Credentials** | Managed secrets stored in Jenkins (API keys, passwords, certificates) |
| **Multibranch Pipeline** | Automatically discovers and builds all branches with a Jenkinsfile |

### 5.2 Full Production Pipeline — Jenkinsfile

```groovy
pipeline {
    agent any

    environment {
        AWS_REGION       = 'eu-central-1'
        ECR_REGISTRY     = '123456789.dkr.ecr.eu-central-1.amazonaws.com'
        ECR_REPOSITORY   = 'agent-service'
        ECS_CLUSTER      = 'production'
        ECS_SERVICE      = 'agent-service'
        PYTHON_VERSION   = '3.12'
        IMAGE_TAG        = "${env.GIT_COMMIT?.take(7) ?: 'latest'}"
    }

    options {
        timeout(time: 60, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timestamps()
    }

    stages {
        // ────────────────────────────────────
        // STAGE 1: Code Quality
        // ────────────────────────────────────
        stage('Lint & Type Check') {
            agent {
                docker {
                    image "python:${PYTHON_VERSION}-slim"
                    args '-u root'
                }
            }
            steps {
                sh '''
                    pip install uv
                    uv sync --frozen
                    ruff check .
                    ruff format --check .
                    mypy src/ --strict
                '''
            }
        }

        // ────────────────────────────────────
        // STAGE 2: Unit Tests
        // ────────────────────────────────────
        stage('Unit Tests') {
            agent {
                docker {
                    image "python:${PYTHON_VERSION}-slim"
                    args '-u root'
                }
            }
            steps {
                sh '''
                    pip install uv
                    uv sync --frozen
                    pytest tests/unit/ -v --cov=src --cov-report=xml --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }

        // ────────────────────────────────────
        // STAGE 3: Security Scanning
        // ────────────────────────────────────
        stage('Security') {
            parallel {
                stage('Secret Detection') {
                    steps {
                        sh 'docker run --rm -v "$(pwd):/repo" zricethezav/gitleaks:latest detect --source /repo'
                    }
                }
                stage('Dependency Audit') {
                    agent {
                        docker { image "python:${PYTHON_VERSION}-slim" }
                    }
                    steps {
                        sh '''
                            pip install pip-audit
                            pip-audit -r requirements.txt
                        '''
                    }
                }
            }
        }

        // ────────────────────────────────────
        // STAGE 4: Integration Tests
        // ────────────────────────────────────
        stage('Integration Tests') {
            steps {
                script {
                    docker.image('docker/compose:latest').inside {
                        sh '''
                            docker-compose -f docker-compose.test.yml up -d
                            sleep 10
                            pytest tests/integration/ -v --tb=short
                        '''
                    }
                }
            }
            post {
                always {
                    sh 'docker-compose -f docker-compose.test.yml down -v || true'
                }
            }
        }

        // ────────────────────────────────────
        // STAGE 5: Build & Push Docker Image
        // ────────────────────────────────────
        stage('Build & Push') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-deploy-credentials']]) {
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REGISTRY}

                        docker build -t ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG} .
                        docker tag ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG} \
                                   ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

                        docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
                    """
                }
            }
        }

        // ────────────────────────────────────
        // STAGE 6: Container Security Scan
        // ────────────────────────────────────
        stage('Image Scan') {
            when { branch 'main' }
            steps {
                sh """
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                        --exit-code 1 \
                        --severity CRITICAL,HIGH \
                        ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
                """
            }
        }

        // ────────────────────────────────────
        // STAGE 7: Deploy to Staging
        // ────────────────────────────────────
        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-deploy-credentials']]) {
                    sh """
                        aws ecs update-service \
                            --cluster staging \
                            --service agent-service-staging \
                            --force-new-deployment \
                            --region ${AWS_REGION}

                        aws ecs wait services-stable \
                            --cluster staging \
                            --services agent-service-staging \
                            --region ${AWS_REGION}
                    """
                }
                sh './scripts/smoke-test.sh https://staging.example.com'
            }
        }

        // ────────────────────────────────────
        // STAGE 8: LLM Eval on Staging
        // ────────────────────────────────────
        stage('LLM Evaluation') {
            when { branch 'main' }
            steps {
                withCredentials([string(credentialsId: 'anthropic-api-key',
                                       variable: 'ANTHROPIC_API_KEY')]) {
                    sh '''
                        pytest tests/evals/ \
                            --eval-threshold=0.85 \
                            --eval-report=eval_report.json \
                            -v
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'eval_report.json'
                }
            }
        }

        // ────────────────────────────────────
        // STAGE 9: Production Approval
        // ────────────────────────────────────
        stage('Approval') {
            when { branch 'main' }
            steps {
                input message: 'Deploy to production?',
                      ok: 'Deploy',
                      submitter: 'lead-engineer,devops-team'
            }
        }

        // ────────────────────────────────────
        // STAGE 10: Deploy to Production
        // ────────────────────────────────────
        stage('Deploy Production') {
            when { branch 'main' }
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-deploy-credentials-prod']]) {
                    sh """
                        aws ecs update-service \
                            --cluster ${ECS_CLUSTER} \
                            --service ${ECS_SERVICE} \
                            --force-new-deployment \
                            --region ${AWS_REGION}

                        aws ecs wait services-stable \
                            --cluster ${ECS_CLUSTER} \
                            --services ${ECS_SERVICE} \
                            --region ${AWS_REGION}
                    """
                }
                sh './scripts/smoke-test.sh https://api.example.com'
            }
        }
    }

    post {
        success {
            slackSend(channel: '#deploys',
                      color: 'good',
                      message: "Deploy successful: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        failure {
            slackSend(channel: '#deploys',
                      color: 'danger',
                      message: "Deploy FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        always {
            cleanWs()
        }
    }
}
```

### 5.3 Key Jenkins Features

**Shared Libraries** (reusable pipeline code):
```groovy
// In Jenkinsfile
@Library('my-shared-lib') _

pipeline {
    stages {
        stage('Deploy') {
            steps {
                deployToECS(cluster: 'prod', service: 'agent-service')
            }
        }
    }
}
```

**Parallel stages**:
```groovy
stage('Tests') {
    parallel {
        stage('Unit') { steps { sh 'pytest tests/unit/' } }
        stage('Lint') { steps { sh 'ruff check .' } }
        stage('Security') { steps { sh 'pip-audit -r requirements.txt' } }
    }
}
```

**Dynamic agents** (spin up EC2/K8s pod per build):
```groovy
agent {
    kubernetes {
        yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: python
    image: python:3.12
    command: ['sleep', 'infinity']
"""
    }
}
```

**Credentials management**: Jenkins stores secrets centrally. Use `withCredentials` to inject them:
```groovy
withCredentials([
    string(credentialsId: 'api-key', variable: 'API_KEY'),
    usernamePassword(credentialsId: 'db-creds', usernameVariable: 'DB_USER', passwordVariable: 'DB_PASS')
]) {
    sh 'echo $API_KEY'  // masked in logs
}
```

---

## 6. GitHub Actions vs Jenkins — When to Pick Which

### 6.1 Comparison Matrix

| Aspect | GitHub Actions | Jenkins |
|---|---|---|
| **Hosting** | Managed (GitHub) or self-hosted runners | Self-hosted (you operate it) |
| **Setup time** | Minutes (add YAML, push) | Hours–days (install, configure, plugins) |
| **Configuration** | YAML in repo | Groovy Jenkinsfile in repo (or UI) |
| **Plugin ecosystem** | Marketplace (20K+ actions) | Plugin ecosystem (1800+ plugins) |
| **Maintenance burden** | Near-zero (managed) | Significant (upgrades, security, scaling) |
| **Cost** | Free tier (2000 min/month); pay per minute after | Free (open source) but you pay for infrastructure |
| **Secrets management** | Built-in (repo/org/environment secrets) | Credentials plugin (adequate but clunkier) |
| **Approval gates** | Environment protection rules | `input` step |
| **Self-hosted runners** | Supported (EC2, K8s, on-prem) | Native (agents are the core concept) |
| **Scalability** | GitHub handles it (or you scale self-hosted) | You handle it (agent provisioning) |
| **Customization** | Limited to YAML + shell | Full Groovy — almost unlimited |
| **Integration** | Tight with GitHub (PRs, issues, packages) | Integrates with everything (but nothing "tightly") |
| **Visibility** | PR checks, deployment status on commits | Blue Ocean UI, dashboard plugins |
| **Multi-repo** | Each repo has its own workflows | Centralized pipelines across repos |
| **Learning curve** | Low | Medium-high (Groovy, plugin configuration) |

### 6.2 Decision Guide

**Pick GitHub Actions when**:
- Your code is on GitHub
- You want minimal operational overhead
- Your pipelines are standard (build, test, deploy)
- Your team is small/medium
- You want CI/CD working in under an hour

**Pick Jenkins when**:
- You need maximum customization and control
- You have complex multi-repo orchestration
- You're on-prem or in a regulated environment that requires self-hosted everything
- Your organization already has Jenkins expertise and infrastructure
- You need to integrate with legacy systems that only have Jenkins plugins

**The trend**: GitHub Actions is eating Jenkins's market share in 2025–2026. Most new projects start on Actions. Jenkins remains entrenched in enterprises with existing investments.

---

## 7. Advanced Patterns

### 7.1 Monorepo CI

When multiple services live in one repo:

```yaml
on:
  push:
    paths:
      - 'services/agent/**'
      - 'services/retrieval/**'
      - 'shared/**'

jobs:
  detect-changes:
    outputs:
      agent: ${{ steps.filter.outputs.agent }}
      retrieval: ${{ steps.filter.outputs.retrieval }}
    steps:
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            agent:
              - 'services/agent/**'
              - 'shared/**'
            retrieval:
              - 'services/retrieval/**'
              - 'shared/**'

  build-agent:
    needs: detect-changes
    if: needs.detect-changes.outputs.agent == 'true'
    # ... build only agent service
```

### 7.2 Auto-Rollback

Monitor after deploy; rollback automatically if metrics breach:

```yaml
- name: Monitor canary (5 minutes)
  run: |
    for i in $(seq 1 10); do
      ERROR_RATE=$(aws cloudwatch get-metric-statistics \
        --namespace "ECS/Agent" \
        --metric-name "5xxErrorRate" \
        --period 30 --statistics Average \
        --start-time $(date -u -d '30 seconds ago' +%Y-%m-%dT%H:%M:%SZ) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
        | jq '.Datapoints[0].Average // 0')

      if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
        echo "Error rate ${ERROR_RATE}% exceeds 5% — rolling back"
        aws ecs update-service \
          --cluster production \
          --service agent-service \
          --task-definition agent-service-prod:PREVIOUS \
          --force-new-deployment
        exit 1
      fi
      sleep 30
    done
```

### 7.3 Terraform in CI

```yaml
terraform-plan:
  runs-on: ubuntu-latest
  steps:
    - uses: hashicorp/setup-terraform@v3
    - run: terraform init
    - run: terraform plan -out=tfplan
    - uses: actions/upload-artifact@v4
      with:
        name: tfplan
        path: tfplan

terraform-apply:
  needs: terraform-plan
  if: github.ref == 'refs/heads/main'
  environment: production  # requires approval
  steps:
    - uses: actions/download-artifact@v4
      with:
        name: tfplan
    - run: terraform apply tfplan
```

### 7.4 GitOps (ArgoCD / Flux)

Instead of CI pushing deploys, CI pushes a new image tag to a Git repo → ArgoCD detects the change → ArgoCD deploys to K8s. The cluster state is always defined by Git.

```yaml
# CI pushes the new tag to a deployment repo
- name: Update deployment repo
  run: |
    git clone https://github.com/org/deployments.git
    cd deployments
    yq e ".image.tag = \"${{ github.sha }}\"" -i charts/agent-service/values.yaml
    git commit -am "Deploy agent-service ${{ github.sha }}"
    git push
```

ArgoCD watches the deployment repo and reconciles.

---

## 8. CI/CD for AI/LLM Applications

This is the section that distinguishes your pipeline from a generic web service pipeline.

### 8.1 What's Different About AI/LLM CI/CD

Standard web apps have a clear contract: given input X, the output should be Y. LLMs produce non-deterministic outputs, so testing is fundamentally harder.

What changes:
- **Unit tests mock LLM responses** — you can't call real APIs in CI (cost, non-determinism)
- **An evaluation suite replaces traditional E2E tests** — you measure quality properties (faithfulness, format compliance, citation accuracy) rather than exact match
- **Prompt versioning is a deployable artifact** — a prompt change is as impactful as a code change
- **Cost monitoring is a pipeline gate** — a bad prompt can 10× your token spend
- **Model version pinning** — you deploy against a specific model version, not "latest"

### 8.2 The LLM Eval Stage

The most important addition to a standard pipeline:

```python
# tests/evals/test_rag_quality.py
import pytest
import json

EVAL_SET = json.load(open("tests/evals/eval_set.jsonl"))
THRESHOLD = 0.85  # 85% of cases must pass

@pytest.mark.parametrize("case", EVAL_SET, ids=lambda c: c["id"])
async def test_rag_answer_quality(case, staging_api):
    response = await staging_api.query(case["query"])

    # Format check
    assert response.get("answer") is not None
    assert len(response["answer"]) <= case.get("max_words", 500) * 5  # rough char limit

    # Content check
    for expected in case.get("expected_contains", []):
        assert expected.lower() in response["answer"].lower(), \
            f"Expected '{expected}' in answer"

    # Citation check
    if case.get("min_citations", 0) > 0:
        assert len(response.get("citations", [])) >= case["min_citations"]

    # Refusal check
    if case.get("should_refuse", False):
        assert response.get("refused", False) or "cannot" in response["answer"].lower()
```

**Gating logic**: fail the pipeline if pass rate drops below threshold. But compute the pass rate across the full suite, not per-case — some cases may be legitimately hard.

### 8.3 Prompt Version Tracking

```yaml
# In the pipeline, tag every deploy with the prompt version
- name: Record prompt versions
  run: |
    echo "Prompt versions deployed:" >> deploy_manifest.json
    for f in prompts/*.jinja; do
      echo "  $(basename $f): $(sha256sum $f | cut -d' ' -f1)" >> deploy_manifest.json
    done
```

### 8.4 Cost Guard

```yaml
- name: Cost estimation
  run: |
    # Run eval suite and capture token usage
    python -m tests.evals.run_evals --dry-run --output=cost_estimate.json

    COST=$(jq '.estimated_daily_cost_usd' cost_estimate.json)
    BASELINE=$(jq '.baseline_daily_cost_usd' cost_estimate.json)

    if (( $(echo "$COST > $BASELINE * 2" | bc -l) )); then
      echo "Cost estimate $COST exceeds 2x baseline $BASELINE — blocking deploy"
      exit 1
    fi
```

### 8.5 Model Version Pinning

```python
# config.py
MODEL_CONFIG = {
    "primary": "claude-sonnet-4-6-20250514",  # specific date snapshot
    "fallback": "claude-haiku-4-5-20251001",
    "embedding": "text-embedding-3-small",
}
```

Pin to dated model versions. A model upgrade is a deliberate decision with eval suite results, not a surprise.

---

## 9. Security in CI/CD

### 9.1 Secrets Management

**Rule 1**: secrets never appear in code, logs, or pipeline definitions.

**Rule 2**: use short-lived credentials (OIDC, STS) over long-lived access keys.

| Secret type | GitHub Actions | Jenkins |
|---|---|---|
| API keys | Repository secrets or environment secrets | Credentials plugin (Secret text) |
| AWS credentials | OIDC (no stored keys) | AWS credentials binding plugin |
| Docker registry | `docker/login-action` | `withCredentials` + `docker login` |
| Database passwords | Environment secrets | Credentials plugin |
| Certificates | Self-hosted runner + mount | Agent filesystem + binding |

### 9.2 Supply Chain Security

- **Dependency lockfiles**: `uv.lock`, `package-lock.json` — verified in CI
- **Signed commits**: require GPG-signed commits on protected branches
- **Pin action versions**: `uses: actions/checkout@v4` not `@main`
- **Scorecard**: OpenSSF Scorecard to audit your repo's security posture
- **SLSA provenance**: generate build provenance attestations

### 9.3 Branch Protection

```
Settings → Branches → main
  [x] Require pull request reviews (1+ approver)
  [x] Require status checks to pass (lint, test, security)
  [x] Require branches to be up to date before merging
  [x] Require signed commits
  [x] Do not allow bypassing the above settings
```

### 9.4 Least-Privilege IAM for CI/CD

Each pipeline stage gets the minimum permissions it needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PushToECR",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:eu-central-1:123456789:repository/agent-service"
    },
    {
      "Sid": "DeployToECS",
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ecs:cluster": "arn:aws:ecs:eu-central-1:123456789:cluster/production"
        }
      }
    }
  ]
}
```

---

## 10. Observability and Debugging

### 10.1 Pipeline Observability

Track these metrics on your pipeline itself:

- **Build duration** (p50, p95) — alert if it creeps above 15 minutes
- **Build success rate** — should be >95%; below that means flaky tests or infra issues
- **Mean time to recovery (MTTR)** — how long from "build broken" to "build fixed"
- **Deploy frequency** — how often you ship to production per week
- **Change failure rate** — % of deploys that cause an incident

These are the four DORA metrics (Deploy Frequency, Lead Time, Change Failure Rate, MTTR) — the industry standard for DevOps performance.

### 10.2 Debugging Failed Pipelines

Common failure patterns and fixes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Flaky test failures | Non-deterministic tests, race conditions, external dependencies | Mock external calls; add retries for infra flakes only |
| "Module not found" in CI | Dependency not in lockfile, or cache stale | Always install from lockfile; bust cache |
| Docker build OOM | Large dependencies or build context | Multi-stage build; `.dockerignore` |
| ECR push fails | IAM permission missing or token expired | Check OIDC role trust policy; re-auth |
| Deploy times out | Health check failing on new version | Check container logs; verify health endpoint |
| Integration test failures | Service container not ready | Add health check waits; increase timeout |
| "Permission denied" | Runner user mismatch with container | `args: '-u root'` or fix file permissions |

---

## 11. Anti-Patterns

**1. No pipeline at all.** Deploying from a developer's laptop. The most dangerous anti-pattern, still common.

**2. 45-minute builds.** If CI takes longer than a coffee break, developers stop waiting for it. Target: under 10 minutes for the full suite. Parallelize aggressively.

**3. Flaky tests left in.** A test that fails 5% of the time is worse than no test — it trains the team to ignore failures. Fix or delete.

**4. Secrets in environment variables in the YAML.** Use the secrets mechanism. Never `env: API_KEY: sk-abc123`.

**5. No staging environment.** Deploying straight from CI to production without a staging step. The blast radius of a bug is your entire user base.

**6. Manual database migrations.** If migrations require SSH-ing into a box and running a script, they will eventually be forgotten or run wrong.

**7. "It works on my machine."** If local and CI environments diverge, bugs slip through. Use the same Docker image locally and in CI.

**8. Deploying on Friday at 5pm.** Automated pipelines make this technically easy. Don't. Nobody wants to debug a production issue at 11pm on a Friday.

**9. No rollback plan.** Every deploy should have a clear "undo" mechanism — revert the ECS task definition, flip the feature flag, restore the database snapshot. Test the rollback.

**10. Ignoring pipeline costs.** GitHub Actions minutes and self-hosted runner compute add up. Cache aggressively, cancel stale runs, right-size runners.

---

## 12. Interview Talking Points

### "Walk me through your CI/CD pipeline."

Strong answer:

> "It's eleven stages. Code quality runs first — ruff and mypy, takes about 15 seconds. Then unit tests with mocked LLM calls, about 45 seconds. Those two gate everything else. If they fail, we stop fast.
>
> Next, security scanning — gitleaks for secret detection, pip-audit for dependency vulnerabilities, Trivy for container image CVEs. Integration tests run in parallel using testcontainers for Postgres and Redis.
>
> If all that passes and we're on main, we build a Docker image (multi-stage for minimal attack surface), push to ECR tagged with the commit SHA, and deploy to staging. On staging we run smoke tests plus our LLM evaluation suite — about 200 test cases checking format compliance, citation accuracy, and content quality against a regression threshold.
>
> Production deploy requires a manual approval gate and uses a canary strategy — 5% traffic for 15 minutes, auto-rollback if error rate exceeds 2%. After full rollout, synthetic transactions run every 5 minutes as an ongoing heartbeat."

### "How do you handle secrets?"

> "Short-lived credentials wherever possible. For AWS, we use OIDC — GitHub generates a token, AWS validates it via an IAM OIDC provider, no stored keys. For API keys (Anthropic, OpenAI), they're in GitHub environment secrets scoped to specific environments. Each environment (staging, production) has its own secrets. Jenkins uses the Credentials plugin with the same scoping. No secret ever appears in a YAML file, a log, or a commit."

### "How do you test LLM applications in CI?"

> "Three layers. Unit tests mock the LLM client entirely — we test prompt template rendering, output parsing, and schema validation without any API calls. Integration tests use a cheap model (Haiku) against real services but with a small eval set. The full eval suite runs on staging after deploy — 200+ cases measuring faithfulness, format compliance, citation accuracy, and refusal behavior. We gate on aggregate pass rate, not per-case, because LLM outputs are non-deterministic. A prompt change is treated as seriously as a code change — it goes through the same pipeline with the same eval gate."

### "How do you roll back a bad deploy?"

> "Three mechanisms, increasing in severity. First, feature flags — the new code is deployed but the feature is toggled off. Fastest, no redeploy needed. Second, ECS task definition revert — point the service back to the previous task definition. Takes about 2 minutes. Third, full rollback — revert the Git commit, which triggers the full pipeline against the known-good code. Takes about 10 minutes.
>
> For database migrations, we use a two-phase approach — additive changes first, then destructive changes in a later migration — so rolling back the application doesn't break against the database."

### "GitHub Actions or Jenkins — how do you decide?"

> "GitHub Actions for most new projects. The setup time is minutes, operational overhead is near-zero, OIDC for AWS is built-in, and the environment protection rules handle approval gates. The only cases where I'd reach for Jenkins are heavy customization needs (complex multi-repo orchestration), regulatory environments that require fully self-hosted infrastructure, or organizations with significant existing Jenkins investment. The trend is clear — Actions is eating Jenkins's market share — but Jenkins is still the right tool for specific enterprise constraints."

---

## How Jenkins and GitHub Actions Deploy

### Jenkins

Jenkins is a **self-hosted** automation server you run on your own infrastructure.

**How it works:**
1. Developer pushes code to Git
2. Jenkins detects the change (via webhook or polling)
3. Jenkins runs a pipeline defined in a `Jenkinsfile` (lives in your repo)
4. Pipeline stages run on Jenkins agents (servers you manage)

```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('Build') {
            steps { sh 'mvn clean package' }
        }
        stage('Test') {
            steps { sh 'mvn test' }
        }
        stage('Deploy') {
            steps {
                sh 'docker build -t myapp .'
                sh 'kubectl apply -f k8s/deployment.yaml'
            }
        }
    }
}
```

**Key traits:**
- You manage the servers (agents), plugins, credentials, scaling
- Very flexible, huge plugin ecosystem
- Common in enterprises with existing infrastructure
- Credentials stored in Jenkins itself, injected as env vars at runtime

---

### GitHub Actions

GitHub Actions is **cloud-hosted** — GitHub runs the compute for you (or you can add self-hosted runners).

**How it works:**
1. Developer pushes code (or opens a PR)
2. GitHub detects the event
3. GitHub spins up a runner (fresh VM) and runs your workflow YAML
4. Workflow defined in `.github/workflows/*.yml`

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build
        run: docker build -t myapp .
      - name: Deploy to AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        run: aws ecs update-service --cluster prod --service myapp
```

**Key traits:**
- No servers to manage (unless using self-hosted runners)
- Secrets stored in GitHub repo/org settings
- Marketplace of pre-built Actions (like npm packages for pipelines)
- Tight integration with PRs, issues, GitHub environments

---

### Side-by-Side Comparison

| | Jenkins | GitHub Actions |
|---|---|---|
| Hosting | Self-managed | GitHub-managed |
| Config | `Jenkinsfile` (Groovy) | `.yml` (YAML) |
| Compute | Your agents | GitHub runners (VMs) |
| Secrets | Jenkins credentials store | GitHub Secrets |
| Cost | Infrastructure cost | Free tier + per-minute pricing |
| Flexibility | Very high | High |
| Setup effort | High | Low |

---

### The Actual Deploy Step

The pipeline itself doesn't "deploy" magically — it just runs shell commands. Common deploy mechanisms:

- **Kubernetes** — `kubectl apply -f deployment.yaml` or `helm upgrade`
- **AWS** — `aws ecs update-service` or `aws deploy`
- **SSH** — `scp` files to a server, restart the process
- **Heroku/Render** — `git push heroku main`

The CI/CD tool is an **orchestrator** — it runs your build, test, and deploy scripts in the right order, on the right trigger.

