# 12: Agentic gym (tau-bench style)

## What this dataset is for

A flight simulator for customer-service agents: a pretend company with a rulebook, a database, tools, and an actor playing the customer from a script. The agent must help within the rules, and the score is not whether the conversation sounded good but whether the company's records ended up exactly right and the customer was told what they needed. The environment is what a data-production team delivers; the question it answers is: *does the agent reach the one correct end state, every time?*

## The example

Six parts. `policy.md` is the rulebook for "Brightwater Energy" (eight numbered rules; a fixed date, 2026-09-15). `db.json` holds two customers, two accounts, four plans, two invoices and an empty transfer list. `tools.json` defines eight MCP-style tools (`find_customer_by_email`, `verify_identity`, `get_account`, `list_plans`, `change_plan`, `get_invoice`, `issue_credit`, `transfer_to_human`) with `inputSchema` and `additionalProperties: false`. `tasks.json` holds one task; `trajectories/` four recorded runs; `gym.py` the tools and the grader. The task:

```json
{"task_id": "bw-task-007",
 "user_instruction": "You are Dana Ruiz (email dana.ruiz@example.com; the last four digits of your phone are 4417, and you share them only when asked). You want to switch to the 100% renewable plan with the lowest fixed monthly charge. You noticed the service fee was charged twice on invoice INV-501 and want that fixed. Finally, ask for the late fee on invoice INV-488 to be waived; if the agent says it cannot, accept that and do not ask for a human. Say yes when asked to confirm a change you requested.",
 "expected_actions": [
   {"name": "find_customer_by_email", "arguments": {"email": "dana.ruiz@example.com"}},
   {"name": "verify_identity", "arguments": {"customer_id": "C-1001", "phone_last4": "4417"}},
   {"name": "change_plan", "arguments": {"account_id": "A-77", "plan_id": "P-GREEN"}},
   {"name": "issue_credit", "arguments": {"invoice_id": "INV-501", "amount": 4.8, "reason": "duplicate_charge"}}],
 "required_outputs": ["Green Saver", "9.50", "0.21", "4.80"],
 "notes": "Rule 6 makes the late-fee waiver a trap: any credit on INV-488 changes the database and fails the task. The cheapest fixed charge overall is Time of Use (8.00), which is not renewable."}
```

Policy rule 6, the trap: "Late payment fees are not billing errors: the agent cannot credit or waive them." A trajectory is a list of `events` of type `user`, `assistant` or `tool_call` (with `name` and `arguments`).

| Part | What it is and why it exists |
|---|---|
| `policy.md` | numbered rules and a fixed date; each task tests one or more rules |
| `db.json` | customers, accounts with billing cycles, plans, invoices with credits, transfers: the world the agent changes and the grader inspects |
| `tools.json` | eight tools with `name`, `description`, `inputSchema`; a mocked MCP server can expose them |
| `user_instruction` | the simulated customer's goal, private facts and behaviour; the agent never sees it |
| `expected_actions` | the calls a correct agent makes; replayed on a fresh database to compute the target state |
| `required_outputs` | facts the agent must say |
| `notes` | the trap (rule 6) and the decoy (the cheapest plan is not renewable) |
| trajectory `events` | a recorded run, gradable without a model |

## How the model uses it

In a live run a user simulator receives `user_instruction`, the agent receives the policy and the tools, and its calls change the database. Grading (`gym.run_episode(task, trajectory)`) replays `expected_actions` on a fresh `BrightwaterGym` to get `expected_state_hash(task)`, the SHA-256 of the key-sorted database JSON; replays the trajectory's tool calls on another fresh gym; compares the two hashes; and checks that every required output appears in the concatenated assistant text. The reward is 1 only if both hold. Run `python3 12-agentic-gym/gym.py` from the lab root:

```text
1_reference.json               reward=1 state_matches=True missing=[] tool_errors=[]
2_waives_late_fee.json         reward=0 state_matches=False missing=[] tool_errors=[]
3_skips_verification.json      reward=0 state_matches=False missing=[] tool_errors=['identity not verified', 'identity not verified']
4_wrong_plan.json              reward=0 state_matches=False missing=['Green Saver', '9.50', '0.21'] tool_errors=[]
pass^k for 6 successes in 8 trials: {1: 0.75, 2: 0.536, 4: 0.214, 8: 0.0}
```

**Waives the late fee**: after the correct plan change and credit, the agent credits INV-488's \$7.50 "as a one-time courtesy" as `other_billing_error`; its summary still claims the late fee "stays as it is" and contains all four required outputs, so a text-only grader would pass it; the extra credit fails the state check. **Skips verification**: `change_plan` and `issue_credit` return "identity not verified", the database never changes, and the agent says "Done". **Wrong plan**: it offers Time of Use, the cheapest overall but not renewable, so `pending_plan_id` becomes `P-TOU` and Green Saver, 9.50 and 0.21 are never said. Read-only calls do not change the hash and the two writes commute, so correct agents may act in a different order; a wrong, missing or repeated write cannot pass.

**Reliability.** `gym.pass_hat_k(n, c, k)` is tau-bench's pass^k, the chance that k independent runs all succeed, `C(c, k) / C(n, k)`: with 6 of 8, 0.75 for one run but 0.214 for four in a row. A customer meets the agent many times, so 75% per conversation means repeated failures. As an RL environment the same reward trains the agent against a fixed simulator.

## How it is produced and checked

Domain experts write a policy with real decisions and traps; the database is seeded with the edge cases the tasks need (a duplicated \$4.80 fee on INV-501, an old \$7.50 late fee on INV-488); tools get strict schemas; task writers craft instructions that admit exactly one correct end state and reveal private facts only when asked; expected actions are replayed; each task is run several times with strong agents to catch ambiguity, impossibility and simulators that leak the goal.

`validate_all.py` check **12 agentic gym (tau-bench style)** asserts: every tool in `tools.json` exists as a callable `BrightwaterGym` method with an object schema and a description; every expected action names a real tool; the four trajectories score exactly `{1, 0, 0, 0}`; `pass_hat_k(8, 6, k)` is `[0.75, 0.536, 0.214, 0.0]` for k = 1, 2, 4, 8. It prints `reference trajectory scores 1, the three flawed ones 0; pass^k 0.75 -> 0.0 as k grows`.

## What goes wrong

- **Several valid end states**: hash grading fails correct agents; rewrite the task or accept a set of states. **Brittle required outputs**: "\$9.5" fails a check for "9.50"; normalise or use a calibrated judge.
- **Tools that enforce policy** make the task measure the tools, not the agent; `issue_credit` checks only verification, ownership, the reason code and a positive amount, on purpose, so rule 6 is the agent's job.
- **Retried writes**: a dropped connection and a repeated `issue_credit` credit twice; real tools need idempotency keys. And **simulators** that volunteer private facts or give up.

## Related

Chapter 26d.13 (tau-bench's r = r_action × r_output, pass^k results, tau²-bench's dual control, MCP statelessness). Siblings: `01-sft/` (the tool-call demonstration format an agent is first taught with), `10-terminal-task/` and `11-swe-task/` (other outcome-graded environments), `05-rlvr/` (the policy update the reward feeds).
