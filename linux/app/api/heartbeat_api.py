"""设备心跳接口。"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.error_codes import PARAM_ERROR, SUCCESS
from app.core.security import verify_api_token
from app.core.validation import (
    validate_device_id,
    validate_device_status,
    validate_free_heap,
    validate_rssi,
)
from app.models.schemas import HeartbeatRequest
from app.repositories.device_repository import DeviceRepository
from app.utils.time_utils import now_iso

router = APIRouter(prefix="/api", tags=["heartbeat"])


@router.post("/heartbeat")
def heartbeat(
    payload: HeartbeatRequest, _: None = Depends(verify_api_token)
) -> dict:
    """接收 ESP32 设备心跳。"""

    if not payload.device_id.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "missing device_id"},
        )

    normalized_device_id = validate_device_id(payload.device_id)
    validate_rssi(payload.rssi)
    validate_free_heap(payload.free_heap)
    validate_device_status(payload.status)

    updated_at = payload.heartbeat_time or now_iso()
    DeviceRepository().upsert_status(
        device_id=normalized_device_id,
        status=payload.status,
        updated_at=updated_at,
        rssi=payload.rssi,
        free_heap=payload.free_heap,
    )
    return {
        "code": SUCCESS,
        "message": "heartbeat accepted",
        "device_status": payload.status,
        "last_seen": updated_at,
    }
