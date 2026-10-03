#!/usr/bin/env python3
r"""Escape dollar signs in Markdown prose so GitHub does not render prices as math.

GitHub treats text between two dollar signs on one line as inline LaTeX ("costs $5 (or $9)..."),
which garbles paragraphs full of prices. A backslash-escaped dollar (\$) renders as a plain "$"
on GitHub and in pandoc. This script escapes every unescaped "$" outside fenced code blocks and
inline code spans, in the book, README.md, GLOSSARY.md and labs/*/README.md. It never touches kit/
(skills use $ARGUMENTS and similar variables).

Usage:  python3 tools/escape_dollars.py [--check]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def targets():
    for base, _dirs, files in os.walk(os.path.join(ROOT, "book")):
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(base, f)
    for f in ("README.md", "GLOSSARY.md"):
        yield os.path.join(ROOT, f)
    labs = os.path.join(ROOT, "labs")
    if os.path.isdir(labs):
        for base, _dirs, files in os.walk(labs):
            for f in files:
                if f.endswith(".md"):
                    yield os.path.join(base, f)


def escape_prose(line):
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "`":
            j = i
            while j < n and line[j] == "`":
                j += 1
            run = j - i
            # find a closing run of exactly the same length
            k = j
            close = -1
            while k < n:
                if line[k] == "`":
                    m = k
                    while m < n and line[m] == "`":
                        m += 1
                    if m - k == run:
                        close = m
                        break
                    k = m
                else:
                    k += 1
            if close == -1:
                out.append(line[i:j])
                i = j
            else:
                out.append(line[i:close])
                i = close
            continue
        if c == "$":
            # count preceding backslashes in the output so far
            prev = "".join(out)
            bs = len(prev) - len(prev.rstrip("\\"))
            out.append("$" if bs % 2 == 1 else "\\$")
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def process(path):
    lines = open(path, encoding="utf8").read().split("\n")
    fence = None
    changed = 0
    for idx, line in enumerate(lines):
        m = FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)
            continue
        if fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and line.strip() == m.group(1):
                fence = None
            continue
        if "$" in line:
            new = escape_prose(line)
            if new != line:
                lines[idx] = new
                changed += 1
    return lines, changed


def main():
    check = "--check" in sys.argv
    total = 0
    for path in targets():
        lines, changed = process(path)
        if changed:
            total += changed
            rel = os.path.relpath(path, ROOT)
            print(f"{rel}: {changed} line(s)" + (" need escaping" if check else " escaped"))
            if not check:
                with open(path, "w", encoding="utf8") as fh:
                    fh.write("\n".join(lines))
    print(f"total lines {'to change' if check else 'changed'}: {total}")
    if check and total:
        sys.exit(1)


if __name__ == "__main__":
    main()
