"""Tests for frameworks_2.py (chapter 39g): fixed examples plus randomized checks against brute force.

Run:  python3 test_frameworks_2.py        (standard library only; prints one line per group)

Randomized algorithms are checked exactly, by replaying every possible sequence of random draws
(ScriptedRandom below), and statistically with a fixed seed.
"""
import sys

sys.dont_write_bytecode = True               # keep the lab folder free of __pycache__

import heapq
import itertools
import math
import random
import re
import time
from collections import Counter, deque
from fractions import Fraction
from functools import cache

import frameworks_2 as F

rng = random.Random(3907)


def check(name, fn):
    started = time.perf_counter()
    note = fn()
    extra = f"  ({note})" if note else ""
    print(f"ok  {name:<24} {time.perf_counter() - started:5.2f} s{extra}")


# ----------------------------------------------------------------------------- shared helpers


def as_sorted_tuples(lists):
    return sorted(tuple(x) for x in lists)


def is_subsequence(small, big):
    it = iter(big)
    return all(ch in it for ch in small)


def subsequences(seq):
    """Every subsequence by index set (duplicates included)."""
    return [tuple(seq[i] for i in idx) for r in range(len(seq) + 1)
            for idx in itertools.combinations(range(len(seq)), r)]


def random_grid(rows, cols, p_land=0.5):
    return [[1 if rng.random() < p_land else 0 for _ in range(cols)] for _ in range(rows)]


def components(grid, value=1):
    """Connected components of cells equal to value, as lists of cells (reference BFS)."""
    rows, cols = len(grid), len(grid[0])
    seen, comps = set(), []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == value and (r, c) not in seen:
                comp, queue = [], deque([(r, c)])
                seen.add((r, c))
                while queue:
                    x, y = queue.popleft()
                    comp.append((x, y))
                    for dx, dy in F.DIRS4:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == value and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            queue.append((nx, ny))
                comps.append(comp)
    return comps


class ScriptedRandom:
    """Plays back a script of draws (extending it with zeros) and records the size of each draw's range."""

    def __init__(self, script):
        self.script, self.pos, self.ranges = script, 0, []

    def randrange(self, a, b=None):
        lo, hi = (0, a) if b is None else (a, b)
        if self.pos == len(self.script):
            self.script.append(0)
        value = lo + self.script[self.pos]
        self.ranges.append(hi - lo)
        self.pos += 1
        return value


def all_runs(algorithm):
    """Yield (result, probability) for every possible run of a randomized algorithm (odometer over draws)."""
    script = []
    while True:
        source = ScriptedRandom(script)
        result = algorithm(source)
        del script[source.pos:]
        probability = Fraction(1)
        for size in source.ranges:
            probability /= size
        yield result, probability
        while script and script[-1] + 1 == source.ranges[len(script) - 1]:
            script.pop()
        if not script:
            return
        script[-1] += 1


def exact_distribution(algorithm):
    dist = Counter()
    for result, probability in all_runs(algorithm):
        dist[result] += probability
    return dist


# ----------------------------------------------------------------------------- 39g.1 search trees


def queens_tree_nodes(n):
    """Nodes visited by the row-by-row N-Queens search with O(1) attack checks (same tree as solve_n_queens)."""
    cols, diag, anti = set(), set(), set()
    nodes = 0

    def place(r):
        nonlocal nodes
        nodes += 1
        if r == n:
            return
        for c in range(n):
            if c in cols or r - c in diag or r + c in anti:
                continue
            cols.add(c)
            diag.add(r - c)
            anti.add(r + c)
            place(r + 1)
            cols.remove(c)
            diag.remove(r - c)
            anti.remove(r + c)

    place(0)
    return nodes


def combine_tree_nodes(n, k):
    """Nodes visited by combine(n, k) with its start-index loop bound, root included."""
    def visit(start, depth):
        if depth == k:
            return 1
        return 1 + sum(visit(x + 1, depth + 1) for x in range(start, n - (k - depth) + 2))

    return visit(1, 0)


def t_search_trees():
    assert F.all_paths_source_target([[1, 2], [3], [3], []]) == [[0, 1, 3], [0, 2, 3]]
    assert as_sorted_tuples(F.all_paths_source_target([[4, 3, 1], [3, 2, 4], [3], [4], []])) == as_sorted_tuples(
        [[0, 4], [0, 3, 4], [0, 1, 3, 4], [0, 1, 2, 3, 4], [0, 1, 4]])
    for _ in range(300):
        n = rng.randint(2, 7)
        graph = [[j for j in range(i + 1, n) if rng.random() < 0.5] for i in range(n)]   # edges go forward: a DAG
        brute = [[0, *mid, n - 1] for r in range(n - 1) for mid in itertools.permutations(range(1, n - 1), r)
                 if all(b in graph[a] for a, b in zip([0, *mid], [*mid, n - 1]))]
        assert as_sorted_tuples(F.all_paths_source_target(graph)) == as_sorted_tuples(brute)
    for n in range(0, 9):
        exact = sum(math.factorial(n) // math.factorial(j) for j in range(n + 1))
        assert F.permutation_tree_size(n) == exact
        if n >= 1:
            assert exact == math.floor(math.e * math.factorial(n))          # the tree has floor(e * n!) nodes
    for n in range(0, 11):                      # the loop bound leaves exactly C(n + 1, k) nodes in combine's tree
        for k in range(n + 1):
            assert combine_tree_nodes(n, k) == math.comb(n + 1, k) <= (k + 1) * math.comb(n, k)
    sizes = {n: queens_tree_nodes(n) for n in range(4, 9)}
    assert sizes == {4: 17, 5: 54, 6: 153, 7: 552, 8: 2057}
    assert F.permutation_tree_size(8) == 109601
    return "8-queens: 2,057 nodes with pruning vs 109,601 in the full permutation tree"


# ----------------------------------------------------------------------------- 39g.2 the framework


SUDOKU_PUZZLES = [
    "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
    "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9",
    "...8.1..........435............7.8........1...2..3....6......75..34........2..6..",
]


def sudoku_plain_mrv(board, stats):
    """Reference solver: branch on the fewest-options cell, no propagation (like chapter 39d's)."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empty = []
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == ".":
                empty.append((r, c))
            else:
                if v in rows[r] or v in cols[c] or v in boxes[r // 3 * 3 + c // 3]:
                    return False
                rows[r].add(v)
                cols[c].add(v)
                boxes[r // 3 * 3 + c // 3].add(v)

    def options(r, c):
        used = rows[r] | cols[c] | boxes[r // 3 * 3 + c // 3]
        return [d for d in "123456789" if d not in used]

    def fill():
        stats["nodes"] += 1
        if not empty:
            return True
        best_i, best = 0, None
        for i, (r, c) in enumerate(empty):
            opts = options(r, c)
            if best is None or len(opts) < len(best):
                best_i, best = i, opts
                if len(opts) <= 1:
                    break
        r, c = empty[best_i]
        empty[best_i] = empty[-1]
        empty.pop()
        b = r // 3 * 3 + c // 3
        for d in best:
            board[r][c] = d
            rows[r].add(d)
            cols[c].add(d)
            boxes[b].add(d)
            if fill():
                return True
            rows[r].remove(d)
            cols[c].remove(d)
            boxes[b].remove(d)
        board[r][c] = "."
        empty.append((r, c))
        return False

    return fill()


def sudoku_valid_completion(grid, puzzle):
    digits = list("123456789")
    return (all(sorted(row) == digits for row in grid)
            and all(sorted(grid[r][c] for r in range(9)) == digits for c in range(9))
            and all(sorted(grid[br + i][bc + j] for i in range(3) for j in range(3)) == digits
                    for br in (0, 3, 6) for bc in (0, 3, 6))
            and all(puzzle[i] in (".", grid[i // 9][i % 9]) for i in range(81)))


def random_solved_sudoku():
    base = [[(r * 3 + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]   # a valid grid
    rows = [b * 3 + r for b in rng.sample(range(3), 3) for r in rng.sample(range(3), 3)]
    cols = [s * 3 + c for s in rng.sample(range(3), 3) for c in rng.sample(range(3), 3)]
    relabel = rng.sample(range(1, 10), 9)
    return [[str(relabel[base[r][c] - 1]) for c in cols] for r in rows]


def t_backtracking_framework():
    for n in range(0, 7):
        nums = rng.sample(range(-9, 10), n)
        assert as_sorted_tuples(F.permute(nums)) == sorted(itertools.permutations(nums))
    for n in range(0, 9):                       # boards against brute force over column permutations
        brute = sorted(tuple("." * c + "Q" + "." * (n - 1 - c) for c in perm)
                       for perm in itertools.permutations(range(n))
                       if len({r - c for r, c in enumerate(perm)}) == n and len({r + c for r, c in enumerate(perm)}) == n)
        assert sorted(tuple(b) for b in F.solve_n_queens(n)) == brute
    known = [1, 1, 0, 0, 2, 10, 4, 40, 92, 352, 724, 2680]
    assert [F.total_n_queens_bitmask(n) for n in range(12)] == known
    assert all(F.total_n_queens_bitmask(n) == len(F.solve_n_queens(n)) for n in range(10))
    plain_nodes, prop_nodes = [], []
    for puzzle in SUDOKU_PUZZLES:
        grid = [list(puzzle[r * 9:r * 9 + 9]) for r in range(9)]
        stats = {}
        assert F.solve_sudoku_propagate(grid, stats) and sudoku_valid_completion(grid, puzzle)
        ref = [list(puzzle[r * 9:r * 9 + 9]) for r in range(9)]
        ref_stats = {"nodes": 0}
        assert sudoku_plain_mrv(ref, ref_stats)
        plain_nodes.append(ref_stats["nodes"])
        prop_nodes.append(stats["nodes"])
    assert plain_nodes[1] > 10_000 and plain_nodes[2] > 10_000 and max(prop_nodes) <= 10
    solved = unsolvable = 0
    for trial in range(80):
        full = random_solved_sudoku()
        keep = set(rng.sample(range(81), rng.randint(22, 40)))
        puzzle = [full[i // 9][i % 9] if i in keep else "." for i in range(81)]
        if trial % 2:                          # change one given without an immediate clash
            i = rng.choice(sorted(keep))
            r, c = divmod(i, 9)
            seen = {puzzle[j] for j in range(81) if j != i and (j // 9 == r or j % 9 == c or
                    (j // 27 == r // 3 and j % 9 // 3 == c // 3))}
            choices = [d for d in "123456789" if d not in seen and d != puzzle[i]]
            if choices:
                puzzle[i] = rng.choice(choices)
        puzzle = "".join(puzzle)
        grid = [list(puzzle[r * 9:r * 9 + 9]) for r in range(9)]
        ref = [row[:] for row in grid]
        answer = F.solve_sudoku_propagate(grid)
        assert answer == sudoku_plain_mrv(ref, {"nodes": 0})
        if answer:
            assert sudoku_valid_completion(grid, puzzle)
            solved += 1
        else:
            assert "".join("".join(row) for row in grid) == puzzle      # every placement was undone
            unsolvable += 1
    clash = [list("11" + "." * 7)] + [["."] * 9 for _ in range(8)]
    assert F.solve_sudoku_propagate(clash) is False
    assert solved > 30 and unsolvable > 5
    return (f"hard Sudoku search nodes, plain MRV {plain_nodes[1]:,} and {plain_nodes[2]:,} vs propagation "
            f"{prop_nodes[1]} and {prop_nodes[2]}; {solved} random solved, {unsolvable} proved unsolvable")


# ----------------------------------------------------------------------------- 39g.3 the nine forms


def permute_unique_nodes(nums, left_first):
    """Node count of the LC 47 search with the 'not used[i - 1]' rule (left_first) or the 'used[i - 1]' rule."""
    nums = sorted(nums)
    used = [False] * len(nums)
    depth = nodes = 0
    leaves = []

    def backtrack():
        nonlocal nodes, depth
        nodes += 1
        if depth == len(nums):
            leaves.append(1)
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i - 1] and (not used[i - 1] if left_first else used[i - 1]):
                continue
            used[i] = True
            depth += 1
            backtrack()
            depth -= 1
            used[i] = False

    backtrack()
    return nodes, len(leaves)


def t_nine_forms():
    for _ in range(300):
        n = rng.randint(0, 7)
        distinct = rng.sample(range(1, 15), n)
        assert as_sorted_tuples(F.subsets_backtrack(distinct)) == sorted(
            c for r in range(n + 1) for c in itertools.combinations(distinct, r))
        k = rng.randint(0, n)
        assert F.combine(n, k) == [list(c) for c in itertools.combinations(range(1, n + 1), k)]
        kk, target = rng.randint(1, 5), rng.randint(1, 40)
        assert F.combination_sum3(kk, target) == [list(c) for c in itertools.combinations(range(1, 10), kk)
                                                  if sum(c) == target]
        multiset = [rng.randint(1, 4) for _ in range(rng.randint(0, 7))]
        assert as_sorted_tuples(F.subsets_with_dup_backtrack(multiset)) == sorted(
            {tuple(sorted(c)) for r in range(len(multiset) + 1) for c in itertools.combinations(multiset, r)})
        target = rng.randint(1, 12)
        result = F.combination_sum2(multiset, target)
        assert as_sorted_tuples(result) == sorted(
            {tuple(sorted(c)) for r in range(len(multiset) + 1) for c in itertools.combinations(multiset, r)
             if sum(c) == target})
        assert len(result) == len({tuple(x) for x in result})              # no duplicates generated
        small = multiset[:6]
        expected = sorted(set(itertools.permutations(small)))
        assert as_sorted_tuples(F.permute_unique(small)) == expected
        assert as_sorted_tuples(F.permute_unique_counter(small)) == expected
        assert len(F.permute_unique(small)) == len(expected)
        pool = rng.sample(range(1, 9), rng.randint(0, 4))
        k = rng.randint(0, 4)
        assert as_sorted_tuples(F.combine_with_reuse(pool, k)) == sorted(
            itertools.combinations_with_replacement(pool, k))
        assert as_sorted_tuples(F.permute_with_reuse(pool, k)) == sorted(itertools.product(pool, repeat=k))
    for _ in range(100):                        # 'not used[i - 1]' never visits more nodes, same leaves
        nums = [rng.randint(1, 3) for _ in range(rng.randint(0, 7))]
        left, right = permute_unique_nodes(nums, True), permute_unique_nodes(nums, False)
        assert left[1] == right[1] and left[0] <= right[0]
    assert permute_unique_nodes([2] * 6, True) == (7, 1) and permute_unique_nodes([2] * 6, False) == (210, 1)
    return "all nine forms equal their itertools counterparts"


# ----------------------------------------------------------------------------- 39g.4 ball and box


def partition_balls_plain(nums, k):
    """Ball view without the symmetry rule, for node counts."""
    target = sum(nums) // k
    nums = sorted(nums, reverse=True)
    buckets = [0] * k
    nodes = 0

    def place(i):
        nonlocal nodes
        nodes += 1
        if i == len(nums):
            return True
        for b in range(k):
            if buckets[b] + nums[i] <= target:
                buckets[b] += nums[i]
                if place(i + 1):
                    return True
                buckets[b] -= nums[i]
        return False

    return place(0), nodes


def partition_buckets_plain(nums, k):
    """Bucket view without the symmetry rule and without the memo, for node counts."""
    target = sum(nums) // k
    nums = sorted(nums, reverse=True)
    nodes = 0

    def fill(done, used, current, start):
        nonlocal nodes
        nodes += 1
        if done == k:
            return True
        if current == target:
            return fill(done + 1, used, 0, 0)
        for i in range(start, len(nums)):
            if not (used >> i) & 1 and current + nums[i] <= target:
                if fill(done, used | (1 << i), current + nums[i], i + 1):
                    return True
        return False

    return fill(0, 0, 0, 0), nodes


def t_ball_and_box():
    for n in range(0, 7):
        nums = rng.sample(range(10), n)
        assert as_sorted_tuples(F.permute_by_placing(nums)) == sorted(itertools.permutations(nums))
    assert F.can_partition_k_balls([4, 3, 2, 3, 5, 2, 1], 4) and not F.can_partition_k_balls([1, 2, 3, 4], 3)
    for _ in range(300):                        # brute force: every assignment of numbers to buckets
        n, k = rng.randint(1, 7), rng.randint(1, 3)
        nums = [rng.randint(1, 6) for _ in range(n)]
        brute = any(len(set(sum(x for x, b in zip(nums, assign) if b == j) for j in range(k))) == 1
                    for assign in itertools.product(range(k), repeat=n))
        assert F.can_partition_k_balls(nums, k) == brute
        assert F.can_partition_k_buckets(nums, k) == brute
        assert F.can_partition_k_dp(nums, k) == brute
    totals = Counter()
    seeded = random.Random(698)                 # its own seed: the counts printed below do not depend on other tests
    for _ in range(24):                         # harder instances whose answer is "no"
        n, k = seeded.choice([(10, 3), (12, 3), (12, 4), (13, 4)])
        while True:
            nums = [seeded.randint(1, 12) for _ in range(n)]
            if sum(nums) % k == 0 and max(nums) <= sum(nums) // k and not F.can_partition_k_dp(nums, k):
                break
        stats_balls, stats_buckets = {}, {}
        assert not F.can_partition_k_balls(nums, k, stats_balls)
        assert not F.can_partition_k_buckets(nums, k, stats_buckets)
        totals["balls, plain"] += partition_balls_plain(nums, k)[1]
        totals["balls, symmetry rule"] += stats_balls["nodes"]
        totals["buckets, plain"] += partition_buckets_plain(nums, k)[1]
        totals["buckets, symmetry rule and memo"] += stats_buckets["nodes"]
    assert totals["balls, symmetry rule"] * 10 < totals["balls, plain"]
    assert totals["buckets, symmetry rule and memo"] * 10 < totals["buckets, plain"]
    for n in range(0, 8):
        brute = sum(1 for s in itertools.product("()", repeat=2 * n)
                    if all(s[:i].count("(") >= s[:i].count(")") for i in range(2 * n + 1)) and s.count("(") == n)
        assert F.count_balanced(n) == brute == math.comb(2 * n, n) // (n + 1)
    assert F.count_balanced(30) == math.comb(60, 30) // 31
    return "nodes on 24 'no' instances: " + ", ".join(f"{name} {count:,}" for name, count in totals.items())


# ----------------------------------------------------------------------------- 39g.5 islands


def island_signature(cells, back_markers):
    """The DFS walk of num_distinct_islands for a set of cells, with or without the 'b' markers."""
    cells, seen, out = set(cells), set(), []

    def walk(r, c, step):
        if (r, c) not in cells or (r, c) in seen:
            return
        seen.add((r, c))
        out.append(step)
        for dr, dc, name in ((1, 0, "d"), (-1, 0, "u"), (0, 1, "r"), (0, -1, "l")):
            walk(r + dr, c + dc, name)
        if back_markers:
            out.append("b")

    walk(*min(cells), "o")
    return "".join(out)


def t_islands():
    gamma, ell = {(0, 0), (1, 0), (0, 1)}, {(0, 0), (1, 0), (1, 1)}
    assert island_signature(gamma, False) == island_signature(ell, False) == "odr"   # a collision
    assert island_signature(gamma, True) == "odbrbb" and island_signature(ell, True) == "odrbbb"
    grid = [[1, 1, 0], [1, 0, 0], [0, 0, 0], [1, 1, 0], [0, 1, 0]]   # the two shapes, stacked
    assert F.num_distinct_islands([row[:] for row in grid]) == 2
    assert F.num_enclaves([[0, 0, 0, 0], [1, 0, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) == 3
    assert F.count_sub_islands([[1, 1, 1, 0, 0], [0, 1, 1, 1, 1], [0, 0, 0, 0, 0], [1, 0, 0, 0, 0], [1, 1, 0, 1, 1]],
                               [[1, 1, 1, 0, 0], [0, 0, 1, 1, 1], [0, 1, 0, 0, 0], [1, 0, 1, 1, 0], [0, 1, 0, 1, 0]]) == 3
    for _ in range(400):
        rows, cols = rng.randint(1, 7), rng.randint(1, 7)
        grid = random_grid(rows, cols, rng.choice([0.3, 0.5, 0.7]))
        comps = components(grid)
        work = [row[:] for row in grid]
        sizes = sorted(F.sink_island(work, r, c) for r, c in (comp[0] for comp in comps))
        assert sizes == sorted(map(len, comps)) and not any(map(any, work))
        border = lambda cell: cell[0] in (0, rows - 1) or cell[1] in (0, cols - 1)
        enclosed = sum(len(comp) for comp in comps if not any(border(cell) for cell in comp))
        assert F.num_enclaves([row[:] for row in grid]) == enclosed
        other = random_grid(rows, cols, 0.6)
        subs = sum(1 for comp in comps if all(other[r][c] == 1 for r, c in comp))
        assert F.count_sub_islands(other, [row[:] for row in grid]) == subs
        shapes = {frozenset((r - comp[0][0], c - comp[0][1]) for r, c in comp)
                  for comp in (sorted(cs) for cs in comps)}
        assert F.num_distinct_islands([row[:] for row in grid]) == len(shapes)
    if sys.getrecursionlimit() == 1000:         # the recursive fill is as deep as the island is large
        try:
            F.sink_island([[1] * 32 for _ in range(32)], 0, 0)
            raise AssertionError("expected RecursionError")
        except RecursionError:
            pass
    return "without the backtrack marker, the shapes {(0,0),(1,0),(0,1)} and {(0,0),(1,0),(1,1)} both serialize as 'odr'"


# ----------------------------------------------------------------------------- 39g.6 BFS


def reference_distances(adjacency, source):
    dist = {source: 0}
    frontier = [source]
    while frontier:
        nxt = []
        for u in frontier:
            for v in adjacency[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    nxt.append(v)
        frontier = nxt
    return dist


def bidirectional_by_state(start, goal, neighbors):
    """A tempting but wrong variant: the two searches take turns after every state, not after every layer."""
    if start == goal:
        return 0
    dist, queues, side = [{start: 0}, {goal: 0}], [deque([start]), deque([goal])], 0
    while queues[0] and queues[1]:
        near, far = dist[side], dist[1 - side]
        state = queues[side].popleft()
        for nxt in neighbors(state):
            if nxt in far:
                return near[state] + 1 + far[nxt]
            if nxt not in near:
                near[nxt] = near[state] + 1
                queues[side].append(nxt)
        side = 1 - side
    return -1


def t_bfs():
    for _ in range(400):                        # random undirected graphs
        n = rng.randint(1, 12)
        adjacency = {u: set() for u in range(n)}
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.25:
                    adjacency[u].add(v)
                    adjacency[v].add(u)
        s, t = rng.randrange(n), rng.randrange(n)
        expected = reference_distances(adjacency, s).get(t, -1)
        nbrs = lambda u: sorted(adjacency[u])
        assert F.bfs_shortest(s, t, nbrs)[0] == expected
        assert F.bidirectional_bfs(s, t, nbrs)[0] == expected
    edges = [(0, 1), (0, 3), (1, 2), (2, 4), (3, 4), (4, 5)]   # 0-3-4-5 is shortest; 0-1-2-4-5 is found first
    adjacency = {u: sorted({b for a, b in edges if a == u} | {a for a, b in edges if b == u}) for u in range(6)}
    assert F.bidirectional_bfs(0, 5, adjacency.get)[0] == 3 and bidirectional_by_state(0, 5, adjacency.get) == 4
    dead = ["0201", "0101", "0102", "1212", "2002"]
    assert F.open_lock(dead, "0202") == F.open_lock(dead, "0202", True) == 6
    assert F.open_lock(["8888"], "0009") == 1
    ring = ["8887", "8889", "8878", "8898", "8788", "8988", "7888", "9888"]
    assert F.open_lock(ring, "8888") == F.open_lock(ring, "8888", True) == -1
    assert F.open_lock(["0000"], "8888") == -1 and F.open_lock([], "0000") == 0
    plain_total = bi_total = 0
    seeded = random.Random(752)                 # its own seed: the counts printed below do not depend on other tests
    for _ in range(60):
        deadends = {"".join(seeded.choice("0123456789") for _ in range(4)) for _ in range(seeded.randint(0, 400))}
        target = "".join(seeded.choice("0123456789") for _ in range(4))
        deadends.discard(target)
        deadends.discard("0000")
        blocked = set(deadends)

        def turns(state):
            for i in range(4):
                for step in (1, -1):
                    nxt = state[:i] + str((int(state[i]) + step) % 10) + state[i + 1:]
                    if nxt not in blocked:
                        yield nxt

        graph = {}
        frontier = ["0000"]
        dist = {"0000": 0}
        while frontier:                         # reference: plain level-by-level BFS
            nxt = []
            for u in frontier:
                for v in turns(u):
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        nxt.append(v)
            frontier = nxt
        expected = dist.get(target, -1)
        a, plain = F.bfs_shortest("0000", target, turns)
        b, bi = F.bidirectional_bfs("0000", target, turns)
        assert a == b == expected == F.open_lock(sorted(deadends), target)
        plain_total += plain
        bi_total += bi
    assert bi_total * 3 < plain_total
    goal_dist = {}                              # sliding puzzle: every one of the 720 boards
    frontier, goal_dist["123450"] = ["123450"], 0
    while frontier:
        nxt = []
        for state in frontier:
            zero = state.index("0")
            for j in F.SLIDE_NEIGHBORS[zero]:
                cells = list(state)
                cells[zero], cells[j] = cells[j], cells[zero]
                child = "".join(cells)
                if child not in goal_dist:
                    goal_dist[child] = goal_dist[state] + 1
                    nxt.append(child)
        frontier = nxt
    assert len(goal_dist) == 360 and max(goal_dist.values()) == 21
    for perm in itertools.permutations(range(6)):
        board = [list(perm[:3]), list(perm[3:])]
        key = "".join(map(str, perm))
        assert F.is_solvable_2x3(board) == (key in goal_dist)
    for perm in rng.sample(list(itertools.permutations(range(6))), 120):
        board = [list(perm[:3]), list(perm[3:])]
        assert F.sliding_puzzle(board) == goal_dist.get("".join(map(str, perm)), -1)
    assert F.sliding_puzzle([[1, 2, 3], [4, 0, 5]]) == 1 and F.sliding_puzzle([[4, 1, 2], [5, 0, 3]]) == 5
    assert F.min_mutation("AACCGGTT", "AACCGGTA", ["AACCGGTA"]) == 1
    assert F.min_mutation("AACCGGTT", "AAACGGTA", ["AACCGGTA", "AACCGCTA", "AAACGGTA"]) == 2
    for _ in range(300):
        length = rng.randint(1, 4)
        start = "".join(rng.choice("ACGT") for _ in range(length))
        bank = list({"".join(rng.choice("ACGT") for _ in range(length)) for _ in range(rng.randint(0, 25))})
        end = rng.choice(bank + [start]) if bank else start
        nodes = [start] + [g for g in bank if g != start]
        adjacency = {g: {h for h in bank if sum(x != y for x, y in zip(g, h)) == 1} for g in nodes}
        assert F.min_mutation(start, end, bank) == reference_distances(adjacency, start).get(end, -1)
    assert F.oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4
    assert F.oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1 and F.oranges_rotting([[0, 2]]) == 0
    for _ in range(300):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        grid = [[rng.choice([0, 1, 1, 2]) for _ in range(cols)] for _ in range(rows)]
        sim, minutes = [row[:] for row in grid], 0
        while True:                             # reference: simulate minute by minute
            rot = [(r, c) for r in range(rows) for c in range(cols) if sim[r][c] == 1 and any(
                0 <= r + dr < rows and 0 <= c + dc < cols and sim[r + dr][c + dc] == 2 for dr, dc in F.DIRS4)]
            if not rot:
                break
            for r, c in rot:
                sim[r][c] = 2
            minutes += 1
        expected = -1 if any(1 in row for row in sim) else minutes
        assert F.oranges_rotting([row[:] for row in grid]) == expected
        mat = [[rng.choice([0, 1, 1]) for _ in range(cols)] for _ in range(rows)]
        mat[rng.randrange(rows)][rng.randrange(cols)] = 0
        zeros = [(r, c) for r in range(rows) for c in range(cols) if mat[r][c] == 0]
        assert F.update_matrix(mat) == [[min(abs(r - a) + abs(c - b) for a, b in zeros) for c in range(cols)]
                                        for r in range(rows)]
        obstacles = [[rng.choice([0, 1]) for _ in range(cols)] for _ in range(rows)]
        obstacles[0][0] = obstacles[-1][-1] = 0
        dist = {(0, 0): 0}                      # reference: Dijkstra with a heap
        heap = [(0, 0, 0)]
        while heap:
            d, r, c = heapq.heappop(heap)
            if d > dist[(r, c)]:
                continue
            for dr, dc in F.DIRS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and d + obstacles[nr][nc] < dist.get((nr, nc), math.inf):
                    dist[(nr, nc)] = d + obstacles[nr][nc]
                    heapq.heappush(heap, (dist[(nr, nc)], nr, nc))
        assert F.minimum_obstacles(obstacles) == dist[(rows - 1, cols - 1)]
    return (f"lock: plain BFS expanded {plain_total:,} states, bidirectional {bi_total:,} "
            f"({plain_total / bi_total:.1f}x fewer); 2x3 puzzle: 360 of 720 boards solvable, hardest 21 moves")


# ----------------------------------------------------------------------------- 39g.7 the DP framework


def t_dp_framework():
    assert [F.fib_naive(n) for n in range(20)] == [F.fib_memo(n) for n in range(20)] == \
        [F.fib_table(n) for n in range(20)] == [F.fib(n) for n in range(20)]
    assert F.fib(90) == F.fib_memo(90) == F.fib_table(90) == 2880067194370816120
    calls = 0

    def counted(n):                             # the naive recursion makes 2 F(n + 1) - 1 calls
        nonlocal calls
        calls += 1
        return n if n < 2 else counted(n - 1) + counted(n - 2)

    counted(25)
    assert calls == 2 * F.fib(26) - 1 and 2 * F.fib(31) - 1 == 2_692_537
    assert F.coin_change_table([1, 2, 5], 11) == 3 and F.coin_change_memo([2], 3) == -1
    assert F.coin_change_brute([1], 0) == 0
    if sys.getrecursionlimit() == 1000:         # each memo level costs more than one frame: amount 1,000 is too deep
        try:
            F.coin_change_memo([1, 2, 5], 1000)
            raise AssertionError("expected RecursionError")
        except RecursionError:
            pass
        assert F.coin_change_table([1, 2, 5], 1000) == 200
    for _ in range(300):
        coins = rng.sample(range(1, 12), rng.randint(1, 4))
        amount = rng.randint(0, 18)
        brute = min((len(c) for r in range(amount + 1) for c in itertools.combinations_with_replacement(coins, r)
                     if sum(c) == amount), default=-1) if amount <= 12 else None
        a, b, c = F.coin_change_brute(coins, amount), F.coin_change_memo(coins, amount), F.coin_change_table(coins, amount)
        assert a == b == c and (brute is None or a == brute)
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(0, 9))]
        best = max((r for r in range(len(nums) + 1) for idx in itertools.combinations(range(len(nums)), r)
                    if all(nums[idx[i]] < nums[idx[i + 1]] for i in range(r - 1))), default=0)
        assert F.length_of_lis_quadratic(nums) == best
        lis = F.longest_increasing_subsequence(nums)
        assert len(lis) == best and all(x < y for x, y in zip(lis, lis[1:])) and is_subsequence(lis, nums)
        envelopes = [[rng.randint(1, 6), rng.randint(1, 6)] for _ in range(rng.randint(0, 8))]
        ordered = sorted(envelopes)
        chain = [1] * len(ordered)              # reference: O(n^2) chain DP with both sides strict
        for i in range(len(ordered)):
            for j in range(i):
                if ordered[j][0] < ordered[i][0] and ordered[j][1] < ordered[i][1]:
                    chain[i] = max(chain[i], chain[j] + 1)
        assert F.max_envelopes(envelopes) == max(chain, default=0)
        n = rng.randint(1, 5)
        matrix = [[rng.randint(-20, 20) for _ in range(n)] for _ in range(n)]
        brute = min(sum(matrix[r][c] for r, c in enumerate(cols))
                    for cols in itertools.product(range(n), repeat=n)
                    if all(abs(a - b) <= 1 for a, b in zip(cols, cols[1:])))
        assert F.min_falling_path_sum(matrix) == F.min_falling_path_sum_memo(matrix) == brute
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 9)))
        t = "".join(rng.choice("ab") for _ in range(rng.randint(0, 4)))
        brute = sum(1 for idx in itertools.combinations(range(len(s)), len(t)) if "".join(s[i] for i in idx) == t)
        assert F.num_distinct(s, t) == F.num_distinct_by_target(s, t) == brute
        words = list({"".join(rng.choice("ab") for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(1, 5))})
        s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 10)))
        splits = []
        for cuts in itertools.product([False, True], repeat=len(s) - 1):   # brute force: every way to cut s
            pieces, last = [], 0
            for i, cut in enumerate(cuts, 1):
                if cut:
                    pieces.append(s[last:i])
                    last = i
            pieces.append(s[last:])
            if all(p in words for p in pieces):
                splits.append(" ".join(pieces))
        assert F.word_break(s, words) == bool(splits)
        assert sorted(F.word_break_all(s, words)) == sorted(splits)
    assert F.word_break("leetcode", ["leet", "code"]) and not F.word_break("catsandog", ["cats", "dog", "sand", "and", "cat"])
    assert sorted(F.word_break_all("catsanddog", ["cat", "cats", "and", "sand", "dog"])) == ["cat sand dog", "cats and dog"]
    assert F.longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18]) == [2, 3, 7, 18]
    assert F.max_envelopes([[5, 4], [6, 4], [6, 7], [2, 3]]) == 3
    return "Fibonacci, coin change, LIS, envelopes, falling paths, distinct subsequences, word break"


# ----------------------------------------------------------------------------- 39g.8 subsequence and string DP


def apply_script(word, ops):
    out, i = [], 0
    for op in ops:
        if op[0] == "keep":
            assert word[i] == op[1]
            out.append(word[i])
            i += 1
        elif op[0] == "replace":
            assert word[i] == op[1]
            out.append(op[2])
            i += 1
        elif op[0] == "delete":
            assert word[i] == op[1]
            i += 1
        else:
            out.append(op[1])
    assert i == len(word)
    return "".join(out)


def t_subsequence_dp():
    assert F.edit_script("horse", "ros")[0] == 3 and F.edit_script("intention", "execution")[0] == 5
    assert F.max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert F.longest_common_subsequence("abcde", "ace") == 3 and F.min_delete_steps("sea", "eat") == 2
    assert F.minimum_delete_sum("sea", "eat") == 231 and F.minimum_delete_sum("delete", "leet") == 403
    assert F.minimum_delete_sum("ab", "ba") == 194                          # keep "b", not "a"
    keep_z, keep_a = 2 * 5 * ord("a"), 2 * 4 * ord("z")    # delete the a's (keep "zzzz") or the z's (keep "aaaaa")
    assert F.longest_common_subsequence("zzzzaaaaa", "aaaaazzzz") == 5 and keep_z == 970 < keep_a == 976
    assert F.minimum_delete_sum("zzzzaaaaa", "aaaaazzzz") == keep_z         # the best string to keep is not an LCS
    assert F.longest_palindrome_subseq("bbbab") == 4 and F.min_insertions("mbadm") == 2
    assert F.min_insertions("leetcode") == 5
    for _ in range(400):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 7)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 7)))

        @cache
        def edit(i, j):                         # reference: top-down recursion
            if i == len(a) or j == len(b):
                return len(a) - i + len(b) - j
            if a[i] == b[j]:
                return edit(i + 1, j + 1)
            return 1 + min(edit(i + 1, j), edit(i, j + 1), edit(i + 1, j + 1))

        distance, ops = F.edit_script(a, b)
        assert distance == edit(0, 0) == sum(op[0] != "keep" for op in ops)
        assert apply_script(a, ops) == b
        common = [sub for sub in set(subsequences(a)) if is_subsequence(sub, b)]
        assert F.longest_common_subsequence(a, b) == max(map(len, common))
        assert F.min_delete_steps(a, b) == len(a) + len(b) - 2 * max(map(len, common))
        weight = lambda seq: sum(map(ord, seq))
        assert F.minimum_delete_sum(a, b) == weight(a) + weight(b) - 2 * max(map(weight, common))
        nums = [rng.randint(-10, 10) for _ in range(rng.randint(1, 12))]
        brute = max(sum(nums[i:j]) for i in range(len(nums)) for j in range(i + 1, len(nums) + 1))
        assert F.max_subarray(nums) == F.max_subarray_prefix(nums) == F.max_subarray_divide(nums) == brute
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 9)))
        palindromes = [sub for sub in subsequences(s) if sub == sub[::-1]]
        assert F.longest_palindrome_subseq(s) == max(map(len, palindromes))

        @cache
        def insertions(i, j):                   # reference: insert directly, no LPS
            if i >= j:
                return 0
            if s[i] == s[j]:
                return insertions(i + 1, j - 1)
            return 1 + min(insertions(i + 1, j), insertions(i, j - 1))

        assert F.min_insertions(s) == insertions(0, len(s) - 1)
    return "edit scripts replay to the target; LCS, 583, 712, 516, 1312 against subsequence enumeration"


# ----------------------------------------------------------------------------- 39g.9 knapsack


def t_knapsack():
    assert F.knapsack_items([1, 2, 3, 5], [1, 6, 10, 16], 7) == (22, [1, 3])
    assert F.change(5, [1, 2, 5]) == 4 and F.change(3, [2]) == 0 and F.change(10, [10]) == 1
    assert F.combination_sum4([1, 2, 3], 4) == 7 and F.combination_sum4([9], 3) == 0
    assert F.change(3, [1, 2]) == 2 and F.combination_sum4([1, 2], 3) == 3   # {1,1,1}, {1,2} vs 1+1+1, 1+2, 2+1
    assert F.find_target_sum_ways_memo([1, 1, 1, 1, 1], 3) == 5
    for _ in range(300):
        n = rng.randint(0, 7)
        weights = [rng.randint(0, 6) for _ in range(n)]
        values = [rng.randint(0, 10) for _ in range(n)]
        capacity = rng.randint(0, 15)
        best = max(sum(values[i] for i in s) for r in range(n + 1) for s in itertools.combinations(range(n), r)
                   if sum(weights[i] for i in s) <= capacity)
        total, chosen = F.knapsack_items(weights, values, capacity)
        assert total == best == sum(values[i] for i in chosen) and sum(weights[i] for i in chosen) <= capacity
        assert len(set(chosen)) == len(chosen)
        nums = [rng.randint(1, 9) for _ in range(rng.randint(0, 8))]
        sums = {sum(c) for r in range(len(nums) + 1) for c in itertools.combinations(nums, r)}
        assert F.can_partition_bitset(nums) == (sum(nums) % 2 == 0 and sum(nums) // 2 in sums)
        coins = rng.sample(range(1, 8), rng.randint(1, 3))
        amount = rng.randint(0, 14)
        brute = sum(1 for r in range(amount + 1) for c in itertools.combinations_with_replacement(coins, r)
                    if sum(c) == amount)
        assert F.change(amount, coins) == brute

        @cache
        def sequences(rest):                    # reference: count ordered sequences directly
            return 1 if rest == 0 else sum(sequences(rest - x) for x in coins if x <= rest)

        assert F.combination_sum4(coins, amount) == sequences(amount)
        nums = [rng.randint(0, 5) for _ in range(rng.randint(1, 8))]
        target = rng.randint(-8, 8)
        brute = sum(1 for signs in itertools.product((1, -1), repeat=len(nums))
                    if sum(s * x for s, x in zip(signs, nums)) == target)
        assert F.find_target_sum_ways_memo(nums, target) == brute
        n = rng.randint(0, 4)
        weights = [rng.randint(0, 5) for _ in range(n)]
        values = [rng.randint(0, 9) for _ in range(n)]
        counts = [rng.randint(0, 5) for _ in range(n)]
        capacity = rng.randint(0, 16)
        brute = max(sum(t * v for t, v in zip(take, values)) for take in itertools.product(*(range(k + 1) for k in counts))
                    if sum(t * w for t, w in zip(take, weights)) <= capacity)
        assert F.bounded_knapsack(weights, values, counts, capacity) == brute
    return "0-1 with reconstruction, bitset subset sum, 518 vs 377 loop order, 494, bounded by binary splitting"


# ----------------------------------------------------------------------------- 39g.10 grid and game DP


def dungeon_forward_naive(dungeon):
    """A wrong forward DP: keep, per cell, only the path that needs the least health so far."""
    rows, cols = len(dungeon), len(dungeon[0])
    best = [[None] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            options = [(0, 0)] if r == c == 0 else []
            if r:
                options.append(best[r - 1][c])
            if c:
                options.append(best[r][c - 1])
            best[r][c] = min((max(need, 1 - (total + dungeon[r][c])), total + dungeon[r][c])
                             for need, total in options)
    return max(1, best[-1][-1][0])


def game_lead(values):
    """Reference for LC 486 and 877: plain game-tree search, no memo; the first player's best lead."""
    def lead(i, j):
        if i > j:
            return 0
        return max(values[i] - lead(i + 1, j), values[j] - lead(i, j - 1))

    return lead(0, len(values) - 1)


def monotone_paths(rows, cols):
    for moves in set(itertools.permutations("D" * (rows - 1) + "R" * (cols - 1))):
        r = c = 0
        cells = [(0, 0)]
        for m in moves:
            r, c = (r + 1, c) if m == "D" else (r, c + 1)
            cells.append((r, c))
        yield cells


def t_grid_game_dp():
    trap = [[0, -1, 2, 0], [0, 0, 1, -5]]
    assert F.calculate_minimum_hp(trap) == 4 and dungeon_forward_naive(trap) == 5
    ring, key, position, greedy_steps = "aababca", "bc", 0, 0
    for ch in key:                              # greedy: rotate to the nearest matching letter
        step, position = min((min(abs(i - position), len(ring) - abs(i - position)), i)
                             for i, c in enumerate(ring) if c == ch)
        greedy_steps += step + 1
    assert greedy_steps == 7 and F.find_rotate_steps(ring, key) == 6
    for _ in range(300):
        rows, cols = rng.randint(1, 4), rng.randint(1, 4)
        grid = [[rng.randint(0, 9) for _ in range(cols)] for _ in range(rows)]
        assert F.min_path_sum(grid) == min(sum(grid[r][c] for r, c in p) for p in monotone_paths(rows, cols))
        dungeon = [[rng.randint(-9, 9) for _ in range(cols)] for _ in range(rows)]
        brute = min(max(1, 1 - min(itertools.accumulate(dungeon[r][c] for r, c in p)))
                    for p in monotone_paths(rows, cols))
        assert F.calculate_minimum_hp(dungeon) == brute
        ring = "".join(rng.choice("abc") for _ in range(rng.randint(1, 6)))
        key = "".join(rng.choice(ring) for _ in range(rng.randint(1, 4)))
        start = (0, 0)                          # reference: BFS over (position, letters spelled), unit moves
        dist, frontier = {start: 0}, [start]
        while frontier:
            nxt = []
            for pos, done in frontier:
                moves = [((pos + 1) % len(ring), done), ((pos - 1) % len(ring), done)]
                if done < len(key) and ring[pos] == key[done]:
                    moves.append((pos, done + 1))
                for state in moves:
                    if state not in dist:
                        dist[state] = dist[(pos, done)] + 1
                        nxt.append(state)
            frontier = nxt
        assert F.find_rotate_steps(ring, key) == min(d for (pos, done), d in dist.items() if done == len(key))
        n = rng.randint(2, 6)
        flights = [[u, v, rng.randint(1, 20)] for u in range(n) for v in range(n) if u != v and rng.random() < 0.35]
        src, dst, k = rng.randrange(n), rng.randrange(n), rng.randint(0, 3)
        best = math.inf

        def walk(city, spent, used):            # reference: every walk with at most k + 1 flights
            nonlocal best
            if city == dst:
                best = min(best, spent)
            if used == k + 1:
                return
            for u, v, price in flights:
                if u == city:
                    walk(v, spent + price, used + 1)

        walk(src, 0, 0)
        assert F.find_cheapest_price(n, flights, src, dst, k) == (-1 if best == math.inf else best)
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 6)))
        p = ""
        for _ in range(rng.randint(0, 5)):
            p += rng.choice("ab.") + rng.choice(["", "", "*"])
        assert F.is_match(s, p) == (re.fullmatch(p, s) is not None)
        balloons = [rng.randint(0, 9) for _ in range(rng.randint(0, 6))]
        brute = 0
        for order in itertools.permutations(range(len(balloons))):
            alive, coins = list(range(len(balloons))), 0
            for b in order:
                pos = alive.index(b)
                left = balloons[alive[pos - 1]] if pos else 1
                right = balloons[alive[pos + 1]] if pos + 1 < len(alive) else 1
                coins += left * balloons[b] * right
                alive.pop(pos)
            brute = max(brute, coins)
        assert F.max_coins(balloons) == brute
        nums = [rng.randint(0, 20) for _ in range(rng.randint(1, 8))]
        assert F.predict_the_winner(nums) == (game_lead(nums) >= 0)
        piles = [rng.randint(1, 9) for _ in range(2 * rng.randint(1, 4))]
        if sum(piles) % 2:                      # LC 877's conditions: the first player wins outright
            assert F.stone_game(piles) and game_lead(piles) > 0
    for eggs in range(1, 5):
        @cache
        def drops(e, floors):                   # reference: the textbook O(k n^2) recurrence
            if floors == 0:
                return 0
            if e == 1:
                return floors
            return 1 + min(max(drops(e - 1, x - 1), drops(e, floors - x)) for x in range(1, floors + 1))

        for floors in range(0, 60):
            assert F.super_egg_drop(eggs, floors) == drops(eggs, floors)
    assert F.super_egg_drop(2, 100) == 14 and F.super_egg_drop(3, 14) == 4
    return "forward DP fails on the dungeon [[0,-1,2,0],[0,0,1,-5]]: it answers 5, the truth is 4"


# ----------------------------------------------------------------------------- 39g.11 house robber and stocks


def random_tree(n):
    if n == 0:
        return None, []
    nodes = [F.TreeNode(rng.randint(0, 9)) for _ in range(n)]
    parent = [None] * n
    for i in range(1, n):
        while True:
            p = rng.randrange(i)
            side = rng.choice(("left", "right"))
            if getattr(nodes[p], side) is None:
                setattr(nodes[p], side, nodes[i])
                parent[i] = p
                break
    return nodes[0], [(nodes[i].val, parent[i]) for i in range(n)]


def stock_brute(prices, k, fee, cooldown):
    best = 0

    def go(day, holding, buys, cash, last_sale):
        nonlocal best
        if day == len(prices):
            if not holding:
                best = max(best, cash)
            return
        go(day + 1, holding, buys, cash, last_sale)                       # rest
        if holding:
            go(day + 1, False, buys, cash + prices[day] - fee, day)       # sell
        elif (k is None or buys < k) and day - last_sale > cooldown:
            go(day + 1, True, buys + 1, cash - prices[day], last_sale)    # buy

    go(0, False, 0, 0, -10 ** 9)
    return best


def t_robber_stocks():
    assert F.rob_circular([2, 3, 2]) == 3 and F.rob_circular([1, 2, 3, 1]) == 4 and F.rob_circular([5]) == 5
    T = F.TreeNode
    assert F.rob_tree(T(3, T(2, None, T(3)), T(3, None, T(1)))) == 7
    assert F.rob_tree(T(3, T(4, T(1), T(3)), T(5, None, T(1)))) == 9 and F.rob_tree(None) == 0
    for _ in range(300):
        houses = [rng.randint(0, 9) for _ in range(rng.randint(1, 9))]
        n = len(houses)
        best = max(sum(houses[i] for i in s) for r in range(n + 1) for s in itertools.combinations(range(n), r)
                   if all((j - i) % n not in (1, n - 1) for i, j in itertools.combinations(s, 2)))
        assert F.rob_circular(houses) == best
        root, nodes = random_tree(rng.randint(0, 9))
        best = max((sum(nodes[i][0] for i in s) for r in range(len(nodes) + 1)
                    for s in itertools.combinations(range(len(nodes)), r)
                    if not any(nodes[i][1] in s for i in s)), default=0)
        assert F.rob_tree(root) == best
    examples = [((7, 1, 5, 3, 6, 4), dict(k=1), 5), ((1, 2, 3, 4, 5), {}, 4), ((7, 6, 4, 3, 1), {}, 0),
                ((3, 3, 5, 0, 0, 3, 1, 4), dict(k=2), 6), ((3, 2, 6, 5, 0, 3), dict(k=2), 7),
                ((1, 2, 3, 0, 2), dict(cooldown=1), 3), ((1, 3, 2, 8, 4, 9), dict(fee=2), 8), ((), {}, 0)]
    for prices, params, expected in examples:
        assert F.max_profit(list(prices), **params) == expected
    for _ in range(600):
        prices = [rng.randint(0, 9) for _ in range(rng.randint(0, 8))]
        k = rng.choice([None, 0, 1, 2, 3])
        fee, cooldown = rng.choice([0, 0, 1, 3]), rng.choice([0, 0, 1, 2])
        assert F.max_profit(prices, k, fee, cooldown) == stock_brute(prices, k, fee, cooldown)
    return "one state machine matches brute force for every mix of k, fee and cooldown"


# ----------------------------------------------------------------------------- 39g.12 greedy


def t_greedy():
    assert F.find_min_arrow_shots([[10, 16], [2, 8], [1, 6], [7, 12]]) == 2
    assert F.find_min_arrow_shots([[1, 2], [2, 3], [3, 4], [4, 5]]) == 2
    assert F.min_meeting_rooms_sweep([[0, 30], [5, 10], [15, 20]]) == 2 and F.min_meeting_rooms_sweep([[1, 5], [5, 10]]) == 1
    assert F.jump([2, 3, 1, 1, 4]) == 2 and not F.can_jump([3, 2, 1, 0, 4])
    assert F.can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3 == F.can_complete_circuit_prefix([1, 2, 3, 4, 5], [3, 4, 5, 1, 2])
    assert F.video_stitching([[0, 2], [4, 6], [8, 10], [1, 9], [1, 5], [5, 9]], 10) == 3
    assert F.greedy_coin_count([1, 3, 4], 6) == 3 and F.coin_change_table([1, 3, 4], 6) == 2
    assert all(F.greedy_coin_count([1, 5, 10, 25], a) == F.coin_change_table([1, 5, 10, 25], a) for a in range(400))
    weights, values, room, dense_value = [6, 5, 5], [7, 5, 5], 10, 0
    for i in sorted(range(3), key=lambda i: -values[i] / weights[i]):   # greedy by value per unit weight
        if weights[i] <= room:
            room -= weights[i]
            dense_value += values[i]
    assert dense_value == 7 and F.knapsack_items(weights, values, 10)[0] == 10
    for _ in range(300):
        intervals = []
        for _ in range(rng.randint(1, 7)):
            s = rng.randint(0, 12)
            intervals.append([s, s + rng.randint(0, 5)])
        ends = sorted({e for _, e in intervals})   # some optimal set of arrows uses right ends only
        need = min(r for r in range(1, len(ends) + 1) for shots in itertools.combinations(ends, r)
                   if all(any(s <= x <= e for x in shots) for s, e in intervals))
        assert F.find_min_arrow_shots(intervals) == need
        meetings = [[s, e] for s, e in intervals if s < e]
        peak = max((sum(s <= t < e for s, e in meetings) for t in range(20)), default=0)
        assert F.min_meeting_rooms_sweep(meetings) == peak
        nums = [rng.randint(0, 3) for _ in range(rng.randint(1, 9))]
        reach = reference_distances({i: {j for j in range(i + 1, min(len(nums), i + nums[i] + 1))}
                                     for i in range(len(nums))}, 0)
        assert F.can_jump(nums) == (len(nums) - 1 in reach)
        if len(nums) - 1 in reach:
            assert F.jump(nums) == reach[len(nums) - 1]
        n = rng.randint(1, 7)
        gas = [rng.randint(0, 6) for _ in range(n)]
        cost = [rng.randint(0, 6) for _ in range(n)]
        valid = [s for s in range(n) if all(sum(gas[(s + i) % n] - cost[(s + i) % n] for i in range(m + 1)) >= 0
                                            for m in range(n))]
        for answer in (F.can_complete_circuit(gas, cost), F.can_complete_circuit_prefix(gas, cost)):
            assert answer in valid if valid else answer == -1
        time_limit = rng.randint(1, 10)
        clips = [[s, s + rng.randint(0, 5)] for s in (rng.randint(0, 9) for _ in range(rng.randint(1, 7)))]

        def covers(chosen):
            reach_to = 0
            for s, e in sorted(chosen):
                if s > reach_to:
                    break
                reach_to = max(reach_to, e)
            return reach_to >= time_limit

        brute = min((r for r in range(1, len(clips) + 1) for c in itertools.combinations(clips, r) if covers(c)),
                    default=-1)
        assert F.video_stitching(clips, time_limit) == brute
    return "coins 1, 3, 4 and amount 6: greedy uses 3 coins (4+1+1), the optimum is 2 (3+3)"


# ----------------------------------------------------------------------------- 39g.13 math techniques


def t_math():
    win = [False]                               # reference: game DP for Nim with moves 1..3
    for n in range(1, 80):
        win.append(any(not win[n - m] for m in (1, 2, 3) if m <= n))
        assert F.can_win_nim(n) == win[n]
    for n in range(0, 300):
        on = [False] * (n + 1)
        for step in range(1, n + 1):
            for i in range(step, n + 1, step):
                on[i] = not on[i]
        assert F.bulb_switch(n) == sum(on)
    for x in range(-40, 5000):
        assert F.is_power_of_two(x) == (x > 0 and bin(x).count("1") == 1)
        if x >= 0:
            assert F.hamming_weight(x) == bin(x).count("1")
    assert F.count_bits(2000) == [bin(i).count("1") for i in range(2001)]
    for _ in range(500):
        base, exp, mod = rng.randint(0, 10 ** 6), rng.randint(0, 10 ** 4), rng.randint(1, 10 ** 5)
        assert F.mod_pow(base, exp, mod) == pow(base, exp, mod)
        digits = [rng.randint(0, 9) for _ in range(rng.randint(1, 6))]
        digits[0] = digits[0] or 1
        a = rng.randint(1, 2 ** 31 - 1)
        assert F.super_pow(a, digits) == pow(a, int("".join(map(str, digits))), 1337)
        a, b = rng.randint(0, 10 ** 6), rng.randint(0, 10 ** 6)
        assert F.gcd(a, b) == math.gcd(a, b) and F.lcm(a, b) == math.lcm(a, b)
    primes = [p for p in range(2, 3000) if all(p % d for d in range(2, math.isqrt(p) + 1))]
    for n in range(0, 3001, 7):
        assert F.count_primes(n) == sum(p < n for p in primes)
    assert F.count_primes(10 ** 6) == 78498
    for n in range(0, 400):
        text = str(math.factorial(n))
        assert F.trailing_zeroes(n) == len(text) - len(text.rstrip("0"))
    counts = Counter(F.trailing_zeroes(x) for x in range(0, 5 * 120))
    for k in range(0, 100):
        assert F.preimage_size_fzf(k) == counts[k]
    assert F.preimage_size_fzf(10 ** 9) in (0, 5)
    for _ in range(300):
        n = rng.randint(2, 12)
        nums = list(range(1, n + 1))
        missing = rng.choice(nums)
        nums[nums.index(missing)] = rng.choice([v for v in nums if v != missing])
        rng.shuffle(nums)
        copy = nums[:]
        tally = Counter(nums)
        assert F.find_error_nums(nums) == [next(v for v in tally if tally[v] == 2), missing] and nums == copy
    return "Nim, bulbs, bit tricks, modular powers, gcd, sieve (78,498 primes below 10^6), factorial zeros, set mismatch"


# ----------------------------------------------------------------------------- 39g.13 randomness and probability


def t_randomness_probability():
    for n in range(1, 6):                       # Fisher-Yates: every permutation has probability exactly 1/n!
        dist = exact_distribution(lambda source: tuple(F.fisher_yates(list(range(n)), source)))
        assert len(dist) == math.factorial(n) and set(dist.values()) == {Fraction(1, math.factorial(n))}
    naive = exact_distribution(lambda source: tuple(F.naive_shuffle([0, 1, 2], source)))
    assert sorted(naive.values()) == [Fraction(4, 27)] * 3 + [Fraction(5, 27)] * 3
    for n in range(1, 7):                       # reservoir: every k-subset equally likely
        for k in range(1, n + 1):
            dist = exact_distribution(lambda source: frozenset(F.reservoir_sample(iter(range(n)), k, source)))
            assert len(dist) == math.comb(n, k) and set(dist.values()) == {Fraction(1, math.comb(n, k))}
    nums = [1, 2, 3, 3, 3, 2, 3]
    dist = exact_distribution(lambda source: F.pick_index(nums, 3, source))
    assert dict(dist) == {i: Fraction(1, 4) for i in (2, 3, 4, 6)}
    seeded = random.Random(2026)
    trials = 24_000
    tally = Counter(tuple(F.fisher_yates(list(range(4)), seeded)) for _ in range(trials))
    chi2 = sum((tally[p] - trials / 24) ** 2 / (trials / 24) for p in itertools.permutations(range(4)))
    assert len(tally) == 24 and chi2 < 49.7        # 23 degrees of freedom, 0.1% critical value
    assert F.monty_hall_exact(False) == Fraction(1, 3) and F.monty_hall_exact(True) == Fraction(2, 3)
    goat_shown = switch_wins = Fraction(0)      # a host who opens a random unpicked door that happens to hide a goat
    for car, pick in itertools.product(range(3), repeat=2):
        for host in (d for d in range(3) if d != pick):
            if host != car:
                goat_shown += Fraction(1, 18)
                switch_wins += Fraction(1, 18) * (3 - pick - host == car)
    assert switch_wins / goat_shown == Fraction(1, 2)
    assert abs(F.monty_hall_simulate(True, 30_000, seeded) - 2 / 3) < 0.015
    assert abs(F.monty_hall_simulate(False, 30_000, seeded) - 1 / 3) < 0.015
    first = next(n for n in range(1, 100) if F.birthday_collision(n) >= Fraction(1, 2))
    assert first == 23 and F.birthday_collision(22) < Fraction(1, 2) and F.birthday_collision(366) == 1
    assert 0.999 < float(F.birthday_collision(70)) < 0.9992
    shared = sum(len(set(seeded.randrange(365) for _ in range(23))) < 23 for _ in range(20_000)) / 20_000
    assert abs(shared - float(F.birthday_collision(23))) < 0.015
    assert F.two_children_puzzles() == {"at least one child is a boy": Fraction(1, 3),
                                        "the older child is a boy": Fraction(1, 2),
                                        "the child you happened to meet is a boy": Fraction(1, 2)}
    return (f"exact enumeration of every random draw: shuffles, reservoirs, pick index; naive shuffle of 3 gives "
            f"4/27 or 5/27; chi-square {chi2:.1f}; birthday threshold 23")


# ----------------------------------------------------------------------------- 39g.13 ugly numbers


def t_ugly():
    bound = 10 ** 9                             # reference: every 2^a 3^b 5^c up to bound, sorted
    smooth = sorted(2 ** a * 3 ** b * 5 ** c for a in range(30) for b in range(19) for c in range(13)
                    if 2 ** a * 3 ** b * 5 ** c <= bound)
    for x in range(-5, 3000):
        y, ok = x, x > 0
        if ok:
            for p in (2, 3, 5):
                while y % p == 0:
                    y //= p
            ok = y == 1
        assert F.is_ugly(x) == ok
    assert [x for x in range(1, 3000) if F.is_ugly(x)] == [x for x in smooth if x < 3000]
    for n in range(1, len(smooth) + 1, 7):
        assert F.nth_ugly_number(n) == smooth[n - 1]
    assert F.nth_ugly_number(1690) == 2123366400
    for _ in range(100):
        primes = sorted(rng.sample([2, 3, 5, 7, 11, 13, 17, 19, 23], rng.randint(1, 4)))
        n = rng.randint(1, 60)
        heap, seen = [1], {1}                   # reference: pop the smallest, push its multiples once
        for _ in range(n - 1):
            x = heapq.heappop(heap)
            for p in primes:
                if x * p not in seen:
                    seen.add(x * p)
                    heapq.heappush(heap, x * p)
        assert F.nth_super_ugly_number(n, primes) == heap[0]
        a, b, c = rng.randint(1, 12), rng.randint(1, 12), rng.randint(1, 12)
        n = rng.randint(1, 60)
        values = [x for x in range(1, 12 * 60 + 1) if x % a == 0 or x % b == 0 or x % c == 0]
        assert F.nth_ugly_number_iii(n, a, b, c) == values[n - 1]
    assert F.nth_ugly_number_iii(1_000_000_000, 2, 217983653, 336916467) == 1999999984
    return "263, 264 (the 1,690th is 2,123,366,400), 313 with a heap, 1201 by binary search"


# ----------------------------------------------------------------------------- 39g.14 classic interview problems


def rectangles_brute(rectangles):
    x1 = min(r[0] for r in rectangles)
    y1 = min(r[1] for r in rectangles)
    x2 = max(r[2] for r in rectangles)
    y2 = max(r[3] for r in rectangles)
    cover = Counter((x, y) for a, b, c, d in rectangles for x in range(a, c) for y in range(b, d))
    return all(cover[(x, y)] == 1 for x in range(x1, x2) for y in range(y1, y2)) and len(cover) == (x2 - x1) * (y2 - y1)


def random_tiling(x1, y1, x2, y2, depth):
    """Split a rectangle by random guillotine cuts: a perfect cover."""
    if depth == 0 or (x2 - x1 < 2 and y2 - y1 < 2) or rng.random() < 0.25:
        return [[x1, y1, x2, y2]]
    if x2 - x1 >= 2 and (y2 - y1 < 2 or rng.random() < 0.5):
        cut = rng.randint(x1 + 1, x2 - 1)
        return random_tiling(x1, y1, cut, y2, depth - 1) + random_tiling(cut, y1, x2, y2, depth - 1)
    cut = rng.randint(y1 + 1, y2 - 1)
    return random_tiling(x1, y1, x2, cut, depth - 1) + random_tiling(x1, cut, x2, y2, depth - 1)


def t_classics():
    assert F.trap_two_pointers([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6 and F.trap_prefix([4, 2, 0, 3, 2, 5]) == 9
    assert F.max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert F.remove_covered_intervals([[1, 4], [3, 6], [2, 8]]) == 2
    assert F.is_possible([1, 2, 3, 3, 4, 5]) and not F.is_possible([1, 2, 3, 4, 4, 5])
    assert F.multiply("123", "456") == "56088" and F.multiply("0", "52") == "0"
    assert F.is_rectangle_cover([[1, 1, 3, 3], [3, 1, 4, 2], [3, 2, 4, 4], [1, 3, 2, 4], [2, 3, 3, 4]])
    assert not F.is_rectangle_cover([[1, 1, 3, 3], [3, 1, 4, 2], [1, 3, 2, 4], [2, 2, 4, 4]])
    true_cases = 0
    for _ in range(400):
        heights = [rng.randint(0, 6) for _ in range(rng.randint(0, 12))]
        brute = sum(min(max(heights[:i + 1]), max(heights[i:])) - h for i, h in enumerate(heights))
        assert F.trap_brute(heights) == F.trap_prefix(heights) == F.trap_two_pointers(heights) == brute
        if len(heights) >= 2:
            assert F.max_area(heights) == max((j - i) * min(heights[i], heights[j])
                                              for i in range(len(heights)) for j in range(i + 1, len(heights)))
        intervals = list({(s, s + rng.randint(1, 6)) for s in (rng.randint(0, 8) for _ in range(rng.randint(1, 7)))})
        covered = sum(any(c <= a and b <= d and (a, b) != (c, d) for c, d in intervals) for a, b in intervals)
        assert F.remove_covered_intervals([list(iv) for iv in intervals]) == len(intervals) - covered
        nums = sorted(rng.randint(1, 6) for _ in range(rng.randint(1, 10)))

        def splittable(rest, runs):             # reference: try every placement of the next value
            if not rest:
                return all(length >= 3 for _, length in runs)
            x, tail = rest[0], rest[1:]
            options = {(end, length) for end, length in runs if end == x - 1}
            for end, length in options:
                i = runs.index((end, length))
                if splittable(tail, runs[:i] + runs[i + 1:] + [(x, length + 1)]):
                    return True
            return splittable(tail, runs + [(x, 1)])

        assert F.is_possible(nums) == splittable(nums, [])
        arr = rng.sample(range(1, 11), rng.randint(1, 10))
        flips = F.pancake_sort(arr)
        work = arr[:]
        for k in flips:
            assert 1 <= k <= len(work)
            work[:k] = work[k - 1::-1]
        assert work == sorted(arr) and len(flips) <= max(2 * len(arr) - 3, 0)
        a, b = str(rng.randint(0, 10 ** rng.randint(1, 30))), str(rng.randint(0, 10 ** rng.randint(1, 30)))
        assert F.multiply(a, b) == str(int(a) * int(b))
        rects = random_tiling(0, 0, rng.randint(1, 6), rng.randint(1, 6), 4)
        if rng.random() < 0.6:                  # perturb: drop, duplicate, shift or add a rectangle
            choice = rng.randrange(4)
            if choice == 0 and len(rects) > 1:
                rects.pop(rng.randrange(len(rects)))
            elif choice == 1:
                rects.append(list(rng.choice(rects)))
            elif choice == 2:
                r = rects[rng.randrange(len(rects))]
                dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                r[0] += dx
                r[2] += dx
                r[1] += dy
                r[3] += dy
            else:
                x, y = rng.randint(0, 5), rng.randint(0, 5)
                rects.append([x, y, x + rng.randint(1, 2), y + rng.randint(1, 2)])
        expected = rectangles_brute(rects)
        true_cases += expected
        assert F.is_rectangle_cover(rects) == expected
    assert true_cases > 100
    return "rain water three ways, container, covered intervals, 659, pancakes, multiply, perfect rectangle"


if __name__ == "__main__":
    started = time.perf_counter()
    tests = [(name, fn) for name, fn in globals().items() if name.startswith("t_")]
    for name, fn in tests:
        check(name[2:], fn)
    print(f"all {len(tests)} groups passed in {time.perf_counter() - started:.1f} s")
