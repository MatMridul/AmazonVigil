# DR-10: Alexa+ MCP Server as the Primary-Track Eligibility Code Path

**Status:** Accepted
**Status History:** 2026-10-23 Proposed; 2026-10-23 Accepted
**Date:** 2026-10-23
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

Amazon Vigil's primary track is **Alexa+**. The hackathon's eligibility rule is
explicit: the repository must **actually call the track's tech in code**
(import / entry point / loaded config), not merely mention it in prose. The
Alexa+ track accepts a **self-hosted MCP server (spec 2025-11-25 or later,
Streamable HTTP)** as the integration. This DR records what satisfies that bar
in code, and what remains a human wiring step.

## Decision

`src/server.py` is the eligibility code path. It uses the **official `mcp`
SDK** (`from mcp.server.fastmcp import FastMCP`, pinned `>=1.0.0,<2.0.0` per
DR-06) and exposes the 8 canonical Vigil tools over the SDK's real
**Streamable HTTP** transport (`mcp.run(transport="streamable-http")`), the
transport the current MCP spec defines (single MCP endpoint, POST for JSON-RPC
in with `application/json` or `text/event-stream` out, GET for SSE, `Origin`
validation, `Mcp-Session-Id` session management).

The 8 tools are the mesh-correlation command surface Alexa+ drives:
`audit_perimeter_event`, `query_wearer_state`, `trigger_tactical_wake`,
`trigger_firetv_deterrence`, `format_emergency_cad_packet`,
`disarm_perimeter_alert`, `explain_incident_reasoning`,
`set_mesh_guard_profile`.

## What is PROVEN in code (CI, no hardware)

`tests/test_mcp_eligibility.py` exercises the genuine SDK — it fails if the
server is a mock or the tools are not really registered:

- the server object is the real `mcp.server.fastmcp.server.FastMCP` class;
- all 8 tools are registered on it (via `list_tools()`), each with a JSON
  `inputSchema` Alexa+ can call against;
- the real Streamable HTTP ASGI app constructs (`streamable_http_app()` returns
  a Starlette app from the SDK transport — not hand-rolled);
- `main()` runs over `transport="streamable-http"`.

This is the "calls the tech in code" evidence: import loads, server constructs,
tools register, real transport app builds.

## What is a HUMAN wiring step (parked for morning)

Executing a **live** Alexa+ ↔ server handshake needs the resident's Echo and a
linked Alexa+ developer account registering the MCP endpoint URL. That is an
account/credential action an agent must not take unattended. The server is
built to the real spec so that wiring is mechanical: start the server, expose
the endpoint, register it with the Alexa+ account.

## Strongest Argument Against

Proving the server constructs and registers tools is not proving a live Alexa+
conversation happened. Accepted: the eligibility rule is about the repo calling
the tech in code, which the SDK usage and transport app satisfy; the live
handshake is demonstrated in the recorded demo once the Echo is wired. The
honesty split holds — no test claims a live Alexa+ round-trip occurred.

## Consequences

- Primary-track eligibility rests on real SDK usage, verified by CI.
- `python -m src.server` starts the real Streamable HTTP endpoint.
- Device-side tool effects remain simulated/MODELED (DR-04) until each device
  adapter lands; the MCP surface itself is real.
