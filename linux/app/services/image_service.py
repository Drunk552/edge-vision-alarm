"""图片保存服务模块。"""

from pathlib import Path
from typing import Protocol

from fastapi import UploadFile

from app.core.config import settings
from app.core.error_codes import IMAGE_FORMAT_ERROR, IMAGE_TOO_LARGE
from app.utils.time_utils import compact_timestamp


class ImageValidationError(ValueError):
    """图片校验失败异常。"""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ReadableUpload(Protocol):
    """上传文件最小协议。"""

    content_type: str | None

    async def read(self) -> bytes:
        """读取上传内容。"""


class ImageService:
    """负责上传图片校验和保存。"""

    async def save_upload(
        self, device_id: str, image: UploadFile | ReadableUpload
    ) -> Path:
        """校验并保存上传图片。"""

        content = await image.read()
        if not self._is_jpeg(content, image.content_type):
            raise ImageValidationError(IMAGE_FORMAT_ERROR, "image must be jpeg")

        max_size = settings.max_image_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise ImageValidationError(IMAGE_TOO_LARGE, "image size exceeds limit")

        raw_dir = settings.image_save_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{compact_timestamp()}_{device_id}.jpg"
        file_path = raw_dir / filename
        file_path.write_bytes(content)
        return file_path

    def save_result_image(self, raw_path: Path, targets: list[dict]) -> Path | None:
        """绘制检测框并保存结果图。"""

        if not targets:
            return None

        try:
            import cv2
        except ImportError:
            return None

        image = cv2.imread(str(raw_path))
        if image is None:
            return None

        for target in targets:
            box = target.get("box") or []
            if len(box) != 4:
                continue
            x1, y1, x2, y2 = box
            label = f"{target['class']} {target['confidence']:.2f}"
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                image,
                label,
                (x1, max(y1 - 8, 16)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

        result_dir = settings.image_save_dir / "result"
        result_dir.mkdir(parents=True, exist_ok=True)
        result_path = result_dir / f"{raw_path.stem}_result.jpg"
        if not cv2.imwrite(str(result_path), image):
            return None
        return result_path

    def image_dir_status(self) -> str:
        """检查图片目录是否可写。"""

        try:
            settings.image_save_dir.mkdir(parents=True, exist_ok=True)
            test_path = settings.image_save_dir / ".write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
        except OSError:
            return "error"
        return "ok"

    def _is_jpeg(self, content: bytes, content_type: str | None) -> bool:
        if content_type not in {"image/jpeg", "image/jpg", "application/octet-stream"}:
            return False
        return content.startswith(b"\xff\xd8") and content.endswith(b"\xff\xd9")
