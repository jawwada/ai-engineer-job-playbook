## 11. Real Interview Questions — Deep Dives

---

### 11.1 Agentic RAG vs Normal RAG

#### The Short Answer
Normal RAG is a fixed, single-pass pipeline. Agentic RAG treats retrieval as a dynamic, reasoned action — the agent decides *whether* to retrieve, *what* to search for, *how many times*, and *whether the results are good enough*.

#### Normal RAG — What It Does

```
User query
    ↓
Embed query → search vector DB → retrieve top-K chunks
    ↓
Stuff chunks into prompt → LLM generates answer
```

**Limitations of normal RAG:**
- The query is used as-is — if the user phrases it poorly, retrieval fails
- Always retrieves, even when the answer is already in context
- Single shot — no retry if the retrieved chunks miss the point
- Can't combine information across multiple retrieval passes
- No verification that retrieved content actually supports the answer

#### Agentic RAG — What It Adds

| Capability | Description | Benefit |
|---|---|---|
| **Query decomposition** | Breaks a complex question into sub-queries, retrieves for each | Handles multi-part and ambiguous questions |
| **Iterative retrieval** | If first retrieval is poor, reformulates query and retrieves again | Higher recall on difficult questions |
| **Self-RAG** | Agent decides *whether* retrieval is needed at all | Saves latency and cost for simple questions |
| **Corrective RAG** | Scores retrieved chunks for relevance; falls back to web search if all are low | Avoids hallucinating from irrelevant context |
| **HyDE** | Generates a hypothetical ideal answer, embeds *that*, uses it to retrieve | Retrieves more semantically relevant chunks |
| **Multi-source routing** | Agent chooses which knowledge base to query based on question type | Better precision, avoids noise from wrong corpus |
| **Citation verification** | Agent checks that each claim is supported by what was actually retrieved | Reduces hallucination in the final answer |

#### Example — Why Agentic RAG Wins on a Complex Question

**Question:** *"What does our refund policy say about digital goods, and has it changed in the last year?"*

**Normal RAG:**
- Embeds the full question
- Retrieves top-5 chunks from the policy KB
- May get chunks about physical goods, not digital
- Has no way to retrieve change history
- Generates a potentially wrong answer

**Agentic RAG:**
```
Thought: This has two parts — current policy for digital goods,
         and historical changes. I'll retrieve separately.

Action: search(kb="policy", query="refund policy digital goods")
Observation: [Chunk: "Digital goods are non-refundable except within
              48 hours of purchase..."]

Thought: Good. Now I need to find if this changed recently.
Action: search(kb="policy_changelog", query="refund policy digital goods 2024 2025")
Observation: [Chunk: "2024-11-01: Extended digital goods refund window
              from 24h to 48h"]

Thought: I have both pieces. I can now give a complete, verified answer.
Final Answer: Current policy allows refunds on digital goods within 48 hours.
              This was extended from 24 hours in November 2024.
```

#### When to Use Each

| Use Normal RAG | Use Agentic RAG |
|---|---|
| Simple, single-topic questions | Complex, multi-part questions |
| Controlled, high-quality corpus | Mixed-quality or multi-source corpus |
| Latency is critical | Accuracy is critical |
| Budget-constrained | Quality-constrained |
| Production pipeline with known query types | Open-ended Q&A or research |

---

### 11.2 Multi-Hop Reasoning

#### What It Is

Multi-hop reasoning answers questions that **cannot be resolved from a single document or a single reasoning step**. The answer to step N depends on the result of step N-1. Each "hop" bridges a gap between a known fact and an unknown one.

```
Question → [Hop 1: retrieve/reason] → Intermediate fact
         → [Hop 2: retrieve/reason] → Intermediate fact
         → [Hop 3: retrieve/reason] → Final Answer
```

#### Classic Examples

**Example 1 — Knowledge graph traversal:**
```
Q: "Who is the CEO of the company that acquired Slack?"

Hop 1: What company acquired Slack?
       → Salesforce (acquired in 2021)
Hop 2: Who is the CEO of Salesforce?
       → Marc Benioff

Answer: Marc Benioff
```

**Example 2 — Policy + compliance:**
```
Q: "Is our product compliant with GDPR's rules on data retention
     for minors?"

Hop 1: What does GDPR say about data retention for minors?
       → Article 8: member states may lower consent age to 13;
         data must be deleted upon request regardless of age

Hop 2: What is our product's data retention policy?
       → We retain user data for 3 years after account deletion

Hop 3: Do we have a special path for minor account deletion?
       → No special path found in policy docs

Answer: Partial gap — deletion timeline may violate GDPR
        for minor accounts. Escalate for legal review.
```

**Example 3 — Financial chain:**
```
Q: "What is the credit rating of the parent company of
     the brand that makes AirPods?"

Hop 1: What brand makes AirPods? → Apple
Hop 2: What is Apple's parent company? → Apple Inc. (self)
Hop 3: What is Apple's credit rating? → AA+ (S&P)

Answer: AA+
```

#### When Multi-Hop Reasoning Is Needed

- **Knowledge base Q&A** — facts are spread across separate documents
- **Research synthesis** — connecting findings across papers
- **Legal/compliance** — trace a regulation → company policy → specific implementation
- **Medical** — symptom → diagnosis → treatment → contraindication check
- **Competitive intelligence** — company → acquisition history → technology portfolio → patent filings
- **Debugging** — error → root cause → related component → fix

#### How It's Implemented

**In RAG systems:** Retrieve → extract intermediate fact → use that fact as next query → retrieve again

**In agent systems (ReAct):** The Thought-Action-Observation loop naturally supports multi-hop — each observation feeds the next thought, which may trigger another tool call

**In CoT:** The model reasons through all hops internally, without external retrieval (only works if all facts are in the training data or context)

#### The Research Finding (From This Folder)

The paper *"Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets"* shows that a single agent with sufficient reasoning tokens often handles multi-hop better than multi-agent setups that split the hops across agents — because inter-agent communication overhead and context loss outweigh the benefits of parallelism for sequential reasoning chains. **Multi-hop is inherently sequential; multi-agent is for parallelism.**

#### Interview One-Liner
> "Multi-hop reasoning is when the answer to a question requires a chain of intermediate lookups or inferences, where each step's output becomes the next step's input. It's used whenever no single document or reasoning step can answer the question directly."

---

### 11.3 Skills vs MCP

These are often confused because both extend what an AI system can do — but they operate at completely different levels of abstraction.

#### The Core Distinction

| | Skills | MCP (Model Context Protocol) |
|---|---|---|
| **What it is** | A reusable behavioral workflow | A protocol (standard interface) for connecting tools/data to models |
| **Analogy** | An appliance (uses power to do something useful) | An electrical outlet (standard interface for power) |
| **Level** | High-level — HOW to approach a task | Low-level — WHAT capabilities are available |
| **Defines** | Sequence of steps, prompts, decision logic | Tool schemas, resource endpoints, data formats |
| **Created by** | Prompt engineers, product teams | Developers building integrations |
| **Consumed by** | The LLM following structured instructions | The LLM calling structured tool APIs |

#### MCP — What It Is

MCP (Model Context Protocol, developed by Anthropic) is a **standard protocol** for exposing tools, resources, and context to LLMs. An MCP server advertises a set of capabilities; any MCP-compatible client (Claude, an IDE plugin, an agent framework) can connect and call them.

Think of it as USB-C for AI tools — one standard connector, many devices.

**MCP provides three things:**
1. **Tools** — functions the model can call (read_file, search_db, create_issue)
2. **Resources** — data the model can access (a file, a database row, a webpage)
3. **Prompts** — pre-built prompt templates the server exposes

**MCP Examples:**

| MCP Server | Tools It Exposes |
|---|---|
| **GitHub MCP** | `create_pr`, `read_file`, `search_code`, `list_issues`, `merge_pr` |
| **Jira/Confluence MCP** | `create_issue`, `search_jql`, `get_page`, `add_comment`, `transition_issue` |
| **Filesystem MCP** | `read_file`, `write_file`, `list_directory`, `search_files` |
| **Database MCP** | `query`, `insert`, `update`, `list_tables`, `describe_schema` |
| **Slack MCP** | `post_message`, `list_channels`, `get_thread`, `search_messages` |
| **Browser MCP** | `navigate`, `click`, `extract_text`, `take_screenshot`, `fill_form` |
| **Postgres MCP** | `run_sql`, `list_schemas`, `explain_query` |

The model doesn't know (or care) that GitHub is written in Go and the DB is PostgreSQL — it just calls the tools defined by the MCP schema.

#### Skills — What They Are

A skill is a **reusable, composable behavioral workflow** — a structured set of instructions, prompts, and decision logic that defines how an agent should tackle a category of task. Skills sit on top of tools; they orchestrate tool use purposefully.

**A skill answers:** "Given this type of task, what is the right sequence of steps, what questions to ask, what format to use, how to handle errors?"

**Skills Examples:**

| Skill | What It Defines |
|---|---|
| **Email generator** | Ask for context → draft in appropriate tone → offer subject line variants → ask for revisions |
| **Code reviewer** | Read the diff → check for bugs → check for style → check for security → produce structured report |
| **PR description writer** | Read git diff → identify what changed and why → write summary, test plan, and risk section |
| **Test suite generator** | Read function → identify edge cases → write happy path, error path, boundary tests |
| **Security reviewer** | Scan for OWASP top 10 → check auth → check input validation → check secrets → produce severity-ranked report |
| **SQL query builder** | Understand the business question → infer schema → write query → explain it in plain English |

#### MCP + Skills Together

They are complementary, not competing:

```
User: "Create a Jira ticket for the bug I just described"

Skill: Bug ticket creator
  Step 1: Extract: title, description, severity, affected component
  Step 2: Look up which project this component belongs to
  Step 3: Format ticket per team's template
  Step 4: Create the ticket
  Step 5: Post link to Slack channel

Tools used (via MCP):
  - Jira MCP → searchJiraProjects(), createJiraIssue()
  - Slack MCP → postMessage()
```

The **skill** defines the workflow and decision logic. The **MCP** provides the actual tools to execute it.

#### Interview One-Liner
> "MCP is a protocol — it's the standard way external systems expose tools and data to a model, like a universal adapter. Skills are behavioral workflows — reusable sequences of steps that define how to accomplish a class of task, potentially using many MCP-connected tools. MCP is the plumbing; skills are the plumber's method."

---

### 11.4 Skill Use Cases Beyond Email Generation

Skills shine wherever a task has a **consistent structure**, **repeatable steps**, and **domain-specific quality criteria** — but the inputs vary each time.

#### Development and Engineering Skills

| Skill | What It Does | Key Steps |
|---|---|---|
| **Code reviewer** | Reviews a PR or code snippet for bugs, style, security | Read code → identify issues by category → rank by severity → suggest fixes |
| **PR description writer** | Generates a structured PR description from a git diff | Read diff → extract intent → write summary, test plan, risk section, screenshots checklist |
| **Test suite generator** | Writes comprehensive tests for a function or module | Analyze signature + docstring → enumerate edge cases → write pytest/jest suite |
| **Refactor advisor** | Identifies code smells and suggests targeted refactors | Parse code → detect patterns (long method, duplicate logic) → propose minimal refactors |
| **Commit message writer** | Writes a conventional commit message from staged changes | Read diff → identify change type (feat/fix/refactor) → write concise imperative message |
| **Dependency auditor** | Reviews package files for vulnerabilities and outdated deps | Read requirements.txt/package.json → cross-reference CVE DB → report by severity |
| **API spec generator** | Generates OpenAPI/Swagger spec from code or description | Read endpoints → infer request/response schemas → produce YAML spec |
| **Database migration writer** | Writes a safe migration script from a schema change description | Understand before/after schema → generate up + down migrations → add safety checks |

#### Documentation and Communication Skills

| Skill | What It Does |
|---|---|
| **README generator** | Reads codebase structure and generates a professional README |
| **Architecture diagram describer** | Reads infrastructure config and writes a textual architecture overview |
| **Meeting notes formatter** | Converts raw transcript or bullet points into structured action items |
| **Incident postmortem writer** | Structures a blameless postmortem from an incident timeline |
| **User story writer** | Converts feature requirements into Agile user stories with acceptance criteria |
| **Release notes generator** | Summarizes a sprint's merged PRs into customer-facing release notes |
| **Onboarding guide writer** | Reads a repo and generates a new-joiner getting-started guide |

#### Analysis and Research Skills

| Skill | What It Does |
|---|---|
| **Log analyzer** | Parses error logs, identifies patterns, clusters errors, suggests root causes |
| **SQL query builder** | Translates business questions into correct, optimized SQL |
| **Data profiler** | Summarizes a CSV/DataFrame: nulls, distributions, outliers, suggested cleanups |
| **Contract summarizer** | Extracts key clauses, obligations, deadlines, and risks from a legal document |
| **Competitive analysis builder** | Scrapes and compares competitor features, pricing, and positioning |
| **Resume screener** | Scores a resume against a job description, flags gaps, suggests interview questions |
| **Paper summarizer** | Reads an academic paper and produces: problem, method, results, limitations, relevance |

#### Security Skills

| Skill | What It Does |
|---|---|
| **Security reviewer** | Scans code for OWASP Top 10, insecure defaults, hardcoded secrets, missing auth |
| **Threat modeler** | Given a system description, generates a STRIDE threat model with mitigations |
| **Pentest report writer** | Converts raw findings into a structured pentest report with severity and remediation |
| **Secrets scanner** | Reviews a codebase or diff for accidentally committed credentials or API keys |

#### What Makes a Good Skill (Design Criteria)

A task is a good candidate for a skill when:

1. **Repeated frequently** — worth the investment in structure
2. **Has clear quality criteria** — you know what "good" looks like
3. **Consistent phases** — input gathering → analysis → output → review always follow the same arc
4. **Benefits from domain prompting** — the skill can encode expert knowledge about format, tone, common mistakes
5. **Composable** — the skill can call other skills or MCP tools as sub-steps

A task is a poor candidate when:
- It's one-off and highly unique
- The user needs to guide every decision (better as a conversation)
- The output format varies wildly per use case

---
