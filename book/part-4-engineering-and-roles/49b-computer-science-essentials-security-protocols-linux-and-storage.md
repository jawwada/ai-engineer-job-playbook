# 49b. Computer-science essentials: encryption, sessions, JWT, OAuth 2.0 and OIDC, TLS and certificates, Linux processes and pipes, and LSM trees

> **What you need to be able to say:** which cryptographic primitive gives which guarantee, and why you never build one yourself; how a server-side session, a JWT and an OAuth access token differ and how each is validated; the authorization code flow with PKCE step by step and what OpenID Connect adds; what an enterprise customer's SSO and SCIM setup needs from you, and how an MCP server authorizes its clients; what a certificate proves, how TLS 1.3 derives its keys with forward secrecy, and what mutual TLS adds; how Linux files, processes, descriptors, signals and pipelines behave when something goes wrong; and why an LSM tree trades read and space amplification for write throughput.

## 49b.1 Why these topics come up for AI engineers and forward-deployed engineers

The model is the new part of an AI system; most production incidents happen in the old parts around it. A forward-deployed engineer meets them in the first week at a customer: the identity team wants single sign-on with SCIM deprovisioning; the security review asks where the agent's Jira connector keeps its refresh tokens and how a remote MCP server checks tokens; a partner API demands client certificates; a model server takes ten seconds to stop and loses its last log lines; and the vector database's p99 latency jumps whenever it compacts. Interviews for AI engineer and FDE roles probe these fundamentals because they predict whether you can be trusted alone with a customer's systems.

The chapter follows the Computer Science topic list of labuladong's algorithm site (https://labuladong.online/en/algo/home/; the articles now live under `/en/fullstack/`), leaving out only its opening introduction to frontend development, and extends each topic with the standards, failure modes and tested code an AI or forward-deployed engineer needs; the explanations, examples and code are this book's own. Modern encryption maps to 49b.2; sessions and cookies to 49b.3; JWT to 49b.4; authentication versus authorization to 49b.5; OAuth 2.0 to 49b.6; OIDC and PKCE to 49b.7; single sign-on to 49b.8; certificates and CAs to 49b.9; TLS key exchange to 49b.10; mutual TLS to 49b.11; the Linux file system to 49b.12; processes, threads and file descriptors to 49b.13; pipeline pitfalls and shell tips to 49b.14; and LSM trees to 49b.15. Chapter 30 covers agent identity and authorization at the data layer, chapter 20b covers MCP, and 49.6 lists the security basics; this chapter goes underneath them.

The lab in `labs/cs-essentials/` holds the longer code: a JWT verifier, PKCE with a toy authorization server that the tests attack, a small LSM key-value store tested against a Python dict through simulated crashes, and a localhost mutual-TLS demonstration. Every Python block below runs as printed (standard library only, Python 3.10 or newer), and blocks that show lab code are copied verbatim from the tested files.

```bash
cd labs/cs-essentials
python3 -B test_cs_essentials.py     # JWT, PKCE, LSM and mTLS tests, a few seconds
python3 -B tiny_lsm.py               # leveled versus size-tiered compaction on one workload
python3 -B mtls_demo.py              # TLS and mTLS over localhost with a throwaway private CA
```

## 49b.2 Modern encryption primer

### 49b.2.1 Three guarantees, and the primitive for each

Cryptography sells three guarantees: **confidentiality** (only key holders can read), **integrity** (any change is detected) and **authenticity** (you know who produced the data; when a third party can check it too, that is non-repudiation). Each primitive gives a specific subset, and most security bugs come from assuming it gives more.

| Primitive | Gives | Does not give |
|---|---|---|
| Hash: SHA-256, SHA-3 | a fingerprint that detects accidental change | authenticity: anyone can rehash altered data |
| MAC: HMAC-SHA256 | integrity and authenticity between holders of a shared key | non-repudiation, confidentiality |
| AEAD: AES-GCM, ChaCha20-Poly1305 | confidentiality, integrity and authenticity of data and associated data | safety when a nonce repeats |
| Password hash: Argon2id, scrypt, bcrypt, PBKDF2 | slow, salted checking of low-entropy secrets | anything useful for random keys (use HKDF) |
| Key agreement: X25519, ECDHE, ML-KEM | a shared secret over a public channel | knowing who is on the other end |
| Signature: Ed25519, ECDSA, RSA-PSS, ML-DSA | integrity and authenticity anyone can check | confidentiality |

Only the key is secret, never the algorithm (Kerckhoffs's principle), and you never design a primitive or protocol yourself: production Python uses `cryptography` (pyca), PyJWT or Authlib for tokens, `argon2-cffi` for Argon2id, and the platform's TLS stack. The toy code below only makes mechanisms visible, and says so.

### 49b.2.2 Hash functions and MACs

A cryptographic hash maps any input to a short digest (32 bytes for SHA-256) so that finding an input for a given digest, or two colliding inputs, is infeasible; a generic collision search on an n-bit digest needs about 2^(n/2) attempts (the birthday bound), so SHA-256 gives 128-bit collision resistance, while MD5 and SHA-1 are broken (a public SHA-1 collision appeared in 2017). A hash authenticates nothing: whoever alters the data can rehash it. A MAC mixes in a key — but not as `sha256(key + message)`, because from that digest an attacker computes a valid digest of `key + message + padding + suffix` (length extension). HMAC (RFC 2104) hashes twice with two derived keys and has no such weakness. Webhook signing is the everyday case; binding a timestamp makes captured requests useless later:

```python
import hashlib
import hmac
import secrets

a = hashlib.sha256(b"transfer $100 to account 42").digest()
b = hashlib.sha256(b"transfer $900 to account 42").digest()
assert sum(bin(x ^ y).count("1") for x, y in zip(a, b)) == 126     # about half of 256 bits flip


def sign_webhook(secret: bytes, body: bytes, timestamp: int) -> str:
    return hmac.new(secret, str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()


def verify_webhook(secret: bytes, body: bytes, timestamp: int, signature: str, now: float) -> bool:
    if abs(now - timestamp) > 300:                           # stale or replayed
        return False
    return hmac.compare_digest(sign_webhook(secret, body, timestamp), signature)   # constant time


secret, body = secrets.token_bytes(32), b'{"event": "ticket.created", "id": 812}'
signature = sign_webhook(secret, body, 1_790_000_000)
assert verify_webhook(secret, body, 1_790_000_000, signature, now=1_790_000_030)
assert not verify_webhook(secret, body.replace(b"812", b"813"), 1_790_000_000, signature, now=1_790_000_030)
assert not verify_webhook(secret, body, 1_790_000_000, signature, now=1_790_003_600)
```

`==` on bytes stops at the first difference, so an attacker who can time many attempts learns a MAC byte by byte; `hmac.compare_digest` does not. Verify over the exact bytes received, before parsing: re-serialized JSON rarely matches.

### 49b.2.3 Authenticated encryption and nonces

AES is a block cipher (128-bit blocks; 128-, 192- or 256-bit keys). ECB mode leaks patterns and CBC without a MAC allows padding-oracle attacks, so modern code uses **authenticated encryption with associated data** (AEAD): AES-GCM, or ChaCha20-Poly1305 (RFC 8439) without AES hardware. Both output ciphertext plus a 16-byte tag over the ciphertext and optional associated data — authenticated but unencrypted bytes such as a tenant id, so a ciphertext cannot be moved to another tenant's row — and decryption releases nothing if the tag fails. Python has no AEAD in the standard library; `AESGCM(key).encrypt(nonce, data, associated_data)` from `cryptography` is the usual call.

Both take a 96-bit **nonce** that must never repeat under one key: a repeat makes the keystreams equal, so the XOR of two ciphertexts is the XOR of their plaintexts, and with GCM it also exposes the authentication key. NIST SP 800-38D limits a key to 2^32 encryptions with random nonces; use counters when one writer owns the key, XChaCha20-Poly1305 (192-bit nonces) for random ones, or AES-GCM-SIV (RFC 8452), where a repeated nonce reveals only that the same message was encrypted twice. At scale, use **envelope encryption**: each object gets its own data key, wrapped by a key-encryption key that never leaves a KMS or HSM, so rotation rewraps small keys, and a customer who disables their managed key (30.6) cuts off access.

### 49b.2.4 Passwords

Passwords carry little entropy, so a fast hash lets a thief test billions of guesses per second on GPUs. Password hashing adds a random per-password **salt**, which defeats precomputed tables, and a deliberately **expensive**, ideally memory-hard function; a **pepper** kept in a vault helps when only the database leaks. OWASP's Password Storage Cheat Sheet, checked in October 2026:

| Algorithm | Parameters OWASP lists | Notes |
|---|---|---|
| Argon2id (first choice) | m = 46 MiB, t = 1, p = 1, or equivalents down to 7 MiB with t = 5 (19 MiB with t = 2 is common) | memory-hard; `argon2-cffi` |
| scrypt | N = 2^17 (128 MiB), r = 8, p = 1, or equivalents down to 8 MiB with p = 10 | memory-hard; `hashlib.scrypt` |
| bcrypt (legacy) | work factor 10 or more | reads at most 72 bytes |
| PBKDF2 (when FIPS-140 is required) | 600,000 iterations with HMAC-SHA256, 220,000 with HMAC-SHA512 | `hashlib.pbkdf2_hmac` |

NIST SP 800-63B-4 (final, 31 July 2025) sets the policy: single-factor passwords of at least 15 characters (8 when one factor of several), accept at least 64, no composition rules or periodic changes, a forced change on evidence of compromise, and a blocklist of common and breached passwords. Store the parameters with each hash so you can raise them and rehash at the next login:

```python
import base64
import hashlib
import hmac
import secrets

N, R, P, MAXMEM = 2 ** 17, 8, 1, 256 * 1024 * 1024        # OWASP's first scrypt option: 128 MiB


def hash_password(password: str, n: int = N) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=n, r=R, p=P, maxmem=MAXMEM, dklen=32)
    b64 = lambda raw: base64.b64encode(raw).decode()
    return f"$scrypt$ln={n.bit_length() - 1},r={R},p={P}${b64(salt)}${b64(digest)}"


def check_password(password: str, stored: str) -> bool:
    _, _, params, salt, digest = stored.split("$")
    ln, r, p = (int(item.split("=")[1]) for item in params.split(","))
    candidate = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=2 ** ln, r=r, p=p,
                               maxmem=MAXMEM, dklen=32)
    return hmac.compare_digest(candidate, base64.b64decode(digest))


stored = hash_password("correct horse battery staple")
assert stored.startswith("$scrypt$ln=17,r=8,p=1$") and check_password("correct horse battery staple", stored)
assert not check_password("correct horse battery stapler", stored)
assert hash_password("same") != hash_password("same")              # different salts
legacy = hash_password("old user", n=2 ** 14)                       # weaker parameters from years ago
assert check_password("old user", legacy) and "ln=14" in legacy     # verify, then rehash with N
```

Each call takes about half a second and 128 MiB here, which is the point; also rate-limit login attempts.

### 49b.2.5 Public-key cryptography: RSA, elliptic curves and signatures

RSA rests on a trapdoor: multiplying two large primes is easy, factoring the product is not. The public key is n = p·q with an exponent e; the private exponent d satisfies e·d ≡ 1 (mod (p − 1)(q − 1)); encryption is c = m^e mod n, decryption c^d mod n, and a signature applies d to a hash that anyone checks with e. Textbook RSA is deterministic and malleable, so real RSA uses OAEP padding for encryption and PSS (or PKCS#1 v1.5) for signatures; PKCS#1 v1.5 *encryption* is legacy because padding oracles recover plaintexts. NIST SP 800-57 rates RSA-2048 at 112 bits of security and RSA-3072 at 128. Elliptic curves reach 128 bits with 256-bit keys: X25519 (RFC 7748) for key agreement, Ed25519 (RFC 8032) for signatures, ECDSA on P-256 where older clients or compliance profiles require it (FIPS 186-5 has approved Ed25519 since 2023). ECDSA needs a fresh secret nonce per signature — two signatures sharing one reveal the private key — which deterministic nonces (RFC 6979) prevent and Ed25519 avoids by design.

```python
# TOY textbook RSA with small primes: insecure in every way (tiny primes, no padding, malleable).
# Never use it; production code uses the cryptography package, or X25519 and Ed25519.
import hashlib
from math import isqrt

p, q, e = 1_000_003, 1_000_033, 65_537                 # real primes have 1,024 bits or more
n = p * q
d = pow(e, -1, (p - 1) * (q - 1))                      # e * d ≡ 1 (mod (p-1)(q-1))
m = 424_242
c = pow(m, e, n)                                       # encrypt with the public key (n, e)
assert pow(c, d, n) == m                               # decrypt with the private key d
h = int.from_bytes(hashlib.sha256(b"deploy model v7").digest(), "big") % n
assert pow(pow(h, d, n), e, n) == h                    # sign with d, verify with e
assert pow(c * pow(2, e, n) % n, d, n) == 2 * m        # malleable: a ciphertext of 2m without the key
factor = next(k for k in range(3, isqrt(n) + 1, 2) if n % k == 0)   # a 40-bit n falls in milliseconds
assert pow(e, -1, (factor - 1) * (n // factor - 1)) == d
```

### 49b.2.6 Key exchange and forward secrecy

In Diffie–Hellman each side keeps a random exponent secret and sends g raised to it modulo a public prime; each then raises the value it received to its own exponent, and both land on g^(ab). Someone watching the wire holds g^a and g^b, and the best known way to get g^(ab) from them is a discrete logarithm, infeasible in a large group (the toy below solves one in a 16-bit group). With fresh (ephemeral) exponents per connection, erased afterwards, stealing a server's long-term key later does not decrypt recorded sessions: **forward secrecy**, which TLS 1.2's RSA key transport lacked and TLS 1.3 requires. Diffie–Hellman alone does not know who is at the other end, so a man in the middle can run one exchange with each side; TLS stops this by having the server sign the handshake (49b.10.3).

```python
# TOY Diffie-Hellman with a 31-bit prime: never use it. Real systems use X25519 (49b.10).
import secrets

p, g = 2 ** 31 - 1, 7                                  # a Mersenne prime and a generator
a, b = secrets.randbelow(p - 3) + 2, secrets.randbelow(p - 3) + 2
A, B = pow(g, a, p), pow(g, b, p)                      # sent in the clear
assert pow(B, a, p) == pow(A, b, p)                    # one shared secret

mallory = secrets.randbelow(p - 3) + 2                 # a man in the middle swaps in her value
M = pow(g, mallory, p)
assert pow(M, a, p) == pow(A, mallory, p) and pow(M, b, p) == pow(B, mallory, p)

small_p, small_g, secret = 65_537, 3, 40_000            # a 16-bit group: brute force in milliseconds
public, x, value = pow(small_g, secret, small_p), 0, 1
while value != public:
    x, value = x + 1, value * small_g % small_p
assert x == secret
```

### 49b.2.7 Post-quantum cryptography, as of October 2026

A large fault-tolerant quantum computer running Shor's algorithm would break RSA, finite-field Diffie–Hellman and elliptic curves; Grover's algorithm only square-roots brute force, so AES-256 and SHA-256 remain comfortable. Recorded traffic could be decrypted later ("harvest now, decrypt later"), so key exchange migrates first and signatures follow.

- **Standards.** FIPS 203 (ML-KEM), FIPS 204 (ML-DSA) and FIPS 205 (SLH-DSA, hash-based) were published on 13 August 2024, and NIST selected HQC as a backup KEM on 11 March 2025; FN-DSA (Falcon) is to follow as FIPS 206, which NIST had not finalized as of October 2026.
- **Hybrid TLS.** RFC 10024 (August 2026) defines X25519MLKEM768 (code point 0x11EC, the only one of its three groups marked Recommended), SecP256r1MLKEM768 and SecP384r1MLKEM1024; a hybrid stays safe if either component holds.
- **Deployment.** Chrome moved from a Kyber draft to ML-KEM in version 131; OpenSSL 3.5 (April 2025) and Go 1.24 offer X25519MLKEM768 by default; iOS 26 and macOS Tahoe 26 advertise hybrid post-quantum key exchange automatically; Cloudflare's 2025 review counted 52 percent of human web traffic using post-quantum encryption.
- **Costs.** An ML-KEM-768 encapsulation key is 1,184 bytes, so a hybrid client key share is 1,216 bytes against 32 for X25519 and ClientHellos no longer fit one packet; ML-DSA-44 signatures are 2,420 bytes, one reason post-quantum web certificates are still being worked out.

**Interview line:** *"Key exchange is moving to hybrid ML-KEM now because recorded traffic can be decrypted later; signatures can follow. My part is an inventory of where we depend on RSA and elliptic curves, TLS terminators that already negotiate X25519MLKEM768, and algorithms chosen in configuration rather than code."*

## 49b.3 Sessions and cookies

### 49b.3.1 HTTP forgets; something has to remember

Every HTTP request stands alone, so each must prove which user it belongs to. A **server-side session** gives the browser a random identifier and keeps the state in a store: revocation is instant, but every service must reach the store. A **self-contained token** (a JWT, 49b.4) carries signed claims any service can verify with the issuer's public key, but stays valid until it expires unless you add a deny-list, which is state again. Browser applications combine them: an `HttpOnly` session cookie at a backend-for-frontend, short-lived tokens behind it.

### 49b.3.2 Cookie attributes

| Attribute | Effect | Use |
|---|---|---|
| `Secure` | sent only over HTTPS | always |
| `HttpOnly` | invisible to JavaScript, so injected script cannot read it (it can still send requests that carry it) | session cookies |
| `SameSite=Lax` | not sent on cross-site POSTs, iframes or `fetch`; sent on top-level GET navigations | default for sessions |
| `SameSite=Strict` | never sent cross-site, even from a link in an email | high-value actions |
| `SameSite=None` | sent everywhere; requires `Secure` | embedded widgets, with `Partitioned` (per top-level site storage) |
| `Domain` | omitted: only the exact host; set: every subdomain receives and can overwrite it | omit |
| `Max-Age`, `Expires` | absent: deleted when the browser session ends; `Max-Age` wins if both are set | absolute session lifetime |
| `__Host-` prefix | accepted only with `Secure`, `Path=/` and no `Domain`, so a sibling subdomain cannot set or shadow it | session cookies |
| `__Secure-` prefix | accepted only with `Secure` | cookies that span subdomains |

Chrome treats a cookie without `SameSite` as `Lax` (rolled out from Chrome 80 in 2020), but not every browser does, so set it explicitly; a session cookie should read `__Host-session=...; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=28800`.

### 49b.3.3 CSRF, and what SameSite does not stop

Cross-site request forgery exploits ambient authority: a page on `evil.example` submits a form to `bank.example`, the browser attaches `bank.example`'s cookies, and the server sees an authenticated request the user never meant. `SameSite=Lax` removes most of it, with gaps: "site" means the registrable domain, so a compromised or user-content subdomain is same-site with the application; state changes on GET (`/approve?id=7`) remain forgeable through navigation; and for cookies without a `SameSite` attribute Chrome introduced a temporary exception that sent them on cross-site top-level POSTs within two minutes of being set. Keep an anti-CSRF token on state-changing requests — stored in the session, or derived from it with a server key as below — and check `Origin` or `Sec-Fetch-Site`. APIs authenticated by an `Authorization: Bearer` header are not exposed, because browsers never add it themselves; the price is a token within reach of JavaScript.

```python
import hashlib
import hmac
import secrets

SERVER_KEY = secrets.token_bytes(32)


def csrf_token(session_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    return nonce + "." + hmac.new(SERVER_KEY, f"{session_id}!{nonce}".encode(), hashlib.sha256).hexdigest()


def csrf_ok(session_id: str, token: str, headers: dict) -> bool:
    if headers.get("Sec-Fetch-Site", "same-origin") not in ("same-origin", "none"):
        return False                                   # the browser says another site sent it
    nonce, _, mac = token.partition(".")
    expected = hmac.new(SERVER_KEY, f"{session_id}!{nonce}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, expected)


token = csrf_token("session-a")
assert csrf_ok("session-a", token, {}) and not csrf_ok("session-b", token, {})
assert not csrf_ok("session-a", token[:-1] + ("0" if token[-1] != "0" else "1"), {})
assert not csrf_ok("session-a", token, {"Sec-Fetch-Site": "cross-site"})
```

### 49b.3.4 Fixation, timeouts, revocation, and what AI applications get wrong

- **Fixation.** If an attacker plants a session id before login (through a sibling subdomain's cookie) and the server keeps it after login, the attacker shares the session; issue a new id at login and at every privilege change.
- **Identifiers, timeouts, logout.** At least 128 bits from `secrets`, stored hashed; idle (about 30 minutes) and absolute (8 to 12 hours) timeouts; logout deletes the record and clears the cookie, and "log out everywhere" (after a SCIM deactivation, 49b.8.3) needs an index from user to sessions.
- **Tokens in `localStorage`.** Chat front ends often keep access tokens where any script can read them, and model output rendered as HTML is a script-injection path (30.4). Keep OAuth tokens server-side; RFC 10017, "OAuth 2.0 for Browser-Based Applications" (a Best Current Practice, August 2026), ranks the backend-for-frontend first and a pure browser client last.
- **Tokens in URLs for streaming.** `EventSource` cannot set headers, so teams put tokens in query strings, where proxies log them; use a same-site cookie or `fetch` with an `Authorization` header.
- **Browsing agents** inherit the ambient authority of the cookies they carry, so give them isolated profiles (20b.4).

## 49b.4 JSON Web Tokens

### 49b.4.1 Structure

A JSON Web Token (RFC 7519) is a set of claims in a JSON Web Signature (JWS, RFC 7515) or, rarely, a JSON Web Encryption (JWE, RFC 7516) container. The compact JWS form is three base64url segments: a header naming the algorithm and key, the claims, and a signature over the ASCII bytes `header.payload`. Base64url is an encoding, so anyone who holds a token reads its claims:

```python
import base64
import json

token = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjIwMjYtMTAifQ"
         ".eyJpc3MiOiJodHRwczovL2F1dGguZXhhbXBsZS5jb20iLCJzdWIiOiJ1c2VyLTQyIiwiYXVkIjoib3JkZXJzLWFwaSIsImlhdCI6MTc5MDAwMDAwMCwiZXhwIjoxNzkwMDAwMzAwLCJzY29wZSI6Im9yZGVyczpyZWFkIn0"
         ".rDHRVTASUqhg1EMtQX2fSeMWib8HSg2R6RtnK4Jom-k")
decode = lambda segment: json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
header_b64, payload_b64, signature_b64 = token.split(".")
header, payload = decode(header_b64), decode(payload_b64)          # no key needed to read them
assert header == {"alg": "HS256", "typ": "JWT", "kid": "2026-10"}
assert payload["sub"] == "user-42" and payload["aud"] == "orders-api" and payload["scope"] == "orders:read"
```

### 49b.4.2 Claims, header parameters and algorithms

| Name | Meaning | Check |
|---|---|---|
| `iss` | issuer | exact match with the expected issuer |
| `sub` | subject, unique within the issuer | key users by `(iss, sub)`, never by email |
| `aud` | intended recipients | must contain your service |
| `exp`, `nbf`, `iat` | expiry, not-before, issued-at (seconds since 1970) | with 30 to 60 seconds of leeway |
| `jti` | unique token id | deny-lists, replay detection, audit |
| `alg`, `kid` (header) | signature algorithm; which issuer key signed | an algorithm *you* allow; the key from the issuer's key set |
| `typ` (header) | `JWT`, or `at+jwt` for access tokens (RFC 9068) | stops one kind of token passing as another |
| `jku`, `x5u`, `jwk` (header) | a key or key URL inside the token | ignore unless pinned |

HS256 uses one shared secret, so every verifier can also mint tokens; it suits a service that issues and checks its own. Asymmetric algorithms let many services verify tokens only the identity provider can mint: RS256 (which OpenID Connect Discovery requires providers to support), PS256, ES256 and Ed25519 (RFC 9864, October 2025, deprecated the ambiguous `EdDSA` value). Providers publish public keys as a key set at the `jwks_uri` in their discovery metadata and rotate by publishing the new key before signing with it; verifiers cache the set and refetch on an unknown `kid`.

### 49b.4.3 The verification checklist

1. Parse strictly: three base64url segments without padding, JSON objects, no duplicate members.
2. Choose the algorithm yourself — an allow-list per issuer — and require the header to match; reject `none`.
3. Take the key by `kid` from the issuer's configured key set, never from the token.
4. Verify the signature in constant time before trusting the payload.
5. Check `iss` exactly, that `aud` contains you, and `exp`, `nbf` and `iat` with a small leeway.
6. Check `typ`; reject `crit` parameters you do not understand.
7. Require the claims you rely on, then authorize from scopes or roles.
8. For high-risk operations check revocation (a `jti` deny-list, or introspection, 49b.6.4); log `jti` and `sub`, never the token.

### 49b.4.4 A complete HS256 verifier

The lab's `jwt_hs256.py` implements the checklist with the standard library. In production the same behavior comes from PyJWT — `jwt.decode(token, key, algorithms=["RS256"], audience="orders-api", issuer="https://auth.example.com", leeway=30, options={"require": ["exp", "iat", "sub"]})`, with `PyJWKClient` fetching the issuer's keys — or from Authlib. Most of its checks close holes that real verifiers have had:

```python
import base64
import hashlib
import hmac
import json
import math
import re
import time

ALGORITHM = "HS256"
MIN_KEY_BYTES = 32  # RFC 7518 section 3.2: the key must be at least as long as the hash output (256 bits)
_B64URL = re.compile(r"[A-Za-z0-9_-]*")


class InvalidToken(Exception):
    """The token must be rejected. Subclasses say why; never tell the caller which check failed."""


class MalformedToken(InvalidToken):
    pass


class BadAlgorithm(InvalidToken):
    pass


class BadSignature(InvalidToken):
    pass


class ExpiredToken(InvalidToken):
    pass


class NotYetValid(InvalidToken):
    pass


class BadClaim(InvalidToken):
    pass


def b64url_encode(data: bytes) -> str:
    """Base64url without padding, as JWS compact serialization requires."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    """Strict base64url: only the URL-safe alphabet, no padding, and exactly one encoding per value."""
    if not _B64URL.fullmatch(text) or len(text) % 4 == 1:
        raise MalformedToken("segment is not base64url")
    data = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    if b64url_encode(data) != text:      # nonzero leftover bits: a second spelling of the same bytes
        raise MalformedToken("segment is not canonical base64url")
    return data


def _reject_constant(name):
    raise MalformedToken(f"{name} is not valid JSON")   # Python's json accepts NaN and Infinity


def _reject_duplicates(pairs):
    obj = {}
    for name, value in pairs:
        if name in obj:
            raise MalformedToken(f"duplicate member {name!r}")
        obj[name] = value
    return obj


def _json_object(segment: str) -> dict:
    try:
        value = json.loads(b64url_decode(segment), object_pairs_hook=_reject_duplicates,
                           parse_constant=_reject_constant)
    except ValueError as err:            # JSONDecodeError and UnicodeDecodeError are ValueErrors
        raise MalformedToken("segment is not JSON") from err
    if not isinstance(value, dict):
        raise MalformedToken("segment is not a JSON object")
    return value


def _check_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) < MIN_KEY_BYTES:
        raise ValueError(f"an HS256 key must be at least {MIN_KEY_BYTES} random bytes")
    if key.lstrip().startswith((b"-----BEGIN", b"ssh-", b"ecdsa-")):
        raise ValueError("that is a public key; using it as an HMAC secret enables algorithm confusion")


def _numeric_date(claims: dict, name: str) -> float:
    value = claims[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BadClaim(f"{name} must be a number of seconds since the epoch")
    return value


def sign(claims: dict, key: bytes, *, kid: str | None = None) -> str:
    """Return header.payload.signature, signed with HMAC-SHA256 under key."""
    _check_key(key)
    header = {"alg": ALGORITHM, "typ": "JWT"}
    if kid is not None:
        header["kid"] = kid
    segments = [b64url_encode(json.dumps(part, separators=(",", ":"), allow_nan=False).encode())
                for part in (header, claims)]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    return ".".join(segments + [b64url_encode(signature)])


def verify(token: str, keys, *, issuer: str, audience: str, now: float | None = None,
           leeway: float = 30, max_age: float | None = None, typ: str | None = "JWT",
           required=("iss", "aud", "exp", "iat", "sub"), is_revoked=None) -> dict:
    """Return the token's claims if every check passes; raise an InvalidToken subclass otherwise.

    keys is one key (bytes) or a dict {kid: key} for rotation. The algorithm is fixed by the verifier,
    never chosen by the token. is_revoked, if given, is called with the jti claim.
    """
    if not isinstance(token, str) or token.count(".") != 2:
        raise MalformedToken("expected header.payload.signature")
    header_b64, payload_b64, signature_b64 = token.split(".")
    if not all(_B64URL.fullmatch(part) for part in (header_b64, payload_b64, signature_b64)):
        raise MalformedToken("segment is not base64url")
    header = _json_object(header_b64)
    if header.get("alg") != ALGORITHM:   # rejects "none", "RS256", "hs256" and a missing alg
        raise BadAlgorithm(f"algorithm {header.get('alg')!r} is not accepted")
    if "crit" in header:
        raise MalformedToken("critical header parameters are not understood")
    if typ is not None and str(header.get("typ", "")).lower() != typ.lower():
        raise MalformedToken("unexpected token type")
    if isinstance(keys, dict):
        kid = header.get("kid")
        key = keys.get(kid) if isinstance(kid, str) else None
        if key is None:
            raise BadSignature("unknown key id")
    else:
        key = keys
    _check_key(key)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected = hmac.new(key, signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, b64url_decode(signature_b64)):
        raise BadSignature("signature does not match")

    claims = _json_object(payload_b64)   # parse the payload only after the signature checks out
    now = time.time() if now is None else now
    for name in required:
        if name not in claims:
            raise BadClaim(f"missing required claim {name!r}")
    if "exp" in claims and now >= _numeric_date(claims, "exp") + leeway:
        raise ExpiredToken("token has expired")
    if "nbf" in claims and now + leeway < _numeric_date(claims, "nbf"):
        raise NotYetValid("token is not valid yet")
    if "iat" in claims:
        issued_at = _numeric_date(claims, "iat")
        if issued_at > now + leeway:
            raise BadClaim("token was issued in the future")
        if max_age is not None and now - issued_at > max_age + leeway:
            raise ExpiredToken("token is older than max_age")
    if claims.get("iss") != issuer:
        raise BadClaim("wrong issuer")
    audiences = claims.get("aud")
    if isinstance(audiences, str):
        audiences = [audiences]
    if not isinstance(audiences, list) or audience not in audiences:
        raise BadClaim("token was not issued for this audience")
    if is_revoked is not None and is_revoked(claims.get("jti")):
        raise BadClaim("token has been revoked")
    return claims


key, now = bytes(range(32)), 1_790_000_000
claims = {"iss": "https://auth.example.com", "sub": "user-42", "aud": "orders-api",
          "iat": now, "exp": now + 300, "scope": "orders:read"}
token = sign(claims, key)
assert verify(token, key, issuer="https://auth.example.com", audience="orders-api", now=now + 10) == claims
header_b64, payload_b64, signature_b64 = token.split(".")
attacks = [  # (token, verifier options, the exception that must be raised)
    (header_b64 + "." + b64url_encode(json.dumps({**claims, "scope": "admin"}).encode()) + "." + signature_b64,
     {}, BadSignature),                                                            # edited claims
    (b64url_encode(b'{"alg":"none","typ":"JWT"}') + "." + payload_b64 + ".", {}, BadAlgorithm),
    (token, {"now": now + 331}, ExpiredToken),                                     # past exp + leeway
    (token, {"audience": "billing-api"}, BadClaim),
    (token + "=", {}, MalformedToken),                                             # padding
]
for bad, options, error in attacks:
    try:
        verify(bad, key, **{"issuer": "https://auth.example.com", "audience": "orders-api", "now": now + 10,
                            **options})
        raise AssertionError("accepted")
    except error:
        pass
```

### 49b.4.5 Attacks and pitfalls

- **`alg: none`.** RFC 7519 defines unsecured tokens; libraries that honored the header accepted unsigned tokens.
- **Algorithm confusion.** A service verifies RS256 tokens with the issuer's public key, which is public. If the header picks the algorithm, an attacker sends `"alg": "HS256"` with an HMAC keyed by the public key's bytes, and a naive verifier checks it with the same bytes. A verifier fixed to RS256 refuses that header outright. The lab's tests run the attack: it succeeds against a naive verifier and fails against `verify`, which will not take a PEM public key as an HMAC secret and, holding its real secret, finds the MAC wrong.
- **No audience check.** One identity provider serves many APIs; without `aud`, a token for a low-value service opens a high-value one.
- **Long lifetimes.** A self-contained token cannot be recalled: keep access tokens to 5 to 15 minutes with rotating refresh tokens (49b.6.3), plus introspection or a deny-list where revocation must be immediate.
- **Storage and transport.** `localStorage` is readable by any script, URLs reach logs (RFC 9700 forbids access tokens in query strings), and claims are readable, so secrets belong in opaque tokens or JWE.
- **Header parameters.** A `kid` pasted into a file path or SQL, or a `jku` or `x5u` URL the server fetches, becomes injection or server-side request forgery, as RFC 8725 already warns. Its update (draft-ietf-oauth-rfc8725bis, in the RFC Editor's queue as of October 2026) adds newer attacks, among them `alg` values in unexpected letter case that slip past blocklists (the lab compares `alg` exactly) and compressed JWE payloads that expand into memory bombs.
- **Parser differentials.** Components that disagree on duplicate JSON members or on base64 with nonzero spare bits disagree on what a token says; the lab rejects both.

**Interview line:** *"I verify a JWT with an algorithm allow-list I configure, a key chosen by `kid` from the issuer's key set, then `iss`, `aud`, `exp`, `nbf` and `typ`, and only then authorize from its scopes. Access tokens live minutes, refresh tokens rotate, and anything that must be revocable at once gets introspection or a deny-list."*

## 49b.5 Authentication versus authorization

### 49b.5.1 Two different questions

Authentication answers *who is this?*; authorization answers *may this principal do this action on this resource, now?* HTTP keeps them apart: 401 means "not authenticated" (with a `WWW-Authenticate` challenge), 403 "authenticated, and not allowed". OAuth 2.0 delegates authorization; OpenID Connect adds authentication (49b.7). For an agent they multiply: Maya authenticates to her identity provider, the agent's backend authenticates as a workload, a token authorizes part of Maya's Jira access, and each tool call is authorized again against what Maya may see (30.2, 30.3).

### 49b.5.2 Credentials, MFA and passkeys

Factors are something you know, have or are, and they resist different attacks. **One-time codes** (TOTP, RFC 6238) are an HMAC of the current 30-second time step under a secret shared at enrollment; a phishing page can relay them within the window. **Push approvals** invite "MFA fatigue", hence number matching. **Passkeys** (WebAuthn, FIDO2) are per-site key pairs: the browser lets the authenticator sign a challenge only for the site that registered the key and puts the page's real origin into the signed data, so a look-alike domain gets nothing to relay. WebAuthn Level 3 became a W3C Recommendation on 25 August 2026, and NIST SP 800-63B-4 accepts syncable passkeys at AAL2 but not AAL3, which requires non-exportable keys. TOTP is short enough to check against its RFC:

```python
import hashlib
import hmac
import struct


def totp(secret: bytes, unix_time: float, digits: int = 6, digest=hashlib.sha1, step: int = 30) -> str:
    mac = hmac.new(secret, struct.pack(">Q", int(unix_time // step)), digest).digest()
    offset = mac[-1] & 0x0F                                   # dynamic truncation (RFC 4226)
    code = int.from_bytes(mac[offset:offset + 4], "big") & 0x7FFFFFFF
    return str(code % 10 ** digits).zfill(digits)


seed = b"12345678901234567890"                                # RFC 6238 Appendix B, 8-digit codes
assert totp(seed, 59, 8) == "94287082" and totp(seed, 1111111109, 8) == "07081804"
assert totp(seed + b"123456789012", 59, 8, hashlib.sha256) == "46119246"
assert totp(seed * 3 + b"1234", 2000000000, 8, hashlib.sha512) == "38618901"
```

A verifier accepts the current step and one either side for clock skew, compares in constant time, and remembers the last step used so a code works once.

### 49b.5.3 Authorization models

| Model | Rule | Strength | Weakness | Tools |
|---|---|---|---|---|
| RBAC | users → roles → permissions | easy to audit | role explosion; no context | IAM roles, Kubernetes RBAC, IdP groups |
| ABAC | a policy over attributes of user, resource, action and context | expressive ("EU analysts read EU rows") | harder to audit | OPA (Rego), Cedar, IAM conditions |
| ReBAC | permissions follow relationships (folder viewer, group member) | fits sharing; answers "who can see this?" | a graph to query fast | Zanzibar (2019), OpenFGA, SpiceDB |

Retrieval-augmented generation needs exactly this: only chunks the user may see reach the model (30.3). A ReBAC check fits in a few lines:

```python
TUPLES = {                                               # (object, relation, subject), Zanzibar style
    ("folder:finance", "viewer", "group:finance#member"),
    ("group:finance", "member", "user:maya"),
    ("doc:q3-forecast", "parent", "folder:finance"),
    ("doc:salaries", "owner", "user:lee"),
    ("doc:handbook", "viewer", "user:*"),
}


def has(obj: str, relation: str, user: str, depth: int = 0) -> bool:
    if depth > 8:                                        # guard against cycles
        return False
    if relation == "viewer" and has(obj, "owner", user, depth + 1):
        return True                                      # owners can view
    for o, r, subject in TUPLES:
        if (o, r) == (obj, relation) and (subject in (user, "user:*") or
                                          ("#" in subject and has(*subject.split("#"), user, depth + 1))):
            return True
    parent = next((s for o, r, s in TUPLES if o == obj and r == "parent"), None)
    return relation == "viewer" and parent is not None and has(parent, "viewer", user, depth + 1)


hits = ["doc:q3-forecast", "doc:salaries", "doc:handbook"]       # what the vector search returned
assert [d for d in hits if has(d, "viewer", "user:maya")] == ["doc:q3-forecast", "doc:handbook"]
assert [d for d in hits if has(d, "viewer", "user:lee")] == ["doc:salaries", "doc:handbook"]
```

### 49b.5.4 Least privilege and delegated authority for agents

An agent acting for a user should hold the intersection of the user's rights and the task's needs; a broad service account that "decides" for the user is a confused deputy waiting for a prompt injection. OAuth token exchange (RFC 8693) turns the user's token into one whose subject is the user and whose `act` claim names the agent, restricted to one API, with narrowed scopes and a short life — the on-behalf-of pattern of 30.2. Keep the agent's workload identity (49b.11) for infrastructure and delegated tokens for user data, require step-up authentication or runtime-enforced approval for consequential actions, and audit who (the user), through what (the agent and its client), did what.

## 49b.6 OAuth 2.0

### 49b.6.1 The problem, and the four roles

Before OAuth, an application that wanted your calendar asked for your password: it got everything, kept it, could not be cut off without a password change, and broke MFA. OAuth 2.0 (RFC 6749) lets a **resource owner** (Maya) grant a **client** (the agent's backend, or an MCP client) limited, revocable access through an **authorization server** (the identity provider), which issues access tokens that a **resource server** (the Jira API, or a remote MCP server) accepts. Clients are **confidential** when they can keep a secret (a backend) and **public** when they cannot (mobile, single-page, desktop and command-line apps).

### 49b.6.2 The authorization code flow, step by step

1. The client creates a random `state`, a PKCE verifier and challenge (49b.7.3) and, for OIDC, a `nonce`, stored with the issuer it expects.
2. It sends the browser to the authorization endpoint with `response_type=code`, `client_id`, `redirect_uri`, `scope`, `state`, `code_challenge`, `code_challenge_method=S256` and, for a specific API, `resource` (RFC 8707).
3. The authorization server authenticates the user (SSO, MFA) and asks for consent.
4. It redirects to the registered `redirect_uri` with `code`, `state` and `iss` (RFC 9207).
5. The client checks `state` and `iss`, then posts the code to the token endpoint over the back channel with the verifier and, if confidential, its client authentication (a secret, a signed JWT or mTLS).
6. The server checks that the code is unused, unexpired (a minute is typical; RFC 6749 recommends at most ten) and bound to this client and redirect URI, recomputes the PKCE challenge, and returns tokens.
7. The client calls the API with `Authorization: Bearer <access token>`.

The front channel — browser URLs, history, logs, `Referer` — leaks, so it carries only a single-use code, useless without the client's credentials and verifier; tokens travel on the back channel:

```http
POST /oauth/token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic c3VwcG9ydC1hZ2VudDpleGFtcGxlLXNlY3JldA==

grant_type=authorization_code&code=Qm9vazQ5YmNvZGUtZXhhbXBsZQ&redirect_uri=https%3A%2F%2Fagent.example.com%2Fcallback&code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk

HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store

{"access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6ImF0K2p3dCJ9...", "token_type": "Bearer",
 "expires_in": 600, "refresh_token": "rt_8KQ2zj...", "scope": "tickets:read"}
```

### 49b.6.3 Other grants and refresh tokens

- **Client credentials**: no user; the client gets a token for its own access. Right for an agent's infrastructure and batch jobs, wrong for user data, because the token carries none of the user's limits.
- **Device authorization grant** (RFC 8628): a device or command-line tool shows a short user code and a URL, then polls the token endpoint (`authorization_pending`, `slow_down`) until the user approves elsewhere. Attackers send victims codes to approve, so show what is being authorized and restrict which clients may use it.
- **Refresh tokens** obtain new short-lived access tokens. RFC 9700 requires a public client's refresh tokens to be sender-constrained (49b.6.6) or **rotated**: each use returns a new one, and presenting a used one revokes the whole chain, because the server cannot tell the client from a thief holding a copy.
- **Token exchange** (RFC 8693): the on-behalf-of pattern (49b.5.4). **Retired** (49b.6.5): the implicit grant (tokens in the URL fragment) and the resource owner password grant.

### 49b.6.4 Scopes, audiences and token types

**Scopes** such as `tickets:read` are what the client requests and the user approves: per capability, few, the minimum, with more added by step-up (49b.8.5). The **audience** names the API a token is for, requested with `resource`; APIs reject tokens minted for others. An **access token** is for the API — opaque or a JWT (RFC 9068, `typ` `at+jwt`) — and says the bearer may call it with these scopes; an **ID token** is always a JWT, addressed to the client, saying who logged in (49b.7). A client that treats an access token as proof of login, or an API that accepts ID tokens, is broken. JWT access tokens validate locally and stay valid until expiry; opaque tokens are checked through introspection (RFC 7662), current at the cost of a call that APIs cache briefly. Clients revoke tokens they no longer need at the revocation endpoint (RFC 7009).

### 49b.6.5 What the Security Best Current Practice changed

RFC 9700 (January 2025, BCP 240) turns a decade of attacks into rules:

| Rule | Level |
|---|---|
| No implicit grant | SHOULD NOT |
| No resource owner password credentials grant | MUST NOT |
| PKCE for public clients; for confidential clients; support at authorization servers | MUST; RECOMMENDED; MUST |
| Exact redirect URI matching (a loopback port may vary for native apps) | MUST |
| A public client's refresh tokens are sender-constrained or rotated | MUST |
| Sender-constrained (mTLS or DPoP) and audience-restricted access tokens | SHOULD |
| No access tokens in URI query parameters; no open redirectors | MUST NOT |
| Clients that use several authorization servers defend against mix-up attacks; checking `iss` (RFC 9207) is the expected defense | REQUIRED; SHOULD |

### 49b.6.6 PAR, DPoP and mTLS-bound tokens

**Pushed authorization requests** (RFC 9126) post the authorization parameters over the back channel first, so the browser carries only a short-lived `request_uri`. **DPoP** (RFC 9449) has the client sign a small proof JWT per request (method, URL, time, a unique id, a hash of the access token) with a key pair it holds, and binds the token to that key (`cnf.jkt`), so a stolen token is useless alone — a fit for single-page apps and command-line agents. **mTLS-bound tokens** (RFC 8705) carry the client certificate's thumbprint and work only over a connection authenticated with it (49b.11).

### 49b.6.7 OAuth 2.1 status

As of October 2026 OAuth 2.1 is still an Internet-Draft: revision 16 of draft-ietf-oauth-v2-1 (3 September 2026), a working-group document whose milestone for submission to the IESG is December 2026. It folds RFC 6749, RFC 6750 and the security BCP together — PKCE for every code flow, no implicit or password grants, exact redirects, no bearer tokens in query strings, sender-constrained or one-time refresh tokens for public clients — and MCP's authorization specification already builds on revision 13.

## 49b.7 OpenID Connect and PKCE

### 49b.7.1 What OpenID Connect adds

An access token tells an API the bearer may call it; it does not tell the *client* who the user is. Treating "I received a valid access token" as login is the classic hole: an application that got a token from the same provider for its own users can present it to your login, and nothing in an opaque token says it was minted for another client. OpenID Connect (Core 1.0) adds the `openid` scope and an **ID token**: a JWT addressed to the client (`aud` = `client_id`) stating who authenticated (`iss`, `sub`), when (`auth_time`, `iat`), how (`acr`, `amr`) and in answer to which request (`nonce`). Providers also offer a `userinfo` endpoint, standard claims such as `email_verified`, and a discovery document at `/.well-known/openid-configuration` whose `issuer` must equal the URL it came from and the `iss` of its tokens. Store users by `(iss, sub)`: linking accounts by email is a takeover risk.

### 49b.7.2 Validating an ID token

After the signature checks of 49b.4.3, with keys from the provider's `jwks_uri`, a client checks that `iss` is the provider, `aud` contains its `client_id` (and `azp` is its `client_id` when there are several audiences), `exp` and `iat` are sane, `nonce` matches the one it stored — which stops replayed and injected responses — and, if it asked for `max_age`, that `auth_time` is recent enough.

### 49b.7.3 PKCE

On phones and desktops the final redirect goes to a custom URL scheme or a loopback port that another application can register or listen on first; holding the code, it could redeem it, because a public client has no secret. With PKCE (RFC 7636) the client makes a random **code verifier** per request (43 to 128 characters; 32 random bytes give 43) and sends only its **challenge**, `BASE64URL(SHA256(verifier))`, through the browser; the token request carries the verifier, and the server recomputes the challenge. An interceptor sees at most the challenge and cannot invert SHA-256. The `plain` method sends the verifier itself and protects nothing against an attacker who sees the authorization request; MCP requires `S256`.

```python
import base64
import hashlib
import hmac
import re
import secrets

_VERIFIER = re.compile(r"[A-Za-z0-9\-._~]{43,128}")   # RFC 7636 section 4.1: unreserved characters


def make_code_verifier(nbytes: int = 32) -> str:
    """A fresh high-entropy verifier: 32 random bytes give 43 base64url characters (256 bits)."""
    if not 32 <= nbytes <= 96:
        raise ValueError("use 32 to 96 random bytes, which encode to 43 to 128 characters")
    return base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).rstrip(b"=").decode("ascii")


def s256_challenge(verifier: str) -> str:
    """code_challenge = BASE64URL(SHA256(ASCII(code_verifier))), without padding."""
    if not _VERIFIER.fullmatch(verifier):
        raise ValueError("a code verifier is 43 to 128 characters from [A-Za-z0-9-._~]")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def verify_code_verifier(verifier: str, challenge: str, method: str = "S256") -> bool:
    """The authorization server's check at the token endpoint. Refuses "plain" outright."""
    if method != "S256" or not isinstance(verifier, str) or not _VERIFIER.fullmatch(verifier):
        return False
    return hmac.compare_digest(s256_challenge(verifier), challenge)


# RFC 7636 Appendix B: 32 octets, their base64url verifier, and its S256 challenge.
octets = bytes([116, 24, 223, 180, 151, 153, 224, 37, 79, 250, 96, 125, 216, 173, 187, 186,
                22, 212, 37, 77, 105, 214, 191, 240, 91, 88, 5, 88, 83, 132, 141, 121])
verifier = base64.urlsafe_b64encode(octets).rstrip(b"=").decode()
assert verifier == "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
assert s256_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
assert verify_code_verifier(verifier, "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM")
assert not verify_code_verifier(make_code_verifier(), s256_challenge(verifier))     # an interceptor
assert not verify_code_verifier(verifier, verifier, method="plain")                 # plain refused
assert len(make_code_verifier()) == 43 and len(make_code_verifier(96)) == 128
```

The lab's `pkce.AuthorizationServer` adds the server side — exact redirect URIs, single-use codes bound to the client, a 60-second lifetime — and its tests play the attacker: an intercepted code without the verifier is refused and consumed, and replaying a redeemed code revokes the tokens it produced, as RFC 6749 recommends. RFC 9700 lets PKCE double as CSRF protection once the client knows the server enforces it, and `nonce` ties an ID token to its request; `state` costs little and the MCP specification still asks for it, so keep all three.

## 49b.8 Single sign-on

### 49b.8.1 One login, many applications

With single sign-on a user authenticates once at an **identity provider** (IdP: Microsoft Entra ID, Okta, Google Workspace, Ping, Keycloak), and each application — a service provider (SP) in SAML, a relying party in OIDC — trusts the IdP's statement, giving one place for MFA, conditional access and deprovisioning. A cookie shared across `*.example.com` is no substitute: any compromised subdomain can read or overwrite it, and it cannot reach SaaS applications.

| | SAML 2.0 | OpenID Connect |
|---|---|---|
| Token and transport | signed XML assertion, auto-posted through the browser | ID token (JWT) from a back-channel token request, plus OAuth access tokens |
| Configuration | metadata XML: entity IDs, assertion consumer service (ACS) URL, certificates | discovery document and client registration |
| Where you meet it | enterprise SaaS, long-lived corporate integrations | new and mobile applications, APIs, MCP |
| Typical bugs | XML signature wrapping, unsigned assertions accepted, expired certificates | algorithm and audience checks, `state` and `nonce`, redirect URIs |

### 49b.8.2 SP-initiated and IdP-initiated login

In an **SP-initiated** login the application sends an authentication request and accepts only a response whose `InResponseTo` matches it. In an **IdP-initiated** login the user clicks a portal tile and the application receives an assertion it never asked for, bound to no browser session; accept it only when needed, with short validity and one-time assertion ids (OIDC instead sends the user to the application's login-initiation URL, which starts a normal flow). Validate SAML with a maintained library: the signature must cover the assertion you read (signature wrapping inserts an unsigned copy), and check `Audience`, `Destination`, the validity window, `InResponseTo` and one-time use.

### 49b.8.3 SCIM provisioning

SSO decides who can log in; provisioning decides which accounts exist. Just-in-time provisioning creates accounts at first login but never removes them, so a departed employee's account, API keys and sessions live on. **SCIM 2.0** (RFC 7643 schema, RFC 7644 protocol) lets the IdP manage accounts through the application's `/scim/v2/Users` and `/scim/v2/Groups` endpoints: create (POST), find (`GET /Users?filter=userName eq "maya@corp.example"`), update and deactivate (PATCH). When HR offboards someone the IdP sends:

```http
PATCH /scim/v2/Users/39d132bd-c850-474d-8115-fdefdfd9319d
Content-Type: application/scim+json

{"schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
 "Operations": [{"op": "replace", "path": "active", "value": false}]}
```

The application must then end the user's sessions, revoke tokens and disable API keys within minutes — the control auditors test. Group pushes map IdP groups to roles.

### 49b.8.4 The FDE's enterprise SSO checklist

1. Agree on OIDC or SAML and on who owns the IdP configuration at the customer.
2. Exchange metadata — SAML entity IDs, ACS URL and signing certificates (note expiry and rotation), or the OIDC issuer, client id, redirect URIs and how secrets or keys are delivered.
3. Key users on an immutable id (persistent SAML `NameID`, OIDC `sub`), not email; map email, name and groups as attributes.
4. Verify the customer's domains, enforce SSO for them, and keep one or two break-glass administrators outside SSO, on passkeys.
5. Configure SCIM with a provisioning-only token and group-to-role mappings; test deprovisioning end to end, including live sessions.
6. Test in staging — right group, no group, deactivated user, expired certificate, clock-skewed assertion — and hand over audit logs keyed to IdP ids.

### 49b.8.5 How MCP servers authorize clients

A remote MCP server is an OAuth resource server and an MCP client an OAuth client acting for the user. The authorization part of the current specification revision, 2026-07-28 (checked October 2026; 20b.7 covers the rest of that revision), requires:

1. **Discovery from a 401.** A request without a token gets `401` with `WWW-Authenticate: Bearer resource_metadata="..."` pointing to the server's protected resource metadata (RFC 9728); without the header, clients try `/.well-known/oauth-protected-resource` with the endpoint's path inserted, then at the root. The metadata's `resource` must equal the server's identifier, and `authorization_servers` names at least one server, whose RFC 8414 or OpenID Connect metadata the client fetches and rejects if its `issuer` differs from the one asked about.
2. **Registration**: pre-registered credentials when the client has them, otherwise a Client ID Metadata Document (the `client_id` is an HTTPS URL serving the client's metadata) if the authorization server advertises support; Dynamic Client Registration is deprecated, a fallback for servers that cannot read metadata documents.
3. **PKCE with S256**, refusing to proceed if the server's metadata lacks `code_challenge_methods_supported`; the `resource` parameter naming the MCP server in both requests; and the returned `iss` compared with the recorded issuer before the code is redeemed.
4. **Audience and no passthrough**: servers accept only tokens issued for them and never forward a client's token upstream.
5. **Step-up**: too few scopes gets `403` with `error="insufficient_scope"`, and the client re-authorizes with the union of old and new scopes. **stdio servers** skip all this and take credentials from their environment.

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer resource_metadata="https://mcp.tickets.example.com/.well-known/oauth-protected-resource/mcp", scope="tickets:read"

GET /.well-known/oauth-protected-resource/mcp HTTP/1.1
Host: mcp.tickets.example.com

HTTP/1.1 200 OK
Content-Type: application/json

{"resource": "https://mcp.tickets.example.com/mcp",
 "authorization_servers": ["https://login.corp.example.com"],
 "scopes_supported": ["tickets:read"]}
```

In an enterprise rollout the customer's IdP is the authorization server (or federates to the vendor's) and scopes map to IdP groups; 20b.6 adds gateways and the enterprise-managed authorization extension, and 30.2 places this in the agent's identity design.

## 49b.9 Certificates and certificate authorities

### 49b.9.1 What a certificate proves

A client must know *which* public key belongs to `mcp.tickets.example.com`, or an attacker who substitutes their own key reads everything. A certificate is a signed statement — "this key belongs to these names, for these purposes, between these dates" — from an issuer the client already trusts, which reduces trust to a few root keys shipped with operating systems and browsers.

| Field | Holds | Why it matters |
|---|---|---|
| Serial, signature algorithm | unique per issuer; how the issuer signed | revocation lists name serials |
| Issuer, subject, validity | distinguished names; `notBefore`, `notAfter` | chains link issuer to subject; expired certificates fail |
| Subject public key info | the key being vouched for | |
| Subject Alternative Name | DNS names, IP addresses, URIs | hostnames are matched here; the common name is legacy |
| Basic constraints, key usage, extended key usage | `CA:TRUE`; `keyCertSign`; `serverAuth`, `clientAuth` | only CAs sign certificates; what the key may do |
| CRL distribution points, authority information access, SCTs | revocation lists, the issuer's certificate, transparency proofs | revocation, chain completion, 49b.9.4 |

In DER, the binary encoding of ASN.1, a certificate is three elements: the to-be-signed body, the signature algorithm and the issuer's signature over the body. The toy root below (public part only, made for this book with `openssl` and an Ed25519 key) shows the raw structure and the fields Python's `ssl` module decodes, offline:

```python
import ssl

TOY_ROOT_PEM = """-----BEGIN CERTIFICATE-----
MIIBhzCCATmgAwIBAgICSh8wBQYDK2VwMDoxGTAXBgNVBAoMEFBsYXlib29rIEV4
YW1wbGUxHTAbBgNVBAMMFFBsYXlib29rIFRveSBSb290IENBMB4XDTI2MTAwMzEx
MzUzNVoXDTM2MDkzMDExMzUzNVowOjEZMBcGA1UECgwQUGxheWJvb2sgRXhhbXBs
ZTEdMBsGA1UEAwwUUGxheWJvb2sgVG95IFJvb3QgQ0EwKjAFBgMrZXADIQA5qsNQ
YEcYF/Wcl1ISxfZnhofjwbE1gSja6h9qOztoOaNjMGEwHQYDVR0OBBYEFEYmPD6K
b9gnr2+zetocr4R+BkAnMB8GA1UdIwQYMBaAFEYmPD6Kb9gnr2+zetocr4R+BkAn
MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMAUGAytlcANBALhAc3iC
ebiF8fzbY0JysgdCC95jGM+Fdxx23Rlti1o7QPPk35I8T7WRb2shs6uov0CtdGiU
020iySRBQFaN+As=
-----END CERTIFICATE-----
"""


def der_children(data: bytes, start: int = 0, end: int | None = None):
    """Yield (tag, value_start, value_end) for each DER element between start and end."""
    end = len(data) if end is None else end
    while start < end:
        tag, length = data[start], data[start + 1]
        start += 2
        if length & 0x80:                              # long form: the next (length & 0x7F) bytes
            size = length & 0x7F
            length = int.from_bytes(data[start:start + size], "big")
            start += size
        yield tag, start, start + length
        start += length


der = ssl.PEM_cert_to_DER_cert(TOY_ROOT_PEM)
(_, s, e), = der_children(der)                         # one outer SEQUENCE
body, algorithm, signature = der_children(der, s, e)
assert (body[0], algorithm[0], signature[0]) == (0x30, 0x30, 0x03)      # SEQUENCE, SEQUENCE, BIT STRING
assert der[algorithm[1]:algorithm[2]] == bytes.fromhex("06032b6570")    # OID 1.3.101.112: Ed25519
assert signature[2] - signature[1] == 65                                # 64-byte signature + pad byte

(info,) = ssl.create_default_context(cadata=TOY_ROOT_PEM).get_ca_certs()   # trust only this root
assert info["subject"] == info["issuer"]                                    # self-signed: a root
assert dict(rdn[0] for rdn in info["subject"])["commonName"] == "Playbook Toy Root CA"
assert info["notAfter"] == "Sep 30 11:35:35 2036 GMT" and info["serialNumber"] == "4A1F"
```

### 49b.9.2 Chains, root stores, CSRs and ACME

Roots are self-signed certificates in **root stores** — Mozilla's (Linux's `ca-certificates`, and `certifi` for `requests`), Apple's, Microsoft's, the Chrome Root Store — and stay offline while **intermediate** CAs sign server certificates. Validation checks each signature up to a trusted root, validity periods, `CA:TRUE` on issuers, the leaf's SAN against the host, and key usages. Servers must send their intermediates: browsers usually fill a gap from caches or the issuer URL in the certificate, but Python and curl fail with "unable to get local issuer certificate". Behind a TLS-inspecting corporate proxy, point Python at the corporate bundle (`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`) or use `truststore`; never turn verification off.

To get a certificate, the server keeps its private key and sends a **certificate signing request** (PKCS #10) with the public key and names, signed to prove possession; the CA validates control of the names and signs. **ACME** (RFC 8555), behind Let's Encrypt and most automated CAs, scripts this with an account key, an order and a challenge — `http-01` (a token under `/.well-known/acme-challenge/`), `dns-01` (a TXT record, required for wildcards) or `tls-alpn-01` — and ACME Renewal Information (RFC 9773, June 2025) lets the CA tell clients when to renew. For internal services and mTLS you run a private CA (a cloud private CA, Vault, cert-manager or SPIRE); a toy one, tested with OpenSSL 3.0 (`mtls_demo.py` runs the same steps and adds a client certificate):

```bash
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout ca.key -out ca.pem \
  -days 365 -subj "/CN=Example Internal Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"
openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout server.key -out server.csr \
  -subj "/CN=orders.internal"
printf 'subjectAltName=DNS:orders.internal\nextendedKeyUsage=serverAuth\n' > server.ext
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -days 30 \
  -extfile server.ext -out server.pem
openssl verify -CAfile ca.pem server.pem                       # server.pem: OK
openssl verify -CAfile ca.pem -purpose sslclient server.pem    # fails: unsuitable certificate purpose
```

### 49b.9.3 Revocation after OCSP, and shrinking lifetimes

A **certificate revocation list** (CRL) is a signed list of revoked serials; **OCSP** asks the CA about one certificate at a time, which reveals the sites each user visits and fails open when the responder is down. Revocation has always been patchy, and short lifetimes are replacing it: Let's Encrypt stopped putting OCSP URLs in new certificates more than 90 days before it shut down its OCSP service on 6 August 2025, publishes revocation only through CRLs, and since 15 January 2026 offers 160-hour certificates (just over six days), including for IP addresses, through its `shortlived` profile. The CA/Browser Forum adopted ballot SC-081v3 on 11 April 2025, and the Baseline Requirements (version 2.3.0 in October 2026) now say:

| Certificates issued on or after | Maximum validity | Maximum reuse of domain validation |
|---|---|---|
| (before 15 March 2026) | 398 days | 398 days |
| 15 March 2026 | 200 days | 200 days |
| 15 March 2027 | 100 days | 100 days |
| 15 March 2029 | 47 days | 10 days |

Let's Encrypt's opt-in `tlsserver` profile has issued 45-day certificates since mid-May 2026, and its default profile moves to 64 days on 10 February 2027 and 45 days on 16 February 2028: automate with ACME, renew at about two-thirds of the lifetime, alert a week before expiry. Public client certificates are ending too: Chrome's root program requires dedicated server-authentication hierarchies by June 2026, so Let's Encrypt dropped `clientAuth` from its default profile on 11 February 2026 and ended its `tlsclient` profile on 8 July 2026. mTLS client certificates now come from a private CA.

### 49b.9.4 Certificate Transparency

Certificate Transparency (RFC 6962) has CAs submit publicly trusted certificates to append-only public logs, which return **signed certificate timestamps** (SCTs); Chrome and Apple reject public TLS certificates without two or three SCTs from distinct logs, depending on lifetime. Domain owners watch the logs (crt.sh is a search interface) for certificates issued for their names by mistake or by attackers; and because the logs are public, keep customer and project names out of public certificates' hostnames.

## 49b.10 TLS 1.3

### 49b.10.1 The handshake, message by message

TLS gives a byte stream confidentiality and integrity and authenticates the server (optionally the client) by certificate. TLS 1.3 (RFC 8446, revised and replaced by RFC 9846 in July 2026) completes a full handshake in one round trip:

| Message | Sender | Encrypted | Purpose |
|---|---|---|---|
| ClientHello | client | no | random value; versions, cipher suites, signature algorithms; SNI and ALPN; **key shares** for groups such as X25519 or X25519MLKEM768, guessed in advance |
| ServerHello | server | no | chosen suite and the server's key share; both sides now derive handshake keys |
| EncryptedExtensions, CertificateRequest | server | yes | remaining settings; a client-certificate request only for mutual TLS |
| Certificate, CertificateVerify | server | yes | the chain, then a signature over the transcript hash with the certificate's key |
| Finished | server, then client | yes | an HMAC over the transcript; then application data flows |

A wrong guess of group costs a HelloRetryRequest round trip. Certificates travel encrypted, so a passive observer sees the server name only in SNI (hidden where Encrypted Client Hello is deployed). TLS 1.3 removed RSA key transport, static Diffie–Hellman, CBC, RC4, compression and renegotiation: every full handshake has forward secrecy and every cipher suite is an AEAD.

### 49b.10.2 ECDHE with X25519, and the key schedule

X25519 is Diffie–Hellman on Curve25519: a private key is 32 random bytes, the public key is the base point (u = 9) "multiplied" by it, and the Montgomery ladder performs the same operations for every bit. The pure-Python version below reproduces the RFC 7748 test vector and the key exchange of the RFC 8448 example handshake, then walks the key schedule — HKDF (RFC 5869) with labeled expansions — to the published secrets. It is for learning: Python integers are not constant time, so real code uses `X25519PrivateKey` from `cryptography`, or simply the TLS library.

```python
import hashlib
import hmac

P, A24, BASE = 2 ** 255 - 19, 121665, (9).to_bytes(32, "little")


def x25519(scalar: bytes, u: bytes) -> bytes:
    """RFC 7748 X25519. Educational only: not constant time."""
    k = bytearray(scalar)
    k[0] &= 248                                          # clamp the scalar
    k[31] = (k[31] & 127) | 64
    k = int.from_bytes(k, "little")
    x1 = int.from_bytes(u, "little") & ((1 << 255) - 1)
    x2, z2, x3, z3, swap = 1, 0, x1, 1, 0
    for t in reversed(range(255)):                       # the Montgomery ladder
        bit = (k >> t) & 1
        swap ^= bit
        if swap:
            x2, x3, z2, z3 = x3, x2, z3, z2
        swap = bit
        a, b, c, d = (x2 + z2) % P, (x2 - z2) % P, (x3 + z3) % P, (x3 - z3) % P
        aa, bb, da, cb = a * a % P, b * b % P, d * a % P, c * b % P
        e = (aa - bb) % P
        x3, z3 = (da + cb) ** 2 % P, x1 * (da - cb) ** 2 % P
        x2, z2 = aa * bb % P, e * (aa + A24 * e) % P
    if swap:
        x2, x3, z2, z3 = x3, x2, z3, z2
    return (x2 * pow(z2, P - 2, P) % P).to_bytes(32, "little")


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def hkdf_expand_label(secret: bytes, label: str, context: bytes, length: int = 32) -> bytes:
    full = b"tls13 " + label.encode()
    info = length.to_bytes(2, "big") + bytes([len(full)]) + full + bytes([len(context)]) + context
    output, block, counter = b"", b"", 1
    while len(output) < length:                          # HKDF-Expand (RFC 5869)
        block = hmac.new(secret, block + info + bytes([counter]), hashlib.sha256).digest()
        output, counter = output + block, counter + 1
    return output[:length]


h = bytes.fromhex
alice = h("77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a")           # RFC 7748, 6.1
assert x25519(alice, BASE) == h("8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a")

client_key = h("49af42ba7f7994852d713ef2784bcbcaa7911de26adc5642cb634540e7ea5005")     # RFC 8448, 3
server_key = h("b1580eeadf6dd589b8ef4f2d5652578cc810e9980191ec8d058308cea216a21e")
shared = x25519(client_key, x25519(server_key, BASE))    # the client's view of the ECDHE secret
assert shared == x25519(server_key, x25519(client_key, BASE)) == \
    h("8bd4054fb55b9d63fdfbacf9f04b9f0d35e6d63f537563efd46272900f89492d")

empty = hashlib.sha256(b"").digest()
early = hkdf_extract(bytes(32), bytes(32))                                  # no pre-shared key
handshake = hkdf_extract(hkdf_expand_label(early, "derived", empty), shared)
assert handshake == h("1dc826e93606aa6fdc0aadc12f741b01046aa6b99f691ed221a9f0ca043fbeac")
transcript = h("860c06edc07858ee8e78f0e7428c58edd6b43f2ca3e6e95f02ed063cf0e1cad8")  # ClientHello..ServerHello
assert hkdf_expand_label(handshake, "c hs traffic", transcript)[:4] == h("b3eddb12")
assert hkdf_expand_label(handshake, "s hs traffic", transcript)[:4] == h("b67b7d69")
main = hkdf_extract(hkdf_expand_label(handshake, "derived", empty), bytes(32))
assert main == h("18df06843d13a08bf2a449844c5f8a478001bc4d4c627984d5a41da8d0402919")
```

The **early secret** comes from a pre-shared key, or zeros without one. Mixing in the (EC)DHE secret gives the **handshake secret**, from which each side derives its handshake traffic secret with a label (`c hs traffic`, `s hs traffic`) and the hash of the messages so far; those keys encrypt everything after ServerHello. One more extraction gives the secret RFC 8446 called the master secret (RFC 9846 drops the word "master" in favor of "main"), which yields the application traffic secrets. Because every traffic secret, and Finished itself, covers the transcript hash, a tampered ClientHello produces different keys and Finished fails.

### 49b.10.3 Server authentication, downgrades, resumption and 0-RTT

To stop a man in the middle (49b.2.6), the server signs the transcript hash — covering both key shares — in CertificateVerify, and the client checks the chain, the hostname and that signature; Finished proves both saw the same transcript. A TLS 1.3 server that negotiates an older version puts a fixed marker in its random value, and a TLS 1.3 client that sees it aborts, so downgrades fail. Session tickets let later connections resume with a pre-shared key (plus fresh (EC)DHE for forward secrecy). **0-RTT** data, sent in the first flight under keys derived from the resumption secret alone, has no forward secrecy and can be **replayed**, so allow it only for idempotent requests, never for a payment or a tool call with side effects (servers can answer `425 Too Early`, RFC 8470). RFC 9846 keeps the flow but forbids reusing key shares and negotiating TLS 1.0 or 1.1, and makes key updates before usage limits mandatory. Separately, the 1,216-byte X25519MLKEM768 key share (49b.2.7) explains many handshakes that suddenly fail behind old load balancers and firewalls that expect a ClientHello to fit in one packet.

### 49b.10.4 What Python's default context enforces

`urllib` and `httpx` build on `ssl.create_default_context()`, urllib3 (under `requests`) builds an equivalent context, and these defaults are the ones to keep:

```python
import ssl

client = ssl.create_default_context()
assert client.protocol == ssl.PROTOCOL_TLS_CLIENT
assert client.verify_mode == ssl.CERT_REQUIRED and client.check_hostname   # valid chain, matching SAN
assert client.options & ssl.OP_NO_COMPRESSION and client.options & ssl.OP_NO_SSLv3
# CPython's own builds set a TLS 1.2 floor (since 3.10); some Linux distributions build Python to
# follow the system OpenSSL policy instead, which reads MINIMUM_SUPPORTED here.
assert client.minimum_version in (ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3,
                                  ssl.TLSVersion.MINIMUM_SUPPORTED)
if ssl.HAS_TLSv1_3:
    suites = {c["name"] for c in client.get_ciphers() if c["protocol"] == "TLSv1.3"}
    assert "TLS_AES_128_GCM_SHA256" in suites and all("GCM" in s or "POLY1305" in s for s in suites)

unsafe = ssl.create_default_context()
try:
    unsafe.verify_mode = ssl.CERT_NONE                   # refused while hostname checking is on
    raise AssertionError("accepted")
except ValueError:
    unsafe.check_hostname = False
    unsafe.verify_mode = ssl.CERT_NONE                   # what verify=False means: talk to anyone

server = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
assert server.protocol == ssl.PROTOCOL_TLS_SERVER and server.verify_mode == ssl.CERT_NONE
server.verify_mode = ssl.CERT_REQUIRED                   # mutual TLS: require a client certificate
```

Since Python 3.13 the default context also sets `VERIFY_X509_STRICT`, which rejects certificates that break RFC 5280 rules OpenSSL otherwise tolerates (private CAs with sloppy extensions start failing after an upgrade), and `VERIFY_X509_PARTIAL_CHAIN`, which lets a trusted intermediate end a chain:

```python
# requires: 3.13
import ssl

flags = ssl.create_default_context().verify_flags
assert flags & ssl.VERIFY_X509_STRICT and flags & ssl.VERIFY_X509_PARTIAL_CHAIN
```

The usual mistakes are `verify=False` "temporarily", a custom `cafile` that replaces rather than adds to the trusted roots, missing SNI when wrapping sockets by hand (pass `server_hostname`), and pinning a leaf certificate that now rotates every few weeks.

## 49b.11 Mutual TLS

### 49b.11.1 What changes

In mutual TLS the server also sends CertificateRequest; the client answers with its own Certificate and a CertificateVerify signed with its private key, and the server validates the chain against its *client* trust store. The server then has a cryptographically proven client identity for every connection — usually a SAN such as a SPIFFE ID — and authorizes on it; a key that never leaves the workload replaces API keys that leak into logs. A TLS 1.3 detail surprises people: the client sends its certificate after the server's Finished, so a client without an acceptable certificate learns of the rejection only on its first read. Tested with Python 3.10 to 3.14 and OpenSSL 3.0, the client's `wrap_socket` returns normally, its first `recv` raises `TLSV13_ALERT_CERTIFICATE_REQUIRED`, and the server logs `PEER_DID_NOT_RETURN_A_CERTIFICATE`, so errors surface in request code, not connect code; `labs/cs-essentials/mtls_demo.py` reproduces this next to successful handshakes and a hostname mismatch.

### 49b.11.2 Where it is used, and what goes wrong

Service meshes (Istio, Linkerd) give every pod a certificate and authenticate pod-to-pod traffic transparently. **SPIFFE** standardizes workload identity — an ID such as `spiffe://example.org/ns/agents/sa/support-agent` in an X.509 SVID's URI SAN — and **SPIRE** attests workloads and issues short-lived SVIDs (30.2). Banks and payment networks require client certificates from partners, sometimes with certificate-bound tokens (RFC 8705), and Kubernetes, etcd, Kafka and PostgreSQL use it too. The pitfalls:

- **A private CA, trusted narrowly.** Publicly trusted TLS CAs have dropped client authentication (49b.9.3), and a server that trusted a public root store for clients would admit certificates issued to strangers; trust a dedicated client CA and authorize on the SAN, not on "the chain verified".
- **Rotation with overlap.** Certificates that live hours to days need automation (SPIRE, cert-manager); when the CA rotates, servers trust old and new CA certificates until clients have moved.
- **Termination at a proxy.** If TLS ends at a load balancer, the application sees the client identity only in a header (Envoy's `x-forwarded-client-cert`), to be accepted only from the proxy after it strips any client-supplied copy.
- **Chains, clocks, debugging.** Clients must send intermediates; skewed clocks produce "not yet valid" errors that look random; `openssl s_client -cert agent.pem -key agent.key -CAfile ca.pem -connect host:443` shows the server's chain, the CA names it accepts for client certificates, and any alert.

**Interview line:** *"mTLS gives each workload a key it never shares and a certificate from our private CA, usually with a SPIFFE ID in the SAN; the server authorizes on that identity, certificates live hours to days and rotate automatically, and in TLS 1.3 a rejected client certificate shows up on the first read, not at connect."*

## 49b.12 The Linux file system

### 49b.12.1 Everything is a file, inodes and links

Linux exposes most resources through one interface: open a path or create an object, get a small integer — a file descriptor — and `read`, `write` and `close` it. Files, directories, devices (`/dev/null`, disks), named pipes and Unix sockets have paths; network sockets and pipes are descriptors without them; a virtual file system layer dispatches each call to ext4, XFS, tmpfs, overlayfs or NFS.

A file's metadata — size, owner, permission bits, timestamps, link count, pointers to data blocks — lives in an **inode**, numbered uniquely within its file system. The inode does not hold the name: a **directory** maps names to inode numbers, and each entry is a link. That explains hard links, why renames within a file system are atomic, why deleting an open file frees nothing, and why a disk can run out of inodes with blocks to spare (`df -i`; millions of tiny cache files are the usual cause).

```python
import os
import stat
import tempfile

with tempfile.TemporaryDirectory() as d:
    original, hard, soft = (os.path.join(d, name) for name in ("model.bin", "hard.bin", "soft.bin"))
    with open(original, "w") as f:
        f.write("weights v1\n")
    os.link(original, hard)                         # a second name for the same inode
    os.symlink("model.bin", soft)                   # a new inode whose content is a path
    assert os.stat(original).st_ino == os.stat(hard).st_ino and os.stat(hard).st_nlink == 2
    assert stat.S_ISLNK(os.lstat(soft).st_mode) and os.lstat(soft).st_size == len("model.bin")
    assert os.lstat(soft).st_ino != os.stat(soft).st_ino == os.stat(original).st_ino   # stat follows

    os.remove(original)                             # removes one name; the inode survives
    assert open(hard).read() == "weights v1\n" and os.stat(hard).st_nlink == 1
    assert os.path.lexists(soft) and not os.path.exists(soft)        # now a dangling link

    log = os.path.join(d, "app.log")
    with open(log, "w") as f:
        f.write("still readable\n")
    with open(log) as handle:
        os.remove(log)                              # blocks are freed when the last descriptor closes
        assert handle.read() == "still readable\n" and not os.path.exists(log)

    with open(hard + ".tmp", "w") as f:
        f.write('{"model": "v2"}')
    os.replace(hard + ".tmp", hard)                 # atomic: readers see the old file or the new one
    assert open(hard).read() == '{"model": "v2"}'
```

The unlinked-but-open file is the "disk full but `du` finds nothing" incident: a process still holds a deleted log (`lsof +L1` finds it). A **hard link** is another name for the same inode and cannot cross file systems or name a directory; a **symbolic link** is a small file holding a path, can point anywhere, and dangles when the target goes. Deployments switch versions atomically by renaming a new symbolic link over `current`.

### 49b.12.2 Permissions

Each inode has an owner, a group and read, write and execute bits for owner, group and others (`rwxr-x---` is `0o750`). On a directory, read lists names, write creates and deletes entries, and execute allows passing through, so deleting a file needs write permission on its *directory*. **Setuid** and **setgid** executables run with the file owner's or group's identity; setgid on a directory makes new files inherit its group; the **sticky bit** (`/tmp` is `1777`) lets only a file's owner, the directory's owner or root delete or rename it. The **umask** removes bits from the mode a program requests:

```python
import os
import stat
import tempfile

with tempfile.TemporaryDirectory() as d:
    previous = os.umask(0o027)                      # no write for the group, nothing for others
    try:
        os.close(os.open(os.path.join(d, "secret.env"), os.O_CREAT | os.O_WRONLY, 0o666))
        os.mkdir(os.path.join(d, "cache"), 0o777)
    finally:
        os.umask(previous)                          # the umask is per process: restore it
    assert stat.S_IMODE(os.stat(os.path.join(d, "secret.env")).st_mode) == 0o640
    assert stat.S_IMODE(os.stat(os.path.join(d, "cache")).st_mode) == 0o750
```

Root bypasses these checks, so containers should run as a non-root user with a read-only root file system; finer controls are ACLs, capabilities (`CAP_NET_BIND_SERVICE` to bind port 443) and SELinux or AppArmor.

### 49b.12.3 /proc, /sys, mounts and durability

`/proc` and `/sys` are kernel views generated on read: `/proc/<pid>/` holds `status`, `cmdline`, `environ` (so secrets in environment variables are visible to the same user), `fd/` and `limits`. On cgroup v2, `/sys/fs/cgroup/memory.max` is a container's memory limit; a model server that sizes caches from the host's `/proc/meminfo` instead is OOM-killed (exit code 137) the first time load rises. Containers see an overlay of read-only image layers plus a writable layer, volumes and tmpfs mounts; model caches such as `~/.cache/huggingface` grow under home directories unless pointed at a volume, and `/dev/shm`, through which PyTorch data-loader workers pass batches, is 64 MB under `docker run` unless `--shm-size` says otherwise — the source of "bus error" crashes.

A successful `write` reaches the kernel's page cache, not the disk: it survives a crash of the process but not a power failure. `fsync(fd)` forces the file to the device, and a new or renamed file also needs an `fsync` of its directory. The safe update — write a temporary file in the same directory, `fsync` it, `rename` it over the old name, `fsync` the directory — is what the LSM store's MANIFEST uses (49b.15.6); databases batch transactions into one `fsync` (group commit) because each costs microseconds to milliseconds.

## 49b.13 Processes, threads and file descriptors

### 49b.13.1 Processes, fork, exec and zombies

A process is a running program with its own address space, descriptor table, credentials, signal handlers and limits, identified by a PID and its parent's PID. New programs start in two steps: `fork` copies the parent (cheaply, with copy-on-write pages), and `exec` replaces the child's program while keeping its PID and its descriptors not marked close-on-exec. The parent collects the exit status with `wait`; until then the finished child is a **zombie**, holding no memory but keeping its PID and process-table entry.

```python
import os
import sys
import time

if sys.platform.startswith("linux"):
    pid = os.fork()
    if pid == 0:                                    # the child exits at once
        os._exit(7)
    state, deadline = None, time.time() + 5
    while state != "Z" and time.time() < deadline:
        with open(f"/proc/{pid}/stat") as f:
            state = f.read().rsplit(")", 1)[1].split()[0]
        time.sleep(0.01)
    assert state == "Z"                             # finished, not yet reaped
    _, status = os.waitpid(pid, 0)                  # reaping collects the status
    assert os.waitstatus_to_exitcode(status) == 7 and not os.path.exists(f"/proc/{pid}")
```

### 49b.13.2 PID 1 in containers

Orphans are re-parented to the init process of their PID namespace, which must reap them. In a container your program is often that PID 1, and the kernel delivers to a namespace's PID 1 only the signals it installed a handler for, whether they come from inside the container or from the host; only SIGKILL and SIGSTOP from the host always get through (pid_namespaces(7)). A program relying on SIGTERM's default action therefore ignores `docker stop` and `kubectl delete` until the grace period ends (10 seconds for `docker stop`, 30 for a Kubernetes pod by default) and SIGKILL arrives. Checked as root with util-linux and dash 0.5.12:

```bash
unshare --fork --pid --mount-proc sh -c 'kill -TERM $$; echo "PID $$ ignored SIGTERM"'   # PID 1 ignored SIGTERM
unshare --fork --pid --mount-proc sh -c 'trap "echo handled; exit 0" TERM; kill -TERM $$' # handled
```

Install a SIGTERM handler, or run a small init as PID 1 (`docker run --init`, which uses tini, or `dumb-init`) that forwards signals and reaps. Use the exec form `CMD ["python", "serve.py"]`: the shell form runs `/bin/sh -c`, which on Debian- and Ubuntu-based images is dash, and dash (0.5.12, tested) does not replace itself with a single command, so the shell becomes PID 1 and your program never sees the signal (bash does replace itself). Entrypoint scripts should end with `exec "$@"`.

### 49b.13.3 Signals and graceful shutdown

| Signal (x86-64 and ARM Linux) | Default | Meaning |
|---|---|---|
| SIGHUP 1 | terminate | terminal closed; by convention "reload configuration" |
| SIGINT 2 | terminate | Ctrl-C |
| SIGKILL 9, SIGSTOP 19 | terminate; stop | cannot be caught, blocked or ignored |
| SIGPIPE 13 | terminate | wrote to a pipe or socket nobody reads (49b.14.1) |
| SIGTERM 15 | terminate | the polite stop: `kill`, `docker stop`, Kubernetes |
| SIGCHLD 17 | ignore | a child changed state: call `wait` |

A shell reports death by signal n as 128 + n — 143 for SIGTERM, 137 for SIGKILL, often the OOM killer — and Python's `subprocess` as −n. On SIGTERM a service stops taking work, finishes or checkpoints what is in flight within the grace period (an agent must not leave a tool call half-applied), flushes logs and traces, and exits 0:

```python
import signal
import subprocess
import sys

WORKER = """
import signal, sys, time
stopping = False
def on_term(signum, frame):
    global stopping
    stopping = True                     # finish the current item; take no new ones
signal.signal(signal.SIGTERM, on_term)
print("ready", flush=True)
while not stopping:
    time.sleep(0.05)                    # one unit of work
print("drained and closed", flush=True)
"""

if sys.platform != "win32":
    for stop, expected_output, expected_code in ((signal.SIGTERM, "drained and closed", 0),
                                                 (signal.SIGKILL, "", -signal.SIGKILL)):
        worker = subprocess.Popen([sys.executable, "-c", WORKER], stdout=subprocess.PIPE, text=True)
        assert worker.stdout.readline().strip() == "ready"
        worker.send_signal(stop)                    # SIGKILL: no handler runs, nothing is flushed
        out, _ = worker.communicate(timeout=10)
        assert out.strip() == expected_output and worker.returncode == expected_code
```

Kubernetes removes a terminating pod from its Service's endpoints in parallel with sending SIGTERM, so a server that exits instantly may drop requests still arriving; a short `preStop` sleep, or serving a few more seconds before draining, closes the gap.

### 49b.13.4 Threads versus processes

A Linux thread shares its creator's address space, descriptors and signal handlers; a process gets copies and fails independently. In CPython's default build one thread runs Python bytecode at a time, so threads (or `asyncio`) suit I/O-bound model and tool calls and processes suit CPU-bound parsing (the optional free-threaded build is covered in 39d.22). Two traps: forking a process that runs threads copies only the calling thread, so a lock another thread held stays locked forever in the child — Python 3.12 warns when `os.fork()` runs in a multi-threaded process, and Python 3.14 changed the default start method of `multiprocessing` and `ProcessPoolExecutor` on Linux from `fork` to `forkserver` — and CUDA does not survive `fork`, so GPU code uses `spawn` or `forkserver`.

### 49b.13.5 File descriptors, redirection and buffering

A descriptor table maps small integers to **open file descriptions**, kernel objects holding the offset and status flags. `dup2(old, new)` makes `new` share `old`'s description, and that is all redirection is: `cmd > out.log 2>&1` opens the file as descriptor 1, then copies 1 onto 2, while `cmd 2>&1 > out.log` points 2 at the *current* stdout (the terminal) first, so errors still reach the terminal. Descriptors survive `fork` and `exec` unless marked close-on-exec, and a leaked write end of a pipe keeps its reader from ever seeing end of file, so since PEP 446 (Python 3.4) Python creates descriptors non-inheritable and `subprocess` passes only what you ask for:

```python
import os
import subprocess
import sys
import tempfile

read_end, write_end = os.pipe()
assert not os.get_inheritable(write_end)            # close-on-exec by default
probe = "import os, sys; os.write(int(sys.argv[1]), b'hello from the child')"
done = subprocess.run([sys.executable, "-c", probe, str(write_end)], capture_output=True)
assert done.returncode != 0 and b"Bad file descriptor" in done.stderr       # never inherited
subprocess.run([sys.executable, "-c", probe, str(write_end)], pass_fds=(write_end,), check=True)
os.close(write_end)
assert os.read(read_end, 100) == b"hello from the child"
os.close(read_end)

with tempfile.TemporaryFile() as log:               # 2>&1: both streams into one file
    both = "import sys; print('out', flush=True); print('err', file=sys.stderr)"
    subprocess.run([sys.executable, "-c", both], stdout=log, stderr=subprocess.STDOUT, check=True)
    log.seek(0)
    assert log.read().split() == [b"out", b"err"]

child = "import sys; print(sys.stdout.isatty(), sys.stdout.line_buffering)"   # stdout is a pipe here
assert subprocess.run([sys.executable, "-c", child], capture_output=True, text=True).stdout.split() \
    == ["False", "False"]                           # so it is block-buffered, not line-buffered
```

Per-process descriptor limits (`ulimit -n`, often 1,024 in interactive shells) turn an HTTP client created per request into `EMFILE: Too many open files`; reuse connection pools. The last check explains a common logging mystery: output that appears at once in a terminal arrives late, or never, in a container log, because into a pipe it waits in a buffer until the buffer fills or the process exits cleanly, and SIGKILL loses it. Use `print(..., flush=True)`, `python -u` or `PYTHONUNBUFFERED=1`.

## 49b.14 Pipelines and shell scripts that fail loudly

Every behavior below was checked with bash 5.2 on Linux, and 49b.14.4 rechecks the main ones.

### 49b.14.1 How a pipeline runs

`a | b | c` starts all three processes at once, joined by pipes (64 KiB kernel buffers by default on Linux): the stages run concurrently, a writer blocks only while its pipe is full, and the pipeline takes about as long as its slowest stage rather than the sum. Consequences:

- **The status is the last command's**: `false | true` succeeds. `set -o pipefail` reports the rightmost failure, and `${PIPESTATUS[@]}` holds every status.
- **SIGPIPE**: when a reader exits early, the writer's next write kills it, so in `yes | head -n 1` the `yes` process exits 141 (128 + 13) — harmless, until `pipefail` makes the whole pipeline fail with 141.
- **Buffering**: programs block-buffer into pipes (49b.13.5); `grep --line-buffered`, `stdbuf -oL` (for C stdio programs) and `python -u` change that.
- **Same-file redirection**: `sort data.txt > data.txt` leaves an empty file, because the shell truncates the file while setting up the redirection, before `sort` starts reading. `sort -o data.txt data.txt` is safe (POSIX lets the output name an input, and `sort` reads everything before writing); for other tools, write a temporary file in the same directory and rename it over the original.
- **Subshells**: each part of a pipeline runs in a subshell, so variables set in `cmd | while read` vanish:

```bash
count=0
printf 'a\nb\n' | while read -r line; do count=$((count + 1)); done
echo "$count"                      # 0: the loop ran in a subshell
while read -r line; do count=$((count + 1)); done < <(printf 'a\nb\n')
echo "$count"                      # 2: process substitution keeps the loop in this shell
```

### 49b.14.2 Quoting, word splitting and odd file names

An unquoted `$var` is split on the characters in `IFS` (whitespace by default) and then glob-expanded: with `f='quarterly report.pdf'`, `rm $f` removes `quarterly` and `report.pdf`. Double-quote every expansion (`"$var"`, `"$(cmd)"`, `"${array[@]}"`), pass arguments on with `"$@"`, put `--` before user-supplied paths (`rm -- "$f"`), build command lines in arrays, and run `shellcheck`. Single quotes keep everything literal; inside double quotes `$`, backquotes and `\` keep their special meaning. File names may contain newlines, so separate them with NUL bytes:

```bash
find ./shards -name '*.jsonl' -print0 | xargs -0 -n 1 -P 8 python3 validate.py    # 8 in parallel
while IFS= read -r -d '' f; do printf 'processing %s\n' "$f"; done < <(find . -name '*.pdf' -print0)
```

### 49b.14.3 `set -euo pipefail`, here-documents and cleanup traps

`set -e` exits on failure, `set -u` on unset variables, and `pipefail` exposes pipeline failures — a good default with holes:

| Situation | Under `set -e` |
|---|---|
| failure in an `if` or `while` condition, or left of `&&` or `\|\|` | ignored: the command is "being tested" |
| a function called as a condition (`if deploy; then`) | `-e` is off for the whole function body |
| `local x=$(failing_cmd)` | continues: `local` succeeds and hides the status |
| `x=$(failing_cmd)` | exits |
| `echo "$(failing_cmd; echo next)"` | the subshell continues; `shopt -s inherit_errexit` stops it, but `echo` still succeeds |
| `${REQUIRED:?message}` | aborts with the message: the clean way to demand a variable |

A here-document feeds literal text to stdin (`<<'EOF'` disables expansion, `<<-EOF` strips leading tabs), and process substitution `<(cmd)` exposes output as a path such as `/dev/fd/63`: `diff <(sort a.txt) <(sort b.txt)`. Bash runs an `EXIT` trap on normal exit, `exit 1`, a `set -e` failure, SIGINT and SIGTERM; dash runs it after a signal only if that signal's own trap calls `exit`. A trapped signal waits for a foreground command to finish (two seconds for a two-second `sleep`), but `cmd & wait $!` handles it at once. The template below, sent SIGTERM mid-job, exited 143, killed the job and removed its temporary directory.

```bash
#!/usr/bin/env bash
set -euo pipefail
workdir=$(mktemp -d)
pid=
cleanup() {
  if [[ -n $pid ]]; then kill -- "$pid" 2>/dev/null || true; fi
  rm -rf -- "$workdir"
}
trap cleanup EXIT
trap 'exit 143' TERM                 # turn the signal into an exit (the idiom dash needs too)
trap 'exit 130' INT

python3 -u run_eval.py --out "$workdir/results.jsonl" &
pid=$!
wait "$pid"                          # lets traps fire promptly; a failure exits through set -e
pid=
cp -- "$workdir/results.jsonl" "./results-$(date +%F).jsonl"
```

### 49b.14.4 Checking the claims, and habits that save time

```python
import shutil
import subprocess


def bash(script: str) -> str:
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True).stdout.strip()


if shutil.which("bash"):
    assert bash("false | true; echo $?") == "0"
    assert bash("set -o pipefail; false | true | (exit 3); echo $? ${PIPESTATUS[*]}") == "3 1 0 3"
    assert bash("set -o pipefail; yes | head -n 1 > /dev/null; echo $?") == "141"
    assert bash("n=0; printf 'a\\nb\\n' | while read -r l; do n=$((n+1)); done; echo $n") == "0"
    assert bash("set -e; f() { local x=$(false); echo survived; }; f") == "survived"
    assert bash("set -e; f() { false; echo inside; }; if f; then echo after; fi") == "inside\nafter"
    assert bash("x='a  b'; printf '[%s]' $x \"$x\"") == "[a][b][a  b]"
    if int(bash("echo ${BASH_VERSINFO[0]}")) >= 5:
        assert bash("trap 'echo cleanup' EXIT; kill -TERM $$; sleep 1") == "cleanup"
```

Habits that save time: `timeout 30s cmd` bounds a step that might hang, `flock` keeps two copies of a cron job from overlapping, `command -v` checks for a tool, `sudo` usually resets `PATH` (give full paths), `bash -x` with `PS4='+ ${BASH_SOURCE}:${LINENO}: '` traces with line numbers, and a script that outgrows a screen should become Python.

## 49b.15 LSM trees

### 49b.15.1 Why sequential writes win

A B-tree updates in place: changing a 100-byte row rewrites a 4 to 16 KB page somewhere on the device, and small random writes cost seeks on disks and erase cycles on SSDs. A **log-structured merge tree** (O'Neil and colleagues, 1996; popularized by Bigtable in 2006, then LevelDB and RocksDB) never updates in place: it logs each write, collects recent writes in a sorted in-memory table, writes that table sequentially as an immutable sorted file, and merges files in the background. Writes become sequential and batched; the cost moves to reads, which may consult several files, and to merging, which rewrites data more than once.

### 49b.15.2 The write path: WAL, memtable, flush

Every put or delete is appended to a **write-ahead log** before it is acknowledged (with an `fsync` per write, or per batch of concurrent writers, to survive power loss), then inserted into the **memtable**, a sorted in-memory structure (a skip list in LevelDB and RocksDB). A full memtable becomes immutable and is **flushed** as a sorted string table (SSTable): entries in key order, a sparse index of block offsets, a Bloom filter and a footer. Once the table is durable and recorded in the manifest, the WAL it covered is deleted. The lab frames each WAL record as one line with a CRC-32; a crash can only damage the tail, so recovery keeps the longest intact prefix and truncates the rest:

```python
import json
import zlib


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


log = b"".join(encode_record(*r) for r in [(1, "user:1", "Ada"), (2, "user:2", "Grace"), (3, "user:1", None)])
records, valid = decode_records(log)
assert records == [(1, "user:1", "Ada"), (2, "user:2", "Grace"), (3, "user:1", None)] and valid == len(log)
torn = log + encode_record(4, "user:3", "Edsger")[:-9]              # power failed mid-write
assert decode_records(torn) == (records, len(log))                   # the torn record is dropped
assert decode_records(log.replace(b'"Grace"', b'"Grade"'))[0] == records[:1]   # bit rot: stop there
```

### 49b.15.3 The read path and Bloom filters

A lookup checks the memtable, then SSTables from newest to oldest, and stops at the first version found — a value, or a **tombstone** meaning "deleted". Key ranges rule out most tables, and a **Bloom filter** rules out nearly all the rest without disk I/O: m bits and k hash functions, where adding a key sets k bits and a lookup answers "definitely absent" if any of its bits is clear — never a false negative. With n keys the false-positive rate is about (1 − e^(−kn/m))^k, minimized at k = (m/n)·ln 2, which needs about 9.6 bits per key for 1 percent and 14.4 for 0.1 percent. A table that passes both checks costs one in-memory index lookup and one block read. Range scans cannot use the filters and must merge every overlapping table, which is where an LSM tree pays more than a B-tree.

```python
import hashlib
import math


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


bloom = BloomFilter.for_capacity(10_000, fp_rate=0.01)
assert (bloom.num_bits, bloom.num_hashes) == (95851, 7)           # about 9.6 bits per key
for i in range(10_000):
    bloom.add(f"doc:{i}")
assert all(bloom.might_contain(f"doc:{i}") for i in range(10_000))   # no false negatives
false_positives = sum(bloom.might_contain(f"missing:{i}") for i in range(50_000))
assert 0.005 < false_positives / 50_000 < 0.015                      # close to the 1% target
```

### 49b.15.4 Tombstones and compaction

Files are immutable, so a delete writes a tombstone with a newer sequence number. It must survive until no older version can exist below it, or the old value **resurrects**: LevelDB drops a tombstone only when no file in a deeper level covers its key, and the lab checks every table outside the compaction. Cassandra also keeps tombstones for `gc_grace_seconds` (ten days by default) so a replica that missed the delete learns of it through repair, and many deletes in one partition make reads wade through tombstones.

**Compaction** merges sorted files into fewer, larger ones — a streaming k-way merge with a heap — keeping each key's newest version and dropping tombstones when safe. It trades **write amplification** (bytes written per byte the application wrote), **read amplification** (files or blocks examined per lookup) and **space amplification** (bytes stored per byte of live data); no design minimizes all three (the "RUM conjecture" of Athanassoulis and colleagues, 2016).

| | Size-tiered (Cassandra STCS, RocksDB universal) | Leveled (LevelDB, RocksDB's default) |
|---|---|---|
| Shape | tiers of similar-sized tables; enough in a tier (4 by default in Cassandra) merge into one larger table | level 0 holds flushes; each level L ≥ 1 is one sorted run split into files, about ten times larger than the level above |
| Write amplification | low: about one rewrite per tier | higher: about fanout rewrites per level |
| Space amplification | high: old versions linger, and merges need room for their output | low: about 10 percent obsolete at the bottom level |
| Read amplification | more tables per lookup | about one file per level |
| Suits | write-heavy, append-mostly data | read-heavy data with updates and deletes |

LevelDB's defaults make the leveled shape concrete: level 0 compacts at four files, level L may hold 10^L MB, files are cut at about 2 MB, and a per-level pointer picks files round-robin. Cassandra 5.0's Unified Compaction Strategy tunes between the two with one parameter (open-source 5.0 still defaults to size-tiered), and time-window compaction lets whole windows of time series expire together. The merge itself, from the lab:

```python
import heapq

_NO_KEY = object()


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


newer = [("a", 9, "a-v2"), ("c", 8, None)]                 # c was deleted after it was written
older = [("a", 1, "a-v1"), ("b", 2, "b-v1"), ("c", 3, "c-v1")]
assert list(merge_newest([older, newer])) == [("a", 9, "a-v2"), ("b", 2, "b-v1"), ("c", 8, None)]
assert list(merge_newest([older, newer], can_drop=lambda key, seq: True)) == [
    ("a", 9, "a-v2"), ("b", 2, "b-v1")]                    # a bottom-level merge may drop the tombstone
```

`python3 -B labs/cs-essentials/tiny_lsm.py` runs one workload — 30,000 operations over 3,000 keys (85 percent puts, 15 percent deletes), an 8 KB memtable, then 5,000 lookups, half for keys never written — through both strategies:

| Strategy | Tables (per level) | Write amplification | Space amplification | Tables probed per lookup | Block reads per lookup |
|---|---|---|---|---|---|
| Leveled | 18 (3, 4, 11) | 3.92 | 1.40 | 2.11 | 0.49 |
| Size-tiered | 7 | 2.63 | 2.83 | 2.40 | 0.52 |

The lab counts write amplification as table bytes written by flushes and compactions per byte flushed (the WAL adds one more write of everything), and space amplification as table data stored per byte of live entries. Only the direction carries over from a toy: leveled compaction rewrote more and stored less garbage, and Bloom filters kept block reads near one per lookup that finds a key.

### 49b.15.5 Snapshots, B-trees, and where LSM engines run

Sequence numbers give snapshots almost free — a reader ignores versions newer than its pinned number — and the same idea, with timestamps in the keys, gives CockroachDB and TiDB their multi-version concurrency control. Against a B-tree (InnoDB, PostgreSQL, SQLite), an LSM tree wins on ingest and on compressing immutable files and loses on predictable reads: compaction causes latency spikes, and write stalls when it falls behind.

As of October 2026, LSM engines include LevelDB, RocksDB (leveled by default) and Pebble (CockroachDB's default since 20.2); RocksDB sits inside TiKV, YugabyteDB, Kafka Streams and Apache Flink's state backend, and Cassandra and ScyllaDB are distributed LSM databases. Weaviate keeps objects and its inverted index in LSM stores (since 1.5) and its HNSW index in a separate commit log; Qdrant built its own Gridstore to replace RocksDB for payloads and sparse vectors (introduced with version 1.13 in early 2025), citing compaction latency spikes; and Prometheus stores time series the same way — a WAL-protected head block, immutable two-hour blocks, tombstone files, background compaction.

### 49b.15.6 The lab's store

`tiny_lsm.LSMStore` keeps `wal.log`, `.sst` files and a `MANIFEST` of live tables. Every flush and compaction writes new tables (temporary name, then rename), replaces the MANIFEST atomically, and only then empties the WAL or deletes the inputs, so recovery opens what the MANIFEST names, deletes everything else, replays the WAL to its last intact record and finishes pending compaction. Reads search tables by descending maximum sequence number, which stays correct when size-tiered compaction merges tables of different ages; the tests compare random operations and simulated crashes against a Python dict.

**Interview line:** *"An LSM tree turns random writes into sequential ones: log, memtable, immutable sorted files, background merging. I pay in read amplification, which Bloom filters and leveled compaction keep near one block per lookup, and in write and space amplification, which I trade by choosing tiered or leveled compaction. Tombstones live until no older version can exist, and compaction debt shows up as latency spikes and write stalls, so I watch pending compaction bytes."*

## 49b.16 Interview questions with model answers, and exercises

**1. Why is `sha256(secret + message)` a bad MAC?** Length extension: from its digest an attacker computes a valid digest for the message with bytes appended. Use HMAC-SHA256 and compare with `hmac.compare_digest`.

**2. How do you store passwords?** Argon2id with OWASP's parameters (for example 19 MiB, two iterations) or scrypt, PBKDF2 where FIPS applies; a salt per password; parameters stored with the hash and raised by rehashing at login; NIST's 15-character minimum for single-factor passwords, no forced rotation, a breached-password blocklist; rate limiting.

**3. Walk through a TLS 1.3 handshake, and say where forward secrecy comes from.** ClientHello with key shares, SNI and ALPN; ServerHello with the server's share; HKDF handshake keys from the shared secret and transcript; encrypted Certificate, CertificateVerify and Finished; the client verifies, sends Finished, and data flows after one round trip. The (EC)DHE shares are ephemeral and erased, so stealing the certificate key later decrypts nothing; it only ever signed the transcript.

**4. Python fails with "unable to get local issuer certificate" while the browser works.** A missing intermediate (browsers fill the gap) or a corporate TLS-inspection root Python does not trust: check with `openssl s_client -showcerts`, fix the chain or add the root (`SSL_CERT_FILE`, `truststore`), never `verify=False`.

**5. Server-side sessions or JWTs?** Sessions revoke instantly but need a shared store; JWTs verify anywhere but cannot be recalled. Browsers get an `HttpOnly`, `Secure`, `SameSite=Lax`, `__Host-` session cookie at a backend-for-frontend; services get short-lived JWTs with rotating refresh tokens.

**6. How do you validate a JWT?** The checklist of 49b.4.3: my algorithm allow-list, the key by `kid` from the issuer's key set, the signature, then `iss`, `aud`, times with leeway, `typ`, and authorization from scopes; never `none`, never keys named by the token.

**7. Does `SameSite` solve CSRF?** Mostly, by withholding cookies from cross-site POSTs; but sibling subdomains are same-site, state-changing GETs stay exploitable and browsers differ, so keep anti-CSRF tokens and `Origin` or `Sec-Fetch-Site` checks.

**8. Why does a code, not a token, pass through the browser, and what does PKCE add?** The front channel leaks, so it carries only a short-lived single-use code redeemed on the back channel; PKCE binds that code to a verifier that never passes through the browser, which protects public clients without secrets.

**9. Access token versus ID token?** The access token is for the API and may be opaque to the client; the ID token is a JWT for the client saying who logged in, when, how and for which request (`nonce`). Never treat an access token as login; never send an ID token to an API.

**10. A customer wants SSO and automatic offboarding.** OIDC or SAML with their IdP on an immutable user id, verified domains, enforced SSO with break-glass admins, plus SCIM whose deactivation revokes sessions and tokens within minutes, all tested in staging (49b.8.4).

**11. How does a remote MCP server authorize a client?** As an OAuth resource server: its 401 points to protected resource metadata naming the authorization server; the client runs the code flow with PKCE and a `resource` parameter and checks `iss`; the server accepts only tokens issued for itself, never passes them upstream, and asks for more scopes with `insufficient_scope`.

**12. What does mTLS add, and what breaks?** Each connection is authenticated by a client key certified by a private CA, often with a SPIFFE ID; it breaks on manual rotation, missing intermediates, CA rollovers without overlapping trust, and proxies that forward identity unsafely.

**13. A container takes exactly 10 seconds to stop and loses its last log lines.** The program is PID 1 without a SIGTERM handler (or sits under a shell), so only Docker's SIGKILL stops it, and its logs sat in a pipe buffer; use exec-form `CMD`, a draining handler or `--init`, and flushed logging.

**14. Why might `set -euo pipefail` not stop a failing script?** `-e` is ignored in conditions, in non-final parts of `&&` and `||` lists and in functions called as conditions; `local x=$(cmd)` hides failures; and `pipefail` turns SIGPIPE from producers cut off by `head` into failures.

**15. When would you choose an LSM tree over a B-tree?** For write-heavy or append-mostly data — events, time series, embedding metadata — where ingest matters more than predictable reads; then explain the write path, Bloom filters, tombstones and the tiered-versus-leveled trade-off.

**Exercises**

1. Extend the lab's verifier to RS256 with `cryptography`, keeping the allow-list, and test that an HS256 token signed with the RSA public key's bytes is refused.
2. Add refresh-token rotation with reuse detection to `pkce.AuthorizationServer`, and test a stolen refresh token used after the client rotated.
3. Write an idempotent SCIM `PATCH /Users/{id}` handler that deactivates a user and ends their sessions.
4. Add snapshots to `LSMStore` and make compaction keep the newest version visible to each live snapshot; test with the randomized harness.
5. Make `mtls_demo.py` rotate its CA with an overlap period, then remove the old root.
6. Write a container entrypoint that traps SIGTERM, forwards it to the main process, waits up to 20 seconds and exits with the child's status; test it with `unshare --pid --fork`.

## Sources

- labuladong, Computer Science topics of the English table of contents (the list this chapter follows and extends): https://labuladong.online/en/algo/home/ and https://raw.githubusercontent.com/labuladong/fucking-algorithm/english/README.md (articles now under https://labuladong.online/en/fullstack/)
- OWASP Password Storage Cheat Sheet (checked October 2026): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html; NIST SP 800-63B-4 (31 July 2025): https://csrc.nist.gov/pubs/sp/800/63/b/4/final and https://pages.nist.gov/800-63-4/sp800-63b/
- NIST FIPS 203, 204 and 205 (13 August 2024): https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards; HQC selection: https://csrc.nist.gov/projects/post-quantum-cryptography; published FIPS (no FIPS 206 as of October 2026): https://csrc.nist.gov/publications/fips; FIPS 186-5 (EdDSA approved, February 2023): https://csrc.nist.gov/pubs/fips/186-5/final; SP 800-38D: https://csrc.nist.gov/pubs/sp/800/38/d/final; SP 800-57 Part 1 Rev. 5: https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- RFCs, each at https://www.rfc-editor.org/rfc/rfcNNNN: 2104 (HMAC), 4226 (HOTP), 5280 (X.509), 5869 (HKDF), 6238 (TOTP), 6265 (cookies), 6749 (OAuth 2.0), 6750 (bearer tokens), 6962 (Certificate Transparency), 6979 (deterministic ECDSA), 7009 (revocation), 7515 to 7519 (JOSE and JWT), 7636 (PKCE), 7643 and 7644 (SCIM), 7662 (introspection), 7748 (X25519), 8032 (EdDSA), 8414 (authorization server metadata), 8439 (ChaCha20-Poly1305), 8446 (TLS 1.3), 8448 (TLS 1.3 traces), 8452 (AES-GCM-SIV), 8470 (425 Too Early), 8555 (ACME), 8628 (device grant), 8693 (token exchange), 8705 (mTLS for OAuth), 8707 (resource indicators), 8725 (JWT BCP), 9068 (JWT access tokens), 9106 (Argon2), 9126 (PAR), 9207 (issuer identification), 9449 (DPoP), 9700 (OAuth Security BCP, January 2025), 9728 (protected resource metadata, April 2025), 9773 (ACME Renewal Information, June 2025), 9846 (TLS 1.3, July 2026), 9864 (fully-specified JOSE algorithms, October 2025), 10017 (OAuth 2.0 for Browser-Based Applications, BCP 212, August 2026), 10024 (hybrid ML-KEM key agreement for TLS 1.3, August 2026)
- IETF drafts, status checked October 2026: OAuth 2.1 https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/; JWT BCP update https://datatracker.ietf.org/doc/draft-ietf-oauth-rfc8725bis/; cookies https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/
- Post-quantum deployment: https://security.googleblog.com/2024/09/a-new-path-for-kyber-on-web.html; https://openssl-library.org/news/openssl-3.5-notes/; https://go.dev/doc/go1.24; https://support.apple.com/en-gb/122756; Cloudflare's 2025 review as reported by heise, https://heise.de/-11116190; key and signature sizes from Open Quantum Safe, https://openquantumsafe.org/liboqs/algorithms/kem/ml-kem.html and https://openquantumsafe.org/liboqs/algorithms/sig/ml-dsa.html
- SHAttered (2017): https://shattered.io/; MDN Set-Cookie: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie; Chromium SameSite updates: https://www.chromium.org/updates/same-site/
- PyJWT https://pyjwt.readthedocs.io/; Authlib https://docs.authlib.org/; pyca/cryptography https://cryptography.io/; W3C WebAuthn Level 3 (Recommendation, 25 August 2026) https://www.w3.org/TR/webauthn-3/; Zanzibar (USENIX ATC 2019) https://www.usenix.org/conference/atc19/presentation/pang
- OpenID Connect Core and Discovery 1.0: https://openid.net/specs/openid-connect-core-1_0.html and https://openid.net/specs/openid-connect-discovery-1_0.html; OASIS SAML 2.0: https://docs.oasis-open.org/security/saml/v2.0/
- Model Context Protocol specification 2026-07-28, Authorization, with its Authorization Server Discovery, Client Registration and Security Considerations pages: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
- CA/Browser Forum ballot SC-081v3 (11 April 2025): https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/; Baseline Requirements: https://github.com/cabforum/servercert/blob/main/docs/BR.md
- Let's Encrypt: https://letsencrypt.org/2025/08/06/ocsp-service-has-reached-end-of-life/; https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability/; https://letsencrypt.org/2025/12/02/from-90-to-45/; https://letsencrypt.org/2025/05/14/ending-tls-client-authentication/; the May 2026 profile changes: https://community.letsencrypt.org/t/upcoming-let-s-encrypt-profile-changes-on-may-13-20th-and-27th/247049
- Chrome CT policy https://googlechrome.github.io/CertificateTransparency/ct_policy.html; Apple CT policy https://support.apple.com/en-us/103214
- Python documentation for `ssl`, `hashlib`, `hmac`, `secrets`, `subprocess` and `os` (https://docs.python.org/3/library/), "What's New in Python 3.13" and "3.14" (https://docs.python.org/3/whatsnew/3.13.html, https://docs.python.org/3/whatsnew/3.14.html) and PEP 446 (https://peps.python.org/pep-0446/)
- SPIFFE https://spiffe.io/docs/latest/spiffe-about/overview/; Envoy `x-forwarded-client-cert` https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers
- Linux man pages (inode(7), proc(5), fork(2), execve(2), wait(2), signal(7), pid_namespaces(7), pipe(7), fsync(2)) https://man7.org/linux/man-pages/; GNU Bash manual https://www.gnu.org/software/bash/manual/bash.html; ShellCheck https://www.shellcheck.net/
- Docker `container stop` https://docs.docker.com/reference/cli/docker/container/stop/ and `docker run` https://github.com/docker/cli/blob/master/man/docker-run.1.md; Kubernetes, "Pod Lifecycle: Termination of Pods" (30-second default grace period) https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination; Google Cloud, "Kubernetes best practices: terminating with grace" https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace
- P. O'Neil et al., "The Log-Structured Merge-Tree", Acta Informatica 33(4), 1996; F. Chang et al., "Bigtable", OSDI 2006; B. H. Bloom, "Space/Time Trade-offs in Hash Coding with Allowable Errors", CACM 13(7), 1970; A. Kirsch and M. Mitzenmacher, "Less Hashing, Same Performance", ESA 2006; M. Athanassoulis et al., "Designing Access Methods: The RUM Conjecture", EDBT 2016
- LevelDB https://github.com/google/leveldb/blob/main/doc/impl.md; RocksDB https://github.com/facebook/rocksdb/wiki/Compaction and https://github.com/facebook/rocksdb/blob/main/USERS.md; Pebble https://www.cockroachlabs.com/blog/pebble-rocksdb-kv-store/; Cassandra https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/stcs.html, https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html and https://www.instaclustr.com/blog/apache-cassandra-5-0-improving-performance-with-unified-compaction-strategy/; ScyllaDB https://docs.scylladb.com/manual/master/cql/compaction.html; Weaviate https://docs.weaviate.io/weaviate/concepts/storage; Qdrant https://qdrant.tech/articles/gridstore-key-value-storage/; Prometheus https://prometheus.io/docs/prometheus/latest/storage/
- Code: `labs/cs-essentials/` in this repository (`jwt_hs256.py`, `pkce.py`, `tiny_lsm.py`, `mtls_demo.py`, `test_cs_essentials.py`, `check_chapter_sync.py`).
