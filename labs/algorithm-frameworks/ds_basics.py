"""Data structures and sorting algorithms built from contiguous arrays and linked nodes (chapter 39e).

Every class and function printed in chapter 39e is copied verbatim from this file; check_chapter_sync.py
enforces it. Standard library only (Python 3.10+). Tests: python3 -B test_ds_basics.py
"""
import hashlib
import heapq
import math
import operator
import random
import struct
import sys
from collections import deque


# ------------------------------------------------------------------------------------ 39e.1 enumeration


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


# ------------------------------------------------------------------------------------ 39e.3 arrays


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


def cpython_list_growth(appends):
    """Capacities a CPython 3.9+ list passes through during appends, from the rule in list_resize."""
    capacities, allocated = [], 0
    for size in range(1, appends + 1):
        if size > allocated:
            allocated = (size + (size >> 3) + 6) & ~3     # size + size/8 + 6, rounded down to a multiple of 4
            capacities.append(allocated)
    return capacities


def measured_list_growth(appends):
    """The same capacities measured with sys.getsizeof: (bytes of the list - bytes of []) / pointer size."""
    items, capacities = [], []
    empty, pointer = sys.getsizeof([]), struct.calcsize("P")
    for i in range(appends):
        items.append(i)
        capacity = (sys.getsizeof(items) - empty) // pointer
        if not capacities or capacity != capacities[-1]:
            capacities.append(capacity)
    return capacities


# ------------------------------------------------------------------------------------ 39e.4 linked lists


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


# ------------------------------------------------------------------------------------ 39e.5 variations


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


class _SkipNode:
    __slots__ = ("key", "value", "forward")

    def __init__(self, key, value, levels):
        self.key, self.value = key, value
        self.forward = [None] * levels    # forward[i]: the next node on level i


class SkipList:
    """Sorted map: a linked list plus random express lanes. Expected O(log n) search, insert and delete."""

    MAX_LEVEL = 32

    def __init__(self, p=0.5, seed=None):
        self._head = _SkipNode(None, None, self.MAX_LEVEL)
        self._levels = 1                  # levels currently in use
        self._size = 0
        self._p = p
        self._rng = random.Random(seed)

    def __len__(self):
        return self._size

    def __iter__(self):
        node = self._head.forward[0]
        while node is not None:
            yield node.key
            node = node.forward[0]

    def _random_levels(self):
        levels = 1                        # a node reaches level i + 1 with probability p^i
        while levels < self.MAX_LEVEL and self._rng.random() < self._p:
            levels += 1
        return levels

    def _predecessors(self, key):
        """For every level, the last node whose key is < key: start high, drop a level when overshooting."""
        update = [self._head] * self.MAX_LEVEL
        node = self._head
        for level in range(self._levels - 1, -1, -1):
            while node.forward[level] is not None and node.forward[level].key < key:
                node = node.forward[level]
            update[level] = node
        return update

    def get(self, key, default=None):
        node = self._predecessors(key)[0].forward[0]
        return node.value if node is not None and node.key == key else default

    def __contains__(self, key):
        node = self._predecessors(key)[0].forward[0]
        return node is not None and node.key == key

    def put(self, key, value):
        update = self._predecessors(key)
        node = update[0].forward[0]
        if node is not None and node.key == key:
            node.value = value
            return
        levels = self._random_levels()
        self._levels = max(self._levels, levels)      # update[] already holds the head on new levels
        node = _SkipNode(key, value, levels)
        for level in range(levels):
            node.forward[level] = update[level].forward[level]
            update[level].forward[level] = node
        self._size += 1

    def delete(self, key):
        update = self._predecessors(key)
        node = update[0].forward[0]
        if node is None or node.key != key:
            return False
        for level in range(len(node.forward)):
            update[level].forward[level] = node.forward[level]
        while self._levels > 1 and self._head.forward[self._levels - 1] is None:
            self._levels -= 1
        self._size -= 1
        return True


class Bitset:
    """Membership for the integers 0..n-1 in n bits: bit i lives in byte i // 8 at position i % 8."""

    def __init__(self, n):
        self.n = n
        self._bytes = bytearray((n + 7) // 8)

    def _check(self, i):
        if not 0 <= i < self.n:
            raise IndexError(f"bit {i} out of range")

    def add(self, i):
        self._check(i)
        self._bytes[i >> 3] |= 1 << (i & 7)

    def discard(self, i):
        self._check(i)
        self._bytes[i >> 3] &= ~(1 << (i & 7))

    def __contains__(self, i):
        return 0 <= i < self.n and (self._bytes[i >> 3] >> (i & 7)) & 1 == 1

    def __len__(self):
        return int.from_bytes(self._bytes, "little").bit_count()     # population count (Python 3.10+)

    def __iter__(self):
        for index, byte in enumerate(self._bytes):
            while byte:
                low = byte & -byte                    # the lowest set bit
                yield 8 * index + low.bit_length() - 1
                byte ^= low


# ------------------------------------------------------------------------------------ 39e.6 stacks, queues


class _Node:
    __slots__ = ("value", "next")

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


class LinkedStack:
    """LIFO on a singly linked list: push and pop at the head, O(1) worst case."""

    def __init__(self):
        self._top = None
        self._size = 0

    def __len__(self):
        return self._size

    def push(self, value):
        self._top = _Node(value, self._top)
        self._size += 1

    def pop(self):
        if self._top is None:
            raise IndexError("pop from an empty stack")
        value, self._top = self._top.value, self._top.next
        self._size -= 1
        return value

    def peek(self):
        if self._top is None:
            raise IndexError("peek at an empty stack")
        return self._top.value


class LinkedQueue:
    """FIFO on a singly linked list: enqueue at the tail, dequeue at the head, O(1) worst case."""

    def __init__(self):
        self._dummy = _Node(None)         # sentinel before the first item, so the empty case is not special
        self._tail = self._dummy
        self._size = 0

    def __len__(self):
        return self._size

    def enqueue(self, value):
        self._tail.next = _Node(value)
        self._tail = self._tail.next
        self._size += 1

    def dequeue(self):
        first = self._dummy.next
        if first is None:
            raise IndexError("dequeue from an empty queue")
        self._dummy.next = first.next
        if first is self._tail:           # removed the last item: the tail falls back to the sentinel
            self._tail = self._dummy
        self._size -= 1
        return first.value

    def peek(self):
        if self._dummy.next is None:
            raise IndexError("peek at an empty queue")
        return self._dummy.next.value


# ------------------------------------------------------------------------------------ 39e.7 hash tables


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


class HashSet:
    """A set is a hash map whose values carry no information."""

    def __init__(self, items=()):
        self._map = LinearProbingHashMap()
        for item in items:
            self.add(item)

    def __len__(self):
        return len(self._map)

    def __iter__(self):
        return iter(self._map)

    def __contains__(self, item):
        return item in self._map

    def add(self, item):
        self._map.put(item, True)

    def discard(self, item):
        self._map.delete(item)


def dict_probe_order(h, size):
    """The slots CPython's dict tries for hash h in an index table of `size` slots (a power of two)."""
    mask = size - 1
    perturb = h & 0xFFFFFFFFFFFFFFFF          # the hash as an unsigned 64-bit number
    i = perturb & mask
    while True:
        yield i
        perturb >>= 5                         # PERTURB_SHIFT: the high bits enter the early probes
        i = (5 * i + perturb + 1) & mask      # once perturb is 0, this visits every slot


_FREE, _DUMMY = -1, -2      # index-table markers: never used, and deleted (probes continue past it)


class CompactDict:
    """A model of CPython's dict: a sparse table of small indices over a dense, insertion-ordered entry list."""

    def __init__(self):
        self._indices = [_FREE] * 8          # PyDict_MINSIZE slots, always a power of two
        self._entries = []                   # [hash, key, value] in insertion order; None once deleted
        self._used = 0                       # live keys
        self._usable = 5                     # appends left before a resize: 2/3 of the slots, minus entries

    def __len__(self):
        return self._used

    def __iter__(self):
        for entry in self._entries:
            if entry is not None:
                yield entry[1]

    def _probe(self, h):
        return dict_probe_order(h, len(self._indices))

    def _lookup(self, key, h):
        """(slot, entry index) of key, or (slot, -1) once a never-used slot proves it absent."""
        for slot in self._probe(h):
            ix = self._indices[slot]
            if ix == _FREE:
                return slot, -1
            if ix >= 0:
                entry_hash, entry_key, _ = self._entries[ix]
                if entry_key is key or (entry_hash == h and entry_key == key):
                    return slot, ix

    def __getitem__(self, key):
        _, ix = self._lookup(key, hash(key))
        if ix < 0:
            raise KeyError(key)
        return self._entries[ix][2]

    def __contains__(self, key):
        return self._lookup(key, hash(key))[1] >= 0

    def __setitem__(self, key, value):
        h = hash(key)
        _, ix = self._lookup(key, h)
        if ix >= 0:
            self._entries[ix][2] = value     # an update keeps the key's place in the order
            return
        if self._usable == 0:
            self._resize(3 * self._used)     # GROWTH_RATE: used * 3, rounded up to a power of two
        for slot in self._probe(h):
            if self._indices[slot] < 0:      # free or dummy: either can take the new index
                break
        self._indices[slot] = len(self._entries)
        self._entries.append([h, key, value])
        self._used += 1
        self._usable -= 1

    def __delitem__(self, key):
        slot, ix = self._lookup(key, hash(key))
        if ix < 0:
            raise KeyError(key)
        self._indices[slot] = _DUMMY         # later keys may have probed past this slot
        self._entries[ix] = None             # a hole: the order of the other entries is untouched
        self._used -= 1

    def _resize(self, minimum):
        size = 8
        while size < minimum:
            size *= 2
        self._entries = [e for e in self._entries if e is not None]     # compaction removes the holes
        self._indices = [_FREE] * size
        for ix, entry in enumerate(self._entries):
            for slot in self._probe(entry[0]):
                if self._indices[slot] == _FREE:
                    break
            self._indices[slot] = ix
        self._usable = 2 * size // 3 - len(self._entries)


# ------------------------------------------------------------------------------------ 39e.8 variations


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


# ------------------------------------------------------------------------------------ 39e.9 binary trees


class TreeNode:
    __slots__ = ("val", "left", "right")

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build_tree(values):
    """LeetCode's level-order notation, e.g. [3, 9, 20, None, None, 15, 7], to a tree."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue, i = deque([root]), 1
    while queue and i < len(values):
        node = queue.popleft()
        for side in ("left", "right"):
            if i < len(values) and values[i] is not None:
                child = TreeNode(values[i])
                setattr(node, side, child)
                queue.append(child)
            i += 1
    return root


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


class NaryNode:
    __slots__ = ("val", "children")

    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []


def nary_orders(root):
    """Preorder and postorder of an n-ary tree: the binary walk with a loop over the children."""
    pre, post = [], []

    def walk(node):
        pre.append(node.val)
        for child in node.children:
            walk(child)
        post.append(node.val)

    if root:
        walk(root)
    return pre, post


def nary_levels(root):
    """Level order of an n-ary tree (LC 429)."""
    levels, queue = [], deque([root] if root else [])
    while queue:
        levels.append([])
        for _ in range(len(queue)):
            node = queue.popleft()
            levels[-1].append(node.val)
            queue.extend(node.children)
    return levels


# ------------------------------------------------------------------------------------ 39e.10 tree variations


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


_MISSING = object()


class AVLTree:
    """Sorted map kept balanced by rotations: sibling subtree heights differ by at most one."""

    def __init__(self):
        self.root = None
        self._size = 0

    def __len__(self):
        return self._size

    def height(self):
        return _height(self.root)

    def put(self, key, value):
        self.root = self._put(self.root, key, value)

    def _put(self, node, key, value):
        if node is None:
            self._size += 1
            return _AVLNode(key, value)
        if key < node.key:
            node.left = self._put(node.left, key, value)
        elif node.key < key:
            node.right = self._put(node.right, key, value)
        else:
            node.value = value
            return node
        return rebalance(node)            # postorder: repair heights on the way back up

    def delete(self, key):
        size = self._size
        self.root = self._delete(self.root, key)
        return self._size < size

    def _delete(self, node, key):
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif node.key < key:
            node.right = self._delete(node.right, key)
        elif node.left is None or node.right is None:
            self._size -= 1
            return node.left or node.right
        else:                             # two children: take the successor's entry, delete the successor
            successor = node.right
            while successor.left:
                successor = successor.left
            node.key, node.value = successor.key, successor.value
            node.right = self._delete(node.right, successor.key)
        return rebalance(node)

    def get(self, key, default=None):
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif node.key < key:
                node = node.right
            else:
                return node.value
        return default

    def __contains__(self, key):
        return self.get(key, _MISSING) is not _MISSING

    def floor(self, key):
        """Largest stored key <= key, or None: what a hash map cannot answer."""
        node, best = self.root, None
        while node:
            if key < node.key:
                node = node.left
            else:
                best, node = node.key, node.right
        return best

    def ceiling(self, key):
        node, best = self.root, None
        while node:
            if node.key < key:
                node = node.right
            else:
                best, node = node.key, node.left
        return best

    def keys(self):
        """Inorder traversal with an explicit stack: the keys in sorted order."""
        out, stack, node = [], [], self.root
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            out.append(node.key)
            node = node.right
        return out


class _TrieNode:
    __slots__ = ("children", "is_key")

    def __init__(self):
        self.children = {}
        self.is_key = False


class Trie:
    """Set of strings stored along shared prefixes: cost depends on the word's length, not on how many words."""

    def __init__(self):
        self.root = _TrieNode()
        self._size = 0

    def __len__(self):
        return self._size

    def _find(self, prefix):
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, _TrieNode())
        if not node.is_key:
            node.is_key = True
            self._size += 1

    def search(self, word):
        node = self._find(word)
        return node is not None and node.is_key

    def starts_with(self, prefix):
        node = self._find(prefix)         # deletion prunes dead branches, so only the root can be bare
        return node is not None and (node.is_key or bool(node.children))

    def keys_with_prefix(self, prefix):
        """Stored words that start with prefix, in sorted order: a preorder walk of the prefix's subtree."""
        out, node = [], self._find(prefix)

        def collect(node, path):
            if node.is_key:
                out.append("".join(path))         # preorder: a word comes before its extensions
            for ch in sorted(node.children):
                path.append(ch)
                collect(node.children[ch], path)
                path.pop()

        if node is not None:
            collect(node, list(prefix))
        return out

    def longest_prefix_of(self, query):
        """The longest stored word that is a prefix of query (longest-prefix match), or None."""
        node, best = self.root, ("" if self.root.is_key else None)
        for i, ch in enumerate(query):
            node = node.children.get(ch)
            if node is None:
                break
            if node.is_key:
                best = query[:i + 1]
        return best

    def delete(self, word):
        """Unmark word, then prune nodes that no longer lead to any word, from the bottom up."""
        path = [self.root]
        for ch in word:
            node = path[-1].children.get(ch)
            if node is None:
                return False
            path.append(node)
        if not path[-1].is_key:
            return False
        path[-1].is_key = False
        self._size -= 1
        for i in range(len(word), 0, -1):         # children before parents: a postorder by hand
            if path[i].is_key or path[i].children:
                break
            del path[i - 1].children[word[i - 1]]
        return True


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


# ------------------------------------------------------------------------------------ 39e.11 graphs


def adjacency_list(n, edges, directed=False):
    """Nodes 0..n-1 and (u, v) pairs -> graph[u] = neighbors of u. O(V + E) space."""
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        if not directed:
            graph[v].append(u)
    return graph


def adjacency_matrix(n, edges, directed=False):
    """matrix[u][v] is True when u -> v exists: O(1) edge test, O(V²) space, O(V) to list neighbors."""
    matrix = [[False] * n for _ in range(n)]
    for u, v in edges:
        matrix[u][v] = True
        if not directed:
            matrix[v][u] = True
    return matrix


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


# ------------------------------------------------------------------------------------ 39e.12 sorting


def selection_sort(a):
    """Grow a sorted prefix by swapping in the minimum of the rest: n(n - 1)/2 comparisons, n - 1 swaps."""
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            if a[j] < a[m]:
                m = j
        a[i], a[m] = a[m], a[i]           # a[i] may leap past items equal to it: not stable


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


def insertion_sort(a):
    """Insert each item into the sorted prefix by shifting larger ones right. O(n + inversions), stable."""
    for i in range(1, len(a)):
        x, j = a[i], i
        while j > 0 and x < a[j - 1]:
            a[j] = a[j - 1]
            j -= 1
        a[j] = x


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


def count_inversions(a):
    """Pairs i < j with a[i] > a[j], counted while merge sorting a copy. O(n log n)."""
    a = list(a)
    buffer = a.copy()

    def sort(lo, hi):
        if hi - lo <= 1:
            return 0
        mid = (lo + hi) // 2
        count = sort(lo, mid) + sort(mid, hi)
        buffer[lo:hi] = a[lo:hi]
        i, j = lo, mid
        for k in range(lo, hi):
            if j == hi or (i < mid and not buffer[j] < buffer[i]):
                a[k] = buffer[i]
                i += 1
            else:
                a[k] = buffer[j]
                j += 1
                count += mid - i          # buffer[j] jumps ahead of every left item still waiting
        return count

    return sort(0, len(a))


def heap_sort(a):
    """Build a max-heap in place, then swap the max to the end and shrink the heap: O(n log n), O(1) space."""
    heapify(a, operator.gt)
    for end in range(len(a) - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(a, 0, end, operator.gt)


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
