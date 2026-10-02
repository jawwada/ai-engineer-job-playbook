# 4. Connect Gmail

Gmail does two jobs in this system: job-alert emails come *in* (LinkedIn, Indeed and Dice alerts are the cheapest, most reliable feed of fresh postings), and recruiter conversations go *out* as drafts you approve. The connection is the claude.ai Gmail connector, which Claude Code inherits automatically when you are logged in with your claude.ai account — there is nothing to install on the machine and the agent never sees your Google password.

**Connect it (once, in the browser):**

1. Open claude.ai → Settings → Connectors, find Gmail and click Connect. Google shows its consent screen; you approve it yourself. The agent is not involved in this step and must not be asked to do it.
2. Back in Claude Code, type `/mcp`. Gmail should be listed with its tools (search threads, read messages, create drafts, reply, labels). If it shows as needing authentication, select it in the `/mcp` panel to sign in.
3. Test it with one sentence: *"Search my Gmail for messages from the last 7 days with 'recruiter' or 'opportunity' in them and list sender, subject and date."* You should get a list, not an error.

**Prepare the inbox so the agent reads only what it should.** Create two labels in Gmail, `Jobs/Alerts` and `Jobs/Recruiters`, and two filters: alert mail (from `jobalerts-noreply@linkedin.com`, `noreply@indeed.com`, `dice.com`) gets `Jobs/Alerts` and skips the inbox; mail that mentions roles, rates or interviews gets `Jobs/Recruiters`. The kit's `CLAUDE.md` tells the agent to search only those labels (`label:Jobs/Alerts newer_than:1d`) and never to open anything else. If you would rather not point an agent at your personal mailbox at all, create a fresh Gmail address for the job search and use it everywhere; many people find this cleaner anyway.

**Set up the alerts that feed it.** On LinkedIn, run each search you care about (for example *Forward Deployed Engineer*, remote, United States, past 24 hours) and switch on the job alert, daily. Do the same on Indeed and on Dice (Dice alerts can be filtered to contract/C2C). Three to five alerts per site is plenty; the agent de-duplicates across them.

**What the agent does with mail — and what it never does.** The `/recruiter-inbox` skill reads new threads under `Jobs/Recruiters`, classifies each (real role with details, vague mass mail, interview logistics, rejection), extracts the facts you need (role, rate or salary, location, W2/C2C, client name) into the tracker, and writes a reply as a **Gmail draft** in your voice using the answers bank. It also pulls new alert mail into the day's scouting list. Sending is a separate, explicit step: the standing rule is *draft everything, send nothing* until you say "send the draft to X". Keep that rule even in auto mode; a wrong application costs little, a wrong email to a recruiter costs a relationship.

**If you cannot or do not want to connect Gmail:** the Chrome integration can read the Gmail web app directly ("open Gmail, show me unread mail labeled Jobs/Recruiters"), which is slower but works, or you can forward recruiter mail to a text file in `inbox/` and point the skill at it.
