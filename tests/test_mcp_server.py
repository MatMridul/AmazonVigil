"""Tests for the FastMCP server tools + idempotency, and the end-to-end
threat pipeline (Task 1.6: test_mcp_server + test_threat_pipeline merged)."""

import io

import numpy as np
import pytest
from PIL import Image

from src.adapters.bedrock_analyzer import BedrockThreatEvaluator
from src.core.integrity_auditor import compute_optical_integrity, preprocess_frame
from src.core.types import HostState, IntegrityVector, ThreatLevel, WearerBioContext
from src.server import (
    IdempotencyCache,
    audit_perimeter_event,
    disarm_perimeter_alert,
    explain_incident_reasoning,
    format_emergency_cad_packet,
    query_wearer_state,
    set_mesh_guard_profile,
    trigger_firetv_deterrence,
    trigger_tactical_wake,
)

pytestmark = pytest.mark.asyncio


def _frame(value: int, size=(1152, 2048)) -> bytes:
    if value < 0:
        arr = np.random.default_rng(1).integers(0, 256, size=(*size, 3), dtype=np.uint8)
    else:
        arr = np.full((*size, 3), value, dtype=np.uint8)
    out = io.BytesIO()
    Image.fromarray(arr, "RGB").save(out, format="PNG")
    return out.getvalue()


# --------------------------------------------------------------------------- #
# Idempotency cache
# --------------------------------------------------------------------------- #
async def test_idempotency_cache_locks_duplicate():
    t = {"now": 0.0}
    cache = IdempotencyCache(ttl=15.0, clock=lambda: t["now"])
    assert cache.check_and_set("tok-1") is True
    assert cache.check_and_set("tok-1") is False  # duplicate within TTL
    t["now"] = 16.0
    assert cache.check_and_set("tok-1") is True  # expired → fresh again


async def test_empty_token_never_deduped():
    cache = IdempotencyCache()
    assert cache.check_and_set("") is True
    assert cache.check_and_set("") is True


# --------------------------------------------------------------------------- #
# The 8 tools
# --------------------------------------------------------------------------- #
async def test_audit_perimeter_event_clean():
    out = await audit_perimeter_event(
        {"camera_id": "cam-1", "pir_motion": True, "acoustic_db": 30.0, "image_bytes": _frame(-1)}
    )
    assert out["optical_tampered"] is False
    assert out["integrity_vector"]["phi_v"] == pytest.approx(1.0)


async def test_audit_perimeter_event_tampered():
    out = await audit_perimeter_event(
        {"camera_id": "cam-1", "pir_motion": True, "image_bytes": _frame(3)}
    )
    assert out["optical_tampered"] is True
    assert out["integrity_vector"]["phi_v"] == 0.0


async def test_query_wearer_state():
    out = await query_wearer_state("maya")
    assert out["user_id"] == "maya"
    assert "is_awake" in out and "on_wrist" in out


async def test_query_wearer_state_requires_id():
    with pytest.raises(ValueError):
        await query_wearer_state("")


async def test_tactical_wake_idempotent():
    first = await trigger_tactical_wake("maya", "echo_whisper", "wake-tok")
    second = await trigger_tactical_wake("maya", "echo_whisper", "wake-tok")
    assert first["status"] == "wake_triggered"
    assert second["status"] == "duplicate_suppressed"


async def test_firetv_validates_mode():
    with pytest.raises(ValueError):
        await trigger_firetv_deterrence("laser_show", 50)


async def test_firetv_validates_volume():
    with pytest.raises(ValueError):
        await trigger_firetv_deterrence("dog_bark", 150)


async def test_firetv_launch_ok():
    out = await trigger_firetv_deterrence("dog_bark", 80, "ftv-tok")
    assert out["status"] == "deterrence_launched"
    assert out["boot_bridge_ms"] == 150


async def test_cad_packet_has_valid_sha256():
    out = await format_emergency_cad_packet("INC-100")
    assert len(out["sha256"]) == 64
    assert out["staged"] is True


async def test_disarm_valid_pin():
    # SEC.2: disarm now verifies the PIN VALUE against the server's configured
    # hash, not just the format. Point the server verifier at a known PIN.
    import src.server as server
    from src.mcp_auth import PinVerifier, hash_pin

    server._pin_verifier = PinVerifier(pin_hash=hash_pin("8391"))
    await format_emergency_cad_packet("INC-200")
    out = await disarm_perimeter_alert("INC-200", "8391")
    assert out["status"] == "disarmed"


async def test_disarm_rejects_wrong_value_even_with_valid_format():
    # The core SEC.2 improvement: a well-formed but WRONG pin must not disarm.
    import src.server as server
    from src.mcp_auth import PinVerifier, hash_pin

    server._pin_verifier = PinVerifier(pin_hash=hash_pin("8391"))
    out = await disarm_perimeter_alert("INC-202", "1234")
    assert out["status"] == "rejected"
    assert out["reason"] == "invalid_pin"


async def test_disarm_rejects_bad_pin():
    import src.server as server
    from src.mcp_auth import PinVerifier, hash_pin

    server._pin_verifier = PinVerifier(pin_hash=hash_pin("8391"))
    out = await disarm_perimeter_alert("INC-201", "12")
    assert out["status"] == "rejected"


async def test_explain_known_and_unknown():
    await format_emergency_cad_packet("INC-300")
    known = await explain_incident_reasoning("INC-300")
    assert known["cad_staged"] is True
    unknown = await explain_incident_reasoning("INC-NOPE")
    assert unknown["status"] == "unknown_incident"


async def test_set_mesh_guard_profile():
    out = await set_mesh_guard_profile("night_sentry", 8)
    assert out["status"] == "profile_set"
    with pytest.raises(ValueError):
        await set_mesh_guard_profile("invalid_mode")


# --------------------------------------------------------------------------- #
# End-to-end pipeline: ingest → preprocess → Φ → classify
# --------------------------------------------------------------------------- #
async def test_pipeline_tampered_frame_escalates():
    raw = _frame(3)  # spray-painted
    report = compute_optical_integrity(raw)
    assert report.phi_v == 0.0

    integrity = IntegrityVector(phi_m=1.0, phi_v=report.phi_v, phi_a=1.0, phi_net=1.0)
    ev = BedrockThreatEvaluator(mock=True)
    assessment = ev.evaluate(
        frame_webp=preprocess_frame(raw),
        audio_transcript="scraping at the lock",
        acoustic_db=55.0,
        bio=WearerBioContext(user_id="maya", host_state=HostState.ASLEEP, is_asleep=True),
        integrity=integrity,
    )
    assert assessment.threat_level in (ThreatLevel.L2_SUSPICIOUS, ThreatLevel.L3_CRITICAL)


async def test_pipeline_clean_family_arrival_safe():
    raw = _frame(-1)  # textured, clean
    report = compute_optical_integrity(raw)
    integrity = IntegrityVector(phi_m=1.0, phi_v=report.phi_v, phi_a=1.0, phi_net=1.0)
    ev = BedrockThreatEvaluator(mock=True)
    assessment = ev.evaluate(
        frame_webp=preprocess_frame(raw),
        audio_transcript="",
        acoustic_db=15.0,
        bio=WearerBioContext(user_id="maya", host_state=HostState.ASLEEP, is_asleep=True),
        integrity=integrity,
    )
    assert assessment.threat_level == ThreatLevel.L0_SAFE
