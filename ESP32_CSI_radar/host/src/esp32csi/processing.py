"""DSP helpers for ESP32 CSI records."""

from __future__ import annotations

import numpy as np
from scipy import signal

from .parser import CSIRecord, records_to_matrix


def clean_records(records: list[CSIRecord]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert valid records to timestamps, CSI matrix, and RSSI."""

    timestamps, csi, rssi = records_to_matrix(records)
    valid = np.all(np.isfinite(csi.real) & np.isfinite(csi.imag), axis=1)
    return timestamps[valid], csi[valid], rssi[valid]


def amplitude_phase(csi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return amplitude and wrapped phase."""

    return np.abs(csi), np.angle(csi)


def unwrap_phase(phase: np.ndarray) -> np.ndarray:
    """Unwrap phase over packets/time."""

    return np.unwrap(phase, axis=0)


def remove_static_mean(values: np.ndarray) -> np.ndarray:
    """Subtract the packet-average static component."""

    return values - np.mean(values, axis=0, keepdims=True)


def median_filter(values: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Median filter along time."""

    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be a positive odd integer")
    return signal.medfilt(values, kernel_size=(kernel_size, 1))


def hampel_filter(values: np.ndarray, window_size: int = 7, n_sigmas: float = 3.0) -> np.ndarray:
    """Suppress outliers with a Hampel-style median absolute deviation filter."""

    filtered = values.copy()
    half = window_size // 2
    for index in range(values.shape[0]):
        start = max(0, index - half)
        stop = min(values.shape[0], index + half + 1)
        window = values[start:stop]
        med = np.median(window, axis=0)
        mad = np.median(np.abs(window - med), axis=0)
        threshold = n_sigmas * 1.4826 * np.where(mad == 0.0, 1e-12, mad)
        mask = np.abs(values[index] - med) > threshold
        filtered[index] = np.where(mask, med, values[index])
    return filtered


def highpass_filter(values: np.ndarray, sample_rate_hz: float, cutoff_hz: float = 0.05) -> np.ndarray:
    """High-pass filter for motion emphasis."""

    if sample_rate_hz <= 0:
        return remove_static_mean(values)
    sos = signal.butter(2, cutoff_hz, btype="highpass", fs=sample_rate_hz, output="sos")
    return signal.sosfiltfilt(sos, values, axis=0)


def bandpass_filter(
    values: np.ndarray,
    sample_rate_hz: float,
    low_hz: float = 0.1,
    high_hz: float = 0.6,
) -> np.ndarray:
    """Band-pass filter for breathing-like periodic motion."""

    sos = signal.butter(3, [low_hz, high_hz], btype="bandpass", fs=sample_rate_hz, output="sos")
    return signal.sosfiltfilt(sos, values, axis=0)


def pca_first_component(values: np.ndarray) -> np.ndarray:
    """First principal component across subcarriers."""

    centered = values - np.mean(values, axis=0, keepdims=True)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    component = centered @ vh[0]
    std = float(np.std(component))
    return component if std == 0.0 else component / std


def sample_rate_from_timestamps(timestamps: np.ndarray) -> float:
    """Estimate packet rate from timestamp seconds."""

    diffs = np.diff(timestamps)
    diffs = diffs[diffs > 0]
    if diffs.size == 0:
        return 0.0
    return float(1.0 / np.median(diffs))

