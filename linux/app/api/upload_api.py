"""图片上传接口。"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.error_codes import DATABASE_ERROR, IMAGE_SAVE_FAILED, PARAM_ERROR
from app.core.security import verify_api_token
from app.core.validation import validate_device_id, validate_free_heap, validate_rssi
from app.services.detection_service import DetectionService
from app.services.image_service import ImageValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_image(
    device_id: str = Form(...),
    image: UploadFile = File(...),
    rssi: int | None = Form(None),
    free_heap: int | None = Form(None),
    capture_time: str | None = Form(None),
    _: None = Depends(verify_api_token),
) -> dict:
    """接收 ESP32 上传的 JPEG 图片。"""

    if not device_id.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": PARAM_ERROR, "message": "missing device_id"},
        )

    normalized_device_id = validate_device_id(device_id)
    validate_rssi(rssi)
    validate_free_heap(free_heap)

    try:
        return await DetectionService().handle_upload(
            device_id=normalized_device_id,
            image=image,
            rssi=rssi,
            free_heap=free_heap,
        )
    except ImageValidationError as exc:
        raise HTTPException(
            status_code=400, detail={"code": exc.code, "message": exc.message}
        ) from exc
    except OSError as exc:
        logger.exception("image save failed | device_id=%s", device_id)
        raise HTTPException(
            status_code=500,
            detail={"code": IMAGE_SAVE_FAILED, "message": "image save failed"},
        ) from exc
    except Exception as exc:
        logger.exception("upload handling failed | device_id=%s", device_id)
        raise HTTPException(
            status_code=500,
            detail={"code": DATABASE_ERROR, "message": "upload handling failed"},
        ) from exc
