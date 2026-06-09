"""Small CSI calibration helpers used by the simulator and file replay."""

from __future__ import annotations

import numpy as np


def unwrap_csi_phase(csi_matrix: np.ndarray) -> np.ndarray:
    """Unwrap CSI phase across subcarriers, then across packets.

    Raw phase is limited to the interval ``-pi`` to ``pi``. When the true phase
    crosses that boundary it appears to jump suddenly. Unwrapping adds or
    subtracts ``2*pi`` so phase changes look continuous again.
    """

    phase = np.angle(csi_matrix)
    phase = np.unwrap(phase, axis=1)
    return np.unwrap(phase, axis=0)


def remove_static_background(csi_matrix: np.ndarray) -> np.ndarray:
    """Remove the packet-average channel to emphasize moving changes.

    Static reflectors such as walls and furniture often dominate WiFi CSI. A
    simple first classroom step is subtracting the mean channel over time. More
    advanced systems use calibration packets, filtering, or reference antennas.
    """

    if csi_matrix.ndim != 2:
        raise ValueError("csi_matrix must be 2-D")
    static_estimate = np.mean(csi_matrix, axis=0, keepdims=True)
    return csi_matrix - static_estimate


def apply_slow_time_window(csi_or_signal: np.ndarray) -> np.ndarray:
    """Apply a Hann window over packets before Doppler processing.

    FFTs assume the observation repeats forever. A window tapers the start and
    end of the packet sequence, reducing spectral leakage in the Doppler plot.
    """

    if csi_or_signal.ndim == 1:
        window = np.hanning(csi_or_signal.size)
    elif csi_or_signal.ndim == 2:
        window = np.hanning(csi_or_signal.shape[0])[:, np.newaxis]
    else:
        raise ValueError("input must be 1-D or 2-D")
    return csi_or_signal * window

