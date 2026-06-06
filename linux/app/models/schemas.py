"""接口请求和响应模型。"""

from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    """设备心跳请求。"""

    device_id: str = Field(min_length=1)
    rssi: int | None = None
    free_heap: int | None = None
    status: str = "online"
    heartbeat_time: str | None = None


class HealthResponse(BaseModel):
    """健康检查响应。"""

    code: int
    status: str
    model_loaded: bool
    database: str
    image_dir: str
    timestamp: str
    message: str
