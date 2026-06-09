/**
 * @file upload_client.h
 * @brief ESP32 图片上传 HTTP 客户端模块。
 */

#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 启动图片上传任务。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t upload_client_start(void);

#ifdef __cplusplus
}
#endif
