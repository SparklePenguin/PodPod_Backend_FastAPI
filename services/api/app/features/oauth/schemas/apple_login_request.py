from pydantic import BaseModel, Field


class AppleUserInfo(BaseModel):
    email: str | None = Field()
    firstName: str | None = Field(alias="firstName")
    lastName: str | None = Field(alias="lastName")


class AppleLoginRequest(BaseModel):
    identity_token: str = Field(alias="identityToken")
    authorization_code: str | None = Field(default=None, alias="authorizationCode")
    user: AppleUserInfo | None = Field(default=None)
    audience: str = Field(
        description="Apple Client ID (Bundle ID for native app, Service ID for web)"
    )
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
