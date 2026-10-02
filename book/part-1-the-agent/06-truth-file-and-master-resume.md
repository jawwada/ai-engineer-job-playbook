# 6. Your truth file and master resume

An agent that applies for you is only as trustworthy as the facts you give it. The kit separates *what is true about you* (the truth file and the master resume) from *how to present it* (the tailoring rules). The agent may rephrase, reorder and emphasize; it may never add a skill, a year, a title or a number that is not in these two files. That one rule is what lets you switch on auto mode later without worrying about what it said.

**`profile/profile.yaml` — the truth file.** The installer copies `profile.example.yaml`; `/job-setup` fills it with you. The parts, for a fictional H-1B holder who contracts through a vendor (the kit's own template uses a US citizen):

```yaml
identity:
  name: Jane Doe
  email: jane@example.com
  phone: "+1 555 010 0000"           # quoted so YAML keeps the leading +
  location: Austin, TX, USA          # as you want it written on forms
  links:
    linkedin: https://www.linkedin.com/in/jane-doe-example
    github: https://github.com/jane-doe-example
work_authorization:
  status: H-1B                       # US citizen | Green card | H-1B | TN | STEM OPT | EAD
  needs_sponsorship: true            # now or in the future; answered honestly on every form
  employment_models: [C2C, W2, full-time]  # what you accept (W2 and full-time with an H-1B transfer)
  c2c_vendor: "Vendor Inc."          # the company that invoices C2C
targets:
  titles: [Forward Deployed Engineer, AI Engineer, Applied AI Engineer, GenAI Engineer]
  seniority: [Senior, Staff, Lead]
  remote_only: true
  min_rate_usd_per_hour: 95
  min_salary_usd: 190000
  start_date: "2 weeks after an offer"
  max_posting_age_hours: 48
  exclude_if: ["US citizens only", "no sponsorship", "onsite", "active security clearance"]
  exclude_companies: ["Example Current Employer Inc."]
skills_years:                        # the anti-overclaiming table; a missing skill = 0
  professional experience: 12        # for "how many years of experience" questions
  python: 12
  rag: 3
  agents: 2
  aws: 8
  kubernetes: 4
  snowflake: 3
skill_aliases:                       # other names (lowercase) -> key in skills_years
  retrieval augmented generation: rag
  agentic ai: agents
  k8s: kubernetes
resume:
  master_path: profile/master-resume.docx
  max_pages: 2
  anchors:                           # exact current text of five paragraphs, copied from the --dump
    headline: "..."
    summary_1: "..."
    summary_2: "..."
    summary_3: "..."
    skills_line: "..."
limits:
  max_applications_per_day: 15       # all platforms together
  linkedin_max_per_day: 25           # LinkedIn ceiling; the overall cap still applies
  mode: review                       # review | auto (Indeed is never submitted)
gmail:
  labels: {alerts: Jobs/Alerts, recruiters: Jobs/Recruiters}
approved_consents: []                # {company, consent, approved_on}, added only after you say yes once
stories: []                          # STAR stories for /interview-prep; numbers must match the resume
```

When a form asks "years of experience with K8s", the agent maps the wording through `skill_aliases` to `kubernetes` and answers 4. A skill that is not listed is 0 — answered as 0, never rounded up and never guessed — which is exactly what you want. The agent never changes `limits.*` itself, and it adds to `approved_consents` only after you approve a specific company's consent text.

**`profile/answers.yaml` — the answers bank.** Screening questions repeat endlessly with different wording, so the bank maps phrases to answers. Matching is case-insensitive, any one phrase is enough, and when several entries match, the longest matching phrase wins; `{{dotted.path}}` is filled from profile.yaml, so changing a floor there changes every answer; `note` tells the agent how to use the answer. Keep every answer literally true:

```yaml
- match: ["legally authorized to work", "authorized to work in the united states", "eligible to work in the us"]
  answer: "Yes"
- match: ["require sponsorship", "need sponsorship", "visa sponsorship", "h-1b"]
  answer: "Yes"
  note: "H-1B transfer; covers now and in the future (work_authorization.needs_sponsorship)."
- match: ["us citizen", "green card", "permanent resident"]
  answer: "No"
- match: ["security clearance", "active clearance", "ts/sci"]
  answer: "No"
- match: ["w2", "w-2", "corp-to-corp", "c2c", "1099", "tax term"]
  answer: "C2C through Vendor Inc., or W2 or full-time with an H-1B transfer."
  note: "Only from work_authorization.employment_models. Single choice: the first allowed option the form offers. 1099 is not allowed."
- match: ["gender", "race", "ethnicity", "veteran", "disability", "self-identify"]
  answer: "Decline to self-identify"
- match: ["desired salary", "salary expectation", "expected compensation"]
  answer: "{{targets.min_salary_usd}}"
  note: "Number field: the number only. Text field: 'USD {{targets.min_salary_usd}} base, flexible on total compensation.'"
- match: ["hourly rate", "desired rate", "bill rate"]
  answer: "{{targets.min_rate_usd_per_hour}}"
- match: ["start date", "available to start", "notice period"]
  answer: "{{targets.start_date}}"
- match: ["text message", "sms", "marketing", "newsletter"]
  answer: "No"
```

Consent, privacy and terms checkboxes are never answered from this bank; they need a per-company entry in `approved_consents`. A question the bank cannot match is left blank in review mode and the agent asks you; in auto mode it stops that application and marks the row `needs-check` with the exact question. Once you answer a new question, add it to the bank and it is answered the same way from then on.

**`profile/master-resume.docx` — the master resume.** One file, at most two pages, in the structure from the next chapter: header, a one-line headline, three profile bullets, a skills line, experience with two to five bullets per role, education and certifications. `/job-setup` copies your file here (your original is never edited), dumps its paragraphs to `profile/master-resume.txt` with `tailor_resume.py --dump`, and records the exact text of five paragraphs as anchors. The tailoring script changes only those five per application: the headline, the three profile bullets and the skills line (reordered or trimmed, never extended). Every experience bullet stays as you wrote it. That is deliberate — it keeps the resume consistent across hundreds of applications and makes every interview answer defensible. If you edit any anchored paragraph in Word later, tailoring stops with exit code 2 (anchor not found) until you copy the new text into `resume.anchors` (run `--dump` again) or re-run `/job-setup`.

**Keep a claims register** for yourself next to it (`profile/claims.md`): for each resume bullet, two lines on what you actually did and where the number came from. The agent does not read it — its only sources of truth are profile.yaml, answers.yaml and the master resume — so move what it should use into those files: recurring screening answers into answers.yaml, and your best stories into `stories` in profile.yaml, where `/interview-prep` picks them up. If you cannot write the evidence for a bullet, the bullet should go.
