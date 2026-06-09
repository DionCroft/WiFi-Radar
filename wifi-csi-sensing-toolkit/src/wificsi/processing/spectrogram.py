"""Short-time Fourier transform helpers for Doppler-like CSI analysis."""

from __future__ import annotations

import numpy as np


def stft_spectrogram(
    signal: np.ndarray,
    sample_rate_hz: float,
    window_seconds: float = 2.0,
    step_seconds: float = 0.25,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute a basic magnitude STFT without requiring SciPy."""

    signal = np.asarray(signal, dtype=float)
    window_size = max(8, int(round(window_seconds * sample_rate_hz)))
    step_size = max(1, int(round(step_seconds * sample_rate_hz)))
    if signal.size < window_size:
        window_size = signal.size
    if window_size < 2:
        return np.array([]), np.array([]), np.empty((0, 0))

    window = np.hanning(window_size)
    spectra = []
    times = []
    for start in range(0, signal.size - window_size + 1, step_size):
        segment = signal[start : start + window_size]
        spectrum = np.abs(np.fft.rfft((segment - np.mean(segment)) * window))
        spectra.append(spectrum)
        times.append((start + window_size / 2.0) / sample_rate_hz)

    frequencies = np.fft.rfftfreq(window_size, d=1.0 / sample_rate_hz)
    return np.asarray(times), frequencies, np.asarray(spectra).T

