"""Small, exact calculations that show how a model (or the team) uses each dataset in this folder.

Each function prints the numbers quoted in chapter 26d. Standard library only:  python3 how_models_use_it.py
"""
import csv
import json
import math
import os
from collections import Counter
from itertools import combinations, permutations

HERE = os.path.dirname(os.path.abspath(__file__))


def load_jsonl(rel):
    with open(os.path.join(HERE, rel), encoding="utf8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


# ------------------------------------------------------------------ 01 SFT: loss only on the assistant's tokens

def sft_loss_mask_demo():
    """Render one chat, mask everything except the assistant's tokens, and average the loss over the rest."""
    record = load_jsonl("01-sft/sft_examples.jsonl")[0]
    tokens, labels = [], []
    for message in record["messages"]:
        header = [f"<|{message['role']}|>"]
        body = message["content"].split()          # toy tokenizer: whitespace; real ones use subwords
        tokens += header + body + ["<|end|>"]
        trained = message["role"] == "assistant"
        labels += [-100] + (body + ["<|end|>"] if trained else [-100] * (len(body) + 1))
    n_trained = sum(1 for label in labels if label != -100)
    # Suppose the model gives each correct next token probability 0.6 before training and 0.9 after.
    before, after = -math.log(0.6), -math.log(0.9)
    print(f"[SFT] {len(tokens)} tokens in the rendered chat, {n_trained} carry loss (assistant reply + end marker);"
          f" mean loss {before:.3f} nats at p=0.6, {after:.3f} at p=0.9")


# ------------------------------------------------------------------ 02 preference pairs: the DPO loss

def dpo_demo(beta=0.1):
    """DPO compares how much more the policy prefers chosen over rejected than the frozen reference does."""
    policy_chosen, policy_rejected = -42.0, -45.0        # summed log-probs of each response under the policy
    ref_chosen, ref_rejected = -43.0, -44.0              # the same under the frozen reference model
    margin = beta * ((policy_chosen - ref_chosen) - (policy_rejected - ref_rejected))
    loss = -math.log(sigmoid(margin))
    print(f"[DPO] beta={beta}: implicit reward margin {margin:.2f}, loss {loss:.3f} "
          f"(loss at zero margin would be {math.log(2):.3f}); the gradient raises chosen and lowers rejected log-probs")


# ------------------------------------------------------------------ 03 reward model: Bradley-Terry, rankings -> pairs, PRM

def reward_model_demo():
    r_chosen, r_rejected = 1.3, -0.4
    loss = -math.log(sigmoid(r_chosen - r_rejected))
    record = load_jsonl("03-reward-model/rankings.jsonl")[0]
    order, ties = record["ranking"], {frozenset(t) for t in record["ties"]}
    pairs = [(a, b) for i, a in enumerate(order) for b in order[i + 1:] if frozenset((a, b)) not in ties]
    print(f"[RM] Bradley-Terry loss for rewards 1.3 vs -0.4: {loss:.3f}; ranking {order} with tie {record['ties'][0]} "
          f"gives {len(pairs)} training pairs: {pairs}")
    flawed = [0.95, 0.92, 0.18, 0.40]       # a process reward model's P(step is correct) for the pen solution
    correct = [0.95, 0.93, 0.90, 0.94]      # the same for a correct solution
    agg = lambda s: (min(s), math.prod(s))
    print(f"[PRM] flawed solution min/product {agg(flawed)[0]:.2f}/{agg(flawed)[1]:.3f}; correct solution "
          f"{agg(correct)[0]:.2f}/{agg(correct)[1]:.3f}; best-of-n keeps the correct one")


# ------------------------------------------------------------------ 04 RLAIF: position-consistency filter

def rlaif_demo():
    records = load_jsonl("04-rlaif/ai_feedback.jsonl")
    kept = [r for r in records if r["label"] is not None]
    consistent = sum(1 for r in records if len({j["verdict"] for j in r["judgments"]}) == 1)
    print(f"[RLAIF] {consistent}/{len(records)} items have the same verdict in both orders; {len(kept)} kept as preference pairs")


# ------------------------------------------------------------------ 05 RLVR: group-relative advantages (GRPO-style)

def grpo_demo():
    group = [1, 0, 0, 1, 1, 0, 0, 0]                   # rewards of 8 sampled completions for one prompt
    mean = sum(group) / len(group)
    std = math.sqrt(sum((r - mean) ** 2 for r in group) / len(group))
    advantages = [round((r - mean) / std, 2) for r in group]
    print(f"[RLVR] group rewards {group}: mean {mean:.3f}, std {std:.3f}, advantages {advantages}")
    print("[RLVR] all-correct or all-wrong groups have std 0, so every advantage is 0 and the prompt teaches nothing")
    for item in load_jsonl("05-rlvr/rlvr_prompts.jsonl"):
        probe = item["difficulty_probe"]
        rate = probe["correct"] / probe["samples"]
        print(f"        {item['id']:<16} pass rate {rate:.2f} -> {'train on it' if 0 < rate < 1 else 'exclude'}")


# ------------------------------------------------------------------ 06 evaluation: confidence intervals, pass@k

def wilson(successes, n, z=1.96):
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def pass_at_k(n, c, k):
    """Unbiased pass@k from n samples with c correct: 1 - C(n-c, k) / C(n, k)."""
    return 1.0 if n - c < k else 1 - math.comb(n - c, k) / math.comb(n, k)


def eval_demo():
    results = load_jsonl("06-eval/results_example.jsonl")
    passed = sum(r["passed"] for r in results)
    lo, hi = wilson(passed, len(results))
    lo400, hi400 = wilson(round(0.667 * 400), 400)
    print(f"[EVAL] {passed}/{len(results)} passed: 95% Wilson interval {lo:.2f}-{hi:.2f}; "
          f"the same rate on 400 items gives {lo400:.2f}-{hi400:.2f}")
    print(f"[EVAL] pass@1 and pass@5 from 10 samples with 3 correct: {pass_at_k(10, 3, 1):.2f}, {pass_at_k(10, 3, 5):.2f}")


# ------------------------------------------------------------------ 07 pairwise annotation: agreement without ground truth

def fleiss_kappa(table):
    """table: one row per item, counts per category; every item has the same number of raters."""
    n_items, raters = len(table), sum(table[0])
    p_j = [sum(row[j] for row in table) / (n_items * raters) for j in range(len(table[0]))]
    p_i = [(sum(c * c for c in row) - raters) / (raters * (raters - 1)) for row in table]
    p_bar, p_e = sum(p_i) / n_items, sum(p * p for p in p_j)
    return (p_bar - p_e) / (1 - p_e)


def krippendorff_alpha_nominal(units):
    """units: list of lists of labels (missing raters simply absent)."""
    coincidence = Counter()
    for labels in units:
        m = len(labels)
        if m < 2:
            continue
        for a, b in permutations(range(m), 2):
            coincidence[(labels[a], labels[b])] += 1 / (m - 1)
    totals = Counter()
    for (a, _), weight in coincidence.items():
        totals[a] += weight
    n = sum(totals.values())
    observed = sum(w for (a, b), w in coincidence.items() if a != b)
    expected = sum(totals[a] * totals[b] for a in totals for b in totals if a != b) / (n - 1)
    return 1 - observed / expected


def annotation_demo():
    with open(os.path.join(HERE, "07-pairwise-annotation/raw_annotations.csv"), encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    regular = [r for r in rows if r["is_gold"] == "false"]
    by_item = {}
    for r in regular:
        by_item.setdefault(r["item_id"], []).append(r["choice"])
    cats = ["A", "B", "tie"]
    table = [[labels.count(c) for c in cats] for labels in by_item.values()]
    for item, labels in by_item.items():
        counts = Counter(labels)
        top, votes = counts.most_common(1)[0]
        soft = {c: round(labels.count(c) / len(labels), 2) for c in cats}
        verdict = (f"majority {top} ({votes}/{len(labels)})" if votes > len(labels) / 2
                   else "no majority: adjudicate or keep only the soft label")
        print(f"[ANNOT] {item}: votes {dict(counts)} {verdict}; soft label {soft}")
    print(f"[ANNOT] Fleiss' kappa {fleiss_kappa(table):.3f}; Krippendorff's alpha (nominal) "
          f"{krippendorff_alpha_nominal(list(by_item.values())):.3f}")
    gold = [r for r in rows if r["is_gold"] == "true"]
    wrong = [r["annotator_id"] for r in gold if r["choice"] != r["gold_answer"]]
    print(f"[ANNOT] gold item: {len(gold) - len(wrong)}/{len(gold)} correct; failed: {wrong}")


# ------------------------------------------------------------------ 08 reasoning: check the answers by program

def reasoning_demo():
    count = sum(1 for p in permutations("1234567") if int("".join(p)) % 11 == 0)
    d = 1.5 / 0.25
    print(f"[REASONING] brute force over 5,040 permutations finds {count} multiples of 11; incline answer d = h/mu = {d:.1f} m")


# ------------------------------------------------------------------ 09 egocentric video: segments become training clips

def video_demo():
    with open(os.path.join(HERE, "09-egocentric-video/clip_annotations.json"), encoding="utf8") as fh:
        ann = json.load(fh)
    fps = 30
    clips = [(a["verb"], a["noun"], round(a["start_s"] * fps), round(a["end_s"] * fps)) for a in ann["actions"]]
    covered = sum(a["end_s"] - a["start_s"] for a in ann["actions"])
    print(f"[VIDEO] {len(clips)} action segments cover {covered:.1f} of 24.0 s; first training clip "
          f"'{clips[0][0]} {clips[0][1]}' = frames {clips[0][2]}-{clips[0][3]}; verbs {dict(Counter(c[0] for c in clips))}")


# ------------------------------------------------------------------ 15 QA: acceptance sampling

def acceptance_demo(n=80, c=2):
    def p_accept(p):
        return sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(c + 1))
    curve = {f"{p:.1%}": round(p_accept(p), 3) for p in (0.005, 0.01, 0.02, 0.03, 0.05, 0.08)}
    print(f"[QA] audit {n} records, accept the batch if at most {c} defects; P(accept) by true defect rate: {curve}")


# ------------------------------------------------------------------ 16 operations: unit economics

def ops_demo(price=150.0, expert_rate=36.0, qa_rate=30.0, budget_minutes=150):
    with open(os.path.join(HERE, "16-ops-telemetry/task_log.csv"), encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    cost = sum(int(r["expert_minutes"]) / 60 * expert_rate + int(r["qa_minutes"]) / 60 * qa_rate for r in rows)
    accepted = sum(r["accepted"] == "true" for r in rows)
    per_item = cost / accepted
    first, second = rows[:5], rows[5:]
    mean = lambda rs: sum(int(r["expert_minutes"]) for r in rs) / len(rs)
    print(f"[OPS] {accepted}/{len(rows)} accepted; cost per accepted item ${per_item:.2f} vs price ${price:.0f}: "
          f"gross margin {1 - per_item / price:.1%}; expert minutes per task {mean(first):.0f} -> {mean(second):.0f} "
          f"(budget {budget_minutes})")


if __name__ == "__main__":
    for demo in (sft_loss_mask_demo, dpo_demo, reward_model_demo, rlaif_demo, grpo_demo, eval_demo,
                 annotation_demo, reasoning_demo, video_demo, acceptance_demo, ops_demo):
        demo()
