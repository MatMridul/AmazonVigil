"""FastMCP Security Server (Task 1.5).

Exposes the 8 canonical Amazon Vigil tools over MCP Streamable HTTP
(MCP Spec 2025-11-25+), using the official ``mcp`` SDK (DR-01):
``from mcp.server.fastmcp import FastMCP``.

Actuation tools honor ``incident_id`` / ``idempotency_token`` (governance rule 5)
and are protected by an in-memory 15-second deduplication cache. Peripheral device
effects are simulated in Phase 1 (DR-04).
"""

from __future__ import annotations

import os
import time
from threading import Lock
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.adapters.bedrock_analyzer import BedrockThreatEvaluator
from src.core.cad_dispatcher import build_cad_packet
from src.core.integrity_auditor import compute_optical_integrity
from src.core.types import IntegrityVector, PerimeterEvent, WearerBioContext

# Idempotency dedup window (governance rule 5).
IDEMPOTENCY_TTL_SECONDS = 15.0


class IdempotencyCache:
    """In-memory TTL cache keyed on idempotency_token (thread-safe)."""

    def __init__(self, ttl: float = IDEMPOTENCY_TTL_SECONDS, *, clock=time.monotonic) -> None:
        self._ttl = ttl
        self._clock = clock
        self._seen: dict[str, float] = {}
        self._lock = Lock()

    def check_and_set(self, token: str) -> bool:
        """Return True if ``token`` is a fresh (non-duplicate) call, else False.

        An empty token is always treated as fresh (no dedup requested).
        """
        if not token:
            return True
        now = self._clock()
        with self._lock:
            # Evict expired entries.
            expired = [k for k, ts in self._seen.items() if now - ts > self._ttl]
            for k in expired:
                del self._seen[k]
            if token in self._seen:
                return False
            self._seen[token] = now
            return True


# --------------------------------------------------------------------------- #
# Server + shared singletons
# --------------------------------------------------------------------------- #
def _build_transport_security():
    """Allow-list the public tunnel/deploy host alongside localhost.

    DNS-rebinding protection stays ON (MCP spec); we explicitly add the public
    host from VIGIL_PUBLIC_URL so Alexa+ / a tunneled client is accepted while
    arbitrary foreign Hosts are still rejected. Without this, a tunneled request
    hits the default localhost-only allow-list and the transport returns 421.
    """
    from urllib.parse import urlparse

    from mcp.server.transport_security import TransportSecuritySettings

    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
    public = os.environ.get("VIGIL_PUBLIC_URL", "").strip()
    if public:
        host = urlparse(public).netloc or public
        allowed_hosts += [host, f"{host}:*"]
        allowed_origins += [f"https://{host}", f"https://{host}:*"]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


mcp = FastMCP("amazon-vigil", transport_security=_build_transport_security())
_dedup = IdempotencyCache()
_evaluator = BedrockThreatEvaluator()

# SEC.2 — value-checked, lockout-protected disarm-PIN verifier (holds only a
# hash, loaded from config; never a literal PIN).
from src.mcp_auth import default_pin_verifier

_pin_verifier = default_pin_verifier()

# Minimal in-memory incident store for Phase 1 reasoning/disarm tools.
_incidents: dict[str, dict] = {}


def _duplicate_response(token: str) -> dict:
    return {"status": "duplicate_suppressed", "idempotency_token": token}


# --------------------------------------------------------------------------- #
# 1. audit_perimeter_event
# --------------------------------------------------------------------------- #
@mcp.tool()
async def audit_perimeter_event(event_payload: dict) -> dict:
    """Ingest raw Ring telemetry, evaluate the Φ integrity vector, and return a
    normalized event with degradation flags."""
    event = PerimeterEvent.model_validate(event_payload)

    phi_v = event.optical_integrity
    optical_reason = "precomputed"
    if phi_v is None and event.image_bytes is not None:
        report = compute_optical_integrity(event.image_bytes)
        phi_v = report.phi_v
        optical_reason = report.reason
    elif phi_v is None:
        phi_v = 1.0  # no frame supplied; assume nominal optical in Phase 1

    integrity = IntegrityVector(
        phi_m=1.0 if event.pir_motion else 0.5,
        phi_v=phi_v,
        phi_a=0.0 if event.acoustic_db <= 0.0 else 1.0,
        phi_net=1.0,
    )
    return {
        "camera_id": event.camera_id,
        "timestamp": event.timestamp,
        "integrity_vector": {
            "phi_m": integrity.phi_m,
            "phi_v": integrity.phi_v,
            "phi_a": integrity.phi_a,
            "phi_net": integrity.phi_net,
        },
        "optical_tampered": integrity.optical_tampered,
        "optical_reason": optical_reason,
        "degraded": integrity.any_failed,
    }


# --------------------------------------------------------------------------- #
# 2. query_wearer_state
# --------------------------------------------------------------------------- #
@mcp.tool()
async def query_wearer_state(user_id: str) -> dict:
    """Query Bee context (simulated in Phase 1) for wearer sleep/awake state."""
    if not user_id:
        raise ValueError("user_id is required")
    # Phase 1 simulation: conservative fail-safe default (DMP D1).
    bio = WearerBioContext(user_id=user_id, is_asleep=True, on_wrist=False)
    return {
        "user_id": user_id,
        "is_awake": not bio.is_asleep,
        "inference_basis": "speech_recency_and_stillness",
        "minutes_since_last_speech": bio.minutes_since_last_speech,
        "device_tier": bio.device_tier,
        "heart_rate": bio.heart_rate,
        "on_wrist": bio.on_wrist,
    }


# --------------------------------------------------------------------------- #
# 3. trigger_tactical_wake
# --------------------------------------------------------------------------- #
@mcp.tool()
async def trigger_tactical_wake(
    user_id: str, channel: str = "echo_whisper", idempotency_token: str = ""
) -> dict:
    """Private interior wake: bedroom Echo whisper + nightstand phone hum."""
    if not user_id:
        raise ValueError("user_id is required")
    if not _dedup.check_and_set(idempotency_token):
        return _duplicate_response(idempotency_token)
    return {
        "status": "wake_triggered",
        "user_id": user_id,
        "channel": channel,
        "simulated": True,
        "idempotency_token": idempotency_token,
    }


# --------------------------------------------------------------------------- #
# 4. trigger_firetv_deterrence
# --------------------------------------------------------------------------- #
@mcp.tool()
async def trigger_firetv_deterrence(
    mode: str, volume_percent: int, idempotency_token: str = ""
) -> dict:
    """Launch Fire TV deterrent ('simulated_party' | 'dog_bark' | 'camera_feed'),
    preceded by a 150 ms hallway Echo Boot-Bridge footstep."""
    valid_modes = {"simulated_party", "dog_bark", "camera_feed"}
    if mode not in valid_modes:
        raise ValueError(f"mode must be one of {sorted(valid_modes)}")
    if not 0 <= volume_percent <= 100:
        raise ValueError("volume_percent must be in [0, 100]")
    if not _dedup.check_and_set(idempotency_token):
        return _duplicate_response(idempotency_token)
    return {
        "status": "deterrence_launched",
        "mode": mode,
        "volume_percent": volume_percent,
        "boot_bridge_ms": 150,
        "simulated": True,
        "idempotency_token": idempotency_token,
    }


# --------------------------------------------------------------------------- #
# 5. format_emergency_cad_packet
# --------------------------------------------------------------------------- #
@mcp.tool()
async def format_emergency_cad_packet(incident_id: str) -> dict:
    """Compile a NENA/RapidSOS Digital CAD manifest with a SHA-256 hash."""
    if not incident_id:
        raise ValueError("incident_id is required")
    packet = build_cad_packet(
        incident_id,
        threat_summary="Active residential breach attempt (simulated Phase 1).",
        evidence_timeline=["event_ingested", "integrity_evaluated", "cad_staged"],
    )
    _incidents.setdefault(incident_id, {})["cad"] = packet.model_dump()
    return packet.model_dump()


# --------------------------------------------------------------------------- #
# 6. disarm_perimeter_alert
# --------------------------------------------------------------------------- #
@mcp.tool()
async def disarm_perimeter_alert(incident_id: str, disarm_pin: str) -> dict:
    """Cancel CAD staging + disarm perimeter on a VERIFIED disarm PIN.

    SEC.2: the PIN is checked by VALUE against a stored hash (never by format
    alone), with brute-force lockout. A wrong 4-digit guess does NOT disarm.
    """
    if not incident_id:
        raise ValueError("incident_id is required")
    if _pin_verifier.is_locked():
        return {"status": "rejected", "reason": "locked_out", "incident_id": incident_id}
    if not _pin_verifier.verify(disarm_pin):
        return {"status": "rejected", "reason": "invalid_pin", "incident_id": incident_id}
    _incidents.setdefault(incident_id, {})["disarmed"] = True
    return {"status": "disarmed", "incident_id": incident_id}


# --------------------------------------------------------------------------- #
# 7. explain_incident_reasoning
# --------------------------------------------------------------------------- #
@mcp.tool()
async def explain_incident_reasoning(incident_id: Optional[str] = None) -> dict:
    """Return a plain-English incident summary and justification."""
    if incident_id is None:
        return {
            "summary": "No incident specified; perimeter nominal.",
            "incidents_known": list(_incidents.keys()),
        }
    record = _incidents.get(incident_id)
    if record is None:
        return {"status": "unknown_incident", "incident_id": incident_id}
    return {
        "incident_id": incident_id,
        "summary": "Simulated Phase 1 incident reasoning.",
        "disarmed": record.get("disarmed", False),
        "cad_staged": "cad" in record,
    }


# --------------------------------------------------------------------------- #
# 8. set_mesh_guard_profile
# --------------------------------------------------------------------------- #
@mcp.tool()
async def set_mesh_guard_profile(mode: str, duration_hours: Optional[int] = None) -> dict:
    """Adjust the operational profile (Daytime Ambient | Night Sentry |
    Vacation | Duress)."""
    valid = {"daytime_ambient", "night_sentry", "vacation", "duress"}
    if mode not in valid:
        raise ValueError(f"mode must be one of {sorted(valid)}")
    if duration_hours is not None and duration_hours <= 0:
        raise ValueError("duration_hours must be positive when provided")
    return {"status": "profile_set", "mode": mode, "duration_hours": duration_hours}


def build_asgi_app():
    """Compose the MCP Streamable-HTTP app with Alexa+ OAuth discovery endpoints.

    Serves, on the same ASGI app the MCP transport uses:
      * GET /.well-known/oauth-protected-resource  -> PRM document (RFC 9728)
      * GET /.well-known/oauth-authorization-server -> AS metadata (RFC 8414)
    The MCP endpoint itself is unchanged, so a properly-formed MCP client still
    initializes and lists tools exactly as before. These well-known documents are
    what Alexa+ fetches during account linking to discover PKCE/S256 support.
    """
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    from src.mcp_auth import BearerAuthMiddleware, auth_enforced, default_server

    auth = default_server()
    app = mcp.streamable_http_app()

    async def prm(_request: "Request") -> "JSONResponse":
        return JSONResponse(auth.prm_document())

    async def as_meta(_request: "Request") -> "JSONResponse":
        return JSONResponse(auth.as_metadata())

    async def healthz(_request: "Request") -> "JSONResponse":
        return JSONResponse({"status": "ok", "auth_enforced": auth_enforced()})

    app.router.add_route(
        "/.well-known/oauth-protected-resource", prm, methods=["GET"]
    )
    app.router.add_route(
        "/.well-known/oauth-authorization-server", as_meta, methods=["GET"]
    )
    app.router.add_route("/healthz", healthz, methods=["GET"])

    # SEC.1 — deny-by-default bearer enforcement at the transport layer. Every
    # request except discovery/health must carry a valid Bearer, so no tool can
    # be reached unauthenticated. Added last so it wraps the whole app.
    app.add_middleware(BearerAuthMiddleware, server=auth)
    return app


def main() -> None:
    """Run the FastMCP server over Streamable HTTP (MCP transport only)."""
    mcp.run(transport="streamable-http")


def main_with_discovery() -> None:
    """Run the composed app (MCP + OAuth discovery endpoints) via uvicorn."""
    import uvicorn

    uvicorn.run(build_asgi_app(), host=mcp.settings.host, port=mcp.settings.port)


if __name__ == "__main__":
    import sys

    if "--with-discovery" in sys.argv:
        main_with_discovery()
    else:
        main()
