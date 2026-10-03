# 37. Interview preparation: the process, the timeline, and arriving fresh

> **The idea:** preparation is a project with a deadline; being fresh on the day is part of the deliverable, not a luxury. Most strong candidates lose interviews not for lack of knowledge but for being tired, scattered or over-rehearsed. This chapter gives a schedule, a kit, and the habits that keep you calm.

## 37.1 Know the loop

AI-engineer and FDE loops in 2026 usually have five stages, each with a different judge:

| Stage | Who | What they test | Your preparation |
|---|---|---|---|
| Recruiter screen (20–30 min) | recruiter | fit, logistics, salary band, communication | 60-second pitch, numbers (rate/salary, start date, authorization), three questions |
| Hiring-manager screen (30–45 min) | manager | motivation, how you think, project depth, team fit | JD reading (chapter 35), two stories, the 90-day sentence |
| Technical deep dive (45–60 min) | senior engineer | your projects in detail; concepts (chapters 14–34); some live reasoning | use-case files (chapter 36), the five topics (chapter 39), concept drills |
| System design (45–60 min) | staff engineer / architect | designing an LLM system end to end with trade-offs | chapter 40's exercises; whiteboard habits |
| Coding / practical (45–90 min) | engineer | Python fluency, data handling, API design; sometimes an agent/RAG take-home | daily short coding practice; a take-home template repo |
| Behavioural / values (30–45 min) | manager or peer panel | collaboration, conflict, ownership, failure | STAR bank (chapter 38) |
| FDE extras | customer-facing panel | presenting, workshops, handling ambiguity, travel | a 10-minute presentation of one use case; discovery questions |
| Role-related knowledge, provider-side Applied AI (60 min, scripted) | Applied AI engineer or lead | five fixed topics (FinOps, observability troubleshooting, agentic design with reasoning, LLM-as-a-judge, security/IAM) scored against named lenses; depth, product specifics, ownership | chapters 39b and 39c; ten-minute recorded answers per topic; the product-name and parameter sheet |

Ask the recruiter for the exact loop, the interviewers' roles, and what each stage looks for. Companies tell you; most candidates do not ask.

### Critic's additions: what "scripted" changes about your preparation

A scripted role-related-knowledge round is different from a technical deep dive in three ways, and each changes what you do the week before:

1. **The questions are fixed; the scoring is on depth.** The interviewer reads the question, then listens for specifics. Rehearse each topic to a ten-minute recording and cut every sentence that contains "robust", "scalable" or "best practice" without a mechanism after it.
2. **The lenses are explicit.** Write the lenses (AI/ML engineering, operational excellence, security/privacy/compliance, scalability, performance and cost) on your notepad and tick them as you cover them; close each answer with the lens you have not touched ("on the scalability lens, at ten times the traffic I would…").
3. **Product names are evidence.** Keep a one-page sheet of current product names and the parameter or setting you would name with each (chapter 39b.0 has the list and a naming table, updated for the April 2026 renaming of Vertex AI to the Gemini Enterprise Agent Platform and the January 2026 launch of Gemini Enterprise for Customer Experience, which succeeded the Customer Engagement Suite). Interviewers forgive an old name said with the new one beside it; they do not forgive "some memory thing".

## 37.2 The two-week plan (adjust to the time you have)

- **Day 1–2:** read the JD four ways (chapter 35); write the 90-day sentence; list the implied architecture; identify gaps.
- **Day 3–5:** update the use-case files for the three projects closest to their problem (chapter 36); write ten STAR stories (chapter 38); drill the five technical topics (chapter 39; chapters 39b and 39c for the provider-side, Google Cloud version) out loud, recorded, ten minutes each, and write the number-defense cards (36.7) for every figure on the resume you sent.
- **Day 6–8:** two system-design dry runs with a timer (chapter 40), one with a friend or the Claude Code kit's `/interview-prep` mock mode; one coding session per day (45 min), working through the pattern sets in chapter 39d.
- **Day 9–10:** company research: product, customers, recent news, engineering blog, the interviewers' public talks or posts; prepare five questions per interviewer type; build or refresh one lab repo relevant to their stack (chapter 34).
- **Day 11–12:** mock interviews end to end; fix the three weakest answers; prepare the logistics kit (37.4).
- **Day 13:** light review only — the use-case files and STAR headlines, not new material. Sleep.
- **Day 14:** the interview. Nothing new.

For a one-week window, do days 1–2, 3–5 compressed, 9, 11, 13.

### Critic's additions: the 72-hour version for a scripted role-related-knowledge round

When the round is days away, not weeks, spend the time on recall under time pressure, not on new reading:

| When | Do | Output |
|---|---|---|
| 72 hours before | read 39b once, end to end; write the five framing answers from memory and compare; mark the three weakest | five 90-second framings you can say without notes |
| 48 hours before | record each topic at ten minutes, framing then depth; listen once at double speed and cut every sentence without a mechanism, number or parameter; drill the 39b.0 naming table until "Agent Runtime — Agent Engine, in the old naming" comes out unprompted | five recordings and a one-page sheet: per topic three product names with a parameter each, two numbers, one trade-off |
| 24 hours before | one mock with someone reading the follow-ups from 39b and 39c aloud and interrupting; then rehearse the two use cases (drive-through and prediction-market resolution) as five-minute designs; stop by early evening | the cheat sheet (39b.6) and the rapid-fire list (43, questions 151–173) printed or on one screen |
| The morning of | read only the cheat sheet and your opening sentences; check the latest list prices you plan to quote, or say "at current list prices" | nothing new |

The trap in a short window is reading release notes until midnight. Prices and product names matter, but an answer with a clear mechanism and an approximate number outscores a precise number delivered without structure.

## 37.3 Not being overwhelmed: how to stay fresh and relaxed

- **Cap the inputs.** Study from your own notes (use-case files, STAR bank, this book's interview lines), not from the open internet the night before. New material within 24 hours of an interview creates anxiety, not competence.
- **Timebox and stop.** Ninety-minute blocks with real breaks; no study after 8 pm the day before; a hard stop on "one more topic".
- **Sleep is a technical skill.** Two full nights before the interview; no late-night cramming; caffeine before noon only on the day before.
- **Move.** A walk or workout the morning of the interview lowers baseline stress more than any breathing app; ten minutes is enough.
- **Pre-interview routine (30 minutes before):** glass of water, bathroom, close every tab except the video call and your one-page notes, headphones tested, phone silent, a printed or on-screen list of your three stories and the 90-day sentence, two slow breaths with a long exhale, and the sentence you will open with.
- **During:** it is a conversation about problems, not a test of you. Take a breath before answering; it is fine to say "let me think for ten seconds". Ask clarifying questions. If you do not know, say what you would do to find out. Write the question down if it is long.
- **After:** a five-minute note on what was asked and what you would improve; then stop thinking about it. Send a short thank-you that references one specific thing discussed.
- **Across a search:** two or three interviews a week at most when possible; keep the agent (Part 1) doing the applications so your evenings are for preparation and rest, not forms; protect one full day off a week.
- **If anxiety is high** — racing thoughts, no sleep, dread — treat it as a real signal: shorten the study plan, talk to someone, and consider professional support. A calm candidate with 80% of the knowledge beats an exhausted one with 100%.

## 37.4 The logistics kit

A quiet room with a neutral background, a wired or strong connection, a second device with the dial-in as backup, the interviewer names and roles, the JD, your tailored resume (the one they have), the use-case files, the STAR headlines, a notepad, water, a clock. For on-site days: the route, a buffer of 30 minutes, a printed resume, comfortable clothes a notch above their dress code, and snacks.

## 37.5 How to answer, in general

- **Headline first, detail on request.** One sentence that answers, then "I can go deeper on the architecture or the results — which is more useful?"
- **Numbers and trade-offs.** Every answer gets a number (latency, cost, accuracy, scale, time) and a trade-off ("we chose X over Y because Z").
- **Structure visible.** "Three things: data, model, operations." Interviewers remember structure.
- **Honesty about edges.** "I have not run Foundry Agent Service (Microsoft Foundry, formerly Azure AI Foundry) in production; I have done the equivalent on AgentCore and here is how I would approach the differences."
- **Bring them in.** "How do you handle permissions today?" turns an interrogation into a design session — especially for FDE roles.

### Critic's additions: the "not high level" self-check

Run this on every rehearsed answer. If any line fails, the answer is high level, whatever it sounds like.

| Check | Fails when you say | Passes when you say |
|---|---|---|
| Mechanism | "we made it resilient" | "retry three times with exponential backoff and jitter, then fall back to the second model behind the gateway, then dead-letter" |
| Number | "it got much cheaper" | "cost per turn from \$0.044 to \$0.014, a 69% reduction, no change on the 200-case eval set" |
| Product and parameter | "a vector database" | "Vector Search on the Agent Platform (Vertex AI Vector Search, in the old naming) with a `tenant` restrict on every query" |
| Threshold | "we monitor latency" | "p95 under 2.5 s; alert at 2× the seven-day baseline for ten minutes" |
| Failure mode | "it works well" | "it fails when the tool swallows a 403 into an empty list; the empty-result-rate monitor catches it" |
| Ownership | "the team should consider" | "in week one I would instrument every call and publish the first cost review" |
| Trade-off | "it depends" | "under one second of latency budget I would do A; otherwise B, because C" |

## 37.6 Questions to ask (choose by stage)

Recruiter: team size, the loop, timeline, compensation band, remote policy. Manager: what is broken, what success looks like in 90 days, how decisions are made, what the last hire struggled with. Engineer: the stack and its pain, the eval and deployment process, on-call. Architect: where the current design is weakest, the roadmap, build vs buy decisions. FDE panel: how customers are chosen, travel expectations, who owns the customer relationship, what happens when a customer asks for something unsafe.

## 37.7 After the loop

Negotiate from the numbers in the truth file (chapter 10's rates and salary floors); ask for the offer in writing; compare total compensation, not base; and update the tracker and the use-case files with what you learned, whatever the outcome. Every loop makes the next one easier — if you write it down.
