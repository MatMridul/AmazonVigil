"""Emergency NENA Digital CAD manifest generator (Phase 1 baseline — DR-04).

Formats a RapidSOS-shaped manifest with a SHA-256 integrity hash. Never dials
911 (SPEC.md §7 — automated robocalls are illegal); the manifest is staged for
1-tap resident transmission only. Expanded in Phase 3 (tasks.md Task 3.3).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Optional

from src.core.types import CadPacket


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
