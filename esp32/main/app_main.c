/**
 * @file app_main.c
 * @brief ESP32-S3-CAM 固件入口。
 */

#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_log.h"
#include "esp_system.h"
#include "alarm_gpio.h"
#include "camera_driver.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "heartbeat.h"
#include "upload_client.h"
#include "wifi_manager.h"

static const char *TAG = "edge_vision_alarm";

void app_main(void)
{
    esp_chip_info_t chip_info;
    uint32_t flash_size = 0;

    esp_chip_info(&chip_info);
    esp_err_t ret = esp_flash_get_size(NULL, &flash_size);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "failed to get flash size: %s", esp_err_to_name(ret));
    }

    ESP_LOGI(TAG, "edge vision alarm firmware start");
    ESP_LOGI(TAG, "chip cores: %d", chip_info.cores);
    ESP_LOGI(TAG, "chip revision: %d", chip_info.revision);
    ESP_LOGI(TAG, "flash size: %lu MB", (unsigned long)(flash_size / (1024 * 1024)));
    ESP_LOGI(TAG, "free heap: %lu bytes", (unsigned long)esp_get_free_heap_size());

    // 初始化本地 LED 告警模块。
    ret = alarm_gpio_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "failed to initialize alarm GPIO: %s", esp_err_to_name(ret));
    }

    // 初始化 Wi-Fi STA 联网。
    ret = wifi_manager_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "failed to initialize Wi-Fi: %s", esp_err_to_name(ret));
    }

    // 启动设备心跳上报任务。
    ret = heartbeat_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "failed to start heartbeat task: %s", esp_err_to_name(ret));
    }

    // 初始化摄像头并启动图片上传任务。
    ret = camera_driver_init();
    if (ret == ESP_OK) {
        ret = upload_client_start();
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "failed to start upload task: %s", esp_err_to_name(ret));
        }
    } else {
        ESP_LOGE(TAG, "camera initialization skipped upload task: %s", esp_err_to_name(ret));
    }

    while (true) {
        if (wifi_manager_is_connected()) {
            int8_t rssi = 0;
            if (wifi_manager_get_rssi(&rssi) == ESP_OK) {
                ESP_LOGI(
                    TAG,
                    "system heartbeat, Wi-Fi connected, RSSI: %d dBm, free heap: %lu bytes",
                    rssi,
                    (unsigned long)esp_get_free_heap_size());
            } else {
                ESP_LOGI(
                    TAG,
                    "system heartbeat, Wi-Fi connected, free heap: %lu bytes",
                    (unsigned long)esp_get_free_heap_size());
            }
        } else {
            ESP_LOGI(
                TAG,
                "system heartbeat, Wi-Fi disconnected, free heap: %lu bytes",
                (unsigned long)esp_get_free_heap_size());
        }
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}
