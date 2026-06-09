"""Parser tests for ESP32 CSI records."""

import numpy as np

from esp32csi.parser import generate_synthetic_records, parse_csi_line, record_to_csv_line


def test_parse_csi_line_converts_imag_real_to_complex() -> None:
    line = "CSI_DATA,100000,aa:bb:cc:dd:ee:ff,-40,11,1,0,0,6,0,-96,0,4,[2,1,4,3]"

    record = parse_csi_line(line)

    assert record.timestamp_s == 0.1
    assert record.src_mac == "aa:bb:cc:dd:ee:ff"
    assert np.allclose(record.csi_complex, [1 + 2j, 3 + 4j])
    assert record.metadata["raw_order"] == "imag,real"


def test_record_round_trip() -> None:
    record = generate_synthetic_records(seconds=0.1, rate_hz=10, subcarriers=4)[0]

    parsed = parse_csi_line(record_to_csv_line(record))

    assert parsed.raw_csi.size == 8
    assert parsed.csi_complex.size == 4

