from app.api.web_api import dashboard


def test_dashboard_contains_main_sections():
    html = dashboard()

    assert "Edge Vision Alarm" in html
    assert "/api/latest" in html
    assert "/api/alarms" in html
    assert "/api/devices" in html
