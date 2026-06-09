#pragma once

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

esp_err_t serial_output_start(QueueHandle_t *out_queue);

