# 39c. The role-related-knowledge interview, part two: Dialogflow CX background, the drive-through and prediction-market use cases, the Applied AI team context, and the communication playbook

> Companion to 39b. The interviewer's team builds for customers; the use cases they name — a drive-through voice agent, prediction-market operators such as Kalshi and Polymarket — are the kind of engagements an Applied AI / Forward Deployed Engineer leads. They will probe conversational-AI depth (Dialogflow CX / Conversational Agents), ask you to reason about those use cases in detail, and judge how you communicate: specific, structured, owning the outcome. This chapter prepares all three.

---

## 39c.1 Dialogflow CX / Conversational Agents: the questions and the answers

### "Explain Dialogflow CX to me as if I were going to build on it tomorrow."
"Dialogflow CX — built today in the Conversational Agents console, which replaced the Dialogflow CX console; part of what Google now sells as Gemini Enterprise for Customer Experience (the Customer Engagement Suite until January 2026); documented next to its ADK-based evolution, CX Agent Studio; and able to call custom agents hosted on the Agent Platform — models a conversation as a state machine. An *agent* contains *flows*; each flow is a graph of *pages*; a page is a state that greets, collects *parameters* through slot filling with reprompts, and defines *routes* — transitions fired by an *intent* match, a *condition* on session parameters, or both — with *fulfillment* (messages, parameter presets, or a *webhook* call to my backend) and a target page or flow. *Intents* are trained from phrases and scoped by where they are referenced; *entities* type the values — system entities like dates, custom entities with synonyms, regex and composite entities, and *session entities* I inject at runtime for a per-store catalog. *Event handlers* cover no-input, no-match and custom events. The generative layer sits on the same graph: *generators* run an LLM prompt inside fulfillment, *data stores* answer from documents and websites with grounding and citations, *playbooks* are goal-driven LLM agents with instructions, examples and tools that a flow can invoke and that can hand control back, and *generative fallback* handles no-match. Operationally: versions and environments, test cases with golden transcripts, the API for CI, conversation history, Customer Experience Insights (formerly Conversational Insights) and analytics, Agent Assist for human agents, built-in telephony with Google speech, DTMF and barge-in, multilingual agents, and the Messenger web widget. The webhook contract is what makes it an application platform: my FastAPI service receives the session, page, intent and parameters, runs business logic, and returns messages, parameter updates or a redirect."

### "When would you use flows versus playbooks?"
"Flows for anything that must be exact and auditable: identity verification, payments, order confirmation, regulated disclosures, escalation rules. Playbooks for open-ended understanding and tasks where a state machine would explode: answering questions from documents, handling mixed intents, gathering loosely structured information, deciding which tool to call. The production pattern is a flow skeleton that invokes playbooks at the open points and takes control back for the transactional steps. I measure fallback rate, containment and task completion per flow and per playbook, and I move a step from playbook to flow when its failure cost rises."

### "How do you test and release a CX agent?"
"Test cases with golden transcripts run in CI through the API on every change; versions deployed to environments (draft, staging, prod) with a rollback; conversation-history review and Insights for drop-offs and no-match clusters; a weekly triage that turns no-match utterances into training phrases or playbook examples; for generative parts, simulated users and judge sampling on transcripts; webhook latency and error rates in Cloud Monitoring because they sit inside the user's turn."

### "What are the hard parts people underestimate?"
"Intent scope collisions ('yes' means different things on different pages — scope by page and use route groups for global intents), parameter validation (entity types are not validation; validate in the webhook), no-match ladders (rephrase → options → human), session-parameter sprawl, webhook latency, multilingual quality drift, cost by session and request at scale, and the handoff payload for human agents — summary, parameters and transcript — which has to be designed, not improvised."

### "How does CX fit with Gemini and the Agent Platform?"
"Playbooks and generators call Gemini models; data stores are Agent Search (formerly Vertex AI Search) data stores; ADK agents on Agent Runtime are reachable from a playbook through tools (OpenAPI or function tools) or A2A; Agent Assist and Customer Experience Insights (formerly Conversational Insights) use the same models for human agents. Security: Sensitive Data Protection redaction, CMEK, data residency, IAM on agents, audit logs. And the direction of travel: CX Agent Studio, the ADK-based evolution of Dialogflow CX inside Gemini Enterprise for Customer Experience, builds agents from instructions, tools, callbacks and guardrails, and can hand a conversation to an existing CX flow as a flow-based agent — so a flow skeleton built today is not wasted."

### Sample mini-design the interviewer may ask for
"An appointment-rescheduling agent: Flow 'Reschedule' with pages Identify (parameters: phone, DOB; webhook verifies), SelectAppointment (session entity of the caller's appointments injected by the webhook), ChooseSlot (parameters: date, time; webhook checks availability), Confirm (explicit yes; webhook commits; no-match ladder), and a global route group for 'agent', 'cancel', 'repeat'. A playbook handles 'what should I bring' and 'how long does it take' from a data store. Telephony through Google's built-in telephony (CES telephony, in the old naming) or a partner such as Twilio or AudioCodes, with barge-in; Agent Assist for the human queue. Metrics: completion rate, average turns, fallback rate, webhook p95."

### The resume story in one breath
"At a creative-AI start-up I built the conversational layer in Dialogflow CX — flows and pages for navigation and account actions, intents and entities for commands, webhook fulfillment to the FastAPI backend that triggered our agentic workflows and returned results into the chat, generative fallback for open requests — so users had deterministic UX for exact things and the agent for everything else."

### Critic's additions: the limits, the webhook contract, the playbook tool types, and nine more follow-ups

**The numbers that prove you have built on it (current published limits; check the quotas page before the interview).** 50 flows per agent, 250 pages per flow, 10,000 intents per agent, 2,000 training phrases per intent per language (768 characters each), 250 entity types per agent, 20 parameters per page, 100 route groups per flow, 50 playbooks per agent. Webhook timeout default 5 seconds and maximum 30 seconds per attempt, one automatic retry on transient failure (so plan for up to twice the timeout), webhook response at most 64 KiB. Sessions expire 30 minutes after the last request. Audio input at most 120 seconds per request; text input for non-generative intent matching at most 256 characters. Runtime quotas: 1,200 text requests and 600 audio requests per minute per project, 600,000 generative tokens per minute, 60 design-time writes per minute. The number an interviewer actually tests you on is the webhook timeout, because it sits inside the user's turn.

**The webhook contract, field by field.** Request: the session (`sessionInfo.session` and `sessionInfo.parameters`), the fulfillment tag you set (`fulfillmentInfo.tag`, so one service can route many pages), the page (`pageInfo` with its form parameters and their state), the matched intent and its confidence (`intentInfo`), the language, the user's text or transcript, and any `payload` the channel added. Response: `fulfillmentResponse.messages` (text, rich payloads, telephony actions), `sessionInfo.parameters` to set or clear state, and `targetPage` or `targetFlow` to redirect. Failures fire `webhook.error` and `webhook.error.timeout` events that you handle on the page, flow or agent level — the handler says "I'm still working on that" and offers a path, never silence. Authentication options: service-agent ID tokens for Cloud Run, service-account access for Google APIs, mutual TLS, basic or header auth, and Service Directory for private networks. Flexible webhooks let you define your own request and response fields when the standard envelope is wrong for an existing API.

**Playbook tool types.** OpenAPI tools (your backend, described by a schema; the playbook calls them), data store tools (grounded answers from an Agent Search data store with citation and grounding-confidence settings), function tools (executed on the client side and returned to the playbook — right for actions the browser or app must perform), and connector tools (Integration Connectors to SaaS and databases). A playbook has a goal, instructions, examples (golden conversations that steer behaviour the way training phrases steer intents), parameters and tools; a routine playbook orchestrates and a task playbook does one job and returns.

**Nine more follow-ups.**
- *"'Yes' means different things on different pages — how do you keep it from matching the wrong route?"* — Intent scoping: an intent is only matchable where it is referenced — by a route on the current page, on the flow's start page, or in a route group attached there; put `confirm.yes` only on confirmation pages, keep global intents (`cancel`, `agent`, `repeat`) in a flow-level route group, and test it with a test case that says "yes" on a page where it must not transition.
- *"How does the webhook know who the user is?"* — Identity is a session parameter set by the channel or by an authentication step (a verified phone number, an OIDC token passed in the request `payload`), never a parameter the NLU fills from speech; the webhook validates it and your backend enforces permissions against it — the same data-layer rule as chapter 39b.5.
- *"The user says 'two of those and cancel the drink' in one utterance."* — Multi-intent utterances are the limit of intent matching; in a flow you handle them with a parameter-collection page that accepts a list entity and a composite entity for modifiers, or you route the whole utterance to a playbook or an LLM step that emits structured operations, and the flow applies them one by one with read-back.
- *"How do you release a change to a live agent safely?"* — Versions are immutable snapshots of a flow; environments (draft, staging, prod) pin versions; test cases run through the API in CI against the draft; experiments split traffic between two versions in an environment and report completion and no-match; rollback is repointing the environment to the previous version, which takes seconds.
- *"What does 'containment' mean precisely in your reports?"* — Sessions that reach a defined success page (order confirmed, question answered with a grounded response) without a live-agent transfer, divided by all sessions; report it next to the no-match rate per page and the transfer rate per reason, because a bot that never transfers and never completes also has high containment.
- *"How do you adapt speech recognition to your vocabulary?"* — Speech adaptation on the agent or per page: phrase sets with boost values for menu items, product names and the words an IVR hears most, custom classes for enumerations, and per-page hints so "two" is boosted on a quantity page; measure word-error rate on your own recordings before and after.
- *"What are the speech-timing settings you would touch first?"* — End-of-speech sensitivity and the no-speech timeout (short for quantity prompts, longer for open questions), barge-in on or off per page (off during a legal disclosure, on everywhere else), and DTMF as a fallback for digits.
- *"How do you keep a playbook from inventing a policy?"* — A data-store tool with a grounding threshold so ungrounded answers are not spoken, instructions that forbid answering policy questions without a tool result, examples that demonstrate the refusal, and judge sampling of generative turns for groundedness; the deterministic flow still owns anything with money attached.
- *"What is the handoff payload?"* — A summary written by a generator, the collected parameters, the transcript, the reason code for the transfer, and the last page — delivered to Agent Assist or the contact-center platform so the human does not restart the conversation; measure it with the repeat-information rate after transfer.

### Critic's additions: CX Agent Studio — what carries over from Dialogflow CX, and five more follow-ups

A Google interviewer in late 2026 may say "Dialogflow", "Conversational Agents", "CES" or "CX Agent Studio" for the same job. Customer Experience Agent Studio is documented as the evolution of Dialogflow CX: a low-code builder built on ADK, inside Gemini Enterprise for Customer Experience, with Dialogflow CX still documented (as the legacy conversational-agents product) for existing agents. The skill transfers if you can map it:

| Dialogflow CX concept | CX Agent Studio counterpart | What to say about it |
|---|---|---|
| Playbooks (goal, instructions, examples) | Agents with instructions (the builder can restructure them into XML for the model) and sub-agents | the open, goal-driven parts |
| Flows and pages for exact paths | Flow-based agents (an existing CX flow runs through `DetectIntent` until `END_SESSION`, then control returns) and handoff rules | keep money, identity and disclosures deterministic; treat each flow as a black box with explicit input and output parameters, and avoid ping-ponging control between flows and LLM agents |
| Route conditions on session parameters | Handoff rules on variables (text, number, boolean) or in Python with `CallbackContext` (`callback_context.variables[...]`) | deterministic transfers between parent and child agents |
| Session parameters | Variables | the conversation's state |
| Webhooks, OpenAPI tools, data-store tools | Tools: OpenAPI, Python code, data stores, Google Search and Maps, Salesforce, ServiceNow, Jira, Confluence, SharePoint, Integration Connectors, MCP, system tools | the backend contract lives here |
| Validation and redaction in the webhook | Callbacks in Python: before and after agent, model and tool | a `before_tool_callback` can skip a tool by returning a result, an `after_model_callback` can redact; they run in a sandbox without private-network access |
| Generative fallback, safety settings | Guardrails: Prompt Guard, Blocklist (words or regex, on input or output), Safety (Relaxed, Balanced, Strict), custom rules, supervisor agents (audio quality, missed tool call); outcomes "say exactly", hand off, or generate | content controls, not authorization |
| Test cases, experiments | Evaluations with test cases and AI-assisted test-case refinement | still gate releases from CI |
| Versions and environments | Versions with changelogs and rollback | same release discipline |
| Built-in and partner telephony | Bidirectional-streaming voice; channels including Google's telephony platform, Google Cloud CCaaS, Twilio, AudioCodes, Five9, SecureCo, WhatsApp and Instagram | latency is the selling point |

The sentence that connects your background to it: "I built on Dialogflow CX; the same design moves to CX Agent Studio — the flows that carry money or identity become flow-based agents, the generative parts become LLM agents with tools, the webhook logic becomes tools, and cheap checks move into callbacks."

**Five more follow-ups.**
- *"Would you migrate a working Dialogflow CX agent now?"* — Not as a big bang. Put a CX Agent Studio root agent in front, call the existing transactional flows as flow-based agents, move the open-ended parts first, and compare containment, no-match and task completion per path on the same traffic split before moving anything with money attached.
- *"CX Agent Studio advertises truly asynchronous tool calls. What problem does that solve?"* — The webhook timeout problem: in Dialogflow CX a slow backend means a 5-second default (30-second maximum) timeout and a `webhook.error.timeout` event; asynchronous tools let the agent keep talking while the backend works. You still need idempotent tools and a status the agent can report.
- *"Where does validation go now?"* — Authoritative validation in the tool service and the data layer; cheap pre-checks and caching in `before_tool_callback`; never only in instructions. Callbacks cannot reach private networks, so anything that needs an internal system belongs in a tool.
- *"How do CX Agent Studio guardrails relate to Model Armor?"* — Guardrails are per-agent conversation controls with an outcome (a fixed response, a handoff, or a regenerated response); Model Armor is a platform-wide screening service with organization-level floor settings. Use the guardrails for conversation behaviour and Model Armor where policy must be uniform across agents; neither authorizes data access.
- *"Shopping and Food Ordering agents exist. When would you build instead?"* — When the customer's catalog, modifier grammar, back-end integration or measurement needs exceed what the productized agent exposes; decide in discovery with a short proof on recorded traffic rather than by preference.

---

## 39c.2 Use case: the drive-through voice agent (the Applied AI version)

Google's own reference here is the work with a major quick-service chain on a drive-through voice assistant; the industry's mixed results (a large chain ending a multi-year pilot in 2024; viral prank failures elsewhere; vendors like SoundHound, Presto and Hi Auto in the market) are the backdrop. Answer with requirements, a layered architecture, the failure modes with their mitigations, and the measurement plan — chapter 41 has the long form.

**Requirements you state first.** 95%+ structured-order accuracy; first response under a second; barge-in; per-store menus, dayparts and promotions; POS integration; crew takeover at any moment; works with engine noise; no personal data collected.

**Architecture on Google Cloud.** Microphone array with echo cancellation and noise suppression at the edge → streaming speech recognition (Chirp models via Speech-to-Text, custom vocabulary with boosted menu items) or a speech-to-speech path (Gemini Live) → understanding that emits *structured order operations* constrained to the catalog (Gemini Flash with a response schema and session entities for the menu; or CX playbooks with tools) → a deterministic order state machine (a CX flow or a service on Cloud Run) that validates against the catalog and rules, applies promotions, handles corrections, caps quantities, and requires explicit confirmation → streaming TTS with short confirmations → POS/KDS integration with idempotent order creation → crew tablet with live order and takeover → telemetry (per-stage latency, ASR confidence, interventions) in Cloud Monitoring and traces → evaluation on a corpus of real and simulated audio (accents, noise, interruptions, pranks) with gold orders, shadow mode before go-live, A/B by store.

**Failure modes → mitigations.** Noise: edge audio processing, confidence-based confirmation. Accents and dialects: adapted ASR, n-best alternatives into understanding, clarification on low confidence. Complex customizations: catalog-constrained extraction, explicit modifier grammar, "did you mean" on ambiguity. Pranks and absurd quantities: hard caps and sanity rules in the state machine, early crew handoff. Compounding errors: the state machine models corrections ("no, make that two" edits the last operation) and reads back before commit. Upsell annoyance: one rules-based prompt, never generative monologues. Latency: streaming at every stage, speculative understanding on partial transcripts, first audio within ~800 ms.

**Measurement.** Order accuracy on structured orders (not transcripts), completion without crew, latency percentiles per stage, interruption recovery, false-confirmation rate, cost per order, crew-intervention rate; dashboards per store; a kill switch to crew-only.

**The sentence that shows ownership.** "I'd start in shadow mode at two stores, publish the accuracy and latency numbers weekly, and gate expansion on order accuracy and crew-intervention rate — the failures in the news were measurement and handoff designed last."

### Critic's additions: Google's 2026 product context, the architecture decision with current names, the rollout gates, and ten follow-ups

**The product context to know.** In January 2026 Google Cloud folded an enhanced Food Ordering agent into Gemini Enterprise for Customer Experience, explicitly "building on its drive-thru success with fast food retailers"; at Next '26 the Shopping and Food Ordering agents were positioned for direct and third-party chat and digital channels, alongside an Omnichannel Gateway that keeps context across web, mobile and voice. So the first question in a customer engagement is not "how do I build a voice agent" but "does the productized agent fit this chain's menu, POS and measurement, or do we build on CX Agent Studio or ADK with the Live API?" — and the answer comes from a two-week proof on recorded lane audio.

**The architecture decision, said with current names.**

| | Cascaded | Speech-to-speech |
|---|---|---|
| Path | Chirp 3 streaming recognition (`chirp_3`, up to 1,000 adaptation phrases, built-in denoiser) → Gemini Flash with a response schema of order operations → order state machine (a Cloud Run service or a flow-based agent) → Chirp 3 HD or Gemini TTS → POS | Gemini Live API (a current Live model) with tools for catalog lookup and order operations; VAD, barge-in and transcription built in |
| Latency | more hops; under one second only with streaming, speculative understanding and pre-synthesized confirmations | lowest; first audio in a few hundred milliseconds after end of speech |
| Control and evidence | a transcript, a structured operation and an audio clip per turn; every stage loggable and screenable | transcripts via `input_audio_transcription` and `output_audio_transcription`; less control over each stage |
| Cost per order (chapter 41's arithmetic) | about 4–5 cents at list prices | about 6–9 cents, rising with the number of turns because the session context is re-billed every turn |
| Where it fits | chains that need audit, per-stage tuning and the lowest cost | chains that prize naturalness and can keep the menu behind a tool |

Either way the order operations stay structured and validated outside the model; that sentence matters more than the choice.

**Two documented caveats that change the design.** Chirp 3's word-level confidence "isn't truly a confidence score" (Google's documentation), so do not trigger confirmations from ASR confidence; use order-level signals instead — an ambiguous catalog match, disagreement between two candidate parses, a modifier the item does not allow, a second clarification. And its denoiser cannot remove background human voices, so passengers and the adjacent lane are handled by the microphone array's beamforming and by an "is this addressed to the order point?" check, not by the recognizer.

**Rollout gates, with numbers.** Shadow mode at two stores for two weeks (the agent listens and builds an order; the crew takes the real order; compare the agent's structured order with the final POS ticket): at least 2,000 orders, exact-match order accuracy at least 95% (about ±1 point at that sample size), false confirmations at most 0.5%, p95 time from the end of the customer's speech to the agent's first response under one second (the requirement), measured per daypart. Then live at the same two stores with the crew monitoring: crew-intervention rate at most 10% and falling week over week. Then twenty stores chosen for noise, accents and dayparts, then the fleet, with a per-store kill switch and a weekly scorecard per store.

**Ten follow-ups.**
- *"A passenger shouts an item from the back seat."* — Beamforming toward the driver's position, an addressee check before applying an operation, and the read-back before commit; anything unclear becomes one clarifying question, never a silent add.
- *"Someone orders 1,000 waters."* — Caps in the state machine, not in the prompt: a per-item maximum, an order-total maximum and a pattern rule for absurd orders that hands off to the crew with the partial order shown on the tablet.
- *"A customer asks whether the sauce contains nuts."* — Never generated: route to the crew or to a deterministic allergen data tool with a fixed, legally reviewed script, and log the question.
- *"The POS is down."* — Queue the order with an idempotency key, tell the customer to confirm at the window, show it on the crew tablet, and alert; automatic switch to crew-only mode if the POS stays down for more than a minute.
- *"Half the lane speaks Spanish."* — Language detection on the first utterance or a per-lane setting, a separate evaluation set and gate per language, and an earlier handoff threshold for the language with less data.
- *"Breakfast ends at 10:30."* — The catalog version (store and daypart) is part of the session state and of the response schema's allowed item ids, so the model cannot emit an item that is not on sale; test the switch minute explicitly.
- *"How do you measure accuracy without listening to everything?"* — Compare the agent's structured order with the final POS ticket; any crew edit is an error candidate; review a 2% random sample of audio by hand to estimate what the ticket comparison misses.
- *"How do you upsell without annoying people?"* — One rules-based offer per order, chosen from the cart, never after "that's all", measured by acceptance rate and by order-completion time; turn it off per store if completion time rises.
- *"Who can stop it?"* — The store manager from the crew tablet (that store), the operations on-call (the fleet), and automatic triggers: POS failure, a recognition outage, or an intervention-rate spike above twice the store's baseline.
- *"What would you report to the chain's executives every week?"* — Order accuracy, completion without crew, p95 time to first response, crew interventions per 100 orders, cost per order, and the three worst stores with the reason — one page, same format every week.

---

## 39c.3 Use case: prediction markets (Kalshi, Polymarket) for an Applied AI team

Why they appear in the conversation: they are high-growth, data-rich customers with problems that map cleanly onto agents — but with money, adversaries and regulation attached. Chapter 42 has the long form; here is the interview shape.

**What you would build for them (prioritized).**
1. *Market creation assistance*: news and schedule ingestion → draft market specs with unambiguous resolution criteria (source, time zone, edge cases) from category templates → duplicate and overlap detection with embeddings → analyst approval. Metric: markets launched per analyst-hour; post-launch disputes.
2. *Resolution assistance*: evidence gathering from allow-listed sources, claim-level verification with citations, confidence scores, a resolution package for humans or the oracle process; everything audited. Metric: resolution latency, dispute and reversal rates.
3. *Integrity and risk*: streaming features over trades and accounts, anomaly detection and account-relationship graphs, LLM-written alert narratives with evidence, case management. Metric: alert precision, time to detect.
4. *Support and user assistants*: grounded strictly in official rules; escalation; multilingual. Metric: containment, explanation accuracy.
5. *Internal operations automation*: agents and copilots across ops, finance, talent and marketing — prompt libraries, eval frameworks, RAG pipelines, standards (the published "AI Ops" role at one of these companies describes exactly this).
6. *Research agents* with read-only tools; nothing that places orders without a separately gated execution path.

**Constraints to say out loud.** Markets move in seconds (freshness is correctness); wording decides outcomes (reduce ambiguity, never add it); adversaries will argue resolutions (evidence and audit); CFTC-regulated exchange on one side, oracle-based resolution on the other; KYC/AML; small teams.

**On Google Cloud.** BigQuery for trades and market data; Pub/Sub and Dataflow for streaming features; Gemini on the Gemini Enterprise Agent Platform (Vertex AI, in the old naming) for drafting and verification with grounding; Agent Search (formerly Vertex AI Search) over allow-listed sources; Agent Runtime (formerly Agent Engine) for the operations agents, each with its own Agent Identity; Model Armor; IAM/VPC-SC; Looker for integrity dashboards; the Gen AI evaluation service and Agent Simulation for adversarial test sets.

**The sentence that shows judgement.** "For a market operator I would make the agent a faster, more consistent analyst — spec drafting, resolution packages with citations, integrity narratives — with approvals on anything that moves money or resolves a market, adversarial evals, and an audit trail a regulator can read."

### Critic's additions: how the two platforms actually resolve, the regulatory facts to state carefully, the resolution-package schema, and seven follow-ups

**How resolution works, in the platforms' own terms (check before the interview; both change).**
- *Kalshi:* each market's rules name the source (league statistics, a government release, an event authority) and may set a determination time later than the event; "a market settles when the official outcome is confirmed and our markets team finalizes the result", most within a few hours (often about three) of the outcome being known, and a delayed or revised source postpones settlement.
- *Polymarket:* resolution runs through UMA's optimistic oracle. Anyone can propose an outcome by posting a bond (typically \$750); a two-hour challenge period follows; a first dispute starts a new proposal round; a second dispute escalates to UMA's Data Verification Mechanism, a token-holder vote that takes about 48 hours. Clarifications are published on-chain through a bulletin-board contract and are meant to be considered by voters.

What this means for an agent: on Kalshi the customer is the markets team, and the agent's job is a faster, better-evidenced determination; on Polymarket the agent can help the operator write clearer markets and clarifications, monitor proposals against the rules, and prepare evidence for disputes — it never is the oracle.

**Regulatory facts, stated with dates and hedged.** Kalshi has been a CFTC-designated contract market since November 2020. Polymarket acquired QCEX, a CFTC-licensed exchange and clearinghouse, for \$112 million in July 2025, received an amended order of designation in November 2025 for intermediated US access, and reopened to US users in December 2025. Sports event contracts have been challenged by several US states, with litigation and mixed rulings continuing through 2026 — so geofencing and per-jurisdiction product rules are system requirements, not legal footnotes. Say "at the time of writing" and do not volunteer opinions on the litigation.

**Why wording and insiders are product risks, not hypotheticals.** Both platforms have had public disputes where the contract's wording, not the event, decided the fight — Polymarket's 2025 market on whether Zelensky would wear a suit is the textbook case — and Kalshi has published enforcement actions against insiders, including candidates trading on their own races. An agent that drafts markets must reduce ambiguity measurably, and an integrity agent must treat "who could know first" as a feature, not a footnote.

**The resolution package, as a schema** (so "resolution assistance" is not high level): `market_id`, `rule_text` (verbatim), `designated_source` (URL and publisher), `observed_value` with `source_url`, `source_published_at` and `retrieved_at`, `timezone_normalization` (the conversion shown), `edge_case_checks` (postponement, cancellation, revision, tie — each with pass or flag), `proposed_outcome`, `confidence`, `dissenting_evidence`, `reviewer`. The gate: auto-propose only when two independent fetches of the designated source agree, every edge-case check passes and confidence clears a threshold set on the backtest for at least 99.5% precision on the automatic path; everything else goes to an analyst with the package pre-filled.

**Seven follow-ups.**
- *"Why not let the model search the web to resolve?"* — Because the rules name the source; Google Search grounding is useful for discovering that the event happened, never for deciding the outcome. The resolver reads only the designated source and records exactly what it read and when.
- *"The source publishes, then revises an hour later."* — The rules decide which publication counts (a contract typically names the release or report that settles it); the agent's edge-case check flags revisions inside the determination window and routes to a human, and the package records both values.
- *"How do you evaluate a market-spec drafter?"* — Against historical disputes: seed the eval set with markets that were disputed or clarified and measure whether the drafter's version would have closed the gap (a named source, a time zone, a tie or postponement clause); plus an ambiguity lint (vague terms, missing source, relative dates) and analysts' edit distance before approval.
- *"How do you detect insider trading around a resolution source?"* — Features: position size and timing relative to the source's publication schedule, first-time accounts that trade one market heavily, P&L concentration, links between accounts (devices, funding sources, referral graph); a graph model plus rules produce alerts; an LLM writes the narrative with the evidence for an analyst; precision at the analysts' alert budget is the metric.
- *"What latency matters?"* — Two different clocks: news to market listing (minutes; analysts approve), and source publication to settlement (hours on Kalshi's process, the challenge window on Polymarket). A resolution assistant that is ten minutes faster but wrong once is a net loss.
- *"How do you stop the operations agent from leaking non-public information?"* — Pending resolutions and surveillance cases sit in a separate project and perimeter; the agent's identity has no grant there; retrieval is ACL-filtered; outputs to public channels go through an approval step; and the audit log shows who saw what before a market moved.
- *"Build it on Google Cloud in one breath."* — Pub/Sub and Dataflow for trades and news, BigQuery for features and history, an ADK resolver on Agent Runtime with read-only tools for the designated sources and an Agent Identity, Gemini Pro with high thinking only on evidence reconciliation, a judge on a different model for the package, Model Armor on fetched pages, a review queue for analysts, and BigQuery tables for every package and decision.

---

## 39c.4 The Applied AI team context: what they are hiring for

An Applied AI / Forward Deployed Engineer at a cloud provider is the customer's lead agent engineer: discovery and scoping with business stakeholders, architecture on the provider's platform, hands-on build (Python, agents, RAG, conversational AI, evaluation and observability pipelines), production hardening (security, scale from thousands of internal users to millions of external ones, performance and cost), enablement of the customer's team, and feedback to product. Expect: Terraform or similar to automate agent setup; full-stack apps against enterprise IT; multi-agent frameworks (ADK, LangGraph, CrewAI; ReAct and chain-of-thought as vocabulary); debugging agent logic; enterprise knowledge bases and RAG optimization; high-traffic troubleshooting; travel. The scoring lenses are AI/ML engineering, operational excellence, security/privacy/compliance, scalability, and performance and cost — map every answer to at least two of them explicitly ("that covers the security lens; on scalability…").

**Other question types from the same guide and how to handle them.**
- *Troubleshooting* ("a marketing manager says the website is slow"): clarify what "slow" means and for whom; look at metrics (p95 by endpoint, region, device), traces, recent deploys, dependencies (DNS, CDN, database), then form hypotheses and test the cheapest first; communicate status; fix; post-mortem. Same ladder as 39b.2.
- *System design* (broad ask, e.g., "design a customer-service agent for a bank"): the 45-minute method in chapter 40; put the security and scale lenses on the board explicitly.
- *Scalability* ("10K internal users today, millions external next year"): stateless services, queues, caching, rate limits, provider capacity, tenancy, cost per request, SLOs, tail-sampled observability, abuse controls, regional deployment.
- *Consulting* ("the customer wants X but it's a bad idea"): discovery questions, the risk in plain terms, a safer alternative with a timeline, the decision documented; ownership of the relationship.
- *Demo / application development*: a small end-to-end app you can show and explain (one of chapter 34's labs on Google Cloud), with evals and traces.

### Critic's additions: the sample questions answered with numbers, and the vocabulary the guide lists

**"A marketing manager says the website is slow" — the specific version.** Clarify in one breath: which pages, since when, for whom (region, device, logged in or not), and whether "slow" means loading or interacting. Then field data before lab data: Core Web Vitals at the 75th percentile from real-user monitoring or the Chrome UX Report — "good" is LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1 — and TTFB, where a jump points at the backend. Server side: p95 latency by endpoint in Cloud Monitoring, slow spans in Cloud Trace, Cloud CDN cache-hit ratio (a deploy that changed cache headers is a classic), Cloud Run revision history, cold starts and concurrency, Cloud SQL Query Insights for the slowest queries, and third-party tags added by marketing itself (the most common answer nobody wants to hear). If the slow part is an AI feature: time to first token, whether streaming was switched off, and input-token growth per request. Communicate on a cadence ("investigating; next update at 15:30"), fix the cause, then write the post-mortem with the prevention item.

**"10K internal users today, millions of external users next year" — do the arithmetic.**

| | Internal | External |
|---|---|---|
| Volume | 10,000 users × 20 requests a working day = 200,000 a day | 2 million daily users × 5 requests = 10 million a day |
| Throughput | about 5 QPS across working hours, under 20 at peak | about 116 QPS on average, 500–600 at the evening peak |
| Tokens | 1.2 billion input tokens a day at 6k per request | 60 billion input tokens a day; at peak about 3.6 million input tokens per second |
| Model cost at Gemini 3.8 Flash introductory list prices, 70% of input cached, 300 output tokens | about \$560 a day | about \$28k a day — roughly \$840k a month, about 0.3 cents a request (roughly double from January 2027) |
| What changes | almost nothing; one region, corporate IdP | Provisioned Throughput and quota planning with Google weeks before launch, multi-region serving, per-user rate limits, abuse controls (bot detection, Model Armor), consumer identity with tenancy in the token, tail-sampled tracing, and a cost ceiling per request agreed with the business |

The sentence for the interviewer: "At ten thousand internal users this is an engineering problem; at millions of external users it is a capacity, cost and abuse problem — I'd agree the per-request cost ceiling with the business before I chose the model."

**The consulting question, answered in the shape they score.** "The customer wants the agent to read all of SharePoint with one service account to save two weeks." Acknowledge the goal (speed); name the risk in one sentence (every user would see every document, and a prompt injection in any document acts with that grant); offer the alternative with its cost (an access-controlled Agent Search data store with ACLs synced from SharePoint and Workforce Identity Federation to the customer's IdP — about two extra weeks); write the decision down with the owner's name; escalate to their security lead and our account team only if they still insist. Ownership is "I will deliver the safe version in four weeks", not "we can't".

**The vocabulary the official guide lists, with one sentence each.** *CCAI* — Contact Center AI, the umbrella name some interviewers still use for what became the Customer Engagement Suite and, in January 2026, Gemini Enterprise for Customer Experience. *ReAct* — the reason–act–observe loop inside any tool-using agent. *Chain of thought* — reasoning written as tokens; contrast with hidden thinking and latent reasoning (39b.3). *LLM serving* — vLLM or a managed endpoint on GPUs or TPUs (TPU 8i, announced at Next '26, targets inference), continuous batching, KV-cache memory, quantization, autoscaling on queue depth. *LLM troubleshooting* — KV-cache out-of-memory at long context, latency from batch settings, quality regressions after a model version change behind an alias, 429s from quota. *LangGraph and CrewAI* — say what each is for (stateful graphs with checkpoints; role-based crews) and that ADK 2.0's graph workflows cover the same ground on Google Cloud.

---

## 39c.5 The communication playbook: specific, structured, owning

**Opening any answer.** One sentence that answers directly. Then "Three parts: …". Then depth. Interviewers write notes in real time; give them headings.

**Being specific.** Replace categories with instances: "a vector database" → "Vector Search on the Agent Platform (Vertex AI Vector Search) with a `tenant` restrict"; "monitor it" → "p95 latency and empty-result rate per tool in Cloud Monitoring with alerts at 2× baseline"; "evaluate" → "a 250-question set with a calibrated faithfulness judge, κ 0.84 against two labelers"; "optimize cost" → "cache the 2.5k-token prefix and route 75% of turns to Flash — 69% lower on our numbers".

**Ownership language.** "I would own…", "In my first week I would…", "The decision I made was…", "I was wrong about X; I fixed it by…". Avoid "the team could", "one might", "it depends" without finishing the sentence ("it depends on the latency budget: under a second I'd do A, otherwise B").

**Professionalism.** Answer the question asked; ask one clarifying question when needed; say "I don't know that product's exact limit; I'd check, but here is how I'd approach it"; never disparage previous employers, customers or tools; keep stories about decisions and results, not blame.

**Avoiding "high level."** Every time you name a component, add how it fails and how you would know. Every time you name a metric, add the threshold. Every time you name a pattern, add the budget. Every time you name a product, add a parameter or a setting ("`thinking_config` with a 2k budget on the planner", "row-level policy filtering on `region`").

**Handling follow-ups.** Welcome them: "Good question — two things change…". Keep the structure: answer, mechanism, number, trade-off. If pushed beyond your knowledge, give the principle and the test you would run.

**Managing the clock.** Five topics in sixty minutes is ten minutes each: 90 seconds framing, 5–6 minutes depth, 2 minutes follow-ups. If you are deep in minute eight, close with the one-line summary and offer to continue.

**Rehearsal plan.** Record yourself on each of the five topics (39b) at ten minutes; cut rambling; make sure each answer contains at least three product names, two numbers and one trade-off; run the follow-ups with a friend or the kit's `/interview-prep` mock; repeat until the structure is reflexive and the examples are yours.

### Critic's additions: three rewrites from high level to specific, and the sentences for awkward moments

**Three rewrites — the same content at two altitudes.**

| Topic | High level (what fails the bar) | Specific (what passes) |
|---|---|---|
| FinOps | "I'd optimize cost with caching and smaller models." | "First attribution: cost per turn by feature from OpenTelemetry token counts joined to a price table in BigQuery. Then cache the 2,500-token prefix — reads at 10% of input price — route 75% of turns to Flash on a difficulty classifier, and trim context to 2,500 tokens: 69% lower at current list prices, 54% after the January 2027 Flash price step, with no change on the 200-case eval set." |
| Security | "I'd use IAM and guardrails." | "The agent acts as the user: OIDC sign-in, a scoped token in the request context, a BigQuery row access policy filtering on `SESSION_USER()`, an ACL-synced Agent Search data store; the agent's own Agent Identity holds only platform access; Model Armor runs inspect-only for two weeks, then blocks; five negative tests run in CI on every change." |
| Observability | "I'd check the logs and fix the prompt." | "Trace first: the `execute_tool` span for `find_dataset` shows `403 accessDenied` on `bigquery.tables.list`, swallowed into an empty list; the principal changed at the 14:02 redeploy. I grant the new principal in Terraform, return `forbidden` as a status, alert when any tool's 403 rate exceeds 1%, and add a replay test." |

**Sentences for the awkward moments.**
- *A product you know under its old name:* "I know it as Agent Engine — Agent Runtime now; the parameters I'd check are the identity type, minimum instances and tracing."
- *A product you have not used:* "I haven't run that in production; the equivalent I built is X, and I'd verify the difference in a day by checking Y and Z."
- *A follow-up that exposes a gap in your design:* "You're right — that fails when the token expires mid-run. I'd refresh it in the tool wrapper and add a test with a 60-second token." Concede in one sentence, then give the mechanism.
- *The interviewer moves on while you are mid-answer:* stop, give the one-line close ("so: trace, layer, fix, test, alert"), and follow them; the script has more topics than minutes.
- *You run out of facts:* give the principle, the number you would measure and the test that would settle it — never invent a limit or a price.

**Make the interviewer's notes easy.** Signpost out loud ("first, attribution; second, the levers; third, governance"), give one number per signpost, and repeat the headline at the end. Interviewers who write while you talk score what they managed to write down.

---

## 39c.6 A note on the coding round that follows

The companion coding interview is general software engineering, not AI: one medium problem in 20–30 lines of Python on a shared editor with no execution — strings, arrays, hash maps, heaps, trees/graphs, bit manipulation; no dynamic programming expected. Method: restate the problem and constraints; clarify input sizes and edge cases aloud; propose a brute force with its complexity; propose the better approach; write clean, typed Python with meaningful names; walk through two examples by hand (including an edge case); state time and space complexity; add tests you would write. Practice the three recurring shapes: (1) string/graph problem → complexity → tree variant; (2) a string problem plus "implement a tracker" mini-design with a heap or a bit array and its complexities; (3) a distributed-systems design discussion after a string-split warm-up. Thirty minutes a day for two weeks on those shapes is enough; chapter 39d covers the twenty coding patterns behind them, with tested templates and LeetCode practice sets, and chapter 49 covers the engineering fundamentals they probe along the way.

### Critic's additions: the "tracker" shape worked end to end, and the distributed follow-up

The editor does not run code and the interviewer expects real Python, not pseudocode. The order that scores: a working solution, then edge cases, then the optimization, then the tests you would write — saying each step before you do it.

**The shape, worked: "Implement a tracker that hands out the smallest free positive id; ids can be released and reused."** Clarify aloud: the range (unbounded or a fixed N?), what releasing an unallocated id should do (raise), and the expected call mix (many allocations, few releases?). Brute force: scan from 1 for the first unused id in a set — O(n) per allocation. Better: a counter for ids never handed out plus a min-heap of released ids.

```python
import heapq


class IdTracker:
    """Hands out the smallest free positive id; released ids are reused first."""

    def __init__(self) -> None:
        self._next = 1                    # smallest id never handed out
        self._free: list[int] = []        # min-heap of released ids
        self._free_set: set[int] = set()  # membership check for double release

    def allocate(self) -> int:
        if self._free:
            ident = heapq.heappop(self._free)
            self._free_set.remove(ident)
            return ident
        ident = self._next
        self._next += 1
        return ident

    def release(self, ident: int) -> None:
        if not 1 <= ident < self._next or ident in self._free_set:
            raise ValueError(f"id {ident} is not currently allocated")
        heapq.heappush(self._free, ident)
        self._free_set.add(ident)
```

Complexity: `allocate` and `release` are O(log f) time, where f is the number of released-but-unused ids; space O(f). Why the heap gives the smallest free id: every id below `_next` is either allocated or in the heap. Walk two examples by hand: allocate three times (1, 2, 3), release 2, allocate (2); and the edge case release(7) or release(2) twice, which raise. Tests you would write: those two sequences, release of 0 and of a negative number, and a randomized test against the brute-force set scan.

**The bit-array variant they may ask for.** For a fixed range of N ids, a bit array costs N/8 bytes (one million ids in 125 KB, against tens of bytes per entry for a heap and a set); allocation scans words for the first word that is not all ones and then finds the lowest zero bit — O(N/64) in the worst case, improved to near-constant with a second-level summary bitmap that marks full words. Say the trade: compact and cache-friendly with a bounded range, against the heap's O(log f) with an unbounded one.

**The distributed follow-up ("now several servers allocate ids").** Three answers with their trade-offs: a single allocator service behind a lease (simple and exact "smallest free", but a contention point and a failover question — leases expire and return ids); partitioning the id space by node (node k takes ids congruent to k modulo the node count — no coordination, but "smallest free" holds only per node); or time-based unique ids (timestamp, node id, sequence) when the requirement is uniqueness rather than smallness. Ask which property the product needs before choosing.
