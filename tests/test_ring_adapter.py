"""Tests for the Ring perimeter adapter (src/adapters/ring_adapter.py).

Exercises the REAL Ring-API-shaped logic (HMAC webhook verification, WHEP URL
construction, event parsing) and the honest simulated fallback, and proves the
adapter plugs into the shared pipeline as an IngestAdapter (no orphan).
"""

from __future__ import annotations

import hashlib
import hmac

from src.adapters.ring_adapter import RingAdapter, RingEvent
from src.pipeline.ingest import IngestAdapter, VigilPipeline


def test_is_ingest_adapter():
    assert isinstance(RingAdapter(), IngestAdapter)


def test_no_token_is_not_live_capable():
    a = RingAdapter(bearer_token=None, webhook_secret=None)
    assert a.is_live_capable is False


def test_with_token_is_live_capable():
    a = RingAdapter(bearer_token="tok_abc")
    assert a.is_live_capable is True


def test_whep_url_is_real_shape():
    a = RingAdapter(bearer_token="tok", api_base="https://api.example.com/v1")
    url = a.whep_session_url("dev123")
    assert url == "https://api.example.com/v1/devices/dev123/media/streaming/whep/sessions"


def test_webhook_hmac_verification_roundtrip():
    secret = "shhh"
    a = RingAdapter(webhook_secret=secret)
    body = b'{"kind":"motion","classification":"human"}'
    good = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert a.verify_webhook(body, good) is True
    assert a.verify_webhook(body, "deadbeef") is False


def test_webhook_unverifiable_without_secret():
    a = RingAdapter(webhook_secret=None)
    assert a.verify_webhook(b"x", "anything") is False  # cannot verify -> untrusted


def test_parse_event_normalizes_payload():
    a = RingAdapter()
    ev = a.parse_event(
        {
            "device_id": "d1",
            "kind": "ding",
            "classification": "human",
            "acoustic_db": 42.0,
        },
        simulated=False,
    )
    assert isinstance(ev, RingEvent)
    assert ev.device_id == "d1" and ev.kind == "ding"
    assert ev.classification == "human" and ev.acoustic_db == 42.0


# --- SEC.4: verified_signature derives from the HMAC check, NOT the payload --- #


def test_parse_event_ignores_self_claimed_verified_flag():
    """An attacker-set 'verified_signature: true' in the body must NOT be trusted."""
    a = RingAdapter(webhook_secret="shhh")
    ev = a.parse_event(
        {"kind": "motion", "verified_signature": True},  # forged flag
        simulated=False,
    )  # no raw_body/signature supplied -> cannot verify -> must be False
    assert ev.verified_signature is False


def test_parse_event_verifies_from_real_hmac():
    secret = "shhh"
    a = RingAdapter(webhook_secret=secret)
    body = b'{"kind":"motion","classification":"human"}'
    good = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    import json as _json

    ev_ok = a.parse_event(_json.loads(body), simulated=False, raw_body=body, signature=good)
    assert ev_ok.verified_signature is True

    ev_bad = a.parse_event(_json.loads(body), simulated=False, raw_body=body, signature="deadbeef")
    assert ev_bad.verified_signature is False


def test_simulated_telemetry_is_flagged():
    telem = RingAdapter(bearer_token=None).telemetry()
    assert telem.simulated is True
    assert telem.source.endswith(":sim")
    assert "ring:" in telem.scenario_id


def test_adapter_drives_pipeline():
    """No-orphan proof: the Ring adapter feeds the real pipeline end to end."""
    result = VigilPipeline(RingAdapter(bearer_token=None)).process()
    # A quiet simulated motion event resolves safely (no dispatch).
    assert result.cad_staged is False
    assert result.level.value in {"L0_SAFE", "L1_AMBIGUOUS"}
