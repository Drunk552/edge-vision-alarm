"""图片清理服务。"""

import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


@dataclass(frozen=True)
class CleanupResult:
    """图片清理统计结果。"""

    scanned: int
    deleted: int
    kept: int
    enabled: bool


class ImageCleanupService:
    """按配置清理过期图片文件。"""

    def __init__(
        self,
        image_root: Path | None = None,
        retention_days: int | None = None,
        enabled: bool | None = None,
        now: float | None = None,
    ) -> None:
        self.image_root = image_root or settings.image_save_dir
        self.retention_days = (
            retention_days
            if retention_days is not None
            else settings.normal_image_retention_days
        )
        self.enabled = (
            enabled if enabled is not None else settings.image_cleanup_enabled
        )
        self.now = now if now is not None else time.time()

    def cleanup(self) -> CleanupResult:
        """执行一次图片清理。"""

        if not self.enabled:
            return CleanupResult(scanned=0, deleted=0, kept=0, enabled=False)
        if not self.image_root.exists():
            return CleanupResult(scanned=0, deleted=0, kept=0, enabled=True)

        scanned = 0
        deleted = 0
        cutoff = self.now - self.retention_days * 24 * 60 * 60

        for file_path in self._iter_image_files():
            scanned += 1
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                deleted += 1

        return CleanupResult(
            scanned=scanned,
            deleted=deleted,
            kept=scanned - deleted,
            enabled=True,
        )

    def _iter_image_files(self):
        for file_path in self.image_root.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {".jpg", ".jpeg"}:
                yield file_path
