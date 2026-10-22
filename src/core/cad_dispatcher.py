"""Emergency NENA Digital CAD manifest generator (Phase 3 — tasks.md Task 3.3).

Promoted from the Phase 1 baseline (DR-04) to the full dispatch engine:

- NENA/RapidSOS structured manifest with a deterministic SHA-256 integrity hash
  (``build_cad_packet`` + ``_canonical_hash`` retained; the live MCP tool calls them).
- A 10-second safe-cancellation staging buffer (``CadStaging``): dispatch is held
  for a countdown during which a verified PIN aborts it.
- 4-digit PIN disarm verification (``verify_disarm_pin``).

Software NEVER auto-dials 911 (SPEC.md §7 — illegal under 47 U.S.C. §227). The
manifest is staged for 1-tap resident transmission only; the buffer governs when
the resident's 1-tap send becomes available, and gives an abort window.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional

from src.core.types import CadPacket

# Safe cancellation buffer before a staged CAD packet is sendable (SPEC.md §2).
CANCEL_BUFFER_SECONDS = 10.0


def _canonical_hash(payload: dict) -> str:
    """Deterministic SHA-256 over a canonical JSON serialization."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_cad_packet(
    incident_id: str,
    *,
    threat_summary: str = "",
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
    evidence_timeline: Optional[list[str]] = None,
    photographic_stills: Optional[list[str]] = None,
    created_at: Optional[float] = None,
) -> CadPacket:
    """Compile a staged NENA/RapidSOS CAD manifest for ``incident_id``."""
    if not incident_id:
        raise ValueError("incident_id is required")

    created = created_at if created_at is not None else time.time()
    timeline = evidence_timeline or []
    stills = photographic_stills or []

    hashable = {
        "incident_id": incident_id,
        "created_at": created,
        "nena_format": "RapidSOS",
        "gps_lat": gps_lat,
        "gps_lon": gps_lon,
        "evidence_timeline": timeline,
        "photographic_stills": stills,
        "threat_summary": threat_summary,
    }
    sha256 = _canonical_hash(hashable)

    return CadPacket(
        incident_id=incident_id,
        created_at=created,
        nena_format="RapidSOS",
        sha256=sha256,
        gps_lat=gps_lat,
        gps_lon=gps_lon,
        evidence_timeline=timeline,
        photographic_stills=stills,
        threat_summary=threat_summary,
        staged=True,
    )


def verify_disarm_pin(disarm_pin: str, expected_pin: Optional[str] = None) -> bool:
    """Validate a 4-digit disarm PIN.

    Format rule: exactly 4 ASCII digits. When ``expected_pin`` is supplied the
    value must also match it (constant-time compare); otherwise only the format
    is enforced (Phase 3 baseline — a secret store lands with the real adapters).
    """
    if not (isinstance(disarm_pin, str) and disarm_pin.isdigit() and len(disarm_pin) == 4):
        return False
    if expected_pin is not None:
        return hmac.compare_digest(disarm_pin, expected_pin)
    return True


@dataclass
class CadStaging:
    """A staged CAD dispatch under a safe-cancellation countdown.

    Pure and clock-injectable: ``now`` is always passed in so the buffer is
    testable without sleeping. States: ``staging`` (countdown running) ->
    ``ready`` (buffer elapsed, resident 1-tap send available) or ``cancelled``.
    """

    packet: CadPacket
    staged_at: float
    buffer_seconds: float = CANCEL_BUFFER_SECONDS
    cancelled: bool = False

    def remaining(self, *, now: float) -> float:
        """Seconds left in the cancellation buffer (0.0 once elapsed)."""
        if self.cancelled:
            return 0.0
        return max(0.0, self.buffer_seconds - (now - self.staged_at))

    def is_cancellable(self, *, now: float) -> bool:
        """True while the countdown is still running and not already cancelled."""
        return not self.cancelled and self.remaining(now=now) > 0.0

    def is_ready(self, *, now: float) -> bool:
        """True once the buffer has elapsed and the packet was not cancelled."""
        return not self.cancelled and self.remaining(now=now) <= 0.0

    def cancel(self, disarm_pin: str, *, now: float, expected_pin: Optional[str] = None) -> bool:
        """Abort the staged dispatch if the PIN is valid and still within buffer.

        Returns True on a successful cancellation, False if the PIN is invalid or
        the cancellation window has already closed.
        """
        if not self.is_cancellable(now=now):
            return False
        if not verify_disarm_pin(disarm_pin, expected_pin):
            return False
        self.cancelled = True
        return True


def stage_cad_dispatch(
    incident_id: str,
    *,
    staged_at: Optional[float] = None,
    buffer_seconds: float = CANCEL_BUFFER_SECONDS,
    **packet_kwargs,
) -> CadStaging:
    """Build a CAD packet and wrap it in a 10s safe-cancellation staging buffer."""
    staged = staged_at if staged_at is not None else time.time()
    packet = build_cad_packet(incident_id, created_at=staged, **packet_kwargs)
    return CadStaging(packet=packet, staged_at=staged, buffer_seconds=buffer_seconds)
