#!/usr/bin/env python3
"""Check that every function and class from this lab that chapter 49b prints is identical to the tested code.

A top-level def or class in a ```python block of the chapter is compared with the object of the same name in
jwt_hs256.py, pkce.py or tiny_lsm.py. Functions that exist only in the chapter (toy RSA, the cookie and
session examples, and so on) are skipped; give them names the lab modules do not use.

Usage:  python3 -B check_chapter_sync.py      (exit code 1 on any difference)
"""
import inspect
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
CHAPTER = os.path.join(HERE, "..", "..", "book", "part-4-engineering-and-roles",
                       "49b-computer-science-essentials-security-protocols-linux-and-storage.md")
sys.path.insert(0, HERE)
import jwt_hs256  # noqa: E402
import pkce  # noqa: E402
import tiny_lsm  # noqa: E402

MODULES = (jwt_hs256, pkce, tiny_lsm)


def top_level_objects(code):
    """Split a code block into top-level def/class chunks (with decorators), keyed by name."""
    chunks, name, lines, pending = {}, None, [], []
    for line in code.split("\n"):
        header = re.match(r"(def|class) (\w+)", line)
        if line.startswith("@"):
            pending.append(line)
        elif header:
            if name:
                chunks[name] = "\n".join(lines).rstrip()
            name, lines, pending = header.group(2), pending + [line], []
        elif line and not line[0].isspace() and not line.startswith((")", "]", "}")):
            if name:
                chunks[name] = "\n".join(lines).rstrip()
            name, lines = None, []
        elif name:
            lines.append(line)
    if name:
        chunks[name] = "\n".join(lines).rstrip()
    return chunks


def main():
    text = open(CHAPTER, encoding="utf8").read()
    shown = problems = 0
    for block in re.findall(r"```python\n(.*?)```", text, flags=re.S):
        for name, source in top_level_objects(block).items():
            owners = [m for m in MODULES if inspect.isfunction(getattr(m, name, None))
                      or inspect.isclass(getattr(m, name, None))]
            if not owners:
                continue
            shown += 1
            if all(inspect.getsource(getattr(m, name)).rstrip() != source for m in owners):
                print(f"differs from {owners[0].__name__}.py: {name}")
                problems += 1
    print(f"{shown} lab functions and classes shown in chapter 49b, {problems} difference(s)")
    sys.exit(1 if problems or not shown else 0)


if __name__ == "__main__":
    main()
