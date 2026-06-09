"""Tests for generic CSV and ESP32 parsing."""

from pathlib import Path

from wificsi.io.esp32 import load_esp32_csv
from wificsi.io.generic_csv import load_generic_csv


def test_generic_csv_list_column(tmp_path: Path) -> None:
    path = tmp_path / "generic.csv"
    path.write_text(
        'timestamp,csi\n0.0,"[1, 0, 0, 1]"\n0.1,"[0, 1, 1, 0]"\n',
        encoding="utf-8",
    )

    data = load_generic_csv(path)

    assert data.csi.shape == (2, 2, 1, 1)
    assert data.csi[0, 1, 0, 0] == 1j


def test_esp32_csv_uses_generic_loader(tmp_path: Path) -> None:
    path = tmp_path / "esp32.csv"
    path.write_text(
        'timestamp,csi\n0,"[1, -1, 2, -2]"\n10,"[3, -3, 4, -4]"\n',
        encoding="utf-8",
    )

    data = load_esp32_csv(path)

    assert data.source == "esp32:esp32.csv"
    assert data.timestamps[1] == 10.0
    assert data.csi.shape == (2, 2, 1, 1)

