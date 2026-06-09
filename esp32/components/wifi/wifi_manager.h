/**
 * @file wifi_manager.h
 * @brief ESP32 Wi-Fi STA 联网管理模块。
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化 Wi-Fi STA 模式并开始连接。
 *
 * @return ESP_OK 表示初始化流程启动成功。
 */
esp_err_t wifi_manager_init(void);

/**
 * @brief 判断 Wi-Fi 是否已经获取 IP。
 *
 * @return true 表示网络已连接并获取 IP。
 */
bool wifi_manager_is_connected(void);

/**
 * @brief 获取当前 Wi-Fi RSSI。
 *
 * @param rssi 输出 RSSI，单位 dBm。
 * @return ESP_OK 表示获取成功。
 */
esp_err_t wifi_manager_get_rssi(int8_t *rssi);

#ifdef __cplusplus
}
#endif
