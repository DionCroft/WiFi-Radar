"""Intel IWL5300 CSI Tool loader."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wificsi.core import CSIData, UnsupportedFormatError
from wificsi.io.base import optional_import


def load_intel5300(path: str | Path) -> CSIData:
    """Load Intel 5300 CSI using csiread when available."""

    csiread = optional_import(
        "csiread",
        "Install with `python -m pip install csiread`, or convert the capture "
        "to the toolkit NPZ/CSV format.",
    )
    if not hasattr(csiread, "Intel"):
        raise UnsupportedFormatError("Installed csiread does not expose csiread.Intel")

    reader = csiread.Intel(str(path), nrxnum=3, ntxnum=3)
    reader.read()
    csi = np.asarray(reader.get_scaled_csi(), dtype=np.complex128)
    timestamps = np.arange(csi.shape[0], dtype=float)
    return CSIData(
        csi=csi,
        timestamps=timestamps,
        source=f"intel5300:{Path(path).name}",
        metadata={"parser": "csiread.Intel"},
    )

