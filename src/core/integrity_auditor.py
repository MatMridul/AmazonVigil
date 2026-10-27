"""Optical Integrity Auditor & Image Preprocessor (Task 1.3).

Computes the optical integrity factor Φ_V from luminance variance (spray paint /
tape blinding) and saturation clipping (laser / IR wash), and proportionally
downscales frames to a max 1024x576 WebP box (DR-02, downscale-only, quality 80).

Also implements the Audio Duplex Mute gate (SPEC.md §7 #6): outbound deterrent
audio playback suppresses inbound acoustic evidence (Φ_A) for the playback
duration + 500 ms to prevent the Ring mic/speaker feedback loop.
"""

from __future__ import annotations

import io
import time
from dataclasses import dataclass

import numpy as np
from PIL import Image

# DR-02: max-fit box, downscale-only, WebP quality 80.
MAX_WIDTH = 1024
MAX_HEIGHT = 576
WEBP_QUALITY = 80

# Audio Duplex Mute dampening tail (SPEC.md §7 #6).
DUPLEX_DAMPEN_MS = 500

# Tamper thresholds (SPEC.md §4 A1/A2; docs calibration).
#  - Spray paint / tape: luminance variance collapses toward 0.
#  - Laser / IR wash:     >95% of pixels clipped near max (255).
LUMINANCE_VARIANCE_FLOOR = 25.0  # below this → blinded (Φ_V → 0)
LUMINANCE_VARIANCE_NOMINAL = 400.0  # at/above this → full optical confidence
SATURATION_CLIP_THRESHOLD = 250  # per-channel value counted as "clipped"
SATURATION_CLIP_FRACTION = 0.95  # >95% clipped → laser wash (Φ_V → 0)


# --------------------------------------------------------------------------- #
# Optical integrity
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class OpticalReport:
    """Diagnostic breakdown of an optical integrity evaluation."""

    phi_v: float
    luminance_variance: float
    saturation_fraction: float
    tampered: bool
    reason: str


def _to_luminance(arr: np.ndarray) -> np.ndarray:
    """Convert an HxWx{1,3,4} uint8 array to a 2D luminance array (Rec. 601)."""
    if arr.ndim == 2:
        return arr.astype(np.float64)
    channels = arr.shape[2]
    if channels == 1:
        return arr[:, :, 0].astype(np.float64)
    rgb = arr[:, :, :3].astype(np.float64)
    return 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]


def compute_optical_integrity(image_bytes: bytes) -> OpticalReport:
    """Compute Φ_V ∈ [0,1] from a raw frame buffer.

    Two independent tamper detectors, worst case wins:
      * luminance-variance collapse → spray paint / tape / total blinding (A1)
      * saturation clipping          → high-beam laser / IR wash (A2)
    """
    if not image_bytes:
        raise ValueError("image_bytes must be non-empty")

    with Image.open(io.BytesIO(image_bytes)) as img:
        arr = np.asarray(img.convert("RGB"))

    lum = _to_luminance(arr)
    variance = float(np.var(lum))

    clipped = np.all(arr[:, :, :3] >= SATURATION_CLIP_THRESHOLD, axis=2)
    saturation_fraction = float(np.mean(clipped))

    # Laser / IR wash: overwhelming clipped-white fraction.
    if saturation_fraction > SATURATION_CLIP_FRACTION:
        return OpticalReport(
            phi_v=0.0,
            luminance_variance=variance,
            saturation_fraction=saturation_fraction,
            tampered=True,
            reason="laser_or_ir_saturation",
        )

    # Spray paint / tape: variance collapse (near-uniform dark frame).
    if variance <= LUMINANCE_VARIANCE_FLOOR:
        return OpticalReport(
            phi_v=0.0,
            luminance_variance=variance,
            saturation_fraction=saturation_fraction,
            tampered=True,
            reason="luminance_variance_collapse",
        )

    # Nominal range: linear confidence between floor and nominal variance.
    if variance >= LUMINANCE_VARIANCE_NOMINAL:
        phi_v = 1.0
    else:
        span = LUMINANCE_VARIANCE_NOMINAL - LUMINANCE_VARIANCE_FLOOR
        phi_v = round((variance - LUMINANCE_VARIANCE_FLOOR) / span, 4)
        phi_v = max(0.0, min(1.0, phi_v))

    return OpticalReport(
        phi_v=phi_v,
        luminance_variance=variance,
        saturation_fraction=saturation_fraction,
        tampered=False,
        reason="nominal",
    )


# --------------------------------------------------------------------------- #
# Frame preprocessing (DR-02)
# --------------------------------------------------------------------------- #
def preprocess_frame(image_bytes: bytes) -> bytes:
    """Downscale-only max-fit resize to <= 1024x576, output WebP (quality 80).

    Preserves aspect ratio; never upscales a smaller source (DR-02). Uses bicubic
    resampling.
    """
    if not image_bytes:
        raise ValueError("image_bytes must be non-empty")

    with Image.open(io.BytesIO(image_bytes)) as src:
        img = src.convert("RGB")
        width, height = img.size

        scale = min(MAX_WIDTH / width, MAX_HEIGHT / height, 1.0)  # <=1 → downscale only
        if scale < 1.0:
            new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
            img = img.resize(new_size, Image.Resampling.BICUBIC)

        out = io.BytesIO()
        img.save(out, format="WEBP", quality=WEBP_QUALITY, method=4)
        return out.getvalue()


# --------------------------------------------------------------------------- #
# Audio Duplex Mute gate (SPEC.md §7 #6)
# --------------------------------------------------------------------------- #
class AudioDuplexMuteGate:
    """Suppresses inbound acoustic evidence during outbound deterrent playback.

    When the Ring speaker plays a bluff ("Hold on, coming to the door!"), the
    co-located mic (1.5 in away) would otherwise loop that audio back and
    false-trigger a breach escalation. This gate locks Φ_A for the playback
    duration plus a 500 ms dampening tail.
    """

    def __init__(self, *, clock=time.monotonic) -> None:
        self._clock = clock
        self._mute_until: float = 0.0

    def begin_playback(self, duration_ms: float) -> float:
        """Mark deterrent audio as playing for ``duration_ms``; returns mute-until."""
        if duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        self._mute_until = self._clock() + (duration_ms + DUPLEX_DAMPEN_MS) / 1000.0
        return self._mute_until

    def is_muted(self) -> bool:
        """True while inbound acoustic intake is suppressed."""
        return self._clock() < self._mute_until

    def gate_phi_a(self, phi_a: float) -> float:
        """Return 0.0 while muted (acoustic evidence untrustworthy), else passthrough."""
        return 0.0 if self.is_muted() else phi_a
