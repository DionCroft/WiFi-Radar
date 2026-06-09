# wifi-radar-simulator

An educational desktop simulator for introducing WiFi radar concepts with Python,
NumPy, matplotlib, and PySide6.

The first version models a simple monostatic radar: one WiFi-like transmitter,
one moving target, and one reflected signal. It is intentionally small enough for
undergraduate electronics students to inspect, modify, and extend.

## What It Shows

- A complex baseband transmit probe, similar to the signal processing view used
  after a radio has down-converted a WiFi signal.
- A delayed reflected signal from a target at a chosen range.
- A Doppler spectrum caused by target motion.
- A range-like matched-filter response showing where the target echo appears.

This is not a certified RF propagation model. It is a teaching simulator that
keeps the important relationships visible:

- Round-trip delay grows with target range.
- Doppler shift grows with target velocity and carrier frequency.
- Matched filtering can turn a delayed echo into a range-like peak.

## Project Layout

```text
wifi-radar-simulator/
├── README.md
├── requirements.txt
├── pyproject.toml
├── src/
│   └── wifi_radar_simulator/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── data_sources.py
│       ├── gui.py
│       └── simulation.py
└── tests/
    └── test_simulation.py
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

If you only want to run the numerical tests and not the GUI, installing NumPy is
enough:

```bash
python -m pip install numpy
```

## Run The App

After the editable install, run from the project root:

```bash
python -m wifi_radar_simulator
```

If installed in editable mode, you can also run:

```bash
wifi-radar-simulator
```

## Run Tests

The tests focus on the numerical simulator and avoid starting the GUI:

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

## Educational Notes

The simulator uses a baseband chirp as a compact stand-in for a WiFi-like probe.
Real WiFi radar systems often work with channel state information (CSI), packet
preambles, or software-defined radio captures. The current code separates the
simulation model from the data source interface so those real inputs can be added
later without rewriting the GUI.

Positive target velocity means the target is moving toward the transmitter and
receiver. In this sign convention, positive velocity creates a positive Doppler
shift.

## Roadmap

- Add recorded CSI file loading with a `CsiFileSource`.
- Add SDR capture support behind the existing data source interface.
- Add multipath and static clutter controls.
- Add several targets with independent range, velocity, and strength.
- Add an OFDM/CSI view for subcarrier amplitude and phase.
- Add calibration examples for phase unwrap, static removal, and windowing.
- Package a desktop executable for Windows, macOS, and Linux.
- Expand tests to cover GUI state and data source plugins.
