"""Tests for the Bedrock multimodal threat evaluator (Task 1.6)."""

import pytest

from src.adapters.bedrock_analyzer import BedrockThreatEvaluator
from src.core.types import (
    HostState,
    IntegrityVector,
    ThreatAssessment,
    ThreatLevel,
    WearerBioContext,
)

NOMINAL = IntegrityVector(phi_m=1.0, phi_v=1.0, phi_a=1.0, phi_net=1.0)
TAMPERED = IntegrityVector(phi_m=1.0, phi_v=0.0, phi_a=1.0, phi_net=1.0)


def _bio(state=HostState.ASLEEP) -> WearerBioContext:
    return WearerBioContext(user_id="maya", host_state=state, is_asleep=True)


def test_mock_mode_default():
    ev = BedrockThreatEvaluator()
    assert ev.mock is True  # VIGIL_MODE defaults to simulation


def test_quiet_benign_is_safe():
    ev = BedrockThreatEvaluator(mock=True)
    out = ev.evaluate(
        frame_webp=None,
        audio_transcript="",
        acoustic_db=20.0,
        bio=_bio(),
        integrity=NOMINAL,
    )
    assert isinstance(out, ThreatAssessment)
    assert out.threat_level == ThreatLevel.L0_SAFE


def test_optical_tamper_escalates():
    ev = BedrockThreatEvaluator(mock=True)
    out = ev.evaluate(
        frame_webp=None,
        audio_transcript="",
        acoustic_db=20.0,
        bio=_bio(),
        integrity=TAMPERED,
    )
    assert out.threat_level in (ThreatLevel.L2_SUSPICIOUS, ThreatLevel.L3_CRITICAL)
    assert "optical_tamper_phi_v_zero" in out.visual_findings


def test_hostile_speech_is_critical():
    ev = BedrockThreatEvaluator(mock=True)
    out = ev.evaluate(
        frame_webp=None,
        audio_transcript="I have a weapon, open up",
        acoustic_db=70.0,
        bio=_bio(),
        integrity=NOMINAL,
    )
    assert out.threat_level == ThreatLevel.L3_CRITICAL


def test_breach_noise_is_suspicious():
    ev = BedrockThreatEvaluator(mock=True)
    out = ev.evaluate(
        frame_webp=None,
        audio_transcript="metal scraping and prying at the lock",
        acoustic_db=60.0,
        bio=_bio(),
        integrity=NOMINAL,
    )
    assert out.threat_level == ThreatLevel.L2_SUSPICIOUS


def test_parse_assessment_repairs_json_fence():
    ev = BedrockThreatEvaluator(mock=True)
    raw = (
        "Here is the result:\n```json\n"
        '{"threat_level":"L1_AMBIGUOUS","threat_score":0.3,'
        '"detected_subject":"BENIGN_STRANGER","recommended_mesh_action":"NOTIFY_HOST",'
        '"justification":"visitor at door"}\n```'
    )
    out = ev._parse_assessment(raw)
    assert out.threat_level == ThreatLevel.L1_AMBIGUOUS
    assert out.threat_score == pytest.approx(0.3)


def test_parse_assessment_accepts_alias():
    ev = BedrockThreatEvaluator(mock=True)
    raw = (
        '{"threat_level":"L3_CRITICAL_DISPATCH","threat_score":0.95,'
        '"detected_subject":"HOSTILE_INTRUDER","recommended_mesh_action":"DISPATCH_EMERGENCY",'
        '"justification":"forced entry"}'
    )
    out = ev._parse_assessment(raw)
    assert out.threat_level == ThreatLevel.L3_CRITICAL  # alias resolved (DR-03)


def test_build_prompt_includes_image_when_present():
    ev = BedrockThreatEvaluator(mock=True)
    prompt = ev.build_prompt(
        frame_webp=b"fakewebp",
        audio_transcript="hi",
        acoustic_db=30.0,
        bio=_bio(),
        integrity=NOMINAL,
    )
    kinds = [block["type"] for block in prompt["messages"][0]["content"]]
    assert "image" in kinds and "text" in kinds
