"""로그아웃 요청 스키마"""

from pydantic import BaseModel, Field


class LogoutRequest(BaseModel):
    """로그아웃 요청"""

    refresh_token: str | None = Field(
        None, description="리프레시 토큰 (제공 시 Redis에서 무효화)"
    )
