"""Launch the live ESP32-style serial visualiser."""

from wificsi.visualisation.live import run_serial_live_plot


run_serial_live_plot(port="COM3", baud=921600)

