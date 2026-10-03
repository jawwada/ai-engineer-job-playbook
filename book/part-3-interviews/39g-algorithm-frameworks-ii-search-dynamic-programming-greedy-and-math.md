# 39g. Algorithm frameworks II: backtracking, BFS, dynamic programming, greedy and math techniques

> **What you need to be able to say:** the decision tree behind a brute-force search and what it costs (nodes times work per node); the backtracking skeleton and which of the nine permutation, combination and subset forms a problem is; why BFS finds shortest paths and when to search from both ends; how a search becomes a dynamic program — state, definition, choices, base case, order — and how to cut its memory; why a greedy choice is safe, by an exchange argument, or why it is not, by a counterexample; and the few number-theory and probability facts that replace a loop with a formula.

## 39g.1 Brute-force search is enumeration on a tree

### 39g.1.1 Where this chapter comes from and how to use it

This chapter follows the topic map of labuladong's algorithm notes (https://labuladong.online/en/algo/home/) — their parts on brute-force search, on dynamic programming and greedy algorithms, and on other common techniques — and extends it. The order of topics and many of the problems come from that map; the explanations, proofs, examples and code are this book's own, with more weight on why each step is correct, what it costs and what the interviewer asks next. Chapters 39e and 39f cover the earlier parts of the same notes, and section 39f.1.4 introduces the split this chapter builds on: traversing a decision tree becomes backtracking, decomposing into shared subproblems becomes dynamic programming.

Where chapter 39d already has tested code (subsets, combination sum, N-Queens, Sudoku, islands, knapsack, coin change, LIS, edit distance, house robber, intervals, rain water), this chapter gives the framework behind it and the variants 39d lacks, and points to "39d.x" instead of repeating it.

Every function shown is copied verbatim from `labs/algorithm-frameworks/frameworks_2.py` (`check_chapter_sync.py 39g` enforces it), and `test_frameworks_2.py` compares nearly every function with a brute-force reference (itertools, exhaustive search, or a replay of every possible random draw) in about ten seconds. The code assumes these imports and the four grid directions:

```python
import heapq
import math
import random
from bisect import bisect_left
from collections import Counter, defaultdict, deque
from fractions import Fraction
from functools import cache

DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
```

### 39g.1.2 The decision tree

Any exhaustive search can be drawn as a tree. The root is the empty partial solution; each edge is one decision (put this value next, put this number in that bucket, slide this tile); a node is the sequence of decisions on its path; a leaf is a complete candidate. For the permutations of `[1, 2, 3]`:

```text
                       []
          /            |            \
       [1]            [2]            [3]
      /    \         /    \         /    \
  [1,2]  [1,3]   [2,1]  [2,3]   [3,1]  [3,2]
    |      |       |      |       |      |
 [1,2,3][1,3,2] [2,1,3][2,3,1] [3,1,2][3,2,1]
```

A search is correct when every valid answer appears in the tree and no answer appears twice. Most bugs in this chapter's problems break one of the two: a loop that starts at 0 instead of the current index produces the set {1, 2} twice, as [1, 2] and [2, 1]; a visited set that is never cleared misses paths that reuse a node.

### 39g.1.3 Backtracking and DFS: work on the edges or at the nodes

The same tree can be walked with the bookkeeping in two places. In the **edge style**, the choice is made and undone inside the loop, around the recursive call, so the root (the empty choice) is never on the path; that is the backtracking skeleton of 39g.2. In the **node style**, the node is added on entry and removed on exit, so the root is on the path. All Paths From Source to Target (797) wants the start node in every answer, so it is written in the node style:

```python
def all_paths_source_target(graph):
    """All paths from node 0 to node n - 1 in a DAG (LC 797): the path changes as nodes are entered and left."""
    target = len(graph) - 1
    out, path = [], []

    def visit(node):
        path.append(node)                      # entering the node: work happens at the node
        if node == target:
            out.append(path[:])
        else:
            for nxt in graph[node]:
                visit(nxt)
        path.pop()                             # leaving the node

    visit(0)
    return out
```

There is no visited set: the graph is acyclic, so no path can loop, and the same node must be allowed on many paths. That is the deeper difference between the two families:

| | Backtracking | Graph DFS |
|---|---|---|
| Enumerates | paths (partial solutions) | vertices |
| Marks on the way down | undone on the way back, so another path may use the vertex | permanent, so each vertex is processed once |
| Cost | number of paths, often exponential | O(V + E) |
| Examples | permutations, N-Queens | islands (39g.5), reachability, cycle detection |

Word Search (79, 39d.17) sits between them: it restores a cell when it backs out, because other paths may use it, but marks the cell while the current path holds it. A permanent visited set in 797 silently loses paths; no visited set in a search on a cyclic graph never terminates.

The validity check can likewise sit at the node (each call checks its own state, as `sink_island` does in 39g.5) or on the edge (the loop skips a bad choice, as `permute` does). And a backtracking function returns nothing when it collects every answer, or a Boolean when one answer is enough, so the first `True` stops the search.

### 39g.1.4 What a search costs, and four kinds of pruning

A search costs the number of nodes it visits times the work per node, plus the cost of copying out answers. For permutations, depth j holds the n!/(n − j)! ordered selections of j items, so the tree has Σ n!/j! nodes over j = 0..n — exactly ⌊e · n!⌋ for n ≥ 1, about 2.72 times the number of leaves:

```python
def permutation_tree_size(n):
    """Nodes visited by used[]-backtracking over the permutations of n items, root included."""
    used = [False] * n

    def visit():
        nodes = 1
        for i in range(n):
            if not used[i]:
                used[i] = True
                nodes += visit()
                used[i] = False
        return nodes

    return visit()
```

| Tree | Answers | Nodes | Total cost |
|---|---|---|---|
| Subsets (every node is an answer) | 2ⁿ | 2ⁿ | O(n · 2ⁿ) with copying |
| Combinations of size k, with the start-index bound of 39g.3.2 | C(n, k) | C(n + 1, k), at most (k + 1) · C(n, k) | O(k · C(n, k)) |
| Permutations | n! | ⌊e · n!⌋ | O(n · n!) |
| n items, each into one of k ≥ 2 buckets | kⁿ | (kⁿ⁺¹ − 1)/(k − 1), less than 2 · kⁿ | O(k · kⁿ) before pruning |

**Pruning** cuts subtrees that cannot contain an answer. It comes in four kinds:

1. **Feasibility.** A partial solution that already breaks a constraint has no valid leaf below it. Placing queens row by row with O(1) attack checks visits 2,057 nodes for n = 8, against 109,601 in the permutation tree of the columns and 16.8 million leaves if each row could take any column (the counts are in the tests).
2. **Bounds.** When the partial cost already rules out the target or the best answer so far, stop. With sorted candidates, one that exceeds the remaining sum ends the loop (`break`, not `continue`).
3. **Symmetry.** When two children lead to identical subtrees, explore one: equal values in a sorted input (39g.3), buckets with equal sums (39g.4).
4. **Ordering.** Branch first on the most constrained decision (the Sudoku cell with the fewest candidates) and try the most promising value first, so the other kinds cut earlier.

A fifth tool is sharing: when different paths reach the same state — the same remaining sum, the same next index — solve the subtree below it once. That is the step to dynamic programming (39g.7).

**Interview line:** *"I'll draw the decision tree first — what a node is, what the choices are, what makes a leaf. The cost is nodes times work per node; I'll prune by feasibility, bounds and symmetry, and if different paths reach the same state I'll memoize, which makes it dynamic programming."*

## 39g.2 The backtracking framework

### 39g.2.1 Path, choices, end condition

A backtracking function stands at one node of the decision tree of 39g.1.2 and works with three things there: the **path**, the edges taken from the root down to this node; the **choices**, the edges that leave it; and the **end condition**, the test that says the node is a leaf. Every such function has the same body:

```python
# illustration: the backtracking skeleton (pseudocode in Python syntax)
def backtrack(path, choices):
    if end_condition(path):
        record(list(path))            # a copy: path keeps changing
        return
    for choice in choices:
        if not valid(path, choice):
            continue                  # feasibility pruning on the edge
        path.append(choice)           # choose: update every piece of shared state
        backtrack(path, next_choices(choices, choice))
        path.pop()                    # unchoose: restore exactly what choose changed
```

The invariant: `backtrack` returns with all shared state exactly as it found it, so every iteration of the loop starts from the same node. 39d.17 gives templates for particular problems; this is what they share.

### 39g.2.2 Permutations with a used array

39d.13 builds permutations breadth-first, by insertion. The backtracking version fills positions left to right and marks the elements on the path:

```python
def permute(nums):
    """All permutations of distinct values (LC 46) with a used[] array: choose, explore, unchoose."""
    out, path = [], []
    used = [False] * len(nums)

    def backtrack():
        if len(path) == len(nums):             # end condition: a leaf of the decision tree
            out.append(path[:])                # copy, because path keeps changing
            return
        for i, x in enumerate(nums):
            if used[i]:
                continue                       # already on the path: not a choice here
            used[i] = True                     # choose
            path.append(x)
            backtrack()                        # explore
            path.pop()                         # unchoose
            used[i] = False

    backtrack()
    return out
```

Leaves come out in lexicographic order of indices, with O(n) memory besides the output. Recording `path` instead of `path[:]` is the classic bug: every answer is the same list, empty at the end. Follow-ups: *k-permutations* stop at `len(path) == k`; *in place by swapping* (swap `nums[start]` with each `nums[i]`, recurse, swap back) needs no `used` array but loses lexicographic order; *next permutation* (31) is a different, O(n) algorithm.

### 39g.2.3 N-Queens: boards, and counting with bitmasks

One queen per row makes rows the levels and columns the choices. A square (r, c) is attacked through its column, its "\" diagonal (r − c constant) or its "/" diagonal (r + c constant), so three Boolean arrays make the check O(1); `solve_n_queens` in the lab returns the boards (51) that way, and 39d.17 counts them (52) with three sets. Three integers do the same a machine word at a time. Bit c of `cols` is set when column c is taken. A queen in column c attacks column c + 1 of the next row along one diagonal and c − 1 along the other, so the diagonal masks shift by one bit per row. The free columns are `full & ~(cols | left | right)`, and `free & -free` isolates the lowest one (in two's complement, `-x` flips every bit above the lowest set bit of `x`):

```python
def total_n_queens_bitmask(n):
    """N-Queens II (LC 52) with bitmasks: one integer per kind of attack, shifted as the rows advance."""
    full = (1 << n) - 1

    def place(cols, left, right):
        if cols == full:                       # n queens placed
            return 1
        count = 0
        free = full & ~(cols | left | right)   # columns of this row that no queen attacks
        while free:
            bit = free & -free                 # lowest free column
            free ^= bit
            count += place(cols | bit, ((left | bit) << 1) & full, (right | bit) >> 1)
        return count

    return place(0, 0, 0)
```

The tree is the same as with sets — 2,057 nodes for n = 8 — but each node costs a few word operations. The tests check the counts 1, 1, 0, 0, 2, 10, 4, 40, 92, 352, 724, 2680 for n = 0..11.

### 39g.2.4 Sudoku: candidates as bits, forced moves, fewest candidates first

39d.17 solves Sudoku with sets, branching on the empty cell with the fewest options. Three changes make it much stronger:

- **Bitmasks.** A 9-bit mask of used digits per row, column and box makes a cell's candidates one expression, `0x1FF & ~(rows[r] | cols[c] | boxes[b])`, and `bit_count()` (Python 3.10+) counts them.
- **Propagation.** After every assignment, place all forced digits before guessing again: a *naked single* (a cell with one candidate) and a *hidden single* (a digit that fits only one cell of a unit). To find hidden singles without counting per digit, fold a unit's candidate masks with `twice |= once & mask; once |= mask`; then `once & ~twice` holds the digits that fit exactly one cell, and a digit in neither `once` nor the unit's placed digits has no cell left — a contradiction.
- **A trail.** Each call records every digit it places, by guess or by propagation, and on failure undoes exactly those.

```python
SUDOKU_UNITS = ([[(r, c) for c in range(9)] for r in range(9)]
                + [[(r, c) for r in range(9)] for c in range(9)]
                + [[(br + i, bc + j) for i in range(3) for j in range(3)]
                   for br in (0, 3, 6) for bc in (0, 3, 6)])


def solve_sudoku_propagate(board, stats=None):
    """Sudoku Solver (LC 37) with bitmask candidates, forced moves (naked and hidden singles) and branching
    on the cell with the fewest candidates. Fills board in place; returns False when there is no solution.
    If stats is a dict, stats["nodes"] counts the search calls."""
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    empty = set()
    for r in range(9):
        for c in range(9):
            if board[r][c] == ".":
                empty.add((r, c))
                continue
            bit = 1 << (int(board[r][c]) - 1)
            b = r // 3 * 3 + c // 3
            if (rows[r] | cols[c] | boxes[b]) & bit:
                return False                   # the givens already clash
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit

    def candidates(r, c):
        return 0x1FF & ~(rows[r] | cols[c] | boxes[r // 3 * 3 + c // 3])

    def assign(r, c, bit, trail):
        rows[r] ^= bit
        cols[c] ^= bit
        boxes[r // 3 * 3 + c // 3] ^= bit
        board[r][c] = str(bit.bit_length())
        empty.discard((r, c))
        trail.append((r, c, bit))

    def undo(trail, stop):
        while len(trail) > stop:
            r, c, bit = trail.pop()
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[r // 3 * 3 + c // 3] ^= bit
            board[r][c] = "."
            empty.add((r, c))

    def propagate(trail):
        """Place every forced digit until none is left; False on a contradiction."""
        progress = True
        while progress:
            progress = False
            for r, c in list(empty):           # naked single: the cell has one candidate
                if (r, c) in empty:
                    mask = candidates(r, c)
                    if mask == 0:
                        return False
                    if (mask & (mask - 1)) == 0:
                        assign(r, c, mask, trail)
                        progress = True
            for unit in SUDOKU_UNITS:          # hidden single: the digit has one possible cell
                once = twice = placed = 0
                for r, c in unit:
                    if (r, c) in empty:
                        mask = candidates(r, c)
                        twice |= once & mask
                        once |= mask
                    else:
                        placed |= 1 << (int(board[r][c]) - 1)
                if (once | placed) != 0x1FF:
                    return False               # some digit has no cell left in this unit
                only = once & ~twice
                while only:
                    bit = only & -only
                    only ^= bit
                    for r, c in unit:
                        if (r, c) in empty and candidates(r, c) & bit:
                            assign(r, c, bit, trail)
                            progress = True
                            break
        return True

    def search():
        if stats is not None:
            stats["nodes"] = stats.get("nodes", 0) + 1
        trail = []
        if propagate(trail):
            if not empty:
                return True
            r, c = min(empty, key=lambda cell: candidates(*cell).bit_count())
            mask = candidates(r, c)
            while mask:
                bit = mask & -mask
                mask ^= bit
                assign(r, c, bit, trail)
                if search():
                    return True
                undo(trail, len(trail) - 1)    # take back this guess only
        undo(trail, 0)                         # take back everything this call placed
        return False

    return search()
```

On the two puzzles in 39d's tests that are built to defeat cell-by-cell search (one is the 17-clue puzzle with an empty top row from Wikipedia's article on Sudoku algorithms), 39d's fewest-options search without propagation, re-implemented in the tests with a counter, makes 13,406 and 17,707 search calls; with propagation the solver makes 1 and 6. The tests also run 80 random puzzles, half of them with one given changed (which leaves many unsolvable), and check every verdict against that complete search. Propagation makes each call dearer, so it pays when the tree is large. Its general form is exact cover — Sudoku picks 81 of 729 placements so that each of 324 constraints is met once — which Knuth's Algorithm X with dancing links solves with the same fewest-options rule.

**Pitfalls.** Undoing the guess but not the digits propagated after it; detecting dead cells but not dead digits; sharing one trail across recursion levels; trusting the givens (the solver rejects givens that already clash).

## 39g.3 Permutations, combinations and subsets in all nine forms

### 39g.3.1 The table and three rules

Two questions classify these enumerations: is the answer a *set* (subsets, combinations) or a *sequence* (permutations)? And are the elements distinct and used once, duplicated in the input and used once, or distinct and reusable?

| Elements | Subsets | Combinations (size k or target sum) | Permutations |
|---|---|---|---|
| Distinct, used once | 78 Subsets | 77 Combinations; 216 Combination Sum III | 46 Permutations |
| With duplicates, used once | 90 Subsets II | 40 Combination Sum II | 47 Permutations II |
| Distinct, reusable | infinite unless bounded; bounded by a sum it is 39 | 39 Combination Sum (target); multisets of size k | sequences of length k with repetition |

Three rules generate all nine:

1. **Order.** Build a set in one canonical order: after choosing index i, only later indices are choices (a `start` index). A sequence may continue with any unused element (a `used` array).
2. **Duplicates.** Sort, so equal values are adjacent, and let only one of a run of equal values branch from the same node.
3. **Reuse.** For sets, recurse with `i` instead of `i + 1`; for sequences, drop the `used` array. (Duplicates plus reuse is distinct plus reuse after removing the duplicates.)

### 39g.3.2 Distinct elements, each used once

```python
def subsets_backtrack(nums):
    """All subsets (LC 78) by backtracking: every node of the tree is an answer."""
    out, path = [], []

    def backtrack(start):
        out.append(path[:])                    # record on entering the node
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1)                   # i + 1: only later elements, so no set appears twice
            path.pop()

    backtrack(0)
    return out


def combine(n, k):
    """All k-element combinations of 1..n (LC 77): the subset tree cut off at depth k."""
    out, path = [], []

    def backtrack(start):
        if len(path) == k:
            out.append(path[:])
            return
        for x in range(start, n - (k - len(path)) + 2):   # leave enough numbers for the rest
            path.append(x)
            backtrack(x + 1)
            path.pop()

    backtrack(1)
    return out


def combination_sum3(k, n):
    """k distinct digits 1..9 that sum to n (LC 216): combinations with two end conditions."""
    out, path = [], []

    def backtrack(start, remaining):
        if len(path) == k:
            if remaining == 0:
                out.append(path[:])
            return
        for d in range(start, 10):
            if d > remaining:
                break                          # digits only grow from here
            path.append(d)
            backtrack(d + 1, remaining - d)
            path.pop()

    backtrack(1, n)
    return out
```

Subsets record every node on entry; combinations record only at depth k. The loop bound in `combine` is a feasibility check: with k − len(path) numbers still needed, the next one can be at most n − (k − len(path)) + 1, or too few remain after it. In `combination_sum3` the digits increase along the path, so a digit larger than the remaining sum ends the loop.

### 39g.3.3 Duplicates in the input: sort and skip

```python
def subsets_with_dup_backtrack(nums):
    """Distinct subsets of a multiset (LC 90): sort; at each depth only the first of equal values branches."""
    nums = sorted(nums)
    out, path = [], []

    def backtrack(start):
        out.append(path[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue                       # this value was already tried at this depth
            path.append(nums[i])
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return out


def combination_sum2(candidates, target):
    """Combinations from a multiset of positive values, each element used once, summing to target (LC 40)."""
    candidates = sorted(candidates)
    out, path = [], []

    def backtrack(start, remaining):
        if remaining == 0:
            out.append(path[:])
            return
        for i in range(start, len(candidates)):
            if i > start and candidates[i] == candidates[i - 1]:
                continue
            if candidates[i] > remaining:
                break
            path.append(candidates[i])
            backtrack(i + 1, remaining - candidates[i])
            path.pop()

    backtrack(0, target)
    return out


def permute_unique(nums):
    """Distinct permutations of a multiset (LC 47): equal values are placed in index order only."""
    nums = sorted(nums)
    out, path = [], []
    used = [False] * len(nums)

    def backtrack():
        if len(path) == len(nums):
            out.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                continue                       # its equal neighbor on the left must be placed first
            used[i] = True
            path.append(nums[i])
            backtrack()
            path.pop()
            used[i] = False

    backtrack()
    return out
```

**Why `i > start` and not `i > 0`.** The skip must remove only *siblings*, children of one node that put the same value in the same position. At `i == start` the loop fills a new depth; an equal `nums[start - 1]` is on the path, and taking both gives a different subset ([2, 2] rather than [2]).

**Why `not used[i - 1]` for permutations.** Copies of a value are interchangeable, so the search should fix one order in which they enter the path. The rule lets the copy at index i be placed only after the copy at i − 1 is on the path, so equal values always appear in index order. Every distinct arrangement has exactly one index-ordered labeling of its copies, so it is produced exactly once. The opposite test, `used[i - 1]`, forces reverse order and is also correct, but it prunes later: it lets any copy go first, even one whose higher-indexed twin can then never be placed, and such a branch dies only when nothing else is left to place. For six equal values the tests count 7 nodes with the first rule and 210 with the second. An alternative avoids the question: branch on the *distinct* values with a `Counter` of remaining copies (`permute_unique_counter` in the lab), which also works for values that cannot be sorted.

### 39g.3.4 Reusable elements

```python
def combine_with_reuse(nums, k):
    """Multisets of size k from distinct values, each reusable: recurse with i, not i + 1."""
    out, path = [], []

    def backtrack(start):
        if len(path) == k:
            out.append(path[:])
            return
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i)                       # the same element may come again, earlier ones may not
            path.pop()

    backtrack(0)
    return out


def permute_with_reuse(nums, k):
    """Sequences of length k over distinct values, each reusable: no start index and no used[]."""
    out, path = [], []

    def backtrack():
        if len(path) == k:
            out.append(path[:])
            return
        for x in nums:
            path.append(x)
            backtrack()
            path.pop()

    backtrack()
    return out
```

The target-sum version with reuse is Combination Sum (39) in 39d.17: `combine_with_reuse` with a sum as the end condition, plus the sorted `break`.

### 39g.3.5 Costs, and the itertools equivalents

| Form | Number of answers | Python's itertools |
|---|---|---|
| Subsets | 2ⁿ | `combinations(nums, r)` for every r |
| Combinations of size k | C(n, k) | `combinations(nums, k)` |
| Permutations | n! | `permutations(nums)` |
| Permutations of a multiset | n! / (m₁! · m₂! · …), mᵢ the multiplicities | `set(permutations(nums))`, which still generates all n! |
| Multisets of size k | C(n + k − 1, k) | `combinations_with_replacement(nums, k)` |
| Sequences of length k with repetition | nᵏ | `product(nums, repeat=k)` |

Each function runs in time proportional to the answers times their length, plus pruned nodes, and the tests compare each with its itertools counterpart. In production, use itertools; in an interview, write the recursion and name the itertools call that replaces it.

**Interview line:** *"Sets get a start index, sequences get a used array. Duplicates get a sort and a skip of equal siblings — for permutations, the copy on the left must already be on the path. Reuse means recursing with i instead of i + 1."*

## 39g.4 Two perspectives of enumeration: balls and boxes

### 39g.4.1 Who chooses whom

Many searches assign n items ("balls") to k places ("boxes"): numbers to buckets, values to positions. The same assignments can be enumerated from either side. In the **ball view**, each ball in turn chooses its box: depth n, up to k children per node. In the **box view**, each box in turn chooses its balls. The leaves are the same; the trees differ in shape, in which pruning is easy to state, and in which states repeat and can be remembered.

For permutations the two views cost the same: `permute` (39g.2.2) lets each position choose an element, and the mirror image (`permute_by_placing` in the lab) lets each element choose a free position; both visit n!/(n − j)! nodes at depth j. The views differ when boxes are interchangeable or have capacities, as in the next problem.

### 39g.4.2 Partition to K Equal Sum Subsets (698), three ways

Split positive numbers into k groups whose sums all equal `target = total / k`.

**Ball view.** Each number chooses a bucket: kⁿ leaves without pruning. Three rules shrink the tree: skip a bucket the number would overflow; place large numbers first, so overflows appear near the root; and — the important one — never try two buckets with equal current sums, because their subtrees are identical up to renaming the buckets (this includes the empty buckets, so the first number goes to bucket 0 only).

```python
def can_partition_k_balls(nums, k, stats=None):
    """Partition to K Equal Sum Subsets (LC 698), ball view: each number picks a bucket. Positive values."""
    total = sum(nums)
    if k <= 0 or total % k:
        return False
    target = total // k
    nums = sorted(nums, reverse=True)          # large numbers first: failures show up near the root
    if nums and nums[0] > target:
        return False
    buckets = [0] * k

    def place(i):
        if stats is not None:
            stats["nodes"] = stats.get("nodes", 0) + 1
        if i == len(nums):
            return True                        # no bucket exceeds target and they sum to k * target
        tried = set()
        for b in range(k):
            if buckets[b] + nums[i] > target or buckets[b] in tried:
                continue                       # overflow, or a bucket identical to one already tried
            tried.add(buckets[b])
            buckets[b] += nums[i]
            if place(i + 1):
                return True
            buckets[b] -= nums[i]
        return False

    return place(0)
```

If every number is placed and no bucket exceeds the target, all equal it, since the sums total k · target.

**Box view.** Fill one bucket at a time, choosing its numbers in index order, then open the next. Buckets are interchangeable here too; the symmetry rule for this view is that a new bucket always takes the first unused number, which has to go somewhere. The view has a further advantage: at a bucket boundary the future depends only on *which* numbers are used, so a used-set that failed can be remembered as a bitmask and never tried again.

```python
def can_partition_k_buckets(nums, k, stats=None):
    """LC 698, bucket view: fill one bucket at a time. Each new bucket takes the first unused number (buckets
    are interchangeable), and a used-set that failed at a bucket boundary is never tried again. Positive values."""
    total = sum(nums)
    if k <= 0 or total % k:
        return False
    target = total // k
    nums = sorted(nums, reverse=True)
    failed = set()

    def fill(done, used, current, start):
        if stats is not None:
            stats["nodes"] = stats.get("nodes", 0) + 1
        if done == k:
            return True
        if current == target:                  # this bucket is full: open the next one
            if used in failed:
                return False
            if fill(done + 1, used, 0, 0):
                return True
            failed.add(used)
            return False
        if current == 0:                       # symmetry: a new bucket holds the first unused number
            first = next(i for i in range(len(nums)) if not (used >> i) & 1)
            return fill(done, used | (1 << first), nums[first], first + 1)
        for i in range(start, len(nums)):      # within a bucket, take numbers in index order
            if (used >> i) & 1 or current + nums[i] > target:
                continue
            if fill(done, used | (1 << i), current + nums[i], i + 1):
                return True
        return False

    return fill(0, 0, 0, 0)
```

**DP over subsets.** Remembering used-sets everywhere gives a dynamic program. List a valid partition bucket by bucket; every prefix of that list fills some complete buckets and part of the next. `level[mask]` is the fill of the open bucket after using exactly the numbers in `mask` in some valid order, or −1 if there is none. Every valid order of the same numbers leaves the same fill, their sum modulo `target`, so one value per mask is enough:

```python
def can_partition_k_dp(nums, k):
    """LC 698 as DP over subsets: level[mask] is the fill of the open bucket after using mask, or -1.
    Positive values."""
    total = sum(nums)
    if k <= 0 or total % k:
        return False
    target = total // k
    n = len(nums)
    level = [-1] * (1 << n)
    level[0] = 0
    for mask in range(1 << n):
        if level[mask] < 0:
            continue                           # no valid order of these numbers exists
        for i in range(n):
            if not (mask >> i) & 1 and level[mask] + nums[i] <= target:
                level[mask | (1 << i)] = (level[mask] + nums[i]) % target
    return level[-1] == 0
```

**Costs.** The ball view is O(k · kⁿ) in the worst case. The box view with the memo is O(n · 3ⁿ): each used-set is expanded at most once, filling one bucket from it tries at most the subsets of the numbers left, and summed over all used-sets that is 3ⁿ subsets. The DP is O(n · 2ⁿ) time and O(2ⁿ) memory on every input, safe for n up to about 16 in Python. On 24 random instances whose answer is "no", so that nothing stops the search early (the tests draw them from a fixed seed and print these counts), the symmetry rules matter far more than the choice of view:

| Search | Nodes visited |
|---|---|
| Ball view, overflow check only | 237,958 |
| Ball view with the equal-sum rule | 4,988 |
| Box view, overflow check only | 234,223 |
| Box view with the first-unused rule and the memo | 5,211 |

Matchsticks to Square (473) is this problem with k = 4; Fair Distribution of Cookies (2305) and Find Minimum Time to Finish All Jobs (1723) minimize the largest bucket instead, with an extra bound (stop when a bucket already exceeds the best answer so far).

### 39g.4.3 Generate parentheses as counting constraints

Generate Parentheses (22, code in 39d.17) is the box view with constraints: each of the 2n positions chooses "(" or ")"; a prefix may take "(" while fewer than n are used, and ")" while it has fewer ")" than "(". Those two counts are all the future depends on, so *counting* the strings collapses the tree into a table of (opens left, closes left) states:

```python
def count_balanced(n):
    """How many balanced strings of n pairs exist: the generator's state, memoized (a Catalan number)."""
    @cache
    def ways(opens, closes):                   # brackets of each kind still to place
        if opens == 0:
            return 1                           # only ")" remain, and they fit
        total = ways(opens - 1, closes)
        if closes > opens:                     # a ")" keeps every prefix balanced
            total += ways(opens, closes - 1)
        return total

    return ways(n, n)
```

The answer is the Catalan number C(2n, n)/(n + 1), about 4ⁿ/(n^1.5 · √π): counting is O(n²), listing is O(n · Cₙ). Memoizing a generator's state to count instead of list is the bridge to 39g.7.

**Interview line:** *"Balls into boxes can be enumerated from either side. I pick the side where interchangeable choices are easy to skip and where the state after each step is small enough to memoize — for k-partition, one bucket at a time with the used set as a bitmask."*

## 39g.5 Island problems with DFS flood fill

### 39g.5.1 The template

A grid is a graph of cells joined to their 4-neighbors, and flood fill is DFS on it. 39d.4 writes it as an iterative BFS that checks each neighbor before queuing it; the recursive DFS below checks at the node — each call first asks whether it stands on unvisited land — so its four recursive calls read like the children of a 4-ary tree:

```python
def sink_island(grid, r, c):
    """DFS flood fill: turn (r, c) and all land 4-connected to it into water; return how many cells sank."""
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c] != 1:
        return 0                               # off the grid, water, or already visited
    grid[r][c] = 0                             # the grid is its own visited set
    size = 1
    for dr, dc in DIRS4:
        size += sink_island(grid, r + dr, c + dc)
    return size
```

Sinking visited land makes the grid its own visited set and yields the island's area (695). A full scan is O(rows · cols). The recursion can be as deep as the island has cells: with Python's default limit of 1,000 frames, a solid 32 × 32 block of land already raises `RecursionError` (the tests check it), so for large grids use 39d.4's iterative version or say you would call `sys.setrecursionlimit`.

### 39g.5.2 Enclaves and closed islands: sink the border first

Number of Closed Islands (1254, code in 39d.4) and Number of Enclaves (1020) ask about land that cannot reach the border. Rather than test each island for border contact, first sink every island that touches the border; what remains is the answer, counted by islands for 1254 and by cells for 1020:

```python
def num_enclaves(grid):
    """Number of Enclaves (LC 1020): sink all land that touches the border, then count what is left."""
    rows, cols = len(grid), len(grid[0])
    for r in range(rows):
        for c in range(cols):
            if r in (0, rows - 1) or c in (0, cols - 1):
                sink_island(grid, r, c)
    return sum(map(sum, grid))
```

Surrounded Regions (130) is the same with letters: mark the "O" regions touching the border, flip every other "O", restore the marked ones.

### 39g.5.3 Sub-islands: disqualify, then count

An island of grid2 is a sub-island when all its cells are land in grid1. Instead of carrying a flag through the recursion, run two passes: sink every island of grid2 that has a cell over water in grid1 (starting the fill from that cell sinks the whole island), then count the survivors:

```python
def count_sub_islands(grid1, grid2):
    """Count Sub Islands (LC 1905): sink each island of grid2 with a cell over water in grid1, then count."""
    rows, cols = len(grid2), len(grid2[0])
    for r in range(rows):
        for c in range(cols):
            if grid2[r][c] == 1 and grid1[r][c] == 0:
                sink_island(grid2, r, c)       # disqualified: part of it is water in grid1
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid2[r][c] == 1:
                sink_island(grid2, r, c)
                count += 1
    return count
```

### 39g.5.4 Distinct islands: serialize the walk

Number of Distinct Islands (694†) counts shapes up to translation. A DFS that starts at an island's first cell in row-major order and tries directions in a fixed order walks every copy of a shape identically, so the sequence of moves identifies the shape — provided it also records the returns:

```python
def num_distinct_islands(grid):
    """Number of Distinct Islands (LC 694): islands equal up to translation give the same DFS walk."""
    rows, cols = len(grid), len(grid[0])
    moves = ((1, 0, "d"), (-1, 0, "u"), (0, 1, "r"), (0, -1, "l"))

    def walk(r, c, step, path):
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != 1:
            return
        grid[r][c] = 0
        path.append(step)                      # entering: the move that led here
        for dr, dc, name in moves:
            walk(r + dr, c + dc, name, path)
        path.append("b")                       # leaving: without it, different shapes can collide

    shapes = set()
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                path = []
                walk(r, c, "o", path)
                shapes.add("".join(path))
    return len(shapes)
```

Without the "b" markers, shapes collide: with the order down, up, right, left, the corner {(0,0), (1,0), (0,1)} and the L {(0,0), (1,0), (1,1)} both serialize as "odr" (the "r" is taken from the top cell in the first and from the bottom cell in the second); with markers they are "odbrbb" and "odrbbb". A walk with explicit returns determines the DFS tree, hence the cells. The simpler alternative, the tests' reference, stores each island as the set of its cells' offsets from its first cell in row-major order. Number of Distinct Islands II (711†) also identifies rotations and reflections: normalize each of the eight transformed copies and keep the smallest.

## 39g.6 The BFS framework

### 39g.6.1 Queue, visited, steps — and why BFS finds shortest paths

BFS explores in layers: the start, then everything one move away, then two. It needs a **queue** of discovered states, a **visited** record so each state is queued once, and a **step count** — a distance per state, as below, or a counter advanced after each full layer, as in `oranges_rotting`. States can be anything hashable: cells, strings, tuples, bitmasks.

```python
def bfs_shortest(start, goal, neighbors):
    """Fewest moves from start to goal in an unweighted graph, or -1; also returns the states expanded."""
    if start == goal:
        return 0, 0
    dist = {start: 0}                          # doubles as the visited set
    queue = deque([start])
    expanded = 0
    while queue:
        state = queue.popleft()
        expanded += 1
        for nxt in neighbors(state):
            if nxt not in dist:                # mark when queued, not when popped
                dist[nxt] = dist[state] + 1
                if nxt == goal:
                    return dist[nxt], expanded
                queue.append(nxt)
    return -1, expanded
```

**Why the first discovery is the shortest.** By induction on d: states at distance d leave the queue before those at d + 1, each labeled with its true distance. A state at distance d + 1 has a neighbor at distance d and none closer, and the states at distance d leave the queue before any farther one, so it is first discovered from one of them, gets label d + 1 and queues behind the states at distance d. Hence the goal can be returned the moment it is generated. Two rules follow: mark a state when it is *queued*, not when it is dequeued (or it can be queued many times), and use BFS only when all moves cost the same — otherwise Dijkstra (39d.23, 39f.13.4), or 0-1 BFS (39g.6.5) for costs 0 and 1. The time is O(V + E) over the states and moves reached.

### 39g.6.2 Open the Lock (752), plain and bidirectional

Four wheels of ten digits give 10,000 states with 8 neighbors each; the dead ends are removed from the graph:

```python
def open_lock(deadends, target, bidirectional=False):
    """Open the Lock (LC 752): BFS over the 10,000 wheel positions; deadends are removed from the graph."""
    dead = set(deadends)
    if "0000" in dead or target in dead:
        return -1

    def turns(state):
        for i in range(4):
            digit = int(state[i])
            for step in (1, -1):
                nxt = state[:i] + str((digit + step) % 10) + state[i + 1:]
                if nxt not in dead:
                    yield nxt

    search = bidirectional_bfs if bidirectional else bfs_shortest
    return search("0000", target, turns)[0]
```

When the goal is known and moves can be undone, search from both ends. A plain BFS to depth d with branching factor b touches about bᵈ states; two searches meeting in the middle touch about 2 · b^(d/2). This version always grows the smaller frontier by one full layer:

```python
def bidirectional_bfs(start, goal, neighbors):
    """Same answer as bfs_shortest if every move can be undone; grows the smaller frontier, a level at a time."""
    if start == goal:
        return 0, 0
    near, far = {start: 0}, {goal: 0}          # distance from each end
    near_level, far_level = [start], [goal]
    expanded = 0
    while near_level and far_level:
        if len(near_level) > len(far_level):   # always expand the smaller side
            near, far = far, near
            near_level, far_level = far_level, near_level
        next_level = []
        for state in near_level:
            expanded += 1
            for nxt in neighbors(state):
                if nxt in far:                 # the searches meet; the first meeting is a shortest path
                    return near[state] + 1 + far[nxt], expanded
                if nxt not in near:
                    near[nxt] = near[state] + 1
                    next_level.append(nxt)
        near_level = next_level
    return -1, expanded
```

**Why the first meeting is optimal.** Say the side being expanded is working through its layer at distance a (it has discovered every state within a of its end), `far` holds every state within b of the other end, and no meeting has been found yet. A meeting found now joins a path of length at most a + 1 + b. Conversely, if a shortest path has length L ≤ a + b + 1, its node at distance a is in the layer being expanded and its successor lies within L − a − 1 ≤ b of the other end, so the meeting is found. The previous round found nothing, so L > a + b; hence L = a + b + 1 and every meeting this round has that length. Expanding whole layers is what makes the argument work: if the two searches take turns after every state, a meeting can be found while a layer is half expanded, and the tests include a six-node graph on which that variant returns 4 for a shortest path of 3.

On 60 random lock instances in the tests (drawn from a fixed seed), plain BFS expands 248,752 states and bidirectional BFS 50,096, five times fewer. State the requirements in an interview: one known goal, reversible moves (or a predecessor function), and forbidden states excluded from both searches — including the target, which is why `open_lock` checks it first.

### 39g.6.3 State-space search: sliding puzzle and genetic mutation

Sliding Puzzle (773) is BFS over board positions written as 6-character strings, with the adjacent cells of each cell precomputed:

```python
SLIDE_NEIGHBORS = ((1, 3), (0, 2, 4), (1, 5), (0, 4), (1, 3, 5), (2, 4))   # cells 0..5 of a 2 x 3 board


def sliding_puzzle(board):
    """Sliding Puzzle (LC 773): BFS over board states written as 6-character strings."""
    start = "".join(str(x) for row in board for x in row)

    def slides(state):
        zero = state.index("0")
        for j in SLIDE_NEIGHBORS[zero]:
            cells = list(state)
            cells[zero], cells[j] = cells[j], cells[zero]
            yield "".join(cells)

    return bfs_shortest(start, "123450", slides)[0]
```

Only half of the 720 boards can be solved. Read the tiles row by row, skipping the 0. A horizontal move keeps that order; a vertical move takes one tile past the two tiles between its old and new places, changing the number of inversions (pairs out of order) by 2 or 0. So the parity of the inversions never changes, the goal has none, and a board with odd parity is unsolvable:

```python
def is_solvable_2x3(board):
    """A 2 x 3 sliding puzzle is solvable exactly when its tiles, read row by row without the 0, have an even
    number of inversions: a move along a row keeps the order; a vertical move jumps a tile over two others."""
    tiles = [x for row in board for x in row if x]
    inversions = sum(a > b for i, a in enumerate(tiles) for b in tiles[i + 1:])
    return inversions % 2 == 0
```

The tests confirm on all 720 boards that the solvable ones are exactly the 360 with even parity, and that the hardest needs 21 moves. The parity check turns a failed search into an O(1) answer; adjusted for the blank's row when the width is even, it decides the 15-puzzle.

Minimum Genetic Mutation (433) changes only the neighbor function: a gene of length 8 has 24 single-letter changes, and only those in the bank are states. Word Ladder (127) is the same with 25 replacement letters per position and the word list as the bank.

```python
def min_mutation(start_gene, end_gene, bank):
    """Minimum Genetic Mutation (LC 433): a move changes one letter and must land on a gene in the bank."""
    valid = set(bank)

    def mutations(gene):
        for i, old in enumerate(gene):
            for letter in "ACGT":
                if letter != old:
                    nxt = gene[:i] + letter + gene[i + 1:]
                    if nxt in valid:
                        yield nxt

    return bfs_shortest(start_gene, end_gene, mutations)[0]
```

### 39g.6.4 Multi-source BFS

For "distance to the nearest source", start with every source in the queue at distance 0 — equivalent to one BFS from a virtual super-source joined to all of them, so the proof above carries over. Rotting Oranges (994) measures layers, so it uses a layer counter; 01 Matrix (542) needs each cell's distance to the nearest 0, so it stores distances:

```python
def oranges_rotting(grid):
    """Rotting Oranges (LC 994): every rotten orange starts in the queue; each BFS level is one minute."""
    rows, cols = len(grid), len(grid[0])
    queue = deque((r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 2)
    fresh = sum(row.count(1) for row in grid)
    minutes = 0
    while queue and fresh:
        minutes += 1
        for _ in range(len(queue)):            # exactly the oranges that turned rotten last minute
            r, c = queue.popleft()
            for dr, dc in DIRS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    queue.append((nr, nc))
    return minutes if fresh == 0 else -1


def update_matrix(mat):
    """01 Matrix (LC 542): distance from each cell to the nearest 0, with every 0 as a source."""
    rows, cols = len(mat), len(mat[0])
    dist = [[-1] * cols for _ in range(rows)]
    queue = deque()
    for r in range(rows):
        for c in range(cols):
            if mat[r][c] == 0:
                dist[r][c] = 0
                queue.append((r, c))
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] < 0:
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return dist
```

One BFS per source would cost O(sources · cells). Walls and Gates (286†), As Far from Land as Possible (1162) and Shortest Bridge (934, whose sources are one island's cells) follow the same pattern.

### 39g.6.5 0-1 BFS

When moves cost 0 or 1, a deque replaces Dijkstra's heap: a free move puts the neighbor at the front, a costly one at the back. The deque then holds states of at most two consecutive distances, the smaller ones in front, so states leave it in order of distance, which is all Dijkstra needed from the heap. In Minimum Obstacle Removal to Reach Corner (2290), entering an obstacle costs one removal:

```python
def minimum_obstacles(grid):
    """Minimum Obstacle Removal to Reach Corner (LC 2290): 0-1 BFS; free moves join the front of the deque."""
    rows, cols = len(grid), len(grid[0])
    dist = [[math.inf] * cols for _ in range(rows)]
    dist[0][0] = 0
    queue = deque([(0, 0)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[r][c] + grid[nr][nc] < dist[nr][nc]:
                dist[nr][nc] = dist[r][c] + grid[nr][nc]   # entering an obstacle costs one removal
                if grid[nr][nc]:
                    queue.append((nr, nc))
                else:
                    queue.appendleft((nr, nc))
    return dist[-1][-1]
```

Here every move into a cell costs the same, so the first time a cell is relaxed its distance is final and no cell enters the deque twice. When the cost depends on the move, as in Minimum Cost to Make at Least One Valid Path in a Grid (1368), where following the cell's arrow is free and changing it costs 1, a state can re-enter the deque when its distance improves; processing the stale copy only re-relaxes neighbors with the current distance, which is harmless. Either way the time is O(rows · cols), without Dijkstra's log factor.

**Interview line:** *"BFS settles states in order of distance, so I return when the goal is first generated and mark states when I queue them. With a fixed goal and reversible moves I'd search from both ends, a full layer at a time; with 0/1 costs, a deque."*

## 39g.7 The dynamic-programming framework

### 39g.7.1 When it applies, and four questions that find the transition

Dynamic programming is exhaustive search that never solves the same subproblem twice. Two properties of the brute-force recursion make it work (CLRS, section 15.3):

- **Overlapping subproblems**: different paths reach the same state. Paying 13 with coins 1, 2 and 5, the sequences 5 then 1, 1 then 5, and 2, 2, 2 all leave 7 to pay, and everything after that point is the same work.
- **Optimal substructure**: a state's best answer is built from best answers of independent smaller states. Shortest paths have it (a subpath of a shortest path is shortest); longest *simple* paths do not, since the longest simple paths u → v and v → w may share vertices and then do not combine into a simple path.

What remains is the **transition**, an equation for a state's answer in terms of smaller states. Four questions produce it, in this order:

1. **State.** What changes between subproblems? An index, a remaining capacity, two prefixes, an interval.
2. **Definition.** What does `dp(state)` mean, in one sentence using the state's variables? "`dp(a)` is the fewest coins that make amount a." Most wrong transitions come from a definition never written down.
3. **Choices.** Which decision, made at this state, leads to smaller states? The last coin; take item i or not; the balloon that bursts last. Each choice becomes one term of the transition.
4. **Base cases.** The smallest states, answered without choices: amount 0 needs 0 coins.

Then compute top-down (recursion plus memo) or bottom-up (dependencies first), and keep only what later states read.

### 39g.7.2 From brute force to O(1) space: Fibonacci and coin change

```python
def fib_naive(n):
    """F(n) straight from the recurrence: about 1.6**n calls, because the same subproblems repeat."""
    return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)


def fib_memo(n):
    """Top-down: the same recursion, but each subproblem is solved once. O(n) time and space."""
    memo = {0: 0, 1: 1}

    def f(i):
        if i not in memo:
            memo[i] = f(i - 1) + f(i - 2)
        return memo[i]

    return f(n)


def fib_table(n):
    """Bottom-up: fill the table in dependency order, with no recursion."""
    if n < 2:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def fib(n):
    """Keep only the two values the transition reads: O(1) space."""
    a, b = 0, 1                                # F(i) and F(i + 1)
    for _ in range(n):
        a, b = b, a + b
    return a
```

The naive recursion makes 2 · F(n + 1) − 1 calls — 2,692,537 for n = 30 — because its call tree shares nothing. The memo answers each subproblem once, O(n). The table computes the same values in increasing order, with no recursion. And since `dp[i]` reads only the two entries before it, two variables replace the table.

Coin Change (322) goes through the same stages. An optimal way to pay a ends with some coin c, and the coins before it must be an optimal way to pay a − c (a better one, plus c, would beat the optimum). So `fewest(a) = 1 + min(fewest(a − c))` over coins c ≤ a, with `fewest(0) = 0` and infinity when nothing fits:

```python
def coin_change_memo(coins, amount):
    """The same recursion with a memo: amount + 1 states, len(coins) choices each."""
    @cache
    def fewest(a):
        if a == 0:
            return 0
        return min((fewest(a - coin) + 1 for coin in coins if coin <= a), default=math.inf)

    best = fewest(amount)
    return -1 if best == math.inf else best


def coin_change_table(coins, amount):
    """Bottom-up: dp[a] is the fewest coins that make amount a; fill a = 1, 2, ..., amount."""
    dp = [0] + [math.inf] * amount
    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)
    return -1 if dp[amount] == math.inf else dp[amount]
```

Without its `@cache` line, `coin_change_memo` is the exponential brute force (`coin_change_brute` in the lab). Memo and table cost O(amount · len(coins)) time and O(amount) space, but the memo can recurse amount / (smallest coin) levels deep, and each level takes more than one interpreter frame (the function and its generator expression). With coins [1, 2, 5] and Python's default limit of 1,000 frames it raises `RecursionError` for amounts in the hundreds (from 249 on CPython 3.11, from 498 on 3.13), far below LeetCode's 10,000, so use the table or raise the limit with `sys.setrecursionlimit`; the tests check amount 1,000. The table cannot shrink to O(1): `dp[a]` reads up to `max(coins)` entries back. 39d.18's `coin_change` puts coins in the outer loop; for a minimum the two orders give the same table, for *counting* they answer different questions (39g.9.3).

### 39g.7.3 Designing transitions by induction: longest increasing subsequence

Induction asks: if `dp` is known for all smaller states, how do I get the next one? It works only with the right definition. For Longest Increasing Subsequence (300), "`dp[i]` is the LIS length of `nums[:i + 1]`" gives no transition, because the length does not say whether `nums[i]` can extend the subsequence — that depends on where it ends. "`dp[i]` is the length of the longest increasing subsequence *ending at* `nums[i]`" works: it is `nums[i]` alone or extends one ending at some `j < i` with `nums[j] < nums[i]`:

```python
def length_of_lis_quadratic(nums):
    """Longest Increasing Subsequence (LC 300) by induction: dp[i] is the longest one that ends at nums[i]."""
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp, default=0)
```

The answer is the maximum over i, not `dp[-1]`. O(n²) time.

**Patience sorting** makes it O(n log n). Deal the numbers left to right onto piles: each goes on the leftmost pile whose top is at least as large, or starts a new pile. The number of piles equals the LIS length:

- **The LIS is at most the number of piles.** Each card lands on a card at least as large, so a pile read bottom to top never increases, and an increasing subsequence takes at most one card per pile.
- **The LIS is at least the number of piles.** When a card goes onto pile k > 0, the top of pile k − 1 is smaller and earlier; record it as the card's predecessor. Following predecessors from a card on the last pile gives one card per pile, increasing and in array order.

The pile tops stay sorted, so finding the pile is a binary search. 39d.23 prints the length-only version; this one returns a subsequence:

```python
def longest_increasing_subsequence(nums):
    """One longest strictly increasing subsequence in O(n log n): patience piles plus back-pointers."""
    tops, top_index = [], []                   # tops[k]: smallest end of an increasing run of length k + 1
    parent = [-1] * len(nums)
    for i, x in enumerate(nums):
        k = bisect_left(tops, x)               # leftmost pile whose top is >= x
        if k == len(tops):
            tops.append(x)
            top_index.append(i)
        else:
            tops[k] = x
            top_index[k] = i
        parent[i] = top_index[k - 1] if k else -1   # the run of length k that x extends
    out, i = [], top_index[-1] if top_index else -1
    while i >= 0:
        out.append(nums[i])
        i = parent[i]
    return out[::-1]
```

`bisect_left` gives strictly increasing subsequences, `bisect_right` non-decreasing ones. Number of Longest Increasing Subsequence (673) keeps, next to each `dp[i]`, how many subsequences achieve it.

### 39g.7.4 Russian Doll Envelopes (354): sort to remove a dimension

An envelope nests in another only if both width and height are strictly smaller. Sorted by width, a nesting chain is an increasing subsequence of heights — except that two envelopes of equal width cannot nest. Sorting equal widths by *decreasing* height fixes that: within a width the heights never increase, so a strictly increasing subsequence takes at most one envelope per width, and strictly increasing heights in width order then mean strictly increasing widths. Conversely, every chain, listed by width, is such a subsequence.

```python
def max_envelopes(envelopes):
    """Russian Doll Envelopes (LC 354): sort by width up and height down, then LIS on the heights."""
    heights = [h for _, h in sorted(envelopes, key=lambda e: (e[0], -e[1]))]
    tops = []
    for h in heights:
        k = bisect_left(tops, h)
        if k == len(tops):
            tops.append(h)
        else:
            tops[k] = h
    return len(tops)
```

O(n log n). In three dimensions, the O(n²) chain DP is the interview answer.

### 39g.7.5 Base cases and memo sentinels: Minimum Falling Path Sum (931)

A falling path takes one cell per row, moving at most one column sideways per step. Bottom-up, one row suffices:

```python
def min_falling_path_sum(matrix):
    """Minimum Falling Path Sum (LC 931): best[c] is the cheapest path ending at column c of this row."""
    best = list(matrix[0])
    n = len(best)
    for row in matrix[1:]:
        best = [row[c] + min(best[max(c - 1, 0):c + 2]) for c in range(n)]
    return min(best)
```

The top-down version makes three decisions that are easy to get wrong:

```python
def min_falling_path_sum_memo(matrix):
    """LC 931 top-down. The memo uses None for 'not computed yet', because any number can be a real answer."""
    n = len(matrix)
    memo = [[None] * n for _ in range(n)]

    def best(r, c):                            # cheapest path from row 0 down to (r, c)
        if c < 0 or c >= n:
            return math.inf                    # off the grid: never chosen by min
        if r == 0:
            return matrix[0][c]
        if memo[r][c] is None:
            memo[r][c] = matrix[r][c] + min(best(r - 1, c - 1), best(r - 1, c), best(r - 1, c + 1))
        return memo[r][c]

    return min(best(n - 1, c) for c in range(n))
```

- **The base case is row 0**, whose cheapest path is the cell itself.
- **Off-grid columns return +∞**, which `min` never picks; returning 0 would let a path step off the grid free.
- **"Not computed" must be a value no answer can take.** Path sums can be zero or negative, so 0 or −1 would be read as answers. `None` is safe; with integer arrays, use a value outside the provable range (with |values| ≤ 100 and n ≤ 100, every path sum lies within ±10,000).

### 39g.7.6 Two views of the same enumeration: Distinct Subsequences (115)

Count the ways to pick characters of s, in order, that spell t. Let `ways(i, j)` count the ways to spell `t[j:]` from `s[i:]`. The definition leaves the choices open, and the two views of 39g.4 give two transitions:

- **Box view.** Each character of t chooses the position of s that supplies it: sum `ways(k + 1, j + 1)` over every `k ≥ i` with `s[k] == t[j]`. O(m · n) states with up to m choices: O(m² · n) for m = len(s), n = len(t).
- **Ball view.** Each character of s is skipped, or used for `t[j]` when they match: `ways(i + 1, j) + ways(i + 1, j + 1)`. Two choices per state: O(m · n).

```python
def num_distinct_by_target(s, t):
    """Distinct Subsequences (LC 115), box view: each character of t picks its position in s. O(m^2 n)."""
    @cache
    def ways(i, j):                            # ways to spell t[j:] with characters of s[i:]
        if j == len(t):
            return 1
        return sum(ways(k + 1, j + 1) for k in range(i, len(s)) if s[k] == t[j])

    return ways(0, 0)


def num_distinct(s, t):
    """LC 115, ball view: each character of s is skipped or used for the next character of t. O(m n)."""
    ways = [1] + [0] * len(t)                  # ways[j]: ways to spell t[:j] with the part of s read so far
    for ch in s:
        for j in range(len(t), 0, -1):         # right to left: this character is used at most once
            if t[j - 1] == ch:
                ways[j] += ways[j - 1]
    return ways[len(t)]
```

The bottom-up ball view updates one row right to left, so each character of s is used at most once — the loop shape of 0-1 knapsack (39g.9.1). When a DP is too slow, look for fewer choices per state before new states.

### 39g.7.7 From backtracking to DP: Word Break (139, 140)

The backtracking solution to Word Break (139) tries, at position i, every dictionary word that matches there and recurses after it. Whether `s[i:]` can be split does not depend on the words used before i, so the result depends only on i and can be memoized; bottom-up, it is one Boolean per suffix:

```python
def word_break(s, word_dict):
    """Word Break (LC 139): can[i] says whether s[i:] splits into dictionary words."""
    words = set(word_dict)
    lengths = {len(w) for w in words}
    can = [False] * len(s) + [True]
    for i in range(len(s) - 1, -1, -1):
        can[i] = any(can[i + n] for n in lengths if i + n <= len(s) and s[i:i + n] in words)
    return can[0]
```

O(n · L · w) for n characters, L distinct word lengths and words up to length w (each slice and hash costs w). Word Break II (140) wants every sentence, so the memo stores lists:

```python
def word_break_all(s, word_dict):
    """Word Break II (LC 140): every sentence, by backtracking memoized on the start index."""
    words = set(word_dict)

    @cache
    def sentences(i):                          # all splits of s[i:], each as one string
        if i == len(s):
            return [""]
        out = []
        for j in range(i + 1, len(s) + 1):
            if s[i:j] in words:
                out.extend(s[i:j] + (" " + rest if rest else "") for rest in sentences(j))
        return out

    return sentences(0)
```

The output can be exponential (with `s = "aaa…a"` and words "a" and "aa", the sentences grow like the Fibonacci numbers), but each suffix's sentences are built once. The recipe: write the brute force with the state as parameters and the answer as the return value, check that the answer depends on nothing else, memoize. If it depends on the path, the path joins the state, usually as a bitmask of at most about 20 items.

### 39g.7.8 Space optimization and traversal order

**Rolling a table into one row.** If `dp[i][j]` reads only row i − 1 and entries of row i to its left, keep one row and overwrite it in place. When computing `row[j]`, the entry above is the old `row[j]`, the entry to the left is the new `row[j − 1]`, and the diagonal `dp[i − 1][j − 1]` was just overwritten — so save it in a variable first (`longest_common_subsequence` in 39g.8.3). If a row reads only the previous row at smaller indices, as 0-1 knapsack does, iterate right to left and no variable is needed. Rolling gives up reconstruction: to recover the choices, keep the full table (39g.8.1, 39g.9.1) or parent pointers.

**Traversal order** follows from the transition: compute every entry after the entries it reads.

| `dp[i][j]` reads | Typical problems | Loop order |
|---|---|---|
| `dp[i-1][j]`, `dp[i][j-1]`, `dp[i-1][j-1]` | two prefixes: LCS, edit distance | i up, j up |
| `dp[i+1][j]`, `dp[i][j-1]`, `dp[i+1][j-1]` | intervals: palindromes, two-player games | i down, j up (or by length) |
| `dp[i][k]` and `dp[k][j]` for i < k < j | interval splitting: burst balloons | by width (or i down, j up) |
| `dp[i+1][j]`, `dp[i+1][j+1]` and entries of row i to the right | two suffixes, or a grid solved backwards: regex, dungeon | i down, j down |

**Other questions.** *Why n + 1 entries?* Index i is the prefix of length i, and the empty prefix is a real state with a known answer. *Where is the answer?* At `dp[n]` for "the first n items", the maximum over all entries for "ends at i". *Are the subproblems independent?* Check that combining their optimal answers never violates a constraint of the whole.

**Interview line:** *"Let me define the state in words — dp(i) is the best answer for … — then the choices, which give the transition, then the base cases. I'll memoize the recursion, turn it into a table in dependency order, and roll it into one row if each row reads only the previous one."*

## 39g.8 Subsequence and string DP

### 39g.8.1 Edit distance with the operations

For Edit Distance (72), let `dp[i][j]` be the fewest edits turning `word1[:i]` into `word2[:j]`, and look at the last characters. If they are equal, keep both: `dp[i − 1][j − 1]`. Nothing else can be cheaper, because dropping the last character of one word changes its distance to the other by at most 1, so `dp[i − 1][j − 1]` is at most `dp[i − 1][j] + 1` and at most `dp[i][j − 1] + 1`. Otherwise the last operation deletes `word1[i − 1]` (`dp[i − 1][j] + 1`), inserts `word2[j − 1]` (`dp[i][j − 1] + 1`) or replaces (`dp[i − 1][j − 1] + 1`). Empty prefixes cost i deletions or j insertions. 39d.23 computes the number with two rows; keeping the whole table lets you walk back from the corner, at each step moving to a neighbor whose value explains the current one:

```python
def edit_script(word1, word2):
    """Edit Distance (LC 72) with the operations: fill the full table, then walk back from the corner."""
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]  # dp[i][j]: edits that turn word1[:i] into word2[:j]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    ops, i, j = [], m, n
    while i or j:
        if i and j and word1[i - 1] == word2[j - 1]:
            ops.append(("keep", word1[i - 1]))
            i, j = i - 1, j - 1
        elif i and j and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append(("replace", word1[i - 1], word2[j - 1]))
            i, j = i - 1, j - 1
        elif i and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(("delete", word1[i - 1]))
            i -= 1
        else:
            ops.append(("insert", word2[j - 1]))
            j -= 1
    return dp[m][n], ops[::-1]
```

For "horse" → "ros" it returns 3: replace h by r, keep o, delete r, keep s, delete e. The tests replay every script. O(m · n) time and space (Hirschberg's method needs only linear space).

### 39g.8.2 Maximum subarray three ways

Maximum Subarray (53) has three classic solutions, each generalizing differently:

```python
def max_subarray(nums):
    """Maximum Subarray (LC 53), Kadane: ending_here is the best sum of a subarray that ends at this index."""
    best = ending_here = nums[0]
    for x in nums[1:]:
        ending_here = max(x, ending_here + x)  # extend the best run ending just before, or start fresh
        best = max(best, ending_here)
    return best


def max_subarray_prefix(nums):
    """LC 53 with prefix sums: a subarray sum is prefix[j] - prefix[i]; keep the smallest earlier prefix."""
    best, prefix, lowest = -math.inf, 0, 0
    for x in nums:
        prefix += x
        best = max(best, prefix - lowest)
        lowest = min(lowest, prefix)
    return best


def max_subarray_divide(nums, lo=0, hi=None):
    """LC 53 by divide and conquer: the best of the left half, the right half and the run across the middle."""
    if hi is None:
        hi = len(nums) - 1
    if lo == hi:
        return nums[lo]
    mid = (lo + hi) // 2
    run, left = 0, -math.inf
    for i in range(mid, lo - 1, -1):           # best sum of a run ending at mid
        run += nums[i]
        left = max(left, run)
    run, right = 0, -math.inf
    for i in range(mid + 1, hi + 1):           # best sum of a run starting at mid + 1
        run += nums[i]
        right = max(right, run)
    return max(max_subarray_divide(nums, lo, mid), max_subarray_divide(nums, mid + 1, hi), left + right)
```

- **DP (Kadane).** `ending_here` is the best sum of a subarray *ending at* the current index (the trick of 39g.7.3): the element alone, or the best run ending just before, extended. O(n), O(1) space.
- **Prefix sums.** A subarray sum is `prefix[j] − prefix[i]`, so subtract the smallest earlier prefix. This version extends to "length at most k" (keep earlier prefixes in a monotonic deque) and to two dimensions.
- **Divide and conquer.** The best subarray lies in the left half, the right half, or across the middle, where it is the best suffix of the left plus the best prefix of the right. O(n log n), and the shape a segment tree uses to answer the question for any range.

Maximum Sum Circular Subarray (918) is the larger of Kadane's answer and the total minus the minimum subarray (unless all values are negative); Maximum Product Subarray (152) tracks both the largest and smallest product ending here, because a negative number swaps them.

### 39g.8.3 Longest common subsequence and its relatives

For Longest Common Subsequence (1143), `dp[i][j]` is the LCS of `a[:i]` and `b[:j]`: if the last characters match, some LCS uses both (`dp[i − 1][j − 1] + 1`); otherwise one is unused (`max(dp[i − 1][j], dp[i][j − 1])`). With the rolling row of 39g.7.8:

```python
def longest_common_subsequence(a, b):
    """Longest Common Subsequence (LC 1143), one row: row[j] is the LCS of a's prefix read so far and b[:j]."""
    row = [0] * (len(b) + 1)
    for ch in a:
        diag = 0                               # dp[i - 1][j - 1], saved before it is overwritten
        for j in range(1, len(b) + 1):
            above = row[j]                     # dp[i - 1][j]
            row[j] = diag + 1 if ch == b[j - 1] else max(above, row[j - 1])
            diag = above
    return row[-1]
```

Delete Operation for Two Strings (583) keeps an LCS and deletes the rest. Minimum ASCII Delete Sum for Two Strings (712) cannot reuse the LCS: it keeps the common subsequence with the largest *character-code sum*. Among equally long ones the choice matters (for "ab" and "ba", keeping "b" costs 194 and keeping "a" 196), and the best need not be a longest one at all: for "zzzzaaaaa" and "aaaaazzzz", keeping "zzzz" costs 970 and keeping the longer "aaaaa" 976. Its recurrence is LCS's with costs in place of counts:

```python
def min_delete_steps(word1, word2):
    """Delete Operation for Two Strings (LC 583): keep a longest common subsequence and delete the rest."""
    return len(word1) + len(word2) - 2 * longest_common_subsequence(word1, word2)


def minimum_delete_sum(s1, s2):
    """Minimum ASCII Delete Sum for Two Strings (LC 712): the LCS recurrence with costs instead of counts."""
    row = [0] * (len(s2) + 1)                  # row[j]: cost to make the part of s1 read so far equal s2[:j]
    for j in range(1, len(s2) + 1):
        row[j] = row[j - 1] + ord(s2[j - 1])
    for ch in s1:
        diag, row[0] = row[0], row[0] + ord(ch)
        for j in range(1, len(s2) + 1):
            above = row[j]
            if ch == s2[j - 1]:
                row[j] = diag
            else:
                row[j] = min(above + ord(ch), row[j - 1] + ord(s2[j - 1]))
            diag = above
    return row[-1]
```

Relatives: Uncrossed Lines (1035) is LCS in disguise; Shortest Common Supersequence (1092) has length `m + n − LCS` and is rebuilt from the full table; Maximum Length of Repeated Subarray (718) wants a contiguous match, so its state is "common run ending at i and j" and its answer a maximum over the table.

### 39g.8.4 Palindromic subsequences

A palindrome reads the same reversed, so the natural state is an interval. For Longest Palindromic Subsequence (516), `dp[i][j]` covers `s[i..j]`: matching ends wrap the best palindrome inside (`dp[i + 1][j − 1] + 2`); otherwise one end is unused (`max(dp[i + 1][j], dp[i][j − 1])`). Row i reads row i + 1, so i runs down, j up, and one row suffices:

```python
def longest_palindrome_subseq(s):
    """Longest Palindromic Subsequence (LC 516): dp[i][j] covers s[i..j]; i runs down, j up; one row kept."""
    n = len(s)
    row = [0] * n                              # row[j] is dp[i][j] for the current i
    for i in range(n - 1, -1, -1):
        row[i] = 1
        diag = 0                               # dp[i + 1][j - 1]; for j = i + 1 it is the empty string
        for j in range(i + 1, n):
            below = row[j]                     # dp[i + 1][j]
            row[j] = diag + 2 if s[i] == s[j] else max(below, row[j - 1])
            diag = below
    return row[-1] if n else 0


def min_insertions(s):
    """Minimum Insertion Steps to Make a String Palindrome (LC 1312): mirror each character outside an LPS."""
    return len(s) - longest_palindrome_subseq(s)
```

**Why Minimum Insertion Steps (1312) is n − LPS.** Mirroring each character outside a longest palindromic subsequence makes a palindrome with n − LPS insertions. Conversely, take any palindrome made by insertions and pair each position with its mirror image. The original characters whose partner is also original, plus an original character in the center, form a palindromic subsequence of s, so there are at most LPS of them; every other original character is paired with an inserted one, so at least n − LPS insertions are needed. The tests check the formula against a recursion that inserts directly. Longest Palindromic Substring (5) is contiguous and different: expanding around each of the 2n − 1 centers takes O(n²) time and O(1) space (Manacher's algorithm takes O(n)).

### 39g.8.5 The subsequence templates

| Template | State | Problems |
|---|---|---|
| One sequence, ending at i | `dp[i]`: best for a subsequence or subarray ending at i; answer = max over i | 300, 354, 53, 673, 152 |
| Two sequences, prefixes | `dp[i][j]` for `a[:i]` and `b[:j]`; look at the last characters | 1143, 72, 115, 583, 712, 1035, 97 Interleaving String, 10 |
| One sequence, interval | `dp[i][j]` for `s[i..j]`; look at both ends | 516, 1312, 312, 486 |

**Interview line:** *"For two strings I define dp(i, j) on the prefixes and look at the last characters: equal means take both, otherwise drop one or pay for an edit. For palindromes I use intervals and look at both ends."*

## 39g.9 The knapsack family

### 39g.9.1 0-1 knapsack: the table, the reconstruction, the single row

Items have weights and values, each is taken at most once, and the total weight must fit a capacity. The state is (items considered, capacity), the choice is skip or take, and `best[i][c]` is the largest value from the first i items within capacity c: `best[i][c] = max(best[i − 1][c], best[i − 1][c − w] + v)` when weight w fits, with 0 for no items. The full table also recovers the chosen items: walking back, whenever `best[i][c]` differs from `best[i − 1][c]`, item i − 1 was taken.

```python
def knapsack_items(weights, values, capacity):
    """0-1 knapsack that also returns the chosen items: keep the full table, then walk back."""
    n = len(weights)
    best = [[0] * (capacity + 1) for _ in range(n + 1)]   # best[i][c]: first i items, capacity c
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            best[i][c] = best[i - 1][c]
            if w <= c:
                best[i][c] = max(best[i][c], best[i - 1][c - w] + v)
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if best[i][c] != best[i - 1][c]:       # item i - 1 changed the optimum, so it was taken
            chosen.append(i - 1)
            c -= weights[i - 1]
    return best[n][capacity], chosen[::-1]
```

39d.18's `knapsack_01` keeps one row and iterates capacities from high to low, so `best[c − w]` is read before this pass overwrites it and still describes the previous items: each item counts at most once. O(n · C) for capacity C is *pseudo-polynomial* — polynomial in the value C, exponential in its digits — fine while n · C stays near 10⁷ in Python, hopeless for C = 10⁹.

### 39g.9.2 Subset sum

Partition Equal Subset Sum (416) asks whether a subset reaches half the total (39d.18's `can_partition`). In Python, one integer can be the whole table: bit s says whether some subset sums to s, and adding x keeps every old sum and every old sum plus x — a shift and an OR:

```python
def can_partition_bitset(nums):
    """Partition Equal Subset Sum (LC 416), an integer as the table: bit s is set if a subset sums to s."""
    total = sum(nums)
    if total % 2:
        return False
    reachable = 1                              # only the empty sum
    for x in nums:
        reachable |= reachable << x            # every old sum, with or without x
    return bool((reachable >> (total // 2)) & 1)
```

It is the same O(n · S) recurrence, S being the total, but CPython runs the inner loop over 30-bit digits in C. For 200 random values from 1 to 100 (a total near 10,000), 39d.18's list version takes about a million Python-level loop steps, while the bitset does 200 shifts and ORs of an integer of at most about 10,000 bits, a few hundred machine digits each; in one run on CPython 3.11 that was 0.07 ms against 25 ms.

### 39g.9.3 Unbounded knapsack: why loop order separates combinations from permutations

When an item can be taken again, the "take" branch stays on its own row: `dp[i][a] = dp[i − 1][a] + dp[i][a − c]` for counting. In one row, amounts go from low to high, so `ways[a − c]` already includes copies of coin c. Coin Change II (518) counts *multisets* of coins; Combination Sum IV (377), despite its name, counts *sequences*:

```python
def change(amount, coins):
    """Coin Change II (LC 518), combinations: coins in the outer loop, so each multiset is counted once."""
    ways = [1] + [0] * amount
    for coin in coins:
        for a in range(coin, amount + 1):      # left to right: this coin may repeat
            ways[a] += ways[a - coin]
    return ways[amount]


def combination_sum4(nums, target):
    """Combination Sum IV (LC 377), ordered sequences: amounts in the outer loop, so every order counts."""
    ways = [1] + [0] * target
    for a in range(1, target + 1):
        for x in nums:
            if x <= a:
                ways[a] += ways[a - x]         # x is the last element of the sequence
    return ways[target]
```

With coins in the outer loop, every multiset is assembled in one canonical order — all its copies of the first coin, then of the second — and counted once. With amounts in the outer loop, `ways[a]` sums over the *last* element, so 1 + 2 and 2 + 1 both count. For amount 3 and values {1, 2}, `change` gives 2 and `combination_sum4` gives 3. Climbing Stairs (70) is `combination_sum4` with {1, 2}. For a minimum, as in 322, the order does not matter.

### 39g.9.4 Target sum, directly and as subset sum

Target Sum (494) puts + or − before each number. The direct DP has state (index, running total):

```python
def find_target_sum_ways_memo(nums, target):
    """Target Sum (LC 494) directly: state (index, running total), two choices per number."""
    @cache
    def ways(i, total):
        if i == len(nums):
            return int(total == target)
        return ways(i + 1, total + nums[i]) + ways(i + 1, total - nums[i])

    return ways(0, 0)
```

That is n times up to 2 · total + 1 states. The transform in 39d.18 does better: with P the sum given +, N the sum given −, P − N = target and P + N = total, so P = (total + target) / 2 and the task is to count subsets summing to P. P must be an integer (total + target even) between 0 and total (|target| ≤ total), or the answer is 0. Zeros double the count, since +0 and −0 are different expressions; the 0-1 counting loop over `range(P, x - 1, -1)` handles them, because for x = 0 it adds `ways[0]` to itself. Python-specific pitfall: a table indexed by a running total that goes negative raises no error — `dp[-3]` silently reads from the end — so offset the index or use a dictionary.

### 39g.9.5 Bounded knapsack by binary splitting

If item i may be taken up to `counts[i]` times, one 0-1 item per copy costs O(C · Σ counts). Bundle the k copies as 1, 2, 4, …, 2ᵗ⁻¹, with t as large as possible, and a remainder r = k − (2ᵗ − 1) < 2ᵗ instead: every count from 0 to k is a sum of some bundles (below 2ᵗ by binary digits, above as r plus a binary part), so a 0-1 knapsack over the bundles covers exactly the allowed counts in O(C · Σ log counts):

```python
def bounded_knapsack(weights, values, counts, capacity):
    """Item i may be used up to counts[i] times: split counts into bundles 1, 2, 4, ..., rest; then 0-1."""
    best = [0] * (capacity + 1)
    for w, v, k in zip(weights, values, counts):
        bundle = 1
        while k > 0:
            take = min(bundle, k)              # every count 0..k is a sum of some of these bundles
            k -= take
            bundle *= 2
            for c in range(capacity, take * w - 1, -1):
                best[c] = max(best[c], best[c - take * w] + take * v)
    return best[capacity]
```

| Variant | Inner loop over capacity | Problems |
|---|---|---|
| 0-1, best value | high to low | 39d.18 `knapsack_01`; 1049 Last Stone Weight II; 474 Ones and Zeroes (two capacities) |
| 0-1, feasible | high to low, or a bitset | 416 |
| 0-1, count | high to low | 494 after the transform |
| Unbounded, best | low to high | 322 |
| Unbounded, count multisets | items outside, amounts inside | 518 |
| Count sequences | amounts outside, items inside | 377, 70 |
| Bounded | binary bundles, then high to low | — |

**Interview line:** *"Knapsack is dp over (items considered, capacity). Each item once: iterate capacity downward so I read the previous items' row; unlimited copies: upward. For counting, items outside count combinations, amounts outside count sequences."*

## 39g.10 Grid and game DP

### 39g.10.1 Minimum Path Sum (64)

Moving right or down, the cheapest path to a cell comes from above or from the left; one row suffices:

```python
def min_path_sum(grid):
    """Minimum Path Sum (LC 64): best[c] is the cheapest path to column c of the current row."""
    best = [math.inf] * len(grid[0])
    best[0] = 0
    for row in grid:
        best[0] += row[0]
        for c in range(1, len(row)):
            best[c] = row[c] + min(best[c], best[c - 1])   # from above, or from the left
    return best[-1]
```

Unique Paths (62) counts paths instead; Triangle (120) is the same idea, best computed bottom-up.

### 39g.10.2 Dungeon Game (174): why it runs backwards

A knight walks from the top-left to the bottom-right cell, right or down; cells add or remove health, which must stay at least 1. Find the smallest starting health.

A forward table fails: a partial path has two relevant numbers, the health required so far and the health left, and one number per cell cannot rank paths by both. In `[[0, -1, 2, 0], [0, 0, 1, -5]]`, take two paths into the cell holding 1: along the bottom row it has required 1 health and arrives with a running total of 1; along the top row it has required 2 and arrives with 2. A forward DP keeps the bottom path; after the final −5 it needs 5 while the top path needs only 4. The forward table answers 5; the truth is 4 (the test checks both).

Backwards, the state is the health needed on *entering* a cell, which depends only on the future — exactly what a DP state must do. The knight continues to the neighbor that needs less, so `need = max(1, min(need_right, need_down) − dungeon[r][c])`, with a virtual neighbor of the last cell needing 1:

```python
def calculate_minimum_hp(dungeon):
    """Dungeon Game (LC 174), solved backwards: need[c] is the health required on entering cell (r, c)."""
    cols = len(dungeon[0])
    need = [math.inf] * (cols + 1)
    need[cols - 1] = 1                         # a virtual cell below the princess: arrive with 1
    for row in reversed(dungeon):
        for c in range(cols - 1, -1, -1):
            need[c] = max(1, min(need[c], need[c + 1]) - row[c])
    return need[0]
```

Ask of every DP whether the state's answer depends on how you got there; if it does, change direction or add the past to the state.

### 39g.10.3 Freedom Trail (514)

A ring turns one position per step, and each letter of the key must be rotated to the top and pressed. Rotating to the nearest copy is not optimal: in the ring "aababca" with key "bc", the nearer b (2 steps) is 3 steps from the c while the other b (3 steps) is next to it, so greedy needs 7 steps and the optimum is 6. The state is the ring position that spelled the last letter; the transition tries every copy of the next letter from every previous position:

```python
def find_rotate_steps(ring, key):
    """Freedom Trail (LC 514): state = ring position that spelled the last letter; value = fewest steps."""
    n = len(ring)
    where = defaultdict(list)
    for i, ch in enumerate(ring):
        where[ch].append(i)
    cost = {0: 0}                              # position at 12 o'clock -> fewest rotations to get here
    for ch in key:
        cost = {j: min(c + min(abs(i - j), n - abs(i - j)) for i, c in cost.items()) for j in where[ch]}
    return min(cost.values()) + len(key)       # plus one button press per letter
```

O(len(key) · m²), m being the most copies of one letter.

### 39g.10.4 Cheapest Flights Within K Stops (787): DP over (flights, city)

With at most k stops a route has at most k + 1 flights. Let `cost[t][v]` be the cheapest arrival at v with at most t flights; a t-flight route is a (t − 1)-flight route plus one flight, so `cost[t][v] = min(cost[t − 1][v], cost[t − 1][u] + price)` over flights (u, v). Each round relaxes every flight once — Bellman–Ford stopped after k + 1 rounds:

```python
def find_cheapest_price(n, flights, src, dst, k):
    """Cheapest Flights Within K Stops (LC 787): dp over (flights taken, city): Bellman-Ford, k + 1 rounds."""
    cost = [math.inf] * n
    cost[src] = 0
    for _ in range(k + 1):                     # after round t: cheapest with at most t flights
        nxt = cost[:]                          # read last round only, so each round adds one flight
        for u, v, price in flights:
            if cost[u] + price < nxt[v]:
                nxt[v] = cost[u] + price
        cost = nxt
    return -1 if cost[dst] == math.inf else cost[dst]
```

The copy is essential: relaxing in place lets one round chain several flights, breaking the stop limit. O((k + 1) · (n + E)) time, the copies included. 39f.13.4 solves the problem with Dijkstra on (city, flights used) states, and 39f.13.8 covers Floyd–Warshall, the DP over "intermediate cities allowed so far".

### 39g.10.5 Regular Expression Matching (10)

Patterns use letters, `.` (any character) and `x*` (zero or more x). Let `match[i][j]` say whether `s[i:]` matches `p[j:]`, and `first` that `s[i]` exists and equals `p[j]` or `p[j]` is `.`. If `p[j + 1]` is `*`, the starred element matches zero copies (`match[i][j + 2]`) or matches `s[i]` and stays (`first and match[i + 1][j]`); otherwise both advance (`first and match[i + 1][j + 1]`). The empty pattern matches only the empty string.

```python
def is_match(s, p):
    """Regular Expression Matching (LC 10): match[i][j] says whether s[i:] matches p[j:]."""
    m, n = len(s), len(p)
    match = [[False] * (n + 1) for _ in range(m + 1)]
    match[m][n] = True
    for i in range(m, -1, -1):
        for j in range(n - 1, -1, -1):
            first = i < m and p[j] in (s[i], ".")
            if j + 1 < n and p[j + 1] == "*":
                match[i][j] = match[i][j + 2] or (first and match[i + 1][j])   # zero copies, or one more
            else:
                match[i][j] = first and match[i + 1][j + 1]
    return match[0][0]
```

O(m · n); the tests compare it with `re.fullmatch` on random strings and patterns. In Wildcard Matching (44), `*` alone matches any sequence: `match[i][j + 1]` (empty) or `match[i + 1][j]` (consume one).

### 39g.10.6 Super Egg Drop (887): change the question

With k eggs and n floors, find the fewest drops that always determine the highest safe floor. The direct DP, `drops(e, f) = 1 + min over x of max(drops(e − 1, x − 1), drops(e, f − x))`, costs O(k · n²), or O(k · n log n) with a binary search on x.

Invert the question: with m drops and e eggs, how many floors can be resolved? Drop from floor `floors(m − 1, e − 1) + 1`: if the egg breaks, the floors below are resolved with m − 1 drops and e − 1 eggs; if not, the floors above with m − 1 drops and e eggs. So `floors(m, e) = floors(m − 1, e − 1) + floors(m − 1, e) + 1`, and the answer is the smallest m with `floors(m, k) ≥ n`:

```python
def super_egg_drop(k, n):
    """Super Egg Drop (LC 887): floors[e] is how many floors m moves and e eggs can always resolve."""
    floors = [0] * (k + 1)
    moves = 0
    while floors[k] < n:
        moves += 1
        for e in range(k, 0, -1):              # right to left: floors[e - 1] still holds the m - 1 value
            floors[e] = floors[e - 1] + floors[e] + 1   # breaks: below; survives: above; plus this floor
    return moves
```

O(k · m) with m ≤ n (about log₂ n once k ≥ log₂ n); `floors(m, e)` equals the sum of C(m, i) for i = 1..e. Two eggs and 100 floors need 14 drops, since 14 + 13 + … + 1 = 105 ≥ 100 while 13 drops resolve only 91 floors (1884). The tests compare with the direct recurrence. When a DP is slow, try swapping the answer with a state variable.

### 39g.10.7 Burst Balloons (312): think about the last move

Bursting balloon k earns `nums[left] · nums[k] · nums[right]` with its current neighbors, which change as balloons disappear, so "which bursts first" does not split the row into independent halves. "Which bursts *last* in the open interval (i, j)" does: when k is last, everything else between i and j is gone, its neighbors are exactly i and j, and the balloons on its two sides never meet. Pad the row with a 1 at each end:

`best[i][j] = max over i < k < j of best[i][k] + vals[i] · vals[k] · vals[j] + best[k][j]`

```python
def max_coins(nums):
    """Burst Balloons (LC 312), interval DP: choose the balloon in (i, j) that bursts last."""
    vals = [1] + nums + [1]
    n = len(vals)
    best = [[0] * n for _ in range(n)]         # best[i][j]: coins for bursting all balloons strictly inside
    for width in range(2, n):
        for i in range(n - width):
            j = i + width
            best[i][j] = max(best[i][k] + vals[i] * vals[k] * vals[j] + best[k][j] for k in range(i + 1, j))
    return best[0][n - 1]
```

Intervals go by increasing width: O(n³) time, O(n²) space, checked against all n! burst orders for n ≤ 6. Minimum Cost to Merge Stones (1000) and matrix-chain multiplication split the same way.

### 39g.10.8 Two-player games: score difference

In Predict the Winner (486), two players alternately take a number from either end; does the first end with at least as much? Track the difference instead of two scores. Let `lead[i][j]` be the best margin the player *to move* can force on `nums[i..j]`; after taking an end, the opponent moves, and the opponent's margin counts against you:

`lead[i][j] = max(nums[i] − lead[i + 1][j], nums[j] − lead[i][j − 1])`, with `lead[i][i] = nums[i]`.

```python
def predict_the_winner(nums):
    """Predict the Winner (LC 486): lead[i][j] is the best margin the player to move forces on nums[i..j]."""
    n = len(nums)
    lead = nums[:]                             # one row; lead[i][i] = nums[i]
    for i in range(n - 2, -1, -1):
        for j in range(i + 1, n):
            lead[j] = max(nums[i] - lead[j], nums[j] - lead[j - 1])
    return lead[-1] >= 0


def stone_game(piles):
    """Stone Game (LC 877): with an even number of piles and an odd total, the first player always wins."""
    return True
```

Stone Game (877) adds an even number of piles and an odd total, and then the first player always wins. Color the piles by index parity. The ends of an even-length row have different colors; if the first player takes, say, the even-indexed end, both ends of the rest are odd-indexed, so the opponent must take an odd one, and the first player again faces one end of each color. So the first player can collect all even-indexed piles or all odd-indexed ones, whichever sum is larger — and with an odd total the sums differ. The tests confirm it with a full game search. Score difference turns any two-player zero-sum game on a sequence into a single-number DP.

**Interview line:** *"If the forward state needs information about the past, I run the DP backwards, as in the dungeon, or invert the question, as in egg drop. For intervals I choose the last operation, because that makes the two sides independent."*

## 39g.11 House robber and the stock state machine

### 39g.11.1 One framework for three robbers

The state is a position, the choice is rob or skip, and robbing forbids the neighbor. On a line (198, code in 39d.23), `best(i) = max(best(i − 1), best(i − 2) + nums[i])`. On a circle (213), the first and last houses are neighbors, so one of them is skipped: solve the line without the first and the line without the last. On a binary tree (337), each subtree reports two numbers — best if its root is robbed, best if not — combined on the way up, a postorder computation (39f.1.3):

```python
def _rob_range(nums, lo, hi):
    """Best haul from nums[lo:hi] with no two adjacent houses: dp(i) = max(dp(i - 1), dp(i - 2) + nums[i])."""
    before, last = 0, 0                        # best up to house i - 2, and up to house i - 1
    for i in range(lo, hi):
        before, last = last, max(last, before + nums[i])
    return last


def rob_circular(nums):
    """House Robber II (LC 213): the first and last houses touch; solve without one, then the other."""
    if len(nums) == 1:
        return nums[0]
    return max(_rob_range(nums, 0, len(nums) - 1), _rob_range(nums, 1, len(nums)))


def rob_tree(root):
    """House Robber III (LC 337): each subtree returns (best if its root is robbed, best if it is not)."""
    def visit(node):
        if node is None:
            return 0, 0
        left, right = visit(node.left), visit(node.right)
        robbed = node.val + left[1] + right[1]  # the children must be skipped
        skipped = max(left) + max(right)        # the children are free to choose
        return robbed, skipped

    return max(visit(root))
```

All O(n); the pair return needs no memo because it carries everything the parent needs. Delete and Earn (740) is House Robber over values: taking v earns v times its count and forbids v − 1 and v + 1.

### 39g.11.2 One state machine for all six stock problems

The six stock problems differ only in constraints. Describe the end of each day by the purchases made so far (t) and whether a share is held, and let `free[d][t]` be the best cash after the first d days without a share. On day d, at `price`:

- **Not holding** = rest, or sell what you held: `free[d + 1][t] = max(free[d][t], hold[t] + price − fee)`.
- **Holding** = rest, or buy, which uses a purchase and needs `cooldown` days without a sale just before it, so it starts from the not-holding value of `cooldown` days earlier: `hold[t] = max(hold[t], free[d − cooldown][t − 1] − price)`.

Initially nothing is held, cash is 0, and holding is impossible (−∞); the answer is the best "not holding" value at the end.

| Problem | Purchases k | Fee | Cooldown |
|---|---|---|---|
| 121 Best Time to Buy and Sell Stock | 1 | 0 | 0 |
| 122 Best Time to Buy and Sell Stock II | unlimited | 0 | 0 |
| 123 Best Time to Buy and Sell Stock III | 2 | 0 | 0 |
| 188 Best Time to Buy and Sell Stock IV | k | 0 | 0 |
| 309 Best Time to Buy and Sell Stock with Cooldown | unlimited | 0 | 1 |
| 714 Best Time to Buy and Sell Stock with Transaction Fee | unlimited | fee | 0 |

```python
def max_profit(prices, k=None, fee=0, cooldown=0):
    """All six stock problems as one state machine (LC 121, 122, 123, 188, 309, 714).

    The state after each day is (buys made so far, holding or not). k caps the buys (None: no cap), fee is
    paid on each sale, and after a sale you wait cooldown days before buying again."""
    if k is not None and 2 * k >= len(prices):
        k = None                               # the cap cannot bind: a trade needs two different days
    layers = 1 if k is None else k + 1         # with no cap: one layer that never counts buys
    step = 0 if k is None else 1
    free = [[0] * layers]                      # free[d][t]: best cash after d days, not holding, t buys
    hold = [-math.inf] * layers                # hold[t]: best cash while holding a share, t buys
    for d, price in enumerate(prices):
        buy_from = free[max(0, d - cooldown)]  # skip the last cooldown days: no sale may fall in them
        free.append([max(free[d][t], hold[t] + price - fee) for t in range(layers)])
        hold = [max(hold[t], buy_from[t - step] - price) if t >= step else hold[t] for t in range(layers)]
    return max(free[-1])
```

A transaction is counted at the buy. A buy and its sale need two different days, so k ≥ n/2 cannot bind and the purchase dimension collapses. The cooldown reads the "not holding" row from `cooldown` days back, hence the stored history (a ring buffer of `cooldown + 1` rows would do). Time O(n · k). Sanity checks: 121's answer is the largest difference between a price and the lowest price before it; 122's is the sum of the positive day-to-day increases. The tests compare the function with an exhaustive search for every mix of k, fee and cooldown.

**Interview line:** *"All six stock problems are one state machine over (day, purchases used, holding or not): the fee is subtracted at the sale, the cooldown reads the not-holding state from further back, and k at least n/2 means no limit."*

## 39g.12 Greedy algorithms

### 39g.12.1 When a greedy choice is safe

A greedy algorithm makes the choice that looks best now and never reconsiders it. It is correct when some optimal solution makes the greedy first choice (the **greedy-choice property**) and what remains is a smaller instance of the same problem (**optimal substructure**). The standard proof is an **exchange argument**: swap the first choice of any optimal solution for the greedy one and show the result is still feasible and no worse; induction does the rest. Without that argument, look for a counterexample.

One family has a general explanation. A nonempty family of feasible sets, closed under taking subsets, is a **matroid** if a smaller feasible set can always be extended by some element of any larger one. Exactly then does the rule "go through the elements from heaviest to lightest and keep each one that leaves the set feasible" find a maximum-weight feasible set for *every* choice of non-negative weights (Rado, 1957; Edmonds, 1971). Forests of a graph form one, which is why Kruskal's algorithm, the same rule run from lightest to heaviest edge, finds a minimum spanning tree (39f.13.6). Disjoint intervals do not — with A = [0, 10), B = [0, 5) and C = [5, 10), {A} cannot be extended from {B, C} — yet "earliest end first" maximizes their number by an exchange argument; with weights it fails, and Maximum Profit in Job Scheduling (1235) needs DP.

### 39g.12.2 Interval scheduling and arrows

To keep the most pairwise disjoint intervals, sort by end and take every interval that starts after the last one taken ends. **Exchange:** let g end first; any optimal selection, sorted by end, starts with an interval ending no earlier than g, and replacing it by g keeps the selection disjoint and the same size. So some optimal selection contains g, and the rest is the same problem on the intervals after g. Non-overlapping Intervals (435, code in 39d.23) is n minus this count.

Minimum Number of Arrows to Burst Balloons (452) runs the same sweep on *closed* intervals: an arrow at x bursts every balloon with start ≤ x ≤ end, so touching balloons share an arrow, and a new arrow is needed only when `start > last_shot` (435 would use `>=`):

```python
def find_min_arrow_shots(points):
    """Minimum Number of Arrows to Burst Balloons (LC 452): shoot at the earliest end. Closed intervals."""
    arrows, last_shot = 0, -math.inf
    for start, end in sorted(points, key=lambda p: p[1]):
        if start > last_shot:                  # the last arrow misses this balloon
            arrows += 1
            last_shot = end
    return arrows
```

**Why shoot at the earliest end.** Every solution hits the first-ending balloon at some x ≤ e₁; moved to e₁, that arrow still hits every balloon it hit (each starts at or before x and ends at or after e₁). **Pitfalls:** sorting by start ([1, 10], [2, 3], [4, 5]: taking [1, 10] first keeps one interval where two fit); confusing closed and half-open endpoints, which decides between `>` and `>=`.

### 39g.12.3 Meeting Rooms II (253†) with a sweep line

The rooms needed equal the largest number of meetings in progress at once: a lower bound, since those meetings need different rooms, and enough, since assigning meetings by start time to any free room fails only when every room is busy at that start. To find the peak, turn each meeting into +1 at its start and −1 at its end and keep a running sum over the sorted events. Meetings are half-open, so ends go before starts at equal times, which sorting `(time, delta)` tuples does because −1 < +1:

```python
def min_meeting_rooms_sweep(intervals):
    """Meeting Rooms II (LC 253) as a sweep line: +1 at each start, -1 at each end; ends first on ties."""
    events = sorted([(start, 1) for start, _ in intervals] + [(end, -1) for _, end in intervals])
    rooms = peak = 0
    for _, delta in events:
        rooms += delta
        peak = max(peak, rooms)
    return peak
```

39d.7 uses a heap of end times instead; with weights in place of ±1, the sweep checks capacity over time (1094 Car Pooling).

### 39g.12.4 Jump games

In Jump Game (55), keep the farthest index reachable so far; standing beyond it means the end is unreachable. In Jump Game II (45), the indices whose fewest jumps is exactly j form a contiguous range, and scanning range j yields the end of range j + 1 — BFS by levels with ranges instead of a queue:

```python
def can_jump(nums):
    """Jump Game (LC 55): track the farthest index reachable so far; fail when standing beyond it."""
    reach = 0
    for i, step in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + step)
    return True


def jump(nums):
    """Jump Game II (LC 45): BFS by levels with no queue; each level is one more jump. The end is reachable."""
    jumps, level_end, farthest = 0, 0, 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == level_end:                     # every index reachable with `jumps` jumps has been scanned
            jumps += 1
            level_end = farthest
    return jumps
```

Both O(n) and O(1) space; `jump` stops before the last index, which needs no further jump.

### 39g.12.5 Gas Station (134), two ways

Stations on a circle give `gas[i]`, and the road to the next costs `cost[i]`. Find a start from which a lap never runs the tank below zero (LeetCode guarantees there is at most one; in general ties can allow several, as with gas [1, 1] and cost [1, 1]).

```python
def can_complete_circuit(gas, cost):
    """Gas Station (LC 134), greedy: if the tank goes negative at i, no start in [start, i] can work."""
    if sum(gas) < sum(cost):
        return -1
    start = tank = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:
            start, tank = i + 1, 0
    return start


def can_complete_circuit_prefix(gas, cost):
    """LC 134 from the graph of the running balance: start just after its lowest point."""
    balance, lowest, start = 0, 0, 0
    for i in range(len(gas)):
        balance += gas[i] - cost[i]
        if balance < lowest:
            lowest, start = balance, i + 1
    return start % len(gas) if balance >= 0 else -1
```

**The reset.** If a lap from s first runs dry after station i, every start s′ between s and i fails too: the lap from s reached s′ with a non-negative tank, so starting at s′ empty is no better. The next candidate is i + 1. If total gas covers total cost, the last candidate works: its own stretch never ran dry, and each abandoned stretch has a negative sum but no negative partial sum before its end, so on the wrap-around the tank never drops below total gas minus total cost.

**The graph view.** Starting at s shifts the running balance of `gas[i] − cost[i]` down by its value just before s, so no point goes negative exactly when s follows a lowest point (and the final balance is non-negative); the code takes the first. Both are O(n); the tests compare them with a simulation from every start.

### 39g.12.6 Video Stitching (1024)

Cover [0, time] with the fewest clips. Sort by start; while [0, covered] is covered, among the clips that start inside it take the one reaching farthest; if none passes `covered`, there is a gap:

```python
def video_stitching(clips, time):
    """Video Stitching (LC 1024): of the clips that start inside the covered part, take the longest-reaching."""
    clips = sorted(clips)
    count = covered = i = 0
    while covered < time:
        farthest = covered
        while i < len(clips) and clips[i][0] <= covered:
            farthest = max(farthest, clips[i][1])
            i += 1
        if farthest == covered:
            return -1                          # a gap: nothing starts inside what is covered
        count += 1
        covered = farthest
    return count
```

**Staying ahead:** after j clips the greedy covers a prefix at least as long as any j clips can (a competitor's next clip starts inside its prefix, hence inside the greedy's, so the greedy considered it). O(n log n). Minimum Number of Taps to Open to Water a Garden (1326) is the same with tap i covering [i − r, i + r]; Jump Game II is the same with "clips" [i, i + nums[i]].

### 39g.12.7 When greedy fails

Paying with the largest coin that fits is optimal for systems such as 1, 5, 10, 25 and wrong in general:

```python
def greedy_coin_count(coins, amount):
    """Largest coin first. Optimal for coin systems such as 1, 5, 10, 25 but not in general; -1 if stuck."""
    count = 0
    for coin in sorted(coins, reverse=True):
        count += amount // coin
        amount %= coin
    return count if amount == 0 else -1
```

With coins 1, 3, 4 and amount 6, greedy pays 4 + 1 + 1 and the optimum is 3 + 3; the tests check this, and that greedy matches the DP of 39g.7.2 for every amount below 400 with US coins. To test whether a system is *canonical* (greedy always optimal), compare greedy with the DP for every amount below the sum of the two largest coins: Kozen and Zaks proved that the smallest failure, if any, lies below that bound. Two more failures to have ready: the 0-1 knapsack by value per unit weight (capacity 10, one item of weight 6 and value 7, two of weight 5 and value 5: greedy takes the dense item and gets 7, the optimum is 10; greedy is right only for the *fractional* knapsack), and weighted interval scheduling.

**Interview line:** *"I commit to a greedy rule only with an exchange argument: take an optimal solution, swap in the greedy choice, show it stays feasible and no worse. If I can't, I look for a small counterexample — coins 1, 3, 4 and amount 6 — and fall back to DP."*

## 39g.13 Math techniques

### 39g.13.1 One-line solutions and why they are right

```python
def can_win_nim(n):
    """Nim Game (LC 292): the player to move loses exactly when n is a multiple of 4."""
    return n % 4 != 0


def bulb_switch(n):
    """Bulb Switcher (LC 319): bulb i is toggled once per divisor, so it ends on iff i is a perfect square."""
    return math.isqrt(n)
```

**Nim Game (292).** Each turn removes 1 to 3 stones; taking the last stone wins. Facing a multiple of 4, every move leaves a non-multiple, and the opponent restores a multiple by taking `n % 4`; eventually you face 0. Facing a non-multiple, take `n % 4` and the roles reverse. The tests check this against the game DP (a position wins if some move reaches a losing one). **Stone Game (877)** is the parity argument of 39g.10.8. **Bulb Switcher (319).** Round d toggles every d-th bulb, so bulb i is toggled once per divisor. Divisors pair up as (d, i/d) except when d = i/d, so the count is odd exactly for perfect squares, and the answer is ⌊√n⌋. `math.isqrt` is exact for any size; `int(math.sqrt(n))` can be off by one for large n.

### 39g.13.2 Bit manipulation

| Expression | Effect | Why |
|---|---|---|
| `n & (n - 1)` | clears the lowest set bit | subtracting 1 flips the lowest set bit and the 0s below it |
| `n & -n` | keeps only the lowest set bit | in two's complement, `-n == ~n + 1` |
| `x ^ x == 0`, `x ^ 0 == x` | pairs cancel | XOR is associative and commutative (39d.16) |
| `(n >> i) & 1` | reads bit i | |
| `n \| (1 << i)`, `n & ~(1 << i)`, `n ^ (1 << i)` | sets, clears, toggles bit i | |
| `x & (m - 1)`, m a power of two | `x % m` for x ≥ 0 | the low bits are the remainder |
| `chr(ord(c) ^ 32)` | swaps the case of an ASCII letter | the cases differ only in bit 5 |

```python
def is_power_of_two(n):
    """Power of Two (LC 231): a power of two has one set bit, and n & (n - 1) clears the lowest one."""
    return n > 0 and (n & (n - 1)) == 0


def hamming_weight(n):
    """Number of 1 Bits (LC 191): clear the lowest set bit until nothing is left."""
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count
```

Clearing the lowest bit repeatedly loops once per set bit, and Counting Bits (338) is a DP on the same trick: `bits[i] = bits[i & (i − 1)] + 1` (`count_bits` in the lab). Missing Number (268) and Single Number (136) are in 39d.16; for 268, n(n + 1)/2 minus the sum also works, but can overflow in fixed-width languages. In Python, negative integers have infinitely many leading 1s, so `hamming_weight(-1)` never stops — mask with `& 0xFFFFFFFF` — and `int.bit_count()` (3.10+) is the built-in count.

### 39g.13.3 Modular arithmetic, fast powers, gcd and lcm

Remainders can be taken at every step of a sum or product. Python's `%` returns a value in [0, m) for positive m, while C, C++ and Java can return a negative remainder after a subtraction (add m first). Division needs a modular inverse, which exists when gcd(a, m) = 1 (`pow(a, -1, m)` in Python 3.8+). **Repeated squaring** computes `base ** exp % mod` in O(log exp) multiplications by walking the exponent's bits. Super Pow (372) gives the exponent as decimal digits; read them from the most significant end with a^(10x + d) = (a^x)^10 · a^d:

```python
def mod_pow(base, exp, mod):
    """base ** exp % mod by repeated squaring: O(log exp) multiplications of numbers below mod."""
    result, base = 1 % mod, base % mod
    while exp:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result


def super_pow(a, b):
    """Super Pow (LC 372): a ** b % 1337, where b is a list of decimal digits, most significant first."""
    result = 1
    for digit in b:                            # a^(10x + d) = (a^x)^10 * a^d
        result = mod_pow(result, 10, 1337) * mod_pow(a, digit, 1337) % 1337
    return result
```

Python's three-argument `pow` does the same in C; Pow(x, n) (50) is the floating-point version. **Euclid's algorithm** rests on one fact: a and b have the same common divisors as b and a mod b, because a mod b = a − q · b. After two steps the first argument has at least halved, so it runs O(log min(a, b)) times (Lamé: at most five times the decimal digits of the smaller number). The lcm follows; divide before multiplying:

```python
def gcd(a, b):
    """Euclid: gcd(a, b) = gcd(b, a mod b); the arguments at least halve every two steps."""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a, b):
    """Least common multiple through the gcd; divide before multiplying to keep numbers small."""
    return 0 if a == 0 or b == 0 else abs(a // gcd(a, b) * b)
```

### 39g.13.4 Counting primes with the sieve of Eratosthenes

Count Primes (204) wants the primes below n. Trial division costs O(n√n); the sieve crosses out multiples instead:

```python
def count_primes(n):
    """Count Primes (LC 204): primes below n by the sieve of Eratosthenes, O(n log log n)."""
    if n < 3:
        return 0
    is_prime = bytearray([1]) * n
    is_prime[0] = is_prime[1] = 0
    for i in range(2, math.isqrt(n - 1) + 1):
        if is_prime[i]:                        # start at i * i: smaller multiples have a smaller prime factor
            is_prime[i * i::i] = bytes(len(range(i * i, n, i)))
    return sum(is_prime)
```

Crossing out starts at i · i, because a smaller multiple k · i with k < i has a smaller prime factor and is already crossed out; the outer loop stops at √n, because every composite below n has a prime factor at most √n. The work is the sum of n/p over primes p ≤ √n, which is O(n log log n) because the sum of 1/p over primes up to x grows like ln ln x (Mertens). Memory is a byte per number, and slice assignment crosses out a whole progression in C. The tests check 78,498 primes below 10⁶.

### 39g.13.5 Factorial zeros and their preimage

A trailing zero of n! is a factor 2 · 5, and 2s are more plentiful, so Factorial Trailing Zeroes (172) counts 5s: one per multiple of 5, one more per multiple of 25, and so on. In Preimage Size of Factorial Zeroes Function (793), the zero count f(x) is constant between multiples of 5 and grows by at least 1 at each, so every value is taken by exactly five consecutive x or by none — a multiple of 25 skips a value: f(24) = 4 and f(25) = 6, so no factorial ends in exactly five zeros. f is non-decreasing, so two binary searches on the monotone predicate `f(x) >= z` (39f.6.2) give the answer:

```python
def trailing_zeroes(n):
    """Factorial Trailing Zeroes (LC 172): count the factors of 5 in n! (factors of 2 are more plentiful)."""
    zeros = 0
    while n:
        n //= 5
        zeros += n
    return zeros


def preimage_size_fzf(k):
    """Preimage Size of Factorial Zeroes Function (LC 793): always 0 or 5, found with two binary searches."""
    def first_with_at_least(z):                # smallest x with trailing_zeroes(x) >= z
        lo, hi = 0, 5 * (z + 1)
        while lo < hi:
            mid = (lo + hi) // 2
            if trailing_zeroes(mid) >= z:
                hi = mid
            else:
                lo = mid + 1
        return lo

    return first_with_at_least(k + 1) - first_with_at_least(k)
```

The bound 5 · (z + 1) works because f(5(z + 1)) ≥ z + 1. Each search is O(log k) steps of O(log k) work.

### 39g.13.6 Finding the missing and the duplicated

In Set Mismatch (645), 1..n appear once each except that one is duplicated and one is missing. Use the array as its own hash table: for each value v, negate the entry at index v − 1; finding it already negative means v was seen before; the one entry left positive marks the missing value.

```python
def find_error_nums(nums):
    """Set Mismatch (LC 645): mark value v by negating slot v - 1; a mark already set means a duplicate."""
    marks = nums[:]                            # work on a copy: the caller's list stays intact
    duplicate = -1
    for x in marks:
        v = abs(x)
        if marks[v - 1] < 0:
            duplicate = v
        else:
            marks[v - 1] = -marks[v - 1]
    missing = next(i + 1 for i, x in enumerate(marks) if x > 0)
    return [duplicate, missing]
```

O(n); mark the input in place and restore it for O(1) extra space. Alternatives: the sum and the sum of squares (their differences from 1..n give d − m and d² − m²), or XOR splitting as in Single Number III (39d.16).

### 39g.13.7 Randomized algorithms: shuffling and reservoir sampling

**Fisher–Yates** fills each position from the left with an item chosen uniformly from the positions not yet filled:

```python
def fisher_yates(items, rng=random):
    """Uniform shuffle in place: slot i receives a uniformly chosen item from the unplaced part i..n-1."""
    for i in range(len(items) - 1):
        j = rng.randrange(i, len(items))
        items[i], items[j] = items[j], items[i]
    return items


def naive_shuffle(items, rng=random):
    """A classic bug: swapping with any index gives n**n equally likely runs over n! orders; not uniform."""
    n = len(items)
    for i in range(n):
        j = rng.randrange(n)
        items[i], items[j] = items[j], items[i]
    return items
```

The n · (n − 1) · … · 2 = n! equally likely draw sequences produce n! different orders (at the first differing draw, the two sequences put different items in the same slot), so each order has probability 1/n!. The tempting variant that swaps with *any* position has nⁿ equally likely runs; for n ≥ 3, n − 1 divides n! but shares no factor with nⁿ, so the runs cannot split evenly among the n! orders. For three items, three orders have probability 4/27 and three 5/27. Shuffle an Array (384) keeps the original and returns a Fisher–Yates copy.

**Reservoir sampling** picks k items uniformly from a stream of unknown length in one pass and O(k) memory: keep the first k; the i-th item (from 1) then replaces a random slot with probability k/i.

```python
def reservoir_sample(stream, k, rng=random):
    """k items chosen uniformly from an iterable of unknown length, in one pass and O(k) memory."""
    sample = []
    for i, item in enumerate(stream):
        if i < k:
            sample.append(item)
        else:
            j = rng.randrange(i + 1)           # the (i + 1)-th item enters with probability k / (i + 1)
            if j < k:
                sample[j] = item
    return sample


def pick_index(nums, target, rng=random):
    """Random Pick Index (LC 398): reservoir sampling of size 1 over the indices that hold target."""
    chosen, seen = -1, 0
    for i, x in enumerate(nums):
        if x == target:
            seen += 1
            if rng.randrange(seen) == 0:       # replace with probability 1 / seen
                chosen = i
    return chosen
```

**Proof.** Item i > k enters with probability k/i; at each later step j it is evicted only if the new item enters (k/j) and picks its slot (1/k), so it survives with probability (j − 1)/j. The product over j = i + 1..n telescopes to i/n, giving k/i · i/n = k/n. The first k items survive with the product from k + 1, also k/n. More strongly, every k-subset is equally likely (by induction on the stream). Linked List Random Node (382) is k = 1 over the nodes; Random Pick Index (398) is k = 1 over the indices holding the target.

**Testing randomized code.** With an injectable random source you can check exactly: the tests replay every possible sequence of draws through a scripted source and add up exact probabilities (`Fraction`s), proving 1/n! per order for Fisher–Yates (n ≤ 5), 1/C(n, k) per subset for the reservoir (n ≤ 6) and the 4/27 and 5/27 above; a seeded chi-square test complements them. Weighted picks (528) are in 39f.6.3, O(1) random removal (380, 710) in 39f.12.2.

### 39g.13.8 Probability puzzles, computed exactly

The safe method is always the same: list equally likely outcomes, condition on what was observed, count.

```python
def monty_hall_exact(switch):
    """Exact chance of winning: enumerate the car's door, the first pick and the host's door."""
    win = Fraction(0)
    for car in range(3):
        for pick in range(3):
            goats = [d for d in range(3) if d not in (car, pick)]   # doors the host may open
            for host in goats:
                final = 3 - pick - host if switch else pick         # doors are 0, 1, 2
                if final == car:
                    win += Fraction(1, 9) / len(goats)
    return win


def birthday_collision(n, days=365):
    """Exact probability that at least two of n people share a birthday (uniform, independent birthdays)."""
    all_distinct = Fraction(1)
    for i in range(n):
        all_distinct *= Fraction(max(days - i, 0), days)
    return 1 - all_distinct


def two_children_puzzles():
    """Exact answers to three wordings of the two-child puzzle, by enumerating equally likely outcomes."""
    outcomes = [(older, younger, met) for older in "BG" for younger in "BG" for met in (0, 1)]

    def p_both_boys(given):
        space = [o for o in outcomes if given(o)]
        return Fraction(sum(o[0] == o[1] == "B" for o in space), len(space))

    return {
        "at least one child is a boy": p_both_boys(lambda o: "B" in o[:2]),
        "the older child is a boy": p_both_boys(lambda o: o[0] == "B"),
        "the child you happened to meet is a boy": p_both_boys(lambda o: o[o[2]] == "B"),
    }
```

**Monty Hall.** You pick one of three doors; the host, who knows where the car is, always opens another door with a goat behind it (choosing at random when both other doors hide goats) and always offers a switch. Switching wins exactly when the first pick was wrong: probability 2/3. The host's knowledge matters: had he opened one of the other two doors at random and it merely happened to hide a goat, switching would win half the time. The tests check both by enumeration, and `monty_hall_simulate` in the lab agrees.

**Birthdays.** The chance that n people all have different birthdays is the product of (365 − i)/365 for i = 0..n − 1. At 23 people a shared birthday has probability 0.507, the first value above one half; at 70 it is 0.9992. The surprise comes from pairs: 23 people form 253. "Does someone share *my* birthday?" differs: among 22 others, 1 − (364/365)²² ≈ 5.9%.

**Two children.** Each child is a boy or a girl with probability 1/2, independently, and the question is the probability that both are boys. The answer depends on how you learned about a boy, which the usual wording ("one of them is a boy") leaves open:

- The family is picked at random from the two-child families with at least one boy, or you ask "is at least one of them a boy?" and hear yes. Only girl–girl is excluded and the three remaining families are equally likely: 1/3.
- You learn that the older child is a boy: 1/2.
- You meet one of the two children, chosen at random, and it is a boy: 1/2, because a two-boy family produces that meeting with probability 1 and a mixed family with probability 1/2. The same holds when a parent tells you the sex of one child chosen at random.

`two_children_puzzles` computes all three by enumerating (older, younger, which child you meet). In an interview, state how the information was obtained before computing.

### 39g.13.9 Ugly numbers

Ugly Number (263): a positive number with no prime factors besides 2, 3 and 5 (divide them out and check for 1; `is_ugly` in the lab). Ugly Number II (264) wants the n-th. Every ugly number after 1 is 2u, 3u or 5u for a smaller ugly u, so the sequence merges three sorted streams, each read through a pointer into the list so far; when two streams produce the same value (6 = 2 · 3 = 3 · 2), advance both:

```python
def nth_ugly_number(n):
    """Ugly Number II (LC 264): merge the sorted streams 2u, 3u and 5u over the ugly numbers found so far."""
    ugly = [1]
    i2 = i3 = i5 = 0                           # the next ugly number to multiply by 2, 3 and 5
    while len(ugly) < n:
        nxt = min(2 * ugly[i2], 3 * ugly[i3], 5 * ugly[i5])
        ugly.append(nxt)
        if nxt == 2 * ugly[i2]:                # advance every stream that produced nxt: no duplicates
            i2 += 1
        if nxt == 3 * ugly[i3]:
            i3 += 1
        if nxt == 5 * ugly[i5]:
            i5 += 1
    return ugly[n - 1]


def nth_super_ugly_number(n, primes):
    """Super Ugly Number (LC 313): the same merge with one stream per prime, kept in a heap."""
    ugly = [1]
    heap = [(p, p, 0) for p in primes]         # (next value of the stream, prime, index into ugly)
    heapq.heapify(heap)
    while len(ugly) < n:
        value = heap[0][0]
        ugly.append(value)
        while heap[0][0] == value:             # advance every stream that produced value
            _, p, i = heapq.heappop(heap)
            heapq.heappush(heap, (p * ugly[i + 1], p, i + 1))
    return ugly[n - 1]
```

Super Ugly Number (313) has k primes, so the stream heads go in a heap: each new value costs O(log k) for every stream that produced it, one per listed prime dividing it, so the total is O(n log k) times that small number. Ugly Number III (1201) means divisible by a, b or c, with n up to 10⁹, so count instead of generating: by inclusion–exclusion, the integers up to x divisible by a, b or c number x/a + x/b + x/c − x/lcm(a, b) − x/lcm(a, c) − x/lcm(b, c) + x/lcm(a, b, c), each quotient rounded down. The count is non-decreasing, so binary search for the smallest x with count(x) ≥ n; that x is divisible by a, b or c (otherwise count(x − 1) = count(x)), so it is the answer:

```python
def nth_ugly_number_iii(n, a, b, c):
    """Ugly Number III (LC 1201): the smallest x with count(x) >= n, where count uses inclusion-exclusion."""
    ab, ac, bc = lcm(a, b), lcm(a, c), lcm(b, c)
    abc = lcm(ab, c)

    def count(x):                              # positive integers <= x divisible by a, b or c
        return x // a + x // b + x // c - x // ab - x // ac - x // bc + x // abc

    lo, hi = 1, n * min(a, b, c)
    while lo < hi:
        mid = (lo + hi) // 2
        if count(mid) >= n:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

O(log(n · min(a, b, c))) steps; in fixed-width languages, cap the lcms to avoid overflow.

**Interview line:** *"For math-flavored problems I look for the invariant that removes the loop — divisor pairs for the bulbs, multiples of four for Nim, parity for the stone game — and for randomness I state the sample space and prove uniformity by counting equally likely draw sequences."*

## 39g.14 Classic interview problems

### 39g.14.1 Trapping Rain Water (42) in three steps

The water above a bar is the lower of the tallest bar to its left and the tallest to its right (both including it) minus its height. The path from that definition to the best solution is a model for improving any algorithm aloud:

```python
def trap_brute(height):
    """Trapping Rain Water (LC 42) by definition: water over a bar is min(tallest left, tallest right) - bar."""
    return sum(min(max(height[:i + 1]), max(height[i:])) - h for i, h in enumerate(height))


def trap_prefix(height):
    """The same formula with both maxima precomputed: O(n) time and O(n) space."""
    n = len(height)
    left, right = [0] * n, [0] * n
    for i in range(n):
        left[i] = max(left[i - 1] if i else 0, height[i])
    for i in range(n - 1, -1, -1):
        right[i] = max(right[i + 1] if i < n - 1 else 0, height[i])
    return sum(min(lo, hi) - h for lo, hi, h in zip(left, right, height))


def trap_two_pointers(height):
    """O(1) space: the side with the lower running maximum is settled; the other side has a higher wall."""
    left, right = 0, len(height) - 1
    left_max = right_max = water = 0
    while left < right:
        left_max = max(left_max, height[left])
        right_max = max(right_max, height[right])
        if left_max <= right_max:
            water += left_max - height[left]
            left += 1
        else:
            water += right_max - height[right]
            right -= 1
    return water
```

The brute force is O(n²); precomputing both maxima makes it O(n) time and space; two pointers need no arrays. **Invariant:** `left_max` is the tallest in `height[0..left]`, `right_max` the tallest in `height[right..n − 1]`. If `left_max ≤ right_max`, the water above `left` is exactly `left_max − height[left]`: its true right maximum is at least `right_max ≥ left_max`, so the left side binds even though the bars between the pointers are unknown. The bar where the pointers meet is never added, and rightly: the pointer standing there kept its place only because that bar was at least as tall as everything the other pointer had passed. 39d.21 adds a monotonic-stack version that fills each basin as its right wall arrives.

### 39g.14.2 Container With Most Water (11)

Choose two lines holding the most water: width times the shorter height.

```python
def max_area(height):
    """Container With Most Water (LC 11): move the shorter wall; no better pair can use it."""
    left, right, best = 0, len(height) - 1, 0
    while left < right:
        best = max(best, (right - left) * min(height[left], height[right]))
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best
```

**Why moving the shorter line is safe.** If `height[left] < height[right]`, every container using `left` with a right end `j < right` is narrower and no taller than `height[left]`, so it holds no more than the current one; `left` can never be in a better pair. (With equal heights the same holds for both lines, so moving either is safe.) One line is discarded per step: O(n). Unlike rain water, the bars in between do not matter.

### 39g.14.3 Interval problems: covered intervals

39d.7 has merging (56), insertion (57) and intersection (986). Remove Covered Intervals (1288) completes the set: [c, d) covers [a, b) when c ≤ a and b ≤ d. Sort by start ascending and, on ties, end descending; then every possible cover comes earlier, and an interval is covered exactly when its end does not exceed the largest end so far:

```python
def remove_covered_intervals(intervals):
    """Remove Covered Intervals (LC 1288): sort by start up and end down; an interval is covered iff its end
    does not pass the largest end seen so far."""
    remaining, max_end = 0, -math.inf
    for _, end in sorted(intervals, key=lambda iv: (iv[0], -iv[1])):
        if end > max_end:
            remaining += 1
            max_end = end
    return remaining
```

The descending tie-break puts the longer of two equal-start intervals first. The three interval questions differ only in sort key and comparison: covered compares ends with a running maximum, merge compares a start with the last end, intersection advances whichever interval ends first.

### 39g.14.4 Split Array into Consecutive Subsequences (659)

Split a sorted array into runs of consecutive integers of length at least 3. For each value x in order: if a run ends at x − 1, append x; otherwise start a run, which needs an x + 1 and an x + 2 at once:

```python
def is_possible(nums):
    """Split Array into Consecutive Subsequences (LC 659), sorted input: extend a run that ends at x - 1
    if there is one, otherwise start x, x + 1, x + 2."""
    left = Counter(nums)                       # values not yet placed
    ends = Counter()                           # ends[v]: runs of length >= 3 that end at v
    for x in nums:
        if left[x] == 0:
            continue                           # already used by a run started earlier
        left[x] -= 1
        if ends[x - 1]:
            ends[x - 1] -= 1
            ends[x] += 1
        elif left[x + 1] and left[x + 2]:
            left[x + 1] -= 1
            left[x + 2] -= 1
            ends[x + 2] += 1
        else:
            return False
    return True
```

**Exchange:** if a valid split starts a new run R at x while a run S ends at x − 1, gluing R onto S keeps every run consecutive and at least 3 long, so appending is never worse. A run starting at x must contain x + 1 and x + 2, so reserving them at once loses nothing. O(n). Hand of Straights (846) and Divide Array in Sets of K Consecutive Numbers (1296) fix the group size at k: start at the smallest remaining value and take k consecutive values.

### 39g.14.5 Pancake Sorting (969)

A flip reverses a prefix. Move the largest unsorted value to the top with one flip and down to the end of the unsorted part with another:

```python
def pancake_sort(arr):
    """Pancake Sorting (LC 969): flip the largest unsorted value to the top, then down to its final place."""
    arr = arr[:]
    flips = []
    for size in range(len(arr), 1, -1):
        i = arr.index(max(arr[:size]))
        if i == size - 1:
            continue                           # already in place
        if i > 0:
            flips.append(i + 1)
            arr[:i + 1] = arr[i::-1]
        flips.append(size)
        arr[:size] = arr[size - 1::-1]
    return flips
```

At most 2n − 3 flips for n ≥ 2: two per value placed, except that the last two values need at most one (the tests check the bound and the result); LeetCode accepts up to 10n. Finding the *fewest* flips for a given stack is NP-hard (Bulteau, Fertin and Rusu, 2011), and Gates and Papadimitriou (1979) showed that (5n + 5)/3 flips always suffice; in an interview, the simple method and its bound are the expected answer.

### 39g.14.6 Multiply Strings (43)

Digit i of the first number (0-based from the left) times digit j of the second lands on positions i + j and i + j + 1 of an (m + n)-digit result: add the product at i + j + 1, keep its last digit, carry the rest left:

```python
def multiply(num1, num2):
    """Multiply Strings (LC 43): digit i of num1 times digit j of num2 lands on positions i + j, i + j + 1."""
    if num1 == "0" or num2 == "0":
        return "0"
    out = [0] * (len(num1) + len(num2))
    for i in range(len(num1) - 1, -1, -1):
        for j in range(len(num2) - 1, -1, -1):
            total = int(num1[i]) * int(num2[j]) + out[i + j + 1]
            out[i + j + 1] = total % 10
            out[i + j] += total // 10
    return "".join(map(str, out)).lstrip("0")
```

O(m · n). In production Python, `str(int(a) * int(b))` is the answer; CPython switches to Karatsuba multiplication, O(n^1.585), for large numbers. Add Strings (415) is the warm-up.

### 39g.14.7 Perfect Rectangle (391)

Do axis-aligned rectangles tile a rectangle exactly? Two cheap conditions decide it: the areas add up to the bounding box's area, and among all rectangle corners only the box's four corners occur an odd number of times:

```python
def is_rectangle_cover(rectangles):
    """Perfect Rectangle (LC 391): the areas add up to the bounding box, and only its four corners appear
    an odd number of times among all rectangle corners."""
    x1 = min(r[0] for r in rectangles)
    y1 = min(r[1] for r in rectangles)
    x2 = max(r[2] for r in rectangles)
    y2 = max(r[3] for r in rectangles)
    area = 0
    odd = set()
    for a, b, c, d in rectangles:
        area += (c - a) * (d - b)
        odd ^= {(a, b), (a, d), (c, b), (c, d)}   # a corner seen an even number of times drops out
    return area == (x2 - x1) * (y2 - y1) and odd == {(x1, y1), (x1, y2), (x2, y1), (x2, y2)}
```

**Why they suffice.** In a two-dimensional difference array (39f.4), a rectangle adds +1 at two opposite corners and −1 at the other two, and summing over the quadrant below and to the left of a cell recovers how many rectangles cover it. Modulo 2 the signs vanish, so the corner points of odd multiplicity determine the parity of every cell's coverage. If they are exactly the box's corners, coverage is odd — at least 1 — inside the box and even outside, so the total area is at least the box's, with equality only when every cell is covered once. Conversely, an exact tiling has equal areas and pairs up every other corner point. O(n); the tests compare it with a cell-by-cell count on random tilings and perturbations of them.

**Interview line:** *"For rain water I start from the per-bar definition, then precompute both maxima, then notice that the smaller running maximum is already final — so two pointers suffice."*

## 39g.15 Interviews: how to talk about search and DP, practice, a plan, and questions

### 39g.15.1 Talking through a search or DP problem

The script of 39d.26 — restate, brute force, pattern, invariant, code, hand test, complexity, follow-up — applies with a sharper middle:

1. **Constraints.** The input size names the budget (39d.2): n ≤ 10 allows n!, n ≤ 20 allows 2ⁿ, n ≤ 500 allows n³, n ≤ 5,000 allows n², 10⁵ needs n log n.
2. **The decision tree.** What a node is, what the choices are, what makes a leaf: the brute force and its cost.
3. **Shared states.** What does the future depend on? That is the state; say the definition of `dp` aloud.
4. **Transition, base cases, answer** (`dp[n]`, or a maximum over i).
5. **Order and cost**: top-down if the order is unclear, bottom-up if the recursion would be deep; states times choices.
6. **Space and reconstruction**, if asked; then **a hand test** on the empty case and one example.

Compressed, for Coin Change II (518): *"Brute force decides coin by coin how many copies to take — exponential. The future depends only on which coins remain and how much is left, so `ways[i][a]` counts multisets of the first i coins summing to a: coin i unused, or used once more, `ways[i − 1][a] + ways[i][a − c]`, with `ways[i][0] = 1`. One row, amounts upward, since the take branch reads the current row: O(n · amount). For [1, 2, 5] and 5 it gives 4. If order mattered I would swap the loops."*

For greedy, state the rule and the two-sentence exchange argument, or the counterexample to the tempting rule. For search, say whether you need the shortest path (BFS) or all solutions (backtracking), whether marks are permanent or undone, and which pruning applies.

### 39g.15.2 Practice sets by section

| Section | Problems |
|---|---|
| 39g.2 Backtracking | 46, 51, 52, 37, 36 Valid Sudoku, 79, 131 Palindrome Partitioning, 93 Restore IP Addresses, 17 Letter Combinations of a Phone Number |
| 39g.3 Nine forms | 78, 90, 77, 216, 39, 40, 46, 47, 784 Letter Case Permutation, 1079 Letter Tile Possibilities, 996 Number of Squareful Arrays |
| 39g.4 Balls and boxes | 698, 473 Matchsticks to Square, 2305 Fair Distribution of Cookies, 1723 Find Minimum Time to Finish All Jobs, 22 |
| 39g.5 Islands | 200, 695, 1254, 1020, 1905, 694†, 711†, 130, 463, 417, 529 |
| 39g.6 BFS | 752, 773, 433, 127, 111, 1091, 1926, 909, 994, 542, 1162, 286†, 934 Shortest Bridge, 2290, 1368 |
| 39g.7 DP framework | 509 Fibonacci Number, 70, 322, 300, 673, 354, 931, 120, 115, 940 Distinct Subsequences II, 139, 140 |
| 39g.8 Strings | 72, 53, 918, 152, 1143, 583, 712, 1035, 1092, 718, 516, 1312, 5 Longest Palindromic Substring, 97, 132 Palindrome Partitioning II |
| 39g.9 Knapsack | 416, 494, 518, 377, 1049, 474, 322 |
| 39g.10 Grids and games | 64, 62, 120, 174, 514, 787, 10, 44, 887, 1884, 312, 1000, 486, 877 |
| 39g.11 Robbers and stocks | 198, 213, 337, 740, 121, 122, 123, 188, 309, 714 |
| 39g.12 Greedy | 435, 452, 253†, 1094, 55, 45, 134, 1024, 1326, 763 Partition Labels, 406 Queue Reconstruction by Height, 1235 |
| 39g.13 Math | 292, 319, 231, 191, 338, 268, 136, 372, 50, 1979 Find Greatest Common Divisor of Array, 204, 172, 793, 645, 384, 382, 398, 528, 470 Implement Rand10() Using Rand7(), 263, 264, 313, 1201 |
| 39g.14 Classics | 42, 11, 1288, 56, 986, 659, 846, 1296, 969, 43, 415, 391 |

### 39g.15.3 A three-week plan

| Week | Sections | How |
|---|---|---|
| 1 | Search, 39g.1–39g.6 | Type the backtracking skeleton and `bfs_shortest` from memory; draw each problem's decision tree before coding |
| 2 | DP, 39g.7–39g.11 | Write the definition of `dp` in one sentence before any code; solve top-down, then bottom-up, then in one row |
| 3 | Greedy, math, classics, 39g.12–39g.14; mixed review | Write the exchange argument or a counterexample for each greedy problem; two timed mocks on a plain editor |

The lab supports deliberate practice: delete a function's body in `frameworks_2.py`, rewrite it from its docstring, and run `python3 test_frameworks_2.py`; the randomized comparisons catch off-by-one errors, missing base cases and wrong loop directions. Keep an error log, and redo missed problems three days and one week later.

### 39g.15.4 Interview questions with model answers

**1. Backtracking versus DFS?** Both go depth first. Backtracking enumerates *paths*, so it undoes each choice and an element can appear on many paths; its cost is the number of paths. Graph DFS enumerates *vertices* with permanent marks, in O(V + E). Word search unmarks a cell on the way back but never reuses it within a path.

**2. Distinct permutations with duplicates — why `not used[i − 1]`?** Sort, and skip `nums[i]` when it equals `nums[i − 1]` and that copy is not on the path. Copies then enter the path in index order, and each distinct permutation has exactly one index-ordered labeling, so it appears once. The reverse rule is also correct but prunes later.

**3. Running time of a backtracking solution?** Nodes of the decision tree times work per node, plus copying the answers: about e · n! nodes with O(n) work for permutations, 2ⁿ for subsets. State the bound you can prove and what pruning buys.

**4. Why does BFS find shortest paths, and when not?** It dequeues states in order of distance, so a state is first discovered from one a step closer to the start and gets its true distance. That needs equal move costs; otherwise Dijkstra, or a deque for costs 0 and 1.

**5. When bidirectional BFS, and what goes wrong?** With one known goal, reversible moves and a large branching factor: about 2 · b^(d/2) states instead of bᵈ. Bugs: letting the two sides take turns after single states instead of whole layers (the first meeting can then be one step too long), not excluding forbidden states from the backward side, directed moves without a predecessor function.

**6. How do you recognize DP and choose the state?** The question asks for a count, an optimum or feasibility; the brute force makes a sequence of choices; different sequences reach the same situation. The state is the smallest description of that situation on which the rest depends. If you cannot say what `dp(state)` means in words, the state is wrong.

**7. Top-down or bottom-up?** Same states and transitions. Top-down follows the derivation and computes only reachable states; bottom-up avoids recursion limits and allows rolling arrays.

**8. Why do Coin Change II and Combination Sum IV loop differently?** Coins outside builds each multiset in one canonical order, so each is counted once; amounts outside sums over the last element, so orders differ. For a minimum the order is irrelevant.

**9. Why does Dungeon Game run backwards?** Forward, a path has two relevant numbers, health required and health left, and one number per cell cannot rank paths (a 2 × 4 grid makes the forward table answer 5 instead of 4). The health needed on entering a cell depends only on what follows, which is what a DP state needs.

**10. How do you prove a greedy algorithm correct? A failure?** Exchange: some optimal solution can be changed to make the greedy first choice without losing feasibility or value, and the rest is a smaller instance. Coins 1, 3, 4 with amount 6 defeat greedy (4 + 1 + 1 against 3 + 3); so does the 0-1 knapsack by value density.

**11. How do you test that a shuffle is uniform?** Inject the random source; for small n replay every draw sequence and check each order has probability exactly 1/n!; for larger n, a chi-square test with a fixed seed. And show why "swap with any index" cannot be uniform: nⁿ runs do not divide evenly among n! orders for n ≥ 3.

**12. Reservoir sampling, and why it is uniform?** Keep the first k; the i-th item replaces a random slot with probability k/i. An item entering at step i survives step j with probability (j − 1)/j; the product telescopes to i/n, giving k/n for every item, in one pass with O(k) memory.

**13. Why the last balloon in Burst Balloons?** When k bursts last between boundaries i and j, its neighbors are exactly i and j and the two sides never meet, so they are independent subproblems; the first balloon changes everyone's neighbors. The result is an O(n³) interval DP by width.

**14. Describe the stock state machine.** State after each day: purchases so far and whether a share is held. Not holding: rest or sell; holding: rest or buy, which uses a purchase and, with a cooldown, reads the not-holding state from further back. The six problems set k to 1, 2, k or unlimited, add a fee at the sale, or a one-day cooldown.

## Sources

- labuladong, *labuladong Algo Notes* (English edition), the topic map this chapter follows and extends: https://labuladong.online/en/algo/home/; table of contents in the repository's English branch: https://github.com/labuladong/fucking-algorithm/blob/english/README.md (checked October 2026). The chapters "Brute Force Search", "Dynamic Programming Algorithms" (with greedy) and "Other Common Techniques" were consulted for coverage and order.
- LeetCode problem set: https://leetcode.com/problemset/. Numbers, titles and Premium marks (†) checked in October 2026 against the doocs/leetcode index, which mirrors LeetCode's titles and lock marks: https://leetcode.doocs.org/en/ (repository https://github.com/doocs/leetcode).
- T. H. Cormen, C. E. Leiserson, R. L. Rivest and C. Stein, *Introduction to Algorithms*, 3rd ed., MIT Press, 2009: chapter 15 (dynamic programming; section 15.3 on optimal substructure, overlapping subproblems and the longest-simple-path counterexample) and chapter 16 (greedy algorithms; section 16.4, matroids).
- R. Bellman, *Dynamic Programming*, Princeton University Press, 1957; R. Bellman, "On a routing problem", *Quarterly of Applied Mathematics* 16(1), 1958, 87–90 (the round-by-round relaxation of 39g.10.4).
- R. Rado, "Note on independence functions", *Proceedings of the London Mathematical Society* (3) 7, 1957, 300–320; J. Edmonds, "Matroids and the greedy algorithm", *Mathematical Programming* 1, 1971, 127–136.
- D. Kozen and S. Zaks, "Optimal bounds for the change-making problem", *Theoretical Computer Science* 123(2), 1994, 377–388.
- D. Aldous and P. Diaconis, "Longest increasing subsequences: from patience sorting to the Baik–Deift–Johansson theorem", *Bulletin of the American Mathematical Society* 36(4), 1999, 413–432.
- D. S. Hirschberg, "A linear space algorithm for computing maximal common subsequences", *Communications of the ACM* 18(6), 1975, 341–343.
- D. E. Knuth, *The Art of Computer Programming*, Vol. 2, *Seminumerical Algorithms*, 3rd ed., Addison-Wesley, 1997: section 3.4.2 (Algorithm P, shuffling; Algorithm R, reservoir sampling) and section 4.5.3 (Euclid's algorithm and Lamé's bound).
- R. A. Fisher and F. Yates, *Statistical Tables for Biological, Agricultural and Medical Research*, Oliver and Boyd, 1938; R. Durstenfeld, "Algorithm 235: Random permutation", *Communications of the ACM* 7(7), 1964, 420; J. S. Vitter, "Random sampling with a reservoir", *ACM Transactions on Mathematical Software* 11(1), 1985, 37–57.
- G. H. Hardy and E. M. Wright, *An Introduction to the Theory of Numbers*, 6th ed., Oxford University Press, 2008 (Mertens' theorems, behind the sieve's O(n log log n)).
- D. E. Knuth, "Dancing links", 2000, https://arxiv.org/abs/cs/0011047; P. Norvig, "Solving Every Sudoku Puzzle", https://norvig.com/sudoku.html; Wikipedia, "Sudoku solving algorithms", https://en.wikipedia.org/wiki/Sudoku_solving_algorithms (the puzzle built against brute force, used in the tests).
- W. H. Gates and C. H. Papadimitriou, "Bounds for sorting by prefix reversal", *Discrete Mathematics* 27(1), 1979, 47–57; L. Bulteau, G. Fertin and I. Rusu, "Pancake flipping is hard", 2011, https://arxiv.org/abs/1111.0434.
- S. Selvin, "A problem in probability" (letter), *The American Statistician* 29(1), 1975, 67, and "On the Monty Hall problem" (letter), *The American Statistician* 29(3), 1975, 134; Wikipedia, "Monty Hall problem", https://en.wikipedia.org/wiki/Monty_Hall_problem (variants, including the host who opens a door at random); M. Bar-Hillel and R. Falk, "Some teasers concerning conditional probabilities", *Cognition* 11(2), 1982, 109–122.
- Python documentation, https://docs.python.org/3/library/: `itertools`, `functools.cache`, `math` (`isqrt`, `comb`, `lcm`), `int.bit_count`, `fractions`, `sys.setrecursionlimit`, and three-argument `pow` with modular inverses.
- Code: `labs/algorithm-frameworks/frameworks_2.py`, `test_frameworks_2.py` and `check_chapter_sync.py` in this repository (standard-library Python 3.10+; run `python3 test_frameworks_2.py`).
