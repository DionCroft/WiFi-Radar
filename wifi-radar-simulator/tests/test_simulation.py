"""Basic tests for the numerical simulator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wifi_radar_simulator.calibration import (
    apply_slow_time_window,
    remove_static_background,
    unwrap_csi_phase,
)
from wifi_radar_simulator.simulation import RadarParameters, RadarTarget, simulate


class SimulationTests(unittest.TestCase):
    def test_result_arrays_have_expected_shapes(self) -> None:
        parameters = RadarParameters(packets=256)
        result = simulate(parameters)

        self.assertEqual(result.time_s.shape, result.tx_signal.shape)
        self.assertEqual(result.time_s.shape, result.rx_signal.shape)
        self.assertEqual(result.doppler_hz.shape, result.doppler_spectrum.shape)
        self.assertEqual(result.doppler_hz.size, parameters.packets)
        self.assertEqual(result.range_m.shape, result.range_response.shape)
        self.assertEqual(result.csi_matrix.shape[0], parameters.packets)
        self.assertEqual(result.csi_matrix.shape, result.csi_amplitude.shape)
        self.assertEqual(result.csi_matrix.shape, result.csi_phase.shape)

    def test_range_peak_is_near_target_range(self) -> None:
        parameters = RadarParameters(
            initial_range_m=15.0,
            multipath_strength=0.0,
            static_clutter_strength=0.0,
            noise_std=0.0,
        )
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

    def test_multiple_targets_are_reported(self) -> None:
        targets = (
            RadarTarget(range_m=10.0, velocity_mps=0.5, strength=0.4),
            RadarTarget(range_m=24.0, velocity_mps=-0.8, strength=1.0),
        )
        result = simulate(
            RadarParameters(
                targets=targets,
                multipath_strength=0.0,
                static_clutter_strength=0.0,
                noise_std=0.0,
            )
        )

        self.assertEqual(result.targets, targets)
        self.assertEqual(result.expected_range_m, 24.0)

    def test_calibration_helpers_keep_expected_shapes(self) -> None:
        csi = np.array(
            [
                [1.0 + 0.0j, -1.0 + 0.0j],
                [0.0 + 1.0j, 0.0 - 1.0j],
                [1.0 + 0.0j, -1.0 + 0.0j],
            ]
        )

        static_removed = remove_static_background(csi)
        phase = unwrap_csi_phase(csi)
        windowed = apply_slow_time_window(csi)

        self.assertEqual(static_removed.shape, csi.shape)
        self.assertEqual(phase.shape, csi.shape)
        self.assertEqual(windowed.shape, csi.shape)
        self.assertTrue(np.allclose(static_removed.mean(axis=0), 0.0))


if __name__ == "__main__":
    unittest.main()
