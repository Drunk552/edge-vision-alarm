"""健康检查接口。"""

from fastapi import APIRouter

from app.core.error_codes import SUCCESS
from app.detectors.factory import create_detector
from app.repositories.database import get_connection
from app.services.image_service import ImageService
from app.utils.time_utils import now_iso

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """检查服务、数据库和图片目录状态。"""

    database_status = "ok"
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
    except Exception:
        database_status = "error"

    image_dir_status = ImageService().image_dir_status()
    detector = create_detector()
    status = (
        "ok" if database_status == "ok" and image_dir_status == "ok" else "degraded"
    )
    return {
        "code": SUCCESS,
        "status": status,
        "model_loaded": detector.model_loaded,
        "database": database_status,
        "image_dir": image_dir_status,
        "timestamp": now_iso(),
        "message": "service healthy" if status == "ok" else "service degraded",
    }
