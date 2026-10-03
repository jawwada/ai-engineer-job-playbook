# Coding-interview patterns lab

Tested Python templates for the twenty coding-interview patterns (the list taught in Design Gurus' *Grokking the Coding Interview*) plus the families that list leaves out — prefix sums with hash maps, union-find, Dijkstra, tries, greedy, the main dynamic-programming shapes and the design classics. Chapter 39d of the book explains each pattern: how to recognize it, the invariant that makes it correct, its complexity, a LeetCode practice set, pitfalls and follow-ups.

Standard library only, Python 3.10 or newer.

```bash
cd labs/coding-patterns
python3 test_patterns.py        # one line per pattern group; runs in a few seconds
python3 check_chapter_sync.py   # confirms the code printed in chapter 39d matches patterns.py
```

## Files

| File | What it holds |
|---|---|
| `patterns.py` | One section per pattern: a template and the classic problems it solves, each with its LeetCode number in the docstring |
| `test_patterns.py` | Fixed examples from the problem statements plus, for nearly every function, randomized checks against a brute-force reference (hundreds of random inputs per pattern), including the thread-ordering and producer–consumer tests and a time guard on the Sudoku solver |
| `check_chapter_sync.py` | Fails if a function, class, import or constant shown in chapter 39d differs from the tested version here |

## How to practice with it

1. Pick a pattern, read its section in chapter 39d, and close the book.
2. Delete the body of one function in `patterns.py` (keep the signature and docstring) and write it from memory.
3. Run `python3 test_patterns.py`. The randomized checks catch the off-by-one and empty-input bugs that two hand-picked examples miss.
4. Restore the file with your version only if it passes; otherwise compare with the original and write the difference in your error log.

Conventions: functions that LeetCode specifies as in-place mutate their input, as an interview answer would; the tests pass copies. Indices are 0-based unless a docstring says otherwise. Problems marked † in the chapter need LeetCode Premium.
