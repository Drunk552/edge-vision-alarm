"""检测器工厂模块。"""

import logging

from app.core.config import settings
from app.detectors.base_detector import BaseDetector, EmptyDetector
from app.detectors.yolov8_detector import Yolov8Detector

logger = logging.getLogger(__name__)


def create_detector() -> BaseDetector:
    """根据模型文件和依赖情况创建检测器。"""

    if not settings.model_path.exists():
        logger.warning(
            "model file not found, use empty detector | path=%s", settings.model_path
        )
        return EmptyDetector()

    detector = Yolov8Detector()
    try:
        detector.load_model()
    except Exception:
        logger.exception("failed to load YOLOv8 model, use empty detector")
        return EmptyDetector()
    return detector
