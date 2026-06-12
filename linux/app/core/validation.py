"""接口参数校验工具。"""

import re

from fastapi import HTTPException

from app.core.error_codes import PARAM_ERROR

DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
VALID_DEVICE_STATUS = {"online", "offline", "error"}


def validate_device_id(device_id: str) -> str:
    """校验并返回规范化后的 device_id。"""

    normalized = device_id.strip()
    if not DEVICE_ID_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=400,
            detail={
                "code": PARAM_ERROR,
                "message": "device_id must be 1-64 chars: letters, digits, _ or -",
            },
        )
    return normalized


def validate_rssi(rssi: int | None) -> None:
    """校验 Wi-Fi RSSI 范围。"""

    if rssi is None:
        return
    if rssi < -120 or rssi > 0:
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "rssi must be between -120 and 0"},
        )


def validate_free_heap(free_heap: int | None) -> None:
    """校验剩余堆内存字段。"""

    if free_heap is None:
        return
    if free_heap < 0:
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "free_heap must be non-negative"},
        )


def validate_device_status(status: str) -> None:
    """校验设备状态字段。"""

    if status not in VALID_DEVICE_STATUS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": PARAM_ERROR,
                "message": "status must be online, offline or error",
            },
        )
