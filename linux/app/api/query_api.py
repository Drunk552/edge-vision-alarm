"""数据查询接口。"""

from fastapi import APIRouter, HTTPException

from app.core.error_codes import PARAM_ERROR, SUCCESS
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.device_repository import DeviceRepository
from app.utils.time_utils import now_iso

router = APIRouter(prefix="/api", tags=["query"])


def _validate_pagination(page: int, page_size: int) -> None:
    """校验分页参数。"""

    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "invalid pagination"},
        )


@router.get("/latest")
def get_latest(device_id: str | None = None) -> dict:
    """查询最新一条检测事件。"""

    event = AlarmRepository().get_latest_event(device_id=device_id)
    if event is None:
        return {"code": SUCCESS, "message": "no data", "data": None}

    top_target = {
        "class": event["target_class"],
        "confidence": event["confidence"],
        "box": None,
    }
    return {
        "code": SUCCESS,
        "message": "ok",
        "event_id": event["event_id"],
        "device_id": event["device_id"],
        "alarm": event["alarm_status"] == "alarm",
        "alarm_level": event["alarm_level"],
        "alarm_action": "none",
        "target_count": 0 if event["target_class"] == "none" else 1,
        "top_target": None if event["target_class"] == "none" else top_target,
        "result_image_path": event["result_image_path"],
        "raw_image_path": event["raw_image_path"],
        "created_at": event["created_at"],
    }


@router.get("/alarms")
def list_alarms(
    device_id: str | None = None,
    target_class: str | None = None,
    handled: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页查询历史检测事件。"""

    _validate_pagination(page, page_size)
    if handled not in {None, 0, 1}:
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "invalid handled"},
        )
    total, items = AlarmRepository().list_events(
        device_id=device_id,
        target_class=target_class,
        handled=handled,
        page=page,
        page_size=page_size,
    )
    return {
        "code": SUCCESS,
        "message": "ok",
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/devices")
def list_devices(
    device_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页查询设备状态。"""

    _validate_pagination(page, page_size)
    total, items = DeviceRepository().list_devices(
        device_id=device_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return {
        "code": SUCCESS,
        "message": "ok",
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.post("/alarms/{event_id}/handle")
def handle_alarm(event_id: int) -> dict:
    """将告警事件标记为已处理。"""

    if event_id < 1:
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "invalid event_id"},
        )

    updated = AlarmRepository().mark_handled(event_id=event_id, handled_at=now_iso())
    if not updated:
        raise HTTPException(
            status_code=404,
            detail={"code": 4004, "message": "event not found"},
        )

    return {"code": SUCCESS, "message": "alarm handled", "event_id": event_id}
