#!/usr/bin/env python3
"""Check that every function and class shown in chapter 39d is identical to the tested one in patterns.py.

Module-level lines shown before the first def/class of a code block (imports, constants) must also
appear verbatim in patterns.py.

Usage:  python3 check_chapter_sync.py      (exit code 1 on any difference)
"""
import inspect
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAPTER = os.path.join(HERE, "..", "..", "book", "part-3-interviews", "39d-coding-interview-patterns.md")
sys.path.insert(0, HERE)
import patterns  # noqa: E402


def top_level_objects(code):
    """Split a code block into top-level def/class chunks keyed by name, plus the lines before the first."""
    chunks, name, lines, prelude = {}, None, [], []
    for line in code.split("\n"):
        m = re.match(r"(def|class) (\w+)", line)
        if m:
            if name:
                chunks[name] = "\n".join(lines).rstrip()
            name, lines = m.group(2), [line]
        elif name:
            lines.append(line)
        elif line.strip():
            prelude.append(line)
    if name:
        chunks[name] = "\n".join(lines).rstrip()
    return chunks, prelude


def main():
    text = open(CHAPTER, encoding="utf8").read()
    module_lines = set(inspect.getsource(patterns).split("\n"))
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.S)
    shown, problems = 0, 0
    for block in blocks:
        chunks, prelude = top_level_objects(block)
        for line in prelude:
            shown += 1
            if line not in module_lines:
                print(f"module-level line not in patterns.py: {line}")
                problems += 1
        for name, source in chunks.items():
            shown += 1
            obj = getattr(patterns, name, None)
            if obj is None:
                print(f"missing in patterns.py: {name}")
                problems += 1
            elif inspect.getsource(obj).rstrip() != source:
                print(f"differs from patterns.py: {name}")
                problems += 1
    print(f"{shown} objects and lines checked, {problems} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
