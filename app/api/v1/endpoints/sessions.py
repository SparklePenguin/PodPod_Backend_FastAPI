from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from app.api.deps import (
    get_session_service,
    get_kakao_oauth_service,
    get_google_oauth_service,
    get_apple_oauth_service,
)
from app.services.kakao_oauth_service import KakaoOauthService, KakaoTokenResponse
from app.services.google_oauth_service import GoogleOauthService, GoogleLoginRequest
from app.services.apple_oauth_service import AppleOauthService, AppleLoginRequest
from app.services.session_service import SessionService
from app.schemas.auth import (
    TokenRefreshRequest,
)
from app.schemas.common import ErrorResponse, SuccessResponse
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


# - MARK: 카카오 로그인
@router.post(
    "/kakao",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "카카오 로그인 성공"},
        400: {"model": ErrorResponse, "description": "카카오 인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def sign_in_with_kakao(
    kakao_sign_in_request: KakaoTokenResponse,
    kakao_oauth_service: KakaoOauthService = Depends(get_kakao_oauth_service),
):
    """카카오 로그인"""
    return await kakao_oauth_service.sign_in_with_kakao(kakao_sign_in_request)


# - MARK: Google 로그인
@router.post(
    "/google",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "Google 로그인 성공"},
        400: {"model": ErrorResponse, "description": "Google 인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def sign_in_with_google(
    google_login_request: GoogleLoginRequest,
    google_oauth_service: GoogleOauthService = Depends(get_google_oauth_service),
):
    """Google 로그인"""
    return await google_oauth_service.sign_in_with_google(google_login_request)


# - MARK: Apple 로그인
@router.post(
    "/apple",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "Apple 로그인 성공"},
        400: {"model": ErrorResponse, "description": "Apple 인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def sign_in_with_apple(
    apple_login_request: AppleLoginRequest,
    apple_oauth_service: AppleOauthService = Depends(get_apple_oauth_service),
):
    """Apple 로그인"""
    return await apple_oauth_service.sign_in_with_apple(apple_login_request)


@router.post(
    "/",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        422: {"description": "입력 데이터 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def create_session(
    login_data: LoginRequest,
    auth_service: SessionService = Depends(get_session_service),
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
    auth_service: SessionService = Depends(get_session_service),
    token: str = Depends(security),
):
    """로그아웃 (세션 삭제)"""
    return await auth_service.logout(token.credentials)


@router.put(
    "/",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        501: {"model": ErrorResponse, "description": "구현되지 않은 기능"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def refresh_session(
    refresh_data: TokenRefreshRequest,
    auth_service: SessionService = Depends(get_session_service),
):
    """토큰 갱신"""
    return await auth_service.refresh_token(refresh_data.refresh_token)
