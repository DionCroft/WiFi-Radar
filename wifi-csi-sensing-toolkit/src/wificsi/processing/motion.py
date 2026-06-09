"""Motion and occupancy scoring."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wificsi.core import CSIData
from wificsi.processing.calibration import remove_static_mean
from wificsi.processing.filtering import moving_average


@dataclass(frozen=True)
class MotionResult:
    timestamps: np.ndarray
    score: np.ndarray
    threshold: float
    occupied: bool


def motion_score(
    data: CSIData,
    smooth_window: int = 5,
    threshold_scale: float = 3.0,
) -> MotionResult:
    """Compute a simple motion/occupancy score from CSI variance energy."""

    dynamic = remove_static_mean(data)
    amp_change = np.abs(dynamic)
    score = np.mean(amp_change**2, axis=(1, 2, 3))
    if smooth_window > 1 and score.size >= smooth_window:
        score = moving_average(score, smooth_window)

    baseline = float(np.median(score))
    spread = float(np.median(np.abs(score - baseline)))
    threshold = baseline + threshold_scale * 1.4826 * spread
    occupied = bool(np.any(score > threshold)) if score.size else False
    return MotionResult(data.timestamps, score, threshold, occupied)

