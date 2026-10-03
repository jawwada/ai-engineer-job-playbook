"""Checks for the fix-log-permissions task. The verifier runs them as root inside the task container."""
import hashlib
import os
import stat
import subprocess

LOG_DIR = "/var/log/app"
LOG = os.path.join(LOG_DIR, "app.log")
JOB = "/opt/app/write_log.sh"
JOB_SHA256 = "4ade4abcfa42a7dcc74ddfdeb40431e09d92f9cebda03a87d07fc62052560840"


def run_as(user, *cmd):
    """Run a command as another user with only that user's own group (no inherited root groups)."""
    return subprocess.run(list(cmd), user=user, group=user, extra_groups=[], capture_output=True, text=True, timeout=60)


def test_job_script_unchanged():
    with open(JOB, "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == JOB_SHA256


def test_job_runs_as_appsvc_and_appends():
    before = os.path.getsize(LOG)
    result = run_as("appsvc", "/bin/sh", JOB)
    assert result.returncode == 0, result.stderr
    assert os.path.getsize(LOG) > before


def test_job_rotates_a_large_log():
    grow = run_as("appsvc", "/bin/sh", "-c", f"head -c 1100000 /dev/zero >> {LOG}")
    assert grow.returncode == 0, grow.stderr
    result = run_as("appsvc", "/bin/sh", JOB)
    assert result.returncode == 0, result.stderr
    assert os.path.exists(LOG + ".1")
    assert os.path.getsize(LOG) < 1024


def test_nothing_is_world_writable():
    for root, _dirs, files in os.walk(LOG_DIR):
        for path in [root] + [os.path.join(root, name) for name in files]:
            assert not os.stat(path).st_mode & stat.S_IWOTH, path


def test_auditor_can_read_but_not_write():
    assert run_as("auditor", "cat", LOG).returncode == 0
    assert run_as("auditor", "/bin/sh", "-c", f"echo tamper >> {LOG}").returncode != 0
