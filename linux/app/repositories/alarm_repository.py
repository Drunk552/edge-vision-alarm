"""告警事件数据访问模块。"""

from app.repositories.database import get_connection


def _row_to_event(row) -> dict:
    """将 SQLite 行转换为事件字典。"""

    return {
        "event_id": row["id"],
        "device_id": row["device_id"],
        "event_type": row["event_type"],
        "alarm_level": row["alarm_level"],
        "target_class": row["target_class"],
        "confidence": row["confidence"],
        "raw_image_path": row["raw_image_path"],
        "result_image_path": row["result_image_path"],
        "alarm_status": row["alarm_status"],
        "handled": row["handled"],
        "created_at": row["created_at"],
    }


class AlarmRepository:
    """封装告警事件数据库操作。"""

    def create_event(
        self,
        device_id: str,
        raw_image_path: str,
        created_at: str,
        event_type: str = "upload",
        alarm_level: str = "normal",
        target_class: str = "none",
        confidence: float | None = None,
        alarm_status: str = "normal",
        result_image_path: str | None = None,
    ) -> int:
        """新增一条检测事件记录。"""

        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO alarm_events (
                    device_id, event_type, alarm_level, target_class, confidence,
                    raw_image_path, result_image_path, alarm_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    event_type,
                    alarm_level,
                    target_class,
                    confidence,
                    raw_image_path,
                    result_image_path,
                    alarm_status,
                    created_at,
                ),
            )
            return int(cursor.lastrowid)

    def get_latest_event(self, device_id: str | None = None) -> dict | None:
        """查询最新一条检测事件。"""

        sql = "SELECT * FROM alarm_events"
        params: list[object] = []
        if device_id:
            sql += " WHERE device_id = ?"
            params.append(device_id)
        sql += " ORDER BY created_at DESC, id DESC LIMIT 1"

        with get_connection() as connection:
            row = connection.execute(sql, params).fetchone()
        return _row_to_event(row) if row else None

    def list_events(
        self,
        device_id: str | None = None,
        target_class: str | None = None,
        handled: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[dict]]:
        """分页查询检测事件。"""

        where_clauses = []
        params: list[object] = []
        if device_id:
            where_clauses.append("device_id = ?")
            params.append(device_id)
        if target_class:
            where_clauses.append("target_class = ?")
            params.append(target_class)
        if handled is not None:
            where_clauses.append("handled = ?")
            params.append(handled)

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        offset = (page - 1) * page_size

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS total FROM alarm_events{where_sql}",
                params,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT * FROM alarm_events{where_sql}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()

        return int(total), [_row_to_event(row) for row in rows]

    def mark_handled(self, event_id: int, handled_at: str) -> bool:
        """将告警事件标记为已处理。"""

        with get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE alarm_events
                SET handled = 1, handled_at = ?, alarm_status = 'handled'
                WHERE id = ?
                """,
                (handled_at, event_id),
            )
            return cursor.rowcount > 0
