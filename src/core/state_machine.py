"""Deterministic threat-level state machine (Phase 1 baseline — DR-04).

A zero-latency local rule table mapping a bounded threat score to a ThreatLevel,
with zero-grace overrides (SPEC.md §2.1 / §2 dwell dynamics). The full operational
mode machine and multi-sensor corroboration land in Phase 3 (tasks.md Task 3.1).
"""

from __future__ import annotations

from src.core.types import IntegrityVector, MeshAction, ThreatLevel

# Threat-score band boundaries (SPEC.md §2 dwell diagram).
BAND_L1 = 0.25
BAND_L2 = 0.65
BAND_L3 = 0.85


def classify_score(score: float) -> ThreatLevel:
    """Map a bounded threat score ∈ [0,1] to a ThreatLevel band."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be in [0.0, 1.0]")
    if score < BAND_L1:
        return ThreatLevel.L0_SAFE
    if score < BAND_L2:
        return ThreatLevel.L1_AMBIGUOUS
    if score < BAND_L3:
        return ThreatLevel.L2_SUSPICIOUS
    return ThreatLevel.L3_CRITICAL


def apply_zero_grace_overrides(
    level: ThreatLevel,
    *,
    integrity: IntegrityVector | None = None,
    weapon_detected: bool = False,
    masked_near_entry: bool = False,
    breach_acoustics: bool = False,
) -> ThreatLevel:
    """Escalate to >= L2 when any zero-grace condition fires (SPEC.md §2.1)."""
    optical_tamper = bool(integrity and integrity.optical_tampered)
    if weapon_detected:
        return ThreatLevel.L3_CRITICAL
    if optical_tamper or masked_near_entry or breach_acoustics:
        return max(level, ThreatLevel.L2_SUSPICIOUS, key=_rank)
    return level


def recommended_action(level: ThreatLevel) -> MeshAction:
    """Default mesh action for a threat level (overridable by Bedrock)."""
    return {
        ThreatLevel.L0_SAFE: MeshAction.SILENT_PASS,
        ThreatLevel.L1_AMBIGUOUS: MeshAction.NOTIFY_HOST,
        ThreatLevel.L2_SUSPICIOUS: MeshAction.WAKE_HOST_AND_DETER,
        ThreatLevel.L3_CRITICAL: MeshAction.DISPATCH_EMERGENCY,
    }[level]


_ORDER = [
    ThreatLevel.L0_SAFE,
    ThreatLevel.L1_AMBIGUOUS,
    ThreatLevel.L2_SUSPICIOUS,
    ThreatLevel.L3_CRITICAL,
]


def _rank(level: ThreatLevel) -> int:
    return _ORDER.index(level)
