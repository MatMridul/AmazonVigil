"""Alexa+ MCP authorization layer — OAuth 2.1 + PKCE (S256) + discovery metadata.

Implements the authorization requirements from Amazon's Alexa+ MCP Toolkit
QuickStart auth checklist so the Vigil MCP server can be account-linked by
Alexa+ (developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart):

* **Discovery**
  - Protected Resource Metadata (PRM) document per RFC 9728, served at
    ``/.well-known/oauth-protected-resource``.
  - Authorization Server metadata (RFC 8414) at
    ``/.well-known/oauth-authorization-server``; ``code_challenge_methods_supported``
    MUST be present and include ``S256`` (Alexa+ won't link without it).
  - Unauthenticated MCP requests return ``401`` (no ``WWW-Authenticate`` header —
    Alexa+ lists that header as "not supported yet").
* **Authorization** — OAuth 2.1 authorization-code flow with PKCE (S256); the
  ``resource`` parameter is bound to the server's canonical URI.
* **Token usage** — Bearer token in the ``Authorization`` header on every
  authenticated request; never in the query string.

This module is pure (no web framework) so it unit-tests in isolation; the ASGI
wiring in ``src/server.py`` imports these builders and validators. It is a
reference-grade local authorization server for the hackathon demo — tokens are
signed/opaque and stored in-memory; a production deployment swaps the store for
a real IdP. Nothing here is fabricated: the discovery documents and the PKCE
verification are the genuine protocol artifacts Alexa+ reads.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.store import KeyValueStore

# PKCE (RFC 7636) — Alexa+ requires the S256 method.
CODE_CHALLENGE_METHOD = "S256"
# Authorization-code TTL and access-token TTL (seconds).
AUTH_CODE_TTL = 300.0
ACCESS_TOKEN_TTL = 3600.0


def _b64url_no_pad(raw: bytes) -> str:
    """Base64url-encode without padding (RFC 7636 §A)."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def compute_s256_challenge(code_verifier: str) -> str:
    """Return the S256 code_challenge for a PKCE code_verifier (RFC 7636 §4.2)."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return _b64url_no_pad(digest)


def verify_pkce_s256(code_verifier: str, code_challenge: str) -> bool:
    """Constant-time verify that a code_verifier matches a stored S256 challenge."""
    if not code_verifier or not code_challenge:
        return False
    expected = compute_s256_challenge(code_verifier)
    return hmac.compare_digest(expected, code_challenge)


def build_prm_document(resource_uri: str, auth_server: str) -> dict:
    """Protected Resource Metadata document (RFC 9728).

    ``resource`` is the MCP server's canonical URI; ``authorization_servers``
    points Alexa+ at the AS metadata it must then fetch.
    """
    return {
        "resource": resource_uri,
        "authorization_servers": [auth_server],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["vigil.mesh"],
    }


def build_as_metadata(issuer: str) -> dict:
    """Authorization Server metadata (RFC 8414).

    ``code_challenge_methods_supported`` MUST include S256 or Alexa+ account
    linking will not proceed (per the Alexa+ auth checklist).
    """
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": [CODE_CHALLENGE_METHOD],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["vigil.mesh"],
    }


@dataclass
class _AuthCode:
    code_challenge: str
    resource: str
    scope: str
    created: float


@dataclass
class _AccessToken:
    resource: str
    scope: str
    created: float


@dataclass
class AuthorizationServer:
    """In-memory OAuth 2.1 + PKCE authorization server (reference-grade).

    Deliberately minimal and dependency-free. Enforces the two protocol
    guarantees Alexa+ checks: a PKCE S256 challenge is required at /authorize and
    verified at /token, and the ``resource`` parameter is bound end-to-end.
    """

    issuer: str
    resource_uri: str
    clock: Callable[[], float] = time.monotonic
    # B.3 — optional durable token store. When set, issued access tokens are
    # also written here with an ABSOLUTE wall-clock expiry, so a restart does not
    # drop live sessions. Auth CODES stay in-memory by design: they are single-
    # use and 5-min-lived, so surviving a restart buys nothing and adds risk.
    token_store: KeyValueStore | None = None
    wall_clock: Callable[[], float] = time.time
    _codes: dict[str, _AuthCode] = field(default_factory=dict)
    _tokens: dict[str, _AccessToken] = field(default_factory=dict)

    _TOKEN_NS = "oauth_token"  # noqa: S105 - KV namespace label, not a secret

    # --- discovery ---------------------------------------------------------- #
    def prm_document(self) -> dict:
        return build_prm_document(self.resource_uri, self.issuer)

    def as_metadata(self) -> dict:
        return build_as_metadata(self.issuer)

    # --- /authorize --------------------------------------------------------- #
    def authorize(
        self,
        *,
        code_challenge: str,
        code_challenge_method: str,
        resource: str,
        scope: str = "vigil.mesh",
    ) -> str:
        """Issue an authorization code. Requires PKCE S256 and a bound resource."""
        if code_challenge_method != CODE_CHALLENGE_METHOD:
            raise ValueError("code_challenge_method must be S256")
        if not code_challenge:
            raise ValueError("code_challenge is required (PKCE)")
        if resource != self.resource_uri:
            raise ValueError("resource must equal the server's canonical URI")
        code = secrets.token_urlsafe(32)
        self._codes[code] = _AuthCode(
            code_challenge=code_challenge,
            resource=resource,
            scope=scope,
            created=self.clock(),
        )
        return code

    # --- /token ------------------------------------------------------------- #
    def exchange_code(self, *, code: str, code_verifier: str, resource: str) -> dict:
        """Exchange an auth code + PKCE verifier for an access token."""
        entry = self._codes.get(code)
        if entry is None:
            raise ValueError("invalid_grant: unknown or used code")
        # Single-use.
        del self._codes[code]
        if self.clock() - entry.created > AUTH_CODE_TTL:
            raise ValueError("invalid_grant: code expired")
        if resource != entry.resource:
            raise ValueError("invalid_target: resource mismatch")
        if not verify_pkce_s256(code_verifier, entry.code_challenge):
            raise ValueError("invalid_grant: PKCE verification failed")
        token = secrets.token_urlsafe(32)
        self._tokens[token] = _AccessToken(
            resource=entry.resource, scope=entry.scope, created=self.clock()
        )
        # B.3 — persist with an absolute wall-clock expiry (monotonic would be
        # meaningless after a restart). validate_bearer re-reads this on a miss.
        if self.token_store is not None:
            self.token_store.put(
                self._TOKEN_NS,
                token,
                {
                    "resource": entry.resource,
                    "scope": entry.scope,
                    "expires_at": self.wall_clock() + ACCESS_TOKEN_TTL,
                },
            )
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": int(ACCESS_TOKEN_TTL),
            "scope": entry.scope,
        }

    # --- bearer validation (every authenticated request) -------------------- #
    def validate_bearer(self, authorization_header: str | None) -> bool:
        """True iff the Authorization header carries a valid, unexpired Bearer.

        Token must be in the header (never the query string), per the checklist.
        Checks the in-memory table first; on a miss (e.g. after a restart) falls
        back to the durable token store using an absolute wall-clock expiry.
        """
        if not authorization_header:
            return False
        parts = authorization_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return False
        token = parts[1]
        tok = self._tokens.get(token)
        if tok is not None:
            if self.clock() - tok.created > ACCESS_TOKEN_TTL:
                del self._tokens[token]
                return False
            return True
        # Not in memory — try the durable store (the restart case).
        if self.token_store is not None:
            rec = self.token_store.get(self._TOKEN_NS, token)
            if rec is None:
                return False
            if self.wall_clock() > rec.get("expires_at", 0.0):
                self.token_store.delete(self._TOKEN_NS, token)
                return False
            return True
        return False


def default_server() -> AuthorizationServer:
    """Build the AS from env (VIGIL_PUBLIC_URL), defaulting to the live tunnel.

    B.3: when VIGIL_STATE_DB is set, issued tokens are persisted (wall-clock
    expiry) so a restart does not log live sessions out; else in-memory only.
    """
    public = os.environ.get(
        "VIGIL_PUBLIC_URL", "https://thermal-entire-sandbank.ngrok-free.dev"
    ).rstrip("/")
    token_store = None
    db_path = os.environ.get("VIGIL_STATE_DB", "").strip()
    if db_path:
        from src.store import SqliteKV

        token_store = SqliteKV(db_path)
    return AuthorizationServer(issuer=public, resource_uri=f"{public}/mcp", token_store=token_store)


# --------------------------------------------------------------------------- #
# SEC.1 — deny-by-default bearer enforcement for the MCP endpoint.
# --------------------------------------------------------------------------- #
# Paths that are intentionally public (discovery is fetched BEFORE a token
# exists, and the health check must be unauthenticated). Everything else under
# the MCP mount requires a valid Bearer token — enforced at the transport layer
# so no tool can be reached unauthenticated, rather than relying on each of the
# 8 tool bodies to remember to check (OWASP #1, the top AI-code failure mode).
_PUBLIC_PREFIXES = (
    "/.well-known/",
    "/healthz",
)


# Enforcement is ON by default. Set VIGIL_AUTH_ENFORCE=0 ONLY for local offline
# dev/tests against the in-memory AS; a field deployment must never set it.
def auth_enforced() -> bool:
    return os.environ.get("VIGIL_AUTH_ENFORCE", "1").strip() not in ("0", "false", "False")


def _is_public_path(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in _PUBLIC_PREFIXES)


class BearerAuthMiddleware:
    """ASGI middleware enforcing a valid Bearer on every non-public request.

    Deny-by-default: an unauthenticated call to the MCP endpoint (and thus any
    tool) gets ``401`` before it ever reaches a tool body. Discovery and health
    paths are explicitly allow-listed because they are fetched before a token
    exists. The token is read ONLY from the Authorization header, never a query
    string (per the Alexa+ checklist and OWASP crypto guidance).
    """

    def __init__(self, app, server: AuthorizationServer | None = None) -> None:
        self.app = app
        self._server = server or default_server()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not auth_enforced():
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if _is_public_path(path):
            await self.app(scope, receive, send)
            return
        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])
        }
        if self._server.validate_bearer(headers.get("authorization")):
            await self.app(scope, receive, send)
            return
        # 401 — no WWW-Authenticate header (Alexa+ lists it "not supported yet").
        from src.audit_log import audit

        audit(
            "auth.denied",
            outcome="denied",
            path=path,
            client=headers.get("x-forwarded-for") or "unknown",
        )
        body = b'{"error":"unauthorized","error_description":"valid Bearer token required"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


# --------------------------------------------------------------------------- #
# Rate limiting — throttle brute-force / DoS on the sensitive endpoints.
# --------------------------------------------------------------------------- #
# A fixed-window counter per client key. Deliberately simple and dependency-free
# (no Redis); a field deployment behind multiple workers moves this to a shared
# store, but for a single-process edge node this defeats a trivial flood of
# /authorize, /token, and /mcp calls. Complements SEC.2's per-PIN lockout with a
# per-CLIENT request cap.
_RATE_LIMIT_MAX = 60  # requests...
_RATE_LIMIT_WINDOW = 60.0  # ...per this many seconds, per client key


class RateLimiter:
    """Thread-safe fixed-window request counter keyed by an arbitrary string."""

    def __init__(
        self,
        max_requests: int = _RATE_LIMIT_MAX,
        window_seconds: float = _RATE_LIMIT_WINDOW,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """True if ``key`` is under its cap for the current window, else False."""
        now = self._clock()
        with self._lock:
            window_start, count = self._hits.get(key, (now, 0))
            if now - window_start >= self._window:
                window_start, count = now, 0  # new window
            count += 1
            self._hits[key] = (window_start, count)
            return count <= self._max


# Paths that get rate-limited (the sensitive auth + tool surfaces).
_RATE_LIMITED_PREFIXES = ("/authorize", "/token", "/mcp")


def _client_key(scope) -> str:
    headers = {
        k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])
    }
    fwd = headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """ASGI middleware returning 429 when a client exceeds its request budget.

    Applies only to the sensitive auth/tool prefixes so discovery/health are
    never throttled. Keyed by client IP (X-Forwarded-For first hop when present).
    """

    def __init__(self, app, limiter: RateLimiter | None = None) -> None:
        self.app = app
        self._limiter = limiter or RateLimiter()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if any(path.startswith(p) for p in _RATE_LIMITED_PREFIXES):
            if not self._limiter.allow(_client_key(scope)):
                from src.audit_log import audit

                audit(
                    "rate_limit.throttled",
                    outcome="throttled",
                    path=path,
                    client=_client_key(scope),
                )
                body = b'{"error":"rate_limited","error_description":"too many requests"}'
                await send(
                    {
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode("ascii")),
                            (b"retry-after", b"60"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return
        await self.app(scope, receive, send)


# --------------------------------------------------------------------------- #
# SEC.2/SEC.3 — stored-PIN verification with brute-force lockout.
# --------------------------------------------------------------------------- #
# The disarm PIN is verified by VALUE against a stored secret, never by format
# alone, and the stored form is a hash (Argon2 in the field; a sha256 fallback
# here keeps the module dependency-free for local dev — swapped in SEC.3). A
# 4-digit space is only 10k combos, so attempts are rate-limited with lockout.
_PIN_MAX_ATTEMPTS = 5
_PIN_LOCKOUT_SECONDS = 300.0


def hash_pin(pin: str, *, salt: str | None = None) -> str:
    """Hash a disarm PIN for storage. Never store the plaintext PIN.

    Dev-grade salted SHA-256 so the module stays dependency-free; SEC.3 swaps
    this for Argon2 (argon2-cffi) without changing callers.
    """
    s = salt or os.environ.get("VIGIL_PIN_SALT", "vigil-dev-salt")
    return hashlib.sha256(f"{s}:{pin}".encode()).hexdigest()


@dataclass
class PinVerifier:
    """Value-checked, lockout-protected disarm-PIN verifier (SEC.2).

    Holds only the HASH of the real PIN. Counts consecutive failures and locks
    out for a cooldown after ``max_attempts``, defeating a trivial brute force
    of the 10k 4-digit space.
    """

    pin_hash: str
    max_attempts: int = _PIN_MAX_ATTEMPTS
    lockout_seconds: float = _PIN_LOCKOUT_SECONDS
    clock: Callable[[], float] = time.monotonic
    _failures: int = 0
    _locked_until: float = 0.0

    def is_locked(self) -> bool:
        return self.clock() < self._locked_until

    def verify(self, pin: str) -> bool:
        """True iff ``pin`` matches the stored hash and we are not locked out."""
        if self.is_locked():
            return False
        if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
            self._register_failure()
            return False
        ok = hmac.compare_digest(hash_pin(pin), self.pin_hash)
        if ok:
            self._failures = 0
            return True
        self._register_failure()
        return False

    def _register_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.max_attempts:
            self._locked_until = self.clock() + self.lockout_seconds
            self._failures = 0


def default_pin_verifier() -> PinVerifier:
    """Build the disarm-PIN verifier from a stored hash (never a literal).

    Reads VIGIL_DISARM_PIN_HASH (preferred). For local dev only, if a raw
    VIGIL_DISARM_PIN is set it is hashed in-process so no plaintext is stored.
    """
    stored = os.environ.get("VIGIL_DISARM_PIN_HASH", "").strip()
    if not stored:
        raw = os.environ.get("VIGIL_DISARM_PIN", "").strip()
        if raw:
            stored = hash_pin(raw)
    if not stored:
        # No PIN configured: a verifier that rejects everything (fail-closed),
        # never a default literal like "1234".
        stored = hash_pin(secrets.token_hex(8))
    return PinVerifier(pin_hash=stored)
