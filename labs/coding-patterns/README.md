# Coding-interview patterns lab

Tested Python templates for the twenty coding-interview patterns taught in Design Gurus' *Grokking the Coding Interview*, plus the families that list leaves out: prefix sums with a hash map, union-find, Dijkstra, tries, greedy interval scheduling, the main dynamic-programming shapes and the LRU cache. Chapter 39d of the book (`book/part-3-interviews/39d-coding-interview-patterns.md`) explains each pattern: how to recognize it from the statement and the constraints, the invariant that makes the template correct, its complexity, a LeetCode practice set, pitfalls and follow-ups. This folder holds the code the chapter prints, the tests that prove it, and a script that keeps the two identical.

## Requirements and quick start

Standard library only, Python 3.10 or newer (this run used 3.14.7). There is no pytest configuration: the test file is a plain script with `assert` statements, so run it directly.

```bash
cd labs/coding-patterns
python3 test_patterns.py        # 21 lines "ok  <group>", then "all 21 pattern groups passed"; about 0.5 s
python3 check_chapter_sync.py   # "126 objects and lines checked, 0 problem(s)"; exit code 1 on any difference
```

`test_patterns.py` prints one line per pattern group (`ok  two_pointers`, `ok  islands`, ... `ok  beyond`) and stops at the first failing assertion with a traceback that names the function. `check_chapter_sync.py` extracts every Python code block from chapter 39d, splits it into top-level `def` and `class` chunks, and compares each one character for character with `inspect.getsource` of the same name in `patterns.py`; module-level lines such as imports and the `DIRS4` constant must also appear verbatim.

| File | What it holds |
|---|---|
| `patterns.py` | 1,825 lines. One section per pattern: a reusable template plus the classic problems it solves, each with its LeetCode number in the docstring. Shared helpers at the top: `ListNode`, `TreeNode`, `build_list`, `list_values`, `build_tree` (LeetCode's level-order notation with `None` for a missing child) and `DIRS4` |
| `test_patterns.py` | Fixed examples from the problem statements plus, for nearly every function, hundreds of seeded random inputs compared with a brute-force reference; thread-ordering and producer-consumer tests; a time guard on the Sudoku solver |
| `check_chapter_sync.py` | Fails if a function, class, import or constant shown in chapter 39d differs from the tested version here |

Conventions: functions that LeetCode specifies as in-place mutate their input, as an interview answer would (`sort_colors`, `num_islands`, `cyclic_sort`, `solve_sudoku`); the tests pass copies. Indices are 0-based unless a docstring says otherwise (`reverse_between` takes 1-indexed positions, as LC 92 does). Problems marked with a dagger in the chapter need LeetCode Premium.

## How to use this lab for interview practice

The chapter is for understanding; the lab is for retrieval practice. The loop:

1. Read one pattern's section in chapter 39d: the cue, the invariant, the template. Close the book.
2. In `patterns.py`, delete the body of one function, keeping the signature and the docstring. The docstring is the problem statement in one line, including the LeetCode number, so it is all the prompt you get.
3. Write the body from memory. Say the invariant out loud before the first line of code: it is what the interviewer is listening for.
4. Run `python3 test_patterns.py`. The randomized comparisons catch the off-by-one and empty-input bugs that two hand-picked examples miss.
5. If it passes, keep your version (then run `python3 check_chapter_sync.py` before committing, because the chapter must show the same code). If it fails, `git diff` your attempt against the reference and write the difference in your error log: the cue you failed to see, the invariant you got wrong.

Timing targets, from the chapter: 15 minutes for an easy problem, 25 for a medium, 40 for a hard, and about two minutes to name the pattern. Solve at least half of your practice problems without running code, because many coding rounds work that way, and walk through two examples by hand before saying "done". Redo every missed problem three days later and a week later. The chapter's four-week plan (39d.25) orders the patterns: arrays and search in week 1, lists, trees and graphs in week 2, heaps, stacks and backtracking in week 3, dynamic programming, greedy and concurrency in week 4.

What `check_chapter_sync.py` guarantees: the code you practice against is the code the book explains. Every template in chapter 39d is copied from `patterns.py`, not retyped, so a comment, a variable name or an edge-case branch in the chapter is the one the tests exercised. If you improve a function here, the chapter is out of date until it is updated, and the check says so.

## The patterns

Each subsection names the functions in `patterns.py`, gives the shape of problem the pattern fits and the invariant that makes the template correct, and shows one example whose output was produced by running the function.

### 1. Two pointers

`pair_with_target_sum`, `remove_duplicates`, `sorted_squares`, `three_sum`, `sort_colors`.

*Intuition.* The input is sorted (or can be sorted without losing the answer) and the question is about a pair, a triplet, or an in-place rewrite. Listen for "sorted", "pair", "in place", "remove duplicates", "partition".

*The invariant.* One pointer at each end: if the pair sum is too small, no pair using the left value can be large enough, so the left pointer moves; symmetrically for the right. For read/write pointers, `nums[:write]` is always the finished prefix.

```python
>>> from patterns import pair_with_target_sum, three_sum
>>> pair_with_target_sum([1, 2, 3, 4, 6], 6)
(1, 3)
>>> three_sum([-1, 0, 1, 2, -1, -4])
[[-1, -1, 2], [-1, 0, 1]]
```

*Complexity.* O(n) time, O(1) extra space for one pass; `three_sum` is O(n²) after an O(n log n) sort.

*Pitfalls.* In `three_sum`, skipping repeated pointer values before checking the sum (loses triplets such as [-2, 1, 1]) rather than after a match; in `sort_colors`, advancing `i` after swapping with `high`, which leaves the swapped-in value unexamined. The random tests compare against `itertools.combinations` and `sorted`, so both show up immediately.

*Practice.* 167 Two Sum II; 26 Remove Duplicates from Sorted Array; 977 Squares of a Sorted Array; 15 3Sum; 75 Sort Colors; 18 4Sum; 11 Container With Most Water.

### 2. Islands (matrix traversal)

`_flood`, `num_islands`, `max_area_of_island`, `flood_fill`, `closed_island`.

*Intuition.* A grid and a question about connected regions: count them, measure the largest, recolor one, or find the ones that do not touch the border.

*The invariant.* A cell is marked when it is enqueued, not when it is dequeued, so every cell enters the queue at most once; `_flood` returns the size of one region and leaves it marked, so the outer loops count each region exactly once.

```python
>>> from patterns import num_islands
>>> num_islands([list(r) for r in ["11000", "11000", "00100", "00011"]])
3
```

*Complexity.* O(rows × cols) time and worst-case space for the queue. Iterative BFS avoids Python's recursion limit of 1,000, which a 100 × 100 grid of land would exceed.

*Pitfalls.* Marking on dequeue (cells are queued many times); in `closed_island`, counting before sinking the border-connected zeros. The tests compute the regions independently with a visited set and compare counts, areas and the recolored image.

*Practice.* 200 Number of Islands; 695 Max Area of Island; 733 Flood Fill; 1254 Number of Closed Islands; 1020 Number of Enclaves; 130 Surrounded Regions; 994 Rotting Oranges.

### 3. Fast and slow pointers

`has_cycle`, `cycle_start`, `middle_node`, `is_palindrome_list`, `is_happy`, `find_duplicate`.

*Intuition.* A linked list, or any "next" function, and a question about a cycle, the middle, or whether a sequence eventually repeats. The array in LC 287 is a linked list in disguise: index i points to `nums[i]`.

*The invariant.* The fast pointer gains one node per step on the slow one, so inside a cycle they meet within one lap; after the meeting, a pointer from the head and the slow pointer are the same distance from the cycle's entry.

```python
>>> from patterns import find_duplicate, is_happy
>>> find_duplicate([1, 3, 4, 2, 2])
2
>>> is_happy(19), is_happy(2)
(True, False)
```

*Complexity.* O(n) time, O(1) space; `find_duplicate` reads the array without modifying it.

*Pitfalls.* Checking `fast.next.next` before `fast.next`; leaving the list reversed in `is_palindrome_list` (the tests assert `list_values(head)` is unchanged afterwards). Random lists with and without cycles compare node identity, not values.

*Practice.* 141 Linked List Cycle; 142 Linked List Cycle II; 876 Middle of the Linked List; 234 Palindrome Linked List; 202 Happy Number; 287 Find the Duplicate Number.

### 4. Sliding window

`max_sum_subarray_k`, `min_subarray_len`, `longest_with_k_distinct`, `length_of_longest_substring`, `character_replacement`, `find_anagrams`, `min_window`.

*Intuition.* A contiguous subarray or substring, and a longest, shortest or count under a condition that is monotone: adding elements can only break it, removing can only restore it.

*The invariant.* The right edge grows by one per step; the left edge moves only forward and only while the condition is broken (for "longest") or still holds (for "shortest"), so every element enters and leaves once.

```python
>>> from patterns import min_window, character_replacement
>>> min_window("ADOBECODEBANC", "ABC")
'BANC'
>>> character_replacement("AABABBA", 1)
4
```

*Complexity.* O(n) time; O(k) or O(alphabet) space for the counts.

*Pitfalls.* Updating the answer before shrinking for "longest" (or after for "shortest"): an off-by-one that two examples will not reveal; forgetting to delete zero counts so `len(counts)` overstates the distinct values. The tests enumerate every window of random strings over a three-letter alphabet.

*Practice.* 209 Minimum Size Subarray Sum; 904 Fruit Into Baskets; 3 Longest Substring Without Repeating Characters; 424 Longest Repeating Character Replacement; 438 Find All Anagrams in a String; 76 Minimum Window Substring.

### 5. Merge intervals

`merge_intervals`, `insert_interval`, `interval_intersection`, `min_meeting_rooms`.

*Intuition.* Ranges with a start and an end; overlaps, merging, free time, rooms.

*The invariant.* After sorting by start, the last interval in the output has the largest end seen so far; a new interval either starts inside it (extend) or after it (append). For rooms, the min-heap's top is the earliest-ending meeting, so a new meeting reuses a room exactly when it can.

```python
>>> from patterns import merge_intervals, min_meeting_rooms
>>> merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]])
[[1, 6], [8, 10], [15, 18]]
>>> min_meeting_rooms([[0, 30], [5, 10], [15, 20]])
2
```

*Complexity.* O(n log n) for the sort, O(n) for the sweep; `insert_interval` is O(n) because the input is already sorted.

*Pitfalls.* Sorting by end when the merge needs start order; open versus closed endpoints (`merge_intervals` merges touching closed intervals, `min_meeting_rooms` treats meetings as half-open). The tests compare the set of covered half-integer points and the busiest instant.

*Practice.* 56 Merge Intervals; 57 Insert Interval; 986 Interval List Intersections; 253 Meeting Rooms II; 435 Non-overlapping Intervals; 1094 Car Pooling.

### 6. Cyclic sort

`cyclic_sort`, `missing_number`, `find_disappeared_numbers`, `find_all_duplicates`, `first_missing_positive`.

*Intuition.* Values in a known range 1..n or 0..n, and a missing or duplicated one wanted in O(n) time and O(1) extra space.

*The invariant.* Each swap places one value at its home index `value - 1` for good; the loop advances only when `nums[i]` is home or its home already holds an equal value, so there are at most n swaps.

```python
>>> from patterns import first_missing_positive, find_disappeared_numbers
>>> first_missing_positive([3, 4, -1, 1])
2
>>> find_disappeared_numbers([4, 3, 2, 7, 8, 2, 3, 1])
[5, 6]
```

*Complexity.* O(n) time, O(1) extra space; the input is mutated.

*Pitfalls.* Computing the target index after the first assignment of a swap (compute `j` first); an infinite loop when a duplicate is already home, which the `nums[i] != nums[j]` test prevents; values outside the range must be skipped, as in LC 41.

*Practice.* 268 Missing Number; 448 Find All Numbers Disappeared in an Array; 442 Find All Duplicates in an Array; 645 Set Mismatch; 41 First Missing Positive.

### 7. In-place reversal of a linked list

`reverse_list`, `reverse_between`, `reverse_k_group`, `rotate_right`.

*Intuition.* Reverse all or part of a linked list without extra memory.

*The invariant.* `prev` is the head of the reversed part, `curr` the head of the unreversed part; each step saves `curr.next` before redirecting it. A dummy head makes "reverse from position 1" the same code as any other position.

```python
>>> from patterns import build_list, list_values, reverse_k_group
>>> list_values(reverse_k_group(build_list([1, 2, 3, 4, 5]), 2))
[2, 1, 4, 3, 5]
```

*Complexity.* O(n) time, O(1) space.

*Pitfalls.* Overwriting `curr.next` before saving it; reversing the short final block in `reverse_k_group` (it must stay as it is). The tests build the expected list with slicing for every random length, range and k.

*Practice.* 206 Reverse Linked List; 92 Reverse Linked List II; 25 Reverse Nodes in k-Group; 24 Swap Nodes in Pairs; 61 Rotate List; 143 Reorder List.

### 8. Tree breadth-first search

`level_order`, `level_order_bottom`, `zigzag_level_order`, `right_side_view`, `min_depth`.

*Intuition.* A tree and an answer per level, or "closest to the root".

*The invariant.* The queue length at the top of the loop is exactly the size of the current level; processing that many nodes before reading the length again keeps the levels separate.

```python
>>> from patterns import build_tree, zigzag_level_order, min_depth
>>> t = build_tree([3, 9, 20, None, None, 15, 7])
>>> zigzag_level_order(t), min_depth(t)
([[3], [20, 9], [15, 7]], 2)
```

*Complexity.* O(n) time; O(width) space for the queue.

*Pitfalls.* `while queue` without fixing the level size (levels blur); `list.pop(0)`, which is O(n) per pop, instead of `collections.deque`. The tests collect levels by recursion and compare.

*Practice.* 102, 107 and 103 Level Order Traversal (plain, bottom-up, zigzag); 111 Minimum Depth of Binary Tree; 199 Binary Tree Right Side View; 515 Find Largest Value in Each Tree Row.

### 9. Tree depth-first search

`has_path_sum`, `path_sum_all`, `count_paths_with_sum`, `max_path_sum`, `diameter_of_binary_tree`, `lowest_common_ancestor`.

*Intuition.* Root-to-leaf paths, or a value at each node computed from its children.

*The invariant.* Each call returns to its parent the one number the parent needs (the best downward gain, the height, or the found node) and updates a shared best as a side effect. For LC 437, the counter of prefix sums on the current path is incremented on entry and decremented on exit, so it describes exactly the path from the root.

```python
>>> from patterns import build_tree, max_path_sum, count_paths_with_sum
>>> max_path_sum(build_tree([-10, 9, 20, None, None, 15, 7]))
42
>>> count_paths_with_sum(build_tree([10, 5, -3, 3, 2, None, 11, 3, -2, None, 1]), 8)
3
```

*Complexity.* O(n) time, O(height) stack.

*Pitfalls.* Treating a node with one child as a leaf; appending `path` instead of `path[:]` so every recorded path aliases the same list. The tests enumerate all node-to-node paths of random trees to check `max_path_sum`, the diameter and every LCA.

*Practice.* 112 Path Sum; 113 Path Sum II; 437 Path Sum III; 543 Diameter of Binary Tree; 124 Binary Tree Maximum Path Sum; 236 Lowest Common Ancestor of a Binary Tree.

### 10. Two heaps

`MedianFinder`, `median_sliding_window`, `find_maximized_capital`.

*Intuition.* A running median, or any split of values into a smaller half and a larger half where only the boundary matters.

*The invariant.* Every value in the lower max-heap is at most every value in the upper min-heap, and the lower heap holds the same number of elements or one more; the median is then one or two heap tops. The window version keeps counts of valid elements and deletes lazily when a stale value reaches a top.

```python
>>> from patterns import MedianFinder, median_sliding_window
>>> mf = MedianFinder(); out = []
>>> for x in (1, 2, 3, 4): mf.add_num(x); out.append(mf.find_median())
>>> out
[1.0, 1.5, 2.0, 2.5]
>>> median_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3)
[1.0, -1.0, -1.0, 3.0, 5.0, 6.0]
```

*Complexity.* O(log n) per insertion; `median_sliding_window` is O(n log n) overall.

*Pitfalls.* Forgetting to negate on the way out of the max-heap; adding to the heap that is already larger without routing through the lower heap, which can break the order invariant. The window test sorts every window of random arrays and compares medians.

*Practice.* 295 Find Median from Data Stream; 480 Sliding Window Median; 502 IPO; 1834 Single-Threaded CPU.

### 11. Subsets

`subsets`, `subsets_with_dup`, `permutations`, `letter_case_permutation`.

*Intuition.* "All subsets", "all permutations", "all strings from toggling case": the answer is exponential and must be built level by level.

*The invariant.* After processing element i, the list holds every result over the first i elements; a new element extends each existing result. With duplicates, a repeated value extends only the results created by the previous step.

```python
>>> from patterns import subsets_with_dup
>>> subsets_with_dup([1, 2, 2])
[[], [1], [2], [1, 2], [2, 2], [1, 2, 2]]
```

*Complexity.* O(2ⁿ · n) for subsets, O(n! · n) for permutations: output-bound.

*Pitfalls.* Iterating over a list while appending to it (the templates build a new list or slice a fixed range); deduplicating with a set of tuples at the end, which generates exponential garbage first. The tests compare with `itertools`.

*Practice.* 78 Subsets; 90 Subsets II; 46 Permutations; 47 Permutations II; 784 Letter Case Permutation; 22 Generate Parentheses.

### 12. Modified binary search

`lower_bound`, `order_agnostic_search`, `ceiling_index`, `next_greatest_letter`, `search_range`, `search_rotated`, `find_min_rotated`, `peak_index_in_mountain`, `min_eating_speed`.

*Intuition.* Sorted, rotated or otherwise monotone data, or "the minimum value that works" where feasibility is monotone in the answer.

*The invariant.* The answer always lies in `[lo, hi]` (or `[lo, hi)` for `lower_bound`); every iteration discards half without discarding the answer. `lower_bound` is the one template to memorize: `search_range` and `ceiling_index` are two calls to it.

```python
>>> from patterns import lower_bound, search_rotated, min_eating_speed
>>> lower_bound([1, 2, 2, 4], 2), lower_bound([1, 2, 2, 4], 3)
(1, 3)
>>> search_rotated([4, 5, 6, 7, 0, 1, 2], 0)
4
>>> min_eating_speed([3, 6, 7, 11], 8)
4
```

*Complexity.* O(log n); O(n log V) for binary search on the answer with an O(n) feasibility check.

*Pitfalls.* Mixing loop conditions and updates (`while lo <= hi` with `hi = mid` loops forever); in rotated arrays with duplicates, the sorted-half test fails when both ends equal the middle. The tests compare `lower_bound` with `bisect_left` on 500 random arrays and search every rotation.

*Practice.* 704 Binary Search; 34 Find First and Last Position; 744 Find Smallest Letter Greater Than Target; 33 Search in Rotated Sorted Array; 153 Find Minimum in Rotated Sorted Array; 852 Peak Index in a Mountain Array; 875 Koko Eating Bananas; 1011 Capacity To Ship Packages Within D Days.

### 13. Top K elements

`kth_largest`, `top_k_frequent`, `KthLargest`, `k_closest_points`, `reorganize_string`.

*Intuition.* "k largest", "k most frequent", "k closest", or a greedy that always takes the most frequent remaining item.

*The invariant.* A min-heap of size k holds the k largest values seen so far; its top is the kth largest, and a new value enters only if it beats the top. `top_k_frequent` replaces the heap with buckets indexed by frequency for O(n).

```python
>>> from patterns import kth_largest, top_k_frequent, reorganize_string
>>> kth_largest([3, 2, 1, 5, 6, 4], 2), top_k_frequent([1, 1, 1, 2, 2, 3], 2)
(5, [1, 2])
>>> reorganize_string("aab"), reorganize_string("aaab")
('aba', '')
```

*Complexity.* O(n log k) time, O(k) space for the heap versions.

*Pitfalls.* A heap of all n values for "top k" (works, but the size-k heap is the expected answer for streams); tuples that compare unorderable objects on ties (add an index as the second element). The tests check `reorganize_string` on 300 random strings for both validity and impossibility.

*Practice.* 215 Kth Largest Element in an Array; 347 Top K Frequent Elements; 703 Kth Largest Element in a Stream; 973 K Closest Points to Origin; 767 Reorganize String; 621 Task Scheduler.

### 14. Bitwise XOR

`single_number`, `single_number_iii`, `bitwise_complement`, `missing_number_xor`.

*Intuition.* Every value appears twice except one (or two); flip the bits of a number; find a missing value without extra memory.

*The invariant.* `x ^ x == 0` and XOR is commutative, so the XOR of a multiset cancels every pair whatever the order; for two singletons, any set bit of `a ^ b` splits the values into two groups each containing one singleton.

```python
>>> from patterns import single_number_iii, bitwise_complement
>>> single_number_iii([1, 2, 1, 3, 2, 5])
[3, 5]
>>> bitwise_complement(5)
2
```

*Complexity.* O(n) time, O(1) space.

*Pitfalls.* Python integers are unbounded, so `~x` is -x - 1, not a 32-bit complement: mask explicitly; precedence differs from C (`1 << n - 1` means `1 << (n - 1)`). The complement is checked against a string-based reference for every n below 2,000.

*Practice.* 136 Single Number; 260 Single Number III; 137 Single Number II; 1009 Complement of Base 10 Integer; 268 Missing Number; 191 Number of 1 Bits.

### 15. Backtracking

`generate_parentheses`, `combination_sum`, `factor_combinations`, `word_exists`, `total_n_queens`, `solve_sudoku`.

*Intuition.* Constraint satisfaction, puzzles, "all valid arrangements": a decision tree explored depth-first with early pruning.

*The invariant.* Choose, recurse, undo: on return from each branch, the shared state (`path`, the board cell, the column and diagonal sets) is exactly what it was before the choice. `solve_sudoku` branches on the empty cell with the fewest options, which keeps hard puzzles well under a second.

```python
>>> from patterns import generate_parentheses, combination_sum, total_n_queens
>>> generate_parentheses(3)
['((()))', '(()())', '(())()', '()(())', '()()()']
>>> combination_sum([2, 3, 6, 7], 7)
[[2, 2, 3], [7]]
>>> total_n_queens(8)
92
```

*Complexity.* Exponential in general; the point is the pruning, and saying so.

*Pitfalls.* Forgetting to undo (the next branch starts from a corrupted state); recursing with `i + 1` when reuse is allowed (LC 39) or `i` when it is not. The tests check `generate_parentheses` against every string of n pairs, `factor_combinations` against brute force for every n below 200, and give the Sudoku solver ten seconds on two puzzles that take plain cell-by-cell backtracking tens of seconds.

*Practice.* 22 Generate Parentheses; 39 Combination Sum; 40 Combination Sum II; 77 Combinations; 79 Word Search; 131 Palindrome Partitioning; 51 N-Queens; 37 Sudoku Solver.

### 16. 0/1 knapsack (dynamic programming)

`knapsack_01`, `can_partition`, `count_subsets_with_sum`, `find_target_sum_ways`, `min_subset_sum_difference`, `coin_change`.

*Intuition.* Choose items under a capacity; partition into equal sums; count the ways to reach a sum. Each item is used at most once (`coin_change` is the unbounded contrast).

*The invariant.* With one row over capacities, filling right to left means `best[c - w]` still describes the previous item set when `best[c]` reads it, so each item is counted once; filling left to right lets an item repeat, which is what the unbounded problem wants.

```python
>>> from patterns import knapsack_01, find_target_sum_ways, coin_change
>>> knapsack_01([1, 2, 3, 5], [1, 6, 10, 16], 7)
22
>>> find_target_sum_ways([1, 1, 1, 1, 1], 3)
5
>>> coin_change([1, 2, 5], 11)
3
```

*Complexity.* O(n × capacity) time, O(capacity) space.

*Pitfalls.* Iterating capacities upward in the 0/1 version (silently allows reuse); forgetting that zeros double the number of ways (the template's loop reaches index 0, so it handles them). The tests enumerate every subset and every sign assignment of small random inputs.

*Practice.* 416 Partition Equal Subset Sum; 494 Target Sum; 1049 Last Stone Weight II; 474 Ones and Zeroes; 322 Coin Change; 518 Coin Change II.

### 17. Topological sort

`topological_order`, `can_finish`, `find_order`, `all_topological_orders`, `alien_order`, `find_min_height_trees`.

*Intuition.* Dependencies, prerequisites, ordering constraints; a graph where the answer is an order.

*The invariant.* Kahn's algorithm: a node enters the queue exactly when its in-degree reaches zero, that is, when every predecessor has been emitted. If the output is shorter than n, the leftover nodes lie on a cycle. Peeling leaves in LC 310 is the same idea on an undirected tree.

```python
>>> from patterns import alien_order, can_finish, find_min_height_trees
>>> alien_order(["wrt", "wrf", "er", "ett", "rftt"])
'wertf'
>>> can_finish(2, [[1, 0], [0, 1]])
False
>>> find_min_height_trees(6, [[3, 0], [3, 1], [3, 2], [3, 4], [5, 4]])
[3, 4]
```

*Complexity.* O(V + E); `all_topological_orders` is output-bound.

*Pitfalls.* Edge direction (LC 207 lists pairs as [course, prerequisite]); in the alien dictionary, using all character pairs instead of only the first difference, and missing the case where a word precedes its own prefix. The tests validate every order against the edges and enumerate all permutations for small graphs.

*Practice.* 207 Course Schedule; 210 Course Schedule II; 269 Alien Dictionary; 310 Minimum Height Trees; 802 Find Eventual Safe States; 2115 Find All Possible Recipes.

### 18. K-way merge

`merge_k_lists`, `kth_smallest_in_sorted_lists`, `kth_smallest_in_matrix`, `smallest_range`.

*Intuition.* k sorted lists or rows, and the kth smallest across them, or a range that touches all of them.

*The invariant.* The heap holds exactly one head per unexhausted list, so its top is the global minimum of what remains; popping and pushing the successor keeps that true.

```python
>>> from patterns import smallest_range, kth_smallest_in_matrix
>>> smallest_range([[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]])
[20, 24]
>>> kth_smallest_in_matrix([[1, 5, 9], [10, 11, 13], [12, 13, 15]], 8)
13
```

*Complexity.* O(N log k) for N elements in k lists; O(k) heap.

*Pitfalls.* Pushing every element at once (O(N log N) and O(N) memory, losing the point); comparing nodes on ties (the list index breaks ties so `ListNode` objects are never compared). The tests flatten and sort as the reference.

*Practice.* 21 Merge Two Sorted Lists; 23 Merge k Sorted Lists; 378 Kth Smallest Element in a Sorted Matrix; 373 Find K Pairs with Smallest Sums; 632 Smallest Range Covering Elements from K Lists.

### 19. Monotonic stack

`next_greater_elements`, `next_greater_element_i`, `next_greater_circular`, `next_smaller_elements`, `daily_temperatures`, `largest_rectangle_area`, `trap`, `max_sliding_window`.

*Intuition.* "Next greater/smaller", spans, histograms, trapped water, the maximum of every window.

*The invariant.* The stack holds indices still waiting for their answer, with values monotone from bottom to top; a new value pops everything it beats and answers those indices. Every index is pushed and popped once.

```python
>>> from patterns import daily_temperatures, largest_rectangle_area, max_sliding_window
>>> daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73])
[1, 1, 4, 2, 1, 1, 0, 0]
>>> largest_rectangle_area([2, 1, 5, 6, 2, 3])
10
>>> max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3)
[3, 3, 5, 5, 6, 7]
```

*Complexity.* O(n) time, O(n) stack.

*Pitfalls.* Storing values instead of indices (you lose distances and boundaries); strict versus non-strict comparison, which decides how equal values are handled; forgetting the final flush (the trailing zero bar in `largest_rectangle_area`). The tests compare every function with an O(n²) scan on 300 random arrays.

*Practice.* 496 Next Greater Element I; 503 Next Greater Element II; 739 Daily Temperatures; 84 Largest Rectangle in Histogram; 42 Trapping Rain Water; 402 Remove K Digits; 239 Sliding Window Maximum.

### 20. Multi-threaded

`invert_tree`, `invert_tree_parallel`, `PrintInOrder`, `BoundedBlockingQueue`, `crawl`.

*Intuition.* Ordering of concurrent calls, producer-consumer, parallel traversal, crawling. On CPython the GIL gives no speedup for pure-Python CPU work; the interview point is finding independent sub-tasks, avoiding shared mutable state and joining results correctly.

*The invariant.* A condition wait sits inside a `while` loop that rechecks the predicate, because a wakeup proves nothing; events are set only after the work they guard; the crawler's main thread owns `seen`, so workers only fetch and no lock is needed.

```python
>>> from patterns import BoundedBlockingQueue
>>> q = BoundedBlockingQueue(2); q.enqueue("a"); q.enqueue("b")
>>> q.size(), q.dequeue()
(2, 'a')
```

*Complexity.* As the sequential algorithm; the cost that matters is contention and the number of threads.

*Pitfalls.* `if` instead of `while` around a condition wait; notifying without holding the lock; check-then-act races on shared sets. The tests start `first`, `second` and `third` in twenty shuffled orders, run three producers against three consumers through a queue of capacity 2, and assert that the crawler fetches each URL once.

*Practice.* 1114 Print in Order; 1115 Print FooBar Alternately; 1117 Building H2O; 1188 Design Bounded Blocking Queue; 1242 Web Crawler Multithreaded; 226 Invert Binary Tree with threads.

### 21. Beyond the twenty

`subarray_sum_equals_k`, `UnionFind`, `find_redundant_connection`, `network_delay_time`, `Trie`, `LRUCache`, `erase_overlap_intervals`, `length_of_lis`, `min_distance`, `rob`.

*Intuition.* The families Grokking's list leaves out but interviews do not: prefix sums with a hash map (subarray sums with negatives), union-find (connectivity that grows as edges arrive), Dijkstra (weighted shortest paths), tries, greedy interval scheduling, LIS, edit distance, house robber, and the LRU cache.

*The invariant.* One each: the hash map counts how often each running sum has appeared, so `seen[running - k]` is the number of subarrays ending here with sum k; union by size keeps find paths O(log n) and path halving flattens them; Dijkstra settles a node the first time it leaves the heap, so later entries for it are stale and skipped; `tails[i]` in `length_of_lis` is the smallest tail of any increasing run of length i + 1.

```python
>>> from patterns import subarray_sum_equals_k, network_delay_time, length_of_lis, min_distance
>>> subarray_sum_equals_k([1, -1, 1], 1)
3
>>> network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2)
2
>>> length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]), min_distance("horse", "ros")
(4, 3)
```

*Complexity.* O(n) for the prefix map; near-constant per union-find operation; O(E log V) for Dijkstra; O(n log n) for LIS; O(mn) for edit distance.

*Pitfalls.* Using a sliding window instead of the prefix map when values can be negative; forgetting the `seen[0] = 1` base case. The tests use Bellman-Ford as the reference for Dijkstra, an O(n²) DP for LIS, a memoized recursion for edit distance, and a model of recency for the LRU cache.

*Practice.* 560 Subarray Sum Equals K; 684 Redundant Connection; 743 Network Delay Time; 208 Implement Trie; 146 LRU Cache; 435 Non-overlapping Intervals; 300 Longest Increasing Subsequence; 72 Edit Distance; 198 House Robber.

## How the tests work

`test_patterns.py` has one function per pattern group, `t_two_pointers` through `t_beyond`; the `__main__` block collects every `t_*` function and runs it through `check`, which prints `ok  <name>`. A shared `random.Random(39)` seeds every draw, so a failure reproduces exactly.

Three kinds of check appear in every group:

- **Fixed examples** from the problem statements, including the edge cases the statements mention (empty inputs, a single node, `k` equal to the length, an impossible target).
- **Brute-force oracles on random inputs.** Sizes are kept small (lengths up to about 12, values in a narrow range so duplicates are common) and the reference is the most obvious correct program: `itertools.combinations` for 3Sum and subsets, every window for the sliding windows, an independent region finder for the islands, `bisect_left` for `lower_bound`, every permutation for the topological orders, Bellman-Ford for Dijkstra, an O(n²) scan for the monotonic stacks. Hundreds of draws per pattern give the random inputs a good chance of hitting every branch, which is what makes deleting a function body and rewriting it a real test.
- **Structural assertions** that an output-only comparison would miss: `is_palindrome_list` must leave the list as it found it; `median_sliding_window` must match sorted medians for every k; the Sudoku solver must finish two hard puzzles in under ten seconds, which fails if you drop the most-constrained-cell ordering; the crawler must fetch each URL once; `PrintInOrder` must produce the same output for twenty shuffled thread starts.

Helper functions at the top of the file (`random_tree`, `tree_levels`, `leaf_paths`, `all_downward_paths`, `path_from_root`, `regions`, `shape`) are the references for the tree and grid patterns.

To add a pattern: write the template in a new section of `patterns.py` with the LeetCode number in the docstring, add a `t_<name>` function in `test_patterns.py` with at least one fixed example and one randomized comparison against a brute-force reference, and run both scripts. If the chapter prints the new function, it must be pasted from `patterns.py` so `check_chapter_sync.py` stays green.

## Map from functions to chapter sections

| Chapter section | Pattern | Functions and classes in `patterns.py` |
|---|---|---|
| 39d.3 | Two pointers | `pair_with_target_sum`, `remove_duplicates`, `sorted_squares`, `three_sum`, `sort_colors` |
| 39d.4 | Islands | `_flood`, `num_islands`, `max_area_of_island`, `flood_fill`, `closed_island` |
| 39d.5 | Fast and slow pointers | `has_cycle`, `cycle_start`, `middle_node`, `is_palindrome_list`, `is_happy`, `find_duplicate` |
| 39d.6 | Sliding window | `max_sum_subarray_k`, `min_subarray_len`, `longest_with_k_distinct`, `length_of_longest_substring`, `character_replacement`, `find_anagrams`, `min_window` |
| 39d.7 | Merge intervals | `merge_intervals`, `insert_interval`, `interval_intersection`, `min_meeting_rooms` |
| 39d.8 | Cyclic sort | `cyclic_sort`, `missing_number`, `find_disappeared_numbers`, `find_all_duplicates`, `first_missing_positive` |
| 39d.9 | In-place reversal | `reverse_list`, `reverse_between`, `reverse_k_group`, `rotate_right` |
| 39d.10 | Tree BFS | `level_order`, `level_order_bottom`, `zigzag_level_order`, `right_side_view`, `min_depth` |
| 39d.11 | Tree DFS | `has_path_sum`, `path_sum_all`, `count_paths_with_sum`, `max_path_sum`, `diameter_of_binary_tree`, `lowest_common_ancestor` |
| 39d.12 | Two heaps | `MedianFinder`, `median_sliding_window`, `find_maximized_capital` |
| 39d.13 | Subsets | `subsets`, `subsets_with_dup`, `permutations`, `letter_case_permutation` |
| 39d.14 | Modified binary search | `lower_bound`, `order_agnostic_search`, `ceiling_index`, `next_greatest_letter`, `search_range`, `search_rotated`, `find_min_rotated`, `peak_index_in_mountain`, `min_eating_speed` |
| 39d.15 | Top K elements | `kth_largest`, `top_k_frequent`, `KthLargest`, `k_closest_points`, `reorganize_string` |
| 39d.16 | Bitwise XOR | `single_number`, `single_number_iii`, `bitwise_complement`, `missing_number_xor` |
| 39d.17 | Backtracking | `generate_parentheses`, `combination_sum`, `factor_combinations`, `word_exists`, `total_n_queens`, `solve_sudoku` |
| 39d.18 | 0/1 knapsack | `knapsack_01`, `can_partition`, `count_subsets_with_sum`, `find_target_sum_ways`, `min_subset_sum_difference`, `coin_change` |
| 39d.19 | Topological sort | `topological_order`, `can_finish`, `find_order`, `all_topological_orders`, `alien_order`, `find_min_height_trees` |
| 39d.20 | K-way merge | `merge_k_lists`, `kth_smallest_in_sorted_lists`, `kth_smallest_in_matrix`, `smallest_range` |
| 39d.21 | Monotonic stack | `next_greater_elements`, `next_greater_element_i`, `next_greater_circular`, `next_smaller_elements`, `daily_temperatures`, `largest_rectangle_area`, `trap`, `max_sliding_window` |
| 39d.22 | Multi-threaded | `invert_tree`, `invert_tree_parallel`, `PrintInOrder`, `BoundedBlockingQueue`, `crawl` |
| 39d.23 | Beyond the twenty | `subarray_sum_equals_k`, `UnionFind`, `find_redundant_connection`, `network_delay_time`, `Trie`, `LRUCache`, `erase_overlap_intervals`, `length_of_lis`, `min_distance`, `rob` |
| shared | Helpers (not printed in the chapter) | `ListNode`, `TreeNode`, `build_list`, `list_values`, `build_tree`, `DIRS4` |

The chapters that build on this lab, 39e to 39g, have their own folder, [`labs/algorithm-frameworks`](../algorithm-frameworks/README.md); nothing there imports from here, so each lab runs on its own.
