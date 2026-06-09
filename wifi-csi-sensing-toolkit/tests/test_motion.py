"""Tests for motion scoring."""

from wificsi.io.simulator import generate_synthetic_csi
from wificsi.processing.motion import motion_score


def test_motion_score_returns_detection_result() -> None:
    data = generate_synthetic_csi(seconds=5, rate_hz=50, seed=2)

    result = motion_score(data)

    assert result.score.shape == data.timestamps.shape
    assert result.threshold >= 0.0
    assert isinstance(result.occupied, bool)

