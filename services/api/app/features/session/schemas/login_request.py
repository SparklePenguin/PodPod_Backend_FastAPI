from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""

    email: str = Field(serialization_alias="email")
    password: str | None = Field(default=None, serialization_alias="password")
    auth_provider: str | None = Field(default=None, serialization_alias="authProvider")
    auth_provider_id: str | None = Field(
        default=None, serialization_alias="authProviderId"
    )
    username: str | None = Field(default=None, serialization_alias="username")
    full_name: str | None = Field(default=None, serialization_alias="fullName")
    profile_image: str | None = Field(default=None, serialization_alias="profileImage")
    fcm_token: str | None = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
