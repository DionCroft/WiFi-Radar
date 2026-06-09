"""Tests for the core CSI data model."""

import numpy as np

from wificsi.core import CSIData, ensure_complex_matrix


def test_csidata_promotes_2d_csi_to_4d() -> None:
    csi = np.ones((10, 4), dtype=complex)
    timestamps = np.arange(10, dtype=float) * 0.01

    data = CSIData(csi=csi, timestamps=timestamps, source="test")

    assert data.csi.shape == (10, 4, 1, 1)
    assert data.packet_count == 10
    assert data.subcarrier_count == 4
    assert data.sample_rate_hz == 100.0


def test_interleaved_real_imag_conversion() -> None:
    values = np.array([[1.0, 2.0, 3.0, 4.0]])

    complex_values = ensure_complex_matrix(values)

    assert complex_values.shape == (1, 2)
    assert complex_values[0, 0] == 1.0 + 2.0j
    assert complex_values[0, 1] == 3.0 + 4.0j

