#!/usr/bin/env bash

# 加载 ESP-IDF 开发环境。请使用：source start_esp32_env.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "请使用 source start_esp32_env.sh，这样 idf.py 环境变量会保留在当前终端。"
    exit 1
fi

IDF_EXPORT="/home/drunk22/.espressif/v6.0.1/esp-idf/export.sh"

if [[ ! -f "${IDF_EXPORT}" ]]; then
    echo "未找到 ESP-IDF export.sh：${IDF_EXPORT}"
    return 1
fi

source "${IDF_EXPORT}" || return 1

echo "ESP-IDF 环境已加载。"
idf.py --version

