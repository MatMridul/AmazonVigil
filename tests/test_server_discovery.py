"""Tests that the MCP server's composed ASGI app serves Alexa+ OAuth discovery
endpoints (src/server.py build_asgi_app) without breaking the MCP transport."""

from __future__ import annotations

from starlette.testclient import TestClient

from src.server import build_asgi_app


def _client() -> TestClient:
    return TestClient(build_asgi_app())


def test_prm_endpoint_served():
    r = _client().get("/.well-known/oauth-protected-resource")
    assert r.status_code == 200
    body = r.json()
    assert body["resource"].endswith("/mcp")
    assert body["authorization_servers"]
    assert body["bearer_methods_supported"] == ["header"]


def test_as_metadata_endpoint_served_with_s256():
    r = _client().get("/.well-known/oauth-authorization-server")
    assert r.status_code == 200
    body = r.json()
    # The load-bearing Alexa+ requirement.
    assert "S256" in body["code_challenge_methods_supported"]
    assert body["authorization_endpoint"].endswith("/authorize")
    assert body["token_endpoint"].endswith("/token")


def test_mcp_endpoint_still_mounted():
    # The MCP transport is still mounted alongside the discovery routes.
    # We assert the /mcp route is REGISTERED rather than driving it through
    # TestClient: the streamable-http transport needs its lifespan/task-group
    # started by a real server (uvicorn) — driving it via TestClient without
    # that raises RuntimeError, which is a harness limitation, not a server
    # defect (the live tunnel handshake already proves /mcp works end to end).
    app = build_asgi_app()
    paths = {getattr(r, "path", None) for r in app.router.routes}
    assert "/.well-known/oauth-protected-resource" in paths
    assert "/.well-known/oauth-authorization-server" in paths
    # The mounted MCP app is present (path "/mcp" mounted by FastMCP).
    mounted = any("/mcp" in str(getattr(r, "path", "")) for r in app.router.routes)
    assert mounted
