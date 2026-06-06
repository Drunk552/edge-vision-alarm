"""检测目标明细数据访问模块。"""

from app.repositories.database import get_connection


class TargetRepository:
    """封装检测目标明细数据库操作。"""

    def create_targets(self, event_id: int, targets: list[dict]) -> None:
        """批量新增检测目标明细。"""

        if not targets:
            return

        rows = []
        for target in targets:
            box = target.get("box") or [None, None, None, None]
            rows.append(
                (
                    event_id,
                    target["class"],
                    target["confidence"],
                    box[0],
                    box[1],
                    box[2],
                    box[3],
                )
            )

        with get_connection() as connection:
            connection.executemany(
                """
                INSERT INTO detection_targets (
                    event_id, target_class, confidence,
                    box_x1, box_y1, box_x2, box_y2
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
