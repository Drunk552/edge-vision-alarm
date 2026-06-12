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
        return [
            {
                "class": "person",
                "confidence": 0.9,
                "box": [60, 50, 80, 80],
                "image_width": 100,
                "image_height": 100,
            }
        ]


@pytest.fixture(autouse=True)
def reset_alarm_rule_state():
    AlarmRuleEngine.reset_states()
    yield
    AlarmRuleEngine.reset_states()


def danger_zone_person() -> dict:
    return {
        "class": "person",
        "confidence": 0.9,
        "box": [60, 50, 80, 80],
        "image_width": 100,
        "image_height": 100,
    }


def test_alarm_rule_marks_first_roi_hit_as_suspected():
    body = AlarmRuleEngine().evaluate(
        "esp32_s3_cam_001",
        [danger_zone_person()],
    )

    assert body["alarm"] is False
    assert body["alarm_level"] == "medium"
    assert body["alarm_action"] == "none"
    assert body["alarm_status"] == "suspected"
    assert body["event_type"] == "danger_zone_intrusion"


def test_alarm_rule_triggers_after_continuous_roi_hits():
    engine = AlarmRuleEngine()
    engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    body = engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    assert body["alarm"] is True
    assert body["alarm_level"] == "high"
    assert body["alarm_action"] == "beep_led"
    assert body["alarm_status"] == "alarm"


def test_alarm_rule_ignores_person_outside_danger_zone():
    body = AlarmRuleEngine().evaluate(
        "esp32_s3_cam_001",
        [
            {
                "class": "person",
                "confidence": 0.9,
                "box": [1, 1, 20, 20],
                "image_width": 100,
                "image_height": 100,
            }
        ],
    )

    assert body["alarm"] is False
    assert body["alarm_level"] == "normal"
    assert body["event_type"] == "upload"


def test_alarm_rule_resets_hit_count_when_roi_miss():
    engine = AlarmRuleEngine()
    engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])
    engine.evaluate(
        "esp32_s3_cam_001",
        [
            {
                "class": "person",
                "confidence": 0.9,
                "box": [1, 1, 20, 20],
                "image_width": 100,
                "image_height": 100,
            }
        ],
    )

    body = engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    assert body["alarm"] is False
    assert body["alarm_status"] == "suspected"


def test_alarm_rule_suppresses_repeated_alarm_in_window():
    now = 100.0
    engine = AlarmRuleEngine(clock=lambda: now)
    engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])
    engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    body = engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    assert body["alarm"] is False
    assert body["alarm_action"] == "none"
    assert body["alarm_status"] == "suppressed"


def test_alarm_rule_triggers_again_after_suppress_window():
    now = 100.0

    def clock() -> float:
        return now

    engine = AlarmRuleEngine(clock=clock)
    engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])
    engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    now = 111.0
    body = engine.evaluate("esp32_s3_cam_001", [danger_zone_person()])

    assert body["alarm"] is True
    assert body["alarm_status"] == "alarm"


@pytest.mark.anyio
async def test_upload_with_detector_records_targets():
    image = FakeUploadFile(b"\xff\xd8fake-image-data\xff\xd9", "image/jpeg")

    body = await DetectionService(detector=FakePersonDetector()).handle_upload(
        device_id="detect_test_device",
        image=image,
    )

    assert body["alarm"] is False
    assert body["alarm_status"] == "suspected"
    assert body["targets"][0]["class"] == "person"

    with get_connection() as connection:
        row = connection.execute(
            "SELECT target_class, confidence FROM detection_targets WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()

    assert row["target_class"] == "person"
    assert row["confidence"] == 0.9
