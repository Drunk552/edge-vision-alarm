/**
 * @file wifi_manager.c
 * @brief ESP32 Wi-Fi STA 联网管理模块。
 */

#include "wifi_manager.h"

#include <string.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "nvs_flash.h"
#include "sdkconfig.h"

#define WIFI_CONNECTED_BIT BIT0

static const char *TAG = "wifi_manager";

static EventGroupHandle_t s_wifi_event_group;
static bool s_wifi_connected = false;
static int s_retry_count = 0;
static bool s_event_loop_created = false;

// 处理 Wi-Fi 连接、断开和获取 IP 事件。
static void wifi_event_handler(
    void *arg,
    esp_event_base_t event_base,
    int32_t event_id,
    void *event_data)
{
    (void)arg;

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        ESP_LOGI(TAG, "Wi-Fi STA started, connecting to router");
        esp_wifi_connect();
        return;
    }

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        s_wifi_connected = false;
        xEventGroupClearBits(s_wifi_event_group, WIFI_CONNECTED_BIT);

        wifi_event_sta_disconnected_t *disconnected = (wifi_event_sta_disconnected_t *)event_data;
        ESP_LOGW(TAG, "Wi-Fi disconnected, reason=%d", disconnected->reason);

        if (s_retry_count < CONFIG_EDGE_WIFI_MAXIMUM_RETRY) {
            s_retry_count++;
            ESP_LOGI(
                TAG,
                "retry Wi-Fi connection, attempt %d/%d",
                s_retry_count,
                CONFIG_EDGE_WIFI_MAXIMUM_RETRY);
            esp_wifi_connect();
        } else {
            s_retry_count = 0;
            ESP_LOGW(
                TAG,
                "Wi-Fi retry limit reached, restart reconnect cycle after disconnect event");
            esp_wifi_connect();
        }
        return;
    }

    if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        s_retry_count = 0;
        s_wifi_connected = true;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
        ESP_LOGI(TAG, "Wi-Fi connected, ip=" IPSTR, IP2STR(&event->ip_info.ip));

        int8_t rssi = 0;
        if (wifi_manager_get_rssi(&rssi) == ESP_OK) {
            ESP_LOGI(TAG, "Wi-Fi RSSI: %d dBm", rssi);
        }
    }
}

// 初始化 NVS，Wi-Fi 驱动需要使用 NVS 保存校准和配置数据。
static esp_err_t init_nvs(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS needs erase before init");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    return ret;
}

esp_err_t wifi_manager_init(void)
{
    ESP_LOGI(TAG, "initialize Wi-Fi manager");

    if (strlen(CONFIG_EDGE_WIFI_SSID) == 0) {
        ESP_LOGW(TAG, "Wi-Fi SSID is empty, please configure it with idf.py menuconfig");
    }

    ESP_ERROR_CHECK(init_nvs());
    ESP_ERROR_CHECK(esp_netif_init());

    if (!s_event_loop_created) {
        esp_err_t ret = esp_event_loop_create_default();
        if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
            return ret;
        }
        s_event_loop_created = true;
    }

    s_wifi_event_group = xEventGroupCreate();
    if (s_wifi_event_group == NULL) {
        ESP_LOGE(TAG, "failed to create Wi-Fi event group");
        return ESP_ERR_NO_MEM;
    }

    esp_netif_create_default_wifi_sta();

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init_config));
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
    strlcpy((char *)wifi_config.sta.ssid, CONFIG_EDGE_WIFI_SSID, sizeof(wifi_config.sta.ssid));
    strlcpy(
        (char *)wifi_config.sta.password,
        CONFIG_EDGE_WIFI_PASSWORD,
        sizeof(wifi_config.sta.password));
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.sae_pwe_h2e = WPA3_SAE_PWE_BOTH;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Wi-Fi initialization finished, ssid=%s", CONFIG_EDGE_WIFI_SSID);
    return ESP_OK;
}

bool wifi_manager_is_connected(void)
{
    return s_wifi_connected;
}

esp_err_t wifi_manager_get_rssi(int8_t *rssi)
{
    if (rssi == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    wifi_ap_record_t ap_info = {0};
    esp_err_t ret = esp_wifi_sta_get_ap_info(&ap_info);
    if (ret != ESP_OK) {
        return ret;
    }

    *rssi = ap_info.rssi;
    return ESP_OK;
}
