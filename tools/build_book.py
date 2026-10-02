#!/usr/bin/env python3
"""Combine every chapter of the book into one Markdown file (and optionally HTML via pandoc).

Usage:  python3 tools/build_book.py [--out dist/ai-engineer-job-playbook.md] [--html] [--no-reference]
"""
import argparse, os, re, subprocess, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
PARTS = [
    ("part-0-introduction", "Part 0 - Introduction"),
    ("part-1-the-agent", "Part 1 - The Claude Code job-search agent"),
    ("part-2-landscape", "Part 2 - The AI engineering landscape"),
    ("part-3-interviews", "Part 3 - Interviews"),
    ("part-4-engineering-and-roles", "Part 4 - Engineering, roles and operating agents"),
    ("part-5-your-resume", "Part 5 - The resume, glossary and portfolio"),
    ("part-7-building-and-earning", "Part 7 - Building and earning"),
    ("part-6-reference-guides", "Part 6 - Reference guides (study library)"),
]
REF_ORDER = ["agentic-ai", "retrieval", "llms", "machine-learning", "clouds", "python-backend", "industries", "interview-practice"]

def chapter_files(part_dir):
    if os.path.basename(part_dir) == "part-6-reference-guides":
        files = [os.path.join(part_dir, "README.md")]
        for sub in REF_ORDER:
            d = os.path.join(part_dir, sub)
            if os.path.isdir(d):
                files += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".md")]
        return [f for f in files if os.path.exists(f)]
    return [os.path.join(part_dir, f) for f in sorted(os.listdir(part_dir)) if f.endswith(".md")]

def title_of(path):
    with open(path, encoding="utf8") as fh:
        for line in fh:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.basename(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist", "ai-engineer-job-playbook.md"))
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--no-reference", action="store_true", help="leave out Part 6")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    chunks = ["---\ntitle: AI Engineer Job Playbook\nsubtitle: Agents, interviews, engineering and building - October 2026 snapshot\n---\n"]
    for folder, part_title in PARTS:
        if a.no_reference and folder == "part-6-reference-guides":
            continue
        d = os.path.join(BOOK, folder)
        if not os.path.isdir(d):
            continue
        chunks.append(f"\n\n# {part_title}\n")
        for f in chapter_files(d):
            text = open(f, encoding="utf8").read().strip()
            chunks.append("\n\n" + text + "\n")
    glossary = os.path.join(ROOT, "GLOSSARY.md")
    if os.path.exists(glossary):
        chunks.append("\n\n" + open(glossary, encoding="utf8").read().strip() + "\n")
    with open(a.out, "w", encoding="utf8") as fh:
        fh.write("".join(chunks))
    print("wrote", a.out)
    if a.html:
        if not shutil.which("pandoc"):
            raise SystemExit("pandoc not found")
        html = os.path.splitext(a.out)[0] + ".html"
        css = os.path.join(ROOT, "tools", "book.css")
        cmd = ["pandoc", a.out, "-o", html, "--standalone", "--toc", "--toc-depth=1", "--embed-resources",
               "--metadata", "lang=en", "-f", "gfm+yaml_metadata_block"]
        if os.path.exists(css):
            cmd += ["--css", css]
        subprocess.run(cmd, check=True)
        print("wrote", html)

if __name__ == "__main__":
    main()
