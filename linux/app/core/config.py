"""服务端配置模块。"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass(frozen=True)
class Settings:
    """Linux 服务端运行配置。"""

    host: str = "0.0.0.0"
    port: int = 8000
    model_path: Path = PROJECT_ROOT / "models" / "yolov8n.pt"
    confidence_threshold: float = 0.6
    alarm_trigger_count: int = 2
    alarm_suppress_seconds: int = 10
    device_offline_seconds: int = 30
    danger_zone_enabled: bool = False
    danger_zone_roi: tuple[tuple[float, float], ...] = ()
    image_save_dir: Path = PROJECT_ROOT / "data" / "images"
    db_path: Path = PROJECT_ROOT / "data" / "alarm_system.db"
    max_image_size_mb: int = 1
    image_cleanup_enabled: bool = True
    normal_image_retention_days: int = 7
    alarm_image_retention_days: int = 30
    api_token: str | None = None


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data if isinstance(data, dict) else {}


def load_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    """从 config.yaml 读取配置。"""

    data = _read_yaml(config_path)

    def path_value(key: str, default: Path) -> Path:
        value = data.get(key)
        if not value:
            return default
        path = Path(str(value))
        return path if path.is_absolute() else PROJECT_ROOT / path

    def bool_value(key: str, default: bool) -> bool:
        value = data.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}

    def roi_value(key: str) -> tuple[tuple[float, float], ...]:
        value = data.get(key, [])
        if not isinstance(value, list):
            return ()

        points: list[tuple[float, float]] = []
        for point in value:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                return ()
            try:
                x = float(point[0])
                y = float(point[1])
            except (TypeError, ValueError):
                return ()
            points.append((x, y))
        return tuple(points)

    return Settings(
        host=str(data.get("HOST", "0.0.0.0")),
        port=int(data.get("PORT", 8000)),
        model_path=path_value("MODEL_PATH", PROJECT_ROOT / "models" / "yolov8n.pt"),
        confidence_threshold=float(data.get("CONF_THRESHOLD", 0.6)),
        alarm_trigger_count=int(data.get("ALARM_TRIGGER_COUNT", 2)),
        alarm_suppress_seconds=int(data.get("ALARM_SUPPRESS_SECONDS", 10)),
        device_offline_seconds=int(data.get("DEVICE_OFFLINE_SECONDS", 30)),
        danger_zone_enabled=bool_value("DANGER_ZONE_ENABLED", False),
        danger_zone_roi=roi_value("DANGER_ZONE_ROI"),
        image_save_dir=path_value("IMAGE_SAVE_DIR", PROJECT_ROOT / "data" / "images"),
        db_path=path_value("DB_PATH", PROJECT_ROOT / "data" / "alarm_system.db"),
        max_image_size_mb=int(data.get("MAX_IMAGE_SIZE_MB", 1)),
        image_cleanup_enabled=bool_value("IMAGE_CLEANUP_ENABLED", True),
        normal_image_retention_days=int(data.get("NORMAL_IMAGE_RETENTION_DAYS", 7)),
        alarm_image_retention_days=int(data.get("ALARM_IMAGE_RETENTION_DAYS", 30)),
        api_token=data.get("API_TOKEN"),
    )


settings = load_settings()
