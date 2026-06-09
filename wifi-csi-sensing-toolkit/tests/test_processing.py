"""Tests for calibration and processing helpers."""

import numpy as np

from wificsi.core import CSIData
from wificsi.processing.calibration import (
    amplitude,
    remove_invalid_packets,
    remove_static_mean,
    unwrap_phase_over_time,
)
from wificsi.processing.features import pca_motion_component
from wificsi.processing.filtering import hampel_filter_time, median_filter_time
from wificsi.processing.spectrogram import stft_spectrogram


def test_remove_invalid_packets_drops_nan_rows() -> None:
    csi = np.ones((4, 3), dtype=complex)
    csi[2, 1] = np.nan + 0j
    data = CSIData(csi=csi, timestamps=np.arange(4, dtype=float))

    cleaned = remove_invalid_packets(data)

    assert cleaned.packet_count == 3


def test_processing_shapes() -> None:
    data = CSIData(
        csi=np.exp(1j * np.linspace(0, 4 * np.pi, 60)).reshape(20, 3),
        timestamps=np.arange(20, dtype=float) * 0.05,
    )

    assert amplitude(data).shape == data.csi.shape
    assert unwrap_phase_over_time(data).shape == data.csi.shape
    assert remove_static_mean(data).shape == data.csi.shape
    assert pca_motion_component(data).shape == (20,)


def test_filters_and_spectrogram() -> None:
    signal = np.zeros(100)
    signal[50] = 10.0

    medianed = median_filter_time(signal, kernel_size=5)
    hampel = hampel_filter_time(signal, window_size=7)
    times, frequencies, spectrum = stft_spectrogram(signal, sample_rate_hz=50)

    assert medianed.shape == signal.shape
    assert hampel.shape == signal.shape
    assert times.size > 0
    assert frequencies.size == spectrum.shape[0]

