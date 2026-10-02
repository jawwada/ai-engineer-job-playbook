# 3. Install the job-agent kit into Claude Code

The kit is a folder of plain text files. Nothing is compiled; you can open every file and change the rules.

**1. Get the kit.** Clone the repo (or unzip the archive you were sent) somewhere you keep code:

```
git clone https://github.com/jawwada/ai-engineer-job-playbook.git
cd ai-engineer-job-playbook
```

It contains `book/` (this book), `kit/` (what gets installed) and `tools/` (the script that builds the book into one file).

**2. Run the installer.** `bash kit/install.sh` does six things, all of them visible in the script: copies `kit/skills/*` to `~/.claude/skills/` and `kit/agents/*` to `~/.claude/agents/` (a same-named skill or agent that is not from the kit is first moved to `~/.claude/job-agent-kit-backups/<timestamp>/`); creates `~/job-search/` with the layout from the previous chapter; copies `CLAUDE.md`, `.claude/settings.json`, `.gitignore` and the `profile/*.example.yaml` templates into it and creates `tracker/applications.csv` (each only if it does not exist yet); installs `tracker.py` and `tailor_resume.py` into `~/job-search/scripts/`; creates `~/job-search/.venv` with python-docx, pypdf and pyyaml; and reports what it created, updated or kept. Running it again is safe: your `profile.yaml`, `answers.yaml`, tracker, `CLAUDE.md` and `settings.json` are never overwritten, while the kit's own files (skills, agents, scripts) are updated in place — so keep your changes in the profile files, not in a SKILL.md. Options: `--skip-venv`, and `PYTHON=/path/to/python3.12` to choose the interpreter.

**3. Start Claude Code in the workspace, with the browser attached.**

```
cd ~/job-search
claude --chrome
```

The first time, accept the workspace-trust dialog (the allow rules in `.claude/settings.json` take effect only after you trust the folder; the deny and ask rules apply regardless) and the one-time Chrome introduction. Then check four things inside the session:

| Type | You should see |
| --- | --- |
| `/` | the kit's commands in the menu: `/job-setup`, `/job-scout`, `/resume-tailor`, `/job-apply`, `/recruiter-inbox`, `/job-tracker`, `/interview-prep` |
| `/agents` | the subagents `job-fit-screener`, `resume-tailor-writer`, `inbox-triager`, `adversarial-reviewer` |
| `/chrome` | Status: Enabled · Extension: Installed |
| `/mcp` | `claude-in-chrome` and, once you have connected it, the Gmail connector |

If the commands are missing, the `~/.claude/skills` folder did not exist when the session started: run `/reload-skills`. Subagents are watched the same way, but if `~/.claude/agents` was created during a running session, restart `claude` once. Skills and agents are picked up live after that — edit a SKILL.md and the next use sees the change.

**4. Set permissions once.** The installer writes `~/job-search/.claude/settings.json`. It pre-approves the boring, safe actions so the agent does not ask forty times a day, and it blocks the dangerous ones:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Read(~/job-search/**)",
      "Edit(~/job-search/**)",
      "Bash(.venv/bin/python *)",
      "Bash(~/job-search/.venv/bin/python *)",
      "Bash(.venv/Scripts/python *)",
      "Bash(soffice *)",
      "Bash(git status *)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "WebFetch(domain:linkedin.com)",
      "WebFetch(domain:*.linkedin.com)",
      "WebFetch(domain:dice.com)",
      "WebFetch(domain:*.dice.com)",
      "WebFetch(domain:indeed.com)",
      "WebFetch(domain:*.indeed.com)",
      "WebFetch(domain:boards.greenhouse.io)",
      "WebFetch(domain:job-boards.greenhouse.io)",
      "WebFetch(domain:jobs.lever.co)",
      "WebFetch(domain:jobs.ashbyhq.com)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Bash(rm -rf *)",
      "mcp__claude_ai_Gmail__send_message",
      "mcp__claude_ai_Gmail__reply",
      "mcp__claude_ai_Gmail__forward"
    ]
  },
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Job agent\"'"
          }
        ]
      }
    ]
  }
}
```

It also asks before `git push`, and it denies the Gmail connector's send, reply and forward tools (connector tools appear as `mcp__claude_ai_<server>__<tool>`), so "drafts only" is enforced by the harness rather than by a prompt. The only scripts it pre-approves are those run with the workspace's Python (`.venv/bin/python ...`), which is why every skill calls `.venv/bin/python scripts/tracker.py` or `.venv/bin/python scripts/tailor_resume.py` rather than a bare `python`. Rule syntax to remember: `Bash(git *)` matches every git command (the space before `*` matters: `Bash(ls *)` does not match `lsof`), `Read(~/path/**)` is a path rule, `WebFetch(domain:x)` is per domain and `domain:*.x` covers its subdomains, deny beats ask beats allow, and `mcp__claude-in-chrome__*` would pre-approve every browser action. The browser tools are deliberately *not* on the allow list for the first week: when Claude Code shows a prompt beginning "Claude in Chrome wants to…", choose the option that allows all actions on that site for the session. After a week of clean reviews you can add `"mcp__claude-in-chrome__*"` to the allow list; site-level permissions are still enforced by the extension itself.

The modes, in case you change `defaultMode`: `default` (labelled Manual in recent versions) prompts on first use of each tool; `acceptEdits` auto-accepts file edits and simple filesystem commands such as `mkdir` and `cp` in the workspace (recommended here); `plan` explores read-only and edits nothing; `auto` lets a background classifier approve routine actions instead of you; `dontAsk` denies anything that would prompt; `bypassPermissions` skips prompts and is not appropriate for a tool that submits job applications under your name.

**5. First run.** Type `/job-setup ~/Documents/resume.docx` (your master resume's path). `/job-setup` and `/job-apply` are marked `disable-model-invocation: true`, so they run only when you type them — Claude will not start setup or an application on its own, and a sentence such as "set me up" does not load them. The skill copies your resume to `profile/master-resume.docx` and dumps its paragraphs, shows you the five anchors (headline, three summary bullets, skills line), interviews you for the facts it cannot infer (work authorization, employment models, rate floors, remote rules, start date, years per skill), writes `profile/profile.yaml` and `profile/answers.yaml`, runs a dry tailoring that must come back with every anchor found and a two-page PDF, adds a `setup-test` row to the tracker and removes it (the one row the agent is ever allowed to delete), and asks you to create the two Gmail labels. When it ends with "setup complete", run `/job-scout` for the first time; chapter 8 explains what happens next.

**Updating the kit later:** `git pull` in the repo folder and re-run `bash kit/install.sh`. Your `profile/`, `tracker/`, `applications/`, `CLAUDE.md` and `settings.json` are never overwritten; if the kit's own `CLAUDE.md` or `settings.json` changed, the installer says so and you merge the difference with `diff`.
