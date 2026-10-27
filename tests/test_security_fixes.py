"""SEC.1 + SEC.2 regression tests — the two real holes closed this session.

SEC.1: deny-by-default bearer enforcement — an unauthenticated request to the
       MCP endpoint is rejected; discovery/health stay public.
SEC.2: the disarm PIN is verified by VALUE against a stored hash, with
       brute-force lockout — a wrong 4-digit guess does NOT disarm.
"""

from __future__ import annotations

import itertools

import pytest

from src.mcp_auth import (
    AuthorizationServer,
    BearerAuthMiddleware,
    PinVerifier,
    _is_public_path,
    compute_s256_challenge,
    hash_pin,
)

RES = "https://example.test/mcp"
ISS = "https://example.test"


def _server() -> AuthorizationServer:
    clock = (float(i) for i in itertools.count())
    return AuthorizationServer(issuer=ISS, resource_uri=RES, clock=lambda: next(clock))


def _valid_bearer(srv: AuthorizationServer) -> str:
    verifier = "v" * 48
    code = srv.authorize(
        code_challenge=compute_s256_challenge(verifier),
        code_challenge_method="S256",
        resource=RES,
    )
    tok = srv.exchange_code(code=code, code_verifier=verifier, resource=RES)
    return f"Bearer {tok['access_token']}"


# --------------------------------------------------------------------------- #
# SEC.1 — authorization guard
# --------------------------------------------------------------------------- #


class _Recorder:
    """Minimal ASGI downstream that records whether it was reached."""

    def __init__(self) -> None:
        self.reached = False

    async def __call__(self, scope, receive, send) -> None:
        self.reached = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def _scope(path: str, *, auth: str | None = None) -> dict:
    headers = []
    if auth is not None:
        headers.append((b"authorization", auth.encode("latin-1")))
    return {"type": "http", "path": path, "headers": headers}


async def _drive(mw: BearerAuthMiddleware, scope: dict) -> int:
    status = {"code": None}

    async def send(msg):
        if msg["type"] == "http.response.start":
            status["code"] = msg["status"]

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    await mw(scope, receive, send)
    return status["code"]


@pytest.mark.asyncio
async def test_unauthenticated_mcp_call_is_rejected(monkeypatch):
    monkeypatch.setenv("VIGIL_AUTH_ENFORCE", "1")
    srv = _server()
    downstream = _Recorder()
    mw = BearerAuthMiddleware(downstream, server=srv)

    code = await _drive(mw, _scope("/mcp"))
    assert code == 401
    assert downstream.reached is False  # never reached a tool


@pytest.mark.asyncio
async def test_valid_bearer_passes_through(monkeypatch):
    monkeypatch.setenv("VIGIL_AUTH_ENFORCE", "1")
    srv = _server()
    downstream = _Recorder()
    mw = BearerAuthMiddleware(downstream, server=srv)

    code = await _drive(mw, _scope("/mcp", auth=_valid_bearer(srv)))
    assert code == 200
    assert downstream.reached is True


@pytest.mark.asyncio
async def test_discovery_and_health_stay_public(monkeypatch):
    monkeypatch.setenv("VIGIL_AUTH_ENFORCE", "1")
    srv = _server()
    downstream = _Recorder()
    mw = BearerAuthMiddleware(downstream, server=srv)

    for path in (
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-authorization-server",
        "/healthz",
    ):
        downstream.reached = False
        code = await _drive(mw, _scope(path))
        assert code == 200, path
        assert downstream.reached is True, path


def test_public_path_allowlist_is_tight():
    assert _is_public_path("/.well-known/oauth-protected-resource")
    assert _is_public_path("/healthz")
    assert not _is_public_path("/mcp")
    assert not _is_public_path("/")  # root is NOT public


# --------------------------------------------------------------------------- #
# SEC.2 — value-checked PIN with lockout
# --------------------------------------------------------------------------- #


def test_correct_pin_disarms():
    v = PinVerifier(pin_hash=hash_pin("8391"))
    assert v.verify("8391") is True


def test_wrong_pin_rejected_even_with_valid_format():
    v = PinVerifier(pin_hash=hash_pin("8391"))
    assert v.verify("1234") is False  # valid shape, wrong value


def test_lockout_after_max_attempts():
    clk = {"t": 0.0}
    v = PinVerifier(
        pin_hash=hash_pin("8391"), max_attempts=5, lockout_seconds=300.0, clock=lambda: clk["t"]
    )
    for _ in range(5):
        assert v.verify("0000") is False
    assert v.is_locked() is True
    # Even the CORRECT pin is refused while locked out.
    assert v.verify("8391") is False
    # After the cooldown elapses, the correct pin works again.
    clk["t"] = 301.0
    assert v.is_locked() is False
    assert v.verify("8391") is True


def test_no_plaintext_pin_stored():
    v = PinVerifier(pin_hash=hash_pin("8391"))
    assert "8391" not in v.pin_hash
    assert len(v.pin_hash) == 64  # sha256 hex


# --------------------------------------------------------------------------- #
# SEC.9 — audit logging redacts secrets
# --------------------------------------------------------------------------- #


def test_audit_redacts_secret_fields(caplog):
    import logging

    from src.audit_log import audit

    with caplog.at_level(logging.INFO, logger="vigil.audit"):
        audit(
            "disarm.attempt",
            outcome="invalid_pin",
            pin="8391",
            token="secret-bearer",
            incident_id="INC-9",
        )

    line = caplog.records[-1].getMessage()
    # The event + safe context are present…
    assert "disarm.attempt" in line
    assert "INC-9" in line
    # …but the secret-bearing fields are redacted, never emitted in the clear.
    assert "8391" not in line
    assert "secret-bearer" not in line
    assert "***" in line
