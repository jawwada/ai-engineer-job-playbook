# Algorithm frameworks lab

Tested Python for chapters 39e, 39f and 39g, which follow the topic map of [labuladong Algo Notes](https://labuladong.online/en/algo/home/) and extend it: data structures built from arrays and linked nodes and the ten sorting algorithms (39e); the classic templates, binary-tree thinking, data-structure design and graph algorithms (39f); backtracking, BFS, dynamic programming, greedy algorithms and math techniques (39g). The explanations, code and tests are this book's own. Chapter 39d's lab, [`labs/coding-patterns`](../coding-patterns/README.md), holds the twenty basic interview patterns these chapters build on; nothing is imported from it, so each file here runs on its own.

Standard library only, Python 3.10 or newer (tested on 3.10 to 3.14).

```bash
cd labs/algorithm-frameworks
python3 -B test_ds_basics.py        # 39e: 25 groups, about 10 s
python3 -B test_frameworks_1.py     # 39f: 23 groups, about 2 s
python3 -B test_frameworks_2.py     # 39g: 16 groups, about 10 s
python3 -B check_chapter_sync.py    # every function and class printed in 39e, 39f and 39g matches the tested code
```

## Files

| File | Chapter | What it holds |
|---|---|---|
| `ds_basics.py` | 39e | A dynamic array, a doubly linked list with sentinels, a ring buffer, a skip list, a bitset, linked stacks and queues, hash maps with separate chaining and with linear probing (tombstone and backward-shift deletion), a model of CPython's compact dict, LinkedHashMap, ArrayHashMap, a Bloom filter, tree traversals, an AVL tree, a trie, a binary heap, a segment tree, Huffman coding, graph representations and traversals, Euler checks, union-find, and the ten sorting algorithms |
| `test_ds_basics.py` | 39e | Random operation sequences compared with `list`, `dict`, `set`, `deque`, `heapq` and `sorted`; cost checks (copies per append, heapify comparisons, Shell sort growth, the Bloom filter's measured false-positive rate against the formula) |
| `frameworks_1.py` | 39f | Linked-list and array two-pointer techniques, nSum, prefix sums and difference arrays, the general sliding-window template and Rabin–Karp, binary search on bounds and on monotone predicates, weighted random pick, monotonic stacks and queues, tree construction and serialization, BST operations, every lowest-common-ancestor variant, merge-sort counting, quickselect, LFU and random-access sets, the exam room, a calculator, consistent hashing, three segment trees, trie applications, bipartite checks, cycle detection, topological sort, Dijkstra variants, A*, Kruskal and Prim, Hierholzer and Floyd–Warshall |
| `test_frameworks_1.py` | 39f | Fixed examples plus 200 to 600 seeded random cases per group against brute force; it also reproduces the numbers the chapter quotes (keys moved by consistent hashing, cells expanded by A*) |
| `frameworks_2.py` | 39g | The backtracking framework, all nine permutation/combination/subset forms, ball-and-box enumeration, island variants, BFS and bidirectional BFS, the DP framework and its classic problems (LIS, envelopes, word break, edit distance with reconstruction, LCS family, palindromes, knapsacks, dungeon, freedom trail, regex, egg drop, burst balloons, stone games), house robber and the stock state machine, greedy algorithms, math tricks, shuffles and reservoir sampling, ugly numbers and classic interview problems |
| `test_frameworks_2.py` | 39g | Brute-force references (`itertools`, exhaustive search on small instances), exact enumeration of every random draw for the sampling functions, and deterministic node counts for the search comparisons the chapter reports |
| `check_chapter_sync.py` | all | Fails if a function, class, import or constant printed in a chapter differs from this folder's code |

## How to practice with it

1. Read a section of 39e, 39f or 39g, then close the book.
2. Delete the body of one function (keep the signature and docstring) and write it from memory.
3. Run the matching test file. The randomized comparisons catch the off-by-one and empty-input bugs that two hand-picked examples miss.
4. Keep your version only if it passes; otherwise compare it with the original and write the difference in your error log.

Conventions: functions that LeetCode specifies as in-place mutate their input, and the tests pass copies. Indices are 0-based unless a docstring says otherwise. Functions that draw random numbers take an `rng` argument so the tests can pass a seeded `random.Random`. Problems marked † in the chapters need LeetCode Premium.
