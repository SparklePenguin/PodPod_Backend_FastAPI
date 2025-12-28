from pydantic import BaseModel, Field


class AppleUserInfo(BaseModel):
    email: str | None = Field(serialization_alias="email")
    firstName: str | None = Field(serialization_alias="firstName")
    lastName: str | None = Field(serialization_alias="lastName")


class AppleLoginRequest(BaseModel):
    identity_token: str = Field(serialization_alias="identityToken")
    authorization_code: str | None = Field(
        default=None, serialization_alias="authorizationCode"
    )
    user: AppleUserInfo | None = Field(default=None, serialization_alias="user")
    fcm_token: str | None = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
