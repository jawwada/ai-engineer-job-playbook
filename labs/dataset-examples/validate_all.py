"""Validate every example dataset in this folder: schema, internal consistency, and the graders.

Each check is what a data-production team runs before delivery: required fields, enums, IDs that
point at real things, numbers that add up, checksums that match, and graders that give the
reference solution reward 1 and known-bad solutions reward 0.

Usage:  python3 validate_all.py
Standard library only. The SWE-bench-style check also needs git and pytest; without them it is
reported as SKIP, not FAIL. Exit code is 0 when nothing fails.
"""
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from itertools import permutations

sys.dont_write_bytecode = True          # importing the lab modules must not leave __pycache__ behind
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = []


class Skip(Exception):
    pass


def check(name):
    def register(fn):
        CHECKS.append((name, fn))
        return fn
    return register


def path(rel):
    return os.path.join(HERE, rel)


def jsonl(rel):
    with open(path(rel), encoding="utf8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_json(rel):
    with open(path(rel), encoding="utf8") as fh:
        return json.load(fh)


def rows(rel):
    with open(path(rel), encoding="utf8", newline="") as fh:
        return list(csv.DictReader(fh))


def module(rel, name):
    spec = importlib.util.spec_from_file_location(name, path(rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def unique_ids(records, key="id"):
    ids = [r[key] for r in records]
    assert len(ids) == len(set(ids)), f"duplicate ids: {[i for i, n in Counter(ids).items() if n > 1]}"


# ---------------------------------------------------------------------------------------- 01 SFT
@check("01 SFT demonstrations")
def _():
    records = jsonl("01-sft/sft_examples.jsonl")
    unique_ids(records)
    for r in records:
        msgs = r["messages"]
        roles = [m["role"] for m in msgs]
        assert set(roles) <= {"system", "user", "assistant", "tool"}, r["id"]
        assert "system" not in roles[1:], f"{r['id']}: system message must come first"
        assert roles[-1] == "assistant" and msgs[-1]["content"], f"{r['id']}: must end with an assistant reply"
        tools = {t["function"]["name"] for t in r.get("tools", [])}
        open_calls = set()
        for m in msgs:
            for call in m.get("tool_calls") or []:
                assert call["function"]["name"] in tools, f"{r['id']}: call to undeclared tool"
                json.loads(call["function"]["arguments"])          # arguments are a JSON string
                open_calls.add(call["id"])
            if m["role"] == "tool":
                assert m["tool_call_id"] in open_calls, f"{r['id']}: tool result without a call"
        meta = r["meta"]
        assert meta["spec_version"] and meta["author"] != meta["reviewer"], f"{r['id']}: needs a separate reviewer"
        assert 1 <= meta["review_score"] <= 5
    return f"{len(records)} chats; roles, tool calls and reviewer fields consistent"


# ---------------------------------------------------------------------------------------- 02 preferences
@check("02 preference pairs")
def _():
    records = jsonl("02-preference/preference_pairs.jsonl")
    unique_ids(records)
    for r in records:
        assert r["prompt"][-1]["role"] == "user"
        assert [m["role"] for m in r["chosen"]] == ["assistant"] == [m["role"] for m in r["rejected"]]
        assert r["chosen"][0]["content"] != r["rejected"][0]["content"]
        votes = Counter(a["preferred"] for a in r["meta"]["annotations"])
        assert votes["chosen"] > votes["rejected"], f"{r['id']}: majority must prefer 'chosen'"
        assert r["meta"]["chosen_sample"] != r["meta"]["rejected_sample"], "pair must come from two samples"
    return f"{len(records)} pairs; annotator majority agrees with the chosen side"


# ---------------------------------------------------------------------------------------- 03 reward model
@check("03 rankings and process labels")
def _():
    for r in jsonl("03-reward-model/rankings.jsonl"):
        ids = [x["id"] for x in r["responses"]]
        assert sorted(r["ranking"]) == sorted(ids), "ranking must be a permutation of the responses"
        for a, b in r["ties"]:
            assert abs(r["ranking"].index(a) - r["ranking"].index(b)) == 1, "tied responses must be adjacent"
        totals = [sum(r["likert"][x].values()) for x in r["ranking"]]
        assert totals == sorted(totals, reverse=True), "Likert totals contradict the ranking"
    for r in jsonl("03-reward-model/prm_steps.jsonl"):
        labels = [s["label"] for s in r["steps"]]
        assert set(labels) <= {-1, 0, 1}
        assert r["first_error_step"] == labels.index(-1) + 1
        assert r["final_answer"] != r["reference_answer"]
        # Re-derive the reference: exactly 10 pens from packs of 4 at $10 and singles at $3.
        best = min(10 * packs + 3 * (10 - 4 * packs) for packs in range(0, 10 // 4 + 1))
        assert str(best) == r["reference_answer"], best
    return "ranking is a permutation with adjacent ties; PRM first error at step 3; reference $26 re-derived"


# ---------------------------------------------------------------------------------------- 04 RLAIF
@check("04 AI feedback (RLAIF)")
def _():
    records = jsonl("04-rlaif/ai_feedback.jsonl")
    for r in records:
        orders = sorted(j["order"] for j in r["judgments"])
        assert orders == ["AB", "BA"], "each item is judged in both orders"
        agree = len({j["verdict"] for j in r["judgments"]}) == 1
        assert (r["label"] is not None) == agree, f"{r['id']}: keep the label only when both orders agree"
        if r["label"]:
            winner = "response_a" if r["judgments"][0]["verdict"] == "A" else "response_b"
            assert r["label"]["chosen"] == winner
        else:
            assert r.get("drop_reason")
        audit = r["human_audit"]
        if audit.get("sampled"):
            assert audit["agrees_with_label"] == (audit["verdict"] == r["judgments"][0]["verdict"])
    return f"{len(records)} items; labels kept only when verdicts survive the order swap"


# ---------------------------------------------------------------------------------------- 05 RLVR
@check("05 RLVR prompts and verifiers")
def _():
    items = jsonl("05-rlvr/rlvr_prompts.jsonl")
    for item in items:
        probe = item["difficulty_probe"]
        informative = 0 < probe["correct"] < probe["samples"]
        assert item["use_in_batch"] == informative, f"{item['id']}: all-right or all-wrong prompts carry no signal"
    verifiers = module("05-rlvr/verifiers.py", "verifiers")
    by_id = {i["id"]: i for i in items}
    expected = {"rlvr-math-0091": [1, 0, 0], "rlvr-code-0337": [1, 0], "rlvr-if-0512": [1, 0]}
    for item_id, completions in verifiers.SAMPLE_COMPLETIONS.items():
        got = [verifiers.reward(by_id[item_id], c) for c in completions]
        assert got == expected[item_id], f"{item_id}: {got}"
    return "batch filter matches the pass-rate probe; verifiers score the samples [1,0,0] [1,0] [1,0]"


# ---------------------------------------------------------------------------------------- 06 eval
@check("06 evaluation set and scorers")
def _():
    items = jsonl("06-eval/eval_items.jsonl")
    unique_ids(items)
    config = load_json("06-eval/eval_config.json")
    assert os.path.exists(path("06-eval/" + config["items_file"]))
    canaries = {i["canary"] for i in items}
    assert len(canaries) == 1 and "do not include in training data" in canaries.pop()
    for item in items:
        for fixture in item["scorer"].get("fixtures", []):
            assert os.path.exists(path("06-eval/" + fixture)), fixture
    ids = {i["id"] for i in items}
    assert all(r["item"] in ids for r in jsonl("06-eval/results_example.jsonl"))
    scorers = module("06-eval/scorers.py", "scorers")
    by_id = scorers.load_items()
    verdicts = {name: scorers.execution_match(by_id["eval-sql-014"], q)[0] for name, q in scorers.SQL_CANDIDATES.items()}
    assert list(verdicts.values()) == [True, False, False], verdicts
    lucky = scorers.execution_match(by_id["eval-sql-014"], scorers.SQL_CANDIDATES["two bugs that cancel on fixture v1"])[1]
    assert list(lucky.values()) == [True, False], "the second fixture must catch the lucky query"
    assert [scorers.unit_tests(by_id["eval-code-007"], c) for c in scorers.MEDIAN_CANDIDATES.values()] == [True, False]
    return "one canary on every item; fixtures exist; the lucky query passes v1 and is caught by v2"


# ---------------------------------------------------------------------------------------- 07 pairwise annotation
@check("07 pairwise annotation (no ground truth)")
def _():
    data = rows("07-pairwise-annotation/raw_annotations.csv")
    by_item = {}
    for r in data:
        assert r["choice"] in {"A", "B", "tie"} and r["shown_left"] in {"A", "B"}
        assert 1 <= int(r["confidence"]) <= 5 and int(r["seconds_spent"]) > 0
        by_item.setdefault(r["item_id"], []).append(r)
    for item_id, group in by_item.items():
        assert len({(g["query"], g["video_a"], g["video_b"]) for g in group}) == 1, f"{item_id}: inconsistent item text"
        annotators = [g["annotator_id"] for g in group]
        assert len(annotators) == len(set(annotators)) == 5, f"{item_id}: needs 5 distinct annotators"
        if group[0]["is_gold"] == "true":
            assert all(g["gold_answer"] in {"A", "B", "tie"} for g in group)
    stats = module("how_models_use_it.py", "how_models_use_it")
    regular = {k: [g["choice"] for g in v] for k, v in by_item.items() if v[0]["is_gold"] == "false"}
    kappa = stats.fleiss_kappa([[labels.count(c) for c in ("A", "B", "tie")] for labels in regular.values()])
    alpha = stats.krippendorff_alpha_nominal(list(regular.values()))
    assert (round(kappa, 3), round(alpha, 3)) == (0.351, 0.367), (kappa, alpha)
    return f"{len(data)} judgments, 5 per item; Fleiss' kappa {kappa:.3f}, Krippendorff's alpha {alpha:.3f}"


# ---------------------------------------------------------------------------------------- 08 reasoning
@check("08 expert reasoning items")
def _():
    items = jsonl("08-reasoning/reasoning_items.jsonl")
    unique_ids(items)
    by_id = {i["id"]: i for i in items}
    count = sum(1 for p in permutations("1234567") if int("".join(p)) % 11 == 0)
    assert count == by_id["rsn-math-0144"]["verifier"]["answer"] == 576
    phys = by_id["rsn-phys-0057"]["verifier"]
    assert abs(1.5 / 0.25 - phys["answer"]) <= phys["tolerance"]
    legal = by_id["rsn-legal-0023"]["verifier"]
    assert legal["pass_threshold"] <= sum(c["points"] for c in legal["rubric"]) == 10
    for item in items:
        assert item["review"]["independent_resolve"]["agrees"], f"{item['id']}: second expert disagrees"
        assert item["common_wrong_answers"], f"{item['id']}: list the traps"
    return "576 re-counted by brute force; d = 6.0 m re-computed; rubric totals 10 with pass at 8"


# ---------------------------------------------------------------------------------------- 09 egocentric video
@check("09 egocentric video annotations")
def _():
    manifest = load_json("09-egocentric-video/clip_manifest.json")
    ann = load_json("09-egocentric-video/clip_annotations.json")
    assert ann["clip_id"] == manifest["clip_id"]
    fps, duration = manifest["fps"], manifest["duration_s"]
    assert manifest["frames"] == round(fps * duration)
    assert all(manifest["privacy"].values()) and manifest["consent_id"]
    actions = ann["actions"]
    for a, b in zip(actions, actions[1:]):
        assert a["end_s"] <= b["start_s"], f"overlapping actions {a['id']} {b['id']}"
    assert all(0 <= a["start_s"] < a["end_s"] <= duration for a in actions)
    for n in ann["narrations"]:
        assert n["text"].startswith("#C C "), "narrations use the camera-wearer convention"
        assert any(a["start_s"] <= n["t_s"] <= a["end_s"] for a in actions), f"narration at {n['t_s']}s has no action"
    width, height = manifest["resolution"]
    tracks = {t["track_id"] for t in ann["object_tracks"]}
    for t in ann["object_tracks"]:
        for box in t["boxes"]:
            x, y, w, h = box["bbox_xywh"]
            assert 0 <= box["frame"] < manifest["frames"] and x + w <= width and y + h <= height, t["track_id"]
    assert all(c["track_id"] in tracks for c in ann["hand_object_contact"])
    return f"{len(actions)} non-overlapping actions; every narration inside an action; boxes inside 1920x1080"


# ---------------------------------------------------------------------------------------- 10 terminal task
@check("10 terminal-agent task (Harbor format)")
def _():
    root = "10-terminal-task/fix-log-permissions/"
    for rel in ("instruction.md", "task.toml", "environment/Dockerfile", "solution/solve.sh",
                "tests/test.sh", "tests/test_outputs.py"):
        assert os.path.exists(path(root + rel)), rel
    try:
        import tomllib
    except ModuleNotFoundError:
        raise Skip("needs Python 3.11+ for tomllib")
    with open(path(root + "task.toml"), "rb") as fh:
        task = tomllib.load(fh)
    assert task["schema_version"] and task["task"]["name"]
    assert task["agent"]["timeout_sec"] > 0 and task["verifier"]["timeout_sec"] > 0
    with open(path(root + "environment/Dockerfile"), encoding="utf8") as fh:
        copies = [line for line in fh if line.strip().upper().startswith(("COPY", "ADD"))]
    assert not any("solution" in c or "tests" in c for c in copies), "the image must not contain tests or solution"
    with open(path(root + "tests/test.sh"), encoding="utf8") as fh:
        assert "/logs/verifier/reward.txt" in fh.read()
    with open(path(root + "tests/test_outputs.py"), encoding="utf8") as fh:
        compile(fh.read(), "test_outputs.py", "exec")           # syntax check without writing bytecode
    return "all six files present; task.toml parses; tests and solution stay out of the image"


# ---------------------------------------------------------------------------------------- 11 SWE task
@check("11 SWE-bench-style instance")
def _():
    inst = load_json("11-swe-task/instance.json")
    required = ["instance_id", "repo", "base_commit", "problem_statement", "hints_text", "created_at", "version",
                "environment_setup_commit", "patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS"]
    assert all(k in inst for k in required)
    touched = lambda patch: re.findall(r"^\+\+\+ b/(\S+)", patch, re.MULTILINE)
    assert all(f.startswith("tests/") for f in touched(inst["test_patch"]))
    assert not any(f.startswith("tests/") for f in touched(inst["patch"])), "the gold patch must not edit tests"
    for test_id in inst["FAIL_TO_PASS"]:
        assert test_id.split("::")[-1] in inst["test_patch"]
    if not shutil.which("git"):
        raise Skip("git not installed; static checks passed")
    if importlib.util.find_spec("pytest") is None:
        raise Skip("pytest not installed for this Python; static checks passed")
    verify = module("11-swe-task/verify_instance.py", "verify_instance")
    gold_resolved, _ = verify.grade(inst, inst["patch"])
    with open(path("11-swe-task/candidate_wrong.patch"), encoding="utf8") as fh:
        wrong_resolved, wrong = verify.grade(inst, fh.read())
    assert gold_resolved and not wrong_resolved
    failing = [t.split("::")[-1] for t, ok in wrong.items() if not ok]
    return f"gold patch resolves; wrong patch fails {failing}"


# ---------------------------------------------------------------------------------------- 12 agentic gym
@check("12 agentic gym (tau-bench style)")
def _():
    gym = module("12-agentic-gym/gym.py", "gym")
    tool_names = [t["name"] for t in load_json("12-agentic-gym/tools.json")["tools"]]
    assert all(callable(getattr(gym.BrightwaterGym, name, None)) for name in tool_names)
    for t in load_json("12-agentic-gym/tools.json")["tools"]:
        assert t["inputSchema"]["type"] == "object" and t["description"]
    task = load_json("12-agentic-gym/tasks.json")[0]
    assert all(a["name"] in tool_names for a in task["expected_actions"])
    rewards = {}
    for name in sorted(os.listdir(path("12-agentic-gym/trajectories"))):
        rewards[name] = gym.run_episode(task, load_json("12-agentic-gym/trajectories/" + name))["reward"]
    assert rewards == {"1_reference.json": 1, "2_waives_late_fee.json": 0, "3_skips_verification.json": 0,
                       "4_wrong_plan.json": 0}, rewards
    assert [round(gym.pass_hat_k(8, 6, k), 3) for k in (1, 2, 4, 8)] == [0.75, 0.536, 0.214, 0.0]
    return "reference trajectory scores 1, the three flawed ones 0; pass^k 0.75 -> 0.0 as k grows"


# ---------------------------------------------------------------------------------------- 13 delivery
@check("13 delivery package (JSONL, CSV, datasheet, manifest)")
def _():
    manifest = load_json("13-delivery/manifest.json")
    for name, meta in manifest["files"].items():
        with open(path("13-delivery/" + name), "rb") as fh:
            blob = fh.read()
        assert hashlib.sha256(blob).hexdigest() == meta["sha256"], f"{name}: checksum mismatch"
        assert len(blob) == meta["bytes"], f"{name}: size mismatch"
    records = jsonl("13-delivery/train.jsonl")
    assert len(records) == manifest["records"]["train"]
    intents = set(re.search(r"enum\[(.*)\]", manifest["schema"]["intent"]).group(1).split(", "))
    for r in records:
        assert r["intent"] in intents and r["split"] == "train"
        for e in r["entities"]:
            assert r["text"][e["start"]:e["end"]] == e["value"], f"{r['id']}: bad offsets for {e['value']}"
    table = {r["id"]: r for r in rows("13-delivery/train.csv")}
    for r in records:
        c = table[r["id"]]
        assert (c["text"], c["intent"]) == (r["text"], r["intent"])
        assert json.loads(c["entities_json"]) == r["entities"] and int(c["entity_count"]) == len(r["entities"])
    return f"3 checksums match; {len(records)} records; entity offsets exact; CSV mirrors JSONL"


# ---------------------------------------------------------------------------------------- 14 provenance
@check("14 synthetic-data lineage")
def _():
    sft = {r["id"]: r for r in jsonl("01-sft/sft_examples.jsonl")}
    for r in jsonl("14-synthetic-provenance/lineage.jsonl"):
        checks = r["automatic_checks"]
        duplicate = checks["near_duplicate_max_cosine"] > checks["dedupe_threshold"]
        if r["status"] == "accepted":
            assert not duplicate and r["qa_review"]["decision"] == "accept"
            assert r["final_record_id"] in sft, "accepted lineage must point at a delivered record"
            assert sft[r["final_record_id"]]["meta"]["source"] != "expert_written", "a generated record is not expert_written"
        else:
            assert duplicate or r.get("reject_reason")
            assert r["final_record_id"] is None
    return "accepted record traces to sft-000417; the near-duplicate (0.96 > 0.92) was rejected"


# ---------------------------------------------------------------------------------------- 15 golden set and QA
@check("15 golden set, gold questions and QA audit")
def _():
    manifest = load_json("13-delivery/manifest.json")
    intents = set(re.search(r"enum\[(.*)\]", manifest["schema"]["intent"]).group(1).split(", "))
    gold = jsonl("15-golden-and-qa/golden_set.jsonl")
    assert all(g["label"] in intents and g["explanation"] for g in gold)
    floor = manifest["quality"]["gold_accuracy_min"]
    flagged = [r["annotator_id"] for r in rows("15-golden-and-qa/gold_question_results.csv")
               if int(r["gold_correct"]) / int(r["gold_seen"]) < floor]
    audit = rows("15-golden-and-qa/qa_audit_sample.csv")
    for r in audit:
        assert (r["defect"] == "true") == (r["delivered_label"] != r["auditor_label"])
    defects = sum(r["defect"] == "true" for r in audit)
    return f"{len(gold)} gold items; below the {floor:.0%} gold floor: {flagged}; audit sample {defects}/{len(audit)} defects"


# ---------------------------------------------------------------------------------------- 16 operations
@check("16 operations telemetry")
def _():
    log = rows("16-ops-telemetry/task_log.csv")
    unique_ids(log, "task_id")
    for r in log:
        assert int(r["expert_minutes"]) > 0 and int(r["qa_minutes"]) >= 0 and int(r["rework_rounds"]) >= 0
        assert r["accepted"] in {"true", "false"}
    return f"{len(log)} task records with minutes, rework and acceptance"


# ---------------------------------------------------------------------------------------- the worked numbers
@check("how_models_use_it.py numbers")
def _():
    out = subprocess.run([sys.executable, path("how_models_use_it.py")], capture_output=True, text=True, check=True).stdout
    for needle in ("77 carry loss", "loss 0.598", "-0.4: 0.168", "1/2 items", "advantages [1.29, -0.77",
                   "0.21-0.94", "0.30, 0.92", "kappa 0.351", "P-04: votes {'A': 2, 'B': 2, 'tie': 1} no majority",
                   "finds 576", "22.7 of 24.0", "'2.0%': 0.784",
                   "$183.81", "-22.5%"):
        assert needle in out, f"missing '{needle}' in the output"
    return "every number quoted in chapter 26d is reproduced"


def main():
    failed = 0
    for name, fn in CHECKS:
        try:
            status, detail = "PASS", fn()
        except Skip as why:
            status, detail = "SKIP", str(why)
        except Exception as err:          # report every failure, keep going
            status, detail = "FAIL", f"{type(err).__name__}: {err}"
            failed += 1
        print(f"{status}  {name:<52} {detail}")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks without failures")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
