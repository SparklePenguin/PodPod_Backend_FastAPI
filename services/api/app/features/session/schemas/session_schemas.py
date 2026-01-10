"""세션 관련 스키마"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""

    email: str = Field()
    password: str | None = Field(default=None)
    auth_provider: str | None = Field(default=None, alias="authProvider")
    auth_provider_id: str | None = Field(default=None, alias="authProviderId")
    username: str | None = Field(default=None)
    full_name: str | None = Field(default=None, alias="fullName")
    profile_image: str | None = Field(default=None, alias="profileImage")
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}


class LogoutRequest(BaseModel):
    """로그아웃 요청"""

    refresh_token: str | None = Field(
        None, description="리프레시 토큰 (제공 시 Redis에서 무효화)"
    )


class TokenRefreshRequest(BaseModel):
    """토큰 갱신 요청 스키마"""

    refresh_token: str = Field(..., alias="refreshToken")

    model_config = {"populate_by_name": True}
