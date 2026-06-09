idf_component_register(
    SRCS "app_main.c"
    INCLUDE_DIRS "."
    REQUIRES alarm camera heartbeat http spi_flash wifi
)
