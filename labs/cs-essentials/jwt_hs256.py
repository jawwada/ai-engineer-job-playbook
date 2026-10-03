"""HS256 JSON Web Tokens with the standard library: signing, and a verifier that makes every check a
production verifier makes (chapter 49b.4).

This is teaching code. Production services use a maintained library such as PyJWT or Authlib, configured
with an explicit algorithm list, issuer, audience and required claims; the checks below show what those
options do.

    token = sign({"sub": "user-42", "iss": ISS, "aud": AUD, "iat": now, "exp": now + 300}, key)
    claims = verify(token, key, issuer=ISS, audience=AUD)
"""
import base64
import hashlib
import hmac
import json
import math
import re
import secrets
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


def issue(subject: str, key: bytes, *, issuer: str, audience: str, ttl: int = 300,
          now: float | None = None, kid: str | None = None, **extra) -> str:
    """Mint a short-lived token with the registered claims a verifier should require."""
    now = int(time.time() if now is None else now)
    claims = {"iss": issuer, "sub": subject, "aud": audience, "iat": now, "nbf": now,
              "exp": now + ttl, "jti": secrets.token_urlsafe(16), **extra}
    return sign(claims, key, kid=kid)


if __name__ == "__main__":
    demo_key = secrets.token_bytes(32)
    demo = issue("user-42", demo_key, issuer="https://auth.example.com", audience="orders-api",
                 scope="orders:read")
    print(demo)
    print(verify(demo, demo_key, issuer="https://auth.example.com", audience="orders-api"))
