"""인증 관련 스키마"""

from app.features.users.schemas import UserDetailDto
from pydantic import BaseModel, Field


class EmailLoginRequest(BaseModel):
    """이메일 로그인 요청 스키마"""

    email: str = Field(...)
    password: str = Field(...)
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}


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


class CredentialDto(BaseModel):
    """토큰 정보 응답 DTO"""

    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")

    model_config = {"populate_by_name": True}


class LoginInfoDto(BaseModel):
    """로그인 정보 응답 DTO"""

    credential: CredentialDto
    user: UserDetailDto
