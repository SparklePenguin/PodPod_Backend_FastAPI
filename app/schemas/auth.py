from pydantic import BaseModel
from typing import Optional

from app.schemas.user import UserDto


# - MARK: 토큰 정보 응답
class Credential(BaseModel):
    access_token: str
    refresh_token: str


# - MARK: 로그인 성공 응답
class SignInResponse(BaseModel):
    credential: Credential
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


# - MARK: 이메일 로그인 요청
class EmailLoginRequest(BaseModel):
    email: str
    password: str


# - MARK: 토큰 갱신 요청
class TokenRefreshRequest(BaseModel):
    refresh_token: str
