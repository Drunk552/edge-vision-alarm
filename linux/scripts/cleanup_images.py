"""手动清理过期图片脚本。"""

from app.services.image_cleanup_service import ImageCleanupService


if __name__ == "__main__":
    result = ImageCleanupService().cleanup()
    print(
        "image cleanup finished: "
        f"enabled={result.enabled} "
        f"scanned={result.scanned} "
        f"deleted={result.deleted} "
        f"kept={result.kept}"
    )
