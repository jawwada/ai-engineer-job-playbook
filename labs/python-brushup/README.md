# Python brush-up lab

Thirty-eight exercises that drill chapter 49a, *Python fundamentals and advanced idioms*. Each exercise is a function or class stub whose docstring states the behavior and gives examples; the tests check those examples plus the edge cases an interviewer would ask about, and a reference solution shows the idiom the chapter recommends.

## Purpose

Chapter 49a explains the language; this lab checks that you can produce it under time pressure without looking. The exercises are deliberately small (a few lines each) and deliberately sharp: every one has a trap that separates "I have written Python" from "I know what Python does". They cover unpacking, integer and decimal arithmetic, pattern matching, strings, lists, bytes, tuples, dicts, sets, comprehensions, closures, classes and operators, properties, the container protocol, abstract base classes, `collections.abc`, generators, decorators, context managers, regular expressions, exception groups, `asyncio` and the observer pattern. Chapter 49a.31.6 schedules them over ten days.

## Requirements

Python 3.11 or newer (exception groups and `except*` arrived in 3.11) and the standard library only. Nothing to install. The lab writes no files.

## Quick start

```bash
cd labs/python-brushup
python3 -B test_exercises.py               # the reference solutions: all 38 pass
python3 -B test_exercises.py --mine        # your answers in exercises.py
python3 -B test_exercises.py --mine 7 12   # only exercises 7 and 12
```

`-B` keeps Python from writing `__pycache__` folders. The runner prints one line per exercise, `PASS`, `FAIL` (with the exception, the line number and the source of the assertion that failed) or `TODO` (the stub still raises `NotImplementedError`), then a summary such as `38 passed, 0 failed, 0 to do (solutions.py)`. The exit code is 1 unless every selected exercise passes, so a fresh checkout gives:

```text
$ python3 -B test_exercises.py --mine 7 12
TODO  07 transpose
TODO  12 make_grid
0 passed, 0 failed, 2 to do (exercises.py)
```

## Files

| File | What it holds |
|---|---|
| `exercises.py` | 38 stubs to fill in; the comment above each names the chapter section that covers it |
| `solutions.py` | reference solutions, written the way the chapter recommends |
| `test_exercises.py` | plain-assert tests; runs against `solutions.py` by default and against `exercises.py` with `--mine` |

## The practice loop

1. Open `exercises.py` and pick an exercise. The comment above it (`# 07 (49a.6, 49a.21)`) names the chapter section; read that section, then close it.
2. Read the docstring. It states the behavior, the error cases, and gives one or two examples in `>>>` form. Those examples are real: running the docstrings of `exercises.py` against `solutions.py` with `doctest` passes all 52 of them.
3. Replace `raise NotImplementedError` with your code. Time-box it: about 10 minutes for a function, 20 for a class.
4. Run `python3 -B test_exercises.py --mine <number>`. A `FAIL` line quotes the assertion, which is usually an edge case: empty input, negative numbers, a shared mutable object, the wrong exception type. Fix and rerun.
5. When it passes, compare with `solutions.py`. Look for what the reference does differently: a built-in you did not use, a copy you forgot, a clearer name, a shorter path.
6. Keep an error log of what failed and why, and redo those exercises two days later without looking at your previous answer.
7. For interview practice, write the answer in a plain editor without running it, explain it out loud as you go, and only then run the tests.

To start an exercise over, copy its stub back from version control (`git checkout -- exercises.py` resets the whole file).

## The topics

Each group below names the exercises it contains, the idiom a senior engineer reaches for, and the trap the tests check.

### Unpacking (exercise 01, `split_head_tail`)

**Intuition.** Star-unpacking (`first, *middle, last = items`) names the parts of a sequence in one statement, works on any iterable, and raises `ValueError` by itself when the shape is wrong. It replaces index arithmetic (`items[0]`, `items[1:-1]`, `items[-1]`), which does not work on iterators and silently misbehaves on short input.

**The exercises.** `split_head_tail(items)` returns `(first, middle, last)` with `middle` a list: `split_head_tail("ab")` is `('a', [], 'b')`.

**The trap.** The test passes `range(3)` (an iterable, not a list) and `[1]`, which must raise `ValueError`. The one-line unpacking handles both; a slicing solution handles neither.

### Arithmetic and `Decimal` (02 `trunc_divmod`, 03 `sum_money`)

**Intuition.** Python's `//` and `%` floor toward negative infinity, so `divmod(-7, 2)` is `(-4, 1)`; C, Java and Go truncate toward zero and give `(-3, -1)`. Porting a hashing or calendar routine without knowing this produces off-by-one bugs on negative inputs only. For money, `float` cannot represent 0.1, and `Decimal` can, with rounding you choose explicitly.

**The exercises.** `trunc_divmod(a, b)` returns the truncating quotient and a remainder with the dividend's sign, exact for huge integers: `trunc_divmod(-7, 2)` is `(-3, -1)`. `sum_money(amounts)` adds decimal strings and rounds to cents with `ROUND_HALF_UP`: `sum_money(["1.005"])` is `Decimal('1.01')`.

**The trap.** The test calls `trunc_divmod(10**30 + 1, -1)`; any solution that goes through `float` (`int(a / b)`) loses the low digits, because `int((10**30 + 1) / -1) != -(10**30 + 1)`. For `sum_money`, `Decimal.quantize` defaults to `ROUND_HALF_EVEN`, so `Decimal("1.005").quantize(Decimal("0.01"))` is `1.00`, not `1.01`; and an empty input must give `Decimal('0.00')` whose `str` is `"0.00"`, which needs a `Decimal` start value for `sum` and a final `quantize`.

### Pattern matching and the loop `else` (04 `parse_command`, 05 `smallest_prime_factor`)

**Intuition.** `match`/`case` on `text.split()` turns a command parser into a list of shapes: literal words, captures, `*rest`, guards and `|` alternatives, read top to bottom. The `for`/`else` clause runs when the loop finishes without `break`, which is exactly "no divisor found", and saves a flag variable.

**The exercises.** `parse_command("take lamp key")` is `('take', ['lamp', 'key'])`; `"go north"` is `('move', 'north')`; `"go"` or `"go up"` is `('error', 'go where?')`; `"quit"` or `"exit"` is `('quit',)`; `"look"` or a blank line is `('look',)`; anything else is `('unknown', text)`. `smallest_prime_factor(91)` is `7`, `smallest_prime_factor(97)` is `97`, and `n < 2` raises `ValueError`.

**The trap.** `"   ".split()` is `[]`, so the blank line must match the same case as `["look"]`; and `["go", *_]` must come after the guarded `["go", direction] if direction in DIRECTIONS`, or every direction becomes an error. For the prime factor, the test uses `2**31 - 1` (a prime) and `1_000_003 * 1_000_033`, so the loop must stop at `math.isqrt(n)` rather than `n`.

### Iteration with `zip` (06 `running_diffs`, 07 `transpose`)

**Intuition.** Neighbors come from `zip(values, values[1:])`, and a transpose is `zip(*rows)`. `zip(..., strict=True)` (3.10) raises instead of silently truncating when the inputs differ in length, which is the right default for data you did not generate yourself.

**The exercises.** `running_diffs([20, 22, 21, 25])` is `[2, -1, 4]`; `transpose([[1, 2, 3], [4, 5, 6]])` is `[[1, 4], [2, 5], [3, 6]]`, and ragged rows raise `ValueError`.

**The trap.** `running_diffs(iter([1, 4, 9]))` must work, so the input has to be materialized before it is sliced. `transpose` must return lists, not the tuples `zip` yields, must give `[]` for `[]`, and must raise on `[[1, 2], [3]]`, which only `strict=True` does.

### Strings (08 `normalize_whitespace`, 09 `is_palindrome`, 10 `format_invoice_line`)

**Intuition.** `str.split()` with no argument splits on any run of whitespace and drops empties, so `" ".join(text.split())` is the whole normalizer. Case-insensitive comparison uses `casefold`, which handles German sharp s and other letters `lower` does not. Format specifications put alignment, width, truncation, grouping and precision in one place: `f"{item:<12.12}{qty:>5}{total:>12,.2f}"`.

**The exercises.** `normalize_whitespace("  many   spaces\there\n")` is `'many spaces here'`. `is_palindrome("A man, a plan, a canal: Panama")` is `True`. `format_invoice_line("Widget", 3, 1250.5)` is `'Widget          3    3,751.50'`.

**The trap.** `is_palindrome("Straße essartS")` is `True` only with `casefold` (`"ß"` becomes `"ss"`); `lower` leaves it alone and the test fails. In the format spec, `.12` after `<12` truncates a long item name, and `,` must come before `.2f`.

### Lists (11 `rotate`, 12 `make_grid`, 13 `sort_employees`)

**Intuition.** Slices make new lists, so a rotation is two slices joined; the modulo makes negative and oversized shifts fall into range. `sorted` with a tuple key sorts by several fields at once, with a negated number for descending order, and it always returns a new list. Nested lists are built with a comprehension because `[[0] * cols] * rows` repeats one reference to one inner list.

**The exercises.** `rotate([1, 2, 3, 4, 5], 2)` is `[4, 5, 1, 2, 3]` and `rotate(items, -1)` is `[2, 3, 4, 5, 1]`. `make_grid(2, 2)` gives independent rows. `sort_employees` orders by team ascending, salary descending, name ascending.

**The trap.** `rotate([], 3)` must not divide by zero, `rotate(items, 0)` must return a copy (`is not items`), and the input must be unchanged afterward. `make_grid` is tested by assigning `grid[0][0]` and checking the other rows did not change; `make_grid(2, 0)` is `[[], []]`. `sort_employees` is checked to leave the original list in its original order.

### Bytes (14 `run_length_encode`)

**Intuition.** `bytes` is immutable and iterating it yields integers, not one-byte strings; `bytearray` is its mutable twin, and the idiom for building binary output is to append to a `bytearray` and return `bytes(out)`.

**The exercises.** `run_length_encode(b"aaab")` is `b'\x03a\x01b'`; a run of 300 identical bytes becomes two pairs with counts 255 and 45.

**The trap.** A count must never exceed 255 (it would not fit in one byte, and `bytes((300, 122))` raises `ValueError`); the empty input returns `b""`; the result must be `bytes`, not `bytearray`. The test decodes its own output to check the round trip.

### Tuples (15 `Point`)

**Intuition.** `typing.NamedTuple` gives you an immutable record that is still a tuple: it compares equal to a plain tuple, unpacks, hashes, and gets field names, a `__repr__` and methods for free. `math.dist` takes any two sequences, so `distance_to` is one line.

**The exercises.** `Point(3, 4).distance_to(Point(0, 0))` is `5.0`; `Point(3, 4) == (3, 4)` is `True`; `scaled(k)` returns a new `Point`.

**The trap.** `p.x = 1` must raise `AttributeError` (the test uses `setattr`), `isinstance(p, tuple)` must hold, and `scaled` must return a `Point`, not a tuple; a hand-written class with `__slots__` fails the second check.

### Dicts (16 `group_by`, 17 `invert_mapping`, 18 `top_k_words`, 19 `deep_merge`)

**Intuition.** Grouping is `defaultdict(list)` and `append`; inverting a many-to-one mapping needs lists on the value side or keys vanish; counting is `Counter`; and merging configuration recursively means copying, because the caller will mutate the result. Dicts keep insertion order, and the tests rely on it.

**The exercises.** `group_by(["apple", "bob", "avocado"], key=lambda w: w[0])` is `{'a': ['apple', 'avocado'], 'b': ['bob']}`. `invert_mapping({"ana": "eng", "bo": "ops", "cy": "eng"})` is `{'eng': ['ana', 'cy'], 'ops': ['bo']}`. `top_k_words("b a c a b", 2)` is `[('a', 2), ('b', 2)]`. `deep_merge({"db": {"host": "h", "port": 1}}, {"db": {"port": 2}})` is `{'db': {'host': 'h', 'port': 2}}`.

**The trap.** `group_by` must return a plain `dict` (`type(...) is dict`), so convert the `defaultdict` before returning it, and the keys must appear in first-seen order. `top_k_words` ties must be alphabetical, which `Counter.most_common` does not guarantee (it keeps insertion order among equals), so sort by `(-count, word)`; the word regex is `[a-z']+` after lowercasing, so `"Don't"` is one word. `deep_merge` is tested by appending to a list inside the result and checking the input's list is untouched, which needs `copy.deepcopy` on both sides; and when the types disagree (`{"a": {"b": 1}}` against `{"a": 2}`) the override wins.

### Sets (20 `dedupe`)

**Intuition.** Order-preserving deduplication is a `seen` set plus an output list; the `key` function lets you deduplicate unhashable items (dicts, lists) by a hashable marker.

**The exercises.** `dedupe(["b", "a", "b", "c", "a"])` is `['b', 'a', 'c']`; with `key=lambda r: r["id"]`, a list of dicts keeps the first row per id.

**The trap.** `dedupe(iter([1, 1, 2]))` must work (consume once, never `len()` or index), and `dict.fromkeys` alone cannot handle a `key` function or unhashable items.

### Comprehensions and higher-order functions (21 `compose`)

**Intuition.** Functions are values: `compose(f, g, h)(x)` is `f(g(h(x)))`, applied right to left like mathematical composition, and the empty composition is the identity. `reversed(funcs)` and a loop is clearer than `functools.reduce` here.

**The exercises.** `compose("-".join, str.split, str.lower)("Python Brush Up")` is `'python-brush-up'`; `compose()(42)` is `42`.

**The trap.** `compose(lambda x: x + 1, lambda x: x * 10)(2)` must be `21`, not `30`; applying left to right is the common mistake.

### Closures (22 `make_counter`, 23 `call_with_supported_kwargs`)

**Intuition.** A closure captures variables from the enclosing function; `nonlocal` is what lets the inner function rebind one, and each call of the factory gets its own cell, so counters are independent. `inspect.signature` reads a function's parameters at run time, which is how frameworks decide which keyword arguments to pass a user callback.

**The exercises.** `c = make_counter(10, -5)` then `c(), c()` is `(10, 5)`. `call_with_supported_kwargs(f, a=1, c=4, unknown=9)` for `def f(a, b=2, *, c=3)` is `(1, 2, 4)`.

**The trap.** Two counters must not share state, and the first call must return `start` itself (the reference starts at `start - step` and increments first). For the signature exercise, a function with `**options` must receive everything, keyword-only parameters count as accepted, and `lambda: "none"` (no parameters) must still be callable.

### Classes and operators (24 `Vector`)

**Intuition.** Operator overloading is a set of special methods, and the protocol for "I do not know this type" is to return `NotImplemented` so Python can try the reflected method on the other operand and finally raise `TypeError`. Defining `__eq__` sets `__hash__` to `None`, so a class that must be a set member or dict key defines both. `__rmul__` makes `2 * v` work; `__iter__` makes `x, y = v` work.

**The exercises.** `Vector(3, 4) + Vector(1, 1)` is `Vector(4, 5)`; `2 * Vector(3, 4)` is `Vector(6, 8)`; `abs(Vector(3, 4))` is `5.0`; `v.dot(Vector(2, 1))` is `10`; `bool(Vector(0, 0))` is `False`.

**The trap.** `Vector(3, 4) == (3, 4)` must be `False`, not an exception: both sides return `NotImplemented`, and `==` then falls back to identity. `v + 1` and `v * "a"` must raise `TypeError`, which they do only if the methods return `NotImplemented` rather than raising or crashing on `other.x`. `len({V(1, 2), V(1, 2)}) == 1` needs `__hash__`.

### Properties (25 `Temperature`)

**Intuition.** A property is a computed attribute with a getter and optional setter behind plain attribute syntax, so validation can be added to a class without changing its callers. Routing `__init__` through the setter means construction is validated too, and a derived property (`fahrenheit`) delegates its setter to the stored one.

**The exercises.** `Temperature(25).fahrenheit` is `77.0`; setting `fahrenheit = 212` makes `celsius` `100.0`; values below -273.15 raise `ValueError`.

**The trap.** A failed set must leave the old value in place, so validate before assigning. `repr(Temperature(0))` must be `'Temperature(celsius=0)'` (use `!r` on the stored value, not a float format). The test uses `inspect.getattr_static` to confirm `fahrenheit` really is a `property` on the class, not an attribute computed once in `__init__`.

### The container protocol (26 `Stack`)

**Intuition.** `__len__`, `__bool__`, `__contains__`, `__iter__` and `__repr__` make a class feel built in: `len(s)`, `if s:`, `x in s`, `for x in s`. The choice of what iteration means is a design decision; a stack iterates from the top.

**The exercises.** After pushing `"a"`, `"b"`, `"c"`: `list(s)` is `['c', 'b', 'a']`, `repr(s)` is `"Stack(['a', 'b', 'c'])"`, `s.peek()` is `'c'`, and `pop()` or `peek()` on an empty stack raises `IndexError`.

**The trap.** Iteration order and `repr` order are opposite (top first versus bottom first), and the empty stack must be falsy; `reversed(self._items)` is the one-line iterator.

### Abstract base classes (27 `Shape`, `Rectangle`, `Square`, `Circle`, `total_area`)

**Intuition.** `abc.ABC` with `@abstractmethod` makes "every shape has an area and a perimeter" a contract that fails at instantiation rather than at the first call. Concrete behavior (`describe`) lives in the base and uses the abstract methods, and `Square` reuses `Rectangle` through `super().__init__(side, side)`.

**The exercises.** `Shape()` raises `TypeError`; `Square(2).describe()` is `'Square area=4.00'`; `Circle(1).describe()` is `'Circle area=3.14'`; `total_area([])` is `0`.

**The trap.** `describe` must use `type(self).__name__` (so a `Square` says `Square`, not `Rectangle`) and `:.2f`; `isinstance(Square(2), Rectangle)` must hold; and `sum` of nothing is `0`, which is what the test wants.

### `collections.abc` (28 `FrozenMapping`)

**Intuition.** Inherit from `collections.abc.Mapping`, implement `__getitem__`, `__iter__` and `__len__`, and `get`, `items`, `keys`, `values`, `__contains__` and `__eq__` are supplied. This is also the safe way to build a custom dict: subclassing `dict` directly skips your overrides in its C-implemented methods.

**The exercises.** `FrozenMapping({"a": 1}, b=2) == {"a": 1, "b": 2}` is `True`; item assignment raises `TypeError`; equal mappings hash equal regardless of insertion order.

**The trap.** Because `Mapping` defines `__eq__`, it sets `__hash__` to `None`, so you must write `__hash__` yourself, and it must be order-independent (`hash(frozenset(self._data.items()))`). The constructor must copy (the test mutates the source dict afterward), and `fm["c"] = 3` must fail, which it does as long as you never define `__setitem__`.

### Generators (29 `flatten`, 30 `fibonacci` and `take`, 31 `chunked`)

**Intuition.** A generator function produces values lazily and keeps its place between calls; `yield from` delegates to a nested generator, which makes recursive flattening three lines. `itertools.islice` takes a prefix of an infinite iterator without materializing it, and the walrus with `tuple(islice(it, n))` is the 3.11 way to batch (3.12 added `itertools.batched`).

**The exercises.** `list(flatten([1, [2, [3, (4,)]], "ab"]))` is `[1, 2, 3, 4, 'ab']`; `take(5, fibonacci())` is `[0, 1, 1, 2, 3]`; `list(chunked(range(7), 3))` is `[(0, 1, 2), (3, 4, 5), (6,)]`.

**The trap.** Strings are leaves: recursing into `"ab"` recurses forever because each character is a one-character string. `flatten` must be a real generator (`inspect.isgenerator`), not a function returning a list. After `take(5, fib)`, `next(fib)` must be `5`: the generator keeps its place, and `take(0, count())` must return immediately. `chunked` is tested on `itertools.count()`, so it must never call `len` or `list` on its input, and `size < 1` raises `ValueError` only once the generator is iterated, which is why the test wraps it in `lambda: list(...)`.

### Decorators (32 `retry`, 33 `count_calls`)

**Intuition.** A decorator factory (`retry(attempts=3)`) returns a decorator that returns a wrapper; `functools.wraps` copies the name, docstring and `__wrapped__` so tooling still sees the original. Taking `sleep` as a parameter makes a backoff decorator testable without waiting: the test passes `waits.append` and inspects the list. State on a wrapper (`wrapper.calls`) is the simplest way to count calls.

**The exercises.** With `attempts=3, delay=1` and a function that always raises `KeyError`, the recorded sleeps are `[1, 2.0]` and the `KeyError` propagates. `ping(), ping(), ping.calls` is `('pong', 'pong', 2)`.

**The trap.** There are `attempts - 1` sleeps, not `attempts`; the last failure is re-raised with a bare `raise`; exceptions not in the tuple are not retried at all (the test counts exactly one call for a `ValueError`); and `flaky.__name__` and `__doc__` must survive. `count_calls` must start at `0` and expose `__wrapped__`.

### Context managers (34 `temporary_attr`)

**Intuition.** `@contextlib.contextmanager` turns a generator into a context manager: code before `yield` is `__enter__`, code after is `__exit__`, and a `try`/`finally` around the `yield` guarantees cleanup when the block raises. A sentinel object distinguishes "the attribute was absent" from "the attribute was `None`".

**The exercises.** `with temporary_attr(Settings, "debug", True) as target:` sets the attribute inside the block, restores it afterward, and `target is Settings`.

**The trap.** The attribute must be restored when the block raises (`finally`), and an attribute that did not exist before must be deleted afterward rather than set to `None`, so `getattr(obj, name, _MISSING)` with a private sentinel, then `delattr`.

### Regular expressions (35 `parse_log_line`)

**Intuition.** Compile once at module level, use named groups so the result is `match.groupdict()`, and use `fullmatch` so a line with trailing garbage is rejected rather than partially matched.

**The exercises.** `parse_log_line("2026-10-03T10:00:02Z ERROR billing-api: card declined")["service"]` is `'billing-api'`; an unknown level or an unrelated line gives `None`.

**The trap.** A trailing newline is allowed, but a message may be empty: `"... worker.7: \n"` must parse with `message == ""`. Stripping the whole line with `strip()` removes the space after the colon and the match fails; strip only `"\r\n"`.

### Exception groups (36 `validate_user`)

**Intuition.** When several independent things can go wrong, report them all at once: collect exceptions in a list and raise `ExceptionGroup(message, errors)`. The caller handles them with `except* ValueError` and `except* TypeError`, and both clauses run for one group.

**The exercises.** `validate_user({"name": "  Ana ", "age": 31})` is `{'name': 'Ana', 'age': 31}`; `{"age": "ten"}` raises a group holding `ValueError("name is required")` and `TypeError("age must be an int")`, in that order.

**The trap.** `bool` is a subclass of `int`, so `age=True` must be rejected explicitly (`isinstance(age, bool)`), and the range check must be an `elif` so a non-integer age produces one error, not two. The test uses `except*` to check that both clauses run on one group.

### `asyncio` (37 `run_with_limit`)

**Intuition.** Fan out many awaitables but cap concurrency with `asyncio.Semaphore`, and `asyncio.gather` returns results in input order no matter which finished first. Each factory is wrapped in a small coroutine that acquires the semaphore, which is the pattern for bounded parallel calls to an API.

**The exercises.** `await run_with_limit(factories, 3)` returns `[factory() results in order]`; the test's jobs record the peak number running, which must be exactly 3.

**The trap.** Awaiting each factory sequentially passes the order check but fails the peak check (it would be 1); awaiting them all without the semaphore fails it the other way (10). An empty list must return `[]`, and the solution raises `ValueError` for `limit < 1`.

### The observer pattern (38 `EventBus`)

**Intuition.** A subject notifies subscribers without knowing who they are: a dict of lists of callables, `subscribe` returns an unsubscribe function (so callers need no handle to the bus internals), and `publish` iterates over a copy because a handler may unsubscribe itself while the event is being delivered.

**The exercises.** `subscribe(event, handler)` returns a function that removes the handler; `publish(event, *args, **kwargs)` calls handlers in subscription order and returns how many were called.

**The trap.** A handler that unsubscribes itself during `publish` must not break iteration or skip the next handler (the test checks `once` runs exactly once and `"second"` still runs); calling the unsubscribe function twice must be harmless; and publishing an event with no subscribers returns `0`. Chapter 49a.29.10 shows a smaller `EventBus` with `publish(event, **payload)` and no count; the lab version adds positional arguments, the count and the idempotent unsubscribe.

## Exercise map

| # | Exercise | Chapter | Drills |
|---|---|---|---|
| 01 | `split_head_tail` | 49a.2 | star-unpacking |
| 02 | `trunc_divmod` | 49a.4 | floor versus truncating division, exact integer arithmetic |
| 03 | `sum_money` | 49a.3 | `Decimal`, `quantize`, rounding modes |
| 04 | `parse_command` | 49a.5 | `match`/`case`: sequence patterns, guards, OR patterns |
| 05 | `smallest_prime_factor` | 49a.5.3 | `for`/`else`, `math.isqrt` |
| 06 | `running_diffs` | 49a.6 | neighbors with `zip` |
| 07 | `transpose` | 49a.6, 49a.21 | `zip(*rows, strict=True)` |
| 08 | `normalize_whitespace` | 49a.7 | `split` and `join` |
| 09 | `is_palindrome` | 49a.7 | `casefold`, `isalnum`, slicing |
| 10 | `format_invoice_line` | 49a.7.3 | format specifications |
| 11 | `rotate` | 49a.8 | slicing, modulo with negatives |
| 12 | `make_grid` | 49a.8.5 | aliasing in nested lists |
| 13 | `sort_employees` | 49a.8.4 | multi-key sorts |
| 14 | `run_length_encode` | 49a.9 | `bytes` and `bytearray` |
| 15 | `Point` | 49a.10 | `typing.NamedTuple` |
| 16 | `group_by` | 49a.11 | `defaultdict` grouping |
| 17 | `invert_mapping` | 49a.11.5 | `setdefault`, many-to-one inversion |
| 18 | `top_k_words` | 49a.11.4, 49a.27.2 | `Counter`, `re.findall`, tie-breaking |
| 19 | `deep_merge` | 49a.11 | recursion, deep copies |
| 20 | `dedupe` | 49a.12 | order-preserving deduplication with a key |
| 21 | `compose` | 49a.15.4 | higher-order functions |
| 22 | `make_counter` | 49a.15.5 | closures and `nonlocal` |
| 23 | `call_with_supported_kwargs` | 49a.15.2 | `inspect.signature`, parameter kinds |
| 24 | `Vector` | 49a.17.11 | operator overloading, `NotImplemented`, `__hash__` |
| 25 | `Temperature` | 49a.17.5 | properties with validation |
| 26 | `Stack` | 49a.17.9 | the container protocol |
| 27 | `Shape`, `Rectangle`, `Square`, `Circle` | 49a.18.3 | abstract base classes, `super()` |
| 28 | `FrozenMapping` | 49a.18.4 | `collections.abc.Mapping`, hashing |
| 29 | `flatten` | 49a.19.3 | recursive generators, `yield from` |
| 30 | `fibonacci`, `take` | 49a.19.2 | infinite generators, `islice` |
| 31 | `chunked` | 49a.19.7 | the iterator protocol, lazy batching |
| 32 | `retry` | 49a.20.5 | decorator factories, backoff, testable sleeps |
| 33 | `count_calls` | 49a.20.1 | decorators with state, `functools.wraps` |
| 34 | `temporary_attr` | 49a.22.2 | `contextlib.contextmanager`, cleanup on errors |
| 35 | `parse_log_line` | 49a.27.2 | regular expressions with named groups |
| 36 | `validate_user` | 49a.23.5 | `ExceptionGroup`, collecting errors |
| 37 | `run_with_limit` | 49a.26.4 | `asyncio.gather` with a semaphore |
| 38 | `EventBus` | 49a.29.10 | the observer pattern, unsubscribing safely |

The chapter points back at the lab in four places: 49a.4.1 (`int((10**30 + 1) / -1)`, exercise 02), 49a.11.5 (inversion, exercise 17), 49a.15.4 (`compose`, exercise 21) and 49a.19.7 (`chunked`, exercise 31).

## How the tests work

`test_exercises.py` registers one function per exercise with the `@exercise(number, name)` decorator; each test receives the module under test as `m` and uses plain `assert` statements, so it reads as a specification. The `raises(exc_type, func, *args, **kwargs)` helper asserts that a call raises a given exception and returns it, but re-raises `NotImplementedError` so that an unfinished stub shows as `TODO` rather than `FAIL`. `main()` imports `solutions` or, with `--mine`, `exercises`, filters by the numbers given, and prints one line per test; for a failure it extracts the last frame of the traceback so you see the assertion's line number and source.

## How to add an exercise

1. In `exercises.py`, add a numbered comment with the chapter section (`# 39 (49a.13.1) ---`) and a stub whose docstring states the behavior, the error cases and at least one `>>>` example, ending in `raise NotImplementedError`. For a class, make `__init__` raise so the runner reports `TODO`.
2. In `solutions.py`, add the reference implementation under the same name and number, written the way the chapter section recommends.
3. In `test_exercises.py`, add a function decorated with `@exercise(39, "name")` that takes `m`, asserts the docstring examples first, then the edge cases, and uses `raises` for exceptions.
4. Run `python3 -B test_exercises.py 39` (must pass) and `python3 -B test_exercises.py --mine 39` (must print `TODO`), then add a row to the exercise map above.
5. Check that the docstring examples really run: `python3 -c "import doctest, exercises, solutions; [doctest.DocTestRunner().run(t) for t in doctest.DocTestFinder().find(exercises, globs=vars(solutions).copy()) if t.examples]"` prints nothing when every example passes.

For algorithm and data-structure practice in the style of coding rounds, continue with `labs/coding-patterns/` (chapter 39d).
