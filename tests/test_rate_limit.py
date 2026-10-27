"""Rate-limiting tests (Phase C hardening) — throttle brute-force / DoS.

Proves the fixed-window limiter caps requests per client per window and resets
on a new window, and that the middleware returns 429 on a sensitive path once
the cap is exceeded while leaving discovery/health untouched.
"""

from __future__ import annotations

import pytest

from src.mcp_auth import RateLimiter, RateLimitMiddleware


def test_limiter_allows_up_to_cap_then_blocks():
    clk = {"t": 0.0}
    rl = RateLimiter(max_requests=3, window_seconds=60.0, clock=lambda: clk["t"])
    assert [rl.allow("ip1") for _ in range(3)] == [True, True, True]
    assert rl.allow("ip1") is False  # 4th in the window is blocked


def test_limiter_resets_next_window():
    clk = {"t": 0.0}
    rl = RateLimiter(max_requests=2, window_seconds=60.0, clock=lambda: clk["t"])
    assert rl.allow("ip1") is True
    assert rl.allow("ip1") is True
    assert rl.allow("ip1") is False
    clk["t"] = 61.0  # new window
    assert rl.allow("ip1") is True


def test_limiter_keys_are_independent():
    clk = {"t": 0.0}
    rl = RateLimiter(max_requests=1, window_seconds=60.0, clock=lambda: clk["t"])
    assert rl.allow("ip1") is True
    assert rl.allow("ip2") is True  # different client, own budget
    assert rl.allow("ip1") is False


class _Recorder:
    def __init__(self) -> None:
        self.reached = False

    async def __call__(self, scope, receive, send) -> None:
        self.reached = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def _scope(path: str, client_ip: str = "1.2.3.4") -> dict:
    return {"type": "http", "path": path, "headers": [], "client": (client_ip, 5555)}


async def _status(mw, scope) -> int:
    code = {"v": None}

    async def send(msg):
        if msg["type"] == "http.response.start":
            code["v"] = msg["status"]

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    await mw(scope, receive, send)
    return code["v"]


@pytest.mark.asyncio
async def test_middleware_429_after_cap_on_sensitive_path():
    clk = {"t": 0.0}
    limiter = RateLimiter(max_requests=2, window_seconds=60.0, clock=lambda: clk["t"])
    downstream = _Recorder()
    mw = RateLimitMiddleware(downstream, limiter=limiter)

    assert await _status(mw, _scope("/mcp")) == 200
    assert await _status(mw, _scope("/mcp")) == 200
    assert await _status(mw, _scope("/mcp")) == 429  # over cap


@pytest.mark.asyncio
async def test_middleware_does_not_throttle_discovery():
    clk = {"t": 0.0}
    limiter = RateLimiter(max_requests=1, window_seconds=60.0, clock=lambda: clk["t"])
    mw = RateLimitMiddleware(_Recorder(), limiter=limiter)
    # Hammer a public path well past the cap — never throttled.
    for _ in range(5):
        assert await _status(mw, _scope("/.well-known/oauth-authorization-server")) == 200
