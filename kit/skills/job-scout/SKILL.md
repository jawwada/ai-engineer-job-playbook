---
name: job-scout
description: Finds fresh US AI Engineer and Forward Deployed Engineer postings from Gmail job alerts, LinkedIn, Dice and Indeed, drops duplicates against the tracker, scores each new posting with the job-fit-screener subagent, writes scouting/<date>.json, prints a ranked table and queues the best ones. Use when the user runs /job-scout or asks to find, search or scout for new jobs.
argument-hint: "[gmail,linkedin,dice,indeed]"
allowed-tools:
  - Read
  - Bash(.venv/bin/python scripts/tracker.py *)
metadata:
  kit: job-agent-kit
---

# Job scout

Sources: `$ARGUMENTS` (comma-separated subset of gmail, linkedin, dice, indeed; empty means all four).
Work from the workspace root and follow CLAUDE.md. Search URL patterns and parameters:
`${CLAUDE_SKILL_DIR}/references/search-urls.md` (read it before the first search).

## 0. Prepare

- Read `profile/profile.yaml`: `targets`, `work_authorization`, `limits`, `gmail.labels`.
- `<date>` is today (YYYY-MM-DD). Create `scouting/<date>/`. Note the current time: posting ages are
  measured from it.

## 1. Gmail job alerts (source `gmail`)

- List the Gmail labels and take the ID of `gmail.labels.alerts` (Jobs/Alerts); search needs the ID.
  Search `label:<ID> newer_than:1d`. Results preview only the oldest messages, so open each thread in
  full (plain text).
- Collect job links: LinkedIn `/jobs/view/<id>` (alerts use `/comm/jobs/view/<id>`), Dice
  `/job-detail/<uuid>`, Indeed `jk=<key>`. Keep the email's received time as proof of freshness.
- Read no other label and no other mail.

## 2. Job boards (sources `linkedin`, `dice`, `indeed`)

Use Claude in Chrome (the user's signed-in browser). For each title in `targets.titles`, and each
employment type the profile accepts, open the search URL from the reference file:

- LinkedIn: Easy Apply, remote, United States, posted within `max_posting_age_hours`, newest first.
- Dice: remote, posted today or in the last 3 days, employment-type filter.
- Indeed: remote, last 24 hours (scouting only; Indeed applications are never submitted by you).

Read result lists with get_page_text. Keep id, title, company, location, posted age, employment
type, rate or salary, Easy Apply flag. Open each candidate that passes the quick filters and capture
the full job description. Pace yourself: a few seconds between page loads, at most 3 result pages
per search. At a login wall, CAPTCHA or "unusual activity" page, stop that source and tell the user.

## 3. Quick filters (before screening)

Record as `skipped` (reason in notes) any posting that is:

- older than `targets.max_posting_age_hours` (unknown age is stale unless a fresh alert proves otherwise);
- from `targets.exclude_companies`, or containing a `targets.exclude_if` phrase;
- hybrid or onsite when `remote_only` is true;
- clearly below `min_rate_usd_per_hour` or `min_salary_usd` when pay is shown;
- not a target title or seniority at all.

## 4. Deduplicate

- One call for all candidate URLs: `.venv/bin/python scripts/tracker.py dupe-check --url <u1> --url <u2> ...`
  (exit 1 means at least one is already tracked), plus `dupe-check --company "<c>" --role "<r>"` per posting.
- The same role posted by several vendors (same end client, near-identical text) counts once: keep
  the best source (Easy Apply or the direct employer) and skip the rest as "duplicate of <id>".

## 5. Screen

- Save each new description to `scouting/<date>/<id>.md` with a header: id, url, apply url, company,
  title, location, employment, rate, posted age in hours, source. Ids follow CLAUDE.md
  (`li-`, `dice-`, `indeed-`, `ats-`).
- Delegate each posting to the **job-fit-screener** subagent (several in parallel is fine). Give it the
  .md path, `profile/profile.yaml`, `profile/master-resume.txt` and the posted age. It returns JSON with
  score, must-haves, blockers and a recommendation.
- Add the tracker row right away:
  `.venv/bin/python scripts/tracker.py add --id <id> --platform <linkedin|dice|indeed|ats> --company "<c>" --role "<r>" --url "<url>" --apply-url "<apply url>" --location "<loc>" --employment "<type>" --rate-or-salary "<pay>" --fit-score <score> --status screened --notes "<one-line verdict>"`
  A posting with blockers gets `--status skipped` and the blockers in notes. Postings dropped in
  steps 3 and 4 are added as `skipped` too, so tomorrow's run does not screen them again.

## 6. Report

- Write `scouting/<date>.json`: a list of objects with id, platform, company, role, url, apply_url,
  location, employment, rate_or_salary, posted_age_hours, easy_apply, score, recommendation,
  blockers, must_haves_missing, jd_path.
- Print a table ranked by score (id, company, role, platform, employment, pay, age in hours, score,
  blockers), then counts: found, duplicates, skipped by reason, screened.

## 7. Queue

- Room today = `limits.max_applications_per_day` minus "Submitted today" (from
  `.venv/bin/python scripts/tracker.py stats`) minus rows already `queued`, `tailored` or `ready`.
- **review** mode: ask the user which ids to queue (ids, "top N" or "none").
- **auto** mode: queue screened rows with score >= 75 and no blockers, best first, up to the room
  left (LinkedIn rows also within `limits.linkedin_max_per_day`). Indeed rows may be queued; they will
  only be prefilled.
- For each: `.venv/bin/python scripts/tracker.py update <id> --status queued`.
- Finish with the next step: `/resume-tailor queued`.
