# Signal Processing Notes

ESP32 CSI is a complex channel measurement. RSSI is one scalar packet-strength
value; CSI is a vector across OFDM subcarriers. CSI can show frequency-selective
multipath changes that RSSI hides.

The host processing pipeline is:

1. Parse CSI CSV lines.
2. Convert raw ESP-IDF byte order from imaginary/real pairs to `real + j*imag`.
3. Remove malformed packets.
4. Convert to amplitude and phase.
5. Unwrap phase along time.
6. Remove static mean clutter.
7. Apply median/Hampel filtering for outliers.
8. Use high-pass filtering for motion.
9. Use 0.1 to 0.6 Hz band-pass filtering for breathing-like periodic motion.
10. Estimate dominant breathing frequency with an FFT peak.

This is an experimental signal-processing pipeline, not a medical monitor.

