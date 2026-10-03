#!/usr/bin/env python3
"""Tests for the chapter 49b lab, with plain asserts and the standard library only.

    python3 -B test_cs_essentials.py            # all tests, a few seconds
    python3 -B test_cs_essentials.py lsm        # only tests whose name contains "lsm"

Exit code 1 if any test fails.
"""
import base64
import hashlib
import hmac
import inspect
import json
import os
import random
import shutil
import sys
import tempfile
import traceback

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jwt_hs256 as jwt  # noqa: E402
import pkce  # noqa: E402
import tiny_lsm  # noqa: E402

ISS, AUD = "https://auth.example.com", "orders-api"
KEY = bytes(range(32))
NOW = 1_790_000_000


def raises(exc_type, fn, *args, **kwargs):
    """Assert that fn(*args, **kwargs) raises exc_type (or a subclass); return the exception."""
    try:
        fn(*args, **kwargs)
    except exc_type as err:
        return err
    raise AssertionError(f"{fn.__name__} did not raise {exc_type.__name__}")


def forge(header, payload, key: bytes) -> str:
    """Sign arbitrary header and payload bytes (or objects) with HS256, to build hostile test tokens."""
    def enc(part):
        raw = part if isinstance(part, bytes) else json.dumps(part).encode()
        return jwt.b64url_encode(raw)
    signing_input = enc(header) + "." + enc(payload)
    signature = hmac.new(key, signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + jwt.b64url_encode(signature)


def claims(**overrides):
    base = {"iss": ISS, "aud": AUD, "sub": "user-42", "iat": NOW, "nbf": NOW, "exp": NOW + 300, "jti": "t-1"}
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def check(token, **kwargs):
    kwargs.setdefault("now", NOW + 10)
    return jwt.verify(token, kwargs.pop("keys", KEY), issuer=kwargs.pop("issuer", ISS),
                      audience=kwargs.pop("audience", AUD), **kwargs)


# ---------------------------------------------------------------- JWT

def test_jwt_round_trip():
    token = jwt.sign(claims(scope="orders:read"), KEY)
    assert token.count(".") == 2
    assert check(token)["scope"] == "orders:read"
    issued = jwt.issue("user-7", KEY, issuer=ISS, audience=AUD, ttl=60, now=NOW)
    got = check(issued)
    assert got["sub"] == "user-7" and got["exp"] - got["iat"] == 60 and len(got["jti"]) >= 16


def test_jwt_tampering_is_detected():
    token = jwt.sign(claims(role="viewer"), KEY)
    header, payload, signature = token.split(".")
    evil = jwt.b64url_encode(json.dumps(claims(role="admin")).encode())
    raises(jwt.BadSignature, check, f"{header}.{evil}.{signature}")
    flipped = signature[:-2] + ("A" if signature[-2] != "A" else "B") + signature[-1]
    raises(jwt.BadSignature, check, f"{header}.{payload}.{flipped}")
    raises(jwt.BadSignature, check, token, keys=bytes(32))                 # wrong key
    other = jwt.sign(claims(sub="someone-else"), KEY)
    raises(jwt.BadSignature, check, f"{header}.{other.split('.')[1]}.{signature}")


def test_jwt_rejects_alg_none_and_other_algorithms():
    payload = jwt.b64url_encode(json.dumps(claims(role="admin")).encode())
    for alg in ("none", "None", "NONE", "", "hs256", "HS512", "RS256", None):
        header = {"typ": "JWT"} if alg is None else {"alg": alg, "typ": "JWT"}
        unsigned = jwt.b64url_encode(json.dumps(header).encode()) + "." + payload + "."
        raises(jwt.BadAlgorithm, check, unsigned)
        raises(jwt.BadAlgorithm, check, forge(header, claims(), KEY))       # even with a valid MAC


def test_jwt_algorithm_confusion():
    # The server's RS256 public key is public. A naive verifier picks the algorithm from the header and
    # passes "the key" to it; for "HS256" that key becomes an HMAC secret the attacker also knows.
    public_pem = b"-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE\n-----END PUBLIC KEY-----\n"
    forged = forge({"alg": "HS256", "typ": "JWT"}, claims(role="admin"), public_pem)

    def naive_verify(token, key):
        header_b64, payload_b64, sig_b64 = token.split(".")
        header = json.loads(jwt.b64url_decode(header_b64))
        if header["alg"] == "HS256":
            mac = hmac.new(key, f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
            if mac != jwt.b64url_decode(sig_b64):
                raise ValueError("bad signature")
        return json.loads(jwt.b64url_decode(payload_b64))   # (RS256 branch omitted)

    assert naive_verify(forged, public_pem)["role"] == "admin"       # the attack works on the naive code
    raises(ValueError, check, forged, keys=public_pem)               # ours refuses a public key as a secret
    raises(jwt.BadSignature, check, forged)                          # and the real secret does not match
    raises(ValueError, jwt.sign, claims(), public_pem)
    raises(ValueError, jwt.sign, claims(), b"too-short-secret")


def test_jwt_time_claims():
    token = jwt.sign(claims(), KEY)
    assert check(token, now=NOW + 300 + 29)                           # inside the 30-second leeway
    raises(jwt.ExpiredToken, check, token, now=NOW + 300 + 30)
    raises(jwt.ExpiredToken, check, token, now=NOW + 301, leeway=0)
    early = jwt.sign(claims(nbf=NOW + 120), KEY)
    raises(jwt.NotYetValid, check, early, now=NOW + 60)
    assert check(early, now=NOW + 100)                                # 20 s early is inside the leeway
    future = jwt.sign(claims(iat=NOW + 3600, nbf=None, exp=NOW + 7200), KEY)
    raises(jwt.BadClaim, check, future)
    raises(jwt.ExpiredToken, check, token, now=NOW + 200, max_age=60)
    for bad in ("1790000300", True, None, [1], float("inf")):
        raw = forge({"alg": "HS256", "typ": "JWT"}, {**claims(), "exp": bad}, KEY) if bad != float("inf") \
            else forge({"alg": "HS256", "typ": "JWT"}, b'{"iss":"%s","aud":"%s","sub":"x","iat":1,"exp":Infinity}'
                       % (ISS.encode(), AUD.encode()), KEY)
        raises(jwt.InvalidToken, check, raw)


def test_jwt_issuer_audience_and_required_claims():
    raises(jwt.BadClaim, check, jwt.sign(claims(iss="https://evil.example.com"), KEY))
    raises(jwt.BadClaim, check, jwt.sign(claims(aud="billing-api"), KEY))
    assert check(jwt.sign(claims(aud=["billing-api", AUD]), KEY))
    raises(jwt.BadClaim, check, jwt.sign(claims(aud={"x": AUD}), KEY))
    raises(jwt.BadClaim, check, jwt.sign(claims(exp=None), KEY))       # exp is required by default
    raises(jwt.BadClaim, check, jwt.sign(claims(sub=None), KEY))
    assert check(jwt.sign(claims(sub=None), KEY), required=("iss", "aud", "exp"))


def test_jwt_key_rotation_by_kid():
    old, new = b"o" * 32, b"n" * 32
    token = jwt.sign(claims(), old, kid="2026-09")
    assert check(token, keys={"2026-09": old, "2026-10": new})
    raises(jwt.BadSignature, check, token, keys={"2026-10": new})      # retired key
    raises(jwt.BadSignature, check, jwt.sign(claims(), old), keys={"2026-09": old})   # no kid
    raises(jwt.BadSignature, check, forge({"alg": "HS256", "typ": "JWT", "kid": ["x"]}, claims(), old),
           keys={"2026-09": old})


def test_jwt_strict_parsing():
    token = jwt.sign(claims(), KEY)
    header, payload, signature = token.split(".")
    raises(jwt.MalformedToken, check, token + "=")                     # padding is not allowed
    raises(jwt.MalformedToken, check, header + "." + payload)
    raises(jwt.MalformedToken, check, token + ".x")
    raises(jwt.MalformedToken, check, f"{header}.{payload}.{signature[:-1]}*")
    # The last of 43 characters carries 2 unused bits: a lenient decoder maps four spellings to one value.
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    variant = signature[:-1] + alphabet[alphabet.index(signature[-1]) ^ 1]
    lenient = base64.urlsafe_b64decode
    assert lenient(variant + "=") == lenient(signature + "=") and variant != signature
    raises(jwt.MalformedToken, check, f"{header}.{payload}.{variant}")
    dup = b'{"iss":"%s","aud":"%s","sub":"a","sub":"admin","iat":%d,"exp":%d}' % (
        ISS.encode(), AUD.encode(), NOW, NOW + 300)
    raises(jwt.MalformedToken, check, forge({"alg": "HS256", "typ": "JWT"}, dup, KEY))
    raises(jwt.MalformedToken, check, forge({"alg": "HS256", "typ": "JWT"}, b"[1, 2]", KEY))
    raises(jwt.MalformedToken, check, forge({"alg": "HS256", "typ": "JWT", "crit": ["exp"]}, claims(), KEY))
    raises(jwt.MalformedToken, check, forge({"alg": "HS256", "typ": "at+jwt"}, claims(), KEY))
    assert check(forge({"alg": "HS256", "typ": "at+jwt"}, claims(), KEY), typ="at+jwt")
    assert check(forge({"alg": "HS256"}, claims(), KEY), typ=None)
    raises(jwt.MalformedToken, check, 12345)


def test_jwt_revocation_hook():
    token = jwt.sign(claims(jti="revoked-1"), KEY)
    raises(jwt.BadClaim, check, token, is_revoked={"revoked-1"}.__contains__)
    assert check(jwt.sign(claims(jti="fine"), KEY), is_revoked={"revoked-1"}.__contains__)


# ---------------------------------------------------------------- PKCE

def test_pkce_rfc7636_appendix_b():
    octets = bytes([116, 24, 223, 180, 151, 153, 224, 37, 79, 250, 96, 125, 216, 173, 187, 186, 22,
                    212, 37, 77, 105, 214, 191, 240, 91, 88, 5, 88, 83, 132, 141, 121])
    verifier = base64.urlsafe_b64encode(octets).rstrip(b"=").decode()
    assert verifier == "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert list(hashlib.sha256(verifier.encode()).digest()) == [
        19, 211, 30, 150, 26, 26, 216, 236, 47, 22, 177, 12, 76, 152, 46, 8, 118, 168, 120, 173, 109,
        241, 68, 86, 110, 225, 137, 74, 203, 112, 249, 195]
    assert pkce.s256_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    assert pkce.verify_code_verifier(verifier, "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM")


def test_pkce_verifier_rules():
    v = pkce.make_code_verifier()
    assert len(v) == 43 and len(pkce.make_code_verifier(96)) == 128
    assert len({pkce.make_code_verifier() for _ in range(200)}) == 200
    raises(ValueError, pkce.make_code_verifier, 31)
    raises(ValueError, pkce.make_code_verifier, 97)
    raises(ValueError, pkce.s256_challenge, "too-short")
    raises(ValueError, pkce.s256_challenge, "a" * 42 + "!")
    assert pkce.s256_challenge("a" * 43) and pkce.s256_challenge("~._-" * 32)
    c = pkce.s256_challenge(v)
    assert not pkce.verify_code_verifier(pkce.make_code_verifier(), c)
    assert not pkce.verify_code_verifier(v, c, method="plain")
    assert not pkce.verify_code_verifier(c, c, method="plain")
    assert not pkce.verify_code_verifier(None, c) and not pkce.verify_code_verifier("x" * 200, c)
    url = pkce.authorization_url("https://as.example.com/authorize", client_id="app", scope="openid",
                                 redirect_uri="http://127.0.0.1:8765/cb", state="s1", code_challenge=c,
                                 resource="https://mcp.example.com/mcp", nonce="n1")
    assert "code_challenge_method=S256" in url and v not in url
    assert "resource=https%3A%2F%2Fmcp.example.com%2Fmcp" in url and "nonce=n1" in url


def test_pkce_authorization_server_flow_and_attacks():
    clock = [1000.0]
    server = pkce.AuthorizationServer({"app": ["http://127.0.0.1:8765/cb"]}, clock=lambda: clock[0])
    redirect = "http://127.0.0.1:8765/cb"

    # The honest flow.
    verifier = pkce.make_code_verifier()
    code = server.authorize(client_id="app", redirect_uri=redirect, code_challenge=pkce.s256_challenge(verifier),
                            scope="tickets:read")
    token = server.token(code=code, client_id="app", redirect_uri=redirect, code_verifier=verifier)
    assert server.introspect(token) == {"active": True, "sub": "alice", "scope": "tickets:read", "client_id": "app"}

    # Replaying the same code fails and revokes what it produced (RFC 6749 section 4.1.2).
    raises(PermissionError, server.token, code=code, client_id="app", redirect_uri=redirect, code_verifier=verifier)
    assert server.introspect(token) == {"active": False}

    # A malicious app intercepts the code but never saw the verifier.
    verifier = pkce.make_code_verifier()
    code = server.authorize(client_id="app", redirect_uri=redirect, code_challenge=pkce.s256_challenge(verifier))
    raises(PermissionError, server.token, code=code, client_id="app", redirect_uri=redirect,
           code_verifier=pkce.make_code_verifier())
    raises(PermissionError, server.token, code=code, client_id="app", redirect_uri=redirect,
           code_verifier=verifier)                                     # the code was consumed by that attempt

    # Exact redirect matching, client binding, expiry and the plain method.
    raises(ValueError, server.authorize, client_id="app", redirect_uri=redirect + "/../evil",
           code_challenge=pkce.s256_challenge(verifier))
    raises(ValueError, server.authorize, client_id="other", redirect_uri=redirect,
           code_challenge=pkce.s256_challenge(verifier))
    raises(ValueError, server.authorize, client_id="app", redirect_uri=redirect, code_challenge=verifier,
           code_challenge_method="plain")
    for bad in ({"client_id": "intruder"}, {"redirect_uri": "http://127.0.0.1:9999/cb"}):
        verifier = pkce.make_code_verifier()
        code = server.authorize(client_id="app", redirect_uri=redirect, code_challenge=pkce.s256_challenge(verifier))
        request = {"code": code, "client_id": "app", "redirect_uri": redirect, "code_verifier": verifier, **bad}
        raises(PermissionError, server.token, **request)
    verifier = pkce.make_code_verifier()
    code = server.authorize(client_id="app", redirect_uri=redirect, code_challenge=pkce.s256_challenge(verifier))
    clock[0] += server.CODE_TTL + 1
    raises(PermissionError, server.token, code=code, client_id="app", redirect_uri=redirect, code_verifier=verifier)
    raises(PermissionError, server.token, code="never-issued", client_id="app", redirect_uri=redirect,
           code_verifier=verifier)


# ---------------------------------------------------------------- LSM building blocks

def test_lsm_bloom_filter():
    bloom = tiny_lsm.BloomFilter.for_capacity(1000, 0.01)
    assert (bloom.num_bits, bloom.num_hashes) == (9586, 7)
    members = [f"member-{i}" for i in range(1000)]
    for key in members:
        bloom.add(key)
    assert all(bloom.might_contain(key) for key in members)               # no false negatives, ever
    false_positives = sum(bloom.might_contain(f"absent-{i}") for i in range(20000))
    assert false_positives / 20000 < 0.02, false_positives
    copy = tiny_lsm.BloomFilter(bloom.num_bits, bloom.num_hashes, bytes(bloom.bits))
    assert all(copy.might_contain(key) for key in members)


def test_lsm_wal_records():
    records = [(1, "a", "x"), (2, "b\nnewline", "y\n"), (3, "a", None), (4, "ключ", "значение")]
    data = b"".join(tiny_lsm.encode_record(*r) for r in records)
    assert data.count(b"\n") == 4
    assert tiny_lsm.decode_records(data) == (records, len(data))
    cut = len(data) - 5                                                   # a torn final write
    assert tiny_lsm.decode_records(data[:cut]) == (records[:3], data.rfind(b"\n", 0, cut) + 1)
    lines = data.split(b"\n")
    lines[1] = lines[1].replace(b'"y', b'"z')                             # bit rot in record 2
    damaged = b"\n".join(lines)
    got, valid = tiny_lsm.decode_records(damaged)
    assert got == records[:1] and valid == len(lines[0]) + 1
    assert tiny_lsm.decode_records(b"") == ([], 0)
    assert tiny_lsm.decode_records(b"zzzzzzzz [1]\n") == ([], 0)


def test_lsm_merge_newest():
    newer = [("a", 9, "A2"), ("c", 8, None), ("d", 7, "D")]
    older = [("a", 1, "A1"), ("b", 2, "B"), ("c", 3, "C")]
    assert list(tiny_lsm.merge_newest([older, newer])) == [
        ("a", 9, "A2"), ("b", 2, "B"), ("c", 8, None), ("d", 7, "D")]
    assert list(tiny_lsm.merge_newest([newer, older], can_drop=lambda key, seq: True)) == [
        ("a", 9, "A2"), ("b", 2, "B"), ("d", 7, "D")]
    assert list(tiny_lsm.merge_newest([])) == []


def test_lsm_size_tiered_buckets():
    sizes = [100, 1000, 110, 95, 900, 5000, 1100, 105]
    buckets = tiny_lsm.size_tiered_buckets(sizes, small=50)
    assert sorted(map(sorted, buckets)) == [[0, 2, 3, 7], [1, 4, 6], [5]]
    assert tiny_lsm.size_tiered_buckets([10, 20, 3000], small=100) == [[0, 1], [2]]


# ---------------------------------------------------------------- LSM store

def check_invariants(store):
    for table in store.tables():
        entries = table.scan()
        keys = [e[0] for e in entries]
        assert keys == sorted(set(keys)) and table.count == len(entries)
        assert (table.min_key, table.max_key) == (keys[0], keys[-1])
        assert all(table.bloom.might_contain(k) for k in keys)
        assert (table.min_seq, table.max_seq) == (min(e[1] for e in entries), max(e[1] for e in entries))
    if store.strategy == "leveled":
        assert len(store.levels[0]) < store.l0_trigger
        for level in store.levels[1:]:
            assert all(a.max_key < b.min_key for a, b in zip(level, level[1:])), "levels >= 1 must not overlap"
    on_disk = {name for name in os.listdir(store.dir) if name.endswith(".sst")}
    assert on_disk == {t.name for t in store.tables()}
    assert not [name for name in os.listdir(store.dir) if name.endswith(".tmp")]


def test_lsm_basic_operations_and_reopen():
    for strategy in ("leveled", "tiered"):
        with tempfile.TemporaryDirectory() as d:
            with tiny_lsm.LSMStore(d, strategy=strategy, memtable_bytes=256) as store:
                for i in range(200):
                    store.put(f"k{i:03d}", f"v{i}")
                store.delete("k050")
                store.put("k007", "seven")
                store.put("empty", "")
                assert store.get("k007") == "seven" and store.get("k050") is None
                assert store.get("empty") == "" and store.get("missing", "dflt") == "dflt"
                assert store.scan("k010", "k014") == [(f"k{i:03d}", f"v{i}") for i in range(10, 14)]
                assert store.stats["flushes"] > 5
                check_invariants(store)
            with tiny_lsm.LSMStore(d, strategy=strategy, memtable_bytes=256) as store:
                assert store.get("k007") == "seven" and store.get("k050") is None and store.get("k199") == "v199"
                assert len(store.scan()) == 200
                raises(TypeError, store.put, "k", None)
                raises(TypeError, store.put, 5, "v")
            raises(ValueError, tiny_lsm.LSMStore, d, strategy="leveled" if strategy == "tiered" else "tiered")


def run_random_workload(strategy, seed, operations=2500, sync=False):
    rng = random.Random(seed)
    model = {}
    keys = [f"user:{i:03d}" for i in range(150)] + ["", "user:", "zzé", "a\nb"]
    d = tempfile.mkdtemp()
    options = {"strategy": strategy, "memtable_bytes": rng.choice([300, 600, 1200]), "sync": sync,
               "l0_trigger": rng.choice([2, 4]), "fanout": rng.choice([3, 10]), "tier_min": rng.choice([3, 4])}
    store = tiny_lsm.LSMStore(d, **options)
    try:
        for step in range(operations):
            r = rng.random()
            key = rng.choice(keys)
            if r < 0.55:
                value = "v" * rng.randrange(0, 40) + str(step)
                store.put(key, value)
                model[key] = value
            elif r < 0.75:
                store.delete(key)
                model.pop(key, None)
            elif r < 0.90:
                assert store.get(key) == model.get(key), (strategy, seed, step, key)
            elif r < 0.94:
                lo, hi = sorted(rng.sample(keys, 2))
                expected = sorted((k, v) for k, v in model.items() if lo <= k < hi)
                assert store.scan(lo, hi) == expected, (strategy, seed, step)
            elif r < 0.96:
                store.flush()
            elif r < 0.975:
                store.compact_all()
                assert all(v is not None for t in store.tables() for _, _, v in t.scan())
            else:
                if rng.random() < 0.5:
                    store.close()                          # clean shutdown
                else:
                    store._wal.close()                     # crash: abandon the store without any cleanup
                store = tiny_lsm.LSMStore(d, **options)
            if step % 250 == 0:
                check_invariants(store)
        assert store.scan() == sorted(model.items())
        store.compact_all()
        assert store.scan() == sorted(model.items())
        check_invariants(store)
        return store.stats
    finally:
        store.close()
        shutil.rmtree(d)


def test_lsm_randomized_against_dict():
    for strategy in ("leveled", "tiered"):
        for seed in range(4):
            stats = run_random_workload(strategy, seed)
            assert stats["compactions"] > 0, (strategy, seed)
    run_random_workload("leveled", 99, operations=300, sync=True)


def test_lsm_torn_and_corrupt_wal():
    with tempfile.TemporaryDirectory() as d:
        store = tiny_lsm.LSMStore(d, memtable_bytes=10 ** 6)
        for i in range(10):
            store.put(f"k{i}", f"v{i}")
        store._wal.close()                                 # crash
        wal = os.path.join(d, "wal.log")
        intact = os.path.getsize(wal)
        with open(wal, "ab") as f:
            f.write(b"0badc0de [11,\"k10\",\"v1")             # a torn last write
        store = tiny_lsm.LSMStore(d, memtable_bytes=10 ** 6)
        assert os.path.getsize(wal) == intact               # the torn tail was cut off
        assert store.scan() == [(f"k{i}", f"v{i}") for i in range(10)]
        store.put("k10", "after-recovery")
        store._wal.close()
        with open(wal, "r+b") as f:                         # corrupt record 6 of 11
            data = f.read()
            start = sum(len(line) + 1 for line in data.split(b"\n")[:5])
            f.seek(start + 12)
            f.write(b"X")
        store = tiny_lsm.LSMStore(d, memtable_bytes=10 ** 6)
        assert store.scan() == [(f"k{i}", f"v{i}") for i in range(5)]   # everything after it is dropped
        store.close()


def test_lsm_crash_between_manifest_and_wal_reset():
    with tempfile.TemporaryDirectory() as d:
        store = tiny_lsm.LSMStore(d, memtable_bytes=10 ** 6)
        for i in range(20):
            store.put(f"k{i:02d}", f"v{i}")
        store.delete("k03")

        def crash():
            raise RuntimeError("power cut")
        store._reset_wal = crash
        raises(RuntimeError, store.flush)                   # table written and in the MANIFEST, WAL intact
        store._wal.close()
        store = tiny_lsm.LSMStore(d, memtable_bytes=10 ** 6)
        assert len(store.tables()) == 1 and len(store.memtable) == 20   # the WAL replays the same records
        expected = [(f"k{i:02d}", f"v{i}") for i in range(20) if i != 3]
        assert store.scan() == expected
        store.flush()
        store.compact_all()
        assert store.scan() == expected
        check_invariants(store)
        store.close()


def test_lsm_crash_during_compaction():
    for strategy in ("leveled", "tiered"):
        with tempfile.TemporaryDirectory() as d:
            options = {"strategy": strategy, "memtable_bytes": 200, "l0_trigger": 3, "tier_min": 3}
            store = tiny_lsm.LSMStore(d, **options)
            model = {}
            for i in range(30):
                store.put(f"k{i % 12:02d}", f"v{i}")
                model[f"k{i % 12:02d}"] = f"v{i}"
            original = store._save_manifest

            def failing_save():                             # flushes save normally; a compaction crashes
                if any(frame.function == "_compact" for frame in inspect.stack()):   # after writing its
                    raise RuntimeError("crash")             # outputs, before switching the MANIFEST
                original()
            store._save_manifest = failing_save
            try:
                for i in range(30, 200):
                    model[f"k{i % 12:02d}"] = f"v{i}"           # the WAL append comes first, so even
                    store.put(f"k{i % 12:02d}", f"v{i}")        # the put that crashes is durable
            except RuntimeError:
                pass
            else:
                raise AssertionError("no compaction happened")
            store._wal.close()
            files_before = set(os.listdir(d))
            store = tiny_lsm.LSMStore(d, **options)
            assert set(os.listdir(d)) < files_before        # the half-finished outputs were deleted
            assert store.scan() == sorted(model.items())
            check_invariants(store)
            store.close()


def test_lsm_old_files_cannot_resurrect_deleted_keys():
    with tempfile.TemporaryDirectory() as d:
        store = tiny_lsm.LSMStore(d, strategy="tiered", memtable_bytes=200, tier_min=100)
        for i in range(40):
            store.put(f"k{i:02d}", "old")
        store.flush()
        snapshot = {t.name: open(t.path, "rb").read() for t in store.tables()}
        for i in range(40):
            store.delete(f"k{i:02d}")
        store.compact_all()
        assert store.scan() == [] and store.tables() == []   # data and tombstones are all gone
        store.close()
        for name, data in snapshot.items():                 # a crash left an old input file behind
            with open(os.path.join(d, name), "wb") as f:
                f.write(data)
        store = tiny_lsm.LSMStore(d, strategy="tiered", memtable_bytes=200, tier_min=100)
        assert store.scan() == [] and store.get("k01") is None
        assert not [n for n in os.listdir(d) if n.endswith(".sst")]
        store.close()


def test_lsm_tombstone_kept_while_older_data_exists():
    with tempfile.TemporaryDirectory() as d:
        store = tiny_lsm.LSMStore(d, strategy="tiered", memtable_bytes=10 ** 6, tier_min=100)
        for i in range(100):
            store.put(f"k{i:03d}", "x" * 20)
        store.flush()                                       # big old table holds k042
        store.delete("k042")
        store.flush()
        store.put("k500", "y")
        store.flush()
        small = [t for t in store.tables() if t.count < 10]
        assert len(small) == 2
        store._compact(small, 0, None)                      # merge only the two small, newer tables
        assert store.get("k042") is None                    # the tombstone survived: it still shadows
        assert any(k == "k042" and v is None for t in store.tables() for k, _, v in t.scan())
        store.compact_all()                                 # now nothing older exists outside the merge
        assert store.get("k042") is None
        assert not any(k == "k042" for t in store.tables() for k, _, _ in t.scan())
        store.close()


def test_lsm_bloom_filters_skip_reads_for_missing_keys():
    with tempfile.TemporaryDirectory() as d:
        store = tiny_lsm.LSMStore(d, memtable_bytes=400)
        for i in range(0, 1000, 2):
            store.put(f"key{i:04d}", "v")                   # even keys only
        store.flush()
        before = dict(store.stats)
        for i in range(1, 1000, 2):                         # odd keys: inside the tables' key ranges
            assert store.get(f"key{i:04d}") is None
        probed = store.stats["tables_probed"] - before["tables_probed"]
        reads = store.stats["block_reads"] - before["block_reads"]
        assert probed > 0 and reads <= 0.05 * probed, (probed, reads)
        report = store.report()
        assert report["space_amp"] >= 1.0 and report["write_amp"] >= 1.0
        store.close()


# ---------------------------------------------------------------- TLS and mTLS over localhost

def test_mtls_localhost_handshakes():
    import mtls_demo                                        # skips itself without the openssl CLI
    assert mtls_demo.main() == 0


def main(pattern=""):
    tests = [(name, fn) for name, fn in globals().items() if name.startswith("test_") and pattern in name]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok    {name}")
        except Exception:
            failures += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"{len(tests) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
