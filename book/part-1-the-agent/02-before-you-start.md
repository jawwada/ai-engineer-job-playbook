# 2. Before you start

Budget about an hour for setup and then 20–30 minutes a day while the search runs. Everything below is checked against the Claude Code documentation as of 2 October 2026; where a version matters it is stated.

**Accounts you need (you log in yourself; the agent never creates accounts or types passwords):**

| Account | Why | Notes |
| --- | --- | --- |
| Claude Pro, Max, Team or Enterprise (claude.ai) | Claude Code, the Chrome integration, the Gmail connector and Remote Control all need a claude.ai login (`/login`). An API key, a long-lived token or a third-party provider (Bedrock, Google's Agent Platform, Foundry) does not work for Chrome or Remote Control. | On Team and Enterprise an Owner must switch Remote Control on in the Claude Code admin settings first. |
| LinkedIn | Easy Apply, recruiter messages, job alerts | Keep your profile current; the agent reads it and never edits it. |
| Dice | The best US contract/C2C board for AI roles | Upload a resume and complete the profile once — Dice reuses it. |
| Indeed | Volume of US full-time AI roles | Indeed's terms forbid automating Indeed Apply (see Guardrails); the agent scouts and prefills there but never submits, in either mode. |
| Gmail | Job alerts in, recruiter mail out | A Google account; connected through the claude.ai Gmail connector, not through your password. |
| GitHub (optional) | Portfolio links on the resume; hosting this kit | Public repos with a README count more than private ones. |

**Software (one-time installs):**

1. Claude Code. macOS/Linux: `curl -fsSL https://claude.ai/install.sh | bash` — Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`. Then run `claude` in any folder and type `/login`, choosing the claude.ai sign-in. Check with `claude --version`.
2. Google Chrome or Microsoft Edge (Claude Code also connects to other Chromium browsers such as Brave, Arc, Vivaldi and Opera) with the **Claude in Chrome** extension, version 1.0.36 or later, from the Chrome Web Store. Sign the extension in with the same claude.ai account. Windows Subsystem for Linux is not supported for the browser integration — on Windows, run Claude Code natively in PowerShell, with Git for Windows installed so it has Git Bash for shell commands.
3. Python 3.10 or newer. You do not install packages yourself: the kit's installer creates a private environment in `~/job-search/.venv` and installs python-docx, pypdf and pyyaml into it, and the agent always runs the scripts with that interpreter (`.venv/bin/python scripts/...`). On macOS the system Python is 3.9, so install a newer one first (`brew install python@3.12`).
4. LibreOffice (free) so the tailoring script can convert .docx to PDF from the command line and count the pages. Without it, the script can still write the .docx (`--no-pdf`), but the two-page check cannot run.
5. git (to clone the kit; optionally to keep a local history of the workspace — the kit's `.gitignore` keeps your profile, tracker and applications out of any commit, and `git push` always asks first).

**Files you prepare once:**

- Your **master resume** as a .docx, at most two pages, with a headline, three summary bullets and a skills line near the top (the five paragraphs tailoring may change), in the format described in chapter 7. Everything the agent sends is derived from this file — employers, titles, skills and numbers come only from it.
- Your **truth file** (`profile/profile.yaml`): identity and links, work authorization and sponsorship, the employment models you accept, target titles, rate and salary floors, the remote rule and hard exclusions, years per skill with their aliases, the resume anchors, daily limits and the mode, the Gmail labels, consents you have approved, and STAR stories for interview prep. `/job-setup` fills it with you.
- Your **answers bank** (`profile/answers.yaml`): the standard screening questions (authorization, sponsorship, citizenship, clearance, W2/C2C, salary and rate, start date, relocation, travel, EEO) matched by phrase, with your exact answers. Screening questions are answered only from this file and the truth file.

**Workspace layout** (the kit's `install.sh` creates this):

```
~/job-search/
  CLAUDE.md                  # standing rules the agent reads every session
  .claude/settings.json      # permission rules (allow, ask, deny) and a notification hook
  .gitignore                 # keeps personal data out of any commit
  profile/
    profile.yaml             # truth file (written by /job-setup from profile.example.yaml)
    answers.yaml             # screening answers bank (from answers.example.yaml)
    master-resume.docx       # the one resume everything is tailored from (a copy of yours)
    master-resume.txt        # its paragraph dump, the text the agent reads
  tracker/
    applications.csv         # one row per job: id, platform, company, role, status, dates, files, notes
  scripts/
    tracker.py               # add, update, list, due, stats, dupe-check, remove (test rows only), pause
    tailor_resume.py         # --dump the master's paragraphs; anchor-based tailoring, PDF export,
                             # page check and numbers guard, with exit codes 0-5
  .venv/                     # private Python environment created by the installer
  applications/
    2026-10-02/li-4012345678/  # one folder per posting: jd.md, fit.md, spec.json, answers.md,
                             # tailored resume and cover letter (.docx, .pdf, .txt), prep.md
  inbox/                     # inbox/<date>/: saved recruiter threads and triage results
  scouting/                  # scouting/<date>.json plus the captured job descriptions
```

The `~/.claude/` folder (skills, agents, user settings) is separate from the workspace: skills and subagents are installed once per machine, the workspace holds your data.
