"""The shared ingest seam (one pipeline, two sources).

``IngestAdapter`` is the single interface every ingest source implements. It
yields a normalized :class:`Telemetry` snapshot — the operational mode, the
seed threat score, the discrete :class:`ThreatSignals`, and a human-readable
summary — which :class:`VigilPipeline` drives through the *real* deterministic
engine (``StateMachine.evaluate`` → ``Transition`` → ``CadStaging`` on
dispatch), producing the same :class:`ScenarioResult` the Phase 8 runner emits.

Two concrete adapters ship:

* :class:`DemoAdapter` — replays the 10 canned baseline scenarios through the
  real runner. Zero external dependencies; deterministic; this is what the web
  console's scenario selector and the offline demo use.
* :class:`LiveAdapter` — reads a telemetry snapshot from the real device
  adapters (Ring / Bee / Fire TV / Alexa+ ingest). It is importable and
  constructs cleanly; when a device or its credentials are absent it falls back
  to a clearly-flagged simulated snapshot (``simulated=True``) rather than
  fabricating a live reading. The live wiring per device lands with each
  device adapter; this seam defines the contract they fill.

The seam is the honesty boundary in code: ``Telemetry.simulated`` and
``Telemetry.source`` travel with every snapshot, so the UI can badge a MODELED
reading as MODELED and a live reading as live, by construction — never by prose.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional

from src.core.state_machine import GuardMode, StateMachine, ThreatSignals
from src.core.types import IntegrityVector, MeshAction
from src.simulator.scenario_runner import (
    ScenarioResult,
    _signals_from_fixture,
    load_scenarios,
    run_scenario,
)

# Fixed evaluation epoch, shared with the scenario runner so demo and live
# results use identical dwell/CAD timing semantics.
_EPOCH = 1_000_000.0


@dataclass(frozen=True)
class Telemetry:
    """A normalized ingest snapshot handed to the pipeline.

    This is the single shape every source produces, whether the bytes came from
    a canned fixture or a live Ring/Bee feed. ``source`` and ``simulated`` are
    the honesty markers that travel downstream to the UI.
    """

    scenario_id: str
    title: str
    mode: GuardMode
    score: float
    signals: ThreatSignals
    source: str  # e.g. "demo", "live:ring", "live:bee"
    simulated: bool  # True when no real device/creds produced this snapshot


class IngestAdapter(abc.ABC):
    """The one interface every ingest source implements."""

    #: Short, stable identifier for this source (used in Telemetry.source).
    source_name: str = "abstract"

    @abc.abstractmethod
    def telemetry(self, selector: Optional[str] = None) -> Telemetry:
        """Return the current normalized telemetry snapshot.

        ``selector`` lets a source pick among several readings (the demo
        adapter uses it as the scenario id; a live adapter may ignore it).
        """
        raise NotImplementedError


class DemoAdapter(IngestAdapter):
    """Replays the 10 canned baseline scenarios through the real runner.

    Deterministic and dependency-free: the demo surface and the offline demo
    video both drive the identical pipeline a live deployment would, with the
    only difference being that the ingest bytes come from
    ``canned_scenarios.json`` instead of a device.
    """

    source_name = "demo"

    def __init__(self) -> None:
        self._catalog = load_scenarios()

    def scenario_ids(self) -> list[str]:
        """Catalog order — what the UI scenario selector lists."""
        return list(self._catalog)

    def telemetry(self, selector: Optional[str] = None) -> Telemetry:
        if selector is None:
            selector = next(iter(self._catalog))
        # Reuse the runner's own fixture resolution via run_scenario's catalog.
        fixture = self._resolve(selector)
        return Telemetry(
            scenario_id=fixture["id"],
            title=fixture["title"],
            mode=GuardMode(fixture["mode"]),
            score=float(fixture["score"]),
            signals=_signals_from_fixture(fixture),
            source=self.source_name,
            simulated=True,
        )

    def _resolve(self, selector: str) -> dict:
        if selector in self._catalog:
            return self._catalog[selector]
        matches = [
            sid for sid in self._catalog if sid.split("_", 1)[0] == selector.zfill(2)
        ]
        if len(matches) == 1:
            return self._catalog[matches[0]]
        raise KeyError(
            f"unknown scenario '{selector}' (known: {sorted(self._catalog)})"
        )


class LiveAdapter(IngestAdapter):
    """Reads telemetry from the real device adapters (Ring/Bee/Fire TV/Alexa+).

    Importable and constructs cleanly with no hardware present. When a device or
    its credentials are unavailable, :meth:`telemetry` returns a snapshot with
    ``simulated=True`` and a neutral baseline reading rather than fabricating a
    live event — the honest fallback. Each device adapter fills in its real
    read path as it lands; this class defines the contract and the safe default.
    """

    source_name = "live"

    def __init__(self, *, device_source: str = "live") -> None:
        self._device_source = device_source

    def telemetry(self, selector: Optional[str] = None) -> Telemetry:
        # No live device wired yet → honest simulated baseline (quiet perimeter).
        integrity = IntegrityVector(phi_m=1.0, phi_v=1.0, phi_a=1.0, phi_net=1.0)
        signals = ThreatSignals(integrity=integrity)
        return Telemetry(
            scenario_id="live_baseline",
            title="Live perimeter (no device wired — simulated baseline)",
            mode=GuardMode.NIGHT_SENTRY,
            score=0.0,
            signals=signals,
            source=f"{self._device_source}:unwired",
            simulated=True,
        )


class VigilPipeline:
    """Drives any adapter's telemetry through the real deterministic engine.

    The pipeline is the single reasoning spine. It does not know or care whether
    the snapshot came from a fixture or a live device — it runs the same
    ``StateMachine`` path and returns the same :class:`ScenarioResult` shape the
    Phase 8 runner emits, so the UI and MCP server have one result contract.
    """

    def __init__(self, adapter: IngestAdapter) -> None:
        self.adapter = adapter

    def process(self, selector: Optional[str] = None) -> ScenarioResult:
        """Ingest one snapshot and resolve it end-to-end.

        For the demo adapter this delegates to the shared ``run_scenario`` so the
        result is byte-identical to the Phase 8 baseline. For a live snapshot it
        runs the same engine directly on the normalized telemetry.
        """
        telem = self.adapter.telemetry(selector)

        if telem.simulated and telem.source == "demo":
            # Identical to the Phase 8 runner — one source of truth for demo.
            return run_scenario(telem.scenario_id)

        # Live (or non-demo) path: run the same engine on normalized telemetry.
        sm = StateMachine(mode=telem.mode)
        transition = sm.evaluate(telem.score, telem.signals, now=_EPOCH)
        cad_staged = transition.action is MeshAction.DISPATCH_EMERGENCY
        return ScenarioResult(
            scenario_id=telem.scenario_id,
            title=telem.title,
            mode=telem.mode,
            level=transition.level,
            action=transition.action,
            permitted_actuators=transition.permitted_actuators,
            cad_staged=cad_staged,
            cad_sha256=None,
            transition=transition,
        )
