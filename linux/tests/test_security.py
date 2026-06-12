from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from app.core import security


@dataclass(frozen=True)
class FakeSettings:
    api_token: str | None


def test_api_token_allows_requests_when_unconfigured(monkeypatch):
    monkeypatch.setattr(security, "settings", FakeSettings(api_token=None))

    assert security.verify_api_token() is None


def test_api_token_rejects_missing_token_when_configured(monkeypatch):
    monkeypatch.setattr(security, "settings", FakeSettings(api_token="secret"))

    with pytest.raises(HTTPException) as exc_info:
        security.verify_api_token()

    assert exc_info.value.status_code == 401


def test_api_token_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(security, "settings", FakeSettings(api_token="secret"))

    with pytest.raises(HTTPException) as exc_info:
        security.verify_api_token("wrong")

    assert exc_info.value.status_code == 401


def test_api_token_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(security, "settings", FakeSettings(api_token="secret"))

    assert security.verify_api_token("secret") is None
