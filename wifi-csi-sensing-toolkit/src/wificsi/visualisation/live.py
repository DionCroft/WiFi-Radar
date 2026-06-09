"""Best-effort live serial visualiser for ESP32-style CSI lines."""

from __future__ import annotations

from collections import deque

import matplotlib.pyplot as plt
import numpy as np

from wificsi.core import UnsupportedFormatError, ensure_complex_matrix


def run_serial_live_plot(port: str, baud: int = 921600, max_packets: int = 300) -> None:
    """Read ESP32-style CSI text lines and update a scrolling amplitude plot."""

    try:
        import serial
    except ImportError as exc:
        raise UnsupportedFormatError(
            "Live serial mode requires pyserial. Install with "
            "`python -m pip install pyserial`."
        ) from exc

    values: deque[np.ndarray] = deque(maxlen=max_packets)
    with serial.Serial(port, baudrate=baud, timeout=1.0) as serial_port:
        fig, ax = plt.subplots(figsize=(9, 4))
        image = None
        plt.ion()

        while plt.fignum_exists(fig.number):
            line = serial_port.readline().decode(errors="ignore").strip()
            vector = _parse_live_line(line)
            if vector is None:
                continue
            values.append(np.abs(vector))
            matrix = np.vstack(values)

            if image is None:
                image = ax.imshow(matrix, aspect="auto", origin="lower")
                ax.set_title("Live ESP32 CSI amplitude")
                ax.set_xlabel("Subcarrier")
                ax.set_ylabel("Recent packet")
                fig.colorbar(image, ax=ax)
            else:
                image.set_data(matrix)
                image.set_clim(float(np.min(matrix)), float(np.max(matrix)))
                ax.set_ylim(0, max(1, matrix.shape[0] - 1))
            plt.pause(0.02)


def _parse_live_line(line: str) -> np.ndarray | None:
    if not line:
        return None
    start = line.find("[")
    end = line.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    numbers = np.fromstring(line[start + 1 : end], sep=",", dtype=float)
    if numbers.size < 2 or numbers.size % 2 != 0:
        return None
    return ensure_complex_matrix(numbers)

