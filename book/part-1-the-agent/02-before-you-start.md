# 2. Before you start

Budget about an hour for setup and then 20–30 minutes a day while the search runs. Everything below is checked against the Claude Code documentation as of 2 October 2026; where a version matters it is stated.

**Accounts you need (you log in yourself; the agent never creates accounts or types passwords):**

| Account | Why | Notes |
| --- | --- | --- |
| Claude Pro or Max (claude.ai) | Claude Code, the Chrome integration, the Gmail connector and Remote Control all require a claude.ai login. An API key does not work for Chrome or Remote Control. | Team/Enterprise also work if the admin has enabled Remote Control. |
| LinkedIn | Easy Apply, recruiter messages, job alerts | Keep your profile current; the agent reads it but does not edit it unless you ask. |
| Dice | The best US contract/C2C board for AI roles | Upload a resume and complete the profile once — Dice reuses it. |
| Indeed | Volume of US full-time AI roles | Indeed's terms forbid automating Indeed Apply (see Guardrails); the agent scouts and prefills in review mode only. |
| Gmail | Job alerts in, recruiter mail out | A Google account; connected through the claude.ai Gmail connector, not through your password. |
| GitHub (optional) | Portfolio links on the resume; hosting this kit | Public repos with a README count more than private ones. |

**Software (one-time installs):**

1. Claude Code. macOS/Linux: `curl -fsSL https://claude.ai/install.sh | bash` — Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`. Then run `claude` in any folder and type `/login`, choosing the claude.ai sign-in. Check with `claude --version`.
2. Google Chrome (or Edge, Brave, Arc, Vivaldi, Opera) with the **Claude in Chrome** extension, version 1.0.36 or later, from the Chrome Web Store. Sign the extension in with the same claude.ai account. Windows Subsystem for Linux is not supported for the browser integration — on Windows, run Claude Code in PowerShell.
3. Python 3.10 or newer with `pip install python-docx pypdf pyyaml` — the tailoring script edits your resume as a .docx and checks the page count of the PDF.
4. LibreOffice (free) so the agent can convert .docx to PDF from the command line (`soffice --headless --convert-to pdf`). Word works too if you prefer to export by hand.
5. git (to clone the kit and to keep a history of every tailored resume).

**Files you prepare once:**

- Your **master resume** as a .docx, two pages, in the format described in *Optimizing the resume* below. Everything the agent sends is derived from this file — it never writes a line that is not supported by it.
- Your **truth file** (`profile/profile.yaml`): name, location, work authorization, visa status, rate and salary floors, remote/onsite rules, years per skill, employers, degrees, links. The agent answers screening questions only from this file.
- Your **answers bank** (`profile/answers.yaml`): the 30–40 standard screening questions (authorization, sponsorship, start date, relocation, clearance, W2/C2C, salary) with your exact answers.

**Workspace layout** (the kit's `install.sh` creates this):

```
~/job-search/
  CLAUDE.md                  # standing rules the agent reads every session
  .claude/settings.json      # permission allow-list for this folder
  profile/
    profile.yaml             # truth file
    answers.yaml             # screening answers bank
    master-resume.docx       # the one resume everything is tailored from
  tracker/
    applications.csv         # one row per job: id, company, role, platform, status, dates, files
  scripts/
    tracker.py               # add, update, list, due follow-ups, stats
    tailor_resume.py         # anchor-based .docx tailoring, PDF export, page and number checks
  .venv/                     # private Python environment created by the installer
  applications/
    2026-10-02/acme-fde/     # one folder per application: resume.docx/.pdf, cover.txt, jd.md, answers.md
  inbox/                     # recruiter mail digests and drafted replies
  scouting/                  # daily search results (jobs.json) and fit scores
```

The `~/.claude/` folder (skills, agents, user settings) is separate from the workspace: skills and subagents are installed once per machine, the workspace holds your data.
