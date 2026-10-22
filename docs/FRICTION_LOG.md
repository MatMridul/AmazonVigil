# Amazon Vigil — Friction Log

Real friction encountered while building Amazon Vigil against the official tools,
SDKs, and APIs required by the Amazon Developer Hackathon 2026. Each entry records
what we hit, why it happened, how we resolved it, and what would have prevented it.

---

## F-01 — `mcp>=1.0.0` silently resolves to a breaking 2.x

**Area:** Model Context Protocol (MCP) Python SDK — `mcp` package
**Date:** 2026-10-22
**Severity:** Build-blocking (1 of 3 test modules failed to import)

### What happened
Our dependency pin was `mcp>=1.0.0` (chosen in DR-01 to use the official SDK's
`from mcp.server.fastmcp import FastMCP`). At install time the resolver picked the
newest release satisfying that range — **mcp 2.x** — which is a breaking major.
In 2.x, `FastMCP` was renamed to `MCPServer`, the `mcp.server.fastmcp` import path
was removed, and other APIs changed. The server module imported fine against the
v1 API we coded to, but blew up at collection under 2.x:

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x,
where FastMCP was renamed to MCPServer (from mcp.server.mcpserver import MCPServer)
and other APIs changed; see the migration guide ... or pin 'mcp<2' to keep
running v1 code.
```

### Why it's friction
The official docs and most current tutorials still teach the v1
`from mcp.server.fastmcp import FastMCP` entry point, and `>=1.0.0` is the natural
pin a developer writes. Nothing in the common guidance warns that an unbounded
range will cross the v1→v2 boundary and break that exact import. The error message
itself is good (it names the fix), but you only see it after a full install.

### Resolution
Pinned `mcp>=1.0.0,<2.0.0` in `requirements.txt` and `pyproject.toml`
(see DR-06). No source changes were needed — our code was correct for the v1 API.

### What would have prevented it
- A clearer upgrade-boundary note in the MCP SDK README / quickstart ("v1 and v2
  are not import-compatible; pin `mcp<2` if you use `mcp.server.fastmcp`").
- The quickstart examples pinning a bounded range rather than `mcp>=1.0.0`.

### Product feedback (for submission)
The `mcp` SDK's v2 error message is excellent — it diagnoses the rename and hands
you the exact remediation. The gap is upstream: the getting-started material should
pin a bounded major so a routine `>=1.0.0` doesn't silently adopt a breaking SDK.
