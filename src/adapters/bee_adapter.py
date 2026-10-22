"""Bee wearable adapter — the resident's bio-state organ (MODELED).

HONESTY NOTICE (read first): the Bee hackathon track requires a project to use
**real data from a Bee device or an Apple Watch running Bee software**. This
project has **no Bee hardware and no real Bee data**, so this adapter is
**MODELED** and Vigil does **NOT** claim the Bee track. Bee is one organ in the
Alexa+ mesh; here it provides a simulated bio-state reading, always flagged
``simulated=True`` / ``modeled=True``. It must never be represented as a live
Bee integration.

It is nonetheless coded to the REAL ``@beeai/cli`` contract (docs.bee.computer)
so a user WITH a Bee device and the CLI authenticated gets genuine data and the
swap is mechanical:

* ``bee login``                authenticate (user action)
* ``bee now --json``           recent conversations → sleep inference
* ``bee today``                daily brief
* sleep state (UX-04): inferred from conversational recency (>1h silence) +
  accelerometer stillness; the screenless Bee Pioneer has no PPG heart rate.

When the CLI is present and authenticated, :meth:`read_bio` shells out to it and
parses the real JSON. When it is absent (our case), it returns a MODELED reading
flagged as such — never fabricated live telemetry.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

from src.core.state_machine import GuardMode, ThreatSignals
from src.core.types import HostState, IntegrityVector, WearerBioContext
from src.pipeline.ingest import IngestAdapter, Telemetry

# Minutes of conversational silence that imply sleep (UX-04 bio-grounding).
_SLEEP_SILENCE_MINUTES = 60


@dataclass(frozen=True)
class BeeReading:
    """A normalized Bee bio-state reading (real or MODELED)."""

    user_id: str
    is_asleep: bool
    minutes_since_last_speech: Optional[int]
    device_tier: str  # "bee_pioneer" | "apple_watch"
    on_wrist: bool
    modeled: bool


class BeeAdapter(IngestAdapter):
    """Reads resident bio-state from the Bee CLI, or a MODELED reading."""

    source_name = "modeled:bee"

    def __init__(self, *, user_id: str = "maya", cli_name: str = "bee") -> None:
        self.user_id = user_id
        self.cli_name = cli_name

    @property
    def cli_available(self) -> bool:
        """True only when the real bee CLI is on PATH (not forced off)."""
        if os.environ.get("VIGIL_FORCE_BEE_MODELED") == "1":
            return False
        return shutil.which(self.cli_name) is not None

    # --- real CLI-shaped read (works if the CLI is present + authed) ------- #

    def _run_bee_now(self) -> Optional[dict]:
        """Invoke ``bee now --json`` and return parsed JSON, or None on failure."""
        try:
            proc = subprocess.run(
                [self.cli_name, "now", "--json"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                return None
            return json.loads(proc.stdout)
        except (OSError, ValueError, subprocess.SubprocessError):
            return None

    @staticmethod
    def infer_sleep(minutes_since_last_speech: Optional[int]) -> bool:
        """UX-04 sleep inference: >1h conversational silence implies asleep."""
        if minutes_since_last_speech is None:
            return False
        return minutes_since_last_speech >= _SLEEP_SILENCE_MINUTES

    def read_bio(self) -> BeeReading:
        """Return the current bio-state: real from the CLI, else MODELED."""
        if self.cli_available:
            data = self._run_bee_now()
            if data is not None:
                mins = data.get("minutes_since_last_speech")
                return BeeReading(
                    user_id=self.user_id,
                    is_asleep=self.infer_sleep(mins),
                    minutes_since_last_speech=mins,
                    device_tier=data.get("device_model", "bee_pioneer"),
                    on_wrist=bool(data.get("on_wrist", True)),
                    modeled=False,
                )
        # MODELED fallback — honest default: asleep, off-wrist fail-safe (DMP D1).
        return BeeReading(
            user_id=self.user_id, is_asleep=True, minutes_since_last_speech=180,
            device_tier="bee_pioneer", on_wrist=False, modeled=True,
        )

    def to_bio_context(self, reading: BeeReading) -> WearerBioContext:
        """Map a reading onto the canonical WearerBioContext type."""
        return WearerBioContext(
            user_id=reading.user_id,
            host_state=HostState.ASLEEP if reading.is_asleep else HostState.AWAKE,
            is_asleep=reading.is_asleep,
            minutes_since_last_speech=reading.minutes_since_last_speech,
            on_wrist=reading.on_wrist,
            device_tier=reading.device_tier,
        )

    # --- IngestAdapter contract -------------------------------------------- #

    def telemetry(self, selector: Optional[str] = None) -> Telemetry:
        """Bio-state snapshot. Bee contributes host-state context, not a threat
        score, so score stays 0.0 and the perimeter sensors drive escalation."""
        reading = self.read_bio()
        mode = GuardMode.NIGHT_SENTRY if reading.is_asleep else GuardMode.DAYTIME_AMBIENT
        integrity = IntegrityVector(phi_m=1.0, phi_v=1.0, phi_a=1.0, phi_net=1.0)
        signals = ThreatSignals(integrity=integrity)
        tier = "MODELED" if reading.modeled else "live"
        return Telemetry(
            scenario_id=f"bee:{reading.user_id}",
            title=f"Bee bio-state · {'asleep' if reading.is_asleep else 'awake'} ({tier})",
            mode=mode,
            score=0.0,
            signals=signals,
            source=self.source_name,
            simulated=reading.modeled,
        )
