"""Synthetic CSI generator for offline tests and demos."""

from __future__ import annotations

import numpy as np

from wificsi.core import CSIData

SPEED_OF_LIGHT_MPS = 299_792_458.0


def generate_synthetic_csi(
    seconds: float = 30.0,
    rate_hz: float = 100.0,
    subcarriers: int = 52,
    rx_antennas: int = 1,
    tx_antennas: int = 1,
    carrier_frequency_hz: float = 5.32e9,
    bandwidth_hz: float = 20e6,
    motion_hz: float = 1.2,
    breathing_hz: float | None = 0.25,
    breathing_displacement_m: float = 0.004,
    noise_std: float = 0.03,
    seed: int = 11,
) -> CSIData:
    """Create realistic synthetic CSI with static and moving paths."""

    rng = np.random.default_rng(seed)
    packets = max(2, int(round(seconds * rate_hz)))
    timestamps = np.arange(packets, dtype=float) / rate_hz
    subcarrier_index = _centered_subcarriers(subcarriers)
    subcarrier_spacing_hz = bandwidth_hz / 64.0
    frequency_offsets_hz = subcarrier_index * subcarrier_spacing_hz
    wavelength_m = SPEED_OF_LIGHT_MPS / carrier_frequency_hz

    csi = np.zeros((packets, subcarriers, rx_antennas, tx_antennas), dtype=complex)

    static_paths = [(4.0, 1.0, 0.0), (8.5, 0.55, 1.4), (17.0, 0.35, -0.7)]
    for distance_m, gain, phase in static_paths:
        csi += _path_response(
            timestamps,
            frequency_offsets_hz,
            distance_m=np.full_like(timestamps, distance_m),
            gain=gain,
            phase_offset=phase,
            wavelength_m=wavelength_m,
            rx_antennas=rx_antennas,
            tx_antennas=tx_antennas,
        )

    moving_distance = 3.0 + 0.05 * np.sin(2.0 * np.pi * motion_hz * timestamps)
    if breathing_hz is not None:
        moving_distance += breathing_displacement_m * np.sin(
            2.0 * np.pi * breathing_hz * timestamps
        )
    csi += _path_response(
        timestamps,
        frequency_offsets_hz,
        distance_m=moving_distance,
        gain=0.22,
        phase_offset=0.3,
        wavelength_m=wavelength_m,
        rx_antennas=rx_antennas,
        tx_antennas=tx_antennas,
    )

    noise = noise_std * (
        rng.standard_normal(csi.shape) + 1j * rng.standard_normal(csi.shape)
    )
    csi += noise

    rssi = 40.0 + 2.0 * np.log10(np.maximum(np.mean(np.abs(csi), axis=(1, 2, 3)), 1e-9))
    return CSIData(
        csi=csi,
        timestamps=timestamps,
        rssi=rssi,
        carrier_frequency_hz=carrier_frequency_hz,
        bandwidth_hz=bandwidth_hz,
        source="synthetic",
        metadata={
            "motion_hz": motion_hz,
            "breathing_hz": breathing_hz,
            "noise_std": noise_std,
        },
    )


def _path_response(
    timestamps: np.ndarray,
    frequency_offsets_hz: np.ndarray,
    distance_m: np.ndarray,
    gain: float,
    phase_offset: float,
    wavelength_m: float,
    rx_antennas: int,
    tx_antennas: int,
) -> np.ndarray:
    delay_s = distance_m[:, np.newaxis] / SPEED_OF_LIGHT_MPS
    carrier_phase = -2.0 * np.pi * distance_m[:, np.newaxis] / wavelength_m
    subcarrier_phase = -2.0 * np.pi * delay_s * frequency_offsets_hz[np.newaxis, :]
    base = gain * np.exp(1j * (carrier_phase + subcarrier_phase + phase_offset))
    return base[:, :, np.newaxis, np.newaxis] * np.ones(
        (timestamps.size, frequency_offsets_hz.size, rx_antennas, tx_antennas),
        dtype=complex,
    )


def _centered_subcarriers(count: int) -> np.ndarray:
    half = count // 2
    negative = np.arange(-half, 0)
    positive = np.arange(1, count - half + 1)
    return np.concatenate((negative, positive)).astype(float)

