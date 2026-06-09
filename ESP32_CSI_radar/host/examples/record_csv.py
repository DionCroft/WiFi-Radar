"""Record ESP32 CSI CSV from a serial port."""

from esp32csi.serial_reader import record_csv


record_csv(port="COM3", baud=921600, output="data/session.csv")

