"""Reference solutions for the Python brush-up lab (chapter 49a).

Standard library only, Python 3.11 or newer. Each function or class matches the stub of the same
name in exercises.py; test_exercises.py checks both. Read a solution only after your own version
passes or after you have given it a real attempt.
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
    """Return (first, middle, last) for an iterable of at least two items; middle is a list."""
    first, *middle, last = items          # ValueError for fewer than two items
    return first, middle, last


# 02 (49a.4) ----------------------------------------------------------------------------------
def trunc_divmod(a: int, b: int) -> tuple[int, int]:
    """Division that truncates toward zero (C, Java, Go), with a == q * b + r."""
    q = abs(a) // abs(b)                  # ZeroDivisionError when b == 0
    if (a < 0) != (b < 0):
        q = -q
    return q, a - q * b


# 03 (49a.3) ----------------------------------------------------------------------------------
def sum_money(amounts: Iterable[str]) -> Decimal:
    """Add decimal strings exactly and round the total to cents, halves rounding up."""
    total = sum((Decimal(a) for a in amounts), Decimal("0"))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# 04 (49a.5) ----------------------------------------------------------------------------------
DIRECTIONS = {"north", "south", "east", "west"}


def parse_command(text: str) -> tuple:
    """Parse a text-adventure command with structural pattern matching."""
    match text.split():
        case ["go", direction] if direction in DIRECTIONS:
            return ("move", direction)
        case ["go", *_]:
            return ("error", "go where?")
        case ["take", item, *more]:
            return ("take", [item, *more])
        case ["quit"] | ["exit"]:
            return ("quit",)
        case ["look"] | []:
            return ("look",)
        case _:
            return ("unknown", text)


# 05 (49a.5.3) --------------------------------------------------------------------------------
def smallest_prime_factor(n: int) -> int:
    """Return the smallest prime factor of n (n itself when n is prime)."""
    if n < 2:
        raise ValueError("n must be at least 2")
    for d in range(2, math.isqrt(n) + 1):
        if n % d == 0:
            break
    else:
        return n                          # no divisor found: n is prime
    return d


# 06 (49a.6) ----------------------------------------------------------------------------------
def running_diffs(values) -> list:
    """Differences between consecutive values."""
    values = list(values)
    return [b - a for a, b in zip(values, values[1:])]


# 07 (49a.6, 49a.21) --------------------------------------------------------------------------
def transpose(matrix) -> list[list]:
    """Transpose a rectangular matrix given as a list of rows; ragged rows raise ValueError."""
    return [list(column) for column in zip(*matrix, strict=True)]


# 08 (49a.7) ----------------------------------------------------------------------------------
def normalize_whitespace(text: str) -> str:
    """Collapse every run of whitespace into one space and trim both ends."""
    return " ".join(text.split())


# 09 (49a.7) ----------------------------------------------------------------------------------
def is_palindrome(text: str) -> bool:
    """True if text reads the same backwards, ignoring case and non-alphanumeric characters."""
    cleaned = [ch for ch in text.casefold() if ch.isalnum()]
    return cleaned == cleaned[::-1]


# 10 (49a.7.3) --------------------------------------------------------------------------------
def format_invoice_line(item: str, qty: int, unit_price: float) -> str:
    """Item left-aligned in 12 (truncated), quantity right-aligned in 5, total right-aligned in 12."""
    total = qty * unit_price
    return f"{item:<12.12}{qty:>5}{total:>12,.2f}"


# 11 (49a.8) ----------------------------------------------------------------------------------
def rotate(items: list, k: int) -> list:
    """Rotate right by k positions (negative k rotates left); returns a new list."""
    if not items:
        return []
    k %= len(items)
    return items[-k:] + items[:-k] if k else list(items)


# 12 (49a.8.5) --------------------------------------------------------------------------------
def make_grid(rows: int, cols: int, fill=0) -> list[list]:
    """A rows x cols grid whose rows are independent lists."""
    return [[fill] * cols for _ in range(rows)]


# 13 (49a.8.4) --------------------------------------------------------------------------------
def sort_employees(records: list[dict]) -> list[dict]:
    """Sort by team ascending, then salary descending, then name ascending."""
    return sorted(records, key=lambda r: (r["team"], -r["salary"], r["name"]))


# 14 (49a.9) ----------------------------------------------------------------------------------
def run_length_encode(data: bytes) -> bytes:
    """Encode runs as (count, byte) pairs with counts from 1 to 255."""
    out = bytearray()
    i = 0
    while i < len(data):
        value = data[i]
        run = 1
        while i + run < len(data) and data[i + run] == value and run < 255:
            run += 1
        out += bytes((run, value))
        i += run
    return bytes(out)


# 15 (49a.10) ---------------------------------------------------------------------------------
class Point(NamedTuple):
    """An immutable 2-D point that is still a tuple."""
    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return math.dist(self, other)

    def scaled(self, k: float) -> Point:
        return Point(self.x * k, self.y * k)


# 16 (49a.11) ---------------------------------------------------------------------------------
def group_by(items: Iterable, key: Callable) -> dict:
    """Group items into lists by key(item), keeping first-seen key order and item order."""
    groups = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return dict(groups)


# 17 (49a.11.5) -------------------------------------------------------------------------------
def invert_mapping(mapping: Mapping) -> dict:
    """Map each value to the list of keys that had it, in the mapping's key order."""
    inverted = {}
    for key, value in mapping.items():
        inverted.setdefault(value, []).append(key)
    return inverted


# 18 (49a.11.4, 49a.27.2) ---------------------------------------------------------------------
def top_k_words(text: str, k: int) -> list[tuple[str, int]]:
    """The k most frequent lowercase words (letters and apostrophes); ties in alphabetical order."""
    counts = Counter(re.findall(r"[a-z']+", text.lower()))
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


# 19 (49a.11) ---------------------------------------------------------------------------------
def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into a copy of base; neither input is modified."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


# 20 (49a.12) ---------------------------------------------------------------------------------
def dedupe(items: Iterable, key: Callable | None = None) -> list:
    """Remove duplicates, keeping the first occurrence and the original order."""
    seen = set()
    out = []
    for item in items:
        marker = item if key is None else key(item)
        if marker not in seen:
            seen.add(marker)
            out.append(item)
    return out


# 21 (49a.15.4) -------------------------------------------------------------------------------
def compose(*funcs: Callable) -> Callable:
    """compose(f, g, h)(x) == f(g(h(x))); compose() returns the identity function."""
    def composed(x):
        for func in reversed(funcs):
            x = func(x)
        return x
    return composed


# 22 (49a.15.5) -------------------------------------------------------------------------------
def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    """Return a function that returns start, start + step, start + 2 * step, ... on each call."""
    current = start - step

    def counter():
        nonlocal current
        current += step
        return current
    return counter


# 23 (49a.15.2) -------------------------------------------------------------------------------
def call_with_supported_kwargs(func: Callable, /, **kwargs) -> Any:
    """Call func with only the keyword arguments its signature accepts (all, if it takes **kwargs)."""
    params = inspect.signature(func).parameters.values()
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params):
        return func(**kwargs)
    accepted = {p.name for p in params
                if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)}
    return func(**{k: v for k, v in kwargs.items() if k in accepted})


# 24 (49a.17.11) ------------------------------------------------------------------------------
class Vector:
    """A 2-D vector with arithmetic operators, equality, hashing, abs, truth and unpacking."""

    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector({self.x!r}, {self.y!r})"

    def __iter__(self):
        yield self.x
        yield self.y

    def __eq__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __bool__(self):
        return bool(self.x or self.y)

    def dot(self, other: Vector):
        return self.x * other.x + self.y * other.y


# 25 (49a.17.5) -------------------------------------------------------------------------------
ABSOLUTE_ZERO_C = -273.15


class Temperature:
    """A temperature stored in Celsius, validated, with a read-write Fahrenheit view."""

    def __init__(self, celsius: float):
        self.celsius = celsius            # goes through the property setter

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < ABSOLUTE_ZERO_C:
            raise ValueError("temperature below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        self.celsius = (value - 32) * 5 / 9

    def __repr__(self):
        return f"Temperature(celsius={self._celsius!r})"


# 26 (49a.17.9) -------------------------------------------------------------------------------
class Stack:
    """A LIFO stack built on a list, with the container protocol."""

    def __init__(self, items: Iterable = ()):
        self._items = list(items)

    def push(self, item) -> None:
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def __len__(self):
        return len(self._items)

    def __bool__(self):
        return bool(self._items)

    def __iter__(self) -> Iterator:
        return reversed(self._items)      # top to bottom

    def __contains__(self, item):
        return item in self._items

    def __repr__(self):
        return f"Stack({self._items!r})"


# 27 (49a.18.3) -------------------------------------------------------------------------------
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

    def describe(self) -> str:
        return f"{type(self).__name__} area={self.area():.2f}"


class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Square(Rectangle):
    def __init__(self, side: float):
        super().__init__(side, side)


class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius


def total_area(shapes: Iterable[Shape]) -> float:
    return sum(shape.area() for shape in shapes)


# 28 (49a.18.4) -------------------------------------------------------------------------------
class FrozenMapping(Mapping):
    """An immutable, hashable mapping built on collections.abc.Mapping."""

    def __init__(self, *args, **kwargs):
        self._data = dict(*args, **kwargs)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __hash__(self):                   # Mapping defines __eq__, so __hash__ must be explicit
        return hash(frozenset(self._data.items()))

    def __repr__(self):
        return f"FrozenMapping({self._data!r})"


# 29 (49a.19.3) -------------------------------------------------------------------------------
def flatten(nested) -> Iterator:
    """Yield the leaves of arbitrarily nested lists and tuples; everything else is a leaf."""
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item


# 30 (49a.19.2) -------------------------------------------------------------------------------
def fibonacci() -> Iterator[int]:
    """Yield 0, 1, 1, 2, 3, 5, ... forever."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def take(n: int, iterable: Iterable) -> list:
    """The first n items of any iterable, as a list."""
    return list(islice(iterable, n))


# 31 (49a.19.7) -------------------------------------------------------------------------------
def chunked(iterable: Iterable, size: int) -> Iterator[tuple]:
    """Yield tuples of up to size items, lazily (itertools.batched in 3.12+)."""
    if size < 1:
        raise ValueError("size must be at least 1")
    iterator = iter(iterable)
    while chunk := tuple(islice(iterator, size)):
        yield chunk


# 32 (49a.20.5) -------------------------------------------------------------------------------
def retry(attempts: int = 3, exceptions: tuple = (Exception,), delay: float = 0.0,
          backoff: float = 2.0, sleep: Callable[[float], Any] = time.sleep) -> Callable:
    """Retry the decorated function on the given exceptions, sleeping delay * backoff ** n between tries."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == attempts:
                        raise
                    sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator


# 33 (49a.20.1) -------------------------------------------------------------------------------
def count_calls(func: Callable) -> Callable:
    """Wrap func so that wrapper.calls counts the calls; keep func's metadata."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper


# 34 (49a.22.2) -------------------------------------------------------------------------------
_MISSING = object()


@contextmanager
def temporary_attr(obj, name: str, value):
    """Set obj.name to value inside the block; restore (or delete) it afterward, even on errors."""
    old = getattr(obj, name, _MISSING)
    setattr(obj, name, value)
    try:
        yield obj
    finally:
        if old is _MISSING:
            delattr(obj, name)
        else:
            setattr(obj, name, old)


# 35 (49a.27.2) -------------------------------------------------------------------------------
LOG_LINE = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) "
    r"(?P<level>DEBUG|INFO|WARNING|ERROR) "
    r"(?P<service>[\w.-]+): "
    r"(?P<message>.*)"
)


def parse_log_line(line: str) -> dict | None:
    """Parse '<timestamp> <LEVEL> <service>: <message>' into a dict, or return None."""
    match = LOG_LINE.fullmatch(line.rstrip("\r\n"))     # keep the space before an empty message
    return match.groupdict() if match else None


# 36 (49a.23.5) -------------------------------------------------------------------------------
def validate_user(data: dict) -> dict:
    """Return {'name', 'age'} cleaned, or raise ExceptionGroup with every problem found."""
    errors = []
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(ValueError("name is required"))
    age = data.get("age")
    if not isinstance(age, int) or isinstance(age, bool):
        errors.append(TypeError("age must be an int"))
    elif not 0 <= age <= 150:
        errors.append(ValueError("age must be between 0 and 150"))
    if errors:
        raise ExceptionGroup("invalid user", errors)
    return {"name": name.strip(), "age": age}


# 37 (49a.26.4) -------------------------------------------------------------------------------
async def run_with_limit(factories: list[Callable[[], Any]], limit: int) -> list:
    """Await every factory() with at most limit running at once; results in input order."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    semaphore = asyncio.Semaphore(limit)

    async def guarded(factory):
        async with semaphore:
            return await factory()

    return await asyncio.gather(*(guarded(f) for f in factories))


# 38 (49a.29.10) ------------------------------------------------------------------------------
class EventBus:
    """Publish events to subscribed handlers, in subscription order."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> Callable[[], None]:
        self._handlers[event].append(handler)

        def unsubscribe():
            if handler in self._handlers[event]:
                self._handlers[event].remove(handler)
        return unsubscribe

    def publish(self, event: str, *args, **kwargs) -> int:
        handlers = list(self._handlers.get(event, ()))   # a copy: handlers may unsubscribe
        for handler in handlers:
            handler(*args, **kwargs)
        return len(handlers)
