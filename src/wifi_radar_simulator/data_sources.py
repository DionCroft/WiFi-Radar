"""Data source interfaces for synthetic and future real radar inputs."""

from __future__ import annotations

from typing import Protocol

from .simulation import RadarParameters, SimulationResult, simulate


class RadarDataSource(Protocol):
    """Common interface for anything that can provide radar data.

    The GUI only needs a ``run`` method. A future CSI or SDR implementation can
    follow this same contract and return a ``SimulationResult``-like structure.
    """

    def run(self, parameters: RadarParameters) -> SimulationResult:
        """Return processed radar data for the current parameter set."""
        ...


class SyntheticRadarSource:
    """Generate data from the built-in educational simulator."""

    def run(self, parameters: RadarParameters) -> SimulationResult:
        return simulate(parameters)


class RecordedCsiSource:
    """Placeholder for future channel state information file support."""

    def __init__(self, path: str) -> None:
        self.path = path

    def run(self, parameters: RadarParameters) -> SimulationResult:
        raise NotImplementedError(
            "CSI replay is planned. Use SyntheticRadarSource for this version."
        )
