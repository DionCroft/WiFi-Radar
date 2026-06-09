"""Motion and presence scoring."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .processing import clean_records, remove_static_mean
from .parser import CSIRecord


@dataclass(frozen=True)
class MotionResult:
    timestamps: np.ndarray
    score: np.ndarray
    threshold: float
    present: bool


def motion_score(records: list[CSIRecord], threshold_scale: float = 3.0) -> MotionResult:
    """Compute robust motion energy after static clutter removal."""

    timestamps, csi, _ = clean_records(records)
    dynamic = remove_static_mean(np.abs(csi))
    score = np.mean(dynamic**2, axis=1)
    baseline = float(np.median(score))
    mad = float(np.median(np.abs(score - baseline)))
    threshold = baseline + threshold_scale * 1.4826 * mad
    return MotionResult(timestamps, score, threshold, bool(np.any(score > threshold)))

