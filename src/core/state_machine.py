"""Deterministic threat-level state machine (Phase 3 — tasks.md Task 3.1).

Promoted from the Phase 1 baseline (DR-04) to the full operational engine:

- 4 operational modes with per-mode dwell-grace windows (SPEC.md §2, SYSTEM_DESIGN §1-§2).
- Score bands  L0 < 0.25 <= L1 < 0.65 <= L2 < 0.85 <= L3.
- Dwell timer: a sub-escalation score sustained past the mode's grace window escalates.
- Zero-grace overrides: optical tamper (phi_v==0), breach acoustics, weapon, or
  masked-near-entry escalate immediately regardless of dwell/mode.
- Multi-sensor corroboration gate: L3_CRITICAL dispatch requires weapon confirmation,
  an active distress flag, or 2+ corroborating sensor indicators (M / V / A).
- SILENT_DURESS protocol: complete actuator silence; direct silent CAD staging only.

The engine is pure and deterministic — no I/O, no clock reads except an injectable
``now`` — so every transition is unit-testable and replayable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.core.types import IntegrityVector, MeshAction, ThreatLevel

# --------------------------------------------------------------------------- #
# Threat-score band boundaries (SPEC.md §2 dwell diagram).
# --------------------------------------------------------------------------- #
BAND_L1 = 0.25
BAND_L2 = 0.65
BAND_L3 = 0.85


class GuardMode(str, Enum):
    """The 4 operational modes (SYSTEM_DESIGN §1-§2)."""

    DAYTIME_AMBIENT = "daytime_ambient"
    NIGHT_SENTRY = "night_sentry"
    VACATION_AWAY = "vacation"
    SILENT_DURESS = "duress"


# Per-mode dwell grace in seconds (SPEC.md §2 / Phase 3 scope).
DWELL_GRACE_SECONDS: dict[GuardMode, float] = {
    GuardMode.DAYTIME_AMBIENT: 45.0,
    GuardMode.NIGHT_SENTRY: 15.0,
    GuardMode.VACATION_AWAY: 10.0,
    GuardMode.SILENT_DURESS: 0.0,
}

_ORDER = [
    ThreatLevel.L0_SAFE,
    ThreatLevel.L1_AMBIGUOUS,
    ThreatLevel.L2_SUSPICIOUS,
    ThreatLevel.L3_CRITICAL,
]


def _rank(level: ThreatLevel) -> int:
    return _ORDER.index(level)


# --------------------------------------------------------------------------- #
# Score banding + zero-grace overrides (retained from Phase 1 baseline).
# --------------------------------------------------------------------------- #
def classify_score(score: float) -> ThreatLevel:
    """Map a bounded threat score in [0,1] to a ThreatLevel band."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be in [0.0, 1.0]")
    if score < BAND_L1:
        return ThreatLevel.L0_SAFE
    if score < BAND_L2:
        return ThreatLevel.L1_AMBIGUOUS
    if score < BAND_L3:
        return ThreatLevel.L2_SUSPICIOUS
    return ThreatLevel.L3_CRITICAL


@dataclass(frozen=True)
class ThreatSignals:
    """Discrete override + corroboration indicators feeding the state machine."""

    integrity: IntegrityVector | None = None
    weapon_detected: bool = False
    masked_near_entry: bool = False
    breach_acoustics: bool = False
    distress_flag: bool = False
    # Corroborating sensor presence (the M / V / A triad).
    motion_indicator: bool = False
    visual_indicator: bool = False
    acoustic_indicator: bool = False

    @property
    def optical_tamper(self) -> bool:
        return bool(self.integrity and self.integrity.optical_tampered)

    @property
    def zero_grace_fired(self) -> bool:
        """Any condition that bypasses the dwell window entirely."""
        return (
            self.weapon_detected
            or self.optical_tamper
            or self.masked_near_entry
            or self.breach_acoustics
        )

    def corroboration_count(self) -> int:
        """Number of independent sensor indicators present (M / V / A)."""
        return sum(
            (self.motion_indicator, self.visual_indicator, self.acoustic_indicator)
        )


def apply_zero_grace_overrides(
    level: ThreatLevel, signals: ThreatSignals
) -> ThreatLevel:
    """Escalate on any zero-grace condition (SPEC.md §2.1).

    Weapon detection goes straight to L3; optical tamper / masked-near-entry /
    breach acoustics floor the level at L2.
    """
    if signals.weapon_detected:
        return ThreatLevel.L3_CRITICAL
    if signals.optical_tamper or signals.masked_near_entry or signals.breach_acoustics:
        return max(level, ThreatLevel.L2_SUSPICIOUS, key=_rank)
    return level


def enforce_l3_corroboration(level: ThreatLevel, signals: ThreatSignals) -> ThreatLevel:
    """Gate L3 dispatch: zero unverified 911 (SPEC.md §2, SYSTEM_DESIGN §2).

    L3_CRITICAL stands only with weapon confirmation, an active distress flag, or
    2+ corroborating sensor indicators. Otherwise it is held down to L2_SUSPICIOUS.
    """
    if level is not ThreatLevel.L3_CRITICAL:
        return level
    corroborated = (
        signals.weapon_detected
        or signals.distress_flag
        or signals.corroboration_count() >= 2
    )
    return level if corroborated else ThreatLevel.L2_SUSPICIOUS


def recommended_action(
    level: ThreatLevel, mode: GuardMode = GuardMode.DAYTIME_AMBIENT
) -> MeshAction:
    """Default mesh action for a level under a mode (overridable by Bedrock).

    SILENT_DURESS forces silence at every level below dispatch, and a silent
    dispatch at L3 — no chimes, sirens, or Fire TV displays ever fire.
    """
    if mode is GuardMode.SILENT_DURESS:
        if level is ThreatLevel.L3_CRITICAL:
            return MeshAction.DISPATCH_EMERGENCY  # silent CAD staging, no deterrents
        return MeshAction.SILENT_PASS
    return {
        ThreatLevel.L0_SAFE: MeshAction.SILENT_PASS,
        ThreatLevel.L1_AMBIGUOUS: MeshAction.NOTIFY_HOST,
        ThreatLevel.L2_SUSPICIOUS: MeshAction.WAKE_HOST_AND_DETER,
        ThreatLevel.L3_CRITICAL: MeshAction.DISPATCH_EMERGENCY,
    }[level]


# --------------------------------------------------------------------------- #
# Actuator plan — enforces the SILENT_DURESS silence invariant as data.
# --------------------------------------------------------------------------- #
# Interior/exterior actuators that make noise or light. Under SILENT_DURESS the
# allowed set is empty by construction, so silence is a cap, not a prose promise.
_ALL_ACTUATORS = (
    "chime",
    "tv_pip_toast",
    "echo_whisper",
    "nightstand_hum",
    "boot_bridge_footsteps",
    "firetv_bluff",
    "synthetic_concierge",
    "mobile_alert",
)


def permitted_actuators(mode: GuardMode, level: ThreatLevel) -> tuple[str, ...]:
    """Actuators allowed to fire for (mode, level). Duress returns () — silence."""
    if mode is GuardMode.SILENT_DURESS:
        return ()
    if level is ThreatLevel.L0_SAFE:
        return ()
    if level is ThreatLevel.L1_AMBIGUOUS:
        return ("chime", "tv_pip_toast", "mobile_alert")
    if level is ThreatLevel.L2_SUSPICIOUS:
        if mode is GuardMode.VACATION_AWAY:
            return ("synthetic_concierge", "mobile_alert")
        if mode is GuardMode.NIGHT_SENTRY:
            return (
                "echo_whisper",
                "nightstand_hum",
                "boot_bridge_footsteps",
                "firetv_bluff",
                "mobile_alert",
            )
        return ("chime", "tv_pip_toast", "mobile_alert")
    # L3_CRITICAL: full deterrence + alerts (never under duress).
    if mode is GuardMode.NIGHT_SENTRY:
        return (
            "echo_whisper",
            "nightstand_hum",
            "boot_bridge_footsteps",
            "firetv_bluff",
            "mobile_alert",
        )
    return ("chime", "firetv_bluff", "mobile_alert")


# --------------------------------------------------------------------------- #
# Dwell-aware state machine.
# --------------------------------------------------------------------------- #
@dataclass
class StateMachine:
    """Deterministic, dwell-aware L0-L3 engine for one perimeter channel.

    ``evaluate`` is pure given its inputs: it reads no wall clock, taking ``now``
    as an argument so scenario tests can advance time exactly.
    """

    mode: GuardMode = GuardMode.DAYTIME_AMBIENT
    current_level: ThreatLevel = ThreatLevel.L0_SAFE
    # Timestamp when the current sub-L2 dwell began, or None if not dwelling.
    _dwell_started_at: float | None = field(default=None, repr=False)

    @property
    def dwell_grace(self) -> float:
        return DWELL_GRACE_SECONDS[self.mode]

    def set_mode(self, mode: GuardMode) -> None:
        self.mode = mode
        self._dwell_started_at = None

    def evaluate(
        self, score: float, signals: ThreatSignals, *, now: float
    ) -> "Transition":
        """Compute the resulting threat level + action for a fresh reading.

        Pipeline: score band -> zero-grace override -> dwell escalation ->
        L3 corroboration gate -> mode-aware action + permitted actuators.
        """
        banded = classify_score(score)
        overridden = apply_zero_grace_overrides(banded, signals)

        # Dwell dynamics: an L1/L2-band reading that persists past the grace
        # window escalates one band. Zero-grace conditions bypass the timer.
        escalated = overridden
        if signals.zero_grace_fired:
            self._dwell_started_at = None
        elif _rank(overridden) >= _rank(ThreatLevel.L1_AMBIGUOUS) and overridden is not ThreatLevel.L3_CRITICAL:
            if self._dwell_started_at is None:
                self._dwell_started_at = now
            elif (now - self._dwell_started_at) >= self.dwell_grace:
                escalated = _ORDER[min(_rank(overridden) + 1, len(_ORDER) - 1)]
        else:
            self._dwell_started_at = None

        gated = enforce_l3_corroboration(escalated, signals)
        self.current_level = gated

        action = recommended_action(gated, self.mode)
        actuators = permitted_actuators(self.mode, gated)
        return Transition(
            mode=self.mode,
            level=gated,
            action=action,
            permitted_actuators=actuators,
            dwell_elapsed=(None if self._dwell_started_at is None else now - self._dwell_started_at),
            corroborated=enforce_l3_corroboration(ThreatLevel.L3_CRITICAL, signals)
            is ThreatLevel.L3_CRITICAL,
        )


@dataclass(frozen=True)
class Transition:
    """The deterministic result of one state-machine evaluation."""

    mode: GuardMode
    level: ThreatLevel
    action: MeshAction
    permitted_actuators: tuple[str, ...]
    dwell_elapsed: float | None
    corroborated: bool

    @property
    def is_silent(self) -> bool:
        """True when no audible/visible actuator may fire (duress invariant)."""
        return len(self.permitted_actuators) == 0
