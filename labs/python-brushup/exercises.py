"""Python brush-up lab (chapter 49a): 38 exercises. Replace each `raise NotImplementedError` with your code.

Check your work with:  python3 -B test_exercises.py --mine        (all exercises)
                       python3 -B test_exercises.py --mine 7 12   (only 7 and 12)
Standard library only, Python 3.11 or newer. The comment above each exercise names the chapter
section that covers it. The examples in the docstrings are the behavior the tests check; the
tests also check edge cases, so read the docstrings closely.
"""
from __future__ import annotations

import asyncio
import copy
import functools
import inspect
import math
import re
import time
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_UP, Decimal
from itertools import islice
from typing import Any, NamedTuple


# 01 (49a.2) ----------------------------------------------------------------------------------
def split_head_tail(items):
    """Return (first, middle, last) for an iterable of at least two items; middle is a list.

    Use star-unpacking. Fewer than two items raises ValueError.

    >>> split_head_tail([1, 2, 3, 4])
    (1, [2, 3], 4)
    >>> split_head_tail("ab")
    ('a', [], 'b')
    """
    raise NotImplementedError


# 02 (49a.4) ----------------------------------------------------------------------------------
def trunc_divmod(a: int, b: int) -> tuple[int, int]:
    """Division that truncates toward zero, as in C, Java and Go, with a == q * b + r.

    The remainder takes the sign of the dividend. Must stay exact for huge integers
    (do not go through float), and raise ZeroDivisionError when b == 0.

    >>> trunc_divmod(-7, 2)       # Python's divmod(-7, 2) is (-4, 1)
    (-3, -1)
    >>> trunc_divmod(7, -2)
    (-3, 1)
    """
    raise NotImplementedError


# 03 (49a.3) ----------------------------------------------------------------------------------
def sum_money(amounts: Iterable[str]) -> Decimal:
    """Add decimal strings exactly and round the total to cents, rounding halves up.

    >>> sum_money(["0.10", "0.20"])
    Decimal('0.30')
    >>> sum_money(["1.005"])     # ROUND_HALF_UP; the default would give 1.00
    Decimal('1.01')
    >>> sum_money([])
    Decimal('0.00')
    """
    raise NotImplementedError


# 04 (49a.5) ----------------------------------------------------------------------------------
DIRECTIONS = {"north", "south", "east", "west"}


def parse_command(text: str) -> tuple:
    """Parse a text-adventure command with match/case on text.split().

    "go <direction>" with a direction in DIRECTIONS -> ("move", direction)
    "go" followed by anything else (or nothing)      -> ("error", "go where?")
    "take <item> [<item> ...]"                        -> ("take", [items...])
    "quit" or "exit"                                  -> ("quit",)
    "look", or an empty or blank line                 -> ("look",)
    anything else                                     -> ("unknown", text)

    >>> parse_command("go north")
    ('move', 'north')
    >>> parse_command("take lamp key")
    ('take', ['lamp', 'key'])
    """
    raise NotImplementedError


# 05 (49a.5.3) --------------------------------------------------------------------------------
def smallest_prime_factor(n: int) -> int:
    """Return the smallest prime factor of n, or n itself when n is prime.

    Use a for loop with an else clause, testing divisors up to math.isqrt(n).
    Raise ValueError for n < 2.

    >>> smallest_prime_factor(91)
    7
    >>> smallest_prime_factor(97)
    97
    """
    raise NotImplementedError


# 06 (49a.6) ----------------------------------------------------------------------------------
def running_diffs(values) -> list:
    """Differences between consecutive values, for any iterable (no index arithmetic).

    >>> running_diffs([20, 22, 21, 25])
    [2, -1, 4]
    >>> running_diffs([5])
    []
    """
    raise NotImplementedError


# 07 (49a.6, 49a.21) --------------------------------------------------------------------------
def transpose(matrix) -> list[list]:
    """Transpose a list of rows into a list of columns; ragged rows raise ValueError.

    >>> transpose([[1, 2, 3], [4, 5, 6]])
    [[1, 4], [2, 5], [3, 6]]
    >>> transpose([])
    []
    """
    raise NotImplementedError


# 08 (49a.7) ----------------------------------------------------------------------------------
def normalize_whitespace(text: str) -> str:
    """Collapse every run of whitespace into one space and trim both ends.

    >>> normalize_whitespace("  many   spaces\\there\\n")
    'many spaces here'
    """
    raise NotImplementedError


# 09 (49a.7) ----------------------------------------------------------------------------------
def is_palindrome(text: str) -> bool:
    """True if text reads the same backwards, ignoring case (casefold) and non-alphanumerics.

    >>> is_palindrome("A man, a plan, a canal: Panama")
    True
    >>> is_palindrome("palindrome")
    False
    """
    raise NotImplementedError


# 10 (49a.7.3) --------------------------------------------------------------------------------
def format_invoice_line(item: str, qty: int, unit_price: float) -> str:
    """Format one invoice line with a single f-string.

    The item is left-aligned in 12 characters and truncated to 12; the quantity is right-aligned
    in 5; the line total (qty * unit_price) is right-aligned in 12 with a thousands separator and
    two decimals.

    >>> format_invoice_line("Widget", 3, 1250.5)
    'Widget          3    3,751.50'
    """
    raise NotImplementedError


# 11 (49a.8) ----------------------------------------------------------------------------------
def rotate(items: list, k: int) -> list:
    """Return a new list rotated right by k (negative k rotates left; k may exceed the length).

    >>> rotate([1, 2, 3, 4, 5], 2)
    [4, 5, 1, 2, 3]
    >>> rotate([1, 2, 3, 4, 5], -1)
    [2, 3, 4, 5, 1]
    """
    raise NotImplementedError


# 12 (49a.8.5) --------------------------------------------------------------------------------
def make_grid(rows: int, cols: int, fill=0) -> list[list]:
    """A rows x cols grid filled with fill, whose rows are independent lists.

    >>> grid = make_grid(2, 2)
    >>> grid[0][0] = 1
    >>> grid
    [[1, 0], [0, 0]]
    """
    raise NotImplementedError


# 13 (49a.8.4) --------------------------------------------------------------------------------
def sort_employees(records: list[dict]) -> list[dict]:
    """Return a new list sorted by team ascending, then salary descending, then name ascending.

    Each record is a dict with "name", "team" and "salary" (a number).
    """
    raise NotImplementedError


# 14 (49a.9) ----------------------------------------------------------------------------------
def run_length_encode(data: bytes) -> bytes:
    """Encode runs of equal bytes as (count, byte) pairs; a count never exceeds 255.

    Build the output in a bytearray and return bytes.

    >>> run_length_encode(b"aaab")
    b'\\x03a\\x01b'
    >>> run_length_encode(b"z" * 300)[0::2]       # counts only: 255, then 45
    b'\\xff-'
    """
    raise NotImplementedError


# 15 (49a.10) ---------------------------------------------------------------------------------
class Point:
    """Replace this class with a typing.NamedTuple called Point with float fields x and y and two methods:

    distance_to(other) -> float   the Euclidean distance (math.dist works on tuples)
    scaled(k) -> Point            a new Point with both coordinates multiplied by k

    >>> Point(3, 4).distance_to(Point(0, 0))
    5.0
    >>> Point(3, 4) == (3, 4)
    True
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError


# 16 (49a.11) ---------------------------------------------------------------------------------
def group_by(items: Iterable, key: Callable) -> dict:
    """Group items into lists by key(item), keeping first-seen key order and item order.

    Return a plain dict.

    >>> group_by(["apple", "bob", "avocado"], key=lambda w: w[0])
    {'a': ['apple', 'avocado'], 'b': ['bob']}
    """
    raise NotImplementedError


# 17 (49a.11.5) -------------------------------------------------------------------------------
def invert_mapping(mapping: Mapping) -> dict:
    """Map each value to the list of keys that had it, in the mapping's key order.

    >>> invert_mapping({"ana": "eng", "bo": "ops", "cy": "eng"})
    {'eng': ['ana', 'cy'], 'ops': ['bo']}
    """
    raise NotImplementedError


# 18 (49a.11.4, 49a.27.2) ---------------------------------------------------------------------
def top_k_words(text: str, k: int) -> list[tuple[str, int]]:
    """The k most frequent words as (word, count) pairs, most frequent first, ties alphabetical.

    Words are runs of lowercase letters and apostrophes after lowercasing the text.

    >>> top_k_words("b a c a b", 2)
    [('a', 2), ('b', 2)]
    """
    raise NotImplementedError


# 19 (49a.11) ---------------------------------------------------------------------------------
def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into a copy of base. Neither input may change, and the
    result must not share nested lists or dicts with them.

    When both sides hold a dict for a key, merge them; otherwise the override value wins.

    >>> deep_merge({"db": {"host": "h", "port": 1}}, {"db": {"port": 2}})
    {'db': {'host': 'h', 'port': 2}}
    """
    raise NotImplementedError


# 20 (49a.12) ---------------------------------------------------------------------------------
def dedupe(items: Iterable, key: Callable | None = None) -> list:
    """Remove duplicates, keeping the first occurrence and the original order.

    With key, two items are duplicates when key(item) is equal (the items may be unhashable).

    >>> dedupe(["b", "a", "b", "c", "a"])
    ['b', 'a', 'c']
    """
    raise NotImplementedError


# 21 (49a.15.4) -------------------------------------------------------------------------------
def compose(*funcs: Callable) -> Callable:
    """compose(f, g, h)(x) == f(g(h(x))); compose() returns the identity function.

    >>> compose("-".join, str.split, str.lower)("Python Brush Up")
    'python-brush-up'
    """
    raise NotImplementedError


# 22 (49a.15.5) -------------------------------------------------------------------------------
def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    """Return a function that returns start, start + step, start + 2 * step, ... on successive calls.

    Use a closure and nonlocal, not a global or a class.

    >>> c = make_counter(10, -5)
    >>> c(), c()
    (10, 5)
    """
    raise NotImplementedError


# 23 (49a.15.2) -------------------------------------------------------------------------------
def call_with_supported_kwargs(func: Callable, /, **kwargs) -> Any:
    """Call func with only the keyword arguments its signature accepts.

    If func takes **kwargs, pass everything. Use inspect.signature.

    >>> def f(a, b=2, *, c=3):
    ...     return a, b, c
    >>> call_with_supported_kwargs(f, a=1, c=4, unknown=9)
    (1, 2, 4)
    """
    raise NotImplementedError


# 24 (49a.17.11) ------------------------------------------------------------------------------
class Vector:
    """A 2-D vector. Implement:

    __init__(x, y); __repr__ -> 'Vector(3, 4)'; __eq__ (only with other Vectors) and __hash__;
    + and - between vectors; * by an int or float on either side; unary -; abs() (the length);
    bool() (False only for the zero vector); iteration (so x, y = v works); dot(other).
    Unsupported operand types must raise TypeError (return NotImplemented).

    >>> Vector(3, 4) + Vector(1, 1)
    Vector(4, 5)
    >>> 2 * Vector(3, 4), abs(Vector(3, 4))
    (Vector(6, 8), 5.0)
    """

    def __init__(self, x, y):
        raise NotImplementedError


# 25 (49a.17.5) -------------------------------------------------------------------------------
class Temperature:
    """A temperature stored in Celsius.

    celsius: a property; setting it below -273.15 raises ValueError and leaves the old value.
    fahrenheit: a property with a getter and a setter (converts, then validates via celsius).
    __repr__ -> 'Temperature(celsius=25)'.

    >>> t = Temperature(25)
    >>> t.fahrenheit
    77.0
    """

    def __init__(self, celsius: float):
        raise NotImplementedError


# 26 (49a.17.9) -------------------------------------------------------------------------------
class Stack:
    """A LIFO stack built on a list.

    Stack(items=()) starts with items (the last one on top); push(item); pop() and peek() raise
    IndexError when empty; len(); bool(); `in`; iteration goes from top to bottom;
    repr -> "Stack(['a', 'b', 'c'])" (bottom to top, like the list).
    """

    def __init__(self, items: Iterable = ()):
        raise NotImplementedError


# 27 (49a.18.3) -------------------------------------------------------------------------------
class Shape:
    """Replace with an abstract base class (abc.ABC) with abstract area() and perimeter() and a
    concrete describe() returning e.g. "Circle area=3.14" (the class name, area to 2 decimals).
    Shape() itself must raise TypeError.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError


class Rectangle(Shape):
    """Rectangle(width, height)."""


class Square(Rectangle):
    """Square(side): a Rectangle whose sides are equal (reuse Rectangle through super())."""


class Circle(Shape):
    """Circle(radius)."""


def total_area(shapes: Iterable[Shape]) -> float:
    """Sum of the areas (0 for no shapes)."""
    raise NotImplementedError


# 28 (49a.18.4) -------------------------------------------------------------------------------
class FrozenMapping:
    """An immutable, hashable mapping. Inherit from collections.abc.Mapping and implement
    __getitem__, __iter__ and __len__; Mapping supplies get, items, __contains__ and __eq__.

    FrozenMapping(*args, **kwargs) accepts what dict() accepts and copies it. Item assignment
    must fail with TypeError. Because Mapping defines __eq__, you must define __hash__ yourself.
    repr -> "FrozenMapping({'a': 1})".

    >>> FrozenMapping({"a": 1}, b=2) == {"a": 1, "b": 2}
    True
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError


# 29 (49a.19.3) -------------------------------------------------------------------------------
def flatten(nested) -> Iterator:
    """A generator that yields the leaves of nested lists and tuples (strings are leaves).

    >>> list(flatten([1, [2, [3, (4,)]], "ab"]))
    [1, 2, 3, 4, 'ab']
    """
    raise NotImplementedError


# 30 (49a.19.2) -------------------------------------------------------------------------------
def fibonacci() -> Iterator[int]:
    """An infinite generator: 0, 1, 1, 2, 3, 5, 8, ..."""
    raise NotImplementedError


def take(n: int, iterable: Iterable) -> list:
    """The first n items of any iterable (possibly infinite), as a list.

    >>> take(5, fibonacci())
    [0, 1, 1, 2, 3]
    """
    raise NotImplementedError


# 31 (49a.19.7) -------------------------------------------------------------------------------
def chunked(iterable: Iterable, size: int) -> Iterator[tuple]:
    """Lazily yield tuples of up to size items, like itertools.batched (3.12+), using islice.

    Must work on infinite iterators; size < 1 raises ValueError.

    >>> list(chunked(range(7), 3))
    [(0, 1, 2), (3, 4, 5), (6,)]
    """
    raise NotImplementedError


# 32 (49a.20.5) -------------------------------------------------------------------------------
def retry(attempts: int = 3, exceptions: tuple = (Exception,), delay: float = 0.0,
          backoff: float = 2.0, sleep: Callable[[float], Any] = time.sleep) -> Callable:
    """A decorator factory: retry the decorated function when it raises one of `exceptions`.

    Make at most `attempts` calls; between failed calls, call sleep(delay), then sleep(delay * backoff),
    and so on; after the last attempt, re-raise the exception. Other exceptions are not retried.
    Keep the function's __name__ and __doc__ (functools.wraps).

    >>> waits = []
    >>> @retry(attempts=3, exceptions=(KeyError,), delay=1, sleep=waits.append)
    ... def fails():
    ...     raise KeyError("x")
    >>> try:
    ...     fails()
    ... except KeyError:
    ...     waits
    [1, 2.0]
    """
    raise NotImplementedError


# 33 (49a.20.1) -------------------------------------------------------------------------------
def count_calls(func: Callable) -> Callable:
    """A decorator that counts calls in wrapper.calls (starting at 0) and keeps func's metadata.

    >>> @count_calls
    ... def ping():
    ...     return "pong"
    >>> ping(), ping(), ping.calls
    ('pong', 'pong', 2)
    """
    raise NotImplementedError


# 34 (49a.22.2) -------------------------------------------------------------------------------
def temporary_attr(obj, name: str, value):
    """A context manager (use contextlib.contextmanager) that sets obj.<name> = value inside the
    block and restores the old value afterward, even if the block raises. If the attribute did
    not exist before, delete it afterward. The `as` target is obj.
    """
    raise NotImplementedError


# 35 (49a.27.2) -------------------------------------------------------------------------------
def parse_log_line(line: str) -> dict | None:
    """Parse '<timestamp> <LEVEL> <service>: <message>' into a dict, or return None.

    timestamp: YYYY-MM-DDTHH:MM:SSZ; LEVEL: DEBUG, INFO, WARNING or ERROR; service: letters,
    digits, '_', '.', '-'; message: the rest (may be empty). A trailing newline is allowed.
    Use a compiled regular expression with named groups.

    >>> parse_log_line("2026-10-03T10:00:02Z ERROR billing-api: card declined")["service"]
    'billing-api'
    """
    raise NotImplementedError


# 36 (49a.23.5) -------------------------------------------------------------------------------
def validate_user(data: dict) -> dict:
    """Return {"name": <stripped name>, "age": <int>}, or raise ExceptionGroup("invalid user", errors)
    listing every problem, in this order:

    ValueError("name is required")              name missing, not a str, or blank
    TypeError("age must be an int")             age missing or not an int (a bool is not an int here)
    ValueError("age must be between 0 and 150") age outside 0..150
    """
    raise NotImplementedError


# 37 (49a.26.4) -------------------------------------------------------------------------------
async def run_with_limit(factories: list[Callable[[], Any]], limit: int) -> list:
    """Await factory() for every factory (each returns an awaitable) with at most `limit` running
    at once, and return the results in input order. Use asyncio.Semaphore and asyncio.gather.
    limit < 1 raises ValueError.
    """
    raise NotImplementedError


# 38 (49a.29.10) ------------------------------------------------------------------------------
class EventBus:
    """Observer pattern.

    subscribe(event, handler) -> a function that unsubscribes the handler (calling it twice is harmless)
    publish(event, *args, **kwargs) -> the number of handlers called; handlers run in subscription
    order, and a handler may unsubscribe itself (or another) while an event is being published.
    """

    def __init__(self):
        raise NotImplementedError
