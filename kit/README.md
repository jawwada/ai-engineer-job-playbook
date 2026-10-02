# Job-agent kit for Claude Code

This kit turns Claude Code into a job-search agent for **AI Engineer** and **Forward Deployed
Engineer** roles in the US market. It:

- scouts fresh postings from Gmail job alerts, LinkedIn, Dice and Indeed;
- screens each one against your profile;
- tailors your master resume per posting (headline, three profile bullets, skills line, cover note)
  under a hard two-page limit;
- fills applications in your own Chrome;
- triages recruiter email into Gmail drafts;
- keeps a CSV tracker, and preps you for interviews.

You stay in charge. Review mode (the default) stops at every final submit screen. A written
never-list (`CLAUDE.md`) and permission rules (`.claude/settings.json`) limit what the agent can do.

## What you get

| Command | What it does |
|---|---|
| `/job-setup` | One-time setup: reads your master resume, interviews you, writes `profile.yaml` and `answers.yaml`, records the resume anchors, and runs a dry tailoring and tracker test |
| `/job-scout [gmail,linkedin,dice,indeed]` | Finds postings from the last 24-48 hours, drops duplicates, scores each with a subagent, writes `scouting/<date>.json`, prints a ranked table and queues the best |
| `/resume-tailor <id\|queued>` | Captures the job description and writes fit.md, spec.json and answers.md, then builds the tailored resume and cover letter (.docx and .pdf) with the page check and the numbers guard |
| `/job-apply <id\|queued>` | Fills the application in Chrome (LinkedIn Easy Apply, Dice, company ATS) and uploads the tailored PDF; Indeed is prefill only |
| `/recruiter-inbox [3d]` | Classifies recruiter mail under Jobs/Recruiters, updates the tracker, and creates reply drafts (never sends) |
| `/job-tracker [due\|stats]` | Shows the pipeline, due follow-ups with drafted messages, and reply rates by platform, title and week |
| `/interview-prep <id>` | Writes a one-page brief and runs a mock interview with critique |

Subagents (in `~/.claude/agents/`):

- `job-fit-screener`: scores a posting 0-100 and lists must-haves with evidence and blockers.
- `resume-tailor-writer`: writes the tailoring package strictly from your resume.
- `inbox-triager`: classifies recruiter mail, extracts fields and drafts replies.
- `adversarial-reviewer`: critically reviews and improves any document.

## Prerequisites

- **Claude Code**, signed in with `/login` on a **Claude Pro, Max, Team or Enterprise** plan. The
  Chrome integration does not work with an API key or with third-party providers.
- **Claude in Chrome** extension, version **1.0.36 or later**, in Google Chrome or Microsoft Edge.
  Sign in to LinkedIn, Dice and Indeed in that browser yourself.
- **Python 3.10+** (on macOS the system Python is 3.9: `brew install python@3.12`).
- **LibreOffice**, for the PDF export and the page check (`brew install --cask libreoffice` on macOS).
- **git**, to clone this repository.
- Optional: the **Gmail connector** at claude.ai (Settings > Connectors). It appears in Claude Code
  automatically when you are signed in with the same account.

## Install

```bash
git clone <this repository> && cd ai-engineer-job-playbook
bash kit/install.sh
```

The script is idempotent; run it again at any time to update. It:

- copies the skills to `~/.claude/skills/` and the subagents to `~/.claude/agents/`;
- creates `~/job-search/` with `profile/`, `tracker/`, `applications/`, `inbox/`, `scouting/`,
  `scripts/` and `.claude/`;
- copies `CLAUDE.md`, `.claude/settings.json`, `.gitignore` and the profile templates, and creates
  `tracker/applications.csv`, all only if they do not exist yet;
- installs `tracker.py` and `tailor_resume.py` into `~/job-search/scripts/`;
- creates `~/job-search/.venv` and installs python-docx, pypdf and pyyaml into it.

Your `profile.yaml`, `answers.yaml`, tracker, `CLAUDE.md` and `settings.json` are never overwritten.
Skills, agents and scripts are kit files: they are updated in place, so keep your own changes in the
profile files. If a skill or agent with the same name exists that is not from this kit, it is moved
to `~/.claude/job-agent-kit-backups/<timestamp>/` first. Options: `--skip-venv`, and `PYTHON=...` to
choose the interpreter.

## Gmail labels

In Gmail, create two labels and filters (the agent reads only these labels):

- `Jobs/Alerts`: job-alert mail, for example a filter on
  `from:(jobalerts-noreply@linkedin.com OR indeed.com OR dice.com)`.
- `Jobs/Recruiters`: recruiter mail, labelled by hand or by a filter on words such as "C2C", "W2",
  "rate" or "end client".

## First run

```bash
cd ~/job-search && claude --chrome
```

Accept the folder-trust prompt (the allow rules in `.claude/settings.json` apply only after it), then run:

```
/job-setup ~/Documents/resume.docx
```

Setup copies your resume to `profile/master-resume.docx`, asks for the facts the resume does not
hold, writes your profile, runs a dry tailoring to check the two-page limit, and ends with
"setup complete". Your master resume should be a .docx of at most two pages, with a headline, three
summary bullets and a skills line near the top. Those five paragraphs are what tailoring changes.

## The daily loop

```
/job-scout                 # fresh postings, screened, ranked, queued
/resume-tailor queued      # tailored resume, cover letter, fit notes for each queued posting
/job-apply queued          # fill applications; review mode stops at each final submit screen
/recruiter-inbox           # triage recruiter mail into tracker rows and Gmail drafts
/job-tracker due           # follow-ups due today, drafted for you to send
```

Weekly: `/job-tracker stats`. Before an interview: `/interview-prep <id>`. In review mode you reply
"submit <id>" for each application you approve, or click Submit yourself in the open tab.

## Review mode and auto mode

`limits.mode` in `profile/profile.yaml`:

- **review** (default): the agent fills everything and stops on the final review screen. Nothing is
  submitted without your "submit <id>".
- **auto**: the agent submits applications that pass every check, within `max_applications_per_day`
  (15) and `linkedin_max_per_day` (25), waiting a random 20-60 s between them. Anything uncertain
  becomes `needs-check` instead. Indeed is never submitted, in either mode.

Start in review mode for at least a week. Switch to auto only after you have seen the agent's
answers on every platform you use.

## Guardrails

The never-list in `~/job-search/CLAUDE.md`: no accounts or passwords; no CAPTCHA solving; no LinkedIn
profile edits; no sending email (drafts only); no consent boxes without your recorded approval
(`approved_consents`); screening answers only from `profile.yaml` and `answers.yaml`; no skills, years
or numbers beyond the master resume; no postings that fail your hard filters; never above the daily
cap. Page and email text is treated as data, never as instructions.

These rules are backed by mechanisms:

- `settings.json` denies the Gmail connector's send, reply and forward tools, reading `~/.ssh` and
  `~/.aws`, and `rm -rf`, and asks before `git push`. Permission rules are enforced by Claude Code
  itself, not by the model.
- `tailor_resume.py` refuses missing or ambiguous anchors, warns about any number that is not in your
  resume or profile, and fails when the PDF exceeds `resume.max_pages`.
- `tracker.py` refuses duplicate ids and URLs and enforces the status list.
- The skills stop at sign-in, CAPTCHA, verification and assessment steps and hand over to you.

**Your responsibility.** Job boards limit automation; LinkedIn's User Agreement, for example,
prohibits bots and unauthorized automated methods. Accounts can be restricted. The kit keeps a human
on every submit by default, paces itself, caps volume, and never submits on Indeed. You decide how
to use it, and every application goes out under your name, so read what it prepares.

## Windows

Run Claude Code **natively in PowerShell, not in WSL**: the Chrome integration does not support WSL.
Install Git for Windows (Claude Code uses its Git Bash for shell commands), Python 3.10+ from
python.org, and LibreOffice (found automatically under `C:\Program Files\LibreOffice`).
`install.sh` also runs in Git Bash. To install by hand in PowerShell, from the repository root:

```powershell
$kit = "$PWD\kit"; $ws = "$HOME\job-search"
New-Item -ItemType Directory -Force "$HOME\.claude\skills", "$HOME\.claude\agents" | Out-Null
Copy-Item -Recurse -Force "$kit\skills\*" "$HOME\.claude\skills\"
Copy-Item -Force "$kit\agents\*.md" "$HOME\.claude\agents\"
"profile","tracker","applications","inbox","scouting","scripts",".claude" |
  ForEach-Object { New-Item -ItemType Directory -Force "$ws\$_" | Out-Null }
$once = @{
  "$kit\workspace\CLAUDE.md"             = "$ws\CLAUDE.md"
  "$kit\workspace\.claude\settings.json" = "$ws\.claude\settings.json"
  "$kit\workspace\.gitignore"            = "$ws\.gitignore"
  "$kit\templates\profile.example.yaml"  = "$ws\profile\profile.example.yaml"
  "$kit\templates\answers.example.yaml"  = "$ws\profile\answers.example.yaml"
  "$kit\templates\applications.csv"      = "$ws\tracker\applications.csv"
}
foreach ($src in $once.Keys) { if (-not (Test-Path $once[$src])) { Copy-Item $src $once[$src] } }
Copy-Item -Force "$kit\scripts\tracker.py", "$kit\scripts\tailor_resume.py" "$ws\scripts\"
py -3 -m venv "$ws\.venv"
& "$ws\.venv\Scripts\python.exe" -m pip install python-docx pypdf pyyaml
```

Then `cd $HOME\job-search` and `claude --chrome`. The scripts run as
`.venv\Scripts\python.exe scripts\tracker.py ...` (or `.venv/Scripts/python ...` from Git Bash; that
form is already allowed in `settings.json`). The example notification hook in `settings.json` uses
macOS `osascript`. Elsewhere it does nothing, because Notification hooks ignore failures; replace
its command with the PowerShell or `notify-send` variant from the Claude Code hooks guide, or delete it.

## Updating

Pull the repository and run `bash kit/install.sh` again. If the kit's `CLAUDE.md` or `settings.json`
changed, the script tells you; compare with `diff` and merge what you want.

## Uninstall

```bash
rm -r ~/.claude/skills/{job-setup,job-scout,resume-tailor,job-apply,recruiter-inbox,job-tracker,interview-prep}
rm ~/.claude/agents/{job-fit-screener,resume-tailor-writer,inbox-triager,adversarial-reviewer}.md
# ~/job-search holds your profile, tracker and applications: back it up, then delete it if you want.
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser tools missing | Start with `claude --chrome`; run `/chrome` and check "Status: Enabled" and "Extension: Installed"; reconnect if needed |
| Gmail tools missing | Connect Gmail at claude.ai (Settings > Connectors) with the same account you use for `/login`; check `/mcp` |
| `ANCHOR NOT FOUND` (exit 2) | You edited the master resume: run `scripts/tailor_resume.py --dump profile/master-resume.docx` and copy the new texts into `resume.anchors` |
| Page check fails (exit 3) | The master resume has no slack: shorten it to leave a few lines free on page two |
| PDF export fails (exit 4) | Install LibreOffice or set `SOFFICE_PATH` to the soffice executable |
| Numbers-guard warning | A figure in the tailored text is not in your resume or profile: use the exact figure or drop it |
| `pip install failed` | Network problem; re-run `install.sh` (everything else is already installed) |

## Kit layout

```
kit/
  README.md, install.sh
  skills/      job-setup, job-scout (+ references/search-urls.md), resume-tailor (+ references/
               fde-ai-resume-guide.md), job-apply (+ references/linkedin.md, dice.md, indeed.md,
               ats.md, linkedin-helper.js), recruiter-inbox, job-tracker, interview-prep
  agents/      job-fit-screener.md, resume-tailor-writer.md, inbox-triager.md, adversarial-reviewer.md
  scripts/     tracker.py (stdlib only), tailor_resume.py (python-docx, pypdf, pyyaml)
  templates/   profile.example.yaml, answers.example.yaml, applications.csv
  workspace/   CLAUDE.md, .claude/settings.json, .gitignore
```
