from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from app.api.deps import get_auth_service
from app.services.auth_service import AuthService
from app.schemas.auth import (
    EmailLoginRequest,
    SocialLoginRequest,
    LoginResponse,
    ErrorResponse,
    TokenRefreshRequest,
)
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None
    auth_provider: Optional[str] = None
    auth_provider_id: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_image: Optional[str] = None


@router.post(
    "/",
    response_model=LoginResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        422: {"description": "입력 데이터 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def create_session(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """세션 생성 (이메일 로그인 + 소셜 로그인 통합)"""
    return await auth_service.login(login_data)


@router.delete(
    "/",
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def delete_session(
    auth_service: AuthService = Depends(get_auth_service),
    token: str = Depends(security),
):
    """로그아웃 (세션 삭제)"""
    return await auth_service.logout(token.credentials)


@router.put(
    "/",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        501: {"model": ErrorResponse, "description": "구현되지 않은 기능"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def refresh_session(
    refresh_data: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """토큰 갱신"""
    return await auth_service.refresh_token(refresh_data.refresh_token)
