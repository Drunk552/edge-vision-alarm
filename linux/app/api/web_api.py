"""Web 管理页面接口。"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    """返回系统管理首页。"""

    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Edge Vision Alarm</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #18202a;
      --muted: #667085;
      --line: #d9dee7;
      --ok: #0f8a5f;
      --warn: #b54708;
      --danger: #b42318;
      --accent: #1f6feb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 24px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 { margin: 0; font-size: 20px; font-weight: 700; }
    h2 { margin: 0 0 12px; font-size: 16px; }
    button {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 8px 12px;
      color: var(--text);
      cursor: pointer;
    }
    button.primary { background: var(--accent); color: white; border-color: var(--accent); }
    main { padding: 20px 24px 32px; max-width: 1280px; margin: 0 auto; }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(280px, .8fr);
      gap: 16px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .latest-image {
      width: 100%;
      min-height: 280px;
      max-height: 520px;
      object-fit: contain;
      background: #eef1f5;
      border: 1px solid var(--line);
      border-radius: 6px;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      min-height: 68px;
    }
    .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
    .value { font-size: 15px; font-weight: 650; overflow-wrap: anywhere; }
    .status { color: var(--ok); }
    .alarm { color: var(--danger); }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: middle;
    }
    th { color: var(--muted); font-weight: 650; }
    .section { margin-top: 16px; }
    .empty { color: var(--muted); padding: 16px 0; }
    @media (max-width: 860px) {
      header { align-items: flex-start; flex-direction: column; }
      main { padding: 16px; }
      .grid { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: 1fr; }
      table { display: block; overflow-x: auto; white-space: nowrap; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Edge Vision Alarm</h1>
    <button class="primary" onclick="loadDashboard()">刷新</button>
  </header>
  <main>
    <section class="grid">
      <div class="panel">
        <h2>最新检测</h2>
        <img id="latestImage" class="latest-image" alt="">
      </div>
      <div class="panel">
        <h2>状态摘要</h2>
        <div class="metrics">
          <div class="metric"><div class="label">设备</div><div id="deviceId" class="value">-</div></div>
          <div class="metric"><div class="label">告警</div><div id="alarmState" class="value">-</div></div>
          <div class="metric"><div class="label">目标</div><div id="targetInfo" class="value">-</div></div>
          <div class="metric"><div class="label">时间</div><div id="createdAt" class="value">-</div></div>
        </div>
      </div>
    </section>

    <section class="panel section">
      <h2>设备状态</h2>
      <div id="devices"></div>
    </section>

    <section class="panel section">
      <h2>历史事件</h2>
      <div id="alarms"></div>
    </section>
  </main>

  <script>
    function imageUrl(path) {
      if (!path) return "";
      return "/" + path.replace(/^data\\/images\\//, "images/");
    }

    function fmt(value) {
      return value === null || value === undefined || value === "" ? "-" : value;
    }

    async function fetchJson(url, options) {
      const response = await fetch(url, options);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }

    async function loadLatest() {
      const data = await fetchJson("/api/latest");
      if (data.data === null) return;
      const path = data.result_image_path || data.raw_image_path;
      const image = document.getElementById("latestImage");
      image.src = imageUrl(path);
      image.alt = path || "";
      document.getElementById("deviceId").textContent = fmt(data.device_id);
      document.getElementById("alarmState").textContent = data.alarm ? "告警" : "正常";
      document.getElementById("alarmState").className = data.alarm ? "value alarm" : "value status";
      const target = data.top_target ? `${data.top_target.class} ${Number(data.top_target.confidence).toFixed(2)}` : "none";
      document.getElementById("targetInfo").textContent = target;
      document.getElementById("createdAt").textContent = fmt(data.created_at);
    }

    async function loadDevices() {
      const data = await fetchJson("/api/devices?page=1&page_size=10");
      if (!data.items.length) {
        document.getElementById("devices").innerHTML = '<div class="empty">暂无设备状态</div>';
        return;
      }
      document.getElementById("devices").innerHTML = `
        <table>
          <thead><tr><th>设备</th><th>状态</th><th>RSSI</th><th>Heap</th><th>最近在线</th></tr></thead>
          <tbody>
            ${data.items.map(item => `
              <tr>
                <td>${fmt(item.device_id)}</td>
                <td>${fmt(item.status)}</td>
                <td>${fmt(item.rssi)}</td>
                <td>${fmt(item.free_heap)}</td>
                <td>${fmt(item.last_seen)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>`;
    }

    async function handleAlarm(eventId) {
      await fetchJson(`/api/alarms/${eventId}/handle`, { method: "POST" });
      await loadDashboard();
    }

    async function loadAlarms() {
      const data = await fetchJson("/api/alarms?page=1&page_size=20");
      if (!data.items.length) {
        document.getElementById("alarms").innerHTML = '<div class="empty">暂无历史事件</div>';
        return;
      }
      document.getElementById("alarms").innerHTML = `
        <table>
          <thead><tr><th>ID</th><th>设备</th><th>类别</th><th>置信度</th><th>级别</th><th>状态</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            ${data.items.map(item => `
              <tr>
                <td>${item.event_id}</td>
                <td>${fmt(item.device_id)}</td>
                <td>${fmt(item.target_class)}</td>
                <td>${item.confidence === null ? "-" : Number(item.confidence).toFixed(2)}</td>
                <td>${fmt(item.alarm_level)}</td>
                <td>${item.handled ? "已处理" : fmt(item.alarm_status)}</td>
                <td>${fmt(item.created_at)}</td>
                <td>${item.handled ? "-" : `<button onclick="handleAlarm(${item.event_id})">处理</button>`}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>`;
    }

    async function loadDashboard() {
      try {
        await Promise.all([loadLatest(), loadDevices(), loadAlarms()]);
      } catch (error) {
        console.error(error);
      }
    }

    loadDashboard();
    setInterval(loadDashboard, 5000);
  </script>
</body>
</html>
"""
