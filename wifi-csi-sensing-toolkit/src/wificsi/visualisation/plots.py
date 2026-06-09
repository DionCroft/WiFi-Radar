"""Matplotlib plotting functions for CSI data and sensing outputs."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from wificsi.core import CSIData
from wificsi.processing.breathing import BreathingResult
from wificsi.processing.calibration import amplitude, unwrap_phase_over_time
from wificsi.processing.motion import MotionResult


def plot_amplitude_heatmap(data: CSIData):
    """Plot CSI amplitude as packets versus subcarriers."""

    matrix = amplitude(data.first_stream())
    fig, ax = plt.subplots(figsize=(9, 4.5))
    image = ax.imshow(matrix, aspect="auto", origin="lower", interpolation="nearest")
    ax.set_title("CSI amplitude heatmap")
    ax.set_xlabel("Subcarrier")
    ax.set_ylabel("Packet")
    fig.colorbar(image, ax=ax, label="Amplitude")
    return fig, ax


def plot_phase_heatmap(data: CSIData):
    """Plot unwrapped CSI phase as packets versus subcarriers."""

    matrix = unwrap_phase_over_time(data.first_stream())
    fig, ax = plt.subplots(figsize=(9, 4.5))
    image = ax.imshow(matrix, aspect="auto", origin="lower", interpolation="nearest")
    ax.set_title("CSI phase heatmap")
    ax.set_xlabel("Subcarrier")
    ax.set_ylabel("Packet")
    fig.colorbar(image, ax=ax, label="Phase (rad)")
    return fig, ax


def plot_motion_score(result: MotionResult):
    """Plot motion score and detection threshold."""

    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(result.timestamps, result.score, label="Motion score")
    ax.axhline(result.threshold, color="tab:red", linestyle="--", label="Threshold")
    ax.set_title("Motion score over time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Score")
    ax.grid(True, alpha=0.25)
    ax.legend()
    return fig, ax


def plot_spectrogram(times: np.ndarray, frequencies: np.ndarray, spectrum: np.ndarray):
    """Plot Doppler or motion spectrogram."""

    fig, ax = plt.subplots(figsize=(9, 4.5))
    db = 20.0 * np.log10(spectrum + 1e-12)
    image = ax.pcolormesh(times, frequencies, db, shading="auto")
    ax.set_title("CSI Doppler / motion spectrogram")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    fig.colorbar(image, ax=ax, label="Magnitude (dB)")
    return fig, ax


def plot_breathing(result: BreathingResult):
    """Plot breathing waveform and spectrum."""

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), constrained_layout=True)
    axes[0].plot(result.timestamps, result.waveform)
    axes[0].set_title("Breathing-like waveform")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Relative motion")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(result.spectrum_hz, result.spectrum)
    axes[1].axvline(result.frequency_hz, color="tab:red", linestyle="--")
    axes[1].set_xlim(0.0, max(1.0, result.frequency_hz * 3.0))
    axes[1].set_title(f"Estimated rate: {result.breaths_per_minute:.1f} breaths/min")
    axes[1].set_xlabel("Frequency (Hz)")
    axes[1].set_ylabel("Magnitude")
    axes[1].grid(True, alpha=0.25)
    return fig, axes

