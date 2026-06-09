"""ESP32 CSI CSV loader."""

from __future__ import annotations

from pathlib import Path

from wificsi.core import CSIData
from wificsi.io.generic_csv import load_generic_csv


def load_esp32_csv(path: str | Path) -> CSIData:
    """Load ESP32 CSI CSV logs with interleaved real/imag vectors."""

    data = load_generic_csv(path)
    return data.copy_with(
        source=f"esp32:{Path(path).name}",
        metadata={**data.metadata, "format": "esp32"},
    )

