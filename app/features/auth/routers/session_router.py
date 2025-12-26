from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.deps.auth import (
    get_current_user_id,
)
from app.deps.database import get_session
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
    session: AsyncSession = Depends(get_session),
):
    """카카오 로그인"""
    service = KakaoOauthService(session)
    result = await service.sign_in_with_kakao(kakao_sign_in_request)
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
    session: AsyncSession = Depends(get_session),
):
    """Google 로그인"""
    service = GoogleOauthService(session)
    result = await service.sign_in_with_google(google_login_request)
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
    session: AsyncSession = Depends(get_session),
):
    """Apple 로그인"""
    service = AppleOauthService(session)
    result = await service.sign_in_with_apple(apple_login_request)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


@router.post(
    "",
    response_model=BaseResponse[dict],
)
async def create_session(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """세션 생성 (이메일 로그인 + 소셜 로그인 통합)"""
    service = SessionService(session)
    result = await service.login(login_data)
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
    session: AsyncSession = Depends(session),
    token: HTTPAuthorizationCredentials = Depends(security),
):
    """로그아웃 (세션 삭제 및 FCM 토큰 삭제)"""
    service = SessionService(session)
    await service.logout(token.credentials, current_user_id)
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
    session: AsyncSession = Depends(get_session),
):
    """토큰 갱신"""
    from app.core.security import (
        TokenBlacklistedError,
        TokenDecodeError,
        TokenExpiredError,
        TokenInvalidError,
    )

    try:
        service = SessionService(session)
        credential = await service.refresh_token(refresh_data.refresh_token)
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
