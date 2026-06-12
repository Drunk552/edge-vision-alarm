import pytest
from fastapi import HTTPException

from app.core.validation import (
    validate_device_id,
    validate_device_status,
    validate_free_heap,
    validate_rssi,
)


def test_validate_device_id_accepts_safe_id():
    assert validate_device_id(" esp32_s3-cam_001 ") == "esp32_s3-cam_001"


@pytest.mark.parametrize("device_id", ["", "bad id", "bad/id", "x" * 65])
def test_validate_device_id_rejects_invalid_id(device_id):
    with pytest.raises(HTTPException):
        validate_device_id(device_id)


@pytest.mark.parametrize("rssi", [-120, -52, 0, None])
def test_validate_rssi_accepts_valid_range(rssi):
    assert validate_rssi(rssi) is None


@pytest.mark.parametrize("rssi", [-121, 1])
def test_validate_rssi_rejects_invalid_range(rssi):
    with pytest.raises(HTTPException):
        validate_rssi(rssi)


def test_validate_free_heap_rejects_negative_value():
    with pytest.raises(HTTPException):
        validate_free_heap(-1)


@pytest.mark.parametrize("status", ["online", "offline", "error"])
def test_validate_device_status_accepts_known_values(status):
    assert validate_device_status(status) is None


def test_validate_device_status_rejects_unknown_value():
    with pytest.raises(HTTPException):
        validate_device_status("sleeping")
