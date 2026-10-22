"""Phase 3 — emergency CAD dispatcher tests (tasks.md Task 3.3).

Validates the NENA/RapidSOS manifest schema, SHA-256 hash reproducibility, the
10-second safe-cancellation buffer, and 4-digit PIN disarm logic. The buffer is
clock-injected so no test sleeps.
"""

from __future__ import annotations

from src.core.cad_dispatcher import (
    CANCEL_BUFFER_SECONDS,
    CadStaging,
    build_cad_packet,
    stage_cad_dispatch,
    verify_disarm_pin,
)
from src.core.types import CadPacket


# --------------------------------------------------------------------------- #
# Packet schema + SHA-256.
# --------------------------------------------------------------------------- #
def test_packet_is_rapidsos_and_staged():
    pkt = build_cad_packet("INC-1", threat_summary="breach", created_at=1000.0)
    assert isinstance(pkt, CadPacket)
    assert pkt.nena_format == "RapidSOS"
    assert pkt.staged is True
    assert len(pkt.sha256) == 64
    assert all(c in "0123456789abcdef" for c in pkt.sha256)


def test_sha256_is_reproducible_for_same_inputs():
    a = build_cad_packet("INC-2", threat_summary="x", created_at=42.0, evidence_timeline=["e1"])
    b = build_cad_packet("INC-2", threat_summary="x", created_at=42.0, evidence_timeline=["e1"])
    assert a.sha256 == b.sha256  # deterministic over canonical JSON


def test_sha256_changes_with_content():
    a = build_cad_packet("INC-3", threat_summary="x", created_at=42.0)
    b = build_cad_packet("INC-3", threat_summary="y", created_at=42.0)
    assert a.sha256 != b.sha256


def test_incident_id_required():
    import pytest

    with pytest.raises(ValueError):
        build_cad_packet("")


# --------------------------------------------------------------------------- #
# PIN verification.
# --------------------------------------------------------------------------- #
def test_valid_four_digit_pin_format():
    assert verify_disarm_pin("0421") is True


def test_invalid_pin_formats_rejected():
    assert verify_disarm_pin("123") is False       # too short
    assert verify_disarm_pin("12345") is False      # too long
    assert verify_disarm_pin("12a4") is False        # non-digit
    assert verify_disarm_pin("") is False


def test_pin_must_match_expected_when_supplied():
    assert verify_disarm_pin("0421", expected_pin="0421") is True
    assert verify_disarm_pin("0000", expected_pin="0421") is False


# --------------------------------------------------------------------------- #
# 10-second safe-cancellation buffer.
# --------------------------------------------------------------------------- #
def test_buffer_default_is_ten_seconds():
    assert CANCEL_BUFFER_SECONDS == 10.0


def test_staging_counts_down_and_becomes_ready():
    s = stage_cad_dispatch("INC-10", staged_at=1000.0)
    assert s.remaining(now=1000.0) == 10.0
    assert s.is_cancellable(now=1003.0) is True
    assert s.remaining(now=1003.0) == 7.0
    assert s.is_ready(now=1003.0) is False
    # After the buffer elapses, it is ready and no longer cancellable.
    assert s.is_ready(now=1010.0) is True
    assert s.is_cancellable(now=1010.0) is False


def test_cancel_within_buffer_with_valid_pin():
    s = stage_cad_dispatch("INC-11", staged_at=0.0)
    assert s.cancel("0421", now=5.0) is True
    assert s.cancelled is True
    assert s.is_ready(now=20.0) is False  # cancelled never becomes ready


def test_cancel_rejected_with_bad_pin():
    s = stage_cad_dispatch("INC-12", staged_at=0.0)
    assert s.cancel("12", now=5.0) is False
    assert s.cancelled is False


def test_cancel_rejected_after_buffer_closes():
    s = stage_cad_dispatch("INC-13", staged_at=0.0)
    # Buffer closed at t=10; a valid PIN at t=11 is too late.
    assert s.cancel("0421", now=11.0) is False
    assert s.cancelled is False
    assert s.is_ready(now=11.0) is True


def test_cancel_honors_expected_pin():
    s = stage_cad_dispatch("INC-14", staged_at=0.0)
    assert s.cancel("0000", now=2.0, expected_pin="0421") is False
    assert s.cancelled is False
    assert s.cancel("0421", now=3.0, expected_pin="0421") is True
    assert s.cancelled is True


def test_staging_packet_hash_matches_standalone_build():
    s = stage_cad_dispatch("INC-15", staged_at=500.0, threat_summary="z")
    direct = build_cad_packet("INC-15", created_at=500.0, threat_summary="z")
    assert s.packet.sha256 == direct.sha256
