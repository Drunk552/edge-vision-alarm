"""设备状态数据访问模块。"""

from datetime import datetime, timezone

from app.core.config import settings
from app.repositories.database import get_connection, init_db


def _row_to_device(row) -> dict:
    """将 SQLite 行转换为设备状态字典。"""

    online = _is_online(row["last_seen"])
    return {
        "device_id": row["device_id"],
        "status": "online" if online else "offline",
        "online": online,
        "rssi": row["rssi"],
        "free_heap": row["free_heap"],
        "last_seen": row["last_seen"],
        "last_heartbeat_at": row["last_heartbeat_at"],
        "last_upload_at": row["last_upload_at"],
        "upload_count": row["upload_count"] or 0,
        "alarm_count": row["alarm_count"] or 0,
        "updated_at": row["updated_at"],
    }


def _is_online(last_seen: str | None) -> bool:
    if not last_seen:
        return False
    try:
        last_seen_at = datetime.fromisoformat(last_seen)
    except ValueError:
        return False
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)

    elapsed = datetime.now(timezone.utc) - last_seen_at.astimezone(timezone.utc)
    return elapsed.total_seconds() <= settings.device_offline_seconds


class DeviceRepository:
    """封装设备状态数据库操作。"""

    def upsert_status(
        self,
        device_id: str,
        status: str,
        updated_at: str,
        rssi: int | None = None,
        free_heap: int | None = None,
    ) -> None:
        """新增或更新设备状态。"""

        init_db()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO device_status (
                    device_id, rssi, free_heap, status, last_seen, updated_at,
                    last_heartbeat_at, upload_count, alarm_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
                ON CONFLICT(device_id) DO UPDATE SET
                    rssi = excluded.rssi,
                    free_heap = excluded.free_heap,
                    status = excluded.status,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at,
                    last_heartbeat_at = excluded.last_heartbeat_at
                """,
                (
                    device_id,
                    rssi,
                    free_heap,
                    status,
                    updated_at,
                    updated_at,
                    updated_at,
                ),
            )

    def record_upload(
        self,
        device_id: str,
        updated_at: str,
        rssi: int | None = None,
        free_heap: int | None = None,
        alarm: bool = False,
    ) -> None:
        """记录一次设备图片上传。"""

        init_db()
        alarm_increment = 1 if alarm else 0
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO device_status (
                    device_id, rssi, free_heap, status, last_seen, updated_at,
                    last_upload_at, upload_count, alarm_count
                )
                VALUES (?, ?, ?, 'online', ?, ?, ?, 1, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    rssi = excluded.rssi,
                    free_heap = excluded.free_heap,
                    status = excluded.status,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at,
                    last_upload_at = excluded.last_upload_at,
                    upload_count = COALESCE(device_status.upload_count, 0) + 1,
                    alarm_count = COALESCE(device_status.alarm_count, 0) + ?
                """,
                (
                    device_id,
                    rssi,
                    free_heap,
                    updated_at,
                    updated_at,
                    updated_at,
                    alarm_increment,
                    alarm_increment,
                ),
            )

    def list_devices(
        self,
        device_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[dict]]:
        """分页查询设备状态。"""

        init_db()
        where_clauses = []
        params: list[object] = []
        if device_id:
            where_clauses.append("device_id = ?")
            params.append(device_id)
        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        offset = (page - 1) * page_size

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS total FROM device_status{where_sql}",
                params,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT * FROM device_status{where_sql}
                ORDER BY updated_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()

        return int(total), [_row_to_device(row) for row in rows]
