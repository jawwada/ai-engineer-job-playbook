"""Tested code for chapter 39g: backtracking, BFS, dynamic programming, greedy and math techniques.

Standard library only, Python 3.10+. The sections follow the chapter (39g.1 to 39g.14); the LeetCode
number is in each docstring. Run `python3 test_frameworks_2.py`.

Conventions: functions that LeetCode specifies as in-place mutate their input (the tests pass copies).
Indices are 0-based unless a docstring says otherwise. Functions that take `rng` accept any object
with `randrange`, so tests can pass a seeded `random.Random` or a scripted source.
"""
from __future__ import annotations

import heapq
import math
import random
from bisect import bisect_left
from collections import Counter, defaultdict, deque
from fractions import Fraction
from functools import cache

DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --------------------------------------------------------------------------- 39g.1 search trees


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


# --------------------------------------------------------------------------- 39g.2 the framework


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


def solve_n_queens(n):
    """N-Queens (LC 51): one queen per row; three boolean arrays make each attack check O(1)."""
    out, queens = [], []                       # queens[r] is the column of the queen in row r
    col_used = [False] * n
    diag_used = [False] * (2 * n - 1)          # r - c + n - 1 is constant along a "\" diagonal
    anti_used = [False] * (2 * n - 1)          # r + c is constant along a "/" diagonal

    def place(r):
        if r == n:
            out.append(["." * c + "Q" + "." * (n - 1 - c) for c in queens])
            return
        for c in range(n):
            d, a = r - c + n - 1, r + c
            if col_used[c] or diag_used[d] or anti_used[a]:
                continue                       # attacked: the whole subtree is pruned
            col_used[c] = diag_used[d] = anti_used[a] = True
            queens.append(c)
            place(r + 1)
            queens.pop()
            col_used[c] = diag_used[d] = anti_used[a] = False

    place(0)
    return out


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


# --------------------------------------------------------------------------- 39g.3 the nine forms


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


def permute_unique_counter(nums):
    """LC 47 again: branch on distinct values with a counter, so duplicates never arise."""
    counts = Counter(nums)
    out, path = [], []

    def backtrack():
        if len(path) == len(nums):
            out.append(path[:])
            return
        for value in counts:
            if counts[value] == 0:
                continue
            counts[value] -= 1
            path.append(value)
            backtrack()
            path.pop()
            counts[value] += 1

    backtrack()
    return out


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


# --------------------------------------------------------------------------- 39g.4 ball and box


def permute_by_placing(nums):
    """LC 46 from the other side: each element in turn picks a free position."""
    n = len(nums)
    out, slots = [], [None] * n

    def place(i):
        if i == n:
            out.append(slots[:])
            return
        for p in range(n):
            if slots[p] is None:
                slots[p] = nums[i]
                place(i + 1)
                slots[p] = None

    place(0)
    return out


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


# --------------------------------------------------------------------------- 39g.5 islands


def sink_island(grid, r, c):
    """DFS flood fill: turn (r, c) and all land 4-connected to it into water; return how many cells sank."""
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c] != 1:
        return 0                               # off the grid, water, or already visited
    grid[r][c] = 0                             # the grid is its own visited set
    size = 1
    for dr, dc in DIRS4:
        size += sink_island(grid, r + dr, c + dc)
    return size


def num_enclaves(grid):
    """Number of Enclaves (LC 1020): sink all land that touches the border, then count what is left."""
    rows, cols = len(grid), len(grid[0])
    for r in range(rows):
        for c in range(cols):
            if r in (0, rows - 1) or c in (0, cols - 1):
                sink_island(grid, r, c)
    return sum(map(sum, grid))


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


# --------------------------------------------------------------------------- 39g.6 BFS


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


def is_solvable_2x3(board):
    """A 2 x 3 sliding puzzle is solvable exactly when its tiles, read row by row without the 0, have an even
    number of inversions: a move along a row keeps the order; a vertical move jumps a tile over two others."""
    tiles = [x for row in board for x in row if x]
    inversions = sum(a > b for i, a in enumerate(tiles) for b in tiles[i + 1:])
    return inversions % 2 == 0


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


# --------------------------------------------------------------------------- 39g.7 the DP framework


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


def coin_change_brute(coins, amount):
    """Coin Change (LC 322) from the definition: the last coin is one of the coins. Exponential time."""
    def fewest(a):
        if a == 0:
            return 0
        return min((fewest(a - coin) + 1 for coin in coins if coin <= a), default=math.inf)

    best = fewest(amount)
    return -1 if best == math.inf else best


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


def length_of_lis_quadratic(nums):
    """Longest Increasing Subsequence (LC 300) by induction: dp[i] is the longest one that ends at nums[i]."""
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp, default=0)


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


def min_falling_path_sum(matrix):
    """Minimum Falling Path Sum (LC 931): best[c] is the cheapest path ending at column c of this row."""
    best = list(matrix[0])
    n = len(best)
    for row in matrix[1:]:
        best = [row[c] + min(best[max(c - 1, 0):c + 2]) for c in range(n)]
    return min(best)


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


def word_break(s, word_dict):
    """Word Break (LC 139): can[i] says whether s[i:] splits into dictionary words."""
    words = set(word_dict)
    lengths = {len(w) for w in words}
    can = [False] * len(s) + [True]
    for i in range(len(s) - 1, -1, -1):
        can[i] = any(can[i + n] for n in lengths if i + n <= len(s) and s[i:i + n] in words)
    return can[0]


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


# --------------------------------------------------------------------------- 39g.8 subsequence and string DP


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


# --------------------------------------------------------------------------- 39g.9 knapsack


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


def can_partition_bitset(nums):
    """Partition Equal Subset Sum (LC 416), an integer as the table: bit s is set if a subset sums to s."""
    total = sum(nums)
    if total % 2:
        return False
    reachable = 1                              # only the empty sum
    for x in nums:
        reachable |= reachable << x            # every old sum, with or without x
    return bool((reachable >> (total // 2)) & 1)


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


def find_target_sum_ways_memo(nums, target):
    """Target Sum (LC 494) directly: state (index, running total), two choices per number."""
    @cache
    def ways(i, total):
        if i == len(nums):
            return int(total == target)
        return ways(i + 1, total + nums[i]) + ways(i + 1, total - nums[i])

    return ways(0, 0)


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


# --------------------------------------------------------------------------- 39g.10 grid and game DP


def min_path_sum(grid):
    """Minimum Path Sum (LC 64): best[c] is the cheapest path to column c of the current row."""
    best = [math.inf] * len(grid[0])
    best[0] = 0
    for row in grid:
        best[0] += row[0]
        for c in range(1, len(row)):
            best[c] = row[c] + min(best[c], best[c - 1])   # from above, or from the left
    return best[-1]


def calculate_minimum_hp(dungeon):
    """Dungeon Game (LC 174), solved backwards: need[c] is the health required on entering cell (r, c)."""
    cols = len(dungeon[0])
    need = [math.inf] * (cols + 1)
    need[cols - 1] = 1                         # a virtual cell below the princess: arrive with 1
    for row in reversed(dungeon):
        for c in range(cols - 1, -1, -1):
            need[c] = max(1, min(need[c], need[c + 1]) - row[c])
    return need[0]


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


def super_egg_drop(k, n):
    """Super Egg Drop (LC 887): floors[e] is how many floors m moves and e eggs can always resolve."""
    floors = [0] * (k + 1)
    moves = 0
    while floors[k] < n:
        moves += 1
        for e in range(k, 0, -1):              # right to left: floors[e - 1] still holds the m - 1 value
            floors[e] = floors[e - 1] + floors[e] + 1   # breaks: below; survives: above; plus this floor
    return moves


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


# --------------------------------------------------------------------------- 39g.11 house robber and stocks


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


class TreeNode:
    __slots__ = ("val", "left", "right")

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


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


# --------------------------------------------------------------------------- 39g.12 greedy


def find_min_arrow_shots(points):
    """Minimum Number of Arrows to Burst Balloons (LC 452): shoot at the earliest end. Closed intervals."""
    arrows, last_shot = 0, -math.inf
    for start, end in sorted(points, key=lambda p: p[1]):
        if start > last_shot:                  # the last arrow misses this balloon
            arrows += 1
            last_shot = end
    return arrows


def min_meeting_rooms_sweep(intervals):
    """Meeting Rooms II (LC 253) as a sweep line: +1 at each start, -1 at each end; ends first on ties."""
    events = sorted([(start, 1) for start, _ in intervals] + [(end, -1) for _, end in intervals])
    rooms = peak = 0
    for _, delta in events:
        rooms += delta
        peak = max(peak, rooms)
    return peak


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


def greedy_coin_count(coins, amount):
    """Largest coin first. Optimal for coin systems such as 1, 5, 10, 25 but not in general; -1 if stuck."""
    count = 0
    for coin in sorted(coins, reverse=True):
        count += amount // coin
        amount %= coin
    return count if amount == 0 else -1


# --------------------------------------------------------------------------- 39g.13 math techniques


def can_win_nim(n):
    """Nim Game (LC 292): the player to move loses exactly when n is a multiple of 4."""
    return n % 4 != 0


def bulb_switch(n):
    """Bulb Switcher (LC 319): bulb i is toggled once per divisor, so it ends on iff i is a perfect square."""
    return math.isqrt(n)


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


def count_bits(n):
    """Counting Bits (LC 338): bits(i) = bits(i & (i - 1)) + 1, a DP over 'i without its lowest set bit'."""
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i & (i - 1)] + 1
    return bits


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


def gcd(a, b):
    """Euclid: gcd(a, b) = gcd(b, a mod b); the arguments at least halve every two steps."""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a, b):
    """Least common multiple through the gcd; divide before multiplying to keep numbers small."""
    return 0 if a == 0 or b == 0 else abs(a // gcd(a, b) * b)


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


def monty_hall_simulate(switch, trials, rng=random):
    """The same game played trials times; returns the fraction won."""
    wins = 0
    for _ in range(trials):
        car, pick = rng.randrange(3), rng.randrange(3)
        goats = [d for d in range(3) if d not in (car, pick)]
        host = goats[rng.randrange(len(goats))]
        final = 3 - pick - host if switch else pick
        wins += final == car
    return wins / trials


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


def is_ugly(n):
    """Ugly Number (LC 263): positive, with no prime factors other than 2, 3 and 5."""
    if n <= 0:
        return False
    for p in (2, 3, 5):
        while n % p == 0:
            n //= p
    return n == 1


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


# --------------------------------------------------------------------------- 39g.14 classic problems


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


def remove_covered_intervals(intervals):
    """Remove Covered Intervals (LC 1288): sort by start up and end down; an interval is covered iff its end
    does not pass the largest end seen so far."""
    remaining, max_end = 0, -math.inf
    for _, end in sorted(intervals, key=lambda iv: (iv[0], -iv[1])):
        if end > max_end:
            remaining += 1
            max_end = end
    return remaining


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
