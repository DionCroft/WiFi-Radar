"""Broadcom Nexmon CSI PCAP loader."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wificsi.core import CSIData, UnsupportedFormatError
from wificsi.io.base import optional_import


def load_nexmon(path: str | Path) -> CSIData:
    """Load Nexmon CSI PCAP using csiread when available."""

    csiread = optional_import(
        "csiread",
        "Install with `python -m pip install csiread`. Some Nexmon PCAP workflows "
        "also need scapy for packet inspection.",
    )
    if not hasattr(csiread, "Nexmon"):
        raise UnsupportedFormatError("Installed csiread does not expose csiread.Nexmon")

    reader = csiread.Nexmon(str(path))
    reader.read()
    csi = np.asarray(reader.csi, dtype=np.complex128)
    timestamps = np.arange(csi.shape[0], dtype=float)
    return CSIData(
        csi=csi,
        timestamps=timestamps,
        source=f"nexmon:{Path(path).name}",
        metadata={"parser": "csiread.Nexmon"},
    )

