#!/usr/bin/env bash

# 加载 ESP-IDF 开发环境。请使用：source start_esp32_env.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "请使用 source start_esp32_env.sh，这样 idf.py 环境变量会保留在当前终端。"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IDF_EXPORT=""

if [[ -n "${IDF_PATH:-}" && -f "${IDF_PATH}/export.sh" ]]; then
    IDF_EXPORT="${IDF_PATH}/export.sh"
fi

if [[ -z "${IDF_EXPORT}" ]]; then
    for candidate in \
        "${HOME}/.espressif/v6.0.1/esp-idf/export.sh" \
        "${HOME}/esp/esp-idf/export.sh" \
        "${HOME}/esp-idf/export.sh"; do
        if [[ -f "${candidate}" ]]; then
            IDF_EXPORT="${candidate}"
            break
        fi
    done
fi

if [[ -z "${IDF_EXPORT}" ]]; then
    IDF_EXPORT="$(find "${HOME}/.espressif" "${HOME}/esp" "${HOME}" \
        -path "*/esp-idf/export.sh" -type f 2>/dev/null | head -n 1)"
fi

if [[ -z "${IDF_EXPORT}" || ! -f "${IDF_EXPORT}" ]]; then
    echo "未找到 ESP-IDF export.sh。"
    echo "请先确认 ESP-IDF 安装位置，例如："
    echo "  find ~/.espressif ~/esp ~ -path '*/esp-idf/export.sh' -type f 2>/dev/null"
    return 1
fi

source "${IDF_EXPORT}" || return 1

echo "ESP-IDF 环境已加载。"
echo "IDF_EXPORT=${IDF_EXPORT}"
idf.py --version
