# 38. The STAR method: drills, a story bank, and worked examples

> **The idea:** behavioural answers are not improvisation; they are retrieval. You keep a bank of 10–15 stories, each written in STAR form with numbers, each tagged to the competencies interviewers test, and you rehearse them until the 90-second version is automatic. Then any question becomes "which story, which angle". Go deeper: Part 6 → *Behavioural interviews at top tech companies*.

## 38.1 STAR, precisely

- **Situation** (15 s): context, scale, constraint. "A $3T asset manager; thousands of marketing assets a year; legal review was the bottleneck."
- **Task** (10 s): what *you* owned. "I owned the design and delivery of the agentic review workflow."
- **Action** (50 s): the decisions you made and why — three or four concrete moves, in first person singular. "I split review into parallel reviewer agents with their own retrieval…; I made every finding cite a rule id…; I put a conflict-detection step…; I negotiated the rubric with legal…"
- **Result** (15 s): numbers, adoption, what changed. "Cycle time dropped from days to hours; zero regulatory escapes in the first quarter; the platform was reused for two more content types."
- **Reflection** (optional, 10 s): what you learned or would do differently. Senior interviewers reward it.

Rules: 90 seconds for the first pass, then let them pull detail; "I" for your decisions, "we" for team outcomes; never a story without a number; never a story where the lesson is that someone else was wrong.

## 38.2 Competencies they test and the story tags

| Competency | Typical prompts | Tag |
|---|---|---|
| Ownership / drive | "a project you drove end to end", "something nobody asked you to do" | OWN |
| Ambiguity | "vague requirements", "no clear owner" | AMB |
| Technical judgement | "a hard technical decision", "trade-off you made" | TECH |
| Failure and learning | "a time you failed", "a production incident" | FAIL |
| Conflict and influence | "disagreed with a stakeholder/engineer", "convinced without authority" | INF |
| Delivery under pressure | "tight deadline", "scope cut" | DEL |
| Customer focus (FDE) | "difficult customer", "pushed back on a customer" | CUST |
| Leadership / mentoring | "grew someone", "built a team" | LEAD |
| Ethics and safety | "asked to do something you thought was wrong", "AI safety concern" | ETH |
| Data-driven decisions | "changed your mind because of data" | DATA |

Each story gets two or three tags; the bank needs every tag covered twice.

## 38.3 A story bank from the reference resume (as examples of form)

| # | Story headline | Tags | Numbers |
|---|---|---|---|
| 1 | Parallel reviewer agents with conflict detection for marketing compliance | OWN, TECH, INF | cycle time, escapes, rules cited |
| 2 | Taking an LLM-first inventory platform from concept to production in nine months as co-founder | OWN, DEL, AMB | $1.5M, 15%, 89% |
| 3 | Serving throughput +80% on GPU/TPU for multimodal models | TECH, DATA | 80%, cost per asset |
| 4 | Two-tower ranking at 10K QPS with statistical gates — saying no to a launch | DATA, INF, TECH | ~100% CTR, QPS |
| 5 | Building a 15-person Smart Agents team and a portfolio with acceptance criteria | LEAD, AMB | team size, use cases |
| 6 | Cutting cloud cost 25% on a forecasting pipeline | TECH, DATA | 25% |
| 7 | A chatbot intent model that improved 30% — and the labeling fight behind it | DATA, INF | 30% |
| 8 | A production incident in model serving and the post-mortem that changed the deploy process | FAIL, OWN | time to recover |
| 9 | Explaining a churn model to actuaries and changing the model to be explainable | INF, ETH, CUST | 20% |
| 10 | Dialogflow CX vs. a pure LLM chat — choosing determinism for transactions | TECH, CUST | fallback rate |
| 11 | A customer request that would have violated data policy, and the alternative I proposed | ETH, CUST | — |
| 12 | Mentoring a junior engineer to own a service | LEAD | — |

Write yours the same way; headlines first, then STAR paragraphs, then the 30-second version.

### Critic's additions: which story answers "have you done this?" in each of the five role-related-knowledge topics

In a scripted technical round the interviewer may follow a design answer with "have you done this?" The answer is a 60-second story, not the 90-second one, and it must use only facts you can defend with a number-defense card (36.7). Mapping the reference bank above, as an example of the method:

| RRK topic | Story from the bank | The probe to prepare | Honest boundary to state |
|---|---|---|---|
| FinOps (token and serving cost) | 6 (cloud cost on a forecasting pipeline), 3 (serving throughput), 2 (multi-LLM routing in the inventory platform) | "What was the unit cost before and after, and which lever gave most?" | if your cost work was on pipelines or GPUs rather than tokens, say so and bridge: "the method — attribute, rank levers, gate on quality — is the same one I'd apply to tokens" |
| Observability troubleshooting | 8 (serving incident and post-mortem) | "How did you find the cause, and what gate did you add?" | the incident was model serving, not an agent; bridge to the trace-first ladder of 39b.2 |
| Agentic design and reasoning placement | 1 (parallel reviewer agents with conflict detection) | "Where did the model reason, and why there?" | describe the reasoning placement you actually used; if you did not run a budget sweep, say how you would |
| LLM-as-a-judge | 1 (judges calibrated against reviewers), 7 (the labeling behind the intent model) | "How did you know the judge, or the labels, were right?" | give the agreement figure only if you measured it |
| Security and IAM | 11 (a customer request that would have violated data policy), 1 (permission-filtered retrieval and audit trail) | "Where was the permission enforced — prompt, tool or data?" | name the layer you enforced at; if it was the tool layer only, say what you would add at the data layer |
| Conversational AI background | 10 (Dialogflow CX versus a pure LLM chat) | "What exactly did the webhook do?" | describe your flows and webhooks; CX Agent Studio is the 2026 evolution, so say how the same design would move there rather than implying you used it |

For the two named use cases (a drive-through voice agent, prediction-market operations) most candidates have no direct story. Say so in one sentence and move to the design: "I haven't built a drive-through agent; the closest is the Dialogflow CX layer I built, and here is how I'd approach the drive-through" — professionalism scores higher than a stretched story.

## 38.4 Two worked stories

**"Tell me about a time you disagreed with a stakeholder."** (INF, TECH)

*Situation:* In the ad-tech ranking work, a new ranking model showed a 6% CTR lift in a two-day A/B test and the product owner wanted to launch before a quarterly review. *Task:* I owned the A/B harness and the launch decision criteria. *Action:* I showed that the test had not reached the pre-registered sample size and that the lift was concentrated in one segment with a known novelty effect; I proposed extending by five days with a guardrail on revenue per impression and a rollback path, and I offered a partial rollout to 20% so the review could cite real numbers. *Result:* The extended test confirmed a smaller but real lift (about 3%), we launched to 100% a week later with no revenue regression, and the pre-registered criteria became the standard for all launches. *Reflection:* The win was making the rule explicit before the next argument, not winning that one.

**"Describe a production failure."** (FAIL, OWN)

*Situation:* A multimodal serving endpoint for the creative platform degraded after a model update; latency tripled and users saw timeouts. *Task:* I was the engineering lead on call. *Action:* I rolled back within minutes using the previous image, then traced the cause to a changed default batch size interacting with GPU memory limits; I added a load test with the production batch profile to CI, a canary stage with latency gates, and an autoscaling policy tied to queue depth. *Result:* Recovery under 15 minutes, no repeat, and the throughput work that followed delivered the 80% improvement. *Reflection:* The incident was a missing gate, not a bad engineer; I changed the process, not the person.

### Critic's additions: the "why?" ladder under each worked story, and two story templates for the five RRK topics

**The follow-ups a senior interviewer asks after the A/B story.** *"What was the pre-registered sample size and how did you compute it?"* (baseline CTR, minimum detectable effect, power 0.8, alpha 0.05 — have the formula in your head: n per arm ≈ 16 × p(1−p) / MDE² for a two-sided test at those settings). *"Why 20% and not 50%?"* (exposure to a possible revenue regression bounded at a fifth of traffic; enough volume to reach significance in the extension window). *"What was the guardrail's non-inferiority bound?"* (a named number, for example revenue per impression not below −1%). *"What did you say to the product owner in the room?"* (the sentence, not the sentiment: "if we launch now and the lift is novelty, the quarterly review will cite a number we have to retract").

**The follow-ups after the incident story.** *"How did you know it was the batch size and not the model?"* (the latency trace showed queueing before inference, GPU memory alerts fired, and a diff of the serving config showed the default change; reverting the config alone reproduced the fix in staging). *"Why did the canary not exist before?"* (it did for the application tier, not for model images — the gap was ownership). *"What did the post-mortem change in the deploy process, concretely?"* (a required load test with the production batch profile, a latency gate on the canary at p95 ≤ 1.2× baseline for 15 minutes, and model images promoted through the same pipeline as code).

**Two templates for stories the role-related-knowledge round rewards.** The five topics in chapter 39b are technical questions, but an interviewer scoring "ownership" will ask "have you done this?" Have a story ready for at least FinOps and security. Fill these with your own facts; do not borrow the examples.

- *FinOps story (OWN, DATA, TECH).* Situation: a named workload with a monthly model spend and the moment it became visible (a budget alert, a finance question). Task: you owned attribution and the reduction. Action: instrumented token counts and cost per feature; found the shape (input-heavy, repeated prefix, frontier model on everything); applied two or three levers with an eval gate on each. Result: the before and after per unit (cost per turn, per document), the quality metric that did not move, and the control you left behind (a dashboard, a budget, a CI cost delta). Reflection: which lever you would pull first next time.
- *Security pushback story (ETH, CUST, INF).* Situation: a stakeholder or customer asked for an agent with broad data access to move faster. Task: you owned the design and the relationship. Action: explained the specific risk in one sentence (a prompt injection in any retrieved document would act with the agent's full grant), proposed the alternative (user-propagated identity, scoped tools, ACL-filtered retrieval) with its timeline, and wrote the decision down. Result: what shipped, when, and the negative test that proves the boundary. Reflection: the sentence that made the stakeholder say yes.

## 38.5 Drills (20 minutes a day for a week)

1. **Headline drill:** read a tag, say the headline of a matching story within three seconds.
2. **90-second drill:** record yourself telling one story; listen for missing numbers and for "we" where it should be "I".
3. **Angle drill:** tell the same story for a different tag (the ranking story as DATA, then as INF).
4. **Follow-up drill:** have a friend or the kit's `/interview-prep` ask "why?" three times after your story.
5. **Compression drill:** the 30-second version, then the one-sentence version.

## 38.6 Pitfalls

Stories with no decision in them; stories where the result is "it was well received"; blaming; the 5-minute story; answering a different question than asked (listen for the tag); and reusing one story for everything — interviewers across a loop compare notes.
