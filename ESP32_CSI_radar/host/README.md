# ESP32 CSI Host Tools

Python host package for recording, parsing, plotting, and analysing CSI lines
from the ESP32 firmware in this project.

Install from this folder:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Main commands:

```bash
esp32csi record --port COM3 --baud 921600 --output data/session.csv
esp32csi live --port COM3 --baud 921600
esp32csi analyse data/session.csv --out results/
esp32csi convert data/session.csv --output data/session.npz
esp32csi simulate --output data/synthetic.csv --seconds 60
```

