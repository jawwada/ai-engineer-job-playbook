---
name: job-apply
description: Fills job applications in the user's Chrome for one tracker id or for every tailored posting, uploading the tailored PDF and answering only from profile.yaml and answers.yaml, with playbooks for LinkedIn Easy Apply, Dice, Indeed (prefill only) and company ATS (Greenhouse, Lever, Ashby; Workday stops). Review mode stops on the final review screen; auto mode submits within the daily caps. Use when the user runs /job-apply.
argument-hint: "<tracker-id | queued>"
disable-model-invocation: true
allowed-tools:
  - Read
  - Bash(.venv/bin/python scripts/tracker.py *)
metadata:
  kit: job-agent-kit
---

# Job apply

Target: `$ARGUMENTS`, either a tracker id or `queued` (the apply queue: every row with status
`tailored`, best fit first). Work from the workspace root. CLAUDE.md applies in full. Read the
playbook for a platform before its first application in a session:

- LinkedIn Easy Apply: `${CLAUDE_SKILL_DIR}/references/linkedin.md` (page helper: `${CLAUDE_SKILL_DIR}/references/linkedin-helper.js`)
- Dice: `${CLAUDE_SKILL_DIR}/references/dice.md`
- Indeed (prefill only): `${CLAUDE_SKILL_DIR}/references/indeed.md`
- Greenhouse, Lever, Ashby, Workday: `${CLAUDE_SKILL_DIR}/references/ats.md`

## 0. Before the first application

- Read `profile/profile.yaml` (identity, work_authorization, skills_years, skill_aliases, limits,
  approved_consents) and `profile/answers.yaml`.
- Mode is `limits.mode`. Read "Submitted today" from `.venv/bin/python scripts/tracker.py stats`.
- Rows: `.venv/bin/python scripts/tracker.py list --status tailored --json`, or the one id. A row that
  is not `tailored` yet needs `/resume-tailor <id>` first: say so and skip it.

## 1. Pre-flight for each row (all must pass; otherwise skip it and say why)

- The tailored resume PDF in `resume_file` exists (and the cover letter, if the posting wants one).
- `fit.md` lists no blockers, and the posting was fresh when scouted. A closed posting becomes `skipped`.
- `.venv/bin/python scripts/tracker.py dupe-check --url "<apply url or url>" --company "<c>" --role "<r>"`
  finds only this row.
- Room is left under `max_applications_per_day`, and on LinkedIn under `linkedin_max_per_day`.

## 2. Fill the application

1. Open the apply URL in a new tab and follow the platform playbook.
2. Contact fields come from `identity`. Upload the tailored resume PDF for this id with the
   file-upload tool. Never click a file input or an "Upload" button (that opens the native file
   picker, which you cannot use); locate the input with find or read_page and pass its ref. Attach the
   cover letter PDF only to a cover-letter upload field, and paste the .txt into a cover-letter text box.
3. Answer every question from an allowed source:
   - `answers.yaml` (the longest matching phrase wins; fill `{{...}}` from profile.yaml) or this
     posting's `answers.md`;
   - years-of-X: `skills_years` through `skill_aliases`; a skill not listed is 0; never round up;
   - nothing matches: do not guess. Leave the field, note the exact question, and continue to the
     review step (review mode) or stop this application and mark it `needs-check` (auto mode).
4. Consent, privacy or terms boxes: tick only if `approved_consents` lists this company and this
   consent. Otherwise ask the user (review mode) or mark `needs-check` (auto mode). If the user
   approves, add {company, consent, approved_on} to `approved_consents` first, then tick.
5. Leave every marketing, SMS, newsletter, "follow company" and talent-community box unticked.
6. Stop and hand over at any account creation, password, verification code, CAPTCHA, assessment or
   profile-editing step.

## 3. The review screen

- Check what will be sent (LinkedIn: `jobHelper.inspect()`; elsewhere read_page or get_page_text):
  every field from an allowed source, the right resume attached, opt-in boxes unticked.
- **review** mode: stop here. Tell the user the id, company, role and tab, list the answers entered
  (mark any you were unsure of), and say: "Reply 'submit <id>' or submit it yourself."
  Then `.venv/bin/python scripts/tracker.py update <id> --status ready --notes "at review screen"`.
- **auto** mode: submit if every check passed and the platform is not Indeed. Indeed always stops as
  in review mode.
- When the user says "submit <id>": re-check the caps, click the final submit button in that tab,
  then verify.

## 4. Verify and record (immediately)

- Confirm the confirmation message or page. Where the platform keeps an applied list, find the job
  there (LinkedIn: My Jobs > Applied; Dice: the job page shows Applied).
- Confirmed: `.venv/bin/python scripts/tracker.py update <id> --status submitted --notes "<platform>: <how>; verified in <where>"`
  (this sets date_applied and a follow-up date 7 days later).
- Not confirmed, or anything was guessed: `.venv/bin/python scripts/tracker.py update <id> --status needs-check --notes "<exact reason>"`
- Close the tab.

## 5. Pace and continue

- Before the next application: `.venv/bin/python scripts/tracker.py pause` (random 20-60 s).
- Stop when the cap is reached, the queue is empty, or a site shows a limit or a bot check.
- Finish with a table (id, company, platform, outcome: submitted, ready, needs-check or skipped, and
  the reason) and "Submitted today" from `tracker.py stats`.
