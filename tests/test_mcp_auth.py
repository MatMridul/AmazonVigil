"""Tests for the Alexa+ MCP authorization layer (src/mcp_auth.py).

Proves each Alexa+ auth-checklist requirement in code:
PKCE S256, discovery metadata with S256, bound resource, bearer validation.
"""

from __future__ import annotations

import pytest

from src.mcp_auth import (
    AuthorizationServer,
    build_as_metadata,
    build_prm_document,
    compute_s256_challenge,
    verify_pkce_s256,
)

RES = "https://example.test/mcp"
ISS = "https://example.test"


def _server() -> AuthorizationServer:
    # Deterministic clock so TTL tests are exact.
    clock = iter([float(i) for i in range(0, 100000, 1)])
    return AuthorizationServer(issuer=ISS, resource_uri=RES, clock=lambda: next(clock))


# --- PKCE S256 (RFC 7636) ------------------------------------------------- #

def test_pkce_s256_roundtrip_matches():
    verifier = "a" * 64
    challenge = compute_s256_challenge(verifier)
    assert verify_pkce_s256(verifier, challenge) is True


def test_pkce_rejects_wrong_verifier():
    challenge = compute_s256_challenge("correct-verifier-correct-verifier-xx")
    assert verify_pkce_s256("wrong-verifier", challenge) is False


def test_pkce_rejects_empty():
    assert verify_pkce_s256("", "x") is False
    assert verify_pkce_s256("x", "") is False


# --- Discovery metadata --------------------------------------------------- #

def test_prm_document_shape():
    doc = build_prm_document(RES, ISS)
    assert doc["resource"] == RES
    assert ISS in doc["authorization_servers"]
    assert doc["bearer_methods_supported"] == ["header"]


def test_as_metadata_requires_s256():
    # The load-bearing Alexa+ requirement: S256 must be advertised.
    meta = build_as_metadata(ISS)
    assert "S256" in meta["code_challenge_methods_supported"]
    assert meta["issuer"] == ISS
    assert meta["authorization_endpoint"].endswith("/authorize")
    assert meta["token_endpoint"].endswith("/token")


# --- Full OAuth 2.1 + PKCE flow ------------------------------------------- #

def test_full_authorization_code_pkce_flow():
    srv = _server()
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    challenge = compute_s256_challenge(verifier)

    code = srv.authorize(
        code_challenge=challenge, code_challenge_method="S256", resource=RES
    )
    token_resp = srv.exchange_code(code=code, code_verifier=verifier, resource=RES)

    assert token_resp["token_type"] == "Bearer"
    assert token_resp["access_token"]
    assert srv.validate_bearer(f"Bearer {token_resp['access_token']}") is True


def test_authorize_rejects_non_s256_method():
    srv = _server()
    with pytest.raises(ValueError):
        srv.authorize(code_challenge="x", code_challenge_method="plain", resource=RES)


def test_authorize_binds_resource():
    srv = _server()
    with pytest.raises(ValueError):
        srv.authorize(
            code_challenge="x", code_challenge_method="S256",
            resource="https://evil.test/mcp",
        )


def test_token_exchange_rejects_bad_pkce():
    srv = _server()
    challenge = compute_s256_challenge("the-real-verifier-the-real-verifier-x")
    code = srv.authorize(
        code_challenge=challenge, code_challenge_method="S256", resource=RES
    )
    with pytest.raises(ValueError):
        srv.exchange_code(code=code, code_verifier="not-the-verifier", resource=RES)


def test_token_exchange_rejects_resource_mismatch():
    srv = _server()
    verifier = "v" * 48
    code = srv.authorize(
        code_challenge=compute_s256_challenge(verifier),
        code_challenge_method="S256", resource=RES,
    )
    with pytest.raises(ValueError):
        srv.exchange_code(code=code, code_verifier=verifier,
                          resource="https://evil.test/mcp")


def test_auth_code_is_single_use():
    srv = _server()
    verifier = "v" * 48
    code = srv.authorize(
        code_challenge=compute_s256_challenge(verifier),
        code_challenge_method="S256", resource=RES,
    )
    srv.exchange_code(code=code, code_verifier=verifier, resource=RES)
    with pytest.raises(ValueError):
        srv.exchange_code(code=code, code_verifier=verifier, resource=RES)


# --- Bearer validation ---------------------------------------------------- #

def test_bearer_rejects_missing_and_malformed():
    srv = _server()
    assert srv.validate_bearer(None) is False
    assert srv.validate_bearer("") is False
    assert srv.validate_bearer("Basic abc") is False
    assert srv.validate_bearer("Bearer") is False
    assert srv.validate_bearer("Bearer unknown-token") is False
