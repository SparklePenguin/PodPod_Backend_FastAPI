from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.user import UserDto


# - MARK: 토큰 정보 응답
class CredentialDto(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")

    model_config = {"populate_by_name": True}


# - MARK: 로그인 성공 응답
class SignInResponse(BaseModel):
    credential: CredentialDto
    user: UserDto


# - MARK: 회원가입 요청
class SignUpRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    nickname: Optional[str] = None
    password: Optional[str] = None
    profile_image: Optional[str] = None
    auth_provider: Optional[str] = None
    auth_provider_id: Optional[str] = None

    model_config = {"populate_by_name": True}


# - MARK: 이메일 로그인 요청
class EmailLoginRequest(BaseModel):
    email: str
    password: str


# - MARK: 토큰 갱신 요청
class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken")

    model_config = {"populate_by_name": True}
