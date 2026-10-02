---
name: interview-prep
description: Builds a one-page interview brief (prep.md) for a tracker id from its job description and fit analysis - the problem behind the posting, the implied architecture, the 90-day sentence, matching STAR stories, likely Forward Deployed Engineer and AI Engineer technical questions and questions to ask - and offers a mock interview with critique. Use when the user runs /interview-prep, has an interview coming up, or wants interview practice for a role.
argument-hint: "<tracker-id>"
allowed-tools:
  - Read
  - Bash(.venv/bin/python scripts/tracker.py *)
metadata:
  kit: job-agent-kit
---

# Interview prep

Tracker id: `$ARGUMENTS`. Work from the workspace root. Facts about the user come only from
`profile/master-resume.txt`, profile.yaml (including `stories`) and what the user tells you now.

## 1. Gather

- Find `applications/*/$ARGUMENTS/` and read `jd.md` and `fit.md`. Without jd.md, capture the posting
  (tracker url, get_page_text in Chrome) into `jd.md` first. Without fit.md, build the must-have to
  evidence map yourself from the master resume.
- Read `profile/master-resume.txt` and the `stories` in `profile/profile.yaml`.

## 2. Analyse (the 20-minute JD routine)

1. Extract must-haves, nice-to-haves, the pains behind them, and the system the team must be building.
2. Map each must-have to evidence (bullet, project, years) and mark gaps honestly.
3. Sketch the architecture and list the questions you would ask.
4. Pick three stories and write the 90-day sentence.

## 3. Write `prep.md` in the posting's folder (one page, about 600 words)

- **Role in one line**: company, role, team, and the interview stage if known.
- **The problem behind the posting**: what is broken or new, why they are hiring now, and how success
  will be measured. Quote the JD phrases that show it.
- **Implied architecture**: a small text diagram (for example sources -> ingestion -> retrieval and
  agents -> evaluation -> deployment and observability, or whatever the JD implies), plus three design
  decisions the team faces, each with its trade-off.
- **The 90-day sentence**: "In 90 days I will have <outcome> for <who>, measured by <metric>",
  grounded in the JD and in the user's real experience.
- **Evidence map**: each must-have, then the user's proof from the resume, or "gap:" with an honest bridge.
- **Three STAR stories** from `stories`, matched to the must-haves, each ending in a result number
  that the resume contains. If fewer than three fit, ask the user for the missing ones (situation,
  task, action, result) and offer to save them to `stories` in profile.yaml.
- **Likely technical questions** (8-10) for this role. For FDE and AI Engineer roles these usually
  include: design RAG over this customer's data; evaluate an LLM feature before launch (offline set,
  judges, online metrics); halve latency or cost; debug an integration that works in staging and fails
  in production; deploy into a customer VPC with data restrictions; agent failure modes and
  guardrails; prompt injection; build versus buy; a customer request that conflicts with the roadmap.
- **Questions to ask** (5): the problem, success at 90 days, how the team works with customers, the
  deployment environment, and how they measure quality.
- **Watch-outs**: gaps to address head-on, and the numbers to have ready.

## 4. Mock interview (offer it; run it only if the user agrees)

- Ask one question at a time and wait for the answer: one behavioural (a story), one system design
  from the implied architecture, two technical deep-dives, one customer scenario.
- After each answer give brief critique, scored 1-5 on each axis:
  - **specificity**: concrete systems, names, scale;
  - **numbers**: metrics, before and after;
  - **trade-offs**: what was rejected, and why;
  - **ownership**: what the user decided and did, not only "we".
  Quote the weakest sentence and offer a stronger version that uses only facts the user stated or
  the resume holds.
- After a story, ask "why?" up to three times to test depth.
- At the end give the scores per axis and the three fixes that matter most, and add improved answer
  outlines to prep.md under "Mock notes".
- If the interview stage is known, record it:
  `.venv/bin/python scripts/tracker.py update <id> --status interview --notes "prep done; mock on <date>"`.
