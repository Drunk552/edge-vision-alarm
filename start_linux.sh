#!/usr/bin/env bash

# 快速启动 Linux 服务端。请使用：source start_linux.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "请使用 source start_linux.sh 启动，这样虚拟环境会保留在当前终端。"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_DIR="${PROJECT_ROOT}/linux"
VENV_DIR="${LINUX_DIR}/.venv"

cd "${LINUX_DIR}" || return 1

if [[ ! -d "${VENV_DIR}" ]]; then
    echo "[1/5] 创建 Python 虚拟环境..."
    python3 -m venv .venv || return 1
else
    echo "[1/5] Python 虚拟环境已存在。"
fi

echo "[2/5] 激活 Python 虚拟环境..."
source "${VENV_DIR}/bin/activate" || return 1

echo "[3/5] 安装/更新开发依赖..."
make install-dev || return 1

echo "[4/5] 初始化 SQLite 数据库..."
make init-db || return 1

echo "[5/5] 启动 FastAPI 服务..."
make run

