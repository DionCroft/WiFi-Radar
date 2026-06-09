"""Basic tests for the numerical simulator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wifi_radar_simulator.simulation import RadarParameters, simulate


class SimulationTests(unittest.TestCase):
    def test_result_arrays_have_expected_shapes(self) -> None:
        parameters = RadarParameters(packets=256)
        result = simulate(parameters)

        self.assertEqual(result.time_s.shape, result.tx_signal.shape)
        self.assertEqual(result.time_s.shape, result.rx_signal.shape)
        self.assertEqual(result.doppler_hz.shape, result.doppler_spectrum.shape)
        self.assertEqual(result.doppler_hz.size, parameters.packets)
        self.assertEqual(result.range_m.shape, result.range_response.shape)

    def test_range_peak_is_near_target_range(self) -> None:
        parameters = RadarParameters(initial_range_m=15.0, noise_std=0.0)
        result = simulate(parameters)

        peak_index = int(result.range_response.argmax())
        measured_range_m = float(result.range_m[peak_index])

        self.assertLess(abs(measured_range_m - parameters.initial_range_m), 2.0)

    def test_doppler_peak_tracks_target_velocity(self) -> None:
        parameters = RadarParameters(target_velocity_mps=1.0, noise_std=0.0, packets=1024)
        result = simulate(parameters)

        peak_index = int(result.doppler_spectrum.argmax())
        measured_doppler_hz = float(result.doppler_hz[peak_index])
        frequency_bin_hz = parameters.packet_rate_hz / parameters.packets

        self.assertLess(
            abs(measured_doppler_hz - result.expected_doppler_hz),
            2.0 * frequency_bin_hz,
        )

    def test_invalid_range_is_rejected(self) -> None:
        parameters = RadarParameters(initial_range_m=0.0)

        with self.assertRaises(ValueError):
            simulate(parameters)


if __name__ == "__main__":
    unittest.main()

