from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(alias="idToken")
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
