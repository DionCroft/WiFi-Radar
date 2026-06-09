"""Feature extraction and export helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from wificsi.core import CSIData
from wificsi.processing.calibration import amplitude, remove_static_mean


def flatten_streams(data: CSIData) -> np.ndarray:
    """Flatten CSI to packets x features."""

    return data.csi.reshape(data.packet_count, -1)


def pca_motion_component(data_or_matrix: CSIData | np.ndarray) -> np.ndarray:
    """Return the first principal component across subcarriers/antennas."""

    matrix = (
        remove_static_mean(data_or_matrix).reshape(data_or_matrix.packet_count, -1)
        if isinstance(data_or_matrix, CSIData)
        else np.asarray(data_or_matrix)
    )
    matrix = np.abs(matrix)
    matrix = matrix - np.mean(matrix, axis=0, keepdims=True)
    if matrix.shape[0] < 2:
        return np.zeros(matrix.shape[0], dtype=float)
    _, _, vh = np.linalg.svd(matrix, full_matrices=False)
    component = matrix @ vh[0]
    std = float(np.std(component))
    return component if std == 0.0 else component / std


def packet_energy(data: CSIData) -> np.ndarray:
    """Average CSI energy per packet."""

    return np.mean(amplitude(data) ** 2, axis=(1, 2, 3))


def export_features_csv(path: str | Path, timestamps: np.ndarray, features: dict[str, np.ndarray]) -> None:
    """Export one-dimensional features to CSV."""

    frame = pd.DataFrame({"timestamp": timestamps})
    for name, values in features.items():
        frame[name] = np.asarray(values)
    frame.to_csv(path, index=False)


def export_features_npz(path: str | Path, timestamps: np.ndarray, features: dict[str, np.ndarray]) -> None:
    """Export features to compressed NPZ."""

    np.savez_compressed(path, timestamps=timestamps, **features)

