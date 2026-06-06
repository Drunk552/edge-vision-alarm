"""SQLite 数据库连接与初始化模块。"""

import sqlite3
from pathlib import Path

from app.core.config import settings


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """创建 SQLite 连接。"""

    path = db_path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path | None = None) -> None:
    """初始化数据库表结构。"""

    with get_connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS alarm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                alarm_level TEXT NOT NULL,
                target_class TEXT NOT NULL,
                confidence REAL,
                raw_image_path TEXT,
                result_image_path TEXT,
                alarm_status TEXT NOT NULL DEFAULT 'normal',
                created_at TEXT NOT NULL,
                handled INTEGER DEFAULT 0,
                handled_at TEXT
            );

            CREATE TABLE IF NOT EXISTS device_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL UNIQUE,
                rssi INTEGER,
                free_heap INTEGER,
                status TEXT,
                last_seen TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS detection_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                target_class TEXT NOT NULL,
                confidence REAL,
                box_x1 INTEGER,
                box_y1 INTEGER,
                box_x2 INTEGER,
                box_y2 INTEGER,
                FOREIGN KEY(event_id) REFERENCES alarm_events(id)
            );
            """
        )
