"""Breathing-like periodic motion estimation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wificsi.core import CSIData
from wificsi.processing.features import pca_motion_component
from wificsi.processing.filtering import moving_average


@dataclass(frozen=True)
class BreathingResult:
    timestamps: np.ndarray
    waveform: np.ndarray
    frequency_hz: float
    breaths_per_minute: float
    spectrum_hz: np.ndarray
    spectrum: np.ndarray


def estimate_breathing_rate(
    data: CSIData,
    min_hz: float = 0.1,
    max_hz: float = 0.6,
) -> BreathingResult:
    """Estimate a breathing-like rate from low-frequency CSI motion."""

    if min_hz <= 0 or max_hz <= min_hz:
        raise ValueError("breathing search range must satisfy 0 < min_hz < max_hz")
    sample_rate = data.sample_rate_hz
    if sample_rate <= 0:
        raise ValueError("timestamps must contain a valid sample rate")

    waveform = pca_motion_component(data)
    if waveform.size >= 5:
        waveform = moving_average(waveform, 5)
    waveform = waveform - np.mean(waveform)

    window = np.hanning(waveform.size)
    spectrum = np.abs(np.fft.rfft(waveform * window))
    frequencies = np.fft.rfftfreq(waveform.size, d=1.0 / sample_rate)
    mask = (frequencies >= min_hz) & (frequencies <= max_hz)
    if not np.any(mask):
        raise ValueError("no FFT bins fall inside the requested breathing range")

    local_index = int(np.argmax(spectrum[mask]))
    frequency_hz = float(frequencies[mask][local_index])
    return BreathingResult(
        timestamps=data.timestamps,
        waveform=waveform,
        frequency_hz=frequency_hz,
        breaths_per_minute=frequency_hz * 60.0,
        spectrum_hz=frequencies,
        spectrum=spectrum,
    )

