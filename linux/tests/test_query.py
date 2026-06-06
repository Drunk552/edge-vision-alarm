from app.api.query_api import get_latest, handle_alarm, list_alarms, list_devices
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.device_repository import DeviceRepository
from app.utils.time_utils import now_iso


def test_latest_returns_latest_event():
    created_at = now_iso()
    event_id = AlarmRepository().create_event(
        device_id="query_test_device",
        raw_image_path="data/images/raw/query_test.jpg",
        created_at=created_at,
    )

    body = get_latest(device_id="query_test_device")

    assert body["code"] == 0
    assert body["event_id"] == event_id
    assert body["device_id"] == "query_test_device"
    assert body["raw_image_path"] == "data/images/raw/query_test.jpg"


def test_list_alarms_returns_paginated_events():
    AlarmRepository().create_event(
        device_id="query_list_device",
        raw_image_path="data/images/raw/query_list.jpg",
        created_at=now_iso(),
    )

    body = list_alarms(device_id="query_list_device", page=1, page_size=10)

    assert body["code"] == 0
    assert body["total"] >= 1
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["items"][0]["device_id"] == "query_list_device"


def test_list_devices_returns_device_status():
    DeviceRepository().upsert_status(
        device_id="query_device_status",
        status="online",
        updated_at=now_iso(),
        rssi=-50,
        free_heap=123456,
    )

    body = list_devices(device_id="query_device_status")

    assert body["code"] == 0
    assert body["total"] == 1
    assert body["items"][0]["device_id"] == "query_device_status"
    assert body["items"][0]["status"] == "online"


def test_handle_alarm_marks_event_handled():
    event_id = AlarmRepository().create_event(
        device_id="handle_test_device",
        raw_image_path="data/images/raw/handle_test.jpg",
        created_at=now_iso(),
        alarm_status="alarm",
        alarm_level="high",
        target_class="person",
        confidence=0.9,
    )

    body = handle_alarm(event_id)
    event = AlarmRepository().get_latest_event(device_id="handle_test_device")

    assert body["code"] == 0
    assert event["handled"] == 1
    assert event["alarm_status"] == "handled"
