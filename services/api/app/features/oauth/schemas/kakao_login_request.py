from pydantic import BaseModel, Field


class KakaoLoginRequest(BaseModel):
    """카카오 로그인 요청"""

    access_token: str = Field(serialization_alias="accessToken")
    fcm_token: str | None = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
