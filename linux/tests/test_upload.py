from dataclasses import replace

import pytest

from app.detectors.base_detector import EmptyDetector
from app.core.config import settings
from app.services import image_service
from app.services.detection_service import DetectionService
from app.services.image_service import ImageService, ImageValidationError


class FakeUploadFile:
    def __init__(self, content: bytes, content_type: str) -> None:
        self._content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


@pytest.mark.anyio
async def test_upload_accepts_jpeg_image():
    jpeg = b"\xff\xd8fake-image-data\xff\xd9"
    image = FakeUploadFile(jpeg, "image/jpeg")

    body = await DetectionService(detector=EmptyDetector()).handle_upload(
        device_id="esp32_s3_cam_001",
        image=image,
        rssi=-52,
        free_heap=184320,
    )

    assert body["code"] == 0
    assert body["alarm"] is False
    assert body["event_id"] > 0


@pytest.mark.anyio
async def test_upload_rejects_non_jpeg_image():
    image = FakeUploadFile(b"not-an-image", "text/plain")

    with pytest.raises(ImageValidationError) as exc_info:
        await DetectionService().handle_upload(
            device_id="esp32_s3_cam_001", image=image
        )
    assert exc_info.value.code == 4002


@pytest.mark.anyio
async def test_image_save_uses_date_and_device_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(image_service, "settings", replace(settings, image_save_dir=tmp_path))
    monkeypatch.setattr(image_service, "date_path", lambda: "2026-06-10")
    image = FakeUploadFile(b"\xff\xd8fake-image-data\xff\xd9", "image/jpeg")

    path = await ImageService().save_upload("esp32_s3_cam_001", image)

    assert path.parent == tmp_path / "raw" / "2026-06-10" / "esp32_s3_cam_001"
    assert path.name.endswith(".jpg")


def test_result_dir_follows_raw_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(image_service, "settings", replace(settings, image_save_dir=tmp_path))
    raw_path = tmp_path / "raw" / "2026-06-10" / "esp32_s3_cam_001" / "a.jpg"

    result_dir = ImageService()._result_dir_for_raw(raw_path)

    assert result_dir == tmp_path / "result" / "2026-06-10" / "esp32_s3_cam_001"
