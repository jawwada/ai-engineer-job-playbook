"""Scorers for the evaluation items in eval_items.jsonl (standard library only).

An evaluation set is only as good as its scorers. Each item names one:

- execution_match: run the reference query and the candidate query on every fixture database and
  compare the result rows. Several fixtures, because one fixture can be passed by luck.
- unit_tests: run the candidate's code with the item's assertions; pass only if all succeed. Like the
  RLVR verifier it trusts the exit code, so an early sys.exit(0) passes (chapter 26d.6, exercise 4).
- rubric_judge: a judge model awards points per criterion; the item passes at the threshold. The
  judge itself is not run here (it needs a model); its per-criterion output is aggregated.

Usage:  python3 scorers.py      (scores sample candidates and shows a wrong query passing one fixture)
"""
import json
import os
import sqlite3
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def load_items():
    with open(os.path.join(HERE, "eval_items.jsonl"), encoding="utf8") as fh:
        return {item["id"]: item for item in map(json.loads, filter(str.strip, fh))}


def run_sql(fixture, query):
    db = sqlite3.connect(":memory:")
    try:
        with open(os.path.join(HERE, fixture), encoding="utf8") as fh:
            db.executescript(fh.read())
        return Counter(map(tuple, db.execute(query).fetchall()))   # a multiset: row order ignored
    finally:
        db.close()


def execution_match(item, candidate_sql):
    """Pass only if the candidate returns the reference's rows on every fixture."""
    per_fixture = {}
    for fixture in item["scorer"]["fixtures"]:
        try:
            per_fixture[fixture] = run_sql(fixture, candidate_sql) == run_sql(fixture, item["reference"])
        except sqlite3.Error:
            per_fixture[fixture] = False        # a query that does not run is wrong
    return all(per_fixture.values()), per_fixture


def unit_tests(item, candidate_code, timeout_s=5):
    """Pass only if every assertion holds. Executes model-written code: sandbox it in production."""
    program = candidate_code + "\n" + "\n".join(item["scorer"]["tests"]) + "\n"
    try:
        done = subprocess.run([sys.executable, "-c", program], capture_output=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return False
    return done.returncode == 0


def rubric_judge(item, judge_points):
    """Aggregate a judge's per-criterion points; each must stay within the criterion's maximum."""
    rubric = item["scorer"]["rubric"]
    assert len(judge_points) == len(rubric)
    assert all(0 <= got <= c["points"] for got, c in zip(judge_points, rubric))
    score = sum(judge_points)
    return score >= item["scorer"]["pass_threshold"], score


SQL_CANDIDATES = {
    "correct, written differently": (
        "WITH first_orders AS (SELECT customer_id, MIN(created_at) AS first_at FROM orders GROUP BY customer_id) "
        "SELECT COUNT(*) FROM first_orders WHERE first_at >= '2026-01-01' AND first_at < '2027-01-01'"),
    "counts anyone who ordered in 2026": (
        "SELECT COUNT(DISTINCT customer_id) FROM orders WHERE created_at >= '2026-01-01'"),
    "two bugs that cancel on fixture v1": (
        "SELECT COUNT(DISTINCT customer_id) FROM orders WHERE created_at BETWEEN '2026-01-01' AND '2026-12-31'"),
}

MEDIAN_CANDIDATES = {
    "sorts, handles even length": (
        "def median(xs):\n    s = sorted(xs)\n    n = len(s)\n    mid = n // 2\n"
        "    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2"),
    "forgets to sort": "def median(xs):\n    return xs[len(xs) // 2]",
}


def demo():
    items = load_items()
    sql_item = items["eval-sql-014"]
    for name, query in SQL_CANDIDATES.items():
        passed, per_fixture = execution_match(sql_item, query)
        detail = ", ".join(f"{os.path.basename(f)}={'match' if ok else 'differs'}" for f, ok in per_fixture.items())
        print(f"[execution_match] {name:<36} pass={passed}  ({detail})")
    code_item = items["eval-code-007"]
    for name, code in MEDIAN_CANDIDATES.items():
        print(f"[unit_tests]      {name:<36} pass={unit_tests(code_item, code)}")
    with open(os.path.join(HERE, "results_example.jsonl"), encoding="utf8") as fh:
        results = [json.loads(line) for line in fh if line.strip()]
    judged = next(r for r in results if r["item"] == "eval-sum-031")
    passed, score = rubric_judge(items["eval-sum-031"], judged["judge_points"])
    print(f"[rubric_judge]    judge points {judged['judge_points']} -> score {score}, pass={passed} "
          f"(threshold {items['eval-sum-031']['scorer']['pass_threshold']})")


if __name__ == "__main__":
    demo()
