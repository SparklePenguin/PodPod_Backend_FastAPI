from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(serialization_alias="idToken")
    fcm_token: str | None = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
