# Algorithm frameworks lab

Tested Python for chapters 39e, 39f and 39g of the book, which follow the topic map of [labuladong Algo Notes](https://labuladong.online/en/algo/home/) and extend it. Chapter 39e builds the data structures from contiguous arrays and linked nodes and implements the ten sorting algorithms (`ds_basics.py`); 39f covers the classic templates, binary-tree thinking, data-structure design and graph algorithms (`frameworks_1.py`); 39g covers backtracking, BFS, dynamic programming, greedy algorithms and math techniques (`frameworks_2.py`). The explanations, code and tests are this book's own. Chapter 39d's lab, [`labs/coding-patterns`](../coding-patterns/README.md), holds the twenty basic interview patterns these chapters build on; nothing is imported from it, so each file here runs on its own.

## Requirements and quick start

Standard library only, Python 3.10 or newer (this run used 3.14.7). The tests are plain scripts with `assert` statements, not pytest suites, so run them directly; `-B` keeps the folder free of `__pycache__`.

```bash
cd labs/algorithm-frameworks
python3 -B test_ds_basics.py        # 39e: 25 groups, about 3.5 s; each line reports what was measured
python3 -B test_frameworks_1.py     # 39f: 23 groups, under 1 s
python3 -B test_frameworks_2.py     # 39g: 16 groups, about 4.5 s, with a timing and a note per group
python3 -B check_chapter_sync.py    # "39e: 68 ... 39f: 127 ... 39g: 125 objects and lines checked, 0 problem(s)"
```

Timings are from a 2024 laptop. `test_ds_basics.py` prints a measurement after each `ok`, for example `copies per op at most 1.36 (bound 2)` for the dynamic array and `measured false-positive rate 0.0103 (formula 0.0100)` for the Bloom filter. `test_frameworks_2.py` prints the node counts the chapter quotes, such as `8-queens: 2,057 nodes with pruning vs 109,601 in the full permutation tree`. `check_chapter_sync.py [39e 39f 39g]` extracts every Python code block from a chapter, splits it into `def` and `class` chunks (decorators included) and compares each with `inspect.getsource` of the same name in the matching module; blocks that start with `# illustration` are pseudocode sketches and are skipped.

| File | Chapter | What it holds |
|---|---|---|
| `ds_basics.py` | 39e | 1,796 lines: dynamic array, doubly linked list with sentinels, ring buffer, skip list, bitset, linked stack and queue, hash maps with chaining and with linear probing (backward-shift and tombstone deletion), a model of CPython's compact dict, `LinkedHashMap`, `ArrayHashMap`, Bloom filter, tree traversals, AVL tree, trie, binary heap, segment tree, Huffman coding, graph representations and traversals, Euler checks, union-find, the ten sorting algorithms |
| `test_ds_basics.py` | 39e | Random operation sequences compared with `list`, `dict`, `set`, `deque`, `OrderedDict`, `heapq`, `bisect` and `sorted`; cost checks (copies per append, heapify swaps, Shell sort growth, the Bloom filter's measured rate) |
| `frameworks_1.py` | 39f | 2,394 lines: traversal versus decomposition, linked-list and array two-pointer techniques, nSum, prefix sums and difference arrays, the sliding-window template and Rabin-Karp, binary search on bounds and predicates, monotonic stacks and queues, tree construction and serialization, BST operations, every LCA variant, merge-sort counting, quickselect, LRU and LFU caches, random-access sets, exam room, calculator, consistent hashing, segment trees, trie applications, bipartite checks, cycle detection, topological sort, Dijkstra variants, A*, Kruskal and Prim, Hierholzer, Floyd-Warshall |
| `test_frameworks_1.py` | 39f | Fixed examples plus 200 to 600 seeded random cases per group against brute force; reproduces the figures the chapter quotes (keys moved by consistent hashing, cells expanded by A*) |
| `frameworks_2.py` | 39g | 1,776 lines: the backtracking framework, the nine permutation/combination/subset forms, ball-and-box enumeration, island variants, BFS and bidirectional BFS, the DP framework and its classic problems, the knapsack family, grid and game DP, house robber and the stock state machine, greedy algorithms, math techniques, shuffles and reservoir sampling, ugly numbers, classic interview problems |
| `test_frameworks_2.py` | 39g | Brute-force references (`itertools`, exhaustive search on small instances), exact enumeration of every random draw for the sampling functions, deterministic node counts for the search comparisons the chapter reports |
| `check_chapter_sync.py` | all | Fails if a function, class, import or constant printed in a chapter differs from this folder's code |

Conventions: functions that LeetCode specifies as in-place mutate their input, and the tests pass copies. Indices are 0-based unless a docstring says otherwise. Functions that draw random numbers take an `rng` argument (default: the `random` module) so the tests can pass a seeded `random.Random` or a scripted source. Problems marked with a dagger in the chapters need LeetCode Premium.

## How to use this lab for interview practice

1. Read one section of 39e, 39f or 39g, then close the book.
2. Delete the body of one function or method in the matching file, keeping the signature and the docstring. The docstring states the problem and its LeetCode number, often with the key idea in a clause; cover that clause for the harder version.
3. Write the body from memory. For a recursive function, say first whether you are traversing (the walk carries state, the answer lives outside) or decomposing (the call returns the answer for its subtree); for a DP, write the definition of `dp` in one sentence before any code; for a greedy, state the exchange argument.
4. Run the matching test file. The randomized comparisons catch off-by-one errors, missing base cases and wrong loop directions.
5. Keep your version only if it passes; otherwise diff it against the reference and log the difference. Run `python3 -B check_chapter_sync.py` before committing, since the chapter must print the same code.

Timing targets, from chapter 39f's two-week plan: 15, 25 and 40 minutes for easy, medium and hard problems, talking out loud, with at least half solved without running code. Chapter 39g's three-week plan adds: type the backtracking skeleton and `bfs_shortest` from memory, draw each problem's decision tree before coding, and solve each DP top-down, then bottom-up, then in one row.

What `check_chapter_sync.py` guarantees: every function and class printed in the three chapters is byte-for-byte the tested one here. The chapters also quote measurements (resizes of a CPython list, keys moved by consistent hashing, states expanded by bidirectional BFS, Sudoku search nodes); the test files assert those, so the numbers in the prose are reproducible, not remembered.

## The families

One subsection per family: the intuition, the invariant that makes the code correct, an example whose output was produced by running it, the complexity, the pitfalls the tests catch, and practice problems from the chapters. The map at the end lists every function by section.

### 39e: Enumeration, arrays, linked lists and their variations

*Intuition.* Every algorithm starts as an enumeration of candidates; speed comes from pruning and reuse, which is all that separates the O(n³), O(n²) and O(n) versions of LC 53. A dynamic array doubles when full and halves at a quarter full, so appends are amortized O(1). Linked nodes make splicing O(1) next to a node you hold, and sentinels remove every special case; a ring buffer is a deque on a fixed array, a skip list a sorted map with random express lanes, a bitset membership in n bits.

*The invariant.* `max_subarray_linear`: `ending_here` is the best sum of a run ending at the current index. `DynamicArray`: between resizes the block is at least a quarter full, so copies stay within twice the operations. `DoublyLinkedList`: with a dummy head and tail every real node has real neighbors. `RingBuffer`: item i lives at `(start + i) % capacity`, and `size` tells empty from full.

```python
>>> from ds_basics import max_subarray_linear, cpython_list_growth, DynamicArray
>>> max_subarray_linear([-2, 1, -3, 4, -1, 2, 1, -5, 4])
6
>>> cpython_list_growth(20)
[4, 8, 16, 24]
>>> a = DynamicArray(); [a.append(i) for i in range(5)] and None; a.insert(0, 99)
>>> list(a), a.capacity(), a.moves
([99, 0, 1, 2, 3, 4], 8, 7)
>>> from ds_basics import DoublyLinkedList, RingBuffer, SkipList, Bitset
>>> d = DoublyLinkedList([1, 2, 3]); h = d.append(4)
>>> d.remove_node(h)                      # O(1): the handle, not an index
4
>>> _ = d.appendleft(0); list(d), list(reversed(d))
([0, 1, 2, 3], [3, 2, 1, 0])
>>> r = RingBuffer(3, when_full="overwrite"); [r.push_back(x) for x in (1, 2, 3, 4)] and None; list(r)
[2, 3, 4]
>>> s = SkipList(seed=1); [s.put(k, k * k) for k in (5, 1, 3)] and None; list(s), s.get(3), 4 in s
([1, 3, 5], 9, False)
>>> b = Bitset(16); b.add(3); b.add(9); list(b), len(b), 4 in b
([3, 9], 2, False)
```

*Complexity.* Amortized O(1) append; O(n) insert at the front; O(1) push, pop and removal by handle; O(min(i, n - i)) to reach index i; expected O(log n) per skip-list operation.

*Pitfalls.* Shifting the tail from the front in `insert` (values get overwritten); shrinking at half full, which makes alternating append and pop O(n); in `LinkedQueue`, not resetting the tail to the sentinel when the last item leaves. The tests run 300 random sequences against `list`, `deque` and `deque(maxlen=...)`, assert the copies-per-operation bound, and check `cpython_list_growth` against `sys.getsizeof` for 3,000 appends.

*Practice.* 53 Maximum Subarray (three versions); 283 Move Zeroes; 189 Rotate Array; 707 Design Linked List; 622 Design Circular Queue; 1206 Design Skiplist; 2166 Design Bitset; 155 Min Stack.

### 39e: Hash tables and their variations

*Intuition.* A hash function turns a key into a slot; collisions are resolved by chaining or by probing. CPython's dict keeps a sparse index table over a dense, insertion-ordered entry list, which is why dicts are ordered. A linked list on top gives an order (LRU); a dense key list gives O(1) random choice; a Bloom filter trades exactness for memory.

*The invariant.* Load-factor bounds keep probes short: chaining rehashes above 3/4, probing keeps half the slots empty. With backward-shift deletion every key still lies on its probe path from its home slot; with tombstones, probes step over deleted slots. `CompactDict` resizes at exactly the insertions where a real dict does.

```python
>>> from ds_basics import LinearProbingHashMap, CompactDict, LinkedHashMap, bloom_parameters, dict_probe_order
>>> m = LinearProbingHashMap(deletion="tombstone"); [m.put(k, k * 2) for k in "abcd"] and None; m.delete("b")
True
>>> sorted(m), m.get("c")
(['a', 'c', 'd'], 'cc')
>>> cd = CompactDict(); cd["x"] = 1; cd["y"] = 2; cd["z"] = 3; del cd["y"]; cd["y"] = 4; list(cd)
['x', 'z', 'y']
>>> lh = LinkedHashMap(access_order=True); lh.put("a", 1); lh.put("b", 2)
>>> lh.get("a"), list(lh)                 # the access moved "a" to the newest end
(1, ['b', 'a'])
>>> bloom_parameters(5000, 0.01)
(47926, 7)
>>> [next(it) for it in [dict_probe_order(17, 8)] for _ in range(5)]
[1, 6, 7, 4, 5]
```

*Complexity.* O(1) expected per operation; `random_key` O(1); about 9.6 bits per item for a 1% false-positive rate.

*Pitfalls.* In `_shift_back`, moving an entry whose home slot lies between the hole and its position (it becomes unreachable); mutating a stored key, after which equal keys never find the entry. The tests run tens of thousands of operations against `dict` and `OrderedDict`, including all-colliding keys, assert the cluster invariant after every deletion, and measure the Bloom filter on 5,000 items.

*Practice.* 705 Design HashSet; 706 Design HashMap; 49 Group Anagrams; 146 LRU Cache; 380 Insert Delete GetRandom O(1); 710 Random Pick with Blacklist.

### 39e: Binary trees, balanced trees, tries, heaps, segment trees and Huffman coding

*Intuition.* Preorder, inorder and postorder are three positions in one walk; what the code can see at each position decides what it can compute (depth flows down as a parameter, size flows up as a return value). A BST is an ordered map only while balanced, and rotations fix heights on the way back up. A trie stores strings along shared prefixes; a heap is a complete tree in an array, built bottom-up in O(n); a segment tree answers range queries for any associative operation; Huffman coding merges the two lightest trees.

*The invariant.* `level_order_by_depth`: the queue length read once per level is that level's width. `shallowest_dfs` keeps searching after a hit, pruning deeper branches. AVL: sibling heights differ by at most one, restored in postorder. Heap: `a[i]` comes before children `2i + 1` and `2i + 2`. Segment tree: each node stores the combine of its range.

```python
>>> from ds_basics import build_tree, three_orders, level_order_by_depth, root_to_leaf_sums, shallowest_bfs, is_leaf
>>> t = build_tree([1, 2, 3, 4, 5, None, 6])
>>> three_orders(t)
([1, 2, 4, 5, 3, 6], [4, 2, 5, 1, 3, 6], [4, 5, 2, 6, 3, 1])
>>> level_order_by_depth(t), root_to_leaf_sums(t), shallowest_bfs(t, is_leaf)
([[1], [2, 3], [4, 5, 6]], [7, 8, 10], 3)
>>> from ds_basics import AVLTree, Trie, heapify, SegmentTree, huffman_codes
>>> avl = AVLTree(); [avl.put(k, None) for k in range(1, 16)] and None; avl.height(), avl.floor(7), avl.ceiling(16)
(4, 7, None)
>>> tr = Trie(); [tr.insert(w) for w in ("car", "card", "care", "cat")] and None
>>> tr.keys_with_prefix("car"), tr.longest_prefix_of("cards")
(['car', 'card', 'care'], 'card')
>>> a = [5, 3, 8, 1, 9, 2]; heapify(a)    # returns the number of swaps
4
>>> a
[1, 3, 2, 5, 9, 8]
>>> seg = SegmentTree([1, 3, 5, 7, 9]); seg.update(1, 10); seg.query(0, 2)
16
>>> huffman_codes({"a": 45, "b": 13, "c": 12, "d": 16, "e": 9, "f": 5})
{'a': '0', 'c': '100', 'b': '101', 'f': '1100', 'e': '1101', 'd': '111'}
```

*Complexity.* O(n) traversals; O(log n) per AVL, heap and segment-tree operation; O(n) heapify; O(L) per trie operation for a word of length L; O(k log k) for Huffman over k symbols.

*Pitfalls.* Reading `len(queue)` inside the inner loop (levels blur); rotating once in the left-right case (straighten the kink first); deleting from a trie without pruning, so `starts_with` reports prefixes of deleted words. The tests compare 400 random binary trees and 200 n-ary trees with recursive references, check AVL heights against the Fibonacci bound after 18,000 operations, heapify swaps against n minus popcount(n), and Huffman optimality against a brute force over the Kraft inequality.

*Practice.* 144, 94, 145 Binary Tree Traversals (recursively, then with a stack); 102 Level Order Traversal; 111 Minimum Depth; 450 Delete Node in a BST; 1382 Balance a BST; 208 Implement Trie; 703 Kth Largest Element in a Stream; 307 Range Sum Query - Mutable.

### 39e: Graphs

*Intuition.* Two representations, two traversals, and the distinction interviews turn on: mark vertices when each should be visited once, mark the current path when a vertex may lie on many answers. Union-find answers connectivity as edges arrive; degree parity decides whether an Euler trail exists.

*The invariant.* BFS marks on enqueue, so the first visit is the closest. `all_paths` keeps an `on_path` set removed in postorder, so other paths may reuse the vertex. `DisjointSet` puts the smaller tree under the larger, so depth grows only when size doubles, and compresses paths on find.

```python
>>> from ds_basics import adjacency_list, bfs_distances, all_paths, DisjointSet, euler_kind
>>> g = adjacency_list(4, [(0, 1), (1, 2), (2, 3), (0, 3)]); bfs_distances(g, 0)
{0: 0, 1: 1, 3: 1, 2: 2}
>>> all_paths([[1, 2], [3], [3], []], 0, 3)
[[0, 1, 3], [0, 2, 3]]
>>> ds = DisjointSet(5); ds.union(0, 1), ds.union(3, 4), ds.count, ds.connected(1, 3)
(True, True, 3, False)
>>> euler_kind(4, [(0, 1), (1, 2), (2, 3), (3, 0)]), euler_kind(3, [(0, 1), (1, 2)])
('circuit', 'path')
```

*Complexity.* O(V + E) for the traversals; near-constant amortized per union-find operation; `all_paths` is output-bound.

*Pitfalls.* A visited set in `all_paths` (loses paths); skipping the connectivity check in `euler_kind` (edges in two pieces have the right degrees but no trail). The tests compare 200 random graphs with reference traversals and 300 Euler classifications with brute force.

*Practice.* 797 All Paths From Source to Target; 1971 Find if Path Exists in Graph; 547 Number of Provinces; 1319 Number of Operations to Make Network Connected.

### 39e: The ten sorting algorithms

*Intuition.* Quick sort does its work before the recursion (partition, then sort the sides); merge sort does it after (sort the halves, then merge): preorder versus postorder again, which is why merge sort can count inversions. Counting, bucket and radix sort escape the n log n bound by not comparing.

*The invariant.* Three-way partition: `a[lo:lt] < pivot`, `a[lt:i] == pivot`, `a[gt+1:hi+1] > pivot`. Merge: ties take the left item, so the sort is stable. Counting sort places right to left, so equal items keep their order, which radix sort needs per digit.

```python
>>> from ds_basics import count_inversions, radix_sort, bucket_sort
>>> count_inversions([5, 2, 4, 1])
5
>>> a = [170, 45, 75, -90, 802, 24, 2, 66]; radix_sort(a); a
[-90, 2, 24, 45, 66, 75, 170, 802]
>>> a = [0.42, 0.32, 0.23, 0.52, 0.25, 0.47]; bucket_sort(a); a
[0.23, 0.25, 0.32, 0.42, 0.47, 0.52]
```

*Complexity.* O(n²) for selection, bubble and insertion (insertion is O(n + inversions)); about O(n^1.25) for Shell sort; O(n log n) expected for quick sort with O(log n) stack by recursing on the smaller side; O(n log n) for merge and heap sort; O(n + k) counting, O(d(n + base)) radix.

*Pitfalls.* Recursing on both sides of quick sort (O(n) stack on sorted input); `<=` instead of `<` in bubble sort, which breaks stability. The tests sort 206 integer and 50 float inputs with all ten algorithms, confirm stability for the six stable ones and find a broken example for each of the other four, and measure Shell sort's growth exponent.

*Practice.* 912 Sort an Array (merge, heap, quick and counting); 75 Sort Colors; 148 Sort List; 315 Count of Smaller Numbers After Self; 493 Reverse Pairs.

### 39f: Traversal versus decomposition

*Intuition.* Every recursive function is written one of two ways. Traversal: a walk carries state down and the answer accumulates outside. Decomposition: the call returns the answer for its subtree, built from the children's answers. Backtracking is traversal of a decision tree; dynamic programming is decomposition with memoization.

*The invariant.* In traversal, the parameters describe the path above the node (`high` is the largest value on it). In decomposition, the return value is a complete answer for the subtree. `node_report` shows all three positions: depth known on entry, inorder rank between the children, size on exit.

```python
>>> from frameworks_1 import build_tree, good_nodes_traverse, good_nodes_decompose, node_report, climb_stairs_decompose
>>> t = build_tree([3, 1, 4, 3, None, 1, 5]); good_nodes_traverse(t), good_nodes_decompose(t)
(4, 4)
>>> node_report(build_tree([1, 2, 3]))
[(1, 0, 3, 1), (2, 1, 1, 0), (3, 1, 1, 2)]
>>> climb_stairs_decompose(5)
8
```

*Complexity.* O(n) for the tree walks; `leaves_decompose` copies lists, O(n × height); `climb_stairs_traverse` is exponential, the memoized decomposition O(n).

*Pitfalls.* Mixing the two styles, so the caller gets half an answer; forgetting the memo in decomposition. The tests compare the paired versions on 400 random trees and the stair counts up to n = 20.

*Practice.* 1448 Count Good Nodes in Binary Tree; 872 Leaf-Similar Trees; 104 Maximum Depth; 543 Diameter; 70 Climbing Stairs.

### 39f: Linked lists and arrays with two pointers

*Intuition.* Dummy heads make splicing uniform; a pointer gap of k finds the kth from the end in one pass; switching heads makes two pointers meet at an intersection. Recursive reversal trusts the definition "returns the head of the reversed rest". On arrays, read/write pointers edit in place, left/right pointers reverse and rotate, and nSum recurses down to 2Sum.

*The invariant.* `reverse_first_n`: after the recursive call, `head.next` is the tail of the reversed block and still points at the successor. `remove_duplicates_keep_k`: `nums[write - k] != x` means x is not the (k + 1)th copy. `n_sum`: sorted input, first elements chosen in index order, equal first values skipped, so every tuple appears once.

```python
>>> from frameworks_1 import build_list, list_values, reverse_first_n, delete_duplicates_all, n_sum, spiral_order, rotate_array
>>> list_values(reverse_first_n(build_list([1, 2, 3, 4, 5]), 3))
[3, 2, 1, 4, 5]
>>> list_values(delete_duplicates_all(build_list([1, 2, 3, 3, 4, 4, 5])))
[1, 2, 5]
>>> n_sum([-1, 0, 1, 2, -1, -4], 3, 0)
[[-1, -1, 2], [-1, 0, 1]]
>>> spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
[1, 2, 3, 6, 9, 8, 7, 4, 5]
>>> a = [1, 2, 3, 4, 5, 6, 7]; rotate_array(a, 3); a
[5, 6, 7, 1, 2, 3, 4]
```

*Complexity.* O(n) for the list operations and in-place edits; O(n²) for `longest_palindrome` and 3Sum; O(n^(k-1)) for nSum.

*Pitfalls.* Forgetting `large_tail.next = None` in `partition_list`, which can close a cycle (the test's `vals` helper fails loudly on cycles); in `spiral_order`, reading the bottom row or left column twice when one row or column remains. The tests compare random lists and arrays with slicing and `itertools` references.

*Practice.* 21 Merge Two Sorted Lists; 86 Partition List; 19 Remove Nth Node From End; 160 Intersection of Two Linked Lists; 82 Remove Duplicates II; 92 Reverse Linked List II; 80 Remove Duplicates from Sorted Array II; 48 Rotate Image; 54 Spiral Matrix; 18 4Sum.

### 39f: Prefix sums, sliding windows and binary search

*Intuition.* Prefix sums answer range sums in O(1) after O(n) setup; a difference array applies range updates in O(1) each. The sliding-window template asks three questions at each step: what changes when `s[right]` enters, when should the window shrink, where is the answer read. Binary search is one closed interval and three searches (exact, leftmost, rightmost), and any false-then-true predicate can be searched the same way, which turns "least capacity that works" into `first_true`.

*The invariant.* `prefix[i]` is the sum of `nums[:i]`. The window's left edge only moves forward, so each element enters and leaves once; when the condition is not monotone (exactly k distinct), change the question to `at_most(k) - at_most(k - 1)`. `left_bound`: `nums[:lo] < target <= nums[hi + 1:]`, so on exit `lo` is the insertion point; `first_true`: everything below `lo` is false, everything above `hi` is true.

```python
>>> from frameworks_1 import NumArray, car_pooling, check_inclusion, subarrays_with_k_distinct, str_str_rabin_karp
>>> NumArray([-2, 0, 3, -5, 2, -1]).sum_range(2, 5)
-1
>>> car_pooling([[2, 1, 5], [3, 3, 7]], 4), car_pooling([[2, 1, 5], [3, 3, 7]], 5)
(False, True)
>>> check_inclusion("ab", "eidbaooo"), subarrays_with_k_distinct([1, 2, 1, 2, 3], 2)
(True, 7)
>>> str_str_rabin_karp("sadbutsad", "sad")
0
>>> from frameworks_1 import binary_search, left_bound, right_bound, first_true, ship_within_days, advantage_count
>>> nums = [1, 2, 2, 2, 3]; binary_search(nums, 2), left_bound(nums, 2), right_bound(nums, 2), left_bound(nums, 4)
(2, 1, 3, -1)
>>> first_true(0, 100, lambda x: x * x >= 50)
8
>>> ship_within_days([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5)
15
>>> advantage_count([2, 7, 11, 15], [1, 10, 4, 11])
[2, 11, 7, 15]
```

*Complexity.* O(1) per range query after O(n) setup; O(n) per window pass, O(26n) for LC 395, O(n + m) expected for Rabin-Karp; O(log n) per binary search, O(n log(sum)) for the capacity searches.

*Pitfalls.* Off-by-one on the half-open range in the difference array (riders leave at `end`, so the update covers `end - 1`); updating `best` before shrinking for a "longest" window; shrinking with `hi = mid` under `while lo <= hi` (infinite loop); a search bound that excludes the answer. The tests enumerate every subarray and substring of random inputs, compare the bounds with `bisect` on 600 random arrays, and check the capacity searches with a brute-force partition.

*Practice.* 303 Range Sum Query; 304 Range Sum Query 2D; 1109 Corporate Flight Bookings; 1094 Car Pooling; 567 Permutation in String; 1004 Max Consecutive Ones III; 992 Subarrays with K Different Integers; 187 Repeated DNA Sequences; 34 Find First and Last Position (both conventions); 1011 Capacity To Ship Packages Within D Days; 410 Split Array Largest Sum; 528 Random Pick with Weight; 870 Advantage Shuffle.

### 39f: Stacks, queues and monotonic structures

*Intuition.* A queue from two stacks is amortized O(1) because each item crosses once. `nearest_index` is the whole monotonic-stack family in one function: pass the comparison and the direction. A monotonic queue is a FIFO queue that also reports its maximum and minimum, which solves sliding-window maxima and "longest window with max - min within a limit".

*The invariant.* `nearest_index`: the waiting stack holds indices whose answer has not arrived, with values monotone. `MaxMinQueue`: an item that leaves before a larger one and is no larger can never be the maximum again, so it is dropped on push; the front candidate is popped when its arrival number departs.

```python
>>> from frameworks_1 import nearest_index, sum_subarray_mins, longest_subarray_within_limit, remove_duplicate_letters
>>> import operator
>>> nearest_index([2, 1, 2, 4, 3], operator.lt)
[1, -1, -1, 4, -1]
>>> sum_subarray_mins([3, 1, 2, 4]), longest_subarray_within_limit([8, 2, 4, 7], 4)
(17, 2)
>>> remove_duplicate_letters("cbacdcbc")
'acdb'
```

*Complexity.* Amortized O(1) per operation; O(n) for every array function.

*Pitfalls.* In `sum_subarray_mins`, strict comparison on both sides (equal minimums counted twice: one side strict, the other not); in `MaxMinQueue`, forgetting to pop the candidate deque when the departing item is its front. The tests compare with O(n²) scans and with a plain list for the queues.

*Practice.* 232 Implement Queue using Stacks; 225 Implement Stack using Queues; 907 Sum of Subarray Minimums; 239 Sliding Window Maximum; 1438 Longest Continuous Subarray With Absolute Diff Within Limit; 316 Remove Duplicate Letters.

### 39f: Binary trees in action, BSTs, LCA and the follow-ups

*Intuition.* Construction finds the root, splits the traversals and recurses. Postorder is where a node sees both subtrees, so duplicate subtrees get a postorder id. Inorder of a BST is sorted, which gives kth smallest, validation by ranges and the greater-sum tree by reverse inorder. LCA has five forms sharing one search. Merge sort as postorder counts inversions while merging; quickselect is quicksort with one branch.

*The invariant.* `build_tree_pre_in`: preorder starts with the root; the k inorder values before it form the left subtree. `is_valid_bst`: every value lies in the open interval passed down. `lca_maybe_missing`: both children are searched before the node tests itself, so a found count of 2 is trustworthy. `count_smaller`: when both halves are sorted, the right-side items merged before `nums[i]` are exactly the later smaller ones.

```python
>>> from frameworks_1 import build_tree, serialize_level, build_tree_pre_in, construct_maximum_binary_tree_stack, delete_node, kth_smallest, lca_deepest_leaves, count_smaller, reverse_pairs
>>> serialize_level(build_tree_pre_in([3, 9, 20, 15, 7], [9, 3, 15, 20, 7]))
'3,9,20,#,#,15,7'
>>> serialize_level(construct_maximum_binary_tree_stack([3, 2, 1, 6, 0, 5]))
'6,3,5,#,2,0,#,#,1'
>>> bst = build_tree([5, 3, 6, 2, 4, None, 7]); kth_smallest(bst, 3), serialize_level(delete_node(bst, 3))
(4, '5,4,6,2,#,#,7')
>>> lca_deepest_leaves(build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])).val
2
>>> count_smaller([5, 2, 6, 1]), reverse_pairs([1, 3, 2, 3, 1])
([2, 1, 1, 0], 2)
```

*Complexity.* O(n) construction with a position map; O(h) per BST operation; O(log² n) for `count_nodes`; O(n log n) for the merge-sort counts; expected O(n) for quickselect.

*Pitfalls.* Validating a BST by comparing only parent and child; in `delete_node` with two children, forgetting to unhook the successor's right subtree. The tests rebuild 300 random trees from every traversal pair, compare BST operations with `bisect`, check every LCA against the paths from the root, and compare the counts with O(n²) scans.

*Practice.* 226 Invert Binary Tree; 114 Flatten Binary Tree; 654 Maximum Binary Tree; 105, 106, 889 Construct Binary Tree from traversal pairs; 652 Find Duplicate Subtrees; 297 Serialize and Deserialize; 230 Kth Smallest in a BST; 1373 Maximum Sum BST; 236, 235, 1123 LCA variants; 222 Count Complete Tree Nodes; 341 Flatten Nested List Iterator; 315, 493, 327 merge-sort counting; 215 Kth Largest Element.

### 39f: Designing data structures

*Intuition.* Design questions combine two structures so each operation is O(1) or O(log n): a dict plus a doubly linked list (LRU), a dict plus frequency buckets (LFU), a list plus a position map (random access with O(1) deletion), a heap of free stretches with lazy invalidation (exam room), recursive descent (calculator), a sorted ring of hashed points (consistent hashing), a lazy segment tree (range add), a trie with payloads (word dictionaries).

*The invariant.* `LRUCacheLinked`: `head.next` is the oldest entry, `tail.prev` the newest. `LFUCache`: `min_freq` is the smallest key of `buckets`, reset to 1 on insertion. `RandomizedSet`: `index[v]` is the position of v in `values`, kept by moving the last element into any hole. `ExamRoom`: a popped stretch is used only if `right_of[a] == b` still holds. `RangeAddTree`: a node's `pending` is pushed down before either child is read.

```python
>>> from frameworks_1 import LFUCache, ExamRoom, calculate, RangeAddTree, MapSum
>>> l = LFUCache(2); l.put(1, 1); l.put(2, 2); _ = l.get(1); l.put(3, 3)   # key 2 is the least used
>>> l.get(2), l.get(3), l.get(1)
(-1, 3, 1)
>>> er = ExamRoom(10); [er.seat() for _ in range(4)]
[0, 9, 4, 2]
>>> calculate("(1+(4+5+2)-3)+(6+8)"), calculate("14-3/2"), calculate("-7/2")
(23, 13, -3)
>>> rt = RangeAddTree(0, 9); rt.add(2, 5, 3); rt.add(4, 8, 2); rt.query(0, 9)
(22, 5)
>>> ms = MapSum(); ms.insert("apple", 3); ms.insert("app", 2); ms.insert("apple", 5); ms.sum("ap")
7
```

*Complexity.* O(1) for the caches and random sets; O(log n) for the exam room, segment trees and ring lookups; O(n) for the calculator.

*Pitfalls.* In `RandomizedCollection.remove`, updating the moved element's position set in the wrong order; in `LFUCache`, deleting an emptied bucket without advancing `min_freq`; in `calculate`, dividing with `//` (rounds toward negative infinity; the problem truncates toward zero). The tests run thousands of random operations against `OrderedDict`, a `Counter`, `eval` on random expressions and a brute-force array, and reproduce the chapter's consistent-hashing figures with 20,000 keys.

*Practice.* 146 LRU Cache (without `OrderedDict`); 460 LFU Cache; 380, 381 Insert Delete GetRandom O(1); 710 Random Pick with Blacklist; 855 Exam Room; 224, 227, 772 Basic Calculator; 307 Range Sum Query - Mutable; 732 My Calendar III; 648 Replace Words; 211 Design Add and Search Words; 677 Map Sum Pairs.

### 39f: Graph algorithms

*Intuition.* Two-coloring by BFS tests bipartiteness; three DFS states (new, on the path, finished) find directed cycles and give topological order as reversed postorder. Union-find over hashable items handles grids and equations. Dijkstra generalizes to products, bottleneck paths and constrained states; A* is Dijkstra with a heuristic ordering the heap. Kruskal and Prim build spanning trees; Hierholzer finds Euler paths; Floyd-Warshall gives all pairs in O(n³).

*The invariant.* Dijkstra settles a node the first time it leaves the heap; later entries are stale. `find_cheapest_price` keeps, per city, the fewest flights among expanded states, so a state with more flights and higher cost is pruned safely. Hierholzer appends a node to the route only when it has no unused edges left, so the reversed route is a trail.

```python
>>> from frameworks_1 import is_bipartite, find_directed_cycle, topo_sort_dfs, minimum_effort_path, find_cheapest_price, astar_grid, kruskal_mst, prim_mst, find_itinerary, find_the_city
>>> is_bipartite([[1, 3], [0, 2], [1, 3], [0, 2]]), find_directed_cycle(4, [(0, 1), (1, 2), (2, 0), (2, 3)])
(True, [0, 1, 2, 0])
>>> topo_sort_dfs(4, [(0, 1), (0, 2), (1, 3), (2, 3)])
[0, 2, 1, 3]
>>> minimum_effort_path([[1, 2, 2], [3, 8, 2], [5, 3, 5]])
2
>>> find_cheapest_price(4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1)
700
>>> astar_grid([[0, 0, 0, 0], [1, 1, 0, 1], [0, 0, 0, 0], [0, 1, 1, 0]], (0, 0), (3, 3))
(6, 8)
>>> edges = [(0, 1, 4), (0, 2, 1), (1, 2, 2), (1, 3, 5), (2, 3, 8)]; kruskal_mst(4, edges), prim_mst(4, edges)
(8, 8)
>>> find_itinerary([["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]])
['JFK', 'MUC', 'LHR', 'SFO', 'SJC']
>>> find_the_city(4, [[0, 1, 3], [1, 2, 1], [1, 3, 4], [2, 3, 1]], 4)
3
```

*Complexity.* O(V + E) for coloring, cycles and topological order; O(E log V) for Dijkstra, Prim and A*; O(E log E) for Kruskal; O(n²) for `min_cost_connect_points`; O(n³) for Floyd-Warshall.

*Pitfalls.* A plain visited set in the directed-cycle check (cross edges look like back edges); in LC 787, settling a city on first pop as plain Dijkstra does (a costlier path with fewer stops may be the only one within k); forgetting reverse edges before Floyd-Warshall on an undirected graph. The tests compare with Kahn's algorithm, a brute-force MST over edge subsets, Dijkstra with explicit stop counts, BFS on grids, and all permutations for itineraries.

*Practice.* 785 Is Graph Bipartite?; 207 Course Schedule (both ways); 130 Surrounded Regions; 990 Satisfiability of Equality Equations; 1514 Path with Maximum Probability; 1631 Path With Minimum Effort; 787 Cheapest Flights Within K Stops; 1584 Min Cost to Connect All Points; 332 Reconstruct Itinerary; 1334 Find the City.

### 39g: Backtracking, the nine forms, balls and boxes

*Intuition.* Brute-force search is enumeration on a decision tree; backtracking does its work on the edges (choose, explore, unchoose). The nine forms are a table, elements distinct, duplicated or reusable against subsets, combinations or permutations, covered by three rules: a start index to avoid reordering, sort-and-skip to avoid duplicates, recurse with `i` instead of `i + 1` to allow reuse. Every enumeration has two perspectives, each ball picks a box or each box picks its balls, and one is usually much smaller.

*The invariant.* On return from each branch, `path`, `used` and the attack arrays are what they were before the choice. In `permute_unique`, equal values are placed in index order (`not used[i - 1]` skips). In `can_partition_k_buckets`, buckets are interchangeable, so a new bucket always takes the first unused number, and a used-set that failed at a bucket boundary is never retried.

```python
>>> from frameworks_2 import permute_unique, combine_with_reuse, total_n_queens_bitmask, can_partition_k_balls, count_balanced
>>> permute_unique([1, 1, 2])
[[1, 1, 2], [1, 2, 1], [2, 1, 1]]
>>> combine_with_reuse([1, 2, 3], 2)
[[1, 1], [1, 2], [1, 3], [2, 2], [2, 3], [3, 3]]
>>> total_n_queens_bitmask(8)
92
>>> stats = {}; can_partition_k_balls([4, 3, 2, 3, 5, 2, 1], 4, stats), stats
(True, {'nodes': 8})
>>> count_balanced(3), count_balanced(4)
(5, 14)
```

*Complexity.* Output-bound: O(n · n!) for permutations, O(n · 2ⁿ) for subsets; the bitmask queens and the propagating Sudoku solver are the same search with cheaper checks and stronger pruning.

*Pitfalls.* Skipping duplicates with `used[i - 1]` instead of `not used[i - 1]` (still correct, but explores far more nodes; the tests count both); in the Sudoku propagator, undoing only the guess instead of everything the call placed. The tests compare all nine forms with `itertools`, verify 62 random solved Sudokus and 18 proved unsolvable, and count search nodes for 24 "no" instances of LC 698 in all three views.

*Practice.* 46 Permutations; 51, 52 N-Queens; 37 Sudoku Solver; 78, 90, 77, 216, 39, 40, 47 the nine forms; 698 Partition to K Equal Sum Subsets; 473 Matchsticks to Square; 22 Generate Parentheses.

### 39g: Islands and the BFS framework

*Intuition.* Flood fill makes the grid its own visited set; sinking border-connected land first turns enclaves and closed islands into a count. BFS on a state space (lock wheels, puzzle boards, genes) finds the fewest moves; expanding from both ends cuts the explored states by an order of magnitude. Multi-source BFS starts with every source in the queue; 0-1 BFS uses a deque with free moves at the front.

*The invariant.* BFS marks a state when it is queued, so the first time a state is seen is at its shortest distance. In `bidirectional_bfs`, the first meeting lies on a shortest path because the smaller frontier is expanded one full level at a time. In `num_distinct_islands`, the walk records a back marker on leaving, without which two different shapes serialize identically.

```python
>>> from frameworks_2 import open_lock, bfs_shortest, bidirectional_bfs, sliding_puzzle, oranges_rotting, minimum_obstacles, num_distinct_islands
>>> open_lock(["0201", "0101", "0102", "1212", "2002"], "0202")
6
>>> turns = lambda s: [s[:i] + str((int(s[i]) + d) % 10) + s[i + 1:] for i in range(4) for d in (1, -1)]
>>> bfs_shortest("0000", "0202", turns), bidirectional_bfs("0000", "0202", turns)
((4, 95), (4, 13))
>>> sliding_puzzle([[1, 2, 3], [4, 0, 5]]), sliding_puzzle([[1, 2, 3], [5, 4, 0]])
(1, -1)
>>> oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]), minimum_obstacles([[0, 1, 1], [1, 1, 0], [1, 1, 0]])
(4, 2)
>>> num_distinct_islands([[1, 1, 0, 1, 1], [1, 0, 0, 0, 0], [0, 0, 0, 0, 1], [1, 1, 0, 1, 1]])
3
```

*Complexity.* O(rows × cols) for the grids; O(states × moves) for BFS; bidirectional BFS explores about twice the square root of what plain BFS does.

*Pitfalls.* Marking on dequeue (states enter the queue many times); in `oranges_rotting`, counting a minute when no orange turned; in 0-1 BFS, refusing to improve a state after it was queued. The tests compare both searches with a layered reference BFS on 400 random graphs, show that a bidirectional search alternating per state instead of per level returns 4 where the answer is 3, sum the expansion counts over 60 seeded lock instances (248,752 plain versus 50,096 bidirectional), and verify every 2 × 3 puzzle board against the parity rule.

*Practice.* 1020 Number of Enclaves; 1905 Count Sub Islands; 694 Number of Distinct Islands; 752 Open the Lock; 773 Sliding Puzzle; 433 Minimum Genetic Mutation; 127 Word Ladder; 994 Rotting Oranges; 542 01 Matrix; 2290 Minimum Obstacle Removal.

### 39g: Dynamic programming: the framework, strings, knapsacks, grids, games and stocks

*Intuition.* DP applies when a brute-force recursion has overlapping subproblems and optimal substructure; four questions find the transition (state, choices, base case, fill order), and each problem goes from brute force to memo to table to one row. Subsequence problems use one index (LIS) or two (edit distance, LCS). The knapsack family is one table over capacity: 0-1 fills right to left, unbounded left to right, and loop order decides whether you count combinations (coins outside) or permutations (amounts outside). The dungeon runs backwards; burst balloons thinks about the last move; game DP tracks the score difference; all six stock problems are one state machine over (buys so far, holding or not).

*The invariant.* `dp[i]` means one sentence, stated before any code: the fewest coins making amount i; the longest increasing subsequence ending at `nums[i]`; the edits turning `word1[:i]` into `word2[:j]`. Loop order follows dependencies: `num_distinct` fills right to left so each character is used at most once; `longest_palindrome_subseq` runs i downward and j upward. `calculate_minimum_hp`: `need[c]` is the least health that survives from cell (r, c) onward, never below 1. `max_profit`: `free[d][t]` and `hold[t]` are the best cash after day d with t buys; a buy after a sale reads `free` from `cooldown` days back.

```python
>>> from frameworks_2 import coin_change_table, longest_increasing_subsequence, max_envelopes, word_break_all, edit_script, longest_palindrome_subseq, num_distinct
>>> coin_change_table([1, 2, 5], 11), longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18])
(3, [2, 3, 7, 18])
>>> max_envelopes([[5, 4], [6, 4], [6, 7], [2, 3]]), num_distinct("rabbbit", "rabbit")
(3, 3)
>>> word_break_all("catsanddog", ["cat", "cats", "and", "sand", "dog"])
['cat sand dog', 'cats and dog']
>>> edit_script("horse", "ros")
(3, [('replace', 'h', 'r'), ('keep', 'o'), ('delete', 'r'), ('keep', 's'), ('delete', 'e')])
>>> longest_palindrome_subseq("bbbab")
4
>>> from frameworks_2 import knapsack_items, change, combination_sum4, calculate_minimum_hp, super_egg_drop, max_coins, rob_circular, max_profit
>>> knapsack_items([1, 2, 3, 5], [1, 6, 10, 16], 7)
(22, [1, 3])
>>> change(5, [1, 2, 5]), combination_sum4([1, 2, 3], 4)
(4, 7)
>>> calculate_minimum_hp([[-2, -3, 3], [-5, -10, 1], [10, 30, -5]]), super_egg_drop(2, 100), max_coins([3, 1, 5, 8])
(7, 14, 167)
>>> rob_circular([2, 3, 2]), max_profit([3, 3, 5, 0, 0, 3, 1, 4], k=2), max_profit([1, 2, 3, 0, 2], cooldown=1), max_profit([1, 3, 2, 8, 4, 9], fee=2)
(3, 6, 3, 8)
```

*Complexity.* O(amount × coins) for coin change; O(n log n) for LIS with patience piles; O(mn) for two-index string problems with O(min(m, n)) space in one row; O(n × capacity) for the knapsacks; O(rows × cols) for grids; O(n³) for burst balloons; O(k log n) for the egg drop; O(days × k) for stocks.

*Pitfalls.* A memo sentinel of 0 or -1 when those are real answers (`min_falling_path_sum_memo` uses `None`); sorting envelopes by height ascending within equal widths (same-width envelopes would nest); iterating capacities upward in the 0-1 knapsack (allows reuse); solving the dungeon forward (the tests show it answers 5 where the truth is 4). The tests check every DP against exhaustive enumeration on small inputs, replay each edit script to confirm it produces the target, and try every mix of k, fee and cooldown against brute force.

*Practice.* 322 Coin Change; 300 Longest Increasing Subsequence; 354 Russian Doll Envelopes; 115 Distinct Subsequences; 139, 140 Word Break; 72 Edit Distance; 1143 Longest Common Subsequence; 516 Longest Palindromic Subsequence; 416 Partition Equal Subset Sum; 518 Coin Change II; 377 Combination Sum IV; 494 Target Sum; 64 Minimum Path Sum; 174 Dungeon Game; 10 Regular Expression Matching; 887 Super Egg Drop; 312 Burst Balloons; 486 Predict the Winner; 198, 213, 337 House Robber; 121, 122, 123, 188, 309, 714 Best Time to Buy and Sell Stock.

### 39g: Greedy algorithms

*Intuition.* A greedy choice is safe when an exchange argument shows any optimal solution can be rewritten to include it. Interval scheduling keeps the earliest end; a sweep line counts overlaps; jump games track the farthest reachable index and count levels like a BFS without a queue; the gas station restarts after the tank goes negative. `greedy_coin_count` is the counterexample: largest coin first is wrong for coins 1, 3, 4.

*The invariant.* `find_min_arrow_shots`: after sorting by end, an arrow at the current end bursts every balloon that starts before it, and none can do better. `jump`: `level_end` is the farthest index reachable with the current number of jumps. `can_complete_circuit`: if the running tank first goes negative at i, no start in `[start, i]` can work.

```python
>>> from frameworks_2 import find_min_arrow_shots, jump, can_complete_circuit, video_stitching, greedy_coin_count
>>> find_min_arrow_shots([[10, 16], [2, 8], [1, 6], [7, 12]]), jump([2, 3, 1, 1, 4])
(2, 2)
>>> can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2])
3
>>> video_stitching([[0, 2], [4, 6], [8, 10], [1, 9], [1, 5], [5, 9]], 10)
3
>>> greedy_coin_count([1, 3, 4], 6)
3
```

*Complexity.* O(n log n) with a sort, O(n) otherwise.

*Pitfalls.* Sorting arrows by start instead of end; `start >= last_shot` for closed intervals sharing an endpoint (one arrow bursts both, so the test is strict); in `jump`, scanning the last index (it would add a jump that never happens). The tests compare with exhaustive search on small inputs and show the coin counterexample (greedy 3 coins, optimum 2).

*Practice.* 435 Non-overlapping Intervals; 452 Minimum Number of Arrows; 253 Meeting Rooms II; 55 Jump Game; 45 Jump Game II; 134 Gas Station; 1024 Video Stitching; 763 Partition Labels.

### 39g: Math techniques, randomness and probability

*Intuition.* One-line answers have reasons: Nim is lost on multiples of 4, bulb i is toggled once per divisor so only squares stay on, `n & (n - 1)` clears the lowest set bit. Fast powers square repeatedly; the sieve marks multiples from i²; factorial zeros count factors of 5. Shuffling and reservoir sampling must be exactly uniform. Probability puzzles are computed exactly with `Fraction`. Ugly numbers are a k-way merge of multiplied streams.

*The invariant.* `fisher_yates`: slot i receives a uniform choice from the unplaced items i..n-1, so each permutation has probability 1/n!. `reservoir_sample`: after item i, each item seen so far is in the sample with probability k/(i + 1). `nth_ugly_number`: every stream that produced the minimum advances, so no value is appended twice.

```python
>>> from frameworks_2 import count_bits, super_pow, count_primes, preimage_size_fzf, monty_hall_exact, nth_ugly_number, nth_ugly_number_iii
>>> count_bits(5), super_pow(2, [1, 0]), count_primes(10 ** 6)
([0, 1, 1, 2, 1, 2], 1024, 78498)
>>> preimage_size_fzf(5), preimage_size_fzf(6)
(0, 5)
>>> monty_hall_exact(True), monty_hall_exact(False)
(Fraction(2, 3), Fraction(1, 3))
>>> nth_ugly_number(10), nth_ugly_number_iii(3, 2, 3, 5)
(12, 4)
```

*Complexity.* O(log exp) for `mod_pow`; O(n log log n) for the sieve; O(n) for a shuffle; O(k) memory for reservoir sampling; O(n log n) for heap-based super ugly numbers; O(log(n × min(a, b, c))) for LC 1201.

*Pitfalls.* `naive_shuffle` (swap with any index) gives n^n equally likely runs over n! orders, so it cannot be uniform; the tests show 4/27 and 5/27 for n = 3. Overflow in `lcm` in other languages (divide before multiplying). The tests enumerate all draws for shuffles, reservoirs and `pick_index`, run a chi-square check, and verify the sieve (78,498 primes below a million) and the 1,690th ugly number.

*Practice.* 292 Nim Game; 319 Bulb Switcher; 191 Number of 1 Bits; 338 Counting Bits; 372 Super Pow; 204 Count Primes; 172 Factorial Trailing Zeroes; 793 Preimage Size of Factorial Zeroes Function; 645 Set Mismatch; 384 Shuffle an Array; 398 Random Pick Index; 263, 264, 313, 1201 Ugly Numbers.

### 39g: Classic interview problems

*Intuition.* Problems that recur because each has one idea: water over a bar is bounded by the shorter of the tallest walls on each side; the container moves its shorter wall; covered intervals sort by start ascending and end descending; consecutive subsequences extend a run or start one of length three; pancake sorting flips the maximum to the top then into place; string multiplication lands digit i times digit j on positions i + j and i + j + 1; a perfect rectangle has matching area and exactly four odd-count corners.

*The invariant.* `trap_two_pointers`: the side with the lower running maximum is settled, because the other side has a wall at least that high. `is_possible`: `ends[v]` counts runs of length at least 3 ending at v, and a value joins a run before starting one. `is_rectangle_cover`: XOR of corner sets leaves exactly the corners seen an odd number of times.

```python
>>> from frameworks_2 import trap_two_pointers, max_area, remove_covered_intervals, is_possible, pancake_sort, multiply, is_rectangle_cover
>>> trap_two_pointers([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]), max_area([1, 8, 6, 2, 5, 4, 8, 3, 7])
(6, 49)
>>> remove_covered_intervals([[1, 4], [3, 6], [2, 8]]), is_possible([1, 2, 3, 3, 4, 5]), is_possible([1, 2, 3, 4, 4, 5])
(2, True, False)
>>> pancake_sort([3, 2, 4, 1]), multiply("123", "456")
([3, 4, 2, 3, 2], '56088')
>>> is_rectangle_cover([[1, 1, 3, 3], [3, 1, 4, 2], [3, 2, 4, 4], [1, 3, 2, 4], [2, 3, 3, 4]])
True
```

*Complexity.* O(n) for water, container, covered intervals and consecutive subsequences after sorting; O(n²) flips for pancake sort; O(mn) for multiplication; O(n) for the rectangle cover.

*Pitfalls.* Sorting covered intervals by end ascending within equal starts (the longer one must come first); checking only the area in the rectangle cover (overlaps and gaps can cancel). The tests compare the three water versions, verify covered intervals and subsequence splits by brute force, and build random tilings with and without a defect.

*Practice.* 42 Trapping Rain Water; 11 Container With Most Water; 1288 Remove Covered Intervals; 659 Split Array into Consecutive Subsequences; 969 Pancake Sorting; 43 Multiply Strings; 391 Perfect Rectangle.

## How the tests work

Each test file defines one `t_<group>` function per family and a `check` runner that prints `ok  <name>`; the `__main__` block collects every `t_*` function by name, so a new group needs no registration. `test_ds_basics.py` reseeds its generator per group (`rng.seed(f"39e-{name}")`) and prints a measurement; `test_frameworks_2.py` prints the elapsed time and a note. A failing assertion stops the run with a traceback naming the function.

Three kinds of check recur:

- **Built-ins and brute force as oracles.** `test_ds_basics.py` drives each structure with thousands of random operations and compares with `list`, `dict`, `set`, `deque`, `OrderedDict`, `heapq`, `bisect` and `sorted`, using small key pools so collisions and deletions of absent keys are common. The other two files keep inputs small (lengths up to about 12) and use the most obvious correct program as the reference: `itertools` for subsets and permutations, every subarray or substring for windows, all paths from the root for LCA, Kahn's algorithm for topological order, exhaustive search for partitions and games, `eval` for the calculator.
- **Invariants and costs, not only outputs.** Chained buckets never exceed length 2 for sequential keys; the linear-probing cluster invariant holds after every deletion; AVL heights stay within the Fibonacci bound; heapify uses at most n minus popcount(n) swaps; copies per append stay under 2; the Bloom filter's measured rate matches the formula; Shell sort's comparisons grow as about n^1.22; stability is confirmed for the six stable sorts and refuted for the other four with a found example.
- **Exact randomness and reported numbers.** For shuffles, reservoir sampling and `pick_index`, a scripted random source replays every possible sequence of draws, so the distribution is checked exactly, not statistically. The search comparisons the chapters quote are asserted: 8-queens explores 2,057 nodes with pruning versus 109,601 in the full permutation tree; the lock instances expand 248,752 states with plain BFS and 50,096 bidirectionally; the consistent-hash ring moves the stated fraction of 20,000 keys.

To add a function: put it in the file for its chapter with the LeetCode number in the docstring; add a fixed example and a randomized comparison to the matching `t_` group, or a new `t_` function; give any random draw an `rng` parameter; run the test file and `check_chapter_sync.py`. If the chapter prints the function, paste it from the file.

## Map from functions to chapter sections

| Section | File | Functions and classes |
|---|---|---|
| 39e.1 | `ds_basics.py` | `max_subarray_cubic`, `max_subarray_quadratic`, `max_subarray_linear` |
| 39e.3 | `ds_basics.py` | `DynamicArray`, `cpython_list_growth`, `measured_list_growth` |
| 39e.4 | `ds_basics.py` | `_DNode`, `DoublyLinkedList` |
| 39e.5 | `ds_basics.py` | `RingBuffer`, `_SkipNode`, `SkipList`, `Bitset` |
| 39e.6 | `ds_basics.py` | `_Node`, `LinkedStack`, `LinkedQueue` |
| 39e.7 | `ds_basics.py` | `_slot`, `ChainedHashMap`, `LinearProbingHashMap`, `HashSet`, `dict_probe_order`, `CompactDict` |
| 39e.8 | `ds_basics.py` | `LinkedHashMap`, `LRUCache`, `ArrayHashMap`, `bloom_parameters`, `BloomFilter` |
| 39e.9 | `ds_basics.py` | `TreeNode`, `build_tree`, `three_orders`, `depths_and_sizes`, `level_order`, `level_order_by_depth`, `root_to_leaf_sums`, `is_leaf`, `shallowest_bfs`, `shallowest_dfs`, `NaryNode`, `nary_orders`, `nary_levels` |
| 39e.10 | `ds_basics.py` | `_AVLNode`, `rotate_right`, `rotate_left`, `rebalance`, `AVLTree`, `_TrieNode`, `Trie`, `sift_up`, `sift_down`, `heapify`, `MinHeap`, `SegmentTree`, `_Merged`, `huffman_codes`, `huffman_encode`, `huffman_decode` |
| 39e.11 | `ds_basics.py` | `adjacency_list`, `adjacency_matrix`, `dfs_order`, `bfs_distances`, `all_paths`, `DisjointSet`, `euler_kind` |
| 39e.12 | `ds_basics.py` | `selection_sort`, `bubble_sort`, `insertion_sort`, `shell_sort`, `quick_sort`, `merge_sort`, `count_inversions`, `heap_sort`, `counting_sort`, `bucket_sort`, `radix_sort` |
| 39f.1 | `frameworks_1.py` | `good_nodes_traverse`, `good_nodes_decompose`, `leaves_traverse`, `leaves_decompose`, `node_report`, `climb_stairs_traverse`, `climb_stairs_decompose` |
| 39f.2 | `frameworks_1.py` | `merge_two_lists`, `partition_list`, `merge_k_lists_divide`, `kth_from_end`, `remove_nth_from_end`, `get_intersection_node`, `delete_duplicates`, `delete_duplicates_all`, `reverse_list_recursive`, `reverse_first_n`, `reverse_between_recursive`, `reverse_k_group_recursive`, `is_palindrome_list_recursive` |
| 39f.3 | `frameworks_1.py` | `remove_element`, `move_zeroes`, `remove_duplicates_keep_k`, `reverse_in_place`, `rotate_array`, `longest_palindrome`, `rotate_image`, `rotate_image_counterclockwise`, `spiral_order`, `generate_spiral_matrix`, `n_sum`, `four_sum` |
| 39f.4 | `frameworks_1.py` | `NumArray`, `NumMatrix`, `add_to_ranges`, `get_modified_array`, `corp_flight_bookings`, `car_pooling` |
| 39f.5 | `frameworks_1.py` | `check_inclusion`, `longest_ones`, `num_subarray_product_less_than_k`, `min_operations_to_zero`, `longest_substring_k_repeats`, `subarrays_with_k_distinct`, `find_repeated_dna_sequences`, `str_str_rabin_karp` |
| 39f.6 | `frameworks_1.py` | `binary_search`, `left_bound`, `right_bound`, `first_true`, `ship_within_days`, `split_array`, `WeightedPicker`, `advantage_count` |
| 39f.7 | `frameworks_1.py` | `MyQueue`, `MyStack`, `nearest_index`, `sum_subarray_mins`, `MaxMinQueue`, `max_sliding_window_queue`, `longest_subarray_within_limit`, `remove_duplicate_letters` |
| 39f.8 | `frameworks_1.py` | `invert_tree_traverse`, `connect_perfect`, `flatten`, `construct_maximum_binary_tree`, `construct_maximum_binary_tree_stack`, `build_tree_pre_in`, `build_tree_in_post`, `build_tree_pre_post`, `find_duplicate_subtrees`, `serialize_preorder`, `deserialize_preorder`, `serialize_level`, `deserialize_level`, `traverse_with_stack` |
| 39f.9 | `frameworks_1.py` | `BSTIterator`, `kth_smallest`, `convert_bst`, `is_valid_bst`, `search_bst`, `insert_into_bst`, `delete_node`, `num_trees`, `generate_trees`, `max_sum_bst` |
| 39f.10 | `frameworks_1.py` | `lca_bst`, `lca_maybe_missing`, `lca_with_parent`, `lca_of_nodes`, `lca_deepest_leaves` |
| 39f.11 | `frameworks_1.py` | `count_nodes`, `NestedInteger`, `NestedIterator`, `merge_sorted`, `count_smaller`, `reverse_pairs`, `count_range_sum`, `find_kth_largest` |
| 39f.12 | `frameworks_1.py` | `_Link`, `LRUCacheLinked`, `LFUCache`, `RandomizedSet`, `RandomizedCollection`, `BlacklistPicker`, `ExamRoom`, `calculate`, `ConsistentHashRing`, `SegmentTree`, `_SegNode`, `RangeAddTree`, `MyCalendarThree`, `replace_words`, `WordDictionary`, `MapSum` |
| 39f.13 | `frameworks_1.py` | `is_bipartite`, `possible_bipartition`, `find_directed_cycle`, `topo_sort_dfs`, `DisjointSet`, `solve_surrounded_regions`, `equations_possible`, `max_probability`, `minimum_effort_path`, `find_cheapest_price`, `astar_grid`, `kruskal_mst`, `prim_mst`, `min_cost_connect_points`, `find_itinerary`, `valid_arrangement`, `floyd_warshall`, `find_the_city` |
| 39g.1 | `frameworks_2.py` | `all_paths_source_target`, `permutation_tree_size` |
| 39g.2 | `frameworks_2.py` | `permute`, `solve_n_queens`, `total_n_queens_bitmask`, `SUDOKU_UNITS`, `solve_sudoku_propagate` |
| 39g.3 | `frameworks_2.py` | `subsets_backtrack`, `combine`, `combination_sum3`, `subsets_with_dup_backtrack`, `combination_sum2`, `permute_unique`, `permute_unique_counter`, `combine_with_reuse`, `permute_with_reuse` |
| 39g.4 | `frameworks_2.py` | `permute_by_placing`, `can_partition_k_balls`, `can_partition_k_buckets`, `can_partition_k_dp`, `count_balanced` |
| 39g.5 | `frameworks_2.py` | `sink_island`, `num_enclaves`, `count_sub_islands`, `num_distinct_islands` |
| 39g.6 | `frameworks_2.py` | `bfs_shortest`, `bidirectional_bfs`, `open_lock`, `SLIDE_NEIGHBORS`, `sliding_puzzle`, `is_solvable_2x3`, `min_mutation`, `oranges_rotting`, `update_matrix`, `minimum_obstacles` |
| 39g.7 | `frameworks_2.py` | `fib_naive`, `fib_memo`, `fib_table`, `fib`, `coin_change_brute`, `coin_change_memo`, `coin_change_table`, `length_of_lis_quadratic`, `longest_increasing_subsequence`, `max_envelopes`, `min_falling_path_sum`, `min_falling_path_sum_memo`, `num_distinct_by_target`, `num_distinct`, `word_break`, `word_break_all` |
| 39g.8 | `frameworks_2.py` | `edit_script`, `max_subarray`, `max_subarray_prefix`, `max_subarray_divide`, `longest_common_subsequence`, `min_delete_steps`, `minimum_delete_sum`, `longest_palindrome_subseq`, `min_insertions` |
| 39g.9 | `frameworks_2.py` | `knapsack_items`, `can_partition_bitset`, `change`, `combination_sum4`, `find_target_sum_ways_memo`, `bounded_knapsack` |
| 39g.10 | `frameworks_2.py` | `min_path_sum`, `calculate_minimum_hp`, `find_rotate_steps`, `find_cheapest_price`, `is_match`, `super_egg_drop`, `max_coins`, `predict_the_winner`, `stone_game` |
| 39g.11 | `frameworks_2.py` | `_rob_range`, `rob_circular`, `TreeNode`, `rob_tree`, `max_profit` |
| 39g.12 | `frameworks_2.py` | `find_min_arrow_shots`, `min_meeting_rooms_sweep`, `can_jump`, `jump`, `can_complete_circuit`, `can_complete_circuit_prefix`, `video_stitching`, `greedy_coin_count` |
| 39g.13 | `frameworks_2.py` | `can_win_nim`, `bulb_switch`, `is_power_of_two`, `hamming_weight`, `count_bits`, `mod_pow`, `super_pow`, `gcd`, `lcm`, `count_primes`, `trailing_zeroes`, `preimage_size_fzf`, `find_error_nums`, `fisher_yates`, `naive_shuffle`, `reservoir_sample`, `pick_index`, `monty_hall_exact`, `monty_hall_simulate`, `birthday_collision`, `two_children_puzzles`, `is_ugly`, `nth_ugly_number`, `nth_super_ugly_number`, `nth_ugly_number_iii` |
| 39g.14 | `frameworks_2.py` | `trap_brute`, `trap_prefix`, `trap_two_pointers`, `max_area`, `remove_covered_intervals`, `is_possible`, `pancake_sort`, `multiply`, `is_rectangle_cover` |
| shared | `frameworks_1.py` | `ListNode`, `TreeNode`, `build_list`, `list_values`, `build_tree` (helpers; the chapter does not print them) |

Some functions exist in the files but are not printed in the chapters, because the prose describes them or they are helpers: in `ds_basics.py` the class bodies of `AVLTree`, `Trie`, `SkipList`, `Bitset`, `CompactDict`, `HashSet`, `LinkedStack`, `LinkedQueue` and the n-ary helpers; in `frameworks_1.py` the level-order serializer, `four_sum`, `insert_into_bst`, `search_bst`, `merge_sorted`, `possible_bipartition`, `min_cost_connect_points` and `MyCalendarThree`; in `frameworks_2.py` `coin_change_brute`, `count_bits`, `is_ugly`, `monty_hall_simulate`, `permute_by_placing`, `permute_unique_counter` and `solve_n_queens`. All are tested.
