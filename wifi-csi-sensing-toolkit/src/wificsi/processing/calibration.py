"""CSI calibration and representation helpers."""

from __future__ import annotations

import numpy as np

from wificsi.core import CSIData


def remove_invalid_packets(data: CSIData) -> CSIData:
    """Drop packets containing NaNs or infinities."""

    flat = data.csi.reshape(data.packet_count, -1)
    valid = np.all(np.isfinite(flat.real) & np.isfinite(flat.imag), axis=1)
    rssi = data.rssi[valid] if data.rssi is not None else None
    return data.copy_with(csi=data.csi[valid], timestamps=data.timestamps[valid], rssi=rssi)


def select_subcarriers(data: CSIData, indices: list[int] | np.ndarray) -> CSIData:
    """Keep only selected subcarriers by integer index."""

    indices = np.asarray(indices, dtype=int)
    return data.copy_with(csi=data.csi[:, indices, :, :])


def amplitude(data_or_csi: CSIData | np.ndarray) -> np.ndarray:
    """Return CSI magnitude."""

    csi = data_or_csi.csi if isinstance(data_or_csi, CSIData) else data_or_csi
    return np.abs(csi)


def phase(data_or_csi: CSIData | np.ndarray) -> np.ndarray:
    """Return wrapped CSI phase in radians."""

    csi = data_or_csi.csi if isinstance(data_or_csi, CSIData) else data_or_csi
    return np.angle(csi)


def unwrap_phase_over_time(data_or_csi: CSIData | np.ndarray) -> np.ndarray:
    """Unwrap phase along the packet/time axis."""

    return np.unwrap(phase(data_or_csi), axis=0)


def remove_static_mean(data_or_csi: CSIData | np.ndarray) -> np.ndarray:
    """Subtract the packet-average CSI to reduce static clutter."""

    csi = data_or_csi.csi if isinstance(data_or_csi, CSIData) else data_or_csi
    return csi - np.mean(csi, axis=0, keepdims=True)


def normalise_amplitude(amp: np.ndarray) -> np.ndarray:
    """Normalise amplitude per subcarrier stream."""

    scale = np.nanmedian(np.abs(amp), axis=0, keepdims=True)
    scale = np.where(scale == 0.0, 1.0, scale)
    return amp / scale

