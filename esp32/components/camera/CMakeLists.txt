idf_component_register(
    SRCS "camera_driver.c"
    INCLUDE_DIRS "."
    REQUIRES config esp32-camera esp_psram
)
