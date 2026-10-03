#!/usr/bin/env python3
"""Check that every function and class printed in chapters 39e, 39f and 39g is identical to the tested code here.

Chapter 39e prints code from ds_basics.py, 39f from frameworks_1.py and 39g from frameworks_2.py. Module-level
lines shown before the first def/class of a code block (imports, constants) must also appear verbatim in the
module. A code block whose first line is "# illustration" is skipped (pseudocode-like sketches).

Usage:  python3 check_chapter_sync.py [39e 39f 39g]      (exit code 1 on any difference)
"""
import glob
import importlib
import inspect
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, "..", "..", "book", "part-3-interviews")
MODULES = {"39e": "ds_basics", "39f": "frameworks_1", "39g": "frameworks_2"}
sys.path.insert(0, HERE)


def top_level_objects(code):
    """Split a code block into top-level def/class chunks (with their decorators) and module-level lines."""
    chunks, prelude, pending = {}, [], []
    name, lines = None, []

    def close():
        if name:
            chunks[name] = "\n".join(lines).rstrip()

    for line in code.split("\n"):
        header = re.match(r"(def|class) (\w+)", line)
        if line.startswith("@"):
            pending.append(line)                    # decorators belong to the next def/class
        elif header:
            close()
            name, lines, pending = header.group(2), pending + [line], []
        elif line and not line[0].isspace() and not line.startswith(("#", ")", "]", "}")):
            close()                                 # a module-level statement after a function
            name, lines = None, []
            prelude.append(line)
        elif name:
            lines.append(line)
        elif line.strip():
            prelude.append(line)
    close()
    return chunks, prelude


def check(chapter_id):
    found = glob.glob(os.path.join(BOOK, f"{chapter_id}-*.md"))
    if not found:
        print(f"{chapter_id}: chapter not written yet")
        return 0, 0
    module = importlib.import_module(MODULES[chapter_id])
    module_lines = set(inspect.getsource(module).split("\n"))
    text = open(found[0], encoding="utf8").read()
    shown = problems = 0
    for block in re.findall(r"```python\n(.*?)```", text, flags=re.S):
        if block.startswith("# illustration"):
            continue
        chunks, prelude = top_level_objects(block)
        for line in prelude:
            shown += 1
            if line not in module_lines:
                print(f"{chapter_id}: module-level line not in {MODULES[chapter_id]}.py: {line}")
                problems += 1
        for name, source in chunks.items():
            shown += 1
            obj = getattr(module, name, None)
            if obj is None:
                print(f"{chapter_id}: missing in {MODULES[chapter_id]}.py: {name}")
                problems += 1
            elif inspect.getsource(obj).rstrip() != source:
                print(f"{chapter_id}: differs from {MODULES[chapter_id]}.py: {name}")
                problems += 1
    print(f"{chapter_id}: {shown} objects and lines checked, {problems} problem(s)")
    return shown, problems


def main(ids):
    total = sum(check(i)[1] for i in ids)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main(sys.argv[1:] or list(MODULES))
