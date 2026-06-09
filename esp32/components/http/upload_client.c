/**
 * @file upload_client.c
 * @brief ESP32 图片上传 HTTP 客户端模块。
 */

#include "upload_client.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "alarm_gpio.h"
#include "app_config.h"
#include "camera_driver.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "wifi_manager.h"

#define UPLOAD_TASK_NAME "upload_task"
#define UPLOAD_TASK_STACK_SIZE 6144
#define UPLOAD_TASK_PRIORITY 4
#define UPLOAD_URL_MAX_LEN 160
#define UPLOAD_RESPONSE_BUFFER_SIZE 512
#define UPLOAD_BOUNDARY "----edge-vision-alarm-boundary"

static const char *TAG = "upload_client";
static TaskHandle_t s_upload_task_handle = NULL;

/**
 * @brief 拼接图片上传接口 URL。
 *
 * @param url 输出 URL 缓冲区。
 * @param url_len URL 缓冲区长度。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t build_upload_url(char *url, size_t url_len)
{
    if (url == NULL || url_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (strlen(APP_CONFIG_SERVER_URL) == 0) {
        ESP_LOGW(TAG, "server URL is empty, please configure it with idf.py menuconfig");
        return ESP_ERR_INVALID_STATE;
    }

    int written = snprintf(url, url_len, "%s/api/upload", APP_CONFIG_SERVER_URL);
    if (written < 0 || written >= (int)url_len) {
        ESP_LOGE(TAG, "upload URL buffer is too small");
        return ESP_ERR_NO_MEM;
    }

    return ESP_OK;
}

/**
 * @brief 写入 HTTP 请求体片段。
 *
 * @param client HTTP Client 句柄。
 * @param data 待写入数据。
 * @param len 待写入数据长度。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t write_http_data(esp_http_client_handle_t client, const char *data, int len)
{
    int written = esp_http_client_write(client, data, len);
    if (written != len) {
        ESP_LOGE(TAG, "failed to write HTTP data, expected=%d, written=%d", len, written);
        return ESP_FAIL;
    }

    return ESP_OK;
}

/**
 * @brief 判断上传响应中是否包含告警标志。
 *
 * @param response 服务端响应字符串。
 * @return true 表示服务端要求本地告警。
 */
static bool upload_response_has_alarm(const char *response)
{
    if (response == NULL) {
        return false;
    }

    return strstr(response, "\"alarm\":true") != NULL || strstr(response, "\"alarm\": true") != NULL;
}

/**
 * @brief 读取上传响应并触发本地告警。
 *
 * @param client HTTP Client 句柄。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t handle_upload_response(esp_http_client_handle_t client)
{
    char response[UPLOAD_RESPONSE_BUFFER_SIZE] = {0};
    int read_len = esp_http_client_read_response(client, response, sizeof(response) - 1);
    if (read_len < 0) {
        ESP_LOGW(TAG, "failed to read upload response");
        return ESP_FAIL;
    }

    response[read_len] = '\0';
    if (upload_response_has_alarm(response)) {
        ESP_LOGI(TAG, "server returned alarm=true");
        esp_err_t ret = alarm_gpio_trigger();
        if (ret != ESP_OK) {
            ESP_LOGW(TAG, "failed to trigger local alarm: %s", esp_err_to_name(ret));
        }
    }

    return ESP_OK;
}

/**
 * @brief 执行一次图片上传。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t upload_image_once(void)
{
    char url[UPLOAD_URL_MAX_LEN] = {0};
    esp_err_t ret = build_upload_url(url, sizeof(url));
    if (ret != ESP_OK) {
        return ret;
    }

    int8_t rssi = 0;
    esp_err_t rssi_ret = wifi_manager_get_rssi(&rssi);
    if (rssi_ret != ESP_OK) {
        ESP_LOGW(TAG, "failed to get Wi-Fi RSSI: %s", esp_err_to_name(rssi_ret));
    }

    camera_fb_t *frame = NULL;
    ret = camera_driver_capture_frame(&frame);
    if (ret != ESP_OK) {
        return ret;
    }

    char meta_part[384] = {0};
    char image_header[192] = {0};
    char end_part[64] = {0};

    int meta_len = snprintf(
        meta_part,
        sizeof(meta_part),
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n"
        "%s\r\n"
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"rssi\"\r\n\r\n"
        "%d\r\n"
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"free_heap\"\r\n\r\n"
        "%" PRIu32 "\r\n",
        UPLOAD_BOUNDARY,
        APP_CONFIG_DEVICE_ID,
        UPLOAD_BOUNDARY,
        rssi_ret == ESP_OK ? rssi : 0,
        UPLOAD_BOUNDARY,
        esp_get_free_heap_size());
    int image_header_len = snprintf(
        image_header,
        sizeof(image_header),
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"image\"; filename=\"esp32.jpg\"\r\n"
        "Content-Type: image/jpeg\r\n\r\n",
        UPLOAD_BOUNDARY);
    int end_len = snprintf(end_part, sizeof(end_part), "\r\n--%s--\r\n", UPLOAD_BOUNDARY);

    if (meta_len < 0 || meta_len >= (int)sizeof(meta_part) ||
        image_header_len < 0 || image_header_len >= (int)sizeof(image_header) ||
        end_len < 0 || end_len >= (int)sizeof(end_part)) {
        ESP_LOGE(TAG, "multipart body buffer is too small");
        camera_driver_return_frame(frame);
        return ESP_ERR_NO_MEM;
    }

    int64_t content_length = meta_len + image_header_len + (int64_t)frame->len + end_len;
    esp_http_client_config_t config = {
        .url = url,
        .method = HTTP_METHOD_POST,
        .timeout_ms = APP_CONFIG_HTTP_TIMEOUT_MS,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (client == NULL) {
        ESP_LOGE(TAG, "failed to initialize HTTP client");
        camera_driver_return_frame(frame);
        return ESP_FAIL;
    }

    char content_type[96] = {0};
    (void)snprintf(
        content_type,
        sizeof(content_type),
        "multipart/form-data; boundary=%s",
        UPLOAD_BOUNDARY);
    esp_http_client_set_header(client, "Content-Type", content_type);
    if (strlen(APP_CONFIG_API_TOKEN) > 0) {
        esp_http_client_set_header(client, "X-API-Token", APP_CONFIG_API_TOKEN);
    }

    ret = esp_http_client_open(client, content_length);
    if (ret == ESP_OK) {
        ret = write_http_data(client, meta_part, meta_len);
    }
    if (ret == ESP_OK) {
        ret = write_http_data(client, image_header, image_header_len);
    }
    if (ret == ESP_OK) {
        ret = write_http_data(client, (const char *)frame->buf, frame->len);
    }
    if (ret == ESP_OK) {
        ret = write_http_data(client, end_part, end_len);
    }

    camera_driver_return_frame(frame);

    if (ret == ESP_OK) {
        int header_ret = esp_http_client_fetch_headers(client);
        if (header_ret < 0) {
            ESP_LOGW(TAG, "failed to fetch upload response headers");
            ret = ESP_FAIL;
        }
    }

    if (ret == ESP_OK) {
        int status_code = esp_http_client_get_status_code(client);
        int64_t response_length = esp_http_client_get_content_length(client);
        ESP_LOGI(
            TAG,
            "image uploaded, status=%d, image_len=%u, response_length=%" PRId64,
            status_code,
            (unsigned int)(content_length - meta_len - image_header_len - end_len),
            response_length);
        if (status_code < 200 || status_code >= 300) {
            ret = ESP_FAIL;
        } else {
            ret = handle_upload_response(client);
        }
    } else {
        ESP_LOGW(TAG, "image upload failed: %s", esp_err_to_name(ret));
    }

    esp_http_client_close(client);
    esp_http_client_cleanup(client);
    return ret;
}

/**
 * @brief 图片上传 FreeRTOS 任务。
 *
 * @param arg 任务参数，当前未使用。
 */
static void upload_task(void *arg)
{
    (void)arg;

    while (true) {
        if (wifi_manager_is_connected()) {
            (void)upload_image_once();
        } else {
            ESP_LOGI(TAG, "skip image upload, Wi-Fi disconnected");
        }

        vTaskDelay(pdMS_TO_TICKS(APP_CONFIG_UPLOAD_INTERVAL_MS));
    }
}

esp_err_t upload_client_start(void)
{
    if (s_upload_task_handle != NULL) {
        ESP_LOGW(TAG, "upload task already started");
        return ESP_OK;
    }

    BaseType_t result = xTaskCreate(
        upload_task,
        UPLOAD_TASK_NAME,
        UPLOAD_TASK_STACK_SIZE,
        NULL,
        UPLOAD_TASK_PRIORITY,
        &s_upload_task_handle);
    if (result != pdPASS) {
        ESP_LOGE(TAG, "failed to create upload task");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "upload task started, interval=%d ms", APP_CONFIG_UPLOAD_INTERVAL_MS);
    return ESP_OK;
}
