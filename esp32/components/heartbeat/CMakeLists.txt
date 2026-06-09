idf_component_register(
    SRCS "heartbeat.c"
    INCLUDE_DIRS "."
    REQUIRES config esp_http_client esp_system wifi
)
