/**
 * @file alarm_gpio.c
 * @brief ESP32 本地 LED 告警联动模块。
 */

#include "alarm_gpio.h"

#include "app_config.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"

#define ALARM_TASK_NAME "alarm_task"
#define ALARM_TASK_STACK_SIZE 3072
#define ALARM_TASK_PRIORITY 4
#define ALARM_QUEUE_LENGTH 3
#define ALARM_QUEUE_ITEM_SIZE sizeof(uint8_t)

static const char *TAG = "alarm_gpio";
static QueueHandle_t s_alarm_queue = NULL;
static TaskHandle_t s_alarm_task_handle = NULL;

/**
 * @brief 设置告警 LED 电平。
 *
 * @param enabled true 表示点亮 LED，false 表示熄灭 LED。
 */
static void set_alarm_led(bool enabled)
{
    int level = enabled ? APP_CONFIG_ALARM_LED_ACTIVE_LEVEL : !APP_CONFIG_ALARM_LED_ACTIVE_LEVEL;
    gpio_set_level(APP_CONFIG_ALARM_LED_GPIO, level);
}

/**
 * @brief 执行一次 LED 闪烁告警。
 */
static void run_led_alarm(void)
{
    int elapsed_ms = 0;

    ESP_LOGI(TAG, "local LED alarm started");
    while (elapsed_ms < APP_CONFIG_ALARM_DURATION_MS) {
        set_alarm_led(true);
        vTaskDelay(pdMS_TO_TICKS(APP_CONFIG_ALARM_BLINK_INTERVAL_MS));
        elapsed_ms += APP_CONFIG_ALARM_BLINK_INTERVAL_MS;

        set_alarm_led(false);
        vTaskDelay(pdMS_TO_TICKS(APP_CONFIG_ALARM_BLINK_INTERVAL_MS));
        elapsed_ms += APP_CONFIG_ALARM_BLINK_INTERVAL_MS;
    }

    set_alarm_led(false);
    ESP_LOGI(TAG, "local LED alarm finished");
}

/**
 * @brief 告警联动 FreeRTOS 任务。
 *
 * @param arg 任务参数，当前未使用。
 */
static void alarm_task(void *arg)
{
    (void)arg;

    uint8_t event = 0;
    while (true) {
        if (xQueueReceive(s_alarm_queue, &event, portMAX_DELAY) == pdTRUE) {
            run_led_alarm();
        }
    }
}

esp_err_t alarm_gpio_init(void)
{
    if (s_alarm_task_handle != NULL) {
        ESP_LOGW(TAG, "alarm GPIO already initialized");
        return ESP_OK;
    }

    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << APP_CONFIG_ALARM_LED_GPIO,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t ret = gpio_config(&io_conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "failed to configure alarm LED GPIO: %s", esp_err_to_name(ret));
        return ret;
    }
    set_alarm_led(false);

    s_alarm_queue = xQueueCreate(ALARM_QUEUE_LENGTH, ALARM_QUEUE_ITEM_SIZE);
    if (s_alarm_queue == NULL) {
        ESP_LOGE(TAG, "failed to create alarm queue");
        return ESP_ERR_NO_MEM;
    }

    BaseType_t result = xTaskCreate(
        alarm_task,
        ALARM_TASK_NAME,
        ALARM_TASK_STACK_SIZE,
        NULL,
        ALARM_TASK_PRIORITY,
        &s_alarm_task_handle);
    if (result != pdPASS) {
        ESP_LOGE(TAG, "failed to create alarm task");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(
        TAG,
        "alarm GPIO initialized, led_gpio=%d, active_level=%d",
        APP_CONFIG_ALARM_LED_GPIO,
        APP_CONFIG_ALARM_LED_ACTIVE_LEVEL);
    return ESP_OK;
}

esp_err_t alarm_gpio_trigger(void)
{
    if (s_alarm_queue == NULL) {
        ESP_LOGE(TAG, "alarm GPIO is not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    uint8_t event = 1;
    if (xQueueSend(s_alarm_queue, &event, 0) != pdTRUE) {
        ESP_LOGW(TAG, "alarm queue is full, drop duplicated alarm");
        return ESP_ERR_TIMEOUT;
    }

    ESP_LOGI(TAG, "local LED alarm triggered");
    return ESP_OK;
}
