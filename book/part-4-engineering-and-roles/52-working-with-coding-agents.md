# 52. Working with coding agents: writing better code, reviewing agent-written complexity, and how to argue for simplicity

> **What you need to be able to say:** how to get good code out of Claude Code and its peers (specification, tests, small steps, memory files, review); how to recognize and push back on the over-engineered patterns agents tend to produce; and how to make the case for simplicity with evidence rather than opinion. In 2026 "can you work with coding agents" is an interview topic in itself.

## 52.1 What changes when an agent writes the code

The bottleneck moves from typing to *specifying, verifying and reviewing*. Agents produce plausible code fast, including abstractions you did not ask for, dependencies you do not need, and tests that test the mock. The engineer's job becomes: write precise intent, give the agent the tools to verify (tests, linters, type checks, a runnable environment), keep the steps small, read the diff like a reviewer, and keep the project's conventions in a memory file the agent reads every time.

## 52.2 Getting better code: the workflow

1. **Specify like a ticket, not a wish.** Inputs, outputs, constraints, non-goals, examples, the definition of done ("`pytest -q` passes, `ruff` clean, no new dependencies, p95 under 200 ms on the fixture").
2. **Explore before editing.** Ask the agent to read the relevant files and summarize the current design; correct its understanding before it writes.
3. **Plan, then implement in slices.** A short plan you approve; one slice per commit; run tests after each; stop when a slice fails rather than letting it "fix" by stubbing.
4. **Tests first when behaviour matters.** Have the agent write failing tests from the spec, confirm they fail for the right reason, then implement. Tests are the reward signal; without them the agent optimizes for "looks done".
5. **Memory file (CLAUDE.md / AGENTS.md).** Conventions, commands, architecture notes, forbidden patterns ("no new abstractions without a second use", "no network in unit tests", "Pydantic at boundaries", "prefer stdlib"), and the review checklist. Update it when you correct the agent twice for the same thing.
6. **Review the diff as a reviewer, not a reader.** Look for: new dependencies, new abstractions, duplicated logic, swallowed exceptions, mocked-away behaviour in tests, hidden I/O, changed public interfaces, and TODOs.
7. **Use sub-agents for independent work and a reviewer agent for the diff**, but you own the merge.
8. **Keep the loop honest.** If the agent repeatedly cannot make a test pass, the spec or the design is wrong — step back, do not let it widen the blast radius.

**The mechanics that make this workflow hold up.**
- **Instructions are context, not enforcement.** Claude Code's documentation is explicit that `CLAUDE.md` is read as context and followed on a best-effort basis; anything that must always or never happen belongs in a permission rule or a hook (chapter 52a). "Never edit the migrations folder" in a memory file is a request; a deny rule on `Edit(./migrations/**)` is enforced by the harness for its file tools and the shell file commands it recognizes, and the OS-level sandbox's filesystem restrictions close the remaining gap (a script that opens and writes the file itself is not covered by the rule alone).
- **Keep the memory file small and scoped.** The guidance is under about 200 lines per file; move rules that apply to one part of the codebase into path-scoped rules (`.claude/rules/` with a `paths` glob) and multi-step procedures into skills, so the context each session pays for stays small.
- **Protect the tests from the implementer.** Agents under pressure to make tests pass sometimes edit the assertion, skip the test, or special-case the test input, and lab system cards have documented this kind of test-gaming. During implementation, deny edits to the test directory (or have a hook flag any diff that touches tests), review test changes separately, and add a few property-based or mutation tests that a special case cannot satisfy.
- **One task per context.** Clear or compact between unrelated tasks; long sessions accumulate stale assumptions and cost more per turn. Use plan mode to agree the approach before edits on anything larger than a small fix.
- **Parallel work in isolated worktrees.** Run independent tasks as separate agents in separate git worktrees (Claude Code sub-agents can be given `isolation: worktree`), so they cannot overwrite each other, and merge through normal pull requests.
- **Review size is a quality control.** Classic code-review research (the Cisco and SmartBear study) found defect discovery drops off beyond roughly 200–400 lines per review session; ask for slices a human can actually review rather than one large agent-written diff.

## 52.3 Patterns agents over-produce (and the simpler alternative)

| Agent tends to write | Why it is a problem | Ask for instead |
|---|---|---|
| A class hierarchy or "manager/factory/strategy" for one use | speculative generality; harder to read and test | a function; add structure at the second use |
| A generic plugin/registry system | indirection; discoverability drops | explicit imports and a dict of handlers |
| Retry/backoff/circuit-breaker helpers rewritten by hand | subtle bugs; duplicates `tenacity` | the library, configured in one place |
| Deep configuration objects and feature flags everywhere | combinatorial behaviour | constants and one settings model |
| Broad `try/except Exception: pass` | hides failures | narrow exceptions; let the caller decide |
| Tests that mock the unit under test or assert on implementation details | green tests, broken code | behaviour tests on inputs/outputs; fixtures with recorded data |
| New dependency for a one-liner | supply-chain and maintenance cost | stdlib or the existing dependency |
| Async everywhere, including CPU-bound code | complexity without benefit | async only at I/O boundaries |
| A custom "agent framework" inside the app | reinventing LangGraph/SDK badly | the chosen framework or a 60-line loop |
| Comments narrating the obvious; docstrings that restate the signature | noise | comments on *why*; docstrings that state contracts and edge cases |
| Giant functions with nested control flow for "flexibility" | untestable | small pure functions and a thin orchestration layer |

**Four agent habits that are worse than over-engineering.** These do not look complex in the diff, which is why reviewers miss them.

| Agent tends to write | Why it is a problem | Control |
|---|---|---|
| A change to the test instead of the code (assertion loosened, test skipped, input special-cased) | the reward signal is corrupted, so every later "green" means nothing | tests read-only during implementation; separate review of test diffs; mutation or property-based tests |
| An import of a package that does not exist or is a near-namesake | attackers register commonly hallucinated names ("slopsquatting"); one study of 576,000 generated code samples found at least 5.2% of package references hallucinated for commercial models and 21.7% for open models, with over 205,000 unique invented names | verify every new dependency exists, is the intended project and is maintained; lockfiles and an internal mirror or allow-list |
| Silent fallbacks (`except: return default`, `or {}`, optional chaining everywhere) | errors become plausible wrong answers that pass tests | fail loudly at boundaries; a lint rule or review check for broad excepts and default-on-error |
| Drive-by edits (renames, reformatting, refactors outside the task) | the diff hides the real change and breaks other people's branches | scope the task in the prompt, reject unrelated hunks, run the formatter in a hook so formatting never appears as a change |

## 52.4 How to argue when the agent (or a colleague) proposes a complex pattern

Argue with evidence, not taste, and make the agent do the work of proving necessity:

- **Ask for the second use.** "Show me the two call sites that need this abstraction." If there is one, it is premature.
- **Ask for the failure it prevents.** "Which test fails without the circuit breaker?" Write that test; if it cannot be written, the component is speculative.
- **Count the cost.** Lines added, dependencies added, concepts a new reader must learn, test complexity. Put the numbers next to the benefit.
- **Propose the smallest version that passes the same tests.** Have the agent implement both; compare diffs and runtime; keep the smaller one unless a measurement says otherwise.
- **Invoke the memory file.** "Our convention is no new abstractions without a second use (CLAUDE.md §3). Rewrite accordingly." Agents follow written rules reliably; they follow vibes poorly.
- **Separate design from implementation.** If the complexity is a design question (new service, new queue, new store), move it to an ADR with options, costs and the decision; do not let it arrive as a 1,200-line PR.
- **Reserve the right to be convinced.** Some complexity is earned: idempotency, retries, schema validation, permission checks. The test is whether a specific failure, measurement or requirement justifies it.

A script for the review comment: *"This adds X (lines/deps/concepts) to prevent Y. I don't see Y in our requirements or tests. Either add a failing test that demonstrates Y, or simplify to Z. If Y is a real risk, let's record it in an ADR and size it properly."*

**Let tools carry part of the argument.** Evidence beats taste, and some of it can be automated. Put numbers in CI: added lines, new dependencies, cyclomatic complexity and the count of new public symbols per PR, with a threshold that triggers a design discussion rather than a block. Use the harness's own reviewers as a second opinion before a human reads the diff: Claude Code ships a bundled `/simplify` skill that runs four review agents in parallel (reuse of existing helpers, simplification, efficiency, and whether the change sits at the right level of abstraction) and applies the fixes, and a separate `/code-review` for correctness bugs, since `/simplify` does not look for them. Ask the agent to argue the opposite case ("list three reasons this abstraction is premature, then decide") before it writes code — the critic pattern of chapter 53 applied to design. None of this replaces the human decision; it moves the conversation from "I don't like it" to "this adds 340 lines, two dependencies and a registry for one call site".

## 52.5 Code quality that interviewers probe

Readable names; small functions; types at boundaries; errors that carry context; logging at boundaries with trace ids; no global state; configuration separate from code; tests that run in seconds; a README that runs the project in ten minutes; a CI that enforces all of it. For AI code specifically: prompts as versioned files with tests, tool schemas as the contract, model clients behind an interface, evals as part of the test suite, and no secrets in the repo.

## 52.6 Using agents without losing your edge

Read the code the agent writes; refactor by hand occasionally; keep solving small problems yourself; use the agent to explain unfamiliar code and to generate alternatives you then judge. Interviewers can tell within minutes whether a candidate understands the code in their own repos.

**What the evidence says about speed, and why you should measure your own.** METR's randomized trial (July 2025) gave 16 experienced open-source developers 246 real issues in repositories they knew well; with early-2025 tools (mostly Cursor with Claude 3.5 and 3.7 Sonnet) they took 19% longer, while believing afterwards that the tools had made them about 20% faster. METR's February 2026 follow-up with late-2025 tools (57 developers, over 800 tasks) could not settle the question: developers increasingly refused to work without AI, and many withheld the tasks they expected AI to speed up most, so METR called the new data only very weak evidence. The 2025 DORA report (chapter 45) adds that AI adoption now goes with higher throughput and with higher delivery instability. The lessons for an interview: perceived speed is not measured speed; the gain depends on the task, the codebase and the reviewer; and the team that measures cycle time, change failure rate and review load before and after adopting an agent can answer "did it help?" with data instead of anecdotes.

**Interview line:** *"I treat a coding agent like a fast junior pair: precise specs, tests as the reward, small reviewed slices, a memory file with our conventions, and a review that asks every abstraction to justify itself with a second use or a failing test."*
