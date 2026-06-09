#include "wifi_csi.h"

#include <string.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_wifi.h"
#include "esp_wifi_types.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "lwip/sockets.h"

static const char *TAG = "wifi_csi";
static QueueHandle_t s_csi_queue;
static EventGroupHandle_t s_wifi_event_group;
static const int WIFI_CONNECTED_BIT = BIT0;

static void wifi_event_handler(
    void *arg,
    esp_event_base_t event_base,
    int32_t event_id,
    void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGW(TAG, "Wi-Fi disconnected; retrying");
        esp_wifi_connect();
        xEventGroupClearBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
        ESP_LOGI(TAG, "Wi-Fi connected");
    }
}

static void csi_rx_callback(void *ctx, wifi_csi_info_t *info)
{
    if (info == NULL || info->buf == NULL || s_csi_queue == NULL) {
        return;
    }

    csi_serial_record_t record = {0};
    const wifi_pkt_rx_ctrl_t *rx_ctrl = &info->rx_ctrl;

    record.timestamp_us = rx_ctrl->timestamp;
    memcpy(record.src_mac, info->mac, sizeof(record.src_mac));
    record.rssi = rx_ctrl->rssi;
    record.rate = rx_ctrl->rate;
    record.sig_mode = rx_ctrl->sig_mode;
    record.mcs = rx_ctrl->mcs;
    record.bandwidth = rx_ctrl->cwb;
    record.channel = rx_ctrl->channel;
    record.secondary_channel = rx_ctrl->secondary_channel;
    record.noise_floor = rx_ctrl->noise_floor;
    record.ant = rx_ctrl->ant;

    uint16_t copy_len = info->len;
    if (copy_len > CONFIG_CSI_MAX_BYTES) {
        copy_len = CONFIG_CSI_MAX_BYTES;
    }
    record.csi_len = copy_len;
    memcpy(record.csi, info->buf, copy_len);

    /* Do not block or print in the Wi-Fi callback. Drop if the host is slow. */
    (void)xQueueSend(s_csi_queue, &record, 0);
}

esp_err_t wifi_csi_init(QueueHandle_t csi_queue)
{
    s_csi_queue = csi_queue;
    s_wifi_event_group = xEventGroupCreate();
    if (s_wifi_event_group == NULL) {
        return ESP_ERR_NO_MEM;
    }

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT,
        ESP_EVENT_ANY_ID,
        &wifi_event_handler,
        NULL,
        NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT,
        IP_EVENT_STA_GOT_IP,
        &wifi_event_handler,
        NULL,
        NULL));

    wifi_config_t wifi_config = {0};
    strncpy((char *)wifi_config.sta.ssid, CONFIG_CSI_WIFI_SSID, sizeof(wifi_config.sta.ssid));
    strncpy((char *)wifi_config.sta.password, CONFIG_CSI_WIFI_PASSWORD, sizeof(wifi_config.sta.password));
    wifi_config.sta.channel = CONFIG_CSI_WIFI_CHANNEL;
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));

    return ESP_OK;
}

esp_err_t wifi_csi_start(void)
{
    ESP_ERROR_CHECK(esp_wifi_start());
    xEventGroupWaitBits(
        s_wifi_event_group,
        WIFI_CONNECTED_BIT,
        pdFALSE,
        pdTRUE,
        pdMS_TO_TICKS(15000));

    wifi_csi_config_t csi_config = {
        .lltf_en = true,
        .htltf_en = true,
        .stbc_htltf2_en = true,
        .ltf_merge_en = true,
        .channel_filter_en = false,
        .manu_scale = false,
        .shift = false,
    };

    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(csi_rx_callback, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));

#if CONFIG_CSI_PROMISCUOUS_MODE
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
    ESP_LOGI(TAG, "Promiscuous mode enabled");
#endif

    ESP_LOGI(TAG, "CSI enabled");
    return ESP_OK;
}

#if CONFIG_CSI_TX_MODE
static void csi_udp_tx_task(void *arg)
{
    const char payload[] = "esp32-csi-radar-demo";
    struct sockaddr_in dest = {
        .sin_family = AF_INET,
        .sin_port = htons(CSI_UDP_TX_PORT),
        .sin_addr.s_addr = htonl(INADDR_BROADCAST),
    };

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) {
        ESP_LOGE(TAG, "UDP socket creation failed");
        vTaskDelete(NULL);
        return;
    }

    int enable_broadcast = 1;
    setsockopt(sock, SOL_SOCKET, SO_BROADCAST, &enable_broadcast, sizeof(enable_broadcast));

    while (true) {
        sendto(sock, payload, sizeof(payload), 0, (struct sockaddr *)&dest, sizeof(dest));
        vTaskDelay(pdMS_TO_TICKS(CONFIG_CSI_TX_INTERVAL_MS));
    }
}

void wifi_csi_start_optional_tx_task(void)
{
    xTaskCreate(csi_udp_tx_task, "csi_udp_tx", 4096, NULL, 4, NULL);
}
#else
void wifi_csi_start_optional_tx_task(void)
{
}
#endif

