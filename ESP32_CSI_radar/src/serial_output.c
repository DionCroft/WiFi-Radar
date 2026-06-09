#include "serial_output.h"

#include <stdio.h>

#include "driver/uart.h"
#include "esp_check.h"
#include "freertos/task.h"

#include "config.h"
#include "wifi_csi.h"

static const char *TAG = "serial_output";

static void print_mac(const uint8_t mac[6])
{
    printf("%02x:%02x:%02x:%02x:%02x:%02x",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static void serial_output_task(void *arg)
{
    QueueHandle_t queue = (QueueHandle_t)arg;
    csi_serial_record_t record;

    while (true) {
        if (xQueueReceive(queue, &record, portMAX_DELAY) != pdTRUE) {
            continue;
        }

#if CONFIG_CSI_OUTPUT_ENABLE
        printf("CSI_DATA,%lu,", (unsigned long)record.timestamp_us);
        print_mac(record.src_mac);
        printf(",%d,%u,%u,%u,%u,%u,%u,%d,%u,%u,[",
               record.rssi,
               record.rate,
               record.sig_mode,
               record.mcs,
               record.bandwidth,
               record.channel,
               record.secondary_channel,
               record.noise_floor,
               record.ant,
               record.csi_len);

        /*
         * ESP-IDF CSI bytes are signed int8 values in raw chip order. For classic
         * ESP32 this order is imaginary, then real. We preserve that raw order on
         * the wire; the host parser converts pairs to real + j*imag.
         */
        for (uint16_t index = 0; index < record.csi_len; ++index) {
            if (index > 0) {
                putchar(',');
            }
            printf("%d", record.csi[index]);
        }
        printf("]\n");
#endif
    }
}

esp_err_t serial_output_start(QueueHandle_t *out_queue)
{
    ESP_RETURN_ON_FALSE(out_queue != NULL, ESP_ERR_INVALID_ARG, TAG, "out_queue is NULL");

    const uart_port_t uart_num = UART_NUM_0;
    uart_config_t uart_config = {
        .baud_rate = CONFIG_CSI_SERIAL_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    ESP_ERROR_CHECK(uart_param_config(uart_num, &uart_config));
    ESP_ERROR_CHECK(uart_driver_install(uart_num, 4096, 0, 0, NULL, 0));

    QueueHandle_t queue = xQueueCreate(CONFIG_CSI_QUEUE_DEPTH, sizeof(csi_serial_record_t));
    ESP_RETURN_ON_FALSE(queue != NULL, ESP_ERR_NO_MEM, TAG, "failed to create CSI queue");

    BaseType_t ok = xTaskCreate(
        serial_output_task,
        "csi_serial_output",
        4096,
        queue,
        4,
        NULL);
    ESP_RETURN_ON_FALSE(ok == pdPASS, ESP_ERR_NO_MEM, TAG, "failed to create serial task");

    *out_queue = queue;
    return ESP_OK;
}

