"""Breathing-like periodic motion estimation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .parser import CSIRecord
from .processing import (
    amplitude_phase,
    bandpass_filter,
    clean_records,
    pca_first_component,
    sample_rate_from_timestamps,
    unwrap_phase,
)


@dataclass(frozen=True)
class BreathingResult:
    timestamps: np.ndarray
    waveform: np.ndarray
    frequency_hz: float
    breaths_per_minute: float
    spectrum_hz: np.ndarray
    spectrum: np.ndarray


def estimate_breathing_rate(
    records: list[CSIRecord],
    min_hz: float = 0.1,
    max_hz: float = 0.6,
) -> BreathingResult:
    """Estimate breathing-like rate from unwrapped CSI phase PCA."""

    timestamps, csi, _ = clean_records(records)
    sample_rate = sample_rate_from_timestamps(timestamps)
    if sample_rate <= 0:
        raise ValueError("cannot estimate sample rate from timestamps")

    _, phase = amplitude_phase(csi)
    phase_unwrapped = unwrap_phase(phase)
    component = pca_first_component(phase_unwrapped)
    waveform = bandpass_filter(component[:, np.newaxis], sample_rate, min_hz, max_hz)[:, 0]
    spectrum = np.abs(np.fft.rfft((waveform - np.mean(waveform)) * np.hanning(waveform.size)))
    frequencies = np.fft.rfftfreq(waveform.size, d=1.0 / sample_rate)
    mask = (frequencies >= min_hz) & (frequencies <= max_hz)
    if not np.any(mask):
        raise ValueError("no FFT bins in requested breathing band")
    frequency = float(frequencies[mask][int(np.argmax(spectrum[mask]))])
    return BreathingResult(timestamps, waveform, frequency, frequency * 60.0, frequencies, spectrum)

