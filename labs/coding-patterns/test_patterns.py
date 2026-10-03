"""Tests for patterns.py: fixed examples plus randomized checks against brute force.

Run:  python3 test_patterns.py        (standard library only; prints one line per pattern)
"""
import functools
import itertools
import random
import threading
import time

import patterns as P

rng = random.Random(39)


def check(name, fn):
    fn()
    print(f"ok  {name}")


# ----------------------------------------------------------------------------- helpers


def lst(values):
    return P.build_list(values)


def vals(head):
    return P.list_values(head)


def random_tree(n, lo=-5, hi=5):
    """Random binary tree with n nodes (values may repeat)."""
    if n == 0:
        return None
    nodes = [P.TreeNode(rng.randint(lo, hi)) for _ in range(n)]
    for i in range(1, n):
        while True:
            parent = nodes[rng.randrange(i)]
            side = rng.choice(("left", "right"))
            if getattr(parent, side) is None:
                setattr(parent, side, nodes[i])
                break
    return nodes[0]


def all_downward_paths(root):
    """Brute force for LC 437: sums of every downward path."""
    sums = []

    def starts(node):
        if node is None:
            return
        def extend(n, acc):
            if n is None:
                return
            acc += n.val
            sums.append(acc)
            extend(n.left, acc)
            extend(n.right, acc)
        extend(node, 0)
        starts(node.left)
        starts(node.right)

    starts(root)
    return sums


def tree_levels(root):
    """Reference for the BFS templates: values per depth, collected by recursion."""
    out = []

    def go(node, depth):
        if node:
            if depth == len(out):
                out.append([])
            out[depth].append(node.val)
            go(node.left, depth + 1)
            go(node.right, depth + 1)

    go(root, 0)
    return out


def leaf_paths(root):
    """Every root-to-leaf path as a list of values."""
    if root is None:
        return []
    if root.left is None and root.right is None:
        return [[root.val]]
    return [[root.val] + p for child in (root.left, root.right) for p in leaf_paths(child)]


def nodes_of(root):
    return [] if root is None else [root] + nodes_of(root.left) + nodes_of(root.right)


def path_from_root(root, target):
    """Nodes from the root down to target (inclusive), or [] if target is not in the tree."""
    if root is None:
        return []
    if root is target:
        return [root]
    below = path_from_root(root.left, target) or path_from_root(root.right, target)
    return [root] + below if below else []


def shape(root):
    return None if root is None else (root.val, shape(root.left), shape(root.right))


def regions(grid, value):
    """Reference for the island templates: 4-connected regions of cells equal to value."""
    rows, cols = len(grid), len(grid[0])
    seen, out = set(), []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == value and (r, c) not in seen:
                seen.add((r, c))
                stack, region = [(r, c)], []
                while stack:
                    x, y = stack.pop()
                    region.append((x, y))
                    for dx, dy in P.DIRS4:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == value and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                out.append(region)
    return out


# ----------------------------------------------------------------------------- 1. two pointers


def t_two_pointers():
    assert P.pair_with_target_sum([1, 2, 3, 4, 6], 6) == (1, 3)
    assert P.pair_with_target_sum([2, 5, 9, 11], 11) == (0, 2)
    assert P.pair_with_target_sum([1, 2], 10) is None
    nums = [2, 3, 3, 3, 6, 9, 9]
    n = P.remove_duplicates(nums)
    assert nums[:n] == [2, 3, 6, 9]
    assert P.remove_duplicates([]) == 0
    assert P.sorted_squares([-2, -1, 0, 2, 3]) == [0, 1, 4, 4, 9]
    assert P.sorted_squares([]) == []
    for _ in range(300):
        arr = sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 12)))
        assert P.sorted_squares(arr) == sorted(x * x for x in arr)
        brute = sorted({tuple(sorted(c)) for c in itertools.combinations(arr, 3) if sum(c) == 0})
        assert sorted(tuple(t) for t in P.three_sum(arr)) == brute
        colors = [rng.randint(0, 2) for _ in range(rng.randint(0, 15))]
        expected = sorted(colors)
        P.sort_colors(colors)
        assert colors == expected
        if len(arr) >= 2:
            i, j = sorted(rng.sample(range(len(arr)), 2))
            got = P.pair_with_target_sum(arr, arr[i] + arr[j])
            assert got is not None and got[0] < got[1] and arr[got[0]] + arr[got[1]] == arr[i] + arr[j]
        target = rng.randint(-41, 41)
        exists = any(a + b == target for a, b in itertools.combinations(arr, 2))
        assert (P.pair_with_target_sum(arr, target) is not None) == exists
        deduped = arr[:]
        assert deduped[:P.remove_duplicates(deduped)] == sorted(set(arr))


# ----------------------------------------------------------------------------- 2. islands


def t_islands():
    grid = [list(r) for r in ["11000", "11000", "00100", "00011"]]
    assert P.num_islands(grid) == 3
    assert P.num_islands([]) == 0
    area = [[0, 0, 1, 0], [1, 1, 1, 0], [0, 0, 0, 1], [1, 1, 0, 1]]
    assert P.max_area_of_island([row[:] for row in area]) == 4
    img = [[1, 1, 1], [1, 1, 0], [1, 0, 1]]
    assert P.flood_fill(img, 1, 1, 2) == [[2, 2, 2], [2, 2, 0], [2, 0, 1]]
    assert P.flood_fill([[0, 0, 0], [0, 0, 0]], 0, 0, 0) == [[0, 0, 0], [0, 0, 0]]
    closed = [[1, 1, 1, 1, 1, 1, 1, 0], [1, 0, 0, 0, 0, 1, 1, 0], [1, 0, 1, 0, 1, 1, 1, 0],
              [1, 0, 0, 0, 0, 1, 0, 1], [1, 1, 1, 1, 1, 1, 1, 0]]
    assert P.closed_island(closed) == 2
    for _ in range(300):
        rows, cols = rng.randint(1, 7), rng.randint(1, 7)
        grid = [[rng.randint(0, 1) for _ in range(cols)] for _ in range(rows)]
        land = regions(grid, 1)
        assert P.num_islands([["1" if v else "0" for v in row] for row in grid]) == len(land)
        assert P.max_area_of_island([row[:] for row in grid]) == max(map(len, land), default=0)
        inner = [g for g in regions(grid, 0) if all(0 < x < rows - 1 and 0 < y < cols - 1 for x, y in g)]
        assert P.closed_island([row[:] for row in grid]) == len(inner)
        image = [[rng.randint(0, 2) for _ in range(cols)] for _ in range(rows)]
        sr, sc, color = rng.randrange(rows), rng.randrange(cols), rng.randint(0, 2)
        expected = [row[:] for row in image]
        for x, y in next(g for g in regions(image, image[sr][sc]) if (sr, sc) in g):
            expected[x][y] = color
        assert P.flood_fill(image, sr, sc, color) == expected


# ----------------------------------------------------------------------------- 3. fast and slow


def t_fast_slow():
    head = lst([1, 2, 3, 4, 5, 6])
    assert not P.has_cycle(head)
    tail = head
    while tail.next:
        tail = tail.next
    third = head.next.next
    tail.next = third
    assert P.has_cycle(head)
    assert P.cycle_start(head) is third
    tail.next = None
    assert P.cycle_start(head) is None
    assert P.middle_node(lst([1, 2, 3, 4, 5])).val == 3
    assert P.middle_node(lst([1, 2, 3, 4, 5, 6])).val == 4
    for values, expected in [([1, 2, 2, 1], True), ([1, 2, 3, 2, 1], True), ([1, 2], False), ([1], True), ([], True)]:
        h = lst(values)
        assert P.is_palindrome_list(h) == expected
        assert vals(h) == values, "the list must be restored"
    assert P.is_happy(19) and not P.is_happy(2) and P.is_happy(1)
    for n in range(1, 1000):
        seen, x = set(), n
        while x != 1 and x not in seen:
            seen.add(x)
            x = sum(int(d) ** 2 for d in str(x))
        assert P.is_happy(n) == (x == 1)
    for _ in range(200):
        n = rng.randint(1, 10)
        dup = rng.randint(1, n)
        arr = list(range(1, n + 1)) + [dup]
        rng.shuffle(arr)
        assert P.find_duplicate(arr) == dup
        nodes = [P.ListNode(rng.randint(0, 3)) for _ in range(rng.randint(0, 12))]
        for a, b in zip(nodes, nodes[1:]):
            a.next = b
        entry = rng.choice(nodes) if nodes and rng.random() < 0.5 else None
        if entry:
            nodes[-1].next = entry
        head = nodes[0] if nodes else None
        assert P.has_cycle(head) == (entry is not None) and P.cycle_start(head) is entry
        if nodes and entry is None:
            assert P.middle_node(head) is nodes[len(nodes) // 2]
        values = [rng.randint(0, 2) for _ in range(rng.randint(0, 8))]
        h = lst(values)
        assert P.is_palindrome_list(h) == (values == values[::-1]) and vals(h) == values


# ----------------------------------------------------------------------------- 4. sliding window


def brute_longest(seq, ok):
    best = 0
    for i in range(len(seq)):
        for j in range(i, len(seq)):
            if ok(seq[i:j + 1]):
                best = max(best, j - i + 1)
    return best


def t_sliding_window():
    assert P.max_sum_subarray_k([2, 1, 5, 1, 3, 2], 3) == 9
    assert P.min_subarray_len(7, [2, 3, 1, 2, 4, 3]) == 2
    assert P.min_subarray_len(100, [1, 2]) == 0
    assert P.longest_with_k_distinct("araaci", 2) == 4
    assert P.longest_with_k_distinct([1, 2, 1], 2) == 3          # Fruit Into Baskets
    assert P.length_of_longest_substring("abcabcbb") == 3
    assert P.length_of_longest_substring("") == 0
    assert P.character_replacement("AABABBA", 1) == 4
    assert P.find_anagrams("cbaebabacd", "abc") == [0, 6]
    assert P.min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert P.min_window("a", "aa") == ""
    for _ in range(300):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 12)))
        k = rng.randint(1, 3)
        assert P.longest_with_k_distinct(s, k) == brute_longest(s, lambda w: len(set(w)) <= k)
        assert P.length_of_longest_substring(s) == brute_longest(s, lambda w: len(set(w)) == len(w))
        assert P.character_replacement(s, k) == brute_longest(
            s, lambda w: len(w) - max(w.count(c) for c in set(w)) <= k)
        nums = [rng.randint(-5, 9) for _ in range(rng.randint(1, 10))]
        kk = rng.randint(1, len(nums))
        assert P.max_sum_subarray_k(nums, kk) == max(sum(nums[i:i + kk]) for i in range(len(nums) - kk + 1))
        pos = [rng.randint(1, 6) for _ in range(rng.randint(0, 10))]
        target = rng.randint(1, 20)
        lengths = [j - i + 1 for i in range(len(pos)) for j in range(i, len(pos)) if sum(pos[i:j + 1]) >= target]
        assert P.min_subarray_len(target, pos) == (min(lengths) if lengths else 0)
        t = "".join(rng.choice("abc") for _ in range(rng.randint(1, 3)))
        assert P.find_anagrams(s, t) == [i for i in range(len(s) - len(t) + 1) if sorted(s[i:i + len(t)]) == sorted(t)]
        need = {c: t.count(c) for c in t}
        windows = [s[i:j + 1] for i in range(len(s)) for j in range(i, len(s))
                   if all(s[i:j + 1].count(c) >= n for c, n in need.items())]
        got = P.min_window(s, t)
        if windows:
            assert len(got) == min(map(len, windows)) and all(got.count(c) >= n for c, n in need.items())
        else:
            assert got == ""


# ----------------------------------------------------------------------------- 5. merge intervals


def covered(intervals):
    points = set()
    for a, b in intervals:
        points.update(x / 2 for x in range(2 * a, 2 * b + 1))
    return points


def t_intervals():
    assert P.merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert P.merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert P.insert_interval([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert P.insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [[1, 2], [3, 10], [12, 16]]
    assert P.interval_intersection([[0, 2], [5, 10], [13, 23], [24, 25]],
                                   [[1, 5], [8, 12], [15, 24], [25, 26]]) == [
        [1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]
    assert P.min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert P.min_meeting_rooms([[7, 10], [2, 4]]) == 1
    assert P.min_meeting_rooms([[1, 5], [5, 9]]) == 1
    for _ in range(300):
        ivs = []
        for _ in range(rng.randint(0, 8)):
            a = rng.randint(0, 20)
            ivs.append([a, a + rng.randint(0, 6)])
        merged = P.merge_intervals([iv[:] for iv in ivs])
        assert covered(merged) == covered(ivs)
        assert all(merged[i][1] < merged[i + 1][0] for i in range(len(merged) - 1))
        new = [rng.randint(0, 20), 0]
        new[1] = new[0] + rng.randint(0, 6)
        assert P.insert_interval(P.merge_intervals([iv[:] for iv in ivs]), new[:]) == P.merge_intervals(
            [iv[:] for iv in ivs] + [new[:]])
        meetings = [[a, b] for a, b in ivs if a < b]
        busiest = max((sum(1 for a, b in meetings if a <= t < b) for t in range(0, 30)), default=0)
        assert P.min_meeting_rooms(meetings) == busiest
        lists = []
        for _ in range(2):                       # LC 986 input: sorted, pairwise disjoint closed intervals
            cur, one = rng.randint(0, 3), []
            for _ in range(rng.randint(0, 4)):
                one.append([cur, cur + rng.randint(0, 4)])
                cur = one[-1][1] + rng.randint(1, 4)
            lists.append(one)
        a_list, b_list = lists
        pairwise = sorted([max(a[0], b[0]), min(a[1], b[1])] for a in a_list for b in b_list
                          if max(a[0], b[0]) <= min(a[1], b[1]))
        assert P.interval_intersection(a_list, b_list) == pairwise


# ----------------------------------------------------------------------------- 6. cyclic sort


def t_cyclic_sort():
    assert P.cyclic_sort([3, 1, 5, 4, 2]) == [1, 2, 3, 4, 5]
    assert P.missing_number([4, 0, 3, 1]) == 2
    assert P.missing_number([0, 1]) == 2
    assert P.find_disappeared_numbers([4, 3, 2, 7, 8, 2, 3, 1]) == [5, 6]
    assert sorted(P.find_all_duplicates([4, 3, 2, 7, 8, 2, 3, 1])) == [2, 3]
    assert P.first_missing_positive([3, 4, -1, 1]) == 2
    assert P.first_missing_positive([7, 8, 9, 11, 12]) == 1
    assert P.first_missing_positive([1, 2, 0]) == 3
    for _ in range(300):
        n = rng.randint(1, 12)
        perm = list(range(1, n + 1))
        rng.shuffle(perm)
        assert P.cyclic_sort(perm[:]) == list(range(1, n + 1))
        gone = rng.randint(0, n)
        arr = [x for x in range(n + 1) if x != gone]
        rng.shuffle(arr)
        assert P.missing_number(arr[:]) == gone == P.missing_number_xor(arr)
        arr = [rng.randint(1, n) for _ in range(n)]
        assert P.find_disappeared_numbers(arr[:]) == sorted(set(range(1, n + 1)) - set(arr))
        counts = {}
        for x in arr:
            counts[x] = counts.get(x, 0) + 1
        if max(counts.values()) <= 2:
            assert sorted(P.find_all_duplicates(arr[:])) == sorted(x for x, c in counts.items() if c == 2)
        arr = [rng.randint(-3, n + 2) for _ in range(n)]
        smallest = 1
        while smallest in arr:
            smallest += 1
        assert P.first_missing_positive(arr[:]) == smallest


# ----------------------------------------------------------------------------- 7. in-place reversal


def t_reversal():
    assert vals(P.reverse_list(lst([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert vals(P.reverse_list(None)) == []
    assert vals(P.reverse_between(lst([1, 2, 3, 4, 5]), 2, 4)) == [1, 4, 3, 2, 5]
    assert vals(P.reverse_k_group(lst([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert vals(P.rotate_right(lst([1, 2, 3, 4, 5]), 2)) == [4, 5, 1, 2, 3]
    for _ in range(300):
        values = [rng.randint(0, 9) for _ in range(rng.randint(1, 10))]
        assert vals(P.reverse_list(lst(values))) == values[::-1]
        n = len(values)
        a = rng.randint(1, n)
        b = rng.randint(a, n)
        assert vals(P.reverse_between(lst(values), a, b)) == values[:a - 1] + values[a - 1:b][::-1] + values[b:]
        k = rng.randint(1, n + 1)
        expected = []
        for i in range(0, n, k):
            block = values[i:i + k]
            expected += block[::-1] if len(block) == k else block
        assert vals(P.reverse_k_group(lst(values), k)) == expected
        r = rng.randint(0, 25)
        expected = values[-(r % n):] + values[:-(r % n)] if r % n else values
        assert vals(P.rotate_right(lst(values), r)) == expected


# ----------------------------------------------------------------------------- 8. tree BFS


def t_tree_bfs():
    root = P.build_tree([3, 9, 20, None, None, 15, 7])
    assert P.level_order(root) == [[3], [9, 20], [15, 7]]
    assert P.level_order_bottom(root) == [[15, 7], [9, 20], [3]]
    assert P.zigzag_level_order(root) == [[3], [20, 9], [15, 7]]
    assert P.right_side_view(P.build_tree([1, 2, 3, None, 5, None, 4])) == [1, 3, 4]
    assert P.min_depth(root) == 2
    assert P.min_depth(P.build_tree([2, None, 3, None, 4, None, 5, None, 6])) == 5
    assert P.level_order(None) == [] and P.min_depth(None) == 0
    for _ in range(300):
        tree = random_tree(rng.randint(0, 12))
        levels = tree_levels(tree)
        assert P.level_order(tree) == levels and P.level_order_bottom(tree) == levels[::-1]
        assert P.zigzag_level_order(tree) == [lv if d % 2 == 0 else lv[::-1] for d, lv in enumerate(levels)]
        assert P.right_side_view(tree) == [lv[-1] for lv in levels]
        assert P.min_depth(tree) == min(map(len, leaf_paths(tree)), default=0)


# ----------------------------------------------------------------------------- 9. tree DFS


def t_tree_dfs():
    root = P.build_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1])
    assert P.has_path_sum(root, 22)
    assert not P.has_path_sum(root, 1000)
    assert sorted(P.path_sum_all(root, 22)) == [[5, 4, 11, 2], [5, 8, 4, 5]]
    assert P.count_paths_with_sum(P.build_tree([10, 5, -3, 3, 2, None, 11, 3, -2, None, 1]), 8) == 3
    assert P.max_path_sum(P.build_tree([-10, 9, 20, None, None, 15, 7])) == 42
    assert P.max_path_sum(P.build_tree([-3])) == -3
    assert P.diameter_of_binary_tree(P.build_tree([1, 2, 3, 4, 5])) == 3
    t = P.build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    p, q = t.left, t.left.right.right            # 5 and 4
    assert P.lowest_common_ancestor(t, p, q) is p
    for _ in range(200):
        tree = random_tree(rng.randint(0, 12))
        target = rng.randint(-6, 6)
        assert P.count_paths_with_sum(tree, target) == sum(1 for s in all_downward_paths(tree) if s == target)
        paths = leaf_paths(tree)
        assert P.has_path_sum(tree, target) == any(sum(p) == target for p in paths)
        assert sorted(P.path_sum_all(tree, target)) == sorted(p for p in paths if sum(p) == target)
        nodes = nodes_of(tree)
        if not nodes:
            continue
        best, longest = float("-inf"), 0
        for a in nodes:                          # every node-to-node path goes up to the LCA and down
            for b in nodes:
                pa, pb = path_from_root(tree, a), path_from_root(tree, b)
                common = sum(1 for x, y in zip(pa, pb) if x is y)
                path = pa[common - 1:] + pb[common:]
                best, longest = max(best, sum(n.val for n in path)), max(longest, len(path) - 1)
                assert P.lowest_common_ancestor(tree, a, b) is pa[common - 1]
        assert P.max_path_sum(tree) == best and P.diameter_of_binary_tree(tree) == longest


# ----------------------------------------------------------------------------- 10. two heaps


def t_two_heaps():
    mf = P.MedianFinder()
    seen = []
    for _ in range(200):
        x = rng.randint(-50, 50)
        mf.add_num(x)
        seen.append(x)
        s = sorted(seen)
        m = len(s)
        expected = float(s[m // 2]) if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2
        assert mf.find_median() == expected
    assert P.median_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]
    for _ in range(300):
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(1, 15))]
        k = rng.randint(1, len(nums))
        expected = []
        for i in range(len(nums) - k + 1):
            w = sorted(nums[i:i + k])
            expected.append(float(w[k // 2]) if k % 2 else (w[k // 2 - 1] + w[k // 2]) / 2)
        assert P.median_sliding_window(nums, k) == expected
    assert P.find_maximized_capital(2, 0, [1, 2, 3], [0, 1, 1]) == 4
    assert P.find_maximized_capital(3, 0, [1, 2, 3], [0, 1, 2]) == 6
    assert P.find_maximized_capital(1, 0, [5], [1]) == 0
    for _ in range(200):
        n = rng.randint(1, 5)
        profits = [rng.randint(0, 5) for _ in range(n)]
        capital = [rng.randint(0, 6) for _ in range(n)]
        k, w = rng.randint(1, n), rng.randint(0, 3)

        def brute(taken, cash, left):            # try every order of at most k affordable projects
            options = [i for i in range(n) if i not in taken and capital[i] <= cash]
            if left == 0 or not options:
                return cash
            return max(brute(taken | {i}, cash + profits[i], left - 1) for i in options)

        assert P.find_maximized_capital(k, w, profits, capital) == brute(frozenset(), w, k)


# ----------------------------------------------------------------------------- 11. subsets


def t_subsets():
    for _ in range(100):
        nums = rng.sample(range(10), rng.randint(0, 5))
        assert sorted(map(sorted, P.subsets(nums))) == sorted(
            sorted(c) for r in range(len(nums) + 1) for c in itertools.combinations(nums, r))
        assert sorted(map(tuple, P.permutations(nums))) == sorted(itertools.permutations(nums))
        dup = [rng.randint(0, 2) for _ in range(rng.randint(0, 6))]
        got = sorted(map(tuple, (sorted(s) for s in P.subsets_with_dup(dup))))
        expected = sorted({tuple(sorted(c)) for r in range(len(dup) + 1) for c in itertools.combinations(dup, r)})
        assert got == expected
    assert sorted(P.letter_case_permutation("a1b2")) == sorted(["a1b2", "a1B2", "A1b2", "A1B2"])
    assert P.letter_case_permutation("12") == ["12"]
    for _ in range(100):
        s = "".join(rng.choice("aB1c") for _ in range(rng.randint(0, 5)))
        choices = [(ch.lower(), ch.upper()) if ch.isalpha() else (ch,) for ch in s]
        assert sorted(P.letter_case_permutation(s)) == sorted("".join(p) for p in itertools.product(*choices))


# ----------------------------------------------------------------------------- 12. binary search


def t_binary_search():
    from bisect import bisect_left
    assert P.order_agnostic_search([10, 6, 4], 10) == 0
    assert P.order_agnostic_search([1, 2, 3, 4, 5], 5) == 4
    assert P.order_agnostic_search([4], 3) == -1
    assert P.ceiling_index([4, 6, 10], 6) == 1 and P.ceiling_index([4, 6, 10], 17) == -1
    assert P.next_greatest_letter(["c", "f", "j"], "a") == "c"
    assert P.next_greatest_letter(["c", "f", "j"], "c") == "f"
    assert P.next_greatest_letter(["c", "f", "j"], "j") == "c"
    assert P.search_range([5, 7, 7, 8, 8, 10], 8) == [3, 4]
    assert P.search_range([5, 7, 7, 8, 8, 10], 6) == [-1, -1]
    assert P.search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert P.find_min_rotated([3, 4, 5, 1, 2]) == 1
    assert P.peak_index_in_mountain([0, 2, 5, 3, 1]) == 2
    assert P.min_eating_speed([3, 6, 7, 11], 8) == 4
    assert P.min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    for _ in range(500):
        arr = sorted(rng.randint(0, 20) for _ in range(rng.randint(0, 12)))
        t = rng.randint(-2, 22)
        assert P.lower_bound(arr, t) == bisect_left(arr, t)
        for seq in (arr, arr[::-1]):
            i = P.order_agnostic_search(seq, t)
            assert (i == -1 and t not in seq) or seq[i] == t
        at_least = [i for i, v in enumerate(arr) if v >= t]
        assert P.ceiling_index(arr, t) == (at_least[0] if at_least else -1)
        hits = [i for i, v in enumerate(arr) if v == t]
        assert P.search_range(arr, t) == ([hits[0], hits[-1]] if hits else [-1, -1])
        letters = sorted(rng.choice("bdfh") for _ in range(rng.randint(2, 6)))
        probe = rng.choice("abcdefghi")
        assert P.next_greatest_letter(letters, probe) == next((x for x in letters if x > probe), letters[0])
        peak = rng.randint(1, 6)
        up = sorted(rng.sample(range(50), peak + 1))
        mountain = up + sorted(rng.sample(range(up[-1]), rng.randint(1, min(5, up[-1]))), reverse=True)
        assert P.peak_index_in_mountain(mountain) == peak
        distinct = sorted(set(arr))
        if distinct:
            r = rng.randrange(len(distinct))
            rotated = distinct[r:] + distinct[:r]
            assert P.search_rotated(rotated, t) == (rotated.index(t) if t in rotated else -1)
            assert P.find_min_rotated(rotated) == min(rotated)
        piles = [rng.randint(1, 30) for _ in range(rng.randint(1, 6))]
        h = rng.randint(len(piles), 40)
        speed = next(s for s in range(1, 31) if sum(-(-p // s) for p in piles) <= h)
        assert P.min_eating_speed(piles, h) == speed


# ----------------------------------------------------------------------------- 13. top K


def t_top_k():
    assert P.kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert sorted(P.top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    stream = P.KthLargest(3, [4, 5, 8, 2])
    assert [stream.add(x) for x in (3, 5, 10, 9, 4)] == [4, 5, 5, 8, 8]
    assert P.k_closest_points([[1, 3], [-2, 2]], 1) == [[-2, 2]]
    strings = ["aab", "aaab", "vvvlo", "", "a"] + ["".join(rng.choice("aabbc") for _ in range(rng.randint(0, 9)))
                                                     for _ in range(300)]
    for s in strings:
        out = P.reorganize_string(s)
        possible = not s or max(s.count(c) for c in set(s)) <= (len(s) + 1) // 2
        if possible:
            assert sorted(out) == sorted(s) and all(out[i] != out[i + 1] for i in range(len(out) - 1))
        else:
            assert out == ""
    for _ in range(300):
        nums = [rng.randint(-10, 10) for _ in range(rng.randint(1, 15))]
        k = rng.randint(1, len(nums))
        assert P.kth_largest(nums, k) == sorted(nums, reverse=True)[k - 1]
        stream = P.KthLargest(k, nums[:k - 1])
        seen = nums[:k - 1]
        for x in nums[k - 1:]:
            seen.append(x)
            assert stream.add(x) == sorted(seen, reverse=True)[k - 1]
        points = [[rng.randint(-5, 5), rng.randint(-5, 5)] for _ in range(len(nums))]
        dist = sorted(x * x + y * y for x, y in points)
        assert sorted(x * x + y * y for x, y in P.k_closest_points(points, k)) == dist[:k]
        counts = {x: nums.count(x) for x in set(nums)}
        kk = rng.randint(1, len(counts))
        top = P.top_k_frequent(nums, kk)
        threshold = sorted(counts.values(), reverse=True)[kk - 1]
        assert len(top) == kk and all(counts[x] >= threshold for x in top)


# ----------------------------------------------------------------------------- 14. XOR


def t_xor():
    assert P.single_number([4, 1, 2, 1, 2]) == 4
    assert P.single_number_iii([1, 2, 1, 3, 2, 5]) == [3, 5]
    assert P.bitwise_complement(5) == 2 and P.bitwise_complement(0) == 1 and P.bitwise_complement(10) == 5
    for n in range(2000):
        assert P.bitwise_complement(n) == int(bin(n)[2:].translate(str.maketrans("01", "10")), 2)
    for _ in range(200):
        a, b = rng.sample(range(-50, 50), 2)
        pairs = rng.sample([x for x in range(-50, 50) if x not in (a, b)], 5)
        arr = pairs * 2 + [a, b]
        rng.shuffle(arr)
        assert P.single_number_iii(arr) == sorted([a, b])
        assert P.single_number(pairs * 2 + [a]) == a


# ----------------------------------------------------------------------------- 15. backtracking


def t_backtracking():
    assert sorted(P.generate_parentheses(3)) == sorted(["((()))", "(()())", "(())()", "()(())", "()()()"])
    assert len(P.generate_parentheses(5)) == 42                       # Catalan number C5
    assert P.combination_sum([2, 3, 6, 7], 7) == [[2, 2, 3], [7]]
    assert P.combination_sum([2], 1) == []
    assert sorted(P.factor_combinations(12)) == [[2, 2, 3], [2, 6], [3, 4]]
    assert P.factor_combinations(1) == [] and P.factor_combinations(37) == []
    assert len(P.factor_combinations(32)) == 6
    board = [list("ABCE"), list("SFCS"), list("ADEE")]
    assert P.word_exists(board, "ABCCED") and P.word_exists(board, "SEE") and not P.word_exists(board, "ABCB")
    assert [P.total_n_queens(n) for n in range(1, 9)] == [1, 0, 0, 2, 10, 4, 40, 92]
    for n in range(6):
        balanced = [s for s in map("".join, itertools.product("()", repeat=2 * n))
                    if all(s[:i].count("(") >= s[:i].count(")") for i in range(2 * n + 1)) and s.count("(") == n]
        assert sorted(P.generate_parentheses(n)) == balanced
    for n in range(1, 200):
        def splits(m, smallest):                 # brute force: every non-decreasing factorization
            return [[m]] + [[f] + rest for f in range(smallest, m) if m % f == 0 for rest in splits(m // f, f)
                            if rest[0] >= f]
        assert sorted(P.factor_combinations(n)) == sorted(s for s in splits(n, 2) if len(s) > 1)
    for _ in range(200):
        candidates, target = rng.sample(range(1, 9), rng.randint(1, 4)), rng.randint(1, 15)
        brute = {tuple(sorted(c)) for r in range(1, target + 1)
                 for c in itertools.combinations_with_replacement(candidates, r) if sum(c) == target}
        assert sorted(map(tuple, P.combination_sum(candidates, target))) == sorted(brute)
        rows, cols = rng.randint(1, 3), rng.randint(1, 3)
        grid = [[rng.choice("ab") for _ in range(cols)] for _ in range(rows)]
        word = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
        cells = [(r, c) for r in range(rows) for c in range(cols)]
        brute = any(all(grid[r][c] == ch for (r, c), ch in zip(path, word)) and
                    all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))
                    for path in itertools.permutations(cells, len(word)))
        assert P.word_exists([row[:] for row in grid], word) == brute
    puzzles = ["53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
               # two puzzles that take cell-by-cell backtracking 10-50 s in CPython; MRV needs well under 1 s
               "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9",
               "...8.1..........435............7.8........1...2..3....6......75..34........2..6.."]
    for puzzle in puzzles:
        grid = [list(puzzle[r * 9:r * 9 + 9]) for r in range(9)]
        start = time.perf_counter()
        assert P.solve_sudoku(grid)
        assert time.perf_counter() - start < 10, "most-constrained-cell ordering should keep this fast"
        digits = list("123456789")
        assert all(sorted(row) == digits for row in grid)
        assert all(sorted(grid[r][c] for r in range(9)) == digits for c in range(9))
        assert all(sorted(grid[br + i][bc + j] for i in range(3) for j in range(3)) == digits
                   for br in (0, 3, 6) for bc in (0, 3, 6))
        assert all(puzzle[i] in (".", grid[i // 9][i % 9]) for i in range(81))


# ----------------------------------------------------------------------------- 16. knapsack


def t_knapsack():
    assert P.knapsack_01([1, 2, 3, 5], [1, 6, 10, 16], 7) == 22
    assert P.can_partition([1, 5, 11, 5]) and not P.can_partition([1, 2, 3, 5])
    assert P.find_target_sum_ways([1, 1, 1, 1, 1], 3) == 5
    assert P.find_target_sum_ways([0, 0, 1], 1) == 4
    assert P.min_subset_sum_difference([1, 2, 3, 9]) == 3
    assert P.coin_change([1, 2, 5], 11) == 3 and P.coin_change([2], 3) == -1 and P.coin_change([1], 0) == 0
    for _ in range(300):
        n = rng.randint(0, 7)
        w = [rng.randint(1, 6) for _ in range(n)]
        v = [rng.randint(0, 10) for _ in range(n)]
        cap = rng.randint(0, 15)
        best = max(sum(v[i] for i in s) for r in range(n + 1) for s in itertools.combinations(range(n), r)
                   if sum(w[i] for i in s) <= cap)
        assert P.knapsack_01(w, v, cap) == best
        nums = [rng.randint(0, 6) for _ in range(rng.randint(0, 7))]
        sums = [sum(s) for r in range(len(nums) + 1) for s in itertools.combinations(nums, r)]
        total = sum(nums)
        assert P.can_partition(nums) == (total % 2 == 0 and total // 2 in sums)
        assert P.min_subset_sum_difference(nums) == min(abs(total - 2 * s) for s in sums)
        target = rng.randint(-8, 8)
        brute = sum(1 for signs in itertools.product((1, -1), repeat=len(nums))
                    if sum(s * x for s, x in zip(signs, nums)) == target)
        assert P.find_target_sum_ways(nums, target) == brute
        assert P.count_subsets_with_sum(nums, abs(target)) == sums.count(abs(target))
        coins = rng.sample(range(1, 8), rng.randint(1, 3))
        amount = rng.randint(0, 20)
        fewest = -1
        for count in range(0, amount + 1):
            if any(sum(c) == amount for c in itertools.combinations_with_replacement(coins, count)):
                fewest = count
                break
        assert P.coin_change(coins, amount) == fewest


# ----------------------------------------------------------------------------- 17. topological sort


def valid_order(order, n, edges):
    pos = {u: i for i, u in enumerate(order)}
    return sorted(order) == list(range(n)) and all(pos[u] < pos[v] for u, v in edges)


def t_topological():
    assert P.can_finish(2, [[1, 0]]) and not P.can_finish(2, [[1, 0], [0, 1]])
    assert P.find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]]) in ([0, 1, 2, 3], [0, 2, 1, 3])
    assert P.find_order(2, [[0, 1], [1, 0]]) == []
    assert P.can_finish(0, [])
    assert P.alien_order(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"
    assert P.alien_order(["z", "x", "z"]) == ""
    assert P.alien_order(["abc", "ab"]) == ""
    assert P.find_min_height_trees(4, [[1, 0], [1, 2], [1, 3]]) == [1]
    assert P.find_min_height_trees(6, [[3, 0], [3, 1], [3, 2], [3, 4], [5, 4]]) == [3, 4]
    for _ in range(100):
        n = rng.randint(1, 6)
        perm = list(range(n))
        rng.shuffle(perm)
        edges = list({(perm[i], perm[j]) for i in range(n) for j in range(i + 1, n) if rng.random() < 0.3})
        order = P.topological_order(n, edges)
        assert order is not None and valid_order(order, n, edges)
        everything = P.all_topological_orders(n, edges)
        brute = [list(p) for p in itertools.permutations(range(n)) if valid_order(list(p), n, edges)]
        assert sorted(everything) == sorted(brute)
        if edges:
            u, v = edges[0]
            assert P.topological_order(n, edges + [(v, u)]) is None
    for _ in range(300):
        alphabet = rng.sample("abcde", rng.randint(1, 5))
        words = ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(1, 5))]
        if rng.random() < 0.7:                   # usually a dictionary sorted in a hidden order
            words.sort(key=lambda w: [alphabet.index(ch) for ch in w])
        letters = {ch for w in words for ch in w}

        def sorted_under(order):
            return len(order) == len(letters) and set(order) == letters and all(
                [order.index(ch) for ch in a] <= [order.index(ch) for ch in b] for a, b in zip(words, words[1:]))

        got = P.alien_order(words)
        assert sorted_under(got) if any(map(sorted_under, itertools.permutations(letters))) else got == ""
        n = rng.randint(1, 9)
        tree_edges = [[i, rng.randrange(i)] for i in range(1, n)]
        adjacency = {i: [] for i in range(n)}
        for a, b in tree_edges:
            adjacency[a].append(b)
            adjacency[b].append(a)

        def height(root):
            depth, frontier = 0, [root]
            seen = {root}
            while True:
                frontier = [v for u in frontier for v in adjacency[u] if v not in seen and not seen.add(v)]
                if not frontier:
                    return depth
                depth += 1

        heights = [height(r) for r in range(n)]
        assert P.find_min_height_trees(n, tree_edges) == [r for r in range(n) if heights[r] == min(heights)]


# ----------------------------------------------------------------------------- 18. K-way merge


def t_k_way_merge():
    merged = P.merge_k_lists([lst([1, 4, 5]), lst([1, 3, 4]), lst([2, 6]), None])
    assert vals(merged) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert P.merge_k_lists([]) is None
    assert P.kth_smallest_in_matrix([[1, 5, 9], [10, 11, 13], [12, 13, 15]], 8) == 13
    assert P.smallest_range([[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]) == [20, 24]
    for _ in range(200):
        lists = [sorted(rng.randint(0, 30) for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 4))]
        flat = sorted(x for row in lists for x in row)
        k = rng.randint(1, len(flat))
        assert P.kth_smallest_in_sorted_lists(lists, k) == flat[k - 1]
        assert vals(P.merge_k_lists([lst(row) for row in lists])) == flat
        n = rng.randint(1, 5)                    # LC 378: rows and columns both sorted
        matrix = [[0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                matrix[r][c] = max(matrix[r - 1][c] if r else 0, matrix[r][c - 1] if c else 0) + rng.randint(0, 3)
        kk = rng.randint(1, n * n)
        assert P.kth_smallest_in_matrix(matrix, kk) == sorted(x for row in matrix for x in row)[kk - 1]
        best = None
        for a in flat:
            for b in flat:
                if a <= b and all(any(a <= x <= b for x in row) for row in lists):
                    if best is None or (b - a, a) < (best[1] - best[0], best[0]):
                        best = [a, b]
        assert P.smallest_range(lists) == best


# ----------------------------------------------------------------------------- 19. monotonic stack


def t_monotonic():
    assert P.next_greater_element_i([4, 1, 2], [1, 3, 4, 2]) == [-1, 3, -1]
    assert P.next_greater_circular([1, 2, 1]) == [2, -1, 2]
    assert P.daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert P.largest_rectangle_area([2, 1, 5, 6, 2, 3]) == 10
    assert P.trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert P.max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    for _ in range(300):
        a = [rng.randint(0, 9) for _ in range(rng.randint(1, 12))]
        n = len(a)
        assert P.next_greater_elements(a) == [next((a[j] for j in range(i + 1, n) if a[j] > a[i]), -1) for i in range(n)]
        assert P.next_smaller_elements(a) == [next((a[j] for j in range(i + 1, n) if a[j] < a[i]), -1) for i in range(n)]
        assert P.next_greater_circular(a) == [next((a[(i + d) % n] for d in range(1, n) if a[(i + d) % n] > a[i]), -1)
                                              for i in range(n)]
        assert P.largest_rectangle_area(a) == max(min(a[i:j + 1]) * (j - i + 1) for i in range(n) for j in range(i, n))
        assert P.trap(a) == sum(max(0, min(max(a[:i + 1]), max(a[i:])) - a[i]) for i in range(n))
        k = rng.randint(1, n)
        assert P.max_sliding_window(a, k) == [max(a[i:i + k]) for i in range(n - k + 1)]
        assert P.daily_temperatures(a) == [next((j - i for j in range(i + 1, n) if a[j] > a[i]), 0) for i in range(n)]
        nums2 = rng.sample(range(20), n)
        nums1 = rng.sample(nums2, rng.randint(1, n))
        assert P.next_greater_element_i(nums1, nums2) == [
            next((y for y in nums2[nums2.index(x) + 1:] if y > x), -1) for x in nums1]


# ----------------------------------------------------------------------------- 20. multi-threaded


def t_threads():
    root = P.build_tree([4, 2, 7, 1, 3, 6, 9])
    assert P.level_order(P.invert_tree_parallel(root)) == [[4], [7, 2], [9, 6, 3, 1]]
    assert P.invert_tree_parallel(None) is None

    def mirrored(t):
        return None if t is None else (t[0], mirrored(t[2]), mirrored(t[1]))

    for _ in range(50):
        tree = random_tree(rng.randint(0, 12))
        expected = mirrored(shape(tree))
        assert shape(P.invert_tree(tree)) == expected
        assert shape(P.invert_tree_parallel(P.invert_tree(tree))) == expected
    for _ in range(20):
        out = []
        foo = P.PrintInOrder()
        calls = [lambda: foo.third(lambda: out.append("third")),
                 lambda: foo.second(lambda: out.append("second")),
                 lambda: foo.first(lambda: out.append("first"))]
        rng.shuffle(calls)
        threads = [threading.Thread(target=c) for c in calls]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        assert out == ["first", "second", "third"]
    queue = P.BoundedBlockingQueue(2)
    received = []

    def produce(start):
        for i in range(start, start + 50):
            queue.enqueue(i)

    def consume():
        for _ in range(50):
            received.append(queue.dequeue())

    workers = [threading.Thread(target=produce, args=(s,)) for s in (0, 100, 200)]
    workers += [threading.Thread(target=consume) for _ in range(3)]
    for w in workers:
        w.start()
    for w in workers:
        w.join(timeout=10)
    assert sorted(received) == list(range(0, 50)) + list(range(100, 150)) + list(range(200, 250))
    assert queue.size() == 0

    site = {
        "http://news.example.com/": ["http://news.example.com/a", "http://other.example.org/x"],
        "http://news.example.com/a": ["http://news.example.com/b", "http://news.example.com/"],
        "http://news.example.com/b": ["http://news.example.com/a"],
    }
    lock = threading.Lock()
    fetched = []

    def get_urls(url):
        with lock:
            fetched.append(url)
        time.sleep(0.01)
        return site.get(url, [])

    assert P.crawl("http://news.example.com/", get_urls) == [
        "http://news.example.com/", "http://news.example.com/a", "http://news.example.com/b"]
    assert sorted(fetched) == sorted(set(fetched)), "each URL fetched once"


# ----------------------------------------------------------------------------- beyond the twenty


def t_beyond():
    assert P.subarray_sum_equals_k([1, 1, 1], 2) == 2 and P.subarray_sum_equals_k([1, 2, 3], 3) == 2
    assert P.find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]
    assert P.network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2) == 2
    assert P.network_delay_time([[1, 2, 1]], 2, 2) == -1
    trie = P.Trie()
    trie.insert("apple")
    assert trie.search("apple") and not trie.search("app") and trie.starts_with("app")
    trie.insert("app")
    assert trie.search("app")
    cache = P.LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)
    assert cache.get(2) == -1
    cache.put(4, 4)
    assert cache.get(1) == -1 and cache.get(3) == 3 and cache.get(4) == 4
    assert P.erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert P.length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4
    assert P.min_distance("horse", "ros") == 3 and P.min_distance("intention", "execution") == 5
    assert P.rob([2, 7, 9, 3, 1]) == 12
    for _ in range(300):
        a = [rng.randint(-3, 3) for _ in range(rng.randint(0, 10))]
        k = rng.randint(-4, 4)
        assert P.subarray_sum_equals_k(a, k) == sum(1 for i in range(len(a)) for j in range(i, len(a)) if sum(a[i:j + 1]) == k)
        b = [rng.randint(0, 9) for _ in range(rng.randint(0, 9))]
        lis = [1] * len(b)
        for i in range(len(b)):
            for j in range(i):
                if b[j] < b[i]:
                    lis[i] = max(lis[i], lis[j] + 1)
        assert P.length_of_lis(b) == max(lis, default=0)
        houses = [rng.randint(0, 9) for _ in range(rng.randint(0, 8))]
        best = max((sum(houses[i] for i in s) for r in range(len(houses) + 1)
                    for s in itertools.combinations(range(len(houses)), r)
                    if all(s[i + 1] - s[i] > 1 for i in range(len(s) - 1))), default=0)
        assert P.rob(houses) == best
        ivs = []
        for _ in range(rng.randint(0, 6)):
            s = rng.randint(0, 10)
            ivs.append([s, s + rng.randint(1, 4)])
        keep = max(r for r in range(len(ivs) + 1) for c in itertools.combinations(sorted(ivs), r)
                   if all(c[i][1] <= c[i + 1][0] for i in range(len(c) - 1)))
        assert P.erase_overlap_intervals(ivs) == len(ivs) - keep
        w1 = "".join(rng.choice("abc") for _ in range(rng.randint(0, 6)))
        w2 = "".join(rng.choice("abc") for _ in range(rng.randint(0, 6)))

        @functools.cache
        def edit(i, j):                          # top-down reference for LC 72
            if i == len(w1) or j == len(w2):
                return len(w1) - i + len(w2) - j
            if w1[i] == w2[j]:
                return edit(i + 1, j + 1)
            return 1 + min(edit(i + 1, j), edit(i, j + 1), edit(i + 1, j + 1))

        assert P.min_distance(w1, w2) == edit(0, 0)
    for _ in range(200):
        n = rng.randint(3, 8)                    # a tree on 1..n plus one extra edge (LC 684)
        edges = [[i, rng.randint(1, i - 1)] for i in range(2, n + 1)]
        extra = rng.choice([[u, v] for u in range(1, n + 1) for v in range(u + 1, n + 1)
                            if [u, v] not in edges and [v, u] not in edges])
        edges.append(extra)
        rng.shuffle(edges)

        def is_tree(es):
            uf = P.UnionFind(n + 1)
            return all(uf.union(u, v) for u, v in es) and uf.components == 2      # node 0 is unused
        removable = [e for i, e in enumerate(edges) if is_tree(edges[:i] + edges[i + 1:])]
        assert P.find_redundant_connection(edges) == removable[-1]
        nodes = rng.randint(1, 6)
        times = []
        for _ in range(rng.randint(0, 12) if nodes > 1 else 0):
            u, v = rng.sample(range(1, nodes + 1), 2)
            times.append([u, v, rng.randint(0, 9)])
        source = rng.randint(1, nodes)
        dist = {v: 0 if v == source else float("inf") for v in range(1, nodes + 1)}
        for _ in range(nodes):                   # Bellman-Ford as the reference
            for u, v, w in times:
                dist[v] = min(dist[v], dist[u] + w)
        far = max(dist.values())
        assert P.network_delay_time(times, nodes, source) == (-1 if far == float("inf") else far)
        trie, words = P.Trie(), set()
        cache, recent, store = P.LRUCache(rng.randint(1, 3)), [], {}
        for _ in range(20):
            word = "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))
            if rng.random() < 0.5:
                trie.insert(word)
                words.add(word)
            assert trie.search(word) == (word in words)
            assert trie.starts_with(word) == any(w.startswith(word) for w in words)
            key = rng.randint(0, 4)
            if key in recent:
                recent.remove(key)
            if rng.random() < 0.5:
                assert cache.get(key) == store.get(key, -1)
                if key in store:
                    recent.append(key)
            else:
                cache.put(key, store.setdefault(key, 0) + 1)
                store[key] += 1
                recent.append(key)
                if len(recent) > cache.capacity:
                    del store[recent.pop(0)]


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in globals().items() if name.startswith("t_")]
    for name, fn in tests:
        check(name[2:], fn)
    print(f"all {len(tests)} pattern groups passed")
