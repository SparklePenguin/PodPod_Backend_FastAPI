from pydantic import BaseModel, Field


class SignUpRequest(BaseModel):
    """회원가입 요청 스키마"""

    email: str | None = Field(default=None)
    username: str | None = Field(default=None)
    nickname: str | None = Field(default=None)
    password: str | None = Field(default=None)
    profile_image: str | None = Field(default=None, alias="profileImage")
    auth_provider: str | None = Field(default=None, alias="authProvider")
    auth_provider_id: str | None = Field(default=None, alias="authProviderId")
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
