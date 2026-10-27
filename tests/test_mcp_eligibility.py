"""Alexa+ MCP eligibility tests (primary track gate).

The hackathon rule: the repo must ACTUALLY call the track's tech in code
(import / entry point / loaded config), not just mention it. These tests
exercise the genuine ``mcp`` SDK — they fail if the server is a mock or the
tools are not really registered on the official FastMCP object — and confirm
the real Streamable HTTP (spec 2025-11-25+) transport app constructs.

They do NOT require a live Echo or Alexa+ account (that wiring is a human step);
they prove the server is a real, reachable MCP endpoint ready for it.
"""

from __future__ import annotations

import asyncio

CANONICAL_TOOLS = {
    "audit_perimeter_event",
    "query_wearer_state",
    "trigger_tactical_wake",
    "trigger_firetv_deterrence",
    "format_emergency_cad_packet",
    "disarm_perimeter_alert",
    "explain_incident_reasoning",
    "set_mesh_guard_profile",
}


def test_server_is_the_real_fastmcp_sdk_object():
    from mcp.server.fastmcp import FastMCP

    from src.server import mcp

    # Not a stub/mock — the genuine SDK class (the 'calls the tech' bar).
    assert isinstance(mcp, FastMCP)


def test_all_eight_tools_registered_on_real_server():
    from src.server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == CANONICAL_TOOLS
    assert len(tools) == 8


def test_streamable_http_app_constructs():
    """The real Streamable HTTP transport app must build (Alexa+ requirement)."""
    from src.server import mcp

    app = mcp.streamable_http_app()
    # Starlette ASGI app from the official SDK transport — not hand-rolled.
    assert app is not None
    assert app.__class__.__module__.startswith("starlette")


def test_tools_carry_input_schemas():
    """Registered tools must expose JSON input schemas so Alexa+ can call them."""
    from src.server import mcp

    tools = asyncio.run(mcp.list_tools())
    for t in tools:
        assert t.inputSchema is not None, f"{t.name} missing inputSchema"


def test_entry_point_is_streamable_http():
    """main() must run the server over the real streamable-http transport."""
    import inspect

    from src import server

    src_text = inspect.getsource(server.main)
    assert "streamable-http" in src_text
