# 3. Install the job-agent kit into Claude Code

The kit is a folder of plain text files. Nothing is compiled; you can open every file and change the rules.

**1. Get the kit.** Clone the repo (or unzip the archive you were sent) somewhere you keep code:

```
git clone https://github.com/jawwada/ai-engineer-job-playbook.git
cd ai-engineer-job-playbook
```

It contains `docs/` (this guide as markdown), `kit/` (what gets installed) and `knowledge/` (the interview and landscape material).

**2. Run the installer.** `bash kit/install.sh` does five things, all of them visible in the script: copies `kit/skills/*` to `~/.claude/skills/`, copies `kit/agents/*` to `~/.claude/agents/`, creates `~/job-search/` with the layout from the previous section, copies `CLAUDE.md`, `.claude/settings.json` and the `profile/*.example.yaml` templates into it, and installs the two helper scripts (`tracker.py`, `tailor_resume.py`). Running it twice is safe; it never overwrites a `profile.yaml` or tracker that already has your data.

**3. Start Claude Code in the workspace, with the browser attached.**

```
cd ~/job-search
claude --chrome
```

The first time, accept the workspace-trust dialog and the one-time Chrome introduction. Then check four things inside the session:

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

It also asks before `git push`, and it denies the Gmail connector's send, reply and forward tools, so "drafts only" is enforced by the harness rather than by a prompt. Rule syntax to remember: `Bash(git *)` matches every git command (the space before `*` matters), `Read(~/path/**)` is a path rule, `WebFetch(domain:x)` is per domain, and `mcp__claude-in-chrome__*` would pre-approve every browser action. The browser tools are deliberately *not* on the allow list for the first week: when Chrome asks "Claude in Chrome wants to…", choose the option that allows all actions on that site for the session. After a week of clean reviews you can add `"mcp__claude-in-chrome__*"` to the allow list; site-level permissions are still enforced by the extension itself.

The modes, in case you change `defaultMode`: `default` prompts on first use of each tool; `acceptEdits` auto-accepts file edits in the workspace (recommended here); `plan` is read-only; `auto` lets a background classifier approve routine actions; `dontAsk` denies anything that would prompt; `bypassPermissions` skips all prompts and is not appropriate for a tool that submits job applications under your name.

**5. First run.** Type `/job-setup`. The skill reads your master resume, interviews you for the facts it cannot infer (work authorization, rate floors, remote rules, start date), writes `profile/profile.yaml` and `profile/answers.yaml`, checks the resume renders to two pages, adds a test row to the tracker and removes it. When it ends with "setup complete", run `/job-scout` for the first time; the daily loop section explains what happens next.

**Updating the kit later:** `git pull` in the repo folder and re-run `bash kit/install.sh`. Your `profile/`, `tracker/` and `applications/` folders are never touched by the installer.
