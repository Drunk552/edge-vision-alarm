"""上传检测业务编排模块。"""

import logging
from pathlib import Path

from fastapi import UploadFile

from app.detectors.base_detector import BaseDetector
from app.detectors.factory import create_detector
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.target_repository import TargetRepository
from app.rules.alarm_rule_engine import AlarmRuleEngine
from app.services.image_service import ImageService
from app.utils.time_utils import now_iso

logger = logging.getLogger(__name__)


class DetectionService:
    """编排图片上传、保存和事件记录流程。"""

    def __init__(
        self,
        image_service: ImageService | None = None,
        alarm_repository: AlarmRepository | None = None,
        device_repository: DeviceRepository | None = None,
        target_repository: TargetRepository | None = None,
        detector: BaseDetector | None = None,
        alarm_rule_engine: AlarmRuleEngine | None = None,
    ) -> None:
        self.image_service = image_service or ImageService()
        self.alarm_repository = alarm_repository or AlarmRepository()
        self.device_repository = device_repository or DeviceRepository()
        self.target_repository = target_repository or TargetRepository()
        self.detector = detector or create_detector()
        self.alarm_rule_engine = alarm_rule_engine or AlarmRuleEngine()

    async def handle_upload(
        self,
        device_id: str,
        image: UploadFile,
        rssi: int | None = None,
        free_heap: int | None = None,
    ) -> dict:
        """处理 ESP32 图片上传请求。"""

        created_at = now_iso()
        raw_path = await self.image_service.save_upload(device_id, image)
        targets = self.detector.detect(str(raw_path))
        decision = self.alarm_rule_engine.evaluate(device_id, targets)
        result_path = self.image_service.save_result_image(raw_path, targets)
        top_target = self._top_target(targets)
        self.device_repository.upsert_status(
            device_id=device_id,
            status="online",
            updated_at=created_at,
            rssi=rssi,
            free_heap=free_heap,
        )
        event_id = self.alarm_repository.create_event(
            device_id=device_id,
            raw_image_path=self._relative_path(raw_path),
            result_image_path=self._relative_path(result_path) if result_path else None,
            created_at=created_at,
            event_type=decision["event_type"],
            alarm_level=decision["alarm_level"],
            target_class=top_target["class"] if top_target else "none",
            confidence=top_target["confidence"] if top_target else None,
            alarm_status=decision["alarm_status"],
        )
        self.target_repository.create_targets(event_id, targets)
        logger.info(
            "image upload success | device_id=%s | event_id=%s | targets=%s | alarm=%s",
            device_id,
            event_id,
            len(targets),
            decision["alarm"],
        )
        return {
            "code": 0,
            "message": "upload accepted",
            "alarm": decision["alarm"],
            "alarm_level": decision["alarm_level"],
            "alarm_action": decision["alarm_action"],
            "targets": targets,
            "event_id": event_id,
        }

    def _relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(Path.cwd()))
        except ValueError:
            return str(path)

    def _top_target(self, targets: list[dict]) -> dict | None:
        if not targets:
            return None
        return max(targets, key=lambda target: target["confidence"])
