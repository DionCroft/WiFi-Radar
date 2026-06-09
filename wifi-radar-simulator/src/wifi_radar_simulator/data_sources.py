"""Data source interfaces for synthetic, CSI, and SDR radar inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .simulation import (
    RadarParameters,
    SimulationResult,
    build_result_from_csi,
    simulate,
)


class RadarDataSource(Protocol):
    """Common interface for anything that can provide radar data."""

    name: str

    def run(self, parameters: RadarParameters) -> SimulationResult:
        """Return processed radar data for the current parameter set."""
        ...


class SyntheticRadarSource:
    """Generate data from the built-in educational simulator."""

    name = "Synthetic scene"

    def run(self, parameters: RadarParameters) -> SimulationResult:
        return simulate(parameters)


class CsiFileSource:
    """Load recorded channel state information from a CSV file.

    The first supported format is intentionally simple and easy to export from
    other tools:

    ``packet,subcarrier,real,imag``

    Each row is one complex CSI value. The loader pivots those rows into a
    packets x subcarriers matrix before applying the same calibration examples
    and plotting pipeline used by the synthetic scene.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.name = f"CSI file: {self.path.name}"

    def run(self, parameters: RadarParameters) -> SimulationResult:
        csi_matrix, subcarriers = load_csi_csv(self.path)
        return build_result_from_csi(
            csi_matrix=csi_matrix,
            subcarriers=subcarriers,
            parameters=parameters,
            source_name=self.name,
        )


class SdrCaptureBackend(Protocol):
    """Minimal adapter expected from a real SDR implementation.

    Hardware-specific code can live in a separate module or package. It only has
    to return a packets x subcarriers complex CSI-like matrix and matching
    subcarrier numbers for the rest of the application to work.
    """

    def capture_csi(
        self,
        parameters: RadarParameters,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Capture or estimate CSI from radio samples."""
        ...


class SdrCaptureSource:
    """Data source wrapper for future live SDR capture support."""

    name = "SDR capture"

    def __init__(self, backend: SdrCaptureBackend | None = None) -> None:
        self.backend = backend

    def run(self, parameters: RadarParameters) -> SimulationResult:
        if self.backend is None:
            raise RuntimeError(
                "No SDR backend is configured. Provide an SdrCaptureBackend "
                "adapter for hardware such as SoapySDR, UHD, or GNU Radio."
            )

        csi_matrix, subcarriers = self.backend.capture_csi(parameters)
        return build_result_from_csi(
            csi_matrix=csi_matrix,
            subcarriers=subcarriers,
            parameters=parameters,
            source_name=self.name,
        )


def load_csi_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load ``packet,subcarrier,real,imag`` CSI CSV data."""

    path = Path(path)
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=float)
    data = np.atleast_1d(data)

    if data.size == 0:
        raise ValueError(f"{path} does not contain CSI rows")
    if data.dtype.names is None:
        raise ValueError("CSI CSV must include a header row")

    names = {name.lower(): name for name in data.dtype.names}
    required = ("packet", "subcarrier", "real", "imag")
    missing = [name for name in required if name not in names]
    if missing:
        raise ValueError(
            "CSI CSV must contain packet, subcarrier, real, and imag columns"
        )

    packet_values = np.asarray(data[names["packet"]], dtype=int)
    subcarrier_values = np.asarray(data[names["subcarrier"]], dtype=float)
    real_values = np.asarray(data[names["real"]], dtype=float)
    imag_values = np.asarray(data[names["imag"]], dtype=float)

    packets = np.unique(packet_values)
    subcarriers = np.unique(subcarrier_values)
    packet_to_row = {packet: index for index, packet in enumerate(packets)}
    subcarrier_to_col = {
        subcarrier: index for index, subcarrier in enumerate(subcarriers)
    }

    csi_matrix = np.zeros((packets.size, subcarriers.size), dtype=complex)
    for packet, subcarrier, real, imag in zip(
        packet_values,
        subcarrier_values,
        real_values,
        imag_values,
    ):
        row = packet_to_row[int(packet)]
        col = subcarrier_to_col[float(subcarrier)]
        csi_matrix[row, col] = real + 1j * imag

    return csi_matrix, subcarriers

