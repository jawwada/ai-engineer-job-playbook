# 39e. Data structures from the inside: arrays, linked lists, hash tables, trees, heaps, graphs and the ten sorting algorithms

> **What you need to be able to say:** how each structure sits in memory and why that layout produces its costs; the invariant every operation preserves; whether a bound is worst-case, amortized or expected, and the argument behind it; how Python's list, dict, set, deque, heapq and sort work underneath; which structure a problem needs, judged from the operations it must support; and the ten classic sorts with their trade-offs in stability, extra space, adaptivity and the n log n barrier.

## 39e.1 Why build data structures yourself

Coding rounds rarely say "implement a hash table", but their follow-ups test exactly that: why `append` is O(1) when the list sometimes copies everything, what a dict does when two keys collide, how to make `get` and `put` O(1) while evicting the least recently used key, why building a heap is linear when n pushes are not.

This chapter and the next two follow the topic map of labuladong's algorithm notes (https://labuladong.online/en/algo/home/) and extend it with tested code, proofs or proof sketches of the costs, the CPython internals behind the Python equivalents, and the interview angle. 39e covers the notes' "Getting Started: Data Structures and Sorting" part and the complexity material; 39f covers the classic templates and the algorithms built on these structures, including the graph algorithms only sketched here; 39g covers backtracking, BFS, dynamic programming, greedy algorithms and math. Chapter 39d, the pattern catalog for the coding round, uses these structures as black boxes; this chapter opens them, and where 39d already has a template (union-find, Dijkstra, a dictionary trie, an `OrderedDict` LRU cache), it builds the layer underneath instead.

**Two storage primitives.** A contiguous array puts element i at address `base + i × size`: any element is one multiplication away and scans are cache-friendly, but the size is fixed at allocation, so growing means copying and inserting in the middle means shifting. Linked nodes keep each value in its own allocation with pointers to its neighbors: splicing a node in or out is O(1) once you hold a neighbor, but reaching element i means following i pointers, each a possible cache miss. Each structure later in the chapter is assembled from one or both layouts, and most add a rule that every operation must preserve: a hash table is an array of buckets whose index comes from the key's hash, a min-heap is an array read as a complete tree in which no parent is larger than its children, and a graph is an array of neighbor lists.

**Faster usually means less repeated work.** A correct algorithm must account for every candidate answer, either by examining it or by an argument that it cannot win; slow and fast versions mostly differ in how much work they repeat along the way (39f.1.1 turns this into a method). The largest-sum subarray (LC 53) has three versions that cover the same candidates at three costs:

```python
def max_subarray_cubic(nums):
    """Largest sum of a non-empty contiguous run (LC 53): try every (i, j), add up nums[i..j]. O(n³)."""
    best = nums[0]
    for i in range(len(nums)):
        for j in range(i, len(nums)):
            total = 0
            for k in range(i, j + 1):
                total += nums[k]
            best = max(best, total)
    return best


def max_subarray_quadratic(nums):
    """Same candidates; the sum of nums[i..j] reuses the sum of nums[i..j-1] instead of starting over. O(n²)."""
    best = nums[0]
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            best = max(best, total)
    return best


def max_subarray_linear(nums):
    """Same candidates grouped by end j: the best run ending at j extends the one ending at j - 1, or restarts."""
    best = ending_here = nums[0]
    for j in range(1, len(nums)):
        ending_here = max(ending_here + nums[j], nums[j])
        best = max(best, ending_here)
    return best
```

All three cover the same n(n + 1)/2 subarrays. The quadratic version gets the sum of `nums[i..j]` from the sum of `nums[i..j-1]` instead of starting over. The linear version groups the candidates by their last index j: a run ending at j is either `nums[j]` alone or a run ending at j − 1 extended by `nums[j]`, and among the latter only the best can win, so one number per end index suffices. That is Kadane's algorithm (39g.8.2 adds a prefix-sum and a divide-and-conquer solution), and its argument, keeping only the candidates that can still win, is the core of dynamic programming (39g.7).

**How to use this chapter.** Write each structure from its description before reading the code. Everything printed is copied verbatim from `labs/algorithm-frameworks/ds_basics.py` (`check_chapter_sync.py` enforces it), which also holds the structures described here without code. `python3 -B test_ds_basics.py` runs 25 groups of tests in several seconds, comparing hundreds of random operation sequences with `list`, `dict`, `set`, `deque`, `heapq`, `sorted` or brute force and checking internal invariants; swap in your own class and rerun. The module needs only these imports:

```python
import hashlib
import heapq
import math
import operator
import random
import struct
import sys
from collections import deque
```

## 39e.2 Complexity you actually use

### 39e.2.1 O, Θ, Ω and four kinds of cost

f(n) = O(g(n)) means that there are constants c > 0 and n₀ with f(n) ≤ c·g(n) for all n ≥ n₀. Ω is the matching lower bound, and Θ means both. Interviews use O loosely for the tight bound; be precise when it matters ("random-pivot quick sort takes Θ(n log n) expected time on every input" beats "quick sort is O(n²)"). Four different claims hide behind "the cost of an operation":

| Kind | Averaged over | Example |
|---|---|---|
| Worst case | Nothing: the maximum over all inputs | Balanced-tree lookup O(log n); heap push O(log n) |
| Average case | A probability distribution over inputs | Quick sort with the first item as pivot: O(n log n) on random input, O(n²) on sorted input |
| Expected | The algorithm's own random choices; holds for every input | Randomized quick sort O(n log n); skip-list search O(log n) |
| Amortized | A sequence of operations; no probability; holds for every sequence | Dynamic-array append O(1); union-find; a queue built from two stacks |

### 39e.2.2 Amortized analysis: why appending is O(1)

Start a doubling array at capacity 1 and append n items. Resizes happen at sizes 1, 2, 4, …, 2^k < n and copy 1 + 2 + … + 2^k = 2^(k+1) − 1 < 2n items in total; with the n writes of the new items, that is fewer than 3n writes, so fewer than 3 per append for every sequence of appends (the aggregate method). The potential method says the same with Φ = 2·size − capacity: an ordinary append costs 1 and raises Φ by 2, and an append that doubles a full array of capacity c costs c + 1 and lowers Φ from c to 2, so cost plus change in Φ is always 3. A single append can still take O(n).

- **Growing by a constant k instead of a factor** costs k + 2k + 3k + … ≈ n²/(2k) copies: Θ(n) per append. Any factor r > 1 keeps the copies below n·r/(r − 1): 2n for doubling, 9n for CPython's factor of about 9/8, which in exchange leaves only about a ninth of the allocation unused, against up to half for doubling.
- **Shrinking at half full would thrash**: a full array doubles on one append and halves on the next pop, copying everything each time. Halving at a quarter full leaves the array half full after every resize, so a quarter of the capacity in operations must pass before the next one. The lab's `DynamicArray` counts its copies: at most 2 per operation over 300 random sequences (the worst is 1.36), and exactly one resize during 10,000 alternating appends and pops at a full boundary.

The same counting makes the monotonic stack of 39d.21 O(n) overall: each element is pushed and popped at most once.

### 39e.2.3 Recursion trees and the master theorem

A recursion that splits size n into a parts of size n/b and spends f(n) outside the calls costs T(n) = a·T(n/b) + f(n). Its recursion tree has log_b n levels, level i holds a^i calls of f(n/b^i) work, and there are n^(log_b a) leaves. The master theorem compares f(n) with n^(log_b a): if f is polynomially smaller, the leaves dominate and T(n) = Θ(n^(log_b a)); if they match, every level costs the same and T(n) = Θ(n^(log_b a) · log n); if f is polynomially larger (and a·f(n/b) ≤ c·f(n) for some c < 1), the root dominates and T(n) = Θ(f(n)).

| Recurrence | Solution | Where it appears |
|---|---|---|
| T(n) = T(n/2) + O(1) | O(log n) | Binary search |
| T(n) = 2T(n/2) + O(1) | O(n) | Traversing a balanced tree; building a segment tree |
| T(n) = 2T(n/2) + O(n) | O(n log n) | Merge sort; quick sort with even splits |
| T(n) = T(n/2) + O(n) | O(n) | Quickselect with good pivots |
| T(n) = T(n/10) + T(9n/10) + O(n) | O(n log n) | Uneven but proportional splits: at most n per level, over log_(10/9) n levels |
| T(n) = T(n − 1) + O(n) | O(n²) | Quick sort's worst case; selection sort |
| T(n) = T(n − 1) + T(n − 2) + O(1) | Θ(φⁿ) ≈ O(1.618ⁿ) | Naive Fibonacci; memoization makes it O(n) (39g.7.2) |
| T(n) = 2T(n − 1) + O(1) | O(2ⁿ) | Enumerating subsets; the Tower of Hanoi |

For recursion over a structure or a state space, multiply calls by work per call: a tree traversal is n calls of O(1) work; a memoized dynamic program costs states × transitions.

### 39e.2.4 Logarithms, constraints, space and constants

A logarithm counts halvings: log₂ of 10³, 10⁶, 10⁹ and 10¹⁸ is about 10, 20, 30 and 60, and the base is only a constant factor inside O; log₂(n!) ≈ n log₂ n − 1.44n gives the sorting lower bound (39e.12). For constraints, 39d.2 maps input sizes to target complexities: CPython manages roughly 10⁶ to 10⁷ simple operations per second, so at n = 10⁵ an O(n²) algorithm needs about 10¹⁰ steps (a quarter of an hour at the faster rate, nearly three hours at the slower) and an O(n log n) one about 1.7 × 10⁶ (under two seconds even at the slower rate). Space includes the recursion stack: a recursive DFS of a path-shaped tree holds n frames, past Python's default limit of 1,000. And constants decide between equal complexities: a three-slot Python node takes 56 bytes on 64-bit CPython 3.11 against 8 for a list slot, and chasing its pointers misses the cache, so the O(n) array scan wins easily.

**Interview line:** *"Append is amortized O(1): doubling makes the copies a geometric series below 2n, so n appends cost under 3n writes; and the array shrinks at a quarter full, not a half, so alternating push and pop at the boundary cannot thrash."*

## 39e.3 Arrays and dynamic arrays

A static array is one block of memory with a fixed length: indexing is address arithmetic, O(1), and a scan is the fastest loop a machine runs. A Python list is a dynamic array of 8-byte pointers to objects that live elsewhere. A dynamic array tracks a size and a capacity, and an implementation is judged on five details: two different index checks (an existing element needs 0 ≤ i < size, while an insertion position may equal size); shifts in the right direction (insertion moves the tail from the back, deletion from the hole forward, or values get overwritten); clearing the vacated slot, or a dead object stays reachable, a leak in any garbage-collected language; doubling when full; and halving at a quarter full. Here a fixed-length Python list stands in for the raw block:

```python
class DynamicArray:
    """A growable array on a fixed-size block: doubles when full, halves when only a quarter full."""

    def __init__(self, capacity=1):
        self._data = [None] * max(1, capacity)    # stands in for one fixed-size block of memory
        self._size = 0
        self.moves = 0                            # elements copied by resizes (the cost analyzed in 39e.2)

    def __len__(self):
        return self._size

    def __iter__(self):
        for i in range(self._size):
            yield self._data[i]

    def capacity(self):
        return len(self._data)

    def _check(self, i, upper):
        if not 0 <= i < upper:
            raise IndexError(f"index {i} out of range")

    def _resize(self, capacity):
        block = [None] * capacity
        for i in range(self._size):
            block[i] = self._data[i]
        self.moves += self._size
        self._data = block

    def get(self, i):
        self._check(i, self._size)
        return self._data[i]

    def set(self, i, value):
        self._check(i, self._size)
        self._data[i] = value

    def append(self, value):
        self.insert(self._size, value)

    def insert(self, i, value):
        """Put value at index i (0 <= i <= len), shifting the tail right: O(len - i), plus amortized O(1)."""
        self._check(i, self._size + 1)            # i == len is allowed: that is an append
        if self._size == len(self._data):
            self._resize(2 * len(self._data))
        for j in range(self._size, i, -1):        # move the last element first, or values get overwritten
            self._data[j] = self._data[j - 1]
        self._data[i] = value
        self._size += 1

    def delete(self, i):
        """Remove and return the item at index i, shifting the tail left; shrink at one quarter full."""
        self._check(i, self._size)
        value = self._data[i]
        for j in range(i, self._size - 1):
            self._data[j] = self._data[j + 1]
        self._size -= 1
        self._data[self._size] = None             # drop the stale reference so the object can be freed
        if len(self._data) > 1 and self._size <= len(self._data) // 4:
            self._resize(len(self._data) // 2)
        return value

    def pop(self):
        return self.delete(self._size - 1)
```

| Operation | Cost |
|---|---|
| `get(i)`, `set(i, x)` | O(1) |
| `append(x)`, `pop()` | O(1) amortized; O(n) for the call that resizes |
| `insert(i, x)`, `delete(i)` | O(n − i) for the shift, plus amortized resizing |
| Search by value | O(n); O(log n) with binary search if sorted |

**How CPython's list grows.** CPython does not double. Since Python 3.9, `list_resize` in `Objects/listobject.c` allocates the new size plus an eighth plus 6, rounded down to a multiple of 4, so appends pass through capacities 0, 4, 8, 16, 24, 32, 40, 52, 64, 76 and so on. It leaves the block alone while the size stays between half the allocation and all of it; once the size drops below half, it shrinks the block to about 9/8 of the size, so a growth and the next shrink are always many operations apart, its version of the quarter rule. The lab's `cpython_list_growth` computes the capacities from that rule and `measured_list_growth` reads them from `sys.getsizeof`; the tests check that the two agree over 3,000 appends (37 resizes). The factor of about 9/8 keeps `append` amortized O(1), and `realloc` can sometimes extend a block in place, so real copies can be fewer than the bound counts.

**Pitfalls.** `list.pop(0)` and `list.insert(0, x)` are O(n), so a BFS built on them is quadratic (use `collections.deque`). Slicing copies. `a + b` builds a new list while `a += b` extends `a` in place. `[[0] * m] * n` makes n references to one row; write `[[0] * m for _ in range(n)]`.

## 39e.4 Linked lists

A singly linked node holds a value and a `next` pointer; a doubly linked node adds `prev`. Splicing next to a node you hold is O(1), reaching index i takes i steps, and deleting a given node from a singly linked list needs its predecessor. Sentinels remove the special cases: with a permanent dummy head and dummy tail, every real node has real neighbors, so an insertion is the same four pointer assignments everywhere and a removal the same two (on LeetCode's `ListNode`, `dummy = ListNode(0, head)` does the same job; 39d.9).

```python
class _DNode:
    __slots__ = ("value", "prev", "next")

    def __init__(self, value=None):
        self.value = value
        self.prev = self.next = None


class DoublyLinkedList:
    """Nodes between two sentinels, so every real node has a real neighbor on each side."""

    def __init__(self, values=()):
        self._head, self._tail = _DNode(), _DNode()       # sentinels: they never hold data
        self._head.next, self._tail.prev = self._tail, self._head
        self._size = 0
        for value in values:
            self.append(value)

    def __len__(self):
        return self._size

    def __iter__(self):
        node = self._head.next
        while node is not self._tail:
            yield node.value
            node = node.next

    def __reversed__(self):
        node = self._tail.prev
        while node is not self._head:
            yield node.value
            node = node.prev

    def _link_before(self, successor, node):
        node.prev, node.next = successor.prev, successor
        successor.prev.next = node
        successor.prev = node
        self._size += 1
        return node

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev
        node.prev = node.next = None                      # a stale handle now fails loudly
        self._size -= 1
        return node.value

    def _node_at(self, i):
        """Walk from the nearer end: at most len / 2 steps."""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range")
        if i < self._size // 2:
            node = self._head.next
            for _ in range(i):
                node = node.next
        else:
            node = self._tail.prev
            for _ in range(self._size - 1 - i):
                node = node.prev
        return node

    def append(self, value):
        """O(1). Returns the node: a handle that makes a later removal O(1)."""
        return self._link_before(self._tail, _DNode(value))

    def appendleft(self, value):
        return self._link_before(self._head.next, _DNode(value))

    def insert(self, i, value):
        """Put value at index i (0 <= i <= len): O(min(i, len - i)) to find the spot, O(1) to link it."""
        successor = self._tail if i == self._size else self._node_at(i)
        return self._link_before(successor, _DNode(value))

    def pop(self):
        if not self._size:
            raise IndexError("pop from an empty list")
        return self._unlink(self._tail.prev)

    def popleft(self):
        if not self._size:
            raise IndexError("pop from an empty list")
        return self._unlink(self._head.next)

    def delete(self, i):
        return self._unlink(self._node_at(i))

    def remove_node(self, node):
        return self._unlink(node)

    def move_to_end(self, node):
        self._unlink(node)
        self._link_before(self._tail, node)

    def get(self, i):
        return self._node_at(i).value

    def set(self, i, value):
        self._node_at(i).value = value
```

`_node_at` walks from the nearer end, so indexing takes at most n/2 steps. `append`, `appendleft` and `insert` return the node as a handle, so a caller can later remove or move it in O(1) without searching; that handle is what makes the LRU cache of 39e.8.1 O(1).

| | Dynamic array | Doubly linked list with handles |
|---|---|---|
| Access by index | O(1) | O(min(i, n − i)) |
| Insert or delete at the ends | O(1) amortized at the back; O(n) at the front | O(1) |
| Insert or delete in the middle | O(n) shifts | O(1) given the node; O(n) to find it |
| Memory per item (64-bit CPython); scanning | An 8-byte pointer plus up to an eighth spare; contiguous and cache-friendly | A 56-byte node plus the pointer to it; pointer chasing |
| Splitting, joining, stable positions | O(n) copies; indices shift | O(1) at known nodes; nodes stay valid |

Linked lists win when items are removed or reordered through handles (LRU and LFU caches, run queues, allocators' free lists), when sublists are spliced, when no operation may pay for a reallocation spike, and when immutable lists share tails, as in functional languages. They lose wherever indexing or fast scans matter, which is most of the time; Python's `deque` (39e.6) is a linked list of 64-slot blocks, keeping O(1) ends with much of an array's locality. The usual bugs: overwriting `next` before saving it, updating `next` but not `prev`, off-by-one walks, and relinking into a cycle.

## 39e.5 Variations: ring buffers, skip lists and bitsets

### 39e.5.1 Ring buffer (circular array)

A ring buffer reads an array as a circle: item i lives at physical index (start + i) mod capacity, so pushing or popping at either end moves `start` or the size, never the data. With only `start` and `end` pointers, start = end would mean both empty and full; keep a size, as here, or leave one slot unused. A full buffer can refuse (a fixed-capacity deque, as LC 622 and 641 ask), overwrite the other end (what `deque(maxlen=k)` does; the tests compare the two), or double and later shrink at a quarter full.

```python
class RingBuffer:
    """Deque on a circular array: item i lives at (start + i) % capacity.

    when_full: "error" raises (a fixed-capacity deque), "overwrite" drops the item at the other end
    (like deque(maxlen=...)), "grow" doubles the array and halves it again at one quarter full.
    """

    def __init__(self, capacity=8, when_full="error"):
        if capacity < 1 or when_full not in ("error", "overwrite", "grow"):
            raise ValueError("capacity must be positive; when_full is error, overwrite or grow")
        self._data = [None] * capacity
        self._start = 0                   # physical index of item 0
        self._size = 0                    # start alone cannot tell an empty buffer from a full one
        self.when_full = when_full

    def __len__(self):
        return self._size

    def __iter__(self):
        for i in range(self._size):
            yield self._data[(self._start + i) % len(self._data)]

    def get(self, i):
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range")
        return self._data[(self._start + i) % len(self._data)]

    def _resize(self, capacity):
        items = list(self)                # unwrap: item 0 moves to physical index 0
        self._data = items + [None] * (capacity - len(items))
        self._start = 0

    def _make_room(self, drop_other_end):
        if self._size < len(self._data):
            return
        if self.when_full == "error":
            raise OverflowError("ring buffer is full")
        if self.when_full == "overwrite":
            drop_other_end()
        else:
            self._resize(2 * len(self._data))

    def _after_pop(self):
        if self.when_full == "grow" and len(self._data) > 1 and self._size <= len(self._data) // 4:
            self._resize(len(self._data) // 2)

    def push_back(self, value):
        self._make_room(self.pop_front)
        self._data[(self._start + self._size) % len(self._data)] = value
        self._size += 1

    def push_front(self, value):
        self._make_room(self.pop_back)
        self._start = (self._start - 1) % len(self._data)    # Python's % is never negative; C's can be
        self._data[self._start] = value
        self._size += 1

    def pop_front(self):
        if not self._size:
            raise IndexError("pop from an empty ring buffer")
        value, self._data[self._start] = self._data[self._start], None
        self._start = (self._start + 1) % len(self._data)
        self._size -= 1
        self._after_pop()
        return value

    def pop_back(self):
        if not self._size:
            raise IndexError("pop from an empty ring buffer")
        i = (self._start + self._size - 1) % len(self._data)
        value, self._data[i] = self._data[i], None
        self._size -= 1
        self._after_pop()
        return value
```

In C, C++ and Java, `%` of a negative number is negative, so write `(start - 1 + capacity) % capacity`; with a power-of-two capacity, `& (capacity - 1)` replaces the division. Ring buffers carry streaming windows (346†, 933), last-k logs, audio buffers and bounded producer–consumer queues.

### 39e.5.2 Skip list

A sorted linked list cannot jump, so finding a key takes O(n). A skip list adds express lanes: every node is on level 0, and a node on level i also joins level i + 1 with probability p = 1/2, so level i holds about n/2^i nodes. A search starts at the head's top level, moves right while the next key is smaller than the target, and drops a level when the next step would overshoot. An insertion records the last node visited on each level, flips coins for the new node's height and splices it in; a deletion unsplices it. The lab's `SkipList` is tested against a dict and a sorted list.

**Why a search takes expected O(log n) steps.** Trace the path backwards from the bottom: at each node it came from above (the tower continues, probability p) or from the left, so climbing a level takes 1/p expected steps over about log_(1/p) n levels, about 2 log₂ n steps for p = 1/2. A node carries 1/(1 − p) = 2 pointers on average, and the chance that any node is taller than c·log₂ n is at most n^(1 − c), so the height is O(log n) with high probability; with 20,000 keys the tests saw a mean tower of 1.999 levels and a tallest of 16 (log₂ 20,000 ≈ 14.3). Against balanced trees, skip lists need no rotations, scan ranges along level 0 and update only nearby pointers, which makes concurrent versions practical (Java's `ConcurrentSkipListMap`); they pay with randomness, extra pointers and weaker locality. Redis implements sorted sets as "a dual-ported data structure containing both a skip list and a hash table". LC 1206 asks for one.

### 39e.5.3 Bitset

When the values are the integers 0 to n − 1, membership needs one bit per value: value i is bit i & 7 of byte i >> 3. The lab's `Bitset` iterates over members with `x & -x`, which isolates the lowest set bit. On 64-bit CPython 3.11, a million flags take 125,000 bytes as a bitset, 8 MB as a list of booleans and about 61 MB as a `set` of integers (the table plus the integer objects, measured with `sys.getsizeof`). Python integers work as bitsets too (`mask |= 1 << i`, `mask >> i & 1`, `mask.bit_count()`), but an `int` is immutable, so every update builds a new one in time proportional to its length: right for the masks of 20 or so bits that subset searches carry as state (39g.2.3, 39g.4.2), wrong for a million flags that change one at a time. Memory grows with the largest possible value, not the number of members, so sparse sets call for a hash set, a compressed bitmap such as Roaring, or a Bloom filter (39e.8.3). LC 2166 is the design exercise.

## 39e.6 Queues, stacks and deques

A stack needs O(1) work at one end, a queue adds at one end and removes at the other, and a deque works at both. On linked lists, a stack is a singly linked list whose head is the top, a queue is a singly linked list with a sentinel head that dequeues at the front and enqueues through a tail pointer (the lab's `LinkedStack` and `LinkedQueue`), and a deque is the doubly linked list of 39e.4; on arrays, a stack is the end of a dynamic array and a queue or deque is a growing ring buffer (39e.5.1).

| Need | Python | Cost | Notes |
|---|---|---|---|
| Stack | `list` (`append`, `pop`, `a[-1]`) | O(1) amortized | Never `pop(0)` |
| Queue or deque | `collections.deque` | O(1) at both ends | Linked 64-slot blocks (`BLOCKLEN` in `Modules/_collectionsmodule.c`); indexing is O(n) in the middle |
| Bounded window | `deque(maxlen=k)` | O(1) | A full deque discards from the opposite end |
| Thread-safe queue | `queue.Queue`, `queue.SimpleQueue` | O(1) plus locking | Producer–consumer (39d.22) |
| Priority queue | `heapq` on a list | O(log n) | 39e.10.5 |

A queue built from two stacks (LC 232) is amortized O(1), because each item moves from the input stack to the output stack at most once; it and the stack built from queues (225) are in 39f.7.1.

## 39e.7 Hash tables

### 39e.7.1 From a key to a slot

A hash function must give equal keys equal hashes, and it should be fast and spread keys evenly; in Python, `__hash__` must agree with `__eq__`, and a class that defines `__eq__` alone gets `__hash__ = None`. Reducing a hash to a slot modulo a prime spreads keys well but costs a division; masking with a power-of-two size is fast but uses only the low bits, so hashes that differ only in high bits (multiples of 2²⁰, say) collide. Tables therefore mix the bits first: Java's `HashMap` XORs the high half into the low half, CPython's dict feeds the high bits into later probes (39e.7.5), and the lab uses Fibonacci hashing, which keeps the top bits of hash × 2⁶⁴/φ (keys 0 to 999 in 2,048 slots never put more than two keys in one slot).

With n keys in m slots, the load factor is α = n/m. If keys spread as if at random, an operation costs O(1 + α) expected, and resizing to keep α bounded (an O(n) rebuild, amortized as in 39e.2) makes it O(1) expected. If all keys share a slot, operations cost O(n), which is what an attacker aims for (39e.7.6).

### 39e.7.2 Separate chaining

Each slot holds a chain: the list of entries whose keys hash there.

```python
def _slot(key, bits):
    """Fibonacci hashing: the top `bits` bits of hash(key) * 2^64/φ (mod 2^64), so every bit of the hash counts."""
    return ((hash(key) * 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF) >> (64 - bits)


class ChainedHashMap:
    """Separate chaining: slot i holds a list of [key, value] pairs whose keys hash to i."""

    def __init__(self, bits=3):
        self._bits = bits                             # 2^bits slots
        self._buckets = [[] for _ in range(1 << bits)]
        self._size = 0

    def __len__(self):
        return self._size

    def __iter__(self):
        for bucket in self._buckets:
            for key, _ in bucket:
                yield key

    def _bucket(self, key):
        return self._buckets[_slot(key, self._bits)]

    def get(self, key, default=None):
        for k, v in self._bucket(key):
            if k == key:
                return v
        return default

    def __contains__(self, key):
        return any(k == key for k, _ in self._bucket(key))

    def put(self, key, value):
        bucket = self._bucket(key)
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value
                return
        bucket.append([key, value])
        self._size += 1
        if self._size > 0.75 * len(self._buckets):            # load factor above 3/4: double
            self._rehash(self._bits + 1)

    def delete(self, key):
        bucket = self._bucket(key)
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = bucket[-1]                        # order inside a chain does not matter
                bucket.pop()
                self._size -= 1
                if self._bits > 3 and self._size < len(self._buckets) / 8:    # below 1/8: halve
                    self._rehash(self._bits - 1)
                return True
        return False

    def _rehash(self, bits):
        old = self._buckets
        self._bits, self._buckets = bits, [[] for _ in range(1 << bits)]
        for bucket in old:
            for pair in bucket:
                self._bucket(pair[0]).append(pair)
```

The table doubles above a load factor of 3/4 and halves below 1/8, so a constant fraction of the capacity in operations separates any two resizes. Java's `HashMap` chains with the same default load factor of 0.75 and, since Java 8, turns a chain into a red-black tree when an insertion finds 8 entries already in it (`TREEIFY_THRESHOLD`; a table with fewer than 64 slots doubles instead), which keeps a crowded slot at O(log n) as long as the colliding keys have distinct hash codes or are `Comparable`.

### 39e.7.3 Open addressing with linear probing

Open addressing stores the entries in the array itself. On a collision, linear probing tries the next slot, wrapping around at the end, and a lookup walks from the key's home slot until it finds the key or an empty slot. Consecutive memory makes it fast, but occupied slots clump into clusters that grow faster the longer they are. Knuth's estimates at load α are about ½(1 + 1/(1 − α)) probes for a successful search and ½(1 + 1/(1 − α)²) for an unsuccessful one: 1.5 and 2.5 at α = 1/2, but 5.5 and 50.5 at α = 0.9, so the lab keeps half the slots empty. Deletion is the hard part: emptying a slot can cut the probe path of a key placed beyond it, which lookups would then miss. The class implements both fixes:

- **Tombstones.** Mark the slot deleted rather than empty. Lookups step over tombstones; an insertion may reuse the first tombstone on its path, but only after confirming that the key is not stored further along. Tombstones count toward the load until a rebuild drops them, so a table with heavy churn slows down until it is rebuilt.
- **Backward shift** (Knuth's Algorithm R). After emptying slot i, walk on through the cluster. An entry at slot j whose home is h may move back into the hole exactly when the hole lies on its probe path from h to j, that is, when (j − h) mod m ≥ (j − i) mod m; move it and make j the new hole, until an empty slot ends the cluster. No tombstones exist: the table ends up exactly as if the deleted key had never been inserted, so later lookups pay nothing for the deletion.

```python
_EMPTY = object()      # a slot unused since the last rehash: a probe that reaches it can stop
_DELETED = object()    # a tombstone: a deleted entry that probes must step over


class LinearProbingHashMap:
    """Open addressing with linear probing. Deletion by backward shift (default) or by tombstones."""

    def __init__(self, bits=3, deletion="shift"):
        if deletion not in ("shift", "tombstone"):
            raise ValueError("deletion is 'shift' or 'tombstone'")
        self.deletion = deletion
        self._bits = bits
        self._keys = [_EMPTY] * (1 << bits)
        self._values = [None] * (1 << bits)
        self._size = 0                    # live keys
        self._used = 0                    # live keys plus tombstones: what makes probes long

    def __len__(self):
        return self._size

    def __iter__(self):
        for key in self._keys:
            if key is not _EMPTY and key is not _DELETED:
                yield key

    def _locate(self, key):
        """(slot, True) if key is stored there; else (slot where it should go, False)."""
        mask = len(self._keys) - 1
        i, reuse = _slot(key, self._bits), -1
        while True:
            k = self._keys[i]
            if k is _EMPTY:
                return (i if reuse < 0 else reuse), False
            if k is _DELETED:
                if reuse < 0:
                    reuse = i                 # first tombstone: insert here if the key is absent
            elif k == key:
                return i, True
            i = (i + 1) & mask            # wrap around at the end of the array

    def get(self, key, default=None):
        i, found = self._locate(key)
        return self._values[i] if found else default

    def __contains__(self, key):
        return self._locate(key)[1]

    def put(self, key, value):
        i, found = self._locate(key)
        if not found:
            if self._keys[i] is _EMPTY:
                self._used += 1
            self._keys[i] = key
            self._size += 1
        self._values[i] = value
        if 2 * self._used > len(self._keys):          # keep at least half the slots empty
            self._rehash()

    def delete(self, key):
        i, found = self._locate(key)
        if not found:
            return False
        self._size -= 1
        if self.deletion == "tombstone":
            self._keys[i], self._values[i] = _DELETED, None
        else:
            self._shift_back(i)
            self._used -= 1
        if self._bits > 3 and 16 * self._size < len(self._keys):     # under 1/16 full: shrink
            self._rehash()
        return True

    def _shift_back(self, hole):
        """Close the hole: move back any later entry of the cluster whose probe path passes the hole."""
        mask = len(self._keys) - 1
        j = hole
        while True:
            j = (j + 1) & mask
            if self._keys[j] is _EMPTY:
                break
            home = _slot(self._keys[j], self._bits)
            if (j - home) & mask >= (j - hole) & mask:        # the hole lies between home and j
                self._keys[hole], self._values[hole] = self._keys[j], self._values[j]
                hole = j
        self._keys[hole], self._values[hole] = _EMPTY, None

    def _rehash(self):
        """Rebuild with 2^bits >= 4 * size slots (at least 8): one quarter full, tombstones gone."""
        pairs = [(k, v) for k, v in zip(self._keys, self._values) if k is not _EMPTY and k is not _DELETED]
        self._bits = max(3, (4 * len(pairs) - 1).bit_length())
        self._keys = [_EMPTY] * (1 << self._bits)
        self._values = [None] * (1 << self._bits)
        self._size = self._used = 0
        for k, v in pairs:
            self.put(k, v)
```

After every operation, the tests check the invariant that makes linear probing correct, using keys of several types and keys that all share one hash: no empty slot lies between a key's home slot and the slot it occupies. Quadratic probing, double hashing, Robin Hood hashing, cuckoo hashing and Swiss tables (Abseil; Rust's `HashMap`) trade along the same axes of cluster length, locality and worst-case lookups.

### 39e.7.4 Hash sets and immutable keys

A set is a map whose values carry no information; the lab's `HashSet` wraps the probing map. CPython's `set` has its own table: it checks the home slot and up to 9 slots after it (`LINEAR_PROBES`) before jumping with the perturbation of 39e.7.5, and resizes once 60% of the slots are in use.

Keys must be immutable because each entry is filed under the hash its key had at insertion. The tests store a list-backed key in a dict and then append to the list: an equal copy of the old value no longer matches the stored key, and an equal copy of the new value has a different hash from the stored one. Only the same object can still match, since CPython checks identity first, and only if its new hash happens to probe the old slot; it missed in 48 of 50 trials. Hence lists, dicts and sets are unhashable, and your own keys should hash only fields that never change (`@dataclass(frozen=True)` generates a matching `__eq__` and `__hash__`).

### 39e.7.5 How CPython's dict works

Since CPython 3.6, a dict has two arrays: a sparse index table, a power-of-two number of small integers (one byte each in small tables) that mark each slot free, deleted (a dummy) or holding an entry's position; and a dense array of (hash, key, value) entries in insertion order (since 3.11, a dict whose keys are all strings stores only key and value, because each `str` caches its own hash). Lookups probe the index table and iteration walks the entries, which is why a dict iterates in insertion order (guaranteed since 3.7) and quickly. The probe order, from `Objects/dictobject.c`:

```python
def dict_probe_order(h, size):
    """The slots CPython's dict tries for hash h in an index table of `size` slots (a power of two)."""
    mask = size - 1
    perturb = h & 0xFFFFFFFFFFFFFFFF          # the hash as an unsigned 64-bit number
    i = perturb & mask
    while True:
        yield i
        perturb >>= 5                         # PERTURB_SHIFT: the high bits enter the early probes
        i = (5 * i + perturb + 1) & mask      # once perturb is 0, this visits every slot
```

- **Probing.** `perturb` starts as the whole hash and loses 5 bits per step (`PERTURB_SHIFT`), so the high bits steer the early probes; once it reaches 0, the recurrence 5i + 1 mod 2^k visits every slot, so a search always ends at a free one.
- **Comparisons.** A lookup checks identity first, then the stored hash, and calls `__eq__` only when the hashes match. The stored hashes also spare every `__hash__` call during a resize.
- **Deletion.** The index slot becomes a dummy, a tombstone, and the entry becomes a hole. An insertion appends a new entry and, in the default build, takes the first free or dummy index slot on its probe path (the free-threaded build skips dummies).
- **Resizing.** The entries array has room for two thirds of the index size (`USABLE_FRACTION`). When it fills, the dict is rebuilt with the smallest power of two that is at least three times the number of live keys (`GROWTH_RATE`, unchanged since 3.7), which compacts the holes and drops the dummies.

The lab's `CompactDict` implements these rules. It matches `dict` over tens of thousands of random operations, iteration order included, and resizes at the 6th, 11th, 22nd, 43rd, 86th and 171st insertion, exactly where `sys.getsizeof` shows a real dict growing once its first 8-slot table exists (an empty dict allocates that table on its first insertion).

### 39e.7.6 Hash flooding

An attacker who knows the hash function and controls the keys can send keys that all collide, so n insertions cost O(n²); Crosby and Wallach demonstrated this in 2003, and the 2011 advisory oCERT-2011-003 showed it against the request parsers of many web frameworks. The defense is a keyed hash: since Python 3.3, `str` and `bytes` hashes are salted with a random per-process key (`PYTHONHASHSEED` reproduces a run), and since 3.4 the function is SipHash (PEP 456; `siphash13` since 3.11, per `sys.hash_info.algorithm`). Integers are not salted: on 64-bit CPython, `hash(n)` is n reduced modulo 2⁶¹ − 1, so integers that differ by multiples of it collide. In one local measurement on CPython 3.11, inserting 4,000 of them into a dict took about 0.1 seconds, against well under a millisecond for 4,000 ordinary integers, and doubling the count roughly quadrupled the time. With untrusted keys, bound their number, validate them, or use a structure with a worst-case guarantee.

**Interview line:** *"A hash table is O(1) expected, not worst case: with a good hash and the load factor kept below a constant, a lookup inspects O(1) slots on average. Collisions go into chains or into the next free slot, and under linear probing a deletion needs a tombstone or a backward shift, or later keys become unreachable."*

## 39e.8 Hash-table variations

### 39e.8.1 LinkedHashMap: hashing plus an order

Map each key to its node in a doubly linked list: the map finds entries, the list keeps an order, and every operation is O(1) because the map hands the list the node it needs. In insertion order, updating a key keeps its position; in access order, every read or write moves the key to the end, which leaves the least recently used key at the front.

```python
class LinkedHashMap:
    """Hash map that remembers an order: insertion order, or access order (which makes an LRU cache)."""

    def __init__(self, access_order=False):
        self._nodes = {}                     # key -> list node holding (key, value)
        self._order = DoublyLinkedList()
        self.access_order = access_order

    def __len__(self):
        return len(self._nodes)

    def __iter__(self):
        for key, _ in self._order:
            yield key

    def get(self, key, default=None):
        node = self._nodes.get(key)
        if node is None:
            return default
        if self.access_order:
            self._order.move_to_end(node)    # O(1) because the map hands us the node
        return node.value[1]

    def put(self, key, value):
        node = self._nodes.get(key)
        if node is None:
            self._nodes[key] = self._order.append((key, value))
            return
        node.value = (key, value)
        if self.access_order:
            self._order.move_to_end(node)

    def delete(self, key):
        node = self._nodes.pop(key, None)
        if node is None:
            return False
        self._order.remove_node(node)
        return True

    def pop_oldest(self):
        key, value = self._order.popleft()
        del self._nodes[key]
        return key, value


class LRUCache:
    """LC 146 from the inside: a LinkedHashMap in access order that evicts its oldest entry."""

    def __init__(self, capacity):
        self.capacity = capacity
        self._map = LinkedHashMap(access_order=True)

    def get(self, key):
        return self._map.get(key, -1)

    def put(self, key, value):
        self._map.put(key, value)
        if len(self._map) > self.capacity:
            self._map.pop_oldest()
```

That is LC 146 without `OrderedDict`; 39d.23 has the `OrderedDict` version, whose `move_to_end` and `popitem(last=False)` are exactly these operations. LC 460 (LFU) maps each use count to an ordered map of the keys with that count, plus the current minimum count (39f.12.1).

### 39e.8.2 ArrayHashMap: a random key in O(1)

LC 380 asks for insert, delete and a uniformly random element, all in O(1). A hash table cannot sample uniformly in worst-case O(1): under chaining, a random slot and then a random entry favors keys in short chains; under open addressing, sampling until a slot is occupied takes an expected 1/α tries. Keep the keys densely in an array with a map from key to position, and delete by moving the last key into the hole.

```python
class ArrayHashMap:
    """Hash map with O(1) random_key: keys sit densely in a list; a dict maps each key to its position."""

    def __init__(self, seed=None):
        self._keys, self._values = [], []
        self._pos = {}
        self._rng = random.Random(seed)

    def __len__(self):
        return len(self._keys)

    def get(self, key, default=None):
        i = self._pos.get(key)
        return default if i is None else self._values[i]

    def put(self, key, value):
        i = self._pos.get(key)
        if i is None:
            self._pos[key] = len(self._keys)
            self._keys.append(key)
            self._values.append(value)
        else:
            self._values[i] = value

    def delete(self, key):
        i = self._pos.pop(key, None)
        if i is None:
            return False
        last_key, last_value = self._keys.pop(), self._values.pop()
        if i < len(self._keys):              # fill the hole with the old last entry: no gaps, O(1)
            self._keys[i], self._values[i] = last_key, last_value
            self._pos[last_key] = i
        return True

    def random_key(self):
        if not self._keys:
            raise KeyError("random_key from an empty map")
        return self._keys[self._rng.randrange(len(self._keys))]
```

In the tests, 40,000 draws from 20 keys give a chi-square statistic of 12.6 on 19 degrees of freedom, consistent with a uniform draw. LC 381 allows duplicates (a set of positions per value), and 710 uses the same remapping idea.

### 39e.8.3 Bloom filter

A Bloom filter answers "have I seen this item?" in m bits with k hash functions, however large the items are. Adding an item sets the k bits its hashes select; a query answers "possibly present" if all k bits are set and "definitely absent" otherwise. Bits are never cleared, so there are no false negatives.

**The false-positive rate.** After n insertions, a given bit is still 0 with probability (1 − 1/m)^(kn) ≈ e^(−kn/m), so a new item is a false positive with probability p ≈ (1 − e^(−kn/m))^k. For a fixed number of bits per item, this is smallest at k = (m/n)·ln 2, when half the bits are set, which gives p ≈ 2^(−k) ≈ 0.6185^(m/n), and therefore m = −n·ln p/(ln 2)² ≈ 1.44·n·log₂(1/p) bits. The derivation treats the k bits a query checks as independent events, which they are not even with ideal hash functions; Bose et al. showed that the formula is therefore a strict underestimate for every k ≥ 2, though the gap is negligible when m is large and k small.

| Target rate | Bits per item | k | Memory for 10⁶ items |
|---|---|---|---|
| 10% | 4.79 | 3 | 0.60 MB |
| 1% | 9.59 | 7 | 1.20 MB |
| 0.1% | 14.38 | 10 | 1.80 MB |
| 0.01% | 19.17 | 13 | 2.40 MB |

For comparison, on 64-bit CPython 3.11 a `set` of a million short strings such as `"user-123456"` takes about 93 MB, counting the string objects.

```python
def bloom_parameters(n, p):
    """Bits m and hash count k for n items at false-positive rate p: m = -n ln p / (ln 2)², k = (m/n) ln 2."""
    m = math.ceil(-n * math.log(p) / math.log(2) ** 2)
    return m, max(1, round(m / n * math.log(2)))


class BloomFilter:
    """Approximate set in m bits: never a false negative; false positives at about the designed rate p."""

    def __init__(self, n, p):
        self.m, self.k = bloom_parameters(max(1, n), p)
        self.bits = Bitset(self.m)

    def _positions(self, item):
        """k positions h1 + i·h2 from one 128-bit digest (double hashing); repr keeps 1 and "1" apart."""
        digest = hashlib.blake2b(repr(item).encode(), digest_size=16).digest()
        h1, h2 = int.from_bytes(digest[:8], "little"), int.from_bytes(digest[8:], "little") | 1
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, item):
        for position in self._positions(item):
            self.bits.add(position)

    def __contains__(self, item):
        return all(position in self.bits for position in self._positions(item))
```

The k positions come from one 128-bit BLAKE2b digest split into two 64-bit hashes and combined as h₁ + i·h₂; Kirsch and Mitzenmacher showed that this double hashing keeps the asymptotic false-positive rate of k independent functions. Unlike Python's salted `hash()`, the digest is the same in every process, so a filter can be saved and shared. With n = 5,000 and p = 1%, the filter takes 47,926 bits (about 6 KB) and k = 7; in the tests, 40,000 queries for non-members gave a false-positive rate of 1.03% against 1.00% predicted, and no member was ever missed.

**Uses and limits.** Storage engines built on log-structured merge trees keep a filter per on-disk file and skip files that cannot hold a key; RocksDB, once a filter policy is set, writes one into every new SST file, and its documentation pairs 9.9 bits per key with a 1% false-positive rate, close to the 9.6 that the formula above gives. Caches, crawlers and distributed joins use filters the same way. A filter cannot delete (clearing a bit may erase other items), cannot list its members, and degrades past its designed n. Counting Bloom filters replace each bit with a small counter (4 bits in Fan et al.'s proposal) to allow deletion at four times the memory; cuckoo filters allow deletion and use less space than space-optimized Bloom filters at false-positive rates below about 3%.

## 39e.9 Binary trees

### 39e.9.1 Terminology and types

In a binary tree each node has at most two children. Depth counts the edges from the root; height counts the edges on the longest downward path, although some texts count nodes (the lab's AVL tree does), so state your convention. Three facts recur: a binary tree with n nodes has n − 1 edges and n + 1 empty child links; a binary tree of height h has at most 2^(h+1) − 1 nodes, so its height is at least ⌈log₂(n + 1)⌉ − 1; and a full binary tree with L leaves has L − 1 internal nodes.

| Type | Definition | Where it matters |
|---|---|---|
| Full | Every node has 0 or 2 children | Huffman trees |
| Complete | All levels full except possibly the last, which fills from the left | Heaps in arrays |
| Perfect | Full, with all leaves at one depth: 2^(h+1) − 1 nodes | Counting arguments |
| Binary search tree | Left subtree < node < right subtree, at every node | Ordered maps |
| Balanced | Height O(log n); in an AVL tree, sibling heights differ by at most 1 | Guaranteed O(log n) |

Textbooks disagree on these names ("full" sometimes means perfect), so define a term before relying on it. Linked nodes (`TreeNode` with `left` and `right`) are the default representation; a complete tree fits in an array with no pointers, the children of i at 2i + 1 and 2i + 2 and its parent at (i − 1) // 2, which is how heaps are stored. LeetCode writes trees in level order with `null` (`None` in Python) for missing children; the lab's `build_tree` reads that notation.

### 39e.9.2 Recursive traversal: positions, not orders

A recursive walk passes each node three times: on the way in, between the two subtrees, and on the way out. Code placed at those positions produces preorder, inorder and postorder:

```python
def three_orders(root):
    """Preorder, inorder and postorder in one walk: where the code sits decides the order."""
    pre, ino, post = [], [], []

    def walk(node):
        if node is None:
            return
        pre.append(node.val)              # first visit: before either child is explored
        walk(node.left)
        ino.append(node.val)              # second visit: between the two child calls
        walk(node.right)
        post.append(node.val)             # third visit: after both children have returned

    walk(root)
    return pre, ino, post


def depths_and_sizes(root):
    """Depth flows down as a parameter (known on entry); subtree size flows up as a return value (known on exit)."""
    depth, size = {}, {}

    def walk(node, d):
        if node is None:
            return 0
        depth[node] = d                   # preorder: what is above the node
        total = 1 + walk(node.left, d + 1) + walk(node.right, d + 1)
        size[node] = total                # postorder: what is below the node
        return total

    walk(root, 0)
    return depth, size
```

Where a line sits decides what it can use. In `depths_and_sizes`, a node's depth is ready on entry, because the parent hands it down as an argument, while its subtree size exists only on exit, once both children have reported; so anything computed from the children, such as heights, balance checks, the trie pruning of 39e.10.4 and the AVL rebalancing of 39e.10.2, goes at the postorder position. Inorder visits a BST's keys in sorted order. A walk takes O(n) time and O(h) stack, which on a path-shaped tree hits Python's recursion limit near depth 1,000 (the lab's `AVLTree.keys` walks inorder with an explicit stack). 39f.1.2 and 39f.1.3 build on these positions to separate traversing with outside state from decomposing into subproblems whose answers the children return.

### 39e.9.3 Level order: three variants

Breadth-first traversal replaces the call stack with a first-in, first-out queue, so nodes leave the queue in order of depth. The three variants differ in what the loop knows about the node in hand. The first knows only the order. The second also knows where each level starts and stops: the queue's length when a level begins is that level's width, because children appended during the inner loop wait behind it. The third attaches data to every queued node (a depth, a path sum, a cost so far), which is how BFS runs on graphs; when edges carry different costs, the queue must become a priority queue, and the result is Dijkstra's algorithm.

```python
def level_order(root):
    """Variant 1: plain BFS. Values come out in level order, as one flat list with no level boundaries."""
    out, queue = [], deque([root] if root else [])
    while queue:
        node = queue.popleft()
        out.append(node.val)
        for child in (node.left, node.right):
            if child:
                queue.append(child)
    return out


def level_order_by_depth(root):
    """Variant 2: one batch per level; the queue's length when a batch starts is that level's width."""
    levels, queue = [], deque([root] if root else [])
    while queue:
        level = []
        for _ in range(len(queue)):       # read the length once: children appended now belong to the next level
            node = queue.popleft()
            level.append(node.val)
            for child in (node.left, node.right):
                if child:
                    queue.append(child)
        levels.append(level)
    return levels


def root_to_leaf_sums(root):
    """Variant 3: each queue entry pairs a node with data about its path (here the sum), the form graphs use."""
    sums, queue = [], deque([(root, root.val)] if root else [])
    while queue:
        node, total = queue.popleft()
        if node.left is None and node.right is None:
            sums.append(total)
        for child in (node.left, node.right):
            if child:
                queue.append((child, total + child.val))
    return sums
```

### 39e.9.4 DFS or BFS?

Depth-first search holds one root-to-node path, O(h) memory; breadth-first search holds a frontier, O(w), where the width w reaches about n/2 at the bottom of a complete tree. DFS suits exhaustive questions (all paths, every subtree, backtracking); BFS suits "nearest" questions, because it meets nodes in order of depth and can stop at the first that qualifies. Searching for the shallowest node that passes a test shows the difference:

```python
def is_leaf(node):
    return node.left is None and node.right is None


def shallowest_bfs(root, is_target):
    """Depth (root = 1) of the shallowest node passing is_target, or 0 if none: stop at the first hit."""
    queue, depth = deque([root] if root else []), 1
    while queue:
        for _ in range(len(queue)):       # every node of this level before any node of the next
            node = queue.popleft()
            if is_target(node):
                return depth
            for child in (node.left, node.right):
                if child:
                    queue.append(child)
        depth += 1
    return 0


def shallowest_dfs(root, is_target):
    """The same answer by recursion. A hit proves nothing about other branches, so the search goes on."""
    best = math.inf

    def walk(node, depth):
        nonlocal best
        if node is None or depth >= best:         # this branch cannot produce a shallower hit
            return
        if is_target(node):
            best = depth                          # nodes below it are deeper still
            return
        walk(node.left, depth + 1)
        walk(node.right, depth + 1)

    walk(root, 1)
    return 0 if best == math.inf else best
```

BFS returns at its first hit. DFS cannot: a hit deep in the left subtree says nothing about a shallower one on the right, so the best it can do is skip every branch already as deep as the best hit so far; it wins only on memory, on wide trees. Minimum depth (LC 111) is `shallowest_bfs(root, is_leaf)`, which 39d.10 writes out directly. Its usual recursive solution, 1 + min(depth(left), depth(right)), hides a trap: at a node with one child, the empty side returns 0 and wins the min, although a missing child is not a leaf. N-ary trees use the same walks with a loop over the children and no inorder position (the lab's `nary_orders` and `nary_levels`). Graphs add one complication, taken up in 39e.11.2: a walk can reach the same vertex again, along a second edge or around a cycle.

## 39e.10 Tree variations

### 39e.10.1 Binary search trees as ordered maps, and why balance matters

The BST invariant makes search, insertion and deletion follow one root-to-leaf path: O(h). Unlike a hash map, a BST also answers ordered questions in O(h): minimum and maximum, the floor and ceiling of x (the largest key ≤ x, the smallest ≥ x), and, with subtree sizes in the nodes, ranks and the k-th smallest key. Deleting a node with two children copies in its successor (the minimum of its right subtree) and deletes the successor, which has at most one child.

Everything depends on h. Random insertion order gives an expected height of Θ(log n), asymptotically about 4.311·ln n (Devroye), although lower-order terms keep real trees well below that figure at practical sizes (Reed); in one local run of 20 random orders of 4,095 keys, the height ranged from 24 to 32 levels, against 12 for a perfect tree. Sorted insertion builds a path of 4,095 levels, a linear scan per operation. Balanced trees guarantee O(log n) by restructuring as they go.

### 39e.10.2 An AVL tree

An AVL tree (Adelson-Velsky and Landis, 1962) stores each node's height and keeps one invariant: at every node, the heights of the two subtrees differ by at most one.

**Why the height is logarithmic.** Let N(h) be the fewest nodes an AVL tree of height h can have, counting height in levels. The sparsest such tree is a root over sparsest subtrees of heights h − 1 and h − 2, so N(h) = 1 + N(h − 1) + N(h − 2) with N(1) = 1 and N(2) = 2: the Fibonacci recurrence shifted, N(h) = F(h + 2) − 1 with F(1) = F(2) = 1. Since F(k) ≥ φ^(k−2) for the golden ratio φ ≈ 1.618, n ≥ φ^h − 1, so h ≤ log_φ(n + 1) ≈ 1.44·log₂(n + 1); the tests check this bound.

**Rotations.** A rotation is a constant-time pointer change that moves a subtree's root down one side and lifts a child, without changing the inorder sequence of keys. Insertion and deletion work as in a plain BST, and every node on the way back up (the postorder position) calls `rebalance`, since only heights on that path change. A node whose sides differ by two needs one rotation when its taller child leans the same way (left-left, right-right) or is level, which happens only after a deletion, and two when it leans the other way (left-right, right-left: first rotate the child to straighten the kink).

```python
class _AVLNode:
    __slots__ = ("key", "value", "left", "right", "height")

    def __init__(self, key, value):
        self.key, self.value = key, value
        self.left = self.right = None
        self.height = 1


def _height(node):
    return node.height if node else 0


def _update(node):
    node.height = 1 + max(_height(node.left), _height(node.right))


def rotate_right(y):
    """y's left child x becomes the subtree root and x's right subtree moves under y; inorder is unchanged."""
    x = y.left
    y.left, x.right = x.right, y
    _update(y)
    _update(x)
    return x


def rotate_left(x):
    y = x.right
    x.right, y.left = y.left, x
    _update(x)
    _update(y)
    return y


def rebalance(node):
    """Restore the AVL invariant at node after one insertion or deletion below it; returns the subtree root."""
    _update(node)
    balance = _height(node.left) - _height(node.right)
    if balance > 1:                                       # left side two taller
        if _height(node.left.left) < _height(node.left.right):
            node.left = rotate_left(node.left)            # left-right case: straighten the kink first
        return rotate_right(node)
    if balance < -1:
        if _height(node.right.right) < _height(node.right.left):
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node
```

An insertion needs at most one single or double rotation, because the rotated subtree regains its height from before the insertion; a deletion may need one per level, O(log n). The lab's `AVLTree` wraps these functions with `put`, `delete`, `get`, `floor`, `ceiling` and an inorder `keys`; the tests run 150 random sequences against a dict plus `bisect` and check the BST order, every height and every balance factor. Inserting 1 to 4,095 in sorted order, the input that ruins a plain BST, yields a perfectly balanced tree of 12 levels.

### 39e.10.3 Red-black trees

A red-black tree colors each node red or black and keeps five properties: every node is red or black; the root is black; the empty leaves (NIL) are black; a red node has black children; and every path from a node down to a NIL leaf passes the same number of black nodes, its black-height.

**Why the height is at most 2·log₂(n + 1).** By induction, a subtree whose root has black-height b holds at least 2^b − 1 internal nodes: each child has black-height at least b − 1, so at least 2^(b−1) − 1 nodes, and 2·(2^(b−1) − 1) + 1 = 2^b − 1. Since a red node never has a red child, at least half the nodes on any root-to-leaf path are black, so the root's black-height is at least h/2. Then n ≥ 2^(h/2) − 1, so h ≤ 2·log₂(n + 1).

The colors are easiest to remember through 2-3-4 trees (B-trees whose nodes hold one to three keys): draw each multi-key node as a black node with its other keys as red children, and the red-black properties say that every leaf of the 2-3-4 tree is at the same depth. An insertion needs at most two rotations and a deletion at most three, plus recolorings that are O(1) amortized. Java's `TreeMap`, the usual implementations of C++'s `std::map` and the Linux kernel use red-black trees.

| | AVL | Red-black | Skip list | B-tree |
|---|---|---|---|---|
| Height or search path | ≤ 1.44 log₂ n | ≤ 2 log₂ n | About 2 log₂ n expected | About log_b n with b keys per node |
| Restructuring per update | Insert: one single or double rotation; delete: O(log n) | Insert ≤ 2 rotations; delete ≤ 3 | None | Node splits and merges |
| Strongest when | Lookups dominate | Updates dominate | Concurrency, simple code | Disks and caches |

Python has no built-in sorted map: use `bisect` on a sorted list (O(log n) search; O(n) insertion, but the shift is one block move in C), the third-party `sortedcontainers.SortedList` (a list of sorted sublists with an index), or `heapq` when only the minimum matters. In an interview, name the tree-map operation you need (floor, ceiling, rank), then use `bisect` or describe a balanced tree.

### 39e.10.4 Tries

A trie stores strings along shared prefixes: each node stands for a prefix, its children extend it by one character, and a flag marks where a stored word ends, so costs depend on the length L of a word, not on how many words are stored. The lab's `Trie` extends the dictionary version of 39d.23. Insert, search and `starts_with` are O(L); `keys_with_prefix` is O(L) plus the size of the subtree it lists, in sorted order because it visits children sorted; `longest_prefix_of` is the longest-prefix match that IP routers perform on address bits. Deletion unmarks the word, then prunes from the bottom up every node that no longer leads to a word, a postorder decision; the tests check that the trie always holds exactly one node per distinct prefix of its words. Pruning keeps `starts_with` correct, except at the root, which always exists, so the empty prefix must check that the root is a word or has children. Against a hash set, a trie answers prefix queries and stores shared prefixes once, but a dict per node costs far more memory in Python than the strings; radix (Patricia) trees collapse chains of single-child nodes.

### 39e.10.5 Binary heaps and priority queues

A binary min-heap is a complete binary tree stored in an array (the children of i at 2i + 1 and 2i + 2) whose parents are never larger than their children, so the minimum sits at index 0. A push appends a leaf at the next free position, keeping the tree complete, and sifts it up past larger parents: O(log n). A pop moves the last leaf to the root and sifts it down, always swapping with the smaller child: O(log n). Peeking is O(1).

```python
import operator


def sift_up(a, i, before=operator.lt):
    """Move a[i] up while it should come before its parent, at index (i - 1) // 2."""
    while i > 0:
        parent = (i - 1) // 2
        if not before(a[i], a[parent]):
            break
        a[i], a[parent] = a[parent], a[i]
        i = parent


def sift_down(a, i, n, before=operator.lt):
    """Move a[i] down within a[:n] until no child (2i + 1, 2i + 2) should come before it. Returns the swaps."""
    swaps = 0
    while True:
        top, left = i, 2 * i + 1
        if left < n and before(a[left], a[top]):
            top = left
        if left + 1 < n and before(a[left + 1], a[top]):
            top = left + 1
        if top == i:
            return swaps
        a[i], a[top] = a[top], a[i]
        i, swaps = top, swaps + 1


def heapify(a, before=operator.lt):
    """Bottom-up construction in O(n): sift down every internal node, the last one first. Returns the swaps."""
    return sum(sift_down(a, i, len(a), before) for i in range(len(a) // 2 - 1, -1, -1))


class MinHeap:
    """Priority queue, smallest first: push and pop O(log n), peek O(1), building from n items O(n)."""

    def __init__(self, items=()):
        self._a = list(items)
        heapify(self._a)

    def __len__(self):
        return len(self._a)

    def peek(self):
        if not self._a:
            raise IndexError("peek at an empty heap")
        return self._a[0]

    def push(self, item):
        self._a.append(item)              # the next free leaf keeps the tree complete
        sift_up(self._a, len(self._a) - 1)

    def pop(self):
        if not self._a:
            raise IndexError("pop from an empty heap")
        last = self._a.pop()              # detach the last leaf and let it fill the root
        if not self._a:
            return last
        top, self._a[0] = self._a[0], last
        sift_down(self._a, 0, len(self._a))
        return top
```

**Why building a heap is O(n).** Floyd's construction sifts down every internal node, last to first, and a node of height h sifts at most h levels; most nodes are near the bottom. Exactly: numbering nodes from 1, node i has height at least h if and only if i·2^h ≤ n (its leftmost descendant h levels down is node i·2^h), so ⌊n/2^h⌋ nodes have height at least h, and the heights add up to Σ_(h≥1) ⌊n/2^h⌋ = n − s(n), where s(n) is the number of 1 bits in n (Legendre's formula). `heapify` therefore makes fewer than n swaps and, at two comparisons per level, fewer than 2n comparisons; the tests confirm the n − s(n) swap bound on 300 random arrays (at most 0.83 swaps per item) and the 2(n − s(n)) comparison bound on random and reversed inputs. Pushing the items one at a time costs O(n log n) in the worst case, because the new leaves, half of all nodes, may each climb the full height.

`heapq` uses the same layout on a plain list, with one refinement documented in its source: sifting down, it moves the hole to a leaf along the smaller children and then sifts the item back up, because the item placed at the root during a pop is usually large, which cut the comparisons for 1,000 pops from about 15,000 to about 8,700. For a max-heap, push negated keys (39d.24); for ties, push (priority, counter, item); and since there is no decrease-key, push a new entry and skip stale ones, as Dijkstra's algorithm does in 39d.23.

### 39e.10.6 Segment trees

Prefix sums answer a range sum in O(1) but need O(n) to update one value; a plain array is the reverse. A segment tree does both in O(log n). Node k covers an interval [lo, hi] and stores its combined value; children 2k and 2k + 1 cover the two halves, and building is a postorder computation, O(n). A query returns the identity at a node disjoint from the range, the stored value at a node inside it, and asks both children otherwise; at most two nodes per level overlap the range partially, so a query visits at most four nodes per level. An update walks down to its leaf and recomputes the ancestors on the way back.

```python
import operator


class SegmentTree:
    """Point update and range query for an associative combine (sum, min, max, gcd), O(log n) each."""

    def __init__(self, values, combine=operator.add, identity=0):
        self.n = len(values)
        self.combine, self.identity = combine, identity
        self.tree = [identity] * (4 * max(1, self.n))    # node 1 is the root; children of k are 2k, 2k + 1
        if self.n:
            self._build(values, 1, 0, self.n - 1)

    def _build(self, values, node, lo, hi):
        if lo == hi:
            self.tree[node] = values[lo]
            return
        mid = (lo + hi) // 2
        self._build(values, 2 * node, lo, mid)
        self._build(values, 2 * node + 1, mid + 1, hi)
        self.tree[node] = self.combine(self.tree[2 * node], self.tree[2 * node + 1])    # postorder

    def update(self, i, value):
        if not 0 <= i < self.n:
            raise IndexError(f"index {i} out of range")
        node, lo, hi = 1, 0, self.n - 1
        path = []
        while lo != hi:                   # walk down to the leaf for i, remembering the path
            path.append(node)
            mid = (lo + hi) // 2
            if i <= mid:
                node, hi = 2 * node, mid
            else:
                node, lo = 2 * node + 1, mid + 1
        self.tree[node] = value
        for node in reversed(path):       # recompute the ancestors, bottom up
            self.tree[node] = self.combine(self.tree[2 * node], self.tree[2 * node + 1])

    def query(self, left, right):
        """combine(values[left..right]), both ends inclusive."""
        return self._query(1, 0, self.n - 1, left, right)

    def _query(self, node, lo, hi, left, right):
        if right < lo or hi < left:
            return self.identity          # disjoint from the query
        if left <= lo and hi <= right:
            return self.tree[node]        # inside the query: use the stored answer
        mid = (lo + hi) // 2
        return self.combine(self._query(2 * node, lo, mid, left, right),
                            self._query(2 * node + 1, mid + 1, hi, left, right))
```

Any associative operation with an identity works (sum with 0, min with +∞, max with −∞, gcd with 0); the tests run all four against brute force. An array of 4n entries suffices, because the height is ⌈log₂ n⌉ and 2^(⌈log₂ n⌉ + 1) < 4n. Lazy propagation for range updates and trees allocated on demand are in 39f.12.6; a Fenwick tree is shorter for prefix sums with point updates but needs an invertible operation.

### 39e.10.7 Huffman coding

A variable-length code can give frequent symbols short codewords, but it must decode without separators, which holds when no codeword is a prefix of another. A prefix-free code is a binary tree with the symbols at its leaves: the path from the root (0 for left, 1 for right) is the codeword, and a symbol costs its frequency times its depth. Huffman's algorithm builds the cheapest tree by repeatedly merging the two lightest trees, O(k log k) for k symbols with a heap:

```python
class _Merged:
    __slots__ = ("left", "right")

    def __init__(self, left, right):
        self.left, self.right = left, right


def huffman_codes(freq):
    """Optimal prefix-free code for {symbol: count}: keep merging the two lightest trees. O(k log k)."""
    if len(freq) == 1:
        return {symbol: "0" for symbol in freq}          # a lone symbol still needs one bit per use
    heap = [(count, i, symbol) for i, (symbol, count) in enumerate(freq.items())]
    heapq.heapify(heap)
    order = len(heap)                                    # tie-breaker, so two trees are never compared
    while len(heap) > 1:
        c1, _, a = heapq.heappop(heap)
        c2, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (c1 + c2, order, _Merged(a, b)))
        order += 1
    codes = {}

    def assign(tree, path):                              # preorder: the path from the root is the code
        if isinstance(tree, _Merged):
            assign(tree.left, path + "0")
            assign(tree.right, path + "1")
        else:
            codes[tree] = path

    if heap:
        assign(heap[0][2], "")
    return codes


def huffman_encode(symbols, codes):
    return "".join(codes[s] for s in symbols)


def huffman_decode(bits, codes):
    """No separators needed: in a prefix-free code the first codeword that matches is the right one."""
    by_code = {code: symbol for symbol, code in codes.items()}
    out, current = [], ""
    for bit in bits:
        current += bit
        if current in by_code:
            out.append(by_code[current])
            current = ""
    if current:
        raise ValueError("the bits end in the middle of a codeword")
    return out
```

**Why it is optimal.** First, an exchange argument: in some optimal tree the two least frequent symbols are siblings at maximum depth, because moving a lighter symbol deeper and a heavier one shallower never increases the cost. Second, replacing those two siblings by one leaf whose frequency is their sum, f₁ + f₂, gives a tree for a problem with one fewer symbol and lowers the cost by exactly f₁ + f₂, so the reduced problem's optimum is at most the original optimum minus (f₁ + f₂). The algorithm's first merge makes that reduction, and by induction it then builds an optimal tree for the reduced problem; splitting the merged leaf back into the two symbols adds exactly f₁ + f₂, which brings the cost to at most the original optimum, so the result is optimal. The total cost is the sum of all merge weights (the whole of LC 1167†), and the average codeword length lies between the entropy H and H + 1.

The tests compare Huffman's cost on 300 random alphabets with a brute force over all codeword lengths allowed by Kraft's inequality (lengths l₁, …, l_k belong to some prefix code exactly when Σ 2^(−l_i) ≤ 1). Whole-bit codewords waste up to a bit per symbol on skewed data (a two-symbol source with probabilities 0.99 and 0.01 has an entropy of about 0.08 bits per symbol, but Huffman spends a full bit on each), where arithmetic coding and asymmetric numeral systems do better. DEFLATE (zip, gzip, PNG) applies Huffman coding to the output of LZ77 and sends canonical codes as lists of lengths; baseline JPEG also uses it.

## 39e.11 Graphs

### 39e.11.1 Terminology and representations

Edges may be directed, weighted or both; degree counts a vertex's edges (in and out separately when directed). A simple path repeats no vertex. A directed graph is strongly connected if every vertex reaches every other along the edges, and weakly connected if it does once directions are ignored. A tree is a connected acyclic undirected graph (V − 1 edges), a DAG a directed acyclic graph, a multigraph one with parallel edges or self-loops; a graph is dense when E is near V² and sparse when E is near V.

```python
def adjacency_list(n, edges, directed=False):
    """Nodes 0..n-1 and (u, v) pairs -> graph[u] = neighbors of u. O(V + E) space."""
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        if not directed:
            graph[v].append(u)
    return graph
```

| Representation | Space | Is (u, v) an edge? | List u's neighbors | Best for |
|---|---|---|---|---|
| Adjacency list | O(V + E) | O(deg u) | O(deg u) | Sparse graphs; nearly every traversal |
| Adjacency matrix | O(V²) | O(1) | O(V) | Dense graphs; Floyd–Warshall; frequent edge tests |
| Edge list | O(E) | O(E) | O(E) | Kruskal (sort the edges); Bellman–Ford (relax every edge) |

Many interview graphs are implicit (grid cells, words one letter apart in 127 Word Ladder, lock combinations in 752 Open the Lock, worked in 39g.6.2): generate the neighbors on the fly.

### 39e.11.2 Traversal: marking vertices, or marking the current path

A tree walk never meets a node twice, but a graph walk can, through a second edge into the same vertex or around a cycle back to where it began. Recording every vertex the first time it is reached means each vertex is expanded once, so DFS and BFS cost O(V + E); without the record, one cycle keeps the walk going forever. BFS marks a vertex when it is queued, not when it is dequeued, so no vertex is queued twice, and BFS first reaches each vertex along a path with the fewest edges. In a disconnected graph, start a traversal from every vertex still unvisited.

```python
def dfs_order(graph, start):
    """Nodes reachable from start, in depth-first preorder. visited lets each node enter once: O(V + E)."""
    visited, order = set(), []

    def dfs(u):
        visited.add(u)
        order.append(u)                   # preorder position
        for v in graph[u]:
            if v not in visited:
                dfs(v)

    dfs(start)
    return order


def bfs_distances(graph, start):
    """Fewest edges from start to each reachable node: mark on enqueue; the first visit is the closest."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def all_paths(graph, source, target):
    """Every simple path source -> target (LC 797 on a DAG). on_path, not visited: a node may lie on many paths."""
    paths, path, on_path = [], [source], {source}

    def dfs(u):
        if u == target:
            paths.append(path.copy())
            return
        for v in graph[u]:
            if v not in on_path:          # only blocks cycles back into the current path
                on_path.add(v)
                path.append(v)
                dfs(v)
                path.pop()                # postorder: leave v, so other paths may use it
                on_path.remove(v)

    dfs(source)
    return paths
```

`all_paths` needs a different set. A vertex may appear in many paths, so a global visited set would lose answers; what must be prevented is a vertex appearing twice in the current path. `on_path` therefore mirrors the recursion stack: `v` joins it just before the call that extends the path to `v` and leaves just after that call returns, so later paths may pass through `v` again. On the DAG of LC 797 the check never fires, but it makes the code correct on graphs with cycles, where it enumerates simple paths; their number can grow exponentially. Cycle detection in directed graphs uses both sets, since an edge to a vertex on the current path closes a cycle (39f.13.2).

### 39e.11.3 Eulerian paths and circuits

An Eulerian path uses every edge exactly once; an Eulerian circuit also ends where it started. Euler settled the Königsberg bridges question in 1736 by counting degrees: each pass through a vertex uses one edge in and one out, so every vertex except the two ends needs even degree. An undirected graph whose edges lie in one connected piece has an Eulerian circuit when every degree is even and a path when exactly two degrees are odd (the path joins those two). A directed graph needs its edges in one weakly connected piece and in-degree equal to out-degree everywhere (a circuit), or everywhere except one start with one extra outgoing edge and one end with one extra incoming edge. Königsberg's four land masses had degrees 5, 3, 3 and 3, so no such walk exists.

```python
def euler_kind(n, edges, directed=False):
    """'circuit', 'path' or None: can one trail use every edge of this multigraph exactly once?"""
    if not edges:
        return "circuit"
    out_deg, in_deg, ds = [0] * n, [0] * n, DisjointSet(n)
    for u, v in edges:
        out_deg[u] += 1
        in_deg[v] += 1
        ds.union(u, v)
    if len({ds.find(u) for u, _ in edges}) > 1:          # edges in two pieces: no single trail
        return None
    if directed:
        unbalanced = sorted(out_deg[v] - in_deg[v] for v in range(n) if out_deg[v] != in_deg[v])
        return "circuit" if not unbalanced else "path" if unbalanced == [-1, 1] else None
    odd = sum((out_deg[v] + in_deg[v]) % 2 for v in range(n))
    return "circuit" if odd == 0 else "path" if odd == 2 else None
```

The tests check `euler_kind` against a brute-force search for a trail over 300 random multigraphs with self-loops. Building the trail itself is Hierholzer's algorithm, O(E), in 39f.13.7 (LC 332, 753, 2097).

### 39e.11.4 Shortest paths: which algorithm when

| Graph and question | Algorithm | Time | Key idea |
|---|---|---|---|
| Unweighted, one source | BFS | O(V + E) | The first visit is the shortest |
| Weights 0 or 1 | 0-1 BFS with a deque | O(V + E) | 0-edges to the front, 1-edges to the back (2290) |
| Non-negative weights, one source | Dijkstra with a binary heap | O((V + E) log V) | Settle in order of distance (39d.23) |
| A DAG, any weights | Relax in topological order | O(V + E) | Edges into v are relaxed before v is used |
| Negative weights; negative cycles | Bellman–Ford | O(VE) | V − 1 rounds; a further improvement means a negative cycle |
| At most k edges | Bellman–Ford for k rounds | O(kE) | Relax from the previous round's distances (787) |
| All pairs, a few hundred vertices | Floyd–Warshall | O(V³) | Admit intermediate vertices one at a time (1334) |
| One target, with a distance estimate | A* | Depends on the estimate | Distance so far plus an admissible (never too large) estimate |

**Why Dijkstra needs non-negative weights.** It settles vertices in increasing order of distance, assuming no later path is shorter. With s→a of weight 2, s→b of weight 3 and b→a of weight −2, it settles a at 2, but s→b→a costs 1. A* with h = 0 is Dijkstra; an admissible h keeps the result optimal, and a consistent h (never dropping by more than the weight of the edge crossed) means no settled vertex is reopened, as with Manhattan distance on a grid. Implementations: Dijkstra in 39d.23 and 39f.13.4, A* in 39f.13.5, Floyd–Warshall in 39f.13.8, 0-1 BFS in 39g.6.5, and the k-round Bellman–Ford of 787 in 39g.10.4.

### 39e.11.5 Minimum spanning trees

A minimum spanning tree (MST) connects all V vertices with V − 1 edges of the smallest total weight. One fact justifies every MST algorithm, the cut property: for any split of the vertices into two sides, a lightest edge crossing the split belongs to some MST. (If an MST T avoids such an edge e, adding e closes a cycle that crosses the split again through some edge f, and swapping f for e gives a spanning tree no heavier than T.) Kruskal's algorithm sorts the edges and keeps each one that joins two components, tracked with union-find: O(E log E). Prim's algorithm grows one tree, adding the lightest edge leaving it with a heap: O(E log V), or O(V²) with an array, which wins on dense graphs such as all pairs of points (1584). Both are implemented in 39f.13.6.

### 39e.11.6 Union-find

Union-find keeps a partition as a forest of parent pointers: `find` follows parents to the root that names a set, and `union` links one root under the other. Union by size hangs the smaller tree under the larger, so a vertex's depth grows only when its tree at least doubles, which bounds every depth by log₂ n; path compression points every vertex on a `find` path at the root. With both, m operations take O(m·α(n)) time, where α is the inverse Ackermann function (Tarjan, 1975), at most 4 for any n that could ever be stored.

```python
class DisjointSet:
    """Union-find with union by size and full path compression: near-constant amortized time per operation."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n                    # number of components

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:     # second pass: point every node on the path at the root
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra              # smaller tree under the larger: depth grows only when size doubles
        self.size[ra] += self.size[rb]
        self.count -= 1
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)
```

The tests compare the components with BFS after every union and check the depth bound. 39d.23 shows path halving, a one-pass variant with the same bound, and 39f.13.3 applies the structure. Union-find cannot split a set once merged, so connectivity under edge deletions needs other methods, such as processing the operations in reverse when they are all known in advance.

## 39e.12 The ten sorting algorithms

### 39e.12.1 What to compare

A sort is **stable** if equal keys keep their input order, which lets you sort records by a secondary key and then stably by the primary key; **in place** if it needs O(1) extra memory (or O(log n) of stack, by some definitions); **adaptive** if partly sorted input makes it faster. A **comparison sort** learns about its input only by comparing pairs: as a decision tree it must tell all n! orderings apart, and a binary tree with n! leaves has height at least log₂(n!) ≈ n log₂ n − 1.44n, so it needs Ω(n log n) comparisons in the worst case and on average. Counting, bucket and radix sort use the keys as array indices and escape the bound when keys are small integers or evenly spread.

| Algorithm | Best | Average | Worst | Extra space | In place | Stable | Adaptive |
|---|---|---|---|---|---|---|---|
| Selection | n² | n² | n² | O(1) | Yes | No | No |
| Bubble (early exit) | n | n² | n² | O(1) | Yes | Yes | Yes |
| Insertion | n | n² | n² | O(1) | Yes | Yes | Yes: O(n + inversions) |
| Shell (Knuth's gaps) | n log n | No formula known; about n^1.22 in the tests | n^(3/2) | O(1) | Yes | No | Partly |
| Quick (random pivot, three-way) | n (all keys equal) | n log n expected | n² (vanishingly unlikely) | O(log n) stack | Yes, under the looser definition | No | No |
| Merge (top-down) | n log n | n log n | n log n | O(n) | No | Yes | No |
| Heap | n log n (n if all keys equal) | n log n | n log n | O(1) | Yes | No | No |
| Counting | n + k | n + k | n + k | O(n + k) | No | Yes | No |
| Bucket | n | n for uniform data | n² | O(n + buckets) | No | Yes, with a stable inner sort | No |
| Radix (LSD) | d(n + b) | d(n + b) | d(n + b) | O(n + b) | No | Yes | No |

Here k is the range of the keys, b the base and d the number of digits. Every sort below rearranges the list it is given (the last three build their output and copy it back). The seven comparison sorts use only `<`, like Python's own sort; the last three compute with the keys themselves. The tests run all ten against `sorted()` on 206 integer inputs, and the eight that accept floats on 50 float inputs as well; they confirm stability for the six stable sorts with tagged equal keys and find an input on which each of the other four reorders equal keys.

### 39e.12.2 Selection, bubble and insertion sort

**Selection sort** swaps the minimum of the rest into place: always n(n − 1)/2 comparisons, even on sorted input, but at most n − 1 swaps, which matters only when writes are expensive. It is not stable, because a swap can carry an item past others equal to it: in [2a, 2b, 1], bringing 1 to the front sends 2a to the end, behind 2b.

```python
def selection_sort(a):
    """Grow a sorted prefix by swapping in the minimum of the rest: n(n - 1)/2 comparisons, n - 1 swaps."""
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            if a[j] < a[m]:
                m = j
        a[i], a[m] = a[m], a[i]           # a[i] may leap past items equal to it: not stable
```

**Bubble sort** swaps adjacent pairs that are out of order. After a pass, everything from the last swap onward is final, so the next pass stops there, and a pass without swaps ends the sort: sorted input costs n − 1 comparisons. Swapping only on strict inequality keeps it stable.

```python
def bubble_sort(a):
    """Swap adjacent pairs that are out of order. Everything after the last swap is final; stop at none."""
    n = len(a)
    while n > 1:
        last_swap = 0
        for i in range(1, n):
            if a[i] < a[i - 1]:           # strict: equal neighbors never swap, so the sort is stable
                a[i - 1], a[i] = a[i], a[i - 1]
                last_swap = i
        n = last_swap
```

**Insertion sort** shifts the larger items of the sorted prefix one place right until the next item fits. Every shift removes exactly one inversion (a pair in the wrong order), so the cost is O(n + inversions): linear on nearly sorted data, quadratic on random data (n(n − 1)/4 inversions on average); the tests check that its comparisons lie between the inversion count and that count plus n − 1. That is why Timsort sorts short runs with binary insertion sort.

```python
def insertion_sort(a):
    """Insert each item into the sorted prefix by shifting larger ones right. O(n + inversions), stable."""
    for i in range(1, len(a)):
        x, j = a[i], i
        while j > 0 and x < a[j - 1]:
            a[j] = a[j - 1]
            j -= 1
        a[j] = x
```

### 39e.12.3 Shell sort

Insertion sort is slow on random data because each shift moves an item one place. Shell sort first insertion-sorts the items h apart for a large gap h, so items travel far in few moves, then repeats with smaller gaps and finishes with h = 1 on a nearly sorted array. An h-sorted array stays h-sorted after it is k-sorted, so later passes do not undo earlier ones.

```python
def shell_sort(a):
    """Insertion sort on items h apart for shrinking gaps h = ..., 40, 13, 4, 1 (Knuth's 3h + 1)."""
    n, h = len(a), 1
    while h < n // 3:
        h = 3 * h + 1
    while h >= 1:
        for i in range(h, n):             # after this pass every h-spaced subsequence is sorted
            x, j = a[i], i
            while j >= h and x < a[j - h]:
                a[j] = a[j - h]
                j -= h
            a[j] = x
        h //= 3
```

The gaps determine the complexity. Shell's original halving gaps can take Θ(n²) time (with n a power of two, odd and even positions never meet until the last pass). Knuth's gaps 1, 4, 13, 40, …, each 3h + 1, used here, have a worst case of Θ(n^(3/2)); Pratt's 2^p·3^q gaps reach Θ(n log² n) with many more passes; Sedgewick's reach O(n^(4/3)); Ciura's 1, 4, 10, 23, 57, 132, 301, 701, found by experiment, is among the fastest in practice. No average-case formula is known for Knuth's gaps; in the tests, random inputs of 1,000, 4,000 and 16,000 items took 14,338, 78,868 and 416,878 comparisons, growing like n^1.22. Shell sort is unstable, since gapped moves carry equal items past each other.

### 39e.12.4 Quick sort: the work happens before the recursion

Quick sort makes its comparisons on the way down. Partitioning a range around a pivot (smaller items to its left, larger to its right) fixes the pivot's final index before either side is sorted, so each call completes its own work before it recurses: drawn as a tree whose nodes are the pivots, the recursion is a preorder walk (39e.9.2). Balanced splits give about log₂ n levels of O(n) work; always pivoting on the first item turns sorted input into a path n levels deep, O(n²). A random pivot makes the expected cost O(n log n) on every input, about 2n·ln n ≈ 1.39·n·log₂ n comparisons.

```python
import random


def quick_sort(a, rng=random):
    """Random pivot, three-way partition, recursion on the smaller side only: O(n log n) expected, O(log n) stack."""
    def sort(lo, hi):                     # sorts a[lo..hi]
        while lo < hi:
            pivot = a[rng.randint(lo, hi)]
            lt, i, gt = lo, lo, hi        # a[lo:lt] < pivot, a[lt:i] == pivot, a[gt + 1:hi + 1] > pivot
            while i <= gt:
                if a[i] < pivot:
                    a[lt], a[i] = a[i], a[lt]
                    lt += 1
                    i += 1
                elif pivot < a[i]:
                    a[i], a[gt] = a[gt], a[i]
                    gt -= 1
                else:
                    i += 1
            if lt - lo < hi - gt:         # the partition was the preorder work; now the two subtrees
                sort(lo, lt - 1)
                lo = gt + 1
            else:
                sort(gt + 1, hi)
                hi = lt - 1

    sort(0, len(a) - 1)
```

Three choices make this version robust. The three-way partition (Dijkstra's Dutch national flag, LC 75) gathers the items equal to the pivot in the middle and never touches them again, so duplicates speed it up and all-equal input takes one pass. Recursing into the smaller side and looping on the larger keeps the stack at O(log n). The random pivot defeats adversarial input. The classic two-way schemes are Lomuto's (one scan, pivot at the end; simple, but more swaps and O(n²) when all keys are equal) and Hoare's (two indices moving inward; fewer swaps and balanced splits on equal keys). Quick sort is not stable. Introsort, the usual implementation of C++'s `std::sort`, switches to heap sort when the recursion gets deeper than about 2·log₂ n, which guarantees O(n log n). Quickselect, the one-sided version that finds the k-th smallest item in expected O(n) (215), is in 39f.11.4.

### 39e.12.5 Merge sort: the work happens after the recursion

Merge sort makes no comparisons on the way down: it cuts the range at the middle, recurses into both halves, and compares items only while merging two finished halves on the way back up, at the postorder position of 39e.9.2. Each of the ⌈log₂ n⌉ levels merges n items, so it takes O(n log n) in every case, with at most n⌈log₂ n⌉ − 2^⌈log₂ n⌉ + 1 comparisons. Taking from the left half on ties makes it stable; the price is O(n) extra memory.

```python
def merge_sort(a):
    """Sort both halves, then merge them (postorder work). Ties take the left item, so it is stable."""
    buffer = a.copy()

    def sort(lo, hi):                     # sorts a[lo:hi]
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        sort(lo, mid)
        sort(mid, hi)
        buffer[lo:hi] = a[lo:hi]
        i, j = lo, mid
        for k in range(lo, hi):
            if j == hi or (i < mid and not buffer[j] < buffer[i]):
                a[k] = buffer[i]
                i += 1
            else:
                a[k] = buffer[j]
                j += 1

    sort(0, len(a))
```

Merge sort suits linked lists, where merging relinks nodes without extra memory (148), and external sorting of runs on disk. The merge also counts inversions: an item from the right half placed first forms an inversion with each item still waiting in the left half, so the lab's `count_inversions` adds `mid - i` at that step. Problems 315 and 493 use the same idea (39f.11.3).

### 39e.12.6 Heap sort

Heap sort builds a max-heap in place in O(n) (39e.10.5), then repeatedly swaps the maximum to the end and sifts the new root down within the shrinking heap.

```python
def heap_sort(a):
    """Build a max-heap in place, then swap the max to the end and shrink the heap: O(n log n), O(1) space."""
    heapify(a, operator.gt)
    for end in range(len(a) - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(a, 0, end, operator.gt)
```

It guarantees O(n log n) with O(1) extra memory and no recursion, which no other comparison sort here offers; but it is unstable, and its sift-downs jump across the array and miss the cache, so it usually runs slower than quick sort. Its main practical role is introsort's fallback.

### 39e.12.7 Counting, bucket and radix sort

**Counting sort** sorts integers spanning a range of size k: count each value, turn the counts into end positions with a running sum, and place the items. Placing from right to left puts the last of several equal items into the last slot for that value, which makes the sort stable; shifting by the minimum handles negative values. It runs in O(n + k), wasteful when the range is huge.

```python
def counting_sort(a):
    """Integers in [lo, hi]: count, turn counts into end positions, place right to left. O(n + k), stable."""
    if not a:
        return
    lo, hi = min(a), max(a)
    count = [0] * (hi - lo + 1)           # offset by lo, so negative values work
    for x in a:
        count[x - lo] += 1
    for v in range(1, len(count)):        # now count[v] = how many items are <= lo + v
        count[v] += count[v - 1]
    out = [None] * len(a)
    for x in reversed(a):                 # right to left: the last equal item takes the last free slot
        count[x - lo] -= 1
        out[count[x - lo]] = x
    a[:] = out
```

**Bucket sort** spreads the values over buckets by value range (the bucket index must never decrease as the value grows), sorts each bucket and concatenates them. With n values spread uniformly over n buckets, insertion-sorting the buckets costs O(n) in expectation, because the expected sum of the squared bucket sizes is below 2n; if everything lands in one bucket, it costs the inner sort's worst case, O(n²) here. Variants solve 164 (with n − 1 buckets the largest gap cannot lie inside a bucket) and 347 and 451 (buckets indexed by frequency).

```python
def bucket_sort(a, buckets=None):
    """Numbers: scatter by value into k buckets, insertion-sort each, concatenate. Expected O(n) if uniform."""
    if len(a) < 2:
        return
    lo, hi = min(a), max(a)
    if lo == hi:
        return
    k = buckets or len(a)
    groups = [[] for _ in range(k)]
    for x in a:
        groups[min(k - 1, int((x - lo) * k / (hi - lo)))].append(x)     # monotone in x
    for group in groups:
        insertion_sort(group)
    a[:] = [x for group in groups for x in group]
```

**Radix sort**, least significant digit first, runs a stable counting sort on the last digit, then on the next, and so on. After pass t the items are sorted by their last t digits: the pass orders them by digit t, and stability keeps the earlier order among items with equal digit t. With d digits in base b it costs O(d(n + b)); 32-bit integers in base 256 need four passes. Most-significant-digit-first radix sort recurses into buckets instead and suits strings.

```python
def radix_sort(a, base=10):
    """Integers: stable counting sort on each digit of x - min, least significant first. O(d(n + base))."""
    if not a:
        return
    lo = min(a)
    largest, place = max(a) - lo, 1
    while place <= largest:               # one pass per digit of the largest shifted value
        count = [0] * base
        for x in a:
            count[(x - lo) // place % base] += 1
        for d in range(1, base):
            count[d] += count[d - 1]
        out = [None] * len(a)
        for x in reversed(a):
            d = (x - lo) // place % base
            count[d] -= 1
            out[count[d]] = x
        a[:] = out
        place *= base
```

### 39e.12.8 How Python sorts

`list.sort` and `sorted` use Timsort, which Tim Peters wrote for Python in 2002. It finds natural runs (ascending, or descending and then reversed in place; before 3.13 a descending run had to be strictly descending, so that reversing it could not reorder equal items), extends short runs to between 32 and 64 items with binary insertion sort, and merges runs from a stack, switching to galloping (an exponential search) once one run has won 7 times in a row (`MIN_GALLOP`), so runs that barely overlap merge almost for free. Since Python 3.11, the merge order follows Munro and Wild's powersort, provably near-optimal in the entropy of the run lengths (`Objects/listsort.txt`). The result is stable, O(n log n) in the worst case and O(n) on sorted or reversed data: in the tests, sorting 100,000 sorted or exactly reversed items took 99,999 comparisons.

The sort only uses `<`. Prefer `key=` to comparison functions: the key function runs once per item, and the comparisons stay inside C. `functools.cmp_to_key` wraps each item in an object whose `<` calls your Python function, about 1.5 million calls for 100,000 random items; in local measurements on CPython 3.11, sorting 200,000 floats through `cmp_to_key` took 7 to 9 times as long as the equivalent `key=`. Use tuples for several keys, `reverse=True`, or two stable passes when keys sort in different directions. LC 179 Largest Number is where a comparison is natural (a goes first when the string a + b is larger than b + a), and `cmp_to_key` handles it.

**Interview line:** *"Comparison sorts need Ω(n log n) comparisons because they must tell n! orderings apart; merge sort meets the bound in every case and is stable, quick sort meets it in expectation with O(log n) extra space, and counting or radix sort beat it only by using the keys as array indices."*

## 39e.13 Choosing a data structure

Start from the operations the problem needs:

| Operations you need | Structure | Python | Cost |
|---|---|---|---|
| Index access, append at the end | Dynamic array | `list` | O(1), amortized for append |
| Add and remove at both ends | Deque | `collections.deque` | O(1) |
| Last in, first out | Stack | `list` | O(1) amortized |
| First in, first out; BFS | Queue | `deque` (`append`, `popleft`) | O(1) |
| The last k items of a stream | Ring buffer | `deque(maxlen=k)` | O(1) |
| Lookup, insert and delete by key | Hash map | `dict`, `Counter`, `defaultdict` | O(1) expected |
| Membership | Hash set | `set`, `frozenset` | O(1) expected |
| Lookup plus recency (LRU) | LinkedHashMap | `OrderedDict` (`move_to_end`, `popitem(last=False)`) | O(1) expected |
| Insert, delete, random element | ArrayHashMap | `list` plus a `dict` of positions | O(1) expected |
| Repeated minimum or maximum with inserts | Binary heap | `heapq` | O(log n) per push or pop |
| Sorted order with updates; floor, ceiling, rank | Balanced BST or skip list | `bisect` on a `list`, or `sortedcontainers` | O(log n) search; O(n) `bisect` insertion |
| Prefix queries over strings | Trie | Nested `dict`s | O(length) |
| Range queries with point updates | Segment tree or Fenwick tree | Write it | O(log n) |
| Connectivity as edges arrive | Union-find | Write it | Nearly O(1) amortized |
| Dense sets or flags over small integers | Bitset | `bytearray`, or an `int` for small masks | O(1) per bit with `bytearray`; an `int` is rebuilt on every change |
| Approximate membership in little memory | Bloom filter | Write it, or use a library | O(k) |
| Graph traversal | Adjacency list | `list` of lists, `defaultdict(list)` | O(V + E) |

When two rows fit, decide by whether you need a worst-case guarantee (a hash map's O(1) is expected, a balanced tree's O(log n) guaranteed), whether order matters, memory, and how much code the interview leaves time for.

## 39e.14 Practice set, study plan and interview questions

### 39e.14.1 Practice set

Problems marked † need LeetCode Premium. Do the design problems without the corresponding built-in.

| Section | Problems |
|---|---|
| 39e.1–39e.3 Complexity and arrays | 53 Maximum Subarray (all three versions); 27 Remove Element; 283 Move Zeroes; 189 Rotate Array; 88 Merge Sorted Array |
| 39e.4 Linked lists | 707 Design Linked List; 206 Reverse Linked List; 21 Merge Two Sorted Lists; 160 Intersection of Two Linked Lists; 430 Flatten a Multilevel Doubly Linked List; 138 Copy List with Random Pointer |
| 39e.5 Ring buffers, skip lists, bitsets | 622 Design Circular Queue; 641 Design Circular Deque; 346 Moving Average from Data Stream†; 1206 Design Skiplist; 2166 Design Bitset |
| 39e.6 Stacks and queues | 232 Implement Queue using Stacks; 225 Implement Stack using Queues; 155 Min Stack; 933 Number of Recent Calls; 20 Valid Parentheses |
| 39e.7 Hash tables | 705 Design HashSet; 706 Design HashMap; 1 Two Sum; 49 Group Anagrams; 128 Longest Consecutive Sequence; 219 Contains Duplicate II |
| 39e.8 Hash-table variations | 146 LRU Cache; 460 LFU Cache; 380 Insert Delete GetRandom O(1); 381 Insert Delete GetRandom O(1) - Duplicates allowed; 710 Random Pick with Blacklist |
| 39e.9 Binary and n-ary trees | 144 Binary Tree Preorder Traversal, 94 Binary Tree Inorder Traversal and 145 Binary Tree Postorder Traversal (recursively, then with a stack); 102 Binary Tree Level Order Traversal; 104 Maximum Depth of Binary Tree; 111 Minimum Depth of Binary Tree; 589 N-ary Tree Preorder Traversal; 429 N-ary Tree Level Order Traversal; 958 Check Completeness of a Binary Tree |
| 39e.10 BSTs, tries, heaps, segment trees, Huffman | 700 Search in a Binary Search Tree; 701 Insert into a Binary Search Tree; 450 Delete Node in a BST; 98 Validate Binary Search Tree; 1382 Balance a Binary Search Tree; 208 Implement Trie (Prefix Tree); 211 Design Add and Search Words Data Structure; 648 Replace Words; 677 Map Sum Pairs; 703 Kth Largest Element in a Stream; 1046 Last Stone Weight; 215 Kth Largest Element in an Array; 303 Range Sum Query - Immutable; 307 Range Sum Query - Mutable; 1167 Minimum Cost to Connect Sticks† |
| 39e.11 Graphs | 797 All Paths From Source to Target; 1971 Find if Path Exists in Graph; 785 Is Graph Bipartite?; 332 Reconstruct Itinerary; 753 Cracking the Safe; 743 Network Delay Time; 787 Cheapest Flights Within K Stops; 2290 Minimum Obstacle Removal to Reach Corner; 1334 Find the City With the Smallest Number of Neighbors at a Threshold Distance; 1584 Min Cost to Connect All Points; 547 Number of Provinces; 1319 Number of Operations to Make Network Connected |
| 39e.12 Sorting | 912 Sort an Array (with merge, heap, quick and counting sort); 75 Sort Colors; 148 Sort List; 147 Insertion Sort List; 315 Count of Smaller Numbers After Self; 493 Reverse Pairs; 164 Maximum Gap; 274 H-Index; 1122 Relative Sort Array; 451 Sort Characters By Frequency; 179 Largest Number |

### 39e.14.2 Study plan

Two weeks at about an hour a day, before or alongside the pattern plan of 39d.25:

| Days | Build from memory | Then solve |
|---|---|---|
| 1–2 | `DynamicArray`, `DoublyLinkedList`, `RingBuffer` | 707, 622, 641, 232 |
| 3–4 | `ChainedHashMap`, `LinearProbingHashMap` with both kinds of deletion | 705, 706, 1, 49 |
| 5 | `LinkedHashMap`, `LRUCache`, `ArrayHashMap` | 146, 380, 460 |
| 6 | `MinHeap` with `heapify`; `Trie` | 703, 215, 208, 211 |
| 7 | The three depth-first orders, the three level orders | 144, 94, 145, 102, 111, 429 |
| 8–9 | A plain BST with deletion, then `AVLTree`; `SegmentTree` | 450, 1382, 307 |
| 10 | Graph traversal, `all_paths`, `DisjointSet`, `euler_kind` | 797, 785, 547, 1319 |
| 11–12 | The ten sorts and the inversion count | 912 (several ways), 75, 148, 315 |
| 13 | Bloom filter, Huffman coding, skip list | 1206, 1167† |
| 14 | Explain each invariant and cost aloud | The questions below |

Each day, write the structure without looking, swap it into `ds_basics.py`, run the tests, and note in your error log (39d.25) which invariant you broke.

### 39e.14.3 Interview questions with model answers

1. **Why is `list.append` O(1) if the list sometimes copies itself?** The capacity grows by a constant factor (about 9/8 in CPython), so the copies form a geometric series: n appends cause fewer than n·r/(r − 1) copies, O(1) amortized each, though one append can cost O(n). Growing by a constant amount would make appends Θ(n) amortized.

2. **Why shrink at a quarter full rather than at half full?** Halving at half full lets alternating appends and pops copy the whole array every time; shrinking at a quarter leaves it half full after every resize, so Θ(capacity) operations pay for each copy.

3. **When would you pick a linked list over an array?** When items are removed or moved through handles in O(1) (an LRU cache), sublists are spliced, or reallocation spikes are unacceptable; otherwise the array wins on indexing, memory and cache behavior.

4. **How does a hash table get O(1), and what is its worst case?** The hash spreads keys over the slots and resizing bounds the load factor, so operations are O(1) expected. If all keys collide, they are O(n); the defenses are a keyed random hash (SipHash in Python), tree bins (Java) or a balanced tree map.

5. **How do you delete from a linear-probing table?** Not by emptying the slot, which cuts later keys' probe paths. Leave a tombstone that lookups skip and the next rebuild removes, or shift later entries of the cluster back into the hole when the hole lies on their probe path.

6. **How does Python's dict keep insertion order?** A sparse index table, probed with perturbation, points into a dense entries array kept in insertion order; iteration walks the entries, and deletions leave holes that the next resize compacts. The order has been a language guarantee since 3.7.

7. **Why must dictionary keys be immutable?** The entry is filed under the key's hash at insertion; after the key changes, neither its old value nor its new one finds the entry, which stays stranded.

8. **Design an LRU cache with O(1) `get` and `put`.** A hash map from key to node of a doubly linked list in recency order: `get` and `put` move the node to the end, and `put` evicts from the front when over capacity. The list is doubly linked so that the handle alone can unlink a node in O(1).

9. **Size a Bloom filter for 100 million URLs at 1% false positives.** m = −n·ln p/(ln 2)² ≈ 9.6 bits per URL, about 958 million bits or 120 MB, with k = (m/n)·ln 2 ≈ 7. A "yes" must be confirmed against the real store, and deletion needs a counting variant.

10. **Why is heapify O(n) when n pushes are O(n log n)?** Sifting down costs a node's height, and the heights sum to n minus the number of 1 bits in n; a push sifts up by its depth instead, and about half the nodes are leaves at depth ⌊log₂ n⌋ or one less.

11. **AVL or red-black?** Both are O(log n). AVL trees are more rigidly balanced (height about 1.44 log₂ n against 2 log₂ n), so lookups are slightly faster; red-black trees need at most two rotations per insertion and three per deletion, so updates are cheaper.

12. **BFS or DFS?** BFS finds shortest paths in unweighted graphs and stops at the nearest answer but holds a frontier (O(width)); DFS holds one path (O(height)) and suits exhaustive search, cycle detection and anything computed from subtrees.

13. **Why does Dijkstra fail with negative edges?** It finalizes a vertex when it leaves the heap, assuming no later path is shorter, and a negative edge breaks that. Use Bellman–Ford (O(VE); it also detects negative cycles) or, on a DAG, topological-order relaxation.

14. **Is quick sort stable, and how do you avoid its worst case?** It is not stable. Random pivots make the quadratic case vanishingly unlikely, a three-way partition handles duplicates, recursing into the smaller side bounds the stack, and introsort falls back to heap sort when the recursion gets too deep.

15. **What does Python's sort do, and why `key=` over a comparison function?** Timsort merges natural runs (in powersort's order since 3.11): stable, O(n) on sorted input, O(n log n) worst case. A key function runs n times; `cmp_to_key` calls Python code on each of roughly n log₂ n comparisons.

## Sources

- labuladong, *labuladong Algo Notes* (English edition), "Getting Started: Data Structures and Sorting" and the complexity articles (the topic map this chapter follows): https://labuladong.online/en/algo/home/; table of contents: https://github.com/labuladong/fucking-algorithm/blob/english/README.md
- T. H. Cormen, C. E. Leiserson, R. L. Rivest and C. Stein, *Introduction to Algorithms*, 4th ed., MIT Press, 2022 (divide and conquer, heapsort, quicksort, linear-time sorting, hash tables, search trees, red-black trees, Huffman codes, amortized analysis, disjoint sets, spanning trees, shortest paths).
- D. E. Knuth, *The Art of Computer Programming*, Vol. 3: *Sorting and Searching*, 2nd ed., Addison-Wesley, 1998 (Shellsort; linear probing and its deletion algorithm).
- CPython source (branches 3.6 to 3.15 and main, read October 2026): `Objects/listobject.c`, `Objects/dictobject.c`, `Objects/setobject.c`, `Modules/_collectionsmodule.c`, `Lib/heapq.py`, `Objects/listsort.txt`: https://github.com/python/cpython; pull request 28108 (bpo-34561), powersort, released in 3.11: https://github.com/python/cpython/pull/28108
- Python documentation: https://docs.python.org/3/reference/datamodel.html#object.__hash__, https://docs.python.org/3/library/stdtypes.html#mapping-types-dict, https://docs.python.org/3/faq/design.html#why-must-dictionary-keys-be-immutable, https://docs.python.org/3/library/collections.html, https://docs.python.org/3/library/heapq.html, https://docs.python.org/3/howto/sorting.html, https://docs.python.org/3/whatsnew/3.11.html (siphash13, bpo-29410; string-keyed dicts without stored hashes, bpo-46845); PEP 456 (SipHash): https://peps.python.org/pep-0456/
- J. I. Munro and S. Wild, "Nearly-optimal mergesorts", ESA 2018; S. A. Crosby and D. S. Wallach, "Denial of service via algorithmic complexity attacks", USENIX Security 2003; oCERT advisory 2011-003: http://ocert.org/advisories/ocert-2011-003.html
- OpenJDK `java/util/HashMap.java`: https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java
- B. H. Bloom, "Space/time trade-offs in hash coding with allowable errors", *Communications of the ACM* 13(7), 1970; A. Kirsch and M. Mitzenmacher, "Less hashing, same performance: building a better Bloom filter", ESA 2006; P. Bose et al., "On the false-positive rate of Bloom filters", *Information Processing Letters* 108(4), 2008 (preprint: https://www.cglab.ca/~morin/publications/ds/bloom-ipl.pdf); L. Fan, P. Cao, J. Almeida and A. Z. Broder, "Summary cache", *IEEE/ACM Transactions on Networking* 8(3), 2000; B. Fan, D. G. Andersen, M. Kaminsky and M. Mitzenmacher, "Cuckoo filter: practically better than Bloom", CoNEXT 2014; RocksDB wiki, "RocksDB Bloom Filter": https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter
- W. Pugh, "Skip lists: a probabilistic alternative to balanced trees", *Communications of the ACM* 33(6), 1990; Redis documentation, sorted sets: https://redis.io/docs/latest/develop/data-types/sorted-sets/
- S. Chambi, D. Lemire, O. Kaser and R. Godin, "Better bitmap performance with Roaring bitmaps", *Software: Practice and Experience* 46(5), 2016.
- G. M. Adelson-Velsky and E. M. Landis, *Doklady Akademii Nauk SSSR* 146, 1962 (AVL trees); L. J. Guibas and R. Sedgewick, "A dichromatic framework for balanced trees", FOCS 1978; L. Devroye, "A note on the height of binary search trees", *Journal of the ACM* 33(3), 1986; B. Reed, "The height of a random binary search tree", *Journal of the ACM* 50(3), 2003; *Sorted Containers* implementation notes: https://grantjenks.com/docs/sortedcontainers/implementation.html; R. W. Floyd, "Algorithm 245: Treesort 3", and J. W. J. Williams, "Algorithm 232: Heapsort", *Communications of the ACM* 7, 1964.
- D. A. Huffman, "A method for the construction of minimum-redundancy codes", *Proceedings of the IRE* 40(9), 1952; RFC 1951, DEFLATE: https://www.rfc-editor.org/rfc/rfc1951
- E. W. Dijkstra, *Numerische Mathematik* 1, 1959; R. Bellman, *Quarterly of Applied Mathematics* 16, 1958; R. W. Floyd, "Algorithm 97", *Communications of the ACM* 5(6), 1962; P. E. Hart, N. J. Nilsson and B. Raphael (A*), *IEEE Transactions on Systems Science and Cybernetics* 4(2), 1968; J. B. Kruskal, *Proceedings of the AMS* 7, 1956; R. C. Prim, *Bell System Technical Journal* 36, 1957; R. E. Tarjan, "Efficiency of a good but not linear set union algorithm", *Journal of the ACM* 22(2), 1975.
- D. L. Shell, "A high-speed sorting procedure", *Communications of the ACM* 2(7), 1959; V. R. Pratt, *Shellsort and Sorting Networks*, PhD thesis, Stanford University, 1971; M. Ciura, "Best increments for the average case of Shellsort", FCT 2001; Wikipedia, "Shellsort": https://en.wikipedia.org/wiki/Shellsort; C. A. R. Hoare, "Quicksort", *The Computer Journal* 5(1), 1962.
- LeetCode problem set: https://leetcode.com/problemset/. Numbers, titles and Premium status (†) checked in October 2026 against the doocs/leetcode index (https://leetcode.doocs.org/en/; repository https://github.com/doocs/leetcode).
- Code: `labs/algorithm-frameworks/ds_basics.py`, `test_ds_basics.py` and `check_chapter_sync.py` in this repository (standard-library Python 3.10+; run `python3 -B test_ds_basics.py`).
