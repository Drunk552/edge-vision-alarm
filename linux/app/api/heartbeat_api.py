"""设备心跳接口。"""

from fastapi import APIRouter, HTTPException

from app.core.error_codes import PARAM_ERROR, SUCCESS
from app.models.schemas import HeartbeatRequest
from app.repositories.device_repository import DeviceRepository
from app.utils.time_utils import now_iso

router = APIRouter(prefix="/api", tags=["heartbeat"])


@router.post("/heartbeat")
def heartbeat(payload: HeartbeatRequest) -> dict:
    """接收 ESP32 设备心跳。"""

    if not payload.device_id.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "missing device_id"},
        )

    updated_at = payload.heartbeat_time or now_iso()
    DeviceRepository().upsert_status(
        device_id=payload.device_id.strip(),
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
