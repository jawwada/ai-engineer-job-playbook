"""Tests for frameworks_1.py: fixed examples plus randomized checks against brute-force references.

Run:  python3 -B test_frameworks_1.py      (standard library only; prints one line per group)
"""
import ast
import itertools
import math
import random
import re
import sys
from collections import Counter, OrderedDict, defaultdict, deque

sys.dont_write_bytecode = True                  # keep the lab folder free of __pycache__
import frameworks_1 as F  # noqa: E402

rng = random.Random(396)


def check(name, fn):
    fn()
    print(f"ok  {name}")


# ----------------------------------------------------------------------------- helpers


def lst(values):
    return F.build_list(values)


def vals(head, limit=100_000):
    """List values; fails loudly on a cycle instead of looping forever."""
    out = []
    while head:
        out.append(head.val)
        head = head.next
        assert len(out) <= limit, "list too long: probably a cycle"
    return out


def random_tree(n, lo=-5, hi=5, distinct=False):
    """Random binary tree with n nodes; distinct=True draws distinct values."""
    if n == 0:
        return None
    values = rng.sample(range(lo, max(hi, lo + n) + 1), n) if distinct else [rng.randint(lo, hi) for _ in range(n)]
    nodes = [F.TreeNode(v) for v in values]
    for i in range(1, n):
        while True:
            parent = nodes[rng.randrange(i)]
            side = rng.choice(("left", "right"))
            if getattr(parent, side) is None:
                setattr(parent, side, nodes[i])
                break
    return nodes[0]


def shape(root):
    """Nested tuple of (value, left, right): equal shapes and values compare equal."""
    if root is None:
        return None
    return (root.val, shape(root.left), shape(root.right))


def preorder(root):
    return [] if root is None else [root.val] + preorder(root.left) + preorder(root.right)


def inorder(root):
    return [] if root is None else inorder(root.left) + [root.val] + inorder(root.right)


def postorder(root):
    return [] if root is None else postorder(root.left) + postorder(root.right) + [root.val]


def nodes_of(root):
    return [] if root is None else [root] + nodes_of(root.left) + nodes_of(root.right)


def path_to(root, target):
    """Nodes from root to target (by identity), or None."""
    if root is None:
        return None
    if root is target:
        return [root]
    for child in (root.left, root.right):
        p = path_to(child, target)
        if p:
            return [root] + p
    return None


def brute_lca(root, targets):
    paths = [path_to(root, t) for t in targets]
    if any(p is None for p in paths):
        return None
    lca = None
    for level in zip(*paths):
        if all(node is level[0] for node in level):
            lca = level[0]
        else:
            break
    return lca


def bst_from(values):
    """Reference BST insertion (independent of the code under test)."""
    root = None
    for v in values:
        node = F.TreeNode(v)
        if root is None:
            root = node
            continue
        cur = root
        while True:
            if v < cur.val:
                if cur.left is None:
                    cur.left = node
                    break
                cur = cur.left
            else:
                if cur.right is None:
                    cur.right = node
                    break
                cur = cur.right
    return root


def copy_tree(root):
    if root is None:
        return None
    return F.TreeNode(root.val, copy_tree(root.left), copy_tree(root.right))


# ----------------------------------------------------------------------------- 39f.1


def t_thinking():
    for values, good in (([3, 1, 4, 3, None, 1, 5], 4), ([3, 3, None, 4, 2], 3), ([1], 1)):    # LC 1448 examples
        root = F.build_tree(values)
        assert F.good_nodes_traverse(root) == F.good_nodes_decompose(root) == good
    assert F.good_nodes_traverse(None) == F.good_nodes_decompose(None) == 0
    root = F.build_tree([3, 5, 1, 6, 2, 9, 8, None, None, 7, 4])                       # LC 872 example 1
    assert F.leaves_traverse(root) == F.leaves_decompose(root) == [6, 7, 4, 9, 8]
    assert F.leaves_traverse(None) == F.leaves_decompose(None) == []
    assert F.climb_stairs_traverse(2) == 2 and F.climb_stairs_traverse(3) == 3
    for n in range(0, 21):
        fib = [1, 1]
        while len(fib) <= n:
            fib.append(fib[-1] + fib[-2])
        assert F.climb_stairs_traverse(n) == F.climb_stairs_decompose(n) == fib[n]
    for _ in range(400):
        root = random_tree(rng.randint(0, 40))
        good = sum(all(a.val <= n.val for a in path_to(root, n)) for n in nodes_of(root))
        assert F.good_nodes_traverse(root) == F.good_nodes_decompose(root) == good
        leaves = [n.val for n in nodes_of(root) if n.left is None and n.right is None]    # preorder keeps them left to right
        assert F.leaves_traverse(root) == F.leaves_decompose(root) == leaves
        report = F.node_report(root)
        nodes = nodes_of(root)                       # preorder
        ino_nodes = []

        def walk(node):
            if node:
                walk(node.left)
                ino_nodes.append(node)
                walk(node.right)

        walk(root)
        rank = {id(n): i for i, n in enumerate(ino_nodes)}
        expected = [(n.val, len(path_to(root, n)) - 1, len(nodes_of(n)), rank[id(n)]) for n in nodes]
        assert report == expected


# ----------------------------------------------------------------------------- 39f.2


def t_linked_lists():
    assert vals(F.merge_two_lists(lst([1, 2, 4]), lst([1, 3, 4]))) == [1, 1, 2, 3, 4, 4]
    assert vals(F.partition_list(lst([1, 4, 3, 2, 5, 2]), 3)) == [1, 2, 2, 4, 3, 5]
    assert vals(F.merge_k_lists_divide([lst([1, 4, 5]), lst([1, 3, 4]), lst([2, 6])])) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert F.merge_k_lists_divide([]) is None and F.merge_k_lists_divide([None]) is None
    assert vals(F.remove_nth_from_end(lst([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]
    assert vals(F.remove_nth_from_end(lst([1]), 1)) == []
    assert vals(F.delete_duplicates_all(lst([1, 2, 3, 3, 4, 4, 5]))) == [1, 2, 5]
    assert vals(F.delete_duplicates_all(lst([1, 1, 1, 2, 3]))) == [2, 3]
    assert vals(F.delete_duplicates(lst([1, 1, 2, 3, 3]))) == [1, 2, 3]
    assert vals(F.reverse_between_recursive(lst([1, 2, 3, 4, 5]), 2, 4)) == [1, 4, 3, 2, 5]
    assert vals(F.reverse_k_group_recursive(lst([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert vals(F.reverse_k_group_recursive(lst([1, 2, 3, 4, 5]), 3)) == [3, 2, 1, 4, 5]
    assert F.is_palindrome_list_recursive(lst([1, 2, 2, 1])) and not F.is_palindrome_list_recursive(lst([1, 2]))
    # LC 160 example: 8 is the first shared node
    shared = lst([8, 4, 5])
    a, b = F.ListNode(4, F.ListNode(1, shared)), F.ListNode(5, F.ListNode(6, F.ListNode(1, shared)))
    assert F.get_intersection_node(a, b) is shared
    for _ in range(500):
        n = rng.randint(0, 12)
        xs, ys = sorted(rng.randint(0, 6) for _ in range(n)), sorted(rng.randint(0, 6) for _ in range(rng.randint(0, 12)))
        a, b = lst(xs), lst(ys)
        source = {id(node): "a" for node in iter_nodes(a)} | {id(node): "b" for node in iter_nodes(b)}
        merged = F.merge_two_lists(a, b)
        assert vals(merged) == sorted(xs + ys)
        node = merged                               # stability: among equal values, a's nodes come first
        while node and node.next:
            if node.val == node.next.val:
                assert not (source[id(node)] == "b" and source[id(node.next)] == "a")
            node = node.next
        values = [rng.randint(0, 9) for _ in range(rng.randint(0, 15))]
        pivot = rng.randint(0, 10)
        assert vals(F.partition_list(lst(values), pivot)) == [v for v in values if v < pivot] + [v for v in values if v >= pivot]
        lists = [sorted(rng.randint(-5, 5) for _ in range(rng.randint(0, 6))) for _ in range(rng.randint(0, 7))]
        assert vals(F.merge_k_lists_divide([lst(x) for x in lists])) == sorted(sum(lists, []))
        k = rng.randint(1, 16)
        node = F.kth_from_end(lst(values), k)
        assert (node is None) if k > len(values) else node.val == values[-k]
        if values:
            n = rng.randint(1, len(values))
            assert vals(F.remove_nth_from_end(lst(values), n)) == values[:len(values) - n] + values[len(values) - n + 1:]
        sv = sorted(values)
        assert vals(F.delete_duplicates(lst(sv))) == sorted(set(sv))
        counts = Counter(sv)
        assert vals(F.delete_duplicates_all(lst(sv))) == [v for v in sv if counts[v] == 1]
        assert vals(F.reverse_list_recursive(lst(values))) == values[::-1]
        if values:
            n = rng.randint(1, len(values))
            assert vals(F.reverse_first_n(lst(values), n)) == values[:n][::-1] + values[n:]
            left = rng.randint(1, len(values))
            right = rng.randint(left, len(values))
            expected = values[:left - 1] + values[left - 1:right][::-1] + values[right:]
            assert vals(F.reverse_between_recursive(lst(values), left, right)) == expected
        k = rng.randint(1, 5)
        expected = []
        for start in range(0, len(values), k):
            block = values[start:start + k]
            expected += block[::-1] if len(block) == k else block
        assert vals(F.reverse_k_group_recursive(lst(values), k)) == expected
        pal = [rng.randint(0, 2) for _ in range(rng.randint(0, 6))]
        pal = pal + pal[::-1][rng.randint(0, 1):] if rng.random() < 0.5 else pal
        assert F.is_palindrome_list_recursive(lst(pal)) == (pal == pal[::-1])
        # intersection: unique prefixes plus an optional shared tail
        tail = lst([rng.randint(0, 9) for _ in range(rng.randint(0, 4))])
        a = build_onto([rng.randint(0, 9) for _ in range(rng.randint(0, 4))], tail)
        b = build_onto([rng.randint(0, 9) for _ in range(rng.randint(0, 4))], tail)
        assert F.get_intersection_node(a, b) is tail


def iter_nodes(head):
    while head:
        yield head
        head = head.next


def build_onto(values, tail):
    head = tail
    for v in reversed(values):
        head = F.ListNode(v, head)
    return head


# ----------------------------------------------------------------------------- 39f.3


def t_arrays():
    nums = [3, 2, 2, 3]
    assert F.remove_element(nums, 3) == 2 and nums[:2] == [2, 2]
    nums = [0, 1, 0, 3, 12]
    F.move_zeroes(nums)
    assert nums == [1, 3, 12, 0, 0]
    nums = [1, 1, 1, 2, 2, 3]
    assert F.remove_duplicates_keep_k(nums, 2) == 5 and nums[:5] == [1, 1, 2, 2, 3]
    nums = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    assert F.remove_duplicates_keep_k(nums, 1) == 5 and nums[:5] == [0, 1, 2, 3, 4]
    chars = list("hello")
    F.reverse_in_place(chars)
    assert chars == list("olleh")
    nums = [1, 2, 3, 4, 5, 6, 7]
    F.rotate_array(nums, 3)
    assert nums == [5, 6, 7, 1, 2, 3, 4]
    assert F.longest_palindrome("babad") in ("bab", "aba") and F.longest_palindrome("cbbd") == "bb"
    m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    F.rotate_image(m)
    assert m == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    assert F.spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert F.spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
    assert F.generate_spiral_matrix(3) == [[1, 2, 3], [8, 9, 4], [7, 6, 5]]
    assert F.four_sum([1, 0, -1, 0, -2, 2], 0) == [[-2, -1, 1, 2], [-2, 0, 0, 2], [-1, 0, 0, 1]]
    assert F.four_sum([2, 2, 2, 2, 2], 8) == [[2, 2, 2, 2]]
    assert F.n_sum([-1, 0, 1, 2, -1, -4], 3, 0) == [[-1, -1, 2], [-1, 0, 1]]
    for _ in range(400):
        values = [rng.randint(-3, 3) for _ in range(rng.randint(0, 12))]
        val = rng.randint(-3, 3)
        nums = values[:]
        length = F.remove_element(nums, val)
        assert nums[:length] == [v for v in values if v != val]
        nums = values[:]
        F.move_zeroes(nums)
        assert nums == [v for v in values if v != 0] + [0] * values.count(0)
        sv, k = sorted(values), rng.randint(1, 3)
        nums = sv[:]
        length = F.remove_duplicates_keep_k(nums, k)
        expected = [v for i, v in enumerate(sv) if sv[:i].count(v) < k]
        assert nums[:length] == expected
        nums, k = values[:], rng.randint(0, 20)
        F.rotate_array(nums, k)
        assert nums == (values[-(k % len(values)):] + values[:-(k % len(values))] if values and k % len(values) else values)
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 12)))
        best = max((len(s[i:j]) for i in range(len(s) + 1) for j in range(i, len(s) + 1) if s[i:j] == s[i:j][::-1]), default=0)
        got = F.longest_palindrome(s)
        assert len(got) == best and got == got[::-1] and got in s
        n = rng.randint(0, 6)
        m = [[rng.randint(0, 9) for _ in range(n)] for _ in range(n)]
        cw, ccw = [r[:] for r in m], [r[:] for r in m]
        F.rotate_image(cw)
        F.rotate_image_counterclockwise(ccw)
        assert cw == [list(row) for row in zip(*m[::-1])]
        assert ccw == [list(row) for row in zip(*m)][::-1]
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        m = [[rng.randint(0, 99) for _ in range(cols)] for _ in range(rows)]
        assert F.spiral_order(m) == brute_spiral(m)
        assert F.spiral_order(F.generate_spiral_matrix(n)) == list(range(1, n * n + 1))
        k = rng.randint(2, 4)
        values = [rng.randint(-4, 4) for _ in range(rng.randint(0, 9))]
        target = rng.randint(-5, 5)
        expected = sorted({tuple(sorted(c)) for c in itertools.combinations(values, k) if sum(c) == target})
        assert sorted(tuple(t) for t in F.n_sum(values, k, target)) == expected


def brute_spiral(m):
    rows, cols = len(m), len(m[0])
    seen, out = set(), []
    r = c = d = 0
    steps = ((0, 1), (1, 0), (0, -1), (-1, 0))
    for _ in range(rows * cols):
        out.append(m[r][c])
        seen.add((r, c))
        nr, nc = r + steps[d][0], c + steps[d][1]
        if not (0 <= nr < rows and 0 <= nc < cols) or (nr, nc) in seen:
            d = (d + 1) % 4
            nr, nc = r + steps[d][0], c + steps[d][1]
        r, c = nr, nc
    return out


# ----------------------------------------------------------------------------- 39f.4


def t_prefix_and_difference():
    arr = F.NumArray([-2, 0, 3, -5, 2, -1])
    assert (arr.sum_range(0, 2), arr.sum_range(2, 5), arr.sum_range(0, 5)) == (1, -1, -3)
    mat = F.NumMatrix([[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]])
    assert (mat.sum_region(2, 1, 4, 3), mat.sum_region(1, 1, 2, 2), mat.sum_region(1, 2, 2, 4)) == (8, 11, 12)
    assert F.get_modified_array(5, [[1, 3, 2], [2, 4, 3], [0, 2, -2]]) == [-2, 0, 3, 5, 3]
    assert F.corp_flight_bookings([[1, 2, 10], [2, 3, 20], [2, 5, 25]], 5) == [10, 55, 45, 25, 25]
    assert not F.car_pooling([[2, 1, 5], [3, 3, 7]], 4) and F.car_pooling([[2, 1, 5], [3, 3, 7]], 5)
    for _ in range(400):
        nums = [rng.randint(-9, 9) for _ in range(rng.randint(1, 15))]
        arr = F.NumArray(nums)
        i = rng.randrange(len(nums))
        j = rng.randint(i, len(nums) - 1)
        assert arr.sum_range(i, j) == sum(nums[i:j + 1])
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        m = [[rng.randint(-9, 9) for _ in range(cols)] for _ in range(rows)]
        mat = F.NumMatrix(m)
        r1, c1 = rng.randrange(rows), rng.randrange(cols)
        r2, c2 = rng.randint(r1, rows - 1), rng.randint(c1, cols - 1)
        assert mat.sum_region(r1, c1, r2, c2) == sum(m[r][c] for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
        base, updates = nums[:], []
        for _ in range(rng.randint(0, 6)):
            i = rng.randrange(len(nums))
            j = rng.randint(i, len(nums) - 1)
            v = rng.randint(-5, 5)
            updates.append((i, j, v))
            for t in range(i, j + 1):
                base[t] += v
        assert F.add_to_ranges(nums, updates) == base
        length = rng.randint(0, 8)
        updates = [(i, rng.randint(i, length - 1), rng.randint(-5, 5)) for i in
                   (rng.randrange(length) for _ in range(rng.randint(0, 5)))] if length else []
        assert F.get_modified_array(length, updates) == [sum(v for i, j, v in updates if i <= t <= j) for t in range(length)]
        n = rng.randint(1, 8)
        bookings = []
        for _ in range(rng.randint(0, 6)):
            first = rng.randint(1, n)
            bookings.append([first, rng.randint(first, n), rng.randint(1, 9)])
        assert F.corp_flight_bookings(bookings, n) == [sum(s for f, l, s in bookings if f <= x <= l) for x in range(1, n + 1)]
        trips = []
        for _ in range(rng.randint(0, 6)):
            start = rng.randint(0, 9)
            trips.append([rng.randint(1, 5), start, rng.randint(start + 1, 10)])
        cap = rng.randint(1, 12)
        peak = max((sum(p for p, s, e in trips if s <= x < e) for x in range(11)), default=0)
        assert F.car_pooling(trips, cap) == (peak <= cap)


# ----------------------------------------------------------------------------- 39f.5


def t_sliding_window():
    assert F.check_inclusion("ab", "eidbaooo") and not F.check_inclusion("ab", "eidboaoo")
    assert F.longest_ones([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2) == 6
    assert F.longest_ones([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3) == 10
    assert F.num_subarray_product_less_than_k([10, 5, 2, 6], 100) == 8
    assert F.num_subarray_product_less_than_k([1, 2, 3], 0) == 0
    assert F.min_operations_to_zero([1, 1, 4, 2, 3], 5) == 2
    assert F.min_operations_to_zero([5, 6, 7, 8, 9], 4) == -1
    assert F.min_operations_to_zero([3, 2, 20, 1, 1, 3], 10) == 5
    assert F.longest_substring_k_repeats("aaabb", 3) == 3 and F.longest_substring_k_repeats("ababbc", 2) == 5
    assert F.subarrays_with_k_distinct([1, 2, 1, 2, 3], 2) == 7 and F.subarrays_with_k_distinct([1, 2, 1, 3, 4], 3) == 3
    assert F.find_repeated_dna_sequences("AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT") == ["AAAAACCCCC", "CCCCCAAAAA"]
    assert F.find_repeated_dna_sequences("AAAAAAAAAAAAA") == ["AAAAAAAAAA"]
    assert F.str_str_rabin_karp("sadbutsad", "sad") == 0 and F.str_str_rabin_karp("leetcode", "leeto") == -1
    for _ in range(400):
        s1 = "".join(rng.choice("abc") for _ in range(rng.randint(1, 4)))
        s2 = "".join(rng.choice("abcd") for _ in range(rng.randint(0, 10)))
        brute = any(sorted(s2[i:i + len(s1)]) == sorted(s1) for i in range(len(s2) - len(s1) + 1))
        assert F.check_inclusion(s1, s2) == brute
        bits = [rng.randint(0, 1) for _ in range(rng.randint(0, 14))]
        k = rng.randint(0, 4)
        assert F.longest_ones(bits, k) == max((j - i for i in range(len(bits) + 1) for j in range(i, len(bits) + 1)
                                               if bits[i:j].count(0) <= k), default=0)
        nums = [rng.randint(1, 6) for _ in range(rng.randint(1, 10))]
        k = rng.randint(0, 60)
        assert F.num_subarray_product_less_than_k(nums, k) == sum(
            1 for i in range(len(nums)) for j in range(i + 1, len(nums) + 1) if math.prod(nums[i:j]) < k)
        x = rng.randint(1, 30)
        best = min((i + (len(nums) - j) for i in range(len(nums) + 1) for j in range(i, len(nums) + 1)
                    if sum(nums[:i]) + sum(nums[j:]) == x), default=-1)
        assert F.min_operations_to_zero(nums, x) == best
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 12)))
        k = rng.randint(1, 3)
        assert F.longest_substring_k_repeats(s, k) == max(
            (j - i for i in range(len(s)) for j in range(i + 1, len(s) + 1) if min(Counter(s[i:j]).values()) >= k), default=0)
        arr = [rng.randint(1, 4) for _ in range(rng.randint(1, 10))]
        k = rng.randint(1, 4)
        assert F.subarrays_with_k_distinct(arr, k) == sum(
            1 for i in range(len(arr)) for j in range(i + 1, len(arr) + 1) if len(set(arr[i:j])) == k)
        dna = "".join(rng.choice("ACGT"[:rng.randint(1, 4)]) for _ in range(rng.randint(0, 30)))
        length = rng.randint(1, 6)
        counts = Counter(dna[i:i + length] for i in range(len(dna) - length + 1))
        assert F.find_repeated_dna_sequences(dna, length) == sorted(t for t, c in counts.items() if c > 1)
        hay = "".join(rng.choice("ab") for _ in range(rng.randint(0, 15)))
        needle = "".join(rng.choice("ab") for _ in range(rng.randint(0, 4)))
        assert F.str_str_rabin_karp(hay, needle) == hay.find(needle)
        assert F.str_str_rabin_karp(hay, needle, mod=3) == hay.find(needle)    # collisions everywhere


# ----------------------------------------------------------------------------- 39f.6


def t_binary_search():
    assert F.binary_search([-1, 0, 3, 5, 9, 12], 9) == 4 and F.binary_search([-1, 0, 3, 5, 9, 12], 2) == -1
    nums = [5, 7, 7, 8, 8, 10]
    assert (F.left_bound(nums, 8), F.right_bound(nums, 8)) == (3, 4)
    assert (F.left_bound(nums, 6), F.right_bound(nums, 6)) == (-1, -1)
    assert F.ship_within_days([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15
    assert F.ship_within_days([3, 2, 2, 4, 1, 4], 3) == 6 and F.ship_within_days([1, 2, 3, 1, 1], 4) == 3
    assert F.split_array([7, 2, 5, 10, 8], 2) == 18 and F.split_array([1, 2, 3, 4, 5], 2) == 9
    assert F.advantage_count([2, 7, 11, 15], [1, 10, 4, 11]) == [2, 11, 7, 15]
    assert F.advantage_count([12, 24, 8, 32], [13, 25, 32, 11]) == [24, 32, 8, 12]
    from bisect import bisect_left, bisect_right
    for _ in range(600):
        nums = sorted(rng.randint(-5, 5) for _ in range(rng.randint(0, 12)))
        target = rng.randint(-7, 7)
        i = F.binary_search(nums, target)
        assert (i == -1) if target not in nums else nums[i] == target
        assert F.left_bound(nums, target) == (bisect_left(nums, target) if target in nums else -1)
        assert F.right_bound(nums, target) == (bisect_right(nums, target) - 1 if target in nums else -1)
        lo, hi, cut = rng.randint(-10, 10), rng.randint(-10, 20), rng.randint(-12, 22)
        assert F.first_true(lo, hi, lambda x: x >= cut) == next((x for x in range(lo, hi + 1) if x >= cut), max(hi + 1, lo))
        weights = [rng.randint(1, 9) for _ in range(rng.randint(1, 8))]
        days = rng.randint(1, len(weights))
        assert F.ship_within_days(weights, days) == brute_partition(weights, days, exact=False)
        assert F.split_array(weights, days) == brute_partition(weights, days, exact=True)
        a = [rng.randint(0, 9) for _ in range(rng.randint(1, 6))]
        b = [rng.randint(0, 9) for _ in range(len(a))]
        out = F.advantage_count(a, b)
        assert sorted(out) == sorted(a)
        assert sum(x > y for x, y in zip(out, b)) == max(sum(x > y for x, y in zip(p, b)) for p in itertools.permutations(a))
    for w in ([1], [1, 3], [3, 1, 2, 4], [5, 0, 5], [2, 7, 1]):
        picker = F.WeightedPicker(w, rng=rng)
        owners = Counter(bisect_left(picker.prefix, t) for t in range(1, sum(w) + 1))
        assert all(owners[i] == x for i, x in enumerate(w))                 # exact: i owns w[i] tickets
        draws = 30_000
        freq = Counter(picker.pick_index() for _ in range(draws))
        for i, x in enumerate(w):
            assert abs(freq[i] / draws - x / sum(w)) < 0.015


def brute_partition(nums, parts, exact):
    """Smallest possible largest part over all splits into `parts` (or at most `parts`) contiguous pieces."""
    n, best = len(nums), float("inf")
    counts = [parts - 1] if exact else range(parts)
    for c in counts:
        for cuts in itertools.combinations(range(1, n), c):
            bounds = (0,) + cuts + (n,)
            best = min(best, max(sum(nums[bounds[i]:bounds[i + 1]]) for i in range(len(bounds) - 1)))
    return best


# ----------------------------------------------------------------------------- 39f.7


def t_stacks_and_queues():
    q, s = F.MyQueue(), F.MyStack()
    q.push(1)
    q.push(2)
    assert q.peek() == 1 and q.pop() == 1 and not q.empty()
    s.push(1)
    s.push(2)
    assert s.top() == 2 and s.pop() == 2 and not s.empty()
    assert F.sum_subarray_mins([3, 1, 2, 4]) == 17 and F.sum_subarray_mins([11, 81, 94, 43, 3]) == 444
    assert F.max_sliding_window_queue([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert F.longest_subarray_within_limit([8, 2, 4, 7], 4) == 2
    assert F.longest_subarray_within_limit([10, 1, 2, 4, 7, 2], 5) == 4
    assert F.longest_subarray_within_limit([4, 2, 2, 2, 4, 4, 2, 2], 0) == 3
    assert F.remove_duplicate_letters("bcabc") == "abc" and F.remove_duplicate_letters("cbacdcbc") == "acdb"
    import operator as op
    for _ in range(300):
        q, s, ref_q, ref_s = F.MyQueue(), F.MyStack(), deque(), []
        for _ in range(30):
            if ref_q and rng.random() < 0.4:
                assert q.peek() == ref_q[0] and q.pop() == ref_q.popleft()
                assert s.top() == ref_s[-1] and s.pop() == ref_s.pop()
            else:
                x = rng.randint(0, 99)
                q.push(x)
                s.push(x)
                ref_q.append(x)
                ref_s.append(x)
            assert q.empty() == (not ref_q) and s.empty() == (not ref_s)
        nums = [rng.randint(0, 5) for _ in range(rng.randint(0, 12))]
        for rel in (op.gt, op.ge, op.lt, op.le):
            nxt = [next((j for j in range(i + 1, len(nums)) if rel(nums[j], nums[i])), -1) for i in range(len(nums))]
            prv = [next((j for j in range(i - 1, -1, -1) if rel(nums[j], nums[i])), -1) for i in range(len(nums))]
            assert F.nearest_index(nums, rel) == nxt and F.nearest_index(nums, rel, reverse=True) == prv
        arr = [rng.randint(1, 6) for _ in range(rng.randint(1, 12))]
        assert F.sum_subarray_mins(arr) == sum(min(arr[i:j]) for i in range(len(arr)) for j in range(i + 1, len(arr) + 1))
        mq, ref = F.MaxMinQueue(), deque()
        for _ in range(40):
            if ref and rng.random() < 0.45:
                assert mq.pop() == ref.popleft()
            else:
                x = rng.randint(0, 6)
                mq.push(x)
                ref.append(x)
            assert len(mq) == len(ref)
            if ref:
                assert mq.max() == max(ref) and mq.min() == min(ref)
        k = rng.randint(1, len(arr))
        assert F.max_sliding_window_queue(arr, k) == [max(arr[i:i + k]) for i in range(len(arr) - k + 1)]
        limit = rng.randint(0, 5)
        assert F.longest_subarray_within_limit(arr, limit) == max(
            j - i for i in range(len(arr)) for j in range(i + 1, len(arr) + 1) if max(arr[i:j]) - min(arr[i:j]) <= limit)
        text = "".join(rng.choice("abcd") for _ in range(rng.randint(1, 9)))
        m = len(set(text))
        brute = min("".join(text[i] for i in combo) for combo in itertools.combinations(range(len(text)), m)
                    if len({text[i] for i in combo}) == m)
        assert F.remove_duplicate_letters(text) == brute


# ----------------------------------------------------------------------------- 39f.8


def t_binary_trees():
    root = F.invert_tree_traverse(F.build_tree([4, 2, 7, 1, 3, 6, 9]))
    assert F.serialize_level(root) == "4,7,2,9,6,3,1"
    root = F.connect_perfect(F.build_tree([1, 2, 3, 4, 5, 6, 7]))
    assert [n.next.val if n.next else None for n in nodes_of(root)] == [None, 3, 5, 6, None, 7, None]
    root = F.build_tree([1, 2, 5, 3, 4, None, 6])
    F.flatten(root)
    assert F.serialize_level(root) == "1,#,2,#,3,#,4,#,5,#,6"
    assert F.serialize_level(F.construct_maximum_binary_tree([3, 2, 1, 6, 0, 5])) == "6,3,5,#,2,0,#,#,1"
    assert F.serialize_level(F.build_tree_pre_in([3, 9, 20, 15, 7], [9, 3, 15, 20, 7])) == "3,9,20,#,#,15,7"
    assert F.serialize_level(F.build_tree_in_post([9, 3, 15, 20, 7], [9, 15, 7, 20, 3])) == "3,9,20,#,#,15,7"
    assert F.serialize_level(F.build_tree_pre_post([1, 2, 4, 5, 3, 6, 7], [4, 5, 2, 6, 7, 3, 1])) == "1,2,3,4,5,6,7"
    dups = F.find_duplicate_subtrees(F.build_tree([1, 2, 3, 4, None, 2, 4, None, None, 4]))
    assert sorted(F.serialize_level(d) for d in dups) == ["2,4", "4"]
    assert F.serialize_level(F.deserialize_level("1,2,3,#,#,4,5")) == "1,2,3,#,#,4,5"
    assert F.serialize_level(None) == "" and F.deserialize_level("") is None
    assert F.deserialize_preorder(F.serialize_preorder(None)) is None
    for h in range(0, 7):                           # perfect trees with h levels
        n = (1 << h) - 1
        assert next_links_ok(F.connect_perfect(F.build_tree(list(range(1, n + 1)))))
    for h in range(1, 13):                          # 39f.8.1: the pair recursion makes (3^h - 1) / 2 calls
        root = F.build_tree(list(range(1, 1 << h)))
        calls = pair_recursion_calls(root)
        assert calls == (3 ** h - 1) // 2 and next_links_ok(root)
    assert calls == 265_720                         # quoted for the 4,095 nodes of 12 levels
    for _ in range(400):
        n = rng.randint(0, 25)
        root = random_tree(n)
        before = shape(root)
        mirrored = shape(F.invert_tree_traverse(copy_tree(root)))
        assert mirrored == mirror(before)
        flat = copy_tree(root)
        F.flatten(flat)
        chain, node = [], flat
        while node:
            assert node.left is None
            chain.append(node.val)
            node = node.right
        assert chain == preorder(root)
        perm = rng.sample(range(50), rng.randint(0, 12))
        a, b = F.construct_maximum_binary_tree(perm), F.construct_maximum_binary_tree_stack(perm)
        assert shape(a) == shape(b) and inorder(a) == perm and is_max_tree(a)
        root = random_tree(n, distinct=True)
        assert shape(F.build_tree_pre_in(preorder(root), inorder(root))) == shape(root)
        assert shape(F.build_tree_in_post(inorder(root), postorder(root))) == shape(root)
        rebuilt = F.build_tree_pre_post(preorder(root), postorder(root))
        assert preorder(rebuilt) == preorder(root) and postorder(rebuilt) == postorder(root)
        root = random_tree(n, 0, 2)
        groups = Counter(F.serialize_preorder(node) for node in nodes_of(root))
        got = [F.serialize_preorder(node) for node in F.find_duplicate_subtrees(root)]
        assert sorted(got) == sorted(key for key, c in groups.items() if c >= 2)
        assert shape(F.deserialize_preorder(F.serialize_preorder(root))) == shape(root)
        assert shape(F.deserialize_level(F.serialize_level(root))) == shape(root)
        assert F.traverse_with_stack(root) == (preorder(root), inorder(root), postorder(root))


def mirror(sh):
    return None if sh is None else (sh[0], mirror(sh[2]), mirror(sh[1]))


def next_links_ok(root):
    """Every node's next is its right neighbor on its level, or None at the end of the level (LC 116)."""
    queue = deque([root] if root else [])
    while queue:
        level = [queue.popleft() for _ in range(len(queue))]
        if any(a.next is not b for a, b in zip(level, level[1:] + [None])):
            return False
        queue.extend(c for node in level for c in (node.left, node.right) if c)
    return True


def pair_recursion_calls(root):
    """LC 116 by recursing on pairs of adjacent nodes, three calls per pair (39f.8.1); returns the number of calls."""
    calls = 0

    def join(a, b):
        nonlocal calls
        calls += 1
        if a and b:
            a.next = b
            join(a.left, a.right)
            join(b.left, b.right)
            join(a.right, b.left)

    if root:
        join(root.left, root.right)
    return calls


def is_max_tree(node):
    if node is None:
        return True
    for child in (node.left, node.right):
        if child and child.val > node.val:
            return False
    return is_max_tree(node.left) and is_max_tree(node.right)


# ----------------------------------------------------------------------------- 39f.9


def t_bst():
    assert F.kth_smallest(F.build_tree([3, 1, 4, None, 2]), 1) == 1
    assert F.kth_smallest(F.build_tree([5, 3, 6, 2, 4, None, None, 1]), 3) == 3
    greater = F.convert_bst(F.build_tree([4, 1, 6, 0, 2, 5, 7, None, None, None, 3, None, None, None, 8]))
    assert F.serialize_level(greater) == "30,36,21,36,35,26,15,#,#,#,33,#,#,#,8"
    assert F.is_valid_bst(F.build_tree([2, 1, 3])) and not F.is_valid_bst(F.build_tree([5, 1, 4, None, None, 3, 6]))
    assert not F.is_valid_bst(F.build_tree([8, 3, 10, 1, 9]))    # 39f.9.2: every parent-child pair ordered, 9 misplaced
    assert F.serialize_level(F.search_bst(F.build_tree([4, 2, 7, 1, 3]), 2)) == "2,1,3"
    assert F.search_bst(F.build_tree([4, 2, 7, 1, 3]), 5) is None
    assert F.num_trees(3) == 5 and F.num_trees(1) == 1 and len(F.generate_trees(3)) == 5
    tree = F.build_tree([1, 4, 3, 2, 4, 2, 5, None, None, None, None, None, None, 4, 6])
    assert F.max_sum_bst(tree) == 20
    assert F.max_sum_bst(F.build_tree([4, 3, None, 1, 2])) == 2 and F.max_sum_bst(F.build_tree([-4, -2, -5])) == 0
    for n in range(0, 9):
        assert F.num_trees(n) == math.comb(2 * n, n) // (n + 1)
        trees = F.generate_trees(n)
        assert len(trees) == (F.num_trees(n) if n else 0)
        assert len({shape(t) for t in trees}) == len(trees)
        assert all(inorder(t) == list(range(1, n + 1)) for t in trees)
    for _ in range(400):
        values = rng.sample(range(-30, 30), rng.randint(0, 20))
        root = bst_from(values)
        ordered = sorted(values)
        it = F.BSTIterator(root)
        seen = []
        while it.has_next():
            seen.append(it.next())
        assert seen == ordered
        if values:
            k = rng.randint(1, len(values))
            assert F.kth_smallest(root, k) == ordered[k - 1]
        greater = F.convert_bst(copy_tree(root))
        assert inorder(greater) == [sum(v for v in values if v >= x) for x in ordered]
        assert F.is_valid_bst(root)
        probe = rng.randint(-31, 31)
        found = F.search_bst(root, probe)
        assert (found is None) if probe not in values else found.val == probe
        if probe not in values:
            grown = F.insert_into_bst(copy_tree(root), probe)
            assert inorder(grown) == sorted(values + [probe]) and F.is_valid_bst(grown)
        if values:
            key = rng.choice(values) if rng.random() < 0.8 else probe
            pruned = F.delete_node(copy_tree(root), key)
            assert inorder(pruned) == [v for v in ordered if v != key] and F.is_valid_bst(pruned)
        any_tree = random_tree(rng.randint(0, 12), -4, 4)
        ino = inorder(any_tree)
        assert F.is_valid_bst(any_tree) == all(a < b for a, b in zip(ino, ino[1:]))
        best = 0
        for node in nodes_of(any_tree):
            sub = inorder(node)
            if all(a < b for a, b in zip(sub, sub[1:])):
                best = max(best, sum(sub))
        assert F.max_sum_bst(any_tree) == best


# ----------------------------------------------------------------------------- 39f.10


def t_lca():
    root = F.build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    by_val = {n.val: n for n in nodes_of(root)}
    assert F.lca_maybe_missing(root, by_val[5], by_val[1]) is root
    assert F.lca_maybe_missing(root, by_val[5], by_val[4]) is by_val[5]
    assert F.lca_maybe_missing(root, by_val[5], F.TreeNode(10)) is None
    assert F.lca_of_nodes(root, [by_val[4], by_val[7]]) is by_val[2]
    assert F.lca_of_nodes(root, [by_val[1]]) is by_val[1]
    assert F.lca_of_nodes(root, [by_val[v] for v in (7, 6, 2, 4)]) is by_val[5]
    assert F.lca_of_nodes(root, list(by_val.values())) is root
    assert F.lca_deepest_leaves(root) is by_val[2]
    bst = F.build_tree([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5])
    by_val = {n.val: n for n in nodes_of(bst)}
    assert F.lca_bst(bst, by_val[2], by_val[8]) is bst and F.lca_bst(bst, by_val[2], by_val[4]) is by_val[2]
    for _ in range(400):
        root = random_tree(rng.randint(1, 25))
        set_parents(root)
        nodes = nodes_of(root)
        p, q = rng.choice(nodes), rng.choice(nodes)
        if p is not q:
            assert F.lca_maybe_missing(root, p, q) is brute_lca(root, [p, q])
            assert F.lca_maybe_missing(root, p, F.TreeNode(0)) is None
        assert F.lca_with_parent(p, q) is brute_lca(root, [p, q])
        group = rng.sample(nodes, rng.randint(1, len(nodes)))
        assert F.lca_of_nodes(root, group) is brute_lca(root, group)
        depth = {id(n): len(path_to(root, n)) for n in nodes}
        deepest = max(depth.values())
        leaves = [n for n in nodes if depth[id(n)] == deepest]
        assert F.lca_deepest_leaves(root) is brute_lca(root, leaves)
        values = rng.sample(range(100), rng.randint(1, 20))
        bst = bst_from(values)
        bnodes = nodes_of(bst)
        p, q = rng.choice(bnodes), rng.choice(bnodes)
        assert F.lca_bst(bst, p, q) is brute_lca(bst, [p, q])


def set_parents(root, parent=None):
    if root:
        root.parent = parent
        set_parents(root.left, root)
        set_parents(root.right, root)


# ----------------------------------------------------------------------------- 39f.11


def t_tree_followups():
    assert F.count_nodes(F.build_tree([1, 2, 3, 4, 5, 6])) == 6 and F.count_nodes(None) == 0
    for n in range(0, 300):
        assert F.count_nodes(F.build_tree(list(range(1, n + 1)))) == n
    assert flatten_all(F.NestedIterator(nested([[1, 1], 2, [1, 1]]))) == [1, 1, 2, 1, 1]
    assert flatten_all(F.NestedIterator(nested([1, [4, [6]]]))) == [1, 4, 6]
    assert flatten_all(F.NestedIterator(nested([[], [[]], []]))) == []
    assert F.count_smaller([5, 2, 6, 1]) == [2, 1, 1, 0] and F.count_smaller([-1, -1]) == [0, 0]
    assert F.reverse_pairs([1, 3, 2, 3, 1]) == 2 and F.reverse_pairs([2, 4, 3, 5, 1]) == 3
    assert F.count_range_sum([-2, 5, -1], -2, 2) == 3 and F.count_range_sum([0], 0, 0) == 1
    assert F.find_kth_largest([3, 2, 1, 5, 6, 4], 2, rng) == 5
    assert F.find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4, rng) == 4
    for _ in range(400):
        structure = random_nested(3)
        it = F.NestedIterator(nested(structure))
        assert flatten_all(it) == list(flat_ints(structure))
        nums = [rng.randint(-6, 6) for _ in range(rng.randint(0, 14))]
        assert F.count_smaller(nums) == [sum(nums[j] < nums[i] for j in range(i + 1, len(nums))) for i in range(len(nums))]
        assert F.reverse_pairs(nums) == sum(nums[i] > 2 * nums[j] for i in range(len(nums)) for j in range(i + 1, len(nums)))
        lower = rng.randint(-6, 6)
        upper = rng.randint(lower, 8)
        assert F.count_range_sum(nums, lower, upper) == sum(
            lower <= sum(nums[i:j + 1]) <= upper for i in range(len(nums)) for j in range(i, len(nums)))
        if nums:
            k = rng.randint(1, len(nums))
            assert F.find_kth_largest(nums, k, rng) == sorted(nums)[-k]
    many = [rng.randint(0, 2) for _ in range(5000)]         # heavy duplicates: three-way partition stays fast
    assert F.find_kth_largest(many, 2500, rng) == sorted(many)[-2500]


def nested(items):
    return [F.NestedInteger(x if isinstance(x, int) else nested(x)) for x in items]


def random_nested(depth):
    out = []
    for _ in range(rng.randint(0, 4)):
        if depth and rng.random() < 0.35:
            out.append(random_nested(depth - 1))
        else:
            out.append(rng.randint(-9, 9))
    return out


def flat_ints(items):
    for x in items:
        if isinstance(x, int):
            yield x
        else:
            yield from flat_ints(x)


def flatten_all(it):
    out = []
    while it.has_next():
        assert it.has_next()                        # idempotent
        out.append(it.next())
    return out


# ----------------------------------------------------------------------------- 39f.12 caches and random sets


def t_caches():
    lru = F.LRUCacheLinked(2)
    lru.put(1, 1)
    lru.put(2, 2)
    assert lru.get(1) == 1
    lru.put(3, 3)
    assert lru.get(2) == -1
    lru.put(4, 4)
    assert (lru.get(1), lru.get(3), lru.get(4)) == (-1, 3, 4)
    lfu = F.LFUCache(2)
    lfu.put(1, 1)
    lfu.put(2, 2)
    assert lfu.get(1) == 1
    lfu.put(3, 3)
    assert lfu.get(2) == -1 and lfu.get(3) == 3
    lfu.put(4, 4)
    assert (lfu.get(1), lfu.get(3), lfu.get(4)) == (-1, 3, 4)
    for _ in range(300):
        cap = rng.randint(1, 4)
        lru, ref = F.LRUCacheLinked(cap), OrderedDict()
        lfu, store, clock = F.LFUCache(cap), {}, 0
        for _ in range(60):
            key = rng.randint(0, 6)
            clock += 1
            if rng.random() < 0.5:
                expected = ref.get(key, -1)
                if key in ref:
                    ref.move_to_end(key)
                assert lru.get(key) == expected
                if key in store:
                    store[key][1] += 1
                    store[key][2] = clock
                assert lfu.get(key) == (store[key][0] if key in store else -1)
            else:
                value = rng.randint(0, 99)
                ref[key] = value
                ref.move_to_end(key)
                if len(ref) > cap:
                    ref.popitem(last=False)
                lru.put(key, value)
                if key in store:
                    store[key][0] = value
                    store[key][1] += 1
                    store[key][2] = clock
                else:
                    if len(store) == cap:
                        victim = min(store, key=lambda k: (store[k][1], store[k][2]))
                        del store[victim]
                    store[key] = [value, 1, clock]
                lfu.put(key, value)
    assert F.LFUCache(0).get(1) == -1


def t_random_structures():
    for _ in range(200):
        rs, ref = F.RandomizedSet(rng), set()
        rc, refc = F.RandomizedCollection(rng), Counter()
        for _ in range(50):
            x = rng.randint(0, 8)
            if rng.random() < 0.55:
                assert rs.insert(x) == (x not in ref)
                ref.add(x)
                assert rc.insert(x) == (refc[x] == 0)
                refc[x] += 1
            else:
                assert rs.remove(x) == (x in ref)
                ref.discard(x)
                assert rc.remove(x) == (refc[x] > 0)
                if refc[x]:
                    refc[x] -= 1
            assert sorted(rs.values) == sorted(ref)
            assert Counter(rc.values) == +refc
            assert all(rc.values[i] == v for v, where in rc.where.items() for i in where)
            if ref:
                assert rs.get_random() in ref
    rc = F.RandomizedCollection(rng)
    for x in [1, 1, 1, 2]:
        rc.insert(x)
    draws = Counter(rc.get_random() for _ in range(20_000))
    assert abs(draws[1] / 20_000 - 0.75) < 0.015
    rs = F.RandomizedSet(rng)
    for x in range(4):
        rs.insert(x)
    rs.remove(1)
    draws = Counter(rs.get_random() for _ in range(15_000))
    assert set(draws) == {0, 2, 3} and all(abs(c / 15_000 - 1 / 3) < 0.02 for c in draws.values())
    picker = F.BlacklistPicker(7, [2, 3, 5], rng)
    draws = Counter(picker.pick() for _ in range(20_000))
    assert set(draws) == {0, 1, 4, 6} and all(abs(c / 20_000 - 0.25) < 0.02 for c in draws.values())
    for _ in range(300):
        n = rng.randint(1, 30)
        blacklist = rng.sample(range(n), rng.randint(0, n - 1))
        picker = F.BlacklistPicker(n, blacklist, rng)
        allowed = sorted(set(range(n)) - set(blacklist))
        images = sorted(picker.remap.get(x, x) for x in range(picker.size))
        assert images == allowed                    # the draw range maps one-to-one onto the allowed numbers


def t_exam_room():
    room = F.ExamRoom(10)
    assert [room.seat(), room.seat(), room.seat(), room.seat()] == [0, 9, 4, 2]
    room.leave(4)
    assert room.seat() == 5
    for _ in range(300):
        n = rng.randint(1, 12)
        room, taken = F.ExamRoom(n), set()
        for _ in range(40):
            if taken and (len(taken) == n or rng.random() < 0.4):
                p = rng.choice(sorted(taken))
                room.leave(p)
                taken.remove(p)
            else:
                if not taken:
                    expected = 0
                else:
                    expected = max((s for s in range(n) if s not in taken),
                                   key=lambda s: (min(abs(s - t) for t in taken), -s))
                assert room.seat() == expected
                taken.add(expected)


# ----------------------------------------------------------------------------- 39f.12 calculator


def reference_eval(text):
    """Evaluate with Python's parser (same precedence for + - * / and unary signs), truncating division."""
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp):
            return -ev(node.operand) if isinstance(node.op, ast.USub) else ev(node.operand)
        a, b = ev(node.left), ev(node.right)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b > 0) else -q

    return ev(ast.parse(text, mode="eval"))


def random_expression(depth):
    roll = rng.random()
    if depth == 0 or roll < 0.25:
        return str(rng.randint(0, 30))
    if roll < 0.35:
        return "-" + random_expression(depth - 1)
    if roll < 0.5:
        return "(" + random_expression(depth - 1) + ")"
    return random_expression(depth - 1) + f" {rng.choice('+-*/')} " + random_expression(depth - 1)


def t_calculator():
    cases = {"1 + 1": 2, " 2-1 + 2 ": 3, "(1+(4+5+2)-3)+(6+8)": 23, "3+2*2": 7, " 3/2 ": 1, " 3+5 / 2 ": 5,
             "6-4/2": 4, "2*(5+5*2)/3+(6/2+8)": 21, "(2+6*3+5-(3*14/7+2)*5)+3": -12, "-(2+3)": -5,
             "- (3 + (4 + 5))": -12, "7/-2": -3, "-7/2": -3, "1-(     -2)": 3}
    for text, expected in cases.items():
        assert F.calculate(text) == expected, text
    tested = 0
    while tested < 600:
        text = random_expression(rng.randint(1, 5))
        try:
            expected = reference_eval(text)
        except ZeroDivisionError:
            continue
        assert F.calculate(text) == expected, text
        assert F.calculate(text.replace(" ", "")) == expected, text
        tested += 1


# ----------------------------------------------------------------------------- 39f.12 consistent hashing


def t_consistent_hashing():
    # This group also measures the figures quoted in 39f.12.5. BLAKE2b and the key names are fixed, so they are exact.
    keys = [f"user:{i}" for i in range(20_000)]
    ring = F.ConsistentHashRing(replicas=100)
    for s in range(10):
        ring.add(f"server-{s}")
    before = {k: ring.lookup(k) for k in keys}
    ring.add("server-10")
    after = {k: ring.lookup(k) for k in keys}
    moved = [k for k in keys if before[k] != after[k]]
    assert all(after[k] == "server-10" for k in moved)      # keys only move to the new server
    modulo_moved = sum(F.ConsistentHashRing._hash(k) % 10 != F.ConsistentHashRing._hash(k) % 11 for k in keys)
    assert round(100 * len(moved) / len(keys), 1) == 10.9   # quoted: 10.9% moved (ideal 1/11, about 9.1%)
    assert round(100 * modulo_moved / len(keys), 1) == 91.1  # quoted: hash % N moves 91.1% (about 10/11)
    single = F.ConsistentHashRing(replicas=1)
    for s in range(10):
        single.add(f"server-{s}")
    mean = len(keys) / 10
    peak = max(Counter(before.values()).values()) / mean
    single_peak = max(Counter(single.lookup(k) for k in keys).values()) / mean
    assert (round(peak, 2), round(single_peak, 2)) == (1.20, 2.52)     # quoted: busiest server vs the mean load
    ring.remove("server-3")
    final = {k: ring.lookup(k) for k in keys}
    assert all(final[k] == after[k] for k in keys if after[k] != "server-3")
    assert all(final[k] != "server-3" for k in keys)
    assert max(Counter(final.values()).values()) / mean < 1.35     # still fairly even after a removal
    empty = F.ConsistentHashRing()
    try:
        empty.lookup("x")
        raise AssertionError("expected LookupError")
    except LookupError:
        pass


# ----------------------------------------------------------------------------- 39f.12 segment trees


def t_segment_trees():
    for _ in range(200):
        n = rng.randint(1, 20)
        values = [rng.randint(-20, 20) for _ in range(n)]
        trees = {"sum": (F.SegmentTree(values[:]), sum),
                 "min": (F.SegmentTree(values[:], min, float("inf")), min),
                 "max": (F.SegmentTree(values[:], max, float("-inf")), max),
                 "concat": (F.SegmentTree([str(v) + "," for v in values], lambda a, b: a + b, ""), "".join)}
        for _ in range(30):
            if rng.random() < 0.4:
                i, v = rng.randrange(n), rng.randint(-20, 20)
                values[i] = v
                for name, (tree, _) in trees.items():
                    tree.update(i, str(v) + "," if name == "concat" else v)
            else:
                lo = rng.randrange(n)
                hi = rng.randint(lo, n - 1)
                for name, (tree, fn) in trees.items():
                    window = values[lo:hi + 1] if name != "concat" else [str(v) + "," for v in values[lo:hi + 1]]
                    assert tree.query(lo, hi) == fn(window)       # concat checks left-to-right order
    for _ in range(200):
        lo, hi = rng.choice([(0, 10**9), (-10**6, 10**6), (0, 15)])
        tree, updates = F.RangeAddTree(lo, hi), []
        for _ in range(25):
            a = rng.randint(lo, hi)
            b = min(hi, a + rng.choice([0, 1, 5, 1000, 10**7]))
            if rng.random() < 0.5:
                v = rng.randint(-5, 9)
                tree.add(a, b, v)
                updates.append((a, b, v))
            else:
                total = sum(v * (min(b, r) - max(a, l) + 1) for l, r, v in updates if l <= b and a <= r)
                points = {a} | {x for l, r, _ in updates for x in (l, r + 1) if a <= x <= b}
                peak = max(sum(v for l, r, v in updates if l <= x <= r) for x in points)
                assert tree.query(a, b) == (total, peak)
    cal = F.MyCalendarThree()
    assert [cal.book(10, 20), cal.book(50, 60), cal.book(10, 40), cal.book(5, 15), cal.book(5, 10), cal.book(25, 55)] == \
        [1, 1, 2, 3, 3, 3]
    for _ in range(100):
        cal, events = F.MyCalendarThree(), []
        for _ in range(15):
            start = rng.randint(0, 40)
            end = rng.randint(start + 1, 41)
            events.append((start, end))
            expected = max(sum(s <= t < e for s, e in events) for t in range(42))
            assert cal.book(start, end) == expected


# ----------------------------------------------------------------------------- 39f.12 tries


def t_tries():
    assert F.replace_words(["cat", "bat", "rat"], "the cattle was rattled by the battery") == "the cat was rat by the bat"
    assert F.replace_words(["a", "b", "c"], "aadsfasf absbs bbab cadsfafs") == "a a b c"
    wd = F.WordDictionary()
    for w in ("bad", "dad", "mad"):
        wd.add_word(w)
    assert [wd.search(q) for q in ("pad", "bad", ".ad", "b..")] == [False, True, True, True]
    ms = F.MapSum()
    ms.insert("apple", 3)
    assert ms.sum("ap") == 3
    ms.insert("app", 2)
    assert ms.sum("ap") == 5
    for _ in range(300):
        roots = ["".join(rng.choice("ab") for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(0, 4))]
        words = ["".join(rng.choice("abc") for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 5))]
        expected = " ".join(min((r for r in roots if w.startswith(r)), key=len, default=w) for w in words)
        assert F.replace_words(roots, " ".join(words)) == expected
        wd, added = F.WordDictionary(), []
        for _ in range(rng.randint(0, 6)):
            w = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
            wd.add_word(w)
            added.append(w)
        for _ in range(6):
            q = "".join(rng.choice("ab.") for _ in range(rng.randint(1, 4)))
            assert wd.search(q) == any(re.fullmatch(q, w) for w in added)
        ms, ref = F.MapSum(), {}
        for _ in range(12):
            key = "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))
            if rng.random() < 0.6:
                val = rng.randint(-5, 9)
                ms.insert(key, val)
                ref[key] = val
            else:
                assert ms.sum(key) == sum(v for k, v in ref.items() if k.startswith(key))


# ----------------------------------------------------------------------------- 39f.13 graphs


def kahn_acyclic(n, edges):
    indeg = [0] * n
    out = defaultdict(list)
    for u, v in edges:
        out[u].append(v)
        indeg[v] += 1
    queue = deque(i for i in range(n) if indeg[i] == 0)
    seen = 0
    while queue:
        u = queue.popleft()
        seen += 1
        for v in out[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return seen == n


def components(n, edges):
    graph = defaultdict(set)
    for u, v in edges:
        graph[u].add(v)
        graph[v].add(u)
    label = {}
    for s in range(n):
        if s in label:
            continue
        label[s] = s
        stack = [s]
        while stack:
            u = stack.pop()
            for v in graph[u]:
                if v not in label:
                    label[v] = s
                    stack.append(v)
    return label


def t_graph_traversal():
    assert not F.is_bipartite([[1, 2, 3], [0, 2], [0, 1, 3], [0, 2]])
    assert F.is_bipartite([[1, 3], [0, 2], [1, 3], [0, 2]])
    assert F.possible_bipartition(4, [[1, 2], [1, 3], [2, 4]]) and not F.possible_bipartition(3, [[1, 2], [1, 3], [2, 3]])
    assert F.find_directed_cycle(3, [(0, 1), (1, 2)]) is None
    assert F.find_directed_cycle(3, [(0, 1), (1, 2), (2, 0)]) in ([0, 1, 2, 0], [1, 2, 0, 1], [2, 0, 1, 2])
    assert F.find_directed_cycle(1, [(0, 0)]) == [0, 0]
    for _ in range(400):
        n = rng.randint(1, 8)
        pairs = [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < 0.35]
        graph = [[] for _ in range(n)]
        for u, v in pairs:
            graph[u].append(v)
            graph[v].append(u)
        brute = any(all(c[u] != c[v] for u, v in pairs) for c in itertools.product((0, 1), repeat=n))
        assert F.is_bipartite(graph) == brute
        assert F.possible_bipartition(n, [[u + 1, v + 1] for u, v in pairs]) == brute
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 2 * n))]
        if rng.random() < 0.5:
            edges = [(u, v) for u, v in edges if u < v]         # often acyclic
        acyclic = kahn_acyclic(n, edges)
        cycle = F.find_directed_cycle(n, edges)
        assert (cycle is None) == acyclic
        if cycle:
            assert cycle[0] == cycle[-1] and len(set(cycle[:-1])) == len(cycle) - 1
            assert all((a, b) in set(edges) for a, b in zip(cycle, cycle[1:]))
        order = F.topo_sort_dfs(n, edges)
        assert (order is None) == (not acyclic)
        if order is not None:
            pos = {v: i for i, v in enumerate(order)}
            assert sorted(order) == list(range(n)) and all(pos[u] < pos[v] for u, v in edges)


def t_union_find():
    board = [list("XXXX"), list("XOOX"), list("XXOX"), list("XOXX")]
    F.solve_surrounded_regions(board)
    assert ["".join(r) for r in board] == ["XXXX", "XXXX", "XXXX", "XOXX"]
    assert not F.equations_possible(["a==b", "b!=a"]) and F.equations_possible(["b==a", "a==b"])
    assert not F.equations_possible(["a!=a"])
    for _ in range(300):
        n = rng.randint(1, 15)
        ds, edges = F.DisjointSet(), []
        for _ in range(rng.randint(0, 12)):
            u, v = rng.randrange(n), rng.randrange(n)
            label = components(n, edges)
            assert ds.union(u, v) == (label[u] != label[v])
            edges.append((u, v))
        label = components(n, edges)
        for _ in range(10):
            u, v = rng.randrange(n), rng.randrange(n)
            assert ds.connected(u, v) == (label[u] == label[v])
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        board = [[rng.choice("XO") for _ in range(cols)] for _ in range(rows)]
        expected = surrounded_reference(board)
        F.solve_surrounded_regions(board)
        assert board == expected
        letters = "abcde"
        eqs = [rng.choice(letters) + rng.choice(["==", "!="]) + rng.choice(letters) for _ in range(rng.randint(1, 6))]
        idx = {c: i for i, c in enumerate(letters)}
        label = components(5, [(idx[e[0]], idx[e[3]]) for e in eqs if e[1] == "="])
        assert F.equations_possible(eqs) == all(label[idx[e[0]]] != label[idx[e[3]]] for e in eqs if e[1] == "!")


def surrounded_reference(board):
    rows, cols = len(board), len(board[0])
    safe = set()
    stack = [(r, c) for r in range(rows) for c in range(cols)
             if (r in (0, rows - 1) or c in (0, cols - 1)) and board[r][c] == "O"]
    safe.update(stack)
    while stack:
        r, c = stack.pop()
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == "O" and (nr, nc) not in safe:
                safe.add((nr, nc))
                stack.append((nr, nc))
    return [["O" if (r, c) in safe else "X" for c in range(cols)] for r in range(rows)]


def dijkstra_all(n, edges):
    import heapq
    graph = defaultdict(list)
    for u, v, w in edges:
        graph[u].append((v, w))
    out = []
    for s in range(n):
        dist = [float("inf")] * n
        dist[s] = 0
        heap = [(0, s)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, w in graph[u]:
                if d + w < dist[v]:
                    dist[v] = d + w
                    heapq.heappush(heap, (d + w, v))
        out.append(dist)
    return out


def bfs_grid(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    if grid[start[0]][start[1]] or grid[goal[0]][goal[1]]:
        return -1, 0
    dist, queue, expanded = {start: 0}, deque([start]), 0
    while queue:
        cell = queue.popleft()
        expanded += 1
        if cell == goal:
            return dist[cell], expanded
        r, c = cell
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and not grid[nr][nc] and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[cell] + 1
                queue.append((nr, nc))
    return -1, expanded


def t_shortest_paths():
    assert abs(F.max_probability(3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.2], 0, 2) - 0.25) < 1e-12
    assert abs(F.max_probability(3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.3], 0, 2) - 0.3) < 1e-12
    assert F.max_probability(3, [[0, 1]], [0.5], 0, 2) == 0.0
    assert F.minimum_effort_path([[1, 2, 2], [3, 8, 2], [5, 3, 5]]) == 2
    assert F.minimum_effort_path([[1, 2, 3], [3, 8, 4], [5, 3, 5]]) == 1
    assert F.minimum_effort_path([[1, 2, 1, 1, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 1, 1, 2, 1]]) == 0
    flights = [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]]
    assert F.find_cheapest_price(4, flights, 0, 3, 1) == 700
    assert F.find_cheapest_price(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1) == 200
    assert F.find_cheapest_price(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0) == 500
    assert F.find_the_city(4, [[0, 1, 3], [1, 2, 1], [1, 3, 4], [2, 3, 1]], 4) == 3
    assert F.find_the_city(5, [[0, 1, 2], [0, 4, 8], [1, 2, 3], [1, 4, 2], [2, 3, 1], [3, 4, 1]], 2) == 0
    fewer = 0
    for _ in range(300):
        n = rng.randint(2, 8)
        edges = [[u, v] for u in range(n) for v in range(u + 1, n) if rng.random() < 0.4]
        probs = [rng.choice([0.1, 0.25, 0.5, 0.8, 1.0, rng.random()]) for _ in edges]
        start, end = rng.sample(range(n), 2)
        best = [0.0] * n
        best[start] = 1.0
        for _ in range(n):
            for (u, v), p in zip(edges, probs):
                best[v] = max(best[v], best[u] * p)
                best[u] = max(best[u], best[v] * p)
        assert abs(F.max_probability(n, edges, probs, start, end) - best[end]) < 1e-12
        rows, cols = rng.randint(1, 5), rng.randint(1, 5)
        heights = [[rng.randint(1, 9) for _ in range(cols)] for _ in range(rows)]
        effort = {(0, 0): 0}
        changed = True
        while changed:
            changed = False
            for r in range(rows):
                for c in range(cols):
                    if (r, c) not in effort:
                        continue
                    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        if 0 <= nr < rows and 0 <= nc < cols:
                            e = max(effort[(r, c)], abs(heights[nr][nc] - heights[r][c]))
                            if e < effort.get((nr, nc), float("inf")):
                                effort[(nr, nc)] = e
                                changed = True
        assert F.minimum_effort_path(heights) == effort[(rows - 1, cols - 1)]
        flights = [[u, v, rng.randint(1, 20)] for u in range(n) for v in range(n) if u != v and rng.random() < 0.35]
        src, dst = rng.sample(range(n), 2)
        k = rng.randint(0, n)
        cost = [float("inf")] * n                       # Bellman-Ford limited to k + 1 rounds
        cost[src] = 0
        for _ in range(k + 1):
            nxt = cost[:]
            for u, v, w in flights:
                nxt[v] = min(nxt[v], cost[u] + w)
            cost = nxt
        assert F.find_cheapest_price(n, flights, src, dst, k) == (cost[dst] if cost[dst] < float("inf") else -1)
        weighted = [(u, v, rng.randint(0, 9)) for u in range(n) for v in range(n) if u != v and rng.random() < 0.3]
        assert F.floyd_warshall(n, weighted) == dijkstra_all(n, weighted)
        dag = [(u, v, rng.randint(-5, 5)) for u in range(n) for v in range(u + 1, n) if rng.random() < 0.4]
        dist = F.floyd_warshall(n, dag)
        for s in range(n):                              # Bellman-Ford reference with negative weights
            ref = [float("inf")] * n
            ref[s] = 0
            for _ in range(n):
                for u, v, w in dag:
                    if ref[u] + w < ref[v]:
                        ref[v] = ref[u] + w
            assert dist[s] == ref
        undirected = [[u, v, rng.randint(1, 9)] for u in range(n) for v in range(u + 1, n) if rng.random() < 0.4]
        threshold = rng.randint(0, 15)
        both = dijkstra_all(n, undirected + [[v, u, w] for u, v, w in undirected])
        counts = [sum(1 for j in range(n) if j != i and both[i][j] <= threshold) for i in range(n)]
        assert F.find_the_city(n, undirected, threshold) == max(i for i in range(n) if counts[i] == min(counts))
        rows, cols = rng.randint(1, 12), rng.randint(1, 12)
        grid = [[1 if rng.random() < 0.25 else 0 for _ in range(cols)] for _ in range(rows)]
        start = (rng.randrange(rows), rng.randrange(cols))
        goal = (rng.randrange(rows), rng.randrange(cols))
        a_len, a_expanded = F.astar_grid(grid, start, goal)
        b_len, b_expanded = bfs_grid(grid, start, goal)
        assert a_len == b_len and a_expanded <= b_expanded
        fewer += a_expanded < b_expanded
    assert fewer > 100                                  # on open grids A* usually expands far fewer cells
    # The figures quoted in 39f.13.5: corner to corner of a 40 x 40 grid, open, and with a wall across row 20
    # from column 5 to the right edge (a gap of five cells on the left). Both searches are deterministic.
    open_grid = [[0] * 40 for _ in range(40)]
    walled = [[1 if r == 20 and c >= 5 else 0 for c in range(40)] for r in range(40)]
    for grid, quoted in ((open_grid, (79, 1600)), (walled, (779, 1565))):
        a_len, a_expanded = F.astar_grid(grid, (0, 0), (39, 39))
        b_len, b_expanded = bfs_grid(grid, (0, 0), (39, 39))
        assert a_len == b_len == 78 and (a_expanded, b_expanded) == quoted


def brute_mst(n, edges):
    best = None
    for combo in itertools.combinations(edges, n - 1):
        if len(set(components(n, [(u, v) for u, v, _ in combo]).values())) == 1:
            w = sum(e[2] for e in combo)
            best = w if best is None else min(best, w)
    return best if n > 1 else 0


def t_mst():
    assert F.min_cost_connect_points([[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]) == 20
    assert F.min_cost_connect_points([[3, 12], [-2, 5], [-4, 1]]) == 18
    assert F.kruskal_mst(3, [(0, 1, 1)]) is None and F.prim_mst(3, [(0, 1, 1)]) is None
    assert F.kruskal_mst(1, []) == F.prim_mst(1, []) == 0
    for _ in range(300):
        n = rng.randint(1, 6)
        edges = [(u, v, rng.randint(1, 9)) for u in range(n) for v in range(u + 1, n) if rng.random() < 0.6]
        if len(edges) > 9:
            edges = rng.sample(edges, 9)
        expected = brute_mst(n, edges)
        assert F.kruskal_mst(n, edges) == F.prim_mst(n, edges) == expected
        points = [[rng.randint(-20, 20), rng.randint(-20, 20)] for _ in range(rng.randint(1, 12))]
        complete = [(i, j, abs(points[i][0] - points[j][0]) + abs(points[i][1] - points[j][1]))
                    for i in range(len(points)) for j in range(i + 1, len(points))]
        assert F.min_cost_connect_points(points) == F.prim_mst(len(points), complete)


def brute_itinerary(tickets):
    tickets = sorted(tickets)
    used, route = [False] * len(tickets), ["JFK"]

    def dfs():
        if len(route) == len(tickets) + 1:
            return True
        for i, (a, b) in enumerate(tickets):
            if not used[i] and a == route[-1]:
                used[i] = True
                route.append(b)
                if dfs():
                    return True
                used[i] = False
                route.pop()
        return False

    dfs()
    return route


def t_euler():
    assert F.find_itinerary([["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]) == \
        ["JFK", "MUC", "LHR", "SFO", "SJC"]
    assert F.find_itinerary([["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]]) == \
        ["JFK", "ATL", "JFK", "SFO", "ATL", "SFO"]
    assert F.valid_arrangement([[5, 1], [4, 5], [11, 9], [9, 4]]) == [[11, 9], [9, 4], [4, 5], [5, 1]]
    assert F.valid_arrangement([[1, 2], [1, 3], [2, 1]]) == [[1, 2], [2, 1], [1, 3]]
    airports = ["JFK", "ATL", "SFO", "LAX", "BOS"]
    for _ in range(300):
        walk = ["JFK"]
        for _ in range(rng.randint(1, 8)):
            walk.append(rng.choice([a for a in airports if a != walk[-1]]))
        tickets = [[a, b] for a, b in zip(walk, walk[1:])]
        rng.shuffle(tickets)
        route = F.find_itinerary(tickets)
        assert route == brute_itinerary(tickets)
        assert sorted([a, b] for a, b in zip(route, route[1:])) == sorted(tickets)
        start = rng.randint(0, 5)
        walk = [start]
        for _ in range(rng.randint(1, 15)):
            walk.append(rng.randint(0, 5))
        pairs = [[a, b] for a, b in zip(walk, walk[1:])]
        rng.shuffle(pairs)
        out = F.valid_arrangement(pairs)
        assert sorted(out) == sorted(pairs) and all(out[i][1] == out[i + 1][0] for i in range(len(out) - 1))


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in globals().items() if name.startswith("t_")]
    for name, fn in tests:
        check(name[2:], fn)
    print(f"all {len(tests)} groups passed")
