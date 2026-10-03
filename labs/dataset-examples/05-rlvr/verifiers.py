"""Reward functions for the RLVR prompts in rlvr_prompts.jsonl (standard library only).

A verifier turns one model completion into a reward in [0, 1]. In RL with verifiable rewards the
policy samples several completions per prompt, each is scored by the prompt's verifier, and the
rewards drive the policy update; nobody grades the reasoning, only the checkable outcome.

Warning: verify_unit_tests executes model-written code. Here it runs in a subprocess with a timeout,
which is fine for a demo but is not a sandbox; production systems run it in an isolated container
with no network and resource limits. It also trusts the exit code, so a completion that exits
early (sys.exit(0) before the assertions run) earns 1.0: a reward hack that RL policies find.
Chapter 26d.6 explains the hole and exercise 4 in 26d.21 asks you to close it.
"""
import json
import re
import subprocess
import sys

ANSWER_LINE = re.compile(r"^\s*Answer:\s*(.+?)\s*$", re.MULTILINE)
CODE_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def verify_numeric(completion, spec):
    """1.0 if the last 'Answer: <number>' line matches the answer within the tolerance, else 0.0."""
    found = ANSWER_LINE.findall(completion)
    if not found:
        return 0.0                                  # no parsable answer is a wrong answer
    text = found[-1].replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return 1.0 if abs(float(match.group()) - float(spec["answer"])) <= spec.get("tolerance", 0) else 0.0


def verify_unit_tests(completion, spec):
    """1.0 if the code block defines the entry point and every test passes, else 0.0."""
    blocks = CODE_BLOCK.findall(completion)
    if not blocks:
        return 0.0
    program = blocks[-1] + "\n" + "\n".join(spec["tests"]) + "\n"
    try:
        result = subprocess.run([sys.executable, "-c", program], capture_output=True, timeout=spec.get("timeout_s", 5))
    except subprocess.TimeoutExpired:
        return 0.0
    return 1.0 if result.returncode == 0 else 0.0


def verify_format_rules(completion, spec):
    """1.0 only if every rule holds; bullets are lines starting with '- '."""
    bullets = [line[2:].strip() for line in completion.splitlines() if line.startswith("- ")]
    for rule in spec["rules"]:
        name, value = rule["rule"], rule["value"]
        if name == "bullet_count" and len(bullets) != value:
            return 0.0
        if name == "max_words_per_bullet" and any(len(b.split()) > value for b in bullets):
            return 0.0
        if name == "forbidden_first_word" and any(b.split() and b.split()[0] == value for b in bullets):
            return 0.0
    return 1.0


VERIFIERS = {"numeric": verify_numeric, "unit_tests": verify_unit_tests, "format_rules": verify_format_rules}


def reward(item, completion):
    return VERIFIERS[item["verifier"]["type"]](completion, item["verifier"])


SAMPLE_COMPLETIONS = {
    "rlvr-math-0091": [
        "Odd positions sum O, even positions sum E, O + E = 28, O - E in {0, 22, -22}, so O = E = 14 ... 4 x 3! x 4! = 576.\nAnswer: 576",
        "There are 7! = 5040 permutations and roughly one in eleven is divisible by 11.\nAnswer: 458",
        "The count is 576.",          # right number, wrong format: the verifier cannot find 'Answer:' and gives 0
    ],
    "rlvr-code-0337": [
        "```python\ndef is_balanced(s: str) -> bool:\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in '([{':\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack\n```",
        "```python\ndef is_balanced(s: str) -> bool:\n    return s.count('(') == s.count(')') and s.count('[') == s.count(']') and s.count('{') == s.count('}')\n```",
    ],
    "rlvr-if-0512": [
        "- Catches bugs before they reach users\n- Spreads knowledge of the codebase\n- Keeps style and design consistent",
        "- The main benefit is catching bugs early\n- Knowledge sharing\n- Consistency",
    ],
}


if __name__ == "__main__":
    with open(__file__.replace("verifiers.py", "rlvr_prompts.jsonl"), encoding="utf8") as fh:
        items = {json.loads(line)["id"]: json.loads(line) for line in fh}
    for item_id, completions in SAMPLE_COMPLETIONS.items():
        rewards = [reward(items[item_id], c) for c in completions]
        print(f"{item_id}: rewards {rewards}")
