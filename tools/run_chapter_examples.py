#!/usr/bin/env python3
"""Run every Python example in a chapter, straight from the Markdown, so the book cannot drift from the truth.

Rules for chapter authors:
- A ```pycon block is a doctest session (lines start with >>> or ...); its printed output must match.
- A ```python block must run on its own (fresh namespace) and should state its results with assert.
- First-line markers in a ```python block:
    # requires: 3.14     run it with that Python version or newer (skipped, with a note, if none is installed)
    # skip-test          shown for reading only (a fragment, or code that needs a network or a server)
- Blocks in other languages are ignored.

Usage:  python3 tools/run_chapter_examples.py book/part-4-engineering-and-roles/49a-....md [more.md ...]
Exit code 1 if any block fails.
"""
import doctest
import glob
import io
import os
import re
import shutil
import subprocess
import sys
import textwrap
from contextlib import redirect_stdout

FENCE = re.compile(r"^```(python|pycon)[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
REQUIRES = re.compile(r"^#\s*requires:\s*(\d+)\.(\d+)")


def find_python(major, minor):
    """Return a path to a Python interpreter of at least the given version, or None."""
    if sys.version_info >= (major, minor):
        return sys.executable
    candidates = []
    for minor_try in range(minor, minor + 6):
        name = f"python{major}.{minor_try}"
        found = shutil.which(name)
        if found:
            candidates.append(found)
        candidates += glob.glob(os.path.expanduser(f"~/.local/bin/{name}"))
    for exe in candidates:
        try:
            out = subprocess.run([exe, "-c", "import sys; print(sys.version_info[:2])"],
                                 capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out.strip() and eval(out) >= (major, minor):
            return exe
    return None


def run_python_block(code, line_no):
    first = code.lstrip().split("\n", 1)[0]
    if first.startswith("# skip-test"):
        return "skip", "marked skip-test"
    m = REQUIRES.match(first)
    if m:
        need = (int(m.group(1)), int(m.group(2)))
        if sys.version_info < need:
            exe = find_python(*need)
            if exe is None:
                return "skip", f"needs Python {need[0]}.{need[1]}, none installed"
            done = subprocess.run([exe, "-B", "-c", code], capture_output=True, text=True, timeout=120)
            if done.returncode != 0:
                return "fail", done.stderr.strip()[-2000:]
            return "pass", f"ran with {os.path.basename(exe)}"
    namespace = {"__name__": "__chapter_example__"}
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(compile(code, f"<block at line {line_no}>", "exec"), namespace)
    except BaseException as err:          # report SystemExit and KeyboardInterrupt too
        return "fail", f"{type(err).__name__}: {err}"
    return "pass", ""


def run_pycon_block(code, line_no, name):
    parser = doctest.DocTestParser()
    test = parser.get_doctest(code, {"__name__": "__chapter_example__"}, f"{name}:{line_no}", name, line_no)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    report = io.StringIO()
    runner.run(test, out=report.write)
    result = runner.summarize(verbose=False)
    if result.failed:
        return "fail", report.getvalue()[-3000:]
    return "pass", f"{result.attempted} statements"


def main(paths):
    sys.dont_write_bytecode = True
    totals = {"pass": 0, "fail": 0, "skip": 0}
    for chapter in paths:
        with open(chapter, encoding="utf8") as fh:
            text = fh.read()
        name = os.path.basename(chapter)
        for match in FENCE.finditer(text):
            kind, code = match.group(1), textwrap.dedent(match.group(2))
            line_no = text.count("\n", 0, match.start()) + 1
            if kind == "pycon":
                status, detail = run_pycon_block(code, line_no, name)
            else:
                status, detail = run_python_block(code, line_no)
            totals[status] += 1
            if status != "pass":
                print(f"{status.upper()}  {name}:{line_no}  {detail}")
    print(f"{totals['pass']} passed, {totals['fail']} failed, {totals['skip']} skipped")
    return 1 if totals["fail"] else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
