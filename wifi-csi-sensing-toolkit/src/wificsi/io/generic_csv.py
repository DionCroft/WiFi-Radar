"""Generic CSV and text CSI loaders."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd

from wificsi.core import CSIData, ensure_complex_matrix


def load_generic_csv(path: str | Path) -> CSIData:
    """Load generic CSV rows with timestamp and CSI values.

    Supported layouts:
    - `timestamp,csi` where csi is a list of interleaved real/imag values.
    - `timestamp,csi_0_real,csi_0_imag,csi_1_real,csi_1_imag,...`
    - `timestamp,real0,imag0,real1,imag1,...`
    """

    path = Path(path)
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"{path} contains no CSI rows")

    timestamp_column = _find_column(frame, ("timestamp", "time", "ts"))
    timestamps = (
        frame[timestamp_column].to_numpy(dtype=float)
        if timestamp_column
        else np.arange(len(frame), dtype=float)
    )

    if "csi" in frame.columns:
        rows = [_parse_vector(value) for value in frame["csi"]]
        matrix = ensure_complex_matrix(np.vstack(rows))
    else:
        value_columns = [column for column in frame.columns if column != timestamp_column]
        numeric = frame[value_columns].to_numpy(dtype=float)
        matrix = ensure_complex_matrix(numeric)

    return CSIData(
        csi=matrix,
        timestamps=_normalise_timestamps(timestamps),
        source=f"generic_csv:{path.name}",
        metadata={"path": str(path), "columns": list(frame.columns)},
    )


def _find_column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lower_to_original = {column.lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate in lower_to_original:
            return lower_to_original[candidate]
    return None


def _parse_vector(value: object) -> np.ndarray:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            parsed = ast.literal_eval(text)
            return np.asarray(parsed, dtype=float)
        return np.fromstring(text.replace(";", ","), sep=",", dtype=float)
    return np.asarray(value, dtype=float)


def _normalise_timestamps(timestamps: np.ndarray) -> np.ndarray:
    timestamps = np.asarray(timestamps, dtype=float)
    if timestamps.size == 0:
        return timestamps
    timestamps = timestamps - timestamps[0]
    if timestamps.size > 1 and np.nanmedian(np.diff(timestamps)) > 10.0:
        timestamps = timestamps / 1000.0
    return timestamps

