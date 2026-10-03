"""Grade a SWE-bench-style instance the way an evaluation harness does (needs git and pytest).

1. Rebuild the repository at base_commit from repo/ (deterministic author, committer and dates,
   so the commit hash must equal instance.json's base_commit).
2. Apply test_patch: FAIL_TO_PASS tests must fail and PASS_TO_PASS tests must pass.
3. Apply a candidate patch (the gold patch, or a model's patch): the instance is resolved only if
   every FAIL_TO_PASS and every PASS_TO_PASS test passes.

Usage:  python3 verify_instance.py [candidate.patch]      (defaults to the gold patch)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Example Maintainer", "GIT_AUTHOR_EMAIL": "maintainer@example.com", "GIT_AUTHOR_DATE": "2026-09-01T09:00:00+00:00",
    "GIT_COMMITTER_NAME": "Example Maintainer", "GIT_COMMITTER_EMAIL": "maintainer@example.com", "GIT_COMMITTER_DATE": "2026-09-01T09:00:00+00:00",
}


def git(cwd, *args, stdin=None):
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args], cwd=cwd,
                          env=dict(os.environ, **GIT_ENV), input=stdin, capture_output=True, text=True, check=True).stdout


def test_passes(cwd, test_id):
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test_id], cwd=cwd,
                            capture_output=True, text=True)
    return result.returncode == 0


def grade(instance, candidate_patch):
    work = tempfile.mkdtemp()
    try:
        shutil.copytree(os.path.join(HERE, "repo"), work, dirs_exist_ok=True)
        git(work, "init", "-q", "-b", "main")
        git(work, "add", "-A")
        git(work, "commit", "-q", "-m", "querykit 0.4")
        head = git(work, "rev-parse", "HEAD").strip()
        assert head == instance["base_commit"], f"base_commit mismatch: {head}"

        git(work, "apply", "-", stdin=instance["test_patch"])
        before_f2p = {t: test_passes(work, t) for t in instance["FAIL_TO_PASS"]}
        before_p2p = {t: test_passes(work, t) for t in instance["PASS_TO_PASS"]}
        assert not any(before_f2p.values()), "a FAIL_TO_PASS test already passes before the fix"
        assert all(before_p2p.values()), "a PASS_TO_PASS test fails before the fix"

        git(work, "apply", "-", stdin=candidate_patch)
        after = {t: test_passes(work, t) for t in instance["FAIL_TO_PASS"] + instance["PASS_TO_PASS"]}
        return all(after.values()), after
    finally:
        shutil.rmtree(work)


def main():
    with open(os.path.join(HERE, "instance.json"), encoding="utf8") as fh:
        instance = json.load(fh)
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf8") as fh:
            candidate = fh.read()
    else:
        candidate = instance["patch"]
    resolved, results = grade(instance, candidate)
    for test_id, ok in results.items():
        print(("PASS " if ok else "FAIL ") + test_id)
    print("resolved:", resolved)
    return resolved


if __name__ == "__main__":
    main()
