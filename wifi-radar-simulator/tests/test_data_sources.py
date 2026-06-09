"""Tests for CSI and SDR data source adapters."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wifi_radar_simulator.data_sources import (
    CsiFileSource,
    SdrCaptureSource,
    load_csi_csv,
)
from wifi_radar_simulator.simulation import RadarParameters


class DataSourceTests(unittest.TestCase):
    def test_csi_csv_loader_pivots_long_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "capture.csv"
            path.write_text(
                "\n".join(
                    [
                        "packet,subcarrier,real,imag",
                        "0,-1,1.0,0.0",
                        "0,1,0.0,1.0",
                        "1,-1,0.5,0.5",
                        "1,1,-1.0,0.0",
                    ]
                ),
                encoding="utf-8",
            )

            csi_matrix, subcarriers = load_csi_csv(path)

        self.assertTrue(np.allclose(subcarriers, [-1.0, 1.0]))
        self.assertEqual(csi_matrix.shape, (2, 2))
        self.assertEqual(csi_matrix[0, 1], 1j)

    def test_csi_file_source_returns_simulation_result(self) -> None:
        rows = ["packet,subcarrier,real,imag"]
        for packet in range(8):
            for subcarrier in (-2, -1, 1, 2):
                rows.append(f"{packet},{subcarrier},{1.0 + packet * 0.1},0.1")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "capture.csv"
            path.write_text("\n".join(rows), encoding="utf-8")

            result = CsiFileSource(path).run(RadarParameters(packets=8))

        self.assertEqual(result.source_name, "CSI file: capture.csv")
        self.assertEqual(result.csi_matrix.shape, (8, 4))
        self.assertEqual(result.doppler_hz.size, 8)

    def test_sdr_source_requires_backend(self) -> None:
        with self.assertRaises(RuntimeError):
            SdrCaptureSource().run(RadarParameters())


if __name__ == "__main__":
    unittest.main()

