# wifi-radar-simulator

An educational desktop simulator for introducing WiFi radar concepts with Python,
NumPy, matplotlib, and PySide6.

The app models a monostatic WiFi-like radar scene: one transmitter/receiver,
several moving targets, multipath reflections, static clutter, and complex
baseband/CSI measurements. It is intentionally small enough for undergraduate
electronics students to inspect, modify, and extend.

## What It Shows

- A complex baseband transmit probe and received echo.
- Several point targets with independent range, velocity, and strength.
- Static clutter and simple multipath reflections.
- A Doppler spectrum caused by packet-to-packet phase rotation.
- A range-like matched-filter response.
- An OFDM/CSI subcarrier view for amplitude and calibrated phase.
- Recorded CSI replay from CSV files.
- An SDR capture extension point for future hardware backends.

This is not a certified RF propagation model. It is a teaching simulator that
keeps the important relationships visible:

- Round-trip delay grows with target range.
- Doppler shift grows with target velocity and carrier frequency.
- Static reflectors can dominate raw CSI unless removed or filtered.
- Matched filtering can turn delayed echoes into range-like peaks.
- OFDM subcarrier phase changes with path delay.

## Project Layout

```text
wifi-radar-simulator/
|-- README.md
|-- requirements.txt
|-- pyproject.toml
|-- src/
|   `-- wifi_radar_simulator/
|       |-- __init__.py
|       |-- __main__.py
|       |-- app.py
|       |-- calibration.py
|       |-- data_sources.py
|       |-- gui.py
|       `-- simulation.py
`-- tests/
    |-- test_data_sources.py
    `-- test_simulation.py
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies and the editable local package:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Run The App

From the project root:

```bash
python -m wifi_radar_simulator
```

If installed in editable mode, you can also run:

```bash
wifi-radar-simulator
```

## Recorded CSI CSV Files

`CsiFileSource` loads a simple long-form CSV:

```csv
packet,subcarrier,real,imag
0,-26,0.91,0.12
0,-25,0.88,0.16
1,-26,0.89,0.18
1,-25,0.84,0.22
```

Each row is one complex CSI value. The loader pivots the rows into a
`packets x subcarriers` matrix, removes the static packet-average background,
unwraps phase, applies a slow-time window for Doppler processing, and reuses the
same plotting pipeline as the synthetic simulator.

## SDR Extension Point

`SdrCaptureSource` is a wrapper for future live radio support. Hardware-specific
code should implement `SdrCaptureBackend.capture_csi(parameters)` and return:

```python
tuple[csi_matrix, subcarriers]
```

This keeps optional backends such as SoapySDR, UHD, or GNU Radio out of the base
dependency set while preserving a clear integration point.

## Calibration Examples

The `calibration.py` module includes three classroom-friendly helpers:

- `unwrap_csi_phase`: removes artificial `-pi` to `pi` phase jumps.
- `remove_static_background`: subtracts packet-average CSI to emphasize moving
  reflectors.
- `apply_slow_time_window`: applies a Hann window before Doppler FFTs.

These are intentionally simple examples, not a complete WiFi sensing calibration
pipeline.

## Run Tests

The tests focus on the numerical simulator and data source adapters:

```bash
python -m unittest discover -s tests
```

## Troubleshooting

If `pip` fails with an import error such as `No module named
'pip._vendor.rich.markup'`, the virtual environment is likely corrupted. Remove
and recreate only the local `.venv` folder:

```powershell
Deactivate
Remove-Item -LiteralPath .\.venv -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Roadmap

- Add a richer CSI importer for common Intel 5300, Nexmon, and ESP32 export
  formats.
- Add optional SDR backend examples for one supported hardware stack.
- Add range-Doppler heatmaps and target tracks over time.
- Add several scenarios such as walking human, rotating fan, and static room.
- Add GUI tests for the main controls and file-loading workflow.
- Package a desktop executable for Windows, macOS, and Linux.

