/**
 * @file camera_driver.c
 * @brief ESP32-S3-CAM 摄像头初始化与图像采集模块。
 */

#include "camera_driver.h"

#include "app_config.h"
#include "esp_camera.h"
#include "esp_log.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sensor.h"

#define CAMERA_TASK_NAME "camera_task"
#define CAMERA_TASK_STACK_SIZE 4096
#define CAMERA_TASK_PRIORITY 4
#define CAMERA_XCLK_FREQ_HZ 20000000

static const char *TAG = "camera_driver";

static bool s_camera_initialized = false;
static TaskHandle_t s_camera_task_handle = NULL;

/**
 * @brief 获取配置中的摄像头分辨率。
 *
 * @return esp32-camera 组件使用的帧尺寸枚举。
 */
static framesize_t get_camera_frame_size(void)
{
#if CONFIG_EDGE_CAMERA_FRAME_SIZE_QVGA
    return FRAMESIZE_QVGA;
#else
    return FRAMESIZE_VGA;
#endif
}

/**
 * @brief 获取摄像头配置。
 *
 * @return esp32-camera 初始化配置。
 */
static camera_config_t get_camera_config(void)
{
    camera_config_t config = {
        .pin_pwdn = APP_CONFIG_CAMERA_PWDN_PIN,
        .pin_reset = APP_CONFIG_CAMERA_RESET_PIN,
        .pin_xclk = APP_CONFIG_CAMERA_XCLK_PIN,
        .pin_sccb_sda = APP_CONFIG_CAMERA_SIOD_PIN,
        .pin_sccb_scl = APP_CONFIG_CAMERA_SIOC_PIN,
        .pin_d7 = APP_CONFIG_CAMERA_D7_PIN,
        .pin_d6 = APP_CONFIG_CAMERA_D6_PIN,
        .pin_d5 = APP_CONFIG_CAMERA_D5_PIN,
        .pin_d4 = APP_CONFIG_CAMERA_D4_PIN,
        .pin_d3 = APP_CONFIG_CAMERA_D3_PIN,
        .pin_d2 = APP_CONFIG_CAMERA_D2_PIN,
        .pin_d1 = APP_CONFIG_CAMERA_D1_PIN,
        .pin_d0 = APP_CONFIG_CAMERA_D0_PIN,
        .pin_vsync = APP_CONFIG_CAMERA_VSYNC_PIN,
        .pin_href = APP_CONFIG_CAMERA_HREF_PIN,
        .pin_pclk = APP_CONFIG_CAMERA_PCLK_PIN,
        .xclk_freq_hz = CAMERA_XCLK_FREQ_HZ,
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = get_camera_frame_size(),
        .jpeg_quality = APP_CONFIG_CAMERA_JPEG_QUALITY,
        .fb_count = 1,
        .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
        .fb_location = CAMERA_FB_IN_PSRAM,
    };

    return config;
}

esp_err_t camera_driver_init(void)
{
    if (s_camera_initialized) {
        ESP_LOGW(TAG, "camera already initialized");
        return ESP_OK;
    }

    ESP_LOGI(TAG, "initialize camera driver");
    camera_config_t config = get_camera_config();
    esp_err_t ret = esp_camera_init(&config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "camera init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    sensor_t *sensor = esp_camera_sensor_get();
    if (sensor != NULL) {
        ESP_LOGI(TAG, "camera sensor detected, pid=0x%04x", sensor->id.PID);
    }

    s_camera_initialized = true;
    ESP_LOGI(TAG, "camera init success");
    return ESP_OK;
}

esp_err_t camera_driver_capture_frame(camera_fb_t **frame)
{
    if (frame == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    *frame = NULL;
    if (!s_camera_initialized) {
        ESP_LOGE(TAG, "camera capture requires initialized camera");
        return ESP_ERR_INVALID_STATE;
    }

    camera_fb_t *captured_frame = esp_camera_fb_get();
    if (captured_frame == NULL) {
        ESP_LOGE(TAG, "camera capture failed");
        return ESP_FAIL;
    }

    *frame = captured_frame;
    return ESP_OK;
}

void camera_driver_return_frame(camera_fb_t *frame)
{
    if (frame != NULL) {
        esp_camera_fb_return(frame);
    }
}

/**
 * @brief 摄像头单帧采集测试任务。
 *
 * @param arg 任务参数，当前未使用。
 */
static void camera_test_task(void *arg)
{
    (void)arg;

    while (true) {
        camera_fb_t *frame = NULL;
        esp_err_t ret = camera_driver_capture_frame(&frame);
        if (ret == ESP_OK) {
            ESP_LOGI(
                TAG,
                "camera frame captured, len=%u bytes, width=%u, height=%u, format=%u, free_heap=%lu",
                (unsigned int)frame->len,
                (unsigned int)frame->width,
                (unsigned int)frame->height,
                (unsigned int)frame->format,
                (unsigned long)esp_get_free_heap_size());

            // 阶段九只验证采集能力，获取到帧后立即释放，避免内存泄漏。
            camera_driver_return_frame(frame);
        }

        vTaskDelay(pdMS_TO_TICKS(APP_CONFIG_CAMERA_CAPTURE_INTERVAL_MS));
    }
}

esp_err_t camera_driver_start_test_task(void)
{
    if (!s_camera_initialized) {
        ESP_LOGE(TAG, "camera test task requires initialized camera");
        return ESP_ERR_INVALID_STATE;
    }

    if (s_camera_task_handle != NULL) {
        ESP_LOGW(TAG, "camera test task already started");
        return ESP_OK;
    }

    BaseType_t result = xTaskCreate(
        camera_test_task,
        CAMERA_TASK_NAME,
        CAMERA_TASK_STACK_SIZE,
        NULL,
        CAMERA_TASK_PRIORITY,
        &s_camera_task_handle);
    if (result != pdPASS) {
        ESP_LOGE(TAG, "failed to create camera test task");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(
        TAG,
        "camera test task started, interval=%d ms",
        APP_CONFIG_CAMERA_CAPTURE_INTERVAL_MS);
    return ESP_OK;
}
