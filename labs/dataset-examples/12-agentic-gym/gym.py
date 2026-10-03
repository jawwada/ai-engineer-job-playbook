"""A tau-bench-style agentic gym: policy, database, tools, a task, and outcome-based grading.

The environment is what a data-production team delivers: the model under test talks to a simulated
user and calls these tools; when the conversation ends, the grader compares the final database
with the state produced by replaying the task's expected actions, and checks that the agent told
the user the required facts. Reward is 1 only if both match.

Tools are plain Python here; tools.json holds the same tools as MCP-style definitions (name,
description, inputSchema) so a mocked MCP server can expose them. Standard library only.

Usage:  python3 gym.py      (runs the reference trajectory and three flawed ones, then pass^k)
"""
import copy
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REASONS = {"duplicate_charge", "meter_error", "other_billing_error"}


class BrightwaterGym:
    def __init__(self):
        with open(os.path.join(HERE, "db.json"), encoding="utf8") as fh:
            self.db = json.load(fh)
        self.verified_customer = None          # session state: set by verify_identity
        self.log = []                          # every tool call with its result

    # ----------------------------------------------------------------- helpers
    def _account_of_verified(self, account_id):
        account = self.db["accounts"].get(account_id)
        if self.verified_customer is None:
            return None, "identity not verified"
        if account is None or account["customer_id"] != self.verified_customer:
            return None, "account not found for the verified customer"
        return account, None

    def _invoice_of_verified(self, invoice_id):
        invoice = self.db["invoices"].get(invoice_id)
        if invoice is None:
            return None, "invoice not found"
        _, error = self._account_of_verified(invoice["account_id"])
        return (None, error) if error else (invoice, None)

    # ----------------------------------------------------------------- tools
    def find_customer_by_email(self, email):
        for cid, customer in self.db["customers"].items():
            if customer["email"] == email.strip().lower():
                return {"customer_id": cid}
        return {"error": "no customer with that email"}

    def verify_identity(self, customer_id, phone_last4):
        customer = self.db["customers"].get(customer_id)
        if customer and customer["phone_last4"] == phone_last4:
            self.verified_customer = customer_id
            return {"verified": True}
        return {"verified": False}

    def get_account(self, account_id):
        account, error = self._account_of_verified(account_id)
        return {"error": error} if error else dict(account, account_id=account_id)

    def list_plans(self):
        return {"plans": [dict(p, plan_id=pid) for pid, p in self.db["plans"].items()]}

    def change_plan(self, account_id, plan_id):
        account, error = self._account_of_verified(account_id)
        if error:
            return {"error": error}
        if plan_id not in self.db["plans"]:
            return {"error": "unknown plan"}
        if account["plan_changed_this_cycle"]:
            return {"error": "plan already changed this billing cycle"}
        account["pending_plan_id"] = plan_id
        account["plan_changed_this_cycle"] = True
        return {"scheduled": plan_id, "effective": account["next_cycle_start"]}

    def get_invoice(self, invoice_id):
        invoice, error = self._invoice_of_verified(invoice_id)
        return {"error": error} if error else dict(invoice, invoice_id=invoice_id)

    def issue_credit(self, invoice_id, amount, reason):
        # The tool checks types and ownership, not policy: whether a credit is allowed is the
        # agent's job (policy rules 5-7), which is exactly what the task tests.
        invoice, error = self._invoice_of_verified(invoice_id)
        if error:
            return {"error": error}
        if reason not in REASONS or amount <= 0:
            return {"error": "invalid amount or reason"}
        invoice["credits"].append({"amount": round(float(amount), 2), "reason": reason})
        return {"credited": round(float(amount), 2), "invoice_id": invoice_id}

    def transfer_to_human(self, summary):
        self.db["transfers"].append({"customer_id": self.verified_customer})
        return {"transferred": True}

    def call(self, name, arguments):
        result = getattr(self, name)(**arguments)
        self.log.append({"name": name, "arguments": arguments, "result": result})
        return result

    # ----------------------------------------------------------------- grading
    def state_hash(self):
        canonical = json.dumps(self.db, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def expected_state_hash(task):
    gym = BrightwaterGym()
    for action in task["expected_actions"]:
        gym.call(action["name"], action["arguments"])
    return gym.state_hash()


def run_episode(task, trajectory):
    """Replay a recorded trajectory (user turns, assistant turns, tool calls) and grade it."""
    gym = BrightwaterGym()
    said = []
    for event in trajectory["events"]:
        if event["type"] == "tool_call":
            gym.call(event["name"], event["arguments"])
        elif event["type"] == "assistant":
            said.append(event["content"])
    state_ok = gym.state_hash() == expected_state_hash(task)
    text = "\n".join(said)
    missing = [fact for fact in task["required_outputs"] if fact not in text]
    reward = 1 if state_ok and not missing else 0
    errors = [c for c in gym.log if "error" in c["result"]]
    return {"reward": reward, "state_matches": state_ok, "missing_outputs": missing, "tool_errors": errors}


def pass_hat_k(n, c, k):
    """tau-bench's pass^k: chance that k independent trials of a task all succeed, estimated from c of n."""
    return math.comb(c, k) / math.comb(n, k)


if __name__ == "__main__":
    with open(os.path.join(HERE, "tasks.json"), encoding="utf8") as fh:
        task = json.load(fh)[0]
    for name in sorted(os.listdir(os.path.join(HERE, "trajectories"))):
        with open(os.path.join(HERE, "trajectories", name), encoding="utf8") as fh:
            trajectory = json.load(fh)
        result = run_episode(task, trajectory)
        print(f"{name:<30} reward={result['reward']} state_matches={result['state_matches']} "
              f"missing={result['missing_outputs']} tool_errors={[e['result']['error'] for e in result['tool_errors']]}")
    print("pass^k for 6 successes in 8 trials:", {k: round(pass_hat_k(8, 6, k), 3) for k in (1, 2, 4, 8)})
