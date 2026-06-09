# wifi-csi-sensing-toolkit

A research-grade but beginner-friendly Python toolkit for Wi-Fi Channel State
Information (CSI) sensing experiments such as human motion, occupancy, and
breathing-like periodic motion detection.

The toolkit runs on a host laptop. A Microsoft Surface Pro 11, for example, can
be a good processing computer, but its built-in Wi-Fi adapter should not be
assumed to expose raw CSI. CSI usually comes from external supported hardware,
special firmware, Linux CSI tooling, PicoScenes, Nexmon, ESP32 logs, or recorded
files.

This project does not require MATLAB.

## What CSI Is

Wi-Fi CSI describes how each OFDM subcarrier changed while traveling from a
transmitter to a receiver. Each CSI value is complex:

- amplitude shows how strong the channel is,
- phase shows the signal's angle after propagation,
- changes over time can reveal motion in the environment.

Commodity Wi-Fi CSI is useful for experiments in presence, motion, gesture, and
breathing-like periodic motion. It is not a medical device, a calibrated radar,
or a reliable identity system.

## Common CSI Hardware And Sources

Supported source modules are included for:

- Intel IWL5300 / Linux 802.11n CSI Tool files.
- Intel AX200 / AX210 / AX201 / AX211 via PicoScenes output where available.
- Qualcomm Atheros QCA9300 / AR9300 via PicoScenes or Atheros CSI Tool output.
- Broadcom Nexmon CSI PCAP files from supported Raspberry Pi, Nexus, or router
  Broadcom chips.
- ESP32 CSI CSV logs.
- Generic CSV or NPZ files.
- Simulated CSI for development without hardware.

Many parsers rely on optional third-party tooling such as `csiread`. If an
optional dependency is unavailable, the parser raises a clear error with install
guidance instead of failing mysteriously.

## Why Laptop Wi-Fi Usually Is Not Enough

Most laptop Wi-Fi drivers expose packets, signal strength, and connection
statistics, but not raw per-subcarrier CSI. Access to CSI generally requires a
specific chipset, modified firmware, kernel tooling, monitor mode support, or an
external device that exports CSI. Treat the laptop as the host that records,
processes, and visualises CSI from a supported source.

## Project Layout

```text
wifi-csi-sensing-toolkit/
|-- README.md
|-- pyproject.toml
|-- requirements.txt
|-- src/wificsi/
|   |-- core.py
|   |-- cli.py
|   |-- io/
|   |-- processing/
|   `-- visualisation/
|-- examples/
|-- tests/
`-- data/
```

## Installation

```bash
cd wifi-csi-sensing-toolkit
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

Install the package:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Optional parser support:

```bash
python -m pip install csiread scapy pyserial
```

## Quick Start: Synthetic Data

Generate a synthetic CSI recording:

```bash
wificsi simulate --seconds 60 --rate 100 --breathing-hz 0.25 --output synthetic.npz
```

Inspect it:

```bash
wificsi info synthetic.npz --format npz
```

Plot amplitude:

```bash
wificsi plot synthetic.npz --format npz --plot amplitude
```

Estimate breathing-like periodic motion:

```bash
wificsi breathing synthetic.npz --format npz --min-hz 0.1 --max-hz 0.6
```

Run the example scripts:

```bash
python examples/generate_synthetic_csi.py
python examples/offline_motion_demo.py
python examples/offline_breathing_demo.py
```

## Quick Start: ESP32 CSV

ESP32 CSI logs commonly contain a timestamp and a CSI vector string containing
interleaved real and imaginary values. This toolkit accepts columns such as:

```csv
timestamp,csi
0.000,"[12, -3, 8, 1, ...]"
0.010,"[11, -2, 7, 2, ...]"
```

Then run:

```bash
wificsi info esp32_capture.csv --format esp32
wificsi plot esp32_capture.csv --format esp32 --plot phase
wificsi motion esp32_capture.csv --format esp32
```

## Quick Start: PicoScenes / Intel / Atheros / Nexmon

These formats are routed through source-specific modules. Install optional
support first:

```bash
python -m pip install csiread scapy
```

Examples:

```bash
wificsi info capture.csi --format intel5300
wificsi motion picoscenes_output.csi --format picoscenes
wificsi plot nexmon_capture.pcap --format nexmon --plot amplitude
```

If the installed parser cannot decode a file, the command explains which
dependency or conversion path is missing. PicoScenes exports vary by version, so
NPZ or CSV export is the most reliable interchange format for this first
toolkit version.

## Processing Pipeline

The typical offline pipeline is:

1. Load CSI into the common `CSIData` object.
2. Remove invalid packets and NaNs.
3. Select usable subcarriers.
4. Convert complex CSI to amplitude and phase.
5. Unwrap phase over time.
6. Remove static clutter with mean subtraction or high-pass filtering.
7. Apply median or Hampel-style outlier filtering.
8. Enhance motion with PCA across subcarriers.
9. Compute motion score, Doppler spectrogram, or breathing-rate estimate.
10. Export processed features to CSV or NPZ.

## Plot Types

Available matplotlib plots:

- CSI amplitude heatmap.
- CSI phase heatmap.
- Motion score over time.
- Doppler/spectrogram plot.
- Breathing waveform and estimated breathing rate.

## Live Serial Visualiser

The live command is intentionally simple and best effort. It reads ESP32-style
CSV/text lines from a serial port and updates a scrolling matplotlib plot:

```bash
wificsi live --source serial --port COM3 --baud 921600
```

On Linux or macOS, the port might look like `/dev/ttyUSB0` or `/dev/tty.usbserial`.

## Limitations

- Commodity Wi-Fi CSI is strongly affected by antenna placement, multipath,
  packet rate, firmware, bandwidth, and channel conditions.
- Breathing estimates are experimental and can be confused by gross motion,
  multiple people, fans, pets, or moving curtains.
- Occupancy and motion scores are not identity recognition.
- Results are not medically accurate and should not be used for diagnosis,
  safety-critical monitoring, or clinical decisions.
- Different chipsets and toolchains scale and order CSI differently.

## Ethics And Privacy

Only run wireless sensing experiments in spaces where you have permission.
Inform participants, respect privacy, and avoid collecting data in shared or
private spaces without consent. Even when CSI does not contain packet payloads,
it can still reveal activity patterns.

## Tests

Tests use generated synthetic data and do not require real CSI hardware:

```bash
python -m pytest
```

