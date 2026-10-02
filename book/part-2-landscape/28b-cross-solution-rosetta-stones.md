# 28b. Cross-solution Rosetta stones: the same concept under every vendor's name

> **Why this chapter exists:** half of the confusion in interviews is vocabulary. A "skill" in Watson Assistant, an Alexa "skill", a Bot Framework "skill", a Rasa "skill" and a Claude "Skill" are five different things; a LangGraph "node", an ADK "agent", a Strands "tool" and an OpenAI "handoff" overlap in odd ways. These tables let you translate on the fly. Each row is one concept; each column is what a platform calls it (— means the platform has no direct equivalent).

## 28b.1 Conversational AI platforms

| Concept | Dialogflow CX / Conversational Agents | Amazon Lex V2 | Copilot Studio | Rasa (CALM) | Watson Assistant / watsonx Orchestrate | Bot Framework / Composer (legacy) | Alexa |
|---|---|---|---|---|---|---|---|
| The bot | Agent | Bot | Agent (formerly Copilot) | Assistant | Assistant | Bot | Skill (an Alexa app) |
| User meaning | Intent (training phrases) | Intent (sample utterances) | Topic trigger phrases / generative orchestration | Intent (legacy) → flows via dialogue understanding | Intent / Action trigger | Intent (LUIS/CLU) | Intent |
| Extracted value | Entity (system/custom/regex/composite/session) | Slot + slot type | Entity | Entity / slot | Entity | Entity | Slot + slot type |
| Conversation structure | Flow → Pages → Routes | Intent → slot elicitation → fulfillment | Topics (deterministic) + generative answers | Flows (YAML steps) | Dialog skill (tree) / Actions skill (steps) | Dialogs (adaptive dialogs) | Dialog model / dialog management |
| State | Page + session parameters | Session attributes, slot values | Variables (topic/global) | Slots / flow state | Context variables | Dialog state / memory scopes | Session attributes |
| Backend call | Webhook (fulfillment) | Lambda code hook / fulfillment | Actions: Power Automate flows, connectors, MCP tools, plugins | Custom actions (action server) | Webhooks / custom extensions / tools | Skills (sub-bots) and HTTP actions | Lambda / HTTPS endpoint |
| LLM-driven agent | Playbook (instructions + tools + examples) | Generative AI features (QnAIntent, assisted NLU, Bedrock agents) | Generative orchestration, autonomous agents | Dialogue understanding (CALM), enterprise search | Conversational search / AI agents in Orchestrate | — | Alexa+ LLM-based experiences |
| Knowledge/RAG | Data store | QnAIntent over Bedrock Knowledge Bases | Knowledge sources (SharePoint, websites, Dataverse) | Enterprise search policy | Search skill / conversational search | QnA Maker (legacy) → Language service | — |
| Reusable module named "skill" | — (reuse via flows/route groups) | — | — | — | Skill = a unit of an assistant (dialog, search, action skills) | Skill = a sub-bot callable from another bot | Skill = the whole voice app |
| Human handoff | Live agent handoff / Agent Assist | Connect agent transfer | Escalate to Dynamics/Omnichannel | Handoff via connectors | Service desk integrations | Handoff libraries | — |
| Telephony | Built-in via CES / partners | Amazon Connect | Dynamics 365 Contact Center | Partners | Phone integrations | Direct Line Speech | Alexa devices |
| Versioning/envs | Versions + environments, test cases | Bot versions + aliases | Environments, solutions (ALM) | Git | Versions | Source control | Skill versions |

The word **"skill"** therefore means: a whole voice app (Alexa), a sub-bot (Bot Framework), a component of an assistant (Watson), and — in the agent world — a packaged instruction set with scripts that a model loads on demand (Anthropic Agent Skills, Deep Agents SkillsMiddleware). Dialogflow CX has no "skill"; its reusable units are flows, route groups and playbooks. Ask which meaning before you answer.

## 28b.2 Agent frameworks

| Concept | LangGraph | Google ADK | AWS Strands | OpenAI Agents SDK | Microsoft Agent Framework | CrewAI | Claude Agent SDK | Deep Agents |
|---|---|---|---|---|---|---|---|---|
| The unit of logic | Node (function) in a StateGraph | Agent (LlmAgent, Sequential/Parallel/LoopAgent) | Agent | Agent | ChatAgent / workflow executor | Agent (role, goal, backstory) | The query/session with a system prompt | Deep agent (compiled graph) |
| Control flow | Edges, conditional edges | Workflow agents, callbacks | Model-driven loop; graph/swarm helpers | Loop + handoffs | Workflows (graph of executors) | Process (sequential/hierarchical), Flows | Model-driven loop | Loop + middleware |
| State | Typed state object, checkpointers | Session state, artifacts | Session manager | Session (SQLite/Redis) + context object | Thread, checkpoint | Memory modules | Session, resumable | LangGraph state + virtual filesystem |
| Tool | Tool (callable with schema) | FunctionTool, OpenAPI tool, MCP toolset | `@tool` function, MCP client | function_tool, hosted tools, MCP | plugin/function, MCP | Tool | built-in tools + custom + MCP | filesystem/todo/task tools + yours |
| Delegation | Subgraph, supervisor/swarm libs | Sub-agents, AgentTool, A2A | Agents-as-tools, swarm, graph, A2A | Handoff, agent-as-tool | Handoff, group chat, magentic | Hierarchical crew | Subagents | `task` sub-agents |
| Human-in-the-loop | interrupt() + resume | callbacks / confirmations | hooks | tool approval callbacks | human-input executors | human input flag | permission modes, hooks | interrupts via LangGraph |
| Memory | Store (long-term), checkpoints (short) | Memory service, Memory Bank | AgentCore Memory, session | sessions | memory in threads/stores | memory | memory files, Skills | MemoryMiddleware (AGENTS.md) |
| Tracing | LangSmith / OTel | OTel / Cloud Trace | OTel | built-in traces | OTel GenAI | built-in | hooks + OTel | LangSmith / OTel |
| Hosting | LangSmith Deployment (formerly LangGraph Platform) / self | Agent Engine / Cloud Run | AgentCore Runtime or Harness / Lambda / EKS | self | Foundry Agent Service (hosted agents) | CrewAI AMP / self | self / Claude Managed Agents | self / LangSmith Deployment |

## 28b.3 Model APIs

| Concept | Anthropic Messages API | OpenAI (Responses/Chat) | Gemini API / Vertex | Bedrock Converse | Azure AI Foundry Models |
|---|---|---|---|---|---|
| Instruction channel | `system` | `instructions` / developer message | `system_instruction` | `system` | same as the underlying model API |
| Tool definition | `tools` with JSON schema; `tool_use` / `tool_result` blocks | `tools`/functions; `function_call` outputs | `tools` with function declarations | `toolConfig`/`tools` | per model |
| Forcing a tool | `tool_choice: any / tool` | `tool_choice` | `tool_config.function_calling_config.mode` | `toolChoice` | per model |
| Structured output | JSON schema via tool or output format | `response_format` / structured outputs | `response_schema` / `response_mime_type` | model-dependent | per model |
| Reasoning control | `thinking` with budget_tokens / effort (adaptive on current frontier models) | `reasoning.effort` | `thinking_config` (thinking budget on 2.5; `thinking_level` minimal/low/medium/high on Gemini 3) | `additionalModelRequestFields` | per model |
| Reasoning state across turns | thinking blocks must be passed back unmodified during tool use | reasoning items (or `previous_response_id`) | thought signatures must be returned in stateless multi-turn and function calling | as the underlying model | per model |
| Sampling controls | `temperature`/`top_p`/`top_k` rejected (400) at non-default values on Claude 4.7 and later | `temperature` unsupported on GPT-5-family reasoning models (GPT-5.1+ only at reasoning effort `none`) | supported, but Google recommends keeping Gemini 3 at the default 1.0 (lower values can cause looping) | as the underlying model | per model |
| Prefix caching | `cache_control` on blocks (5 min / 1 h) | automatic prompt caching | implicit caching (automatic) plus explicit cache objects | prompt caching | per model |
| Batch | Message Batches API | Batch API | Batch prediction | Batch inference | Batch |
| Server-side tools | web search, web fetch, code execution, computer use, MCP connector | web search, file search, code interpreter, computer use, MCP | Google Search grounding, code execution, URL context | Knowledge Bases, Guardrails | Bing grounding, file search, code interpreter |
| Files | Files API | Files API | File API | S3 | Files |
| Agent harness | Claude Agent SDK / Managed Agents | Agents SDK | ADK / Agent Engine | Strands / AgentCore | Agent Framework / Agent Service |

## 28b.4 Protocols

| Concept | MCP | A2A | OpenAPI tools | Native function calling |
|---|---|---|---|---|
| Unit | Tool, Resource, Prompt (server primitives) | Agent Card, Task, Message, Artifact | Operation | Function schema |
| Discovery | `tools/list`, `resources/list`; `server/discover` from the 2026-07-28 revision | `/.well-known/agent-card.json` (the pre-0.3 path was `agent.json`) | spec document | none (in code) |
| Transport | stdio, streamable HTTP (responses may stream as SSE; stateless from 2026-07-28) | v1.0 bindings: JSON-RPC, gRPC, HTTP+JSON; SSE streaming; webhook push notifications | HTTP | in the model request |
| Long-running work | tasks (experimental in 2025-11-25; an extension in 2026-07-28) | task lifecycle (submitted, working, input-required, auth-required, completed, failed, canceled, rejected) | async patterns per API | your code |
| Auth | OAuth 2.1 with protected-resource metadata; Client ID Metadata Documents preferred over dynamic registration | security schemes declared on the card (OAuth, API keys, mTLS) | per API | n/a |
| Who talks | model client ↔ tool server | agent ↔ agent | agent ↔ API | model ↔ your code |
| Governance | gateways, registries (official MCP Registry, AWS Agent Registry) | registries, Agentic AI Foundation | API gateways | your code |

Two neighbouring protocols complete the picture: **AG-UI** (agent ↔ front end: a stream of typed events such as text deltas, tool-call start/end and state snapshots, adopted by CopilotKit and AgentCore) and the commerce/payment protocols (ACP, AP2, UCP, x402, MPP; chapter 23).

## 28b.5 Retrieval and vector stores

| Concept | pgvector | Pinecone | Qdrant | Weaviate | Milvus | Elasticsearch/OpenSearch | Azure AI Search | Vertex AI Search / Vector Search | Databricks Vector Search (AI Search since June 2026) |
|---|---|---|---|---|---|---|---|---|---|
| Container | table + index | index + namespace | collection | collection (class) | collection + partition | index | index | data store / index + deployed index | index (Delta-synced or direct) |
| Record | row | vector + metadata | point + payload | object + properties | entity | document | document | document / datapoint | row |
| Filter | `WHERE` | metadata filter | payload filter | `where` | `expr` | `bool.filter` | OData `$filter` | restricts / filters | `filters` |
| Hybrid | tsvector + vector | sparse-dense | sparse vectors + fusion | built-in `hybrid` | sparse + dense | `knn` + `match` + RRF | vector + text + semantic ranker | built-in | hybrid |
| Compute unit | your Postgres | serverless RU/WU | nodes | nodes | nodes | nodes | search units | nodes/queries | DBUs |

## 28b.6 Observability and evaluation

| Concept | OpenTelemetry (GenAI) | LangSmith | Langfuse | Arize Phoenix | MLflow Tracing | Datadog LLM Obs |
|---|---|---|---|---|---|---|
| Request tree | trace | trace/run | trace | trace | trace | trace |
| Unit of work | span (`invoke_agent`, `chat`, `execute_tool`, `retrieval`) | run (chain/llm/tool/retriever) | observation (span/generation/event) | span (OpenInference kinds) | span | span |
| Model call | `chat` span with `gen_ai.*` | LLM run | generation | LLM span | LLM span | LLM span |
| Content | opt-in event | inputs/outputs | input/output | attributes | inputs/outputs | prompt/completion |
| Eval dataset | — | dataset + experiments | dataset + runs | datasets + experiments | evaluation datasets | — |
| Judge | your code / vendor evaluators | evaluators | evaluators | evals | `mlflow.evaluate`, Agent Evaluation judges | quality checks |

## 28b.7 MLOps objects

| Concept | MLflow | Vertex AI | SageMaker | Azure ML / Foundry | Databricks |
|---|---|---|---|---|---|
| Experiment / run | experiment, run | experiment, run | experiment, trial | job, run | MLflow experiment |
| Registered model | registered model, version, alias | Model Registry model + version | Model Package Group / Package | registered model + version | Unity Catalog model |
| Pipeline | Projects/recipes (or Airflow) | Vertex Pipelines (KFP) | SageMaker Pipelines | Azure ML pipelines | Lakeflow Jobs |
| Feature store | — | Vertex Feature Store | SageMaker Feature Store | Azure ML feature store | Databricks Feature Store |
| Endpoint | model serving (Databricks) | Endpoint | Endpoint | Online endpoint | Model Serving endpoint |
| Monitor | — | Model Monitoring | Model Monitor | Data drift monitor | Lakehouse Monitoring |
| Prompt registry | MLflow Prompt Registry | Vertex prompt management | Bedrock Prompt Management (versioned prompts with variables) | Foundry prompt flow (legacy)/evals | MLflow |

## 28b.8 Data platform units and names

| Concept | Databricks | Snowflake | BigQuery | Fabric | AWS |
|---|---|---|---|---|---|
| Governance catalog | Unity Catalog (catalog.schema.table) | Horizon (database.schema.table) | Dataplex / datasets (project.dataset.table) | OneLake + Purview | Glue Catalog / Lake Formation |
| Compute unit | DBU | credit | slot / bytes scanned | capacity unit (CU) | instance-hours / DPU |
| Serverless SQL | SQL warehouse | virtual warehouse | serverless by default | Warehouse / SQL endpoint | Athena / Redshift Serverless |
| Table format | Delta (+ Iceberg via UniForm) | native + Iceberg | native + BigLake Iceberg | Delta | Iceberg (S3 Tables), Hudi, Delta |
| LLM in SQL | `ai_query`, AI Functions | Cortex AI Functions (`AI_COMPLETE`, `AI_CLASSIFY`, `AI_FILTER`, `AI_AGG`) | `AI.GENERATE`, `AI.GENERATE_TABLE`, `ML.GENERATE_TEXT` | AI functions | Redshift ML / Bedrock integration |
| Vector search | AI Search (formerly Vector Search) | Cortex Search | `VECTOR_SEARCH` | — (Azure AI Search) | OpenSearch / Aurora pgvector / S3 Vectors |
| Semantic layer | Unity Catalog metric views | semantic views (Cortex Analyst) | Looker (LookML) semantic layer | Power BI semantic models, Fabric IQ ontology (preview) | — (dbt, or Quick Sight topics) |
| Agent front end | Genie | Snowflake Intelligence | BigQuery data agents / Gemini Enterprise | Fabric data agents | Amazon Quick (formerly QuickSight and Quick Suite) |

## 28b.9 Cloud AI service equivalents (beyond LLMs)

| Need | AWS | Azure | Google Cloud |
|---|---|---|---|
| Speech-to-text | Transcribe | Azure AI Speech | Speech-to-Text (Chirp) |
| Text-to-speech | Polly | Azure AI Speech | Text-to-Speech |
| Speech-to-speech model | Nova Sonic | GPT realtime on Foundry | Gemini Live |
| Document OCR/extraction | Textract | Document Intelligence | Document AI |
| Vision | Rekognition | Azure AI Vision | Vision AI / Vertex vision models |
| Translation | Translate | Translator | Translation AI |
| Content safety | Bedrock Guardrails, Comprehend | Content Safety, Prompt Shields | Model Armor, safety settings |
| PII detection | Comprehend, Macie | PII detection, Purview | Sensitive Data Protection (DLP) |
| Search/RAG | Bedrock Knowledge Bases and Bedrock Managed Knowledge Base, OpenSearch (Kendra: maintenance mode from 30 June 2026, closed to new customers from 30 July 2026, AWS recommends the Managed Knowledge Base) | Azure AI Search, Foundry IQ | Search (formerly Vertex AI Search), RAG Engine |
| Contact center | Connect + Lex + Q | Dynamics 365 Contact Center + Copilot Studio | Customer Engagement Suite (Conversational Agents, Agent Assist) |
| Enterprise assistant | Amazon Quick (Amazon Q Business is closed to new customers as of 2026; AWS points to Quick) | Microsoft 365 Copilot | Gemini for Workspace / Gemini Enterprise (formerly Agentspace) |
| Managed agents | Bedrock Agents, AgentCore Runtime and Harness | Foundry Agent Service (hosted agents) | Agent Engine (Gemini Enterprise Agent Platform) |
| Agent identity | IAM roles + AgentCore Identity (OAuth vault, OBO) | Entra Agent ID | Agent Identity |
| Agent registry / governance | AWS Agent Registry | Agent 365, Foundry Control Plane | Agent Registry |
| Tool gateway | AgentCore Gateway | API Management AI gateway, Foundry tools | Agent Gateway, Apigee |

## 28b.10 Model-training vocabulary across labs

| Concept | Generic | Also called |
|---|---|---|
| Instruction tuning | SFT | supervised fine-tuning, behaviour cloning |
| Preference optimization | RLHF / DPO | alignment, preference tuning, RLAIF (AI feedback) |
| Verifiable-reward RL | RLVR / GRPO | reasoning RL, outcome-reward RL, reinforcement fine-tuning (RFT, the managed-service name at OpenAI, Bedrock and Foundry) |
| Compression | distillation | strong-to-weak training, teacher–student, synthetic-data training |
| Adapter tuning | LoRA / PEFT | adapters, delta weights |
| Extended thinking | reasoning / thinking tokens | chain of thought, test-time compute, thinking budget, reasoning effort |

When an interviewer uses a term you half-recognize, map it to the row, say the generic name, and answer in that vocabulary — it signals breadth without pretending to know their specific product.
