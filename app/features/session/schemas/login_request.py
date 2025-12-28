from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""

    email: str = Field(serialization_alias="email")
    password: Optional[str] = Field(default=None, serialization_alias="password")
    auth_provider: Optional[str] = Field(
        default=None, serialization_alias="authProvider"
    )
    auth_provider_id: Optional[str] = Field(
        default=None, serialization_alias="authProviderId"
    )
    username: Optional[str] = Field(default=None, serialization_alias="username")
    full_name: Optional[str] = Field(default=None, serialization_alias="fullName")
    profile_image: Optional[str] = Field(
        default=None, serialization_alias="profileImage"
    )
    fcm_token: Optional[str] = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}
