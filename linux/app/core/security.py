"""接口 Token 鉴权工具。"""

from hmac import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException

from app.core.config import settings
from app.core.error_codes import AUTH_ERROR


def verify_api_token(
    x_api_token: Annotated[str | None, Header(alias="X-API-Token")] = None,
) -> None:
    """校验 API Token，未配置 Token 时以开发模式放行。"""

    expected_token = settings.api_token
    if not expected_token:
        return

    if x_api_token and compare_digest(x_api_token, str(expected_token)):
        return

    raise HTTPException(
        status_code=401,
        detail={"code": AUTH_ERROR, "message": "invalid api token"},
    )
