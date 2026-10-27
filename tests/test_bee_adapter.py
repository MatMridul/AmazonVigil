"""Tests for the Bee wearable adapter (src/adapters/bee_adapter.py).

Bee is MODELED (no device/real data; Vigil does not claim the Bee track). These
tests verify the real-CLI-shaped sleep inference, the honest MODELED fallback
flagging, bio-context mapping, and pipeline wiring. VIGIL_FORCE_BEE_MODELED=1
makes the fallback deterministic even if a 'bee' binary is on PATH.
"""

from __future__ import annotations

import pytest

from src.adapters.bee_adapter import BeeAdapter, BeeReading
from src.core.types import HostState, WearerBioContext
from src.pipeline.ingest import IngestAdapter, VigilPipeline


@pytest.fixture(autouse=True)
def force_modeled(monkeypatch):
    monkeypatch.setenv("VIGIL_FORCE_BEE_MODELED", "1")


def test_is_ingest_adapter():
    assert isinstance(BeeAdapter(), IngestAdapter)


def test_forced_modeled_is_not_cli_available():
    assert BeeAdapter().cli_available is False


@pytest.mark.parametrize(
    "mins,expected", [(None, False), (0, False), (59, False), (60, True), (180, True)]
)
def test_sleep_inference_threshold(mins, expected):
    # UX-04: >=60 min conversational silence implies asleep.
    assert BeeAdapter.infer_sleep(mins) is expected


def test_modeled_reading_is_flagged():
    reading = BeeAdapter().read_bio()
    assert isinstance(reading, BeeReading)
    assert reading.modeled is True
    assert reading.is_asleep is True  # off-wrist fail-safe default


def test_bio_context_mapping():
    a = BeeAdapter()
    ctx = a.to_bio_context(a.read_bio())
    assert isinstance(ctx, WearerBioContext)
    assert ctx.host_state is HostState.ASLEEP
    assert ctx.device_tier == "bee_pioneer"


def test_telemetry_is_modeled_and_sources_bee():
    telem = BeeAdapter().telemetry()
    assert telem.simulated is True
    assert telem.source == "modeled:bee"
    assert "MODELED" in telem.title


def test_adapter_drives_pipeline():
    """No-orphan proof: Bee bio-state drives the pipeline (contributes context)."""
    result = VigilPipeline(BeeAdapter()).process()
    # Bio-state alone (quiet perimeter) resolves safe — no dispatch.
    assert result.cad_staged is False
    assert result.level.value == "L0_SAFE"
