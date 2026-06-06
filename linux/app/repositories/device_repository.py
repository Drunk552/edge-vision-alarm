"""设备状态数据访问模块。"""

from app.repositories.database import get_connection


def _row_to_device(row) -> dict:
    """将 SQLite 行转换为设备状态字典。"""

    return {
        "device_id": row["device_id"],
        "status": row["status"],
        "rssi": row["rssi"],
        "free_heap": row["free_heap"],
        "last_seen": row["last_seen"],
        "updated_at": row["updated_at"],
    }


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

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO device_status (
                    device_id, rssi, free_heap, status, last_seen, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    rssi = excluded.rssi,
                    free_heap = excluded.free_heap,
                    status = excluded.status,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at
                """,
                (device_id, rssi, free_heap, status, updated_at, updated_at),
            )

    def list_devices(
        self,
        device_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[dict]]:
        """分页查询设备状态。"""

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
