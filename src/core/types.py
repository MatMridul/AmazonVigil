"""Strict Pydantic v2 data models for Amazon Vigil.

Grounded in SPEC.md §2 (mathematical formalization) and §5.2 (Bedrock
ThreatAssessment schema). Canonical ThreatLevel names follow DR-03.
"""

from __future__ import annotations

import time
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class ThreatLevel(str, Enum):
    """Canonical threat levels (SPEC.md §5.2, DR-03).

    Alias members (L0_IGNORE, L1_OBSERVE, L2_DETER, L3_CRITICAL_DISPATCH) resolve
    to the canonical values for developer convenience and never serialize
    independently — see ``ThreatLevel.from_alias``.
    """

    L0_SAFE = "L0_SAFE"
    L1_AMBIGUOUS = "L1_AMBIGUOUS"
    L2_SUSPICIOUS = "L2_SUSPICIOUS"
    L3_CRITICAL = "L3_CRITICAL"

    @classmethod
    def from_alias(cls, value: str) -> ThreatLevel:
        """Resolve either a canonical name or a Phase 1 prompt alias (DR-03)."""
        aliases = {
            "L0_IGNORE": cls.L0_SAFE,
            "L1_OBSERVE": cls.L1_AMBIGUOUS,
            "L2_DETER": cls.L2_SUSPICIOUS,
            "L3_CRITICAL_DISPATCH": cls.L3_CRITICAL,
        }
        if value in aliases:
            return aliases[value]
        return cls(value)


class DetectedSubject(str, Enum):
    """Subject classification (SPEC.md §2.3 / §5.2)."""

    FAMILY = "FAMILY"
    BENIGN_STRANGER = "BENIGN_STRANGER"
    SUSPICIOUS_STRANGER = "SUSPICIOUS_STRANGER"
    HOSTILE_INTRUDER = "HOSTILE_INTRUDER"
    ANIMAL_ENVIRONMENTAL = "ANIMAL_ENVIRONMENTAL"


class AudioSentiment(str, Enum):
    """Audio sentiment classes (SPEC.md §5.2)."""

    BENIGN = "BENIGN"
    NEUTRAL = "NEUTRAL"
    HOSTILE = "HOSTILE"
    BREACH_NOISE = "BREACH_NOISE"
    INDETERMINATE = "INDETERMINATE"


class MeshAction(str, Enum):
    """Recommended coordinated mesh action (SPEC.md §5.2)."""

    SILENT_PASS = "SILENT_PASS"  # noqa: S105 - enum action value, not a secret
    NOTIFY_HOST = "NOTIFY_HOST"
    WAKE_HOST_AND_DETER = "WAKE_HOST_AND_DETER"
    DISPATCH_EMERGENCY = "DISPATCH_EMERGENCY"


class HostState(str, Enum):
    """Resident state inferred from Bee / Apple Watch (SPEC.md §2.4)."""

    AWAKE = "H_awake"
    ASLEEP = "H_asleep"
    AWAY = "H_away"
    DISTRESS = "H_distress"
    UNKNOWN = "H_unknown"  # Bee off-wrist fail-safe (DMP D1)


# --------------------------------------------------------------------------- #
# Signal integrity vector  Φ = [Φ_M, Φ_V, Φ_A, Φ_net]^T ∈ [0,1]^4
# --------------------------------------------------------------------------- #
class IntegrityVector(BaseModel):
    """The 4D signal integrity vector (SPEC.md §2.2).

    Each component is a continuous confidence in [0.0, 1.0]. The spec enumerates
    canonical rungs {0.0 failed, 0.5 degraded, 1.0 nominal} but the auditor may
    emit intermediate values; the type enforces only the bounds.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    phi_m: float = Field(..., ge=0.0, le=1.0, description="Motion / PIR integrity")
    phi_v: float = Field(..., ge=0.0, le=1.0, description="Vision / optical integrity")
    phi_a: float = Field(..., ge=0.0, le=1.0, description="Acoustic integrity")
    phi_net: float = Field(..., ge=0.0, le=1.0, description="Network integrity")

    def as_list(self) -> list[float]:
        """Return [Φ_M, Φ_V, Φ_A, Φ_net] in canonical order."""
        return [self.phi_m, self.phi_v, self.phi_a, self.phi_net]

    @property
    def any_failed(self) -> bool:
        return any(v <= 0.0 for v in self.as_list())

    @property
    def optical_tampered(self) -> bool:
        """Φ_V == 0 → spray paint / tape / laser wash (zero-grace override)."""
        return self.phi_v <= 0.0


# --------------------------------------------------------------------------- #
# Perimeter event (Ring telemetry)
# --------------------------------------------------------------------------- #
class PerimeterEvent(BaseModel):
    """Raw perimeter telemetry from the Ring sensor triad (SPEC.md §2.1)."""

    model_config = ConfigDict(extra="forbid")

    timestamp: float = Field(default_factory=time.time, description="Unix epoch seconds")
    camera_id: str = Field(..., min_length=1)
    image_path: str | None = Field(
        default=None, description="Path to raw frame on disk (mutually usable with image_bytes)"
    )
    image_bytes: bytes | None = Field(
        default=None, description="Raw frame buffer; preferred for in-memory pipelines"
    )
    pir_motion: bool = Field(default=False, description="Binary PIR trip (M ∈ {0,1})")
    acoustic_db: float = Field(
        default=0.0, ge=0.0, le=194.0, description="Ambient acoustic level in dB SPL"
    )
    optical_integrity: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Pre-computed Φ_V if available"
    )

    @field_validator("image_bytes")
    @classmethod
    def _non_empty_bytes(cls, v: bytes | None) -> bytes | None:
        if v is not None and len(v) == 0:
            raise ValueError("image_bytes must be non-empty when provided")
        return v


# --------------------------------------------------------------------------- #
# Wearer biological context (Bee / Apple Watch)
# --------------------------------------------------------------------------- #
class WearerBioContext(BaseModel):
    """Resident biological context (SPEC.md §2.4, §7 Bio-Grounding reality)."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., min_length=1)
    host_state: HostState = Field(default=HostState.UNKNOWN)
    heart_rate: int | None = Field(
        default=None,
        ge=20,
        le=250,
        description="BPM — Tier B (Apple Watch/HealthKit) only; Bee Pioneer has no PPG",
    )
    is_asleep: bool = Field(
        default=False, description="H_asleep: conversational silence >1h + accelerometer stillness"
    )
    minutes_since_last_speech: int | None = Field(
        default=None, ge=0, description="Derived from `bee now --json` utterance timestamps"
    )
    motion_level: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Accelerometer-derived locomotion intensity"
    )
    on_wrist: bool = Field(default=True)
    device_tier: str = Field(
        default="bee_pioneer", description="'bee_pioneer' (screenless clip) or 'apple_watch'"
    )

    @field_validator("device_tier")
    @classmethod
    def _valid_tier(cls, v: str) -> str:
        if v not in {"bee_pioneer", "apple_watch"}:
            raise ValueError("device_tier must be 'bee_pioneer' or 'apple_watch'")
        return v


# --------------------------------------------------------------------------- #
# NENA Digital CAD staging packet
# --------------------------------------------------------------------------- #
class CadPacket(BaseModel):
    """NENA-compliant Digital CAD manifest, staged for 1-tap resident dispatch.

    Software never auto-dials 911 (SPEC.md §7 — illegal under 47 U.S.C. §227).
    This is a formatted manifest only.
    """

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(..., min_length=1)
    created_at: float = Field(default_factory=time.time)
    nena_format: str = Field(default="RapidSOS")
    sha256: str = Field(
        ..., min_length=64, max_length=64, description="Integrity hash of the manifest"
    )
    gps_lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    gps_lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    evidence_timeline: list[str] = Field(default_factory=list)
    photographic_stills: list[str] = Field(default_factory=list)
    threat_summary: str = Field(default="")
    staged: bool = Field(default=True, description="Staged for 1-tap send; never auto-transmitted")


# --------------------------------------------------------------------------- #
# Threat assessment (Bedrock output — SPEC.md §5.2 schema)
# --------------------------------------------------------------------------- #
class ThreatAssessment(BaseModel):
    """Structured threat assessment matching SPEC.md §5.2 Bedrock JSON schema."""

    model_config = ConfigDict(extra="forbid")

    threat_level: ThreatLevel
    threat_score: float = Field(..., ge=0.0, le=1.0)
    detected_subject: DetectedSubject
    visual_findings: list[str] = Field(default_factory=list)
    audio_sentiment: AudioSentiment = Field(default=AudioSentiment.INDETERMINATE)
    recommended_mesh_action: MeshAction
    justification: str = Field(..., min_length=1, description="Chain-of-thought rationale")
    recommended_actuators: list[str] = Field(default_factory=list)
    cad_packet: CadPacket | None = Field(default=None)

    @field_validator("threat_level", mode="before")
    @classmethod
    def _resolve_alias(cls, v):
        """Accept canonical names or DR-03 aliases on input."""
        if isinstance(v, str):
            return ThreatLevel.from_alias(v)
        return v
