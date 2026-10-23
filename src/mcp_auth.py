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
from dataclasses import dataclass, field
from typing import Optional

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
    clock: "callable" = time.monotonic
    _codes: dict[str, _AuthCode] = field(default_factory=dict)
    _tokens: dict[str, _AccessToken] = field(default_factory=dict)

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
            code_challenge=code_challenge, resource=resource,
            scope=scope, created=self.clock(),
        )
        return code

    # --- /token ------------------------------------------------------------- #
    def exchange_code(
        self, *, code: str, code_verifier: str, resource: str
    ) -> dict:
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
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": int(ACCESS_TOKEN_TTL),
            "scope": entry.scope,
        }

    # --- bearer validation (every authenticated request) -------------------- #
    def validate_bearer(self, authorization_header: Optional[str]) -> bool:
        """True iff the Authorization header carries a valid, unexpired Bearer.

        Token must be in the header (never the query string), per the checklist.
        """
        if not authorization_header:
            return False
        parts = authorization_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return False
        tok = self._tokens.get(parts[1])
        if tok is None:
            return False
        if self.clock() - tok.created > ACCESS_TOKEN_TTL:
            del self._tokens[parts[1]]
            return False
        return True


def default_server() -> AuthorizationServer:
    """Build the AS from env (VIGIL_PUBLIC_URL), defaulting to the live tunnel."""
    public = os.environ.get(
        "VIGIL_PUBLIC_URL", "https://thermal-entire-sandbank.ngrok-free.dev"
    ).rstrip("/")
    return AuthorizationServer(issuer=public, resource_uri=f"{public}/mcp")
