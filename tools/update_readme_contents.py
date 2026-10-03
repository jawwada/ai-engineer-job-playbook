#!/usr/bin/env python3
"""Regenerate the "## Contents" section of README.md from the chapter files' H1 titles.

Usage:  python3 tools/update_readme_contents.py

The section between "## Contents" and the next "## " heading is rewritten. Chapter order is the
file-name order inside each part folder (the same order tools/build_book.py uses).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
README = os.path.join(ROOT, "README.md")

PARTS = [
    ("part-0-introduction", "Part 0 — Introduction"),
    ("part-1-the-agent", "Part 1 — The Claude Code job-search agent"),
    ("part-2-landscape", "Part 2 — The AI engineering landscape"),
    ("part-3-interviews", "Part 3 — Interviews"),
    ("part-4-engineering-and-roles", "Part 4 — Engineering, roles and operating agents"),
    ("part-5-your-resume", "Part 5 — The resume, glossary and portfolio"),
    ("part-6-reference-guides", "Part 6 — Reference guides (study library)"),
    ("part-7-building-and-earning", "Part 7 — Building and earning"),
    ("part-8-advanced-questions", "Part 8 — Advanced interview questions, answered in depth"),
]
PART6_LINE = ("- [Study library index](book/part-6-reference-guides/README.md) — agentic AI, retrieval, LLMs, "
              "machine learning, clouds, Python and backend, industries, interview practice")
EXTRAS = [
    "**Labs:** [Coding-interview patterns](labs/coding-patterns/README.md) — tested templates for the twenty "
    "LeetCode patterns and the families beyond them, checked against brute force (chapter 39d); "
    "[FinOps analyst lab](labs/finops-analyst/README.md) — synthetic multi-cloud billing data with "
    "forecasting, variance, anomaly, allocation, commitment, savings and executive-summary exercises "
    "(chapter 47g). Both are standard-library Python.",
    "**Glossary:** [GLOSSARY.md](GLOSSARY.md)",
]


def title_of(path):
    with open(path, encoding="utf8") as fh:
        for line in fh:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.basename(path)


def contents_lines():
    out = []
    for folder, part_title in PARTS:
        d = os.path.join(BOOK, folder)
        if not os.path.isdir(d):
            continue
        out += [f"**{part_title}**", ""]
        if folder == "part-6-reference-guides":
            out.append(PART6_LINE)
        else:
            for f in sorted(os.listdir(d)):
                if f.endswith(".md"):
                    rel = f"book/{folder}/{f}"
                    out.append(f"- [{title_of(os.path.join(d, f))}]({rel})")
        out.append("")
    for extra in EXTRAS:
        out += [extra, ""]
    return out


def main():
    lines = open(README, encoding="utf8").read().split("\n")
    start = lines.index("## Contents")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    new = lines[: start + 1] + [""] + contents_lines() + lines[end:]
    with open(README, "w", encoding="utf8") as fh:
        fh.write("\n".join(new))
    n = sum(1 for l in contents_lines() if l.startswith("- ["))
    print(f"README contents rewritten: {n} entries")


if __name__ == "__main__":
    main()
