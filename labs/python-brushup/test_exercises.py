#!/usr/bin/env python3
"""Tests for the Python brush-up lab (chapter 49a). Plain asserts, standard library only, Python 3.11+.

Usage:
    python3 -B test_exercises.py               # check the reference solutions (solutions.py)
    python3 -B test_exercises.py --mine        # check your answers (exercises.py)
    python3 -B test_exercises.py --mine 4 12   # only exercises 4 and 12

Prints one line per exercise: PASS, FAIL (with the failing line), or TODO (still raises
NotImplementedError). The exit code is 1 unless every selected exercise passes.
"""
import argparse
import asyncio
import importlib
import inspect
import math
import os
import sys
import traceback
from decimal import Decimal
from itertools import count, islice

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TESTS = []


def exercise(number, name):
    def register(test):
        TESTS.append((number, name, test))
        return test
    return register


def raises(exc_type, func, *args, **kwargs):
    """Return the exception func raised, failing if it raised nothing or something else."""
    try:
        func(*args, **kwargs)
    except NotImplementedError:
        raise
    except exc_type as err:
        return err
    raise AssertionError(f"expected {exc_type.__name__}")


@exercise(1, "split_head_tail")
def _(m):
    assert m.split_head_tail([1, 2, 3, 4]) == (1, [2, 3], 4)
    assert m.split_head_tail("ab") == ("a", [], "b")
    assert m.split_head_tail(range(3)) == (0, [1], 2)
    raises(ValueError, m.split_head_tail, [1])


@exercise(2, "trunc_divmod")
def _(m):
    assert m.trunc_divmod(7, 2) == (3, 1)
    assert m.trunc_divmod(-7, 2) == (-3, -1)
    assert m.trunc_divmod(7, -2) == (-3, 1)
    assert m.trunc_divmod(-7, -2) == (3, -1)
    for a in range(-20, 21):
        for b in [-7, -3, -1, 1, 2, 5]:
            q, r = m.trunc_divmod(a, b)
            assert a == q * b + r and abs(r) < abs(b) and (r == 0 or (r < 0) == (a < 0)), (a, b)
    assert m.trunc_divmod(10**30 + 1, -1) == (-(10**30 + 1), 0)
    raises(ZeroDivisionError, m.trunc_divmod, 1, 0)


@exercise(3, "sum_money")
def _(m):
    assert m.sum_money(["0.10", "0.20"]) == Decimal("0.30")
    assert m.sum_money(["1.005"]) == Decimal("1.01")              # half up, not half even
    assert m.sum_money(["2.665"]) == Decimal("2.67")
    assert m.sum_money([]) == Decimal("0.00") and str(m.sum_money([])) == "0.00"
    assert m.sum_money(["19.99"] * 3) == Decimal("59.97")
    assert m.sum_money(iter(["-1.50", "1.25"])) == Decimal("-0.25")


@exercise(4, "parse_command")
def _(m):
    assert m.parse_command("go north") == ("move", "north")
    assert m.parse_command("go up") == ("error", "go where?")
    assert m.parse_command("go") == ("error", "go where?")
    assert m.parse_command("take lamp") == ("take", ["lamp"])
    assert m.parse_command("take lamp key") == ("take", ["lamp", "key"])
    assert m.parse_command("quit") == ("quit",) and m.parse_command("exit") == ("quit",)
    assert m.parse_command("look") == ("look",) and m.parse_command("   ") == ("look",)
    assert m.parse_command("dance wildly") == ("unknown", "dance wildly")


@exercise(5, "smallest_prime_factor")
def _(m):
    assert [m.smallest_prime_factor(n) for n in (2, 3, 4, 9, 15, 91, 97)] == [2, 3, 2, 3, 3, 7, 97]
    assert m.smallest_prime_factor(2**31 - 1) == 2**31 - 1             # a prime
    assert m.smallest_prime_factor(1_000_003 * 1_000_033) == 1_000_003
    raises(ValueError, m.smallest_prime_factor, 1)


@exercise(6, "running_diffs")
def _(m):
    assert m.running_diffs([20, 22, 21, 25]) == [2, -1, 4]
    assert m.running_diffs([5]) == [] and m.running_diffs([]) == []
    assert m.running_diffs(iter([1, 4, 9])) == [3, 5]


@exercise(7, "transpose")
def _(m):
    assert m.transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
    assert m.transpose([[1]]) == [[1]] and m.transpose([]) == []
    raises(ValueError, m.transpose, [[1, 2], [3]])


@exercise(8, "normalize_whitespace")
def _(m):
    assert m.normalize_whitespace("  many   spaces\there\n") == "many spaces here"
    assert m.normalize_whitespace("") == "" and m.normalize_whitespace(" \t\n ") == ""


@exercise(9, "is_palindrome")
def _(m):
    assert m.is_palindrome("A man, a plan, a canal: Panama")
    assert m.is_palindrome("") and m.is_palindrome("No 'x' in Nixon")
    assert not m.is_palindrome("palindrome")
    assert m.is_palindrome("Straße essartS")                          # casefold, not lower


@exercise(10, "format_invoice_line")
def _(m):
    assert m.format_invoice_line("Widget", 3, 1250.5) == "Widget".ljust(12) + "3".rjust(5) + "3,751.50".rjust(12)
    assert m.format_invoice_line("A very long product name", 1, 2) == "A very long " + "1".rjust(5) + "2.00".rjust(12)
    assert m.format_invoice_line("Gadget", 12, 0.5) == "Gadget         12        6.00"


@exercise(11, "rotate")
def _(m):
    items = [1, 2, 3, 4, 5]
    assert m.rotate(items, 2) == [4, 5, 1, 2, 3]
    assert m.rotate(items, -1) == [2, 3, 4, 5, 1]
    assert m.rotate(items, 7) == [4, 5, 1, 2, 3] and m.rotate(items, 0) == items
    assert m.rotate([], 3) == [] and items == [1, 2, 3, 4, 5]          # input unchanged
    assert m.rotate(items, 5) is not items


@exercise(12, "make_grid")
def _(m):
    grid = m.make_grid(3, 2, fill=".")
    assert grid == [[".", "."], [".", "."], [".", "."]]
    grid[0][0] = "#"
    assert grid == [["#", "."], [".", "."], [".", "."]]               # rows are independent
    assert m.make_grid(0, 5) == [] and m.make_grid(2, 0) == [[], []]


@exercise(13, "sort_employees")
def _(m):
    staff = [
        {"name": "di", "team": "ops", "salary": 95},
        {"name": "ana", "team": "eng", "salary": 120},
        {"name": "bo", "team": "ops", "salary": 95},
        {"name": "cy", "team": "eng", "salary": 135},
    ]
    original = [dict(r) for r in staff]
    assert [r["name"] for r in m.sort_employees(staff)] == ["cy", "ana", "bo", "di"]
    assert staff == original                                           # a new list


@exercise(14, "run_length_encode")
def _(m):
    def decode(encoded):
        return b"".join(bytes([value]) * run for run, value in zip(encoded[::2], encoded[1::2]))
    assert m.run_length_encode(b"aaab") == bytes([3, 97, 1, 98])
    assert m.run_length_encode(b"") == b""
    long_run = b"z" * 600
    encoded = m.run_length_encode(long_run)
    assert encoded == bytes([255, 122, 255, 122, 90, 122]) and decode(encoded) == long_run
    sample = bytes([0, 0, 255, 255, 255, 1])
    assert decode(m.run_length_encode(sample)) == sample and isinstance(m.run_length_encode(sample), bytes)


@exercise(15, "Point")
def _(m):
    p = m.Point(3, 4)
    assert p == (3, 4) and p.x == 3 and isinstance(p, tuple)
    assert p.distance_to(m.Point(0, 0)) == 5.0
    assert p.scaled(2) == m.Point(6, 8) and isinstance(p.scaled(2), m.Point)
    raises(AttributeError, setattr, p, "x", 1)


@exercise(16, "group_by")
def _(m):
    words = ["apple", "bob", "avocado", "cat", "banana"]
    assert m.group_by(words, key=lambda w: w[0]) == {"a": ["apple", "avocado"], "b": ["bob", "banana"], "c": ["cat"]}
    assert list(m.group_by(words, key=len)) == [5, 3, 7, 6]            # first-seen key order
    assert m.group_by([], key=len) == {} and type(m.group_by([1], key=str)) is dict


@exercise(17, "invert_mapping")
def _(m):
    assert m.invert_mapping({"ana": "eng", "bo": "ops", "cy": "eng"}) == {"eng": ["ana", "cy"], "ops": ["bo"]}
    assert m.invert_mapping({}) == {}


@exercise(18, "top_k_words")
def _(m):
    text = "The cat and the hat. The cat sat! A hat, a cat; the end."
    assert m.top_k_words(text, 3) == [("the", 4), ("cat", 3), ("a", 2)]
    assert m.top_k_words("b a c a b", 2) == [("a", 2), ("b", 2)]       # ties alphabetical
    assert m.top_k_words("", 5) == [] and m.top_k_words("Don't stop", 1) == [("don't", 1)]


@exercise(19, "deep_merge")
def _(m):
    base = {"db": {"host": "localhost", "port": 5432}, "debug": False, "tags": ["a"]}
    override = {"db": {"port": 6543, "user": "app"}, "debug": True}
    merged = m.deep_merge(base, override)
    assert merged == {"db": {"host": "localhost", "port": 6543, "user": "app"}, "debug": True, "tags": ["a"]}
    assert base["db"] == {"host": "localhost", "port": 5432}           # inputs untouched
    merged["tags"].append("b")
    assert base["tags"] == ["a"]                                       # no shared nested objects
    assert m.deep_merge({"a": {"b": 1}}, {"a": 2}) == {"a": 2}
    assert m.deep_merge({"a": 1}, {"a": {"b": 2}}) == {"a": {"b": 2}}


@exercise(20, "dedupe")
def _(m):
    assert m.dedupe(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
    rows = [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}, {"id": 1, "v": "z"}]
    assert m.dedupe(rows, key=lambda r: r["id"]) == rows[:2]
    assert m.dedupe([]) == [] and m.dedupe(iter([1, 1, 2])) == [1, 2]


@exercise(21, "compose")
def _(m):
    slugify = m.compose("-".join, str.split, str.lower)
    assert slugify("Python Brush Up") == "python-brush-up"
    assert m.compose()(42) == 42
    assert m.compose(lambda x: x + 1, lambda x: x * 10)(2) == 21       # right to left


@exercise(22, "make_counter")
def _(m):
    c = m.make_counter()
    assert [c(), c(), c()] == [0, 1, 2]
    d = m.make_counter(start=10, step=-5)
    assert [d(), d()] == [10, 5] and c() == 3                          # independent state


@exercise(23, "call_with_supported_kwargs")
def _(m):
    def f(a, b=2, *, c=3):
        return a, b, c

    def g(**options):
        return options

    assert m.call_with_supported_kwargs(f, a=1, c=4, unknown=9) == (1, 2, 4)
    assert m.call_with_supported_kwargs(g, x=1, y=2) == {"x": 1, "y": 2}
    assert m.call_with_supported_kwargs(lambda: "none") == "none"


@exercise(24, "Vector")
def _(m):
    V = m.Vector
    v = V(3, 4)
    assert repr(v) == "Vector(3, 4)" and v == V(3, 4) and v != V(4, 3)
    assert v + V(1, 1) == V(4, 5) and v - V(1, 1) == V(2, 3)
    assert v * 2 == V(6, 8) and 2 * v == V(6, 8) and -v == V(-3, -4)
    assert abs(v) == 5.0 and not V(0, 0) and V(0, 1)
    assert v.dot(V(2, 1)) == 10 and tuple(v) == (3, 4)
    x, y = v
    assert (x, y) == (3, 4)
    assert len({V(1, 2), V(1, 2)}) == 1
    assert (v == (3, 4)) is False
    raises(TypeError, lambda: v + 1)
    raises(TypeError, lambda: v * "a")


@exercise(25, "Temperature")
def _(m):
    t = m.Temperature(25)
    assert t.celsius == 25 and t.fahrenheit == 77.0
    t.fahrenheit = 212
    assert math.isclose(t.celsius, 100.0)
    raises(ValueError, m.Temperature, -300)
    raises(ValueError, setattr, t, "celsius", -274)
    raises(ValueError, setattr, t, "fahrenheit", -500)
    assert math.isclose(t.celsius, 100.0)                              # failed sets change nothing
    assert repr(m.Temperature(0)) == "Temperature(celsius=0)"
    assert isinstance(inspect.getattr_static(m.Temperature, "fahrenheit"), property)


@exercise(26, "Stack")
def _(m):
    s = m.Stack()
    assert not s and len(s) == 0
    raises(IndexError, s.pop)
    raises(IndexError, s.peek)
    for item in ("a", "b", "c"):
        s.push(item)
    assert s and len(s) == 3 and s.peek() == "c" and "b" in s and "z" not in s
    assert list(s) == ["c", "b", "a"]                                   # top to bottom
    assert repr(s) == "Stack(['a', 'b', 'c'])"
    assert s.pop() == "c" and len(s) == 2
    assert list(m.Stack([1, 2])) == [2, 1]


@exercise(27, "Shape hierarchy")
def _(m):
    raises(TypeError, m.Shape)                                          # abstract
    r, s, c = m.Rectangle(2, 3), m.Square(2), m.Circle(1)
    assert (r.area(), r.perimeter()) == (6, 10)
    assert (s.area(), s.perimeter()) == (4, 8) and isinstance(s, m.Rectangle)
    assert math.isclose(c.area(), math.pi) and math.isclose(c.perimeter(), 2 * math.pi)
    assert s.describe() == "Square area=4.00" and c.describe() == "Circle area=3.14"
    assert math.isclose(m.total_area([r, s, c]), 10 + math.pi) and m.total_area([]) == 0


@exercise(28, "FrozenMapping")
def _(m):
    from collections.abc import Mapping
    fm = m.FrozenMapping({"a": 1}, b=2)
    assert fm["a"] == 1 and len(fm) == 2 and sorted(fm) == ["a", "b"]
    assert fm == {"a": 1, "b": 2} and isinstance(fm, Mapping)
    assert fm.get("missing", 0) == 0 and "b" in fm and dict(fm.items()) == {"a": 1, "b": 2}
    assert hash(fm) == hash(m.FrozenMapping(b=2, a=1))
    assert len({fm, m.FrozenMapping(a=1, b=2)}) == 1
    try:
        fm["c"] = 3
    except TypeError:
        pass
    else:
        raise AssertionError("FrozenMapping accepted item assignment")
    source = {"x": 1}
    copy_of = m.FrozenMapping(source)
    source["x"] = 99
    assert copy_of["x"] == 1                                            # copied, not aliased
    assert repr(m.FrozenMapping(a=1)) == "FrozenMapping({'a': 1})"


@exercise(29, "flatten")
def _(m):
    assert list(m.flatten([1, [2, [3, (4,)]], 5])) == [1, 2, 3, 4, 5]
    assert list(m.flatten(["ab", ["cd"]])) == ["ab", "cd"]              # strings are leaves
    assert list(m.flatten([])) == [] and list(m.flatten([[[]]])) == []
    assert inspect.isgenerator(m.flatten([1]))


@exercise(30, "fibonacci and take")
def _(m):
    assert m.take(10, m.fibonacci()) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    fib = m.fibonacci()
    m.take(5, fib)
    assert next(fib) == 5                                               # the generator keeps its place
    assert m.take(3, "abcdef") == ["a", "b", "c"] and m.take(0, count()) == []
    assert m.take(100, m.fibonacci())[-1] == 218922995834555169026


@exercise(31, "chunked")
def _(m):
    assert list(m.chunked(range(7), 3)) == [(0, 1, 2), (3, 4, 5), (6,)]
    assert list(m.chunked([], 2)) == []
    assert list(islice(m.chunked(count(), 2), 2)) == [(0, 1), (2, 3)]   # lazy on infinite input
    raises(ValueError, lambda: list(m.chunked([1], 0)))


@exercise(32, "retry")
def _(m):
    delays = []
    outcomes = iter([ConnectionError("reset"), TimeoutError("slow"), "ok"])

    @m.retry(attempts=3, exceptions=(ConnectionError, TimeoutError), delay=0.5, backoff=2, sleep=delays.append)
    def flaky():
        """Call a flaky service."""
        result = next(outcomes)
        if isinstance(result, Exception):
            raise result
        return result

    assert flaky() == "ok" and delays == [0.5, 1.0]
    assert flaky.__name__ == "flaky" and flaky.__doc__ == "Call a flaky service."

    calls = []

    @m.retry(attempts=2, exceptions=(ConnectionError,), sleep=lambda s: None)
    def always_down():
        calls.append(1)
        raise ConnectionError("down")

    raises(ConnectionError, always_down)
    assert len(calls) == 2

    calls.clear()

    @m.retry(attempts=5, exceptions=(ConnectionError,), sleep=lambda s: None)
    def bad_request():
        calls.append(1)
        raise ValueError("400")

    raises(ValueError, bad_request)
    assert len(calls) == 1                                              # not retried


@exercise(33, "count_calls")
def _(m):
    @m.count_calls
    def add(a, b=0):
        """Add two numbers."""
        return a + b

    assert add.calls == 0
    assert add(1, b=2) == 3 and add(5) == 5 and add.calls == 2
    assert add.__name__ == "add" and add.__doc__ == "Add two numbers." and add.__wrapped__(1, 1) == 2


@exercise(34, "temporary_attr")
def _(m):
    class Settings:
        debug = False

    with m.temporary_attr(Settings, "debug", True) as target:
        assert Settings.debug is True and target is Settings
    assert Settings.debug is False
    try:
        with m.temporary_attr(Settings, "debug", True):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert Settings.debug is False                                     # restored after an error
    with m.temporary_attr(Settings, "brand_new", 1):
        assert Settings.brand_new == 1
    assert not hasattr(Settings, "brand_new")                           # removed if it did not exist


@exercise(35, "parse_log_line")
def _(m):
    line = "2026-10-03T10:00:02Z ERROR billing-api: card declined (code 51)"
    assert m.parse_log_line(line) == {
        "timestamp": "2026-10-03T10:00:02Z", "level": "ERROR",
        "service": "billing-api", "message": "card declined (code 51)"}
    assert m.parse_log_line(line + "\n")["level"] == "ERROR"
    assert m.parse_log_line("2026-10-03T10:00:02Z TRACE x: y") is None
    assert m.parse_log_line("not a log line") is None
    assert m.parse_log_line("2026-10-03T10:00:02Z INFO worker.7: ")["message"] == ""


@exercise(36, "validate_user")
def _(m):
    assert m.validate_user({"name": "  Ana ", "age": 31}) == {"name": "Ana", "age": 31}
    try:
        m.validate_user({"age": "ten"})
    except* ValueError as group:
        assert [str(e) for e in group.exceptions] == ["name is required"]
    except* TypeError as group:
        assert [str(e) for e in group.exceptions] == ["age must be an int"]
    else:
        raise AssertionError("expected an ExceptionGroup")
    err = raises(ExceptionGroup, m.validate_user, {"name": "Bo", "age": 200})
    assert [str(e) for e in err.exceptions] == ["age must be between 0 and 150"]
    err = raises(ExceptionGroup, m.validate_user, {"name": " ", "age": True})
    assert [type(e) for e in err.exceptions] == [ValueError, TypeError]   # bool is not an age


@exercise(37, "run_with_limit")
def _(m):
    state = {"running": 0, "peak": 0}

    def make(i, delay):
        async def job():
            state["running"] += 1
            state["peak"] = max(state["peak"], state["running"])
            await asyncio.sleep(delay)
            state["running"] -= 1
            return i * i
        return job

    factories = [make(i, 0.01 * (5 - i % 5)) for i in range(10)]
    assert asyncio.run(m.run_with_limit(factories, 3)) == [i * i for i in range(10)]
    assert state["peak"] == 3
    assert asyncio.run(m.run_with_limit([], 2)) == []


@exercise(38, "EventBus")
def _(m):
    bus = m.EventBus()
    received = []
    unsubscribe = bus.subscribe("paid", lambda order_id: received.append(("email", order_id)))
    bus.subscribe("paid", lambda order_id: received.append(("ledger", order_id)))
    assert bus.publish("paid", 7) == 2
    unsubscribe()
    unsubscribe()                                                        # a second call is harmless
    assert bus.publish("paid", order_id=8) == 1
    assert received == [("email", 7), ("ledger", 7), ("ledger", 8)]
    assert bus.publish("nobody-listens") == 0

    once_calls = []

    def once(**payload):
        once_calls.append(payload)
        remove_once()                                                    # unsubscribe during publish

    remove_once = bus.subscribe("tick", once)
    bus.subscribe("tick", lambda **payload: once_calls.append("second"))
    bus.publish("tick", n=1)
    bus.publish("tick", n=2)
    assert once_calls == [{"n": 1}, "second", "second"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Python brush-up exercises.")
    parser.add_argument("--mine", action="store_true", help="test exercises.py instead of solutions.py")
    parser.add_argument("numbers", nargs="*", type=int, help="exercise numbers to run (default: all)")
    args = parser.parse_args(argv)

    module = importlib.import_module("exercises" if args.mine else "solutions")
    selected = [t for t in TESTS if not args.numbers or t[0] in args.numbers]
    passed = failed = todo = 0
    for number, name, test in selected:
        label = f"{number:02d} {name}"
        try:
            test(module)
        except NotImplementedError:
            todo += 1
            print(f"TODO  {label}")
        except Exception as err:                                         # AssertionError or a bug
            failed += 1
            frame = traceback.extract_tb(err.__traceback__)[-1]
            detail = f"{type(err).__name__}: {err}" if str(err) else type(err).__name__
            print(f"FAIL  {label}  ({detail}; line {frame.lineno}: {frame.line})")
        else:
            passed += 1
            print(f"PASS  {label}")
    print(f"{passed} passed, {failed} failed, {todo} to do ({module.__name__}.py)")
    return 0 if passed == len(selected) else 1


if __name__ == "__main__":
    sys.exit(main())
