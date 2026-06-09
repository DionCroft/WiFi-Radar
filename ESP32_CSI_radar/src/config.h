#pragma once

/* Project defaults can be overridden with idf.py menuconfig. */

#ifndef CONFIG_CSI_WIFI_SSID
#define CONFIG_CSI_WIFI_SSID "YOUR_WIFI_SSID"
#endif

#ifndef CONFIG_CSI_WIFI_PASSWORD
#define CONFIG_CSI_WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#endif

#ifndef CONFIG_CSI_WIFI_CHANNEL
#define CONFIG_CSI_WIFI_CHANNEL 6
#endif

#ifndef CONFIG_CSI_SERIAL_BAUD
#define CONFIG_CSI_SERIAL_BAUD 921600
#endif

#ifndef CONFIG_CSI_QUEUE_DEPTH
#define CONFIG_CSI_QUEUE_DEPTH 32
#endif

#ifndef CONFIG_CSI_MAX_BYTES
#define CONFIG_CSI_MAX_BYTES 512
#endif

#ifndef CONFIG_CSI_TX_INTERVAL_MS
#define CONFIG_CSI_TX_INTERVAL_MS 100
#endif

#define CSI_UDP_TX_PORT 3333

