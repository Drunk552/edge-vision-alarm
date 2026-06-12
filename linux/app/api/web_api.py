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
      --bg: #f4f6f8;
      --panel: #ffffff;
      --panel-soft: #f9fafb;
      --text: #17202a;
      --muted: #667085;
      --line: #d9dee7;
      --line-soft: #eef1f5;
      --ok: #0f8a5f;
      --warn: #b54708;
      --danger: #b42318;
      --accent: #1f6feb;
      --accent-soft: #e8f1ff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    header {
      position: sticky;
      top: 0;
      z-index: 2;
      background: rgba(255, 255, 255, .96);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(10px);
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      max-width: 1360px;
      margin: 0 auto;
      padding: 14px 24px;
    }
    .brand {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 220px;
    }
    h1 { margin: 0; font-size: 20px; font-weight: 750; }
    .subtitle { color: var(--muted); font-size: 13px; }
    .actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }
    button {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 8px 12px;
      color: var(--text);
      cursor: pointer;
      font: inherit;
    }
    button:hover { border-color: #b8c2d2; }
    button.primary {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    button.link-button {
      color: var(--accent);
      background: transparent;
      border-color: transparent;
      padding: 4px 0;
    }
    main {
      max-width: 1360px;
      margin: 0 auto;
      padding: 18px 24px 32px;
    }
    .status-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .stat {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 78px;
    }
    .label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
      white-space: nowrap;
    }
    .value {
      font-size: 18px;
      font-weight: 750;
      overflow-wrap: anywhere;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(330px, .65fr);
      gap: 16px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line-soft);
    }
    h2 { margin: 0; font-size: 16px; font-weight: 720; }
    .panel-body { padding: 16px; }
    .image-wrap {
      display: grid;
      place-items: center;
      min-height: 460px;
      background: #eef2f7;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    .latest-image {
      width: 100%;
      height: 100%;
      max-height: 620px;
      object-fit: contain;
      display: block;
    }
    .detail-list {
      display: grid;
      gap: 10px;
    }
    .detail-row {
      display: grid;
      grid-template-columns: 96px minmax(0, 1fr);
      gap: 10px;
      align-items: center;
      min-height: 32px;
      border-bottom: 1px solid var(--line-soft);
      padding-bottom: 10px;
    }
    .detail-row:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }
    .muted { color: var(--muted); font-size: 13px; }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .badge::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
    }
    .badge.ok {
      color: var(--ok);
      background: #e8f7f0;
    }
    .badge.warn {
      color: var(--warn);
      background: #fff4e5;
    }
    .badge.danger {
      color: var(--danger);
      background: #ffebe9;
    }
    .badge.neutral {
      color: var(--muted);
      background: #eef1f5;
    }
    .section { margin-top: 16px; }
    .table-wrap {
      width: 100%;
      overflow-x: auto;
    }
    table {
      width: 100%;
      min-width: 760px;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--line-soft);
      padding: 11px 10px;
      text-align: left;
      vertical-align: middle;
    }
    th {
      color: var(--muted);
      font-weight: 700;
      background: var(--panel-soft);
      white-space: nowrap;
    }
    tr:hover td { background: #fbfcfe; }
    .selected-row td { background: var(--accent-soft); }
    .empty {
      color: var(--muted);
      padding: 20px 0;
      text-align: center;
    }
    .error {
      display: none;
      margin-bottom: 16px;
      border: 1px solid #f0b8b4;
      background: #fff1f0;
      color: var(--danger);
      border-radius: 8px;
      padding: 12px 14px;
    }
    .nowrap { white-space: nowrap; }
    @media (max-width: 980px) {
      .topbar { align-items: flex-start; flex-direction: column; }
      .actions { width: 100%; justify-content: flex-start; }
      main { padding: 14px 14px 28px; }
      .status-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .layout { grid-template-columns: 1fr; }
      .image-wrap { min-height: 320px; }
    }
    @media (max-width: 560px) {
      .status-strip { grid-template-columns: 1fr; }
      .detail-row { grid-template-columns: 82px minmax(0, 1fr); }
      button { width: auto; }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div class="brand">
        <h1>Edge Vision Alarm</h1>
        <div class="subtitle">边缘视觉安全告警管理台</div>
      </div>
      <div class="actions">
        <span id="selectedDevice" class="muted"></span>
        <button onclick="clearDeviceFilter()">全部设备</button>
        <button class="primary" onclick="loadDashboard()">刷新</button>
      </div>
    </div>
  </header>
  <main>
    <div id="errorBanner" class="error"></div>

    <section class="status-strip">
      <div class="stat">
        <div class="label">在线设备</div>
        <div id="onlineDevices" class="value">-</div>
      </div>
      <div class="stat">
        <div class="label">设备总数</div>
        <div id="totalDevices" class="value">-</div>
      </div>
      <div class="stat">
        <div class="label">事件总数</div>
        <div id="totalEvents" class="value">-</div>
      </div>
      <div class="stat">
        <div class="label">最近刷新</div>
        <div id="lastRefresh" class="value">-</div>
      </div>
    </section>

    <section class="layout">
      <div class="panel">
        <div class="panel-header">
          <h2>最新检测</h2>
          <span id="latestStatusBadge" class="badge neutral">无数据</span>
        </div>
        <div class="panel-body">
          <div class="image-wrap">
            <img id="latestImage" class="latest-image" alt="">
          </div>
        </div>
      </div>

      <aside class="panel">
        <div class="panel-header">
          <h2>检测详情</h2>
        </div>
        <div class="panel-body">
          <div class="detail-list">
            <div class="detail-row"><div class="label">设备</div><div id="deviceId" class="value">-</div></div>
            <div class="detail-row"><div class="label">告警状态</div><div id="alarmState">-</div></div>
            <div class="detail-row"><div class="label">事件类型</div><div id="eventType" class="value">-</div></div>
            <div class="detail-row"><div class="label">目标</div><div id="targetInfo" class="value">-</div></div>
            <div class="detail-row"><div class="label">时间</div><div id="createdAt" class="value">-</div></div>
          </div>
        </div>
      </aside>
    </section>

    <section class="panel section">
      <div class="panel-header">
        <h2>设备状态</h2>
        <span id="deviceSummary" class="muted">-</span>
      </div>
      <div id="devices" class="table-wrap"></div>
    </section>

    <section class="panel section">
      <div class="panel-header">
        <h2>历史事件</h2>
        <span id="alarmSummary" class="muted">-</span>
      </div>
      <div id="alarms" class="table-wrap"></div>
    </section>
  </main>

  <script>
    let selectedDeviceId = "";

    function imageUrl(path) {
      if (!path) return "";
      return "/" + path.replace(/^data\\/images\\//, "images/");
    }

    function fmt(value) {
      return value === null || value === undefined || value === "" ? "-" : value;
    }

    function shortTime(value) {
      if (!value) return "-";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString();
    }

    async function fetchJson(url, options) {
      const response = await fetch(url, options);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }

    async function loadLatest() {
      const suffix = selectedDeviceId ? `?device_id=${encodeURIComponent(selectedDeviceId)}` : "";
      const data = await fetchJson(`/api/latest${suffix}`);
      if (data.data === null) {
        clearLatest();
        return;
      }

      const path = data.result_image_path || data.raw_image_path;
      const image = document.getElementById("latestImage");
      image.src = imageUrl(path);
      image.alt = path || "";
      document.getElementById("deviceId").textContent = fmt(data.device_id);
      document.getElementById("alarmState").innerHTML = statusBadge(data.alarm_status);
      document.getElementById("latestStatusBadge").outerHTML = statusBadge(data.alarm_status, "latestStatusBadge");
      document.getElementById("eventType").textContent = fmt(data.event_type);
      const target = data.top_target ? `${data.top_target.class} ${Number(data.top_target.confidence).toFixed(2)}` : "none";
      document.getElementById("targetInfo").textContent = target;
      document.getElementById("createdAt").textContent = shortTime(data.created_at);
    }

    function clearLatest() {
      document.getElementById("latestImage").removeAttribute("src");
      document.getElementById("deviceId").textContent = "-";
      document.getElementById("alarmState").innerHTML = statusBadge("normal");
      document.getElementById("latestStatusBadge").outerHTML = statusBadge("normal", "latestStatusBadge");
      document.getElementById("eventType").textContent = "-";
      document.getElementById("targetInfo").textContent = "-";
      document.getElementById("createdAt").textContent = "-";
    }

    async function loadDevices() {
      const data = await fetchJson("/api/devices?page=1&page_size=20");
      const onlineCount = data.items.filter(item => item.online).length;
      document.getElementById("onlineDevices").textContent = `${onlineCount}`;
      document.getElementById("totalDevices").textContent = `${data.total}`;
      document.getElementById("deviceSummary").textContent = `在线 ${onlineCount} / 共 ${data.items.length}`;

      if (!data.items.length) {
        document.getElementById("devices").innerHTML = '<div class="empty">暂无设备状态</div>';
        return;
      }
      document.getElementById("devices").innerHTML = `
        <table>
          <thead><tr><th>设备</th><th>状态</th><th>RSSI</th><th>Heap</th><th>上传</th><th>告警</th><th>最近心跳</th><th>最近上传</th></tr></thead>
          <tbody>
            ${data.items.map(item => `
              <tr class="${item.device_id === selectedDeviceId ? "selected-row" : ""}">
                <td><button class="link-button device-filter" data-device-id="${item.device_id}">${fmt(item.device_id)}</button></td>
                <td>${deviceBadge(item.online)}</td>
                <td class="nowrap">${fmt(item.rssi)}</td>
                <td class="nowrap">${fmt(item.free_heap)}</td>
                <td>${fmt(item.upload_count)}</td>
                <td>${fmt(item.alarm_count)}</td>
                <td>${shortTime(item.last_heartbeat_at || item.last_seen)}</td>
                <td>${shortTime(item.last_upload_at)}</td>
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
      const deviceParam = selectedDeviceId ? `&device_id=${encodeURIComponent(selectedDeviceId)}` : "";
      const data = await fetchJson(`/api/alarms?page=1&page_size=20${deviceParam}`);
      document.getElementById("totalEvents").textContent = `${data.total}`;
      document.getElementById("alarmSummary").textContent = selectedDeviceId ? `设备 ${selectedDeviceId}` : "全部设备";

      if (!data.items.length) {
        document.getElementById("alarms").innerHTML = '<div class="empty">暂无历史事件</div>';
        return;
      }
      document.getElementById("alarms").innerHTML = `
        <table>
          <thead><tr><th>ID</th><th>设备</th><th>事件</th><th>类别</th><th>置信度</th><th>级别</th><th>状态</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            ${data.items.map(item => `
              <tr>
                <td>${item.event_id}</td>
                <td>${fmt(item.device_id)}</td>
                <td>${fmt(item.event_type)}</td>
                <td>${fmt(item.target_class)}</td>
                <td>${item.confidence === null ? "-" : Number(item.confidence).toFixed(2)}</td>
                <td>${fmt(item.alarm_level)}</td>
                <td>${item.handled ? statusBadge("handled") : statusBadge(item.alarm_status)}</td>
                <td>${shortTime(item.created_at)}</td>
                <td>${item.handled ? "-" : `<button onclick="handleAlarm(${item.event_id})">处理</button>`}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>`;
    }

    function statusText(status) {
      const map = {
        alarm: "告警",
        suspected: "可疑",
        suppressed: "已抑制",
        handled: "已处理",
        normal: "正常"
      };
      return map[status] || fmt(status);
    }

    function statusClass(status) {
      if (status === "alarm") return "danger";
      if (status === "suspected" || status === "suppressed") return "warn";
      if (status === "normal" || status === "handled") return "ok";
      return "neutral";
    }

    function statusBadge(status, id) {
      const idAttr = id ? ` id="${id}"` : "";
      return `<span${idAttr} class="badge ${statusClass(status)}">${statusText(status)}</span>`;
    }

    function deviceBadge(online) {
      return `<span class="badge ${online ? "ok" : "neutral"}">${online ? "在线" : "离线"}</span>`;
    }

    async function selectDevice(deviceId) {
      selectedDeviceId = deviceId;
      await loadDashboard();
    }

    async function clearDeviceFilter() {
      selectedDeviceId = "";
      await loadDashboard();
    }

    function showError(error) {
      const banner = document.getElementById("errorBanner");
      banner.textContent = `请求失败：${error.message || error}`;
      banner.style.display = "block";
    }

    function clearError() {
      const banner = document.getElementById("errorBanner");
      banner.textContent = "";
      banner.style.display = "none";
    }

    async function loadDashboard() {
      try {
        clearError();
        document.getElementById("selectedDevice").textContent = selectedDeviceId ? `当前设备：${selectedDeviceId}` : "当前设备：全部";
        await Promise.all([loadLatest(), loadDevices(), loadAlarms()]);
        document.getElementById("lastRefresh").textContent = new Date().toLocaleTimeString();
      } catch (error) {
        console.error(error);
        showError(error);
      }
    }

    loadDashboard();
    setInterval(loadDashboard, 5000);
    document.addEventListener("click", event => {
      const button = event.target.closest(".device-filter");
      if (button) selectDevice(button.dataset.deviceId);
    });
  </script>
</body>
</html>
"""
