from pydantic import BaseModel, Field


class EmailLoginRequest(BaseModel):
    """이메일 로그인 요청 스키마"""

    email: str = Field(..., serialization_alias="email")
    password: str = Field(..., serialization_alias="password")
    fcm_token: str | None = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
