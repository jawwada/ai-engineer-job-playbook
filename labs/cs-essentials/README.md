# Computer-science essentials lab

Small, tested implementations of four mechanisms that chapter 49b (*Computer-science essentials: encryption, sessions, JWT, OAuth 2.0 and OIDC, TLS and certificates, Linux processes and pipes, and LSM trees*) explains in prose: signing and verifying JSON Web Tokens, PKCE for the OAuth 2.0 authorization code flow, a log-structured merge-tree key-value store, and TLS with mutual authentication over localhost.

## Purpose

Each module exists so that a mechanism you will be asked about in an interview, or will have to debug in production, is something you have run, broken and watched recover. The JWT verifier makes every check a production verifier makes, and the tests run the real attacks against it. The PKCE module includes a toy authorization server so the attack PKCE was designed to stop can be executed as a test. The LSM store is compared with a Python dict through thousands of random operations, restarts and simulated crashes. The mTLS demo creates a private certificate authority and shows what each side sees in four situations.

Every function and class that chapter 49b prints is copied from these files, and `check_chapter_sync.py` fails if the two drift. The modules are teaching code: production systems use vetted libraries (PyJWT or Authlib for tokens, your identity provider's SDK for OAuth, `cryptography` for primitives, RocksDB or the engine inside your database for storage, SPIRE or a service mesh for workload certificates), and each section below says what the library adds that the toy leaves out.

## Requirements

- Python 3.10 or newer; the standard library only (`hmac`, `hashlib`, `secrets`, `json`, `ssl`, `zlib`, `heapq`, `bisect`).
- `mtls_demo.py` also needs the `openssl` command-line tool on `PATH` to mint its throwaway certificates. Without it the demo prints `skipped` and exits 0, and the mTLS test passes vacuously.
- No packages to install, no network access, no files written outside temporary directories.

Tested here with Python 3.14.7 (linked against OpenSSL 3.6.4) and the OpenSSL 4.0.3 command-line tool.

## Quick start

```bash
cd labs/cs-essentials
python3 -B test_cs_essentials.py        # all 25 tests, about four seconds
python3 -B test_cs_essentials.py lsm    # only tests whose name contains "lsm"
python3 -B jwt_hs256.py                 # mint and verify one token
python3 -B pkce.py                      # a verifier, its challenge and an authorization URL
python3 -B tiny_lsm.py                  # one workload under leveled and size-tiered compaction
python3 -B mtls_demo.py                 # four localhost handshakes against a private CA
python3 -B check_chapter_sync.py        # the code printed in chapter 49b matches these files
```

`-B` stops Python from writing `__pycache__` folders. The test runner prints `ok` or `FAIL` per test with a traceback for failures, then `25 passed, 0 failed`; its exit code is 1 if anything failed. The sync checker ends with `23 lab functions and classes shown in chapter 49b, 0 difference(s)`.

## `jwt_hs256.py`: HS256 JSON Web Tokens

### Intuition

A session cookie is a random handle the server looks up on every request, which needs a shared store that every service can reach. A JSON Web Token turns the lookup inside out: the issuer writes the facts (who, for which API, until when) into the token and signs them, and any service holding the key can check the signature and trust the facts without calling anyone. The price is that a token cannot be recalled once minted, which is why lifetimes are minutes and why anything that must be revocable at once still needs a deny-list or introspection.

The signature is the entire security of the scheme, so the design question is what an attacker who can forge a header can make a careless verifier do. History answers with `alg: none` (the verifier honored a header asking for no signature), algorithm confusion (a header asking for HMAC with a key the verifier thought was an RSA public key), missing audience checks (a token for a cheap service opening an expensive one) and parser differentials (two components disagreeing about which `sub` a payload with duplicate members names). The module is built around refusing every one of those.

### How it works

`sign(claims, key, *, kid=None)` builds a header `{"alg": "HS256", "typ": "JWT"}` (plus `kid` if given), serializes header and claims as compact JSON, base64url-encodes them without padding (`b64url_encode`), computes HMAC-SHA256 over the ASCII bytes of `header.payload`, and returns `header.payload.signature`. `_check_key` runs first: the key must be `bytes` of at least `MIN_KEY_BYTES` (32, RFC 7518's minimum of one hash output), and must not look like a PEM or SSH public key.

`issue(subject, key, *, issuer, audience, ttl=300, now=None, kid=None, **extra)` is the convenience minter: it fills `iss`, `sub`, `aud`, `iat`, `nbf`, `exp = now + ttl` and a random `jti`, then calls `sign`.

`verify(token, keys, *, issuer, audience, now=None, leeway=30, max_age=None, typ="JWT", required=("iss", "aud", "exp", "iat", "sub"), is_revoked=None)` performs the chapter's checklist (49b.4.3) in this order, raising a subclass of `InvalidToken` at the first failure:

1. The token is a `str` with exactly two dots, and all three segments use only the base64url alphabet (`MalformedToken`).
2. The header is decoded by `_json_object`: `b64url_decode` is strict (no padding, no length of 1 mod 4, and the decoded bytes must re-encode to the same text, which rejects nonzero leftover bits), then `json.loads` with `_reject_duplicates` as `object_pairs_hook` and `_reject_constant` as `parse_constant` (Python's JSON otherwise accepts `NaN` and `Infinity`). The result must be an object.
3. `alg` must equal `ALGORITHM` exactly: `none`, `None`, `hs256`, `HS512`, `RS256` and a missing `alg` all raise `BadAlgorithm`. The verifier, never the token, chooses the algorithm.
4. A `crit` header is refused outright; `typ` is compared case-insensitively with the expected type (`"JWT"` by default, `"at+jwt"` for RFC 9068 access tokens, `None` to skip).
5. If `keys` is a dict, the header's `kid` selects the key; a missing, non-string or unknown `kid` raises `BadSignature("unknown key id")`. Otherwise `keys` is the one key. `_check_key` then applies to whichever key was chosen.
6. The expected HMAC is compared with `hmac.compare_digest` (constant time).
7. Only now is the payload decoded, with the same strict parser. Every claim in `required` must be present.
8. Time claims, checked by `_numeric_date` (a finite number, not a bool, not a string): `exp` fails when `now >= exp + leeway` (`ExpiredToken`); `nbf` fails when `now + leeway < nbf` (`NotYetValid`); `iat` in the future fails (`BadClaim`), and `max_age` bounds `now - iat` (`ExpiredToken`).
9. `iss` must equal `issuer` exactly; `aud` may be a string or a list and must contain `audience` (`BadClaim`).
10. If `is_revoked` is given, it is called with `jti` and a true result rejects the token.

The exception hierarchy (`MalformedToken`, `BadAlgorithm`, `BadSignature`, `ExpiredToken`, `NotYetValid`, `BadClaim`) lets your code log the reason while telling the caller only that the token was invalid.

### Example

```python
>>> import json
>>> from jwt_hs256 import issue, verify, sign, b64url_encode, b64url_decode, BadSignature, BadAlgorithm, ExpiredToken
>>> key, now = bytes(range(32)), 1_790_000_000
>>> token = issue("user-42", key, issuer="https://auth.example.com", audience="orders-api", ttl=300, now=now, scope="orders:read")
>>> header, payload, sig = token.split(".")
>>> json.loads(b64url_decode(header))
{'alg': 'HS256', 'typ': 'JWT'}
>>> claims = verify(token, key, issuer="https://auth.example.com", audience="orders-api", now=now + 10)
>>> claims["sub"], claims["exp"] - claims["iat"], claims["scope"]
('user-42', 300, 'orders:read')
>>> verify(token, key, issuer="https://auth.example.com", audience="orders-api", now=now + 400)
Traceback (most recent call last):
  ...
jwt_hs256.ExpiredToken: token has expired
>>> evil = b64url_encode(json.dumps({**claims, "scope": "orders:admin"}).encode())
>>> verify(f"{header}.{evil}.{sig}", key, issuer="https://auth.example.com", audience="orders-api", now=now + 10)
Traceback (most recent call last):
  ...
jwt_hs256.BadSignature: signature does not match
>>> unsigned = b64url_encode(b'{"alg":"none","typ":"JWT"}') + "." + payload + "."
>>> verify(unsigned, key, issuer="https://auth.example.com", audience="orders-api", now=now + 10)
Traceback (most recent call last):
  ...
jwt_hs256.BadAlgorithm: algorithm 'none' is not accepted
>>> rotated = sign(claims, b"n" * 32, kid="2026-10")
>>> verify(rotated, {"2026-09": b"o" * 32, "2026-10": b"n" * 32}, issuer="https://auth.example.com", audience="orders-api", now=now + 10)["sub"]
'user-42'
```

`python3 -B jwt_hs256.py` prints a freshly minted token and its verified claims.

### What the tests check

`test_jwt_tampering_is_detected` swaps the payload, flips one signature character, uses the wrong key, and splices the payload of a different valid token. `test_jwt_rejects_alg_none_and_other_algorithms` tries eight `alg` spellings, each unsigned and with a correct HMAC attached. `test_jwt_algorithm_confusion` runs the classic attack end to end: a `naive_verify` that reads the algorithm from the header accepts a token HMAC-signed with a PEM public key, while `verify` refuses the public key as a secret and, holding the real secret, rejects the MAC. `test_jwt_time_claims` covers the leeway on both sides, `nbf`, a future `iat`, `max_age`, and `exp` given as a string, a bool, `null`, a list and `Infinity`. `test_jwt_issuer_audience_and_required_claims`, `test_jwt_key_rotation_by_kid` and `test_jwt_revocation_hook` cover the claim checks, retired or missing `kid` values and the deny-list hook. `test_jwt_strict_parsing` covers padding, missing and extra segments, the four spellings of one signature that a lenient decoder would accept, duplicate `sub` members, an array payload, `crit`, `typ` mismatch and a non-string token.

### What production uses instead, and why

PyJWT (`jwt.decode(token, key, algorithms=["RS256"], audience=..., issuer=..., leeway=30, options={"require": [...]})` with `PyJWKClient` fetching the issuer's key set) or Authlib. They add asymmetric algorithms (RS256, PS256, ES256, Ed25519), so many services can verify tokens that only the identity provider can mint; key fetching and caching from a `jwks_uri` with a refetch on an unknown `kid`; JWE; and years of parser fixes. What HS256 itself cannot defend against: anyone who can verify can also mint, so a shared secret in twenty services is twenty places to steal it. And no verifier defends against a stolen valid token during its lifetime; short lifetimes, rotating refresh tokens and sender-constrained tokens (DPoP, mTLS-bound tokens, 49b.6.6) are for that.

## `pkce.py`: PKCE and a toy authorization server

### Intuition

In the OAuth 2.0 authorization code flow the browser carries only a short-lived, single-use *code* back to the application, which redeems it for tokens on a back channel the browser never sees. A server-side application also presents a client secret at redemption, so an intercepted code is useless. A native or single-page application has no secret (anything it ships can be extracted), and on phones and desktops the redirect lands on a custom URL scheme or a loopback port that another application can register first and so catch the code.

PKCE (RFC 7636) gives the public client a secret that exists for one request only. The client invents a random *code verifier*, sends its SHA-256 hash (the *code challenge*) in the authorization request, and sends the verifier itself when redeeming the code; the server hashes and compares. An interceptor saw the challenge but cannot invert SHA-256. The design is minimal on purpose: one random string, one hash, no new keys, no new round trips.

### How it works

Client side:

- `make_code_verifier(nbytes=32)` returns `nbytes` random bytes (32 to 96) base64url-encoded without padding: 32 bytes give 43 characters, 96 give 128, the limits RFC 7636 section 4.1 sets. The characters are all unreserved, so a verifier can travel in a form body unescaped.
- `s256_challenge(verifier)` checks the verifier against `_VERIFIER` (43 to 128 characters from `[A-Za-z0-9-._~]`) and returns `BASE64URL(SHA256(ASCII(verifier)))`.
- `authorization_url(endpoint, *, client_id, redirect_uri, scope, state, code_challenge, resource=None, nonce=None)` builds the front-channel URL with `response_type=code`, `code_challenge_method=S256`, optionally `resource` (RFC 8707, the API the token is for, which MCP requires) and `nonce` (OpenID Connect, echoed in the ID token). Only the challenge travels here.

Server side:

- `verify_code_verifier(verifier, challenge, method="S256")` is the token endpoint's check: `method` must be `S256` (the `plain` method is refused outright), the verifier must be a string matching `_VERIFIER`, and the recomputed challenge is compared with `hmac.compare_digest`.
- `AuthorizationServer(clients, *, clock=time.time)` holds registered clients (`client_id` to a list of exact redirect URIs), issued codes and issued tokens in memory. `authorize(*, client_id, redirect_uri, code_challenge, code_challenge_method="S256", scope="", user="alice")` is what runs after the user has logged in and consented: the redirect URI must be registered exactly (a mismatch raises `ValueError`, meaning "show an error page, never redirect"), the method must be `S256` and the challenge must look like one, and the returned code is stored with the client, redirect URI, challenge, scope, a `CODE_TTL` of 60 seconds and `used = False`.
- `token(*, code, client_id, redirect_uri, code_verifier)` raises `PermissionError("invalid_grant")` on any failure. An unknown code fails. A code that was already used fails *and revokes every token it produced* (RFC 6749 section 4.1.2's recommendation for replay). Then the code is marked used before anything else is checked, so the first redemption attempt consumes it whether or not it succeeds. Expiry, client binding, redirect URI and the verifier are checked together, and a success returns a random access token.
- `introspect(token)` answers RFC 7662 style: `{"active": False}` for anything unknown or revoked, otherwise `active`, `sub`, `scope` and `client_id`.

### Example

The verifier is the one from RFC 7636 Appendix B, so the challenge is the published test vector.

```python
>>> import pkce
>>> verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
>>> challenge = pkce.s256_challenge(verifier)
>>> challenge
'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
>>> pkce.verify_code_verifier(verifier, challenge)
True
>>> pkce.verify_code_verifier(pkce.make_code_verifier(), challenge)      # an interceptor's guess
False
>>> pkce.verify_code_verifier(verifier, verifier, method="plain")
False
>>> len(pkce.make_code_verifier()), len(pkce.make_code_verifier(96))
(43, 128)
>>> clock = [1000.0]
>>> server = pkce.AuthorizationServer({"cli-app": ["http://127.0.0.1:8765/cb"]}, clock=lambda: clock[0])
>>> code = server.authorize(client_id="cli-app", redirect_uri="http://127.0.0.1:8765/cb", code_challenge=challenge, scope="tickets:read")
>>> token = server.token(code=code, client_id="cli-app", redirect_uri="http://127.0.0.1:8765/cb", code_verifier=verifier)
>>> server.introspect(token)
{'active': True, 'sub': 'alice', 'scope': 'tickets:read', 'client_id': 'cli-app'}
>>> server.token(code=code, client_id="cli-app", redirect_uri="http://127.0.0.1:8765/cb", code_verifier=verifier)
Traceback (most recent call last):
  ...
PermissionError: invalid_grant
>>> server.introspect(token)                                             # the replay revoked it
{'active': False}
>>> server.authorize(client_id="cli-app", redirect_uri="http://127.0.0.1:8765/cb/../evil", code_challenge=challenge)
Traceback (most recent call last):
  ...
ValueError: unknown client or redirect URI
```

`python3 -B pkce.py` prints a fresh verifier, its challenge and a complete authorization URL.

### What the tests check

`test_pkce_rfc7636_appendix_b` reproduces the RFC's vector byte for byte. `test_pkce_verifier_rules` checks lengths 43 and 128, uniqueness, the byte-count limits and character class, that a wrong verifier, the `plain` method, `None` and a 200-character string all fail, and that the authorization URL carries `code_challenge_method=S256`, `resource` and `nonce` but never the verifier. `test_pkce_authorization_server_flow_and_attacks` runs the honest flow, the replay (the code fails and the earlier token goes inactive), the interception (a malicious app with the code but a wrong verifier is refused, and the legitimate client's later attempt is refused too because the code was consumed), a traversal in the redirect URI, an unknown client, the `plain` method, a token request from a different client or redirect URI, an expired code via the injected clock, and a code that was never issued.

### What production uses instead, and why

The OAuth client of Authlib, `requests-oauthlib`, MSAL, the Google or Okta SDKs or the MCP SDK, all of which generate the verifier and challenge exactly this way, against a real authorization server (Keycloak, Entra ID, Okta, Auth0). The toy has no login or consent screen, no client secrets, no refresh tokens (rotation with reuse detection is chapter 49b's exercise 2), no pushed authorization requests and no DPoP, and it keeps everything in a dict. PKCE itself does not defend against a malicious application the user authorizes *as itself*, phishing of the login page, or a token stolen after issuance; `state` still defends against CSRF on the redirect and `nonce` still binds an ID token to its request, so the chapter (49b.7.3) says to keep all three.

## `tiny_lsm.py`: a log-structured merge-tree store

### Intuition

A B-tree updates in place: changing a 100-byte row rewrites the page that holds it, and small random writes cost seeks on disks and erase cycles on SSDs. A log-structured merge tree never updates in place: every write is appended to a log, kept in a sorted in-memory table, and eventually written out sequentially as an immutable sorted file, and files are merged in the background. Writes become sequential and batched, which is why LevelDB, RocksDB, Pebble, Cassandra, ScyllaDB and the storage inside many vector databases use the design; the cost moves to reads, which may consult several files, and to merging, which rewrites data more than once.

Three questions shape every LSM engine, and the module makes each visible. How does a read avoid touching every file? Key ranges and a Bloom filter per table rule out nearly all of them without I/O, and a sparse index turns the rest into one block read. How does a delete work when files are immutable? A *tombstone* shadows older versions until a merge can prove no older version exists anywhere. How does the store survive a crash halfway through a flush or a merge? No file is modified after it is named, and the set of live files switches with one atomic rename of a MANIFEST.

### How it works

**On disk.** A directory holds `wal.log`, numbered `.sst` files and a `MANIFEST`. `encode_record(seq, key, value)` frames one WAL record as a line: the CRC-32 of the JSON body `[seq, key, value]` in hex, a space, the body. `decode_records(data)` returns `(records, valid_length)` and stops at the first torn or corrupt record, because a crash can only damage the tail. An `SSTable` is one JSON line `[key, seq, value]` per entry in key order, a footer line holding the sparse index (first key and byte offset of every `index_every` entries), the Bloom filter bits, the count and the key and sequence ranges, then the footer's offset as 20 digits. `SSTable.write` writes to `path + ".tmp"` and renames, so a table exists completely under its name or not at all. `SSTable.find(key)` bisects the index and reads one block; `SSTable.scan(start, end)` returns a range, tombstones included.

**Bloom filter.** `BloomFilter.for_capacity(n_items, fp_rate=0.01)` sizes the bit array with m = -n ln p / (ln 2)^2 and k = (m / n) ln 2 hash positions. `_positions` derives the k positions from two 64-bit halves of one SHA-256 digest (h1 + i * h2), `add` sets bits and `might_contain` answers "definitely absent" or "maybe present"; there are never false negatives.

**Write path.** `LSMStore.put(key, value)` and `delete(key)` both go through `_write`: increment `_seq`, append the record to the WAL and `flush()` it to the operating system (with `sync=True`, also `fsync` it), then set `memtable[key] = (seq, value)`, where `value None` is a tombstone. When the memtable's byte estimate reaches `memtable_bytes`, `flush()` sorts it, writes it as a new level-0 table through `_new_table`, appends the table to `levels[0]`, calls `_save_manifest` (write `MANIFEST.tmp`, `os.replace`, and `fsync` the directory when `sync=True`), then `_reset_wal` and `_maybe_compact`. The order matters: the table is named in the MANIFEST before the WAL is emptied, so a crash between the two replays records that are already in a table, which is harmless because sequence numbers make the replay idempotent.

**Read path.** `get(key, default=None)` checks the memtable, then tables sorted by `max_seq` descending. It stops as soon as the best version found is newer than every remaining table's `max_seq`, skips tables whose key range excludes the key, skips tables whose Bloom filter says absent (`stats["bloom_skips"]`), and calls `find` on the rest (`stats["block_reads"]`). Searching by maximum sequence number rather than by level keeps reads correct under size-tiered compaction, where a merged table can be newer than smaller ones. `scan(start, end)` merges the memtable and every table's `scan` with `merge_newest`, which is a `heapq.merge` keyed on `(key, -seq)` that yields each key once, newest version first, and drops tombstones only when `can_drop(key, seq)` allows it.

**Compaction.** `_maybe_compact` loops until `_pick_leveled` or `_pick_tiered` returns no job. Leveled: when level 0 holds `l0_trigger` tables they are merged with the overlapping level-1 tables; when level L (L >= 1) exceeds `level_base_bytes * fanout ** (L - 1)` one of its files, chosen round-robin by `pointers`, is merged with the overlapping files of level L + 1, or relinked without a rewrite (a trivial move) if nothing overlaps. Tiered: `size_tiered_buckets` groups tables of similar size the way Cassandra does, and a bucket with `tier_min` tables is merged into one. `_compact` builds `can_drop` from the tables *outside* the merge: a tombstone may go only if no outside table with an older minimum sequence number could hold the key (by range and Bloom filter). It writes outputs through `_write_run` (split at about `target_file_bytes` for leveled), saves the MANIFEST, and only then deletes the inputs. `compact_all` merges everything into one run.

**Recovery.** `_recover` opens the tables the MANIFEST lists, refuses a directory created with the other strategy, deletes every `.tmp` and every `.sst` the MANIFEST does not name, replays the WAL into the memtable, truncates a torn tail, and runs `_maybe_compact` to finish work a crash left undone. `report()` derives write, space and read amplification from the `stats` counters.

### Example

```python
>>> import os, tempfile
>>> from tiny_lsm import LSMStore, BloomFilter, encode_record, decode_records, merge_newest
>>> d = tempfile.mkdtemp()
>>> store = LSMStore(d, strategy="leveled", memtable_bytes=256)
>>> for i in range(100):
...     store.put(f"user:{i:03d}", f"name-{i}")
>>> store.delete("user:007")
>>> store.put("user:042", "Ada")
>>> store.get("user:042"), store.get("user:007"), store.get("nobody", "?")
('Ada', None, '?')
>>> store.scan("user:040", "user:043")
[('user:040', 'name-40'), ('user:041', 'name-41'), ('user:042', 'Ada')]
>>> store.report()
{'tables': 12, 'levels': [0, 2, 10], 'write_amp': 2.0, 'space_amp': 1.0, 'probes_per_get': 0.0, 'block_reads_per_get': 0.0}
>>> store.close()
>>> store = LSMStore(d, strategy="leveled", memtable_bytes=256)      # reopen: MANIFEST plus WAL replay
>>> store.get("user:042"), len(store.scan())
('Ada', 99)
>>> bloom = BloomFilter.for_capacity(1000, 0.01)
>>> bloom.num_bits, bloom.num_hashes
(9586, 7)
>>> data = encode_record(1, "a", "x") + encode_record(2, "a", None)
>>> data
b'e99a024b [1,"a","x"]\n6ced6c32 [2,"a",null]\n'
>>> decode_records(data[:-4])                                           # a torn last record is dropped
([(1, 'a', 'x')], 21)
>>> older = [("a", 1, "A1"), ("b", 2, "B"), ("c", 3, "C")]
>>> newer = [("a", 9, "A2"), ("c", 8, None)]
>>> list(merge_newest([older, newer]))
[('a', 9, 'A2'), ('b', 2, 'B'), ('c', 8, None)]
>>> list(merge_newest([older, newer], can_drop=lambda key, seq: True))
[('a', 9, 'A2'), ('b', 2, 'B')]
```

`python3 -B tiny_lsm.py` runs 30,000 operations over 3,000 keys with an 8 KB memtable, then 5,000 lookups, half for keys never written, under both strategies, and prints the table that chapter 49b.15.4 reproduces: leveled compaction ends with 18 tables, write amplification 3.92 and space amplification 1.4; size-tiered with 7 tables, 2.63 and 2.83. Block reads stay near 0.5 per lookup because the Bloom filters answer most of the misses.

### What the tests check

The building blocks first: `test_lsm_bloom_filter` checks the sizing formula (9,586 bits and 7 hashes for 1,000 keys at 1 percent), no false negatives, under 2 percent false positives over 20,000 absent keys, and reconstruction from saved bits. `test_lsm_wal_records` round-trips records containing newlines and non-ASCII keys, cuts the last record, flips a byte in the middle, and feeds an empty log and a bad CRC. `test_lsm_merge_newest` and `test_lsm_size_tiered_buckets` pin the merge order and the bucketing.

Then the store. `check_invariants` asserts sorted unique keys and correct metadata in every table, non-overlapping tables in levels 1 and deeper, and that the files on disk are exactly the tables the MANIFEST names. `test_lsm_randomized_against_dict` runs `run_random_workload` for both strategies and four seeds: 2,500 random puts, deletes, gets, scans, flushes, major compactions, clean closes and simulated crashes, checking every read against a dict. `test_lsm_torn_and_corrupt_wal` appends a torn record and corrupts a middle one. `test_lsm_crash_between_manifest_and_wal_reset` and `test_lsm_crash_during_compaction` inject failures at the two dangerous moments (after the MANIFEST is saved but before the WAL is emptied; after a compaction's outputs are written but before the MANIFEST switch) and check that recovery deletes half-finished outputs and loses nothing. `test_lsm_old_files_cannot_resurrect_deleted_keys` copies a compaction's input files back into the directory and reopens. `test_lsm_tombstone_kept_while_older_data_exists` merges only two small newer tables and checks the tombstone survives, then checks a major compaction removes it. `test_lsm_bloom_filters_skip_reads_for_missing_keys` looks up 500 absent keys inside the tables' ranges and requires at most 5 percent of the probes to read a block.

### What production uses instead, and why

RocksDB (leveled by default, inside TiKV, YugabyteDB, Kafka Streams and Flink), LevelDB, Pebble (CockroachDB), or the LSM engine inside Cassandra, ScyllaDB, Weaviate and Prometheus. They add a skip-list memtable instead of a dict sorted at every flush; binary blocks with per-block checksums and compression instead of JSON lines; a block cache; concurrent writers and background compaction threads with write stalls when compaction falls behind; snapshots pinned to a sequence number (chapter 49b's exercise 4); and column families, prefix Bloom filters and dozens of tunables. The failures the toy does not survive: bit rot inside an SSTable (it checks WAL records, not table blocks), two processes on one directory, and, with the default `sync=False`, a power failure rather than a process crash.

## `mtls_demo.py`: TLS and mutual TLS over localhost

### Intuition

Ordinary TLS authenticates one side: the client checks that the server's certificate chains to a trusted root and names the host it meant to reach, and the server learns nothing about the client beyond its IP address. Services then identify callers with API keys and bearer tokens, which get copied into configuration, logs and tickets. Mutual TLS makes the server demand a certificate too, so every connection arrives with a proven client identity (usually a SPIFFE ID in the certificate's URI SAN) signed by a private key that never left the workload. Service meshes do this transparently between pods; banks demand it from partners.

The detail people get wrong, and the one the demo exists to show: in TLS 1.3 the client sends its certificate *after* the server's `Finished`, so a client without an acceptable certificate completes its side of the handshake and learns of the rejection only on its first read. Errors surface in request code, not connect code, which changes where you look when a service "connects fine but every call fails".

### How it works

`make_pki(d)` shells out to `openssl` in a temporary directory: a self-signed P-256 root (`ca.pem`, `CA:TRUE`, `keyCertSign`), then for each leaf a key, a CSR and a certificate signed by the CA with an extension file. The server leaf carries `DNS:orders.internal` and `extendedKeyUsage=serverAuth`; the client leaf carries `URI:spiffe://example.org/ns/agents/sa/support-agent` (`SPIFFE_ID`) and `clientAuth`. Both also carry `subjectKeyIdentifier` and `authorityKeyIdentifier`, because Python 3.13 and newer verify with OpenSSL's strict X.509 flags, which reject an issued certificate without an authority key identifier. No key is stored in the repository.

`handshake(d, *, require_client_cert, client_cert, hostname="orders.internal")` runs one connection on `127.0.0.1` and an ephemeral port. The server context is `ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)` with the server chain loaded; with `require_client_cert` it sets `verify_mode = CERT_REQUIRED` and trusts only `ca.pem` for clients. The client context is `create_default_context(cafile=ca.pem)`, with the agent certificate loaded when `client_cert` is true. A thread accepts, wraps the socket, reads the peer certificate's URI SANs into `server_saw` and sends `hello`; the main thread connects with `server_hostname=hostname`, records `tls.version()` and the reply, and catches `SSLCertVerificationError` and other `SSLError`s into `client_error`. The server records its own failure reason into `server_error`.

`main()` skips with exit 0 if `openssl` is not on `PATH`, otherwise runs four handshakes and asserts the outcomes before printing them:

1. Server-only TLS: `TLSv1.3`, reply received, the server saw no client identity.
2. mTLS with the agent certificate: the server saw `[SPIFFE_ID]`.
3. mTLS without a client certificate: the client's `wrap_socket` returned (`handshake` is `TLSv1.3`), no reply arrived, the client's first `recv` raised `TLSV13_ALERT_CERTIFICATE_REQUIRED`, and the server logged `PEER_DID_NOT_RETURN_A_CERTIFICATE`.
4. A client expecting `billing.internal`: no handshake at all; the client error contains `Hostname mismatch`.

### Example

```text
$ python3 -B mtls_demo.py
server-only TLS                    {'handshake': 'TLSv1.3', 'server_saw': [], 'reply': b'hello'}
mTLS with a client certificate     {'handshake': 'TLSv1.3', 'server_saw': ['spiffe://example.org/ns/agents/sa/support-agent'], 'reply': b'hello'}
mTLS without a client certificate  {'handshake': 'TLSv1.3', 'server_error': 'PEER_DID_NOT_RETURN_A_CERTIFICATE', 'client_error': 'TLSV13_ALERT_CERTIFICATE_REQUIRED'}
wrong hostname                     {'client_error': "Hostname mismatch, certificate is not valid for 'billing.internal'.", 'server_error': 'SSLV3_ALERT_BAD_CERTIFICATE'}
```

The exact wording of the server's alert in the last line comes from OpenSSL and may differ between versions; `main` asserts only the client side there.

### What the tests check

`test_mtls_localhost_handshakes` imports the module and asserts that `main()` returns 0, which means all four assertions inside it held (or the demo skipped itself for lack of `openssl`).

### What production uses instead, and why

A workload identity system: SPIRE issuing short-lived X.509 SVIDs after attesting the workload, cert-manager in Kubernetes, or a service mesh (Istio, Linkerd) that rotates certificates and enforces mTLS in the sidecar. The demo does not rotate the CA with an overlap period (chapter 49b's exercise 5), send intermediates, check revocation, bind tokens to the client certificate (RFC 8705), or handle termination at a proxy, where the application sees the client identity only in a header such as `x-forwarded-client-cert`. mTLS itself does not defend against a compromised workload using its own legitimate key, or a server that trusts a public root store for clients and so admits certificates issued to strangers; authorize on the SAN, not on "the chain verified".

## `check_chapter_sync.py`

The checker extracts every top-level `def` and `class` from the chapter's ```` ```python ```` blocks, looks for an object of the same name in `jwt_hs256`, `pkce` or `tiny_lsm`, and compares `inspect.getsource` with the printed text. Functions that exist only in the chapter (the toy RSA and Diffie-Hellman, the cookie examples, the X25519 walk-through) are skipped because no lab module has an object of that name. It exits 1 on any difference or if nothing matched, so a chapter edit that leaves the tested code behind fails loudly.

## How the four modules connect to interview questions

Chapter 49b.16 lists fifteen questions with model answers; the lab lets you answer eight of them from code you have run.

- **Why is `sha256(secret + message)` a bad MAC?** (Q1) Length extension. `jwt_hs256.sign` uses `hmac.new(key, signing_input, hashlib.sha256)` and `verify` compares with `hmac.compare_digest`.
- **Walk through a TLS 1.3 handshake.** (Q3) `mtls_demo.handshake` records `tls.version()` as `TLSv1.3` after one round trip, and case 3 shows the client certificate arriving after the server's `Finished`.
- **Server-side sessions or JWTs?** (Q5) Sessions revoke instantly but need a shared store; JWTs verify anywhere but cannot be recalled. `issue` defaults to a 300-second `ttl`, and `verify` takes `is_revoked` for the cases where revocation must be immediate.
- **How do you validate a JWT?** (Q6) Walk through `verify` in order: algorithm allow-list, key by `kid`, constant-time signature, then `iss`, `aud`, the time claims, `typ` and required claims. `test_jwt_algorithm_confusion` is the story about why the verifier chooses the algorithm.
- **Why does a code, not a token, pass through the browser, and what does PKCE add?** (Q8) `authorization_url` carries only the challenge; `AuthorizationServer.token` redeems the code on the back channel; `test_pkce_authorization_server_flow_and_attacks` is the interception attack failing.
- **Access token versus ID token?** (Q9) `authorization_url` takes `resource` (which API the access token is for) and `nonce` (which request the ID token answers); `introspect` is how a resource server checks an opaque access token.
- **What does mTLS add, and what breaks?** (Q12) Case 2 of the demo is the identity in the SAN; case 3 is the error surfacing on the first read.
- **When would you choose an LSM tree over a B-tree?** (Q15) Run `tiny_lsm.py` and explain the two rows: leveled rewrites more (write amplification 3.92 against 2.63) and stores less garbage (space amplification 1.4 against 2.83); then explain tombstones with `test_lsm_tombstone_kept_while_older_data_exists`.

Questions 2, 4, 7, 10, 11, 13 and 14 (passwords, missing intermediates, `SameSite`, SSO and SCIM, MCP authorization, PID 1 and `set -euo pipefail`) are chapter-only, though the `resource` parameter in `authorization_url` is part of the answer to question 11.

## Map of functions to chapter sections

| Object | File | Chapter section | Shown verbatim |
|---|---|---|---|
| `InvalidToken` and its six subclasses | `jwt_hs256.py` | 49b.4.4 | yes |
| `b64url_encode`, `b64url_decode` | `jwt_hs256.py` | 49b.4.1 (encoding), 49b.4.4 | yes |
| `_reject_constant`, `_reject_duplicates`, `_json_object` | `jwt_hs256.py` | 49b.4.3 step 1, 49b.4.5 (parser differentials) | yes |
| `_check_key` | `jwt_hs256.py` | 49b.4.5 (algorithm confusion) | yes |
| `_numeric_date`, `sign`, `verify` | `jwt_hs256.py` | 49b.4.2 to 49b.4.4 | yes |
| `issue` | `jwt_hs256.py` | 49b.4.5 (short lifetimes, `jti`) | described |
| `make_code_verifier`, `s256_challenge`, `verify_code_verifier` | `pkce.py` | 49b.7.3 | yes |
| `authorization_url` | `pkce.py` | 49b.6.2 (the flow), 49b.7.1 (`nonce`), 49b.8.5 (`resource`) | described |
| `AuthorizationServer` | `pkce.py` | 49b.6.2, 49b.7.3 | described |
| `encode_record`, `decode_records` | `tiny_lsm.py` | 49b.15.2 | yes |
| `BloomFilter` | `tiny_lsm.py` | 49b.15.3 | yes |
| `merge_newest` | `tiny_lsm.py` | 49b.15.4 | yes |
| `size_tiered_buckets` | `tiny_lsm.py` | 49b.15.4 (the compaction table) | described |
| `SSTable`, `LSMStore` | `tiny_lsm.py` | 49b.15.2 to 49b.15.6 | described |
| `make_pki`, `handshake`, `main` | `mtls_demo.py` | 49b.9.1 (certificates), 49b.11.1 | described |

## Exercises

1. Add a `max_lifetime` option to `jwt_hs256.verify` that rejects tokens whose `exp - iat` exceeds it, with tests for a token minted with a one-year lifetime.
2. Add `ES256` verification behind the same interface using the `cryptography` package, keeping the rule that the verifier, not the token, chooses the algorithm.
3. Give `LSMStore` snapshots: a read that pins a sequence number and ignores newer versions. Which compactions must now keep older versions?
4. Replace the memtable dict, which is sorted on every flush and scan, with a skip list, and measure `scan` on a memtable of 100,000 keys.
5. Add a block cache to `SSTable.find` and report the hit rate from `tiny_lsm.py` for a skewed (Zipf) key distribution.
6. Change `mtls_demo.py` so the client certificate expires in the past and record which side reports the error, and how.
