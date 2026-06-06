from app.api.health_api import health_check


def test_health_check_returns_service_state():
    body = health_check()

    assert body["code"] == 0
    assert body["database"] == "ok"
    assert body["image_dir"] == "ok"
