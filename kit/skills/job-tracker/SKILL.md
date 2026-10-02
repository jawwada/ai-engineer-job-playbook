---
name: job-tracker
description: Shows the job-search pipeline from tracker/applications.csv, lists follow-ups that are due with drafted follow-up messages (drafts only), and reports weekly reply rates by platform and title. Use when the user runs /job-tracker or asks about application status, follow-ups or reply rates.
argument-hint: "[due | stats]"
allowed-tools:
  - Read
  - Bash(.venv/bin/python scripts/tracker.py *)
metadata:
  kit: job-agent-kit
---

# Job tracker

Mode: `$ARGUMENTS`: empty (pipeline), `due` or `stats`. Work from the workspace root. The tracker CSV
is the source of truth; change it only through `scripts/tracker.py`, never by editing the file.

## No argument: the pipeline

1. Run `.venv/bin/python scripts/tracker.py stats` and `.venv/bin/python scripts/tracker.py list --json`.
2. Show counts per status, then the action lists in this order:
   - `ready`: applications at the review screen or Indeed prefills waiting for the user (company,
     role, platform, since when);
   - `needs-check`: each with the reason from its notes and the decision the user must make;
   - `interview` and `replied`: the next step from the notes;
   - `queued` and `tailored`: what `/resume-tailor` and `/job-apply` will pick up next;
   - follow-ups due today (count), and "Submitted today" against `limits.max_applications_per_day`.
3. Keep it short and end with the next useful command.

## `due`: follow-ups

1. Run `.venv/bin/python scripts/tracker.py due --json`.
2. For each row, read `applications/*/<id>/fit.md` if it exists and write a follow-up of at most 90
   words: the role and the date applied, one specific match from fit.md, availability, and a question
   about next steps. Facts only from profile.yaml and the master resume.
3. Drafts only, never send:
   - recruiter rows (`mail-` ids, or notes with a recruiter's email address): create a Gmail reply
     draft in that thread, or a new draft to that address;
   - other rows: save `applications/<date>/<id>/follow-up.md` with the text and where to send it (the
     job poster on LinkedIn, or the recruiter contact from the notes).
4. Record it: `.venv/bin/python scripts/tracker.py update <id> --notes "follow-up drafted"`. When the
   user confirms they sent it, set the next check:
   `.venv/bin/python scripts/tracker.py update <id> --follow-up-on <date 7 days later>`.

## `stats`: the weekly report

1. Run `.venv/bin/python scripts/tracker.py stats --since 28d --json` and
   `.venv/bin/python scripts/tracker.py stats --json` (all time).
2. Report applications per ISO week (last 4 weeks), and reply rate and interview rate by platform, by
   title family and by week; then the current pipeline and "Submitted today" against the cap.
   (A reply is any response: replied, interview, rejected or offer.)
3. Read the numbers honestly: say when samples are small (under about 20 applications), and remember
   that replies lag 1-2 weeks, so the latest week always looks worse.
4. Suggest at most three concrete changes, for example: more searches for a title family that gets
   replies; fewer applications on a platform with no replies after 20 or more; a higher queue
   threshold if low fit scores never get replies.
