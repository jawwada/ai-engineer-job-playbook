# 10: Terminal-agent task (Harbor format)

## What this dataset is for

An escape room for agents: a sealed container with something broken inside, a written brief, and a hidden checklist that runs after the agent declares it is done. The agent may type any command; only the final state counts. The same folder serves as a benchmark item (many agents, compare pass rates) and as an RL environment (one agent, many attempts, reward the successes). The question it answers is: *can the agent repair a realistic system to a verifiable end state, without being shown the checks?*

## The example

`fix-log-permissions/` follows the Harbor task layout (the format of Terminal-Bench 2.0): `instruction.md`, `task.toml`, `environment/` (a Dockerfile and the job script), `solution/solve.sh`, and `tests/` (`test.sh` and `test_outputs.py`). The instruction, in full:

```markdown
# Fix the log permissions for the nightly job

The nightly job `/opt/app/write_log.sh` runs as the system user `appsvc`. It appends a line to `/var/log/app/app.log` and, once that file passes 1 MB, rotates it to `/var/log/app/app.log.1`. Right now it fails with `Permission denied`.

Make the job work when it runs as `appsvc`:

- `appsvc` must be able to append to `/var/log/app/app.log` and to create and rename files in `/var/log/app`.
- Do not modify `/opt/app/write_log.sh`, and do not run the job as root.
- Nothing under `/var/log/app` may be writable by other users (no world-writable files or directories).
- The user `auditor` must still be able to read `/var/log/app/app.log` but must not be able to write to it.
```

`task.toml`, trimmed, and the three-line reference solution:

```toml
schema_version = "1.3"
[task]
name = "playbook-examples/fix-log-permissions"
description = "Fix ownership and modes so a service account's nightly job can write and rotate its log without world-writable paths."
[metadata]
difficulty = "easy"
estimated_expert_minutes = 10
[verifier]
timeout_sec = 120.0
user = "root"
[agent]
timeout_sec = 900.0
user = "root"
[environment]
cpus = 1
memory_mb = 1024
```

```bash
chown -R appsvc:appsvc /var/log/app
chmod 755 /var/log/app
chmod 644 /var/log/app/app.log
```

| Part | What it is and why it exists |
|---|---|
| `instruction.md` | the whole specification the agent gets; every test must trace back to a sentence in it |
| `schema_version`, `[task]` | format 1.3; name as org/name, authors, description, keywords |
| `[metadata]` | the author's own fields: difficulty, category, `estimated_expert_minutes`, failure mode |
| `[agent]`, `[verifier]` | timeouts (900 and 120 seconds) and users for each phase |
| `[environment]` | build timeout, CPUs, memory, storage: reproducible resources |
| `environment/` | the broken starting state (`python:3.12-slim`, `pytest==8.3.3`, a root-owned log directory with mode 755 and a 644 log) |
| `solution/solve.sh` | proof that the task is solvable: the oracle |
| `tests/` | the hidden checks, and the script that writes 1 or 0 to `/logs/verifier/reward.txt` |

## How the model uses it

The harness builds the image from `environment/`, starts a container and gives the agent the instruction; the agent works through a shell, here as root for at most 900 seconds. When it stops, the harness uploads `tests/` into the container and runs `test.sh`, which runs `pytest` on `test_outputs.py` and writes `1` or `0` to `/logs/verifier/reward.txt`. Tests arrive only after the agent finishes, so it can neither read nor edit them; that is also why no `COPY` line in the Dockerfile may mention `tests` or `solution`.

The five tests check outcomes, not commands: the job script is unchanged (SHA-256 `4ade4abc…`); it runs as `appsvc` and appends; it rotates a log grown past 1 MB; nothing under `/var/log/app` is world-writable; `auditor` can read but not write. Any fix producing that state passes (group-writable 775 and 664 modes for the `appsvc` group pass too), while shortcuts fail: `chmod 777` breaks the world-writable test, editing the script breaks the checksum, and running the job as root never helps because the tests run it as `appsvc`. The helper `run_as(user, *cmd)` executes each check as the named user with only that user's own group (`extra_groups=[]`).

Two sanity runs are mandatory: the oracle must score 1 and doing nothing must score 0 (the untouched container fails the append and rotation tests). **As a benchmark** the metric is the pass rate over repeated trials, averaged over tasks. **As an RL environment** the reward file is the episode reward and a task's repeated rollouts form the GRPO group of `05-rlvr/`. Running it for real needs a Harbor-compatible harness with Docker; the lab's validator checks the task statically.

## How it is produced and checked

Authors with operations experience write tasks from real problems: a realistic, unambiguous goal, a verifiable end state, pinned dependencies, no internet unless declared. They write environment, solution and tests; run the oracle repeatedly (to catch flaky tests) and a no-op; have a second engineer attack the tests with shortcuts and alternative solutions; and run several agents several times to measure difficulty.

`validate_all.py` check **10 terminal-agent task (Harbor format)** asserts: all six files exist; `task.toml` parses (with `tomllib`, so Python 3.11 or newer; older interpreters report SKIP) with a `schema_version`, a task name and positive agent and verifier timeouts; no `COPY` or `ADD` line in the Dockerfile mentions `solution` or `tests`; `test.sh` writes `/logs/verifier/reward.txt`; `test_outputs.py` compiles. It prints `all six files present; task.toml parses; tests and solution stay out of the image`. The criteria that matter most need Docker: oracle = 1 on every run, no-op = 0, and tests that accept every valid solution and reject the shortcuts.

## What goes wrong

- **Tests or solution in the image**: the agent copies the answer.
- **Tests stricter or looser than the instruction.** `run_as` passes `extra_groups=[]`, which keeps root's supplementary groups out of the check but fails a valid fix that grants access through a new supplementary group; either choice is defensible, so state it in the instruction or test it (exercise 6 in chapter 26d.21).
- **A verifier sharing the agent's container**: the agent cannot touch the tests but can change what they rely on (the interpreter, `pytest`, `/bin/sh`); and **flaky tests** from network installs, timing or test order.

## Related

Chapter 26d.11 (Harbor's `reward.json`, Terminal-Bench 2.0's 89 tasks, oracle and no-op rules). Siblings: `11-swe-task/` (a repository instead of a system), `12-agentic-gym/` (a simulated business instead of a container), `05-rlvr/` (how a 0/1 reward becomes a policy update).
