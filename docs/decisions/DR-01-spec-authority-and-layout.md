# DR-01: Spec Authority & Phase 1 Project Layout

**Status:** Accepted
**Status History:** 2026-10-14 Proposed; 2026-10-14 Accepted
**Date:** 2026-10-14
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

The Phase 1 build prompt and the frozen specs described two different project
skeletons and two different MCP libraries:

- **Phase 1 prompt:** `fastmcp>=0.4.1`; files `src/models/threat.py`,
  `src/engine/bedrock_evaluator.py`, `src/adapters/ring/optical_auditor.py`,
  `src/server/mcp_server.py`.
- **Frozen `SPEC.md` §6 + `tasks.md` Phase 1:** `mcp>=1.0.0`; files
  `src/core/types.py`, `src/core/integrity_auditor.py`,
  `src/adapters/bedrock_analyzer.py`, `src/server.py`.

Governance rule #1 ("ground all work strictly in SPEC.md / tasks.md") makes the
frozen specs authoritative, but the build prompt was the explicit instruction for
this phase. This is a one-way-door naming decision — reversing it later means
moving every import and path.

## Options Considered

- **Option A — Follow the frozen specs' layout and `mcp>=1.0.0`.** Honors
  governance rule #1. `fastmcp` is now folded into the official `mcp` SDK
  (`from mcp.server.fastmcp import FastMCP`), so no capability is lost. Keeps the
  tree consistent with the later-phase tasks.md references.
- **Option B — Follow the Phase 1 prompt's layout and `fastmcp>=0.4.1`.** Honors
  the literal build instruction but contradicts the frozen specs the same prompt
  told us to ground everything in, and splits from the tree used by Phases 2–9.

## Decision

**Option A.** `SPEC.md` §6 and `tasks.md` win. Use the official `mcp>=1.0.0`
package via `from mcp.server.fastmcp import FastMCP`. Phase 1 tree:

- `src/core/types.py` — Pydantic v2 schemas (Φ, Telemetry, State, ThreatAssessment, CAD)
- `src/core/integrity_auditor.py` — optical auditor, Φ_V, variance/saturation tamper detection, duplex mute gate
- `src/adapters/bedrock_analyzer.py` — Claude 3.5 Sonnet multimodal evaluator + offline mock fallback
- `src/server.py` — FastMCP streamable HTTP server, 8 tools, 15s idempotency cache
- `src/core/state_machine.py`, `src/core/cad_dispatcher.py` — lightweight Phase 1 baseline stubs as needed
- `tests/test_integrity_auditor.py`, `tests/test_bedrock_analyzer.py`, `tests/test_mcp_server.py`

## Rationale

The specs were explicitly frozen and the governance rules name them as the single
source of truth. The official `mcp` SDK supersedes the standalone `fastmcp`
package, so Option A loses nothing and keeps the whole roadmap on one tree.

## Strongest Argument Against

The Phase 1 prompt was the most recent and most specific instruction; overriding
it with older documents risks ignoring a deliberate late change the owner made in
the prompt. Mitigated by explicit owner ratification of this DR.

## Consequences

- All Phase 1 code uses `mcp>=1.0.0`, not `fastmcp` as a standalone dependency.
- The prompt's four file paths are mapped onto the spec tree; any later reference
  to `src/models/` or `src/engine/` should be read as the spec-tree equivalent.
- Establishes the precedent: **frozen specs outrank the per-phase prompt** when
  they conflict, unless a future DR overturns a specific spec point.
