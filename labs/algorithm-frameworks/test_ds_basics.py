"""Tests for ds_basics.py: fixed examples plus randomized comparison against Python built-ins or brute force.

Run:  python3 -B test_ds_basics.py      (standard library only; fixed seed; prints one line per group)
"""
import bisect
import heapq
import itertools
import math
import operator
import random
import sys
from collections import OrderedDict, deque

import ds_basics as D

sys.dont_write_bytecode = True
rng = random.Random(3905)


def check(name, fn):
    rng.seed(f"39e-{name}")               # each group gets its own reproducible stream
    detail = fn()
    print(f"ok  {name}" + (f": {detail}" if detail else ""))


def expect(exc, fn, *args):
    try:
        fn(*args)
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__} from {getattr(fn, '__name__', fn)}{args}")


class Tagged(int):
    """An int carrying a tag: compares by value only, so a sort's stability shows in the order of the tags."""

    def __new__(cls, value, tag):
        obj = super().__new__(cls, value)
        obj.tag = tag
        return obj


class Counted:
    """Wraps a value and counts calls to <, the only comparison the sorts use."""
    calls = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        Counted.calls += 1
        return self.v < other.v


class BadKey:
    """Equal by name, but every instance has the same hash: one long collision cluster."""
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, BadKey) and self.name == other.name

    def __hash__(self):
        return 42

    def __repr__(self):
        return f"BadKey({self.name!r})"


# ----------------------------------------------------------------------------- 39e.1 and 39e.2


def t_enumeration():
    assert D.max_subarray_linear([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6         # LC 53 example
    assert D.max_subarray_cubic([-3, -1, -2]) == D.max_subarray_linear([-3, -1, -2]) == -1
    for _ in range(400):
        nums = [rng.randint(-10, 10) for _ in range(rng.randint(1, 12))]
        ref = max(sum(nums[i:j]) for i in range(len(nums)) for j in range(i + 1, len(nums) + 1))
        assert D.max_subarray_cubic(nums) == D.max_subarray_quadratic(nums) == D.max_subarray_linear(nums) == ref
    return "400 random arrays: the three enumerations agree with brute force"


def t_dynamic_array():
    arr = D.DynamicArray()
    for i in range(1000):
        arr.append(i)
    assert list(arr) == list(range(1000)) and arr.capacity() == 1024
    assert arr.moves == 1023                                  # 1 + 2 + 4 + ... + 512 < 2n
    for i in range(1000, 1024):
        arr.append(i)
    assert arr.capacity() == 1024 and arr.moves == 1023       # full now
    for _ in range(10000):                                    # alternate at the boundary: no thrashing
        arr.append(0)
        arr.pop()
    assert arr.moves == 1023 + 1024 and arr.capacity() == 2048  # one growth to 2048, then nothing
    total_ops = worst = 0
    for _ in range(300):
        arr, ref, ops = D.DynamicArray(rng.choice([1, 2, 5])), [], 0
        start_moves = arr.moves
        for _ in range(rng.randint(1, 150)):
            ops += 1
            r = rng.random()
            if r < 0.45:
                x = rng.randint(0, 99)
                arr.append(x)
                ref.append(x)
            elif r < 0.6:
                i, x = rng.randint(0, len(ref)), rng.randint(0, 99)
                arr.insert(i, x)
                ref.insert(i, x)
            elif r < 0.8 and ref:
                i = rng.randrange(len(ref))
                assert arr.delete(i) == ref.pop(i)
            elif r < 0.9 and ref:
                assert arr.pop() == ref.pop()
            elif ref:
                i, x = rng.randrange(len(ref)), rng.randint(0, 99)
                arr.set(i, x)
                ref[i] = x
                assert arr.get(i) == x
            assert list(arr) == ref and len(arr) == len(ref) <= arr.capacity()
        total_ops += ops
        worst = max(worst, (arr.moves - start_moves) / ops)
        assert arr.moves - start_moves <= 2 * ops               # amortized: at most 2 copies per operation
        expect(IndexError, arr.get, len(ref))
        expect(IndexError, arr.set, -1, 0)
        expect(IndexError, arr.insert, len(ref) + 1, 0)
        expect(IndexError, arr.delete, len(ref))
    expect(IndexError, D.DynamicArray().pop)
    return f"300 random sequences ({total_ops} ops) match list; copies per op at most {worst:.2f} (bound 2)"


def t_list_growth():
    formula = D.cpython_list_growth(3000)
    assert formula[:9] == [4, 8, 16, 24, 32, 40, 52, 64, 76]
    if sys.implementation.name == "cpython" and sys.version_info >= (3, 9):
        assert formula == D.measured_list_growth(3000)
        return f"list_resize formula matches sys.getsizeof for 3000 appends ({len(formula)} resizes)"
    return "formula only (not CPython 3.9+)"


# ----------------------------------------------------------------------------- 39e.4


def t_doubly_linked_list():
    total = 0
    for _ in range(300):
        dll, ref, handles, fresh = D.DoublyLinkedList(), [], {}, itertools.count()
        for _ in range(rng.randint(1, 80)):
            total += 1
            r = rng.random()
            if r < 0.2:
                v = next(fresh)
                handles[v] = dll.append(v)
                ref.append(v)
            elif r < 0.35:
                v = next(fresh)
                handles[v] = dll.appendleft(v)
                ref.insert(0, v)
            elif r < 0.5:
                v, i = next(fresh), rng.randint(0, len(ref))
                handles[v] = dll.insert(i, v)
                ref.insert(i, v)
            elif r < 0.6 and ref:
                v = dll.pop()
                assert v == ref.pop()
                del handles[v]
            elif r < 0.7 and ref:
                v = dll.popleft()
                assert v == ref.pop(0)
                del handles[v]
            elif r < 0.78 and ref:
                i = rng.randrange(len(ref))
                v = dll.delete(i)
                assert v == ref.pop(i)
                del handles[v]
            elif r < 0.86 and ref:
                v = rng.choice(ref)
                assert dll.remove_node(handles.pop(v)) == v
                ref.remove(v)
            elif r < 0.93 and ref:
                v = rng.choice(ref)
                dll.move_to_end(handles[v])
                ref.remove(v)
                ref.append(v)
            elif ref:
                i = rng.randrange(len(ref))
                assert dll.get(i) == ref[i]
                v = next(fresh)
                handles[v] = handles.pop(ref[i])
                dll.set(i, v)
                ref[i] = v
            assert list(dll) == ref and list(reversed(dll)) == ref[::-1] and len(dll) == len(ref)
        expect(IndexError, dll.get, len(ref))
        expect(IndexError, dll.insert, len(ref) + 1, 0)
    empty = D.DoublyLinkedList()
    expect(IndexError, empty.pop)
    expect(IndexError, empty.popleft)
    assert list(D.DoublyLinkedList("abc")) == ["a", "b", "c"]
    return f"300 random sequences ({total} ops) match list, forward and backward, with O(1) handles"


# ----------------------------------------------------------------------------- 39e.5


def t_ring_buffer():
    ops = 0
    for mode in ("error", "overwrite", "grow"):
        for _ in range(150):
            cap = rng.randint(1, 6)
            rb = D.RingBuffer(cap, when_full=mode)
            ref = deque(maxlen=cap) if mode == "overwrite" else deque()
            for _ in range(80):
                ops += 1
                op = rng.choice(("push_back", "push_front", "pop_back", "pop_front", "get"))
                if op.startswith("push"):
                    x = rng.randint(0, 99)
                    if mode == "error" and len(ref) == cap:
                        expect(OverflowError, getattr(rb, op), x)
                        continue
                    getattr(rb, op)(x)
                    (ref.append if op == "push_back" else ref.appendleft)(x)
                elif op.startswith("pop"):
                    if not ref:
                        expect(IndexError, getattr(rb, op))
                        continue
                    assert getattr(rb, op)() == (ref.pop() if op == "pop_back" else ref.popleft())
                elif ref:
                    i = rng.randrange(len(ref))
                    assert rb.get(i) == ref[i]
                assert list(rb) == list(ref) and len(rb) == len(ref)
                if mode == "grow":
                    capacity = len(rb._data)
                    assert len(ref) <= capacity and (capacity == 1 or len(ref) > capacity // 4 or capacity <= cap)
    expect(ValueError, D.RingBuffer, 0)
    return f"error, overwrite and grow modes match deque / deque(maxlen) over {ops} operations"


def t_skip_list():
    total = 0
    for trial in range(120):
        sl, ref = D.SkipList(seed=trial), {}
        for _ in range(200):
            total += 1
            k = rng.randint(-30, 30)
            r = rng.random()
            if r < 0.5:
                v = rng.randint(0, 999)
                sl.put(k, v)
                ref[k] = v
            elif r < 0.8:
                assert sl.delete(k) == (k in ref)
                ref.pop(k, None)
            else:
                assert sl.get(k) == ref.get(k) and (k in sl) == (k in ref)
            assert len(sl) == len(ref)
        assert list(sl) == sorted(ref)
    sl = D.SkipList(seed=7)
    keys = list(range(20000))
    rng.shuffle(keys)
    for k in keys:
        sl.put(k, k)
    levels = []
    node = sl._head.forward[0]
    while node:
        levels.append(len(node.forward))
        node = node.forward[0]
    mean = sum(levels) / len(levels)
    assert 1.9 < mean < 2.1 and max(levels) <= 30 and list(sl) == list(range(20000))
    return f"120 random sequences ({total} ops) match dict + sorted; 20,000 keys: mean tower {mean:.3f}, " \
           f"tallest {max(levels)} (log2 n = {math.log2(20000):.1f})"


def t_bitset():
    for _ in range(200):
        n = rng.randint(1, 100)
        bs, ref = D.Bitset(n), set()
        for _ in range(100):
            i = rng.randrange(n)
            if rng.random() < 0.6:
                bs.add(i)
                ref.add(i)
            else:
                bs.discard(i)
                ref.discard(i)
            assert (i in bs) == (i in ref) and len(bs) == len(ref)
        assert list(bs) == sorted(ref)
        assert -1 not in bs and n not in bs
        expect(IndexError, bs.add, n)
    return "200 random bitsets match set (membership, count, sorted iteration)"


# ----------------------------------------------------------------------------- 39e.6


def t_stacks_and_queues():
    for _ in range(200):
        st, ref = D.LinkedStack(), []
        q, qref = D.LinkedQueue(), deque()
        ring = D.RingBuffer(1, when_full="grow")
        for _ in range(100):
            x = rng.randint(0, 99)
            if rng.random() < 0.55:
                st.push(x)
                ref.append(x)
                q.enqueue(x)
                ring.push_back(x)
                qref.append(x)
            else:
                if ref:
                    assert st.peek() == ref[-1] and st.pop() == ref.pop()
                else:
                    expect(IndexError, st.pop)
                if qref:
                    assert q.peek() == qref[0] and q.dequeue() == qref[0] == ring.pop_front()
                    qref.popleft()
                else:
                    expect(IndexError, q.dequeue)
            assert len(st) == len(ref) and len(q) == len(qref) == len(ring)
    return "200 random sequences: LinkedStack matches list, LinkedQueue and RingBuffer(grow) match deque"


# ----------------------------------------------------------------------------- 39e.7


def key_pool():
    ints = [rng.randint(-50, 50) for _ in range(15)] + [k << 20 for k in range(8)] + [2 ** 70 + 1]
    strs = ["".join(rng.choice("abc") for _ in range(rng.randint(0, 3))) for _ in range(10)]
    tups = [(rng.randint(0, 2), rng.choice("xy")) for _ in range(6)]
    bad = [BadKey(name) for name in "pqrstuvw"]
    return ints + strs + tups + bad


def exercise_map(m, steps, keys, invariant=None):
    ref = {}
    for _ in range(steps):
        key = rng.choice(keys)
        r = rng.random()
        if r < 0.5:
            value = rng.randint(0, 999)
            m.put(key, value)
            ref[key] = value
        elif r < 0.8:
            assert m.delete(key) == (key in ref)
            ref.pop(key, None)
        else:
            assert m.get(key) == ref.get(key) and (key in m) == (key in ref)
        assert len(m) == len(ref)
        if invariant:
            invariant(m)
    keys_seen = list(m)
    assert len(keys_seen) == len(ref) and set(keys_seen) == set(ref)
    return ref


def t_chained_hash_map():
    total = 0
    for _ in range(150):
        steps = rng.randint(1, 300)
        total += steps
        exercise_map(D.ChainedHashMap(), steps, key_pool())
    m = D.ChainedHashMap()
    for i in range(1000):
        m.put(i, i)
    longest = max(len(b) for b in m._buckets)
    assert len(m._buckets) == 2048 and longest <= 8
    for i in range(1000):
        assert m.delete(i)
    assert len(m._buckets) == 8                                # shrank back
    return f"150 random sequences ({total} ops, ints, strings, tuples, all-colliding keys) match dict; " \
           f"keys 0..999 fill 2048 slots with chains of at most {longest}"


def lp_invariants(m):
    keys, mask = m._keys, len(m._keys) - 1
    assert 2 * m._used <= len(keys)
    assert sum(k is not D._EMPTY for k in keys) == m._used
    assert sum(k is not D._EMPTY and k is not D._DELETED for k in keys) == m._size
    if m.deletion == "shift":
        assert all(k is not D._DELETED for k in keys)
    for j, k in enumerate(keys):                               # no empty slot between a key's home and the key
        if k is D._EMPTY or k is D._DELETED:
            continue
        i = D._slot(k, m._bits)
        while i != j:
            assert keys[i] is not D._EMPTY
            i = (i + 1) & mask


def t_linear_probing():
    total = 0
    for deletion in ("shift", "tombstone"):
        for _ in range(150):
            steps = rng.randint(1, 300)
            total += steps
            exercise_map(D.LinearProbingHashMap(deletion=deletion), steps, key_pool(), lp_invariants)
    m = D.LinearProbingHashMap(deletion="tombstone")
    for i in range(6):                                         # churn: tombstones pile up, then a rehash clears them
        m.put(i, i)
    for round_ in range(200):
        m.delete(round_ % 6)
        m.put(round_ % 6, round_)
        lp_invariants(m)
    assert sum(k is D._DELETED for k in m._keys) <= len(m._keys) // 2
    return f"shift and tombstone deletion: 300 random sequences ({total} ops) match dict, cluster invariant holds"


def compact_invariants(d):
    assert d._usable >= 0 and d._usable == 2 * len(d._indices) // 3 - len(d._entries)
    live = [i for i, e in enumerate(d._entries) if e is not None]
    assert len(live) == d._used
    assert sorted(ix for ix in d._indices if ix >= 0) == live


def t_compact_dict():
    total = 0
    for _ in range(200):
        d, ref = D.CompactDict(), {}
        keys = key_pool()
        for _ in range(rng.randint(1, 300)):
            total += 1
            key = rng.choice(keys)
            r = rng.random()
            if r < 0.55:
                value = rng.randint(0, 999)
                d[key] = value
                ref[key] = value
            elif r < 0.8:
                if key in ref:
                    del d[key]
                    del ref[key]
                else:
                    expect(KeyError, d.__delitem__, key)
            else:
                assert (key in d) == (key in ref)
                if key in ref:
                    assert d[key] == ref[key]
                else:
                    expect(KeyError, d.__getitem__, key)
            compact_invariants(d)
            assert list(d) == list(ref) and len(d) == len(ref)        # same insertion order as dict
    for size in (8, 64, 1024):                                 # the probe order reaches every slot
        for h in (0, 1, -1, 2 ** 63 - 1, hash("abc"), rng.getrandbits(64)):
            assert set(itertools.islice(D.dict_probe_order(h, size), 20 * size)) == set(range(size))
    sizes, d = [], D.CompactDict()
    for i in range(100):
        d[i] = i
        if not sizes or len(d._indices) != sizes[-1]:
            sizes.append(len(d._indices))
    assert sizes == [8, 16, 32, 64, 128, 256]
    model, d = [], D.CompactDict()
    for i in range(200):
        before = len(d._indices)
        d[i] = i
        if len(d._indices) != before:
            model.append(i + 1)
    assert model == [6, 11, 22, 43, 86, 171]
    detail = ""
    if sys.implementation.name == "cpython" and sys.version_info >= (3, 7):
        real, real_dict, last = [], {}, sys.getsizeof({})
        for i in range(200):
            real_dict[i] = i
            if sys.getsizeof(real_dict) != last:
                real.append(i + 1)
                last = sys.getsizeof(real_dict)
        assert [p for p in real if p > 1] == model                # p == 1: the first table allocation
        detail = ", the same insertions where a real dict grows"
    return f"200 random sequences ({total} ops) match dict, including iteration order; " \
           f"resizes at insertions {model}{detail}"


def t_hash_set_and_keys():
    for _ in range(100):
        hs, ref = D.HashSet(), set()
        for _ in range(100):
            x = rng.randint(0, 30)
            if rng.random() < 0.6:
                hs.add(x)
                ref.add(x)
            else:
                hs.discard(x)
                ref.discard(x)
            assert (x in hs) == (x in ref) and len(hs) == len(ref)
        assert set(hs) == ref

    class MutableKey:
        def __init__(self, items):
            self.items = list(items)

        def __eq__(self, other):
            return self.items == other.items

        def __hash__(self):
            return hash(tuple(self.items))

    lost = 0
    for n in range(50):                                       # mutate a key after storing it
        key = MutableKey([n, n + 1])
        d = {key: "v"}
        m = D.ChainedHashMap()
        m.put(key, "v")
        key.items.append(n + 2)
        # an equal copy of the old value fails equality; an equal copy of the new value has the wrong
        # stored hash in dict. Only the same object can still match, by identity, if its new hash
        # happens to probe the old slot.
        assert MutableKey([n, n + 1]) not in d and MutableKey([n, n + 1, n + 2]) not in d and len(d) == 1
        assert MutableKey([n, n + 1]) not in m and len(m) == 1
        lost += key not in d
    modulus = sys.hash_info.modulus
    assert len({hash(7 + k * modulus) for k in range(100)}) == 1  # int hashes are not salted
    assert hash(-1) == -2                                     # -1 is reserved for errors in CPython's C API
    return f"HashSet matches set; after mutating a stored key, equal keys never find the entry, and the " \
           f"key object itself missed it in {lost} of 50 dicts"


# ----------------------------------------------------------------------------- 39e.8


def t_linked_hash_map():
    total = 0
    for access in (False, True):
        for _ in range(150):
            m, ref = D.LinkedHashMap(access_order=access), OrderedDict()
            for _ in range(rng.randint(1, 120)):
                total += 1
                k = rng.randint(0, 12)
                r = rng.random()
                if r < 0.45:
                    v = rng.randint(0, 99)
                    m.put(k, v)
                    if access and k in ref:
                        ref.move_to_end(k)
                    ref[k] = v
                elif r < 0.65:
                    assert m.delete(k) == (k in ref)
                    ref.pop(k, None)
                elif r < 0.75 and ref:
                    assert m.pop_oldest() == ref.popitem(last=False)
                else:
                    assert m.get(k) == ref.get(k)
                    if access and k in ref:
                        ref.move_to_end(k)
                assert list(m) == list(ref) and len(m) == len(ref)
    for _ in range(200):
        cap = rng.randint(1, 4)
        cache, ref = D.LRUCache(cap), OrderedDict()
        for _ in range(50):
            k = rng.randint(0, 6)
            if rng.random() < 0.5:
                expected = ref.get(k, -1)
                if k in ref:
                    ref.move_to_end(k)
                assert cache.get(k) == expected
            else:
                v = rng.randint(0, 99)
                cache.put(k, v)
                ref[k] = v
                ref.move_to_end(k)
                if len(ref) > cap:
                    ref.popitem(last=False)
    return f"insertion and access order match OrderedDict ({total} ops); LRUCache matches 200 references"


def t_array_hash_map():
    for trial in range(150):
        m, ref = D.ArrayHashMap(seed=trial), {}
        for _ in range(150):
            k = rng.randint(0, 20)
            r = rng.random()
            if r < 0.5:
                v = rng.randint(0, 99)
                m.put(k, v)
                ref[k] = v
            elif r < 0.8:
                assert m.delete(k) == (k in ref)
                ref.pop(k, None)
            else:
                assert m.get(k) == ref.get(k)
                if ref:
                    assert m.random_key() in ref
            assert len(m) == len(ref) and sorted(m._keys) == sorted(ref)
            assert all(m._keys[i] == k for k, i in m._pos.items())
    m = D.ArrayHashMap(seed=1)
    for k in range(30):
        m.put(k, k)
    for k in range(0, 30, 3):
        m.delete(k)
    draws = 40000
    counts = {}
    for _ in range(draws):
        k = m.random_key()
        counts[k] = counts.get(k, 0) + 1
    expected = draws / len(m)
    chi2 = sum((c - expected) ** 2 / expected for c in counts.values())
    assert set(counts) == set(m._keys) and chi2 < 50           # 19 degrees of freedom: 50 is far in the tail
    expect(KeyError, D.ArrayHashMap().random_key)
    return f"150 random sequences match dict; random_key uniform over 20 keys (chi-square {chi2:.1f}, 19 dof)"


def t_bloom_filter():
    assert D.bloom_parameters(1_000_000, 0.01) == (9585059, 7)
    assert D.bloom_parameters(1_000_000, 0.001) == (14377588, 10)
    n, p = 5000, 0.01
    bf = D.BloomFilter(n, p)
    members = [f"user-{i}" for i in range(n)]
    for x in members:
        bf.add(x)
    assert all(x in bf for x in members)                       # no false negatives, ever
    trials = 40000
    false_pos = sum(f"other-{i}" in bf for i in range(trials))
    rate = false_pos / trials
    predicted = (1 - math.exp(-bf.k * n / bf.m)) ** bf.k
    assert 0.5 * p < rate < 2 * p and abs(rate - predicted) < 0.004
    assert 1 not in D.BloomFilter(10, 0.01) and "1" not in D.BloomFilter(10, 0.01)
    small = D.BloomFilter(10, 0.01)
    small.add(1)
    assert 1 in small
    return f"m={bf.m} bits, k={bf.k} for n={n}, p={p}: measured false-positive rate {rate:.4f} " \
           f"(formula {predicted:.4f}); no false negatives"


# ----------------------------------------------------------------------------- 39e.9


def random_tree(n, distinct=True):
    if n == 0:
        return None
    values = rng.sample(range(1000), n) if distinct else [rng.randint(-5, 5) for _ in range(n)]
    nodes = [D.TreeNode(v) for v in values]
    for i in range(1, n):
        while True:
            parent = nodes[rng.randrange(i)]
            side = rng.choice(("left", "right"))
            if getattr(parent, side) is None:
                setattr(parent, side, nodes[i])
                break
    return nodes[0]


def ref_orders(root):
    """Iterative reference: a stack of (node, state) with state 0 = enter, 1 = between, 2 = leave."""
    pre, ino, post = [], [], []
    stack = [(root, 0)] if root else []
    while stack:
        node, state = stack.pop()
        if state == 0:
            pre.append(node.val)
            stack.append((node, 1))
            if node.left:
                stack.append((node.left, 0))
        elif state == 1:
            ino.append(node.val)
            stack.append((node, 2))
            if node.right:
                stack.append((node.right, 0))
        else:
            post.append(node.val)
    return pre, ino, post


def ref_levels(root):
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


def to_level_list(root):
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        if node:
            out.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            out.append(None)
    while out and out[-1] is None:
        out.pop()
    return out


def t_tree_traversals():
    root = D.build_tree([3, 9, 20, None, None, 15, 7])
    assert D.level_order_by_depth(root) == [[3], [9, 20], [15, 7]]
    assert D.three_orders(root) == ([3, 9, 20, 15, 7], [9, 3, 15, 20, 7], [9, 15, 7, 20, 3])
    assert D.shallowest_bfs(root, D.is_leaf) == D.shallowest_dfs(root, D.is_leaf) == 2   # LC 111 example 1
    chain = D.build_tree([2, None, 3, None, 4, None, 5, None, 6])
    assert D.shallowest_bfs(chain, D.is_leaf) == D.shallowest_dfs(chain, D.is_leaf) == 5  # LC 111 example 2
    assert D.shallowest_bfs(None, D.is_leaf) == D.shallowest_dfs(None, D.is_leaf) == 0
    for _ in range(400):
        root = random_tree(rng.randint(0, 25))
        assert D.three_orders(root) == ref_orders(root)
        levels = ref_levels(root)
        assert D.level_order_by_depth(root) == levels
        assert D.level_order(root) == [v for level in levels for v in level]
        assert to_level_list(D.build_tree(to_level_list(root))) == to_level_list(root)
        leaves = []

        def collect(node, depth, total):
            if node:
                total += node.val
                if not node.left and not node.right:
                    leaves.append((depth, total))
                collect(node.left, depth + 1, total)
                collect(node.right, depth + 1, total)

        collect(root, 1, 0)
        assert sorted(D.root_to_leaf_sums(root)) == sorted(t for _, t in leaves)
        min_leaf = min((d for d, _ in leaves), default=0)
        assert D.shallowest_bfs(root, D.is_leaf) == D.shallowest_dfs(root, D.is_leaf) == min_leaf
        nodes_at = []                                          # (depth, value) of every node, for brute force

        def gather(node, depth):
            if node:
                nodes_at.append((depth, node.val))
                gather(node.left, depth + 1)
                gather(node.right, depth + 1)

        gather(root, 1)
        k = rng.randint(2, 9)
        hit = min((d for d, v in nodes_at if v % k == 0), default=0)
        assert D.shallowest_bfs(root, lambda nd: nd.val % k == 0) == hit
        assert D.shallowest_dfs(root, lambda nd: nd.val % k == 0) == hit
        depth, size = D.depths_and_sizes(root)

        def count(node):
            return 1 + count(node.left) + count(node.right) if node else 0

        def check_depths(node, d):
            if node:
                assert depth[node] == d and size[node] == count(node)
                check_depths(node.left, d + 1)
                check_depths(node.right, d + 1)

        check_depths(root, 0)
    for _ in range(200):
        n = rng.randint(0, 20)
        nodes = [D.NaryNode(i) for i in range(n)]
        for i in range(1, n):
            nodes[rng.randrange(i)].children.append(nodes[i])
        root = nodes[0] if nodes else None
        pre, post = [], []

        def walk(node):
            pre.append(node.val)
            for c in node.children:
                walk(c)
            post.append(node.val)

        if root:
            walk(root)
        assert D.nary_orders(root) == (pre, post)
        levels, frontier = [], [root] if root else []
        while frontier:
            levels.append([x.val for x in frontier])
            frontier = [c for x in frontier for c in x.children]
        assert D.nary_levels(root) == levels
    return "400 random binary trees and 200 n-ary trees: orders, levels, shallowest match (BFS and DFS), " \
           "depth/size match references"


# ----------------------------------------------------------------------------- 39e.10


def avl_check(node):
    """Returns (height, size, keys) after asserting the AVL and BST invariants."""
    if node is None:
        return 0, 0, []
    hl, sl, kl = avl_check(node.left)
    hr, sr, kr = avl_check(node.right)
    assert abs(hl - hr) <= 1 and node.height == 1 + max(hl, hr)
    assert all(k < node.key for k in kl) and all(node.key < k for k in kr)
    return node.height, 1 + sl + sr, kl + [node.key] + kr


PHI = (1 + 5 ** 0.5) / 2


def t_avl_tree():
    total = 0
    for _ in range(150):
        t, ref = D.AVLTree(), {}
        for _ in range(rng.randint(1, 250)):
            total += 1
            k = rng.randint(0, 80)
            r = rng.random()
            if r < 0.55:
                v = rng.randint(0, 999)
                t.put(k, v)
                ref[k] = v
            elif r < 0.85:
                assert t.delete(k) == (k in ref)
                ref.pop(k, None)
            else:
                assert t.get(k) == ref.get(k) and (k in t) == (k in ref)
                keys = sorted(ref)
                i = bisect.bisect_right(keys, k)
                assert t.floor(k) == (keys[i - 1] if i else None)
                j = bisect.bisect_left(keys, k)
                assert t.ceiling(k) == (keys[j] if j < len(keys) else None)
        h, size, keys = avl_check(t.root)
        assert size == len(t) == len(ref) and keys == t.keys() == sorted(ref)
        assert h <= math.log(len(ref) + 1, PHI) + 1e-9
    t = D.AVLTree()
    for k in range(1, 4096):                                   # sorted inserts: a plain BST would be a path
        t.put(k, k)
    assert t.height() == 12 and avl_check(t.root)[1] == 4095   # 4095 = 2^12 - 1: perfectly balanced
    return f"150 random sequences ({total} ops) match dict + bisect; heights within log_φ(n + 1); " \
           f"4095 sorted inserts give height {t.height()}"


def t_trie():
    for _ in range(200):
        t, ref = D.Trie(), set()
        words = ["".join(rng.choice("abc") for _ in range(rng.randint(0, 4))) for _ in range(25)]
        for _ in range(120):
            w = rng.choice(words)
            r = rng.random()
            if r < 0.5:
                t.insert(w)
                ref.add(w)
            elif r < 0.75:
                assert t.delete(w) == (w in ref)
                ref.discard(w)
            else:
                assert t.search(w) == (w in ref)
                p = w[:rng.randint(0, len(w))]
                assert t.starts_with(p) == any(x.startswith(p) for x in ref)
                assert t.keys_with_prefix(p) == sorted(x for x in ref if x.startswith(p))
                q = w + rng.choice(["", "a", "cb"])
                matches = [x for x in ref if q.startswith(x)]
                assert t.longest_prefix_of(q) == (max(matches, key=len) if matches else None)
            assert len(t) == len(ref)

            def nodes(node):
                return 1 + sum(nodes(c) for c in node.children.values())

            prefixes = {x[:i] for x in ref for i in range(1, len(x) + 1)}
            assert nodes(t.root) == 1 + len(prefixes)              # deletion pruned every dead branch
    return "200 random sequences match a set: search, prefixes, longest prefix, delete with pruning"


def t_heap():
    for n in range(1, 400):                                     # sum of node heights = n - popcount(n) < n
        heights = sum(int(math.log2(n // (i + 1))) for i in range(n))
        assert heights == n - bin(n).count("1")
    worst = 0
    for _ in range(300):
        a = [rng.randint(-20, 20) for _ in range(rng.randint(0, 300))]
        b = a.copy()
        swaps = D.heapify(b)
        assert swaps <= len(a) - bin(len(a)).count("1") if a else swaps == 0
        worst = max(worst, swaps / max(1, len(a)))
        assert all(not b[i] < b[(i - 1) // 2] for i in range(1, len(b)))
        assert sorted(b) == sorted(a)
        c = a.copy()
        D.heapify(c, operator.gt)
        assert all(not c[i] > c[(i - 1) // 2] for i in range(1, len(c)))
    most = 0
    for n in list(range(1, 300)) + [1000, 1023, 1024, 4095]:   # at most two comparisons per level sifted
        for values in (range(n, 0, -1), [rng.random() for _ in range(n)]):
            Counted.calls = 0
            D.heapify([Counted(v) for v in values])
            assert Counted.calls <= 2 * (n - bin(n).count("1"))
            most = max(most, Counted.calls / n)
    for _ in range(200):
        h, ref = D.MinHeap([rng.randint(0, 50) for _ in range(rng.randint(0, 10))]), []
        ref = list(h._a)
        heapq.heapify(ref)
        for _ in range(100):
            if rng.random() < 0.55:
                x = rng.randint(0, 50)
                h.push(x)
                heapq.heappush(ref, x)
            elif ref:
                assert h.peek() == ref[0]
                assert h.pop() == heapq.heappop(ref)
            else:
                expect(IndexError, h.pop)
                expect(IndexError, h.peek)
            assert len(h) == len(ref)
    return f"heapify on 300 arrays: valid heaps, swaps <= n - popcount(n) (worst {worst:.2f} per item); " \
           f"comparisons <= 2(n - popcount(n)) (worst {most:.2f} per item); MinHeap matches heapq"


def t_segment_tree():
    combos = [(operator.add, 0, sum), (min, math.inf, min), (max, -math.inf, max), (math.gcd, 0, None)]
    for _ in range(200):
        n = rng.randint(1, 40)
        values = [rng.randint(-50, 50) for _ in range(n)]
        for combine, identity, ref in combos:
            vals = [abs(v) for v in values] if combine is math.gcd else values.copy()
            st = D.SegmentTree(vals, combine, identity)
            for _ in range(30):
                if rng.random() < 0.4:
                    i, x = rng.randrange(n), rng.randint(-50, 50)
                    x = abs(x) if combine is math.gcd else x
                    st.update(i, x)
                    vals[i] = x
                else:
                    lo = rng.randrange(n)
                    hi = rng.randrange(lo, n)
                    part = vals[lo:hi + 1]
                    expected = ref(part) if ref else math.gcd(*part)
                    assert st.query(lo, hi) == expected
            expect(IndexError, st.update, n, 0)
    return "200 random arrays x sum, min, max, gcd: point updates and range queries match brute force"


def t_huffman():
    clrs = {"a": 45, "b": 13, "c": 12, "d": 16, "e": 9, "f": 5}
    codes = D.huffman_codes(clrs)
    assert sum(clrs[s] * len(c) for s, c in codes.items()) == 224    # the known optimum for these counts
    assert D.huffman_codes({"x": 3}) == {"x": "0"} and D.huffman_codes({}) == {}
    for _ in range(300):
        k = rng.randint(1, 6)
        freq = {chr(97 + i): rng.randint(1, 30) for i in range(k)}
        codes = D.huffman_codes(freq)
        cost = sum(freq[s] * len(codes[s]) for s in freq)
        best = min(sum(f * l for f, l in zip(freq.values(), lengths))   # Kraft: any lengths with
                   for lengths in itertools.product(range(1, max(2, k)), repeat=k)   # sum 2^-l <= 1 are
                   if sum(2.0 ** -l for l in lengths) <= 1)                  # realizable as a prefix code
        assert cost == best
        cw = list(codes.values())
        assert not any(a != b and b.startswith(a) for a in cw for b in cw)  # prefix-free
        total = sum(freq.values())
        entropy = -sum(f / total * math.log2(f / total) for f in freq.values())
        avg = cost / total
        assert k == 1 or entropy - 1e-9 <= avg < entropy + 1
        text = [rng.choice(list(freq)) for _ in range(rng.randint(0, 40))]
        assert D.huffman_decode(D.huffman_encode(text, codes), codes) == text
    expect(ValueError, D.huffman_decode, "1", {"a": "10", "b": "11", "c": "0"})
    return "300 random alphabets: optimal (vs Kraft brute force), prefix-free, H <= L < H + 1, lossless"


# ----------------------------------------------------------------------------- 39e.11


def random_edges(n, m, allow_loops=False):
    edges = []
    for _ in range(m):
        u, v = rng.randrange(n), rng.randrange(n)
        if u == v and not allow_loops:
            continue
        edges.append((u, v))
    return edges


def ref_dfs(graph, start):
    """Iterative DFS with a stack of neighbor iterators: same order as the recursive version."""
    seen, order, stack = {start}, [start], [iter(graph[start])]
    while stack:
        for v in stack[-1]:
            if v not in seen:
                seen.add(v)
                order.append(v)
                stack.append(iter(graph[v]))
                break
        else:
            stack.pop()
    return order


def brute_paths(graph, n, s, t):
    out = []
    others = [v for v in range(n) if v not in (s, t)]
    for r in range(len(others) + 1):
        for middle in itertools.permutations(others, r):
            path = [s, *middle, t] if s != t else [s]
            if s == t and middle:
                continue
            if all(b in graph[a] for a, b in zip(path, path[1:])):
                out.append(path)
    return sorted(out)


def brute_euler(n, edges, directed):
    m = len(edges)
    if m == 0:
        return "circuit"
    result = set()

    def dfs(u, used, start, count):
        if count == m:
            result.add("circuit" if u == start else "path")
            return
        for i, (a, b) in enumerate(edges):
            if not used[i]:
                for x, y in ((a, b),) if directed else ((a, b), (b, a)):
                    if x == u:
                        used[i] = True
                        dfs(y, used, start, count + 1)
                        used[i] = False

    for s in range(n):
        dfs(s, [False] * m, s, 0)
    return "circuit" if "circuit" in result else "path" if "path" in result else None


def t_graphs():
    for _ in range(200):
        n = rng.randint(1, 8)
        directed = rng.random() < 0.5
        edges = random_edges(n, rng.randint(0, 14))
        g = D.adjacency_list(n, edges, directed)
        mat = D.adjacency_matrix(n, edges, directed)
        assert all(mat[u][v] == (v in g[u]) for u in range(n) for v in range(n))
        s = rng.randrange(n)
        assert D.dfs_order(g, s) == ref_dfs(g, s)
        dist = {s: 0}                                          # reference: relax |V| rounds
        for _ in range(n):
            for u in range(n):
                for v in g[u]:
                    if u in dist and dist[u] + 1 < dist.get(v, math.inf):
                        dist[v] = dist[u] + 1
        assert D.bfs_distances(g, s) == dist
    for _ in range(200):                                       # all simple paths, DAGs and cyclic graphs
        n = rng.randint(2, 6)
        if rng.random() < 0.5:
            edges = [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < 0.5]   # a DAG
        else:
            edges = sorted(set(random_edges(n, rng.randint(0, 12))))     # simple graph: no parallel edges
        g = D.adjacency_list(n, edges, directed=True)
        s, t = 0, n - 1
        assert sorted(D.all_paths(g, s, t)) == brute_paths(g, n, s, t)
    assert D.all_paths([[1, 2], [3], [3], []], 0, 3) == [[0, 1, 3], [0, 2, 3]]          # LC 797 example 1
    kinds = {"circuit": 0, "path": 0, None: 0}
    for _ in range(300):
        n = rng.randint(1, 5)
        directed = rng.random() < 0.5
        edges = random_edges(n, rng.randint(0, 6), allow_loops=True)
        kind = D.euler_kind(n, edges, directed)
        assert kind == brute_euler(n, edges, directed)
        kinds[kind] += 1
    bridges = [(0, 1), (0, 1), (0, 2), (0, 2), (0, 3), (1, 3), (2, 3)]                    # Königsberg
    assert D.euler_kind(4, bridges) is None
    return f"200 graphs: DFS order, BFS distances, list/matrix agree; 200 path enumerations; " \
           f"300 Euler checks vs brute force ({kinds['circuit']} circuits, {kinds['path']} paths, {kinds[None]} none)"


def t_union_find():
    for _ in range(200):
        n = rng.randint(1, 30)
        ds, edges = D.DisjointSet(n), []
        for _ in range(rng.randint(0, 40)):
            a, b = rng.randrange(n), rng.randrange(n)
            g = D.adjacency_list(n, edges)
            joined = b in D.bfs_distances(g, a)
            assert ds.union(a, b) == (not joined)
            edges.append((a, b))
            g = D.adjacency_list(n, edges)
            comps = len({min(D.bfs_distances(g, v)) for v in range(n)})
            assert ds.count == comps
            x, y = rng.randrange(n), rng.randrange(n)
            assert ds.connected(x, y) == (y in D.bfs_distances(g, x))
            root = ds.find(x)
            assert ds.parent[x] == root                        # path compression: x now points at the root
        roots = [v for v in range(n) if ds.parent[v] == v]
        assert sum(ds.size[r] for r in roots) == n
        assert all(ds.size[r] >= 2 ** max_depth(ds, r) for r in roots)
    return "200 random union sequences match BFS components; sizes and compression checked"


def max_depth(ds, root):
    depth = 0
    for v in range(len(ds.parent)):
        d, x = 0, v
        while ds.parent[x] != x:
            x, d = ds.parent[x], d + 1
        if x == root:
            depth = max(depth, d)
    return depth


# ----------------------------------------------------------------------------- 39e.12


def quick(a):
    D.quick_sort(a, rng)


SORTS = [D.selection_sort, D.bubble_sort, D.insertion_sort, D.shell_sort, quick,
         D.merge_sort, D.heap_sort, D.counting_sort, D.bucket_sort, D.radix_sort]
STABLE = {D.bubble_sort, D.insertion_sort, D.merge_sort, D.counting_sort, D.bucket_sort, D.radix_sort}
INTEGER_ONLY = {D.counting_sort, D.radix_sort}


def inputs():
    yield []
    yield [5]
    yield [2, 1]
    yield [3] * 20
    yield list(range(30))
    yield list(range(30, 0, -1))
    for _ in range(150):
        n = rng.randint(0, 60)
        yield [rng.randint(-20, 20) for _ in range(n)]
    for _ in range(50):
        yield [rng.randint(-10 ** 6, 10 ** 6) for _ in range(rng.randint(0, 60))]


def t_sorting():
    cases = list(inputs())
    floats = [[rng.random() * 100 - 50 for _ in range(rng.randint(0, 50))] for _ in range(50)]
    for sort in SORTS:
        for a in cases:
            b = a.copy()
            sort(b)
            assert b == sorted(a), (sort.__name__, a)
        if sort not in INTEGER_ONLY:
            for a in floats:
                b = a.copy()
                sort(b)
                assert b == sorted(a)
    for sort in (D.radix_sort,):
        for base in (2, 16, 256):
            for a in cases[:60]:
                b = a.copy()
                sort(b, base)
                assert b == sorted(a)
    unstable_found = {}
    for sort in SORTS:                                         # stable ones never reorder equal keys;
        for trial in range(300):                               # each unstable one fails on some input
            a = [Tagged(rng.randint(0, 4), i) for i in range(rng.randint(0, 12))]
            b = a.copy()
            sort(b)
            ok = b == sorted(a) and all(b[i].tag < b[i + 1].tag for i in range(len(b) - 1) if b[i] == b[i + 1])
            if sort in STABLE:
                assert ok, (sort.__name__, a)
            elif not ok:
                assert b == sorted(a)
                unstable_found[sort] = True
                break
    assert set(unstable_found) == set(SORTS) - STABLE
    for _ in range(100):
        a = [rng.randint(0, 30) for _ in range(rng.randint(0, 50))]
        brute = sum(a[i] > a[j] for i in range(len(a)) for j in range(i + 1, len(a)))
        assert D.count_inversions(a) == brute
    big = list(range(20000))
    for a in (big, big[::-1], [7] * 20000):
        b = a.copy()
        quick(b)
        assert b == sorted(a)
    return f"10 sorts x {len(cases)} integer inputs (+50 float inputs) match sorted(); " \
           f"stability confirmed for 6, broken examples found for the other 4; inversions match brute force"


def comparisons(sort, values):
    Counted.calls = 0
    sort([Counted(v) for v in values])
    return Counted.calls


def t_sort_costs():
    for n in (1, 10, 100):
        a = [rng.random() for _ in range(n)]
        assert comparisons(D.selection_sort, a) == n * (n - 1) // 2
        assert comparisons(D.bubble_sort, sorted(a)) == max(0, n - 1)
        assert comparisons(D.insertion_sort, sorted(a)) == max(0, n - 1)
    for _ in range(100):
        a = [rng.randint(0, 50) for _ in range(rng.randint(1, 80))]
        inv = D.count_inversions(a)
        c = comparisons(D.insertion_sort, a)
        assert inv <= c <= inv + len(a) - 1
        n = len(a)
        lg = math.ceil(math.log2(n)) if n > 1 else 0
        assert comparisons(D.merge_sort, a) <= n * lg - 2 ** lg + 1
    counts = {}
    for n in (1000, 4000, 16000):
        a = [rng.random() for _ in range(n)]
        counts[n] = comparisons(D.shell_sort, a)
    exponent = math.log(counts[16000] / counts[1000], 16)
    assert exponent < 1.5
    timsort = []
    for values in (range(100000), range(100000, 0, -1)):     # one natural run each: n - 1 comparisons
        Counted.calls = 0
        sorted(Counted(v) for v in values)
        timsort.append(Counted.calls)
    assert timsort == [99999, 99999]
    return "selection n(n-1)/2, bubble/insertion n - 1 on sorted input, insertion = inversions + O(n), " \
           f"merge within its worst-case bound; shell sort comparisons {counts} (growth n^{exponent:.2f}); " \
           f"sorted() on 100,000 sorted / reversed items: {timsort[0]} / {timsort[1]} comparisons"


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in list(globals().items()) if name.startswith("t_") and callable(fn)]
    for name, fn in tests:
        check(name[2:], fn)
    print(f"all {len(tests)} groups passed")
