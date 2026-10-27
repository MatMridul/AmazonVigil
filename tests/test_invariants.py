"""SEC.10 — safety-invariant tests. The moat, locked as executable guarantees.

These assert that Vigil's three load-bearing safety properties are enforced by
the ARCHITECTURE (caps, dispatch tables, gates), not by prose or model intent —
so a future edit that quietly breaks one FAILS here. If any of these go red, a
safety guarantee the whole product rests on has been broken; treat it as a
release blocker, not a flaky test.

Invariants:
  I1  Silence-under-duress: under SILENT_DURESS no audible/visible actuator may
      EVER fire, at any threat level. The permitted-actuator set is () by cap.
  I2  No auto-911: the CAD path only STAGES a manifest (staged=True); it never
      auto-sends. A staged packet is inert until a human 1-tap send.
  I3  L3 corroboration gate: L3_CRITICAL stands only with weapon OR distress OR
      2+ corroborating sensors; an uncorroborated L3 is held down to L2.
"""

from __future__ import annotations

from src.core.cad_dispatcher import build_cad_packet, stage_cad_dispatch
from src.core.state_machine import (
    GuardMode,
    StateMachine,
    ThreatSignals,
    enforce_l3_corroboration,
    permitted_actuators,
    recommended_action,
)
from src.core.types import IntegrityVector, MeshAction, ThreatLevel

_ALL_LEVELS = [
    ThreatLevel.L0_SAFE,
    ThreatLevel.L1_AMBIGUOUS,
    ThreatLevel.L2_SUSPICIOUS,
    ThreatLevel.L3_CRITICAL,
]
_ALL_MODES = list(GuardMode)


# --- I1: silence-under-duress --------------------------------------------- #

def test_duress_permits_zero_actuators_at_every_level():
    for level in _ALL_LEVELS:
        assert permitted_actuators(GuardMode.SILENT_DURESS, level) == (), (
            f"DURESS must be silent at {level}, got actuators"
        )


def test_duress_transition_is_silent_even_at_critical():
    # Drive a maxed-out, fully-corroborated threat under duress and prove the
    # resulting plan still fires nothing audible/visible.
    sm = StateMachine(mode=GuardMode.SILENT_DURESS)
    signals = ThreatSignals(
        weapon_detected=True, distress_flag=True,
        motion_indicator=True, visual_indicator=True, acoustic_indicator=True,
    )
    t = sm.evaluate(1.0, signals, now=0.0)
    assert t.is_silent is True
    assert t.permitted_actuators == ()


def test_duress_below_dispatch_is_silent_pass():
    # Every non-dispatch level under duress maps to SILENT_PASS (no notify/deter).
    for level in (ThreatLevel.L0_SAFE, ThreatLevel.L1_AMBIGUOUS, ThreatLevel.L2_SUSPICIOUS):
        assert recommended_action(level, GuardMode.SILENT_DURESS) is MeshAction.SILENT_PASS


# --- I2: no auto-911 ------------------------------------------------------ #

def test_cad_packet_is_always_staged_never_sent():
    packet = build_cad_packet("INC-INV-1", threat_summary="test")
    # The only field that governs transmission is 'staged'; it is True (inert),
    # and there is no 'sent'/'transmitted' field the engine can flip itself.
    assert packet.staged is True
    assert not hasattr(packet, "sent")
    assert not hasattr(packet, "transmitted")


def test_cad_staging_requires_human_window_not_auto_send():
    staging = stage_cad_dispatch("INC-INV-2", staged_at=0.0)
    # Freshly staged: cancellable, not yet "ready", never auto-dispatched.
    assert staging.cancelled is False
    assert staging.is_cancellable(now=0.0) is True
    # Even once the buffer elapses, "ready" means a human MAY send — it is not a send.
    assert staging.is_ready(now=999.0) is True


# --- I3: L3 corroboration gate -------------------------------------------- #

def test_uncorroborated_l3_is_held_to_l2():
    # A top-band score with NO corroboration must not stand at L3.
    bare = ThreatSignals()
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, bare) is ThreatLevel.L2_SUSPICIOUS


def test_l3_stands_with_weapon():
    s = ThreatSignals(weapon_detected=True)
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, s) is ThreatLevel.L3_CRITICAL


def test_l3_stands_with_distress_flag():
    s = ThreatSignals(distress_flag=True)
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, s) is ThreatLevel.L3_CRITICAL


def test_l3_stands_with_two_corroborating_sensors():
    s = ThreatSignals(motion_indicator=True, visual_indicator=True)
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, s) is ThreatLevel.L3_CRITICAL


def test_l3_single_sensor_is_not_enough():
    s = ThreatSignals(motion_indicator=True)  # only one indicator
    assert enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, s) is ThreatLevel.L2_SUSPICIOUS


def test_full_engine_holds_uncorroborated_critical_score_at_l2():
    # End-to-end through the real engine: a 1.0 score with no corroboration and
    # no zero-grace override must NOT dispatch.
    sm = StateMachine(mode=GuardMode.NIGHT_SENTRY)
    integrity = IntegrityVector(phi_m=1.0, phi_v=1.0, phi_a=1.0, phi_net=1.0)
    t = sm.evaluate(1.0, ThreatSignals(integrity=integrity), now=0.0)
    assert t.level is not ThreatLevel.L3_CRITICAL
    assert t.action is not MeshAction.DISPATCH_EMERGENCY
