# 28. Conversational AI platforms: Dialogflow CX, Amazon Lex and Connect, Microsoft Copilot Studio, Rasa and the voice stacks

> **What you need to be able to say:** the two generations of conversational AI (intent/flow-based and LLM-based) and why production systems use both; what each platform provides; how channels, telephony and contact centers fit; and how you would choose. Chapter 41 goes deep on Dialogflow CX and designs a drive-through voice agent.

## 28.1 Two generations, one production reality

**Generation 1 — intents, entities, flows.** A classifier maps each utterance to an *intent* ("reschedule_appointment"), extracts *entities* (date, location), and a *dialog manager* walks a designed *flow* (states/pages, slot filling, conditions, webhooks to backend systems). Deterministic, testable, auditable, cheap at runtime, and painful to build and maintain for anything open-ended; brittle to phrasing outside the training phrases.

**Generation 2 — LLM agents.** A model with instructions, tools and retrieval holds the conversation, handling paraphrase, mixed intents and open questions; generative answers from knowledge bases; "playbooks"/"generative flows" instead of hand-built state machines. Flexible and fast to build; risks are hallucination, policy drift, cost and latency, and the difficulty of guaranteeing a transactional step.

**Production in 2026 is a hybrid:** an LLM handles understanding and open dialogue; deterministic flows own the steps that must be exact (identity verification, payment, order confirmation, regulated disclosures); tools reach the systems of record; guardrails and evaluation wrap everything; and a human handoff is one turn away. Every platform below is converging on this shape from one side or the other.

## 28.2 The platforms

**Google Conversational Agents (Dialogflow CX) — part of the Customer Engagement Suite, built on what was Vertex AI Agent Builder (the Gemini Enterprise Agent Platform since April 2026).** Flows and pages (a state machine with scoped intents and parameters), intents and entities (with ML-based NLU), route groups, webhooks (fulfillment to your backend, e.g., FastAPI), *generators* and *playbooks* (LLM-driven steps and goal-oriented agents with instructions and tools), *data stores* (RAG over websites and documents), built-in telephony and the CES voice stack (Google STT/TTS, Agent Assist, Insights/analytics), test cases and versions/environments, multilingual support, and the Dialogflow CX Messenger web widget. Strength: the most complete deterministic + generative design surface and Google's speech quality; weakness: pricing by session and request, complexity, and Google's product renames — in January 2026 Google also packaged ready-made shopping, support and food-ordering agents plus a "CX Agent Studio" as **Gemini Enterprise for Customer Experience**, so expect that name in job descriptions alongside CES and Dialogflow CX (verify which console a customer actually uses). Chapter 41.

**Amazon Lex V2 + Amazon Connect.** Lex is the bot engine (intents, slots, Lambda fulfillment, generative features such as assisted slot resolution and QnAIntent over Bedrock Knowledge Bases); Connect is the cloud contact center (telephony, chat, routing, agent workspace, Contact Lens analytics, Amazon Q in Connect for agent assistance and self-service); since November 2025 Connect's **agentic self-service** agents reason and take actions (refunds, account changes) across voice and messaging, with **Nova Sonic** speech-to-speech adapting to the caller's tone (English and Spanish GA at launch, other languages in preview), and Bedrock Agents/AgentCore for custom LLM-agent logic. Strength: all-AWS contact center with pay-per-use; weakness: Lex's design surface is simpler than Dialogflow CX's for complex flows.

**Microsoft Copilot Studio (+ Dynamics 365 Contact Center, Azure AI Foundry).** Low-code agent builder for business users with generative orchestration, topics (deterministic flows), knowledge sources (SharePoint, websites, Dataverse, Work IQ/Microsoft Graph), actions via Power Platform connectors, MCP servers and computer use; channels: Teams, M365 Copilot, web, and voice through Dynamics 365 Contact Center/telephony. Strength: Microsoft 365 integration and governance; weakness: licensing complexity (message/credit packs), less control than code for engineers — engineers typically pair it with Foundry Agent Service and MCP servers.

**Rasa (open source + Rasa Pro/CALM).** Code-first dialogue management with *flows* described in YAML and an LLM-based *dialogue understanding* layer (CALM) that maps conversation to flow steps; self-hostable, strong for regulated enterprises wanting control and on-prem. Weakness: you run it.

**Others worth naming:** Kore.ai and Yellow.ai (enterprise suites), Voiceflow (design and prototyping with LLM agents), Cognigy (now part of NICE), Parloa and PolyAI (voice-first), Genesys and NICE CXone (contact-center suites with built-in bots and agent assist), Twilio (programmable voice/messaging, ConversationRelay for LLM voice), Salesforce Agentforce (CRM-native), Zendesk and Intercom (support-native), Sierra and Decagon (LLM-native support agents).

**Voice building blocks (for custom stacks):** telephony (Twilio, Vonage, Telnyx, SIP trunks), real-time transport (WebRTC via LiveKit or Daily), ASR (Deepgram, AssemblyAI, Google, Azure, Whisper), TTS (ElevenLabs, Cartesia, Google, Azure, Polly), speech-to-speech (OpenAI Realtime, Gemini Live, Nova Sonic), turn detection (voice-activity detection plus semantic end-of-turn models such as LiveKit's turn detector, Pipecat Smart Turn, or ASR with built-in end-of-turn prediction), orchestration (LiveKit Agents, Pipecat, Vapi, Retell, Bland), and evaluation (simulated callers, call QA judges).

### Critic's additions: turn-taking is the hard part of voice

Most voice agents that "feel robotic" fail on turn-taking, not on the language model. The mechanics to be able to explain:

- **Endpointing.** A pure silence threshold (voice-activity detection, typically 500–800 ms of silence) either cuts callers off mid-thought or adds dead air to every turn. Semantic end-of-turn models look at the partial transcript ("my account number is…" is not finished) and let you shorten the silence threshold to 200–300 ms on complete utterances while waiting longer on incomplete ones.
- **Barge-in.** When the caller speaks over the agent, stop TTS within ~100–200 ms, discard the unspoken remainder from the conversation history (or the model will believe it said things the caller never heard), and distinguish real interruptions from backchannels ("uh-huh", "right") and background noise.
- **Latency hiding.** Start the LLM on a stable partial transcript, stream TTS from the first sentence of the reply, and use short acknowledgements while a slow tool runs ("let me check that order").
- **Speech-to-speech versus chain.** Native models handle prosody and overlap better and cut latency; the chain gives you a transcript to log, deterministic text guardrails before audio is spoken, and the freedom to swap ASR, LLM and TTS independently — regulated deployments usually keep the chain or run a text guardrail on the native model's transcript in parallel.
- **Telephony realities.** Phone audio is 8 kHz narrowband; ASR accuracy drops versus wideband test sets, so evaluate on real call recordings, not studio audio. DTMF (keypad) input remains the safest path for card numbers and PINs, and PCI scope rules usually require that card digits never reach the model or the transcript.

## 28.3 Comparison

| | Dialogflow CX / CES | Lex + Connect | Copilot Studio | Rasa | LLM-native stack (LiveKit/Pipecat + models) |
|---|---|---|---|---|---|
| Deterministic flows | ✔✔ (pages, routes) | ✔ (intents, slots) | ✔ (topics) | ✔✔ (flows) | you build |
| LLM agents | ✔ playbooks, generators, data stores | ✔ via Bedrock, QnAIntent | ✔✔ generative orchestration | ✔ CALM | ✔✔ |
| Voice/telephony | ✔✔ built in | ✔✔ Connect | ✔ via D365 CC | via partners | ✔ with Twilio/LiveKit |
| Enterprise integration | webhooks, GCP | Lambda, AWS | Power Platform, MCP, Graph | your code | your code |
| Governance | GCP IAM, versions, test cases | AWS IAM, Contact Lens | Entra, DLP, M365 | on-prem possible | your responsibility |
| Best for | complex multilingual contact-center bots on GCP | AWS-centric contact centers | M365 shops, business-built agents | control, on-prem | latency-critical, custom voice products |

## 28.4 Design principles that survive every platform

1. **Separate what must be exact from what can be generative.** Identity, money, confirmations: deterministic. Understanding, explanation, small talk: generative.
2. **Design the handoff first.** Humans receive a summary, the transcript and the structured state; the bot never traps a user.
3. **Ground every answer** in a knowledge source with citations or a tool call; measure containment honestly (a user who gave up is not "contained" — count a conversation as resolved only if the same customer does not come back on the same issue within, say, 7 days through any channel).
4. **Test like software**: conversation test cases, regression suites, simulated users for LLM parts, judge sampling in production.
5. **Latency budgets** for voice: endpointing, streaming, first-audio under a second, barge-in.
6. **Analytics**: intent/topic coverage, fallback rate, escalation reasons, CSAT, cost per conversation; feed failures back into flows and knowledge.

**Interview line:** *"I keep a deterministic core for the transactional steps and let an LLM own understanding and open dialogue, grounded in tools and retrieval, with a human handoff that carries state. Dialogflow CX or Lex/Connect or Copilot Studio supply the flows, telephony and governance; a custom LiveKit-style stack when latency and voice quality are the product."*
