"""Tests for the shared ingest seam (src/pipeline/ingest.py).

Proves the seam is WIRED to the real pipeline — not an orphan abstraction:
the demo adapter driven through VigilPipeline must produce the identical result
the Phase 8 runner produces for every baseline scenario, and the live adapter's
no-device fallback must be honestly flagged simulated.
"""

from __future__ import annotations

import pytest

from src.core.state_machine import GuardMode
from src.pipeline.ingest import (
    DemoAdapter,
    IngestAdapter,
    LiveAdapter,
    Telemetry,
    VigilPipeline,
)
from src.simulator.scenario_runner import load_scenarios, run_scenario


@pytest.fixture
def catalog():
    return load_scenarios()


def test_demo_adapter_lists_all_ten_baselines():
    adapter = DemoAdapter()
    ids = adapter.scenario_ids()
    assert len(ids) == 10
    assert ids[0].startswith("01_")


def test_demo_adapter_telemetry_is_flagged_simulated():
    telem = DemoAdapter().telemetry("06")
    assert isinstance(telem, Telemetry)
    assert telem.simulated is True
    assert telem.source == "demo"
    assert telem.scenario_id == "06_covert_entry_breach"


@pytest.mark.parametrize("scenario_id", list(load_scenarios().keys()))
def test_pipeline_demo_path_matches_phase8_runner(scenario_id):
    """The seam must not drift from the canonical runner for ANY scenario."""
    pipeline = VigilPipeline(DemoAdapter())
    via_seam = pipeline.process(scenario_id)
    canonical = run_scenario(scenario_id)
    assert via_seam.level == canonical.level
    assert via_seam.action == canonical.action
    assert via_seam.permitted_actuators == canonical.permitted_actuators
    assert via_seam.cad_staged == canonical.cad_staged
    assert via_seam.cad_sha256 == canonical.cad_sha256


def test_pipeline_demo_prefix_selector():
    pipeline = VigilPipeline(DemoAdapter())
    assert pipeline.process("10").scenario_id == "10_host_duress_armed_coercion"


def test_live_adapter_is_importable_and_constructs():
    adapter = LiveAdapter()
    assert isinstance(adapter, IngestAdapter)
    assert adapter.source_name == "live"


def test_live_adapter_fallback_is_honestly_simulated():
    """No device wired → simulated baseline, never a fabricated live event."""
    telem = LiveAdapter().telemetry()
    assert telem.simulated is True
    assert "unwired" in telem.source
    assert telem.mode is GuardMode.NIGHT_SENTRY
    assert telem.score == 0.0


def test_live_adapter_baseline_resolves_to_safe():
    """The honest live baseline is a quiet perimeter — L0, no dispatch."""
    result = VigilPipeline(LiveAdapter()).process()
    assert result.cad_staged is False
    assert result.permitted_actuators == () or result.action.value in {
        "SILENT_PASS",
        "NOTIFY_HOST",
    }
