import pytest

from app.detectors.base_detector import EmptyDetector
from app.services.detection_service import DetectionService
from app.services.image_service import ImageValidationError


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
