"""Tested code for chapter 39f: the classic templates, binary-tree thinking, data-structure design and graphs.

Standard library only, Python 3.10+. Run `python3 -B test_frameworks_1.py` (one line per group) and
`python3 -B check_chapter_sync.py 39f` (the code printed in the chapter must match this file).

Chapter 39d's lab (labs/coding-patterns/patterns.py) holds the basic templates this file builds on:
two pointers, sliding window, iterative reversal, monotonic stack, Kahn's algorithm, UnionFind,
Dijkstra, Trie and LRUCache. Nothing is imported from it, so this file runs on its own.

Conventions: functions that LeetCode specifies as in-place mutate their input; the tests pass copies.
Indices are 0-based unless a docstring says otherwise. Code that draws random numbers takes an `rng`
argument (default: the `random` module) so the tests can pass a seeded random.Random.
"""
import hashlib
import heapq
import operator
import random
import re
from bisect import bisect_left, insort
from collections import Counter, OrderedDict, defaultdict, deque
from functools import cache
from itertools import accumulate

# --------------------------------------------------------------------------- shared structures


class ListNode:
    __slots__ = ("val", "next")

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    """Binary-tree node. `next` (LC 116) and `parent` (LC 1650) stay None unless a problem uses them."""
    __slots__ = ("val", "left", "right", "next", "parent")

    def __init__(self, val=0, left=None, right=None, next=None, parent=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next
        self.parent = parent


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


def build_tree(level_order):
    """Tree from LeetCode's level-order list, with None for a missing child."""
    if not level_order or level_order[0] is None:
        return None
    root = TreeNode(level_order[0])
    queue, i = deque([root]), 1
    while queue and i < len(level_order):
        node = queue.popleft()
        if level_order[i] is not None:
            node.left = TreeNode(level_order[i])
            queue.append(node.left)
        i += 1
        if i < len(level_order) and level_order[i] is not None:
            node.right = TreeNode(level_order[i])
            queue.append(node.right)
        i += 1
    return root


# --------------------------------------------------------------------------- 39f.1 two ways to think


def good_nodes_traverse(root):
    """Count Good Nodes (LC 1448), traversal: the walk carries the path maximum; the count lives outside."""
    count = 0

    def walk(node, high):                   # high: the largest value on the path above node
        nonlocal count
        if node is None:
            return
        if node.val >= high:
            count += 1
        walk(node.left, max(high, node.val))
        walk(node.right, max(high, node.val))

    walk(root, float("-inf"))
    return count


def good_nodes_decompose(root, high=float("-inf")):
    """The same count, decomposition: the good nodes of this subtree, given the largest value above it."""
    if root is None:
        return 0
    here = max(high, root.val)
    return (root.val >= high) + good_nodes_decompose(root.left, here) + good_nodes_decompose(root.right, here)


def leaves_traverse(root):
    """Leaf values from left to right (the sequence LC 872 compares), traversal: append at each leaf."""
    out = []

    def walk(node):
        if node is None:
            return
        if node.left is None and node.right is None:
            out.append(node.val)
        walk(node.left)
        walk(node.right)

    walk(root)
    return out


def leaves_decompose(root):
    """The same sequence, decomposition: the left subtree's leaves, then the right's. O(n * height) copying."""
    if root is None:
        return []
    if root.left is None and root.right is None:
        return [root.val]
    return leaves_decompose(root.left) + leaves_decompose(root.right)


def node_report(root):
    """(value, depth, subtree size, inorder rank) for every node, in preorder, from one walk."""
    rows, rank = [], 0

    def walk(node, depth):
        nonlocal rank
        if node is None:
            return 0
        row = [node.val, depth, 0, 0]
        rows.append(row)                    # preorder position
        left_size = walk(node.left, depth + 1)
        row[3] = rank                       # inorder position
        rank += 1
        right_size = walk(node.right, depth + 1)
        row[2] = 1 + left_size + right_size     # postorder position
        return row[2]

    walk(root, 0)
    return [tuple(row) for row in rows]


def climb_stairs_traverse(n):
    """Ways to climb n stairs in steps of 1 or 2 (LC 70), traversal: count the leaves."""
    count = 0

    def walk(position):
        nonlocal count
        if position >= n:
            count += position == n          # a leaf of the decision tree: count it if it lands on n
            return
        walk(position + 1)
        walk(position + 2)

    walk(0)
    return count


def climb_stairs_decompose(n):
    """Same count, decomposition: ways(k) = ways(k - 1) + ways(k - 2), memoized. O(n)."""
    @cache
    def ways(k):
        if k <= 1:
            return 1
        return ways(k - 1) + ways(k - 2)

    return ways(n)


# --------------------------------------------------------------------------- 39f.2 linked lists


def merge_two_lists(a, b):
    """Merge two sorted lists by relinking their nodes (LC 21). Stable: on ties, a's node goes first."""
    dummy = tail = ListNode()
    while a and b:
        if b.val < a.val:
            tail.next, b = b, b.next
        else:
            tail.next, a = a, a.next
        tail = tail.next
    tail.next = a if a else b               # one list is used up: append the rest of the other
    return dummy.next


def partition_list(head, x):
    """Nodes with values < x first, then the others, each part in its original order (LC 86)."""
    small = small_tail = ListNode()
    large = large_tail = ListNode()
    while head:
        if head.val < x:
            small_tail.next = head
            small_tail = head
        else:
            large_tail.next = head
            large_tail = head
        head = head.next
    large_tail.next = None                  # the last large node may still point into the small part
    small_tail.next = large.next
    return small.next


def merge_k_lists_divide(lists):
    """Merge k sorted lists by merging pairs in rounds (LC 23): O(N log k), no heap."""
    lists = list(lists)
    if not lists:
        return None
    while len(lists) > 1:
        paired = [merge_two_lists(lists[i], lists[i + 1]) for i in range(0, len(lists) - 1, 2)]
        lists = paired + lists[2 * len(paired):]   # an odd list out waits for the next round
    return lists[0]


def kth_from_end(head, k):
    """The kth node from the end (k >= 1) in one pass, or None if the list is shorter."""
    lead = head
    for _ in range(k):
        if lead is None:
            return None
        lead = lead.next
    trail = head
    while lead:                             # the gap stays k, so trail stops k nodes before the end
        lead, trail = lead.next, trail.next
    return trail


def remove_nth_from_end(head, n):
    """Delete the nth node from the end, 1 <= n <= length (LC 19), in one pass."""
    dummy = ListNode(0, head)
    lead = head
    for _ in range(n):
        lead = lead.next
    before = dummy                          # starts one node behind head: the gap to lead is n + 1
    while lead:
        lead, before = lead.next, before.next
    before.next = before.next.next          # lead fell off, so before.next is the nth node from the end
    return dummy.next


def get_intersection_node(a, b):
    """First node shared by two lists, or None (LC 160): each pointer walks both lists."""
    p, q = a, b
    while p is not q:
        p = p.next if p else b
        q = q.next if q else a
    return p


def delete_duplicates(head):
    """Sorted list: keep one node per value (LC 83)."""
    node = head
    while node and node.next:
        if node.next.val == node.val:
            node.next = node.next.next      # unlink the copy; stay, in case of a third one
        else:
            node = node.next
    return head


def delete_duplicates_all(head):
    """Sorted list: remove every value that occurs more than once (LC 82)."""
    dummy = tail = ListNode()
    node = head
    while node:
        if node.next and node.next.val == node.val:
            value = node.val
            while node and node.val == value:
                node = node.next            # skip the whole run of this value
        else:
            tail.next = node
            tail = node
            node = node.next
    tail.next = None
    return dummy.next


def reverse_list_recursive(head):
    """Reverse a list (LC 206) by recursion. Definition: returns the head of the reversed list."""
    if head is None or head.next is None:
        return head
    new_head = reverse_list_recursive(head.next)    # trust it: the rest is reversed, head.next is its tail
    head.next.next = head
    head.next = None
    return new_head


def reverse_first_n(head, n):
    """Reverse the first n nodes, 1 <= n <= length; return the new head. The old head (now the tail)
    points at the node after the block."""
    if n == 1:
        return head
    new_head = reverse_first_n(head.next, n - 1)    # head.next is now the tail, pointing at the successor
    successor = head.next.next
    head.next.next = head
    head.next = successor
    return new_head


def reverse_between_recursive(head, left, right):
    """Reverse positions left..right, 1-indexed (LC 92): hang the reversed block on the node before it."""
    dummy = ListNode(0, head)               # left = 1 needs a node before the block too
    before = dummy
    for _ in range(left - 1):
        before = before.next
    before.next = reverse_first_n(before.next, right - left + 1)
    return dummy.next


def reverse_k_group_recursive(head, k):
    """Reverse every full block of k nodes; a short tail stays as it is (LC 25)."""
    node = head
    for _ in range(k):
        if node is None:
            return head                     # fewer than k nodes left
        node = node.next
    new_head = reverse_first_n(head, k)     # head is now the block's tail, pointing at `node`
    head.next = reverse_k_group_recursive(node, k)
    return new_head


def is_palindrome_list_recursive(head):
    """Palindrome linked list (LC 234) by postorder recursion. O(n) time and stack."""
    front = head

    def check(node):
        nonlocal front
        if node is None:
            return True
        if not check(node.next):
            return False
        if node.val != front.val:           # postorder position: node runs from the tail backward
            return False
        front = front.next
        return True

    return check(head)


# --------------------------------------------------------------------------- 39f.3 arrays


def remove_element(nums, val):
    """Remove every val in place and return the new length (LC 27); nums[:write] is the kept part."""
    write = 0
    for x in nums:
        if x != val:
            nums[write] = x
            write += 1
    return write


def move_zeroes(nums):
    """Move the zeros to the end, keeping the order of the others (LC 283): swap each nonzero forward."""
    write = 0
    for read, x in enumerate(nums):
        if x != 0:
            nums[write], nums[read] = x, nums[write]    # nums[write:read] holds only zeros
            write += 1


def remove_duplicates_keep_k(nums, k):
    """Sorted input: keep at most k copies of each value in place (LC 26: k = 1; LC 80: k = 2)."""
    write = 0
    for x in nums:
        if write < k or nums[write - k] != x:   # x would not be the (k + 1)th copy
            nums[write] = x
            write += 1
    return write


def reverse_in_place(items, lo=0, hi=None):
    """Reverse items[lo..hi], inclusive, with two pointers moving toward each other (LC 344)."""
    hi = len(items) - 1 if hi is None else hi
    while lo < hi:
        items[lo], items[hi] = items[hi], items[lo]
        lo += 1
        hi -= 1


def rotate_array(nums, k):
    """Rotate right by k steps in place with O(1) extra space (LC 189): three reversals."""
    n = len(nums)
    if n == 0:
        return
    k %= n
    reverse_in_place(nums, 0, n - 1)        # the last k values move to the front, but backward
    reverse_in_place(nums, 0, k - 1)
    reverse_in_place(nums, k, n - 1)


def longest_palindrome(s):
    """Longest palindromic substring (LC 5): expand around all 2n - 1 centers. O(n²), O(1) space."""
    def expand(lo, hi):
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            lo -= 1
            hi += 1
        return lo + 1, hi                   # s[lo + 1:hi] is the palindrome

    best_lo = best_hi = 0
    for center in range(len(s)):
        for lo, hi in (expand(center, center), expand(center, center + 1)):
            if hi - lo > best_hi - best_lo:
                best_lo, best_hi = lo, hi
    return s[best_lo:best_hi]


def rotate_image(matrix):
    """Rotate an n x n matrix 90 degrees clockwise in place (LC 48): transpose, then reverse each row."""
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()


def rotate_image_counterclockwise(matrix):
    """Rotate 90 degrees counterclockwise in place: transpose, then reverse the order of the rows."""
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    matrix.reverse()


def spiral_order(matrix):
    """Clockwise spiral order (LC 54): four boundaries that close in after each side is read."""
    if not matrix or not matrix[0]:
        return []
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    out = []
    while top <= bottom and left <= right:
        out.extend(matrix[top][c] for c in range(left, right + 1))
        top += 1
        out.extend(matrix[r][right] for r in range(top, bottom + 1))
        right -= 1
        if top <= bottom:                   # a row is left to read backward
            out.extend(matrix[bottom][c] for c in range(right, left - 1, -1))
            bottom -= 1
        if left <= right:                   # a column is left to read upward
            out.extend(matrix[r][left] for r in range(bottom, top - 1, -1))
            left += 1
    return out


def generate_spiral_matrix(n):
    """Fill an n x n matrix with 1..n² in spiral order (LC 59): walk, and turn right when blocked."""
    matrix = [[0] * n for _ in range(n)]
    steps = ((0, 1), (1, 0), (0, -1), (-1, 0))     # right, down, left, up
    r = c = d = 0
    for value in range(1, n * n + 1):
        matrix[r][c] = value
        dr, dc = steps[d]
        if not (0 <= r + dr < n and 0 <= c + dc < n and matrix[r + dr][c + dc] == 0):
            d = (d + 1) % 4
            dr, dc = steps[d]
        r, c = r + dr, c + dc
    return matrix


def n_sum(nums, n, target):
    """All unique n-tuples (n >= 2) summing to target, as sorted lists (LC 15: n = 3; LC 18: n = 4)."""
    arr = sorted(nums)

    def solve(start, k, goal):
        out = []
        if k == 2:
            lo, hi = start, len(arr) - 1
            while lo < hi:
                total = arr[lo] + arr[hi]
                if total < goal:
                    lo += 1
                elif total > goal:
                    hi -= 1
                else:
                    out.append([arr[lo], arr[hi]])
                    lo += 1
                    hi -= 1
                    while lo < hi and arr[lo] == arr[lo - 1]:
                        lo += 1
                    while lo < hi and arr[hi] == arr[hi + 1]:
                        hi -= 1
            return out
        for i in range(start, len(arr) - k + 1):
            if i > start and arr[i] == arr[i - 1]:
                continue                    # same first value: the same tuples again
            if arr[i] * k > goal:
                break                       # even the k smallest remaining values overshoot
            if arr[i] + arr[-1] * (k - 1) < goal:
                continue                    # even the largest partners fall short
            for rest in solve(i + 1, k - 1, goal - arr[i]):
                out.append([arr[i]] + rest)
        return out

    return solve(0, n, target)


def four_sum(nums, target):
    """Unique quadruplets summing to target (LC 18)."""
    return n_sum(nums, 4, target)


# --------------------------------------------------------------------------- 39f.4 prefix sums and differences


class NumArray:
    """Range sums of a fixed array in O(1) per query (LC 303): prefix[i] is the sum of nums[:i]."""

    def __init__(self, nums):
        self.prefix = [0]
        for x in nums:
            self.prefix.append(self.prefix[-1] + x)

    def sum_range(self, left, right):
        """Sum of nums[left..right], inclusive."""
        return self.prefix[right + 1] - self.prefix[left]


class NumMatrix:
    """Rectangle sums of a fixed matrix in O(1) per query (LC 304), zero-padded prefix table."""

    def __init__(self, matrix):
        rows, cols = len(matrix), len(matrix[0]) if matrix else 0
        self.pre = [[0] * (cols + 1) for _ in range(rows + 1)]
        for r in range(rows):
            for c in range(cols):
                self.pre[r + 1][c + 1] = (matrix[r][c] + self.pre[r][c + 1]
                                          + self.pre[r + 1][c] - self.pre[r][c])

    def sum_region(self, r1, c1, r2, c2):
        """Sum of the rectangle with corners (r1, c1) and (r2, c2), inclusive."""
        p = self.pre
        return p[r2 + 1][c2 + 1] - p[r1][c2 + 1] - p[r2 + 1][c1] + p[r1][c1]


def add_to_ranges(nums, updates):
    """nums after each (lo, hi, delta) adds delta to nums[lo..hi], inclusive: O(len(nums) + len(updates))."""
    jumps = [b - a for a, b in zip([0] + nums, nums)] + [0]    # jumps[i] = nums[i] - nums[i - 1], one spare
    for lo, hi, delta in updates:
        jumps[lo] += delta                  # the values from lo onward rise by delta ...
        jumps[hi + 1] -= delta              # ... and from hi + 1 onward fall back
    return list(accumulate(jumps[:-1]))


def get_modified_array(length, updates):
    """Range Addition (LC 370): apply inclusive (start, end, inc) updates to an all-zero array."""
    return add_to_ranges([0] * length, updates)


def corp_flight_bookings(bookings, n):
    """Seats booked on each of flights 1..n (LC 1109); a booking is [first, last, seats], 1-indexed."""
    return add_to_ranges([0] * n, [(first - 1, last - 1, seats) for first, last, seats in bookings])


def car_pooling(trips, capacity):
    """Can one car serve every trip (LC 1094)? A trip is [passengers, start, end]; riders leave at end."""
    if not trips:
        return True
    stretches = max(end for _, _, end in trips)         # stretch p is the drive from p to p + 1
    aboard = add_to_ranges([0] * stretches, [(start, end - 1, riders) for riders, start, end in trips])
    return max(aboard) <= capacity


# --------------------------------------------------------------------------- 39f.5 sliding window


def check_inclusion(s1, s2):
    """Does s2 contain a permutation of s1 (LC 567)? A window of len(s1) and a count of unbalanced letters."""
    balance = Counter(s1)                   # per letter: s1's count minus the window's count
    unbalanced = len(balance)               # letters whose balance is not 0

    def shift(ch, step):
        nonlocal unbalanced
        unbalanced -= balance[ch] != 0
        balance[ch] += step
        unbalanced += balance[ch] != 0

    for right, ch in enumerate(s2):
        shift(ch, -1)                       # Q1: s2[right] enters the window
        if right >= len(s1):
            shift(s2[right - len(s1)], +1)  # Q2: the oldest letter leaves, so the length stays len(s1)
        if unbalanced == 0:                 # Q3: every count matches s1's, so the window is a permutation
            return True
    return False


def longest_ones(nums, k):
    """Longest run of 1s after flipping at most k zeros (LC 1004): the longest window with <= k zeros."""
    zeros = left = best = 0
    for right, x in enumerate(nums):
        zeros += x == 0                     # Q1
        while zeros > k:                    # Q2: shrink while the window is invalid
            zeros -= nums[left] == 0
            left += 1
        best = max(best, right - left + 1)  # Q3: after shrinking, the window is valid
    return best


def num_subarray_product_less_than_k(nums, k):
    """Count subarrays with product < k, positive values (LC 713): each right end adds right - left + 1."""
    if k <= 1:
        return 0
    product = 1
    left = count = 0
    for right, x in enumerate(nums):
        product *= x
        while product >= k:
            product //= nums[left]          # exact: nums[left] is a factor of product
            left += 1
        count += right - left + 1           # the valid windows ending at right start at left..right
    return count


def min_operations_to_zero(nums, x):
    """Fewest end removals that reduce x to exactly 0 (LC 1658), or -1."""
    goal = sum(nums) - x
    if goal < 0:
        return -1
    left = window = 0
    best = -1
    for right, value in enumerate(nums):
        window += value
        while window > goal:
            window -= nums[left]
            left += 1
        if window == goal:
            best = max(best, right - left + 1)
    return -1 if best < 0 else len(nums) - best


def longest_substring_k_repeats(s, k):
    """Longest substring whose letters all occur at least k times (LC 395). O(26 n)."""
    best = 0
    for u in range(1, len(set(s)) + 1):
        counts = Counter()
        left = distinct = full = 0          # full: letters with count >= k
        for right, ch in enumerate(s):
            counts[ch] += 1
            distinct += counts[ch] == 1
            full += counts[ch] == k
            while distinct > u:
                out = s[left]
                full -= counts[out] == k
                counts[out] -= 1
                distinct -= counts[out] == 0
                left += 1
            if distinct == u == full:
                best = max(best, right - left + 1)
    return best


def subarrays_with_k_distinct(nums, k):
    """Count subarrays with exactly k distinct values (LC 992): at_most(k) - at_most(k - 1)."""
    def at_most(m):
        counts = Counter()
        left = total = 0
        for right, x in enumerate(nums):
            counts[x] += 1
            while len(counts) > m:
                counts[nums[left]] -= 1
                if counts[nums[left]] == 0:
                    del counts[nums[left]]
                left += 1
            total += right - left + 1
        return total

    return at_most(k) - at_most(k - 1)


def find_repeated_dna_sequences(s, length=10):
    """Substrings of the given length that occur more than once (LC 187), exact rolling code."""
    code_of = {"A": 0, "C": 1, "G": 2, "T": 3}
    mask = (1 << (2 * length)) - 1
    seen, repeated = set(), set()
    code = 0
    for right, ch in enumerate(s):
        code = ((code << 2) | code_of[ch]) & mask
        if right >= length - 1:
            if code in seen:
                repeated.add(s[right - length + 1:right + 1])
            else:
                seen.add(code)
    return sorted(repeated)


def str_str_rabin_karp(haystack, needle, base=256, mod=1_000_000_007):
    """Index of the first occurrence of needle, or -1 (LC 28), by Rabin-Karp."""
    m, n = len(needle), len(haystack)
    if m == 0:
        return 0
    if m > n:
        return -1
    high = pow(base, m - 1, mod)            # weight of the window's leading character
    target = window = 0
    for i in range(m):
        target = (target * base + ord(needle[i])) % mod
        window = (window * base + ord(haystack[i])) % mod
    for start in range(n - m + 1):
        if window == target and haystack[start:start + m] == needle:
            return start
        if start + m < n:
            window = ((window - ord(haystack[start]) * high) * base + ord(haystack[start + m])) % mod
    return -1


# --------------------------------------------------------------------------- 39f.6 binary search


def binary_search(nums, target):
    """Index of target in a sorted list, or -1 (LC 704), on the closed interval [lo, hi]."""
    lo, hi = 0, len(nums) - 1
    while lo <= hi:                         # [lo, hi] is not empty
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1                    # mid is ruled out, so it leaves the interval too
        else:
            hi = mid - 1
    return -1


def left_bound(nums, target):
    """First index of target in a sorted list, or -1. On exit, lo is the insertion point (bisect_left)."""
    lo, hi = 0, len(nums) - 1
    while lo <= hi:                         # invariant: nums[:lo] < target <= nums[hi + 1:]
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1                    # mid might be the answer, but nums[hi + 1:] remembers it
    if lo < len(nums) and nums[lo] == target:
        return lo
    return -1


def right_bound(nums, target):
    """Last index of target in a sorted list, or -1. On exit, hi is bisect_right - 1."""
    lo, hi = 0, len(nums) - 1
    while lo <= hi:                         # invariant: nums[:lo] <= target < nums[hi + 1:]
        mid = lo + (hi - lo) // 2
        if nums[mid] <= target:
            lo = mid + 1
        else:
            hi = mid - 1
    if hi >= 0 and nums[hi] == target:
        return hi
    return -1


def first_true(lo, hi, predicate):
    """Smallest x in [lo, hi] with predicate(x) true, for a false-then-true predicate; else hi + 1."""
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if predicate(mid):
            hi = mid - 1
        else:
            lo = mid + 1
    return lo


def ship_within_days(weights, days):
    """Least capacity that ships the packages in order within `days` days (LC 1011)."""
    def fits(capacity):
        used, load = 1, 0
        for w in weights:
            if load + w > capacity:         # greedy: fill each day as far as it goes
                used += 1
                load = 0
            load += w
        return used <= days

    return first_true(max(weights), sum(weights), fits)


def split_array(nums, k):
    """Split Array Largest Sum (LC 410): the same search as LC 1011 (values are >= 0)."""
    return ship_within_days(nums, k)


class WeightedPicker:
    """Random Pick with Weight (LC 528): index i with probability w[i] / sum(w)."""

    def __init__(self, w, rng=random):
        self.prefix = list(accumulate(w))   # index i owns the tickets prefix[i - 1] + 1 .. prefix[i]
        self.rng = rng

    def pick_index(self):
        ticket = self.rng.randint(1, self.prefix[-1])
        return bisect_left(self.prefix, ticket)     # first index whose range reaches the ticket


def advantage_count(nums1, nums2):
    """Advantage Shuffle (LC 870): our values, smallest first, take the smallest unbeaten value they beat."""
    targets = sorted(range(len(nums2)), key=nums2.__getitem__)    # nums2's positions, smallest value first
    out = [None] * len(nums2)
    spare = []                              # our values that beat nothing still unbeaten
    beaten = 0
    for x in sorted(nums1):
        if x > nums2[targets[beaten]]:
            out[targets[beaten]] = x
            beaten += 1
        else:
            spare.append(x)
    for i in targets[beaten:]:              # the positions we cannot win take the spare values
        out[i] = spare.pop()
    return out


# --------------------------------------------------------------------------- 39f.7 stacks and queues


class MyQueue:
    """Queue from two stacks (LC 232): amortized O(1) per operation."""

    def __init__(self):
        self.inbox, self.outbox = [], []

    def push(self, x):
        self.inbox.append(x)

    def _refill(self):
        if not self.outbox:                 # only when empty, or newer items would jump the line
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def pop(self):
        self._refill()
        return self.outbox.pop()

    def peek(self):
        self._refill()
        return self.outbox[-1]

    def empty(self):
        return not self.inbox and not self.outbox


class MyStack:
    """Stack from one queue (LC 225): rotate after each push. Push O(n), pop and top O(1)."""

    def __init__(self):
        self.queue = deque()

    def push(self, x):
        self.queue.append(x)
        for _ in range(len(self.queue) - 1):
            self.queue.append(self.queue.popleft())

    def pop(self):
        return self.queue.popleft()

    def top(self):
        return self.queue[0]

    def empty(self):
        return not self.queue


def nearest_index(nums, beats, reverse=False):
    """Nearest index to the right (left if reverse) whose value beats nums[i], else -1. O(n)."""
    out = [-1] * len(nums)
    waiting = []
    for i in (range(len(nums) - 1, -1, -1) if reverse else range(len(nums))):
        while waiting and beats(nums[i], nums[waiting[-1]]):
            out[waiting.pop()] = i          # i is the first to beat it from that side
        waiting.append(i)
    return out


def sum_subarray_mins(arr, mod=10**9 + 7):
    """Sum of the minimums of all subarrays (LC 907), O(n)."""
    n = len(arr)
    prev_smaller = nearest_index(arr, operator.lt, reverse=True)
    next_smaller_eq = nearest_index(arr, operator.le)
    total = 0
    for i, x in enumerate(arr):
        starts = i - prev_smaller[i]
        ends = (next_smaller_eq[i] if next_smaller_eq[i] >= 0 else n) - i
        total += x * starts * ends
    return total % mod


class MaxMinQueue:
    """FIFO queue that also reports its maximum and minimum, amortized O(1) per operation."""

    def __init__(self):
        self.items = deque()
        self.front = 0                      # arrival number of the item at the front
        self.high = deque()                 # (arrival, value) candidates for the max; values fall front to back
        self.low = deque()                  # (arrival, value) candidates for the min; values rise front to back

    def push(self, x):
        arrival = self.front + len(self.items)
        self.items.append(x)
        while self.high and self.high[-1][1] <= x:
            self.high.pop()                 # leaves before x and is no larger: never the maximum again
        self.high.append((arrival, x))
        while self.low and self.low[-1][1] >= x:
            self.low.pop()
        self.low.append((arrival, x))

    def pop(self):
        x = self.items.popleft()
        if self.high[0][0] == self.front:   # the departing item was the front candidate
            self.high.popleft()
        if self.low[0][0] == self.front:
            self.low.popleft()
        self.front += 1
        return x

    def max(self):
        return self.high[0][1]

    def min(self):
        return self.low[0][1]

    def __len__(self):
        return len(self.items)


def max_sliding_window_queue(nums, k):
    """Sliding Window Maximum (LC 239) with MaxMinQueue: push the arrival, pop the departure."""
    window, out = MaxMinQueue(), []
    for i, x in enumerate(nums):
        window.push(x)
        if len(window) > k:
            window.pop()
        if i >= k - 1:
            out.append(window.max())
    return out


def longest_subarray_within_limit(nums, limit):
    """Longest subarray with max - min <= limit (LC 1438): a sliding window kept in a MaxMinQueue."""
    window = MaxMinQueue()
    best = 0
    for x in nums:
        window.push(x)
        while window.max() - window.min() > limit:
            window.pop()                    # the queue's front is the window's left end
        best = max(best, len(window))
    return best


def remove_duplicate_letters(s):
    """Smallest subsequence, in lexicographic order, with exactly one copy of each letter (LC 316, LC 1081)."""
    last = {ch: i for i, ch in enumerate(s)}    # the last index of each letter
    stack, kept = [], set()
    for i, ch in enumerate(s):
        if ch in kept:
            continue
        while stack and stack[-1] > ch and last[stack[-1]] > i:
            kept.remove(stack.pop())        # a larger letter with a copy still ahead can wait for it
        stack.append(ch)
        kept.add(ch)
    return "".join(stack)


# --------------------------------------------------------------------------- 39f.8 binary trees


def invert_tree_traverse(root):
    """Invert a binary tree (LC 226), traversal thinking: swap the children at every node."""
    def walk(node):
        if node is None:
            return
        node.left, node.right = node.right, node.left   # preorder position
        walk(node.left)
        walk(node.right)

    walk(root)
    return root


def connect_perfect(root):
    """Populating Next Right Pointers (LC 116), perfect tree: preorder, using the parent's next."""
    if root is None or root.left is None:
        return root
    root.left.next = root.right
    if root.next:
        root.right.next = root.next.left    # the link that crosses between two parents
    connect_perfect(root.left)
    connect_perfect(root.right)
    return root


def flatten(root):
    """Flatten into a right-leaning preorder chain, in place (LC 114)."""
    def flat(node):
        if node is None:
            return None
        left_tail = flat(node.left)
        right_tail = flat(node.right)
        if left_tail:
            left_tail.right = node.right
            node.right, node.left = node.left, None
        return right_tail or left_tail or node

    flat(root)


def construct_maximum_binary_tree(nums):
    """Maximum Binary Tree (LC 654) from its definition: the maximum is the root. O(n²) worst case."""
    def build(lo, hi):                      # the tree for nums[lo:hi]
        if lo >= hi:
            return None
        top = max(range(lo, hi), key=nums.__getitem__)
        return TreeNode(nums[top], build(lo, top), build(top + 1, hi))

    return build(0, len(nums))


def construct_maximum_binary_tree_stack(nums):
    """Maximum Binary Tree in O(n) with a decreasing stack, which holds the right spine built so far."""
    stack = []
    for x in nums:
        node = TreeNode(x)
        while stack and stack[-1].val < x:
            node.left = stack.pop()         # the smaller run hangs below x, on its left
        if stack:
            stack[-1].right = node          # x is the new right child of the nearest larger value
        stack.append(node)
    return stack[0] if stack else None


def build_tree_pre_in(preorder, inorder):
    """Rebuild a tree from its preorder and inorder lists, distinct values (LC 105). O(n)."""
    where = {v: i for i, v in enumerate(inorder)}

    def build(pre_lo, in_lo, size):
        if size == 0:
            return None
        root_val = preorder[pre_lo]         # preorder starts with the root
        k = where[root_val] - in_lo         # inorder: the k values before the root form the left subtree
        left = build(pre_lo + 1, in_lo, k)
        right = build(pre_lo + 1 + k, in_lo + k + 1, size - 1 - k)
        return TreeNode(root_val, left, right)

    return build(0, 0, len(preorder))


def build_tree_in_post(inorder, postorder):
    """Rebuild a tree from its inorder and postorder lists, distinct values (LC 106). O(n)."""
    where = {v: i for i, v in enumerate(inorder)}

    def build(in_lo, post_lo, size):
        if size == 0:
            return None
        root_val = postorder[post_lo + size - 1]    # postorder ends with the root
        k = where[root_val] - in_lo
        left = build(in_lo, post_lo, k)
        right = build(in_lo + k + 1, post_lo + k, size - 1 - k)
        return TreeNode(root_val, left, right)

    return build(0, 0, len(inorder))


def build_tree_pre_post(preorder, postorder):
    """A tree with these preorder and postorder lists (LC 889); a lone child goes left."""
    where = {v: i for i, v in enumerate(postorder)}

    def build(pre_lo, post_lo, size):
        if size == 0:
            return None
        root = TreeNode(preorder[pre_lo])
        if size > 1:
            k = where[preorder[pre_lo + 1]] - post_lo + 1   # size of the subtree rooted at the next value
            root.left = build(pre_lo + 1, post_lo, k)
            root.right = build(pre_lo + 1 + k, post_lo + k, size - 1 - k)
        return root

    return build(0, 0, len(preorder))


def find_duplicate_subtrees(root):
    """One root per subtree that occurs at least twice (LC 652): postorder ids, O(n)."""
    ids, seen, out = {}, Counter(), []

    def subtree_id(node):
        if node is None:
            return 0
        key = (subtree_id(node.left), node.val, subtree_id(node.right))
        uid = ids.setdefault(key, len(ids) + 1)
        seen[uid] += 1
        if seen[uid] == 2:                  # report each repeated subtree once
            out.append(node)
        return uid

    subtree_id(root)
    return out


def serialize_preorder(root):
    """Preorder with "#" for every empty child (LC 297); the markers make the tree recoverable."""
    out = []

    def walk(node):
        if node is None:
            out.append("#")
            return
        out.append(str(node.val))
        walk(node.left)
        walk(node.right)

    walk(root)
    return ",".join(out)


def deserialize_preorder(data):
    """Inverse of serialize_preorder: read the tokens in the order they were written."""
    tokens = iter(data.split(","))

    def build():
        token = next(tokens)
        if token == "#":
            return None
        node = TreeNode(int(token))
        node.left = build()
        node.right = build()
        return node

    return build()


def serialize_level(root):
    """Level order with "#" for empty children and trailing markers dropped (LeetCode's own format)."""
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append("#")
            continue
        out.append(str(node.val))
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] == "#":
        out.pop()
    return ",".join(out)


def deserialize_level(data):
    """Inverse of serialize_level: each node, in queue order, takes the next two tokens as its children."""
    if not data:
        return None
    tokens = data.split(",")

    def make(i):
        return TreeNode(int(tokens[i])) if i < len(tokens) and tokens[i] != "#" else None

    root = TreeNode(int(tokens[0]))
    queue, i = deque([root]), 1
    while queue:
        node = queue.popleft()
        node.left, node.right = make(i), make(i + 1)
        i += 2
        queue.extend(child for child in (node.left, node.right) if child)
    return root


def traverse_with_stack(root):
    """Preorder, inorder and postorder from one explicit-stack walk; a frame is [node, stage]."""
    pre, ino, post = [], [], []
    stack = [[root, 0]] if root else []
    while stack:
        frame = stack[-1]
        node, stage = frame
        if stage == 0:
            pre.append(node.val)            # preorder position
            frame[1] = 1
            if node.left:
                stack.append([node.left, 0])
        elif stage == 1:
            ino.append(node.val)            # inorder position
            frame[1] = 2
            if node.right:
                stack.append([node.right, 0])
        else:
            post.append(node.val)           # postorder position
            stack.pop()
    return pre, ino, post


# --------------------------------------------------------------------------- 39f.9 binary search trees


class BSTIterator:
    """Inorder iterator over a BST (LC 173): O(h) memory, amortized O(1) per call."""

    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node:                         # the path to the smallest value not yet returned
            self.stack.append(node)
            node = node.left

    def next(self):
        node = self.stack.pop()
        self._push_left(node.right)
        return node.val

    def has_next(self):
        return bool(self.stack)


def kth_smallest(root, k):
    """kth smallest value in a BST, 1-indexed (LC 230): stop the inorder walk after k steps. O(h + k)."""
    walk = BSTIterator(root)
    for _ in range(k - 1):
        walk.next()
    return walk.next()


def convert_bst(root):
    """Greater Sum Tree (LC 538, LC 1038): each value becomes the sum of all values >= it. Reverse inorder."""
    running = 0

    def walk(node):
        nonlocal running
        if node is None:
            return
        walk(node.right)                    # larger values first
        running += node.val
        node.val = running
        walk(node.left)

    walk(root)
    return root


def is_valid_bst(root):
    """Strict BST check (LC 98): pass down the open interval that each subtree's values must lie in."""
    def fits(node, low, high):
        if node is None:
            return True
        if not low < node.val < high:
            return False
        return fits(node.left, low, node.val) and fits(node.right, node.val, high)

    return fits(root, float("-inf"), float("inf"))


def search_bst(root, val):
    """The node holding val, or None (LC 700): one comparison per level, O(h)."""
    node = root
    while node and node.val != val:
        node = node.left if val < node.val else node.right
    return node


def insert_into_bst(root, val):
    """Insert a value that is not in the BST yet (LC 701) and return the root."""
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert_into_bst(root.left, val)
    else:
        root.right = insert_into_bst(root.right, val)
    return root


def delete_node(root, key):
    """Delete key from a BST and return the new root (LC 450), O(h)."""
    if root is None:
        return None
    if key < root.val:
        root.left = delete_node(root.left, key)
        return root
    if key > root.val:
        root.right = delete_node(root.right, key)
        return root
    if root.left is None or root.right is None:     # at most one child: it takes the node's place
        return root.left or root.right
    parent, successor = root, root.right            # two children: the smallest node on the right
    while successor.left:
        parent, successor = successor, successor.left
    if parent is not root:                          # unhook it; its right subtree takes its place
        parent.left = successor.right
        successor.right = root.right
    successor.left = root.left
    return successor


def num_trees(n):
    """Number of structurally unique BSTs on 1..n (LC 96): pick the root, multiply the two sides' counts."""
    @cache
    def count(size):                        # depends only on how many values, not which
        if size <= 1:
            return 1
        return sum(count(left) * count(size - 1 - left) for left in range(size))

    return count(n)


def generate_trees(n):
    """Every structurally unique BST on 1..n (LC 95). Results share subtrees, which LeetCode accepts."""
    @cache
    def build(lo, hi):
        if lo > hi:
            return (None,)
        trees = []
        for root_val in range(lo, hi + 1):
            for left in build(lo, root_val - 1):
                for right in build(root_val + 1, hi):
                    trees.append(TreeNode(root_val, left, right))
        return tuple(trees)

    return list(build(1, n)) if n else []


def max_sum_bst(root):
    """Largest key sum of a BST subtree (LC 1373); 0 counts the empty tree."""
    best = 0

    def summary(node):                      # (smallest key, largest key, sum) if a BST, else None
        nonlocal best
        if node is None:
            return float("inf"), float("-inf"), 0
        left, right = summary(node.left), summary(node.right)
        if left is None or right is None or not left[1] < node.val < right[0]:
            return None
        total = left[2] + node.val + right[2]
        best = max(best, total)
        return min(left[0], node.val), max(right[1], node.val), total

    summary(root)
    return best


# --------------------------------------------------------------------------- 39f.10 lowest common ancestor


def lca_bst(root, p, q):
    """LCA in a BST (LC 235): walk down until p and q are on different sides. O(h)."""
    lo, hi = min(p.val, q.val), max(p.val, q.val)
    node = root
    while node:
        if node.val < lo:
            node = node.right
        elif node.val > hi:
            node = node.left
        else:
            return node                     # lo <= node.val <= hi: the paths split here
    return None


def lca_maybe_missing(root, p, q):
    """LCA of p and q, or None if either is missing from the tree (LC 1644)."""
    found = 0

    def walk(node):
        nonlocal found
        if node is None:
            return None
        left = walk(node.left)
        right = walk(node.right)
        if node is p or node is q:          # postorder position: the children were searched first
            found += 1
            return node
        if left and right:
            return node
        return left or right

    lca = walk(root)
    return lca if found == 2 else None


def lca_with_parent(p, q):
    """LCA with parent pointers and no root (LC 1650): LC 160's switch on the paths up."""
    a, b = p, q
    while a is not b:
        a = a.parent if a else q
        b = b.parent if b else p
    return a


def lca_of_nodes(root, nodes):
    """LCA of nodes that are all in the tree (LC 1676): LC 236's search with a set of targets."""
    targets = set(nodes)

    def walk(node):
        if node is None or node in targets:
            return node
        left, right = walk(node.left), walk(node.right)
        if left and right:
            return node
        return left or right

    return walk(root)


def lca_deepest_leaves(root):
    """LCA of the deepest leaves (LC 1123, same as LC 865): each call returns (height, that LCA)."""
    def walk(node):
        if node is None:
            return 0, None
        left_height, left_lca = walk(node.left)
        right_height, right_lca = walk(node.right)
        if left_height == right_height:     # deepest leaves on both sides: this node joins them
            return left_height + 1, node
        if left_height > right_height:
            return left_height + 1, left_lca
        return right_height + 1, right_lca

    return walk(root)[1]


# --------------------------------------------------------------------------- 39f.11 tree follow-ups


def count_nodes(root):
    """Nodes in a complete binary tree (LC 222) in O(log² n)."""
    left_height = right_height = 0
    node = root
    while node:
        left_height += 1
        node = node.left
    node = root
    while node:
        right_height += 1
        node = node.right
    if left_height == right_height:         # perfect: 2^h - 1 nodes, no need to look inside
        return (1 << left_height) - 1
    return 1 + count_nodes(root.left) + count_nodes(root.right)


class NestedInteger:
    """A minimal stand-in for LeetCode's interface: an int, or a list of NestedInteger."""

    def __init__(self, value):
        self.value = value

    def is_integer(self):
        return isinstance(self.value, int)

    def get_integer(self):
        return self.value

    def get_list(self):
        return self.value


class NestedIterator:
    """Flatten Nested List Iterator (LC 341), lazily: a stack of list iterators."""

    def __init__(self, nested_list):
        self.stack = [iter(nested_list)]
        self.ready = None                   # the next integer, once has_next has found it

    def has_next(self):
        while self.ready is None and self.stack:
            item = next(self.stack[-1], None)
            if item is None:
                self.stack.pop()            # that list is used up
            elif item.is_integer():
                self.ready = item.get_integer()
            else:
                self.stack.append(iter(item.get_list()))
        return self.ready is not None

    def next(self):
        self.has_next()
        value, self.ready = self.ready, None
        return value


def merge_sorted(a, b):
    """Merge two sorted lists into a new sorted list, O(len(a) + len(b))."""
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if b[j] < a[i]:
            out.append(b[j])
            j += 1
        else:
            out.append(a[i])
            i += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def count_smaller(nums):
    """For each i, how many later values are smaller (LC 315): merge sort of indices."""
    counts = [0] * len(nums)

    def sort(idx):
        if len(idx) <= 1:
            return idx
        mid = len(idx) // 2
        left, right = sort(idx[:mid]), sort(idx[mid:])
        merged, j = [], 0
        for i in left:
            while j < len(right) and nums[right[j]] < nums[i]:
                merged.append(right[j])
                j += 1
            counts[i] += j                  # postorder position: both halves are sorted
            merged.append(i)
        merged.extend(right[j:])
        return merged

    sort(list(range(len(nums))))
    return counts


def reverse_pairs(nums):
    """Count pairs i < j with nums[i] > 2 * nums[j] (LC 493): count across halves, then merge."""
    def sort(arr):
        if len(arr) <= 1:
            return arr, 0
        mid = len(arr) // 2
        left, a = sort(arr[:mid])
        right, b = sort(arr[mid:])
        count, j = a + b, 0
        for x in left:                      # both halves sorted, so j only moves forward
            while j < len(right) and x > 2 * right[j]:
                j += 1
            count += j
        return merge_sorted(left, right), count

    return sort(nums)[1]


def count_range_sum(nums, lower, upper):
    """Count ranges i..j whose sum lies in [lower, upper] (LC 327): merge sort on prefix sums."""
    prefix = [0, *accumulate(nums)]

    def sort(arr):
        if len(arr) <= 1:
            return arr, 0
        mid = len(arr) // 2
        left, a = sort(arr[:mid])
        right, b = sort(arr[mid:])
        count, lo, hi = a + b, 0, 0
        for p in left:
            while lo < len(right) and right[lo] < p + lower:
                lo += 1
            while hi < len(right) and right[hi] <= p + upper:
                hi += 1
            count += hi - lo
        return merge_sorted(left, right), count

    return sort(prefix)[1]


def find_kth_largest(nums, k, rng=random):
    """kth largest (LC 215) by quickselect with a three-way partition; expected O(n)."""
    arr = list(nums)
    target = len(arr) - k                   # the answer's index in ascending order
    lo, hi = 0, len(arr) - 1
    while True:
        pivot = arr[rng.randint(lo, hi)]
        lt, i, gt = lo, lo, hi              # arr[lo:lt] < pivot, arr[lt:i] == pivot, arr[gt + 1:hi + 1] > pivot
        while i <= gt:
            if arr[i] < pivot:
                arr[lt], arr[i] = arr[i], arr[lt]
                lt += 1
                i += 1
            elif arr[i] > pivot:
                arr[i], arr[gt] = arr[gt], arr[i]
                gt -= 1
            else:
                i += 1
        if target < lt:
            hi = lt - 1
        elif target > gt:
            lo = gt + 1
        else:
            return pivot


# --------------------------------------------------------------------------- 39f.12 design


class _Link:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = None


class LRUCacheLinked:
    """LRU cache (LC 146) from a dict and a doubly linked list with two sentinels; capacity >= 1."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.nodes = {}
        self.head, self.tail = _Link(), _Link()     # head.next is the oldest, tail.prev the newest
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _append(self, node):
        node.prev, node.next = self.tail.prev, self.tail
        self.tail.prev.next = node
        self.tail.prev = node

    def get(self, key):
        node = self.nodes.get(key)
        if node is None:
            return -1
        self._unlink(node)
        self._append(node)
        return node.value

    def put(self, key, value):
        node = self.nodes.get(key)
        if node:
            node.value = value
            self._unlink(node)
        else:
            if len(self.nodes) == self.capacity:
                oldest = self.head.next
                self._unlink(oldest)
                del self.nodes[oldest.key]
            node = self.nodes[key] = _Link(key, value)
        self._append(node)


class LFUCache:
    """LFU cache (LC 460): key -> [value, freq], freq -> keys in recency order, min_freq. O(1)."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}
        self.buckets = defaultdict(OrderedDict)
        self.min_freq = 0

    def _touch(self, key):
        entry = self.entries[key]
        freq = entry[1]
        del self.buckets[freq][key]
        if not self.buckets[freq]:
            del self.buckets[freq]
            if self.min_freq == freq:
                self.min_freq = freq + 1
        entry[1] = freq + 1
        self.buckets[freq + 1][key] = None

    def get(self, key):
        if key not in self.entries:
            return -1
        self._touch(key)
        return self.entries[key][0]

    def put(self, key, value):
        if self.capacity <= 0:
            return
        if key in self.entries:
            self.entries[key][0] = value
            self._touch(key)
            return
        if len(self.entries) == self.capacity:
            evicted, _ = self.buckets[self.min_freq].popitem(last=False)
            if not self.buckets[self.min_freq]:
                del self.buckets[self.min_freq]
            del self.entries[evicted]
        self.entries[key] = [value, 1]
        self.buckets[1][key] = None
        self.min_freq = 1


class RandomizedSet:
    """Insert, remove and get_random in O(1) average (LC 380): a list plus value -> index."""

    def __init__(self, rng=random):
        self.values, self.index, self.rng = [], {}, rng

    def insert(self, val):
        if val in self.index:
            return False
        self.index[val] = len(self.values)
        self.values.append(val)
        return True

    def remove(self, val):
        i = self.index.pop(val, None)
        if i is None:
            return False
        last = self.values.pop()
        if i < len(self.values):            # val was not the last element: fill its hole
            self.values[i] = last
            self.index[last] = i
        return True

    def get_random(self):
        return self.values[self.rng.randrange(len(self.values))]


class RandomizedCollection:
    """The multiset version (LC 381): value -> set of its positions; get_random is weighted by count."""

    def __init__(self, rng=random):
        self.values, self.where, self.rng = [], defaultdict(set), rng

    def insert(self, val):
        self.where[val].add(len(self.values))
        self.values.append(val)
        return len(self.where[val]) == 1

    def remove(self, val):
        if not self.where.get(val):
            return False
        i = self.where[val].pop()
        last = self.values.pop()
        last_pos = len(self.values)         # where `last` used to be
        if i != last_pos:
            self.values[i] = last
            self.where[last].discard(last_pos)
            self.where[last].add(i)
        if not self.where[val]:
            del self.where[val]
        return True

    def get_random(self):
        return self.values[self.rng.randrange(len(self.values))]


class BlacklistPicker:
    """Uniform pick from [0, n) minus a blacklist (LC 710), one draw per pick."""

    def __init__(self, n, blacklist, rng=random):
        self.size = n - len(blacklist)
        self.rng = rng
        banned = set(blacklist)
        spare = (x for x in range(self.size, n) if x not in banned)
        self.remap = {b: next(spare) for b in blacklist if b < self.size}

    def pick(self):
        x = self.rng.randrange(self.size)
        return self.remap.get(x, x)


class ExamRoom:
    """Exam Room (LC 855): free stretches in a heap keyed by (-distance, seat); stale ones skipped."""

    def __init__(self, n):
        self.n = n
        self.right_of = {-1: n}             # occupied seat (or the left wall) -> next occupied (or wall)
        self.left_of = {n: -1}
        self.heap = []
        self._add_stretch(-1, n)

    def _add_stretch(self, a, b):
        if b - a < 2:
            return                          # no empty seat between a and b
        if a == -1:
            seat, dist = 0, b
        elif b == self.n:
            seat, dist = self.n - 1, self.n - 1 - a
        else:
            seat, dist = (a + b) // 2, (b - a) // 2
        heapq.heappush(self.heap, (-dist, seat, a, b))

    def seat(self):
        while True:
            _, seat, a, b = heapq.heappop(self.heap)
            if self.right_of.get(a) == b:   # is the stretch still there?
                break
        self.right_of[a], self.right_of[seat] = seat, b
        self.left_of[b], self.left_of[seat] = seat, a
        self._add_stretch(a, seat)
        self._add_stretch(seat, b)
        return seat

    def leave(self, p):
        a, b = self.left_of.pop(p), self.right_of.pop(p)
        self.right_of[a], self.left_of[b] = b, a
        self._add_stretch(a, b)


def calculate(s):
    """Evaluate + - * / and parentheses, dividing toward zero (LC 224, 227, 772)."""
    tokens = re.findall(r"\d+|[-+*/()]", s)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take():
        nonlocal pos
        pos += 1
        return tokens[pos - 1]

    def expr():
        value = term()
        while peek() in ("+", "-"):
            if take() == "+":
                value += term()
            else:
                value -= term()
        return value

    def term():
        value = factor()
        while peek() in ("*", "/"):
            if take() == "*":
                value *= factor()
            else:
                divisor = factor()
                quotient = abs(value) // abs(divisor)
                value = quotient if (value >= 0) == (divisor > 0) else -quotient
        return value

    def factor():
        token = take()
        if token == "-":
            return -factor()
        if token == "+":
            return factor()
        if token == "(":
            value = expr()
            take()                          # the matching ")"
            return value
        return int(token)

    return expr()


class ConsistentHashRing:
    """Consistent hashing with virtual nodes: a key belongs to the first point at or after it."""

    def __init__(self, replicas=100):
        self.replicas = replicas
        self.points = []                    # sorted positions on the ring
        self.owner = {}                     # position -> server

    @staticmethod
    def _hash(text):
        return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")

    def add(self, server):
        for r in range(self.replicas):
            point = self._hash(f"{server}#{r}")
            if point not in self.owner:     # a 64-bit collision is very unlikely; skip it if it happens
                self.owner[point] = server
                insort(self.points, point)

    def remove(self, server):
        for r in range(self.replicas):
            point = self._hash(f"{server}#{r}")
            if self.owner.get(point) == server:
                del self.owner[point]
                self.points.pop(bisect_left(self.points, point))

    def lookup(self, key):
        if not self.points:
            raise LookupError("the ring is empty")
        i = bisect_left(self.points, self._hash(key)) % len(self.points)    # wrap past the top
        return self.owner[self.points[i]]


class SegmentTree:
    """Point update and range query for an associative operation with an identity, O(log n)."""

    def __init__(self, values, combine=operator.add, identity=0):
        self.combine, self.identity = combine, identity
        self.size = 1
        while self.size < len(values):
            self.size *= 2
        self.tree = [identity] * (2 * self.size)
        self.tree[self.size:self.size + len(values)] = values
        for i in range(self.size - 1, 0, -1):
            self.tree[i] = combine(self.tree[2 * i], self.tree[2 * i + 1])

    def update(self, index, value):
        """values[index] = value, then recompute the ancestors."""
        i = index + self.size
        self.tree[i] = value
        while i > 1:
            i //= 2
            self.tree[i] = self.combine(self.tree[2 * i], self.tree[2 * i + 1])

    def query(self, left, right):
        """combine(values[left], ..., values[right]), inclusive, in left-to-right order."""
        left_acc = right_acc = self.identity
        lo, hi = left + self.size, right + self.size + 1    # half-open [lo, hi) over the leaves
        while lo < hi:
            if lo & 1:                      # lo is a right child: its parent reaches past the range
                left_acc = self.combine(left_acc, self.tree[lo])
                lo += 1
            if hi & 1:                      # hi - 1 is a left child: same on the right edge
                hi -= 1
                right_acc = self.combine(self.tree[hi], right_acc)
            lo //= 2
            hi //= 2
        return self.combine(left_acc, right_acc)


class _SegNode:
    __slots__ = ("left", "right", "total", "best", "pending")

    def __init__(self):
        self.left = self.right = None
        self.total = self.best = self.pending = 0


class RangeAddTree:
    """Range add, range sum and range max on [lo, hi], all values starting at 0."""

    def __init__(self, lo, hi):
        self.lo, self.hi = lo, hi
        self.root = _SegNode()

    @staticmethod
    def _apply(node, lo, hi, val):
        node.total += val * (hi - lo + 1)
        node.best += val
        node.pending += val

    def _push_down(self, node, lo, mid, hi):
        if node.left is None:
            node.left, node.right = _SegNode(), _SegNode()
        if node.pending:
            self._apply(node.left, lo, mid, node.pending)
            self._apply(node.right, mid + 1, hi, node.pending)
            node.pending = 0

    def add(self, left, right, val):
        """Add val to every index in [left, right]."""
        self._add(self.root, self.lo, self.hi, left, right, val)

    def _add(self, node, lo, hi, left, right, val):
        if right < lo or hi < left:
            return
        if left <= lo and hi <= right:      # fully covered: update here, leave a note for the children
            self._apply(node, lo, hi, val)
            return
        mid = (lo + hi) // 2
        self._push_down(node, lo, mid, hi)
        self._add(node.left, lo, mid, left, right, val)
        self._add(node.right, mid + 1, hi, left, right, val)
        node.total = node.left.total + node.right.total
        node.best = max(node.left.best, node.right.best)

    def query(self, left, right):
        """(sum, max) over [left, right]."""
        return self._query(self.root, self.lo, self.hi, left, right)

    def _query(self, node, lo, hi, left, right):
        if right < lo or hi < left:
            return 0, float("-inf")
        if left <= lo and hi <= right:
            return node.total, node.best
        mid = (lo + hi) // 2
        self._push_down(node, lo, mid, hi)
        left_sum, left_max = self._query(node.left, lo, mid, left, right)
        right_sum, right_max = self._query(node.right, mid + 1, hi, left, right)
        return left_sum + right_sum, max(left_max, right_max)


class MyCalendarThree:
    """My Calendar III (LC 732): after each booking [start, end), the largest number of overlapping bookings."""

    def __init__(self, horizon=10**9):
        self.tree = RangeAddTree(0, horizon)

    def book(self, start, end):
        self.tree.add(start, end - 1, 1)
        return self.tree.query(0, self.tree.hi)[1]


def replace_words(dictionary, sentence):
    """Replace each word by its shortest root from the dictionary (LC 648), with a trie of the roots."""
    trie = {}
    for root in dictionary:
        node = trie
        for ch in root:
            node = node.setdefault(ch, {})
        node["$"] = root                    # the end marker stores the whole root

    def shortest_root(word):
        node = trie
        for ch in word:
            if "$" in node or ch not in node:
                break
            node = node[ch]
        return node.get("$", word)

    return " ".join(shortest_root(word) for word in sentence.split())


class WordDictionary:
    """Add words; search with "." matching any one letter (LC 211): a trie plus DFS on every "." branch."""

    def __init__(self):
        self.root = {}

    def add_word(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def search(self, word):
        def match(node, i):
            if i == len(word):
                return "$" in node
            if word[i] == ".":
                return any(match(child, i + 1) for ch, child in node.items() if ch != "$")
            child = node.get(word[i])
            return child is not None and match(child, i + 1)

        return match(self.root, 0)


class MapSum:
    """Map Sum Pairs (LC 677): every trie node stores the total value of the keys below it."""

    def __init__(self):
        self.values = {}
        self.root = {"#": 0}

    def insert(self, key, val):
        delta = val - self.values.get(key, 0)
        self.values[key] = val
        node = self.root
        node["#"] += delta
        for ch in key:
            node = node.setdefault(ch, {"#": 0})
            node["#"] += delta

    def sum(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node:
                return 0
            node = node[ch]
        return node["#"]


# --------------------------------------------------------------------------- 39f.13 graphs


def is_bipartite(graph):
    """Can the nodes split into two sides with every edge crossing (LC 785)? BFS two-coloring per component."""
    color = {}
    for start in range(len(graph)):
        if start in color:
            continue
        color[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in graph[u]:
                if v not in color:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    return False            # an edge inside one side closes an odd cycle
    return True


def possible_bipartition(n, dislikes):
    """Split people 1..n into two groups with no dislike pair inside a group (LC 886)."""
    graph = [[] for _ in range(n + 1)]
    for a, b in dislikes:
        graph[a].append(b)
        graph[b].append(a)
    return is_bipartite(graph)


def find_directed_cycle(n, edges):
    """A directed cycle as [v, ..., v], or None if acyclic: iterative DFS with three states."""
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
    state = [0] * n                         # 0 new, 1 on the path, 2 finished
    parent = [-1] * n
    for start in range(n):
        if state[start]:
            continue
        state[start] = 1
        stack = [(start, iter(graph[start]))]
        while stack:
            u, neighbors = stack[-1]
            v = next(neighbors, None)
            if v is None:
                state[u] = 2                # postorder position: everything below u is explored
                stack.pop()
            elif state[v] == 0:
                state[v], parent[v] = 1, u
                stack.append((v, iter(graph[v])))
            elif state[v] == 1:             # back edge u -> v: the path from v down to u, plus this edge
                cycle = [u]
                while cycle[-1] != v:
                    cycle.append(parent[cycle[-1]])
                return cycle[::-1] + [v]
    return None


def topo_sort_dfs(n, edges):
    """Topological order of 0..n-1 as the reversed DFS postorder; None if there is a cycle."""
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
    state = [0] * n
    finished = []

    def visit(u):
        state[u] = 1
        for v in graph[u]:
            if state[v] == 1 or (state[v] == 0 and not visit(v)):
                return False                # a back edge here or below: no order exists
        state[u] = 2
        finished.append(u)                  # postorder position
        return True

    for u in range(n):
        if state[u] == 0 and not visit(u):
            return None
    return finished[::-1]


class DisjointSet:
    """Union-find over any hashable items, created on first use; path compression and union by size."""

    def __init__(self):
        self.parent, self.size = {}, {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x], self.size[x] = x, 1
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:       # second pass: point the whole path at the root
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)


def solve_surrounded_regions(board):
    """Capture regions of "O" that do not reach the border (LC 130), in place."""
    if not board or not board[0]:
        return
    rows, cols = len(board), len(board[0])
    ds = DisjointSet()
    for r in range(rows):
        for c in range(cols):
            if board[r][c] != "O":
                continue
            if r in (0, rows - 1) or c in (0, cols - 1):
                ds.union((r, c), "safe")
            for nr, nc in ((r + 1, c), (r, c + 1)):     # down and right cover every edge once
                if nr < rows and nc < cols and board[nr][nc] == "O":
                    ds.union((r, c), (nr, nc))
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == "O" and not ds.connected((r, c), "safe"):
                board[r][c] = "X"


def equations_possible(equations):
    """Satisfiability of Equality Equations (LC 990): union every "a==b" first, then test every "a!=b"."""
    ds = DisjointSet()
    for eq in equations:
        if eq[1] == "=":
            ds.union(eq[0], eq[3])
    return all(not ds.connected(eq[0], eq[3]) for eq in equations if eq[1] == "!")


def max_probability(n, edges, succ_prob, start, end):
    """Path with Maximum Probability (LC 1514): Dijkstra with products, via a max-heap."""
    graph = [[] for _ in range(n)]
    for (u, v), p in zip(edges, succ_prob):
        graph[u].append((v, p))
        graph[v].append((u, p))
    best = [0.0] * n
    best[start] = 1.0
    heap = [(-1.0, start)]
    while heap:
        neg, u = heapq.heappop(heap)
        prob = -neg
        if u == end:
            return prob
        if prob < best[u]:
            continue                        # stale entry
        for v, p in graph[u]:
            if prob * p > best[v]:
                best[v] = prob * p
                heapq.heappush(heap, (-best[v], v))
    return 0.0


def minimum_effort_path(heights):
    """Path With Minimum Effort (LC 1631): minimize the largest step on the path; Dijkstra with max for +."""
    rows, cols = len(heights), len(heights[0])
    effort = [[float("inf")] * cols for _ in range(rows)]
    effort[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        e, r, c = heapq.heappop(heap)
        if (r, c) == (rows - 1, cols - 1):
            return e
        if e > effort[r][c]:
            continue
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols:
                step = max(e, abs(heights[nr][nc] - heights[r][c]))
                if step < effort[nr][nc]:
                    effort[nr][nc] = step
                    heapq.heappush(heap, (step, nr, nc))
    return effort[rows - 1][cols - 1]


def find_cheapest_price(n, flights, src, dst, k):
    """Cheapest Flights Within K Stops (LC 787): Dijkstra on states (city, flights used)."""
    graph = [[] for _ in range(n)]
    for u, v, price in flights:
        graph[u].append((v, price))
    fewest = [float("inf")] * n             # fewest flights among the expanded states at each city
    heap = [(0, src, 0)]                    # (cost, city, flights used)
    while heap:
        cost, city, used = heapq.heappop(heap)
        if city == dst:
            return cost
        if used >= fewest[city] or used > k:
            continue
        fewest[city] = used
        for nxt, price in graph[city]:
            heapq.heappush(heap, (cost + price, nxt, used + 1))
    return -1


def astar_grid(grid, start, goal):
    """A* on a 4-connected grid (0 open, 1 wall): (length or -1, cells expanded)."""
    rows, cols = len(grid), len(grid[0])
    if grid[start[0]][start[1]] or grid[goal[0]][goal[1]]:
        return -1, 0

    def h(cell):
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    dist = {start: 0}
    heap = [(h(start), h(start), start)]    # (f = g + h, h to break ties toward the goal, cell)
    closed = set()
    while heap:
        _, _, cell = heapq.heappop(heap)
        if cell in closed:
            continue
        closed.add(cell)
        if cell == goal:
            return dist[cell], len(closed)
        r, c = cell
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nxt[0] < rows and 0 <= nxt[1] < cols and not grid[nxt[0]][nxt[1]]:
                g = dist[cell] + 1
                if g < dist.get(nxt, float("inf")):
                    dist[nxt] = g
                    heapq.heappush(heap, (g + h(nxt), h(nxt), nxt))
    return -1, len(closed)


def kruskal_mst(n, edges):
    """Minimum spanning tree weight by Kruskal; edges are (u, v, w). None if disconnected."""
    ds = DisjointSet()
    total = used = 0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if ds.union(u, v):
            total += w
            used += 1
    return total if used == max(n - 1, 0) else None


def prim_mst(n, edges):
    """Minimum spanning tree weight by lazy Prim; edges are (u, v, w). None if disconnected."""
    if n == 0:
        return 0
    graph = [[] for _ in range(n)]
    for u, v, w in edges:
        graph[u].append((w, v))
        graph[v].append((w, u))
    in_tree = [False] * n
    heap = [(0, 0)]
    total = count = 0
    while heap and count < n:
        w, u = heapq.heappop(heap)
        if in_tree[u]:
            continue                        # stale: u joined through a cheaper edge
        in_tree[u] = True
        total += w
        count += 1
        for edge in graph[u]:
            if not in_tree[edge[1]]:
                heapq.heappush(heap, edge)
    return total if count == n else None


def min_cost_connect_points(points):
    """Min Cost to Connect All Points (LC 1584): Prim on the complete graph with a plain array, O(n²)."""
    n = len(points)
    cheapest = [float("inf")] * n           # cheapest known edge from the tree to each point outside it
    in_tree = [False] * n
    total = 0
    if n:
        cheapest[0] = 0
    for _ in range(n):
        u = min((i for i in range(n) if not in_tree[i]), key=cheapest.__getitem__)
        in_tree[u] = True
        total += cheapest[u]
        ux, uy = points[u]
        for v in range(n):
            if not in_tree[v]:
                cheapest[v] = min(cheapest[v], abs(points[v][0] - ux) + abs(points[v][1] - uy))
    return total


def find_itinerary(tickets):
    """Reconstruct Itinerary (LC 332): Hierholzer, smallest destination first."""
    graph = defaultdict(list)
    for a, b in sorted(tickets, reverse=True):
        graph[a].append(b)                  # reverse-sorted, so pop() yields the smallest destination
    route, stack = [], ["JFK"]
    while stack:
        while graph[stack[-1]]:
            stack.append(graph[stack[-1]].pop())
        route.append(stack.pop())
    return route[::-1]


def valid_arrangement(pairs):
    """Valid Arrangement of Pairs (LC 2097): an Eulerian path of the pairs."""
    graph = defaultdict(list)
    balance = Counter()
    for a, b in pairs:
        graph[a].append(b)
        balance[a] += 1
        balance[b] -= 1
    start = next((node for node, d in balance.items() if d == 1), pairs[0][0])
    path, stack = [], [start]
    while stack:
        while graph[stack[-1]]:
            stack.append(graph[stack[-1]].pop())
        path.append(stack.pop())
    path.reverse()
    return [[path[i], path[i + 1]] for i in range(len(path) - 1)]


def floyd_warshall(n, edges):
    """All-pairs shortest distances for directed edges (u, v, w), inf if unreachable. O(n³)."""
    inf = float("inf")
    dist = [[0 if i == j else inf for j in range(n)] for i in range(n)]
    for u, v, w in edges:
        dist[u][v] = min(dist[u][v], w)
    for k in range(n):
        row_k = dist[k]
        for i in range(n):
            via = dist[i][k]
            if via == inf:
                continue
            row_i = dist[i]
            for j in range(n):
                if via + row_k[j] < row_i[j]:
                    row_i[j] = via + row_k[j]
    return dist


def find_the_city(n, edges, distance_threshold):
    """The city with the fewest others within the threshold, the largest index on ties (LC 1334)."""
    dist = floyd_warshall(n, list(edges) + [(v, u, w) for u, v, w in edges])
    best_city, best_count = -1, n + 1
    for i in range(n):
        count = sum(1 for j in range(n) if j != i and dist[i][j] <= distance_threshold)
        if count <= best_count:             # <=, so a later (larger) index wins a tie
            best_city, best_count = i, count
    return best_city
