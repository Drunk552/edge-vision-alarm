"""时间工具模块。"""

from datetime import datetime, timezone


def now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""

    return datetime.now(timezone.utc).isoformat()


def compact_timestamp() -> str:
    """生成适合文件名使用的时间戳。"""

    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def date_path() -> str:
    """生成图片归档目录使用的 UTC 日期。"""

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
