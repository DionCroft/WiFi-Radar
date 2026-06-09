"""PySide6 user interface for the WiFi radar simulator."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .data_sources import SyntheticRadarSource
from .simulation import RadarParameters, SimulationResult


class MainWindow(QMainWindow):
    """Main desktop window with controls and three educational plots."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("wifi-radar-simulator")
        self.source = SyntheticRadarSource()

        self.range_input = self._make_double_spin_box(1.0, 80.0, 12.0, " m", 0.5)
        self.velocity_input = self._make_double_spin_box(-5.0, 5.0, 1.2, " m/s", 0.1)
        self.noise_input = self._make_double_spin_box(0.0, 0.25, 0.02, "", 0.01)
        self.packet_input = QSpinBox()
        self.packet_input.setRange(128, 2048)
        self.packet_input.setSingleStep(128)
        self.packet_input.setValue(512)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        run_button = QPushButton("Run simulation")
        run_button.clicked.connect(self.update_simulation)

        control_panel = self._build_control_panel(run_button)
        plot_panel = self._build_plot_panel()

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(control_panel)
        layout.addWidget(plot_panel, stretch=1)
        self.setCentralWidget(root)

        self.update_simulation()

    def _build_control_panel(self, run_button: QPushButton) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFixedWidth(290)

        title = QLabel("WiFi Radar Controls")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        subtitle = QLabel(
            "Synthetic baseband model for transmitter, moving target, and echo."
        )
        subtitle.setWordWrap(True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow("Target range", self.range_input)
        form.addRow("Target velocity", self.velocity_input)
        form.addRow("Noise level", self.noise_input)
        form.addRow("Doppler packets", self.packet_input)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(run_button)
        layout.addSpacing(8)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        return panel

    def _build_plot_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(8, 6), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        return panel

    def update_simulation(self) -> None:
        parameters = RadarParameters(
            initial_range_m=self.range_input.value(),
            target_velocity_mps=self.velocity_input.value(),
            noise_std=self.noise_input.value(),
            packets=self.packet_input.value(),
        )
        result = self.source.run(parameters)
        self._draw_result(result)
        self.status_label.setText(
            "Round-trip delay: "
            f"{result.expected_delay_s * 1e9:.1f} ns\n"
            "Expected Doppler: "
            f"{result.expected_doppler_hz:.1f} Hz\n"
            "Range resolution: "
            f"{result.range_resolution_m:.2f} m"
        )

    def _draw_result(self, result: SimulationResult) -> None:
        self.figure.clear()
        time_axis_us = result.time_s * 1e6

        time_ax = self.figure.add_subplot(3, 1, 1)
        time_ax.plot(
            time_axis_us,
            self._normalize(result.tx_signal.real),
            label="Transmitted probe",
            linewidth=1.1,
        )
        time_ax.plot(
            time_axis_us,
            self._normalize(result.rx_signal.real),
            label="Reflected signal",
            linewidth=1.1,
            alpha=0.85,
        )
        time_ax.set_title("Time-domain baseband signal")
        time_ax.set_xlabel("Time (microseconds)")
        time_ax.set_ylabel("Normalized amplitude")
        time_ax.grid(True, alpha=0.25)
        time_ax.legend(loc="upper right")

        doppler_ax = self.figure.add_subplot(3, 1, 2)
        doppler_db = 20.0 * np.log10(result.doppler_spectrum + 1e-12)
        doppler_ax.plot(result.doppler_hz, doppler_db, color="#2563eb", linewidth=1.2)
        doppler_ax.axvline(
            result.expected_doppler_hz,
            color="#b91c1c",
            linestyle="--",
            linewidth=1.0,
            label="Expected shift",
        )
        doppler_ax.set_title("Doppler spectrum from packet-to-packet phase")
        doppler_ax.set_xlabel("Frequency shift (Hz)")
        doppler_ax.set_ylabel("Magnitude (dB)")
        doppler_ax.grid(True, alpha=0.25)
        doppler_ax.legend(loc="upper right")

        range_ax = self.figure.add_subplot(3, 1, 3)
        range_ax.plot(
            result.range_m,
            result.range_response,
            color="#047857",
            linewidth=1.2,
        )
        range_ax.axvline(
            result.expected_range_m,
            color="#b91c1c",
            linestyle="--",
            linewidth=1.0,
            label="Target range",
        )
        range_ax.set_xlim(0, min(80, max(20, result.expected_range_m + 20)))
        range_ax.set_title("Range-like matched-filter response")
        range_ax.set_xlabel("Range (m)")
        range_ax.set_ylabel("Normalized response")
        range_ax.grid(True, alpha=0.25)
        range_ax.legend(loc="upper right")

        self.canvas.draw_idle()

    @staticmethod
    def _make_double_spin_box(
        minimum: float,
        maximum: float,
        value: float,
        suffix: str,
        step: float,
    ) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setSingleStep(step)
        box.setDecimals(2)
        box.setSuffix(suffix)
        return box

    @staticmethod
    def _normalize(values: np.ndarray) -> np.ndarray:
        peak = float(np.max(np.abs(values)))
        if peak == 0.0:
            return values
        return values / peak

