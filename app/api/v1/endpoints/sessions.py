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
from app.services.apple_oauth_service import (
    AppleOauthService,
    AppleLoginRequest,
    AppleCallbackParam,
)
from app.services.session_service import SessionService
from app.schemas.auth import (
    TokenRefreshRequest,
)
from app.schemas.common import BaseResponse
from app.core.http_status import HttpStatus
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
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "카카오 로그인 성공",
        },
    },
)
async def sign_in_with_kakao(
    kakao_sign_in_request: KakaoTokenResponse,
    kakao_oauth_service: KakaoOauthService = Depends(get_kakao_oauth_service),
):
    """카카오 로그인"""
    result = await kakao_oauth_service.sign_in_with_kakao(kakao_sign_in_request)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


# - MARK: Google 로그인
@router.post(
    "/google",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "Google 로그인 성공",
        },
    },
)
async def sign_in_with_google(
    google_login_request: GoogleLoginRequest,
    google_oauth_service: GoogleOauthService = Depends(get_google_oauth_service),
):
    """Google 로그인"""
    result = await google_oauth_service.sign_in_with_google(google_login_request)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


# - MARK: Apple 로그인
@router.post(
    "/apple",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "Apple 로그인 성공",
        },
    },
)
async def sign_in_with_apple(
    apple_login_request: AppleLoginRequest,
    apple_oauth_service: AppleOauthService = Depends(get_apple_oauth_service),
):
    """Apple 로그인"""
    result = await apple_oauth_service.sign_in_with_apple(apple_login_request)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


@router.post(
    "",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "세션 생성 성공",
        },
    },
)
async def create_session(
    login_data: LoginRequest,
    auth_service: SessionService = Depends(get_session_service),
):
    """세션 생성 (이메일 로그인 + 소셜 로그인 통합)"""
    result = await auth_service.login(login_data)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


@router.delete(
    "",
    status_code=HttpStatus.NO_CONTENT,
    responses={
        HttpStatus.NO_CONTENT: {
            "description": "로그아웃 성공 (No Content)",
        },
    },
    dependencies=[Depends(security)],
)
async def delete_session(
    auth_service: SessionService = Depends(get_session_service),
    token: str = Depends(security),
):
    """로그아웃 (세션 삭제)"""
    await auth_service.logout(token.credentials)
    return BaseResponse.ok(code=HttpStatus.NO_CONTENT)


@router.put(
    "",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "토큰 갱신 성공",
        },
    },
)
async def refresh_session(
    refresh_data: TokenRefreshRequest,
    auth_service: SessionService = Depends(get_session_service),
):
    """토큰 갱신"""
    from app.core.security import (
        TokenExpiredError,
        TokenInvalidError,
        TokenDecodeError,
        TokenBlacklistedError,
    )

    try:
        credential = await auth_service.refresh_token(refresh_data.refresh_token)
        return BaseResponse.ok(data=credential.model_dump(by_alias=True))
    except (
        TokenExpiredError,
        TokenInvalidError,
        TokenDecodeError,
        TokenBlacklistedError,
    ) as e:
        return BaseResponse.error(code=HttpStatus.UNAUTHORIZED, message=e.message)
    except Exception as e:
        return BaseResponse.error(
            code=HttpStatus.INTERNAL_SERVER_ERROR,
            message=f"토큰 갱신 실패: {str(e)}",
        )
