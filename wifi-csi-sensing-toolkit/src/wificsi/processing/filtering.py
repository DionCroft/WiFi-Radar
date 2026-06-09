"""Filtering functions for CSI time series."""

from __future__ import annotations

import numpy as np


def highpass_mean(signal: np.ndarray) -> np.ndarray:
    """Simple high-pass effect by removing the time average."""

    return signal - np.mean(signal, axis=0, keepdims=True)


def median_filter_time(signal: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply a small median filter along time without requiring SciPy."""

    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be a positive odd integer")
    if kernel_size == 1:
        return signal.copy()

    pad = kernel_size // 2
    padded = np.pad(signal, [(pad, pad)] + [(0, 0)] * (signal.ndim - 1), mode="edge")
    windows = np.stack([padded[offset : offset + signal.shape[0]] for offset in range(kernel_size)])
    return np.median(windows, axis=0)


def hampel_filter_time(
    signal: np.ndarray,
    window_size: int = 7,
    n_sigmas: float = 3.0,
) -> np.ndarray:
    """Suppress outliers using a Hampel-style median absolute deviation rule."""

    if window_size < 3 or window_size % 2 == 0:
        raise ValueError("window_size must be an odd integer greater than 1")

    filtered = np.asarray(signal, dtype=float).copy()
    pad = window_size // 2
    padded = np.pad(filtered, [(pad, pad)] + [(0, 0)] * (filtered.ndim - 1), mode="edge")

    for index in range(filtered.shape[0]):
        window = padded[index : index + window_size]
        median = np.median(window, axis=0)
        mad = np.median(np.abs(window - median), axis=0)
        threshold = n_sigmas * 1.4826 * np.where(mad == 0.0, 1e-12, mad)
        mask = np.abs(filtered[index] - median) > threshold
        filtered[index] = np.where(mask, median, filtered[index])
    return filtered


def moving_average(signal: np.ndarray, window_size: int = 5) -> np.ndarray:
    """Smooth a one-dimensional signal with a centered moving average."""

    if window_size < 1:
        raise ValueError("window_size must be positive")
    kernel = np.ones(window_size, dtype=float) / window_size
    return np.convolve(signal, kernel, mode="same")

