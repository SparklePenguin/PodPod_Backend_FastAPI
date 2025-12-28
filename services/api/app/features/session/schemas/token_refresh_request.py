from pydantic import BaseModel, Field


class TokenRefreshRequest(BaseModel):
    """토큰 갱신 요청 스키마"""

    refresh_token: str = Field(..., serialization_alias="refreshToken")

    model_config = {"populate_by_name": True}
