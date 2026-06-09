"""Loader dispatch for CSI sources."""

from __future__ import annotations

from pathlib import Path

from wificsi.core import CSIData, UnsupportedFormatError, load_npz


def load_csi(path: str | Path, fmt: str) -> CSIData:
    """Load a CSI file by format name."""

    fmt = fmt.lower().replace("-", "").replace("_", "")
    path = Path(path)

    if fmt == "npz":
        return load_npz(path)
    if fmt in {"csv", "genericcsv"}:
        from .generic_csv import load_generic_csv

        return load_generic_csv(path)
    if fmt == "esp32":
        from .esp32 import load_esp32_csv

        return load_esp32_csv(path)
    if fmt in {"intel5300", "iwl5300"}:
        from .intel5300 import load_intel5300

        return load_intel5300(path)
    if fmt in {"picoscenes", "pico"}:
        from .picoscenes import load_picoscenes

        return load_picoscenes(path)
    if fmt in {"atheros", "qca9300", "ar9300"}:
        from .atheros import load_atheros

        return load_atheros(path)
    if fmt in {"nexmon", "pcap"}:
        from .nexmon import load_nexmon

        return load_nexmon(path)

    raise UnsupportedFormatError(f"Unsupported CSI format: {fmt}")


def optional_import(module_name: str, install_hint: str):
    """Import an optional dependency with user-friendly guidance."""

    try:
        return __import__(module_name)
    except ImportError as exc:
        raise UnsupportedFormatError(
            f"Optional dependency '{module_name}' is required. {install_hint}"
        ) from exc

