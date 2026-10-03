# Python brush-up lab

Thirty-eight exercises that drill chapter 49a, *Python fundamentals and advanced idioms*: unpacking, integer and decimal arithmetic, pattern matching, strings, lists, bytes, tuples, dicts, sets, comprehensions, closures, classes and operators, properties, the container protocol, abstract base classes, `collections.abc`, generators, decorators, context managers, regular expressions, exception groups, `asyncio` and the observer pattern. Each exercise is a function or class stub with a docstring that states the behavior and gives examples; the tests check those examples plus the edge cases an interviewer would ask about.

Standard library only, Python 3.11 or newer.

```bash
cd labs/python-brushup
python3 -B test_exercises.py               # the reference solutions: all 38 pass
python3 -B test_exercises.py --mine        # your answers in exercises.py
python3 -B test_exercises.py --mine 7 12   # only exercises 7 and 12
```

The `-B` flag keeps Python from writing `__pycache__` folders. The script prints one line per exercise, `PASS`, `FAIL` (with the assertion that failed and its line) or `TODO` (the stub still raises `NotImplementedError`), then a summary; the exit code is 1 unless every selected exercise passes.

## Files

| File | What it holds |
|---|---|
| `exercises.py` | 38 stubs to fill in; the comment above each names the chapter section that covers it |
| `solutions.py` | reference solutions, written the way the chapter recommends |
| `test_exercises.py` | plain-assert tests; runs against `solutions.py` by default and against `exercises.py` with `--mine` |

## How to practice with it

1. Read the chapter section named in the exercise's comment, then close it.
2. Write the function or class in `exercises.py` from the docstring alone. Time-box it: about 10 minutes for a function, 20 for a class.
3. Run `python3 -B test_exercises.py --mine <number>`. A `FAIL` line shows the exact assertion; most failures are an edge case (empty input, negative numbers, a shared mutable object, an exception type).
4. When it passes, compare with `solutions.py`. Look for what the reference does differently: a built-in you did not use, a copy you forgot, a clearer name.
5. Keep an error log of what failed and why, and redo those exercises two days later without looking at your previous answer.
6. For interview practice, write the answer in a plain editor without running it, explain it out loud as you go, and only then run the tests.

To start an exercise over, copy its stub back from version control (`git checkout -- exercises.py` resets the whole file).

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

For algorithm and data-structure practice in the style of coding rounds, continue with `labs/coding-patterns/` (chapter 39d).
