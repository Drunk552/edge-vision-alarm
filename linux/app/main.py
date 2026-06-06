"""FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import health_api, heartbeat_api, query_api, upload_api, web_api
from app.core.config import settings
from app.core.logger import setup_logging
from app.repositories.database import init_db

setup_logging()
init_db()

app = FastAPI(title="Edge Vision Alarm", version="0.1.0")
app.include_router(web_api.router)
app.include_router(health_api.router)
app.include_router(upload_api.router)
app.include_router(heartbeat_api.router)
app.include_router(query_api.router)

settings.image_save_dir.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=settings.image_save_dir), name="images")
