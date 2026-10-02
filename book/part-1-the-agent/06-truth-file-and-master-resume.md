# 6. Your truth file and master resume

An agent that applies for you is only as trustworthy as the facts you give it. The kit separates *what is true about you* (the truth file and the master resume) from *how to present it* (the tailoring rules). The agent may rephrase, reorder and emphasize; it may never add a skill, a year, a title or a number that is not in these two files. That one rule is what lets you switch on auto mode later without worrying about what it said.

**`profile/profile.yaml` — the truth file.** The installer copies an example; `/job-setup` fills it with you. The important parts:

```yaml
identity:
  name: Jane Doe
  email: jane@example.com
  phone: "+1 555 010 0000"
  location: {city: Austin, state: TX, country: US, timezone: America/Chicago}
  links: {linkedin: linkedin.com/in/janedoe, github: github.com/janedoe}
work_authorization:
  status: H-1B            # US citizen | green card | H-1B | OPT/STEM | TN | needs visa
  needs_sponsorship: true # answered honestly on every form
  employment_models: [C2C, W2]   # what you will accept
  c2c_vendor: "Vendor Inc."      # if you contract through an employer
targets:
  titles: [Forward Deployed Engineer, AI Engineer, Applied AI Engineer, GenAI Engineer, Solutions Engineer (AI)]
  seniority: [senior, staff, lead]
  remote_only: true
  min_rate_usd_per_hour: 95
  min_salary_usd: 190000
  start_date: 2 weeks notice
  max_posting_age_hours: 48
  exclude_if: ["US citizens only", "W2 only", "onsite", "clearance required"]
skills_years:               # the anti-overclaiming table; missing = 0
  python: 12
  langchain_langgraph: 3
  rag: 3
  aws: 8
  azure: 5
  gcp: 4
  kubernetes: 4
  dialogflow_cx: 1
  snowflake: 3
limits:
  max_applications_per_day: 15
  mode: review              # review | auto
```

When a form asks "years of experience with Snowflake", the agent reads `skills_years.snowflake`. If the key is missing it answers 0 and flags the job for you instead of guessing — which is exactly what you want.

**`profile/answers.yaml` — the answers bank.** Screening questions repeat endlessly with different wording, so the bank maps patterns to answers. Keep every answer literally true:

```yaml
- match: ["authorized to work", "legally authorized", "eligible to work in the US"]
  answer: "Yes"
- match: ["require sponsorship", "visa sponsorship", "now or in the future"]
  answer: "Yes — H-1B transfer"
- match: ["US citizen", "green card holder", "permanent resident"]
  answer: "No"
- match: ["security clearance"]
  answer: "No"
- match: ["W-2 only", "W2 employee"]
  answer: "No — corp-to-corp through Vendor Inc.; W2 possible with H-1B transfer"
- match: ["gender", "race", "ethnicity", "veteran", "disability"]
  answer: "Decline to self-identify"
- match: ["desired salary", "salary expectation"]
  answer: "$190,000 (negotiable)"
- match: ["hourly rate", "desired rate"]
  answer: "$95/h C2C (negotiable)"
- match: ["start date", "available to start"]
  answer: "Two weeks from offer"
- match: ["text messages", "SMS", "marketing"]
  answer: "No"
```

A question the bank cannot match is left blank in review mode and the agent asks you; in auto mode it skips that application and records why. Once you answer a new question, add it to the bank and it is answered the same way forever.

**`profile/master-resume.docx` — the master resume.** One file, two pages, in the structure from the next section: header, a one-line headline, three profile bullets, a *Core expertise* block grouped by theme, experience with two to five bullets per role, education and certifications. The tailoring script changes only three things per application: the headline, the three profile bullets and the order of keywords inside the expertise groups. Every experience bullet stays as you wrote it. That is deliberate — it keeps the resume consistent across hundreds of applications and makes every interview answer defensible.

**Keep a claims register** next to it (`profile/claims.md`): for each resume bullet, two lines on what you actually did and where the number came from. The agent uses it to write cover letters and screening answers with specifics, and you use it to prepare for interviews. If you cannot write the evidence for a bullet, the bullet should go.
