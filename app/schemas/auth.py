from pydantic import BaseModel
from typing import Optional


# - MARK: 사용자 정보 응답
class User(BaseModel):
    id: int
    email: Optional[str] = None
    username: Optional[str] = None
    profile_image: Optional[str] = None


# - MARK: 토큰 정보 응답
class Credential(BaseModel):
    access_token: str
    refresh_token: str


# - MARK: 로그인 성공 응답
class SignInResponse(BaseModel):
    credential: Credential
    user: User


# - MARK: 회원가입 요청
class SignUpRequest(BaseModel):
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: str
    profile_image: Optional[str] = None


# - MARK: 이메일 로그인 요청
class EmailLoginRequest(BaseModel):
    email: str
    password: str


# - MARK: 소셜 로그인 요청
class SocialLoginRequest(BaseModel):
    email: str
    auth_provider: str
    auth_provider_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_image: Optional[str] = None


# - MARK: 토큰 갱신 요청
class TokenRefreshRequest(BaseModel):
    refresh_token: str
