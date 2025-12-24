from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.api.deps import (
    get_apple_oauth_service,
    get_current_user_id,
    get_google_oauth_service,
    get_kakao_oauth_service,
    get_session_service,
)
from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.features.auth.schemas import (
    TokenRefreshRequest,
)
from app.features.auth.services.apple_oauth_service import (
    AppleLoginRequest,
    AppleOauthService,
)
from app.features.auth.services.google_oauth_service import (
    GoogleLoginRequest,
    GoogleOauthService,
)
from app.features.auth.services.kakao_oauth_service import (
    KakaoOauthService,
    KakaoTokenResponse,
)
from app.features.auth.services.session_service import SessionService

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
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
    # result는 이미 dict 타입이므로 model_dump 불필요
    return BaseResponse.ok(data=result)


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
    # result는 이미 dict 타입이므로 model_dump 불필요
    return BaseResponse.ok(data=result)


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
    current_user_id: int = Depends(get_current_user_id),
    auth_service: SessionService = Depends(get_session_service),
    token: HTTPAuthorizationCredentials = Depends(security),
):
    """로그아웃 (세션 삭제 및 FCM 토큰 삭제)"""
    await auth_service.logout(token.credentials, current_user_id)
    return BaseResponse.ok(http_status=HttpStatus.NO_CONTENT)


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
        TokenBlacklistedError,
        TokenDecodeError,
        TokenExpiredError,
        TokenInvalidError,
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
        return BaseResponse.error(
            error_key="TOKEN_INVALID",
            error_code=1002,
            http_status=HttpStatus.UNAUTHORIZED,
            message_ko=e.message,
            message_en=e.message,
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="TOKEN_REFRESH_FAILED",
            error_code=5001,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"토큰 갱신 실패: {str(e)}",
            message_en=f"Token refresh failed: {str(e)}",
        )
