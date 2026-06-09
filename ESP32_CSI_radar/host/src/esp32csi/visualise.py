"""Matplotlib visualisation for ESP32 CSI records."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from .breathing import BreathingResult
from .motion import MotionResult
from .processing import amplitude_phase, clean_records, sample_rate_from_timestamps
from .parser import CSIRecord


def amplitude_heatmap(records: list[CSIRecord]):
    timestamps, csi, _ = clean_records(records)
    amp, _ = amplitude_phase(csi)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    image = ax.imshow(amp, aspect="auto", origin="lower", interpolation="nearest")
    ax.set_title("ESP32 CSI amplitude heatmap")
    ax.set_xlabel("Subcarrier")
    ax.set_ylabel("Packet")
    fig.colorbar(image, ax=ax, label="Amplitude")
    return fig, ax


def motion_plot(result: MotionResult):
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(result.timestamps, result.score, label="Motion score")
    ax.axhline(result.threshold, color="tab:red", linestyle="--", label="Threshold")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Score")
    ax.grid(True, alpha=0.25)
    ax.legend()
    return fig, ax


def breathing_plot(result: BreathingResult):
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), constrained_layout=True)
    axes[0].plot(result.timestamps, result.waveform)
    axes[0].set_title("Breathing-like band signal")
    axes[0].set_xlabel("Time (s)")
    axes[0].grid(True, alpha=0.25)
    axes[1].plot(result.spectrum_hz, result.spectrum)
    axes[1].axvline(result.frequency_hz, color="tab:red", linestyle="--")
    axes[1].set_title(f"Estimated {result.breaths_per_minute:.1f} breaths/min")
    axes[1].set_xlabel("Frequency (Hz)")
    axes[1].grid(True, alpha=0.25)
    return fig, axes


def spectrogram_plot(records: list[CSIRecord]):
    timestamps, csi, _ = clean_records(records)
    amp = np.mean(np.abs(csi), axis=1)
    sample_rate = sample_rate_from_timestamps(timestamps)
    frequencies, times, spectrum = signal.spectrogram(
        amp - np.mean(amp),
        fs=sample_rate,
        nperseg=min(256, amp.size),
        noverlap=min(128, max(0, amp.size // 2 - 1)),
    )
    fig, ax = plt.subplots(figsize=(9, 4.5))
    image = ax.pcolormesh(times, frequencies, 10.0 * np.log10(spectrum + 1e-12), shading="auto")
    ax.set_title("CSI motion spectrogram")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    fig.colorbar(image, ax=ax, label="Power (dB)")
    return fig, ax


def save_figure(fig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)

