"""Tests for breathing-like rate estimation."""

from wificsi.io.simulator import generate_synthetic_csi
from wificsi.processing.breathing import estimate_breathing_rate


def test_breathing_estimate_tracks_synthetic_rate() -> None:
    data = generate_synthetic_csi(
        seconds=60,
        rate_hz=50,
        motion_hz=0.05,
        breathing_hz=0.25,
        noise_std=0.01,
        seed=3,
    )

    result = estimate_breathing_rate(data, min_hz=0.1, max_hz=0.6)

    assert abs(result.frequency_hz - 0.25) < 0.05
    assert 12.0 <= result.breaths_per_minute <= 18.0

