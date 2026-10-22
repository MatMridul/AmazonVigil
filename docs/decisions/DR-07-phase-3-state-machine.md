# DR-07: Phase 3 Deterministic State Machine & CAD Staging Design

**Status:** Accepted
**Status History:** 2026-10-22 Proposed; 2026-10-22 Accepted
**Date:** 2026-10-22
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A (promotes the Phase 1 baseline stubs noted in DR-04)
**Superseded By:** N/A

## Context

Phase 3 (tasks.md Task 3.1/3.3) promotes `src/core/state_machine.py` and
`src/core/cad_dispatcher.py` from Phase 1 baseline stubs to the full deterministic
engines: the 4 operational modes, dwell dynamics, zero-grace overrides, the L3
multi-sensor corroboration rule, the SILENT_DURESS silent protocol, the 10s CAD
cancel buffer, and PIN disarm. Several of these are hard safety invariants, so the
question is HOW each is enforced, not merely that the code "does" it.

## Decisions

1. **Duress silence is a cap, not a prose promise.** `permitted_actuators(mode,
   level)` returns the empty tuple `()` for `SILENT_DURESS` at every level by
   construction, and `Transition.is_silent` reads that set. "Zero sirens, zero
   chimes, zero Fire TV" is therefore enforced by the allowed-set being empty, not
   by a comment asking callers to behave. (Owner's standing rule: make the boundary
   a cap/table, not a sentence.)

2. **L3 dispatch is gated by corroboration.** `enforce_l3_corroboration` holds any
   L3 band down to L2 unless weapon OR active distress flag OR >=2 independent
   sensor indicators (M/V/A) are present — enforcing "zero unverified 911" as a
   code path, not a policy note.

3. **The engine is pure and clock-injected.** `StateMachine.evaluate(..., now=)`
   and `CadStaging(..., now=)` never read the wall clock; time is a parameter. This
   makes every transition and the 10s buffer deterministically replayable in tests
   (owner's deterministic-replay requirement) and removes sleep-based flakiness.

4. **Mode strings match the live MCP tool.** `GuardMode` values reuse the exact
   strings already accepted by `set_mesh_guard_profile` in `src/server.py`
   (`daytime_ambient`/`night_sentry`/`vacation`/`duress`) so the tool and the
   engine cannot drift.

5. **`recommended_action(level, mode=DAYTIME_AMBIENT)`.** The mode parameter
   defaults so the mode-agnostic Bedrock fallback heuristic
   (`bedrock_analyzer.py`) keeps compiling; mode-aware callers pass it explicitly.
   (This regression was caught by running the FULL suite, not just the new files —
   recorded here as the reason the default exists.)

## Strongest Argument Against

Defaulting `mode` risks a caller silently getting DAYTIME behavior when it meant
something else. Mitigated: the only mode-less caller is the fallback heuristic,
which is genuinely mode-agnostic (it maps level->action with no actuator plan),
and the state machine itself always passes mode explicitly.

## Consequences

- Silence, corroboration, and dwell are all testable invariants with no I/O.
- Full suite: 77 passed, 0 warnings (filterwarnings=error).
- Server wiring of the StateMachine into the live tools remains a later step; the
  engines are standalone and consumed by tests in Phase 3.
