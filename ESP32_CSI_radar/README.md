# esp32-csi-radar-demo

An ESP-IDF / PlatformIO ESP32 Wi-Fi CSI sensing project for authorised human
presence, motion, and breathing-like experiments. It includes firmware for
capturing CSI and a Python host application for logging, plotting, and analysis.

The host computer may be a Microsoft Surface Pro 11 running Windows, Linux, or
WSL. Treat the Surface as the processing laptop only; its built-in Wi-Fi should
not be assumed to expose raw CSI. The ESP32 connects by USB serial and provides
the CSI stream.

## What CSI Is

Channel State Information describes how each Wi-Fi OFDM subcarrier changed while
travelling through the room. CSI is complex-valued and contains amplitude and
phase per subcarrier.

RSSI is one packet-strength number. CSI is a vector of per-subcarrier channel
measurements. CSI is richer than RSSI and can show multipath changes from human
motion, but it is also sensitive to placement, channel, firmware, and noise.

## Hardware

Targets include ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C5, and ESP32-C6
where supported by ESP-IDF CSI APIs. Prefer ESP32-S3 or ESP32-C6 for new
experiments.

## Firmware Build And Flash

This folder is a PlatformIO ESP-IDF project. You can use PlatformIO:

```bash
pio run
pio run --target upload
pio device monitor --baud 921600
```

Or ESP-IDF directly from this folder:

```bash
idf.py set-target esp32s3
idf.py menuconfig
idf.py build flash monitor
```

Configure SSID, password, channel, queue depth, CSI output, promiscuous mode,
and optional TX mode in `idf.py menuconfig` under `ESP32 CSI Radar Demo`.

## Serial CSV Format

The firmware emits:

```text
CSI_DATA,timestamp_us,src_mac,rssi,rate,sig_mode,mcs,bandwidth,channel,secondary_channel,noise_floor,ant,csi_len,[imag0,real0,imag1,real1,...]
```

ESP-IDF CSI bytes are preserved in raw chip order. For classic ESP32 this is
imaginary then real. The host parser exposes complex values as `real + j*imag`.

## Python Host Installation

```bash
cd host
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

On Linux or WSL, activate with `source .venv/bin/activate`.

## Live Recording

```bash
esp32csi record --port COM3 --baud 921600 --output data/session.csv
```

Linux ports usually look like `/dev/ttyUSB0` or `/dev/ttyACM0`.

## Live View

```bash
esp32csi live --port COM3 --baud 921600
```

## Offline Analysis

```bash
esp32csi analyse data/session.csv --out results/
esp32csi convert data/session.csv --output data/session.npz
esp32csi simulate --output data/synthetic.csv --seconds 60
```

## Setup Options

1. One ESP32 receiver connected to a normal Wi-Fi router/AP.
2. Two ESP32 boards, with one optional UDP broadcast transmitter.
3. Multiple ESP32 receivers for future diversity.

Using a normal router/AP as transmitter is often easiest.

## Troubleshooting

See:

- `docs/experiment_setup.md`
- `docs/signal_processing.md`
- `docs/troubleshooting.md`

Common issues include no CSI lines, malformed CSI vectors, serial throughput
limits, Wi-Fi not connected, and callback overload.

## Safety, Legality, Ethics

This project is for authorised sensing experiments only. Do not use it for
deauthentication, spoofing, credential capture, stealth monitoring, bypassing
network protections, or any network disruption. Only test where all occupants
know about the experiment and consent.

Breathing-like estimates are experimental and are not medically accurate. This
is not a medical device.

