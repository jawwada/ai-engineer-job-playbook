# 13. Troubleshooting

Everything below happened during the run this guide was written from (about 250 applications over a week). The fixes are built into the kit; the table is so you recognize the symptom.

| Symptom | Cause | Fix |
| --- | --- | --- |
| The kit's commands do not appear under `/` | `~/.claude/skills` was created after the session started | `/reload-skills`; for subagents in a new `~/.claude/agents` folder, restart `claude` once |
| `/chrome` says *Extension: Not detected* | Extension not installed/enabled, or Chrome has not read the new native-messaging host file | Check `chrome://extensions`, restart Chrome, then `/chrome` → **Reconnect extension**; restart both if needed |
| Browser tools return *Receiving end does not exist* or stop responding after a quiet hour | The extension's service worker went idle | `/chrome` → **Reconnect extension** |
| *No tab available* | The agent acted before a tab existed | Ask it to open a new tab and retry |
| Clicks and uploads fail while you work in another window | The agent's tab is in the background and Chrome throttles it | Keep the Chrome window visible; the skill's page scripts are written to work in hidden tabs (synchronous, no timers), but uploads still need a visible tab |
| The Easy Apply resume upload "succeeds" but the old resume is still attached | LinkedIn's file input is hidden; a click on *Upload resume* opens the OS dialog the agent cannot use | The skill exposes the hidden `input[type=file]` and uploads through it, then verifies the file name on the review step |
| The job panel does not change when the agent "opens" the next card | LinkedIn's single-page app ignored the synthetic click | The skill clicks the card's coordinates instead and checks the title changed |
| The injected page helper disappears | The page reloaded (LinkedIn does this after a submit) | The skill re-injects its helper before every job; if you drive by hand, say "re-inject the helper" |
| A page script's output is blocked as *cookie / query string* content | Returned text contained `key=value&other=value` patterns | The skill returns structured JSON without URL-like strings; avoid asking it to print raw query strings |
| *Follow company* gets ticked, or a profile prompt appears after submit | LinkedIn defaults | Untick on the review step; choose *Not now* on the profile prompt (both are in the playbook) |
| LinkedIn says you have reached the application limit for today | Daily Easy Apply throttle | The tracker marks remaining packages `ready`; they go first tomorrow. Lower the cap |
| The application looked submitted but is not in *My jobs → Applied* | A modal step did not advance (a required field was empty, or a consent box was unticked) | Verify against the platform's own list before marking `submitted`; the skill does this for LinkedIn and Dice |
| Workday asks to create an account | By design | You create the account and verify the email; then the agent continues |
| A CAPTCHA or a login page appears | By design | You solve it; the agent waits and resumes |
| The tailored resume runs to three pages | The headline or a profile bullet grew too long, or the PDF converter changed fonts | The script checks the page count; keep the headline under \~85 characters and bullets to two lines; install the fonts the master resume uses so LibreOffice renders them |
| The .docx edit did not take (old text still there) | Word splits a sentence into several XML runs, so a plain text replace misses | `tailor_resume.py` merges runs before replacing; if you edit the master in Word, re-run `/job-setup` to re-index it |
| LibreOffice conversion fails or hangs | A stale `soffice` process or missing fonts | `pkill soffice`, retry; check `soffice --version`; on macOS the binary is inside `LibreOffice.app/Contents/MacOS` |
| Screening form has a question the agent cannot answer | Not in the bank | It asks you (review mode) or skips and records `needs-answer` (auto mode); add the answer to `answers.yaml` |
| Duplicate postings keep appearing | Several agencies repost the same client role | The screener keeps the earliest; add the agency to `exclude_companies` if it is persistent |
| The session gets slow and the context fills up | Long job descriptions and page dumps accumulate | Run `/compact` between batches; the skills capture JDs to files instead of keeping them in the conversation |
| Remote Control shows the session offline | The `claude` process stopped, the laptop slept with the lid closed, or the network was down for more than ten minutes in server mode | Reopen the terminal and run `claude --continue --rc`; keep the machine awake as described above |
| Gmail tools are missing from `/mcp` | Connector not connected on claude.ai, or logged in with an API key | Connect Gmail in claude.ai Settings → Connectors, then `/login` with your claude.ai account |

If a problem is not in this table, ask the agent to explain what it saw ("take a screenshot and tell me what is on the page") before retrying; almost every stuck state is visible in the Chrome window.
