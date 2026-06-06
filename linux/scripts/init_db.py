"""初始化 SQLite 数据库脚本。"""

from app.repositories.database import init_db


if __name__ == "__main__":
    init_db()
    print("database initialized")

