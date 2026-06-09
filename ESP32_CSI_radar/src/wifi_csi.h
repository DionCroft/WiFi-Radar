#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "esp_wifi_types.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#include "config.h"

typedef struct {
    uint32_t timestamp_us;
    uint8_t src_mac[6];
    int8_t rssi;
    uint8_t rate;
    uint8_t sig_mode;
    uint8_t mcs;
    uint8_t bandwidth;
    uint8_t channel;
    uint8_t secondary_channel;
    int8_t noise_floor;
    uint8_t ant;
    uint16_t csi_len;
    int8_t csi[CONFIG_CSI_MAX_BYTES];
} csi_serial_record_t;

esp_err_t wifi_csi_init(QueueHandle_t csi_queue);
esp_err_t wifi_csi_start(void);
void wifi_csi_start_optional_tx_task(void);

