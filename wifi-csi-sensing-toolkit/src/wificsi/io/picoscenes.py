"""PicoScenes CSI loader."""

from __future__ import annotations

from pathlib import Path

from wificsi.core import CSIData, UnsupportedFormatError
from wificsi.io.base import optional_import


def load_picoscenes(path: str | Path) -> CSIData:
    """Load PicoScenes files when supported by installed Python tooling."""

    optional_import(
        "csiread",
        "Install with `python -m pip install csiread`. PicoScenes file support "
        "varies by version; NPZ or CSV export is recommended if parsing fails.",
    )
    raise UnsupportedFormatError(
        "Direct PicoScenes parsing is not available in this lightweight loader. "
        "Export PicoScenes CSI to CSV/NPZ, then use `--format csv` or `--format npz`."
    )

