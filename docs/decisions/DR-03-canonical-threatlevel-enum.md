# DR-03: Canonical ThreatLevel Enum

**Status:** Accepted
**Status History:** 2026-10-14 Proposed; 2026-10-14 Accepted
**Date:** 2026-10-14
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

Two different `ThreatLevel` enumerations appeared:

- Phase 1 prompt Task 1.2: `L0_IGNORE`, `L1_OBSERVE`, `L2_DETER`,
  `L3_CRITICAL_DISPATCH`.
- `SPEC.md` §5.2 Bedrock output JSON schema: `L0_SAFE`, `L1_AMBIGUOUS`,
  `L2_SUSPICIOUS`, `L3_CRITICAL`.

The Bedrock structured-output schema and the scenario matrix all reference the
SPEC.md §5.2 names, so tests and the model contract depend on them.

## Options Considered

- **Option A — SPEC.md §5.2 names canonical, prompt names as aliases.** The
  on-the-wire and test-facing values match the frozen output schema; developer
  convenience aliases map the prompt's verbs onto them.
- **Option B — Prompt names canonical.** Would force rewriting the Bedrock JSON
  schema and every scenario reference in the frozen specs.

## Decision

**Option A.** Canonical:
`ThreatLevel = ["L0_SAFE", "L1_AMBIGUOUS", "L2_SUSPICIOUS", "L3_CRITICAL"]`.
Aliases provided for developer convenience: `L0_IGNORE → L0_SAFE`,
`L1_OBSERVE → L1_AMBIGUOUS`, `L2_DETER → L2_SUSPICIOUS`,
`L3_CRITICAL_DISPATCH → L3_CRITICAL`.

## Rationale

The canonical names are the ones the Bedrock JSON contract, the 10-scenario
matrix, and the threat-score bands already use. Aliasing preserves the prompt's
action-oriented vocabulary without a second source of truth on the wire.

## Strongest Argument Against

Aliases add a small surface for confusion (two names for one level). Mitigated by
making the SPEC.md value the only one serialized; aliases are read-only
conveniences that resolve to the canonical member.

## Consequences

- `ThreatAssessment.threat_level` serializes to the SPEC.md §5.2 strings.
- Alias members resolve to canonical values; serialization never emits an alias.
