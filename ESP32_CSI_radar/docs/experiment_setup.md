# Experiment Setup

## Option 1: Router/AP As Transmitter

Use one ESP32 as the CSI receiver and connect it to a normal Wi-Fi router or
access point. The router, laptop, or another client can generate traffic. This
is usually the simplest setup.

## Option 2: Two ESP32 Boards

Use one ESP32 in receiver mode and one ESP32 in optional `CSI_TX_MODE`. The TX
board sends simple UDP broadcast packets. This is standards-friendly and avoids
deauthentication, spoofing, or disruptive packet injection.

## Option 3: Multiple Receivers

Future experiments can place multiple ESP32 receivers around a room for spatial
diversity. Keep clocks and labels organised because data alignment becomes the
main challenge.

## Recommended Procedure

1. Keep the router/transmitter fixed.
2. Keep the receiver fixed.
3. Record an empty-room baseline.
4. Record walking or obvious motion.
5. Record seated breathing at short distance.
6. Compare amplitude, motion score, spectrogram, and breathing-band plots.
7. Avoid other people moving during baseline.
8. Use external antenna boards when available for repeatability.
9. Label experiments with room, distance, orientation, channel, and participants.

