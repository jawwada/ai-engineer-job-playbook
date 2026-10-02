# 1. What you're building

You set up Claude Code as a job-search assistant: it finds fresh US AI roles, tailors your resume to each one, fills the application in your own logged-in browser, logs everything in a tracker, and drafts replies to recruiters — while you approve what gets sent.

It is built from a few plain files you can read and edit, not a black box:

| Part | What it does | Where it lives |
| --- | --- | --- |
| Claude Code | The agent: runs in your terminal, reads and writes files, calls tools | `claude` command |
| `CLAUDE.md` | Standing rules: honesty, freshness, daily caps, what it must never do | `~/job-search/CLAUDE.md` |
| Skills | Step-by-step playbooks: setup, scout, tailor, apply, inbox, tracker | `~/.claude/skills/<name>/SKILL.md` |
| Subagents | Helpers that work in parallel: fit screening, resume tailoring | `~/.claude/agents/*.md` |
| Claude in Chrome | Drives LinkedIn, Dice and Indeed inside your own Chrome | Chrome extension + `claude --chrome` |
| Gmail connector | Reads job alerts and recruiter mail, prepares reply drafts | claude.ai connector, listed in `/mcp` |
| Truth file, master resume, tracker | Your facts, your 2-page resume, one row per job | `~/job-search/profile/`, `~/job-search/tracker/` |

The agent runs in one of two modes, set in `profile.yaml`:

- **Review mode (default):** it fills every form and stops on the final review screen; you look, then click Submit or tell it to submit.
- **Auto mode:** it submits on its own within daily caps. Switch this on only after a week of clean reviews, and read *Guardrails* first — some sites forbid automated applying.

Background knowledge for the roles (the platform landscape, RAG, knowledge graphs, conversational AI, observability and the interview topics) is in Parts 2 to 4 of this book.

```mermaid
flowchart LR
  YOU["You: review, approve, interview"] --> CC["Claude Code in ~/job-search"]
  CC --> SK["Skills: job-setup, job-scout, resume-tailor, job-apply, recruiter-inbox, job-tracker, interview-prep"]
  CC --> SA["Subagents: job-fit-screener, resume-tailor-writer, inbox-triager, adversarial-reviewer"]
  CC --> CH["Claude in Chrome: LinkedIn, Dice, Indeed, company ATS forms"]
  CC --> GM["Gmail connector: alerts in, drafts out"]
  CC --> FS[("Files: profile, master resume, tracker, applications")]
  CC --> RC["Remote Control: phone and web"]
```
