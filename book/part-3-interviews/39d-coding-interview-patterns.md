# 39d. Coding interview patterns: the twenty LeetCode patterns, with tested templates and how to recognize them

> **What you need to be able to say:** which pattern a problem belongs to within the first two minutes and why (the cue in the statement or the constraints), the invariant that makes it correct, the template written cleanly from memory, its time and space complexity, and the follow-up that turns the easy version into the hard one.

## 39d.1 What the coding round rewards, and how to use this chapter

LeetCode has well over three thousand problems, but interviewers draw from a few dozen shapes. A pattern is a reusable plan — a data structure plus an invariant — that turns a brute-force O(n²) or O(2ⁿ) idea into the expected O(n) or O(n log n) one. The twenty patterns here are the list in Arslan Ahmad's April 2026 Design Gurus article on *Grokking the Coding Interview* (the course itself has since grown to about forty patterns); the explanations, templates and practice sets are this book's own. The round scores four things, in this order:

1. **Finding the better approach.** Saying the brute force first and then naming the pattern ("this is a variable-size sliding window, because the answer is a contiguous run and shrinking a valid window keeps it valid") is worth more than jumping straight to code.
2. **Writing it correctly without running it.** Many rounds use an editor with no execution (chapter 39c.6). Templates you have typed twenty times are the ones you will not get wrong under pressure.
3. **Explaining the invariant and the complexity.** "Everything left of `write` is unique and sorted" is the sentence that convinces an interviewer the code is right.
4. **Handling the follow-up.** "Now the input is a stream", "now values can be negative", "now do it in O(1) space", "now there are k lists". Each pattern section below ends with the follow-ups that come up.

How to use the chapter: read the recognition tables in 39d.2 first. For each pattern, read the cues and the invariant, type the template from memory once, then solve the practice set in the order given, timed (15 minutes for an easy, 25 for a medium, 40 for a hard). Every template is copied verbatim from `labs/coding-patterns/patterns.py` (`check_chapter_sync.py` enforces it). To check your own version, replace the function in `patterns.py` with yours and run `python3 test_patterns.py`: it compares nearly every function with a brute-force reference on random inputs, which catches the off-by-one errors that two hand-picked examples miss.

The templates assume these imports, a four-direction constant for grids, and LeetCode's node classes (the helpers `build_list`, `list_values` and `build_tree` in `patterns.py` convert to and from Python lists and LeetCode's level-order notation for tests):

```python
import heapq
import threading
from bisect import bisect_left
from collections import Counter, OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


class ListNode:
    __slots__ = ("val", "next")

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    __slots__ = ("val", "left", "right")

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

The twenty patterns and where they map on LeetCode (problems marked † need LeetCode Premium; the middle column gives the article's sample problems under Grokking's own names):

| # | Pattern | Article's sample problems | LeetCode equivalents |
|---|---|---|---|
| 1 | Two pointers | Pair with Target Sum; Remove Duplicates; Squaring a Sorted Array | 167, 26, 977 |
| 2 | Islands (matrix traversal) | Number of Islands; Biggest Island; Flood Fill | 200, 695, 733 |
| 3 | Fast and slow pointers | LinkedList Cycle; Middle of the LinkedList; Palindrome LinkedList | 141, 876, 234 |
| 4 | Sliding window | Maximum Sum Subarray of Size K; Fruits Into Baskets; Longest Substring with K Distinct Characters | 643, 904, 340† |
| 5 | Merge intervals | Merge Intervals; Insert Interval; Intervals Intersection | 56, 57, 986 |
| 6 | Cyclic sort | Find the Missing Number; Find all Duplicates; Duplicates In Array | 268, 442, 287 |
| 7 | In-place reversal of a linked list | Reverse a LinkedList; Reverse a Sub-list; Reverse Every K-element Sub-list | 206, 92, 25 |
| 8 | Tree breadth-first search | Binary Tree Level Order Traversal; Reverse Level Order Traversal; Zigzag Traversal | 102, 107, 103 |
| 9 | Tree depth-first search | Binary Tree Path Sum; All Paths for a Sum; Count Paths for a Sum | 112, 113, 437 |
| 10 | Two heaps | Find the Median of a Number Stream; Sliding Window Median; Maximize Capital | 295, 480, 502 |
| 11 | Subsets | Subsets; Subsets With Duplicates; String Permutations | 78, 90, 784 (the course's "String Permutations by changing case") |
| 12 | Modified binary search | Order-agnostic Binary Search; Ceiling of a Number; Next Letter | (none), 35 (closest), 744 |
| 13 | Top K elements | Top K Frequent Numbers; Kth Largest Number in a Stream; Top K Frequent Elements | 347, 703, 347 again (215 is the array version of 703) |
| 14 | Bitwise XOR | Single Number; Two Single Numbers; Complement of Base 10 Number | 136, 260, 1009 |
| 15 | Backtracking | Sudoku Solver; Factor Combinations; Generate Parentheses | 37, 254†, 22 |
| 16 | 0/1 knapsack (dynamic programming) | 0/1 Knapsack; Equal Subset Sum Partition; Subset Sum | (none), 416, (none; 494 counts the ways) |
| 17 | Topological sort (graph) | Task Scheduling Order; All Tasks Scheduling Orders; Alien Dictionary | 210, (none), 269† |
| 18 | K-way merge | Merge K Sorted Lists; Kth Smallest Number in M Sorted Lists; Smallest Number Range | 23, 378 (closest), 632 |
| 19 | Monotonic stack | Next Greater Element; Next Smaller Element; Largest Rectangle in Histogram | 496, (1475 is the closest), 84 |
| 20 | Multi-threaded | Invert Binary Tree; Binary Search Tree Iterator; Same Tree | 226, 173, 100 (solved with threads), plus 1114–1242 |

The list is a curriculum, not the whole syllabus: hash maps with prefix sums, graph traversal and shortest paths, union-find, tries, greedy choices and the other dynamic-programming families come up at least as often as some of the twenty (the current course covers most of them too), so 39d.23 adds them in shorter form. Chapters 39e–39g go underneath and beyond this catalog: data structures from the inside and the ten sorting algorithms (39e); the classic templates, binary-tree thinking, data-structure design and graph algorithms (39f); and backtracking, BFS, dynamic programming, greedy algorithms and math techniques (39g).

## 39d.2 Recognize the pattern from the statement and the constraints

Read the statement for the shape of the answer, then read the constraints for the complexity you need. The two together usually leave one or two candidate patterns.

| Cue in the problem | Pattern to try first | First move |
|---|---|---|
| Sorted array; find a pair or triplet with a sum, or dedupe in place | Two pointers (39d.3) | One pointer at each end, or a read and a write pointer |
| Grid of cells; count or measure connected regions; spread from sources | Islands (39d.4) | BFS or DFS from each unvisited cell, marking on visit |
| Linked list or "next" function; cycle, middle, or "eventually repeats" | Fast and slow pointers (39d.5) | Move one pointer twice as fast |
| Contiguous subarray or substring; longest, shortest, or count with a condition | Sliding window (39d.6) | Grow on the right, shrink on the left while the condition breaks |
| Ranges with start and end; overlaps, merging, free time, rooms | Merge intervals (39d.7) | Sort by start, then sweep |
| Values in a known range 1..n (or 0..n); find missing or duplicated ones in O(1) space | Cyclic sort (39d.8) | Swap each value into index value − 1 |
| Reverse all or part of a linked list without extra memory | In-place reversal (39d.9) | prev, curr, next pointers and a dummy head |
| Tree, answer per level or "closest to the root" | Tree BFS (39d.10) | Queue; process `len(queue)` nodes per level |
| Tree, root-to-leaf paths, or a value computed from children | Tree DFS (39d.11) | Recursion that returns something to the parent |
| Running median; split values into a smaller and a larger half | Two heaps (39d.12) | Max-heap for the lower half, min-heap for the upper |
| "All subsets", "all permutations", "all combinations" | Subsets (39d.13) or backtracking (39d.17) | Build level by level, or choose–explore–unchoose |
| Sorted (or rotated, or monotone) data; "minimum value that works" | Modified binary search (39d.14) | Keep the answer inside [lo, hi] and halve |
| "k largest", "k most frequent", "k closest" | Top K (39d.15) | A heap of size k |
| Every value appears twice except one; flip bits | Bitwise XOR (39d.16) | XOR everything; pairs cancel |
| Constraint satisfaction, puzzles, "all valid arrangements" | Backtracking (39d.17) | Choose, recurse, undo; prune early |
| Choose items under a capacity; partition into equal sums; count ways to reach a sum | 0/1 knapsack (39d.18) | A table over capacity, filled right to left |
| Dependencies, prerequisites, ordering constraints | Topological sort (39d.19) | Kahn's algorithm: in-degrees and a queue |
| k sorted lists or rows; kth smallest across them | K-way merge (39d.20) | A heap holding one head per list |
| "Next greater/smaller", spans, histograms, removing digits | Monotonic stack (39d.21) | A stack of indices waiting for their answer |
| Threads, ordering of concurrent calls, producer–consumer, crawling | Multi-threaded (39d.22) | Events, conditions, a pool; no shared mutable state |
| "Subarray sum equals k" with negatives; counts of prefixes | Prefix sums plus a hash map (39d.23) | Store how often each running sum appeared |
| Graph as edges or adjacency lists; reachability, copying, two-coloring | Graph traversal (39d.23) | BFS or DFS with a visited set or map |
| Connectivity that grows as edges arrive; "redundant edge" | Union-find (39d.23) | Union by size with path halving |
| Weighted shortest path | Dijkstra (39d.23) | Heap of (distance, node); skip stale entries |

The constraints tell you the budget. With about 10⁸ simple operations per second in compiled languages and 10⁶–10⁷ in Python, the usual mapping is:

| Input size n | Target complexity | Typical patterns |
|---|---|---|
| n ≤ 10 | O(n!) | Permutations, backtracking |
| n ≤ 20–25 | O(2ⁿ) or O(2ⁿ · n) | Subsets, bitmask DP, backtracking with pruning |
| n ≤ 40 | O(2^(n/2) · n) | Meet in the middle: enumerate each half, sort one, search it from the other |
| n ≤ 500 | O(n³) | Interval DP, Floyd–Warshall |
| n ≤ 5,000 | O(n²) | Two-dimensional DP, pairs |
| n ≤ 10⁵–10⁶ | O(n log n) or O(n) | Sorting plus a sweep, heaps, binary search, sliding window, monotonic stack, hash maps |
| Values up to 10⁹ with a monotone feasibility check | O(n log V) | Binary search on the answer |

## 39d.3 Pattern 1 — Two pointers

**Recognize it.** The input is sorted (or can be sorted without losing the answer), and you need a pair, a triplet, or an in-place rewrite. Words to listen for: "sorted", "pair", "triplet", "in place", "remove duplicates", "partition".

**The idea and its invariant.** Two indices move toward each other, or one reads while the other writes. For a sorted pair sum, the invariant is that no pair outside `[left, right]` can be the answer: if the sum is too small, every pair that uses `nums[left]` with a smaller right element is smaller still, so `left` can move. For a read–write pass, everything left of `write` is the finished output. Each step discards at least one candidate, so the scan is linear.

```python
def pair_with_target_sum(nums, target):
    """Sorted input: indices (i, j), i < j, with nums[i] + nums[j] == target (LC 167, 0-based)."""
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return left, right
        if total < target:
            left += 1          # need a bigger sum: only moving left up can give one
        else:
            right -= 1
    return None


def remove_duplicates(nums):
    """Sorted input: keep one copy of each value in place, return the new length (LC 26)."""
    if not nums:
        return 0
    write = 1                  # nums[:write] holds the distinct values seen so far
    for read in range(1, len(nums)):
        if nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write


def sorted_squares(nums):
    """Sorted input with negatives: the squares in sorted order (LC 977), filled from the back."""
    n = len(nums)
    out = [0] * n
    left, right = 0, n - 1
    for pos in range(n - 1, -1, -1):
        if abs(nums[left]) > abs(nums[right]):
            out[pos] = nums[left] ** 2
            left += 1
        else:
            out[pos] = nums[right] ** 2
            right -= 1
    return out


def three_sum(nums):
    """All unique triplets that sum to zero (LC 15): fix one value, two pointers on the rest."""
    nums = sorted(nums)
    out = []
    for i in range(len(nums) - 2):
        if nums[i] > 0:
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                out.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
    return out


def sort_colors(nums):
    """Dutch national flag (LC 75): 0s, 1s and 2s in one pass, in place."""
    low, i, high = 0, 0, len(nums) - 1
    while i <= high:
        if nums[i] == 0:
            nums[low], nums[i] = nums[i], nums[low]
            low += 1
            i += 1
        elif nums[i] == 1:
            i += 1
        else:                  # do not advance i: the swapped-in value is unexamined
            nums[high], nums[i] = nums[i], nums[high]
            high -= 1
```

**Complexity.** O(n) time and O(1) extra space for one pass; 3Sum is O(n²) after an O(n log n) sort. The sort is often the real cost: say so.

**Practice set.** 167 Two Sum II - Input Array Is Sorted; 26 Remove Duplicates from Sorted Array; 977 Squares of a Sorted Array; 15 3Sum; 16 3Sum Closest; 259 3Sum Smaller†; 75 Sort Colors; 18 4Sum; 844 Backspace String Compare; 11 Container With Most Water; 42 Trapping Rain Water (two-pointer version).

**Pitfalls.** In 3Sum, skip a repeated fixed value before its pass and repeated pointer values only after a match: forgetting either reports a triplet twice, and skipping pointer repeats before checking loses triplets like [−2, 1, 1]; `left <= right` where `left < right` is meant (a pair needs two distinct indices); forgetting that sorting destroys original indices when the problem asks for them (use 1 Two Sum with a hash map instead).

**Follow-ups.** "The array is not sorted": hash map, O(n) time and O(n) space, or sort with indices. "Return all pairs, including duplicates": count multiplicities. "k-sum": recurse down to 2-sum, O(n^(k−1)). "Closest sum": track the best gap while moving the pointers.

## 39d.4 Pattern 2 — Islands (matrix traversal)

**Recognize it.** A grid of cells and a question about connected regions: count them, measure the biggest, recolor one, find the ones that touch (or do not touch) the border, or spread something from many sources at once ("rotting oranges", "distance to the nearest gate").

**The idea and its invariant.** Treat each cell as a graph node with up to four neighbors. Scan every cell; each unvisited land cell starts a breadth-first (or depth-first) search that marks its whole region. Every cell is marked once, so the scan is linear in the grid size. Mark a cell when you add it to the queue, not when you remove it, or the same cell can be queued several times.

```python
def _flood(grid, r, c, target, mark):
    """Iterative BFS from (r, c) over 4-connected cells equal to target; marks them; returns the size."""
    rows, cols = len(grid), len(grid[0])
    grid[r][c] = mark          # mark on enqueue, not on dequeue, or cells are queued twice
    queue = deque([(r, c)])
    size = 0
    while queue:
        x, y = queue.popleft()
        size += 1
        for dx, dy in DIRS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == target:
                grid[nx][ny] = mark
                queue.append((nx, ny))
    return size


def num_islands(grid):
    """Count 4-connected groups of "1" (LC 200). Mutates the grid."""
    count = 0
    for r in range(len(grid)):
        for c in range(len(grid[0]) if grid else 0):
            if grid[r][c] == "1":
                _flood(grid, r, c, "1", "0")
                count += 1
    return count


def max_area_of_island(grid):
    """Size of the largest 4-connected group of 1s (LC 695). Mutates the grid."""
    best = 0
    for r in range(len(grid)):
        for c in range(len(grid[0]) if grid else 0):
            if grid[r][c] == 1:
                best = max(best, _flood(grid, r, c, 1, 0))
    return best


def flood_fill(image, sr, sc, color):
    """Recolor the region that contains (sr, sc) (LC 733)."""
    start = image[sr][sc]
    if start != color:         # same color would loop forever: nothing to do
        _flood(image, sr, sc, start, color)
    return image


def closed_island(grid):
    """Islands of 0s not touching the border (LC 1254): sink border-connected land first."""
    rows, cols = len(grid), len(grid[0])
    for r in range(rows):
        for c in range(cols):
            if (r in (0, rows - 1) or c in (0, cols - 1)) and grid[r][c] == 0:
                _flood(grid, r, c, 0, 1)
    count = 0
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 0:
                _flood(grid, r, c, 0, 1)
                count += 1
    return count
```

**Complexity.** O(rows × cols) time; O(rows × cols) worst-case space for the queue (or the recursion stack in DFS). Iterative BFS avoids Python's default recursion limit of 1,000, which a 100 × 100 grid of land would exceed with recursive DFS.

**Practice set.** 200 Number of Islands; 695 Max Area of Island; 733 Flood Fill; 463 Island Perimeter; 1254 Number of Closed Islands; 1020 Number of Enclaves; 130 Surrounded Regions; 694 Number of Distinct Islands† (record each island's shape relative to its first cell); 994 Rotting Oranges (multi-source BFS); 417 Pacific Atlantic Water Flow; 1559 Detect Cycles in 2D Grid.

**Pitfalls.** Mutating the caller's grid when they need it later (say you will, or copy); mixing up rows and columns in bounds checks; recursive DFS overflowing the stack on large grids; marking on dequeue.

**Follow-ups.** "Count islands as land is added one cell at a time" (305 Number of Islands II†): union-find, near O(1) per addition. "Diagonal neighbors count": eight directions. "Shortest path from many sources": put all sources in the queue at distance 0. "The grid is too big for memory": process row by row with union-find over two rows.

## 39d.5 Pattern 3 — Fast and slow pointers

**Recognize it.** A linked list, or any sequence defined by "next", and a question about a cycle, the middle, or the k-th node from the end. Also disguised cycles: "repeat this digit operation — does it reach 1?" (202 Happy Number) and "n + 1 values in 1..n — find the duplicate without changing the array" (287).

**The idea and its invariant.** One pointer moves one step, the other two. If there is a cycle, the fast pointer gains one node per step and must meet the slow one inside the cycle. After they meet, a pointer started from the head and one left at the meeting point, moving one step each, meet at the cycle's entrance: if the tail before the cycle has length a and they met b steps into a cycle of length L, the slow pointer walked a + b and the fast 2(a + b), so a + b is a multiple of L and walking a more steps from the meeting point lands on the entrance. Without a cycle, the fast pointer reaches the end when the slow one is at the middle.

```python
def has_cycle(head):
    """Floyd's cycle detection (LC 141)."""
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            return True
    return False


def cycle_start(head):
    """Node where the cycle begins, or None (LC 142): after the meeting, walk one pointer from head."""
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            entry = head
            while entry is not slow:
                entry, slow = entry.next, slow.next
            return entry
    return None


def middle_node(head):
    """Middle node; the second middle for even lengths, as LC 876 specifies."""
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow


def is_palindrome_list(head):
    """O(1) extra space (LC 234): reverse the second half, compare, then restore it."""
    if head is None or head.next is None:
        return True
    first_end = head
    fast = head
    while fast.next and fast.next.next:
        first_end, fast = first_end.next, fast.next.next
    second = reverse_list(first_end.next)
    p1, p2, same = head, second, True
    while p2:
        if p1.val != p2.val:
            same = False
            break
        p1, p2 = p1.next, p2.next
    first_end.next = reverse_list(second)   # leave the input as we found it
    return same


def is_happy(n):
    """Floyd's algorithm on the digit-square sequence (LC 202)."""
    def step(x):
        return sum(int(d) ** 2 for d in str(x))
    slow, fast = n, step(n)
    while fast != 1 and slow != fast:
        slow, fast = step(slow), step(step(fast))
    return fast == 1


def find_duplicate(nums):
    """n + 1 values in 1..n, one repeated (LC 287): cycle entry of i -> nums[i]; O(1) space, read-only."""
    slow = fast = nums[0]
    while True:
        slow, fast = nums[slow], nums[nums[fast]]
        if slow == fast:
            break
    entry = nums[0]
    while entry != slow:
        entry, slow = nums[entry], nums[slow]
    return entry
```

**Complexity.** O(n) time, O(1) space — the point of the pattern. A hash set of visited nodes also works in O(n) space; say that first, then improve.

**Practice set.** 141 Linked List Cycle; 142 Linked List Cycle II; 876 Middle of the Linked List; 234 Palindrome Linked List; 202 Happy Number; 143 Reorder List; 457 Circular Array Loop; 287 Find the Duplicate Number; 19 Remove Nth Node From End of List (gap pointers).

**Pitfalls.** Checking `fast.next.next` without first checking `fast.next`; comparing values instead of node identity (`is`) when lists contain duplicates; for palindromes, leaving the list reversed — restore it, as the template does, because a function that silently mutates its input fails a code review.

**Follow-ups.** "Length of the cycle": after meeting, count steps until the slow pointer returns. "Do it without modifying the list" (palindrome): copy to an array in O(n) space, or reverse and restore. "Why does 287 work?": the map i → nums[i] sends 0..n into 1..n, so the walk from 0 must enter a cycle that 0 is not on; the cycle's entrance then has two predecessors, one on the path from 0 and one on the cycle, so two indices hold it — it is the duplicate.

## 39d.6 Pattern 4 — Sliding window

**Recognize it.** The answer is a contiguous subarray or substring, and you need the longest, the shortest, a count, or all of them, subject to a condition on the window (a sum, a number of distinct characters, character counts matching). Fixed size ("every window of k") or variable size ("longest with at most k distinct").

**The idea and its invariant.** Expand the right edge one element at a time; shrink the left edge while the window breaks the condition (for "longest") or while it still satisfies it (for "shortest"). The invariant: for "longest", after shrinking, `[left, right]` is the longest valid window ending at `right`; for "shortest", the last window recorded before shrinking breaks the condition is the shortest valid one ending at `right`. Each index enters and leaves once, so the work is linear. This only works when the condition is *monotone*: if a window is valid, so is every window inside it (for "longest"), or every window containing it (for "shortest"). Negative numbers break monotonicity for sums — then use prefix sums (39d.23).

```python
def max_sum_subarray_k(nums, k):
    """Fixed window: the largest sum of k consecutive values (LC 643 asks for the average)."""
    if not 0 < k <= len(nums):
        raise ValueError("need 0 < k <= len(nums)")
    window = best = sum(nums[:k])
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best


def min_subarray_len(target, nums):
    """Shortest subarray with sum >= target, positive values (LC 209); 0 if none."""
    best = len(nums) + 1
    window = left = 0
    for right, x in enumerate(nums):
        window += x
        while window >= target:            # shrink while the window still qualifies
            best = min(best, right - left + 1)
            window -= nums[left]
            left += 1
    return 0 if best > len(nums) else best


def longest_with_k_distinct(seq, k):
    """Longest run with at most k distinct values (LC 340). Fruit Into Baskets (LC 904) is k = 2."""
    counts = Counter()
    left = best = 0
    for right, item in enumerate(seq):
        counts[item] += 1
        while len(counts) > k:
            counts[seq[left]] -= 1
            if counts[seq[left]] == 0:
                del counts[seq[left]]
            left += 1
        best = max(best, right - left + 1)
    return best


def length_of_longest_substring(s):
    """No repeated characters (LC 3): jump the left edge past the previous occurrence."""
    last_seen = {}
    left = best = 0
    for right, ch in enumerate(s):
        if last_seen.get(ch, -1) >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best


def character_replacement(s, k):
    """Longest run that can be made one letter with at most k replacements (LC 424)."""
    counts = Counter()
    left = max_freq = best = 0
    for right, ch in enumerate(s):
        counts[ch] += 1
        max_freq = max(max_freq, counts[ch])   # may go stale; only a larger max_freq can improve best
        if right - left + 1 - max_freq > k:
            counts[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


def find_anagrams(s, p):
    """Start indices of p's anagrams in s (LC 438): fixed window of len(p) with counts."""
    if len(p) > len(s):
        return []
    need, window = Counter(p), Counter(s[:len(p)])
    out = [0] if window == need else []
    for i in range(len(p), len(s)):
        window[s[i]] += 1
        window[s[i - len(p)]] -= 1
        if window[s[i - len(p)]] == 0:
            del window[s[i - len(p)]]
        if window == need:
            out.append(i - len(p) + 1)
    return out


def min_window(s, t):
    """Smallest window of s containing every character of t, with multiplicity (LC 76)."""
    if not s or not t:
        return ""
    need = Counter(t)
    missing = len(t)
    left = 0
    best_len, best_start = float("inf"), 0
    for right, ch in enumerate(s):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1                      # negative counts are surplus inside the window
        if missing == 0:
            while need[s[left]] < 0:       # drop surplus characters from the left
                need[s[left]] += 1
                left += 1
            if right - left + 1 < best_len:
                best_len, best_start = right - left + 1, left
            need[s[left]] += 1             # give up one required character and keep scanning
            missing += 1
            left += 1
    return "" if best_len == float("inf") else s[best_start:best_start + best_len]
```

**Complexity.** O(n) time. Space is O(k) or O(alphabet) for the counts.

**Practice set.** 643 Maximum Average Subarray I; 209 Minimum Size Subarray Sum; 904 Fruit Into Baskets; 340 Longest Substring with At Most K Distinct Characters†; 3 Longest Substring Without Repeating Characters; 424 Longest Repeating Character Replacement; 1004 Max Consecutive Ones III; 567 Permutation in String; 438 Find All Anagrams in a String; 713 Subarray Product Less Than K; 76 Minimum Window Substring; 30 Substring with Concatenation of All Words; 239 Sliding Window Maximum (with a monotonic deque, 39d.21).

**Pitfalls.** Using a window on sums with negative values; updating the answer before shrinking (for "longest") or after shrinking (for "shortest") — the wrong order is an off-by-one that two examples will not reveal; forgetting to delete zero counts, so `len(counts)` overstates the distinct count. In 424, `max_freq` is allowed to go stale: the window only needs to grow when a strictly larger frequency appears, which is why the template uses `if` rather than `while` and never lowers `max_freq`.

**Follow-ups.** "Count the subarrays with at most k distinct": add `right − left + 1` at each step; "exactly k" is at-most(k) − at-most(k − 1) (992 Subarrays with K Different Integers). "Now values can be negative" (209 becomes 862 Shortest Subarray with Sum at Least K): the window is no longer monotone, so keep prefix-sum indices in a deque with increasing sums, pop (and measure) the front while the current sum minus the front's is at least k, and pop the back while its sum is not smaller than the current one, O(n). "The stream does not fit in memory": the window state is all you keep. "Return the window, not the length": record `left` with the best length, as `min_window` does.

## 39d.7 Pattern 5 — Merge intervals

**Recognize it.** Pairs of start and end: meetings, bookings, ranges of IDs, time slots. Questions about overlap, merging, inserting, intersecting, free time, or how many resources are needed at the busiest moment.

**The idea and its invariant.** Sort by start; then each interval either overlaps the last merged one (its start is at most the last end) or begins a new block. After processing interval i, the output is the merged form of the first i intervals. For "how many rooms", keep a min-heap of the end times of meetings in progress: the heap size is the number of rooms in use, and the earliest end tells you whether a room has freed up. Decide early whether intervals are closed ([1, 2] and [2, 3] overlap) or half-open (a meeting ending at 10 frees the room for one starting at 10) — that choice decides between `<` and `<=` in every comparison.

```python
def merge_intervals(intervals):
    """Merge overlapping closed intervals; touching ones ([1,2], [2,3]) merge too (LC 56)."""
    out = []
    for start, end in sorted(intervals):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def insert_interval(intervals, new):
    """Insert into sorted, non-overlapping intervals and merge (LC 57), in O(n)."""
    out, i, n = [], 0, len(intervals)
    start, end = new
    while i < n and intervals[i][1] < start:          # entirely before
        out.append(intervals[i])
        i += 1
    while i < n and intervals[i][0] <= end:           # overlapping: absorb
        start, end = min(start, intervals[i][0]), max(end, intervals[i][1])
        i += 1
    out.append([start, end])
    out.extend(intervals[i:])                         # entirely after
    return out


def interval_intersection(a, b):
    """Intersections of two sorted, internally disjoint lists (LC 986)."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if lo <= hi:
            out.append([lo, hi])
        if a[i][1] < b[j][1]:                          # drop the one that ends first
            i += 1
        else:
            j += 1
    return out


def min_meeting_rooms(intervals):
    """Rooms needed for half-open meetings [start, end) (LC 253): min-heap of end times."""
    ends = []
    for start, end in sorted(intervals):
        if ends and ends[0] <= start:                  # earliest-ending room is free again
            heapq.heapreplace(ends, end)
        else:
            heapq.heappush(ends, end)
    return len(ends)
```

**Complexity.** O(n log n) for the sort, then O(n); rooms is O(n log n) with the heap. Insert into an already sorted list is O(n) with no sort.

**Practice set.** 56 Merge Intervals; 57 Insert Interval; 986 Interval List Intersections; 252 Meeting Rooms†; 253 Meeting Rooms II†; 435 Non-overlapping Intervals (greedy by end, 39d.23); 452 Minimum Number of Arrows to Burst Balloons; 759 Employee Free Time†; 1094 Car Pooling; 729 My Calendar I.

**Pitfalls.** Sorting by end when the merge needs start order (and vice versa for the greedy "keep the most intervals" problem, which sorts by end); mutating the input's inner lists when merging (copy if the caller keeps them); open versus closed endpoints.

**Follow-ups.** "Intervals arrive one at a time and you must answer queries": a balanced tree or sorted container keyed by start, O(log n) per insert. "Maximum overlap with weights": a sweep line over +weight/−weight events sorted by time, with ends before starts at equal times for half-open intervals. "Free time across many calendars": merge everything, then read the gaps.

## 39d.8 Pattern 6 — Cyclic sort

**Recognize it.** The values are in a known range — 1..n or 0..n — and the question is which values are missing, duplicated, or misplaced, usually with "O(1) extra space" or "without sorting".

**The idea and its invariant.** Index i is the home of value i + 1. Walk the array; while the current value is not at its home and its home does not already hold the same value, swap it home. Every swap puts one value in its final position, and a value at home never moves again, so there are at most n swaps and the pass is O(n) even with the inner `while`. Afterwards, any index i whose value is wrong tells you a missing number (i + 1) and a duplicate (the value it holds).

```python
def cyclic_sort(nums):
    """Values are exactly 1..n: put each value at index value - 1 in O(n), in place."""
    i = 0
    while i < len(nums):
        j = nums[i] - 1
        if nums[i] != nums[j]:
            nums[i], nums[j] = nums[j], nums[i]        # each swap places one value for good
        else:
            i += 1
    return nums


def missing_number(nums):
    """n distinct values from 0..n, one missing (LC 268). Mutates nums; value n has no slot."""
    i, n = 0, len(nums)
    while i < n:
        j = nums[i]
        if j < n and nums[i] != nums[j]:
            nums[i], nums[j] = nums[j], nums[i]
        else:
            i += 1
    for i in range(n):
        if nums[i] != i:
            return i
    return n


def find_disappeared_numbers(nums):
    """Values in 1..n, some repeated: the values that never appear (LC 448). Mutates nums."""
    i = 0
    while i < len(nums):
        j = nums[i] - 1
        if nums[i] != nums[j]:
            nums[i], nums[j] = nums[j], nums[i]
        else:
            i += 1
    return [i + 1 for i, value in enumerate(nums) if value != i + 1]


def find_all_duplicates(nums):
    """Values in 1..n, each once or twice: the ones seen twice, in O(n) (LC 442). Mutates nums."""
    i = 0
    while i < len(nums):
        j = nums[i] - 1
        if nums[i] != nums[j]:
            nums[i], nums[j] = nums[j], nums[i]
        else:
            i += 1
    return [value for i, value in enumerate(nums) if value != i + 1]   # unsorted: sorting costs O(n log n)


def first_missing_positive(nums):
    """Smallest missing positive in O(n) time and O(1) extra space (LC 41). Mutates nums."""
    n = len(nums)
    i = 0
    while i < n:
        j = nums[i] - 1
        if 0 <= j < n and nums[i] != nums[j]:          # ignore values with no slot
            nums[i], nums[j] = nums[j], nums[i]
        else:
            i += 1
    for i in range(n):
        if nums[i] != i + 1:
            return i + 1
    return n + 1
```

**Complexity.** O(n) time, O(1) extra space — by rearranging the input. If the input must not change, 268 has a read-only XOR answer (39d.16) and 287 has the cycle answer (39d.5).

**Practice set.** 268 Missing Number; 448 Find All Numbers Disappeared in an Array; 442 Find All Duplicates in an Array; 645 Set Mismatch; 287 Find the Duplicate Number (with the read-only constraint, cycle detection is the expected answer); 41 First Missing Positive.

**Pitfalls.** Swapping with an index computed after the first assignment (compute `j` first, as the templates do); infinite loops when a duplicate is already home — the `nums[i] != nums[j]` test prevents them; values outside the range (zero, negatives, larger than n) must be skipped, as in 41.

**Follow-ups.** "Find the duplicate and the missing number together" (645): after the sort, the one wrong index gives both. "First k missing positives": continue past n with the values you saw. "Explain why it is O(n) with a nested loop": the swap count argument above.

## 39d.9 Pattern 7 — In-place reversal of a linked list

**Recognize it.** Reverse a linked list, or part of one, or every block of k nodes, without allocating a second list. Also: rotate a list, swap pairs, reorder halves.

**The idea and its invariant.** Three references: `prev` (the already-reversed part), `curr` (the next node to flip), and `nxt` (saved before you overwrite `curr.next`). After each step, `prev` heads a reversed list of everything processed so far and `curr` heads the untouched remainder. A dummy node before the head removes the special case where the head itself changes, which is most of the bugs in sub-list problems.

```python
def reverse_list(head):
    """Reverse a singly linked list (LC 206)."""
    prev, curr = None, head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev, curr = curr, nxt
    return prev


def reverse_between(head, left, right):
    """Reverse positions left..right, 1-indexed, in one pass (LC 92)."""
    dummy = ListNode(0, head)
    before = dummy
    for _ in range(left - 1):
        before = before.next
    curr = before.next
    for _ in range(right - left):          # move curr.next to the front of the sub-list
        nxt = curr.next
        curr.next = nxt.next
        nxt.next = before.next
        before.next = nxt
    return dummy.next


def reverse_k_group(head, k):
    """Reverse every full block of k nodes; a short tail stays as it is (LC 25)."""
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        kth = group_prev
        for _ in range(k):
            kth = kth.next
            if kth is None:
                return dummy.next
        group_next = kth.next
        prev, curr = group_next, group_prev.next
        while curr is not group_next:
            nxt = curr.next
            curr.next = prev
            prev, curr = curr, nxt
        first = group_prev.next            # becomes the block's tail
        group_prev.next = kth
        group_prev = first


def rotate_right(head, k):
    """Rotate the list right by k places (LC 61): close it into a ring, then cut."""
    if head is None or head.next is None or k == 0:
        return head
    length, tail = 1, head
    while tail.next:
        tail = tail.next
        length += 1
    k %= length
    if k == 0:
        return head
    tail.next = head
    new_tail = head
    for _ in range(length - k - 1):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next = None
    return new_head
```

**Complexity.** O(n) time, O(1) space. A recursive reversal is shorter but uses O(n) stack.

**Practice set.** 206 Reverse Linked List; 92 Reverse Linked List II; 25 Reverse Nodes in k-Group; 24 Swap Nodes in Pairs; 61 Rotate List; 143 Reorder List (middle, reverse the second half, interleave); 2074 Reverse Nodes in Even Length Groups.

**Pitfalls.** Losing the rest of the list by overwriting `curr.next` before saving it; forgetting to reconnect the reversed block to the nodes before and after it; reversing a partial last block in 25 (it must stay as it is). Draw three boxes and the arrows before you code — interviewers expect the drawing.

**Follow-ups.** "Reverse alternate blocks of k": a flag that skips every other block. "Do it recursively": state the O(n) stack cost. "Doubly linked list": swap `prev` and `next` on each node.

## 39d.10 Pattern 8 — Tree breadth-first search

**Recognize it.** A tree question whose answer is organized by depth: level order, averages or maxima per level, the right-side view, zigzag order, connecting nodes on the same level, the minimum depth, the maximum width.

**The idea and its invariant.** A queue holds the frontier. At the top of each loop, the queue contains exactly one whole level, so taking `len(queue)` nodes processes that level and enqueues the next. The first leaf BFS reaches is the shallowest one, which is why minimum depth can stop early where DFS cannot.

```python
def level_order(root):
    """Values level by level (LC 102): the queue length at the top of the loop is the level size."""
    if root is None:
        return []
    out, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        out.append(level)
    return out


def level_order_bottom(root):
    """Levels from the leaves up (LC 107)."""
    return level_order(root)[::-1]


def zigzag_level_order(root):
    """Alternate left-to-right and right-to-left (LC 103)."""
    return [lvl if depth % 2 == 0 else lvl[::-1] for depth, lvl in enumerate(level_order(root))]


def right_side_view(root):
    """Last value of each level (LC 199)."""
    return [lvl[-1] for lvl in level_order(root)]


def min_depth(root):
    """Nodes on the shortest root-to-leaf path (LC 111): BFS stops at the first leaf."""
    if root is None:
        return 0
    queue = deque([(root, 1)])
    while queue:
        node, depth = queue.popleft()
        if node.left is None and node.right is None:
            return depth
        if node.left:
            queue.append((node.left, depth + 1))
        if node.right:
            queue.append((node.right, depth + 1))
    return 0
```

**Complexity.** O(n) time; O(w) space, where w is the widest level — up to n/2 for a complete tree. DFS uses O(h) for the height instead; mention the trade when asked which to use.

**Practice set.** 102 Binary Tree Level Order Traversal; 107 Binary Tree Level Order Traversal II; 103 Binary Tree Zigzag Level Order Traversal; 637 Average of Levels in Binary Tree; 111 Minimum Depth of Binary Tree; 199 Binary Tree Right Side View; 515 Find Largest Value in Each Tree Row; 116 and 117 Populating Next Right Pointers in Each Node (I and II); 662 Maximum Width of Binary Tree (index nodes as in a heap: children of i are 2i and 2i + 1).

**Pitfalls.** Iterating `while queue` without fixing the level size first (levels blur); using a Python list with `pop(0)`, which is O(n) per pop — use `collections.deque`; reversing with `insert(0, …)` inside the loop instead of reversing each level once.

**Follow-ups.** "The tree is a general graph": add a visited set. "Connect next pointers in O(1) extra space" (117): walk the current level through the next pointers you built on the previous one. "Vertical order" (987): record (column, row, value) for every node, sort, and group by column.

## 39d.11 Pattern 9 — Tree depth-first search

**Recognize it.** Root-to-leaf paths, path sums, values that depend on the subtrees (height, diameter, balance, maximum path), validation (is it a binary search tree?), lowest common ancestors.

**The idea and its invariant.** Recursion where each call either carries information down (the remaining sum, the allowed value range) or returns information up (a height, a best downward gain). The key design decision is what the function returns to its parent, which is often different from the final answer — in 124 a node returns the best path that a parent can extend, while the global best may bend through the node. When building lists of paths, keep one shared path list, append on the way in and pop on the way out, and copy it only when you record an answer.

```python
def has_path_sum(root, target):
    """Is there a root-to-leaf path with this sum (LC 112)?"""
    if root is None:
        return False
    if root.left is None and root.right is None:
        return root.val == target
    rest = target - root.val
    return has_path_sum(root.left, rest) or has_path_sum(root.right, rest)


def path_sum_all(root, target):
    """Every root-to-leaf path with this sum (LC 113): one shared path list, append and pop."""
    out, path = [], []

    def dfs(node, remaining):
        if node is None:
            return
        path.append(node.val)
        if node.left is None and node.right is None and remaining == node.val:
            out.append(path[:])            # copy: path keeps changing
        else:
            dfs(node.left, remaining - node.val)
            dfs(node.right, remaining - node.val)
        path.pop()

    dfs(root, target)
    return out


def count_paths_with_sum(root, target):
    """Downward paths starting and ending anywhere with this sum (LC 437): prefix sums on the path."""
    seen = Counter({0: 1})

    def dfs(node, running):
        if node is None:
            return 0
        running += node.val
        count = seen[running - target]
        seen[running] += 1
        count += dfs(node.left, running) + dfs(node.right, running)
        seen[running] -= 1                 # leaving this node: its prefix is off the path
        return count

    return dfs(root, 0)


def max_path_sum(root):
    """Best node-to-node path sum (LC 124): each call returns the best downward gain."""
    best = float("-inf")

    def gain(node):
        nonlocal best
        if node is None:
            return 0
        left, right = max(gain(node.left), 0), max(gain(node.right), 0)
        best = max(best, node.val + left + right)       # path that bends at this node
        return node.val + max(left, right)              # path a parent can extend

    gain(root)
    return best


def diameter_of_binary_tree(root):
    """Edges on the longest path between any two nodes (LC 543)."""
    best = 0

    def height(node):
        nonlocal best
        if node is None:
            return 0
        left, right = height(node.left), height(node.right)
        best = max(best, left + right)
        return 1 + max(left, right)

    height(root)
    return best


def lowest_common_ancestor(root, p, q):
    """LCA of two nodes in a binary tree (LC 236)."""
    if root is None or root is p or root is q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if left and right:
        return root
    return left or right
```

**Complexity.** O(n) time, O(h) space for the recursion (O(n) for a degenerate tree); listing all paths costs O(n · h) for the copies. 437 with prefix sums is O(n) instead of the O(n²) "start a search from every node".

**Practice set.** 112 Path Sum; 113 Path Sum II; 437 Path Sum III; 129 Sum Root to Leaf Numbers; 257 Binary Tree Paths; 543 Diameter of Binary Tree; 124 Binary Tree Maximum Path Sum; 98 Validate Binary Search Tree; 236 Lowest Common Ancestor of a Binary Tree; 1430 Check If a String Is a Valid Sequence from Root to Leaves Path in a Binary Tree†; 110 Balanced Binary Tree.

**Pitfalls.** Treating a node with one child as a leaf (path sums must end at real leaves); appending `path` instead of `path[:]` (every recorded path aliases the same list); validating a BST by comparing only parent and child instead of passing the allowed range down; Python recursion depth on a 10⁵-node chain — use an explicit stack or raise the limit and say why.

**Follow-ups.** "Paths can start and end anywhere" (437): prefix sums. "Return the path, not the sum": carry the path or reconstruct from parent pointers. "Iterative DFS": a stack of (node, state) pairs; in-order traversal with a stack is worth having ready for BST questions (230 Kth Smallest Element in a BST).

## 39d.12 Pattern 10 — Two heaps

**Recognize it.** You must keep a set of numbers split into a smaller half and a larger half while values arrive (or leave): running medians, sliding-window medians, or scheduling where you repeatedly need the best of one group and the cheapest of another (maximize capital).

**The idea and its invariant.** A max-heap holds the lower half and a min-heap the upper half; every value in the lower heap is at most every value in the upper heap, and the sizes differ by at most one. The median is the top of the larger heap or the mean of both tops. Until Python 3.14, `heapq` had only min-heap functions, so the max-heap stores negated values; 3.14 added `heappush_max` and its siblings, but negation works on every version. For sliding windows, values must also leave; deleting from the middle of a heap is O(k), so the template marks departed values in a `delayed` counter and discards them when they reach a top — lazy deletion — while tracking the valid sizes separately.

```python
class MedianFinder:
    """Running median (LC 295): max-heap of the lower half (negated) and min-heap of the upper half."""

    def __init__(self):
        self.low = []      # max-heap via negation; may hold one more element than high
        self.high = []

    def add_num(self, num):
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))   # largest of low moves up
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def find_median(self):
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2


def median_sliding_window(nums, k):
    """Median of every window of size k (LC 480): two heaps with lazy deletion, O(n log n)."""
    low, high = [], []                 # low: max-heap (negated); high: min-heap
    delayed = Counter()                # values removed from the window but still inside a heap
    low_size = high_size = 0           # valid elements only

    def prune(heap, sign):
        while heap and delayed[sign * heap[0]]:
            delayed[sign * heap[0]] -= 1
            heapq.heappop(heap)

    def rebalance():
        nonlocal low_size, high_size
        if low_size > high_size + 1:
            heapq.heappush(high, -heapq.heappop(low))
            low_size, high_size = low_size - 1, high_size + 1
            prune(low, -1)
        elif low_size < high_size:
            heapq.heappush(low, -heapq.heappop(high))
            low_size, high_size = low_size + 1, high_size - 1
            prune(high, 1)

    def add(x):
        nonlocal low_size, high_size
        if not low or x <= -low[0]:
            heapq.heappush(low, -x)
            low_size += 1
        else:
            heapq.heappush(high, x)
            high_size += 1
        rebalance()

    def remove(x):
        nonlocal low_size, high_size
        delayed[x] += 1
        if x <= -low[0]:
            low_size -= 1
            if x == -low[0]:
                prune(low, -1)
        else:
            high_size -= 1
            if high and x == high[0]:
                prune(high, 1)
        rebalance()

    out = []
    for i, x in enumerate(nums):
        add(x)
        if i >= k:
            remove(nums[i - k])
        if i >= k - 1:
            out.append(float(-low[0]) if k % 2 else (-low[0] + high[0]) / 2)
    return out


def find_maximized_capital(k, w, profits, capital):
    """IPO / Maximize Capital (LC 502): unlock projects by capital, take the most profitable each time."""
    projects = sorted(zip(capital, profits))   # plays the role of the min-heap by capital
    available = []                             # max-heap of unlocked profits (negated)
    i = 0
    for _ in range(k):
        while i < len(projects) and projects[i][0] <= w:
            heapq.heappush(available, -projects[i][1])
            i += 1
        if not available:
            break
        w -= heapq.heappop(available)
    return w
```

**Complexity.** O(log n) per insertion and O(1) per median query; sliding-window median O(n log n) overall; maximize capital O(n log n).

**Practice set.** 295 Find Median from Data Stream; 480 Sliding Window Median; 502 IPO; 436 Find Right Interval (two heaps or sort plus binary search); 1834 Single-Threaded CPU (heap of available tasks).

**Pitfalls.** Forgetting to negate on the way out of the max-heap; rebalancing before moving the largest of the lower half up (the template always routes a new value through the lower heap so the order invariant cannot break); for lazy deletion, deciding which heap a departing value belongs to by comparing with the lower heap's top — values equal to it are in the lower heap or tie with the upper one, and either removal is valid because they are equal.

**Follow-ups.** "Most values are in a small range": a counting array gives O(1) updates and an O(range) median. "Percentile other than the median": size the heaps in that ratio. "Median of two sorted arrays" (4): binary search on the partition, not heaps.

## 39d.13 Pattern 11 — Subsets

**Recognize it.** "Return all subsets", "all permutations", "all combinations", "all strings you can make by …". The output itself is exponential, so the goal is to generate it without duplicates or wasted work.

**The idea and its invariant.** Breadth-first construction: start with the empty subset; each new element creates a copy of every existing subset with the element added, so after processing i elements the list holds exactly the subsets of those i elements. With duplicates in the input, sort first, and let a repeated value extend only the subsets created in the previous step — extending older ones would recreate subsets you already have. Permutations insert each new element at every position of every partial permutation. The same problems can be written with backtracking (39d.17); know both, because interviewers ask for the other one as the follow-up.

```python
def subsets(nums):
    """All subsets (LC 78), breadth-first: each new element doubles the list."""
    out = [[]]
    for x in nums:
        out += [s + [x] for s in out]
    return out


def subsets_with_dup(nums):
    """All distinct subsets with duplicates in the input (LC 90)."""
    nums = sorted(nums)
    out = [[]]
    start = 0                      # where the previous step's additions begin
    for i, x in enumerate(nums):
        begin = start if i > 0 and x == nums[i - 1] else 0   # a repeat extends only the newest subsets
        start = len(out)
        out += [s + [x] for s in out[begin:start]]
    return out


def permutations(nums):
    """All permutations of distinct values (LC 46): insert each value at every position."""
    perms = [[]]
    for x in nums:
        perms = [p[:i] + [x] + p[i:] for p in perms for i in range(len(p) + 1)]
    return perms


def letter_case_permutation(s):
    """Every string from changing the case of letters (LC 784)."""
    out = [s]
    for i, ch in enumerate(s):
        if ch.isalpha():
            out += [t[:i] + t[i].swapcase() + t[i + 1:] for t in out]
    return out
```

**Complexity.** Subsets: O(n · 2ⁿ) time and space (2ⁿ subsets of average length n/2). Permutations: O(n · n!). Say the output size is the floor; no algorithm can beat it.

**Practice set.** 78 Subsets; 90 Subsets II; 46 Permutations; 47 Permutations II; 784 Letter Case Permutation; 22 Generate Parentheses; 320 Generalized Abbreviation†; 241 Different Ways to Add Parentheses; 95 Unique Binary Search Trees II; 96 Unique Binary Search Trees (counting only: Catalan numbers, a DP).

**Pitfalls.** Iterating over a list while appending to it (the templates build a new list or slice a fixed range); deduplicating with a set of tuples at the end, which works but wastes exponential work — the sorted "extend only the newest" rule avoids generating duplicates at all.

**Follow-ups.** "Generate lazily": a generator or an iterator over bitmasks 0..2ⁿ − 1. "Only subsets of size k": combinations with a start index (77 Combinations). "Count them instead of listing them": a formula or DP, never the list.

## 39d.14 Pattern 12 — Modified binary search

**Recognize it.** Sorted data, or data that is sorted in pieces (rotated, a mountain, an infinite stream), or — the most valuable variant — a question of the form "the smallest value of x for which feasible(x) is true", where feasibility is monotone in x (eating speed, ship capacity, the largest minimum distance). That is binary search on the answer.

**The idea and its invariant.** Keep the answer inside `[lo, hi]` and halve the range each step. Memorize one template — the lower bound: the first index whose value is at least the target, with `hi = len(nums)` so "not found" is representable — and derive the rest from it. For rotated arrays, one half around `mid` is always sorted; check whether the target lies in that half. For "minimum feasible", test `feasible(mid)`; if true, the answer is at most `mid` (`hi = mid`), otherwise it is above (`lo = mid + 1`).

```python
def lower_bound(nums, target):
    """First index whose value is >= target (len(nums) if none). The one template to memorize."""
    lo, hi = 0, len(nums)              # answer is in [lo, hi]
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def order_agnostic_search(nums, target):
    """Index of target in an array sorted ascending or descending, or -1."""
    lo, hi = 0, len(nums) - 1
    ascending = len(nums) < 2 or nums[0] <= nums[-1]
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if (nums[mid] < target) == ascending:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def ceiling_index(nums, target):
    """Index of the smallest value >= target in ascending nums, or -1."""
    i = lower_bound(nums, target)
    return i if i < len(nums) else -1


def next_greatest_letter(letters, target):
    """Smallest letter strictly greater than target, wrapping around (LC 744)."""
    lo, hi = 0, len(letters)
    while lo < hi:
        mid = (lo + hi) // 2
        if letters[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return letters[lo % len(letters)]


def search_range(nums, target):
    """First and last index of target in sorted integers (LC 34): two lower bounds."""
    first = lower_bound(nums, target)
    if first == len(nums) or nums[first] != target:
        return [-1, -1]
    return [first, lower_bound(nums, target + 1) - 1]


def search_rotated(nums, target):
    """Rotated sorted array of distinct values (LC 33): one half around mid is always sorted."""
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:                       # left half sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:                                           # right half sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


def find_min_rotated(nums):
    """Minimum of a rotated sorted array of distinct values (LC 153)."""
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1                                # the drop is right of mid
        else:
            hi = mid
    return nums[lo]


def peak_index_in_mountain(arr):
    """Index of the peak of a strictly increasing-then-decreasing array (LC 852)."""
    lo, hi = 0, len(arr) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < arr[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo


def min_eating_speed(piles, h):
    """Binary search on the answer (LC 875): the smallest speed that finishes within h hours."""
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((p + mid - 1) // mid for p in piles) <= h:   # feasible: try slower
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**Complexity.** O(log n) for searches; O(n log V) for binary search on an answer of size V with an O(n) feasibility check.

**Practice set.** 704 Binary Search; 35 Search Insert Position; 744 Find Smallest Letter Greater Than Target; 34 Find First and Last Position of Element in Sorted Array; 702 Search in a Sorted Array of Unknown Size† (double the bound until it passes the target); 658 Find K Closest Elements; 852 Peak Index in a Mountain Array; 1095 Find in Mountain Array; 33 Search in Rotated Sorted Array; 81 Search in Rotated Sorted Array II; 153 Find Minimum in Rotated Sorted Array; 162 Find Peak Element; 74 Search a 2D Matrix; 875 Koko Eating Bananas; 1011 Capacity To Ship Packages Within D Days; 410 Split Array Largest Sum.

**Pitfalls.** Mixing loop conditions and updates (`while lo <= hi` with `hi = mid` loops forever); rounding `mid` down when the update is `lo = mid` (once `hi = lo + 1`, `mid` equals `lo` and the loop never ends — round up with `(lo + hi + 1) // 2` in upper-bound variants); in other languages, `(lo + hi) / 2` overflowing 32-bit integers (write `lo + (hi − lo) / 2`; Python integers do not overflow, but say you know); with duplicates in rotated arrays, the sorted-half test fails when the ends equal the middle — shrink by one (both ends in 81 when `nums[lo] == nums[mid] == nums[hi]`; `hi -= 1` in 154 when `nums[mid] == nums[hi]`), which makes the worst case O(n).

**Follow-ups.** "Floating-point answer" (a square root to 10⁻⁶): iterate a fixed number of times. "Search in a matrix sorted by rows and columns" (240): start at the top-right corner and walk, O(rows + cols). "Why is binary search on the answer correct?": state the monotonicity of feasibility in one sentence.

## 39d.15 Pattern 13 — Top K elements

**Recognize it.** "The k largest", "the k most frequent", "the k closest", "the kth smallest", "keep the top k of a stream", and scheduling problems that repeatedly take the most frequent remaining item.

**The idea and its invariant.** To keep the k largest, use a min-heap of size k: its top is the smallest of the current top k, so any new value larger than the top replaces it. That costs O(n log k) instead of sorting's O(n log n), and it works on streams. When frequencies are bounded by n, bucket sort by frequency is O(n). Quickselect gives O(n) average for a single kth element but O(n²) worst case; mention it as the alternative and its trade-off.

```python
def kth_largest(nums, k):
    """Kth largest value (LC 215): a min-heap of the k largest seen, O(n log k)."""
    heap = nums[:k]
    heapq.heapify(heap)
    for x in nums[k:]:
        if x > heap[0]:
            heapq.heapreplace(heap, x)
    return heap[0]


def top_k_frequent(nums, k):
    """The k most frequent values (LC 347): bucket by frequency, O(n)."""
    buckets = [[] for _ in range(len(nums) + 1)]
    for value, freq in Counter(nums).items():
        buckets[freq].append(value)
    out = []
    for freq in range(len(buckets) - 1, 0, -1):
        for value in buckets[freq]:
            out.append(value)
            if len(out) == k:
                return out
    return out


class KthLargest:
    """Kth largest in a stream (LC 703): keep exactly the k largest in a min-heap."""

    def __init__(self, k, nums):
        self.k = k
        self.heap = []
        for x in nums:
            self.add(x)

    def add(self, val):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, val)
        elif val > self.heap[0]:
            heapq.heapreplace(self.heap, val)
        return self.heap[0]


def k_closest_points(points, k):
    """The k points closest to the origin (LC 973); nsmallest keeps a heap of size k."""
    return heapq.nsmallest(k, points, key=lambda p: p[0] * p[0] + p[1] * p[1])


def reorganize_string(s):
    """Rearrange so no two neighbors are equal, or return "" (LC 767): greedy with a max-heap."""
    heap = [(-count, ch) for ch, count in Counter(s).items()]
    heapq.heapify(heap)
    out, held = [], None              # held: the last character used, kept out for one turn
    while heap:
        count, ch = heapq.heappop(heap)
        out.append(ch)
        if held:
            heapq.heappush(heap, held)
        held = (count + 1, ch) if count + 1 < 0 else None
    return "".join(out) if len(out) == len(s) else ""
```

**Complexity.** O(n log k) time and O(k) space with the heap; O(n) with buckets; reorganize string O(n log a) for an alphabet of size a.

**Practice set.** 215 Kth Largest Element in an Array; 347 Top K Frequent Elements; 703 Kth Largest Element in a Stream; 973 K Closest Points to Origin; 451 Sort Characters By Frequency; 692 Top K Frequent Words; 767 Reorganize String; 621 Task Scheduler; 358 Rearrange String k Distance Apart†; 1167 Minimum Cost to Connect Sticks†; 895 Maximum Frequency Stack; 1481 Least Number of Unique Integers after K Removals.

**Pitfalls.** A max-heap of all n values for "top k" (O(n + k log n) — fine, but the size-k min-heap is the expected answer for streams); tuples that compare unorderable objects on ties (add an index as the second element); 692 requires ties broken alphabetically, which interacts with the heap order — sort by (−count, word).

**Follow-ups.** "The data does not fit in one machine": for the k largest values, take the top k of each shard and merge — the global top k lies in the union of the local lists. For the k most frequent, that union can miss the answer (a value seen 3 times on each of ten shards totals 30, yet loses every shard to a different value seen 4 times there), so first partition by value so that each count lives on one shard, then take local top k and merge. "Approximate frequencies on a stream with bounded memory": Count–Min sketch plus a heap (heavy hitters). "Kth largest in O(n) worst case": median of medians.

## 39d.16 Pattern 14 — Bitwise XOR

**Recognize it.** Every value appears an even number of times except one or two; a value must be found without extra memory; bits must be flipped or counted.

**The idea and its invariant.** XOR is associative and commutative, x ^ x = 0 and x ^ 0 = x, so XOR-ing a whole list cancels every pair and leaves the odd one out. With two unique values a and b, the total is a ^ b ≠ 0; any set bit of it (the lowest is `x & -x`) differs between a and b, so splitting the list by that bit separates them, and each half reduces to the one-unique case. The companion trick is `x & (x − 1)`, which clears the lowest set bit: repeat it to count bits, and `x & (x − 1) == 0` tests a positive x for being a power of two.

```python
def single_number(nums):
    """Every value appears twice except one (LC 136): x ^ x == 0 and XOR is order-free."""
    acc = 0
    for value in nums:
        acc ^= value
    return acc


def single_number_iii(nums):
    """Two values appear once, the rest twice (LC 260): split on one set bit of a ^ b."""
    both = 0
    for value in nums:
        both ^= value
    bit = both & -both                    # lowest set bit: a and b differ there
    a = b = 0
    for value in nums:
        if value & bit:
            a ^= value
        else:
            b ^= value
    return sorted([a, b])


def bitwise_complement(n):
    """Flip every bit of n's binary form (LC 1009); the complement of 0 is 1."""
    if n == 0:
        return 1
    return n ^ ((1 << n.bit_length()) - 1)


def missing_number_xor(nums):
    """LC 268 again, read-only: XOR every index and value; pairs cancel."""
    acc = len(nums)
    for i, value in enumerate(nums):
        acc ^= i ^ value
    return acc
```

**Complexity.** O(n) time, O(1) space.

**Practice set.** 136 Single Number; 260 Single Number III; 137 Single Number II (count bits modulo 3); 1009 Complement of Base 10 Integer (476 Number Complement is the same problem without n = 0); 832 Flipping an Image; 268 Missing Number; 191 Number of 1 Bits; 338 Counting Bits; 190 Reverse Bits; 371 Sum of Two Integers.

**Pitfalls.** Python integers are unbounded: `~x` is −x − 1, not a 32-bit complement, so mask explicitly (`x ^ ((1 << bits) − 1)`), and 190 and 371 need a 32-bit mask to emulate fixed-width arithmetic; precedence that differs from C and Java — in Python `&`, `|` and `^` bind tighter than comparisons, so `x & 1 == 0` means `(x & 1) == 0`, but shifts bind looser than arithmetic, so `1 << n - 1` means `1 << (n - 1)`; parenthesize anyway.

**Follow-ups.** "Every value appears three times except one" (137): count each bit position modulo 3. "Find the missing and the repeated value" (645): XOR splits them as in 260. "Subsets as bitmasks": iterate `mask` from 0 to 2ⁿ − 1 and test bit i with `mask >> i & 1`.

## 39d.17 Pattern 15 — Backtracking

**Recognize it.** "Find all valid …" or "is there any …" over a combinatorial space with constraints: puzzles (Sudoku, N-Queens), words in a grid, combinations that sum to a target, factorizations, partitions of a string, IP addresses.

**The idea and its invariant.** Depth-first search over partial solutions: choose an option, recurse, then undo the choice so the shared state is exactly as it was. The state on the way down is always a valid partial solution; anything that cannot be completed is pruned as early as possible. Most of the speed comes from pruning — sorted candidates that let you `break`, constraint sets that make the validity check O(1), and choosing the most constrained position first. The Sudoku template branches on the empty cell with the fewest options. Each step costs more than taking cells in order, so on some puzzles plain order wins, but on the two test puzzles built to defeat cell-by-cell order, cell-by-cell search took about 10 and 50 seconds in CPython and this template about a third of a second each.

```python
def generate_parentheses(n):
    """All balanced strings of n pairs (LC 22): add "(" while any remain, ")" while it stays valid."""
    out = []

    def build(prefix, opened, closed):
        if len(prefix) == 2 * n:
            out.append(prefix)
            return
        if opened < n:
            build(prefix + "(", opened + 1, closed)
        if closed < opened:
            build(prefix + ")", opened, closed + 1)

    build("", 0, 0)
    return out


def combination_sum(candidates, target):
    """Combinations of distinct candidates, each reusable, that sum to target (LC 39)."""
    candidates = sorted(candidates)
    out, path = [], []

    def dfs(start, remaining):
        if remaining == 0:
            out.append(path[:])
            return
        for i in range(start, len(candidates)):
            c = candidates[i]
            if c > remaining:
                break                     # sorted, so no later candidate fits either
            path.append(c)
            dfs(i, remaining - c)         # i, not i + 1: the same candidate may repeat
            path.pop()

    dfs(0, target)
    return out


def factor_combinations(n):
    """Factorizations of n into factors >= 2, non-decreasing, excluding [n] itself (LC 254)."""
    out = []

    def dfs(remaining, smallest, path):
        f = smallest
        while f * f <= remaining:
            if remaining % f == 0:
                out.append(path + [f, remaining // f])
                dfs(remaining // f, f, path + [f])
            f += 1

    dfs(n, 2, [])
    return out


def word_exists(board, word):
    """Word Search (LC 79): DFS that marks a cell while it is on the path and restores it after."""
    rows, cols = len(board), len(board[0])

    def dfs(r, c, i):
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        saved, board[r][c] = board[r][c], "#"
        found = any(dfs(r + dr, c + dc, i + 1) for dr, dc in DIRS4)
        board[r][c] = saved
        return found

    return any(dfs(r, c, 0) for r in range(rows) for c in range(cols))


def total_n_queens(n):
    """Number of N-Queens solutions (LC 52): one queen per row; sets for columns and diagonals."""
    cols, diag, anti = set(), set(), set()

    def place(r):
        if r == n:
            return 1
        count = 0
        for c in range(n):
            if c in cols or r - c in diag or r + c in anti:
                continue
            cols.add(c)
            diag.add(r - c)
            anti.add(r + c)
            count += place(r + 1)
            cols.remove(c)
            diag.remove(r - c)
            anti.remove(r + c)
        return count

    return place(0)


def solve_sudoku(board):
    """Fill the "." cells in place (LC 37), always branching on the empty cell with the fewest options."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empty = []
    for r in range(9):
        for c in range(9):
            value = board[r][c]
            if value == ".":
                empty.append((r, c))
            else:
                rows[r].add(value)
                cols[c].add(value)
                boxes[r // 3 * 3 + c // 3].add(value)

    def options(r, c):
        used = rows[r] | cols[c] | boxes[r // 3 * 3 + c // 3]
        return [d for d in "123456789" if d not in used]

    def fill():
        if not empty:
            return True
        best_i, best = 0, None
        for i, (r, c) in enumerate(empty):        # most constrained cell; a forced one ends the scan
            opts = options(r, c)
            if best is None or len(opts) < len(best):
                best_i, best = i, opts
                if len(opts) <= 1:
                    break
        r, c = empty[best_i]
        empty[best_i] = empty[-1]                 # O(1) removal: the order of empty does not matter
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
```

**Complexity.** Exponential in the worst case; state the bound you can defend (N-Queens is below n!; word search is O(rows · cols · 3^L) for a word of length L, since after the first step at most three neighbors are unvisited; combination sum is bounded by the number of multisets of candidates up to the target) and say what pruning buys in practice.

**Practice set.** 22 Generate Parentheses; 39 Combination Sum; 40 Combination Sum II; 216 Combination Sum III; 77 Combinations; 17 Letter Combinations of a Phone Number; 79 Word Search; 212 Word Search II (with a trie, 39d.23); 131 Palindrome Partitioning; 93 Restore IP Addresses; 254 Factor Combinations†; 51 N-Queens; 52 N-Queens II; 37 Sudoku Solver.

**Pitfalls.** Forgetting to undo (the next branch starts from a corrupted state); recording the shared `path` instead of a copy; generating duplicate combinations because the loop starts at 0 instead of the current index; recursing with `i + 1` when reuse is allowed (39) or `i` when it is not (40).

**Follow-ups.** "Count solutions instead of listing them": return counts and add memoization if subproblems repeat — at which point it has become dynamic programming. "Find one solution fast": order choices well and stop at the first success, as `solve_sudoku` does. "Explain the difference from subsets (39d.13)": subsets build every option breadth-first; backtracking walks one branch at a time and prunes, which is what makes constrained search feasible.

## 39d.18 Pattern 16 — 0/1 knapsack (dynamic programming)

**Recognize it.** Each item can be taken at most once, there is a capacity or a target sum, and you want the best value, a yes/no, or the number of ways: subset sum, equal-sum partition, target sum with plus and minus signs, the last stone weight, the fewest elements reaching a target. If items can be reused, it is the unbounded variant (coin change).

**The idea and its invariant.** Let `best[c]` be the best value achievable with capacity c using the items considered so far. Adding item (w, v) gives `best[c] = max(best[c], best[c − w] + v)`. Iterate capacities from high to low so that `best[c − w]` still describes the state *before* this item — that is what limits each item to one use. Iterating low to high instead lets the item be reused, which turns the same loop into the unbounded knapsack. Many problems reduce to subset sum after a short algebra step: in 494, the plus-set P and minus-set N satisfy P − N = target and P + N = total, so you need subsets summing to (total + target) / 2.

```python
def knapsack_01(weights, values, capacity):
    """Best value with each item used at most once: one row of the table, filled right to left."""
    best = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):         # right to left: item counted once
            best[c] = max(best[c], best[c - w] + v)
    return best[capacity]


def can_partition(nums):
    """Equal Subset Sum Partition (LC 416): can a subset reach half the total?"""
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    reachable = [True] + [False] * target
    for x in nums:
        for s in range(target, x - 1, -1):
            reachable[s] = reachable[s] or reachable[s - x]
    return reachable[target]


def count_subsets_with_sum(nums, target):
    """Number of subsets (by position) with the given sum; non-negative values."""
    ways = [1] + [0] * target
    for x in nums:
        for s in range(target, x - 1, -1):           # x == 0 doubles every count, as it should
            ways[s] += ways[s - x]
    return ways[target]


def find_target_sum_ways(nums, target):
    """Ways to put + or - before each value to reach target (LC 494): P - N = target, P + N = total."""
    total = sum(nums)
    if abs(target) > total or (total + target) % 2:
        return 0
    return count_subsets_with_sum(nums, (total + target) // 2)


def min_subset_sum_difference(nums):
    """Split non-negative values into two subsets with the smallest difference of sums."""
    total = sum(nums)
    half = total // 2
    reachable = [True] + [False] * half
    for x in nums:
        for s in range(half, x - 1, -1):
            reachable[s] = reachable[s] or reachable[s - x]
    best = max(s for s in range(half + 1) if reachable[s])
    return total - 2 * best


def coin_change(coins, amount):
    """Fewest coins (LC 322) — the unbounded contrast: left to right lets a coin repeat."""
    impossible = amount + 1
    fewest = [0] + [impossible] * amount
    for coin in coins:
        for a in range(coin, amount + 1):
            fewest[a] = min(fewest[a], fewest[a - coin] + 1)
    return fewest[amount] if fewest[amount] != impossible else -1
```

**Complexity.** O(n · C) time and O(C) space for capacity or target C. This is pseudo-polynomial — polynomial in the value C, exponential in its number of digits — so it is fine while n · C stays near 10⁷ in Python and hopeless for C = 10⁹ (then meet in the middle over 2^(n/2) subsets, as in 2035, or a different idea).

**Practice set.** 416 Partition Equal Subset Sum; 494 Target Sum; 1049 Last Stone Weight II; 474 Ones and Zeroes (two capacities); 322 Coin Change and 518 Coin Change II (unbounded); 377 Combination Sum IV (order matters: loop over amounts outside, coins inside); 2035 Partition Array Into Two Arrays to Minimize Sum Difference (negative values: meet in the middle).

**Pitfalls.** Iterating capacities upward in the 0/1 version (silently allows reuse); forgetting that zeros double the count of ways (the template handles it because its loop reaches index 0); applying the subset-sum reduction when values can be negative (the table index goes negative — offset it or use a dictionary).

**Follow-ups.** "Reconstruct the chosen items": keep the full two-dimensional table, or a parent pointer per capacity per item, and walk back. "Return the count modulo 10⁹ + 7": reduce in the inner loop. "Explain the space optimization": the two-dimensional table only ever reads the previous row, so one row updated right to left suffices. "Make 416 faster in Python": treat an integer as the reachable-sums row — `bits |= bits << x` for each value, then test bit `target` — the same recurrence, a machine word at a time.

## 39d.19 Pattern 17 — Topological sort (graph)

**Recognize it.** Tasks with prerequisites, build orders, course schedules, compile dependencies, the order of letters in an alien alphabet, "is it possible to finish?", "give one valid order", "give all valid orders".

**The idea and its invariant.** In a directed acyclic graph, some node has no incoming edges — a source. Kahn's algorithm repeatedly removes a source and decrements the in-degree of its neighbors; any neighbor reaching zero becomes a source. The output order respects every edge because a node is emitted only after all its predecessors. If nodes remain when the queue empties, they lie on a cycle and no order exists. All orders come from backtracking over the current sources. The leaf-peeling variant (310) applies the same idea to an undirected tree to find its center.

```python
def topological_order(n, edges):
    """Kahn's algorithm over nodes 0..n-1; edges are (before, after). None if there is a cycle."""
    graph = [[] for _ in range(n)]
    indegree = [0] * n
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    queue = deque(i for i in range(n) if indegree[i] == 0)
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return order if len(order) == n else None


def can_finish(num_courses, prerequisites):
    """Course Schedule (LC 207): pairs are [course, prerequisite]."""
    return topological_order(num_courses, [(p, c) for c, p in prerequisites]) is not None


def find_order(num_courses, prerequisites):
    """Course Schedule II (LC 210): one valid order, or [] if impossible."""
    order = topological_order(num_courses, [(p, c) for c, p in prerequisites])
    return order if order is not None else []


def all_topological_orders(n, edges):
    """Every valid order (all task-scheduling orders): backtrack over the current sources."""
    graph = [[] for _ in range(n)]
    indegree = [0] * n
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    used = [False] * n
    out, order = [], []

    def backtrack():
        if len(order) == n:
            out.append(order[:])
            return
        for u in range(n):
            if not used[u] and indegree[u] == 0:
                used[u] = True
                order.append(u)
                for v in graph[u]:
                    indegree[v] -= 1
                backtrack()
                for v in graph[u]:
                    indegree[v] += 1
                order.pop()
                used[u] = False

    backtrack()
    return out


def alien_order(words):
    """Letter order from a sorted alien dictionary (LC 269); "" if the input is inconsistent."""
    letters = {ch for word in words for ch in word}
    graph = {ch: set() for ch in letters}
    indegree = {ch: 0 for ch in letters}
    for w1, w2 in zip(words, words[1:]):
        for a, b in zip(w1, w2):
            if a != b:                    # only the first difference tells us anything
                if b not in graph[a]:
                    graph[a].add(b)
                    indegree[b] += 1
                break
        else:
            if len(w1) > len(w2):          # "abc" before "ab" cannot be sorted
                return ""
    queue = deque(sorted(ch for ch in letters if indegree[ch] == 0))
    out = []
    while queue:
        ch = queue.popleft()
        out.append(ch)
        for nxt in sorted(graph[ch]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return "".join(out) if len(out) == len(letters) else ""


def find_min_height_trees(n, edges):
    """Roots of minimum-height trees (LC 310): peel leaves layer by layer until one or two remain."""
    if n <= 2:
        return list(range(n))
    graph = [set() for _ in range(n)]
    for u, v in edges:
        graph[u].add(v)
        graph[v].add(u)
    leaves = [i for i in range(n) if len(graph[i]) == 1]
    remaining = n
    while remaining > 2:
        remaining -= len(leaves)
        next_leaves = []
        for leaf in leaves:
            neighbor = graph[leaf].pop()
            graph[neighbor].remove(leaf)
            if len(graph[neighbor]) == 1:
                next_leaves.append(neighbor)
        leaves = next_leaves
    return sorted(leaves)
```

**Complexity.** O(V + E) time and space; all orders is exponential in the worst case (a graph with no edges has V! orders).

**Practice set.** 207 Course Schedule; 210 Course Schedule II; 269 Alien Dictionary†; 444 Sequence Reconstruction† (a unique order exists only if the queue never holds more than one source); 310 Minimum Height Trees; 802 Find Eventual Safe States; 2115 Find All Possible Recipes from Given Supplies; 1203 Sort Items by Groups Respecting Dependencies; 329 Longest Increasing Path in a Matrix (DFS with memo, or topological order on the grid).

**Pitfalls.** Edge direction — 207 lists pairs as [course, prerequisite], so the edge is prerequisite → course; in the alien dictionary, using all character pairs instead of only the first difference, and missing the invalid case where a word precedes its own prefix; DFS-based topological sort without a three-color visited state cannot detect cycles.

**Follow-ups.** "Unique order?": the queue must hold exactly one node at every step. "Lexicographically smallest order": replace the queue with a min-heap. "Parallel scheduling — minimum number of semesters" (1136 Parallel Courses†): process the queue level by level and count levels.

## 39d.20 Pattern 18 — K-way merge

**Recognize it.** k sorted lists, arrays, files or matrix rows; merge them, or find the kth smallest across them, or the smallest range that touches each one.

**The idea and its invariant.** A min-heap holds the current head of each list. Popping gives the global minimum among all remaining elements, because each list's unseen elements are no smaller than its head. Push the popped element's successor and continue. Store (value, list index, position) tuples so that ties never fall through to comparing nodes, which Python cannot order. For the smallest range, also track the maximum among the heads: the heap's minimum and that maximum bound a range that touches every list, and you can only improve it by advancing the list that holds the minimum.

```python
def merge_k_lists(lists):
    """Merge k sorted linked lists (LC 23). The list index breaks ties so nodes are never compared."""
    heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
    heapq.heapify(heap)
    dummy = tail = ListNode()
    while heap:
        _, i, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next


def kth_smallest_in_sorted_lists(lists, k):
    """Kth smallest across sorted lists: pop k - 1 times from a heap holding one head per list."""
    heap = [(lst[0], r, 0) for r, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    for _ in range(k - 1):
        _, r, c = heapq.heappop(heap)
        if c + 1 < len(lists[r]):
            heapq.heappush(heap, (lists[r][c + 1], r, c + 1))
    return heap[0][0]


def kth_smallest_in_matrix(matrix, k):
    """Rows and columns sorted (LC 378): K-way merge over the rows."""
    return kth_smallest_in_sorted_lists(matrix, k)


def smallest_range(lists):
    """Smallest range holding at least one value from each list (LC 632)."""
    heap = [(lst[0], r, 0) for r, lst in enumerate(lists)]
    heapq.heapify(heap)
    current_max = max(lst[0] for lst in lists)
    best = [heap[0][0], current_max]
    while True:
        low, r, c = heapq.heappop(heap)
        if current_max - low < best[1] - best[0]:
            best = [low, current_max]
        if c + 1 == len(lists[r]):              # one list is exhausted: no full range is left
            return best
        nxt = lists[r][c + 1]
        current_max = max(current_max, nxt)
        heapq.heappush(heap, (nxt, r, c + 1))
```

**Complexity.** O(N log k) for N total elements across k lists; O(k) heap space. Kth smallest is O(k + K log k) for the Kth element.

**Practice set.** 21 Merge Two Sorted Lists; 88 Merge Sorted Array (fill from the back); 23 Merge k Sorted Lists; 378 Kth Smallest Element in a Sorted Matrix; 373 Find K Pairs with Smallest Sums; 632 Smallest Range Covering Elements from K Lists; 264 Ugly Number II; 4 Median of Two Sorted Arrays (binary search, but often asked here).

**Pitfalls.** Pushing every element at once (O(N log N) and O(N) memory, losing the point); comparing nodes on ties; forgetting empty lists when building the heap.

**Follow-ups.** "Lists live on disk and do not fit in memory": the same algorithm is an external merge sort, with one buffered reader per file. "Divide and conquer instead of a heap": merge pairs of lists in rounds, also O(N log k). "378 without a heap": binary search on the value range, counting elements ≤ mid in O(n) per step.

## 39d.21 Pattern 19 — Monotonic stack

**Recognize it.** For each element, find the next (or previous) greater or smaller element; spans ("how many consecutive days was the price at most today's"); areas bounded by the nearest lower bar; removing digits to make the smallest number; sums over all subarrays of their minimum.

**The idea and its invariant.** Keep a stack of indices still waiting for their answer, with values in monotone order. When a new element arrives, it is the answer for every waiting index it beats: pop them and record. Each index is pushed and popped once, so the whole pass is O(n) even though there is a loop inside the loop. For histograms, when a bar is popped, the current index is its right boundary and the new stack top is its left boundary, so its maximal rectangle is known at that moment; a sentinel bar of height zero at the end flushes the stack. The deque version (sliding window maximum) adds removal from the front when indices fall out of the window.

```python
def next_greater_elements(nums):
    """For each index, the next value to the right that is greater, else -1."""
    out = [-1] * len(nums)
    stack = []                          # indices still waiting; their values are non-increasing
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            out[stack.pop()] = x
        stack.append(i)
    return out


def next_greater_element_i(nums1, nums2):
    """LC 496: next greater value in nums2 for each value of nums1 (distinct values)."""
    nge = dict(zip(nums2, next_greater_elements(nums2)))
    return [nge[x] for x in nums1]


def next_greater_circular(nums):
    """LC 503: the array wraps around, so walk it twice and push indices only on the first pass."""
    n = len(nums)
    out = [-1] * n
    stack = []
    for i in range(2 * n):
        x = nums[i % n]
        while stack and nums[stack[-1]] < x:
            out[stack.pop()] = x
        if i < n:
            stack.append(i)
    return out


def next_smaller_elements(nums):
    """For each index, the next value to the right that is smaller, else -1."""
    out = [-1] * len(nums)
    stack = []
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] > x:
            out[stack.pop()] = x
        stack.append(i)
    return out


def daily_temperatures(temps):
    """Days until a warmer day (LC 739)."""
    out = [0] * len(temps)
    stack = []
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            out[j] = i - j
        stack.append(i)
    return out


def largest_rectangle_area(heights):
    """Largest rectangle in a histogram (LC 84). A trailing 0 flushes the stack at the end."""
    bars = heights + [0]
    stack = []                          # indices with increasing heights
    best = 0
    for i, h in enumerate(bars):
        while stack and bars[stack[-1]] >= h:
            height = bars[stack.pop()]
            left = stack[-1] + 1 if stack else 0        # first bar the rectangle can start at
            best = max(best, height * (i - left))
        stack.append(i)
    return best


def trap(height):
    """Trapping Rain Water (LC 42) with a stack: fill each basin as its right wall arrives."""
    water = 0
    stack = []
    for i, h in enumerate(height):
        while stack and height[stack[-1]] < h:
            bottom = stack.pop()
            if not stack:
                break
            left = stack[-1]
            water += (i - left - 1) * (min(height[left], h) - height[bottom])
        stack.append(i)
    return water


def max_sliding_window(nums, k):
    """Sliding Window Maximum (LC 239): a monotonic deque whose front is the window's maximum."""
    window = deque()                    # indices; values decreasing from front to back
    out = []
    for i, x in enumerate(nums):
        while window and nums[window[-1]] <= x:
            window.pop()
        window.append(i)
        if window[0] <= i - k:          # front fell out of the window
            window.popleft()
        if i >= k - 1:
            out.append(nums[window[0]])
    return out
```

**Complexity.** O(n) time, O(n) space.

**Practice set.** 496 Next Greater Element I; 503 Next Greater Element II; 739 Daily Temperatures; 1475 Final Prices With a Special Discount in a Shop (next smaller-or-equal); 901 Online Stock Span; 84 Largest Rectangle in Histogram; 85 Maximal Rectangle (a histogram per row); 42 Trapping Rain Water; 402 Remove K Digits; 316 Remove Duplicate Letters; 907 Sum of Subarray Minimums; 962 Maximum Width Ramp; 239 Sliding Window Maximum.

**Pitfalls.** Storing values instead of indices (you lose the distance and the boundaries); strict versus non-strict comparison — it decides how equal values are handled, and in counting problems like 907 one side must be strict and the other not, or equal minimums are counted twice; forgetting the final flush of indices that never found an answer.

**Follow-ups.** "Previous greater instead of next": scan from the right, or read the stack top when pushing. "Circular array": walk twice, as `next_greater_circular` does. "Online, one value at a time" (901): the stack holds (price, span) pairs and merges spans as it pops.

## 39d.22 Pattern 20 — Multi-threaded

**Recognize it.** The problem statement mentions threads, concurrent calls, ordering guarantees between functions called from different threads, producers and consumers, rate limits, or crawling with workers. Grokking's version also re-solves familiar tree problems (invert a tree, iterate a BST, compare two trees) with threads, to test whether you can find independent sub-tasks and combine their results safely. LeetCode has a concurrency category (1114 onward).

**The idea and its invariant.** Three rules cover most interview problems. First, split work so threads never write the same data — the two subtrees of a node are disjoint, so inverting them concurrently needs no lock. Second, when threads must coordinate, use a primitive whose meaning matches the requirement: an event for "wait until X has happened", a condition variable (always waited on inside a `while` loop, because wakeups can be spurious or stolen) for "wait until the state allows me to proceed", a semaphore for "at most n at a time", a barrier for "everyone reaches this point". Third, keep shared state owned by one thread when you can: in the crawler below, workers only fetch, and the main thread alone updates `seen`, so no lock is needed.

```python
def invert_tree(root):
    """Invert a binary tree (LC 226), sequentially."""
    if root:
        root.left, root.right = invert_tree(root.right), invert_tree(root.left)
    return root


def invert_tree_parallel(root, workers=2):
    """The multi-threaded variant: the two subtrees are disjoint, so they can be inverted concurrently.

    On CPython's default build the GIL allows no speedup for pure-Python CPU work; the interview point
    is to find independent sub-tasks, avoid shared mutable state, and join the results correctly.
    """
    if root is None:
        return None
    with ThreadPoolExecutor(max_workers=workers) as pool:
        left_future = pool.submit(invert_tree, root.left)
        right_future = pool.submit(invert_tree, root.right)
        root.left, root.right = right_future.result(), left_future.result()
    return root


class PrintInOrder:
    """Print in Order (LC 1114): first, second and third run in order whatever the thread schedule."""

    def __init__(self):
        self._first_done = threading.Event()
        self._second_done = threading.Event()

    def first(self, print_first):
        print_first()
        self._first_done.set()

    def second(self, print_second):
        self._first_done.wait()
        print_second()
        self._second_done.set()

    def third(self, print_third):
        self._second_done.wait()
        print_third()


class BoundedBlockingQueue:
    """Bounded Blocking Queue (LC 1188): one lock, two conditions, waits always in a while loop."""

    def __init__(self, capacity):
        self._items = deque()
        self._capacity = capacity
        lock = threading.Lock()
        self._not_full = threading.Condition(lock)
        self._not_empty = threading.Condition(lock)

    def enqueue(self, element):
        with self._not_full:
            while len(self._items) >= self._capacity:
                self._not_full.wait()
            self._items.append(element)
            self._not_empty.notify()

    def dequeue(self):
        with self._not_empty:
            while not self._items:
                self._not_empty.wait()
            item = self._items.popleft()
            self._not_full.notify()
            return item

    def size(self):
        with self._not_full:
            return len(self._items)


def crawl(start_url, get_urls, workers=8):
    """Web Crawler Multithreaded (LC 1242 style): same host only, each URL fetched once.

    Level-synchronous: worker threads only fetch; the main thread owns `seen`, so no lock is needed.
    """
    host = urlsplit(start_url).hostname
    seen = {start_url}
    frontier = [start_url]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while frontier:
            next_frontier = []
            for urls in pool.map(get_urls, frontier):
                for url in urls:
                    if urlsplit(url).hostname == host and url not in seen:
                        seen.add(url)
                        next_frontier.append(url)
            frontier = next_frontier
    return sorted(seen)
```

**Complexity and the GIL.** In CPython's default build, the global interpreter lock lets only one thread run Python bytecode at a time, so threads speed up I/O-bound work (crawling, API calls) but not CPU-bound work like inverting a tree. For CPU-bound parallelism use processes (`ProcessPoolExecutor`), since Python 3.14 an `InterpreterPoolExecutor` (one interpreter, with its own GIL, per worker), or the free-threaded build from PEP 703 — experimental in 3.13 and officially supported since 3.14 (PEP 779), but still a separate, optional build rather than the default. Say this before the interviewer asks; then explain that the exercise is about structure and correctness.

**Practice set.** 1114 Print in Order; 1115 Print FooBar Alternately; 1116 Print Zero Even Odd; 1117 Building H2O; 1195 Fizz Buzz Multithreaded; 1226 The Dining Philosophers; 1188 Design Bounded Blocking Queue†; 1242 Web Crawler Multithreaded†; and with threads as in Grokking: 226 Invert Binary Tree, 173 Binary Search Tree Iterator, 100 Same Tree.

**Pitfalls.** `if` instead of `while` around a condition wait; notifying without holding the lock; deadlock from acquiring two locks in different orders (the dining philosophers: order the forks or limit diners with a semaphore); unbounded thread creation per task instead of a pool; check-then-act races on shared sets (two workers both see a URL as new).

**Follow-ups.** "Make the crawler continuous instead of level by level": a work queue plus a pending counter, and a lock around `seen` (or a single coordinator thread). "Rate-limit the crawler": a token bucket shared by workers. "Same in asyncio": tasks and an `asyncio.Semaphore`; one event loop, cooperative scheduling, no GIL contention for I/O.

## 39d.23 Beyond the twenty: the patterns the list leaves out

The twenty are a strong core, but four families come up at least as often as bitwise XOR or the multi-threaded set: hash maps with prefix sums, graph algorithms beyond topological sort, tries, and the rest of dynamic programming, plus greedy choices and the design classics. Each gets the short treatment.

**Prefix sums with a hash map.** When a sliding window fails because values can be negative, count subarrays through running sums: a subarray ending at i sums to k exactly when an earlier running sum equals `running − k`. Variants keep the earliest index of each sum (525 Contiguous Array, treating 0 as −1) or sums modulo k (523 Continuous Subarray Sum). Related hash-map staples: 1 Two Sum, 49 Group Anagrams, 128 Longest Consecutive Sequence (start counting only from values whose predecessor is absent), 238 Product of Array Except Self (prefix and suffix products).

```python
def subarray_sum_equals_k(nums, k):
    """Count subarrays summing to k (LC 560): prefix sums in a hash map; works with negatives."""
    seen = Counter({0: 1})
    running = count = 0
    for x in nums:
        running += x
        count += seen[running - k]
        seen[running] += 1
    return count
```

**Union-find (disjoint sets).** Connectivity that grows as edges arrive: number of components, the first edge that closes a cycle, merging accounts that share an email, islands added one cell at a time. With union by size and path compression (the template uses path halving, a one-pass variant with the same bound) each operation costs nearly constant amortized time (the inverse Ackermann function). Practice: 547 Number of Provinces, 684 Redundant Connection, 721 Accounts Merge, 990 Satisfiability of Equality Equations, 1202 Smallest String With Swaps, 305 Number of Islands II†.

```python
class UnionFind:
    """Disjoint sets with path halving and union by size: near-constant time per operation."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True


def find_redundant_connection(edges):
    """The edge that closes a cycle in a graph that was a tree (LC 684); nodes are 1..n."""
    uf = UnionFind(len(edges) + 1)
    for u, v in edges:
        if not uf.union(u, v):
            return [u, v]
    return []
```

**Graph traversal and shortest paths.** On adjacency lists, BFS or DFS with a visited set answers reachability, and a visited map from original to copy answers 133 Clone Graph (create the copy before visiting neighbors, or cycles recurse forever); coloring nodes alternately during BFS tests 785 Is Graph Bipartite?, and a disconnected graph needs a fresh search from every unvisited node. Unweighted graphs: BFS gives shortest paths in edges (127 Word Ladder, 752 Open the Lock, 1091 Shortest Path in Binary Matrix). Non-negative weights: Dijkstra with a heap of (distance, node), skipping entries for nodes already settled — O((V + E) log V). Practice: 743 Network Delay Time, 1631 Path With Minimum Effort, 1514 Path with Maximum Probability. With a limit on the number of edges (787 Cheapest Flights Within K Stops), use Bellman–Ford for k + 1 rounds or BFS by levels; negative weights rule Dijkstra out.

```python
def network_delay_time(times, n, k):
    """Dijkstra (LC 743): time for a signal from k to reach all nodes 1..n, or -1."""
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {}
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in dist:                       # stale entry: a shorter path already settled u
            continue
        dist[u] = d
        for v, w in graph[u]:
            if v not in dist:
                heapq.heappush(heap, (d + w, v))
    return max(dist.values()) if len(dist) == n else -1
```

**Tries.** Prefix questions over many words: autocomplete, "does any word start with", word search with a whole dictionary, replacing words by their shortest root. Each node is a dictionary of children plus an end marker; insert and lookup cost O(length of the word). Practice: 208 Implement Trie (Prefix Tree), 211 Design Add and Search Words Data Structure, 212 Word Search II, 648 Replace Words, 1268 Search Suggestions System.

```python
class Trie:
    """Prefix tree (LC 208) with dict children."""

    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def _walk(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and "$" in node

    def starts_with(self, prefix):
        return self._walk(prefix) is not None
```

**Greedy choices.** When a local choice can be proven never to hurt (an exchange argument: swapping the greedy choice into any optimal solution keeps it optimal), sort and sweep. Keeping the most non-overlapping intervals means always keeping the one that ends first. Practice: 435 Non-overlapping Intervals, 452 Minimum Number of Arrows to Burst Balloons, 55 Jump Game, 45 Jump Game II, 134 Gas Station, 763 Partition Labels, 406 Queue Reconstruction by Height. State the exchange argument; an unproven greedy is a classic wrong answer, and a small counterexample is how interviewers show it.

```python
def erase_overlap_intervals(intervals):
    """Fewest removals to leave non-overlapping intervals (LC 435): greedy, keep the earliest end."""
    removed = 0
    last_end = float("-inf")
    for start, end in sorted(intervals, key=lambda iv: iv[1]):
        if start >= last_end:
            last_end = end
        else:
            removed += 1
    return removed
```

**The other dynamic-programming families.** Knapsack (39d.18) is one of six shapes worth knowing by name. One-dimensional sequences: 70 Climbing Stairs, 198 House Robber, 213 House Robber II, 139 Word Break, 91 Decode Ways. Two-dimensional grids: 62 Unique Paths, 64 Minimum Path Sum, 221 Maximal Square. Two strings: 1143 Longest Common Subsequence, 72 Edit Distance, 115 Distinct Subsequences, 97 Interleaving String. Subsequences: 300 Longest Increasing Subsequence (O(n log n) with patience sorting, as below), 354 Russian Doll Envelopes. Intervals and states: 5 Longest Palindromic Substring, 516 Longest Palindromic Subsequence, 312 Burst Balloons, 121 and 309 (best time to buy and sell stock, with states for holding, not holding and cooldown). The method is the same each time: define the state in words ("the best result using the first i items with capacity c"), write the transition, fix the base cases, choose the iteration order so every dependency is computed first, then reduce space if only the previous row is used.

```python
def length_of_lis(nums):
    """Longest strictly increasing subsequence (LC 300): patience sorting, O(n log n)."""
    tails = []                          # tails[i]: smallest tail of an increasing run of length i + 1
    for x in nums:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)


def min_distance(word1, word2):
    """Edit distance (LC 72) with two rows of the table."""
    prev = list(range(len(word2) + 1))
    for i, a in enumerate(word1, 1):
        curr = [i] + [0] * len(word2)
        for j, b in enumerate(word2, 1):
            if a == b:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])   # delete, insert, replace
        prev = curr
    return prev[-1]


def rob(nums):
    """House Robber (LC 198): best with or without the previous house."""
    take = skip = 0
    for x in nums:
        take, skip = skip + x, max(take, skip)
    return max(take, skip)
```

**Design classics.** 146 LRU Cache (a hash map plus a doubly linked list; in Python, `OrderedDict` — say how you would build it without), 460 LFU Cache, 155 Min Stack, 380 Insert Delete GetRandom O(1), 981 Time Based Key-Value Store (binary search per key), 295 (two heaps). Also stacks for parsing: 20 Valid Parentheses, 150 Evaluate Reverse Polish Notation, 224 Basic Calculator. And matrix manipulation: 48 Rotate Image, 54 Spiral Matrix, 73 Set Matrix Zeroes.

```python
class LRUCache:
    """LRU Cache (LC 146) with OrderedDict; say how you would build it from a hash map plus a doubly linked list."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.items = OrderedDict()

    def get(self, key):
        if key not in self.items:
            return -1
        self.items.move_to_end(key)
        return self.items[key]

    def put(self, key, value):
        self.items[key] = value
        self.items.move_to_end(key)
        if len(self.items) > self.capacity:
            self.items.popitem(last=False)
```

## 39d.24 The Python toolkit for coding rounds

Chapter 49a is the full Python brush-up; this list is the subset a coding round leans on.

- **`collections.deque`** for queues: O(1) `append` and `popleft`. `list.pop(0)` is O(n).
- **`heapq`** is a min-heap on a list: `heappush`, `heappop`, `heapreplace` (pop then push, one sift), `heappushpop`, `nsmallest`/`nlargest` (heap of size k inside). Max-heap: push negated keys, which works everywhere; Python 3.14 added `heappush_max`, `heappop_max` and the rest. Ties: push `(priority, counter, item)` so items are never compared.
- **`bisect`**: `bisect_left` is the lower bound of 39d.14, `bisect_right` the upper bound; `insort` keeps a list sorted in O(n) per insert (the search is O(log n), the shift is not). Since 3.10 they take `key=`, which makes binary search on the answer one line: with `speeds = range(1, max(piles) + 1)` and `feasible(s)` true when speed s finishes in time, the answer to 875 is `speeds[bisect_left(speeds, True, key=feasible)]`.
- **`collections.Counter` and `defaultdict`**: counting and grouping in one line. `c - d` drops non-positive counts; `c.subtract(d)` keeps them. Since Python 3.10, equality treats missing keys as zero (`Counter(a=1, b=0) == Counter(a=1)`; earlier versions said no), but `len()` still counts zero-count keys — so the window templates delete a key when its count reaches zero.
- **`functools.cache`** (`lru_cache(maxsize=None)`) turns a recursive function into top-down dynamic programming; arguments must be hashable (tuples, not lists).
- **Recursion depth**: the default limit is 1,000 frames. Prefer iterative BFS or an explicit stack for deep structures, or call `sys.setrecursionlimit` and say you would not in production.
- **Sorting** is Timsort, stable, O(n log n); `key=` beats comparison functions; sorting tuples sorts by the first element, then the next.
- **Strings** are immutable: build with a list and `"".join(parts)`; `s[::-1]` reverses.
- **Integers** do not overflow in Python — but say when another language would need a 64-bit type or a modulus.
- **`float("inf")`** for sentinels; `math.inf` reads better.
- **Typing**: `def f(nums: list[int]) -> int:` costs seconds and reads as care in a shared editor.

## 39d.25 A study plan

The patterns stick through spaced repetition on mixed sets, not through reading. A plan for four weeks at about ten hours a week (compress to two weeks by halving the problem counts; the Google-style round in 39c.6 needs mostly weeks 1–3):

| Week | Patterns | Problems | How |
|---|---|---|---|
| 1 | Two pointers, sliding window, prefix sums and hash maps, merge intervals, cyclic sort, binary search (including on the answer) | about 35 | Type each template from memory before the first problem of its pattern; time every problem |
| 2 | Linked lists (fast and slow, reversal), trees (BFS, DFS), islands, graph traversal, topological sort, union-find, shortest paths | about 35 | Draw before you code; explain each invariant out loud |
| 3 | Heaps (two heaps, top K, K-way merge), monotonic stack, subsets, backtracking, tries, bitwise XOR | about 30 | Mixed sets: do not look at the pattern label before solving |
| 4 | Dynamic programming (knapsack and the other families), greedy, design classics, concurrency; then mock interviews | about 25 plus 4 mocks | Mock interviews on a plain editor with no execution, out loud, with a timer |

Three habits make the plan work. First, keep an error log: for every problem you missed, write the cue you failed to see and the invariant you got wrong; reread the log before each session. Second, revisit: redo every missed problem three days later and again a week later without looking at your old code. Third, practice without running code at least half the time, because that is how many coding rounds work, and walk through two examples by hand before saying "done".

On AI assistants: use them as a coach after you have tried — ask for a hint about the pattern, not the code; ask it to generate adversarial test cases for your solution; ask it to explain why your approach failed. Do not let it write your first attempt. Assume the interview forbids AI help unless the company says otherwise, and practice under that assumption.

## 39d.26 Talking through a problem: a worked example

The problem: *given an array of fruit types along a row of trees, collect as many fruits as possible in a contiguous stretch using two baskets, each holding one type* (904 Fruit Into Baskets). What a strong candidate says, compressed:

1. **Restate and clarify.** "I need the longest contiguous subarray with at most two distinct values. Can the array be empty? Are the types small integers? Up to 10⁵ elements?" (It cannot be empty; types are integers; up to 10⁵.)
2. **Brute force.** "For each start, extend until a third type appears: O(n²), too slow for 10⁵."
3. **Name the pattern and why.** "The answer is a contiguous run, and the condition 'at most two types' is monotone — any window inside a valid window is valid — so a variable sliding window works: grow on the right, shrink on the left while there are three types."
4. **State the invariant.** "After each step, the window is the longest valid window ending at `right`, and the counter holds the types inside it."
5. **Code** (`longest_with_k_distinct` with k = 2) while narrating each line.
6. **Test by hand.** `[1, 2, 1]` → 3; `[0, 1, 2, 2]` → 3 (window moves past the 0); `[1, 2, 3, 2, 2]` → 4. Mention the edge case of a single element.
7. **Complexity.** "O(n) time — each index enters and leaves the window once — and O(1) space, because the counter never holds more than three keys."
8. **Follow-up ready.** "For k baskets, the same code with k. To count windows instead of the longest, add `right − left + 1` each step."

That script — restate, brute force, pattern with the reason, invariant, code, hand test, complexity, follow-up — is the same for every pattern in this chapter, and it is most of what an interviewer means by "communication" in a coding round.

**Interview line:** *"Brute force first; then the pattern and the cue that points to it — a contiguous run under a monotone condition is a sliding window, a sorted pair is two pointers, k sorted lists is a heap of heads; then the invariant, the code, a hand test on an edge case, and the complexity before you ask."*

## Sources

- Arslan Ahmad, "Mastering the 20 Coding Patterns for Interviews", Design Gurus blog, 10 April 2026 (the twenty-pattern list and its sample problems): https://www.designgurus.io/blog/grokking-the-coding-interview-patterns
- Design Gurus, *Grokking the Coding Interview: Patterns for Coding Questions* (course page, which in October 2026 lists 31 common and 11 advanced patterns): https://www.designgurus.io/course/grokking-the-coding-interview
- LeetCode problem set: https://leetcode.com/problemset/. Numbers, titles and Premium status (†) checked in October 2026 against the doocs/leetcode index, which mirrors LeetCode's titles and lock marks but drops question marks, so 785's title was checked on leetcode.com (https://leetcode.doocs.org/en/; repository https://github.com/doocs/leetcode).
- Python documentation: `heapq`, including the max-heap functions added in 3.14 (https://docs.python.org/3/library/heapq.html); `bisect`, with `key=` since 3.10 (https://docs.python.org/3/library/bisect.html); `collections`, for `Counter` equality since 3.10 (https://docs.python.org/3/library/collections.html); `threading` (https://docs.python.org/3/library/threading.html); `concurrent.futures`, including `InterpreterPoolExecutor` (https://docs.python.org/3/library/concurrent.futures.html); "What's New in Python 3.14" (https://docs.python.org/3/whatsnew/3.14.html).
- PEP 703, "Making the Global Interpreter Lock Optional in CPython" (accepted October 2023; experimental free-threaded build in 3.13): https://peps.python.org/pep-0703/
- PEP 779, "Criteria for supported status for free-threaded Python" (3.14: supported, still optional): https://peps.python.org/pep-0779/
- A. B. Kahn, "Topological sorting of large networks", *Communications of the ACM* 5(11), 1962 (the in-degree algorithm used in 39d.19).
- R. W. Floyd's cycle-finding method, as presented in the exercises to section 3.1 of D. E. Knuth, *The Art of Computer Programming*, Vol. 2 (the tortoise-and-hare argument in 39d.5).
- E. W. Dijkstra, "A note on two problems in connexion with graphs", *Numerische Mathematik* 1, 1959 (39d.23).
- R. E. Tarjan, "Efficiency of a good but not linear set union algorithm", *Journal of the ACM* 22(2), 1975, and R. E. Tarjan and J. van Leeuwen, "Worst-case analysis of set union algorithms", *Journal of the ACM* 31(2), 1984 (the near-constant bound for union-find, and for the path halving used in 39d.23).
- Code: `labs/coding-patterns/patterns.py`, `test_patterns.py` and `check_chapter_sync.py` in this repository (standard-library Python 3.10+; run `python3 test_patterns.py`).
