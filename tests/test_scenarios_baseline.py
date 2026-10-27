"""Phase 8 — baseline scenario tests (tasks.md Task 8.2).

Drives all 10 SPEC.md §3 baseline scenarios end-to-end through the deterministic
runner and asserts the exact threat band, mesh action, actuator emptiness, and
CAD staging status declared in the fixture catalog.
"""

from __future__ import annotations

import pytest

from src.core.state_machine import GuardMode
from src.core.types import MeshAction, ThreatLevel
from src.simulator.scenario_runner import load_scenarios, run_all, run_scenario

_CATALOG = load_scenarios()
_IDS = list(_CATALOG.keys())


def test_catalog_has_ten_scenarios():
    assert len(_CATALOG) == 10


@pytest.mark.parametrize("scenario_id", _IDS)
def test_scenario_matches_expected_outcome(scenario_id):
    fixture = _CATALOG[scenario_id]
    result = run_scenario(scenario_id, catalog=_CATALOG)

    assert result.level == ThreatLevel(fixture["expected_level"]), (
        f"{scenario_id}: level {result.level} != {fixture['expected_level']}"
    )
    assert result.action == MeshAction(fixture["expected_action"]), (
        f"{scenario_id}: action {result.action} != {fixture['expected_action']}"
    )
    assert (len(result.permitted_actuators) == 0) == fixture["expected_actuators_empty"], (
        f"{scenario_id}: actuator emptiness mismatch (got {result.permitted_actuators})"
    )
    assert result.cad_staged == fixture["expected_cad_staged"], (
        f"{scenario_id}: cad_staged {result.cad_staged} != {fixture['expected_cad_staged']}"
    )


def test_duress_scenario_10_is_silent_but_dispatches():
    """Scenario 10 is the critical invariant: L3 dispatch with ZERO actuators."""
    r = run_scenario("10", catalog=_CATALOG)
    assert r.mode == GuardMode.SILENT_DURESS
    assert r.level == ThreatLevel.L3_CRITICAL
    assert r.action == MeshAction.DISPATCH_EMERGENCY
    assert r.permitted_actuators == ()  # complete silence
    assert r.cad_staged is True  # but CAD still goes out
    assert r.cad_sha256 is not None and len(r.cad_sha256) == 64


def test_forced_entry_scenario_07_dispatches_with_deterrents():
    r = run_scenario("07", catalog=_CATALOG)
    assert r.level == ThreatLevel.L3_CRITICAL
    assert r.cad_staged is True
    assert len(r.permitted_actuators) > 0  # not silent — night-sentry deterrents fire


def test_lens_tamper_scenario_08_escalates_via_zero_grace():
    """Scenario 08: phi_v=0 tamper + breach noise -> L2 even though score is sub-L2."""
    r = run_scenario("08", catalog=_CATALOG)
    assert r.level == ThreatLevel.L2_SUSPICIOUS
    assert r.action == MeshAction.WAKE_HOST_AND_DETER


def test_run_all_returns_ten_results():
    results = run_all()
    assert len(results) == 10
    assert all(r.cad_sha256 is None or len(r.cad_sha256) == 64 for r in results)


def test_prefix_and_full_id_resolve_identically():
    a = run_scenario("06", catalog=_CATALOG)
    b = run_scenario("06_covert_entry_breach", catalog=_CATALOG)
    assert a.level == b.level and a.action == b.action


def test_unknown_scenario_raises():
    with pytest.raises(KeyError):
        run_scenario("99", catalog=_CATALOG)
