"""Parser for ESP32 CSI CSV lines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


@dataclass(frozen=True)
class CSIRecord:
    """One parsed ESP32 CSI record."""

    timestamp_s: float
    src_mac: str
    rssi: int
    metadata: dict[str, Any]
    csi_complex: np.ndarray
    raw_csi: np.ndarray


class CSIParseError(ValueError):
    """Raised when a CSI line cannot be parsed."""


def parse_csi_line(line: str) -> CSIRecord:
    """Parse one `CSI_DATA,...,[imag0,real0,...]` line.

    ESP-IDF documents classic ESP32 CSI bytes as signed int8 values ordered
    imaginary then real. The raw bytes are preserved, while `csi_complex` is
    exposed as real + j*imag for normal DSP work.
    """

    line = line.strip()
    if not line.startswith("CSI_DATA,"):
        raise CSIParseError("line does not start with CSI_DATA")

    list_start = line.find("[")
    list_end = line.rfind("]")
    if list_start == -1 or list_end == -1 or list_end <= list_start:
        raise CSIParseError("CSI list is missing or malformed")

    prefix = line[:list_start].rstrip(",")
    fields = prefix.split(",")
    if len(fields) != 13:
        raise CSIParseError(f"expected 13 metadata fields, got {len(fields)}")

    raw = np.fromstring(line[list_start + 1 : list_end], sep=",", dtype=np.int16)
    if raw.size < 2:
        raise CSIParseError("CSI vector is empty")
    if raw.size % 2 != 0:
        raw = raw[:-1]

    csi_len = int(fields[12])
    if csi_len != raw.size:
        csi_len = raw.size

    imag = raw[0::2].astype(float)
    real = raw[1::2].astype(float)
    csi_complex = real + 1j * imag

    metadata = {
        "rate": int(fields[4]),
        "sig_mode": int(fields[5]),
        "mcs": int(fields[6]),
        "bandwidth": int(fields[7]),
        "channel": int(fields[8]),
        "secondary_channel": int(fields[9]),
        "noise_floor": int(fields[10]),
        "ant": int(fields[11]),
        "csi_len": csi_len,
        "raw_order": "imag,real",
    }
    return CSIRecord(
        timestamp_s=int(fields[1]) / 1_000_000.0,
        src_mac=fields[2],
        rssi=int(fields[3]),
        metadata=metadata,
        csi_complex=csi_complex,
        raw_csi=raw.astype(np.int8),
    )


def try_parse_csi_line(line: str) -> CSIRecord | None:
    """Parse a line, returning None for malformed records."""

    try:
        return parse_csi_line(line)
    except (CSIParseError, ValueError):
        return None


def record_to_csv_line(record: CSIRecord) -> str:
    """Serialise a CSIRecord back to the stable CSV line format."""

    meta = record.metadata
    raw = ",".join(str(int(value)) for value in record.raw_csi)
    return (
        "CSI_DATA,"
        f"{int(record.timestamp_s * 1_000_000)},"
        f"{record.src_mac},"
        f"{record.rssi},"
        f"{meta.get('rate', 0)},"
        f"{meta.get('sig_mode', 0)},"
        f"{meta.get('mcs', 0)},"
        f"{meta.get('bandwidth', 0)},"
        f"{meta.get('channel', 0)},"
        f"{meta.get('secondary_channel', 0)},"
        f"{meta.get('noise_floor', 0)},"
        f"{meta.get('ant', 0)},"
        f"{len(record.raw_csi)},"
        f"[{raw}]"
    )


def load_records_csv(path: str | Path) -> list[CSIRecord]:
    """Load a raw ESP32 CSI CSV log."""

    records: list[CSIRecord] = []
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            record = try_parse_csi_line(line)
            if record is not None:
                records.append(record)
    return records


def save_records_csv(records: Iterable[CSIRecord], path: str | Path) -> None:
    """Save records as raw CSI CSV lines."""

    with Path(path).open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record_to_csv_line(record) + "\n")


def records_to_matrix(records: list[CSIRecord]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return timestamps, CSI matrix, and RSSI from parsed records."""

    if not records:
        raise ValueError("no CSI records available")
    min_len = min(record.csi_complex.size for record in records)
    timestamps = np.array([record.timestamp_s for record in records], dtype=float)
    timestamps -= timestamps[0]
    csi = np.vstack([record.csi_complex[:min_len] for record in records])
    rssi = np.array([record.rssi for record in records], dtype=float)
    return timestamps, csi, rssi


def save_records_npz(records: list[CSIRecord], path: str | Path) -> None:
    """Save parsed records as a compact NPZ."""

    timestamps, csi, rssi = records_to_matrix(records)
    np.savez_compressed(path, timestamps=timestamps, csi=csi, rssi=rssi)


def generate_synthetic_records(
    seconds: float = 60.0,
    rate_hz: float = 100.0,
    subcarriers: int = 64,
    breathing_hz: float = 0.25,
    seed: int = 5,
) -> list[CSIRecord]:
    """Generate ESP32-like CSI records for tests and demos."""

    rng = np.random.default_rng(seed)
    count = max(2, int(seconds * rate_hz))
    timestamps = np.arange(count) / rate_hz
    sc = np.arange(subcarriers)
    static = 25.0 * np.exp(1j * (0.05 * sc))
    records = []
    for timestamp in timestamps:
        breathing = 3.5 * np.sin(2.0 * np.pi * breathing_hz * timestamp)
        motion = 7.0 * np.sin(2.0 * np.pi * 1.1 * timestamp)
        phase = 0.02 * sc + 0.15 * breathing + 0.02 * motion
        csi = static + 6.0 * np.exp(1j * phase)
        csi += rng.normal(0.0, 0.8, subcarriers) + 1j * rng.normal(0.0, 0.8, subcarriers)
        raw = np.empty(subcarriers * 2, dtype=np.int8)
        raw[0::2] = np.clip(np.round(csi.imag), -128, 127).astype(np.int8)
        raw[1::2] = np.clip(np.round(csi.real), -128, 127).astype(np.int8)
        records.append(
            CSIRecord(
                timestamp_s=float(timestamp),
                src_mac="aa:bb:cc:dd:ee:ff",
                rssi=-42,
                metadata={
                    "rate": 11,
                    "sig_mode": 1,
                    "mcs": 0,
                    "bandwidth": 0,
                    "channel": 6,
                    "secondary_channel": 0,
                    "noise_floor": -96,
                    "ant": 0,
                    "csi_len": int(raw.size),
                    "raw_order": "imag,real",
                },
                csi_complex=csi,
                raw_csi=raw,
            )
        )
    return records

