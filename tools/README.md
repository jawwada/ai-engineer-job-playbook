# Tools: building, checking and maintaining the book

Four standard-library Python scripts and one stylesheet keep the book consistent. None of them is needed to read the book; all of them are needed to change it. Run them from the repository root.

| Script | What it does | When to run it |
|---|---|---|
| `build_book.py` | Concatenates every chapter into one Markdown file, optionally rendered to HTML with pandoc | Before publishing a snapshot, or to read the book as one document |
| `update_readme_contents.py` | Rewrites the `## Contents` section of `README.md` from the chapters' H1 titles | After adding, renaming or renumbering a chapter |
| `escape_dollars.py` | Escapes `$` in prose so GitHub does not render prices as LaTeX | After editing any chapter that mentions money |
| `run_chapter_examples.py` | Executes every Python code block in a chapter so the book's examples cannot drift from the truth | After editing a chapter with runnable code (49a, 49b) |
| `book.css` | The stylesheet for the HTML build | Used by `build_book.py --html` |

The labs carry a fifth kind of check, `check_chapter_sync.py` in `labs/coding-patterns`, `labs/algorithm-frameworks` and `labs/cs-essentials`, which verifies that every function shown in a chapter is byte-identical to the tested one in the lab. See the labs' READMEs.

## Intuition: why a book needs a build

A book with ninety-plus chapters, prices that change monthly and code that must run is a software project with a Markdown front end. Three things go wrong without tooling: the table of contents drifts from the files (a renamed chapter is still listed under its old title), GitHub's Markdown renderer turns a sentence with two dollar signs into an equation, and a code example that was correct in March stops running in October because a library or a Python version changed. Each script below removes one of those failure modes mechanically, so a contributor's pull request can be checked rather than trusted.

## `build_book.py`: one file from many

```bash
python3 tools/build_book.py                     # writes dist/ai-engineer-job-playbook.md
python3 tools/build_book.py --html              # also writes dist/ai-engineer-job-playbook.html (needs pandoc)
python3 tools/build_book.py --no-reference      # leave out Part 6, the study library
python3 tools/build_book.py --out /tmp/book.md  # choose the output path
```

**How it works.** The script holds the part order in a `PARTS` list (Part 7 and Part 8 are placed before Part 6 so the reference library closes the book). For each part folder it takes every `.md` file in file-name order, which is why chapter files are numbered and why `40b` sorts after `40` and before `41`. Part 6 is special: its `README.md` comes first, then each study-library subfolder in the `REF_ORDER` list. The chunks are joined under a YAML metadata block (title and subtitle) so pandoc can render a title page; with `--html`, pandoc is called with a table of contents to depth 1 (one entry per part and chapter), embedded resources (one self-contained HTML file), and `book.css` if present.

**What to know when editing.** Adding a part means adding a tuple to `PARTS` here *and* in `update_readme_contents.py`; the two lists are kept separately because their titles use different dashes (plain hyphen for pandoc, em dash for the README). A chapter is included only if its file name ends in `.md`; a draft you do not want built can sit in the folder with another extension. The script never edits chapter files.

**Example.**

```
$ python3 tools/build_book.py
wrote /Users/.../dist/ai-engineer-job-playbook.md
$ grep -c '^# Part ' dist/ai-engineer-job-playbook.md
10
```

Ten matches: the nine part titles the script inserts (Parts 0 to 8, with Part 6 last) plus the H1 of Part 6's own README, which the script includes as that part's first file.

The `dist/` folder is ignored by git; the built file is a product, not a source.

## `update_readme_contents.py`: the table of contents

```bash
python3 tools/update_readme_contents.py
# README contents rewritten: 105 entries
```

**How it works.** It finds the line `## Contents` in `README.md` and the next `## ` heading, and replaces everything between them. For each part it prints a bold part title and one bullet per chapter, taking the link text from the chapter's first `# ` line, so a chapter's H1 is its canonical title everywhere. Part 6 is summarised in one line (`PART6_LINE`) rather than listed chapter by chapter. Two extras follow the parts: the labs line and the glossary line, both held in the `EXTRAS` list.

**What to know when editing.** If you rename a chapter, change its H1 and run this script; do not edit the README's list by hand, the next run would overwrite it. If you add a lab, add it to `EXTRAS` here. The script prints the number of chapter entries so a drop in the count after a run is a sign that a file lost its H1 or its `.md` extension.

## `escape_dollars.py`: prices are not mathematics

```bash
python3 tools/escape_dollars.py           # escape in place, print the files changed
python3 tools/escape_dollars.py --check   # exit 1 if anything would change (for CI)
```

**Intuition.** GitHub renders `$5 (or $9)` as inline LaTeX because it sees text between two dollar signs. A chapter about token prices has dozens of them on one line. A backslash before the dollar sign (`\$`) renders as a plain dollar on GitHub and in pandoc, so the rule is simply: every `$` in prose is escaped, and every `$` in code is not.

**How it works.** The script walks `book/`, `README.md`, `GLOSSARY.md` and every `.md` under `labs/`, and skips `kit/` entirely because skill files use `$ARGUMENTS` and similar variables. For each file it tracks fenced code blocks (any run of three or more backticks or tildes opens a fence; the same marker closes it) and leaves their contents alone. Outside fences, `escape_prose` walks each line character by character, skips inline code spans by matching backtick runs of equal length, and inserts a backslash before any `$` that is not already escaped (it counts the preceding backslashes so `\\$` is left as is). Only lines that change are rewritten, and the file is written only when at least one line changed, so a clean run touches nothing and prints `total lines changed: 0`.

**What it does not do.** It does not unescape, so a `\$` inside a code span that was escaped by mistake stays escaped; fix those by hand. It does not know about HTML comments or front matter.

**Example.**

```
$ python3 tools/escape_dollars.py --check
book/part-2-landscape/31-finops-and-token-economics.md: 2 line(s) need escaping
total lines to change: 2
$ python3 tools/escape_dollars.py
book/part-2-landscape/31-finops-and-token-economics.md: 2 line(s) escaped
total lines changed: 2
```

## `run_chapter_examples.py`: the book's code must run

```bash
python3 tools/run_chapter_examples.py book/part-4-engineering-and-roles/49a-python-fundamentals-and-advanced-idioms.md
# 188 passed, 0 failed, 0 skipped
```

**Intuition.** A chapter that teaches Python idioms is only trustworthy if every example runs today, on the Python the reader has. Instead of copying examples into a test file, where they would drift from the prose, this script executes them straight from the Markdown.

**How it works.** A regular expression finds every fenced block whose language is `python` or `pycon`. A `pycon` block is treated as a doctest session: lines starting with `>>>` or `...` are run and the printed output must match what the chapter shows (with `ELLIPSIS` and `NORMALIZE_WHITESPACE` allowed, so `...` can stand for long output). A `python` block is compiled and executed in a fresh namespace with stdout captured; it should state its results with `assert` so that a wrong result is a failure rather than a silently different print. Two first-line markers change the behaviour: `# skip-test` shows a block for reading only (a fragment, or code that needs a network or a server), and `# requires: 3.14` runs the block in a subprocess with an interpreter of at least that version, found by `find_python` among `python3.14`, `python3.15` and so on, on the path or under `~/.local/bin`; if none is installed the block is skipped with a note rather than failed. Blocks in any other language are ignored. The exit code is 1 if any block failed, so the script can gate a pull request.

**Writing a block that passes.** State results with `assert`, not `print`; keep each block self-contained (a fresh namespace means a block cannot use a name defined in an earlier block); mark fragments with `# skip-test`; use `pycon` when the point is the printed output.

**Example of a failure report.**

```
FAIL  49a-python-fundamentals-and-advanced-idioms.md:1432  AssertionError:
1 passed, 1 failed, 0 skipped
```

The line number is the line of the opening fence in the chapter, so the failing example is one search away.

## `book.css`

A short stylesheet for the HTML build: a serif body at a readable measure, sans-serif headings, a dark-mode palette through `prefers-color-scheme`, bordered tables that scroll horizontally on narrow screens, and a boxed table of contents. Edit it freely; it has no effect on the Markdown.

## A contributor's checklist

1. Edit or add chapters in `book/part-*/`. A new chapter needs a numbered file name and an H1 starting with the chapter number.
2. If the chapter has runnable Python, run `run_chapter_examples.py` on it.
3. If it mentions prices, run `escape_dollars.py`.
4. If you added or renamed a chapter, run `update_readme_contents.py`.
5. If a lab mirrors the chapter's code, run that lab's `check_chapter_sync.py` and its tests.
6. Run `build_book.py` once to make sure the whole book still assembles.
7. Review with the adversarial reviewer in `kit/agents/adversarial-reviewer.md`, which weaves its corrections into the prose.
