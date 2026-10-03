"""Tested templates for the coding-interview patterns in chapter 39d.

Standard library only, Python 3.10+. Each section holds one reusable template and the classic
problems it solves; the LeetCode number is in each docstring. Run `python3 test_patterns.py`.

Conventions: functions that LeetCode specifies as in-place mutate their input (as the interview
version would); the tests pass copies. Indices are 0-based unless a docstring says otherwise.
"""
from __future__ import annotations

import heapq
import threading
from bisect import bisect_left
from collections import Counter, OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

# --------------------------------------------------------------------------- shared structures


class ListNode:
    __slots__ = ("val", "next")

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def build_list(values):
    head = None
    for value in reversed(list(values)):
        head = ListNode(value, head)
    return head


def list_values(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


class TreeNode:
    __slots__ = ("val", "left", "right")

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build_tree(level_order):
    """Build a tree from LeetCode's level-order list, with None for a missing child."""
    if not level_order or level_order[0] is None:
        return None
    values = iter(level_order)
    root = TreeNode(next(values))
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for side in ("left", "right"):
            value = next(values, StopIteration)
            if value is StopIteration:
                return root
            if value is not None:
                child = TreeNode(value)
                setattr(node, side, child)
                queue.append(child)
    return root


DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# --------------------------------------------------------------------------- 1. two pointers


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


# --------------------------------------------------------------------------- 2. islands (matrix traversal)


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


# --------------------------------------------------------------------------- 3. fast and slow pointers


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


# --------------------------------------------------------------------------- 4. sliding window


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


# --------------------------------------------------------------------------- 5. merge intervals


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


# --------------------------------------------------------------------------- 6. cyclic sort


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


# --------------------------------------------------------------------------- 7. in-place reversal of a linked list


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


# --------------------------------------------------------------------------- 8. tree breadth-first search


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


# --------------------------------------------------------------------------- 9. tree depth-first search


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


# --------------------------------------------------------------------------- 10. two heaps


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


# --------------------------------------------------------------------------- 11. subsets


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


# --------------------------------------------------------------------------- 12. modified binary search


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


# --------------------------------------------------------------------------- 13. top K elements


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


# --------------------------------------------------------------------------- 14. bitwise XOR


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


# --------------------------------------------------------------------------- 15. backtracking


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


# --------------------------------------------------------------------------- 16. 0/1 knapsack (dynamic programming)


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


# --------------------------------------------------------------------------- 17. topological sort


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


# --------------------------------------------------------------------------- 18. K-way merge


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


# --------------------------------------------------------------------------- 19. monotonic stack


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


# --------------------------------------------------------------------------- 20. multi-threaded


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


# --------------------------------------------------------------------------- beyond the twenty


def subarray_sum_equals_k(nums, k):
    """Count subarrays summing to k (LC 560): prefix sums in a hash map; works with negatives."""
    seen = Counter({0: 1})
    running = count = 0
    for x in nums:
        running += x
        count += seen[running - k]
        seen[running] += 1
    return count


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
