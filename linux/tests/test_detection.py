import pytest

from app.repositories.database import get_connection
from app.rules.alarm_rule_engine import AlarmRuleEngine
from app.services.detection_service import DetectionService
from tests.test_upload import FakeUploadFile


class FakePersonDetector:
    @property
    def model_loaded(self) -> bool:
        return True

    def detect(self, image_path: str) -> list[dict]:
        return [{"class": "person", "confidence": 0.9, "box": [1, 2, 30, 40]}]


def test_alarm_rule_triggers_on_person():
    body = AlarmRuleEngine().evaluate(
        "esp32_s3_cam_001",
        [{"class": "person", "confidence": 0.9, "box": [1, 2, 30, 40]}],
    )

    assert body["alarm"] is True
    assert body["alarm_level"] == "high"
    assert body["alarm_action"] == "beep_led"


@pytest.mark.anyio
async def test_upload_with_detector_records_targets():
    image = FakeUploadFile(b"\xff\xd8fake-image-data\xff\xd9", "image/jpeg")

    body = await DetectionService(detector=FakePersonDetector()).handle_upload(
        device_id="detect_test_device",
        image=image,
    )

    assert body["alarm"] is True
    assert body["targets"][0]["class"] == "person"

    with get_connection() as connection:
        row = connection.execute(
            "SELECT target_class, confidence FROM detection_targets WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()

    assert row["target_class"] == "person"
    assert row["confidence"] == 0.9
