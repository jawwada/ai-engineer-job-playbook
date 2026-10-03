"""PKCE (RFC 7636) for the OAuth 2.0 authorization code flow, plus a tiny in-memory authorization server that
enforces it, so the attack PKCE stops can be run as a test (chapter 49b.7).

Client side: make_code_verifier() once per authorization request, send s256_challenge(verifier) in the
authorization request, keep the verifier, and send it in the token request. Server side:
verify_code_verifier(). Production code uses the OAuth client of a maintained library (Authlib, or the
identity provider's SDK), which does exactly this.
"""
import base64
import hashlib
import hmac
import re
import secrets
import time
import urllib.parse

_VERIFIER = re.compile(r"[A-Za-z0-9\-._~]{43,128}")   # RFC 7636 section 4.1: unreserved characters
_CHALLENGE = re.compile(r"[A-Za-z0-9_-]{43}")          # base64url of a SHA-256 digest, no padding


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


def authorization_url(endpoint: str, *, client_id: str, redirect_uri: str, scope: str, state: str,
                      code_challenge: str, resource: str | None = None, nonce: str | None = None) -> str:
    """The front-channel request the client sends the browser to. Only the challenge travels here."""
    params = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
              "scope": scope, "state": state, "code_challenge": code_challenge,
              "code_challenge_method": "S256"}
    if resource is not None:
        params["resource"] = resource                  # RFC 8707: the API the token is for
    if nonce is not None:
        params["nonce"] = nonce                        # OpenID Connect: echoed in the ID token
    return endpoint + "?" + urllib.parse.urlencode(params)


class AuthorizationServer:
    """An in-memory authorization and token endpoint that enforces exact redirect URIs, single-use
    short-lived codes bound to the client, and PKCE with S256. For tests and demonstrations only."""

    CODE_TTL = 60

    def __init__(self, clients: dict, *, clock=time.time):
        self.clients = clients                         # client_id -> list of registered redirect URIs
        self.clock = clock
        self._codes = {}
        self._tokens = {}

    def authorize(self, *, client_id: str, redirect_uri: str, code_challenge: str,
                  code_challenge_method: str = "S256", scope: str = "", user: str = "alice") -> str:
        """Called after the user has logged in and consented. Returns the code put in the redirect."""
        if redirect_uri not in self.clients.get(client_id, ()):
            raise ValueError("unknown client or redirect URI")    # show an error page, never redirect
        if code_challenge_method != "S256" or not _CHALLENGE.fullmatch(code_challenge):
            raise ValueError("an S256 code challenge is required")
        code = secrets.token_urlsafe(32)
        self._codes[code] = {"client_id": client_id, "redirect_uri": redirect_uri, "user": user,
                             "challenge": code_challenge, "scope": scope, "used": False,
                             "expires": self.clock() + self.CODE_TTL, "tokens": []}
        return code

    def token(self, *, code: str, client_id: str, redirect_uri: str, code_verifier: str) -> str:
        """The back-channel token request. Raises PermissionError("invalid_grant") on any failure."""
        grant = self._codes.get(code)
        if grant is None:
            raise PermissionError("invalid_grant")
        if grant["used"]:                              # replay: revoke what the first use produced
            for token in grant["tokens"]:
                self._tokens.pop(token, None)
            raise PermissionError("invalid_grant")
        grant["used"] = True                           # the first redemption attempt consumes the code
        if (self.clock() > grant["expires"] or grant["client_id"] != client_id
                or grant["redirect_uri"] != redirect_uri
                or not verify_code_verifier(code_verifier, grant["challenge"])):
            raise PermissionError("invalid_grant")
        access_token = secrets.token_urlsafe(32)
        self._tokens[access_token] = {"sub": grant["user"], "scope": grant["scope"],
                                      "client_id": client_id}
        grant["tokens"].append(access_token)
        return access_token

    def introspect(self, token: str) -> dict:
        """RFC 7662 style: {"active": false} for anything unknown, expired or revoked."""
        info = self._tokens.get(token)
        return {"active": False} if info is None else {"active": True, **info}


if __name__ == "__main__":
    verifier = make_code_verifier()
    print("verifier ", verifier)
    print("challenge", s256_challenge(verifier))
    print(authorization_url("https://auth.example.com/authorize", client_id="cli-app",
                            redirect_uri="http://127.0.0.1:8765/callback", scope="openid tickets:read",
                            state=secrets.token_urlsafe(16), code_challenge=s256_challenge(verifier)))
