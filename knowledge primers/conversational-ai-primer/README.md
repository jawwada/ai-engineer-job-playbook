# Conversational AI Primer: Dialogflow CX in depth, with LangChain and LangGraph as the alternative

A 91-page primer on building conversational assistants, written for an engineer who has to design one for a client or defend one on a whiteboard. Google's **Dialogflow CX** (now surfaced inside the Conversational Agents console with its generative playbooks) is covered as the main platform; **LangChain and LangGraph** are covered as the LLM-first alternative; and a decision guide explains how to choose between them and how most enterprises combine them. Every build is accompanied by working code.

## Files

| File | What it is |
|---|---|
| `Conversational AI Primer - Dialogflow CX in Depth, with LangChain and LangGraph as the Alternative.md` | The primer in Markdown, with the four diagrams linked from `images/` |
| `Conversational AI Primer - Dialogflow CX in Depth, with LangChain and LangGraph as the Alternative.pdf` | The same document as a 91-page US-letter PDF |
| `images/conversational-system-parts.png` | The seven parts of a conversational system, and how CX and LangGraph fill each |
| `images/dialogflow-cx-object-model.png` | The Dialogflow CX object model: agent, flows, pages, handlers, agent-wide resources |
| `images/clinic-assistant-langgraph.png` | The clinic assistant as a LangGraph: understand, decide, seven actions, END |
| `images/hybrid-cx-langgraph.png` | The CX-front, LangGraph-behind-a-webhook hybrid |

## Contents

**Part I — Foundations.** 1. What conversational AI is, and the three generations (rule-and-intent, hybrid, LLM-first) with a vocabulary table mapping each term to its CX and LangGraph names. 2. Anatomy of a conversational system (seven parts) and the design principles that survive every generation.

**Part II — Dialogflow CX.** 3. The mental model: agents, flows, pages, state handlers, intents, entities, parameters, sessions, fulfillment, one turn step by step. 4. Concepts in depth: condition syntax, routes and route groups, the event catalogue, forms and reprompts, the webhook contract with JSON examples, versions and environments, settings that bite. 5. Generative features: generators, generative fallback, data stores, playbooks (routine and task) and tools (OpenAPI, data store, function, connector, Code Interpreter), with 2026 pricing. 6. Worked build: a clinic appointment and order-status agent, from conversation design to a deployable FastAPI webhook. 7. Programmatic CX: the Python client, agent export and restore, Terraform, a release pipeline. 8. Testing, NLU tuning, analytics (a BigQuery containment query), speech and telephony, IAM, quotas, operations. 9. Conversation design patterns and anti-patterns, with a review checklist.

**Part III — The LLM-first alternative.** 10. Why LangChain and LangGraph, the mental model, and a what-replaces-what table. 11. LangGraph fundamentals with code: state and reducers, checkpointers and threads, `interrupt()` and `Command`, streaming, `create_agent` with middleware, subgraphs, durable execution. 12. Worked build: the same clinic assistant in LangGraph (policy in edges, confirmation as an interrupt, FastAPI adapter, tests). 13. Worked build: a voice-first drive-through ordering agent (menu as data, upsell rules, read-back, POS) in both CX and LangGraph, with the speech pipeline. 14. Worked build: a prediction-market conversational agent for Kalshi and Polymarket (exchange adapters, risk policy, quoting, human-in-the-loop order placement, compliance guardrails, a refusal eval suite). 15. Production concerns: guardrails, evaluation, observability, latency and cost, deployment, a launch checklist.

**Part IV — Choosing, combining, talking about it.** 16. The decision table, four hybrid patterns, migration paths, other frameworks, a one-paragraph recommendation. 17. Interview talking points and the author's own experience (Dialogflow CX at Noctal, an intent-classification chatbot at E.ON, agentic HITL workflows at Capital Group). Appendix: glossary, full webhook request and response examples, sources.

## How it was built

Written on 17 October 2026 as a Claude Doc from the Google Cloud documentation for Conversational Agents (Dialogflow CX), the LangChain and LangGraph 1.x documentation, the venues' API documentation for section 14, and the author's engagement history; the pages consulted are listed in the appendix with the as-of date. Product names, model lists, pricing and the prediction-market regulatory picture change quickly; appendix A.4 lists which sections to re-check before relying on them.

Related chapter in the book: the conversational and voice AI chapter in the interview-preparation part, and `knowledge primers/dialogflow_cx_applied_ai_field_guide.pdf`.
