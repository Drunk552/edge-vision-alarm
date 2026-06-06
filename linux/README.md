# Edge Vision Alarm Linux Service

这是边缘视觉安全告警系统的 Linux 服务端。当前阶段实现最小可运行闭环：

- `GET /api/health`：服务健康检查。
- `POST /api/upload`：接收 ESP32 上传的 JPEG 图片并保存。
- `POST /api/heartbeat`：接收设备心跳并更新设备状态。
- `GET /api/latest`：查询最新一次上传/检测结果。
- `GET /api/alarms`：分页查询历史检测事件。
- `GET /api/devices`：分页查询设备状态。
- `POST /api/alarms/{event_id}/handle`：将事件标记为已处理。
- `GET /`：轻量 Web 管理页面。
- SQLite 初始化和基础事件记录。

## 启动

推荐在项目根目录使用快速启动脚本：

```bash
source start_linux.sh
```

等价手动步骤：

```bash
cd linux
python3 -m venv .venv
source .venv/bin/activate
make install-dev
make init-db
make run
```

服务默认监听 `0.0.0.0:8000`。

## 上传测试

```bash
curl -F "device_id=esp32_s3_cam_001" \
     -F "image=@test.jpg;type=image/jpeg" \
     -F "rssi=-52" \
     -F "free_heap=184320" \
     http://127.0.0.1:8000/api/upload
```
