/**
 * @file heartbeat.c
 * @brief ESP32 设备心跳上报模块。
 */

#include "heartbeat.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "app_config.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "wifi_manager.h"

#define HEARTBEAT_TASK_NAME "heartbeat_task"
#define HEARTBEAT_TASK_STACK_SIZE 4096
#define HEARTBEAT_TASK_PRIORITY 5
#define HEARTBEAT_URL_MAX_LEN 160
#define HEARTBEAT_BODY_MAX_LEN 256

static const char *TAG = "heartbeat";
static TaskHandle_t s_heartbeat_task_handle = NULL;

/**
 * @brief 拼接心跳接口 URL。
 *
 * @param url 输出 URL 缓冲区。
 * @param url_len URL 缓冲区长度。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t build_heartbeat_url(char *url, size_t url_len)
{
    if (url == NULL || url_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (strlen(APP_CONFIG_SERVER_URL) == 0) {
        ESP_LOGW(TAG, "server URL is empty, please configure it with idf.py menuconfig");
        return ESP_ERR_INVALID_STATE;
    }

    int written = snprintf(url, url_len, "%s/api/heartbeat", APP_CONFIG_SERVER_URL);
    if (written < 0 || written >= (int)url_len) {
        ESP_LOGE(TAG, "heartbeat URL buffer is too small");
        return ESP_ERR_NO_MEM;
    }

    return ESP_OK;
}

/**
 * @brief 构造心跳 JSON 请求体。
 *
 * @param body 输出 JSON 缓冲区。
 * @param body_len JSON 缓冲区长度。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t build_heartbeat_body(char *body, size_t body_len)
{
    if (body == NULL || body_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    int8_t rssi = 0;
    esp_err_t rssi_ret = wifi_manager_get_rssi(&rssi);
    if (rssi_ret != ESP_OK) {
        ESP_LOGW(TAG, "failed to get Wi-Fi RSSI: %s", esp_err_to_name(rssi_ret));
    }

    int written = snprintf(
        body,
        body_len,
        "{\"device_id\":\"%s\",\"rssi\":%d,\"free_heap\":%" PRIu32 ",\"status\":\"online\"}",
        APP_CONFIG_DEVICE_ID,
        rssi_ret == ESP_OK ? rssi : 0,
        esp_get_free_heap_size());
    if (written < 0 || written >= (int)body_len) {
        ESP_LOGE(TAG, "heartbeat body buffer is too small");
        return ESP_ERR_NO_MEM;
    }

    return ESP_OK;
}

/**
 * @brief 执行一次心跳上报。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t post_heartbeat_once(void)
{
    char url[HEARTBEAT_URL_MAX_LEN] = {0};
    char body[HEARTBEAT_BODY_MAX_LEN] = {0};

    esp_err_t ret = build_heartbeat_url(url, sizeof(url));
    if (ret != ESP_OK) {
        return ret;
    }

    ret = build_heartbeat_body(body, sizeof(body));
    if (ret != ESP_OK) {
        return ret;
    }

    esp_http_client_config_t config = {
        .url = url,
        .method = HTTP_METHOD_POST,
        .timeout_ms = APP_CONFIG_HTTP_TIMEOUT_MS,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (client == NULL) {
        ESP_LOGE(TAG, "failed to initialize HTTP client");
        return ESP_FAIL;
    }

    esp_http_client_set_header(client, "Content-Type", "application/json");
    if (strlen(APP_CONFIG_API_TOKEN) > 0) {
        esp_http_client_set_header(client, "X-API-Token", APP_CONFIG_API_TOKEN);
    }
    esp_http_client_set_post_field(client, body, strlen(body));

    ret = esp_http_client_perform(client);
    if (ret == ESP_OK) {
        int status_code = esp_http_client_get_status_code(client);
        int64_t content_length = esp_http_client_get_content_length(client);
        ESP_LOGI(
            TAG,
            "heartbeat posted, status=%d, response_length=%" PRId64,
            status_code,
            content_length);
        if (status_code < 200 || status_code >= 300) {
            ret = ESP_FAIL;
        }
    } else {
        ESP_LOGW(TAG, "heartbeat post failed: %s", esp_err_to_name(ret));
    }

    esp_http_client_cleanup(client);
    return ret;
}

/**
 * @brief 心跳上报 FreeRTOS 任务。
 *
 * @param arg 任务参数，当前未使用。
 */
static void heartbeat_task(void *arg)
{
    (void)arg;

    while (true) {
        if (wifi_manager_is_connected()) {
            (void)post_heartbeat_once();
        } else {
            ESP_LOGI(TAG, "skip heartbeat, Wi-Fi disconnected");
        }

        vTaskDelay(pdMS_TO_TICKS(APP_CONFIG_HEARTBEAT_INTERVAL_MS));
    }
}

esp_err_t heartbeat_start(void)
{
    if (s_heartbeat_task_handle != NULL) {
        ESP_LOGW(TAG, "heartbeat task already started");
        return ESP_OK;
    }

    BaseType_t result = xTaskCreate(
        heartbeat_task,
        HEARTBEAT_TASK_NAME,
        HEARTBEAT_TASK_STACK_SIZE,
        NULL,
        HEARTBEAT_TASK_PRIORITY,
        &s_heartbeat_task_handle);
    if (result != pdPASS) {
        ESP_LOGE(TAG, "failed to create heartbeat task");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "heartbeat task started, interval=%d ms", APP_CONFIG_HEARTBEAT_INTERVAL_MS);
    return ESP_OK;
}
