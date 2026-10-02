---
name: job-setup
description: First-run setup of the ~/job-search workspace. Reads the master resume, interviews the user for missing facts (work authorization, rates, remote rules, start date, links), writes profile/profile.yaml and profile/answers.yaml, records the exact resume anchor texts, and verifies the tailoring script, the two-page check and the tracker. Use when the user runs /job-setup or wants to create or redo their job-search profile.
argument-hint: "[path to master resume .docx]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Bash(.venv/bin/python *)
metadata:
  kit: job-agent-kit
---

# Job setup

Set up the job-search workspace for this user. Work from the workspace root (the folder with
CLAUDE.md, `scripts/` and `.venv/`). Optional argument, the master resume path: `$ARGUMENTS`

Facts come only from the resume and from the user. Never invent or "improve" a fact during setup.

## 1. Check the workspace

- Confirm that `scripts/tailor_resume.py`, `scripts/tracker.py`, `profile/profile.example.yaml`,
  `profile/answers.example.yaml` and `tracker/applications.csv` exist, and that
  `.venv/bin/python -c "import docx, pypdf, yaml"` succeeds. If not, tell the user to run
  `bash kit/install.sh` from the kit and stop.
- If `profile/profile.yaml` already exists, ask whether to update it (first copy it to
  `profile/profile.yaml.bak-<date>`) or stop.

## 2. Read the master resume

- Use the path from the arguments, or ask for it. It must be a .docx (Word, or a Google Docs
  export). If the user only has a PDF, ask them to export a .docx first.
- Copy it to `profile/master-resume.docx` (never edit the user's original), then dump it:
  `.venv/bin/python scripts/tailor_resume.py --dump profile/master-resume.docx > profile/master-resume.txt`
- Read the dump. Note name, contact details, links, titles, employers with dates, skills and every number.

## 3. Choose the anchors

The tailoring script rewrites only these paragraphs. Pick them from the dump and show each to the
user with its `[index]`:

- `headline`: the title line under the name.
- `summary_1`, `summary_2`, `summary_3`: the three profile or summary bullets at the top.
- `skills_line`: the core skills line. If it starts with a label such as "Skills:", use only the text
  after the label, so the label keeps its formatting.

If the resume has no headline or fewer than three summary bullets, explain that tailoring changes
only these places, suggest adding them in Word (each as its own paragraph), and wait for the new
file. Each anchor must be the whole paragraph (or the text after a label) and unique in the document.

## 4. Interview for missing facts

Ask in small batches (AskUserQuestion if available), proposing what the resume suggests:

1. Work authorization: status, sponsorship now or later, employment models accepted (W2, C2C, 1099,
   full-time), and the company that invoices C2C, if any.
2. Targets: titles (default Forward Deployed Engineer, AI Engineer, Applied AI Engineer), seniority,
   remote only, minimum hourly rate (USD), minimum base salary (USD), start date or notice period,
   maximum posting age (default 48 h), hard exclusions (clearance, onsite, W2-only, citizens-only and
   so on), and companies to avoid (current employer, its clients).
3. Location as written on forms, and links: LinkedIn, GitHub, portfolio.
4. `skills_years`: propose years per skill from the resume dates and let the user correct them. Never
   more than the resume supports. Include total professional experience.
5. Answers: travel, relocation, time zone, EEO (default: decline), how to answer salary questions.
6. Limits: mode (default review), applications per day (default 15), LinkedIn ceiling (default 25).
7. Gmail: ask the user to connect the Gmail connector at claude.ai (Settings > Connectors) and to
   create two labels with filters themselves (you do not create labels or filters):
   - `Jobs/Alerts`: for example `from:(jobalerts-noreply@linkedin.com OR indeed.com OR dice.com)`
   - `Jobs/Recruiters`: recruiter mail, labelled by hand or by a filter on words such as "C2C", "W2", "rate", "end client".

## 5. Write the profile files

- Copy `profile/profile.example.yaml` to `profile/profile.yaml` and replace every example value; keep
  the comments. Copy `profile/answers.example.yaml` to `profile/answers.yaml` and adapt every answer
  to the user's facts (authorization, sponsorship, citizenship, clearance, W2/C2C, rates, start date,
  travel, time zone). Keep the `{{...}}` placeholders where they fit.
- Fill `resume.anchors` by copying each paragraph's text from the dump exactly (do not retype or fix
  typos). Put each value in double quotes and escape inner double quotes.
- Validate: `.venv/bin/python -c "import yaml; [yaml.safe_load(open(f)) for f in ('profile/profile.yaml', 'profile/answers.yaml')]; print('yaml ok')"`

## 6. Dry run of the tailoring

- Write `applications/_setup-test/spec.json` with `"company": "Setup Test"`, `"role": "Dry run"` and
  one replacement per anchor whose `text` is that anchor's current text (so nothing changes).
- Run `.venv/bin/python scripts/tailor_resume.py --profile profile/profile.yaml --spec applications/_setup-test/spec.json`
- Expect exit 0, every anchor `exact` (or `substring` for a labelled skills line) and `"page_check": "pass"`.
  - Exit 2: an anchor is wrong. Copy it again from the dump and re-run.
  - Exit 3: the master resume is already longer than `max_pages`. Ask the user to shorten it, keeping
    a few lines of slack because tailored text varies in length, then re-run.
  - Exit 4: LibreOffice is missing or failed. Ask the user to install it (or set SOFFICE_PATH) and re-run.
- ATS readability: print the PDF text with
  `.venv/bin/python -c "import sys; from pypdf import PdfReader; print(''.join(p.extract_text() for p in PdfReader(sys.argv[1]).pages)[:1500])" "<resume pdf>"`
  and confirm that name, email and headline come out as text in a sensible order. If they do not
  (text in images, columns that interleave), tell the user what an ATS will see.

## 7. Tracker smoke test

- `.venv/bin/python scripts/tracker.py add --id setup-test --platform test --company "Setup Test" --role "Dry run" --url https://example.com/setup-test`
- `.venv/bin/python scripts/tracker.py list` shows the row. Then
  `.venv/bin/python scripts/tracker.py remove setup-test` and `list` again: the row is gone and the header is intact.
- Leave `applications/_setup-test/` in place (git ignores it) and tell the user they may delete it.

## 8. Finish

Summarize: work authorization and employment models, targets and floors, mode and caps, the five
anchors, the dry-run page count, the Gmail labels still to create, and the daily loop:
`/job-scout`, `/resume-tailor queued`, `/job-apply queued`, `/recruiter-inbox`, `/job-tracker due`.

End your final message with exactly this line: setup complete
