/**
 * @file heartbeat.h
 * @brief ESP32 设备心跳上报模块。
 */

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 启动心跳上报任务。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t heartbeat_start(void);

#ifdef __cplusplus
}
#endif
