# Troubleshooting

## No CSI Lines

- Confirm the ESP32 is connected to Wi-Fi.
- Confirm CSI output is enabled in menuconfig.
- Generate traffic from the AP or another client.
- Try promiscuous mode if appropriate for your experiment.

## Only RSSI Changes

RSSI is a scalar and may change even when CSI is not configured correctly. Check
that `esp_wifi_set_csi_config`, `esp_wifi_set_csi_rx_cb`, and
`esp_wifi_set_csi(true)` all succeed.

## Malformed CSI List

The host parser expects:

```text
CSI_DATA,timestamp_us,src_mac,rssi,rate,sig_mode,mcs,bandwidth,channel,secondary_channel,noise_floor,ant,csi_len,[imag0,real0,...]
```

Dropped serial bytes usually mean the baud rate is too low or the host is not
reading fast enough.

## Serial Too Slow

Use `921600` baud or higher if stable. Reduce packet rate, disable promiscuous
mode, increase queue depth, or output fewer CSI packets.

## Windows COM Port Issue

Check Device Manager for the COM port. Close other serial monitors before
running `esp32csi record`.

## Callback Overload

Never print directly from the CSI callback. This firmware queues minimal data
and lets a serial task format CSV lines.

