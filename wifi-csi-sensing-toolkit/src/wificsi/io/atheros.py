"""Atheros QCA9300 / AR9300 CSI loader."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wificsi.core import CSIData, UnsupportedFormatError
from wificsi.io.base import optional_import


def load_atheros(path: str | Path) -> CSIData:
    """Load Atheros CSI using csiread when available."""

    csiread = optional_import(
        "csiread",
        "Install with `python -m pip install csiread`, or convert the capture "
        "to the toolkit NPZ/CSV format.",
    )
    if not hasattr(csiread, "Atheros"):
        raise UnsupportedFormatError("Installed csiread does not expose csiread.Atheros")

    reader = csiread.Atheros(str(path))
    reader.read()
    csi = np.asarray(reader.csi, dtype=np.complex128)
    timestamps = np.arange(csi.shape[0], dtype=float)
    return CSIData(
        csi=csi,
        timestamps=timestamps,
        source=f"atheros:{Path(path).name}",
        metadata={"parser": "csiread.Atheros"},
    )

