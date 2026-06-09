idf_component_register(
    SRCS "upload_client.c"
    INCLUDE_DIRS "."
    REQUIRES alarm camera config esp_http_client esp_system wifi
)
