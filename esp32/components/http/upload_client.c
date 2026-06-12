/**
 * @file upload_client.c
 * @brief ESP32 图片上传 HTTP 客户端模块。
 */

#include "upload_client.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "alarm_gpio.h"
#include "app_config.h"
#include "camera_driver.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "wifi_manager.h"

#define UPLOAD_TASK_NAME "upload_task"
#define UPLOAD_TASK_STACK_SIZE 6144
#define UPLOAD_TASK_PRIORITY 4
#define UPLOAD_URL_MAX_LEN 160
#define UPLOAD_RESPONSE_BUFFER_SIZE 512
#define UPLOAD_BOUNDARY "----edge-vision-alarm-boundary"
#define UPLOAD_BACKOFF_FIRST_THRESHOLD 3
#define UPLOAD_BACKOFF_SECOND_THRESHOLD 6
#define UPLOAD_BACKOFF_MAX_DELAY_MS 60000
#define UPLOAD_ALARM_FIELD_MAX_LEN 24

static const char *TAG = "upload_client";
static TaskHandle_t s_upload_task_handle = NULL;
static int s_upload_fail_count = 0;

typedef struct {
    bool alarm;
    int event_id;
    char alarm_status[UPLOAD_ALARM_FIELD_MAX_LEN];
    char alarm_action[UPLOAD_ALARM_FIELD_MAX_LEN];
} upload_response_t;

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
 * @brief 定位 JSON 字段值起始位置。
 *
 * @param json JSON 字符串。
 * @param key 字段名。
 * @return 字段值起始位置，未找到时返回 NULL。
 */
static const char *find_json_value(const char *json, const char *key)
{
    if (json == NULL || key == NULL) {
        return NULL;
    }

    char pattern[48] = {0};
    int written = snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    if (written < 0 || written >= (int)sizeof(pattern)) {
        return NULL;
    }

    const char *position = strstr(json, pattern);
    if (position == NULL) {
        return NULL;
    }

    position = strchr(position + written, ':');
    if (position == NULL) {
        return NULL;
    }
    position++;
    while (*position == ' ' || *position == '\t' || *position == '\r' || *position == '\n') {
        position++;
    }
    return position;
}

/**
 * @brief 解析 JSON bool 字段。
 *
 * @param json JSON 字符串。
 * @param key 字段名。
 * @param output 输出 bool。
 */
static void parse_json_bool(const char *json, const char *key, bool *output)
{
    const char *value = find_json_value(json, key);
    if (value == NULL || output == NULL) {
        return;
    }

    if (strncmp(value, "true", 4) == 0) {
        *output = true;
    } else if (strncmp(value, "false", 5) == 0) {
        *output = false;
    }
}

/**
 * @brief 解析 JSON int 字段。
 *
 * @param json JSON 字符串。
 * @param key 字段名。
 * @param output 输出整数。
 */
static void parse_json_int(const char *json, const char *key, int *output)
{
    const char *value = find_json_value(json, key);
    if (value == NULL || output == NULL) {
        return;
    }

    int parsed = 0;
    if (sscanf(value, "%d", &parsed) == 1) {
        *output = parsed;
    }
}

/**
 * @brief 解析 JSON 字符串字段。
 *
 * @param json JSON 字符串。
 * @param key 字段名。
 * @param output 输出缓冲区。
 * @param output_len 输出缓冲区长度。
 */
static void parse_json_string(const char *json, const char *key, char *output, size_t output_len)
{
    const char *value = find_json_value(json, key);
    if (value == NULL || output == NULL || output_len == 0 || *value != '"') {
        return;
    }

    value++;
    size_t index = 0;
    while (*value != '\0' && *value != '"' && index + 1 < output_len) {
        output[index++] = *value++;
    }
    output[index] = '\0';
}

/**
 * @brief 解析上传响应 JSON。
 *
 * @param json 服务端响应字符串。
 * @param output 解析结果。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t parse_upload_response(const char *json, upload_response_t *output)
{
    if (json == NULL || output == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    memset(output, 0, sizeof(*output));
    output->event_id = -1;
    strlcpy(output->alarm_status, "unknown", sizeof(output->alarm_status));
    strlcpy(output->alarm_action, "none", sizeof(output->alarm_action));

    parse_json_bool(json, "alarm", &output->alarm);
    parse_json_int(json, "event_id", &output->event_id);
    parse_json_string(json, "alarm_status", output->alarm_status, sizeof(output->alarm_status));
    parse_json_string(json, "alarm_action", output->alarm_action, sizeof(output->alarm_action));
    return ESP_OK;
}

/**
 * @brief 判断告警动作是否需要本地 LED 联动。
 *
 * @param action 服务端返回的 alarm_action。
 * @return true 表示需要触发 LED。
 */
static bool alarm_action_needs_led(const char *action)
{
    if (action == NULL) {
        return false;
    }

    return strcmp(action, "beep_led") == 0 || strcmp(action, "led") == 0;
}

/**
 * @brief 根据解析后的响应执行本地动作。
 *
 * @param response 解析后的上传响应。
 */
static void handle_parsed_upload_response(const upload_response_t *response)
{
    if (response == NULL) {
        return;
    }

    ESP_LOGI(
        TAG,
        "upload response parsed, alarm=%s, status=%s, action=%s, event_id=%d",
        response->alarm ? "true" : "false",
        response->alarm_status,
        response->alarm_action,
        response->event_id);

    if (response->alarm && alarm_action_needs_led(response->alarm_action)) {
        esp_err_t ret = alarm_gpio_trigger();
        if (ret != ESP_OK) {
            ESP_LOGW(TAG, "failed to trigger local alarm: %s", esp_err_to_name(ret));
        }
    }
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
    upload_response_t parsed_response;
    esp_err_t ret = parse_upload_response(response, &parsed_response);
    if (ret != ESP_OK) {
        return ret;
    }

    handle_parsed_upload_response(&parsed_response);
    return ESP_OK;
}

/**
 * @brief 记录上传成功并重置失败计数。
 */
static void record_upload_success(void)
{
    if (s_upload_fail_count > 0) {
        ESP_LOGI(TAG, "upload recovered after %d failure(s)", s_upload_fail_count);
    }
    s_upload_fail_count = 0;
}

/**
 * @brief 记录上传失败。
 *
 * @param ret 上传失败错误码。
 */
static void record_upload_failure(esp_err_t ret)
{
    s_upload_fail_count++;
    ESP_LOGW(
        TAG,
        "image upload failed: %s, fail_count=%d",
        esp_err_to_name(ret),
        s_upload_fail_count);
}

/**
 * @brief 获取当前上传任务延迟。
 *
 * @return FreeRTOS tick 延迟。
 */
static TickType_t get_upload_delay_ticks(void)
{
    int delay_ms = APP_CONFIG_UPLOAD_INTERVAL_MS;
    if (s_upload_fail_count >= UPLOAD_BACKOFF_SECOND_THRESHOLD) {
        delay_ms *= 4;
    } else if (s_upload_fail_count >= UPLOAD_BACKOFF_FIRST_THRESHOLD) {
        delay_ms *= 2;
    }

    if (delay_ms > UPLOAD_BACKOFF_MAX_DELAY_MS) {
        delay_ms = UPLOAD_BACKOFF_MAX_DELAY_MS;
    }

    if (delay_ms != APP_CONFIG_UPLOAD_INTERVAL_MS) {
        ESP_LOGI(TAG, "upload backoff active, delay=%d ms", delay_ms);
    }
    return pdMS_TO_TICKS(delay_ms);
}

/**
 * @brief 执行一次图片上传。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
static esp_err_t upload_image_once(void)
{
    int64_t start_us = esp_timer_get_time();
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
            "image uploaded, status=%d, image_len=%u, response_length=%" PRId64
            ", elapsed=%" PRId64 " ms",
            status_code,
            (unsigned int)(content_length - meta_len - image_header_len - end_len),
            response_length,
            (esp_timer_get_time() - start_us) / 1000);
        if (status_code < 200 || status_code >= 300) {
            ret = ESP_FAIL;
        } else {
            ret = handle_upload_response(client);
        }
    }

    esp_http_client_close(client);
    esp_http_client_cleanup(client);

    if (ret == ESP_OK) {
        record_upload_success();
    } else {
        ESP_LOGW(
            TAG,
            "upload attempt elapsed=%" PRId64 " ms",
            (esp_timer_get_time() - start_us) / 1000);
    }
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
            esp_err_t ret = upload_image_once();
            if (ret != ESP_OK) {
                record_upload_failure(ret);
            }
        } else {
            ESP_LOGI(TAG, "skip image upload, Wi-Fi disconnected");
        }

        vTaskDelay(get_upload_delay_ticks());
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
