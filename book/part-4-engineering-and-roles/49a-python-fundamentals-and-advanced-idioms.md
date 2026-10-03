# 49a. Python fundamentals and advanced idioms: a complete brush-up for interviews and production code

> **What you need to be able to say:** how Python's object model works (names bound to objects, identity versus equality, mutability) and why it explains most surprising behavior; the operations and costs of every built-in type and collection; how functions, closures, decorators, iterators, generators and context managers work underneath; how classes, inheritance, the method resolution order, descriptors and protocols fit together; what changed from 3.8 to 3.14 and what 3.15 adds; and the classic gotchas with their fixes, each with an example small enough to type in an interview without running it.

## 49a.1 How to use this chapter, and the data model in one page

This chapter is a brush-up for engineers who already write Python and need every fundamental exact enough to explain out loud and to rely on in production. It sits underneath 49.1 (production Python) and 39d.24 (the toolkit for coding rounds): where those say "use a `deque`" or "type every boundary", this one explains what a `deque` is and what a type hint does at run time.

Every example runs. `python3 tools/run_chapter_examples.py book/part-4-engineering-and-roles/49a-python-fundamentals-and-advanced-idioms.md` executes each `python` block in a fresh namespace (results are stated with `assert`) and each `pycon` block as a doctest session; a block whose first line is `# requires: 3.12` (or 3.13, 3.14) runs with that interpreter. The examples target Python 3.11 and newer: 3.11 is the oldest release line still receiving security fixes in October 2026, 3.14 is the current feature release (3.14.8 shipped on 1 October 2026), and 3.15 is at its third release candidate, with the final release scheduled for 9 October 2026 (49a.28). Only the standard library is used. The lab in `labs/python-brushup/` has 38 exercises with tests that span the chapter.

How to read it: with an interview this week, read 49a.1, 49a.15, 49a.17 to 49a.20, 49a.30 and 49a.31, and type the examples from memory. The rest is reference: each section is self-contained, moving from intuition to mechanics and code, then costs and pitfalls.

### 49a.1.1 Names, objects, identity, type and value

A variable in Python is a name bound to an object, not a box that holds a value. Assignment binds a name; it never copies. Every object has three things:

- **Identity**: `id(obj)`, unique among objects alive at the same time and constant for the object's lifetime (in CPython, the memory address). `a is b` compares identities.
- **Type**: `type(obj)`, which decides what operations the object supports. The type never changes in normal code.
- **Value**: what `==` compares, through the type's `__eq__` method.

```pycon
>>> a = [1, 2, 3]
>>> b = a              # a second name for the same list
>>> b.append(4)
>>> a
[1, 2, 3, 4]
>>> a is b
True
>>> c = list(a)        # a new list with an equal value
>>> c == a, c is a
(True, False)
```

With an immutable object the same code behaves differently, because "changing" an immutable value creates a new object and rebinds the name:

```pycon
>>> x = 10
>>> y = x
>>> x += 1             # binds x to a new int; y still names 10
>>> x, y
(11, 10)
```

**Mutability** is a property of the type. Lists, dicts, sets, `bytearray`, `array.array`, `deque` and most user-defined instances are mutable: their value can change while their identity stays. Numbers, `bool`, `str`, `bytes`, `tuple`, `frozenset`, `range` and `None` are immutable. Among built-ins, only immutable values can be dict keys or set members (a tuple only when everything inside it is hashable), and mutability explains the aliasing bugs in 49a.30.

Function arguments follow the same rule, which is called call by sharing (or call by object reference): the parameter is a new name bound to the caller's object. Mutating the object is visible to the caller; rebinding the parameter is not.

```python
def mutate(items):
    items.append("added")      # changes the caller's list

def rebind(items):
    items = ["new list"]       # rebinds the local name only
    return items

data = ["original"]
mutate(data)
assert data == ["original", "added"]
rebind(data)
assert data == ["original", "added"]
```

### 49a.1.2 `is` versus `==`, and interning

`==` asks "are the values equal?" and can be redefined by any class. `is` asks "is this the same object?" and cannot be redefined. Use `is` for singletons only: `None`, `True` and `False` (though truthiness or `==` usually reads better for booleans), `Ellipsis`, `NotImplemented`, and sentinel objects you create yourself (49a.21).

CPython caches small integers (−5 to 256) and interns many short strings, so `is` can appear to work on values and then fail on larger or computed ones. Both are implementation details of CPython that other interpreters do not promise:

```python
import sys

big = 10 ** 6
computed = int("1000000")          # built at run time: a new object in CPython
assert big == computed
assert big is not computed         # equal values, different objects

small = 7
assert small is int("7")           # true in CPython because -5..256 are cached; never rely on it

s1 = "".join(["data", "base"])
s2 = "database"
assert s1 == s2 and s1 is not s2
assert sys.intern(s1) is sys.intern(s2)   # explicit interning returns one shared object
```

Comparing with a number or string literal using `is` (`x is 7`) is a bug, and since Python 3.8 the compiler emits a `SyntaxWarning` for it.

### 49a.1.3 Everything is an object, and syntax calls special methods

Functions, classes, modules and types are objects too: they have a type (`type(len)` is `builtin_function_or_method`, and `type(int)` and `type(type)` are both `type`), and can be stored, passed and given attributes. The *data model* is the set of special ("dunder") methods through which syntax reaches your objects: `len(x)` calls `type(x).__len__(x)`, `a + b` calls `a.__add__(b)` and falls back to `b.__radd__(a)`, `x[k]` calls `__getitem__`, `for` calls `__iter__`, `with` calls `__enter__` and `__exit__`, and `f(...)` calls `__call__`. Implicit calls look the method up on the type, not the instance:

```python
class Bag:
    def __init__(self, *items):
        self.items = list(items)

    def __len__(self):
        return len(self.items)

bag = Bag(1, 2, 3)
assert len(bag) == 3
bag.__len__ = lambda: 99          # an instance attribute, ignored by len()
assert len(bag) == 3              # special methods are looked up on the type
assert bag.__len__() == 99        # explicit attribute access does see it
```

Prefer `isinstance(x, T)` to `type(x) is T`: it accepts subclasses, and remember that `bool` is a subclass of `int`, so `isinstance(True, int)` is true.

## 49a.2 Variables, assignment and scope

### 49a.2.1 Assignment forms

Python has one assignment operator with several target shapes. The right-hand side is evaluated completely first, then the targets are assigned from left to right.

```python
a = b = []                         # chained: both names bind ONE list
a.append(1)
assert b == [1]

x, y = 1, 2
x, y = y, x                        # the right side becomes a tuple, then it is unpacked
assert (x, y) == (2, 1)

first, *rest = [10, 20, 30, 40]
*init, last = "abc"
head, *middle, tail = range(5)
assert (first, rest) == (10, [20, 30, 40])
assert (init, last) == (["a", "b"], "c")       # a starred target is always a list
assert (head, middle, tail) == (0, [1, 2, 3], 4)

(p, q), r = (1, 2), 3              # nested unpacking
assert (p, q, r) == (1, 2, 3)

for name, score in [("ana", 3), ("bo", 5)]:    # unpacking in a for target
    pass
assert (name, score) == ("bo", 5)              # loop variables survive the loop

try:
    u, v = [1, 2, 3]
except ValueError as err:
    assert "too many values to unpack" in str(err)
```

Because targets are assigned left to right, a swap whose second index depends on the first target changes meaning halfway through. This bites in cyclic sort (39d.8):

```python
nums = [2, 1]
i = 0
nums[i], nums[nums[i] - 1] = nums[nums[i] - 1], nums[i]   # nums[0] is assigned first...
assert nums == [2, 1]              # ...so the second index is computed from the new value: no swap

nums = [2, 1]
j = nums[i] - 1                    # fix: compute every index before the swap
nums[i], nums[j] = nums[j], nums[i]
assert nums == [1, 2]
```

### 49a.2.2 Augmented assignment on mutable and immutable objects

`x += y` first tries `x.__iadd__(y)`, which mutates `x` in place and returns it; if the type has no `__iadd__` it falls back to `x = x + y`, which builds a new object. Lists have `__iadd__`; tuples, strings and numbers do not. The difference shows through aliases:

```python
nums = [1, 2]
alias = nums
nums += [3]                # list.__iadd__ extends in place
assert alias == [1, 2, 3] and alias is nums

tup = (1, 2)
alias_t = tup
tup += (3,)                # no tuple.__iadd__: a new tuple is bound to tup
assert alias_t == (1, 2) and tup == (1, 2, 3)

nums += (4, 5)             # += accepts any iterable, like extend()
assert nums == [1, 2, 3, 4, 5]
try:
    nums = nums + (6,)     # + insists on another list
except TypeError:
    pass

box = ([],)
try:
    box[0] += ["x"]        # the list is extended, then the tuple item assignment fails
except TypeError:
    pass
assert box == (["x"],)     # the mutation happened anyway
```

The last case is a classic puzzle: `box[0] += ["x"]` is `box[0] = box[0].__iadd__(["x"])`; the in-place extend succeeds before the item assignment into the tuple raises.

### 49a.2.3 Scope: LEGB, `global` and `nonlocal`

A bare name is looked up in four scopes, in order: **L**ocal (the current function), **E**nclosing functions, **G**lobal (the module), **B**uilt-ins. Scope is decided at compile time: if a function assigns a name anywhere in its body (including `+=`, a `for` target, an `import` or a `def`), the name is local for the whole body. Reading it before the assignment raises `UnboundLocalError`, a subclass of `NameError`. `global name` makes assignments bind the module-level name; `nonlocal name` binds the nearest enclosing function's name.

```python
counter = 0

def broken_increment():
    counter += 1               # the assignment makes counter local, so the read fails

def increment():
    global counter
    counter += 1

try:
    broken_increment()
except UnboundLocalError:
    pass
increment()
assert counter == 1

def make_accumulator():
    total = 0
    def add(amount):
        nonlocal total         # rebind the enclosing function's variable
        total += amount
        return total
    return add

acc = make_accumulator()
acc(5)
assert acc(10) == 15

def shadow():
    len = 3                    # a local name hides the built-in, in this function only
    return len

assert shadow() == 3 and len("ab") == 2
```

A class body is a scope, but not an *enclosing* scope for the functions defined inside it: a method cannot see class attributes by bare name and must go through `self` or the class. The same rule produces a surprise with comprehensions in class bodies (49a.14).

### 49a.2.4 `del`, constants by convention, and annotated variables

`del name` removes a binding, not an object; the object is freed when nothing refers to it (49a.25). `del` also removes items (`del items[0]`, `del mapping[key]`) and attributes. Python has no constants: `UPPER_CASE` is a convention, and `typing.Final` only tells a type checker to reject reassignment. Annotations are not checked either, and an annotation without a value declares a name without binding it.

```python
import typing

MAX_RETRIES: typing.Final = 3      # a convention plus a hint for type checkers
MAX_RETRIES = 4                    # runs; mypy or pyright would report it
assert MAX_RETRIES == 4

values = [1, 2, 3]
alias = values
del values                         # removes the name, not the list
assert alias == [1, 2, 3]
try:
    values
except NameError:
    pass

def annotated():
    limit: int = "not an int"      # annotations are not enforced at run time
    pending: list[str]             # declared, never bound, and still local
    try:
        pending
    except UnboundLocalError:
        return limit

assert annotated() == "not an int"
```

## 49a.3 Built-in types and their operations

| Type | Mutable | Hashable | Literal or constructor | Notes |
|---|---|---|---|---|
| `int` | no | yes | `42`, `0x2A`, `0b101`, `1_000` | arbitrary precision |
| `float` | no | yes | `3.14`, `1e-3`, `float("inf")` | IEEE 754 double |
| `complex` | no | yes | `3 + 4j` | no ordering |
| `bool` | no | yes | `True`, `False` | subclass of `int` |
| `NoneType` | no | yes | `None` | one instance |
| `str` | no | yes | `"text"`, `'text'`, `"""text"""`, `r"\d"`, `f"{x}"` | Unicode code points |
| `bytes` | no | yes | `b"\x00\xff"` | integers 0 to 255 |
| `bytearray` | yes | no | `bytearray(b"ab")` | mutable bytes |
| `list` | yes | no | `[1, 2]` | dynamic array |
| `tuple` | no | if its items are | `(1, 2)`, `1, 2`, `(1,)` | |
| `dict` | yes | no | `{"k": 1}` | insertion-ordered hash table |
| `set` | yes | no | `{1, 2}`, `set()` | `{}` is an empty dict |
| `frozenset` | no | yes | `frozenset({1, 2})` | |
| `range` | no | yes | `range(0, 10, 2)` | lazy arithmetic sequence |

### 49a.3.1 `int`: arbitrary precision

Python integers never overflow; they grow as needed, and arithmetic on very large values just gets slower. The useful extras: `bit_length()`, `bit_count()` (3.10), literals in other bases and with underscores, `int(text, base)`, `math.isqrt` for exact integer square roots, and three-argument `pow` for modular arithmetic.

```python
import math

big = 2 ** 100
assert big == 1267650600228229401496703205376
assert big.bit_length() == 101
assert (255).bit_count() == 8                    # 3.10+
assert 0b1010 == 10 and 0o17 == 15 and 0xFF == 255 and 1_000_000 == 10**6
assert int("ff", 16) == 255 and int("0x1f", 0) == 31 and int(" 42 ") == 42
assert int(3.99) == 3 and int(-3.99) == -3      # int() truncates toward zero
assert math.floor(-3.5) == -4 and math.ceil(-3.5) == -3

n = (2 ** 53 + 1) ** 2
assert math.isqrt(n) == 2 ** 53 + 1             # exact
assert int(math.sqrt(n)) != 2 ** 53 + 1         # float square root loses the last digit

assert pow(3, 200, 1000) == pow(3, 200) % 1000  # modular power without the huge number
assert pow(3, -1, 7) == 5                        # modular inverse (3.8+): 3 * 5 % 7 == 1

try:
    int("9" * 5000)                              # str-to-int conversion is capped at 4,300 digits
except ValueError as err:
    assert "4300" in str(err)
```

The 4,300-digit cap on converting between `int` and decimal strings arrived in 3.11 (and in security releases of 3.7 to 3.10) to stop denial-of-service attacks through quadratic-time conversion; bases that are powers of two, such as `hex()`, are exempt, and `sys.set_int_max_str_digits()` raises the cap when you need to.

### 49a.3.2 `float`: IEEE 754 doubles

A float is a 64-bit binary floating-point number with about 15 to 17 significant decimal digits. Most decimal fractions, including 0.1, have no exact binary representation, so the stored value is the nearest double and small errors appear in arithmetic. Compare floats with a tolerance, use `math.fsum` when the sum must be correctly rounded, and know that `round()` rounds halves to the even neighbor (banker's rounding) and works on the exact binary value.

```python
import math

assert 0.1 + 0.2 != 0.3
assert repr(0.1 + 0.2) == "0.30000000000000004"
assert math.isclose(0.1 + 0.2, 0.3)                # rel_tol=1e-09 by default
assert not math.isclose(1e-12, 0.0)                # a relative tolerance never matches zero...
assert math.isclose(1e-12, 0.0, abs_tol=1e-9)      # ...so pass abs_tol for values near zero

assert round(0.5) == 0 and round(1.5) == 2 and round(2.5) == 2   # ties go to the even neighbor
assert round(0.285, 2) == 0.28     # the double nearest 0.285 is slightly below it
assert round(1234.5678, -2) == 1200.0 and isinstance(round(2.5), int)

nan = float("nan")
assert nan != nan and math.isnan(nan)
assert math.inf > 10 ** 308 and float("1e309") == math.inf
assert 7 / 2 == 3.5 and 6 / 3 == 2.0               # / always returns a float
assert (0.75).as_integer_ratio() == (3, 4) and (2.0).is_integer()
assert math.fsum([0.1] * 10) == 1.0                # correctly rounded sum
```

The built-in `sum` changed here: since 3.12 it uses compensated (Neumaier) summation for floats, so its results can differ from 3.11 in the last bit.

```python
import sys

total = sum([0.1] * 10)
if sys.version_info >= (3, 12):
    assert total == 1.0                    # compensated summation
else:
    assert total == 0.9999999999999999     # naive left-to-right summation
```

### 49a.3.3 `decimal.Decimal` and `fractions.Fraction`

`Decimal` is base-10 floating point with configurable precision (28 significant digits by default) and explicit rounding modes, for money and anything a human checks against a decimal calculation. Build it from strings or integers, never floats, which carry their binary error along. `quantize` rounds to a fixed exponent; the default mode is `ROUND_HALF_EVEN`, and invoices usually want `ROUND_HALF_UP`. `Fraction` is an exact rational number.

```python
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction

assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
assert Decimal(0.1) != Decimal("0.1")           # the float's binary error came along
assert Decimal("1.1") != 1.1                    # compared with the float's exact value

cents = Decimal("0.01")
amount = Decimal("2.665")
assert amount.quantize(cents) == Decimal("2.66")                         # ROUND_HALF_EVEN
assert amount.quantize(cents, rounding=ROUND_HALF_UP) == Decimal("2.67")
assert str(Decimal("1.10") * 2) == "2.20"       # trailing zeros (significance) are kept

with localcontext() as ctx:                     # precision is a property of the context
    ctx.prec = 5
    assert Decimal(1) / Decimal(7) == Decimal("0.14286")

try:
    Decimal("1.1") + 1.1                        # mixing with float is refused
except TypeError:
    pass

assert Fraction(1, 3) + Fraction(1, 6) == Fraction(1, 2)
assert Fraction("0.75") == Fraction(3, 4)
assert Fraction(0.1).denominator == 2 ** 55      # the float's exact value is a binary fraction
assert float(Fraction(1, 3)) == 1 / 3
```

### 49a.3.4 `complex`, `bool` and `None`

```python
import cmath

z = 3 + 4j
assert abs(z) == 5.0 and (z.real, z.imag) == (3.0, 4.0)
assert z.conjugate() == 3 - 4j and cmath.sqrt(-1) == 1j
try:
    z < 1j                                       # complex numbers have no ordering
except TypeError:
    pass

assert isinstance(True, int) and True + True == 2
assert sum(n > 2 for n in [1, 3, 5]) == 2        # counting with booleans; True is also the dict key 1 (49a.11.3)

def no_return():
    pass

assert no_return() is None                       # functions without return give None
assert type(None)() is None                      # NoneType has exactly one instance
```

### 49a.3.5 Text and binary data in one paragraph

`str` is an immutable sequence of Unicode code points; `bytes` is an immutable sequence of integers from 0 to 255; `bytearray` is the mutable version of `bytes`. Text becomes bytes with `encode` (UTF-8 by default) and bytes become text with `decode`. Strings get a full section (49a.7), and binary data a short one (49a.9).

### 49a.3.6 Conversions

```python
assert int("42") == 42 and float("1e3") == 1000.0 and float(" -2.5 ") == -2.5
try:
    int("3.5")                         # int() parses integer strings only
except ValueError:
    pass
assert int(float("3.5")) == 3
assert str(b"hi") == "b'hi'"           # str() of bytes is its repr, not a decoding
assert b"hi".decode() == "hi"
assert (ord("A"), chr(97)) == (65, "a")
assert (bin(10), oct(8), hex(255)) == ("0b1010", "0o10", "0xff")
assert format(255, "08b") == "11111111" and format(0.5, ".0%") == "50%"
assert list("abc") == ["a", "b", "c"] and tuple([1, 2]) == (1, 2)
assert dict([("a", 1), ("b", 2)]) == {"a": 1, "b": 2}
assert set("hello") == {"h", "e", "l", "o"}
assert bool("False") is True           # any non-empty string is truthy
```

### 49a.3.7 Truthiness

Every object has a truth value, used by `if`, `while`, `and`, `or` and `not`. False values: `None`, `False`, numeric zeros (`0`, `0.0`, `0j`, `Decimal(0)`, `Fraction(0)`), empty sequences and collections (`""`, `b""`, `()`, `[]`, `{}`, `set()`, `range(0)`), and objects whose `__bool__` returns `False` or, when there is no `__bool__`, whose `__len__` returns 0. Everything else is true, including `"0"`, `" "`, `[0]` and `float("nan")`. When 0 or an empty string is a valid value, test `x is None` instead of `if x:` (49a.4.4 shows the bug).

```python
falsy = [None, False, 0, 0.0, 0j, "", b"", (), [], {}, set(), range(0)]
assert not any(falsy)
truthy = ["0", " ", [0], (None,), float("nan"), -1, object()]
assert all(truthy)

class Inventory:
    def __init__(self, items):
        self.items = items

    def __len__(self):                 # no __bool__: truth falls back to len()
        return len(self.items)

assert not Inventory([]) and Inventory(["apple"])
```

## 49a.4 Operators

### 49a.4.1 Arithmetic, floor division and modulo with negatives

`//` is floor division: it rounds toward negative infinity, not toward zero. `%` is defined to keep the identity `a == (a // b) * b + a % b`, so the remainder takes the sign of the divisor. `divmod(a, b)` returns both. C, Java and Go truncate toward zero instead, which matters when you port code. `**` is right-associative and binds tighter than a unary minus on its left.

```python
import math

assert 7 // 2 == 3 and -7 // 2 == -4               # floor, not truncation
assert 7 % 3 == 1 and -7 % 3 == 2 and 7 % -3 == -2 # the sign follows the divisor
for a, b in [(7, 3), (-7, 3), (7, -3), (-7, -3)]:
    assert a == (a // b) * b + a % b               # the identity that defines both
assert divmod(-7, 3) == (-3, 2)
assert divmod(7.5, 2) == (3.0, 1.5)                # works on floats too

assert math.fmod(-7, 3) == -1.0                    # C semantics: the sign follows the dividend
assert int(-7 / 3) == -2                           # truncation, but through a float...
assert int((10**30 + 1) / -1) != -(10**30 + 1)     # ...which loses digits on big ints (lab exercise 02)

assert -2 ** 2 == -4 and (-2) ** 2 == 4            # ** binds tighter than unary minus
assert 2 ** 3 ** 2 == 512                          # right-associative: 2 ** 9
assert 2 ** -1 == 0.5
assert isinstance((-8) ** (1 / 3), complex)        # fractional power of a negative number

week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
assert week[(0 - 1) % 7] == "sun"                  # % wraps negative offsets cleanly
```

### 49a.4.2 Bitwise operators

`&`, `|`, `^`, `~`, `<<` and `>>` work on integers as if they were two's complement numbers with an infinite sign extension, so `~x == -x - 1` and right-shifting a negative number floors. The same operators are overloaded for sets, dict views and `enum.Flag`.

```python
assert (0b1100 & 0b1010, 0b1100 | 0b1010, 0b1100 ^ 0b1010) == (0b1000, 0b1110, 0b0110)
assert ~5 == -6                                    # ~x == -x - 1
assert 1 << 10 == 1024 and 1024 >> 3 == 128
assert -9 >> 1 == -5                               # an arithmetic shift floors

n = 0b10110
assert n & 1 == 0                                  # even
assert n & (n - 1) == 0b10100                      # clear the lowest set bit
assert n & -n == 0b10                              # isolate the lowest set bit

def is_power_of_two(x: int) -> bool:
    return x > 0 and x & (x - 1) == 0

assert [k for k in range(20) if is_power_of_two(k)] == [1, 2, 4, 8, 16]
assert 6 & 3 == 2                                  # parsed as (6 & 3) == 2, unlike C
```

### 49a.4.3 Comparisons and chaining

`a < b < c` means `a < b and b < c`, with `b` evaluated once. Chaining applies to every comparison operator, including `==`, `in` and `is`, which produces the occasional puzzle. Sequences compare lexicographically, strings by code point, and ordering between unrelated types raises `TypeError` (Python 3 has no "everything is comparable" rule).

```python
x = 5
assert 1 < x < 10 and not (1 < x > 10)
assert (False == False in [False]) is True        # (False == False) and (False in [False])
assert ((False == False) in [False]) is False     # parenthesized: True in [False]
assert 1 == 1.0 == True                           # numbers compare by value across types
assert (1, 2) < (1, 3) and [1, 2] < [1, 2, 0] and "Z" < "a"
try:
    1 < "a"
except TypeError:
    pass
```

### 49a.4.4 Boolean operators return operands

`and` and `or` short-circuit and return one of their operands, not necessarily a `bool`: `x or y` returns `x` if `x` is truthy, otherwise `y`; `x and y` returns `x` if `x` is falsy, otherwise `y`. `not` always returns a `bool`. Precedence is `not`, then `and`, then `or`, and all three bind more loosely than comparisons.

```python
assert ("" or "default") == "default"
assert ("value" or "default") == "value"
assert (0 and 1 / 0) == 0                 # short-circuit: 1 / 0 never runs
assert (None or 0 or "") == ""            # all falsy: the last operand comes back
assert (True or False and False) is True  # and binds tighter than or
assert not None is True                   # means not (None is True)

def port_or_default(port=None):
    return port or 8080                   # pitfall: port=0 is replaced too

def port_or_default_fixed(port=None):
    return 8080 if port is None else port # only "not given" gets the default

assert port_or_default(0) == 8080 and port_or_default_fixed(0) == 0
```

### 49a.4.5 The walrus operator `:=`

An assignment expression (3.8) binds a name inside an expression and returns the value. Use it when a value is needed both for a test and afterward: reading until a sentinel, a regex match, or a comprehension filter that would otherwise compute something twice. Inside a comprehension, the name binds in the enclosing scope.

```python
import re

data = [3, 8, 1, 9, 4]
if (n := len(data)) > 3:
    summary = f"{n} items"
assert summary == "5 items"

lines = iter(["alpha", "beta", "", "gamma"])
collected = []
while (line := next(lines)) != "":        # read until a blank line
    collected.append(line)
assert collected == ["alpha", "beta"]

raw = ["  a ", "   ", "b  "]
cleaned = [text for s in raw if (text := s.strip())]   # strip once, filter on the result
assert cleaned == ["a", "b"]

if match := re.search(r"(\d+) ms", "latency: 42 ms"):
    assert int(match.group(1)) == 42

squares = [last := k * k for k in range(4)]
assert squares == [0, 1, 4, 9] and last == 9           # the name leaks to the enclosing scope
```

### 49a.4.6 Conditional expressions, identity and membership

`a if condition else b` evaluates only the branch it returns. `is` and `is not` compare identity. `in` and `not in` call `__contains__`, falling back to iteration; the cost depends on the container (49a.25). For built-in containers, `x in c` is defined as "some element is `x` or equals `x`", so identity is checked first.

```python
def sign(n):
    return "negative" if n < 0 else "zero" if n == 0 else "positive"   # nesting hurts beyond one level

assert [sign(v) for v in (-2, 0, 3)] == ["negative", "zero", "positive"]
assert "ell" in "hello" and "x" not in "hello"      # substring search for str
assert 2 in {1: "a", 2: "b"} and "a" not in {1: "a"} # dict membership tests keys
assert 3 * 10**11 in range(0, 10**12, 3)            # range answers in O(1)

nan = float("nan")
assert nan in [nan]                                 # identity is checked before equality
assert nan != nan
```

### 49a.4.7 Precedence, highest first

| Operators | Meaning |
|---|---|
| `(...)`, `[...]`, `{...}` | grouping and displays |
| `x[i]`, `x[i:j]`, `f(...)`, `x.attr` | subscription, slicing, call, attribute |
| `await x` | await |
| `**` | power (right-associative; binds tighter than a unary minus on its left) |
| `+x`, `-x`, `~x` | unary plus, minus, bitwise not |
| `*`, `@`, `/`, `//`, `%` | multiplication, matrix multiplication, divisions, remainder |
| `+`, `-` | addition, subtraction |
| `<<`, `>>` | shifts |
| `&` | bitwise and |
| `^` | bitwise xor |
| `\|` | bitwise or |
| `in`, `not in`, `is`, `is not`, `<`, `<=`, `>`, `>=`, `!=`, `==` | comparisons (chainable) |
| `not x` | boolean not |
| `and` | boolean and |
| `or` | boolean or |
| `x if c else y` | conditional expression |
| `lambda` | lambda expression |
| `:=` | assignment expression |

Two consequences worth remembering: bitwise operators bind tighter than comparisons (`flags & MASK == 0` means `(flags & MASK) == 0`, the opposite of C), and `not a == b` means `not (a == b)`. When in doubt, add parentheses; readers will not have the table memorized either.

### 49a.4.8 The `operator` module

The `operator` module exposes operators as functions, which is what `sorted`, `max`, `functools.reduce` and `map` want.

```python
import operator
from functools import reduce

rows = [("ana", 31), ("bo", 25), ("cy", 31)]
assert sorted(rows, key=operator.itemgetter(1, 0)) == [("bo", 25), ("ana", 31), ("cy", 31)]
assert reduce(operator.mul, range(1, 6)) == 120
assert operator.methodcaller("upper")("abc") == "ABC"
assert operator.attrgetter("real")(3 + 4j) == 3.0
assert operator.add(2, 3) == 5 and operator.neg(4) == -4
assert list(map(operator.pow, [2, 3], [3, 2])) == [8, 9]
```

## 49a.5 Statements and control flow

### 49a.5.1 `if`, `elif`, `else`

Python has no `switch` statement. Short chains of `if`/`elif` are fine; a long chain that maps keys to actions is usually a dict of functions (a dispatch table), and a chain that inspects the *shape* of data is a `match` statement.

```python
def handle(command, *args):
    handlers = {
        "add": lambda a, b: a + b,
        "neg": lambda a: -a,
    }
    try:
        return handlers[command](*args)
    except KeyError:
        raise ValueError(f"unknown command {command!r}") from None

assert handle("add", 2, 3) == 5 and handle("neg", 4) == -4
```

### 49a.5.2 Structural pattern matching: `match` and `case`

`match` (3.10) compares a subject against patterns from top to bottom and runs the first case that matches. Unlike a switch, patterns can destructure the subject and bind names. The pattern kinds:

| Pattern | Example | Matches when |
|---|---|---|
| Literal | `case 0:`, `case "quit":`, `case None:` | equal (`None`, `True`, `False` by identity) |
| Capture | `case name:` | always; binds `name` (irrefutable) |
| Wildcard | `case _:` | always; binds nothing |
| Value | `case Level.ERROR:`, `case http.HTTPStatus.OK:` | equal; must be a dotted name |
| Sequence | `case [x, y]:`, `case [first, *rest]:` | a sequence (not `str`, `bytes` or `bytearray`) of that shape |
| Mapping | `case {"tool": name, "args": args}:` | a mapping with those keys (extra keys allowed; `**rest` collects them) |
| Class | `case Click(x=0, y=y):`, `case Click(x, y):`, `case str():` | `isinstance` plus attribute patterns; positional ones use `__match_args__` |
| OR | `case 0 \| 1:` | any alternative |
| AS | `case [x, y] as pair:` | the pattern, binding the whole subject too |
| Guard | `case [x, y] if x == y:` | the pattern and then the condition |

```python
from dataclasses import dataclass

@dataclass
class Click:
    x: int
    y: int

@dataclass
class KeyPress:
    key: str

def route(event):
    match event:
        case None:
            return "nothing"
        case 0 | 1 as bit:                                   # OR pattern with AS
            return f"bit {bit}"
        case str() as text if text.startswith("/"):          # class pattern plus guard
            return f"command {text[1:]}"
        case str():
            return "text"
        case [x, y]:                                         # any two-item sequence
            return f"pair {x},{y}"
        case [first, *rest]:
            return f"starts with {first}, {len(rest)} more"
        case {"tool": "search", "args": {"query": str(q)}}:  # patterns nest; str(q) binds the whole str
            return f"search for {q}"
        case {"tool": name, **extra}:                        # extra keys allowed; **extra collects them
            return f"{name} with {sorted(extra)}"
        case Click(0, 0):                                    # positional: dataclasses set __match_args__
            return "click at the origin"
        case Click(x=x, y=y) if x > 100:
            return f"click in the side panel at y={y}"
        case Click() | KeyPress(key="esc"):
            return "other click, or escape"
        case _:
            return "unknown"

assert route(None) == "nothing" and route(1) == "bit 1"
assert route("/help") == "command help"
assert route("hello") == "text"                              # strings are not sequence patterns
assert route((3, 4)) == "pair 3,4"                           # tuples and lists both match [x, y]
assert route([7, 8, 9]) == "starts with 7, 2 more"
assert route({"tool": "search", "args": {"query": "python"}}) == "search for python"
assert route({"tool": "fetch", "url": "u", "timeout": 5}) == "fetch with ['timeout', 'url']"
assert route(Click(0, 0)) == "click at the origin"
assert route(Click(150, 20)) == "click in the side panel at y=20"
assert route(Click(5, 5)) == route(KeyPress("esc")) == "other click, or escape"
assert route(KeyPress("a")) == "unknown" and route(3.5) == "unknown"
```

The pitfall everyone hits once: a bare name in a pattern is a capture, not a comparison with a variable. `case ERROR:` matches anything and binds it to `ERROR`; the compiler refuses such a case when other cases follow it. Use a dotted name (an enum member or a module constant) or a literal.

```python
import enum

class Level(enum.Enum):
    DEBUG = 10
    ERROR = 40

def should_page(level):
    match level:
        case Level.ERROR:        # a dotted name is a value pattern, compared with ==
            return True
        case _:
            return False

assert should_page(Level.ERROR) and not should_page(Level.DEBUG)

source = '''
ERROR = 40
def should_page(level):
    match level:
        case ERROR:              # meant as "== ERROR", but a bare name captures anything
            return True
        case _:
            return False
'''
try:
    compile(source, "<demo>", "exec")
    refused = False
except SyntaxError as err:
    refused = "makes remaining patterns unreachable" in err.msg
assert refused
```

Match on shape, not on long lists of values: commands, JSON events, tool-call payloads and trees of dataclasses are where `match` beats `if` chains.

### 49a.5.3 Loops, `break`, `continue`, `pass`, and the loop `else`

`for` iterates over any iterable; `while` repeats while a condition is true. `break` leaves the loop, `continue` skips to the next iteration, `pass` does nothing (a placeholder where a statement is required). A loop's `else` block runs when the loop ends without `break`; read it as "no break". It replaces the found-flag in search loops. Python has no do-while; write `while True:` with a `break`.

```python
def first_failure(checks):
    for name, passed in checks:
        if not passed:
            break
    else:                        # no break: every check passed
        return None
    return name

assert first_failure([("lint", True), ("tests", False), ("build", False)]) == "tests"
assert first_failure([("lint", True)]) is None

attempts = 0
while attempts < 3:
    attempts += 1
else:
    exhausted = True             # the condition became false; there was no break
assert exhausted and attempts == 3

total = 0
for n in range(10):
    if n % 2:
        continue                 # skip odd numbers
    total += n
assert total == 20
```

### 49a.5.4 `try`, `except`, `else`, `finally`

`try` runs a block; the first `except` clause whose type matches handles the exception; `else` runs only when the block raised nothing (code there is not protected, which keeps the `try` block small); `finally` always runs, whether the block returned, raised or broke out of a loop. The `except ... as err` name is deleted when the clause ends, to avoid a reference cycle through the traceback; copy what you need.

```python
events = []

def run(action):
    try:
        events.append("try")
        result = action()
    except ZeroDivisionError as err:
        events.append(f"except {type(err).__name__}")
        return "failed"
    else:
        events.append("else")          # only when the try block raised nothing
        return result
    finally:
        events.append("finally")       # always, even after a return

assert run(lambda: 42) == 42
assert events == ["try", "else", "finally"]
events.clear()
assert run(lambda: 1 / 0) == "failed"
assert events == ["try", "except ZeroDivisionError", "finally"]

try:
    int("x")
except (ValueError, TypeError) as err:  # a tuple catches several types
    message = str(err)
try:
    err                                 # the except target is unbound after the clause
except NameError:
    pass
assert "invalid literal" in message
```

Exceptions get a full section in 49a.23 (hierarchy, chaining, groups, notes and the 3.14 syntax change).

### 49a.5.5 `raise`, `raise ... from`, and `assert`

`raise SomeError("message")` raises; a bare `raise` inside an `except` block re-raises the current exception with its traceback; `raise NewError(...) from err` records the original as `__cause__`, which the traceback prints as "The above exception was the direct cause...". `assert condition, message` raises `AssertionError` when the condition is false, and is removed entirely when Python runs with `-O`, so it is for internal invariants and tests, never for validating input or enforcing security.

```python
import subprocess
import sys

def parse_port(text):
    try:
        port = int(text)
    except ValueError as err:
        raise ValueError(f"port must be a number, got {text!r}") from err
    if not 0 < port < 65536:
        raise ValueError(f"port out of range: {port}")
    return port

try:
    parse_port("http")
except ValueError as err:
    assert isinstance(err.__cause__, ValueError)     # the original error is kept

code = "assert False, 'checked'; print('assert skipped')"
plain = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
optimized = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
assert plain.returncode == 1 and "AssertionError: checked" in plain.stderr
assert optimized.returncode == 0 and optimized.stdout.strip() == "assert skipped"
```

### 49a.5.6 `with`, `import`, and `if __name__ == "__main__"`

`with` acquires a resource and guarantees its release (49a.22). Several managers fit on one line, or inside parentheses across lines (officially supported since 3.10).

`import` has four forms: `import json`, `import xml.etree.ElementTree as ET`, `from pathlib import Path`, and the discouraged `from module import *`. Inside a package, `from . import sibling` and `from .sibling import name` are relative imports. A module's code runs once per process, on first import; later imports reuse the object cached in `sys.modules` (49a.24).

Every module has a `__name__`: its import name, or `"__main__"` when it is the program being run (`python tool.py` or `python -m package.tool`). The guard `if __name__ == "__main__":` keeps script behavior out of imports: the module's top-level code still runs on import, but the guarded block runs only when the file is the program. That matters for tests, for tools that import your module, and for `multiprocessing` with the spawn and forkserver start methods, which import the main module in each child (49a.26.3).

**Interview line:** *"`match` is for destructuring shapes, not a switch on values: bare names capture, dotted names compare. Loop `else` means no break; `try`'s `else` keeps the protected block small; `finally` always runs; and `assert` disappears under -O, so it never guards input."*

## 49a.6 Loops and iteration idioms

A `for` loop asks its iterable for an iterator and calls `next()` on it until `StopIteration` (49a.19). The idioms below are how fluent Python avoids index arithmetic.

### 49a.6.1 `range`, `enumerate`, `zip`, `reversed`, `sorted`

`range` is a lazy, immutable arithmetic sequence: it supports `len`, indexing, slicing and an O(1) membership test for integers without building a list. `enumerate(iterable, start=0)` yields `(index, item)` pairs. `zip` walks several iterables in parallel and stops at the shortest, silently; `strict=True` (3.10) turns a length mismatch into a `ValueError`, and `itertools.zip_longest` pads instead. `reversed` needs a sequence (or a `__reversed__` method); `sorted` takes any iterable and returns a new list.

```python
from itertools import zip_longest

r = range(10, 0, -3)
assert list(r) == [10, 7, 4, 1] and len(r) == 4 and r[1] == 7 and r[-1] == 1
assert range(0, 20, 5)[1:3] == range(5, 15, 5)       # slicing a range gives a range

names = ["ana", "bo", "cy"]
assert list(enumerate(names, start=1)) == [(1, "ana"), (2, "bo"), (3, "cy")]

scores = [90, 72]
assert list(zip(names, scores)) == [("ana", 90), ("bo", 72)]    # "cy" silently dropped
try:
    list(zip(names, scores, strict=True))                        # 3.10+
except ValueError:
    pass
assert list(zip_longest(names, scores, fillvalue=0)) == [("ana", 90), ("bo", 72), ("cy", 0)]

assert list(reversed(names)) == ["cy", "bo", "ana"]
assert sorted("banana") == ["a", "a", "a", "b", "n", "n"]
assert sorted({3: "c", 1: "a"}) == [1, 3]                        # iterating a dict yields keys
```

### 49a.6.2 Index or value, and neighbors

Iterate over values directly; reach for `enumerate` when you need the position as well, and for `zip(xs, xs[1:])` or `itertools.pairwise` (3.10) when you need neighbors. `for i in range(len(xs))` is right only when you assign through the index.

```python
from itertools import pairwise

stamps = [0, 4, 9, 11]                                 # event times in seconds
gaps = [b - a for a, b in zip(stamps, stamps[1:])]     # neighbors without index arithmetic
assert gaps == [4, 5, 2] and [b - a for a, b in pairwise(stamps)] == gaps

for i, s in enumerate(stamps):
    stamps[i] = s * 1000                               # assigning through the index is fine
assert stamps == [0, 4000, 9000, 11000]
```

### 49a.6.3 Do not change a collection while iterating over it

Removing items from a list while looping over it skips elements, because the iterator walks by position while the list shifts under it. Changing a dict's or set's size during iteration raises `RuntimeError`. Build a new collection, assign through a slice to keep the same list object, or iterate over a snapshot.

```python
nums = [1, 2, 2, 3, 4]
for n in nums:
    if n % 2 == 0:
        nums.remove(n)                  # the list shifts under the iterator
assert nums == [1, 2, 3]                # one 2 survived

nums = [1, 2, 2, 3, 4]
alias = nums
nums[:] = [n for n in nums if n % 2]    # replace the contents; aliases see the change
assert alias == [1, 3]

counts = {"a": 0, "b": 2}
try:
    for k in counts:
        if counts[k] == 0:
            del counts[k]
except RuntimeError as err:
    assert "changed size during iteration" in str(err)

counts = {"a": 0, "b": 2}
for k in list(counts):                  # iterate over a snapshot of the keys
    if counts[k] == 0:
        del counts[k]
assert counts == {"b": 2}
```

### 49a.6.4 Two less common forms: loop `else` and `iter(callable, sentinel)`

The loop `else` (49a.5.3) replaces a "found" flag. The two-argument form of `iter` calls a function repeatedly until it returns the sentinel, which turns a read-chunks loop into a `for` loop:

```python
import io
from functools import partial

stream = io.BytesIO(b"abcdefghij")
chunks = list(iter(partial(stream.read, 4), b""))   # call read(4) until it returns b""
assert chunks == [b"abcd", b"efgh", b"ij"]
```

**Interview line:** *"I iterate over values, with enumerate for the index and zip or pairwise for neighbors, pass strict=True when lengths must match, and never resize a collection while iterating over it."*

## 49a.7 Strings in depth

### 49a.7.1 Immutability, indexing and slicing

A `str` is an immutable sequence of Unicode code points. Indexing is O(1) (CPython stores each string with a fixed width per character, 1, 2 or 4 bytes, chosen by its widest character), slicing copies, and every "modifying" method returns a new string. Slices clamp to the bounds and never raise; a single index out of range raises `IndexError`.

```python
s = "interview"
assert s[0] == "i" and s[-1] == "w" and s[2:5] == "ter" and s[::-1] == "weivretni"
assert s[::2] == "itriw" and s[:100] == s and s[100:] == ""
try:
    s[100]
except IndexError:
    pass
try:
    s[0] = "I"                          # strings are immutable
except TypeError:
    pass
assert "I" + s[1:] == "Interview"       # build a new string instead
```

### 49a.7.2 The methods you will use

```python
assert "ana,,bo".split(",") == ["ana", "", "bo"]            # an explicit separator keeps empty fields
assert "  many   spaces here ".split() == ["many", "spaces", "here"]   # no argument: runs of whitespace
assert "a.b.c.d".rsplit(".", 1) == ["a.b.c", "d"]          # maxsplit from the right
assert "k=v=w".partition("=") == ("k", "=", "v=w")         # always a 3-tuple
assert "no-equals".partition("=") == ("no-equals", "", "")
assert "line1\nline2\r\n".splitlines() == ["line1", "line2"]
assert "-".join(["2026", "10", "03"]) == "2026-10-03"       # join is a method of the separator
assert "  padded\t\n".strip() == "padded"
assert "--== title ==--".strip("-= ") == "title"            # strip removes a SET of characters
assert "v3.14.8".removeprefix("v") == "3.14.8"              # 3.9+: one exact prefix
assert "report.csv".removesuffix(".csv") == "report"
assert "a-b-c".replace("-", "+", 1) == "a+b-c"             # optional count
assert "hello".find("l") == 2 and "hello".rfind("l") == 3 and "hello".find("z") == -1
try:
    "hello".index("z")                                     # index raises instead of returning -1
except ValueError:
    pass
assert "aaaa".count("aa") == 2                             # non-overlapping matches
assert "photo.JPG".lower().endswith((".jpg", ".png"))      # startswith/endswith take tuples
assert "Straße".casefold() == "strasse" and "Straße".lower() == "straße"   # casefold for caseless matching
assert "7".zfill(3) == "007" and "-7".zfill(4) == "-007"   # the sign stays in front

leet = str.maketrans({"a": "4", "e": "3", "o": "0"})
assert "leet code".translate(leet) == "l33t c0d3"
assert "education".translate(str.maketrans("", "", "aeiou")) == "dctn"   # delete characters
```

The character-class predicates differ in ways that matter for input validation. `isdecimal` accepts only characters usable to write base-10 numbers, `isdigit` adds things like superscripts, and `isnumeric` adds fractions and other numerals. None accepts a sign or a decimal point, so the reliable way to validate a number is to try converting it.

```python
assert "123".isdecimal() and "123".isdigit() and "123".isnumeric()
assert "²".isdigit() and not "²".isdecimal()        # superscript two
assert "½".isnumeric() and not "½".isdigit()        # vulgar fraction one half
assert "٣".isdecimal() and int("٣") == 3            # Arabic-Indic digit three: int() accepts it
assert not "-5".isdigit() and not "3.5".isdecimal() # signs and points are not digits
assert "snake_case".isidentifier() and "abc".isalpha() and "abc123".isalnum() and " \t".isspace()

def parse_int(text):
    try:
        return int(text)                             # handles signs, spaces and underscores
    except ValueError:
        return None

assert parse_int(" -5 ") == -5 and parse_int("3.5") is None
```

### 49a.7.3 f-strings and format specifications

An f-string evaluates the expressions in braces and formats each with a *format specification* after a colon, which in simplified form is `[[fill]align][sign][#][0][width][grouping][.precision][type]`. Alignment is `<` (left), `>` (right), `^` (center) or `=` (pad after the sign); grouping is `,` or `_`; common types are `d`, `f`, `e`, `g`, `%`, `x`, `o`, `b`. A conversion `!r`, `!s` or `!a` applies `repr`, `str` or `ascii` first, and a trailing `=` (3.8) prints the expression text too: the fastest debugging print.

```python
import datetime

name, qty, price = "widget", 1250, 1234567.891
assert f"{name:<8}|" == "widget  |" and f"{name:>8}|" == "  widget|"
assert f"{name:^10}" == "  widget  " and f"{name:*^10}" == "**widget**"
assert f"{qty:,}" == "1,250" and f"{qty:_}" == "1_250"
assert f"{price:,.2f}" == "1,234,567.89"
assert f"{0.256:.1%}" == "25.6%"
assert f"{42:08.3f}" == "0042.000"
assert f"{-42:=8}" == "-     42" and f"{42:+}" == "+42"
assert f"{255:x} {255:#x} {255:o} {5:b} {5:08b}" == "ff 0xff 377 101 00000101"
assert f"{1234.5:e}" == "1.234500e+03" and f"{0.000012345:g}" == "1.2345e-05"

width, precision = 10, 3
assert f"{3.14159:{width}.{precision}f}" == "     3.142"     # nested replacement fields
assert f"{name!r}" == "'widget'" and f"{'é'!a}" == "'\\xe9'"
assert f"{qty=}" == "qty=1250" and f"{qty * 2 = }" == "qty * 2 = 2500"
assert f"{{literal braces}}" == "{literal braces}"

when = datetime.date(2026, 10, 3)
assert f"{when:%Y-%m-%d}" == "2026-10-03"                     # types define their own specs
assert f"{when!r}" == "datetime.date(2026, 10, 3)"
```

Python 3.12 (PEP 701) made f-strings part of the grammar: the same quote character can appear inside the braces, and backslashes, line breaks and comments are allowed there.

```python
# requires: 3.12
songs = ["intro", "outro"]
assert f"{", ".join(songs)}" == "intro, outro"     # 3.12+: reuse the outer quotes
assert f"{"\n".join(songs)}" == "intro\noutro"     # 3.12+: backslashes inside the braces
total = f"{
    sum([1, 2, 3])  # 3.12+: comments and line breaks inside the braces
}"
assert total == "6"
```

### 49a.7.4 `str.format`, `%`, and templates

`str.format` uses the same specification language with positions or names, and suits templates that are data (a translation file, a config value). The `%` operator is the oldest style; `logging` still uses it, as in `log.info("user %s", user_id)`, which defers formatting until a record is emitted. Never build SQL or shell commands with any of them: use parameters (49a.27) or the 3.14 template strings (49a.28).

```python
assert "{} has {} items".format("cart", 3) == "cart has 3 items"
assert "{0}-{1}-{0}".format("a", "b") == "a-b-a"
assert "{user[name]} is {user[age]:>3}".format(user={"name": "ana", "age": 7}) == "ana is   7"
assert "Hello {name}".format_map({"name": "bo"}) == "Hello bo"
assert "%s has %d items (%.1f%%)" % ("cart", 3, 37.5) == "cart has 3 items (37.5%)"
```

### 49a.7.5 Raw strings, Unicode, and bytes

A raw string (`r"..."`) keeps backslashes literally, which is what regular expressions and Windows paths need; it cannot end with an odd number of backslashes. Text is a sequence of code points; files, sockets and hashes deal in bytes, and `encode`/`decode` convert between them with an explicit encoding (UTF-8 unless you have a reason). The same visible text can be different code-point sequences (precomposed "é" versus "e" plus a combining accent), so normalize with `unicodedata.normalize` before comparing user input.

```python
import re
import unicodedata

assert r"\d+" == "\\d+" and len(r"\n") == 2
assert re.findall(r"\d+\.\d+", "v1.25 and v3.10") == ["1.25", "3.10"]

word = "café"
encoded = word.encode("utf-8")
assert encoded == b"caf\xc3\xa9" and len(word) == 4 and len(encoded) == 5
assert encoded.decode("utf-8") == word
try:
    encoded.decode("ascii")
except UnicodeDecodeError:
    pass
assert encoded.decode("ascii", errors="replace") == "caf\ufffd\ufffd"
assert "naïve".encode("ascii", errors="ignore") == b"nave"

composed, decomposed = "\u00e9", "e\u0301"   # one code point, and two
assert composed != decomposed and len(decomposed) == 2
assert unicodedata.normalize("NFC", decomposed) == composed
assert ord("中") == 0x4E2D and "中".encode() == b"\xe4\xb8\xad"
```

### 49a.7.6 Building strings efficiently, and what string operations cost

Each `+` on immutable strings creates a new string, so a loop of `result += piece` can be quadratic (CPython sometimes extends the string in place when nothing else refers to it, but that optimization is fragile and other implementations need not have it). Collect the pieces in a list and `"".join` them once, or write to an `io.StringIO`.

```python
import io

parts = []
for i in range(5):
    parts.append(f"<li>{i}</li>")
html = "".join(parts)                 # one pass over the total length
assert html.startswith("<li>0</li><li>1</li>")

buffer = io.StringIO()
for i in range(3):
    buffer.write(f"{i},")
assert buffer.getvalue() == "0,1,2,"
```

| Operation | Cost | Note |
|---|---|---|
| `len(s)`, `s[i]` | O(1) | |
| `s[a:b]` | O(b − a) | copies |
| `a + b` | O(len(a) + len(b)) | a new string |
| `"".join(parts)` | O(total length) | the way to concatenate many pieces |
| `sub in s`, `s.find(sub)`, `s.count(sub)`, `s.replace(...)` | O(len(s)) typical | since 3.10 CPython uses the two-way algorithm for long patterns, which avoids quadratic worst cases |
| `s.split()`, `s.strip()`, `s.lower()` | O(len(s)) | |
| `hash(s)` | O(len(s)) once | cached on the object afterward |
| `s == t` | O(len) | stops at the first difference |

**Interview line:** *"Strings are immutable sequences of code points: slicing copies, methods return new strings, and I build output with join. Anything that reaches SQL, a shell or HTML gets parameters or escaping, never string formatting."*

## 49a.8 Lists

A list is a dynamic array of references: a contiguous block of pointers with spare capacity at the end. That one sentence predicts its costs: indexing and appending are cheap, inserting or removing at the front is not, and searching is linear.

### 49a.8.1 Every list method

```python
items = [3, 1, 4]
items.append(1)               # [3, 1, 4, 1]
items.extend([5, 9])          # [3, 1, 4, 1, 5, 9]
items.insert(0, 2)            # [2, 3, 1, 4, 1, 5, 9]
items.remove(1)               # removes the FIRST 1: [2, 3, 4, 1, 5, 9]
last = items.pop()            # 9
first = items.pop(0)          # 2
assert (items, last, first) == ([3, 4, 1, 5], 9, 2)
assert items.index(1) == 2 and items.count(5) == 1
items.sort()
assert items == [1, 3, 4, 5]
items.reverse()
assert items == [5, 4, 3, 1]
clone = items.copy()          # same as items[:] or list(items): a shallow copy
items.clear()
assert items == [] and clone == [5, 4, 3, 1]

try:
    [1, 2].remove(3)          # remove and index raise ValueError when the value is absent
except ValueError:
    pass
try:
    [].pop()                  # pop on an empty list raises IndexError
except IndexError:
    pass
assert [1, 2] * 2 == [1, 2, 1, 2] and [1] + [2] == [1, 2]
```

### 49a.8.2 Slicing and slice assignment

`xs[start:stop:step]` copies the selected items into a new list. Assigning to a plain slice replaces that region with any number of items, so the list can grow or shrink; assigning to an extended slice (with a step) needs exactly as many items as the slice selects. `del` works on slices too.

```python
letters = list("abcdefg")
assert letters[1:4] == ["b", "c", "d"] and letters[::2] == ["a", "c", "e", "g"]
assert letters[-3:] == ["e", "f", "g"] and letters[::-1][:2] == ["g", "f"]

letters[1:3] = ["X"]                  # two items replaced by one
assert letters == ["a", "X", "d", "e", "f", "g"]
letters[1:1] = ["b", "c"]             # an empty slice: pure insertion
assert letters == ["a", "b", "c", "X", "d", "e", "f", "g"]
del letters[3]
letters[::2] = ["A", "C", "E", "G"]   # extended slice: the lengths must match
assert letters == ["A", "b", "C", "d", "E", "f", "G"]
try:
    letters[::2] = ["too", "few"]
except ValueError:
    pass
del letters[::2]
assert letters == ["b", "d", "f"]
```

### 49a.8.3 List comprehensions

A comprehension builds a list from an expression, one or more `for` clauses and optional `if` filters. The clauses read left to right exactly like nested loops written top to bottom. A conditional *expression* (`a if c else b`) goes before the `for`; a filter `if` goes after it.

```python
matrix = [[1, 2, 3], [4, 5, 6]]
flat = [x for row in matrix for x in row]            # for row in matrix: for x in row:
assert flat == [1, 2, 3, 4, 5, 6]
assert [[x * 10 for x in row] for row in matrix] == [[10, 20, 30], [40, 50, 60]]   # nested: keeps the rows
assert [x * x for x in flat if x % 2 == 0] == [4, 16, 36]
assert ["even" if x % 2 == 0 else "odd" for x in range(4)] == ["even", "odd", "even", "odd"]
```

### 49a.8.4 Sorting: `key`, stability, and multiple keys

`list.sort()` sorts in place and returns `None`; `sorted()` returns a new list from any iterable. Both use Timsort: stable (equal keys keep their order), O(n log n), and close to O(n) on mostly sorted data. The `key` function runs once per element. For several keys return a tuple, negating numeric keys to reverse them; when a key cannot be negated (strings), sort in passes from the minor key to the major one and let stability do the rest. `functools.cmp_to_key` adapts a comparison function for orders that are not a key, such as "which concatenation is larger".

```python
from functools import cmp_to_key

people = [("ana", "eng", 120), ("bo", "ops", 95), ("cy", "eng", 135), ("di", "ops", 95)]
by_salary = sorted(people, key=lambda p: p[2], reverse=True)
assert [p[0] for p in by_salary] == ["cy", "ana", "bo", "di"]   # stable: bo stays before di

assert [p[0] for p in sorted(people, key=lambda p: (p[1], -p[2]))] == ["cy", "ana", "bo", "di"]

staged = sorted(people, key=lambda p: p[0], reverse=True)   # pass 1, the minor key: name descending
staged.sort(key=lambda p: p[1])                             # pass 2, the major key; ties keep pass-1 order
assert [p[0] for p in staged] == ["cy", "ana", "di", "bo"]

words = ["banana", "apple", "Cherry"]
assert sorted(words) == ["Cherry", "apple", "banana"]             # code points: uppercase first
assert sorted(words, key=str.casefold) == ["apple", "banana", "Cherry"]
assert sorted(words, key=len) == ["apple", "banana", "Cherry"]    # ties keep input order

def larger_concatenation_first(a, b):
    return -1 if a + b > b + a else (1 if a + b < b + a else 0)

nums = ["3", "30", "34", "5", "9"]
assert "".join(sorted(nums, key=cmp_to_key(larger_concatenation_first))) == "9534330"

result = [3, 1, 2].sort()
assert result is None                 # sort() works in place and returns None
```

### 49a.8.5 Copying and aliasing

A shallow copy (`xs.copy()`, `xs[:]`, `list(xs)`, `copy.copy(xs)`) makes a new outer list that refers to the same inner objects. `copy.deepcopy` copies recursively, handles cycles, and is much slower. Multiplying a list of lists repeats references, not copies.

```python
import copy

grid = [[1, 2], [3, 4]]
shallow = grid.copy()
deep = copy.deepcopy(grid)
grid[0].append(99)
assert shallow[0] == [1, 2, 99] and shallow[0] is grid[0]   # inner lists are shared
assert deep[0] == [1, 2]

bad = [[0] * 3] * 3                   # three references to ONE inner list
bad[0][0] = 1
assert bad == [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
good = [[0] * 3 for _ in range(3)]    # a new inner list per row
good[0][0] = 1
assert good == [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
```

`[0] * 3` is safe because integers are immutable; the problem only appears when the repeated element is mutable.

### 49a.8.6 Costs, and lists as stacks

| Operation | Average cost | Why |
|---|---|---|
| `xs[i]`, `xs[i] = v`, `len(xs)` | O(1) | direct index into the pointer array |
| `xs.append(v)`, `xs.pop()` | O(1) amortized | spare capacity; an occasional resize copies everything |
| `xs.insert(i, v)`, `xs.pop(i)`, `del xs[i]` | O(n − i) | every later element shifts; at the front that is O(n) |
| `v in xs`, `xs.index(v)`, `xs.count(v)`, `xs.remove(v)` | O(n) | linear scan |
| `xs[a:b]`, `xs.copy()` | O(b − a), O(n) | copies references |
| `xs.extend(ys)`, `xs + ys` | O(len(ys)), O(n + m) | |
| `xs.sort()`, `sorted(xs)` | O(n log n) | Timsort; near O(n) on sorted runs |
| `min`, `max`, `sum`, `xs.reverse()` | O(n) | |

The over-allocation is visible with `sys.getsizeof`: a list's size grows in jumps, not one slot per append. A list is a good stack: `append` pushes and `pop()` pops, both O(1) at the end. It is a bad queue: use `collections.deque` (49a.13).

```python
def balanced(text):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack

assert balanced("f(a[1], {b: 2})") and not balanced("(]") and not balanced("((")
```

## 49a.9 Arrays: `array`, `bytearray` and `memoryview`

A list stores pointers to full objects: each float costs an 8-byte pointer plus a 24-byte float object. The `array` module stores raw C values of one type, chosen by a *typecode*, in one contiguous buffer. It behaves like a list but rejects values of the wrong type or range, and converts to and from bytes cheaply. Vectorized math is NumPy's job; `array` is for compact storage and binary I/O.

| Typecode | C type | Python type | Minimum bytes |
|---|---|---|---|
| `"b"`, `"B"` | signed, unsigned char | int | 1 |
| `"h"`, `"H"` | signed, unsigned short | int | 2 |
| `"i"`, `"I"` | signed, unsigned int | int | 2 (4 on common platforms) |
| `"l"`, `"L"` | signed, unsigned long | int | 4 |
| `"q"`, `"Q"` | signed, unsigned long long | int | 8 |
| `"f"`, `"d"` | float, double | float | 4, 8 |
| `"w"` | Py_UCS4 | one-character str | 4 (added in 3.13; `"u"` is deprecated and scheduled for removal in 3.16) |

```python
import sys
from array import array

readings = array("d", [21.5, 22.0, 19.75])    # C doubles, 8 bytes each
readings.append(20.25)
assert readings.itemsize == 8 and len(readings) == 4
assert readings[1:3] == array("d", [22.0, 19.75])   # slices are arrays
assert sum(readings) / len(readings) == 20.875

counts = array("H", [1, 2, 3])                # unsigned 16-bit
try:
    counts.append(70_000)                     # out of range for the C type
except OverflowError:
    pass
try:
    counts.append(1.5)                        # wrong Python type
except TypeError:
    pass

raw = readings.tobytes()                      # native byte order; byteswap() converts
restored = array("d")
restored.frombytes(raw)
assert restored == readings and len(raw) == 32

as_list = [float(i) for i in range(100_000)]
as_array = array("d", as_list)
list_bytes = sys.getsizeof(as_list) + sum(sys.getsizeof(x) for x in as_list)
assert sys.getsizeof(as_array) < list_bytes / 3     # about 8 bytes per value against about 32
```

`bytearray` is a mutable `bytes`: you can assign items and slices, extend it, and use it as a reusable I/O buffer. `memoryview` exposes the memory of any buffer-protocol object (`bytes`, `bytearray`, `array`, `mmap`) without copying: slicing a memoryview gives another view, and writing through a view of a mutable buffer changes the buffer. Use it to parse large binary data or hand parts of a buffer to `socket.send` without copies. `struct` packs and unpacks fixed binary records with explicit sizes and byte order.

```python
import struct

packet = bytearray(b"\x01\x02hello")
packet[0] = 0xFF                              # item assignment
packet[2:7] = b"HELLO"                        # slice assignment
packet.extend(b"!")
assert packet == bytearray(b"\xff\x02HELLO!") and packet.hex() == "ff0248454c4c4f21"

buffer = bytearray(b"header:payload")
view = memoryview(buffer)
payload = view[7:]                            # no copy: a window onto the same memory
payload[0:3] = b"PAY"                         # writing through the view changes the buffer
assert buffer == bytearray(b"header:PAYload")
assert payload.tobytes() == b"PAYload" and payload.nbytes == 7
try:
    memoryview(b"read-only")[0] = 65          # a view of bytes is read-only
except TypeError:
    pass

record = struct.pack("<HIf", 7, 1_000_000, 0.5)   # little-endian uint16, uint32, float32
assert len(record) == 10 and struct.unpack("<HIf", record) == (7, 1_000_000, 0.5)
```

When to use which: a list for general-purpose sequences of objects; `array` for large homogeneous numeric data you store, send or read in binary; `bytes` for immutable binary data and dict keys; `bytearray` to build or edit binary data; `memoryview` to slice big buffers without copying; `struct` to read and write binary formats.

## 49a.10 Tuples

### 49a.10.1 Packing, unpacking and immutability

The comma makes a tuple, not the parentheses: `point = 3, 4` is a tuple, `(5)` is just 5, and a one-element tuple needs a trailing comma. A function that "returns several values" returns one tuple, which the caller unpacks. A tuple's immutability is shallow: you cannot rebind its slots, but a mutable object inside it can still change, and such a tuple is unhashable.

```python
point = 3, 4                          # packing
single = (5,)
not_a_tuple = (5)
assert type(point) is tuple and type(single) is tuple and type(not_a_tuple) is int
assert () == tuple()

def min_max(values):
    return min(values), max(values)   # returns one tuple

lo, hi = min_max([4, 1, 9])           # unpacking
assert (lo, hi) == (1, 9)

pair = ([1], "label")
pair[0].append(2)                     # the slot cannot change; the list in it can
assert pair == ([1, 2], "label")
try:
    hash(pair)                        # unhashable because one item is unhashable
except TypeError:
    pass

distances = {("berlin", "paris"): 878, ("paris", "rome"): 1106}   # composite dict keys
assert distances[("berlin", "paris")] == 878
assert (1, 2, 2).count(2) == 2 and (1, 2, 3).index(3) == 2
assert (1, "b") < (1, "c") < (2, "a")                             # lexicographic order
```

Use a tuple for a fixed-size record whose positions mean different things (a coordinate, a database row, a dict key made of several parts) and a list for a variable-length sequence of similar things. Tuples are slightly smaller and faster to create, and constant tuples are built once at compile time.

### 49a.10.2 Named tuples

`collections.namedtuple` and `typing.NamedTuple` create tuple subclasses whose positions also have names. They stay tuples (indexing, unpacking, comparison, hashing all work) and cost no more memory than a plain tuple, which makes them a good return type for functions that return several values. `typing.NamedTuple` uses class syntax with annotations, defaults and methods. When you need mutability, validation or inheritance, use a dataclass (49a.17.12).

```python
from collections import namedtuple
from typing import NamedTuple

Span = namedtuple("Span", ["start", "end"])
s = Span(3, 8)
assert s.start == 3 and s[1] == 8 and s == (3, 8)    # still a tuple
assert s._replace(end=9) == Span(3, 9)              # "modify" by building a new one
assert s._asdict() == {"start": 3, "end": 8} and Span._fields == ("start", "end")
start, end = s

class Endpoint(NamedTuple):
    host: str
    port: int = 443

    def url(self) -> str:
        return f"https://{self.host}:{self.port}"

api = Endpoint("api.internal")
assert api.url() == "https://api.internal:443"
try:
    api.port = 80                                    # immutable like any tuple
except AttributeError:
    pass
```

## 49a.11 Dictionaries

A dict is a hash table: the key's hash picks a slot, and equality confirms the match. That gives average O(1) lookup, insertion and deletion, requires keys to be hashable, and, since Python 3.7, the language guarantees that iteration follows insertion order.

### 49a.11.1 Creating, reading and updating

```python
inventory = {"apple": 3, "pear": 0}
assert inventory["apple"] == 3
try:
    inventory["fig"]                                   # a missing key raises KeyError
except KeyError:
    pass
assert inventory.get("fig") is None and inventory.get("fig", 0) == 0
assert inventory.setdefault("fig", 7) == 7 and inventory["fig"] == 7    # inserted
assert inventory.setdefault("fig", 99) == 7                             # existing value kept

defaults = {"timeout": 30, "retries": 3}
overrides = {"retries": 5}
merged = defaults | overrides            # 3.9+: a new dict; the right side wins
assert merged == {"timeout": 30, "retries": 5} and defaults["retries"] == 3
defaults |= overrides                    # in place, like update()
assert defaults == merged
assert {**{"a": 1}, **{"a": 2, "b": 3}} == {"a": 2, "b": 3}   # unpacking merges too (3.5+)

assert inventory.pop("pear") == 0 and inventory.pop("missing", None) is None
assert inventory.popitem() == ("fig", 7)   # LIFO: the most recently inserted pair
del inventory["apple"]
assert inventory == {}

assert dict(zip(["a", "b"], [1, 2])) == {"a": 1, "b": 2}
squares = {n: n * n for n in range(4)}     # dict comprehension
assert list(squares) == [0, 1, 2, 3]       # iteration follows insertion order
assert list(reversed(squares)) == [3, 2, 1, 0]   # 3.8+
assert {"a": 1, "b": 2} == {"b": 2, "a": 1}      # equality ignores order
```

`dict.fromkeys(keys, value)` is handy with an immutable value and a trap with a mutable one, because every key gets the same object:

```python
shared = dict.fromkeys(["a", "b"], [])
shared["a"].append(1)
assert shared == {"a": [1], "b": [1]}            # one list behind every key
separate = {k: [] for k in ["a", "b"]}           # a comprehension builds one per key
separate["a"].append(1)
assert separate == {"a": [1], "b": []}
```

### 49a.11.2 Views

`keys()`, `values()` and `items()` return *views*: live windows onto the dict, not copies. Key views and item views are set-like and support `&`, `|`, `-` and `^`.

```python
stock = {"apple": 3, "pear": 1}
keys, items = stock.keys(), stock.items()
stock["fig"] = 2
assert list(keys) == ["apple", "pear", "fig"]          # the view sees later changes
assert keys & {"pear", "kiwi"} == {"pear"}             # set operations on keys
assert ("fig", 2) in items
assert sorted(stock, key=stock.get) == ["pear", "fig", "apple"]   # keys ordered by value
assert max(stock.items(), key=lambda kv: kv[1]) == ("apple", 3)
```

### 49a.11.3 What a key must be: the `__eq__` and `__hash__` contract

A key must be hashable, and objects that compare equal must have equal hashes. The dict stores the hash with the entry and compares hashes before calling `__eq__`, so breaking the contract, or mutating a key after inserting it, makes entries unreachable. Values that are equal across types are the same key: `1`, `1.0` and `True` collide by design.

```python
class Tag:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Tag) and self.name == other.name

    def __hash__(self):
        return hash(self.name)              # equal tags hash alike

counts = {Tag("py"): 1}
assert counts[Tag("py")] == 1               # a different but equal object finds the entry

key = Tag("go")
counts[key] = 2
key.name = "rust"                           # mutating a key after insertion...
assert Tag("go") not in counts and Tag("rust") not in counts   # ...strands the entry
assert len(counts) == 2

try:
    {[1, 2]: "x"}
except TypeError as err:
    assert "unhashable" in str(err)

mixed = {1: "int", 1.0: "float", True: "bool"}
assert mixed == {1: "bool"}                 # one key; the first key object and the last value stay
```

| Operation | Average | Worst case |
|---|---|---|
| `d[k]`, `d[k] = v`, `del d[k]`, `k in d`, `d.get(k)` | O(1) | O(n) with pathological hash collisions |
| `d.pop(k)`, `d.popitem()`, `d.setdefault(k, v)` | O(1) | O(n) |
| iteration, `d.copy()`, `list(d)` | O(n) | |
| `d1 \| d2`, `d1.update(d2)` | O(len(d1) + len(d2)), O(len(d2)) | |

String hashes are randomized per process (set `PYTHONHASHSEED` to reproduce one), so never persist `hash()` values or rely on set iteration order for strings.

### 49a.11.4 `defaultdict`, `Counter`, `OrderedDict` and `ChainMap`

`defaultdict(factory)` calls `factory()` to create a missing value whenever you read a missing key with `[]`. That makes grouping one line, and it also means that merely reading `d[k]` inserts `k`; use `get` or `in` to look without creating.

```python
from collections import defaultdict

words = ["apple", "avocado", "banana", "blueberry", "cherry"]
by_letter = defaultdict(list)
for w in words:
    by_letter[w[0]].append(w)               # a missing key starts as list()
assert by_letter["b"] == ["banana", "blueberry"]
assert dict(by_letter) == {"a": ["apple", "avocado"], "b": ["banana", "blueberry"], "c": ["cherry"]}

assert by_letter.get("z") is None and "z" not in by_letter    # get() and in do not create keys
by_letter["z"]                                                # reading with [] does
assert by_letter["z"] == [] and "z" in by_letter
```

`Counter` is a dict subclass for counting hashable things. Missing keys read as zero without being inserted, `most_common(n)` returns the top counts (ties in first-seen order), and counters support arithmetic: `+` and `-` add and subtract (keeping only positive results), `&` and `|` take the minimum and maximum of each count.

```python
from collections import Counter

votes = Counter(["py", "go", "py", "rust", "py", "go"])
assert votes["py"] == 3 and votes["java"] == 0 and "java" not in votes
assert votes.most_common(2) == [("py", 3), ("go", 2)]
votes.update(["rust", "rust"])              # adds to the counts (dict.update would replace)
assert votes["rust"] == 3 and votes.total() == 8                # total(): 3.10+

used, free = Counter(cpu=5, gpu=2), Counter(cpu=3, gpu=4)
assert used + free == Counter(cpu=8, gpu=6)
assert used - free == Counter(cpu=2)        # zero and negative results are dropped
assert used & free == Counter(cpu=3, gpu=2) and used | free == Counter(cpu=5, gpu=4)
used.subtract(free)                         # subtract() keeps zero and negative counts
assert used == Counter(cpu=2, gpu=-2)
assert Counter("listen") == Counter("silent")   # an anagram check in one line
```

Plain dicts keep insertion order, so `OrderedDict` is now for its extra operations: `move_to_end(key, last=True)`, `popitem(last=False)` for FIFO removal, and order-sensitive equality between two `OrderedDict`s. Those make it the classic building block for an LRU cache (39d.23 has one; the `functools.lru_cache` decorator in 49a.20 is the production answer).

```python
from collections import OrderedDict

pages = OrderedDict(home=1, docs=2, blog=3)             # least recently used first
pages.move_to_end("home")                               # "home" was just used
assert list(pages) == ["docs", "blog", "home"]
assert pages.popitem(last=False) == ("docs", 2)         # evict from the front
pages.move_to_end("home", last=False)                   # last=False moves a key to the front
assert list(pages) == ["home", "blog"]
assert OrderedDict(a=1, b=2) != OrderedDict(b=2, a=1)   # order matters between OrderedDicts
assert OrderedDict(a=1, b=2) == {"b": 2, "a": 1}        # but not against a plain dict
```

`ChainMap` searches several mappings in order without merging them, which models layered settings (a request's options over a team's over global defaults) and nested scopes. Writes go to the first mapping only.

```python
from collections import ChainMap

defaults = {"model": "small", "temperature": 0.2}
team = {"model": "large"}
request = {}
settings = ChainMap(request, team, defaults)
assert settings["model"] == "large" and settings["temperature"] == 0.2
settings["temperature"] = 0.0               # lands in request, not in defaults
assert request == {"temperature": 0.0} and defaults["temperature"] == 0.2
trial = settings.new_child({"model": "tiny"})   # a new front layer
assert trial["model"] == "tiny" and settings["model"] == "large"
```

The `repr` of an `OrderedDict` changed in 3.12, from a list of pairs (`OrderedDict([('a', 1)])`) to dict syntax (`OrderedDict({'a': 1})`); doctests that print one need updating when you upgrade.

### 49a.11.5 Dict patterns: counting, grouping, inverting, indexing

```python
from collections import defaultdict

orders = [("ana", 30), ("bo", 15), ("ana", 20)]

totals = defaultdict(int)
for customer, amount in orders:
    totals[customer] += amount                         # summing per key
assert totals == {"ana": 50, "bo": 15}

grouped = {}
for customer, amount in orders:
    grouped.setdefault(customer, []).append(amount)   # grouping with a plain dict
assert grouped == {"ana": [30, 20], "bo": [15]}

codes = {"de": "Germany", "at": "Austria"}
assert {v: k for k, v in codes.items()} == {"Germany": "de", "Austria": "at"}   # one-to-one inversion

users = [{"id": 7, "name": "ana"}, {"id": 9, "name": "bo"}]
by_id = {u["id"]: u for u in users}                   # index records for O(1) lookups
assert by_id[9]["name"] == "bo"
```

When several keys share a value, a one-to-one inversion silently keeps only the last key; group the keys into lists instead (lab exercise 17). Two more dict patterns carry most coding rounds: "value seen so far" maps (Two Sum in one pass, prefix sums with a hash map; 39d.23) and memo tables for recursion, where `functools.cache` (49a.20.5, 39d.24) is the table you should reach for first.

## 49a.12 Sets and frozensets

A set is a hash table without values: unordered, unique, hashable elements, average O(1) membership. Operators work between sets; the named methods accept any iterable. `frozenset` is the immutable, hashable version, so it can be a dict key or an element of another set.

```python
a, b = {1, 2, 3, 4}, {3, 4, 5}
assert a | b == {1, 2, 3, 4, 5} and a & b == {3, 4}       # union, intersection
assert a - b == {1, 2} and a ^ b == {1, 2, 5}             # difference, symmetric difference
assert {1, 2} <= a and {1, 2} < a and a >= {4}            # subset, proper subset, superset
assert a.union([9], (10,)) == {1, 2, 3, 4, 9, 10}         # methods take any iterables
try:
    a | [9]                                               # operators need sets
except TypeError:
    pass

s = {1}
s.add(2)
s.update([3, 4])                     # like |=
s.discard(99)                        # no error when absent
try:
    s.remove(99)                     # KeyError when absent
except KeyError:
    pass
s -= {4}
assert s == {1, 2, 3}
assert {n % 3 for n in range(10)} == {0, 1, 2}             # set comprehension
assert set() != {} and type({}) is dict                    # {} is an empty dict

groups = {frozenset({"ana", "bo"}): "pair"}                # frozensets are hashable
assert groups[frozenset({"bo", "ana"})] == "pair"
```

| Operation | Average cost |
|---|---|
| `x in s`, `s.add(x)`, `s.remove(x)`, `s.discard(x)` | O(1) |
| `s \| t` | O(len(s) + len(t)) |
| `s & t` | O(min(len(s), len(t))) |
| `s - t` | O(len(s)) |
| `s <= t` | O(len(s)) |
| `set(iterable)` | O(n) |

Set iteration order is arbitrary and, for strings, changes between processes. To remove duplicates while keeping the first occurrences in order, use `dict.fromkeys`; when the items are unhashable or you deduplicate by a derived key, keep a `seen` set:

```python
items = ["b", "a", "b", "c", "a"]
assert list(dict.fromkeys(items)) == ["b", "a", "c"]

def dedupe(iterable, key=None):
    seen = set()
    for item in iterable:
        marker = item if key is None else key(item)
        if marker not in seen:
            seen.add(marker)
            yield item

rows = [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}, {"id": 1, "v": "z"}]
assert [r["v"] for r in dedupe(rows, key=lambda r: r["id"])] == ["x", "y"]
```

## 49a.13 Other standard collections: `deque`, `heapq`, `bisect` and queues

For how these appear in coding rounds, see 39d.24; here are the mechanics.

### 49a.13.1 `collections.deque`

A double-ended queue built from linked blocks: O(1) appends and pops at both ends, O(n) access in the middle. `maxlen` makes it a bounded buffer that discards from the opposite end, which is the simplest "last N events" structure.

```python
from collections import deque

line = deque(["b", "c"])
line.appendleft("a")                 # O(1); list.insert(0, x) is O(n)
line.append("d")
assert line.popleft() == "a" and line.pop() == "d"
line.rotate(1)                       # rotate right: the last item moves to the front
assert list(line) == ["c", "b"] and line[0] == "c"

recent = deque(maxlen=3)
for event in ["login", "view", "click", "logout"]:
    recent.append(event)             # "login" falls off the left end
assert list(recent) == ["view", "click", "logout"]
```

### 49a.13.2 `heapq`

`heapq` keeps a binary min-heap inside a plain list: `heap[0]` is always the smallest item, `heappush` and `heappop` are O(log n), and `heapify` is O(n). Tuples order by their first element, so `(priority, item)` pairs work, with a counter in the middle when items themselves cannot be compared. For a max-heap, push negated keys (works on every version) or, on 3.14, use the new `_max` functions.

```python
import heapq
import itertools

tasks = [(3, "rotate logs"), (1, "fix outage"), (2, "review PR")]
heapq.heapify(tasks)
heapq.heappush(tasks, (0, "page on-call"))
assert heapq.heappop(tasks) == (0, "page on-call")
assert [heapq.heappop(tasks)[1] for _ in range(3)] == ["fix outage", "review PR", "rotate logs"]

nums = [5, 1, 8, 3, 9, 2]
assert heapq.nlargest(2, nums) == [9, 8] and heapq.nsmallest(2, nums) == [1, 2]
assert list(heapq.merge([1, 4, 7], [2, 5], [3])) == [1, 2, 3, 4, 5, 7]   # lazy k-way merge

max_heap = []
for n in nums:
    heapq.heappush(max_heap, -n)     # negate for a max-heap
assert -max_heap[0] == 9

tie_breaker = itertools.count()
jobs = []
heapq.heappush(jobs, (1, next(tie_breaker), {"name": "a"}))   # dicts cannot be compared,
heapq.heappush(jobs, (1, next(tie_breaker), {"name": "b"}))   # so the counter decides ties
assert heapq.heappop(jobs)[2] == {"name": "a"}
```

```python
# requires: 3.14
import heapq

scores = [5, 1, 8, 3]
heapq.heapify_max(scores)            # 3.14+: max-heap functions
heapq.heappush_max(scores, 7)
assert heapq.heappop_max(scores) == 8 and scores[0] == 7
```

### 49a.13.3 `bisect`

`bisect_left(a, x)` returns the first index where `x` could be inserted into the sorted list `a` while keeping it sorted (the lower bound); `bisect_right` returns the index after any existing equal items (the upper bound). `insort` inserts in order: the search is O(log n), the shift is O(n). Since 3.10 the functions take `key=`.

```python
import bisect

bounds = [100, 300, 1000]                    # upper bounds of latency buckets, in ms
labels = ["fast", "ok", "slow", "timeout risk"]

def bucket(ms):
    return labels[bisect.bisect_left(bounds, ms)]   # a value equal to a bound stays in that bucket

assert [bucket(ms) for ms in (40, 100, 101, 999, 5000)] == ["fast", "fast", "ok", "slow", "timeout risk"]

ids = [10, 20, 30, 30, 40]
assert bisect.bisect_left(ids, 30) == 2 and bisect.bisect_right(ids, 30) == 4
bisect.insort(ids, 25)
assert ids == [10, 20, 25, 30, 30, 40]

people = [("ana", 31), ("bo", 42), ("cy", 57)]               # sorted by age
i = bisect.bisect_left(people, 40, key=lambda p: p[1])       # 3.10+
assert people[i] == ("bo", 42)
```

### 49a.13.4 `queue` and `asyncio.Queue`

`queue.Queue` (FIFO), `LifoQueue` and `PriorityQueue` are thread-safe, with blocking `get` and `put`, optional `maxsize` for backpressure, and `task_done`/`join` to wait until every item is processed. `asyncio.Queue` has the same shape for coroutines, with `await q.put(item)` and `await q.get()` and the same sentinel pattern for shutdown; it is not thread-safe. A `deque` is enough inside a single thread.

```python
import queue
import threading

work = queue.Queue()
results = []

def worker():
    while (item := work.get()) is not None:   # None is the stop signal
        results.append(item * 2)
        work.task_done()
    work.task_done()

thread = threading.Thread(target=worker)
thread.start()
for n in range(5):
    work.put(n)
work.put(None)
work.join()                                   # returns when every item is marked done
thread.join()
assert results == [0, 2, 4, 6, 8]
```

| Need | Use |
|---|---|
| FIFO queue or both ends | `collections.deque` |
| Repeatedly take the smallest (or largest) | `heapq` on a list |
| Sorted list with binary search, few inserts | `list` plus `bisect` |
| Producer and consumer threads, or coroutines | `queue.Queue`, `asyncio.Queue` |

## 49a.14 Comprehensions and generator expressions in depth

There are four forms: list `[expr for ...]`, set `{expr for ...}`, dict `{key: value for ...}` and generator `(expr for ...)`. There is no tuple comprehension; `tuple(expr for ...)` passes a generator expression to `tuple`. Each form is equivalent to nested `for` loops and `if` filters written in the same order, with one difference in scope: the loop variables belong to the comprehension and do not leak into the surrounding code.

```python
x = "outer"
squares = [x * x for x in range(4)]
assert x == "outer"                                     # the loop variable did not leak

words = ["apple", "bob", "civic", "dad", "eve"]
lengths = {w: len(w) for w in words if len(w) > 3}      # dict comprehension with a filter
assert lengths == {"apple": 5, "civic": 5}
initials = {w[0] for w in words}                        # set comprehension
assert initials == {"a", "b", "c", "d", "e"}
assert tuple(n * 2 for n in range(3)) == (0, 2, 4)      # "tuple comprehension"
assert sum(len(w) for w in words) == 19                 # a sole argument needs no extra parentheses
```

### 49a.14.1 When things are evaluated

The outermost iterable is evaluated immediately, when the comprehension or generator expression is created. Everything else, including the filter conditions and inner iterables, is evaluated as items are produced. For a list comprehension that distinction is invisible; for a generator expression, which runs later, it shows:

```python
threshold = 2
gen = (n for n in [1, 2, 3, 4] if n > threshold)
threshold = 3                         # the filter reads the name when the generator runs
assert list(gen) == [4]

items = [1, 2]
gen = (n for n in items)
items = [9, 9]                        # rebinding does not matter: the iterable was taken already
assert list(gen) == [1, 2]
assert list(gen) == []                # and a generator is exhausted after one pass (49a.19)
```

### 49a.14.2 Scope, the walrus, and class bodies

Since Python 3, a comprehension runs in its own scope. Python 3.12 inlined list, dict and set comprehensions into the enclosing function for speed (PEP 709) while keeping that visible scoping. An assignment expression inside a comprehension binds in the enclosing scope on purpose, which is the one way to get a value out (49a.4.5).

In a class body there is a trap: the comprehension's scope cannot see names defined in the class body, because class bodies are not enclosing scopes for nested functions (49a.2.3). Only the outermost iterable, evaluated in the class body itself, can use them.

```python
class Report:
    columns = ["id", "name"]
    prefix = "col_"
    upper = [c.upper() for c in columns]           # fine: columns is the outermost iterable
    try:
        headers = [prefix + c for c in columns]    # prefix is invisible inside the comprehension
    except NameError:
        headers = None

assert Report.upper == ["ID", "NAME"] and Report.headers is None
Report.headers = [Report.prefix + c for c in Report.columns]   # compute it outside the class body
assert Report.headers == ["col_id", "col_name"]
```

### 49a.14.3 Generator expressions and memory

A list comprehension builds the whole list; a generator expression produces one item at a time, so feeding `sum`, `any`, `max`, `"".join` or a `for` loop from a generator uses constant memory. `any` and `all` also stop at the first decisive item.

```python
import sys

as_list = [n for n in range(100_000)]
as_gen = (n for n in range(100_000))
assert sys.getsizeof(as_gen) < 500 < sys.getsizeof(as_list)   # the generator holds no items

checked = []
def is_negative(n):
    checked.append(n)
    return n < 0

assert any(is_negative(n) for n in [3, -1, 4, -5])
assert checked == [3, -1]                     # any() stopped at the first True
```

### 49a.14.4 Readability limits

Comprehensions build a collection from an expression. Two `for` clauses and one condition is about the limit; beyond that, write a loop or a generator function with named steps. Do not use a comprehension for side effects (`[print(x) for x in items]` builds a list of `None`s) or nest conditional expressions in one. Comprehensions are usually faster than a loop with `append`, but readability decides.

**Interview line:** *"A comprehension is nested loops with its own scope; the outermost iterable is evaluated at once and the rest lazily, which matters for generator expressions; in a class body it cannot see class attributes; and past two fors and a filter I write a loop."*

## 49a.15 Functions

### 49a.15.1 `def` creates an object at run time

`def` is an executable statement: when it runs, it creates a function object and binds it to a name. The object carries its code, its default values (evaluated once, at that moment), its annotations, its docstring and, for nested functions, the closure cells it captured.

```python
def greet(name: str, punctuation: str = "!") -> str:
    """Return a greeting."""
    return f"Hello, {name}{punctuation}"

assert greet.__name__ == "greet" and greet.__doc__ == "Return a greeting."
assert greet.__defaults__ == ("!",)
assert greet.__annotations__ == {"name": str, "punctuation": str, "return": str}
assert greet.__code__.co_argcount == 2

alias = greet                          # functions are ordinary objects
assert alias("Ana") == "Hello, Ana!"
greet.calls = 0                        # they can even carry attributes
```

### 49a.15.2 Parameters: positional-only, keyword-only, defaults, `*args`, `**kwargs`

The full parameter list has five zones, in this order:

```python
def request(method, url, /, body=None, *extra, timeout=10.0, retries=3, **headers):
    return method, url, body, extra, timeout, retries, headers

assert request("GET", "/items") == ("GET", "/items", None, (), 10.0, 3, {})
assert request("POST", "/items", {"a": 1}, "x", timeout=2, Accept="json") == (
    "POST", "/items", {"a": 1}, ("x",), 2, 3, {"Accept": "json"})
try:
    request(method="GET", url="/items")     # positional-only parameters reject keywords
except TypeError:
    pass
assert request("GET", "/", url="kept")[6] == {"url": "kept"}   # so **headers may use those names
```

- Before `/`: **positional-only** (3.8). Callers cannot pass them by name, so you can rename them freely, and `**kwargs` can accept the same names. Many built-ins are positional-only, such as `len(obj, /)`.
- Between `/` and `*`: positional-or-keyword, the default kind.
- `*args` collects extra positional arguments into a tuple. A bare `*` without a name ends the positional parameters without collecting any.
- After `*` or `*args`: **keyword-only**. Use them for options and flags, so that a call reads `fetch(url, verify=False)` instead of `fetch(url, False)`.
- `**kwargs` collects extra keyword arguments into a dict.

At the call site, `*iterable` spreads items into positional arguments and `**mapping` spreads key–value pairs into keyword arguments; several of each are allowed, and a repeated keyword is a `TypeError`.

```python
def volume(length, width, height):
    return length * width * height

dims = [2, 3]
assert volume(*dims, 4) == 24
assert volume(**{"length": 2, "width": 3, "height": 4}) == 24
assert volume(*[2], *[3], **{"height": 4}) == 24
try:
    volume(2, 3, 4, **{"height": 5})   # height given twice
except TypeError:
    pass

def tag(name, /, *, closed=True):
    return f"<{name}/>" if closed else f"<{name}>"

assert tag("br") == "<br/>" and tag("p", closed=False) == "<p>"
try:
    tag("p", False)                    # keyword-only: the flag must be named
except TypeError:
    pass
```

`inspect.signature(func)` shows the parameter list and is what frameworks such as FastAPI read to build their request parsing.

### 49a.15.3 The mutable default argument pitfall

Default values are evaluated once, when `def` runs, and stored on the function. A mutable default is therefore shared by every call that does not pass the argument. The same applies to values that should be computed per call, such as the current time.

```python
import datetime

def add_tag(tag, tags=[]):              # the list is created once
    tags.append(tag)
    return tags

assert add_tag("a") == ["a"]
assert add_tag("b") == ["a", "b"]       # the same list again
assert add_tag.__defaults__ == (["a", "b"],)

def add_tag_fixed(tag, tags=None):      # None as the "not given" marker
    if tags is None:
        tags = []
    tags.append(tag)
    return tags

assert add_tag_fixed("a") == ["a"] and add_tag_fixed("b") == ["b"]

def stamp(message, when=datetime.datetime.now()):   # frozen at definition time
    return when

assert stamp("x") is stamp("y")         # every call gets the same timestamp object
```

When `None` is itself a meaningful value, use a private sentinel object as the default (49a.21.4).

### 49a.15.4 Functions as values: higher-order functions, `map`, `filter`, `reduce`, `partial`

A higher-order function takes or returns functions. The built-ins `sorted`, `min`, `max` take a `key` function; `map` and `filter` return lazy iterators; `functools.reduce` folds a sequence into one value; `functools.partial` fixes some arguments of a function and returns a new callable.

```python
from functools import partial, reduce
import operator

names = ["bo", "Ana", "cy"]
assert sorted(names, key=str.lower) == ["Ana", "bo", "cy"]
assert max(names, key=len) == "Ana" and min([], default=None) is None
prices = {"apple": 3, "pear": 1}
assert max(prices, key=prices.get) == "apple"            # the key with the largest value

assert list(map(str.upper, names)) == ["BO", "ANA", "CY"]   # same as [s.upper() for s in names]
assert list(map(operator.add, [1, 2], [10, 20])) == [11, 22]
assert list(filter(None, [0, 1, "", "x"])) == [1, "x"]      # None keeps truthy items
assert reduce(operator.mul, [1, 2, 3, 4]) == 24
assert reduce(lambda acc, s: acc + len(s), names, 0) == 7  # an initializer for empty input

by_length = partial(sorted, key=len)                     # a new callable with key fixed
assert by_length(["ccc", "a", "bb"]) == ["a", "bb", "ccc"]
assert by_length.func is sorted and by_length.keywords == {"key": len}
```

Prefer a comprehension to `map` or `filter` with a `lambda`; use `map` when you already have a named function. Prefer `sum`, `math.prod`, `any`, `all`, `max` and `"".join` to `reduce` when one of them says what you mean. Functions that return functions, such as `compose(f, g)(x) == f(g(x))`, are lab exercise 21.

### 49a.15.5 Closures, `nonlocal`, and the late-binding pitfall

A nested function that uses variables of the enclosing function is a *closure*: Python stores those variables in cells shared between the two functions, so the inner function keeps them alive after the outer one returns. The cells hold variables, not values: the inner function reads the variable's current value when it runs. That is why functions created in a loop all see the loop variable's final value.

```python
def make_counter():
    count = 0
    def increment():
        nonlocal count                 # without it, count += 1 would make count local
        count += 1
        return count
    return increment

counter = make_counter()
counter()
assert counter() == 2
assert counter.__code__.co_freevars == ("count",)
assert counter.__closure__[0].cell_contents == 2

multipliers = [lambda x: x * i for i in range(3)]
assert [f(10) for f in multipliers] == [20, 20, 20]       # every lambda sees the final i

multipliers = [lambda x, i=i: x * i for i in range(3)]    # fix 1: bind the value as a default
assert [f(10) for f in multipliers] == [0, 10, 20]

from functools import partial
from operator import mul
multipliers = [partial(mul, i) for i in range(3)]         # fix 2: partial stores the value
assert [f(10) for f in multipliers] == [0, 10, 20]
```

Closures and small classes are interchangeable ways to keep state with behavior. A closure is lighter for one operation; a class is clearer once there are several operations or the state should be inspectable.

### 49a.15.6 `lambda`

`lambda params: expression` creates an anonymous function whose body is a single expression: no statements, no annotations, and the name `<lambda>` in tracebacks. Use it for short keys and callbacks. Do not assign a lambda to a name (write a `def`, which gives the function a real name), and do not wrap a function that you could pass directly: `key=lambda s: len(s)` is just `key=len`.

```python
files = [{"name": "b.txt", "size": 300}, {"name": "a.txt", "size": 120}]
assert [f["name"] for f in sorted(files, key=lambda f: f["size"])] == ["a.txt", "b.txt"]
assert (lambda: 0).__name__ == "<lambda>"
assert sorted(["ccc", "a", "bb"], key=len) == ["a", "bb", "ccc"]   # no lambda needed
```

### 49a.15.7 Recursion and the recursion limit

Each call uses a frame, and the interpreter stops runaway recursion at a limit (1,000 by default, `sys.getrecursionlimit()`) with `RecursionError`; Python does not optimize tail calls. For deep structures (long linked lists, degenerate trees), use a loop with an explicit stack. `sys.setrecursionlimit` raises the limit, and since 3.11 Python-to-Python calls no longer consume C stack, but recursion through C code (a `functools.cache` wrapper, a `key=` function) still does, so the loop remains the robust fix.

```python
import sys

def depth_recursive(node):
    return 0 if node is None else 1 + depth_recursive(node[1])

def depth_iterative(node):
    depth = 0
    while node is not None:            # the explicit loop has no frame limit
        depth, node = depth + 1, node[1]
    return depth

chain = None
for value in range(5_000):
    chain = (value, chain)             # a linked list 5,000 nodes deep

assert sys.getrecursionlimit() == 1000
try:
    depth_recursive(chain)
except RecursionError:
    pass
assert depth_iterative(chain) == 5_000
```

### 49a.15.8 Docstrings and annotations

A docstring is the first statement of a module, class or function when it is a string literal; it lands in `__doc__` and is what `help()` shows. By the PEP 257 convention it starts with a one-line imperative summary ("Return the..."), then a blank line and the details. Annotations are stored in `__annotations__` and not checked by the interpreter (49a.16).

Python 3.13 strips the common leading indentation from docstrings at compile time, which shrinks `.pyc` files and changes what `__doc__` contains; `inspect.getdoc` gives the cleaned text on every version.

```python
import inspect
import sys

def documented():
    """Summary line.

    Details indented by four spaces.
    """

lines = documented.__doc__.splitlines()
if sys.version_info >= (3, 13):
    assert lines[2] == "Details indented by four spaces."       # 3.13+: indentation removed
else:
    assert lines[2] == "    Details indented by four spaces."
assert inspect.getdoc(documented).splitlines()[2] == "Details indented by four spaces."
```

## 49a.16 Type hints for real code

Type hints are annotations that tools read: static checkers (mypy, pyright), editors and some runtime libraries (`dataclasses`, Pydantic). The interpreter stores them and otherwise ignores them, so a wrong type is not a run-time error unless a library checks it. They document the contract, let a checker catch whole classes of bugs before tests run, and make refactoring safe; running a checker is part of the workflow in 49.1.

### 49a.16.1 The everyday forms

```python
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Optional, Union

def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)

def find_user(user_id: int, users: Mapping[int, str]) -> str | None:   # 3.10+ union syntax
    return users.get(user_id)

Handler = Callable[[str], bool]          # a plain assignment works as an alias on every version

def keep(handler: Handler, items: Iterable[str]) -> list[str]:   # built-in generics: 3.9+
    return [item for item in items if handler(item)]

def double(n: int) -> int:
    return n * 2

assert keep(str.isupper, ["A", "b"]) == ["A"] and mean([1, 2]) == 1.5
assert double("ab") == "abab"            # not checked at run time: a checker would flag this call
assert isinstance(3, int | str)          # unions work with isinstance since 3.10
assert Optional[int] == Union[int, None] == (int | None)
coordinates: dict[str, tuple[float, float]] = {"berlin": (52.52, 13.40)}
anything: Any = object()                 # Any switches checking off; object accepts anything but allows little
```

Use the abstract types from `collections.abc` for parameters (`Iterable`, `Sequence`, `Mapping`) so callers can pass any suitable container, and concrete types for return values (`list[str]`). `X | None` (3.10) is the modern spelling of `Optional[X]`; in 3.14 `typing.Union` and `types.UnionType` became the same class, so both spellings now print as `int | None`.

### 49a.16.2 Generics: `TypeVar` and the 3.12 syntax

A type variable says "the same type here as there": a function that returns the first item of a sequence of `T` returns a `T`. Before 3.12, type variables are declared as module-level objects; 3.12 (PEP 695) added a dedicated syntax with square brackets after the function or class name, and a `type` statement for aliases that are evaluated lazily, so they can refer to themselves.

```python
from collections.abc import Sequence
from typing import Generic, TypeVar

T = TypeVar("T")
N = TypeVar("N", int, float)              # constrained: int or float
S = TypeVar("S", bound=Sequence)          # bounded: any Sequence subtype

def first(items: Sequence[T]) -> T:
    return items[0]

class Box(Generic[T]):                    # a generic class before 3.12
    def __init__(self, item: T) -> None:
        self.item = item

assert Box[int](1).item == 1 and first("xyz") == "x"
```

```python
# requires: 3.12
from collections.abc import Sequence

def first[T](items: Sequence[T]) -> T:            # the type parameter is declared inline
    return items[0]

def clamp[N: (int, float)](value: N, low: N, high: N) -> N:   # constrained
    return max(low, min(value, high))

def longest[S: Sequence](a: S, b: S) -> S:        # bounded
    return a if len(a) >= len(b) else b

class Box[T]:                                     # a generic class: no Generic[T] base needed
    def __init__(self, item: T) -> None:
        self.item = item

type Pair[T] = tuple[T, T]                        # a lazily evaluated generic alias
type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None   # recursive, no quotes

assert Box[int](1).item == 1 and first("xyz") == "x"
assert clamp(15, 0, 10) == 10 and longest([1, 2], [3]) == [1, 2]
assert type(Pair).__name__ == "TypeAliasType" and Pair.__value__.__origin__ is tuple
assert first.__type_params__[0].__name__ == "T"
```

### 49a.16.3 `Protocol`: structural typing

A `Protocol` describes the methods an object must have, without requiring inheritance: any class with a matching `render()` method satisfies `Renderable`. This is duck typing (49a.18) made checkable. `@runtime_checkable` lets `isinstance` test for the methods' presence, not their signatures.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str: ...

class Badge:                           # does not inherit from Renderable
    def __init__(self, label: str) -> None:
        self.label = label

    def render(self) -> str:
        return f"[{self.label}]"

def page(parts: list[Renderable]) -> str:
    return " ".join(part.render() for part in parts)

assert page([Badge("new"), Badge("beta")]) == "[new] [beta]"
assert isinstance(Badge("x"), Renderable) and not isinstance("text", Renderable)
```

### 49a.16.4 `TypedDict`, `Literal`, `Final`, `ClassVar`, `Self`, `overload`

```python
from typing import ClassVar, Final, Literal, NotRequired, Self, TypedDict, overload

class ToolCall(TypedDict):               # the shape of a JSON object
    name: str
    arguments: dict[str, object]
    mode: NotRequired[Literal["auto", "manual"]]   # NotRequired: 3.11+

call: ToolCall = {"name": "search", "arguments": {"q": "python"}}
assert type(call) is dict                # at run time a TypedDict value is a plain dict
assert ToolCall.__required_keys__ == frozenset({"name", "arguments"})

class Tally:
    instances: ClassVar[int] = 0         # a class attribute, not an instance field
    LIMIT: Final = 100                   # the checker rejects reassignment

    def __init__(self) -> None:
        self.value = 0
        Tally.instances += 1

    def increment(self) -> Self:         # 3.11+: "the type of the receiver", also in subclasses
        self.value += 1
        return self

assert Tally().increment().increment().value == 2 and Tally.instances == 1

@overload
def to_bytes(data: str) -> bytes: ...
@overload
def to_bytes(data: None) -> None: ...
def to_bytes(data):                      # the one implementation that runs
    return None if data is None else data.encode()

assert to_bytes("hi") == b"hi" and to_bytes(None) is None
```

`@overload` lets the checker know that the return type depends on the argument types; only the final undecorated definition exists at run time. `Literal` restricts a value to listed constants and pairs well with `match`. `Final` and `ClassVar` are instructions to the checker, not run-time protections.

### 49a.16.5 `ParamSpec`, `TYPE_CHECKING`, `assert_never` and friends

`ParamSpec` (3.10) lets a decorator declare that its wrapper takes exactly the parameters of the wrapped function, so checkers keep the signature (49a.20). `TYPE_CHECKING` is `False` at run time and `True` for checkers, which is how you import a type only for annotations and avoid an import cycle. `assert_never` (3.11) marks code a checker should prove unreachable, which gives exhaustiveness checks over `Literal` values and enums.

```python
import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, ParamSpec, TypeVar, assert_never

if TYPE_CHECKING:
    from decimal import Decimal           # imported for the checker only

P = ParamSpec("P")
R = TypeVar("R")

def logged(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper

@logged
def total(prices: "list[Decimal]") -> "Decimal | int":
    return sum(prices)

assert total([]) == 0 and total.__name__ == "total"

def area(shape: Literal["square", "circle"], size: float) -> float:
    if shape == "square":
        return size * size
    elif shape == "circle":
        return 3.14159 * size * size
    else:
        assert_never(shape)               # unreachable for the checker; raises if reached

try:
    area("hexagon", 1.0)                  # a checker rejects this call; at run time it raises
except AssertionError:
    pass
```

Others worth recognizing: `Annotated[int, metadata]` (3.9) attaches metadata that Pydantic reads; `NewType` makes a distinct type name at no run-time cost; `typing.cast` tells the checker to trust you; `@typing.override` (3.12) verifies that a method really overrides one; `TypeIs` (3.13) writes narrowing functions; `warnings.deprecated` (3.13) marks deprecated APIs for the checker and at run time.

### 49a.16.6 Annotations at run time, and the 3.14 change

Up to 3.13, annotations on functions and classes are evaluated when the `def` or `class` statement runs, so a name used in an annotation must already exist; forward references have to be quoted strings, or the module starts with `from __future__ import annotations` (PEP 563), which stores every annotation as a string. Python 3.14 (PEP 649 and PEP 749) makes evaluation lazy: annotations are computed only when something asks for them, so forward references work without quotes and defining annotations costs almost nothing. The new `annotationlib` module reads them in three formats: `VALUE` (evaluate, as before), `FORWARDREF` (evaluate what is defined and leave markers for the rest) and `STRING`.

```python
import sys
from typing import get_type_hints

class Order:
    total: "float"                        # a quoted forward reference
    items: list[str]

assert get_type_hints(Order) == {"total": float, "items": list[str]}   # resolves the strings

try:
    def handler(event: UndefinedEvent) -> None:   # needs the name at definition time before 3.14
        pass
    defined = True
except NameError:
    defined = False
assert defined == (sys.version_info >= (3, 14))
```

```python
# requires: 3.14
import annotationlib

class Node:
    def __init__(self, value: int, next: Node | None = None) -> None:   # no quotes needed
        self.value = value
        self.next = next

assert annotationlib.get_annotations(Node.__init__)["next"] == Node | None

def handler(event: UndefinedEvent) -> None:      # defining it is fine: nothing is evaluated yet
    pass

try:
    handler.__annotations__                       # evaluating it is not
except NameError:
    pass
strings = annotationlib.get_annotations(handler, format=annotationlib.Format.STRING)
assert strings == {"event": "UndefinedEvent", "return": "None"}
with_refs = annotationlib.get_annotations(handler, format=annotationlib.Format.FORWARDREF)
assert with_refs["return"] is None and type(with_refs["event"]).__name__ == "ForwardRef"
```

```python
from __future__ import annotations          # PEP 563: every annotation is stored as a string

def area(shape: Shape) -> float:            # Shape does not exist, and nothing evaluates it
    return 0.0

assert area.__annotations__ == {"shape": "Shape", "return": "float"}
```

`from __future__ import annotations` still works in 3.14 and keeps its string behavior; PEP 749 plans to deprecate it once the last version without lazy annotations (3.13) reaches end of life, and to remove it later. New code that targets 3.14 and later does not need it.

## 49a.17 Classes and objects

A `class` statement runs its body once, collects the names it defines into a namespace, and creates a class object from it. Instances are created by calling the class. Attribute lookup on an instance checks the instance's own `__dict__` and then the class and its bases, in method resolution order (49a.18.2), with descriptors (49a.18.9) adding the details.

### 49a.17.1 Class attributes, instance attributes, and the shared mutable pitfall

Names assigned in the class body are class attributes, shared by every instance. `self.name = ...` inside a method creates an instance attribute in that object's `__dict__`. Assigning to an attribute through an instance always creates or updates an instance attribute, which shadows a class attribute of the same name; mutating a class attribute through an instance changes the shared object.

```python
class Session:
    timeout = 30                   # class attribute: one value shared by all instances
    headers = {}                   # pitfall: one dict shared by all instances

    def __init__(self, user):
        self.user = user           # instance attribute, stored in this object's __dict__

ana, bo = Session("ana"), Session("bo")
assert ana.timeout == bo.timeout == Session.timeout
assert vars(ana) == {"user": "ana"}           # the instance stores only its own attributes

ana.headers["Authorization"] = "token-ana"    # mutates the shared dict...
assert bo.headers == {"Authorization": "token-ana"}   # ...so bo now sends ana's token

ana.timeout = 5                               # assignment creates an instance attribute
assert bo.timeout == 30 and vars(ana)["timeout"] == 5
del ana.timeout                               # remove the shadow
assert ana.timeout == 30
```

The fix for per-instance containers is to create them in `__init__` (`self.headers = {}`). Class attributes are right for constants, defaults that are immutable, and counters you update deliberately through the class (`Session.count += 1`).

### 49a.17.2 `__init__` and `__new__`

Calling `Cls(args)` runs `Cls.__new__(Cls, args)` to create the object and then, if it returned an instance of `Cls`, `__init__(obj, args)` to initialize it. You almost always write only `__init__`, which must return `None`. Override `__new__` when the value must be fixed at creation, which is the case for subclasses of immutable types such as `int`, `float`, `str` and `tuple`, and for instance caching.

```python
class Celsius(float):
    def __new__(cls, degrees):
        if degrees < -273.15:
            raise ValueError("below absolute zero")
        return super().__new__(cls, degrees)   # an immutable value is set in __new__

assert Celsius(21.5) + 1 == 22.5 and isinstance(Celsius(0), float)
try:
    Celsius(-300)
except ValueError:
    pass
```

### 49a.17.3 Instance methods, class methods and static methods

An instance method receives the instance (`self`). A `@classmethod` receives the class (`cls`) and is the idiomatic alternative constructor, because `cls` is the subclass when called on one. A `@staticmethod` receives nothing implicitly; it is a plain function in the class namespace, and a module-level function is often clearer.

```python
from datetime import date

class Invoice:
    tax_rate = 0.2

    def __init__(self, number: str, amount: float, issued: date):
        self.number = number
        self.amount = amount
        self.issued = issued

    def total(self) -> float:                      # needs the instance
        return round(self.amount * (1 + self.tax_rate), 2)

    @classmethod
    def from_line(cls, line: str) -> "Invoice":    # gets the class: an alternative constructor
        number, amount, issued = line.split(";")
        return cls(number, float(amount), date.fromisoformat(issued))

    @staticmethod
    def is_valid_number(number: str) -> bool:      # neither self nor cls
        return number.startswith("INV-") and number[4:].isdigit()

class ExportInvoice(Invoice):
    tax_rate = 0.0

inv = ExportInvoice.from_line("INV-7;100.0;2026-10-01")
assert type(inv) is ExportInvoice and inv.total() == 100.0      # cls was the subclass
assert Invoice.is_valid_number("INV-42") and not Invoice.is_valid_number("42")
bound = inv.total
assert bound.__self__ is inv and bound.__func__ is Invoice.total  # a bound method = function + instance
assert Invoice.total(inv) == inv.total()                          # the explicit form of the same call
```

### 49a.17.4 Public, "protected" and "private"

Python has no access modifiers; it has conventions and one mechanism.

- `name`: public, part of the class's interface.
- `_name`: internal by convention ("protected"). Nothing stops access, but callers who use it accept that it may change; `from module import *` skips module-level names that start with an underscore.
- `__name` (two leading underscores, at most one trailing): **name mangling**. Inside a class body, the compiler rewrites it to `_ClassName__name`. The purpose is to stop a subclass from clobbering its parent's attribute by accident, not to hide anything.
- `__name__`: reserved for the language's special names; do not invent new ones.

```python
class Account:
    def __init__(self, owner, balance):
        self.owner = owner                 # public
        self._audit = []                   # internal by convention
        self.__balance = balance           # stored as _Account__balance

    def balance(self):
        return self.__balance              # inside the class body the short name works

class SavingsAccount(Account):
    def __init__(self, owner, balance):
        super().__init__(owner, balance)
        self.__balance = "the subclass's own"   # stored as _SavingsAccount__balance: no clash

acct = SavingsAccount("ana", 100)
assert acct.balance() == 100
assert sorted(vars(acct)) == ["_Account__balance", "_SavingsAccount__balance", "_audit", "owner"]
try:
    acct.__balance                         # outside a class body nothing is rewritten
except AttributeError:
    pass
assert acct._Account__balance == 100       # "private" is reachable by its mangled name
```

### 49a.17.5 Properties: computed attributes, validation and read-only access

`@property` turns a method into an attribute read; `@x.setter` and `@x.deleter` handle assignment and `del`. Start with plain public attributes; if you later need validation or computation, switch to a property and no caller changes. That is why Python code does not write `get_x()` and `set_x()` methods.

```python
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius               # goes through the setter, so it is validated

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._celsius = value

    @celsius.deleter
    def celsius(self):
        del self._celsius

    @property
    def fahrenheit(self):                    # computed and read-only
        return self._celsius * 9 / 5 + 32

t = Temperature(25)
assert t.fahrenheit == 77.0
t.celsius = 30
assert t.fahrenheit == 86.0
try:
    t.celsius = -300
except ValueError:
    pass
try:
    t.fahrenheit = 0                         # no setter: read-only
except AttributeError:
    pass
del t.celsius
assert not hasattr(t, "_celsius")
```

### 49a.17.6 `__slots__`

Declaring `__slots__ = ("x", "y")` gives instances fixed storage for those attributes and no per-instance `__dict__`. Instances are smaller, attribute access is slightly faster, and a misspelled assignment raises instead of creating a new attribute. The costs: no new attributes, no `__weakref__` unless you list it, a subclass without its own `__slots__` gets a `__dict__` back, and two bases with non-empty slots cannot be combined. Use slots for classes with many instances (graph nodes, records); `@dataclass(slots=True)` (3.10) generates them for you.

```python
import sys

class PointDict:
    def __init__(self, x, y):
        self.x, self.y = x, y

class PointSlots:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y

a, b = PointDict(1, 2), PointSlots(1, 2)
assert hasattr(a, "__dict__") and not hasattr(b, "__dict__")
assert sys.getsizeof(b) < sys.getsizeof(a) + sys.getsizeof(a.__dict__)
try:
    b.z = 3                                  # no slot named z
except AttributeError:
    pass
```

### 49a.17.7 `__repr__` and `__str__`

`repr(obj)` is for developers: unambiguous, ideally a valid constructor call. The REPL, debuggers, logs of containers and `f"{obj!r}"` use it. `str(obj)` is for end users and falls back to `__repr__` when not defined. Always define `__repr__`; define `__str__` only when users see the object.

```python
class Money:
    def __init__(self, amount, currency):
        self.amount, self.currency = amount, currency

    def __repr__(self):
        return f"{type(self).__name__}({self.amount!r}, {self.currency!r})"

    def __str__(self):
        return f"{self.amount} {self.currency}"

m = Money("12.50", "EUR")
assert repr(m) == "Money('12.50', 'EUR')" and str(m) == "12.50 EUR"
assert f"{m}" == "12.50 EUR" and f"{m!r}" == "Money('12.50', 'EUR')"
assert str([m]) == "[Money('12.50', 'EUR')]"      # containers show their items' repr
```

### 49a.17.8 Equality, hashing and ordering

By default, objects are equal only to themselves and hash by identity. Defining `__eq__` sets `__hash__` to `None`, because the identity hash would break the rule that equal objects hash equally. To keep instances hashable, define `__hash__` from the fields that `__eq__` compares, and keep those fields immutable. Comparison methods return `NotImplemented` (not `False`) for types they do not handle, so that Python can try the other operand's method. `functools.total_ordering` derives the remaining comparisons from `__eq__` and one of `__lt__`, `__le__`, `__gt__`, `__ge__`.

```python
from functools import total_ordering

@total_ordering
class Version:
    def __init__(self, text):
        self.parts = tuple(int(p) for p in text.split("."))

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented            # let the other side try
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)              # the same fields as __eq__

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.parts < other.parts

    def __repr__(self):
        return f"Version({'.'.join(map(str, self.parts))!r})"

assert Version("3.10.1") > Version("3.9.18")      # numeric, unlike comparing the strings:
assert "3.10.1" < "3.9.18"
assert sorted([Version("3.14"), Version("3.8"), Version("3.12")]) == [
    Version("3.8"), Version("3.12"), Version("3.14")]
assert len({Version("1.0"), Version("1.0")}) == 1  # hashable, so sets deduplicate
assert Version("1.0") != "1.0"                     # NotImplemented on both sides: not equal
try:
    Version("1.0") < "2.0"                         # NotImplemented on both sides: TypeError
except TypeError:
    pass

class OnlyEq:
    def __eq__(self, other):
        return True

assert OnlyEq.__hash__ is None                     # __eq__ without __hash__: unhashable
```

### 49a.17.9 The container protocol

A class becomes a container by implementing `__len__`, `__getitem__` (which receives an `int` or a `slice`), `__contains__` and `__iter__` (plus `__setitem__` and `__delitem__` if it is mutable). Missing methods have fallbacks: `in` and iteration work with only `__getitem__`, by trying indexes from 0 until `IndexError`; `reversed()` works with `__len__` and `__getitem__`. Inheriting from the ABCs in `collections.abc` (49a.18.4) fills in the rest systematically.

```python
class Playlist:
    def __init__(self, songs):
        self._songs = list(songs)

    def __len__(self):
        return len(self._songs)

    def __getitem__(self, index):           # ints and slices
        if isinstance(index, slice):
            return Playlist(self._songs[index])
        return self._songs[index]

    def __contains__(self, song):
        return song in self._songs

    def __iter__(self):
        return iter(self._songs)

    def __repr__(self):
        return f"Playlist({self._songs!r})"

p = Playlist(["intro", "verse", "outro"])
assert len(p) == 3 and p[0] == "intro" and p[-1] == "outro"
assert isinstance(p[1:], Playlist) and list(p[1:]) == ["verse", "outro"]
assert "verse" in p and list(reversed(p)) == ["outro", "verse", "intro"]

class Squares:                              # only __getitem__: the legacy iteration protocol
    def __getitem__(self, i):
        if i >= 5:
            raise IndexError(i)
        return i * i

assert list(Squares()) == [0, 1, 4, 9, 16] and 9 in Squares()
```

### 49a.17.10 Callable objects

An instance whose class defines `__call__` can be called like a function while keeping state between calls: configured strategies, rate limiters, caches, and the class-based decorators in 49a.20.

```python
class RateLimiter:
    def __init__(self, max_calls):
        self.max_calls = max_calls
        self.calls = 0

    def __call__(self, action):
        if self.calls >= self.max_calls:
            return "rejected"
        self.calls += 1
        return action()

limit = RateLimiter(max_calls=2)
assert [limit(lambda: "ok") for _ in range(3)] == ["ok", "ok", "rejected"]
assert callable(limit) and callable(len) and not callable(3)
```

### 49a.17.11 Operator overloading

`a + b` calls `a.__add__(b)`; if that method is missing or returns `NotImplemented`, Python calls `b.__radd__(a)`; if both decline, it raises `TypeError`. (When the right operand's type is a subclass of the left operand's type and overrides the reflected method, that method is tried first.) `a += b` calls `__iadd__`, which should mutate and return `self`, and falls back to `__add__`. Unary operators map to `__neg__`, `__pos__`, `__abs__` and `__invert__`, and truth to `__bool__`. `sum()` starts from `0`, so a class that should be summable needs `__radd__` to accept `0`.

```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

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

    def __radd__(self, other):              # sum() starts from 0
        return self if other == 0 else self.__add__(other)

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__                      # 3 * v becomes v.__rmul__(3)

v = Vector(3, 4)
assert v + Vector(1, 1) == Vector(4, 5) and v * 2 == 2 * v == Vector(6, 8)
assert sum([Vector(1, 0), Vector(0, 1)]) == Vector(1, 1)
try:
    v + 1                                    # both sides return NotImplemented
except TypeError:
    pass
v += Vector(1, 1)                            # no __iadd__: falls back to __add__ and rebinds v
assert v == Vector(4, 5)
```

Lab exercise 24 completes this class with subtraction, unary minus, `abs`, truth and unpacking.

### 49a.17.12 Dataclasses

`@dataclass` (3.7) reads the class's annotated fields and generates `__init__`, `__repr__` and `__eq__`. Options add more: `frozen=True` makes instances immutable and hashable, `order=True` generates comparisons that compare fields as a tuple, `slots=True` and `kw_only=True` (both 3.10) add slots and keyword-only parameters. `field()` customizes one field: `default_factory` for mutable defaults (a plain mutable default is rejected), `repr=False`, `compare=False`. `__post_init__` runs after the generated `__init__`, for validation and derived fields. `dataclasses.replace` (and `copy.replace` in 3.13) builds a modified copy.

```python
from dataclasses import FrozenInstanceError, asdict, dataclass, field, replace

@dataclass
class Task:
    title: str
    priority: int = 3
    tags: list[str] = field(default_factory=list)            # a new list per instance
    notes: str = field(default="", repr=False, compare=False)

    def __post_init__(self):                                   # validation
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be 1..5")

t = Task("write tests", tags=["qa"])
assert repr(t) == "Task(title='write tests', priority=3, tags=['qa'])"
assert t == Task("write tests", 3, ["qa"], notes="ignored by ==")
assert asdict(t) == {"title": "write tests", "priority": 3, "tags": ["qa"], "notes": ""}
assert Task.__hash__ is None                  # eq=True without frozen: unhashable
try:
    Task("bad", priority=9)
except ValueError:
    pass
try:
    @dataclass
    class Broken:
        items: list = []                      # rejected when the class is created
except ValueError as err:
    assert "default_factory" in str(err)

@dataclass(frozen=True, order=True, slots=True)
class Release:
    major: int
    minor: int
    label: str = field(default="", compare=False)

r = Release(3, 14)
assert Release(3, 9) < Release(3, 14) < Release(4, 0)       # compared as (major, minor)
assert replace(r, minor=15) == Release(3, 15) and r.minor == 14
assert len({Release(3, 14), Release(3, 14, "final")}) == 1  # hashable; label is not compared
try:
    r.minor = 15
except FrozenInstanceError:
    pass
assert not hasattr(r, "__dict__")

@dataclass(kw_only=True)
class Config:
    host: str
    port: int = 8080

assert Config(host="localhost").port == 8080
try:
    Config("localhost")                       # keyword-only: names are required
except TypeError:
    pass
```

For untrusted input (JSON, LLM output), parse and validate with Pydantic at the boundary (49.1) and use dataclasses inside.

### 49a.17.13 Enums

An `Enum` is a fixed set of named singleton members, each with a `name` and a `value`. Members are looked up by value (`Status("done")`) or by name (`Status["DONE"]`), iterate in definition order, and compare by identity; a plain `Enum` member never equals its raw value. `IntEnum` and (3.11) `StrEnum` members are also `int` or `str` and compare equal to their values, which helps at JSON and database boundaries. `Flag` combines members with bitwise operators. `auto()` picks values, and `@unique` rejects duplicate values.

```python
from enum import Enum, Flag, IntEnum, StrEnum, auto, unique

@unique
class Status(Enum):
    PENDING = "pending"
    DONE = "done"

    @property
    def is_final(self):
        return self is Status.DONE

assert Status("done") is Status.DONE and Status["PENDING"] is Status.PENDING
assert Status.DONE.name == "DONE" and Status.DONE.value == "done"
assert Status.DONE != "done"                         # a plain Enum never equals its value
assert [s.name for s in Status] == ["PENDING", "DONE"] and Status.DONE.is_final

class Priority(IntEnum):
    LOW = 1
    HIGH = 2

assert Priority.HIGH > Priority.LOW and Priority.HIGH == 2

class Mode(StrEnum):                                 # 3.11+
    READ = auto()                                    # in a StrEnum, auto() is the lowercased name
    WRITE = auto()

assert Mode.READ == "read" and f"{Mode.WRITE}" == "write"

class Channel(Flag):
    EMAIL = auto()                                   # 1, 2, 4: one bit per member
    SMS = auto()
    PUSH = auto()

alerts = Channel.EMAIL | Channel.PUSH
assert Channel.EMAIL in alerts and Channel.SMS not in alerts and alerts.value == 5
```

## 49a.18 Inheritance, class hierarchies and polymorphism

### 49a.18.1 Single inheritance and overriding

A subclass inherits every attribute of its base classes and overrides one by defining the same name. Inside a method, `self.method()` always dispatches on the instance's actual class, so a base-class method that calls `self.format()` uses the subclass's override; that is the template-method idea in one line. `super().method()` calls the next implementation up the hierarchy. Every class ultimately inherits from `object`.

```python
class Notifier:
    def __init__(self, recipient):
        self.recipient = recipient

    def format(self, message):
        return f"To {self.recipient}: {message}"

    def send(self, message):
        return self.format(message)            # dispatches on the actual class of self

class UrgentNotifier(Notifier):
    def format(self, message):                 # override, extending the parent's version
        return super().format(message.upper()) + " [urgent]"

n = UrgentNotifier("ops")
assert n.send("disk full") == "To ops: DISK FULL [urgent]"
assert isinstance(n, Notifier) and issubclass(UrgentNotifier, Notifier)
assert UrgentNotifier.__bases__ == (Notifier,) and issubclass(Notifier, object)
```

### 49a.18.2 Multiple inheritance, the MRO, and cooperative `super()`

With several base classes, Python linearizes the hierarchy into one list, the **method resolution order** (`Cls.__mro__`), and every attribute lookup walks it from left to right. The list comes from the **C3 linearization**, which guarantees three things: a class comes before its bases, the bases keep the order written in the `class` statement, and the order of every base's own MRO is preserved. If no list satisfies all three, the class statement fails.

`super()` does not mean "my parent". It means "the next class after this one in the MRO of the instance's type". That is what makes *cooperative* multiple inheritance work: if every `__init__` in a diamond calls `super().__init__(**kwargs)` exactly once and takes the keyword arguments it understands, each class's initializer runs exactly once, in MRO order.

```python
class Base:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)              # object.__init__: kwargs must be used up by now
        self.calls = ["Base"]

class Logging(Base):
    def __init__(self, *, log_level="info", **kwargs):
        super().__init__(**kwargs)              # in a Service, the next class is Caching, not Base
        self.calls.append("Logging")
        self.log_level = log_level

class Caching(Base):
    def __init__(self, *, cache_size=128, **kwargs):
        super().__init__(**kwargs)
        self.calls.append("Caching")
        self.cache_size = cache_size

class Service(Logging, Caching):
    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.calls.append("Service")
        self.name = name

s = Service("api", log_level="debug", cache_size=10)
assert [c.__name__ for c in Service.__mro__] == ["Service", "Logging", "Caching", "Base", "object"]
assert s.calls == ["Base", "Caching", "Logging", "Service"]   # each __init__ ran once
assert (s.log_level, s.cache_size) == ("debug", 10)
```

To compute it by hand, C3 merges the parents' MROs and the list of bases: it repeatedly takes the first head of those lists that does not appear in the tail of any list, and gives up when no head qualifies.

```python
class Root: pass
class Left(Root): pass
class Right(Root): pass
class Mixin: pass
class Leaf(Left, Mixin, Right): pass

assert [c.__name__ for c in Leaf.__mro__] == ["Leaf", "Left", "Mixin", "Right", "Root", "object"]

class A: pass
class B(A): pass
try:
    class C(A, B):            # A must precede B (base order) and follow it (B's own MRO)
        pass
except TypeError as err:
    assert "consistent method resolution" in str(err)
```

### 49a.18.3 Abstract base classes

An abstract base class (`abc.ABC`) declares methods with `@abstractmethod`; a class with any unimplemented abstract method cannot be instantiated, so a missing implementation fails at construction instead of deep inside a call. ABCs can also carry concrete methods built on the abstract ones.

```python
import math
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    def describe(self) -> str:                    # concrete, built on the abstract method
        return f"{type(self).__name__} with area {self.area():.2f}"

class Circle(Shape):
    def __init__(self, r):
        self.r = r

    def area(self):
        return math.pi * self.r ** 2

class Square(Shape):
    def __init__(self, side):
        self.side = side

    def area(self):
        return self.side ** 2

class Incomplete(Shape):
    pass

for abstract in (Shape, Incomplete):
    try:
        abstract()
    except TypeError as err:
        assert "abstract" in str(err)

shapes = [Circle(1), Square(2)]
assert [s.describe() for s in shapes] == ["Circle with area 3.14", "Square with area 4.00"]
assert sum(s.area() for s in shapes) == math.pi + 4      # one call, many implementations
```

### 49a.18.4 Implementing `collections.abc` interfaces

The ABCs in `collections.abc` define the standard container interfaces and supply most methods once you implement a few. Inherit from `Mapping` and write `__getitem__`, `__iter__` and `__len__`, and you get `get`, `keys`, `items`, `values`, `__contains__` and `__eq__`; `MutableMapping` adds `__setitem__` and `__delitem__` and gives you `pop`, `popitem`, `setdefault`, `update` and `clear`. `Sequence` needs `__getitem__` and `__len__` and supplies `__contains__`, `__iter__`, `__reversed__`, `index` and `count`.

This is also the safe way to build a custom dict (`collections.UserDict` is the other). Subclassing `dict` directly is a trap, because its C-implemented methods (`__init__`, `update`, `setdefault`) do not call your overridden `__setitem__`.

```python
from collections.abc import Iterable, MutableMapping, Sequence, Sized

class CaseInsensitiveDict(MutableMapping):
    """A mapping whose string keys ignore case; it remembers the last spelling used."""

    def __init__(self, data=(), **kwargs):
        self._store = {}                         # casefolded key -> (original key, value)
        self.update(data, **kwargs)              # update() comes from MutableMapping

    def __getitem__(self, key):
        return self._store[key.casefold()][1]

    def __setitem__(self, key, value):
        self._store[key.casefold()] = (key, value)

    def __delitem__(self, key):
        del self._store[key.casefold()]

    def __iter__(self):
        return (original for original, _ in self._store.values())

    def __len__(self):
        return len(self._store)

headers = CaseInsensitiveDict({"Content-Type": "json"}, Accept="text")
assert headers["content-type"] == "json" and "ACCEPT" in headers
assert headers.get("x-missing", "none") == "none"           # from Mapping
headers.setdefault("X-Trace", "abc")                         # from MutableMapping
assert sorted(headers) == ["Accept", "Content-Type", "X-Trace"]
assert headers.pop("accept") == "text" and len(headers) == 2
assert headers == {"Content-Type": "json", "X-Trace": "abc"}

class LowerDict(dict):                       # the trap
    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

d = LowerDict(A=1)                           # dict.__init__ ignores the override
d["B"] = 2
d.update(C=3)                                # so does dict.update
assert d == {"A": 1, "b": 2, "C": 3}

assert isinstance(headers, MutableMapping) and not isinstance(headers, dict)
assert isinstance([], Iterable) and isinstance("", Sized) and not isinstance({}, Sequence)
```

`isinstance([], Iterable)` is true even though `list` does not inherit from `Iterable`: some ABCs (`Iterable`, `Sized`, `Hashable`, `Callable` and others) recognize any class that has the right method, through a `__subclasshook__`. Others, such as `Sequence` and `Mapping`, need inheritance or an explicit `register()` call.

### 49a.18.5 Polymorphism: duck typing, ABCs, Protocols, operators and `singledispatch`

Polymorphism means one interface, many implementations. Python offers five ways to get it:

| Mechanism | How a type qualifies | Checked by |
|---|---|---|
| Duck typing | it has the method that gets called | nothing until the call |
| ABC (`abc.ABC`, `collections.abc`) | inherits or is registered | `isinstance`, instantiation |
| `typing.Protocol` | has methods with matching signatures (49a.16.3) | the static checker (and `isinstance` with `@runtime_checkable`) |
| Operator overloading | implements special methods (49a.17.11) | the operator itself |
| `functools.singledispatch` | a function registered for its type | dispatch on the first argument's type |

`singledispatch` overloads a function on the type of its first argument, which is useful when you cannot add methods to the types involved (built-ins, third-party classes); `singledispatchmethod` does the same for methods.

```python
import io
import json
from datetime import date
from decimal import Decimal
from functools import singledispatch

def save(report, stream):                 # duck typing: anything with .write() works
    stream.write(report)

buffer = io.StringIO()
save("ok", buffer)
assert buffer.getvalue() == "ok"

@singledispatch
def to_json(value):
    raise TypeError(f"cannot serialize {type(value).__name__}")

@to_json.register
def _(value: date):                       # the annotation selects the type
    return value.isoformat()

@to_json.register
def _(value: Decimal):
    return str(value)

@to_json.register(set)
@to_json.register(frozenset)
def _(value):
    return sorted(value)

payload = {"day": date(2026, 10, 3), "price": Decimal("9.99"), "tags": {"b", "a"}}
assert json.dumps(payload, default=to_json) == (
    '{"day": "2026-10-03", "price": "9.99", "tags": ["a", "b"]}')
try:
    to_json(object())
except TypeError:
    pass
```

### 49a.18.6 Composition versus inheritance

Inheritance says "is a" and couples the subclass to the parent's implementation: every public method of the parent becomes part of the child's interface, and changes in the parent ripple down (the fragile base class problem). Composition says "has a": the object holds a collaborator and exposes only what it means. Prefer composition for reuse, and inheritance for true subtypes and for extension points a framework designs for (an `ABC` you are meant to implement).

```python
class StackViaInheritance(list):          # every list method leaks into the interface
    push = list.append

class Stack:                              # composition: only stack operations
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop()

    def __len__(self):
        return len(self._items)

leaky = StackViaInheritance()
leaky.push(1)
leaky.insert(0, 99)                       # allowed, and LIFO order is gone
assert leaky == [99, 1]

s = Stack()
s.push(1)
assert not hasattr(s, "insert") and s.pop() == 1 and len(s) == 0
```

### 49a.18.7 Mixins

A mixin is a small class that adds one capability and is meant to be combined with others through multiple inheritance: it has no state of its own (or initializes cooperatively), does not stand alone, and goes to the left of the main base class so its methods take precedence.

```python
import json

class ReprMixin:
    def __repr__(self):
        fields = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"{type(self).__name__}({fields})"

class JsonMixin:
    def to_json(self):
        return json.dumps(vars(self), sort_keys=True)

class User(ReprMixin, JsonMixin):
    def __init__(self, name, admin=False):
        self.name, self.admin = name, admin

u = User("ana")
assert repr(u) == "User(name='ana', admin=False)"
assert u.to_json() == '{"admin": false, "name": "ana"}'
```

### 49a.18.8 `__init_subclass__`, class decorators and metaclasses

Three tools customize classes, in increasing order of power and of the surprise they cause:

1. **`__init_subclass__`** (3.6) is a class method on a base class that runs whenever a subclass is created. It handles most registry and validation needs, and keyword arguments in the `class` line reach it.
2. **Class decorators** take a class and return it (or a replacement) after the class body runs. `@dataclass` and `@total_ordering` are class decorators.
3. **Metaclasses** are the classes of classes. `type` is the default; a subclass of `type` can intercept class creation (`__new__`, `__init__`, `__prepare__`) and the behavior of the class object itself, such as what `Cls(...)` does (`__call__`). `ABCMeta`, `EnumType` and many ORMs are metaclasses. Use one only when the first two cannot do the job: metaclasses are inherited by every subclass, and two unrelated metaclasses in one hierarchy conflict.

```python
class Plugin:
    registry = {}

    def __init_subclass__(cls, /, name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry[name or cls.__name__.lower()] = cls

class CsvExporter(Plugin, name="csv"):    # the keyword reaches __init_subclass__
    pass

class JsonExporter(Plugin):
    pass

assert Plugin.registry == {"csv": CsvExporter, "jsonexporter": JsonExporter}

def register(registry):
    def decorator(cls):
        registry[cls.__name__] = cls
        return cls                        # a class decorator returns the class
    return decorator

HANDLERS = {}

@register(HANDLERS)
class Refund:
    pass

assert HANDLERS == {"Refund": Refund}

Point = type("Point", (), {"x": 0, "show": lambda self: f"x={self.x}"})   # classes are made by type
assert Point().show() == "x=0" and type(Point) is type

class InstanceCounter(type):              # a metaclass derives from type
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        cls.instances = 0

    def __call__(cls, *args, **kwargs):   # runs on Widget(...), before __new__ and __init__
        cls.instances += 1
        return super().__call__(*args, **kwargs)

class Widget(metaclass=InstanceCounter):
    pass

Widget()
Widget()
assert Widget.instances == 2 and type(Widget) is InstanceCounter
```

### 49a.18.9 Descriptors: how properties, methods and `classmethod` work

A descriptor is an object stored as a class attribute whose class defines any of `__get__`, `__set__` and `__delete__`. When you access the attribute through an instance, Python calls the descriptor instead of returning it. When the instance's `__dict__` holds the same name, the kind decides who wins: a **data descriptor** (it defines `__set__` or `__delete__`) always does, while a **non-data descriptor** (only `__get__`) loses to the instance's own entry. `__set_name__` (3.6) tells the descriptor the attribute name it was assigned to.

This one mechanism implements most of the class machinery: functions are non-data descriptors whose `__get__` returns a bound method; `property` is a data descriptor; `classmethod` binds the class instead of the instance; `staticmethod` returns the plain function; `functools.cached_property` is a non-data descriptor that stores its result in the instance `__dict__`, so the second access never reaches it.

```python
class Bounded:
    """A data descriptor that rejects values outside [low, high]: one validator, many attributes."""

    def __init__(self, low, high):
        self.low, self.high = low, high

    def __set_name__(self, owner, name):        # called once, when the owning class is created
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self                          # accessed on the class itself
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        if not self.low <= value <= self.high:
            raise ValueError(f"{self.name}={value!r} is outside [{self.low}, {self.high}]")
        obj.__dict__[self.name] = value          # same key as the attribute: a data descriptor still wins

class Order:
    quantity = Bounded(1, 1_000)
    discount = Bounded(0.0, 0.5)

    def __init__(self, quantity, discount=0.0):
        self.quantity = quantity                 # calls Bounded.__set__
        self.discount = discount

o = Order(3, 0.1)
assert (o.quantity, o.discount) == (3, 0.1) and vars(o) == {"quantity": 3, "discount": 0.1}
try:
    o.discount = 0.9
except ValueError as err:
    assert str(err) == "discount=0.9 is outside [0.0, 0.5]"
assert isinstance(Order.quantity, Bounded)
```

```python
from functools import cached_property

class Greeter:
    def hello(self):
        return f"hello from {type(self).__name__}"

    @classmethod
    def make(cls):
        return cls()

    @staticmethod
    def version():
        return 1

g = Greeter()
raw = Greeter.__dict__["hello"]                  # the plain function stored on the class
bound = raw.__get__(g, Greeter)                  # what g.hello does behind the scenes
assert bound() == "hello from Greeter" and bound.__self__ is g
assert type(Greeter.__dict__["make"].__get__(None, Greeter)()) is Greeter
assert Greeter.__dict__["version"].__get__(g, Greeter)() == 1

g.hello = lambda: "shadowed"                     # functions are non-data descriptors,
assert g.hello() == "shadowed"                   # so an instance attribute wins

class Account:
    @property
    def balance(self):
        return 100

a = Account()
a.__dict__["balance"] = 5                        # write the instance dict directly
assert a.balance == 100                          # property is a data descriptor: it wins

class Report:
    def __init__(self, rows):
        self.rows = rows
        self.computations = 0

    @cached_property
    def total(self):
        self.computations += 1
        return sum(self.rows)

r = Report([1, 2, 3])
assert r.total == 6 and r.total == 6 and r.computations == 1   # computed once
assert vars(r)["total"] == 6                                    # cached in the instance dict
del r.total                                                     # invalidate the cache
assert r.total == 6 and r.computations == 2
```

The full lookup for `obj.attr` is therefore: find `attr` along `type(obj).__mro__`; if it is a data descriptor, call its `__get__`; otherwise, if `attr` is in `obj.__dict__`, return that; otherwise, if the class attribute is a non-data descriptor, call its `__get__`; otherwise return the class attribute; and if all of that fails, call `__getattr__` if the class defines it, else raise `AttributeError`. `__getattribute__` runs on every access and is rarely worth overriding; `__getattr__` runs only on failure, which makes it the right hook for delegation:

```python
class LoggingProxy:
    def __init__(self, target):
        self._target = target
        self.accessed = []

    def __getattr__(self, name):               # called only when normal lookup fails
        self.accessed.append(name)
        return getattr(self._target, name)

proxy = LoggingProxy([3, 1, 2])
proxy.sort()
assert proxy._target == [1, 2, 3] and proxy.accessed == ["sort"]
```

## 49a.19 Iterators and generators

### 49a.19.1 Iterables, iterators and the protocol

An **iterable** is anything `iter()` accepts: an object with `__iter__` that returns an iterator (or, the legacy way, with an index-based `__getitem__`). An **iterator** is an object with `__next__`, which returns the next item or raises `StopIteration`, and an `__iter__` that returns itself. A `for` loop is this protocol in a loop:

```python
items = ["a", "b"]
iterator = iter(items)                 # calls items.__iter__()
collected = []
while True:
    try:
        item = next(iterator)          # calls iterator.__next__()
    except StopIteration:
        break
    collected.append(item)
assert collected == items

assert iter(items) is not items        # a list is iterable, not an iterator
assert iter(iterator) is iterator      # an iterator returns itself
assert next(iterator, "done") == "done"   # a default instead of StopIteration
```

Containers hand out a *fresh* iterator on every `iter()` call, which is why you can loop over a list twice; an iterator is a cursor and can be consumed only once. When you write an iterable class, keep that split: the container's `__iter__` returns a new iterator object each time.

```python
class Countdown:                       # the iterable: every iter() starts a new pass
    def __init__(self, start):
        self.start = start

    def __iter__(self):
        return CountdownIterator(self.start)

class CountdownIterator:               # the iterator: one pass, holds the position
    def __init__(self, current):
        self.current = current

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

c = Countdown(3)
assert list(c) == [3, 2, 1] and list(c) == [3, 2, 1]    # re-iterable
it = iter(c)
assert next(it) == 3 and list(it) == [2, 1] and list(it) == []
```

### 49a.19.2 Generator functions

A function that contains `yield` is a generator function: calling it runs none of its body and returns a generator, which is an iterator. Each `next()` runs the body until the next `yield`, hands out that value and freezes the frame, local variables included, until the following `next()`. A `return` (or the end of the body) raises `StopIteration`, carrying the returned value in its `value` attribute.

```python
import inspect

log = []

def countdown(start):
    log.append("started")
    while start > 0:
        yield start
        start -= 1
    return "liftoff"

gen = countdown(2)
assert log == [] and inspect.getgeneratorstate(gen) == "GEN_CREATED"   # nothing ran yet
assert next(gen) == 2 and log == ["started"]
assert inspect.getgeneratorstate(gen) == "GEN_SUSPENDED"
assert next(gen) == 1
try:
    next(gen)
except StopIteration as stop:
    assert stop.value == "liftoff"          # a generator's return value
assert inspect.getgeneratorstate(gen) == "GEN_CLOSED"

class Countdown:
    def __init__(self, start):
        self.start = start

    def __iter__(self):                     # a generator method replaces the iterator class
        yield from range(self.start, 0, -1)

assert list(Countdown(3)) == [3, 2, 1] and list(Countdown(3)) == [3, 2, 1]
```

### 49a.19.3 `yield from`

`yield from iterable` yields every item of another iterable, forwards `send()` and `throw()` to it when it is a generator, and evaluates to the sub-generator's return value. It makes recursive generators read naturally:

```python
def flatten(items):
    for item in items:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)        # delegate to the recursive call
        else:
            yield item

assert list(flatten([1, [2, [3, (4,)]], 5])) == [1, 2, 3, 4, 5]

def inner():
    yield "a"
    return "inner done"

def outer(results):
    results.append((yield from inner()))   # the value of yield from is inner's return value
    yield "b"

results = []
assert list(outer(results)) == ["a", "b"] and results == ["inner done"]
```

### 49a.19.4 `send`, `throw` and `close`

Generators are also coroutines in the old sense: `gen.send(value)` resumes the generator and makes the paused `yield` evaluate to `value` (prime it first with `next(gen)`). `gen.throw(exc)` raises an exception at the paused `yield` (since 3.12 only the one-argument form avoids a deprecation warning), and `gen.close()` raises `GeneratorExit` there, so `finally` blocks run; garbage collection closes abandoned generators the same way. `asyncio` drives `async def` coroutines (49a.26) with the same `send` and `throw`, and `contextlib.contextmanager` uses `throw` to deliver the `with` block's exception into your generator.

```python
def running_average():
    total = count = 0
    average = None
    while True:
        value = yield average               # receives what send() passes in
        total += value
        count += 1
        average = total / count

avg = running_average()
next(avg)                                   # prime: run to the first yield
assert avg.send(10) == 10.0 and avg.send(20) == 15.0

cleanup = []

def resource():
    try:
        yield "open"
        yield "still open"
    finally:
        cleanup.append("closed")            # runs on close() and on garbage collection

r = resource()
assert next(r) == "open"
r.close()                                   # GeneratorExit at the paused yield
assert cleanup == ["closed"]

def tolerant():
    while True:
        try:
            yield "waiting"
        except ValueError:
            yield "recovered"

t = tolerant()
next(t)
assert t.throw(ValueError("bad input")) == "recovered"
```

### 49a.19.5 Lazy pipelines

Generators compose into pipelines in which each item flows through every stage before the next item is read, so memory stays constant however large the input is, and work stops as soon as the consumer stops asking. It is the standard-library way to process log files, CSV exports or JSON Lines datasets that do not fit in memory.

```python
import io

log_file = io.StringIO(
    "2026-10-03T10:00:01 INFO request ok 120ms\n"
    "2026-10-03T10:00:02 ERROR upstream timeout 5000ms\n"
    "2026-10-03T10:00:03 INFO request ok 80ms\n"
    "malformed\n"
    "2026-10-03T10:00:04 ERROR db locked 300ms\n"
)

def read_lines(f):
    for line in f:
        yield line.rstrip("\n")

def parse(lines):
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue                                  # skip lines we cannot parse
        timestamp, level, *words, latency = parts
        yield {"level": level, "message": " ".join(words), "ms": int(latency.removesuffix("ms"))}

def only(level, records):
    return (r for r in records if r["level"] == level)

errors = only("ERROR", parse(read_lines(log_file)))  # nothing has been read yet
assert log_file.tell() == 0
assert next(errors) == {"level": "ERROR", "message": "upstream timeout", "ms": 5000}
assert 0 < log_file.tell() < len(log_file.getvalue())   # only the first two lines were read
assert [r["ms"] for r in errors] == [300]
```

### 49a.19.6 The one-shot pitfall

Generators, `map`, `filter`, `zip`, file objects and most other iterators can be consumed once. A function that walks its argument twice works with a list and silently returns wrong answers with a generator; `x in iterator` consumes items up to the match. Materialize with `list()` when you need two passes, use `itertools.tee` for two independent cursors, or accept an iterable you can call `iter()` on twice.

```python
squares = (n * n for n in range(5))
assert 9 in squares                     # consumes 0, 1, 4 and 9
assert list(squares) == [16]            # only the rest is left

def stats(values):
    total = sum(values)
    count = sum(1 for _ in values)      # a second pass over the same argument
    return total, count

assert stats([1, 2, 3]) == (6, 3)
assert stats(n for n in [1, 2, 3]) == (6, 0)    # silently wrong with a generator

numbers = map(int, ["1", "2", "3"])
assert sum(numbers) == 6 and list(numbers) == []

it = iter([1, 2, 3, 4])
assert list(zip(it, it)) == [(1, 2), (3, 4)]    # one iterator twice: consecutive pairs
```

### 49a.19.7 `itertools`

`itertools` is a toolkit of fast, lazy building blocks: infinite streams (`count`, `cycle`, `repeat`), joining and slicing (`chain`, `islice`), running results (`accumulate`), grouping of adjacent items (`groupby`, so sort first to group globally), combinatorics (`product`, `permutations`, `combinations`), neighbors and batches (`pairwise` 3.10, `batched` 3.12 with `strict=` in 3.13), filters (`takewhile`, `dropwhile`, `filterfalse`, `compress`), `starmap`, `tee` and `zip_longest`. The ones worth knowing by heart:

```python
import itertools as it
import operator

assert list(zip(it.count(start=1), ["a", "b"])) == [(1, "a"), (2, "b")]     # number items lazily
assert list(it.islice(it.cycle(["primary", "replica"]), 3)) == ["primary", "replica", "primary"]
assert list(it.chain([1, 2], (3,), "ab")) == [1, 2, 3, "a", "b"]
assert list(it.chain.from_iterable([[1], [2, 3]])) == [1, 2, 3]

deposits = [100, -30, 50]
assert list(it.accumulate(deposits)) == [100, 70, 120]                      # balance after each step
assert list(it.accumulate([12, 15, 11, 18], max)) == [12, 15, 15, 18]       # highest so far
assert list(it.accumulate([2, 3, 4], operator.mul, initial=1)) == [1, 2, 6, 24]   # initial comes first

words = ["apple", "avocado", "banana", "blueberry", "apricot"]
by_letter = {k: list(g) for k, g in it.groupby(sorted(words), key=lambda w: w[0])}
assert by_letter == {"a": ["apple", "apricot", "avocado"], "b": ["banana", "blueberry"]}
runs = [(k, len(list(g))) for k, g in it.groupby(words, key=lambda w: w[0])]
assert runs == [("a", 2), ("b", 2), ("a", 1)]       # unsorted input: "a" appears twice

sizes, colors = ["S", "M"], ["red", "blue"]
assert list(it.product(sizes, colors)) == [("S", "red"), ("S", "blue"), ("M", "red"), ("M", "blue")]
assert len(list(it.product([0, 1], repeat=3))) == 8                          # every 3-bit pattern
team = ["ana", "bo", "cy"]
assert len(list(it.permutations(team, 2))) == 6                              # ordered pairs
assert list(it.combinations(team, 2)) == [("ana", "bo"), ("ana", "cy"), ("bo", "cy")]
assert list(it.pairwise([1, 4, 9])) == [(1, 4), (4, 9)]
assert list(it.starmap(divmod, [(7, 2), (9, 4)])) == [(3, 1), (2, 1)]
latencies = [12, 15, 230, 14]
assert list(it.takewhile(lambda ms: ms < 100, latencies)) == [12, 15]       # stops at the first slow one
assert list(it.dropwhile(lambda ms: ms < 100, latencies)) == [230, 14]
assert list(it.compress(team, [True, False, True])) == ["ana", "cy"]
assert list(it.zip_longest([1, 2, 3], ["x"])) == [(1, "x"), (2, None), (3, None)]   # pads with None

left, right = it.tee(iter([1, 2, 3]))
assert list(left) == [1, 2, 3] and list(right) == [1, 2, 3]
```

```python
# requires: 3.12
import sys
from itertools import batched

rows = ["r1", "r2", "r3", "r4", "r5"]
assert list(batched(rows, 2)) == [("r1", "r2"), ("r3", "r4"), ("r5",)]   # e.g. bulk inserts of two rows
if sys.version_info >= (3, 13):
    try:
        list(batched(rows, 2, strict=True))      # 3.13+: a short last batch is an error
        raised = False
    except ValueError:
        raised = True
    assert raised
```

On 3.11 the same thing is a few lines with `islice`; exercise 31 in the lab asks you to write it.

Combinatoric generators grow fast: `permutations(range(n))` yields n! tuples and `combinations(range(n), r)` yields C(n, r). `math.perm` and `math.comb` count them without generating anything, which is the first thing to compute before deciding whether brute force is feasible.

## 49a.20 Decorators

### 49a.20.1 From functions as objects to wrappers

A decorator is a function that takes a function and returns a new one, plus syntax: `@decorator` above `def f` means `f = decorator(f)`, executed once, when the `def` runs (usually at import time). Most decorators return a wrapper closure that does something before and after calling the original. Without `functools.wraps`, the wrapper replaces the original's name, docstring and annotations, which breaks logging, debugging, documentation tools and frameworks that read signatures; `wraps` copies them over and stores the original in `__wrapped__`.

```python
import functools

def shout(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).upper()
    return wrapper

def greet(name):
    """Return a greeting."""
    return f"hello {name}"

loud = shout(greet)                         # exactly what @shout would do
assert loud("ana") == "HELLO ANA"
assert loud.__name__ == "wrapper" and loud.__doc__ is None    # metadata lost

def shout_properly(func):
    @functools.wraps(func)                  # copy name, docstring, module, annotations
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).upper()
    return wrapper

@shout_properly
def greet2(name):
    """Return a greeting."""
    return f"hello {name}"

assert greet2("bo") == "HELLO BO"
assert greet2.__name__ == "greet2" and greet2.__doc__ == "Return a greeting."
assert greet2.__wrapped__("bo") == "hello bo"   # the undecorated function is still reachable
```

### 49a.20.2 Decorators with arguments

`@retry(attempts=3)` first calls `retry(attempts=3)`, which must return the actual decorator. Hence three levels: the factory takes the options, the decorator takes the function, the wrapper takes the call's arguments.

```python
import functools

def repeat(times):                          # the factory: takes the options
    def decorator(func):                    # the decorator: takes the function
        @functools.wraps(func)
        def wrapper(*args, **kwargs):       # the wrapper: takes the call's arguments
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator

@repeat(3)
def roll():
    return 4

assert roll() == [4, 4, 4]
```

### 49a.20.3 Stacking order

`@outer` above `@inner` above `def f` means `f = outer(inner(f))`: the decorator nearest the function is applied first, and at call time the outermost wrapper runs first.

```python
import functools

applied = []

def tag(label):
    def decorator(func):
        applied.append(label)
        @functools.wraps(func)
        def wrapper():
            return f"<{label}>{func()}</{label}>"
        return wrapper
    return decorator

@tag("b")
@tag("i")
def text():
    return "hi"

assert applied == ["i", "b"]                 # the bottom decorator is applied first
assert text() == "<b><i>hi</i></b>"           # the top wrapper runs outermost
```

Order matters in practice: put `@functools.cache` below a timing decorator to time cache hits too, or above it to skip timing them; put authentication outside retries so a rejected call is not retried; and `@property`, `@classmethod` and `@staticmethod` normally go on top, because they turn the function into a descriptor that other decorators do not expect.

### 49a.20.4 Decorating methods, and class-based decorators

A function-based decorator works on methods unchanged: the wrapper is itself a function, hence a descriptor that binds, and `self` arrives as the first positional argument. A decorator written as a class (an instance with `__call__`) keeps state in attributes, but instances of ordinary classes are not descriptors, so on a method it would never receive `self`. Adding a `__get__` that binds the instance fixes it.

```python
import functools
import types

class CountCallsNoBinding:                        # an ordinary class: not a descriptor
    def __init__(self, func):
        functools.update_wrapper(self, func)      # the class form of wraps
        self.func = func
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.func(*args, **kwargs)

class CountCalls(CountCallsNoBinding):
    def __get__(self, obj, objtype=None):         # bind like a function does
        if obj is None:
            return self
        return types.MethodType(self, obj)

@CountCalls
def ping():
    return "pong"

ping()
ping()
assert ping.calls == 2 and ping.__name__ == "ping"

class Service:
    @CountCalls
    def health(self):
        return f"{type(self).__name__} ok"

    @CountCallsNoBinding
    def broken_health(self):
        return "ok"

assert Service().health() == "Service ok" and Service.health.calls == 1
try:
    Service().broken_health()                     # no __get__: the instance is never passed
    error = ""
except TypeError as err:
    error = str(err)
assert "missing 1 required positional argument: 'self'" in error
```

### 49a.20.5 Practical decorators

**Timing.** Measure with `time.perf_counter` (monotonic, high resolution), record in a `finally` so failures are timed too, and send the measurement to logging or metrics rather than printing it.

```python
import functools
import time

def timed(records):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                records.append((func.__name__, time.perf_counter() - start))
        return wrapper
    return decorator

timings = []

@timed(timings)
def total(n):
    return sum(range(n))

assert total(10_000) == 49995000
name, seconds = timings[0]
assert name == "total" and seconds >= 0
```

**Retry with exponential backoff and jitter.** Retry only errors that a retry can fix (timeouts, connection resets, 429 and 5xx responses), cap the number of attempts and the delay, and randomize the delay ("full jitter": uniform between zero and the capped exponential delay) so that many clients failing together do not retry together. Injecting `sleep` and the random source makes the decorator testable without waiting; 49.1 shows the production version with `tenacity`.

```python
import functools
import random
import time

def retry(*, attempts=3, base_delay=0.1, max_delay=2.0,
          exceptions=(ConnectionError, TimeoutError), sleep=time.sleep, rng=random.random):
    """Retry transient failures with exponential backoff and full jitter."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == attempts - 1:
                        raise                                # out of attempts
                    cap = min(max_delay, base_delay * 2 ** attempt)
                    sleep(rng() * cap)                       # uniform in [0, cap)
        return wrapper
    return decorator

delays = []
outcomes = iter([ConnectionError("reset"), TimeoutError("slow"), "ok"])

@retry(attempts=3, sleep=delays.append, rng=lambda: 0.5)
def flaky_call():
    outcome = next(outcomes)
    if isinstance(outcome, Exception):
        raise outcome
    return outcome

assert flaky_call() == "ok"
assert delays == [0.05, 0.1]             # half of the caps 0.1 and 0.2

calls = []

@retry(sleep=lambda seconds: None)
def bad_request():
    calls.append(1)
    raise ValueError("400 Bad Request")  # not transient: no retry

try:
    bad_request()
except ValueError:
    pass
assert len(calls) == 1
```

**Memoization.** `functools.cache` (3.9) memoizes without a size limit; `functools.lru_cache(maxsize=n)` evicts the least recently used entry; both expose `cache_info()` and `cache_clear()` and require hashable arguments. On methods, both caches hold a reference to `self` in their keys and keep instances alive; use `functools.cached_property` (49a.18.9) or a per-instance dict there.

```python
import functools

@functools.cache
def ways_to_climb(n):
    return 1 if n <= 1 else ways_to_climb(n - 1) + ways_to_climb(n - 2)

assert ways_to_climb(80) == 37889062373143906          # instant; exponential without the cache
info = ways_to_climb.cache_info()
assert (info.hits, info.misses) == (78, 81)

@functools.lru_cache(maxsize=2)
def square(n):
    return n * n

for n in (1, 2, 1, 3, 2):                              # 3 evicts 2, then 2 evicts 1
    square(n)
assert square.cache_info().hits == 1 and square.cache_info().currsize == 2
try:
    functools.cache(len)([1, 2])                       # a list cannot be a cache key
except TypeError:
    pass
```

**Input validation.** A decorator can bind the call's arguments to the signature with `inspect.signature(func).bind(*args, **kwargs)` and check them against the annotations before calling; Pydantic's `validate_call` is the complete version for production.

**Registration.** A decorator can record a function and return it unchanged: command tables, plugin registries, event handlers and URL routes in web frameworks all work this way.

```python
COMMANDS = {}

def command(name):
    def decorator(func):
        COMMANDS[name] = func
        return func                        # registered, not wrapped
    return decorator

@command("greet")
def greet(who):
    return f"hi {who}"

assert COMMANDS["greet"]("ana") == "hi ana" and greet("bo") == "hi bo"
```

**Class decorators** work the same way on classes: they receive the class after its body has run and return it, modified or replaced; 49a.18.8 has a registering one, and `@dataclass` is the standard library's best-known example.

### 49a.20.6 Decorators in the standard library

| Decorators | What they do |
|---|---|
| `@property`, `@classmethod`, `@staticmethod` | descriptors for attributes and methods (49a.17, 49a.18.9) |
| `@functools.wraps`, `@functools.cache`, `@functools.lru_cache`, `@functools.cached_property` | wrapper metadata; memoization; compute once per instance |
| `@functools.total_ordering`, `@functools.singledispatch` | derive comparisons; overload on the first argument's type |
| `@dataclasses.dataclass`, `@enum.unique` | generate `__init__`, `__repr__`, `__eq__`; reject duplicate enum values |
| `@contextlib.contextmanager`, `@abc.abstractmethod` | a context manager from a generator (49a.22); require an override |
| `@typing.overload`, `@typing.override` (3.12), `@warnings.deprecated` (3.13) | information for type checkers (the last also warns at run time) |

To keep a decorated function's signature visible to type checkers, annotate the decorator with `ParamSpec` (49a.16.5).

## 49a.21 Special structures and idioms

Most of these appeared in context earlier; this section collects the idioms that experienced Python programmers expect to see, with the ones not yet shown.

### 49a.21.1 `zip` to unzip and transpose, `enumerate`, `any` and `all`

`zip(*pairs)` unpacks a list of pairs into separate arguments, which "unzips" it; the same trick transposes a matrix. `any` and `all` take any iterable, stop at the first decisive item, and have the vacuous-truth answers for empty input.

```python
pairs = [("ana", 3), ("bo", 5), ("cy", 4)]
names, scores = zip(*pairs)                 # unzip
assert names == ("ana", "bo", "cy") and scores == (3, 5, 4)
matrix = [[1, 2, 3], [4, 5, 6]]
assert [list(col) for col in zip(*matrix)] == [[1, 4], [2, 5], [3, 6]]   # transpose
assert dict(zip(names, scores)) == {"ana": 3, "bo": 5, "cy": 4}
assert max(zip(scores, names)) == (5, "bo")  # compare by score, then by name
assert [f"{i}. {n}" for i, n in enumerate(names, 1)] == ["1. ana", "2. bo", "3. cy"]

orders = [{"id": 1, "paid": True}, {"id": 2, "paid": False}]
assert any(not o["paid"] for o in orders) and not all(o["paid"] for o in orders)
assert all([]) is True and any([]) is False # vacuous truth
```

### 49a.21.2 `map` and `filter` versus comprehensions; `sorted`, `min`, `max` with `key`; `reversed`

Comprehensions are the default because they read left to right and need no `lambda`; `map` and `filter` win when the function already has a name. `key=` on `sorted`, `min`, `max`, `heapq.nlargest` and `itertools.groupby` computes a comparison key once per element; `min` and `max` also take `default=` for empty input. `reversed()` returns a lazy reverse iterator over a sequence, while `xs[::-1]` builds a reversed copy.

```python
words = ["kiwi", "Fig", "banana"]
assert list(map(str.lower, words)) == [w.lower() for w in words]   # a named function: map reads well
assert min(words, key=len) == "Fig" and max([], default="none") == "none"
assert list(reversed(words)) == words[::-1] == ["banana", "Fig", "kiwi"]
```

### 49a.21.3 Slice objects and unpacking in literals and calls

`a[1:5:2]` is `a[slice(1, 5, 2)]`, and a named slice documents fixed-width fields. `*` and `**` unpack into list, tuple, set and dict displays as well as calls.

```python
row = "2026-10-03,ana,42.50"
DATE, NAME, AMOUNT = slice(0, 10), slice(11, 14), slice(15, None)
assert (row[DATE], row[NAME], row[AMOUNT]) == ("2026-10-03", "ana", "42.50")
assert slice(1, 10, 2).indices(5) == (1, 5, 2)      # clamp to a sequence of length 5

first, second = [1, 2], (3, 4)
assert [*first, *second] == [1, 2, 3, 4] and (*first, 5) == (1, 2, 5)
assert {*first, *second} == {1, 2, 3, 4}
assert {**{"a": 1}, "b": 2} == {"a": 1, "b": 2}

def show(*args, **kwargs):
    return args, kwargs

assert show(*"ab", **{"sep": "-"}) == (("a", "b"), {"sep": "-"})
```

### 49a.21.4 `Ellipsis`, underscores and sentinels

`...` is the singleton `Ellipsis`. It serves as a placeholder body (like `pass`), as "any arguments" in `Callable[..., T]`, as "any length" in `tuple[int, ...]`, and as a marker in stub files and NumPy-style slicing.

| Form | Meaning |
|---|---|
| `_` | a throwaway name (`for _ in range(3)`), the wildcard in `match`, and the last result in the interactive interpreter |
| `_name` | internal to a module or class; skipped by `from module import *` |
| `__name` | a name-mangled class attribute (49a.17.4) |
| `__name__` | a special name defined by the language |
| `name_` | avoids clashing with a keyword or built-in (`class_`, `type_`) |
| `1_000_000` | digit grouping in numeric literals |

A **sentinel** is a unique object used as a marker when `None` is itself a valid value, typically for "argument not given". `object()` creates one that no caller can pass by accident. Python 3.15, due on 9 October 2026, adds a `sentinel` built-in for this (PEP 661), with a readable `repr`.

```python
assert ... is Ellipsis and type(...).__name__ == "ellipsis"

def todo():
    ...                                      # a placeholder body

assert todo() is None

_MISSING = object()

def get_setting(settings, key, default=_MISSING):
    try:
        return settings[key]
    except KeyError:
        if default is _MISSING:              # no default given: let the error out
            raise
        return default

settings = {"timeout": None}
assert get_setting(settings, "timeout") is None        # None is a real value here
assert get_setting(settings, "retries", default=3) == 3
try:
    get_setting(settings, "retries")
except KeyError:
    pass
```

### 49a.21.5 EAFP versus LBYL

EAFP ("easier to ask forgiveness than permission") attempts the operation and handles the exception; LBYL ("look before you leap") checks first. Python favors EAFP: the code reads as the happy path and has no race between check and use (`if os.path.exists(path): open(path)` still fails if the file vanishes in between). Since 3.11, entering a `try` block costs essentially nothing, because handler locations live in a table built at compile time; you pay only when an exception is raised. LBYL is still right when failure is the common case or the check prevents an expensive or irreversible action.

```python
config = {"port": "8080"}

if "port" in config and config["port"].isdigit():   # LBYL: two checks, still misses " 8080"
    port = int(config["port"])

try:                                                # EAFP: the conversion is the check
    port = int(config["port"])
except (KeyError, ValueError):
    port = 80
assert port == 8080
```

### 49a.21.6 Idiom quick reference

| Instead of | Write |
|---|---|
| `for i in range(len(xs)): x = xs[i]` | `for x in xs:` or `for i, x in enumerate(xs):` |
| `if len(xs) > 0:` | `if xs:` |
| `if x == None:` | `if x is None:` |
| `try: v = d[k]` / `except KeyError: v = default` | `v = d.get(k, default)` |
| `tmp = a; a = b; b = tmp` | `a, b = b, a` |
| `list(map(lambda x: x * 2, xs))` | `[x * 2 for x in xs]` |
| `f = open(p)` ... `f.close()` | `with open(p) as f:` or `Path(p).read_text()` |
| `type(x) == int` | `isinstance(x, int)` |
| `if x > 0 and x < 10:` | `if 0 < x < 10:` |
| `print("x =", x)` while debugging | `print(f"{x = }")` |
| a flag variable set inside a search loop | `for ... else` |
| `d = {}` then `if k not in d: d[k] = []` | `defaultdict(list)` or `d.setdefault(k, [])` |

## 49a.22 Context managers and resource handling

### 49a.22.1 The protocol

`with manager as target:` calls `manager.__enter__()` and binds its result to `target`; when the block ends, by finishing, returning, breaking or raising, it calls `manager.__exit__(exc_type, exc, traceback)` (three `None`s if nothing was raised), and a true return value suppresses the exception. So `with` is a reusable `try`/`finally` whose cleanup lives in the manager: files, locks, transactions, temporary directories and patched test settings all work this way.

```python
class Transaction:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        self.log.append("begin")
        return self                               # bound by "as"

    def __exit__(self, exc_type, exc, tb):
        self.log.append("rollback" if exc_type else "commit")
        return False                              # do not suppress the exception

log = []
with Transaction(log):
    pass
try:
    with Transaction(log) as tx:
        raise ValueError("constraint violated")
except ValueError:
    pass
assert log == ["begin", "commit", "begin", "rollback"]
```

### 49a.22.2 `contextlib.contextmanager`

Writing a class with two methods is ceremony for most managers. `@contextmanager` turns a generator into one: the code before `yield` is the setup, the yielded value is the `as` target, and the code after it is the teardown. Put the `yield` inside `try`/`finally`, or the teardown will not run when the block raises.

```python
from contextlib import contextmanager

@contextmanager
def temporary_attr(obj, name, value):
    old = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield obj
    finally:
        setattr(obj, name, old)                   # restored even if the block raises

class Settings:
    debug = False

with temporary_attr(Settings, "debug", True):
    assert Settings.debug is True
assert Settings.debug is False

try:
    with temporary_attr(Settings, "debug", True):
        raise RuntimeError("test failure")
except RuntimeError:
    pass
assert Settings.debug is False
```

### 49a.22.3 `suppress`, `ExitStack`, `closing`, `nullcontext`, `redirect_stdout`

```python
import contextlib
import io
import pathlib
import tempfile

cache = {"a": 1}
with contextlib.suppress(KeyError):            # try/except KeyError: pass, in one line
    del cache["missing"]

with tempfile.TemporaryDirectory() as tmp:
    cleanup = []
    with contextlib.ExitStack() as stack:      # managers chosen at run time, all exited at the end
        logs = {}
        for level in ("error", "warning", "info"):
            path = pathlib.Path(tmp, f"{level}.log")
            logs[level] = stack.enter_context(path.open("w", encoding="utf-8"))
        stack.callback(cleanup.append, "callbacks run too")
        logs["error"].write("disk full\n")
    assert all(f.closed for f in logs.values()) and cleanup == ["callbacks run too"]
    assert pathlib.Path(tmp, "error.log").read_text(encoding="utf-8") == "disk full\n"

class Connection:                              # has close() but no __exit__
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

with contextlib.closing(Connection()) as conn:
    pass
assert conn.closed

def process(items, lock=None):
    with lock if lock is not None else contextlib.nullcontext():   # an optional manager
        return len(items)

assert process([1, 2]) == 2

buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):       # capture print() output
    print("captured")
assert buffer.getvalue() == "captured\n"
```

### 49a.22.4 Files with `pathlib`

`pathlib.Path` is the modern interface to the file system: `/` joins paths, attributes split them (`name`, `stem`, `suffix`, `parent`), and methods read, write, list and test. Always pass `encoding="utf-8"` for text (the default depends on the platform's locale until 3.15, which makes UTF-8 the default under PEP 686), open CSV files with `newline=""`, and iterate over a file object to stream a large file line by line instead of reading it whole.

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    reports = root / "data" / "reports"                  # / joins path segments
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / "q3-summary.txt"
    report.write_text("line one\nline two\n", encoding="utf-8")

    assert (report.name, report.stem, report.suffix) == ("q3-summary.txt", "q3-summary", ".txt")
    assert report.parent == reports and report.exists() and report.is_file()
    assert report.read_text(encoding="utf-8").splitlines() == ["line one", "line two"]

    with report.open("a", encoding="utf-8") as f:        # "a" appends, "w" truncates, "x" fails if present
        f.write("line three\n")
    with report.open(encoding="utf-8") as f:
        count = sum(1 for _ in f)                        # streams; never holds the whole file
    assert count == 3

    (reports / "q4-summary.txt").touch()
    assert sorted(p.name for p in root.rglob("*.txt")) == ["q3-summary.txt", "q4-summary.txt"]   # recursive
    report.unlink(missing_ok=True)                       # delete; no error if already gone
```

### 49a.22.5 JSON, JSON Lines and CSV round trips

`json` maps dicts, lists, strings, numbers, booleans and `None` to JSON and back. Tuples come back as lists and non-string keys as strings, and dates, `Decimal`s and sets need a `default=` function on the way out (49a.18.5). JSON Lines (one document per line) is the usual format for logs, evaluation sets and fine-tuning data, because it streams and appends. `csv` returns every field as a string.

```python
import csv
import json
import tempfile
from pathlib import Path

record = {"id": 7, "tags": ("a", "b"), 1: "int key", "name": "Zoë"}
text = json.dumps(record, ensure_ascii=False)
assert text == '{"id": 7, "tags": ["a", "b"], "1": "int key", "name": "Zoë"}'
assert json.loads(text) == {"id": 7, "tags": ["a", "b"], "1": "int key", "name": "Zoë"}

rows = [{"name": "ana", "score": 3}, {"name": "bo, jr.", "score": 5}]
with tempfile.TemporaryDirectory() as tmp:
    jsonl = Path(tmp) / "events.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")              # one document per line
    with jsonl.open(encoding="utf-8") as f:
        assert [json.loads(line) for line in f] == rows

    table = Path(tmp) / "scores.csv"
    with table.open("w", newline="", encoding="utf-8") as f:   # newline="": csv controls line endings
        writer = csv.DictWriter(f, fieldnames=["name", "score"])
        writer.writeheader()
        writer.writerows(rows)
    with table.open(newline="", encoding="utf-8") as f:
        loaded = list(csv.DictReader(f))
    assert table.read_text(encoding="utf-8").splitlines()[2] == '"bo, jr.",5'   # quoted as needed

assert loaded == [{"name": "ana", "score": "3"}, {"name": "bo, jr.", "score": "5"}]   # all strings
```

### 49a.22.6 `tempfile`

`tempfile.TemporaryDirectory()` and `tempfile.NamedTemporaryFile()` create uniquely named, private locations and delete them when the `with` block ends; `mkstemp` and `mkdtemp` create them without automatic cleanup. Tests should use them (or pytest's `tmp_path`) rather than writing next to the code. Never build temporary file names yourself: predictable names in shared directories are a security problem.

## 49a.23 Exceptions in depth

### 49a.23.1 The hierarchy

```text
BaseException
 ├── BaseExceptionGroup
 ├── GeneratorExit
 ├── KeyboardInterrupt
 ├── SystemExit
 └── Exception
      ├── ArithmeticError: ZeroDivisionError, OverflowError, FloatingPointError
      ├── AssertionError, AttributeError, BufferError, EOFError, MemoryError, ReferenceError
      ├── ExceptionGroup (also a BaseExceptionGroup)
      ├── ImportError: ModuleNotFoundError
      ├── LookupError: IndexError, KeyError
      ├── NameError: UnboundLocalError
      ├── OSError: FileNotFoundError, PermissionError, TimeoutError, ConnectionError, ...
      ├── RuntimeError: NotImplementedError, RecursionError
      ├── StopIteration, StopAsyncIteration
      ├── SyntaxError, SystemError, TypeError
      ├── ValueError: UnicodeError (UnicodeDecodeError, UnicodeEncodeError)
      └── Warning: DeprecationWarning, UserWarning, SyntaxWarning, RuntimeWarning, ...
```

Ordinary errors derive from `Exception`. `KeyboardInterrupt`, `SystemExit` and `GeneratorExit` derive only from `BaseException`, so `except Exception` lets Ctrl+C and `sys.exit()` through, and so does `asyncio.CancelledError` (a `BaseException` since 3.8), which keeps task cancellation working. A bare `except:` catches all of them, which is why it is a bug in almost every codebase.

```python
import asyncio

assert issubclass(KeyboardInterrupt, BaseException) and not issubclass(KeyboardInterrupt, Exception)
assert not issubclass(asyncio.CancelledError, Exception)    # except Exception will not swallow it
assert asyncio.TimeoutError is TimeoutError                 # one TimeoutError since 3.11
assert issubclass(FileNotFoundError, OSError) and issubclass(KeyError, LookupError)

def risky():
    raise KeyboardInterrupt                   # as if the user pressed Ctrl+C

def swallow_everything():
    try:
        risky()
    except:                                   # catches KeyboardInterrupt and SystemExit too
        return "swallowed"

def catch_errors_only():
    try:
        risky()
    except Exception:
        return "handled"

assert swallow_everything() == "swallowed"
try:
    catch_errors_only()
except KeyboardInterrupt:
    pass                                      # the interrupt got through, as it should
```

### 49a.23.2 Custom exceptions

Give a package one base exception so callers can catch everything it raises with one clause, then subclass it for the cases callers handle differently. Pass the message to `super().__init__` so `str(err)` and `err.args` stay useful, and store structured details as attributes (a retry delay, an HTTP status, the field that failed) instead of making callers parse messages.

```python
import copy

class AppError(Exception):
    """Base class for every error this package raises."""

class ToolError(AppError):
    def __init__(self, tool: str, message: str, *, retryable: bool = False):
        super().__init__(f"{tool}: {message}")
        self.tool = tool
        self.retryable = retryable

class RateLimited(ToolError):
    def __init__(self, tool: str, retry_after: float):
        super().__init__(tool, f"rate limited, retry after {retry_after}s", retryable=True)
        self.retry_after = retry_after

try:
    raise RateLimited("search", 2.5)
except AppError as err:                       # one clause catches the whole family
    assert str(err) == "search: rate limited, retry after 2.5s"
    assert err.retryable and err.retry_after == 2.5 and isinstance(err, ToolError)
    try:
        copy.copy(err)                        # rebuilt as RateLimited(*err.args): wrong arguments
    except TypeError:
        pass
```

The last lines show a production trap: exceptions are copied and pickled by calling the class with `err.args`, so an exception whose `__init__` signature differs from its `args` cannot cross a process boundary (`multiprocessing`, `ProcessPoolExecutor`). Keep `__init__` compatible with `args`, or define `__reduce__`.

### 49a.23.3 Chaining: `__cause__`, `__context__` and `from None`

When an exception is raised while another is being handled, Python records the first one as `__context__` of the second and prints both ("During handling of the above exception, another exception occurred"). `raise New(...) from err` states the causal link explicitly in `__cause__` ("The above exception was the direct cause of the following exception"), which is how you translate a low-level error into a domain error without losing the original. `raise New(...) from None` hides the context when it is an implementation detail.

```python
import traceback

def load(config):
    try:
        return config["port"]
    except KeyError as err:
        raise LookupError("port not configured") from err

try:
    load({})
except LookupError as err:
    assert isinstance(err.__cause__, KeyError) and err.__suppress_context__
    assert "direct cause" in "".join(traceback.format_exception(err))

try:
    try:
        1 / 0
    except ZeroDivisionError:
        undefined_name                         # a bug inside the handler
except NameError as err:
    assert isinstance(err.__context__, ZeroDivisionError) and err.__cause__ is None
    assert "During handling" in "".join(traceback.format_exception(err))

try:
    try:
        {}["k"]
    except KeyError:
        raise ValueError("bad input") from None   # the KeyError is an implementation detail
except ValueError as err:
    assert err.__suppress_context__ and err.__cause__ is None
```

### 49a.23.4 `finally` semantics

`finally` runs after the `try` block's return value has been computed, and before the function actually returns. If the `finally` block itself executes `return`, `break` or `continue`, it replaces the pending return value or silently discards the in-flight exception. That is almost always a bug, and since 3.14 the compiler emits a `SyntaxWarning` for it (PEP 765).

```python
import warnings

def work(events):
    try:
        events.append("try")
        return "from try"
    finally:
        events.append("finally")              # runs after the return value is computed

events = []
assert work(events) == "from try" and events == ["try", "finally"]

source = '''
def swallow():
    try:
        raise RuntimeError("lost")
    finally:
        return "finally wins"
'''
namespace = {}
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)    # 3.14+ warns about this code
    exec(compile(source, "<demo>", "exec"), namespace)
assert namespace["swallow"]() == "finally wins"       # the RuntimeError vanished
```

```python
# requires: 3.14
import warnings

source = "def f():\n    try:\n        pass\n    finally:\n        return 1\n"
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    compile(source, "<demo>", "exec")
assert [w.category for w in caught] == [SyntaxWarning]    # PEP 765
```

### 49a.23.5 Exception groups and `except*` (3.11)

Sometimes several independent things fail at once: concurrent tasks (49a.26), or a validator that should report every problem instead of the first. `ExceptionGroup(message, exceptions)` carries them together, and `except*` handles the matching part of a group: each `except*` clause runs for the exceptions of its type, several clauses can run for one group, and whatever no clause matched is re-raised as a new group. `split()` and `subgroup()` do the same filtering by hand.

```python
def validate(user):
    errors = []
    if not user.get("name"):
        errors.append(ValueError("name is required"))
    if not isinstance(user.get("age"), int):
        errors.append(TypeError("age must be an int"))
    if errors:
        raise ExceptionGroup("invalid user", errors)

handled = []
try:
    validate({"age": "ten"})
except* ValueError as group:
    handled += [str(e) for e in group.exceptions]
except* TypeError as group:
    handled += [str(e) for e in group.exceptions]
assert handled == ["name is required", "age must be an int"]   # both clauses ran

batch = ExceptionGroup("batch", [ValueError("a"), KeyError("b"), ValueError("c")])
values, rest = batch.split(ValueError)
assert [str(e) for e in values.exceptions] == ["a", "c"] and len(rest.exceptions) == 1
try:
    try:
        raise batch
    except* ValueError:
        pass                                   # handles both ValueErrors
except ExceptionGroup as remaining:            # the KeyError comes back in a new group
    assert [type(e) for e in remaining.exceptions] == [KeyError]
```

### 49a.23.6 Notes (3.11)

`err.add_note(text)` attaches context to an exception that is already in flight, without wrapping it in another type; tracebacks print the notes under the message. It is the clean way to say which row, file or request was being processed.

```python
import traceback

try:
    try:
        int("x")
    except ValueError as err:
        err.add_note("while parsing row 42 of orders.csv")
        raise                                  # same exception, same type, more context
except ValueError as err:
    assert err.__notes__ == ["while parsing row 42 of orders.csv"]
    assert "while parsing row 42" in "".join(traceback.format_exception(err))
```

### 49a.23.7 `except A, B:` without parentheses (3.14)

Python 3.14 (PEP 758) accepts several exception types without parentheses when the clause has no `as`; with `as`, the parentheses are still required. Before 3.14 the unparenthesized form is a `SyntaxError` (in Python 2 it meant something else entirely, which is why it was forbidden for so long). Keep the parentheses in code that must run on older versions.

```python
# requires: 3.14
def classify(exc):
    try:
        raise exc
    except ValueError, TypeError:              # 3.14+: no parentheses needed without "as"
        return "bad input"
    except (KeyError, IndexError) as err:      # with "as", parentheses are still required
        return f"missing: {type(err).__name__}"

assert classify(TypeError()) == "bad input" and classify(KeyError("k")) == "missing: KeyError"
```

```python
import sys

source = "try:\n    pass\nexcept ValueError, TypeError:\n    pass\n"
try:
    compile(source, "<demo>", "exec")
    accepted = True
except SyntaxError:
    accepted = False
assert accepted == (sys.version_info >= (3, 14))
```

### 49a.23.8 Logging exceptions, and handling them well

Inside an `except` block, `logger.exception("message")` logs at ERROR level with the full traceback (it is `logger.error(..., exc_info=True)`). Log an exception once, at the boundary that handles it (the request handler, the job runner), not at every layer it passes through, or one failure produces five log entries.

```python
import io
import logging

stream = io.StringIO()
logger = logging.getLogger("brushup.orders")
handler = logging.StreamHandler(stream)
logger.addHandler(handler)
logger.propagate = False
try:
    {}["order_id"]
except KeyError:
    logger.exception("failed to load order %s", 42)    # ERROR plus the traceback
logger.removeHandler(handler)

output = stream.getvalue()
assert output.startswith("failed to load order 42")
assert "Traceback (most recent call last)" in output and "KeyError: 'order_id'" in output
```

The rules that keep error handling honest: raise the most specific type; catch only what you can handle, as narrowly as possible; never `except Exception: pass`; re-raise with a bare `raise`; translate at module boundaries with `raise ... from err`; release resources with `with` or `finally`; and return expected outcomes as values when the caller must reason about them, as a tool returning "not found" to an agent does in 49.1.

**Interview line:** *"`except Exception`, never a bare except, because KeyboardInterrupt, SystemExit and CancelledError are BaseExceptions; one base exception per package; `raise ... from err` keeps the cause; a return in finally swallows errors, which 3.14 warns about; ExceptionGroup with except* reports several failures, and add_note adds context."*

## 49a.24 Modules, packages and the import system

### 49a.24.1 What `import` does

A module is an object, usually created from a `.py` file. `import shop.pricing` looks up `"shop.pricing"` in the `sys.modules` cache and stops if it is there; otherwise it finds the module on `sys.path` (the script's directory, `PYTHONPATH`, the standard library, `site-packages`), creates a module object, registers it in `sys.modules`, **executes its code once** and binds the name. Every later import gets the cached object, which is why module-level code runs once and a module-level instance behaves as a singleton (49a.29); `importlib.reload` runs the code again into the same object.

A package is a directory of modules. With an `__init__.py` it is a regular package, and that file runs on the first import of the package or anything in it; without one it is a namespace package (PEP 420), which can span directories. Relative imports (`from . import sibling`, `from .. import parent`) work only when the module is imported as part of its package, so run package modules with `python -m package.module`, not `python package/module.py`. `__all__` lists what `from module import *` exports and documents the public API.

```python
import importlib
import sys
import tempfile
import textwrap
from pathlib import Path

files = {
    "shop/__init__.py": '''
        """Runs on the first import of shop or of any submodule."""
        from .pricing import total          # a relative import of a sibling
        __all__ = ["total"]
    ''',
    "shop/registry.py": '''
        loads = []
    ''',
    "shop/pricing.py": '''
        from . import registry
        registry.loads.append(__name__)     # a side effect that shows each execution
        TAX = 0.2

        def total(prices):
            return round(sum(prices) * (1 + TAX), 2)
    ''',
}

with tempfile.TemporaryDirectory() as tmp:
    for name, source in files.items():
        path = Path(tmp, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    sys.path.insert(0, tmp)
    try:
        import shop
        import shop.pricing as first
        import shop.pricing as second
        from shop import registry

        assert first is second is sys.modules["shop.pricing"]    # cached: one module object
        assert registry.loads == ["shop.pricing"]                # executed once
        assert shop.total([10, 20]) == 36.0

        namespace = {}
        exec("from shop import *", namespace)
        assert "total" in namespace and "pricing" not in namespace   # __all__ decides

        importlib.reload(first)                                  # runs the module code again
        assert registry.loads == ["shop.pricing", "shop.pricing"]
    finally:
        sys.path.remove(tmp)
        for module_name in [m for m in sys.modules if m == "shop" or m.startswith("shop.")]:
            del sys.modules[module_name]
```

### 49a.24.2 Circular imports

Two modules that import each other at the top level work only if neither needs the other's names while it is still executing; otherwise one finds a partially initialized module and the import fails. Fixes, in order of preference: move the shared code into a third module; import the module instead of names from it (`import pkg.a`, then `pkg.a.VALUE` at call time); import inside the function that needs it; and for annotation-only imports, `if TYPE_CHECKING:` (49a.16.5).

```python
import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    package = Path(tmp, "circ")
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "a.py").write_text("from circ.b import helper\nVALUE = 1\n")
    (package / "b.py").write_text("from circ.a import VALUE\n\ndef helper():\n    return VALUE\n")
    broken = subprocess.run([sys.executable, "-B", "-c", "import circ.a"],
                            cwd=tmp, capture_output=True, text=True)
    (package / "b.py").write_text("import circ.a\n\ndef helper():\n    return circ.a.VALUE\n")
    fixed = subprocess.run([sys.executable, "-B", "-c", "import circ.a; print(circ.a.helper())"],
                           cwd=tmp, capture_output=True, text=True)

assert "partially initialized module" in broken.stderr
assert fixed.stdout.strip() == "1"
```

### 49a.24.3 Virtual environments, `pyproject.toml` and entry points

A virtual environment is a directory with its own `site-packages` and a `python` that uses it, so each project gets its own dependency versions without touching the system interpreter. The standard workflow (49.1 covers locking with uv or Poetry):

```bash
python3 -m venv .venv            # create the environment
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"   # install this project in editable mode, with dev extras
python -c "import sys; print(sys.prefix != sys.base_prefix)"   # True inside a venv
```

`pyproject.toml` declares the build system and the project's metadata, dependencies and command-line entry points. `[project.scripts]` creates console commands at install time: `brushup = "brushup_tools.cli:main"` installs a `brushup` executable that imports `brushup_tools.cli` and calls `main()`. Plugin systems use entry-point groups (`[project.entry-points."myapp.plugins"]`), which the host application discovers with `importlib.metadata.entry_points(group="myapp.plugins")`. Since 3.11 the standard library can read TOML:

```python
import tomllib

config = tomllib.loads('''
[project]
name = "brushup-tools"
requires-python = ">=3.11"

[project.scripts]
brushup = "brushup_tools.cli:main"
''')
assert config["project"]["requires-python"] == ">=3.11"
assert config["project"]["scripts"] == {"brushup": "brushup_tools.cli:main"}
```

**Interview line:** *"Import finds, creates, caches in sys.modules and executes a module once per process; relative imports need the module imported as part of its package, so I run it with `-m`. A circular import fails when a module needs a name from a half-initialized one; I restructure, or import the module instead of the name."*

## 49a.25 Memory and performance

### 49a.25.1 Reference counting and the cycle collector

CPython frees most objects by **reference counting**: when an object's count of references drops to zero it is freed at once (running `__del__`, if any). Other implementations such as PyPy collect later, so release resources with `with`, not `del`. Reference counting cannot free a **cycle** (objects referring to each other), so a cyclic garbage collector (the `gc` module) periodically finds groups of objects reachable only from each other. Releases 3.14.0 to 3.14.4 used an incremental collector that scanned the old generation a slice at a time; after users saw much higher memory use in production, 3.14.5 restored the generational collector of 3.13.

A **weak reference** (`weakref`) points to an object without keeping it alive, which suits caches and observers that must not prevent cleanup. Not every type supports them: `list`, `dict`, `int` and `str` instances do not, while instances of ordinary classes do.

```python
import gc
import sys
import weakref

class Node:
    def __init__(self, name):
        self.name = name
        self.peer = None

obj = Node("x")
before = sys.getrefcount(obj)          # the call itself adds a temporary reference
alias = obj
assert sys.getrefcount(obj) == before + 1
del alias
assert sys.getrefcount(obj) == before

a, b = Node("a"), Node("b")
a.peer, b.peer = b, a                  # a reference cycle
probe = weakref.ref(a)                 # watches a without keeping it alive
del a, b
gc.collect()                           # reference counts never reach zero; the collector frees them
assert probe() is None

cache = weakref.WeakValueDictionary()
item = Node("cached")
cache["key"] = item
assert cache["key"] is item
del item                               # the last strong reference
gc.collect()
assert "key" not in cache              # the entry disappeared with the object
try:
    weakref.ref([1, 2])                # plain lists do not support weak references
except TypeError:
    pass
```

### 49a.25.2 Measuring memory: `sys.getsizeof` and `tracemalloc`

`sys.getsizeof` reports the size of one object, not of what it refers to: a list's size counts its array of pointers, not the elements. The numbers also change between versions (strings shrank in 3.12, instances changed layout in 3.11 to 3.13), so never hard-code them. To measure what a piece of code really allocates, use `tracemalloc`.

```python
import sys
import tracemalloc

inner = list(range(10_000))
outer = [inner]
assert sys.getsizeof(outer) < sys.getsizeof(inner)      # the inner list is not counted

tracemalloc.start()
before, _ = tracemalloc.get_traced_memory()
data = [str(i) for i in range(10_000)]
after, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
assert after - before > sys.getsizeof(data)             # the strings themselves count here
```

### 49a.25.3 The costs of built-in operations

The cost tables are with each type: `str` in 49a.7.6, `list` in 49a.8.6, `dict` in 49a.11.3 and `set` in 49a.12; a `deque` is O(1) at both ends and O(n) in the middle (49a.13.1), and `len()` is O(1) for all of them. Average-case hash operations degrade to O(n) only under pathological collisions; string hash randomization makes those hard to provoke from outside.

### 49a.25.4 Timing with `timeit`, and profiling before optimizing

`timeit` runs a snippet many times and reports the total; take the minimum of several repeats, because the noise is all upward. From a shell, `python -m timeit -s "setup" "statement"` does the same. For whole programs, profile first (`python -m cProfile -s cumtime app.py`, or a sampling profiler) and optimize the hot spot the profile shows, not the one you suspect. Timings vary with machine load, so the block below states the cost difference by counting equality checks, which do not vary.

```python
import timeit

setup = "data = list(range(10_000)); as_set = set(data)"
list_time = min(timeit.repeat("9_999 in data", setup=setup, number=200, repeat=3))
set_time = min(timeit.repeat("9_999 in as_set", setup=setup, number=200, repeat=3))
assert list_time > 0 and set_time > 0  # typically a factor of 100 or more apart, but never guaranteed

class Key:
    comparisons = 0

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        Key.comparisons += 1
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

keys = [Key(i) for i in range(10_000)]
key_set = set(keys)
probe = Key(9_999)                     # equal to the last key, but a different object
Key.comparisons = 0
assert probe in keys and Key.comparisons == 10_000   # the list compares with every element: O(n)
Key.comparisons = 0
assert probe in key_set and Key.comparisons == 1     # the hash picks the slot: one comparison, O(1)
```

### 49a.25.5 Speedups that matter, in order

1. **A better algorithm or data structure.** Replacing a list membership test inside a loop with a set turns O(n²) into O(n), as in the `seen` set of 49a.12; no micro-optimization comes close.
2. **Built-ins and the standard library**, which run in C: `sum`, `min`, `max`, `sorted`, `str.join`, `collections.Counter`, `itertools`, `bisect`, `heapq`.
3. **Comprehensions** instead of loops that call `append`, and generator expressions to avoid building intermediate lists.
4. **Caching** repeated pure computations with `functools.cache`.
5. **Fewer lookups in hot loops**: local variables are faster than globals and attribute lookups, so binding `append = out.append` before a tight loop helps a little; do it only where a profile says so.
6. **`__slots__`** for millions of small objects, and `array` for large homogeneous numbers.
7. **Concurrency**: threads or asyncio for waiting on I/O, processes for CPU-bound pure Python (49a.26).

Copies cost time too: slicing, `list(x)`, `dict(x)` and `copy.copy` are O(n); `copy.deepcopy` walks the whole structure; `bytes` slicing copies while `memoryview` slicing does not (49a.9).

## 49a.26 Concurrency

### 49a.26.1 The GIL, and what it does and does not mean

In the default CPython build, the **global interpreter lock** lets one thread execute Python bytecode at a time. Threads still help with I/O, because blocking calls (sockets, `time.sleep`, file I/O, `hashlib` and `zlib` on large inputs) release the lock, but they do not speed up CPU-bound Python. Nor does the GIL make code thread-safe: `counter += 1` is several bytecode steps, and a thread switch between them loses updates, so shared state needs a lock. 3.13 added an experimental free-threaded build, which 3.14 supports officially but optionally (49a.26.6).

| Tool | Best for | Shares memory | Notes |
|---|---|---|---|
| `threading`, `ThreadPoolExecutor` | I/O-bound work with blocking libraries | yes | simple; needs locks for shared state |
| `asyncio` | many concurrent I/O operations with async libraries | yes, one thread | cooperative: one blocking call stalls everything |
| `multiprocessing`, `ProcessPoolExecutor` | CPU-bound pure Python | no (pickled messages) | process start-up and serialization costs |
| `concurrent.interpreters`, `InterpreterPoolExecutor` (3.14) | CPU-bound work, isolated, in one process | no | each interpreter has its own GIL; extension support varies |
| free-threaded build (3.13 experimental, 3.14 supported) | CPU-bound threads | yes | separate interpreter build; extensions must support it |

### 49a.26.2 Threads for I/O

`concurrent.futures.ThreadPoolExecutor` is the high-level interface: `map` returns results in input order, `submit` returns a `Future`, and `as_completed` yields futures as they finish. A `threading.Lock` (used as a context manager) protects shared state.

```python
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch(delay):
    time.sleep(delay)                            # stands in for a network call; releases the GIL
    return delay

all_waiting = threading.Barrier(5, timeout=30)

def fetch_together(delay):
    all_waiting.wait()                           # returns only when five calls are in flight at once
    return fetch(delay)

with ThreadPoolExecutor(max_workers=5) as pool:
    results = list(pool.map(fetch_together, [0.2] * 5))   # input order is kept
assert results == [0.2] * 5                      # the waits overlapped: about 0.2 s in total, not 1.0 s

with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(fetch, d): d for d in (0.03, 0.01, 0.02)}
    finished = [futures[f] for f in as_completed(futures)]
assert sorted(finished) == [0.01, 0.02, 0.03]    # yielded in completion order, not submission order

counter = 0
lock = threading.Lock()

def add(n):
    global counter
    for _ in range(n):
        with lock:                               # without it, updates can be lost
            counter += 1

threads = [threading.Thread(target=add, args=(10_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
assert counter == 40_000
```

### 49a.26.3 Processes for CPU-bound work

`ProcessPoolExecutor` runs functions in separate processes, each with its own interpreter and GIL, so CPU-bound Python uses several cores. Arguments, functions and results are pickled, so functions must be importable (top-level, not lambdas or nested functions), and the main script needs the `if __name__ == "__main__":` guard, because the spawn and forkserver start methods import it in every child. Spawn is the default on Windows and macOS; on Linux and other POSIX systems, 3.14 changed the default from fork to forkserver, so code that relied on fork copying the parent's memory must now request fork.

```python
import math
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=2) as pool:
    digits = list(pool.map(math.factorial, [500, 1000, 1500]))   # a picklable, importable function
assert [len(str(d)) for d in digits] == [1135, 2568, 4115]
```

### 49a.26.4 `async` and `await`

An `async def` function returns a coroutine object when called; nothing runs until it is awaited or scheduled as a task on an event loop. `await` suspends the coroutine until the awaited operation completes, letting the loop run other coroutines meanwhile, all in one thread. `asyncio.run(main())` starts a loop, runs the coroutine and closes the loop. `asyncio.gather` runs several awaitables concurrently and returns their results in order. 49.1 shows the production pattern (one HTTP client, timeouts per call, semaphores per provider).

```python
import asyncio

in_flight = peak = 0

async def call_model(prompt, delay):
    global in_flight, peak
    in_flight += 1
    peak = max(peak, in_flight)
    await asyncio.sleep(delay)                   # stands in for a network call
    in_flight -= 1
    return f"answer to {prompt}"

async def main():
    return await asyncio.gather(call_model("a", 0.2), call_model("b", 0.2), call_model("c", 0.2))

assert asyncio.run(main()) == ["answer to a", "answer to b", "answer to c"]   # argument order
assert peak == 3                                 # all three waited at once: about 0.2 s, not 0.6 s
```

`asyncio.TaskGroup` (3.11) gives structured concurrency: tasks created in the group are awaited when the `async with` block ends, and if one fails, the others are canceled and the failures are raised together as an `ExceptionGroup` (49a.23.5). Prefer it to bare `create_task` calls, whose exceptions are easy to lose.

```python
import asyncio

async def ok(n):
    await asyncio.sleep(0.01)
    return n

async def fails():
    await asyncio.sleep(0.005)
    raise ValueError("tool failed")

async def main():
    async with asyncio.TaskGroup() as tg:       # 3.11+
        first = tg.create_task(ok(1))
        second = tg.create_task(ok(2))
    results = [first.result(), second.result()]
    errors = []
    try:
        async with asyncio.TaskGroup() as tg:
            slow = tg.create_task(asyncio.sleep(10))
            tg.create_task(fails())
    except* ValueError as group:
        errors = [str(e) for e in group.exceptions]
    return results, errors, slow.cancelled()

assert asyncio.run(main()) == ([1, 2], ["tool failed"], True)   # the sibling was canceled
```

Every network call needs a deadline. `asyncio.timeout()` (3.11) bounds a block and raises `TimeoutError`; `asyncio.wait_for` bounds one awaitable. A semaphore limits how many operations are in flight, which is how you respect a provider's rate limit, and `asyncio.to_thread` (3.9) runs a blocking function in a thread so it does not freeze the loop.

```python
import asyncio
import time

async def main():
    try:
        async with asyncio.timeout(0.05):            # 3.11+
            await asyncio.sleep(1)
        timed_out = False
    except TimeoutError:
        timed_out = True
    result = await asyncio.wait_for(asyncio.sleep(0.01, result="done"), timeout=1)

    limit = asyncio.Semaphore(2)                     # at most two calls in flight
    in_flight = peak = 0

    async def limited(i):
        nonlocal in_flight, peak
        async with limit:
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return i

    ordered = await asyncio.gather(*(limited(i) for i in range(6)))
    await asyncio.to_thread(time.sleep, 0.01)        # blocking code, off the event loop
    return timed_out, result, ordered, peak

assert asyncio.run(main()) == (True, "done", [0, 1, 2, 3, 4, 5], 2)
```

The asyncio mistakes interviewers probe: calling a blocking function (`time.sleep`, a synchronous HTTP client) inside a coroutine, which stalls every other task; calling a coroutine function without awaiting it, which creates a coroutine that never runs (Python warns "coroutine ... was never awaited"); creating tasks without keeping a reference or awaiting them, so their exceptions vanish; and catching `CancelledError` without re-raising it.

### 49a.26.5 `queue`, `asyncio.Queue` and producer–consumer

The queues in 49a.13.4 are the safe way to pass work between threads or coroutines: a bounded queue gives backpressure, and a sentinel value or `task_done`/`join` coordinates shutdown. Prefer passing messages through a queue to sharing mutable objects under locks.

### 49a.26.6 Free-threaded Python and subinterpreters

The free-threaded build (PEP 703) is a separately compiled interpreter, usually installed as `python3.13t` or `python3.14t`, in which threads run Python code in parallel. It was experimental in 3.13; PEP 779 made it supported in 3.14, but not the default. Single-threaded code runs slower on it: What's New in 3.14 puts the penalty at roughly 5 to 10 percent depending on platform and compiler, and the free-threading HOWTO measures an average of about 1 percent on macOS on ARM to 8 percent on x86-64 Linux. Importing an extension that has not declared support re-enables the GIL with a warning, and data races in your own code become real, so locks and queues matter more.

```python
import sys
import sysconfig

free_threaded_build = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))   # how the interpreter was built
gil_enabled = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True   # 3.13+: the run-time state
assert gil_enabled or free_threaded_build      # the GIL can only be off on a free-threaded build
```

Python 3.12 gave each subinterpreter its own GIL (PEP 684), and 3.14 exposes them in the standard library (PEP 734): `concurrent.interpreters` creates isolated interpreters in the same process, which communicate through queues and by copying (mostly pickling) data, and `concurrent.futures.InterpreterPoolExecutor` runs functions in a pool of them. They give parallelism for CPU-bound work with less overhead than processes, but not every extension module supports them yet.

```python
# requires: 3.14
import math
from concurrent import interpreters
from concurrent.futures import InterpreterPoolExecutor

interp = interpreters.create()
assert interp.call(math.factorial, 10) == 3628800      # runs inside an isolated interpreter
interp.close()

with InterpreterPoolExecutor(max_workers=2) as pool:   # each worker has its own interpreter and GIL
    assert list(pool.map(math.factorial, [5, 6])) == [120, 720]
```

## 49a.27 Standard-library essentials for daily work

### 49a.27.1 `datetime` and `zoneinfo`

Use aware datetimes (with a `tzinfo`) for anything that crosses machines or users: store and compute in UTC, and convert to a named zone (`zoneinfo.ZoneInfo`, 3.9) only for display. Naive and aware datetimes cannot be compared. `datetime.UTC` (3.11) is an alias for `timezone.utc`; `datetime.utcnow()` returns a naive value and is deprecated since 3.12 in favor of `datetime.now(UTC)`. Since 3.11, `fromisoformat` parses most ISO 8601 strings, including a trailing `Z`. On Windows, `zoneinfo` may need the `tzdata` package for its time-zone database.

```python
from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

berlin, new_york = ZoneInfo("Europe/Berlin"), ZoneInfo("America/New_York")
meeting = datetime(2026, 10, 3, 15, 0, tzinfo=berlin)
assert meeting.utcoffset() == timedelta(hours=2)               # summer time in October
assert meeting.astimezone(new_york).hour == 9                   # the same instant elsewhere
assert meeting.astimezone(UTC).isoformat() == "2026-10-03T13:00:00+00:00"

before = datetime(2026, 3, 29, 1, 30, tzinfo=berlin)            # clocks jump forward at 2:00
later = before.astimezone(UTC) + timedelta(hours=1)             # add real elapsed time in UTC
assert later.astimezone(berlin).isoformat() == "2026-03-29T03:30:00+02:00"

try:
    datetime(2026, 10, 3, 12, 0) < meeting                      # naive versus aware
except TypeError:
    pass
assert datetime.fromisoformat("2026-10-03T12:00:00Z").tzinfo == timezone.utc
assert date(2026, 10, 3).strftime("%A %d %B %Y") == "Saturday 03 October 2026"
assert datetime.strptime("03/10/2026", "%d/%m/%Y").date() == date(2026, 10, 3)
assert (date(2026, 12, 25) - date(2026, 10, 3)).days == 83
```

### 49a.27.2 `re`

Write patterns as raw strings and compile the ones you reuse. `match` anchors at the start, `fullmatch` at both ends, `search` scans; `findall` returns strings (or tuples of groups), `finditer` returns match objects; `sub` replaces with backreferences; named groups `(?P<name>...)` make code readable. Quantifiers are greedy by default (`.*` takes as much as possible); add `?` for the shortest match. `re.VERBOSE` allows comments inside patterns. Nested quantifiers such as `(a+)+` can backtrack exponentially on hostile input, so do not run user-supplied patterns or vulnerable patterns on untrusted text.

```python
import re

LOG = re.compile(r"(?P<level>INFO|ERROR) (?P<service>\w+): (?P<message>.*)")
m = LOG.match("ERROR billing: card declined")
assert m.group("level") == "ERROR" and m["service"] == "billing"
assert m.groupdict() == {"level": "ERROR", "service": "billing", "message": "card declined"}
assert LOG.match("DEBUG x: y") is None

html = "<b>bold</b> and <i>italic</i>"
assert re.findall(r"<(.+)>", html) == ["b>bold</b> and <i>italic</i"]   # greedy
assert re.findall(r"<(.+?)>", html) == ["b", "/b", "i", "/i"]           # non-greedy

assert re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3.\2.\1", "due 2026-10-03") == "due 03.10.2026"
assert re.split(r"[,;]\s*", "a, b;c") == ["a", "b", "c"]
assert re.fullmatch(r"[A-Z]{3}-\d{4}", "ABC-1234") and not re.fullmatch(r"[A-Z]{3}-\d{4}", "ABC-12345")
assert [m.start() for m in re.finditer("a", "banana")] == [1, 3, 5]
assert re.search(r"^total", "items\ntotal: 3", re.MULTILINE)
assert re.escape("1+1=2?") == r"1\+1=2\?"

```

### 49a.27.3 `logging`

Each module gets its own logger with `logging.getLogger(__name__)`; the application configures handlers and levels once, at its entry point (`logging.basicConfig` or `logging.config.dictConfig`), and libraries never configure logging themselves. Pass arguments separately (`logger.info("charged %s", amount)`) so formatting happens only when the record is emitted, and attach context through `extra` or a structured-logging formatter.

```python
import io
import logging

stream = io.StringIO()
logger = logging.getLogger("brushup.payments")
handler = logging.StreamHandler(stream)
handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(request_id)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

logger.debug("not emitted: below the logger's level")
logger.info("charged %s cents", 1250, extra={"request_id": "r-42"})
assert stream.getvalue() == "INFO brushup.payments r-42 charged 1250 cents\n"
logger.removeHandler(handler)
```

### 49a.27.4 `argparse`

```python
import argparse
import contextlib
import io

parser = argparse.ArgumentParser(prog="export")
parser.add_argument("source")                                   # positional
parser.add_argument("--format", choices=["csv", "json"], default="csv")
parser.add_argument("--limit", type=int, default=100)
parser.add_argument("-v", "--verbose", action="store_true")

args = parser.parse_args(["orders.db", "--format", "json", "--limit", "5", "-v"])
assert (args.source, args.format, args.limit, args.verbose) == ("orders.db", "json", 5, True)

with contextlib.redirect_stderr(io.StringIO()) as err:
    try:
        parser.parse_args(["orders.db", "--limit", "many"])     # a usage error exits with code 2
    except SystemExit as exit_info:
        assert exit_info.code == 2
assert "invalid int value" in err.getvalue()
```

### 49a.27.5 `sqlite3`

`sqlite3` is a full SQL database in the standard library, ideal for local tools, tests and caches. Always pass values as parameters (`?` placeholders), never with string formatting, which is how SQL injection happens. The connection's context manager wraps a transaction (commit on success, rollback on an exception) but does not close the connection; use `contextlib.closing` for that.

```python
import sqlite3
from contextlib import closing

with closing(sqlite3.connect(":memory:")) as conn:
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, team TEXT)")
    with conn:                                                    # one transaction
        conn.executemany("INSERT INTO users (name, team) VALUES (?, ?)",
                         [("ana", "eng"), ("bo", "ops"), ("cy", "eng")])

    hostile = "ana'; DROP TABLE users; --"
    assert conn.execute("SELECT id FROM users WHERE name = ?", (hostile,)).fetchall() == []

    conn.row_factory = sqlite3.Row                                # rows addressable by column name
    assert conn.execute("SELECT name FROM users WHERE id = ?", (2,)).fetchone()["name"] == "bo"

    try:
        with conn:
            conn.execute("INSERT INTO users (name, team) VALUES (?, ?)", ("di", "eng"))
            conn.execute("INSERT INTO users (name) VALUES (NULL)")   # violates NOT NULL
    except sqlite3.IntegrityError:
        pass
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3   # both inserts rolled back
```

### 49a.27.6 `subprocess`

Run other programs with `subprocess.run`, passing the command as a list (no shell, so no shell injection), with `capture_output=True, text=True` to collect output, `check=True` to raise on a non-zero exit code, and a `timeout`. Use `shell=True` only with fixed strings you wrote yourself.

```python
import subprocess
import sys

result = subprocess.run([sys.executable, "-c", "print('hello from a child')"],
                        capture_output=True, text=True, check=True, timeout=30)
assert result.stdout == "hello from a child\n" and result.returncode == 0
try:
    subprocess.run([sys.executable, "-c", "import sys; sys.exit(3)"], check=True, timeout=30)
except subprocess.CalledProcessError as err:
    assert err.returncode == 3
```

### 49a.27.7 `unittest` and `doctest`

`unittest` is the standard library's xUnit framework (test classes, `setUp`, assertion methods, `unittest.mock` for test doubles); `doctest` runs the interactive examples in docstrings, which keeps documentation honest. Most projects run both through pytest, which also runs plain `assert`-based test functions.

```python
import io
import unittest

def slugify(text):
    return "-".join(text.lower().replace("-", " ").split())

class SlugifyTest(unittest.TestCase):
    def test_collapses_spaces_and_dashes(self):
        self.assertEqual(slugify("Python  Brush-Up"), "python-brush-up")

suite = unittest.defaultTestLoader.loadTestsFromTestCase(SlugifyTest)
result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
assert result.wasSuccessful() and result.testsRun == 1
```

This chapter's own `pycon` blocks are doctests: the runner in 49a.1 hands them to `doctest.DocTestRunner`.

### 49a.27.8 The rest of the toolbox

| Module | Use it for |
|---|---|
| `functools`, `itertools`, `collections`, `dataclasses`, `typing`, `enum`, `contextlib` | sections 49a.11 to 49a.22 |
| `pathlib`, `shutil`, `tempfile`, `os` | files and directories |
| `json`, `csv`, `tomllib` (3.11), `sqlite3` | data formats and storage |
| `secrets` | tokens and passwords; `random` is not cryptographically secure |
| `hashlib`, `hmac`, `uuid`, `base64` | digests, signatures, identifiers, encodings |
| `statistics`, `math`, `random`, `decimal`, `fractions` | numbers |
| `textwrap`, `string`, `unicodedata`, `re` | text |
| `graphlib` (3.9) | topological sorting of dependencies |
| `urllib.parse` | splitting, building and encoding URLs |
| `concurrent.futures`, `asyncio`, `threading`, `queue`, `multiprocessing` | concurrency |
| `importlib`, `importlib.metadata`, `sys`, `sysconfig` | the interpreter and installed packages |

```python
import hashlib
import secrets
import statistics
from graphlib import TopologicalSorter
from urllib.parse import parse_qs, urlencode, urlsplit

assert len(secrets.token_urlsafe(16)) >= 16                     # unpredictable tokens
assert hashlib.sha256(b"abc").hexdigest().startswith("ba7816bf")
assert statistics.median([3, 1, 4, 1, 5]) == 3
steps = TopologicalSorter({"deploy": {"build", "test"}, "test": {"build"}})
assert list(steps.static_order()) == ["build", "test", "deploy"]
parts = urlsplit("https://api.example.com/v1/search?q=python&page=2")
assert parts.netloc == "api.example.com" and parse_qs(parts.query) == {"q": ["python"], "page": ["2"]}
assert urlencode({"q": "a b", "n": 1}) == "q=a+b&n=1"
```

## 49a.28 What changed by version

Interviewers ask what is new to see whether you keep up, and production codebases pin versions. Support status on 3 October 2026: 3.14 receives bug fixes; 3.11, 3.12 and 3.13 receive security fixes only; 3.10 reached end of life on 1 October 2026; 3.15 is a release candidate, with the final release scheduled for 9 October 2026.

| Version (release) | Language | Standard library and runtime | Typing |
|---|---|---|---|
| 3.8 (14 Oct 2019) | `:=` (PEP 572); positional-only parameters `/` (PEP 570); `f"{x=}"` | `functools.cached_property`; `math.prod`, `math.isqrt`; `pow(x, -1, m)`; `reversed(dict)`; `importlib.metadata`; `SyntaxWarning` for `is` with a literal | `Literal`, `Final`, `Protocol`, `TypedDict` |
| 3.9 (5 Oct 2020) | dict `\|` and `\|=` (PEP 584); new PEG parser | `str.removeprefix`/`removesuffix`; `zoneinfo`; `graphlib`; `functools.cache`; `math.lcm`; `asyncio.to_thread` | `list[int]` and other built-in generics (PEP 585); `Annotated` |
| 3.10 (4 Oct 2021) | `match`/`case` (PEPs 634 to 636); parenthesized context managers; much better error messages | `zip(strict=True)`; `itertools.pairwise`; `int.bit_count`; `bisect` `key=`; dataclass `slots=`, `kw_only=`; `aiter`/`anext`; `Counter.total` | `X \| Y` (PEP 604); `ParamSpec`; `TypeAlias`; `TypeGuard` |
| 3.11 (24 Oct 2022) | exception groups and `except*` (PEP 654); `add_note` (PEP 678); precise error locations in tracebacks | 1.25 times faster on average; zero-cost `try`; `tomllib`; `asyncio.TaskGroup`, `asyncio.timeout`; `enum.StrEnum`; `datetime.UTC`; broader `fromisoformat`; int-to-str digit limit | `Self`; `LiteralString`; `TypeVarTuple`; `Required`/`NotRequired`; `assert_never`; `reveal_type` |
| 3.12 (2 Oct 2023) | `def f[T]`, `class C[T]`, `type X = ...` (PEP 695); f-strings in the grammar (PEP 701) | `itertools.batched`; `math.sumprod`; Neumaier `sum()` for floats; per-interpreter GIL (PEP 684); `sys.monitoring` (PEP 669); inlined comprehensions (PEP 709); `distutils` removed; `utcnow()` deprecated; `OrderedDict` repr changed | `@override`; `Unpack[TypedDict]` for `**kwargs` |
| 3.13 (7 Oct 2024) | docstring indentation stripped at compile time | new interactive REPL; experimental free-threaded build (PEP 703) and JIT (PEP 744); defined `locals()` semantics (PEP 667); `copy.replace`; `batched(strict=)`; 19 legacy modules removed (PEP 594) | type parameter defaults (PEP 696); `warnings.deprecated`; `ReadOnly`; `TypeIs` |
| 3.14 (7 Oct 2025) | template strings `t"..."` (PEP 750); lazy annotations (PEPs 649, 749); `except A, B:` without parentheses (PEP 758); `SyntaxWarning` for control flow leaving `finally` (PEP 765) | `concurrent.interpreters` and `InterpreterPoolExecutor` (PEP 734); free-threaded build supported (PEP 779); `compression.zstd`; `annotationlib`; `map(strict=)`; heapq max-heap functions; `functools.Placeholder`; `uuid.uuid7`; REPL syntax highlighting; `python -m asyncio ps`; forkserver default on POSIX except macOS; incremental GC in 3.14.0 to 3.14.4 only | `typing.Union` and `X \| Y` are one type |
| 3.15 (**pre-release**: release candidate 3 on 2 Oct 2026, final scheduled for 9 Oct 2026) | explicit lazy imports `lazy import json` (PEP 810); unpacking in comprehensions `[*xs for xs in lists]` (PEP 798) | `frozendict` (PEP 814) and `sentinel` (PEP 661) built-ins; UTF-8 as the default encoding (PEP 686); a `profiling` package with a sampling profiler (PEP 799) | `TypedDict` extra items (PEP 728); `TypeForm` (PEP 747) |

The 3.15 row lists only features that appear in the official What's New in Python 3.15 at release candidate 3, plus the dates in PEP 790. Python 3.15 was not released on 3 October 2026, so none of its features is tested in this chapter, and details can still change before the final release.

### 49a.28.1 Template strings (3.14)

An f-string becomes a `str` immediately, which is wrong when values must be treated differently from the literal text: escaped for HTML, passed as SQL parameters, or kept as structured log fields. A t-string (PEP 750) has the same syntax with a `t` prefix but produces a `string.templatelib.Template` object. Iterating over it yields the literal strings and `Interpolation` objects (each with `value`, `expression`, `conversion` and `format_spec`) in order, and a processing function decides how to combine them.

```python
# requires: 3.14
from html import escape
from string.templatelib import Interpolation, Template

def convert(value, conversion):
    return {"r": repr, "s": str, "a": ascii}[conversion](value) if conversion else value

def render_html(template: Template) -> str:
    """Escape every interpolated value; keep the literal markup as written."""
    parts = []
    for item in template:                             # str parts and Interpolations, in order
        if isinstance(item, Interpolation):
            value = format(convert(item.value, item.conversion), item.format_spec)
            parts.append(escape(value))
        else:
            parts.append(item)
    return "".join(parts)

user = "<script>alert('x')</script>"
page = t"<p>Hello {user}!</p>"
assert type(page) is Template
assert page.strings == ("<p>Hello ", "!</p>") and page.values == (user,)
assert page.interpolations[0].expression == "user"
assert render_html(page) == "<p>Hello &lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;!</p>"

def to_sql(template: Template) -> tuple[str, list]:
    """Turn a t-string into a parameterized query: values never enter the SQL text."""
    sql, params = [], []
    for item in template:
        if isinstance(item, Interpolation):
            sql.append("?")
            params.append(item.value)
        else:
            sql.append(item)
    return "".join(sql), params

name = "ana'; DROP TABLE users; --"
query, params = to_sql(t"SELECT * FROM users WHERE name = {name} AND age > {30}")
assert query == "SELECT * FROM users WHERE name = ? AND age > ?" and params == [name, 30]

amount = 1234.5
assert f"{amount:,.2f}" == "1,234.50"                 # an f-string is already a str
assert t"{amount:,.2f}".interpolations[0].format_spec == ",.2f"   # a t-string leaves it to the renderer
```

### 49a.28.2 Smaller additions worth knowing

```python
# requires: 3.13
import copy
from collections import namedtuple
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Point:
    x: int
    y: int

Pair = namedtuple("Pair", "a b")
assert copy.replace(Point(1, 2), y=5) == Point(1, 5)          # 3.13+: one function, many types
assert copy.replace(date(2026, 10, 3), day=9) == date(2026, 10, 9)
assert copy.replace(Pair(1, 2), b=3) == Pair(1, 3)
```

```python
# requires: 3.14
import uuid
from functools import Placeholder, partial

try:
    list(map(pow, [2, 3], [2], strict=True))       # 3.14+: map checks lengths like zip
except ValueError:
    pass
square = partial(pow, Placeholder, 2)               # 3.14+: leave a positional slot open
assert square(7) == 49
assert uuid.uuid7().version == 7                    # 3.14+: time-ordered UUIDs
```

## 49a.29 Design patterns in Python

The "Gang of Four" catalog (Gamma, Helm, Johnson and Vlissides, 1994) names recurring designs for object-oriented code; many exist to work around languages without first-class functions, so in Python several collapse into a function, a dict or a module. Interviewers want the intent and the lighter Python form. The list of patterns and their order follow the design-pattern series on labuladong's site; the explanations and code here are this book's own. Each pattern below has a tested example, the Pythonic form, and when not to use it.

### 49a.29.1 Singleton

*Intent:* exactly one instance, reachable from anywhere (configuration, a connection pool, an API client). *In Python:* a module is already a singleton (49a.24.1), so a module-level instance is the simplest form, and `functools.cache` on a factory gives a lazy one that tests can reset. The classic `__new__` override works, but any `__init__` runs again on every call. *When not to use it:* usually. A singleton is global mutable state that hides dependencies, leaks state between tests and needs a lock if several threads can create it first; create one instance at the entry point and pass it in (dependency injection).

```python
import functools

class Settings:                               # the classic form: __new__ returns one shared instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.values = {}
        return cls._instance

assert Settings() is Settings()
Settings().values["debug"] = True
assert Settings().values == {"debug": True}   # global state: every caller and every test sees it

class HttpClient:
    def __init__(self, base_url):
        self.base_url = base_url

@functools.cache
def get_client():                             # lazily created once
    return HttpClient("https://api.example.com")

assert get_client() is get_client()
get_client.cache_clear()                      # and resettable in tests

def handle_request(client: HttpClient):       # dependency injection: the caller decides
    return client.base_url

assert handle_request(HttpClient("http://test")) == "http://test"
```

### 49a.29.2 Factory Method

*Intent:* let a method or function decide which concrete class to instantiate, so callers depend only on the common interface. *In Python:* classes are callables, so a dict from names to classes is a complete factory; `@classmethod` alternative constructors (49a.17.3) are the other common form. *When not to use it:* when the caller already knows the class, call it; the indirection pays off only when data (a setting, a file extension) makes the choice.

```python
import csv
import io
import json

class JsonExporter:
    def export(self, rows):
        return json.dumps(rows)

class CsvExporter:
    def export(self, rows):
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()

EXPORTERS = {"json": JsonExporter, "csv": CsvExporter}   # classes are factories already

def make_exporter(fmt: str):
    try:
        return EXPORTERS[fmt]()
    except KeyError:
        raise ValueError(f"unknown format {fmt!r}") from None

rows = [{"id": 1, "name": "ana"}]
assert make_exporter("json").export(rows) == '[{"id": 1, "name": "ana"}]'
assert make_exporter("csv").export(rows).splitlines() == ["id,name", "1,ana"]
```

### 49a.29.3 Abstract Factory

*Intent:* create families of related objects that must be used together (storage and queue for one cloud, or fakes for tests) without naming their classes. *In Python:* an object whose attributes are the factories, here a frozen dataclass of callables; swapping the whole family is one argument. *When not to use it:* when the objects need not match, pass the individual factories or instances.

```python
from collections.abc import Callable
from dataclasses import dataclass

class LocalStorage:
    def __init__(self):
        self.blobs = {}

    def put(self, key, data):
        self.blobs[key] = data

class LocalQueue:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)

class ObjectStoreStorage(LocalStorage):       # stand-ins for a cloud family
    pass

class ManagedQueue(LocalQueue):
    pass

@dataclass(frozen=True)
class Platform:                               # the abstract factory: one family per instance
    storage: Callable[[], LocalStorage]
    queue: Callable[[], LocalQueue]

LOCAL = Platform(storage=LocalStorage, queue=LocalQueue)
CLOUD = Platform(storage=ObjectStoreStorage, queue=ManagedQueue)

def ingest(platform: Platform, doc_id: str, text: str):
    storage, queue = platform.storage(), platform.queue()   # always a matching pair
    storage.put(doc_id, text)
    queue.send({"event": "stored", "id": doc_id})
    return storage, queue

storage, queue = ingest(LOCAL, "d1", "hello")
assert storage.blobs == {"d1": "hello"} and queue.messages == [{"event": "stored", "id": "d1"}]
storage, queue = ingest(CLOUD, "d2", "hi")
assert (type(storage), type(queue)) == (ObjectStoreStorage, ManagedQueue)
```

### 49a.29.4 Builder

*Intent:* assemble a complex object step by step, validating as you go, instead of calling a constructor with a dozen parameters. *In Python:* keyword arguments with defaults and dataclasses remove most of the need. *When not to use it:* when one call with keyword arguments describes the object; keep builders for fluent APIs (query, request and test-data builders) and for objects validated as a whole before they exist.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Request:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    timeout: float = 10.0

class RequestBuilder:
    def __init__(self, method, url):
        self._method, self._url = method, url
        self._headers, self._params, self._timeout = {}, {}, 10.0

    def header(self, name, value):
        self._headers[name] = value
        return self                           # returning self allows chaining

    def param(self, name, value):
        self._params[name] = value
        return self

    def timeout(self, seconds):
        if seconds <= 0:
            raise ValueError("timeout must be positive")
        self._timeout = seconds
        return self

    def build(self):
        return Request(self._method, self._url, dict(self._headers), dict(self._params), self._timeout)

req = RequestBuilder("GET", "/search").header("Accept", "json").param("q", "python").timeout(2).build()
assert req == Request("GET", "/search", {"Accept": "json"}, {"q": "python"}, 2)

# The Pythonic default: keyword arguments with defaults say the same thing.
assert Request("GET", "/search", headers={"Accept": "json"}, params={"q": "python"}, timeout=2) == req
```

### 49a.29.5 Prototype

*Intent:* create objects by copying a configured instance instead of building from scratch. *In Python:* `copy.copy`, `copy.deepcopy`, `dataclasses.replace` and, since 3.13, `copy.replace`; customize with `__copy__` and `__deepcopy__`. The classic bug is a shallow copy that shares nested mutable state with the prototype. *When not to use it:* when construction is cheap and explicit, call the constructor; `deepcopy` is slow on large structures and duplicates things that must not be copied, such as locks, open files and connections.

```python
import copy
from dataclasses import dataclass, field, replace

@dataclass
class Document:
    title: str
    sections: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

template = Document("Incident report", ["Summary", "Timeline", "Actions"], {"owner": "sre"})

draft = copy.deepcopy(template)               # an independent clone
draft.title = "Incident 2026-10-03"
draft.sections.append("Follow-ups")
assert template.sections == ["Summary", "Timeline", "Actions"]

shallow = copy.copy(template)                 # shares the inner list with the prototype
shallow.sections.append("Oops")
assert template.sections[-1] == "Oops"

variant = replace(template, title="Postmortem")   # a shallow copy with changed fields
assert variant.title == "Postmortem" and variant.meta is template.meta
```

### 49a.29.6 Adapter

*Intent:* make an existing class usable through the interface a client expects, by wrapping it and translating calls. *In Python:* a small wrapper class (composition, not inheritance) or a plain function; with duck typing and Protocols, the target interface is often just "has these methods". *When not to use it:* if you own both sides, change one interface instead; if one call needs converting, a function is enough.

```python
class LegacyWeather:                          # a third-party class with the wrong interface
    def get_temp_f(self, city_code):
        return {"BER": 59.0}[city_code]

class LegacyWeatherAdapter:                   # provides temperature_c(city), as our code expects
    CODES = {"Berlin": "BER"}

    def __init__(self, legacy: LegacyWeather):
        self._legacy = legacy

    def temperature_c(self, city: str) -> float:
        fahrenheit = self._legacy.get_temp_f(self.CODES[city])
        return round((fahrenheit - 32) * 5 / 9, 1)

def report(provider, city):
    return f"{city}: {provider.temperature_c(city)} C"

assert report(LegacyWeatherAdapter(LegacyWeather()), "Berlin") == "Berlin: 15.0 C"
```

### 49a.29.7 Composite

*Intent:* treat single objects and groups through the same interface, so trees (file systems, UI layouts, an agent's plan of steps and sub-plans) can be processed recursively without type checks. *In Python:* one shared method and recursion. *When not to use it:* for plain data trees (parsed JSON, nested dicts and lists), one recursive function is simpler than a class per node type; the pattern pays off when nodes carry behavior.

```python
class File:
    def __init__(self, name, size):
        self.name, self._size = name, size

    def size(self):
        return self._size

class Folder:
    def __init__(self, name, *children):
        self.name, self.children = name, list(children)

    def size(self):                           # the same interface as File
        return sum(child.size() for child in self.children)

root = Folder("root", File("a.txt", 100), Folder("src", File("main.py", 250), File("util.py", 50)))
assert root.size() == 400 and root.children[1].size() == 300
```

### 49a.29.8 Decorator (the pattern) versus Python decorators

*Intent of the pattern:* wrap an object in another object with the same interface to add behavior, at run time and per object, stacking as many layers as needed. Python's `@decorator` syntax (49a.20) is a different, related thing: it wraps *functions or classes*, once, at definition time. Both rely on wrapping and delegation; the pattern composes objects dynamically, the syntax transforms definitions statically. *When not to use it:* when every object needs the same extra behavior, a function decorator or subclass is simpler; deep wrapper stacks make tracebacks hard to follow.

```python
class EmailNotifier:
    def send(self, message):
        return [f"email: {message}"]

class NotifierDecorator:                      # same interface, delegates to the wrapped object
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def send(self, message):
        return self._wrapped.send(message)

class WithSlack(NotifierDecorator):
    def send(self, message):
        return super().send(message) + [f"slack: {message}"]

class WithSms(NotifierDecorator):
    def send(self, message):
        return super().send(message) + [f"sms: {message}"]

critical = WithSms(WithSlack(EmailNotifier()))   # composed at run time, per object
assert critical.send("db down") == ["email: db down", "slack: db down", "sms: db down"]
```

### 49a.29.9 Bridge

*Intent:* separate an abstraction from its implementation so the two can vary independently, avoiding a subclass for every combination (three report types times three output formats would otherwise be nine classes). *In Python:* composition, with the implementation passed in. *When not to use it:* when only one dimension varies, a parameter or subclass covers it.

```python
class MarkdownRenderer:
    def heading(self, text):
        return f"# {text}"

    def item(self, text):
        return f"- {text}"

class HtmlRenderer:
    def heading(self, text):
        return f"<h1>{text}</h1>"

    def item(self, text):
        return f"<li>{text}</li>"

class IncidentReport:                         # the abstraction holds an implementation
    def __init__(self, renderer, actions):
        self.renderer, self.actions = renderer, actions

    def render(self):
        lines = [self.renderer.heading("Incident")]
        lines += [self.renderer.item(a) for a in self.actions]
        return "\n".join(lines)

actions = ["roll back", "add alert"]
assert IncidentReport(MarkdownRenderer(), actions).render() == "# Incident\n- roll back\n- add alert"
assert IncidentReport(HtmlRenderer(), actions).render().startswith("<h1>")
```

### 49a.29.10 Observer

*Intent:* let a subject notify any number of subscribers without knowing who they are. *In Python:* a dict of lists of callables; return an unsubscribe function; iterate over a copy so handlers can unsubscribe during a publish; use `weakref` (49a.25.1) when the subject must not keep subscribers alive, and queues across threads or coroutines. *When not to use it:* with one known receiver, call it directly; when order, failures or delivery guarantees matter (here one raising handler stops the rest), make explicit calls or use a queue with retries.

```python
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event, handler):
        self._subscribers[event].append(handler)
        return lambda: self._subscribers[event].remove(handler)   # call it to unsubscribe

    def publish(self, event, **payload):
        for handler in list(self._subscribers[event]):            # a copy: safe to unsubscribe
            handler(**payload)

bus = EventBus()
received = []
unsubscribe = bus.subscribe("order_paid", lambda order_id: received.append(("email", order_id)))
bus.subscribe("order_paid", lambda order_id: received.append(("ledger", order_id)))
bus.publish("order_paid", order_id=7)
unsubscribe()
bus.publish("order_paid", order_id=8)
assert received == [("email", 7), ("ledger", 7), ("ledger", 8)]
```

### 49a.29.11 Strategy

*Intent:* choose an algorithm at run time behind a common interface. *In Python:* functions are first-class, so a strategy is usually a function passed as an argument (`key=` in `sorted` is the standard library's own example), or a closure when it needs configuration; use classes only when strategies carry significant state or several related methods. *When not to use it:* with one algorithm, or a choice that never changes at run time, call it directly.

```python
def no_discount(total):
    return total

def percent_off(rate):                        # a configured strategy is a closure
    def strategy(total):
        return round(total * (1 - rate), 2)
    return strategy

def bulk_discount(total):
    return total - 10 if total >= 100 else total

def checkout(total, pricing=no_discount):
    return pricing(total)

assert checkout(80) == 80
assert checkout(80, percent_off(0.25)) == 60.0
assert checkout(120, bulk_discount) == 110
best = min([no_discount, percent_off(0.05), bulk_discount], key=lambda s: s(120))
assert best is bulk_discount
```

### 49a.29.12 Patterns the language already provides

Other classic patterns are built into the language: Iterator is the iterator protocol (49a.19), Command is any callable (a function, a `partial`, an object with `__call__`), Template Method is a base class calling overridable hooks (49a.18.1), and Visitor is often a `functools.singledispatch` function (49a.18.5).

**Interview line:** *"I know the patterns by intent, and in Python most get lighter: a strategy is a function, a factory a dict of classes, a singleton a module-level object or better an injected dependency, observers a list of callables, and a builder mostly keyword arguments. I use the class-based forms when there is real state or a family of objects to keep consistent."*

## 49a.30 Thirty classic gotchas

This is the list to reread the evening before an interview. Each row names the trap, the fix and the section whose example demonstrates it; the five that no earlier section shows are demonstrated after the table. Cover the Fix column and predict it before reading.

| # | Gotcha | Fix | Shown in |
|---|---|---|---|
| 1 | A mutable default (`def f(x, items=[])`) is shared by every call | default to `None`; create the list inside | 49a.15.3 |
| 2 | `[lambda: n for n in range(3)]` all return 2: closures capture variables | `lambda n=n: n`, or `partial` | 49a.15.5 |
| 3 | `is` seems to compare values, thanks to small-int caching and interning | `==` for values; `is` for `None` and sentinels | 49a.1.2 |
| 4 | Removing from a list while looping over it skips elements | build a new list, or assign to `xs[:]` | 49a.6.3 |
| 5 | Resizing a dict or set during iteration raises `RuntimeError` | iterate over `list(d)` | 49a.6.3 |
| 6 | `0.1 + 0.2 != 0.3` | `math.isclose`; `Decimal` built from strings for money | 49a.3.2 |
| 7 | `config.copy()` shares the nested dicts and lists | `copy.deepcopy` | 49a.8.5 |
| 8 | `[[0] * n] * m` is m references to one row | `[[0] * n for _ in range(m)]` | 49a.8.5 |
| 9 | A mutable class attribute is shared by every instance | create it in `__init__` | 49a.17.1 |
| 10 | `s += piece` in a loop can be quadratic | collect pieces, then `"".join` | 49a.7.6 |
| 11 | A bare `except:` also catches `KeyboardInterrupt` and `SystemExit` | `except Exception`, or narrower | 49a.23.1 |
| 12 | Defining `__eq__` makes instances unhashable | define `__hash__` over the same immutable fields | 49a.17.8 |
| 13 | Iterators are one-shot: a second pass sees nothing | `list()` them, or `itertools.tee` | 49a.19.6 |
| 14 | Reading `d[k]` on a `defaultdict` inserts `k` | look with `d.get(k)` or `k in d` | 49a.11.4 |
| 15 | `xs = xs.sort()` loses the list: `sort()` returns `None` | `sorted(xs)` for a new list | 49a.8.4 |
| 16 | Comparisons chain: `False == False in [False]` is true | parenthesize mixed comparisons | 49a.4.3 |
| 17 | `-7 // 2 == -4`: floor, not truncation | truncate explicitly when porting C or Java | 49a.4.1 |
| 18 | `round(2.5) == 2` and `round(0.285, 2) == 0.28` | `Decimal.quantize` with an explicit rounding mode | 49a.3.2 |
| 19 | Assigning a global name in a function makes it local: `UnboundLocalError` | pass values in and out, or `global` | 49a.2.3 |
| 20 | `dict.fromkeys(keys, [])` gives every key the same list | `{k: [] for k in keys}` | 49a.11.1 |
| 21 | `("admin")` is a string, so `in` tests substrings | a trailing comma: `("admin",)` | below |
| 22 | `str.strip(chars)` removes a set of characters, not a suffix | `removeprefix` and `removesuffix` | below |
| 23 | A comprehension in a class body cannot see class attributes | compute it outside the class body | 49a.14.2 |
| 24 | `value or default` also replaces 0 and `""` | `default if value is None else value` | 49a.4.4 |
| 25 | `1`, `1.0` and `True` are the same dict key | do not mix numeric types as keys | 49a.11.3 |
| 26 | An uncalled method is truthy; an unawaited coroutine never runs | call it; await it | below |
| 27 | `return` in `finally` discards the exception in flight | never leave `finally` early; 3.14 warns | 49a.23.4 |
| 28 | JSON turns tuples into lists and keys into strings | convert or validate after loading | 49a.22.5 |
| 29 | A variable named `list` or `id` hides the built-in | pick another name | below |
| 30 | `assert (cond, "msg")` never fails: the tuple is true | `assert cond, "msg"` | below |

```python
import asyncio
import warnings

allowed = ("admin")                                   # 21: a string, not a tuple
assert "adm" in allowed and "adm" not in ("admin",)

assert "transcript.txt".rstrip(".txt") == "transcrip" # 22: every trailing ".", "t" and "x" went
assert "transcript.txt".removesuffix(".txt") == "transcript"

class Order:
    def is_paid(self):
        return False

assert bool(Order().is_paid) is True                  # 26: the method object, not its result
saved = []

async def save():
    saved.append("saved")

async def main():
    save()                                            # creates a coroutine and drops it
    await save()

with warnings.catch_warnings():
    warnings.simplefilter("ignore", RuntimeWarning)   # "coroutine 'save' was never awaited"
    asyncio.run(main())
assert saved == ["saved"]                             # only the awaited call ran

list = [1, 2, 3]                                      # 29: hides the built-in list type
try:
    list("abc")
    shadowed = False
except TypeError:
    shadowed = True
del list                                              # the built-in is visible again
assert shadowed and list("ab") == ["a", "b"]

with warnings.catch_warnings(record=True) as caught:  # 30: compiling warns...
    warnings.simplefilter("always")
    code = compile("assert (1 == 2, 'never fails')", "<demo>", "exec")
exec(code)                                            # ...and running raises nothing
assert any("always true" in str(w.message) for w in caught)
```

Five more that earlier sections demonstrate: `t[0] += [x]` on a tuple both mutates and raises (49a.2.2); the swap `a[i], a[a[i]] = ...` uses the new value for the second index (49a.2.1); the `except ... as err` name is unbound after the block (49a.5.4); naive and aware datetimes cannot be compared (49a.27.1); and `functools.lru_cache` on a method keeps every instance alive (49a.20.5).

## 49a.31 Interview questions with model answers, and a practice plan

The answers are the compressed core of what a strong candidate says; the section in parentheses has the details and code. Practice them out loud, then answer again with a small example typed from memory.

### 49a.31.1 The data model and built-in types

**1. What happens on `b = a` when `a` is a list, and how are arguments passed?** Both names refer to one list. Arguments work the same way (call by sharing): mutating a parameter is visible to the caller, rebinding it is not (49a.1.1).

**2. `is` versus `==`?** `==` compares values through `__eq__`; `is` compares identity and is for `None` and sentinels. Small-int caching makes `is` look right on values, which is the trap (49a.1.2).

**3. What makes an object hashable, and why can a list not be a dict key?** A hash that never changes, with equal objects hashing equally. A list's hash would change with its contents and strand the entry (49a.11.3, 49a.17.8).

**4. Which values are falsy?** `None`, `False`, numeric zeros, empty containers and strings, and objects whose `__bool__` or `__len__` says so; `"0"` and `[0]` are truthy (49a.3.7).

**5. What is `-7 // 2`, and why?** `-4`: `//` floors, and `%` takes the divisor's sign so that `a == (a // b) * b + a % b`; C and Java give −3 (49a.4.1).

**6. Why is `0.1 + 0.2 != 0.3`, and how do you handle money?** Binary doubles cannot represent most decimal fractions. Compare with `math.isclose`; for money, `Decimal` from strings with an explicit rounding mode, or integer cents (49a.3.2, 49a.3.3).

**7. Explain LEGB and `UnboundLocalError`.** Local, enclosing, global, built-in. Any assignment makes a name local for the whole function, so reading it first fails; `global` and `nonlocal` redirect the assignment (49a.2.3).

### 49a.31.2 Collections

**8. List, tuple, set or dict?** A list for an ordered, changing sequence; a tuple for a fixed record or composite key; a set for membership; a dict for lookup by key. Then `deque`, `heapq` and `Counter` (49a.8 to 49a.13).

**9. How does a dict work, and is it ordered?** A hash table: the hash picks a slot, equality confirms the key, collisions are probed; O(1) on average, insertion-ordered since 3.7 (49a.11).

**10. Shallow versus deep copy?** A shallow copy is a new container of the same inner objects; `copy.deepcopy` copies recursively and handles cycles, at a cost (49a.8.5).

**11. Remove duplicates while keeping order?** `list(dict.fromkeys(items))`, or a `seen` set of keys for unhashable items (49a.12).

**12. Why `deque` instead of a list for a queue?** `list.pop(0)` is O(n); `deque.popleft` is O(1), and `deque(maxlen=n)` is a ring buffer (49a.13.1).

**13. Sort records by team ascending and salary descending.** `sorted(rows, key=lambda r: (r.team, -r.salary))`, or two stable sorts, minor key first (49a.8.4).

### 49a.31.3 Functions, iteration and decorators

**14. What is wrong with `def f(x, items=[])`?** The list is created once and shared by every call that omits it; default to `None` (49a.15.3).

**15. Explain `/`, `*`, `*args` and `**kwargs`.** Before `/`: positional-only; after `*`: keyword-only; `*args` and `**kwargs` collect extras into a tuple and a dict, and unpack at call sites (49a.15.2).

**16. What is a closure, and what is the late-binding problem?** An inner function that keeps the enclosing variables alive and reads them when it runs, so loop-made functions see the last value; bind it as a default (49a.15.5).

**17. What is a decorator? Write one.** A callable that replaces a function at definition time: `@d` means `f = d(f)`. A timing decorator uses `perf_counter`, `try`/`finally` and `functools.wraps` (49a.20.1, 49a.20.5).

**18. Decorators with arguments, and stacking order?** `@retry(attempts=3)` calls a factory that returns the decorator; stacked decorators apply bottom-up and run top-down (49a.20.2, 49a.20.3).

**19. Iterable versus iterator?** An iterable hands out iterators and can be walked again; an iterator has `__next__`, returns itself from `__iter__` and is consumed once (49a.19.1).

**20. When do you use a generator instead of a list?** For large, unbounded or streaming data; a list for several passes, indexing or the length (49a.19.2, 49a.19.5).

**21. What does `yield from` do?** It yields a sub-iterator's items, forwards `send` and `throw`, and evaluates to the sub-generator's return value (49a.19.3).

**22. How does `with` work?** `__enter__`, the block, then always `__exit__` with the exception details, which can suppress it; `@contextmanager` builds one from a generator (49a.22).

### 49a.31.4 Classes and objects

**23. `@classmethod` versus `@staticmethod`?** A class method receives the class (alternative constructors that work for subclasses); a static method receives nothing and is often better as a module function (49a.17.3).

**24. How do you make an attribute private?** You cannot: `_name` is a convention, `__name` is mangled to `_Class__name` against subclass clashes, and a `property` adds validation (49a.17.4, 49a.17.5).

**25. `__repr__` versus `__str__`?** `__repr__` is the unambiguous developer view used by the REPL and containers; `__str__` is for users and falls back to `__repr__` (49a.17.7).

**26. Explain the MRO and `super()` in multiple inheritance.** C3 puts children before parents and keeps base order; `super()` is the next class in the instance's MRO, so cooperative methods each run once (49a.18.2).

**27. ABC, Protocol or duck typing?** Duck typing needs only the method; an ABC is nominal and fails at instantiation; a Protocol is structural and checked statically. ABCs for frameworks, Protocols at boundaries (49a.16.3, 49a.18.3).

**28. What is a descriptor?** A class attribute with `__get__`, `__set__` or `__delete__`; functions, `property`, `classmethod` and `cached_property` are descriptors, and data descriptors beat the instance dict (49a.18.9).

**29. What are `__slots__` for?** Fixed storage instead of a per-instance `__dict__`: less memory and no stray attributes, for classes with very many instances (49a.17.6).

**30. dataclass, NamedTuple, TypedDict or Pydantic?** NamedTuple for small immutable records, dataclass for records with defaults and validation, TypedDict for JSON-shaped dicts, Pydantic for untrusted input (49a.17.12).

**31. `__new__` versus `__init__`, and when would you write a metaclass?** `__new__` creates (immutable subclasses, caching), `__init__` initializes; a metaclass only when `__init_subclass__` and class decorators cannot do the job (49a.17.2, 49a.18.8).

### 49a.31.5 Runtime, concurrency and the rest

**32. What is the GIL, and how do you choose between threads, processes and asyncio?** One thread runs bytecode at a time in the default build, but blocking I/O releases it: threads or asyncio for I/O, processes or subinterpreters for CPU-bound Python (49a.26).

**33. How does CPython manage memory?** Reference counting plus a cycle collector; weak references observe without keeping alive; measure with `tracemalloc`, not `sys.getsizeof` (49a.25).

**34. EAFP or LBYL?** Try and catch the specific exception, which avoids races between check and use; look first when failure is common or irreversible (49a.21.5).

**35. What is new in recent Python versions?** 3.11 speed, exception groups and TaskGroup; 3.12 type-parameter syntax; 3.13 the new REPL and experimental free threading; 3.14 t-strings and lazy annotations; 3.15 lazy imports and `frozendict` (49a.28).

**36. What do type hints do at run time?** Almost nothing: they are stored (lazily since 3.14) for checkers and libraries such as dataclasses and Pydantic (49a.16).

**37. How do you report several errors at once?** Raise an `ExceptionGroup` and handle subsets with `except*`; `add_note` adds context without wrapping (49a.23.5, 49a.23.6).

**38. How do you find and fix slow Python code?** Profile first, fix the algorithm or data structure, then use built-ins and caching, and only then micro-optimize (49a.25.4, 49a.25.5).

### 49a.31.6 A ten-day practice plan

| Day | Read | Lab exercises (`labs/python-brushup/`) | Drill |
|---|---|---|---|
| 1 | 49a.1 to 49a.5 | 01 to 05 | explain names, objects and mutability aloud; questions 1 to 7 |
| 2 | 49a.6 to 49a.9 | 06 to 14 | the string and list methods of 49a.7.2 and 49a.8.1 from memory |
| 3 | 49a.10 to 49a.14 | 15 to 20 | questions 8 to 13; gotchas 4 to 8 |
| 4 | 49a.15 and 49a.16 | 21 to 23 | a closure and a keyword-only signature from memory; questions 14 to 16 |
| 5 | 49a.17 | 24 to 26 | `Vector` with all the operators, without looking |
| 6 | 49a.18 | 27 and 28 | an MRO by hand, checked with `__mro__`; questions 23 to 31 |
| 7 | 49a.19 to 49a.21 | 29 to 33 | the retry decorator and a generator pipeline from memory; questions 17 to 21 |
| 8 | 49a.22 to 49a.24 | 34 and 36 | a context manager both ways; a package with a relative import |
| 9 | 49a.25 to 49a.27 | 35 and 37 | asyncio with TaskGroup, timeout and a semaphore; question 32 |
| 10 | 49a.28 to 49a.31 | 38, then any you missed | all thirty gotchas; a mock interview on questions 1 to 38 |

Run `python3 -B labs/python-brushup/test_exercises.py --mine` after each session: it prints one line per exercise, and the failures are your error log. Redo every failed exercise two days later without looking at your previous answer. For coding rounds, continue with chapter 39d; for production habits, with 49.1.

## Sources

- Python documentation, *The Python Language Reference*: data model (https://docs.python.org/3/reference/datamodel.html), execution model and name binding (https://docs.python.org/3/reference/executionmodel.html), expressions and operator precedence (https://docs.python.org/3/reference/expressions.html), compound statements including `match`, `try` and `with` (https://docs.python.org/3/reference/compound_stmts.html), and the import system (https://docs.python.org/3/reference/import.html).
- Python documentation, *The Python Standard Library*: built-in functions, including the 3.12 change to `sum()` and the 3.14 `strict` flag of `map()` (https://docs.python.org/3/library/functions.html); built-in types (https://docs.python.org/3/library/stdtypes.html); built-in exceptions (https://docs.python.org/3/library/exceptions.html); and the module pages for `collections`, `collections.abc`, `itertools`, `functools`, `operator`, `array`, `struct`, `heapq`, `bisect`, `queue`, `copy`, `dataclasses`, `enum`, `abc`, `typing`, `annotationlib`, `string.templatelib`, `contextlib`, `pathlib`, `json`, `csv`, `tempfile`, `tomllib`, `re`, `datetime`, `zoneinfo`, `logging`, `argparse`, `sqlite3`, `subprocess`, `unittest`, `doctest`, `gc`, `weakref`, `sys`, `tracemalloc`, `timeit`, `threading`, `concurrent.futures`, `concurrent.interpreters`, `multiprocessing`, `asyncio`, `decimal`, `fractions` and `math` (index: https://docs.python.org/3/library/index.html).
- Python HOWTOs: Descriptor Guide (https://docs.python.org/3/howto/descriptor.html); Sorting Techniques (https://docs.python.org/3/howto/sorting.html); Annotations Best Practices (https://docs.python.org/3/howto/annotations.html); Python support for free threading (https://docs.python.org/3/howto/free-threading-python.html); and Michele Simionato, "The Python 2.3 Method Resolution Order" (https://docs.python.org/3/howto/mro.html).
- Python tutorial, "Floating-Point Arithmetic: Issues and Limitations" (https://docs.python.org/3/tutorial/floatingpoint.html).
- What's New in Python 3.8 (https://docs.python.org/3/whatsnew/3.8.html), 3.9 (https://docs.python.org/3/whatsnew/3.9.html), 3.10 (https://docs.python.org/3/whatsnew/3.10.html), 3.11 (https://docs.python.org/3/whatsnew/3.11.html), 3.12 (https://docs.python.org/3/whatsnew/3.12.html), 3.13 (https://docs.python.org/3/whatsnew/3.13.html), 3.14, including the reversal of the incremental garbage collector in 3.14.5 (https://docs.python.org/3/whatsnew/3.14.html), and the 3.15 draft read at release candidate 3 (https://docs.python.org/3.15/whatsnew/3.15.html).
- Release schedules and status, checked on 3 October 2026: PEP 745, "Python 3.14 Release Schedule" (3.14.8 released 1 October 2026; https://peps.python.org/pep-0745/); PEP 790, "Python 3.15 Release Schedule" (release candidate 3 on 2 October 2026, final scheduled for 9 October 2026; https://peps.python.org/pep-0790/); Python Developer's Guide, "Status of Python versions" (3.10 end of life on 1 October 2026; 3.11 to 3.13 security fixes only; https://devguide.python.org/versions/).
- PEPs cited in the chapter (each at https://peps.python.org/pep-NNNN/): 257 (docstrings), 420 (namespace packages), 563 (postponed annotations), 570 (positional-only parameters), 572 (assignment expressions), 584 (dict union), 585 (built-in generics), 594 (removing dead batteries), 604 (`X | Y`), 634 to 636 (pattern matching), 649 and 749 (deferred annotations), 654 (exception groups), 661 (sentinels), 667 (`locals()` semantics), 669 (`sys.monitoring`), 678 (exception notes), 684 (per-interpreter GIL), 686 (UTF-8 default), 695 (type parameter syntax), 696 (type parameter defaults), 701 (f-string grammar), 703 (optional GIL), 709 (comprehension inlining), 728 (`TypedDict` extra items), 734 (subinterpreters in the standard library), 744 (JIT), 747 (`TypeForm`), 750 (template strings), 758 (`except` without parentheses), 765 (control flow in `finally`), 779 (supported free-threaded build), 798 (unpacking in comprehensions), 799 (profiling package), 810 (explicit lazy imports), 814 (`frozendict`); PEPs 745 and 790 are the release schedules above.
- Python wiki, "TimeComplexity" (https://wiki.python.org/moin/TimeComplexity).
- K. Barrett, B. Cassels, P. Haahr, D. A. Moon, K. Playford and P. T. Withington, "A Monotonic Superclass Linearization for Dylan", OOPSLA 1996 (the C3 algorithm in 49a.18.2).
- E. Gamma, R. Helm, R. Johnson and J. Vlissides, *Design Patterns: Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994 (the patterns in 49a.29); Brandon Rhodes, "Python Design Patterns" (https://python-patterns.guide/), for further reading on their Pythonic forms.
- labuladong, design-pattern series: Singleton (https://labuladong.online/en/algo/design-pattern/singleton/), Factory Method, Abstract Factory, Builder, Prototype, Adapter, Composite, Decorator, Bridge, Observer and Strategy (same path, with `factory-method`, `abstract-factory`, `builder`, `prototype`, `adapter`, `composite`, `decorator`, `bridge`, `observer` and `strategy`); on 3 October 2026 these addresses redirect to https://labuladong.online/en/fullstack/design-pattern/. The list and order of patterns in 49a.29 follow this series; the explanations and code are this book's own.
- IEEE 754-2019, *IEEE Standard for Floating-Point Arithmetic* (49a.3.2).
- Jake Edge, "A Python security fix breaks (some) bignums", LWN.net, 14 September 2022 (https://lwn.net/Articles/907572/), on CVE-2020-10735: the 4,300-digit limit, the security releases that introduced it, and its exemption for power-of-two bases.
- CPython pull request GH-22904 (bpo-41972), "Use the two-way algorithm for string searching", merged for 3.10 (https://github.com/python/cpython/pull/22904), for the substring-search note in 49a.7.6.
- Luciano Ramalho, *Fluent Python*, 2nd edition, O'Reilly, 2022 (further reading on the data model, iterators, decorators and descriptors).
- Code: every example in this chapter runs with `python3 tools/run_chapter_examples.py book/part-4-engineering-and-roles/49a-python-fundamentals-and-advanced-idioms.md`; the exercises are in `labs/python-brushup/` (`python3 -B labs/python-brushup/test_exercises.py`).
