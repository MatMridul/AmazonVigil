"""Tests for the Optical Integrity Auditor & preprocessor (Task 1.6)."""

import io

import pytest
from PIL import Image

from src.core.integrity_auditor import (
    AudioDuplexMuteGate,
    compute_optical_integrity,
    preprocess_frame,
)


# --------------------------------------------------------------------------- #
# Φ_V computation
# --------------------------------------------------------------------------- #
def test_clean_frame_high_integrity(clean_frame_bytes):
    report = compute_optical_integrity(clean_frame_bytes)
    assert report.phi_v == pytest.approx(1.0)
    assert report.tampered is False
    assert report.reason == "nominal"


def test_spraypaint_frame_collapses_phi_v(spraypaint_frame_bytes):
    report = compute_optical_integrity(spraypaint_frame_bytes)
    assert report.phi_v == 0.0
    assert report.tampered is True
    assert report.reason == "luminance_variance_collapse"


def test_laser_saturation_collapses_phi_v(laser_frame_bytes):
    report = compute_optical_integrity(laser_frame_bytes)
    assert report.phi_v == 0.0
    assert report.tampered is True
    assert report.reason == "laser_or_ir_saturation"


def test_empty_bytes_rejected():
    with pytest.raises(ValueError):
        compute_optical_integrity(b"")


# --------------------------------------------------------------------------- #
# preprocess_frame — DR-02 (max-fit, downscale-only, WebP q80)
# --------------------------------------------------------------------------- #
def test_resize_bounds_and_webp(clean_frame_bytes):
    out = preprocess_frame(clean_frame_bytes)
    with Image.open(io.BytesIO(out)) as img:
        assert img.format == "WEBP"
        w, h = img.size
    assert w <= 1024 and h <= 576


def test_resize_preserves_aspect_ratio(clean_frame_bytes):
    # Source is 2048x1152 (16:9 == 1.7778).
    out = preprocess_frame(clean_frame_bytes)
    with Image.open(io.BytesIO(out)) as img:
        w, h = img.size
    assert abs((w / h) - (2048 / 1152)) <= 0.0178  # ±1%


def test_small_frame_not_upscaled(small_frame_bytes):
    out = preprocess_frame(small_frame_bytes)
    with Image.open(io.BytesIO(out)) as img:
        assert img.size == (640, 360)  # unchanged — downscale only
        assert img.format == "WEBP"


def test_preprocess_empty_rejected():
    with pytest.raises(ValueError):
        preprocess_frame(b"")


# --------------------------------------------------------------------------- #
# Audio Duplex Mute gate
# --------------------------------------------------------------------------- #
def test_duplex_mute_gates_phi_a():
    t = {"now": 1000.0}
    gate = AudioDuplexMuteGate(clock=lambda: t["now"])
    gate.begin_playback(duration_ms=1000)  # muted for 1000 + 500 ms
    assert gate.is_muted() is True
    assert gate.gate_phi_a(1.0) == 0.0

    t["now"] = 1000.0 + 1.4  # before the 1.5s window closes
    assert gate.is_muted() is True

    t["now"] = 1000.0 + 1.6  # after window
    assert gate.is_muted() is False
    assert gate.gate_phi_a(1.0) == 1.0


def test_duplex_negative_duration_rejected():
    gate = AudioDuplexMuteGate()
    with pytest.raises(ValueError):
        gate.begin_playback(duration_ms=-1)
