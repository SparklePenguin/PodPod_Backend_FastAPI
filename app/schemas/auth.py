from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int  # 토큰 만료 시간 (초)


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Token] = None
    user: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: str
    status: int
    message: str


class RegisterRequest(BaseModel):
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: str
    profile_image: Optional[str] = None


class EmailLoginRequest(BaseModel):
    email: str
    password: str


class SocialLoginRequest(BaseModel):
    email: str
    auth_provider: str
    auth_provider_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_image: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str
