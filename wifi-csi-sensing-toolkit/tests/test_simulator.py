"""Tests for synthetic CSI generation."""

import numpy as np

from wificsi.io.simulator import generate_synthetic_csi


def test_synthetic_csi_shape_and_metadata() -> None:
    data = generate_synthetic_csi(seconds=2, rate_hz=50, subcarriers=16, seed=1)

    assert data.csi.shape == (100, 16, 1, 1)
    assert data.timestamps.shape == (100,)
    assert data.source == "synthetic"
    assert data.metadata["breathing_hz"] == 0.25
    assert np.iscomplexobj(data.csi)

