# DR-04: Phase 1 Scope Boundary & Adapter Stubbing

**Status:** Accepted
**Status History:** 2026-10-14 Proposed; 2026-10-14 Accepted
**Date:** 2026-10-14
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

`tasks.md` defines nine phases. The Phase 1 build prompt (Tasks 1.1–1.6) is a
subset: environment, data models, optical auditor + preprocessor, Bedrock
evaluator, the 8-tool FastMCP server, and tests. The peripheral hardware adapters
(Ring WebRTC, Bee CLI, Fire TV WebSocket), the full state machine, the simulator,
and the UI are later phases. The 8 MCP tools nominally touch some of those
adapters.

## Options Considered

- **Option A — Build Phase 1 core; stub peripheral adapters.** Implement types,
  auditor, Bedrock evaluator, FastMCP server with all 8 tools and the idempotency
  cache, and tests. Ring/Bee/Fire TV are clean, typed stubs sufficient to fulfill
  the tool contracts. State machine and CAD dispatcher are lightweight baseline
  stubs.
- **Option B — Pull later-phase adapters forward.** Build real Ring/Bee/Fire TV
  integrations now. Larger blast radius, out of the approved phase scope, and
  needs live hardware/credentials unavailable at this stage.

## Decision

**Option A.** Build exactly the Phase 1 core. Peripheral adapters are clean,
typed stubs with honest "simulation/mock" behavior, sufficient for the 8 tool
contracts and for offline tests. No fabricated hardware behavior.

## Rationale

Matches the approved phase scope, keeps the change reviewable, and respects the
honesty split: a stub that announces it is a stub is truthful; a stub pretending
to be live hardware is not.

## Strongest Argument Against

Stubs can mask integration risk that only surfaces when real adapters land.
Mitigated by typing the stub boundaries exactly to the eventual live contract so
the later swap is mechanical, and by keeping `VIGIL_MODE=simulation` explicit.

## Consequences

- Phase 1 ships with `VIGIL_MODE=simulation` behavior for all device adapters.
- The 8 MCP tools are fully implemented at the contract level; their device-side
  effects are mocked until the relevant later phase.
- CAD dispatcher and state machine exist as baseline stubs, expanded in Phase 3.
