# FDE and AI Engineer resumes: what the screen looks for

A recruiter spends under a minute on the first pass and an ATS parses the file before that. The top
third of page one (headline, three profile bullets, skills line) decides whether the rest is read.
That is why the kit tailors exactly those places and leaves the experience section untouched.

## What the two roles are screened for

| | AI Engineer (Applied AI, LLM, GenAI Engineer) | Forward Deployed Engineer |
|---|---|---|
| Owns | LLM features and agents in production | a customer's outcome, from proof of concept to production inside the customer's environment |
| Proof they want | shipped systems with users, eval-driven quality, latency and cost per request, observability | go-lives, time-to-value, integrations in messy enterprise environments, customer trust |
| Keywords that matter | RAG, retrieval and reranking, agents and tool use, evaluation (gold sets, LLM-as-judge), guardrails, Python, one cloud's AI stack, tracing | customer-facing, discovery, POC to production, integration (SSO, VPC, IAM, APIs), security reviews (SOC 2, HIPAA, data residency), stakeholder communication, travel |
| Red flags | demos only, no metrics, no evals, framework lists without systems | no customer contact, nothing reached production, no ownership of an outcome |

Many postings mix both. Read which failure the role is paged for: a wrong or expensive answer
(AI Engineer) or a customer that never reached production (FDE). Lead with evidence for that one.

## Structure (two pages, US format)

1. Name and contact line: city and state, email, phone, LinkedIn, GitHub. No photo, no date of birth.
2. **Headline** (at most 85 characters): target title + two or three strongest truthful themes.
   Example: `Forward Deployed AI Engineer | RAG, Agents and Enterprise Integration`.
3. **Three profile bullets**: one per top must-have of the posting, each with a number.
4. **Skills line**: the posting's matching skills first. Reorder or drop; never add.
5. Experience: reverse chronological, 3-6 bullets per recent role, older roles shorter.
6. Education, then certifications and selected projects or open source, if relevant.

## The bullet formula

**Verb + what you built or changed + for whom or at what scale + how (key tech) + measurable result.**

- Weak: "Worked on a RAG chatbot using LangChain."
- Strong: "Built a retrieval assistant for 120 support agents (hybrid search, reranking, 300-case eval
  set) that cut median handling time 38%."

Rules: the result is a number already in the master resume (time, cost, accuracy, adoption, revenue,
scale); one idea per bullet; at most two lines; past tense for past roles; no "responsible for",
"helped", "various". For FDE postings, name the customer setting (regulated industry, on-prem, VPC)
and the outcome (go-live, renewal, adoption).

## Using the job description's words

- Mirror the posting's exact phrases where the resume truthfully supports them ("LLM evaluation"
  rather than "model testing" if the posting says so). ATS search and recruiters both match strings.
- Put each must-have keyword where it is proven: in a profile bullet or the skills line, not in a
  keyword dump.
- A must-have the resume does not support is a gap. Name it in fit.md and prepare an honest bridge
  for the interview; never write it into the resume.

## ATS rules

- Keep the master as .docx and upload a PDF produced from it (text-based, not scanned).
- Standard headings: Experience, Education, Skills. Single column reads most reliably; text in tables
  and text boxes can be read out of order or skipped, so keep contact details and the headline in
  normal paragraphs, not only in a header, footer, table or text box.
- No images, icons or charts for content; standard fonts; plain hyphens and bullets.
- Dates as "Mon YYYY - Mon YYYY" or "YYYY - YYYY", consistently.
- File name: "<Name> - Resume - <Company>.pdf" (the script does this).
- Two pages at most; the script enforces `resume.max_pages`.

## Honesty rules

- Every skill, employer, title, year and number comes from the master resume or profile.yaml.
- Numbers keep the master's exact figure and format; no rounding, no new metrics.
- Years of experience come from `skills_years`; a skill not listed is 0.
- If the posting needs something the user lacks, the answer is a gap note, not a stretched claim.
