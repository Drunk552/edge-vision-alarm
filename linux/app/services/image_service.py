"""图片保存服务模块。"""

from pathlib import Path
from typing import Protocol

from fastapi import UploadFile

from app.core.config import settings
from app.core.error_codes import IMAGE_FORMAT_ERROR, IMAGE_TOO_LARGE
from app.utils.time_utils import compact_timestamp, date_path


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

        raw_dir = settings.image_save_dir / "raw" / date_path() / device_id
        raw_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{compact_timestamp()}.jpg"
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

        self._draw_danger_zone(cv2, image)

        for target in targets:
            box = target.get("box") or []
            if len(box) != 4:
                continue
            x1, y1, x2, y2 = box
            color = self._target_color(target)
            suffix = " danger_zone" if target.get("in_danger_zone") else ""
            label = f"{target['class']} {target['confidence']:.2f}{suffix}"
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                image,
                label,
                (x1, max(y1 - 8, 16)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

        result_dir = self._result_dir_for_raw(raw_path)
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

    def _draw_danger_zone(self, cv2, image) -> None:
        if not settings.danger_zone_enabled or len(settings.danger_zone_roi) < 3:
            return

        height, width = image.shape[:2]
        points = [
            [int(x * width), int(y * height)] for x, y in settings.danger_zone_roi
        ]
        try:
            import numpy as np
        except ImportError:
            return

        polygon = np.array(points, dtype=np.int32)
        cv2.polylines(image, [polygon], isClosed=True, color=(0, 165, 255), thickness=2)
        cv2.putText(
            image,
            "danger zone",
            tuple(polygon[0]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 165, 255),
            2,
            cv2.LINE_AA,
        )

    def _target_color(self, target: dict) -> tuple[int, int, int]:
        if target.get("in_danger_zone"):
            return (0, 0, 255)
        return (0, 180, 0)

    def _result_dir_for_raw(self, raw_path: Path) -> Path:
        raw_root = settings.image_save_dir / "raw"
        result_root = settings.image_save_dir / "result"
        try:
            relative_parent = raw_path.parent.relative_to(raw_root)
        except ValueError:
            return result_root
        return result_root / relative_parent
