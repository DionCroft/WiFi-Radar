"""Numerical model for the educational WiFi radar simulator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SPEED_OF_LIGHT_MPS = 299_792_458.0


@dataclass(frozen=True)
class RadarParameters:
    """User-adjustable radar and target parameters.

    The carrier frequency is a real WiFi channel frequency, while the transmit
    waveform is a complex baseband chirp. Baseband means the 2.4 GHz carrier has
    already been mathematically removed, which is how most digital radio signal
    processing code views the received samples.
    """

    carrier_frequency_hz: float = 2.437e9
    bandwidth_hz: float = 20.0e6
    packet_duration_s: float = 20.0e-6
    sample_rate_hz: float = 100.0e6
    packet_rate_hz: float = 500.0
    packets: int = 512
    initial_range_m: float = 12.0
    target_velocity_mps: float = 1.2
    noise_std: float = 0.02
    seed: int = 7


@dataclass(frozen=True)
class SimulationResult:
    """Arrays returned by one simulator run."""

    time_s: np.ndarray
    tx_signal: np.ndarray
    rx_signal: np.ndarray
    doppler_hz: np.ndarray
    doppler_spectrum: np.ndarray
    range_m: np.ndarray
    range_response: np.ndarray
    expected_delay_s: float
    expected_doppler_hz: float
    expected_range_m: float
    range_resolution_m: float


def simulate(parameters: RadarParameters) -> SimulationResult:
    """Run the synthetic radar model.

    The model has two pieces:

    1. Fast time: one short transmitted probe is delayed and attenuated to model
       a reflected signal from a target at a fixed range.
    2. Slow time: many packet returns are used to show Doppler as phase rotation
       from packet to packet.
    """

    _validate_parameters(parameters)

    rng = np.random.default_rng(parameters.seed)
    time_s = _sample_times(parameters)
    tx_signal = _baseband_chirp(time_s, parameters.bandwidth_hz, parameters.packet_duration_s)

    wavelength_m = SPEED_OF_LIGHT_MPS / parameters.carrier_frequency_hz
    expected_delay_s = 2.0 * parameters.initial_range_m / SPEED_OF_LIGHT_MPS
    expected_doppler_hz = 2.0 * parameters.target_velocity_mps / wavelength_m

    rx_signal = _reflected_packet(
        tx_signal=tx_signal,
        time_s=time_s,
        delay_s=expected_delay_s,
        doppler_hz=expected_doppler_hz,
        sample_rate_hz=parameters.sample_rate_hz,
        range_m=parameters.initial_range_m,
        noise_std=parameters.noise_std,
        rng=rng,
    )

    range_m, range_response = _range_response(
        tx_signal=tx_signal,
        rx_signal=rx_signal,
        sample_rate_hz=parameters.sample_rate_hz,
    )
    doppler_hz, doppler_spectrum = _doppler_spectrum(parameters, wavelength_m, rng)

    range_resolution_m = SPEED_OF_LIGHT_MPS / (2.0 * parameters.bandwidth_hz)

    return SimulationResult(
        time_s=time_s,
        tx_signal=tx_signal,
        rx_signal=rx_signal,
        doppler_hz=doppler_hz,
        doppler_spectrum=doppler_spectrum,
        range_m=range_m,
        range_response=range_response,
        expected_delay_s=expected_delay_s,
        expected_doppler_hz=expected_doppler_hz,
        expected_range_m=parameters.initial_range_m,
        range_resolution_m=range_resolution_m,
    )


def _validate_parameters(parameters: RadarParameters) -> None:
    if parameters.carrier_frequency_hz <= 0:
        raise ValueError("carrier_frequency_hz must be positive")
    if parameters.bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive")
    if parameters.packet_duration_s <= 0:
        raise ValueError("packet_duration_s must be positive")
    if parameters.sample_rate_hz <= 2.0 * parameters.bandwidth_hz:
        raise ValueError("sample_rate_hz should exceed twice the bandwidth")
    if parameters.packet_rate_hz <= 0:
        raise ValueError("packet_rate_hz must be positive")
    if parameters.packets < 8:
        raise ValueError("packets must be at least 8")
    if parameters.initial_range_m <= 0:
        raise ValueError("initial_range_m must be positive")
    if parameters.noise_std < 0:
        raise ValueError("noise_std must be non-negative")


def _sample_times(parameters: RadarParameters) -> np.ndarray:
    sample_count = int(round(parameters.packet_duration_s * parameters.sample_rate_hz))
    return np.arange(sample_count, dtype=float) / parameters.sample_rate_hz


def _baseband_chirp(
    time_s: np.ndarray,
    bandwidth_hz: float,
    duration_s: float,
) -> np.ndarray:
    """Create a complex chirp centered around zero baseband frequency.

    A chirp sweeps through frequency during the packet. When the receiver
    correlates the echo with the known transmitted chirp, delayed copies produce
    peaks that can be interpreted as range-like information.
    """

    chirp_rate_hz_per_s = bandwidth_hz / duration_s
    start_frequency_hz = -0.5 * bandwidth_hz
    phase_cycles = start_frequency_hz * time_s + 0.5 * chirp_rate_hz_per_s * time_s**2
    window = np.hanning(time_s.size)
    return window * np.exp(1j * 2.0 * np.pi * phase_cycles)


def _reflected_packet(
    tx_signal: np.ndarray,
    time_s: np.ndarray,
    delay_s: float,
    doppler_hz: float,
    sample_rate_hz: float,
    range_m: float,
    noise_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Delay and Doppler-shift the transmitted packet to make an echo."""

    delayed = _fractional_delay(tx_signal, delay_s * sample_rate_hz)

    # Echoes get weaker with distance. This display-oriented scaling keeps the
    # target visible while still showing that far targets are harder to detect.
    attenuation = 1.0 / (1.0 + range_m / 8.0) ** 2
    doppler_phase = np.exp(1j * 2.0 * np.pi * doppler_hz * time_s)
    echo = attenuation * delayed * doppler_phase

    noise = noise_std * (
        rng.standard_normal(tx_signal.size) + 1j * rng.standard_normal(tx_signal.size)
    )
    return echo + noise


def _fractional_delay(signal: np.ndarray, delay_samples: float) -> np.ndarray:
    """Apply a non-integer sample delay using linear interpolation."""

    sample_index = np.arange(signal.size, dtype=float)
    delayed_real = np.interp(
        sample_index - delay_samples,
        sample_index,
        signal.real,
        left=0.0,
        right=0.0,
    )
    delayed_imag = np.interp(
        sample_index - delay_samples,
        sample_index,
        signal.imag,
        left=0.0,
        right=0.0,
    )
    return delayed_real + 1j * delayed_imag


def _range_response(
    tx_signal: np.ndarray,
    rx_signal: np.ndarray,
    sample_rate_hz: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Matched-filter the echo against the known transmitted probe."""

    correlation = np.correlate(rx_signal, tx_signal, mode="full")
    lags = np.arange(-tx_signal.size + 1, tx_signal.size)
    positive = lags >= 0

    range_m = SPEED_OF_LIGHT_MPS * lags[positive] / (2.0 * sample_rate_hz)
    response = np.abs(correlation[positive])
    peak = float(np.max(response))
    if peak > 0.0:
        response = response / peak
    return range_m, response


def _doppler_spectrum(
    parameters: RadarParameters,
    wavelength_m: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a slow-time Doppler spectrum from packet phase changes."""

    slow_time_s = np.arange(parameters.packets, dtype=float) / parameters.packet_rate_hz

    # Positive velocity means the target moves toward the radar, so range gets
    # smaller and the complex return phase advances from packet to packet.
    range_over_time_m = parameters.initial_range_m - parameters.target_velocity_mps * slow_time_s
    phase_rad = -4.0 * np.pi * range_over_time_m / wavelength_m
    amplitude = 1.0 / (1.0 + parameters.initial_range_m / 8.0) ** 2

    slow_returns = amplitude * np.exp(1j * phase_rad)
    slow_returns += parameters.noise_std * 0.2 * (
        rng.standard_normal(parameters.packets)
        + 1j * rng.standard_normal(parameters.packets)
    )

    window = np.hanning(parameters.packets)
    spectrum = np.fft.fftshift(np.fft.fft(slow_returns * window))
    magnitude = np.abs(spectrum)
    peak = float(np.max(magnitude))
    if peak > 0.0:
        magnitude = magnitude / peak

    frequency_hz = np.fft.fftshift(
        np.fft.fftfreq(parameters.packets, d=1.0 / parameters.packet_rate_hz)
    )
    return frequency_hz, magnitude

