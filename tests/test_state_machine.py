"""Phase 3 — deterministic state machine tests (tasks.md Task 3.1).

Validates the 4 operational modes, dwell escalations, zero-grace overrides, the
SILENT_DURESS silent protocol, and L3 multi-sensor corroboration. Every test
injects ``now`` so dwell timing is exact and clock-free.
"""

from __future__ import annotations

import pytest

from src.core.state_machine import (
    DWELL_GRACE_SECONDS,
    GuardMode,
    StateMachine,
    ThreatSignals,
    classify_score,
    enforce_l3_corroboration,
    permitted_actuators,
)
from src.core.types import IntegrityVector, MeshAction, ThreatLevel


def _phi(phi_v: float = 1.0) -> IntegrityVector:
    return IntegrityVector(phi_m=1.0, phi_v=phi_v, phi_a=1.0, phi_net=1.0)


# --------------------------------------------------------------------------- #
# Score banding.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "score,expected",
    [
        (0.0, ThreatLevel.L0_SAFE),
        (0.24, ThreatLevel.L0_SAFE),
        (0.25, ThreatLevel.L1_AMBIGUOUS),
        (0.64, ThreatLevel.L1_AMBIGUOUS),
        (0.65, ThreatLevel.L2_SUSPICIOUS),
        (0.84, ThreatLevel.L2_SUSPICIOUS),
        (0.85, ThreatLevel.L3_CRITICAL),
        (1.0, ThreatLevel.L3_CRITICAL),
    ],
)
def test_score_bands(score, expected):
    assert classify_score(score) == expected


def test_score_out_of_range_rejected():
    with pytest.raises(ValueError):
        classify_score(1.5)
    with pytest.raises(ValueError):
        classify_score(-0.1)


# --------------------------------------------------------------------------- #
# Dwell grace per mode.
# --------------------------------------------------------------------------- #
def test_dwell_grace_table():
    assert DWELL_GRACE_SECONDS[GuardMode.DAYTIME_AMBIENT] == 45.0
    assert DWELL_GRACE_SECONDS[GuardMode.NIGHT_SENTRY] == 15.0
    assert DWELL_GRACE_SECONDS[GuardMode.VACATION_AWAY] == 10.0
    assert DWELL_GRACE_SECONDS[GuardMode.SILENT_DURESS] == 0.0


def test_dwell_escalates_only_after_grace_elapses():
    sm = StateMachine(mode=GuardMode.NIGHT_SENTRY)  # 15s grace
    sig = ThreatSignals(integrity=_phi())
    # An L1-band score at t=0 starts the dwell timer but does not escalate.
    t0 = sm.evaluate(0.30, sig, now=1000.0)
    assert t0.level == ThreatLevel.L1_AMBIGUOUS
    # Still within grace (t=1010, 10s elapsed) -> no escalation.
    t1 = sm.evaluate(0.30, sig, now=1010.0)
    assert t1.level == ThreatLevel.L1_AMBIGUOUS
    # Past grace (t=1016, 16s elapsed) -> escalates one band.
    t2 = sm.evaluate(0.30, sig, now=1016.0)
    assert t2.level == ThreatLevel.L2_SUSPICIOUS


def test_daytime_longer_grace_holds_lower():
    sm = StateMachine(mode=GuardMode.DAYTIME_AMBIENT)  # 45s grace
    sig = ThreatSignals(integrity=_phi())
    sm.evaluate(0.30, sig, now=0.0)
    # At 20s, night would have escalated, but daytime's 45s grace holds L1.
    assert sm.evaluate(0.30, sig, now=20.0).level == ThreatLevel.L1_AMBIGUOUS


def test_dwell_resets_when_score_drops_to_safe():
    sm = StateMachine(mode=GuardMode.VACATION_AWAY)  # 10s grace
    sig = ThreatSignals(integrity=_phi())
    sm.evaluate(0.30, sig, now=0.0)
    # Drop to safe clears the dwell timer.
    assert sm.evaluate(0.10, sig, now=5.0).level == ThreatLevel.L0_SAFE
    # A new L1 reading starts a fresh timer; not escalated immediately at +6s.
    assert sm.evaluate(0.30, sig, now=11.0).level == ThreatLevel.L1_AMBIGUOUS


# --------------------------------------------------------------------------- #
# Zero-grace overrides.
# --------------------------------------------------------------------------- #
def test_optical_tamper_zero_grace_to_l2():
    sm = StateMachine(mode=GuardMode.DAYTIME_AMBIENT)
    sig = ThreatSignals(integrity=_phi(phi_v=0.0))
    # Even a near-zero score escalates immediately to L2 with no dwell.
    t = sm.evaluate(0.05, sig, now=0.0)
    assert t.level == ThreatLevel.L2_SUSPICIOUS
    assert t.dwell_elapsed is None


def test_weapon_zero_grace_straight_to_l3():
    sm = StateMachine(mode=GuardMode.DAYTIME_AMBIENT)
    sig = ThreatSignals(integrity=_phi(), weapon_detected=True)
    t = sm.evaluate(0.0, sig, now=0.0)
    assert t.level == ThreatLevel.L3_CRITICAL  # weapon self-corroborates


def test_breach_and_masked_floor_at_l2():
    sm = StateMachine(mode=GuardMode.NIGHT_SENTRY)
    assert (
        sm.evaluate(0.0, ThreatSignals(integrity=_phi(), breach_acoustics=True), now=0.0).level
        == ThreatLevel.L2_SUSPICIOUS
    )
    assert (
        sm.evaluate(0.0, ThreatSignals(integrity=_phi(), masked_near_entry=True), now=0.0).level
        == ThreatLevel.L2_SUSPICIOUS
    )


# --------------------------------------------------------------------------- #
# L3 multi-sensor corroboration gate.
# --------------------------------------------------------------------------- #
def test_l3_held_without_corroboration():
    # A high score alone, with only ONE sensor indicator, cannot dispatch.
    sig = ThreatSignals(integrity=_phi(), motion_indicator=True)
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, sig) == ThreatLevel.L2_SUSPICIOUS


def test_l3_stands_with_two_sensors():
    sig = ThreatSignals(integrity=_phi(), motion_indicator=True, acoustic_indicator=True)
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, sig) == ThreatLevel.L3_CRITICAL


def test_l3_stands_with_distress_flag():
    sig = ThreatSignals(integrity=_phi(), distress_flag=True)
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, sig) == ThreatLevel.L3_CRITICAL


def test_l3_dispatch_via_state_machine_requires_corroboration():
    sm = StateMachine(mode=GuardMode.NIGHT_SENTRY)
    # Score in L3 band but only one indicator -> held at L2.
    held = sm.evaluate(0.95, ThreatSignals(integrity=_phi(), visual_indicator=True), now=0.0)
    assert held.level == ThreatLevel.L2_SUSPICIOUS
    assert held.action == MeshAction.WAKE_HOST_AND_DETER
    # Two indicators -> true L3 dispatch.
    full = sm.evaluate(
        0.95,
        ThreatSignals(integrity=_phi(), visual_indicator=True, acoustic_indicator=True),
        now=1.0,
    )
    assert full.level == ThreatLevel.L3_CRITICAL
    assert full.action == MeshAction.DISPATCH_EMERGENCY


# --------------------------------------------------------------------------- #
# SILENT_DURESS protocol — complete actuator silence.
# --------------------------------------------------------------------------- #
def test_duress_is_silent_at_every_level():
    sm = StateMachine(mode=GuardMode.SILENT_DURESS)
    for score in (0.1, 0.4, 0.7, 0.95):
        t = sm.evaluate(
            score,
            ThreatSignals(integrity=_phi(), weapon_detected=True),  # even with weapon
            now=0.0,
        )
        assert t.is_silent, f"duress must stay silent at score {score}"
        assert t.permitted_actuators == ()


def test_duress_l3_dispatches_silently():
    sm = StateMachine(mode=GuardMode.SILENT_DURESS)
    t = sm.evaluate(0.95, ThreatSignals(integrity=_phi(), distress_flag=True), now=0.0)
    assert t.level == ThreatLevel.L3_CRITICAL
    assert t.action == MeshAction.DISPATCH_EMERGENCY  # silent CAD, no deterrents
    assert t.permitted_actuators == ()


def test_duress_low_level_is_silent_pass():
    sm = StateMachine(mode=GuardMode.SILENT_DURESS)
    t = sm.evaluate(0.10, ThreatSignals(integrity=_phi()), now=0.0)
    assert t.action == MeshAction.SILENT_PASS
    assert t.is_silent


# --------------------------------------------------------------------------- #
# Per-mode actuator plans.
# --------------------------------------------------------------------------- #
def test_night_sentry_actuators_include_bluff_and_boot_bridge():
    acts = permitted_actuators(GuardMode.NIGHT_SENTRY, ThreatLevel.L2_SUSPICIOUS)
    assert "firetv_bluff" in acts
    assert "boot_bridge_footsteps" in acts
    assert "echo_whisper" in acts


def test_vacation_uses_concierge():
    acts = permitted_actuators(GuardMode.VACATION_AWAY, ThreatLevel.L2_SUSPICIOUS)
    assert "synthetic_concierge" in acts
    assert "mobile_alert" in acts


def test_daytime_l1_is_chime_and_toast():
    acts = permitted_actuators(GuardMode.DAYTIME_AMBIENT, ThreatLevel.L1_AMBIGUOUS)
    assert set(acts) == {"chime", "tv_pip_toast", "mobile_alert"}


def test_l0_never_actuates():
    for mode in GuardMode:
        assert permitted_actuators(mode, ThreatLevel.L0_SAFE) == ()


def test_set_mode_resets_dwell():
    sm = StateMachine(mode=GuardMode.NIGHT_SENTRY)
    sm.evaluate(0.30, ThreatSignals(integrity=_phi()), now=0.0)
    sm.set_mode(GuardMode.DAYTIME_AMBIENT)
    assert sm._dwell_started_at is None
    assert sm.mode == GuardMode.DAYTIME_AMBIENT
