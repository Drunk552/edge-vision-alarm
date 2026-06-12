from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.config import settings
from app.repositories import device_repository
from app.repositories.device_repository import DeviceRepository
from app.utils.time_utils import now_iso


def test_heartbeat_updates_last_heartbeat_fields():
    updated_at = now_iso()
    device_id = f"device_heartbeat_{uuid4().hex}"

    DeviceRepository().upsert_status(
        device_id=device_id,
        status="online",
        updated_at=updated_at,
        rssi=-55,
        free_heap=1000,
    )
    _, items = DeviceRepository().list_devices(device_id=device_id)

    assert items[0]["online"] is True
    assert items[0]["status"] == "online"
    assert items[0]["last_heartbeat_at"] == updated_at
    assert items[0]["last_upload_at"] is None
    assert items[0]["upload_count"] == 0
    assert items[0]["alarm_count"] == 0


def test_upload_updates_upload_and_alarm_counters():
    repository = DeviceRepository()
    device_id = f"device_upload_{uuid4().hex}"
    repository.record_upload(
        device_id=device_id,
        updated_at=now_iso(),
        rssi=-50,
        free_heap=2000,
        alarm=False,
    )
    repository.record_upload(
        device_id=device_id,
        updated_at=now_iso(),
        rssi=-48,
        free_heap=1900,
        alarm=True,
    )

    _, items = repository.list_devices(device_id=device_id)

    assert items[0]["last_upload_at"] is not None
    assert items[0]["upload_count"] == 2
    assert items[0]["alarm_count"] == 1
    assert items[0]["rssi"] == -48
    assert items[0]["free_heap"] == 1900


def test_device_query_marks_stale_device_offline(monkeypatch):
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=120)
    device_id = f"device_offline_{uuid4().hex}"
    monkeypatch.setattr(
        device_repository,
        "settings",
        replace(settings, device_offline_seconds=30),
    )

    DeviceRepository().upsert_status(
        device_id=device_id,
        status="online",
        updated_at=stale_time.isoformat(),
    )
    _, items = DeviceRepository().list_devices(device_id=device_id)

    assert items[0]["online"] is False
    assert items[0]["status"] == "offline"
