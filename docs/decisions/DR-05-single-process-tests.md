# DR-05: Single-Process Test Execution Under Host RAM Pressure

**Status:** Accepted
**Status History:** 2026-10-14 Proposed; 2026-10-14 Accepted
**Date:** 2026-10-14
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

The build host is under memory pressure (~1.7–2.2 GB free during Phase 1).
Parallel test execution (`pytest-xdist`) and large parallel sub-agent waves risk
failing or destabilizing other sessions on the host.

## Options Considered

- **Option A — Single-process `pytest -v`.** Serial execution, bounded memory.
  Slightly slower but safe under pressure.
- **Option B — Parallel `pytest -n auto`.** Faster but spawns multiple worker
  processes, multiplying peak RAM — unsafe at <2 GB free.

## Decision

**Option A.** Run tests single-process (`pytest -v`). No `pytest-xdist` in
Phase 1. Avoid wide parallel sub-agent waves while host RAM is tight.

## Rationale

Correctness proof does not require parallelism; a bounded serial run protects the
shared host. Speed is not the constraint here.

## Strongest Argument Against

Serial runs are slower as the suite grows, which could lengthen the
edit-test loop later. Mitigated by targeted test selection during development and
revisiting parallelism once host RAM recovers (would need a new/updated DR).

## Consequences

- Phase 1 CI/local guidance: `pytest -v`, single process.
- Revisit parallel testing only when host memory allows; record any change here
  via Status History or a superseding DR.
