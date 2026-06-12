import os

from app.services.image_cleanup_service import ImageCleanupService


def write_image(path, mtime):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xd8test\xff\xd9")
    os.utime(path, (mtime, mtime))


def test_image_cleanup_deletes_expired_images(tmp_path):
    now = 1_000_000.0
    old_image = tmp_path / "raw" / "2026-01-01" / "device" / "old.jpg"
    fresh_image = tmp_path / "raw" / "2026-01-02" / "device" / "fresh.jpg"
    write_image(old_image, now - 8 * 24 * 60 * 60)
    write_image(fresh_image, now - 1 * 24 * 60 * 60)

    result = ImageCleanupService(
        image_root=tmp_path,
        retention_days=7,
        enabled=True,
        now=now,
    ).cleanup()

    assert result.scanned == 2
    assert result.deleted == 1
    assert result.kept == 1
    assert not old_image.exists()
    assert fresh_image.exists()


def test_image_cleanup_keeps_files_when_disabled(tmp_path):
    now = 1_000_000.0
    old_image = tmp_path / "result" / "2026-01-01" / "device" / "old_result.jpg"
    write_image(old_image, now - 30 * 24 * 60 * 60)

    result = ImageCleanupService(
        image_root=tmp_path,
        retention_days=7,
        enabled=False,
        now=now,
    ).cleanup()

    assert result.enabled is False
    assert result.scanned == 0
    assert old_image.exists()
