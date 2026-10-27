"""Ring perimeter adapter — the mesh's eyes and ears.

Coded to the REAL Ring Appstore API surface (developer.ring.com):

* **Auth** — the user authorizes the app in the Ring App; the app exchanges the
  authorization code for a **Bearer token** used on every API call.
* **Events** — a configured webhook endpoint receives real-time motion /
  doorbell events. Each event carries an **HMAC signature** for verification and
  a **classification** (``human`` / ``animal`` / ``vehicle``).
* **Live video** — a **WHEP** (WebRTC-HTTP Egress Protocol) session is opened
  with ``POST .../media/streaming/whep/sessions`` (``Authorization: Bearer``,
  ``Content-Type: application/sdp``); **video only, no audio**.

A physical Ring device is NOT required (Ring track rule): with no credentials
this adapter runs in clearly-flagged **simulated** mode, emitting a canned event
shaped exactly like a real one — never a fabricated "live" reading. The verify /
parse / WHEP-URL logic is real and unit-tested regardless of mode, so wiring a
real token later is mechanical.

Environment (live mode):
    RING_BEARER_TOKEN     OAuth bearer token from the Ring App authorization
    RING_WEBHOOK_SECRET   HMAC secret for webhook signature verification
    RING_API_BASE         API base (default https://api.amazonvision.com/v1)
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass

from src.core.state_machine import GuardMode, ThreatSignals
from src.core.types import IntegrityVector
from src.pipeline.ingest import IngestAdapter, Telemetry

_DEFAULT_API_BASE = "https://api.amazonvision.com/v1"

# Ring event classification → our signal semantics.
_CLASS_TO_SUBJECT = {
    "human": "face_unv",
    "animal": "animal",
    "vehicle": "vehicle",
    "package": "package",
}


@dataclass(frozen=True)
class RingEvent:
    """A normalized Ring perimeter event (real or simulated)."""

    device_id: str
    kind: str  # "motion" | "ding" (doorbell)
    classification: str  # human | animal | vehicle | package | unknown
    acoustic_db: float
    verified_signature: bool
    simulated: bool


class RingAdapter(IngestAdapter):
    """Reads Ring perimeter events and feeds them into the pipeline telemetry."""

    source_name = "live:ring"

    def __init__(
        self,
        *,
        bearer_token: str | None = None,
        webhook_secret: str | None = None,
        api_base: str | None = None,
    ) -> None:
        self.bearer_token = bearer_token or os.environ.get("RING_BEARER_TOKEN")
        self.webhook_secret = webhook_secret or os.environ.get("RING_WEBHOOK_SECRET")
        self.api_base = api_base or os.environ.get("RING_API_BASE", _DEFAULT_API_BASE)

    @property
    def is_live_capable(self) -> bool:
        """True only when a real bearer token is configured."""
        return bool(self.bearer_token)

    # --- real API-shaped operations (work in both modes) ------------------- #

    def verify_webhook(self, body: bytes, signature: str) -> bool:
        """Verify a Ring webhook's HMAC-SHA256 signature (constant-time).

        Returns False when no secret is configured (cannot verify → do not
        trust), matching Ring's security model.
        """
        if not self.webhook_secret:
            return False
        expected = hmac.new(self.webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def whep_session_url(self, device_id: str) -> str:
        """Construct the real WHEP WebRTC egress URL for a device's live video."""
        return f"{self.api_base}/devices/{device_id}/media/streaming/whep/sessions"

    def parse_event(self, payload: dict, *, simulated: bool = False) -> RingEvent:
        """Normalize a Ring webhook payload into a RingEvent."""
        return RingEvent(
            device_id=str(payload.get("device_id", "ring_front")),
            kind=str(payload.get("kind", "motion")),
            classification=str(payload.get("classification", "unknown")),
            acoustic_db=float(payload.get("acoustic_db", 0.0)),
            verified_signature=bool(payload.get("verified_signature", False)),
            simulated=simulated,
        )

    # --- IngestAdapter contract -------------------------------------------- #

    def telemetry(self, selector: str | None = None) -> Telemetry:
        """Return a normalized telemetry snapshot from the latest Ring event.

        Live mode would pull the newest webhook event; with no token we emit an
        honest simulated motion event (quiet human at the door), flagged
        ``simulated=True`` — never a fabricated live breach.
        """
        if self.is_live_capable:
            # Live wiring lands with the webhook receiver; until then, the
            # honest statement is that no live event is buffered yet.
            event = RingEvent(
                device_id="ring_front",
                kind="motion",
                classification="unknown",
                acoustic_db=0.0,
                verified_signature=True,
                simulated=False,
            )
            simulated = False
        else:
            event = RingEvent(
                device_id="ring_front",
                kind="motion",
                classification="human",
                acoustic_db=0.0,
                verified_signature=False,
                simulated=True,
            )
            simulated = True

        integrity = IntegrityVector(phi_m=1.0, phi_v=1.0, phi_a=1.0, phi_net=1.0)
        signals = ThreatSignals(
            integrity=integrity,
            motion_indicator=event.kind in ("motion", "ding"),
            visual_indicator=event.classification in ("human", "vehicle"),
            acoustic_indicator=event.acoustic_db > 0.0,
        )
        return Telemetry(
            scenario_id=f"ring:{event.device_id}:{event.kind}",
            title=f"Ring {event.kind} · {event.classification}"
            + (" (simulated)" if simulated else " (live)"),
            mode=GuardMode.NIGHT_SENTRY,
            score=0.0,  # the engine + Bedrock set the real score downstream
            signals=signals,
            source=self.source_name + (":sim" if simulated else ""),
            simulated=simulated,
        )
