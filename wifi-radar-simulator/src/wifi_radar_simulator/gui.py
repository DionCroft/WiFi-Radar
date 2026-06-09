"""PySide6 user interface for the WiFi radar simulator."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .data_sources import CsiFileSource, RadarDataSource, SyntheticRadarSource
from .simulation import RadarParameters, RadarTarget, SimulationResult


class MainWindow(QMainWindow):
    """Main desktop window with controls and educational plots."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("wifi-radar-simulator")
        self.source: RadarDataSource = SyntheticRadarSource()

        self.target_inputs = [
            self._make_target_inputs(12.0, 1.2, 1.0),
            self._make_target_inputs(23.0, -0.6, 0.45),
            self._make_target_inputs(38.0, 0.25, 0.25),
        ]
        self.multipath_input = self._make_double_spin_box(0.0, 1.0, 0.18, "", 0.02)
        self.clutter_input = self._make_double_spin_box(0.0, 1.0, 0.12, "", 0.02)
        self.noise_input = self._make_double_spin_box(0.0, 0.25, 0.02, "", 0.01)
        self.packet_input = QSpinBox()
        self.packet_input.setRange(128, 2048)
        self.packet_input.setSingleStep(128)
        self.packet_input.setValue(512)

        self.source_label = QLabel("Source: Synthetic scene")
        self.source_label.setWordWrap(True)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        run_button = QPushButton("Run")
        run_button.clicked.connect(self.update_simulation)

        synthetic_button = QPushButton("Synthetic")
        synthetic_button.clicked.connect(self.use_synthetic_source)

        csi_button = QPushButton("Load CSI CSV")
        csi_button.clicked.connect(self.load_csi_file)

        control_panel = self._build_control_panel(run_button, synthetic_button, csi_button)
        plot_panel = self._build_plot_panel()

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(control_panel)
        layout.addWidget(plot_panel, stretch=1)
        self.setCentralWidget(root)

        self.update_simulation()

    def _build_control_panel(
        self,
        run_button: QPushButton,
        synthetic_button: QPushButton,
        csi_button: QPushButton,
    ) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(360)

        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)

        title = QLabel("WiFi Radar Controls")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        source_buttons = QHBoxLayout()
        source_buttons.addWidget(synthetic_button)
        source_buttons.addWidget(csi_button)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addLayout(source_buttons)
        layout.addWidget(self.source_label)

        for index, inputs in enumerate(self.target_inputs, start=1):
            layout.addWidget(self._build_target_group(index, inputs))

        scene_group = QGroupBox("Scene")
        scene_form = QFormLayout(scene_group)
        scene_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        scene_form.addRow("Multipath", self.multipath_input)
        scene_form.addRow("Static clutter", self.clutter_input)
        scene_form.addRow("Noise", self.noise_input)
        scene_form.addRow("Packets", self.packet_input)
        layout.addWidget(scene_group)

        layout.addWidget(run_button)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        scroll.setWidget(panel)
        return scroll

    def _build_target_group(
        self,
        index: int,
        inputs: tuple[QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox],
    ) -> QGroupBox:
        range_input, velocity_input, strength_input = inputs
        group = QGroupBox(f"Target {index}")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow("Range", range_input)
        form.addRow("Velocity", velocity_input)
        form.addRow("Strength", strength_input)
        return group

    def _build_plot_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(9, 8), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        return panel

    def use_synthetic_source(self) -> None:
        self.source = SyntheticRadarSource()
        self.source_label.setText("Source: Synthetic scene")
        self.update_simulation()

    def load_csi_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load CSI CSV",
            "",
            "CSV files (*.csv);;All files (*.*)",
        )
        if not path:
            return
        self.source = CsiFileSource(path)
        self.source_label.setText(f"Source: {self.source.name}")
        self.update_simulation()

    def update_simulation(self) -> None:
        parameters = self._parameters_from_controls()
        try:
            result = self.source.run(parameters)
        except Exception as exc:
            QMessageBox.warning(self, "Simulation error", str(exc))
            return

        self._draw_result(result)
        target_count = len(result.targets)
        self.status_label.setText(
            f"Targets: {target_count}\n"
            "Primary delay: "
            f"{result.expected_delay_s * 1e9:.1f} ns\n"
            "Primary Doppler: "
            f"{result.expected_doppler_hz:.1f} Hz\n"
            "Range resolution: "
            f"{result.range_resolution_m:.2f} m"
        )

    def _parameters_from_controls(self) -> RadarParameters:
        targets = tuple(
            RadarTarget(
                range_m=range_input.value(),
                velocity_mps=velocity_input.value(),
                strength=strength_input.value(),
            )
            for range_input, velocity_input, strength_input in self.target_inputs
        )
        primary = targets[0]
        return RadarParameters(
            initial_range_m=primary.range_m,
            target_velocity_mps=primary.velocity_mps,
            target_strength=primary.strength,
            targets=targets,
            multipath_strength=self.multipath_input.value(),
            static_clutter_strength=self.clutter_input.value(),
            noise_std=self.noise_input.value(),
            packets=self.packet_input.value(),
        )

    def _draw_result(self, result: SimulationResult) -> None:
        self.figure.clear()
        time_axis = result.time_s
        time_label = "Time (seconds)" if time_axis[-1] > 0.001 else "Time (microseconds)"
        if time_label == "Time (microseconds)":
            time_axis = time_axis * 1e6

        time_ax = self.figure.add_subplot(4, 1, 1)
        time_ax.plot(
            time_axis,
            self._normalize(result.tx_signal.real),
            label="Reference",
            linewidth=1.0,
        )
        time_ax.plot(
            time_axis,
            self._normalize(result.rx_signal.real),
            label="Received",
            linewidth=1.0,
            alpha=0.85,
        )
        time_ax.set_title("Time-domain or packet-domain signal")
        time_ax.set_xlabel(time_label)
        time_ax.set_ylabel("Normalized amplitude")
        time_ax.grid(True, alpha=0.25)
        time_ax.legend(loc="upper right")

        doppler_ax = self.figure.add_subplot(4, 1, 2)
        doppler_db = 20.0 * np.log10(result.doppler_spectrum + 1e-12)
        doppler_ax.plot(result.doppler_hz, doppler_db, color="#2563eb", linewidth=1.1)
        doppler_ax.axvline(
            result.expected_doppler_hz,
            color="#b91c1c",
            linestyle="--",
            linewidth=1.0,
            label="Primary target",
        )
        doppler_ax.set_title("Doppler spectrum")
        doppler_ax.set_xlabel("Frequency shift (Hz)")
        doppler_ax.set_ylabel("Magnitude (dB)")
        doppler_ax.grid(True, alpha=0.25)
        doppler_ax.legend(loc="upper right")

        range_ax = self.figure.add_subplot(4, 1, 3)
        range_ax.plot(
            result.range_m,
            result.range_response,
            color="#047857",
            linewidth=1.1,
        )
        for target in result.targets:
            range_ax.axvline(
                target.range_m,
                color="#b91c1c",
                linestyle="--",
                linewidth=0.8,
                alpha=0.55,
            )
        range_ax.set_xlim(0, min(90, max(25, result.expected_range_m + 25)))
        range_ax.set_title("Range-like matched-filter response")
        range_ax.set_xlabel("Range (m)")
        range_ax.set_ylabel("Normalized response")
        range_ax.grid(True, alpha=0.25)

        csi_ax = self.figure.add_subplot(4, 1, 4)
        csi_amp = np.mean(result.csi_amplitude, axis=0)
        csi_phase = np.mean(result.csi_phase, axis=0)
        csi_ax.plot(
            result.csi_subcarriers,
            self._normalize(csi_amp),
            color="#7c3aed",
            linewidth=1.1,
            label="Amplitude",
        )
        phase_ax = csi_ax.twinx()
        phase_ax.plot(
            result.csi_subcarriers,
            csi_phase,
            color="#b45309",
            linewidth=1.0,
            label="Phase",
        )
        csi_ax.set_title("OFDM/CSI subcarrier view")
        csi_ax.set_xlabel("Subcarrier index")
        csi_ax.set_ylabel("Normalized amplitude")
        phase_ax.set_ylabel("Unwrapped phase (rad)")
        csi_ax.grid(True, alpha=0.25)
        self._combined_legend(csi_ax, phase_ax)

        self.canvas.draw_idle()

    @staticmethod
    def _make_target_inputs(
        range_m: float,
        velocity_mps: float,
        strength: float,
    ) -> tuple[QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox]:
        return (
            MainWindow._make_double_spin_box(1.0, 90.0, range_m, " m", 0.5),
            MainWindow._make_double_spin_box(-8.0, 8.0, velocity_mps, " m/s", 0.1),
            MainWindow._make_double_spin_box(0.0, 2.0, strength, "", 0.05),
        )

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
        peak = float(np.max(np.abs(values))) if values.size else 0.0
        if peak == 0.0:
            return values
        return values / peak

    @staticmethod
    def _combined_legend(left_axis, right_axis) -> None:
        handles = left_axis.get_lines() + right_axis.get_lines()
        labels = [handle.get_label() for handle in handles]
        left_axis.legend(handles, labels, loc="upper right")

