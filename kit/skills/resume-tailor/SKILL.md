---
name: resume-tailor
description: Builds the application package for one tracker id or for every queued posting. Captures the job description, has the resume-tailor-writer subagent write fit.md, spec.json and answers.md from the master resume only, runs tailor_resume.py to produce the tailored resume and cover letter (.docx and .pdf), enforces the two-page limit and the numbers guard, and marks the row tailored. Use when the user runs /resume-tailor or asks to tailor a resume or prepare an application.
argument-hint: "<tracker-id | queued>"
allowed-tools:
  - Read
  - Bash(.venv/bin/python scripts/tracker.py *)
  - Bash(.venv/bin/python scripts/tailor_resume.py *)
metadata:
  kit: job-agent-kit
---

# Resume tailor

Target: `$ARGUMENTS`, either a tracker id or `queued` (every row with status `queued`, best fit
first). Work from the workspace root and follow CLAUDE.md. What FDE and AI Engineer screens look for,
and the bullet and ATS rules: `${CLAUDE_SKILL_DIR}/references/fde-ai-resume-guide.md`.

## 0. Prepare

- Resolve the rows: `.venv/bin/python scripts/tracker.py list --status queued --json`, or the single
  id. Refuse a row that is already `submitted` or later.
- If `profile/master-resume.docx` is newer than `profile/master-resume.txt`, refresh the dump:
  `.venv/bin/python scripts/tailor_resume.py --dump profile/master-resume.docx > profile/master-resume.txt`
- Read `profile/profile.yaml` once (anchors, max_pages, floors).

## 1. For each row

1. **Folder**: `applications/<today>/<id>/`, or the existing `applications/*/<id>/` if there is one.
2. **Job description** to `jd.md`: copy `scouting/*/<id>.md` if present; otherwise open the posting in
   Chrome and capture the full text with get_page_text. Start the file with id, company, role, url,
   apply url, location, employment, pay, posted date and capture time. If the posting is closed
   ("No longer accepting applications"), set the row to `skipped` with that reason and go on.
3. **Write**: delegate to the **resume-tailor-writer** subagent. Give it the folder path, `jd.md`,
   `profile/profile.yaml`, `profile/answers.yaml`, `profile/master-resume.txt` and the guide path above.
   It writes `fit.md`, `spec.json` and `answers.md` into the folder.
4. **Check the spec before building**:
   - valid JSON; `company` and `role` match the row;
   - replacements only for `headline`, `summary_1`, `summary_2`, `summary_3` and optionally `skills_line`;
   - headline at most 85 characters;
   - each summary bullet carries a number that appears in `profile/master-resume.txt`;
   - the skills line only reorders or drops skills from the current skills line;
   - cover letter body about 150 words, facts from the resume and profile only.
   If a check fails, send the spec back to the writer with the exact problem.
5. **Build**:
   `.venv/bin/python scripts/tailor_resume.py --profile profile/profile.yaml --spec applications/<date>/<id>/spec.json`
   Read the JSON summary it prints:
   - exit 0, `"page_check": "pass"` and an empty `numbers_guard.unsupported`: done.
   - `numbers_guard.unsupported` not empty: that figure is not in the master resume or profile. Use it
     exactly as the master states it, or drop it, then re-run. Never ship an unsupported number.
   - exit 2 (anchor not found): the master resume or the anchors changed. Stop and ask the user to
     re-run `/job-setup` (step 3, anchors).
   - exit 3 (too many pages): shorten the longest replacement (headline first, then the longest
     bullet) and re-run. After two failed attempts, mark `needs-check`.
   - exit 4 (PDF failed): report the LibreOffice error and mark `needs-check`.
6. **Look at the result**: the resume PDF text (pypdf) reads in a sensible order, the headline and
   bullets read naturally next to the untouched experience section, and `answers.md` flags every
   UNKNOWN question.
7. **Record it immediately**:
   `.venv/bin/python scripts/tracker.py update <id> --status tailored --resume-file "<resume pdf>" --cover-file "<cover pdf>" --notes "tailored; fit <score>; gaps: <short list>"`

## 2. Report

One line per row: company, role, fit score, files written, gaps from fit.md, and any UNKNOWN
screening questions the user must answer (offer to add the answers to `profile/answers.yaml`).
Next step: `/job-apply queued`.
