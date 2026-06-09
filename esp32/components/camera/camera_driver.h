/**
 * @file camera_driver.h
 * @brief ESP32-S3-CAM 摄像头初始化与图像采集模块。
 */

#pragma once

#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"
#include "esp_camera.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化摄像头模块。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t camera_driver_init(void);

/**
 * @brief 获取一帧摄像头 JPEG 图像。
 *
 * @param frame 输出图像帧指针，使用完成后必须调用 camera_driver_return_frame 释放。
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t camera_driver_capture_frame(camera_fb_t **frame);

/**
 * @brief 释放摄像头图像帧。
 *
 * @param frame 需要释放的图像帧指针。
 */
void camera_driver_return_frame(camera_fb_t *frame);

/**
 * @brief 启动摄像头单帧采集测试任务。
 *
 * @return 成功返回 ESP_OK，失败返回对应错误码。
 */
esp_err_t camera_driver_start_test_task(void);

#ifdef __cplusplus
}
#endif
