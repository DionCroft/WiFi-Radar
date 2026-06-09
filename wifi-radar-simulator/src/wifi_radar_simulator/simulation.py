"""Numerical model for the educational WiFi radar simulator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .calibration import (
    apply_slow_time_window,
    remove_static_background,
    unwrap_csi_phase,
)

SPEED_OF_LIGHT_MPS = 299_792_458.0


@dataclass(frozen=True)
class RadarTarget:
    """A simple point target in the radar scene.

    ``range_m`` is the one-way distance to the target. ``velocity_mps`` is
    positive when the target moves toward the transmitter/receiver. ``strength``
    is a display-friendly reflection coefficient, not a calibrated radar cross
    section.
    """

    range_m: float
    velocity_mps: float
    strength: float = 1.0


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
    target_strength: float = 1.0
    targets: tuple[RadarTarget, ...] = ()
    multipath_strength: float = 0.18
    static_clutter_strength: float = 0.12
    noise_std: float = 0.02
    csi_subcarriers: int = 52
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
    csi_subcarriers: np.ndarray
    csi_matrix: np.ndarray
    csi_amplitude: np.ndarray
    csi_phase: np.ndarray
    expected_delay_s: float
    expected_doppler_hz: float
    expected_range_m: float
    range_resolution_m: float
    targets: tuple[RadarTarget, ...]
    source_name: str = "Synthetic scene"


def simulate(parameters: RadarParameters) -> SimulationResult:
    """Run the synthetic radar model.

    The model has three teaching views:

    1. Fast time: one short transmitted probe is delayed and attenuated to model
       echoes from targets, multipath, and static clutter.
    2. Slow time: many packet returns show Doppler as phase rotation from packet
       to packet.
    3. CSI/OFDM: each subcarrier sees a different phase slope when echoes are
       delayed, which is the core measurement used in many WiFi radar papers.
    """

    _validate_parameters(parameters)

    rng = np.random.default_rng(parameters.seed)
    targets = _resolve_targets(parameters)
    primary_target = max(targets, key=lambda target: target.strength)

    time_s = _sample_times(parameters)
    tx_signal = _baseband_chirp(time_s, parameters.bandwidth_hz, parameters.packet_duration_s)

    wavelength_m = SPEED_OF_LIGHT_MPS / parameters.carrier_frequency_hz
    expected_delay_s = 2.0 * primary_target.range_m / SPEED_OF_LIGHT_MPS
    expected_doppler_hz = 2.0 * primary_target.velocity_mps / wavelength_m

    rx_signal = _reflected_packet(
        tx_signal=tx_signal,
        time_s=time_s,
        targets=targets,
        parameters=parameters,
        rng=rng,
    )

    range_m, range_response = _range_response(
        tx_signal=tx_signal,
        rx_signal=rx_signal,
        sample_rate_hz=parameters.sample_rate_hz,
    )
    doppler_hz, doppler_spectrum = _doppler_spectrum(parameters, wavelength_m, targets, rng)
    csi_subcarriers, csi_matrix = _synthetic_csi(parameters, wavelength_m, targets, rng)

    csi_without_static = remove_static_background(csi_matrix)
    csi_amplitude = np.abs(csi_without_static)
    csi_phase = unwrap_csi_phase(csi_without_static)
    range_resolution_m = SPEED_OF_LIGHT_MPS / (2.0 * parameters.bandwidth_hz)

    return SimulationResult(
        time_s=time_s,
        tx_signal=tx_signal,
        rx_signal=rx_signal,
        doppler_hz=doppler_hz,
        doppler_spectrum=doppler_spectrum,
        range_m=range_m,
        range_response=range_response,
        csi_subcarriers=csi_subcarriers,
        csi_matrix=csi_matrix,
        csi_amplitude=csi_amplitude,
        csi_phase=csi_phase,
        expected_delay_s=expected_delay_s,
        expected_doppler_hz=expected_doppler_hz,
        expected_range_m=primary_target.range_m,
        range_resolution_m=range_resolution_m,
        targets=targets,
    )


def build_result_from_csi(
    csi_matrix: np.ndarray,
    subcarriers: np.ndarray,
    parameters: RadarParameters,
    source_name: str,
) -> SimulationResult:
    """Adapt a recorded CSI matrix to the simulator result structure.

    A real CSI file does not contain a known transmit chirp, so the time-domain
    fields become packet-average CSI traces. The Doppler and range-like views are
    still useful teaching plots: FFT across packets estimates Doppler, while IFFT
    across subcarriers shows delay-like structure.
    """

    _validate_parameters(parameters)
    if csi_matrix.ndim != 2:
        raise ValueError("csi_matrix must be a 2-D packets x subcarriers array")
    if csi_matrix.shape[1] != subcarriers.size:
        raise ValueError("subcarrier count must match csi_matrix columns")

    csi_without_static = remove_static_background(csi_matrix)
    csi_windowed = apply_slow_time_window(csi_without_static)
    csi_amplitude = np.abs(csi_without_static)
    csi_phase = unwrap_csi_phase(csi_without_static)

    packet_count = csi_matrix.shape[0]
    time_s = np.arange(packet_count, dtype=float) / parameters.packet_rate_hz
    rx_signal = np.mean(csi_without_static, axis=1)
    tx_signal = np.ones_like(rx_signal)

    doppler_hz = np.fft.fftshift(
        np.fft.fftfreq(packet_count, d=1.0 / parameters.packet_rate_hz)
    )
    doppler_spectrum = np.abs(np.fft.fftshift(np.fft.fft(np.mean(csi_windowed, axis=1))))
    doppler_spectrum = _normalize(doppler_spectrum)

    range_profile = np.mean(np.abs(np.fft.ifft(csi_without_static, axis=1)), axis=0)
    range_response = _normalize(range_profile)
    range_m = (
        np.arange(subcarriers.size, dtype=float)
        * SPEED_OF_LIGHT_MPS
        / (2.0 * parameters.bandwidth_hz)
    )

    targets = _resolve_targets(parameters)
    primary_target = max(targets, key=lambda target: target.strength)

    return SimulationResult(
        time_s=time_s,
        tx_signal=tx_signal,
        rx_signal=rx_signal,
        doppler_hz=doppler_hz,
        doppler_spectrum=doppler_spectrum,
        range_m=range_m,
        range_response=range_response,
        csi_subcarriers=subcarriers,
        csi_matrix=csi_matrix,
        csi_amplitude=csi_amplitude,
        csi_phase=csi_phase,
        expected_delay_s=2.0 * primary_target.range_m / SPEED_OF_LIGHT_MPS,
        expected_doppler_hz=(
            2.0
            * primary_target.velocity_mps
            / (SPEED_OF_LIGHT_MPS / parameters.carrier_frequency_hz)
        ),
        expected_range_m=primary_target.range_m,
        range_resolution_m=SPEED_OF_LIGHT_MPS / (2.0 * parameters.bandwidth_hz),
        targets=targets,
        source_name=source_name,
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
    if parameters.target_strength < 0:
        raise ValueError("target_strength must be non-negative")
    if parameters.multipath_strength < 0:
        raise ValueError("multipath_strength must be non-negative")
    if parameters.static_clutter_strength < 0:
        raise ValueError("static_clutter_strength must be non-negative")
    if parameters.noise_std < 0:
        raise ValueError("noise_std must be non-negative")
    if parameters.csi_subcarriers < 8:
        raise ValueError("csi_subcarriers must be at least 8")
    for target in parameters.targets:
        if target.range_m <= 0:
            raise ValueError("target range_m must be positive")
        if target.strength < 0:
            raise ValueError("target strength must be non-negative")


def _resolve_targets(parameters: RadarParameters) -> tuple[RadarTarget, ...]:
    targets = parameters.targets or (
        RadarTarget(
            range_m=parameters.initial_range_m,
            velocity_mps=parameters.target_velocity_mps,
            strength=parameters.target_strength,
        ),
    )
    active_targets = tuple(target for target in targets if target.strength > 0.0)
    if not active_targets:
        raise ValueError("at least one target must have positive strength")
    return active_targets


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
    targets: tuple[RadarTarget, ...],
    parameters: RadarParameters,
    rng: np.random.Generator,
) -> np.ndarray:
    """Delay and Doppler-shift the transmitted packet to make echoes."""

    echo = np.zeros_like(tx_signal, dtype=complex)
    wavelength_m = SPEED_OF_LIGHT_MPS / parameters.carrier_frequency_hz

    for target in targets:
        echo += _target_echo(
            tx_signal=tx_signal,
            time_s=time_s,
            range_m=target.range_m,
            velocity_mps=target.velocity_mps,
            strength=target.strength,
            sample_rate_hz=parameters.sample_rate_hz,
            wavelength_m=wavelength_m,
        )

        # Multipath is modeled as weaker delayed copies caused by reflections
        # from walls, desks, or other objects before the signal reaches us.
        if parameters.multipath_strength > 0.0:
            echo += _target_echo(
                tx_signal=tx_signal,
                time_s=time_s,
                range_m=target.range_m + 4.0,
                velocity_mps=target.velocity_mps * 0.85,
                strength=target.strength * parameters.multipath_strength,
                sample_rate_hz=parameters.sample_rate_hz,
                wavelength_m=wavelength_m,
            )
            echo += _target_echo(
                tx_signal=tx_signal,
                time_s=time_s,
                range_m=target.range_m + 9.0,
                velocity_mps=target.velocity_mps * 0.5,
                strength=target.strength * parameters.multipath_strength * 0.55,
                sample_rate_hz=parameters.sample_rate_hz,
                wavelength_m=wavelength_m,
            )

    if parameters.static_clutter_strength > 0.0:
        for clutter_range_m, clutter_gain in ((3.5, 1.0), (7.0, 0.65), (18.0, 0.4)):
            echo += _target_echo(
                tx_signal=tx_signal,
                time_s=time_s,
                range_m=clutter_range_m,
                velocity_mps=0.0,
                strength=parameters.static_clutter_strength * clutter_gain,
                sample_rate_hz=parameters.sample_rate_hz,
                wavelength_m=wavelength_m,
            )

    noise = parameters.noise_std * (
        rng.standard_normal(tx_signal.size) + 1j * rng.standard_normal(tx_signal.size)
    )
    return echo + noise


def _target_echo(
    tx_signal: np.ndarray,
    time_s: np.ndarray,
    range_m: float,
    velocity_mps: float,
    strength: float,
    sample_rate_hz: float,
    wavelength_m: float,
) -> np.ndarray:
    delay_s = 2.0 * range_m / SPEED_OF_LIGHT_MPS
    doppler_hz = 2.0 * velocity_mps / wavelength_m
    delayed = _fractional_delay(tx_signal, delay_s * sample_rate_hz)

    # Echoes get weaker with distance. This display-oriented scaling keeps
    # targets visible while still showing why far targets are harder to detect.
    attenuation = strength / (1.0 + range_m / 8.0) ** 2
    doppler_phase = np.exp(1j * 2.0 * np.pi * doppler_hz * time_s)
    return attenuation * delayed * doppler_phase


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
    response = _normalize(np.abs(correlation[positive]))
    return range_m, response


def _doppler_spectrum(
    parameters: RadarParameters,
    wavelength_m: float,
    targets: tuple[RadarTarget, ...],
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a slow-time Doppler spectrum from packet phase changes."""

    slow_time_s = np.arange(parameters.packets, dtype=float) / parameters.packet_rate_hz
    slow_returns = np.zeros(parameters.packets, dtype=complex)

    for target in targets:
        slow_returns += _slow_time_return(
            range_m=target.range_m,
            velocity_mps=target.velocity_mps,
            strength=target.strength,
            slow_time_s=slow_time_s,
            wavelength_m=wavelength_m,
        )
        if parameters.multipath_strength > 0.0:
            slow_returns += _slow_time_return(
                range_m=target.range_m + 4.0,
                velocity_mps=target.velocity_mps * 0.85,
                strength=target.strength * parameters.multipath_strength,
                slow_time_s=slow_time_s,
                wavelength_m=wavelength_m,
            )

    if parameters.static_clutter_strength > 0.0:
        slow_returns += parameters.static_clutter_strength * np.ones_like(slow_returns)

    slow_returns += parameters.noise_std * 0.2 * (
        rng.standard_normal(parameters.packets)
        + 1j * rng.standard_normal(parameters.packets)
    )

    windowed = apply_slow_time_window(slow_returns)
    spectrum = np.fft.fftshift(np.fft.fft(windowed))
    magnitude = _normalize(np.abs(spectrum))

    frequency_hz = np.fft.fftshift(
        np.fft.fftfreq(parameters.packets, d=1.0 / parameters.packet_rate_hz)
    )
    return frequency_hz, magnitude


def _slow_time_return(
    range_m: float,
    velocity_mps: float,
    strength: float,
    slow_time_s: np.ndarray,
    wavelength_m: float,
) -> np.ndarray:
    # Positive velocity means the target moves toward the radar, so range gets
    # smaller and the complex return phase advances from packet to packet.
    range_over_time_m = range_m - velocity_mps * slow_time_s
    phase_rad = -4.0 * np.pi * range_over_time_m / wavelength_m
    amplitude = strength / (1.0 + range_m / 8.0) ** 2
    return amplitude * np.exp(1j * phase_rad)


def _synthetic_csi(
    parameters: RadarParameters,
    wavelength_m: float,
    targets: tuple[RadarTarget, ...],
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Create packets x subcarriers CSI for the synthetic scene."""

    subcarriers = _wifi_subcarrier_indices(parameters.csi_subcarriers)
    subcarrier_spacing_hz = parameters.bandwidth_hz / 64.0
    frequency_offsets_hz = subcarriers * subcarrier_spacing_hz
    slow_time_s = np.arange(parameters.packets, dtype=float) / parameters.packet_rate_hz
    csi = np.zeros((parameters.packets, subcarriers.size), dtype=complex)

    for target in targets:
        csi += _csi_path(
            range_m=target.range_m,
            velocity_mps=target.velocity_mps,
            strength=target.strength,
            slow_time_s=slow_time_s,
            frequency_offsets_hz=frequency_offsets_hz,
            wavelength_m=wavelength_m,
        )

        if parameters.multipath_strength > 0.0:
            csi += _csi_path(
                range_m=target.range_m + 4.0,
                velocity_mps=target.velocity_mps * 0.85,
                strength=target.strength * parameters.multipath_strength,
                slow_time_s=slow_time_s,
                frequency_offsets_hz=frequency_offsets_hz,
                wavelength_m=wavelength_m,
            )
            csi += _csi_path(
                range_m=target.range_m + 9.0,
                velocity_mps=target.velocity_mps * 0.5,
                strength=target.strength * parameters.multipath_strength * 0.55,
                slow_time_s=slow_time_s,
                frequency_offsets_hz=frequency_offsets_hz,
                wavelength_m=wavelength_m,
            )

    if parameters.static_clutter_strength > 0.0:
        for clutter_range_m, clutter_gain in ((3.5, 1.0), (7.0, 0.65), (18.0, 0.4)):
            csi += _csi_path(
                range_m=clutter_range_m,
                velocity_mps=0.0,
                strength=parameters.static_clutter_strength * clutter_gain,
                slow_time_s=slow_time_s,
                frequency_offsets_hz=frequency_offsets_hz,
                wavelength_m=wavelength_m,
            )

    noise = parameters.noise_std * 0.08 * (
        rng.standard_normal(csi.shape) + 1j * rng.standard_normal(csi.shape)
    )
    return subcarriers, csi + noise


def _csi_path(
    range_m: float,
    velocity_mps: float,
    strength: float,
    slow_time_s: np.ndarray,
    frequency_offsets_hz: np.ndarray,
    wavelength_m: float,
) -> np.ndarray:
    range_over_time_m = range_m - velocity_mps * slow_time_s
    delay_s = 2.0 * range_over_time_m[:, np.newaxis] / SPEED_OF_LIGHT_MPS
    doppler_phase = -4.0 * np.pi * range_over_time_m[:, np.newaxis] / wavelength_m
    subcarrier_phase = -2.0 * np.pi * delay_s * frequency_offsets_hz[np.newaxis, :]
    amplitude = strength / (1.0 + range_m / 8.0) ** 2
    return amplitude * np.exp(1j * (doppler_phase + subcarrier_phase))


def _wifi_subcarrier_indices(count: int) -> np.ndarray:
    """Return centered OFDM subcarrier numbers with the DC bin removed."""

    half = count // 2
    negative = np.arange(-half, 0)
    positive = np.arange(1, count - half + 1)
    return np.concatenate((negative, positive)).astype(float)


def _normalize(values: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(values))) if values.size else 0.0
    if peak == 0.0:
        return values
    return values / peak

