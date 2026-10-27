"""Shared pytest fixtures: synthetic camera frames for optical tests."""

import io

import numpy as np
import pytest
from PIL import Image


def _encode(arr: np.ndarray, fmt: str = "PNG") -> bytes:
    out = io.BytesIO()
    Image.fromarray(arr.astype("uint8"), "RGB").save(out, format=fmt)
    return out.getvalue()


@pytest.fixture
def clean_frame_bytes() -> bytes:
    """A high-variance textured 16:9 frame (nominal optical integrity)."""
    rng = np.random.default_rng(42)
    arr = rng.integers(0, 256, size=(1152, 2048, 3), dtype=np.uint8)
    return _encode(arr)


@pytest.fixture
def spraypaint_frame_bytes() -> bytes:
    """A near-black uniform frame (spray paint / tape → Φ_V = 0)."""
    arr = np.full((1152, 2048, 3), 3, dtype=np.uint8)
    return _encode(arr)


@pytest.fixture
def laser_frame_bytes() -> bytes:
    """A fully saturated white frame (laser / IR wash → Φ_V = 0)."""
    arr = np.full((1152, 2048, 3), 255, dtype=np.uint8)
    return _encode(arr)


@pytest.fixture
def small_frame_bytes() -> bytes:
    """A sub-target 640x360 16:9 frame (must NOT be upscaled)."""
    rng = np.random.default_rng(7)
    arr = rng.integers(0, 256, size=(360, 640, 3), dtype=np.uint8)
    return _encode(arr)
