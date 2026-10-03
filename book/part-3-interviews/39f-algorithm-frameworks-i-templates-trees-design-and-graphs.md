# 39f. Algorithm frameworks I: the classic templates, binary-tree thinking, data-structure design and graph algorithms

> **What you need to be able to say:** whether your recursion walks a structure (traversal) or builds an answer from its parts (decomposition), and what the code knows at the preorder, inorder and postorder positions; the single sliding-window template and its three questions; one binary-search convention with its invariant; how to assemble O(1) caches, random-access sets and range-query trees from simpler parts; and which graph algorithm a problem needs, with the property that makes it correct — no improving extensions for Dijkstra, a consistent heuristic for A*, the cut property for minimum spanning trees, balanced degrees for an Eulerian path.

## 39f.1 How to think about algorithms

This chapter follows the topic map of labuladong's algorithm notes (https://labuladong.online/en/algo/home/) — the "Classic Problem Solving Templates" and "Data Structure Algorithms" chapters — and extends it; 39e covers the data structures from the inside, and 39g covers backtracking, BFS, dynamic programming, greedy algorithms and math. The order and choice of problems follow the notes, as do a few of their framings, credited where they appear; the explanations, proofs, examples, code and tests are this book's own, and each section adds invariants, proof sketches, complexity, pitfalls and interview follow-ups. The basic templates already in 39d are referred to as 39d.x, not printed again.

Every function and class below is copied verbatim from `labs/algorithm-frameworks/frameworks_1.py` (`python3 -B check_chapter_sync.py 39f` enforces it), and `test_frameworks_1.py` checks nearly every function against a brute-force reference on hundreds of seeded random inputs; the figures quoted in the text (call counts, keys moved, cells expanded) are measured and asserted there too. To practice, delete a function body, rewrite it from memory, and rerun the tests. The code uses these imports, the same `ListNode` as 39d (fields `val` and `next`; the module defines its own copy so that it runs alone), and a `TreeNode` with the two extra fields, `next` and `parent`, that two LeetCode variants need; `build_list`, `list_values` and `build_tree` in the module convert from Python lists and LeetCode's level-order notation:

```python
import hashlib
import heapq
import operator
import random
import re
from bisect import bisect_left, insort
from collections import Counter, OrderedDict, defaultdict, deque
from functools import cache
from itertools import accumulate


class TreeNode:
    """Binary-tree node. `next` (LC 116) and `parent` (LC 1650) stay None unless a problem uses them."""
    __slots__ = ("val", "left", "right", "next", "parent")

    def __init__(self, val=0, left=None, right=None, next=None, parent=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next
        self.parent = parent
```

### 39f.1.1 Enumeration, pruning and reuse

One observation underlies labuladong's notes and is worth keeping in view: a computer answers a search question by trying candidates, so designing an algorithm means organizing the trying, and the trying goes wrong in two ways — a candidate is never examined, so the answer can be wrong, or the same work is done again and again, so the answer comes too late. Every technique in this chapter repairs one of the two. **Ordered enumeration** — two pointers, sliding windows, binary search — uses sortedness or monotonicity to prove that whole groups of candidates cannot win: in a sorted two-sum, the n²/2 pairs form a triangle, and each comparison rules out a whole row or column of it. **Recursive enumeration** — backtracking, dynamic programming — walks a tree of decisions, so every candidate is reached, and stores the answers to repeated subproblems, so none is computed twice. **Data structures** — prefix sums, heaps, segment trees, hash maps — keep partial answers ready so nothing is recomputed. When stuck, write the brute force and ask which candidates cannot matter (prune them) and which work repeats (store it).

### 39f.1.2 Two ways to write a recursive function: traversal and decomposition

Every recursive function walks a tree — the tree of its calls — so binary trees are where recursion is easiest to learn, and labuladong's notes organize all of recursion around one split between two ways of writing it:

1. **Traversal.** A walker visits every node once; the function returns nothing, and the answer accumulates in variables outside the calls. You design it by deciding what the walker records, and at which point of its visit.
2. **Decomposition.** The function promises an answer for any subtree, and a tree's answer is assembled from the answers its children return. You design it by writing the promise down in one sentence and then relying on it for the children, without unrolling their calls — the inductive step of a proof.

Here are two problems, each written both ways. Count Good Nodes in Binary Tree (1448) counts the nodes whose value is at least every value on the path from the root to them; Leaf-Similar Trees (872) compares two trees' leaf values from left to right, so it needs that sequence:

```python
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
```

In 1448 the largest value on the path is a fact about what lies *above* a node, so both versions pass it down as an argument; what differs is where the count lives — in one variable outside the calls, or in return values added up on the way back. Both are O(n) time and O(h) stack for a tree of height h. The decomposition version of the leaf sequence says most plainly what the sequence *is*, but every concatenation copies its operands, so each leaf is copied once per ancestor: O(n · h) in total, O(n²) for a long spine with a leaf hanging off every spine node, while the traversal version appends each leaf once. That trade is typical: decomposition is easier to prove, traversal is often cheaper.

Choose by asking where the information lives. If a tree's answer follows from its subtrees' answers (height, size, sum, "is it a BST"), write a function with a return value. If it depends on what lies *above* a node (depth, the path from the root, the allowed range of values), pass that down as parameters or keep it outside. Many solutions do both, as `good_nodes_decompose` does.

**Interview line:** *"Before I code a tree problem I say where each piece of information comes from. Facts the subtrees can report — sizes, heights, sums — I return; facts about the path above a node — a depth, a running maximum, an allowed range — I pass down; and an answer collected along the way, such as a list, I keep outside the calls."*

### 39f.1.3 What code can see at the preorder, inorder and postorder positions

39e.9.2 shows that preorder, inorder and postorder are positions in one recursive function rather than three procedures, and that a depth is known on the way into a node while a subtree size is known only on the way out. The inorder position adds one more fact: when code there runs, exactly the nodes that precede this one in inorder have been visited, so its rank is known — in a BST, the number of smaller keys. `node_report` fills four facts about each node in one walk, each at the first position where it is available:

```python
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
```

Two consequences follow. Any question that needs facts about a subtree (height, size, sum, maximum, BST-ness, a serialization) is a postorder question, and computing those facts once at the postorder position, instead of from scratch at each node, turns O(n²) into O(n) — 39d.11's diameter (543) and the maximum-sum BST of 39f.9.3 both rely on it. And the positions generalize: an n-ary tree has preorder and postorder but no single inorder position, and depth-first search on a graph has an "enter vertex" and a "leave vertex" position, which cycle detection and topological sort use in 39f.13.2.

### 39f.1.4 From trees to backtracking, dynamic programming and divide and conquer

| Style | The function returns | State lives in | Family |
|---|---|---|---|
| Traversal of a decision tree | nothing | outside variables; a path extended and undone | backtracking (39d.17, 39g.2) |
| Decomposition, overlapping subproblems | the answer for a subproblem | a memo table | dynamic programming (39d.18, 39g.7) |
| Decomposition, disjoint subproblems | the answer for a part | return values | divide and conquer: merge sort works at postorder, quicksort at preorder (39e.12.4, 39e.12.5, 39f.11) |

The smallest example of the split is counting the ways to climb n stairs in steps of 1 or 2 (70). Traversal walks the decision tree and counts the leaves that land on n, making a number of calls that grows like φⁿ (φ ≈ 1.618), because nothing is shared. Decomposition says the last step came from k − 1 or k − 2, so `ways(k) = ways(k − 1) + ways(k − 2)`, and the memo computes each k once.

```python
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
```

When you must *list* the solutions (every path, every subset), there is nothing to share and traversal is right; when you need only a count or an optimum, equal subproblems can share one answer and decomposition is right. That distinction decides between backtracking and dynamic programming throughout 39g; 39g.7.7 turns one into the other.

## 39f.2 Linked lists with two pointers

Three habits prevent most linked-list bugs: start from a **dummy node** whenever the head might change, **save `next` before overwriting it**, and **terminate the list you build** (`tail.next = None`) so a stale pointer cannot form a cycle. 39d.5 covers fast and slow pointers (cycle, cycle entry, middle, palindrome in O(1) space) and 39d.9 the iterative reversals.

### 39f.2.1 Splicing with dummy heads: merge, partition, merge k

Merging two sorted lists (21) relinks existing nodes behind a dummy head. Partitioning around x (86) deals each node to a "small" or a "large" list, then joins them. Merging k lists (23) can reuse the two-list merge in rounds, halving the number of lists each round.

```python
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
```

Merge and partition are O(n) time, O(1) space. Pairwise merging is O(N log k) for N nodes: each round touches every node once, and there are ⌈log₂ k⌉ rounds — the same bound as 39d.20's heap, without a heap or tie-breaking (the heap version suits streams). **Pitfalls.** In 86, omitting `large_tail.next = None` leaves the last large node pointing into the small part: a cycle. Merging k lists one at a time into an accumulator is O(N · k).

### 39f.2.2 Pointer gaps, and why cycle detection works

For the kth node from the end, start a lead pointer k nodes ahead and move both until the lead falls off; the gap is the invariant. Removing the nth node from the end (19) needs the node *before* the target, so the trailing pointer starts one step further back, on a dummy placed in front of the head: the gap becomes n + 1, and deleting the head is no longer a special case.

```python
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
```

39d.5 has the code for cycle detection (141) and the entry (142); here is the full proof, the standard follow-up. Let the tail before the cycle have a nodes and the cycle L nodes; the pointers are compared after every step. (1) *They meet.* Once both are in the cycle, the fast pointer gains one node per step on the slow one, so the gap between them along the direction of travel shrinks by one per step and reaches 0 within L steps of the slow pointer's arrival: the slow pointer completes at most one lap. (2) *Where.* Say they meet after t steps, b steps past the entry. The fast pointer walked 2t and the slow one t, and they stand on the same node, so the extra t steps are whole laps: t is a multiple of L. The slow pointer's t steps are a to reach the entry, b more, and possibly one whole lap, so a + b is a multiple of L as well. (3) *The entry.* From the meeting point, a more steps reach b + a ≡ 0 (mod L) past the entry — the entry itself. A pointer started at the head also reaches the entry after a steps, and cannot meet the other one sooner, because until then it is outside the cycle; so the two first meet at the entry. (4) *The length.* Hold one pointer still and walk the other around: L steps.

### 39f.2.3 Intersection by switching heads, and deduplication

If list A has x nodes of its own, list B has y, and they share c tail nodes (160), a pointer walking A then B and a pointer walking B then A each need x + y + c steps (plus one through `None`) to reach the first shared node, so they arrive together — earlier if x = y; with c = 0 they reach `None` together. O(n + m) time, O(1) space; 39f.10 reuses it for trees with parent pointers.

```python
def get_intersection_node(a, b):
    """First node shared by two lists, or None (LC 160): each pointer walks both lists."""
    p, q = a, b
    while p is not q:
        p = p.next if p else b
        q = q.next if q else a
    return p
```

Removing every value that repeats in a sorted list (82) — not just the extra copies (83, which only unlinks a repeated next node) — must drop the first node of each run, and the head may disappear, so build the result behind a dummy and skip whole runs:

```python
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
```

For an unsorted list (1836 Remove Duplicates From an Unsorted Linked List†), count values in a first pass and skip nodes whose count exceeds one in a second.

### 39f.2.4 Recursive reversal: trust the definition

The recursive reversals are the cleanest exercise in decomposition: state what the function returns, assume the recursive call keeps that promise, and handle only the node in front. `reverse_list_recursive(head)` returns the head of the reversed list. After the call on `head.next`, the rest is reversed and `head.next` still points at the old second node — now the rest's *tail* — so two assignments put `head` after it.

`reverse_first_n(head, n)` reverses only the first n nodes. A sharper definition keeps it as short: *return the new head, and leave the old head, now the block's tail, pointing at the node after the block*. By that promise, after the call on `head.next`, `head.next` is the tail of the reversed block and points at the successor, so `head` slots in between. Then reversing positions `left..right` (92) walks a pointer to the node just before the block — a dummy supplies one when the block starts at the head — and hangs the reversed block there, and reversing groups of k (25) checks that k nodes exist, reverses them, and recurses on the rest.

```python
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
```

All are O(n) time, but the recursion costs stack: O(n) for 206, O(right − left) for 92, O(n/k + k) for the groups. The iterative versions in 39d.9 use O(1) space; write those in an interview unless asked for recursion, and mention Python's default limit of 1,000 frames.

### 39f.2.5 Palindrome linked list by postorder recursion

39d.5's `is_palindrome_list` reverses the second half in O(1) space. The recursive alternative uses the call stack as a backward pointer: as the recursion unwinds, the node at the postorder position moves from the tail toward the head while `front` moves forward.

```python
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
```

It is O(n) time and stack — no better than copying to an array — but it shows that postorder on a list means "visit from the back".

**Practice set.** 21 Merge Two Sorted Lists; 86 Partition List; 23 Merge k Sorted Lists; 19 Remove Nth Node From End of List; 142 Linked List Cycle II; 160 Intersection of Two Linked Lists; 82 Remove Duplicates from Sorted List II; 92 Reverse Linked List II; 25 Reverse Nodes in k-Group; 234 Palindrome Linked List; 445 Add Two Numbers II; 148 Sort List (split at the middle, sort both halves, `merge_two_lists`).

## 39f.3 Arrays with two pointers

In an array the two pointers can be a **fast and a slow** pointer moving the same way (the slow one marks the end of the output), or **left and right** pointers moving toward each other (each step settles one end). 39d.3 covers pair sums, deduplication (26), sorted squares, 3Sum and the Dutch flag.

### 39f.3.1 Fast and slow: editing in place

Every in-place filter keeps one invariant: after reading position i, `nums[:write]` is the answer for `nums[:i + 1]`. Removing a value (27) writes every other element; moving zeros to the end (283) swaps each nonzero into the write position instead of copying it there, so the zeros gather behind that position, the other values keep their order, and no second pass is needed. Deduplication generalizes to "keep at most k copies" of each value in a sorted array (k = 1 is 26, k = 2 is 80): the copies of x already kept are the last ones written, so x may be written when the element k places back in the output differs from it.

```python
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
```

All O(n) time, O(1) space. Calling `nums.remove(0)` and `nums.append(0)` per zero is O(n²), because each removal shifts the rest of the list.

### 39f.3.2 Left and right: reversal, rotation, palindromes

Reversal (344) swaps the ends and moves inward. Rotation by k (189) is three reversals: reversing the whole array brings the last k elements to the front, backward, and reversing each part fixes their order; reversing the words of a string (151) is the same trick.

```python
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
```

Pointers can also move *outward*. Every palindrome has a center — a character or the gap between two — so the longest palindromic substring (5) comes from expanding around each of the 2n − 1 centers while the ends match:

```python
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
```

O(n²) time in the worst case and O(1) space, against O(n²) space for the dynamic program over all substrings. Manacher's algorithm reaches O(n) by reusing mirrored expansions; name it, but few interviewers expect it written.

### 39f.3.3 Two-dimensional traversal

Rotating an n × n matrix 90 degrees clockwise in place (48) is a transpose followed by reversing each row. Check it by indices: clockwise rotation means `new[i][j] = old[n − 1 − j][i]`; the transpose gives `T[i][j] = old[j][i]`, and reversing row i reads `T[i][n − 1 − j] = old[n − 1 − j][i]`. Counterclockwise is the transpose followed by reversing the order of the rows (`rotate_image_counterclockwise` in the lab).

```python
def rotate_image(matrix):
    """Rotate an n x n matrix 90 degrees clockwise in place (LC 48): transpose, then reverse each row."""
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
```

A spiral (54) reads the top row, the right column, the bottom row backward and the left column upward, shrinking four boundaries after each side; the two `if` checks stop a last single row or column from being read twice. Filling a spiral (59) uses a different method worth having: walk, and turn right when the next cell is outside or already filled.

```python
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
```

### 39f.3.4 The nSum framework

3Sum fixes one value and solves 2Sum on the rest; 4Sum fixes one value and solves 3Sum. One recursive function covers every k: sort once, and to solve k-sum from position `start`, try each distinct first value and solve (k − 1)-sum after it, down to the two-pointer base case.

```python
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
```

**No duplicates.** In sorted order, equal tuples can only come from choosing the same value twice at the same level; skipping a first value equal to its predecessor at that level (`i > start`) prevents it, and the base case skips repeats after each match. **Pruning.** k times the current value is a lower bound on every remaining sum; if it exceeds the goal, stop (`break`). If the current value plus k − 1 copies of the largest still falls short, skip it (`continue`). **Complexity.** O(n^(k − 1)) for k ≥ 2 plus the sort; `four_sum` (18) is `n_sum(nums, 4, target)`. **Pitfall.** Writing `i > 0` instead of `i > start`: below the top level it skips a value equal to the one the outer level chose, so 4Sum on [−1, −1, 1, 1] with target 0 loses [−1, −1, 1, 1].

**Practice set.** 27 Remove Element; 283 Move Zeroes; 80 Remove Duplicates from Sorted Array II; 189 Rotate Array; 151 Reverse Words in a String; 5 Longest Palindromic Substring; 48 Rotate Image; 54 Spiral Matrix; 59 Spiral Matrix II; 15 3Sum; 16 3Sum Closest; 18 4Sum.

## 39f.4 Prefix sums and difference arrays

The two are inverses: a prefix-sum array turns range *queries* into two lookups, and a difference array turns range *updates* into two writes.

Store `prefix[i]`, the sum of the first i values, with `prefix[0] = 0`; then `nums[left..right]` sums to `prefix[right + 1] − prefix[left]` (303), and the leading zero removes the `left = 0` special case. In two dimensions (304), `pre[r + 1][c + 1]` is the sum of the rectangle from (0, 0) to (r, c), filled by inclusion–exclusion (the cell, plus the rectangle above, plus the one to the left, minus their overlap, counted twice); a query subtracts the strips above and to the left and adds back the corner.

```python
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
```

O(n) or O(rows × cols) to build, O(1) per query, but static: with interleaved updates use a Fenwick tree or the segment tree of 39f.12.6. For "how many subarrays sum to k" with negatives, combine prefix sums with a hash map (39d.23).

A difference array stores the jumps between neighbors: `jumps[0] = nums[0]` and `jumps[i] = nums[i] − nums[i − 1]`. Adding v to `nums[i..j]` changes only two jumps: the one into i rises by v and the one after j falls by v. A prefix sum over the jumps rebuilds the array, and one spare slot at the end spares a bounds check. Range Addition (370†) is the template (`get_modified_array` in the lab); Corporate Flight Bookings (1109) shifts from 1-indexed flights; in Car Pooling (1094), riders are aboard on `[start, end)`, so a trip covers the stretches `start..end − 1`.

```python
def add_to_ranges(nums, updates):
    """nums after each (lo, hi, delta) adds delta to nums[lo..hi], inclusive: O(len(nums) + len(updates))."""
    jumps = [b - a for a, b in zip([0] + nums, nums)] + [0]    # jumps[i] = nums[i] - nums[i - 1], one spare
    for lo, hi, delta in updates:
        jumps[lo] += delta                  # the values from lo onward rise by delta ...
        jumps[hi + 1] -= delta              # ... and from hi + 1 onward fall back
    return list(accumulate(jumps[:-1]))


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
```

q updates cost O(n + q) instead of O(n · q), provided the reads come after the updates. In two dimensions (2536 Increment Submatrices by One), add v at one corner, subtract it past the two adjacent corners, add it back past the opposite one, then take a 2D prefix sum.

**Practice set.** 303 Range Sum Query - Immutable; 304 Range Sum Query 2D - Immutable; 1314 Matrix Block Sum; 238 Product of Array Except Self; 525 Contiguous Array; 974 Subarray Sums Divisible by K; 370 Range Addition†; 1109 Corporate Flight Bookings; 1094 Car Pooling; 2536 Increment Submatrices by One.

## 39f.5 The sliding-window framework

39d.6 solves the classic window problems one by one. This section gives the template behind all of them, the argument for why it works, and what to do when it does not. Framing the template as a few questions to answer comes from labuladong's notes; the answers by problem type and the correctness argument are added here.

### 39f.5.1 One template, three questions

```python
# illustration: the sliding-window skeleton; Q1-Q3 are the three questions
left = 0
for right, item in enumerate(seq):
    add item to the window state              # Q1: what changes when seq[right] enters?
    while the window must shrink:             # Q2: when must seq[left] leave?
        (record here for "shortest")          # Q3: where is the answer read?
        remove seq[left] from the window state
        left += 1
    (record here for "longest" or "count")
```

- **Q1, expanding:** what summary of the window do you keep (a sum, counts, the number of zeros, the number of letters still unmatched), and how does one arrival change it?
- **Q2, shrinking:** for "longest valid", shrink *while the window is invalid*; for "shortest valid", *while it is still valid*; for a fixed length, once whenever it outgrows the length.
- **Q3, recording:** for "longest", after the shrink loop; for "shortest", inside it, before each removal; for counting, add `right − left + 1` after it — the number of valid windows ending at `right`.

**Why it is correct.** It needs a monotone condition: for "longest", every window inside a valid window is valid. Then the valid left ends for a given `right` form a range ending at `right` (possibly empty, which leaves `left = right + 1` and an empty window), and its smallest member never decreases as `right` grows, because a window that was invalid stays invalid when extended. So `left` never moves back, and for each `right` the loop stops at exactly the smallest valid left end. The mirror argument covers "shortest". **Why it is linear.** Each index enters once and leaves at most once.

### 39f.5.2 How each problem answers the three questions

| Problem | Q1: window state | Q2: shrink when | Q3: record |
|---|---|---|---|
| 76 Minimum Window Substring (39d) | counts still missing | while every need is met | inside: shortest |
| 567 Permutation in String | each letter's balance against s1, and how many letters are unbalanced | once, when longer than s1 | after: no letter unbalanced |
| 3 Longest Substring Without Repeating Characters (39d) | last index of each letter | when the new letter was last seen inside the window: jump past that index | after: longest |
| 1004 Max Consecutive Ones III | number of zeros | while zeros > k | after: longest |
| 713 Subarray Product Less Than K | product | while product ≥ k | after: add `right − left + 1` |
| 1658 Minimum Operations to Reduce X to Zero | sum | while sum > total − x | after: longest with sum = total − x |

```python
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
```

In 567, `shift` removes a letter's old contribution to `unbalanced` and adds its new one, so the count changes only when a balance moves onto or off 0, and `unbalanced == 0` means the window holds exactly s1's letters with s1's counts: a permutation of s1. One counter serves both strings, so there is no second map to keep in step. In 1658, removing from both ends leaves a contiguous middle, so "fewest removals" becomes "longest middle run summing to `sum(nums) − x`": the reframing is the real step.

### 39f.5.3 When the condition is not monotone: change the question

**Exactly k = at most k − at most (k − 1).** "Exactly k distinct values" is not monotone (shrinking can drop to k − 1); "at most k" is (992).

**Add a constraint that restores monotonicity.** In 395 every letter must occur at least k times; adding a letter can repair or break a window, so neither direction is safe. Fix the number of distinct letters u: under "at most u distinct", the condition is monotone, and among those windows record the ones with exactly u letters, each occurring at least k times — one pass per u, O(26 · n). Nothing is missed: for an optimal substring T with u letters, when `right` reaches T's end the window is the longest one ending there with at most u letters, so it contains T, has exactly T's letters, and each count is at least T's.

```python
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
```

**When nothing helps.** With negative numbers, a condition on the window's sum is not monotone, and no added constraint repairs it: use prefix sums with a hash map (39d.23) or a monotonic deque over prefix sums (862, sketched in 39d.6).

### 39f.5.4 Rabin–Karp: sliding a window over hashes

Comparing each window with a pattern costs O(m), so a naive scan is O(n · m). Rabin–Karp keeps a hash of the window and updates it in O(1): read the window as a number in base b, `s[i]·b^(m−1) + … + s[i+m−1]` modulo a prime p; sliding subtracts the leading term, multiplies by b and adds the new character. With DNA's four letters, a 10-letter window fits exactly in 20 bits, so Repeated DNA Sequences (187) needs no modulus and has no collisions:

```python
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
```

With a general alphabet the hash is reduced modulo p and two windows can collide, so equal hashes are only candidates, confirmed by comparing the text (28):

```python
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
```

**Collisions.** For two different strings of length m, the difference of their hashes is a nonzero polynomial in b of degree at most m − 1, with at most m − 1 roots modulo p, so for a random base they collide with probability at most (m − 1)/p. False matches then cost less than n · m²/p comparisons in expectation, so with p above m² the expected time is O(n + m). With a fixed base, inputs can be built to collide, giving O(n · m) (the tests force collisions with `mod=3`; the verification keeps the answers right), so randomize the base against hostile inputs. Rabin–Karp earns its keep with many patterns of one length, repeated substrings, or hashing inside a binary search (1044 Longest Duplicate Substring); for one search in Python, use `str.find`.

**Practice set.** 567 Permutation in String; 1004 Max Consecutive Ones III; 713 Subarray Product Less Than K; 1658 Minimum Operations to Reduce X to Zero; 395 Longest Substring with At Least K Repeating Characters; 992 Subarrays with K Different Integers; 220 Contains Duplicate III; 187 Repeated DNA Sequences; 28 Find the Index of the First Occurrence in a String; 1044 Longest Duplicate Substring.

## 39f.6 Binary search as a framework

The cure for off-by-one errors is one convention for the search interval, one invariant, and every variant derived from them. 39d.14 uses the half-open convention and builds everything from a lower bound. This section uses the closed convention, which makes exact match, left bound and right bound three copies of one loop. Both are correct; never mix their pieces.

| | Closed `[lo, hi]` (here) | Half-open `[lo, hi)` (39d.14) |
|---|---|---|
| Start | `lo, hi = 0, len(nums) − 1` | `lo, hi = 0, len(nums)` |
| Loop while | `lo <= hi` | `lo < hi` |
| Updates | `lo = mid + 1` or `hi = mid − 1`: mid always leaves | `lo = mid + 1` or `hi = mid` |
| After the loop | `lo = hi + 1`, the insertion point (`len(nums)` if every value is smaller); test `lo < len(nums)` before reading `nums[lo]` | `lo = hi`, the same insertion point, with the same test |

### 39f.6.1 One interval, three searches

`[lo, hi]` holds every index still in play. Once `nums[mid]` is compared, mid is out of play, so both updates exclude it and the interval shrinks every iteration — the termination argument. `mid = lo + (hi − lo) // 2` avoids overflow in languages with fixed-size integers.

```python
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
```

**The invariants.** `left_bound` keeps `nums[:lo] < target <= nums[hi + 1:]`; both regions start empty and each update grows one of them. The loop ends with `lo = hi + 1`, where they meet, so `lo` is the first index with a value at least the target — `bisect_left`'s insertion point — and the answer if `nums[lo]` equals the target. `right_bound` keeps `nums[:lo] <= target < nums[hi + 1:]`, so `hi` ends on the last index with a value at most the target (`bisect_right − 1`). With the invariant written down, "first value greater than" or "last value smaller than" needs no new reasoning.

### 39f.6.2 Binary search on a monotone predicate

If a yes-or-no question `predicate(x)` is false for small x and true from some point on, the same loop finds the boundary: `first_true` is `left_bound` with the comparison replaced by the predicate.

In 1011 (Capacity To Ship Packages Within D Days), capacity C is feasible if loading each day greedily, in order, needs at most D days. Feasibility is monotone — a bigger ship never needs more days — so the answer is the first feasible capacity in `[max(weights), sum(weights)]`. Greedy loading is a valid test because it stays ahead: by induction on d, greedy's first d days ship at least as many packages as the first d days of any schedule that respects the capacity, so if some schedule finishes within D days, greedy does too. Split Array Largest Sum (410) is the same question: the smallest cap for which greedy packing needs at most k parts. "At most" suffices because values are non-negative, so a part can always be split further without raising the maximum.

```python
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
```

O(n log S) for S the total weight. The tests compare both with exhaustive search over every way to cut the array. **Recognize it:** a minimum maximum or a maximum minimum, a large numeric range, and an easy check once the answer is fixed — 875 Koko Eating Bananas, 1482 Minimum Number of Days to Make m Bouquets, 2187 Minimum Time to Complete Trips. Say the monotonicity out loud: it is the proof.

### 39f.6.3 Weighted random pick, and advantage shuffle

Random Pick with Weight (528) wants index i with probability `w[i] / sum(w)`. Think of tickets: index i owns the w[i] tickets ending at `prefix[i]`, the running total. Draw a ticket uniformly from 1 to the total; its owner is the first index whose running total reaches it — a left-bound search.

```python
class WeightedPicker:
    """Random Pick with Weight (LC 528): index i with probability w[i] / sum(w)."""

    def __init__(self, w, rng=random):
        self.prefix = list(accumulate(w))   # index i owns the tickets prefix[i - 1] + 1 .. prefix[i]
        self.rng = rng

    def pick_index(self):
        ticket = self.rng.randint(1, self.prefix[-1])
        return bisect_left(self.prefix, ticket)     # first index whose range reaches the ticket
```

O(n) to build, O(log n) per pick. The tests check ownership exactly (index i owns w[i] tickets), then the distribution over 30,000 seeded draws. **Pitfall.** Drawing tickets 0 to total − 1 with `bisect_left` gives index 0 one ticket too many and the last index one too few. **Follow-ups.** Changing weights: a Fenwick tree, O(log n) per update and pick. k picks without replacement: keep the k largest keys `u^(1/w)` (Efraimidis–Spirakis). 497 Random Point in Non-overlapping Rectangles weights by area.

Advantage Shuffle (870) rearranges `nums1` to beat `nums2` in as many positions as possible. Take your values from the smallest up, against their values from the smallest up. If your current value beats their smallest unbeaten value, pair them: in any optimal arrangement, moving your value into that position loses no win, because the value it displaces is at least as large and wins wherever yours did. If it does not, it beats nothing still unbeaten, so it becomes a spare for a position you cannot win.

```python
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
```

O(n log n). The tests compare the number of wins with the best over every permutation. The same exchange argument settles other pairings, such as 881 Boats to Save People.

**Practice set.** 704 Binary Search; 34 Find First and Last Position of Element in Sorted Array; 658 Find K Closest Elements; 875 Koko Eating Bananas; 1011 Capacity To Ship Packages Within D Days; 410 Split Array Largest Sum; 1482 Minimum Number of Days to Make m Bouquets; 1283 Find the Smallest Divisor Given a Threshold; 528 Random Pick with Weight; 870 Advantage Shuffle.

## 39f.7 Stacks and queues

### 39f.7.1 Building each from the other

A queue from two stacks (232): push onto an inbox; pop from an outbox, and when the outbox is empty, pour the whole inbox into it, reversing the order once. Each element is pushed, moved and popped once, so m operations cost O(m): amortized O(1), although one pop can cost O(n). Pouring into a non-empty outbox would let newer elements leave first. A stack from one queue (225): after each push, rotate the older elements behind the new one; push O(n), pop O(1).

```python
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
```

### 39f.7.2 The monotonic stack as one template

39d.21 codes next greater, next smaller, the circular version, daily temperatures, the histogram and trapping rain water separately. They are one template. Scan the array with a stack of indices still waiting for their answer; when a new element *beats* the top, it is the top's answer, so pop and record. No ordering rule is needed: an index stays only because nothing after it has beaten it, which keeps the stack monotone by itself. Scanning right to left turns "next" into "previous", and the relation picks greater, greater-or-equal, smaller or smaller-or-equal: eight variants in one function.

```python
def nearest_index(nums, beats, reverse=False):
    """Nearest index to the right (left if reverse) whose value beats nums[i], else -1. O(n)."""
    out = [-1] * len(nums)
    waiting = []
    for i in (range(len(nums) - 1, -1, -1) if reverse else range(len(nums))):
        while waiting and beats(nums[i], nums[waiting[-1]]):
            out[waiting.pop()] = i          # i is the first to beat it from that side
        waiting.append(i)
    return out
```

Each index is pushed once and popped at most once: O(n). Two extras: after the pops, the index left on top is the previous element the current one does *not* beat, which gives "previous" answers in the same pass; and for circular arrays, scan 2n positions and push only in the first n (39d.21).

Strictness matters when counting. Sum of Subarray Minimums (907) adds each value times the number of subarrays where it is the minimum; with equal values, a subarray has several minimums and must be credited to one. Bound each element by the previous *strictly* smaller value on the left and the next smaller *or equal* value on the right: an equal value to its left stays inside its range and an equal value to its right ends it, so each subarray is credited once, to the rightmost of its minimums. In `[2, 2]`, the whole array counts for the second 2, not the first.

```python
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
```

The same pair of passes gives 2104 Sum of Subarray Ranges and the boundaries in 84 Largest Rectangle in Histogram.

### 39f.7.3 The monotonic queue

A sliding window needs a FIFO queue and often the window's maximum or minimum. A heap costs O(log n) per operation and needs lazy deletion; a deque of candidates costs amortized O(1). The candidates for the maximum are the items with nothing at least as large behind them. An arrival evicts every candidate no larger than itself from the back: those items leave before it and never exceed it, so while they remain, it outranks them. The candidates therefore strictly decrease from front to back, and the front one is the maximum. Each item also carries its arrival number, and a candidate leaves the front when the item with its number departs; matching by number rather than by value means equal values need no special care. The minimum is the mirror image.

```python
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
```

Every value enters and leaves each deque at most once. 39d.21's `max_sliding_window` uses the same idea for a fixed-size window over an array, with array indices as the arrival numbers (the lab's `max_sliding_window_queue` is 239 with this class). 1438 needs both ends: it is the 39f.5 template with this queue as the window state, valid while max − min ≤ limit. The queue also speeds up dynamic programs that take the maximum over the last k states (1696 Jump Game VI).

### 39f.7.4 Remove duplicate letters

Remove Duplicate Letters (316, the same as 1081) keeps one copy of each letter and wants the lexicographically smallest result. Build it on a stack, knowing each letter's last index: when a smaller letter arrives and the top letter occurs again later, pop the top — a later copy can take its place, and the smaller letter moves forward. If the top never occurs again, it must stay. A letter already on the stack is skipped, because the letter directly above it is larger: when that letter was pushed, this one was on top with a copy still to come, so a smaller arrival would have popped it. Dropping the earlier copy would therefore move a larger letter into its place. (The letters further up need not be larger: in "bcab", the a above b sits on c, which never recurs.)

```python
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
```

O(n) time, O(alphabet) space. The tests compare with the minimum over all subsequences that keep each letter once. 402 Remove K Digits is the same greedy with a budget of k pops.

**Practice set.** 232 Implement Queue using Stacks; 225 Implement Stack using Queues; 155 Min Stack; 907 Sum of Subarray Minimums; 2104 Sum of Subarray Ranges; 456 132 Pattern; 1944 Number of Visible People in a Queue; 239 Sliding Window Maximum; 1438 Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit; 1696 Jump Game VI; 316 Remove Duplicate Letters; 402 Remove K Digits.

## 39f.8 Binary trees in action

Tree problems come in four kinds, and naming the kind is half the solution: *traversal* (act at every node), *construction* (find the root, split the rest, recurse), *postorder* (each node needs facts about its subtrees) and *serialization*. 39d.10 and 39d.11 cover level order, paths and heights.

### 39f.8.1 Traversal problems: invert, connect, flatten

Inverting a tree (226) swaps the children of every node, at the preorder position (postorder also works; 39d.22's `invert_tree` is the decomposition version). The inorder position fails: after the swap, the walk enters the new right child — the subtree it just inverted — so one subtree is inverted twice and the other never.

```python
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
```

Populating next pointers in a perfect tree (116) needs a link that crosses between two parents, from a right child to the neighbor's left child. In preorder, a node's own `next` is already set by its parent when the node is visited, and through it the node reaches its neighbor's left child.

```python
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
```

O(n) time, O(log n) stack. A widely shared alternative recurses on *pairs* of adjacent nodes, linking the pair and then recursing on three pairs of their children (each node's two children, and the right child of the first with the left child of the second). It is correct but not linear. Every call makes three more, so the calls triple per level while the adjacent pairs only double: a sibling pair is reached once through each pair its parent belongs to, and the repeats compound further down. A perfect tree with h levels gets (3^h − 1)/2 calls, counting those that stop on empty children — 265,720 for the 4,095 nodes of 12 levels (the tests count them) — which is Θ(n^(log₂ 3)) ≈ n^1.58. The O(1)-space version walks each level along the `next` links already built (and, for 117, keeps a dummy head for the next level).

Flattening into a right-leaning chain in preorder (114) is decomposition: `flat(node)` flattens the subtree and returns its *last* node, and at the postorder position the node splices its flat left part between itself and its flat right part. Returning the tail makes it O(n); walking to find the tail is O(n²) on a left-leaning tree.

```python
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
```

### 39f.8.2 Construction: find the root, split, recurse

A rule picks the root and splits the remaining values into left and right parts, and recursion builds each part. In the Maximum Binary Tree (654), the maximum is the root and the elements on either side of it form the subtrees.

```python
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
```

The recursive version is O(n²) on sorted input. The stack version is O(n): a node's parent is the *smaller* of its nearest greater neighbors on the left and right, which a decreasing stack exposes — the popped run hangs on the new node's left, and the new node hangs on the right of the larger value left on the stack.

From preorder and inorder with distinct values (105), the first preorder value is the root, its inorder position splits the inorder list, and the left part's size k splits the preorder list; from inorder and postorder (106) the root is the *last* postorder value. Passing a start in each list and a size, instead of four bounds, leaves fewer numbers to keep consistent, and a dictionary from value to inorder index makes the build O(n).

```python
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
```

From preorder and postorder (889) the tree is not unique: preorder `[1, 2]` and postorder `[2, 1]` fit 2 as either child of 1, because the lists never reveal the side of a *lone* child. Picking a side always gives a valid answer: treat the value after the root in preorder as the root of the left subtree, and its position in postorder gives that subtree's size. The answer is unique exactly when every node has zero or two children.

```python
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
```

### 39f.8.3 Postorder problems: find duplicate subtrees

Find Duplicate Subtrees (652) wants one root per subtree that occurs more than once. A node can describe its subtree only after both children have: postorder. Building a string per subtree costs O(n²) in the worst case; giving each distinct (left id, value, right id) triple a small integer id makes each key O(1), so the whole pass is O(n).

```python
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
```

### 39f.8.4 Serialization and deserialization

A sequence can rebuild a tree if it records the empty children (297). In **preorder with null markers**, each node writes its value and then its two subtrees, and an empty subtree writes `#` (n values and n + 1 markers); deserializing reads the tokens in the same order with the same recursion. LeetCode's own **level-order** format (BFS order with markers, trailing markers dropped) is `serialize_level` and `deserialize_level` in the lab.

```python
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
```

Postorder with markers also works (read from the end: root, right, left). Inorder with markers does not: a root 1 with left child 2, and a root 2 with right child 1, both write `#,2,#,1,#`. For a BST (449 Serialize and Deserialize BST), plain preorder suffices, because the values show where each subtree ends (1008 Construct Binary Search Tree from Preorder Traversal).

### 39f.8.5 Iterative traversal with an explicit stack

Recursion is a stack the interpreter manages; managing it yourself avoids the recursion limit. This version keeps one frame per node on the current path with a *stage*: 0 just entered, 1 left subtree done, 2 both done. Each stage is one of the three positions of 39f.1.3, so code from any position of a recursive solution moves into the matching branch unchanged.

```python
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
```

O(n) time, O(h) space. The usual shortcuts (push right then left for preorder, run down the left spine for inorder) give one order each; the staged frame gives all three positions, which a postorder computation needs.

**Practice set.** 144, 94 and 145 (the three traversals, recursively and with a stack); 226 Invert Binary Tree; 116 and 117 Populating Next Right Pointers in Each Node I and II; 114 Flatten Binary Tree to Linked List; 654 Maximum Binary Tree; 105 and 106 (construction from two traversals); 889 Construct Binary Tree from Preorder and Postorder Traversal; 652 Find Duplicate Subtrees; 297 Serialize and Deserialize Binary Tree; 449 Serialize and Deserialize BST; 331 Verify Preorder Serialization of a Binary Tree.

## 39f.9 Binary search trees

Two facts carry most BST questions: an **inorder walk visits the values in sorted order**, and **each comparison discards a whole subtree**, so search, insertion and deletion cost O(h) — O(log n) when balanced, O(n) for a chain.

### 39f.9.1 Inorder is sorted

The kth smallest value (230) is the kth node of an inorder walk, and an iterator that keeps the path to the next smallest value on a stack (173 Binary Search Tree Iterator) makes stopping early easy: each node is pushed and popped once, so k calls cost O(h + k). The greater-sum tree (538, the same as 1038) walks from largest to smallest — *reverse* inorder — with a running total.

```python
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
```

**Follow-up.** "Frequent kth queries on a changing tree": store subtree sizes and descend by comparing k with the left size, O(h) per query — an order-statistics tree.

### 39f.9.2 Validate and delete

Validating (98) by comparing each node with its children is the classic wrong answer: in `[8, 3, 10, 1, 9]` every parent–child pair is ordered (1 < 3 < 9 under 3, and 3 < 8 < 10 at the root), but 9 sits in 8's left subtree. Each node must fit an *interval* inherited from all its ancestors — information flowing down, at the preorder position. Search (700) and insertion (701) walk down by comparison (`search_bst` and `insert_into_bst` in the lab). Deletion (450) has three cases: a leaf disappears, a node with one child is replaced by that child, and a node with two children is replaced by its *successor*, the smallest node of its right subtree. The successor has no left child, so unhooking it takes one assignment — its right subtree moves up into its place — and a single walk down finds both the successor and its parent.

```python
def is_valid_bst(root):
    """Strict BST check (LC 98): pass down the open interval that each subtree's values must lie in."""
    def fits(node, low, high):
        if node is None:
            return True
        if not low < node.val < high:
            return False
        return fits(node.left, low, node.val) and fits(node.right, node.val, high)

    return fits(root, float("-inf"), float("inf"))


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
```

O(h) each. When the successor is `root.right` itself, it keeps its right subtree and only gains `root.left`. The code relinks the successor node instead of copying its key into `root`, so every surviving key stays in the node object it started in, and references to nodes held elsewhere (an iterator's stack, a map from keys to nodes) stay valid. **Pitfalls.** `<=` where values are strictly ordered (or the reverse); not returning the possibly new root from insert and delete.

### 39f.9.3 Counting and generating BSTs; maximum sum BST

How many BSTs hold 1..n (96)? Choose root r: r − 1 values form the left subtree and n − r the right, and the choices multiply. The count depends only on how many values, so a one-argument memo suffices: `G(n) = Σ G(i) · G(n − 1 − i)` over i from 0 to n − 1, with `G(0) = G(1) = 1` — the Catalan numbers, O(n²). Generating them (95) is the same recursion returning lists of trees; with the memo, results share subtrees, which LeetCode accepts.

```python
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
```

There are Catalan(n) ≈ 4ⁿ / (n^1.5 · √π) trees, so generation is exponential however it is done.

Maximum Sum BST in Binary Tree (1373) asks for the largest sum among subtrees that are BSTs. Validating each subtree from scratch is O(n²). Instead, each subtree reports a summary at the postorder position: `None` if it is not a BST, otherwise its smallest key, its largest key and its sum. A node is the root of a BST exactly when both children are, and its key lies above the left side's largest and below the right side's smallest. The empty subtree reports (+∞, −∞, 0), which passes both comparisons, so leaves and one-child nodes need no special case.

```python
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
```

O(n) time. The answer is at least 0 because the empty tree counts. The tests compare with a brute force that validates every subtree.

**Practice set.** 230 Kth Smallest Element in a BST; 173 Binary Search Tree Iterator; 538 Convert BST to Greater Tree; 98 Validate Binary Search Tree; 701 Insert into a Binary Search Tree; 450 Delete Node in a BST; 96 and 95 Unique Binary Search Trees I and II; 1373 Maximum Sum BST in Binary Tree; 501 Find Mode in Binary Search Tree; 99 Recover Binary Search Tree.

## 39f.10 Lowest common ancestor in all its forms

The lowest common ancestor (LCA) of two nodes is the deepest node with both in its subtree (a node counts as its own descendant). Every variant rests on one search, 39d.11's `lowest_common_ancestor` for 236, whose promise is: *return None if this subtree holds neither target, the target if it holds one, and their LCA if it holds both*. A node that is itself a target returns itself without searching below. Otherwise, at the postorder position, if both children found something, the targets are on different sides and this node is the LCA; if only one did, it passes that result up.

Why may the search stop at p without looking below it? If q is below p, the answer is p, which is what gets returned; if q is elsewhere, some ancestor receives p from one side and q from the other. Nothing below p changes the answer — *provided both nodes exist*. The variants play with that proviso.

| Problem | What changes | Fix |
|---|---|---|
| 236 Lowest Common Ancestor of a Binary Tree (39d.11) | nothing | the base search |
| 1644 Lowest Common Ancestor of a Binary Tree II† | p or q may be missing | search everything, count the targets, answer only if both were found |
| 1676 Lowest Common Ancestor of a Binary Tree IV† | a list of targets | the base search with a set |
| 1650 Lowest Common Ancestor of a Binary Tree III† | parent pointers, no root | the paths to the root are merging lists: 160's switch |
| 235 Lowest Common Ancestor of a Binary Search Tree | a BST | walk down while both values are on one side, O(h) |
| 1123 Lowest Common Ancestor of Deepest Leaves (same as 865) | the deepest leaves | return (height, LCA) from each subtree |

```python
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
```

In 1644 the target check moves *after* the recursive calls, so a missing target is noticed. In 235 the first node whose value lies between the two is where the paths split. In 1123, equal heights on both sides mean the deepest leaves lie on both sides and the node joins them; otherwise the answer comes from the taller side. All are O(n) time and O(h) stack, except the BST walk and the parent-pointer version, which are O(h); the tests compare each with a brute force that intersects root-to-node paths. **Follow-ups.** Many queries on a static tree: binary lifting (each node's 2^i-th ancestors) answers each in O(log n) after O(n log n) preprocessing. Distance between nodes: `depth(p) + depth(q) − 2 · depth(lca)`.

## 39f.11 Tree follow-ups

### 39f.11.1 Count the nodes of a complete tree in O(log² n)

In a complete tree (222), if a subtree's leftmost and rightmost paths have the same length h, the subtree is *perfect* and has `2^h − 1` nodes, with no need to look inside.

```python
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
```

**Why O(log² n).** Of a complete tree's two subtrees, at least one is perfect: if the last level ends in the left half, the right subtree is perfect (one level shorter); otherwise the left one is. The perfect one returns after measuring its paths, so the recursion continues into one subtree per level: O(log n) levels, each paying O(log n) to measure.

### 39f.11.2 Lazy flattening of a nested list

Flatten Nested List Iterator (341) can flatten everything in the constructor, but that holds every integer in memory and does work that may never be used. The lazy version treats the nested list as an n-ary tree and keeps a stack of iterators, one per open list: `has_next` advances the top iterator, pops exhausted lists and opens nested ones. (`NestedInteger` in the lab is a minimal stand-in for LeetCode's interface.)

```python
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
```

Memory is O(depth), a full iteration O(total size). `has_next` must be idempotent — calling it twice must not skip an element — hence `ready`; and it must skip empty lists, hence the loop. A stack of child iterators is a paused depth-first search, so the same design gives a lazy iterator over any tree.

### 39f.11.3 Merge sort as postorder: counting while merging

Merge sort works at the postorder position: sort both halves, then merge (39e.12.5 builds the sort). At the merge, both halves are sorted *and* every left element preceded every right element in the original order. So a question about pairs i < j splits into pairs inside each half (counted by the recursion) and *cross* pairs, which two forward-only pointers count in linear time because both halves are sorted.

- **315 Count of Smaller Numbers After Self:** sort indices by value; when a left-half index is placed, the right-half indices placed before it are exactly the later, smaller elements.
- **493 Reverse Pairs** (`nums[i] > 2 · nums[j]`): before merging, advance a pointer over the right half for each left value; the condition differs from the merge order, so the count is a separate pass.
- **327 Count of Range Sum:** a range sum is `prefix[j] − prefix[i]` with i < j; for each left prefix p, the right prefixes in `[p + lower, p + upper]` form a window whose two edges only move right.

```python
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
```

All O(n log n) (`merge_sorted` is the ordinary two-way merge). A Fenwick tree over compressed values solves them too; the merge-sort version needs no compression and shows the divide-and-conquer pattern, which is usually what is being tested.

### 39f.11.4 Quickselect: quicksort as preorder with one branch

Quicksort (39e.12.4) partitions at the preorder position and recurses into both sides; quickselect recurses only into the side that holds the wanted position — `len − k` in ascending order for the kth largest (215). A random pivot lands in the middle half of the values with probability one half, and such a pivot removes at least a quarter of the range, so on average every two rounds shrink the range to three quarters: expected work at most 2(n + 3n/4 + (3/4)²n + …) = 8n. A three-way partition keeps many equal values from making it quadratic.

```python
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
```

The worst case is O(n²), vanishingly unlikely with random pivots; median of medians makes it O(n) at a large constant (name it, do not write it). 39d.15's heap is O(n log k) and works on streams.

**Practice set.** 222 Count Complete Tree Nodes; 341 Flatten Nested List Iterator; 912 Sort an Array; 315 Count of Smaller Numbers After Self; 493 Reverse Pairs; 327 Count of Range Sum; 215 Kth Largest Element in an Array; 973 K Closest Points to Origin.

## 39f.12 Designing data structures

List the operations and their required costs, pick the structure that gives each cost (a hash map for lookup, a doubly linked list for O(1) removal from the middle, an array for random access, a heap for "the best one"), and link them — usually by a map from a key to a node or position — stating the invariants every operation restores.

### 39f.12.1 LRU and LFU caches

An LRU cache (146) needs O(1) lookup (a hash map) and O(1) "move to the most-recent end" and "evict the oldest" (a doubly linked list, whose nodes can unlink themselves). The map points at nodes, and each node stores its key so that evicting the oldest node can delete its map entry. 39d.23 prints the `OrderedDict` version — this very design inside the standard library; when the interviewer says "without `OrderedDict`", this is the answer:

```python
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
```

`_Link` is a node with `key`, `value`, `prev` and `next` slots. Two sentinels keep the list non-empty, so `_unlink` and `_append` have no special cases. All O(1).

An LFU cache (460) evicts the least frequently used key, the least recently used among ties. `entries` maps a key to its value and frequency; `buckets` maps a frequency to its keys in recency order (an `OrderedDict`: oldest first, any key removable in O(1)); `min_freq` names the bucket to evict from. Keeping `min_freq` exact without scanning is the subtle part: a hit moves a key from bucket f to f + 1, so the minimum changes only if bucket f was the minimum and is now empty — and then it is f + 1, where the moved key went. A new key has frequency 1, so insertion sets `min_freq = 1`; eviction happens just before, while `min_freq` is still right.

```python
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
```

All O(1); the tests run both caches against brute-force references.

### 39f.12.2 Random access with O(1) deletion

Insert Delete GetRandom O(1) (380) needs an array for uniform sampling, and an array deletes in O(1) only if order does not matter: move the last element into the hole and pop the end, with a map from value to index. The multiset version (381) maps each value to a *set* of positions; when the removed value and the moved one are equal, discard the old last position and add the hole to the same set.

```python
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
```

In 381, values come up in proportion to their counts, which the tests check with seeded draws.

Random Pick with Blacklist (710) wants a uniform pick from `[0, n)` minus a blacklist, with one random call. Draw from `[0, size)`, `size = n − len(blacklist)`, and remap each blacklisted number below `size`, once, to an allowed number in `[size, n)`. The counts match: the top range holds `len(blacklist)` numbers, and its blacklisted ones are exactly those *not* below `size`.

```python
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
```

O(B) to build, O(1) per pick, memory independent of n (up to 10⁹).

### 39f.12.3 Exam room

In Exam Room (855), `seat()` takes the seat farthest from everyone (lowest number on ties) and `leave(p)` frees seat p. Think in *stretches* of empty seats between neighbors, with walls at −1 and n: stretch (a, b) offers seat `(a + b) // 2` at distance `(b − a) // 2`, or seat 0 at distance b against the left wall, or seat n − 1 at distance `n − 1 − a` against the right. Keep stretches in a heap keyed by `(−distance, seat)`; `seat()` splits one, `leave()` merges two. Old stretches stay in the heap and are discarded when popped if they no longer match the current neighbors — lazy deletion.

```python
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
```

O(log m) amortized per call after m calls; a sorted list scanned in O(n) per call is a fine first answer. The tests compare with a brute force over every free seat.

### 39f.12.4 A calculator by recursive descent

Basic Calculator (224: `+`, `-`, parentheses and unary minus), II (227: `+ - * /` without parentheses) and III (772†: the four operators and parentheses) are one problem. Write one grammar rule per precedence level — an *expression* is terms joined by `+` or `-`, a *term* is factors joined by `*` or `/`, a *factor* is a number, a parenthesized expression or a signed factor — and one function per rule. Precedence comes from the nesting, left-to-right order from the loops (`8 - 3 - 2` is `(8 - 3) - 2`; a right-recursive rule would compute `8 - (3 - 2)`), and unary minus binds tightest because it lives in the factor rule.

```python
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
```

LeetCode's division truncates toward zero, but Python's `//` floors (`−7 // 2` is −4, not −3), so the code divides absolute values and fixes the sign. O(n) time. The tests compare 600 random expressions with Python's own parser (`ast`, same precedence, truncating division substituted). For 227 alone a stack of signed terms suffices; recursive descent extends, since a new operator is a new rule.

### 39f.12.5 Consistent hashing

`hash(key) % N` reshuffles almost everything when N changes: going from 10 to 11 servers moves about 10/11 of the keys. Consistent hashing puts servers and keys on one circle of hash values; a key belongs to the first server point at or after it, clockwise. A new server takes only the keys on the arcs just before its points, and a removed one hands its arcs to the next points. Placing each server at many points (*virtual nodes*) evens out the arcs.

```python
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
```

The hash must be stable across processes — Python's `hash` for strings is salted per process (`PYTHONHASHSEED`) — so the ring uses `hashlib`. Lookups are O(log P) for P points. The figures that follow are measured and asserted by `t_consistent_hashing` in the tests, and they are exact, because BLAKE2b and the names (`user:0` to `user:19999` for the keys, `server-0` onward for the servers) are fixed. With 20,000 keys on 10 servers of 100 virtual nodes each, adding an 11th server moved 10.9% of the keys (the ideal is 1/11 ≈ 9.1%), all of them to the new server, while `hash % N` going from 10 to 11 would move 91.1%. On the 10-server ring the busiest server held 1.20 times the mean load, against 2.52 when each server has a single point. Replicas go on the next R distinct servers clockwise, as in Amazon's Dynamo.

### 39f.12.6 Segment trees

A segment tree answers range queries for any associative operation, with updates, in O(log n) each. Its leaves are the array, and each internal node summarizes its two children. An update changes one leaf and its ancestors; a query covers `[l, r]` with at most two *canonical* nodes per level. Below, node i has children 2i and 2i + 1 and the leaves start at `size`; the query climbs from both ends, taking an edge node whenever its parent would reach outside the range. Separate left and right accumulators keep the order, so non-commutative operations work too (the tests use string concatenation).

```python
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
```

Two extensions. **Dynamic nodes** for ranges such as 0..10⁹: create a node (`_SegNode`, with `left`, `right`, `total`, `best` and `pending` slots) only when an operation first reaches it, O(log R) new nodes per call. **Lazy propagation** for range updates: stop at the canonical nodes, update their summaries (sum grows by v times the length, maximum by v), and leave a *pending* note that moves to the children only when an operation must descend. Both keep each operation at O(log R), and `RangeAddTree` below uses both.

```python
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
```

My Calendar III (732, `MyCalendarThree` in the lab) adds 1 on `[start, end − 1]` over a range of 10⁹ and reads the maximum overlap at the root. The tests compare with direct computation from the list of updates. **Lighter tools:** a Fenwick tree for prefix sums with point updates; a sparse table for static range minimum; a difference array when all updates precede the reads.

### 39f.12.7 Trie applications

39d.23 builds the basic trie (208). **Replace Words (648)** stores each root at its end node and walks each word until the first end node — the shortest root. **Design Add and Search Words Data Structure (211)** branches into every child at a `.`: a depth-first search whose cost grows with the number of dots. **Map Sum Pairs (677)** stores at each node the total of the values below it, so `sum(prefix)` is one walk; re-inserting a key adds only the *difference* along its path.

```python
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
```

**Practice set.** 146 LRU Cache; 460 LFU Cache; 380 Insert Delete GetRandom O(1); 381 Insert Delete GetRandom O(1) - Duplicates allowed; 710 Random Pick with Blacklist; 855 Exam Room; 224 Basic Calculator; 772 Basic Calculator III†; 307 Range Sum Query - Mutable; 732 My Calendar III; 715 Range Module; 648 Replace Words; 211 Design Add and Search Words Data Structure; 677 Map Sum Pairs; 895 Maximum Frequency Stack.

## 39f.13 Graph algorithms

Graph traversal is tree traversal plus a record of what has been visited. 39d covers grid search (39d.4), Kahn's algorithm (39d.19), union-find and Dijkstra (39d.23); this section adds the algorithms around them, each with the property that makes it correct.

### 39f.13.1 Bipartite graphs

A graph is bipartite (785) if its nodes split into two sides with every edge crossing — equivalently, if it has no odd cycle. Color a start node 0 and spread by BFS, giving each newly reached node the opposite color. A node's color is the parity of its BFS distance from the start, so an edge between two nodes of the same color proves an odd cycle: the two BFS paths to its ends plus the edge form a closed walk of odd length, and every closed walk of odd length contains an odd cycle. If no such edge appears, the coloring is the split. A disconnected graph needs a fresh start in every component.

```python
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
```

O(V + E). Possible Bipartition (886) is the same check on a graph built from the "dislike" pairs, with people numbered from 1 (`possible_bipartition` in the lab).

### 39f.13.2 Cycles and topological order in directed graphs

In a directed graph, reaching an already visited node does not mean a cycle: an edge into a *finished* node is harmless (u → v, u → w, v → x, w → x has none). DFS tracks three states — new, **on the current path**, finished — and a cycle exists exactly when an edge reaches a node still on the path (a *back edge*). The path is the DFS stack, so the cycle can be read off through parent links.

```python
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
```

O(V + E); the explicit stack of `(node, iterator)` pairs avoids the recursion limit. Topological order comes from the same DFS: record each node at its **postorder** position and reverse the list. For an edge u → v, v finishes before u: if v was new, its whole visit happens inside u's; if finished, it finished earlier; it cannot be on the path, or there would be a cycle.

```python
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
```

| | Kahn (39d.19) | DFS postorder |
|---|---|---|
| Idea | repeatedly remove a node with no incoming edges | reverse the finishing order |
| Cycle shows up as | fewer than V nodes output | an edge to a node on the path |
| Extras | a unique order iff the queue never holds two; a heap gives the smallest order; levels count rounds | reports the cycle itself; extends to strongly connected components (Tarjan, Kosaraju) |

### 39f.13.3 Union-find applications

39d.23 gives union-find over integers (and 684 Redundant Connection). This version takes any hashable items, created on first use, which suits letters and grid cells; with path compression and union by size, m operations cost O(m α(n)), α being the inverse Ackermann function.

```python
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
```

In **Surrounded Regions (130)** an `O` survives exactly when it connects to a border `O`: join every border `O` to one extra item, `"safe"`, join neighboring `O` cells (down and right cover each edge once), and capture the rest. A virtual node for "the outside" is a reusable trick. In **Satisfiability of Equality Equations (990)**, equality is transitive, so apply every `==` before checking any `!=`; in the given order, an equality arriving after the inequality it contradicts would be missed.

### 39f.13.4 Dijkstra with restrictions

39d.23's Dijkstra (743) is correct because **extending a path never makes it better**: the best unsettled candidate cannot be improved through other unsettled nodes, which are no better and only get worse, so a node's value is final when it is first popped. Negative weights break the property. The path value need not be a sum:

- **1514 Path with Maximum Probability:** the product of probabilities, each at most 1, so extending never increases it. Use a max-heap.
- **1631 Path With Minimum Effort:** the *largest* step on the path — `max` in place of `+` keeps the property. 778 Swim in Rising Water is the same bottleneck problem.
- **787 Cheapest Flights Within K Stops:** cost is a sum, but at most k + 1 flights are allowed. A cheaper arrival that used more flights does not dominate a dearer one that used fewer, so the state is (city, flights used). A popped state is skipped when the same city was already expanded with no more flights (popped earlier, so no dearer). The flight counts of a city's expansions therefore strictly decrease, and only counts 0 to k can be expanded, so each city is expanded at most k + 1 times.

```python
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
```

O(E log E) for the first two; O(K · E log(K · E)) for 787. **Alternatives.** For 787, Bellman–Ford limited to k + 1 rounds, each relaxing from a *copy* of the previous round (without it one round chains several flights), O(K · E) — the tests' reference. For 1631, binary search on the effort with BFS. **Pitfall.** In 787, a plain visited set over cities discards the fewer-flights route a later state needed.

**Interview line:** *"Dijkstra needs one property: extending a path never makes it better. Products of probabilities and path maxima have it; negative weights and hop limits do not, so for those I change the algorithm or the state."*

### 39f.13.5 A* search

Dijkstra expands nodes in order of their distance g from the start, in every direction. A* expands them in order of `f = g + h`, h being an *estimate* of the remaining distance, so the search leans toward the goal. A heuristic is **admissible** if it never overestimates; then the goal's distance is optimal when the goal is popped (if nodes may be reopened). It is **consistent** if `h(u) ≤ w(u, v) + h(v)` on every edge and 0 at the goal; then the reduced weights `w − h(u) + h(v)` are non-negative, A* is Dijkstra on them, and each node is expanded once, with its final distance. Manhattan distance is consistent on a 4-connected grid with unit steps, since one step changes it by exactly 1. Ties in f go to the smaller h, toward the goal.

```python
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
```

On 300 random grids the tests check that A* returns BFS's length and never expands more cells. That holds for any consistent heuristic that is 0 only at the goal: A* expands only cells with `f ≤ C*` (C* the optimal length), which have `g < C*` except the goal itself, and BFS expands every cell with `g < C*` first. The tests also measure, from corner to corner of a 40 × 40 grid, how many cells each search expands, up to and including the goal: on an open grid, A* 79 (exactly the cells of one shortest path) and BFS all 1,600; with a wall across row 20 from column 5 to the right edge, leaving a gap of five cells on the left, A* 779 and BFS 1,565. A* still wins, but a wall that the heuristic cannot see costs it ten times the work. 1091 Shortest Path in Binary Matrix moves in 8 directions: use the Chebyshev distance `max(|dr|, |dc|)`.

### 39f.13.6 Minimum spanning trees: Kruskal and Prim

A minimum spanning tree connects all V nodes with V − 1 edges of least total weight. Both classic algorithms rest on the **cut property**: take the edges chosen so far, which lie in some minimum spanning tree, and any split of the nodes into two groups that none of them crosses; after adding a lightest edge e across the split, the chosen edges still lie in some minimum spanning tree. (Exchange: if that tree T lacks e, adding e to T closes a cycle, which must cross the split again through some edge f. Since e is a lightest crossing edge, f is no lighter than e, and f was not chosen, because no chosen edge crosses the split; swapping f for e gives a spanning tree no heavier than T that holds every chosen edge and e.) **Kruskal** sorts the edges and takes each one that joins two components — the lightest edge across the split between one of those components and the rest. **Prim** grows one tree, always adding the lightest edge leaving it; the lazy version skips popped edges that lead back into the tree.

```python
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
```

Both are O(E log E). Min Cost to Connect All Points (1584) is the tree of the complete graph under Manhattan distance, with E = n(n − 1)/2 edges; there the array version of Prim, which scans a plain array of the cheapest known edge into each outside point instead of keeping a heap, is O(n²) and best (`min_cost_connect_points` in the lab). The tests compare Kruskal and Prim with brute force over every set of V − 1 edges, and `min_cost_connect_points` with the heap version. **Follow-ups.** 1489 Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree: rerun Kruskal without each edge and with it forced. 1168 Optimize Water Distribution in a Village†: a virtual node joined to every house at the price of its well.

### 39f.13.7 Eulerian paths with Hierholzer's algorithm

An Eulerian path uses every *edge* once. In a directed graph it exists exactly when the edges form one connected piece and every node has equal in- and out-degree, except possibly a start with one extra outgoing edge and an end with one extra incoming edge (undirected: zero or two odd-degree nodes). Hierholzer finds one in O(E): walk unused edges until stuck — only possible at the end, or back where a closed detour began — and emit each node when its edges run out. Reversed, the emission order is the path, with each later detour spliced in where it began.

```python
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
```

For the lexicographically smallest itinerary (332), taking the smallest destination first is enough: if that choice leads to the true dead end, the branch is emitted first and lands *last* after reversal, where a dead end belongs. The tests compare with brute-force backtracking. 2097 is the general directed version, starting where out-degree exceeds in-degree; 753 Cracking the Safe is an Eulerian circuit on a de Bruijn graph.

### 39f.13.8 Floyd–Warshall: all pairs at once

After round k, `dist[i][j]` is the shortest path from i to j whose intermediate nodes all lie in 0..k; round k + 1 either avoids node k + 1 or passes through it once (`dist[i][k+1] + dist[k+1][j]`). That is the whole algorithm, and it is why k must be the outer loop.

```python
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
```

O(V³) time, O(V²) space; negative edges are fine, and a negative `dist[i][i]` reveals a negative cycle. In 1334, scanning with `<=` lets the largest index win ties, as asked. With non-negative weights on a sparse graph, V runs of Dijkstra (O(V · E log V)) are faster; Floyd–Warshall wins on dense graphs and simplicity. With Boolean or/and it computes reachability (1462 Course Schedule IV).

**Practice set.** 785 Is Graph Bipartite?; 886 Possible Bipartition; 802 Find Eventual Safe States; 130 Surrounded Regions; 990 Satisfiability of Equality Equations; 399 Evaluate Division; 1514 Path with Maximum Probability; 1631 Path With Minimum Effort; 778 Swim in Rising Water; 787 Cheapest Flights Within K Stops; 1091 Shortest Path in Binary Matrix; 1584 Min Cost to Connect All Points; 1135 Connecting Cities With Minimum Cost†; 332 Reconstruct Itinerary; 2097 Valid Arrangement of Pairs; 1334 Find the City With the Smallest Number of Neighbors at a Threshold Distance.

## 39f.14 Practice sets, a two-week plan, and interview questions

### 39f.14.1 A two-week plan

Each practice set above runs from the template problem to its variations. Time them (15, 25 and 40 minutes for easy, medium and hard), talk out loud, solve at least half without running code, and log the invariant you got wrong. The plan assumes about two hours a day and 39d's templates (if not, start with 39d.25's plan).

| Day | Topic | Problems |
|---|---|---|
| 1 | Traversal versus decomposition | 1448, 872, 104 (each both ways); 144, 94, 145 (recursively and with a stack); 543, 70 |
| 2 | Linked lists | 21, 86, 23, 19, 160, 82, 92 recursively, 25, 234 |
| 3 | Arrays and nSum | 80, 283, 189, 5, 48, 54, 59, 18 |
| 4 | Prefix sums and differences | 303, 304, 1314, 525, 1109, 1094 |
| 5 | Sliding window | 567, 1004, 713, 1658, 395, 992, 187 |
| 6 | Binary search | 34 in both conventions, 1011, 410, 875, 528, 870 |
| 7 | Review: redo every miss without notes | the error log |
| 8 | Stacks and queues | 232, 225, 907, 239, 1438, 316 |
| 9 | Binary trees | 226, 116, 114, 654, 105, 889, 652, 297 |
| 10 | BSTs and LCA | 230, 98, 450, 96, 1373, 236, 235, 1123 |
| 11 | Tree follow-ups | 222, 341, 315, 493, 327, 215 |
| 12 | Design | 146 without `OrderedDict`, 460, 380, 710, 855, 224, 307, 211 |
| 13 | Graphs | 785, 207 both ways, 130, 990, 1631, 787, 1584, 332, 1334 |
| 14 | Mock: three unlabeled problems in 90 minutes, then the questions below | three misses from the log |

### 39f.14.2 Interview questions with model answers

**1. What is the difference between traversal and decomposition?**
*Traversal walks the structure with a function that returns nothing and keeps the answer outside. Decomposition defines the function by its return value for a subproblem and combines the subproblems' answers, trusting the definition in the recursive calls. Backtracking is traversal of a decision tree; dynamic programming and divide and conquer are decomposition, with and without overlapping subproblems.*

**2. Why is the postorder position special?**
*It is the only moment when both subtrees' results are available, so facts about a subtree — height, size, sum, whether it is a BST, its serialization — are computed there once, O(n) in total. Recomputing them from every node is the usual O(n²) mistake.*

**3. When does a sliding window work, and what if it does not?**
*It needs a monotone condition: any window inside a valid one is valid (for "longest"), or any window containing a valid one is valid (for "shortest"). Then the left edge never moves back and the scan is O(n). Otherwise change the question: "exactly k" is "at most k" minus "at most k − 1"; fixing the number of distinct letters restores monotonicity in 395; with negative numbers, use prefix sums.*

**4. State your binary-search invariant for the left bound.**
*Closed interval, `while lo <= hi`: everything before lo is smaller than the target, everything after hi is at least the target. Mid always leaves the interval, so it terminates, and at exit lo = hi + 1 is the first index with a value at least the target. I then check whether it holds the target.*

**5. How do you recognize binary search on the answer?**
*A minimum maximum or maximum minimum over a large numeric range, with an easy check for a fixed candidate. It is correct when feasibility is monotone — if capacity C works, any larger capacity works — so the feasible values form a suffix of the range.*

**6. How does a monotonic queue give a window's maximum in amortized O(1)?**
*Beside the items it keeps the candidates for the maximum in decreasing order; an arrival removes every candidate no larger than itself from the back, since those leave earlier and can never be the maximum again. The front candidate is the maximum, and it leaves when its own item departs, which I detect by tagging items with arrival numbers. Each value enters and leaves the candidate deque at most once.*

**7. Design an LFU cache with O(1) operations.**
*Key to value and frequency; frequency to an ordered set of keys by recency; and the minimum frequency. A hit moves the key from bucket f to f + 1, and the minimum becomes f + 1 only if bucket f was the minimum and is now empty. A new key has frequency 1 and resets the minimum to 1. Eviction pops the oldest key of the minimum bucket.*

**8. How do you delete from an array in O(1) and still sample uniformly?**
*Give up order: move the last element into the hole and pop the end, with a map from value to index to find the hole and update the moved element. With duplicates, map each value to a set of indices and handle the case where the moved element has the same value.*

**9. Why does consistent hashing move so few keys when a server is added?**
*A key belongs to the next server point clockwise on a shared hash circle, so a new server takes only the keys just before its own points, about 1/(N + 1) of them; with hash mod N almost every key moves. Virtual nodes keep the arcs, and the loads, even.*

**10. When can Dijkstra be adapted to a different path cost?**
*When extending a path never makes it better: sums of non-negative weights, products of probabilities at most 1, the maximum edge on a path; then a node's value is final when first popped. With negative weights, or a limit such as "at most k edges" under which a dearer path may be the only one that can continue, use Bellman–Ford or put the limit into the state, as (city, stops) in 787.*

**11. What does a consistent A* heuristic buy, and why are Kruskal and Prim correct?**
*Admissibility makes the result optimal; consistency, h(u) ≤ w(u, v) + h(v), makes the reduced weights non-negative, so A* is Dijkstra on them and expands each node once. Kruskal and Prim both add a lightest edge crossing a cut that no chosen edge crosses (a component, or the tree, against the rest), and the cut property says the chosen edges then still fit inside some minimum spanning tree.*

**12. How do you detect a cycle in a directed graph, and why is a visited set not enough?**
*DFS with three states: a cycle exists exactly when an edge reaches a node still on the current path. A visited set also flags edges into finished nodes, which are harmless, since two paths meeting again are not a cycle. Kahn's algorithm is the alternative: if not every node reaches in-degree zero, there is a cycle.*

## Sources

- labuladong, *labuladong Algo Notes* (English edition), "Classic Problem Solving Templates" and "Data Structure Algorithms" — the topic map this chapter follows and extends: https://labuladong.online/en/algo/home/; table of contents: https://github.com/labuladong/fucking-algorithm/blob/english/README.md (checked October 2026).
- LeetCode problem set: https://leetcode.com/problemset/. Numbers, titles and Premium status (†) checked in October 2026 against the doocs/leetcode index, which mirrors LeetCode's titles and lock marks (https://leetcode.doocs.org/en/; repository https://github.com/doocs/leetcode); 785's question mark follows chapter 39d's check on leetcode.com.
- E. W. Dijkstra, "A note on two problems in connexion with graphs", *Numerische Mathematik* 1, 1959 (shortest paths, and a tree-growing minimum spanning tree method).
- R. C. Prim, "Shortest connection networks and some generalizations", *Bell System Technical Journal* 36(6), 1957; J. B. Kruskal, "On the shortest spanning subtree of a graph and the traveling salesman problem", *Proceedings of the AMS* 7(1), 1956.
- R. Bellman, "On a routing problem", *Quarterly of Applied Mathematics* 16(1), 1958, 87–90 (the round-by-round relaxation behind Bellman–Ford, used for 787 and as the tests' reference).
- P. E. Hart, N. J. Nilsson and B. Raphael, "A formal basis for the heuristic determination of minimum cost paths", *IEEE Transactions on Systems Science and Cybernetics* 4(2), 1968 (A*).
- R. W. Floyd, "Algorithm 97: Shortest path", *Communications of the ACM* 5(6), 1962; S. Warshall, "A theorem on Boolean matrices", *Journal of the ACM* 9(1), 1962.
- C. Hierholzer and C. Wiener, "Ueber die Möglichkeit, einen Linienzug ohne Wiederholung und ohne Unterbrechung zu umfahren", *Mathematische Annalen* 6, 1873, 30–32 (published after Hierholzer's death in 1871).
- A. B. Kahn, "Topological sorting of large networks", *Communications of the ACM* 5(11), 1962; R. E. Tarjan, "Depth-first search and linear graph algorithms", *SIAM Journal on Computing* 1(2), 1972.
- R. E. Tarjan, "Efficiency of a good but not linear set union algorithm", *Journal of the ACM* 22(2), 1975 (the inverse-Ackermann bound).
- R. M. Karp and M. O. Rabin, "Efficient randomized pattern-matching algorithms", *IBM Journal of Research and Development* 31(2), 1987; G. Manacher, "A new linear-time 'on-line' algorithm for finding the smallest initial palindrome of a string", *Journal of the ACM* 22(3), 1975, 346–351.
- P. M. Fenwick, "A new data structure for cumulative frequency tables", *Software: Practice and Experience* 24(3), 1994, 327–336 (the Fenwick tree named as an alternative in 39f.4, 39f.6.3, 39f.11.3 and 39f.12.6).
- D. Karger, E. Lehman, T. Leighton, R. Panigrahy, M. Levine and D. Lewin, "Consistent hashing and random trees: distributed caching protocols for relieving hot spots on the World Wide Web", *Proceedings of the 29th ACM Symposium on Theory of Computing (STOC)*, 1997, 654–663; G. DeCandia et al., "Dynamo: Amazon's highly available key-value store", *SOSP 2007* (virtual nodes and replica placement).
- C. A. R. Hoare, "Algorithm 65: Find", *Communications of the ACM* 4(7), 1961 (quickselect); M. Blum, R. W. Floyd, V. Pratt, R. L. Rivest and R. E. Tarjan, "Time bounds for selection", *Journal of Computer and System Sciences* 7(4), 1973 (median of medians).
- P. S. Efraimidis and P. G. Spirakis, "Weighted random sampling with a reservoir", *Information Processing Letters* 97(5), 2006.
- Python documentation: `bisect` (https://docs.python.org/3/library/bisect.html), `collections.OrderedDict` (https://docs.python.org/3/library/collections.html), `hashlib` (https://docs.python.org/3/library/hashlib.html), `ast` (https://docs.python.org/3/library/ast.html), `PYTHONHASHSEED` (https://docs.python.org/3/using/cmdline.html#envvar-PYTHONHASHSEED).
- Code: `labs/algorithm-frameworks/frameworks_1.py`, `test_frameworks_1.py` and `check_chapter_sync.py` in this repository (standard-library Python 3.10+; run `python3 -B test_frameworks_1.py`).
