# Computer-science essentials lab

Small, tested implementations of the mechanisms chapter 49b explains: signing and verifying JSON Web Tokens, PKCE for the OAuth authorization code flow, a log-structured merge-tree (LSM) key-value store, and TLS with mutual authentication over localhost. They exist to make the mechanisms concrete and testable; production systems use vetted libraries (PyJWT or Authlib for tokens, your identity provider's SDK for OAuth, `cryptography` for primitives, RocksDB or the engine inside your database for storage).

Standard library only, Python 3.10 or newer. `mtls_demo.py` also needs the `openssl` command-line tool and skips itself without it.

```bash
cd labs/cs-essentials
python3 -B test_cs_essentials.py        # every test, a few seconds
python3 -B test_cs_essentials.py lsm    # only the tests whose name contains "lsm"
python3 -B tiny_lsm.py                  # a workload comparing leveled and size-tiered compaction
python3 -B mtls_demo.py                 # four localhost handshakes with a throwaway private CA
python3 -B check_chapter_sync.py        # the code printed in chapter 49b matches these files
```

## Files

| File | What it holds |
|---|---|
| `jwt_hs256.py` | `sign`, `verify` and `issue` for HS256 tokens. The verifier fixes the algorithm (rejecting `none`, other algorithms and public keys used as HMAC secrets), compares signatures in constant time, decodes base64url strictly, rejects duplicate JSON members and non-finite numbers, checks `typ`, `crit`, `exp`, `nbf`, `iat`, `iss` and `aud` with a leeway, selects rotated keys by `kid`, and accepts a revocation hook |
| `pkce.py` | `make_code_verifier`, `s256_challenge` and `verify_code_verifier` (RFC 7636), `authorization_url`, and `AuthorizationServer`, an in-memory authorization server that enforces exact redirect URIs, single-use codes bound to the client, a 60-second code lifetime and S256 |
| `tiny_lsm.py` | `LSMStore`: a write-ahead log with a CRC per record, a memtable, immutable SSTables with a sparse index and a Bloom filter, sequence numbers, tombstones, leveled or size-tiered compaction (with trivial moves), range scans, an atomically replaced MANIFEST and crash recovery; plus standalone pieces: `BloomFilter`, `encode_record`, `decode_records` and `merge_newest` (printed in the chapter) and `size_tiered_buckets` |
| `mtls_demo.py` | Creates a root CA, a server certificate and a client certificate with a SPIFFE-style URI SAN in a temporary directory, then checks server-only TLS, mTLS, mTLS without a client certificate and a hostname mismatch |
| `test_cs_essentials.py` | Plain-assert tests: JWT tampering, `alg` substitution, algorithm confusion, expiry and leeway, audience, issuer, key rotation and strict parsing; the RFC 7636 Appendix B vector and an interception attack against the toy authorization server; Bloom filter false-positive rates, torn and corrupt WAL records, randomized operations on `LSMStore` compared with a dict (including restarts after simulated crashes), crashes between a flush and the WAL reset and in the middle of a compaction, and a check that leftover files cannot resurrect deleted keys |
| `check_chapter_sync.py` | Fails if a lab function or class printed in chapter 49b differs from the tested version here |

## Exercises

1. Add a `max_lifetime` option to `jwt_hs256.verify` that rejects tokens whose `exp - iat` exceeds it, with tests for a token minted with a one-year lifetime.
2. Add `ES256` verification behind the same interface using the `cryptography` package, keeping the rule that the verifier, not the token, chooses the algorithm.
3. Give `LSMStore` snapshots: a read that pins a sequence number and ignores newer versions. Which compactions must now keep older versions?
4. Replace the memtable dict, which is sorted on every flush and scan, with a skip list, and measure `scan` on a memtable of 100,000 keys.
5. Add a block cache to `SSTable.find` and report the hit rate from `tiny_lsm.py` for a skewed (Zipf) key distribution.
6. Change `mtls_demo.py` so the client certificate expires in the past and record which side reports the error, and how.
