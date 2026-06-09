"""Core CSI data model and common utilities."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np


class CSIError(RuntimeError):
    """Base exception for clear CSI toolkit errors."""


class UnsupportedFormatError(CSIError):
    """Raised when an optional parser or file format is unavailable."""


@dataclass(frozen=True)
class CSIData:
    """Common internal representation for Wi-Fi CSI.

    The CSI array is always normalised to four dimensions:
    ``packets x subcarriers x rx_antennas x tx_antennas``.
    """

    csi: np.ndarray
    timestamps: np.ndarray
    rssi: np.ndarray | None = None
    channel: int | None = None
    carrier_frequency_hz: float | None = None
    bandwidth_hz: float | None = None
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        csi = np.asarray(self.csi, dtype=np.complex128)
        if csi.ndim == 2:
            csi = csi[:, :, np.newaxis, np.newaxis]
        elif csi.ndim == 3:
            csi = csi[:, :, :, np.newaxis]
        elif csi.ndim != 4:
            raise ValueError(
                "csi must have shape packets x subcarriers x rx x tx, "
                "or a lower-dimensional compatible shape"
            )

        timestamps = np.asarray(self.timestamps, dtype=float)
        if timestamps.ndim != 1:
            raise ValueError("timestamps must be a one-dimensional array")
        if timestamps.size != csi.shape[0]:
            raise ValueError("timestamps length must match CSI packet count")

        object.__setattr__(self, "csi", csi)
        object.__setattr__(self, "timestamps", timestamps)
        if self.rssi is not None:
            object.__setattr__(self, "rssi", np.asarray(self.rssi, dtype=float))

    @property
    def packet_count(self) -> int:
        return int(self.csi.shape[0])

    @property
    def subcarrier_count(self) -> int:
        return int(self.csi.shape[1])

    @property
    def rx_count(self) -> int:
        return int(self.csi.shape[2])

    @property
    def tx_count(self) -> int:
        return int(self.csi.shape[3])

    @property
    def duration_s(self) -> float:
        if self.timestamps.size < 2:
            return 0.0
        return float(self.timestamps[-1] - self.timestamps[0])

    @property
    def sample_rate_hz(self) -> float:
        if self.timestamps.size < 2:
            return 0.0
        diffs = np.diff(self.timestamps)
        valid = diffs[diffs > 0]
        if valid.size == 0:
            return 0.0
        return float(1.0 / np.median(valid))

    def copy_with(self, **changes: Any) -> "CSIData":
        return replace(self, **changes)

    def first_stream(self) -> np.ndarray:
        """Return packets x subcarriers for the first rx/tx stream."""

        return self.csi[:, :, 0, 0]

    def summary(self) -> str:
        return (
            f"source={self.source}, packets={self.packet_count}, "
            f"subcarriers={self.subcarrier_count}, rx={self.rx_count}, "
            f"tx={self.tx_count}, duration={self.duration_s:.2f}s, "
            f"rate={self.sample_rate_hz:.2f}Hz"
        )


def save_npz(data: CSIData, path: str | Path) -> None:
    """Save CSIData in the toolkit's generic NPZ interchange format."""

    np.savez_compressed(
        path,
        csi=data.csi,
        timestamps=data.timestamps,
        rssi=data.rssi if data.rssi is not None else np.array([]),
        channel=-1 if data.channel is None else data.channel,
        carrier_frequency_hz=np.nan
        if data.carrier_frequency_hz is None
        else data.carrier_frequency_hz,
        bandwidth_hz=np.nan if data.bandwidth_hz is None else data.bandwidth_hz,
        source=data.source,
        metadata=np.array([repr(data.metadata)], dtype=object),
    )


def load_npz(path: str | Path) -> CSIData:
    """Load the toolkit's generic NPZ interchange format."""

    with np.load(path, allow_pickle=True) as npz:
        rssi = npz["rssi"]
        channel = int(npz["channel"]) if int(npz["channel"]) >= 0 else None
        carrier = float(npz["carrier_frequency_hz"])
        bandwidth = float(npz["bandwidth_hz"])
        return CSIData(
            csi=npz["csi"],
            timestamps=npz["timestamps"],
            rssi=None if rssi.size == 0 else rssi,
            channel=channel,
            carrier_frequency_hz=None if np.isnan(carrier) else carrier,
            bandwidth_hz=None if np.isnan(bandwidth) else bandwidth,
            source=str(npz["source"]),
            metadata={"loaded_from": str(path)},
        )


def ensure_complex_matrix(values: np.ndarray) -> np.ndarray:
    """Convert interleaved real/imag numeric values to a complex matrix."""

    values = np.asarray(values, dtype=float)
    if values.shape[-1] % 2 != 0:
        raise ValueError("CSI vector must contain interleaved real/imag pairs")
    real = values[..., 0::2]
    imag = values[..., 1::2]
    return real + 1j * imag

