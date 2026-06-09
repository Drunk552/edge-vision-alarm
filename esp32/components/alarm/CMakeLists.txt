idf_component_register(
    SRCS "alarm_gpio.c"
    INCLUDE_DIRS "."
    REQUIRES config esp_driver_gpio
)
