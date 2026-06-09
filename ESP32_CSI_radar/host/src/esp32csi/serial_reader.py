"""Serial reading and recording helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .parser import try_parse_csi_line


def iter_serial_lines(port: str, baud: int = 921600) -> Iterator[str]:
    """Yield text lines from a serial port."""

    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("pyserial is required: python -m pip install pyserial") from exc

    with serial.Serial(port, baudrate=baud, timeout=1.0) as serial_port:
        while True:
            line = serial_port.readline().decode(errors="replace").strip()
            if line:
                yield line


def record_csv(port: str, baud: int, output: str | Path) -> None:
    """Record parseable CSI lines to a CSV text file."""

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for line in iter_serial_lines(port, baud):
            if try_parse_csi_line(line) is not None:
                handle.write(line + "\n")
                handle.flush()

