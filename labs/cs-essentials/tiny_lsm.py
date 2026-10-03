"""A tiny LSM-tree key-value store for learning (chapter 49b.15).

    store = LSMStore("data", strategy="leveled")       # or strategy="tiered"
    store.put("user:42", "Ada")
    store.delete("user:7")
    store.get("user:42")                               # -> "Ada"
    store.scan("user:", "user;")                       # live pairs with "user:" <= key < "user;"
    store.close()

What it has: a write-ahead log with a CRC per record (a torn tail is dropped on recovery), a memtable,
immutable sorted SSTable files with a sparse index and a Bloom filter each, sequence numbers so the newest
version of a key always wins, tombstones for deletes, size-tiered or leveled compaction, range scans, a
MANIFEST replaced atomically so that a crash during a flush or a compaction leaves a consistent store, and
counters for write, read and space amplification. What it leaves out: concurrency, compression, block
caches, snapshots and per-block checksums. Keys and values are str. Production systems use RocksDB, LevelDB,
Pebble or the engine inside the database you already run.

Run `python3 tiny_lsm.py` for a workload that compares the two compaction strategies.
"""
import bisect
import hashlib
import heapq
import json
import math
import os
import zlib

_NO_KEY = object()


class BloomFilter:
    """A bit array and k hash positions per key: no false negatives, a tunable false-positive rate."""

    def __init__(self, num_bits: int, num_hashes: int, bits: bytes | None = None):
        self.num_bits = max(8, num_bits)
        self.num_hashes = max(1, num_hashes)
        self.bits = bytearray(bits) if bits is not None else bytearray((self.num_bits + 7) // 8)

    @classmethod
    def for_capacity(cls, n_items: int, fp_rate: float = 0.01) -> "BloomFilter":
        """Optimal size for n items: m = -n ln p / (ln 2)^2 bits and k = (m / n) ln 2 hash functions."""
        n = max(1, n_items)
        num_bits = math.ceil(-n * math.log(fp_rate) / math.log(2) ** 2)
        return cls(num_bits, round(num_bits / n * math.log(2)))

    def _positions(self, key: str) -> list:
        digest = hashlib.sha256(key.encode("utf-8", "surrogatepass")).digest()
        h1 = int.from_bytes(digest[:8], "little")
        h2 = int.from_bytes(digest[8:16], "little") | 1     # k positions from two hashes: h1 + i * h2
        return [(h1 + i * h2) % self.num_bits for i in range(self.num_hashes)]

    def add(self, key: str) -> None:
        for p in self._positions(key):
            self.bits[p >> 3] |= 1 << (p & 7)

    def might_contain(self, key: str) -> bool:
        return all(self.bits[p >> 3] & (1 << (p & 7)) for p in self._positions(key))


def encode_record(seq: int, key: str, value: str | None) -> bytes:
    """One WAL record per line: the CRC-32 of the body in hex, a space, then the JSON body [seq, key, value].
    JSON escapes control characters, so a body never contains a raw newline. value None is a tombstone."""
    body = json.dumps([seq, key, value], separators=(",", ":")).encode("ascii")
    return b"%08x %s\n" % (zlib.crc32(body), body)


def decode_records(data: bytes) -> tuple:
    """Parse a WAL image into (records, valid_length). Stops at the first torn or corrupt record: a crash
    can only damage the tail, and nothing after a damaged record can be trusted to be in order."""
    records, offset = [], 0
    while True:
        end = data.find(b"\n", offset)
        if end < 0:
            return records, offset              # no newline: the last write was torn, or the log is empty
        crc, _, body = data[offset:end].partition(b" ")
        try:
            if len(crc) != 8 or int(crc, 16) != zlib.crc32(body):
                return records, offset
            seq, key, value = json.loads(body)
        except (ValueError, TypeError):
            return records, offset
        records.append((seq, key, value))
        offset = end + 1


def merge_newest(runs, can_drop=None):
    """Merge runs of (key, seq, value) entries, each sorted by key with unique keys, into one sorted stream
    that keeps only the newest version of every key. A tombstone (value None) is kept unless
    can_drop(key, seq) says that no older version of the key can exist outside these runs."""
    previous = _NO_KEY
    for key, seq, value in heapq.merge(*runs, key=lambda entry: (entry[0], -entry[1])):
        if key == previous:
            continue                            # an older version of a key that is already decided
        previous = key
        if value is None and can_drop is not None and can_drop(key, seq):
            continue
        yield key, seq, value


def size_tiered_buckets(sizes: list, *, low: float = 0.5, high: float = 1.5, small: int = 4096) -> list:
    """Group table indexes into buckets of similar size, as Cassandra's size-tiered strategy does: a table
    joins a bucket when its size is within [low, high] times the bucket's average, and tables under
    `small` bytes all share one bucket."""
    buckets = []                                # [average size, [indexes]]
    for i in sorted(range(len(sizes)), key=sizes.__getitem__):
        for bucket in buckets:
            average, members = bucket
            if low * average <= sizes[i] <= high * average or (sizes[i] < small and average < small):
                members.append(i)
                bucket[0] = sum(sizes[j] for j in members) / len(members)
                break
        else:
            buckets.append([sizes[i], [i]])
    return [members for _, members in buckets]


def _overlaps(table, lo: str, hi: str) -> bool:
    return not (table.max_key < lo or table.min_key > hi)


class SSTable:
    """An immutable sorted file: one JSON line [key, seq, value] per entry, a footer line holding the sparse
    index (first key and byte offset of every block), the Bloom filter and the key and sequence ranges,
    and finally the footer's byte offset as 20 digits."""

    def __init__(self, path: str):
        self.path = path
        self.name = os.path.basename(path)
        with open(path, "rb") as f:
            f.seek(-21, os.SEEK_END)
            self.data_end = int(f.read(20))
            f.seek(self.data_end)
            footer = json.loads(f.readline())
        self.index = footer["index"]
        self.index_keys = [key for key, _ in self.index]
        self.bloom = BloomFilter(footer["bloom_bits"], footer["bloom_hashes"], bytes.fromhex(footer["bloom"]))
        self.count = footer["count"]
        self.min_key, self.max_key = footer["min_key"], footer["max_key"]
        self.min_seq, self.max_seq = footer["min_seq"], footer["max_seq"]
        self.size = os.path.getsize(path)

    @classmethod
    def write(cls, path: str, entries: list, *, index_every: int = 16, fp_rate: float = 0.01,
              sync: bool = False) -> "SSTable":
        """Write sorted, unique-key entries to path atomically: a temporary file, then a rename."""
        bloom = BloomFilter.for_capacity(len(entries), fp_rate)
        index, offset = [], 0
        with open(path + ".tmp", "wb") as f:
            for i, (key, seq, value) in enumerate(entries):
                if i % index_every == 0:
                    index.append([key, offset])
                line = json.dumps([key, seq, value], separators=(",", ":")).encode("ascii") + b"\n"
                f.write(line)
                offset += len(line)
                bloom.add(key)
            footer = {"index": index, "count": len(entries),
                      "min_key": entries[0][0], "max_key": entries[-1][0],
                      "min_seq": min(e[1] for e in entries), "max_seq": max(e[1] for e in entries),
                      "bloom": bloom.bits.hex(), "bloom_bits": bloom.num_bits, "bloom_hashes": bloom.num_hashes}
            f.write(json.dumps(footer, separators=(",", ":")).encode("ascii") + b"\n")
            f.write(b"%020d\n" % offset)
            f.flush()
            if sync:
                os.fsync(f.fileno())
        os.replace(path + ".tmp", path)         # the table appears complete under its name, or not at all
        return cls(path)

    def find(self, key: str):
        """Read the one block that could hold key. Returns (seq, value) or None; value None is a tombstone."""
        i = bisect.bisect_right(self.index_keys, key) - 1
        if i < 0:
            return None
        start = self.index[i][1]
        end = self.index[i + 1][1] if i + 1 < len(self.index) else self.data_end
        with open(self.path, "rb") as f:
            f.seek(start)
            block = f.read(end - start)
        for line in block.splitlines():
            k, seq, value = json.loads(line)
            if k == key:
                return seq, value
            if k > key:
                return None
        return None

    def scan(self, start: str | None = None, end: str | None = None) -> list:
        """Entries with start <= key < end in key order, tombstones included (None means unbounded)."""
        i = 0 if start is None else max(bisect.bisect_right(self.index_keys, start) - 1, 0)
        offset = self.index[i][1]
        out = []
        with open(self.path, "rb") as f:
            f.seek(offset)
            for line in f.read(self.data_end - offset).splitlines():
                key, seq, value = json.loads(line)
                if end is not None and key >= end:
                    break
                if start is None or key >= start:
                    out.append((key, seq, value))
        return out


class LSMStore:
    """WAL + memtable + SSTables + compaction. One process per directory; not thread-safe.

    strategy="leveled": flushes land in level 0 (tables may overlap); when level 0 has l0_trigger tables
    they are merged with the overlapping level-1 tables. Each level L >= 1 is one sorted run split into
    files of about target_file_bytes; when its size exceeds level_base_bytes * fanout ** (L - 1), one
    file (chosen round-robin) is merged into level L + 1. Low read and space amplification.

    strategy="tiered": tables of similar size are grouped into buckets; when a bucket holds tier_min
    tables, they are merged into one bigger table. Low write amplification, more space and read cost.

    sync=False flushes every write to the operating system (it survives a crash of this process);
    sync=True also fsyncs files and directories (it survives a power failure, much more slowly).
    """

    def __init__(self, directory: str, *, strategy: str = "leveled", memtable_bytes: int = 4096,
                 sync: bool = False, l0_trigger: int = 4, fanout: int = 10, max_levels: int = 7,
                 level_base_bytes: int | None = None, target_file_bytes: int | None = None,
                 tier_min: int = 4, tier_max: int = 32, index_every: int = 16, bloom_fp_rate: float = 0.01):
        if strategy not in ("leveled", "tiered"):
            raise ValueError("strategy must be 'leveled' or 'tiered'")
        os.makedirs(directory, exist_ok=True)
        self.dir = directory
        self.strategy = strategy
        self.memtable_bytes = memtable_bytes
        self.sync = sync
        self.l0_trigger = l0_trigger
        self.fanout = fanout
        self.max_levels = max_levels
        self.level_base_bytes = level_base_bytes or 4 * memtable_bytes
        self.target_file_bytes = target_file_bytes or memtable_bytes
        self.tier_min = tier_min
        self.tier_max = tier_max
        self.index_every = index_every
        self.bloom_fp_rate = bloom_fp_rate
        self.stats = dict.fromkeys(
            ("user_bytes", "wal_bytes", "flushes", "flush_bytes", "compactions", "trivial_moves",
             "compaction_read_bytes", "compaction_write_bytes", "gets", "tables_probed",
             "bloom_skips", "block_reads"), 0)
        self._recover()

    # ----- recovery -----

    def _path(self, name: str) -> str:
        return os.path.join(self.dir, name)

    def _recover(self) -> None:
        """Open the tables the MANIFEST lists, delete leftovers of an interrupted flush or compaction,
        then replay the WAL into the memtable and cut off a torn tail."""
        if os.path.exists(self._path("MANIFEST")):
            with open(self._path("MANIFEST")) as f:
                manifest = json.load(f)
            if manifest["strategy"] != self.strategy:
                raise ValueError(f"this store was created with strategy={manifest['strategy']!r}")
            self.next_file = manifest["next_file"]
            self.levels = [[SSTable(self._path(name)) for name in level] for level in manifest["levels"]]
            self.pointers = {int(level): key for level, key in manifest["pointers"].items()}
        else:
            self.next_file, self.levels, self.pointers = 1, [[]], {}
        live = {t.name for t in self.tables()}
        for name in os.listdir(self.dir):
            if name.endswith(".tmp") or (name.endswith(".sst") and name not in live):
                os.remove(self._path(name))
        self._seq = max((t.max_seq for t in self.tables()), default=0)
        self.memtable, self._mem_bytes = {}, 0
        data = b""
        if os.path.exists(self._path("wal.log")):
            with open(self._path("wal.log"), "rb") as f:
                data = f.read()
        records, valid_length = decode_records(data)
        for seq, key, value in records:
            self.memtable[key] = (seq, value)
            self._mem_bytes += len(encode_record(seq, key, value))
            self._seq = max(self._seq, seq)
        if valid_length < len(data):
            with open(self._path("wal.log"), "r+b") as f:
                f.truncate(valid_length)        # append after the last intact record, never after garbage
        self._wal = open(self._path("wal.log"), "ab")
        self._maybe_compact()                   # finish compaction work a crash left undone

    # ----- writes -----

    def put(self, key: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("values are str; use delete() to remove a key")
        self._write(key, value)

    def delete(self, key: str) -> None:
        self._write(key, None)                  # a tombstone: deletes are writes in an LSM tree

    def _write(self, key: str, value: str | None) -> None:
        if not isinstance(key, str):
            raise TypeError("keys are str")
        self._seq += 1
        record = encode_record(self._seq, key, value)
        self._wal.write(record)
        self._wal.flush()                       # now in the OS page cache: survives a process crash
        if self.sync:
            os.fsync(self._wal.fileno())        # now on the device: survives a power failure
        self.memtable[key] = (self._seq, value)
        self._mem_bytes += len(record)
        self.stats["user_bytes"] += len(key) + len(value or "")
        self.stats["wal_bytes"] += len(record)
        if self._mem_bytes >= self.memtable_bytes:
            self.flush()

    def flush(self) -> None:
        """Write the memtable as a new level-0 table, record it in the MANIFEST, then empty the WAL."""
        if not self.memtable:
            return
        entries = [(key, seq, value) for key, (seq, value) in sorted(self.memtable.items())]
        table = self._new_table(entries)
        self.levels[0].append(table)
        self._save_manifest()
        self._reset_wal()
        self.memtable, self._mem_bytes = {}, 0
        self.stats["flushes"] += 1
        self.stats["flush_bytes"] += table.size
        self._maybe_compact()

    # ----- reads -----

    def get(self, key: str, default=None):
        """Memtable first, then tables from newest to oldest; stop once no older table can hold a newer
        version than the one found. Key ranges and Bloom filters skip most tables without any I/O."""
        self.stats["gets"] += 1
        if key in self.memtable:
            value = self.memtable[key][1]
            return default if value is None else value
        best = None                             # (seq, value) of the newest version found so far
        for table in sorted(self.tables(), key=lambda t: t.max_seq, reverse=True):
            if best is not None and table.max_seq < best[0]:
                break
            if not table.min_key <= key <= table.max_key:
                continue
            self.stats["tables_probed"] += 1
            if not table.bloom.might_contain(key):
                self.stats["bloom_skips"] += 1
                continue
            self.stats["block_reads"] += 1
            found = table.find(key)
            if found is not None and (best is None or found[0] > best[0]):
                best = found
        if best is None or best[1] is None:
            return default
        return best[1]

    def scan(self, start: str | None = None, end: str | None = None) -> list:
        """Live (key, value) pairs with start <= key < end, in key order: a merge of every sorted source."""
        def in_range(key):
            return (start is None or key >= start) and (end is None or key < end)
        runs = [sorted((key, seq, value) for key, (seq, value) in self.memtable.items() if in_range(key))]
        runs += [table.scan(start, end) for table in self.tables()]
        return [(key, value) for key, _, value in merge_newest(runs) if value is not None]

    def tables(self) -> list:
        return [table for level in self.levels for table in level]

    # ----- compaction -----

    def _maybe_compact(self) -> None:
        while True:
            job = self._pick_leveled() if self.strategy == "leveled" else self._pick_tiered()
            if job is None:
                return
            self._compact(*job)

    def _ensure_level(self, level: int) -> None:
        while len(self.levels) <= level:
            self.levels.append([])

    def _pick_leveled(self):
        if len(self.levels[0]) >= self.l0_trigger:
            lo = min(t.min_key for t in self.levels[0])
            hi = max(t.max_key for t in self.levels[0])
            self._ensure_level(1)
            return self.levels[0] + [t for t in self.levels[1] if _overlaps(t, lo, hi)], 1, None
        for level in range(1, min(len(self.levels), self.max_levels - 1)):
            if sum(t.size for t in self.levels[level]) > self.level_base_bytes * self.fanout ** (level - 1):
                pointer = self.pointers.get(level)
                tables = self.levels[level]
                chosen = next((t for t in tables if pointer is None or t.min_key > pointer), tables[0])
                self._ensure_level(level + 1)
                below = [t for t in self.levels[level + 1] if _overlaps(t, chosen.min_key, chosen.max_key)]
                return [chosen] + below, level + 1, (level, chosen.max_key)
        return None

    def _pick_tiered(self):
        tables = self.levels[0]
        buckets = size_tiered_buckets([t.size for t in tables], small=self.memtable_bytes)
        ready = [b for b in buckets if len(b) >= self.tier_min]
        if not ready:
            return None
        bucket = min(ready, key=lambda b: sum(tables[i].size for i in b) / len(b))
        chosen = sorted(bucket, key=lambda i: tables[i].size)[:self.tier_max]
        return [tables[i] for i in chosen], 0, None

    def _compact(self, inputs: list, output_level: int, pointer) -> None:
        names = {t.name for t in inputs}
        if pointer is not None:
            self.pointers[pointer[0]] = pointer[1]
        if pointer is not None and len(inputs) == 1:                  # a level-to-level job with nothing
            self.levels[pointer[0]].remove(inputs[0])                 # overlapping below: a trivial move
            self.levels[output_level].append(inputs[0])               # relinks the file without rewriting
            self.levels[output_level].sort(key=lambda t: t.min_key)
            self._save_manifest()
            self.stats["trivial_moves"] += 1
            return
        outside = [t for t in self.tables() if t.name not in names]

        def can_drop(key, seq):                 # a tombstone may go once no older version can exist elsewhere
            return not any(t.min_seq < seq and t.min_key <= key <= t.max_key and t.bloom.might_contain(key)
                           for t in outside)

        merged = merge_newest([t.scan() for t in inputs], can_drop)
        outputs = self._write_run(merged, self.target_file_bytes if self.strategy == "leveled" else None)
        for level in self.levels:
            level[:] = [t for t in level if t.name not in names]
        self.levels[output_level].extend(outputs)
        if self.strategy == "leveled" and output_level >= 1:
            self.levels[output_level].sort(key=lambda t: t.min_key)
        self._save_manifest()                   # the switch to the new files happens here, atomically
        for t in inputs:
            os.remove(t.path)
        self.stats["compactions"] += 1
        self.stats["compaction_read_bytes"] += sum(t.size for t in inputs)
        self.stats["compaction_write_bytes"] += sum(t.size for t in outputs)

    def compact_all(self) -> None:
        """A major compaction: merge every table into one sorted run in the last level, dropping all
        tombstones and overwritten versions."""
        self.flush()
        if not self.tables():
            return
        last = max(1, len(self.levels) - 1) if self.strategy == "leveled" else 0
        self._ensure_level(last)
        self._compact(self.tables(), last, None)

    def _write_run(self, entries, split_bytes) -> list:
        """Write sorted unique-key entries as one table, or as several of about split_bytes each."""
        outputs, chunk, chunk_bytes = [], [], 0
        for entry in entries:
            chunk.append(entry)
            chunk_bytes += len(entry[0]) + len(entry[2] or "") + 16
            if split_bytes is not None and chunk_bytes >= split_bytes:
                outputs.append(self._new_table(chunk))
                chunk, chunk_bytes = [], 0
        if chunk:
            outputs.append(self._new_table(chunk))
        return outputs

    # ----- files -----

    def _new_table(self, entries: list) -> SSTable:
        name = f"{self.next_file:06d}.sst"
        self.next_file += 1
        return SSTable.write(self._path(name), entries, index_every=self.index_every,
                             fp_rate=self.bloom_fp_rate, sync=self.sync)

    def _save_manifest(self) -> None:
        manifest = {"strategy": self.strategy, "next_file": self.next_file,
                    "levels": [[t.name for t in level] for level in self.levels],
                    "pointers": {str(level): key for level, key in self.pointers.items()}}
        with open(self._path("MANIFEST.tmp"), "w") as f:
            json.dump(manifest, f)
            f.flush()
            if self.sync:
                os.fsync(f.fileno())
        os.replace(self._path("MANIFEST.tmp"), self._path("MANIFEST"))
        self._sync_directory()

    def _reset_wal(self) -> None:
        self._wal.close()
        with open(self._path("wal.log"), "wb") as f:     # those records now live in an SSTable
            if self.sync:
                os.fsync(f.fileno())
        self._wal = open(self._path("wal.log"), "ab")

    def _sync_directory(self) -> None:
        if not self.sync:
            return
        try:                                    # make the renames durable (Linux and macOS; not Windows)
            fd = os.open(self.dir, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError:
            pass

    def close(self) -> None:
        """Close the WAL. The memtable needs no flush: the next open replays it from the WAL."""
        self._wal.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ----- measurements -----

    def report(self) -> dict:
        """Amplification figures for the work done so far (chapter 49b.15.4 defines them). write_amp counts
        table bytes written by flushes and compactions per byte flushed (the WAL is left out); space_amp is
        table data stored per byte of live entries."""
        s = self.stats
        live = list(merge_newest([t.scan() for t in self.tables()], can_drop=lambda key, seq: True))
        needed = sum(len(json.dumps([k, q, v], separators=(",", ":"))) + 1 for k, q, v in live)
        stored = sum(t.data_end for t in self.tables())
        return {
            "tables": len(self.tables()),
            "levels": [len(level) for level in self.levels],
            "write_amp": round((s["flush_bytes"] + s["compaction_write_bytes"]) / max(1, s["flush_bytes"]), 2),
            "space_amp": round(stored / needed, 2) if needed else None,
            "probes_per_get": round(s["tables_probed"] / max(1, s["gets"]), 2),
            "block_reads_per_get": round(s["block_reads"] / max(1, s["gets"]), 2),
        }


def _demo(operations: int = 30000, keys: int = 3000, seed: int = 7) -> None:
    import random
    import tempfile
    print(f"{operations} operations over {keys} keys: 85% puts, 15% deletes, then 5000 gets")
    print(f"{'strategy':10} {'tables':>6} {'per level':>14} {'write amp':>9} {'space amp':>9} "
          f"{'probes/get':>10} {'reads/get':>9}")
    for strategy in ("leveled", "tiered"):
        rng = random.Random(seed)
        with tempfile.TemporaryDirectory() as directory:
            store = LSMStore(directory, strategy=strategy, memtable_bytes=8192)
            for _ in range(operations):
                key = f"key{rng.randrange(keys):05d}"
                if rng.random() < 0.85:
                    store.put(key, f"value-{rng.randrange(10 ** 6)}")
                else:
                    store.delete(key)
            store.flush()
            for _ in range(5000):
                store.get(f"key{rng.randrange(keys * 2):05d}")    # half of the keys were never written
            r = store.report()
            print(f"{strategy:10} {r['tables']:>6} {str(r['levels']):>14} {r['write_amp']:>9} "
                  f"{r['space_amp']:>9} {r['probes_per_get']:>10} {r['block_reads_per_get']:>9}")
            store.close()


if __name__ == "__main__":
    _demo()
