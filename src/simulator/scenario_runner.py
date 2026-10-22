"""Deterministic scenario runner (Phase 8 — tasks.md Task 8.2).

Loads the 10 baseline scenarios from ``canned_scenarios.json`` and drives each one
through the real pipeline:

    fixture ingest  ->  IntegrityVector (Phi)  ->  StateMachine.evaluate
                    ->  Transition (level, action, actuators)  ->  CadStaging (on dispatch)

The runner is deterministic by design: it uses the local edge path (the
StateMachine), not a live Bedrock call, so the asserted threat bands are
reproducible offline — exactly what the baseline test suite and the UI's
scenario selector need. A fixed ``now`` makes dwell/CAD timing exact.

CLI:
    python -m src.simulator.scenario_runner --scenario 06
    python -m src.simulator.scenario_runner --all
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from src.core.cad_dispatcher import CadStaging, stage_cad_dispatch
from src.core.state_machine import (
    GuardMode,
    StateMachine,
    ThreatSignals,
    Transition,
)
from src.core.types import IntegrityVector, MeshAction, ThreatLevel

_FIXTURE_PATH = Path(__file__).with_name("canned_scenarios.json")

# Fixed evaluation epoch so dwell/CAD timing is deterministic across runs.
_EPOCH = 1_000_000.0


@dataclass(frozen=True)
class ScenarioResult:
    """The end-to-end outcome of one scenario run."""

    scenario_id: str
    title: str
    mode: GuardMode
    level: ThreatLevel
    action: MeshAction
    permitted_actuators: tuple[str, ...]
    cad_staged: bool
    cad_sha256: Optional[str]
    transition: Transition

    def as_dict(self) -> dict:
        """JSON-serializable view for the web console / CLI."""
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "mode": self.mode.value,
            "level": self.level.value,
            "action": self.action.value,
            "permitted_actuators": list(self.permitted_actuators),
            "cad_staged": self.cad_staged,
            "cad_sha256": self.cad_sha256,
        }


def load_scenarios() -> dict[str, dict]:
    """Load the fixture catalog keyed by scenario id."""
    data = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {s["id"]: s for s in data["scenarios"]}


def _signals_from_fixture(fixture: dict) -> ThreatSignals:
    raw = fixture.get("signals", {})
    phi_v = float(fixture.get("phi_v", 1.0))
    integrity = IntegrityVector(phi_m=1.0, phi_v=phi_v, phi_a=1.0, phi_net=1.0)
    return ThreatSignals(
        integrity=integrity,
        weapon_detected=bool(raw.get("weapon_detected", False)),
        masked_near_entry=bool(raw.get("masked_near_entry", False)),
        breach_acoustics=bool(raw.get("breach_acoustics", False)),
        distress_flag=bool(raw.get("distress_flag", False)),
        motion_indicator=bool(raw.get("motion_indicator", False)),
        visual_indicator=bool(raw.get("visual_indicator", False)),
        acoustic_indicator=bool(raw.get("acoustic_indicator", False)),
    )


def _resolve_fixture(scenario: Union[str, dict], catalog: dict[str, dict]) -> dict:
    """Accept a full fixture dict, a full id, or a 2-digit prefix like '06'."""
    if isinstance(scenario, dict):
        return scenario
    if scenario in catalog:
        return catalog[scenario]
    # Prefix match on the leading numeric id (e.g. '06' -> '06_covert_entry_breach').
    matches = [sid for sid in catalog if sid.split("_", 1)[0] == scenario.zfill(2)]
    if len(matches) == 1:
        return catalog[matches[0]]
    raise KeyError(f"unknown scenario '{scenario}' (known: {sorted(catalog)})")


def run_scenario(scenario: Union[str, dict], *, catalog: Optional[dict] = None) -> ScenarioResult:
    """Run one scenario end-to-end and return its deterministic result."""
    catalog = catalog if catalog is not None else load_scenarios()
    fixture = _resolve_fixture(scenario, catalog)

    mode = GuardMode(fixture["mode"])
    signals = _signals_from_fixture(fixture)
    score = float(fixture["score"])

    sm = StateMachine(mode=mode)
    transition = sm.evaluate(score, signals, now=_EPOCH)

    cad_staged = False
    cad_sha256: Optional[str] = None
    if transition.action is MeshAction.DISPATCH_EMERGENCY:
        staging: CadStaging = stage_cad_dispatch(
            incident_id=fixture["id"],
            staged_at=_EPOCH,
            threat_summary=fixture["title"],
            evidence_timeline=["ingest", "integrity_evaluated", "state_resolved", "cad_staged"],
        )
        cad_staged = True
        cad_sha256 = staging.packet.sha256

    return ScenarioResult(
        scenario_id=fixture["id"],
        title=fixture["title"],
        mode=mode,
        level=transition.level,
        action=transition.action,
        permitted_actuators=transition.permitted_actuators,
        cad_staged=cad_staged,
        cad_sha256=cad_sha256,
        transition=transition,
    )


def run_all() -> list[ScenarioResult]:
    """Run every baseline scenario in catalog order."""
    catalog = load_scenarios()
    return [run_scenario(sid, catalog=catalog) for sid in catalog]


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Amazon Vigil deterministic scenario runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="scenario id or 2-digit prefix, e.g. 06")
    group.add_argument("--all", action="store_true", help="run all baseline scenarios")
    args = parser.parse_args()

    results = run_all() if args.all else [run_scenario(args.scenario)]
    print(json.dumps([r.as_dict() for r in results], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
