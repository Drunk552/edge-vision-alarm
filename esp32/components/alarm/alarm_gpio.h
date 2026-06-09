/**
 * @file alarm_gpio.h
 * @brief ESP32 本地 LED 告警联动模块。
 */

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化告警 GPIO 模块并启动告警任务。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t alarm_gpio_init(void);

/**
 * @brief 触发一次本地 LED 告警。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t alarm_gpio_trigger(void);

#ifdef __cplusplus
}
#endif
