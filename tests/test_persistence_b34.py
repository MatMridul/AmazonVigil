"""Phase B.3/B.4 persistence tests — tokens and guard profile survive a restart.

B.3: a token issued by one AuthorizationServer (with a durable token store) is
     still valid for a FRESH server instance on the same store — the restart
     case — and a token past its wall-clock expiry is rejected.
B.4: the active guard profile persists across a fresh profile-store instance.
"""

from __future__ import annotations

import pytest

from src.mcp_auth import ACCESS_TOKEN_TTL, AuthorizationServer, compute_s256_challenge
from src.store import InMemoryKV, SqliteKV
from src.store.kv_store import KeyValueStore

RES = "https://example.test/mcp"
ISS = "https://example.test"


@pytest.fixture(params=["memory", "sqlite"])
def kv(request, tmp_path) -> KeyValueStore:
    if request.param == "memory":
        return InMemoryKV()
    return SqliteKV(tmp_path / "kv.db")


# --- KV parity ------------------------------------------------------------ #


def test_kv_put_get(kv):
    kv.put("ns", "k", {"v": 1})
    assert kv.get("ns", "k") == {"v": 1}


def test_kv_namespaces_isolate(kv):
    kv.put("a", "k", {"v": 1})
    kv.put("b", "k", {"v": 2})
    assert kv.get("a", "k") == {"v": 1}
    assert kv.get("b", "k") == {"v": 2}


def test_kv_delete_and_keys(kv):
    kv.put("ns", "k1", {"v": 1})
    kv.put("ns", "k2", {"v": 2})
    assert set(kv.keys("ns")) == {"k1", "k2"}
    kv.delete("ns", "k1")
    assert kv.get("ns", "k1") is None


# --- B.3: token survives a restart ---------------------------------------- #


def _issue_token(srv: AuthorizationServer) -> str:
    verifier = "v" * 48
    code = srv.authorize(
        code_challenge=compute_s256_challenge(verifier),
        code_challenge_method="S256",
        resource=RES,
    )
    return srv.exchange_code(code=code, code_verifier=verifier, resource=RES)["access_token"]


def test_token_survives_restart(tmp_path):
    store = SqliteKV(tmp_path / "tokens.db")
    wall = {"t": 1000.0}

    srv1 = AuthorizationServer(
        issuer=ISS, resource_uri=RES, token_store=store, wall_clock=lambda: wall["t"]
    )
    token = _issue_token(srv1)
    assert srv1.validate_bearer(f"Bearer {token}") is True

    # Fresh instance (restart) on the same store — empty in-memory table, but the
    # durable store still holds the live token.
    srv2 = AuthorizationServer(
        issuer=ISS, resource_uri=RES, token_store=store, wall_clock=lambda: wall["t"]
    )
    assert srv2.validate_bearer(f"Bearer {token}") is True, "token did not survive restart"


def test_persisted_token_expires_by_wall_clock(tmp_path):
    store = SqliteKV(tmp_path / "tokens.db")
    wall = {"t": 1000.0}
    srv1 = AuthorizationServer(
        issuer=ISS, resource_uri=RES, token_store=store, wall_clock=lambda: wall["t"]
    )
    token = _issue_token(srv1)

    # Advance wall clock past the TTL, then restart: the token must be rejected.
    wall["t"] = 1000.0 + ACCESS_TOKEN_TTL + 1.0
    srv2 = AuthorizationServer(
        issuer=ISS, resource_uri=RES, token_store=store, wall_clock=lambda: wall["t"]
    )
    assert srv2.validate_bearer(f"Bearer {token}") is False


def test_no_store_means_no_restart_survival():
    # Default (no token_store): a fresh server does not know an old token.
    srv1 = AuthorizationServer(issuer=ISS, resource_uri=RES)
    token = _issue_token(srv1)
    srv2 = AuthorizationServer(issuer=ISS, resource_uri=RES)
    assert srv2.validate_bearer(f"Bearer {token}") is False


# --- B.4: guard profile survives a restart -------------------------------- #


def test_guard_profile_survives_restart(tmp_path):
    db = tmp_path / "profile.db"
    s1 = SqliteKV(db)
    s1.put("guard_profile", "active", {"mode": "vacation", "duration_hours": 72})
    del s1

    s2 = SqliteKV(db)
    rec = s2.get("guard_profile", "active")
    assert rec is not None, "guard profile did not survive restart"
    assert rec["mode"] == "vacation"
    assert rec["duration_hours"] == 72
