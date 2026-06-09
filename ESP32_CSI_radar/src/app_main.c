#include <string.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#include "config.h"
#include "serial_output.h"
#include "wifi_csi.h"

static const char *TAG = "app_main";
static QueueHandle_t s_csi_queue;

static void initialise_nvs(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
        return;
    }
    ESP_ERROR_CHECK(ret);
}

void app_main(void)
{
    initialise_nvs();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    ESP_ERROR_CHECK(serial_output_start(&s_csi_queue));
    ESP_ERROR_CHECK(wifi_csi_init(s_csi_queue));
    ESP_ERROR_CHECK(wifi_csi_start());

#if CONFIG_CSI_TX_MODE
    wifi_csi_start_optional_tx_task();
#endif

    ESP_LOGI(TAG, "ESP32 CSI radar demo started");
    ESP_LOGI(TAG, "Serial CSV format: CSI_DATA,timestamp_us,src_mac,rssi,rate,sig_mode,mcs,bandwidth,channel,secondary_channel,noise_floor,ant,csi_len,[imag0,real0,...]");
}

