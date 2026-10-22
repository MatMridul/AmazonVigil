# DR-08: Phase 8 Scenario Simulator — Deterministic Edge Path

**Status:** Accepted
**Status History:** 2026-10-22 Proposed; 2026-10-22 Accepted
**Date:** 2026-10-22
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

Phase 8 (tasks.md Task 8.1/8.2) builds the scenario catalog
(`src/simulator/canned_scenarios.json`) and runner
(`src/simulator/scenario_runner.py`) that drive all 10 SPEC.md §3 baseline
scenarios end-to-end, plus the baseline test suite. The runner also becomes the
data source the Phase 7 web console's scenario selector will call, so its
outputs must be reproducible and fast.

## Decisions

1. **The runner uses the deterministic edge path, not a live Bedrock call.** Each
   scenario is resolved through `StateMachine.evaluate`, the same local rule path
   that fires when Bedrock is unreachable (SPEC.md §3.2). Rationale: scenario
   outcomes must be identical on every machine (judge reproducibility, offline
   demo, CI with no AWS creds) and must not cost a cloud round-trip when a judge
   clicks through the UI. Live multimodal reasoning remains available via the
   `BedrockThreatEvaluator` for real events; the SIMULATOR is deliberately
   deterministic.

2. **Fixtures carry symbolic ingest AND the discrete signals/score the engine
   consumes.** The §3 matrix is symbolic (`V_weapon`, `A_breach_noise`); the
   fixture translates those into the `ThreatSignals` override/corroboration flags
   + a seed `score` + the operational `mode` implied by host state. The symbolic
   `ingest` block is retained for display/provenance. Expected outcomes
   (`expected_level`/`action`/`actuators_empty`/`cad_staged`) are asserted, so a
   fixture that drifts from the spec fails a test.

3. **A fixed evaluation epoch (`_EPOCH`).** `now` is pinned so dwell and the 10s
   CAD buffer are deterministic; no scenario depends on wall-clock timing.

4. **CAD is staged only on `DISPATCH_EMERGENCY`.** Scenario 10 (duress) proves the
   load-bearing invariant: L3 dispatch with an EMPTY actuator set — CAD goes out
   while every siren/chime/display stays silent.

## Strongest Argument Against

A deterministic simulator does not exercise the real Bedrock multimodal path, so a
green scenario suite is not evidence the cloud reasoner works. Accepted: the
simulator's job is to prove the *deterministic mesh logic* and feed the UI; the
Bedrock path has its own tests (`test_bedrock_analyzer.py`) and the honesty split
(SPEC §7) keeps the two claims separate.

## Consequences

- `python -m src.simulator.scenario_runner --scenario 06 | --all` emits JSON ready
  for the Phase 7 scenario selector.
- Full suite: 94 passed, 0 warnings (filterwarnings=error).
- The Phase 7 UI can render live scenario reactions with zero AWS dependency.
