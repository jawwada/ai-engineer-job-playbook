# 11. Monitoring and staying connected

The agent runs on your computer, in a terminal, with Chrome open. "Staying connected" means three things: you can see and steer that session from your phone, it runs on a schedule without you typing, and it tells you when it needs you.

**Remote Control: the session on your phone.** Start the session with Remote Control on:

```
cd ~/job-search
claude --remote-control "Job search"
```

(`--rc` is the short form; inside a running session `/remote-control` or `/rc` does the same and keeps the conversation.) The first time, Claude Code asks *Enable Remote Control? (y/n)* once. It then prints a session URL and a QR code: open claude.ai/code in any browser or the Claude mobile app (tap **Code**) and the session is there, live, with everything the terminal shows. From the phone you can type the same commands — *"run /job-scout"*, *"queue 2 and 5"*, *"submit"* when a review screen is waiting — and the work happens on your computer, in your Chrome. Requirements: a Pro, Max, Team or Enterprise plan signed in with `/login` (API keys do not work), and the `claude` process must keep running: close the terminal and the session goes offline. If the laptop sleeps or the network drops, Claude Code reconnects by itself when it is back. To have every session connect automatically, run `/config` and switch on **Enable Remote Control for all sessions** (or set `"remoteControlAtStartup": true` in `~/.claude/settings.json`). On a machine you reach over SSH, start it inside `tmux` so it survives the disconnect.

**Scheduled runs: the loop without typing.** Inside the session, `/loop` repeats a prompt on an interval: `/loop 2h /job-scout` scouts every two hours, `/loop 30m check for a waiting review screen and tell me` keeps the review queue moving. A loop lives inside the session (it stops when the session ends and expires after seven days; the shortest interval is one minute), which is exactly right here because the browser and your files are local to that session. Claude Code's cloud routines (`/schedule`) run on Anthropic's servers without your files or your Chrome, so they are not suitable for applying; they are fine for a morning digest of alert mail through the Gmail connector. The Claude Desktop app can also run scheduled tasks on your machine with local files and connectors, if you prefer an app over a terminal. Whatever you schedule, the daily cap and the review-mode rules still apply.

**Notifications when it needs you.** Claude Code fires a *Notification* hook whenever it is waiting for permission or input. Add this to `~/job-search/.claude/settings.json` to get a desktop notification (macOS; on Linux use `notify-send`, on Windows a PowerShell toast):

```json
"hooks": {
  "Notification": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "osascript -e 'display notification \"The job agent is waiting for you\" with title \"Claude Code\"'"
        }
      ]
    }
  ]
}
```

With Remote Control on, the same moments show up in the Claude app as the session waiting on you, which is the practical "push notification" for a review screen while you are away from the desk.

**Keep the machine awake and the browser alive.** On a Mac run `caffeinate -dims` in a second terminal (or set the display to never sleep while plugged in); on Windows set the power plan so the PC never sleeps when plugged in. Chrome must stay open with LinkedIn, Dice and Indeed logged in; the extension's background worker can go idle after long inactivity, in which case browser calls fail with *Receiving end does not exist* and `/chrome` → **Reconnect extension** fixes it. A laptop lid closed without an external display suspends everything, Remote Control included.

**Resuming after a restart.** `claude --continue` resumes the last conversation in the folder; add `--rc` to put it back on your phone. The tracker is a file, so nothing is lost between sessions: the first `/job-scout` after a break simply skips what is already recorded.

**What to look at each day** (two minutes): the tracker summary (`/job-tracker`), the list of `needs-check` rows, drafts waiting in Gmail, and the Chrome window's tab group — if a tab is sitting on a form, something stopped and the terminal or the app will say why.
