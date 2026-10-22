# DR-06: Pin `mcp` to the v1 Major (`<2.0.0`)

**Status:** Accepted
**Status History:** 2026-10-22 Proposed; 2026-10-22 Accepted
**Date:** 2026-10-22
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A (amends the version constraint assumed by DR-01; DR-01 itself stays frozen)
**Superseded By:** N/A

## Context

DR-01 chose the official `mcp` SDK over the standalone `fastmcp` package and froze
the import `from mcp.server.fastmcp import FastMCP`, declaring the constraint
`mcp>=1.0.0` in both `requirements.txt` and `pyproject.toml`.

At first install (2026-10-22), the resolver satisfied `>=1.0.0` with **mcp 2.x**,
the newest release. mcp 2.x is a **breaking major**: `FastMCP` was renamed to
`MCPServer`, the import path `mcp.server.fastmcp` was removed, and other APIs
changed. Collection of `tests/test_mcp_server.py` failed with:

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x,
where FastMCP was renamed to MCPServer ... see the migration guide ... or pin
'mcp<2' to keep running v1 code.
```

The other 18 tests collected cleanly; only the server-importing module broke. The
build prompt and DR-01 both assumed the v1 FastMCP API, so our code is correct
*for v1* — the defect was purely the unbounded upper version range.

## Options Considered

- **Option A — Pin `mcp>=1.0.0,<2.0.0`.** Keeps the exact import DR-01 froze; no
  source changes; the v1 FastMCP streamable-HTTP API is stable and documented.
  One-line constraint change in two files + reinstall.
- **Option B — Migrate to mcp 2.x `MCPServer`.** Rewrite `src/server.py` and the
  test imports to the renamed API. Larger churn, touches the frozen DR-01 import
  decision, and adopts a newer/less-battle-tested API days before the deadline.

## Decision

**Option A.** Pin `mcp>=1.0.0,<2.0.0` in `requirements.txt` and `pyproject.toml`.
The import decision in DR-01 is unchanged; this DR only bounds the major version
that decision implicitly assumed.

## Rationale

DR-01's code is already written against the v1 FastMCP API and is spec-faithful.
Bounding the major is the minimal, lowest-risk fix and keeps us aligned with the
frozen import. Migrating to 2.x would trade a one-line pin for a rewrite plus new
risk with no Phase 1 benefit.

## Strongest Argument Against

Pinning below a major means we forgo mcp 2.x improvements and will eventually need
a deliberate migration if the ecosystem moves on. Accepted: a hackathon build
values a stable, proven API over the newest one, and a future DR can plan the
v2 migration if warranted.

## Consequences

- `mcp` is locked to the v1 line; `from mcp.server.fastmcp import FastMCP` keeps
  working as DR-01 specified.
- A future `mcp` v2 migration, if ever undertaken, requires its own DR superseding
  this constraint.
- Logged as friction item F-01 (see `docs/FRICTION_LOG.md`) for the hackathon
  friction-log judging bonus.
